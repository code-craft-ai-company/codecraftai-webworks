"""
.. module:: test_endpoint
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Tests for the Endpoint base class.

.. moduleauthor:: Code Craft AI LLC
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []

from ccai.webworks.endpoints import (
    AccessPolicy,
    Doc,
    Endpoint,
    EndpointDescriptor,
    EndpointRegistry,
    EndpointRegistrationError,
    EndpointConflictError,
    RateLimit,
)


# =============================================================================
# Task 5.1: Endpoint class with class-level defaults
# =============================================================================

def test_endpoint_has_class_level_defaults():
    """Test that Endpoint class has expected class-level default attributes."""
    
    # Verify default attributes exist
    if not hasattr(Endpoint, "access_policy"):
        raise AssertionError("Endpoint missing 'access_policy' attribute")
    
    if not hasattr(Endpoint, "rate_limit"):
        raise AssertionError("Endpoint missing 'rate_limit' attribute")
    
    if not hasattr(Endpoint, "methods"):
        raise AssertionError("Endpoint missing 'methods' attribute")
    
    if not hasattr(Endpoint, "version"):
        raise AssertionError("Endpoint missing 'version' attribute")
    
    if not hasattr(Endpoint, "tags"):
        raise AssertionError("Endpoint missing 'tags' attribute")
    
    if not hasattr(Endpoint, "serializers"):
        raise AssertionError("Endpoint missing 'serializers' attribute")
    
    # Verify default values
    if Endpoint.access_policy is not None:
        raise AssertionError(f"Expected access_policy=None, got {Endpoint.access_policy}")
    
    if Endpoint.rate_limit is not None:
        raise AssertionError(f"Expected rate_limit=None, got {Endpoint.rate_limit}")
    
    if Endpoint.methods != ["GET"]:
        raise AssertionError(f"Expected methods=['GET'], got {Endpoint.methods}")
    
    if Endpoint.version is not None:
        raise AssertionError(f"Expected version=None, got {Endpoint.version}")
    
    if Endpoint.tags != []:
        raise AssertionError(f"Expected tags=[], got {Endpoint.tags}")
    
    if Endpoint.serializers != {}:
        raise AssertionError(f"Expected serializers={{}}, got {Endpoint.serializers}")
    
    return


def test_endpoint_subclass_can_override_defaults():
    """Test that subclasses can override class-level defaults."""
    
    class CustomEndpoint(Endpoint):
        access_policy = AccessPolicy(roles=["admin"])
        rate_limit = RateLimit(requests=100, window=60)
        methods = ["GET", "POST"]
        version = "v1"
        tags = ["api", "custom"]
        serializers = {"json": "application/json"}
    
    # Verify subclass attributes
    if CustomEndpoint.access_policy.roles != ("admin",):
        raise AssertionError(f"Expected roles=['admin'], got {CustomEndpoint.access_policy.roles}")
    
    if CustomEndpoint.rate_limit.requests != 100:
        raise AssertionError(f"Expected requests=100, got {CustomEndpoint.rate_limit.requests}")
    
    if CustomEndpoint.methods != ["GET", "POST"]:
        raise AssertionError(f"Expected methods=['GET', 'POST'], got {CustomEndpoint.methods}")
    
    if CustomEndpoint.version != "v1":
        raise AssertionError(f"Expected version='v1', got {CustomEndpoint.version}")
    
    if CustomEndpoint.tags != ["api", "custom"]:
        raise AssertionError(f"Expected tags=['api', 'custom'], got {CustomEndpoint.tags}")
    
    if CustomEndpoint.serializers != {"json": "application/json"}:
        raise AssertionError(f"Expected serializers with json, got {CustomEndpoint.serializers}")
    
    # Verify base class is unchanged
    if Endpoint.access_policy is not None:
        raise AssertionError("Base Endpoint.access_policy should still be None")
    
    if Endpoint.methods != ["GET"]:
        raise AssertionError("Base Endpoint.methods should still be ['GET']")
    
    return


# =============================================================================
# Task 5.2: attach_at() classmethod decorator
# =============================================================================

def test_attach_at_returns_original_function():
    """Test that attach_at decorator returns the original function unchanged."""
    
    def my_handler():
        return "hello"
    
    original_id = id(my_handler)
    
    decorated = Endpoint.attach_at(leaf="status")(my_handler)
    
    # Verify same object identity
    if id(decorated) != original_id:
        raise AssertionError("Decorated function should have same id as original")
    
    if decorated is not my_handler:
        raise AssertionError("Decorated function should be the same object as original")
    
    # Verify function still works
    if decorated() != "hello":
        raise AssertionError("Decorated function should still work correctly")
    
    return


def test_attach_at_registers_descriptor():
    """Test that attach_at registers an EndpointDescriptor with the registry."""
    registry = EndpointRegistry()
    
    @Endpoint.attach_at(leaf="test")
    def test_handler():
        pass
    
    registry.collect_from(test_handler)
    descriptors = registry.collect()
    
    if len(descriptors) != 1:
        raise AssertionError(f"Expected 1 descriptor, got {len(descriptors)}")
    
    desc = descriptors[0]
    
    if desc.handler is not test_handler:
        raise AssertionError("Descriptor handler should be test_handler")
    
    if desc.leaf != "test":
        raise AssertionError(f"Expected leaf='test', got {desc.leaf}")
    
    if desc.methods != ["GET"]:
        raise AssertionError(f"Expected methods=['GET'], got {desc.methods}")
    
    return


def test_attach_at_with_path_parameter():
    """Test that attach_at accepts path parameter instead of leaf."""
    registry = EndpointRegistry()
    
    @Endpoint.attach_at(path="/api/v1/status")
    def status_handler():
        pass
    
    registry.collect_from(status_handler)
    descriptors = registry.collect()
    
    if len(descriptors) != 1:
        raise AssertionError(f"Expected 1 descriptor, got {len(descriptors)}")
    
    desc = descriptors[0]
    
    if desc.path != "/api/v1/status":
        raise AssertionError(f"Expected path='/api/v1/status', got {desc.path}")
    
    if desc.leaf is not None:
        raise AssertionError(f"Expected leaf=None, got {desc.leaf}")
    
    return


def test_attach_at_raises_error_without_leaf_or_path():
    """Test that attach_at raises EndpointRegistrationError without leaf or path."""
    
    error_raised = False
    error_instance = None
    
    try:
        @Endpoint.attach_at()
        def bad_handler():
            pass
    except EndpointRegistrationError as e:
        error_raised = True
        error_instance = e
    
    if not error_raised:
        raise AssertionError("Expected EndpointRegistrationError to be raised")
    
    if "leaf" not in error_instance.missing_fields and "path" not in error_instance.missing_fields:
        raise AssertionError("Expected missing_fields to contain 'leaf' or 'path'")
    
    return


def test_attach_at_kwargs_override_class_defaults():
    """Test that explicit kwargs override class-level defaults."""
    registry = EndpointRegistry()
    
    class CustomEndpoint(Endpoint):
        methods = ["GET"]
        version = "v1"
        tags = ["default"]
    
    @CustomEndpoint.attach_at(
        leaf="override",
        methods=["POST", "PUT"],
        version="v2",
        tags=["custom"]
    )
    def override_handler():
        pass
    
    registry.collect_from(override_handler)
    descriptors = registry.collect()
    desc = descriptors[0]
    
    # Verify kwargs override class defaults
    if desc.methods != ["POST", "PUT"]:
        raise AssertionError(f"Expected methods=['POST', 'PUT'], got {desc.methods}")
    
    if desc.version != "v2":
        raise AssertionError(f"Expected version='v2', got {desc.version}")
    
    if desc.tags != ["custom"]:
        raise AssertionError(f"Expected tags=['custom'], got {desc.tags}")
    
    return


def test_attach_at_inherits_class_defaults_when_not_specified():
    """Test that class defaults are used when kwargs not specified."""
    registry = EndpointRegistry()
    
    class CustomEndpoint(Endpoint):
        methods = ["GET", "POST"]
        version = "v1"
        tags = ["api"]
        access_policy = AccessPolicy(roles=["user"])
        rate_limit = RateLimit(requests=50, window=30)
    
    @CustomEndpoint.attach_at(leaf="inherit")
    def inherit_handler():
        pass
    
    registry.collect_from(inherit_handler)
    descriptors = registry.collect()
    desc = descriptors[0]
    
    # Verify class defaults are inherited
    if desc.methods != ["GET", "POST"]:
        raise AssertionError(f"Expected methods=['GET', 'POST'], got {desc.methods}")
    
    if desc.version != "v1":
        raise AssertionError(f"Expected version='v1', got {desc.version}")
    
    if desc.tags != ["api"]:
        raise AssertionError(f"Expected tags=['api'], got {desc.tags}")
    
    if desc.constraints.access_policy.roles != ("user",):
        raise AssertionError(f"Expected roles=['user'], got {desc.constraints.access_policy.roles}")
    
    if desc.constraints.rate_limit.requests != 50:
        raise AssertionError(f"Expected requests=50, got {desc.constraints.rate_limit.requests}")
    
    return


def test_attach_at_accepts_all_documented_parameters():
    """Test that attach_at accepts all documented parameters."""
    registry = EndpointRegistry()
    
    policy = AccessPolicy(roles=["admin"], scopes=["read", "write"])
    limit = RateLimit(requests=100, window=60)
    doc = Doc(summary="Test endpoint", description="A test endpoint")
    
    @Endpoint.attach_at(
        leaf="full",
        path=None,
        methods=["GET", "POST"],
        version="v2",
        tags=["test", "full"],
        access_policy=policy,
        rate_limit=limit,
        doc=doc,
        on_conflict="error"
    )
    def full_handler():
        pass
    
    registry.collect_from(full_handler)
    descriptors = registry.collect()
    desc = descriptors[0]
    
    if desc.leaf != "full":
        raise AssertionError(f"Expected leaf='full', got {desc.leaf}")
    
    if desc.methods != ["GET", "POST"]:
        raise AssertionError(f"Expected methods=['GET', 'POST'], got {desc.methods}")
    
    if desc.version != "v2":
        raise AssertionError(f"Expected version='v2', got {desc.version}")
    
    if desc.tags != ["test", "full"]:
        raise AssertionError(f"Expected tags=['test', 'full'], got {desc.tags}")
    
    if desc.constraints.access_policy.roles != ("admin",):
        raise AssertionError(f"Expected roles=['admin'], got {desc.constraints.access_policy.roles}")
    
    if desc.constraints.rate_limit.requests != 100:
        raise AssertionError(f"Expected requests=100, got {desc.constraints.rate_limit.requests}")
    
    if desc.doc.summary != "Test endpoint":
        raise AssertionError(f"Expected summary='Test endpoint', got {desc.doc.summary}")
    
    return


def test_attach_at_stores_extra_kwargs_in_extras():
    """Test that additional kwargs are stored in descriptor.extras."""
    registry = EndpointRegistry()
    
    @Endpoint.attach_at(
        leaf="extras",
        custom_field="custom_value",
        another_field=123
    )
    def extras_handler():
        pass
    
    registry.collect_from(extras_handler)
    descriptors = registry.collect()
    desc = descriptors[0]
    
    if desc.extras.get("custom_field") != "custom_value":
        raise AssertionError(f"Expected custom_field='custom_value', got {desc.extras.get('custom_field')}")
    
    if desc.extras.get("another_field") != 123:
        raise AssertionError(f"Expected another_field=123, got {desc.extras.get('another_field')}")
    
    return


def test_collect_raises_conflict_error_on_duplicate():
    """Test that collecting two handlers at one path+method conflicts."""
    registry = EndpointRegistry()

    @Endpoint.attach_at(leaf="conflict", methods=["GET"])
    def first_handler():
        pass

    @Endpoint.attach_at(leaf="conflict", methods=["GET"])
    def second_handler():
        pass

    # Decorating raises nothing: attach_at marks the handler and has no
    # other effect, so two handlers may claim the same location as long as
    # no single application takes both. The conflict is a property of a
    # registry, and is detected when one is asked to hold both.
    registry.collect_from(first_handler)

    error_raised = False

    try:
        registry.collect_from(second_handler)
    except EndpointConflictError:
        error_raised = True

    if not error_raised:
        raise AssertionError("Expected EndpointConflictError to be raised")

    return


def test_separate_registries_do_not_conflict():
    """Two applications may each serve the same path without conflicting."""
    registry_one = EndpointRegistry()
    registry_two = EndpointRegistry()

    @Endpoint.attach_at(leaf="shared", methods=["GET"])
    def handler_one():
        pass

    @Endpoint.attach_at(leaf="shared", methods=["GET"])
    def handler_two():
        pass

    registry_one.collect_from(handler_one)
    registry_two.collect_from(handler_two)

    if len(registry_one.collect()) != 1:
        raise AssertionError("Expected 1 descriptor in the first registry")

    if len(registry_two.collect()) != 1:
        raise AssertionError("Expected 1 descriptor in the second registry")

    return


def test_attach_at_allows_replace_on_conflict():
    """Test that attach_at allows replacement when on_conflict='replace'."""
    registry = EndpointRegistry()
    
    @Endpoint.attach_at(leaf="replace", methods=["GET"])
    def first_handler():
        pass
    
    @Endpoint.attach_at(leaf="replace", methods=["GET"], on_conflict="replace")
    def second_handler():
        pass
    
    registry.collect_from(first_handler, second_handler)
    descriptors = registry.collect()
    
    # Should have only one descriptor (the replacement)
    if len(descriptors) != 1:
        raise AssertionError(f"Expected 1 descriptor after replace, got {len(descriptors)}")
    
    if descriptors[0].handler is not second_handler:
        raise AssertionError("Expected descriptor handler to be second_handler")
    
    return


# =============================================================================
# Task 5.3: attach_child() classmethod
# =============================================================================

def test_attach_child_creates_descriptor():
    """Test that attach_child creates an EndpointDescriptor."""
    
    class ParentEndpoint(Endpoint):
        base_path = "/api/v1"
    
    class ChildEndpoint(Endpoint):
        methods = ["GET", "POST"]
    
    descriptor = ParentEndpoint.attach_child(ChildEndpoint, leaf="users")
    
    if not isinstance(descriptor, EndpointDescriptor):
        raise AssertionError("attach_child should return an EndpointDescriptor")
    
    if descriptor.path != "/api/v1/users":
        raise AssertionError(f"Expected path='/api/v1/users', got {descriptor.path}")
    
    if descriptor.methods != ["GET", "POST"]:
        raise AssertionError(f"Expected methods=['GET', 'POST'], got {descriptor.methods}")
    
    return


def test_attach_child_computes_relative_path_from_base_path():
    """Test that attach_child computes path relative to parent's base_path."""
    
    class ParentEndpoint(Endpoint):
        base_path = "/api/v1"
    
    class ChildEndpoint(Endpoint):
        pass
    
    descriptor = ParentEndpoint.attach_child(ChildEndpoint, leaf="portals")
    
    if descriptor.path != "/api/v1/portals":
        raise AssertionError(f"Expected path='/api/v1/portals', got {descriptor.path}")
    
    return


