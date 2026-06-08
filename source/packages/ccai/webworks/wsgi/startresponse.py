"""
    StartResponse callable module for the WSGI layer.
    
    This module provides the StartResponse class which implements the WSGI
    start_response callable. It captures status and headers, tracks whether
    headers have been sent, and provides the write callable for legacy support.
"""

import socket
import sys
from typing import Any, Callable, Dict, List, Optional, Tuple

from ccai.webworks.wsgi.httpwriter import HTTPWriter
from ccai.webworks.wsgi.serverconfig import ServerConfig
from ccai.webworks.wsgi.constants import HTTP_STATUS_PHRASES


class StartResponse:
    """
        WSGI start_response callable implementation.
        
        This class implements the start_response callable as defined in PEP 3333.
        It captures the status and headers provided by the WSGI application,
        tracks whether headers have been sent, and provides the write callable
        for legacy WSGI applications.
        
        The start_response callable is called by the WSGI application to begin
        the HTTP response. It must be called before any body content is yielded.
    """
    
    def __init__(
        self,
        sock: socket.socket,
        config: Optional[ServerConfig] = None,
        keep_alive: bool = False,
        http_version: str = "HTTP/1.1"
    ):
        """
            Construct a StartResponse callable.
            
            :param sock: Client socket to write to.
            :param config: Server configuration. If None, uses defaults.
            :param keep_alive: Whether to use keep-alive connection.
            :param http_version: HTTP version string for the response.
        """
        self._socket = sock
        
        if config is not None:
            self._config = config
        else:
            self._config = ServerConfig()
        
        self._keep_alive = keep_alive
        self._http_version = http_version
        
        # Create HTTP writer for sending response
        self._writer = HTTPWriter(sock, self._config)
        
        # Response state
        self._status: Optional[str] = None
        self._headers: List[Tuple[str, str]] = []
        self._headers_sent: bool = False
        self._exc_info: Optional[Tuple[Any, Any, Any]] = None
        
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
            
            :returns: True if keep-alive is enabled.
        """
        return self._keep_alive
    
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
        """
        # Handle exc_info per PEP 3333
        if exc_info is not None:
            try:
                if self._headers_sent:
                    # Headers already sent, must re-raise the exception
                    # Use raise ... from None to avoid chaining
                    raise exc_info[1].with_traceback(exc_info[2])
            finally:
                # Avoid circular reference
                exc_info = None
        elif self._status is not None:
            # start_response called again without exc_info
            # This is an error per PEP 3333
            errmsg = "start_response already called without exc_info"
            raise RuntimeError(errmsg)
        
        # Store status and headers
        self._status = status
        self._headers = list(response_headers)
        
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
        
        # Write status line
        self._writer.write_status_line(status_code, reason)
        
        # Prepare headers with Connection header for keep-alive
        headers_to_send = self._prepare_headers()
        
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
            Prepare headers for sending, adding Connection header if needed.
            
            :returns: List of headers with Connection header added.
        """
        headers = list(self._headers)
        
        # Check if Connection header is already present
        has_connection = False
        for name, _ in headers:
            if name.lower() == "connection":
                has_connection = True
                break
        
        # Add Connection header based on keep-alive setting
        if not has_connection:
            if self._keep_alive:
                headers.append(("Connection", "keep-alive"))
            else:
                headers.append(("Connection", "close"))
        
        rtnval = headers
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
        
        # Create new writer for the next response
        self._writer = HTTPWriter(self._socket, self._config)
        
        return
