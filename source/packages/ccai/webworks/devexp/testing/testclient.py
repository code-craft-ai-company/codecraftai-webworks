"""
    HTTP test client for in-process endpoint testing.

    This module provides the :class:`TestClient` class that executes
    HTTP requests against an application without starting a real server.
    It supports all standard HTTP methods, JSON, form, multipart and raw
    request bodies, custom headers, query parameters, cookie persistence
    via :class:`CookieJar`, redirect following, and authentication
    helpers.

    The client accepts the framework's own application object. The kind
    of application is detected and the matching transport is used (see
    :mod:`ccai.webworks.devexp.testing.transports`):

    - an **ASGI** application, such as ``ASGIApplication`` or the ``app``
      of a site, is called with a real ``http`` scope, so routing,
      middleware, sessions and CSRF protection are exercised;
    - a **WSGI** application is called with a PEP 3333 ``environ``;
    - a plain callable with the signature
      ``(method, path, headers, body) -> (status_code, headers, body)``
      is called directly.

    Example::

        from ccai.webworks.devexp.testing.testclient import TestClient

        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200
"""

import json as _json_module
import time
import uuid

from email.utils import parsedate_to_datetime
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple, Union
from urllib.parse import urlencode, urlsplit

from ccai.webworks.devexp.testing.testresponse import TestResponse
from ccai.webworks.devexp.testing.transports import create_transport


DEFAULT_BASE_URL = "http://testserver"
"""The origin requests are addressed to when the path is not an absolute URL."""

MAX_REDIRECTS = 20
"""The number of redirects followed before the client gives up."""

REDIRECT_STATUS_CODES = (301, 302, 303, 307, 308)
"""Status codes that carry a ``Location`` to follow."""

HeadersArgument = Union[Dict[str, str], Sequence[Tuple[str, str]]]
"""Request headers, as a dictionary or a list of (name, value) tuples."""


class TooManyRedirectsError(Exception):
    """
        Raised when a request is redirected more than :data:`MAX_REDIRECTS` times.
    """


# =============================================================================
# CookieJar
# =============================================================================

class _StoredCookie:
    """
        One cookie held by the :class:`CookieJar`, with its attributes.

        :param name: The cookie name.
        :param value: The cookie value.
        :param path: The path the cookie is scoped to.
        :param domain: The domain the cookie is scoped to, or ``None`` when
            the cookie was set without one.
        :param host_only: Whether the cookie is sent only to the exact host
            that set it.
        :param secure: Whether the cookie is sent only over ``https``.
        :param expires_at: The time, as seconds since the epoch, at which
            the cookie expires, or ``None`` for a session cookie.
    """

    def __init__(
        self,
        name: str,
        value: str,
        path: str = "/",
        domain: Optional[str] = None,
        host_only: bool = True,
        secure: bool = False,
        expires_at: Optional[float] = None,
    ):
        """
            Construct a _StoredCookie.

            :param name: The cookie name.
            :param value: The cookie value.
            :param path: The path the cookie is scoped to.
            :param domain: The domain the cookie is scoped to.
            :param host_only: Whether only the setting host receives it.
            :param secure: Whether the cookie is restricted to ``https``.
            :param expires_at: Expiry as seconds since the epoch.
        """
        self.name = name
        self.value = value
        self.path = path
        self.domain = domain
        self.host_only = host_only
        self.secure = secure
        self.expires_at = expires_at
        return

    def is_expired(self, now: float) -> bool:
        """
            Whether the cookie has expired.

            :param now: The current time as seconds since the epoch.

            :returns: ``True`` if the cookie must no longer be sent.
        """
        expired = self.expires_at is not None and self.expires_at <= now
        return expired

    def matches(self, path: str, host: Optional[str], scheme: str) -> bool:
        """
            Whether the cookie is sent with a request.

            :param path: The request path.
            :param host: The request host without port, or ``None`` to
                skip the domain check.
            :param scheme: The request URL scheme.

            :returns: ``True`` if the path, domain and Secure rules allow it.
        """
        if self.secure and scheme != "https":
            return False

        if host is not None and self.domain is not None:
            lower_host = host.lower()

            if self.host_only:
                if lower_host != self.domain:
                    return False
            else:
                if lower_host != self.domain and not lower_host.endswith("." + self.domain):
                    return False

        # RFC 6265 section 5.1.4 path-match.
        cookie_path = self.path

        if path == cookie_path:
            return True

        if path.startswith(cookie_path):
            if cookie_path.endswith("/"):
                return True
            if path[len(cookie_path):len(cookie_path) + 1] == "/":
                return True

        return False


