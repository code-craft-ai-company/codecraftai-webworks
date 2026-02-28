"""
    Tests for the HTTPWriter class.
    
    This module contains unit tests and property-based tests for the HTTP
    response writer functionality.
    
    **Feature: wsgi-layer, Property 12: HTTP Response Generation Correctness**
    **Validates: Requirements 12.1, 12.2, 12.3, 12.4, 12.5, 12.6**
"""

import random
import socket
import string
from typing import List, Tuple

from automojo.webworks.wsgi.httpwriter import HTTPWriter, SERVER_NAME
from automojo.webworks.wsgi.serverconfig import ServerConfig
from automojo.webworks.wsgi.constants import HTTP_STATUS_PHRASES


# =============================================================================
# Test Helpers and Mock Classes
# =============================================================================

class MockSocket:
    """
        Mock socket for testing HTTP writing.
        
        Captures all data written to the socket for verification.
    """
    
    def __init__(self):
        """
            Construct a mock socket.
        """
        self._data: bytes = b""
        self._closed: bool = False
        return
    
    def send(self, data: bytes) -> int:
        """
            Capture data sent to the socket.
            
            :param data: Data to send.
            
            :returns: Number of bytes sent.
        """
        if self._closed:
            raise socket.error("Socket is closed")
        
        self._data += data
        rtnval = len(data)
        return rtnval
    
    def close(self) -> None:
        """
            Close the mock socket.
        """
        self._closed = True
        return
    
    @property
    def data(self) -> bytes:
        """
            Get all data written to the socket.
            
            :returns: All captured data.
        """
        return self._data
    
    def get_data_as_string(self) -> str:
        """
            Get data as a decoded string.
            
            :returns: Data decoded as latin-1.
        """
        rtnval = self._data.decode("latin-1")
        return rtnval


def generate_random_string(min_length: int = 1, max_length: int = 50) -> str:
    """
        Generate a random alphanumeric string.
    """
    length = random.randint(min_length, max_length)
    chars = string.ascii_letters + string.digits
    rtnval = "".join(random.choice(chars) for _ in range(length))
    return rtnval


def generate_random_status_code() -> int:
    """
        Generate a random HTTP status code.
    """
    common_codes = [200, 201, 204, 301, 302, 400, 401, 403, 404, 500, 502, 503]
    rtnval = random.choice(common_codes)
    return rtnval


def generate_random_headers() -> List[Tuple[str, str]]:
    """
        Generate random HTTP headers with unique names.
    """
    num_headers = random.randint(0, 10)
    headers: List[Tuple[str, str]] = []
    used_names: set = set()
    common_headers = [
        "Content-Type", "Cache-Control", "X-Request-Id", "X-Custom-Header",
        "Accept", "Accept-Language", "Accept-Encoding",
    ]
    available_common = list(common_headers)
    
    for _ in range(num_headers):
        if random.random() < 0.7 and len(available_common) > 0:
            header_name = random.choice(available_common)
            available_common.remove(header_name)
        else:
            # Generate unique custom header name
            header_name = "X-" + generate_random_string(3, 15).title()
            while header_name.lower() in used_names:
                header_name = "X-" + generate_random_string(3, 15).title()
        
        if header_name.lower() not in used_names:
            header_value = generate_random_string(1, 100)
            headers.append((header_name, header_value))
            used_names.add(header_name.lower())
    
    return headers


def generate_random_body() -> bytes:
    """
        Generate a random response body.
    """
    if random.random() < 0.2:
        rtnval = b""
    else:
        length = random.randint(1, 500)
        rtnval = bytes(random.randint(32, 126) for _ in range(length))
    return rtnval


def parse_http_response(data: bytes) -> Tuple[str, List[Tuple[str, str]], bytes]:
    """
        Parse an HTTP response into components.
        
        :param data: Raw HTTP response bytes.
        
        :returns: Tuple of (status_line, headers, body).
    """
    # Split headers and body
    if b"\r\n\r\n" in data:
        header_section, body = data.split(b"\r\n\r\n", 1)
    else:
        header_section = data
        body = b""
    
    # Parse header lines
    lines = header_section.split(b"\r\n")
    status_line = lines[0].decode("ascii")
    
    headers: List[Tuple[str, str]] = []
    for line in lines[1:]:
        if len(line) == 0:
            continue
        line_str = line.decode("latin-1")
        if ":" in line_str:
            name, value = line_str.split(":", 1)
            headers.append((name.strip(), value.strip()))
    
    rtnval = (status_line, headers, body)
    return rtnval


