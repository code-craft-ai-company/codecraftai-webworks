"""
    Tests for the ScopeParser class.
    
    This module contains unit tests for the ASGI scope parser functionality.
"""

from typing import Any, Dict, List, Tuple

from automojo.webworks.asgi.scopeparser import ScopeParser
from automojo.webworks.asgi.constants import (
    SCOPE_REQUEST,
    SCOPE_ROUTE,
    SCOPE_PATH_PARAMS,
)
from automojo.webworks.wsgi.request import Request


# =============================================================================
# Unit Tests for ScopeParser - Basic HTTP Scope Extraction
# =============================================================================

def test_get_method_returns_method_from_scope():
    """
        Test that get_method returns the method from scope.
    """
    parser = ScopeParser()
    scope = {"method": "POST"}
    
    result = parser.get_method(scope)
    
    expected = "POST"
    if result != expected:
        errmsg = f"Expected method '{expected}', got '{result}'"
        raise AssertionError(errmsg)
    
    return


def test_get_method_returns_default_when_missing():
    """
        Test that get_method returns 'GET' when method is missing.
    """
    parser = ScopeParser()
    scope: Dict[str, Any] = {}
    
    result = parser.get_method(scope)
    
    expected = "GET"
    if result != expected:
        errmsg = f"Expected default method '{expected}', got '{result}'"
        raise AssertionError(errmsg)
    
    return


def test_get_path_returns_path_from_scope():
    """
        Test that get_path returns the path from scope.
    """
    parser = ScopeParser()
    scope = {"path": "/api/users"}
    
    result = parser.get_path(scope)
    
    expected = "/api/users"
    if result != expected:
        errmsg = f"Expected path '{expected}', got '{result}'"
        raise AssertionError(errmsg)
    
    return


def test_get_path_returns_default_when_missing():
    """
        Test that get_path returns '/' when path is missing.
    """
    parser = ScopeParser()
    scope: Dict[str, Any] = {}
    
    result = parser.get_path(scope)
    
    expected = "/"
    if result != expected:
        errmsg = f"Expected default path '{expected}', got '{result}'"
        raise AssertionError(errmsg)
    
    return


def test_get_query_string_returns_decoded_query_string():
    """
        Test that get_query_string decodes bytes to string.
    """
    parser = ScopeParser()
    scope = {"query_string": b"id=1&name=test"}
    
    result = parser.get_query_string(scope)
    
    expected = "id=1&name=test"
    if result != expected:
        errmsg = f"Expected query string '{expected}', got '{result}'"
        raise AssertionError(errmsg)
    
    return


def test_get_query_string_returns_empty_when_missing():
    """
        Test that get_query_string returns empty string when missing.
    """
    parser = ScopeParser()
    scope: Dict[str, Any] = {}
    
    result = parser.get_query_string(scope)
    
    expected = ""
    if result != expected:
        errmsg = f"Expected empty query string, got '{result}'"
        raise AssertionError(errmsg)
    
    return


def test_get_scheme_returns_scheme_from_scope():
    """
        Test that get_scheme returns the scheme from scope.
    """
    parser = ScopeParser()
    scope = {"scheme": "https"}
    
    result = parser.get_scheme(scope)
    
    expected = "https"
    if result != expected:
        errmsg = f"Expected scheme '{expected}', got '{result}'"
        raise AssertionError(errmsg)
    
    return


def test_get_scheme_returns_default_when_missing():
    """
        Test that get_scheme returns 'http' when scheme is missing.
    """
    parser = ScopeParser()
    scope: Dict[str, Any] = {}
    
    result = parser.get_scheme(scope)
    
    expected = "http"
    if result != expected:
        errmsg = f"Expected default scheme '{expected}', got '{result}'"
        raise AssertionError(errmsg)
    
    return


def test_get_server_returns_server_tuple_from_scope():
    """
        Test that get_server returns the server tuple from scope.
    """
    parser = ScopeParser()
    scope = {"server": ("example.com", 8080)}
    
    result = parser.get_server(scope)
    
    expected = ("example.com", 8080)
    if result != expected:
        errmsg = f"Expected server {expected}, got {result}"
        raise AssertionError(errmsg)
    
    return


def test_get_server_returns_default_for_http_when_missing():
    """
        Test that get_server returns localhost:80 for http when missing.
    """
    parser = ScopeParser()
    scope = {"scheme": "http"}
    
    result = parser.get_server(scope)
    
    expected = ("localhost", 80)
    if result != expected:
        errmsg = f"Expected default server {expected}, got {result}"
        raise AssertionError(errmsg)
    
    return


def test_get_server_returns_default_for_https_when_missing():
    """
        Test that get_server returns localhost:443 for https when missing.
    """
    parser = ScopeParser()
    scope = {"scheme": "https"}
    
    result = parser.get_server(scope)
    
    expected = ("localhost", 443)
    if result != expected:
        errmsg = f"Expected default server {expected}, got {result}"
        raise AssertionError(errmsg)
    
    return


