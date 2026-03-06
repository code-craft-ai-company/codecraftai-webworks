"""
    Property-based test for Schema Conversion Round-Trip.

    **Validates: Requirements 2.1, 2.2, 2.4**

    Property 1: Schema Conversion Round-Trip
    For any Python dataclass or Pydantic model, converting to JSON Schema and
    then validating a conforming JSON object against that schema SHALL accept
    all valid instances of the original type.

    This test exercises the property across a diverse set of dataclasses with
    varying field types: primitives, nested dataclasses, optional fields, lists,
    dicts, and unions. For each type, we convert to JSON Schema, verify the
    schema structure, create a conforming instance, and verify the instance
    conforms to the generated schema.
"""

import dataclasses

from dataclasses import dataclass, field
from datetime import date, datetime, time
from decimal import Decimal
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from automojo.webworks.openapi.schemaconverter import SchemaConverter


# =============================================================================
# Helper: Schema Validation
# =============================================================================

def _validate_instance_against_schema(instance: dict, schema: dict, all_schemas: dict, path: str = "root") -> List[str]:
    """
        Validates a JSON-like dictionary against a JSON Schema definition.

        Checks that required fields are present, types match, and nested
        structures conform. Returns a list of violation messages.

        :param instance: The JSON-like dictionary to validate.
        :param schema: The JSON Schema to validate against.
        :param all_schemas: All component schemas for resolving $ref.
        :param path: The current path for error reporting.

        :returns: A list of violation message strings (empty if valid).
    """
    violations = []

    # Resolve $ref, preserving nullable from the referring schema
    if "$ref" in schema:
        ref_path = schema["$ref"]
        ref_nullable = schema.get("nullable", False)
        schema_name = ref_path.split("/")[-1]
        if schema_name not in all_schemas:
            violations.append(f"{path}: unresolved $ref '{ref_path}'")
            return violations
        schema = dict(all_schemas[schema_name])
        if ref_nullable:
            schema["nullable"] = True

    # Handle oneOf
    if "oneOf" in schema:
        matched = False
        for sub_schema in schema["oneOf"]:
            sub_violations = _validate_instance_against_schema(
                instance=instance, schema=sub_schema,
                all_schemas=all_schemas, path=path
            )
            if len(sub_violations) == 0:
                matched = True
                break
        if not matched:
            violations.append(f"{path}: value does not match any oneOf schema")
        return violations


    # Handle nullable schemas - if nullable is true and instance is None, accept it
    is_nullable = schema.get("nullable", False)
    if is_nullable and instance is None:
        return violations

    schema_type = schema.get("type")

    # Validate type
    if schema_type == "object":
        if not isinstance(instance, dict):
            violations.append(f"{path}: expected object, got {type(instance).__name__}")
            return violations

        # Check required fields
        required = schema.get("required", [])
        for req_field in required:
            if req_field not in instance:
                violations.append(f"{path}: missing required field '{req_field}'")

        # Validate properties
        properties = schema.get("properties", {})
        for prop_name, prop_schema in properties.items():
            if prop_name in instance:
                prop_violations = _validate_instance_against_schema(
                    instance=instance[prop_name], schema=prop_schema,
                    all_schemas=all_schemas, path=f"{path}.{prop_name}"
                )
                violations.extend(prop_violations)

    elif schema_type == "array":
        if not isinstance(instance, list):
            violations.append(f"{path}: expected array, got {type(instance).__name__}")
            return violations

        items_schema = schema.get("items", {})
        for idx, item in enumerate(instance):
            item_violations = _validate_instance_against_schema(
                instance=item, schema=items_schema,
                all_schemas=all_schemas, path=f"{path}[{idx}]"
            )
            violations.extend(item_violations)

    elif schema_type == "string":
        if not isinstance(instance, str):
            violations.append(f"{path}: expected string, got {type(instance).__name__}")

    elif schema_type == "integer":
        if not isinstance(instance, int) or isinstance(instance, bool):
            violations.append(f"{path}: expected integer, got {type(instance).__name__}")

    elif schema_type == "number":
        if not isinstance(instance, (int, float)) or isinstance(instance, bool):
            violations.append(f"{path}: expected number, got {type(instance).__name__}")

    elif schema_type == "boolean":
        if not isinstance(instance, bool):
            violations.append(f"{path}: expected boolean, got {type(instance).__name__}")

    elif schema_type == "null":
        if instance is not None:
            violations.append(f"{path}: expected null, got {type(instance).__name__}")

    return violations


