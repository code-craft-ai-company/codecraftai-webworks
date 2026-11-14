"""
    Tests for the RestBlueprint class.
    
    This module contains tests for the RestBlueprint class which provides
    REST API collections with shared versioning, tags, and authentication
    requirements.
"""

from dataclasses import dataclass

from ccai.webworks.endpoints.accesspolicy import AccessPolicy
from ccai.webworks.endpoints.ratelimit import RateLimit
from ccai.webworks.endpoints.registry import EndpointRegistry
from ccai.webworks.endpoints.restblueprint import RestBlueprint


# Test schema for CRUD operations
@dataclass
class UserSchema:
    """Test schema for user resources."""
    id: str
    name: str
    email: str


def test_restblueprint_has_base_path_attribute():
    """Test that RestBlueprint has base_path class attribute."""
    assert hasattr(RestBlueprint, "base_path")
    assert RestBlueprint.base_path is None


def test_restblueprint_has_base_leaf_attribute():
    """Test that RestBlueprint has base_leaf class attribute."""
    assert hasattr(RestBlueprint, "base_leaf")
    assert RestBlueprint.base_leaf is None


def test_restblueprint_has_replace_tags_attribute():
    """Test that RestBlueprint has replace_tags class attribute."""
    assert hasattr(RestBlueprint, "replace_tags")
    assert RestBlueprint.replace_tags is False


def test_restblueprint_extends_restendpoint():
    """Test that RestBlueprint extends RestEndpoint."""
    from ccai.webworks.endpoints.restendpoint import RestEndpoint
    assert issubclass(RestBlueprint, RestEndpoint)


def test_restblueprint_has_register_method():
    """Test that RestBlueprint has register() method."""
    assert hasattr(RestBlueprint, "register")
    assert callable(RestBlueprint.register)


def test_restblueprint_has_add_crud_method():
    """Test that RestBlueprint has add_crud() method."""
    assert hasattr(RestBlueprint, "add_crud")
    assert callable(RestBlueprint.add_crud)


def test_restblueprint_attach_at_computes_path_from_base():
    """Test that attach_at computes path relative to base_path."""
    registry = EndpointRegistry()
    class ApiBlueprint(RestBlueprint):
        base_path = "/api/v1"
    
    @ApiBlueprint.attach_at(leaf="users")
    def list_users():
        pass
    
    registry.collect_from(list_users)
    descriptors = registry.collect()
    assert len(descriptors) == 1
    assert descriptors[0].path == "/api/v1/users"


def test_restblueprint_attach_at_computes_path_from_base_leaf():
    """Test that attach_at computes path relative to base_leaf."""
    registry = EndpointRegistry()
    class ApiBlueprint(RestBlueprint):
        base_leaf = "api"
    
    @ApiBlueprint.attach_at(leaf="status")
    def get_status():
        pass
    
    registry.collect_from(get_status)
    descriptors = registry.collect()
    assert len(descriptors) == 1
    assert descriptors[0].path == "/api/status"


def test_restblueprint_attach_at_with_absolute_path():
    """Test that attach_at with absolute=True overrides base path."""
    registry = EndpointRegistry()
    class ApiBlueprint(RestBlueprint):
        base_path = "/api/v1"
    
    @ApiBlueprint.attach_at(path="/health", absolute=True)
    def health_check():
        pass
    
    registry.collect_from(health_check)
    descriptors = registry.collect()
    assert len(descriptors) == 1
    assert descriptors[0].path == "/health"


def test_restblueprint_tag_merging_default():
    """Test that tags are merged by default (not replaced)."""
    registry = EndpointRegistry()
    class ApiBlueprint(RestBlueprint):
        base_path = "/api"
        tags = ["api", "v1"]
    
    @ApiBlueprint.attach_at(leaf="users", tags=["users"])
    def list_users():
        pass
    
    registry.collect_from(list_users)
    descriptors = registry.collect()
    assert len(descriptors) == 1
    # Child tags + parent tags merged
    assert "users" in descriptors[0].tags
    assert "api" in descriptors[0].tags
    assert "v1" in descriptors[0].tags


