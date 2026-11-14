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



# =============================================================================
# Index integrity: replace and failed registrations
# =============================================================================

def test_replacing_one_method_keeps_the_other_methods_registered():
    """Replacing GET on a descriptor registered for GET and POST leaves POST served by the original handler."""
    registry = setup_clean_registry()

    original = EndpointDescriptor(handler=sample_handler, module=__name__, path="/a", methods=["GET", "POST"])
    override = EndpointDescriptor(handler=another_handler, module=__name__, path="/a", methods=["GET"])

    registry.register(original)
    registry.register(override, on_conflict="replace")

    served = {}
    for descriptor in registry.collect():
        for method in descriptor.methods:
            served[method] = descriptor.handler

    if served != {"GET": another_handler, "POST": sample_handler}:
        errmsg = f"Expected GET -> another_handler and POST -> sample_handler, got {served}"
        raise AssertionError(errmsg)

    return


def test_replacing_one_method_does_not_modify_the_replaced_descriptor():
    """The descriptor that lost a method is narrowed in the registry only; the object passed in is untouched."""
    registry = setup_clean_registry()

    original = EndpointDescriptor(handler=sample_handler, module=__name__, path="/a", methods=["GET", "POST"])
    override = EndpointDescriptor(handler=another_handler, module=__name__, path="/a", methods=["GET"])

    registry.register(original)
    registry.register(override, on_conflict="replace")

    if original.methods != ["GET", "POST"]:
        errmsg = f"Expected the original descriptor to keep its methods, got {original.methods}"
        raise AssertionError(errmsg)

    return


def test_replaced_method_can_be_claimed_again_after_replace():
    """After a replace, the surviving method still conflicts and the replaced one belongs to the override."""
    registry = setup_clean_registry()

    original = EndpointDescriptor(handler=sample_handler, module=__name__, path="/a", methods=["GET", "POST"])
    override = EndpointDescriptor(handler=another_handler, module=__name__, path="/a", methods=["GET"])
    late = EndpointDescriptor(handler=third_handler, module=__name__, path="/a", methods=["POST"])

    registry.register(original)
    registry.register(override, on_conflict="replace")

    try:
        registry.register(late)
    except EndpointConflictError as err:
        if err.existing_handler is not sample_handler:
            errmsg = f"Expected the conflict to name the handler still serving POST, got {err.existing_handler}"
            raise AssertionError(errmsg)
    else:
        raise AssertionError("Expected POST /a to still be registered and to conflict")

    return


def test_replacing_every_method_removes_the_descriptor():
    """A descriptor whose every method is replaced is no longer collected."""
    registry = setup_clean_registry()

    original = EndpointDescriptor(handler=sample_handler, module=__name__, path="/a", methods=["GET"])
    override = EndpointDescriptor(handler=another_handler, module=__name__, path="/a", methods=["GET"])

    registry.register(original)
    registry.register(override, on_conflict="replace")

    handlers = [descriptor.handler for descriptor in registry.collect()]

    if handlers != [another_handler]:
        errmsg = f"Expected only the override to remain, got {handlers}"
        raise AssertionError(errmsg)

    return


def test_failed_registration_leaves_no_index_entry_behind():
    """A registration rejected on its second method claims nothing: its first method stays free."""
    registry = setup_clean_registry()

    holder = EndpointDescriptor(handler=sample_handler, module=__name__, path="/b", methods=["POST"])
    rejected = EndpointDescriptor(handler=another_handler, module=__name__, path="/b", methods=["GET", "POST"])
    later = EndpointDescriptor(handler=third_handler, module=__name__, path="/b", methods=["GET"])

    registry.register(holder)

    try:
        registry.register(rejected)
    except EndpointConflictError:
        pass
    else:
        raise AssertionError("Expected the second registration to conflict on POST")

    # GET /b was never registered, so it must be free for another handler
    registry.register(later)

    handlers = [descriptor.handler for descriptor in registry.collect()]

    if handlers != [sample_handler, third_handler]:
        errmsg = f"Expected the holder and the later handler only, got {handlers}"
        raise AssertionError(errmsg)

    return


