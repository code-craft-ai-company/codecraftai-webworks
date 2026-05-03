"""
    Tests for the Request class.
    
    This module contains unit tests for the Request class which provides
    an abstraction over WSGI/ASGI request objects.
"""

import io
import json
from typing import Any, Dict

from automojo.webworks.authentication.core import (
    AuthenticationContext,
    Principal,
)
from automojo.webworks.routing.request import Request
from automojo.webworks.routing.headers import Headers
from automojo.webworks.routing.queryparams import QueryParams


# =============================================================================
# Unit Tests for Request - Core Properties
# =============================================================================

def test_request_method_returns_uppercase():
    """
        Test that method property returns uppercase HTTP method.
    """
    request = Request(method="get", path="/")
    
    result = request.method
    
    expected = "GET"
    if result != expected:
        errmsg = f"Expected '{expected}', got '{result}'"
        raise AssertionError(errmsg)
    
    return


def test_request_path_returns_path():
    """
        Test that path property returns the request path.
    """
    request = Request(method="GET", path="/api/users")
    
    result = request.path
    
    expected = "/api/users"
    if result != expected:
        errmsg = f"Expected '{expected}', got '{result}'"
        raise AssertionError(errmsg)
    
    return


def test_request_query_params_returns_queryparams():
    """
        Test that query_params property returns QueryParams instance.
    """
    request = Request(method="GET", path="/", query_string=b"foo=bar&baz=qux")
    
    result = request.query_params
    
    if not isinstance(result, QueryParams):
        errmsg = f"Expected QueryParams instance, got {type(result)}"
        raise AssertionError(errmsg)
    
    if result.get("foo") != "bar":
        errmsg = f"Expected 'bar', got '{result.get('foo')}'"
        raise AssertionError(errmsg)
    
    return


def test_request_headers_returns_headers():
    """
        Test that headers property returns Headers instance.
    """
    request = Request(
        method="GET",
        path="/",
        headers={"Content-Type": "application/json"}
    )
    
    result = request.headers
    
    if not isinstance(result, Headers):
        errmsg = f"Expected Headers instance, got {type(result)}"
        raise AssertionError(errmsg)
    
    if result.get("Content-Type") != "application/json":
        errmsg = f"Expected 'application/json', got '{result.get('Content-Type')}'"
        raise AssertionError(errmsg)
    
    return


def test_request_body_returns_bytes():
    """
        Test that body property returns request body as bytes.
    """
    body_content = b'{"key": "value"}'
    request = Request(method="POST", path="/", body=body_content)
    
    result = request.body
    
    if result != body_content:
        errmsg = f"Expected {body_content}, got {result}"
        raise AssertionError(errmsg)
    
    return


def test_request_cookies_parses_cookie_header():
    """
        Test that cookies property parses Cookie header.
    """
    request = Request(
        method="GET",
        path="/",
        headers={"Cookie": "session=abc123; user=john"}
    )
    
    result = request.cookies
    
    if result.get("session") != "abc123":
        errmsg = f"Expected 'abc123', got '{result.get('session')}'"
        raise AssertionError(errmsg)
    
    if result.get("user") != "john":
        errmsg = f"Expected 'john', got '{result.get('user')}'"
        raise AssertionError(errmsg)
    
    return


def test_request_cookies_returns_empty_dict_when_no_cookie():
    """
        Test that cookies returns empty dict when no Cookie header.
    """
    request = Request(method="GET", path="/")
    
    result = request.cookies
    
    if result != {}:
        errmsg = f"Expected empty dict, got {result}"
        raise AssertionError(errmsg)
    
    return


def test_request_url_builds_full_url():
    """
        Test that url property builds full URL.
    """
    request = Request(
        method="GET",
        path="/api/users",
        query_string=b"page=1",
        scheme="https",
        host="example.com",
        port=443
    )
    
    result = request.url
    
    expected = "https://example.com/api/users?page=1"
    if result != expected:
        errmsg = f"Expected '{expected}', got '{result}'"
        raise AssertionError(errmsg)
    
    return


def test_request_url_includes_port_when_non_standard():
    """
        Test that url includes port when non-standard.
    """
    request = Request(
        method="GET",
        path="/",
        scheme="http",
        host="localhost",
        port=8080
    )
    
    result = request.url
    
    expected = "http://localhost:8080/"
    if result != expected:
        errmsg = f"Expected '{expected}', got '{result}'"
        raise AssertionError(errmsg)
    
    return


def test_request_url_omits_standard_http_port():
    """
        Test that url omits standard HTTP port 80.
    """
    request = Request(
        method="GET",
        path="/",
        scheme="http",
        host="example.com",
        port=80
    )
    
    result = request.url
    
    expected = "http://example.com/"
    if result != expected:
        errmsg = f"Expected '{expected}', got '{result}'"
        raise AssertionError(errmsg)
    
    return


def test_request_url_omits_standard_https_port():
    """
        Test that url omits standard HTTPS port 443.
    """
    request = Request(
        method="GET",
        path="/",
        scheme="https",
        host="example.com",
        port=443
    )
    
    result = request.url
    
    expected = "https://example.com/"
    if result != expected:
        errmsg = f"Expected '{expected}', got '{result}'"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for Request - Path Parameters
# =============================================================================