# =============================================================================
# Unit Tests for HTTPWriter
# =============================================================================

def test_init_with_default_config():
    """
        Test that HTTPWriter initializes with default configuration.
    """
    mock_sock = MockSocket()
    writer = HTTPWriter(mock_sock)
    
    if writer.socket is not mock_sock:
        errmsg = "Expected socket to be the mock socket"
        raise AssertionError(errmsg)
    
    if writer.headers_sent:
        errmsg = "Expected headers_sent to be False initially"
        raise AssertionError(errmsg)
    
    return


def test_init_with_custom_config():
    """
        Test that HTTPWriter initializes with custom configuration.
    """
    mock_sock = MockSocket()
    config = ServerConfig(timeout=60)
    writer = HTTPWriter(mock_sock, config)
    
    if writer.socket is not mock_sock:
        errmsg = "Expected socket to be the mock socket"
        raise AssertionError(errmsg)
    
    return


def test_write_status_line_200_ok():
    """
        Test writing a 200 OK status line.
    """
    mock_sock = MockSocket()
    writer = HTTPWriter(mock_sock)
    
    writer.write_status_line(200)
    writer.flush()
    
    data = mock_sock.get_data_as_string()
    
    if not data.startswith("HTTP/1.1 200 OK\r\n"):
        errmsg = f"Expected status line 'HTTP/1.1 200 OK\\r\\n', got '{data[:30]}'"
        raise AssertionError(errmsg)
    
    return


def test_write_status_line_404_not_found():
    """
        Test writing a 404 Not Found status line.
    """
    mock_sock = MockSocket()
    writer = HTTPWriter(mock_sock)
    
    writer.write_status_line(404)
    writer.flush()
    
    data = mock_sock.get_data_as_string()
    
    if not data.startswith("HTTP/1.1 404 Not Found\r\n"):
        errmsg = f"Expected status line 'HTTP/1.1 404 Not Found\\r\\n', got '{data[:35]}'"
        raise AssertionError(errmsg)
    
    return


def test_write_status_line_with_custom_reason():
    """
        Test writing a status line with custom reason phrase.
    """
    mock_sock = MockSocket()
    writer = HTTPWriter(mock_sock)
    
    writer.write_status_line(200, "All Good")
    writer.flush()
    
    data = mock_sock.get_data_as_string()
    
    if not data.startswith("HTTP/1.1 200 All Good\r\n"):
        errmsg = f"Expected status line 'HTTP/1.1 200 All Good\\r\\n', got '{data[:30]}'"
        raise AssertionError(errmsg)
    
    return


def test_write_status_line_unknown_code():
    """
        Test writing a status line with unknown status code.
    """
    mock_sock = MockSocket()
    writer = HTTPWriter(mock_sock)
    
    writer.write_status_line(599)
    writer.flush()
    
    data = mock_sock.get_data_as_string()
    
    if not data.startswith("HTTP/1.1 599 Unknown\r\n"):
        errmsg = f"Expected status line 'HTTP/1.1 599 Unknown\\r\\n', got '{data[:30]}'"
        raise AssertionError(errmsg)
    
    return


def test_write_headers_basic():
    """
        Test writing basic headers.
    """
    mock_sock = MockSocket()
    writer = HTTPWriter(mock_sock)
    
    headers = [
        ("Content-Type", "text/plain"),
        ("Content-Length", "100"),
    ]
    
    writer.write_headers(headers)
    writer.flush()
    
    data = mock_sock.get_data_as_string()
    
    if "Content-Type: text/plain\r\n" not in data:
        errmsg = "Expected Content-Type header in output"
        raise AssertionError(errmsg)
    
    if "Content-Length: 100\r\n" not in data:
        errmsg = "Expected Content-Length header in output"
        raise AssertionError(errmsg)
    
    return


