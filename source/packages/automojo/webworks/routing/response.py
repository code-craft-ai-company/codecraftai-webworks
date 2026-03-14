"""
    Response module.
    
    This module provides the Response class and its subclasses for building
    HTTP responses with status codes, headers, and body content.
    
    The Response class provides a clean abstraction over WSGI/ASGI response
    formats, allowing handlers to build responses without dealing with
    protocol-specific details.
"""

import json
from http.cookies import SimpleCookie
from typing import Any, Dict, Iterable, Iterator, List, Optional, Tuple, Union


# HTTP status phrases for common status codes
HTTP_STATUS_PHRASES: Dict[int, str] = {
    100: "Continue",
    101: "Switching Protocols",
    200: "OK",
    201: "Created",
    202: "Accepted",
    204: "No Content",
    301: "Moved Permanently",
    302: "Found",
    303: "See Other",
    304: "Not Modified",
    307: "Temporary Redirect",
    308: "Permanent Redirect",
    400: "Bad Request",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Not Found",
    405: "Method Not Allowed",
    406: "Not Acceptable",
    408: "Request Timeout",
    409: "Conflict",
    410: "Gone",
    413: "Payload Too Large",
    415: "Unsupported Media Type",
    422: "Unprocessable Entity",
    429: "Too Many Requests",
    500: "Internal Server Error",
    501: "Not Implemented",
    502: "Bad Gateway",
    503: "Service Unavailable",
    504: "Gateway Timeout",
}


