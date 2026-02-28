"""
    Tests for the OIDCAuthenticator module.
    
    This module contains unit tests and property-based tests for the
    OIDCAuthenticator class and related utility functions.
"""

import asyncio
import base64
import hashlib
import hmac
import json
import random
import secrets
import string
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set

from automojo.webworks.authentication import (
    AuthenticationStatus,
    AuthenticationResult,
    Principal,
    AuthenticationContext,
    IDTokenClaims,
    IDTokenValidationError,
    OIDCAuthenticator,
    OIDCProviderMetadata,
    OIDCTokenResponse,
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


# =============================================================================
# Test Data Generators
# =============================================================================

def generate_random_string(min_length: int = 1, max_length: int = 50) -> str:
    """
        Generate a random string of printable characters.
    """
    length = random.randint(min_length, max_length)
    chars = string.ascii_letters + string.digits + "_-."
    return ''.join(random.choices(chars, k=length))


def generate_random_identifier() -> str:
    """
        Generate a random identifier (alphanumeric).
    """
    length = random.randint(5, 30)
    chars = string.ascii_letters + string.digits
    return ''.join(random.choices(chars, k=length))


def generate_random_email() -> str:
    """
        Generate a random email address.
    """
    local = generate_random_string(5, 15)
    domain = generate_random_string(5, 10)
    return f"{local}@{domain}.com"


def generate_random_url() -> str:
    """
        Generate a random URL.
    """
    domain = generate_random_string(5, 15)
    path = generate_random_string(3, 10)
    return f"https://{domain}.example.com/{path}"


def generate_random_issuer() -> str:
    """
        Generate a random issuer URL.
    """
    domain = generate_random_string(5, 15)
    return f"https://{domain}.example.com"


def generate_random_client_id() -> str:
    """
        Generate a random client ID.
    """
    return f"client_{generate_random_identifier()}"


def generate_random_subject() -> str:
    """
        Generate a random subject identifier.
    """
    return generate_random_identifier()


def generate_random_name() -> str:
    """
        Generate a random full name.
    """
    first_names = ["Alice", "Bob", "Charlie", "Diana", "Eve", "Frank"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Davis"]
    return f"{random.choice(first_names)} {random.choice(last_names)}"


def generate_random_id_token_claims(
    issuer: Optional[str] = None,
    subject: Optional[str] = None,
    audience: Optional[str] = None,
    include_name: bool = True,
    include_email: bool = True,
    expired: bool = False
) -> Dict[str, Any]:
    """
        Generate random ID token claims.
    """
    now = int(time.time())
    
    claims = {
        "iss": issuer or generate_random_issuer(),
        "sub": subject or generate_random_subject(),
        "aud": audience or generate_random_client_id(),
        "exp": now - 3600 if expired else now + 3600,
        "iat": now - 60
    }
    
    if include_name:
        claims["name"] = generate_random_name()
    
    if include_email:
        claims["email"] = generate_random_email()
        claims["email_verified"] = random.choice([True, False])
    
    return claims


def create_unsigned_id_token(claims: Dict[str, Any]) -> str:
    """
        Create an unsigned ID token (alg: none) for testing.
    """
    header = {"alg": "none", "typ": "JWT"}
    
    header_b64 = base64.urlsafe_b64encode(
        json.dumps(header).encode()
    ).decode().rstrip('=')
    
    payload_b64 = base64.urlsafe_b64encode(
        json.dumps(claims).encode()
    ).decode().rstrip('=')
    
    return f"{header_b64}.{payload_b64}."


def create_hs256_id_token(claims: Dict[str, Any], secret: str) -> str:
    """
        Create an HS256 signed ID token for testing.
    """
    header = {"alg": "HS256", "typ": "JWT"}
    
    header_b64 = base64.urlsafe_b64encode(
        json.dumps(header).encode()
    ).decode().rstrip('=')
    
    payload_b64 = base64.urlsafe_b64encode(
        json.dumps(claims).encode()
    ).decode().rstrip('=')
    
    signing_input = f"{header_b64}.{payload_b64}"
    
    signature = hmac.new(
        secret.encode('utf-8'),
        signing_input.encode('utf-8'),
        hashlib.sha256
    ).digest()
    
    sig_b64 = base64.urlsafe_b64encode(signature).decode().rstrip('=')
    
    return f"{header_b64}.{payload_b64}.{sig_b64}"


# =============================================================================
# Mock Stores
# =============================================================================

class MockOIDCClientStore:
    """
        A mock OAuth2 client store for OIDC testing.
    """
    
    def __init__(self):
        self._clients: Dict[str, Dict[str, Any]] = {}
    
    def add_client(
        self,
        client_id: str,
        client_secret: Optional[str] = None,
        **kwargs
    ) -> None:
        """
            Add a client to the store.
        """
        self._clients[client_id] = {
            "client_id": client_id,
            "client_secret": client_secret,
            **kwargs
        }
    
    async def validate_client(
        self,
        client_id: str,
        client_secret: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
            Validate client credentials.
        """
        client = self._clients.get(client_id)
        if client is None:
            return None
        
        stored_secret = client.get("client_secret")
        if stored_secret is not None:
            if client_secret != stored_secret:
                return None
        
        return client
    
    async def get_client(self, client_id: str) -> Optional[Dict[str, Any]]:
        """
            Get client by ID.
        """
        return self._clients.get(client_id)


class MockOIDCTokenStore:
    """
        A mock OAuth2 token store for OIDC testing.
    """
    
    def __init__(self):
        self._access_tokens: Dict[str, Dict[str, Any]] = {}
        self._refresh_tokens: Dict[str, Dict[str, Any]] = {}
    
    def add_access_token(
        self,
        token: str,
        client_id: str,
        user_id: Optional[str] = None,
        scope: Optional[Set[str]] = None,
        expires_at: Optional[datetime] = None,
        **kwargs
    ) -> None:
        """
            Add an access token to the store.
        """
        self._access_tokens[token] = {
            "access_token": token,
            "client_id": client_id,
            "user_id": user_id,
            "scope": scope,
            "expires_at": expires_at,
            **kwargs
        }
    
    async def store_token(self, token: Any, client_id: str, user_id: Optional[str] = None) -> None:
        """
            Store a token.
        """
        pass
    
    async def validate_access_token(self, access_token: str) -> Optional[Dict[str, Any]]:
        """
            Validate an access token.
        """
        token_data = self._access_tokens.get(access_token)
        if token_data is None:
            return None
        
        expires_at = token_data.get("expires_at")
        if expires_at and datetime.utcnow() > expires_at:
            return None
        
        return token_data
    
    async def validate_refresh_token(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        """
            Validate a refresh token.
        """
        return self._refresh_tokens.get(refresh_token)
    
    async def revoke_token(self, token: str) -> bool:
        """
            Revoke a token.
        """
        if token in self._access_tokens:
            del self._access_tokens[token]
            return True
        return False


# =============================================================================
# Helper Functions
# =============================================================================

def run_async(coro):
    """
        Run an async coroutine synchronously for testing.
    """
    return asyncio.get_event_loop().run_until_complete(coro)


# =============================================================================
# Unit Tests for Nonce Functions
# =============================================================================

def test_generate_nonce_default_length():
    """
        Test generating nonce with default length.
    """
    nonce = generate_nonce()
    
    if len(nonce) != 32:
        errmsg = f"Expected length 32, got {len(nonce)}"
        raise AssertionError(errmsg)
    
    return


def test_generate_nonce_custom_length():
    """
        Test generating nonce with custom length.
    """
    nonce = generate_nonce(length=64)
    
    if len(nonce) != 64:
        errmsg = f"Expected length 64, got {len(nonce)}"
        raise AssertionError(errmsg)
    
    return


def test_validate_nonce_matching():
    """
        Test validating matching nonce values.
    """
    nonce = generate_nonce()
    
    result = validate_nonce(nonce, nonce)
    
    if not result:
        errmsg = "Expected validation to succeed for matching nonces"
        raise AssertionError(errmsg)
    
    return


def test_validate_nonce_mismatched():
    """
        Test validating mismatched nonce values.
    """
    nonce1 = generate_nonce()
    nonce2 = generate_nonce()
    
    result = validate_nonce(nonce1, nonce2)
    
    if result:
        errmsg = "Expected validation to fail for mismatched nonces"
        raise AssertionError(errmsg)
    
    return


def test_validate_nonce_none():
    """
        Test validating None nonce value.
    """
    nonce = generate_nonce()
    
    result = validate_nonce(nonce, None)
    
    if result:
        errmsg = "Expected validation to fail for None nonce"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for Discovery URL
# =============================================================================

def test_build_discovery_url():
    """
        Test building discovery URL.
    """
    issuer = "https://auth.example.com"
    
    url = build_discovery_url(issuer)
    
    expected = "https://auth.example.com/.well-known/openid-configuration"
    if url != expected:
        errmsg = f"Expected '{expected}', got '{url}'"
        raise AssertionError(errmsg)
    
    return


def test_build_discovery_url_with_trailing_slash():
    """
        Test building discovery URL with trailing slash in issuer.
    """
    issuer = "https://auth.example.com/"
    
    url = build_discovery_url(issuer)
    
    expected = "https://auth.example.com/.well-known/openid-configuration"
    if url != expected:
        errmsg = f"Expected '{expected}', got '{url}'"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for ID Token Decoding
# =============================================================================

def test_decode_id_token_unverified():
    """
        Test decoding ID token without verification.
    """
    claims = {
        "iss": "https://auth.example.com",
        "sub": "user123",
        "aud": "client123",
        "exp": int(time.time()) + 3600,
        "iat": int(time.time())
    }
    
    token = create_unsigned_id_token(claims)
    header, payload = decode_id_token_unverified(token)
    
    if header.get("alg") != "none":
        errmsg = f"Expected alg 'none', got '{header.get('alg')}'"
        raise AssertionError(errmsg)
    
    if payload.get("sub") != "user123":
        errmsg = f"Expected sub 'user123', got '{payload.get('sub')}'"
        raise AssertionError(errmsg)
    
    return


def test_decode_id_token_unverified_invalid_format():
    """
        Test decoding invalid ID token format.
    """
    try:
        decode_id_token_unverified("invalid.token")
        raise AssertionError("Expected IDTokenValidationError")
    except IDTokenValidationError as e:
        if e.error != "invalid_token":
            errmsg = f"Expected error 'invalid_token', got '{e.error}'"
            raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for ID Token Claim Validation
# =============================================================================

def test_validate_id_token_claims_valid():
    """
        Test validating valid ID token claims.
    """
    issuer = "https://auth.example.com"
    audience = "client123"
    
    claims = {
        "iss": issuer,
        "sub": "user123",
        "aud": audience,
        "exp": int(time.time()) + 3600,
        "iat": int(time.time())
    }
    
    result = validate_id_token_claims(claims, issuer, audience)
    
    if result.sub != "user123":
        errmsg = f"Expected sub 'user123', got '{result.sub}'"
        raise AssertionError(errmsg)
    
    return


def test_validate_id_token_claims_invalid_issuer():
    """
        Test validating claims with invalid issuer.
    """
    claims = {
        "iss": "https://wrong.example.com",
        "sub": "user123",
        "aud": "client123",
        "exp": int(time.time()) + 3600,
        "iat": int(time.time())
    }
    
    try:
        validate_id_token_claims(claims, "https://auth.example.com", "client123")
        raise AssertionError("Expected IDTokenValidationError")
    except IDTokenValidationError as e:
        if "issuer" not in e.error_description.lower():
            errmsg = f"Expected issuer error, got '{e.error_description}'"
            raise AssertionError(errmsg)
    
    return


def test_validate_id_token_claims_invalid_audience():
    """
        Test validating claims with invalid audience.
    """
    claims = {
        "iss": "https://auth.example.com",
        "sub": "user123",
        "aud": "wrong_client",
        "exp": int(time.time()) + 3600,
        "iat": int(time.time())
    }
    
    try:
        validate_id_token_claims(claims, "https://auth.example.com", "client123")
        raise AssertionError("Expected IDTokenValidationError")
    except IDTokenValidationError as e:
        if "audience" not in e.error_description.lower():
            errmsg = f"Expected audience error, got '{e.error_description}'"
            raise AssertionError(errmsg)
    
    return


def test_validate_id_token_claims_expired():
    """
        Test validating expired claims.
    """
    claims = {
        "iss": "https://auth.example.com",
        "sub": "user123",
        "aud": "client123",
        "exp": int(time.time()) - 3600,  # Expired
        "iat": int(time.time()) - 7200
    }
    
    try:
        validate_id_token_claims(claims, "https://auth.example.com", "client123")
        raise AssertionError("Expected IDTokenValidationError")
    except IDTokenValidationError as e:
        if "expired" not in e.error_description.lower():
            errmsg = f"Expected expiration error, got '{e.error_description}'"
            raise AssertionError(errmsg)
    
    return


def test_validate_id_token_claims_with_nonce():
    """
        Test validating claims with nonce.
    """
    nonce = generate_nonce()
    
    claims = {
        "iss": "https://auth.example.com",
        "sub": "user123",
        "aud": "client123",
        "exp": int(time.time()) + 3600,
        "iat": int(time.time()),
        "nonce": nonce
    }
    
    result = validate_id_token_claims(
        claims, "https://auth.example.com", "client123", nonce=nonce
    )
    
    if result.nonce != nonce:
        errmsg = f"Expected nonce '{nonce}', got '{result.nonce}'"
        raise AssertionError(errmsg)
    
    return


def test_validate_id_token_claims_nonce_mismatch():
    """
        Test validating claims with mismatched nonce.
    """
    claims = {
        "iss": "https://auth.example.com",
        "sub": "user123",
        "aud": "client123",
        "exp": int(time.time()) + 3600,
        "iat": int(time.time()),
        "nonce": "token_nonce"
    }
    
    try:
        validate_id_token_claims(
            claims, "https://auth.example.com", "client123", nonce="expected_nonce"
        )
        raise AssertionError("Expected IDTokenValidationError")
    except IDTokenValidationError as e:
        if "nonce" not in e.error_description.lower():
            errmsg = f"Expected nonce error, got '{e.error_description}'"
            raise AssertionError(errmsg)
    
    return


def test_validate_id_token_claims_multiple_audiences():
    """
        Test validating claims with multiple audiences.
    """
    claims = {
        "iss": "https://auth.example.com",
        "sub": "user123",
        "aud": ["client123", "client456"],
        "azp": "client123",
        "exp": int(time.time()) + 3600,
        "iat": int(time.time())
    }
    
    result = validate_id_token_claims(claims, "https://auth.example.com", "client123")
    
    if result.azp != "client123":
        errmsg = f"Expected azp 'client123', got '{result.azp}'"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for HMAC Signature Verification
# =============================================================================

def test_verify_id_token_signature_hmac_valid():
    """
        Test verifying valid HMAC signature.
    """
    secret = "test_secret_key"
    claims = {
        "iss": "https://auth.example.com",
        "sub": "user123",
        "aud": "client123",
        "exp": int(time.time()) + 3600,
        "iat": int(time.time())
    }
    
    token = create_hs256_id_token(claims, secret)
    
    result = verify_id_token_signature_hmac(token, secret, "HS256")
    
    if not result:
        errmsg = "Expected signature verification to succeed"
        raise AssertionError(errmsg)
    
    return


def test_verify_id_token_signature_hmac_invalid():
    """
        Test verifying invalid HMAC signature.
    """
    claims = {
        "iss": "https://auth.example.com",
        "sub": "user123",
        "aud": "client123",
        "exp": int(time.time()) + 3600,
        "iat": int(time.time())
    }
    
    token = create_hs256_id_token(claims, "correct_secret")
    
    result = verify_id_token_signature_hmac(token, "wrong_secret", "HS256")
    
    if result:
        errmsg = "Expected signature verification to fail"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for IDTokenClaims
# =============================================================================

def test_id_token_claims_from_dict():
    """
        Test creating IDTokenClaims from dictionary.
    """
    now = int(time.time())
    data = {
        "iss": "https://auth.example.com",
        "sub": "user123",
        "aud": "client123",
        "exp": now + 3600,
        "iat": now,
        "name": "Test User",
        "email": "test@example.com",
        "email_verified": True
    }
    
    claims = IDTokenClaims.from_dict(data)
    
    if claims.sub != "user123":
        errmsg = f"Expected sub 'user123', got '{claims.sub}'"
        raise AssertionError(errmsg)
    
    if claims.name != "Test User":
        errmsg = f"Expected name 'Test User', got '{claims.name}'"
        raise AssertionError(errmsg)
    
    if claims.email != "test@example.com":
        errmsg = f"Expected email 'test@example.com', got '{claims.email}'"
        raise AssertionError(errmsg)
    
    return


def test_id_token_claims_to_dict():
    """
        Test converting IDTokenClaims to dictionary.
    """
    now = int(time.time())
    claims = IDTokenClaims(
        iss="https://auth.example.com",
        sub="user123",
        aud=["client123"],
        exp=now + 3600,
        iat=now,
        name="Test User",
        email="test@example.com"
    )
    
    result = claims.to_dict()
    
    if result["sub"] != "user123":
        errmsg = f"Expected sub 'user123', got '{result['sub']}'"
        raise AssertionError(errmsg)
    
    if result["name"] != "Test User":
        errmsg = f"Expected name 'Test User', got '{result['name']}'"
        raise AssertionError(errmsg)
    
    return


def test_id_token_claims_is_expired():
    """
        Test IDTokenClaims.is_expired property.
    """
    now = int(time.time())
    
    # Not expired
    claims = IDTokenClaims(
        iss="https://auth.example.com",
        sub="user123",
        aud=["client123"],
        exp=now + 3600,
        iat=now
    )
    
    if claims.is_expired:
        errmsg = "Expected claims to not be expired"
        raise AssertionError(errmsg)
    
    # Expired
    expired_claims = IDTokenClaims(
        iss="https://auth.example.com",
        sub="user123",
        aud=["client123"],
        exp=now - 3600,
        iat=now - 7200
    )
    
    if not expired_claims.is_expired:
        errmsg = "Expected claims to be expired"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for UserInfo
# =============================================================================

def test_userinfo_from_dict():
    """
        Test creating UserInfo from dictionary.
    """
    data = {
        "sub": "user123",
        "name": "Test User",
        "given_name": "Test",
        "family_name": "User",
        "email": "test@example.com",
        "email_verified": True,
        "picture": "https://example.com/photo.jpg"
    }
    
    userinfo = UserInfo.from_dict(data)
    
    if userinfo.sub != "user123":
        errmsg = f"Expected sub 'user123', got '{userinfo.sub}'"
        raise AssertionError(errmsg)
    
    if userinfo.name != "Test User":
        errmsg = f"Expected name 'Test User', got '{userinfo.name}'"
        raise AssertionError(errmsg)
    
    if userinfo.email != "test@example.com":
        errmsg = f"Expected email 'test@example.com', got '{userinfo.email}'"
        raise AssertionError(errmsg)
    
    return


def test_userinfo_to_dict():
    """
        Test converting UserInfo to dictionary.
    """
    userinfo = UserInfo(
        sub="user123",
        name="Test User",
        email="test@example.com",
        email_verified=True
    )
    
    result = userinfo.to_dict()
    
    if result["sub"] != "user123":
        errmsg = f"Expected sub 'user123', got '{result['sub']}'"
        raise AssertionError(errmsg)
    
    if result["name"] != "Test User":
        errmsg = f"Expected name 'Test User', got '{result['name']}'"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for OIDCProviderMetadata
# =============================================================================

def test_oidc_provider_metadata_from_dict():
    """
        Test creating OIDCProviderMetadata from dictionary.
    """
    data = {
        "issuer": "https://auth.example.com",
        "authorization_endpoint": "https://auth.example.com/authorize",
        "token_endpoint": "https://auth.example.com/token",
        "userinfo_endpoint": "https://auth.example.com/userinfo",
        "jwks_uri": "https://auth.example.com/.well-known/jwks.json",
        "scopes_supported": ["openid", "profile", "email"],
        "response_types_supported": ["code", "token"],
        "id_token_signing_alg_values_supported": ["RS256", "HS256"]
    }
    
    metadata = OIDCProviderMetadata.from_dict(data)
    
    if metadata.issuer != "https://auth.example.com":
        errmsg = f"Expected issuer 'https://auth.example.com', got '{metadata.issuer}'"
        raise AssertionError(errmsg)
    
    if "openid" not in metadata.scopes_supported:
        errmsg = f"Expected 'openid' in scopes_supported"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for OIDCTokenResponse
# =============================================================================

def test_oidc_token_response_from_dict():
    """
        Test creating OIDCTokenResponse from dictionary.
    """
    data = {
        "access_token": "access123",
        "token_type": "Bearer",
        "id_token": "id_token_jwt",
        "expires_in": 3600,
        "refresh_token": "refresh456",
        "scope": "openid profile email"
    }
    
    response = OIDCTokenResponse.from_dict(data)
    
    if response.access_token != "access123":
        errmsg = f"Expected access_token 'access123', got '{response.access_token}'"
        raise AssertionError(errmsg)
    
    if response.id_token != "id_token_jwt":
        errmsg = f"Expected id_token 'id_token_jwt', got '{response.id_token}'"
        raise AssertionError(errmsg)
    
    if response.scope != {"openid", "profile", "email"}:
        errmsg = f"Expected scope set, got '{response.scope}'"
        raise AssertionError(errmsg)
    
    return


def test_oidc_token_response_to_dict():
    """
        Test converting OIDCTokenResponse to dictionary.
    """
    response = OIDCTokenResponse(
        access_token="access123",
        token_type="Bearer",
        id_token="id_token_jwt",
        expires_in=3600,
        scope={"openid", "profile"}
    )
    
    result = response.to_dict()
    
    if result["access_token"] != "access123":
        errmsg = f"Expected access_token 'access123', got '{result['access_token']}'"
        raise AssertionError(errmsg)
    
    if result["id_token"] != "id_token_jwt":
        errmsg = f"Expected id_token 'id_token_jwt', got '{result['id_token']}'"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for OIDCAuthenticator
# =============================================================================

def test_oidc_authenticator_scheme():
    """
        Test that OIDCAuthenticator returns "OIDC" as scheme.
    """
    client_store = MockOIDCClientStore()
    token_store = MockOIDCTokenStore()
    
    authenticator = OIDCAuthenticator(
        client_store=client_store,
        token_store=token_store,
        issuer="https://auth.example.com",
        client_id="test_client"
    )
    
    if authenticator.scheme != "OIDC":
        errmsg = f"Expected scheme 'OIDC', got '{authenticator.scheme}'"
        raise AssertionError(errmsg)
    
    return


def test_oidc_authenticator_issuer():
    """
        Test that OIDCAuthenticator returns correct issuer.
    """
    client_store = MockOIDCClientStore()
    token_store = MockOIDCTokenStore()
    
    authenticator = OIDCAuthenticator(
        client_store=client_store,
        token_store=token_store,
        issuer="https://auth.example.com",
        client_id="test_client"
    )
    
    if authenticator.issuer != "https://auth.example.com":
        errmsg = f"Expected issuer 'https://auth.example.com', got '{authenticator.issuer}'"
        raise AssertionError(errmsg)
    
    return


def test_oidc_authenticator_client_id():
    """
        Test that OIDCAuthenticator returns correct client_id.
    """
    client_store = MockOIDCClientStore()
    token_store = MockOIDCTokenStore()
    
    authenticator = OIDCAuthenticator(
        client_store=client_store,
        token_store=token_store,
        issuer="https://auth.example.com",
        client_id="test_client"
    )
    
    if authenticator.client_id != "test_client":
        errmsg = f"Expected client_id 'test_client', got '{authenticator.client_id}'"
        raise AssertionError(errmsg)
    
    return


def test_oidc_authenticator_create_authorization_url():
    """
        Test creating OIDC authorization URL.
    """
    client_store = MockOIDCClientStore()
    token_store = MockOIDCTokenStore()
    
    authenticator = OIDCAuthenticator(
        client_store=client_store,
        token_store=token_store,
        issuer="https://auth.example.com",
        client_id="test_client",
        authorization_endpoint="/oauth/authorize"
    )
    
    url = authenticator.create_authorization_url(
        redirect_uri="https://example.com/callback",
        scope={"profile", "email"},
        state="test_state",
        nonce="test_nonce"
    )
    
    if "/oauth/authorize?" not in url:
        errmsg = f"Expected authorization endpoint in URL, got '{url}'"
        raise AssertionError(errmsg)
    
    if "client_id=test_client" not in url:
        errmsg = f"Expected client_id in URL, got '{url}'"
        raise AssertionError(errmsg)
    
    if "openid" not in url:
        errmsg = f"Expected 'openid' scope in URL, got '{url}'"
        raise AssertionError(errmsg)
    
    if "nonce=test_nonce" not in url:
        errmsg = f"Expected nonce in URL, got '{url}'"
        raise AssertionError(errmsg)
    
    return


def test_oidc_authenticator_validate_id_token_hmac():
    """
        Test validating ID token with HMAC signature.
    """
    client_store = MockOIDCClientStore()
    token_store = MockOIDCTokenStore()
    client_secret = "test_secret_key"
    
    authenticator = OIDCAuthenticator(
        client_store=client_store,
        token_store=token_store,
        issuer="https://auth.example.com",
        client_id="test_client",
        client_secret=client_secret,
        supported_algorithms={"HS256"}
    )
    
    claims = {
        "iss": "https://auth.example.com",
        "sub": "user123",
        "aud": "test_client",
        "exp": int(time.time()) + 3600,
        "iat": int(time.time()),
        "name": "Test User",
        "email": "test@example.com"
    }
    
    token = create_hs256_id_token(claims, client_secret)
    
    result = run_async(authenticator.validate_id_token(token))
    
    if result.sub != "user123":
        errmsg = f"Expected sub 'user123', got '{result.sub}'"
        raise AssertionError(errmsg)
    
    if result.name != "Test User":
        errmsg = f"Expected name 'Test User', got '{result.name}'"
        raise AssertionError(errmsg)
    
    if result.email != "test@example.com":
        errmsg = f"Expected email 'test@example.com', got '{result.email}'"
        raise AssertionError(errmsg)
    
    return


def test_oidc_authenticator_validate_id_token_invalid_signature():
    """
        Test validating ID token with invalid signature.
    """
    client_store = MockOIDCClientStore()
    token_store = MockOIDCTokenStore()
    
    authenticator = OIDCAuthenticator(
        client_store=client_store,
        token_store=token_store,
        issuer="https://auth.example.com",
        client_id="test_client",
        client_secret="correct_secret",
        supported_algorithms={"HS256"}
    )
    
    claims = {
        "iss": "https://auth.example.com",
        "sub": "user123",
        "aud": "test_client",
        "exp": int(time.time()) + 3600,
        "iat": int(time.time())
    }
    
    token = create_hs256_id_token(claims, "wrong_secret")
    
    try:
        run_async(authenticator.validate_id_token(token))
        raise AssertionError("Expected IDTokenValidationError")
    except IDTokenValidationError as e:
        if "signature" not in e.error_description.lower():
            errmsg = f"Expected signature error, got '{e.error_description}'"
            raise AssertionError(errmsg)
    
    return


# =============================================================================
# Property-Based Tests
# =============================================================================

def test_property_19_oidc_id_token_claim_extraction():
    """
        Property 19: OIDC ID Token Claim Extraction
        
        *For any* valid OIDC id_token, the Authentication_Context SHALL contain
        the standard claims (sub, name, email) as Principal attributes when
        present in the token.
        
        **Feature: authentication, Property 19: OIDC ID Token Claim Extraction**
        **Validates: Requirements 7.4, 7.5**
        
        This property test verifies that:
        1. The 'sub' claim is always extracted and becomes the Principal identifier
        2. The 'name' claim, when present, is extracted into the context
        3. The 'email' claim, when present, is extracted into the context
        4. All standard OIDC claims present in the token appear in the attributes
    """
    client_store = MockOIDCClientStore()
    token_store = MockOIDCTokenStore()
    client_secret = "test_secret_for_property_test"
    issuer = "https://auth.example.com"
    client_id = "test_client"
    
    authenticator = OIDCAuthenticator(
        client_store=client_store,
        token_store=token_store,
        issuer=issuer,
        client_id=client_id,
        client_secret=client_secret,
        supported_algorithms={"HS256"}
    )
    
    # Run 100 iterations with random claims
    for iteration in range(100):
        # Generate random claims
        include_name = random.choice([True, False])
        include_email = random.choice([True, False])
        include_picture = random.choice([True, False])
        include_given_name = random.choice([True, False])
        include_family_name = random.choice([True, False])
        
        now = int(time.time())
        subject = generate_random_subject()
        
        claims = {
            "iss": issuer,
            "sub": subject,
            "aud": client_id,
            "exp": now + 3600,
            "iat": now
        }
        
        # Add optional claims
        expected_name = None
        if include_name:
            expected_name = generate_random_name()
            claims["name"] = expected_name
        
        expected_email = None
        if include_email:
            expected_email = generate_random_email()
            claims["email"] = expected_email
            claims["email_verified"] = random.choice([True, False])
        
        expected_picture = None
        if include_picture:
            expected_picture = generate_random_url()
            claims["picture"] = expected_picture
        
        expected_given_name = None
        if include_given_name:
            expected_given_name = random.choice(["Alice", "Bob", "Charlie", "Diana"])
            claims["given_name"] = expected_given_name
        
        expected_family_name = None
        if include_family_name:
            expected_family_name = random.choice(["Smith", "Johnson", "Williams"])
            claims["family_name"] = expected_family_name
        
        # Create signed token
        token = create_hs256_id_token(claims, client_secret)
        
        # Validate token and extract claims
        try:
            result = run_async(authenticator.validate_id_token(token))
        except IDTokenValidationError as e:
            errmsg = f"Iteration {iteration}: Unexpected validation error: {e.error_description}"
            raise AssertionError(errmsg)
        
        # Verify 'sub' claim is always extracted
        if result.sub != subject:
            errmsg = f"Iteration {iteration}: Expected sub '{subject}', got '{result.sub}'"
            raise AssertionError(errmsg)
        
        # Verify 'name' claim extraction when present
        if include_name:
            if result.name != expected_name:
                errmsg = f"Iteration {iteration}: Expected name '{expected_name}', got '{result.name}'"
                raise AssertionError(errmsg)
        
        # Verify 'email' claim extraction when present
        if include_email:
            if result.email != expected_email:
                errmsg = f"Iteration {iteration}: Expected email '{expected_email}', got '{result.email}'"
                raise AssertionError(errmsg)
        
        # Verify 'picture' claim extraction when present
        if include_picture:
            if result.picture != expected_picture:
                errmsg = f"Iteration {iteration}: Expected picture '{expected_picture}', got '{result.picture}'"
                raise AssertionError(errmsg)
        
        # Verify all claims appear in to_dict()
        result_dict = result.to_dict()
        
        for claim_key, claim_value in claims.items():
            if claim_key in result_dict:
                if result_dict[claim_key] != claim_value:
                    # Handle audience which may be converted to list
                    if claim_key == "aud":
                        if isinstance(result_dict[claim_key], list):
                            if claim_value not in result_dict[claim_key]:
                                errmsg = f"Iteration {iteration}: Claim '{claim_key}' mismatch"
                                raise AssertionError(errmsg)
                        continue
                    errmsg = f"Iteration {iteration}: Claim '{claim_key}' expected '{claim_value}', got '{result_dict[claim_key]}'"
                    raise AssertionError(errmsg)
    
    return


# =============================================================================
# Additional Unit Tests for Extract Functions
# =============================================================================

def test_extract_standard_claims():
    """
        Test extracting standard OIDC claims from a claims dictionary.
    """
    claims = {
        "sub": "user123",
        "name": "Test User",
        "email": "test@example.com",
        "custom_claim": "custom_value",
        "another_custom": 12345
    }
    
    standard = extract_standard_claims(claims)
    
    if "sub" not in standard:
        errmsg = "Expected 'sub' in standard claims"
        raise AssertionError(errmsg)
    
    if "name" not in standard:
        errmsg = "Expected 'name' in standard claims"
        raise AssertionError(errmsg)
    
    if "email" not in standard:
        errmsg = "Expected 'email' in standard claims"
        raise AssertionError(errmsg)
    
    if "custom_claim" in standard:
        errmsg = "Did not expect 'custom_claim' in standard claims"
        raise AssertionError(errmsg)
    
    return


def test_extract_id_token_claims():
    """
        Test separating standard and custom claims.
    """
    claims = {
        "iss": "https://auth.example.com",
        "sub": "user123",
        "aud": "client123",
        "exp": 1234567890,
        "iat": 1234567800,
        "name": "Test User",
        "email": "test@example.com",
        "custom_claim": "custom_value",
        "another_custom": 12345
    }
    
    standard, custom = extract_id_token_claims(claims)
    
    # Standard claims should include iss, sub, aud, exp, iat, name, email
    if "iss" not in standard:
        errmsg = "Expected 'iss' in standard claims"
        raise AssertionError(errmsg)
    
    if "sub" not in standard:
        errmsg = "Expected 'sub' in standard claims"
        raise AssertionError(errmsg)
    
    if "name" not in standard:
        errmsg = "Expected 'name' in standard claims"
        raise AssertionError(errmsg)
    
    # Custom claims should include custom_claim and another_custom
    if "custom_claim" not in custom:
        errmsg = "Expected 'custom_claim' in custom claims"
        raise AssertionError(errmsg)
    
    if "another_custom" not in custom:
        errmsg = "Expected 'another_custom' in custom claims"
        raise AssertionError(errmsg)
    
    # Custom claims should not include standard claims
    if "sub" in custom:
        errmsg = "Did not expect 'sub' in custom claims"
        raise AssertionError(errmsg)
    
    return
