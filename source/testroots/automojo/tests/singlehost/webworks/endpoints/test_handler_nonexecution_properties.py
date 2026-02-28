"""
.. module:: test_handler_nonexecution_properties
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Property-based tests for handler non-execution during import.

.. moduleauthor:: Automation Mojo LLC

This module contains property-based tests for the Endpoint class,
validating Property 11: Handler Non-Execution During Import across
many generated inputs.
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []

import random
import string
from typing import Any, Dict, List, Optional

from automojo.webworks.endpoints import (
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
    EndpointRegistry.clear()


def _create_subclass(iteration: int, attrs: Dict[str, Any]) -> type:
    """Create a unique Endpoint subclass with the given class attributes."""
    return type(f"NonExecEndpoint_{iteration}", (Endpoint,), dict(attrs))


# =============================================================================
# Property 11: Handler Non-Execution During Import
# Feature: endpoint-abstractions, Property 11: Handler Non-Execution During Import
# Validates: Requirements 6.2
# =============================================================================

def test_property_handler_not_called_during_attach_at():
    """
        Property 11: Handler Non-Execution During Import - attach_at

        *For any* handler function decorated with attach_at, the handler
        SHALL NOT be executed during the decoration process. Only descriptor
        generation and registry insertion SHALL occur.

        **Feature: endpoint-abstractions, Property 11: Handler Non-Execution During Import**
        **Validates: Requirements 6.2**
    """
    for iteration in range(100):
        _clear_registry()

        call_count = [0]

        def handler():
            call_count[0] += 1
            return iteration

        handler.__name__ = f"handler_noexec_{iteration}"
        handler.__qualname__ = f"handler_noexec_{iteration}"

        leaf = f"noexec_{iteration}_{generate_random_leaf()}"
        methods = generate_random_methods()
        tags = generate_random_tags()
        access_policy = generate_random_access_policy()
        rate_limit = generate_random_rate_limit()
        doc = generate_random_doc()

        decorated = Endpoint.attach_at(
            leaf=leaf,
            methods=methods,
            tags=tags,
            access_policy=access_policy,
            rate_limit=rate_limit,
            doc=doc,
        )(handler)

        if call_count[0] != 0:
            raise AssertionError(
                f"Iteration {iteration}: Handler was called {call_count[0]} time(s) "
                f"during attach_at decoration. Expected 0 calls."
            )

    return


def test_property_handler_not_called_during_subclass_attach_at():
    """
        Property 11: Handler Non-Execution During Import - Subclass attach_at

        *For any* Endpoint subclass with class-level attributes, decorating
        a handler with the subclass's attach_at SHALL NOT execute the handler.
        Only descriptor generation SHALL occur.

        **Feature: endpoint-abstractions, Property 11: Handler Non-Execution During Import**
        **Validates: Requirements 6.2**
    """
    for iteration in range(100):
        _clear_registry()

        class_methods = generate_random_methods()
        class_tags = generate_random_tags()
        class_policy = generate_random_access_policy()
        class_rate_limit = generate_random_rate_limit()

        SubEndpoint = _create_subclass(iteration, {
            "methods": class_methods,
            "tags": class_tags,
            "access_policy": class_policy,
            "rate_limit": class_rate_limit,
        })

        call_count = [0]

        def handler():
            call_count[0] += 1
            return iteration

        handler.__name__ = f"handler_sub_noexec_{iteration}"
        handler.__qualname__ = f"handler_sub_noexec_{iteration}"

        leaf = f"sub_noexec_{iteration}_{generate_random_leaf()}"

        SubEndpoint.attach_at(leaf=leaf)(handler)

        if call_count[0] != 0:
            raise AssertionError(
                f"Iteration {iteration}: Handler was called {call_count[0]} time(s) "
                f"during subclass attach_at decoration. Expected 0 calls."
            )

    return


def test_property_handler_not_called_during_registry_collect():
    """
        Property 11: Handler Non-Execution During Import - Registry Collect

        *For any* set of registered endpoints, calling EndpointRegistry.collect()
        SHALL NOT execute any of the registered handlers. The collect operation
        SHALL only return descriptor records.

        **Feature: endpoint-abstractions, Property 11: Handler Non-Execution During Import**
        **Validates: Requirements 6.2**
    """
    for iteration in range(100):
        _clear_registry()

        num_handlers = random.randint(1, 5)
        call_counts = []

        for idx in range(num_handlers):
            call_count = [0]
            call_counts.append(call_count)

            def make_handler(cc, i):
                def handler():
                    cc[0] += 1
                    return i
                handler.__name__ = f"handler_collect_{iteration}_{i}"
                handler.__qualname__ = f"handler_collect_{iteration}_{i}"
                return handler

            handler = make_handler(call_count, idx)
            leaf = f"collect_{iteration}_{idx}_{generate_random_leaf()}"
            Endpoint.attach_at(leaf=leaf)(handler)

        # Reset counts after registration (registration itself should not call them,
        # but we want to isolate the collect() call)
        for cc in call_counts:
            cc[0] = 0

        # Call collect - this should not execute any handlers
        descriptors = EndpointRegistry.collect()

        for idx, cc in enumerate(call_counts):
            if cc[0] != 0:
                raise AssertionError(
                    f"Iteration {iteration}: Handler {idx} was called {cc[0]} time(s) "
                    f"during EndpointRegistry.collect(). Expected 0 calls."
                )

        if len(descriptors) != num_handlers:
            raise AssertionError(
                f"Iteration {iteration}: Expected {num_handlers} descriptors from "
                f"collect(), got {len(descriptors)}"
            )

    return


def test_property_handler_callable_preserved_after_attach_at():
    """
        Property 11: Handler Non-Execution During Import - Callable Preserved

        *For any* handler decorated with attach_at, the handler SHALL remain
        callable after decoration and SHALL only execute when explicitly
        invoked, not during the import/registration phase.

        **Feature: endpoint-abstractions, Property 11: Handler Non-Execution During Import**
        **Validates: Requirements 6.2**
    """
    for iteration in range(100):
        _clear_registry()

        call_count = [0]
        expected_return = random.randint(0, 10000)

        def handler():
            call_count[0] += 1
            return expected_return

        handler.__name__ = f"handler_callable_{iteration}"
        handler.__qualname__ = f"handler_callable_{iteration}"

        leaf = f"callable_{iteration}_{generate_random_leaf()}"

        decorated = Endpoint.attach_at(leaf=leaf)(handler)

        # Verify no calls during decoration
        if call_count[0] != 0:
            raise AssertionError(
                f"Iteration {iteration}: Handler was called during decoration. "
                f"Expected 0 calls, got {call_count[0]}."
            )

        # Now explicitly call the handler - it should work
        result = decorated()

        if call_count[0] != 1:
            raise AssertionError(
                f"Iteration {iteration}: Handler call count after explicit invocation "
                f"should be 1, got {call_count[0]}."
            )

        if result != expected_return:
            raise AssertionError(
                f"Iteration {iteration}: Handler returned {result}, "
                f"expected {expected_return}."
            )

    return
