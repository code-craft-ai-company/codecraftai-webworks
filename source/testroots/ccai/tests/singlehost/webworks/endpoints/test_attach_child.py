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
    EndpointRegistrationError,
    EndpointRegistry,
    RateLimit,
    RestBlueprint,
)


# =============================================================================
# Task 5.1: attach_child() classmethod in Blueprint
# =============================================================================

def test_blueprint_has_attach_child_method():
    """Test that Blueprint has attach_child() classmethod."""
    
    if not hasattr(Blueprint, "attach_child"):
        raise AssertionError("Blueprint missing 'attach_child' method")
    
    if not callable(Blueprint.attach_child):
        raise AssertionError("Blueprint.attach_child should be callable")
    
    return


def test_attach_child_accepts_child_endpoint_class():
    """Test that attach_child accepts a child endpoint class."""
    
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
    
    class ParentBlueprint(Blueprint):
        base_path = "/api"
    
    class ChildEndpoint(Endpoint):
        base_leaf = "items"
    
    result = ParentBlueprint.attach_child(ChildEndpoint)
    
    if not isinstance(result, EndpointDescriptor):
        raise AssertionError(f"Expected EndpointDescriptor, got {type(result)}")
    
    return


def test_attach_child_registers_descriptor():
    """Test that a descriptor from attach_child can be registered."""
    registry = EndpointRegistry()

    class ParentBlueprint(Blueprint):
        base_path = "/api"

    class ChildEndpoint(Endpoint):
        base_leaf = "items"

    # attach_child hands back the descriptor rather than filing it anywhere.
    # Its handler is a placeholder built inside the call, so collect_from has
    # no name to reach it by -- the descriptor itself is the handle.
    descriptor = ParentBlueprint.attach_child(ChildEndpoint)
    registry.register(descriptor)

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

    class ParentBlueprint(Blueprint):
        base_path = "/api"

    class UsersEndpoint(Endpoint):
        base_leaf = "users"

    class ItemsEndpoint(Endpoint):
        base_leaf = "items"

    desc1 = ParentBlueprint.attach_child(UsersEndpoint)
    desc2 = ParentBlueprint.attach_child(ItemsEndpoint)

    registry.register(desc1)
    registry.register(desc2)

    if desc1.path != "/api/users":
        raise AssertionError(f"Expected path='/api/users', got {desc1.path}")
    
    if desc2.path != "/api/items":
        raise AssertionError(f"Expected path='/api/items', got {desc2.path}")
    
    descriptors = registry.collect()
    if len(descriptors) != 2:
        raise AssertionError(f"Expected 2 descriptors in registry, got {len(descriptors)}")
    
    return


def test_attach_child_nested_blueprints():
    """Test that a nested blueprint attaches its children under its parent's prefix."""
    
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

    # Then V1Blueprint attaches its own child under the placement Root gave
    # it; the product composes Root's prefix, V1's base and the child leaf.
    nested_desc = V1Blueprint.attach_child(UsersEndpoint, parent_placement=v1_desc)
    
    if nested_desc.path != "/api/v1/users":
        raise AssertionError(f"Expected path='/api/v1/users', got {nested_desc.path}")
    
    # Without a placement, attach_child stays relative to V1's own base
    # (single-level behavior is unchanged).
    users_desc = V1Blueprint.attach_child(UsersEndpoint)

    if users_desc.path != "/v1/users":
        raise AssertionError(f"Expected path='/v1/users', got {users_desc.path}")

    return


def test_attach_child_nested_blueprints_three_levels():
    """Test that prefixes compose through every level of nesting, from the root down."""
    
    class RootBlueprint(Blueprint):
        base_path = "/api"
    
    class V1Blueprint(Blueprint):
        base_path = "/v1"
    
    class AdminBlueprint(Blueprint):
        base_leaf = "admin"
    
    class UsersEndpoint(Endpoint):
        base_leaf = "users"
    
    v1_desc = RootBlueprint.attach_child(V1Blueprint)
    admin_desc = V1Blueprint.attach_child(AdminBlueprint, parent_placement=v1_desc)
    users_desc = AdminBlueprint.attach_child(UsersEndpoint, parent_placement=admin_desc)
    
    if admin_desc.path != "/api/v1/admin":
        raise AssertionError(f"Expected path='/api/v1/admin', got {admin_desc.path}")
    
    if users_desc.path != "/api/v1/admin/users":
        raise AssertionError(f"Expected path='/api/v1/admin/users', got {users_desc.path}")
    
    return


