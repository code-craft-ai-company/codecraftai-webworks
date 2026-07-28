"""
.. module:: test_restendpoint
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Tests for the RestEndpoint class.

.. moduleauthor:: Code Craft AI LLC
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []

from dataclasses import dataclass
from typing import List, Optional

from ccai.webworks.endpoints import (
    AccessPolicy,
    Doc,
    EndpointRegistry,
    RateLimit,
    RestEndpoint,
    SchemaInspectionError,
    EndpointRegistrationError,
)


# ============================================================================
# Test Fixtures - Dataclass schemas for testing
# ============================================================================

@dataclass
class UserSchema:
    """Test schema representing a user."""
    id: int
    name: str
    email: str


@dataclass
class UserCreateSchema:
    """Test schema for creating a user."""
    name: str
    email: str


@dataclass
class ErrorSchema:
    """Test schema for error responses."""
    code: int
    message: str


@dataclass
class OptionalFieldsSchema:
    """Test schema with optional fields."""
    required_field: str
    optional_field: Optional[str] = None


@dataclass
class ListFieldSchema:
    """Test schema with list fields."""
    items: List[str]
    count: int


# ============================================================================
# Helper function
# ============================================================================

def _clear_registry():
    """Helper to clear the registry before tests."""
    registry = EndpointRegistry()
# ============================================================================
# Test: RestEndpoint class structure
# ============================================================================

def test_restendpoint_inherits_from_endpoint():
    """RestEndpoint should inherit from Endpoint."""
    from ccai.webworks.endpoints.endpoint import Endpoint
    
    if not issubclass(RestEndpoint, Endpoint):
        raise AssertionError("RestEndpoint should be a subclass of Endpoint")


def test_restendpoint_has_rest_specific_attributes():
    """RestEndpoint should have REST-specific class attributes."""
    if not hasattr(RestEndpoint, "request_schema"):
        raise AssertionError("RestEndpoint should have request_schema attribute")
    
    if not hasattr(RestEndpoint, "response_schema"):
        raise AssertionError("RestEndpoint should have response_schema attribute")
    
    if not hasattr(RestEndpoint, "error_map"):
        raise AssertionError("RestEndpoint should have error_map attribute")
    
    if not hasattr(RestEndpoint, "summary"):
        raise AssertionError("RestEndpoint should have summary attribute")
    
    if not hasattr(RestEndpoint, "description"):
        raise AssertionError("RestEndpoint should have description attribute")


def test_restendpoint_default_attributes():
    """RestEndpoint default attributes should be None or empty."""
    if RestEndpoint.request_schema is not None:
        raise AssertionError("Default request_schema should be None")
    
    if RestEndpoint.response_schema is not None:
        raise AssertionError("Default response_schema should be None")
    
    if RestEndpoint.error_map != {}:
        raise AssertionError("Default error_map should be empty dict")
    
    if RestEndpoint.summary is not None:
        raise AssertionError("Default summary should be None")
    
    if RestEndpoint.description is not None:
        raise AssertionError("Default description should be None")


# ============================================================================
# Test: RestEndpoint.attach_at with schema inspection
# ============================================================================

def test_attach_at_with_dataclass_request_schema():
    """attach_at should inspect dataclass request schemas."""
    registry = EndpointRegistry()
    _clear_registry()
    
    @RestEndpoint.attach_at(leaf="users", methods=["POST"], request_schema=UserCreateSchema)
    def create_user():
        pass
    
    registry.collect_from(create_user)
    descriptors = registry.collect()
    if len(descriptors) != 1:
        raise AssertionError(f"Should have one descriptor, got {len(descriptors)}")
    
    descriptor = descriptors[0]
    if "rest" not in descriptor.extras:
        raise AssertionError("Descriptor should have 'rest' in extras")
    
    if "request_schema" not in descriptor.extras["rest"]:
        raise AssertionError("REST extras should have request_schema")
    
    schema = descriptor.extras["rest"]["request_schema"]
    if schema["type"] != "object":
        raise AssertionError(f"Schema type should be object, got {schema['type']}")
    
    if "properties" not in schema:
        raise AssertionError("Schema should have properties")
    
    if "name" not in schema["properties"]:
        raise AssertionError("Schema should have 'name' property")
    
    if "email" not in schema["properties"]:
        raise AssertionError("Schema should have 'email' property")


def test_attach_at_with_dataclass_response_schema():
    """attach_at should inspect dataclass response schemas."""
    registry = EndpointRegistry()
    _clear_registry()
    
    @RestEndpoint.attach_at(leaf="users", methods=["GET"], response_schema=UserSchema)
    def get_users():
        pass
    
    registry.collect_from(get_users)
    descriptors = registry.collect()
    descriptor = descriptors[0]
    
    if "response_schema" not in descriptor.extras["rest"]:
        raise AssertionError("REST extras should have response_schema")
    
    schema = descriptor.extras["rest"]["response_schema"]
    if schema["type"] != "object":
        raise AssertionError(f"Schema type should be object, got {schema['type']}")
    
    if "id" not in schema["properties"]:
        raise AssertionError("Schema should have 'id' property")


def test_attach_at_with_error_map():
    """attach_at should inspect error map schemas."""
    registry = EndpointRegistry()
    _clear_registry()
    
    @RestEndpoint.attach_at(
        leaf="users",
        methods=["GET"],
        error_map={400: ErrorSchema, 404: ErrorSchema}
    )
    def get_user():
        pass
    
    registry.collect_from(get_user)
    descriptors = registry.collect()
    descriptor = descriptors[0]
    
    if "error_map" not in descriptor.extras["rest"]:
        raise AssertionError("REST extras should have error_map")
    
    error_map = descriptor.extras["rest"]["error_map"]
    if 400 not in error_map:
        raise AssertionError("Error map should have 400 status")
    
    if 404 not in error_map:
        raise AssertionError("Error map should have 404 status")


def test_attach_at_with_optional_fields_schema():
    """attach_at should correctly handle schemas with optional fields."""
    registry = EndpointRegistry()
    _clear_registry()
    
    @RestEndpoint.attach_at(leaf="optional", methods=["POST"], request_schema=OptionalFieldsSchema)
    def create_optional():
        pass
    
    registry.collect_from(create_optional)
    descriptors = registry.collect()
    descriptor = descriptors[0]
    
    schema = descriptor.extras["rest"]["request_schema"]
    if "required" not in schema:
        raise AssertionError("Schema should have required field")
    
    if "required_field" not in schema["required"]:
        raise AssertionError("required_field should be in required list")


def test_attach_at_with_list_fields_schema():
    """attach_at should correctly handle schemas with list fields."""
    registry = EndpointRegistry()
    _clear_registry()
    
    @RestEndpoint.attach_at(leaf="lists", methods=["POST"], request_schema=ListFieldSchema)
    def create_list():
        pass
    
    registry.collect_from(create_list)
    descriptors = registry.collect()
    descriptor = descriptors[0]
    
    schema = descriptor.extras["rest"]["request_schema"]
    if "items" not in schema["properties"]:
        raise AssertionError("Schema should have 'items' property")
    
    items_schema = schema["properties"]["items"]
    if items_schema["type"] != "array":
        raise AssertionError(f"items should be array type, got {items_schema['type']}")


# ============================================================================
# Test: RestEndpoint class attribute inheritance
# ============================================================================

def test_subclass_inherits_rest_attributes():
    """Subclass should inherit REST-specific attributes."""
    registry = EndpointRegistry()
    _clear_registry()
    
    class UserEndpoint(RestEndpoint):
        request_schema = UserCreateSchema
        response_schema = UserSchema
        summary = "User operations"
        description = "Endpoints for user management"
    
    @UserEndpoint.attach_at(leaf="users", methods=["POST"])
    def create_user():
        pass
    
    registry.collect_from(create_user)
    descriptors = registry.collect()
    descriptor = descriptors[0]
    
    # Should have inherited schemas
    if "request_schema" not in descriptor.extras["rest"]:
        raise AssertionError("Should inherit request_schema from class")
    
    if "response_schema" not in descriptor.extras["rest"]:
        raise AssertionError("Should inherit response_schema from class")
    
    # Should have doc from class summary/description
    if descriptor.doc is None:
        raise AssertionError("Should have doc from class attributes")
    
    if descriptor.doc.summary != "User operations":
        raise AssertionError(f"Doc summary should match class summary, got {descriptor.doc.summary}")


def test_kwargs_override_class_attributes():
    """Explicit kwargs should override class attributes."""
    registry = EndpointRegistry()
    _clear_registry()
    
    class UserEndpoint(RestEndpoint):
        request_schema = UserCreateSchema
        summary = "Default summary"
    
    custom_doc = Doc(summary="Custom summary")
    
    @UserEndpoint.attach_at(
        leaf="users",
        methods=["POST"],
        request_schema=ErrorSchema,  # Override class schema
        doc=custom_doc  # Override class summary
    )
    def create_user():
        pass
    
    registry.collect_from(create_user)
    descriptors = registry.collect()
    descriptor = descriptors[0]
    
    # Should use kwarg schema, not class schema
    schema = descriptor.extras["rest"]["request_schema"]
    if "code" not in schema["properties"]:
        raise AssertionError("Should use ErrorSchema (has 'code'), not UserCreateSchema")
    
    # Should use kwarg doc
    if descriptor.doc.summary != "Custom summary":
        raise AssertionError(f"Should use custom doc, not class summary, got {descriptor.doc.summary}")


# ============================================================================
# Test: CRUD helper methods
# ============================================================================

def test_read_helper_uses_get_method():
    """read() helper should use GET method."""
    registry = EndpointRegistry()
    _clear_registry()
    
    @RestEndpoint.read(leaf="users", response_schema=UserSchema)
    def get_users():
        pass
    
    descriptors = registry.collect()
    descriptor = descriptors[0]
    
    if descriptor.methods != ["GET"]:
        raise AssertionError(f"read() should use GET method, got {descriptor.methods}")


def test_create_helper_uses_post_method():
    """create() helper should use POST method."""
    registry = EndpointRegistry()
    _clear_registry()
    
    @RestEndpoint.create(leaf="users", request_schema=UserCreateSchema)
    def create_user():
        pass
    
    descriptors = registry.collect()
    descriptor = descriptors[0]
    
    if descriptor.methods != ["POST"]:
        raise AssertionError(f"create() should use POST method, got {descriptor.methods}")


def test_update_helper_uses_put_patch_methods():
    """update() helper should use PUT and PATCH methods."""
    registry = EndpointRegistry()
    _clear_registry()
    
    @RestEndpoint.update(leaf="users", request_schema=UserCreateSchema)
    def update_user():
        pass
    
    descriptors = registry.collect()
    descriptor = descriptors[0]
    
    if descriptor.methods != ["PUT", "PATCH"]:
        raise AssertionError(f"update() should use PUT and PATCH methods, got {descriptor.methods}")


def test_delete_helper_uses_delete_method():
    """delete() helper should use DELETE method."""
    registry = EndpointRegistry()
    _clear_registry()
    
    @RestEndpoint.delete(leaf="users")
    def delete_user():
        pass
    
    descriptors = registry.collect()
    descriptor = descriptors[0]
    
    if descriptor.methods != ["DELETE"]:
        raise AssertionError(f"delete() should use DELETE method, got {descriptor.methods}")


def test_crud_helpers_preserve_function_identity():
    """CRUD helpers should return the original function unchanged."""
    _clear_registry()
    
    def original_read():
        pass
    
    def original_create():
        pass
    
    def original_update():
        pass
    
    def original_delete():
        pass
    
    decorated_read = RestEndpoint.read(leaf="r")(original_read)
    decorated_create = RestEndpoint.create(leaf="c")(original_create)
    decorated_update = RestEndpoint.update(leaf="u")(original_update)
    decorated_delete = RestEndpoint.delete(leaf="d")(original_delete)
    
    if decorated_read is not original_read:
        raise AssertionError("read() should return original function")
    
    if decorated_create is not original_create:
        raise AssertionError("create() should return original function")
    
    if decorated_update is not original_update:
        raise AssertionError("update() should return original function")
    
    if decorated_delete is not original_delete:
        raise AssertionError("delete() should return original function")


def test_crud_helpers_accept_all_parameters():
    """CRUD helpers should accept all standard parameters."""
    registry = EndpointRegistry()
    _clear_registry()
    
    policy = AccessPolicy(roles=["admin"])
    limit = RateLimit(requests=10, window=60)
    doc = Doc(summary="Test endpoint")
    
    @RestEndpoint.read(
        leaf="test",
        version="v1",
        tags=["test"],
        access_policy=policy,
        rate_limit=limit,
        response_schema=UserSchema,
        error_map={404: ErrorSchema},
        doc=doc,
        custom_extra="value"
    )
    def test_handler():
        pass
    
    descriptors = registry.collect()
    descriptor = descriptors[0]
    
    if descriptor.version != "v1":
        raise AssertionError(f"Should have version, got {descriptor.version}")
    
    if descriptor.tags != ["test"]:
        raise AssertionError(f"Should have tags, got {descriptor.tags}")
    
    if descriptor.constraints.access_policy != policy:
        raise AssertionError("Should have access_policy")
    
    if descriptor.constraints.rate_limit != limit:
        raise AssertionError("Should have rate_limit")
    
    if descriptor.extras.get("custom_extra") != "value":
        raise AssertionError(f"Should have custom extra, got {descriptor.extras.get('custom_extra')}")


# ============================================================================
# Test: Decorator identity preservation
# ============================================================================

def test_attach_at_returns_original_function():
    """attach_at should return the original function unchanged."""
    _clear_registry()
    
    def original_handler():
        return "original"
    
    decorated = RestEndpoint.attach_at(leaf="test")(original_handler)
    
    if decorated is not original_handler:
        raise AssertionError("Decorated function should be identical to original")
    
    if decorated() != "original":
        raise AssertionError("Decorated function should work the same as original")


def test_attach_at_allows_decorator_stacking():
    """attach_at should allow stacking with other decorators."""
    _clear_registry()
    
    def custom_decorator(func):
        func.custom_attr = "custom"
        return func
    
    @custom_decorator
    @RestEndpoint.attach_at(leaf="test")
    def handler():
        pass
    
    if not hasattr(handler, "custom_attr"):
        raise AssertionError("Custom decorator should have been applied")
    
    if handler.custom_attr != "custom":
        raise AssertionError("Custom decorator attribute should be preserved")


# ============================================================================
# Test: Error handling
# ============================================================================

def test_attach_at_raises_on_missing_leaf_and_path():
    """attach_at should raise EndpointRegistrationError when both leaf and path are missing."""
    _clear_registry()
    
    raised = False
    error_instance = None
    
    try:
        @RestEndpoint.attach_at(methods=["GET"])
        def handler():
            pass
    except EndpointRegistrationError as err:
        raised = True
        error_instance = err
    
    if not raised:
        raise AssertionError("Should raise EndpointRegistrationError")
    
    if "leaf" not in error_instance.missing_fields and "path" not in error_instance.missing_fields:
        raise AssertionError("Error should indicate missing leaf/path")
