"""
    StartResponse callable module for the WSGI layer.
    
    This module provides the StartResponse class which implements the WSGI
    start_response callable. It captures status and headers, tracks whether
    headers have been sent, and provides the write callable for legacy support.
"""

import socket
from typing import Any, Callable, List, Optional, Tuple

from ccai.webworks.wsgi.exceptions import InvalidResponseHeader
from ccai.webworks.wsgi.headervalidation import (
    validate_headers,
    validate_status,
)
from ccai.webworks.wsgi.httpwriter import HTTPWriter
from ccai.webworks.wsgi.serverconfig import ServerConfig


# Status codes of responses that never carry a body
STATUS_CODES_WITHOUT_BODY: Tuple[int, ...] = (204, 304)

# Status codes of responses that must not declare a Content-Length
STATUS_CODES_WITHOUT_CONTENT_LENGTH: Tuple[int, ...] = (204,)


class StartResponse:
    """
        WSGI start_response callable implementation.
        
        This class implements the start_response callable as defined in PEP 3333.
        It captures the status and headers provided by the WSGI application,
        tracks whether headers have been sent, and provides the write callable
        for legacy WSGI applications.
        
        The start_response callable is called by the WSGI application to begin
        the HTTP response. It must be called before any body content is yielded.
        
        The status and headers are only stored by the call. They are written
        when the first body bytes are ready or when the response is finished,
        which is when the framing of the body is decided:
        
        - a declared Content-Length is used as it is,
        - otherwise an HTTP/1.1 connection that is kept alive gets chunked
          transfer encoding,
        - otherwise the connection is closed after the body.
    """
    
    def __init__(
        self,
        sock: socket.socket,
        config: Optional[ServerConfig] = None,
        keep_alive: bool = False,
        http_version: str = "HTTP/1.1",
        request_method: str = "GET"
    ):
        """
            Construct a StartResponse callable.
            
            :param sock: Client socket to write to.
            :param config: Server configuration. If None, uses defaults.
            :param keep_alive: Whether to use keep-alive connection.
            :param http_version: HTTP version of the request being answered.
            :param request_method: HTTP method of the request being answered.
        """
        self._socket = sock
        
        if config is not None:
            self._config = config
        else:
            self._config = ServerConfig()
        
        self._keep_alive = keep_alive
        self._http_version = http_version.upper()
        self._request_method = request_method.upper()
        
        # Create HTTP writer for sending response
        self._writer = HTTPWriter(sock, self._config)
        
        # Response state
        self._status: Optional[str] = None
        self._headers: List[Tuple[str, str]] = []
        self._headers_sent: bool = False
        self._exc_info: Optional[Tuple[Any, Any, Any]] = None
        self._known_body_size: Optional[int] = None
        
        return
    
    @property
    def status(self) -> Optional[str]:
        """
            Get the response status string.
            
            :returns: Status string (e.g., "200 OK") or None if not set.
        """
        return self._status
    
    @property
    def headers(self) -> List[Tuple[str, str]]:
        """
            Get the response headers.
            
            :returns: List of (name, value) header tuples.
        """
        return self._headers
    
    @property
    def headers_sent(self) -> bool:
        """
            Check if headers have been sent to the client.
            
            :returns: True if headers have been sent.
        """
        return self._headers_sent
    
    @property
    def keep_alive(self) -> bool:
        """
            Check if keep-alive is enabled.
            
            The value is final once the response has been finished. It turns
            False when the response cannot be framed on a connection that
            stays open, or when the body written did not match the headers.
            
            :returns: True if keep-alive is enabled.
        """
        return self._keep_alive
    
    @property
    def request_method(self) -> str:
        """
            Get the HTTP method of the request being answered.
            
            :returns: HTTP method string in upper case.
        """
        return self._request_method
    
    @property
    def writer(self) -> HTTPWriter:
        """
            Get the HTTP writer.
            
            :returns: HTTPWriter instance.
        """
        return self._writer


    def __call__(
        self,
        status: str,
        response_headers: List[Tuple[str, str]],
        exc_info: Optional[Tuple[Any, Any, Any]] = None
    ) -> Callable[[bytes], None]:
        """
            WSGI start_response callable.
            
            This method is called by the WSGI application to begin the HTTP
            response. It captures the status and headers, and returns the
            write callable for legacy support.
            
            Per PEP 3333:
            - If exc_info is provided and headers have been sent, re-raise the exception
            - If exc_info is provided and headers have not been sent, replace the stored headers
            - The write callable is returned for legacy applications
            
            :param status: HTTP status string (e.g., "200 OK").
            :param response_headers: List of (name, value) header tuples.
            :param exc_info: Optional exception info tuple from sys.exc_info().
            
            :returns: Write callable for legacy WSGI support.
            
            :raises: Re-raises exception from exc_info if headers already sent.
            :raises: InvalidResponseHeader if the status or a header is not safe
                     to write, for example because it contains CR or LF.
        """
        # Handle exc_info per PEP 3333
        if exc_info is not None:
            try:
                if self._headers_sent:
                    # Headers already sent, must re-raise the exception
                    # Use raise ... from None to avoid chaining
                    raise exc_info[1].with_traceback(exc_info[2])
            finally:
                # Drop the exc_info reference to avoid a circular reference
                del exc_info
        elif self._status is not None:
            # start_response called again without exc_info
            # This is an error per PEP 3333
            errmsg = "start_response already called without exc_info"
            raise RuntimeError(errmsg)
        
        # Refuse a status or header that would corrupt the response before
        # anything is stored or written.
        headers = list(response_headers)
        validate_status(status)
        validate_headers(headers)
        
        for name, _ in headers:
            if name.lower() == "transfer-encoding":
                # The framing of the body belongs to the server (PEP 3333,
                # hop-by-hop headers). Honouring this header would frame
                # the body twice.
                errmsg = "the application must not set the Transfer-Encoding header"
                raise InvalidResponseHeader(errmsg)
        
        # Store status and headers
        self._status = status
        self._headers = headers
        
        # Return write callable for legacy support
        rtnval = self.write
        return rtnval
    
    def write(self, data: bytes) -> None:
        """
            Legacy write callable for WSGI applications.
            
            This method is returned by start_response for legacy WSGI applications
            that use the write callable instead of returning an iterator.
            
            Per PEP 3333, the write callable should be avoided in new applications
            but must be supported for backwards compatibility.
            
            :param data: Bytes to write to the response body.
        """
        # Send headers if not already sent
        if not self._headers_sent:
            self.send_headers()
        
        # Write data to socket
        if len(data) > 0:
            self._writer.write_body(data)
            self._writer.flush()
        
        return
    
    def set_known_body_size(self, size: int) -> None:
        """
            Tell the response how large its whole body is.
            
            The server calls this when it can see the size of the body before
            the headers are written, for example when the application returned
            a list of one item or produced no body at all. The size is used as
            the Content-Length when the application did not declare one. It has
            no effect once the headers have been sent.
            
            :param size: Size of the whole body in bytes.
        """
        self._known_body_size = size
        return
    
    def finish(self) -> None:
        """
            Finish the response after the application produced its whole body.
            
            Sends the headers if no body bytes caused them to be sent, ends the
            body and flushes it. If the application wrote fewer bytes than the
            Content-Length it declared, the client cannot tell where the response
            ends, so the connection is marked to be closed.
        """
        if not self._headers_sent:
            if self._known_body_size is None:
                self._known_body_size = 0
            self.send_headers()
        
        self._writer.finish()
        
        if not self._writer.body_complete:
            self._keep_alive = False
        
        return
    
    def send_headers(self) -> None:
        """
            Send HTTP status line and headers to the client.
            
            This method writes the HTTP status line and all response headers
            to the client socket. It also sets the Connection header based
            on the keep-alive setting.
            
            This method should be called before any body content is written.
            It is automatically called by the write() method if headers have
            not been sent.
        """
        if self._headers_sent:
            return
        
        if self._status is None:
            errmsg = "start_response not called before sending headers"
            raise RuntimeError(errmsg)
        
        # Parse status code from status string
        status_code = self._parse_status_code(self._status)
        reason = self._parse_reason_phrase(self._status)
        
        # Prepare headers, deciding how the body is framed. This is done
        # before the status line is written so that a response that is
        # refused here leaves nothing behind in the writer.
        headers_to_send = self._prepare_headers()
        
        # Write status line
        self._writer.write_status_line(status_code, reason)
        
        # Write headers
        self._writer.write_headers(headers_to_send)
        
        # Flush to ensure headers are sent
        self._writer.flush()
        
        # Mark headers as sent
        self._headers_sent = True
        
        return
    
    def _parse_status_code(self, status: str) -> int:
        """
            Parse the status code from a status string.
            
            :param status: Status string (e.g., "200 OK").
            
            :returns: Integer status code.
        """
        # Status format is "CODE REASON" or just "CODE"
        parts = status.split(None, 1)
        
        if len(parts) == 0:
            errmsg = f"Invalid status string: '{status}'"
            raise ValueError(errmsg)
        
        try:
            rtnval = int(parts[0])
        except ValueError as val_err:
            errmsg = f"Invalid status code in '{status}'"
            raise ValueError(errmsg) from val_err
        
        return rtnval
    
    def _parse_reason_phrase(self, status: str) -> Optional[str]:
        """
            Parse the reason phrase from a status string.
            
            :param status: Status string (e.g., "200 OK").
            
            :returns: Reason phrase or None if not present.
        """
        # Status format is "CODE REASON" or just "CODE"
        parts = status.split(None, 1)
        
        if len(parts) >= 2:
            rtnval = parts[1]
        else:
            rtnval = None
        
        return rtnval
    
    def _prepare_headers(self) -> List[Tuple[str, str]]:
        """
            Prepare headers for sending and decide how the body is framed.
            
            Sets up the writer for the body (discarded, limited to the declared
            length, or chunked) and settles whether the connection is kept
            alive. The Connection header sent always states that decision.
            
            :returns: List of headers to send.
            
            :raises: InvalidResponseHeader if the declared Content-Length is
                     not a plain decimal number.
        """
        status_code = self._parse_status_code(self._status)
        
        # Take the Connection header of the application out, it is sent
        # again below with the value the server settled on.
        headers: List[Tuple[str, str]] = []
        for name, value in self._headers:
            if name.lower() == "connection":
                if value.strip().lower() == "close":
                    self._keep_alive = False
            else:
                headers.append((name, value))
        
        informational = status_code >= 100 and status_code < 200
        
        if informational or status_code in STATUS_CODES_WITHOUT_CONTENT_LENGTH:
            headers = self._remove_header(headers, "content-length")
        
        body_allowed = True
        if self._request_method == "HEAD":
            body_allowed = False
        elif informational or status_code in STATUS_CODES_WITHOUT_BODY:
            body_allowed = False
        
        declared_length = self._find_content_length(headers)
        
        if not body_allowed:
            self._writer.set_body_discarded(True)
        elif declared_length is not None:
            self._writer.set_body_limit(declared_length)
        elif self._known_body_size is not None:
            headers.append(("Content-Length", str(self._known_body_size)))
            self._writer.set_body_limit(self._known_body_size)
        elif self._keep_alive and self._http_version == "HTTP/1.1":
            headers.append(("Transfer-Encoding", "chunked"))
            self._writer.set_chunked(True)
        else:
            # The end of the body can only be marked by closing the connection
            self._keep_alive = False
        
        if self._keep_alive:
            headers.append(("Connection", "keep-alive"))
        else:
            headers.append(("Connection", "close"))
        
        rtnval = headers
        return rtnval
    
    def _remove_header(
        self,
        headers: List[Tuple[str, str]],
        name_lower: str
    ) -> List[Tuple[str, str]]:
        """
            Remove every header with the given name from a header list.
            
            :param headers: List of (name, value) header tuples.
            :param name_lower: Lower case name of the header to remove.
            
            :returns: New list without the header.
        """
        rtnval: List[Tuple[str, str]] = []
        
        for name, value in headers:
            if name.lower() != name_lower:
                rtnval.append((name, value))
        
        return rtnval
    
    def _find_content_length(self, headers: List[Tuple[str, str]]) -> Optional[int]:
        """
            Find the Content-Length the application declared.
            
            :param headers: List of (name, value) header tuples.
            
            :returns: The declared length or None if none was declared.
            
            :raises: InvalidResponseHeader if the value is not a plain decimal
                     number or if two values disagree.
        """
        rtnval: Optional[int] = None
        
        for name, value in headers:
            if name.lower() != "content-length":
                continue
            
            length_str = value.strip()
            if not length_str.isascii() or not length_str.isdigit():
                errmsg = f"Content-Length {value!r} is not a decimal number"
                raise InvalidResponseHeader(errmsg)
            
            length = int(length_str)
            if rtnval is not None and rtnval != length:
                errmsg = "the response has conflicting Content-Length headers"
                raise InvalidResponseHeader(errmsg)
            
            rtnval = length
        
        return rtnval
    
    def flush(self) -> None:
        """
            Flush any buffered data to the socket.
        """
        self._writer.flush()
        return
    
    def close(self) -> None:
        """
            Close the writer and flush any remaining data.
        """
        self._writer.close()
        return
    
    def reset(self) -> None:
        """
            Reset the start_response state for reuse.
            
            This is useful for keep-alive connections where the same
            StartResponse instance may be reused for multiple requests.
        """
        self._status = None
        self._headers = []
        self._headers_sent = False
        self._exc_info = None
        self._known_body_size = None
        
        # Create new writer for the next response
        self._writer = HTTPWriter(self._socket, self._config)
        
        return
