"""
    Tests for the HTTPParser class.
    
    This module contains unit tests and property-based tests for the HTTP
    request parser functionality.
    
    **Feature: wsgi-layer, Property 11: HTTP Request Parsing Correctness**
    **Validates: Requirements 11.1, 11.2, 11.3, 11.8, 11.9, 11.10**
    
    **Feature: wsgi-layer, Property 13: Server Environ Construction**
    **Validates: Requirements 5.3, 5.4**
"""

import io
import socket
import random
import string
from typing import Any, Dict, List

from ccai.webworks.wsgi.httpparser import (
    HTTPParser,
    SUPPORTED_METHODS,
    SUPPORTED_VERSIONS,
)
from ccai.webworks.wsgi.serverconfig import ServerConfig
from ccai.webworks.wsgi.exceptions import (
    ConnectionClosed,
    IncompleteRequest,
    RequestEntityTooLarge,
    RequestLineTooLong,
    RequestParseError,
    RequestTimeout,
    HeaderTooLarge,
    TooManyHeaders,
)
from ccai.webworks.wsgi.socketreader import SocketReader


# =============================================================================
# Test Helpers and Generators
# =============================================================================

def generate_random_string(min_length: int = 1, max_length: int = 50) -> str:
    """
        Generate a random alphanumeric string.
    """
    length = random.randint(min_length, max_length)
    chars = string.ascii_letters + string.digits
    rtnval = "".join(random.choice(chars) for _ in range(length))
    return rtnval


def generate_random_path() -> str:
    """
        Generate a random URL path.
    """
    num_segments = random.randint(0, 5)
    if num_segments == 0:
        rtnval = "/"
    else:
        segments = [generate_random_string(1, 20) for _ in range(num_segments)]
        rtnval = "/" + "/".join(segments)
    return rtnval


def generate_random_query_string() -> str:
    """
        Generate a random query string.
    """
    num_params = random.randint(0, 5)
    if num_params == 0:
        rtnval = ""
    else:
        params = []
        for _ in range(num_params):
            key = generate_random_string(1, 15)
            value = generate_random_string(0, 30)
            params.append(f"{key}={value}")
        rtnval = "&".join(params)
    return rtnval


def generate_random_method() -> str:
    """
        Generate a random HTTP method.
    """
    methods = ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"]
    rtnval = random.choice(methods)
    return rtnval


def generate_random_http_version() -> str:
    """
        Generate a random HTTP version.
    """
    rtnval = random.choice(["HTTP/1.0", "HTTP/1.1"])
    return rtnval


def generate_random_headers() -> Dict[str, str]:
    """
        Generate random HTTP headers.
    """
    num_headers = random.randint(0, 10)
    headers: Dict[str, str] = {}
    common_headers = [
        "Accept", "Accept-Language", "Accept-Encoding", "User-Agent",
        "Authorization", "Cache-Control", "X-Request-Id", "X-Forwarded-For",
    ]
    for _ in range(num_headers):
        if random.random() < 0.7 and len(common_headers) > 0:
            header_name = random.choice(common_headers)
        else:
            header_name = "X-" + generate_random_string(3, 15).title()
        header_value = generate_random_string(1, 100)
        headers[header_name] = header_value
    return headers


def generate_random_body() -> bytes:
    """
        Generate a random request body.
    """
    if random.random() < 0.3:
        rtnval = b""
    else:
        length = random.randint(1, 500)
        rtnval = bytes(random.randint(32, 126) for _ in range(length))
    return rtnval


def build_http_request(
    method: str,
    path: str,
    http_version: str,
    headers: Dict[str, str],
    body: bytes
) -> bytes:
    """
        Build a raw HTTP request from components.
    """
    lines: List[bytes] = []
    
    # Request line
    request_line = f"{method} {path} {http_version}"
    lines.append(request_line.encode("ascii"))
    
    # Headers
    for name, value in headers.items():
        header_line = f"{name}: {value}"
        lines.append(header_line.encode("latin-1"))
    
    # Add Content-Length if body present
    if len(body) > 0:
        lines.append(f"Content-Length: {len(body)}".encode("ascii"))
    
    # Empty line to end headers
    lines.append(b"")
    
    # Join with CRLF
    request = b"\r\n".join(lines)
    
    # Add body
    if len(body) > 0:
        request = request + b"\r\n" + body
    
    rtnval = request
    return rtnval


class MockSocket:
    """
        Mock socket for testing HTTP parsing.
    """
    
    def __init__(self, data: bytes):
        """
            Construct a mock socket with data to read.
        """
        self._data = data
        self._position = 0
        return
    
    def recv(self, size: int) -> bytes:
        """
            Read data from the mock socket.
        """
        if self._position >= len(self._data):
            rtnval = b""
        else:
            end = min(self._position + size, len(self._data))
            rtnval = self._data[self._position:end]
            self._position = end
        return rtnval


# =============================================================================
# Unit Tests for HTTPParser
# =============================================================================

def test_init_with_default_config():
    """
        Test that HTTPParser initializes with default configuration.
    """
    parser = HTTPParser()
    
    if parser.max_header_size != 8192:
        errmsg = f"Expected max_header_size 8192, got {parser.max_header_size}"
        raise AssertionError(errmsg)
    
    if parser.max_headers != 100:
        errmsg = f"Expected max_headers 100, got {parser.max_headers}"
        raise AssertionError(errmsg)
    
    return


def test_init_with_custom_config():
    """
        Test that HTTPParser initializes with custom configuration.
    """
    config = ServerConfig(max_header_size=4096, max_headers=50)
    parser = HTTPParser(config)
    
    if parser.max_header_size != 4096:
        errmsg = f"Expected max_header_size 4096, got {parser.max_header_size}"
        raise AssertionError(errmsg)
    
    if parser.max_headers != 50:
        errmsg = f"Expected max_headers 50, got {parser.max_headers}"
        raise AssertionError(errmsg)
    
    return


def test_parse_request_line_valid_get():
    """
        Test parsing a valid GET request line.
    """
    parser = HTTPParser()
    line = b"GET /api/users HTTP/1.1"
    
    method, path, version = parser.parse_request_line(line)
    
    if method != "GET":
        errmsg = f"Expected method 'GET', got '{method}'"
        raise AssertionError(errmsg)
    
    if path != "/api/users":
        errmsg = f"Expected path '/api/users', got '{path}'"
        raise AssertionError(errmsg)
    
    if version != "HTTP/1.1":
        errmsg = f"Expected version 'HTTP/1.1', got '{version}'"
        raise AssertionError(errmsg)
    
    return


