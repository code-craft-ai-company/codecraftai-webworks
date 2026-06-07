"""
.. module:: test_security_decorators
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Tests for the security decorator functions.

.. moduleauthor:: Code Craft AI LLC

This module contains unit tests for the security decorators defined in the
decorators module. The decorators tested are require_auth, require_roles,
require_scopes, and public_endpoint. Each test verifies that the decorator
attaches the correct AccessPolicy metadata to the handler function and that
decorators are composable when stacked.
"""

from ccai.webworks.security.accesspolicy import AccessPolicy
from ccai.webworks.security.decorators import (
    HANDLER_POLICY_ATTR,
    get_handler_policy,
    public_endpoint,
    require_auth,
    require_roles,
    require_scopes,
)


# =============================================================================
# Unit Tests for @require_auth decorator
# =============================================================================

def test_require_auth_attaches_policy():
    """
        Test that @require_auth attaches an AccessPolicy to the handler.
    """

    @require_auth
    def my_handler():
        return

    has_policy = hasattr(my_handler, HANDLER_POLICY_ATTR)
    if has_policy is not True:
        errmsg = "Expected handler to have _access_policy attribute"
        raise AssertionError(errmsg)

    return


def test_require_auth_sets_require_auth_true():
    """
        Test that @require_auth creates a policy with require_auth=True.
    """

    @require_auth
    def my_handler():
        return

    policy = get_handler_policy(my_handler)

    if policy.require_auth is not True:
        errmsg = f"Expected require_auth to be True, got {policy.require_auth}"
        raise AssertionError(errmsg)

    return


def test_require_auth_has_empty_roles_and_scopes():
    """
        Test that @require_auth creates a policy with no roles or scopes.
    """

    @require_auth
    def my_handler():
        return

    policy = get_handler_policy(my_handler)

    if policy.roles != ():
        errmsg = f"Expected roles to be empty tuple, got {policy.roles}"
        raise AssertionError(errmsg)

    if policy.scopes != ():
        errmsg = f"Expected scopes to be empty tuple, got {policy.scopes}"
        raise AssertionError(errmsg)

    return


def test_require_auth_returns_access_policy_instance():
    """
        Test that @require_auth attaches a valid AccessPolicy instance.
    """

    @require_auth
    def my_handler():
        return

    policy = get_handler_policy(my_handler)

    is_access_policy = isinstance(policy, AccessPolicy)
    if is_access_policy is not True:
        errmsg = f"Expected AccessPolicy instance, got {type(policy)}"
        raise AssertionError(errmsg)

    return



# =============================================================================
# Unit Tests for @require_roles decorator
# =============================================================================

def test_require_roles_attaches_policy():
    """
        Test that @require_roles attaches an AccessPolicy to the handler.
    """

    @require_roles("admin", "editor")
    def my_handler():
        return

    has_policy = hasattr(my_handler, HANDLER_POLICY_ATTR)
    if has_policy is not True:
        errmsg = "Expected handler to have _access_policy attribute"
        raise AssertionError(errmsg)

    return


def test_require_roles_sets_specified_roles():
    """
        Test that @require_roles stores the specified role names.
    """

    @require_roles("admin", "editor")
    def my_handler():
        return

    policy = get_handler_policy(my_handler)

    expected_roles = ("admin", "editor")
    if policy.roles != expected_roles:
        errmsg = f"Expected roles {expected_roles}, got {policy.roles}"
        raise AssertionError(errmsg)

    return


def test_require_roles_sets_require_auth_true():
    """
        Test that @require_roles creates a policy with require_auth=True.
    """

    @require_roles("admin")
    def my_handler():
        return

    policy = get_handler_policy(my_handler)

    if policy.require_auth is not True:
        errmsg = f"Expected require_auth to be True, got {policy.require_auth}"
        raise AssertionError(errmsg)

    return


