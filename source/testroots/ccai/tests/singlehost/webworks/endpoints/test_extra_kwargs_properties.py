"""
.. module:: test_extra_kwargs_properties
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Property-based tests for extra kwargs preservation.

.. moduleauthor:: Code Craft AI LLC

This module contains property-based tests for the Endpoint class,
validating Property 4: Extra Kwargs Preservation across many generated
inputs.
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []

import random
import string
from typing import Any, Dict, List

from ccai.webworks.endpoints import (
    Endpoint,
    EndpointRegistry,
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


def _generate_random_extras(min_keys: int = 1, max_keys: int = 5) -> Dict[str, Any]:
    """Generate a random dictionary of extra kwargs with varied value types."""
    num_keys = random.randint(min_keys, max_keys)
    extras = {}
    for _ in range(num_keys):
        key = generate_random_string(4, 10)
        value_type = random.choice(["string", "int", "float", "bool", "list", "dict", "none"])
        if value_type == "string":
            extras[key] = generate_random_string(3, 15)
        elif value_type == "int":
            extras[key] = random.randint(-1000, 1000)
        elif value_type == "float":
            extras[key] = round(random.uniform(-100.0, 100.0), 4)
        elif value_type == "bool":
            extras[key] = random.choice([True, False])
        elif value_type == "list":
            extras[key] = [generate_random_string(2, 6) for _ in range(random.randint(0, 4))]
        elif value_type == "dict":
            extras[key] = {generate_random_string(3, 6): generate_random_string(3, 6)
                          for _ in range(random.randint(1, 3))}
        elif value_type == "none":
            extras[key] = None
    return extras


# =============================================================================
# Property 4: Extra Kwargs Preservation
# Feature: endpoint-abstractions, Property 4: Extra Kwargs Preservation
# Validates: Requirements 2.7, 5.4
# =============================================================================

def test_property_extra_kwargs_appear_verbatim_in_extras():
    """
        Property 4: Extra Kwargs Preservation - Verbatim Storage

        *For any* additional kwargs passed to attach_at beyond the standard
        parameters, those kwargs SHALL appear verbatim in the descriptor's
        extras field.

        **Feature: endpoint-abstractions, Property 4: Extra Kwargs Preservation**
        **Validates: Requirements 2.7, 5.4**
    """
    for iteration in range(100):
        _clear_registry()

        handler = _make_handler(iteration, "verbatim")
        leaf = f"verbatim_{iteration}_{generate_random_leaf()}"
        extras = _generate_random_extras()

        Endpoint.attach_at(leaf=leaf, **extras)(handler)

        descriptors = EndpointRegistry.collect()

        if len(descriptors) != 1:
            raise AssertionError(
                f"Iteration {iteration}: Expected 1 descriptor, got {len(descriptors)}"
            )

        desc = descriptors[0]

        for key, value in extras.items():
            if key not in desc.extras:
                raise AssertionError(
                    f"Iteration {iteration}: Extra key '{key}' not found in "
                    f"descriptor extras. extras keys: {list(desc.extras.keys())}"
                )

            if desc.extras[key] != value:
                raise AssertionError(
                    f"Iteration {iteration}: Extra key '{key}' value mismatch. "
                    f"Expected {value!r}, got {desc.extras[key]!r}"
                )

    return


def test_property_unknown_keys_preserved_for_downstream():
    """
        Property 4: Extra Kwargs Preservation - Unknown Key Preservation

        *For any* set of unknown keys passed to attach_at, those keys
        SHALL be preserved in the descriptor's extras field for downstream
        consumers, regardless of key name or value type.

        **Feature: endpoint-abstractions, Property 4: Extra Kwargs Preservation**
        **Validates: Requirements 2.7, 5.4**
    """
    for iteration in range(100):
        _clear_registry()

        handler = _make_handler(iteration, "unknown")
        leaf = f"unknown_{iteration}_{generate_random_leaf()}"

        # Generate extras with deliberately unusual key names
        num_keys = random.randint(1, 6)
        extras = {}
        for idx in range(num_keys):
            key = f"custom_{generate_random_string(3, 8)}_{idx}"
            extras[key] = {
                "nested_str": generate_random_string(),
                "nested_int": random.randint(0, 999),
                "nested_list": [random.randint(0, 10) for _ in range(random.randint(0, 3))],
            }

        Endpoint.attach_at(leaf=leaf, **extras)(handler)

        descriptors = EndpointRegistry.collect()
        desc = descriptors[0]

        for key, value in extras.items():
            if key not in desc.extras:
                raise AssertionError(
                    f"Iteration {iteration}: Unknown key '{key}' was not preserved "
                    f"in descriptor extras"
                )

            if desc.extras[key] != value:
                raise AssertionError(
                    f"Iteration {iteration}: Unknown key '{key}' value was altered. "
                    f"Expected {value!r}, got {desc.extras[key]!r}"
                )

    return


def test_property_extras_do_not_interfere_with_standard_params():
    """
        Property 4: Extra Kwargs Preservation - No Interference

        *For any* attach_at call with both standard parameters and extra
        kwargs, the extra kwargs SHALL be stored in extras without
        interfering with the standard descriptor fields.

        **Feature: endpoint-abstractions, Property 4: Extra Kwargs Preservation**
        **Validates: Requirements 2.7, 5.4**
    """
    all_methods = ["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"]

    for iteration in range(100):
        _clear_registry()

        handler = _make_handler(iteration, "nointerf")
        leaf = f"nointerf_{iteration}_{generate_random_leaf()}"
        methods = random.sample(all_methods, random.randint(1, len(all_methods)))
        tags = [generate_random_string(3, 8) for _ in range(random.randint(0, 3))]
        version = generate_random_string(2, 5)
        extras = _generate_random_extras()

        Endpoint.attach_at(
            leaf=leaf,
            methods=methods,
            tags=tags,
            version=version,
            **extras
        )(handler)

        descriptors = EndpointRegistry.collect()
        desc = descriptors[0]

        # Verify standard fields are unaffected by extras
        if desc.leaf != leaf:
            raise AssertionError(
                f"Iteration {iteration}: leaf mismatch. "
                f"Expected '{leaf}', got '{desc.leaf}'"
            )

        if desc.methods != methods:
            raise AssertionError(
                f"Iteration {iteration}: methods mismatch. "
                f"Expected {methods}, got {desc.methods}"
            )

        if desc.tags != tags:
            raise AssertionError(
                f"Iteration {iteration}: tags mismatch. "
                f"Expected {tags}, got {desc.tags}"
            )

        if desc.version != version:
            raise AssertionError(
                f"Iteration {iteration}: version mismatch. "
                f"Expected '{version}', got '{desc.version}'"
            )

        # Verify extras are still present
        for key, value in extras.items():
            if key not in desc.extras:
                raise AssertionError(
                    f"Iteration {iteration}: Extra key '{key}' missing from extras "
                    f"when standard params also provided"
                )

            if desc.extras[key] != value:
                raise AssertionError(
                    f"Iteration {iteration}: Extra key '{key}' value mismatch. "
                    f"Expected {value!r}, got {desc.extras[key]!r}"
                )

    return


def test_property_empty_extras_yields_no_spurious_keys():
    """
        Property 4: Extra Kwargs Preservation - Empty Extras

        *For any* attach_at call with no extra kwargs, the descriptor's
        extras field SHALL not contain spurious keys (only framework-
        managed keys like 'serializers' or 'rest' may appear).

        **Feature: endpoint-abstractions, Property 4: Extra Kwargs Preservation**
        **Validates: Requirements 2.7, 5.4**
    """
    # Known framework-managed keys that may appear in extras
    FRAMEWORK_KEYS = {"serializers", "rest"}

    for iteration in range(100):
        _clear_registry()

        handler = _make_handler(iteration, "empty")
        leaf = f"empty_{iteration}_{generate_random_leaf()}"

        Endpoint.attach_at(leaf=leaf)(handler)

        descriptors = EndpointRegistry.collect()
        desc = descriptors[0]

        unexpected_keys = set(desc.extras.keys()) - FRAMEWORK_KEYS
        if unexpected_keys:
            raise AssertionError(
                f"Iteration {iteration}: Descriptor extras contains unexpected "
                f"keys when no extras were passed: {unexpected_keys}. "
                f"Full extras: {desc.extras}"
            )

    return


def test_property_extras_identity_preserved_for_mutable_values():
    """
        Property 4: Extra Kwargs Preservation - Mutable Value Identity

        *For any* extra kwargs with mutable values (lists, dicts) passed
        to attach_at, the values stored in the descriptor's extras SHALL
        be equal to the original values.

        **Feature: endpoint-abstractions, Property 4: Extra Kwargs Preservation**
        **Validates: Requirements 2.7, 5.4**
    """
    for iteration in range(100):
        _clear_registry()

        handler = _make_handler(iteration, "mutable")
        leaf = f"mutable_{iteration}_{generate_random_leaf()}"

        # Generate extras with only mutable values
        extras = {}
        for idx in range(random.randint(1, 4)):
            key = f"mutable_{generate_random_string(3, 6)}_{idx}"
            if random.choice([True, False]):
                extras[key] = [generate_random_string(2, 5) for _ in range(random.randint(1, 5))]
            else:
                extras[key] = {
                    generate_random_string(3, 6): random.randint(0, 100)
                    for _ in range(random.randint(1, 4))
                }

        # Snapshot the original values
        original_values = {k: (list(v) if isinstance(v, list) else dict(v))
                          for k, v in extras.items()}

        Endpoint.attach_at(leaf=leaf, **extras)(handler)

        descriptors = EndpointRegistry.collect()
        desc = descriptors[0]

        for key, original in original_values.items():
            if key not in desc.extras:
                raise AssertionError(
                    f"Iteration {iteration}: Mutable extra key '{key}' not found "
                    f"in descriptor extras"
                )

            if desc.extras[key] != original:
                raise AssertionError(
                    f"Iteration {iteration}: Mutable extra key '{key}' value "
                    f"mismatch. Expected {original!r}, got {desc.extras[key]!r}"
                )

    return