def _validate_schema_structure(schema: dict, all_schemas: dict, path: str = "root") -> List[str]:
    """
        Validates that a JSON Schema dictionary has a valid structure.

        Checks for required keys like 'type' or '$ref' or 'oneOf', and
        validates nested schema structures recursively.

        :param schema: The JSON Schema dictionary to validate.
        :param all_schemas: All component schemas for resolving $ref.
        :param path: The current path for error reporting.

        :returns: A list of structural violation messages (empty if valid).
    """
    violations = []

    # A valid schema must have type, $ref, or oneOf
    has_type = "type" in schema
    has_ref = "$ref" in schema
    has_one_of = "oneOf" in schema
    has_nullable = "nullable" in schema

    if not has_type and not has_ref and not has_one_of:
        # Empty schema is valid for Any type
        if len(schema) > 0 and not has_nullable:
            violations.append(f"{path}: schema has no 'type', '$ref', or 'oneOf'")
        return violations

    if has_ref:
        ref_path = schema["$ref"]
        schema_name = ref_path.split("/")[-1]
        if schema_name not in all_schemas:
            violations.append(f"{path}: unresolved $ref '{ref_path}'")
        return violations

    if has_one_of:
        for idx, sub_schema in enumerate(schema["oneOf"]):
            sub_violations = _validate_schema_structure(
                schema=sub_schema, all_schemas=all_schemas,
                path=f"{path}.oneOf[{idx}]"
            )
            violations.extend(sub_violations)
        return violations

    schema_type = schema.get("type")

    if schema_type == "object":
        properties = schema.get("properties", {})
        for prop_name, prop_schema in properties.items():
            sub_violations = _validate_schema_structure(
                schema=prop_schema, all_schemas=all_schemas,
                path=f"{path}.properties.{prop_name}"
            )
            violations.extend(sub_violations)

        additional = schema.get("additionalProperties")
        if isinstance(additional, dict):
            sub_violations = _validate_schema_structure(
                schema=additional, all_schemas=all_schemas,
                path=f"{path}.additionalProperties"
            )
            violations.extend(sub_violations)

    elif schema_type == "array":
        items_schema = schema.get("items")
        if items_schema is None:
            violations.append(f"{path}: array schema missing 'items'")
        else:
            sub_violations = _validate_schema_structure(
                schema=items_schema, all_schemas=all_schemas,
                path=f"{path}.items"
            )
            violations.extend(sub_violations)

    return violations


# =============================================================================
# Test Dataclasses - Diverse Types for Property Testing
# =============================================================================

@dataclass
class PrimitivesOnly:
    """
        A dataclass with only primitive fields.
    """
    name: str
    age: int
    score: float
    active: bool


@dataclass
class WithOptionalFields:
    """
        A dataclass with optional fields.
    """
    title: str
    subtitle: Optional[str] = None
    count: Optional[int] = None


@dataclass
class WithListFields:
    """
        A dataclass with list-typed fields.
    """
    tags: List[str]
    scores: List[int]


@dataclass
class WithDictFields:
    """
        A dataclass with dict-typed fields.
    """
    metadata: Dict[str, str]
    counts: Dict[str, int]


@dataclass
class WithUnionFields:
    """
        A dataclass with union-typed fields.
    """
    value: Union[str, int]
    label: Union[str, float, bool]


@dataclass
class InnerDetail:
    """
        A simple inner dataclass for nesting tests.
    """
    key: str
    value: int


@dataclass
class WithNestedDataclass:
    """
        A dataclass with a nested dataclass field.
    """
    name: str
    detail: InnerDetail


@dataclass
class WithDefaultValues:
    """
        A dataclass with various default values.
    """
    name: str
    enabled: bool = True
    priority: int = 5
    label: str = "default"


@dataclass
class WithDefaultFactory:
    """
        A dataclass with default_factory fields.
    """
    name: str
    items: List[str] = field(default_factory=list)
    config: Dict[str, str] = field(default_factory=dict)


@dataclass
class WithFieldMetadata:
    """
        A dataclass with field metadata descriptions.
    """
    name: str = field(metadata={"description": "The entity name"})
    count: int = field(default=0, metadata={"description": "Item count"})