def test_require_roles_has_empty_scopes():
    """
        Test that @require_roles creates a policy with no scopes.
    """

    @require_roles("admin")
    def my_handler():
        return

    policy = get_handler_policy(my_handler)

    if policy.scopes != ():
        errmsg = f"Expected scopes to be empty tuple, got {policy.scopes}"
        raise AssertionError(errmsg)

    return


def test_require_roles_with_single_role():
    """
        Test that @require_roles works with a single role argument.
    """

    @require_roles("viewer")
    def my_handler():
        return

    policy = get_handler_policy(my_handler)

    expected_roles = ("viewer",)
    if policy.roles != expected_roles:
        errmsg = f"Expected roles {expected_roles}, got {policy.roles}"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for @require_scopes decorator
# =============================================================================

def test_require_scopes_attaches_policy():
    """
        Test that @require_scopes attaches an AccessPolicy to the handler.
    """

    @require_scopes("read", "write")
    def my_handler():
        return

    has_policy = hasattr(my_handler, HANDLER_POLICY_ATTR)
    if has_policy is not True:
        errmsg = "Expected handler to have _access_policy attribute"
        raise AssertionError(errmsg)

    return


def test_require_scopes_sets_specified_scopes():
    """
        Test that @require_scopes stores the specified scope names.
    """

    @require_scopes("read", "write")
    def my_handler():
        return

    policy = get_handler_policy(my_handler)

    expected_scopes = ("read", "write")
    if policy.scopes != expected_scopes:
        errmsg = f"Expected scopes {expected_scopes}, got {policy.scopes}"
        raise AssertionError(errmsg)

    return


def test_require_scopes_sets_require_auth_true():
    """
        Test that @require_scopes creates a policy with require_auth=True.
    """

    @require_scopes("read")
    def my_handler():
        return

    policy = get_handler_policy(my_handler)

    if policy.require_auth is not True:
        errmsg = f"Expected require_auth to be True, got {policy.require_auth}"
        raise AssertionError(errmsg)

    return


def test_require_scopes_has_empty_roles():
    """
        Test that @require_scopes creates a policy with no roles.
    """

    @require_scopes("read")
    def my_handler():
        return

    policy = get_handler_policy(my_handler)

    if policy.roles != ():
        errmsg = f"Expected roles to be empty tuple, got {policy.roles}"
        raise AssertionError(errmsg)

    return


def test_require_scopes_with_single_scope():
    """
        Test that @require_scopes works with a single scope argument.
    """

    @require_scopes("read")
    def my_handler():
        return

    policy = get_handler_policy(my_handler)

    expected_scopes = ("read",)
    if policy.scopes != expected_scopes:
        errmsg = f"Expected scopes {expected_scopes}, got {policy.scopes}"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for @public_endpoint decorator
# =============================================================================

def test_public_endpoint_attaches_policy():
    """
        Test that @public_endpoint attaches an AccessPolicy to the handler.
    """

    @public_endpoint
    def my_handler():
        return

    has_policy = hasattr(my_handler, HANDLER_POLICY_ATTR)
    if has_policy is not True:
        errmsg = "Expected handler to have _access_policy attribute"
        raise AssertionError(errmsg)

    return


def test_public_endpoint_sets_require_auth_false():
    """
        Test that @public_endpoint creates a policy with require_auth=False.
    """

    @public_endpoint
    def my_handler():
        return

    policy = get_handler_policy(my_handler)

    if policy.require_auth is not False:
        errmsg = f"Expected require_auth to be False, got {policy.require_auth}"
        raise AssertionError(errmsg)

    return


def test_public_endpoint_has_empty_roles_and_scopes():
    """
        Test that @public_endpoint creates a policy with no roles or scopes.
    """

    @public_endpoint
    def my_handler():
        return

    policy = get_handler_policy(my_handler)

    if policy.roles != ():
        errmsg = f"Expected roles to be empty tuple, got {policy.roles}"
        raise AssertionError(errmsg)

    if policy.scopes != ():
        errmsg = f"Expected scopes to be empty tuple, got {policy.scopes}"
        raise AssertionError(errmsg)

    return


