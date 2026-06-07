"""
.. module:: test_registry_properties
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Property-based tests for EndpointRegistry error handling.

.. moduleauthor:: Code Craft AI LLC

This module contains property-based tests for the EndpointRegistry and
Endpoint.attach_at registration error handling, validating Property 9:
Registration Error Handling across many generated inputs.
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []

import random
import string
from typing import List, Optional

from ccai.webworks.endpoints.accesspolicy import AccessPolicy
from ccai.webworks.endpoints.constraints import EndpointConstraints
from ccai.webworks.endpoints.descriptor import EndpointDescriptor
from ccai.webworks.endpoints.endpoint import Endpoint
from ccai.webworks.endpoints.exceptions import EndpointRegistrationError
from ccai.webworks.endpoints.registry import EndpointConflictError, EndpointRegistry


# =============================================================================
# Helper Functions for Generating Random Test Data
# =============================================================================

def generate_random_string(min_len: int = 3, max_len: int = 10) -> str:
    """Generate a random alphanumeric string."""
    length = random.randint(min_len, max_len)
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))


def generate_random_leaf() -> str:
    """Generate a random URL leaf segment."""
    segments = random.randint(1, 3)
    return "/".join(generate_random_string(3, 8) for _ in range(segments))


def generate_random_path() -> str:
    """Generate a random URL path."""
    segments = random.randint(1, 4)
    parts = [generate_random_string(3, 8) for _ in range(segments)]
    return "/" + "/".join(parts)


VALID_HTTP_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"]


def generate_random_methods() -> List[str]:
    """Generate a random list of HTTP methods (at least one)."""
    count = random.randint(1, 3)
    return random.sample(VALID_HTTP_METHODS, k=min(count, len(VALID_HTTP_METHODS)))


def make_handler(name: str = None):
    """Create a uniquely named handler function."""
    if name is None:
        name = "handler_" + generate_random_string(5, 10)

    def handler():
        pass

    handler.__name__ = name
    handler.__module__ = "test_registry_properties"
    return handler


def make_descriptor(
    handler=None,
    leaf: Optional[str] = None,
    path: Optional[str] = None,
    methods: Optional[List[str]] = None
) -> EndpointDescriptor:
    """Create an EndpointDescriptor with the given or random values."""
    if handler is None:
        handler = make_handler()
    if methods is None:
        methods = ["GET"]

    return EndpointDescriptor(
        handler=handler,
        module=handler.__module__,
        leaf=leaf,
        path=path,
        methods=methods,
        constraints=EndpointConstraints()
    )


# =============================================================================
# Property 9: Registration Error Handling
# Feature: endpoint-abstractions, Property 9: Registration Error Handling
# Validates: Requirements 2.4, 2.5, 6.5, 6.6
# =============================================================================

def test_property_missing_leaf_and_path_raises_registration_error():
    """
        Property 9: Registration Error Handling - Missing Mandatory Metadata

        *For any* attach_at call where both leaf and path are omitted,
        EndpointRegistrationError SHALL be raised with details about
        the missing fields.

        **Feature: endpoint-abstractions, Property 9: Registration Error Handling**
        **Validates: Requirements 2.4**
    """
    for iteration in range(100):
        handler = make_handler()

        # Generate random non-location kwargs to ensure the error is
        # specifically about missing leaf/path regardless of other params
        random_methods = generate_random_methods()
        random_version = generate_random_string() if random.random() > 0.5 else None
        random_tags = [generate_random_string() for _ in range(random.randint(0, 3))]

        caught = False
        try:
            decorator = Endpoint.attach_at(
                methods=random_methods,
                version=random_version,
                tags=random_tags
            )
            decorator(handler)
        except EndpointRegistrationError as exc:
            caught = True

            # The error should reference the missing fields
            if "leaf" not in str(exc) and "path" not in str(exc):
                errmsg = (
                    f"Iteration {iteration}: EndpointRegistrationError message should "
                    f"mention 'leaf' or 'path'. Got: {exc}"
                )
                raise AssertionError(errmsg)

        if not caught:
            errmsg = (
                f"Iteration {iteration}: Expected EndpointRegistrationError when both "
                f"leaf and path are None. methods={random_methods}, "
                f"version={random_version}, tags={random_tags}"
            )
            raise AssertionError(errmsg)

    return


def test_property_conflict_raises_error_for_same_path_method():
    """
        Property 9: Registration Error Handling - Conflict Detection

        *For any* two descriptors targeting the same path+method combination,
        the EndpointRegistry SHALL raise EndpointConflictError naming both
        handlers when on_conflict="error".

        **Feature: endpoint-abstractions, Property 9: Registration Error Handling**
        **Validates: Requirements 2.5, 6.5**
    """
    for iteration in range(100):
        EndpointRegistry.clear()

        # Generate a random path and method combination
        use_path = random.choice([True, False])
        if use_path:
            location_path = generate_random_path()
            location_leaf = None
        else:
            location_leaf = generate_random_leaf()
            location_path = None

        methods = [random.choice(VALID_HTTP_METHODS)]

        handler_a = make_handler("handler_a_" + generate_random_string(4, 6))
        handler_b = make_handler("handler_b_" + generate_random_string(4, 6))

        desc_a = make_descriptor(
            handler=handler_a,
            leaf=location_leaf,
            path=location_path,
            methods=methods
        )
        desc_b = make_descriptor(
            handler=handler_b,
            leaf=location_leaf,
            path=location_path,
            methods=methods
        )

        # First registration should succeed
        EndpointRegistry.register(desc_a, on_conflict="error")

        # Second registration at same path+method should raise conflict
        caught = False
        try:
            EndpointRegistry.register(desc_b, on_conflict="error")
        except EndpointConflictError as exc:
            caught = True

            # Error should reference the conflicting method
            if exc.method != methods[0].upper():
                errmsg = (
                    f"Iteration {iteration}: EndpointConflictError.method should be "
                    f"'{methods[0].upper()}', got '{exc.method}'"
                )
                raise AssertionError(errmsg)

            # Error should reference both handlers
            if exc.existing_handler is not handler_a:
                errmsg = (
                    f"Iteration {iteration}: EndpointConflictError.existing_handler "
                    f"should reference handler_a."
                )
                raise AssertionError(errmsg)

            if exc.new_handler is not handler_b:
                errmsg = (
                    f"Iteration {iteration}: EndpointConflictError.new_handler "
                    f"should reference handler_b."
                )
                raise AssertionError(errmsg)

        if not caught:
            errmsg = (
                f"Iteration {iteration}: Expected EndpointConflictError for duplicate "
                f"registration at path={location_path}, leaf={location_leaf}, "
                f"methods={methods}"
            )
            raise AssertionError(errmsg)

    EndpointRegistry.clear()
    return


def test_property_on_conflict_replace_allows_override():
    """
        Property 9: Registration Error Handling - Replace Override

        *For any* two descriptors targeting the same path+method combination,
        when on_conflict="replace" is used, the existing registration SHALL
        be replaced without error and the registry SHALL contain the new
        handler.

        **Feature: endpoint-abstractions, Property 9: Registration Error Handling**
        **Validates: Requirements 6.6**
    """
    for iteration in range(100):
        EndpointRegistry.clear()

        # Generate a random path and method combination
        use_path = random.choice([True, False])
        if use_path:
            location_path = generate_random_path()
            location_leaf = None
        else:
            location_leaf = generate_random_leaf()
            location_path = None

        methods = [random.choice(VALID_HTTP_METHODS)]

        handler_a = make_handler("orig_" + generate_random_string(4, 6))
        handler_b = make_handler("repl_" + generate_random_string(4, 6))

        desc_a = make_descriptor(
            handler=handler_a,
            leaf=location_leaf,
            path=location_path,
            methods=methods
        )
        desc_b = make_descriptor(
            handler=handler_b,
            leaf=location_leaf,
            path=location_path,
            methods=methods
        )

        # First registration
        EndpointRegistry.register(desc_a, on_conflict="error")

        # Second registration with replace should not raise
        try:
            EndpointRegistry.register(desc_b, on_conflict="replace")
        except EndpointConflictError as exc:
            errmsg = (
                f"Iteration {iteration}: on_conflict='replace' should not raise "
                f"EndpointConflictError. Got: {exc}"
            )
            raise AssertionError(errmsg)

        # The registry should now contain the replacement handler
        collected = EndpointRegistry.collect()
        matching = [
            d for d in collected
            if d.handler is handler_b
        ]

        if len(matching) == 0:
            errmsg = (
                f"Iteration {iteration}: After replace, registry should contain "
                f"the new handler '{handler_b.__name__}'. "
                f"Found handlers: {[d.handler.__name__ for d in collected]}"
            )
            raise AssertionError(errmsg)

        # The original handler should no longer be in the registry
        originals = [
            d for d in collected
            if d.handler is handler_a
        ]

        if len(originals) > 0:
            errmsg = (
                f"Iteration {iteration}: After replace, registry should not contain "
                f"the original handler '{handler_a.__name__}'. "
                f"Found handlers: {[d.handler.__name__ for d in collected]}"
            )
            raise AssertionError(errmsg)

    EndpointRegistry.clear()
    return


def test_property_no_conflict_for_different_methods_same_path():
    """
        Property 9: Registration Error Handling - No False Conflicts

        *For any* two descriptors targeting the same path but different
        HTTP methods, the EndpointRegistry SHALL accept both registrations
        without raising an error.

        **Feature: endpoint-abstractions, Property 9: Registration Error Handling**
        **Validates: Requirements 2.5, 6.5**
    """
    for iteration in range(100):
        EndpointRegistry.clear()

        # Generate a random path
        use_path = random.choice([True, False])
        if use_path:
            location_path = generate_random_path()
            location_leaf = None
        else:
            location_leaf = generate_random_leaf()
            location_path = None

        # Pick two distinct methods
        method_pair = random.sample(VALID_HTTP_METHODS, k=2)

        handler_a = make_handler()
        handler_b = make_handler()

        desc_a = make_descriptor(
            handler=handler_a,
            leaf=location_leaf,
            path=location_path,
            methods=[method_pair[0]]
        )
        desc_b = make_descriptor(
            handler=handler_b,
            leaf=location_leaf,
            path=location_path,
            methods=[method_pair[1]]
        )

        # Both registrations should succeed without error
        try:
            EndpointRegistry.register(desc_a, on_conflict="error")
            EndpointRegistry.register(desc_b, on_conflict="error")
        except EndpointConflictError as exc:
            errmsg = (
                f"Iteration {iteration}: Different methods on same path should not "
                f"conflict. methods={method_pair}, path={location_path}, "
                f"leaf={location_leaf}. Got: {exc}"
            )
            raise AssertionError(errmsg)

        collected = EndpointRegistry.collect()
        if len(collected) != 2:
            errmsg = (
                f"Iteration {iteration}: Registry should contain 2 descriptors "
                f"for different methods on same path. Got {len(collected)}."
            )
            raise AssertionError(errmsg)

    EndpointRegistry.clear()
    return


def test_property_attach_at_with_leaf_or_path_succeeds():
    """
        Property 9: Registration Error Handling - Valid Registration

        *For any* attach_at call where at least one of leaf or path is
        provided, the registration SHALL succeed without raising
        EndpointRegistrationError (assuming no conflicts).

        **Feature: endpoint-abstractions, Property 9: Registration Error Handling**
        **Validates: Requirements 2.4**
    """
    for iteration in range(100):
        EndpointRegistry.clear()

        handler = make_handler()

        # Randomly choose to provide leaf, path, or both
        choice = random.choice(["leaf", "path", "both"])

        kwargs = {}
        if choice == "leaf":
            kwargs["leaf"] = generate_random_leaf()
        elif choice == "path":
            kwargs["path"] = generate_random_path()
        else:
            kwargs["leaf"] = generate_random_leaf()
            kwargs["path"] = generate_random_path()

        try:
            decorator = Endpoint.attach_at(**kwargs)
            result = decorator(handler)
        except EndpointRegistrationError as exc:
            errmsg = (
                f"Iteration {iteration}: attach_at with {choice} should not raise "
                f"EndpointRegistrationError. kwargs={kwargs}. Got: {exc}"
            )
            raise AssertionError(errmsg)

        # The decorator should return the original handler
        if result is not handler:
            errmsg = (
                f"Iteration {iteration}: attach_at should return the original "
                f"handler function."
            )
            raise AssertionError(errmsg)

    EndpointRegistry.clear()
    return
