"""
    Tests for the EnvironParser class.
    
    This module contains unit tests and property-based tests for the WSGI
    environ parser functionality.
    
    **Feature: wsgi-layer, Property 2: Environ Parsing Round-Trip**
    **Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 2.9, 2.10, 2.11**
"""

import random
import string
from io import BytesIO
from typing import Any, Dict

from ccai.webworks.wsgi.environparser import EnvironParser
from ccai.webworks.wsgi.request import Request
from ccai.webworks.wsgi.constants import ENVIRON_REQUEST, ENVIRON_ROUTE, ENVIRON_PATH_PARAMS
from ccai.webworks.wsgi.exceptions import RequestEntityTooLarge


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


def generate_random_scheme() -> str:
    """
        Generate a random URL scheme.
    """
    rtnval = random.choice(["http", "https"])
    return rtnval


def generate_random_host() -> str:
    """
        Generate a random host name.
    """
    hosts = ["localhost", "example.com", "api.example.com", "test.local", "192.168.1.1"]
    rtnval = random.choice(hosts)
    return rtnval


def generate_random_port(scheme: str) -> int:
    """
        Generate a random port number.
    """
    if random.random() < 0.3:
        if scheme == "https":
            rtnval = 443
        else:
            rtnval = 80
    else:
        rtnval = random.randint(1024, 65535)
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
        length = random.randint(1, 1000)
        rtnval = bytes(random.randint(0, 255) for _ in range(length))
    return rtnval


def generate_random_content_type() -> str:
    """
        Generate a random content type.
    """
    content_types = [
        "application/json", "application/x-www-form-urlencoded",
        "text/plain", "text/html", "application/xml",
    ]
    rtnval = random.choice(content_types)
    return rtnval


def generate_random_environ() -> Dict[str, Any]:
    """
        Generate a random valid WSGI environ dictionary.
    """
    method = generate_random_method()
    path = generate_random_path()
    query_string = generate_random_query_string()
    scheme = generate_random_scheme()
    host = generate_random_host()
    port = generate_random_port(scheme)
    headers = generate_random_headers()
    body = generate_random_body()

    environ: Dict[str, Any] = {
        "REQUEST_METHOD": method,
        "PATH_INFO": path,
        "QUERY_STRING": query_string,
        "wsgi.url_scheme": scheme,
        "SERVER_NAME": host,
        "SERVER_PORT": str(port),
        "wsgi.input": BytesIO(body),
    }

    for header_name, header_value in headers.items():
        environ_key = "HTTP_" + header_name.upper().replace("-", "_")
        environ[environ_key] = header_value

    if len(body) > 0:
        content_type = generate_random_content_type()
        environ["CONTENT_TYPE"] = content_type
        environ["CONTENT_LENGTH"] = str(len(body))

    return environ


def environ_to_request_values(environ: Dict[str, Any]) -> Dict[str, Any]:
    """
        Extract expected request values from an environ dictionary.
    """
    wsgi_input = environ.get("wsgi.input")
    if wsgi_input is not None:
        wsgi_input.seek(0)
        body = wsgi_input.read()
        wsgi_input.seek(0)
    else:
        body = b""

    headers: Dict[str, str] = {}
    for key, value in environ.items():
        if key.startswith("HTTP_"):
            header_name = key[5:].replace("_", "-").title()
            headers[header_name] = str(value)

    content_type = environ.get("CONTENT_TYPE")
    if content_type is not None and len(str(content_type)) > 0:
        headers["Content-Type"] = str(content_type)

    content_length = environ.get("CONTENT_LENGTH")
    if content_length is not None and len(str(content_length)) > 0:
        headers["Content-Length"] = str(content_length)

    rtnval = {
        "method": environ.get("REQUEST_METHOD", "GET").upper(),
        "path": environ.get("PATH_INFO", "/"),
        "query_string": environ.get("QUERY_STRING", ""),
        "scheme": environ.get("wsgi.url_scheme", "http").lower(),
        "host": environ.get("SERVER_NAME", "localhost"),
        "port": int(environ.get("SERVER_PORT", "80")),
        "headers": headers,
        "body": body,
        "content_type": content_type if content_type and len(str(content_type)) > 0 else None,
        "content_length": int(content_length) if content_length and len(str(content_length)) > 0 else None,
    }
    return rtnval



