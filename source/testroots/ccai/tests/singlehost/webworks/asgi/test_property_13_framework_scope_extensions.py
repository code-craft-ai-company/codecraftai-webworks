"""
    Property-Based Tests for Framework Scope Extensions (Property 13).

    Property 13: Framework Scope Extensions
    For any request processed by the application, the scope dictionary SHALL
    contain webworks.request with the Request object, and after routing, SHALL
    contain webworks.route and webworks.path_params with the matched route
    information. Custom middleware scope keys SHALL use the framework namespace,
    standard ASGI keys SHALL be preserved unmodified, and the state key SHALL
    be supported per ASGI spec.

    Validates: Requirements 12.1, 12.2, 12.3, 12.4, 12.5, 12.6, 12.7
"""

import random
import string
from typing import Any, Dict, List, Optional, Tuple

from ccai.webworks.asgi.scopeparser import (
    ScopeParser,
    FRAMEWORK_NAMESPACE,
    STANDARD_ASGI_KEYS,
)
from ccai.webworks.asgi.constants import (
    SCOPE_REQUEST,
    SCOPE_ROUTE,
    SCOPE_PATH_PARAMS,
    SCOPE_STATE,
)
from ccai.webworks.wsgi.request import Request


# =============================================================================
# Random Generators
# =============================================================================

VALID_HTTP_METHODS = ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"]
VALID_SCHEMES = ["http", "https"]
VALID_HTTP_VERSIONS = ["1.0", "1.1", "2"]


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


def generate_random_headers_dict() -> Dict[str, str]:
    """Generate random headers as a dictionary."""
    common_names = ["accept", "content-type", "host", "user-agent", "x-request-id"]
    num_headers = random.randint(0, 4)
    headers: Dict[str, str] = {}
    for _ in range(num_headers):
        name = random.choice(common_names)
        if name not in headers:
            headers[name] = generate_random_string(1, 20)
    return headers


def generate_random_server() -> Tuple[str, int]:
    """Generate a random server (host, port) tuple."""
    host = generate_random_string(3, 10) + ".example.com"
    port = random.choice([80, 443, 8000, 8080])
    return (host, port)


def generate_random_request() -> Request:
    """Generate a random Request object."""
    server = generate_random_server()
    request = Request(
        method=random.choice(VALID_HTTP_METHODS),
        path=generate_random_path(),
        query_string=generate_random_string(0, 20),
        headers=generate_random_headers_dict(),
        body=generate_random_string(0, 50).encode("utf-8"),
        scheme=random.choice(VALID_SCHEMES),
        host=server[0],
        port=server[1],
    )
    return request


def generate_random_http_scope() -> Dict[str, Any]:
    """Generate a random valid ASGI HTTP scope."""
    scope: Dict[str, Any] = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": random.choice(VALID_HTTP_VERSIONS),
        "method": random.choice(VALID_HTTP_METHODS),
        "path": generate_random_path(),
        "query_string": generate_random_string(0, 30).encode("utf-8"),
        "headers": [],
        "scheme": random.choice(VALID_SCHEMES),
        "server": generate_random_server(),
    }
    if random.random() > 0.3:
        octets = [str(random.randint(1, 254)) for _ in range(4)]
        scope["client"] = (".".join(octets), random.randint(1024, 65535))
    return scope


def generate_random_path_params() -> Dict[str, str]:
    """Generate random path parameters."""
    num_params = random.randint(1, 5)
    params: Dict[str, str] = {}
    for _ in range(num_params):
        key = generate_random_string(2, 10)
        value = generate_random_string(1, 15)
        params[key] = value
    return params


def generate_random_route() -> str:
    """Generate a random route pattern string."""
    num_segments = random.randint(1, 4)
    segments = []
    for _ in range(num_segments):
        if random.random() > 0.5:
            segments.append("{" + generate_random_string(2, 8) + "}")
        else:
            segments.append(generate_random_string(2, 10))
    rtnval = "/" + "/".join(segments)
    return rtnval