def test_get_client_returns_client_tuple_from_scope():
    """
        Test that get_client returns the client tuple from scope.
    """
    parser = ScopeParser()
    scope = {"client": ("192.168.1.100", 54321)}
    
    result = parser.get_client(scope)
    
    expected = ("192.168.1.100", 54321)
    if result != expected:
        errmsg = f"Expected client {expected}, got {result}"
        raise AssertionError(errmsg)
    
    return


def test_get_client_returns_none_when_missing():
    """
        Test that get_client returns None when client is missing.
    """
    parser = ScopeParser()
    scope: Dict[str, Any] = {}
    
    result = parser.get_client(scope)
    
    if result is not None:
        errmsg = f"Expected None, got {result}"
        raise AssertionError(errmsg)
    
    return


def test_get_http_version_returns_version_from_scope():
    """
        Test that get_http_version returns the version from scope.
    """
    parser = ScopeParser()
    scope = {"http_version": "2"}
    
    result = parser.get_http_version(scope)
    
    expected = "2"
    if result != expected:
        errmsg = f"Expected http_version '{expected}', got '{result}'"
        raise AssertionError(errmsg)
    
    return


def test_get_http_version_returns_default_when_missing():
    """
        Test that get_http_version returns '1.1' when missing.
    """
    parser = ScopeParser()
    scope: Dict[str, Any] = {}
    
    result = parser.get_http_version(scope)
    
    expected = "1.1"
    if result != expected:
        errmsg = f"Expected default http_version '{expected}', got '{result}'"
        raise AssertionError(errmsg)
    
    return


def test_get_root_path_returns_root_path_from_scope():
    """
        Test that get_root_path returns the root_path from scope.
    """
    parser = ScopeParser()
    scope = {"root_path": "/app"}
    
    result = parser.get_root_path(scope)
    
    expected = "/app"
    if result != expected:
        errmsg = f"Expected root_path '{expected}', got '{result}'"
        raise AssertionError(errmsg)
    
    return


def test_get_root_path_returns_empty_when_missing():
    """
        Test that get_root_path returns empty string when missing.
    """
    parser = ScopeParser()
    scope: Dict[str, Any] = {}
    
    result = parser.get_root_path(scope)
    
    expected = ""
    if result != expected:
        errmsg = f"Expected empty root_path, got '{result}'"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for ScopeParser - Header Extraction
# =============================================================================

def test_get_headers_extracts_headers_from_byte_tuples():
    """
        Test that get_headers extracts headers from byte tuples.
    """
    parser = ScopeParser()
    scope = {
        "headers": [
            (b"content-type", b"application/json"),
            (b"accept", b"*/*"),
        ]
    }
    
    result = parser.get_headers(scope)
    
    if "Content-Type" not in result:
        errmsg = "Expected 'Content-Type' header in result"
        raise AssertionError(errmsg)
    
    if result["Content-Type"] != "application/json":
        errmsg = f"Expected Content-Type='application/json', got '{result['Content-Type']}'"
        raise AssertionError(errmsg)
    
    if "Accept" not in result:
        errmsg = "Expected 'Accept' header in result"
        raise AssertionError(errmsg)
    
    if result["Accept"] != "*/*":
        errmsg = f"Expected Accept='*/*', got '{result['Accept']}'"
        raise AssertionError(errmsg)
    
    return


def test_get_headers_normalizes_header_names_to_title_case():
    """
        Test that get_headers normalizes header names to title case.
    """
    parser = ScopeParser()
    scope = {
        "headers": [
            (b"x-custom-header", b"custom-value"),
            (b"X-ANOTHER-HEADER", b"another-value"),
        ]
    }
    
    result = parser.get_headers(scope)
    
    if "X-Custom-Header" not in result:
        errmsg = "Expected 'X-Custom-Header' header in result"
        raise AssertionError(errmsg)
    
    if "X-Another-Header" not in result:
        errmsg = "Expected 'X-Another-Header' header in result"
        raise AssertionError(errmsg)
    
    return


def test_get_headers_returns_empty_dict_when_no_headers():
    """
        Test that get_headers returns empty dict when no headers.
    """
    parser = ScopeParser()
    scope: Dict[str, Any] = {}
    
    result = parser.get_headers(scope)
    
    if len(result) != 0:
        errmsg = f"Expected empty headers dict, got {len(result)} headers"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for ScopeParser - parse_http Method
# =============================================================================

def test_parse_http_creates_request_object():
    """
        Test that parse_http creates a Request object with correct values.
    """
    parser = ScopeParser()
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/api/users",
        "query_string": b"id=1",
        "scheme": "https",
        "server": ("example.com", 443),
        "headers": [
            (b"content-type", b"application/json"),
            (b"content-length", b"100"),
        ],
    }
    
    result = parser.parse_http(scope)
    
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
    
    return