def test_request_path_params_initially_empty():
    """
        Test that path_params is initially empty.
    """
    request = Request(method="GET", path="/users/123")
    
    result = request.path_params
    
    if result != {}:
        errmsg = f"Expected empty dict, got {result}"
        raise AssertionError(errmsg)
    
    return


def test_request_path_params_can_be_set():
    """
        Test that path_params can be set.
    """
    request = Request(method="GET", path="/users/123")
    
    request.path_params = {"id": 123}
    
    result = request.path_params
    expected = {"id": 123}
    if result != expected:
        errmsg = f"Expected {expected}, got {result}"
        raise AssertionError(errmsg)
    
    return


def test_request_path_params_mutable():
    """
        Test that path_params is mutable.
    """
    request = Request(method="GET", path="/users/123/posts/456")
    
    request.path_params = {"user_id": 123}
    request.path_params["post_id"] = 456
    
    result = request.path_params
    expected = {"user_id": 123, "post_id": 456}
    if result != expected:
        errmsg = f"Expected {expected}, got {result}"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for Request - JSON Parsing
# =============================================================================

def test_request_json_parses_valid_json():
    """
        Test that json() parses valid JSON body.
    """
    body = b'{"name": "John", "age": 30}'
    request = Request(method="POST", path="/", body=body)
    
    result = request.json()
    
    expected = {"name": "John", "age": 30}
    if result != expected:
        errmsg = f"Expected {expected}, got {result}"
        raise AssertionError(errmsg)
    
    return


def test_request_json_parses_array():
    """
        Test that json() parses JSON array.
    """
    body = b'[1, 2, 3]'
    request = Request(method="POST", path="/", body=body)
    
    result = request.json()
    
    expected = [1, 2, 3]
    if result != expected:
        errmsg = f"Expected {expected}, got {result}"
        raise AssertionError(errmsg)
    
    return


def test_request_json_raises_on_invalid_json():
    """
        Test that json() raises on invalid JSON.
    """
    body = b'not valid json'
    request = Request(method="POST", path="/", body=body)
    
    try:
        request.json()
        errmsg = "Expected JSONDecodeError for invalid JSON"
        raise AssertionError(errmsg)
    except json.JSONDecodeError:
        pass
    
    return


def test_request_json_handles_empty_body():
    """
        Test that json() raises on empty body.
    """
    request = Request(method="POST", path="/", body=b"")
    
    try:
        request.json()
        errmsg = "Expected JSONDecodeError for empty body"
        raise AssertionError(errmsg)
    except json.JSONDecodeError:
        pass
    
    return


# =============================================================================
# Unit Tests for Request - Form Parsing
# =============================================================================

def test_request_form_parses_form_data():
    """
        Test that form() parses form-encoded body.
    """
    body = b"name=John&email=john%40example.com"
    request = Request(method="POST", path="/", body=body)
    
    result = request.form()
    
    expected = {"name": "John", "email": "john@example.com"}
    if result != expected:
        errmsg = f"Expected {expected}, got {result}"
        raise AssertionError(errmsg)
    
    return


def test_request_form_handles_empty_body():
    """
        Test that form() handles empty body.
    """
    request = Request(method="POST", path="/", body=b"")
    
    result = request.form()
    
    expected = {}
    if result != expected:
        errmsg = f"Expected {expected}, got {result}"
        raise AssertionError(errmsg)
    
    return


def test_request_form_handles_blank_values():
    """
        Test that form() handles blank values.
    """
    body = b"name=&email=test"
    request = Request(method="POST", path="/", body=body)
    
    result = request.form()
    
    expected = {"name": "", "email": "test"}
    if result != expected:
        errmsg = f"Expected {expected}, got {result}"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for Request - from_wsgi()
# =============================================================================

def test_request_from_wsgi_extracts_method():
    """
        Test that from_wsgi() extracts HTTP method.
    """
    environ = {
        "REQUEST_METHOD": "POST",
        "PATH_INFO": "/",
    }
    
    request = Request.from_wsgi(environ)
    
    result = request.method
    expected = "POST"
    if result != expected:
        errmsg = f"Expected '{expected}', got '{result}'"
        raise AssertionError(errmsg)
    
    return


def test_request_from_wsgi_extracts_path():
    """
        Test that from_wsgi() extracts path.
    """
    environ = {
        "REQUEST_METHOD": "GET",
        "PATH_INFO": "/api/users",
    }
    
    request = Request.from_wsgi(environ)
    
    result = request.path
    expected = "/api/users"
    if result != expected:
        errmsg = f"Expected '{expected}', got '{result}'"
        raise AssertionError(errmsg)
    
    return


def test_request_from_wsgi_extracts_query_string():
    """
        Test that from_wsgi() extracts query string.
    """
    environ = {
        "REQUEST_METHOD": "GET",
        "PATH_INFO": "/",
        "QUERY_STRING": "foo=bar",
    }
    
    request = Request.from_wsgi(environ)
    
    result = request.query_params.get("foo")
    expected = "bar"
    if result != expected:
        errmsg = f"Expected '{expected}', got '{result}'"
        raise AssertionError(errmsg)
    
    return


def test_request_from_wsgi_extracts_headers():
    """
        Test that from_wsgi() extracts headers.
    """
    environ = {
        "REQUEST_METHOD": "GET",
        "PATH_INFO": "/",
        "HTTP_ACCEPT": "application/json",
        "HTTP_X_CUSTOM_HEADER": "custom-value",
    }
    
    request = Request.from_wsgi(environ)
    
    accept = request.headers.get("Accept")
    if accept != "application/json":
        errmsg = f"Expected 'application/json', got '{accept}'"
        raise AssertionError(errmsg)
    
    custom = request.headers.get("X-Custom-Header")
    if custom != "custom-value":
        errmsg = f"Expected 'custom-value', got '{custom}'"
        raise AssertionError(errmsg)
    
    return


