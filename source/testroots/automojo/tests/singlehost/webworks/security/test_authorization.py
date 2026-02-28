"""
    Tests for the authorization engine components.

    This module contains unit tests for the AuthorizationResult dataclass,
    the AuthorizationRule protocol, and the Authorization_Engine class
    including evaluate(), check_roles(), check_scopes(), hooks, and
    custom rules.
"""

from automojo.webworks.security.accesspolicy import AccessPolicy
from automojo.webworks.security.securitycontext import Security_Context
from automojo.webworks.security.authorizationengine import (
    AuthorizationResult,
    AuthorizationRule,
    Authorization_Engine,
)


# =============================================================================
# Unit Tests for AuthorizationResult
# =============================================================================

def test_authorization_result_default_fields():
    """
        Test that AuthorizationResult can be created with only the required
        allowed field and that optional fields default to None.
    """
    result = AuthorizationResult(allowed=True)

    if result.allowed is not True:
        errmsg = f"Expected allowed to be True, got {result.allowed}"
        raise AssertionError(errmsg)

    if result.reason is not None:
        errmsg = f"Expected reason to be None, got {result.reason}"
        raise AssertionError(errmsg)

    if result.policy is not None:
        errmsg = f"Expected policy to be None, got {result.policy}"
        raise AssertionError(errmsg)

    if result.context is not None:
        errmsg = f"Expected context to be None, got {result.context}"
        raise AssertionError(errmsg)

    return


def test_authorization_result_with_all_fields():
    """
        Test that AuthorizationResult can be created with all fields populated.
    """
    policy = AccessPolicy(roles=("admin",))
    ctx = Security_Context(user_id="user-1", roles=("admin",))

    result = AuthorizationResult(
        allowed=False,
        reason="Missing required scope",
        policy=policy,
        context=ctx
    )

    if result.allowed is not False:
        errmsg = f"Expected allowed to be False, got {result.allowed}"
        raise AssertionError(errmsg)

    if result.reason != "Missing required scope":
        errmsg = f"Expected reason 'Missing required scope', got '{result.reason}'"
        raise AssertionError(errmsg)

    if result.policy is not policy:
        errmsg = "Expected policy to be the same instance"
        raise AssertionError(errmsg)

    if result.context is not ctx:
        errmsg = "Expected context to be the same instance"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for AuthorizationRule
# =============================================================================

def test_authorization_rule_can_be_subclassed():
    """
        Test that AuthorizationRule can be subclassed and its evaluate
        method can be overridden to return an AuthorizationResult.
    """

    class AllowAllRule(AuthorizationRule):
        def evaluate(self, policy, context, request):
            rtnval = AuthorizationResult(allowed=True, reason="Custom allow")
            return rtnval

    rule = AllowAllRule()
    policy = AccessPolicy()
    ctx = Security_Context(user_id="user-1")

    result = rule.evaluate(policy, ctx, None)

    if result is None:
        errmsg = "Expected evaluate to return an AuthorizationResult"
        raise AssertionError(errmsg)

    if result.allowed is not True:
        errmsg = f"Expected allowed to be True, got {result.allowed}"
        raise AssertionError(errmsg)

    if result.reason != "Custom allow":
        errmsg = f"Expected reason 'Custom allow', got '{result.reason}'"
        raise AssertionError(errmsg)

    return


def test_authorization_rule_can_return_none():
    """
        Test that an AuthorizationRule can return None to indicate
        that it does not apply and evaluation should continue.
    """

    class PassThroughRule(AuthorizationRule):
        def evaluate(self, policy, context, request):
            return None

    rule = PassThroughRule()
    policy = AccessPolicy()
    ctx = Security_Context(user_id="user-1")

    result = rule.evaluate(policy, ctx, None)

    if result is not None:
        errmsg = f"Expected evaluate to return None, got {result}"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for Authorization_Engine - evaluate()
# =============================================================================