def test_parse_http_extracts_content_type():
    """
        Test that parse_http extracts content type from headers.
    """
    parser = ScopeParser()
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/",
        "headers": [
            (b"content-type", b"application/json"),
        ],
    }
    
    result = parser.parse_http(scope)
    
    if result.content_type != "application/json":
        errmsg = f"Expected content_type 'application/json', got '{result.content_type}'"
        raise AssertionError(errmsg)
    
    return


def test_parse_http_extracts_content_length():
    """
        Test that parse_http extracts content length from headers.
    """
    parser = ScopeParser()
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/",
        "headers": [
            (b"content-length", b"256"),
        ],
    }
    
    result = parser.parse_http(scope)
    
    if result.content_length != 256:
        errmsg = f"Expected content_length 256, got {result.content_length}"
        raise AssertionError(errmsg)
    
    return


def test_parse_http_handles_missing_optional_keys():
    """
        Test that parse_http handles missing optional keys with defaults.
    """
    parser = ScopeParser()
    scope: Dict[str, Any] = {
        "type": "http",
    }
    
    result = parser.parse_http(scope)
    
    if result.method != "GET":
        errmsg = f"Expected default method 'GET', got '{result.method}'"
        raise AssertionError(errmsg)
    
    if result.path != "/":
        errmsg = f"Expected default path '/', got '{result.path}'"
        raise AssertionError(errmsg)
    
    if result.query_string != "":
        errmsg = f"Expected empty query_string, got '{result.query_string}'"
        raise AssertionError(errmsg)
    
    if result.scheme != "http":
        errmsg = f"Expected default scheme 'http', got '{result.scheme}'"
        raise AssertionError(errmsg)
    
    return


def test_parse_http_creates_request_with_empty_body():
    """
        Test that parse_http creates Request with empty body.
        
        The body must be read asynchronously via receive callable,
        so parse_http should create a Request with empty body.
    """
    parser = ScopeParser()
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/",
    }
    
    result = parser.parse_http(scope)
    
    if result.body != b"":
        errmsg = f"Expected empty body, got {len(result.body)} bytes"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for ScopeParser - Framework Scope Extensions
# =============================================================================

def test_set_framework_scope_sets_request():
    """
        Test that set_framework_scope sets the webworks.request key.
    """
    parser = ScopeParser()
    scope: Dict[str, Any] = {}
    
    request = Request(
        method="GET",
        path="/",
        query_string="",
        headers={},
        body=b"",
        scheme="http",
        host="localhost",
        port=80,
    )
    
    parser.set_framework_scope(scope, request)
    
    if SCOPE_REQUEST not in scope:
        errmsg = f"Expected '{SCOPE_REQUEST}' key in scope"
        raise AssertionError(errmsg)
    
    if scope[SCOPE_REQUEST] is not request:
        errmsg = "Expected request object in scope"
        raise AssertionError(errmsg)
    
    return


def test_set_framework_scope_sets_route():
    """
        Test that set_framework_scope sets the webworks.route key.
    """
    parser = ScopeParser()
    scope: Dict[str, Any] = {}
    
    request = Request(
        method="GET",
        path="/",
        query_string="",
        headers={},
        body=b"",
        scheme="http",
        host="localhost",
        port=80,
    )
    
    route = {"name": "test_route", "pattern": "/users/{id}"}
    
    parser.set_framework_scope(scope, request, route=route)
    
    if SCOPE_ROUTE not in scope:
        errmsg = f"Expected '{SCOPE_ROUTE}' key in scope"
        raise AssertionError(errmsg)
    
    if scope[SCOPE_ROUTE] != route:
        errmsg = "Expected route object in scope"
        raise AssertionError(errmsg)
    
    return


def test_set_framework_scope_sets_path_params():
    """
        Test that set_framework_scope sets the webworks.path_params key.
    """
    parser = ScopeParser()
    scope: Dict[str, Any] = {}
    
    request = Request(
        method="GET",
        path="/",
        query_string="",
        headers={},
        body=b"",
        scheme="http",
        host="localhost",
        port=80,
    )
    
    path_params = {"id": "123", "name": "test"}
    
    parser.set_framework_scope(scope, request, path_params=path_params)
    
    if SCOPE_PATH_PARAMS not in scope:
        errmsg = f"Expected '{SCOPE_PATH_PARAMS}' key in scope"
        raise AssertionError(errmsg)
    
    if scope[SCOPE_PATH_PARAMS] != path_params:
        errmsg = "Expected path_params object in scope"
        raise AssertionError(errmsg)
    
    return


