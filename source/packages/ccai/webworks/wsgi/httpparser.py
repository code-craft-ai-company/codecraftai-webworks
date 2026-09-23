"""
    HTTP request parser module for the WSGI layer.
    
    This module provides the HTTPParser class for parsing HTTP requests from
    socket data and constructing valid WSGI environ dictionaries.
"""

import io
import socket
from typing import Any, Dict, IO, List, Optional, Tuple

from ccai.webworks.wsgi.serverconfig import ServerConfig
from ccai.webworks.wsgi.exceptions import (
    RequestParseError,
    HeaderTooLarge,
    TooManyHeaders,
)


# HTTP methods supported by the parser
SUPPORTED_METHODS: Tuple[str, ...] = (
    "GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS",
    "CONNECT", "TRACE",
)

# HTTP versions supported by the parser
SUPPORTED_VERSIONS: Tuple[str, ...] = ("HTTP/1.0", "HTTP/1.1")

# Default buffer size for reading from socket
DEFAULT_BUFFER_SIZE: int = 8192


class HTTPParser:
    """
        Parses HTTP requests from socket data.
        
        This class handles parsing of HTTP request lines, headers, and body
        according to RFC 7230. It enforces configurable limits on header size
        and count to prevent resource exhaustion attacks.
    """
    
    def __init__(self, config: Optional[ServerConfig] = None):
        """
            Construct an HTTP parser.
            
            :param config: Server configuration for limits. If None, uses defaults.
        """
        if config is not None:
            self._config = config
        else:
            self._config = ServerConfig()
        
        self._max_header_size = self._config.max_header_size
        self._max_headers = self._config.max_headers
        self._max_request_size = self._config.max_request_size
        return
    
    @property
    def max_header_size(self) -> int:
        """
            Get the maximum header size limit.
            
            :returns: Maximum header size in bytes.
        """
        return self._max_header_size
    
    @property
    def max_headers(self) -> int:
        """
            Get the maximum number of headers limit.
            
            :returns: Maximum number of headers.
        """
        return self._max_headers
    
    @property
    def max_request_size(self) -> int:
        """
            Get the maximum request size limit.
            
            :returns: Maximum request size in bytes (0 = unlimited).
        """
        return self._max_request_size

    
    def parse_request_line(self, line: bytes) -> Tuple[str, str, str]:
        """
            Parse HTTP request line.
            
            Parses a request line in the format: METHOD PATH HTTP/VERSION
            
            :param line: Raw request line bytes.
            
            :returns: Tuple of (method, path, http_version).
            
            :raises: RequestParseError if the request line is malformed.
        """
        # Decode the line, stripping any trailing whitespace
        try:
            line_str = line.decode("ascii").strip()
        except UnicodeDecodeError as decode_err:
            errmsg = "Invalid characters in request line"
            raise RequestParseError(errmsg) from decode_err
        
        if len(line_str) == 0:
            errmsg = "Empty request line"
            raise RequestParseError(errmsg)
        
        # Split the request line into parts
        parts = line_str.split(" ")
        
        if len(parts) < 3:
            errmsg = f"Malformed request line: expected 'METHOD PATH HTTP/VERSION', got '{line_str}'"
            raise RequestParseError(errmsg)
        
        # Extract method, path, and version
        method = parts[0].upper()
        http_version = parts[-1].upper()
        
        # Path may contain spaces (though unusual), so join middle parts
        path = " ".join(parts[1:-1])
        
        # Validate method
        if method not in SUPPORTED_METHODS:
            errmsg = f"Unsupported HTTP method: {method}"
            raise RequestParseError(errmsg)
        
        # Validate HTTP version
        if http_version not in SUPPORTED_VERSIONS:
            errmsg = f"Unsupported HTTP version: {http_version}"
            raise RequestParseError(errmsg)
        
        # Validate path starts with /
        if not path.startswith("/") and not path.startswith("*"):
            # Allow * for OPTIONS requests
            if method != "OPTIONS" or path != "*":
                # Check if it's an absolute URI (for proxy requests)
                if not path.lower().startswith("http://") and not path.lower().startswith("https://"):
                    errmsg = f"Invalid request path: {path}"
                    raise RequestParseError(errmsg)
        
        rtnval = (method, path, http_version)
        return rtnval
    
    def _extract_path_and_query(self, raw_path: str) -> Tuple[str, str]:
        """
            Extract path and query string from a raw path.
            
            :param raw_path: Raw path possibly containing query string.
            
            :returns: Tuple of (path, query_string).
        """
        if "?" in raw_path:
            path, query_string = raw_path.split("?", 1)
        else:
            path = raw_path
            query_string = ""
        
        rtnval = (path, query_string)
        return rtnval

    
    def parse_headers(self, header_lines: List[bytes]) -> Dict[str, str]:
        """
            Parse HTTP headers from a list of header lines.
            
            Handles header continuation lines (folded headers) according to RFC 7230.
            Enforces header size and count limits.
            
            :param header_lines: List of raw header line bytes.
            
            :returns: Dict of header name to value.
            
            :raises: HeaderTooLarge if total header size exceeds limit.
            :raises: TooManyHeaders if header count exceeds limit.
            :raises: RequestParseError if headers are malformed.
        """
        headers: Dict[str, str] = {}
        total_size = 0
        header_count = 0
        current_name: Optional[str] = None
        current_value: Optional[str] = None
        
        for line in header_lines:
            # Track total header size
            total_size += len(line)
            if self._max_header_size > 0 and total_size > self._max_header_size:
                raise HeaderTooLarge(self._max_header_size)
            
            # Decode the line
            try:
                line_str = line.decode("latin-1")
            except UnicodeDecodeError as decode_err:
                errmsg = "Invalid characters in header"
                raise RequestParseError(errmsg) from decode_err
            
            # Check for header continuation (line starts with whitespace)
            if len(line_str) > 0 and line_str[0] in (" ", "\t"):
                if current_name is None:
                    errmsg = "Header continuation without preceding header"
                    raise RequestParseError(errmsg)
                # Append to current header value (folded header)
                current_value = current_value + " " + line_str.strip()
                continue
            
            # Save previous header if exists
            if current_name is not None:
                headers[current_name] = current_value
            
            # Skip empty lines
            line_str = line_str.strip()
            if len(line_str) == 0:
                current_name = None
                current_value = None
                continue
            
            # Parse header name and value
            if ":" not in line_str:
                errmsg = f"Malformed header line: {line_str}"
                raise RequestParseError(errmsg)
            
            colon_pos = line_str.index(":")
            name = line_str[:colon_pos].strip()
            value = line_str[colon_pos + 1:].strip()
            
            # Validate header name (no whitespace allowed)
            if " " in name or "\t" in name:
                errmsg = f"Invalid header name: {name}"
                raise RequestParseError(errmsg)
            
            # Check header count limit
            header_count += 1
            if self._max_headers > 0 and header_count > self._max_headers:
                raise TooManyHeaders(self._max_headers)
            
            current_name = name
            current_value = value
        
        # Save last header if exists
        if current_name is not None:
            headers[current_name] = current_value
        
        rtnval = headers
        return rtnval
    
    def parse_headers_from_socket(self, sock: socket.socket) -> Dict[str, str]:
        """
            Parse HTTP headers from a socket.
            
            Reads header lines from the socket until an empty line is encountered.
            
            :param sock: Socket to read from.
            
            :returns: Dict of header name to value.
            
            :raises: HeaderTooLarge if total header size exceeds limit.
            :raises: TooManyHeaders if header count exceeds limit.
            :raises: RequestParseError if headers are malformed.
        """
        header_lines: List[bytes] = []
        total_size = 0
        
        while True:
            line = self._read_line(sock)
            
            # Track total size
            total_size += len(line)
            if self._max_header_size > 0 and total_size > self._max_header_size:
                raise HeaderTooLarge(self._max_header_size)
            
            # Empty line signals end of headers
            stripped = line.strip()
            if len(stripped) == 0:
                break
            
            header_lines.append(line)
        
        rtnval = self.parse_headers(header_lines)
        return rtnval
    
    def _read_line(self, sock: socket.socket) -> bytes:
        """
            Read a line from a socket.
            
            Reads bytes until CRLF or LF is encountered.
            
            :param sock: Socket to read from.
            
            :returns: Line bytes including line ending.
        """
        line = b""
        while True:
            try:
                char = sock.recv(1)
            except socket.error:
                break
            
            if len(char) == 0:
                break
            
            line += char
            
            if char == b"\n":
                break
        
        rtnval = line
        return rtnval

    
    def parse_chunked_body(self, sock: socket.socket) -> bytes:
        """
            Parse a chunked transfer encoded request body.
            
            Reads chunks from the socket until a zero-length chunk is encountered.
            
            :param sock: Socket to read from.
            
            :returns: Complete body bytes.
            
            :raises: RequestParseError if chunked encoding is malformed.
        """
        body_parts: List[bytes] = []
        total_size = 0
        
        while True:
            # Read chunk size line
            size_line = self._read_line(sock)
            
            try:
                size_str = size_line.decode("ascii").strip()
            except UnicodeDecodeError as decode_err:
                errmsg = "Invalid characters in chunk size"
                raise RequestParseError(errmsg) from decode_err
            
            # Handle chunk extensions (ignore them)
            if ";" in size_str:
                size_str = size_str.split(";")[0].strip()
            
            # Parse chunk size (hexadecimal)
            try:
                chunk_size = int(size_str, 16)
            except ValueError as val_err:
                errmsg = f"Invalid chunk size: {size_str}"
                raise RequestParseError(errmsg) from val_err
            
            # Zero-length chunk signals end of body
            if chunk_size == 0:
                # Read trailing CRLF after last chunk
                self._read_line(sock)
                break
            
            # Check size limit
            total_size += chunk_size
            if self._max_request_size > 0 and total_size > self._max_request_size:
                errmsg = f"Chunked body exceeds maximum size of {self._max_request_size} bytes"
                raise RequestParseError(errmsg)
            
            # Read chunk data
            chunk_data = self._read_exact(sock, chunk_size)
            if len(chunk_data) != chunk_size:
                errmsg = f"Incomplete chunk: expected {chunk_size} bytes, got {len(chunk_data)}"
                raise RequestParseError(errmsg)
            
            body_parts.append(chunk_data)
            
            # Read trailing CRLF after chunk data
            trailing = self._read_line(sock)
            if trailing.strip() != b"":
                errmsg = "Missing CRLF after chunk data"
                raise RequestParseError(errmsg)
        
        rtnval = b"".join(body_parts)
        return rtnval
    
    def _read_exact(self, sock: socket.socket, size: int) -> bytes:
        """
            Read exactly the specified number of bytes from a socket.
            
            :param sock: Socket to read from.
            :param size: Number of bytes to read.
            
            :returns: Bytes read.
        """
        data = b""
        remaining = size
        
        while remaining > 0:
            try:
                chunk = sock.recv(min(remaining, DEFAULT_BUFFER_SIZE))
            except socket.error:
                break
            
            if len(chunk) == 0:
                break
            
            data += chunk
            remaining -= len(chunk)
        
        rtnval = data
        return rtnval
    
    def create_chunked_body_stream(self, sock: socket.socket) -> IO[bytes]:
        """
            Create a file-like object for reading a chunked body.
            
            This allows lazy reading of chunked bodies without loading
            the entire body into memory.
            
            :param sock: Socket to read from.
            
            :returns: File-like object for reading the body.
        """
        # For simplicity, read the entire chunked body and wrap in BytesIO
        # A more sophisticated implementation could stream chunks
        body = self.parse_chunked_body(sock)
        rtnval = io.BytesIO(body)
        return rtnval

    
    def build_environ(
        self,
        method: str,
        path: str,
        http_version: str,
        headers: Dict[str, str],
        body_stream: IO[bytes],
        client_addr: Tuple[str, int],
        server_addr: Tuple[str, int],
        scheme: str = "http"
    ) -> Dict[str, Any]:
        """
            Build WSGI environ dictionary from parsed request.
            
            Constructs a complete WSGI environ dictionary containing all
            required CGI and WSGI keys.
            
            :param method: HTTP method.
            :param path: Request path (may include query string).
            :param http_version: HTTP version string.
            :param headers: Parsed headers dictionary.
            :param body_stream: File-like object for request body.
            :param client_addr: Client address tuple (host, port).
            :param server_addr: Server address tuple (host, port).
            :param scheme: URL scheme (http or https).
            
            :returns: Complete WSGI environ dict.
        """
        # Extract path and query string
        path_info, query_string = self._extract_path_and_query(path)
        
        # Build the environ dictionary
        environ: Dict[str, Any] = {}
        
        # CGI variables (required)
        environ["REQUEST_METHOD"] = method
        environ["SCRIPT_NAME"] = ""
        environ["PATH_INFO"] = path_info
        environ["QUERY_STRING"] = query_string
        environ["SERVER_NAME"] = server_addr[0]
        environ["SERVER_PORT"] = str(server_addr[1])
        environ["SERVER_PROTOCOL"] = http_version
        
        # WSGI variables (required)
        environ["wsgi.version"] = (1, 0)
        environ["wsgi.url_scheme"] = scheme
        environ["wsgi.input"] = body_stream
        environ["wsgi.errors"] = io.StringIO()
        environ["wsgi.multithread"] = True
        environ["wsgi.multiprocess"] = True
        environ["wsgi.run_once"] = False
        
        # Optional CGI variables
        environ["REMOTE_ADDR"] = client_addr[0]
        environ["REMOTE_HOST"] = client_addr[0]
        environ["REMOTE_PORT"] = str(client_addr[1])
        
        # Convert headers to CGI/environ format
        for header_name, header_value in headers.items():
            header_name_upper = header_name.upper()
            
            # Content-Type and Content-Length are special
            if header_name_upper == "CONTENT-TYPE":
                environ["CONTENT_TYPE"] = header_value
            elif header_name_upper == "CONTENT-LENGTH":
                environ["CONTENT_LENGTH"] = header_value
            else:
                # Other headers get HTTP_ prefix
                environ_key = "HTTP_" + header_name_upper.replace("-", "_")
                environ[environ_key] = header_value
        
        # Set Host header info if present
        host_header = headers.get("Host") or headers.get("host")
        if host_header is not None:
            # The Host header may carry a port; it is passed through as-is and does not
            # override SERVER_NAME/PORT, which come from the actual server address.
            environ["HTTP_HOST"] = host_header
        
        rtnval = environ
        return rtnval
    
    def parse_request(
        self,
        sock: socket.socket,
        client_addr: Tuple[str, int],
        server_addr: Tuple[str, int],
        scheme: str = "http"
    ) -> Dict[str, Any]:
        """
            Parse a complete HTTP request from socket and build environ.
            
            This is the main entry point for parsing HTTP requests.
            
            :param sock: Socket to read from.
            :param client_addr: Client address tuple (host, port).
            :param server_addr: Server address tuple (host, port).
            :param scheme: URL scheme (http or https).
            
            :returns: Complete WSGI environ dict.
            
            :raises: RequestParseError if request is malformed.
        """
        # Read and parse request line
        request_line = self._read_line(sock)
        if len(request_line.strip()) == 0:
            errmsg = "Empty request"
            raise RequestParseError(errmsg)
        
        method, path, http_version = self.parse_request_line(request_line)
        
        # Parse headers
        headers = self.parse_headers_from_socket(sock)
        
        # Determine body handling
        content_length_str = headers.get("Content-Length") or headers.get("content-length")
        transfer_encoding = headers.get("Transfer-Encoding") or headers.get("transfer-encoding")
        
        if transfer_encoding is not None and "chunked" in transfer_encoding.lower():
            # Chunked transfer encoding
            body_stream = self.create_chunked_body_stream(sock)
        elif content_length_str is not None:
            # Fixed-length body
            try:
                content_length = int(content_length_str)
            except ValueError as val_err:
                errmsg = f"Invalid Content-Length: {content_length_str}"
                raise RequestParseError(errmsg) from val_err
            
            if content_length < 0:
                errmsg = f"Negative Content-Length: {content_length}"
                raise RequestParseError(errmsg)
            
            # Check size limit
            if self._max_request_size > 0 and content_length > self._max_request_size:
                errmsg = f"Request body exceeds maximum size of {self._max_request_size} bytes"
                raise RequestParseError(errmsg)
            
            body_data = self._read_exact(sock, content_length)
            body_stream = io.BytesIO(body_data)
        else:
            # No body
            body_stream = io.BytesIO(b"")
        
        # Build and return environ
        rtnval = self.build_environ(
            method=method,
            path=path,
            http_version=http_version,
            headers=headers,
            body_stream=body_stream,
            client_addr=client_addr,
            server_addr=server_addr,
            scheme=scheme
        )
        return rtnval

    
    def validate_request_line(self, line: bytes) -> bool:
        """
            Validate that a request line is well-formed.
            
            :param line: Raw request line bytes.
            
            :returns: True if valid, False otherwise.
        """
        try:
            self.parse_request_line(line)
            rtnval = True
        except RequestParseError:
            rtnval = False
        return rtnval
    
    def validate_headers(self, header_lines: List[bytes]) -> bool:
        """
            Validate that headers are well-formed.
            
            :param header_lines: List of raw header line bytes.
            
            :returns: True if valid, False otherwise.
        """
        try:
            self.parse_headers(header_lines)
            rtnval = True
        except (RequestParseError, HeaderTooLarge, TooManyHeaders):
            rtnval = False
        return rtnval
    
    def is_valid_method(self, method: str) -> bool:
        """
            Check if a method is valid.
            
            :param method: HTTP method string.
            
            :returns: True if valid, False otherwise.
        """
        rtnval = method.upper() in SUPPORTED_METHODS
        return rtnval
    
    def is_valid_http_version(self, version: str) -> bool:
        """
            Check if an HTTP version is valid.
            
            :param version: HTTP version string.
            
            :returns: True if valid, False otherwise.
        """
        rtnval = version.upper() in SUPPORTED_VERSIONS
        return rtnval
    
    def format_error_response(self, status_code: int, message: str) -> bytes:
        """
            Format an HTTP error response.
            
            Creates a minimal HTTP response for error conditions.
            
            :param status_code: HTTP status code.
            :param message: Error message.
            
            :returns: Complete HTTP response bytes.
        """
        from ccai.webworks.wsgi.constants import HTTP_STATUS_PHRASES
        
        reason = HTTP_STATUS_PHRASES.get(status_code, "Error")
        body = f"{status_code} {reason}: {message}".encode("utf-8")
        
        response_lines = [
            f"HTTP/1.1 {status_code} {reason}".encode("ascii"),
            b"Content-Type: text/plain; charset=utf-8",
            f"Content-Length: {len(body)}".encode("ascii"),
            b"Connection: close",
            b"",
            body,
        ]
        
        rtnval = b"\r\n".join(response_lines)
        return rtnval
    
    def create_bad_request_response(self, detail: str) -> bytes:
        """
            Create an HTTP 400 Bad Request response.
            
            :param detail: Description of what is wrong with the request.
            
            :returns: Complete HTTP response bytes.
        """
        rtnval = self.format_error_response(400, detail)
        return rtnval
