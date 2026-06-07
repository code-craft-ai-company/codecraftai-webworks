"""
.. module:: basic
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: HTTP Basic Authentication implementation.

.. moduleauthor:: Code Craft AI LLC

This module provides the BasicAuthenticator class which implements HTTP Basic
Authentication as defined in RFC 7617. It extracts Base64-encoded credentials
from the Authorization header and validates them against an IdentityProvider.
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


import base64
import logging
from typing import Any, Optional, Protocol, runtime_checkable

from ccai.webworks.authentication.core import (
    AuthenticationContext,
    AuthenticationResult,
    AuthenticationStatus,
    Principal
)


# Module-level logger used by the Basic authenticator. Malformed
# Authorization headers and base64 decode failures are logged at
# warning level so an operator can distinguish "broken client" from
# "broken server" without a packet capture.
logger = logging.getLogger(__name__)


@runtime_checkable
class IdentityProvider(Protocol):
    """
        Protocol for identity validation backends.
        
        An IdentityProvider is responsible for validating username/password
        credentials and returning a Principal if the credentials are valid.
    """
    
    async def validate_credentials(
        self,
        username: str,
        password: str
    ) -> Optional[Principal]:
        """
            Validate username/password credentials.
            
            :param username: The username to validate.
            :param password: The password to validate.
            
            :returns: A Principal if credentials are valid, None otherwise.
        """
        ...
    
    async def get_principal(self, identifier: str) -> Optional[Principal]:
        """
            Retrieve a principal by identifier.
            
            :param identifier: The unique identifier of the principal.
            
            :returns: The Principal if found, None otherwise.
        """
        ...


class BasicAuthenticator:
    """
        HTTP Basic Authentication implementation.
        
        This authenticator implements HTTP Basic Authentication as defined
        in RFC 7617. It extracts Base64-encoded credentials from the
        Authorization header and validates them against the configured
        IdentityProvider.
        
        The authentication flow is:
        1. Check for Authorization header with "Basic" scheme
        2. Decode Base64 credentials to extract username:password
        3. Validate credentials against the IdentityProvider
        4. Return SUCCESS with context or FAILURE with error
        
        Example usage::
        
            identity_provider = MyIdentityProvider()
            authenticator = BasicAuthenticator(identity_provider, realm="MyApp")
            
            result = await authenticator.authenticate(request)
            if result.status == AuthenticationStatus.SUCCESS:
                principal = result.context.principal
        
        :param identity_provider: The provider for validating credentials.
        :param realm: The authentication realm for WWW-Authenticate header.
    """
    
    def __init__(
        self,
        identity_provider: IdentityProvider,
        realm: str = "Restricted"
    ):
        """
            Initialize the BasicAuthenticator.
            
            :param identity_provider: The provider for validating credentials.
            :param realm: The authentication realm for WWW-Authenticate header.
                         Defaults to "Restricted".
        """
        self._identity_provider = identity_provider
        self._realm = realm
    
    @property
    def scheme(self) -> str:
        """
            Return the authentication scheme identifier.
            
            :returns: The string "Basic".
        """
        return "Basic"
    
    @property
    def realm(self) -> str:
        """
            Return the authentication realm.
            
            :returns: The configured realm string.
        """
        return self._realm
    
    def can_handle(self, request: Any) -> bool:
        """
            Check if this authenticator can handle the given request.
            
            This method checks if the request contains an Authorization
            header that starts with "Basic " (case-insensitive).
            
            :param request: The HTTP request object to examine.
            
            :returns: True if the request has a Basic Authorization header,
                     False otherwise.
        """
        auth_header = self._get_authorization_header(request)
        if auth_header is None:
            return False
        return auth_header.lower().startswith("basic ")
    
    async def authenticate(self, request: Any) -> AuthenticationResult:
        """
            Attempt to authenticate the request using Basic authentication.
            
            This method:
            1. Extracts the Authorization header
            2. Decodes the Base64 credentials
            3. Validates the credentials against the IdentityProvider
            4. Returns the appropriate AuthenticationResult
            
            :param request: The HTTP request containing credentials.
            
            :returns: An AuthenticationResult with:
                     - SUCCESS and context if credentials are valid
                     - FAILURE with error if credentials are invalid
                     - CHALLENGE if no credentials provided
                     - FAILURE with bad_request if credentials are malformed
        """
        auth_header = self._get_authorization_header(request)
        
        # No Authorization header - issue challenge
        if auth_header is None or auth_header.strip() == "":
            return self._challenge_response()
        
        # Parse the Authorization header
        try:
            scheme, credentials = self._parse_authorization_header(auth_header)
        except ValueError as e:
            logger.warning("Basic auth: malformed Authorization header: %s", e)
            return self._bad_request(str(e))

        # Check if this is a Basic auth header
        if scheme.lower() != "basic":
            return AuthenticationResult(status=AuthenticationStatus.SKIP)

        # Decode the Base64 credentials
        try:
            username, password = self._decode_credentials(credentials)
        except ValueError as e:
            logger.warning("Basic auth: failed to decode credentials: %s", e)
            return self._bad_request(str(e))
        
        # Validate credentials against the identity provider
        principal = await self._identity_provider.validate_credentials(
            username, password
        )
        
        if principal is None:
            return AuthenticationResult(
                status=AuthenticationStatus.FAILURE,
                error_code="invalid_credentials",
                error_description="Invalid username or password"
            )
        
        # Success - return context with principal
        return AuthenticationResult(
            status=AuthenticationStatus.SUCCESS,
            context=AuthenticationContext(
                principal=principal,
                scheme=self.scheme
            )
        )
    
    def _get_authorization_header(self, request: Any) -> Optional[str]:
        """
            Extract the Authorization header from the request.
            
            This method handles different request object types by checking
            for common header access patterns.
            
            :param request: The HTTP request object.
            
            :returns: The Authorization header value or None if not present.
        """
        # Handle dict-like request objects (e.g., test mocks)
        if isinstance(request, dict):
            headers = request.get("headers", {})
            if isinstance(headers, dict):
                # Try case-insensitive lookup
                for key, value in headers.items():
                    if key.lower() == "authorization":
                        return value
            return None
        
        # Handle request objects with headers attribute
        if hasattr(request, "headers"):
            headers = request.headers
            if isinstance(headers, dict):
                for key, value in headers.items():
                    if key.lower() == "authorization":
                        return value
            elif hasattr(headers, "get"):
                # Try common header access methods
                return headers.get("Authorization") or headers.get("authorization")
        
        return None
    
    def _parse_authorization_header(self, auth_header: str) -> tuple:
        """
            Parse the Authorization header into scheme and credentials.
            
            :param auth_header: The Authorization header value.
            
            :returns: A tuple of (scheme, credentials).
            
            :raises ValueError: If the header format is invalid.
        """
        parts = auth_header.split(" ", 1)
        if len(parts) != 2:
            raise ValueError("Invalid Authorization header format")
        
        scheme = parts[0]
        credentials = parts[1].strip()
        
        if not credentials:
            raise ValueError("Missing credentials in Authorization header")
        
        return scheme, credentials
    
    def _decode_credentials(self, credentials: str) -> tuple:
        """
            Decode Base64 credentials into username and password.
            
            :param credentials: The Base64-encoded credentials string.
            
            :returns: A tuple of (username, password).
            
            :raises ValueError: If decoding fails or format is invalid.
        """
        try:
            decoded = base64.b64decode(credentials).decode("utf-8")
        except Exception as exc:
            # Re-raise as ValueError to preserve the existing API
            # contract; the caller logs and returns 400 Bad Request.
            raise ValueError("Invalid Base64 encoding") from exc
        
        if ":" not in decoded:
            raise ValueError("Malformed credentials: missing separator")
        
        # Split on first colon only (password may contain colons)
        username, password = decoded.split(":", 1)
        
        return username, password
    
    def _challenge_response(self) -> AuthenticationResult:
        """
            Create a challenge response for unauthenticated requests.
            
            :returns: An AuthenticationResult with CHALLENGE status and
                     WWW-Authenticate header value.
        """
        return AuthenticationResult(
            status=AuthenticationStatus.CHALLENGE,
            challenge=f'Basic realm="{self._realm}"'
        )
    
    def _bad_request(self, message: str) -> AuthenticationResult:
        """
            Create a bad request response for malformed credentials.
            
            :param message: The error message describing the problem.
            
            :returns: An AuthenticationResult with FAILURE status and
                     bad_request error code.
        """
        return AuthenticationResult(
            status=AuthenticationStatus.FAILURE,
            error_code="bad_request",
            error_description=message
        )


def encode_basic_credentials(username: str, password: str) -> str:
    """
        Encode username and password as Basic auth credentials.
        
        This utility function creates the Base64-encoded credentials
        string for use in an Authorization header.
        
        :param username: The username to encode.
        :param password: The password to encode.
        
        :returns: The Base64-encoded credentials string.
    """
    credentials = f"{username}:{password}"
    encoded = base64.b64encode(credentials.encode("utf-8")).decode("utf-8")
    return encoded


def create_basic_auth_header(username: str, password: str) -> str:
    """
        Create a complete Basic Authorization header value.
        
        This utility function creates the full Authorization header
        value including the "Basic " prefix.
        
        :param username: The username to encode.
        :param password: The password to encode.
        
        :returns: The complete Authorization header value.
    """
    encoded = encode_basic_credentials(username, password)
    return f"Basic {encoded}"