def test_restblueprint_tag_replacement():
    """Test that replace_tags=True causes child tags to replace parent tags."""
    registry = EndpointRegistry()
    class ApiBlueprint(RestBlueprint):
        base_path = "/api"
        tags = ["api", "v1"]
        replace_tags = True
    
    @ApiBlueprint.attach_at(leaf="users", tags=["users"])
    def list_users():
        pass
    
    registry.collect_from(list_users)
    descriptors = registry.collect()
    assert len(descriptors) == 1
    # Only child tags, parent tags replaced
    assert descriptors[0].tags == ["users"]


def test_restblueprint_version_inheritance():
    """Test that version is inherited from blueprint."""
    registry = EndpointRegistry()
    class ApiBlueprint(RestBlueprint):
        base_path = "/api"
        version = "v2"
    
    @ApiBlueprint.attach_at(leaf="users")
    def list_users():
        pass
    
    registry.collect_from(list_users)
    descriptors = registry.collect()
    assert len(descriptors) == 1
    assert descriptors[0].version == "v2"


def test_restblueprint_version_override():
    """Test that version can be overridden in attach_at."""
    registry = EndpointRegistry()
    class ApiBlueprint(RestBlueprint):
        base_path = "/api"
        version = "v1"
    
    @ApiBlueprint.attach_at(leaf="users", version="v3")
    def list_users():
        pass
    
    registry.collect_from(list_users)
    descriptors = registry.collect()
    assert len(descriptors) == 1
    assert descriptors[0].version == "v3"


def test_restblueprint_register_returns_descriptors():
    """Test that register() returns list of descriptors."""
    class ApiBlueprint(RestBlueprint):
        base_path = "/api"
    
    @ApiBlueprint.attach_at(leaf="users")
    def list_users():
        pass
    
    @ApiBlueprint.attach_at(leaf="items")
    def list_items():
        pass
    
    descriptors = ApiBlueprint.register()
    assert len(descriptors) == 2


def test_restblueprint_register_with_router():
    """Test that register() calls router.add_endpoint for each descriptor."""
    class MockRouter:
        def __init__(self):
            self.endpoints = []
        
        def add_endpoint(self, descriptor):
            self.endpoints.append(descriptor)
    
    class ApiBlueprint(RestBlueprint):
        base_path = "/api"
    
    @ApiBlueprint.attach_at(leaf="users")
    def list_users():
        pass
    
    router = MockRouter()
    ApiBlueprint.register(router=router)
    
    assert len(router.endpoints) == 1
    assert router.endpoints[0].path == "/api/users"


def test_restblueprint_add_crud_registers_list_endpoint():
    """Test that add_crud registers list endpoint."""
    class ApiBlueprint(RestBlueprint):
        base_path = "/api"
    
    def list_users():
        pass
    
    descriptors = ApiBlueprint.add_crud(
        resource="users",
        schema=UserSchema,
        list_handler=list_users
    )
    
    assert len(descriptors) == 1
    assert descriptors[0].path == "/api/users"
    assert descriptors[0].methods == ["GET"]
    assert descriptors[0].doc.summary == "List Users"


def test_restblueprint_add_crud_registers_create_endpoint():
    """Test that add_crud registers create endpoint."""
    class ApiBlueprint(RestBlueprint):
        base_path = "/api"
    
    def create_user():
        pass
    
    descriptors = ApiBlueprint.add_crud(
        resource="users",
        schema=UserSchema,
        create_handler=create_user
    )
    
    assert len(descriptors) == 1
    assert descriptors[0].path == "/api/users"
    assert descriptors[0].methods == ["POST"]
    assert descriptors[0].doc.summary == "Create Users"


def test_restblueprint_add_crud_registers_read_endpoint():
    """Test that add_crud registers read endpoint."""
    class ApiBlueprint(RestBlueprint):
        base_path = "/api"
    
    def get_user():
        pass
    
    descriptors = ApiBlueprint.add_crud(
        resource="users",
        schema=UserSchema,
        read_handler=get_user
    )
    
    assert len(descriptors) == 1
    assert descriptors[0].path == "/api/users/{id}"
    assert descriptors[0].methods == ["GET"]
    assert descriptors[0].doc.summary == "Get Users"