def test_set_framework_scope_does_not_set_route_when_none():
    """
        Test that set_framework_scope does not set route when None.
    """
    parser = ScopeParser()
    scope: Dict[str, Any] = {}
    
    request = Request(
        method="GET",
        path="/",
        query_string="",
        headers={},
        body=b"",
        scheme="http",
        host="localhost",
        port=80,
    )
    
    parser.set_framework_scope(scope, request, route=None)
    
    if SCOPE_ROUTE in scope:
        errmsg = f"Did not expect '{SCOPE_ROUTE}' key in scope"
        raise AssertionError(errmsg)
    
    return


def test_set_framework_scope_does_not_set_path_params_when_none():
    """
        Test that set_framework_scope does not set path_params when None.
    """
    parser = ScopeParser()
    scope: Dict[str, Any] = {}
    
    request = Request(
        method="GET",
        path="/",
        query_string="",
        headers={},
        body=b"",
        scheme="http",
        host="localhost",
        port=80,
    )
    
    parser.set_framework_scope(scope, request, path_params=None)
    
    if SCOPE_PATH_PARAMS in scope:
        errmsg = f"Did not expect '{SCOPE_PATH_PARAMS}' key in scope"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for ScopeParser - Custom Scope Keys from Middleware
# =============================================================================

def test_set_custom_scope_key_adds_namespace_prefix():
    """
        Test that set_custom_scope_key adds framework namespace prefix.
    """
    parser = ScopeParser()
    scope: Dict[str, Any] = {}
    
    parser.set_custom_scope_key(scope, "user_id", "12345")
    
    expected_key = "webworks.user_id"
    if expected_key not in scope:
        errmsg = f"Expected '{expected_key}' key in scope"
        raise AssertionError(errmsg)
    
    if scope[expected_key] != "12345":
        errmsg = f"Expected value '12345', got '{scope[expected_key]}'"
        raise AssertionError(errmsg)
    
    return


def test_set_custom_scope_key_preserves_existing_prefix():
    """
        Test that set_custom_scope_key preserves existing namespace prefix.
    """
    parser = ScopeParser()
    scope: Dict[str, Any] = {}
    
    parser.set_custom_scope_key(scope, "webworks.session", {"id": "abc"})
    
    expected_key = "webworks.session"
    if expected_key not in scope:
        errmsg = f"Expected '{expected_key}' key in scope"
        raise AssertionError(errmsg)
    
    if scope[expected_key] != {"id": "abc"}:
        errmsg = f"Expected session dict, got '{scope[expected_key]}'"
        raise AssertionError(errmsg)
    
    return


def test_get_custom_scope_key_retrieves_value():
    """
        Test that get_custom_scope_key retrieves value with namespace.
    """
    parser = ScopeParser()
    scope: Dict[str, Any] = {"webworks.user_id": "12345"}
    
    result = parser.get_custom_scope_key(scope, "user_id")
    
    if result != "12345":
        errmsg = f"Expected '12345', got '{result}'"
        raise AssertionError(errmsg)
    
    return


def test_get_custom_scope_key_returns_default_when_missing():
    """
        Test that get_custom_scope_key returns default when key missing.
    """
    parser = ScopeParser()
    scope: Dict[str, Any] = {}
    
    result = parser.get_custom_scope_key(scope, "missing_key", default="default_value")
    
    if result != "default_value":
        errmsg = f"Expected 'default_value', got '{result}'"
        raise AssertionError(errmsg)
    
    return


def test_get_custom_scope_key_with_full_namespace():
    """
        Test that get_custom_scope_key works with full namespace key.
    """
    parser = ScopeParser()
    scope: Dict[str, Any] = {"webworks.auth_token": "token123"}
    
    result = parser.get_custom_scope_key(scope, "webworks.auth_token")
    
    if result != "token123":
        errmsg = f"Expected 'token123', got '{result}'"
        raise AssertionError(errmsg)
    
    return


def test_get_framework_scope_keys_returns_all_framework_keys():
    """
        Test that get_framework_scope_keys returns all framework namespace keys.
    """
    parser = ScopeParser()
    scope: Dict[str, Any] = {
        "type": "http",
        "method": "GET",
        "webworks.request": "request_obj",
        "webworks.user_id": "12345",
        "webworks.session": {"id": "abc"},
    }
    
    result = parser.get_framework_scope_keys(scope)
    
    if len(result) != 3:
        errmsg = f"Expected 3 framework keys, got {len(result)}"
        raise AssertionError(errmsg)
    
    if "webworks.request" not in result:
        errmsg = "Expected 'webworks.request' in result"
        raise AssertionError(errmsg)
    
    if "webworks.user_id" not in result:
        errmsg = "Expected 'webworks.user_id' in result"
        raise AssertionError(errmsg)
    
    if "webworks.session" not in result:
        errmsg = "Expected 'webworks.session' in result"
        raise AssertionError(errmsg)
    
    return


