"""
.. module:: test_validation
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Tests for the REST API validation infrastructure.

    This module contains unit tests and property-based tests for the
    Validator class, including Pydantic model validation, dataclass
    validation, nested validation, and partial update support.

.. moduleauthor:: Automation Mojo LLC
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []

import random
import string
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from automojo.webworks.endpoints.rest import (
    Validator,
    ValidationError,
    FieldError,
)


# =============================================================================
# Test Dataclasses
# =============================================================================

@dataclass
class SimpleUser:
    """Simple dataclass for testing."""
    name: str
    age: int


@dataclass
class UserWithDefaults:
    """Dataclass with default values for testing."""
    name: str
    age: int = 0
    active: bool = True


@dataclass
class UserWithOptional:
    """Dataclass with optional field for testing."""
    name: str
    email: Optional[str] = None


@dataclass
class Address:
    """Nested dataclass for testing."""
    street: str
    city: str
    zip_code: str


@dataclass
class UserWithAddress:
    """Dataclass with nested dataclass for testing."""
    name: str
    address: Address


@dataclass
class UserWithMetadata:
    """Dataclass with field metadata for validation."""
    name: str = field(metadata={"min_length": 2, "max_length": 50})
    age: int = field(metadata={"min_value": 0, "max_value": 150})
    email: str = field(default="", metadata={"pattern": r"^[\w\.-]+@[\w\.-]+\.\w+$"})


@dataclass
class UserWithChoices:
    """Dataclass with choices validation."""
    name: str
    status: str = field(metadata={"choices": ["active", "inactive", "pending"]})


@dataclass
class UserWithTags:
    """Dataclass with list field."""
    name: str
    tags: List[str] = field(default_factory=list)


@dataclass
class UserWithAddressList:
    """Dataclass with list of nested dataclasses."""
    name: str
    addresses: List[Address] = field(default_factory=list)


@dataclass
class UserWithPostInit:
    """Dataclass with post-init validation."""
    name: str
    age: int
    
    def __post_init__(self):
        if self.age < 0:
            raise ValueError("Age cannot be negative")
        if not self.name.strip():
            raise ValueError("Name cannot be empty or whitespace")


# =============================================================================
# Random Data Generators
# =============================================================================

def generate_random_string(min_length: int = 1, max_length: int = 50) -> str:
    """Generate a random string of alphanumeric characters."""
    length = random.randint(min_length, max_length)
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def generate_random_field_path(max_depth: int = 3) -> str:
    """Generate a random field path like 'user.email' or 'items.0.name'."""
    parts = []
    depth = random.randint(1, max_depth)
    for i in range(depth):
        if random.random() < 0.3 and i > 0:
            # Add array index
            parts.append(str(random.randint(0, 10)))
        else:
            parts.append(generate_random_string(3, 15))
    return '.'.join(parts)


def generate_random_error_code() -> str:
    """Generate a random error code."""
    codes = [
        "required", "type_error", "invalid", "min_length", "max_length",
        "min_value", "max_value", "pattern", "invalid_choice"
    ]
    return random.choice(codes)


def generate_random_simple_user_data() -> Dict[str, Any]:
    """Generate random data for SimpleUser."""
    return {
        "name": generate_random_string(3, 30),
        "age": random.randint(0, 120)
    }


def generate_random_address_data() -> Dict[str, Any]:
    """Generate random data for Address."""
    return {
        "street": generate_random_string(5, 50),
        "city": generate_random_string(3, 30),
        "zip_code": generate_random_string(5, 10)
    }


def generate_random_user_with_address_data() -> Dict[str, Any]:
    """Generate random data for UserWithAddress."""
    return {
        "name": generate_random_string(3, 30),
        "address": generate_random_address_data()
    }


# =============================================================================
# Unit Tests: Validator Basic Functionality
# =============================================================================

def test_validator_validate_dict_schema():
    """Validator should validate dict schema."""
    validator = Validator()
    data = {"name": "Alice", "age": 30}
    
    result = validator.validate(data, dict)
    
    if result != data:
        raise AssertionError(f"Expected {data}, got {result}")


def test_validator_validate_dict_schema_rejects_non_dict():
    """Validator should reject non-dict for dict schema."""
    validator = Validator()
    data = ["item1", "item2"]
    
    raised = False
    try:
        validator.validate(data, dict)
    except ValidationError as e:
        raised = True
        if not e.field_errors:
            raise AssertionError("Expected field_errors to be populated")
        if e.field_errors[0].code != "type_error":
            raise AssertionError(f"Expected code 'type_error', got '{e.field_errors[0].code}'")
    
    if not raised:
        raise AssertionError("Expected ValidationError to be raised")


def test_validator_validate_null_data():
    """Validator should reject null data."""
    validator = Validator()
    
    raised = False
    try:
        validator.validate(None, dict)
    except ValidationError as e:
        raised = True
        if "required" not in e.message.lower():
            raise AssertionError(f"Expected 'required' in message, got '{e.message}'")
    
    if not raised:
        raise AssertionError("Expected ValidationError to be raised")


# =============================================================================
# Unit Tests: Dataclass Validation
# =============================================================================

def test_validator_validate_simple_dataclass():
    """Validator should validate simple dataclass."""
    validator = Validator()
    data = {"name": "Alice", "age": 30}
    
    result = validator.validate(data, SimpleUser)
    
    if not isinstance(result, SimpleUser):
        raise AssertionError(f"Expected SimpleUser, got {type(result)}")
    
    if result.name != "Alice":
        raise AssertionError(f"Expected name 'Alice', got '{result.name}'")
    
    if result.age != 30:
        raise AssertionError(f"Expected age 30, got {result.age}")


def test_validator_validate_dataclass_with_defaults():
    """Validator should use default values for missing fields."""
    validator = Validator()
    data = {"name": "Alice"}
    
    result = validator.validate(data, UserWithDefaults)
    
    if result.name != "Alice":
        raise AssertionError(f"Expected name 'Alice', got '{result.name}'")
    
    if result.age != 0:
        raise AssertionError(f"Expected default age 0, got {result.age}")
    
    if result.active is not True:
        raise AssertionError(f"Expected default active True, got {result.active}")


def test_validator_validate_dataclass_missing_required():
    """Validator should raise ValidationError for missing required field."""
    validator = Validator()
    data = {"name": "Alice"}  # Missing 'age'
    
    raised = False
    try:
        validator.validate(data, SimpleUser)
    except ValidationError as e:
        raised = True
        if not e.field_errors:
            raise AssertionError("Expected field_errors to be populated")
        
        age_error = None
        for fe in e.field_errors:
            if fe.field == "age":
                age_error = fe
                break
        
        if age_error is None:
            raise AssertionError("Expected error for 'age' field")
        
        if age_error.code != "required":
            raise AssertionError(f"Expected code 'required', got '{age_error.code}'")
    
    if not raised:
        raise AssertionError("Expected ValidationError to be raised")


def test_validator_validate_dataclass_optional_field():
    """Validator should handle optional fields."""
    validator = Validator()
    data = {"name": "Alice"}
    
    result = validator.validate(data, UserWithOptional)
    
    if result.name != "Alice":
        raise AssertionError(f"Expected name 'Alice', got '{result.name}'")
    
    if result.email is not None:
        raise AssertionError(f"Expected email None, got '{result.email}'")


def test_validator_validate_dataclass_optional_field_with_value():
    """Validator should accept value for optional field."""
    validator = Validator()
    data = {"name": "Alice", "email": "alice@example.com"}
    
    result = validator.validate(data, UserWithOptional)
    
    if result.email != "alice@example.com":
        raise AssertionError(f"Expected email 'alice@example.com', got '{result.email}'")


def test_validator_validate_dataclass_optional_field_null():
    """Validator should accept null for optional field."""
    validator = Validator()
    data = {"name": "Alice", "email": None}
    
    result = validator.validate(data, UserWithOptional)
    
    if result.email is not None:
        raise AssertionError(f"Expected email None, got '{result.email}'")


# =============================================================================
# Unit Tests: Nested Dataclass Validation
# =============================================================================

def test_validator_validate_nested_dataclass():
    """Validator should validate nested dataclass."""
    validator = Validator()
    data = {
        "name": "Alice",
        "address": {
            "street": "123 Main St",
            "city": "NYC",
            "zip_code": "10001"
        }
    }
    
    result = validator.validate(data, UserWithAddress)
    
    if not isinstance(result, UserWithAddress):
        raise AssertionError(f"Expected UserWithAddress, got {type(result)}")
    
    if not isinstance(result.address, Address):
        raise AssertionError(f"Expected Address, got {type(result.address)}")
    
    if result.address.city != "NYC":
        raise AssertionError(f"Expected city 'NYC', got '{result.address.city}'")


def test_validator_validate_nested_dataclass_missing_nested_field():
    """Validator should report nested field path for missing field."""
    validator = Validator()
    data = {
        "name": "Alice",
        "address": {
            "street": "123 Main St",
            "city": "NYC"
            # Missing zip_code
        }
    }
    
    raised = False
    try:
        validator.validate(data, UserWithAddress)
    except ValidationError as e:
        raised = True
        if not e.field_errors:
            raise AssertionError("Expected field_errors to be populated")
        
        # Should have error for address.zip_code
        zip_error = None
        for fe in e.field_errors:
            if "zip_code" in fe.field:
                zip_error = fe
                break
        
        if zip_error is None:
            raise AssertionError("Expected error for 'address.zip_code' field")
        
        if "address" not in zip_error.field:
            raise AssertionError(f"Expected nested path, got '{zip_error.field}'")
    
    if not raised:
        raise AssertionError("Expected ValidationError to be raised")


def test_validator_validate_list_of_nested_dataclass():
    """Validator should validate list of nested dataclasses."""
    validator = Validator()
    data = {
        "name": "Alice",
        "addresses": [
            {"street": "123 Main St", "city": "NYC", "zip_code": "10001"},
            {"street": "456 Oak Ave", "city": "LA", "zip_code": "90001"}
        ]
    }
    
    result = validator.validate(data, UserWithAddressList)
    
    if not isinstance(result, UserWithAddressList):
        raise AssertionError(f"Expected UserWithAddressList, got {type(result)}")
    
    if len(result.addresses) != 2:
        raise AssertionError(f"Expected 2 addresses, got {len(result.addresses)}")
    
    if not isinstance(result.addresses[0], Address):
        raise AssertionError(f"Expected Address, got {type(result.addresses[0])}")


def test_validator_validate_list_of_nested_dataclass_with_error():
    """Validator should report indexed path for list item errors."""
    validator = Validator()
    data = {
        "name": "Alice",
        "addresses": [
            {"street": "123 Main St", "city": "NYC", "zip_code": "10001"},
            {"street": "456 Oak Ave", "city": "LA"}  # Missing zip_code
        ]
    }
    
    raised = False
    try:
        validator.validate(data, UserWithAddressList)
    except ValidationError as e:
        raised = True
        if not e.field_errors:
            raise AssertionError("Expected field_errors to be populated")
        
        # Should have error for addresses.1.zip_code
        zip_error = None
        for fe in e.field_errors:
            if "zip_code" in fe.field and "1" in fe.field:
                zip_error = fe
                break
        
        if zip_error is None:
            raise AssertionError("Expected error for 'addresses.1.zip_code' field")
    
    if not raised:
        raise AssertionError("Expected ValidationError to be raised")


# =============================================================================
# Unit Tests: Field Metadata Validation
# =============================================================================

def test_validator_validate_metadata_min_length():
    """Validator should enforce min_length metadata."""
    validator = Validator()
    data = {"name": "A", "age": 30, "email": ""}  # name too short
    
    raised = False
    try:
        validator.validate(data, UserWithMetadata)
    except ValidationError as e:
        raised = True
        name_error = None
        for fe in e.field_errors:
            if fe.field == "name":
                name_error = fe
                break
        
        if name_error is None:
            raise AssertionError("Expected error for 'name' field")
        
        if name_error.code != "min_length":
            raise AssertionError(f"Expected code 'min_length', got '{name_error.code}'")
    
    if not raised:
        raise AssertionError("Expected ValidationError to be raised")


def test_validator_validate_metadata_max_length():
    """Validator should enforce max_length metadata."""
    validator = Validator()
    data = {"name": "A" * 100, "age": 30, "email": ""}  # name too long
    
    raised = False
    try:
        validator.validate(data, UserWithMetadata)
    except ValidationError as e:
        raised = True
        name_error = None
        for fe in e.field_errors:
            if fe.field == "name":
                name_error = fe
                break
        
        if name_error is None:
            raise AssertionError("Expected error for 'name' field")
        
        if name_error.code != "max_length":
            raise AssertionError(f"Expected code 'max_length', got '{name_error.code}'")
    
    if not raised:
        raise AssertionError("Expected ValidationError to be raised")


def test_validator_validate_metadata_min_value():
    """Validator should enforce min_value metadata."""
    validator = Validator()
    data = {"name": "Alice", "age": -5, "email": ""}  # age negative
    
    raised = False
    try:
        validator.validate(data, UserWithMetadata)
    except ValidationError as e:
        raised = True
        age_error = None
        for fe in e.field_errors:
            if fe.field == "age":
                age_error = fe
                break
        
        if age_error is None:
            raise AssertionError("Expected error for 'age' field")
        
        if age_error.code != "min_value":
            raise AssertionError(f"Expected code 'min_value', got '{age_error.code}'")
    
    if not raised:
        raise AssertionError("Expected ValidationError to be raised")


def test_validator_validate_metadata_max_value():
    """Validator should enforce max_value metadata."""
    validator = Validator()
    data = {"name": "Alice", "age": 200, "email": ""}  # age too high
    
    raised = False
    try:
        validator.validate(data, UserWithMetadata)
    except ValidationError as e:
        raised = True
        age_error = None
        for fe in e.field_errors:
            if fe.field == "age":
                age_error = fe
                break
        
        if age_error is None:
            raise AssertionError("Expected error for 'age' field")
        
        if age_error.code != "max_value":
            raise AssertionError(f"Expected code 'max_value', got '{age_error.code}'")
    
    if not raised:
        raise AssertionError("Expected ValidationError to be raised")


def test_validator_validate_metadata_choices():
    """Validator should enforce choices metadata."""
    validator = Validator()
    data = {"name": "Alice", "status": "unknown"}  # invalid status
    
    raised = False
    try:
        validator.validate(data, UserWithChoices)
    except ValidationError as e:
        raised = True
        status_error = None
        for fe in e.field_errors:
            if fe.field == "status":
                status_error = fe
                break
        
        if status_error is None:
            raise AssertionError("Expected error for 'status' field")
        
        if status_error.code != "invalid_choice":
            raise AssertionError(f"Expected code 'invalid_choice', got '{status_error.code}'")
    
    if not raised:
        raise AssertionError("Expected ValidationError to be raised")


def test_validator_validate_metadata_valid_data():
    """Validator should accept valid data with metadata constraints."""
    validator = Validator()
    data = {"name": "Alice", "age": 30, "email": "alice@example.com"}
    
    result = validator.validate(data, UserWithMetadata)
    
    if result.name != "Alice":
        raise AssertionError(f"Expected name 'Alice', got '{result.name}'")
    
    if result.age != 30:
        raise AssertionError(f"Expected age 30, got {result.age}")


# =============================================================================
# Unit Tests: Partial Validation
# =============================================================================

def test_validator_validate_partial_mode():
    """Validator should skip missing required fields in partial mode."""
    validator = Validator()
    data = {"name": "Alice"}  # Missing 'age' but partial=True
    
    result = validator.validate(data, SimpleUser, partial=True)
    
    # In partial mode, returns a dict with only validated fields
    if not isinstance(result, dict):
        raise AssertionError(f"Expected dict in partial mode, got {type(result)}")
    
    if result.get("name") != "Alice":
        raise AssertionError(f"Expected name 'Alice', got '{result.get('name')}'")
    
    # 'age' should not be in the result since it wasn't provided
    if "age" in result:
        raise AssertionError("Expected 'age' to not be in partial result")


def test_validator_validate_partial_mode_validates_provided_fields():
    """Validator should still validate provided fields in partial mode."""
    validator = Validator()
    data = {"name": "A", "age": 30}  # name too short
    
    raised = False
    try:
        validator.validate(data, UserWithMetadata, partial=True)
    except ValidationError as e:
        raised = True
        name_error = None
        for fe in e.field_errors:
            if fe.field == "name":
                name_error = fe
                break
        
        if name_error is None:
            raise AssertionError("Expected error for 'name' field")
    
    if not raised:
        raise AssertionError("Expected ValidationError to be raised")


# =============================================================================
# Unit Tests: Post-Init Validation
# =============================================================================

def test_validator_validate_post_init_success():
    """Validator should run post-init validation."""
    validator = Validator()
    data = {"name": "Alice", "age": 30}
    
    result = validator.validate(data, UserWithPostInit)
    
    if result.name != "Alice":
        raise AssertionError(f"Expected name 'Alice', got '{result.name}'")


def test_validator_validate_post_init_failure():
    """Validator should catch post-init validation errors."""
    validator = Validator()
    data = {"name": "Alice", "age": -5}  # Negative age triggers post-init error
    
    raised = False
    try:
        validator.validate(data, UserWithPostInit)
    except ValidationError as e:
        raised = True
        if "negative" not in e.message.lower():
            raise AssertionError(f"Expected 'negative' in message, got '{e.message}'")
    
    if not raised:
        raise AssertionError("Expected ValidationError to be raised")


# =============================================================================
# Property-Based Tests
# =============================================================================

# Feature: rest-api-support, Property 4: Validation Error Structure
# *For any* validation failure, the raised ValidationError SHALL contain
# a list of FieldError objects where each error includes the field path,
# error code, and human-readable message.
# **Validates: Requirements 5.4, 5.5**

def test_property_4_validation_error_structure():
    """
        Property 4: Validation Error Structure
        
        For any validation failure, the raised ValidationError SHALL contain
        a list of FieldError objects where each error includes the field path,
        error code, and human-readable message.
        
        **Validates: Requirements 5.4, 5.5**
    """
    validator = Validator()
    
    # Run 100 iterations with various invalid data scenarios
    for iteration in range(100):
        # Generate random invalid data scenarios
        scenario = random.choice([
            "missing_required",
            "invalid_type",
            "nested_missing",
            "metadata_violation",
            "multiple_errors"
        ])
        
        try:
            if scenario == "missing_required":
                # Missing required field
                data = {"name": generate_random_string(3, 20)}  # Missing 'age'
                validator.validate(data, SimpleUser)
                
            elif scenario == "invalid_type":
                # Non-dict for dataclass
                data = [generate_random_string(3, 20)]
                validator.validate(data, SimpleUser)
                
            elif scenario == "nested_missing":
                # Missing nested field
                data = {
                    "name": generate_random_string(3, 20),
                    "address": {
                        "street": generate_random_string(5, 30),
                        "city": generate_random_string(3, 20)
                        # Missing zip_code
                    }
                }
                validator.validate(data, UserWithAddress)
                
            elif scenario == "metadata_violation":
                # Metadata constraint violation
                data = {
                    "name": "A",  # Too short (min_length=2)
                    "age": 30,
                    "email": ""
                }
                validator.validate(data, UserWithMetadata)
                
            elif scenario == "multiple_errors":
                # Multiple validation errors
                data = {}  # Missing both name and age
                validator.validate(data, SimpleUser)
            
            # If we get here, validation didn't fail as expected
            # This is acceptable for some random data
            continue
            
        except ValidationError as e:
            # Property: ValidationError must have a message
            if not isinstance(e.message, str):
                errmsg = f"Iteration {iteration} ({scenario}): message must be a string"
                raise AssertionError(errmsg)
            
            if len(e.message) == 0:
                errmsg = f"Iteration {iteration} ({scenario}): message must not be empty"
                raise AssertionError(errmsg)
            
            # Property: ValidationError must have field_errors list
            if not isinstance(e.field_errors, list):
                errmsg = f"Iteration {iteration} ({scenario}): field_errors must be a list"
                raise AssertionError(errmsg)
            
            # Property: field_errors must not be empty for validation failures
            if len(e.field_errors) == 0:
                errmsg = f"Iteration {iteration} ({scenario}): field_errors must not be empty"
                raise AssertionError(errmsg)
            
            # Property: Each field_error must be a FieldError instance
            for idx, fe in enumerate(e.field_errors):
                if not isinstance(fe, FieldError):
                    errmsg = f"Iteration {iteration} ({scenario}): field_errors[{idx}] must be FieldError"
                    raise AssertionError(errmsg)
                
                # Property: field must be a non-empty string
                if not isinstance(fe.field, str):
                    errmsg = f"Iteration {iteration} ({scenario}): field_errors[{idx}].field must be string"
                    raise AssertionError(errmsg)
                
                if len(fe.field) == 0:
                    errmsg = f"Iteration {iteration} ({scenario}): field_errors[{idx}].field must not be empty"
                    raise AssertionError(errmsg)
                
                # Property: code must be a non-empty string
                if not isinstance(fe.code, str):
                    errmsg = f"Iteration {iteration} ({scenario}): field_errors[{idx}].code must be string"
                    raise AssertionError(errmsg)
                
                if len(fe.code) == 0:
                    errmsg = f"Iteration {iteration} ({scenario}): field_errors[{idx}].code must not be empty"
                    raise AssertionError(errmsg)
                
                # Property: message must be a non-empty string
                if not isinstance(fe.message, str):
                    errmsg = f"Iteration {iteration} ({scenario}): field_errors[{idx}].message must be string"
                    raise AssertionError(errmsg)
                
                if len(fe.message) == 0:
                    errmsg = f"Iteration {iteration} ({scenario}): field_errors[{idx}].message must not be empty"
                    raise AssertionError(errmsg)
    
    return


def test_property_4_validation_error_field_path_format():
    """
        Property 4: Validation Error Structure - Field Path Format
        
        For any nested validation failure, the field path SHALL correctly
        represent the path to the invalid field using dot notation
        (e.g., "user.address.city").
        
        **Validates: Requirements 5.4, 5.5**
    """
    validator = Validator()
    
    # Run 100 iterations with nested validation scenarios
    for iteration in range(100):
        # Generate random nested data with missing fields
        depth = random.randint(1, 2)
        
        if depth == 1:
            # Single level nesting
            data = {
                "name": generate_random_string(3, 20),
                "address": {
                    "street": generate_random_string(5, 30),
                    "city": generate_random_string(3, 20)
                    # Missing zip_code
                }
            }
            expected_field_prefix = "address"
            schema = UserWithAddress
        else:
            # List nesting
            idx = random.randint(0, 5)
            addresses = []
            for i in range(idx + 1):
                if i == idx:
                    # This one has missing field
                    addresses.append({
                        "street": generate_random_string(5, 30),
                        "city": generate_random_string(3, 20)
                        # Missing zip_code
                    })
                else:
                    addresses.append({
                        "street": generate_random_string(5, 30),
                        "city": generate_random_string(3, 20),
                        "zip_code": generate_random_string(5, 10)
                    })
            
            data = {
                "name": generate_random_string(3, 20),
                "addresses": addresses
            }
            expected_field_prefix = f"addresses.{idx}"
            schema = UserWithAddressList
        
        try:
            validator.validate(data, schema)
            # If validation passes, skip this iteration
            continue
        except ValidationError as e:
            # Property: At least one field error should have the expected prefix
            has_expected_prefix = False
            for fe in e.field_errors:
                if fe.field.startswith(expected_field_prefix):
                    has_expected_prefix = True
                    break
            
            if not has_expected_prefix:
                errmsg = f"Iteration {iteration}: Expected field path starting with '{expected_field_prefix}'"
                raise AssertionError(errmsg)
            
            # Property: Field path should use dot notation
            for fe in e.field_errors:
                # Field path should not contain invalid characters
                valid_chars = set(string.ascii_letters + string.digits + "._$")
                for char in fe.field:
                    if char not in valid_chars:
                        errmsg = f"Iteration {iteration}: Invalid character '{char}' in field path '{fe.field}'"
                        raise AssertionError(errmsg)
    
    return


def test_property_4_validation_error_multiple_errors():
    """
        Property 4: Validation Error Structure - Multiple Errors
        
        For any data with multiple validation failures, the ValidationError
        SHALL contain all field-level errors, not just the first one.
        
        **Validates: Requirements 5.4, 5.5**
    """
    validator = Validator()
    
    # Run 100 iterations with multiple error scenarios
    for iteration in range(100):
        # Generate data with multiple missing required fields
        num_missing = random.randint(2, 3)
        
        if num_missing == 2:
            # Missing both name and age
            data = {}
            schema = SimpleUser
            expected_fields = {"name", "age"}
        else:
            # Missing multiple nested fields
            data = {
                "name": generate_random_string(3, 20),
                "address": {}  # Missing all address fields
            }
            schema = UserWithAddress
            expected_fields = {"address.street", "address.city", "address.zip_code"}
        
        try:
            validator.validate(data, schema)
            # If validation passes, skip this iteration
            continue
        except ValidationError as e:
            # Property: Should have multiple field errors
            if len(e.field_errors) < 2:
                errmsg = f"Iteration {iteration}: Expected multiple field errors, got {len(e.field_errors)}"
                raise AssertionError(errmsg)
            
            # Property: All expected fields should have errors
            error_fields = {fe.field for fe in e.field_errors}
            for expected_field in expected_fields:
                if expected_field not in error_fields:
                    errmsg = f"Iteration {iteration}: Missing error for field '{expected_field}'"
                    raise AssertionError(errmsg)
    
    return
