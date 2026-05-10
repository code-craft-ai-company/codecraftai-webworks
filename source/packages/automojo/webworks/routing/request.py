"""
    Request module.
    
    This module provides the Request class for abstracting over WSGI/ASGI
    request objects, providing a clean API for accessing headers, body,
    query parameters, and path parameters.
"""

import json
import logging
from http.cookies import SimpleCookie
from typing import Any, Dict, Optional
from urllib.parse import parse_qs, urlencode

from automojo.webworks.authentication.core import AuthenticationContext
from automojo.webworks.routing.headers import Headers
from automojo.webworks.routing.queryparams import QueryParams

# Avoid circular import; use TYPE_CHECKING for MiddlewareContext
# and UploadedFile (the latter to keep the email parser cost out of
# the import-time critical path — see the lazy imports inside
# :meth:`form` / :meth:`files`).
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from automojo.webworks.routing.middlewarecontext import MiddlewareContext
    from automojo.webworks.routing.multipart import UploadedFile


# Module-level logger. Body parsing, cookie parsing, and port
# coercion failures are all swallowed by the Request class to keep
# the request handler from blowing up on malformed input — but the
# operator still wants the breadcrumb in the journal so a sudden
# spike of unparseable cookies / Content-Length values is visible.
logger = logging.getLogger(__name__)


