"""
    WSGI Request module.
    
    This module provides the Request class that represents an HTTP request
    parsed from a WSGI environ dictionary.
"""

from typing import Any, Dict, Optional
from urllib.parse import parse_qs


class Request:
    """
        Represents an HTTP request parsed from WSGI environ.
        
        This class provides a clean interface to access request data including
        method, path, query string, headers, body, scheme, host, and port.
    """
    
    def __init__(
        self,
        method: str,
        path: str,
        query_string: str,
        headers: Dict[str, str],
        body: bytes,
        scheme: str,
        host: str,
        port: int,
        content_type: Optional[str] = None,
        content_length: Optional[int] = None
    ):
        """
            Construct a Request object.
            
            :param method: HTTP method (e.g., 'GET', 'POST').
            :param path: Request path (e.g., '/api/users').
            :param query_string: Query string without leading '?'.
            :param headers: Dictionary of header names to values.
            :param body: Request body as bytes.
            :param scheme: URL scheme ('http' or 'https').
            :param host: Server host name.
            :param port: Server port number.
            :param content_type: Content-Type header value.
            :param content_length: Content-Length header value.
        """
        self._method = method
        self._path = path
        self._query_string = query_string
        self._headers = headers
        self._body = body
        self._scheme = scheme
        self._host = host
        self._port = port
        self._content_type = content_type
        self._content_length = content_length
        self._query_params: Optional[Dict[str, list]] = None
        self._background_tasks: Optional[Any] = None
        return
    
    @property
    def method(self) -> str:
        """
            Get the HTTP method.
            
            :returns: HTTP method string (e.g., 'GET', 'POST').
        """
        return self._method
    
    @property
    def path(self) -> str:
        """
            Get the request path.
            
            :returns: Request path string.
        """
        return self._path
    
    @property
    def query_string(self) -> str:
        """
            Get the query string.
            
            :returns: Query string without leading '?'.
        """
        return self._query_string
    
    @property
    def headers(self) -> Dict[str, str]:
        """
            Get the request headers.
            
            :returns: Dictionary of header names to values.
        """
        return self._headers
    
    @property
    def body(self) -> bytes:
        """
            Get the request body.
            
            :returns: Request body as bytes.
        """
        return self._body
    
    @property
    def scheme(self) -> str:
        """
            Get the URL scheme.
            
            :returns: URL scheme string ('http' or 'https').
        """
        return self._scheme
    
    @property
    def host(self) -> str:
        """
            Get the server host.
            
            :returns: Server host string.
        """
        return self._host
    
    @property
    def port(self) -> int:
        """
            Get the server port.
            
            :returns: Server port number.
        """
        return self._port
    
    @property
    def content_type(self) -> Optional[str]:
        """
            Get the Content-Type header.
            
            :returns: Content-Type string or None.
        """
        return self._content_type
    
    @property
    def content_length(self) -> Optional[int]:
        """
            Get the Content-Length header.
            
            :returns: Content-Length as integer or None.
        """
        return self._content_length
    
    @property
    def query_params(self) -> Dict[str, list]:
        """
            Get parsed query parameters.
            
            :returns: Dictionary of parameter names to lists of values.
        """
        if self._query_params is None:
            self._query_params = parse_qs(self._query_string, keep_blank_values=True)
        
        return self._query_params
    
    @property
    def background_tasks(self) -> Optional[Any]:
        """
            Get the background tasks manager for this request.
            
            Background tasks are async functions that run after the response
            is sent. This property is set by the ASGI HTTP handler.
            
            :returns: BackgroundTasks instance or None.
        """
        return self._background_tasks
    
    @background_tasks.setter
    def background_tasks(self, value: Any) -> None:
        """
            Set the background tasks manager for this request.
            
            :param value: BackgroundTasks instance.
        """
        self._background_tasks = value
        return
    
    @property
    def url(self) -> str:
        """
            Get the full URL.
            
            :returns: Full URL string.
        """
        # Determine if we need to include the port
        include_port = True
        if self._scheme == "http" and self._port == 80:
            include_port = False
        elif self._scheme == "https" and self._port == 443:
            include_port = False
        
        if include_port:
            host_part = f"{self._host}:{self._port}"
        else:
            host_part = self._host
        
        if len(self._query_string) > 0:
            rtnval = f"{self._scheme}://{host_part}{self._path}?{self._query_string}"
        else:
            rtnval = f"{self._scheme}://{host_part}{self._path}"
        
        return rtnval
    
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
                "query_string": self._query_string,
                "headers": self._headers.copy(),
                "body_length": len(self._body),
                "scheme": self._scheme,
                "host": self._host,
                "port": self._port,
                "content_type": self._content_type,
                "content_length": self._content_length,
                "url": self.url,
            }
        
        return rtnval
    
    def __repr__(self) -> str:
        """
            Get string representation of the request.
            
            :returns: String representation.
        """
        rtnval = f"Request({self._method} {self.url})"
        return rtnval
