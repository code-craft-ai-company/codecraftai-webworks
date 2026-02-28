"""
    WSGI Response module.
    
    This module provides the Response class that represents an HTTP response
    and the ResponseBuilder class that converts Response objects to WSGI format.
"""

from typing import Any, Dict, Iterable, List, Optional, Tuple, Union

from automojo.webworks.wsgi.constants import HTTP_STATUS_PHRASES


class Response:
    """
        Represents an HTTP response.
        
        This class provides a clean interface to construct HTTP responses with
        status code, headers, and body content.
    """
    
    def __init__(
        self,
        status_code: int = 200,
        headers: Optional[Dict[str, str]] = None,
        body: Union[bytes, str, None] = None,
        content_type: Optional[str] = None
    ):
        """
            Construct a Response object.
            
            :param status_code: HTTP status code (e.g., 200, 404).
            :param headers: Dictionary of header names to values.
            :param body: Response body as bytes or string.
            :param content_type: Content-Type header value.
        """
        self._status_code = status_code
        
        if headers is None:
            self._headers: Dict[str, str] = {}
        else:
            self._headers = headers.copy()
        
        if body is None:
            self._body = b""
        elif isinstance(body, str):
            self._body = body.encode("utf-8")
        else:
            self._body = body
        
        if content_type is not None:
            self._headers["Content-Type"] = content_type
        
        return
    
    @property
    def status_code(self) -> int:
        """
            Get the HTTP status code.
            
            :returns: HTTP status code integer.
        """
        return self._status_code
    
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
    
    @property
    def content_type(self) -> Optional[str]:
        """
            Get the Content-Type header.
            
            :returns: Content-Type string or None.
        """
        rtnval = self._headers.get("Content-Type")
        return rtnval
    
    def set_header(self, name: str, value: str) -> None:
        """
            Set a response header.
            
            :param name: Header name.
            :param value: Header value.
        """
        self._headers[name] = value
        return
    
    def get_header(self, name: str, default: Optional[str] = None) -> Optional[str]:
        """
            Get a header value by name.
            
            :param name: Header name.
            :param default: Default value if header not found.
            
            :returns: Header value or default.
        """
        rtnval = self._headers.get(name, default)
        return rtnval
    
    def as_dict(self) -> Dict[str, Any]:
        """
            Convert the response to a dictionary representation.
            
            :returns: Dictionary representation of the response.
        """
        rtnval = {
            "status_code": self._status_code,
            "headers": self._headers.copy(),
            "body_length": len(self._body),
        }
        return rtnval
    
    def __repr__(self) -> str:
        """
            Get string representation of the response.
            
            :returns: String representation.
        """
        rtnval = f"Response({self._status_code}, body_length={len(self._body)})"
        return rtnval


class ResponseBuilder:
    """
        Converts framework Response objects to WSGI format.
        
        This class handles the conversion of Response objects to the tuple format
        expected by WSGI servers: (status, headers, body_iterator).
    """
    
    # Hop-by-hop headers that should not be included in responses per RFC 2616
    HOP_BY_HOP_HEADERS = frozenset([
        "connection",
        "keep-alive",
        "proxy-authenticate",
        "proxy-authorization",
        "te",
        "trailers",
        "transfer-encoding",
        "upgrade",
    ])
    
    def __init__(self):
        """
            Construct a ResponseBuilder.
        """
        return
    
    def format_status(self, status_code: int, reason: Optional[str] = None) -> str:
        """
            Format status code and reason phrase.
            
            :param status_code: HTTP status code.
            :param reason: Optional reason phrase (uses default if not provided).
            
            :returns: Status string like "200 OK".
        """
        if reason is None:
            reason = HTTP_STATUS_PHRASES.get(status_code, "Unknown")
        
        rtnval = f"{status_code} {reason}"
        return rtnval
    
    def is_hop_by_hop(self, header_name: str) -> bool:
        """
            Check if header is a hop-by-hop header.
            
            Hop-by-hop headers are connection-specific and should not be
            forwarded by proxies or included in WSGI responses.
            
            :param header_name: Header name to check.
            
            :returns: True if header is hop-by-hop.
        """
        rtnval = header_name.lower() in self.HOP_BY_HOP_HEADERS
        return rtnval

    def format_headers(
        self,
        headers: Dict[str, str],
        body_length: Optional[int] = None,
        content_type: Optional[str] = None
    ) -> List[Tuple[str, str]]:
        """
            Format headers as list of tuples, filtering hop-by-hop headers.
            
            :param headers: Response headers dict.
            :param body_length: Optional body length for Content-Length header.
            :param content_type: Optional content type if not in headers.
            
            :returns: List of (name, value) tuples.
        """
        result: List[Tuple[str, str]] = []
        
        # Track which headers we've added to avoid duplicates
        added_headers: set = set()
        
        # Add headers from the dict, filtering hop-by-hop headers
        for name, value in headers.items():
            if self.is_hop_by_hop(name):
                continue
            
            result.append((name, str(value)))
            added_headers.add(name.lower())
        
        # Add Content-Type if not present and provided
        if content_type is not None and "content-type" not in added_headers:
            result.append(("Content-Type", content_type))
            added_headers.add("content-type")
        
        # Add Content-Length if not present and body length is known
        if body_length is not None and "content-length" not in added_headers:
            result.append(("Content-Length", str(body_length)))
            added_headers.add("content-length")
        
        return result
    
    def build(
        self,
        response: Response
    ) -> Tuple[str, List[Tuple[str, str]], Iterable[bytes]]:
        """
            Convert Response to WSGI format.
            
            :param response: Framework Response object.
            
            :returns: Tuple of (status, headers, body_iterator).
        """
        # Format status string
        status = self.format_status(response.status_code)
        
        # Get body and determine length
        body = response.body
        body_length: Optional[int] = None
        
        if len(body) > 0:
            body_length = len(body)
        
        # Determine content type for responses with body
        content_type: Optional[str] = None
        if body_length is not None and body_length > 0:
            if response.content_type is None:
                # Default to text/plain if body exists but no content type set
                content_type = "text/plain; charset=utf-8"
            else:
                content_type = response.content_type
        
        # Format headers
        headers = self.format_headers(
            response.headers,
            body_length=body_length,
            content_type=content_type
        )
        
        # Create body iterator
        if len(body) > 0:
            body_iterator: Iterable[bytes] = [body]
        else:
            body_iterator = []
        
        rtnval = (status, headers, body_iterator)
        return rtnval
