"""
.. module:: authentication
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Authentication infrastructure for the automojo-webworks framework.

.. moduleauthor:: Automation Mojo LLC

This module provides a modular, extensible framework for authenticating requests.
It follows a pluggable architecture where different authentication mechanisms
(Basic, Bearer, OAuth2, etc.) are implemented as discrete Authenticator components.
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


from automojo.webworks.authentication.apikey import (
    APIKeyAuthenticator,
    APIKeyLocation,
    APIKeyStore,
    extract_api_key
)
from automojo.webworks.authentication.authenticator import Authenticator
from automojo.webworks.authentication.basic import (
    BasicAuthenticator,
    IdentityProvider,
    encode_basic_credentials,
    create_basic_auth_header
)
from automojo.webworks.authentication.bearer import (
    BearerAuthenticator,
    TokenStore,
    decode_jwt,
    encode_jwt,
    extract_bearer_token,
    JWTError,
    JWTExpiredError,
    JWTInvalidSignatureError,
    JWTInvalidClaimsError,
    JWTDecodeError
)
from automojo.webworks.authentication.core import (
    AuthenticationStatus,
    AuthenticationResult,
    Principal,
    AuthenticationContext,
    verify_authentication_context_compliance,
    verify_principal_compliance
)
from automojo.webworks.authentication.errors import (
    AccountLockedError,
    AccountLockoutEntry,
    AccountLockoutPolicy,
    AuthenticationError,
    InternalAuthenticationError,
    LockoutConfig,
    RateLimitConfig,
    RateLimitEntry,
    RateLimitExceededError,
    RateLimiter,
    create_safe_error_response,
    handle_authentication_error,
    sanitize_credentials,
    sanitize_dict,
    wrap_internal_error
)
from automojo.webworks.authentication.digest import (
    DigestAlgorithm,
    DigestAuthenticator,
    DigestCredentials,
    DigestIdentityProvider,
    NonceData,
    NonceStore,
    compute_digest_response,
    compute_ha1,
    create_digest_auth_header
)
from automojo.webworks.authentication.hmac_auth import (
    HMACAlgorithm,
    HMACAuthenticator,
    HMACCredentials,
    HMACKeyStore,
    compute_hmac_signature,
    create_hmac_auth_header
)
from automojo.webworks.authentication.oauth2 import (
    OAuth2Authenticator,
    OAuth2AuthorizationCode,
    OAuth2AuthorizationCodeStore,
    OAuth2ClientStore,
    OAuth2Error,
    OAuth2GrantType,
    OAuth2Token,
    OAuth2TokenStore,
    OAuth2UserAuthenticator,
    PKCEMethod,
    create_oauth2_error_response,
    generate_code_challenge,
    generate_code_verifier,
    generate_state,
    validate_state,
    verify_code_challenge
)
from automojo.webworks.authentication.oidc import (
    IDTokenClaims,
    IDTokenValidationError,
    OIDCAuthenticator,
    OIDCKeyProvider,
    OIDCProviderDiscovery,
    OIDCProviderMetadata,
    OIDCTokenResponse,
    OIDCUserInfoProvider,
    UserInfo,
    build_discovery_url,
    decode_id_token_unverified,
    extract_id_token_claims,
    extract_standard_claims,
    generate_nonce,
    validate_id_token_claims,
    validate_nonce,
    verify_id_token_signature_hmac
)
from automojo.webworks.authentication.session import (
    CookieAttributes,
    InMemorySessionStore,
    SameSitePolicy,
    SessionAuthenticator,
    SessionData,
    SessionStore,
    generate_secure_session_id
)
from automojo.webworks.authentication.system import AuthenticationSystem
from automojo.webworks.authentication.middleware import (
    AuthenticationMiddleware,
    create_authentication_middleware
)
from automojo.webworks.authentication.blueprints import (
    APIKeyBlueprint,
    APIKeyCreateRequest,
    APIKeyResponse,
    AuthError,
    AuthResponse,
    BasicAuthBlueprint,
    BearerAuthBlueprint,
    OAuth2Blueprint,
    OIDCBlueprint,
    SecurityBlueprint,
    SessionAuthBlueprint,
)


__all__ = [
    "AccountLockedError",
    "AccountLockoutEntry",
    "AccountLockoutPolicy",
    "APIKeyAuthenticator",
    "APIKeyBlueprint",
    "APIKeyCreateRequest",
    "APIKeyLocation",
    "APIKeyResponse",
    "APIKeyStore",
    "AuthError",
    "AuthResponse",
    "Authenticator",
    "AuthenticationContext",
    "AuthenticationError",
    "AuthenticationMiddleware",
    "AuthenticationResult",
    "AuthenticationStatus",
    "AuthenticationSystem",
    "BasicAuthBlueprint",
    "BasicAuthenticator",
    "BearerAuthBlueprint",
    "BearerAuthenticator",
    "CookieAttributes",
    "DigestAlgorithm",
    "DigestAuthenticator",
    "DigestCredentials",
    "DigestIdentityProvider",
    "HMACAlgorithm",
    "HMACAuthenticator",
    "HMACCredentials",
    "HMACKeyStore",
    "IDTokenClaims",
    "IDTokenValidationError",
    "IdentityProvider",
    "InMemorySessionStore",
    "InternalAuthenticationError",
    "JWTDecodeError",
    "JWTError",
    "JWTExpiredError",
    "JWTInvalidClaimsError",
    "JWTInvalidSignatureError",
    "LockoutConfig",
    "NonceData",
    "NonceStore",
    "OAuth2Authenticator",
    "OAuth2AuthorizationCode",
    "OAuth2AuthorizationCodeStore",
    "OAuth2Blueprint",
    "OAuth2ClientStore",
    "OAuth2Error",
    "OAuth2GrantType",
    "OAuth2Token",
    "OAuth2TokenStore",
    "OAuth2UserAuthenticator",
    "OIDCAuthenticator",
    "OIDCBlueprint",
    "OIDCKeyProvider",
    "OIDCProviderDiscovery",
    "OIDCProviderMetadata",
    "OIDCTokenResponse",
    "OIDCUserInfoProvider",
    "PKCEMethod",
    "Principal",
    "RateLimitConfig",
    "RateLimitEntry",
    "RateLimitExceededError",
    "RateLimiter",
    "SameSitePolicy",
    "SecurityBlueprint",
    "SessionAuthBlueprint",
    "SessionAuthenticator",
    "SessionData",
    "SessionStore",
    "TokenStore",
    "UserInfo",
    "build_discovery_url",
    "compute_digest_response",
    "compute_ha1",
    "compute_hmac_signature",
    "create_authentication_middleware",
    "create_basic_auth_header",
    "create_digest_auth_header",
    "create_hmac_auth_header",
    "create_oauth2_error_response",
    "create_safe_error_response",
    "decode_id_token_unverified",
    "decode_jwt",
    "encode_basic_credentials",
    "encode_jwt",
    "extract_api_key",
    "extract_bearer_token",
    "extract_id_token_claims",
    "extract_standard_claims",
    "generate_code_challenge",
    "generate_code_verifier",
    "generate_nonce",
    "generate_secure_session_id",
    "generate_state",
    "handle_authentication_error",
    "sanitize_credentials",
    "sanitize_dict",
    "validate_id_token_claims",
    "validate_nonce",
    "validate_state",
    "verify_authentication_context_compliance",
    "verify_code_challenge",
    "verify_id_token_signature_hmac",
    "verify_principal_compliance",
    "wrap_internal_error",
]
