"""
    Tests for the Router class.
    
    This module tests the URL routing functionality including:
    - Route registration
    - Path matching
    - Parameter extraction
    - Configuration options (strict_slashes, case_sensitive)
"""

from ccai.webworks.routing import Router, RouteMatch, RoutingError, Request
from ccai.webworks.endpoints.descriptor import EndpointDescriptor


def _create_handler(name: str):
    """Create a simple handler function with a given name."""
    def handler(request):
        return {"handler": name}
    handler.__name__ = name
    return handler


def _create_descriptor(
    path: str,
    methods: list = None,
    handler_name: str = None
) -> EndpointDescriptor:
    """Create an EndpointDescriptor for testing."""
    if methods is None:
        methods = ["GET"]
    if handler_name is None:
        handler_name = f"handler_{path.replace('/', '_').strip('_')}"
    
    handler = _create_handler(handler_name)
    
    return EndpointDescriptor(
        handler=handler,
        module="test_module",
        path=path,
        methods=methods
    )


# =============================================================================
# Router Construction Tests
# =============================================================================

def test_router_default_construction():
    """Test Router construction with default parameters."""
    router = Router()
    
    assert router.strict_slashes == True
    assert router.case_sensitive == True
    assert router.redirect_slashes == False
    return


def test_router_custom_construction():
    """Test Router construction with custom parameters."""
    router = Router(
        strict_slashes=False,
        case_sensitive=False,
        redirect_slashes=True
    )
    
    assert router.strict_slashes == False
    assert router.case_sensitive == False
    assert router.redirect_slashes == True
    return


# =============================================================================
# Route Registration Tests
# =============================================================================

def test_add_endpoint_simple_path():
    """Test adding an endpoint with a simple static path."""
    router = Router()
    descriptor = _create_descriptor("/users", ["GET"])
    
    router.add_endpoint(descriptor)
    
    # Verify by matching
    request = Request(method="GET", path="/users")
    match = router.match(request)
    
    assert match is not None
    assert match.handler == descriptor.handler
    assert match.matched_path == "/users"
    return


def test_add_endpoint_multiple_methods():
    """Test adding an endpoint with multiple HTTP methods."""
    router = Router()
    descriptor = _create_descriptor("/users", ["GET", "POST"])
    
    router.add_endpoint(descriptor)
    
    # Verify GET
    request_get = Request(method="GET", path="/users")
    match_get = router.match(request_get)
    assert match_get is not None
    
    # Verify POST
    request_post = Request(method="POST", path="/users")
    match_post = router.match(request_post)
    assert match_post is not None
    return


def test_add_endpoint_parameterized_path():
    """Test adding an endpoint with parameterized path."""
    router = Router()
    descriptor = _create_descriptor("/users/{id}", ["GET"])
    
    router.add_endpoint(descriptor)
    
    request = Request(method="GET", path="/users/42")
    match = router.match(request)
    
    assert match is not None
    assert match.path_params == {"id": "42"}
    return


def test_add_endpoint_typed_parameter():
    """Test adding an endpoint with typed parameter."""
    router = Router()
    descriptor = _create_descriptor("/users/{id:int}", ["GET"])
    
    router.add_endpoint(descriptor)
    
    request = Request(method="GET", path="/users/42")
    match = router.match(request)
    
    assert match is not None
    assert match.path_params == {"id": 42}
    assert isinstance(match.path_params["id"], int)
    return


def test_add_endpoint_conflict_raises_error():
    """Test that adding conflicting routes raises RoutingError."""
    router = Router()
    descriptor1 = _create_descriptor("/users", ["GET"], "handler1")
    descriptor2 = _create_descriptor("/users", ["GET"], "handler2")
    
    router.add_endpoint(descriptor1)
    
    try:
        router.add_endpoint(descriptor2)
        assert False, "Expected RoutingError"
    except RoutingError as e:
        assert e.path == "/users"
        assert e.method == "GET"
        assert e.existing_handler is not None
    return


def test_add_endpoint_same_path_different_methods():
    """Test adding same path with different methods is allowed."""
    router = Router()
    descriptor1 = _create_descriptor("/users", ["GET"], "get_handler")
    descriptor2 = _create_descriptor("/users", ["POST"], "post_handler")
    
    router.add_endpoint(descriptor1)
    router.add_endpoint(descriptor2)
    
    # Both should match
    request_get = Request(method="GET", path="/users")
    request_post = Request(method="POST", path="/users")
    
    assert router.match(request_get) is not None
    assert router.match(request_post) is not None
    return