def test_get_framework_scope_keys_excludes_standard_keys():
    """
        Test that get_framework_scope_keys excludes standard ASGI keys.
    """
    parser = ScopeParser()
    scope: Dict[str, Any] = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "webworks.request": "request_obj",
    }
    
    result = parser.get_framework_scope_keys(scope)
    
    if "type" in result:
        errmsg = "Did not expect 'type' in framework keys"
        raise AssertionError(errmsg)
    
    if "method" in result:
        errmsg = "Did not expect 'method' in framework keys"
        raise AssertionError(errmsg)
    
    if "path" in result:
        errmsg = "Did not expect 'path' in framework keys"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for ScopeParser - Standard ASGI Key Preservation
# =============================================================================

def test_is_standard_asgi_key_returns_true_for_standard_keys():
    """
        Test that is_standard_asgi_key returns True for standard keys.
    """
    parser = ScopeParser()
    
    standard_keys = ["type", "method", "path", "headers", "server", "client", "state"]
    
    for key in standard_keys:
        result = parser.is_standard_asgi_key(key)
        if not result:
            errmsg = f"Expected '{key}' to be a standard ASGI key"
            raise AssertionError(errmsg)
    
    return


def test_is_standard_asgi_key_returns_false_for_framework_keys():
    """
        Test that is_standard_asgi_key returns False for framework keys.
    """
    parser = ScopeParser()
    
    framework_keys = ["webworks.request", "webworks.route", "webworks.path_params"]
    
    for key in framework_keys:
        result = parser.is_standard_asgi_key(key)
        if result:
            errmsg = f"Did not expect '{key}' to be a standard ASGI key"
            raise AssertionError(errmsg)
    
    return


def test_preserve_standard_keys_does_not_modify_standard_keys():
    """
        Test that preserve_standard_keys does not modify standard ASGI keys.
    """
    parser = ScopeParser()
    scope: Dict[str, Any] = {
        "type": "http",
        "method": "GET",
        "path": "/original",
        "webworks.request": "original_request",
    }
    
    updates = {
        "type": "websocket",  # Should be ignored
        "method": "POST",  # Should be ignored
        "path": "/modified",  # Should be ignored
        "webworks.request": "new_request",  # Should be applied
        "webworks.custom": "custom_value",  # Should be applied
    }
    
    result = parser.preserve_standard_keys(scope, updates)
    
    # Standard keys should be unchanged
    if result["type"] != "http":
        errmsg = f"Expected type 'http', got '{result['type']}'"
        raise AssertionError(errmsg)
    
    if result["method"] != "GET":
        errmsg = f"Expected method 'GET', got '{result['method']}'"
        raise AssertionError(errmsg)
    
    if result["path"] != "/original":
        errmsg = f"Expected path '/original', got '{result['path']}'"
        raise AssertionError(errmsg)
    
    # Framework keys should be updated
    if result["webworks.request"] != "new_request":
        errmsg = f"Expected webworks.request 'new_request', got '{result['webworks.request']}'"
        raise AssertionError(errmsg)
    
    if result.get("webworks.custom") != "custom_value":
        errmsg = f"Expected webworks.custom 'custom_value', got '{result.get('webworks.custom')}'"
        raise AssertionError(errmsg)
    
    return


def test_preserve_standard_keys_supports_state_key():
    """
        Test that preserve_standard_keys preserves the state key per ASGI spec.
    """
    parser = ScopeParser()
    scope: Dict[str, Any] = {
        "type": "http",
        "state": {"original": "value"},
    }
    
    updates = {
        "state": {"modified": "value"},  # Should be ignored
    }
    
    result = parser.preserve_standard_keys(scope, updates)
    
    if result["state"] != {"original": "value"}:
        errmsg = f"Expected original state, got '{result['state']}'"
        raise AssertionError(errmsg)
    
    return


def test_get_state_returns_state_from_scope():
    """
        Test that get_state returns the state dictionary from scope.
    """
    parser = ScopeParser()
    scope: Dict[str, Any] = {
        "type": "http",
        "state": {"user_id": "12345", "session": "abc"},
    }
    
    result = parser.get_state(scope)
    
    if result != {"user_id": "12345", "session": "abc"}:
        errmsg = f"Expected state dict, got '{result}'"
        raise AssertionError(errmsg)
    
    return


def test_get_state_returns_empty_dict_when_missing():
    """
        Test that get_state returns empty dict when state is missing.
    """
    parser = ScopeParser()
    scope: Dict[str, Any] = {"type": "http"}
    
    result = parser.get_state(scope)
    
    if result != {}:
        errmsg = f"Expected empty dict, got '{result}'"
        raise AssertionError(errmsg)
    
    return