def test_attach_child_computes_relative_path_from_base_leaf():
    """Test that attach_child computes path relative to parent's base_leaf."""
    
    class ParentEndpoint(Endpoint):
        base_leaf = "api"
    
    class ChildEndpoint(Endpoint):
        pass
    
    descriptor = ParentEndpoint.attach_child(ChildEndpoint, leaf="users")
    
    if descriptor.path != "/api/users":
        raise AssertionError(f"Expected path='/api/users', got {descriptor.path}")
    
    return


def test_attach_child_inherits_parent_constraints():
    """Test that attach_child inherits parent constraints when child doesn't set them."""
    
    class ParentEndpoint(Endpoint):
        base_path = "/api"
        access_policy = AccessPolicy(roles=["user"])
        rate_limit = RateLimit(requests=100, window=60)
    
    class ChildEndpoint(Endpoint):
        pass
    
    descriptor = ParentEndpoint.attach_child(ChildEndpoint, leaf="items")
    
    # Child should inherit parent's constraints
    if descriptor.constraints.access_policy.roles != ("user",):
        raise AssertionError(f"Expected roles=['user'], got {descriptor.constraints.access_policy.roles}")
    
    if descriptor.constraints.rate_limit.requests != 100:
        raise AssertionError(f"Expected requests=100, got {descriptor.constraints.rate_limit.requests}")
    
    return


