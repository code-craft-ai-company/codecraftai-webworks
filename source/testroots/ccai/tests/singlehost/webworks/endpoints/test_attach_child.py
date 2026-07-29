"""
.. module:: test_attach_child
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Tests for the Blueprint.attach_child() method.

.. moduleauthor:: Code Craft AI LLC
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []

from ccai.webworks.endpoints import (
    AccessPolicy,
    Blueprint,
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
# =============================================================================
# Task 5.1: attach_child() classmethod in Blueprint
# =============================================================================

def test_blueprint_has_attach_child_method():
    """Test that Blueprint has attach_child() classmethod."""
    registry = EndpointRegistry()
    
    if not hasattr(Blueprint, "attach_child"):
        raise AssertionError("Blueprint missing 'attach_child' method")
    
    if not callable(Blueprint.attach_child):
        raise AssertionError("Blueprint.attach_child should be callable")
    
    return


def test_attach_child_accepts_child_endpoint_class():
    """Test that attach_child accepts a child endpoint class."""
    registry = EndpointRegistry()
    
    class ParentBlueprint(Blueprint):
        base_path = "/api/v1"
    
    class ChildEndpoint(Endpoint):
        base_leaf = "users"
        methods = ["GET"]
    
    descriptor = ParentBlueprint.attach_child(ChildEndpoint)
    
    if not isinstance(descriptor, EndpointDescriptor):
        raise AssertionError(f"Expected EndpointDescriptor, got {type(descriptor)}")
    
    return


def test_attach_child_composes_path_from_parent_base_path():
    """Test that attach_child composes path relative to parent base_path."""
    registry = EndpointRegistry()
    
    class ParentBlueprint(Blueprint):
        base_path = "/api/v1"
    
    class ChildEndpoint(Endpoint):
        base_leaf = "users"
    
    descriptor = ParentBlueprint.attach_child(ChildEndpoint)
    
    if descriptor.path != "/api/v1/users":
        raise AssertionError(f"Expected path='/api/v1/users', got {descriptor.path}")
    
    return


def test_attach_child_composes_path_from_parent_base_leaf():
    """Test that attach_child composes path relative to parent base_leaf."""
    registry = EndpointRegistry()
    
    class ParentBlueprint(Blueprint):
        base_leaf = "api"
    
    class ChildEndpoint(Endpoint):
        base_leaf = "users"
    
    descriptor = ParentBlueprint.attach_child(ChildEndpoint)
    
    if descriptor.path != "/api/users":
        raise AssertionError(f"Expected path='/api/users', got {descriptor.path}")
    
    return


def test_attach_child_with_leaf_override():
    """Test that attach_child accepts leaf override."""
    registry = EndpointRegistry()
    
    class ParentBlueprint(Blueprint):
        base_path = "/api/v1"
    
    class ChildEndpoint(Endpoint):
        base_leaf = "users"
    
    descriptor = ParentBlueprint.attach_child(ChildEndpoint, leaf="customers")
    
    if descriptor.path != "/api/v1/customers":
        raise AssertionError(f"Expected path='/api/v1/customers', got {descriptor.path}")
    
    return


def test_attach_child_with_path_override():
    """Test that attach_child accepts path override."""
    registry = EndpointRegistry()
    
    class ParentBlueprint(Blueprint):
        base_path = "/api/v1"
    
    class ChildEndpoint(Endpoint):
        base_path = "/original"
    
    descriptor = ParentBlueprint.attach_child(ChildEndpoint, path="/override/path")
    
    if descriptor.path != "/api/v1/override/path":
        raise AssertionError(f"Expected path='/api/v1/override/path', got {descriptor.path}")
    
    return


def test_attach_child_returns_endpoint_descriptor():
    """Test that attach_child returns an EndpointDescriptor."""
    registry = EndpointRegistry()
    
    class ParentBlueprint(Blueprint):
        base_path = "/api"
    
    class ChildEndpoint(Endpoint):
        base_leaf = "items"
    
    result = ParentBlueprint.attach_child(ChildEndpoint)
    
    if not isinstance(result, EndpointDescriptor):
        raise AssertionError(f"Expected EndpointDescriptor, got {type(result)}")
    
    return


def test_attach_child_registers_descriptor():
    """Test that attach_child registers the descriptor with EndpointRegistry."""
    registry = EndpointRegistry()
    registry = EndpointRegistry()
    
    class ParentBlueprint(Blueprint):
        base_path = "/api"
    
    class ChildEndpoint(Endpoint):
        base_leaf = "items"
    
    ParentBlueprint.attach_child(ChildEndpoint)
    
    descriptors = registry.collect()
    
    if len(descriptors) != 1:
        raise AssertionError(f"Expected 1 descriptor in registry, got {len(descriptors)}")
    
    if descriptors[0].path != "/api/items":
        raise AssertionError(f"Expected path='/api/items', got {descriptors[0].path}")
    
    return


# =============================================================================
# Task 5.2: Child attribute preservation
# =============================================================================

def test_attach_child_preserves_child_methods():
    """Test that attach_child preserves child's methods when not overridden."""
    registry = EndpointRegistry()
    
    class ParentBlueprint(Blueprint):
        base_path = "/api"
        methods = ["GET"]
    
    class ChildEndpoint(Endpoint):
        base_leaf = "items"
        methods = ["POST", "PUT"]
    
    descriptor = ParentBlueprint.attach_child(ChildEndpoint)
    
    if descriptor.methods != ["POST", "PUT"]:
        raise AssertionError(f"Expected methods=['POST', 'PUT'], got {descriptor.methods}")
    
    return