def test_request_from_wsgi_extracts_content_type():
    """
        Test that from_wsgi() extracts Content-Type header.
    """
    environ = {
        "REQUEST_METHOD": "POST",
        "PATH_INFO": "/",
        "CONTENT_TYPE": "application/json",
    }
    
    request = Request.from_wsgi(environ)
    
    result = request.headers.get("Content-Type")
    expected = "application/json"
    if result != expected:
        errmsg = f"Expected '{expected}', got '{result}'"
        raise AssertionError(errmsg)
    
    return


def test_request_from_wsgi_extracts_body():
    """
        Test that from_wsgi() extracts body from wsgi.input.
    """
    body_content = b'{"key": "value"}'
    environ = {
        "REQUEST_METHOD": "POST",
        "PATH_INFO": "/",
        "CONTENT_LENGTH": str(len(body_content)),
        "wsgi.input": io.BytesIO(body_content),
    }
    
    request = Request.from_wsgi(environ)
    
    result = request.body
    if result != body_content:
        errmsg = f"Expected {body_content}, got {result}"
        raise AssertionError(errmsg)
    
    return


def test_request_from_wsgi_extracts_scheme():
    """
        Test that from_wsgi() extracts URL scheme.
    """
    environ = {
        "REQUEST_METHOD": "GET",
        "PATH_INFO": "/",
        "wsgi.url_scheme": "https",
    }
    
    request = Request.from_wsgi(environ)
    
    if "https://" not in request.url:
        errmsg = f"Expected 'https://' in URL, got '{request.url}'"
        raise AssertionError(errmsg)
    
    return


def test_request_from_wsgi_extracts_host_and_port():
    """
        Test that from_wsgi() extracts host and port.
    """
    environ = {
        "REQUEST_METHOD": "GET",
        "PATH_INFO": "/",
        "SERVER_NAME": "example.com",
        "SERVER_PORT": "8080",
        "wsgi.url_scheme": "http",
    }
    
    request = Request.from_wsgi(environ)
    
    expected = "http://example.com:8080/"
    if request.url != expected:
        errmsg = f"Expected '{expected}', got '{request.url}'"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for Request - from_asgi()
# =============================================================================

def test_request_from_asgi_extracts_method():
    """
        Test that from_asgi() extracts HTTP method.
    """
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/",
        "headers": [],
    }
    
    request = Request.from_asgi(scope)
    
    result = request.method
    expected = "POST"
    if result != expected:
        errmsg = f"Expected '{expected}', got '{result}'"
        raise AssertionError(errmsg)
    
    return


def test_request_from_asgi_extracts_path():
    """
        Test that from_asgi() extracts path.
    """
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/api/users",
        "headers": [],
    }
    
    request = Request.from_asgi(scope)
    
    result = request.path
    expected = "/api/users"
    if result != expected:
        errmsg = f"Expected '{expected}', got '{result}'"
        raise AssertionError(errmsg)
    
    return


def test_request_from_asgi_extracts_query_string():
    """
        Test that from_asgi() extracts query string.
    """
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "query_string": b"foo=bar",
        "headers": [],
    }
    
    request = Request.from_asgi(scope)
    
    result = request.query_params.get("foo")
    expected = "bar"
    if result != expected:
        errmsg = f"Expected '{expected}', got '{result}'"
        raise AssertionError(errmsg)
    
    return


def test_request_from_asgi_extracts_headers():
    """
        Test that from_asgi() extracts headers from bytes pairs.
    """
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "headers": [
            (b"accept", b"application/json"),
            (b"x-custom-header", b"custom-value"),
        ],
    }
    
    request = Request.from_asgi(scope)
    
    accept = request.headers.get("accept")
    if accept != "application/json":
        errmsg = f"Expected 'application/json', got '{accept}'"
        raise AssertionError(errmsg)
    
    custom = request.headers.get("x-custom-header")
    if custom != "custom-value":
        errmsg = f"Expected 'custom-value', got '{custom}'"
        raise AssertionError(errmsg)
    
    return


def test_request_from_asgi_extracts_body():
    """
        Test that from_asgi() uses provided body.
    """
    body_content = b'{"key": "value"}'
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/",
        "headers": [],
    }
    
    request = Request.from_asgi(scope, body=body_content)
    
    result = request.body
    if result != body_content:
        errmsg = f"Expected {body_content}, got {result}"
        raise AssertionError(errmsg)
    
    return


def test_request_from_asgi_extracts_scheme():
    """
        Test that from_asgi() extracts URL scheme.
    """
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "scheme": "https",
        "headers": [],
    }
    
    request = Request.from_asgi(scope)
    
    if "https://" not in request.url:
        errmsg = f"Expected 'https://' in URL, got '{request.url}'"
        raise AssertionError(errmsg)
    
    return


def test_request_from_asgi_extracts_server():
    """
        Test that from_asgi() extracts server host and port.
    """
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "scheme": "http",
        "server": ("example.com", 8080),
        "headers": [],
    }
    
    request = Request.from_asgi(scope)
    
    expected = "http://example.com:8080/"
    if request.url != expected:
        errmsg = f"Expected '{expected}', got '{request.url}'"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for Request - Edge Cases
