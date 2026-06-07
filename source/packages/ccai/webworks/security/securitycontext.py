"""
.. module:: securitycontext
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Immutable security context containing authenticated user information.

.. moduleauthor:: Code Craft AI LLC

This module provides the Security_Context frozen dataclass that represents
the authenticated user's identity, roles, scopes, and authentication metadata.
The context is immutable after creation to prevent tampering. A guest() classmethod
provides a convenient way to create an unauthenticated context with empty roles
and scopes.
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple


@dataclass(frozen=True)
class SecurityContext:
    """
        Immutable security context containing authenticated user information.

        This dataclass holds the identity, roles, scopes, and authentication
        metadata for a user. It is frozen to prevent modification after creation,
        ensuring that security context data cannot be tampered with during
        request processing.

        :param user_id: Unique identifier for the authenticated user, or None for guests.
        :param username: Display name of the authenticated user.
        :param email: Email address of the authenticated user.
        :param roles: Tuple of role names assigned to the user.
        :param scopes: Tuple of scope names granted to the user.
        :param provider: Name of the authentication provider that created this context.
        :param authenticated_at: Timestamp when authentication occurred.
        :param expires_at: Timestamp when this context expires.
        :param extra: Additional metadata as a dictionary. Callers should treat
            this as read-only to preserve the immutability intent of the context.
    """

    user_id: Optional[str] = None
    username: Optional[str] = None
    email: Optional[str] = None
    roles: Tuple[str, ...] = field(default_factory=tuple)
    scopes: Tuple[str, ...] = field(default_factory=tuple)
    provider: Optional[str] = None
    authenticated_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    extra: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_authenticated(self) -> bool:
        """
            Return True if this context represents an authenticated user.

            A context is considered authenticated when a user_id is present.

            :returns: True if user_id is not None.
        """
        is_auth = self.user_id is not None
        return is_auth

    @property
    def is_expired(self) -> bool:
        """
            Return True if this context has expired.

            A context without an expires_at value never expires.

            :returns: True if the current time is past expires_at.
        """
        if self.expires_at is None:
            return False

        now = datetime.now(timezone.utc)
        expired = now > self.expires_at
        return expired

    def has_role(self, role: str) -> bool:
        """
            Check if this context has a specific role.

            :param role: The role name to check for.

            :returns: True if the role is present in this context's roles.
        """
        found = role in self.roles
        return found

    def has_scope(self, scope: str) -> bool:
        """
            Check if this context has a specific scope.

            :param scope: The scope name to check for.

            :returns: True if the scope is present in this context's scopes.
        """
        found = scope in self.scopes
        return found

    def has_any_role(self, *roles: str) -> bool:
        """
            Check if this context has any of the specified roles.

            :param roles: Variable number of role names to check.

            :returns: True if at least one of the specified roles is present.
        """
        context_roles = self.roles
        found = any(role in context_roles for role in roles)
        return found

    def has_all_scopes(self, *scopes: str) -> bool:
        """
            Check if this context has all of the specified scopes.

            :param scopes: Variable number of scope names to check.

            :returns: True if all of the specified scopes are present.
        """
        context_scopes = self.scopes
        found = all(scope in context_scopes for scope in scopes)
        return found

    @classmethod
    def guest(cls) -> "SecurityContext":
        """
            Create a guest context with no authentication.

            The guest context has no user_id, no roles, no scopes, and
            is_authenticated will return False.

            :returns: A new SecurityContext representing an unauthenticated guest.
        """
        rtnval = cls()
        return rtnval
