"""
    Tests for the AccessPolicy frozen dataclass.

    This module contains unit tests for the AccessPolicy class including
    field defaults, merge_with() behavior, check() evaluation logic,
    get_denial_reason() output, and immutability verification.
"""

from ccai.webworks.security.accesspolicy import AccessPolicy
from ccai.webworks.security.securitycontext import SecurityContext


# =============================================================================
# Unit Tests for AccessPolicy Fields and Defaults
# =============================================================================

def test_access_policy_default_fields():
    """
        Test that a default AccessPolicy has expected default values.
    """
    policy = AccessPolicy()

    if policy.roles != ():
        errmsg = f"Expected roles to be empty tuple, got {policy.roles}"
        raise AssertionError(errmsg)

    if policy.scopes != ():
        errmsg = f"Expected scopes to be empty tuple, got {policy.scopes}"
        raise AssertionError(errmsg)

    if policy.require_auth is not True:
        errmsg = f"Expected require_auth to be True, got {policy.require_auth}"
        raise AssertionError(errmsg)

    if policy.constraints != {}:
        errmsg = f"Expected constraints to be empty dict, got {policy.constraints}"
        raise AssertionError(errmsg)

    return


def test_access_policy_with_all_fields():
    """
        Test that AccessPolicy can be created with all fields populated.
    """
    policy = AccessPolicy(
        roles=("admin", "editor"),
        scopes=("read", "write"),
        require_auth=False,
        constraints={"max_rate": 100}
    )

    if policy.roles != ("admin", "editor"):
        errmsg = f"Expected roles ('admin', 'editor'), got {policy.roles}"
        raise AssertionError(errmsg)

    if policy.scopes != ("read", "write"):
        errmsg = f"Expected scopes ('read', 'write'), got {policy.scopes}"
        raise AssertionError(errmsg)

    if policy.require_auth is not False:
        errmsg = f"Expected require_auth to be False, got {policy.require_auth}"
        raise AssertionError(errmsg)

    if policy.constraints != {"max_rate": 100}:
        errmsg = f"Expected constraints {{'max_rate': 100}}, got {policy.constraints}"
        raise AssertionError(errmsg)

    return


def test_access_policy_is_immutable():
    """
        Test that AccessPolicy fields cannot be modified after creation.
    """
    policy = AccessPolicy(roles=("admin",), scopes=("read",))

    try:
        policy.roles = ("hacker",)
        errmsg = "Expected FrozenInstanceError when setting roles"
        raise AssertionError(errmsg)
    except AttributeError:
        pass

    try:
        policy.require_auth = False
        errmsg = "Expected FrozenInstanceError when setting require_auth"
        raise AssertionError(errmsg)
    except AttributeError:
        pass

    return


# =============================================================================
# Unit Tests for merge_with()
# =============================================================================

def test_merge_with_unions_roles_by_default():
    """
        Test that merge_with combines roles as a union by default.
    """
    policy_a = AccessPolicy(roles=("admin", "editor"))
    policy_b = AccessPolicy(roles=("editor", "viewer"))

    merged = policy_a.merge_with(policy_b)

    expected_roles = ("admin", "editor", "viewer")
    if merged.roles != expected_roles:
        errmsg = f"Expected merged roles {expected_roles}, got {merged.roles}"
        raise AssertionError(errmsg)

    return


def test_merge_with_unions_scopes_by_default():
    """
        Test that merge_with combines scopes as a union by default.
    """
    policy_a = AccessPolicy(scopes=("read", "write"))
    policy_b = AccessPolicy(scopes=("write", "delete"))

    merged = policy_a.merge_with(policy_b)

    expected_scopes = ("read", "write", "delete")
    if merged.scopes != expected_scopes:
        errmsg = f"Expected merged scopes {expected_scopes}, got {merged.scopes}"
        raise AssertionError(errmsg)

    return


def test_merge_with_replace_roles():
    """
        Test that merge_with replaces roles when replace_roles is True.
    """
    policy_a = AccessPolicy(roles=("admin", "editor"))
    policy_b = AccessPolicy(roles=("viewer",))

    merged = policy_a.merge_with(policy_b, replace_roles=True)

    expected_roles = ("viewer",)
    if merged.roles != expected_roles:
        errmsg = f"Expected replaced roles {expected_roles}, got {merged.roles}"
        raise AssertionError(errmsg)

    return


def test_merge_with_replace_scopes():
    """
        Test that merge_with replaces scopes when replace_scopes is True.
    """
    policy_a = AccessPolicy(scopes=("read", "write"))
    policy_b = AccessPolicy(scopes=("delete",))

    merged = policy_a.merge_with(policy_b, replace_scopes=True)

    expected_scopes = ("delete",)
    if merged.scopes != expected_scopes:
        errmsg = f"Expected replaced scopes {expected_scopes}, got {merged.scopes}"
        raise AssertionError(errmsg)

    return