def test_attach_child_merges_constraints():
    """Test that attach_child merges parent and child constraints."""
    
    class ParentEndpoint(Endpoint):
        base_path = "/api"
        access_policy = AccessPolicy(roles=["user"], scopes=["read"])
    
    class ChildEndpoint(Endpoint):
        access_policy = AccessPolicy(roles=["admin"], scopes=["write"])
    
    descriptor = ParentEndpoint.attach_child(ChildEndpoint, leaf="admin")
    
    # Constraints should be merged (union by default)
    if "user" not in descriptor.constraints.access_policy.roles:
        raise AssertionError("Expected 'user' in merged roles")
    
    if "admin" not in descriptor.constraints.access_policy.roles:
        raise AssertionError("Expected 'admin' in merged roles")
    
    if "read" not in descriptor.constraints.access_policy.scopes:
        raise AssertionError("Expected 'read' in merged scopes")
    
    if "write" not in descriptor.constraints.access_policy.scopes:
        raise AssertionError("Expected 'write' in merged scopes")
    
    return


def test_attach_child_allows_placement_overrides():
    """Test that attach_child allows overriding child's placement."""
    
    class ParentEndpoint(Endpoint):
        base_path = "/api/v1"
    
    class ChildEndpoint(Endpoint):
        base_leaf = "default"
        methods = ["GET"]
    
    descriptor = ParentEndpoint.attach_child(
        ChildEndpoint,
        leaf="override",
        methods=["POST", "PUT"]
    )
    
    if descriptor.path != "/api/v1/override":
        raise AssertionError(f"Expected path='/api/v1/override', got {descriptor.path}")
    
    if descriptor.methods != ["POST", "PUT"]:
        raise AssertionError(f"Expected methods=['POST', 'PUT'], got {descriptor.methods}")
    
    return