class CookieJar:
    """
        A cookie jar that persists cookies across :class:`TestClient`
        requests the way a browser does.

        The jar honours the attributes of ``Set-Cookie``: a cookie with
        ``Max-Age=0`` or an ``Expires`` date in the past is removed, and
        ``Path``, ``Domain`` and ``Secure`` decide which requests a cookie
        is sent with. A logout that clears the session cookie therefore
        really clears it for the following requests.
    """

    def __init__(self):
        """
            Construct an empty CookieJar.
        """
        self._store: Dict[Tuple[str, str, str], _StoredCookie] = {}
        return

    @property
    def cookies(self) -> Dict[str, str]:
        """
            All stored, unexpired cookies as a dictionary.

            :returns: A copy of the cookie name-value pairs.
        """
        now = time.time()

        result: Dict[str, str] = {}
        for cookie in self._store.values():
            if not cookie.is_expired(now):
                result[cookie.name] = cookie.value

        return result

    def set(
        self,
        name: str,
        value: str,
        path: str = "/",
        domain: Optional[str] = None,
        secure: bool = False,
        max_age: Optional[int] = None,
    ) -> None:
        """
            Set a cookie.

            :param name: The cookie name.
            :param value: The cookie value.
            :param path: The path the cookie is scoped to.
            :param domain: The domain the cookie is scoped to. ``None``
                sends it to every host.
            :param secure: Whether the cookie is sent only over ``https``.
            :param max_age: Lifetime in seconds. ``None`` makes a session
                cookie; zero or a negative number removes the cookie.
        """
        normalized_domain = None
        if domain is not None:
            normalized_domain = domain.lstrip(".").lower()

        key = (normalized_domain or "", path, name)

        if max_age is not None and max_age <= 0:
            self._store.pop(key, None)
            return

        expires_at = None
        if max_age is not None:
            expires_at = time.time() + max_age

        self._store[key] = _StoredCookie(
            name=name,
            value=value,
            path=path,
            domain=normalized_domain,
            host_only=False,
            secure=secure,
            expires_at=expires_at,
        )

        return

    def get(self, name: str, default: Optional[str] = None) -> Optional[str]:
        """
            Get a cookie value by name.

            :param name: The cookie name.
            :param default: Value to return if the cookie is not found.

            :returns: The cookie value or the default.
        """
        return self.cookies.get(name, default)

    def delete(self, name: str) -> None:
        """
            Delete every cookie with the given name.

            :param name: The cookie name to remove.
        """
        for key in list(self._store.keys()):
            if key[2] == name:
                del self._store[key]

        return

    def clear(self) -> None:
        """
            Remove all cookies.
        """
        self._store.clear()
        return

    def to_header(
        self,
        path: Optional[str] = None,
        host: Optional[str] = None,
        scheme: str = "http",
    ) -> str:
        """
            Format the cookies that apply to a request as a ``Cookie``
            header value.

            Called without arguments, every unexpired cookie that is not
            restricted to ``https`` is included.

            :param path: The request path, or ``None`` to ignore cookie paths.
            :param host: The request host without port, or ``None`` to
                ignore cookie domains.
            :param scheme: The request URL scheme.

            :returns: A string in the form ``name1=value1; name2=value2``.
        """
        now = time.time()

        # Drop cookies that expired since they were stored.
        for key in list(self._store.keys()):
            if self._store[key].is_expired(now):
                del self._store[key]

        # Cookies with longer paths are listed first (RFC 6265 section 5.4).
        candidates = sorted(
            self._store.values(),
            key=lambda cookie: len(cookie.path),
            reverse=True,
        )

        parts = []
        for cookie in candidates:
            if path is None:
                if cookie.secure and scheme != "https":
                    continue
            elif not cookie.matches(path, host, scheme):
                continue

            parts.append("{}={}".format(cookie.name, cookie.value))

        header_value = "; ".join(parts)

        return header_value

    def update_from_headers(
        self,
        headers: Union[Dict[str, str], Sequence[Tuple[str, str]]],
        request_path: str = "/",
        request_host: Optional[str] = None,
    ) -> None:
        """
            Extract ``Set-Cookie`` headers and store or remove the cookies.

            Accepts the headers as a dictionary or as a list of
            ``(name, value)`` tuples; a list is how several ``Set-Cookie``
            headers of one response are carried.

            :param headers: The response headers.
            :param request_path: The path of the request that received the
                response; a cookie without a ``Path`` is scoped to its
                directory.
            :param request_host: The host of that request; a cookie without
                a ``Domain`` is sent only to this host.
        """
        if isinstance(headers, dict):
            pairs = list(headers.items())
        else:
            pairs = list(headers)

        for header_name, header_value in pairs:
            if header_name.lower() == "set-cookie":
                self._parse_set_cookie(header_value, request_path, request_host)

        return

    def _parse_set_cookie(
        self,
        header_value: str,
        request_path: str = "/",
        request_host: Optional[str] = None,
    ) -> None:
        """
            Parse a single Set-Cookie header value and apply it to the jar.

            :param header_value: The Set-Cookie header value string.
            :param request_path: The path of the request being answered.
            :param request_host: The host of the request being answered.
        """
        # The cookie name=value is the first segment before any semicolon
        parts = header_value.split(";")

        name_value = parts[0].strip()
        if "=" not in name_value:
            return

        eq_index = name_value.index("=")
        name = name_value[:eq_index].strip()
        value = name_value[eq_index + 1:].strip()

        if not name:
            return

        path = None
        domain = None
        secure = False
        max_age = None
        expires_at = None

        for attribute in parts[1:]:
            attribute = attribute.strip()

            if len(attribute) == 0:
                continue

            attr_name, _separator, attr_value = attribute.partition("=")
            attr_name = attr_name.strip().lower()
            attr_value = attr_value.strip()

            if attr_name == "path":
                if attr_value.startswith("/"):
                    path = attr_value
            elif attr_name == "domain":
                if len(attr_value) > 0:
                    domain = attr_value.lstrip(".").lower()
            elif attr_name == "secure":
                secure = True
            elif attr_name == "max-age":
                try:
                    max_age = int(attr_value)
                except ValueError:
                    # An unparseable Max-Age is ignored (RFC 6265 section 5.2.2).
                    max_age = None
            elif attr_name == "expires":
                try:
                    expires_at = parsedate_to_datetime(attr_value).timestamp()
                except (TypeError, ValueError):
                    # An unparseable date is ignored (RFC 6265 section 5.2.1).
                    expires_at = None

        if path is None:
            path = self._default_path(request_path)

        host_only = domain is None

        if host_only and request_host is not None:
            domain = request_host.lower()

        now = time.time()

        # Max-Age takes precedence over Expires.
        if max_age is not None:
            expires_at = now + max_age

        key = (domain or "", path, name)

        # A cookie placed in the jar by the test (without a domain) is the
        # same cookie as far as the server is concerned; the server's
        # answer replaces it.
        self._store.pop(("", path, name), None)

        if expires_at is not None and expires_at <= now:
            # The server expired the cookie: remove it.
            self._store.pop(key, None)
            return

        self._store[key] = _StoredCookie(
            name=name,
            value=value,
            path=path,
            domain=domain,
            host_only=host_only,
            secure=secure,
            expires_at=expires_at,
        )

        return

    def _default_path(self, request_path: str) -> str:
        """
            Compute the default path of a cookie set without a ``Path``.

            This is the directory of the request path (RFC 6265 section 5.1.4).

            :param request_path: The path of the request being answered.

            :returns: The default cookie path.
        """
        if not request_path.startswith("/"):
            return "/"

        last_slash = request_path.rfind("/")

        if last_slash <= 0:
            return "/"

        return request_path[:last_slash]