def test_parse_request_line_valid_post():
    """
        Test parsing a valid POST request line.
    """
    parser = HTTPParser()
    line = b"POST /api/users HTTP/1.0"
    
    method, path, version = parser.parse_request_line(line)
    
    if method != "POST":
        errmsg = f"Expected method 'POST', got '{method}'"
        raise AssertionError(errmsg)
    
    if path != "/api/users":
        errmsg = f"Expected path '/api/users', got '{path}'"
        raise AssertionError(errmsg)
    
    if version != "HTTP/1.0":
        errmsg = f"Expected version 'HTTP/1.0', got '{version}'"
        raise AssertionError(errmsg)
    
    return


def test_parse_request_line_with_query_string():
    """
        Test parsing a request line with query string.
    """
    parser = HTTPParser()
    line = b"GET /api/users?id=1&name=test HTTP/1.1"
    
    method, path, version = parser.parse_request_line(line)
    
    if method != "GET":
        errmsg = f"Expected method 'GET', got '{method}'"
        raise AssertionError(errmsg)
    
    if path != "/api/users?id=1&name=test":
        errmsg = f"Expected path '/api/users?id=1&name=test', got '{path}'"
        raise AssertionError(errmsg)
    
    return


def test_parse_request_line_empty_raises_error():
    """
        Test that parsing an empty request line raises RequestParseError.
    """
    parser = HTTPParser()
    line = b""
    
    exception_raised = False
    try:
        parser.parse_request_line(line)
    except RequestParseError:
        exception_raised = True
    
    if not exception_raised:
        errmsg = "Expected RequestParseError for empty request line"
        raise AssertionError(errmsg)
    
    return


def test_parse_request_line_malformed_raises_error():
    """
        Test that parsing a malformed request line raises RequestParseError.
    """
    parser = HTTPParser()
    line = b"GET /api/users"  # Missing HTTP version
    
    exception_raised = False
    try:
        parser.parse_request_line(line)
    except RequestParseError:
        exception_raised = True
    
    if not exception_raised:
        errmsg = "Expected RequestParseError for malformed request line"
        raise AssertionError(errmsg)
    
    return


def test_parse_request_line_unsupported_method_raises_error():
    """
        Test that parsing an unsupported method raises RequestParseError.
    """
    parser = HTTPParser()
    line = b"INVALID /api/users HTTP/1.1"
    
    exception_raised = False
    try:
        parser.parse_request_line(line)
    except RequestParseError:
        exception_raised = True
    
    if not exception_raised:
        errmsg = "Expected RequestParseError for unsupported method"
        raise AssertionError(errmsg)
    
    return


def test_parse_request_line_unsupported_version_raises_error():
    """
        Test that parsing an unsupported HTTP version raises RequestParseError.
    """
    parser = HTTPParser()
    line = b"GET /api/users HTTP/2.0"
    
    exception_raised = False
    try:
        parser.parse_request_line(line)
    except RequestParseError:
        exception_raised = True
    
    if not exception_raised:
        errmsg = "Expected RequestParseError for unsupported HTTP version"
        raise AssertionError(errmsg)
    
    return


def test_parse_headers_valid():
    """
        Test parsing valid HTTP headers.
    """
    parser = HTTPParser()
    header_lines = [
        b"Content-Type: application/json",
        b"Accept: text/html",
        b"X-Custom-Header: custom-value",
    ]
    
    headers = parser.parse_headers(header_lines)
    
    if "Content-Type" not in headers:
        errmsg = "Expected 'Content-Type' header in result"
        raise AssertionError(errmsg)
    
    if headers["Content-Type"] != "application/json":
        errmsg = f"Expected Content-Type='application/json', got '{headers['Content-Type']}'"
        raise AssertionError(errmsg)
    
    if "Accept" not in headers:
        errmsg = "Expected 'Accept' header in result"
        raise AssertionError(errmsg)
    
    if "X-Custom-Header" not in headers:
        errmsg = "Expected 'X-Custom-Header' header in result"
        raise AssertionError(errmsg)
    
    return


def test_parse_headers_with_continuation():
    """
        Test parsing headers with continuation lines (folded headers).
    """
    parser = HTTPParser()
    header_lines = [
        b"X-Long-Header: value part one",
        b" value part two",
        b"\tvalue part three",
    ]
    
    headers = parser.parse_headers(header_lines)
    
    if "X-Long-Header" not in headers:
        errmsg = "Expected 'X-Long-Header' header in result"
        raise AssertionError(errmsg)
    
    expected_value = "value part one value part two value part three"
    if headers["X-Long-Header"] != expected_value:
        errmsg = f"Expected '{expected_value}', got '{headers['X-Long-Header']}'"
        raise AssertionError(errmsg)
    
    return


def test_parse_headers_exceeds_size_limit():
    """
        Test that parsing headers exceeding size limit raises HeaderTooLarge.
    """
    config = ServerConfig(max_header_size=100)
    parser = HTTPParser(config)
    
    # Create headers that exceed the limit
    header_lines = [
        b"X-Large-Header: " + b"x" * 200,
    ]
    
    exception_raised = False
    try:
        parser.parse_headers(header_lines)
    except HeaderTooLarge:
        exception_raised = True
    
    if not exception_raised:
        errmsg = "Expected HeaderTooLarge exception"
        raise AssertionError(errmsg)
    
    return


def test_parse_headers_exceeds_count_limit():
    """
        Test that parsing too many headers raises TooManyHeaders.
    """
    config = ServerConfig(max_headers=3)
    parser = HTTPParser(config)
    
    # Create more headers than allowed
    header_lines = [
        b"Header-1: value1",
        b"Header-2: value2",
        b"Header-3: value3",
        b"Header-4: value4",
    ]
    
    exception_raised = False
    try:
        parser.parse_headers(header_lines)
    except TooManyHeaders:
        exception_raised = True
    
    if not exception_raised:
        errmsg = "Expected TooManyHeaders exception"
        raise AssertionError(errmsg)
    
    return


def test_parse_headers_malformed_raises_error():
    """
        Test that parsing malformed headers raises RequestParseError.
    """
    parser = HTTPParser()
    header_lines = [
        b"Invalid header without colon",
    ]
    
    exception_raised = False
    try:
        parser.parse_headers(header_lines)
    except RequestParseError:
        exception_raised = True
    
    if not exception_raised:
        errmsg = "Expected RequestParseError for malformed header"
        raise AssertionError(errmsg)
    
    return


