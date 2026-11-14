"""
    WSGI Response module.
    
    This module provides the Response class that represents an HTTP response
    and the ResponseBuilder class that converts Response objects to WSGI format.
"""

from typing import Any, Dict, Iterable, List, Optional, Tuple, Union

from ccai.webworks.wsgi.constants import HTTP_STATUS_PHRASES
from ccai.webworks.wsgi.headervalidation import validate_headers


# Status codes of responses that carry neither a body nor a Content-Length
STATUS_CODES_WITHOUT_BODY: Tuple[int, ...] = (204, 304)


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
            
            :raises: InvalidResponseHeader if a header name or value is not safe
                     to send, for example because it contains CR or LF.
        """
        header_items: List[Tuple[str, str]] = []
        for name, value in headers.items():
            header_items.append((name, value))
        
        result = self.format_header_list(
            header_items,
            body_length=body_length,
            content_type=content_type
        )
        return result
    
    def format_header_list(
        self,
        headers: List[Tuple[str, str]],
        body_length: Optional[int] = None,
        content_type: Optional[str] = None
    ) -> List[Tuple[str, str]]:
        """
            Format a list of headers, filtering hop-by-hop headers.
            
            Unlike a dict, a list can hold a header more than once, which is
            how several Set-Cookie headers are carried.
            
            :param headers: Response headers as (name, value) tuples.
            :param body_length: Optional body length for Content-Length header.
            :param content_type: Optional content type if not in headers.
            
            :returns: List of (name, value) tuples.
            
            :raises: InvalidResponseHeader if a header name or value is not safe
                     to send, for example because it contains CR or LF.
        """
        result: List[Tuple[str, str]] = []
        
        # Track which headers we've added to avoid duplicates
        added_headers: set = set()
        
        # Add the given headers, filtering hop-by-hop headers
        for name, value in headers:
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
        
        # A header that holds a line break would be split into two headers
        # by whatever writes the response. It is refused here, where every
        # WSGI server the application runs under is covered.
        validate_headers(result)
        
        return result
    
    def _get_response_headers(self, response: Any) -> List[Tuple[str, str]]:
        """
            Get every header of a response object, cookies included.
            
            The framework response keeps its cookies outside of the headers
            dict and offers the complete list through '_get_all_headers'.
            Responses without that method only have the dict.
            
            :param response: Response object.
            
            :returns: List of (name, value) header tuples.
        """
        rtnval: List[Tuple[str, str]] = []
        
        all_headers = getattr(response, "_get_all_headers", None)
        if callable(all_headers):
            for name, value in all_headers():
                rtnval.append((name, value))
        else:
            for name, value in response.headers.items():
                rtnval.append((name, value))
        
        return rtnval
    
    def _get_response_content_type(
        self,
        response: Any,
        headers: List[Tuple[str, str]]
    ) -> Optional[str]:
        """
            Get the content type of a response object.
            
            :param response: Response object.
            :param headers: Headers of the response as (name, value) tuples.
            
            :returns: Content type or None if the response does not set one.
        """
        rtnval: Optional[str] = getattr(response, "content_type", None)
        
        if rtnval is None:
            for name, value in headers:
                if name.lower() == "content-type":
                    rtnval = value
                    break
        
        return rtnval
    
    def build(
        self,
        response: Any
    ) -> Tuple[str, List[Tuple[str, str]], Iterable[bytes]]:
        """
            Convert Response to WSGI format.
            
            Accepts the Response of this module and the response classes of
            the framework, including streaming responses, whose body is passed
            on as an iterator and not collected in memory.
            
            :param response: Response object.
            
            :returns: Tuple of (status, headers, body_iterator).
            
            :raises: InvalidResponseHeader if a header name or value is not safe
                     to send.
        """
        # Format status string
        status_code = response.status_code
        status = self.format_status(status_code)
        
        response_headers = self._get_response_headers(response)
        response_content_type = self._get_response_content_type(response, response_headers)
        
        status_has_body = True
        if status_code >= 100 and status_code < 200:
            status_has_body = False
        elif status_code in STATUS_CODES_WITHOUT_BODY:
            status_has_body = False
        
        iter_content = getattr(response, "iter_content", None)
        
        if callable(iter_content):
            # Streaming response: the size of the body is not known and the
            # body is not read here.
            body_iterator: Iterable[bytes] = iter_content()
            
            # WSGI has no way to wait on an async iterator.
            if hasattr(body_iterator, "__aiter__"):
                errmsg = (
                    "A streaming response with async content can not be served "
                    "through WSGI; serve it through the ASGI application."
                )
                raise TypeError(errmsg)
            body_length: Optional[int] = None
            content_type: Optional[str] = response_content_type
        else:
            body = response.body
            
            # The length is stated for an empty body as well, a client that
            # keeps the connection open has no other way to tell that the
            # response is complete.
            body_length = None
            if status_has_body:
                body_length = len(body)
            
            # Determine content type for responses with body
            content_type = None
            if len(body) > 0:
                if response_content_type is None:
                    # Default to text/plain if body exists but no content type set
                    content_type = "text/plain; charset=utf-8"
                else:
                    content_type = response_content_type
            
            # Create body iterator
            if len(body) > 0 and status_has_body:
                body_iterator = [body]
            else:
                body_iterator = []
        
        # Format headers
        headers = self.format_header_list(
            response_headers,
            body_length=body_length,
            content_type=content_type
        )
        
        rtnval = (status, headers, body_iterator)
        return rtnval