def test_restblueprint_add_crud_registers_update_endpoint():
    """Test that add_crud registers update endpoint."""
    class ApiBlueprint(RestBlueprint):
        base_path = "/api"
    
    def update_user():
        pass
    
    descriptors = ApiBlueprint.add_crud(
        resource="users",
        schema=UserSchema,
        update_handler=update_user
    )
    
    assert len(descriptors) == 1
    assert descriptors[0].path == "/api/users/{id}"
    assert "PUT" in descriptors[0].methods
    assert "PATCH" in descriptors[0].methods
    assert descriptors[0].doc.summary == "Update Users"


def test_restblueprint_add_crud_registers_delete_endpoint():
    """Test that add_crud registers delete endpoint."""
    class ApiBlueprint(RestBlueprint):
        base_path = "/api"
    
    def delete_user():
        pass
    
    descriptors = ApiBlueprint.add_crud(
        resource="users",
        schema=UserSchema,
        delete_handler=delete_user
    )
    
    assert len(descriptors) == 1
    assert descriptors[0].path == "/api/users/{id}"
    assert descriptors[0].methods == ["DELETE"]
    assert descriptors[0].doc.summary == "Delete Users"


def test_restblueprint_add_crud_registers_all_endpoints():
    """Test that add_crud registers all CRUD endpoints when all handlers provided."""
    class ApiBlueprint(RestBlueprint):
        base_path = "/api"
    
    def list_users():
        pass
    
    def create_user():
        pass
    
    def get_user():
        pass
    
    def update_user():
        pass
    
    def delete_user():
        pass
    
    descriptors = ApiBlueprint.add_crud(
        resource="users",
        schema=UserSchema,
        list_handler=list_users,
        create_handler=create_user,
        read_handler=get_user,
        update_handler=update_user,
        delete_handler=delete_user
    )
    
    assert len(descriptors) == 5


def test_restblueprint_inherits_access_policy():
    """Test that child endpoints inherit access_policy from blueprint."""
    registry = EndpointRegistry()
    policy = AccessPolicy(roles=["admin"], scopes=["read"])
    
    class ApiBlueprint(RestBlueprint):
        base_path = "/api"
        access_policy = policy
    
    @ApiBlueprint.attach_at(leaf="users")
    def list_users():
        pass
    
    registry.collect_from(list_users)
    descriptors = registry.collect()
    assert len(descriptors) == 1
    assert descriptors[0].constraints.access_policy == policy


def test_restblueprint_inherits_rate_limit():
    """Test that child endpoints inherit rate_limit from blueprint."""
    registry = EndpointRegistry()
    limit = RateLimit(requests=100, window=60)
    
    class ApiBlueprint(RestBlueprint):
        base_path = "/api"
        rate_limit = limit
    
    @ApiBlueprint.attach_at(leaf="users")
    def list_users():
        pass
    
    registry.collect_from(list_users)
    descriptors = registry.collect()
    assert len(descriptors) == 1
    assert descriptors[0].constraints.rate_limit == limit


def test_restblueprint_schema_inspection():
    """Test that schema inspection works for REST endpoints."""
    registry = EndpointRegistry()
    class ApiBlueprint(RestBlueprint):
        base_path = "/api"
    
    @ApiBlueprint.attach_at(leaf="users", response_schema=UserSchema)
    def list_users():
        pass
    
    registry.collect_from(list_users)
    descriptors = registry.collect()
    assert len(descriptors) == 1
    assert "rest" in descriptors[0].extras
    assert "response_schema" in descriptors[0].extras["rest"]


# =============================================================================
# Policy composition, absolute routes and class-body handlers
# =============================================================================

def test_child_access_policy_merges_with_blueprint_policy():
    """A per-handler access policy adds to the blueprint's policy; it does not replace it."""

    class AdminBlueprint(RestBlueprint):
        base_path = "/admin"
        access_policy = AccessPolicy(roles=["admin"])

    @AdminBlueprint.attach_at(leaf="reports", methods=["GET"], access_policy=AccessPolicy(scopes=["reports:read"]))
    def reports(request):
        return {}

    policy = AdminBlueprint.register()[0].constraints.access_policy

    assert "admin" in policy.roles, f"blueprint role lost: {policy.roles}"
    assert "reports:read" in policy.scopes, f"handler scope lost: {policy.scopes}"


