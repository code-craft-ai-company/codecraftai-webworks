"""
.. module:: authenticator
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Authenticator protocol definition for the authentication framework.

.. moduleauthor:: Automation Mojo LLC

This module defines the Authenticator protocol that all authentication
implementations must follow. The protocol specifies the interface for
authentication mechanisms such as Basic, Bearer, OAuth2, etc.
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


from abc import abstractmethod
from typing import Any, Dict, Protocol, runtime_checkable

from automojo.webworks.authentication.core import AuthenticationResult


@runtime_checkable
class Authenticator(Protocol):
    """
        Protocol for authentication implementations.
        
        All authentication mechanisms (Basic, Bearer, OAuth2, etc.) must
        implement this protocol. The protocol defines the interface for
        extracting and validating credentials from HTTP requests.
        
        The authentication flow is:
        1. can_handle() is called to check if this authenticator applies
        2. If can_handle() returns True, authenticate() is called
        3. authenticate() returns an AuthenticationResult with the outcome
        
        Implementations should be stateless and thread-safe.
    """
    
    @property
    @abstractmethod
    def scheme(self) -> str:
        """
            Return the authentication scheme identifier.
            
            The scheme is a unique string that identifies this authentication
            mechanism (e.g., "Basic", "Bearer", "Digest", "APIKey").
            
            :returns: The scheme identifier string.
        """
        ...
    
    def can_handle(self, request: Any) -> bool:
        """
            Check if this authenticator can handle the given request.
            
            This method examines the request to determine if it contains
            credentials that this authenticator can process. For example,
            a Basic authenticator checks for an Authorization header
            starting with "Basic ".
            
            :param request: The HTTP request object to examine.
            
            :returns: True if this authenticator can handle the request,
                     False otherwise.
        """
        ...
    
    @abstractmethod
    async def authenticate(self, request: Any) -> AuthenticationResult:
        """
            Attempt to authenticate the request.
            
            This method extracts credentials from the request and validates
            them against the configured identity provider or token store.
            
            :param request: The HTTP request object containing credentials.
            
            :returns: An AuthenticationResult with:
                     - SUCCESS and context if authentication succeeded
                     - FAILURE with error details if authentication failed
                     - CHALLENGE with WWW-Authenticate value if challenge needed
                     - SKIP if this authenticator doesn't apply
        """
        ...

