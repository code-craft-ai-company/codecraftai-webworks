"""
    Tests for the EndpointRegistry class.
    
    This module contains unit tests for the endpoint registry that collects
    all endpoint descriptors from attach_at/attach_child calls.
"""

from ccai.webworks.endpoints.registry import EndpointRegistry, EndpointConflictError
from ccai.webworks.endpoints.descriptor import EndpointDescriptor
from ccai.webworks.endpoints.constraints import EndpointConstraints
from ccai.webworks.endpoints.accesspolicy import AccessPolicy
from ccai.webworks.endpoints.ratelimit import RateLimit


# =============================================================================
# Helper Functions for Testing
# =============================================================================

def sample_handler():
    """Sample handler function for testing."""
    return "response"


def another_handler():
    """Another sample handler function for testing."""
    return "another response"


def third_handler():
    """Third sample handler function for testing."""
    return "third response"


def setup_clean_registry():
    """Clear the registry before each test."""
    return EndpointRegistry()


# =============================================================================
# Unit Tests for EndpointRegistry - Basic Registration
# =============================================================================

def test_registry_register_single_descriptor():
    """
        Test that a single descriptor can be registered.
    """
    registry = setup_clean_registry()
    descriptor = EndpointDescriptor(
        handler=sample_handler,
        module="test_module",
        leaf="status",
        methods=["GET"]
    )
    
    registry.register(descriptor)
    
    collected = registry.collect()
    
    if len(collected) != 1:
        errmsg = f"Expected 1 descriptor, got {len(collected)}"
        raise AssertionError(errmsg)
    
    if collected[0] is not descriptor:
        errmsg = "Expected collected descriptor to be the same object"
        raise AssertionError(errmsg)
    
    return


def test_registry_register_multiple_descriptors():
    """
        Test that multiple descriptors can be registered.
    """
    registry = setup_clean_registry()
    descriptor1 = EndpointDescriptor(
        handler=sample_handler,
        module="test_module",
        leaf="status",
        methods=["GET"]
    )
    
    descriptor2 = EndpointDescriptor(
        handler=another_handler,
        module="test_module",
        leaf="health",
        methods=["GET"]
    )
    
    registry.register(descriptor1)
    registry.register(descriptor2)
    
    collected = registry.collect()
    
    if len(collected) != 2:
        errmsg = f"Expected 2 descriptors, got {len(collected)}"
        raise AssertionError(errmsg)
    
    return


def test_registry_collect_returns_copy():
    """
        Test that collect() returns a copy of the descriptors list.
    """
    registry = setup_clean_registry()
    descriptor = EndpointDescriptor(
        handler=sample_handler,
        module="test_module",
        leaf="status",
        methods=["GET"]
    )
    
    registry.register(descriptor)
    
    collected1 = registry.collect()
    collected2 = registry.collect()
    
    if collected1 is collected2:
        errmsg = "Expected collect() to return different list objects"
        raise AssertionError(errmsg)
    
    # Modifying the returned list should not affect the registry
    collected1.clear()
    
    collected3 = registry.collect()
    if len(collected3) != 1:
        errmsg = f"Expected 1 descriptor after clearing returned list, got {len(collected3)}"
        raise AssertionError(errmsg)
    
    return


def test_registry_clear():
    """
        Test that clear() removes all registered descriptors.
    """
    registry = setup_clean_registry()
    descriptor = EndpointDescriptor(
        handler=sample_handler,
        module="test_module",
        leaf="status",
        methods=["GET"]
    )
    
    registry.register(descriptor)
    
    if len(registry.collect()) != 1:
        errmsg = "Expected 1 descriptor before clear"
        raise AssertionError(errmsg)
    
    registry = EndpointRegistry()
    if len(registry.collect()) != 0:
        errmsg = f"Expected 0 descriptors after clear, got {len(registry.collect())}"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for EndpointRegistry - Conflict Detection
# =============================================================================

def test_registry_conflict_same_path_method():
    """
        Test that registering the same path+method raises EndpointConflictError.
    """
    registry = setup_clean_registry()
    descriptor1 = EndpointDescriptor(
        handler=sample_handler,
        module="test_module",
        leaf="status",
        methods=["GET"]
    )
    
    descriptor2 = EndpointDescriptor(
        handler=another_handler,
        module="test_module",
        leaf="status",
        methods=["GET"]
    )
    
    registry.register(descriptor1)
    
    try:
        registry.register(descriptor2)
        raise AssertionError("Expected EndpointConflictError to be raised")
    except EndpointConflictError as e:
        if e.path != "/status":
            errmsg = f"Expected path '/status', got {e.path}"
            raise AssertionError(errmsg)
        if e.method != "GET":
            errmsg = f"Expected method 'GET', got {e.method}"
            raise AssertionError(errmsg)
    
    return


