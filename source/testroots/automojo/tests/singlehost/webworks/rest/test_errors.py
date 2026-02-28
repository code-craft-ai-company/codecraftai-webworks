"""
.. module:: test_errors
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Tests for the REST API error handling infrastructure.

    This module contains unit tests and property-based tests for the
    ErrorHandler class and error map inheritance functionality.

.. moduleauthor:: Automation Mojo LLC
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []

import random
import string
from typing import Dict, List, Optional, Type

from automojo.webworks.endpoints.rest import (
    ErrorHandler,
    ErrorMapping,
    FieldError,
    RESTError,
    ValidationError,
    merge_error_maps,
)


# =============================================================================
# Random Data Generators
# =============================================================================

def generate_random_string(min_length: int = 1, max_length: int = 50) -> str:
    """Generate a random string of alphanumeric characters."""
    length = random.randint(min_length, max_length)
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def generate_random_status_code() -> int:
    """Generate a random HTTP status code."""
    # Common HTTP error status codes
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


def generate_random_field_error() -> FieldError:
    """Generate a random FieldError instance."""
    field_codes = ["required", "invalid", "type_error", "min_length", "max_length", "pattern"]
    return FieldError(
        field=generate_random_string(3, 15),
        code=random.choice(field_codes),
        message=generate_random_string(10, 50)
    )


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


# =============================================================================
# Unit Tests: ErrorHandler Initialization
# =============================================================================

def test_error_handler_default_debug_false():
    """ErrorHandler should default to debug=False (production mode)."""
    handler = ErrorHandler()
    
    if handler.debug is not False:
        raise AssertionError(f"Expected debug=False, got {handler.debug}")


def test_error_handler_debug_true():
    """ErrorHandler should accept debug=True."""
    handler = ErrorHandler(debug=True)
    
    if handler.debug is not True:
        raise AssertionError(f"Expected debug=True, got {handler.debug}")


def test_error_handler_has_default_mappings():
    """ErrorHandler should have default mappings for common exceptions."""
    handler = ErrorHandler()
    
    # Check that default mappings exist
    if ValueError not in handler._mappings:
        raise AssertionError("ValueError should be in default mappings")
    
    if KeyError not in handler._mappings:
        raise AssertionError("KeyError should be in default mappings")
    
    if PermissionError not in handler._mappings:
        raise AssertionError("PermissionError should be in default mappings")
    
    if ValidationError not in handler._mappings:
        raise AssertionError("ValidationError should be in default mappings")


def test_error_handler_default_mapping_status_codes():
    """Default mappings should have correct status codes."""
    handler = ErrorHandler()
    
    # ValueError -> 400
    if handler._mappings[ValueError].status_code != 400:
        raise AssertionError(f"ValueError should map to 400, got {handler._mappings[ValueError].status_code}")
    
    # KeyError -> 404
    if handler._mappings[KeyError].status_code != 404:
        raise AssertionError(f"KeyError should map to 404, got {handler._mappings[KeyError].status_code}")
    
    # PermissionError -> 403
    if handler._mappings[PermissionError].status_code != 403:
        raise AssertionError(f"PermissionError should map to 403, got {handler._mappings[PermissionError].status_code}")
    
    # ValidationError -> 400
    if handler._mappings[ValidationError].status_code != 400:
        raise AssertionError(f"ValidationError should map to 400, got {handler._mappings[ValidationError].status_code}")


# =============================================================================
# Unit Tests: ErrorHandler.register_mapping()
# =============================================================================

def test_error_handler_register_mapping():
    """register_mapping() should add a new mapping."""
    handler = ErrorHandler()
    
    mapping = ErrorMapping(status_code=409, error_code="conflict")
    handler.register_mapping(CustomNotFoundError, mapping)
    
    if CustomNotFoundError not in handler._mappings:
        raise AssertionError("Custom exception should be registered")
    
    if handler._mappings[CustomNotFoundError] != mapping:
        raise AssertionError("Registered mapping should match")


def test_error_handler_register_mapping_override():
    """register_mapping() should override existing mappings."""
    handler = ErrorHandler()
    
    # Override ValueError mapping
    new_mapping = ErrorMapping(status_code=422, error_code="unprocessable")
    handler.register_mapping(ValueError, new_mapping)
    
    if handler._mappings[ValueError].status_code != 422:
        raise AssertionError(f"Override should change status code, got {handler._mappings[ValueError].status_code}")


# =============================================================================
# Unit Tests: ErrorHandler.handle() - Default Mappings
# =============================================================================

def test_error_handler_handle_value_error():
    """handle() should return 400 for ValueError."""
    handler = ErrorHandler()
    exc = ValueError("Invalid input")
    
    rest_error, status_code = handler.handle(exc)
    
    if status_code != 400:
        raise AssertionError(f"Expected status 400, got {status_code}")
    
    if rest_error.error != "bad_request":
        raise AssertionError(f"Expected error 'bad_request', got '{rest_error.error}'")


def test_error_handler_handle_key_error():
    """handle() should return 404 for KeyError."""
    handler = ErrorHandler()
    exc = KeyError("user_123")
    
    rest_error, status_code = handler.handle(exc)
    
    if status_code != 404:
        raise AssertionError(f"Expected status 404, got {status_code}")
    
    if rest_error.error != "not_found":
        raise AssertionError(f"Expected error 'not_found', got '{rest_error.error}'")


def test_error_handler_handle_permission_error():
    """handle() should return 403 for PermissionError."""
    handler = ErrorHandler()
    exc = PermissionError("Access denied")
    
    rest_error, status_code = handler.handle(exc)
    
    if status_code != 403:
        raise AssertionError(f"Expected status 403, got {status_code}")
    
    if rest_error.error != "forbidden":
        raise AssertionError(f"Expected error 'forbidden', got '{rest_error.error}'")


def test_error_handler_handle_validation_error():
    """handle() should return 400 for ValidationError with field_errors."""
    handler = ErrorHandler()
    field_errors = [
        FieldError(field="email", code="required", message="Email is required")
    ]
    exc = ValidationError("Validation failed", field_errors=field_errors)
    
    rest_error, status_code = handler.handle(exc)
    
    if status_code != 400:
        raise AssertionError(f"Expected status 400, got {status_code}")
    
    if rest_error.error != "validation_error":
        raise AssertionError(f"Expected error 'validation_error', got '{rest_error.error}'")
    
    if rest_error.field_errors is None:
        raise AssertionError("field_errors should be included")
    
    if len(rest_error.field_errors) != 1:
        raise AssertionError(f"Expected 1 field error, got {len(rest_error.field_errors)}")


# =============================================================================
# Unit Tests: ErrorHandler.handle() - Unhandled Exceptions
# =============================================================================

def test_error_handler_handle_unhandled_exception_debug():
    """handle() should return 500 with details for unhandled exception in debug mode."""
    handler = ErrorHandler(debug=True)
    exc = CustomServerError("Database connection failed")
    
    rest_error, status_code = handler.handle(exc)
    
    if status_code != 500:
        raise AssertionError(f"Expected status 500, got {status_code}")
    
    if rest_error.error != "internal_error":
        raise AssertionError(f"Expected error 'internal_error', got '{rest_error.error}'")
    
    # In debug mode, should include exception details
    if "Database connection failed" not in rest_error.message:
        raise AssertionError(f"Debug mode should include exception message, got '{rest_error.message}'")


def test_error_handler_handle_unhandled_exception_production():
    """handle() should return 500 without details for unhandled exception in production mode."""
    handler = ErrorHandler(debug=False)
    exc = CustomServerError("Database connection failed")
    
    rest_error, status_code = handler.handle(exc)
    
    if status_code != 500:
        raise AssertionError(f"Expected status 500, got {status_code}")
    
    if rest_error.error != "internal_error":
        raise AssertionError(f"Expected error 'internal_error', got '{rest_error.error}'")
    
    # In production mode, should NOT include exception details
    if "Database connection failed" in rest_error.message:
        raise AssertionError("Production mode should hide exception details")
    
    if rest_error.message != "An internal error occurred":
        raise AssertionError(f"Expected generic message, got '{rest_error.message}'")


# =============================================================================
# Unit Tests: ErrorHandler.handle() - Endpoint Error Map Priority
# =============================================================================

def test_error_handler_endpoint_map_takes_priority():
    """handle() should check endpoint error_map before global mappings."""
    handler = ErrorHandler()
    
    # Create endpoint-specific mapping that overrides ValueError
    endpoint_map = {
        ValueError: ErrorMapping(status_code=422, error_code="unprocessable_entity")
    }
    
    exc = ValueError("Invalid input")
    rest_error, status_code = handler.handle(exc, endpoint_error_map=endpoint_map)
    
    # Should use endpoint mapping, not global
    if status_code != 422:
        raise AssertionError(f"Expected status 422 from endpoint map, got {status_code}")
    
    if rest_error.error != "unprocessable_entity":
        raise AssertionError(f"Expected error from endpoint map, got '{rest_error.error}'")


def test_error_handler_falls_back_to_global():
    """handle() should fall back to global mappings when not in endpoint map."""
    handler = ErrorHandler()
    
    # Endpoint map doesn't include KeyError
    endpoint_map = {
        ValueError: ErrorMapping(status_code=422, error_code="unprocessable_entity")
    }
    
    exc = KeyError("user_123")
    rest_error, status_code = handler.handle(exc, endpoint_error_map=endpoint_map)
    
    # Should use global mapping for KeyError
    if status_code != 404:
        raise AssertionError(f"Expected status 404 from global map, got {status_code}")


def test_error_handler_endpoint_map_custom_exception():
    """handle() should use endpoint map for custom exceptions."""
    handler = ErrorHandler()
    
    endpoint_map = {
        CustomNotFoundError: ErrorMapping(
            status_code=404,
            error_code="resource_not_found",
            message_template="{resource_type} {resource_id} not found"
        )
    }
    
    exc = CustomNotFoundError("User", "123")
    rest_error, status_code = handler.handle(exc, endpoint_error_map=endpoint_map)
    
    if status_code != 404:
        raise AssertionError(f"Expected status 404, got {status_code}")
    
    if rest_error.error != "resource_not_found":
        raise AssertionError(f"Expected error 'resource_not_found', got '{rest_error.error}'")


# =============================================================================
# Unit Tests: ErrorHandler.handle() - Subclass Matching
# =============================================================================

def test_error_handler_matches_exception_subclass():
    """handle() should match exception subclasses to parent mappings."""
    handler = ErrorHandler()
    
    # Create a subclass of ValueError
    class CustomValueError(ValueError):
        pass
    
    exc = CustomValueError("Custom value error")
    rest_error, status_code = handler.handle(exc)
    
    # Should match ValueError mapping
    if status_code != 400:
        raise AssertionError(f"Expected status 400 for ValueError subclass, got {status_code}")


# =============================================================================
# Unit Tests: Production Mode Error Hiding
# =============================================================================

def test_error_handler_hides_500_details_production():
    """handle() should hide details for 500 errors in production mode."""
    handler = ErrorHandler(debug=False)
    
    # Register a mapping that returns 500
    handler.register_mapping(
        CustomServerError,
        ErrorMapping(status_code=500, error_code="server_error")
    )
    
    exc = CustomServerError("Sensitive database error details")
    rest_error, status_code = handler.handle(exc)
    
    if status_code != 500:
        raise AssertionError(f"Expected status 500, got {status_code}")
    
    # Should hide the sensitive details
    if "Sensitive database error details" in rest_error.message:
        raise AssertionError("Production mode should hide 500 error details")
    
    if rest_error.message != "An internal error occurred":
        raise AssertionError(f"Expected generic message, got '{rest_error.message}'")


def test_error_handler_shows_500_details_debug():
    """handle() should show details for 500 errors in debug mode."""
    handler = ErrorHandler(debug=True)
    
    # Register a mapping that returns 500
    handler.register_mapping(
        CustomServerError,
        ErrorMapping(status_code=500, error_code="server_error")
    )
    
    exc = CustomServerError("Database error details")
    rest_error, status_code = handler.handle(exc)
    
    if status_code != 500:
        raise AssertionError(f"Expected status 500, got {status_code}")
    
    # Should show the details in debug mode
    if "Database error details" not in rest_error.message:
        raise AssertionError(f"Debug mode should show 500 error details, got '{rest_error.message}'")


def test_error_handler_does_not_hide_4xx_details():
    """handle() should NOT hide details for 4xx errors even in production mode."""
    handler = ErrorHandler(debug=False)
    
    exc = ValueError("Invalid email format")
    rest_error, status_code = handler.handle(exc)
    
    if status_code != 400:
        raise AssertionError(f"Expected status 400, got {status_code}")
    
    # 4xx errors should show details even in production
    if "Invalid email format" not in rest_error.message:
        raise AssertionError(f"4xx errors should show details, got '{rest_error.message}'")


# =============================================================================
# Unit Tests: merge_error_maps()
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

# Feature: rest-api-support, Property 7: Error Response Status Code Mapping
# *For any* exception type with a registered error mapping, the error handler
# SHALL return the mapped status code and error code. *For any* ValidationError,
# the response SHALL be 400 with field_errors populated. *For any* NotFound,
# the response SHALL be 404. *For any* unhandled exception, the response SHALL be 500.
# **Validates: Requirements 7.3, 7.4, 7.5, 7.6, 7.7, 7.8, 8.1, 8.2**

def test_property_7_error_response_status_code_mapping():
    """
        Property 7: Error Response Status Code Mapping
        
        For any exception type with a registered error mapping, the error
        handler SHALL return the mapped status code and error code.
        
        For any ValidationError, the response SHALL be 400 with field_errors
        populated.
        
        For any unhandled exception, the response SHALL be 500.
        
        **Validates: Requirements 7.3, 7.4, 7.5, 7.6, 7.7, 7.8, 8.1, 8.2**
    """
    # Run 100 iterations with random data
    for iteration in range(100):
        handler = ErrorHandler(debug=random.choice([True, False]))
        
        # Test case 1: Registered exception returns mapped status code
        custom_mapping = generate_random_error_mapping()
        handler.register_mapping(CustomNotFoundError, custom_mapping)
        
        exc = CustomNotFoundError("User", generate_random_string(5, 10))
        rest_error, status_code = handler.handle(exc)
        
        # Property: status code must match mapping
        if status_code != custom_mapping.status_code:
            errmsg = f"Iteration {iteration}: Expected status {custom_mapping.status_code}, got {status_code}"
            raise AssertionError(errmsg)
        
        # Property: error code must match mapping
        if rest_error.error != custom_mapping.error_code:
            errmsg = f"Iteration {iteration}: Expected error '{custom_mapping.error_code}', got '{rest_error.error}'"
            raise AssertionError(errmsg)
        
        # Test case 2: ValidationError returns 400 with field_errors
        num_field_errors = random.randint(1, 5)
        field_errors = [generate_random_field_error() for _ in range(num_field_errors)]
        validation_exc = ValidationError(
            generate_random_string(10, 50),
            field_errors=field_errors
        )
        
        rest_error, status_code = handler.handle(validation_exc)
        
        # Property: ValidationError must return 400
        if status_code != 400:
            errmsg = f"Iteration {iteration}: ValidationError should return 400, got {status_code}"
            raise AssertionError(errmsg)
        
        # Property: ValidationError must have error code 'validation_error'
        if rest_error.error != "validation_error":
            errmsg = f"Iteration {iteration}: ValidationError should have error 'validation_error', got '{rest_error.error}'"
            raise AssertionError(errmsg)
        
        # Property: field_errors must be populated
        if rest_error.field_errors is None:
            errmsg = f"Iteration {iteration}: ValidationError response should have field_errors"
            raise AssertionError(errmsg)
        
        # Property: field_errors count must match
        if len(rest_error.field_errors) != num_field_errors:
            errmsg = f"Iteration {iteration}: Expected {num_field_errors} field errors, got {len(rest_error.field_errors)}"
            raise AssertionError(errmsg)
        
        # Test case 3: KeyError returns 404 (not_found)
        key_exc = KeyError(generate_random_string(5, 20))
        rest_error, status_code = handler.handle(key_exc)
        
        # Property: KeyError must return 404
        if status_code != 404:
            errmsg = f"Iteration {iteration}: KeyError should return 404, got {status_code}"
            raise AssertionError(errmsg)
        
        # Property: KeyError must have error code 'not_found'
        if rest_error.error != "not_found":
            errmsg = f"Iteration {iteration}: KeyError should have error 'not_found', got '{rest_error.error}'"
            raise AssertionError(errmsg)
        
        # Test case 4: PermissionError returns 403 (forbidden)
        perm_exc = PermissionError(generate_random_string(10, 30))
        rest_error, status_code = handler.handle(perm_exc)
        
        # Property: PermissionError must return 403
        if status_code != 403:
            errmsg = f"Iteration {iteration}: PermissionError should return 403, got {status_code}"
            raise AssertionError(errmsg)
        
        # Property: PermissionError must have error code 'forbidden'
        if rest_error.error != "forbidden":
            errmsg = f"Iteration {iteration}: PermissionError should have error 'forbidden', got '{rest_error.error}'"
            raise AssertionError(errmsg)
        
        # Test case 5: Unhandled exception returns 500
        unhandled_exc = CustomServerError(generate_random_string(10, 50))
        # Use a fresh handler without CustomServerError mapping
        fresh_handler = ErrorHandler(debug=handler.debug)
        rest_error, status_code = fresh_handler.handle(unhandled_exc)
        
        # Property: Unhandled exception must return 500
        if status_code != 500:
            errmsg = f"Iteration {iteration}: Unhandled exception should return 500, got {status_code}"
            raise AssertionError(errmsg)
        
        # Property: Unhandled exception must have error code 'internal_error'
        if rest_error.error != "internal_error":
            errmsg = f"Iteration {iteration}: Unhandled exception should have error 'internal_error', got '{rest_error.error}'"
            raise AssertionError(errmsg)
        
        # Test case 6: Production mode hides 500 error details
        prod_handler = ErrorHandler(debug=False)
        sensitive_message = generate_random_string(20, 50)
        unhandled_exc = CustomServerError(sensitive_message)
        rest_error, status_code = prod_handler.handle(unhandled_exc)
        
        # Property: Production mode must hide sensitive details
        if sensitive_message in rest_error.message:
            errmsg = f"Iteration {iteration}: Production mode should hide sensitive details"
            raise AssertionError(errmsg)
        
        # Property: Production mode must use generic message
        if rest_error.message != "An internal error occurred":
            errmsg = f"Iteration {iteration}: Production mode should use generic message, got '{rest_error.message}'"
            raise AssertionError(errmsg)
        
        # Test case 7: Debug mode shows 500 error details
        debug_handler = ErrorHandler(debug=True)
        rest_error, status_code = debug_handler.handle(unhandled_exc)
        
        # Property: Debug mode must show exception details
        if sensitive_message not in rest_error.message:
            errmsg = f"Iteration {iteration}: Debug mode should show exception details"
            raise AssertionError(errmsg)
        
        # Test case 8: Endpoint error_map takes priority over global
        endpoint_status = generate_random_status_code()
        endpoint_error_code = generate_random_error_code()
        endpoint_map = {
            ValueError: ErrorMapping(status_code=endpoint_status, error_code=endpoint_error_code)
        }
        
        value_exc = ValueError(generate_random_string(10, 30))
        rest_error, status_code = handler.handle(value_exc, endpoint_error_map=endpoint_map)
        
        # Property: Endpoint map must take priority
        if status_code != endpoint_status:
            errmsg = f"Iteration {iteration}: Endpoint map should take priority, expected {endpoint_status}, got {status_code}"
            raise AssertionError(errmsg)
        
        if rest_error.error != endpoint_error_code:
            errmsg = f"Iteration {iteration}: Endpoint map should take priority, expected '{endpoint_error_code}', got '{rest_error.error}'"
            raise AssertionError(errmsg)
    
    return


def test_property_error_map_inheritance():
    """
        Property: Error Map Inheritance
        
        For any parent and child error maps, the merged map SHALL contain
        all parent mappings plus all child mappings, with child mappings
        overriding parent mappings for the same exception type.
        
        **Validates: Requirements 8.6**
    """
    # Run 100 iterations with random data
    for iteration in range(100):
        # Generate random parent map
        parent_exceptions = [ValueError, KeyError, PermissionError]
        parent_map: Dict[Type[Exception], ErrorMapping] = {}
        num_parent = random.randint(0, len(parent_exceptions))
        for exc_type in random.sample(parent_exceptions, num_parent):
            parent_map[exc_type] = generate_random_error_mapping()
        
        # Generate random child map (may overlap with parent)
        child_exceptions = [ValueError, TypeError, RuntimeError]
        child_map: Dict[Type[Exception], ErrorMapping] = {}
        num_child = random.randint(0, len(child_exceptions))
        for exc_type in random.sample(child_exceptions, num_child):
            child_map[exc_type] = generate_random_error_mapping()
        
        # Merge maps
        result = merge_error_maps(
            parent_map if parent_map else None,
            child_map if child_map else None
        )
        
        # Property: Result must contain all parent mappings (unless overridden)
        for exc_type, mapping in parent_map.items():
            if exc_type not in result:
                errmsg = f"Iteration {iteration}: Parent mapping for {exc_type} should be in result"
                raise AssertionError(errmsg)
            
            # If not in child, should match parent
            if exc_type not in child_map:
                if result[exc_type] != mapping:
                    errmsg = f"Iteration {iteration}: Parent mapping for {exc_type} should be preserved"
                    raise AssertionError(errmsg)
        
        # Property: Result must contain all child mappings
        for exc_type, mapping in child_map.items():
            if exc_type not in result:
                errmsg = f"Iteration {iteration}: Child mapping for {exc_type} should be in result"
                raise AssertionError(errmsg)
            
            # Child should always override
            if result[exc_type] != mapping:
                errmsg = f"Iteration {iteration}: Child mapping for {exc_type} should override parent"
                raise AssertionError(errmsg)
        
        # Property: Result should not contain any extra mappings
        expected_keys = set(parent_map.keys()) | set(child_map.keys())
        if set(result.keys()) != expected_keys:
            errmsg = f"Iteration {iteration}: Result should only contain parent and child mappings"
            raise AssertionError(errmsg)
    
    return
