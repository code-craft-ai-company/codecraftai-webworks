"""
.. module:: oidc
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: OpenID Connect Authentication implementation.

.. moduleauthor:: Code Craft AI LLC

This module provides the OIDCAuthenticator class which extends OAuth 2.0
authentication with OpenID Connect identity layer support. It implements
id_token validation, discovery endpoint support, and UserInfo endpoint access.
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


import base64
import hashlib
import hmac
import json
import logging
import secrets
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Protocol, Set, Tuple, runtime_checkable
from urllib.parse import urlencode

from ccai.webworks.authentication.core import (
    AuthenticationContext,
    AuthenticationResult,
    AuthenticationStatus,
    Principal
)
from ccai.webworks.authentication.oauth2 import (
    OAuth2Authenticator,
    OAuth2AuthorizationCodeStore,
    OAuth2ClientStore,
    OAuth2TokenStore,
    OAuth2UserAuthenticator,
)


# Module-level logger for the OIDC helpers. Signature-verification
# failures and id_token decode errors are logged at warning so the
# operator can spot a misconfigured IdP or an attempted forgery.
logger = logging.getLogger(__name__)


# =============================================================================
# OIDC Standard Claims
# =============================================================================

# Standard OIDC claims as defined in OpenID Connect Core 1.0
OIDC_STANDARD_CLAIMS = {
    "sub",           # Subject - Identifier for the End-User
    "name",          # Full name
    "given_name",    # Given name(s) or first name(s)
    "family_name",   # Surname(s) or last name(s)
    "middle_name",   # Middle name(s)
    "nickname",      # Casual name
    "preferred_username",  # Shorthand name
    "profile",       # Profile page URL
    "picture",       # Profile picture URL
    "website",       # Web page or blog URL
    "email",         # Preferred e-mail address
    "email_verified",  # True if email has been verified
    "gender",        # Gender
    "birthdate",     # Birthday
    "zoneinfo",      # Time zone
    "locale",        # Locale
    "phone_number",  # Preferred telephone number
    "phone_number_verified",  # True if phone number has been verified
    "address",       # Preferred postal address
    "updated_at",    # Time the information was last updated
}


# =============================================================================
# OIDC Data Classes
# =============================================================================

@dataclass
class OIDCProviderMetadata:
    """
        OpenID Connect Provider Metadata as defined in OpenID Connect Discovery 1.0.
        
        This dataclass represents the metadata returned from the
        .well-known/openid-configuration endpoint.
        
        :param issuer: URL that the OP asserts as its Issuer Identifier.
        :param authorization_endpoint: URL of the OP's Authorization Endpoint.
        :param token_endpoint: URL of the OP's Token Endpoint.
        :param userinfo_endpoint: URL of the OP's UserInfo Endpoint.
        :param jwks_uri: URL of the OP's JSON Web Key Set document.
        :param registration_endpoint: URL of the OP's Dynamic Client Registration Endpoint.
        :param scopes_supported: List of OAuth 2.0 scope values supported.
        :param response_types_supported: List of OAuth 2.0 response_type values supported.
        :param grant_types_supported: List of OAuth 2.0 grant_type values supported.
        :param subject_types_supported: List of Subject Identifier types supported.
        :param id_token_signing_alg_values_supported: List of JWS signing algorithms supported.
        :param claims_supported: List of Claim Names supported.
    """
    
    issuer: str
    authorization_endpoint: str
    token_endpoint: str
    userinfo_endpoint: Optional[str] = None
    jwks_uri: Optional[str] = None
    registration_endpoint: Optional[str] = None
    scopes_supported: List[str] = field(default_factory=lambda: ["openid"])
    response_types_supported: List[str] = field(default_factory=lambda: ["code"])
    grant_types_supported: List[str] = field(default_factory=lambda: ["authorization_code"])
    subject_types_supported: List[str] = field(default_factory=lambda: ["public"])
    id_token_signing_alg_values_supported: List[str] = field(default_factory=lambda: ["RS256"])
    claims_supported: List[str] = field(default_factory=list)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OIDCProviderMetadata":
        """
            Create OIDCProviderMetadata from a dictionary.
            
            :param data: Dictionary containing provider metadata.
            
            :returns: An OIDCProviderMetadata instance.
        """
        return cls(
            issuer=data["issuer"],
            authorization_endpoint=data["authorization_endpoint"],
            token_endpoint=data["token_endpoint"],
            userinfo_endpoint=data.get("userinfo_endpoint"),
            jwks_uri=data.get("jwks_uri"),
            registration_endpoint=data.get("registration_endpoint"),
            scopes_supported=data.get("scopes_supported", ["openid"]),
            response_types_supported=data.get("response_types_supported", ["code"]),
            grant_types_supported=data.get("grant_types_supported", ["authorization_code"]),
            subject_types_supported=data.get("subject_types_supported", ["public"]),
            id_token_signing_alg_values_supported=data.get(
                "id_token_signing_alg_values_supported", ["RS256"]
            ),
            claims_supported=data.get("claims_supported", [])
        )


@dataclass
class OIDCTokenResponse:
    """
        OpenID Connect Token Response.
        
        This dataclass extends the OAuth 2.0 token response with the
        id_token field required by OpenID Connect.
        
        :param access_token: The access token string.
        :param token_type: The token type (typically "Bearer").
        :param id_token: The ID Token (JWT) containing identity claims.
        :param expires_in: Optional time in seconds until token expires.
        :param refresh_token: Optional refresh token.
        :param scope: Optional set of granted scopes.
    """
    
    access_token: str
    token_type: str = "Bearer"
    id_token: Optional[str] = None
    expires_in: Optional[int] = None
    refresh_token: Optional[str] = None
    scope: Optional[Set[str]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """
            Convert the token response to a dictionary.
            
            :returns: Dictionary representation of the token response.
        """
        result: Dict[str, Any] = {
            "access_token": self.access_token,
            "token_type": self.token_type
        }
        if self.id_token is not None:
            result["id_token"] = self.id_token
        if self.expires_in is not None:
            result["expires_in"] = self.expires_in
        if self.refresh_token is not None:
            result["refresh_token"] = self.refresh_token
        if self.scope is not None:
            result["scope"] = " ".join(self.scope)
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OIDCTokenResponse":
        """
            Create an OIDCTokenResponse from a dictionary.
            
            :param data: Dictionary containing token response data.
            
            :returns: An OIDCTokenResponse instance.
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
            id_token=data.get("id_token"),
            expires_in=data.get("expires_in"),
            refresh_token=data.get("refresh_token"),
            scope=scope
        )


