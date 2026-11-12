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
from ccai.webworks.wsgi.headervalidation import (
    validate_headers,
    validate_reason_phrase,
)


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
        
        A failed send is never hidden. The error is raised to the caller, which
        must stop producing the response and close the connection.
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
        self._chunked: bool = False
        self._chunked_finished: bool = False
        self._body_discarded: bool = False
        self._body_limit: Optional[int] = None
        self._body_bytes_written: int = 0
        self._body_truncated: bool = False
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
    
    @property
    def chunked(self) -> bool:
        """
            Check if the body is written with chunked transfer encoding.
            
            :returns: True if 'write_body' frames what it writes as chunks.
        """
        return self._chunked
    
    @property
    def body_discarded(self) -> bool:
        """
            Check if body bytes are dropped instead of written.
            
            :returns: True if the response must not carry a body.
        """
        return self._body_discarded
    
    @property
    def body_limit(self) -> Optional[int]:
        """
            Get the number of body bytes the response declared.
            
            :returns: The declared Content-Length or None if none was declared.
        """
        return self._body_limit
    
    @property
    def body_bytes_written(self) -> int:
        """
            Get the number of body bytes written so far.
            
            :returns: Number of body bytes passed to the connection.
        """
        return self._body_bytes_written
    
    @property
    def body_truncated(self) -> bool:
        """
            Check if body bytes beyond the declared length were dropped.
            
            :returns: True if the application wrote more than it declared.
        """
        return self._body_truncated
    
    @property
    def body_complete(self) -> bool:
        """
            Check if the body written matches what the response declared.
            
            :returns: False only when a Content-Length was declared and fewer
                      bytes than that were written.
        """
        if self._body_discarded or self._body_limit is None:
            rtnval = True
        else:
            rtnval = self._body_bytes_written >= self._body_limit
        return rtnval
    
    def set_chunked(self, chunked: bool) -> None:
        """
            Choose whether 'write_body' frames the body as chunks.
            
            :param chunked: True to use chunked transfer encoding.
        """
        self._chunked = chunked
        return
    
    def set_body_discarded(self, discarded: bool) -> None:
        """
            Choose whether body bytes are dropped instead of written.
            
            This is set for responses that must not carry a body: the response
            to a HEAD request and responses with a 1xx, 204 or 304 status.
            
            :param discarded: True to drop every body byte.
        """
        self._body_discarded = discarded
        return
    
    def set_body_limit(self, limit: Optional[int]) -> None:
        """
            Set the number of body bytes the response declared.
            
            Bytes beyond the limit are dropped, because writing them would run
            into the next response on a connection that is kept alive.
            
            :param limit: The declared Content-Length, or None for no limit.
        """
        self._body_limit = limit
        return


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
        
        validate_reason_phrase(reason)
        
        status_line = f"HTTP/1.1 {int(status_code)} {reason}\r\n"
        self._write_raw(status_line.encode("latin-1"))
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
            
            :raises: InvalidResponseHeader if a header name or value is not safe
                     to write. Nothing is written in that case.
        """
        # Refuse the whole header block before any of it is written
        validate_headers(headers)
        
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
            Write response body bytes.
            
            The bytes are framed as a chunk when chunked transfer encoding has
            been chosen, dropped when the response must not carry a body, and
            cut off at the declared Content-Length when one was set.
            
            :param body: Response body bytes.
        """
        if len(body) == 0:
            return
        
        if self._body_discarded:
            return
        
        if self._body_limit is not None:
            room = self._body_limit - self._body_bytes_written
            if len(body) > room:
                self._body_truncated = True
                body = body[:room]
            
            if len(body) == 0:
                return
        
        self._body_bytes_written += len(body)
        
        if self._chunked:
            self._write_chunk(body)
        else:
            self._write_raw(body)
        
        return
    
    def _write_chunk(self, chunk: bytes) -> None:
        """
            Write one chunk in chunked transfer encoding.
            
            :param chunk: Chunk data, must not be empty because an empty chunk
                          ends the body.
        """
        chunk_size = f"{len(chunk):x}\r\n"
        self._write_raw(chunk_size.encode("ascii"))
        self._write_raw(chunk)
        self._write_raw(b"\r\n")
        return
    
    def finish(self) -> None:
        """
            Finish the response body and flush it to the socket.
            
            Writes the terminating chunk when chunked transfer encoding is in
            use. Call this once after the last body bytes, and only when the
            body was produced without an error: a body that stops without its
            terminating chunk is how the client learns it was cut short.
        """
        if self._chunked and not self._chunked_finished and not self._body_discarded:
            self._write_raw(b"0\r\n\r\n")
            self._chunked_finished = True
        
        self.flush()
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
                self._write_chunk(chunk)
        
        # Write terminating zero-length chunk
        self._write_raw(b"0\r\n\r\n")
        self._chunked_finished = True
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
            
            Sends all buffered data and clears the buffer. The buffer is cleared
            even when the send fails, what could not be sent is lost and the
            response is incomplete.
            
            :raises: OSError if the socket reports an error or times out.
            :raises: BrokenPipeError if the client closed the connection.
        """
        if len(self._buffer) == 0:
            return
        
        total_sent = 0
        data_to_send = self._buffer
        self._buffer = b""
        
        while total_sent < len(data_to_send):
            sent = self._socket.send(data_to_send[total_sent:])
            if sent == 0:
                errmsg = "The client closed the connection while the response was being sent"
                raise BrokenPipeError(errmsg)
            total_sent += sent
        
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
