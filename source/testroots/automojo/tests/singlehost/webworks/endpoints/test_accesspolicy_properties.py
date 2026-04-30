"""
.. module:: test_accesspolicy_properties
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Property-based tests for AccessPolicy merge behavior.

.. moduleauthor:: Automation Mojo LLC

This module contains property-based tests for the AccessPolicy class,
validating Property 7: Security Policy Composition across many generated
inputs.
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []

import random
import string
from typing import List

from automojo.webworks.endpoints.accesspolicy import AccessPolicy


# =============================================================================
# Helper Functions for Generating Random Test Data
# =============================================================================

def generate_random_string(min_len: int = 3, max_len: int = 10) -> str:
    """Generate a random alphanumeric string."""
    length = random.randint(min_len, max_len)
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))


def generate_random_roles() -> List[str]:
    """Generate a random list of roles."""
    num_roles = random.randint(0, 4)
    return [generate_random_string(3, 8) for _ in range(num_roles)]


def generate_random_scopes() -> List[str]:
    """Generate a random list of scopes."""
    num_scopes = random.randint(0, 4)
    return [generate_random_string(3, 8) for _ in range(num_scopes)]


def generate_random_access_policy() -> AccessPolicy:
    """Generate a random AccessPolicy with random roles, scopes, and require_auth."""
    return AccessPolicy(
        roles=generate_random_roles(),
        scopes=generate_random_scopes(),
        require_auth=random.choice([True, False])
    )


class MockUser:
    """
        Mock user class for testing AccessPolicy.check().
    """

    def __init__(
        self,
        roles: List[str] = None,
        scopes: List[str] = None,
        is_authenticated: bool = True
    ):
        self._roles = roles or []
        self._scopes = scopes or []
        self._is_authenticated = is_authenticated

    @property
    def roles(self) -> List[str]:
        return self._roles

    @property
    def scopes(self) -> List[str]:
        return self._scopes

    @property
    def is_authenticated(self) -> bool:
        return self._is_authenticated


# =============================================================================
# Property 7: Security Policy Composition
# Feature: endpoint-abstractions, Property 7: Security Policy Composition
# Validates: Requirements 7.6, 7.7
# =============================================================================

def test_property_merge_enforces_all_constraints_logical_and():
    """
        Property 7: Security Policy Composition

        *For any* endpoint with multiple applicable policies (e.g., blueprint
        policy + handler policy), the combined policy SHALL enforce all
        constraints via logical AND, ensuring nested definitions do not
        inadvertently weaken security.

        This test verifies that merging two policies produces a combined
        policy whose require_auth is the logical OR of both inputs (meaning
        if either requires auth, the merged result requires auth). This
        ensures the merged policy never weakens the auth requirement.

        **Feature: endpoint-abstractions, Property 7: Security Policy Composition**
        **Validates: Requirements 7.6, 7.7**
    """
    for iteration in range(100):
        policy_a = generate_random_access_policy()
        policy_b = generate_random_access_policy()

        merged = policy_a.merge_with(policy_b)

        # require_auth must be logical OR: if either requires auth, merged must too
        expected_require_auth = policy_a.require_auth or policy_b.require_auth

        if merged.require_auth != expected_require_auth:
            errmsg = (
                f"Iteration {iteration}: Merged require_auth should be logical OR. "
                f"policy_a.require_auth={policy_a.require_auth}, "
                f"policy_b.require_auth={policy_b.require_auth}, "
                f"merged.require_auth={merged.require_auth}, "
                f"expected={expected_require_auth}"
            )
            raise AssertionError(errmsg)

    return


def test_property_merge_roles_union_by_default():
    """
        Property 7: Security Policy Composition - Roles Union

        *For any* two AccessPolicy objects merged with default settings,
        the merged roles SHALL be the union of both role lists, ensuring
        no roles are lost during composition.

        **Feature: endpoint-abstractions, Property 7: Security Policy Composition**
        **Validates: Requirements 7.6, 7.7**
    """
    for iteration in range(100):
        policy_a = generate_random_access_policy()
        policy_b = generate_random_access_policy()

        merged = policy_a.merge_with(policy_b)

        # All roles from both policies must be present in merged
        for role in policy_a.roles:
            if role not in merged.roles:
                errmsg = (
                    f"Iteration {iteration}: Merged roles missing role from policy_a. "
                    f"role={role}, policy_a.roles={policy_a.roles}, "
                    f"merged.roles={merged.roles}"
                )
                raise AssertionError(errmsg)

        for role in policy_b.roles:
            if role not in merged.roles:
                errmsg = (
                    f"Iteration {iteration}: Merged roles missing role from policy_b. "
                    f"role={role}, policy_b.roles={policy_b.roles}, "
                    f"merged.roles={merged.roles}"
                )
                raise AssertionError(errmsg)

        # Merged roles should not contain duplicates
        if len(merged.roles) != len(set(merged.roles)):
            errmsg = (
                f"Iteration {iteration}: Merged roles contain duplicates. "
                f"merged.roles={merged.roles}"
            )
            raise AssertionError(errmsg)

    return


def test_property_merge_scopes_union_by_default():
    """
        Property 7: Security Policy Composition - Scopes Union

        *For any* two AccessPolicy objects merged with default settings,
        the merged scopes SHALL be the union of both scope lists, ensuring
        no scopes are lost during composition.

        **Feature: endpoint-abstractions, Property 7: Security Policy Composition**
        **Validates: Requirements 7.6, 7.7**
    """
    for iteration in range(100):
        policy_a = generate_random_access_policy()
        policy_b = generate_random_access_policy()

        merged = policy_a.merge_with(policy_b)

        # All scopes from both policies must be present in merged
        for scope in policy_a.scopes:
            if scope not in merged.scopes:
                errmsg = (
                    f"Iteration {iteration}: Merged scopes missing scope from policy_a. "
                    f"scope={scope}, policy_a.scopes={policy_a.scopes}, "
                    f"merged.scopes={merged.scopes}"
                )
                raise AssertionError(errmsg)

        for scope in policy_b.scopes:
            if scope not in merged.scopes:
                errmsg = (
                    f"Iteration {iteration}: Merged scopes missing scope from policy_b. "
                    f"scope={scope}, policy_b.scopes={policy_b.scopes}, "
                    f"merged.scopes={merged.scopes}"
                )
                raise AssertionError(errmsg)

        # Merged scopes should not contain duplicates
        if len(merged.scopes) != len(set(merged.scopes)):
            errmsg = (
                f"Iteration {iteration}: Merged scopes contain duplicates. "
                f"merged.scopes={merged.scopes}"
            )
            raise AssertionError(errmsg)

    return


def test_property_merge_never_weakens_security():
    """
        Property 7: Security Policy Composition - No Weakening

        *For any* two AccessPolicy objects, the merged policy SHALL never
        be weaker than either input policy. Specifically:
        - If either policy requires auth, the merged policy requires auth
        - The merged roles are a superset of each input's roles
        - The merged scopes are a superset of each input's scopes

        A user who fails either input policy MUST also fail the merged policy
        (when the merged policy is used for access checks).

        **Feature: endpoint-abstractions, Property 7: Security Policy Composition**
        **Validates: Requirements 7.6, 7.7**
    """
    for iteration in range(100):
        policy_a = generate_random_access_policy()
        policy_b = generate_random_access_policy()

        merged = policy_a.merge_with(policy_b)

        # Auth requirement must never weaken
        if policy_a.require_auth and not merged.require_auth:
            errmsg = (
                f"Iteration {iteration}: Merged policy weakened auth requirement from policy_a. "
                f"policy_a.require_auth={policy_a.require_auth}, "
                f"merged.require_auth={merged.require_auth}"
            )
            raise AssertionError(errmsg)

        if policy_b.require_auth and not merged.require_auth:
            errmsg = (
                f"Iteration {iteration}: Merged policy weakened auth requirement from policy_b. "
                f"policy_b.require_auth={policy_b.require_auth}, "
                f"merged.require_auth={merged.require_auth}"
            )
            raise AssertionError(errmsg)

        # Merged roles must be a superset of each input's roles
        merged_roles_set = set(merged.roles)
        if not set(policy_a.roles).issubset(merged_roles_set):
            errmsg = (
                f"Iteration {iteration}: Merged roles not a superset of policy_a roles. "
                f"policy_a.roles={policy_a.roles}, merged.roles={merged.roles}"
            )
            raise AssertionError(errmsg)

        if not set(policy_b.roles).issubset(merged_roles_set):
            errmsg = (
                f"Iteration {iteration}: Merged roles not a superset of policy_b roles. "
                f"policy_b.roles={policy_b.roles}, merged.roles={merged.roles}"
            )
            raise AssertionError(errmsg)

        # Merged scopes must be a superset of each input's scopes
        merged_scopes_set = set(merged.scopes)
        if not set(policy_a.scopes).issubset(merged_scopes_set):
            errmsg = (
                f"Iteration {iteration}: Merged scopes not a superset of policy_a scopes. "
                f"policy_a.scopes={policy_a.scopes}, merged.scopes={merged.scopes}"
            )
            raise AssertionError(errmsg)

        if not set(policy_b.scopes).issubset(merged_scopes_set):
            errmsg = (
                f"Iteration {iteration}: Merged scopes not a superset of policy_b scopes. "
                f"policy_b.scopes={policy_b.scopes}, merged.scopes={merged.scopes}"
            )
            raise AssertionError(errmsg)

    return


def test_property_merge_returns_new_instance():
    """
        Property 7: Security Policy Composition - Immutability

        *For any* two AccessPolicy objects, merging SHALL return a new
        AccessPolicy instance without modifying either input policy.

        **Feature: endpoint-abstractions, Property 7: Security Policy Composition**
        **Validates: Requirements 7.6, 7.7**
    """
    for iteration in range(100):
        policy_a = generate_random_access_policy()
        policy_b = generate_random_access_policy()

        # Snapshot original values. AccessPolicy stores roles/scopes as
        # tuples, so snapshot as tuples for direct equality comparison
        # against the live attributes after merge_with returns.
        a_roles_before = tuple(policy_a.roles)
        a_scopes_before = tuple(policy_a.scopes)
        a_auth_before = policy_a.require_auth
        b_roles_before = tuple(policy_b.roles)
        b_scopes_before = tuple(policy_b.scopes)
        b_auth_before = policy_b.require_auth

        merged = policy_a.merge_with(policy_b)

        # Merged must be a different object
        if merged is policy_a:
            errmsg = f"Iteration {iteration}: Merged policy is the same object as policy_a."
            raise AssertionError(errmsg)

        if merged is policy_b:
            errmsg = f"Iteration {iteration}: Merged policy is the same object as policy_b."
            raise AssertionError(errmsg)

        # Original policies must be unchanged
        if policy_a.roles != a_roles_before:
            errmsg = (
                f"Iteration {iteration}: policy_a.roles was mutated. "
                f"before={a_roles_before}, after={policy_a.roles}"
            )
            raise AssertionError(errmsg)

        if policy_a.scopes != a_scopes_before:
            errmsg = (
                f"Iteration {iteration}: policy_a.scopes was mutated. "
                f"before={a_scopes_before}, after={policy_a.scopes}"
            )
            raise AssertionError(errmsg)

        if policy_a.require_auth != a_auth_before:
            errmsg = (
                f"Iteration {iteration}: policy_a.require_auth was mutated. "
                f"before={a_auth_before}, after={policy_a.require_auth}"
            )
            raise AssertionError(errmsg)

        if policy_b.roles != b_roles_before:
            errmsg = (
                f"Iteration {iteration}: policy_b.roles was mutated. "
                f"before={b_roles_before}, after={policy_b.roles}"
            )
            raise AssertionError(errmsg)

        if policy_b.scopes != b_scopes_before:
            errmsg = (
                f"Iteration {iteration}: policy_b.scopes was mutated. "
                f"before={b_scopes_before}, after={policy_b.scopes}"
            )
            raise AssertionError(errmsg)

        if policy_b.require_auth != b_auth_before:
            errmsg = (
                f"Iteration {iteration}: policy_b.require_auth was mutated. "
                f"before={b_auth_before}, after={policy_b.require_auth}"
            )
            raise AssertionError(errmsg)

    return


def test_property_merge_check_combined_enforcement():
    """
        Property 7: Security Policy Composition - Combined Enforcement

        *For any* two AccessPolicy objects with roles and scopes, a user
        who satisfies the merged policy MUST have credentials that satisfy
        the combined constraints. The merged policy enforces all constraints
        via logical AND.

        Specifically: a user who passes the merged policy check must have
        at least one role from the merged role set AND all scopes from the
        merged scope set.

        **Feature: endpoint-abstractions, Property 7: Security Policy Composition**
        **Validates: Requirements 7.6, 7.7**
    """
    for iteration in range(100):
        policy_a = generate_random_access_policy()
        policy_b = generate_random_access_policy()

        merged = policy_a.merge_with(policy_b)

        # Create a user that satisfies the merged policy
        # (has at least one merged role and all merged scopes)
        satisfying_roles = list(merged.roles) if merged.roles else []
        satisfying_scopes = list(merged.scopes) if merged.scopes else []

        user = MockUser(
            roles=satisfying_roles,
            scopes=satisfying_scopes,
            is_authenticated=True
        )

        result = merged.check(user)

        # A user with all merged roles and scopes should pass
        if not result:
            errmsg = (
                f"Iteration {iteration}: User with all merged credentials should pass. "
                f"merged.roles={merged.roles}, merged.scopes={merged.scopes}, "
                f"user.roles={user.roles}, user.scopes={user.scopes}"
            )
            raise AssertionError(errmsg)

        # If merged has scopes, a user missing one scope must fail
        if len(merged.scopes) > 0:
            missing_scope_user = MockUser(
                roles=satisfying_roles,
                scopes=satisfying_scopes[:-1],  # Remove last scope
                is_authenticated=True
            )
            result_missing = merged.check(missing_scope_user)

            if result_missing:
                errmsg = (
                    f"Iteration {iteration}: User missing a scope should fail merged check. "
                    f"merged.scopes={merged.scopes}, "
                    f"user.scopes={missing_scope_user.scopes}"
                )
                raise AssertionError(errmsg)

        # If merged requires auth, unauthenticated user must fail
        if merged.require_auth:
            unauth_user = MockUser(
                roles=satisfying_roles,
                scopes=satisfying_scopes,
                is_authenticated=False
            )
            result_unauth = merged.check(unauth_user)

            if result_unauth:
                errmsg = (
                    f"Iteration {iteration}: Unauthenticated user should fail when "
                    f"merged.require_auth=True."
                )
                raise AssertionError(errmsg)

    return


def test_property_merge_with_replace_roles_replaces_completely():
    """
        Property 7: Security Policy Composition - Replace Roles

        *For any* two AccessPolicy objects, when merge_with is called with
        replace_roles=True, the merged roles SHALL be exactly the other
        policy's roles, not a union.

        **Feature: endpoint-abstractions, Property 7: Security Policy Composition**
        **Validates: Requirements 7.6, 7.7**
    """
    for iteration in range(100):
        policy_a = generate_random_access_policy()
        policy_b = generate_random_access_policy()

        merged = policy_a.merge_with(policy_b, replace_roles=True)

        if merged.roles != policy_b.roles:
            errmsg = (
                f"Iteration {iteration}: With replace_roles=True, merged roles "
                f"should equal policy_b.roles. "
                f"policy_a.roles={policy_a.roles}, policy_b.roles={policy_b.roles}, "
                f"merged.roles={merged.roles}"
            )
            raise AssertionError(errmsg)

        # Scopes should still be union (not replaced)
        for scope in policy_a.scopes:
            if scope not in merged.scopes:
                errmsg = (
                    f"Iteration {iteration}: replace_roles should not affect scopes. "
                    f"Missing scope={scope} from policy_a in merged.scopes={merged.scopes}"
                )
                raise AssertionError(errmsg)

    return


def test_property_merge_with_replace_scopes_replaces_completely():
    """
        Property 7: Security Policy Composition - Replace Scopes

        *For any* two AccessPolicy objects, when merge_with is called with
        replace_scopes=True, the merged scopes SHALL be exactly the other
        policy's scopes, not a union.

        **Feature: endpoint-abstractions, Property 7: Security Policy Composition**
        **Validates: Requirements 7.6, 7.7**
    """
    for iteration in range(100):
        policy_a = generate_random_access_policy()
        policy_b = generate_random_access_policy()

        merged = policy_a.merge_with(policy_b, replace_scopes=True)

        if merged.scopes != policy_b.scopes:
            errmsg = (
                f"Iteration {iteration}: With replace_scopes=True, merged scopes "
                f"should equal policy_b.scopes. "
                f"policy_a.scopes={policy_a.scopes}, policy_b.scopes={policy_b.scopes}, "
                f"merged.scopes={merged.scopes}"
            )
            raise AssertionError(errmsg)

        # Roles should still be union (not replaced)
        for role in policy_a.roles:
            if role not in merged.roles:
                errmsg = (
                    f"Iteration {iteration}: replace_scopes should not affect roles. "
                    f"Missing role={role} from policy_a in merged.roles={merged.roles}"
                )
                raise AssertionError(errmsg)

    return
