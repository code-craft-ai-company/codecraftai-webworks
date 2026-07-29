"""
.. module:: test_endpoint_identity_properties
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Property-based tests for decorator identity preservation.

.. moduleauthor:: Code Craft AI LLC

This module contains property-based tests for the Endpoint class,
validating Property 1: Decorator Identity Preservation across many
generated inputs.
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []

import random
import string
from typing import List, Optional

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
    count = random.randint(0, 4)
    return [generate_random_string(3, 8) for _ in range(count)]


def generate_random_access_policy() -> Optional[AccessPolicy]:
    """Generate a random AccessPolicy or None."""
    if random.choice([True, False]):
        return None
    roles = [generate_random_string(3, 8) for _ in range(random.randint(0, 3))]
    scopes = [generate_random_string(3, 8) for _ in range(random.randint(0, 3))]
    return AccessPolicy(roles=roles, scopes=scopes, require_auth=random.choice([True, False]))


def generate_random_rate_limit() -> Optional[RateLimit]:
    """Generate a random RateLimit or None."""
    if random.choice([True, False]):
        return None
    return RateLimit(requests=random.randint(1, 1000), window=random.randint(1, 3600))


def generate_random_doc() -> Optional[Doc]:
    """Generate a random Doc or None."""
    if random.choice([True, False]):
        return None
    return Doc(
        summary=generate_random_string(5, 20),
        description=generate_random_string(10, 40),
        deprecated=random.choice([True, False])
    )


def _clear_registry():
    """Helper to clear the registry before tests."""
    registry = EndpointRegistry()
def _make_handler(iteration: int):
    """Create a unique handler function for a given iteration."""
    def handler():
        return iteration
    handler.__name__ = f"handler_{iteration}"
    handler.__qualname__ = f"handler_{iteration}"
    return handler


# =============================================================================
# Property 1: Decorator Identity Preservation
# Feature: endpoint-abstractions, Property 1: Decorator Identity Preservation
# Validates: Requirements 2.1, 4.3
# =============================================================================

def test_property_decorator_returns_identical_function():
    """
        Property 1: Decorator Identity Preservation

        *For any* handler function decorated with attach_at, the returned
        function SHALL be identical (same object identity) to the original
        function, ensuring decorator stacking works correctly.

        This test verifies that the decorator returns the exact same object
        (identity check via `is`) for randomly generated handler functions
        with varying attach_at parameters.

        **Feature: endpoint-abstractions, Property 1: Decorator Identity Preservation**
        **Validates: Requirements 2.1, 4.3**
    """
    for iteration in range(100):
        registry = EndpointRegistry()

        handler = _make_handler(iteration)
        original_id = id(handler)

        # Generate a unique leaf per iteration to avoid conflicts
        leaf = f"prop1_{iteration}_{generate_random_leaf()}"

        decorated = Endpoint.attach_at(
            leaf=leaf,
            methods=generate_random_methods(),
            tags=generate_random_tags(),
            access_policy=generate_random_access_policy(),
            rate_limit=generate_random_rate_limit(),
            doc=generate_random_doc()
        )(handler)

        if decorated is not handler:
            errmsg = (
                f"Iteration {iteration}: Decorated function is not the same object "
                f"as the original handler. id(original)={original_id}, "
                f"id(decorated)={id(decorated)}"
            )
            raise AssertionError(errmsg)

    return


def test_property_decorator_preserves_function_callable():
    """
        Property 1: Decorator Identity Preservation - Callable Preservation

        *For any* handler function decorated with attach_at, the decorated
        function SHALL remain callable and produce the same return value
        as the original function.

        **Feature: endpoint-abstractions, Property 1: Decorator Identity Preservation**
        **Validates: Requirements 2.1, 4.3**
    """
    for iteration in range(100):
        registry = EndpointRegistry()

        expected_value = random.randint(0, 10000)

        def handler():
            return expected_value

        handler.__name__ = f"handler_callable_{iteration}"
        handler.__qualname__ = f"handler_callable_{iteration}"

        leaf = f"callable_{iteration}_{generate_random_leaf()}"

        decorated = Endpoint.attach_at(leaf=leaf)(handler)

        result = decorated()

        if result != expected_value:
            errmsg = (
                f"Iteration {iteration}: Decorated function returned {result}, "
                f"expected {expected_value}."
            )
            raise AssertionError(errmsg)

    return


def test_property_decorator_preserves_identity_with_subclasses():
    """
        Property 1: Decorator Identity Preservation - Subclass Decorators

        *For any* Endpoint subclass with class-level defaults, the attach_at
        decorator SHALL still return the identical original function object.

        **Feature: endpoint-abstractions, Property 1: Decorator Identity Preservation**
        **Validates: Requirements 2.1, 4.3**
    """
    for iteration in range(100):
        registry = EndpointRegistry()

        # Create a random subclass with random class-level defaults
        subclass_attrs = {
            "methods": generate_random_methods(),
            "tags": generate_random_tags(),
            "version": generate_random_string(2, 5) if random.choice([True, False]) else None,
        }

        policy = generate_random_access_policy()
        if policy is not None:
            subclass_attrs["access_policy"] = policy

        limit = generate_random_rate_limit()
        if limit is not None:
            subclass_attrs["rate_limit"] = limit

        CustomEndpoint = type(f"CustomEndpoint_{iteration}", (Endpoint,), subclass_attrs)

        handler = _make_handler(iteration)
        leaf = f"subclass_{iteration}_{generate_random_leaf()}"

        decorated = CustomEndpoint.attach_at(leaf=leaf)(handler)

        if decorated is not handler:
            errmsg = (
                f"Iteration {iteration}: Subclass decorator did not return the "
                f"original handler. Subclass attrs: {subclass_attrs}"
            )
            raise AssertionError(errmsg)

    return


def test_property_decorator_preserves_identity_with_extras():
    """
        Property 1: Decorator Identity Preservation - Extra Kwargs

        *For any* handler decorated with attach_at that includes arbitrary
        extra kwargs, the returned function SHALL be identical to the
        original function.

        **Feature: endpoint-abstractions, Property 1: Decorator Identity Preservation**
        **Validates: Requirements 2.1, 4.3**
    """
    for iteration in range(100):
        registry = EndpointRegistry()

        handler = _make_handler(iteration)
        leaf = f"extras_{iteration}_{generate_random_leaf()}"

        # Generate random extra kwargs
        num_extras = random.randint(1, 5)
        extras = {
            generate_random_string(4, 8): generate_random_string(4, 12)
            for _ in range(num_extras)
        }

        decorated = Endpoint.attach_at(leaf=leaf, **extras)(handler)

        if decorated is not handler:
            errmsg = (
                f"Iteration {iteration}: Decorator with extras did not return "
                f"the original handler. extras={extras}"
            )
            raise AssertionError(errmsg)

    return


def test_property_decorator_preserves_identity_with_path():
    """
        Property 1: Decorator Identity Preservation - Path Parameter

        *For any* handler decorated with attach_at using the path parameter
        (instead of leaf), the returned function SHALL be identical to the
        original function.

        **Feature: endpoint-abstractions, Property 1: Decorator Identity Preservation**
        **Validates: Requirements 2.1, 4.3**
    """
    for iteration in range(100):
        registry = EndpointRegistry()

        handler = _make_handler(iteration)

        # Generate a random path
        segments = [generate_random_string(3, 8) for _ in range(random.randint(1, 4))]
        path = "/" + "/".join(segments) + f"/{iteration}"

        decorated = Endpoint.attach_at(
            path=path,
            methods=generate_random_methods()
        )(handler)

        if decorated is not handler:
            errmsg = (
                f"Iteration {iteration}: Decorator with path={path} did not "
                f"return the original handler."
            )
            raise AssertionError(errmsg)

    return