def test_attach_child_nested_blueprint_path_override():
    """Test that a leaf/path override on a nested attach is composed under the placement."""
    
    class RootBlueprint(Blueprint):
        base_path = "/api"
    
    class V1Blueprint(Blueprint):
        base_path = "/v1"
    
    class UsersEndpoint(Endpoint):
        base_leaf = "users"
    
    v1_desc = RootBlueprint.attach_child(V1Blueprint)
    
    leaf_desc = V1Blueprint.attach_child(UsersEndpoint, leaf="people", parent_placement=v1_desc)
    path_desc = V1Blueprint.attach_child(UsersEndpoint, path="/people/list", parent_placement=v1_desc)
    
    if leaf_desc.path != "/api/v1/people":
        raise AssertionError(f"Expected path='/api/v1/people', got {leaf_desc.path}")
    
    if path_desc.path != "/api/v1/people/list":
        raise AssertionError(f"Expected path='/api/v1/people/list', got {path_desc.path}")
    
    return


def test_attach_child_nested_blueprint_inherits_placement_constraints():
    """Test that a nested child inherits the constraints of every level above it."""
    
    class RootBlueprint(Blueprint):
        base_path = "/api"
        access_policy = AccessPolicy(roles=["user"])
        rate_limit = RateLimit(requests=100, window=60)
        tags = ["api"]
        version = "v1"
    
    class AdminBlueprint(Blueprint):
        base_leaf = "admin"
        access_policy = AccessPolicy(roles=["admin"])
    
    class UsersEndpoint(Endpoint):
        base_leaf = "users"
    
    admin_desc = RootBlueprint.attach_child(AdminBlueprint)
    users_desc = AdminBlueprint.attach_child(UsersEndpoint, parent_placement=admin_desc)
    
    roles = users_desc.constraints.access_policy.roles
    if "user" not in roles or "admin" not in roles:
        raise AssertionError(f"Expected roles from Root and Admin ('user', 'admin'), got {roles}")
    
    if users_desc.constraints.rate_limit is None or users_desc.constraints.rate_limit.requests != 100:
        raise AssertionError(f"Expected Root's rate limit to cascade, got {users_desc.constraints.rate_limit}")
    
    if users_desc.tags != ["api"]:
        raise AssertionError(f"Expected Root's tags to cascade, got {users_desc.tags}")
    
    if users_desc.version != "v1":
        raise AssertionError(f"Expected Root's version to cascade, got {users_desc.version}")
    
    # Single-level, AdminBlueprint only contributes its own policy
    standalone_desc = AdminBlueprint.attach_child(UsersEndpoint)
    standalone_roles = standalone_desc.constraints.access_policy.roles
    if standalone_roles != ("admin",):
        raise AssertionError(f"Expected roles=('admin',) without a placement, got {standalone_roles}")
    
    return


def test_attach_child_nested_blueprint_register_includes_nested_child():
    """Test that register() on the nested blueprint returns the child it attached under its placement."""
    
    class RootBlueprint(Blueprint):
        base_path = "/api"
    
    class V1Blueprint(Blueprint):
        base_path = "/v1"
    
    class UsersEndpoint(Endpoint):
        base_leaf = "users"
    
    v1_desc = RootBlueprint.attach_child(V1Blueprint)
    nested_desc = V1Blueprint.attach_child(UsersEndpoint, parent_placement=v1_desc)

    if nested_desc.path != "/api/v1/users":
        raise AssertionError(f"Expected path='/api/v1/users', got {nested_desc.path}")

    registered = V1Blueprint.register()
    
    found = False
    for descriptor in registered:
        if descriptor is nested_desc:
            found = True
            break
    
    if found is not True:
        registered_paths = [descriptor.path for descriptor in registered]
        raise AssertionError(f"Expected V1Blueprint.register() to include /api/v1/users, got {registered_paths}")
    
    return


