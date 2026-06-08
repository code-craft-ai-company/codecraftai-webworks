"""
    HTTP test client for in-process endpoint testing.

    This module provides the :class:`TestClient` class that executes
    HTTP requests against an application callable without starting a
    real server. It supports all standard HTTP methods, JSON and form
    data request bodies, custom headers, query parameters, cookie
    persistence via :class:`CookieJar`, and authentication helpers.

    The application callable must accept the signature::

        (method, path, headers, body) -> (status_code, headers, body)

    where *method* is a string, *path* is the full path with query
    string, *headers* is a ``dict``, *body* is ``bytes``, and the
    return value is a tuple of ``(int, dict, bytes)``.
"""

import json as _json_module

from typing import Any, Callable, Dict, List, Optional, Tuple
from urllib.parse import urlencode, quote as url_quote

from ccai.webworks.devexp.testing.testresponse import TestResponse


# =============================================================================
# CookieJar
# =============================================================================

class CookieJar:
    """
        A simple cookie jar that stores cookies as name-value pairs
        and persists them across multiple :class:`TestClient` requests.
    """

    def __init__(self):
        """
            Construct an empty CookieJar.
        """
        self._cookies: Dict[str, str] = {}
        return

    @property
    def cookies(self) -> Dict[str, str]:
        """
            All stored cookies as a dictionary.

            :returns: A copy of the cookie name-value pairs.
        """
        return dict(self._cookies)

    def set(self, name: str, value: str) -> None:
        """
            Set a cookie.

            :param name: The cookie name.
            :param value: The cookie value.
        """
        self._cookies[name] = value
        return

    def get(self, name: str, default: Optional[str] = None) -> Optional[str]:
        """
            Get a cookie value by name.

            :param name: The cookie name.
            :param default: Value to return if the cookie is not found.

            :returns: The cookie value or the default.
        """
        return self._cookies.get(name, default)

    def delete(self, name: str) -> None:
        """
            Delete a cookie by name.

            :param name: The cookie name to remove.
        """
        self._cookies.pop(name, None)
        return

    def clear(self) -> None:
        """
            Remove all cookies.
        """
        self._cookies.clear()
        return

    def to_header(self) -> str:
        """
            Format all cookies as a ``Cookie`` header value.

            :returns: A string in the form ``name1=value1; name2=value2``.
        """
        if not self._cookies:
            return ""

        parts = []
        for name, value in self._cookies.items():
            parts.append("{}={}".format(name, value))

        header_value = "; ".join(parts)

        return header_value

    def update_from_headers(self, headers: Dict[str, str]) -> None:
        """
            Extract ``Set-Cookie`` headers and store the cookies.

            Handles both single and multiple ``Set-Cookie`` values.
            Only the cookie name and value are extracted; attributes
            such as ``Path``, ``Domain``, and ``Expires`` are ignored.

            :param headers: The response headers dictionary.
        """
        for header_name, header_value in headers.items():
            if header_name.lower() == "set-cookie":
                self._parse_set_cookie(header_value)

        return

    def _parse_set_cookie(self, header_value: str) -> None:
        """
            Parse a single Set-Cookie header value and store the cookie.

            :param header_value: The Set-Cookie header value string.
        """
        # The cookie name=value is the first segment before any semicolon
        parts = header_value.split(";")
        if not parts:
            return

        name_value = parts[0].strip()
        if "=" not in name_value:
            return

        eq_index = name_value.index("=")
        name = name_value[:eq_index].strip()
        value = name_value[eq_index + 1:].strip()

        if name:
            self._cookies[name] = value

        return


# =============================================================================
# TestClient
# =============================================================================

