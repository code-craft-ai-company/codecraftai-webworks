"""
.. module:: test_policy_factories
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Tests for the policy factory convenience functions.

.. moduleauthor:: Automation Mojo LLC

This module contains unit tests for the policy factory functions defined in
the policyfactories module. The factories tested are public(), authenticated(),
roles(), and scopes(). Each test verifies that the returned AccessPolicy has
the correct field values and is a valid AccessPolicy instance.
"""

from automojo.webworks.security.accesspolicy import AccessPolicy
from automojo.webworks.security.policyfactories import (
    public,
    authenticated,
    roles,
    scopes,
)
from automojo.webworks.security.securitycontext import Security_Context


# =============================================================================
# Unit Tests for public() factory
# =============================================================================

def test_public_returns_access_policy_instance():
    """
        Test that public() returns an AccessPolicy instance.
    """
    policy = public()

    is_access_policy = isinstance(policy, AccessPolicy)
    if is_access_policy is not True:
        errmsg = f"Expected AccessPolicy instance, got {type(policy)}"
        raise AssertionError(errmsg)

    return


def test_public_sets_require_auth_false():
    """
        Test that public() returns a policy with require_auth set to False.
    """
    policy = public()

    if policy.require_auth is not False:
        errmsg = f"Expected require_auth to be False, got {policy.require_auth}"
        raise AssertionError(errmsg)

    return


def test_public_has_empty_roles_and_scopes():
    """
        Test that public() returns a policy with no roles or scopes.
    """
    policy = public()

    if policy.roles != ():
        errmsg = f"Expected roles to be empty tuple, got {policy.roles}"
        raise AssertionError(errmsg)

    if policy.scopes != ():
        errmsg = f"Expected scopes to be empty tuple, got {policy.scopes}"
        raise AssertionError(errmsg)

    return


def test_public_allows_unauthenticated_access():
    """
        Test that a public policy passes check() for a guest context.
    """
    policy = public()
    guest = Security_Context.guest()

    check_result = policy.check(guest)
    if check_result is not True:
        errmsg = "Expected public policy to allow guest access"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for authenticated() factory
# =============================================================================

def test_authenticated_returns_access_policy_instance():
    """
        Test that authenticated() returns an AccessPolicy instance.
    """
    policy = authenticated()

    is_access_policy = isinstance(policy, AccessPolicy)
    if is_access_policy is not True:
        errmsg = f"Expected AccessPolicy instance, got {type(policy)}"
        raise AssertionError(errmsg)

    return


def test_authenticated_sets_require_auth_true():
    """
        Test that authenticated() returns a policy with require_auth set to True.
    """
    policy = authenticated()

    if policy.require_auth is not True:
        errmsg = f"Expected require_auth to be True, got {policy.require_auth}"
        raise AssertionError(errmsg)

    return


def test_authenticated_has_empty_roles_and_scopes():
    """
        Test that authenticated() returns a policy with no roles or scopes.
    """
    policy = authenticated()

    if policy.roles != ():
        errmsg = f"Expected roles to be empty tuple, got {policy.roles}"
        raise AssertionError(errmsg)

    if policy.scopes != ():
        errmsg = f"Expected scopes to be empty tuple, got {policy.scopes}"
        raise AssertionError(errmsg)

    return


def test_authenticated_denies_guest_access():
    """
        Test that an authenticated policy denies access for a guest context.
    """
    policy = authenticated()
    guest = Security_Context.guest()

    check_result = policy.check(guest)
    if check_result is not False:
        errmsg = "Expected authenticated policy to deny guest access"
        raise AssertionError(errmsg)

    return


def test_authenticated_allows_authenticated_user():
    """
        Test that an authenticated policy allows access for an authenticated user.
    """
    policy = authenticated()
    user_ctx = Security_Context(user_id="user-1", username="testuser")

    check_result = policy.check(user_ctx)
    if check_result is not True:
        errmsg = "Expected authenticated policy to allow authenticated user"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for roles() factory
# =============================================================================

def test_roles_returns_access_policy_instance():
    """
        Test that roles() returns an AccessPolicy instance.
    """
    policy = roles("admin", "editor")

    is_access_policy = isinstance(policy, AccessPolicy)
    if is_access_policy is not True:
        errmsg = f"Expected AccessPolicy instance, got {type(policy)}"
        raise AssertionError(errmsg)

    return


def test_roles_sets_specified_roles():
    """
        Test that roles() stores the specified role names.
    """
    policy = roles("admin", "editor")

    expected_roles = ("admin", "editor")
    if policy.roles != expected_roles:
        errmsg = f"Expected roles {expected_roles}, got {policy.roles}"
        raise AssertionError(errmsg)

    return


def test_roles_sets_require_auth_true():
    """
        Test that roles() returns a policy with require_auth set to True.
    """
    policy = roles("admin")

    if policy.require_auth is not True:
        errmsg = f"Expected require_auth to be True, got {policy.require_auth}"
        raise AssertionError(errmsg)

    return