class Response:
    """
        HTTP response abstraction for building responses with status,
        headers, and body content.
        
        This class provides a clean interface for constructing HTTP responses
        that can be converted to both WSGI and ASGI formats.
        
        :param status_code: HTTP status code (default 200).
        :param headers: Optional dictionary of response headers.
        :param body: Response body as bytes.
        
        Example:
            response = Response(200, {"Content-Type": "text/plain"}, b"Hello")
            response.set_header("X-Custom", "value")
            response.set_cookie("session", "abc123", httponly=True)
    """
    
    def __init__(
        self,
        status_code: int = 200,
        headers: Optional[Dict[str, str]] = None,
        body: bytes = b""
    ):
        """
            Construct a Response.
            
            :param status_code: HTTP status code (default 200).
            :param headers: Response headers dict.
            :param body: Response body as bytes.
        """
        self._status_code = status_code
        self._headers: Dict[str, str] = {}
        self._body = body
        self._cookies: SimpleCookie = SimpleCookie()
        
        # Initialize headers
        if headers is not None:
            for name, value in headers.items():
                self._headers[name] = value
        
        return

    @property
    def status_code(self) -> int:
        """
            Get the HTTP status code.
            
            :returns: HTTP status code.
        """
        return self._status_code
    
    @status_code.setter
    def status_code(self, value: int) -> None:
        """
            Set the HTTP status code.
            
            :param value: HTTP status code.
        """
        self._status_code = value
        return
    
    @property
    def headers(self) -> Dict[str, str]:
        """
            Get the response headers.
            
            :returns: Dictionary of header names to values.
        """
        return self._headers
    
    @property
    def body(self) -> bytes:
        """
            Get the response body.
            
            :returns: Response body as bytes.
        """
        return self._body
    
    @body.setter
    def body(self, value: bytes) -> None:
        """
            Set the response body.
            
            :param value: Response body as bytes.
        """
        self._body = value
        return
    
    def set_header(self, name: str, value: str) -> None:
        """
            Set a response header.
            
            :param name: Header name.
            :param value: Header value.
        """
        self._headers[name] = value
        return
    
    def set_cookie(
        self,
        name: str,
        value: str,
        max_age: Optional[int] = None,
        expires: Optional[str] = None,
        path: str = "/",
        domain: Optional[str] = None,
        secure: bool = False,
        httponly: bool = False,
        samesite: Optional[str] = None
    ) -> None:
        """
            Set a response cookie.
            
            :param name: Cookie name.
            :param value: Cookie value.
            :param max_age: Maximum age in seconds.
            :param expires: Expiration date string.
            :param path: Cookie path (default "/").
            :param domain: Cookie domain.
            :param secure: Whether cookie requires HTTPS.
            :param httponly: Whether cookie is HTTP-only.
            :param samesite: SameSite attribute (Strict, Lax, None).
        """
        self._cookies[name] = value
        morsel = self._cookies[name]
        
        if max_age is not None:
            morsel["max-age"] = str(max_age)
        if expires is not None:
            morsel["expires"] = expires
        if path:
            morsel["path"] = path
        if domain is not None:
            morsel["domain"] = domain
        if secure:
            morsel["secure"] = True
        if httponly:
            morsel["httponly"] = True
        if samesite is not None:
            morsel["samesite"] = samesite
        
        return
    
    def delete_cookie(
        self,
        name: str,
        path: str = "/",
        domain: Optional[str] = None
    ) -> None:
        """
            Delete a cookie by setting it to expire.
            
            :param name: Cookie name.
            :param path: Cookie path (default "/").
            :param domain: Cookie domain.
        """
        self.set_cookie(
            name=name,
            value="",
            max_age=0,
            expires="Thu, 01 Jan 1970 00:00:00 GMT",
            path=path,
            domain=domain
        )
        return

    def _get_status_line(self) -> str:
        """
            Get the HTTP status line.
            
            :returns: Status line string (e.g., "200 OK").
        """
        phrase = HTTP_STATUS_PHRASES.get(self._status_code, "Unknown")
        return f"{self._status_code} {phrase}"
    
    def _get_all_headers(self) -> List[Tuple[str, str]]:
        """
            Get all headers including cookies.
            
            :returns: List of (name, value) tuples.
        """
        headers_list: List[Tuple[str, str]] = []
        
        # Add regular headers
        for name, value in self._headers.items():
            headers_list.append((name, value))
        
        # Add cookie headers
        for cookie_name in self._cookies:
            cookie_header = self._cookies[cookie_name].OutputString()
            headers_list.append(("Set-Cookie", cookie_header))
        
        return headers_list
    
    def to_wsgi(self) -> Tuple[str, List[Tuple[str, str]], Iterable[bytes]]:
        """
            Convert to WSGI response format.
            
            :returns: Tuple of (status, headers, body_iterable).
        """
        status = self._get_status_line()
        headers = self._get_all_headers()
        body_iterable: Iterable[bytes] = [self._body] if self._body else []
        
        return (status, headers, body_iterable)
    
    def to_asgi(self) -> Dict[str, Any]:
        """
            Convert to ASGI response events.
            
            :returns: Dictionary with 'start' and 'body' events.
        """
        headers_list: List[List[bytes]] = []
        for name, value in self._get_all_headers():
            headers_list.append([name.encode("latin-1"), value.encode("latin-1")])
        
        start_event = {
            "type": "http.response.start",
            "status": self._status_code,
            "headers": headers_list,
        }
        
        body_event = {
            "type": "http.response.body",
            "body": self._body,
            "more_body": False,
        }
        
        return {
            "start": start_event,
            "body": body_event,
        }
    
    def __repr__(self) -> str:
        """
            Get string representation.
            
            :returns: String representation.
        """
        return f"Response({self._status_code})"


class JSONResponse(Response):
    """
        Response with JSON body and automatic Content-Type header.
        
        This class automatically serializes Python objects to JSON and
        sets the appropriate Content-Type header.
        
        :param content: Python object to serialize as JSON.
        :param status_code: HTTP status code (default 200).
        :param headers: Optional additional headers.
        
        Example:
            response = JSONResponse({"message": "Hello"})
            response = JSONResponse({"error": "Not found"}, status_code=404)
    """
    
    def __init__(
        self,
        content: Any,
        status_code: int = 200,
        headers: Optional[Dict[str, str]] = None
    ):
        """
            Construct a JSON response.
            
            :param content: Python object to serialize as JSON.
            :param status_code: HTTP status code.
            :param headers: Additional headers.
        """
        # Serialize content to JSON
        body = json.dumps(content, ensure_ascii=False).encode("utf-8")
        
        # Initialize base response
        super().__init__(status_code=status_code, headers=headers, body=body)
        
        # Set Content-Type header
        self.set_header("Content-Type", "application/json; charset=utf-8")
        
        return
    
    def __repr__(self) -> str:
        """
            Get string representation.
            
            :returns: String representation.
        """
        return f"JSONResponse({self._status_code})"