def test_attach_child_parent_placement_without_path_raises():
    """Test that a placement with neither path nor leaf is rejected."""
    
    class V1Blueprint(Blueprint):
        base_path = "/v1"
    
    class UsersEndpoint(Endpoint):
        base_leaf = "users"
    
    def handler():
        return
    
    empty_placement = EndpointDescriptor(handler=handler, module=__name__)
    
    raised = None
    try:
        V1Blueprint.attach_child(UsersEndpoint, parent_placement=empty_placement)
    except EndpointRegistrationError as exc:
        raised = exc
    
    if raised is None:
        raise AssertionError("Expected EndpointRegistrationError for a placement without path or leaf")
    
    return


# =============================================================================
# attach_child re-places the child's own handlers
# =============================================================================

def _dispatch_get(router, path):
    """Send a GET for ``path`` through a Dispatcher over ``router`` and return the response."""
    from ccai.webworks.routing.dispatcher import Dispatcher
    from ccai.webworks.routing.request import Request

    dispatcher = Dispatcher(router)
    response = dispatcher.dispatch(Request("GET", path))
    return response


def test_attach_child_route_serves_the_childs_handler():
    """A route from ParentBP.attach_child(Child), registered via ParentBP.register(router), runs the child's handler."""
    import json

    from ccai.webworks.routing.router import Router

    class ParentBlueprint(Blueprint):
        base_path = "/api"

    class ChildBlueprint(Blueprint):
        base_path = "/items"

    @ChildBlueprint.attach_at(leaf="list", methods=["GET"])
    def list_items(request):
        return {"items": [1, 2]}

    ParentBlueprint.attach_child(ChildBlueprint)

    router = Router()
    ParentBlueprint.register(router)
    response = _dispatch_get(router, "/api/items/list")

    if response.status_code != 200:
        raise AssertionError(f"Expected 200 from the child's handler, got {response.status_code}: {response.body!r}")

    if json.loads(response.body) != {"items": [1, 2]}:
        raise AssertionError(f"Expected the child handler's result, got {response.body!r}")

    return


def test_attach_child_places_handlers_under_the_placement_path():
    """Each handler the child declared is re-placed with the child's base swapped for the placement path."""

    class ParentBlueprint(Blueprint):
        base_path = "/api"

    class ChildBlueprint(Blueprint):
        base_path = "/items"

    @ChildBlueprint.attach_at(leaf="list", methods=["GET"])
    def list_items(request):
        return {}

    @ChildBlueprint.attach_at(path="{item_id}", methods=["DELETE"])
    def delete_item(request):
        return {}

    ParentBlueprint.attach_child(ChildBlueprint)

    placed = sorted((descriptor.path, tuple(descriptor.methods)) for descriptor in ParentBlueprint.register())
    expected = [("/api/items/list", ("GET",)), ("/api/items/{item_id}", ("DELETE",))]

    if placed != expected:
        raise AssertionError(f"Expected {expected}, got {placed}")

    return


def test_attach_child_keeps_the_childs_own_descriptors_unchanged():
    """Re-placing under a parent does not move the route the child declared for itself."""

    class ParentBlueprint(Blueprint):
        base_path = "/api"

    class ChildBlueprint(Blueprint):
        base_path = "/items"

    @ChildBlueprint.attach_at(leaf="list", methods=["GET"])
    def list_items(request):
        return {}

    ParentBlueprint.attach_child(ChildBlueprint)

    child_paths = [descriptor.path for descriptor in ChildBlueprint.register()]

    if child_paths != ["/items/list"]:
        raise AssertionError(f"Expected the child's own path to stay '/items/list', got {child_paths}")

    return