# =============================================================================
# Unit Tests for EnvironParser
# =============================================================================

def test_get_method_returns_request_method():
    """
        Test that get_method returns the REQUEST_METHOD from environ.
    """
    parser = EnvironParser()
    environ = {"REQUEST_METHOD": "POST"}
    
    result = parser.get_method(environ)
    
    expected = "POST"
    if result != expected:
        errmsg = f"Expected method '{expected}', got '{result}'"
        raise AssertionError(errmsg)
    
    return


def test_get_method_returns_default_when_missing():
    """
        Test that get_method returns 'GET' when REQUEST_METHOD is missing.
    """
    parser = EnvironParser()
    environ: Dict[str, Any] = {}
    
    result = parser.get_method(environ)
    
    expected = "GET"
    if result != expected:
        errmsg = f"Expected default method '{expected}', got '{result}'"
        raise AssertionError(errmsg)
    
    return


def test_get_path_returns_path_info():
    """
        Test that get_path returns the PATH_INFO from environ.
    """
    parser = EnvironParser()
    environ = {"PATH_INFO": "/api/users"}
    
    result = parser.get_path(environ)
    
    expected = "/api/users"
    if result != expected:
        errmsg = f"Expected path '{expected}', got '{result}'"
        raise AssertionError(errmsg)
    
    return


def test_get_path_returns_default_when_missing():
    """
        Test that get_path returns '/' when PATH_INFO is missing.
    """
    parser = EnvironParser()
    environ: Dict[str, Any] = {}
    
    result = parser.get_path(environ)
    
    expected = "/"
    if result != expected:
        errmsg = f"Expected default path '{expected}', got '{result}'"
        raise AssertionError(errmsg)
    
    return


def test_get_query_string_returns_query_string():
    """
        Test that get_query_string returns the QUERY_STRING from environ.
    """
    parser = EnvironParser()
    environ = {"QUERY_STRING": "id=1&name=test"}
    
    result = parser.get_query_string(environ)
    
    expected = "id=1&name=test"
    if result != expected:
        errmsg = f"Expected query string '{expected}', got '{result}'"
        raise AssertionError(errmsg)
    
    return


def test_get_scheme_returns_url_scheme():
    """
        Test that get_scheme returns the wsgi.url_scheme from environ.
    """
    parser = EnvironParser()
    environ = {"wsgi.url_scheme": "https"}
    
    result = parser.get_scheme(environ)
    
    expected = "https"
    if result != expected:
        errmsg = f"Expected scheme '{expected}', got '{result}'"
        raise AssertionError(errmsg)
    
    return


def test_get_host_returns_server_name():
    """
        Test that get_host returns the SERVER_NAME from environ.
    """
    parser = EnvironParser()
    environ = {"SERVER_NAME": "example.com"}
    
    result = parser.get_host(environ)
    
    expected = "example.com"
    if result != expected:
        errmsg = f"Expected host '{expected}', got '{result}'"
        raise AssertionError(errmsg)
    
    return


def test_get_port_returns_server_port():
    """
        Test that get_port returns the SERVER_PORT from environ.
    """
    parser = EnvironParser()
    environ = {"SERVER_PORT": "8080", "wsgi.url_scheme": "http"}
    
    result = parser.get_port(environ)
    
    expected = 8080
    if result != expected:
        errmsg = f"Expected port {expected}, got {result}"
        raise AssertionError(errmsg)
    
    return


def test_get_port_returns_default_for_http():
    """
        Test that get_port returns 80 for http when SERVER_PORT is missing.
    """
    parser = EnvironParser()
    environ = {"wsgi.url_scheme": "http"}
    
    result = parser.get_port(environ)
    
    expected = 80
    if result != expected:
        errmsg = f"Expected default http port {expected}, got {result}"
        raise AssertionError(errmsg)
    
    return


def test_get_port_returns_default_for_https():
    """
        Test that get_port returns 443 for https when SERVER_PORT is missing.
    """
    parser = EnvironParser()
    environ = {"wsgi.url_scheme": "https"}
    
    result = parser.get_port(environ)
    
    expected = 443
    if result != expected:
        errmsg = f"Expected default https port {expected}, got {result}"
        raise AssertionError(errmsg)
    
    return



