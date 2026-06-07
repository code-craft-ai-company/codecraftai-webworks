"""
    Tests for the StartResponse class.
    
    This module contains unit tests for the WSGI start_response callable
    implementation.
"""

import socket
from typing import List, Tuple

from ccai.webworks.wsgi.startresponse import StartResponse
from ccai.webworks.wsgi.serverconfig import ServerConfig


# =============================================================================
# Test Helpers and Mock Classes
# =============================================================================

class MockSocket:
    """
        Mock socket for testing StartResponse.
        
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
    
    def clear(self) -> None:
        """
            Clear captured data.
        """
        self._data = b""
        return


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
# Unit Tests for StartResponse - Task 21.1
# =============================================================================

def test_init_with_default_config():
    """
        Test that StartResponse initializes with default configuration.
    """
    mock_sock = MockSocket()
    start_response = StartResponse(mock_sock)
    
    if start_response.status is not None:
        errmsg = "Expected status to be None initially"
        raise AssertionError(errmsg)
    
    if len(start_response.headers) != 0:
        errmsg = "Expected headers to be empty initially"
        raise AssertionError(errmsg)
    
    if start_response.headers_sent:
        errmsg = "Expected headers_sent to be False initially"
        raise AssertionError(errmsg)
    
    return


def test_init_with_custom_config():
    """
        Test that StartResponse initializes with custom configuration.
    """
    mock_sock = MockSocket()
    config = ServerConfig(timeout=60)
    start_response = StartResponse(mock_sock, config)
    
    if start_response.status is not None:
        errmsg = "Expected status to be None initially"
        raise AssertionError(errmsg)
    
    return


def test_init_with_keep_alive():
    """
        Test that StartResponse initializes with keep_alive setting.
    """
    mock_sock = MockSocket()
    start_response = StartResponse(mock_sock, keep_alive=True)
    
    if not start_response.keep_alive:
        errmsg = "Expected keep_alive to be True"
        raise AssertionError(errmsg)
    
    return


def test_status_captured():
    """
        Test that status is captured when start_response is called.
    """
    mock_sock = MockSocket()
    start_response = StartResponse(mock_sock)
    
    start_response("200 OK", [])
    
    if start_response.status != "200 OK":
        errmsg = f"Expected status '200 OK', got '{start_response.status}'"
        raise AssertionError(errmsg)
    
    return


def test_headers_captured():
    """
        Test that headers are captured when start_response is called.
    """
    mock_sock = MockSocket()
    start_response = StartResponse(mock_sock)
    
    headers = [
        ("Content-Type", "text/plain"),
        ("Content-Length", "100"),
    ]
    
    start_response("200 OK", headers)
    
    if len(start_response.headers) != 2:
        errmsg = f"Expected 2 headers, got {len(start_response.headers)}"
        raise AssertionError(errmsg)
    
    if start_response.headers[0] != ("Content-Type", "text/plain"):
        errmsg = f"Expected first header ('Content-Type', 'text/plain'), got {start_response.headers[0]}"
        raise AssertionError(errmsg)
    
    return


def test_headers_sent_initially_false():
    """
        Test that headers_sent is False before sending.
    """
    mock_sock = MockSocket()
    start_response = StartResponse(mock_sock)
    
    start_response("200 OK", [])
    
    if start_response.headers_sent:
        errmsg = "Expected headers_sent to be False before send_headers"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for __call__() method - Task 21.2
# =============================================================================

def test_call_returns_write_callable():
    """
        Test that __call__ returns the write callable.
    """
    mock_sock = MockSocket()
    start_response = StartResponse(mock_sock)
    
    write = start_response("200 OK", [])
    
    # The write callable should be callable and should be the write method
    if not callable(write):
        errmsg = "Expected __call__ to return a callable"
        raise AssertionError(errmsg)
    
    # Verify it's the write method by checking it works correctly
    # Call write and verify it sends headers and data
    write(b"test")
    
    if not start_response.headers_sent:
        errmsg = "Expected write callable to send headers"
        raise AssertionError(errmsg)
    
    return


def test_call_with_exc_info_headers_not_sent():
    """
        Test that exc_info replaces headers when headers not sent.
    """
    mock_sock = MockSocket()
    start_response = StartResponse(mock_sock)
    
    # First call
    start_response("200 OK", [("X-First", "value")])
    
    # Second call with exc_info (simulating error recovery)
    try:
        raise ValueError("Test error")
    except ValueError:
        import sys
        exc_info = sys.exc_info()
        
        # This should replace the headers since they haven't been sent
        start_response("500 Internal Server Error", [("X-Error", "true")], exc_info)
    
    if start_response.status != "500 Internal Server Error":
        errmsg = f"Expected status '500 Internal Server Error', got '{start_response.status}'"
        raise AssertionError(errmsg)
    
    if start_response.headers[0] != ("X-Error", "true"):
        errmsg = f"Expected header ('X-Error', 'true'), got {start_response.headers[0]}"
        raise AssertionError(errmsg)
    
    return


def test_call_with_exc_info_headers_sent_raises():
    """
        Test that exc_info re-raises exception when headers already sent.
    """
    mock_sock = MockSocket()
    start_response = StartResponse(mock_sock)
    
    # First call and send headers
    start_response("200 OK", [])
    start_response.send_headers()
    
    # Second call with exc_info should re-raise
    exception_raised = False
    
    try:
        raise ValueError("Test error")
    except ValueError:
        import sys
        exc_info = sys.exc_info()
        
        try:
            start_response("500 Internal Server Error", [], exc_info)
        except ValueError as val_err:
            if str(val_err) == "Test error":
                exception_raised = True
    
    if not exception_raised:
        errmsg = "Expected ValueError to be re-raised when headers already sent"
        raise AssertionError(errmsg)
    
    return


def test_call_twice_without_exc_info_raises():
    """
        Test that calling start_response twice without exc_info raises error.
    """
    mock_sock = MockSocket()
    start_response = StartResponse(mock_sock)
    
    start_response("200 OK", [])
    
    exception_raised = False
    
    try:
        start_response("200 OK", [])
    except RuntimeError as rt_err:
        if "already called" in str(rt_err):
            exception_raised = True
    
    if not exception_raised:
        errmsg = "Expected RuntimeError when calling start_response twice without exc_info"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for write() method - Task 21.3
# =============================================================================

def test_write_sends_headers_first():
    """
        Test that write() sends headers before body data.
    """
    mock_sock = MockSocket()
    start_response = StartResponse(mock_sock)
    
    start_response("200 OK", [("Content-Type", "text/plain")])
    
    if start_response.headers_sent:
        errmsg = "Expected headers_sent to be False before write"
        raise AssertionError(errmsg)
    
    start_response.write(b"Hello")
    
    if not start_response.headers_sent:
        errmsg = "Expected headers_sent to be True after write"
        raise AssertionError(errmsg)
    
    return


def test_write_sends_data_to_socket():
    """
        Test that write() sends data to the socket.
    """
    mock_sock = MockSocket()
    start_response = StartResponse(mock_sock)
    
    start_response("200 OK", [("Content-Type", "text/plain")])
    start_response.write(b"Hello, World!")
    
    data = mock_sock.get_data_as_string()
    
    if "Hello, World!" not in data:
        errmsg = "Expected body data in socket output"
        raise AssertionError(errmsg)
    
    return


def test_write_empty_data():
    """
        Test that write() handles empty data.
    """
    mock_sock = MockSocket()
    start_response = StartResponse(mock_sock)
    
    start_response("200 OK", [])
    start_response.write(b"")
    
    # Headers should still be sent
    if not start_response.headers_sent:
        errmsg = "Expected headers_sent to be True after write with empty data"
        raise AssertionError(errmsg)
    
    return


def test_write_multiple_times():
    """
        Test that write() can be called multiple times.
    """
    mock_sock = MockSocket()
    start_response = StartResponse(mock_sock)
    
    start_response("200 OK", [])
    start_response.write(b"Hello, ")
    start_response.write(b"World!")
    
    data = mock_sock.get_data_as_string()
    
    if "Hello, " not in data:
        errmsg = "Expected first write data in socket output"
        raise AssertionError(errmsg)
    
    if "World!" not in data:
        errmsg = "Expected second write data in socket output"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for send_headers() method - Task 21.4
# =============================================================================

def test_send_headers_writes_status_line():
    """
        Test that send_headers writes the HTTP status line.
    """
    mock_sock = MockSocket()
    start_response = StartResponse(mock_sock)
    
    start_response("200 OK", [])
    start_response.send_headers()
    
    data = mock_sock.get_data_as_string()
    
    if not data.startswith("HTTP/1.1 200 OK\r\n"):
        errmsg = f"Expected status line 'HTTP/1.1 200 OK\\r\\n', got '{data[:30]}'"
        raise AssertionError(errmsg)
    
    return


def test_send_headers_writes_headers():
    """
        Test that send_headers writes all response headers.
    """
    mock_sock = MockSocket()
    start_response = StartResponse(mock_sock)
    
    headers = [
        ("Content-Type", "text/plain"),
        ("X-Custom", "value"),
    ]
    
    start_response("200 OK", headers)
    start_response.send_headers()
    
    data = mock_sock.get_data_as_string()
    
    if "Content-Type: text/plain\r\n" not in data:
        errmsg = "Expected Content-Type header in output"
        raise AssertionError(errmsg)
    
    if "X-Custom: value\r\n" not in data:
        errmsg = "Expected X-Custom header in output"
        raise AssertionError(errmsg)
    
    return


def test_send_headers_adds_connection_close():
    """
        Test that send_headers adds Connection: close when keep_alive is False.
    """
    mock_sock = MockSocket()
    start_response = StartResponse(mock_sock, keep_alive=False)
    
    start_response("200 OK", [])
    start_response.send_headers()
    
    data = mock_sock.get_data_as_string()
    
    if "Connection: close\r\n" not in data:
        errmsg = "Expected Connection: close header in output"
        raise AssertionError(errmsg)
    
    return


def test_send_headers_adds_connection_keep_alive():
    """
        Test that send_headers adds Connection: keep-alive when keep_alive is True.
    """
    mock_sock = MockSocket()
    start_response = StartResponse(mock_sock, keep_alive=True)
    
    start_response("200 OK", [])
    start_response.send_headers()
    
    data = mock_sock.get_data_as_string()
    
    if "Connection: keep-alive\r\n" not in data:
        errmsg = "Expected Connection: keep-alive header in output"
        raise AssertionError(errmsg)
    
    return


def test_send_headers_does_not_override_connection():
    """
        Test that send_headers does not override existing Connection header.
    """
    mock_sock = MockSocket()
    start_response = StartResponse(mock_sock, keep_alive=True)
    
    headers = [("Connection", "close")]
    
    start_response("200 OK", headers)
    start_response.send_headers()
    
    data = mock_sock.get_data_as_string()
    
    # Should have the original Connection: close, not keep-alive
    if "Connection: close\r\n" not in data:
        errmsg = "Expected original Connection: close header to be preserved"
        raise AssertionError(errmsg)
    
    # Count Connection headers - should only be one
    connection_count = data.count("Connection:")
    
    if connection_count != 1:
        errmsg = f"Expected exactly 1 Connection header, found {connection_count}"
        raise AssertionError(errmsg)
    
    return


def test_send_headers_sets_headers_sent():
    """
        Test that send_headers sets headers_sent flag.
    """
    mock_sock = MockSocket()
    start_response = StartResponse(mock_sock)
    
    start_response("200 OK", [])
    
    if start_response.headers_sent:
        errmsg = "Expected headers_sent to be False before send_headers"
        raise AssertionError(errmsg)
    
    start_response.send_headers()
    
    if not start_response.headers_sent:
        errmsg = "Expected headers_sent to be True after send_headers"
        raise AssertionError(errmsg)
    
    return


def test_send_headers_idempotent():
    """
        Test that send_headers is idempotent (can be called multiple times).
    """
    mock_sock = MockSocket()
    start_response = StartResponse(mock_sock)
    
    start_response("200 OK", [("Content-Type", "text/plain")])
    start_response.send_headers()
    
    # Get data after first send
    first_data = mock_sock.data
    
    # Call again - should not write more data
    start_response.send_headers()
    
    second_data = mock_sock.data
    
    if first_data != second_data:
        errmsg = "Expected send_headers to be idempotent"
        raise AssertionError(errmsg)
    
    return


def test_send_headers_without_start_response_raises():
    """
        Test that send_headers raises error if start_response not called.
    """
    mock_sock = MockSocket()
    start_response = StartResponse(mock_sock)
    
    exception_raised = False
    
    try:
        start_response.send_headers()
    except RuntimeError as rt_err:
        if "start_response not called" in str(rt_err):
            exception_raised = True
    
    if not exception_raised:
        errmsg = "Expected RuntimeError when send_headers called before start_response"
        raise AssertionError(errmsg)
    
    return


def test_send_headers_parses_status_code():
    """
        Test that send_headers correctly parses various status codes.
    """
    test_cases = [
        ("200 OK", 200),
        ("404 Not Found", 404),
        ("500 Internal Server Error", 500),
        ("201 Created", 201),
    ]
    
    for status_str, expected_code in test_cases:
        mock_sock = MockSocket()
        start_response = StartResponse(mock_sock)
        
        start_response(status_str, [])
        start_response.send_headers()
        
        data = mock_sock.get_data_as_string()
        expected_prefix = f"HTTP/1.1 {expected_code}"
        
        if not data.startswith(expected_prefix):
            errmsg = f"Expected status line to start with '{expected_prefix}' for '{status_str}'"
            raise AssertionError(errmsg)
    
    return


def test_reset_clears_state():
    """
        Test that reset() clears all state for reuse.
    """
    mock_sock = MockSocket()
    start_response = StartResponse(mock_sock)
    
    start_response("200 OK", [("Content-Type", "text/plain")])
    start_response.send_headers()
    
    # Reset for next request
    start_response.reset()
    
    if start_response.status is not None:
        errmsg = "Expected status to be None after reset"
        raise AssertionError(errmsg)
    
    if len(start_response.headers) != 0:
        errmsg = "Expected headers to be empty after reset"
        raise AssertionError(errmsg)
    
    if start_response.headers_sent:
        errmsg = "Expected headers_sent to be False after reset"
        raise AssertionError(errmsg)
    
    return


def test_complete_response_flow():
    """
        Test a complete response flow using StartResponse.
    """
    mock_sock = MockSocket()
    start_response = StartResponse(mock_sock, keep_alive=False)
    
    # Simulate WSGI application calling start_response
    headers = [
        ("Content-Type", "text/html"),
        ("Content-Length", "13"),
    ]
    
    write = start_response("200 OK", headers)
    
    # Use write callable (legacy style)
    write(b"Hello, World!")
    
    # Verify complete response
    data = mock_sock.get_data_as_string()
    
    # Check status line
    if not data.startswith("HTTP/1.1 200 OK\r\n"):
        errmsg = "Expected correct status line"
        raise AssertionError(errmsg)
    
    # Check headers
    if "Content-Type: text/html\r\n" not in data:
        errmsg = "Expected Content-Type header"
        raise AssertionError(errmsg)
    
    if "Content-Length: 13\r\n" not in data:
        errmsg = "Expected Content-Length header"
        raise AssertionError(errmsg)
    
    if "Connection: close\r\n" not in data:
        errmsg = "Expected Connection: close header"
        raise AssertionError(errmsg)
    
    # Check body
    if "Hello, World!" not in data:
        errmsg = "Expected body content"
        raise AssertionError(errmsg)
    
    return