def test_attach_child_inherits_version_from_parent():
    """Test that attach_child inherits version from parent when child doesn't set it."""
    
    class ParentEndpoint(Endpoint):
        base_path = "/api"
        version = "v2"
    
    class ChildEndpoint(Endpoint):
        pass
    
    descriptor = ParentEndpoint.attach_child(ChildEndpoint, leaf="items")
    
    if descriptor.version != "v2":
        raise AssertionError(f"Expected version='v2', got {descriptor.version}")
    
    return


def test_attach_child_child_version_overrides_parent():
    """Test that child's version overrides parent's version."""
    
    class ParentEndpoint(Endpoint):
        base_path = "/api"
        version = "v1"
    
    class ChildEndpoint(Endpoint):
        version = "v2"
    
    descriptor = ParentEndpoint.attach_child(ChildEndpoint, leaf="items")
    
    if descriptor.version != "v2":
        raise AssertionError(f"Expected version='v2', got {descriptor.version}")
    
    return


def test_attach_child_merge_tags_appends_parent_tags():
    """Test that merge_tags=True appends parent tags to child tags."""
    
    class ParentEndpoint(Endpoint):
        base_path = "/api"
        tags = ["api", "v1"]
    
    class ChildEndpoint(Endpoint):
        tags = ["users"]
    
    descriptor = ParentEndpoint.attach_child(
        ChildEndpoint,
        leaf="users",
        merge_tags=True
    )
    
    # Child tags should include both child and parent tags
    if "users" not in descriptor.tags:
        raise AssertionError("Expected 'users' in merged tags")
    
    if "api" not in descriptor.tags:
        raise AssertionError("Expected 'api' in merged tags")
    
    if "v1" not in descriptor.tags:
        raise AssertionError("Expected 'v1' in merged tags")
    
    return