def test_merge_with_require_auth_or_logic():
    """
        Test that merged require_auth is True if either policy requires auth.
    """
    policy_no_auth = AccessPolicy(require_auth=False)
    policy_auth = AccessPolicy(require_auth=True)

    merged_a = policy_no_auth.merge_with(policy_auth)
    if merged_a.require_auth is not True:
        errmsg = f"Expected require_auth True when other requires auth, got {merged_a.require_auth}"
        raise AssertionError(errmsg)

    merged_b = policy_auth.merge_with(policy_no_auth)
    if merged_b.require_auth is not True:
        errmsg = f"Expected require_auth True when self requires auth, got {merged_b.require_auth}"
        raise AssertionError(errmsg)

    merged_c = policy_no_auth.merge_with(policy_no_auth)
    if merged_c.require_auth is not False:
        errmsg = f"Expected require_auth False when neither requires auth, got {merged_c.require_auth}"
        raise AssertionError(errmsg)

    return


def test_merge_with_combines_constraints():
    """
        Test that merge_with merges constraints dicts with other overriding self.
    """
    policy_a = AccessPolicy(constraints={"max_rate": 100, "region": "us"})
    policy_b = AccessPolicy(constraints={"max_rate": 200, "tier": "premium"})

    merged = policy_a.merge_with(policy_b)

    if merged.constraints.get("max_rate") != 200:
        errmsg = f"Expected max_rate 200 (overridden by other), got {merged.constraints.get('max_rate')}"
        raise AssertionError(errmsg)

    if merged.constraints.get("region") != "us":
        errmsg = f"Expected region 'us' (from self), got {merged.constraints.get('region')}"
        raise AssertionError(errmsg)

    if merged.constraints.get("tier") != "premium":
        errmsg = f"Expected tier 'premium' (from other), got {merged.constraints.get('tier')}"
        raise AssertionError(errmsg)

    return


def test_merge_with_returns_new_policy():
    """
        Test that merge_with returns a new AccessPolicy instance.
    """
    policy_a = AccessPolicy(roles=("admin",))
    policy_b = AccessPolicy(roles=("editor",))

    merged = policy_a.merge_with(policy_b)

    if merged is policy_a:
        errmsg = "Expected merged policy to be a new instance, not policy_a"
        raise AssertionError(errmsg)

    if merged is policy_b:
        errmsg = "Expected merged policy to be a new instance, not policy_b"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for check()
# =============================================================================

def test_check_passes_for_authenticated_user_with_role_and_scope():
    """
        Test that check returns True when all constraints are satisfied.
    """
    policy = AccessPolicy(
        roles=("admin", "editor"),
        scopes=("read", "write"),
        require_auth=True
    )
    ctx = SecurityContext(
        user_id="user-1",
        roles=("admin",),
        scopes=("read", "write", "delete")
    )

    result = policy.check(ctx)

    if result is not True:
        errmsg = "Expected check to return True for fully satisfied context"
        raise AssertionError(errmsg)

    return


def test_check_fails_when_not_authenticated():
    """
        Test that check returns False when require_auth is True and context
        is not authenticated.
    """
    policy = AccessPolicy(require_auth=True)
    ctx = SecurityContext.guest()

    result = policy.check(ctx)

    if result is not False:
        errmsg = "Expected check to return False for unauthenticated guest"
        raise AssertionError(errmsg)

    return


def test_check_passes_when_auth_not_required():
    """
        Test that check returns True when require_auth is False and context
        is not authenticated.
    """
    policy = AccessPolicy(require_auth=False)
    ctx = SecurityContext.guest()

    result = policy.check(ctx)

    if result is not True:
        errmsg = "Expected check to return True when auth not required"
        raise AssertionError(errmsg)

    return


def test_check_fails_when_missing_required_role():
    """
        Test that check returns False when the context lacks any required role.
    """
    policy = AccessPolicy(roles=("admin", "superadmin"))
    ctx = SecurityContext(user_id="user-1", roles=("editor",))

    result = policy.check(ctx)

    if result is not False:
        errmsg = "Expected check to return False when no required role is present"
        raise AssertionError(errmsg)

    return


def test_check_passes_with_one_matching_role():
    """
        Test that check returns True when the context has at least one
        of the required roles (OR logic).
    """
    policy = AccessPolicy(roles=("admin", "editor"))
    ctx = SecurityContext(user_id="user-1", roles=("editor",))

    result = policy.check(ctx)

    if result is not True:
        errmsg = "Expected check to return True when one required role matches"
        raise AssertionError(errmsg)

    return


def test_check_fails_when_missing_required_scope():
    """
        Test that check returns False when the context is missing a required scope.
    """
    policy = AccessPolicy(scopes=("read", "write"))
    ctx = SecurityContext(user_id="user-1", scopes=("read",))

    result = policy.check(ctx)

    if result is not False:
        errmsg = "Expected check to return False when a required scope is missing"
        raise AssertionError(errmsg)

    return