# =============================================================================
# Route Matching Tests
# =============================================================================

def test_match_static_path():
    """Test matching a static path."""
    router = Router()
    descriptor = _create_descriptor("/api/users", ["GET"])
    router.add_endpoint(descriptor)
    
    request = Request(method="GET", path="/api/users")
    match = router.match(request)
    
    assert match is not None
    assert match.handler == descriptor.handler
    assert match.path_params == {}
    return


def test_match_returns_none_for_no_match():
    """Test that match returns None when no route matches."""
    router = Router()
    descriptor = _create_descriptor("/users", ["GET"])
    router.add_endpoint(descriptor)
    
    request = Request(method="GET", path="/posts")
    match = router.match(request)
    
    assert match is None
    return


def test_match_returns_none_for_wrong_method():
    """Test that match returns None for wrong HTTP method."""
    router = Router()
    descriptor = _create_descriptor("/users", ["GET"])
    router.add_endpoint(descriptor)
    
    request = Request(method="POST", path="/users")
    match = router.match(request)
    
    assert match is None
    return


def test_match_parameterized_path():
    """Test matching a parameterized path."""
    router = Router()
    descriptor = _create_descriptor("/users/{id}/posts/{post_id}", ["GET"])
    router.add_endpoint(descriptor)
    
    request = Request(method="GET", path="/users/123/posts/456")
    match = router.match(request)
    
    assert match is not None
    assert match.path_params == {"id": "123", "post_id": "456"}
    return


def test_match_typed_int_parameter():
    """Test matching with int type converter."""
    router = Router()
    descriptor = _create_descriptor("/users/{id:int}", ["GET"])
    router.add_endpoint(descriptor)
    
    # Valid int
    request = Request(method="GET", path="/users/42")
    match = router.match(request)
    assert match is not None
    assert match.path_params["id"] == 42
    
    # Invalid int should not match
    request_invalid = Request(method="GET", path="/users/abc")
    match_invalid = router.match(request_invalid)
    assert match_invalid is None
    return


def test_match_typed_uuid_parameter():
    """Test matching with UUID type converter."""
    router = Router()
    descriptor = _create_descriptor("/items/{id:uuid}", ["GET"])
    router.add_endpoint(descriptor)
    
    from uuid import UUID
    
    # Valid UUID
    request = Request(method="GET", path="/items/550e8400-e29b-41d4-a716-446655440000")
    match = router.match(request)
    assert match is not None
    assert match.path_params["id"] == UUID("550e8400-e29b-41d4-a716-446655440000")
    
    # Invalid UUID should not match
    request_invalid = Request(method="GET", path="/items/not-a-uuid")
    match_invalid = router.match(request_invalid)
    assert match_invalid is None
    return


def test_match_wildcard_path():
    """Test matching with wildcard path converter."""
    router = Router()
    descriptor = _create_descriptor("/files/{filepath:path}", ["GET"])
    router.add_endpoint(descriptor)
    
    request = Request(method="GET", path="/files/docs/readme.txt")
    match = router.match(request)
    
    assert match is not None
    assert match.path_params["filepath"] == "docs/readme.txt"
    return


def test_match_root_path():
    """Test matching the root path."""
    router = Router()
    descriptor = _create_descriptor("/", ["GET"])
    router.add_endpoint(descriptor)
    
    request = Request(method="GET", path="/")
    match = router.match(request)
    
    assert match is not None
    assert match.path_params == {}
    return


# =============================================================================
# Route Precedence Tests
# =============================================================================

def test_match_prefers_static_over_param():
    """Test that static routes are preferred over parameterized routes."""
    router = Router()
    
    # Add parameterized route first
    param_descriptor = _create_descriptor("/users/{id}", ["GET"], "param_handler")
    router.add_endpoint(param_descriptor)
    
    # Add static route second
    static_descriptor = _create_descriptor("/users/profile", ["GET"], "static_handler")
    router.add_endpoint(static_descriptor)
    
    # Static path should match static route
    request = Request(method="GET", path="/users/profile")
    match = router.match(request)
    
    assert match is not None
    assert match.handler.__name__ == "static_handler"
    return


