"""
.. module:: test_descriptor_emission_properties
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Property-based tests for descriptor emission.

.. moduleauthor:: Code Craft AI LLC

This module contains property-based tests for the Endpoint class,
validating Property 3: Descriptor Emission across many generated inputs.
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
    EndpointConstraints,
    EndpointDescriptor,
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


def _make_handler(iteration: int, suffix: str = ""):
    """Create a unique handler function for a given iteration."""
    def handler():
        return iteration
    handler.__name__ = f"handler_{suffix}_{iteration}"
    handler.__qualname__ = f"handler_{suffix}_{iteration}"
    return handler


def _create_subclass(iteration: int, attrs: Dict[str, Any]) -> type:
    """Create a unique Endpoint subclass with the given class attributes."""
    return type(f"EmissionEndpoint_{iteration}", (Endpoint,), dict(attrs))



# =============================================================================
# Property 3: Descriptor Emission
# Feature: endpoint-abstractions, Property 3: Descriptor Emission
# Validates: Requirements 4.1, 6.1
# =============================================================================

def test_property_attach_at_emits_descriptor_to_registry():
    """
        Property 3: Descriptor Emission - attach_at Registration

        *For any* attach_at call, an EndpointDescriptor SHALL be emitted
        to the EndpointRegistry containing the handler reference and merged
        metadata from both class attributes and call kwargs.

        **Feature: endpoint-abstractions, Property 3: Descriptor Emission**
        **Validates: Requirements 4.1, 6.1**
    """
    for iteration in range(100):
        _clear_registry()

        handler = _make_handler(iteration, "emit")
        leaf = f"emit_{iteration}_{generate_random_leaf()}"
        methods = generate_random_methods()
        tags = generate_random_tags()
        version = generate_random_string(2, 5) if random.choice([True, False]) else None
        access_policy = generate_random_access_policy()
        rate_limit = generate_random_rate_limit()
        doc = generate_random_doc()

        Endpoint.attach_at(
            leaf=leaf,
            methods=methods,
            tags=tags,
            version=version,
            access_policy=access_policy,
            rate_limit=rate_limit,
            doc=doc,
        )(handler)

        descriptors = EndpointRegistry.collect()

        if len(descriptors) != 1:
            raise AssertionError(
                f"Iteration {iteration}: Expected exactly 1 descriptor in registry, "
                f"got {len(descriptors)}"
            )

        desc = descriptors[0]

        if not isinstance(desc, EndpointDescriptor):
            raise AssertionError(
                f"Iteration {iteration}: Registry entry is not an EndpointDescriptor, "
                f"got {type(desc).__name__}"
            )

        if desc.handler is not handler:
            raise AssertionError(
                f"Iteration {iteration}: Descriptor handler is not the original handler. "
                f"Expected handler_{iteration}, got {desc.handler.__name__}"
            )

        if desc.leaf != leaf:
            raise AssertionError(
                f"Iteration {iteration}: Descriptor leaf mismatch. "
                f"Expected '{leaf}', got '{desc.leaf}'"
            )

        if desc.methods != methods:
            raise AssertionError(
                f"Iteration {iteration}: Descriptor methods mismatch. "
                f"Expected {methods}, got {desc.methods}"
            )

        if desc.tags != tags:
            raise AssertionError(
                f"Iteration {iteration}: Descriptor tags mismatch. "
                f"Expected {tags}, got {desc.tags}"
            )

        if desc.version != version:
            raise AssertionError(
                f"Iteration {iteration}: Descriptor version mismatch. "
                f"Expected '{version}', got '{desc.version}'"
            )

        if desc.doc is not doc:
            raise AssertionError(
                f"Iteration {iteration}: Descriptor doc is not the original doc object"
            )

    return


def test_property_attach_at_emits_descriptor_with_merged_class_attrs():
    """
        Property 3: Descriptor Emission - Merged Class Attributes

        *For any* Endpoint subclass with class-level attributes, attach_at
        SHALL emit a descriptor containing merged metadata from both class
        attributes and call kwargs.

        **Feature: endpoint-abstractions, Property 3: Descriptor Emission**
        **Validates: Requirements 4.1, 6.1**
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

        handler = _make_handler(iteration, "merged")
        leaf = f"merged_{iteration}_{generate_random_leaf()}"

        # Randomly decide which kwargs to override
        kwargs: Dict[str, Any] = {"leaf": leaf}
        override_methods = None
        override_tags = None
        override_version = None

        if random.choice([True, False]):
            override_methods = generate_random_methods()
            kwargs["methods"] = override_methods

        if random.choice([True, False]):
            override_tags = generate_random_tags()
            kwargs["tags"] = override_tags

        if random.choice([True, False]):
            override_version = generate_random_string(2, 5) + "_ov"
            kwargs["version"] = override_version

        SubEndpoint.attach_at(**kwargs)(handler)

        descriptors = EndpointRegistry.collect()

        if len(descriptors) != 1:
            raise AssertionError(
                f"Iteration {iteration}: Expected 1 descriptor, got {len(descriptors)}"
            )

        desc = descriptors[0]

        # Verify handler reference
        if desc.handler is not handler:
            raise AssertionError(
                f"Iteration {iteration}: Descriptor handler is not the original handler"
            )

        # Verify merged methods
        expected_methods = override_methods if override_methods is not None else class_methods
        if desc.methods != expected_methods:
            raise AssertionError(
                f"Iteration {iteration}: methods mismatch. "
                f"Expected {expected_methods}, got {desc.methods}"
            )

        # Verify merged tags
        expected_tags = override_tags if override_tags is not None else class_tags
        if desc.tags != expected_tags:
            raise AssertionError(
                f"Iteration {iteration}: tags mismatch. "
                f"Expected {expected_tags}, got {desc.tags}"
            )

        # Verify merged version
        expected_version = override_version if override_version is not None else class_version
        if desc.version != expected_version:
            raise AssertionError(
                f"Iteration {iteration}: version mismatch. "
                f"Expected '{expected_version}', got '{desc.version}'"
            )

    return


