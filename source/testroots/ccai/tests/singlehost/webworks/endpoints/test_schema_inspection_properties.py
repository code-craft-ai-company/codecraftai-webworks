"""
.. module:: test_schema_inspection_properties
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Property-based tests for schema inspection.

.. moduleauthor:: Code Craft AI LLC

This module contains property-based tests for the RestEndpoint class,
validating Property 12: Schema Inspection across many generated inputs.
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []

import dataclasses
import random
import string
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ccai.webworks.endpoints import (
    EndpointRegistry,
    RestEndpoint,
)


# =============================================================================
# Helper Functions for Generating Random Test Data
# =============================================================================

def generate_random_string(min_len: int = 3, max_len: int = 10) -> str:
    """Generate a random alphanumeric string."""
    length = random.randint(min_len, max_len)
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))


def generate_random_leaf() -> str:
    """Generate a random URL leaf segment."""
    return generate_random_string(3, 12)


def _clear_registry():
    """Helper to clear the registry before tests."""
    EndpointRegistry.clear()


def _make_handler(iteration: int, suffix: str = ""):
    """Create a unique handler function for a given iteration."""
    def handler():
        return iteration
    handler.__name__ = f"handler_{suffix}_{iteration}"
    handler.__qualname__ = f"handler_{suffix}_{iteration}"
    return handler


# =============================================================================
# Dataclass Generators
# =============================================================================

# Basic Python types that can be used in dataclass fields
BASIC_FIELD_TYPES = [str, int, float, bool]


def _generate_dataclass_fields() -> List[tuple]:
    """
        Generate a random list of (name, type, has_default) tuples for
        building a dataclass at runtime.
    """
    num_fields = random.randint(1, 6)
    fields = []
    for idx in range(num_fields):
        name = f"field_{generate_random_string(3, 6)}_{idx}"
        ftype = random.choice(BASIC_FIELD_TYPES)
        has_default = random.choice([True, False])
        fields.append((name, ftype, has_default))
    return fields


def _build_dataclass(name: str, field_specs: List[tuple]) -> type:
    """
        Build a dataclass type dynamically from field specifications.

        :param name: The class name for the dataclass.
        :param field_specs: List of (field_name, field_type, has_default) tuples.

        :returns: A new dataclass type.
    """
    dc_fields = []
    # Put required fields first, then optional fields (dataclass ordering rule)
    required = [(n, t) for n, t, has_default in field_specs if not has_default]
    optional = [(n, t) for n, t, has_default in field_specs if has_default]

    annotations = {}
    namespace = {}

    for fname, ftype in required:
        annotations[fname] = ftype

    for fname, ftype in optional:
        annotations[fname] = ftype
        # Provide a default value appropriate for the type
        defaults = {str: "", int: 0, float: 0.0, bool: False}
        namespace[fname] = defaults.get(ftype, None)

    namespace["__annotations__"] = annotations
    cls = type(name, (), namespace)
    return dataclass(cls)


def _build_pydantic_like_model(name: str, field_specs: List[tuple]) -> type:
    """
        Build a class that mimics a Pydantic model by providing a
        model_json_schema classmethod. This avoids a hard dependency
        on Pydantic while testing the inspection path.

        :param name: The class name.
        :param field_specs: List of (field_name, field_type, has_default) tuples.

        :returns: A class with a model_json_schema classmethod.
    """
    type_map = {
        str: "string",
        int: "integer",
        float: "number",
        bool: "boolean",
    }

    properties = {}
    required = []
    for fname, ftype, has_default in field_specs:
        properties[fname] = {"type": type_map.get(ftype, "string")}
        if not has_default:
            required.append(fname)

    schema = {
        "type": "object",
        "title": name,
        "properties": properties,
    }
    if required:
        schema["required"] = required

    # Capture schema in closure
    captured_schema = dict(schema)

    class PydanticLike:
        pass

    PydanticLike.__name__ = name
    PydanticLike.__qualname__ = name

    @classmethod
    def model_json_schema(cls):
        return dict(captured_schema)

    PydanticLike.model_json_schema = model_json_schema

    return PydanticLike


# =============================================================================
# Property 12: Schema Inspection
# Feature: endpoint-abstractions, Property 12: Schema Inspection
# Validates: Requirements 8.7
# =============================================================================

def test_property_dataclass_request_schema_captured_in_extras():
    """
        Property 12: Schema Inspection - Dataclass Request Schema

        *For any* attach_at call with a request_schema that is a dataclass,
        the decorator SHALL inspect __dataclass_fields__ to capture
        JSON-schema fragments in the descriptor under extras["rest"].

        **Feature: endpoint-abstractions, Property 12: Schema Inspection**
        **Validates: Requirements 8.7**
    """
    for iteration in range(100):
        _clear_registry()

        handler = _make_handler(iteration, "dc_req")
        leaf = f"dc_req_{iteration}_{generate_random_leaf()}"
        field_specs = _generate_dataclass_fields()
        dc_name = f"ReqSchema_{iteration}"
        schema_cls = _build_dataclass(dc_name, field_specs)

        RestEndpoint.attach_at(leaf=leaf, request_schema=schema_cls)(handler)

        descriptors = EndpointRegistry.collect()

        if len(descriptors) != 1:
            raise AssertionError(
                f"Iteration {iteration}: Expected 1 descriptor, got {len(descriptors)}"
            )

        desc = descriptors[0]

        if "rest" not in desc.extras:
            raise AssertionError(
                f"Iteration {iteration}: extras['rest'] missing from descriptor"
            )

        rest = desc.extras["rest"]

        if "request_schema" not in rest:
            raise AssertionError(
                f"Iteration {iteration}: extras['rest']['request_schema'] missing. "
                f"rest keys: {list(rest.keys())}"
            )

        captured = rest["request_schema"]

        if captured.get("type") != "object":
            raise AssertionError(
                f"Iteration {iteration}: Expected schema type 'object', "
                f"got {captured.get('type')!r}"
            )

        if "properties" not in captured:
            raise AssertionError(
                f"Iteration {iteration}: Schema missing 'properties' key"
            )

        # Verify every dataclass field appears in the captured schema
        for fname, ftype, _ in field_specs:
            if fname not in captured["properties"]:
                raise AssertionError(
                    f"Iteration {iteration}: Dataclass field '{fname}' not found "
                    f"in captured schema properties. "
                    f"Properties: {list(captured['properties'].keys())}"
                )

    return


def test_property_dataclass_response_schema_captured_in_extras():
    """
        Property 12: Schema Inspection - Dataclass Response Schema

        *For any* attach_at call with a response_schema that is a dataclass,
        the decorator SHALL inspect __dataclass_fields__ to capture
        JSON-schema fragments in the descriptor under extras["rest"].

        **Feature: endpoint-abstractions, Property 12: Schema Inspection**
        **Validates: Requirements 8.7**
    """
    for iteration in range(100):
        _clear_registry()

        handler = _make_handler(iteration, "dc_resp")
        leaf = f"dc_resp_{iteration}_{generate_random_leaf()}"
        field_specs = _generate_dataclass_fields()
        dc_name = f"RespSchema_{iteration}"
        schema_cls = _build_dataclass(dc_name, field_specs)

        RestEndpoint.attach_at(leaf=leaf, response_schema=schema_cls)(handler)

        descriptors = EndpointRegistry.collect()
        desc = descriptors[0]

        if "rest" not in desc.extras:
            raise AssertionError(
                f"Iteration {iteration}: extras['rest'] missing from descriptor"
            )

        rest = desc.extras["rest"]

        if "response_schema" not in rest:
            raise AssertionError(
                f"Iteration {iteration}: extras['rest']['response_schema'] missing"
            )

        captured = rest["response_schema"]

        if captured.get("type") != "object":
            raise AssertionError(
                f"Iteration {iteration}: Expected schema type 'object', "
                f"got {captured.get('type')!r}"
            )

        for fname, ftype, _ in field_specs:
            if fname not in captured["properties"]:
                raise AssertionError(
                    f"Iteration {iteration}: Dataclass field '{fname}' not found "
                    f"in captured response schema properties"
                )

    return


def test_property_pydantic_model_schema_captured_via_model_json_schema():
    """
        Property 12: Schema Inspection - Pydantic Model

        *For any* attach_at call with a request_schema or response_schema
        that has a model_json_schema method (Pydantic model), the decorator
        SHALL call model_json_schema() to capture JSON-schema fragments.

        **Feature: endpoint-abstractions, Property 12: Schema Inspection**
        **Validates: Requirements 8.7**
    """
    for iteration in range(100):
        _clear_registry()

        handler = _make_handler(iteration, "pydantic")
        leaf = f"pydantic_{iteration}_{generate_random_leaf()}"
        field_specs = _generate_dataclass_fields()
        model_name = f"PydModel_{iteration}"
        model_cls = _build_pydantic_like_model(model_name, field_specs)

        # Use as request_schema
        RestEndpoint.attach_at(leaf=leaf, request_schema=model_cls)(handler)

        descriptors = EndpointRegistry.collect()
        desc = descriptors[0]

        rest = desc.extras.get("rest", {})

        if "request_schema" not in rest:
            raise AssertionError(
                f"Iteration {iteration}: Pydantic model schema not captured "
                f"in extras['rest']['request_schema']"
            )

        captured = rest["request_schema"]
        expected = model_cls.model_json_schema()

        if captured != expected:
            raise AssertionError(
                f"Iteration {iteration}: Captured schema does not match "
                f"model_json_schema() output.\n"
                f"Expected: {expected}\n"
                f"Got: {captured}"
            )

    return


def test_property_both_request_and_response_schemas_captured():
    """
        Property 12: Schema Inspection - Both Schemas

        *For any* attach_at call with both request_schema and response_schema,
        both SHALL be inspected and captured independently in
        extras["rest"]["request_schema"] and extras["rest"]["response_schema"].

        **Feature: endpoint-abstractions, Property 12: Schema Inspection**
        **Validates: Requirements 8.7**
    """
    for iteration in range(100):
        _clear_registry()

        handler = _make_handler(iteration, "both")
        leaf = f"both_{iteration}_{generate_random_leaf()}"

        req_fields = _generate_dataclass_fields()
        resp_fields = _generate_dataclass_fields()

        req_cls = _build_dataclass(f"BothReq_{iteration}", req_fields)
        resp_cls = _build_dataclass(f"BothResp_{iteration}", resp_fields)

        RestEndpoint.attach_at(
            leaf=leaf,
            request_schema=req_cls,
            response_schema=resp_cls
        )(handler)

        descriptors = EndpointRegistry.collect()
        desc = descriptors[0]

        rest = desc.extras.get("rest", {})

        if "request_schema" not in rest:
            raise AssertionError(
                f"Iteration {iteration}: request_schema missing from rest extras"
            )

        if "response_schema" not in rest:
            raise AssertionError(
                f"Iteration {iteration}: response_schema missing from rest extras"
            )

        # Verify request schema has all fields
        req_captured = rest["request_schema"]
        for fname, ftype, _ in req_fields:
            if fname not in req_captured.get("properties", {}):
                raise AssertionError(
                    f"Iteration {iteration}: Request field '{fname}' missing "
                    f"from captured request schema"
                )

        # Verify response schema has all fields
        resp_captured = rest["response_schema"]
        for fname, ftype, _ in resp_fields:
            if fname not in resp_captured.get("properties", {}):
                raise AssertionError(
                    f"Iteration {iteration}: Response field '{fname}' missing "
                    f"from captured response schema"
                )

    return


def test_property_dataclass_required_fields_marked_in_schema():
    """
        Property 12: Schema Inspection - Required Fields

        *For any* dataclass schema with fields that have no default value,
        those fields SHALL appear in the "required" list of the captured
        JSON schema.

        **Feature: endpoint-abstractions, Property 12: Schema Inspection**
        **Validates: Requirements 8.7**
    """
    for iteration in range(100):
        _clear_registry()

        handler = _make_handler(iteration, "required")
        leaf = f"required_{iteration}_{generate_random_leaf()}"

        # Ensure at least one required and one optional field
        field_specs = _generate_dataclass_fields()
        has_required = any(not hd for _, _, hd in field_specs)
        has_optional = any(hd for _, _, hd in field_specs)

        if not has_required:
            # Add a required field
            field_specs.append((f"req_{iteration}", str, False))
        if not has_optional:
            # Add an optional field
            field_specs.append((f"opt_{iteration}", int, True))

        dc_name = f"ReqFields_{iteration}"
        schema_cls = _build_dataclass(dc_name, field_specs)

        RestEndpoint.attach_at(leaf=leaf, request_schema=schema_cls)(handler)

        descriptors = EndpointRegistry.collect()
        desc = descriptors[0]

        captured = desc.extras.get("rest", {}).get("request_schema", {})
        captured_required = captured.get("required", [])

        expected_required = [
            fname for fname, _, has_default in field_specs if not has_default
        ]

        for fname in expected_required:
            if fname not in captured_required:
                raise AssertionError(
                    f"Iteration {iteration}: Required field '{fname}' not in "
                    f"schema required list. Got: {captured_required}"
                )

        expected_optional = [
            fname for fname, _, has_default in field_specs if has_default
        ]

        for fname in expected_optional:
            if fname in captured_required:
                raise AssertionError(
                    f"Iteration {iteration}: Optional field '{fname}' should "
                    f"not be in schema required list. Got: {captured_required}"
                )

    return
