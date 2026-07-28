"""
.. module:: test_blueprint
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Tests for the Blueprint class.

.. moduleauthor:: Code Craft AI LLC
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []

from ccai.webworks.endpoints import (
    AccessPolicy,
    Blueprint,
    Doc,
    Endpoint,
    EndpointDescriptor,
    EndpointRegistry,
    RateLimit,
)


# =============================================================================
# Test Setup - Clear registry before each test
# =============================================================================

def _clear_registry():
    """Helper to clear the registry before tests."""
    registry = EndpointRegistry()
    # Also clear the blueprint's internal descriptor cache
    Blueprint._blueprint_descriptors.clear()


# =============================================================================
# Task 6.1: Blueprint class extending Endpoint
# =============================================================================

def test_blueprint_extends_endpoint():
    """Test that Blueprint class extends Endpoint."""
    _clear_registry()
    
    if not issubclass(Blueprint, Endpoint):
        raise AssertionError("Blueprint should be a subclass of Endpoint")
    
    return


def test_blueprint_has_base_path_attribute():
    """Test that Blueprint has base_path class attribute."""
    _clear_registry()
    
    if not hasattr(Blueprint, "base_path"):
        raise AssertionError("Blueprint missing 'base_path' attribute")
    
    if Blueprint.base_path is not None:
        raise AssertionError(f"Expected base_path=None, got {Blueprint.base_path}")
    
    return


def test_blueprint_has_base_leaf_attribute():
    """Test that Blueprint has base_leaf class attribute."""
    _clear_registry()
    
    if not hasattr(Blueprint, "base_leaf"):
        raise AssertionError("Blueprint missing 'base_leaf' attribute")
    
    if Blueprint.base_leaf is not None:
        raise AssertionError(f"Expected base_leaf=None, got {Blueprint.base_leaf}")
    
    return


def test_blueprint_has_merge_tags_attribute():
    """Test that Blueprint has merge_tags class attribute."""
    _clear_registry()
    
    if not hasattr(Blueprint, "merge_tags"):
        raise AssertionError("Blueprint missing 'merge_tags' attribute")
    
    if Blueprint.merge_tags is not False:
        raise AssertionError(f"Expected merge_tags=False, got {Blueprint.merge_tags}")
    
    return


def test_blueprint_subclass_can_set_base_path():
    """Test that Blueprint subclass can set base_path."""
    _clear_registry()
    
    class ApiBlueprint(Blueprint):
        base_path = "/api/v1"
    
    if ApiBlueprint.base_path != "/api/v1":
        raise AssertionError(f"Expected base_path='/api/v1', got {ApiBlueprint.base_path}")
    
    # Verify base class is unchanged
    if Blueprint.base_path is not None:
        raise AssertionError("Base Blueprint.base_path should still be None")
    
    return


def test_blueprint_subclass_can_set_base_leaf():
    """Test that Blueprint subclass can set base_leaf."""
    _clear_registry()
    
    class ApiBlueprint(Blueprint):
        base_leaf = "api"
    
    if ApiBlueprint.base_leaf != "api":
        raise AssertionError(f"Expected base_leaf='api', got {ApiBlueprint.base_leaf}")
    
    return


def test_blueprint_subclass_can_set_merge_tags():
    """Test that Blueprint subclass can set merge_tags."""
    _clear_registry()
    
    class ApiBlueprint(Blueprint):
        merge_tags = True
    
    if ApiBlueprint.merge_tags is not True:
        raise AssertionError(f"Expected merge_tags=True, got {ApiBlueprint.merge_tags}")
    
    return


def test_blueprint_inherits_endpoint_attributes():
    """Test that Blueprint inherits all Endpoint class attributes."""
    _clear_registry()
    
    # Verify inherited attributes exist
    if not hasattr(Blueprint, "access_policy"):
        raise AssertionError("Blueprint missing inherited 'access_policy' attribute")
    
    if not hasattr(Blueprint, "rate_limit"):
        raise AssertionError("Blueprint missing inherited 'rate_limit' attribute")
    
    if not hasattr(Blueprint, "methods"):
        raise AssertionError("Blueprint missing inherited 'methods' attribute")
    
    if not hasattr(Blueprint, "version"):
        raise AssertionError("Blueprint missing inherited 'version' attribute")
    
    if not hasattr(Blueprint, "tags"):
        raise AssertionError("Blueprint missing inherited 'tags' attribute")
    
    if not hasattr(Blueprint, "serializers"):
        raise AssertionError("Blueprint missing inherited 'serializers' attribute")
    
    return


def test_blueprint_subclass_can_set_constraints():
    """Test that Blueprint subclass can set access_policy and rate_limit."""
    _clear_registry()
    
    class SecureBlueprint(Blueprint):
        base_path = "/api/secure"
        access_policy = AccessPolicy(roles=["admin"])
        rate_limit = RateLimit(requests=100, window=60)
    
    if SecureBlueprint.access_policy.roles != ("admin",):
        raise AssertionError(f"Expected roles=['admin'], got {SecureBlueprint.access_policy.roles}")
    
    if SecureBlueprint.rate_limit.requests != 100:
        raise AssertionError(f"Expected requests=100, got {SecureBlueprint.rate_limit.requests}")
    
    return


# =============================================================================
# Task 6.1: Blueprint attach_at computes paths relative to base
# =============================================================================

def test_blueprint_attach_at_computes_path_from_base_path():
    """Test that Blueprint.attach_at computes path relative to base_path."""
    registry = EndpointRegistry()
    _clear_registry()
    
    class ApiBlueprint(Blueprint):
        base_path = "/api/v1"
    
    @ApiBlueprint.attach_at(leaf="users")
    def list_users():
        pass
    
    registry.collect_from(list_users)
    descriptors = registry.collect()
    
    if len(descriptors) != 1:
        raise AssertionError(f"Expected 1 descriptor, got {len(descriptors)}")
    
    desc = descriptors[0]
    
    if desc.path != "/api/v1/users":
        raise AssertionError(f"Expected path='/api/v1/users', got {desc.path}")
    
    return


def test_blueprint_attach_at_computes_path_from_base_leaf():
    """Test that Blueprint.attach_at computes path relative to base_leaf."""
    registry = EndpointRegistry()
    _clear_registry()
    
    class ApiBlueprint(Blueprint):
        base_leaf = "api"
    
    @ApiBlueprint.attach_at(leaf="status")
    def get_status():
        pass
    
    registry.collect_from(get_status)
    descriptors = registry.collect()
    desc = descriptors[0]
    
    if desc.path != "/api/status":
        raise AssertionError(f"Expected path='/api/status', got {desc.path}")
    
    return


def test_blueprint_attach_at_with_nested_path():
    """Test that Blueprint.attach_at handles nested paths correctly."""
    registry = EndpointRegistry()
    _clear_registry()
    
    class ApiBlueprint(Blueprint):
        base_path = "/api/v1"
    
    @ApiBlueprint.attach_at(path="/users/profile")
    def get_profile():
        pass
    
    registry.collect_from(get_profile)
    descriptors = registry.collect()
    desc = descriptors[0]
    
    if desc.path != "/api/v1/users/profile":
        raise AssertionError(f"Expected path='/api/v1/users/profile', got {desc.path}")
    
    return


def test_blueprint_attach_at_inherits_constraints():
    """Test that Blueprint.attach_at inherits blueprint constraints."""
    registry = EndpointRegistry()
    _clear_registry()
    
    class SecureBlueprint(Blueprint):
        base_path = "/api/secure"
        access_policy = AccessPolicy(roles=["admin"])
        rate_limit = RateLimit(requests=50, window=30)
    
    @SecureBlueprint.attach_at(leaf="data")
    def get_data():
        pass
    
    registry.collect_from(get_data)
    descriptors = registry.collect()
    desc = descriptors[0]
    
    if desc.constraints.access_policy.roles != ("admin",):
        raise AssertionError(f"Expected roles=['admin'], got {desc.constraints.access_policy.roles}")
    
    if desc.constraints.rate_limit.requests != 50:
        raise AssertionError(f"Expected requests=50, got {desc.constraints.rate_limit.requests}")
    
    return


def test_blueprint_attach_at_merge_tags_false():
    """Test that Blueprint.attach_at with merge_tags=False uses child tags."""
    registry = EndpointRegistry()
    _clear_registry()
    
    class ApiBlueprint(Blueprint):
        base_path = "/api"
        tags = ["api", "v1"]
        merge_tags = False
    
    @ApiBlueprint.attach_at(leaf="users", tags=["users"])
    def list_users():
        pass
    
    registry.collect_from(list_users)
    descriptors = registry.collect()
    desc = descriptors[0]
    
    # Child tags should win
    if desc.tags != ["users"]:
        raise AssertionError(f"Expected tags=['users'], got {desc.tags}")
    
    return


def test_blueprint_attach_at_merge_tags_true():
    """Test that Blueprint.attach_at with merge_tags=True merges tags."""
    registry = EndpointRegistry()
    _clear_registry()
    
    class ApiBlueprint(Blueprint):
        base_path = "/api"
        tags = ["api", "v1"]
        merge_tags = True
    
    @ApiBlueprint.attach_at(leaf="users", tags=["users"])
    def list_users():
        pass
    
    registry.collect_from(list_users)
    descriptors = registry.collect()
    desc = descriptors[0]
    
    # Tags should be merged
    if "users" not in desc.tags:
        raise AssertionError("Expected 'users' in merged tags")
    
    if "api" not in desc.tags:
        raise AssertionError("Expected 'api' in merged tags")
    
    if "v1" not in desc.tags:
        raise AssertionError("Expected 'v1' in merged tags")
    
    return


def test_blueprint_attach_at_no_child_tags_uses_parent():
    """Test that Blueprint.attach_at uses parent tags when child has none."""
    registry = EndpointRegistry()
    _clear_registry()
    
    class ApiBlueprint(Blueprint):
        base_path = "/api"
        tags = ["api", "v1"]
    
    @ApiBlueprint.attach_at(leaf="status")
    def get_status():
        pass
    
    registry.collect_from(get_status)
    descriptors = registry.collect()
    desc = descriptors[0]
    
    if desc.tags != ["api", "v1"]:
        raise AssertionError(f"Expected tags=['api', 'v1'], got {desc.tags}")
    
    return


# =============================================================================
# Task 6.2: Blueprint register() method
# =============================================================================

def test_blueprint_has_register_method():
    """Test that Blueprint has register() classmethod."""
    _clear_registry()
    
    if not hasattr(Blueprint, "register"):
        raise AssertionError("Blueprint missing 'register' method")
    
    if not callable(Blueprint.register):
        raise AssertionError("Blueprint.register should be callable")
    
    return


def test_blueprint_register_returns_list():
    """Test that Blueprint.register() returns a list."""
    _clear_registry()
    
    class ApiBlueprint(Blueprint):
        base_path = "/api"
    
    result = ApiBlueprint.register()
    
    if not isinstance(result, list):
        raise AssertionError(f"Expected list, got {type(result)}")
    
    return


def test_blueprint_register_returns_descriptors():
    """Test that Blueprint.register() returns EndpointDescriptor objects."""
    _clear_registry()
    
    class ApiBlueprint(Blueprint):
        base_path = "/api"
    
    @ApiBlueprint.attach_at(leaf="users")
    def list_users():
        pass
    
    @ApiBlueprint.attach_at(leaf="items")
    def list_items():
        pass
    
    result = ApiBlueprint.register()
    
    if len(result) != 2:
        raise AssertionError(f"Expected 2 descriptors, got {len(result)}")
    
    for desc in result:
        if not isinstance(desc, EndpointDescriptor):
            raise AssertionError(f"Expected EndpointDescriptor, got {type(desc)}")
    
    return


def test_blueprint_register_without_router():
    """Test that Blueprint.register() works without router parameter."""
    _clear_registry()
    
    class ApiBlueprint(Blueprint):
        base_path = "/api"
    
    @ApiBlueprint.attach_at(leaf="test")
    def test_handler():
        pass
    
    # Should not raise when router is None
    result = ApiBlueprint.register(router=None)
    
    if len(result) != 1:
        raise AssertionError(f"Expected 1 descriptor, got {len(result)}")
    
    return


def test_blueprint_register_with_router():
    """Test that Blueprint.register() calls router.add_endpoint for each descriptor."""
    _clear_registry()
    
    class ApiBlueprint(Blueprint):
        base_path = "/api"
    
    @ApiBlueprint.attach_at(leaf="users")
    def list_users():
        pass
    
    @ApiBlueprint.attach_at(leaf="items")
    def list_items():
        pass
    
    # Create a mock router that tracks calls
    added_descriptors = []
    
    class MockRouter:
        def add_endpoint(self, descriptor):
            added_descriptors.append(descriptor)
    
    router = MockRouter()
    result = ApiBlueprint.register(router=router)
    
    # Verify router.add_endpoint was called for each descriptor
    if len(added_descriptors) != 2:
        raise AssertionError(f"Expected 2 add_endpoint calls, got {len(added_descriptors)}")
    
    # Verify the same descriptors were returned
    if len(result) != 2:
        raise AssertionError(f"Expected 2 descriptors returned, got {len(result)}")
    
    return


def test_blueprint_register_filters_by_base_path():
    """Test that Blueprint.register() only returns descriptors under its base path."""
    _clear_registry()
    
    class ApiBlueprint(Blueprint):
        base_path = "/api"
    
    class OtherBlueprint(Blueprint):
        base_path = "/other"
    
    @ApiBlueprint.attach_at(leaf="users")
    def api_users():
        pass
    
    @OtherBlueprint.attach_at(leaf="items")
    def other_items():
        pass
    
    # Register only ApiBlueprint
    api_result = ApiBlueprint.register()
    
    # Should only include /api/users, not /other/items
    if len(api_result) != 1:
        raise AssertionError(f"Expected 1 descriptor for ApiBlueprint, got {len(api_result)}")
    
    if api_result[0].path != "/api/users":
        raise AssertionError(f"Expected path='/api/users', got {api_result[0].path}")
    
    return


def test_blueprint_register_returns_empty_list_when_no_endpoints():
    """Test that Blueprint.register() returns empty list when no endpoints registered."""
    _clear_registry()
    
    class EmptyBlueprint(Blueprint):
        base_path = "/empty"
    
    result = EmptyBlueprint.register()
    
    if result != []:
        raise AssertionError(f"Expected empty list, got {result}")
    
    return


def test_blueprint_multiple_methods_single_endpoint():
    """Test that Blueprint handles endpoints with multiple HTTP methods."""
    _clear_registry()
    
    class ApiBlueprint(Blueprint):
        base_path = "/api"
    
    @ApiBlueprint.attach_at(leaf="resource", methods=["GET", "POST", "PUT"])
    def resource_handler():
        pass
    
    result = ApiBlueprint.register()
    
    if len(result) != 1:
        raise AssertionError(f"Expected 1 descriptor, got {len(result)}")
    
    if result[0].methods != ["GET", "POST", "PUT"]:
        raise AssertionError(f"Expected methods=['GET', 'POST', 'PUT'], got {result[0].methods}")
    
    return


def test_blueprint_inherits_version():
    """Test that Blueprint endpoints inherit version from blueprint."""
    registry = EndpointRegistry()
    _clear_registry()
    
    class VersionedBlueprint(Blueprint):
        base_path = "/api"
        version = "v2"
    
    @VersionedBlueprint.attach_at(leaf="status")
    def get_status():
        pass
    
    registry.collect_from(get_status)
    descriptors = registry.collect()
    desc = descriptors[0]
    
    if desc.version != "v2":
        raise AssertionError(f"Expected version='v2', got {desc.version}")
    
    return


def test_blueprint_endpoint_can_override_version():
    """Test that endpoint can override blueprint version."""
    registry = EndpointRegistry()
    _clear_registry()
    
    class VersionedBlueprint(Blueprint):
        base_path = "/api"
        version = "v1"
    
    @VersionedBlueprint.attach_at(leaf="status", version="v3")
    def get_status():
        pass
    
    registry.collect_from(get_status)
    descriptors = registry.collect()
    desc = descriptors[0]
    
    if desc.version != "v3":
        raise AssertionError(f"Expected version='v3', got {desc.version}")
    
    return