def test_registry_conflict_different_methods_allowed():
    """
        Test that same path with different methods is allowed.
    """
    registry = setup_clean_registry()
    descriptor1 = EndpointDescriptor(
        handler=sample_handler,
        module="test_module",
        leaf="resource",
        methods=["GET"]
    )
    
    descriptor2 = EndpointDescriptor(
        handler=another_handler,
        module="test_module",
        leaf="resource",
        methods=["POST"]
    )
    
    registry.register(descriptor1)
    registry.register(descriptor2)
    
    collected = registry.collect()
    
    if len(collected) != 2:
        errmsg = f"Expected 2 descriptors, got {len(collected)}"
        raise AssertionError(errmsg)
    
    return


def test_registry_conflict_multiple_methods():
    """
        Test conflict detection with multiple methods on a descriptor.
    """
    registry = setup_clean_registry()
    descriptor1 = EndpointDescriptor(
        handler=sample_handler,
        module="test_module",
        leaf="resource",
        methods=["GET", "POST"]
    )
    
    descriptor2 = EndpointDescriptor(
        handler=another_handler,
        module="test_module",
        leaf="resource",
        methods=["POST"]  # Conflicts with POST from descriptor1
    )
    
    registry.register(descriptor1)
    
    try:
        registry.register(descriptor2)
        raise AssertionError("Expected EndpointConflictError to be raised")
    except EndpointConflictError as e:
        if e.method != "POST":
            errmsg = f"Expected method 'POST', got {e.method}"
            raise AssertionError(errmsg)
    
    return


def test_registry_on_conflict_replace():
    """
        Test that on_conflict='replace' allows overriding existing registration.
    """
    registry = setup_clean_registry()
    descriptor1 = EndpointDescriptor(
        handler=sample_handler,
        module="test_module",
        leaf="status",
        methods=["GET"]
    )
    
    descriptor2 = EndpointDescriptor(
        handler=another_handler,
        module="test_module",
        leaf="status",
        methods=["GET"]
    )
    
    registry.register(descriptor1)
    registry.register(descriptor2, on_conflict="replace")
    
    collected = registry.collect()
    
    if len(collected) != 1:
        errmsg = f"Expected 1 descriptor after replace, got {len(collected)}"
        raise AssertionError(errmsg)
    
    if collected[0].handler is not another_handler:
        errmsg = "Expected handler to be another_handler after replace"
        raise AssertionError(errmsg)
    
    return


def test_registry_conflict_with_path():
    """
        Test conflict detection using path instead of leaf.
    """
    registry = setup_clean_registry()
    descriptor1 = EndpointDescriptor(
        handler=sample_handler,
        module="test_module",
        path="/api/v1/status",
        methods=["GET"]
    )
    
    descriptor2 = EndpointDescriptor(
        handler=another_handler,
        module="test_module",
        path="/api/v1/status",
        methods=["GET"]
    )
    
    registry.register(descriptor1)
    
    try:
        registry.register(descriptor2)
        raise AssertionError("Expected EndpointConflictError to be raised")
    except EndpointConflictError as e:
        if e.path != "/api/v1/status":
            errmsg = f"Expected path '/api/v1/status', got {e.path}"
            raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for EndpointConflictError
# =============================================================================

def test_endpoint_conflict_error_attributes():
    """
        Test that EndpointConflictError has correct attributes.
    """
    error = EndpointConflictError(
        path="/status",
        method="GET",
        existing_handler=sample_handler,
        new_handler=another_handler
    )
    
    if error.path != "/status":
        errmsg = f"Expected path '/status', got {error.path}"
        raise AssertionError(errmsg)
    
    if error.method != "GET":
        errmsg = f"Expected method 'GET', got {error.method}"
        raise AssertionError(errmsg)
    
    if error.existing_handler is not sample_handler:
        errmsg = "Expected existing_handler to be sample_handler"
        raise AssertionError(errmsg)
    
    if error.new_handler is not another_handler:
        errmsg = "Expected new_handler to be another_handler"
        raise AssertionError(errmsg)
    
    return