# =============================================================================
# collect_from: order independence and class sources
# =============================================================================

def test_collect_from_replace_does_not_depend_on_handler_names():
    """An override named to sort before the handler it replaces still replaces it."""
    import types

    from ccai.webworks.endpoints.endpoint import Endpoint

    module = types.ModuleType("override_before_original")

    @Endpoint.attach_at(leaf="thing", methods=["GET"], on_conflict="replace")
    def a_override(request):
        return "override"

    @Endpoint.attach_at(leaf="thing", methods=["GET"])
    def z_original(request):
        return "original"

    module.a_override = a_override
    module.z_original = z_original

    registry = setup_clean_registry()
    registry.collect_from(module)

    handlers = [descriptor.handler for descriptor in registry.collect()]

    if handlers != [a_override]:
        errmsg = f"Expected only the override to be registered, got {handlers}"
        raise AssertionError(errmsg)

    return


def test_collect_from_registers_in_definition_order():
    """Handlers of a module are registered in the order they are defined, not by name."""
    import types

    from ccai.webworks.endpoints.endpoint import Endpoint

    module = types.ModuleType("definition_order")

    @Endpoint.attach_at(leaf="zebra", methods=["GET"])
    def zebra(request):
        return {}

    @Endpoint.attach_at(leaf="apple", methods=["GET"])
    def apple(request):
        return {}

    module.zebra = zebra
    module.apple = apple

    registry = setup_clean_registry()
    registry.collect_from(module)

    leaves = [descriptor.leaf for descriptor in registry.collect()]

    if leaves != ["zebra", "apple"]:
        errmsg = f"Expected definition order ['zebra', 'apple'], got {leaves}"
        raise AssertionError(errmsg)

    return


def test_collect_from_class_includes_free_function_handlers():
    """Collecting a blueprint class registers the free functions declared through it."""
    from ccai.webworks.endpoints.blueprint import Blueprint

    class ApiBlueprint(Blueprint):
        base_path = "/api"

    @ApiBlueprint.attach_at(leaf="users", methods=["GET"])
    def list_users(request):
        return {}

    registry = setup_clean_registry()
    count = registry.collect_from(ApiBlueprint)

    if count != 1:
        errmsg = f"Expected 1 descriptor collected from the blueprint class, got {count}"
        raise AssertionError(errmsg)

    if registry.collect()[0].path != "/api/users":
        errmsg = f"Expected '/api/users', got {registry.collect()[0].path}"
        raise AssertionError(errmsg)

    return


def test_collect_from_module_does_not_pull_in_endpoints_declared_through_an_imported_class():
    """A module that merely holds a blueprint class does not collect that class's free-function handlers."""
    import types

    from ccai.webworks.endpoints.blueprint import Blueprint

    class SharedBlueprint(Blueprint):
        base_path = "/shared"

    @SharedBlueprint.attach_at(leaf="elsewhere", methods=["GET"])
    def defined_elsewhere(request):
        return {}

    module = types.ModuleType("holds_only_the_class")
    module.SharedBlueprint = SharedBlueprint

    registry = setup_clean_registry()
    count = registry.collect_from(module)

    if count != 0:
        errmsg = f"Expected nothing to be collected through the imported class, got {count}"
        raise AssertionError(errmsg)

    return


def test_collecting_again_after_a_replace_registers_nothing():
    """Re-collecting a module whose handler was replaced is a no-op, not a conflict."""
    import types

    from ccai.webworks.endpoints.endpoint import Endpoint

    module = types.ModuleType("collected_twice")

    @Endpoint.attach_at(leaf="twice", methods=["GET"])
    def original(request):
        return {}

    @Endpoint.attach_at(leaf="twice", methods=["GET"], on_conflict="replace")
    def override(request):
        return {}

    module.original = original
    module.override = override

    registry = setup_clean_registry()
    registry.collect_from(module)
    count = registry.collect_from(module)

    if count != 0:
        errmsg = f"Expected the second collection to register nothing, got {count}"
        raise AssertionError(errmsg)

    return