def test_attach_child_overrides_methods_when_provided():
    """Test that attach_child overrides methods when explicitly provided."""
    registry = EndpointRegistry()
    
    class ParentBlueprint(Blueprint):
        base_path = "/api"
    
    class ChildEndpoint(Endpoint):
        base_leaf = "items"
        methods = ["GET"]
    
    descriptor = ParentBlueprint.attach_child(ChildEndpoint, methods=["DELETE"])
    
    if descriptor.methods != ["DELETE"]:
        raise AssertionError(f"Expected methods=['DELETE'], got {descriptor.methods}")
    
    return


def test_attach_child_preserves_child_version():
    """Test that attach_child preserves child's version when not overridden."""
    registry = EndpointRegistry()
    
    class ParentBlueprint(Blueprint):
        base_path = "/api"
        version = "v1"
    
    class ChildEndpoint(Endpoint):
        base_leaf = "items"
        version = "v2"
    
    descriptor = ParentBlueprint.attach_child(ChildEndpoint)
    
    if descriptor.version != "v2":
        raise AssertionError(f"Expected version='v2', got {descriptor.version}")
    
    return


def test_attach_child_inherits_parent_version_when_child_has_none():
    """Test that attach_child inherits parent version when child has none."""
    registry = EndpointRegistry()
    
    class ParentBlueprint(Blueprint):
        base_path = "/api"
        version = "v1"
    
    class ChildEndpoint(Endpoint):
        base_leaf = "items"
        version = None
    
    descriptor = ParentBlueprint.attach_child(ChildEndpoint)
    
    if descriptor.version != "v1":
        raise AssertionError(f"Expected version='v1', got {descriptor.version}")
    
    return


def test_attach_child_overrides_version_when_provided():
    """Test that attach_child overrides version when explicitly provided."""
    registry = EndpointRegistry()
    
    class ParentBlueprint(Blueprint):
        base_path = "/api"
        version = "v1"
    
    class ChildEndpoint(Endpoint):
        base_leaf = "items"
        version = "v2"
    
    descriptor = ParentBlueprint.attach_child(ChildEndpoint, version="v3")
    
    if descriptor.version != "v3":
        raise AssertionError(f"Expected version='v3', got {descriptor.version}")
    
    return


