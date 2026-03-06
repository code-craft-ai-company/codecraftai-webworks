"""
    Tests for the Schema_Converter class in the OpenAPI schema converter module.

    This module contains unit tests covering primitive type conversion, dataclass
    conversion, complex type handling (List, Dict, Optional, Union), $ref generation
    for nested dataclasses, circular reference handling, and schema name generation.
"""

import dataclasses

from dataclasses import dataclass, field
from datetime import date, datetime, time
from decimal import Decimal
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from automojo.webworks.openapi.schemaconverter import (
    PYTHON_TO_JSON_SCHEMA,
    SchemaConverter,
)


# =============================================================================
# Test Dataclasses
# =============================================================================

@dataclass
class SimpleItem:
    """
        A simple dataclass for testing basic conversion.
    """
    name: str
    count: int


@dataclass
class ItemWithDefaults:
    """
        A dataclass with default values for testing default handling.
    """
    name: str
    active: bool = True
    score: float = 0.0


@dataclass
class ItemWithDescription:
    """
        A dataclass with field metadata descriptions.
    """
    name: str = field(metadata={"description": "The name of the item"})
    value: int = field(default=0, metadata={"description": "The numeric value"})


@dataclass
class NestedAddress:
    """
        A dataclass representing an address, used for nested type testing.
    """
    street: str
    city: str


@dataclass
class NestedPerson:
    """
        A dataclass with a nested dataclass field.
    """
    name: str
    address: NestedAddress


@dataclass
class TreeNode:
    """
        A self-referencing dataclass for circular reference testing.
    """
    value: str
    children: Optional[List["TreeNode"]] = None


@dataclass
class ItemWithFactory:
    """
        A dataclass with a default_factory field.
    """
    name: str
    tags: List[str] = field(default_factory=list)


# =============================================================================
# Unit Tests for PYTHON_TO_JSON_SCHEMA Mapping
# =============================================================================

def test_python_to_json_schema_contains_str():
    """
        Test that the mapping contains an entry for str.
    """
    if str not in PYTHON_TO_JSON_SCHEMA:
        errmsg = "Expected str to be in PYTHON_TO_JSON_SCHEMA"
        raise AssertionError(errmsg)

    expected = {"type": "string"}
    actual = PYTHON_TO_JSON_SCHEMA[str]

    if actual != expected:
        errmsg = f"Expected {expected}, got {actual}"
        raise AssertionError(errmsg)

    return


def test_python_to_json_schema_contains_int():
    """
        Test that the mapping contains an entry for int.
    """
    expected = {"type": "integer"}
    actual = PYTHON_TO_JSON_SCHEMA[int]

    if actual != expected:
        errmsg = f"Expected {expected}, got {actual}"
        raise AssertionError(errmsg)

    return


def test_python_to_json_schema_contains_float():
    """
        Test that the mapping contains an entry for float.
    """
    expected = {"type": "number"}
    actual = PYTHON_TO_JSON_SCHEMA[float]

    if actual != expected:
        errmsg = f"Expected {expected}, got {actual}"
        raise AssertionError(errmsg)

    return


def test_python_to_json_schema_contains_bool():
    """
        Test that the mapping contains an entry for bool.
    """
    expected = {"type": "boolean"}
    actual = PYTHON_TO_JSON_SCHEMA[bool]

    if actual != expected:
        errmsg = f"Expected {expected}, got {actual}"
        raise AssertionError(errmsg)

    return


def test_python_to_json_schema_contains_bytes():
    """
        Test that bytes maps to string with binary format.
    """
    expected = {"type": "string", "format": "binary"}
    actual = PYTHON_TO_JSON_SCHEMA[bytes]

    if actual != expected:
        errmsg = f"Expected {expected}, got {actual}"
        raise AssertionError(errmsg)

    return


def test_python_to_json_schema_contains_datetime():
    """
        Test that datetime maps to string with date-time format.
    """
    expected = {"type": "string", "format": "date-time"}
    actual = PYTHON_TO_JSON_SCHEMA[datetime]

    if actual != expected:
        errmsg = f"Expected {expected}, got {actual}"
        raise AssertionError(errmsg)

    return