def test_check_passes_with_all_required_scopes():
    """
        Test that check returns True when the context has all required scopes
        (AND logic).
    """
    policy = AccessPolicy(scopes=("read", "write"))
    ctx = SecurityContext(user_id="user-1", scopes=("read", "write", "delete"))

    result = policy.check(ctx)

    if result is not True:
        errmsg = "Expected check to return True when all required scopes present"
        raise AssertionError(errmsg)

    return


def test_check_passes_with_empty_roles_and_scopes():
    """
        Test that check returns True when policy has no role or scope requirements
        and the context is authenticated.
    """
    policy = AccessPolicy(require_auth=True)
    ctx = SecurityContext(user_id="user-1")

    result = policy.check(ctx)

    if result is not True:
        errmsg = "Expected check to return True with no role/scope requirements"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for get_denial_reason()
# =============================================================================

def test_get_denial_reason_returns_none_when_check_passes():
    """
        Test that get_denial_reason returns None when the context satisfies
        the policy.
    """
    policy = AccessPolicy(roles=("admin",), scopes=("read",))
    ctx = SecurityContext(user_id="user-1", roles=("admin",), scopes=("read",))

    reason = policy.get_denial_reason(ctx)

    if reason is not None:
        errmsg = f"Expected None when check passes, got '{reason}'"
        raise AssertionError(errmsg)

    return


def test_get_denial_reason_for_unauthenticated():
    """
        Test that get_denial_reason returns authentication message for
        unauthenticated context.
    """
    policy = AccessPolicy(require_auth=True)
    ctx = SecurityContext.guest()

    reason = policy.get_denial_reason(ctx)

    if reason is None:
        errmsg = "Expected a denial reason for unauthenticated context"
        raise AssertionError(errmsg)

    if "Authentication" not in reason and "authentication" not in reason:
        errmsg = f"Expected reason to mention authentication, got '{reason}'"
        raise AssertionError(errmsg)

    return


def test_get_denial_reason_for_missing_role():
    """
        Test that get_denial_reason returns role message when required role
        is missing.
    """
    policy = AccessPolicy(roles=("admin",))
    ctx = SecurityContext(user_id="user-1", roles=("editor",))

    reason = policy.get_denial_reason(ctx)

    if reason is None:
        errmsg = "Expected a denial reason for missing role"
        raise AssertionError(errmsg)

    if "role" not in reason and "Role" not in reason:
        errmsg = f"Expected reason to mention role, got '{reason}'"
        raise AssertionError(errmsg)

    return


def test_get_denial_reason_for_missing_scope():
    """
        Test that get_denial_reason returns scope message when required scope
        is missing.
    """
    policy = AccessPolicy(scopes=("read", "write"))
    ctx = SecurityContext(user_id="user-1", scopes=("read",))

    reason = policy.get_denial_reason(ctx)

    if reason is None:
        errmsg = "Expected a denial reason for missing scope"
        raise AssertionError(errmsg)

    if "scope" not in reason and "Scope" not in reason:
        errmsg = f"Expected reason to mention scope, got '{reason}'"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Property-Based Tests for Policy Merge Behavior
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


def _random_access_policy():
    """
        Generate a random AccessPolicy with random roles, scopes, require_auth,
        and constraints.

        :returns: A randomly configured AccessPolicy instance.
    """
    roles = _random_string_tuple()
    scopes = _random_string_tuple()
    require_auth = random.choice([True, False])
    constraints = {}
    constraint_count = random.randint(0, 3)
    for _ in range(constraint_count):
        key = "".join(random.choices(string.ascii_lowercase, k=4))
        value = random.randint(0, 100)
        constraints[key] = value

    rtnval = AccessPolicy(
        roles=roles,
        scopes=scopes,
        require_auth=require_auth,
        constraints=constraints
    )

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


