"""
.. module:: test_descriptor_metadata_completeness_properties
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Property-based tests for descriptor metadata completeness.

.. moduleauthor:: Code Craft AI LLC

This module contains property-based tests for the EndpointRegistry,
validating Property 13: Descriptor Metadata Completeness across many
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
    registry = EndpointRegistry()
def _make_handler(iteration: int, suffix: str = ""):
    """Create a unique handler function for a given iteration."""
    def handler():
        return iteration
    handler.__name__ = f"handler_{suffix}_{iteration}"
    handler.__qualname__ = f"handler_{suffix}_{iteration}"
    return handler


# =============================================================================
# Property 13: Descriptor Metadata Completeness
# Feature: endpoint-abstractions, Property 13: Descriptor Metadata Completeness
# Validates: Requirements 11.1
# =============================================================================

def test_property_collect_descriptors_have_all_metadata_fields():
    """
        Property 13: Descriptor Metadata Completeness - Field Presence

        *For any* call to registry.collect(), each returned
        descriptor SHALL include all metadata fields: path (or leaf),
        methods, constraints (with access_policy, scopes, rate_limits,
        roles), version, tags, doc, handler, module, and extras.

        **Feature: endpoint-abstractions, Property 13: Descriptor Metadata Completeness**
        **Validates: Requirements 11.1**
    """
    registry = EndpointRegistry()
    for iteration in range(100):
        _clear_registry()

        handler = _make_handler(iteration, "meta")
        leaf = f"meta_{iteration}_{generate_random_leaf()}"
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

        descriptors = registry.collect()

        if len(descriptors) != 1:
            raise AssertionError(
                f"Iteration {iteration}: Expected 1 descriptor, got {len(descriptors)}"
            )

        desc = descriptors[0]

        # Verify descriptor is the correct type
        if not isinstance(desc, EndpointDescriptor):
            raise AssertionError(
                f"Iteration {iteration}: Collected item is not EndpointDescriptor, "
                f"got {type(desc).__name__}"
            )

        # Verify all top-level fields are present and accessible
        required_attrs = [
            "handler", "module", "leaf", "path", "methods",
            "version", "tags", "constraints", "doc", "extras"
        ]
        for attr in required_attrs:
            if not hasattr(desc, attr):
                raise AssertionError(
                    f"Iteration {iteration}: Descriptor missing attribute '{attr}'"
                )

        # Verify handler reference
        if desc.handler is not handler:
            raise AssertionError(
                f"Iteration {iteration}: handler reference mismatch"
            )

        # Verify module is a non-empty string
        if not isinstance(desc.module, str) or len(desc.module) == 0:
            raise AssertionError(
                f"Iteration {iteration}: module should be a non-empty string, "
                f"got '{desc.module}'"
            )

        # Verify leaf or path is set
        if desc.leaf is None and desc.path is None:
            raise AssertionError(
                f"Iteration {iteration}: Both leaf and path are None; "
                f"at least one must be set"
            )

        # Verify methods is a non-empty list
        if not isinstance(desc.methods, list) or len(desc.methods) == 0:
            raise AssertionError(
                f"Iteration {iteration}: methods should be a non-empty list, "
                f"got {desc.methods}"
            )

        # Verify constraints is an EndpointConstraints instance
        if not isinstance(desc.constraints, EndpointConstraints):
            raise AssertionError(
                f"Iteration {iteration}: constraints should be EndpointConstraints, "
                f"got {type(desc.constraints).__name__}"
            )

        # Verify constraints has all sub-fields
        constraints = desc.constraints
        for c_attr in ["access_policy", "rate_limit", "scopes", "roles"]:
            if not hasattr(constraints, c_attr):
                raise AssertionError(
                    f"Iteration {iteration}: constraints missing attribute '{c_attr}'"
                )

        # Verify scopes and roles are lists
        if not isinstance(constraints.scopes, list):
            raise AssertionError(
                f"Iteration {iteration}: constraints.scopes should be a list, "
                f"got {type(constraints.scopes).__name__}"
            )
        if not isinstance(constraints.roles, list):
            raise AssertionError(
                f"Iteration {iteration}: constraints.roles should be a list, "
                f"got {type(constraints.roles).__name__}"
            )

        # Verify tags is a list
        if not isinstance(desc.tags, list):
            raise AssertionError(
                f"Iteration {iteration}: tags should be a list, "
                f"got {type(desc.tags).__name__}"
            )

        # Verify extras is a dict
        if not isinstance(desc.extras, dict):
            raise AssertionError(
                f"Iteration {iteration}: extras should be a dict, "
                f"got {type(desc.extras).__name__}"
            )

    return


def test_property_collect_preserves_access_policy_in_constraints():
    """
        Property 13: Descriptor Metadata Completeness - Access Policy Consolidation

        *For any* endpoint registered with an access_policy, the descriptor
        returned by collect() SHALL include the access_policy within its
        constraints object, and the constraints scopes and roles SHALL
        reflect the policy values.

        **Feature: endpoint-abstractions, Property 13: Descriptor Metadata Completeness**
        **Validates: Requirements 11.1**
    """
    registry = EndpointRegistry()
    for iteration in range(100):
        _clear_registry()

        handler = _make_handler(iteration, "policy")
        leaf = f"policy_{iteration}_{generate_random_leaf()}"

        # Always generate a non-None policy for this test
        roles = [generate_random_string(3, 8) for _ in range(random.randint(1, 4))]
        scopes = [generate_random_string(3, 8) for _ in range(random.randint(1, 4))]
        require_auth = random.choice([True, False])
        access_policy = AccessPolicy(roles=roles, scopes=scopes, require_auth=require_auth)

        Endpoint.attach_at(
            leaf=leaf,
            access_policy=access_policy,
        )(handler)

        descriptors = registry.collect()
        desc = descriptors[0]

        # Verify access_policy is present in constraints
        if desc.constraints.access_policy is None:
            raise AssertionError(
                f"Iteration {iteration}: constraints.access_policy is None "
                f"but an access_policy was provided"
            )

        # Verify the policy values match
        if desc.constraints.access_policy.require_auth != require_auth:
            raise AssertionError(
                f"Iteration {iteration}: require_auth mismatch. "
                f"Expected {require_auth}, got {desc.constraints.access_policy.require_auth}"
            )

        # Verify roles are reflected in constraints
        for role in roles:
            if role not in desc.constraints.roles:
                raise AssertionError(
                    f"Iteration {iteration}: Role '{role}' from access_policy "
                    f"not found in constraints.roles: {desc.constraints.roles}"
                )

        # Verify scopes are reflected in constraints
        for scope in scopes:
            if scope not in desc.constraints.scopes:
                raise AssertionError(
                    f"Iteration {iteration}: Scope '{scope}' from access_policy "
                    f"not found in constraints.scopes: {desc.constraints.scopes}"
                )

    return


def test_property_collect_preserves_rate_limit_in_constraints():
    """
        Property 13: Descriptor Metadata Completeness - Rate Limit Consolidation

        *For any* endpoint registered with a rate_limit, the descriptor
        returned by collect() SHALL include the rate_limit within its
        constraints object with the correct requests and window values.

        **Feature: endpoint-abstractions, Property 13: Descriptor Metadata Completeness**
        **Validates: Requirements 11.1**
    """
    registry = EndpointRegistry()
    for iteration in range(100):
        _clear_registry()

        handler = _make_handler(iteration, "rlimit")
        leaf = f"rlimit_{iteration}_{generate_random_leaf()}"

        # Always generate a non-None rate limit for this test
        requests = random.randint(1, 1000)
        window = random.randint(1, 3600)
        rate_limit = RateLimit(requests=requests, window=window)

        Endpoint.attach_at(
            leaf=leaf,
            rate_limit=rate_limit,
        )(handler)

        descriptors = registry.collect()
        desc = descriptors[0]

        # Verify rate_limit is present in constraints
        if desc.constraints.rate_limit is None:
            raise AssertionError(
                f"Iteration {iteration}: constraints.rate_limit is None "
                f"but a rate_limit was provided"
            )

        if desc.constraints.rate_limit.requests != requests:
            raise AssertionError(
                f"Iteration {iteration}: rate_limit.requests mismatch. "
                f"Expected {requests}, got {desc.constraints.rate_limit.requests}"
            )

        if desc.constraints.rate_limit.window != window:
            raise AssertionError(
                f"Iteration {iteration}: rate_limit.window mismatch. "
                f"Expected {window}, got {desc.constraints.rate_limit.window}"
            )

    return


def test_property_collect_multiple_descriptors_all_complete():
    """
        Property 13: Descriptor Metadata Completeness - Multiple Endpoints

        *For any* set of N registered endpoints, collect() SHALL return
        N descriptors each with complete consolidated metadata including
        path, methods, access_policy, scopes, and rate_limits.

        **Feature: endpoint-abstractions, Property 13: Descriptor Metadata Completeness**
        **Validates: Requirements 11.1**
    """
    registry = EndpointRegistry()
    for iteration in range(100):
        _clear_registry()

        num_endpoints = random.randint(2, 5)
        registered = []

        for idx in range(num_endpoints):
            handler = _make_handler(iteration * 100 + idx, f"multi_{idx}")
            leaf = f"multi_{iteration}_{idx}_{generate_random_leaf()}"
            methods = generate_random_methods()
            access_policy = generate_random_access_policy()
            rate_limit = generate_random_rate_limit()
            tags = generate_random_tags()
            version = generate_random_string(2, 5) if random.choice([True, False]) else None
            doc = generate_random_doc()

            Endpoint.attach_at(
                leaf=leaf,
                methods=methods,
                access_policy=access_policy,
                rate_limit=rate_limit,
                tags=tags,
                version=version,
                doc=doc,
            )(handler)

            registered.append({
                "handler": handler,
                "leaf": leaf,
                "methods": methods,
                "access_policy": access_policy,
                "rate_limit": rate_limit,
                "tags": tags,
                "version": version,
            })

        descriptors = registry.collect()

        if len(descriptors) != num_endpoints:
            raise AssertionError(
                f"Iteration {iteration}: Expected {num_endpoints} descriptors, "
                f"got {len(descriptors)}"
            )

        for desc_idx, desc in enumerate(descriptors):
            # Every descriptor must be an EndpointDescriptor
            if not isinstance(desc, EndpointDescriptor):
                raise AssertionError(
                    f"Iteration {iteration}, descriptor {desc_idx}: "
                    f"Not an EndpointDescriptor, got {type(desc).__name__}"
                )

            # Every descriptor must have constraints
            if not isinstance(desc.constraints, EndpointConstraints):
                raise AssertionError(
                    f"Iteration {iteration}, descriptor {desc_idx}: "
                    f"constraints is not EndpointConstraints"
                )

            # Every descriptor must have a non-empty methods list
            if not desc.methods:
                raise AssertionError(
                    f"Iteration {iteration}, descriptor {desc_idx}: "
                    f"methods is empty"
                )

            # Every descriptor must have leaf or path
            if desc.leaf is None and desc.path is None:
                raise AssertionError(
                    f"Iteration {iteration}, descriptor {desc_idx}: "
                    f"Both leaf and path are None"
                )

            # Every descriptor must have a handler
            if desc.handler is None:
                raise AssertionError(
                    f"Iteration {iteration}, descriptor {desc_idx}: "
                    f"handler is None"
                )

            # Constraints sub-fields must be proper types
            if not isinstance(desc.constraints.scopes, list):
                raise AssertionError(
                    f"Iteration {iteration}, descriptor {desc_idx}: "
                    f"constraints.scopes is not a list"
                )
            if not isinstance(desc.constraints.roles, list):
                raise AssertionError(
                    f"Iteration {iteration}, descriptor {desc_idx}: "
                    f"constraints.roles is not a list"
                )

    return


def test_property_collect_no_policy_yields_empty_scopes_and_roles():
    """
        Property 13: Descriptor Metadata Completeness - No Policy Defaults

        *For any* endpoint registered without an access_policy, the
        descriptor returned by collect() SHALL have constraints with
        empty scopes and roles lists and access_policy set to None.

        **Feature: endpoint-abstractions, Property 13: Descriptor Metadata Completeness**
        **Validates: Requirements 11.1**
    """
    registry = EndpointRegistry()
    for iteration in range(100):
        _clear_registry()

        handler = _make_handler(iteration, "nopol")
        leaf = f"nopol_{iteration}_{generate_random_leaf()}"

        Endpoint.attach_at(leaf=leaf)(handler)

        descriptors = registry.collect()
        desc = descriptors[0]

        if desc.constraints.access_policy is not None:
            raise AssertionError(
                f"Iteration {iteration}: access_policy should be None "
                f"when not provided, got {desc.constraints.access_policy}"
            )

        if desc.constraints.scopes != []:
            raise AssertionError(
                f"Iteration {iteration}: scopes should be empty list "
                f"when no policy, got {desc.constraints.scopes}"
            )

        if desc.constraints.roles != []:
            raise AssertionError(
                f"Iteration {iteration}: roles should be empty list "
                f"when no policy, got {desc.constraints.roles}"
            )

        if desc.constraints.rate_limit is not None:
            raise AssertionError(
                f"Iteration {iteration}: rate_limit should be None "
                f"when not provided, got {desc.constraints.rate_limit}"
            )

    return


def test_property_collect_security_row_has_all_columns():
    """
        Property 13: Descriptor Metadata Completeness - Security Row

        *For any* descriptor returned by collect(), calling to_security_row()
        SHALL produce a dictionary with all required columns: path, methods,
        handler, access_policy, scopes, roles, rate_limit, and summary.

        **Feature: endpoint-abstractions, Property 13: Descriptor Metadata Completeness**
        **Validates: Requirements 11.1**
    """
    registry = EndpointRegistry()
    required_columns = [
        "path", "methods", "handler", "access_policy",
        "scopes", "roles", "rate_limit", "summary"
    ]

    for iteration in range(100):
        _clear_registry()

        handler = _make_handler(iteration, "secrow")
        leaf = f"secrow_{iteration}_{generate_random_leaf()}"
        methods = generate_random_methods()
        access_policy = generate_random_access_policy()
        rate_limit = generate_random_rate_limit()
        doc = generate_random_doc()

        Endpoint.attach_at(
            leaf=leaf,
            methods=methods,
            access_policy=access_policy,
            rate_limit=rate_limit,
            doc=doc,
        )(handler)

        descriptors = registry.collect()
        desc = descriptors[0]

        row = desc.to_security_row()

        if not isinstance(row, dict):
            raise AssertionError(
                f"Iteration {iteration}: to_security_row() should return a dict, "
                f"got {type(row).__name__}"
            )

        for col in required_columns:
            if col not in row:
                raise AssertionError(
                    f"Iteration {iteration}: Security row missing column '{col}'. "
                    f"Available keys: {list(row.keys())}"
                )

        # Verify path is derived from leaf
        expected_path = f"/{leaf}"
        if row["path"] != expected_path:
            raise AssertionError(
                f"Iteration {iteration}: Security row path mismatch. "
                f"Expected '{expected_path}', got '{row['path']}'"
            )

        # Verify methods column is a string representation
        if not isinstance(row["methods"], str):
            raise AssertionError(
                f"Iteration {iteration}: Security row methods should be a string, "
                f"got {type(row['methods']).__name__}"
            )

    return