@dataclass
class WithDateTimeFields:
    """
        A dataclass with date/time typed fields.
    """
    created_at: datetime
    birth_date: date
    alarm_time: time


@dataclass
class WithSpecialTypes:
    """
        A dataclass with UUID, Decimal, bytes, and Any fields.
    """
    identifier: UUID
    amount: Decimal
    payload: bytes
    extra: Any


@dataclass
class WithOptionalNested:
    """
        A dataclass with an optional nested dataclass.
    """
    name: str
    detail: Optional[InnerDetail] = None


@dataclass
class WithListOfNested:
    """
        A dataclass with a list of nested dataclasses.
    """
    name: str
    details: List[InnerDetail]


@dataclass
class WithComplexCombination:
    """
        A dataclass combining multiple complex type patterns.
    """
    name: str
    tags: List[str]
    metadata: Dict[str, Any]
    detail: Optional[InnerDetail] = None
    priority: int = 0


# =============================================================================
# Conforming Instance Generators
# =============================================================================

# Each entry maps a dataclass type to a list of conforming JSON-like dicts.
# Multiple instances per type exercise different valid value combinations.

CONFORMING_INSTANCES = {
    PrimitivesOnly: [
        {"name": "Alice", "age": 30, "score": 95.5, "active": True},
        {"name": "", "age": 0, "score": 0.0, "active": False},
        {"name": "Bob", "age": 999, "score": -1.5, "active": True},
    ],
    WithOptionalFields: [
        {"title": "Hello"},
        {"title": "Hello", "subtitle": "World", "count": 42},
        {"title": "Test", "subtitle": None, "count": None},
    ],
    WithListFields: [
        {"tags": ["a", "b", "c"], "scores": [1, 2, 3]},
        {"tags": [], "scores": []},
        {"tags": ["single"], "scores": [100]},
    ],
    WithDictFields: [
        {"metadata": {"key": "value"}, "counts": {"a": 1}},
        {"metadata": {}, "counts": {}},
        {"metadata": {"x": "y", "z": "w"}, "counts": {"total": 99}},
    ],
    WithUnionFields: [
        {"value": "text", "label": "name"},
        {"value": 42, "label": 3.14},
        {"value": "hello", "label": True},
    ],
    WithNestedDataclass: [
        {"name": "Parent", "detail": {"key": "k1", "value": 10}},
        {"name": "", "detail": {"key": "", "value": 0}},
    ],
    WithDefaultValues: [
        {"name": "Item"},
        {"name": "Item", "enabled": False, "priority": 1, "label": "custom"},
        {"name": "Other", "enabled": True, "priority": 5, "label": "default"},
    ],
    WithDefaultFactory: [
        {"name": "Item"},
        {"name": "Item", "items": ["a", "b"], "config": {"k": "v"}},
        {"name": "Empty", "items": [], "config": {}},
    ],
    WithFieldMetadata: [
        {"name": "Entity"},
        {"name": "Entity", "count": 10},
        {"name": "Other", "count": 0},
    ],
    WithDateTimeFields: [
        {"created_at": "2024-01-15T10:30:00", "birth_date": "1990-05-20", "alarm_time": "07:30:00"},
        {"created_at": "2000-12-31T23:59:59", "birth_date": "2024-06-01", "alarm_time": "00:00:00"},
    ],
    WithSpecialTypes: [
        {"identifier": "550e8400-e29b-41d4-a716-446655440000", "amount": "99.99", "payload": "binary-data", "extra": "anything"},
        {"identifier": "00000000-0000-0000-0000-000000000000", "amount": "0", "payload": "", "extra": 42},
    ],
    WithOptionalNested: [
        {"name": "WithDetail", "detail": {"key": "k", "value": 1}},
        {"name": "WithoutDetail", "detail": None},
        {"name": "Simple"},
    ],
    WithListOfNested: [
        {"name": "Parent", "details": [{"key": "a", "value": 1}, {"key": "b", "value": 2}]},
        {"name": "Empty", "details": []},
    ],
    WithComplexCombination: [
        {"name": "Complex", "tags": ["a"], "metadata": {"k": "v"}, "detail": {"key": "x", "value": 5}, "priority": 1},
        {"name": "Minimal", "tags": [], "metadata": {}},
        {"name": "NoDetail", "tags": ["x", "y"], "metadata": {"a": 1}, "detail": None, "priority": 0},
    ],
}