def test_build_environ_basic():
    """
        Test building a basic WSGI environ dictionary.
    """
    parser = HTTPParser()
    body_stream = io.BytesIO(b"")
    
    environ = parser.build_environ(
        method="GET",
        path="/api/users",
        http_version="HTTP/1.1",
        headers={"Accept": "application/json"},
        body_stream=body_stream,
        client_addr=("127.0.0.1", 12345),
        server_addr=("0.0.0.0", 8000),
        scheme="http"
    )
    
    if environ["REQUEST_METHOD"] != "GET":
        errmsg = f"Expected REQUEST_METHOD='GET', got '{environ['REQUEST_METHOD']}'"
        raise AssertionError(errmsg)
    
    if environ["PATH_INFO"] != "/api/users":
        errmsg = f"Expected PATH_INFO='/api/users', got '{environ['PATH_INFO']}'"
        raise AssertionError(errmsg)
    
    if environ["SERVER_NAME"] != "0.0.0.0":
        errmsg = f"Expected SERVER_NAME='0.0.0.0', got '{environ['SERVER_NAME']}'"
        raise AssertionError(errmsg)
    
    if environ["SERVER_PORT"] != "8000":
        errmsg = f"Expected SERVER_PORT='8000', got '{environ['SERVER_PORT']}'"
        raise AssertionError(errmsg)
    
    if environ["wsgi.url_scheme"] != "http":
        errmsg = f"Expected wsgi.url_scheme='http', got '{environ['wsgi.url_scheme']}'"
        raise AssertionError(errmsg)
    
    if environ["REMOTE_ADDR"] != "127.0.0.1":
        errmsg = f"Expected REMOTE_ADDR='127.0.0.1', got '{environ['REMOTE_ADDR']}'"
        raise AssertionError(errmsg)
    
    return


def test_build_environ_with_query_string():
    """
        Test building environ with query string in path.
    """
    parser = HTTPParser()
    body_stream = io.BytesIO(b"")
    
    environ = parser.build_environ(
        method="GET",
        path="/api/users?id=1&name=test",
        http_version="HTTP/1.1",
        headers={},
        body_stream=body_stream,
        client_addr=("127.0.0.1", 12345),
        server_addr=("0.0.0.0", 8000),
        scheme="http"
    )
    
    if environ["PATH_INFO"] != "/api/users":
        errmsg = f"Expected PATH_INFO='/api/users', got '{environ['PATH_INFO']}'"
        raise AssertionError(errmsg)
    
    if environ["QUERY_STRING"] != "id=1&name=test":
        errmsg = f"Expected QUERY_STRING='id=1&name=test', got '{environ['QUERY_STRING']}'"
        raise AssertionError(errmsg)
    
    return


def test_build_environ_with_content_type():
    """
        Test building environ with Content-Type header.
    """
    parser = HTTPParser()
    body_stream = io.BytesIO(b"test body")
    
    environ = parser.build_environ(
        method="POST",
        path="/api/users",
        http_version="HTTP/1.1",
        headers={"Content-Type": "application/json", "Content-Length": "9"},
        body_stream=body_stream,
        client_addr=("127.0.0.1", 12345),
        server_addr=("0.0.0.0", 8000),
        scheme="http"
    )
    
    if environ.get("CONTENT_TYPE") != "application/json":
        errmsg = f"Expected CONTENT_TYPE='application/json', got '{environ.get('CONTENT_TYPE')}'"
        raise AssertionError(errmsg)
    
    if environ.get("CONTENT_LENGTH") != "9":
        errmsg = f"Expected CONTENT_LENGTH='9', got '{environ.get('CONTENT_LENGTH')}'"
        raise AssertionError(errmsg)
    
    return


def test_build_environ_converts_headers_to_http_prefix():
    """
        Test that headers are converted to HTTP_* environ keys.
    """
    parser = HTTPParser()
    body_stream = io.BytesIO(b"")
    
    environ = parser.build_environ(
        method="GET",
        path="/",
        http_version="HTTP/1.1",
        headers={"Accept": "application/json", "User-Agent": "TestClient/1.0"},
        body_stream=body_stream,
        client_addr=("127.0.0.1", 12345),
        server_addr=("0.0.0.0", 8000),
        scheme="http"
    )
    
    if environ.get("HTTP_ACCEPT") != "application/json":
        errmsg = f"Expected HTTP_ACCEPT='application/json', got '{environ.get('HTTP_ACCEPT')}'"
        raise AssertionError(errmsg)
    
    if environ.get("HTTP_USER_AGENT") != "TestClient/1.0":
        errmsg = f"Expected HTTP_USER_AGENT='TestClient/1.0', got '{environ.get('HTTP_USER_AGENT')}'"
        raise AssertionError(errmsg)
    
    return


def test_build_environ_includes_wsgi_keys():
    """
        Test that environ includes required WSGI keys.
    """
    parser = HTTPParser()
    body_stream = io.BytesIO(b"")
    
    environ = parser.build_environ(
        method="GET",
        path="/",
        http_version="HTTP/1.1",
        headers={},
        body_stream=body_stream,
        client_addr=("127.0.0.1", 12345),
        server_addr=("0.0.0.0", 8000),
        scheme="http"
    )
    
    required_wsgi_keys = [
        "wsgi.version", "wsgi.url_scheme", "wsgi.input",
        "wsgi.errors", "wsgi.multithread", "wsgi.multiprocess", "wsgi.run_once"
    ]
    
    for key in required_wsgi_keys:
        if key not in environ:
            errmsg = f"Expected '{key}' in environ"
            raise AssertionError(errmsg)
    
    return


def test_is_valid_method_returns_true_for_supported():
    """
        Test that is_valid_method returns True for supported methods.
    """
    parser = HTTPParser()
    
    for method in SUPPORTED_METHODS:
        result = parser.is_valid_method(method)
        if not result:
            errmsg = f"Expected '{method}' to be valid"
            raise AssertionError(errmsg)
    
    return


def test_is_valid_method_returns_false_for_unsupported():
    """
        Test that is_valid_method returns False for unsupported methods.
    """
    parser = HTTPParser()
    
    result = parser.is_valid_method("INVALID")
    
    if result:
        errmsg = "Expected 'INVALID' to be invalid"
        raise AssertionError(errmsg)
    
    return


def test_is_valid_http_version_returns_true_for_supported():
    """
        Test that is_valid_http_version returns True for supported versions.
    """
    parser = HTTPParser()
    
    for version in SUPPORTED_VERSIONS:
        result = parser.is_valid_http_version(version)
        if not result:
            errmsg = f"Expected '{version}' to be valid"
            raise AssertionError(errmsg)
    
    return