class HTMLResponse(Response):
    """
        Response with HTML body and automatic Content-Type header.
        
        :param content: HTML content as string.
        :param status_code: HTTP status code (default 200).
        :param headers: Optional additional headers.
        
        Example:
            response = HTMLResponse("<h1>Hello</h1>")
    """
    
    def __init__(
        self,
        content: str,
        status_code: int = 200,
        headers: Optional[Dict[str, str]] = None
    ):
        """
            Construct an HTML response.
            
            :param content: HTML content as string.
            :param status_code: HTTP status code.
            :param headers: Additional headers.
        """
        body = content.encode("utf-8")
        
        super().__init__(status_code=status_code, headers=headers, body=body)
        
        self.set_header("Content-Type", "text/html; charset=utf-8")
        
        return
    
    def __repr__(self) -> str:
        """
            Get string representation.
            
            :returns: String representation.
        """
        return f"HTMLResponse({self._status_code})"


class RedirectResponse(Response):
    """
        HTTP redirect response.
        
        :param url: URL to redirect to.
        :param status_code: HTTP status code (default 307 Temporary Redirect).
        :param headers: Optional additional headers.
        
        Example:
            response = RedirectResponse("/new-location")
            response = RedirectResponse("/permanent", status_code=301)
    """
    
    def __init__(
        self,
        url: str,
        status_code: int = 307,
        headers: Optional[Dict[str, str]] = None
    ):
        """
            Construct a redirect response.
            
            :param url: URL to redirect to.
            :param status_code: HTTP status code (default 307).
            :param headers: Additional headers.
        """
        super().__init__(status_code=status_code, headers=headers, body=b"")
        
        self.set_header("Location", url)
        
        return
    
    def __repr__(self) -> str:
        """
            Get string representation.
            
            :returns: String representation.
        """
        location = self._headers.get("Location", "")
        return f"RedirectResponse({self._status_code}, {location!r})"


class StreamingResponse(Response):
    """
        Response that streams body content.
        
        This class is used for streaming large responses where the body
        is generated incrementally.
        
        :param content: Iterable of bytes chunks.
        :param status_code: HTTP status code (default 200).
        :param headers: Optional additional headers.
        :param media_type: Optional media type for Content-Type header.
        
        Example:
            def generate():
                yield b"chunk1"
                yield b"chunk2"
            response = StreamingResponse(generate())
    """
    
    def __init__(
        self,
        content: Iterable[bytes],
        status_code: int = 200,
        headers: Optional[Dict[str, str]] = None,
        media_type: Optional[str] = None
    ):
        """
            Construct a streaming response.
            
            :param content: Iterable of bytes chunks.
            :param status_code: HTTP status code.
            :param headers: Additional headers.
            :param media_type: Optional media type.
        """
        super().__init__(status_code=status_code, headers=headers, body=b"")
        
        self._content_iterator = content
        
        if media_type is not None:
            self.set_header("Content-Type", media_type)
        
        return
    
    @property
    def body(self) -> bytes:
        """
            Get the response body.
            
            For streaming responses, this consumes the iterator and
            returns all content as bytes.
            
            :returns: Response body as bytes.
        """
        if self._body:
            return self._body
        
        # Consume iterator and cache result
        chunks = list(self._content_iterator)
        self._body = b"".join(chunks)
        return self._body
    
    def iter_content(self) -> Iterator[bytes]:
        """
            Iterate over body content chunks.
            
            If the body has already been consumed (e.g. via the ``body``
            property), yields the cached body as a single chunk.
            
            :returns: Iterator of bytes chunks.
        """
        if self._body:
            return iter([self._body])
        return iter(self._content_iterator)
    
    def to_wsgi(self) -> Tuple[str, List[Tuple[str, str]], Iterable[bytes]]:
        """
            Convert to WSGI response format.
            
            :returns: Tuple of (status, headers, body_iterable).
        """
        status = self._get_status_line()
        headers = self._get_all_headers()
        
        return (status, headers, self._content_iterator)
    
    def __repr__(self) -> str:
        """
            Get string representation.
            
            :returns: String representation.
        """
        return f"StreamingResponse({self._status_code})"