def test_ensure_state_creates_state_when_missing():
    """
        Test that ensure_state creates state key when missing.
    """
    parser = ScopeParser()
    scope: Dict[str, Any] = {"type": "http"}
    
    result = parser.ensure_state(scope)
    
    if "state" not in scope:
        errmsg = "Expected 'state' key to be created in scope"
        raise AssertionError(errmsg)
    
    if result != {}:
        errmsg = f"Expected empty dict, got '{result}'"
        raise AssertionError(errmsg)
    
    return


def test_ensure_state_returns_existing_state():
    """
        Test that ensure_state returns existing state without modification.
    """
    parser = ScopeParser()
    scope: Dict[str, Any] = {
        "type": "http",
        "state": {"existing": "value"},
    }
    
    result = parser.ensure_state(scope)
    
    if result != {"existing": "value"}:
        errmsg = f"Expected existing state, got '{result}'"
        raise AssertionError(errmsg)
    
    return


def test_ensure_state_allows_modification():
    """
        Test that ensure_state returns a reference that can be modified.
    """
    parser = ScopeParser()
    scope: Dict[str, Any] = {"type": "http"}
    
    state = parser.ensure_state(scope)
    state["new_key"] = "new_value"
    
    if scope["state"].get("new_key") != "new_value":
        errmsg = "Expected state modification to be reflected in scope"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Random Data Generators for Property Tests
# =============================================================================

import random
import string


# Valid HTTP methods per ASGI spec
VALID_HTTP_METHODS = ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS", "TRACE"]

# Valid HTTP versions
VALID_HTTP_VERSIONS = ["1.0", "1.1", "2"]

# Valid URL schemes
VALID_SCHEMES = ["http", "https"]

# Common header names for generation
COMMON_HEADER_NAMES = [
    "accept", "accept-encoding", "accept-language", "authorization",
    "cache-control", "content-type", "content-length", "host",
    "user-agent", "x-request-id", "x-forwarded-for", "cookie",
]


def generate_random_string(min_length: int = 1, max_length: int = 20) -> str:
    """Generate a random alphanumeric string."""
    length = random.randint(min_length, max_length)
    chars = string.ascii_lowercase + string.digits
    rtnval = "".join(random.choice(chars) for _ in range(length))
    return rtnval


def generate_random_path() -> str:
    """Generate a random URL path."""
    num_segments = random.randint(0, 5)
    if num_segments == 0:
        rtnval = "/"
    else:
        segments = [generate_random_string(1, 15) for _ in range(num_segments)]
        rtnval = "/" + "/".join(segments)
    return rtnval


def generate_random_query_string() -> str:
    """Generate a random query string (without leading '?')."""
    num_params = random.randint(0, 5)
    if num_params == 0:
        rtnval = ""
    else:
        params = []
        for _ in range(num_params):
            key = generate_random_string(1, 10)
            value = generate_random_string(1, 10)
            params.append(f"{key}={value}")
        rtnval = "&".join(params)
    return rtnval


def generate_random_headers() -> List[Tuple[bytes, bytes]]:
    """Generate random ASGI-format headers as list of byte tuples."""
    num_headers = random.randint(0, 6)
    headers: List[Tuple[bytes, bytes]] = []
    used_names: set = set()

    for _ in range(num_headers):
        name = random.choice(COMMON_HEADER_NAMES)
        if name in used_names:
            continue
        used_names.add(name)
        value = generate_random_string(1, 30)
        headers.append((name.encode("latin-1"), value.encode("latin-1")))

    return headers


def generate_random_server() -> Tuple[str, int]:
    """Generate a random server (host, port) tuple."""
    host = generate_random_string(3, 15) + ".example.com"
    port = random.choice([80, 443, 8000, 8080, 3000, 5000, 9090])
    rtnval = (host, port)
    return rtnval


def generate_random_client() -> Tuple[str, int]:
    """Generate a random client (host, port) tuple."""
    octets = [str(random.randint(1, 254)) for _ in range(4)]
    host = ".".join(octets)
    port = random.randint(1024, 65535)
    rtnval = (host, port)
    return rtnval


def generate_random_http_scope() -> Dict[str, Any]:
    """
        Generate a random valid ASGI HTTP scope dictionary.

        All fields are populated with random but valid values.
    """
    method = random.choice(VALID_HTTP_METHODS)
    path = generate_random_path()
    query_string = generate_random_query_string()
    scheme = random.choice(VALID_SCHEMES)
    http_version = random.choice(VALID_HTTP_VERSIONS)
    root_path = random.choice(["", "/app", "/api/v1"])
    server = generate_random_server()
    headers = generate_random_headers()

    scope: Dict[str, Any] = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": http_version,
        "method": method,
        "path": path,
        "query_string": query_string.encode("utf-8"),
        "scheme": scheme,
        "root_path": root_path,
        "headers": headers,
        "server": server,
    }

    # Optionally include client (it's optional per ASGI spec)
    if random.random() > 0.2:
        scope["client"] = generate_random_client()

    return scope