def test_roles_has_empty_scopes():
    """
        Test that roles() returns a policy with no scopes.
    """
    policy = roles("admin", "editor")

    if policy.scopes != ():
        errmsg = f"Expected scopes to be empty tuple, got {policy.scopes}"
        raise AssertionError(errmsg)

    return


def test_roles_with_single_role():
    """
        Test that roles() works with a single role argument.
    """
    policy = roles("viewer")

    expected_roles = ("viewer",)
    if policy.roles != expected_roles:
        errmsg = f"Expected roles {expected_roles}, got {policy.roles}"
        raise AssertionError(errmsg)

    return


def test_roles_denies_user_without_matching_role():
    """
        Test that a roles policy denies a user who lacks the required roles.
    """
    policy = roles("admin")
    user_ctx = Security_Context(user_id="user-1", roles=("viewer",))

    check_result = policy.check(user_ctx)
    if check_result is not False:
        errmsg = "Expected roles policy to deny user without matching role"
        raise AssertionError(errmsg)

    return


def test_roles_allows_user_with_matching_role():
    """
        Test that a roles policy allows a user who has one of the required roles.
    """
    policy = roles("admin", "editor")
    user_ctx = Security_Context(user_id="user-1", roles=("editor",))

    check_result = policy.check(user_ctx)
    if check_result is not True:
        errmsg = "Expected roles policy to allow user with matching role"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for scopes() factory
# =============================================================================

def test_scopes_returns_access_policy_instance():
    """
        Test that scopes() returns an AccessPolicy instance.
    """
    policy = scopes("read", "write")

    is_access_policy = isinstance(policy, AccessPolicy)
    if is_access_policy is not True:
        errmsg = f"Expected AccessPolicy instance, got {type(policy)}"
        raise AssertionError(errmsg)

    return


def test_scopes_sets_specified_scopes():
    """
        Test that scopes() stores the specified scope names.
    """
    policy = scopes("read", "write")

    expected_scopes = ("read", "write")
    if policy.scopes != expected_scopes:
        errmsg = f"Expected scopes {expected_scopes}, got {policy.scopes}"
        raise AssertionError(errmsg)

    return


def test_scopes_sets_require_auth_true():
    """
        Test that scopes() returns a policy with require_auth set to True.
    """
    policy = scopes("read")

    if policy.require_auth is not True:
        errmsg = f"Expected require_auth to be True, got {policy.require_auth}"
        raise AssertionError(errmsg)

    return


def test_scopes_has_empty_roles():
    """
        Test that scopes() returns a policy with no roles.
    """
    policy = scopes("read", "write")

    if policy.roles != ():
        errmsg = f"Expected roles to be empty tuple, got {policy.roles}"
        raise AssertionError(errmsg)

    return


def test_scopes_with_single_scope():
    """
        Test that scopes() works with a single scope argument.
    """
    policy = scopes("read")

    expected_scopes = ("read",)
    if policy.scopes != expected_scopes:
        errmsg = f"Expected scopes {expected_scopes}, got {policy.scopes}"
        raise AssertionError(errmsg)

    return


def test_scopes_denies_user_missing_a_scope():
    """
        Test that a scopes policy denies a user who is missing one of the
        required scopes.
    """
    policy = scopes("read", "write")
    user_ctx = Security_Context(user_id="user-1", scopes=("read",))

    check_result = policy.check(user_ctx)
    if check_result is not False:
        errmsg = "Expected scopes policy to deny user missing required scope"
        raise AssertionError(errmsg)

    return


def test_scopes_allows_user_with_all_scopes():
    """
        Test that a scopes policy allows a user who has all required scopes.
    """
    policy = scopes("read", "write")
    user_ctx = Security_Context(user_id="user-1", scopes=("read", "write", "delete"))

    check_result = policy.check(user_ctx)
    if check_result is not True:
        errmsg = "Expected scopes policy to allow user with all required scopes"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for factory return type consistency
# =============================================================================

def test_all_factories_return_access_policy_with_passable_to_attach():
    """
        Test that all factory functions return AccessPolicy instances that
        can be used with attach_at() by verifying they are valid AccessPolicy
        objects with the expected interface.
    """
    policies = [
        public(),
        authenticated(),
        roles("admin"),
        scopes("read"),
    ]

    for policy in policies:
        is_access_policy = isinstance(policy, AccessPolicy)
        if is_access_policy is not True:
            errmsg = f"Expected AccessPolicy instance, got {type(policy)}"
            raise AssertionError(errmsg)

        has_check = hasattr(policy, "check")
        if has_check is not True:
            errmsg = "Expected policy to have check() method"
            raise AssertionError(errmsg)

        has_merge = hasattr(policy, "merge_with")
        if has_merge is not True:
            errmsg = "Expected policy to have merge_with() method"
            raise AssertionError(errmsg)

    return