def test_child_without_policy_inherits_blueprint_policy():
    """A handler that gives no access policy takes the blueprint's unchanged."""

    class AdminBlueprint(RestBlueprint):
        base_path = "/admin"
        access_policy = AccessPolicy(roles=["admin"])

    @AdminBlueprint.attach_at(leaf="status", methods=["GET"])
    def status(request):
        return {}

    policy = AdminBlueprint.register()[0].constraints.access_policy

    assert tuple(policy.roles) == ("admin",)


def test_child_rate_limit_cannot_loosen_blueprint_rate_limit():
    """The most restrictive of the blueprint's and the handler's rate limits applies."""

    class LimitedBlueprint(RestBlueprint):
        base_path = "/limited"
        rate_limit = RateLimit(requests=5, window=60)

    @LimitedBlueprint.attach_at(leaf="burst", methods=["GET"], rate_limit=RateLimit(requests=500, window=60))
    def burst(request):
        return {}

    rate_limit = LimitedBlueprint.register()[0].constraints.rate_limit

    assert rate_limit.requests == 5, f"expected the blueprint's stricter limit, got {rate_limit.requests}"


def test_handler_in_class_body_takes_the_subclass_policy():
    """A handler written in the blueprint's own body carries that blueprint's access policy."""

    class SecuredBlueprint(RestBlueprint):
        base_path = "/secured"
        access_policy = AccessPolicy(roles=["admin"])

        @staticmethod
        @RestBlueprint.attach_at(leaf="thing", methods=["GET"])
        def thing(request):
            return {}

    descriptor = SecuredBlueprint.register()[0]
    policy = descriptor.constraints.access_policy

    assert policy is not None, "the subclass's access policy was not applied"
    assert "admin" in policy.roles
    assert list(descriptor.constraints.roles) == ["admin"]


def test_register_returns_absolute_routes():
    """A handler declared absolute=True is returned by register() although it sits outside the base path."""

    class ApiBlueprint(RestBlueprint):
        base_path = "/api"

    @ApiBlueprint.attach_at(path="/health", methods=["GET"], absolute=True)
    def health(request):
        return {}

    paths = [descriptor.path for descriptor in ApiBlueprint.register()]

    assert paths == ["/health"], f"expected ['/health'], got {paths}"


def test_register_returns_handlers_from_other_modules_when_blueprint_has_no_base():
    """A blueprint with no base path returns every handler declared through it, whatever module defines it."""

    class LooseBlueprint(RestBlueprint):
        pass

    def elsewhere(request):
        return {}

    elsewhere.__module__ = "some.other.module"
    LooseBlueprint.attach_at(leaf="elsewhere", methods=["GET"])(elsewhere)

    paths = [descriptor.path for descriptor in LooseBlueprint.register()]

    assert paths == ["/elsewhere"], f"expected ['/elsewhere'], got {paths}"


def test_absolute_without_path_is_rejected():
    """absolute=True needs the path it should use; a leaf alone is refused."""
    from ccai.webworks.endpoints.exceptions import EndpointRegistrationError

    class ApiBlueprint(RestBlueprint):
        base_path = "/api"

    try:
        ApiBlueprint.attach_at(leaf="health", absolute=True)
    except EndpointRegistrationError:
        pass
    else:
        raise AssertionError("expected EndpointRegistrationError for absolute=True without a path")


def test_instance_method_handler_is_bound_when_registered():
    """A handler declared ``def thing(self, request)`` in a blueprint body answers a request."""
    import json

    from ccai.webworks.routing.dispatcher import Dispatcher
    from ccai.webworks.routing.request import Request
    from ccai.webworks.routing.router import Router

    class InnerBlueprint(RestBlueprint):
        base_path = "/inner"
        greeting = "hello"

        @RestBlueprint.attach_at(leaf="thing", methods=["GET"])
        def thing(self, request):
            return {"greeting": self.greeting, "path": request.path}

    router = Router()
    InnerBlueprint.register(router)

    response = Dispatcher(router).dispatch(Request("GET", "/inner/thing"))

    assert response.status_code == 200, f"expected 200, got {response.status_code}: {response.body!r}"
    assert json.loads(response.body) == {"greeting": "hello", "path": "/inner/thing"}