def test_get_headers_extracts_http_headers():
    """
        Test that get_headers extracts HTTP_* prefixed headers.
    """
    parser = EnvironParser()
    environ = {
        "HTTP_ACCEPT": "application/json",
        "HTTP_USER_AGENT": "TestClient/1.0",
        "HTTP_X_CUSTOM_HEADER": "custom-value",
    }
    
    result = parser.get_headers(environ)
    
    if "Accept" not in result:
        errmsg = "Expected 'Accept' header in result"
        raise AssertionError(errmsg)
    
    if result["Accept"] != "application/json":
        errmsg = f"Expected Accept='application/json', got '{result['Accept']}'"
        raise AssertionError(errmsg)
    
    if "User-Agent" not in result:
        errmsg = "Expected 'User-Agent' header in result"
        raise AssertionError(errmsg)
    
    if "X-Custom-Header" not in result:
        errmsg = "Expected 'X-Custom-Header' header in result"
        raise AssertionError(errmsg)
    
    return


def test_get_headers_includes_content_type():
    """
        Test that get_headers includes CONTENT_TYPE.
    """
    parser = EnvironParser()
    environ = {"CONTENT_TYPE": "application/json"}
    
    result = parser.get_headers(environ)
    
    if "Content-Type" not in result:
        errmsg = "Expected 'Content-Type' header in result"
        raise AssertionError(errmsg)
    
    if result["Content-Type"] != "application/json":
        errmsg = f"Expected Content-Type='application/json', got '{result['Content-Type']}'"
        raise AssertionError(errmsg)
    
    return


def test_get_headers_includes_content_length():
    """
        Test that get_headers includes CONTENT_LENGTH.
    """
    parser = EnvironParser()
    environ = {"CONTENT_LENGTH": "100"}
    
    result = parser.get_headers(environ)
    
    if "Content-Length" not in result:
        errmsg = "Expected 'Content-Length' header in result"
        raise AssertionError(errmsg)
    
    if result["Content-Length"] != "100":
        errmsg = f"Expected Content-Length='100', got '{result['Content-Length']}'"
        raise AssertionError(errmsg)
    
    return


def test_get_body_reads_from_wsgi_input():
    """
        Test that get_body reads from wsgi.input.
    """
    parser = EnvironParser()
    body_content = b"test body content"
    environ = {
        "wsgi.input": BytesIO(body_content),
        "CONTENT_LENGTH": str(len(body_content)),
    }
    
    result = parser.get_body(environ)
    
    if result != body_content:
        errmsg = f"Expected body '{body_content}', got '{result}'"
        raise AssertionError(errmsg)
    
    return


def test_get_body_returns_empty_when_no_input():
    """
        Test that get_body returns empty bytes when wsgi.input is missing.
    """
    parser = EnvironParser()
    environ: Dict[str, Any] = {}
    
    result = parser.get_body(environ)
    
    if result != b"":
        errmsg = f"Expected empty body, got '{result}'"
        raise AssertionError(errmsg)
    
    return


def test_get_body_respects_content_length():
    """
        Test that get_body reads only CONTENT_LENGTH bytes.
    """
    parser = EnvironParser()
    full_content = b"test body content with extra data"
    expected_length = 17
    environ = {
        "wsgi.input": BytesIO(full_content),
        "CONTENT_LENGTH": str(expected_length),
    }
    
    result = parser.get_body(environ)
    
    if len(result) != expected_length:
        errmsg = f"Expected body length {expected_length}, got {len(result)}"
        raise AssertionError(errmsg)
    
    return


def test_get_body_enforces_max_size():
    """
        Test that get_body raises RequestEntityTooLarge when body exceeds max size.
    """
    max_size = 100
    parser = EnvironParser(max_body_size=max_size)
    body_content = b"x" * 200
    environ = {
        "wsgi.input": BytesIO(body_content),
        "CONTENT_LENGTH": str(len(body_content)),
    }
    
    exception_raised = False
    try:
        parser.get_body(environ)
    except RequestEntityTooLarge:
        exception_raised = True
    
    if not exception_raised:
        errmsg = "Expected RequestEntityTooLarge exception"
        raise AssertionError(errmsg)
    
    return



