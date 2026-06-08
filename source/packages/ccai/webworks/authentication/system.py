"""
.. module:: system
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Central authentication system coordinator.

.. moduleauthor:: Code Craft AI LLC

This module provides the AuthenticationSystem class which serves as the
central coordinator for authentication in the webworks framework. It
manages a registry of Authenticator implementations and orchestrates
the authentication process.
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


from typing import Any, Dict, List, Optional, Tuple

from ccai.webworks.authentication.authenticator import Authenticator
from ccai.webworks.authentication.core import (
    AuthenticationResult,
    AuthenticationStatus
)


class AuthenticationSystem:
    """
        Central authentication coordinator.
        
        The AuthenticationSystem manages a registry of Authenticator
        implementations and coordinates the authentication process.
        Authenticators are registered with a scheme identifier and
        optional priority, and are invoked in priority order during
        authentication.
        
        The authentication process iterates through registered authenticators
        until one succeeds or returns a definitive failure. If all
        authenticators skip or fail, an appropriate failure response is
        returned.
        
        Example usage::
        
            auth_system = AuthenticationSystem()
            auth_system.register(BasicAuthenticator(identity_provider), priority=10)
            auth_system.register(BearerAuthenticator(token_store), priority=20)
            
            result = await auth_system.authenticate(request)
            if result.status == AuthenticationStatus.SUCCESS:
                context = result.context
    """
    
    def __init__(self):
        """
            Initialize the AuthenticationSystem.
            
            Creates an empty registry for authenticators.
        """
        # Maps scheme -> (authenticator, priority)
        self._authenticators: Dict[str, Tuple[Authenticator, int]] = {}
        # Cached list of schemes in priority order (highest first)
        self._scheme_order: List[str] = []
    
    def register(self, authenticator: Authenticator, priority: int = 0) -> None:
        """
            Register an authenticator with optional priority.
            
            The authenticator is associated with its scheme identifier.
            If an authenticator with the same scheme is already registered,
            it will be replaced.
            
            Higher priority values are checked first during authentication.
            
            :param authenticator: The authenticator to register.
            :param priority: Priority value (higher = checked first). Default is 0.
        """
        scheme = authenticator.scheme
        self._authenticators[scheme] = (authenticator, priority)
        self._update_order()
    
    def unregister(self, scheme: str) -> bool:
        """
            Unregister an authenticator by scheme.
            
            :param scheme: The scheme identifier of the authenticator to remove.
            
            :returns: True if an authenticator was removed, False if not found.
        """
        if scheme in self._authenticators:
            del self._authenticators[scheme]
            self._update_order()
            return True
        return False
    
    def get_authenticator(self, scheme: str) -> Optional[Authenticator]:
        """
            Get a registered authenticator by scheme.
            
            :param scheme: The scheme identifier to look up.
            
            :returns: The authenticator if found, None otherwise.
        """
        entry = self._authenticators.get(scheme)
        if entry is not None:
            return entry[0]
        return None
    
    def get_registered_schemes(self) -> List[str]:
        """
            Get a list of all registered scheme identifiers.
            
            :returns: List of scheme identifiers in priority order.
        """
        return list(self._scheme_order)
    
    def get_authenticator_count(self) -> int:
        """
            Get the number of registered authenticators.
            
            :returns: The count of registered authenticators.
        """
        return len(self._authenticators)

    
    async def authenticate(self, request: Any) -> AuthenticationResult:
        """
            Attempt authentication using registered authenticators.
            
            Iterates through authenticators in priority order (highest first)
            until one succeeds or returns a definitive failure. Authenticators
            that return SKIP are bypassed.
            
            The iteration terminates when:
            - An authenticator returns SUCCESS (authentication succeeded)
            - An authenticator returns FAILURE (definitive failure)
            - All authenticators have been tried
            
            If multiple authenticators return CHALLENGE, their challenges
            are combined in the response.
            
            :param request: The HTTP request to authenticate.
            
            :returns: An AuthenticationResult with:
                     - SUCCESS and context if any authenticator succeeded
                     - FAILURE if an authenticator definitively failed
                     - CHALLENGE if challenges were issued but no success
                     - FAILURE with no_credentials if no authenticator applied
        """
        challenges: List[str] = []
        
        for scheme in self._scheme_order:
            authenticator, _ = self._authenticators[scheme]
            
            # Check if this authenticator can handle the request
            if not authenticator.can_handle(request):
                continue
            
            # Attempt authentication
            result = await authenticator.authenticate(request)
            
            if result.status == AuthenticationStatus.SUCCESS:
                # Authentication succeeded, return immediately
                return result
            elif result.status == AuthenticationStatus.CHALLENGE:
                # Collect challenge for later
                if result.challenge:
                    challenges.append(result.challenge)
            elif result.status == AuthenticationStatus.FAILURE:
                # Definitive failure, stop trying
                return result
            # SKIP status: continue to next authenticator
        
        # No authenticator succeeded
        if challenges:
            # Return combined challenges
            return AuthenticationResult(
                status=AuthenticationStatus.CHALLENGE,
                challenge=", ".join(challenges)
            )
        
        # No authenticator could handle the request
        return AuthenticationResult(
            status=AuthenticationStatus.FAILURE,
            error_code="no_credentials",
            error_description="No valid credentials provided"
        )
    
    def _update_order(self) -> None:
        """
            Update the scheme order list based on priorities.
            
            Schemes are sorted by priority in descending order (highest first).
            Schemes with equal priority are sorted alphabetically for
            deterministic ordering.
        """
        # Sort by priority (descending), then by scheme name (ascending) for stability
        sorted_items = sorted(
            self._authenticators.items(),
            key=lambda item: (-item[1][1], item[0])  # (-priority, scheme)
        )
        self._scheme_order = [scheme for scheme, _ in sorted_items]