def test_write_headers_adds_date():
    """
        Test that write_headers adds Date header if not present.
    """
    mock_sock = MockSocket()
    writer = HTTPWriter(mock_sock)
    
    headers = [("Content-Type", "text/plain")]
    
    writer.write_headers(headers, include_date=True)
    writer.flush()
    
    data = mock_sock.get_data_as_string()
    
    if "Date:" not in data:
        errmsg = "Expected Date header in output"
        raise AssertionError(errmsg)
    
    return


def test_write_headers_adds_server():
    """
        Test that write_headers adds Server header if not present.
    """
    mock_sock = MockSocket()
    writer = HTTPWriter(mock_sock)
    
    headers = [("Content-Type", "text/plain")]
    
    writer.write_headers(headers, include_server=True)
    writer.flush()
    
    data = mock_sock.get_data_as_string()
    
    if f"Server: {SERVER_NAME}\r\n" not in data:
        errmsg = f"Expected Server header '{SERVER_NAME}' in output"
        raise AssertionError(errmsg)
    
    return


def test_write_headers_does_not_duplicate_date():
    """
        Test that write_headers does not duplicate Date header.
    """
    mock_sock = MockSocket()
    writer = HTTPWriter(mock_sock)
    
    headers = [
        ("Content-Type", "text/plain"),
        ("Date", "Mon, 01 Jan 2024 00:00:00 GMT"),
    ]
    
    writer.write_headers(headers, include_date=True)
    writer.flush()
    
    data = mock_sock.get_data_as_string()
    
    # Count occurrences of Date:
    date_count = data.count("Date:")
    
    if date_count != 1:
        errmsg = f"Expected exactly 1 Date header, found {date_count}"
        raise AssertionError(errmsg)
    
    return


def test_write_headers_does_not_duplicate_server():
    """
        Test that write_headers does not duplicate Server header.
    """
    mock_sock = MockSocket()
    writer = HTTPWriter(mock_sock)
    
    headers = [
        ("Content-Type", "text/plain"),
        ("Server", "CustomServer/1.0"),
    ]
    
    writer.write_headers(headers, include_server=True)
    writer.flush()
    
    data = mock_sock.get_data_as_string()
    
    # Count occurrences of Server:
    server_count = data.count("Server:")
    
    if server_count != 1:
        errmsg = f"Expected exactly 1 Server header, found {server_count}"
        raise AssertionError(errmsg)
    
    return


def test_write_headers_ends_with_empty_line():
    """
        Test that write_headers ends with empty line (CRLF CRLF).
    """
    mock_sock = MockSocket()
    writer = HTTPWriter(mock_sock)
    
    headers = [("Content-Type", "text/plain")]
    
    writer.write_headers(headers, include_date=False, include_server=False)
    writer.flush()
    
    data = mock_sock.data
    
    if not data.endswith(b"\r\n\r\n"):
        errmsg = "Expected headers to end with CRLF CRLF"
        raise AssertionError(errmsg)
    
    return


def test_write_headers_sets_headers_sent():
    """
        Test that write_headers sets headers_sent flag.
    """
    mock_sock = MockSocket()
    writer = HTTPWriter(mock_sock)
    
    if writer.headers_sent:
        errmsg = "Expected headers_sent to be False before write_headers"
        raise AssertionError(errmsg)
    
    writer.write_headers([])
    
    if not writer.headers_sent:
        errmsg = "Expected headers_sent to be True after write_headers"
        raise AssertionError(errmsg)
    
    return


def test_write_body_basic():
    """
        Test writing a basic body.
    """
    mock_sock = MockSocket()
    writer = HTTPWriter(mock_sock)
    
    body = b"Hello, World!"
    writer.write_body(body)
    writer.flush()
    
    if mock_sock.data != body:
        errmsg = f"Expected body '{body}', got '{mock_sock.data}'"
        raise AssertionError(errmsg)
    
    return


def test_write_body_empty():
    """
        Test writing an empty body.
    """
    mock_sock = MockSocket()
    writer = HTTPWriter(mock_sock)
    
    writer.write_body(b"")
    writer.flush()
    
    if len(mock_sock.data) != 0:
        errmsg = f"Expected empty body, got {len(mock_sock.data)} bytes"
        raise AssertionError(errmsg)
    
    return