@dataclass
class IDTokenClaims:
    """
        ID Token claims as defined in OpenID Connect Core 1.0.
        
        This dataclass represents the claims contained in an ID Token.
        
        :param iss: Issuer Identifier.
        :param sub: Subject Identifier.
        :param aud: Audience(s) the ID Token is intended for.
        :param exp: Expiration time.
        :param iat: Time at which the JWT was issued.
        :param auth_time: Time when End-User authentication occurred.
        :param nonce: String value used to associate a Client session with an ID Token.
        :param acr: Authentication Context Class Reference.
        :param amr: Authentication Methods References.
        :param azp: Authorized party.
        :param name: Full name.
        :param email: Email address.
        :param email_verified: Whether email is verified.
        :param picture: Profile picture URL.
        :param additional_claims: Any additional claims not in the standard set.
    """
    
    iss: str
    sub: str
    aud: List[str]
    exp: int
    iat: int
    auth_time: Optional[int] = None
    nonce: Optional[str] = None
    acr: Optional[str] = None
    amr: Optional[List[str]] = None
    azp: Optional[str] = None
    name: Optional[str] = None
    email: Optional[str] = None
    email_verified: Optional[bool] = None
    picture: Optional[str] = None
    additional_claims: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def is_expired(self) -> bool:
        """
            Check if the ID token has expired.
            
            :returns: True if expired, False otherwise.
        """
        return time.time() > self.exp
    
    def to_dict(self) -> Dict[str, Any]:
        """
            Convert the claims to a dictionary.
            
            :returns: Dictionary representation of the claims.
        """
        result: Dict[str, Any] = {
            "iss": self.iss,
            "sub": self.sub,
            "aud": self.aud,
            "exp": self.exp,
            "iat": self.iat
        }
        if self.auth_time is not None:
            result["auth_time"] = self.auth_time
        if self.nonce is not None:
            result["nonce"] = self.nonce
        if self.acr is not None:
            result["acr"] = self.acr
        if self.amr is not None:
            result["amr"] = self.amr
        if self.azp is not None:
            result["azp"] = self.azp
        if self.name is not None:
            result["name"] = self.name
        if self.email is not None:
            result["email"] = self.email
        if self.email_verified is not None:
            result["email_verified"] = self.email_verified
        if self.picture is not None:
            result["picture"] = self.picture
        result.update(self.additional_claims)
        return result

    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "IDTokenClaims":
        """
            Create IDTokenClaims from a dictionary.
            
            :param data: Dictionary containing ID token claims.
            
            :returns: An IDTokenClaims instance.
        """
        # Extract standard claims
        aud = data.get("aud", [])
        if isinstance(aud, str):
            aud = [aud]
        
        amr = data.get("amr")
        if amr is not None and not isinstance(amr, list):
            amr = [amr]
        
        # Collect additional claims
        standard_keys = {
            "iss", "sub", "aud", "exp", "iat", "auth_time", "nonce",
            "acr", "amr", "azp", "name", "email", "email_verified", "picture"
        }
        additional = {k: v for k, v in data.items() if k not in standard_keys}
        
        return cls(
            iss=data["iss"],
            sub=data["sub"],
            aud=aud,
            exp=data["exp"],
            iat=data["iat"],
            auth_time=data.get("auth_time"),
            nonce=data.get("nonce"),
            acr=data.get("acr"),
            amr=amr,
            azp=data.get("azp"),
            name=data.get("name"),
            email=data.get("email"),
            email_verified=data.get("email_verified"),
            picture=data.get("picture"),
            additional_claims=additional
        )


