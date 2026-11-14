"""
    HTTP request parser module for the WSGI layer.
    
    This module provides the HTTPParser class for parsing HTTP requests from
    socket data and constructing valid WSGI environ dictionaries.
"""

import io
import re
import socket
from typing import Any, Dict, IO, List, Optional, Tuple, Union
from urllib.parse import unquote_to_bytes, urlsplit

from ccai.webworks.wsgi.headervalidation import HEADER_NAME_PATTERN
from ccai.webworks.wsgi.serverconfig import ServerConfig
from ccai.webworks.wsgi.socketreader import SocketReader
from ccai.webworks.wsgi.exceptions import (
    ConnectionClosed,
    HeaderTooLarge,
    IncompleteRequest,
    LineTooLong,
    RequestEntityTooLarge,
    RequestLineTooLong,
    RequestParseError,
    RequestTimeout,
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

# Limit for a chunk size line or a trailer section when the header size limit
# has been turned off. Framing lines are never read without a limit.
DEFAULT_FRAMING_LINE_SIZE: int = 8192

# A Content-Length value is one or more ASCII digits and nothing else. The
# 'int' builtin is far more lenient ('+5', '5_0', ' 5 ', other digit scripts),
# and every extra form is a chance for a proxy in front of this server to
# frame the same request differently.
CONTENT_LENGTH_PATTERN = re.compile(r"[0-9]+")

# A chunk size is one to sixteen hexadecimal digits and nothing else
CHUNK_SIZE_PATTERN = re.compile(r"[0-9A-Fa-f]{1,16}")

# The type of the objects the parser can read a request from
RequestSource = Union[socket.socket, SocketReader]


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
        
        self._max_request_line = self._config.max_request_line
        self._max_header_size = self._config.max_header_size
        self._max_headers = self._config.max_headers
        self._max_request_size = self._config.max_request_size
        return
    
    @property
    def max_request_line(self) -> int:
        """
            Get the maximum request line size limit.
            
            :returns: Maximum request line size in bytes (0 = unlimited).
        """
        return self._max_request_line
    
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
        names_seen: Dict[str, str] = {}
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
                continuation = line_str.strip()
                self._check_header_value(current_name, continuation)
                current_value = current_value + " " + continuation
                continue
            
            # Save previous header if exists
            if current_name is not None:
                self._store_header(headers, names_seen, current_name, current_value)
            
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
            name = line_str[:colon_pos]
            value = line_str[colon_pos + 1:].strip()
            
            # Validate header name. Whitespace between the name and the colon
            # is rejected and not stripped: a proxy that does not strip it sees
            # a different header than this server would.
            if HEADER_NAME_PATTERN.fullmatch(name) is None:
                errmsg = f"Invalid header name: {name}"
                raise RequestParseError(errmsg)
            
            self._check_header_value(name, value)
            
            # Check header count limit
            header_count += 1
            if self._max_headers > 0 and header_count > self._max_headers:
                raise TooManyHeaders(self._max_headers)
            
            current_name = name
            current_value = value
        
        # Save last header if exists
        if current_name is not None:
            self._store_header(headers, names_seen, current_name, current_value)
        
        rtnval = headers
        return rtnval
    
    def _check_header_value(self, name: str, value: str) -> None:
        """
            Check that a header value holds no character that ends a line.
            
            :param name: Header name, used in the error message.
            :param value: Header value with the line ending already removed.
            
            :raises: RequestParseError if the value contains CR, LF or NUL.
        """
        for forbidden in ("\r", "\n", "\x00"):
            if forbidden in value:
                errmsg = f"Invalid character in the value of header '{name}'"
                raise RequestParseError(errmsg)
        return
    
    def _store_header(
        self,
        headers: Dict[str, str],
        names_seen: Dict[str, str],
        name: str,
        value: str
    ) -> None:
        """
            Store a parsed header, combining it with an earlier header of the same name.
            
            Header names are compared without regard to case. A repeated header is
            joined to the earlier value with ', ' as RFC 7230 section 3.2.2 allows,
            except Cookie which is joined with '; '. The framing headers are not
            joined: a second Content-Length must repeat the first value and a
            second Host is refused.
            
            :param headers: Headers collected so far, keyed by the first spelling
                            seen of each name.
            :param names_seen: Map of lower case header name to the key used
                               in 'headers'.
            :param name: Name of the header to store.
            :param value: Value of the header to store.
            
            :raises: RequestParseError if the header conflicts with an earlier one.
        """
        name_lower = name.lower()
        
        if name_lower not in names_seen:
            names_seen[name_lower] = name
            headers[name] = value
            return
        
        stored_name = names_seen[name_lower]
        stored_value = headers[stored_name]
        
        if name_lower == "content-length":
            if stored_value != value:
                errmsg = "Conflicting Content-Length headers"
                raise RequestParseError(errmsg)
        elif name_lower == "host":
            errmsg = "More than one Host header"
            raise RequestParseError(errmsg)
        elif name_lower == "cookie":
            headers[stored_name] = stored_value + "; " + value
        else:
            headers[stored_name] = stored_value + ", " + value
        
        return
    
    def _get_header(self, headers: Dict[str, str], name: str) -> Optional[str]:
        """
            Look up a header without regard to the case of its name.
            
            :param headers: Parsed headers dictionary.
            :param name: Header name to look up.
            
            :returns: The header value or None if the header is not present.
        """
        rtnval: Optional[str] = None
        name_lower = name.lower()
        
        for header_name, header_value in headers.items():
            if header_name.lower() == name_lower:
                rtnval = header_value
                break
        
        return rtnval
    
    def _get_reader(self, source: RequestSource) -> SocketReader:
        """
            Get the reader to use for a request source.
            
            A SocketReader is used as it is, so the bytes it has read ahead stay
            available across calls. A plain socket is wrapped in a reader that
            does not read ahead, so no byte the caller did not ask for is taken
            from the socket.
            
            :param source: Socket or SocketReader to read from.
            
            :returns: SocketReader for the source.
        """
        if isinstance(source, SocketReader):
            rtnval = source
        else:
            rtnval = SocketReader(source, read_ahead=False)
        return rtnval
    
    def parse_headers_from_socket(self, sock: RequestSource) -> Dict[str, str]:
        """
            Parse HTTP headers from a socket.
            
            Reads header lines from the socket until an empty line is encountered.
            The size and count limits are enforced while the lines are read, so
            headers over the limit are refused without being held in memory.
            
            :param sock: Socket or SocketReader to read from.
            
            :returns: Dict of header name to value.
            
            :raises: HeaderTooLarge if total header size exceeds limit.
            :raises: TooManyHeaders if header count exceeds limit.
            :raises: IncompleteRequest if the connection closed inside the headers.
            :raises: RequestParseError if headers are malformed.
        """
        reader = self._get_reader(sock)
        header_lines = self._read_header_section(reader)
        
        rtnval = self.parse_headers(header_lines)
        return rtnval
    
    def _read_header_section(self, reader: SocketReader) -> List[bytes]:
        """
            Read the lines of a header section, up to the empty line that ends it.
            
            :param reader: SocketReader to read from.
            
            :returns: List of raw header lines without the terminating empty line.
            
            :raises: HeaderTooLarge if total header size exceeds limit.
            :raises: TooManyHeaders if header count exceeds limit.
            :raises: IncompleteRequest if the connection closed inside the section.
        """
        header_lines: List[bytes] = []
        total_size = 0
        header_count = 0
        
        while True:
            if self._max_header_size > 0:
                line_limit = self._max_header_size - total_size
                if line_limit <= 0:
                    raise HeaderTooLarge(self._max_header_size)
            else:
                line_limit = 0
            
            try:
                line = reader.read_line(line_limit)
            except LineTooLong as long_err:
                raise HeaderTooLarge(self._max_header_size) from long_err
            
            if not line.endswith(b"\n"):
                errmsg = "Connection closed before the end of the headers"
                raise IncompleteRequest(errmsg)
            
            total_size += len(line)
            
            # Only a line that is empty ends the headers. A line of blanks is
            # a continuation line and must not be taken for the end.
            if line == b"\r\n" or line == b"\n":
                break
            
            # Continuation lines extend the header before them
            if not line.startswith((b" ", b"\t")):
                header_count += 1
                if self._max_headers > 0 and header_count > self._max_headers:
                    raise TooManyHeaders(self._max_headers)
            
            header_lines.append(line)
        
        return header_lines
    
    def _read_line(self, sock: RequestSource, max_size: int = 0) -> bytes:
        """
            Read a line from a socket.
            
            Reads bytes until LF is encountered. The line is not allowed to
            grow past the limit.
            
            :param sock: Socket or SocketReader to read from.
            :param max_size: Maximum line size in bytes (0 = unlimited).
            
            :returns: Line bytes including line ending. If the connection closed
                      first, the bytes read so far without a line ending.
            
            :raises: LineTooLong if the line is longer than 'max_size'.
            :raises: socket.timeout if the read timed out.
        """
        reader = self._get_reader(sock)
        rtnval = reader.read_line(max_size)
        return rtnval

    
    def parse_chunked_body(self, sock: RequestSource) -> bytes:
        """
            Parse a chunked transfer encoded request body.
            
            Reads chunks from the socket until a zero-length chunk is encountered,
            then reads and discards the trailer section so the next request on the
            connection starts at the right byte.
            
            :param sock: Socket or SocketReader to read from.
            
            :returns: Complete body bytes.
            
            :raises: RequestParseError if chunked encoding is malformed.
            :raises: IncompleteRequest if the connection closed inside the body.
            :raises: RequestEntityTooLarge if the body exceeds the size limit.
        """
        reader = self._get_reader(sock)
        body_parts: List[bytes] = []
        total_size = 0
        
        if self._max_header_size > 0:
            line_limit = self._max_header_size
        else:
            line_limit = DEFAULT_FRAMING_LINE_SIZE
        
        while True:
            # Read chunk size line
            try:
                size_line = reader.read_line(line_limit)
            except LineTooLong as long_err:
                errmsg = "Chunk size line too long"
                raise RequestParseError(errmsg) from long_err
            
            if not size_line.endswith(b"\n"):
                errmsg = "Connection closed inside a chunked body"
                raise IncompleteRequest(errmsg)
            
            if not size_line.endswith(b"\r\n"):
                errmsg = "Chunk size line not terminated by CRLF"
                raise RequestParseError(errmsg)
            
            try:
                size_str = size_line[:-2].decode("ascii")
            except UnicodeDecodeError as decode_err:
                errmsg = "Invalid characters in chunk size"
                raise RequestParseError(errmsg) from decode_err
            
            # Handle chunk extensions (ignore them)
            if ";" in size_str:
                size_str = size_str.split(";")[0]
            
            # Parse chunk size (hexadecimal digits only)
            if CHUNK_SIZE_PATTERN.fullmatch(size_str) is None:
                errmsg = f"Invalid chunk size: {size_str}"
                raise RequestParseError(errmsg)
            
            chunk_size = int(size_str, 16)
            
            # Zero-length chunk signals end of body
            if chunk_size == 0:
                self._discard_trailers(reader, line_limit)
                break
            
            # Check size limit
            total_size += chunk_size
            if self._max_request_size > 0 and total_size > self._max_request_size:
                raise RequestEntityTooLarge(self._max_request_size, total_size)
            
            # Read chunk data
            chunk_data = reader.read_exact(chunk_size)
            if len(chunk_data) != chunk_size:
                errmsg = f"Incomplete chunk: expected {chunk_size} bytes, got {len(chunk_data)}"
                raise IncompleteRequest(errmsg)
            
            body_parts.append(chunk_data)
            
            # Read the CRLF that follows the chunk data
            trailing = reader.read_exact(2)
            if len(trailing) != 2:
                errmsg = "Connection closed inside a chunked body"
                raise IncompleteRequest(errmsg)
            
            if trailing != b"\r\n":
                errmsg = "Missing CRLF after chunk data"
                raise RequestParseError(errmsg)
        
        rtnval = b"".join(body_parts)
        return rtnval
    
    def _discard_trailers(self, reader: SocketReader, section_limit: int) -> None:
        """
            Read and discard the trailer section that follows the last chunk.
            
            The trailer section is zero or more header lines followed by an empty
            line. It has to be consumed, otherwise its bytes would be parsed as
            the start of the next request on the connection.
            
            :param reader: SocketReader to read from.
            :param section_limit: Maximum size in bytes of the whole trailer section.
            
            :raises: RequestParseError if the trailer section is too large.
            :raises: IncompleteRequest if the connection closed inside the trailers.
        """
        total_size = 0
        
        while True:
            line_limit = section_limit - total_size
            if line_limit <= 0:
                errmsg = "Trailer section too large"
                raise RequestParseError(errmsg, status_code=431)
            
            try:
                line = reader.read_line(line_limit)
            except LineTooLong as long_err:
                errmsg = "Trailer section too large"
                raise RequestParseError(errmsg, status_code=431) from long_err
            
            if not line.endswith(b"\n"):
                errmsg = "Connection closed inside the trailers of a chunked body"
                raise IncompleteRequest(errmsg)
            
            total_size += len(line)
            
            if line == b"\r\n" or line == b"\n":
                break
        
        return
    
    def _read_exact(self, sock: RequestSource, size: int) -> bytes:
        """
            Read exactly the specified number of bytes from a socket.
            
            :param sock: Socket or SocketReader to read from.
            :param size: Number of bytes to read.
            
            :returns: Bytes read. Fewer than 'size' bytes only when the
                      connection closed first.
            
            :raises: socket.timeout if the read timed out.
        """
        reader = self._get_reader(sock)
        rtnval = reader.read_exact(size)
        return rtnval
    
    def create_chunked_body_stream(self, sock: RequestSource) -> IO[bytes]:
        """
            Create a file-like object for reading a chunked body.
            
            This allows lazy reading of chunked bodies without loading
            the entire body into memory.
            
            :param sock: Socket or SocketReader to read from.
            
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
        raw_path, query_string = self._extract_path_and_query(path)
        path_info = self._decode_path(raw_path)
        
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
        # The body stream holds exactly the body of this request and reports
        # end of file after it, so it is safe to read without CONTENT_LENGTH.
        environ["wsgi.input_terminated"] = True
        environ["wsgi.errors"] = io.StringIO()
        environ["wsgi.multithread"] = True
        environ["wsgi.multiprocess"] = True
        environ["wsgi.run_once"] = False
        
        # Optional CGI variables
        environ["REMOTE_ADDR"] = client_addr[0]
        environ["REMOTE_HOST"] = client_addr[0]
        environ["REMOTE_PORT"] = str(client_addr[1])
        
        # The request target exactly as the client sent it
        environ["REQUEST_URI"] = path
        environ["RAW_URI"] = path
        
        # Convert headers to CGI/environ format
        for header_name, header_value in headers.items():
            # The environ key replaces '-' with '_', so 'X-User' and 'X_User'
            # would become the same key. A client could then supply a header
            # that a proxy in front of the server strips or sets. Names with
            # an underscore are not passed to the application.
            if "_" in header_name:
                continue
            
            header_name_upper = header_name.upper()
            
            # Content-Type and Content-Length are special
            if header_name_upper == "CONTENT-TYPE":
                environ["CONTENT_TYPE"] = header_value
            elif header_name_upper == "CONTENT-LENGTH":
                environ["CONTENT_LENGTH"] = header_value
            else:
                # Other headers get HTTP_ prefix. The Host header is passed
                # through as HTTP_HOST and does not override SERVER_NAME/PORT,
                # which come from the actual server address.
                environ_key = "HTTP_" + header_name_upper.replace("-", "_")
                environ[environ_key] = header_value
        
        rtnval = environ
        return rtnval
    
    def _decode_path(self, raw_path: str) -> str:
        """
            Convert the path of a request target into a PATH_INFO value.
            
            PEP 3333 defines PATH_INFO as the percent-decoded path, carried in
            a native string whose characters are the decoded bytes (latin-1).
            A request target in absolute form, as sent to a proxy, is reduced
            to its path first.
            
            :param raw_path: Path part of the request target, without the query string.
            
            :returns: PATH_INFO value.
        """
        target_path = raw_path
        
        target_lower = raw_path.lower()
        if target_lower.startswith("http://") or target_lower.startswith("https://"):
            target_parts = urlsplit(raw_path)
            target_path = target_parts.path
            if len(target_path) == 0:
                target_path = "/"
        
        path_bytes = unquote_to_bytes(target_path)
        rtnval = path_bytes.decode("latin-1")
        return rtnval
    
    def _parse_content_length(self, value: str) -> int:
        """
            Parse a Content-Length header value strictly.
            
            :param value: Content-Length header value.
            
            :returns: Content length in bytes.
            
            :raises: RequestParseError if the value is not a plain decimal number.
        """
        if CONTENT_LENGTH_PATTERN.fullmatch(value) is None:
            errmsg = f"Invalid Content-Length: {value}"
            raise RequestParseError(errmsg)
        
        rtnval = int(value)
        return rtnval
    
    def _read_request_line(self, reader: SocketReader) -> bytes:
        """
            Read the request line of the next request on a connection.
            
            One empty line before the request line is skipped, as RFC 7230
            section 3.5 asks of a robust server.
            
            :param reader: SocketReader to read from.
            
            :returns: Raw request line including its line ending.
            
            :raises: ConnectionClosed if the client closed the connection
                     without sending a request.
            :raises: RequestLineTooLong if the request line exceeds the limit.
            :raises: IncompleteRequest if the connection closed inside the line.
        """
        empty_lines_skipped = 0
        
        while True:
            try:
                request_line = reader.read_line(self._max_request_line)
            except LineTooLong as long_err:
                raise RequestLineTooLong(self._max_request_line) from long_err
            
            if len(request_line) == 0:
                # End of stream before any byte of a request
                raise ConnectionClosed()
            
            if not request_line.endswith(b"\n"):
                errmsg = "Connection closed inside the request line"
                raise IncompleteRequest(errmsg)
            
            if request_line == b"\r\n" or request_line == b"\n":
                if empty_lines_skipped == 0:
                    empty_lines_skipped += 1
                    continue
                
                errmsg = "Empty request"
                raise RequestParseError(errmsg)
            
            break
        
        return request_line
    
    def parse_request(
        self,
        sock: RequestSource,
        client_addr: Tuple[str, int],
        server_addr: Tuple[str, int],
        scheme: str = "http"
    ) -> Dict[str, Any]:
        """
            Parse a complete HTTP request from socket and build environ.
            
            This is the main entry point for parsing HTTP requests. Pass the
            SocketReader of the connection when more than one request is read
            from it, so bytes read ahead are kept for the next request.
            
            A request is only returned when all of it was received. A request
            that is cut short, stalls or has ambiguous framing raises and is
            never handed to the application.
            
            :param sock: Socket or SocketReader to read from.
            :param client_addr: Client address tuple (host, port).
            :param server_addr: Server address tuple (host, port).
            :param scheme: URL scheme (http or https).
            
            :returns: Complete WSGI environ dict.
            
            :raises: ConnectionClosed if the client closed the connection
                     without sending a request.
            :raises: RequestParseError if request is malformed.
            :raises: RequestEntityTooLarge if the body exceeds the size limit.
            :raises: RequestTimeout if the client stalled part way through
                     a request.
            :raises: socket.timeout if no request arrived before the timeout.
        """
        reader = self._get_reader(sock)
        
        # A timeout before the first byte of a request is an idle connection
        # and is left to bubble. Once a request has started, a timeout means
        # the client stalled and is reported as a request timeout.
        try:
            request_line = self._read_request_line(reader)
        except socket.timeout as timeout_err:
            if reader.has_buffered_data:
                raise RequestTimeout(self._config.timeout) from timeout_err
            raise
        
        try:
            rtnval = self._parse_started_request(
                reader,
                request_line,
                client_addr,
                server_addr,
                scheme
            )
        except socket.timeout as timeout_err:
            raise RequestTimeout(self._config.timeout) from timeout_err
        
        return rtnval
    
    def _parse_started_request(
        self,
        reader: SocketReader,
        request_line: bytes,
        client_addr: Tuple[str, int],
        server_addr: Tuple[str, int],
        scheme: str
    ) -> Dict[str, Any]:
        """
            Parse the rest of a request whose request line has been read.
            
            :param reader: SocketReader to read from.
            :param request_line: Raw request line.
            :param client_addr: Client address tuple (host, port).
            :param server_addr: Server address tuple (host, port).
            :param scheme: URL scheme (http or https).
            
            :returns: Complete WSGI environ dict.
            
            :raises: RequestParseError if request is malformed.
            :raises: RequestEntityTooLarge if the body exceeds the size limit.
        """
        method, path, http_version = self.parse_request_line(request_line)
        
        # Parse headers
        headers = self.parse_headers_from_socket(reader)
        
        # A deadline placed on the reader bounds the request line and the
        # headers. The body is bounded by its size limit and by the timeout
        # of each read, a large upload is allowed to take longer.
        reader.set_deadline(None)
        
        # Determine body handling
        content_length_str = self._get_header(headers, "Content-Length")
        transfer_encoding = self._get_header(headers, "Transfer-Encoding")
        
        if transfer_encoding is not None:
            # A request that states its length both ways is the classic
            # request smuggling vector, it is refused and not interpreted.
            if content_length_str is not None:
                errmsg = "Both Transfer-Encoding and Content-Length are present"
                raise RequestParseError(errmsg)
            
            if http_version == "HTTP/1.0":
                errmsg = "Transfer-Encoding is not allowed in an HTTP/1.0 request"
                raise RequestParseError(errmsg)
            
            codings: List[str] = []
            for coding in transfer_encoding.split(","):
                codings.append(coding.strip().lower())
            
            final_coding = codings[-1]
            if final_coding != "chunked":
                errmsg = "The final transfer coding of a request must be chunked"
                raise RequestParseError(errmsg)
            
            if len(codings) != 1:
                errmsg = f"Unsupported transfer coding: {transfer_encoding}"
                raise RequestParseError(errmsg, status_code=501)
            
            # Chunked transfer encoding
            body_data = self.parse_chunked_body(reader)
            
            # The body handed to the application is the decoded one, so the
            # headers are made to describe it.
            headers = self._describe_decoded_body(headers, len(body_data))
            
            body_stream = io.BytesIO(body_data)
        elif content_length_str is not None:
            # Fixed-length body
            content_length = self._parse_content_length(content_length_str)
            
            # Check size limit
            if self._max_request_size > 0 and content_length > self._max_request_size:
                raise RequestEntityTooLarge(self._max_request_size, content_length)
            
            body_data = reader.read_exact(content_length)
            if len(body_data) != content_length:
                errmsg = f"Incomplete body: expected {content_length} bytes, got {len(body_data)}"
                raise IncompleteRequest(errmsg)
            
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
    
    def _describe_decoded_body(
        self,
        headers: Dict[str, str],
        body_size: int
    ) -> Dict[str, str]:
        """
            Rewrite the framing headers of a request whose chunked body was decoded.
            
            :param headers: Parsed headers of the request.
            :param body_size: Size in bytes of the decoded body.
            
            :returns: Copy of the headers without Transfer-Encoding and with a
                      Content-Length equal to the size of the decoded body.
        """
        rtnval: Dict[str, str] = {}
        
        for header_name, header_value in headers.items():
            if header_name.lower() != "transfer-encoding":
                rtnval[header_name] = header_value
        
        rtnval["Content-Length"] = str(body_size)
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
        except RequestParseError:
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