# =============================================================================
# TestClient
# =============================================================================

class TestClient:
    """
        HTTP client for testing endpoints without a real server.

        The client executes requests in-process by calling the
        application directly. It manages default headers, cookie
        persistence, and optional authentication.

        The application may be an ASGI application (the framework's
        ``ASGIApplication``), a WSGI application, or a plain callable
        that accepts::

            (method, path, headers, body) -> (status_code, headers, body)

        Used as a context manager the client also runs the ASGI lifespan:
        startup on entry and shutdown on exit.

        :param app: The application to test against.
        :param default_headers: Optional default headers sent with
            every request.
        :param transport: ``"asgi"``, ``"wsgi"`` or ``"callable"``.
            ``None`` detects the kind of application.
        :param base_url: The origin requests are addressed to. Its scheme
            and host become the request's scheme and ``Host``.
        :param follow_redirects: Whether redirect responses are followed
            by default.
        :param raise_app_exceptions: Whether an exception raised by the
            application propagates into the test (``True``) or becomes a
            ``500`` response (``False``).
    """

    def __init__(
        self,
        app: Callable,
        default_headers: Optional[Dict[str, str]] = None,
        transport: Optional[str] = None,
        base_url: str = DEFAULT_BASE_URL,
        follow_redirects: bool = False,
        raise_app_exceptions: bool = True,
    ):
        """
            Construct a TestClient.

            :param app: The application to test against.
            :param default_headers: Default headers to include in
                every request.
            :param transport: The transport name, or ``None`` to detect it.
            :param base_url: The origin requests are addressed to.
            :param follow_redirects: Whether to follow redirects by default.
            :param raise_app_exceptions: Whether application exceptions
                propagate into the test.
        """
        self._app = app
        self._default_headers: Dict[str, str] = dict(default_headers or {})
        self._cookies = CookieJar()
        self._auth: Optional[Tuple[str, str]] = None
        self._auth_header: Optional[Tuple[str, str]] = None
        self._follow_redirects = follow_redirects

        base_parts = urlsplit(base_url)
        self._scheme = base_parts.scheme or "http"
        self._host = base_parts.netloc or "testserver"

        self._transport = create_transport(
            app, transport=transport, raise_app_exceptions=raise_app_exceptions,
        )

        return

    # -------------------------------------------------------------------------
    # Properties
    # -------------------------------------------------------------------------

    @property
    def app(self) -> Callable:
        """
            The application callable being tested.

            :returns: The application callable.
        """
        return self._app

    @property
    def default_headers(self) -> Dict[str, str]:
        """
            The default headers sent with every request.

            :returns: A copy of the default headers dictionary.
        """
        return dict(self._default_headers)

    @property
    def cookies(self) -> CookieJar:
        """
            The cookie jar used for cookie persistence.

            :returns: The :class:`CookieJar` instance.
        """
        return self._cookies

    @property
    def transport_name(self) -> str:
        """
            The kind of application the client is calling.

            :returns: ``"asgi"``, ``"wsgi"`` or ``"callable"``.
        """
        return self._transport.name

    # -------------------------------------------------------------------------
    # Lifecycle
    # -------------------------------------------------------------------------

    def __enter__(self) -> "TestClient":
        """
            Start the application's lifespan and return the client.

            :returns: This client.
        """
        self._transport.startup()
        return self

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        """
            Shut the application's lifespan down and release the transport.

            :param exc_type: The exception type, if the block raised.
            :param exc_value: The exception, if the block raised.
            :param traceback: The traceback, if the block raised.
        """
        try:
            self._transport.shutdown()
        finally:
            self._transport.close()

        return

    def close(self) -> None:
        """
            Release the resources of the transport.

            Needed only for an ASGI application used without the context
            manager; it stops the event loop thread the client started.
        """
        self._transport.close()
        return

    # -------------------------------------------------------------------------
    # Authentication Helpers
    # -------------------------------------------------------------------------

    def set_basic_auth(self, username: str, password: str) -> None:
        """
            Configure HTTP Basic authentication for all subsequent
            requests.

            :param username: The username.
            :param password: The password.
        """
        import base64

        credentials = "{}:{}".format(username, password)
        encoded = base64.b64encode(credentials.encode("utf-8")).decode("utf-8")
        self._auth_header = ("Authorization", "Basic {}".format(encoded))
        return

    def set_bearer_token(self, token: str) -> None:
        """
            Configure Bearer token authentication for all subsequent
            requests.

            :param token: The bearer token string.
        """
        self._auth_header = ("Authorization", "Bearer {}".format(token))
        return

    def clear_auth(self) -> None:
        """
            Remove any configured authentication.
        """
        self._auth_header = None
        return

    # -------------------------------------------------------------------------
    # HTTP Method Helpers
    # -------------------------------------------------------------------------

    def request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Any] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[HeadersArgument] = None,
        content: Optional[Union[bytes, str]] = None,
        files: Optional[Dict[str, Any]] = None,
        follow_redirects: Optional[bool] = None,
    ) -> TestResponse:
        """
            Send a request with any HTTP method.

            :param method: The HTTP method string.
            :param path: The request path.
            :param params: Optional query parameters.
            :param json: Optional JSON body.
            :param data: Optional form data body.
            :param headers: Optional request-specific headers.
            :param content: Optional raw body, as ``bytes`` or ``str``.
            :param files: Optional files to upload as
                ``multipart/form-data``. Each value is the file content
                (``bytes`` or a binary file object), or a tuple of
                ``(filename, content)`` or
                ``(filename, content, content_type)``.
            :param follow_redirects: Whether to follow redirects. ``None``
                uses the client's default.

            :returns: A :class:`TestResponse` instance.
        """
        return self._make_request(
            method, path, params=params, json=json, data=data, headers=headers,
            content=content, files=files, follow_redirects=follow_redirects,
        )

    def get(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[HeadersArgument] = None,
        follow_redirects: Optional[bool] = None,
    ) -> TestResponse:
        """
            Send a GET request.

            :param path: The request path.
            :param params: Optional query parameters.
            :param headers: Optional request-specific headers.
            :param follow_redirects: Whether to follow redirects.

            :returns: A :class:`TestResponse` instance.
        """
        return self._make_request(
            "GET", path, params=params, headers=headers, follow_redirects=follow_redirects,
        )

    def post(
        self,
        path: str,
        json: Optional[Any] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[HeadersArgument] = None,
        content: Optional[Union[bytes, str]] = None,
        files: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        follow_redirects: Optional[bool] = None,
    ) -> TestResponse:
        """
            Send a POST request.

            :param path: The request path.
            :param json: Optional JSON body.
            :param data: Optional form data body.
            :param headers: Optional request-specific headers.
            :param content: Optional raw body.
            :param files: Optional files to upload as multipart form data.
            :param params: Optional query parameters.
            :param follow_redirects: Whether to follow redirects.

            :returns: A :class:`TestResponse` instance.
        """
        return self._make_request(
            "POST", path, params=params, json=json, data=data, headers=headers,
            content=content, files=files, follow_redirects=follow_redirects,
        )

    def put(
        self,
        path: str,
        json: Optional[Any] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[HeadersArgument] = None,
        content: Optional[Union[bytes, str]] = None,
        files: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        follow_redirects: Optional[bool] = None,
    ) -> TestResponse:
        """
            Send a PUT request.

            :param path: The request path.
            :param json: Optional JSON body.
            :param data: Optional form data body.
            :param headers: Optional request-specific headers.
            :param content: Optional raw body.
            :param files: Optional files to upload as multipart form data.
            :param params: Optional query parameters.
            :param follow_redirects: Whether to follow redirects.

            :returns: A :class:`TestResponse` instance.
        """
        return self._make_request(
            "PUT", path, params=params, json=json, data=data, headers=headers,
            content=content, files=files, follow_redirects=follow_redirects,
        )

    def patch(
        self,
        path: str,
        json: Optional[Any] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[HeadersArgument] = None,
        content: Optional[Union[bytes, str]] = None,
        files: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        follow_redirects: Optional[bool] = None,
    ) -> TestResponse:
        """
            Send a PATCH request.

            :param path: The request path.
            :param json: Optional JSON body.
            :param data: Optional form data body.
            :param headers: Optional request-specific headers.
            :param content: Optional raw body.
            :param files: Optional files to upload as multipart form data.
            :param params: Optional query parameters.
            :param follow_redirects: Whether to follow redirects.

            :returns: A :class:`TestResponse` instance.
        """
        return self._make_request(
            "PATCH", path, params=params, json=json, data=data, headers=headers,
            content=content, files=files, follow_redirects=follow_redirects,
        )

    def delete(
        self,
        path: str,
        headers: Optional[HeadersArgument] = None,
        params: Optional[Dict[str, Any]] = None,
        follow_redirects: Optional[bool] = None,
    ) -> TestResponse:
        """
            Send a DELETE request.

            :param path: The request path.
            :param headers: Optional request-specific headers.
            :param params: Optional query parameters.
            :param follow_redirects: Whether to follow redirects.

            :returns: A :class:`TestResponse` instance.
        """
        return self._make_request(
            "DELETE", path, params=params, headers=headers, follow_redirects=follow_redirects,
        )

    def head(
        self,
        path: str,
        headers: Optional[HeadersArgument] = None,
        params: Optional[Dict[str, Any]] = None,
        follow_redirects: Optional[bool] = None,
    ) -> TestResponse:
        """
            Send a HEAD request.

            :param path: The request path.
            :param headers: Optional request-specific headers.
            :param params: Optional query parameters.
            :param follow_redirects: Whether to follow redirects.

            :returns: A :class:`TestResponse` instance.
        """
        return self._make_request(
            "HEAD", path, params=params, headers=headers, follow_redirects=follow_redirects,
        )

    def options(
        self,
        path: str,
        headers: Optional[HeadersArgument] = None,
        params: Optional[Dict[str, Any]] = None,
        follow_redirects: Optional[bool] = None,
    ) -> TestResponse:
        """
            Send an OPTIONS request.

            :param path: The request path.
            :param headers: Optional request-specific headers.
            :param params: Optional query parameters.
            :param follow_redirects: Whether to follow redirects.

            :returns: A :class:`TestResponse` instance.
        """
        return self._make_request(
            "OPTIONS", path, params=params, headers=headers, follow_redirects=follow_redirects,
        )

    # -------------------------------------------------------------------------
    # Internal Request Handling
    # -------------------------------------------------------------------------

    def _make_request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Any] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[HeadersArgument] = None,
        content: Optional[Union[bytes, str]] = None,
        files: Optional[Dict[str, Any]] = None,
        follow_redirects: Optional[bool] = None,
    ) -> TestResponse:
        """
            Build and execute a request against the application.

            Merges default headers with request-specific headers.
            Handles cookie injection and extraction. Encodes the request
            body. When redirects are followed, each redirect response is
            recorded in the final response's ``history``.

            :param method: The HTTP method string.
            :param path: The request path.
            :param params: Optional query parameters.
            :param json: Optional JSON body.
            :param data: Optional form data body.
            :param headers: Optional request-specific headers.
            :param content: Optional raw body.
            :param files: Optional files for a multipart body.
            :param follow_redirects: Whether to follow redirects. ``None``
                uses the client's default.

            :returns: A :class:`TestResponse` instance.

            :raises TooManyRedirectsError: If more than
                :data:`MAX_REDIRECTS` redirects are followed.
        """
        if follow_redirects is None:
            follow_redirects = self._follow_redirects

        # Build the full path with query parameters
        full_path = self._build_path(path, params)

        # Encode the request body
        body, content_type = self._encode_request_body(json, data, content, files)

        history: List[TestResponse] = []

        current_method = method
        current_path = full_path
        current_body = body
        current_content_type = content_type
        current_headers = headers

        response = None

        while response is None:
            status_code, response_headers, chunks = self._send_once(
                current_method, current_path, current_headers,
                current_body, current_content_type,
            )

            candidate = TestResponse(
                status_code=status_code,
                headers=response_headers,
                body=b"".join(chunks),
                chunks=chunks,
                history=history,
            )

            location = candidate.get_header("Location")

            is_redirect = status_code in REDIRECT_STATUS_CODES and location is not None

            if not follow_redirects or not is_redirect:
                response = candidate
                break

            if len(history) >= MAX_REDIRECTS:
                errmsg = "Exceeded {} redirects; the last one pointed to '{}'.".format(
                    MAX_REDIRECTS, location
                )
                raise TooManyRedirectsError(errmsg)

            history.append(candidate)

            current_path = self._resolve_redirect(current_path, location)

            # 303 always becomes a GET; 301 and 302 do for a POST, as
            # browsers do. 307 and 308 repeat the request unchanged.
            becomes_get = status_code == 303 or (
                status_code in (301, 302) and current_method.upper() == "POST"
            )

            if becomes_get:
                if current_method.upper() != "HEAD":
                    current_method = "GET"
                current_body = b""
                current_content_type = None

        return response

    def _send_once(
        self,
        method: str,
        full_path: str,
        headers: Optional[HeadersArgument],
        body: bytes,
        content_type: Optional[str],
    ) -> Tuple[int, List[Tuple[str, str]], List[bytes]]:
        """
            Send one request through the transport and update the cookies.

            :param method: The HTTP method string.
            :param full_path: The request path with its query string.
            :param headers: Optional request-specific headers.
            :param body: The encoded request body.
            :param content_type: The content type of the body, if any.

            :returns: The status code, response headers and body pieces.
        """
        request_path = full_path.split("?", 1)[0]
        host_name = self._host.split(":", 1)[0]

        # Merge headers: defaults < cookies < auth < request-specific
        merged_headers = self._merge_headers(headers, request_path=request_path)

        if content_type is not None and not self._contains_header(merged_headers, "Content-Type"):
            merged_headers.append(("Content-Type", content_type))

        status_code, response_headers, chunks = self._transport.send(
            method, full_path, merged_headers, body, self._scheme, self._host,
        )

        # Update cookies from response
        self._cookies.update_from_headers(
            response_headers, request_path=request_path, request_host=host_name,
        )

        return status_code, response_headers, chunks

    def _resolve_redirect(self, current_path: str, location: str) -> str:
        """
            Turn a ``Location`` header into the next request path.

            An absolute URL is reduced to its path and query; a relative
            reference is resolved against the current path.

            :param current_path: The path of the request that was redirected.
            :param location: The value of the ``Location`` header.

            :returns: The path, with query string, of the next request.
        """
        from urllib.parse import urljoin

        current_url = "{}://{}{}".format(self._scheme, self._host, current_path)
        target_parts = urlsplit(urljoin(current_url, location))

        next_path = target_parts.path or "/"

        if target_parts.query:
            next_path = "{}?{}".format(next_path, target_parts.query)

        return next_path

    def _build_path(
        self,
        path: str,
        params: Optional[Dict[str, Any]],
    ) -> str:
        """
            Build the full request path with query parameters.

            :param path: The base path.
            :param params: Optional query parameters dictionary.

            :returns: The full path string.
        """
        if params is None or len(params) == 0:
            return path

        query_string = urlencode(params, doseq=True)
        separator = "&" if "?" in path else "?"
        full_path = "{}{}{}".format(path, separator, query_string)

        return full_path

    def _contains_header(self, headers: List[Tuple[str, str]], name: str) -> bool:
        """
            Check whether a header list contains a header, ignoring case.

            :param headers: The header list.
            :param name: The header name.

            :returns: ``True`` if the header is present.
        """
        lower_name = name.lower()

        for header_name, _header_value in headers:
            if header_name.lower() == lower_name:
                return True

        return False

    def _merge_headers(
        self,
        request_headers: Optional[HeadersArgument],
        request_path: Optional[str] = None,
    ) -> List[Tuple[str, str]]:
        """
            Merge default headers, cookies, authentication, and
            request-specific headers into a single header list.

            Request-specific headers take highest precedence, followed
            by authentication, then cookies, then defaults. A later
            source replaces a header of the same name from an earlier
            one. Request-specific headers given as a list of tuples may
            repeat a name; all of them are sent.

            :param request_headers: Optional request-specific headers.
            :param request_path: The path of the request, used to select
                the cookies that apply to it.

            :returns: The merged headers as a list of (name, value) tuples.
        """
        merged: Dict[str, Tuple[str, str]] = {}

        for name, value in self._default_headers.items():
            merged[name.lower()] = (name, value)

        # Add cookie header
        host_name = self._host.split(":", 1)[0]
        cookie_value = self._cookies.to_header(
            path=request_path, host=host_name, scheme=self._scheme,
        )
        if cookie_value:
            merged["cookie"] = ("Cookie", cookie_value)

        # Add authentication header
        if self._auth_header is not None:
            auth_name, auth_value = self._auth_header
            merged[auth_name.lower()] = (auth_name, auth_value)

        # Request-specific headers override everything
        repeated: List[Tuple[str, str]] = []

        if request_headers is not None:
            if isinstance(request_headers, dict):
                request_pairs = list(request_headers.items())
            else:
                request_pairs = list(request_headers)

            seen_in_request = set()

            for name, value in request_pairs:
                lower_name = name.lower()

                if lower_name in seen_in_request:
                    repeated.append((name, value))
                else:
                    seen_in_request.add(lower_name)
                    merged[lower_name] = (name, value)

        header_list = list(merged.values()) + repeated

        return header_list

    def _encode_request_body(
        self,
        json: Optional[Any],
        data: Optional[Dict[str, Any]],
        content: Optional[Union[bytes, str]],
        files: Optional[Dict[str, Any]],
    ) -> Tuple[bytes, Optional[str]]:
        """
            Encode the request body from whichever form was given.

            Raw *content* is sent as it is. *files* produce a
            ``multipart/form-data`` body that also carries the *data*
            fields. Otherwise the body is encoded by :meth:`_encode_body`.

            :param json: Optional JSON-serializable value.
            :param data: Optional form data dictionary.
            :param content: Optional raw body.
            :param files: Optional files for a multipart body.

            :returns: A tuple of (body_bytes, content_type_string).
        """
        if content is not None:
            if isinstance(content, str):
                return content.encode("utf-8"), "text/plain; charset=utf-8"
            return bytes(content), None

        if files is not None:
            return self._encode_multipart(data, files)

        return self._encode_body(json, data)

    def _encode_multipart(
        self,
        data: Optional[Dict[str, Any]],
        files: Dict[str, Any],
    ) -> Tuple[bytes, str]:
        """
            Encode form fields and files as ``multipart/form-data``.

            :param data: Optional form fields sent alongside the files.
            :param files: The files, keyed by field name. Each value is the
                content (``bytes`` or a binary file object) or a tuple of
                ``(filename, content)`` or ``(filename, content, content_type)``.

            :returns: A tuple of (body_bytes, content_type_string).
        """
        boundary = "testclient-{}".format(uuid.uuid4().hex)
        boundary_bytes = boundary.encode("ascii")

        parts: List[bytes] = []

        if data is not None:
            for field_name, field_value in data.items():
                parts.append(b"--" + boundary_bytes + b"\r\n")
                parts.append(
                    'Content-Disposition: form-data; name="{}"\r\n\r\n'.format(
                        self._quote_parameter(field_name)
                    ).encode("utf-8")
                )
                parts.append(str(field_value).encode("utf-8"))
                parts.append(b"\r\n")

        for field_name, file_spec in files.items():
            filename = field_name
            file_content_type = "application/octet-stream"

            if isinstance(file_spec, tuple):
                filename = file_spec[0]
                file_content = file_spec[1]
                if len(file_spec) > 2 and file_spec[2] is not None:
                    file_content_type = file_spec[2]
            else:
                file_content = file_spec

            if hasattr(file_content, "read"):
                file_content = file_content.read()

            if isinstance(file_content, str):
                file_content = file_content.encode("utf-8")

            parts.append(b"--" + boundary_bytes + b"\r\n")
            parts.append(
                'Content-Disposition: form-data; name="{}"; filename="{}"\r\n'.format(
                    self._quote_parameter(field_name), self._quote_parameter(filename)
                ).encode("utf-8")
            )
            parts.append("Content-Type: {}\r\n\r\n".format(file_content_type).encode("utf-8"))
            parts.append(bytes(file_content))
            parts.append(b"\r\n")

        parts.append(b"--" + boundary_bytes + b"--\r\n")

        body = b"".join(parts)
        content_type = "multipart/form-data; boundary={}".format(boundary)

        return body, content_type

    def _quote_parameter(self, value: str) -> str:
        """
            Escape a value for use inside a quoted header parameter.

            :param value: The field name or file name.

            :returns: The value with quotes and line breaks made harmless.
        """
        quoted = str(value).replace("\\", "\\\\").replace('"', '\\"')
        quoted = quoted.replace("\r", " ").replace("\n", " ")

        return quoted

    def _encode_body(
        self,
        json: Optional[Any],
        data: Optional[Dict[str, Any]],
    ) -> Tuple[bytes, Optional[str]]:
        """
            Encode the request body from JSON or form data.

            If *json* is provided, the body is JSON-encoded and the
            content type is ``application/json``. If *data* is provided,
            the body is URL-encoded and the content type is
            ``application/x-www-form-urlencoded``. If neither is
            provided, the body is empty bytes.

            :param json: Optional JSON-serializable value.
            :param data: Optional form data dictionary.

            :returns: A tuple of (body_bytes, content_type_string).
        """
        if json is not None:
            body = _json_module.dumps(json).encode("utf-8")
            content_type = "application/json"
            return body, content_type

        if data is not None:
            body = urlencode(data, doseq=True).encode("utf-8")
            content_type = "application/x-www-form-urlencoded"
            return body, content_type

        return b"", None