@dataclass
class UserInfo:
    """
        UserInfo response as defined in OpenID Connect Core 1.0.
        
        This dataclass represents the claims returned from the UserInfo endpoint.
        
        :param sub: Subject Identifier.
        :param name: Full name.
        :param given_name: Given name(s) or first name(s).
        :param family_name: Surname(s) or last name(s).
        :param middle_name: Middle name(s).
        :param nickname: Casual name.
        :param preferred_username: Shorthand name.
        :param profile: Profile page URL.
        :param picture: Profile picture URL.
        :param website: Web page or blog URL.
        :param email: Preferred e-mail address.
        :param email_verified: True if email has been verified.
        :param gender: Gender.
        :param birthdate: Birthday.
        :param zoneinfo: Time zone.
        :param locale: Locale.
        :param phone_number: Preferred telephone number.
        :param phone_number_verified: True if phone number has been verified.
        :param address: Preferred postal address.
        :param updated_at: Time the information was last updated.
        :param additional_claims: Any additional claims.
    """
    
    sub: str
    name: Optional[str] = None
    given_name: Optional[str] = None
    family_name: Optional[str] = None
    middle_name: Optional[str] = None
    nickname: Optional[str] = None
    preferred_username: Optional[str] = None
    profile: Optional[str] = None
    picture: Optional[str] = None
    website: Optional[str] = None
    email: Optional[str] = None
    email_verified: Optional[bool] = None
    gender: Optional[str] = None
    birthdate: Optional[str] = None
    zoneinfo: Optional[str] = None
    locale: Optional[str] = None
    phone_number: Optional[str] = None
    phone_number_verified: Optional[bool] = None
    address: Optional[Dict[str, Any]] = None
    updated_at: Optional[int] = None
    additional_claims: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """
            Convert the UserInfo to a dictionary.
            
            :returns: Dictionary representation of the UserInfo.
        """
        result: Dict[str, Any] = {"sub": self.sub}
        
        optional_fields = [
            "name", "given_name", "family_name", "middle_name", "nickname",
            "preferred_username", "profile", "picture", "website", "email",
            "email_verified", "gender", "birthdate", "zoneinfo", "locale",
            "phone_number", "phone_number_verified", "address", "updated_at"
        ]
        
        for field_name in optional_fields:
            value = getattr(self, field_name)
            if value is not None:
                result[field_name] = value
        
        result.update(self.additional_claims)
        return result

    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserInfo":
        """
            Create UserInfo from a dictionary.
            
            :param data: Dictionary containing UserInfo claims.
            
            :returns: A UserInfo instance.
        """
        standard_keys = {
            "sub", "name", "given_name", "family_name", "middle_name",
            "nickname", "preferred_username", "profile", "picture", "website",
            "email", "email_verified", "gender", "birthdate", "zoneinfo",
            "locale", "phone_number", "phone_number_verified", "address",
            "updated_at"
        }
        additional = {k: v for k, v in data.items() if k not in standard_keys}
        
        return cls(
            sub=data["sub"],
            name=data.get("name"),
            given_name=data.get("given_name"),
            family_name=data.get("family_name"),
            middle_name=data.get("middle_name"),
            nickname=data.get("nickname"),
            preferred_username=data.get("preferred_username"),
            profile=data.get("profile"),
            picture=data.get("picture"),
            website=data.get("website"),
            email=data.get("email"),
            email_verified=data.get("email_verified"),
            gender=data.get("gender"),
            birthdate=data.get("birthdate"),
            zoneinfo=data.get("zoneinfo"),
            locale=data.get("locale"),
            phone_number=data.get("phone_number"),
            phone_number_verified=data.get("phone_number_verified"),
            address=data.get("address"),
            updated_at=data.get("updated_at"),
            additional_claims=additional
        )


# =============================================================================
# OIDC Protocols
# =============================================================================

@runtime_checkable
class OIDCProviderDiscovery(Protocol):
    """
        Protocol for OIDC provider discovery.
        
        Implementations of this protocol are responsible for fetching
        and caching provider metadata from the discovery endpoint.
    """
    
    async def get_provider_metadata(
        self,
        issuer: str
    ) -> Optional[OIDCProviderMetadata]:
        """
            Get provider metadata for an issuer.
            
            :param issuer: The issuer URL.
            
            :returns: Provider metadata if available, None otherwise.
        """