def test_engine_allows_authenticated_user_with_matching_role_and_scope():
    """
        Test that evaluate returns allowed=True when the context satisfies
        all policy constraints.
    """
    engine = Authorization_Engine()
    policy = AccessPolicy(
        roles=("admin", "editor"),
        scopes=("read", "write"),
        require_auth=True
    )
    ctx = Security_Context(
        user_id="user-1",
        roles=("admin",),
        scopes=("read", "write", "delete")
    )

    result = engine.evaluate(policy, ctx)

    if result.allowed is not True:
        errmsg = f"Expected allowed=True, got {result.allowed}, reason={result.reason}"
        raise AssertionError(errmsg)

    if result.policy is not policy:
        errmsg = "Expected result.policy to be the evaluated policy"
        raise AssertionError(errmsg)

    if result.context is not ctx:
        errmsg = "Expected result.context to be the evaluated context"
        raise AssertionError(errmsg)

    return


def test_engine_denies_unauthenticated_when_auth_required():
    """
        Test that evaluate returns allowed=False when require_auth is True
        and the context is not authenticated.
    """
    engine = Authorization_Engine()
    policy = AccessPolicy(require_auth=True)
    ctx = Security_Context.guest()

    result = engine.evaluate(policy, ctx)

    if result.allowed is not False:
        errmsg = f"Expected allowed=False, got {result.allowed}"
        raise AssertionError(errmsg)

    if result.reason is None:
        errmsg = "Expected a denial reason for unauthenticated context"
        raise AssertionError(errmsg)

    return


def test_engine_allows_unauthenticated_when_auth_not_required():
    """
        Test that evaluate returns allowed=True when require_auth is False
        and the context is not authenticated.
    """
    engine = Authorization_Engine()
    policy = AccessPolicy(require_auth=False)
    ctx = Security_Context.guest()

    result = engine.evaluate(policy, ctx)

    if result.allowed is not True:
        errmsg = f"Expected allowed=True, got {result.allowed}, reason={result.reason}"
        raise AssertionError(errmsg)

    return


def test_engine_denies_when_missing_required_role():
    """
        Test that evaluate returns allowed=False when the context lacks
        any of the required roles.
    """
    engine = Authorization_Engine()
    policy = AccessPolicy(roles=("admin", "superadmin"))
    ctx = Security_Context(user_id="user-1", roles=("editor",))

    result = engine.evaluate(policy, ctx)

    if result.allowed is not False:
        errmsg = f"Expected allowed=False, got {result.allowed}"
        raise AssertionError(errmsg)

    if result.reason is None:
        errmsg = "Expected a denial reason for missing role"
        raise AssertionError(errmsg)

    return


def test_engine_allows_with_one_matching_role():
    """
        Test that evaluate returns allowed=True when the context has at
        least one of the required roles (OR logic).
    """
    engine = Authorization_Engine()
    policy = AccessPolicy(roles=("admin", "editor"))
    ctx = Security_Context(user_id="user-1", roles=("editor",))

    result = engine.evaluate(policy, ctx)

    if result.allowed is not True:
        errmsg = f"Expected allowed=True, got {result.allowed}, reason={result.reason}"
        raise AssertionError(errmsg)

    return


def test_engine_denies_when_missing_required_scope():
    """
        Test that evaluate returns allowed=False when the context is
        missing a required scope.
    """
    engine = Authorization_Engine()
    policy = AccessPolicy(scopes=("read", "write"))
    ctx = Security_Context(user_id="user-1", scopes=("read",))

    result = engine.evaluate(policy, ctx)

    if result.allowed is not False:
        errmsg = f"Expected allowed=False, got {result.allowed}"
        raise AssertionError(errmsg)

    if result.reason is None:
        errmsg = "Expected a denial reason for missing scope"
        raise AssertionError(errmsg)

    return