def test_python_to_json_schema_contains_date():
    """
        Test that date maps to string with date format.
    """
    expected = {"type": "string", "format": "date"}
    actual = PYTHON_TO_JSON_SCHEMA[date]

    if actual != expected:
        errmsg = f"Expected {expected}, got {actual}"
        raise AssertionError(errmsg)

    return


def test_python_to_json_schema_contains_time():
    """
        Test that time maps to string with time format.
    """
    expected = {"type": "string", "format": "time"}
    actual = PYTHON_TO_JSON_SCHEMA[time]

    if actual != expected:
        errmsg = f"Expected {expected}, got {actual}"
        raise AssertionError(errmsg)

    return


def test_python_to_json_schema_contains_uuid():
    """
        Test that UUID maps to string with uuid format.
    """
    expected = {"type": "string", "format": "uuid"}
    actual = PYTHON_TO_JSON_SCHEMA[UUID]

    if actual != expected:
        errmsg = f"Expected {expected}, got {actual}"
        raise AssertionError(errmsg)

    return


def test_python_to_json_schema_contains_decimal():
    """
        Test that Decimal maps to string with decimal format.
    """
    expected = {"type": "string", "format": "decimal"}
    actual = PYTHON_TO_JSON_SCHEMA[Decimal]

    if actual != expected:
        errmsg = f"Expected {expected}, got {actual}"
        raise AssertionError(errmsg)

    return


def test_python_to_json_schema_contains_any():
    """
        Test that Any maps to an empty schema.
    """
    expected = {}
    actual = PYTHON_TO_JSON_SCHEMA[Any]

    if actual != expected:
        errmsg = f"Expected {expected}, got {actual}"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for Primitive Type Conversion
# =============================================================================

def test_convert_str():
    """
        Test converting str type to JSON Schema.
    """
    converter = SchemaConverter()
    result = converter.convert(python_type=str)

    expected = {"type": "string"}
    if result != expected:
        errmsg = f"Expected {expected}, got {result}"
        raise AssertionError(errmsg)

    return


def test_convert_int():
    """
        Test converting int type to JSON Schema.
    """
    converter = SchemaConverter()
    result = converter.convert(python_type=int)

    expected = {"type": "integer"}
    if result != expected:
        errmsg = f"Expected {expected}, got {result}"
        raise AssertionError(errmsg)

    return


def test_convert_float():
    """
        Test converting float type to JSON Schema.
    """
    converter = SchemaConverter()
    result = converter.convert(python_type=float)

    expected = {"type": "number"}
    if result != expected:
        errmsg = f"Expected {expected}, got {result}"
        raise AssertionError(errmsg)

    return


def test_convert_bool():
    """
        Test converting bool type to JSON Schema.
    """
    converter = SchemaConverter()
    result = converter.convert(python_type=bool)

    expected = {"type": "boolean"}
    if result != expected:
        errmsg = f"Expected {expected}, got {result}"
        raise AssertionError(errmsg)

    return


def test_convert_datetime():
    """
        Test converting datetime type to JSON Schema.
    """
    converter = SchemaConverter()
    result = converter.convert(python_type=datetime)

    expected = {"type": "string", "format": "date-time"}
    if result != expected:
        errmsg = f"Expected {expected}, got {result}"
        raise AssertionError(errmsg)

    return


def test_convert_uuid():
    """
        Test converting UUID type to JSON Schema.
    """
    converter = SchemaConverter()
    result = converter.convert(python_type=UUID)

    expected = {"type": "string", "format": "uuid"}
    if result != expected:
        errmsg = f"Expected {expected}, got {result}"
        raise AssertionError(errmsg)

    return


def test_convert_any():
    """
        Test converting Any type to JSON Schema.
    """
    converter = SchemaConverter()
    result = converter.convert(python_type=Any)

    expected = {}
    if result != expected:
        errmsg = f"Expected {expected}, got {result}"
        raise AssertionError(errmsg)

    return