def test_property_policy_merge_behavior():
    """
        Property test for Policy Merge Behavior.

        **Validates: Requirements 1.5, 3.3, 3.4, 3.5, 3.6, 3.7**

        For any two AccessPolicy objects P1 and P2, when P1.merge_with(P2)
        is called:
        - The resulting policy's roles SHALL be the union of P1.roles and
          P2.roles (unless replace_roles=True)
        - The resulting policy's scopes SHALL be the union of P1.scopes and
          P2.scopes (unless replace_scopes=True)
        - When replace_roles=True, the result SHALL contain only P2.roles
        - When replace_scopes=True, the result SHALL contain only P2.scopes
        - The resulting policy's require_auth SHALL be True if either P1 or
          P2 requires auth
    """
    iteration_count = 100

    for iteration in range(iteration_count):
        p1 = _random_access_policy()
        p2 = _random_access_policy()

        # --- Default merge: roles and scopes are order-preserving unions ---
        merged_default = p1.merge_with(p2)

        expected_roles = _order_preserving_union(p1.roles, p2.roles)
        if merged_default.roles != expected_roles:
            errmsg = (
                f"Iteration {iteration}: Default merge roles mismatch. "
                f"P1.roles={p1.roles}, P2.roles={p2.roles}, "
                f"expected={expected_roles}, got={merged_default.roles}"
            )
            raise AssertionError(errmsg)

        expected_scopes = _order_preserving_union(p1.scopes, p2.scopes)
        if merged_default.scopes != expected_scopes:
            errmsg = (
                f"Iteration {iteration}: Default merge scopes mismatch. "
                f"P1.scopes={p1.scopes}, P2.scopes={p2.scopes}, "
                f"expected={expected_scopes}, got={merged_default.scopes}"
            )
            raise AssertionError(errmsg)

        # --- require_auth is OR of both policies ---
        expected_auth = p1.require_auth or p2.require_auth
        if merged_default.require_auth != expected_auth:
            errmsg = (
                f"Iteration {iteration}: require_auth mismatch. "
                f"P1.require_auth={p1.require_auth}, P2.require_auth={p2.require_auth}, "
                f"expected={expected_auth}, got={merged_default.require_auth}"
            )
            raise AssertionError(errmsg)

        # --- replace_roles=True: result contains only P2.roles ---
        merged_replace_roles = p1.merge_with(p2, replace_roles=True)
        if merged_replace_roles.roles != p2.roles:
            errmsg = (
                f"Iteration {iteration}: replace_roles merge mismatch. "
                f"P2.roles={p2.roles}, got={merged_replace_roles.roles}"
            )
            raise AssertionError(errmsg)

        # --- replace_scopes=True: result contains only P2.scopes ---
        merged_replace_scopes = p1.merge_with(p2, replace_scopes=True)
        if merged_replace_scopes.scopes != p2.scopes:
            errmsg = (
                f"Iteration {iteration}: replace_scopes merge mismatch. "
                f"P2.scopes={p2.scopes}, got={merged_replace_scopes.scopes}"
            )
            raise AssertionError(errmsg)

    return


# =============================================================================
# Property-Based Tests for Policy Evaluation
# =============================================================================


def _random_security_context():
    """
        Generate a random Security_Context with random authentication state,
        roles, and scopes.

        Approximately half of the generated contexts will be authenticated
        (have a user_id) and half will be guests.

        :returns: A randomly configured Security_Context instance.
    """
    is_authenticated = random.choice([True, False])

    if is_authenticated:
        user_id = "user-" + "".join(random.choices(string.ascii_lowercase, k=4))
    else:
        user_id = None

    roles = _random_string_tuple()
    scopes = _random_string_tuple()

    rtnval = SecurityContext(
        user_id=user_id,
        roles=roles,
        scopes=scopes
    )

    return rtnval


def test_property_policy_evaluation():
    """
        Property test for Policy Evaluation.

        **Validates: Requirements 1.6, 1.7, 5.1, 5.3, 5.4, 5.5**

        For any AccessPolicy P and Security_Context C, P.check(C) SHALL
        return True if and only if:
        - If P.require_auth=True, then C.is_authenticated must be True
        - If P.roles is non-empty, then C must have at least one role
          from P.roles (OR logic)
        - If P.scopes is non-empty, then C must have all scopes from
          P.scopes (AND logic)
    """
    iteration_count = 100

    for iteration in range(iteration_count):
        policy = _random_access_policy()
        ctx = _random_security_context()

        # --- Compute expected result manually ---
        expected = True

        # Condition 1: Authentication check
        if policy.require_auth is True:
            if ctx.is_authenticated is not True:
                expected = False

        # Condition 2: Role check (OR logic)
        if expected is True and len(policy.roles) > 0:
            has_matching_role = any(role in ctx.roles for role in policy.roles)
            if has_matching_role is not True:
                expected = False

        # Condition 3: Scope check (AND logic)
        if expected is True and len(policy.scopes) > 0:
            has_all_scopes = all(scope in ctx.scopes for scope in policy.scopes)
            if has_all_scopes is not True:
                expected = False

        # --- Verify P.check(C) matches expected ---
        actual = policy.check(ctx)

        if actual != expected:
            errmsg = (
                f"Iteration {iteration}: Policy evaluation mismatch. "
                f"policy.require_auth={policy.require_auth}, "
                f"policy.roles={policy.roles}, policy.scopes={policy.scopes}, "
                f"ctx.user_id={ctx.user_id}, ctx.roles={ctx.roles}, "
                f"ctx.scopes={ctx.scopes}, expected={expected}, got={actual}"
            )
            raise AssertionError(errmsg)

    return