# =============================================================================
# Property-Based Tests
# =============================================================================

# Feature: asgi-layer, Property 2: HTTP Scope Parsing Round-Trip
# *For any* valid ASGI HTTP scope containing method, path, query_string,
# headers, scheme, server, client, http_version, and root_path, parsing the
# scope into a Request object SHALL preserve all values such that they can
# be reconstructed from the Request.
# **Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 2.9, 2.10**

def test_property_2_http_scope_parsing_round_trip():
    """
        Property 2: HTTP Scope Parsing Round-Trip

        For any valid ASGI HTTP scope, parsing the scope into a Request
        object SHALL preserve all values: method, path, query_string,
        headers, scheme, server (host, port), and optional client.

        **Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 2.9, 2.10**
    """
    parser = ScopeParser()

    # Run 100 iterations with random scopes
    for iteration in range(100):
        scope = generate_random_http_scope()

        # Extract expected values directly from scope
        expected_method = scope["method"]
        expected_path = scope["path"]
        expected_query_string = scope["query_string"].decode("utf-8")
        expected_scheme = scope["scheme"]
        expected_server = scope["server"]
        expected_http_version = scope["http_version"]
        expected_root_path = scope["root_path"]

        # Parse scope into Request
        request = parser.parse_http(scope)

        # Property: method is preserved (Req 2.1)
        if request.method != expected_method:
            errmsg = (
                f"Iteration {iteration}: method mismatch: "
                f"'{request.method}' != '{expected_method}'"
            )
            raise AssertionError(errmsg)

        # Property: path is preserved (Req 2.2)
        if request.path != expected_path:
            errmsg = (
                f"Iteration {iteration}: path mismatch: "
                f"'{request.path}' != '{expected_path}'"
            )
            raise AssertionError(errmsg)

        # Property: query_string is preserved (Req 2.3)
        if request.query_string != expected_query_string:
            errmsg = (
                f"Iteration {iteration}: query_string mismatch: "
                f"'{request.query_string}' != '{expected_query_string}'"
            )
            raise AssertionError(errmsg)

        # Property: scheme is preserved (Req 2.5)
        if request.scheme != expected_scheme:
            errmsg = (
                f"Iteration {iteration}: scheme mismatch: "
                f"'{request.scheme}' != '{expected_scheme}'"
            )
            raise AssertionError(errmsg)

        # Property: server host is preserved (Req 2.6)
        if request.host != str(expected_server[0]):
            errmsg = (
                f"Iteration {iteration}: host mismatch: "
                f"'{request.host}' != '{expected_server[0]}'"
            )
            raise AssertionError(errmsg)

        # Property: server port is preserved (Req 2.6)
        if request.port != int(expected_server[1]):
            errmsg = (
                f"Iteration {iteration}: port mismatch: "
                f"{request.port} != {expected_server[1]}"
            )
            raise AssertionError(errmsg)

        # Property: headers are preserved with title-case normalization (Req 2.4)
        expected_headers = {}
        for name_bytes, value_bytes in scope["headers"]:
            name = name_bytes.decode("latin-1").title()
            value = value_bytes.decode("latin-1")
            expected_headers[name] = value

        if request.headers != expected_headers:
            errmsg = (
                f"Iteration {iteration}: headers mismatch: "
                f"{request.headers} != {expected_headers}"
            )
            raise AssertionError(errmsg)

        # Property: body is empty bytes since body is read async (Req 2.10)
        if request.body != b"":
            errmsg = (
                f"Iteration {iteration}: body should be empty bytes, "
                f"got {request.body!r}"
            )
            raise AssertionError(errmsg)

    return