def test_convert_none_type():
    """
        Test converting NoneType to JSON Schema.
    """
    converter = SchemaConverter()
    result = converter.convert(python_type=type(None))

    expected = {"type": "null"}
    if result != expected:
        errmsg = f"Expected {expected}, got {result}"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for Dataclass Conversion
# =============================================================================

def test_convert_simple_dataclass():
    """
        Test converting a simple dataclass with required fields.
    """
    converter = SchemaConverter()
    result = converter.convert(python_type=SimpleItem)

    if "$ref" not in result:
        errmsg = f"Expected a $ref in result, got {result}"
        raise AssertionError(errmsg)

    expected_ref = "#/components/schemas/SimpleItem"
    if result["$ref"] != expected_ref:
        errmsg = f"Expected $ref '{expected_ref}', got {result['$ref']!r}"
        raise AssertionError(errmsg)

    schemas = converter.get_all_schemas()
    if "SimpleItem" not in schemas:
        errmsg = f"Expected 'SimpleItem' in schemas, got keys: {list(schemas.keys())}"
        raise AssertionError(errmsg)

    schema = schemas["SimpleItem"]
    if schema["type"] != "object":
        errmsg = f"Expected type 'object', got {schema['type']!r}"
        raise AssertionError(errmsg)

    if "name" not in schema["properties"]:
        errmsg = f"Expected 'name' in properties, got {list(schema['properties'].keys())}"
        raise AssertionError(errmsg)

    if "count" not in schema["properties"]:
        errmsg = f"Expected 'count' in properties, got {list(schema['properties'].keys())}"
        raise AssertionError(errmsg)

    if "required" not in schema:
        errmsg = "Expected 'required' key in schema"
        raise AssertionError(errmsg)

    if "name" not in schema["required"]:
        errmsg = f"Expected 'name' in required, got {schema['required']}"
        raise AssertionError(errmsg)

    if "count" not in schema["required"]:
        errmsg = f"Expected 'count' in required, got {schema['required']}"
        raise AssertionError(errmsg)

    return


def test_convert_dataclass_with_defaults():
    """
        Test converting a dataclass that has fields with default values.
    """
    converter = SchemaConverter()
    converter.convert(python_type=ItemWithDefaults)

    schemas = converter.get_all_schemas()
    schema = schemas["ItemWithDefaults"]

    # 'name' has no default, so it should be required
    if "required" not in schema:
        errmsg = "Expected 'required' key in schema"
        raise AssertionError(errmsg)

    if "name" not in schema["required"]:
        errmsg = f"Expected 'name' in required, got {schema['required']}"
        raise AssertionError(errmsg)

    # 'active' and 'score' have defaults, so they should NOT be required
    if "active" in schema["required"]:
        errmsg = "'active' should not be in required since it has a default"
        raise AssertionError(errmsg)

    if "score" in schema["required"]:
        errmsg = "'score' should not be in required since it has a default"
        raise AssertionError(errmsg)

    # Check default values are preserved
    active_schema = schema["properties"]["active"]
    if active_schema.get("default") is not True:
        errmsg = f"Expected default True for 'active', got {active_schema.get('default')!r}"
        raise AssertionError(errmsg)

    score_schema = schema["properties"]["score"]
    if score_schema.get("default") != 0.0:
        errmsg = f"Expected default 0.0 for 'score', got {score_schema.get('default')!r}"
        raise AssertionError(errmsg)

    return


def test_convert_dataclass_with_descriptions():
    """
        Test converting a dataclass that has field metadata descriptions.
    """
    converter = SchemaConverter()
    converter.convert(python_type=ItemWithDescription)

    schemas = converter.get_all_schemas()
    schema = schemas["ItemWithDescription"]

    name_schema = schema["properties"]["name"]
    if name_schema.get("description") != "The name of the item":
        errmsg = f"Expected description 'The name of the item', got {name_schema.get('description')!r}"
        raise AssertionError(errmsg)

    value_schema = schema["properties"]["value"]
    if value_schema.get("description") != "The numeric value":
        errmsg = f"Expected description 'The numeric value', got {value_schema.get('description')!r}"
        raise AssertionError(errmsg)

    return