# =============================================================================

def test_request_repr_shows_method_and_path():
    """
        Test that __repr__ shows method and path.
    """
    request = Request(method="GET", path="/api/users")
    
    result = repr(request)
    
    if "GET" not in result:
        errmsg = f"Expected 'GET' in repr, got '{result}'"
        raise AssertionError(errmsg)
    
    if "/api/users" not in result:
        errmsg = f"Expected '/api/users' in repr, got '{result}'"
        raise AssertionError(errmsg)
    
    return


def test_request_default_values():
    """
        Test that Request has sensible defaults.
    """
    request = Request(method="GET", path="/")
    
    if request.body != b"":
        errmsg = f"Expected empty body, got {request.body}"
        raise AssertionError(errmsg)
    
    if len(request.headers) != 0:
        errmsg = f"Expected no headers, got {len(request.headers)}"
        raise AssertionError(errmsg)
    
    if len(request.query_params) != 0:
        errmsg = f"Expected no query params, got {len(request.query_params)}"
        raise AssertionError(errmsg)
    
    return


def test_request_from_wsgi_handles_missing_values():
    """
        Test that from_wsgi() handles missing environ values.
    """
    environ = {}
    
    request = Request.from_wsgi(environ)
    
    if request.method != "GET":
        errmsg = f"Expected 'GET' default method, got '{request.method}'"
        raise AssertionError(errmsg)
    
    if request.path != "/":
        errmsg = f"Expected '/' default path, got '{request.path}'"
        raise AssertionError(errmsg)
    
    return


def test_request_from_asgi_handles_missing_values():
    """
        Test that from_asgi() handles missing scope values.
    """
    scope = {}
    
    request = Request.from_asgi(scope)
    
    if request.method != "GET":
        errmsg = f"Expected 'GET' default method, got '{request.method}'"
        raise AssertionError(errmsg)
    
    if request.path != "/":
        errmsg = f"Expected '/' default path, got '{request.path}'"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Property Tests
# =============================================================================

import random
import string
from urllib.parse import urlencode, parse_qs


def _random_string(length: int = 8) -> str:
    """Generate a random alphanumeric string."""
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))


def _random_key() -> str:
    """Generate a random parameter key (alphanumeric, starting with letter)."""
    first_char = random.choice(string.ascii_lowercase)
    rest = ''.join(random.choices(string.ascii_lowercase + string.digits + '_', k=random.randint(2, 10)))
    return first_char + rest


def _random_value() -> str:
    """Generate a random parameter value."""
    # Include various characters that need URL encoding
    chars = string.ascii_letters + string.digits + ' -_.~'
    length = random.randint(1, 20)
    return ''.join(random.choices(chars, k=length))


def _generate_single_value_params(num_params: int) -> dict:
    """Generate a dict of random single-value parameters."""
    params = {}
    for _ in range(num_params):
        key = _random_key()
        # Ensure unique keys
        while key in params:
            key = _random_key()
        params[key] = _random_value()
    return params


# -----------------------------------------------------------------------------
# Property 4: Request Query/Form Parsing Round-Trip
# **Validates: Requirements 3.3, 3.7**
#
# *For any* valid query string or form-encoded body, parsing SHALL produce a
# dict where each key maps to its value(s), and the original data can be
# reconstructed from the parsed result (round-trip for single-value keys).
# -----------------------------------------------------------------------------

def test_property_query_params_round_trip():
    """
    Property 4: Request Query/Form Parsing - Query String Round-Trip
    
    For any valid query string with single-value keys, parsing via query_params
    and reconstructing via urlencode should produce an equivalent query string
    that parses to the same values.
    
    **Feature: router-request-handling, Property 4: Request Query/Form Parsing**
    **Validates: Requirements 3.3, 3.7**
    """
    # Run 100 iterations
    for _ in range(100):
        # Generate random parameters (1-5 params)
        num_params = random.randint(1, 5)
        original_params = _generate_single_value_params(num_params)
        
        # Encode to query string
        query_string = urlencode(original_params)
        query_bytes = query_string.encode('utf-8')
        
        # Create request and parse query params
        request = Request(method="GET", path="/", query_string=query_bytes)
        
        # Extract parsed values
        parsed_params = dict(request.query_params.items())
        
        # Property: All original keys should be present
        for key in original_params:
            if key not in parsed_params:
                errmsg = f"Key '{key}' missing from parsed params"
                raise AssertionError(errmsg)
        
        # Property: All parsed values should match original values
        for key, value in original_params.items():
            parsed_value = parsed_params.get(key)
            if parsed_value != value:
                errmsg = f"Value mismatch for key '{key}': expected '{value}', got '{parsed_value}'"
                raise AssertionError(errmsg)
        
        # Property: Round-trip - re-encode and re-parse should give same result
        reconstructed_query = urlencode(parsed_params)
        reconstructed_bytes = reconstructed_query.encode('utf-8')
        
        request2 = Request(method="GET", path="/", query_string=reconstructed_bytes)
        reparsed_params = dict(request2.query_params.items())
        
        if reparsed_params != parsed_params:
            errmsg = f"Round-trip failed: original={parsed_params}, reparsed={reparsed_params}"
            raise AssertionError(errmsg)
    
    return