class Request:
    """
        Abstraction over WSGI/ASGI request providing clean access to
        request data without exposing raw protocol details.
    """
    
    def __init__(
        self,
        method: str,
        path: str,
        query_string: bytes = b"",
        headers: Optional[Dict[str, str]] = None,
        body: bytes = b"",
        scheme: str = "http",
        host: str = "localhost",
        port: int = 80,
        scope: Optional[Dict[str, Any]] = None
    ):
        """
            Construct a Request from components.

            For WSGI/ASGI construction, use from_wsgi() or from_asgi().

            :param method: HTTP method (GET, POST, etc.).
            :param path: Request path without query string.
            :param query_string: Query string as bytes (without leading '?').
            :param headers: Optional dictionary of header names to values.
            :param body: Request body as bytes.
            :param scheme: URL scheme (http or https).
            :param host: Server hostname.
            :param port: Server port.
            :param scope: Optional underlying ASGI / WSGI scope dict.
                          When supplied, it is exposed read-only via
                          :attr:`scope` so middleware-injected keys
                          (e.g. ``"auth"`` populated by
                          :class:`AuthenticationMiddleware`) can be
                          read directly from the request. Defaults to
                          an empty dict for direct construction (tests).
        """
        self._method = method.upper()
        self._path = path
        self._query_string = query_string
        self._headers = Headers(headers)
        self._body = body
        self._scheme = scheme
        self._host = host
        self._port = port
        self._path_params: Dict[str, Any] = {}
        self._middleware_context: Optional["MiddlewareContext"] = None
        self._scope: Dict[str, Any] = scope if scope is not None else {}

        # Lazily initialized
        self._query_params: Optional[QueryParams] = None
        self._cookies: Optional[Dict[str, str]] = None
        self._background_tasks: Optional[Any] = None
        return
    
    @classmethod
    def from_wsgi(cls, environ: Dict[str, Any]) -> "Request":
        """
            Construct Request from WSGI environ dict.
            
            :param environ: WSGI environ dictionary.
            
            :returns: Request instance.
        """
        # Extract HTTP method
        method = environ.get("REQUEST_METHOD", "GET")
        
        # Extract path
        path = environ.get("PATH_INFO", "/")
        
        # Extract query string
        query_string_str = environ.get("QUERY_STRING", "")
        query_string = query_string_str.encode("utf-8") if query_string_str else b""
        
        # Extract headers from environ
        # WSGI headers are prefixed with HTTP_ (except Content-Type and Content-Length)
        headers: Dict[str, str] = {}
        for key, value in environ.items():
            if key.startswith("HTTP_"):
                # Convert HTTP_CONTENT_TYPE to Content-Type
                header_name = key[5:].replace("_", "-").title()
                headers[header_name] = value
            elif key == "CONTENT_TYPE" and value:
                headers["Content-Type"] = value
            elif key == "CONTENT_LENGTH" and value:
                headers["Content-Length"] = value
        
        # Extract body from wsgi.input
        body = b""
        wsgi_input = environ.get("wsgi.input")
        if wsgi_input is not None:
            content_length_str = environ.get("CONTENT_LENGTH", "")
            if content_length_str:
                try:
                    content_length = int(content_length_str)
                    body = wsgi_input.read(content_length)
                except (ValueError, TypeError) as exc:
                    # Bad Content-Length — fall back to a full read so
                    # the handler still sees the body, but the
                    # operator gets a breadcrumb pointing at the
                    # malformed header.
                    logger.warning(
                        "Request.from_wsgi: invalid CONTENT_LENGTH=%r (%s); "
                        "falling back to full wsgi.input read",
                        content_length_str,
                        exc,
                    )
                    body = wsgi_input.read()
            else:
                # Try to read without content length
                try:
                    body = wsgi_input.read()
                except Exception as exc:
                    # wsgi.input may have been exhausted or closed by
                    # an upstream component; emit a warning so a
                    # silently-empty body stops being mysterious.
                    logger.warning(
                        "Request.from_wsgi: failed to read wsgi.input: %s", exc
                    )
                    body = b""
        
        # Extract scheme
        scheme = environ.get("wsgi.url_scheme", "http")
        
        # Extract host and port
        host = environ.get("SERVER_NAME", "localhost")
        port_str = environ.get("SERVER_PORT", "80")
        try:
            port = int(port_str)
        except (ValueError, TypeError) as exc:
            # SERVER_PORT was non-integer — defaulting to 80 keeps
            # the request usable but the operator should know the
            # WSGI environ was malformed.
            logger.warning(
                "Request.from_wsgi: invalid SERVER_PORT=%r (%s); defaulting to 80",
                port_str,
                exc,
            )
            port = 80
        
        request = cls(
            method=method,
            path=path,
            query_string=query_string,
            headers=headers,
            body=body,
            scheme=scheme,
            host=host,
            port=port,
            scope=environ
        )
        return request


    @classmethod
    def from_asgi(cls, scope: Dict[str, Any], body: bytes = b"") -> "Request":
        """
            Construct Request from ASGI scope dict.
            
            :param scope: ASGI scope dictionary.
            :param body: Request body as bytes (must be provided separately in ASGI).
            
            :returns: Request instance.
        """
        # Extract HTTP method
        method = scope.get("method", "GET")
        
        # Extract path
        path = scope.get("path", "/")
        
        # Extract query string
        query_string = scope.get("query_string", b"")
        if isinstance(query_string, str):
            query_string = query_string.encode("utf-8")
        
        # Extract headers from ASGI format
        # ASGI headers are a list of [name, value] pairs as bytes
        headers: Dict[str, str] = {}
        raw_headers = scope.get("headers", [])
        for header_pair in raw_headers:
            if len(header_pair) >= 2:
                name = header_pair[0]
                value = header_pair[1]
                # Decode bytes to string
                if isinstance(name, bytes):
                    name = name.decode("latin-1")
                if isinstance(value, bytes):
                    value = value.decode("latin-1")
                headers[name] = value
        
        # Extract scheme
        scheme = scope.get("scheme", "http")
        
        # Extract host and port from server tuple
        server = scope.get("server")
        if server is not None and len(server) >= 2:
            host = server[0]
            port = server[1]
        else:
            host = "localhost"
            port = 80

        request = cls(
            method=method,
            path=path,
            query_string=query_string,
            headers=headers,
            body=body,
            scheme=scheme,
            host=host,
            port=port,
            scope=scope
        )
        return request
    
    @property
    def scope(self) -> Dict[str, Any]:
        """
            The underlying ASGI scope (or WSGI ``environ``) the
            request was constructed from.

            Exposes the same dict that the application server gave to
            :meth:`from_asgi` / :meth:`from_wsgi`. Middleware that
            stashes data on the scope dict — typically the
            authentication, session, or rate-limit middleware —
            makes that data available here so handlers can read it
            without reaching for a separate side-channel.

            For requests constructed directly via the public
            constructor (e.g. unit tests), the value is the ``scope``
            dict supplied as a keyword argument, or an empty dict
            when none was provided.

            The dict is intentionally exposed by reference rather
            than by copy so middleware-side mutations are visible to
            handlers (this is the contract every ASGI scope
            consumer relies on). Consumers should treat the dict as
            read-only by convention; mutations should go through the
            originating middleware, not directly here.

            For typed shortcuts to specific keys, use the dedicated
            property (e.g. :attr:`auth` for ``scope["auth"]``); reach
            for the dict for keys that don't have one yet.

            :returns: The scope dict (never ``None``).
        """
        rtnval = self._scope
        return rtnval

    @property
    def auth(self) -> Optional[AuthenticationContext]:
        """
            Authentication context resolved for this request, or
            ``None``.

            Typed shortcut for ``self.scope.get("auth")``.
            :class:`AuthenticationMiddleware` writes the resolved
            :class:`AuthenticationContext` to ``scope["auth"]``
            after the :class:`AuthenticationSystem` runs. ``None``
            is written for excluded paths and for optional paths
            where authentication didn't succeed.

            ``None`` is also returned for requests constructed
            without scope context (direct unit-test construction,
            requests synthesised from a non-middleware code path).

            Defensive type check: when ``scope["auth"]`` is set but
            isn't an :class:`AuthenticationContext` (a misbehaving
            third-party middleware, for example), this property
            returns ``None`` rather than mis-reporting a typed
            value.  Code that wants to inspect non-conforming
            ``scope["auth"]`` payloads should read them via
            :attr:`scope` directly.

            :returns: The bound :class:`AuthenticationContext`, or
                      ``None``.
        """
        candidate = self._scope.get("auth")
        if isinstance(candidate, AuthenticationContext):
            return candidate
        return None

    @property
    def query_string(self) -> str:
        """
            Get the query string as a string.

            :returns: Query string without leading '?'.
        """
        rtnval = self._query_string.decode("utf-8", errors="replace")
        return rtnval

    @property
    def raw_query_string(self) -> bytes:
        """
            Get the raw query string as bytes.

            :returns: Raw query string without leading '?'.
        """
        rtnval = self._query_string
        return rtnval

    @property
    def scheme(self) -> str:
        """
            Get the URL scheme.

            :returns: URL scheme string ('http' or 'https').
        """
        rtnval = self._scheme
        return rtnval

    @property
    def host(self) -> str:
        """
            Get the server host.

            :returns: Server host string.
        """
        rtnval = self._host
        return rtnval

    @property
    def port(self) -> int:
        """
            Get the server port.

            :returns: Server port number.
        """
        rtnval = self._port
        return rtnval

    @property
    def content_type(self) -> Optional[str]:
        """
            Get the Content-Type header.

            :returns: Content-Type string or None.
        """
        rtnval = self._headers.get("Content-Type")
        return rtnval

    @property
    def content_length(self) -> Optional[int]:
        """
            Get the Content-Length header.

            :returns: Content-Length as integer or None.
        """
        value = self._headers.get("Content-Length")
        if not value:
            return None
        try:
            rtnval = int(value)
            return rtnval
        except (TypeError, ValueError):
            return None

    @property
    def background_tasks(self) -> Optional[Any]:
        """
            Get the background tasks manager for this request.

            :returns: BackgroundTasks instance or None.
        """
        rtnval = self._background_tasks
        return rtnval

    @background_tasks.setter
    def background_tasks(self, value: Optional[Any]) -> None:
        """
            Set the background tasks manager for this request.

            :param value: BackgroundTasks instance.
        """
        self._background_tasks = value
        return

    def get_header(self, name: str, default: Optional[str] = None) -> Optional[str]:
        """
            Get a header value by name (case-insensitive).

            :param name: Header name.
            :param default: Default value if header not found.

            :returns: Header value or default.
        """
        # Headers are stored with title case, so normalize the lookup
        normalized_name = name.title()
        rtnval = self._headers.get(normalized_name, default)
        return rtnval

    def as_dict(self, brief: bool = False) -> Dict[str, Any]:
        """
            Convert the request to a dictionary representation.

            :param brief: If True, return a simplified representation.

            :returns: Dictionary representation of the request.
        """
        if brief:
            rtnval = {
                "method": self._method,
                "path": self._path,
                "url": self.url,
            }
        else:
            rtnval = {
                "method": self._method,
                "path": self._path,
                "query_string": self.query_string,
                "headers": dict(self._headers.items()),
                "body_length": len(self._body),
                "scheme": self._scheme,
                "host": self._host,
                "port": self._port,
                "content_type": self.content_type,
                "content_length": self.content_length,
                "url": self.url,
            }

        return rtnval

    @property
    def method(self) -> str:
        """
            HTTP method (GET, POST, etc.).
            
            :returns: HTTP method string in uppercase.
        """
        rtnval = self._method
        return rtnval
    
    @property
    def path(self) -> str:
        """
            Request path without query string.
            
            :returns: Request path string.
        """
        rtnval = self._path
        return rtnval
    
    @property
    def query_params(self) -> QueryParams:
        """
            Query parameters as dict-like object.
            
            :returns: QueryParams instance.
        """
        if self._query_params is None:
            self._query_params = QueryParams(self._query_string)
        rtnval = self._query_params
        return rtnval
    
    @property
    def headers(self) -> Headers:
        """
            Request headers as case-insensitive dict-like object.
            
            :returns: Headers instance.
        """
        rtnval = self._headers
        return rtnval
    
    @property
    def body(self) -> bytes:
        """
            Raw request body as bytes.
            
            :returns: Request body bytes.
        """
        rtnval = self._body
        return rtnval
    
    def json(self) -> Any:
        """
            Parse body as JSON and return Python object.
            
            :returns: Parsed JSON as Python object.
            
            :raises json.JSONDecodeError: If body is not valid JSON.
        """
        body_str = self._body.decode("utf-8")
        rtnval = json.loads(body_str)
        return rtnval
    
    def form(self) -> Dict[str, str]:
        """
            Parse the body as form data and return the form fields as
            a flat ``dict``.

            Two body shapes are recognised:

              * ``application/x-www-form-urlencoded`` — the body is
                URL-decoded and split on ``&`` / ``=``.
              * ``multipart/form-data`` — the body is parsed by
                :func:`automojo.webworks.routing.multipart.parse_multipart`.
                Only the *form-field* parts (no ``filename``) are
                surfaced here; uploaded files are read separately
                via :meth:`files`.

            For both shapes, when a field appears more than once,
            the **first** occurrence wins (matching the long-standing
            behaviour of this method). Consumers that need
            duplicate-name semantics should call
            :func:`parse_multipart` directly and walk
            :attr:`MultipartResult.form_parts`.

            :returns: Dict of field name to first-value string.
                      Empty dict for non-form bodies (JSON, etc.) or
                      when the body could not be parsed.
        """
        content_type_header = self._headers.get("Content-Type", "") or ""
        content_type_lower = str(content_type_header).split(";", 1)[0].strip().lower()

        if content_type_lower == "multipart/form-data":
            from automojo.webworks.routing.multipart import parse_multipart

            multipart_result = parse_multipart(
                body=self._body,
                content_type=str(content_type_header),
            )

            rtnval: Dict[str, str] = {}
            for field_name, value in multipart_result.form_parts:
                if field_name not in rtnval:
                    rtnval[field_name] = value

            return rtnval

        body_str = self._body.decode("utf-8")
        parsed = parse_qs(body_str, keep_blank_values=True)
        # Convert lists to single values (first value)
        rtnval = {}
        for key, values in parsed.items():
            if len(values) > 0:
                rtnval[key] = values[0]
        return rtnval

    def files(self) -> Dict[str, "UploadedFile"]:
        """
            Parse the body as ``multipart/form-data`` and return the
            uploaded files keyed by form-field name.

            Returns an empty dict for non-multipart bodies, so
            callers can unconditionally read this method without a
            content-type pre-check. When a file part appears more
            than once under the same field name, the **last**
            occurrence wins; consumers that need every part should
            call :func:`parse_multipart` directly and walk
            :attr:`MultipartResult.file_parts`.

            :returns: Dict of form-field name to
                      :class:`UploadedFile`. Empty dict for
                      non-multipart bodies.
        """
        from automojo.webworks.routing.multipart import (
            UploadedFile as _UploadedFile,
            parse_multipart,
        )

        content_type_header = self._headers.get("Content-Type", "") or ""
        content_type_lower = str(content_type_header).split(";", 1)[0].strip().lower()

        if content_type_lower != "multipart/form-data":
            empty: Dict[str, "_UploadedFile"] = {}
            return empty

        multipart_result = parse_multipart(
            body=self._body,
            content_type=str(content_type_header),
        )

        rtnval = multipart_result.files
        return rtnval
    
    @property
    def path_params(self) -> Dict[str, Any]:
        """
            Path parameters extracted during routing.
            
            :returns: Dictionary of path parameter names to values.
        """
        rtnval = self._path_params
        return rtnval
    
    @path_params.setter
    def path_params(self, value: Dict[str, Any]) -> None:
        """
            Set path parameters (called by dispatcher after routing).
            
            :param value: Dictionary of path parameter names to values.
        """
        self._path_params = value
        return
    
    @property
    def middleware_context(self) -> Optional["MiddlewareContext"]:
        """
            Middleware context attached during pipeline execution.
            
            :returns: The MiddlewareContext instance or None.
        """
        rtnval = self._middleware_context
        return rtnval
    
    @middleware_context.setter
    def middleware_context(self, value: Optional["MiddlewareContext"]) -> None:
        """
            Set the middleware context (called by dispatcher before pipeline execution).
            
            :param value: The MiddlewareContext instance or None.
        """
        self._middleware_context = value
        return
    
    @property
    def cookies(self) -> Dict[str, str]:
        """
            Request cookies parsed from Cookie header.
            
            :returns: Dictionary of cookie names to values.
        """
        if self._cookies is None:
            self._cookies = {}
            cookie_header = self._headers.get("Cookie", "")
            if cookie_header:
                simple_cookie = SimpleCookie()
                try:
                    simple_cookie.load(cookie_header)
                    for key, morsel in simple_cookie.items():
                        self._cookies[key] = morsel.value
                except Exception as exc:
                    # Malformed cookie header — return empty dict so
                    # the handler still works, but log enough context
                    # for the operator to spot a misbehaving client
                    # without leaking the cookie value itself.
                    logger.warning(
                        "Request.cookies: failed to parse Cookie header (path=%s): %s",
                        getattr(self, "_path", "<unknown>"),
                        exc,
                    )
        rtnval = self._cookies
        return rtnval
    
    @property
    def url(self) -> str:
        """
            Full request URL including scheme, host, path, and query.
            
            :returns: Full URL string.
        """
        # Build the URL
        url_parts = [self._scheme, "://", self._host]
        
        # Add port if non-standard
        if self._scheme == "http" and self._port != 80:
            url_parts.append(f":{self._port}")
        elif self._scheme == "https" and self._port != 443:
            url_parts.append(f":{self._port}")
        
        # Add path
        url_parts.append(self._path)
        
        # Add query string if present
        if self._query_string:
            query_str = self._query_string.decode("utf-8", errors="replace")
            url_parts.append("?")
            url_parts.append(query_str)
        
        rtnval = "".join(url_parts)
        return rtnval
    
    def __repr__(self) -> str:
        """
            Get string representation.
            
            :returns: String representation.
        """
        rtnval = f"Request({self._method} {self._path})"
        return rtnval