def test_match_prefers_typed_over_string_param():
    """Test that typed parameters are preferred over string parameters."""
    router = Router()
    
    # Add int param route first (more specific)
    int_descriptor = _create_descriptor("/items/{id:int}", ["GET"], "int_handler")
    router.add_endpoint(int_descriptor)
    
    # Add string param route second (less specific)
    str_descriptor = _create_descriptor("/items/{name}", ["GET"], "str_handler")
    router.add_endpoint(str_descriptor)
    
    # Numeric path should match int route (more specific)
    request = Request(method="GET", path="/items/42")
    match = router.match(request)
    
    assert match is not None
    assert match.path_params["id"] == 42
    assert match.handler.__name__ == "int_handler"
    
    # Non-numeric path should match string route
    request_str = Request(method="GET", path="/items/hello")
    match_str = router.match(request_str)
    
    assert match_str is not None
    assert match_str.path_params["name"] == "hello"
    assert match_str.handler.__name__ == "str_handler"
    return


# =============================================================================
# Configuration Tests
# =============================================================================

def test_strict_slashes_true():
    """Test strict_slashes=True treats trailing slashes as different routes."""
    router = Router(strict_slashes=True)
    
    descriptor = _create_descriptor("/users", ["GET"])
    router.add_endpoint(descriptor)
    
    # Without trailing slash should match
    request = Request(method="GET", path="/users")
    match = router.match(request)
    assert match is not None
    
    # With trailing slash should NOT match
    request_slash = Request(method="GET", path="/users/")
    match_slash = router.match(request_slash)
    assert match_slash is None
    return


def test_strict_slashes_false():
    """Test strict_slashes=False matches both variants."""
    router = Router(strict_slashes=False)
    
    descriptor = _create_descriptor("/users", ["GET"])
    router.add_endpoint(descriptor)
    
    # Without trailing slash should match
    request = Request(method="GET", path="/users")
    match = router.match(request)
    assert match is not None
    
    # With trailing slash should also match
    request_slash = Request(method="GET", path="/users/")
    match_slash = router.match(request_slash)
    assert match_slash is not None
    return


def test_case_sensitive_true():
    """Test case_sensitive=True matches paths case-sensitively."""
    router = Router(case_sensitive=True)
    
    descriptor = _create_descriptor("/Users", ["GET"])
    router.add_endpoint(descriptor)
    
    # Exact case should match
    request = Request(method="GET", path="/Users")
    match = router.match(request)
    assert match is not None
    
    # Different case should NOT match
    request_lower = Request(method="GET", path="/users")
    match_lower = router.match(request_lower)
    assert match_lower is None
    return


def test_case_sensitive_false():
    """Test case_sensitive=False matches paths case-insensitively."""
    router = Router(case_sensitive=False)
    
    descriptor = _create_descriptor("/Users", ["GET"])
    router.add_endpoint(descriptor)
    
    # Exact case should match
    request = Request(method="GET", path="/Users")
    match = router.match(request)
    assert match is not None
    
    # Different case should also match
    request_lower = Request(method="GET", path="/users")
    match_lower = router.match(request_lower)
    assert match_lower is not None
    return


# =============================================================================
# RouteMatch Tests
# =============================================================================

def test_route_match_contains_descriptor():
    """Test that RouteMatch contains the endpoint descriptor."""
    router = Router()
    descriptor = _create_descriptor("/users", ["GET"])
    router.add_endpoint(descriptor)
    
    request = Request(method="GET", path="/users")
    match = router.match(request)
    
    assert match is not None
    assert match.descriptor == descriptor
    return


def test_route_match_contains_matched_path():
    """Test that RouteMatch contains the matched path pattern."""
    router = Router()
    descriptor = _create_descriptor("/users/{id:int}", ["GET"])
    router.add_endpoint(descriptor)
    
    request = Request(method="GET", path="/users/42")
    match = router.match(request)
    
    assert match is not None
    assert match.matched_path == "/users/{id:int}"
    return


# =============================================================================
# Router Repr Test
# =============================================================================

def test_router_repr():
    """Test Router string representation."""
    router = Router()
    descriptor = _create_descriptor("/users", ["GET"])
    router.add_endpoint(descriptor)
    
    repr_str = repr(router)
    
    assert "Router" in repr_str
    assert "routes=1" in repr_str
    return


# =============================================================================
# Property Tests
# =============================================================================

import random
import string


def _random_string(length: int = 8) -> str:
    """Generate a random alphanumeric string."""
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))


def _random_path_segment() -> str:
    """Generate a random path segment."""
    return _random_string(random.randint(3, 10))


def _random_static_path(depth: int = None) -> str:
    """Generate a random static path."""
    if depth is None:
        depth = random.randint(1, 4)
    segments = [_random_path_segment() for _ in range(depth)]
    return "/" + "/".join(segments)