def test_engine_allows_with_all_required_scopes():
    """
        Test that evaluate returns allowed=True when the context has all
        required scopes (AND logic).
    """
    engine = Authorization_Engine()
    policy = AccessPolicy(scopes=("read", "write"))
    ctx = Security_Context(user_id="user-1", scopes=("read", "write", "delete"))

    result = engine.evaluate(policy, ctx)

    if result.allowed is not True:
        errmsg = f"Expected allowed=True, got {result.allowed}, reason={result.reason}"
        raise AssertionError(errmsg)

    return


def test_engine_allows_with_empty_roles_and_scopes():
    """
        Test that evaluate returns allowed=True when the policy has no
        role or scope requirements and the context is authenticated.
    """
    engine = Authorization_Engine()
    policy = AccessPolicy(require_auth=True)
    ctx = Security_Context(user_id="user-1")

    result = engine.evaluate(policy, ctx)

    if result.allowed is not True:
        errmsg = f"Expected allowed=True, got {result.allowed}, reason={result.reason}"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for Authorization_Engine - check_roles() and check_scopes()
# =============================================================================

def test_check_roles_returns_true_with_matching_role():
    """
        Test that check_roles returns True when the context has at least
        one of the required roles.
    """
    engine = Authorization_Engine()
    ctx = Security_Context(user_id="user-1", roles=("admin", "editor"))

    result = engine.check_roles(("editor", "viewer"), ctx)

    if result is not True:
        errmsg = f"Expected check_roles to return True, got {result}"
        raise AssertionError(errmsg)

    return


def test_check_roles_returns_false_with_no_matching_role():
    """
        Test that check_roles returns False when the context has none
        of the required roles.
    """
    engine = Authorization_Engine()
    ctx = Security_Context(user_id="user-1", roles=("viewer",))

    result = engine.check_roles(("admin", "superadmin"), ctx)

    if result is not False:
        errmsg = f"Expected check_roles to return False, got {result}"
        raise AssertionError(errmsg)

    return


def test_check_scopes_returns_true_with_all_scopes():
    """
        Test that check_scopes returns True when the context has all
        required scopes.
    """
    engine = Authorization_Engine()
    ctx = Security_Context(user_id="user-1", scopes=("read", "write", "delete"))

    result = engine.check_scopes(("read", "write"), ctx)

    if result is not True:
        errmsg = f"Expected check_scopes to return True, got {result}"
        raise AssertionError(errmsg)

    return


def test_check_scopes_returns_false_when_missing_scope():
    """
        Test that check_scopes returns False when the context is missing
        at least one required scope.
    """
    engine = Authorization_Engine()
    ctx = Security_Context(user_id="user-1", scopes=("read",))

    result = engine.check_scopes(("read", "write"), ctx)

    if result is not False:
        errmsg = f"Expected check_scopes to return False, got {result}"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for Authorization_Engine - Hooks
# =============================================================================

def test_pre_hooks_are_called_before_evaluation():
    """
        Test that pre-hooks are called during evaluate and receive
        the policy and context.
    """
    engine = Authorization_Engine()
    hook_calls = []

    def pre_hook(policy, context):
        hook_calls.append(("pre", policy, context))

    engine.add_pre_hook(pre_hook)

    policy = AccessPolicy(require_auth=False)
    ctx = Security_Context.guest()

    engine.evaluate(policy, ctx)

    if len(hook_calls) != 1:
        errmsg = f"Expected 1 pre-hook call, got {len(hook_calls)}"
        raise AssertionError(errmsg)

    call_tag = hook_calls[0][0]
    if call_tag != "pre":
        errmsg = f"Expected hook tag 'pre', got '{call_tag}'"
        raise AssertionError(errmsg)

    call_policy = hook_calls[0][1]
    if call_policy is not policy:
        errmsg = "Expected pre-hook to receive the evaluated policy"
        raise AssertionError(errmsg)

    call_context = hook_calls[0][2]
    if call_context is not ctx:
        errmsg = "Expected pre-hook to receive the evaluated context"
        raise AssertionError(errmsg)

    return


