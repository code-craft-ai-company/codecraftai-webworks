"""
.. module:: test_resourceendpoint
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Tests for the ResourceEndpoint class providing CRUD operation helpers.

    This module contains unit tests and property-based tests for the
    ResourceEndpoint class, including HTTP method to CRUD operation mapping,
    route registration, and resource URL generation.

.. moduleauthor:: Code Craft AI LLC
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []

import random
from dataclasses import dataclass
from typing import Any

from ccai.webworks.endpoints.rest import (
    ResourceEndpoint,
    METHOD_TO_OPERATION,
    METHOD_STATUS_CODES,
    ALL_CRUD_METHODS,
)


# =============================================================================
# Test Fixtures
# =============================================================================

@dataclass
class TestResource:
    """Test resource with an ID for testing get_resource_url."""
    id: int
    name: str


class TestUserEndpoint(ResourceEndpoint):
    """Test endpoint for users resource."""
    resource_name = "users"
    id_param = "{id:int}"
    
    def get(self, id: Any) -> Any:
        return {"id": id, "name": "Test User"}
    
    def create(self, payload: Any) -> Any:
        return {"id": 1, "name": payload.get("name", "New User")}
    
    def update(self, id: Any, payload: Any) -> Any:
        return {"id": id, "name": payload.get("name", "Updated User")}
    
    def partial_update(self, id: Any, payload: Any) -> Any:
        return {"id": id, "name": payload.get("name", "Patched User")}
    
    def delete(self, id: Any) -> None:
        pass


class ReadOnlyEndpoint(ResourceEndpoint):
    """Test endpoint with only GET allowed."""
    resource_name = "readonly"
    allowed_methods = ["GET"]


class WriteOnlyEndpoint(ResourceEndpoint):
    """Test endpoint with only POST allowed."""
    resource_name = "writeonly"
    allowed_methods = ["POST"]


class PartialCrudEndpoint(ResourceEndpoint):
    """Test endpoint with partial CRUD methods."""
    resource_name = "partial"
    allowed_methods = ["GET", "POST", "DELETE"]


# =============================================================================
# Unit Tests: METHOD_TO_OPERATION Mapping
# =============================================================================

def test_method_to_operation_get():
    """GET should map to 'get' operation."""
    if METHOD_TO_OPERATION.get("GET") != "get":
        raise AssertionError(f"Expected 'get', got '{METHOD_TO_OPERATION.get('GET')}'")


def test_method_to_operation_post():
    """POST should map to 'create' operation."""
    if METHOD_TO_OPERATION.get("POST") != "create":
        raise AssertionError(f"Expected 'create', got '{METHOD_TO_OPERATION.get('POST')}'")


def test_method_to_operation_put():
    """PUT should map to 'update' operation."""
    if METHOD_TO_OPERATION.get("PUT") != "update":
        raise AssertionError(f"Expected 'update', got '{METHOD_TO_OPERATION.get('PUT')}'")


def test_method_to_operation_patch():
    """PATCH should map to 'partial_update' operation."""
    if METHOD_TO_OPERATION.get("PATCH") != "partial_update":
        raise AssertionError(f"Expected 'partial_update', got '{METHOD_TO_OPERATION.get('PATCH')}'")


def test_method_to_operation_delete():
    """DELETE should map to 'delete' operation."""
    if METHOD_TO_OPERATION.get("DELETE") != "delete":
        raise AssertionError(f"Expected 'delete', got '{METHOD_TO_OPERATION.get('DELETE')}'")


def test_method_to_operation_all_crud_methods_mapped():
    """All CRUD methods should have a mapping."""
    for method in ALL_CRUD_METHODS:
        if method not in METHOD_TO_OPERATION:
            raise AssertionError(f"Method '{method}' not in METHOD_TO_OPERATION")


# =============================================================================
# Unit Tests: METHOD_STATUS_CODES Mapping
# =============================================================================

def test_method_status_codes_get():
    """GET should have status code 200."""
    if METHOD_STATUS_CODES.get("GET") != 200:
        raise AssertionError(f"Expected 200, got {METHOD_STATUS_CODES.get('GET')}")


def test_method_status_codes_post():
    """POST should have status code 201 (Created)."""
    if METHOD_STATUS_CODES.get("POST") != 201:
        raise AssertionError(f"Expected 201, got {METHOD_STATUS_CODES.get('POST')}")


def test_method_status_codes_put():
    """PUT should have status code 200."""
    if METHOD_STATUS_CODES.get("PUT") != 200:
        raise AssertionError(f"Expected 200, got {METHOD_STATUS_CODES.get('PUT')}")


def test_method_status_codes_patch():
    """PATCH should have status code 200."""
    if METHOD_STATUS_CODES.get("PATCH") != 200:
        raise AssertionError(f"Expected 200, got {METHOD_STATUS_CODES.get('PATCH')}")


def test_method_status_codes_delete():
    """DELETE should have status code 204 (No Content)."""
    if METHOD_STATUS_CODES.get("DELETE") != 204:
        raise AssertionError(f"Expected 204, got {METHOD_STATUS_CODES.get('DELETE')}")


# =============================================================================
# Unit Tests: ResourceEndpoint Class Attributes
# =============================================================================

def test_resource_endpoint_default_id_param():
    """ResourceEndpoint should have default id_param of '{id:int}'."""
    if ResourceEndpoint.id_param != "{id:int}":
        raise AssertionError(f"Expected '{{id:int}}', got '{ResourceEndpoint.id_param}'")


def test_resource_endpoint_default_allowed_methods_none():
    """ResourceEndpoint should have allowed_methods as None by default."""
    if ResourceEndpoint.allowed_methods is not None:
        raise AssertionError(f"Expected None, got {ResourceEndpoint.allowed_methods}")


def test_resource_endpoint_default_resource_name_none():
    """ResourceEndpoint should have resource_name as None by default."""
    if ResourceEndpoint.resource_name is not None:
        raise AssertionError(f"Expected None, got {ResourceEndpoint.resource_name}")


# =============================================================================
# Unit Tests: CRUD Method Stubs
# =============================================================================

def test_crud_method_get_raises_not_implemented():
    """get() should raise NotImplementedError when not overridden."""
    endpoint = ResourceEndpoint()
    raised = False
    try:
        endpoint.get(1)
    except NotImplementedError as e:
        raised = True
        if "get()" not in str(e):
            raise AssertionError(f"Expected 'get()' in error message, got '{e}'")
    
    if not raised:
        raise AssertionError("get() should raise NotImplementedError")


def test_crud_method_create_raises_not_implemented():
    """create() should raise NotImplementedError when not overridden."""
    endpoint = ResourceEndpoint()
    raised = False
    try:
        endpoint.create({})
    except NotImplementedError as e:
        raised = True
        if "create()" not in str(e):
            raise AssertionError(f"Expected 'create()' in error message, got '{e}'")
    
    if not raised:
        raise AssertionError("create() should raise NotImplementedError")


def test_crud_method_update_raises_not_implemented():
    """update() should raise NotImplementedError when not overridden."""
    endpoint = ResourceEndpoint()
    raised = False
    try:
        endpoint.update(1, {})
    except NotImplementedError as e:
        raised = True
        if "update()" not in str(e):
            raise AssertionError(f"Expected 'update()' in error message, got '{e}'")
    
    if not raised:
        raise AssertionError("update() should raise NotImplementedError")


def test_crud_method_partial_update_raises_not_implemented():
    """partial_update() should raise NotImplementedError when not overridden."""
    endpoint = ResourceEndpoint()
    raised = False
    try:
        endpoint.partial_update(1, {})
    except NotImplementedError as e:
        raised = True
        if "partial_update()" not in str(e):
            raise AssertionError(f"Expected 'partial_update()' in error message, got '{e}'")
    
    if not raised:
        raise AssertionError("partial_update() should raise NotImplementedError")


def test_crud_method_delete_raises_not_implemented():
    """delete() should raise NotImplementedError when not overridden."""
    endpoint = ResourceEndpoint()
    raised = False
    try:
        endpoint.delete(1)
    except NotImplementedError as e:
        raised = True
        if "delete()" not in str(e):
            raise AssertionError(f"Expected 'delete()' in error message, got '{e}'")
    
    if not raised:
        raise AssertionError("delete() should raise NotImplementedError")


# =============================================================================
# Unit Tests: get_operation_for_method
# =============================================================================

def test_get_operation_for_method_get():
    """get_operation_for_method('GET') should return 'get'."""
    result = ResourceEndpoint.get_operation_for_method("GET")
    if result != "get":
        raise AssertionError(f"Expected 'get', got '{result}'")


def test_get_operation_for_method_post():
    """get_operation_for_method('POST') should return 'create'."""
    result = ResourceEndpoint.get_operation_for_method("POST")
    if result != "create":
        raise AssertionError(f"Expected 'create', got '{result}'")


def test_get_operation_for_method_lowercase():
    """get_operation_for_method should handle lowercase methods."""
    result = ResourceEndpoint.get_operation_for_method("get")
    if result != "get":
        raise AssertionError(f"Expected 'get', got '{result}'")


def test_get_operation_for_method_unknown():
    """get_operation_for_method should return None for unknown methods."""
    result = ResourceEndpoint.get_operation_for_method("OPTIONS")
    if result is not None:
        raise AssertionError(f"Expected None, got '{result}'")


# =============================================================================
# Unit Tests: get_method_for_operation
# =============================================================================

def test_get_method_for_operation_get():
    """get_method_for_operation('get') should return 'GET'."""
    result = ResourceEndpoint.get_method_for_operation("get")
    if result != "GET":
        raise AssertionError(f"Expected 'GET', got '{result}'")


def test_get_method_for_operation_create():
    """get_method_for_operation('create') should return 'POST'."""
    result = ResourceEndpoint.get_method_for_operation("create")
    if result != "POST":
        raise AssertionError(f"Expected 'POST', got '{result}'")


def test_get_method_for_operation_unknown():
    """get_method_for_operation should return None for unknown operations."""
    result = ResourceEndpoint.get_method_for_operation("unknown")
    if result is not None:
        raise AssertionError(f"Expected None, got '{result}'")


# =============================================================================
# Unit Tests: get_default_status_code
# =============================================================================

def test_get_default_status_code_get():
    """get_default_status_code('GET') should return 200."""
    result = ResourceEndpoint.get_default_status_code("GET")
    if result != 200:
        raise AssertionError(f"Expected 200, got {result}")


def test_get_default_status_code_post():
    """get_default_status_code('POST') should return 201."""
    result = ResourceEndpoint.get_default_status_code("POST")
    if result != 201:
        raise AssertionError(f"Expected 201, got {result}")


def test_get_default_status_code_delete():
    """get_default_status_code('DELETE') should return 204."""
    result = ResourceEndpoint.get_default_status_code("DELETE")
    if result != 204:
        raise AssertionError(f"Expected 204, got {result}")


def test_get_default_status_code_unknown():
    """get_default_status_code should return 200 for unknown methods."""
    result = ResourceEndpoint.get_default_status_code("OPTIONS")
    if result != 200:
        raise AssertionError(f"Expected 200, got {result}")


# =============================================================================
# Unit Tests: get_effective_allowed_methods
# =============================================================================

def test_get_effective_allowed_methods_default():
    """get_effective_allowed_methods should return all CRUD methods when None."""
    result = ResourceEndpoint.get_effective_allowed_methods()
    if set(result) != set(ALL_CRUD_METHODS):
        raise AssertionError(f"Expected all CRUD methods, got {result}")


def test_get_effective_allowed_methods_read_only():
    """get_effective_allowed_methods should return configured methods."""
    result = ReadOnlyEndpoint.get_effective_allowed_methods()
    if result != ["GET"]:
        raise AssertionError(f"Expected ['GET'], got {result}")


def test_get_effective_allowed_methods_partial():
    """get_effective_allowed_methods should return partial list."""
    result = PartialCrudEndpoint.get_effective_allowed_methods()
    if set(result) != {"GET", "POST", "DELETE"}:
        raise AssertionError(f"Expected GET, POST, DELETE, got {result}")


# =============================================================================
# Unit Tests: get_resource_url
# =============================================================================

def test_get_resource_url_with_dataclass():
    """get_resource_url should extract id from dataclass."""
    endpoint = TestUserEndpoint()
    resource = TestResource(id=123, name="Test")
    
    result = endpoint.get_resource_url(resource)
    
    if result != "/users/123":
        raise AssertionError(f"Expected '/users/123', got '{result}'")


def test_get_resource_url_with_dict():
    """get_resource_url should extract id from dict."""
    endpoint = TestUserEndpoint()
    resource = {"id": 456, "name": "Test"}
    
    result = endpoint.get_resource_url(resource)
    
    if result != "/users/456":
        raise AssertionError(f"Expected '/users/456', got '{result}'")


def test_get_resource_url_with_none():
    """get_resource_url should return None for None resource."""
    endpoint = TestUserEndpoint()
    
    result = endpoint.get_resource_url(None)
    
    if result is not None:
        raise AssertionError(f"Expected None, got '{result}'")


def test_get_resource_url_without_id():
    """get_resource_url should return None when resource has no id."""
    endpoint = TestUserEndpoint()
    resource = {"name": "No ID"}
    
    result = endpoint.get_resource_url(resource)
    
    if result is not None:
        raise AssertionError(f"Expected None, got '{result}'")


def test_get_resource_url_without_resource_name():
    """get_resource_url should return None when resource_name not set."""
    endpoint = ResourceEndpoint()
    resource = {"id": 123}
    
    result = endpoint.get_resource_url(resource)
    
    if result is not None:
        raise AssertionError(f"Expected None, got '{result}'")


def test_get_resource_url_with_pk_attribute():
    """get_resource_url should try 'pk' as alternative id attribute."""
    
    @dataclass
    class ResourceWithPk:
        pk: int
        name: str
    
    endpoint = TestUserEndpoint()
    resource = ResourceWithPk(pk=789, name="Test")
    
    result = endpoint.get_resource_url(resource)
    
    if result != "/users/789":
        raise AssertionError(f"Expected '/users/789', got '{result}'")


# =============================================================================
# Unit Tests: Subclass Implementation
# =============================================================================

def test_subclass_get_implementation():
    """Subclass should be able to implement get()."""
    endpoint = TestUserEndpoint()
    result = endpoint.get(42)
    
    if result.get("id") != 42:
        raise AssertionError(f"Expected id 42, got {result.get('id')}")


def test_subclass_create_implementation():
    """Subclass should be able to implement create()."""
    endpoint = TestUserEndpoint()
    result = endpoint.create({"name": "Alice"})
    
    if result.get("name") != "Alice":
        raise AssertionError(f"Expected name 'Alice', got {result.get('name')}")


def test_subclass_update_implementation():
    """Subclass should be able to implement update()."""
    endpoint = TestUserEndpoint()
    result = endpoint.update(1, {"name": "Bob"})
    
    if result.get("name") != "Bob":
        raise AssertionError(f"Expected name 'Bob', got {result.get('name')}")


def test_subclass_partial_update_implementation():
    """Subclass should be able to implement partial_update()."""
    endpoint = TestUserEndpoint()
    result = endpoint.partial_update(1, {"name": "Charlie"})
    
    if result.get("name") != "Charlie":
        raise AssertionError(f"Expected name 'Charlie', got {result.get('name')}")


def test_subclass_delete_implementation():
    """Subclass should be able to implement delete()."""
    endpoint = TestUserEndpoint()
    # Should not raise
    endpoint.delete(1)


# =============================================================================
# Property-Based Tests
# =============================================================================

# Feature: rest-api-support, Property 1: HTTP Method to CRUD Operation Mapping
# *For any* ResourceEndpoint and any HTTP method in allowed_methods, the method
# SHALL be correctly mapped to its corresponding CRUD operation
# (GET→get, POST→create, PUT→update, PATCH→partial_update, DELETE→delete).
# **Validates: Requirements 1.2, 1.3, 1.7**

def test_property_1_http_method_to_crud_operation_mapping():
    """
        Property 1: HTTP Method to CRUD Operation Mapping
        
        For any ResourceEndpoint and any HTTP method in allowed_methods,
        the method SHALL be correctly mapped to its corresponding CRUD
        operation (GET→get, POST→create, PUT→update, PATCH→partial_update,
        DELETE→delete).
        
        **Validates: Requirements 1.2, 1.3, 1.7**
    """
    # Define the expected mapping
    expected_mapping = {
        "GET": "get",
        "POST": "create",
        "PUT": "update",
        "PATCH": "partial_update",
        "DELETE": "delete",
    }
    
    # Run 100 iterations with random configurations
    for iteration in range(100):
        # Generate a random subset of allowed methods
        num_methods = random.randint(1, len(ALL_CRUD_METHODS))
        random_methods = random.sample(ALL_CRUD_METHODS, num_methods)
        
        # Property 1: For each method in allowed_methods, the mapping must be correct
        for method in random_methods:
            operation = ResourceEndpoint.get_operation_for_method(method)
            expected_operation = expected_mapping.get(method)
            
            if operation != expected_operation:
                errmsg = (
                    f"Iteration {iteration}: Method '{method}' mapped to '{operation}', "
                    f"expected '{expected_operation}'"
                )
                raise AssertionError(errmsg)
        
        # Property 2: The reverse mapping must also be correct
        for method in random_methods:
            expected_operation = expected_mapping.get(method)
            reverse_method = ResourceEndpoint.get_method_for_operation(expected_operation)
            
            if reverse_method != method:
                errmsg = (
                    f"Iteration {iteration}: Operation '{expected_operation}' mapped to "
                    f"'{reverse_method}', expected '{method}'"
                )
                raise AssertionError(errmsg)
        
        # Property 3: METHOD_TO_OPERATION constant must match class method
        for method in random_methods:
            constant_operation = METHOD_TO_OPERATION.get(method)
            class_operation = ResourceEndpoint.get_operation_for_method(method)
            
            if constant_operation != class_operation:
                errmsg = (
                    f"Iteration {iteration}: Constant mapping '{constant_operation}' "
                    f"differs from class method '{class_operation}' for '{method}'"
                )
                raise AssertionError(errmsg)
        
        # Property 4: All methods in allowed_methods must have a valid operation
        for method in random_methods:
            operation = ResourceEndpoint.get_operation_for_method(method)
            
            if operation is None:
                errmsg = (
                    f"Iteration {iteration}: Method '{method}' has no operation mapping"
                )
                raise AssertionError(errmsg)
        
        # Property 5: get_effective_allowed_methods returns correct methods
        # Create a dynamic endpoint class with the random methods
        class DynamicEndpoint(ResourceEndpoint):
            resource_name = "dynamic"
            allowed_methods = random_methods
        
        effective_methods = DynamicEndpoint.get_effective_allowed_methods()
        
        if set(effective_methods) != set(random_methods):
            errmsg = (
                f"Iteration {iteration}: Effective methods {effective_methods} "
                f"don't match configured {random_methods}"
            )
            raise AssertionError(errmsg)
        
        # Property 6: When allowed_methods is None, all CRUD methods are allowed
        class AllMethodsEndpoint(ResourceEndpoint):
            resource_name = "all"
            allowed_methods = None
        
        all_effective = AllMethodsEndpoint.get_effective_allowed_methods()
        
        if set(all_effective) != set(ALL_CRUD_METHODS):
            errmsg = (
                f"Iteration {iteration}: With allowed_methods=None, expected all CRUD "
                f"methods {ALL_CRUD_METHODS}, got {all_effective}"
            )
            raise AssertionError(errmsg)
        
        # Property 7: Status codes are correctly mapped for each method
        for method in random_methods:
            status_code = ResourceEndpoint.get_default_status_code(method)
            expected_status = METHOD_STATUS_CODES.get(method)
            
            if status_code != expected_status:
                errmsg = (
                    f"Iteration {iteration}: Method '{method}' has status {status_code}, "
                    f"expected {expected_status}"
                )
                raise AssertionError(errmsg)
    
    return