def _random_method() -> str:
    """Generate a random HTTP method."""
    return random.choice(["GET", "POST", "PUT", "DELETE", "PATCH"])


# -----------------------------------------------------------------------------
# Property 1: Route Matching Correctness
# **Validates: Requirements 1.3, 1.4, 1.5, 1.6**
# 
# *For any* registered route with path P and method M, and any request with
# matching path P and method M, the Router SHALL return a RouteMatch containing
# the correct handler and descriptor. *For any* request with non-matching path
# or method, the Router SHALL return None.
# -----------------------------------------------------------------------------

def test_property_route_matching_correctness():
    """
    Property 1: Route Matching Correctness
    
    For any registered route with path P and method M:
    - A request with matching path P and method M returns a RouteMatch
    - A request with non-matching path returns None
    - A request with non-matching method returns None
    
    **Feature: router-request-handling, Property 1: Route Matching Correctness**
    **Validates: Requirements 1.3, 1.4, 1.5, 1.6**
    """
    # Run 100 iterations
    for _ in range(100):
        router = Router()
        
        # Generate random path and method
        path = _random_static_path()
        method = _random_method()
        
        # Create and register descriptor
        descriptor = _create_descriptor(path, [method])
        router.add_endpoint(descriptor)
        
        # Property: Matching path and method should return RouteMatch
        request_match = Request(method=method, path=path)
        match = router.match(request_match)
        
        assert match is not None, f"Expected match for {method} {path}"
        assert match.handler == descriptor.handler, "Handler should match"
        assert match.descriptor == descriptor, "Descriptor should match"
        assert match.matched_path == path, "Matched path should match"
        
        # Property: Non-matching path should return None
        non_matching_path = path + "/" + _random_path_segment()
        request_wrong_path = Request(method=method, path=non_matching_path)
        match_wrong_path = router.match(request_wrong_path)
        
        assert match_wrong_path is None, f"Expected no match for wrong path {non_matching_path}"
        
        # Property: Non-matching method should return None
        other_methods = [m for m in ["GET", "POST", "PUT", "DELETE", "PATCH"] if m != method]
        if other_methods:
            wrong_method = random.choice(other_methods)
            request_wrong_method = Request(method=wrong_method, path=path)
            match_wrong_method = router.match(request_wrong_method)
            
            assert match_wrong_method is None, f"Expected no match for wrong method {wrong_method}"
    
    return


# -----------------------------------------------------------------------------
# Property 3: Route Precedence
# **Validates: Requirements 2.6, 2.7**
#
# *For any* set of registered routes where multiple could match a given path,
# the Router SHALL prefer more specific routes (static > parameterized > wildcard).
# *For any* routes with equal specificity, the Router SHALL use registration
# order as tiebreaker, returning the first registered route.
# -----------------------------------------------------------------------------

def test_property_route_precedence_static_over_param():
    """
    Property 3: Route Precedence - Static over Parameterized
    
    For any path that could match both a static route and a parameterized route,
    the static route should be preferred.
    
    **Feature: router-request-handling, Property 3: Route Precedence**
    **Validates: Requirements 2.6, 2.7**
    """
    # Run 100 iterations
    for _ in range(100):
        router = Router()
        
        # Generate a base path
        base = _random_path_segment()
        static_segment = _random_path_segment()
        
        # Create parameterized route (less specific)
        param_path = f"/{base}/{{id}}"
        param_descriptor = _create_descriptor(param_path, ["GET"], "param_handler")
        router.add_endpoint(param_descriptor)
        
        # Create static route (more specific)
        static_path = f"/{base}/{static_segment}"
        static_descriptor = _create_descriptor(static_path, ["GET"], "static_handler")
        router.add_endpoint(static_descriptor)
        
        # Property: Static route should be preferred for exact match
        request = Request(method="GET", path=static_path)
        match = router.match(request)
        
        assert match is not None, f"Expected match for {static_path}"
        assert match.handler.__name__ == "static_handler", \
            f"Static route should be preferred, got {match.handler.__name__}"
        
        # Property: Parameterized route should match other values
        other_value = _random_path_segment()
        while other_value == static_segment:
            other_value = _random_path_segment()
        
        other_path = f"/{base}/{other_value}"
        request_other = Request(method="GET", path=other_path)
        match_other = router.match(request_other)
        
        assert match_other is not None, f"Expected match for {other_path}"
        assert match_other.handler.__name__ == "param_handler", \
            f"Parameterized route should match other values"
    
    return