def test_parse_creates_request_object():
    """
        Test that parse creates a Request object with correct values.
    """
    parser = EnvironParser()
    body_content = b"test body"
    environ = {
        "REQUEST_METHOD": "POST",
        "PATH_INFO": "/api/users",
        "QUERY_STRING": "id=1",
        "wsgi.url_scheme": "https",
        "SERVER_NAME": "example.com",
        "SERVER_PORT": "443",
        "CONTENT_TYPE": "application/json",
        "CONTENT_LENGTH": str(len(body_content)),
        "wsgi.input": BytesIO(body_content),
        "HTTP_ACCEPT": "application/json",
    }
    
    result = parser.parse(environ)
    
    if not isinstance(result, Request):
        errmsg = f"Expected Request object, got {type(result)}"
        raise AssertionError(errmsg)
    
    if result.method != "POST":
        errmsg = f"Expected method 'POST', got '{result.method}'"
        raise AssertionError(errmsg)
    
    if result.path != "/api/users":
        errmsg = f"Expected path '/api/users', got '{result.path}'"
        raise AssertionError(errmsg)
    
    if result.query_string != "id=1":
        errmsg = f"Expected query_string 'id=1', got '{result.query_string}'"
        raise AssertionError(errmsg)
    
    if result.scheme != "https":
        errmsg = f"Expected scheme 'https', got '{result.scheme}'"
        raise AssertionError(errmsg)
    
    if result.host != "example.com":
        errmsg = f"Expected host 'example.com', got '{result.host}'"
        raise AssertionError(errmsg)
    
    if result.port != 443:
        errmsg = f"Expected port 443, got {result.port}"
        raise AssertionError(errmsg)
    
    if result.body != body_content:
        errmsg = f"Expected body '{body_content}', got '{result.body}'"
        raise AssertionError(errmsg)
    
    return


def test_set_framework_environ_sets_request():
    """
        Test that set_framework_environ sets the webworks.request key.
    """
    parser = EnvironParser()
    environ: Dict[str, Any] = {}
    
    request = Request(
        method="GET",
        path="/",
        query_string="",
        headers={},
        body=b"",
        scheme="http",
        host="localhost",
        port=80
    )
    
    parser.set_framework_environ(environ, request)
    
    if ENVIRON_REQUEST not in environ:
        errmsg = f"Expected '{ENVIRON_REQUEST}' key in environ"
        raise AssertionError(errmsg)
    
    if environ[ENVIRON_REQUEST] is not request:
        errmsg = "Expected request object in environ"
        raise AssertionError(errmsg)
    
    return


def test_set_framework_environ_sets_route():
    """
        Test that set_framework_environ sets the webworks.route key.
    """
    parser = EnvironParser()
    environ: Dict[str, Any] = {}
    
    request = Request(
        method="GET",
        path="/",
        query_string="",
        headers={},
        body=b"",
        scheme="http",
        host="localhost",
        port=80
    )
    
    route = {"name": "test_route"}
    
    parser.set_framework_environ(environ, request, route=route)
    
    if ENVIRON_ROUTE not in environ:
        errmsg = f"Expected '{ENVIRON_ROUTE}' key in environ"
        raise AssertionError(errmsg)
    
    if environ[ENVIRON_ROUTE] != route:
        errmsg = "Expected route object in environ"
        raise AssertionError(errmsg)
    
    return


def test_set_framework_environ_sets_path_params():
    """
        Test that set_framework_environ sets the webworks.path_params key.
    """
    parser = EnvironParser()
    environ: Dict[str, Any] = {}
    
    request = Request(
        method="GET",
        path="/",
        query_string="",
        headers={},
        body=b"",
        scheme="http",
        host="localhost",
        port=80
    )
    
    path_params = {"id": "123", "name": "test"}
    
    parser.set_framework_environ(environ, request, path_params=path_params)
    
    if ENVIRON_PATH_PARAMS not in environ:
        errmsg = f"Expected '{ENVIRON_PATH_PARAMS}' key in environ"
        raise AssertionError(errmsg)
    
    if environ[ENVIRON_PATH_PARAMS] != path_params:
        errmsg = "Expected path_params object in environ"
        raise AssertionError(errmsg)
    
    return



# =============================================================================
# Property-Based Tests for EnvironParser
# =============================================================================