def test_is_valid_http_version_returns_false_for_unsupported():
    """
        Test that is_valid_http_version returns False for unsupported versions.
    """
    parser = HTTPParser()
    
    result = parser.is_valid_http_version("HTTP/2.0")
    
    if result:
        errmsg = "Expected 'HTTP/2.0' to be invalid"
        raise AssertionError(errmsg)
    
    return


def test_format_error_response_creates_valid_response():
    """
        Test that format_error_response creates a valid HTTP response.
    """
    parser = HTTPParser()
    
    response = parser.format_error_response(400, "Invalid request")
    
    if not response.startswith(b"HTTP/1.1 400 Bad Request"):
        errmsg = f"Expected response to start with 'HTTP/1.1 400 Bad Request', got '{response[:50]}'"
        raise AssertionError(errmsg)
    
    if b"Content-Type: text/plain" not in response:
        errmsg = "Expected Content-Type header in response"
        raise AssertionError(errmsg)
    
    if b"Connection: close" not in response:
        errmsg = "Expected Connection: close header in response"
        raise AssertionError(errmsg)
    
    return


def test_create_bad_request_response():
    """
        Test that create_bad_request_response creates a 400 response.
    """
    parser = HTTPParser()
    
    response = parser.create_bad_request_response("Missing header")
    
    if not response.startswith(b"HTTP/1.1 400 Bad Request"):
        errmsg = "Expected response to start with 'HTTP/1.1 400 Bad Request'"
        raise AssertionError(errmsg)
    
    if b"Missing header" not in response:
        errmsg = "Expected error detail in response body"
        raise AssertionError(errmsg)
    
    return



# =============================================================================
# Property-Based Tests for HTTPParser
# =============================================================================

def test_property_http_request_parsing_correctness():
    """
        Property test: HTTP Request Parsing Correctness
        
        For any valid HTTP/1.0 or HTTP/1.1 request, the HTTPParser SHALL correctly
        extract method, path, headers, and body, and construct a valid WSGI environ
        dictionary that preserves all request information.
        
        **Feature: wsgi-layer, Property 11: HTTP Request Parsing Correctness**
        **Validates: Requirements 11.1, 11.2, 11.3, 11.8, 11.9, 11.10**
    """
    parser = HTTPParser()
    
    # Run 100 iterations with random HTTP requests
    num_iterations = 100
    
    for iteration in range(num_iterations):
        # Generate random request components
        method = generate_random_method()
        path = generate_random_path()
        query_string = generate_random_query_string()
        http_version = generate_random_http_version()
        headers = generate_random_headers()
        body = generate_random_body()
        
        # Build full path with query string
        if len(query_string) > 0:
            full_path = f"{path}?{query_string}"
        else:
            full_path = path
        
        # Test request line parsing (Requirement 11.1, 11.9)
        request_line = f"{method} {full_path} {http_version}".encode("ascii")
        parsed_method, parsed_path, parsed_version = parser.parse_request_line(request_line)
        
        if parsed_method != method:
            errmsg = f"Iteration {iteration}: Method mismatch. Expected '{method}', got '{parsed_method}'"
            raise AssertionError(errmsg)
        
        if parsed_path != full_path:
            errmsg = f"Iteration {iteration}: Path mismatch. Expected '{full_path}', got '{parsed_path}'"
            raise AssertionError(errmsg)
        
        if parsed_version != http_version:
            errmsg = f"Iteration {iteration}: Version mismatch. Expected '{http_version}', got '{parsed_version}'"
            raise AssertionError(errmsg)
        
        # Test header parsing (Requirement 11.2, 11.3)
        header_lines = [f"{name}: {value}".encode("latin-1") for name, value in headers.items()]
        parsed_headers = parser.parse_headers(header_lines)
        
        for header_name, header_value in headers.items():
            if header_name not in parsed_headers:
                errmsg = f"Iteration {iteration}: Missing header '{header_name}'"
                raise AssertionError(errmsg)
            
            if parsed_headers[header_name] != header_value:
                errmsg = f"Iteration {iteration}: Header '{header_name}' mismatch. Expected '{header_value}', got '{parsed_headers[header_name]}'"
                raise AssertionError(errmsg)
        
        # Test environ construction (Requirement 11.10)
        body_stream = io.BytesIO(body)
        environ = parser.build_environ(
            method=method,
            path=full_path,
            http_version=http_version,
            headers=headers,
            body_stream=body_stream,
            client_addr=("127.0.0.1", 12345),
            server_addr=("0.0.0.0", 8000),
            scheme="http"
        )
        
        # Verify environ contains correct values
        if environ["REQUEST_METHOD"] != method:
            errmsg = f"Iteration {iteration}: Environ REQUEST_METHOD mismatch. Expected '{method}', got '{environ['REQUEST_METHOD']}'"
            raise AssertionError(errmsg)
        
        if environ["PATH_INFO"] != path:
            errmsg = f"Iteration {iteration}: Environ PATH_INFO mismatch. Expected '{path}', got '{environ['PATH_INFO']}'"
            raise AssertionError(errmsg)
        
        if environ["QUERY_STRING"] != query_string:
            errmsg = f"Iteration {iteration}: Environ QUERY_STRING mismatch. Expected '{query_string}', got '{environ['QUERY_STRING']}'"
            raise AssertionError(errmsg)
        
        if environ["SERVER_PROTOCOL"] != http_version:
            errmsg = f"Iteration {iteration}: Environ SERVER_PROTOCOL mismatch. Expected '{http_version}', got '{environ['SERVER_PROTOCOL']}'"
            raise AssertionError(errmsg)
    
    return