def test_attach_child_preserves_child_tags():
    """Test that attach_child preserves child's tags when not overridden."""
    registry = EndpointRegistry()
    
    class ParentBlueprint(Blueprint):
        base_path = "/api"
        tags = ["api"]
    
    class ChildEndpoint(Endpoint):
        base_leaf = "items"
        tags = ["items", "crud"]
    
    descriptor = ParentBlueprint.attach_child(ChildEndpoint)
    
    # Child tags should win by default
    if descriptor.tags != ["items", "crud"]:
        raise AssertionError(f"Expected tags=['items', 'crud'], got {descriptor.tags}")
    
    return


def test_attach_child_overrides_tags_when_provided():
    """Test that attach_child overrides tags when explicitly provided."""
    registry = EndpointRegistry()
    
    class ParentBlueprint(Blueprint):
        base_path = "/api"
        tags = ["api"]
    
    class ChildEndpoint(Endpoint):
        base_leaf = "items"
        tags = ["items"]
    
    descriptor = ParentBlueprint.attach_child(ChildEndpoint, tags=["override"])
    
    if descriptor.tags != ["override"]:
        raise AssertionError(f"Expected tags=['override'], got {descriptor.tags}")
    
    return


def test_attach_child_preserves_child_serializers():
    """Test that attach_child preserves child's serializers in extras."""
    registry = EndpointRegistry()
    
    class ParentBlueprint(Blueprint):
        base_path = "/api"
    
    class ChildEndpoint(Endpoint):
        base_leaf = "items"
        serializers = {"json": "application/json"}
    
    descriptor = ParentBlueprint.attach_child(ChildEndpoint)
    
    if "serializers" not in descriptor.extras:
        raise AssertionError("Expected 'serializers' in descriptor.extras")
    
    if descriptor.extras["serializers"] != {"json": "application/json"}:
        raise AssertionError(f"Expected serializers={{'json': 'application/json'}}, got {descriptor.extras['serializers']}")
    
    return


# =============================================================================
# Task 5.3: Constraint inheritance for attach_child
# =============================================================================

def test_attach_child_inherits_parent_access_policy():
    """Test that attach_child inherits parent access_policy when child has none."""
    registry = EndpointRegistry()
    
    class ParentBlueprint(Blueprint):
        base_path = "/api"
        access_policy = AccessPolicy(roles=["admin"])
    
    class ChildEndpoint(Endpoint):
        base_leaf = "items"
        access_policy = None
    
    descriptor = ParentBlueprint.attach_child(ChildEndpoint)
    
    if descriptor.constraints.access_policy is None:
        raise AssertionError("Expected access_policy to be inherited from parent")
    
    if descriptor.constraints.access_policy.roles != ("admin",):
        raise AssertionError(f"Expected roles=['admin'], got {descriptor.constraints.access_policy.roles}")
    
    return


def test_attach_child_merges_access_policies():
    """Test that attach_child merges parent and child access policies."""
    registry = EndpointRegistry()
    
    class ParentBlueprint(Blueprint):
        base_path = "/api"
        access_policy = AccessPolicy(roles=["user"])
    
    class ChildEndpoint(Endpoint):
        base_leaf = "items"
        access_policy = AccessPolicy(roles=["admin"])
    
    descriptor = ParentBlueprint.attach_child(ChildEndpoint)
    
    # Roles should be merged (union)
    roles = descriptor.constraints.access_policy.roles
    if "user" not in roles or "admin" not in roles:
        raise AssertionError(f"Expected roles to contain both 'user' and 'admin', got {roles}")
    
    return


def test_attach_child_inherits_parent_rate_limit():
    """Test that attach_child inherits parent rate_limit when child has none."""
    registry = EndpointRegistry()
    
    class ParentBlueprint(Blueprint):
        base_path = "/api"
        rate_limit = RateLimit(requests=100, window=60)
    
    class ChildEndpoint(Endpoint):
        base_leaf = "items"
        rate_limit = None
    
    descriptor = ParentBlueprint.attach_child(ChildEndpoint)
    
    if descriptor.constraints.rate_limit is None:
        raise AssertionError("Expected rate_limit to be inherited from parent")
    
    if descriptor.constraints.rate_limit.requests != 100:
        raise AssertionError(f"Expected requests=100, got {descriptor.constraints.rate_limit.requests}")
    
    return