def test_endpoint_conflict_error_message():
    """
        Test that EndpointConflictError has informative message.
    """
    error = EndpointConflictError(
        path="/status",
        method="GET",
        existing_handler=sample_handler,
        new_handler=another_handler
    )
    
    message = str(error)
    
    if "GET" not in message:
        errmsg = f"Expected 'GET' in error message, got {message}"
        raise AssertionError(errmsg)
    
    if "/status" not in message:
        errmsg = f"Expected '/status' in error message, got {message}"
        raise AssertionError(errmsg)
    
    if "sample_handler" not in message:
        errmsg = f"Expected 'sample_handler' in error message, got {message}"
        raise AssertionError(errmsg)
    
    if "another_handler" not in message:
        errmsg = f"Expected 'another_handler' in error message, got {message}"
        raise AssertionError(errmsg)
    
    return



# =============================================================================
# Unit Tests for EndpointRegistry - export_security_map
# =============================================================================

def test_export_security_map_markdown_empty():
    """
        Test export_security_map with no registered endpoints.
    """
    registry = setup_clean_registry()
    result = registry.export_security_map(format="markdown")
    
    if "No endpoints registered" not in result:
        errmsg = f"Expected 'No endpoints registered' message, got {result}"
        raise AssertionError(errmsg)
    
    return


def test_export_security_map_markdown_basic():
    """
        Test export_security_map generates markdown table.
    """
    registry = setup_clean_registry()
    descriptor = EndpointDescriptor(
        handler=sample_handler,
        module="test_module",
        leaf="status",
        methods=["GET"],
        tags=["api"]
    )
    
    registry.register(descriptor)
    
    result = registry.export_security_map(format="markdown")
    
    if "| path |" not in result:
        errmsg = f"Expected markdown header, got {result}"
        raise AssertionError(errmsg)
    
    if "/status" not in result:
        errmsg = f"Expected '/status' in result, got {result}"
        raise AssertionError(errmsg)
    
    if "GET" not in result:
        errmsg = f"Expected 'GET' in result, got {result}"
        raise AssertionError(errmsg)
    
    return


def test_export_security_map_csv():
    """
        Test export_security_map generates CSV format.
    """
    registry = setup_clean_registry()
    descriptor = EndpointDescriptor(
        handler=sample_handler,
        module="test_module",
        leaf="status",
        methods=["GET"]
    )
    
    registry.register(descriptor)
    
    result = registry.export_security_map(format="csv")
    
    if "path,methods,handler" not in result:
        errmsg = f"Expected CSV header, got {result}"
        raise AssertionError(errmsg)
    
    if "/status" not in result:
        errmsg = f"Expected '/status' in result, got {result}"
        raise AssertionError(errmsg)
    
    return


def test_export_security_map_json():
    """
        Test export_security_map generates JSON format.
    """
    registry = setup_clean_registry()
    descriptor = EndpointDescriptor(
        handler=sample_handler,
        module="test_module",
        leaf="status",
        methods=["GET"]
    )
    
    registry.register(descriptor)
    
    result = registry.export_security_map(format="json")
    
    import json
    parsed = json.loads(result)
    
    if not isinstance(parsed, list):
        errmsg = f"Expected JSON array, got {type(parsed)}"
        raise AssertionError(errmsg)
    
    if len(parsed) != 1:
        errmsg = f"Expected 1 item in JSON array, got {len(parsed)}"
        raise AssertionError(errmsg)
    
    if parsed[0]["path"] != "/status":
        errmsg = f"Expected path '/status', got {parsed[0]['path']}"
        raise AssertionError(errmsg)
    
    return


def test_export_security_map_filter_tag():
    """
        Test export_security_map filters by tag.
    """
    registry = setup_clean_registry()
    descriptor1 = EndpointDescriptor(
        handler=sample_handler,
        module="test_module",
        leaf="admin",
        methods=["GET"],
        tags=["admin", "api"]
    )
    
    descriptor2 = EndpointDescriptor(
        handler=another_handler,
        module="test_module",
        leaf="public",
        methods=["GET"],
        tags=["public", "api"]
    )
    
    registry.register(descriptor1)
    registry.register(descriptor2)
    
    # Filter by admin tag
    result = registry.export_security_map(filter_tag="admin", format="json")
    
    import json
    parsed = json.loads(result)
    
    if len(parsed) != 1:
        errmsg = f"Expected 1 item after filtering, got {len(parsed)}"
        raise AssertionError(errmsg)
    
    if parsed[0]["path"] != "/admin":
        errmsg = f"Expected path '/admin', got {parsed[0]['path']}"
        raise AssertionError(errmsg)
    
    return