def test_attach_child_placed_handler_inherits_parent_policy():
    """A re-placed handler requires the parent's roles as well as its own."""

    class ParentBlueprint(Blueprint):
        base_path = "/admin"
        access_policy = AccessPolicy(roles=["admin"])

    class ChildBlueprint(Blueprint):
        base_path = "/reports"

    @ChildBlueprint.attach_at(leaf="daily", methods=["GET"], access_policy=AccessPolicy(scopes=["reports:read"]))
    def daily_report(request):
        return {}

    ParentBlueprint.attach_child(ChildBlueprint)

    placed = ParentBlueprint.register()[0]
    policy = placed.constraints.access_policy

    if "admin" not in policy.roles:
        raise AssertionError(f"Expected the parent's role 'admin' on the placed handler, got {policy.roles}")

    if "reports:read" not in policy.scopes:
        raise AssertionError(f"Expected the handler's own scope to be kept, got {policy.scopes}")

    return


def test_attach_child_placement_is_not_registered_when_handlers_are_placed():
    """The placement descriptor is not returned by register() once real handlers stand in its place."""

    class ParentBlueprint(Blueprint):
        base_path = "/api"

    class ChildBlueprint(Blueprint):
        base_path = "/items"

    @ChildBlueprint.attach_at(path="/", methods=["GET"])
    def items_root(request):
        return {}

    placement = ParentBlueprint.attach_child(ChildBlueprint)

    registered = ParentBlueprint.register()
    for descriptor in registered:
        if descriptor is placement:
            raise AssertionError("The placement must not be registered beside the handler placed at the same path")

    if [descriptor.path for descriptor in registered] != ["/api/items"]:
        raise AssertionError(f"Expected one route at '/api/items', got {[d.path for d in registered]}")

    return


def test_attach_child_on_rest_blueprint_records_placed_handlers():
    """RestBlueprint inherits Endpoint.attach_child, which now records the placed handlers for register()."""

    class ParentRestBlueprint(RestBlueprint):
        base_path = "/v1"

    class ChildRestBlueprint(RestBlueprint):
        base_path = "/users"

    @ChildRestBlueprint.attach_at(leaf="me", methods=["GET"])
    def current_user(request):
        return {}

    ParentRestBlueprint.attach_child(ChildRestBlueprint)

    paths = [descriptor.path for descriptor in ParentRestBlueprint.register()]

    if paths != ["/v1/users/me"]:
        raise AssertionError(f"Expected ['/v1/users/me'] from register(), got {paths}")

    return


def test_attach_child_placement_handler_explains_a_child_without_handlers():
    """Calling the stand-in handler of a placement names the child that declared no handlers."""

    class ParentBlueprint(Blueprint):
        base_path = "/api"

    class EmptyChild(Endpoint):
        base_leaf = "nothing"

    placement = ParentBlueprint.attach_child(EmptyChild)

    try:
        placement.handler(None)
    except EndpointRegistrationError as err:
        if "EmptyChild" not in str(err):
            raise AssertionError(f"Expected the error to name the child, got: {err}")
    else:
        raise AssertionError("Expected EndpointRegistrationError from a placement with no handler behind it")

    return


def test_attach_child_nested_children_are_placed_under_the_whole_chain():
    """Attaching leaves first, then the middle blueprint to the root, serves the leaf under every prefix."""

    class RootBlueprint(Blueprint):
        base_path = "/api"

    class V1Blueprint(Blueprint):
        base_path = "/v1"

    class UsersBlueprint(Blueprint):
        base_path = "/users"

    @UsersBlueprint.attach_at(leaf="me", methods=["GET"])
    def current_user(request):
        return {}

    V1Blueprint.attach_child(UsersBlueprint)
    RootBlueprint.attach_child(V1Blueprint)

    paths = [descriptor.path for descriptor in RootBlueprint.register()]

    if paths != ["/api/v1/users/me"]:
        raise AssertionError(f"Expected ['/api/v1/users/me'], got {paths}")

    return