def test_attach_child_uses_most_restrictive_rate_limit():
    """Test that attach_child uses most restrictive rate limit."""
    registry = EndpointRegistry()
    
    class ParentBlueprint(Blueprint):
        base_path = "/api"
        rate_limit = RateLimit(requests=100, window=60)
    
    class ChildEndpoint(Endpoint):
        base_leaf = "items"
        rate_limit = RateLimit(requests=50, window=60)
    
    descriptor = ParentBlueprint.attach_child(ChildEndpoint)
    
    # Most restrictive should be 50 requests
    if descriptor.constraints.rate_limit.requests != 50:
        raise AssertionError(f"Expected requests=50 (most restrictive), got {descriptor.constraints.rate_limit.requests}")
    
    return


def test_attach_child_merge_tags_true():
    """Test that attach_child merges tags when parent has merge_tags=True."""
    registry = EndpointRegistry()
    
    class ParentBlueprint(Blueprint):
        base_path = "/api"
        tags = ["api", "v1"]
        merge_tags = True
    
    class ChildEndpoint(Endpoint):
        base_leaf = "items"
        tags = ["items"]
    
    descriptor = ParentBlueprint.attach_child(ChildEndpoint)
    
    # Tags should be merged
    if "items" not in descriptor.tags:
        raise AssertionError("Expected 'items' in merged tags")
    
    if "api" not in descriptor.tags:
        raise AssertionError("Expected 'api' in merged tags")
    
    if "v1" not in descriptor.tags:
        raise AssertionError("Expected 'v1' in merged tags")
    
    return


def test_attach_child_merge_tags_false():
    """Test that attach_child uses child tags when parent has merge_tags=False."""
    registry = EndpointRegistry()
    
    class ParentBlueprint(Blueprint):
        base_path = "/api"
        tags = ["api", "v1"]
        merge_tags = False
    
    class ChildEndpoint(Endpoint):
        base_leaf = "items"
        tags = ["items"]
    
    descriptor = ParentBlueprint.attach_child(ChildEndpoint)
    
    # Child tags should win
    if descriptor.tags != ["items"]:
        raise AssertionError(f"Expected tags=['items'], got {descriptor.tags}")
    
    return


def test_attach_child_inherits_parent_tags_when_child_has_none():
    """Test that attach_child inherits parent tags when child has none."""
    registry = EndpointRegistry()
    
    class ParentBlueprint(Blueprint):
        base_path = "/api"
        tags = ["api", "v1"]
    
    class ChildEndpoint(Endpoint):
        base_leaf = "items"
        tags = []
    
    descriptor = ParentBlueprint.attach_child(ChildEndpoint)
    
    # Parent tags should be inherited
    if descriptor.tags != ["api", "v1"]:
        raise AssertionError(f"Expected tags=['api', 'v1'], got {descriptor.tags}")
    
    return


def test_attach_child_access_policy_override():
    """Test that attach_child accepts access_policy override."""
    registry = EndpointRegistry()
    
    class ParentBlueprint(Blueprint):
        base_path = "/api"
        access_policy = AccessPolicy(roles=["user"])
    
    class ChildEndpoint(Endpoint):
        base_leaf = "items"
        access_policy = AccessPolicy(roles=["admin"])
    
    override_policy = AccessPolicy(roles=["superuser"])
    descriptor = ParentBlueprint.attach_child(ChildEndpoint, access_policy=override_policy)
    
    # Override should be merged with parent
    roles = descriptor.constraints.access_policy.roles
    if "superuser" not in roles:
        raise AssertionError(f"Expected 'superuser' in roles, got {roles}")
    
    return