def test_convert_dataclass_with_default_factory():
    """
        Test converting a dataclass that has a default_factory field.
    """
    converter = SchemaConverter()
    converter.convert(python_type=ItemWithFactory)

    schemas = converter.get_all_schemas()
    schema = schemas["ItemWithFactory"]

    # 'name' is required, 'tags' has a default_factory so it is not required
    if "name" not in schema["required"]:
        errmsg = f"Expected 'name' in required, got {schema['required']}"
        raise AssertionError(errmsg)

    if "tags" in schema.get("required", []):
        errmsg = "'tags' should not be in required since it has a default_factory"
        raise AssertionError(errmsg)

    return


def test_convert_nested_dataclass():
    """
        Test converting a dataclass with a nested dataclass field.
    """
    converter = SchemaConverter()
    result = converter.convert(python_type=NestedPerson)

    if "$ref" not in result:
        errmsg = f"Expected a $ref in result, got {result}"
        raise AssertionError(errmsg)

    schemas = converter.get_all_schemas()

    if "NestedPerson" not in schemas:
        errmsg = f"Expected 'NestedPerson' in schemas, got keys: {list(schemas.keys())}"
        raise AssertionError(errmsg)

    if "NestedAddress" not in schemas:
        errmsg = f"Expected 'NestedAddress' in schemas, got keys: {list(schemas.keys())}"
        raise AssertionError(errmsg)

    person_schema = schemas["NestedPerson"]
    address_prop = person_schema["properties"]["address"]

    expected_ref = "#/components/schemas/NestedAddress"
    if address_prop.get("$ref") != expected_ref:
        errmsg = f"Expected address $ref '{expected_ref}', got {address_prop}"
        raise AssertionError(errmsg)

    return


def test_convert_dataclass_returns_ref_on_second_call():
    """
        Test that converting the same dataclass twice returns a $ref both times
        and does not duplicate the schema in the cache.
    """
    converter = SchemaConverter()

    result1 = converter.convert(python_type=SimpleItem)
    result2 = converter.convert(python_type=SimpleItem)

    if result1 != result2:
        errmsg = f"Expected same result on second call, got {result1} and {result2}"
        raise AssertionError(errmsg)

    schemas = converter.get_all_schemas()
    schema_count = len([k for k in schemas.keys() if k == "SimpleItem"])

    if schema_count != 1:
        errmsg = f"Expected exactly 1 SimpleItem schema, found {schema_count}"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for Complex Type Handling
# =============================================================================

def test_convert_list_of_str():
    """
        Test converting List[str] to JSON Schema array.
    """
    converter = SchemaConverter()
    result = converter.convert(python_type=List[str])

    expected = {
        "type": "array",
        "items": {"type": "string"},
    }

    if result != expected:
        errmsg = f"Expected {expected}, got {result}"
        raise AssertionError(errmsg)

    return


def test_convert_list_of_int():
    """
        Test converting List[int] to JSON Schema array.
    """
    converter = SchemaConverter()
    result = converter.convert(python_type=List[int])

    expected = {
        "type": "array",
        "items": {"type": "integer"},
    }

    if result != expected:
        errmsg = f"Expected {expected}, got {result}"
        raise AssertionError(errmsg)

    return


def test_convert_list_of_dataclass():
    """
        Test converting List[SimpleItem] to JSON Schema array with $ref items.
    """
    converter = SchemaConverter()
    result = converter.convert(python_type=List[SimpleItem])

    if result["type"] != "array":
        errmsg = f"Expected type 'array', got {result['type']!r}"
        raise AssertionError(errmsg)

    items = result["items"]
    if "$ref" not in items:
        errmsg = f"Expected $ref in items, got {items}"
        raise AssertionError(errmsg)

    if items["$ref"] != "#/components/schemas/SimpleItem":
        errmsg = f"Expected $ref '#/components/schemas/SimpleItem', got {items['$ref']!r}"
        raise AssertionError(errmsg)

    return