# =============================================================================
# Property-Based Tests
# =============================================================================

# Feature: asgi-layer, Property 13: Framework Scope Extensions
# *For any* request processed by the application, the scope dictionary SHALL
# contain webworks.request with the Request object, and after routing, SHALL
# contain webworks.route and webworks.path_params with the matched route
# information.
# **Validates: Requirements 12.1, 12.2, 12.3, 12.4, 12.5, 12.6, 12.7**


def test_property_13_set_framework_scope_stores_request():
    """
        Property 13: Framework Scope Stores Request Object

        For any Request object and scope dictionary, calling set_framework_scope
        SHALL store the Request at scope['webworks.request'] such that it is
        the same object that was passed in.

        **Validates: Requirement 12.2**
    """
    parser = ScopeParser()

    for iteration in range(100):
        scope = generate_random_http_scope()
        request = generate_random_request()

        parser.set_framework_scope(scope, request)

        # Property: webworks.request must be present in scope
        if SCOPE_REQUEST not in scope:
            errmsg = (
                f"Iteration {iteration}: scope missing '{SCOPE_REQUEST}' "
                f"after set_framework_scope"
            )
            raise AssertionError(errmsg)

        # Property: webworks.request must be the exact Request object
        if scope[SCOPE_REQUEST] is not request:
            errmsg = (
                f"Iteration {iteration}: scope['{SCOPE_REQUEST}'] is not "
                f"the same Request object that was passed in"
            )
            raise AssertionError(errmsg)

    return


def test_property_13_set_framework_scope_stores_route_and_path_params():
    """
        Property 13: Framework Scope Stores Route and Path Params

        For any route and path_params, calling set_framework_scope with
        route and path_params SHALL store them at scope['webworks.route']
        and scope['webworks.path_params'] respectively.

        **Validates: Requirements 12.3, 12.4**
    """
    parser = ScopeParser()

    for iteration in range(100):
        scope = generate_random_http_scope()
        request = generate_random_request()
        route = generate_random_route()
        path_params = generate_random_path_params()

        parser.set_framework_scope(scope, request, route=route, path_params=path_params)

        # Property: webworks.route must be present and match
        if SCOPE_ROUTE not in scope:
            errmsg = (
                f"Iteration {iteration}: scope missing '{SCOPE_ROUTE}' "
                f"after set_framework_scope with route"
            )
            raise AssertionError(errmsg)

        if scope[SCOPE_ROUTE] is not route:
            errmsg = (
                f"Iteration {iteration}: scope['{SCOPE_ROUTE}'] is not "
                f"the same route object that was passed in"
            )
            raise AssertionError(errmsg)

        # Property: webworks.path_params must be present and match
        if SCOPE_PATH_PARAMS not in scope:
            errmsg = (
                f"Iteration {iteration}: scope missing '{SCOPE_PATH_PARAMS}' "
                f"after set_framework_scope with path_params"
            )
            raise AssertionError(errmsg)

        if scope[SCOPE_PATH_PARAMS] is not path_params:
            errmsg = (
                f"Iteration {iteration}: scope['{SCOPE_PATH_PARAMS}'] is not "
                f"the same path_params dict that was passed in"
            )
            raise AssertionError(errmsg)

    return


def test_property_13_set_framework_scope_omits_none_route_and_params():
    """
        Property 13: Framework Scope Omits None Route and Params

        When set_framework_scope is called without route or path_params,
        those keys SHALL NOT be added to the scope dictionary.

        **Validates: Requirements 12.3, 12.4**
    """
    parser = ScopeParser()

    for iteration in range(100):
        scope = generate_random_http_scope()
        request = generate_random_request()

        parser.set_framework_scope(scope, request)

        # Property: webworks.route must not be present when route is None
        if SCOPE_ROUTE in scope:
            errmsg = (
                f"Iteration {iteration}: scope contains '{SCOPE_ROUTE}' "
                f"when no route was provided"
            )
            raise AssertionError(errmsg)

        # Property: webworks.path_params must not be present when path_params is None
        if SCOPE_PATH_PARAMS in scope:
            errmsg = (
                f"Iteration {iteration}: scope contains '{SCOPE_PATH_PARAMS}' "
                f"when no path_params were provided"
            )
            raise AssertionError(errmsg)

    return


