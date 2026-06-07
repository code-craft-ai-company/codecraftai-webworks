"""
.. module:: test_negotiation
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Tests for the REST API content negotiation infrastructure.

    This module contains unit tests and property-based tests for the
    ContentNegotiator class and related exceptions (NotAcceptable,
    UnsupportedMediaType).

.. moduleauthor:: Code Craft AI LLC
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []

import random
import string
from typing import List, Optional

from ccai.webworks.endpoints.rest import (
    ContentNegotiator,
    NotAcceptable,
    UnsupportedMediaType,
    SerializerRegistry,
    JSONSerializer,
    JSONDeserializer,
    create_default_registry,
    DEFAULT_CONTENT_TYPE,
)


# =============================================================================
# Test Helpers
# =============================================================================

def create_test_registry() -> SerializerRegistry:
    """Create a registry with JSON support for testing."""
    return create_default_registry()


def create_empty_registry() -> SerializerRegistry:
    """Create an empty registry for testing edge cases."""
    return SerializerRegistry()


# =============================================================================
# Random Data Generators for Property Tests
# =============================================================================

def generate_random_string(min_length: int = 1, max_length: int = 20) -> str:
    """Generate a random string of alphanumeric characters."""
    length = random.randint(min_length, max_length)
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))


def generate_random_quality() -> float:
    """Generate a random quality value between 0.0 and 1.0."""
    return round(random.uniform(0.0, 1.0), 2)


def generate_random_accept_header_with_json() -> str:
    """Generate a random Accept header that includes application/json."""
    # Possible formats to include
    formats = [
        "application/json",
        "text/html",
        "application/xml",
        "text/plain",
        "*/*",
        "application/*",
    ]
    
    # Always include application/json
    selected = ["application/json"]
    
    # Add some random other formats
    num_others = random.randint(0, 3)
    for _ in range(num_others):
        fmt = random.choice(formats)
        if fmt not in selected:
            selected.append(fmt)
    
    # Shuffle and add quality values
    random.shuffle(selected)
    parts = []
    for fmt in selected:
        if random.random() < 0.5:
            q = generate_random_quality()
            parts.append(f"{fmt};q={q}")
        else:
            parts.append(fmt)
    
    return ", ".join(parts)


def generate_random_accept_header_without_json() -> str:
    """Generate a random Accept header that does NOT include application/json."""
    # Formats that are NOT application/json
    formats = [
        "text/html",
        "application/xml",
        "text/plain",
        "text/csv",
        "application/pdf",
    ]
    
    num_formats = random.randint(1, 3)
    selected = random.sample(formats, min(num_formats, len(formats)))
    
    parts = []
    for fmt in selected:
        if random.random() < 0.5:
            q = generate_random_quality()
            parts.append(f"{fmt};q={q}")
        else:
            parts.append(fmt)
    
    return ", ".join(parts)


def generate_random_content_type_json() -> str:
    """Generate a random Content-Type header for JSON."""
    base = "application/json"
    
    # Sometimes add charset parameter
    if random.random() < 0.3:
        return f"{base}; charset=utf-8"
    
    return base


def generate_random_content_type_unsupported() -> str:
    """Generate a random unsupported Content-Type."""
    unsupported = [
        "application/xml",
        "text/html",
        "text/plain",
        "application/pdf",
        "image/png",
        "multipart/form-data",
    ]
    return random.choice(unsupported)


# =============================================================================
# Unit Tests: NotAcceptable Exception
# =============================================================================

def test_not_acceptable_status_code():
    """NotAcceptable should have status_code 406."""
    exc = NotAcceptable(["application/json"])
    
    if exc.status_code != 406:
        errmsg = f"Expected status_code 406, got {exc.status_code}"
        raise AssertionError(errmsg)


def test_not_acceptable_supported_types():
    """NotAcceptable should store supported_types."""
    supported = ["application/json", "application/xml"]
    exc = NotAcceptable(supported)
    
    if exc.supported_types != supported:
        errmsg = f"Expected supported_types {supported}, got {exc.supported_types}"
        raise AssertionError(errmsg)


def test_not_acceptable_detail_message():
    """NotAcceptable should include supported formats in detail."""
    supported = ["application/json", "application/xml"]
    exc = NotAcceptable(supported)
    
    if "application/json" not in exc.detail:
        raise AssertionError("Expected 'application/json' in detail message")
    
    if "application/xml" not in exc.detail:
        raise AssertionError("Expected 'application/xml' in detail message")


def test_not_acceptable_single_type():
    """NotAcceptable should work with single supported type."""
    exc = NotAcceptable(["application/json"])
    
    if exc.status_code != 406:
        raise AssertionError("Expected status_code 406")
    
    if "application/json" not in exc.detail:
        raise AssertionError("Expected 'application/json' in detail")


# =============================================================================
# Unit Tests: UnsupportedMediaType Exception
# =============================================================================

def test_unsupported_media_type_status_code():
    """UnsupportedMediaType should have status_code 415."""
    exc = UnsupportedMediaType("text/xml", ["application/json"])
    
    if exc.status_code != 415:
        errmsg = f"Expected status_code 415, got {exc.status_code}"
        raise AssertionError(errmsg)


def test_unsupported_media_type_content_type():
    """UnsupportedMediaType should store content_type."""
    exc = UnsupportedMediaType("text/xml", ["application/json"])
    
    if exc.content_type != "text/xml":
        errmsg = f"Expected content_type 'text/xml', got '{exc.content_type}'"
        raise AssertionError(errmsg)


def test_unsupported_media_type_supported_types():
    """UnsupportedMediaType should store supported_types."""
    supported = ["application/json", "application/xml"]
    exc = UnsupportedMediaType("text/html", supported)
    
    if exc.supported_types != supported:
        errmsg = f"Expected supported_types {supported}, got {exc.supported_types}"
        raise AssertionError(errmsg)


def test_unsupported_media_type_detail_message():
    """UnsupportedMediaType should include content type and supported formats in detail."""
    exc = UnsupportedMediaType("text/xml", ["application/json"])
    
    if "text/xml" not in exc.detail:
        raise AssertionError("Expected 'text/xml' in detail message")
    
    if "application/json" not in exc.detail:
        raise AssertionError("Expected 'application/json' in detail message")


# =============================================================================
# Unit Tests: ContentNegotiator.select_response_format
# =============================================================================

def test_select_response_format_exact_match():
    """select_response_format should return exact match."""
    registry = create_test_registry()
    negotiator = ContentNegotiator(registry)
    
    result = negotiator.select_response_format("application/json")
    
    if result != "application/json":
        errmsg = f"Expected 'application/json', got '{result}'"
        raise AssertionError(errmsg)


def test_select_response_format_with_quality():
    """select_response_format should respect quality values."""
    registry = create_test_registry()
    negotiator = ContentNegotiator(registry)
    
    # JSON has higher quality
    result = negotiator.select_response_format("text/html;q=0.5, application/json;q=1.0")
    
    if result != "application/json":
        errmsg = f"Expected 'application/json', got '{result}'"
        raise AssertionError(errmsg)


def test_select_response_format_wildcard():
    """select_response_format should handle wildcard."""
    registry = create_test_registry()
    negotiator = ContentNegotiator(registry)
    
    result = negotiator.select_response_format("*/*")
    
    if result != "application/json":
        errmsg = f"Expected 'application/json', got '{result}'"
        raise AssertionError(errmsg)


def test_select_response_format_type_wildcard():
    """select_response_format should handle type wildcard."""
    registry = create_test_registry()
    negotiator = ContentNegotiator(registry)
    
    result = negotiator.select_response_format("application/*")
    
    if result != "application/json":
        errmsg = f"Expected 'application/json', got '{result}'"
        raise AssertionError(errmsg)


def test_select_response_format_none_header():
    """select_response_format should default to JSON when Accept is None."""
    registry = create_test_registry()
    negotiator = ContentNegotiator(registry)
    
    result = negotiator.select_response_format(None)
    
    if result != "application/json":
        errmsg = f"Expected 'application/json', got '{result}'"
        raise AssertionError(errmsg)


def test_select_response_format_empty_header():
    """select_response_format should default to JSON when Accept is empty."""
    registry = create_test_registry()
    negotiator = ContentNegotiator(registry)
    
    result = negotiator.select_response_format("")
    
    if result != "application/json":
        errmsg = f"Expected 'application/json', got '{result}'"
        raise AssertionError(errmsg)


def test_select_response_format_whitespace_header():
    """select_response_format should default to JSON when Accept is whitespace."""
    registry = create_test_registry()
    negotiator = ContentNegotiator(registry)
    
    result = negotiator.select_response_format("   ")
    
    if result != "application/json":
        errmsg = f"Expected 'application/json', got '{result}'"
        raise AssertionError(errmsg)


def test_select_response_format_not_acceptable():
    """select_response_format should raise NotAcceptable when no match."""
    registry = create_test_registry()
    negotiator = ContentNegotiator(registry)
    
    raised = False
    try:
        negotiator.select_response_format("text/xml")
    except NotAcceptable as e:
        raised = True
        if e.status_code != 406:
            raise AssertionError(f"Expected status_code 406, got {e.status_code}")
        if "application/json" not in e.supported_types:
            raise AssertionError("Expected 'application/json' in supported_types")
    
    if not raised:
        raise AssertionError("Expected NotAcceptable to be raised")


def test_select_response_format_multiple_unsupported():
    """select_response_format should raise NotAcceptable for multiple unsupported types."""
    registry = create_test_registry()
    negotiator = ContentNegotiator(registry)
    
    raised = False
    try:
        negotiator.select_response_format("text/xml, text/html, application/pdf")
    except NotAcceptable as e:
        raised = True
        if e.status_code != 406:
            raise AssertionError(f"Expected status_code 406, got {e.status_code}")
    
    if not raised:
        raise AssertionError("Expected NotAcceptable to be raised")


# =============================================================================
# Unit Tests: ContentNegotiator.validate_request_format
# =============================================================================

def test_validate_request_format_json():
    """validate_request_format should accept application/json."""
    registry = create_test_registry()
    negotiator = ContentNegotiator(registry)
    
    result = negotiator.validate_request_format("application/json")
    
    if result != "application/json":
        errmsg = f"Expected 'application/json', got '{result}'"
        raise AssertionError(errmsg)


def test_validate_request_format_json_with_charset():
    """validate_request_format should accept JSON with charset parameter."""
    registry = create_test_registry()
    negotiator = ContentNegotiator(registry)
    
    result = negotiator.validate_request_format("application/json; charset=utf-8")
    
    if result != "application/json":
        errmsg = f"Expected 'application/json', got '{result}'"
        raise AssertionError(errmsg)


def test_validate_request_format_none():
    """validate_request_format should default to JSON when Content-Type is None."""
    registry = create_test_registry()
    negotiator = ContentNegotiator(registry)
    
    result = negotiator.validate_request_format(None)
    
    if result != "application/json":
        errmsg = f"Expected 'application/json', got '{result}'"
        raise AssertionError(errmsg)


def test_validate_request_format_empty():
    """validate_request_format should default to JSON when Content-Type is empty."""
    registry = create_test_registry()
    negotiator = ContentNegotiator(registry)
    
    result = negotiator.validate_request_format("")
    
    if result != "application/json":
        errmsg = f"Expected 'application/json', got '{result}'"
        raise AssertionError(errmsg)


def test_validate_request_format_whitespace():
    """validate_request_format should default to JSON when Content-Type is whitespace."""
    registry = create_test_registry()
    negotiator = ContentNegotiator(registry)
    
    result = negotiator.validate_request_format("   ")
    
    if result != "application/json":
        errmsg = f"Expected 'application/json', got '{result}'"
        raise AssertionError(errmsg)


def test_validate_request_format_unsupported():
    """validate_request_format should raise UnsupportedMediaType for unsupported type."""
    registry = create_test_registry()
    negotiator = ContentNegotiator(registry)
    
    raised = False
    try:
        negotiator.validate_request_format("text/xml")
    except UnsupportedMediaType as e:
        raised = True
        if e.status_code != 415:
            raise AssertionError(f"Expected status_code 415, got {e.status_code}")
        if e.content_type != "text/xml":
            raise AssertionError(f"Expected content_type 'text/xml', got '{e.content_type}'")
        if "application/json" not in e.supported_types:
            raise AssertionError("Expected 'application/json' in supported_types")
    
    if not raised:
        raise AssertionError("Expected UnsupportedMediaType to be raised")


def test_validate_request_format_case_insensitive():
    """validate_request_format should be case-insensitive."""
    registry = create_test_registry()
    negotiator = ContentNegotiator(registry)
    
    result = negotiator.validate_request_format("Application/JSON")
    
    if result != "application/json":
        errmsg = f"Expected 'application/json', got '{result}'"
        raise AssertionError(errmsg)


# =============================================================================
# Unit Tests: Edge Cases
# =============================================================================

def test_content_negotiator_empty_registry_select():
    """ContentNegotiator with empty registry should raise NotAcceptable."""
    registry = create_empty_registry()
    negotiator = ContentNegotiator(registry)
    
    raised = False
    try:
        negotiator.select_response_format("application/json")
    except NotAcceptable as e:
        raised = True
        # Should default to JSON in supported types
        if "application/json" not in e.supported_types:
            raise AssertionError("Expected 'application/json' in supported_types")
    
    if not raised:
        raise AssertionError("Expected NotAcceptable to be raised")


def test_content_negotiator_empty_registry_validate():
    """ContentNegotiator with empty registry should raise UnsupportedMediaType."""
    registry = create_empty_registry()
    negotiator = ContentNegotiator(registry)
    
    raised = False
    try:
        negotiator.validate_request_format("application/json")
    except UnsupportedMediaType as e:
        raised = True
        # Should default to JSON in supported types
        if "application/json" not in e.supported_types:
            raise AssertionError("Expected 'application/json' in supported_types")
    
    if not raised:
        raise AssertionError("Expected UnsupportedMediaType to be raised")


def test_default_content_type_constant():
    """DEFAULT_CONTENT_TYPE should be 'application/json'."""
    if DEFAULT_CONTENT_TYPE != "application/json":
        errmsg = f"Expected DEFAULT_CONTENT_TYPE 'application/json', got '{DEFAULT_CONTENT_TYPE}'"
        raise AssertionError(errmsg)


# =============================================================================
# Property-Based Tests
# =============================================================================

# Feature: rest-api-support, Property 6: Content Negotiation Selection
# *For any* Accept header value, the content negotiator SHALL select the most
# appropriate supported format, or return 406 Not Acceptable if no format matches.
# *For any* missing Accept header, the system SHALL default to application/json.
# **Validates: Requirements 6.1, 6.4, 6.5**

def test_property_6_content_negotiation_default_json():
    """
        Property 6: Content Negotiation Selection (default to JSON)
        
        For any missing or empty Accept header, the system SHALL default
        to application/json.
        
        **Validates: Requirements 6.2, 6.5**
    """
    registry = create_test_registry()
    negotiator = ContentNegotiator(registry)
    
    # Run 100 iterations with various empty/None values
    empty_values = [None, "", "   ", "\t", "\n", "  \t  "]
    
    for iteration in range(100):
        # Select a random empty value
        accept_header = random.choice(empty_values)
        
        # Property: should always return application/json
        result = negotiator.select_response_format(accept_header)
        
        if result != "application/json":
            errmsg = f"Iteration {iteration}: Expected 'application/json' for empty Accept header, got '{result}'"
            raise AssertionError(errmsg)
    
    return


def test_property_6_content_negotiation_accepts_json():
    """
        Property 6: Content Negotiation Selection (Accept header with JSON)
        
        For any Accept header that includes application/json (directly or via wildcard),
        the system SHALL select application/json.
        
        **Validates: Requirements 6.1, 6.5**
    """
    registry = create_test_registry()
    negotiator = ContentNegotiator(registry)
    
    # Run 100 iterations with random Accept headers that include JSON
    for iteration in range(100):
        accept_header = generate_random_accept_header_with_json()
        
        # Property: should return application/json (the only supported type)
        result = negotiator.select_response_format(accept_header)
        
        if result != "application/json":
            errmsg = f"Iteration {iteration}: Expected 'application/json' for Accept '{accept_header}', got '{result}'"
            raise AssertionError(errmsg)
    
    return


def test_property_6_content_negotiation_not_acceptable():
    """
        Property 6: Content Negotiation Selection (406 Not Acceptable)
        
        For any Accept header that does NOT include application/json or wildcards,
        the system SHALL raise NotAcceptable (406).
        
        **Validates: Requirements 6.4**
    """
    registry = create_test_registry()
    negotiator = ContentNegotiator(registry)
    
    # Run 100 iterations with Accept headers that don't include JSON
    for iteration in range(100):
        accept_header = generate_random_accept_header_without_json()
        
        # Property: should raise NotAcceptable
        raised = False
        try:
            negotiator.select_response_format(accept_header)
        except NotAcceptable as e:
            raised = True
            
            # Property: status code must be 406
            if e.status_code != 406:
                errmsg = f"Iteration {iteration}: Expected status_code 406, got {e.status_code}"
                raise AssertionError(errmsg)
            
            # Property: supported_types must include application/json
            if "application/json" not in e.supported_types:
                errmsg = f"Iteration {iteration}: Expected 'application/json' in supported_types"
                raise AssertionError(errmsg)
        
        if not raised:
            errmsg = f"Iteration {iteration}: Expected NotAcceptable for Accept '{accept_header}'"
            raise AssertionError(errmsg)
    
    return


def test_property_6_content_negotiation_validate_json():
    """
        Property 6: Content Negotiation Selection (validate JSON Content-Type)
        
        For any Content-Type header that is application/json (with or without params),
        the system SHALL accept it.
        
        **Validates: Requirements 6.6**
    """
    registry = create_test_registry()
    negotiator = ContentNegotiator(registry)
    
    # Run 100 iterations with JSON Content-Type variations
    for iteration in range(100):
        content_type = generate_random_content_type_json()
        
        # Property: should return application/json
        result = negotiator.validate_request_format(content_type)
        
        if result != "application/json":
            errmsg = f"Iteration {iteration}: Expected 'application/json' for Content-Type '{content_type}', got '{result}'"
            raise AssertionError(errmsg)
    
    return


def test_property_6_content_negotiation_unsupported_media_type():
    """
        Property 6: Content Negotiation Selection (415 Unsupported Media Type)
        
        For any Content-Type header that is NOT application/json,
        the system SHALL raise UnsupportedMediaType (415).
        
        **Validates: Requirements 6.7**
    """
    registry = create_test_registry()
    negotiator = ContentNegotiator(registry)
    
    # Run 100 iterations with unsupported Content-Types
    for iteration in range(100):
        content_type = generate_random_content_type_unsupported()
        
        # Property: should raise UnsupportedMediaType
        raised = False
        try:
            negotiator.validate_request_format(content_type)
        except UnsupportedMediaType as e:
            raised = True
            
            # Property: status code must be 415
            if e.status_code != 415:
                errmsg = f"Iteration {iteration}: Expected status_code 415, got {e.status_code}"
                raise AssertionError(errmsg)
            
            # Property: content_type must match the unsupported type
            if e.content_type != content_type:
                errmsg = f"Iteration {iteration}: Expected content_type '{content_type}', got '{e.content_type}'"
                raise AssertionError(errmsg)
            
            # Property: supported_types must include application/json
            if "application/json" not in e.supported_types:
                errmsg = f"Iteration {iteration}: Expected 'application/json' in supported_types"
                raise AssertionError(errmsg)
        
        if not raised:
            errmsg = f"Iteration {iteration}: Expected UnsupportedMediaType for Content-Type '{content_type}'"
            raise AssertionError(errmsg)
    
    return


def test_property_6_content_negotiation_validate_default():
    """
        Property 6: Content Negotiation Selection (default Content-Type)
        
        For any missing or empty Content-Type header, the system SHALL
        default to application/json.
        
        **Validates: Requirements 6.6**
    """
    registry = create_test_registry()
    negotiator = ContentNegotiator(registry)
    
    # Run 100 iterations with various empty/None values
    empty_values = [None, "", "   ", "\t", "\n"]
    
    for iteration in range(100):
        content_type = random.choice(empty_values)
        
        # Property: should return application/json
        result = negotiator.validate_request_format(content_type)
        
        if result != "application/json":
            errmsg = f"Iteration {iteration}: Expected 'application/json' for empty Content-Type, got '{result}'"
            raise AssertionError(errmsg)
    
    return