# =============================================================================
# Property Test
# =============================================================================

def test_property_schema_conversion_roundtrip():
    """
        **Validates: Requirements 2.1, 2.2, 2.4**

        Property 1: Schema Conversion Round-Trip

        For any Python dataclass, converting to JSON Schema and then validating
        a conforming JSON object against that schema SHALL accept all valid
        instances of the original type.

        This test iterates over a diverse set of dataclass types, converts each
        to JSON Schema, validates the schema structure, and then validates
        multiple conforming instances against the generated schema.
    """
    all_test_types = list(CONFORMING_INSTANCES.keys())
    total_validations = 0
    total_types = len(all_test_types)

    for dc_type in all_test_types:
        # Create a fresh converter for each type to avoid cross-contamination
        # of the schema cache between unrelated types
        converter = SchemaConverter()

        # Step 1: Convert the dataclass to JSON Schema
        schema_result = converter.convert(python_type=dc_type)
        all_schemas = converter.get_all_schemas()

        # Step 2: Resolve the schema (it may be a $ref)
        resolved_schema = schema_result
        if "$ref" in schema_result:
            ref_name = schema_result["$ref"].split("/")[-1]
            if ref_name not in all_schemas:
                errmsg = (
                    f"Schema conversion for {dc_type.__name__} produced "
                    f"$ref '{schema_result['$ref']}' but schema not found in cache"
                )
                raise AssertionError(errmsg)
            resolved_schema = all_schemas[ref_name]

        # Step 3: Validate the schema structure
        structure_violations = _validate_schema_structure(
            schema=resolved_schema, all_schemas=all_schemas,
            path=dc_type.__name__
        )
        if len(structure_violations) > 0:
            errmsg = (
                f"Schema structure validation failed for {dc_type.__name__}:\n"
                + "\n".join(f"  - {v}" for v in structure_violations)
            )
            raise AssertionError(errmsg)

        # Step 4: Verify the schema has correct top-level type
        if resolved_schema.get("type") != "object":
            errmsg = (
                f"Schema for {dc_type.__name__} should have type 'object', "
                f"got '{resolved_schema.get('type')}'"
            )
            raise AssertionError(errmsg)

        # Step 5: Verify properties exist
        properties = resolved_schema.get("properties")
        if properties is None:
            errmsg = f"Schema for {dc_type.__name__} is missing 'properties'"
            raise AssertionError(errmsg)

        # Step 6: Verify required fields match dataclass fields without defaults
        dc_fields = dataclasses.fields(dc_type)
        expected_required = []
        for f in dc_fields:
            has_default = f.default is not dataclasses.MISSING
            has_factory = f.default_factory is not dataclasses.MISSING
            if not has_default and not has_factory:
                expected_required.append(f.name)

        actual_required = resolved_schema.get("required", [])
        if sorted(actual_required) != sorted(expected_required):
            errmsg = (
                f"Schema for {dc_type.__name__} has required={actual_required}, "
                f"expected={expected_required}"
            )
            raise AssertionError(errmsg)

        # Step 7: Verify all dataclass fields appear in properties
        for f in dc_fields:
            if f.name not in properties:
                errmsg = (
                    f"Schema for {dc_type.__name__} is missing property '{f.name}'"
                )
                raise AssertionError(errmsg)

        # Step 8: Validate conforming instances against the schema
        instances = CONFORMING_INSTANCES[dc_type]
        for idx, instance in enumerate(instances):
            instance_violations = _validate_instance_against_schema(
                instance=instance, schema=resolved_schema,
                all_schemas=all_schemas,
                path=f"{dc_type.__name__}[{idx}]"
            )
            if len(instance_violations) > 0:
                errmsg = (
                    f"Conforming instance {idx} for {dc_type.__name__} "
                    f"failed validation:\n"
                    + "\n".join(f"  - {v}" for v in instance_violations)
                )
                raise AssertionError(errmsg)
            total_validations += 1

    # Verify we tested a meaningful number of types and instances
    if total_types < 10:
        errmsg = f"Expected at least 10 test types, got {total_types}"
        raise AssertionError(errmsg)

    if total_validations < 25:
        errmsg = f"Expected at least 25 total validations, got {total_validations}"
        raise AssertionError(errmsg)

    return