def test_property_13_custom_scope_keys_use_framework_namespace():
    """
        Property 13: Custom Scope Keys Use Framework Namespace

        For any custom key set via set_custom_scope_key, the key SHALL be
        stored with the 'webworks.' namespace prefix. Keys already prefixed
        SHALL not be double-prefixed.

        **Validates: Requirements 12.1, 12.5**
    """
    parser = ScopeParser()

    for iteration in range(100):
        scope = generate_random_http_scope()
        key_name = generate_random_string(3, 15)
        value = generate_random_string(1, 20)

        # Test without prefix - should auto-add prefix
        parser.set_custom_scope_key(scope, key_name, value)

        expected_key = f"{FRAMEWORK_NAMESPACE}{key_name}"
        if expected_key not in scope:
            errmsg = (
                f"Iteration {iteration}: scope missing '{expected_key}' "
                f"after set_custom_scope_key with key '{key_name}'"
            )
            raise AssertionError(errmsg)

        if scope[expected_key] != value:
            errmsg = (
                f"Iteration {iteration}: scope['{expected_key}'] = "
                f"'{scope[expected_key]}', expected '{value}'"
            )
            raise AssertionError(errmsg)

        # Test with prefix already present - should not double-prefix
        scope2 = generate_random_http_scope()
        prefixed_key = f"{FRAMEWORK_NAMESPACE}{key_name}"
        value2 = generate_random_string(1, 20)

        parser.set_custom_scope_key(scope2, prefixed_key, value2)

        if prefixed_key not in scope2:
            errmsg = (
                f"Iteration {iteration}: scope missing '{prefixed_key}' "
                f"after set_custom_scope_key with already-prefixed key"
            )
            raise AssertionError(errmsg)

        # Property: must not double-prefix
        double_prefixed = f"{FRAMEWORK_NAMESPACE}{prefixed_key}"
        if double_prefixed in scope2:
            errmsg = (
                f"Iteration {iteration}: scope contains double-prefixed key "
                f"'{double_prefixed}'"
            )
            raise AssertionError(errmsg)

    return


def test_property_13_get_custom_scope_key_round_trip():
    """
        Property 13: Custom Scope Key Get/Set Round-Trip

        For any custom key set via set_custom_scope_key, retrieving it via
        get_custom_scope_key with the same key name SHALL return the same value.

        **Validates: Requirements 12.1, 12.5**
    """
    parser = ScopeParser()

    for iteration in range(100):
        scope = generate_random_http_scope()
        key_name = generate_random_string(3, 15)
        value = generate_random_string(1, 20)

        parser.set_custom_scope_key(scope, key_name, value)
        retrieved = parser.get_custom_scope_key(scope, key_name)

        if retrieved != value:
            errmsg = (
                f"Iteration {iteration}: get_custom_scope_key returned "
                f"'{retrieved}', expected '{value}' for key '{key_name}'"
            )
            raise AssertionError(errmsg)

        # Also test retrieval with the full prefixed key
        full_key = f"{FRAMEWORK_NAMESPACE}{key_name}"
        retrieved2 = parser.get_custom_scope_key(scope, full_key)

        if retrieved2 != value:
            errmsg = (
                f"Iteration {iteration}: get_custom_scope_key with full key "
                f"'{full_key}' returned '{retrieved2}', expected '{value}'"
            )
            raise AssertionError(errmsg)

    return


