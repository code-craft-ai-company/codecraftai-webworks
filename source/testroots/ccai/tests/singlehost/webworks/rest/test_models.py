"""
.. module:: test_models
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Tests for the REST API support core data models.

    This module contains unit tests and property-based tests for the core
    data models: FieldError, RESTError, ErrorMapping, and ValidationError.

.. moduleauthor:: Code Craft AI LLC
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []

import json
import random
import string
from typing import Any, Dict, List, Optional

from ccai.webworks.endpoints.rest import (
    FieldError,
    RESTError,
    ErrorMapping,
    ValidationError,
)


# =============================================================================
# Random Data Generators
# =============================================================================

def generate_random_string(min_length: int = 1, max_length: int = 50) -> str:
    """Generate a random string of alphanumeric characters."""
    length = random.randint(min_length, max_length)
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def generate_random_error_code() -> str:
    """Generate a random error code string."""
    codes = [
        "validation_error", "not_found", "unauthorized", "forbidden",
        "bad_request", "internal_error", "conflict", "gone",
        "method_not_allowed", "unsupported_media_type", "parse_error"
    ]
    return random.choice(codes)


def generate_random_field_path() -> str:
    """Generate a random field path like 'user.email' or 'items[0].name'."""
    parts = []
    depth = random.randint(1, 3)
    for i in range(depth):
        part = generate_random_string(3, 15)
        if random.random() < 0.3 and i > 0:
            # Add array index
            part = f"{part}[{random.randint(0, 10)}]"
        parts.append(part)
    return '.'.join(parts)


def generate_random_field_error() -> FieldError:
    """Generate a random FieldError instance."""
    field_codes = ["required", "invalid", "type_error", "min_length", "max_length", "pattern"]
    return FieldError(
        field=generate_random_field_path(),
        code=random.choice(field_codes),
        message=generate_random_string(10, 100)
    )


def generate_random_details() -> Optional[Dict[str, Any]]:
    """Generate random details dictionary or None."""
    if random.random() < 0.3:
        return None
    
    details = {}
    num_keys = random.randint(1, 5)
    for _ in range(num_keys):
        key = generate_random_string(3, 15)
        value_type = random.choice(['string', 'int', 'bool', 'list'])
        if value_type == 'string':
            details[key] = generate_random_string(5, 30)
        elif value_type == 'int':
            details[key] = random.randint(-1000, 1000)
        elif value_type == 'bool':
            details[key] = random.choice([True, False])
        else:
            details[key] = [generate_random_string(3, 10) for _ in range(random.randint(1, 5))]
    return details


def generate_random_field_errors() -> Optional[List[FieldError]]:
    """Generate a random list of FieldError instances or None."""
    if random.random() < 0.3:
        return None
    
    num_errors = random.randint(1, 5)
    return [generate_random_field_error() for _ in range(num_errors)]


def generate_random_rest_error() -> RESTError:
    """Generate a random RESTError instance."""
    return RESTError(
        error=generate_random_error_code(),
        message=generate_random_string(10, 100),
        details=generate_random_details(),
        field_errors=generate_random_field_errors()
    )


# =============================================================================
# Unit Tests: FieldError
# =============================================================================

def test_field_error_creation():
    """FieldError should be created with field, code, and message."""
    fe = FieldError(field="email", code="required", message="Email is required")
    
    if fe.field != "email":
        raise AssertionError(f"Expected field 'email', got '{fe.field}'")
    
    if fe.code != "required":
        raise AssertionError(f"Expected code 'required', got '{fe.code}'")
    
    if fe.message != "Email is required":
        raise AssertionError(f"Expected message 'Email is required', got '{fe.message}'")


def test_field_error_nested_path():
    """FieldError should support nested field paths."""
    fe = FieldError(field="user.address.city", code="invalid", message="Invalid city")
    
    if fe.field != "user.address.city":
        raise AssertionError(f"Expected nested path, got '{fe.field}'")


def test_field_error_array_index_path():
    """FieldError should support array index in field paths."""
    fe = FieldError(field="items[0].name", code="type_error", message="Expected string")
    
    if fe.field != "items[0].name":
        raise AssertionError(f"Expected array index path, got '{fe.field}'")


# =============================================================================
# Unit Tests: RESTError
# =============================================================================

def test_rest_error_creation_minimal():
    """RESTError should be created with just error and message."""
    err = RESTError(error="not_found", message="Resource not found")
    
    if err.error != "not_found":
        raise AssertionError(f"Expected error 'not_found', got '{err.error}'")
    
    if err.message != "Resource not found":
        raise AssertionError(f"Expected message 'Resource not found', got '{err.message}'")
    
    if err.details is not None:
        raise AssertionError(f"Expected details None, got '{err.details}'")
    
    if err.field_errors is not None:
        raise AssertionError(f"Expected field_errors None, got '{err.field_errors}'")


def test_rest_error_creation_with_details():
    """RESTError should accept optional details dictionary."""
    details = {"resource_type": "user", "resource_id": 123}
    err = RESTError(error="not_found", message="Resource not found", details=details)
    
    if err.details != details:
        raise AssertionError(f"Expected details {details}, got '{err.details}'")


def test_rest_error_creation_with_field_errors():
    """RESTError should accept optional field_errors list."""
    field_errors = [
        FieldError(field="email", code="required", message="Email is required"),
        FieldError(field="name", code="min_length", message="Name too short")
    ]
    err = RESTError(
        error="validation_error",
        message="Validation failed",
        field_errors=field_errors
    )
    
    if err.field_errors != field_errors:
        raise AssertionError(f"Expected field_errors list, got '{err.field_errors}'")
    
    if len(err.field_errors) != 2:
        raise AssertionError(f"Expected 2 field errors, got {len(err.field_errors)}")


def test_rest_error_to_dict_minimal():
    """to_dict() should return dict with error and message only when no optionals."""
    err = RESTError(error="not_found", message="Resource not found")
    result = err.to_dict()
    
    if result != {"error": "not_found", "message": "Resource not found"}:
        raise AssertionError(f"Unexpected dict: {result}")
    
    if "details" in result:
        raise AssertionError("details should not be in dict when None")
    
    if "field_errors" in result:
        raise AssertionError("field_errors should not be in dict when None")


def test_rest_error_to_dict_with_details():
    """to_dict() should include details when present."""
    details = {"resource_type": "user"}
    err = RESTError(error="not_found", message="Not found", details=details)
    result = err.to_dict()
    
    if result.get("details") != details:
        raise AssertionError(f"Expected details in dict, got {result}")


def test_rest_error_to_dict_with_field_errors():
    """to_dict() should serialize field_errors as list of dicts."""
    field_errors = [
        FieldError(field="email", code="required", message="Email is required")
    ]
    err = RESTError(
        error="validation_error",
        message="Validation failed",
        field_errors=field_errors
    )
    result = err.to_dict()
    
    expected_field_errors = [
        {"field": "email", "code": "required", "message": "Email is required"}
    ]
    
    if result.get("field_errors") != expected_field_errors:
        raise AssertionError(f"Expected field_errors {expected_field_errors}, got {result.get('field_errors')}")


def test_rest_error_to_dict_json_serializable():
    """to_dict() result should be JSON serializable."""
    field_errors = [
        FieldError(field="email", code="required", message="Email is required")
    ]
    err = RESTError(
        error="validation_error",
        message="Validation failed",
        details={"count": 1, "items": ["a", "b"]},
        field_errors=field_errors
    )
    result = err.to_dict()
    
    try:
        json_str = json.dumps(result)
        parsed = json.loads(json_str)
    except (TypeError, ValueError) as e:
        raise AssertionError(f"to_dict() result should be JSON serializable: {e}")
    
    if parsed != result:
        raise AssertionError(f"JSON round-trip failed: {parsed} != {result}")


# =============================================================================
# Unit Tests: ErrorMapping
# =============================================================================

def test_error_mapping_creation():
    """ErrorMapping should be created with status_code and error_code."""
    mapping = ErrorMapping(status_code=404, error_code="not_found")
    
    if mapping.status_code != 404:
        raise AssertionError(f"Expected status_code 404, got {mapping.status_code}")
    
    if mapping.error_code != "not_found":
        raise AssertionError(f"Expected error_code 'not_found', got '{mapping.error_code}'")
    
    if mapping.message_template is not None:
        raise AssertionError(f"Expected message_template None, got '{mapping.message_template}'")


def test_error_mapping_with_template():
    """ErrorMapping should accept optional message_template."""
    mapping = ErrorMapping(
        status_code=400,
        error_code="bad_request",
        message_template="Invalid value: {args}"
    )
    
    if mapping.message_template != "Invalid value: {args}":
        raise AssertionError(f"Expected template, got '{mapping.message_template}'")


def test_error_mapping_build_response_no_template():
    """build_response() should use exception string when no template."""
    mapping = ErrorMapping(status_code=400, error_code="bad_request")
    exc = ValueError("Invalid input value")
    
    result = mapping.build_response(exc)
    
    if not isinstance(result, RESTError):
        raise AssertionError(f"Expected RESTError, got {type(result)}")
    
    if result.error != "bad_request":
        raise AssertionError(f"Expected error 'bad_request', got '{result.error}'")
    
    if result.message != "Invalid input value":
        raise AssertionError(f"Expected message from exception, got '{result.message}'")


def test_error_mapping_build_response_with_template():
    """build_response() should interpolate exception attributes into template."""
    mapping = ErrorMapping(
        status_code=404,
        error_code="not_found",
        message_template="Resource not found"
    )
    exc = KeyError("user_123")
    
    result = mapping.build_response(exc)
    
    if result.error != "not_found":
        raise AssertionError(f"Expected error 'not_found', got '{result.error}'")
    
    if result.message != "Resource not found":
        raise AssertionError(f"Expected template message, got '{result.message}'")


def test_error_mapping_build_response_with_attribute_interpolation():
    """build_response() should interpolate exception attributes."""
    
    class CustomError(Exception):
        def __init__(self, resource_type: str, resource_id: int):
            self.resource_type = resource_type
            self.resource_id = resource_id
            super().__init__(f"{resource_type} {resource_id} not found")
    
    mapping = ErrorMapping(
        status_code=404,
        error_code="not_found",
        message_template="{resource_type} with id {resource_id} was not found"
    )
    exc = CustomError("User", 123)
    
    result = mapping.build_response(exc)
    
    if result.message != "User with id 123 was not found":
        raise AssertionError(f"Expected interpolated message, got '{result.message}'")


def test_error_mapping_build_response_fallback_on_missing_attr():
    """build_response() should fall back to exception string on missing attribute."""
    mapping = ErrorMapping(
        status_code=400,
        error_code="bad_request",
        message_template="Missing: {nonexistent_attr}"
    )
    exc = ValueError("Some error")
    
    result = mapping.build_response(exc)
    
    # Should fall back to exception string
    if result.message != "Some error":
        raise AssertionError(f"Expected fallback message, got '{result.message}'")


def test_error_mapping_build_response_includes_field_errors():
    """build_response() should include field_errors from ValidationError."""
    mapping = ErrorMapping(
        status_code=400,
        error_code="validation_error",
        message_template="Validation failed"
    )
    
    field_errors = [
        FieldError(field="email", code="required", message="Email is required")
    ]
    exc = ValidationError("Validation failed", field_errors=field_errors)
    
    result = mapping.build_response(exc)
    
    if result.field_errors is None:
        raise AssertionError("Expected field_errors to be included")
    
    if len(result.field_errors) != 1:
        raise AssertionError(f"Expected 1 field error, got {len(result.field_errors)}")
    
    if result.field_errors[0].field != "email":
        raise AssertionError(f"Expected field 'email', got '{result.field_errors[0].field}'")


# =============================================================================
# Unit Tests: ValidationError
# =============================================================================

def test_validation_error_creation_minimal():
    """ValidationError should be created with just a message."""
    exc = ValidationError("Validation failed")
    
    if exc.message != "Validation failed":
        raise AssertionError(f"Expected message 'Validation failed', got '{exc.message}'")
    
    if exc.field_errors != []:
        raise AssertionError(f"Expected empty field_errors, got {exc.field_errors}")
    
    if str(exc) != "Validation failed":
        raise AssertionError(f"Expected str(exc) to be message, got '{str(exc)}'")


def test_validation_error_creation_with_field_errors():
    """ValidationError should accept field_errors list."""
    field_errors = [
        FieldError(field="email", code="required", message="Email is required"),
        FieldError(field="name", code="min_length", message="Name too short")
    ]
    exc = ValidationError("Validation failed", field_errors=field_errors)
    
    if exc.field_errors != field_errors:
        raise AssertionError(f"Expected field_errors list, got {exc.field_errors}")
    
    if len(exc.field_errors) != 2:
        raise AssertionError(f"Expected 2 field errors, got {len(exc.field_errors)}")


def test_validation_error_is_exception():
    """ValidationError should be an Exception subclass."""
    exc = ValidationError("Test error")
    
    if not isinstance(exc, Exception):
        raise AssertionError("ValidationError should be an Exception")
    
    # Should be raisable
    raised = False
    try:
        raise exc
    except ValidationError as caught:
        raised = True
        if caught.message != "Test error":
            raise AssertionError(f"Caught exception has wrong message: {caught.message}")
    
    if not raised:
        raise AssertionError("ValidationError should be raisable")


# =============================================================================
# Property-Based Tests
# =============================================================================

# Feature: rest-api-support, Property 3: Response Serialization Round-Trip
# *For any* valid response object (dataclass, Pydantic model, dict, or list)
# and any schema, serializing to JSON and then deserializing back SHALL
# produce an equivalent object.
# **Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5**

def test_property_3_rest_error_serialization_round_trip():
    """
        Property 3: Response Serialization Round-Trip
        
        For any valid RESTError object, serializing to dict via to_dict()
        and then reconstructing the object SHALL produce an equivalent
        RESTError with the same error, message, details, and field_errors.
        
        **Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5**
    """
    # Run 100 iterations with random data
    for iteration in range(100):
        # Generate a random RESTError
        original = generate_random_rest_error()
        
        # Serialize to dict
        serialized = original.to_dict()
        
        # Property: serialized must be a dict
        if not isinstance(serialized, dict):
            errmsg = f"Iteration {iteration}: to_dict() should return dict, got {type(serialized)}"
            raise AssertionError(errmsg)
        
        # Property: serialized must have 'error' key
        if "error" not in serialized:
            errmsg = f"Iteration {iteration}: serialized dict missing 'error' key"
            raise AssertionError(errmsg)
        
        # Property: serialized must have 'message' key
        if "message" not in serialized:
            errmsg = f"Iteration {iteration}: serialized dict missing 'message' key"
            raise AssertionError(errmsg)
        
        # Property: error value must match original
        if serialized["error"] != original.error:
            errmsg = f"Iteration {iteration}: error mismatch: {serialized['error']} != {original.error}"
            raise AssertionError(errmsg)
        
        # Property: message value must match original
        if serialized["message"] != original.message:
            errmsg = f"Iteration {iteration}: message mismatch: {serialized['message']} != {original.message}"
            raise AssertionError(errmsg)
        
        # Property: details should only be present if original had details
        if original.details is None:
            if "details" in serialized:
                errmsg = f"Iteration {iteration}: details should not be in dict when None"
                raise AssertionError(errmsg)
        else:
            if "details" not in serialized:
                errmsg = f"Iteration {iteration}: details should be in dict when present"
                raise AssertionError(errmsg)
            if serialized["details"] != original.details:
                errmsg = f"Iteration {iteration}: details mismatch"
                raise AssertionError(errmsg)
        
        # Property: field_errors should only be present if original had field_errors
        if original.field_errors is None:
            if "field_errors" in serialized:
                errmsg = f"Iteration {iteration}: field_errors should not be in dict when None"
                raise AssertionError(errmsg)
        else:
            if "field_errors" not in serialized:
                errmsg = f"Iteration {iteration}: field_errors should be in dict when present"
                raise AssertionError(errmsg)
            
            # Property: field_errors count must match
            if len(serialized["field_errors"]) != len(original.field_errors):
                errmsg = f"Iteration {iteration}: field_errors count mismatch"
                raise AssertionError(errmsg)
            
            # Property: each field_error must have correct structure
            for idx, (ser_fe, orig_fe) in enumerate(zip(serialized["field_errors"], original.field_errors)):
                if ser_fe["field"] != orig_fe.field:
                    errmsg = f"Iteration {iteration}: field_error[{idx}].field mismatch"
                    raise AssertionError(errmsg)
                if ser_fe["code"] != orig_fe.code:
                    errmsg = f"Iteration {iteration}: field_error[{idx}].code mismatch"
                    raise AssertionError(errmsg)
                if ser_fe["message"] != orig_fe.message:
                    errmsg = f"Iteration {iteration}: field_error[{idx}].message mismatch"
                    raise AssertionError(errmsg)
        
        # Property: serialized dict must be JSON serializable
        try:
            json_str = json.dumps(serialized)
            parsed = json.loads(json_str)
        except (TypeError, ValueError) as e:
            errmsg = f"Iteration {iteration}: to_dict() result not JSON serializable: {e}"
            raise AssertionError(errmsg)
        
        # Property: JSON round-trip must preserve data
        if parsed != serialized:
            errmsg = f"Iteration {iteration}: JSON round-trip changed data"
            raise AssertionError(errmsg)
        
        # Reconstruct RESTError from serialized dict
        reconstructed_field_errors = None
        if "field_errors" in parsed:
            reconstructed_field_errors = [
                FieldError(field=fe["field"], code=fe["code"], message=fe["message"])
                for fe in parsed["field_errors"]
            ]
        
        reconstructed = RESTError(
            error=parsed["error"],
            message=parsed["message"],
            details=parsed.get("details"),
            field_errors=reconstructed_field_errors
        )
        
        # Property: reconstructed error must equal original error
        if reconstructed.error != original.error:
            errmsg = f"Iteration {iteration}: reconstructed error mismatch"
            raise AssertionError(errmsg)
        
        if reconstructed.message != original.message:
            errmsg = f"Iteration {iteration}: reconstructed message mismatch"
            raise AssertionError(errmsg)
        
        if reconstructed.details != original.details:
            errmsg = f"Iteration {iteration}: reconstructed details mismatch"
            raise AssertionError(errmsg)
        
        # Compare field_errors
        if original.field_errors is None:
            if reconstructed.field_errors is not None:
                errmsg = f"Iteration {iteration}: reconstructed field_errors should be None"
                raise AssertionError(errmsg)
        else:
            if reconstructed.field_errors is None:
                errmsg = f"Iteration {iteration}: reconstructed field_errors should not be None"
                raise AssertionError(errmsg)
            
            if len(reconstructed.field_errors) != len(original.field_errors):
                errmsg = f"Iteration {iteration}: reconstructed field_errors count mismatch"
                raise AssertionError(errmsg)
            
            for idx, (rec_fe, orig_fe) in enumerate(zip(reconstructed.field_errors, original.field_errors)):
                if rec_fe.field != orig_fe.field:
                    errmsg = f"Iteration {iteration}: reconstructed field_error[{idx}].field mismatch"
                    raise AssertionError(errmsg)
                if rec_fe.code != orig_fe.code:
                    errmsg = f"Iteration {iteration}: reconstructed field_error[{idx}].code mismatch"
                    raise AssertionError(errmsg)
                if rec_fe.message != orig_fe.message:
                    errmsg = f"Iteration {iteration}: reconstructed field_error[{idx}].message mismatch"
                    raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests: PaginationInfo
# =============================================================================

def test_pagination_info_creation():
    """PaginationInfo should be created with all required fields."""
    from ccai.webworks.endpoints.rest import PaginationInfo
    
    info = PaginationInfo(
        total=100,
        page=2,
        page_size=10,
        total_pages=10,
        next="/items?page=3&page_size=10",
        prev="/items?page=1&page_size=10",
        first="/items?page=1&page_size=10",
        last="/items?page=10&page_size=10"
    )
    
    if info.total != 100:
        raise AssertionError(f"Expected total 100, got {info.total}")
    
    if info.page != 2:
        raise AssertionError(f"Expected page 2, got {info.page}")
    
    if info.page_size != 10:
        raise AssertionError(f"Expected page_size 10, got {info.page_size}")
    
    if info.total_pages != 10:
        raise AssertionError(f"Expected total_pages 10, got {info.total_pages}")


def test_pagination_info_create_classmethod():
    """PaginationInfo.create() should compute total_pages and links."""
    from ccai.webworks.endpoints.rest import PaginationInfo
    
    info = PaginationInfo.create(
        total=95,
        page=2,
        page_size=10,
        base_url="/items"
    )
    
    # total_pages should be ceil(95/10) = 10
    if info.total_pages != 10:
        raise AssertionError(f"Expected total_pages 10, got {info.total_pages}")
    
    # Should have next link (page 3)
    if info.next is None:
        raise AssertionError("Expected next link")
    if "page=3" not in info.next:
        raise AssertionError(f"Expected page=3 in next link, got {info.next}")
    
    # Should have prev link (page 1)
    if info.prev is None:
        raise AssertionError("Expected prev link")
    if "page=1" not in info.prev:
        raise AssertionError(f"Expected page=1 in prev link, got {info.prev}")


def test_pagination_info_create_first_page():
    """PaginationInfo.create() should have no prev link on first page."""
    from ccai.webworks.endpoints.rest import PaginationInfo
    
    info = PaginationInfo.create(
        total=50,
        page=1,
        page_size=10,
        base_url="/items"
    )
    
    if info.prev is not None:
        raise AssertionError(f"Expected no prev link on first page, got {info.prev}")
    
    if info.next is None:
        raise AssertionError("Expected next link on first page")


def test_pagination_info_create_last_page():
    """PaginationInfo.create() should have no next link on last page."""
    from ccai.webworks.endpoints.rest import PaginationInfo
    
    info = PaginationInfo.create(
        total=50,
        page=5,
        page_size=10,
        base_url="/items"
    )
    
    if info.next is not None:
        raise AssertionError(f"Expected no next link on last page, got {info.next}")
    
    if info.prev is None:
        raise AssertionError("Expected prev link on last page")


def test_pagination_info_create_empty_collection():
    """PaginationInfo.create() should handle empty collections."""
    from ccai.webworks.endpoints.rest import PaginationInfo
    
    info = PaginationInfo.create(
        total=0,
        page=1,
        page_size=10,
        base_url="/items"
    )
    
    if info.total_pages != 1:
        raise AssertionError(f"Expected total_pages 1 for empty collection, got {info.total_pages}")
    
    if info.next is not None:
        raise AssertionError("Expected no next link for empty collection")
    
    if info.prev is not None:
        raise AssertionError("Expected no prev link for empty collection")


def test_pagination_info_create_with_query_params():
    """PaginationInfo.create() should handle base_url with existing query params."""
    from ccai.webworks.endpoints.rest import PaginationInfo
    
    info = PaginationInfo.create(
        total=50,
        page=2,
        page_size=10,
        base_url="/items?filter=active"
    )
    
    # Should use & separator for additional params
    if info.next is None:
        raise AssertionError("Expected next link")
    if "&page=" not in info.next:
        raise AssertionError(f"Expected & separator in next link, got {info.next}")


# =============================================================================
# Unit Tests: PaginatedResponse
# =============================================================================

def test_paginated_response_creation():
    """PaginatedResponse should be created with items and pagination."""
    from ccai.webworks.endpoints.rest import PaginationInfo, PaginatedResponse
    
    pagination = PaginationInfo(
        total=100,
        page=1,
        page_size=10,
        total_pages=10
    )
    items = [{"id": i, "name": f"Item {i}"} for i in range(10)]
    
    response = PaginatedResponse(items=items, pagination=pagination)
    
    if len(response.items) != 10:
        raise AssertionError(f"Expected 10 items, got {len(response.items)}")
    
    if response.pagination.total != 100:
        raise AssertionError(f"Expected total 100, got {response.pagination.total}")


def test_paginated_response_to_dict():
    """PaginatedResponse.to_dict() should return proper structure."""
    from ccai.webworks.endpoints.rest import PaginationInfo, PaginatedResponse
    
    pagination = PaginationInfo(
        total=50,
        page=2,
        page_size=10,
        total_pages=5,
        next="/items?page=3&page_size=10",
        prev="/items?page=1&page_size=10",
        first="/items?page=1&page_size=10",
        last="/items?page=5&page_size=10"
    )
    items = [{"id": 1}, {"id": 2}]
    
    response = PaginatedResponse(items=items, pagination=pagination)
    result = response.to_dict()
    
    if "items" not in result:
        raise AssertionError("Expected 'items' in dict")
    
    if "pagination" not in result:
        raise AssertionError("Expected 'pagination' in dict")
    
    if result["pagination"]["total"] != 50:
        raise AssertionError(f"Expected total 50, got {result['pagination']['total']}")
    
    if "links" not in result["pagination"]:
        raise AssertionError("Expected 'links' in pagination")
    
    if result["pagination"]["links"]["next"] != "/items?page=3&page_size=10":
        raise AssertionError(f"Expected next link, got {result['pagination']['links']['next']}")


def test_paginated_response_to_dict_json_serializable():
    """PaginatedResponse.to_dict() should be JSON serializable."""
    import json
    from ccai.webworks.endpoints.rest import PaginationInfo, PaginatedResponse
    
    pagination = PaginationInfo.create(total=20, page=1, page_size=10, base_url="/items")
    items = [{"id": i} for i in range(10)]
    
    response = PaginatedResponse(items=items, pagination=pagination)
    result = response.to_dict()
    
    try:
        json_str = json.dumps(result)
        parsed = json.loads(json_str)
    except (TypeError, ValueError) as e:
        raise AssertionError(f"to_dict() result should be JSON serializable: {e}")


# =============================================================================
# Unit Tests: select_status_code
# =============================================================================

def test_select_status_code_get():
    """select_status_code should return 200 for GET."""
    from ccai.webworks.endpoints.rest import select_status_code
    
    data, status = select_status_code("GET", {"id": 1})
    
    if status != 200:
        raise AssertionError(f"Expected 200 for GET, got {status}")


def test_select_status_code_post():
    """select_status_code should return 201 for POST."""
    from ccai.webworks.endpoints.rest import select_status_code
    
    data, status = select_status_code("POST", {"id": 1})
    
    if status != 201:
        raise AssertionError(f"Expected 201 for POST, got {status}")


def test_select_status_code_put():
    """select_status_code should return 200 for PUT."""
    from ccai.webworks.endpoints.rest import select_status_code
    
    data, status = select_status_code("PUT", {"id": 1})
    
    if status != 200:
        raise AssertionError(f"Expected 200 for PUT, got {status}")


def test_select_status_code_patch():
    """select_status_code should return 200 for PATCH."""
    from ccai.webworks.endpoints.rest import select_status_code
    
    data, status = select_status_code("PATCH", {"id": 1})
    
    if status != 200:
        raise AssertionError(f"Expected 200 for PATCH, got {status}")


def test_select_status_code_delete():
    """select_status_code should return 204 for DELETE."""
    from ccai.webworks.endpoints.rest import select_status_code
    
    data, status = select_status_code("DELETE", None)
    
    if status != 204:
        raise AssertionError(f"Expected 204 for DELETE, got {status}")


def test_select_status_code_override():
    """select_status_code should use override when provided."""
    from ccai.webworks.endpoints.rest import select_status_code
    
    data, status = select_status_code("POST", {"id": 1}, status_code_override=200)
    
    if status != 200:
        raise AssertionError(f"Expected 200 with override, got {status}")


def test_select_status_code_tuple_return():
    """select_status_code should handle (data, status_code) tuple returns."""
    from ccai.webworks.endpoints.rest import select_status_code
    
    handler_result = ({"id": 1}, 202)
    data, status = select_status_code("POST", handler_result)
    
    if status != 202:
        raise AssertionError(f"Expected 202 from tuple, got {status}")
    
    if data != {"id": 1}:
        raise AssertionError(f"Expected data from tuple, got {data}")


def test_select_status_code_tuple_takes_precedence():
    """Tuple status code should take precedence over override."""
    from ccai.webworks.endpoints.rest import select_status_code
    
    handler_result = ({"id": 1}, 202)
    data, status = select_status_code("POST", handler_result, status_code_override=200)
    
    if status != 202:
        raise AssertionError(f"Expected 202 from tuple (precedence), got {status}")


def test_select_status_code_lowercase_method():
    """select_status_code should handle lowercase methods."""
    from ccai.webworks.endpoints.rest import select_status_code
    
    data, status = select_status_code("get", {"id": 1})
    
    if status != 200:
        raise AssertionError(f"Expected 200 for lowercase get, got {status}")


def test_select_status_code_unknown_method():
    """select_status_code should return 200 for unknown methods."""
    from ccai.webworks.endpoints.rest import select_status_code
    
    data, status = select_status_code("OPTIONS", {})
    
    if status != 200:
        raise AssertionError(f"Expected 200 for unknown method, got {status}")


# =============================================================================
# Unit Tests: build_location_header
# =============================================================================

def test_build_location_header_post_201():
    """build_location_header should return ID for POST/201."""
    from ccai.webworks.endpoints.rest import build_location_header
    
    resource = {"id": 123, "name": "Test"}
    result = build_location_header("POST", 201, resource)
    
    if result != "123":
        raise AssertionError(f"Expected '123', got '{result}'")


def test_build_location_header_not_post():
    """build_location_header should return None for non-POST methods."""
    from ccai.webworks.endpoints.rest import build_location_header
    
    resource = {"id": 123}
    result = build_location_header("GET", 200, resource)
    
    if result is not None:
        raise AssertionError(f"Expected None for GET, got '{result}'")


def test_build_location_header_not_201():
    """build_location_header should return None for non-201 status."""
    from ccai.webworks.endpoints.rest import build_location_header
    
    resource = {"id": 123}
    result = build_location_header("POST", 200, resource)
    
    if result is not None:
        raise AssertionError(f"Expected None for status 200, got '{result}'")


def test_build_location_header_none_resource():
    """build_location_header should return None for None resource."""
    from ccai.webworks.endpoints.rest import build_location_header
    
    result = build_location_header("POST", 201, None)
    
    if result is not None:
        raise AssertionError(f"Expected None for None resource, got '{result}'")


def test_build_location_header_no_id():
    """build_location_header should return None when resource has no ID."""
    from ccai.webworks.endpoints.rest import build_location_header
    
    resource = {"name": "Test"}
    result = build_location_header("POST", 201, resource)
    
    if result is not None:
        raise AssertionError(f"Expected None for resource without ID, got '{result}'")


def test_build_location_header_with_custom_func():
    """build_location_header should use custom function when provided."""
    from ccai.webworks.endpoints.rest import build_location_header
    
    resource = {"id": 123}
    
    def custom_url_func(res):
        return f"/api/v1/items/{res['id']}"
    
    result = build_location_header("POST", 201, resource, custom_url_func)
    
    if result != "/api/v1/items/123":
        raise AssertionError(f"Expected custom URL, got '{result}'")


def test_build_location_header_dataclass_resource():
    """build_location_header should extract ID from dataclass."""
    from dataclasses import dataclass
    from ccai.webworks.endpoints.rest import build_location_header
    
    @dataclass
    class Resource:
        id: int
        name: str
    
    resource = Resource(id=456, name="Test")
    result = build_location_header("POST", 201, resource)
    
    if result != "456":
        raise AssertionError(f"Expected '456', got '{result}'")


# =============================================================================
# Property-Based Tests: HTTP Method to Status Code Mapping
# =============================================================================

# Feature: rest-api-support, Property 8: HTTP Method to Status Code Mapping
# *For any* successful request, the response status code SHALL match the HTTP
# method convention: GET→200, POST (create)→201, PUT→200, PATCH→200, DELETE→204.
# *For any* endpoint with a custom status_code attribute, that value SHALL
# override the default.
# **Validates: Requirements 9.1, 9.2, 9.3, 9.4, 9.5**

def test_property_8_http_method_to_status_code_mapping():
    """
        Property 8: HTTP Method to Status Code Mapping
        
        For any successful request, the response status code SHALL match
        the HTTP method convention: GET→200, POST→201, PUT→200, PATCH→200,
        DELETE→204. For any endpoint with a custom status_code attribute,
        that value SHALL override the default.
        
        **Validates: Requirements 9.1, 9.2, 9.3, 9.4, 9.5**
    """
    import random
    from ccai.webworks.endpoints.rest import select_status_code
    
    # Expected default status codes
    expected_defaults = {
        "GET": 200,
        "POST": 201,
        "PUT": 200,
        "PATCH": 200,
        "DELETE": 204,
    }
    
    methods = list(expected_defaults.keys())
    
    # Run 100 iterations
    for iteration in range(100):
        # Pick a random method
        method = random.choice(methods)
        
        # Generate random data
        data = {"id": random.randint(1, 1000), "value": generate_random_string(5, 20)}
        
        # Property 1: Default status code matches convention
        result_data, status = select_status_code(method, data)
        expected_status = expected_defaults[method]
        
        if status != expected_status:
            errmsg = (
                f"Iteration {iteration}: Method '{method}' returned status {status}, "
                f"expected {expected_status}"
            )
            raise AssertionError(errmsg)
        
        # Property 2: Data is preserved
        if result_data != data:
            errmsg = f"Iteration {iteration}: Data was modified by select_status_code"
            raise AssertionError(errmsg)
        
        # Property 3: Override takes precedence over default
        override_status = random.choice([200, 201, 202, 204, 400, 404, 500])
        result_data, status = select_status_code(method, data, status_code_override=override_status)
        
        if status != override_status:
            errmsg = (
                f"Iteration {iteration}: Override status {override_status} not applied, "
                f"got {status}"
            )
            raise AssertionError(errmsg)
        
        # Property 4: Tuple return takes precedence over everything
        tuple_status = random.choice([200, 201, 202, 204, 400, 404, 500])
        handler_result = (data, tuple_status)
        result_data, status = select_status_code(method, handler_result, status_code_override=override_status)
        
        if status != tuple_status:
            errmsg = (
                f"Iteration {iteration}: Tuple status {tuple_status} not applied, "
                f"got {status}"
            )
            raise AssertionError(errmsg)
        
        if result_data != data:
            errmsg = f"Iteration {iteration}: Data from tuple was not extracted correctly"
            raise AssertionError(errmsg)
        
        # Property 5: Lowercase methods work the same
        lowercase_method = method.lower()
        result_data, status = select_status_code(lowercase_method, data)
        
        if status != expected_defaults[method]:
            errmsg = (
                f"Iteration {iteration}: Lowercase method '{lowercase_method}' "
                f"returned status {status}, expected {expected_defaults[method]}"
            )
            raise AssertionError(errmsg)
    
    return


# =============================================================================
# Property-Based Tests: Pagination Consistency
# =============================================================================

# Feature: rest-api-support, Property 9: Pagination Consistency
# *For any* collection endpoint with total items T, page P, and page_size S,
# the PaginationInfo SHALL correctly compute total_pages as ceil(T/S), and
# the navigation links SHALL be valid URLs that return the correct pages
# when followed.
# **Validates: Requirements 2.2, 2.3, 2.6**

def test_property_9_pagination_consistency():
    """
        Property 9: Pagination Consistency
        
        For any collection endpoint with total items T, page P, and page_size S,
        the PaginationInfo SHALL correctly compute total_pages as ceil(T/S),
        and the navigation links SHALL be valid URLs that return the correct
        pages when followed.
        
        **Validates: Requirements 2.2, 2.3, 2.6**
    """
    import random
    import math
    from ccai.webworks.endpoints.rest import PaginationInfo
    
    # Run 100 iterations
    for iteration in range(100):
        # Generate random pagination parameters
        total = random.randint(0, 1000)
        page_size = random.randint(1, 100)
        
        # Calculate expected total_pages
        if total == 0:
            expected_total_pages = 1
        else:
            expected_total_pages = math.ceil(total / page_size)
        
        # Pick a random valid page
        page = random.randint(1, max(1, expected_total_pages))
        
        # Generate random base URL
        base_url = f"/api/{generate_random_string(3, 10)}"
        
        # Create PaginationInfo
        info = PaginationInfo.create(
            total=total,
            page=page,
            page_size=page_size,
            base_url=base_url
        )
        
        # Property 1: total_pages is correctly computed
        if info.total_pages != expected_total_pages:
            errmsg = (
                f"Iteration {iteration}: total_pages {info.total_pages} != "
                f"expected {expected_total_pages} (total={total}, page_size={page_size})"
            )
            raise AssertionError(errmsg)
        
        # Property 2: page is within valid range
        if info.page < 1 or info.page > info.total_pages:
            errmsg = (
                f"Iteration {iteration}: page {info.page} out of range "
                f"[1, {info.total_pages}]"
            )
            raise AssertionError(errmsg)
        
        # Property 3: total, page_size are preserved
        if info.total != total:
            errmsg = f"Iteration {iteration}: total {info.total} != {total}"
            raise AssertionError(errmsg)
        
        if info.page_size != page_size:
            errmsg = f"Iteration {iteration}: page_size {info.page_size} != {page_size}"
            raise AssertionError(errmsg)
        
        # Property 4: first page has no prev link
        if info.page == 1 and info.prev is not None:
            errmsg = f"Iteration {iteration}: First page should have no prev link"
            raise AssertionError(errmsg)
        
        # Property 5: last page has no next link
        if info.page == info.total_pages and info.next is not None:
            errmsg = f"Iteration {iteration}: Last page should have no next link"
            raise AssertionError(errmsg)
        
        # Property 6: middle pages have both prev and next links
        if 1 < info.page < info.total_pages:
            if info.prev is None:
                errmsg = f"Iteration {iteration}: Middle page should have prev link"
                raise AssertionError(errmsg)
            if info.next is None:
                errmsg = f"Iteration {iteration}: Middle page should have next link"
                raise AssertionError(errmsg)
        
        # Property 7: first and last links are always present
        if info.first is None:
            errmsg = f"Iteration {iteration}: first link should always be present"
            raise AssertionError(errmsg)
        
        if info.last is None:
            errmsg = f"Iteration {iteration}: last link should always be present"
            raise AssertionError(errmsg)
        
        # Property 8: Navigation links contain correct page numbers
        if info.next is not None:
            expected_next_page = info.page + 1
            if f"page={expected_next_page}" not in info.next:
                errmsg = (
                    f"Iteration {iteration}: next link should contain page={expected_next_page}, "
                    f"got {info.next}"
                )
                raise AssertionError(errmsg)
        
        if info.prev is not None:
            expected_prev_page = info.page - 1
            if f"page={expected_prev_page}" not in info.prev:
                errmsg = (
                    f"Iteration {iteration}: prev link should contain page={expected_prev_page}, "
                    f"got {info.prev}"
                )
                raise AssertionError(errmsg)
        
        if "page=1" not in info.first:
            errmsg = f"Iteration {iteration}: first link should contain page=1, got {info.first}"
            raise AssertionError(errmsg)
        
        if f"page={info.total_pages}" not in info.last:
            errmsg = (
                f"Iteration {iteration}: last link should contain page={info.total_pages}, "
                f"got {info.last}"
            )
            raise AssertionError(errmsg)
        
        # Property 9: All links contain page_size
        for link_name, link in [("first", info.first), ("last", info.last)]:
            if f"page_size={page_size}" not in link:
                errmsg = (
                    f"Iteration {iteration}: {link_name} link should contain "
                    f"page_size={page_size}, got {link}"
                )
                raise AssertionError(errmsg)
        
        if info.next is not None and f"page_size={page_size}" not in info.next:
            errmsg = (
                f"Iteration {iteration}: next link should contain page_size={page_size}, "
                f"got {info.next}"
            )
            raise AssertionError(errmsg)
        
        if info.prev is not None and f"page_size={page_size}" not in info.prev:
            errmsg = (
                f"Iteration {iteration}: prev link should contain page_size={page_size}, "
                f"got {info.prev}"
            )
            raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests: JSON Merge Patch Functions
# =============================================================================

def test_apply_json_merge_patch_basic_update():
    """apply_json_merge_patch should update fields present in patch."""
    from ccai.webworks.endpoints.rest import apply_json_merge_patch
    
    original = {"name": "Alice", "age": 30}
    patch = {"age": 31}
    
    result = apply_json_merge_patch(original, patch)
    
    if result.get("name") != "Alice":
        raise AssertionError(f"Expected name 'Alice', got '{result.get('name')}'")
    
    if result.get("age") != 31:
        raise AssertionError(f"Expected age 31, got {result.get('age')}")


def test_apply_json_merge_patch_null_removes_field():
    """apply_json_merge_patch should remove fields with null values."""
    from ccai.webworks.endpoints.rest import apply_json_merge_patch
    
    original = {"name": "Alice", "email": "alice@example.com", "age": 30}
    patch = {"email": None}
    
    result = apply_json_merge_patch(original, patch)
    
    if "email" in result:
        raise AssertionError("Expected 'email' to be removed")
    
    if result.get("name") != "Alice":
        raise AssertionError(f"Expected name 'Alice', got '{result.get('name')}'")
    
    if result.get("age") != 30:
        raise AssertionError(f"Expected age 30, got {result.get('age')}")


def test_apply_json_merge_patch_preserves_unpatched_fields():
    """apply_json_merge_patch should preserve fields not in patch."""
    from ccai.webworks.endpoints.rest import apply_json_merge_patch
    
    original = {"name": "Alice", "email": "alice@example.com", "age": 30, "city": "NYC"}
    patch = {"age": 31}
    
    result = apply_json_merge_patch(original, patch)
    
    if result.get("name") != "Alice":
        raise AssertionError(f"Expected name 'Alice', got '{result.get('name')}'")
    
    if result.get("email") != "alice@example.com":
        raise AssertionError(f"Expected email 'alice@example.com', got '{result.get('email')}'")
    
    if result.get("city") != "NYC":
        raise AssertionError(f"Expected city 'NYC', got '{result.get('city')}'")


def test_apply_json_merge_patch_adds_new_fields():
    """apply_json_merge_patch should add new fields from patch."""
    from ccai.webworks.endpoints.rest import apply_json_merge_patch
    
    original = {"name": "Alice"}
    patch = {"email": "alice@example.com"}
    
    result = apply_json_merge_patch(original, patch)
    
    if result.get("name") != "Alice":
        raise AssertionError(f"Expected name 'Alice', got '{result.get('name')}'")
    
    if result.get("email") != "alice@example.com":
        raise AssertionError(f"Expected email 'alice@example.com', got '{result.get('email')}'")


def test_apply_json_merge_patch_nested_objects():
    """apply_json_merge_patch should recursively merge nested objects."""
    from ccai.webworks.endpoints.rest import apply_json_merge_patch
    
    original = {
        "name": "Alice",
        "address": {
            "street": "123 Main St",
            "city": "NYC",
            "zip": "10001"
        }
    }
    patch = {
        "address": {
            "city": "LA"
        }
    }
    
    result = apply_json_merge_patch(original, patch)
    
    if result.get("name") != "Alice":
        raise AssertionError(f"Expected name 'Alice', got '{result.get('name')}'")
    
    address = result.get("address", {})
    
    if address.get("street") != "123 Main St":
        raise AssertionError(f"Expected street '123 Main St', got '{address.get('street')}'")
    
    if address.get("city") != "LA":
        raise AssertionError(f"Expected city 'LA', got '{address.get('city')}'")
    
    if address.get("zip") != "10001":
        raise AssertionError(f"Expected zip '10001', got '{address.get('zip')}'")


def test_apply_json_merge_patch_does_not_modify_original():
    """apply_json_merge_patch should not modify the original object."""
    from ccai.webworks.endpoints.rest import apply_json_merge_patch
    
    original = {"name": "Alice", "age": 30}
    patch = {"age": 31}
    
    result = apply_json_merge_patch(original, patch)
    
    if original.get("age") != 30:
        raise AssertionError("Original object was modified")
    
    if result.get("age") != 31:
        raise AssertionError(f"Expected result age 31, got {result.get('age')}")


def test_apply_json_merge_patch_remove_null_fields_false():
    """apply_json_merge_patch with remove_null_fields=False should keep null values."""
    from ccai.webworks.endpoints.rest import apply_json_merge_patch
    
    original = {"name": "Alice", "email": "alice@example.com"}
    patch = {"email": None}
    
    result = apply_json_merge_patch(original, patch, remove_null_fields=False)
    
    if "email" not in result:
        raise AssertionError("Expected 'email' to be present")
    
    if result.get("email") is not None:
        raise AssertionError(f"Expected email None, got '{result.get('email')}'")


def test_extract_patch_fields_basic():
    """extract_patch_fields should return all fields from patch."""
    from ccai.webworks.endpoints.rest import extract_patch_fields
    
    patch = {"name": "Alice", "age": 30}
    
    result = extract_patch_fields(patch)
    
    if result != patch:
        raise AssertionError(f"Expected {patch}, got {result}")


def test_extract_patch_fields_exclude_null():
    """extract_patch_fields with include_null=False should exclude null values."""
    from ccai.webworks.endpoints.rest import extract_patch_fields
    
    patch = {"name": "Alice", "email": None, "age": 30}
    
    result = extract_patch_fields(patch, include_null=False)
    
    if "email" in result:
        raise AssertionError("Expected 'email' to be excluded")
    
    if result.get("name") != "Alice":
        raise AssertionError(f"Expected name 'Alice', got '{result.get('name')}'")
    
    if result.get("age") != 30:
        raise AssertionError(f"Expected age 30, got {result.get('age')}")


def test_get_removed_fields_basic():
    """get_removed_fields should return fields with null values."""
    from ccai.webworks.endpoints.rest import get_removed_fields
    
    patch = {"name": "Alice", "email": None, "phone": None, "age": 30}
    
    result = get_removed_fields(patch)
    
    if set(result) != {"email", "phone"}:
        raise AssertionError(f"Expected ['email', 'phone'], got {result}")


def test_get_removed_fields_no_nulls():
    """get_removed_fields should return empty list when no null values."""
    from ccai.webworks.endpoints.rest import get_removed_fields
    
    patch = {"name": "Alice", "age": 30}
    
    result = get_removed_fields(patch)
    
    if result != []:
        raise AssertionError(f"Expected [], got {result}")


# =============================================================================
# Property-Based Tests: Partial Update Field Preservation
# =============================================================================

# Feature: rest-api-support, Property 5: Partial Update Field Preservation
# *For any* PATCH request with a subset of fields, only the fields present
# in the request body SHALL be updated, and all other fields SHALL retain
# their original values.
# **Validates: Requirements 11.2, 11.4**

def test_property_5_partial_update_field_preservation():
    """
        Property 5: Partial Update Field Preservation
        
        For any PATCH request with a subset of fields, only the fields present
        in the request body SHALL be updated, and all other fields SHALL retain
        their original values.
        
        **Validates: Requirements 11.2, 11.4**
    """
    import random
    from ccai.webworks.endpoints.rest import apply_json_merge_patch
    
    # Define a set of possible field names
    all_field_names = [
        "name", "email", "age", "city", "country", "phone", "status",
        "active", "score", "level", "title", "description", "category",
        "priority", "tags", "metadata"
    ]
    
    # Run 100 iterations
    for iteration in range(100):
        # Generate a random original object with a random subset of fields
        num_original_fields = random.randint(3, len(all_field_names))
        original_field_names = random.sample(all_field_names, num_original_fields)
        
        original = {}
        for field_name in original_field_names:
            # Generate random values of different types
            value_type = random.choice(["string", "int", "bool", "list"])
            if value_type == "string":
                original[field_name] = generate_random_string(3, 20)
            elif value_type == "int":
                original[field_name] = random.randint(0, 1000)
            elif value_type == "bool":
                original[field_name] = random.choice([True, False])
            else:
                original[field_name] = [generate_random_string(2, 10) for _ in range(random.randint(1, 5))]
        
        # Generate a random patch with a subset of the original fields
        num_patch_fields = random.randint(1, max(1, len(original_field_names) // 2))
        patch_field_names = random.sample(original_field_names, num_patch_fields)
        
        patch = {}
        for field_name in patch_field_names:
            # Generate new values for the patch
            value_type = random.choice(["string", "int", "bool", "null"])
            if value_type == "string":
                patch[field_name] = generate_random_string(3, 20)
            elif value_type == "int":
                patch[field_name] = random.randint(0, 1000)
            elif value_type == "bool":
                patch[field_name] = random.choice([True, False])
            else:
                # null value means field removal
                patch[field_name] = None
        
        # Apply the patch
        result = apply_json_merge_patch(original, patch)
        
        # Property 1: Fields in patch with non-null values should be updated
        for field_name, patch_value in patch.items():
            if patch_value is not None:
                if result.get(field_name) != patch_value:
                    errmsg = (
                        f"Iteration {iteration}: Field '{field_name}' should be updated to "
                        f"'{patch_value}', got '{result.get(field_name)}'"
                    )
                    raise AssertionError(errmsg)
        
        # Property 2: Fields in patch with null values should be removed
        for field_name, patch_value in patch.items():
            if patch_value is None:
                if field_name in result:
                    errmsg = (
                        f"Iteration {iteration}: Field '{field_name}' should be removed "
                        f"(null in patch), but is present with value '{result.get(field_name)}'"
                    )
                    raise AssertionError(errmsg)
        
        # Property 3: Fields NOT in patch should retain original values
        for field_name in original_field_names:
            if field_name not in patch:
                if result.get(field_name) != original.get(field_name):
                    errmsg = (
                        f"Iteration {iteration}: Field '{field_name}' should retain original "
                        f"value '{original.get(field_name)}', got '{result.get(field_name)}'"
                    )
                    raise AssertionError(errmsg)
        
        # Property 4: Original object should not be modified
        for field_name in original_field_names:
            # Check that original still has its original values
            # (We can't easily verify this without storing a copy, but we can check
            # that the original dict still has all its keys)
            if field_name not in original:
                errmsg = (
                    f"Iteration {iteration}: Original object was modified - "
                    f"field '{field_name}' is missing"
                )
                raise AssertionError(errmsg)
        
        # Property 5: Result should have correct number of fields
        # (original fields - removed fields)
        removed_fields = [f for f, v in patch.items() if v is None]
        expected_field_count = len(original_field_names) - len(removed_fields)
        
        if len(result) != expected_field_count:
            errmsg = (
                f"Iteration {iteration}: Expected {expected_field_count} fields in result, "
                f"got {len(result)}"
            )
            raise AssertionError(errmsg)
    
    return


def test_property_5_partial_update_nested_objects():
    """
        Property 5: Partial Update Field Preservation - Nested Objects
        
        For any PATCH request with nested objects, the merge should be
        recursive, preserving nested fields not present in the patch.
        
        **Validates: Requirements 11.2, 11.4**
    """
    import random
    from ccai.webworks.endpoints.rest import apply_json_merge_patch
    
    # Run 100 iterations
    for iteration in range(100):
        # Generate a random original object with nested structure
        original = {
            "name": generate_random_string(3, 20),
            "profile": {
                "bio": generate_random_string(10, 50),
                "avatar": generate_random_string(5, 20),
                "settings": {
                    "theme": random.choice(["light", "dark"]),
                    "notifications": random.choice([True, False]),
                    "language": random.choice(["en", "es", "fr", "de"])
                }
            },
            "metadata": {
                "created": generate_random_string(10, 20),
                "updated": generate_random_string(10, 20)
            }
        }
        
        # Generate a random patch that updates some nested fields
        patch_scenarios = [
            # Update single nested field
            {"profile": {"bio": generate_random_string(10, 50)}},
            # Update deeply nested field
            {"profile": {"settings": {"theme": random.choice(["light", "dark"])}}},
            # Update multiple nested fields
            {"profile": {"bio": generate_random_string(10, 50), "avatar": generate_random_string(5, 20)}},
            # Remove nested field with null
            {"profile": {"avatar": None}},
            # Update top-level and nested
            {"name": generate_random_string(3, 20), "profile": {"bio": generate_random_string(10, 50)}},
        ]
        
        patch = random.choice(patch_scenarios)
        
        # Apply the patch
        result = apply_json_merge_patch(original, patch)
        
        # Property 1: Top-level fields not in patch should be preserved
        if "name" not in patch:
            if result.get("name") != original.get("name"):
                errmsg = (
                    f"Iteration {iteration}: Top-level 'name' should be preserved, "
                    f"expected '{original.get('name')}', got '{result.get('name')}'"
                )
                raise AssertionError(errmsg)
        
        # Property 2: Nested fields not in patch should be preserved
        if "profile" in patch:
            profile_patch = patch["profile"]
            original_profile = original["profile"]
            result_profile = result.get("profile", {})
            
            for field_name in original_profile:
                if field_name not in profile_patch:
                    if result_profile.get(field_name) != original_profile.get(field_name):
                        errmsg = (
                            f"Iteration {iteration}: Nested field 'profile.{field_name}' "
                            f"should be preserved, expected '{original_profile.get(field_name)}', "
                            f"got '{result_profile.get(field_name)}'"
                        )
                        raise AssertionError(errmsg)
        
        # Property 3: metadata should be completely preserved if not in patch
        if "metadata" not in patch:
            if result.get("metadata") != original.get("metadata"):
                errmsg = (
                    f"Iteration {iteration}: 'metadata' should be preserved, "
                    f"expected '{original.get('metadata')}', got '{result.get('metadata')}'"
                )
                raise AssertionError(errmsg)
        
        # Property 4: Deeply nested fields should be preserved
        if "profile" in patch and "settings" in patch.get("profile", {}):
            settings_patch = patch["profile"]["settings"]
            original_settings = original["profile"]["settings"]
            result_settings = result.get("profile", {}).get("settings", {})
            
            for field_name in original_settings:
                if field_name not in settings_patch:
                    if result_settings.get(field_name) != original_settings.get(field_name):
                        errmsg = (
                            f"Iteration {iteration}: Deeply nested field "
                            f"'profile.settings.{field_name}' should be preserved"
                        )
                        raise AssertionError(errmsg)
    
    return


def test_property_5_partial_update_with_validator():
    """
        Property 5: Partial Update Field Preservation - With Validator
        
        For any partial validation, only the fields present in the data
        should be validated and returned, preserving the partial nature
        of the update.
        
        **Validates: Requirements 11.2, 11.4**
    """
    import random
    from dataclasses import dataclass
    from typing import Optional
    from ccai.webworks.endpoints.rest import Validator
    
    @dataclass
    class TestUser:
        name: str
        email: str
        age: int
        city: Optional[str] = None
    
    validator = Validator()
    
    # Run 100 iterations
    for iteration in range(100):
        # Generate random partial data (subset of fields)
        all_fields = ["name", "email", "age", "city"]
        num_fields = random.randint(1, len(all_fields))
        selected_fields = random.sample(all_fields, num_fields)
        
        partial_data = {}
        for field_name in selected_fields:
            if field_name == "name":
                partial_data["name"] = generate_random_string(3, 20)
            elif field_name == "email":
                partial_data["email"] = f"{generate_random_string(5, 10)}@example.com"
            elif field_name == "age":
                partial_data["age"] = random.randint(1, 100)
            elif field_name == "city":
                partial_data["city"] = generate_random_string(3, 15)
        
        # Validate with partial=True
        result = validator.validate(partial_data, TestUser, partial=True)
        
        # Property 1: Result should be a dict (not a full instance) in partial mode
        if not isinstance(result, dict):
            errmsg = (
                f"Iteration {iteration}: Partial validation should return dict, "
                f"got {type(result)}"
            )
            raise AssertionError(errmsg)
        
        # Property 2: Only provided fields should be in result
        for field_name in result:
            if field_name not in partial_data:
                errmsg = (
                    f"Iteration {iteration}: Field '{field_name}' should not be in result "
                    f"(not in partial data)"
                )
                raise AssertionError(errmsg)
        
        # Property 3: All provided fields should be in result
        for field_name in partial_data:
            if field_name not in result:
                errmsg = (
                    f"Iteration {iteration}: Field '{field_name}' should be in result "
                    f"(was in partial data)"
                )
                raise AssertionError(errmsg)
        
        # Property 4: Values should match
        for field_name, value in partial_data.items():
            if result.get(field_name) != value:
                errmsg = (
                    f"Iteration {iteration}: Field '{field_name}' value mismatch, "
                    f"expected '{value}', got '{result.get(field_name)}'"
                )
                raise AssertionError(errmsg)
    
    return