def test_property_attach_at_with_path_emits_descriptor():
    """
        Property 3: Descriptor Emission - Path Parameter

        *For any* attach_at call using the path parameter instead of leaf,
        an EndpointDescriptor SHALL be emitted to the registry with the
        correct path value.

        **Feature: endpoint-abstractions, Property 3: Descriptor Emission**
        **Validates: Requirements 4.1, 6.1**
    """
    for iteration in range(100):
        _clear_registry()

        handler = _make_handler(iteration, "path")
        segments = [generate_random_string(3, 8) for _ in range(random.randint(1, 4))]
        path = "/" + "/".join(segments) + f"/{iteration}"
        methods = generate_random_methods()

        Endpoint.attach_at(path=path, methods=methods)(handler)

        descriptors = EndpointRegistry.collect()

        if len(descriptors) != 1:
            raise AssertionError(
                f"Iteration {iteration}: Expected 1 descriptor, got {len(descriptors)}"
            )

        desc = descriptors[0]

        if desc.handler is not handler:
            raise AssertionError(
                f"Iteration {iteration}: Descriptor handler is not the original handler"
            )

        if desc.path != path:
            raise AssertionError(
                f"Iteration {iteration}: Descriptor path mismatch. "
                f"Expected '{path}', got '{desc.path}'"
            )

        if desc.methods != methods:
            raise AssertionError(
                f"Iteration {iteration}: Descriptor methods mismatch. "
                f"Expected {methods}, got {desc.methods}"
            )

    return


def test_property_each_attach_at_call_adds_one_descriptor():
    """
        Property 3: Descriptor Emission - Accumulation

        *For any* sequence of N attach_at calls, the EndpointRegistry
        SHALL contain exactly N descriptors, each corresponding to one
        call.

        **Feature: endpoint-abstractions, Property 3: Descriptor Emission**
        **Validates: Requirements 4.1, 6.1**
    """
    for iteration in range(100):
        _clear_registry()

        num_handlers = random.randint(1, 6)
        handlers = []

        for idx in range(num_handlers):
            handler = _make_handler(iteration * 100 + idx, f"accum_{idx}")
            leaf = f"accum_{iteration}_{idx}_{generate_random_leaf()}"
            Endpoint.attach_at(leaf=leaf)(handler)
            handlers.append(handler)

        descriptors = EndpointRegistry.collect()

        if len(descriptors) != num_handlers:
            raise AssertionError(
                f"Iteration {iteration}: Expected {num_handlers} descriptors, "
                f"got {len(descriptors)}"
            )

        # Verify each handler appears in the descriptors
        descriptor_handlers = [d.handler for d in descriptors]
        for idx, handler in enumerate(handlers):
            if handler not in descriptor_handlers:
                raise AssertionError(
                    f"Iteration {iteration}: Handler {idx} not found in "
                    f"registry descriptors"
                )

    return


