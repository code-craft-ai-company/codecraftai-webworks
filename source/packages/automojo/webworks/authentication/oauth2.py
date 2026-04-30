"""
.. module:: oauth2
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: OAuth 2.0 Authentication implementation.

.. moduleauthor:: Automation Mojo LLC

This module provides the OAuth2Authenticator class which implements OAuth 2.0
authentication flows as defined in RFC 6749. It supports Authorization Code,
Client Credentials, and Resource Owner Password Credentials flows, along with
PKCE (RFC 7636) for public clients.
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


import base64
import hashlib
import json
import secrets
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, Optional, Protocol, Set, runtime_checkable
from urllib.parse import parse_qs, urlencode, urlparse

from automojo.webworks.authentication.core import (
    AuthenticationContext,
    AuthenticationResult,
    AuthenticationStatus,
    Principal
)


class OAuth2GrantType(Enum):
    """
        OAuth 2.0 grant types supported by the authenticator.
        
        :cvar AUTHORIZATION_CODE: Authorization Code flow (RFC 6749 Section 4.1)
        :cvar CLIENT_CREDENTIALS: Client Credentials flow (RFC 6749 Section 4.4)
        :cvar PASSWORD: Resource Owner Password Credentials flow (RFC 6749 Section 4.3)
        :cvar REFRESH_TOKEN: Token refresh (RFC 6749 Section 6)
    """
    
    AUTHORIZATION_CODE = "authorization_code"
    CLIENT_CREDENTIALS = "client_credentials"
    PASSWORD = "password"
    REFRESH_TOKEN = "refresh_token"


class PKCEMethod(Enum):
    """
        PKCE code challenge methods as defined in RFC 7636.
        
        :cvar PLAIN: Plain text code challenge (not recommended)
        :cvar S256: SHA-256 hashed code challenge (recommended)
    """
    
    PLAIN = "plain"
    S256 = "S256"


@dataclass
class OAuth2Token:
    """
        OAuth 2.0 token representation.
        
        This dataclass represents the tokens returned from an OAuth 2.0
        token endpoint response.
        
        :param access_token: The access token string.
        :param token_type: The token type (typically "Bearer").
        :param expires_in: Optional time in seconds until token expires.
        :param refresh_token: Optional refresh token for obtaining new access tokens.
        :param scope: Optional set of granted scopes.
    """
    
    access_token: str
    token_type: str = "Bearer"
    expires_in: Optional[int] = None
    refresh_token: Optional[str] = None
    scope: Optional[Set[str]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """
            Convert the token to a dictionary for JSON serialization.
            
            :returns: Dictionary representation of the token.
        """
        result: Dict[str, Any] = {
            "access_token": self.access_token,
            "token_type": self.token_type
        }
        if self.expires_in is not None:
            result["expires_in"] = self.expires_in
        if self.refresh_token is not None:
            result["refresh_token"] = self.refresh_token
        if self.scope is not None:
            result["scope"] = " ".join(self.scope)
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OAuth2Token":
        """
            Create an OAuth2Token from a dictionary.
            
            :param data: Dictionary containing token data.
            
            :returns: An OAuth2Token instance.
        """
        scope = None
        if "scope" in data:
            scope_str = data["scope"]
            if isinstance(scope_str, str):
                scope = set(scope_str.split()) if scope_str else set()
            elif isinstance(scope_str, (list, set)):
                scope = set(scope_str)
        
        return cls(
            access_token=data["access_token"],
            token_type=data.get("token_type", "Bearer"),
            expires_in=data.get("expires_in"),
            refresh_token=data.get("refresh_token"),
            scope=scope
        )


@dataclass
class OAuth2AuthorizationCode:
    """
        OAuth 2.0 authorization code representation.
        
        This dataclass represents an authorization code issued during the
        Authorization Code flow, including PKCE parameters if used.
        
        :param code: The authorization code string.
        :param client_id: The client identifier that requested the code.
        :param redirect_uri: The redirect URI used in the authorization request.
        :param scope: Set of requested scopes.
        :param state: Optional state parameter for CSRF protection.
        :param code_challenge: Optional PKCE code challenge.
        :param code_challenge_method: Optional PKCE code challenge method.
        :param created_at: Timestamp when the code was created.
        :param expires_at: Optional expiration timestamp.
        :param user_id: Optional identifier of the authenticated user.
    """
    
    code: str
    client_id: str
    redirect_uri: str
    scope: Set[str] = field(default_factory=set)
    state: Optional[str] = None
    code_challenge: Optional[str] = None
    code_challenge_method: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None
    user_id: Optional[str] = None
    
    @property
    def is_expired(self) -> bool:
        """
            Check if the authorization code has expired.

            Naive ``expires_at`` values (no ``tzinfo``) are interpreted as UTC
            so the comparison against the current time always operates on aware
            datetimes; otherwise callers passing ``datetime.utcnow()`` would
            trigger ``TypeError: can't compare offset-naive and offset-aware
            datetimes``.

            :returns: True if expired, False otherwise.
        """
        if self.expires_at is None:
            return False

        expires_at = self.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        return datetime.now(timezone.utc) > expires_at


@dataclass
class OAuth2Error:
    """
        OAuth 2.0 error response as defined in RFC 6749 Section 5.2.
        
        :param error: Error code (e.g., "invalid_request", "invalid_client").
        :param error_description: Optional human-readable error description.
        :param error_uri: Optional URI for more information about the error.
    """
    
    error: str
    error_description: Optional[str] = None
    error_uri: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """
            Convert the error to a dictionary for JSON serialization.
            
            :returns: Dictionary representation of the error.
        """
        result: Dict[str, Any] = {"error": self.error}
        if self.error_description is not None:
            result["error_description"] = self.error_description
        if self.error_uri is not None:
            result["error_uri"] = self.error_uri
        return result



@runtime_checkable
class OAuth2ClientStore(Protocol):
    """
        Protocol for OAuth 2.0 client storage and validation.
        
        Implementations of this protocol are responsible for storing and
        validating OAuth 2.0 client credentials.
    """
    
    async def validate_client(
        self,
        client_id: str,
        client_secret: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
            Validate client credentials and return client info if valid.
            
            :param client_id: The client identifier.
            :param client_secret: Optional client secret for confidential clients.
            
            :returns: Client information dictionary if valid, None otherwise.
        """
        ...
    
    async def get_client(self, client_id: str) -> Optional[Dict[str, Any]]:
        """
            Get client information by client ID.
            
            :param client_id: The client identifier.
            
            :returns: Client information dictionary if found, None otherwise.
        """
        ...