def test_property_form_parsing_round_trip():
    """
    Property 4: Request Query/Form Parsing - Form Data Round-Trip
    
    For any valid form-encoded body with single-value keys, parsing via form()
    and reconstructing via urlencode should produce an equivalent body that
    parses to the same values.
    
    **Feature: router-request-handling, Property 4: Request Query/Form Parsing**
    **Validates: Requirements 3.3, 3.7**
    """
    # Run 100 iterations
    for _ in range(100):
        # Generate random parameters (1-5 params)
        num_params = random.randint(1, 5)
        original_params = _generate_single_value_params(num_params)
        
        # Encode to form body
        form_body = urlencode(original_params)
        form_bytes = form_body.encode('utf-8')
        
        # Create request and parse form data
        request = Request(method="POST", path="/", body=form_bytes)
        
        # Extract parsed values
        parsed_params = request.form()
        
        # Property: All original keys should be present
        for key in original_params:
            if key not in parsed_params:
                errmsg = f"Key '{key}' missing from parsed form data"
                raise AssertionError(errmsg)
        
        # Property: All parsed values should match original values
        for key, value in original_params.items():
            parsed_value = parsed_params.get(key)
            if parsed_value != value:
                errmsg = f"Value mismatch for key '{key}': expected '{value}', got '{parsed_value}'"
                raise AssertionError(errmsg)
        
        # Property: Round-trip - re-encode and re-parse should give same result
        reconstructed_body = urlencode(parsed_params)
        reconstructed_bytes = reconstructed_body.encode('utf-8')
        
        request2 = Request(method="POST", path="/", body=reconstructed_bytes)
        reparsed_params = request2.form()
        
        if reparsed_params != parsed_params:
            errmsg = f"Round-trip failed: original={parsed_params}, reparsed={reparsed_params}"
            raise AssertionError(errmsg)
    
    return


def test_property_query_form_equivalence():
    """
    Property 4: Request Query/Form Parsing - Query and Form Equivalence
    
    For any valid parameter set, parsing the same data as query string or
    form body should produce equivalent results.
    
    **Feature: router-request-handling, Property 4: Request Query/Form Parsing**
    **Validates: Requirements 3.3, 3.7**
    """
    # Run 100 iterations
    for _ in range(100):
        # Generate random parameters (1-5 params)
        num_params = random.randint(1, 5)
        original_params = _generate_single_value_params(num_params)
        
        # Encode to query string / form body (same format)
        encoded_data = urlencode(original_params)
        encoded_bytes = encoded_data.encode('utf-8')
        
        # Parse as query string
        request_query = Request(method="GET", path="/", query_string=encoded_bytes)
        query_parsed = dict(request_query.query_params.items())
        
        # Parse as form body
        request_form = Request(method="POST", path="/", body=encoded_bytes)
        form_parsed = request_form.form()
        
        # Property: Both parsing methods should produce equivalent results
        if query_parsed != form_parsed:
            errmsg = f"Query and form parsing differ: query={query_parsed}, form={form_parsed}"
            raise AssertionError(errmsg)
    
    return


# -----------------------------------------------------------------------------
# Property 5: Request JSON Round-Trip
# **Validates: Requirements 3.6**
#
# *For any* valid JSON body, calling `request.json()` SHALL return a Python
# object that, when serialized back to JSON, produces equivalent JSON content.
# -----------------------------------------------------------------------------

def _generate_random_json_value(depth: int = 0, max_depth: int = 3):
    """
        Generate a random JSON-serializable value.
        
        :param depth: Current recursion depth.
        :param max_depth: Maximum recursion depth for nested structures.
        
        :returns: A random JSON-serializable value.
    """
    # Limit depth to prevent infinite recursion
    if depth >= max_depth:
        # At max depth, only generate primitives
        value_type = random.choice(['string', 'int', 'float', 'bool', 'null'])
    else:
        value_type = random.choice(['string', 'int', 'float', 'bool', 'null', 'array', 'object'])
    
    if value_type == 'string':
        # Generate random string with various characters
        length = random.randint(0, 20)
        chars = string.ascii_letters + string.digits + ' -_.!@#$%^&*()[]{}:;,<>?'
        return ''.join(random.choices(chars, k=length))
    elif value_type == 'int':
        return random.randint(-1000000, 1000000)
    elif value_type == 'float':
        # Generate float with limited precision to avoid floating point issues
        return round(random.uniform(-1000.0, 1000.0), 6)
    elif value_type == 'bool':
        return random.choice([True, False])
    elif value_type == 'null':
        return None
    elif value_type == 'array':
        # Generate array with 0-5 elements
        length = random.randint(0, 5)
        return [_generate_random_json_value(depth + 1, max_depth) for _ in range(length)]
    elif value_type == 'object':
        # Generate object with 0-5 keys
        num_keys = random.randint(0, 5)
        obj = {}
        for _ in range(num_keys):
            # Generate valid JSON object key (string)
            key_length = random.randint(1, 10)
            key = ''.join(random.choices(string.ascii_lowercase + string.digits + '_', k=key_length))
            obj[key] = _generate_random_json_value(depth + 1, max_depth)
        return obj
    
    return None