def test_export_security_map_filter_tag_no_match():
    """
        Test export_security_map with filter that matches nothing.
    """
    registry = setup_clean_registry()
    descriptor = EndpointDescriptor(
        handler=sample_handler,
        module="test_module",
        leaf="status",
        methods=["GET"],
        tags=["api"]
    )
    
    registry.register(descriptor)
    
    result = registry.export_security_map(filter_tag="nonexistent", format="json")
    
    import json
    parsed = json.loads(result)
    
    if len(parsed) != 0:
        errmsg = f"Expected 0 items after filtering, got {len(parsed)}"
        raise AssertionError(errmsg)
    
    return


def test_export_security_map_with_constraints():
    """
        Test export_security_map includes constraint information.
    """
    registry = setup_clean_registry()
    policy = AccessPolicy(roles=["admin"], scopes=["read"], require_auth=True)
    limit = RateLimit(requests=100, window=60)
    constraints = EndpointConstraints(
        access_policy=policy,
        rate_limit=limit,
        roles=["admin"],
        scopes=["read"]
    )
    
    descriptor = EndpointDescriptor(
        handler=sample_handler,
        module="test_module",
        leaf="admin",
        methods=["GET"],
        constraints=constraints
    )
    
    registry.register(descriptor)
    
    result = registry.export_security_map(format="json")
    
    import json
    parsed = json.loads(result)
    
    if "admin" not in parsed[0]["roles"]:
        errmsg = f"Expected 'admin' in roles, got {parsed[0]['roles']}"
        raise AssertionError(errmsg)
    
    if "read" not in parsed[0]["scopes"]:
        errmsg = f"Expected 'read' in scopes, got {parsed[0]['scopes']}"
        raise AssertionError(errmsg)
    
    if "100/60s" not in parsed[0]["rate_limit"]:
        errmsg = f"Expected '100/60s' in rate_limit, got {parsed[0]['rate_limit']}"
        raise AssertionError(errmsg)
    
    return


def test_export_security_map_invalid_format():
    """
        Test export_security_map raises error for invalid format.
    """
    registry = setup_clean_registry()
    try:
        registry.export_security_map(format="invalid")
        raise AssertionError("Expected ValueError to be raised")
    except ValueError as e:
        if "Unsupported format" not in str(e):
            errmsg = f"Expected 'Unsupported format' in error message, got {str(e)}"
            raise AssertionError(errmsg)
    
    return


def test_export_security_map_multiple_endpoints():
    """
        Test export_security_map with multiple endpoints.
    """
    registry = setup_clean_registry()
    descriptor1 = EndpointDescriptor(
        handler=sample_handler,
        module="test_module",
        leaf="status",
        methods=["GET"],
        tags=["api"]
    )
    
    descriptor2 = EndpointDescriptor(
        handler=another_handler,
        module="test_module",
        path="/api/v1/users",
        methods=["GET", "POST"],
        tags=["api", "users"]
    )
    
    descriptor3 = EndpointDescriptor(
        handler=third_handler,
        module="test_module",
        leaf="health",
        methods=["GET"],
        tags=["monitoring"]
    )
    
    registry.register(descriptor1)
    registry.register(descriptor2)
    registry.register(descriptor3)
    
    result = registry.export_security_map(format="json")
    
    import json
    parsed = json.loads(result)
    
    if len(parsed) != 3:
        errmsg = f"Expected 3 items, got {len(parsed)}"
        raise AssertionError(errmsg)
    
    paths = [item["path"] for item in parsed]
    
    if "/status" not in paths:
        errmsg = f"Expected '/status' in paths, got {paths}"
        raise AssertionError(errmsg)
    
    if "/api/v1/users" not in paths:
        errmsg = f"Expected '/api/v1/users' in paths, got {paths}"
        raise AssertionError(errmsg)
    
    if "/health" not in paths:
        errmsg = f"Expected '/health' in paths, got {paths}"
        raise AssertionError(errmsg)
    
    return