def test_public_endpoint_returns_access_policy_instance():
    """
        Test that @public_endpoint attaches a valid AccessPolicy instance.
    """

    @public_endpoint
    def my_handler():
        return

    policy = get_handler_policy(my_handler)

    is_access_policy = isinstance(policy, AccessPolicy)
    if is_access_policy is not True:
        errmsg = f"Expected AccessPolicy instance, got {type(policy)}"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for decorator composability (stacking)
# =============================================================================

def test_stacking_require_auth_and_require_roles():
    """
        Test that stacking @require_auth and @require_roles merges policies.
    """

    @require_roles("admin")
    @require_auth
    def my_handler():
        return

    policy = get_handler_policy(my_handler)

    if policy.require_auth is not True:
        errmsg = f"Expected require_auth to be True, got {policy.require_auth}"
        raise AssertionError(errmsg)

    expected_roles = ("admin",)
    if policy.roles != expected_roles:
        errmsg = f"Expected roles {expected_roles}, got {policy.roles}"
        raise AssertionError(errmsg)

    return


def test_stacking_require_roles_and_require_scopes():
    """
        Test that stacking @require_roles and @require_scopes merges policies.
    """

    @require_scopes("read", "write")
    @require_roles("admin")
    def my_handler():
        return

    policy = get_handler_policy(my_handler)

    expected_roles = ("admin",)
    if policy.roles != expected_roles:
        errmsg = f"Expected roles {expected_roles}, got {policy.roles}"
        raise AssertionError(errmsg)

    expected_scopes = ("read", "write")
    if policy.scopes != expected_scopes:
        errmsg = f"Expected scopes {expected_scopes}, got {policy.scopes}"
        raise AssertionError(errmsg)

    if policy.require_auth is not True:
        errmsg = f"Expected require_auth to be True, got {policy.require_auth}"
        raise AssertionError(errmsg)

    return


def test_stacking_multiple_require_roles():
    """
        Test that stacking multiple @require_roles merges role lists as union.
    """

    @require_roles("editor")
    @require_roles("admin")
    def my_handler():
        return

    policy = get_handler_policy(my_handler)

    has_admin = "admin" in policy.roles
    if has_admin is not True:
        errmsg = f"Expected 'admin' in roles, got {policy.roles}"
        raise AssertionError(errmsg)

    has_editor = "editor" in policy.roles
    if has_editor is not True:
        errmsg = f"Expected 'editor' in roles, got {policy.roles}"
        raise AssertionError(errmsg)

    return


def test_stacking_all_decorators():
    """
        Test that stacking all four decorators produces a merged policy.
    """

    @require_scopes("write")
    @require_roles("admin")
    @require_auth
    def my_handler():
        return

    policy = get_handler_policy(my_handler)

    if policy.require_auth is not True:
        errmsg = f"Expected require_auth to be True, got {policy.require_auth}"
        raise AssertionError(errmsg)

    expected_roles = ("admin",)
    if policy.roles != expected_roles:
        errmsg = f"Expected roles {expected_roles}, got {policy.roles}"
        raise AssertionError(errmsg)

    expected_scopes = ("write",)
    if policy.scopes != expected_scopes:
        errmsg = f"Expected scopes {expected_scopes}, got {policy.scopes}"
        raise AssertionError(errmsg)

    return


def test_public_endpoint_merged_with_require_auth_results_in_auth_required():
    """
        Test that merging @public_endpoint with @require_auth results in
        require_auth=True because merge uses logical OR for require_auth.
    """

    @require_auth
    @public_endpoint
    def my_handler():
        return

    policy = get_handler_policy(my_handler)

    if policy.require_auth is not True:
        errmsg = (
            f"Expected require_auth to be True after merging public with "
            f"require_auth, got {policy.require_auth}"
        )
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for get_handler_policy helper
# =============================================================================