@runtime_checkable
class OAuth2AuthorizationCodeStore(Protocol):
    """
        Protocol for OAuth 2.0 authorization code storage.
        
        Implementations of this protocol are responsible for storing and
        retrieving authorization codes during the Authorization Code flow.
    """
    
    async def store_code(self, auth_code: OAuth2AuthorizationCode) -> None:
        """
            Store an authorization code.
            
            :param auth_code: The authorization code to store.
        """
        ...
    
    async def get_code(self, code: str) -> Optional[OAuth2AuthorizationCode]:
        """
            Retrieve an authorization code.
            
            :param code: The authorization code string.
            
            :returns: The OAuth2AuthorizationCode if found, None otherwise.
        """
        ...
    
    async def delete_code(self, code: str) -> bool:
        """
            Delete an authorization code (after use).
            
            :param code: The authorization code string.
            
            :returns: True if deleted, False if not found.
        """
        ...


@runtime_checkable
class OAuth2TokenStore(Protocol):
    """
        Protocol for OAuth 2.0 token storage.
        
        Implementations of this protocol are responsible for storing and
        validating OAuth 2.0 access and refresh tokens.
    """
    
    async def store_token(
        self,
        token: OAuth2Token,
        client_id: str,
        user_id: Optional[str] = None
    ) -> None:
        """
            Store an OAuth 2.0 token.
            
            :param token: The token to store.
            :param client_id: The client that owns the token.
            :param user_id: Optional user identifier for user-bound tokens.
        """
        ...
    
    async def validate_access_token(
        self,
        access_token: str
    ) -> Optional[Dict[str, Any]]:
        """
            Validate an access token and return associated data.
            
            :param access_token: The access token string.
            
            :returns: Token data dictionary if valid, None otherwise.
        """
        ...
    
    async def validate_refresh_token(
        self,
        refresh_token: str
    ) -> Optional[Dict[str, Any]]:
        """
            Validate a refresh token and return associated data.
            
            :param refresh_token: The refresh token string.
            
            :returns: Token data dictionary if valid, None otherwise.
        """
        ...
    
    async def revoke_token(self, token: str) -> bool:
        """
            Revoke a token (access or refresh).
            
            :param token: The token string to revoke.
            
            :returns: True if revoked, False if not found.
        """
        ...


