"""
.. module:: accesspolicy
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Security constraint dataclass for endpoint access control.

.. moduleauthor:: Automation Mojo LLC

This module provides the AccessPolicy dataclass for defining security constraints
on endpoints. It supports role-based and permission-based access control, and
integrates with the authentication system via AuthenticationContext.
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []

from dataclasses import dataclass, field
from typing import List, Optional, Protocol, TYPE_CHECKING, Union, runtime_checkable

if TYPE_CHECKING:
    from automojo.webworks.authentication.core import AuthenticationContext


@runtime_checkable
class User(Protocol):
    """
        Protocol defining the minimal user interface for access policy checks.
        
        Any user object passed to AccessPolicy.check() must have these attributes.
    """
    
    @property
    def roles(self) -> List[str]:
        """The roles assigned to the user."""
        ...
    
    @property
    def scopes(self) -> List[str]:
        """The scopes granted to the user."""
        ...
    
    @property
    def is_authenticated(self) -> bool:
        """Whether the user is authenticated."""
        ...


@dataclass
class AccessPolicy:
    """
        Security constraint defining roles, scopes, and authentication
        requirements for an endpoint.
        
        This dataclass holds access control information that determines
        which users can access an endpoint based on their roles, scopes,
        and authentication status.
        
        :param roles: List of roles that grant access to the endpoint.
        :param scopes: List of scopes required to access the endpoint.
        :param require_auth: Whether authentication is required.
    """
    
    roles: List[str] = field(default_factory=list)
    scopes: List[str] = field(default_factory=list)
    require_auth: bool = True
    
    def merge_with(
        self,
        other: "AccessPolicy",
        replace_roles: bool = False,
        replace_scopes: bool = False
    ) -> "AccessPolicy":
        """
            Merge this policy with another, combining constraints.
            
            The merged policy enforces all constraints (logical AND).
            By default, roles and scopes are combined (union). When
            replace flags are set, the other policy's values replace
            this policy's values.
            
            :param other: Policy to merge with.
            :param replace_roles: If True, other.roles replaces self.roles.
            :param replace_scopes: If True, other.scopes replaces self.scopes.
            
            :returns: New AccessPolicy with combined constraints.
        """
        if replace_roles:
            merged_roles = list(other.roles)
        else:
            # Union of roles, preserving order (self first, then other)
            merged_roles = list(self.roles)
            for role in other.roles:
                if role not in merged_roles:
                    merged_roles.append(role)
        
        if replace_scopes:
            merged_scopes = list(other.scopes)
        else:
            # Union of scopes, preserving order (self first, then other)
            merged_scopes = list(self.scopes)
            for scope in other.scopes:
                if scope not in merged_scopes:
                    merged_scopes.append(scope)
        
        # require_auth is True if either policy requires it (logical OR)
        merged_require_auth = self.require_auth or other.require_auth
        
        return AccessPolicy(
            roles=merged_roles,
            scopes=merged_scopes,
            require_auth=merged_require_auth
        )
    
    def check(self, user: User) -> bool:
        """
            Check if a user satisfies this policy.
            
            The user must satisfy all constraints:
            - If require_auth is True, user must be authenticated
            - If roles are specified, user must have at least one matching role
            - If scopes are specified, user must have all required scopes
            
            :param user: User to check against policy.
            
            :returns: True if user satisfies all constraints.
        """
        # Check authentication requirement
        if self.require_auth and not user.is_authenticated:
            return False
        
        # Check roles (user must have at least one matching role)
        if self.roles:
            user_roles = set(user.roles)
            required_roles = set(self.roles)
            if not user_roles.intersection(required_roles):
                return False
        
        # Check scopes (user must have all required scopes)
        if self.scopes:
            user_scopes = set(user.scopes)
            required_scopes = set(self.scopes)
            if not required_scopes.issubset(user_scopes):
                return False
        
        return True
    
    def check_authentication_context(
        self,
        context: Optional["AuthenticationContext"]
    ) -> bool:
        """
            Check if an AuthenticationContext satisfies this policy.
            
            This method provides integration with the authentication system
            by accepting an AuthenticationContext and checking its Principal
            against the policy constraints.
            
            The context must satisfy all constraints:
            - If require_auth is True, context must not be None and not expired
            - If roles are specified, principal must have at least one matching role
            - If scopes are specified, principal must have all required scopes
              (scopes are checked against principal's permissions)
            
            :param context: AuthenticationContext to check against policy,
                           or None if not authenticated.
            
            :returns: True if context satisfies all constraints.
        """
        # Check authentication requirement
        if self.require_auth:
            if context is None:
                return False
            if context.is_expired:
                return False
        
        # If no context and auth not required, allow access
        if context is None:
            return True
        
        principal = context.principal
        
        # Check roles (principal must have at least one matching role)
        if self.roles:
            principal_roles = set(principal.roles)
            required_roles = set(self.roles)
            if not principal_roles.intersection(required_roles):
                return False
        
        # Check scopes (principal must have all required scopes)
        # Scopes are mapped to principal permissions
        if self.scopes:
            principal_permissions = set(principal.permissions)
            required_scopes = set(self.scopes)
            if not required_scopes.issubset(principal_permissions):
                return False
        
        return True
    
    def check_roles(
        self,
        context: Optional["AuthenticationContext"]
    ) -> bool:
        """
            Check if an AuthenticationContext has the required roles.
            
            This is a convenience method for role-based access control that
            only checks role constraints, ignoring scope requirements.
            
            :param context: AuthenticationContext to check, or None.
            
            :returns: True if context has at least one required role,
                     or if no roles are required.
        """
        if not self.roles:
            return True
        
        if context is None:
            return False
        
        if context.is_expired:
            return False
        
        principal_roles = set(context.principal.roles)
        required_roles = set(self.roles)
        
        return bool(principal_roles.intersection(required_roles))
    
    def check_permissions(
        self,
        context: Optional["AuthenticationContext"]
    ) -> bool:
        """
            Check if an AuthenticationContext has the required permissions.
            
            This is a convenience method for permission-based access control
            that only checks scope/permission constraints, ignoring role
            requirements.
            
            :param context: AuthenticationContext to check, or None.
            
            :returns: True if context has all required permissions,
                     or if no permissions are required.
        """
        if not self.scopes:
            return True
        
        if context is None:
            return False
        
        if context.is_expired:
            return False
        
        principal_permissions = set(context.principal.permissions)
        required_scopes = set(self.scopes)
        
        return required_scopes.issubset(principal_permissions)
