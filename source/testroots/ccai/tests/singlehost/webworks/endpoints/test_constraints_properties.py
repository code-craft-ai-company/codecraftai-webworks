"""
.. module:: test_constraints_properties
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Property-based tests for EndpointConstraints inheritance behavior.

.. moduleauthor:: Code Craft AI LLC

This module contains property-based tests for the EndpointConstraints class,
validating Property 5: Constraint Inheritance across many generated inputs.
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []

import random
import string
from typing import List

from ccai.webworks.endpoints.accesspolicy import AccessPolicy
from ccai.webworks.endpoints.constraints import EndpointConstraints
from ccai.webworks.endpoints.ratelimit import RateLimit


# =============================================================================
# Helper Functions for Generating Random Test Data
# =============================================================================

def generate_random_string(min_len: int = 3, max_len: int = 10) -> str:
    """Generate a random alphanumeric string."""
    length = random.randint(min_len, max_len)
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))


def generate_random_string_list(max_items: int = 4) -> List[str]:
    """Generate a random list of unique strings."""
    num_items = random.randint(0, max_items)
    return list({generate_random_string() for _ in range(num_items)})


def generate_random_access_policy() -> AccessPolicy:
    """Generate a random AccessPolicy."""
    return AccessPolicy(
        roles=generate_random_string_list(4),
        scopes=generate_random_string_list(4),
        require_auth=random.choice([True, False])
    )


def generate_random_rate_limit() -> RateLimit:
    """Generate a random RateLimit with positive values."""
    return RateLimit(
        requests=random.randint(1, 10000),
        window=random.randint(1, 3600)
    )


def generate_random_constraints(
    allow_none_policy: bool = True,
    allow_none_rate_limit: bool = True
) -> EndpointConstraints:
    """Generate a random EndpointConstraints object."""
    if allow_none_policy:
        access_policy = random.choice([None, generate_random_access_policy()])
    else:
        access_policy = generate_random_access_policy()

    if allow_none_rate_limit:
        rate_limit = random.choice([None, generate_random_rate_limit()])
    else:
        rate_limit = generate_random_rate_limit()

    return EndpointConstraints(
        access_policy=access_policy,
        rate_limit=rate_limit,
        scopes=generate_random_string_list(4),
        roles=generate_random_string_list(4)
    )


def requests_per_second(limit: RateLimit) -> float:
    """Calculate the requests-per-second ratio for a rate limit."""
    if limit.window == 0:
        return float('inf')
    return limit.requests / limit.window



# =============================================================================
# Property 5: Constraint Inheritance
# Feature: endpoint-abstractions, Property 5: Constraint Inheritance
# Validates: Requirements 3.6, 6.7, 7.1, 7.2, 7.3, 9.4, 10.6
# =============================================================================

def test_property_child_inherits_parent_access_policy_when_unset():
    """
        Property 5: Constraint Inheritance - Access Policy Inheritance

        *For any* parent with an access_policy and a child with no
        access_policy, the merged constraints SHALL inherit the parent's
        access_policy.

        **Feature: endpoint-abstractions, Property 5: Constraint Inheritance**
        **Validates: Requirements 7.1, 7.2**
    """
    for iteration in range(100):
        parent = generate_random_constraints(allow_none_policy=False)
        child = EndpointConstraints(
            access_policy=None,
            rate_limit=random.choice([None, generate_random_rate_limit()]),
            scopes=generate_random_string_list(4),
            roles=generate_random_string_list(4)
        )

        merged = EndpointConstraints.merge(parent, child)

        # Child has no policy, so merged should inherit parent's policy
        if merged.access_policy is None:
            errmsg = (
                f"Iteration {iteration}: Merged access_policy should inherit "
                f"parent policy when child has none. "
                f"parent.access_policy={parent.access_policy}, "
                f"merged.access_policy={merged.access_policy}"
            )
            raise AssertionError(errmsg)

        if merged.access_policy.require_auth != parent.access_policy.require_auth:
            errmsg = (
                f"Iteration {iteration}: Inherited access_policy.require_auth "
                f"does not match parent. "
                f"parent={parent.access_policy.require_auth}, "
                f"merged={merged.access_policy.require_auth}"
            )
            raise AssertionError(errmsg)

        # Parent roles should be present in inherited policy
        for role in parent.access_policy.roles:
            if role not in merged.access_policy.roles:
                errmsg = (
                    f"Iteration {iteration}: Inherited policy missing parent role. "
                    f"role={role}, parent.roles={parent.access_policy.roles}, "
                    f"merged.roles={merged.access_policy.roles}"
                )
                raise AssertionError(errmsg)

    return


def test_property_child_overrides_parent_access_policy_when_set():
    """
        Property 5: Constraint Inheritance - Access Policy Override

        *For any* parent and child both with access_policy set, the
        merged constraints SHALL combine both policies (child overrides
        parent) following the merge_with rules.

        **Feature: endpoint-abstractions, Property 5: Constraint Inheritance**
        **Validates: Requirements 7.1, 7.3**
    """
    for iteration in range(100):
        parent = generate_random_constraints(allow_none_policy=False)
        child = generate_random_constraints(allow_none_policy=False)

        merged = EndpointConstraints.merge(parent, child)

        if merged.access_policy is None:
            errmsg = (
                f"Iteration {iteration}: Merged access_policy should not be None "
                f"when both parent and child have policies."
            )
            raise AssertionError(errmsg)

        # The merged policy should be the result of parent.merge_with(child)
        expected_policy = parent.access_policy.merge_with(child.access_policy)

        if set(merged.access_policy.roles) != set(expected_policy.roles):
            errmsg = (
                f"Iteration {iteration}: Merged policy roles do not match expected. "
                f"parent.roles={parent.access_policy.roles}, "
                f"child.roles={child.access_policy.roles}, "
                f"merged.roles={merged.access_policy.roles}, "
                f"expected.roles={expected_policy.roles}"
            )
            raise AssertionError(errmsg)

        if set(merged.access_policy.scopes) != set(expected_policy.scopes):
            errmsg = (
                f"Iteration {iteration}: Merged policy scopes do not match expected. "
                f"parent.scopes={parent.access_policy.scopes}, "
                f"child.scopes={child.access_policy.scopes}, "
                f"merged.scopes={merged.access_policy.scopes}, "
                f"expected.scopes={expected_policy.scopes}"
            )
            raise AssertionError(errmsg)

        if merged.access_policy.require_auth != expected_policy.require_auth:
            errmsg = (
                f"Iteration {iteration}: Merged require_auth does not match expected. "
                f"parent={parent.access_policy.require_auth}, "
                f"child={child.access_policy.require_auth}, "
                f"merged={merged.access_policy.require_auth}, "
                f"expected={expected_policy.require_auth}"
            )
            raise AssertionError(errmsg)

    return


def test_property_child_inherits_parent_rate_limit_when_unset():
    """
        Property 5: Constraint Inheritance - Rate Limit Inheritance

        *For any* parent with a rate_limit and a child with no rate_limit,
        the merged constraints SHALL inherit the parent's rate_limit.

        **Feature: endpoint-abstractions, Property 5: Constraint Inheritance**
        **Validates: Requirements 7.1, 7.2**
    """
    for iteration in range(100):
        parent = EndpointConstraints(
            access_policy=None,
            rate_limit=generate_random_rate_limit(),
            scopes=[],
            roles=[]
        )
        child = EndpointConstraints(
            access_policy=None,
            rate_limit=None,
            scopes=[],
            roles=[]
        )

        merged = EndpointConstraints.merge(parent, child)

        # Child has no rate_limit, so merged should inherit parent's
        if merged.rate_limit is None:
            errmsg = (
                f"Iteration {iteration}: Merged rate_limit should inherit "
                f"parent rate_limit when child has none. "
                f"parent.rate_limit={parent.rate_limit}"
            )
            raise AssertionError(errmsg)

        if merged.rate_limit.requests != parent.rate_limit.requests:
            errmsg = (
                f"Iteration {iteration}: Inherited rate_limit.requests "
                f"does not match parent. "
                f"parent={parent.rate_limit.requests}, "
                f"merged={merged.rate_limit.requests}"
            )
            raise AssertionError(errmsg)

        if merged.rate_limit.window != parent.rate_limit.window:
            errmsg = (
                f"Iteration {iteration}: Inherited rate_limit.window "
                f"does not match parent. "
                f"parent={parent.rate_limit.window}, "
                f"merged={merged.rate_limit.window}"
            )
            raise AssertionError(errmsg)

    return


def test_property_rate_limit_most_restrictive_when_both_set():
    """
        Property 5: Constraint Inheritance - Rate Limit Most Restrictive

        *For any* parent and child both with rate_limit set, the merged
        constraints SHALL use the most restrictive rate limit.

        **Feature: endpoint-abstractions, Property 5: Constraint Inheritance**
        **Validates: Requirements 7.1, 7.3**
    """
    for iteration in range(100):
        parent = EndpointConstraints(
            access_policy=None,
            rate_limit=generate_random_rate_limit(),
            scopes=[],
            roles=[]
        )
        child = EndpointConstraints(
            access_policy=None,
            rate_limit=generate_random_rate_limit(),
            scopes=[],
            roles=[]
        )

        merged = EndpointConstraints.merge(parent, child)

        if merged.rate_limit is None:
            errmsg = (
                f"Iteration {iteration}: Merged rate_limit should not be None "
                f"when both parent and child have rate limits."
            )
            raise AssertionError(errmsg)

        parent_rps = requests_per_second(parent.rate_limit)
        child_rps = requests_per_second(child.rate_limit)
        merged_rps = requests_per_second(merged.rate_limit)
        expected_rps = min(parent_rps, child_rps)

        if abs(merged_rps - expected_rps) > 1e-12:
            errmsg = (
                f"Iteration {iteration}: Merged rate_limit should be the most "
                f"restrictive. parent={parent.rate_limit} (rps={parent_rps}), "
                f"child={child.rate_limit} (rps={child_rps}), "
                f"merged={merged.rate_limit} (rps={merged_rps}), "
                f"expected_rps={expected_rps}"
            )
            raise AssertionError(errmsg)

    return


def test_property_scopes_union_by_default():
    """
        Property 5: Constraint Inheritance - Scopes Union Default

        *For any* parent and child with scopes, the merged scopes SHALL
        be the union of both scope lists by default (replace_scopes=False).

        **Feature: endpoint-abstractions, Property 5: Constraint Inheritance**
        **Validates: Requirements 7.1, 7.2, 7.3**
    """
    for iteration in range(100):
        parent = EndpointConstraints(
            access_policy=None,
            rate_limit=None,
            scopes=generate_random_string_list(4),
            roles=[]
        )
        child = EndpointConstraints(
            access_policy=None,
            rate_limit=None,
            scopes=generate_random_string_list(4),
            roles=[]
        )

        merged = EndpointConstraints.merge(parent, child, replace_scopes=False)

        # All parent scopes must be present
        for scope in parent.scopes:
            if scope not in merged.scopes:
                errmsg = (
                    f"Iteration {iteration}: Merged scopes missing parent scope. "
                    f"scope={scope}, parent.scopes={parent.scopes}, "
                    f"merged.scopes={merged.scopes}"
                )
                raise AssertionError(errmsg)

        # All child scopes must be present
        for scope in child.scopes:
            if scope not in merged.scopes:
                errmsg = (
                    f"Iteration {iteration}: Merged scopes missing child scope. "
                    f"scope={scope}, child.scopes={child.scopes}, "
                    f"merged.scopes={merged.scopes}"
                )
                raise AssertionError(errmsg)

        # No duplicates
        if len(merged.scopes) != len(set(merged.scopes)):
            errmsg = (
                f"Iteration {iteration}: Merged scopes contain duplicates. "
                f"merged.scopes={merged.scopes}"
            )
            raise AssertionError(errmsg)

    return


def test_property_roles_union_by_default():
    """
        Property 5: Constraint Inheritance - Roles Union Default

        *For any* parent and child with roles, the merged roles SHALL
        be the union of both role lists by default (replace_roles=False).

        **Feature: endpoint-abstractions, Property 5: Constraint Inheritance**
        **Validates: Requirements 7.1, 7.2, 7.3**
    """
    for iteration in range(100):
        parent = EndpointConstraints(
            access_policy=None,
            rate_limit=None,
            scopes=[],
            roles=generate_random_string_list(4)
        )
        child = EndpointConstraints(
            access_policy=None,
            rate_limit=None,
            scopes=[],
            roles=generate_random_string_list(4)
        )

        merged = EndpointConstraints.merge(parent, child, replace_roles=False)

        # All parent roles must be present
        for role in parent.roles:
            if role not in merged.roles:
                errmsg = (
                    f"Iteration {iteration}: Merged roles missing parent role. "
                    f"role={role}, parent.roles={parent.roles}, "
                    f"merged.roles={merged.roles}"
                )
                raise AssertionError(errmsg)

        # All child roles must be present
        for role in child.roles:
            if role not in merged.roles:
                errmsg = (
                    f"Iteration {iteration}: Merged roles missing child role. "
                    f"role={role}, child.roles={child.roles}, "
                    f"merged.roles={merged.roles}"
                )
                raise AssertionError(errmsg)

        # No duplicates
        if len(merged.roles) != len(set(merged.roles)):
            errmsg = (
                f"Iteration {iteration}: Merged roles contain duplicates. "
                f"merged.roles={merged.roles}"
            )
            raise AssertionError(errmsg)

    return



def test_property_scopes_replace_when_flag_set():
    """
        Property 5: Constraint Inheritance - Scopes Replace

        *For any* parent and child with scopes, when replace_scopes=True
        the merged scopes SHALL be exactly the child's scopes.

        **Feature: endpoint-abstractions, Property 5: Constraint Inheritance**
        **Validates: Requirements 7.1, 7.3**
    """
    for iteration in range(100):
        parent = EndpointConstraints(
            access_policy=None,
            rate_limit=None,
            scopes=generate_random_string_list(4),
            roles=[]
        )
        child = EndpointConstraints(
            access_policy=None,
            rate_limit=None,
            scopes=generate_random_string_list(4),
            roles=[]
        )

        merged = EndpointConstraints.merge(parent, child, replace_scopes=True)

        if merged.scopes != child.scopes:
            errmsg = (
                f"Iteration {iteration}: With replace_scopes=True, merged scopes "
                f"should equal child scopes. "
                f"child.scopes={child.scopes}, merged.scopes={merged.scopes}"
            )
            raise AssertionError(errmsg)

    return


def test_property_roles_replace_when_flag_set():
    """
        Property 5: Constraint Inheritance - Roles Replace

        *For any* parent and child with roles, when replace_roles=True
        the merged roles SHALL be exactly the child's roles.

        **Feature: endpoint-abstractions, Property 5: Constraint Inheritance**
        **Validates: Requirements 7.1, 7.3**
    """
    for iteration in range(100):
        parent = EndpointConstraints(
            access_policy=None,
            rate_limit=None,
            scopes=[],
            roles=generate_random_string_list(4)
        )
        child = EndpointConstraints(
            access_policy=None,
            rate_limit=None,
            scopes=[],
            roles=generate_random_string_list(4)
        )

        merged = EndpointConstraints.merge(parent, child, replace_roles=True)

        if merged.roles != child.roles:
            errmsg = (
                f"Iteration {iteration}: With replace_roles=True, merged roles "
                f"should equal child roles. "
                f"child.roles={child.roles}, merged.roles={merged.roles}"
            )
            raise AssertionError(errmsg)

    return


def test_property_both_none_constraints_merge_to_none():
    """
        Property 5: Constraint Inheritance - Both None

        *For any* parent and child where both access_policy and rate_limit
        are None, the merged constraints SHALL also have None for those fields.

        **Feature: endpoint-abstractions, Property 5: Constraint Inheritance**
        **Validates: Requirements 7.1, 7.2**
    """
    for iteration in range(100):
        parent = EndpointConstraints(
            access_policy=None,
            rate_limit=None,
            scopes=generate_random_string_list(4),
            roles=generate_random_string_list(4)
        )
        child = EndpointConstraints(
            access_policy=None,
            rate_limit=None,
            scopes=generate_random_string_list(4),
            roles=generate_random_string_list(4)
        )

        merged = EndpointConstraints.merge(parent, child)

        if merged.access_policy is not None:
            errmsg = (
                f"Iteration {iteration}: Merged access_policy should be None "
                f"when both parent and child are None. "
                f"merged.access_policy={merged.access_policy}"
            )
            raise AssertionError(errmsg)

        if merged.rate_limit is not None:
            errmsg = (
                f"Iteration {iteration}: Merged rate_limit should be None "
                f"when both parent and child are None. "
                f"merged.rate_limit={merged.rate_limit}"
            )
            raise AssertionError(errmsg)

    return


def test_property_merge_does_not_mutate_inputs():
    """
        Property 5: Constraint Inheritance - Immutability

        *For any* parent and child constraints, merging SHALL return a
        new EndpointConstraints instance without modifying either input.

        **Feature: endpoint-abstractions, Property 5: Constraint Inheritance**
        **Validates: Requirements 3.6, 10.6**
    """
    for iteration in range(100):
        parent = generate_random_constraints()
        child = generate_random_constraints()

        # Snapshot original values
        parent_scopes_before = list(parent.scopes)
        parent_roles_before = list(parent.roles)
        parent_policy_before = parent.access_policy
        parent_rate_before = parent.rate_limit
        child_scopes_before = list(child.scopes)
        child_roles_before = list(child.roles)
        child_policy_before = child.access_policy
        child_rate_before = child.rate_limit

        merged = EndpointConstraints.merge(parent, child)

        # Merged must be a different object
        if merged is parent:
            errmsg = f"Iteration {iteration}: Merged is the same object as parent."
            raise AssertionError(errmsg)

        if merged is child:
            errmsg = f"Iteration {iteration}: Merged is the same object as child."
            raise AssertionError(errmsg)

        # Parent must be unchanged
        if parent.scopes != parent_scopes_before:
            errmsg = (
                f"Iteration {iteration}: parent.scopes was mutated. "
                f"before={parent_scopes_before}, after={parent.scopes}"
            )
            raise AssertionError(errmsg)

        if parent.roles != parent_roles_before:
            errmsg = (
                f"Iteration {iteration}: parent.roles was mutated. "
                f"before={parent_roles_before}, after={parent.roles}"
            )
            raise AssertionError(errmsg)

        if parent.access_policy is not parent_policy_before:
            errmsg = (
                f"Iteration {iteration}: parent.access_policy reference changed."
            )
            raise AssertionError(errmsg)

        if parent.rate_limit is not parent_rate_before:
            errmsg = (
                f"Iteration {iteration}: parent.rate_limit reference changed."
            )
            raise AssertionError(errmsg)

        # Child must be unchanged
        if child.scopes != child_scopes_before:
            errmsg = (
                f"Iteration {iteration}: child.scopes was mutated. "
                f"before={child_scopes_before}, after={child.scopes}"
            )
            raise AssertionError(errmsg)

        if child.roles != child_roles_before:
            errmsg = (
                f"Iteration {iteration}: child.roles was mutated. "
                f"before={child_roles_before}, after={child.roles}"
            )
            raise AssertionError(errmsg)

        if child.access_policy is not child_policy_before:
            errmsg = (
                f"Iteration {iteration}: child.access_policy reference changed."
            )
            raise AssertionError(errmsg)

        if child.rate_limit is not child_rate_before:
            errmsg = (
                f"Iteration {iteration}: child.rate_limit reference changed."
            )
            raise AssertionError(errmsg)

    return


def test_property_merge_security_never_weakens():
    """
        Property 5: Constraint Inheritance - Security Never Weakens

        *For any* parent-child constraint merge, the merged constraints
        SHALL never be weaker than the parent. Specifically:
        - If parent has access_policy, merged must have access_policy
        - If parent has rate_limit, merged must have rate_limit
        - Merged scopes must be a superset of parent scopes (default mode)
        - Merged roles must be a superset of parent roles (default mode)

        **Feature: endpoint-abstractions, Property 5: Constraint Inheritance**
        **Validates: Requirements 3.6, 7.1, 7.2, 7.3, 9.4**
    """
    for iteration in range(100):
        parent = generate_random_constraints()
        child = generate_random_constraints()

        merged = EndpointConstraints.merge(parent, child)

        # If parent has access_policy, merged must have one
        if parent.access_policy is not None and merged.access_policy is None:
            errmsg = (
                f"Iteration {iteration}: Merged lost parent access_policy. "
                f"parent.access_policy={parent.access_policy}"
            )
            raise AssertionError(errmsg)

        # If parent has rate_limit, merged must have one
        if parent.rate_limit is not None and merged.rate_limit is None:
            errmsg = (
                f"Iteration {iteration}: Merged lost parent rate_limit. "
                f"parent.rate_limit={parent.rate_limit}"
            )
            raise AssertionError(errmsg)

        # If parent has rate_limit, merged rate must be at least as restrictive
        if parent.rate_limit is not None and merged.rate_limit is not None:
            parent_rps = requests_per_second(parent.rate_limit)
            merged_rps = requests_per_second(merged.rate_limit)
            if merged_rps > parent_rps + 1e-12:
                errmsg = (
                    f"Iteration {iteration}: Merged rate_limit is less restrictive "
                    f"than parent. parent={parent.rate_limit} (rps={parent_rps}), "
                    f"merged={merged.rate_limit} (rps={merged_rps})"
                )
                raise AssertionError(errmsg)

        # Merged scopes must be superset of parent scopes (default union)
        parent_scopes_set = set(parent.scopes)
        merged_scopes_set = set(merged.scopes)
        if not parent_scopes_set.issubset(merged_scopes_set):
            errmsg = (
                f"Iteration {iteration}: Merged scopes not a superset of parent. "
                f"parent.scopes={parent.scopes}, merged.scopes={merged.scopes}"
            )
            raise AssertionError(errmsg)

        # Merged roles must be superset of parent roles (default union)
        parent_roles_set = set(parent.roles)
        merged_roles_set = set(merged.roles)
        if not parent_roles_set.issubset(merged_roles_set):
            errmsg = (
                f"Iteration {iteration}: Merged roles not a superset of parent. "
                f"parent.roles={parent.roles}, merged.roles={merged.roles}"
            )
            raise AssertionError(errmsg)

    return