@runtime_checkable
class OIDCKeyProvider(Protocol):
    """
        Protocol for OIDC public key retrieval.
        
        Implementations of this protocol are responsible for fetching
        and caching public keys from the JWKS endpoint for signature
        verification.
    """
    
    async def get_public_key(
        self,
        issuer: str,
        kid: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
            Get a public key for signature verification.
            
            :param issuer: The issuer URL.
            :param kid: Optional key ID to retrieve a specific key.
            
            :returns: The public key data if found, None otherwise.
        """


@runtime_checkable
class OIDCUserInfoProvider(Protocol):
    """
        Protocol for fetching UserInfo from the UserInfo endpoint.
        
        Implementations of this protocol are responsible for making
        requests to the UserInfo endpoint with the access token.
    """
    
    async def get_userinfo(
        self,
        userinfo_endpoint: str,
        access_token: str
    ) -> Optional[UserInfo]:
        """
            Fetch UserInfo from the UserInfo endpoint.
            
            :param userinfo_endpoint: The UserInfo endpoint URL.
            :param access_token: The access token to use for authorization.
            
            :returns: UserInfo if successful, None otherwise.
        """


# =============================================================================
# ID Token Validation
# =============================================================================

class IDTokenValidationError(Exception):
    """
        Exception raised when ID token validation fails.
        
        :param error: Error code.
        :param error_description: Human-readable error description.
    """
    
    def __init__(self, error: str, error_description: str):
        self.error = error
        self.error_description = error_description
        super().__init__(error_description)


def decode_id_token_unverified(id_token: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
        Decode an ID token without verifying the signature.
        
        This function decodes the header and payload of a JWT ID token
        without verifying the signature. Use this only for extracting
        the key ID (kid) from the header before signature verification.
        
        :param id_token: The ID token string.
        
        :returns: Tuple of (header, payload) dictionaries.
        
        :raises IDTokenValidationError: If the token format is invalid.
    """
    try:
        parts = id_token.split('.')
        if len(parts) != 3:
            raise IDTokenValidationError(
                "invalid_token",
                "ID token must have three parts"
            )
        
        # Decode header
        header_b64 = parts[0]
        # Add padding if needed
        padding = 4 - len(header_b64) % 4
        if padding != 4:
            header_b64 += '=' * padding
        header_bytes = base64.urlsafe_b64decode(header_b64)
        header = json.loads(header_bytes.decode('utf-8'))
        
        # Decode payload
        payload_b64 = parts[1]
        padding = 4 - len(payload_b64) % 4
        if padding != 4:
            payload_b64 += '=' * padding
        payload_bytes = base64.urlsafe_b64decode(payload_b64)
        payload = json.loads(payload_bytes.decode('utf-8'))
        
        return header, payload
        
    except (ValueError, json.JSONDecodeError) as e:
        raise IDTokenValidationError(
            "invalid_token",
            f"Failed to decode ID token: {str(e)}"
        )


def validate_id_token_claims(
    claims: Dict[str, Any],
    issuer: str,
    audience: str,
    nonce: Optional[str] = None,
    max_age: Optional[int] = None
) -> IDTokenClaims:
    """
        Validate ID token claims according to OpenID Connect Core 1.0.
        
        :param claims: The decoded claims dictionary.
        :param issuer: Expected issuer value.
        :param audience: Expected audience (client_id).
        :param nonce: Expected nonce value (if used in authorization request).
        :param max_age: Maximum authentication age in seconds.
        
        :returns: Validated IDTokenClaims.
        
        :raises IDTokenValidationError: If validation fails.
    """
    # Validate required claims are present
    required_claims = ["iss", "sub", "aud", "exp", "iat"]
    for claim in required_claims:
        if claim not in claims:
            raise IDTokenValidationError(
                "invalid_token",
                f"Missing required claim: {claim}"
            )
    
    # Validate issuer
    if claims["iss"] != issuer:
        raise IDTokenValidationError(
            "invalid_token",
            f"Invalid issuer: expected '{issuer}', got '{claims['iss']}'"
        )
    
    # Validate audience
    aud = claims["aud"]
    if isinstance(aud, str):
        aud = [aud]
    
    if audience not in aud:
        raise IDTokenValidationError(
            "invalid_token",
            f"Invalid audience: '{audience}' not in {aud}"
        )
    
    # If multiple audiences, azp must be present and match client_id
    if len(aud) > 1:
        azp = claims.get("azp")
        if azp is None:
            raise IDTokenValidationError(
                "invalid_token",
                "azp claim required when multiple audiences present"
            )
        if azp != audience:
            raise IDTokenValidationError(
                "invalid_token",
                f"Invalid azp: expected '{audience}', got '{azp}'"
            )
    
    # Validate expiration
    exp = claims["exp"]
    if not isinstance(exp, (int, float)):
        raise IDTokenValidationError(
            "invalid_token",
            "exp claim must be a number"
        )
    
    if time.time() > exp:
        raise IDTokenValidationError(
            "invalid_token",
            "ID token has expired"
        )
    
    # Validate iat (issued at)
    iat = claims["iat"]
    if not isinstance(iat, (int, float)):
        raise IDTokenValidationError(
            "invalid_token",
            "iat claim must be a number"
        )
    
    # Validate nonce if provided
    if nonce is not None:
        token_nonce = claims.get("nonce")
        if token_nonce is None:
            raise IDTokenValidationError(
                "invalid_token",
                "nonce claim required but not present"
            )
        if not secrets.compare_digest(str(nonce), str(token_nonce)):
            raise IDTokenValidationError(
                "invalid_token",
                "nonce mismatch"
            )
    
    # Validate auth_time if max_age was specified
    if max_age is not None:
        auth_time = claims.get("auth_time")
        if auth_time is None:
            raise IDTokenValidationError(
                "invalid_token",
                "auth_time claim required when max_age specified"
            )
        if not isinstance(auth_time, (int, float)):
            raise IDTokenValidationError(
                "invalid_token",
                "auth_time claim must be a number"
            )
        if time.time() - auth_time > max_age:
            raise IDTokenValidationError(
                "invalid_token",
                "Authentication is too old"
            )
    
    return IDTokenClaims.from_dict(claims)


def verify_id_token_signature_hmac(
    id_token: str,
    secret: str,
    algorithm: str = "HS256"
) -> bool:
    """
        Verify an ID token signature using HMAC.
        
        :param id_token: The ID token string.
        :param secret: The shared secret for HMAC verification.
        :param algorithm: The HMAC algorithm (HS256, HS384, HS512).
        
        :returns: True if signature is valid, False otherwise.
    """
    try:
        parts = id_token.split('.')
        if len(parts) != 3:
            return False
        
        # Get the signing input (header.payload)
        signing_input = f"{parts[0]}.{parts[1]}"
        
        # Decode the signature
        sig_b64 = parts[2]
        padding = 4 - len(sig_b64) % 4
        if padding != 4:
            sig_b64 += '=' * padding
        signature = base64.urlsafe_b64decode(sig_b64)
        
        # Determine hash algorithm
        if algorithm == "HS256":
            hash_alg = hashlib.sha256
        elif algorithm == "HS384":
            hash_alg = hashlib.sha384
        elif algorithm == "HS512":
            hash_alg = hashlib.sha512
        else:
            return False
        
        # Compute expected signature
        expected_sig = hmac.HMAC(
            secret.encode('utf-8'),
            signing_input.encode('utf-8'),
            hash_alg
        ).digest()
        
        # Compare signatures using constant-time comparison
        return hmac.compare_digest(signature, expected_sig)

    except Exception as exc:
        # An ID-token signature verification failing is the canonical
        # sign of a tampered token or a misconfigured signing secret.
        # Operator should always see this in the journal (without the
        # token in plaintext).
        logger.warning(
            "OIDC: HMAC signature verification raised %s: %s",
            type(exc).__name__,
            exc,
        )
        return False


def _verify_id_token_signature_asymmetric(
    id_token: str,
    public_key: Dict[str, Any],
    algorithm: str
) -> bool:
    """
        Verify an ID token signature using an asymmetric public key.

        Handles the RSASSA-PKCS1-v1_5 (``RS*``), RSASSA-PSS (``PS*``),
        and ECDSA (``ES*``) algorithm families by delegating to the
        in-house :mod:`ccai.webworks.security.jsonwebtoken` module.
        The signature is verified over the ``header.payload`` segments
        of the compact token.

        :param id_token: The compact ID token string.
        :param public_key: The provider's public key as a raw JWK
                           mapping (as returned by an
                           :class:`OIDCKeyProvider`).
        :param algorithm: The token's signing algorithm.

        :returns: True if the signature is valid, False otherwise.
    """
    from ccai.webworks.security import jsonwebtoken

    try:
        parts = id_token.split('.')
        if len(parts) != 3:
            return False

        signing_input = "{}.{}".format(parts[0], parts[1]).encode("ascii")
        signature = jsonwebtoken.base64url_decode(parts[2])

        verification_key = jsonwebtoken.JsonWebKey(public_key)

        rtnval = jsonwebtoken.verify_signature(
            signing_input=signing_input,
            signature=signature,
            key=verification_key,
            algorithm=algorithm,
        )
        return rtnval

    except jsonwebtoken.JoseError as jose_exc:
        # A malformed key or unsupported algorithm is an operator
        # configuration problem; surface it in the journal (without the
        # token in plaintext) and treat the signature as invalid.
        logger.warning(
            "OIDC: asymmetric signature verification raised %s: %s",
            type(jose_exc).__name__,
            jose_exc,
        )
        return False


def extract_standard_claims(claims: Dict[str, Any]) -> Dict[str, Any]:
    """
        Extract standard OIDC claims from a claims dictionary.
        
        :param claims: The full claims dictionary.
        
        :returns: Dictionary containing only standard OIDC claims.
    """
    return {k: v for k, v in claims.items() if k in OIDC_STANDARD_CLAIMS}


# =============================================================================
# OIDC Authenticator
# =============================================================================

class OIDCAuthenticator(OAuth2Authenticator):
    """
        OpenID Connect Authentication implementation.
        
        This authenticator extends OAuth2Authenticator with OpenID Connect
        identity layer support. It provides:
        
        - ID Token validation (signature, issuer, audience, expiration)
        - Standard claim extraction (sub, name, email, etc.)
        - Discovery endpoint support (.well-known/openid-configuration)
        - UserInfo endpoint support
        
        Example usage::
        
            # Create authenticator
            authenticator = OIDCAuthenticator(
                client_store=my_client_store,
                token_store=my_token_store,
                issuer="https://auth.example.com",
                client_id="my-client-id"
            )
            
            # Validate ID token
            claims = await authenticator.validate_id_token(id_token)
            
            # Get UserInfo
            userinfo = await authenticator.get_userinfo(access_token)
        
        :param client_store: Store for validating OAuth 2.0 clients.
        :param token_store: Store for validating and storing tokens.
        :param issuer: The expected issuer URL.
        :param client_id: The client identifier (audience for ID tokens).
        :param client_secret: Optional client secret for HMAC signature verification.
        :param code_store: Optional store for authorization codes.
        :param user_authenticator: Optional authenticator for Password flow.
        :param key_provider: Optional provider for public keys (RSA/EC verification).
        :param discovery_provider: Optional provider for OIDC discovery.
        :param userinfo_provider: Optional provider for UserInfo endpoint.
        :param authorization_endpoint: URL path for authorization endpoint.
        :param token_endpoint: URL path for token endpoint.
        :param userinfo_endpoint: URL path for UserInfo endpoint.
        :param supported_algorithms: Set of supported signing algorithms.
        :param require_nonce: Whether to require nonce in ID tokens.
    """
    
    def __init__(
        self,
        client_store: OAuth2ClientStore,
        token_store: OAuth2TokenStore,
        issuer: str,
        client_id: str,
        client_secret: Optional[str] = None,
        code_store: Optional[OAuth2AuthorizationCodeStore] = None,
        user_authenticator: Optional[OAuth2UserAuthenticator] = None,
        key_provider: Optional[OIDCKeyProvider] = None,
        discovery_provider: Optional[OIDCProviderDiscovery] = None,
        userinfo_provider: Optional[OIDCUserInfoProvider] = None,
        authorization_endpoint: str = "/oauth/authorize",
        token_endpoint: str = "/oauth/token",
        userinfo_endpoint: Optional[str] = "/oauth/userinfo",
        supported_algorithms: Optional[Set[str]] = None,
        require_nonce: bool = False,
        **kwargs
    ):
        """
            Initialize the OIDCAuthenticator.
        """
        super().__init__(
            client_store=client_store,
            token_store=token_store,
            code_store=code_store,
            user_authenticator=user_authenticator,
            authorization_endpoint=authorization_endpoint,
            token_endpoint=token_endpoint,
            **kwargs
        )
        
        self._issuer = issuer
        self._client_id = client_id
        self._client_secret = client_secret
        self._key_provider = key_provider
        self._discovery_provider = discovery_provider
        self._userinfo_provider = userinfo_provider
        self._userinfo_endpoint = userinfo_endpoint
        self._supported_algorithms = supported_algorithms or {"HS256", "RS256"}
        self._require_nonce = require_nonce
        
        # Cache for provider metadata
        self._provider_metadata: Optional[OIDCProviderMetadata] = None
    
    @property
    def scheme(self) -> str:
        """
            Return the authentication scheme identifier.
            
            :returns: The string "OIDC".
        """
        return "OIDC"
    
    @property
    def issuer(self) -> str:
        """
            Return the expected issuer URL.
            
            :returns: The issuer URL.
        """
        return self._issuer
    
    @property
    def client_id(self) -> str:
        """
            Return the client identifier.
            
            :returns: The client ID.
        """
        return self._client_id

    
    async def validate_id_token(
        self,
        id_token: str,
        nonce: Optional[str] = None,
        max_age: Optional[int] = None
    ) -> IDTokenClaims:
        """
            Validate an ID token and return the claims.
            
            This method performs full validation of an ID token including:
            - Signature verification
            - Issuer validation
            - Audience validation
            - Expiration validation
            - Nonce validation (if provided)
            - auth_time validation (if max_age provided)
            
            :param id_token: The ID token string.
            :param nonce: Expected nonce value (if used in authorization request).
            :param max_age: Maximum authentication age in seconds.
            
            :returns: Validated IDTokenClaims.
            
            :raises IDTokenValidationError: If validation fails.
        """
        # Decode token without verification to get header
        header, payload = decode_id_token_unverified(id_token)
        
        # Get algorithm from header
        alg = header.get("alg")
        if alg is None:
            raise IDTokenValidationError(
                "invalid_token",
                "Missing algorithm in token header"
            )
        
        if alg not in self._supported_algorithms:
            raise IDTokenValidationError(
                "invalid_token",
                f"Unsupported algorithm: {alg}"
            )
        
        # Verify signature based on algorithm
        if alg.startswith("HS"):
            # HMAC signature - use client secret
            if self._client_secret is None:
                raise IDTokenValidationError(
                    "invalid_token",
                    "Client secret required for HMAC signature verification"
                )
            
            if not verify_id_token_signature_hmac(
                id_token, self._client_secret, alg
            ):
                raise IDTokenValidationError(
                    "invalid_token",
                    "Invalid signature"
                )
        
        elif alg.startswith("RS") or alg.startswith("ES") or alg.startswith("PS"):
            # RSA/EC/PS signature - use public key from provider
            if self._key_provider is None:
                raise IDTokenValidationError(
                    "invalid_token",
                    "Key provider required for RSA/EC signature verification"
                )
            
            kid = header.get("kid")
            public_key = await self._key_provider.get_public_key(
                self._issuer, kid
            )

            if public_key is None:
                raise IDTokenValidationError(
                    "invalid_token",
                    "Unable to retrieve public key for signature verification"
                )

            # Verify the RSA/EC/PS signature against the provider's
            # published public key using the in-house JOSE module.
            # ``get_public_key`` returns the raw JWK mapping; build a
            # verification key from it and confirm the signature over
            # the ``header.payload`` segments.
            if not _verify_id_token_signature_asymmetric(
                id_token, public_key, alg
            ):
                raise IDTokenValidationError(
                    "invalid_token",
                    "Invalid signature"
                )
        
        elif alg == "none":
            # Unsigned token - only accept if explicitly allowed
            if "none" not in self._supported_algorithms:
                raise IDTokenValidationError(
                    "invalid_token",
                    "Unsigned tokens not allowed"
                )
        
        else:
            raise IDTokenValidationError(
                "invalid_token",
                f"Unsupported algorithm: {alg}"
            )
        
        # Validate claims
        if self._require_nonce and nonce is None:
            raise IDTokenValidationError(
                "invalid_token",
                "Nonce is required but not provided"
            )
        
        return validate_id_token_claims(
            payload,
            self._issuer,
            self._client_id,
            nonce=nonce,
            max_age=max_age
        )
    
    async def get_provider_metadata(self) -> Optional[OIDCProviderMetadata]:
        """
            Get the OIDC provider metadata via discovery.
            
            This method fetches the provider metadata from the
            .well-known/openid-configuration endpoint.
            
            :returns: Provider metadata if available, None otherwise.
        """
        if self._provider_metadata is not None:
            return self._provider_metadata
        
        if self._discovery_provider is None:
            return None
        
        self._provider_metadata = await self._discovery_provider.get_provider_metadata(
            self._issuer
        )
        
        return self._provider_metadata
    
    async def get_userinfo(
        self,
        access_token: str
    ) -> Optional[UserInfo]:
        """
            Fetch UserInfo from the UserInfo endpoint.
            
            :param access_token: The access token to use for authorization.
            
            :returns: UserInfo if successful, None otherwise.
        """
        if self._userinfo_provider is None:
            return None
        
        # Get UserInfo endpoint from discovery or configuration
        userinfo_endpoint = self._userinfo_endpoint
        
        if userinfo_endpoint is None:
            metadata = await self.get_provider_metadata()
            if metadata is not None:
                userinfo_endpoint = metadata.userinfo_endpoint
        
        if userinfo_endpoint is None:
            return None
        
        return await self._userinfo_provider.get_userinfo(
            userinfo_endpoint,
            access_token
        )

    
    def create_authorization_url(
        self,
        redirect_uri: str,
        scope: Optional[Set[str]] = None,
        state: Optional[str] = None,
        nonce: Optional[str] = None,
        code_challenge: Optional[str] = None,
        code_challenge_method: Optional[str] = None,
        response_type: str = "code",
        prompt: Optional[str] = None,
        max_age: Optional[int] = None,
        ui_locales: Optional[str] = None,
        acr_values: Optional[str] = None,
        base_url: str = ""
    ) -> str:
        """
            Create an authorization URL for the OIDC Authorization Code flow.
            
            This method extends the OAuth2 authorization URL with OIDC-specific
            parameters like nonce, prompt, max_age, etc.
            
            :param redirect_uri: The redirect URI for the callback.
            :param scope: Optional set of requested scopes (openid is always included).
            :param state: Optional state parameter for CSRF protection.
            :param nonce: Optional nonce for ID token validation.
            :param code_challenge: Optional PKCE code challenge.
            :param code_challenge_method: Optional PKCE method ("plain" or "S256").
            :param response_type: Response type (default "code").
            :param prompt: Space-delimited list of prompt values (none, login, consent, select_account).
            :param max_age: Maximum authentication age in seconds.
            :param ui_locales: Preferred languages for the UI.
            :param acr_values: Requested Authentication Context Class Reference values.
            :param base_url: Optional base URL to prepend to the endpoint.
            
            :returns: The authorization URL with query parameters.
        """
        # Ensure openid scope is included
        if scope is None:
            scope = {"openid"}
        else:
            scope = scope | {"openid"}
        
        params: Dict[str, str] = {
            "response_type": response_type,
            "client_id": self._client_id,
            "redirect_uri": redirect_uri,
            "scope": " ".join(scope)
        }
        
        if state:
            params["state"] = state
        
        if nonce:
            params["nonce"] = nonce
        
        if code_challenge:
            params["code_challenge"] = code_challenge
            params["code_challenge_method"] = code_challenge_method or "S256"
        
        if prompt:
            params["prompt"] = prompt
        
        if max_age is not None:
            params["max_age"] = str(max_age)
        
        if ui_locales:
            params["ui_locales"] = ui_locales
        
        if acr_values:
            params["acr_values"] = acr_values
        
        query_string = urlencode(params)
        return f"{base_url}{self._authorization_endpoint}?{query_string}"
    
    async def authenticate(self, request: Any) -> AuthenticationResult:
        """
            Authenticate a request using the Bearer access token.
            
            This method extends OAuth2 authentication to also validate
            ID tokens when present and extract OIDC claims.
            
            :param request: The HTTP request containing the token.
            
            :returns: An AuthenticationResult with:
                     - SUCCESS and context if token is valid
                     - FAILURE with error if token is invalid
                     - SKIP if no Bearer header present
        """
        # Use parent class authentication
        result = await super().authenticate(request)
        
        if result.status == AuthenticationStatus.SUCCESS:
            # Update scheme to OIDC
            if result.context is not None:
                result.context.scheme = self.scheme
        
        return result
    
    def _create_success_result_from_id_token(
        self,
        claims: IDTokenClaims,
        access_token: Optional[str] = None,
        userinfo: Optional[UserInfo] = None
    ) -> AuthenticationResult:
        """
            Create a successful authentication result from ID token claims.
            
            :param claims: The validated ID token claims.
            :param access_token: Optional access token.
            :param userinfo: Optional UserInfo data.
            
            :returns: An AuthenticationResult with SUCCESS status and context.
        """
        # Build attributes from claims
        attributes = claims.to_dict()
        
        # Merge UserInfo if available
        if userinfo is not None:
            userinfo_dict = userinfo.to_dict()
            for key, value in userinfo_dict.items():
                if key not in attributes or attributes[key] is None:
                    attributes[key] = value
        
        # Extract roles from claims if present
        roles: Set[str] = set()
        if "roles" in attributes:
            role_val = attributes["roles"]
            if isinstance(role_val, list):
                roles = set(role_val)
            elif isinstance(role_val, str):
                roles = {role_val}
        
        # Extract permissions if present
        permissions: Set[str] = set()
        if "permissions" in attributes:
            perm_val = attributes["permissions"]
            if isinstance(perm_val, list):
                permissions = set(perm_val)
            elif isinstance(perm_val, str):
                permissions = {perm_val}
        
        principal = Principal(
            identifier=claims.sub,
            display_name=claims.name or userinfo.name if userinfo else claims.name,
            roles=roles,
            permissions=permissions,
            attributes=attributes
        )
        
        # Determine expiration
        expires_at = datetime.fromtimestamp(claims.exp, tz=timezone.utc)
        
        return AuthenticationResult(
            status=AuthenticationStatus.SUCCESS,
            context=AuthenticationContext(
                principal=principal,
                scheme=self.scheme,
                expires_at=expires_at,
                attributes=attributes
            )
        )


# =============================================================================
# Utility Functions
# =============================================================================

def generate_nonce(length: int = 32) -> str:
    """
        Generate a cryptographically secure nonce for OIDC.
        
        The nonce is used to associate a Client session with an ID Token
        and to mitigate replay attacks.
        
        :param length: Length of the nonce string. Default is 32.
        
        :returns: The nonce string.
    """
    return secrets.token_urlsafe(length)[:length]


def validate_nonce(expected_nonce: str, received_nonce: Optional[str]) -> bool:
    """
        Validate a nonce using constant-time comparison.
        
        :param expected_nonce: The expected nonce value.
        :param received_nonce: The received nonce value from the ID token.
        
        :returns: True if nonces match, False otherwise.
    """
    if received_nonce is None:
        return False
    return secrets.compare_digest(expected_nonce, received_nonce)


def build_discovery_url(issuer: str) -> str:
    """
        Build the OIDC discovery URL for an issuer.
        
        :param issuer: The issuer URL.
        
        :returns: The discovery endpoint URL.
    """
    # Remove trailing slash if present
    issuer = issuer.rstrip('/')
    return f"{issuer}/.well-known/openid-configuration"


def extract_id_token_claims(
    claims: Dict[str, Any]
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
        Separate standard OIDC claims from custom claims.
        
        :param claims: The full claims dictionary.
        
        :returns: Tuple of (standard_claims, custom_claims).
    """
    standard = {}
    custom = {}
    
    for key, value in claims.items():
        if key in OIDC_STANDARD_CLAIMS or key in {
            "iss", "sub", "aud", "exp", "iat", "auth_time", "nonce",
            "acr", "amr", "azp"
        }:
            standard[key] = value
        else:
            custom[key] = value
    
    return standard, custom
