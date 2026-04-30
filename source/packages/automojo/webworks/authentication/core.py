"""
.. module:: core
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Core authentication data structures and enumerations.

.. moduleauthor:: Automation Mojo LLC

This module contains the fundamental data structures used throughout the
authentication system including AuthenticationStatus, AuthenticationResult,
Principal, and AuthenticationContext.
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional, Set


class AuthenticationStatus(Enum):
    """
        Status of an authentication attempt.
        
        This enum represents the possible outcomes of an authentication
        attempt by an Authenticator.
        
        :cvar SUCCESS: Authentication succeeded, context is available.
        :cvar FAILURE: Authentication failed definitively.
        :cvar CHALLENGE: Requires client response (e.g., Digest auth).
        :cvar SKIP: Authenticator doesn't apply to this request.
    """
    
    SUCCESS = "success"
    FAILURE = "failure"
    CHALLENGE = "challenge"
    SKIP = "skip"


@dataclass
class Principal:
    """
        Represents an authenticated entity (user, service, or application).
        
        The Principal contains identity information about the authenticated
        entity including a unique identifier, optional display name, and
        collections of roles and permissions for authorization decisions.
        
        :param identifier: Unique identifier for the principal.
        :param display_name: Human-readable name for display purposes.
        :param roles: Set of roles assigned to the principal.
        :param permissions: Set of permissions granted to the principal.
        :param attributes: Additional scheme-specific attributes.
    """
    
    identifier: str
    display_name: Optional[str] = None
    roles: Set[str] = field(default_factory=set)
    permissions: Set[str] = field(default_factory=set)
    attributes: Dict[str, Any] = field(default_factory=dict)
    
    def has_role(self, role: str) -> bool:
        """
            Check if the principal has a specific role.
            
            :param role: The role to check for.
            
            :returns: True if the principal has the role, False otherwise.
        """
        return role in self.roles
    
    def has_permission(self, permission: str) -> bool:
        """
            Check if the principal has a specific permission.
            
            :param permission: The permission to check for.
            
            :returns: True if the principal has the permission, False otherwise.
        """
        return permission in self.permissions


@dataclass
class AuthenticationContext:
    """
        Context containing authentication information for a request.
        
        The AuthenticationContext is created upon successful authentication
        and contains the authenticated Principal, the scheme used, timestamps,
        and any additional scheme-specific attributes.
        
        :param principal: The authenticated entity.
        :param scheme: The authentication scheme identifier (e.g., "Basic", "Bearer").
        :param authenticated_at: Timestamp when authentication occurred.
        :param expires_at: Optional expiration timestamp for the authentication.
        :param attributes: Additional scheme-specific data (e.g., JWT claims).
    """
    
    principal: Principal
    scheme: str
    authenticated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None
    attributes: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def is_expired(self) -> bool:
        """
            Check if the authentication has expired.

            Naive ``expires_at`` values (no ``tzinfo``) are interpreted as
            UTC so that comparisons against the current time always operate
            on aware datetimes. This protects against a class of caller
            bugs where ``datetime.utcnow()`` is used to construct the
            context — without the coercion the comparison would raise
            ``TypeError: can't compare offset-naive and offset-aware
            datetimes``.

            :returns: True if expires_at is set and has passed, False otherwise.
        """
        if self.expires_at is None:
            return False

        expires_at = self.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        return datetime.now(timezone.utc) > expires_at


@dataclass
class AuthenticationResult:
    """
        Result of an authentication attempt.
        
        This dataclass encapsulates the outcome of an authentication attempt
        including the status, optional context on success, challenge information
        for challenge-response flows, and error details on failure.
        
        :param status: The authentication status.
        :param context: The authentication context (on SUCCESS).
        :param challenge: WWW-Authenticate header value (on CHALLENGE).
        :param error_code: Error code identifier (on FAILURE).
        :param error_description: Human-readable error description (on FAILURE).
    """
    
    status: AuthenticationStatus
    context: Optional[AuthenticationContext] = None
    challenge: Optional[str] = None
    error_code: Optional[str] = None
    error_description: Optional[str] = None


# =============================================================================
# Protocol Compliance Verification
# =============================================================================

def verify_authentication_context_compliance(context: AuthenticationContext) -> bool:
    """
        Verify that an AuthenticationContext instance is compliant with the
        expected interface for cross-scheme consistency.
        
        This function checks that the context has all required attributes
        with compatible types, ensuring that code consuming AuthenticationContext
        objects can work uniformly regardless of which authentication scheme
        produced the context.
        
        :param context: The AuthenticationContext to verify.
        
        :returns: True if the context is compliant, False otherwise.
        
        :raises TypeError: If the context is not an AuthenticationContext instance.
        :raises ValueError: If the context has invalid attribute types.
    """
    if not isinstance(context, AuthenticationContext):
        raise TypeError(
            f"Expected AuthenticationContext, got {type(context).__name__}"
        )
    
    # Verify principal is present and valid
    if context.principal is None:
        raise ValueError("AuthenticationContext.principal must not be None")
    
    if not isinstance(context.principal, Principal):
        raise ValueError(
            f"AuthenticationContext.principal must be a Principal, "
            f"got {type(context.principal).__name__}"
        )
    
    # Verify principal has valid identifier
    if not isinstance(context.principal.identifier, str):
        raise ValueError(
            f"Principal.identifier must be a string, "
            f"got {type(context.principal.identifier).__name__}"
        )
    
    if len(context.principal.identifier) == 0:
        raise ValueError("Principal.identifier must not be empty")
    
    # Verify scheme is a non-empty string
    if not isinstance(context.scheme, str):
        raise ValueError(
            f"AuthenticationContext.scheme must be a string, "
            f"got {type(context.scheme).__name__}"
        )
    
    if len(context.scheme) == 0:
        raise ValueError("AuthenticationContext.scheme must not be empty")
    
    # Verify authenticated_at is a datetime
    if not isinstance(context.authenticated_at, datetime):
        raise ValueError(
            f"AuthenticationContext.authenticated_at must be a datetime, "
            f"got {type(context.authenticated_at).__name__}"
        )
    
    # Verify expires_at is None or datetime
    if context.expires_at is not None and not isinstance(context.expires_at, datetime):
        raise ValueError(
            f"AuthenticationContext.expires_at must be None or datetime, "
            f"got {type(context.expires_at).__name__}"
        )
    
    # Verify attributes is a dict
    if not isinstance(context.attributes, dict):
        raise ValueError(
            f"AuthenticationContext.attributes must be a dict, "
            f"got {type(context.attributes).__name__}"
        )
    
    # Verify principal roles and permissions are iterable
    try:
        list(context.principal.roles)
    except TypeError:
        raise ValueError("Principal.roles must be iterable")
    
    try:
        list(context.principal.permissions)
    except TypeError:
        raise ValueError("Principal.permissions must be iterable")
    
    return True


def verify_principal_compliance(principal: Principal) -> bool:
    """
        Verify that a Principal instance is compliant with the expected interface.
        
        This function checks that the principal has all required attributes
        with compatible types.
        
        :param principal: The Principal to verify.
        
        :returns: True if the principal is compliant, False otherwise.
        
        :raises TypeError: If the principal is not a Principal instance.
        :raises ValueError: If the principal has invalid attribute types.
    """
    if not isinstance(principal, Principal):
        raise TypeError(
            f"Expected Principal, got {type(principal).__name__}"
        )
    
    # Verify identifier is a non-empty string
    if not isinstance(principal.identifier, str):
        raise ValueError(
            f"Principal.identifier must be a string, "
            f"got {type(principal.identifier).__name__}"
        )
    
    if len(principal.identifier) == 0:
        raise ValueError("Principal.identifier must not be empty")
    
    # Verify display_name is None or string
    if principal.display_name is not None and not isinstance(principal.display_name, str):
        raise ValueError(
            f"Principal.display_name must be None or string, "
            f"got {type(principal.display_name).__name__}"
        )
    
    # Verify roles is iterable
    try:
        list(principal.roles)
    except TypeError:
        raise ValueError("Principal.roles must be iterable")
    
    # Verify permissions is iterable
    try:
        list(principal.permissions)
    except TypeError:
        raise ValueError("Principal.permissions must be iterable")
    
    # Verify attributes is a dict
    if not isinstance(principal.attributes, dict):
        raise ValueError(
            f"Principal.attributes must be a dict, "
            f"got {type(principal.attributes).__name__}"
        )
    
    # Verify has_role and has_permission methods exist and are callable
    if not callable(getattr(principal, 'has_role', None)):
        raise ValueError("Principal must have callable has_role method")
    
    if not callable(getattr(principal, 'has_permission', None)):
        raise ValueError("Principal must have callable has_permission method")
    
    return True
