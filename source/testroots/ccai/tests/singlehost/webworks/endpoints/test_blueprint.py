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
    Endpoint,
    EndpointDescriptor,
    EndpointRegistry,
    RateLimit,
)


# =============================================================================
# Test Setup - Clear registry before each test
# =============================================================================

def _clear_registry():
    """Build a registry for a test to own."""
    return EndpointRegistry()


# =============================================================================
# Task 6.1: Blueprint class extending Endpoint
# =============================================================================

def test_blueprint_extends_endpoint():
    """Test that Blueprint class extends Endpoint."""
    
    if not issubclass(Blueprint, Endpoint):
        raise AssertionError("Blueprint should be a subclass of Endpoint")
    
    return


def test_blueprint_has_base_path_attribute():
    """Test that Blueprint has base_path class attribute."""
    
    if not hasattr(Blueprint, "base_path"):
        raise AssertionError("Blueprint missing 'base_path' attribute")
    
    if Blueprint.base_path is not None:
        raise AssertionError(f"Expected base_path=None, got {Blueprint.base_path}")
    
    return


def test_blueprint_has_base_leaf_attribute():
    """Test that Blueprint has base_leaf class attribute."""
    
    if not hasattr(Blueprint, "base_leaf"):
        raise AssertionError("Blueprint missing 'base_leaf' attribute")
    
    if Blueprint.base_leaf is not None:
        raise AssertionError(f"Expected base_leaf=None, got {Blueprint.base_leaf}")
    
    return


def test_blueprint_has_merge_tags_attribute():
    """Test that Blueprint has merge_tags class attribute."""
    
    if not hasattr(Blueprint, "merge_tags"):
        raise AssertionError("Blueprint missing 'merge_tags' attribute")
    
    if Blueprint.merge_tags is not False:
        raise AssertionError(f"Expected merge_tags=False, got {Blueprint.merge_tags}")
    
    return


def test_blueprint_subclass_can_set_base_path():
    """Test that Blueprint subclass can set base_path."""
    
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
    
    class ApiBlueprint(Blueprint):
        base_leaf = "api"
    
    if ApiBlueprint.base_leaf != "api":
        raise AssertionError(f"Expected base_leaf='api', got {ApiBlueprint.base_leaf}")
    
    return


def test_blueprint_subclass_can_set_merge_tags():
    """Test that Blueprint subclass can set merge_tags."""
    
    class ApiBlueprint(Blueprint):
        merge_tags = True
    
    if ApiBlueprint.merge_tags is not True:
        raise AssertionError(f"Expected merge_tags=True, got {ApiBlueprint.merge_tags}")
    
    return


def test_blueprint_inherits_endpoint_attributes():
    """Test that Blueprint inherits all Endpoint class attributes."""
    
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
    
    if not hasattr(Blueprint, "register"):
        raise AssertionError("Blueprint missing 'register' method")
    
    if not callable(Blueprint.register):
        raise AssertionError("Blueprint.register should be callable")
    
    return


def test_blueprint_register_returns_list():
    """Test that Blueprint.register() returns a list."""
    
    class ApiBlueprint(Blueprint):
        base_path = "/api"
    
    result = ApiBlueprint.register()
    
    if not isinstance(result, list):
        raise AssertionError(f"Expected list, got {type(result)}")
    
    return


def test_blueprint_register_returns_descriptors():
    """Test that Blueprint.register() returns EndpointDescriptor objects."""
    
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
    
    class EmptyBlueprint(Blueprint):
        base_path = "/empty"
    
    result = EmptyBlueprint.register()
    
    if result != []:
        raise AssertionError(f"Expected empty list, got {result}")
    
    return


def test_blueprint_multiple_methods_single_endpoint():
    """Test that Blueprint handles endpoints with multiple HTTP methods."""
    
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


# =============================================================================
# absolute=True and register() membership
# =============================================================================

def test_blueprint_attach_at_honours_absolute():
    """Blueprint.attach_at(absolute=True) uses the path as written, without the blueprint prefix."""

    class FreeBlueprint(Blueprint):
        base_path = "/free"

    @FreeBlueprint.attach_at(path="/abs", methods=["GET"], absolute=True)
    def absolute_handler(request):
        return {}

    paths = [descriptor.path for descriptor in FreeBlueprint.register()]

    if paths != ["/abs"]:
        raise AssertionError(f"Expected ['/abs'], got {paths}")

    return


def test_blueprint_register_returns_absolute_and_prefixed_routes_together():
    """register() returns a blueprint's absolute route alongside its prefixed ones."""

    class MixedBlueprint(Blueprint):
        base_path = "/mixed"

    @MixedBlueprint.attach_at(leaf="inside", methods=["GET"])
    def inside(request):
        return {}

    @MixedBlueprint.attach_at(path="/outside", methods=["GET"], absolute=True)
    def outside(request):
        return {}

    paths = sorted(descriptor.path for descriptor in MixedBlueprint.register())

    if paths != ["/mixed/inside", "/outside"]:
        raise AssertionError(f"Expected ['/mixed/inside', '/outside'], got {paths}")

    return


def test_blueprint_instance_method_handler_is_bound_when_registered():
    """A handler declared ``def thing(self, request)`` in a Blueprint body is called on an instance."""

    class GreetingBlueprint(Blueprint):
        base_path = "/greeting"
        word = "hi"

        @Blueprint.attach_at(leaf="say", methods=["GET"])
        def say(self, request):
            return {"word": self.word}

    descriptor = GreetingBlueprint.register()[0]

    if descriptor.handler(None) != {"word": "hi"}:
        raise AssertionError("Expected the handler to run bound to a blueprint instance")

    return