@runtime_checkable
class OAuth2UserAuthenticator(Protocol):
    """
        Protocol for authenticating users in the Password Credentials flow.
        
        Implementations of this protocol are responsible for validating
        user credentials in the Resource Owner Password Credentials flow.
    """
    
    async def authenticate_user(
        self,
        username: str,
        password: str
    ) -> Optional[Dict[str, Any]]:
        """
            Authenticate a user with username and password.
            
            :param username: The username.
            :param password: The password.
            
            :returns: User information dictionary if valid, None otherwise.
        """
        ...


# =============================================================================
# PKCE Utility Functions
# =============================================================================

def generate_code_verifier(length: int = 64) -> str:
    """
        Generate a PKCE code verifier.
        
        The code verifier is a cryptographically random string using the
        characters [A-Z] / [a-z] / [0-9] / "-" / "." / "_" / "~" with a
        minimum length of 43 and maximum of 128 characters.
        
        :param length: Length of the code verifier (43-128). Default is 64.
        
        :returns: The code verifier string.
        
        :raises ValueError: If length is not between 43 and 128.
    """
    if length < 43 or length > 128:
        raise ValueError("Code verifier length must be between 43 and 128")
    
    # Use URL-safe base64 characters without padding
    return secrets.token_urlsafe(length)[:length]


def generate_code_challenge(
    code_verifier: str,
    method: PKCEMethod = PKCEMethod.S256
) -> str:
    """
        Generate a PKCE code challenge from a code verifier.
        
        :param code_verifier: The code verifier string.
        :param method: The challenge method (PLAIN or S256).
        
        :returns: The code challenge string.
    """
    if method == PKCEMethod.PLAIN:
        return code_verifier
    
    # S256: BASE64URL(SHA256(code_verifier))
    digest = hashlib.sha256(code_verifier.encode('ascii')).digest()
    # Base64URL encode without padding
    challenge = base64.urlsafe_b64encode(digest).decode('ascii').rstrip('=')
    return challenge


def verify_code_challenge(
    code_verifier: str,
    code_challenge: str,
    method: str
) -> bool:
    """
        Verify a PKCE code challenge against a code verifier.
        
        :param code_verifier: The code verifier from the token request.
        :param code_challenge: The code challenge from the authorization request.
        :param method: The challenge method ("plain" or "S256").
        
        :returns: True if the code verifier matches the challenge, False otherwise.
    """
    if method.lower() == "plain":
        return code_verifier == code_challenge
    
    if method.upper() == "S256":
        expected_challenge = generate_code_challenge(
            code_verifier,
            PKCEMethod.S256
        )
        return secrets.compare_digest(expected_challenge, code_challenge)
    
    return False


# =============================================================================
# State Parameter Utility Functions
# =============================================================================

def generate_state(length: int = 32) -> str:
    """
        Generate a cryptographically secure state parameter.
        
        The state parameter is used to prevent CSRF attacks in the
        Authorization Code flow.
        
        :param length: Length of the state string. Default is 32.
        
        :returns: The state string.
    """
    return secrets.token_urlsafe(length)[:length]