def test_property_environ_parsing_round_trip():
    """
        Property test: Environ Parsing Round-Trip
        
        For any valid WSGI environ dictionary, parsing the environ into a Request
        object SHALL preserve all values such that they can be reconstructed from
        the Request.
        
        **Feature: wsgi-layer, Property 2: Environ Parsing Round-Trip**
        **Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 2.9, 2.10, 2.11**
    """
    parser = EnvironParser()
    
    # Run 100 iterations with random environ dictionaries
    num_iterations = 100
    
    for iteration in range(num_iterations):
        # Generate random environ
        environ = generate_random_environ()
        
        # Extract expected values before parsing (body read consumes the stream)
        expected = environ_to_request_values(environ)
        
        # Parse environ into Request
        request = parser.parse(environ)
        
        # Verify method is preserved (Requirement 2.1)
        if request.method != expected["method"]:
            errmsg = f"Iteration {iteration}: Method mismatch. Expected '{expected['method']}', got '{request.method}'"
            raise AssertionError(errmsg)
        
        # Verify path is preserved (Requirement 2.2)
        if request.path != expected["path"]:
            errmsg = f"Iteration {iteration}: Path mismatch. Expected '{expected['path']}', got '{request.path}'"
            raise AssertionError(errmsg)
        
        # Verify query string is preserved (Requirement 2.3)
        if request.query_string != expected["query_string"]:
            errmsg = f"Iteration {iteration}: Query string mismatch. Expected '{expected['query_string']}', got '{request.query_string}'"
            raise AssertionError(errmsg)
        
        # Verify scheme is preserved (Requirement 2.8)
        if request.scheme != expected["scheme"]:
            errmsg = f"Iteration {iteration}: Scheme mismatch. Expected '{expected['scheme']}', got '{request.scheme}'"
            raise AssertionError(errmsg)
        
        # Verify host is preserved (Requirement 2.9)
        if request.host != expected["host"]:
            errmsg = f"Iteration {iteration}: Host mismatch. Expected '{expected['host']}', got '{request.host}'"
            raise AssertionError(errmsg)
        
        # Verify port is preserved (Requirement 2.10)
        if request.port != expected["port"]:
            errmsg = f"Iteration {iteration}: Port mismatch. Expected {expected['port']}, got {request.port}"
            raise AssertionError(errmsg)
        
        # Verify body is preserved (Requirement 2.7)
        if request.body != expected["body"]:
            errmsg = f"Iteration {iteration}: Body mismatch. Expected {len(expected['body'])} bytes, got {len(request.body)} bytes"
            raise AssertionError(errmsg)
        
        # Verify headers are preserved (Requirements 2.4, 2.5, 2.6)
        for header_name, header_value in expected["headers"].items():
            if header_name not in request.headers:
                errmsg = f"Iteration {iteration}: Missing header '{header_name}'"
                raise AssertionError(errmsg)
            
            if request.headers[header_name] != header_value:
                errmsg = f"Iteration {iteration}: Header '{header_name}' mismatch. Expected '{header_value}', got '{request.headers[header_name]}'"
                raise AssertionError(errmsg)
        
        # Verify content type is preserved (Requirement 2.5)
        if expected["content_type"] is not None:
            if request.content_type != expected["content_type"]:
                errmsg = f"Iteration {iteration}: Content-Type mismatch. Expected '{expected['content_type']}', got '{request.content_type}'"
                raise AssertionError(errmsg)
        
        # Verify content length is preserved (Requirement 2.6)
        if expected["content_length"] is not None:
            if request.content_length != expected["content_length"]:
                errmsg = f"Iteration {iteration}: Content-Length mismatch. Expected {expected['content_length']}, got {request.content_length}"
                raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for Framework Environ Extensions
# =============================================================================

def test_get_framework_environ_with_full_key():
    """
        Test that get_framework_environ retrieves value with full key name.
    """
    parser = EnvironParser()
    environ: Dict[str, Any] = {
        "webworks.request": "test_request",
        "webworks.custom": "custom_value",
    }
    
    result = parser.get_framework_environ(environ, "webworks.request")
    
    expected = "test_request"
    if result != expected:
        errmsg = f"Expected '{expected}', got '{result}'"
        raise AssertionError(errmsg)
    
    return


def test_get_framework_environ_with_short_key():
    """
        Test that get_framework_environ retrieves value with short key name.
    """
    parser = EnvironParser()
    environ: Dict[str, Any] = {
        "webworks.request": "test_request",
    }
    
    result = parser.get_framework_environ(environ, "request")
    
    expected = "test_request"
    if result != expected:
        errmsg = f"Expected '{expected}', got '{result}'"
        raise AssertionError(errmsg)
    
    return