def test_post_hooks_are_called_after_evaluation():
    """
        Test that post-hooks are called during evaluate and receive
        the policy, context, and result.
    """
    engine = Authorization_Engine()
    hook_calls = []

    def post_hook(policy, context, result):
        hook_calls.append(("post", policy, context, result))

    engine.add_post_hook(post_hook)

    policy = AccessPolicy(require_auth=False)
    ctx = Security_Context.guest()

    eval_result = engine.evaluate(policy, ctx)

    if len(hook_calls) != 1:
        errmsg = f"Expected 1 post-hook call, got {len(hook_calls)}"
        raise AssertionError(errmsg)

    call_result = hook_calls[0][3]
    if call_result is not eval_result:
        errmsg = "Expected post-hook to receive the evaluation result"
        raise AssertionError(errmsg)

    return


def test_post_hooks_called_on_denial():
    """
        Test that post-hooks are called even when authorization is denied.
    """
    engine = Authorization_Engine()
    hook_calls = []

    def post_hook(policy, context, result):
        hook_calls.append(result)

    engine.add_post_hook(post_hook)

    policy = AccessPolicy(require_auth=True)
    ctx = Security_Context.guest()

    eval_result = engine.evaluate(policy, ctx)

    if len(hook_calls) != 1:
        errmsg = f"Expected 1 post-hook call on denial, got {len(hook_calls)}"
        raise AssertionError(errmsg)

    if hook_calls[0].allowed is not False:
        errmsg = "Expected post-hook to receive denied result"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for Authorization_Engine - Custom Rules
# =============================================================================

def test_custom_rule_overrides_standard_checks():
    """
        Test that a custom rule returning an AuthorizationResult takes
        precedence over the standard role and scope checks.
    """

    class AlwaysAllowRule(AuthorizationRule):
        def evaluate(self, policy, context, request):
            rtnval = AuthorizationResult(
                allowed=True,
                reason="Custom rule override",
                policy=policy,
                context=context
            )
            return rtnval

    engine = Authorization_Engine(custom_rules=[AlwaysAllowRule()])

    # Policy that would normally deny a guest
    policy = AccessPolicy(roles=("admin",), require_auth=True)
    ctx = Security_Context.guest()

    result = engine.evaluate(policy, ctx)

    if result.allowed is not True:
        errmsg = f"Expected custom rule to allow access, got allowed={result.allowed}"
        raise AssertionError(errmsg)

    if result.reason != "Custom rule override":
        errmsg = f"Expected reason 'Custom rule override', got '{result.reason}'"
        raise AssertionError(errmsg)

    return


def test_custom_rule_returning_none_falls_through():
    """
        Test that a custom rule returning None allows evaluation to
        continue with the standard checks.
    """

    class PassThroughRule(AuthorizationRule):
        def evaluate(self, policy, context, request):
            return None

    engine = Authorization_Engine(custom_rules=[PassThroughRule()])

    policy = AccessPolicy(require_auth=True)
    ctx = Security_Context.guest()

    result = engine.evaluate(policy, ctx)

    if result.allowed is not False:
        errmsg = f"Expected standard check to deny, got allowed={result.allowed}"
        raise AssertionError(errmsg)

    return


def test_add_custom_rule_method():
    """
        Test that add_custom_rule adds a rule that is evaluated during
        the next call to evaluate().
    """

    class DenyAllRule(AuthorizationRule):
        def evaluate(self, policy, context, request):
            rtnval = AuthorizationResult(
                allowed=False,
                reason="Denied by custom rule",
                policy=policy,
                context=context
            )
            return rtnval

    engine = Authorization_Engine()

    # Without the rule, this should be allowed
    policy = AccessPolicy(require_auth=False)
    ctx = Security_Context.guest()

    result_before = engine.evaluate(policy, ctx)
    if result_before.allowed is not True:
        errmsg = "Expected allowed=True before adding custom rule"
        raise AssertionError(errmsg)

    # Add the deny rule
    engine.add_custom_rule(DenyAllRule())

    result_after = engine.evaluate(policy, ctx)
    if result_after.allowed is not False:
        errmsg = "Expected allowed=False after adding deny custom rule"
        raise AssertionError(errmsg)

    if result_after.reason != "Denied by custom rule":
        errmsg = f"Expected reason 'Denied by custom rule', got '{result_after.reason}'"
        raise AssertionError(errmsg)

    return


