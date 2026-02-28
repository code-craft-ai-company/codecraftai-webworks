"""
    Request module.
    
    This module provides the Request class for abstracting over WSGI/ASGI
    request objects, providing a clean API for accessing headers, body,
    query parameters, and path parameters.
"""

import json
from http.cookies import SimpleCookie
from typing import Any, Dict, Optional
from urllib.parse import parse_qs, urlencode

from automojo.webworks.routing.headers import Headers
from automojo.webworks.routing.queryparams import QueryParams


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
        port: int = 80
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
        
        # Lazily initialized
        self._query_params: Optional[QueryParams] = None
        self._cookies: Optional[Dict[str, str]] = None
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
                except (ValueError, TypeError):
                    body = wsgi_input.read()
            else:
                # Try to read without content length
                try:
                    body = wsgi_input.read()
                except Exception:
                    body = b""
        
        # Extract scheme
        scheme = environ.get("wsgi.url_scheme", "http")
        
        # Extract host and port
        host = environ.get("SERVER_NAME", "localhost")
        port_str = environ.get("SERVER_PORT", "80")
        try:
            port = int(port_str)
        except (ValueError, TypeError):
            port = 80
        
        request = cls(
            method=method,
            path=path,
            query_string=query_string,
            headers=headers,
            body=body,
            scheme=scheme,
            host=host,
            port=port
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
            port=port
        )
        return request
    
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
            Parse body as form-encoded data and return dict.
            
            :returns: Dictionary of form field names to values.
        """
        body_str = self._body.decode("utf-8")
        parsed = parse_qs(body_str, keep_blank_values=True)
        # Convert lists to single values (first value)
        rtnval: Dict[str, str] = {}
        for key, values in parsed.items():
            if len(values) > 0:
                rtnval[key] = values[0]
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
                except Exception:
                    # If parsing fails, return empty dict
                    pass
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