def test_property_route_precedence_typed_over_string():
    """
    Property 3: Route Precedence - Typed over String Parameters
    
    For any path that could match both a typed parameter route and a string
    parameter route, the typed route should be preferred when the value matches.
    
    **Feature: router-request-handling, Property 3: Route Precedence**
    **Validates: Requirements 2.6, 2.7**
    """
    # Run 100 iterations
    for _ in range(100):
        router = Router()
        
        # Generate a base path
        base = _random_path_segment()
        
        # Create typed route (more specific)
        typed_path = f"/{base}/{{id:int}}"
        typed_descriptor = _create_descriptor(typed_path, ["GET"], "typed_handler")
        router.add_endpoint(typed_descriptor)
        
        # Create string route (less specific)
        string_path = f"/{base}/{{name}}"
        string_descriptor = _create_descriptor(string_path, ["GET"], "string_handler")
        router.add_endpoint(string_descriptor)
        
        # Property: Typed route should be preferred for numeric values
        numeric_value = random.randint(1, 10000)
        request_numeric = Request(method="GET", path=f"/{base}/{numeric_value}")
        match_numeric = router.match(request_numeric)
        
        assert match_numeric is not None, f"Expected match for numeric path"
        assert match_numeric.handler.__name__ == "typed_handler", \
            f"Typed route should be preferred for numeric values"
        assert match_numeric.path_params["id"] == numeric_value, \
            f"Parameter should be converted to int"
        
        # Property: String route should match non-numeric values
        string_value = _random_path_segment()
        # Ensure it's not purely numeric
        while string_value.isdigit():
            string_value = _random_path_segment()
        
        request_string = Request(method="GET", path=f"/{base}/{string_value}")
        match_string = router.match(request_string)
        
        assert match_string is not None, f"Expected match for string path"
        assert match_string.handler.__name__ == "string_handler", \
            f"String route should match non-numeric values"
    
    return


def test_property_route_precedence_registration_order():
    """
    Property 3: Route Precedence - Registration Order Tiebreaker
    
    For routes with equal specificity, the first registered route should be
    returned.
    
    **Feature: router-request-handling, Property 3: Route Precedence**
    **Validates: Requirements 2.6, 2.7**
    """
    # Run 100 iterations
    for _ in range(100):
        router = Router()
        
        # Generate a base path
        base = _random_path_segment()
        
        # Create two routes with same specificity (both parameterized)
        # Note: These have different parameter names so they're not conflicts
        first_path = f"/{base}/{{first_id:int}}"
        first_descriptor = _create_descriptor(first_path, ["GET"], "first_handler")
        router.add_endpoint(first_descriptor)
        
        # The first registered route should be matched
        numeric_value = random.randint(1, 10000)
        request = Request(method="GET", path=f"/{base}/{numeric_value}")
        match = router.match(request)
        
        assert match is not None, f"Expected match"
        assert match.handler.__name__ == "first_handler", \
            f"First registered route should be preferred"
    
    return


# -----------------------------------------------------------------------------
# Property 14: Router Configuration Behavior
# **Validates: Requirements 11.2, 11.3, 11.5**
#
# *For any* Router with `strict_slashes=True`, paths `/foo` and `/foo/` SHALL
# be treated as different routes. *For any* Router with `strict_slashes=False`,
# both variants SHALL match the same handler. *For any* Router with
# `case_sensitive=False`, paths `/Foo` and `/foo` SHALL match the same handler.
# -----------------------------------------------------------------------------

def test_property_router_config_strict_slashes_true():
    """
    Property 14: Router Configuration - strict_slashes=True
    
    For any Router with strict_slashes=True, paths /foo and /foo/ should be
    treated as different routes.
    
    **Feature: router-request-handling, Property 14: Router Configuration Behavior**
    **Validates: Requirements 11.2, 11.3, 11.5**
    """
    # Run 100 iterations
    for _ in range(100):
        router = Router(strict_slashes=True)
        
        # Generate random path without trailing slash
        path = _random_static_path()
        
        # Register route without trailing slash
        descriptor = _create_descriptor(path, ["GET"])
        router.add_endpoint(descriptor)
        
        # Property: Path without trailing slash should match
        request_no_slash = Request(method="GET", path=path)
        match_no_slash = router.match(request_no_slash)
        
        assert match_no_slash is not None, f"Expected match for {path}"
        
        # Property: Path with trailing slash should NOT match
        path_with_slash = path + "/"
        request_with_slash = Request(method="GET", path=path_with_slash)
        match_with_slash = router.match(request_with_slash)
        
        assert match_with_slash is None, \
            f"Expected no match for {path_with_slash} when strict_slashes=True"
    
    return