def test_property_13_standard_asgi_keys_preserved():
    """
        Property 13: Standard ASGI Keys Preserved

        For any scope with standard ASGI keys, calling preserve_standard_keys
        with updates SHALL NOT modify any standard ASGI key values. Only
        non-standard keys (including framework namespace keys) SHALL be updated.

        **Validates: Requirement 12.6**
    """
    parser = ScopeParser()

    for iteration in range(100):
        scope = generate_random_http_scope()

        # Capture original values of all standard keys
        original_standard: Dict[str, Any] = {}
        for key in STANDARD_ASGI_KEYS:
            if key in scope:
                original_standard[key] = scope[key]

        # Create updates that attempt to overwrite standard keys and add custom keys
        updates: Dict[str, Any] = {}

        # Try to overwrite some standard keys
        updates["type"] = "tampered"
        updates["method"] = "TAMPERED"
        updates["path"] = "/tampered"

        # Add framework namespace keys (these should be applied)
        custom_key = f"{FRAMEWORK_NAMESPACE}custom_{generate_random_string(3, 8)}"
        custom_value = generate_random_string(1, 15)
        updates[custom_key] = custom_value

        result = parser.preserve_standard_keys(scope, updates)

        # Property: standard ASGI keys must retain original values
        for key, original_value in original_standard.items():
            if key in result and result[key] != original_value:
                errmsg = (
                    f"Iteration {iteration}: standard key '{key}' was modified "
                    f"from '{original_value}' to '{result[key]}'"
                )
                raise AssertionError(errmsg)

        # Property: framework namespace keys must be updated
        if custom_key not in result:
            errmsg = (
                f"Iteration {iteration}: framework key '{custom_key}' was not "
                f"applied by preserve_standard_keys"
            )
            raise AssertionError(errmsg)

        if result[custom_key] != custom_value:
            errmsg = (
                f"Iteration {iteration}: framework key '{custom_key}' has "
                f"value '{result[custom_key]}', expected '{custom_value}'"
            )
            raise AssertionError(errmsg)

    return


def test_property_13_state_key_support():
    """
        Property 13: State Key Support Per ASGI Spec

        The scope SHALL support a 'state' key for application-level state.
        ensure_state SHALL create the state dict if missing, and get_state
        SHALL return the state dict or empty dict if absent.

        **Validates: Requirement 12.7**
    """
    parser = ScopeParser()

    for iteration in range(100):
        scope = generate_random_http_scope()

        # Test get_state on scope without state key
        if "state" in scope:
            del scope["state"]

        state = parser.get_state(scope)
        if not isinstance(state, dict):
            errmsg = (
                f"Iteration {iteration}: get_state returned "
                f"{type(state).__name__}, expected dict"
            )
            raise AssertionError(errmsg)

        # Test ensure_state creates state if missing
        if "state" in scope:
            del scope["state"]

        ensured = parser.ensure_state(scope)
        if not isinstance(ensured, dict):
            errmsg = (
                f"Iteration {iteration}: ensure_state returned "
                f"{type(ensured).__name__}, expected dict"
            )
            raise AssertionError(errmsg)

        # Property: after ensure_state, 'state' key must exist in scope
        if "state" not in scope:
            errmsg = (
                f"Iteration {iteration}: scope missing 'state' key "
                f"after ensure_state"
            )
            raise AssertionError(errmsg)

        # Property: ensure_state must return the same dict that is in scope
        if scope["state"] is not ensured:
            errmsg = (
                f"Iteration {iteration}: ensure_state returned a different "
                f"dict than scope['state']"
            )
            raise AssertionError(errmsg)

        # Test with pre-existing state
        scope3 = generate_random_http_scope()
        existing_state = {"app_key": generate_random_string(3, 10)}
        scope3["state"] = existing_state

        retrieved = parser.get_state(scope3)
        if retrieved is not existing_state:
            errmsg = (
                f"Iteration {iteration}: get_state did not return the "
                f"existing state dict"
            )
            raise AssertionError(errmsg)

        ensured3 = parser.ensure_state(scope3)
        if ensured3 is not existing_state:
            errmsg = (
                f"Iteration {iteration}: ensure_state replaced existing "
                f"state dict instead of returning it"
            )
            raise AssertionError(errmsg)

    return


