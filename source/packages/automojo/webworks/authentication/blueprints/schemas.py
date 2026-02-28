"""
.. module:: schemas
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Common request and response schemas for authentication blueprints.

.. moduleauthor:: Automation Mojo LLC

This module provides shared request and response schema dataclasses used
across the authentication blueprints. These schemas define the structure
of data exchanged between clients and authentication endpoints.
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class LoginRequest:
    """
        Request schema for basic login endpoints.

        :param username: The username credential.
        :param password: The password credential.
    """

    username: str
    password: str


@dataclass
class LoginResponse:
    """
        Response schema for basic login endpoints.

        :param authenticated: Whether authentication was successful.
        :param principal_id: The identifier of the authenticated principal.
        :param message: An optional human-readable message.
    """

    authenticated: bool
    principal_id: Optional[str] = None
    message: Optional[str] = None


@dataclass
class TokenRequest:
    """
        Request schema for token endpoints.

        :param grant_type: The OAuth 2.0 grant type (e.g., "password", "refresh_token").
        :param username: The username for password grant.
        :param password: The password for password grant.
        :param refresh_token: The refresh token for refresh_token grant.
        :param scope: The requested scope.
    """

    grant_type: str
    username: Optional[str] = None
    password: Optional[str] = None
    refresh_token: Optional[str] = None
    scope: Optional[str] = None


@dataclass
class TokenResponse:
    """
        Response schema for token endpoints.

        :param access_token: The issued access token.
        :param token_type: The type of token issued (default "Bearer").
        :param expires_in: Token lifetime in seconds.
        :param refresh_token: An optional refresh token.
        :param scope: The scope of the access token.
    """

    access_token: str
    token_type: str = "Bearer"
    expires_in: Optional[int] = None
    refresh_token: Optional[str] = None
    scope: Optional[str] = None


@dataclass
class APIKeyCreateRequest:
    """
        Request schema for API key creation.

        :param name: A human-readable name for the API key.
        :param scopes: Optional list of permission scopes for the key.
        :param expires_in: Optional lifetime in seconds for the key.
    """

    name: str
    scopes: Optional[List[str]] = None
    expires_in: Optional[int] = None


@dataclass
class APIKeyResponse:
    """
        Response schema for API key operations.

        The ``key`` field is only populated in the creation response.
        Subsequent list or get operations will not include the raw key value.

        :param key_id: The unique identifier for the API key.
        :param name: The human-readable name of the key.
        :param key: The raw API key value (only returned on creation).
        :param scopes: The permission scopes assigned to the key.
        :param created_at: ISO 8601 timestamp of when the key was created.
        :param expires_at: Optional ISO 8601 timestamp of when the key expires.
    """

    key_id: str
    name: str
    key: Optional[str] = None
    scopes: List[str] = field(default_factory=list)
    created_at: Optional[str] = None
    expires_at: Optional[str] = None


@dataclass
class SessionLoginRequest:
    """
        Request schema for session-based login.

        :param username: The username credential.
        :param password: The password credential.
        :param remember_me: Whether to extend the session duration.
    """

    username: str
    password: str
    remember_me: bool = False


@dataclass
class SessionInfo:
    """
        Response schema for session information.

        :param session_id: The unique session identifier.
        :param principal_id: The identifier of the authenticated principal.
        :param created_at: ISO 8601 timestamp of when the session was created.
        :param expires_at: Optional ISO 8601 timestamp of when the session expires.
        :param last_accessed: ISO 8601 timestamp of the last session activity.
    """

    session_id: str
    principal_id: str
    created_at: str
    expires_at: Optional[str] = None
    last_accessed: Optional[str] = None


@dataclass
class OAuth2AuthorizeRequest:
    """
        Query parameters for the OAuth 2.0 authorization endpoint.

        :param response_type: The desired response type (e.g., "code").
        :param client_id: The client application identifier.
        :param redirect_uri: The URI to redirect to after authorization.
        :param scope: Optional requested scope.
        :param state: Optional opaque state value for CSRF protection.
        :param code_challenge: Optional PKCE code challenge.
        :param code_challenge_method: Optional PKCE challenge method ("S256" or "plain").
    """

    response_type: str
    client_id: str
    redirect_uri: str
    scope: Optional[str] = None
    state: Optional[str] = None
    code_challenge: Optional[str] = None
    code_challenge_method: Optional[str] = None


@dataclass
class OAuth2TokenRequest:
    """
        Request schema for the OAuth 2.0 token endpoint.

        :param grant_type: The grant type (e.g., "authorization_code", "client_credentials").
        :param code: The authorization code (for authorization_code grant).
        :param redirect_uri: The redirect URI used in the authorization request.
        :param client_id: The client application identifier.
        :param client_secret: The client secret for authentication.
        :param code_verifier: The PKCE code verifier.
        :param refresh_token: The refresh token (for refresh_token grant).
        :param scope: Optional requested scope.
    """

    grant_type: str
    code: Optional[str] = None
    redirect_uri: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    code_verifier: Optional[str] = None
    refresh_token: Optional[str] = None
    scope: Optional[str] = None


@dataclass
class OIDCDiscovery:
    """
        OpenID Connect discovery document.

        Contains the metadata about the OpenID Connect provider including
        endpoints, supported response types, signing algorithms, scopes,
        and claims.

        :param issuer: The issuer identifier URL.
        :param authorization_endpoint: URL of the authorization endpoint.
        :param token_endpoint: URL of the token endpoint.
        :param userinfo_endpoint: URL of the UserInfo endpoint.
        :param jwks_uri: URL of the JSON Web Key Set document.
        :param response_types_supported: List of supported response types.
        :param subject_types_supported: List of supported subject types.
        :param id_token_signing_alg_values_supported: List of supported
            signing algorithms for ID tokens.
        :param scopes_supported: List of supported OAuth 2.0 scopes.
        :param claims_supported: List of supported claims.
    """

    issuer: str
    authorization_endpoint: str
    token_endpoint: str
    userinfo_endpoint: str
    jwks_uri: str
    response_types_supported: List[str] = field(default_factory=list)
    subject_types_supported: List[str] = field(default_factory=list)
    id_token_signing_alg_values_supported: List[str] = field(
        default_factory=list
    )
    scopes_supported: List[str] = field(default_factory=list)
    claims_supported: List[str] = field(default_factory=list)


@dataclass
class UserInfo:
    """
        UserInfo response schema.

        Contains claims about the authenticated user as returned by the
        UserInfo endpoint.

        :param sub: The subject identifier for the user.
        :param name: The user's full name.
        :param email: The user's email address.
        :param email_verified: Whether the email address has been verified.
        :param picture: URL of the user's profile picture.
    """

    sub: str
    name: Optional[str] = None
    email: Optional[str] = None
    email_verified: Optional[bool] = None
    picture: Optional[str] = None