def test_classmethod_handler_is_bound_to_the_class_when_registered():
    """A handler declared as a classmethod in a blueprint body is called with the class."""

    class CountingBlueprint(RestBlueprint):
        base_path = "/counting"
        label = "counted"

        @classmethod
        @RestBlueprint.attach_at(leaf="label", methods=["GET"])
        def read_label(cls, request):
            return {"label": cls.label}

    descriptor = CountingBlueprint.register()[0]

    assert descriptor.handler(None) == {"label": "counted"}


def test_register_returns_the_same_bound_descriptor_each_call():
    """Binding a class-body handler does not make register() hand out a new descriptor per call."""

    class StableBlueprint(RestBlueprint):
        base_path = "/stable"

        @RestBlueprint.attach_at(leaf="thing", methods=["GET"])
        def thing(self, request):
            return {}

    first = StableBlueprint.register()
    second = StableBlueprint.register()

    assert len(first) == 1
    assert first[0] is second[0]


def test_static_handler_in_class_body_is_left_unbound():
    """A @staticmethod handler is registered as the function it is."""

    class StaticBlueprint(RestBlueprint):
        base_path = "/static"

        @staticmethod
        @RestBlueprint.attach_at(leaf="thing", methods=["GET"])
        def thing(request):
            return {"ok": True}

    descriptor = StaticBlueprint.register()[0]

    assert descriptor.handler is StaticBlueprint.__dict__["thing"].__func__


def test_instance_method_handler_on_unconstructible_blueprint_is_reported():
    """A blueprint that cannot be built without arguments reports that when its instance methods are bound."""
    from ccai.webworks.endpoints.exceptions import EndpointRegistrationError

    class NeedsArgumentBlueprint(RestBlueprint):
        base_path = "/needs"

        def __init__(self, required):
            self.required = required

        @RestBlueprint.attach_at(leaf="thing", methods=["GET"])
        def thing(self, request):
            return {}

    try:
        NeedsArgumentBlueprint.register()
    except EndpointRegistrationError as err:
        assert "NeedsArgumentBlueprint" in str(err)
    else:
        raise AssertionError("expected EndpointRegistrationError")


def test_restblueprint_records_its_name_on_routes():
    """A RestBlueprint route names the blueprint in its extras, also when declared in the class body."""

    class NamedRestBlueprint(RestBlueprint):
        base_path = "/named-rest"

        @RestBlueprint.attach_at(leaf="items", methods=["GET"])
        def list_items(self, request):
            return {}

    @NamedRestBlueprint.attach_at(leaf="other", methods=["GET"])
    def other(request):
        return {}

    names = sorted(descriptor.extras.get("blueprint") for descriptor in NamedRestBlueprint.register())

    assert names == ["NamedRestBlueprint", "NamedRestBlueprint"], names


# =============================================================================
# rest_processing on RestBlueprint.attach_at
# =============================================================================

from ccai.webworks.endpoints.descriptor import REST_MANAGED_EXTRA, REST_PROCESSING_EXTRA


@dataclass
class _BlueprintProcessingIn:
    """Request schema of the rest_processing tests."""
    name: str


def test_restblueprint_attach_at_records_rest_processing():
    """
        Test that RestBlueprint routes record REST processing, and the opt-out.
    """
    class _ProcessingBlueprint(RestBlueprint):
        base_path = "/rp/restbp"

    @_ProcessingBlueprint.attach_at(leaf="managed", methods=["POST"], request_schema=_BlueprintProcessingIn)
    def managed(request):
        return None

    @_ProcessingBlueprint.attach_at(leaf="raw", methods=["POST"], request_schema=_BlueprintProcessingIn, rest_processing=False)
    def raw(request):
        return None

    managed_descriptor = _ProcessingBlueprint._find_descriptors_for_handler(managed)[0]
    raw_descriptor = _ProcessingBlueprint._find_descriptors_for_handler(raw)[0]

    if managed_descriptor.extras["rest"].get(REST_MANAGED_EXTRA) is not True:
        raise AssertionError(f"Expected a REST managed route, got {managed_descriptor.extras['rest']}")

    if raw_descriptor.extras["rest"].get(REST_PROCESSING_EXTRA) is not False:
        raise AssertionError(f"Expected the opt-out, got {raw_descriptor.extras['rest']}")

    return