def test_write_body_iterator():
    """
        Test writing body from an iterator.
    """
    mock_sock = MockSocket()
    writer = HTTPWriter(mock_sock)
    
    chunks = [b"Hello, ", b"World", b"!"]
    writer.write_body_iterator(chunks)
    writer.flush()
    
    expected = b"Hello, World!"
    if mock_sock.data != expected:
        errmsg = f"Expected body '{expected}', got '{mock_sock.data}'"
        raise AssertionError(errmsg)
    
    return


def test_write_chunked_basic():
    """
        Test writing chunked transfer encoding.
    """
    mock_sock = MockSocket()
    writer = HTTPWriter(mock_sock)
    
    chunks = [b"Hello", b"World"]
    writer.write_chunked(chunks)
    writer.flush()
    
    data = mock_sock.data
    
    # Verify chunked format
    # First chunk: 5\r\nHello\r\n
    if b"5\r\nHello\r\n" not in data:
        errmsg = "Expected first chunk '5\\r\\nHello\\r\\n' in output"
        raise AssertionError(errmsg)
    
    # Second chunk: 5\r\nWorld\r\n
    if b"5\r\nWorld\r\n" not in data:
        errmsg = "Expected second chunk '5\\r\\nWorld\\r\\n' in output"
        raise AssertionError(errmsg)
    
    # Terminating chunk: 0\r\n\r\n
    if not data.endswith(b"0\r\n\r\n"):
        errmsg = "Expected terminating chunk '0\\r\\n\\r\\n' at end"
        raise AssertionError(errmsg)
    
    return


def test_write_chunked_empty_chunks_skipped():
    """
        Test that empty chunks are skipped in chunked encoding.
    """
    mock_sock = MockSocket()
    writer = HTTPWriter(mock_sock)
    
    chunks = [b"Hello", b"", b"World"]
    writer.write_chunked(chunks)
    writer.flush()
    
    data = mock_sock.data
    
    # Should not have 0\r\n in the middle (only at end)
    # Count occurrences of "0\r\n"
    zero_chunks = data.count(b"0\r\n")
    
    # Should only have one zero chunk at the end
    if zero_chunks != 1:
        errmsg = f"Expected exactly 1 zero chunk, found {zero_chunks}"
        raise AssertionError(errmsg)
    
    return


def test_write_chunked_empty_iterator():
    """
        Test writing chunked encoding with empty iterator.
    """
    mock_sock = MockSocket()
    writer = HTTPWriter(mock_sock)
    
    writer.write_chunked([])
    writer.flush()
    
    # Should only have terminating chunk
    if mock_sock.data != b"0\r\n\r\n":
        errmsg = f"Expected only terminating chunk, got '{mock_sock.data}'"
        raise AssertionError(errmsg)
    
    return


def test_flush_sends_buffered_data():
    """
        Test that flush sends buffered data.
    """
    mock_sock = MockSocket()
    writer = HTTPWriter(mock_sock)
    
    # Write small amount (won't auto-flush)
    writer._write_raw(b"test")
    
    # Data should be in buffer, not socket yet
    if len(mock_sock.data) > 0:
        # Small data might be buffered
        pass
    
    # Flush should send it
    writer.flush()
    
    if b"test" not in mock_sock.data:
        errmsg = "Expected 'test' in socket data after flush"
        raise AssertionError(errmsg)
    
    return


def test_write_response_complete():
    """
        Test writing a complete response.
    """
    mock_sock = MockSocket()
    writer = HTTPWriter(mock_sock)
    
    headers = [
        ("Content-Type", "text/plain"),
        ("Content-Length", "13"),
    ]
    body = b"Hello, World!"
    
    writer.write_response(200, headers, body)
    
    data = mock_sock.get_data_as_string()
    
    if not data.startswith("HTTP/1.1 200 OK\r\n"):
        errmsg = "Expected response to start with status line"
        raise AssertionError(errmsg)
    
    if "Content-Type: text/plain\r\n" not in data:
        errmsg = "Expected Content-Type header in response"
        raise AssertionError(errmsg)
    
    if "Hello, World!" not in data:
        errmsg = "Expected body in response"
        raise AssertionError(errmsg)
    
    return