def test_convert_dict_str_to_int():
    """
        Test converting Dict[str, int] to JSON Schema object.
    """
    converter = SchemaConverter()
    result = converter.convert(python_type=Dict[str, int])

    expected = {
        "type": "object",
        "additionalProperties": {"type": "integer"},
    }

    if result != expected:
        errmsg = f"Expected {expected}, got {result}"
        raise AssertionError(errmsg)

    return


def test_convert_dict_str_to_any():
    """
        Test converting Dict[str, Any] to JSON Schema object.
    """
    converter = SchemaConverter()
    result = converter.convert(python_type=Dict[str, Any])

    expected = {
        "type": "object",
        "additionalProperties": {},
    }

    if result != expected:
        errmsg = f"Expected {expected}, got {result}"
        raise AssertionError(errmsg)

    return


def test_convert_optional_str():
    """
        Test converting Optional[str] to nullable JSON Schema.
    """
    converter = SchemaConverter()
    result = converter.convert(python_type=Optional[str])

    if result.get("type") != "string":
        errmsg = f"Expected type 'string', got {result.get('type')!r}"
        raise AssertionError(errmsg)

    if result.get("nullable") is not True:
        errmsg = f"Expected nullable True, got {result.get('nullable')!r}"
        raise AssertionError(errmsg)

    return


def test_convert_optional_int():
    """
        Test converting Optional[int] to nullable JSON Schema.
    """
    converter = SchemaConverter()
    result = converter.convert(python_type=Optional[int])

    if result.get("type") != "integer":
        errmsg = f"Expected type 'integer', got {result.get('type')!r}"
        raise AssertionError(errmsg)

    if result.get("nullable") is not True:
        errmsg = f"Expected nullable True, got {result.get('nullable')!r}"
        raise AssertionError(errmsg)

    return


def test_convert_optional_dataclass():
    """
        Test converting Optional[SimpleItem] to nullable $ref.
    """
    converter = SchemaConverter()
    result = converter.convert(python_type=Optional[SimpleItem])

    if result.get("nullable") is not True:
        errmsg = f"Expected nullable True, got {result.get('nullable')!r}"
        raise AssertionError(errmsg)

    if "$ref" not in result:
        errmsg = f"Expected $ref in result, got {result}"
        raise AssertionError(errmsg)

    return


def test_convert_union_str_int():
    """
        Test converting Union[str, int] to JSON Schema oneOf.
    """
    converter = SchemaConverter()
    result = converter.convert(python_type=Union[str, int])

    if "oneOf" not in result:
        errmsg = f"Expected 'oneOf' in result, got {result}"
        raise AssertionError(errmsg)

    one_of = result["oneOf"]
    if len(one_of) != 2:
        errmsg = f"Expected 2 items in oneOf, got {len(one_of)}"
        raise AssertionError(errmsg)

    types_found = [s.get("type") for s in one_of]
    if "string" not in types_found:
        errmsg = f"Expected 'string' in oneOf types, got {types_found}"
        raise AssertionError(errmsg)

    if "integer" not in types_found:
        errmsg = f"Expected 'integer' in oneOf types, got {types_found}"
        raise AssertionError(errmsg)

    return


def test_convert_union_str_int_none():
    """
        Test converting Union[str, int, None] to nullable oneOf.
    """
    converter = SchemaConverter()
    result = converter.convert(python_type=Union[str, int, None])

    if "oneOf" not in result:
        errmsg = f"Expected 'oneOf' in result, got {result}"
        raise AssertionError(errmsg)

    if result.get("nullable") is not True:
        errmsg = f"Expected nullable True, got {result.get('nullable')!r}"
        raise AssertionError(errmsg)

    one_of = result["oneOf"]
    if len(one_of) != 2:
        errmsg = f"Expected 2 items in oneOf (excluding None), got {len(one_of)}"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for $ref Handling and Schema Cache
# =============================================================================