def test_property_descriptor_has_constraints_object():
    """
        Property 3: Descriptor Emission - Constraints Structure

        *For any* attach_at call, the emitted descriptor SHALL contain
        a properly structured EndpointConstraints object with the merged
        access_policy and rate_limit values.

        **Feature: endpoint-abstractions, Property 3: Descriptor Emission**
        **Validates: Requirements 4.1, 6.1**
    """
    for iteration in range(100):
        _clear_registry()

        handler = _make_handler(iteration, "constraints")
        leaf = f"constr_{iteration}_{generate_random_leaf()}"
        access_policy = generate_random_access_policy()
        rate_limit = generate_random_rate_limit()

        Endpoint.attach_at(
            leaf=leaf,
            access_policy=access_policy,
            rate_limit=rate_limit,
        )(handler)

        descriptors = EndpointRegistry.collect()
        desc = descriptors[0]

        if not isinstance(desc.constraints, EndpointConstraints):
            raise AssertionError(
                f"Iteration {iteration}: Descriptor constraints is not an "
                f"EndpointConstraints, got {type(desc.constraints).__name__}"
            )

        if desc.constraints.access_policy is not access_policy:
            raise AssertionError(
                f"Iteration {iteration}: Constraints access_policy does not "
                f"match the provided policy"
            )

        if desc.constraints.rate_limit is not rate_limit:
            raise AssertionError(
                f"Iteration {iteration}: Constraints rate_limit does not "
                f"match the provided rate_limit"
            )

        # Verify scopes and roles are derived from access_policy.
        # AccessPolicy stores roles/scopes as tuples; EndpointConstraints
        # stores them as lists. Compare via list() coercion at the
        # assertion boundary.
        if access_policy is not None:
            if desc.constraints.scopes != list(access_policy.scopes):
                raise AssertionError(
                    f"Iteration {iteration}: Constraints scopes mismatch. "
                    f"Expected {list(access_policy.scopes)}, got {desc.constraints.scopes}"
                )
            if desc.constraints.roles != list(access_policy.roles):
                raise AssertionError(
                    f"Iteration {iteration}: Constraints roles mismatch. "
                    f"Expected {list(access_policy.roles)}, got {desc.constraints.roles}"
                )
        else:
            if desc.constraints.scopes != []:
                raise AssertionError(
                    f"Iteration {iteration}: Constraints scopes should be empty "
                    f"when no access_policy, got {desc.constraints.scopes}"
                )
            if desc.constraints.roles != []:
                raise AssertionError(
                    f"Iteration {iteration}: Constraints roles should be empty "
                    f"when no access_policy, got {desc.constraints.roles}"
                )

    return


def test_property_attach_child_emits_descriptor():
    """
        Property 3: Descriptor Emission - attach_child

        *For any* attach_child call, an EndpointDescriptor SHALL be
        returned containing the child handler reference and merged
        metadata from both parent and child.

        **Feature: endpoint-abstractions, Property 3: Descriptor Emission**
        **Validates: Requirements 4.1, 6.1**
    """
    for iteration in range(100):
        _clear_registry()

        # Create parent with base_path
        parent_base_path = f"/api/v{random.randint(1, 5)}"
        parent_tags = generate_random_tags()
        parent_version = generate_random_string(2, 5)
        parent_policy = generate_random_access_policy()

        Parent = _create_subclass(iteration, {
            "base_path": parent_base_path,
            "tags": parent_tags,
            "version": parent_version,
            "access_policy": parent_policy,
        })

        # Create child endpoint
        child_leaf = generate_random_leaf()
        child_methods = generate_random_methods()

        Child = type(f"ChildEndpoint_{iteration}", (Endpoint,), {
            "methods": child_methods,
            "base_leaf": child_leaf,
            "__module__": "test_module",
        })

        descriptor = Parent.attach_child(Child)

        if not isinstance(descriptor, EndpointDescriptor):
            raise AssertionError(
                f"Iteration {iteration}: attach_child did not return an "
                f"EndpointDescriptor, got {type(descriptor).__name__}"
            )

        if descriptor.methods != child_methods:
            raise AssertionError(
                f"Iteration {iteration}: Child methods mismatch. "
                f"Expected {child_methods}, got {descriptor.methods}"
            )

        # Verify the path is composed from parent base + child leaf
        expected_path = f"{parent_base_path}/{child_leaf}"
        if descriptor.path != expected_path:
            raise AssertionError(
                f"Iteration {iteration}: Composed path mismatch. "
                f"Expected '{expected_path}', got '{descriptor.path}'"
            )

    return


def test_property_descriptor_module_matches_handler():
    """
        Property 3: Descriptor Emission - Module Tracking

        *For any* attach_at call, the emitted descriptor SHALL record
        the handler's __module__ attribute so the endpoint can be traced
        back to its source.

        **Feature: endpoint-abstractions, Property 3: Descriptor Emission**
        **Validates: Requirements 4.1, 6.1**
    """
    for iteration in range(100):
        _clear_registry()

        handler = _make_handler(iteration, "module")
        leaf = f"mod_{iteration}_{generate_random_leaf()}"

        Endpoint.attach_at(leaf=leaf)(handler)

        descriptors = EndpointRegistry.collect()
        desc = descriptors[0]

        if desc.module != handler.__module__:
            raise AssertionError(
                f"Iteration {iteration}: Descriptor module mismatch. "
                f"Expected '{handler.__module__}', got '{desc.module}'"
            )

    return