def test_get_framework_environ_returns_default():
    """
        Test that get_framework_environ returns default when key not found.
    """
    parser = EnvironParser()
    environ: Dict[str, Any] = {}
    
    result = parser.get_framework_environ(environ, "missing", default="default_value")
    
    expected = "default_value"
    if result != expected:
        errmsg = f"Expected '{expected}', got '{result}'"
        raise AssertionError(errmsg)
    
    return


def test_get_custom_environ_keys_returns_matching_keys():
    """
        Test that get_custom_environ_keys returns all keys in namespace.
    """
    parser = EnvironParser()
    environ: Dict[str, Any] = {
        "webworks.request": "request_obj",
        "webworks.route": "route_obj",
        "webworks.custom": "custom_value",
        "REQUEST_METHOD": "GET",
        "other.key": "other_value",
    }
    
    result = parser.get_custom_environ_keys(environ, "webworks")
    
    if len(result) != 3:
        errmsg = f"Expected 3 keys, got {len(result)}"
        raise AssertionError(errmsg)
    
    if "webworks.request" not in result:
        errmsg = "Expected 'webworks.request' in result"
        raise AssertionError(errmsg)
    
    if "webworks.route" not in result:
        errmsg = "Expected 'webworks.route' in result"
        raise AssertionError(errmsg)
    
    if "webworks.custom" not in result:
        errmsg = "Expected 'webworks.custom' in result"
        raise AssertionError(errmsg)
    
    return


def test_get_custom_environ_keys_with_different_namespace():
    """
        Test that get_custom_environ_keys filters by namespace.
    """
    parser = EnvironParser()
    environ: Dict[str, Any] = {
        "webworks.request": "request_obj",
        "myapp.setting": "setting_value",
        "myapp.config": "config_value",
    }
    
    result = parser.get_custom_environ_keys(environ, "myapp")
    
    if len(result) != 2:
        errmsg = f"Expected 2 keys, got {len(result)}"
        raise AssertionError(errmsg)
    
    if "myapp.setting" not in result:
        errmsg = "Expected 'myapp.setting' in result"
        raise AssertionError(errmsg)
    
    if "myapp.config" not in result:
        errmsg = "Expected 'myapp.config' in result"
        raise AssertionError(errmsg)
    
    return


def test_is_standard_wsgi_key_for_cgi_variables():
    """
        Test that is_standard_wsgi_key returns True for CGI variables.
    """
    parser = EnvironParser()
    
    cgi_keys = [
        "REQUEST_METHOD", "SCRIPT_NAME", "PATH_INFO", "QUERY_STRING",
        "CONTENT_TYPE", "CONTENT_LENGTH", "SERVER_NAME", "SERVER_PORT",
    ]
    
    for key in cgi_keys:
        result = parser.is_standard_wsgi_key(key)
        if not result:
            errmsg = f"Expected '{key}' to be a standard WSGI key"
            raise AssertionError(errmsg)
    
    return


def test_is_standard_wsgi_key_for_http_headers():
    """
        Test that is_standard_wsgi_key returns True for HTTP_* headers.
    """
    parser = EnvironParser()
    
    http_keys = ["HTTP_ACCEPT", "HTTP_USER_AGENT", "HTTP_X_CUSTOM"]
    
    for key in http_keys:
        result = parser.is_standard_wsgi_key(key)
        if not result:
            errmsg = f"Expected '{key}' to be a standard WSGI key"
            raise AssertionError(errmsg)
    
    return


def test_is_standard_wsgi_key_for_wsgi_keys():
    """
        Test that is_standard_wsgi_key returns True for wsgi.* keys.
    """
    parser = EnvironParser()
    
    wsgi_keys = ["wsgi.input", "wsgi.errors", "wsgi.url_scheme", "wsgi.multithread"]
    
    for key in wsgi_keys:
        result = parser.is_standard_wsgi_key(key)
        if not result:
            errmsg = f"Expected '{key}' to be a standard WSGI key"
            raise AssertionError(errmsg)
    
    return