def test_get_handler_policy_returns_none_for_undecorated():
    """
        Test that get_handler_policy returns None for a handler without
        any security decorators.
    """

    def my_handler():
        return

    policy = get_handler_policy(my_handler)

    if policy is not None:
        errmsg = f"Expected None for undecorated handler, got {policy}"
        raise AssertionError(errmsg)

    return


def test_get_handler_policy_returns_policy_for_decorated():
    """
        Test that get_handler_policy returns the attached policy for a
        decorated handler.
    """

    @require_auth
    def my_handler():
        return

    policy = get_handler_policy(my_handler)

    if policy is None:
        errmsg = "Expected a policy for decorated handler, got None"
        raise AssertionError(errmsg)

    is_access_policy = isinstance(policy, AccessPolicy)
    if is_access_policy is not True:
        errmsg = f"Expected AccessPolicy instance, got {type(policy)}"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Property-Based Tests for Security Decorator Behavior
# =============================================================================

import random
import string


def _random_string_tuple(max_length=5):
    """
        Generate a tuple of random unique strings for use as roles or scopes.

        :returns: A tuple of 0 to max_length random lowercase strings.
    """
    count = random.randint(0, max_length)
    items = []
    for _ in range(count):
        length = random.randint(1, 8)
        item = "".join(random.choices(string.ascii_lowercase, k=length))
        items.append(item)

    # Deduplicate while preserving order
    seen = set()
    unique = []
    for item in items:
        if item not in seen:
            seen.add(item)
            unique.append(item)

    rtnval = tuple(unique)

    return rtnval


def _order_preserving_union(tuple_a, tuple_b):
    """
        Compute the order-preserving union of two tuples.

        Items from tuple_a appear first in their original order, followed by
        items from tuple_b that are not already present.

        :param tuple_a: First tuple.
        :param tuple_b: Second tuple.

        :returns: A tuple containing the order-preserving union.
    """
    seen = set()
    combined = []
    for item in tuple_a:
        if item not in seen:
            seen.add(item)
            combined.append(item)
    for item in tuple_b:
        if item not in seen:
            seen.add(item)
            combined.append(item)

    rtnval = tuple(combined)

    return rtnval


def test_property_require_auth_creates_correct_policy():
    """
        Property test for @require_auth decorator behavior.

        **Validates: Requirements 9.1**

        For any handler function decorated with @require_auth, the attached
        policy SHALL have require_auth=True, empty roles, and empty scopes.
    """
    iteration_count = 100

    for iteration in range(iteration_count):

        def handler():
            return

        decorated = require_auth(handler)

        policy = get_handler_policy(decorated)

        if policy is None:
            errmsg = f"Iteration {iteration}: @require_auth did not attach a policy"
            raise AssertionError(errmsg)

        if not isinstance(policy, AccessPolicy):
            errmsg = (
                f"Iteration {iteration}: Expected AccessPolicy instance, "
                f"got {type(policy)}"
            )
            raise AssertionError(errmsg)

        if policy.require_auth is not True:
            errmsg = (
                f"Iteration {iteration}: Expected require_auth=True, "
                f"got {policy.require_auth}"
            )
            raise AssertionError(errmsg)

        if policy.roles != ():
            errmsg = (
                f"Iteration {iteration}: Expected empty roles, "
                f"got {policy.roles}"
            )
            raise AssertionError(errmsg)

        if policy.scopes != ():
            errmsg = (
                f"Iteration {iteration}: Expected empty scopes, "
                f"got {policy.scopes}"
            )
            raise AssertionError(errmsg)

    return