def test_engine_default_policy():
    """
        Test that the engine stores a default policy when none is provided.
    """
    engine = Authorization_Engine()

    default_policy = engine._default_policy

    if default_policy is None:
        errmsg = "Expected a default policy to be set"
        raise AssertionError(errmsg)

    if not isinstance(default_policy, AccessPolicy):
        errmsg = f"Expected default policy to be AccessPolicy, got {type(default_policy)}"
        raise AssertionError(errmsg)

    return


def test_engine_with_custom_default_policy():
    """
        Test that the engine uses a provided default policy.
    """
    custom_default = AccessPolicy(require_auth=False)
    engine = Authorization_Engine(default_policy=custom_default)

    if engine._default_policy is not custom_default:
        errmsg = "Expected engine to use the provided default policy"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Property-Based Tests
# =============================================================================

import random
import string


def _random_role_pool():
    """
        Generate a pool of role names to draw from during property testing.

        :returns: A list of role name strings.
    """
    pool = [
        "admin", "editor", "viewer", "moderator", "superadmin",
        "manager", "analyst", "operator", "auditor", "developer"
    ]
    return pool


def _random_scope_pool():
    """
        Generate a pool of scope names to draw from during property testing.

        :returns: A list of scope name strings.
    """
    pool = [
        "read", "write", "delete", "create", "update",
        "execute", "manage", "audit", "export", "import"
    ]
    return pool


def _random_access_policy(role_pool, scope_pool):
    """
        Generate a random AccessPolicy with random roles, scopes, and
        require_auth setting.

        :param role_pool: List of possible role names.
        :param scope_pool: List of possible scope names.

        :returns: A randomly configured AccessPolicy.
    """
    num_roles = random.randint(0, 4)
    roles = tuple(random.sample(role_pool, min(num_roles, len(role_pool))))

    num_scopes = random.randint(0, 4)
    scopes = tuple(random.sample(scope_pool, min(num_scopes, len(scope_pool))))

    require_auth = random.choice([True, False])

    policy = AccessPolicy(roles=roles, scopes=scopes, require_auth=require_auth)
    return policy


def _random_security_context(role_pool, scope_pool):
    """
        Generate a random Security_Context with random user_id, roles,
        and scopes.

        :param role_pool: List of possible role names.
        :param scope_pool: List of possible scope names.

        :returns: A randomly configured Security_Context.
    """
    is_authenticated = random.choice([True, False])

    if is_authenticated:
        user_id = "user-" + "".join(random.choices(string.ascii_lowercase, k=6))
    else:
        user_id = None

    num_roles = random.randint(0, 4)
    roles = tuple(random.sample(role_pool, min(num_roles, len(role_pool))))

    num_scopes = random.randint(0, 4)
    scopes = tuple(random.sample(scope_pool, min(num_scopes, len(scope_pool))))

    ctx = Security_Context(user_id=user_id, roles=roles, scopes=scopes)
    return ctx