def test_is_standard_wsgi_key_for_custom_keys():
    """
        Test that is_standard_wsgi_key returns False for custom keys.
    """
    parser = EnvironParser()
    
    custom_keys = ["webworks.request", "myapp.setting", "custom_key"]
    
    for key in custom_keys:
        result = parser.is_standard_wsgi_key(key)
        if result:
            errmsg = f"Expected '{key}' to NOT be a standard WSGI key"
            raise AssertionError(errmsg)
    
    return


def test_set_framework_environ_preserves_existing_keys():
    """
        Test that set_framework_environ preserves existing environ keys.
    """
    parser = EnvironParser()
    environ: Dict[str, Any] = {
        "REQUEST_METHOD": "GET",
        "PATH_INFO": "/test",
        "HTTP_ACCEPT": "application/json",
        "wsgi.url_scheme": "http",
        "custom.middleware.key": "middleware_value",
    }
    
    request = Request(
        method="GET",
        path="/test",
        query_string="",
        headers={},
        body=b"",
        scheme="http",
        host="localhost",
        port=80
    )
    
    parser.set_framework_environ(environ, request)
    
    # Verify standard WSGI keys are preserved
    if environ.get("REQUEST_METHOD") != "GET":
        errmsg = "REQUEST_METHOD was modified"
        raise AssertionError(errmsg)
    
    if environ.get("PATH_INFO") != "/test":
        errmsg = "PATH_INFO was modified"
        raise AssertionError(errmsg)
    
    if environ.get("HTTP_ACCEPT") != "application/json":
        errmsg = "HTTP_ACCEPT was modified"
        raise AssertionError(errmsg)
    
    if environ.get("wsgi.url_scheme") != "http":
        errmsg = "wsgi.url_scheme was modified"
        raise AssertionError(errmsg)
    
    # Verify custom middleware keys are preserved
    if environ.get("custom.middleware.key") != "middleware_value":
        errmsg = "custom.middleware.key was modified"
        raise AssertionError(errmsg)
    
    # Verify framework keys were set
    if environ.get(ENVIRON_REQUEST) is not request:
        errmsg = "webworks.request was not set correctly"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Property-Based Tests for Framework Environ Extensions
# =============================================================================

def generate_random_route() -> Dict[str, Any]:
    """
        Generate a random route object.
    """
    route_names = ["home", "users", "api_endpoint", "dashboard", "settings"]
    methods = ["GET", "POST", "PUT", "DELETE"]
    
    rtnval = {
        "name": random.choice(route_names),
        "method": random.choice(methods),
        "pattern": "/" + generate_random_string(3, 15),
    }
    return rtnval


def generate_random_path_params() -> Dict[str, Any]:
    """
        Generate random path parameters.
    """
    num_params = random.randint(0, 5)
    rtnval: Dict[str, Any] = {}
    
    for _ in range(num_params):
        key = generate_random_string(3, 10)
        # Mix of string and integer values
        if random.random() < 0.5:
            value = generate_random_string(1, 20)
        else:
            value = random.randint(1, 10000)
        rtnval[key] = value
    
    return rtnval


def generate_random_custom_environ_keys() -> Dict[str, Any]:
    """
        Generate random custom environ keys from middleware.
    """
    num_keys = random.randint(0, 5)
    rtnval: Dict[str, Any] = {}
    
    namespaces = ["middleware", "auth", "cache", "session", "custom"]
    
    for _ in range(num_keys):
        namespace = random.choice(namespaces)
        key_name = generate_random_string(3, 15)
        full_key = f"{namespace}.{key_name}"
        
        # Mix of value types
        value_type = random.choice(["string", "int", "bool", "dict"])
        if value_type == "string":
            value = generate_random_string(1, 50)
        elif value_type == "int":
            value = random.randint(1, 10000)
        elif value_type == "bool":
            value = random.choice([True, False])
        else:
            value = {"nested": generate_random_string(1, 20)}
        
        rtnval[full_key] = value
    
    return rtnval