def test_attach_child_default_tags_behavior():
    """Test that by default child tags win over parent tags."""
    
    class ParentEndpoint(Endpoint):
        base_path = "/api"
        tags = ["api", "v1"]
    
    class ChildEndpoint(Endpoint):
        tags = ["users"]
    
    descriptor = ParentEndpoint.attach_child(ChildEndpoint, leaf="users")
    
    # Child tags should win (default behavior)
    if descriptor.tags != ["users"]:
        raise AssertionError(f"Expected tags=['users'], got {descriptor.tags}")
    
    return


def test_attach_child_parent_placement_composes_nested_prefix():
    """Test that Endpoint.attach_child composes a nested child under the parent's placement."""
    
    class RootEndpoint(Endpoint):
        base_path = "/api"
        access_policy = AccessPolicy(roles=["user"])
        tags = ["api"]
    
    class V1Endpoint(Endpoint):
        base_path = "/v1"
    
    class UsersEndpoint(Endpoint):
        base_leaf = "users"
    
    v1_desc = RootEndpoint.attach_child(V1Endpoint)
    users_desc = V1Endpoint.attach_child(UsersEndpoint, parent_placement=v1_desc)
    
    if v1_desc.path != "/api/v1":
        raise AssertionError(f"Expected path='/api/v1', got {v1_desc.path}")
    
    if users_desc.path != "/api/v1/users":
        raise AssertionError(f"Expected path='/api/v1/users', got {users_desc.path}")
    
    if users_desc.constraints.access_policy is None or users_desc.constraints.access_policy.roles != ("user",):
        raise AssertionError(f"Expected Root's policy to cascade, got {users_desc.constraints.access_policy}")
    
    if users_desc.tags != ["api"]:
        raise AssertionError(f"Expected Root's tags to cascade, got {users_desc.tags}")
    
    # Single-level behavior is unchanged without a placement
    standalone_desc = V1Endpoint.attach_child(UsersEndpoint)
    if standalone_desc.path != "/v1/users":
        raise AssertionError(f"Expected path='/v1/users', got {standalone_desc.path}")
    
    return


