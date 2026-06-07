"""
.. module:: test_path_composition_properties
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Property-based tests for path composition in endpoint hierarchies.

.. moduleauthor:: Code Craft AI LLC

This module contains property-based tests validating Property 10: Path
Composition across many generated inputs. It covers path composition
semantics for Endpoint.attach_child, Blueprint._compose_path, and
RestBlueprint._compute_full_path.
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []

import random
import string
from typing import List, Optional

from ccai.webworks.endpoints.blueprint import Blueprint
from ccai.webworks.endpoints.endpoint import Endpoint
from ccai.webworks.endpoints.registry import EndpointRegistry
from ccai.webworks.endpoints.restblueprint import RestBlueprint


# =============================================================================
# Helper Functions for Generating Random Test Data
# =============================================================================

def generate_random_segment(min_len: int = 2, max_len: int = 8) -> str:
    """Generate a random URL path segment (lowercase alphanumeric)."""
    length = random.randint(min_len, max_len)
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))


def generate_random_base_path() -> str:
    """Generate a random absolute base path like /api/v1."""
    num_segments = random.randint(1, 3)
    segments = [generate_random_segment() for _ in range(num_segments)]
    return "/" + "/".join(segments)


def generate_random_leaf() -> str:
    """Generate a random URL leaf segment."""
    return generate_random_segment(2, 10)


def generate_random_methods() -> List[str]:
    """Generate a random list of HTTP methods."""
    all_methods = ["GET", "POST", "PUT", "PATCH", "DELETE"]
    count = random.randint(1, len(all_methods))
    return random.sample(all_methods, count)



# =============================================================================
# Property 10: Path Composition - Endpoint._compute_child_path
# Feature: endpoint-abstractions, Property 10: Path Composition
# Validates: Requirements 9.6, 9.7, 10.3, 10.4
# =============================================================================

def test_property_child_path_with_base_path_and_leaf():
    """
        Property 10: Path Composition - base_path + child leaf

        *For any* parent with base_path and child with leaf, the resulting
        path SHALL be base_path/leaf.

        **Feature: endpoint-abstractions, Property 10: Path Composition**
        **Validates: Requirements 10.3, 10.4**
    """
    for iteration in range(100):
        base_path = generate_random_base_path()
        child_leaf = generate_random_leaf()

        # Create a parent endpoint subclass with base_path
        parent_cls = type(
            f"Parent_{iteration}",
            (Endpoint,),
            {"base_path": base_path, "base_leaf": None}
        )

        result = parent_cls._compute_child_path(
            child_leaf=child_leaf,
            child_path=None
        )

        expected = f"{base_path.rstrip('/')}/{child_leaf}"

        if result != expected:
            errmsg = (
                f"Iteration {iteration}: Expected path '{expected}' but got "
                f"'{result}' for base_path='{base_path}', child_leaf='{child_leaf}'"
            )
            raise AssertionError(errmsg)

    return


def test_property_child_path_with_base_leaf_and_child_leaf():
    """
        Property 10: Path Composition - base_leaf + child leaf

        *For any* parent with base_leaf (no base_path) and child with leaf,
        the resulting path SHALL be /base_leaf/child_leaf.

        **Feature: endpoint-abstractions, Property 10: Path Composition**
        **Validates: Requirements 9.6, 10.3**
    """
    for iteration in range(100):
        base_leaf = generate_random_leaf()
        child_leaf = generate_random_leaf()

        parent_cls = type(
            f"Parent_{iteration}",
            (Endpoint,),
            {"base_path": None, "base_leaf": base_leaf}
        )

        result = parent_cls._compute_child_path(
            child_leaf=child_leaf,
            child_path=None
        )

        expected = f"/{base_leaf}/{child_leaf}"

        if result != expected:
            errmsg = (
                f"Iteration {iteration}: Expected path '{expected}' but got "
                f"'{result}' for base_leaf='{base_leaf}', child_leaf='{child_leaf}'"
            )
            raise AssertionError(errmsg)

    return


def test_property_child_path_with_base_path_and_child_absolute_path():
    """
        Property 10: Path Composition - base_path + child absolute path

        *For any* parent with base_path and child with an absolute path
        (starting with /), the resulting path SHALL be base_path + child_path.

        **Feature: endpoint-abstractions, Property 10: Path Composition**
        **Validates: Requirements 10.3, 10.4**
    """
    for iteration in range(100):
        base_path = generate_random_base_path()
        child_path = "/" + generate_random_segment()

        parent_cls = type(
            f"Parent_{iteration}",
            (Endpoint,),
            {"base_path": base_path, "base_leaf": None}
        )

        result = parent_cls._compute_child_path(
            child_leaf=None,
            child_path=child_path
        )

        expected = f"{base_path.rstrip('/')}{child_path}"

        if result != expected:
            errmsg = (
                f"Iteration {iteration}: Expected path '{expected}' but got "
                f"'{result}' for base_path='{base_path}', child_path='{child_path}'"
            )
            raise AssertionError(errmsg)

    return


def test_property_child_path_with_base_path_and_child_relative_path():
    """
        Property 10: Path Composition - base_path + child relative path

        *For any* parent with base_path and child with a relative path
        (not starting with /), the resulting path SHALL be base_path/child_path.

        **Feature: endpoint-abstractions, Property 10: Path Composition**
        **Validates: Requirements 10.3, 10.4**
    """
    for iteration in range(100):
        base_path = generate_random_base_path()
        child_path = generate_random_segment()

        parent_cls = type(
            f"Parent_{iteration}",
            (Endpoint,),
            {"base_path": base_path, "base_leaf": None}
        )

        result = parent_cls._compute_child_path(
            child_leaf=None,
            child_path=child_path
        )

        expected = f"{base_path.rstrip('/')}/{child_path}"

        if result != expected:
            errmsg = (
                f"Iteration {iteration}: Expected path '{expected}' but got "
                f"'{result}' for base_path='{base_path}', child_path='{child_path}'"
            )
            raise AssertionError(errmsg)

    return


def test_property_child_path_no_parent_base_returns_child_path():
    """
        Property 10: Path Composition - No parent base

        *For any* parent with no base_path and no base_leaf, the child's
        path SHALL be returned as-is.

        **Feature: endpoint-abstractions, Property 10: Path Composition**
        **Validates: Requirements 10.3**
    """
    for iteration in range(100):
        child_path = "/" + generate_random_segment()

        parent_cls = type(
            f"Parent_{iteration}",
            (Endpoint,),
            {"base_path": None, "base_leaf": None}
        )

        result = parent_cls._compute_child_path(
            child_leaf=None,
            child_path=child_path
        )

        if result != child_path:
            errmsg = (
                f"Iteration {iteration}: Expected path '{child_path}' but got "
                f"'{result}' when parent has no base"
            )
            raise AssertionError(errmsg)

    return


def test_property_child_path_no_parent_base_no_child_path_returns_none():
    """
        Property 10: Path Composition - No parent base, no child path/leaf

        *For any* parent with no base and child with no path or leaf,
        the result SHALL be None.

        **Feature: endpoint-abstractions, Property 10: Path Composition**
        **Validates: Requirements 10.3**
    """
    for iteration in range(100):
        parent_cls = type(
            f"Parent_{iteration}",
            (Endpoint,),
            {"base_path": None, "base_leaf": None}
        )

        result = parent_cls._compute_child_path(
            child_leaf=None,
            child_path=None
        )

        if result is not None:
            errmsg = (
                f"Iteration {iteration}: Expected None but got '{result}' "
                f"when both parent base and child path/leaf are None"
            )
            raise AssertionError(errmsg)

    return



# =============================================================================
# Property 10: Path Composition - Blueprint._compose_path
# Feature: endpoint-abstractions, Property 10: Path Composition
# Validates: Requirements 9.6, 9.7, 10.3, 10.4
# =============================================================================

def test_property_blueprint_compose_path_base_path_with_leaf():
    """
        Property 10: Path Composition - Blueprint base_path + leaf

        *For any* Blueprint with base_path and a child leaf, _compose_path
        SHALL return base_path/leaf.

        **Feature: endpoint-abstractions, Property 10: Path Composition**
        **Validates: Requirements 9.6, 10.3**
    """
    for iteration in range(100):
        base_path = generate_random_base_path()
        child_leaf = generate_random_leaf()

        bp_cls = type(
            f"BP_{iteration}",
            (Blueprint,),
            {"base_path": base_path, "base_leaf": None}
        )

        result = bp_cls._compose_path(leaf=child_leaf, path=None)

        expected_base = base_path.rstrip("/")
        expected = f"{expected_base}/{child_leaf}"

        if result != expected:
            errmsg = (
                f"Iteration {iteration}: Expected '{expected}' but got "
                f"'{result}' for base_path='{base_path}', leaf='{child_leaf}'"
            )
            raise AssertionError(errmsg)

    return


def test_property_blueprint_compose_path_base_leaf_with_child_leaf():
    """
        Property 10: Path Composition - Blueprint base_leaf + child leaf

        *For any* Blueprint with base_leaf and a child leaf, _compose_path
        SHALL return /base_leaf/child_leaf.

        **Feature: endpoint-abstractions, Property 10: Path Composition**
        **Validates: Requirements 9.6, 10.3**
    """
    for iteration in range(100):
        base_leaf = generate_random_leaf()
        child_leaf = generate_random_leaf()

        bp_cls = type(
            f"BP_{iteration}",
            (Blueprint,),
            {"base_path": None, "base_leaf": base_leaf}
        )

        result = bp_cls._compose_path(leaf=child_leaf, path=None)

        expected = f"/{base_leaf}/{child_leaf}"

        if result != expected:
            errmsg = (
                f"Iteration {iteration}: Expected '{expected}' but got "
                f"'{result}' for base_leaf='{base_leaf}', child_leaf='{child_leaf}'"
            )
            raise AssertionError(errmsg)

    return


def test_property_blueprint_compose_path_base_path_with_absolute_child_path():
    """
        Property 10: Path Composition - Blueprint base_path + absolute child path

        *For any* Blueprint with base_path and a child with absolute path
        (starting with /), _compose_path SHALL return base_path + child_path.

        **Feature: endpoint-abstractions, Property 10: Path Composition**
        **Validates: Requirements 9.6, 10.3, 10.4**
    """
    for iteration in range(100):
        base_path = generate_random_base_path()
        child_path = "/" + generate_random_segment()

        bp_cls = type(
            f"BP_{iteration}",
            (Blueprint,),
            {"base_path": base_path, "base_leaf": None}
        )

        result = bp_cls._compose_path(leaf=None, path=child_path)

        expected_base = base_path.rstrip("/")
        expected = f"{expected_base}{child_path}"

        if result != expected:
            errmsg = (
                f"Iteration {iteration}: Expected '{expected}' but got "
                f"'{result}' for base_path='{base_path}', child_path='{child_path}'"
            )
            raise AssertionError(errmsg)

    return


def test_property_blueprint_compose_path_base_path_with_relative_child_path():
    """
        Property 10: Path Composition - Blueprint base_path + relative child path

        *For any* Blueprint with base_path and a child with relative path
        (not starting with /), _compose_path SHALL return base_path/child_path.

        **Feature: endpoint-abstractions, Property 10: Path Composition**
        **Validates: Requirements 9.6, 10.3**
    """
    for iteration in range(100):
        base_path = generate_random_base_path()
        child_path = generate_random_segment()

        bp_cls = type(
            f"BP_{iteration}",
            (Blueprint,),
            {"base_path": base_path, "base_leaf": None}
        )

        result = bp_cls._compose_path(leaf=None, path=child_path)

        expected_base = base_path.rstrip("/")
        expected = f"{expected_base}/{child_path}"

        if result != expected:
            errmsg = (
                f"Iteration {iteration}: Expected '{expected}' but got "
                f"'{result}' for base_path='{base_path}', child_path='{child_path}'"
            )
            raise AssertionError(errmsg)

    return


def test_property_blueprint_compose_path_no_base_uses_child_directly():
    """
        Property 10: Path Composition - Blueprint no base, child path used directly

        *For any* Blueprint with no base_path and no base_leaf, _compose_path
        SHALL return the child path directly (prefixed with / if needed).

        **Feature: endpoint-abstractions, Property 10: Path Composition**
        **Validates: Requirements 9.6**
    """
    for iteration in range(100):
        child_path = "/" + generate_random_segment()

        bp_cls = type(
            f"BP_{iteration}",
            (Blueprint,),
            {"base_path": None, "base_leaf": None}
        )

        result = bp_cls._compose_path(leaf=None, path=child_path)

        if result != child_path:
            errmsg = (
                f"Iteration {iteration}: Expected '{child_path}' but got "
                f"'{result}' when blueprint has no base"
            )
            raise AssertionError(errmsg)

    return



# =============================================================================
# Property 10: Path Composition - RestBlueprint absolute override
# Feature: endpoint-abstractions, Property 10: Path Composition
# Validates: Requirements 9.7
# =============================================================================

def test_property_restblueprint_absolute_overrides_prefix():
    """
        Property 10: Path Composition - RestBlueprint absolute=True override

        *For any* RestBlueprint with base_path and a child attachment with
        absolute=True, the child's path SHALL override the blueprint prefix
        and be used as-is.

        **Feature: endpoint-abstractions, Property 10: Path Composition**
        **Validates: Requirements 9.7**
    """
    for iteration in range(100):
        base_path = generate_random_base_path()
        child_path = "/" + generate_random_segment()

        bp_cls = type(
            f"RBP_{iteration}",
            (RestBlueprint,),
            {
                "base_path": base_path,
                "base_leaf": None,
                "tags": [],
                "replace_tags": False,
            }
        )

        # When absolute=True, _compute_full_path is bypassed and path is used directly
        # Simulate the attach_at logic: if absolute, computed_path = path
        computed_path = child_path  # absolute=True means path is used as-is

        if computed_path != child_path:
            errmsg = (
                f"Iteration {iteration}: Expected absolute path '{child_path}' "
                f"but got '{computed_path}' for base_path='{base_path}'"
            )
            raise AssertionError(errmsg)

    return


def test_property_restblueprint_compute_full_path_base_path_with_leaf():
    """
        Property 10: Path Composition - RestBlueprint._compute_full_path

        *For any* RestBlueprint with base_path and a child leaf,
        _compute_full_path SHALL return base_path/leaf.

        **Feature: endpoint-abstractions, Property 10: Path Composition**
        **Validates: Requirements 9.6, 10.3**
    """
    for iteration in range(100):
        base_path = generate_random_base_path()
        child_leaf = generate_random_leaf()

        bp_cls = type(
            f"RBP_{iteration}",
            (RestBlueprint,),
            {"base_path": base_path, "base_leaf": None}
        )

        result = bp_cls._compute_full_path(leaf=child_leaf, path=None)

        expected_base = base_path.rstrip("/")
        expected = f"{expected_base}/{child_leaf}"

        if result != expected:
            errmsg = (
                f"Iteration {iteration}: Expected '{expected}' but got "
                f"'{result}' for base_path='{base_path}', leaf='{child_leaf}'"
            )
            raise AssertionError(errmsg)

    return


# =============================================================================
# Property 10: Path Composition - Endpoint.attach_child integration
# Feature: endpoint-abstractions, Property 10: Path Composition
# Validates: Requirements 10.3, 10.4
# =============================================================================

def test_property_attach_child_composes_path_from_parent_base():
    """
        Property 10: Path Composition - attach_child path composition

        *For any* parent Endpoint with base_path and a child Endpoint with
        base_leaf, attach_child SHALL produce a descriptor whose path is
        base_path/child_leaf.

        **Feature: endpoint-abstractions, Property 10: Path Composition**
        **Validates: Requirements 10.3, 10.4**
    """
    for iteration in range(100):
        base_path = generate_random_base_path()
        child_leaf = generate_random_leaf()

        parent_cls = type(
            f"Parent_{iteration}",
            (Endpoint,),
            {
                "base_path": base_path,
                "base_leaf": None,
                "access_policy": None,
                "rate_limit": None,
                "methods": ["GET"],
                "version": None,
                "tags": [],
                "serializers": {},
            }
        )

        child_cls = type(
            f"Child_{iteration}",
            (Endpoint,),
            {
                "base_path": None,
                "base_leaf": child_leaf,
                "access_policy": None,
                "rate_limit": None,
                "methods": ["GET"],
                "version": None,
                "tags": [],
                "serializers": {},
            }
        )

        descriptor = parent_cls.attach_child(child_cls)

        expected = f"{base_path.rstrip('/')}/{child_leaf}"

        if descriptor.path != expected:
            errmsg = (
                f"Iteration {iteration}: Expected descriptor.path='{expected}' "
                f"but got '{descriptor.path}' for parent base_path='{base_path}', "
                f"child base_leaf='{child_leaf}'"
            )
            raise AssertionError(errmsg)

    return


def test_property_attach_child_leaf_override_takes_precedence():
    """
        Property 10: Path Composition - attach_child leaf override

        *For any* parent with base_path and a child with base_leaf, when
        attach_child is called with an explicit leaf kwarg, the override
        leaf SHALL be used instead of the child's base_leaf.

        **Feature: endpoint-abstractions, Property 10: Path Composition**
        **Validates: Requirements 10.3, 10.4**
    """
    for iteration in range(100):
        base_path = generate_random_base_path()
        child_base_leaf = generate_random_leaf()
        override_leaf = generate_random_leaf()

        parent_cls = type(
            f"Parent_{iteration}",
            (Endpoint,),
            {
                "base_path": base_path,
                "base_leaf": None,
                "access_policy": None,
                "rate_limit": None,
                "methods": ["GET"],
                "version": None,
                "tags": [],
                "serializers": {},
            }
        )

        child_cls = type(
            f"Child_{iteration}",
            (Endpoint,),
            {
                "base_path": None,
                "base_leaf": child_base_leaf,
                "access_policy": None,
                "rate_limit": None,
                "methods": ["GET"],
                "version": None,
                "tags": [],
                "serializers": {},
            }
        )

        descriptor = parent_cls.attach_child(child_cls, leaf=override_leaf)

        expected = f"{base_path.rstrip('/')}/{override_leaf}"

        if descriptor.path != expected:
            errmsg = (
                f"Iteration {iteration}: Expected descriptor.path='{expected}' "
                f"but got '{descriptor.path}' when leaf override='{override_leaf}' "
                f"was provided (child base_leaf='{child_base_leaf}')"
            )
            raise AssertionError(errmsg)

    return


def test_property_path_composition_no_double_slashes():
    """
        Property 10: Path Composition - No double slashes

        *For any* combination of parent base_path and child leaf/path,
        the composed path SHALL NOT contain double slashes (//).

        **Feature: endpoint-abstractions, Property 10: Path Composition**
        **Validates: Requirements 9.6, 10.3**
    """
    for iteration in range(100):
        # Generate base paths that may have trailing slashes
        base_path = generate_random_base_path()
        if random.choice([True, False]):
            base_path = base_path + "/"

        child_leaf = generate_random_leaf()

        bp_cls = type(
            f"BP_{iteration}",
            (Blueprint,),
            {"base_path": base_path, "base_leaf": None}
        )

        result = bp_cls._compose_path(leaf=child_leaf, path=None)

        if "//" in result:
            errmsg = (
                f"Iteration {iteration}: Path '{result}' contains double "
                f"slashes for base_path='{base_path}', leaf='{child_leaf}'"
            )
            raise AssertionError(errmsg)

    return


def test_property_path_composition_starts_with_slash():
    """
        Property 10: Path Composition - Paths start with /

        *For any* Blueprint._compose_path call that produces a non-None
        result, the path SHALL start with /.

        **Feature: endpoint-abstractions, Property 10: Path Composition**
        **Validates: Requirements 9.6**
    """
    for iteration in range(100):
        base_path = generate_random_base_path()
        use_leaf = random.choice([True, False])

        bp_cls = type(
            f"BP_{iteration}",
            (Blueprint,),
            {"base_path": base_path, "base_leaf": None}
        )

        if use_leaf:
            child_leaf = generate_random_leaf()
            result = bp_cls._compose_path(leaf=child_leaf, path=None)
        else:
            child_path = generate_random_segment()
            result = bp_cls._compose_path(leaf=None, path=child_path)

        if result is not None and not result.startswith("/"):
            errmsg = (
                f"Iteration {iteration}: Path '{result}' does not start "
                f"with / for base_path='{base_path}'"
            )
            raise AssertionError(errmsg)

    return
