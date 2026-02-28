"""
.. module:: authorizationengine
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Authorization engine for evaluating access policies against
        security contexts to make authorization decisions.

.. moduleauthor:: Automation Mojo LLC

This module provides the authorization engine components for the security
framework. It includes the AuthorizationResult dataclass for representing
authorization decisions, the AuthorizationRule protocol for custom rules,
and the Authorization_Engine class that evaluates access policies against
security contexts.

The Authorization_Engine supports pre/post hooks for extensibility, custom
authorization rules, and provides methods for checking roles (OR logic)
and scopes (AND logic).
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []

from dataclasses import dataclass
from typing import Any, Callable, List, Optional, Tuple

from automojo.webworks.security.accesspolicy import AccessPolicy
from automojo.webworks.security.securitycontext import Security_Context


@dataclass
class AuthorizationResult:
    """
        Result of an authorization decision.

        Contains the allow/deny decision along with an optional reason
        for the decision, the policy that was evaluated, and the security
        context that was checked.

        :param allowed: Whether access is allowed.
        :param reason: Human-readable reason for the decision.
        :param policy: The AccessPolicy that was evaluated.
        :param context: The Security_Context that was checked.
    """

    allowed: bool
    reason: Optional[str] = None
    policy: Optional[AccessPolicy] = None
    context: Optional[Security_Context] = None


class AuthorizationRule:
    """
        Protocol for custom authorization rules.

        Custom rules can be registered with the Authorization_Engine to
        provide additional authorization logic beyond the standard role
        and scope checks. When a rule returns an AuthorizationResult,
        that result is used immediately. When a rule returns None, the
        engine continues to the next rule or falls through to standard
        checks.
    """

    def evaluate(
        self,
        policy: AccessPolicy,
        context: Security_Context,
        request: Any
    ) -> Optional[AuthorizationResult]:
        """
            Evaluate this custom rule against the given policy and context.

            :param policy: The access policy to evaluate.
            :param context: The security context to check.
            :param request: The incoming request object.

            :returns: An AuthorizationResult if this rule applies, or None
                to continue evaluation with the next rule.
        """
        ...


class Authorization_Engine:
    """
        Evaluates access policies against security contexts to make
        authorization decisions.

        The engine supports a default policy, custom authorization rules,
        and pre/post hooks for extensibility. The evaluate() method runs
        through the following steps:

        1. Run pre-hooks
        2. Check custom rules (if any return a result, use it)
        3. Check require_auth
        4. Check roles (OR logic)
        5. Check scopes (AND logic)
        6. Run post-hooks
        7. Return AuthorizationResult

        :param default_policy: The default policy to use when none is provided.
        :param custom_rules: A list of custom AuthorizationRule instances.
    """

    def __init__(
        self,
        default_policy: Optional[AccessPolicy] = None,
        custom_rules: Optional[List[AuthorizationRule]] = None
    ):
        self._default_policy = default_policy if default_policy is not None else AccessPolicy()
        self._custom_rules = custom_rules if custom_rules is not None else []
        self._pre_hooks: List[Callable] = []
        self._post_hooks: List[Callable] = []
        return

    def evaluate(
        self,
        policy: AccessPolicy,
        context: Security_Context
    ) -> AuthorizationResult:
        """
            Evaluate a policy against a security context.

            Runs through pre-hooks, custom rules, standard checks
            (authentication, roles, scopes), and post-hooks to produce
            an authorization decision.

            :param policy: The access policy to evaluate.
            :param context: The security context to check.

            :returns: An AuthorizationResult with the decision and reason.
        """
        # Step 1: Run pre-hooks
        for hook in self._pre_hooks:
            hook(policy, context)

        # Step 2: Check custom rules first
        for rule in self._custom_rules:
            rule_result = rule.evaluate(policy, context, None)
            if rule_result is not None:
                # Run post-hooks before returning
                for hook in self._post_hooks:
                    hook(policy, context, rule_result)
                return rule_result

        # Step 3: Check require_auth
        if policy.require_auth is True:
            is_auth = context.is_authenticated
            if is_auth is not True:
                result = AuthorizationResult(
                    allowed=False,
                    reason="Authentication is required",
                    policy=policy,
                    context=context
                )
                # Run post-hooks before returning
                for hook in self._post_hooks:
                    hook(policy, context, result)
                return result

        # Step 4: Check roles (OR logic)
        policy_roles = policy.roles
        if len(policy_roles) > 0:
            has_role = self.check_roles(policy_roles, context)
            if has_role is not True:
                result = AuthorizationResult(
                    allowed=False,
                    reason="Missing required role",
                    policy=policy,
                    context=context
                )
                # Run post-hooks before returning
                for hook in self._post_hooks:
                    hook(policy, context, result)
                return result

        # Step 5: Check scopes (AND logic)
        policy_scopes = policy.scopes
        if len(policy_scopes) > 0:
            has_scopes = self.check_scopes(policy_scopes, context)
            if has_scopes is not True:
                result = AuthorizationResult(
                    allowed=False,
                    reason="Missing required scope",
                    policy=policy,
                    context=context
                )
                # Run post-hooks before returning
                for hook in self._post_hooks:
                    hook(policy, context, result)
                return result

        # All checks passed
        result = AuthorizationResult(
            allowed=True,
            reason=None,
            policy=policy,
            context=context
        )

        # Step 6: Run post-hooks
        for hook in self._post_hooks:
            hook(policy, context, result)

        # Step 7: Return result
        return result

    def check_roles(
        self,
        required_roles: Tuple[str, ...],
        context: Security_Context
    ) -> bool:
        """
            Check if the context has any of the required roles (OR logic).

            :param required_roles: Tuple of role names to check for.
            :param context: Security context to check.

            :returns: True if the context has at least one required role.
        """
        has_role = context.has_any_role(*required_roles)
        return has_role

    def check_scopes(
        self,
        required_scopes: Tuple[str, ...],
        context: Security_Context
    ) -> bool:
        """
            Check if the context has all required scopes (AND logic).

            :param required_scopes: Tuple of scope names to check for.
            :param context: Security context to check.

            :returns: True if the context has all required scopes.
        """
        has_all = context.has_all_scopes(*required_scopes)
        return has_all

    def add_pre_hook(self, hook: Callable) -> None:
        """
            Add a pre-authorization hook.

            Pre-hooks are called before authorization evaluation begins.
            They receive the policy and context as arguments.

            :param hook: A callable that accepts (policy, context).
        """
        self._pre_hooks.append(hook)
        return

    def add_post_hook(self, hook: Callable) -> None:
        """
            Add a post-authorization hook.

            Post-hooks are called after authorization evaluation completes.
            They receive the policy, context, and result as arguments.

            :param hook: A callable that accepts (policy, context, result).
        """
        self._post_hooks.append(hook)
        return

    def add_custom_rule(self, rule: AuthorizationRule) -> None:
        """
            Add a custom authorization rule.

            Custom rules are evaluated before the standard role and scope
            checks. If a custom rule returns an AuthorizationResult, that
            result is used immediately without further evaluation.

            :param rule: An AuthorizationRule instance to add.
        """
        self._custom_rules.append(rule)
        return
