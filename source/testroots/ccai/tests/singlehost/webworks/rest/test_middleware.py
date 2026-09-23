"""
.. module:: test_middleware
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Tests for the REST middleware including property-based tests
               for Location header generation and error map inheritance.

    This module contains unit tests and property-based tests for the
    RESTMiddleware class.

.. moduleauthor:: Code Craft AI LLC
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []

import random
import string
from dataclasses import dataclass
from typing import Any, Dict, Optional, Type

from ccai.webworks.endpoints.rest import (
    RESTMiddleware,
    create_rest_middleware,
    SerializerRegistry,
    JSONSerializer,
    Validator,
    ErrorHandler,
    ErrorMapping,
    build_location_header,
    merge_error_maps,
    create_default_registry,
)


# =============================================================================
# Random Data Generators
# =============================================================================

def generate_random_string(min_length: int = 1, max_length: int = 50) -> str:
    """Generate a random string of alphanumeric characters."""
    length = random.randint(min_length, max_length)
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def generate_random_id() -> str:
    """Generate a random resource ID."""
    id_types = ['int', 'uuid', 'slug']
    id_type = random.choice(id_types)
    
    if id_type == 'int':
        return str(random.randint(1, 999999))
    elif id_type == 'uuid':
        # Generate a UUID-like string
        parts = [
            ''.join(random.choices('0123456789abcdef', k=8)),
            ''.join(random.choices('0123456789abcdef', k=4)),
            ''.join(random.choices('0123456789abcdef', k=4)),
            ''.join(random.choices('0123456789abcdef', k=4)),
            ''.join(random.choices('0123456789abcdef', k=12)),
        ]
        return '-'.join(parts)
    else:
        # Generate a slug
        words = [generate_random_string(3, 10).lower() for _ in range(random.randint(1, 3))]
        return '-'.join(words)


def generate_random_resource_name() -> str:
    """Generate a random resource name (URL segment)."""
    names = ['users', 'posts', 'comments', 'products', 'orders', 'items', 'tasks', 'projects']
    return random.choice(names)


def generate_random_status_code() -> int:
    """Generate a random HTTP status code."""
    codes = [400, 401, 403, 404, 405, 406, 409, 410, 415, 422, 429, 500, 501, 502, 503]
    return random.choice(codes)


def generate_random_error_code() -> str:
    """Generate a random error code string."""
    codes = [
        "validation_error", "not_found", "unauthorized", "forbidden",
        "bad_request", "internal_error", "conflict", "gone",
        "method_not_allowed", "unsupported_media_type", "parse_error"
    ]
    return random.choice(codes)


def generate_random_error_mapping() -> ErrorMapping:
    """Generate a random ErrorMapping instance."""
    has_template = random.random() < 0.5
    return ErrorMapping(
        status_code=generate_random_status_code(),
        error_code=generate_random_error_code(),
        message_template=generate_random_string(10, 50) if has_template else None
    )


# =============================================================================
# Mock Classes for Testing
# =============================================================================

@dataclass
class MockResource:
    """Mock resource with an ID for testing."""
    id: str
    name: str


class MockResourceDict(dict):
    """Mock resource as a dict with ID."""
    pass


class MockResourceNoId:
    """Mock resource without an ID."""
    name: str = "test"


class MockRequest:
    """Mock HTTP request for testing."""
    
    def __init__(
        self,
        method: str = "GET",
        path: str = "/",
        headers: Optional[Dict[str, str]] = None,
        body: bytes = b''
    ):
        self.method = method
        self.path = path
        self.headers = headers or {}
        self.body = body
        self.endpoint_descriptor = None
        self.endpoint = None
        self.payload = None


class MockEndpoint:
    """Mock endpoint for testing."""
    
    def __init__(
        self,
        resource_name: str = "items",
        error_map: Optional[Dict[Type[Exception], ErrorMapping]] = None,
        status_code: Optional[int] = None
    ):
        self.resource_name = resource_name
        self.error_map = error_map or {}
        self.status_code = status_code
    
    def get_resource_url(self, resource: Any) -> Optional[str]:
        """Get URL for a resource."""
        resource_id = None
        
        if hasattr(resource, 'id'):
            resource_id = resource.id
        elif isinstance(resource, dict) and 'id' in resource:
            resource_id = resource['id']
        
        if resource_id is not None:
            return f"/{self.resource_name}/{resource_id}"
        
        return None


# =============================================================================
# Custom Exception Classes for Testing
# =============================================================================

class CustomNotFoundError(Exception):
    """Custom exception for testing not found scenarios."""
    
    def __init__(self, resource_type: str, resource_id: str):
        self.resource_type = resource_type
        self.resource_id = resource_id
        super().__init__(f"{resource_type} with id {resource_id} not found")


class CustomAuthError(Exception):
    """Custom exception for testing authentication scenarios."""
    
    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(f"Authentication failed: {reason}")


class CustomServerError(Exception):
    """Custom exception for testing server error scenarios."""
    pass


class ParentException(Exception):
    """Parent exception for inheritance testing."""
    pass


class ChildException(ParentException):
    """Child exception for inheritance testing."""
    pass


# =============================================================================
# Unit Tests: RESTMiddleware Initialization
# =============================================================================

def test_rest_middleware_creation():
    """RESTMiddleware should be created with required components."""
    registry = create_default_registry()
    validator = Validator()
    error_handler = ErrorHandler()
    
    middleware = RESTMiddleware(
        serializer_registry=registry,
        validator=validator,
        error_handler=error_handler
    )
    
    if middleware.serializer_registry is not registry:
        raise AssertionError("serializer_registry should be set")
    
    if middleware.validator is not validator:
        raise AssertionError("validator should be set")
    
    if middleware.error_handler is not error_handler:
        raise AssertionError("error_handler should be set")
    
    if middleware.negotiator is None:
        raise AssertionError("negotiator should be created")


def test_rest_middleware_name():
    """RESTMiddleware should have name 'rest'."""
    middleware = create_rest_middleware()
    
    if middleware.name != "rest":
        raise AssertionError(f"Expected name 'rest', got '{middleware.name}'")


def test_create_rest_middleware_default():
    """create_rest_middleware() should create middleware with defaults."""
    middleware = create_rest_middleware()
    
    if middleware.serializer_registry is None:
        raise AssertionError("serializer_registry should be created")
    
    if middleware.validator is None:
        raise AssertionError("validator should be created")
    
    if middleware.error_handler is None:
        raise AssertionError("error_handler should be created")


def test_create_rest_middleware_debug():
    """create_rest_middleware() should accept debug parameter."""
    middleware = create_rest_middleware(debug=True)
    
    if middleware.error_handler.debug is not True:
        raise AssertionError("error_handler should have debug=True")


def test_create_rest_middleware_custom_registry():
    """create_rest_middleware() should accept custom registry."""
    custom_registry = SerializerRegistry()
    custom_registry.register_serializer(JSONSerializer())
    
    middleware = create_rest_middleware(serializer_registry=custom_registry)
    
    if middleware.serializer_registry is not custom_registry:
        raise AssertionError("Should use custom registry")


# =============================================================================
# Unit Tests: Location Header Generation
# =============================================================================

def test_build_location_header_post_201():
    """build_location_header() should return ID for POST/201."""
    resource = MockResource(id="123", name="Test")
    
    location = build_location_header(
        method="POST",
        status_code=201,
        resource=resource
    )
    
    if location != "123":
        raise AssertionError(f"Expected '123', got '{location}'")


def test_build_location_header_with_custom_func():
    """build_location_header() should use custom get_resource_url function."""
    resource = MockResource(id="456", name="Test")
    
    def custom_url_func(res):
        return f"/custom/{res.id}"
    
    location = build_location_header(
        method="POST",
        status_code=201,
        resource=resource,
        get_resource_url_func=custom_url_func
    )
    
    if location != "/custom/456":
        raise AssertionError(f"Expected '/custom/456', got '{location}'")


def test_build_location_header_not_post():
    """build_location_header() should return None for non-POST methods."""
    resource = MockResource(id="123", name="Test")
    
    for method in ["GET", "PUT", "PATCH", "DELETE"]:
        location = build_location_header(
            method=method,
            status_code=201,
            resource=resource
        )
        
        if location is not None:
            raise AssertionError(f"Expected None for {method}, got '{location}'")


def test_build_location_header_not_201():
    """build_location_header() should return None for non-201 status."""
    resource = MockResource(id="123", name="Test")
    
    for status in [200, 202, 204, 400, 404, 500]:
        location = build_location_header(
            method="POST",
            status_code=status,
            resource=resource
        )
        
        if location is not None:
            raise AssertionError(f"Expected None for status {status}, got '{location}'")


def test_build_location_header_no_id():
    """build_location_header() should return None when resource has no ID."""
    resource = MockResourceNoId()
    
    location = build_location_header(
        method="POST",
        status_code=201,
        resource=resource
    )
    
    if location is not None:
        raise AssertionError(f"Expected None for resource without ID, got '{location}'")


def test_build_location_header_dict_resource():
    """build_location_header() should work with dict resources."""
    resource = {"id": "789", "name": "Test"}
    
    location = build_location_header(
        method="POST",
        status_code=201,
        resource=resource
    )
    
    if location != "789":
        raise AssertionError(f"Expected '789', got '{location}'")


def test_build_location_header_none_resource():
    """build_location_header() should return None for None resource."""
    location = build_location_header(
        method="POST",
        status_code=201,
        resource=None
    )
    
    if location is not None:
        raise AssertionError(f"Expected None, got '{location}'")


# =============================================================================
# Unit Tests: Error Map Inheritance
# =============================================================================

def test_merge_error_maps_both_none():
    """merge_error_maps() should return empty dict when both are None."""
    result = merge_error_maps(None, None)
    
    if result != {}:
        raise AssertionError(f"Expected empty dict, got {result}")


def test_merge_error_maps_parent_only():
    """merge_error_maps() should return parent map when child is None."""
    parent_map = {
        ValueError: ErrorMapping(status_code=400, error_code="bad_request")
    }
    
    result = merge_error_maps(parent_map, None)
    
    if result != parent_map:
        raise AssertionError(f"Expected parent map, got {result}")


def test_merge_error_maps_child_only():
    """merge_error_maps() should return child map when parent is None."""
    child_map = {
        KeyError: ErrorMapping(status_code=404, error_code="not_found")
    }
    
    result = merge_error_maps(None, child_map)
    
    if result != child_map:
        raise AssertionError(f"Expected child map, got {result}")


def test_merge_error_maps_child_extends_parent():
    """merge_error_maps() should include both parent and child mappings."""
    parent_map = {
        ValueError: ErrorMapping(status_code=400, error_code="bad_request")
    }
    child_map = {
        KeyError: ErrorMapping(status_code=404, error_code="not_found")
    }
    
    result = merge_error_maps(parent_map, child_map)
    
    if ValueError not in result:
        raise AssertionError("Result should include parent mapping")
    
    if KeyError not in result:
        raise AssertionError("Result should include child mapping")


def test_merge_error_maps_child_overrides_parent():
    """merge_error_maps() should have child override parent for same exception."""
    parent_map = {
        ValueError: ErrorMapping(status_code=400, error_code="bad_request")
    }
    child_map = {
        ValueError: ErrorMapping(status_code=422, error_code="unprocessable")
    }
    
    result = merge_error_maps(parent_map, child_map)
    
    if result[ValueError].status_code != 422:
        raise AssertionError(f"Child should override parent, got status {result[ValueError].status_code}")
    
    if result[ValueError].error_code != "unprocessable":
        raise AssertionError(f"Child should override parent, got error '{result[ValueError].error_code}'")


# =============================================================================
# Property-Based Tests
# =============================================================================

# Feature: rest-api-support, Property 11: Location Header for Created Resources
# *For any* POST request that creates a resource with an identifier, the response
# SHALL include a Location header containing a valid URL constructed from the
# resource endpoint path and the resource identifier.
# **Validates: Requirements 10.1, 10.2, 10.4**

def test_property_11_location_header_for_created_resources():
    """
        Property 11: Location Header for Created Resources
        
        For any POST request that creates a resource with an identifier,
        the response SHALL include a Location header containing a valid URL
        constructed from the resource endpoint path and the resource identifier.
        
        **Validates: Requirements 10.1, 10.2, 10.4**
    """
    # Run 100 iterations with random data
    for iteration in range(100):
        # Generate random resource ID and name
        resource_id = generate_random_id()
        resource_name = generate_random_resource_name()
        
        # Test case 1: Resource with 'id' attribute
        @dataclass
        class ResourceWithId:
            id: str
            name: str
        
        resource = ResourceWithId(id=resource_id, name=generate_random_string(5, 20))
        
        # Create endpoint with get_resource_url
        endpoint = MockEndpoint(resource_name=resource_name)
        
        # Build location header using endpoint's method
        location = endpoint.get_resource_url(resource)
        
        # Property: Location should be a valid URL with resource ID
        if location is None:
            errmsg = f"Iteration {iteration}: Location should not be None for resource with ID"
            raise AssertionError(errmsg)
        
        # Property: Location should contain the resource ID
        if resource_id not in location:
            errmsg = f"Iteration {iteration}: Location '{location}' should contain resource ID '{resource_id}'"
            raise AssertionError(errmsg)
        
        # Property: Location should contain the resource name
        if resource_name not in location:
            errmsg = f"Iteration {iteration}: Location '{location}' should contain resource name '{resource_name}'"
            raise AssertionError(errmsg)
        
        # Property: Location should be a valid path format
        if not location.startswith('/'):
            errmsg = f"Iteration {iteration}: Location '{location}' should start with '/'"
            raise AssertionError(errmsg)
        
        # Test case 2: Resource as dict with 'id' key
        dict_resource = {"id": resource_id, "name": generate_random_string(5, 20)}
        
        location = endpoint.get_resource_url(dict_resource)
        
        # Property: Location should work for dict resources
        if location is None:
            errmsg = f"Iteration {iteration}: Location should not be None for dict resource with ID"
            raise AssertionError(errmsg)
        
        if resource_id not in location:
            errmsg = f"Iteration {iteration}: Location '{location}' should contain dict resource ID '{resource_id}'"
            raise AssertionError(errmsg)
        
        # Test case 3: build_location_header function
        location = build_location_header(
            method="POST",
            status_code=201,
            resource=resource,
            get_resource_url_func=endpoint.get_resource_url
        )
        
        # Property: build_location_header should return valid URL for POST/201
        if location is None:
            errmsg = f"Iteration {iteration}: build_location_header should return URL for POST/201"
            raise AssertionError(errmsg)
        
        if resource_id not in location:
            errmsg = f"Iteration {iteration}: build_location_header result '{location}' should contain ID '{resource_id}'"
            raise AssertionError(errmsg)
        
        # Test case 4: Non-POST method should return None
        for method in ["GET", "PUT", "PATCH", "DELETE"]:
            location = build_location_header(
                method=method,
                status_code=201,
                resource=resource,
                get_resource_url_func=endpoint.get_resource_url
            )
            
            # Property: Non-POST methods should not generate Location header
            if location is not None:
                errmsg = f"Iteration {iteration}: {method} should not generate Location header, got '{location}'"
                raise AssertionError(errmsg)
        
        # Test case 5: Non-201 status should return None
        for status in [200, 202, 204, 400, 404, 500]:
            location = build_location_header(
                method="POST",
                status_code=status,
                resource=resource,
                get_resource_url_func=endpoint.get_resource_url
            )
            
            # Property: Non-201 status should not generate Location header
            if location is not None:
                errmsg = f"Iteration {iteration}: Status {status} should not generate Location header, got '{location}'"
                raise AssertionError(errmsg)
        
        # Test case 6: Resource without ID should return None
        class ResourceNoId:
            def __init__(self, name: str):
                self.name = name
        
        no_id_resource = ResourceNoId(name=generate_random_string(5, 20))
        
        location = build_location_header(
            method="POST",
            status_code=201,
            resource=no_id_resource
        )
        
        # Property: Resource without ID should not generate Location header
        if location is not None:
            errmsg = f"Iteration {iteration}: Resource without ID should not generate Location header, got '{location}'"
            raise AssertionError(errmsg)
        
        # Test case 7: None resource should return None
        location = build_location_header(
            method="POST",
            status_code=201,
            resource=None
        )
        
        # Property: None resource should not generate Location header
        if location is not None:
            errmsg = f"Iteration {iteration}: None resource should not generate Location header, got '{location}'"
            raise AssertionError(errmsg)
    
    return


# Feature: rest-api-support, Property 12: Error Map Inheritance
# *For any* endpoint with a parent endpoint, the effective error_map SHALL be
# the parent's error_map merged with the child's error_map, where child mappings
# override parent mappings for the same exception type.
# **Validates: Requirements 8.6**

def test_property_12_error_map_inheritance():
    """
        Property 12: Error Map Inheritance
        
        For any endpoint with a parent endpoint, the effective error_map
        SHALL be the parent's error_map merged with the child's error_map,
        where child mappings override parent mappings for the same exception type.
        
        **Validates: Requirements 8.6**
    """
    # Define exception types for testing
    exception_types = [
        ValueError, KeyError, TypeError, RuntimeError, PermissionError,
        CustomNotFoundError, CustomAuthError, CustomServerError,
        ParentException, ChildException
    ]
    
    # Run 100 iterations with random data
    for iteration in range(100):
        # Generate random parent error map
        num_parent_mappings = random.randint(0, len(exception_types))
        parent_exceptions = random.sample(exception_types, num_parent_mappings)
        parent_map: Dict[Type[Exception], ErrorMapping] = {}
        
        for exc_type in parent_exceptions:
            parent_map[exc_type] = generate_random_error_mapping()
        
        # Generate random child error map (may overlap with parent)
        num_child_mappings = random.randint(0, len(exception_types))
        child_exceptions = random.sample(exception_types, num_child_mappings)
        child_map: Dict[Type[Exception], ErrorMapping] = {}
        
        for exc_type in child_exceptions:
            child_map[exc_type] = generate_random_error_mapping()
        
        # Merge the maps
        result = merge_error_maps(
            parent_map if parent_map else None,
            child_map if child_map else None
        )
        
        # Property 1: Result must contain all parent mappings (unless overridden by child)
        for exc_type, mapping in parent_map.items():
            if exc_type not in result:
                errmsg = f"Iteration {iteration}: Parent mapping for {exc_type.__name__} should be in result"
                raise AssertionError(errmsg)
            
            # If not in child, should match parent exactly
            if exc_type not in child_map:
                if result[exc_type] != mapping:
                    errmsg = f"Iteration {iteration}: Parent mapping for {exc_type.__name__} should be preserved when not overridden"
                    raise AssertionError(errmsg)
        
        # Property 2: Result must contain all child mappings
        for exc_type, mapping in child_map.items():
            if exc_type not in result:
                errmsg = f"Iteration {iteration}: Child mapping for {exc_type.__name__} should be in result"
                raise AssertionError(errmsg)
            
            # Child should always override parent
            if result[exc_type] != mapping:
                errmsg = f"Iteration {iteration}: Child mapping for {exc_type.__name__} should override parent"
                raise AssertionError(errmsg)
        
        # Property 3: Result should not contain any extra mappings
        expected_keys = set(parent_map.keys()) | set(child_map.keys())
        if set(result.keys()) != expected_keys:
            errmsg = f"Iteration {iteration}: Result should only contain parent and child mappings"
            raise AssertionError(errmsg)
        
        # Property 4: For overlapping exceptions, child status_code should be used
        overlapping = set(parent_map.keys()) & set(child_map.keys())
        for exc_type in overlapping:
            if result[exc_type].status_code != child_map[exc_type].status_code:
                errmsg = f"Iteration {iteration}: Child status_code should override parent for {exc_type.__name__}"
                raise AssertionError(errmsg)
            
            if result[exc_type].error_code != child_map[exc_type].error_code:
                errmsg = f"Iteration {iteration}: Child error_code should override parent for {exc_type.__name__}"
                raise AssertionError(errmsg)
        
        # Property 5: Merging with None should work correctly
        # Test parent only
        result_parent_only = merge_error_maps(parent_map if parent_map else None, None)
        if parent_map:
            for exc_type in parent_map:
                if exc_type not in result_parent_only:
                    errmsg = f"Iteration {iteration}: Parent-only merge should include all parent mappings"
                    raise AssertionError(errmsg)
        
        # Test child only
        result_child_only = merge_error_maps(None, child_map if child_map else None)
        if child_map:
            for exc_type in child_map:
                if exc_type not in result_child_only:
                    errmsg = f"Iteration {iteration}: Child-only merge should include all child mappings"
                    raise AssertionError(errmsg)
        
        # Property 6: Merging None with None should return empty dict
        result_both_none = merge_error_maps(None, None)
        if result_both_none != {}:
            errmsg = f"Iteration {iteration}: Merging None with None should return empty dict"
            raise AssertionError(errmsg)
        
        # Property 7: ErrorHandler should use merged map correctly
        handler = ErrorHandler()
        
        # Test that endpoint map takes priority
        if child_map:
            # Pick a random exception from child map
            test_exc_type = random.choice(list(child_map.keys()))
            test_mapping = child_map[test_exc_type]
            
            # Create an instance of the exception
            if test_exc_type == CustomNotFoundError:
                test_exc = CustomNotFoundError("Test", "123")
            elif test_exc_type == CustomAuthError:
                test_exc = CustomAuthError("test reason")
            else:
                test_exc = test_exc_type("test message")
            
            # Handle with merged map
            rest_error, status_code = handler.handle(test_exc, endpoint_error_map=result)
            
            # Property: Status code should match child mapping
            if status_code != test_mapping.status_code:
                errmsg = f"Iteration {iteration}: Handler should use merged map status code {test_mapping.status_code}, got {status_code}"
                raise AssertionError(errmsg)
            
            # Property: Error code should match child mapping
            if rest_error.error != test_mapping.error_code:
                errmsg = f"Iteration {iteration}: Handler should use merged map error code '{test_mapping.error_code}', got '{rest_error.error}'"
                raise AssertionError(errmsg)
    
    return


# =============================================================================
# Additional Unit Tests for Middleware
# =============================================================================

def test_middleware_get_header():
    """Middleware should extract headers from request."""
    middleware = create_rest_middleware()
    
    request = MockRequest(headers={"Content-Type": "application/json", "Accept": "application/json"})
    
    content_type = middleware._get_header(request, "Content-Type")
    if content_type != "application/json":
        raise AssertionError(f"Expected 'application/json', got '{content_type}'")
    
    accept = middleware._get_header(request, "Accept")
    if accept != "application/json":
        raise AssertionError(f"Expected 'application/json', got '{accept}'")


def test_middleware_get_method():
    """Middleware should extract method from request."""
    middleware = create_rest_middleware()
    
    for method in ["GET", "POST", "PUT", "PATCH", "DELETE"]:
        request = MockRequest(method=method)
        result = middleware._get_method(request)
        
        if result != method:
            raise AssertionError(f"Expected '{method}', got '{result}'")


def test_middleware_get_body():
    """Middleware should extract body from request."""
    middleware = create_rest_middleware()
    
    body = b'{"name": "test"}'
    request = MockRequest(body=body)
    
    result = middleware._get_body(request)
    if result != body:
        raise AssertionError(f"Expected body bytes, got '{result}'")


def test_middleware_has_request_body():
    """Middleware should detect if request has body."""
    middleware = create_rest_middleware()
    
    # POST with body
    request = MockRequest(method="POST", body=b'{"name": "test"}')
    if not middleware._has_request_body(request):
        raise AssertionError("POST with body should have request body")
    
    # GET without body
    request = MockRequest(method="GET", body=b'')
    if middleware._has_request_body(request):
        raise AssertionError("GET should not have request body")
    
    # POST without body
    request = MockRequest(method="POST", body=b'')
    if middleware._has_request_body(request):
        raise AssertionError("POST without body should not have request body")


def test_middleware_handle_error():
    """Middleware should handle errors and return error response."""
    middleware = create_rest_middleware()
    
    request = MockRequest()
    exc = ValueError("Test error")
    
    response = middleware._handle_error(request, exc)
    
    if response["status_code"] != 400:
        raise AssertionError(f"Expected status 400, got {response['status_code']}")
    
    if response["content_type"] != "application/json":
        raise AssertionError(f"Expected content type 'application/json', got '{response['content_type']}'")


def test_middleware_create_response():
    """Middleware should create response dict."""
    middleware = create_rest_middleware()
    
    response = middleware._create_response(
        body=b'{"test": true}',
        status_code=200,
        content_type="application/json",
        headers={"X-Custom": "value"}
    )
    
    if response["body"] != b'{"test": true}':
        raise AssertionError("Body should match")
    
    if response["status_code"] != 200:
        raise AssertionError("Status code should match")
    
    if response["content_type"] != "application/json":
        raise AssertionError("Content type should match")
    
    if response["headers"]["X-Custom"] != "value":
        raise AssertionError("Headers should match")