def _json_equivalent(a: Any, b: Any) -> bool:
    """
        Check if two JSON values are equivalent.
        
        Handles floating point comparison with tolerance.
        
        :param a: First value.
        :param b: Second value.
        
        :returns: True if values are equivalent.
    """
    if type(a) != type(b):
        # Special case: int and float comparison
        if isinstance(a, (int, float)) and isinstance(b, (int, float)):
            return abs(float(a) - float(b)) < 1e-9
        return False
    
    if isinstance(a, dict):
        if set(a.keys()) != set(b.keys()):
            return False
        return all(_json_equivalent(a[k], b[k]) for k in a.keys())
    
    if isinstance(a, list):
        if len(a) != len(b):
            return False
        return all(_json_equivalent(x, y) for x, y in zip(a, b))
    
    if isinstance(a, float):
        return abs(a - b) < 1e-9
    
    return a == b


def test_property_json_round_trip():
    """
    Property 5: Request JSON Round-Trip
    
    For any valid JSON body, calling request.json() SHALL return a Python
    object that, when serialized back to JSON, produces equivalent JSON content.
    
    **Feature: router-request-handling, Property 5: Request JSON Round-Trip**
    **Validates: Requirements 3.6**
    """
    # Run 100 iterations
    for iteration in range(100):
        # Generate a random JSON-serializable value
        original_value = _generate_random_json_value(depth=0, max_depth=3)
        
        # Serialize to JSON bytes
        json_str = json.dumps(original_value)
        json_bytes = json_str.encode('utf-8')
        
        # Create request with JSON body
        request = Request(method="POST", path="/", body=json_bytes)
        
        # Parse JSON from request
        parsed_value = request.json()
        
        # Property 1: Parsed value should be equivalent to original
        if not _json_equivalent(original_value, parsed_value):
            errmsg = f"Iteration {iteration}: Parsed value differs from original. Original: {original_value}, Parsed: {parsed_value}"
            raise AssertionError(errmsg)
        
        # Property 2: Round-trip - serialize parsed value and re-parse
        re_serialized = json.dumps(parsed_value)
        re_serialized_bytes = re_serialized.encode('utf-8')
        
        request2 = Request(method="POST", path="/", body=re_serialized_bytes)
        re_parsed_value = request2.json()
        
        # Re-parsed value should be equivalent to parsed value
        if not _json_equivalent(parsed_value, re_parsed_value):
            errmsg = f"Iteration {iteration}: Round-trip failed. Parsed: {parsed_value}, Re-parsed: {re_parsed_value}"
            raise AssertionError(errmsg)
    
    return


def test_property_json_round_trip_objects():
    """
    Property 5: Request JSON Round-Trip - Object Focus
    
    For any valid JSON object, calling request.json() SHALL return a Python
    dict that, when serialized back to JSON, produces equivalent JSON content.
    
    **Feature: router-request-handling, Property 5: Request JSON Round-Trip**
    **Validates: Requirements 3.6**
    """
    # Run 100 iterations focusing on objects
    for iteration in range(100):
        # Generate a random JSON object (dict)
        num_keys = random.randint(1, 8)
        original_obj = {}
        for _ in range(num_keys):
            key_length = random.randint(1, 15)
            key = ''.join(random.choices(string.ascii_lowercase + string.digits + '_', k=key_length))
            original_obj[key] = _generate_random_json_value(depth=1, max_depth=2)
        
        # Serialize to JSON bytes
        json_str = json.dumps(original_obj)
        json_bytes = json_str.encode('utf-8')
        
        # Create request with JSON body
        request = Request(method="POST", path="/", body=json_bytes)
        
        # Parse JSON from request
        parsed_obj = request.json()
        
        # Property: Parsed object should be a dict
        if not isinstance(parsed_obj, dict):
            errmsg = f"Iteration {iteration}: Expected dict, got {type(parsed_obj)}"
            raise AssertionError(errmsg)
        
        # Property: All keys should be present
        if set(original_obj.keys()) != set(parsed_obj.keys()):
            errmsg = f"Iteration {iteration}: Key mismatch. Original keys: {set(original_obj.keys())}, Parsed keys: {set(parsed_obj.keys())}"
            raise AssertionError(errmsg)
        
        # Property: All values should be equivalent
        for key in original_obj:
            if not _json_equivalent(original_obj[key], parsed_obj[key]):
                errmsg = f"Iteration {iteration}: Value mismatch for key '{key}'. Original: {original_obj[key]}, Parsed: {parsed_obj[key]}"
                raise AssertionError(errmsg)
        
        # Property: Round-trip should preserve structure
        re_serialized = json.dumps(parsed_obj)
        re_serialized_bytes = re_serialized.encode('utf-8')
        
        request2 = Request(method="POST", path="/", body=re_serialized_bytes)
        re_parsed_obj = request2.json()
        
        if not _json_equivalent(parsed_obj, re_parsed_obj):
            errmsg = f"Iteration {iteration}: Round-trip failed for object"
            raise AssertionError(errmsg)
    
    return