def test_property_server_environ_construction():
    """
        Property test: Server Environ Construction
        
        For any HTTP request received by the built-in server, the constructed WSGI
        environ dictionary SHALL contain all required CGI and WSGI keys with correct
        values matching the original HTTP request.
        
        **Feature: wsgi-layer, Property 13: Server Environ Construction**
        **Validates: Requirements 5.3, 5.4**
    """
    parser = HTTPParser()
    
    # Required CGI keys per WSGI spec
    required_cgi_keys = [
        "REQUEST_METHOD", "SCRIPT_NAME", "PATH_INFO", "QUERY_STRING",
        "SERVER_NAME", "SERVER_PORT", "SERVER_PROTOCOL",
    ]
    
    # Required WSGI keys per WSGI spec
    required_wsgi_keys = [
        "wsgi.version", "wsgi.url_scheme", "wsgi.input",
        "wsgi.errors", "wsgi.multithread", "wsgi.multiprocess", "wsgi.run_once",
    ]
    
    # Run 100 iterations with random HTTP requests
    num_iterations = 100
    
    for iteration in range(num_iterations):
        # Generate random request components
        method = generate_random_method()
        path = generate_random_path()
        query_string = generate_random_query_string()
        http_version = generate_random_http_version()
        headers = generate_random_headers()
        body = generate_random_body()
        
        # Build full path with query string
        if len(query_string) > 0:
            full_path = f"{path}?{query_string}"
        else:
            full_path = path
        
        # Generate random server and client addresses
        server_host = random.choice(["0.0.0.0", "127.0.0.1", "192.168.1.1"])
        server_port = random.randint(1024, 65535)
        client_host = f"192.168.1.{random.randint(1, 254)}"
        client_port = random.randint(1024, 65535)
        scheme = random.choice(["http", "https"])
        
        # Build environ
        body_stream = io.BytesIO(body)
        environ = parser.build_environ(
            method=method,
            path=full_path,
            http_version=http_version,
            headers=headers,
            body_stream=body_stream,
            client_addr=(client_host, client_port),
            server_addr=(server_host, server_port),
            scheme=scheme
        )
        
        # Verify all required CGI keys are present (Requirement 5.3)
        for key in required_cgi_keys:
            if key not in environ:
                errmsg = f"Iteration {iteration}: Missing required CGI key '{key}'"
                raise AssertionError(errmsg)
        
        # Verify all required WSGI keys are present (Requirement 5.3)
        for key in required_wsgi_keys:
            if key not in environ:
                errmsg = f"Iteration {iteration}: Missing required WSGI key '{key}'"
                raise AssertionError(errmsg)
        
        # Verify CGI values match request (Requirement 5.4)
        if environ["REQUEST_METHOD"] != method:
            errmsg = f"Iteration {iteration}: REQUEST_METHOD mismatch"
            raise AssertionError(errmsg)
        
        if environ["PATH_INFO"] != path:
            errmsg = f"Iteration {iteration}: PATH_INFO mismatch"
            raise AssertionError(errmsg)
        
        if environ["QUERY_STRING"] != query_string:
            errmsg = f"Iteration {iteration}: QUERY_STRING mismatch"
            raise AssertionError(errmsg)
        
        if environ["SERVER_NAME"] != server_host:
            errmsg = f"Iteration {iteration}: SERVER_NAME mismatch"
            raise AssertionError(errmsg)
        
        if environ["SERVER_PORT"] != str(server_port):
            errmsg = f"Iteration {iteration}: SERVER_PORT mismatch"
            raise AssertionError(errmsg)
        
        # Verify WSGI values (Requirement 5.4)
        if environ["wsgi.url_scheme"] != scheme:
            errmsg = f"Iteration {iteration}: wsgi.url_scheme mismatch"
            raise AssertionError(errmsg)
        
        if environ["wsgi.version"] != (1, 0):
            errmsg = f"Iteration {iteration}: wsgi.version mismatch"
            raise AssertionError(errmsg)
        
        # Verify wsgi.input contains the body
        environ["wsgi.input"].seek(0)
        read_body = environ["wsgi.input"].read()
        if read_body != body:
            errmsg = f"Iteration {iteration}: wsgi.input body mismatch"
            raise AssertionError(errmsg)
        
        # Verify headers are converted to HTTP_* keys
        for header_name, header_value in headers.items():
            header_upper = header_name.upper()
            if header_upper in ("CONTENT-TYPE", "CONTENT-LENGTH"):
                # These are special and don't get HTTP_ prefix
                environ_key = header_upper.replace("-", "_")
            else:
                environ_key = "HTTP_" + header_upper.replace("-", "_")
            
            if environ_key not in environ:
                errmsg = f"Iteration {iteration}: Missing header key '{environ_key}'"
                raise AssertionError(errmsg)
            
            if environ[environ_key] != header_value:
                errmsg = f"Iteration {iteration}: Header '{environ_key}' value mismatch"
                raise AssertionError(errmsg)
    
    return


# =============================================================================
# Tests for limits, end of stream and timeouts while reading a request
# =============================================================================

class StallingSocket:
    """
        Mock socket that serves its data and then times out, like a client that
        stops sending without closing the connection.
    """
    
    def __init__(self, data: bytes):
        """
            Construct a stalling socket with the data it serves first.
        """
        self._data = data
        self._position = 0
        return
    
    def recv(self, size: int) -> bytes:
        """
            Read data from the mock socket, time out when it is used up.
        """
        if self._position >= len(self._data):
            raise socket.timeout("timed out")
        
        end = min(self._position + size, len(self._data))
        rtnval = self._data[self._position:end]
        self._position = end
        return rtnval


CLIENT_ADDR = ("127.0.0.1", 12345)
SERVER_ADDR = ("127.0.0.1", 8000)


def parse_raw_request(data: bytes, config: ServerConfig = None) -> Dict[str, Any]:
    """
        Parse a raw request with a parser built from the given configuration.
    """
    parser = HTTPParser(config)
    rtnval = parser.parse_request(MockSocket(data), CLIENT_ADDR, SERVER_ADDR)
    return rtnval


def get_parse_error(data: bytes, config: ServerConfig = None) -> Exception:
    """
        Parse a raw request that must be refused and return the error raised.
    """
    rtnval = None
    try:
        parse_raw_request(data, config)
    except Exception as err:
        rtnval = err
    
    if rtnval is None:
        errmsg = f"Expected the request to be refused: {data[:80]!r}"
        raise AssertionError(errmsg)
    
    return rtnval


def test_parse_request_refuses_request_line_over_limit_with_414():
    """
        Test that a request line longer than the limit is refused with 414.
    """
    config = ServerConfig(max_request_line=256)
    data = b"GET /" + b"a" * 5000 + b" HTTP/1.1\r\nHost: x\r\n\r\n"
    
    err = get_parse_error(data, config)
    
    if not isinstance(err, RequestLineTooLong):
        errmsg = f"Expected RequestLineTooLong, got {type(err).__name__}: {err}"
        raise AssertionError(errmsg)
    
    if err.status_code != 414:
        errmsg = f"Expected status code 414, got {err.status_code}"
        raise AssertionError(errmsg)
    
    return


