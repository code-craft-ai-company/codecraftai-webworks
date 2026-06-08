"""
.. module:: test_serialization
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Tests for the REST API serialization infrastructure.

    This module contains unit tests and property-based tests for the
    serialization classes: Serializer, Deserializer, JSONSerializer,
    JSONDeserializer, and SerializerRegistry.

.. moduleauthor:: Code Craft AI LLC
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []

import json
import random
import string
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ccai.webworks.endpoints.rest import (
    Serializer,
    Deserializer,
    JSONSerializer,
    JSONDeserializer,
    SerializerRegistry,
    ValidationError,
    create_default_registry,
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
class UserWithOptionalList:
    """Dataclass with optional list field."""
    name: str
    tags: List[str] = field(default_factory=list)


# =============================================================================
# Random Data Generators
# =============================================================================

def generate_random_string(min_length: int = 1, max_length: int = 50) -> str:
    """Generate a random string of alphanumeric characters."""
    length = random.randint(min_length, max_length)
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def generate_random_int(min_val: int = -1000, max_val: int = 1000) -> int:
    """Generate a random integer."""
    return random.randint(min_val, max_val)


def generate_random_float(min_val: float = -1000.0, max_val: float = 1000.0) -> float:
    """Generate a random float."""
    return random.uniform(min_val, max_val)


def generate_random_bool() -> bool:
    """Generate a random boolean."""
    return random.choice([True, False])


def generate_random_primitive() -> Any:
    """Generate a random primitive value."""
    choice = random.choice(['string', 'int', 'float', 'bool', 'none'])
    if choice == 'string':
        return generate_random_string(1, 30)
    elif choice == 'int':
        return generate_random_int()
    elif choice == 'float':
        return generate_random_float()
    elif choice == 'bool':
        return generate_random_bool()
    else:
        return None


def generate_random_dict(max_depth: int = 2, max_keys: int = 5) -> Dict[str, Any]:
    """Generate a random dictionary."""
    result = {}
    num_keys = random.randint(1, max_keys)
    
    for _ in range(num_keys):
        key = generate_random_string(3, 15)
        if max_depth > 0 and random.random() < 0.3:
            # Nested dict
            result[key] = generate_random_dict(max_depth - 1, max_keys)
        elif random.random() < 0.2:
            # List of primitives
            result[key] = [generate_random_primitive() for _ in range(random.randint(1, 5))]
        else:
            result[key] = generate_random_primitive()
    
    return result


def generate_random_simple_user() -> SimpleUser:
    """Generate a random SimpleUser dataclass."""
    return SimpleUser(
        name=generate_random_string(3, 30),
        age=random.randint(0, 120)
    )


def generate_random_user_with_defaults() -> UserWithDefaults:
    """Generate a random UserWithDefaults dataclass."""
    return UserWithDefaults(
        name=generate_random_string(3, 30),
        age=random.randint(0, 120),
        active=generate_random_bool()
    )


# =============================================================================
# Unit Tests: JSONSerializer
# =============================================================================

def test_json_serializer_content_type():
    """JSONSerializer should have content_type 'application/json'."""
    serializer = JSONSerializer()
    
    if serializer.content_type != "application/json":
        errmsg = f"Expected content_type 'application/json', got '{serializer.content_type}'"
        raise AssertionError(errmsg)


def test_json_serializer_dict():
    """JSONSerializer should serialize dict to JSON bytes."""
    serializer = JSONSerializer()
    data = {"name": "Alice", "age": 30}
    
    result = serializer.serialize(data)
    
    if not isinstance(result, bytes):
        raise AssertionError(f"Expected bytes, got {type(result)}")
    
    parsed = json.loads(result.decode("utf-8"))
    if parsed != data:
        raise AssertionError(f"Expected {data}, got {parsed}")


def test_json_serializer_nested_dict():
    """JSONSerializer should serialize nested dict."""
    serializer = JSONSerializer()
    data = {"user": {"name": "Alice", "address": {"city": "NYC"}}}
    
    result = serializer.serialize(data)
    parsed = json.loads(result.decode("utf-8"))
    
    if parsed != data:
        raise AssertionError(f"Expected {data}, got {parsed}")


def test_json_serializer_list():
    """JSONSerializer should serialize list."""
    serializer = JSONSerializer()
    data = [{"name": "Alice"}, {"name": "Bob"}]
    
    result = serializer.serialize(data)
    parsed = json.loads(result.decode("utf-8"))
    
    if parsed != data:
        raise AssertionError(f"Expected {data}, got {parsed}")


def test_json_serializer_dataclass():
    """JSONSerializer should serialize dataclass using asdict()."""
    serializer = JSONSerializer()
    user = SimpleUser(name="Alice", age=30)
    
    result = serializer.serialize(user)
    parsed = json.loads(result.decode("utf-8"))
    
    expected = {"name": "Alice", "age": 30}
    if parsed != expected:
        raise AssertionError(f"Expected {expected}, got {parsed}")


def test_json_serializer_nested_dataclass():
    """JSONSerializer should serialize nested dataclass."""
    serializer = JSONSerializer()
    user = UserWithAddress(
        name="Alice",
        address=Address(street="123 Main St", city="NYC", zip_code="10001")
    )
    
    result = serializer.serialize(user)
    parsed = json.loads(result.decode("utf-8"))
    
    expected = {
        "name": "Alice",
        "address": {"street": "123 Main St", "city": "NYC", "zip_code": "10001"}
    }
    if parsed != expected:
        raise AssertionError(f"Expected {expected}, got {parsed}")


def test_json_serializer_primitives():
    """JSONSerializer should serialize primitive values."""
    serializer = JSONSerializer()
    
    # String
    result = serializer.serialize("hello")
    if json.loads(result) != "hello":
        raise AssertionError("String serialization failed")
    
    # Integer
    result = serializer.serialize(42)
    if json.loads(result) != 42:
        raise AssertionError("Integer serialization failed")
    
    # Float
    result = serializer.serialize(3.14)
    if abs(json.loads(result) - 3.14) > 0.001:
        raise AssertionError("Float serialization failed")
    
    # Boolean
    result = serializer.serialize(True)
    if json.loads(result) is not True:
        raise AssertionError("Boolean serialization failed")
    
    # None
    result = serializer.serialize(None)
    if json.loads(result) is not None:
        raise AssertionError("None serialization failed")


def test_json_serializer_unicode():
    """JSONSerializer should handle unicode characters."""
    serializer = JSONSerializer()
    data = {"name": "日本語", "emoji": "🎉"}
    
    result = serializer.serialize(data)
    parsed = json.loads(result.decode("utf-8"))
    
    if parsed != data:
        raise AssertionError(f"Unicode handling failed: {parsed}")



# =============================================================================
# Unit Tests: JSONDeserializer
# =============================================================================

def test_json_deserializer_content_type():
    """JSONDeserializer should have content_type 'application/json'."""
    deserializer = JSONDeserializer()
    
    if deserializer.content_type != "application/json":
        errmsg = f"Expected content_type 'application/json', got '{deserializer.content_type}'"
        raise AssertionError(errmsg)


def test_json_deserializer_dict():
    """JSONDeserializer should deserialize JSON to dict."""
    deserializer = JSONDeserializer()
    data = b'{"name": "Alice", "age": 30}'
    
    result = deserializer.deserialize(data, dict)
    
    expected = {"name": "Alice", "age": 30}
    if result != expected:
        raise AssertionError(f"Expected {expected}, got {result}")


def test_json_deserializer_dataclass():
    """JSONDeserializer should deserialize JSON to dataclass."""
    deserializer = JSONDeserializer()
    data = b'{"name": "Alice", "age": 30}'
    
    result = deserializer.deserialize(data, SimpleUser)
    
    if not isinstance(result, SimpleUser):
        raise AssertionError(f"Expected SimpleUser, got {type(result)}")
    
    if result.name != "Alice":
        raise AssertionError(f"Expected name 'Alice', got '{result.name}'")
    
    if result.age != 30:
        raise AssertionError(f"Expected age 30, got {result.age}")


def test_json_deserializer_dataclass_with_defaults():
    """JSONDeserializer should use default values for missing fields."""
    deserializer = JSONDeserializer()
    data = b'{"name": "Alice"}'
    
    result = deserializer.deserialize(data, UserWithDefaults)
    
    if result.name != "Alice":
        raise AssertionError(f"Expected name 'Alice', got '{result.name}'")
    
    if result.age != 0:
        raise AssertionError(f"Expected default age 0, got {result.age}")
    
    if result.active is not True:
        raise AssertionError(f"Expected default active True, got {result.active}")


def test_json_deserializer_nested_dataclass():
    """JSONDeserializer should deserialize nested dataclass."""
    deserializer = JSONDeserializer()
    data = b'{"name": "Alice", "address": {"street": "123 Main St", "city": "NYC", "zip_code": "10001"}}'
    
    result = deserializer.deserialize(data, UserWithAddress)
    
    if not isinstance(result, UserWithAddress):
        raise AssertionError(f"Expected UserWithAddress, got {type(result)}")
    
    if not isinstance(result.address, Address):
        raise AssertionError(f"Expected Address, got {type(result.address)}")
    
    if result.address.city != "NYC":
        raise AssertionError(f"Expected city 'NYC', got '{result.address.city}'")


def test_json_deserializer_invalid_json():
    """JSONDeserializer should raise ValidationError on invalid JSON."""
    deserializer = JSONDeserializer()
    data = b'{"name": "Alice", invalid}'
    
    raised = False
    try:
        deserializer.deserialize(data, dict)
    except ValidationError as e:
        raised = True
        if "Invalid JSON" not in e.message:
            raise AssertionError(f"Expected 'Invalid JSON' in message, got '{e.message}'")
        if not e.field_errors:
            raise AssertionError("Expected field_errors to be populated")
        if e.field_errors[0].code != "parse_error":
            raise AssertionError(f"Expected code 'parse_error', got '{e.field_errors[0].code}'")
    
    if not raised:
        raise AssertionError("Expected ValidationError to be raised")


def test_json_deserializer_missing_required_field():
    """JSONDeserializer should raise ValidationError on missing required field."""
    deserializer = JSONDeserializer()
    data = b'{"name": "Alice"}'  # Missing 'age' field
    
    raised = False
    try:
        deserializer.deserialize(data, SimpleUser)
    except ValidationError as e:
        raised = True
        if not e.field_errors:
            raise AssertionError("Expected field_errors to be populated")
        
        # Find the error for 'age' field
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


def test_json_deserializer_type_mismatch_dict():
    """JSONDeserializer should raise ValidationError when expecting dict but got array."""
    deserializer = JSONDeserializer()
    data = b'["item1", "item2"]'  # Array instead of object
    
    raised = False
    try:
        deserializer.deserialize(data, dict)
    except ValidationError as e:
        raised = True
        if "Expected JSON object" not in e.message:
            raise AssertionError(f"Expected 'Expected JSON object' in message, got '{e.message}'")
    
    if not raised:
        raise AssertionError("Expected ValidationError to be raised")


def test_json_deserializer_unicode():
    """JSONDeserializer should handle unicode characters."""
    deserializer = JSONDeserializer()
    data = '{"name": "日本語"}'.encode("utf-8")
    
    result = deserializer.deserialize(data, dict)
    
    if result.get("name") != "日本語":
        raise AssertionError(f"Unicode handling failed: {result}")


# =============================================================================
# Unit Tests: SerializerRegistry
# =============================================================================

def test_serializer_registry_register_serializer():
    """SerializerRegistry should register and retrieve serializers."""
    registry = SerializerRegistry()
    serializer = JSONSerializer()
    
    registry.register_serializer(serializer)
    
    result = registry.get_serializer("application/json")
    if result is not serializer:
        raise AssertionError("Expected registered serializer")


def test_serializer_registry_register_deserializer():
    """SerializerRegistry should register and retrieve deserializers."""
    registry = SerializerRegistry()
    deserializer = JSONDeserializer()
    
    registry.register_deserializer(deserializer)
    
    result = registry.get_deserializer("application/json")
    if result is not deserializer:
        raise AssertionError("Expected registered deserializer")


def test_serializer_registry_get_unknown_type():
    """SerializerRegistry should return None for unknown content types."""
    registry = SerializerRegistry()
    
    result = registry.get_serializer("application/xml")
    if result is not None:
        raise AssertionError("Expected None for unknown type")
    
    result = registry.get_deserializer("application/xml")
    if result is not None:
        raise AssertionError("Expected None for unknown type")


def test_serializer_registry_content_type_with_params():
    """SerializerRegistry should handle content types with parameters."""
    registry = SerializerRegistry()
    registry.register_serializer(JSONSerializer())
    
    # Should match even with charset parameter
    result = registry.get_serializer("application/json; charset=utf-8")
    if result is None:
        raise AssertionError("Expected serializer for content type with params")


def test_serializer_registry_negotiate_exact_match():
    """negotiate_content_type should return exact match."""
    registry = create_default_registry()
    
    result = registry.negotiate_content_type("application/json")
    if result != "application/json":
        raise AssertionError(f"Expected 'application/json', got '{result}'")


def test_serializer_registry_negotiate_with_quality():
    """negotiate_content_type should respect quality values."""
    registry = create_default_registry()
    
    # JSON has higher quality
    result = registry.negotiate_content_type("text/html;q=0.5, application/json;q=1.0")
    if result != "application/json":
        raise AssertionError(f"Expected 'application/json', got '{result}'")


def test_serializer_registry_negotiate_wildcard():
    """negotiate_content_type should handle wildcard."""
    registry = create_default_registry()
    
    result = registry.negotiate_content_type("*/*")
    if result != "application/json":
        raise AssertionError(f"Expected 'application/json', got '{result}'")


def test_serializer_registry_negotiate_type_wildcard():
    """negotiate_content_type should handle type wildcard."""
    registry = create_default_registry()
    
    result = registry.negotiate_content_type("application/*")
    if result != "application/json":
        raise AssertionError(f"Expected 'application/json', got '{result}'")


def test_serializer_registry_negotiate_no_match():
    """negotiate_content_type should return None when no match."""
    registry = create_default_registry()
    
    result = registry.negotiate_content_type("text/xml")
    if result is not None:
        raise AssertionError(f"Expected None, got '{result}'")


def test_serializer_registry_negotiate_empty_header():
    """negotiate_content_type should return None for empty header."""
    registry = create_default_registry()
    
    result = registry.negotiate_content_type("")
    if result is not None:
        raise AssertionError(f"Expected None for empty header, got '{result}'")
    
    result = registry.negotiate_content_type("   ")
    if result is not None:
        raise AssertionError(f"Expected None for whitespace header, got '{result}'")


def test_serializer_registry_supported_types():
    """SerializerRegistry should report supported content types."""
    registry = create_default_registry()
    
    if "application/json" not in registry.supported_content_types:
        raise AssertionError("Expected 'application/json' in supported_content_types")
    
    if "application/json" not in registry.supported_request_types:
        raise AssertionError("Expected 'application/json' in supported_request_types")


def test_create_default_registry():
    """create_default_registry should return registry with JSON support."""
    registry = create_default_registry()
    
    serializer = registry.get_serializer("application/json")
    if serializer is None:
        raise AssertionError("Expected JSON serializer in default registry")
    
    deserializer = registry.get_deserializer("application/json")
    if deserializer is None:
        raise AssertionError("Expected JSON deserializer in default registry")



# =============================================================================
# Property-Based Tests
# =============================================================================

# Feature: rest-api-support, Property 2: Request Deserialization Round-Trip
# *For any* valid JSON request body and any schema (dataclass, Pydantic model,
# or dict), deserializing the JSON to a schema instance and then serializing
# it back to JSON SHALL produce equivalent JSON content.
# **Validates: Requirements 3.1, 3.2, 3.3, 3.4**

def test_property_2_json_serialization_round_trip_dict():
    """
        Property 2: Request Deserialization Round-Trip (dict schema)
        
        For any valid JSON dict, deserializing to dict and serializing back
        SHALL produce equivalent JSON content.
        
        **Validates: Requirements 3.1, 3.2, 3.3, 3.4**
    """
    serializer = JSONSerializer()
    deserializer = JSONDeserializer()
    
    # Run 100 iterations with random data
    for iteration in range(100):
        # Generate a random dict
        original_dict = generate_random_dict(max_depth=3, max_keys=5)
        
        # Serialize to JSON bytes
        json_bytes = serializer.serialize(original_dict)
        
        # Property: serialized result must be bytes
        if not isinstance(json_bytes, bytes):
            errmsg = f"Iteration {iteration}: serialize() should return bytes, got {type(json_bytes)}"
            raise AssertionError(errmsg)
        
        # Deserialize back to dict
        deserialized = deserializer.deserialize(json_bytes, dict)
        
        # Property: deserialized result must be a dict
        if not isinstance(deserialized, dict):
            errmsg = f"Iteration {iteration}: deserialize() should return dict, got {type(deserialized)}"
            raise AssertionError(errmsg)
        
        # Serialize the deserialized dict again
        json_bytes_2 = serializer.serialize(deserialized)
        
        # Property: second serialization must produce equivalent JSON
        # Parse both to compare (order-independent)
        parsed_1 = json.loads(json_bytes.decode("utf-8"))
        parsed_2 = json.loads(json_bytes_2.decode("utf-8"))
        
        if parsed_1 != parsed_2:
            errmsg = f"Iteration {iteration}: Round-trip produced different JSON"
            raise AssertionError(errmsg)
        
        # Property: deserialized dict must equal original
        # Note: We compare via JSON to handle float precision
        if json.dumps(deserialized, sort_keys=True) != json.dumps(original_dict, sort_keys=True):
            errmsg = f"Iteration {iteration}: Deserialized dict differs from original"
            raise AssertionError(errmsg)
    
    return


def test_property_2_json_serialization_round_trip_dataclass():
    """
        Property 2: Request Deserialization Round-Trip (dataclass schema)
        
        For any valid dataclass instance, serializing to JSON and deserializing
        back SHALL produce an equivalent dataclass instance.
        
        **Validates: Requirements 3.1, 3.2, 3.3, 3.4**
    """
    serializer = JSONSerializer()
    deserializer = JSONDeserializer()
    
    # Run 100 iterations with random data
    for iteration in range(100):
        # Generate a random SimpleUser
        original_user = generate_random_simple_user()
        
        # Serialize to JSON bytes
        json_bytes = serializer.serialize(original_user)
        
        # Property: serialized result must be bytes
        if not isinstance(json_bytes, bytes):
            errmsg = f"Iteration {iteration}: serialize() should return bytes, got {type(json_bytes)}"
            raise AssertionError(errmsg)
        
        # Deserialize back to SimpleUser
        deserialized = deserializer.deserialize(json_bytes, SimpleUser)
        
        # Property: deserialized result must be a SimpleUser
        if not isinstance(deserialized, SimpleUser):
            errmsg = f"Iteration {iteration}: deserialize() should return SimpleUser, got {type(deserialized)}"
            raise AssertionError(errmsg)
        
        # Property: deserialized user must have same name
        if deserialized.name != original_user.name:
            errmsg = f"Iteration {iteration}: name mismatch: '{deserialized.name}' != '{original_user.name}'"
            raise AssertionError(errmsg)
        
        # Property: deserialized user must have same age
        if deserialized.age != original_user.age:
            errmsg = f"Iteration {iteration}: age mismatch: {deserialized.age} != {original_user.age}"
            raise AssertionError(errmsg)
        
        # Serialize the deserialized user again
        json_bytes_2 = serializer.serialize(deserialized)
        
        # Property: second serialization must produce equivalent JSON
        parsed_1 = json.loads(json_bytes.decode("utf-8"))
        parsed_2 = json.loads(json_bytes_2.decode("utf-8"))
        
        if parsed_1 != parsed_2:
            errmsg = f"Iteration {iteration}: Round-trip produced different JSON"
            raise AssertionError(errmsg)
    
    return


def test_property_2_json_serialization_round_trip_dataclass_with_defaults():
    """
        Property 2: Request Deserialization Round-Trip (dataclass with defaults)
        
        For any valid dataclass with default values, serializing to JSON and
        deserializing back SHALL produce an equivalent dataclass instance.
        
        **Validates: Requirements 3.1, 3.2, 3.3, 3.4**
    """
    serializer = JSONSerializer()
    deserializer = JSONDeserializer()
    
    # Run 100 iterations with random data
    for iteration in range(100):
        # Generate a random UserWithDefaults
        original_user = generate_random_user_with_defaults()
        
        # Serialize to JSON bytes
        json_bytes = serializer.serialize(original_user)
        
        # Deserialize back to UserWithDefaults
        deserialized = deserializer.deserialize(json_bytes, UserWithDefaults)
        
        # Property: deserialized result must be a UserWithDefaults
        if not isinstance(deserialized, UserWithDefaults):
            errmsg = f"Iteration {iteration}: deserialize() should return UserWithDefaults"
            raise AssertionError(errmsg)
        
        # Property: all fields must match
        if deserialized.name != original_user.name:
            errmsg = f"Iteration {iteration}: name mismatch"
            raise AssertionError(errmsg)
        
        if deserialized.age != original_user.age:
            errmsg = f"Iteration {iteration}: age mismatch"
            raise AssertionError(errmsg)
        
        if deserialized.active != original_user.active:
            errmsg = f"Iteration {iteration}: active mismatch"
            raise AssertionError(errmsg)
    
    return


def test_property_2_json_serialization_round_trip_list():
    """
        Property 2: Request Deserialization Round-Trip (list)
        
        For any valid list of dicts, serializing to JSON and deserializing
        back SHALL produce an equivalent list.
        
        **Validates: Requirements 3.1, 3.2, 3.3, 3.4**
    """
    serializer = JSONSerializer()
    
    # Run 100 iterations with random data
    for iteration in range(100):
        # Generate a random list of dicts
        num_items = random.randint(0, 10)
        original_list = [generate_random_dict(max_depth=2, max_keys=3) for _ in range(num_items)]
        
        # Serialize to JSON bytes
        json_bytes = serializer.serialize(original_list)
        
        # Property: serialized result must be bytes
        if not isinstance(json_bytes, bytes):
            errmsg = f"Iteration {iteration}: serialize() should return bytes"
            raise AssertionError(errmsg)
        
        # Parse JSON to verify structure
        parsed = json.loads(json_bytes.decode("utf-8"))
        
        # Property: parsed result must be a list
        if not isinstance(parsed, list):
            errmsg = f"Iteration {iteration}: parsed result should be list, got {type(parsed)}"
            raise AssertionError(errmsg)
        
        # Property: list length must match
        if len(parsed) != len(original_list):
            errmsg = f"Iteration {iteration}: list length mismatch: {len(parsed)} != {len(original_list)}"
            raise AssertionError(errmsg)
        
        # Property: each item must match (via JSON comparison for float precision)
        for idx, (parsed_item, original_item) in enumerate(zip(parsed, original_list)):
            if json.dumps(parsed_item, sort_keys=True) != json.dumps(original_item, sort_keys=True):
                errmsg = f"Iteration {iteration}: list item {idx} mismatch"
                raise AssertionError(errmsg)
    
    return