def test_property_json_round_trip_arrays():
    """
    Property 5: Request JSON Round-Trip - Array Focus
    
    For any valid JSON array, calling request.json() SHALL return a Python
    list that, when serialized back to JSON, produces equivalent JSON content.
    
    **Feature: router-request-handling, Property 5: Request JSON Round-Trip**
    **Validates: Requirements 3.6**
    """
    # Run 100 iterations focusing on arrays
    for iteration in range(100):
        # Generate a random JSON array (list)
        length = random.randint(0, 10)
        original_array = [_generate_random_json_value(depth=1, max_depth=2) for _ in range(length)]
        
        # Serialize to JSON bytes
        json_str = json.dumps(original_array)
        json_bytes = json_str.encode('utf-8')
        
        # Create request with JSON body
        request = Request(method="POST", path="/", body=json_bytes)
        
        # Parse JSON from request
        parsed_array = request.json()
        
        # Property: Parsed value should be a list
        if not isinstance(parsed_array, list):
            errmsg = f"Iteration {iteration}: Expected list, got {type(parsed_array)}"
            raise AssertionError(errmsg)
        
        # Property: Length should match
        if len(original_array) != len(parsed_array):
            errmsg = f"Iteration {iteration}: Length mismatch. Original: {len(original_array)}, Parsed: {len(parsed_array)}"
            raise AssertionError(errmsg)
        
        # Property: All elements should be equivalent
        for idx, (orig, parsed) in enumerate(zip(original_array, parsed_array)):
            if not _json_equivalent(orig, parsed):
                errmsg = f"Iteration {iteration}: Element mismatch at index {idx}. Original: {orig}, Parsed: {parsed}"
                raise AssertionError(errmsg)
        
        # Property: Round-trip should preserve structure
        re_serialized = json.dumps(parsed_array)
        re_serialized_bytes = re_serialized.encode('utf-8')
        
        request2 = Request(method="POST", path="/", body=re_serialized_bytes)
        re_parsed_array = request2.json()
        
        if not _json_equivalent(parsed_array, re_parsed_array):
            errmsg = f"Iteration {iteration}: Round-trip failed for array"
            raise AssertionError(errmsg)
    
    return


# =============================================================================
# Request.scope + Request.auth
# =============================================================================


def test_request_scope_property_returns_empty_dict_when_no_scope_supplied():
    """
        Direct construction without a ``scope`` kwarg yields an empty
        scope dict — consumers can still read ``request.scope`` and
        get a usable mapping rather than ``None``.
    """
    request = Request(method="GET", path="/")

    if request.scope != {}:
        errmsg = "Expected empty dict scope by default, got {!r}".format(request.scope)
        raise AssertionError(errmsg)

    return


def test_request_scope_property_round_trips_supplied_scope():
    """
        A ``scope`` dict passed to the constructor is exposed by
        reference (the same identity) so middleware-side mutations
        are visible to handlers.
    """
    supplied: Dict[str, Any] = {
        "session": "fake-session",
        "rate_limit_remaining": 99,
    }

    request = Request(method="GET", path="/", scope=supplied)

    if request.scope is not supplied:
        errmsg = "Expected scope property to return the supplied dict by reference"
        raise AssertionError(errmsg)

    if request.scope.get("session") != "fake-session":
        errmsg = "Expected sibling middleware-injected keys to be readable via scope"
        raise AssertionError(errmsg)

    if request.scope.get("rate_limit_remaining") != 99:
        errmsg = "Expected arbitrary middleware-injected keys to be readable"
        raise AssertionError(errmsg)

    return


def test_request_auth_returns_none_by_default():
    """
        Direct construction without a scope / without an ``auth`` key
        in scope yields ``request.auth is None``.
    """
    request = Request(method="GET", path="/")

    if request.auth is not None:
        errmsg = "Expected auth to be None by default, got {!r}".format(request.auth)
        raise AssertionError(errmsg)

    request_with_empty_auth = Request(method="GET", path="/", scope={})

    if request_with_empty_auth.auth is not None:
        errmsg = "Expected auth to be None when scope has no 'auth' key"
        raise AssertionError(errmsg)

    return


def test_request_auth_returns_value_from_scope():
    """
        ``request.auth`` is a typed shortcut for
        ``request.scope.get("auth")`` when the value is an
        :class:`AuthenticationContext`.
    """
    real_context = AuthenticationContext(
        principal=Principal(identifier="u-1"),
        scheme="Session",
    )

    request = Request(method="GET", path="/", scope={"auth": real_context})

    if request.auth is not real_context:
        errmsg = "Expected request.auth to return the scope['auth'] value"
        raise AssertionError(errmsg)

    return


def test_request_auth_returns_none_for_non_authenticationcontext_payload():
    """
        Defensive type check: when ``scope["auth"]`` carries
        something that isn't an :class:`AuthenticationContext` (a
        misbehaving third-party middleware, for example),
        ``request.auth`` returns ``None`` rather than mis-reporting
        an arbitrary object as the expected return type. The raw
        value remains accessible via :attr:`scope` for callers that
        need it.
    """
    arbitrary_object = {"not": "an AuthenticationContext"}

    request = Request(method="GET", path="/", scope={"auth": arbitrary_object})

    if request.auth is not None:
        errmsg = (
            "Expected None when scope['auth'] is not an "
            "AuthenticationContext, got {!r}".format(request.auth)
        )
        raise AssertionError(errmsg)

    if request.scope.get("auth") is not arbitrary_object:
        errmsg = "Expected the raw scope value to remain accessible via .scope"
        raise AssertionError(errmsg)

    return