def test_write_error_response():
    """
        Test writing an error response.
    """
    mock_sock = MockSocket()
    writer = HTTPWriter(mock_sock)
    
    writer.write_error_response(404, "Resource not found")
    
    data = mock_sock.get_data_as_string()
    
    if not data.startswith("HTTP/1.1 404 Not Found\r\n"):
        errmsg = "Expected 404 status line"
        raise AssertionError(errmsg)
    
    if "Content-Type: text/plain" not in data:
        errmsg = "Expected Content-Type header"
        raise AssertionError(errmsg)
    
    if "Connection: close" not in data:
        errmsg = "Expected Connection: close header"
        raise AssertionError(errmsg)
    
    if "Resource not found" not in data:
        errmsg = "Expected error message in body"
        raise AssertionError(errmsg)
    
    return


def test_close_flushes_buffer():
    """
        Test that close flushes the buffer.
    """
    mock_sock = MockSocket()
    writer = HTTPWriter(mock_sock)
    
    writer._write_raw(b"test data")
    writer.close()
    
    if b"test data" not in mock_sock.data:
        errmsg = "Expected data to be flushed on close"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Property-Based Tests for HTTPWriter
# =============================================================================

def test_property_http_response_generation_correctness():
    """
        Property test: HTTP Response Generation Correctness
        
        For any WSGI response (status, headers, body iterator), the HTTPWriter
        SHALL produce a valid HTTP/1.1 response with correct status line,
        properly formatted headers, and complete body content.
        
        **Feature: wsgi-layer, Property 12: HTTP Response Generation Correctness**
        **Validates: Requirements 12.1, 12.2, 12.3, 12.4, 12.5, 12.6**
    """
    # Run 100 iterations with random HTTP responses
    num_iterations = 100
    
    for iteration in range(num_iterations):
        # Generate random response components
        status_code = generate_random_status_code()
        headers = generate_random_headers()
        body = generate_random_body()
        
        # Add Content-Length header for body
        if len(body) > 0:
            headers.append(("Content-Length", str(len(body))))
        
        # Create mock socket and writer
        mock_sock = MockSocket()
        writer = HTTPWriter(mock_sock)
        
        # Write the response
        writer.write_response(status_code, headers, body)
        
        # Parse the generated response
        response_data = mock_sock.data
        parsed_status, parsed_headers, parsed_body = parse_http_response(response_data)
        
        # Verify status line format (Requirement 12.1)
        expected_reason = HTTP_STATUS_PHRASES.get(status_code, "Unknown")
        expected_status = f"HTTP/1.1 {status_code} {expected_reason}"
        
        if parsed_status != expected_status:
            errmsg = f"Iteration {iteration}: Status line mismatch. Expected '{expected_status}', got '{parsed_status}'"
            raise AssertionError(errmsg)
        
        # Verify headers are properly formatted (Requirement 12.2)
        header_dict = {name.lower(): value for name, value in parsed_headers}
        
        for name, value in headers:
            name_lower = name.lower()
            if name_lower not in header_dict:
                errmsg = f"Iteration {iteration}: Missing header '{name}'"
                raise AssertionError(errmsg)
            
            if header_dict[name_lower] != value:
                errmsg = f"Iteration {iteration}: Header '{name}' value mismatch. Expected '{value}', got '{header_dict[name_lower]}'"
                raise AssertionError(errmsg)
        
        # Verify Date header is present (Requirement 12.5)
        if "date" not in header_dict:
            errmsg = f"Iteration {iteration}: Missing Date header"
            raise AssertionError(errmsg)
        
        # Verify Server header is present (Requirement 12.6)
        if "server" not in header_dict:
            errmsg = f"Iteration {iteration}: Missing Server header"
            raise AssertionError(errmsg)
        
        # Verify body content (Requirement 12.3)
        if parsed_body != body:
            errmsg = f"Iteration {iteration}: Body mismatch. Expected {len(body)} bytes, got {len(parsed_body)} bytes"
            raise AssertionError(errmsg)
    
    return


