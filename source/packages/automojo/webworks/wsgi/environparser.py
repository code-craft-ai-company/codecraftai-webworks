"""
    WSGI Environ Parser module.
    
    This module provides the EnvironParser class that parses WSGI environ dictionaries
    into framework Request objects, extracting HTTP method, path, query string, headers,
    body, and other request data.
    
    The EnvironParser integrates with RequestBodyParser to parse request bodies based
    on Content-Type header, supporting form-encoded, multipart, and JSON bodies.
"""

from typing import Any, Dict, Optional, Tuple, TYPE_CHECKING
from io import BytesIO

from automojo.webworks.wsgi.constants import (
    ENVIRON_REQUEST,
    ENVIRON_ROUTE,
    ENVIRON_PATH_PARAMS,
)
from automojo.webworks.wsgi.bodyparser import RequestBodyParser, UploadedFile


if TYPE_CHECKING:
    from automojo.webworks.wsgi.request import Request


class EnvironParser:
    """
        Parses WSGI environ dictionary into framework Request objects.
        
        This class extracts request data from the WSGI environ dictionary including
        HTTP method, path, query string, headers, body, scheme, host, and port.
        It also supports setting framework-specific environ keys.
    """
    
    # Default values for optional environ keys
    DEFAULT_METHOD: str = "GET"
    DEFAULT_PATH: str = "/"
    DEFAULT_QUERY_STRING: str = ""
    DEFAULT_SCHEME: str = "http"
    DEFAULT_HOST: str = "localhost"
    DEFAULT_PORT: int = 80
    DEFAULT_HTTPS_PORT: int = 443
    
    def __init__(self, max_body_size: int = 0):
        """
            Construct an environ parser.
            
            :param max_body_size: Maximum request body size in bytes (0 = unlimited).
        """
        self._max_body_size = max_body_size
        self._body_parser = RequestBodyParser(max_size=max_body_size)
        return
    
    @property
    def max_body_size(self) -> int:
        """
            Get the maximum body size limit.
            
            :returns: Maximum body size in bytes (0 = unlimited).
        """
        return self._max_body_size
    
    @property
    def body_parser(self) -> RequestBodyParser:
        """
            Get the request body parser.
            
            :returns: RequestBodyParser instance.
        """
        return self._body_parser
    
    def get_method(self, environ: Dict[str, Any]) -> str:
        """
            Extract HTTP method from environ.
            
            :param environ: WSGI environ dictionary.
            
            :returns: HTTP method string (e.g., 'GET', 'POST').
        """
        method = environ.get("REQUEST_METHOD", self.DEFAULT_METHOD)
        rtnval = str(method).upper()
        return rtnval
    
    def get_path(self, environ: Dict[str, Any]) -> str:
        """
            Extract request path from environ.
            
            :param environ: WSGI environ dictionary.
            
            :returns: Request path string (e.g., '/api/users').
        """
        path = environ.get("PATH_INFO", self.DEFAULT_PATH)
        rtnval = str(path) if path is not None else self.DEFAULT_PATH
        return rtnval
    
    def get_query_string(self, environ: Dict[str, Any]) -> str:
        """
            Extract query string from environ.
            
            :param environ: WSGI environ dictionary.
            
            :returns: Query string without leading '?' (e.g., 'id=1&name=test').
        """
        query_string = environ.get("QUERY_STRING", self.DEFAULT_QUERY_STRING)
        rtnval = str(query_string) if query_string is not None else self.DEFAULT_QUERY_STRING
        return rtnval
    
    def get_scheme(self, environ: Dict[str, Any]) -> str:
        """
            Extract URL scheme from environ.
            
            :param environ: WSGI environ dictionary.
            
            :returns: URL scheme string ('http' or 'https').
        """
        scheme = environ.get("wsgi.url_scheme", self.DEFAULT_SCHEME)
        rtnval = str(scheme).lower() if scheme is not None else self.DEFAULT_SCHEME
        return rtnval
    
    def get_host(self, environ: Dict[str, Any]) -> str:
        """
            Extract server host from environ.
            
            :param environ: WSGI environ dictionary.
            
            :returns: Server host string (e.g., 'localhost', 'example.com').
        """
        host = environ.get("SERVER_NAME", self.DEFAULT_HOST)
        rtnval = str(host) if host is not None else self.DEFAULT_HOST
        return rtnval
    
    def get_port(self, environ: Dict[str, Any]) -> int:
        """
            Extract server port from environ.
            
            :param environ: WSGI environ dictionary.
            
            :returns: Server port number.
        """
        port_str = environ.get("SERVER_PORT")
        
        if port_str is None:
            scheme = self.get_scheme(environ)
            if scheme == "https":
                rtnval = self.DEFAULT_HTTPS_PORT
            else:
                rtnval = self.DEFAULT_PORT
        else:
            try:
                rtnval = int(port_str)
            except (ValueError, TypeError):
                scheme = self.get_scheme(environ)
                if scheme == "https":
                    rtnval = self.DEFAULT_HTTPS_PORT
                else:
                    rtnval = self.DEFAULT_PORT
        
        return rtnval
    
    def get_headers(self, environ: Dict[str, Any]) -> Dict[str, str]:
        """
            Extract HTTP headers from environ.
            
            Converts HTTP_* keys to header names by removing the HTTP_ prefix
            and converting underscores to hyphens. Also includes CONTENT_TYPE
            and CONTENT_LENGTH which are not prefixed with HTTP_ in WSGI.
            
            :param environ: WSGI environ dictionary.
            
            :returns: Dictionary of header names to values.
        """
        headers: Dict[str, str] = {}
        
        # Extract HTTP_* prefixed headers
        for key, value in environ.items():
            if key.startswith("HTTP_"):
                # Convert HTTP_HEADER_NAME to Header-Name
                header_name = key[5:].replace("_", "-").title()
                headers[header_name] = str(value)
        
        # Handle CONTENT_TYPE specially (not prefixed with HTTP_ in WSGI)
        content_type = environ.get("CONTENT_TYPE")
        if content_type is not None:
            content_type_str = str(content_type)
            if len(content_type_str) > 0:
                headers["Content-Type"] = content_type_str
        
        # Handle CONTENT_LENGTH specially (not prefixed with HTTP_ in WSGI)
        content_length = environ.get("CONTENT_LENGTH")
        if content_length is not None:
            content_length_str = str(content_length)
            if len(content_length_str) > 0:
                headers["Content-Length"] = content_length_str
        
        return headers
    
    def get_content_type(self, environ: Dict[str, Any]) -> Optional[str]:
        """
            Extract Content-Type header from environ.
            
            :param environ: WSGI environ dictionary.
            
            :returns: Content-Type string or None if not present.
        """
        content_type = environ.get("CONTENT_TYPE")
        
        if content_type is None:
            rtnval = None
        else:
            content_type_str = str(content_type)
            if len(content_type_str) > 0:
                rtnval = content_type_str
            else:
                rtnval = None
        
        return rtnval
    
    def get_content_length(self, environ: Dict[str, Any]) -> Optional[int]:
        """
            Extract Content-Length header from environ.
            
            :param environ: WSGI environ dictionary.
            
            :returns: Content-Length as integer or None if not present or invalid.
        """
        content_length = environ.get("CONTENT_LENGTH")
        
        if content_length is None:
            rtnval = None
        else:
            content_length_str = str(content_length)
            if len(content_length_str) == 0:
                rtnval = None
            else:
                try:
                    rtnval = int(content_length_str)
                except (ValueError, TypeError):
                    rtnval = None
        
        return rtnval
    
    def get_body(self, environ: Dict[str, Any]) -> bytes:
        """
            Read request body from wsgi.input.
            
            Respects CONTENT_LENGTH if present. If CONTENT_LENGTH is not present,
            reads until EOF. Enforces max_body_size if configured.
            
            :param environ: WSGI environ dictionary.
            
            :returns: Request body as bytes.
            
            :raises RequestEntityTooLarge: If body exceeds max_body_size.
        """
        from automojo.webworks.wsgi.exceptions import RequestEntityTooLarge
        
        wsgi_input = environ.get("wsgi.input")
        
        if wsgi_input is None:
            rtnval = b""
            return rtnval
        
        content_length = self.get_content_length(environ)
        
        # Check size limit before reading if content length is known
        if content_length is not None:
            if self._max_body_size > 0 and content_length > self._max_body_size:
                raise RequestEntityTooLarge(self._max_body_size, content_length)
        
        if content_length is not None:
            # Read exactly content_length bytes
            body = wsgi_input.read(content_length)
        else:
            # No content length, read until EOF but respect max size
            if self._max_body_size > 0:
                # Read up to max_body_size + 1 to detect overflow
                body = wsgi_input.read(self._max_body_size + 1)
                if len(body) > self._max_body_size:
                    raise RequestEntityTooLarge(self._max_body_size, len(body))
            else:
                # No limit, read all
                body = wsgi_input.read()
        
        # Ensure we return bytes
        if isinstance(body, bytes):
            rtnval = body
        else:
            rtnval = body.encode("utf-8") if body is not None else b""
        
        return rtnval
    
    def parse_body(
        self,
        environ: Dict[str, Any]
    ) -> Tuple[bytes, Optional[Any]]:
        """
            Parse request body based on Content-Type.
            
            Uses the integrated RequestBodyParser to parse the body according
            to the Content-Type header. Supports:
            - application/x-www-form-urlencoded: Returns dict of form fields
            - multipart/form-data: Returns dict with 'fields' and 'files' keys
            - application/json: Returns parsed JSON value
            - Other types: Returns None for parsed_data
            
            :param environ: WSGI environ dictionary.
            
            :returns: Tuple of (raw_body, parsed_data).
                      parsed_data is None for unknown content types.
            
            :raises BadRequestBody: If body cannot be parsed.
            :raises RequestEntityTooLarge: If body exceeds max_body_size.
        """
        wsgi_input = environ.get("wsgi.input")
        
        if wsgi_input is None:
            rtnval = (b"", None)
            return rtnval
        
        content_type = self.get_content_type(environ)
        content_length = self.get_content_length(environ)
        
        raw_body, parsed_data = self._body_parser.parse(
            wsgi_input,
            content_type,
            content_length
        )
        
        rtnval = (raw_body, parsed_data)
        return rtnval
    
    def parse_form_body(
        self,
        environ: Dict[str, Any]
    ) -> Dict[str, str]:
        """
            Parse form-encoded request body.
            
            Convenience method for parsing application/x-www-form-urlencoded bodies.
            
            :param environ: WSGI environ dictionary.
            
            :returns: Dictionary of form field names to values.
            
            :raises BadRequestBody: If body cannot be parsed.
            :raises RequestEntityTooLarge: If body exceeds max_body_size.
        """
        body = self.get_body(environ)
        content_type = self.get_content_type(environ) or "application/x-www-form-urlencoded"
        
        rtnval = self._body_parser.parse_form(body, content_type)
        return rtnval
    
    def parse_json_body(
        self,
        environ: Dict[str, Any]
    ) -> Any:
        """
            Parse JSON request body.
            
            Convenience method for parsing application/json bodies.
            
            :param environ: WSGI environ dictionary.
            
            :returns: Parsed JSON value.
            
            :raises BadRequestBody: If JSON is invalid.
            :raises RequestEntityTooLarge: If body exceeds max_body_size.
        """
        body = self.get_body(environ)
        
        rtnval = self._body_parser.parse_json(body)
        return rtnval
    
    def parse_multipart_body(
        self,
        environ: Dict[str, Any]
    ) -> Tuple[Dict[str, str], Dict[str, UploadedFile]]:
        """
            Parse multipart form data request body.
            
            Convenience method for parsing multipart/form-data bodies.
            
            :param environ: WSGI environ dictionary.
            
            :returns: Tuple of (form_fields, uploaded_files).
            
            :raises BadRequestBody: If body cannot be parsed.
            :raises RequestEntityTooLarge: If body exceeds max_body_size.
        """
        wsgi_input = environ.get("wsgi.input")
        
        if wsgi_input is None:
            rtnval = ({}, {})
            return rtnval
        
        content_type = self.get_content_type(environ) or "multipart/form-data"
        content_length = self.get_content_length(environ)
        
        rtnval = self._body_parser.parse_multipart(
            wsgi_input,
            content_type,
            content_length
        )
        return rtnval

    def parse(self, environ: Dict[str, Any]) -> "Request":
        """
            Parse WSGI environ into a Request object.
            
            Combines all environ data into a Request object, handling missing
            optional keys with default values.
            
            :param environ: WSGI environ dictionary.
            
            :returns: Parsed Request object.
            
            :raises RequestEntityTooLarge: If body exceeds max_body_size.
        """
        from automojo.webworks.wsgi.request import Request
        
        method = self.get_method(environ)
        path = self.get_path(environ)
        query_string = self.get_query_string(environ)
        headers = self.get_headers(environ)
        body = self.get_body(environ)
        scheme = self.get_scheme(environ)
        host = self.get_host(environ)
        port = self.get_port(environ)
        content_type = self.get_content_type(environ)
        content_length = self.get_content_length(environ)
        
        request = Request(
            method=method,
            path=path,
            query_string=query_string,
            headers=headers,
            body=body,
            scheme=scheme,
            host=host,
            port=port,
            content_type=content_type,
            content_length=content_length
        )
        
        return request
    
    def set_framework_environ(
        self,
        environ: Dict[str, Any],
        request: "Request",
        route: Optional[Any] = None,
        path_params: Optional[Dict[str, Any]] = None
    ) -> None:
        """
            Set framework-specific environ keys.
            
            Sets the following keys in the environ dictionary:
            - webworks.request: The Request object
            - webworks.route: The matched route (if any)
            - webworks.path_params: Path parameters (if any)
            
            This method preserves any existing custom environ keys added by
            middleware. Only the framework-specific keys listed above are
            modified.
            
            :param environ: WSGI environ dictionary to modify.
            :param request: The Request object to store.
            :param route: The matched route (optional).
            :param path_params: Path parameters dictionary (optional).
        """
        environ[ENVIRON_REQUEST] = request
        
        if route is not None:
            environ[ENVIRON_ROUTE] = route
        
        if path_params is not None:
            environ[ENVIRON_PATH_PARAMS] = path_params
        else:
            environ[ENVIRON_PATH_PARAMS] = {}
        
        return
    
    def get_framework_environ(
        self,
        environ: Dict[str, Any],
        key: str,
        default: Optional[Any] = None
    ) -> Optional[Any]:
        """
            Get a framework-specific environ key.
            
            This method retrieves values from environ keys in the webworks
            namespace. It supports both full key names (e.g., 'webworks.request')
            and short names (e.g., 'request').
            
            :param environ: WSGI environ dictionary.
            :param key: The key name (with or without 'webworks.' prefix).
            :param default: Default value if key not found.
            
            :returns: The value from environ or default.
        """
        # Normalize key to include webworks prefix
        if not key.startswith("webworks."):
            full_key = f"webworks.{key}"
        else:
            full_key = key
        
        rtnval = environ.get(full_key, default)
        return rtnval
    
    def get_custom_environ_keys(
        self,
        environ: Dict[str, Any],
        namespace: str = "webworks"
    ) -> Dict[str, Any]:
        """
            Get all custom environ keys in a namespace.
            
            This method retrieves all environ keys that start with the given
            namespace prefix. This is useful for middleware that needs to
            access all framework-specific or custom environ values.
            
            :param environ: WSGI environ dictionary.
            :param namespace: The namespace prefix to filter by (default: 'webworks').
            
            :returns: Dictionary of matching keys and values.
        """
        prefix = f"{namespace}."
        rtnval: Dict[str, Any] = {}
        
        for key, value in environ.items():
            if key.startswith(prefix):
                rtnval[key] = value
        
        return rtnval
    
    def is_standard_wsgi_key(self, key: str) -> bool:
        """
            Check if a key is a standard WSGI environ key.
            
            Standard WSGI keys include CGI variables (REQUEST_METHOD, PATH_INFO,
            etc.), HTTP headers (HTTP_*), and WSGI-specific keys (wsgi.*).
            
            :param key: The environ key to check.
            
            :returns: True if the key is a standard WSGI key.
        """
        # CGI variables
        cgi_keys = {
            "REQUEST_METHOD", "SCRIPT_NAME", "PATH_INFO", "QUERY_STRING",
            "CONTENT_TYPE", "CONTENT_LENGTH", "SERVER_NAME", "SERVER_PORT",
            "SERVER_PROTOCOL", "REMOTE_HOST", "REMOTE_ADDR", "AUTH_TYPE",
            "REMOTE_USER", "REMOTE_IDENT", "GATEWAY_INTERFACE",
        }
        
        if key in cgi_keys:
            rtnval = True
        elif key.startswith("HTTP_"):
            # HTTP headers
            rtnval = True
        elif key.startswith("wsgi."):
            # WSGI-specific keys
            rtnval = True
        else:
            rtnval = False
        
        return rtnval