def test_attach_child_parent_placement_with_rest_blueprint():
    """Test that RestBlueprint (which uses Endpoint.attach_child) composes nested prefixes."""
    
    from ccai.webworks.endpoints.restblueprint import RestBlueprint
    
    class ApiBlueprint(RestBlueprint):
        base_path = "/api"
    
    class PortalBlueprint(RestBlueprint):
        base_leaf = "magic"
    
    class PortalEndpoint(Endpoint):
        base_leaf = "portals"
    
    portal_placement = ApiBlueprint.attach_child(PortalBlueprint)
    portals_desc = PortalBlueprint.attach_child(PortalEndpoint, parent_placement=portal_placement)
    
    if portals_desc.path != "/api/magic/portals":
        raise AssertionError(f"Expected path='/api/magic/portals', got {portals_desc.path}")
    
    return


def test_attach_child_parent_placement_with_leaf_only():
    """Test that a placement carrying only a leaf (parent without a base) is composed as /<leaf>."""
    
    class RootEndpoint(Endpoint):
        pass
    
    class V1Endpoint(Endpoint):
        base_leaf = "v1"
    
    class UsersEndpoint(Endpoint):
        base_leaf = "users"
    
    # Root has no base, so attaching V1 under a leaf override yields a
    # placement that carries only that leaf.
    v1_desc = RootEndpoint.attach_child(V1Endpoint, leaf="version1")
    users_desc = V1Endpoint.attach_child(UsersEndpoint, parent_placement=v1_desc)
    
    if v1_desc.path is not None or v1_desc.leaf != "version1":
        raise AssertionError(f"Expected a leaf-only placement, got path={v1_desc.path}, leaf={v1_desc.leaf}")
    
    if users_desc.path != "/version1/users":
        raise AssertionError(f"Expected path='/version1/users', got {users_desc.path}")
    
    return


# =============================================================================
# BUG-1 Regression: _dataclass_to_schema required-field detection
# =============================================================================

def test_dataclass_to_schema_detects_required_fields():
    """Test that _dataclass_to_schema correctly distinguishes required from optional fields."""
    
    from dataclasses import dataclass, field
    
    @dataclass
    class SampleSchema:
        name: str              # Required (no default)
        age: int               # Required (no default)
        email: str = ""        # Optional (has default)
        tags: list = field(default_factory=list)  # Optional (has default_factory)
    
    schema = Endpoint._dataclass_to_schema(SampleSchema)
    
    # Verify basic structure
    if schema["type"] != "object":
        raise AssertionError(f"Expected type 'object', got {schema['type']}")
    
    if "properties" not in schema:
        raise AssertionError("Expected 'properties' key in schema")
    
    # Verify all four fields are present
    prop_names = set(schema["properties"].keys())
    if prop_names != {"name", "age", "email", "tags"}:
        raise AssertionError(f"Expected properties {{name, age, email, tags}}, got {prop_names}")
    
    # Verify required fields
    if "required" not in schema:
        raise AssertionError("Expected 'required' key in schema")
    
    required = set(schema["required"])
    
    if "name" not in required:
        raise AssertionError("Expected 'name' to be required")
    
    if "age" not in required:
        raise AssertionError("Expected 'age' to be required")
    
    if "email" in required:
        raise AssertionError("Expected 'email' to NOT be required (has default)")
    
    if "tags" in required:
        raise AssertionError("Expected 'tags' to NOT be required (has default_factory)")
    
    return


def test_dataclass_to_schema_no_required_fields():
    """Test that _dataclass_to_schema omits 'required' key when all fields have defaults."""
    
    from dataclasses import dataclass, field
    
    @dataclass
    class AllOptional:
        name: str = "unknown"
        count: int = 0
        items: list = field(default_factory=list)
    
    schema = Endpoint._dataclass_to_schema(AllOptional)
    
    if "required" in schema:
        raise AssertionError(f"Expected no 'required' key when all fields have defaults, got {schema['required']}")
    
    return

