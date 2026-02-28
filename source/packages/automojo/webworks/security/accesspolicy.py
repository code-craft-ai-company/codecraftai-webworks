"""
.. module:: accesspolicy
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Immutable access policy defining roles, scopes, and authentication
        requirements for an endpoint.

.. moduleauthor:: Automation Mojo LLC

This module provides the AccessPolicy frozen dataclass that represents a security
constraint for an endpoint. An AccessPolicy specifies which roles, scopes, and
authentication requirements must be satisfied for access to be granted. Policies
are immutable after creation and can be merged together to form combined constraints.

The merge_with() method combines two policies following composition rules where
the merged result enforces all constraints via logical AND. The check() method
evaluates whether a Security_Context satisfies the policy, and get_denial_reason()
provides a human-readable explanation when access is denied.
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []

from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Tuple

from automojo.webworks.security.securitycontext import Security_Context


@dataclass(frozen=True)
class AccessPolicy:
    """
        Security constraint defining roles, scopes, and authentication
        requirements for an endpoint. Immutable after creation.

        :param roles: Tuple of role names required for access. When non-empty,
            the user must have at least one of these roles (OR logic).
        :param scopes: Tuple of scope names required for access. When non-empty,
            the user must have all of these scopes (AND logic).
        :param require_auth: Whether authentication is mandatory for this policy.
        :param constraints: Additional custom constraint types as a dictionary.
            Callers should treat this as read-only to preserve the immutability
            intent of the policy.
    """

    roles: Tuple[str, ...] = field(default_factory=tuple)
    scopes: Tuple[str, ...] = field(default_factory=tuple)
    require_auth: bool = True
    constraints: Dict[str, Any] = field(default_factory=dict)

    def merge_with(
        self,
        other: "AccessPolicy",
        replace_roles: bool = False,
        replace_scopes: bool = False
    ) -> "AccessPolicy":
        """
            Merge this policy with another, combining constraints.

            The merged policy enforces all constraints via logical AND. By default,
            roles and scopes are combined as a union (deduplicated). When replace
            flags are set, the other policy's values fully replace this policy's
            values for that field.

            :param other: Policy to merge with.
            :param replace_roles: If True, other.roles replaces self.roles
                instead of performing a union.
            :param replace_scopes: If True, other.scopes replaces self.scopes
                instead of performing a union.

            :returns: A new AccessPolicy with combined constraints.
        """
        if replace_roles is True:
            merged_roles = other.roles
        else:
            seen = set()
            combined = []
            for role in self.roles:
                if role not in seen:
                    seen.add(role)
                    combined.append(role)
            for role in other.roles:
                if role not in seen:
                    seen.add(role)
                    combined.append(role)
            merged_roles = tuple(combined)

        if replace_scopes is True:
            merged_scopes = other.scopes
        else:
            seen = set()
            combined = []
            for scope in self.scopes:
                if scope not in seen:
                    seen.add(scope)
                    combined.append(scope)
            for scope in other.scopes:
                if scope not in seen:
                    seen.add(scope)
                    combined.append(scope)
            merged_scopes = tuple(combined)

        merged_require_auth = self.require_auth or other.require_auth

        merged_constraints = dict(self.constraints)
        merged_constraints.update(other.constraints)

        rtnval = AccessPolicy(
            roles=merged_roles,
            scopes=merged_scopes,
            require_auth=merged_require_auth,
            constraints=merged_constraints
        )

        return rtnval

    def check(self, context: Security_Context) -> bool:
        """
            Check if a security context satisfies this policy.

            The check evaluates three conditions in order:
            1. If require_auth is True, the context must be authenticated.
            2. If roles is non-empty, the context must have at least one
               of the required roles (OR logic).
            3. If scopes is non-empty, the context must have all of the
               required scopes (AND logic).

            :param context: Security context to check against this policy.

            :returns: True if the context satisfies all constraints.
        """
        if self.require_auth is True:
            is_auth = context.is_authenticated
            if is_auth is not True:
                return False

        policy_roles = self.roles
        if len(policy_roles) > 0:
            has_required_role = context.has_any_role(*policy_roles)
            if has_required_role is not True:
                return False

        policy_scopes = self.scopes
        if len(policy_scopes) > 0:
            has_all_required_scopes = context.has_all_scopes(*policy_scopes)
            if has_all_required_scopes is not True:
                return False

        rtnval = True

        return rtnval

    def get_denial_reason(self, context: Security_Context) -> Optional[str]:
        """
            Get the reason why a context fails this policy.

            Evaluates the same conditions as check() and returns a
            human-readable string describing the first constraint that
            is not satisfied. Returns None if the context passes all checks.

            :param context: Security context that may fail the check.

            :returns: Human-readable denial reason, or None if check passes.
        """
        if self.require_auth is True:
            is_auth = context.is_authenticated
            if is_auth is not True:
                rtnval = "Authentication is required"
                return rtnval

        policy_roles = self.roles
        if len(policy_roles) > 0:
            has_required_role = context.has_any_role(*policy_roles)
            if has_required_role is not True:
                rtnval = "Missing required role"
                return rtnval

        policy_scopes = self.scopes
        if len(policy_scopes) > 0:
            has_all_required_scopes = context.has_all_scopes(*policy_scopes)
            if has_all_required_scopes is not True:
                rtnval = "Missing required scope"
                return rtnval

        rtnval = None

        return rtnval