def test_property_2_individual_extractors_match_parse_http():
    """
        Property 2: Individual Extractor Consistency

        For any valid ASGI HTTP scope, the individual get_* methods SHALL
        return values consistent with the Request produced by parse_http().

        **Validates: Requirements 2.1, 2.2, 2.3, 2.5, 2.6, 2.7, 2.8, 2.9**
    """
    parser = ScopeParser()

    # Run 100 iterations with random scopes
    for iteration in range(100):
        scope = generate_random_http_scope()

        # Parse via parse_http
        request = parser.parse_http(scope)

        # Extract via individual methods
        method = parser.get_method(scope)
        path = parser.get_path(scope)
        query_string = parser.get_query_string(scope)
        scheme = parser.get_scheme(scope)
        server = parser.get_server(scope)
        http_version = parser.get_http_version(scope)
        root_path = parser.get_root_path(scope)
        headers = parser.get_headers(scope)
        client = parser.get_client(scope)

        # Property: get_method matches request.method (Req 2.1)
        if method != request.method:
            errmsg = f"Iteration {iteration}: get_method '{method}' != request.method '{request.method}'"
            raise AssertionError(errmsg)

        # Property: get_path matches request.path (Req 2.2)
        if path != request.path:
            errmsg = f"Iteration {iteration}: get_path '{path}' != request.path '{request.path}'"
            raise AssertionError(errmsg)

        # Property: get_query_string matches request.query_string (Req 2.3)
        if query_string != request.query_string:
            errmsg = f"Iteration {iteration}: get_query_string '{query_string}' != request.query_string '{request.query_string}'"
            raise AssertionError(errmsg)

        # Property: get_headers matches request.headers (Req 2.4)
        if headers != request.headers:
            errmsg = f"Iteration {iteration}: get_headers mismatch"
            raise AssertionError(errmsg)

        # Property: get_scheme matches request.scheme (Req 2.5)
        if scheme != request.scheme:
            errmsg = f"Iteration {iteration}: get_scheme '{scheme}' != request.scheme '{request.scheme}'"
            raise AssertionError(errmsg)

        # Property: get_server matches request host/port (Req 2.6)
        if server[0] != request.host or server[1] != request.port:
            errmsg = f"Iteration {iteration}: get_server {server} != ({request.host}, {request.port})"
            raise AssertionError(errmsg)

        # Property: get_client returns tuple or None (Req 2.7)
        if "client" in scope:
            if client is None:
                errmsg = f"Iteration {iteration}: get_client returned None when client is in scope"
                raise AssertionError(errmsg)
        else:
            if client is not None:
                errmsg = f"Iteration {iteration}: get_client returned {client} when client not in scope"
                raise AssertionError(errmsg)

        # Property: get_http_version returns valid version (Req 2.8)
        if http_version != scope.get("http_version", "1.1"):
            errmsg = f"Iteration {iteration}: get_http_version '{http_version}' != scope http_version"
            raise AssertionError(errmsg)

        # Property: get_root_path returns root path (Req 2.9)
        if root_path != scope.get("root_path", ""):
            errmsg = f"Iteration {iteration}: get_root_path '{root_path}' != scope root_path"
            raise AssertionError(errmsg)

    return


def test_property_2_missing_optional_keys_use_defaults():
    """
        Property 2: Missing Optional Keys Default Handling

        For any ASGI HTTP scope with missing optional keys, parsing SHALL
        use sensible defaults without raising exceptions.

        **Validates: Requirement 2.10**
    """
    parser = ScopeParser()

    # Keys that can be omitted from scope
    optional_keys = ["method", "path", "query_string", "scheme", "server",
                     "client", "http_version", "root_path", "headers"]

    # Run 100 iterations removing random subsets of optional keys
    for iteration in range(100):
        scope = generate_random_http_scope()

        # Remove a random subset of optional keys
        num_to_remove = random.randint(1, len(optional_keys))
        keys_to_remove = random.sample(optional_keys, num_to_remove)

        for key in keys_to_remove:
            scope.pop(key, None)

        # Property: parse_http must not raise for missing optional keys
        try:
            request = parser.parse_http(scope)
        except Exception as exc:
            errmsg = (
                f"Iteration {iteration}: parse_http raised {type(exc).__name__} "
                f"when keys {keys_to_remove} were missing: {exc}"
            )
            raise AssertionError(errmsg)

        # Property: request must be a valid Request object
        if not isinstance(request, Request):
            errmsg = (
                f"Iteration {iteration}: parse_http returned "
                f"{type(request).__name__} instead of Request"
            )
            raise AssertionError(errmsg)

        # Property: method defaults to GET when missing
        if "method" in keys_to_remove:
            if request.method != "GET":
                errmsg = f"Iteration {iteration}: default method should be 'GET', got '{request.method}'"
                raise AssertionError(errmsg)

        # Property: path defaults to "/" when missing
        if "path" in keys_to_remove:
            if request.path != "/":
                errmsg = f"Iteration {iteration}: default path should be '/', got '{request.path}'"
                raise AssertionError(errmsg)

        # Property: query_string defaults to empty when missing
        if "query_string" in keys_to_remove:
            if request.query_string != "":
                errmsg = f"Iteration {iteration}: default query_string should be '', got '{request.query_string}'"
                raise AssertionError(errmsg)

        # Property: scheme defaults to "http" when missing
        if "scheme" in keys_to_remove:
            if request.scheme != "http":
                errmsg = f"Iteration {iteration}: default scheme should be 'http', got '{request.scheme}'"
                raise AssertionError(errmsg)

        # Property: headers defaults to empty dict when missing
        if "headers" in keys_to_remove:
            if request.headers != {}:
                errmsg = f"Iteration {iteration}: default headers should be {{}}, got {request.headers}"
                raise AssertionError(errmsg)

    return
