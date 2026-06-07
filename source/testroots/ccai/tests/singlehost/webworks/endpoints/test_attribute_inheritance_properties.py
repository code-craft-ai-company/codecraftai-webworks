"""
.. module:: test_attribute_inheritance_properties
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Property-based tests for attribute inheritance and override.

.. moduleauthor:: Code Craft AI LLC

This module contains property-based tests for the Endpoint class,
validating Property 2: Attribute Inheritance and Override across many
generated inputs.
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []

import random
import string
from typing import Any, Dict, List, Optional

from ccai.webworks.endpoints import (
    AccessPolicy,
    Doc,
    Endpoint,
    EndpointRegistry,
    RateLimit,
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


def generate_random_methods() -> List[str]:
    """Generate a random list of HTTP methods."""
    all_methods = ["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"]
    count = random.randint(1, len(all_methods))
    return random.sample(all_methods, count)


def generate_random_tags() -> List[str]:
    """Generate a random list of tags."""
    count = random.randint(1, 4)
    return [generate_random_string(3, 8) for _ in range(count)]


def generate_random_access_policy() -> AccessPolicy:
    """Generate a random AccessPolicy (never None)."""
    roles = [generate_random_string(3, 8) for _ in range(random.randint(1, 3))]
    scopes = [generate_random_string(3, 8) for _ in range(random.randint(1, 3))]
    return AccessPolicy(roles=roles, scopes=scopes, require_auth=random.choice([True, False]))


def generate_random_rate_limit() -> RateLimit:
    """Generate a random RateLimit (never None)."""
    return RateLimit(requests=random.randint(1, 1000), window=random.randint(1, 3600))


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


def _create_subclass(iteration: int, attrs: Dict[str, Any]) -> type:
    """Create a unique Endpoint subclass with the given class attributes."""
    return type(f"TestEndpoint_{iteration}", (Endpoint,), dict(attrs))



# =============================================================================
# Property 2: Attribute Inheritance and Override
# Feature: endpoint-abstractions, Property 2: Attribute Inheritance and Override
# Validates: Requirements 1.3, 1.4, 1.6, 2.3, 2.8
# =============================================================================

def test_property_explicit_kwargs_override_class_attributes():
    """
        Property 2: Attribute Inheritance and Override - Explicit Override

        *For any* Endpoint subclass with class-level attributes and any
        attach_at call with explicit kwargs, the explicit kwargs SHALL
        override the class attributes in the resulting descriptor.

        **Feature: endpoint-abstractions, Property 2: Attribute Inheritance and Override**
        **Validates: Requirements 1.3, 2.3, 2.8**
    """
    for iteration in range(100):
        _clear_registry()

        # Generate class-level defaults
        class_methods = generate_random_methods()
        class_tags = generate_random_tags()
        class_version = generate_random_string(2, 5)
        class_policy = generate_random_access_policy()
        class_rate_limit = generate_random_rate_limit()

        SubEndpoint = _create_subclass(iteration, {
            "methods": class_methods,
            "tags": class_tags,
            "version": class_version,
            "access_policy": class_policy,
            "rate_limit": class_rate_limit,
        })

        # Generate explicit overrides (all different from class defaults)
        override_methods = generate_random_methods()
        override_tags = generate_random_tags()
        override_version = generate_random_string(2, 5) + "_override"
        override_policy = generate_random_access_policy()
        override_rate_limit = generate_random_rate_limit()

        handler = _make_handler(iteration, "override")
        leaf = f"override_{iteration}_{generate_random_leaf()}"

        SubEndpoint.attach_at(
            leaf=leaf,
            methods=override_methods,
            tags=override_tags,
            version=override_version,
            access_policy=override_policy,
            rate_limit=override_rate_limit,
        )(handler)

        # Retrieve the descriptor from the registry
        descriptors = EndpointRegistry.collect()
        if len(descriptors) != 1:
            raise AssertionError(
                f"Iteration {iteration}: Expected 1 descriptor, got {len(descriptors)}"
            )

        desc = descriptors[0]

        # Verify explicit kwargs override class attributes
        if desc.methods != override_methods:
            raise AssertionError(
                f"Iteration {iteration}: methods should be override {override_methods}, "
                f"got {desc.methods}"
            )

        if desc.tags != override_tags:
            raise AssertionError(
                f"Iteration {iteration}: tags should be override {override_tags}, "
                f"got {desc.tags}"
            )

        if desc.version != override_version:
            raise AssertionError(
                f"Iteration {iteration}: version should be override '{override_version}', "
                f"got '{desc.version}'"
            )

        if desc.constraints.access_policy is not override_policy:
            raise AssertionError(
                f"Iteration {iteration}: access_policy should be the override policy"
            )

        if desc.constraints.rate_limit is not override_rate_limit:
            raise AssertionError(
                f"Iteration {iteration}: rate_limit should be the override rate_limit"
            )

    return


def test_property_missing_kwargs_fallback_to_class_defaults():
    """
        Property 2: Attribute Inheritance and Override - Fallback to Defaults

        *For any* Endpoint subclass with class-level attributes and any
        attach_at call without certain kwargs, the missing kwargs SHALL
        fall back to class defaults in the resulting descriptor.

        **Feature: endpoint-abstractions, Property 2: Attribute Inheritance and Override**
        **Validates: Requirements 1.4, 1.6**
    """
    for iteration in range(100):
        _clear_registry()

        # Generate class-level defaults
        class_methods = generate_random_methods()
        class_tags = generate_random_tags()
        class_version = generate_random_string(2, 5)
        class_policy = generate_random_access_policy()
        class_rate_limit = generate_random_rate_limit()

        SubEndpoint = _create_subclass(iteration, {
            "methods": class_methods,
            "tags": class_tags,
            "version": class_version,
            "access_policy": class_policy,
            "rate_limit": class_rate_limit,
        })

        handler = _make_handler(iteration, "fallback")
        leaf = f"fallback_{iteration}_{generate_random_leaf()}"

        # Call attach_at with only the mandatory leaf, no overrides
        SubEndpoint.attach_at(leaf=leaf)(handler)

        descriptors = EndpointRegistry.collect()
        if len(descriptors) != 1:
            raise AssertionError(
                f"Iteration {iteration}: Expected 1 descriptor, got {len(descriptors)}"
            )

        desc = descriptors[0]

        # Verify class defaults are used
        if desc.methods != class_methods:
            raise AssertionError(
                f"Iteration {iteration}: methods should fall back to class default "
                f"{class_methods}, got {desc.methods}"
            )

        if desc.tags != class_tags:
            raise AssertionError(
                f"Iteration {iteration}: tags should fall back to class default "
                f"{class_tags}, got {desc.tags}"
            )

        if desc.version != class_version:
            raise AssertionError(
                f"Iteration {iteration}: version should fall back to class default "
                f"'{class_version}', got '{desc.version}'"
            )

        if desc.constraints.access_policy is not class_policy:
            raise AssertionError(
                f"Iteration {iteration}: access_policy should fall back to class default"
            )

        if desc.constraints.rate_limit is not class_rate_limit:
            raise AssertionError(
                f"Iteration {iteration}: rate_limit should fall back to class default"
            )

    return



def test_property_class_attributes_unchanged_after_attachment():
    """
        Property 2: Attribute Inheritance and Override - Immutability

        *For any* Endpoint subclass with class-level attributes, after
        attach_at is called with explicit overrides, the class attributes
        SHALL remain unchanged.

        **Feature: endpoint-abstractions, Property 2: Attribute Inheritance and Override**
        **Validates: Requirements 2.3**
    """
    for iteration in range(100):
        _clear_registry()

        # Generate class-level defaults
        class_methods = generate_random_methods()
        class_tags = generate_random_tags()
        class_version = generate_random_string(2, 5)
        class_policy = generate_random_access_policy()
        class_rate_limit = generate_random_rate_limit()

        SubEndpoint = _create_subclass(iteration, {
            "methods": list(class_methods),
            "tags": list(class_tags),
            "version": class_version,
            "access_policy": class_policy,
            "rate_limit": class_rate_limit,
        })

        # Snapshot class attributes before attachment
        before_methods = list(SubEndpoint.methods)
        before_tags = list(SubEndpoint.tags)
        before_version = SubEndpoint.version
        before_policy = SubEndpoint.access_policy
        before_rate_limit = SubEndpoint.rate_limit

        handler = _make_handler(iteration, "immutable")
        leaf = f"immutable_{iteration}_{generate_random_leaf()}"

        # Call attach_at with explicit overrides
        SubEndpoint.attach_at(
            leaf=leaf,
            methods=generate_random_methods(),
            tags=generate_random_tags(),
            version=generate_random_string(2, 5) + "_new",
            access_policy=generate_random_access_policy(),
            rate_limit=generate_random_rate_limit(),
        )(handler)

        # Verify class attributes are unchanged
        if SubEndpoint.methods != before_methods:
            raise AssertionError(
                f"Iteration {iteration}: class methods mutated from "
                f"{before_methods} to {SubEndpoint.methods}"
            )

        if SubEndpoint.tags != before_tags:
            raise AssertionError(
                f"Iteration {iteration}: class tags mutated from "
                f"{before_tags} to {SubEndpoint.tags}"
            )

        if SubEndpoint.version != before_version:
            raise AssertionError(
                f"Iteration {iteration}: class version mutated from "
                f"'{before_version}' to '{SubEndpoint.version}'"
            )

        if SubEndpoint.access_policy is not before_policy:
            raise AssertionError(
                f"Iteration {iteration}: class access_policy was replaced"
            )

        if SubEndpoint.rate_limit is not before_rate_limit:
            raise AssertionError(
                f"Iteration {iteration}: class rate_limit was replaced"
            )

    return


def test_property_partial_override_mixes_class_and_kwargs():
    """
        Property 2: Attribute Inheritance and Override - Partial Override

        *For any* Endpoint subclass, when attach_at is called with only
        some kwargs, the provided kwargs SHALL override their corresponding
        class attributes while the remaining attributes fall back to class
        defaults.

        **Feature: endpoint-abstractions, Property 2: Attribute Inheritance and Override**
        **Validates: Requirements 1.3, 1.4, 2.8**
    """
    # The overridable attributes we test
    ATTR_KEYS = ["methods", "tags", "version", "access_policy", "rate_limit"]

    for iteration in range(100):
        _clear_registry()

        # Generate class-level defaults
        class_attrs = {
            "methods": generate_random_methods(),
            "tags": generate_random_tags(),
            "version": generate_random_string(2, 5),
            "access_policy": generate_random_access_policy(),
            "rate_limit": generate_random_rate_limit(),
        }

        SubEndpoint = _create_subclass(iteration, dict(class_attrs))

        # Randomly pick a subset of attributes to override (at least 1)
        num_overrides = random.randint(1, len(ATTR_KEYS) - 1)
        override_keys = random.sample(ATTR_KEYS, num_overrides)

        override_values = {}
        for key in override_keys:
            if key == "methods":
                override_values[key] = generate_random_methods()
            elif key == "tags":
                override_values[key] = generate_random_tags()
            elif key == "version":
                override_values[key] = generate_random_string(2, 5) + "_partial"
            elif key == "access_policy":
                override_values[key] = generate_random_access_policy()
            elif key == "rate_limit":
                override_values[key] = generate_random_rate_limit()

        handler = _make_handler(iteration, "partial")
        leaf = f"partial_{iteration}_{generate_random_leaf()}"

        SubEndpoint.attach_at(leaf=leaf, **override_values)(handler)

        descriptors = EndpointRegistry.collect()
        if len(descriptors) != 1:
            raise AssertionError(
                f"Iteration {iteration}: Expected 1 descriptor, got {len(descriptors)}"
            )

        desc = descriptors[0]

        for key in ATTR_KEYS:
            if key in override_keys:
                # This attribute was overridden
                expected = override_values[key]
            else:
                # This attribute should fall back to class default
                expected = class_attrs[key]

            if key == "methods":
                actual = desc.methods
            elif key == "tags":
                actual = desc.tags
            elif key == "version":
                actual = desc.version
            elif key == "access_policy":
                actual = desc.constraints.access_policy
            elif key == "rate_limit":
                actual = desc.constraints.rate_limit

            if key in ("access_policy", "rate_limit"):
                if actual is not expected:
                    source = "override" if key in override_keys else "class default"
                    raise AssertionError(
                        f"Iteration {iteration}: {key} should be {source} object, "
                        f"but identity check failed. Overridden keys: {override_keys}"
                    )
            else:
                if actual != expected:
                    source = "override" if key in override_keys else "class default"
                    raise AssertionError(
                        f"Iteration {iteration}: {key} should be {source} "
                        f"{expected}, got {actual}. Overridden keys: {override_keys}"
                    )

    return


def test_property_subclass_defaults_inherited_by_handler():
    """
        Property 2: Attribute Inheritance and Override - Subclass Inheritance

        *For any* Endpoint subclass that defines class attributes such as
        access_policy, rate_limit, methods, version, and tags, a handler
        decorated with attach_at() SHALL inherit those constraints
        automatically when no overrides are provided.

        **Feature: endpoint-abstractions, Property 2: Attribute Inheritance and Override**
        **Validates: Requirements 1.6**
    """
    for iteration in range(100):
        _clear_registry()

        # Generate random class-level defaults
        class_methods = generate_random_methods()
        class_tags = generate_random_tags()
        class_version = generate_random_string(2, 5)
        class_policy = generate_random_access_policy()
        class_rate_limit = generate_random_rate_limit()
        class_serializers = {generate_random_string(): generate_random_string()}

        SubEndpoint = _create_subclass(iteration, {
            "methods": class_methods,
            "tags": class_tags,
            "version": class_version,
            "access_policy": class_policy,
            "rate_limit": class_rate_limit,
            "serializers": class_serializers,
        })

        handler = _make_handler(iteration, "inherit")
        leaf = f"inherit_{iteration}_{generate_random_leaf()}"

        SubEndpoint.attach_at(leaf=leaf)(handler)

        descriptors = EndpointRegistry.collect()
        desc = descriptors[0]

        # Verify all class attributes are inherited
        if desc.methods != class_methods:
            raise AssertionError(
                f"Iteration {iteration}: methods not inherited. "
                f"Expected {class_methods}, got {desc.methods}"
            )

        if desc.tags != class_tags:
            raise AssertionError(
                f"Iteration {iteration}: tags not inherited. "
                f"Expected {class_tags}, got {desc.tags}"
            )

        if desc.version != class_version:
            raise AssertionError(
                f"Iteration {iteration}: version not inherited. "
                f"Expected '{class_version}', got '{desc.version}'"
            )

        if desc.constraints.access_policy is not class_policy:
            raise AssertionError(
                f"Iteration {iteration}: access_policy not inherited from subclass"
            )

        if desc.constraints.rate_limit is not class_rate_limit:
            raise AssertionError(
                f"Iteration {iteration}: rate_limit not inherited from subclass"
            )

        # Verify serializers are carried through in extras
        if "serializers" not in desc.extras:
            raise AssertionError(
                f"Iteration {iteration}: serializers not found in descriptor extras"
            )

        if desc.extras["serializers"] != class_serializers:
            raise AssertionError(
                f"Iteration {iteration}: serializers not inherited. "
                f"Expected {class_serializers}, got {desc.extras['serializers']}"
            )

    return