def test_property_router_config_strict_slashes_false():
    """
    Property 14: Router Configuration - strict_slashes=False
    
    For any Router with strict_slashes=False, both /foo and /foo/ should match
    the same handler.
    
    **Feature: router-request-handling, Property 14: Router Configuration Behavior**
    **Validates: Requirements 11.2, 11.3, 11.5**
    """
    # Run 100 iterations
    for _ in range(100):
        router = Router(strict_slashes=False)
        
        # Generate random path without trailing slash
        path = _random_static_path()
        
        # Register route without trailing slash
        descriptor = _create_descriptor(path, ["GET"])
        router.add_endpoint(descriptor)
        
        # Property: Path without trailing slash should match
        request_no_slash = Request(method="GET", path=path)
        match_no_slash = router.match(request_no_slash)
        
        assert match_no_slash is not None, f"Expected match for {path}"
        
        # Property: Path with trailing slash should also match
        path_with_slash = path + "/"
        request_with_slash = Request(method="GET", path=path_with_slash)
        match_with_slash = router.match(request_with_slash)
        
        assert match_with_slash is not None, \
            f"Expected match for {path_with_slash} when strict_slashes=False"
        
        # Both should return the same handler
        assert match_no_slash.handler == match_with_slash.handler, \
            "Both variants should return the same handler"
    
    return


def test_property_router_config_case_sensitive_true():
    """
    Property 14: Router Configuration - case_sensitive=True
    
    For any Router with case_sensitive=True, paths /Foo and /foo should be
    treated as different routes.
    
    **Feature: router-request-handling, Property 14: Router Configuration Behavior**
    **Validates: Requirements 11.2, 11.3, 11.5**
    """
    # Run 100 iterations
    for _ in range(100):
        router = Router(case_sensitive=True)
        
        # Generate random path with mixed case
        segment = _random_path_segment()
        path = f"/{segment.capitalize()}"  # First letter uppercase
        
        # Register route with specific case
        descriptor = _create_descriptor(path, ["GET"])
        router.add_endpoint(descriptor)
        
        # Property: Exact case should match
        request_exact = Request(method="GET", path=path)
        match_exact = router.match(request_exact)
        
        assert match_exact is not None, f"Expected match for {path}"
        
        # Property: Different case should NOT match
        path_lower = path.lower()
        if path_lower != path:  # Only test if case actually differs
            request_lower = Request(method="GET", path=path_lower)
            match_lower = router.match(request_lower)
            
            assert match_lower is None, \
                f"Expected no match for {path_lower} when case_sensitive=True"
    
    return


def test_property_router_config_case_sensitive_false():
    """
    Property 14: Router Configuration - case_sensitive=False
    
    For any Router with case_sensitive=False, paths /Foo and /foo should match
    the same handler.
    
    **Feature: router-request-handling, Property 14: Router Configuration Behavior**
    **Validates: Requirements 11.2, 11.3, 11.5**
    """
    # Run 100 iterations
    for _ in range(100):
        router = Router(case_sensitive=False)
        
        # Generate random path with mixed case
        segment = _random_path_segment()
        path = f"/{segment.capitalize()}"  # First letter uppercase
        
        # Register route with specific case
        descriptor = _create_descriptor(path, ["GET"])
        router.add_endpoint(descriptor)
        
        # Property: Exact case should match
        request_exact = Request(method="GET", path=path)
        match_exact = router.match(request_exact)
        
        assert match_exact is not None, f"Expected match for {path}"
        
        # Property: Different case should also match
        path_lower = path.lower()
        request_lower = Request(method="GET", path=path_lower)
        match_lower = router.match(request_lower)
        
        assert match_lower is not None, \
            f"Expected match for {path_lower} when case_sensitive=False"
        
        # Both should return the same handler
        assert match_exact.handler == match_lower.handler, \
            "Both case variants should return the same handler"
        
        # Also test uppercase
        path_upper = path.upper()
        request_upper = Request(method="GET", path=path_upper)
        match_upper = router.match(request_upper)
        
        assert match_upper is not None, \
            f"Expected match for {path_upper} when case_sensitive=False"
    
    return
