"""
    Tests for the RestBlueprint class.
    
    This module contains tests for the RestBlueprint class which provides
    REST API collections with shared versioning, tags, and authentication
    requirements.
"""

from dataclasses import dataclass
from typing import List, Optional

from automojo.webworks.endpoints.accesspolicy import AccessPolicy
from automojo.webworks.endpoints.doc import Doc
from automojo.webworks.endpoints.ratelimit import RateLimit
from automojo.webworks.endpoints.registry import EndpointRegistry
from automojo.webworks.endpoints.restblueprint import RestBlueprint


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
    from automojo.webworks.endpoints.restendpoint import RestEndpoint
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
    EndpointRegistry.clear()
    
    class ApiBlueprint(RestBlueprint):
        base_path = "/api/v1"
    
    @ApiBlueprint.attach_at(leaf="users")
    def list_users():
        pass
    
    descriptors = EndpointRegistry.collect()
    assert len(descriptors) == 1
    assert descriptors[0].path == "/api/v1/users"


def test_restblueprint_attach_at_computes_path_from_base_leaf():
    """Test that attach_at computes path relative to base_leaf."""
    EndpointRegistry.clear()
    
    class ApiBlueprint(RestBlueprint):
        base_leaf = "api"
    
    @ApiBlueprint.attach_at(leaf="status")
    def get_status():
        pass
    
    descriptors = EndpointRegistry.collect()
    assert len(descriptors) == 1
    assert descriptors[0].path == "/api/status"


def test_restblueprint_attach_at_with_absolute_path():
    """Test that attach_at with absolute=True overrides base path."""
    EndpointRegistry.clear()
    
    class ApiBlueprint(RestBlueprint):
        base_path = "/api/v1"
    
    @ApiBlueprint.attach_at(path="/health", absolute=True)
    def health_check():
        pass
    
    descriptors = EndpointRegistry.collect()
    assert len(descriptors) == 1
    assert descriptors[0].path == "/health"


def test_restblueprint_tag_merging_default():
    """Test that tags are merged by default (not replaced)."""
    EndpointRegistry.clear()
    
    class ApiBlueprint(RestBlueprint):
        base_path = "/api"
        tags = ["api", "v1"]
    
    @ApiBlueprint.attach_at(leaf="users", tags=["users"])
    def list_users():
        pass
    
    descriptors = EndpointRegistry.collect()
    assert len(descriptors) == 1
    # Child tags + parent tags merged
    assert "users" in descriptors[0].tags
    assert "api" in descriptors[0].tags
    assert "v1" in descriptors[0].tags


def test_restblueprint_tag_replacement():
    """Test that replace_tags=True causes child tags to replace parent tags."""
    EndpointRegistry.clear()
    
    class ApiBlueprint(RestBlueprint):
        base_path = "/api"
        tags = ["api", "v1"]
        replace_tags = True
    
    @ApiBlueprint.attach_at(leaf="users", tags=["users"])
    def list_users():
        pass
    
    descriptors = EndpointRegistry.collect()
    assert len(descriptors) == 1
    # Only child tags, parent tags replaced
    assert descriptors[0].tags == ["users"]


def test_restblueprint_version_inheritance():
    """Test that version is inherited from blueprint."""
    EndpointRegistry.clear()
    
    class ApiBlueprint(RestBlueprint):
        base_path = "/api"
        version = "v2"
    
    @ApiBlueprint.attach_at(leaf="users")
    def list_users():
        pass
    
    descriptors = EndpointRegistry.collect()
    assert len(descriptors) == 1
    assert descriptors[0].version == "v2"


def test_restblueprint_version_override():
    """Test that version can be overridden in attach_at."""
    EndpointRegistry.clear()
    
    class ApiBlueprint(RestBlueprint):
        base_path = "/api"
        version = "v1"
    
    @ApiBlueprint.attach_at(leaf="users", version="v3")
    def list_users():
        pass
    
    descriptors = EndpointRegistry.collect()
    assert len(descriptors) == 1
    assert descriptors[0].version == "v3"


def test_restblueprint_register_returns_descriptors():
    """Test that register() returns list of descriptors."""
    EndpointRegistry.clear()
    
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
    EndpointRegistry.clear()
    
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
    descriptors = ApiBlueprint.register(router=router)
    
    assert len(router.endpoints) == 1
    assert router.endpoints[0].path == "/api/users"


def test_restblueprint_add_crud_registers_list_endpoint():
    """Test that add_crud registers list endpoint."""
    EndpointRegistry.clear()
    
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
    EndpointRegistry.clear()
    
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
    EndpointRegistry.clear()
    
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
    EndpointRegistry.clear()
    
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
    EndpointRegistry.clear()
    
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
    EndpointRegistry.clear()
    
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
    EndpointRegistry.clear()
    
    policy = AccessPolicy(roles=["admin"], scopes=["read"])
    
    class ApiBlueprint(RestBlueprint):
        base_path = "/api"
        access_policy = policy
    
    @ApiBlueprint.attach_at(leaf="users")
    def list_users():
        pass
    
    descriptors = EndpointRegistry.collect()
    assert len(descriptors) == 1
    assert descriptors[0].constraints.access_policy == policy


def test_restblueprint_inherits_rate_limit():
    """Test that child endpoints inherit rate_limit from blueprint."""
    EndpointRegistry.clear()
    
    limit = RateLimit(requests=100, window=60)
    
    class ApiBlueprint(RestBlueprint):
        base_path = "/api"
        rate_limit = limit
    
    @ApiBlueprint.attach_at(leaf="users")
    def list_users():
        pass
    
    descriptors = EndpointRegistry.collect()
    assert len(descriptors) == 1
    assert descriptors[0].constraints.rate_limit == limit


def test_restblueprint_schema_inspection():
    """Test that schema inspection works for REST endpoints."""
    EndpointRegistry.clear()
    
    class ApiBlueprint(RestBlueprint):
        base_path = "/api"
    
    @ApiBlueprint.attach_at(leaf="users", response_schema=UserSchema)
    def list_users():
        pass
    
    descriptors = EndpointRegistry.collect()
    assert len(descriptors) == 1
    assert "rest" in descriptors[0].extras
    assert "response_schema" in descriptors[0].extras["rest"]