def test_property_13_get_framework_scope_keys_returns_only_namespaced():
    """
        Property 13: Get Framework Scope Keys Returns Only Namespaced

        For any scope with a mix of standard ASGI keys and framework namespace
        keys, get_framework_scope_keys SHALL return only keys prefixed with
        'webworks.' and none of the standard ASGI keys.

        **Validates: Requirements 12.1, 12.5**
    """
    parser = ScopeParser()

    for iteration in range(100):
        scope = generate_random_http_scope()
        request = generate_random_request()

        # Add framework scope keys
        parser.set_framework_scope(scope, request)

        # Add some custom keys via set_custom_scope_key
        num_custom = random.randint(1, 4)
        custom_keys: Dict[str, str] = {}
        for _ in range(num_custom):
            key = generate_random_string(3, 10)
            value = generate_random_string(1, 15)
            parser.set_custom_scope_key(scope, key, value)
            custom_keys[f"{FRAMEWORK_NAMESPACE}{key}"] = value

        framework_keys = parser.get_framework_scope_keys(scope)

        # Property: all returned keys must start with framework namespace
        for key in framework_keys:
            if not key.startswith(FRAMEWORK_NAMESPACE):
                errmsg = (
                    f"Iteration {iteration}: get_framework_scope_keys returned "
                    f"key '{key}' which does not start with '{FRAMEWORK_NAMESPACE}'"
                )
                raise AssertionError(errmsg)

        # Property: no standard ASGI keys should be in the result
        for key in STANDARD_ASGI_KEYS:
            if key in framework_keys:
                errmsg = (
                    f"Iteration {iteration}: get_framework_scope_keys returned "
                    f"standard ASGI key '{key}'"
                )
                raise AssertionError(errmsg)

        # Property: webworks.request must be in the result
        if SCOPE_REQUEST not in framework_keys:
            errmsg = (
                f"Iteration {iteration}: get_framework_scope_keys missing "
                f"'{SCOPE_REQUEST}'"
            )
            raise AssertionError(errmsg)

        # Property: all custom keys we added must be in the result
        for key, value in custom_keys.items():
            if key not in framework_keys:
                errmsg = (
                    f"Iteration {iteration}: get_framework_scope_keys missing "
                    f"custom key '{key}'"
                )
                raise AssertionError(errmsg)

            if framework_keys[key] != value:
                errmsg = (
                    f"Iteration {iteration}: framework key '{key}' has value "
                    f"'{framework_keys[key]}', expected '{value}'"
                )
                raise AssertionError(errmsg)

    return


def test_property_13_is_standard_asgi_key_classification():
    """
        Property 13: Standard ASGI Key Classification

        For any key in STANDARD_ASGI_KEYS, is_standard_asgi_key SHALL return
        True. For any framework namespace key, is_standard_asgi_key SHALL
        return False.

        **Validates: Requirement 12.6**
    """
    parser = ScopeParser()

    for iteration in range(100):
        # Property: all standard keys must be classified as standard
        for key in STANDARD_ASGI_KEYS:
            if not parser.is_standard_asgi_key(key):
                errmsg = (
                    f"Iteration {iteration}: is_standard_asgi_key returned "
                    f"False for standard key '{key}'"
                )
                raise AssertionError(errmsg)

        # Property: framework namespace keys must not be classified as standard
        custom_key = f"{FRAMEWORK_NAMESPACE}{generate_random_string(3, 15)}"
        if parser.is_standard_asgi_key(custom_key):
            errmsg = (
                f"Iteration {iteration}: is_standard_asgi_key returned True "
                f"for framework key '{custom_key}'"
            )
            raise AssertionError(errmsg)

        # Property: random non-standard, non-framework keys must not be standard
        random_key = f"custom.{generate_random_string(3, 10)}"
        if parser.is_standard_asgi_key(random_key):
            errmsg = (
                f"Iteration {iteration}: is_standard_asgi_key returned True "
                f"for random key '{random_key}'"
            )
            raise AssertionError(errmsg)

    return