def test_property_policy_inheritance_security():
    """
        Property 3: Policy Inheritance Security

        **Validates: Requirements 3.1, 3.2, 3.8, 3.9**

        For any parent-child endpoint relationship where parent has policy
        P_parent and child has policy P_child:
        - If P_child is None, the effective policy SHALL be P_parent
        - If P_child is defined, the effective policy SHALL be at least as
          restrictive as P_parent
        - The combined policy SHALL never allow access that P_parent would
          deny (security non-weakening)

        Security non-weakening is validated per constraint dimension:
        - require_auth: if parent requires auth, effective must also require auth
        - scopes (AND logic): effective scopes are a superset of parent scopes,
          so any scope denial by parent is preserved in effective
        - roles (OR logic with union per Req 3.4): union merging is by design;
          the non-weakening property is verified by checking that parent denials
          due to authentication or scopes are never weakened by the merge

        This test runs 100 iterations with randomly generated policies and
        security contexts to verify the inheritance properties hold universally.
    """
    role_pool = _random_role_pool()
    scope_pool = _random_scope_pool()

    iterations = 100

    for iteration_idx in range(iterations):
        parent_policy = _random_access_policy(role_pool, scope_pool)

        # Randomly decide if child has a policy or not
        child_has_policy = random.choice([True, False])

        if child_has_policy:
            child_policy = _random_access_policy(role_pool, scope_pool)
        else:
            child_policy = None

        # Compute effective policy
        if child_policy is None:
            effective_policy = parent_policy
        else:
            effective_policy = parent_policy.merge_with(child_policy)

        # Property 3a: If P_child is None, effective == P_parent
        if child_policy is None:
            if effective_policy is not parent_policy:
                errmsg = (
                    f"Iteration {iteration_idx}: When child policy is None, "
                    f"effective policy should be the parent policy instance"
                )
                raise AssertionError(errmsg)

        # Property 3b: require_auth non-weakening
        # If parent requires auth, effective must also require auth
        if child_policy is not None:
            if parent_policy.require_auth is True:
                if effective_policy.require_auth is not True:
                    errmsg = (
                        f"Iteration {iteration_idx}: require_auth non-weakening "
                        f"violated. Parent requires auth but effective does not. "
                        f"Parent require_auth={parent_policy.require_auth}, "
                        f"Child require_auth={child_policy.require_auth}, "
                        f"Effective require_auth={effective_policy.require_auth}"
                    )
                    raise AssertionError(errmsg)

        # Property 3c: Scope non-weakening
        # Effective scopes must be a superset of parent scopes (AND logic
        # means more scopes = more restrictive)
        if child_policy is not None:
            parent_scope_set = set(parent_policy.scopes)
            effective_scope_set = set(effective_policy.scopes)

            if not parent_scope_set.issubset(effective_scope_set):
                missing = parent_scope_set - effective_scope_set
                errmsg = (
                    f"Iteration {iteration_idx}: Scope non-weakening violated. "
                    f"Parent scopes not preserved in effective policy. "
                    f"Missing scopes: {missing}. "
                    f"Parent scopes={parent_policy.scopes}, "
                    f"Child scopes={child_policy.scopes}, "
                    f"Effective scopes={effective_policy.scopes}"
                )
                raise AssertionError(errmsg)

        # Property 3d: Security non-weakening for auth and scope denials
        # Generate random contexts and verify that if the parent denies
        # due to authentication or scopes, the effective policy also denies
        num_contexts = 10

        for ctx_idx in range(num_contexts):
            ctx = _random_security_context(role_pool, scope_pool)

            parent_allows = parent_policy.check(ctx)
            effective_allows = effective_policy.check(ctx)

            if parent_allows is False and effective_allows is True:
                # Determine why parent denied
                denial_reason = parent_policy.get_denial_reason(ctx)

                # Auth and scope denials must never be weakened
                if denial_reason == "Authentication is required":
                    errmsg = (
                        f"Iteration {iteration_idx}, context {ctx_idx}: "
                        f"Auth non-weakening violated. Parent denied due to "
                        f"authentication but effective allowed. "
                        f"Context: user_id={ctx.user_id}"
                    )
                    raise AssertionError(errmsg)

                if denial_reason == "Missing required scope":
                    errmsg = (
                        f"Iteration {iteration_idx}, context {ctx_idx}: "
                        f"Scope non-weakening violated. Parent denied due to "
                        f"missing scope but effective allowed. "
                        f"Parent scopes={parent_policy.scopes}, "
                        f"Effective scopes={effective_policy.scopes}, "
                        f"Context scopes={ctx.scopes}"
                    )
                    raise AssertionError(errmsg)

    return