def test_parse_request_refuses_endless_request_line_without_newline():
    """
        Test that bytes without any line feed are refused once the limit is passed.
    """
    config = ServerConfig(max_request_line=256)
    
    err = get_parse_error(b"G" * 100000, config)
    
    if not isinstance(err, RequestLineTooLong):
        errmsg = f"Expected RequestLineTooLong, got {type(err).__name__}: {err}"
        raise AssertionError(errmsg)
    
    return


def test_parse_request_refuses_headers_over_limit_with_431():
    """
        Test that headers larger than the limit are refused with 431 while being read.
    """
    config = ServerConfig(max_header_size=512)
    data = b"GET / HTTP/1.1\r\nX-Big: " + b"a" * 5000 + b"\r\n\r\n"
    
    err = get_parse_error(data, config)
    
    if not isinstance(err, HeaderTooLarge):
        errmsg = f"Expected HeaderTooLarge, got {type(err).__name__}: {err}"
        raise AssertionError(errmsg)
    
    if err.status_code != 431:
        errmsg = f"Expected status code 431, got {err.status_code}"
        raise AssertionError(errmsg)
    
    return


def test_parse_request_refuses_too_many_headers_with_431():
    """
        Test that more headers than the limit are refused with 431.
    """
    config = ServerConfig(max_headers=3)
    data = b"GET / HTTP/1.1\r\n" + b"".join(b"X-H%d: v\r\n" % idx for idx in range(10)) + b"\r\n"
    
    err = get_parse_error(data, config)
    
    if not isinstance(err, TooManyHeaders):
        errmsg = f"Expected TooManyHeaders, got {type(err).__name__}: {err}"
        raise AssertionError(errmsg)
    
    if err.status_code != 431:
        errmsg = f"Expected status code 431, got {err.status_code}"
        raise AssertionError(errmsg)
    
    return


def test_parse_request_refuses_body_over_limit_with_413():
    """
        Test that a Content-Length over the body limit is refused with 413.
    """
    config = ServerConfig(max_request_size=10)
    data = b"POST / HTTP/1.1\r\nContent-Length: 11\r\n\r\nhello world"
    
    err = get_parse_error(data, config)
    
    if not isinstance(err, RequestEntityTooLarge):
        errmsg = f"Expected RequestEntityTooLarge, got {type(err).__name__}: {err}"
        raise AssertionError(errmsg)
    
    if err.status_code != 413:
        errmsg = f"Expected status code 413, got {err.status_code}"
        raise AssertionError(errmsg)
    
    return


def test_parse_request_raises_connection_closed_when_nothing_was_sent():
    """
        Test that a connection closed before any request byte is not a bad request.
    """
    err = get_parse_error(b"")
    
    if not isinstance(err, ConnectionClosed):
        errmsg = f"Expected ConnectionClosed, got {type(err).__name__}: {err}"
        raise AssertionError(errmsg)
    
    return


def test_parse_request_refuses_connection_closed_inside_headers():
    """
        Test that headers that end with the connection, without the empty line, are refused.
    """
    err = get_parse_error(b"GET / HTTP/1.1\r\nHost: x\r\n")
    
    if not isinstance(err, IncompleteRequest):
        errmsg = f"Expected IncompleteRequest, got {type(err).__name__}: {err}"
        raise AssertionError(errmsg)
    
    return


def test_parse_request_refuses_body_shorter_than_content_length():
    """
        Test that a body cut short is refused and not handed over truncated.
    """
    err = get_parse_error(b"POST / HTTP/1.1\r\nContent-Length: 100\r\n\r\nshort")
    
    if not isinstance(err, IncompleteRequest):
        errmsg = f"Expected IncompleteRequest, got {type(err).__name__}: {err}"
        raise AssertionError(errmsg)
    
    return


def test_parse_request_lets_idle_timeout_bubble():
    """
        Test that a timeout before any request byte stays a socket timeout.
    """
    parser = HTTPParser()
    
    raised = None
    try:
        parser.parse_request(StallingSocket(b""), CLIENT_ADDR, SERVER_ADDR)
    except Exception as err:
        raised = err
    
    if not isinstance(raised, socket.timeout) or isinstance(raised, RequestTimeout):
        errmsg = f"Expected a plain socket.timeout, got {type(raised).__name__}: {raised}"
        raise AssertionError(errmsg)
    
    return


def test_parse_request_reports_stall_inside_headers_as_request_timeout():
    """
        Test that a client that stalls inside the headers gets a request timeout.
    """
    parser = HTTPParser()
    
    raised = None
    try:
        parser.parse_request(StallingSocket(b"GET / HTTP/1.1\r\nHost: x\r\n"), CLIENT_ADDR, SERVER_ADDR)
    except Exception as err:
        raised = err
    
    if not isinstance(raised, RequestTimeout):
        errmsg = f"Expected RequestTimeout, got {type(raised).__name__}: {raised}"
        raise AssertionError(errmsg)
    
    if raised.status_code != 408:
        errmsg = f"Expected status code 408, got {raised.status_code}"
        raise AssertionError(errmsg)
    
    return


def test_parse_request_reports_stall_inside_body_as_request_timeout():
    """
        Test that a client that stalls inside the body gets a request timeout.
    """
    parser = HTTPParser()
    data = b"POST / HTTP/1.1\r\nContent-Length: 100\r\n\r\nshort"
    
    raised = None
    try:
        parser.parse_request(StallingSocket(data), CLIENT_ADDR, SERVER_ADDR)
    except Exception as err:
        raised = err
    
    if not isinstance(raised, RequestTimeout):
        errmsg = f"Expected RequestTimeout, got {type(raised).__name__}: {raised}"
        raise AssertionError(errmsg)
    
    return


def test_parse_request_skips_one_empty_line_before_request_line():
    """
        Test that one empty line before the request line is ignored.
    """
    environ = parse_raw_request(b"\r\nGET /after HTTP/1.1\r\nHost: x\r\n\r\n")
    
    if environ["PATH_INFO"] != "/after":
        errmsg = f"Expected PATH_INFO '/after', got {environ['PATH_INFO']!r}"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Tests for request framing
# =============================================================================

def test_parse_request_refuses_content_length_with_transfer_encoding():
    """
        Test that a request with both Content-Length and Transfer-Encoding is refused.
    """
    data = b"POST / HTTP/1.1\r\nContent-Length: 4\r\nTransfer-Encoding: chunked\r\n\r\n5\r\nhello\r\n0\r\n\r\n"
    
    err = get_parse_error(data)
    
    if not isinstance(err, RequestParseError) or err.status_code != 400:
        errmsg = f"Expected a 400 RequestParseError, got {type(err).__name__}: {err}"
        raise AssertionError(errmsg)
    
    return


