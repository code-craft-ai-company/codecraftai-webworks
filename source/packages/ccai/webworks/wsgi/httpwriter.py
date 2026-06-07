"""
    HTTP response writer module for the WSGI layer.
    
    This module provides the HTTPWriter class for writing HTTP responses to
    sockets. It handles status line, headers, and body writing including
    support for chunked transfer encoding.
"""

import socket
from datetime import datetime, timezone
from typing import Iterable, List, Optional, Tuple

from ccai.webworks.wsgi.serverconfig import ServerConfig
from ccai.webworks.wsgi.constants import HTTP_STATUS_PHRASES


# Default buffer size for writing to socket
DEFAULT_BUFFER_SIZE: int = 8192

# Server identification string
SERVER_NAME: str = "WebWorks/1.0"


class HTTPWriter:
    """
        Writes HTTP responses to client sockets.
        
        This class handles the formatting and writing of HTTP responses
        including status lines, headers, and body content. It supports
        both Content-Length based responses and chunked transfer encoding.
    """
    
    def __init__(
        self,
        sock: socket.socket,
        config: Optional[ServerConfig] = None
    ):
        """
            Construct an HTTP writer.
            
            :param sock: Client socket to write to.
            :param config: Server configuration. If None, uses defaults.
        """
        self._socket = sock
        
        if config is not None:
            self._config = config
        else:
            self._config = ServerConfig()
        
        self._buffer: bytes = b""
        self._headers_sent: bool = False
        return
    
    @property
    def socket(self) -> socket.socket:
        """
            Get the client socket.
            
            :returns: Client socket.
        """
        return self._socket
    
    @property
    def headers_sent(self) -> bool:
        """
            Check if headers have been sent.
            
            :returns: True if headers have been sent.
        """
        return self._headers_sent


    def write_status_line(self, status_code: int, reason: Optional[str] = None) -> None:
        """
            Write HTTP status line to the socket.
            
            Writes a valid HTTP/1.1 status line in the format:
            HTTP/1.1 <status_code> <reason_phrase>
            
            :param status_code: HTTP status code (e.g., 200, 404).
            :param reason: Optional reason phrase. Uses default if not provided.
        """
        if reason is None:
            reason = HTTP_STATUS_PHRASES.get(status_code, "Unknown")
        
        status_line = f"HTTP/1.1 {status_code} {reason}\r\n"
        self._write_raw(status_line.encode("ascii"))
        return
    
    def write_headers(
        self,
        headers: List[Tuple[str, str]],
        include_date: bool = True,
        include_server: bool = True
    ) -> None:
        """
            Write HTTP headers to the socket.
            
            Writes headers in correct HTTP format with CRLF line endings.
            Optionally adds Date and Server headers if not already present.
            
            :param headers: List of (name, value) header tuples.
            :param include_date: If True, add Date header if not present.
            :param include_server: If True, add Server header if not present.
        """
        # Track which headers are present
        header_names_lower = {name.lower() for name, _ in headers}
        
        # Write provided headers
        for name, value in headers:
            header_line = f"{name}: {value}\r\n"
            self._write_raw(header_line.encode("latin-1"))
        
        # Add Date header if not present
        if include_date and "date" not in header_names_lower:
            date_value = self._format_http_date()
            date_line = f"Date: {date_value}\r\n"
            self._write_raw(date_line.encode("ascii"))
        
        # Add Server header if not present
        if include_server and "server" not in header_names_lower:
            server_line = f"Server: {SERVER_NAME}\r\n"
            self._write_raw(server_line.encode("ascii"))
        
        # Write empty line to end headers
        self._write_raw(b"\r\n")
        self._headers_sent = True
        return
    
    def _format_http_date(self) -> str:
        """
            Format current time as HTTP date.
            
            Returns date in RFC 7231 format:
            Sun, 06 Nov 1994 08:49:37 GMT
            
            :returns: Formatted date string.
        """
        now = datetime.now(timezone.utc)
        # Format: Day, DD Mon YYYY HH:MM:SS GMT
        rtnval = now.strftime("%a, %d %b %Y %H:%M:%S GMT")
        return rtnval
    
    def write_body(self, body: bytes) -> None:
        """
            Write response body with Content-Length.
            
            Writes the complete body to the socket. This method assumes
            Content-Length header has already been set appropriately.
            
            :param body: Response body bytes.
        """
        if len(body) > 0:
            self._write_raw(body)
        return
    
    def write_body_iterator(self, body_iterator: Iterable[bytes]) -> None:
        """
            Write response body from an iterator.
            
            Iterates over the body iterator and writes each chunk.
            
            :param body_iterator: Iterable yielding body chunks.
        """
        for chunk in body_iterator:
            if len(chunk) > 0:
                self._write_raw(chunk)
        return
    
    def write_chunked(self, body_iterator: Iterable[bytes]) -> None:
        """
            Write response body using chunked transfer encoding.
            
            Writes each chunk from the iterator in chunked format:
            <chunk_size_hex>\r\n<chunk_data>\r\n
            
            Ends with a zero-length chunk: 0\r\n\r\n
            
            :param body_iterator: Iterable yielding body chunks.
        """
        for chunk in body_iterator:
            if len(chunk) > 0:
                # Write chunk size in hex
                chunk_size = f"{len(chunk):x}\r\n"
                self._write_raw(chunk_size.encode("ascii"))
                
                # Write chunk data
                self._write_raw(chunk)
                
                # Write trailing CRLF
                self._write_raw(b"\r\n")
        
        # Write terminating zero-length chunk
        self._write_raw(b"0\r\n\r\n")
        return
    
    def flush(self) -> None:
        """
            Flush buffered data to the socket.
            
            Sends any buffered data immediately. This is useful for
            streaming responses where data should be sent as soon as
            it is available.
        """
        if len(self._buffer) > 0:
            self._send_buffer()
        return
    
    def _write_raw(self, data: bytes) -> None:
        """
            Write raw bytes to the buffer.
            
            Adds data to the internal buffer and flushes when the buffer
            reaches the threshold size.
            
            :param data: Bytes to write.
        """
        self._buffer += data
        
        # Flush if buffer is large enough
        if len(self._buffer) >= DEFAULT_BUFFER_SIZE:
            self._send_buffer()
        
        return
    
    def _send_buffer(self) -> None:
        """
            Send buffered data to the socket.
            
            Sends all buffered data and clears the buffer.
        """
        if len(self._buffer) == 0:
            return
        
        total_sent = 0
        data_to_send = self._buffer
        
        while total_sent < len(data_to_send):
            try:
                sent = self._socket.send(data_to_send[total_sent:])
                if sent == 0:
                    # Connection closed
                    break
                total_sent += sent
            except socket.error:
                # Socket error, stop sending
                break
        
        self._buffer = b""
        return
    
    def write_response(
        self,
        status_code: int,
        headers: List[Tuple[str, str]],
        body: bytes,
        reason: Optional[str] = None
    ) -> None:
        """
            Write a complete HTTP response.
            
            Convenience method that writes status line, headers, and body
            in a single call.
            
            :param status_code: HTTP status code.
            :param headers: List of (name, value) header tuples.
            :param body: Response body bytes.
            :param reason: Optional reason phrase.
        """
        self.write_status_line(status_code, reason)
        self.write_headers(headers)
        self.write_body(body)
        self.flush()
        return
    
    def write_error_response(
        self,
        status_code: int,
        message: str
    ) -> bytes:
        """
            Write an HTTP error response.
            
            Creates and writes a minimal error response with the given
            status code and message.
            
            :param status_code: HTTP status code.
            :param message: Error message for the body.
            
            :returns: The response bytes that were written.
        """
        reason = HTTP_STATUS_PHRASES.get(status_code, "Error")
        body = f"{status_code} {reason}: {message}".encode("utf-8")
        
        headers: List[Tuple[str, str]] = [
            ("Content-Type", "text/plain; charset=utf-8"),
            ("Content-Length", str(len(body))),
            ("Connection", "close"),
        ]
        
        self.write_response(status_code, headers, body, reason)
        
        rtnval = body
        return rtnval
    
    def close(self) -> None:
        """
            Close the writer and flush any remaining data.
            
            Flushes the buffer but does not close the socket.
        """
        self.flush()
        return