def test_from_asgi_threads_scope_into_request():
    """
        ``Request.from_asgi`` retains the source scope dict so
        middleware-injected keys (e.g. ``"auth"`` set by
        :class:`AuthenticationMiddleware`) are reachable from the
        request without a side-channel.
    """
    real_context = AuthenticationContext(
        principal=Principal(identifier="u-2"),
        scheme="Session",
    )
    scope: Dict[str, Any] = {
        "type": "http",
        "method": "GET",
        "path": "/dashboard",
        "headers": [],
        "auth": real_context,
    }

    request = Request.from_asgi(scope)

    if request.scope is not scope:
        errmsg = "from_asgi should retain the scope by reference"
        raise AssertionError(errmsg)

    if request.auth is not real_context:
        errmsg = "Expected request.auth to surface the scope-injected context"
        raise AssertionError(errmsg)

    return


def test_from_asgi_works_when_scope_has_no_auth_key():
    """
        Scopes without an ``"auth"`` key are tolerated — the
        property returns ``None``.
    """
    scope: Dict[str, Any] = {
        "type": "http",
        "method": "GET",
        "path": "/health",
        "headers": [],
    }

    request = Request.from_asgi(scope)

    if request.auth is not None:
        errmsg = "Expected None auth when scope lacks the key, got {!r}".format(
            request.auth
        )
        raise AssertionError(errmsg)

    if request.scope is not scope:
        errmsg = "Expected scope identity to be preserved even without 'auth'"
        raise AssertionError(errmsg)

    return


def test_from_wsgi_exposes_environ_as_scope():
    """
        WSGI environ is also surfaced via ``request.scope`` so the
        same access pattern works under both protocol families.
        Custom WSGI middleware that stashes data in environ remains
        accessible via ``request.scope``.
    """
    environ: Dict[str, Any] = {
        "REQUEST_METHOD": "GET",
        "PATH_INFO": "/dashboard",
        "QUERY_STRING": "",
        "SERVER_NAME": "test.example.com",
        "SERVER_PORT": "443",
        "wsgi.url_scheme": "https",
        "wsgi.input": None,
        "automojo.custom_key": "value-from-wsgi-middleware",
    }

    request = Request.from_wsgi(environ)

    if request.scope is not environ:
        errmsg = "from_wsgi should retain the environ by reference"
        raise AssertionError(errmsg)

    if request.scope.get("automojo.custom_key") != "value-from-wsgi-middleware":
        errmsg = "Expected custom WSGI environ keys to be accessible via scope"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Request.form() + Request.files() — multipart integration
# =============================================================================


def test_request_form_handles_urlencoded_body():
    """
        ``Request.form()`` continues to handle the long-standing
        ``application/x-www-form-urlencoded`` body shape — no
        regression from the multipart additions.
    """
    request = Request(
        method="POST",
        path="/",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        body=b"username=alice&token=secret",
    )

    form = request.form()

    if form.get("username") != "alice":
        errmsg = "Expected form['username'] == 'alice', got {!r}".format(form.get("username"))
        raise AssertionError(errmsg)

    if form.get("token") != "secret":
        errmsg = "Expected form['token'] == 'secret', got {!r}".format(form.get("token"))
        raise AssertionError(errmsg)

    return


def test_request_form_extracts_multipart_form_fields():
    boundary = "----WebworksRequestTestBoundary"
    body_lines = [
        b"--" + boundary.encode("latin-1"),
        b'Content-Disposition: form-data; name="package"',
        b"",
        b"examplepkg",
        b"--" + boundary.encode("latin-1"),
        b'Content-Disposition: form-data; name=":action"',
        b"",
        b"file_upload",
        b"--" + boundary.encode("latin-1") + b"--",
        b"",
    ]
    body = b"\r\n".join(body_lines)

    request = Request(
        method="POST",
        path="/repository/legacy",
        headers={"Content-Type": "multipart/form-data; boundary=" + boundary},
        body=body,
    )

    form = request.form()

    if form.get("package") != "examplepkg":
        errmsg = "Expected form['package'] == 'examplepkg', got {!r}".format(form.get("package"))
        raise AssertionError(errmsg)

    if form.get(":action") != "file_upload":
        errmsg = "Expected form[':action'] == 'file_upload'"
        raise AssertionError(errmsg)

    return


def test_request_files_returns_uploaded_file():
    boundary = "----WebworksRequestFileBoundary"
    file_bytes = b"binary\x00content here"

    body_lines = [
        b"--" + boundary.encode("latin-1"),
        b'Content-Disposition: form-data; name="content"; filename="payload.bin"',
        b"Content-Type: application/octet-stream",
        b"",
        file_bytes,
        b"--" + boundary.encode("latin-1") + b"--",
        b"",
    ]
    body = b"\r\n".join(body_lines)

    request = Request(
        method="POST",
        path="/upload",
        headers={"Content-Type": "multipart/form-data; boundary=" + boundary},
        body=body,
    )

    files = request.files()

    upload = files.get("content")
    if upload is None:
        errmsg = "Expected request.files() to surface the uploaded part"
        raise AssertionError(errmsg)

    if upload.filename != "payload.bin":
        errmsg = "Expected filename 'payload.bin', got {!r}".format(upload.filename)
        raise AssertionError(errmsg)

    if upload.content != file_bytes:
        errmsg = "Expected file bytes round-trip"
        raise AssertionError(errmsg)

    return


def test_request_files_returns_empty_dict_for_non_multipart_request():
    request = Request(
        method="POST",
        path="/",
        headers={"Content-Type": "application/json"},
        body=b'{"foo": "bar"}',
    )

    files = request.files()

    if files != {}:
        errmsg = "Expected empty dict for non-multipart request, got {!r}".format(files)
        raise AssertionError(errmsg)

    return