def test_parse_request_refuses_transfer_encoding_that_only_contains_chunked():
    """
        Test that a transfer coding such as 'xchunked' is not taken for chunked.
    """
    data = b"POST / HTTP/1.1\r\nTransfer-Encoding: xchunked\r\n\r\n5\r\nhello\r\n0\r\n\r\n"
    
    err = get_parse_error(data)
    
    if not isinstance(err, RequestParseError) or err.status_code != 400:
        errmsg = f"Expected a 400 RequestParseError, got {type(err).__name__}: {err}"
        raise AssertionError(errmsg)
    
    return


def test_parse_request_refuses_transfer_encoding_not_ending_in_chunked():
    """
        Test that a transfer coding list whose last coding is not chunked is refused.
    """
    data = b"POST / HTTP/1.1\r\nTransfer-Encoding: chunked, gzip\r\n\r\n5\r\nhello\r\n0\r\n\r\n"
    
    err = get_parse_error(data)
    
    if not isinstance(err, RequestParseError) or err.status_code != 400:
        errmsg = f"Expected a 400 RequestParseError, got {type(err).__name__}: {err}"
        raise AssertionError(errmsg)
    
    return


def test_parse_request_refuses_transfer_encoding_in_http_1_0():
    """
        Test that Transfer-Encoding in an HTTP/1.0 request is refused.
    """
    data = b"POST / HTTP/1.0\r\nTransfer-Encoding: chunked\r\n\r\n5\r\nhello\r\n0\r\n\r\n"
    
    err = get_parse_error(data)
    
    if not isinstance(err, RequestParseError) or err.status_code != 400:
        errmsg = f"Expected a 400 RequestParseError, got {type(err).__name__}: {err}"
        raise AssertionError(errmsg)
    
    return


def test_parse_request_refuses_lenient_content_length_forms():
    """
        Test that Content-Length values 'int' accepts but HTTP does not are refused.
    """
    for value in (b"+5", b"5_0", b"0x10", b"-5", b"5, 5", b"5.0", b"\xb2"):
        data = b"POST / HTTP/1.1\r\nContent-Length: " + value + b"\r\n\r\nhello"
        
        err = get_parse_error(data)
        
        if not isinstance(err, RequestParseError) or err.status_code != 400:
            errmsg = f"Expected a 400 RequestParseError for Content-Length {value!r}, got {type(err).__name__}: {err}"
            raise AssertionError(errmsg)
    
    return


def test_parse_request_refuses_conflicting_content_length_headers():
    """
        Test that two Content-Length headers with different values are refused.
    """
    data = b"POST / HTTP/1.1\r\nContent-Length: 5\r\nContent-Length: 3\r\n\r\nhello"
    
    err = get_parse_error(data)
    
    if not isinstance(err, RequestParseError) or err.status_code != 400:
        errmsg = f"Expected a 400 RequestParseError, got {type(err).__name__}: {err}"
        raise AssertionError(errmsg)
    
    return


def test_parse_request_accepts_repeated_identical_content_length():
    """
        Test that a Content-Length header repeated with the same value is accepted.
    """
    data = b"POST / HTTP/1.1\r\nContent-Length: 5\r\nContent-Length: 5\r\n\r\nhello"
    
    environ = parse_raw_request(data)
    
    if environ["CONTENT_LENGTH"] != "5":
        errmsg = f"Expected CONTENT_LENGTH '5', got {environ['CONTENT_LENGTH']!r}"
        raise AssertionError(errmsg)
    
    return


def test_parse_request_honours_content_length_in_any_case():
    """
        Test that the body is read when the Content-Length name is not capitalised as usual.
    """
    data = b"POST / HTTP/1.1\r\nCONTENT-LENGTH: 5\r\n\r\nhello"
    
    environ = parse_raw_request(data)
    body = environ["wsgi.input"].read()
    
    if body != b"hello":
        errmsg = f"Expected the body b'hello', got {body!r}"
        raise AssertionError(errmsg)
    
    return


def test_parse_request_decodes_chunked_body():
    """
        Test that a chunked body is decoded and described by CONTENT_LENGTH.
    """
    data = b"POST / HTTP/1.1\r\nTransfer-Encoding: chunked\r\n\r\n5\r\nhello\r\n6;ext=1\r\n world\r\n0\r\n\r\n"
    
    environ = parse_raw_request(data)
    body = environ["wsgi.input"].read()
    
    if body != b"hello world":
        errmsg = f"Expected the decoded body b'hello world', got {body!r}"
        raise AssertionError(errmsg)
    
    if environ.get("CONTENT_LENGTH") != "11":
        errmsg = f"Expected CONTENT_LENGTH '11', got {environ.get('CONTENT_LENGTH')!r}"
        raise AssertionError(errmsg)
    
    if "HTTP_TRANSFER_ENCODING" in environ:
        errmsg = "Expected Transfer-Encoding to be removed once the body is decoded"
        raise AssertionError(errmsg)
    
    return


def test_parse_request_consumes_chunked_trailers():
    """
        Test that the trailers of a chunked body are not parsed as the next request.
    """
    data = (
        b"POST /first HTTP/1.1\r\nTransfer-Encoding: chunked\r\n\r\n"
        b"5\r\nhello\r\n0\r\nX-Trailer: GET /smuggled HTTP/1.1\r\n\r\n"
        b"GET /second HTTP/1.1\r\nHost: x\r\n\r\n"
    )
    parser = HTTPParser()
    reader = SocketReader(MockSocket(data))
    
    parser.parse_request(reader, CLIENT_ADDR, SERVER_ADDR)
    environ = parser.parse_request(reader, CLIENT_ADDR, SERVER_ADDR)
    
    if environ["PATH_INFO"] != "/second":
        errmsg = f"Expected the next request to be '/second', got {environ['PATH_INFO']!r}"
        raise AssertionError(errmsg)
    
    return


def test_parse_chunked_body_refuses_chunk_size_that_is_not_plain_hex():
    """
        Test that chunk sizes 'int' accepts but HTTP does not are refused.
    """
    for size in (b"0x5", b"+5", b"5_0", b" 5", b"5 "):
        data = b"POST / HTTP/1.1\r\nTransfer-Encoding: chunked\r\n\r\n" + size + b"\r\nhello\r\n0\r\n\r\n"
        
        err = get_parse_error(data)
        
        if not isinstance(err, RequestParseError) or err.status_code != 400:
            errmsg = f"Expected a 400 RequestParseError for chunk size {size!r}, got {type(err).__name__}: {err}"
            raise AssertionError(errmsg)
    
    return