def test_property_chunked_transfer_encoding():
    """
        Property test: Chunked Transfer Encoding Correctness
        
        For any response body written with chunked transfer encoding, the
        HTTPWriter SHALL produce valid chunked encoding with correct chunk
        sizes and proper termination.
        
        **Feature: wsgi-layer, Property 12: HTTP Response Generation Correctness**
        **Validates: Requirements 12.4**
    """
    # Run 100 iterations with random chunked responses
    num_iterations = 100
    
    for iteration in range(num_iterations):
        # Generate random chunks
        num_chunks = random.randint(0, 10)
        chunks = []
        for _ in range(num_chunks):
            chunk_size = random.randint(1, 100)
            chunk = bytes(random.randint(32, 126) for _ in range(chunk_size))
            chunks.append(chunk)
        
        # Create mock socket and writer
        mock_sock = MockSocket()
        writer = HTTPWriter(mock_sock)
        
        # Write chunked response
        writer.write_chunked(chunks)
        writer.flush()
        
        # Parse and verify chunked encoding
        data = mock_sock.data
        
        # Verify terminating chunk
        if not data.endswith(b"0\r\n\r\n"):
            errmsg = f"Iteration {iteration}: Missing terminating chunk"
            raise AssertionError(errmsg)
        
        # Parse chunks and verify content
        reconstructed_body = b""
        remaining = data
        
        while len(remaining) > 0:
            # Find chunk size line
            crlf_pos = remaining.find(b"\r\n")
            if crlf_pos == -1:
                errmsg = f"Iteration {iteration}: Invalid chunked encoding - missing CRLF"
                raise AssertionError(errmsg)
            
            size_line = remaining[:crlf_pos]
            
            try:
                chunk_size = int(size_line.decode("ascii"), 16)
            except ValueError as val_err:
                errmsg = f"Iteration {iteration}: Invalid chunk size '{size_line}'"
                raise AssertionError(errmsg) from val_err
            
            # Zero chunk means end
            if chunk_size == 0:
                break
            
            # Extract chunk data
            chunk_start = crlf_pos + 2
            chunk_end = chunk_start + chunk_size
            chunk_data = remaining[chunk_start:chunk_end]
            
            if len(chunk_data) != chunk_size:
                errmsg = f"Iteration {iteration}: Chunk size mismatch. Expected {chunk_size}, got {len(chunk_data)}"
                raise AssertionError(errmsg)
            
            reconstructed_body += chunk_data
            
            # Move past chunk data and trailing CRLF
            remaining = remaining[chunk_end + 2:]
        
        # Verify reconstructed body matches original
        expected_body = b"".join(chunks)
        
        if reconstructed_body != expected_body:
            errmsg = f"Iteration {iteration}: Reconstructed body mismatch. Expected {len(expected_body)} bytes, got {len(reconstructed_body)} bytes"
            raise AssertionError(errmsg)
    
    return


def test_property_status_line_format():
    """
        Property test: Status Line Format Correctness
        
        For any valid HTTP status code, the HTTPWriter SHALL produce a
        status line in the format "HTTP/1.1 <code> <reason>".
        
        **Feature: wsgi-layer, Property 12: HTTP Response Generation Correctness**
        **Validates: Requirements 12.1**
    """
    # Test all known status codes
    for status_code, expected_reason in HTTP_STATUS_PHRASES.items():
        mock_sock = MockSocket()
        writer = HTTPWriter(mock_sock)
        
        writer.write_status_line(status_code)
        writer.flush()
        
        data = mock_sock.get_data_as_string()
        expected_line = f"HTTP/1.1 {status_code} {expected_reason}\r\n"
        
        if data != expected_line:
            errmsg = f"Status code {status_code}: Expected '{expected_line}', got '{data}'"
            raise AssertionError(errmsg)
    
    # Test random unknown status codes
    num_iterations = 50
    
    for _ in range(num_iterations):
        # Generate a status code not in the standard list
        status_code = random.randint(100, 599)
        while status_code in HTTP_STATUS_PHRASES:
            status_code = random.randint(100, 599)
        
        mock_sock = MockSocket()
        writer = HTTPWriter(mock_sock)
        
        writer.write_status_line(status_code)
        writer.flush()
        
        data = mock_sock.get_data_as_string()
        expected_line = f"HTTP/1.1 {status_code} Unknown\r\n"
        
        if data != expected_line:
            errmsg = f"Unknown status code {status_code}: Expected '{expected_line}', got '{data}'"
            raise AssertionError(errmsg)
    
    return