def test_get_ref_for_dataclass():
    """
        Test that get_ref returns the correct $ref path for a dataclass.
    """
    converter = SchemaConverter()
    ref_path = converter.get_ref(python_type=SimpleItem)

    expected = "#/components/schemas/SimpleItem"
    if ref_path != expected:
        errmsg = f"Expected ref path '{expected}', got {ref_path!r}"
        raise AssertionError(errmsg)

    return


def test_get_all_schemas_returns_cached_schemas():
    """
        Test that get_all_schemas returns all schemas that have been converted.
    """
    converter = SchemaConverter()
    converter.convert(python_type=SimpleItem)
    converter.convert(python_type=NestedPerson)

    schemas = converter.get_all_schemas()

    if "SimpleItem" not in schemas:
        errmsg = f"Expected 'SimpleItem' in schemas, got keys: {list(schemas.keys())}"
        raise AssertionError(errmsg)

    if "NestedPerson" not in schemas:
        errmsg = f"Expected 'NestedPerson' in schemas, got keys: {list(schemas.keys())}"
        raise AssertionError(errmsg)

    if "NestedAddress" not in schemas:
        errmsg = f"Expected 'NestedAddress' in schemas, got keys: {list(schemas.keys())}"
        raise AssertionError(errmsg)

    return


def test_get_all_schemas_returns_copy():
    """
        Test that get_all_schemas returns a copy, not the internal cache.
    """
    converter = SchemaConverter()
    converter.convert(python_type=SimpleItem)

    schemas1 = converter.get_all_schemas()
    schemas2 = converter.get_all_schemas()

    if schemas1 is schemas2:
        errmsg = "Expected get_all_schemas to return a new dict each time"
        raise AssertionError(errmsg)

    return


def test_schema_name_uses_class_name():
    """
        Test that schema names are based on the class __name__.
    """
    converter = SchemaConverter()
    converter.convert(python_type=SimpleItem)

    schemas = converter.get_all_schemas()

    if "SimpleItem" not in schemas:
        errmsg = f"Expected schema name 'SimpleItem', got keys: {list(schemas.keys())}"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for Circular Reference Handling
# =============================================================================

def test_circular_reference_does_not_recurse_infinitely():
    """
        Test that a self-referencing dataclass does not cause infinite recursion.
    """
    converter = SchemaConverter()
    result = converter.convert(python_type=TreeNode)

    if "$ref" not in result:
        errmsg = f"Expected $ref in result, got {result}"
        raise AssertionError(errmsg)

    schemas = converter.get_all_schemas()

    if "TreeNode" not in schemas:
        errmsg = f"Expected 'TreeNode' in schemas, got keys: {list(schemas.keys())}"
        raise AssertionError(errmsg)

    return


def test_circular_reference_schema_has_properties():
    """
        Test that the schema for a self-referencing dataclass has correct properties.
    """
    converter = SchemaConverter()
    converter.convert(python_type=TreeNode)

    schemas = converter.get_all_schemas()
    schema = schemas["TreeNode"]

    if "value" not in schema["properties"]:
        errmsg = f"Expected 'value' in properties, got {list(schema['properties'].keys())}"
        raise AssertionError(errmsg)

    if "children" not in schema["properties"]:
        errmsg = f"Expected 'children' in properties, got {list(schema['properties'].keys())}"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for Unknown Type Fallback
# =============================================================================

def test_convert_unknown_type_returns_object():
    """
        Test that an unknown type falls back to a generic object schema.
    """

    class UnknownClass:
        """
            A plain class that is not a dataclass or Pydantic model.
        """
        pass

    converter = SchemaConverter()
    result = converter.convert(python_type=UnknownClass)

    expected = {"type": "object"}
    if result != expected:
        errmsg = f"Expected {expected}, got {result}"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for Converter Initialization
# =============================================================================

def test_converter_initial_state():
    """
        Test that a new Schema_Converter has empty caches.
    """
    converter = SchemaConverter()

    schemas = converter.get_all_schemas()
    if len(schemas) != 0:
        errmsg = f"Expected empty schemas, got {schemas}"
        raise AssertionError(errmsg)

    return