def test_parse_chunked_body_refuses_missing_crlf_after_chunk():
    """
        Test that chunk data that is not followed by CRLF is refused.
    """
    data = b"POST / HTTP/1.1\r\nTransfer-Encoding: chunked\r\n\r\n5\r\nhelloXX0\r\n\r\n"
    
    err = get_parse_error(data)
    
    if not isinstance(err, RequestParseError):
        errmsg = f"Expected RequestParseError, got {type(err).__name__}: {err}"
        raise AssertionError(errmsg)
    
    return


def test_parse_chunked_body_enforces_body_limit_with_413():
    """
        Test that a chunked body over the body limit is refused with 413.
    """
    config = ServerConfig(max_request_size=4)
    data = b"POST / HTTP/1.1\r\nTransfer-Encoding: chunked\r\n\r\n5\r\nhello\r\n0\r\n\r\n"
    
    err = get_parse_error(data, config)
    
    if not isinstance(err, RequestEntityTooLarge):
        errmsg = f"Expected RequestEntityTooLarge, got {type(err).__name__}: {err}"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Tests for repeated headers, header names and the path
# =============================================================================

def test_parse_headers_joins_repeated_header_with_comma():
    """
        Test that a repeated header keeps every value, joined with a comma.
    """
    parser = HTTPParser()
    
    headers = parser.parse_headers([b"X-Forwarded-For: 10.0.0.1", b"x-forwarded-for: 10.0.0.2"])
    
    if headers.get("X-Forwarded-For") != "10.0.0.1, 10.0.0.2":
        errmsg = f"Expected both values joined with ', ', got {headers}"
        raise AssertionError(errmsg)
    
    return


def test_parse_headers_joins_repeated_cookie_with_semicolon():
    """
        Test that repeated Cookie headers are joined with a semicolon.
    """
    parser = HTTPParser()
    
    headers = parser.parse_headers([b"Cookie: a=1", b"Cookie: b=2"])
    
    if headers.get("Cookie") != "a=1; b=2":
        errmsg = f"Expected the cookies joined with '; ', got {headers}"
        raise AssertionError(errmsg)
    
    return


def test_parse_headers_refuses_second_host_header():
    """
        Test that a request with two Host headers is refused.
    """
    parser = HTTPParser()
    
    raised = False
    try:
        parser.parse_headers([b"Host: a.example", b"Host: b.example"])
    except RequestParseError:
        raised = True
    
    if not raised:
        errmsg = "Expected RequestParseError for two Host headers"
        raise AssertionError(errmsg)
    
    return


def test_parse_headers_refuses_whitespace_before_colon():
    """
        Test that a header name followed by a space before the colon is refused.
    """
    parser = HTTPParser()
    
    raised = False
    try:
        parser.parse_headers([b"Content-Length : 5"])
    except RequestParseError:
        raised = True
    
    if not raised:
        errmsg = "Expected RequestParseError for whitespace between the name and the colon"
        raise AssertionError(errmsg)
    
    return


def test_parse_headers_refuses_bare_carriage_return_in_value():
    """
        Test that a carriage return inside a header value is refused.
    """
    parser = HTTPParser()
    
    raised = False
    try:
        parser.parse_headers([b"X-Test: a\rX-Injected: b"])
    except RequestParseError:
        raised = True
    
    if not raised:
        errmsg = "Expected RequestParseError for a carriage return inside a value"
        raise AssertionError(errmsg)
    
    return


def test_build_environ_drops_header_names_with_underscore():
    """
        Test that a header named with an underscore cannot stand in for the hyphen form.
    """
    parser = HTTPParser()
    
    environ = parser.build_environ(
        method="GET",
        path="/",
        http_version="HTTP/1.1",
        headers={"X-User": "from-proxy", "X_User": "from-client"},
        body_stream=io.BytesIO(b""),
        client_addr=CLIENT_ADDR,
        server_addr=SERVER_ADDR
    )
    
    if environ.get("HTTP_X_USER") != "from-proxy":
        errmsg = f"Expected HTTP_X_USER to come from 'X-User', got {environ.get('HTTP_X_USER')!r}"
        raise AssertionError(errmsg)
    
    return


def test_build_environ_percent_decodes_path_info():
    """
        Test that PATH_INFO is the percent-decoded path.
    """
    parser = HTTPParser()
    
    environ = parser.build_environ(
        method="GET",
        path="/files/a%20b?q=a%20b",
        http_version="HTTP/1.1",
        headers={},
        body_stream=io.BytesIO(b""),
        client_addr=CLIENT_ADDR,
        server_addr=SERVER_ADDR
    )
    
    if environ["PATH_INFO"] != "/files/a b":
        errmsg = f"Expected PATH_INFO '/files/a b', got {environ['PATH_INFO']!r}"
        raise AssertionError(errmsg)
    
    # The query string is left encoded, decoding it is up to the application
    if environ["QUERY_STRING"] != "q=a%20b":
        errmsg = f"Expected QUERY_STRING 'q=a%20b', got {environ['QUERY_STRING']!r}"
        raise AssertionError(errmsg)
    
    return


def test_build_environ_carries_utf8_path_as_latin1_string():
    """
        Test that a UTF-8 path is carried the way PEP 3333 defines, one character per byte.
    """
    parser = HTTPParser()
    
    environ = parser.build_environ(
        method="GET",
        path="/caf%C3%A9",
        http_version="HTTP/1.1",
        headers={},
        body_stream=io.BytesIO(b""),
        client_addr=CLIENT_ADDR,
        server_addr=SERVER_ADDR
    )
    
    decoded = environ["PATH_INFO"].encode("latin-1").decode("utf-8")
    
    if decoded != "/caf\u00e9":
        errmsg = f"Expected PATH_INFO to decode to '/caf\u00e9', got {decoded!r}"
        raise AssertionError(errmsg)
    
    return


def test_build_environ_keeps_raw_request_target():
    """
        Test that the request target as sent is available as REQUEST_URI.
    """
    parser = HTTPParser()
    
    environ = parser.build_environ(
        method="GET",
        path="/files/a%20b?q=1",
        http_version="HTTP/1.1",
        headers={},
        body_stream=io.BytesIO(b""),
        client_addr=CLIENT_ADDR,
        server_addr=SERVER_ADDR
    )
    
    if environ.get("REQUEST_URI") != "/files/a%20b?q=1":
        errmsg = f"Expected REQUEST_URI to be the raw target, got {environ.get('REQUEST_URI')!r}"
        raise AssertionError(errmsg)
    
    return