def test_property_require_roles_creates_correct_policy():
    """
        Property test for @require_roles decorator behavior.

        **Validates: Requirements 9.2**

        For any random tuple of role names, @require_roles(*roles) SHALL
        create an AccessPolicy with roles equal to the provided roles and
        require_auth=True.
    """
    iteration_count = 100

    for iteration in range(iteration_count):
        role_names = _random_string_tuple(max_length=6)

        def handler():
            return

        decorated = require_roles(*role_names)(handler)

        policy = get_handler_policy(decorated)

        if policy is None:
            errmsg = (
                f"Iteration {iteration}: @require_roles did not attach a policy. "
                f"role_names={role_names}"
            )
            raise AssertionError(errmsg)

        if not isinstance(policy, AccessPolicy):
            errmsg = (
                f"Iteration {iteration}: Expected AccessPolicy instance, "
                f"got {type(policy)}"
            )
            raise AssertionError(errmsg)

        if policy.roles != role_names:
            errmsg = (
                f"Iteration {iteration}: Expected roles={role_names}, "
                f"got {policy.roles}"
            )
            raise AssertionError(errmsg)

        if policy.require_auth is not True:
            errmsg = (
                f"Iteration {iteration}: Expected require_auth=True, "
                f"got {policy.require_auth}"
            )
            raise AssertionError(errmsg)

        if policy.scopes != ():
            errmsg = (
                f"Iteration {iteration}: Expected empty scopes, "
                f"got {policy.scopes}"
            )
            raise AssertionError(errmsg)

    return


def test_property_require_scopes_creates_correct_policy():
    """
        Property test for @require_scopes decorator behavior.

        **Validates: Requirements 9.3**

        For any random tuple of scope names, @require_scopes(*scopes) SHALL
        create an AccessPolicy with scopes equal to the provided scopes and
        require_auth=True.
    """
    iteration_count = 100

    for iteration in range(iteration_count):
        scope_names = _random_string_tuple(max_length=6)

        def handler():
            return

        decorated = require_scopes(*scope_names)(handler)

        policy = get_handler_policy(decorated)

        if policy is None:
            errmsg = (
                f"Iteration {iteration}: @require_scopes did not attach a policy. "
                f"scope_names={scope_names}"
            )
            raise AssertionError(errmsg)

        if not isinstance(policy, AccessPolicy):
            errmsg = (
                f"Iteration {iteration}: Expected AccessPolicy instance, "
                f"got {type(policy)}"
            )
            raise AssertionError(errmsg)

        if policy.scopes != scope_names:
            errmsg = (
                f"Iteration {iteration}: Expected scopes={scope_names}, "
                f"got {policy.scopes}"
            )
            raise AssertionError(errmsg)

        if policy.require_auth is not True:
            errmsg = (
                f"Iteration {iteration}: Expected require_auth=True, "
                f"got {policy.require_auth}"
            )
            raise AssertionError(errmsg)

        if policy.roles != ():
            errmsg = (
                f"Iteration {iteration}: Expected empty roles, "
                f"got {policy.roles}"
            )
            raise AssertionError(errmsg)

    return


def test_property_public_endpoint_creates_correct_policy():
    """
        Property test for @public_endpoint decorator behavior.

        **Validates: Requirements 9.4**

        For any handler function decorated with @public_endpoint, the attached
        policy SHALL have require_auth=False, empty roles, and empty scopes.
    """
    iteration_count = 100

    for iteration in range(iteration_count):

        def handler():
            return

        decorated = public_endpoint(handler)

        policy = get_handler_policy(decorated)

        if policy is None:
            errmsg = f"Iteration {iteration}: @public_endpoint did not attach a policy"
            raise AssertionError(errmsg)

        if not isinstance(policy, AccessPolicy):
            errmsg = (
                f"Iteration {iteration}: Expected AccessPolicy instance, "
                f"got {type(policy)}"
            )
            raise AssertionError(errmsg)

        if policy.require_auth is not False:
            errmsg = (
                f"Iteration {iteration}: Expected require_auth=False, "
                f"got {policy.require_auth}"
            )
            raise AssertionError(errmsg)

        if policy.roles != ():
            errmsg = (
                f"Iteration {iteration}: Expected empty roles, "
                f"got {policy.roles}"
            )
            raise AssertionError(errmsg)

        if policy.scopes != ():
            errmsg = (
                f"Iteration {iteration}: Expected empty scopes, "
                f"got {policy.scopes}"
            )
            raise AssertionError(errmsg)

    return