def validate_state(expected_state: str, received_state: Optional[str]) -> bool:
    """
        Validate a state parameter using constant-time comparison.
        
        :param expected_state: The expected state value.
        :param received_state: The received state value from the callback.
        
        :returns: True if states match, False otherwise.
    """
    if received_state is None:
        return False
    return secrets.compare_digest(expected_state, received_state)



# =============================================================================
# OAuth2 Authenticator
# =============================================================================

class OAuth2Authenticator:
    """
        OAuth 2.0 Authentication implementation.
        
        This authenticator implements OAuth 2.0 authentication flows as defined
        in RFC 6749. It supports:
        
        - Authorization Code flow (Section 4.1)
        - Client Credentials flow (Section 4.4)
        - Resource Owner Password Credentials flow (Section 4.3)
        - Token refresh (Section 6)
        - PKCE extension (RFC 7636)
        
        The authenticator can be used to:
        1. Validate access tokens in incoming requests
        2. Generate authorization URLs for the Authorization Code flow
        3. Exchange authorization codes for tokens
        4. Obtain tokens via Client Credentials or Password flows
        5. Refresh tokens using refresh tokens
        
        Example usage::
        
            # Create authenticator with stores
            authenticator = OAuth2Authenticator(
                client_store=my_client_store,
                token_store=my_token_store,
                authorization_endpoint="/oauth/authorize",
                token_endpoint="/oauth/token"
            )
            
            # Validate access token in request
            result = await authenticator.authenticate(request)
            
            # Generate authorization URL
            auth_url = authenticator.create_authorization_url(
                client_id="my-client",
                redirect_uri="https://example.com/callback",
                scope={"read", "write"},
                state="random-state"
            )
        
        :param client_store: Store for validating OAuth 2.0 clients.
        :param token_store: Store for validating and storing tokens.
        :param code_store: Optional store for authorization codes.
        :param user_authenticator: Optional authenticator for Password flow.
        :param authorization_endpoint: URL path for authorization endpoint.
        :param token_endpoint: URL path for token endpoint.
        :param supported_grant_types: Set of supported grant types.
        :param default_token_lifetime: Default access token lifetime in seconds.
        :param refresh_token_lifetime: Refresh token lifetime in seconds.
        :param require_pkce: Whether to require PKCE for Authorization Code flow.
    """
    
    def __init__(
        self,
        client_store: OAuth2ClientStore,
        token_store: OAuth2TokenStore,
        code_store: Optional[OAuth2AuthorizationCodeStore] = None,
        user_authenticator: Optional[OAuth2UserAuthenticator] = None,
        authorization_endpoint: str = "/oauth/authorize",
        token_endpoint: str = "/oauth/token",
        supported_grant_types: Optional[Set[OAuth2GrantType]] = None,
        default_token_lifetime: int = 3600,
        refresh_token_lifetime: int = 86400,
        require_pkce: bool = False
    ):
        """
            Initialize the OAuth2Authenticator.
            
            :param client_store: Store for validating OAuth 2.0 clients.
            :param token_store: Store for validating and storing tokens.
            :param code_store: Optional store for authorization codes.
            :param user_authenticator: Optional authenticator for Password flow.
            :param authorization_endpoint: URL path for authorization endpoint.
            :param token_endpoint: URL path for token endpoint.
            :param supported_grant_types: Set of supported grant types.
            :param default_token_lifetime: Default access token lifetime in seconds.
            :param refresh_token_lifetime: Refresh token lifetime in seconds.
            :param require_pkce: Whether to require PKCE for Authorization Code flow.
        """
        self._client_store = client_store
        self._token_store = token_store
        self._code_store = code_store
        self._user_authenticator = user_authenticator
        self._authorization_endpoint = authorization_endpoint
        self._token_endpoint = token_endpoint
        self._default_token_lifetime = default_token_lifetime
        self._refresh_token_lifetime = refresh_token_lifetime
        self._require_pkce = require_pkce
        
        # Default supported grant types
        if supported_grant_types is None:
            self._supported_grant_types = {
                OAuth2GrantType.AUTHORIZATION_CODE,
                OAuth2GrantType.CLIENT_CREDENTIALS,
                OAuth2GrantType.REFRESH_TOKEN
            }
        else:
            self._supported_grant_types = supported_grant_types
    
    @property
    def scheme(self) -> str:
        """
            Return the authentication scheme identifier.
            
            :returns: The string "OAuth2".
        """
        return "OAuth2"
    
    @property
    def authorization_endpoint(self) -> str:
        """
            Return the authorization endpoint URL path.
            
            :returns: The authorization endpoint path.
        """
        return self._authorization_endpoint
    
    @property
    def token_endpoint(self) -> str:
        """
            Return the token endpoint URL path.
            
            :returns: The token endpoint path.
        """
        return self._token_endpoint
    
    def can_handle(self, request: Any) -> bool:
        """
            Check if this authenticator can handle the given request.
            
            This method checks if the request contains a Bearer token
            in the Authorization header.
            
            :param request: The HTTP request object to examine.
            
            :returns: True if the request has a Bearer Authorization header,
                     False otherwise.
        """
        auth_header = self._get_authorization_header(request)
        if auth_header is None:
            return False
        return auth_header.lower().startswith("bearer ")
    
    async def authenticate(self, request: Any) -> AuthenticationResult:
        """
            Authenticate a request using the Bearer access token.
            
            This method extracts the access token from the Authorization
            header and validates it against the token store.
            
            :param request: The HTTP request containing the token.
            
            :returns: An AuthenticationResult with:
                     - SUCCESS and context if token is valid
                     - FAILURE with error if token is invalid
                     - SKIP if no Bearer header present
        """
        auth_header = self._get_authorization_header(request)
        
        if auth_header is None:
            return AuthenticationResult(status=AuthenticationStatus.SKIP)
        
        # Extract token from Bearer header
        token = self._extract_bearer_token(auth_header)
        if token is None:
            return AuthenticationResult(status=AuthenticationStatus.SKIP)
        
        # Validate token against store
        token_data = await self._token_store.validate_access_token(token)
        
        if token_data is None:
            return AuthenticationResult(
                status=AuthenticationStatus.FAILURE,
                error_code="invalid_token",
                error_description="The access token is invalid or has expired"
            )
        
        # Create authentication context from token data
        return self._create_success_result(token_data)
    
    def create_authorization_url(
        self,
        client_id: str,
        redirect_uri: str,
        scope: Optional[Set[str]] = None,
        state: Optional[str] = None,
        code_challenge: Optional[str] = None,
        code_challenge_method: Optional[str] = None,
        base_url: str = ""
    ) -> str:
        """
            Create an authorization URL for the Authorization Code flow.
            
            :param client_id: The client identifier.
            :param redirect_uri: The redirect URI for the callback.
            :param scope: Optional set of requested scopes.
            :param state: Optional state parameter for CSRF protection.
            :param code_challenge: Optional PKCE code challenge.
            :param code_challenge_method: Optional PKCE method ("plain" or "S256").
            :param base_url: Optional base URL to prepend to the endpoint.
            
            :returns: The authorization URL with query parameters.
        """
        params: Dict[str, str] = {
            "response_type": "code",
            "client_id": client_id,
            "redirect_uri": redirect_uri
        }
        
        if scope:
            params["scope"] = " ".join(scope)
        
        if state:
            params["state"] = state
        
        if code_challenge:
            params["code_challenge"] = code_challenge
            params["code_challenge_method"] = code_challenge_method or "S256"
        
        query_string = urlencode(params)
        return f"{base_url}{self._authorization_endpoint}?{query_string}"
    
    async def exchange_authorization_code(
        self,
        code: str,
        client_id: str,
        client_secret: Optional[str] = None,
        redirect_uri: Optional[str] = None,
        code_verifier: Optional[str] = None
    ) -> tuple[Optional[OAuth2Token], Optional[OAuth2Error]]:
        """
            Exchange an authorization code for tokens.
            
            :param code: The authorization code.
            :param client_id: The client identifier.
            :param client_secret: Optional client secret for confidential clients.
            :param redirect_uri: The redirect URI used in the authorization request.
            :param code_verifier: Optional PKCE code verifier.
            
            :returns: Tuple of (OAuth2Token, None) on success or
                     (None, OAuth2Error) on failure.
        """
        if self._code_store is None:
            return None, OAuth2Error(
                error="server_error",
                error_description="Authorization code flow not configured"
            )
        
        # Validate client
        client_info = await self._client_store.validate_client(
            client_id, client_secret
        )
        if client_info is None:
            return None, OAuth2Error(
                error="invalid_client",
                error_description="Client authentication failed"
            )
        
        # Retrieve and validate authorization code
        auth_code = await self._code_store.get_code(code)
        if auth_code is None:
            return None, OAuth2Error(
                error="invalid_grant",
                error_description="Invalid authorization code"
            )
        
        # Check if code is expired
        if auth_code.is_expired:
            await self._code_store.delete_code(code)
            return None, OAuth2Error(
                error="invalid_grant",
                error_description="Authorization code has expired"
            )
        
        # Verify client_id matches
        if auth_code.client_id != client_id:
            return None, OAuth2Error(
                error="invalid_grant",
                error_description="Authorization code was not issued to this client"
            )
        
        # Verify redirect_uri matches
        if redirect_uri and auth_code.redirect_uri != redirect_uri:
            return None, OAuth2Error(
                error="invalid_grant",
                error_description="Redirect URI mismatch"
            )
        
        # Verify PKCE if code challenge was used
        if auth_code.code_challenge:
            if code_verifier is None:
                return None, OAuth2Error(
                    error="invalid_grant",
                    error_description="Code verifier required"
                )
            
            if not verify_code_challenge(
                code_verifier,
                auth_code.code_challenge,
                auth_code.code_challenge_method or "S256"
            ):
                return None, OAuth2Error(
                    error="invalid_grant",
                    error_description="Code verifier validation failed"
                )
        elif self._require_pkce:
            return None, OAuth2Error(
                error="invalid_grant",
                error_description="PKCE is required"
            )
        
        # Delete the code (single use)
        await self._code_store.delete_code(code)
        
        # Generate tokens
        token = self._generate_token(
            client_id=client_id,
            user_id=auth_code.user_id,
            scope=auth_code.scope,
            include_refresh=True
        )
        
        # Store the token
        await self._token_store.store_token(
            token, client_id, auth_code.user_id
        )
        
        return token, None
    
    async def client_credentials_grant(
        self,
        client_id: str,
        client_secret: str,
        scope: Optional[Set[str]] = None
    ) -> tuple[Optional[OAuth2Token], Optional[OAuth2Error]]:
        """
            Obtain tokens using the Client Credentials flow.
            
            :param client_id: The client identifier.
            :param client_secret: The client secret.
            :param scope: Optional set of requested scopes.
            
            :returns: Tuple of (OAuth2Token, None) on success or
                     (None, OAuth2Error) on failure.
        """
        if OAuth2GrantType.CLIENT_CREDENTIALS not in self._supported_grant_types:
            return None, OAuth2Error(
                error="unsupported_grant_type",
                error_description="Client credentials grant not supported"
            )
        
        # Validate client credentials
        client_info = await self._client_store.validate_client(
            client_id, client_secret
        )
        if client_info is None:
            return None, OAuth2Error(
                error="invalid_client",
                error_description="Client authentication failed"
            )
        
        # Generate token (no refresh token for client credentials)
        token = self._generate_token(
            client_id=client_id,
            scope=scope,
            include_refresh=False
        )
        
        # Store the token
        await self._token_store.store_token(token, client_id)
        
        return token, None
    
    async def password_grant(
        self,
        client_id: str,
        client_secret: Optional[str],
        username: str,
        password: str,
        scope: Optional[Set[str]] = None
    ) -> tuple[Optional[OAuth2Token], Optional[OAuth2Error]]:
        """
            Obtain tokens using the Resource Owner Password Credentials flow.
            
            :param client_id: The client identifier.
            :param client_secret: Optional client secret.
            :param username: The resource owner's username.
            :param password: The resource owner's password.
            :param scope: Optional set of requested scopes.
            
            :returns: Tuple of (OAuth2Token, None) on success or
                     (None, OAuth2Error) on failure.
        """
        if OAuth2GrantType.PASSWORD not in self._supported_grant_types:
            return None, OAuth2Error(
                error="unsupported_grant_type",
                error_description="Password grant not supported"
            )
        
        if self._user_authenticator is None:
            return None, OAuth2Error(
                error="server_error",
                error_description="Password grant not configured"
            )
        
        # Validate client
        client_info = await self._client_store.validate_client(
            client_id, client_secret
        )
        if client_info is None:
            return None, OAuth2Error(
                error="invalid_client",
                error_description="Client authentication failed"
            )
        
        # Authenticate user
        user_info = await self._user_authenticator.authenticate_user(
            username, password
        )
        if user_info is None:
            return None, OAuth2Error(
                error="invalid_grant",
                error_description="Invalid username or password"
            )
        
        user_id = user_info.get("id") or user_info.get("sub") or username
        
        # Generate token with refresh token
        token = self._generate_token(
            client_id=client_id,
            user_id=user_id,
            scope=scope,
            include_refresh=True
        )
        
        # Store the token
        await self._token_store.store_token(token, client_id, user_id)
        
        return token, None
    
    async def refresh_token_grant(
        self,
        client_id: str,
        client_secret: Optional[str],
        refresh_token: str,
        scope: Optional[Set[str]] = None
    ) -> tuple[Optional[OAuth2Token], Optional[OAuth2Error]]:
        """
            Obtain new tokens using a refresh token.
            
            :param client_id: The client identifier.
            :param client_secret: Optional client secret.
            :param refresh_token: The refresh token.
            :param scope: Optional set of requested scopes (must be subset).
            
            :returns: Tuple of (OAuth2Token, None) on success or
                     (None, OAuth2Error) on failure.
        """
        if OAuth2GrantType.REFRESH_TOKEN not in self._supported_grant_types:
            return None, OAuth2Error(
                error="unsupported_grant_type",
                error_description="Refresh token grant not supported"
            )
        
        # Validate client
        client_info = await self._client_store.validate_client(
            client_id, client_secret
        )
        if client_info is None:
            return None, OAuth2Error(
                error="invalid_client",
                error_description="Client authentication failed"
            )
        
        # Validate refresh token
        token_data = await self._token_store.validate_refresh_token(refresh_token)
        if token_data is None:
            return None, OAuth2Error(
                error="invalid_grant",
                error_description="Invalid refresh token"
            )
        
        # Verify client_id matches
        if token_data.get("client_id") != client_id:
            return None, OAuth2Error(
                error="invalid_grant",
                error_description="Refresh token was not issued to this client"
            )
        
        # Determine scope (requested scope must be subset of original)
        original_scope = token_data.get("scope")
        if original_scope and isinstance(original_scope, str):
            original_scope = set(original_scope.split())
        elif original_scope and isinstance(original_scope, list):
            original_scope = set(original_scope)
        
        if scope and original_scope:
            if not scope.issubset(original_scope):
                return None, OAuth2Error(
                    error="invalid_scope",
                    error_description="Requested scope exceeds original scope"
                )
        else:
            scope = original_scope
        
        user_id = token_data.get("user_id")
        
        # Revoke old refresh token
        await self._token_store.revoke_token(refresh_token)
        
        # Generate new tokens
        token = self._generate_token(
            client_id=client_id,
            user_id=user_id,
            scope=scope,
            include_refresh=True
        )
        
        # Store the new token
        await self._token_store.store_token(token, client_id, user_id)
        
        return token, None
    
    def _get_authorization_header(self, request: Any) -> Optional[str]:
        """
            Extract the Authorization header from the request.
            
            :param request: The HTTP request object.
            
            :returns: The Authorization header value or None if not present.
        """
        # Handle dict-like request objects
        if isinstance(request, dict):
            headers = request.get("headers", {})
            if isinstance(headers, dict):
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
                return headers.get("Authorization") or headers.get("authorization")
        
        return None
    
    def _extract_bearer_token(self, auth_header: str) -> Optional[str]:
        """
            Extract the token from a Bearer Authorization header.
            
            :param auth_header: The Authorization header value.
            
            :returns: The token string if valid Bearer format, None otherwise.
        """
        if not auth_header:
            return None
        
        parts = auth_header.split(' ', 1)
        if len(parts) != 2:
            return None
        
        scheme, token = parts
        if scheme.lower() != 'bearer':
            return None
        
        token = token.strip()
        if not token:
            return None
        
        return token
    
    def _generate_token(
        self,
        client_id: str,
        user_id: Optional[str] = None,
        scope: Optional[Set[str]] = None,
        include_refresh: bool = True
    ) -> OAuth2Token:
        """
            Generate an OAuth2Token with access and optional refresh tokens.
            
            :param client_id: The client identifier.
            :param user_id: Optional user identifier.
            :param scope: Optional set of scopes.
            :param include_refresh: Whether to include a refresh token.
            
            :returns: An OAuth2Token instance.
        """
        access_token = secrets.token_urlsafe(32)
        refresh_token = secrets.token_urlsafe(32) if include_refresh else None
        
        return OAuth2Token(
            access_token=access_token,
            token_type="Bearer",
            expires_in=self._default_token_lifetime,
            refresh_token=refresh_token,
            scope=scope
        )
    
    def _create_success_result(
        self,
        token_data: Dict[str, Any]
    ) -> AuthenticationResult:
        """
            Create a successful authentication result from token data.
            
            :param token_data: The token data dictionary.
            
            :returns: An AuthenticationResult with SUCCESS status and context.
        """
        # Extract principal information
        identifier = (
            token_data.get("user_id") or
            token_data.get("sub") or
            token_data.get("client_id") or
            "unknown"
        )
        display_name = token_data.get("name")
        roles = set(token_data.get("roles", []))
        permissions = set(token_data.get("permissions", []))
        
        # Handle scope as roles if no explicit roles
        if not roles and "scope" in token_data:
            scope = token_data["scope"]
            if isinstance(scope, str):
                roles = set(scope.split())
            elif isinstance(scope, (list, set)):
                roles = set(scope)
        
        principal = Principal(
            identifier=identifier,
            display_name=display_name,
            roles=roles,
            permissions=permissions,
            attributes=token_data
        )
        
        # Determine expiration
        expires_at = None
        if "exp" in token_data:
            try:
                expires_at = datetime.fromtimestamp(token_data["exp"], tz=timezone.utc)
            except (TypeError, ValueError, OSError):
                pass
        elif "expires_at" in token_data:
            exp_val = token_data["expires_at"]
            if isinstance(exp_val, datetime):
                expires_at = exp_val
            elif isinstance(exp_val, (int, float)):
                try:
                    expires_at = datetime.fromtimestamp(exp_val, tz=timezone.utc)
                except (TypeError, ValueError, OSError):
                    pass
        
        return AuthenticationResult(
            status=AuthenticationStatus.SUCCESS,
            context=AuthenticationContext(
                principal=principal,
                scheme=self.scheme,
                expires_at=expires_at,
                attributes=token_data
            )
        )


def create_oauth2_error_response(error: OAuth2Error) -> Dict[str, Any]:
    """
        Create an OAuth 2.0 error response dictionary.
        
        This function creates a properly formatted error response
        as defined in RFC 6749 Section 5.2.
        
        :param error: The OAuth2Error to convert.
        
        :returns: Dictionary suitable for JSON serialization.
    """
    return error.to_dict()