# =============================================================================
# Blueprint name recorded for blueprint scoped middleware
# =============================================================================

def test_blueprint_records_its_name_on_free_function_routes():
    """Test that a route attached through a blueprint names the blueprint in its extras."""

    class NamedFreeBlueprint(Blueprint):
        base_path = "/named"

    @NamedFreeBlueprint.attach_at(leaf="items", methods=["GET"])
    def list_items(request):
        return {}

    descriptors = NamedFreeBlueprint.register()

    names = [descriptor.extras.get("blueprint") for descriptor in descriptors]
    if names != ["NamedFreeBlueprint"]:
        raise AssertionError(f"Expected the blueprint name on the route, got {names}")

    return


def test_blueprint_claims_routes_declared_in_its_body():
    """Test that a handler decorated in the class body through the base class names the subclass."""

    class NamedBodyBlueprint(Blueprint):
        base_path = "/body"

        @Blueprint.attach_at(leaf="items", methods=["GET"])
        def list_items(self, request):
            return {}

    descriptors = NamedBodyBlueprint.register()

    names = [descriptor.extras.get("blueprint") for descriptor in descriptors]
    if names != ["NamedBodyBlueprint"]:
        raise AssertionError(f"Expected the subclass name on the route, got {names}")

    return


def test_blueprint_keeps_an_explicit_blueprint_name():
    """Test that attach_at(blueprint=...) chooses the name recorded on the route."""

    class ExplicitNameBlueprint(Blueprint):
        base_path = "/explicit"

    @ExplicitNameBlueprint.attach_at(leaf="items", methods=["GET"], blueprint="shop")
    def list_items(request):
        return {}

    descriptors = ExplicitNameBlueprint.register()

    names = [descriptor.extras.get("blueprint") for descriptor in descriptors]
    if names != ["shop"]:
        raise AssertionError(f"Expected the explicit name on the route, got {names}")

    return


def test_blueprint_names_the_routes_of_an_attached_child():
    """Test that the handlers of an attached plain endpoint belong to the attaching blueprint."""

    class NamedChildEndpoint(Endpoint):
        pass

    @NamedChildEndpoint.attach_at(path="/child", methods=["GET"])
    def child_handler(request):
        return {}

    class NamedParentBlueprint(Blueprint):
        base_path = "/parent"

    NamedParentBlueprint.attach_child(NamedChildEndpoint)

    descriptors = NamedParentBlueprint.register()

    names = [descriptor.extras.get("blueprint") for descriptor in descriptors]
    if names != ["NamedParentBlueprint"]:
        raise AssertionError(f"Expected the parent blueprint name on the child route, got {names}")

    return


def test_blueprint_scoped_middleware_runs_for_the_blueprint_routes():
    """Test that middleware registered at scope='blueprint' under the class name runs for its routes."""
    from ccai.webworks.routing.dispatcher import Dispatcher
    from ccai.webworks.routing.middlewareregistry import MiddlewareRegistry
    from ccai.webworks.routing.request import Request
    from ccai.webworks.routing.router import Router

    class MiddlewareShopBlueprint(Blueprint):
        base_path = "/mwshop"

    @MiddlewareShopBlueprint.attach_at(leaf="items", methods=["GET"])
    def list_items(request):
        return {"ok": True}

    seen = []

    def blueprint_middleware(request, call_next):
        seen.append(request.path)
        return call_next(request)

    registry = MiddlewareRegistry()
    registry.register(blueprint_middleware, scope="blueprint", scope_key="MiddlewareShopBlueprint")

    router = Router()
    MiddlewareShopBlueprint.register(router=router)
    dispatcher = Dispatcher(router, registry=registry)

    response = dispatcher.dispatch(Request(method="GET", path="/mwshop/items"))

    if response.status_code != 200 or seen != ["/mwshop/items"]:
        raise AssertionError(f"Expected the blueprint middleware to run, got {response.status_code} {seen}")

    return


# =============================================================================
# rest_processing on Blueprint.attach_at
# =============================================================================

from dataclasses import dataclass as _rest_dataclass

from ccai.webworks.endpoints.descriptor import REST_MANAGED_EXTRA, REST_PROCESSING_EXTRA


@_rest_dataclass
class _BlueprintSchema:
    """Request schema of the rest_processing tests."""
    name: str


def test_blueprint_attach_at_records_rest_processing_and_class_default():
    """
        Test that Blueprint routes record REST processing, and that a
        blueprint class setting rest_processing = False opts its routes out.
    """
    class _ManagedBlueprint(Blueprint):
        base_path = "/rp/bp"

    class _RawBlueprint(Blueprint):
        base_path = "/rp/rawbp"
        rest_processing = False

    @_ManagedBlueprint.attach_at(leaf="managed", methods=["POST"], request_schema=_BlueprintSchema)
    def managed(request):
        return None

    @_RawBlueprint.attach_at(leaf="raw", methods=["POST"], request_schema=_BlueprintSchema)
    def raw(request):
        return None

    managed_descriptor = Endpoint._find_descriptors_for_handler(managed)[0]
    raw_descriptor = Endpoint._find_descriptors_for_handler(raw)[0]

    if managed_descriptor.extras["rest"].get(REST_MANAGED_EXTRA) is not True:
        raise AssertionError(f"Expected a REST managed route, got {managed_descriptor.extras['rest']}")

    if raw_descriptor.extras["rest"].get(REST_PROCESSING_EXTRA) is not False:
        raise AssertionError(f"Expected the class default to opt out, got {raw_descriptor.extras['rest']}")

    return