def test_property_decorator_stacking_combines_policies():
    """
        Property test for decorator stacking behavior.

        **Validates: Requirements 9.5, 9.6, 9.8**

        For any random roles and scopes, stacking @require_roles and
        @require_scopes on the same handler SHALL produce a merged policy
        whose roles are the union of all applied roles, whose scopes are
        the union of all applied scopes, and whose require_auth is True.
    """
    iteration_count = 100

    for iteration in range(iteration_count):
        roles_a = _random_string_tuple(max_length=4)
        roles_b = _random_string_tuple(max_length=4)
        scopes_a = _random_string_tuple(max_length=4)
        scopes_b = _random_string_tuple(max_length=4)

        # --- Stack @require_roles(roles_a) then @require_roles(roles_b) ---
        def handler_roles():
            return

        decorated_roles = require_roles(*roles_b)(require_roles(*roles_a)(handler_roles))

        policy_roles = get_handler_policy(decorated_roles)

        expected_roles = _order_preserving_union(roles_a, roles_b)
        if policy_roles.roles != expected_roles:
            errmsg = (
                f"Iteration {iteration}: Stacked roles mismatch. "
                f"roles_a={roles_a}, roles_b={roles_b}, "
                f"expected={expected_roles}, got={policy_roles.roles}"
            )
            raise AssertionError(errmsg)

        # --- Stack @require_scopes(scopes_a) then @require_scopes(scopes_b) ---
        def handler_scopes():
            return

        decorated_scopes = require_scopes(*scopes_b)(require_scopes(*scopes_a)(handler_scopes))

        policy_scopes = get_handler_policy(decorated_scopes)

        expected_scopes = _order_preserving_union(scopes_a, scopes_b)
        if policy_scopes.scopes != expected_scopes:
            errmsg = (
                f"Iteration {iteration}: Stacked scopes mismatch. "
                f"scopes_a={scopes_a}, scopes_b={scopes_b}, "
                f"expected={expected_scopes}, got={policy_scopes.scopes}"
            )
            raise AssertionError(errmsg)

        # --- Stack @require_roles and @require_scopes together ---
        def handler_combined():
            return

        decorated_combined = require_scopes(*scopes_a)(require_roles(*roles_a)(handler_combined))

        policy_combined = get_handler_policy(decorated_combined)

        if policy_combined.roles != roles_a:
            errmsg = (
                f"Iteration {iteration}: Combined stack roles mismatch. "
                f"expected={roles_a}, got={policy_combined.roles}"
            )
            raise AssertionError(errmsg)

        if policy_combined.scopes != scopes_a:
            errmsg = (
                f"Iteration {iteration}: Combined stack scopes mismatch. "
                f"expected={scopes_a}, got={policy_combined.scopes}"
            )
            raise AssertionError(errmsg)

        if policy_combined.require_auth is not True:
            errmsg = (
                f"Iteration {iteration}: Combined stack require_auth mismatch. "
                f"expected=True, got={policy_combined.require_auth}"
            )
            raise AssertionError(errmsg)

        # --- Stack @public_endpoint with @require_auth: auth wins via OR ---
        def handler_public_auth():
            return

        decorated_pub_auth = require_auth(public_endpoint(handler_public_auth))

        policy_pub_auth = get_handler_policy(decorated_pub_auth)

        if policy_pub_auth.require_auth is not True:
            errmsg = (
                f"Iteration {iteration}: public + require_auth should yield "
                f"require_auth=True, got {policy_pub_auth.require_auth}"
            )
            raise AssertionError(errmsg)

    return