class TestClient:
    """
        HTTP client for testing endpoints without a real server.

        The client executes requests in-process by calling the
        application callable directly. It manages default headers,
        cookie persistence, and optional authentication.

        The application callable must accept::

            (method, path, headers, body) -> (status_code, headers, body)

        :param app: The application callable to test against.
        :param default_headers: Optional default headers sent with
            every request.
    """

    def __init__(
        self,
        app: Callable,
        default_headers: Optional[Dict[str, str]] = None,
    ):
        """
            Construct a TestClient.

            :param app: The application callable.
            :param default_headers: Default headers to include in
                every request.
        """
        self._app = app
        self._default_headers: Dict[str, str] = dict(default_headers or {})
        self._cookies = CookieJar()
        self._auth: Optional[Tuple[str, str]] = None
        self._auth_header: Optional[Tuple[str, str]] = None
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

    def get(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> TestResponse:
        """
            Send a GET request.

            :param path: The request path.
            :param params: Optional query parameters.
            :param headers: Optional request-specific headers.

            :returns: A :class:`TestResponse` instance.
        """
        return self._make_request("GET", path, params=params, headers=headers)

    def post(
        self,
        path: str,
        json: Optional[Any] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> TestResponse:
        """
            Send a POST request.

            :param path: The request path.
            :param json: Optional JSON body.
            :param data: Optional form data body.
            :param headers: Optional request-specific headers.

            :returns: A :class:`TestResponse` instance.
        """
        return self._make_request("POST", path, json=json, data=data, headers=headers)

    def put(
        self,
        path: str,
        json: Optional[Any] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> TestResponse:
        """
            Send a PUT request.

            :param path: The request path.
            :param json: Optional JSON body.
            :param data: Optional form data body.
            :param headers: Optional request-specific headers.

            :returns: A :class:`TestResponse` instance.
        """
        return self._make_request("PUT", path, json=json, data=data, headers=headers)

    def patch(
        self,
        path: str,
        json: Optional[Any] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> TestResponse:
        """
            Send a PATCH request.

            :param path: The request path.
            :param json: Optional JSON body.
            :param data: Optional form data body.
            :param headers: Optional request-specific headers.

            :returns: A :class:`TestResponse` instance.
        """
        return self._make_request("PATCH", path, json=json, data=data, headers=headers)

    def delete(
        self,
        path: str,
        headers: Optional[Dict[str, str]] = None,
    ) -> TestResponse:
        """
            Send a DELETE request.

            :param path: The request path.
            :param headers: Optional request-specific headers.

            :returns: A :class:`TestResponse` instance.
        """
        return self._make_request("DELETE", path, headers=headers)

    def head(
        self,
        path: str,
        headers: Optional[Dict[str, str]] = None,
    ) -> TestResponse:
        """
            Send a HEAD request.

            :param path: The request path.
            :param headers: Optional request-specific headers.

            :returns: A :class:`TestResponse` instance.
        """
        return self._make_request("HEAD", path, headers=headers)

    def options(
        self,
        path: str,
        headers: Optional[Dict[str, str]] = None,
    ) -> TestResponse:
        """
            Send an OPTIONS request.

            :param path: The request path.
            :param headers: Optional request-specific headers.

            :returns: A :class:`TestResponse` instance.
        """
        return self._make_request("OPTIONS", path, headers=headers)

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
        headers: Optional[Dict[str, str]] = None,
    ) -> TestResponse:
        """
            Build and execute a request against the application.

            Merges default headers with request-specific headers.
            Handles cookie injection and extraction. Encodes JSON
            and form data bodies as appropriate.

            :param method: The HTTP method string.
            :param path: The request path.
            :param params: Optional query parameters.
            :param json: Optional JSON body.
            :param data: Optional form data body.
            :param headers: Optional request-specific headers.

            :returns: A :class:`TestResponse` instance.
        """
        # Build the full path with query parameters
        full_path = self._build_path(path, params)

        # Merge headers: defaults < auth < cookies < request-specific
        merged_headers = self._merge_headers(headers)

        # Encode the request body
        body, content_type = self._encode_body(json, data)

        if content_type is not None and "Content-Type" not in merged_headers:
            merged_headers["Content-Type"] = content_type

        # Call the application
        status_code, response_headers, response_body = self._app(
            method, full_path, merged_headers, body,
        )

        # Update cookies from response
        self._cookies.update_from_headers(response_headers)

        # Build and return the response
        response = TestResponse(
            status_code=status_code,
            headers=response_headers,
            body=response_body,
        )

        return response

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

        query_string = urlencode(params)
        separator = "&" if "?" in path else "?"
        full_path = "{}{}{}".format(path, separator, query_string)

        return full_path

    def _merge_headers(
        self,
        request_headers: Optional[Dict[str, str]],
    ) -> Dict[str, str]:
        """
            Merge default headers, authentication, cookies, and
            request-specific headers into a single dictionary.

            Request-specific headers take highest precedence, followed
            by authentication, then cookies, then defaults.

            :param request_headers: Optional request-specific headers.

            :returns: The merged headers dictionary.
        """
        merged = dict(self._default_headers)

        # Add cookie header
        cookie_value = self._cookies.to_header()
        if cookie_value:
            merged["Cookie"] = cookie_value

        # Add authentication header
        if self._auth_header is not None:
            auth_name, auth_value = self._auth_header
            merged[auth_name] = auth_value

        # Request-specific headers override everything
        if request_headers is not None:
            merged.update(request_headers)

        return merged

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
            body = urlencode(data).encode("utf-8")
            content_type = "application/x-www-form-urlencoded"
            return body, content_type

        return b"", None