def test_property_framework_environ_extensions():
    """
        Property test: Framework Environ Extensions
        
        For any request processed by the application, the environ dictionary
        SHALL contain webworks.request with the Request object, and after
        routing, SHALL contain webworks.route and webworks.path_params with
        the matched route information. Standard WSGI keys and custom middleware
        keys SHALL be preserved.
        
        **Feature: wsgi-layer, Property 10: Framework Environ Extensions**
        **Validates: Requirements 9.1, 9.2, 9.3, 9.4, 9.5, 9.6**
    """
    parser = EnvironParser()
    
    # Run 100 iterations with random data
    num_iterations = 100
    
    for iteration in range(num_iterations):
        # Generate random environ with standard WSGI keys
        environ = generate_random_environ()
        
        # Add random custom middleware keys
        custom_keys = generate_random_custom_environ_keys()
        for key, value in custom_keys.items():
            environ[key] = value
        
        # Store original standard WSGI keys for verification
        original_standard_keys: Dict[str, Any] = {}
        for key, value in environ.items():
            if parser.is_standard_wsgi_key(key):
                original_standard_keys[key] = value
        
        # Store original custom keys for verification
        original_custom_keys = custom_keys.copy()
        
        # Parse environ into Request
        wsgi_input = environ.get("wsgi.input")
        if wsgi_input is not None:
            wsgi_input.seek(0)
        
        request = parser.parse(environ)
        
        # Reset wsgi.input for verification
        if wsgi_input is not None:
            wsgi_input.seek(0)
        
        # Generate random route and path params
        route = generate_random_route() if random.random() > 0.3 else None
        path_params = generate_random_path_params() if random.random() > 0.3 else None
        
        # Set framework environ
        parser.set_framework_environ(environ, request, route=route, path_params=path_params)
        
        # Verify webworks.request is set (Requirement 9.2)
        if ENVIRON_REQUEST not in environ:
            errmsg = f"Iteration {iteration}: webworks.request not set in environ"
            raise AssertionError(errmsg)
        
        if environ[ENVIRON_REQUEST] is not request:
            errmsg = f"Iteration {iteration}: webworks.request does not match request object"
            raise AssertionError(errmsg)
        
        # Verify webworks.route is set when provided (Requirement 9.3)
        if route is not None:
            if ENVIRON_ROUTE not in environ:
                errmsg = f"Iteration {iteration}: webworks.route not set when route provided"
                raise AssertionError(errmsg)
            
            if environ[ENVIRON_ROUTE] != route:
                errmsg = f"Iteration {iteration}: webworks.route does not match route object"
                raise AssertionError(errmsg)
        
        # Verify webworks.path_params is set (Requirement 9.4)
        if ENVIRON_PATH_PARAMS not in environ:
            errmsg = f"Iteration {iteration}: webworks.path_params not set in environ"
            raise AssertionError(errmsg)
        
        if path_params is not None:
            if environ[ENVIRON_PATH_PARAMS] != path_params:
                errmsg = f"Iteration {iteration}: webworks.path_params does not match"
                raise AssertionError(errmsg)
        else:
            if environ[ENVIRON_PATH_PARAMS] != {}:
                errmsg = f"Iteration {iteration}: webworks.path_params should be empty dict when not provided"
                raise AssertionError(errmsg)
        
        # Verify custom middleware keys are preserved (Requirements 9.1, 9.5)
        for key, value in original_custom_keys.items():
            if key not in environ:
                errmsg = f"Iteration {iteration}: Custom key '{key}' was removed"
                raise AssertionError(errmsg)
            
            if environ[key] != value:
                errmsg = f"Iteration {iteration}: Custom key '{key}' was modified"
                raise AssertionError(errmsg)
        
        # Verify standard WSGI keys are preserved (Requirement 9.6)
        for key, value in original_standard_keys.items():
            if key not in environ:
                errmsg = f"Iteration {iteration}: Standard WSGI key '{key}' was removed"
                raise AssertionError(errmsg)
            
            # Special handling for wsgi.input which may have been read
            if key == "wsgi.input":
                continue
            
            if environ[key] != value:
                errmsg = f"Iteration {iteration}: Standard WSGI key '{key}' was modified"
                raise AssertionError(errmsg)
        
        # Verify get_framework_environ works correctly
        retrieved_request = parser.get_framework_environ(environ, "request")
        if retrieved_request is not request:
            errmsg = f"Iteration {iteration}: get_framework_environ did not retrieve request correctly"
            raise AssertionError(errmsg)
        
        # Verify get_custom_environ_keys returns framework keys
        framework_keys = parser.get_custom_environ_keys(environ, "webworks")
        if ENVIRON_REQUEST not in framework_keys:
            errmsg = f"Iteration {iteration}: get_custom_environ_keys did not return webworks.request"
            raise AssertionError(errmsg)
    
    return