def test_attach_child_rate_limit_override():
    """Test that attach_child accepts rate_limit override."""
    registry = EndpointRegistry()
    
    class ParentBlueprint(Blueprint):
        base_path = "/api"
        rate_limit = RateLimit(requests=100, window=60)
    
    class ChildEndpoint(Endpoint):
        base_leaf = "items"
        rate_limit = RateLimit(requests=50, window=60)
    
    override_limit = RateLimit(requests=25, window=60)
    descriptor = ParentBlueprint.attach_child(ChildEndpoint, rate_limit=override_limit)
    
    # Override should be used (most restrictive)
    if descriptor.constraints.rate_limit.requests != 25:
        raise AssertionError(f"Expected requests=25, got {descriptor.constraints.rate_limit.requests}")
    
    return


def test_attach_child_extra_kwargs_preserved():
    """Test that attach_child preserves extra kwargs in descriptor.extras."""
    registry = EndpointRegistry()
    
    class ParentBlueprint(Blueprint):
        base_path = "/api"
    
    class ChildEndpoint(Endpoint):
        base_leaf = "items"
    
    descriptor = ParentBlueprint.attach_child(
        ChildEndpoint,
        custom_field="custom_value",
        another_field=123
    )
    
    if "custom_field" not in descriptor.extras:
        raise AssertionError("Expected 'custom_field' in descriptor.extras")
    
    if descriptor.extras["custom_field"] != "custom_value":
        raise AssertionError(f"Expected custom_field='custom_value', got {descriptor.extras['custom_field']}")
    
    if "another_field" not in descriptor.extras:
        raise AssertionError("Expected 'another_field' in descriptor.extras")
    
    if descriptor.extras["another_field"] != 123:
        raise AssertionError(f"Expected another_field=123, got {descriptor.extras['another_field']}")
    
    return


def test_attach_child_with_doc_kwarg():
    """Test that attach_child accepts doc kwarg."""
    registry = EndpointRegistry()
    
    from ccai.webworks.endpoints import Doc
    
    class ParentBlueprint(Blueprint):
        base_path = "/api"
    
    class ChildEndpoint(Endpoint):
        base_leaf = "items"
    
    doc = Doc(summary="List items", description="Returns all items")
    descriptor = ParentBlueprint.attach_child(ChildEndpoint, doc=doc)
    
    if descriptor.doc is None:
        raise AssertionError("Expected doc to be set")
    
    if descriptor.doc.summary != "List items":
        raise AssertionError(f"Expected summary='List items', got {descriptor.doc.summary}")
    
    return


def test_attach_child_multiple_children():
    """Test that attach_child can attach multiple children."""
    registry = EndpointRegistry()
    registry = EndpointRegistry()
    
    class ParentBlueprint(Blueprint):
        base_path = "/api"
    
    class UsersEndpoint(Endpoint):
        base_leaf = "users"
    
    class ItemsEndpoint(Endpoint):
        base_leaf = "items"
    
    desc1 = ParentBlueprint.attach_child(UsersEndpoint)
    desc2 = ParentBlueprint.attach_child(ItemsEndpoint)
    
    if desc1.path != "/api/users":
        raise AssertionError(f"Expected path='/api/users', got {desc1.path}")
    
    if desc2.path != "/api/items":
        raise AssertionError(f"Expected path='/api/items', got {desc2.path}")
    
    descriptors = registry.collect()
    if len(descriptors) != 2:
        raise AssertionError(f"Expected 2 descriptors in registry, got {len(descriptors)}")
    
    return


def test_attach_child_nested_blueprints():
    """Test that attach_child works with nested blueprints."""
    registry = EndpointRegistry()
    
    class RootBlueprint(Blueprint):
        base_path = "/api"
    
    class V1Blueprint(Blueprint):
        base_path = "/v1"
    
    class UsersEndpoint(Endpoint):
        base_leaf = "users"
    
    # First attach V1Blueprint to Root
    v1_desc = RootBlueprint.attach_child(V1Blueprint)
    
    if v1_desc.path != "/api/v1":
        raise AssertionError(f"Expected path='/api/v1', got {v1_desc.path}")
    
    return
