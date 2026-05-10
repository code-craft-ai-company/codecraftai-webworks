"""
    Tests for the BearerAuthenticator module.
    
    This module contains unit tests and property-based tests for the
    BearerAuthenticator class and related utility functions.
"""

import asyncio
import random
import string
import time
from typing import Any, Dict, Optional, Set

from automojo.webworks.authentication import (
    AuthenticationStatus,
    AuthenticationResult,
    Principal,
    AuthenticationContext,
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


def generate_random_secret() -> str:
    """
        Generate a random secret key.
    """
    length = random.randint(16, 64)
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(random.choices(chars, k=length))


def generate_random_roles() -> Set[str]:
    """
        Generate a random set of role strings.
    """
    num_roles = random.randint(0, 5)
    return {generate_random_string(1, 15) for _ in range(num_roles)}


def generate_random_permissions() -> Set[str]:
    """
        Generate a random set of permission strings.
    """
    num_permissions = random.randint(0, 5)
    return {generate_random_string(1, 20) for _ in range(num_permissions)}


def generate_random_token() -> str:
    """
        Generate a random opaque token string.
    """
    length = random.randint(20, 100)
    chars = string.ascii_letters + string.digits + "-_"
    return ''.join(random.choices(chars, k=length))


def generate_random_jwt_claims(
    include_exp: bool = True,
    expired: bool = False,
    include_iss: bool = False,
    issuer: Optional[str] = None,
    include_aud: bool = False,
    audience: Optional[str] = None
) -> Dict[str, Any]:
    """
        Generate random JWT claims.
    """
    claims = {
        "sub": generate_random_identifier(),
        "name": generate_random_string(5, 30),
        "iat": int(time.time())
    }
    
    if include_exp:
        if expired:
            # Expired 1 hour ago
            claims["exp"] = int(time.time()) - 3600
        else:
            # Expires in 1 hour
            claims["exp"] = int(time.time()) + 3600
    
    if include_iss:
        claims["iss"] = issuer or generate_random_string(5, 20)
    
    if include_aud:
        claims["aud"] = audience or generate_random_string(5, 20)
    
    # Optionally add roles
    if random.choice([True, False]):
        claims["roles"] = list(generate_random_roles())
    
    return claims


# =============================================================================
# Mock Token Store
# =============================================================================

class MockTokenStore:
    """
        A mock token store for testing BearerAuthenticator.
        
        This store maintains a mapping of token -> claims for validation.
    """
    
    def __init__(self):
        self._tokens: Dict[str, Dict[str, Any]] = {}
    
    def add_token(self, token: str, claims: Dict[str, Any]) -> None:
        """
            Add a token to the store.
        """
        self._tokens[token] = claims
    
    async def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
            Validate a token and return its claims.
        """
        return self._tokens.get(token)
    
    async def store_token(
        self,
        token: str,
        claims: Dict[str, Any],
        expires_in: int
    ) -> None:
        """
            Store a token with its claims.
        """
        self._tokens[token] = claims
    
    async def revoke_token(self, token: str) -> bool:
        """
            Revoke a token.
        """
        if token in self._tokens:
            del self._tokens[token]
            return True
        return False


# =============================================================================
# Mock Request Object
# =============================================================================

class MockRequest:
    """
        A mock HTTP request object for testing.
    """
    
    def __init__(self, headers: Optional[Dict[str, str]] = None):
        self.headers = headers or {}


# =============================================================================
# Helper Functions
# =============================================================================

def run_async(coro):
    """
        Run an async coroutine synchronously for testing.
    """
    return asyncio.run(coro)


# =============================================================================
# Unit Tests for extract_bearer_token
# =============================================================================

def test_extract_bearer_token_valid():
    """
        Test extracting token from valid Bearer header.
    """
    token = extract_bearer_token("Bearer mytoken123")
    
    if token != "mytoken123":
        errmsg = f"Expected 'mytoken123', got '{token}'"
        raise AssertionError(errmsg)
    
    return


def test_extract_bearer_token_case_insensitive():
    """
        Test that Bearer scheme is case-insensitive.
    """
    token = extract_bearer_token("bearer mytoken123")
    
    if token != "mytoken123":
        errmsg = f"Expected 'mytoken123', got '{token}'"
        raise AssertionError(errmsg)
    
    return


def test_extract_bearer_token_with_spaces():
    """
        Test extracting token with leading/trailing spaces.
    """
    token = extract_bearer_token("Bearer   mytoken123  ")
    
    if token != "mytoken123":
        errmsg = f"Expected 'mytoken123', got '{token}'"
        raise AssertionError(errmsg)
    
    return


def test_extract_bearer_token_empty_header():
    """
        Test extracting token from empty header.
    """
    token = extract_bearer_token("")
    
    if token is not None:
        errmsg = f"Expected None for empty header, got '{token}'"
        raise AssertionError(errmsg)
    
    return


def test_extract_bearer_token_no_token():
    """
        Test extracting token when only scheme is present.
    """
    token = extract_bearer_token("Bearer ")
    
    if token is not None:
        errmsg = f"Expected None for missing token, got '{token}'"
        raise AssertionError(errmsg)
    
    return


def test_extract_bearer_token_wrong_scheme():
    """
        Test extracting token with wrong scheme.
    """
    token = extract_bearer_token("Basic dXNlcjpwYXNz")
    
    if token is not None:
        errmsg = f"Expected None for Basic scheme, got '{token}'"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for encode_jwt and decode_jwt
# =============================================================================

def test_encode_decode_jwt_round_trip():
    """
        Test that encoding and decoding a JWT produces the same claims.
    """
    secret = "test-secret-key"
    claims = {
        "sub": "user123",
        "name": "Test User",
        "exp": int(time.time()) + 3600
    }
    
    token = encode_jwt(claims, secret, "HS256")
    decoded = decode_jwt(token, secret, ["HS256"])
    
    if decoded["sub"] != claims["sub"]:
        errmsg = f"Expected sub '{claims['sub']}', got '{decoded['sub']}'"
        raise AssertionError(errmsg)
    
    if decoded["name"] != claims["name"]:
        errmsg = f"Expected name '{claims['name']}', got '{decoded['name']}'"
        raise AssertionError(errmsg)
    
    return


def test_decode_jwt_invalid_signature():
    """
        Test that decoding with wrong secret fails.
    """
    claims = {"sub": "user123", "exp": int(time.time()) + 3600}
    token = encode_jwt(claims, "correct-secret", "HS256")
    
    try:
        decode_jwt(token, "wrong-secret", ["HS256"])
        raise AssertionError("Expected JWTInvalidSignatureError")
    except JWTInvalidSignatureError:
        pass  # Expected
    
    return


def test_decode_jwt_expired():
    """
        Test that decoding expired token fails.
    """
    claims = {"sub": "user123", "exp": int(time.time()) - 3600}  # Expired
    secret = "test-secret"
    token = encode_jwt(claims, secret, "HS256")
    
    try:
        decode_jwt(token, secret, ["HS256"])
        raise AssertionError("Expected JWTExpiredError")
    except JWTExpiredError:
        pass  # Expected
    
    return


def test_decode_jwt_invalid_issuer():
    """
        Test that decoding with wrong issuer fails.
    """
    claims = {"sub": "user123", "iss": "wrong-issuer", "exp": int(time.time()) + 3600}
    secret = "test-secret"
    token = encode_jwt(claims, secret, "HS256")
    
    try:
        decode_jwt(token, secret, ["HS256"], issuer="expected-issuer")
        raise AssertionError("Expected JWTInvalidClaimsError")
    except JWTInvalidClaimsError:
        pass  # Expected
    
    return


def test_decode_jwt_invalid_audience():
    """
        Test that decoding with wrong audience fails.
    """
    claims = {"sub": "user123", "aud": "wrong-audience", "exp": int(time.time()) + 3600}
    secret = "test-secret"
    token = encode_jwt(claims, secret, "HS256")
    
    try:
        decode_jwt(token, secret, ["HS256"], audience="expected-audience")
        raise AssertionError("Expected JWTInvalidClaimsError")
    except JWTInvalidClaimsError:
        pass  # Expected
    
    return


def test_decode_jwt_invalid_format():
    """
        Test that decoding invalid JWT format fails.
    """
    try:
        decode_jwt("not.a.valid.jwt.token", "secret", ["HS256"])
        raise AssertionError("Expected JWTDecodeError")
    except JWTDecodeError:
        pass  # Expected
    
    return


def test_decode_jwt_algorithm_not_allowed():
    """
        Test that decoding with disallowed algorithm fails.
    """
    claims = {"sub": "user123", "exp": int(time.time()) + 3600}
    secret = "test-secret"
    token = encode_jwt(claims, secret, "HS256")
    
    try:
        decode_jwt(token, secret, ["HS512"])  # Only allow HS512
        raise AssertionError("Expected JWTInvalidSignatureError")
    except JWTInvalidSignatureError:
        pass  # Expected
    
    return


# =============================================================================
# Unit Tests for BearerAuthenticator
# =============================================================================

def test_bearer_authenticator_scheme():
    """
        Test that BearerAuthenticator returns "Bearer" as scheme.
    """
    # BearerAuthenticator now requires at least one validation
    # method (jwt_secret or token_store). For the scheme /
    # can_handle tests we pass a placeholder secret since the
    # tests don't exercise the validation path.
    authenticator = BearerAuthenticator(jwt_secret="placeholder")
    
    if authenticator.scheme != "Bearer":
        errmsg = f"Expected scheme 'Bearer', got '{authenticator.scheme}'"
        raise AssertionError(errmsg)
    
    return


def test_bearer_authenticator_can_handle_with_bearer_header():
    """
        Test that can_handle returns True for Bearer auth header.
    """
    # BearerAuthenticator now requires at least one validation
    # method (jwt_secret or token_store). For the scheme /
    # can_handle tests we pass a placeholder secret since the
    # tests don't exercise the validation path.
    authenticator = BearerAuthenticator(jwt_secret="placeholder")
    request = MockRequest(headers={"Authorization": "Bearer token123"})
    
    if not authenticator.can_handle(request):
        errmsg = "Expected can_handle to return True for Bearer auth header"
        raise AssertionError(errmsg)
    
    return


def test_bearer_authenticator_can_handle_case_insensitive():
    """
        Test that can_handle is case-insensitive for scheme.
    """
    # BearerAuthenticator now requires at least one validation
    # method (jwt_secret or token_store). For the scheme /
    # can_handle tests we pass a placeholder secret since the
    # tests don't exercise the validation path.
    authenticator = BearerAuthenticator(jwt_secret="placeholder")
    request = MockRequest(headers={"Authorization": "bearer token123"})
    
    if not authenticator.can_handle(request):
        errmsg = "Expected can_handle to return True for lowercase 'bearer'"
        raise AssertionError(errmsg)
    
    return


def test_bearer_authenticator_can_handle_without_header():
    """
        Test that can_handle returns False when no Authorization header.
    """
    # BearerAuthenticator now requires at least one validation
    # method (jwt_secret or token_store). For the scheme /
    # can_handle tests we pass a placeholder secret since the
    # tests don't exercise the validation path.
    authenticator = BearerAuthenticator(jwt_secret="placeholder")
    request = MockRequest(headers={})
    
    if authenticator.can_handle(request):
        errmsg = "Expected can_handle to return False without Authorization header"
        raise AssertionError(errmsg)
    
    return


def test_bearer_authenticator_can_handle_with_basic_header():
    """
        Test that can_handle returns False for Basic auth header.
    """
    # BearerAuthenticator now requires at least one validation
    # method (jwt_secret or token_store). For the scheme /
    # can_handle tests we pass a placeholder secret since the
    # tests don't exercise the validation path.
    authenticator = BearerAuthenticator(jwt_secret="placeholder")
    request = MockRequest(headers={"Authorization": "Basic dXNlcjpwYXNz"})
    
    if authenticator.can_handle(request):
        errmsg = "Expected can_handle to return False for Basic auth header"
        raise AssertionError(errmsg)
    
    return


def test_bearer_authenticator_authenticate_valid_jwt():
    """
        Test authentication with valid JWT token.
    """
    secret = "test-secret-key"
    claims = {
        "sub": "user123",
        "name": "Test User",
        "exp": int(time.time()) + 3600
    }
    token = encode_jwt(claims, secret, "HS256")
    
    authenticator = BearerAuthenticator(jwt_secret=secret)
    request = MockRequest(headers={"Authorization": f"Bearer {token}"})
    
    result = run_async(authenticator.authenticate(request))
    
    if result.status != AuthenticationStatus.SUCCESS:
        errmsg = f"Expected SUCCESS status, got {result.status}"
        raise AssertionError(errmsg)
    
    if result.context is None:
        errmsg = "Expected context to be present on success"
        raise AssertionError(errmsg)
    
    if result.context.principal.identifier != "user123":
        errmsg = f"Expected principal identifier 'user123', got '{result.context.principal.identifier}'"
        raise AssertionError(errmsg)
    
    if result.context.scheme != "Bearer":
        errmsg = f"Expected scheme 'Bearer', got '{result.context.scheme}'"
        raise AssertionError(errmsg)
    
    return


def test_bearer_authenticator_authenticate_expired_jwt():
    """
        Test authentication with expired JWT token.
    """
    secret = "test-secret-key"
    claims = {
        "sub": "user123",
        "exp": int(time.time()) - 3600  # Expired
    }
    token = encode_jwt(claims, secret, "HS256")
    
    authenticator = BearerAuthenticator(jwt_secret=secret)
    request = MockRequest(headers={"Authorization": f"Bearer {token}"})
    
    result = run_async(authenticator.authenticate(request))
    
    if result.status != AuthenticationStatus.FAILURE:
        errmsg = f"Expected FAILURE status, got {result.status}"
        raise AssertionError(errmsg)
    
    if result.error_code != "invalid_token":
        errmsg = f"Expected error_code 'invalid_token', got '{result.error_code}'"
        raise AssertionError(errmsg)
    
    if "expired" not in result.error_description.lower():
        errmsg = f"Expected 'expired' in error description, got '{result.error_description}'"
        raise AssertionError(errmsg)
    
    return


def test_bearer_authenticator_authenticate_invalid_signature():
    """
        Test authentication with invalid JWT signature.
    """
    claims = {"sub": "user123", "exp": int(time.time()) + 3600}
    token = encode_jwt(claims, "wrong-secret", "HS256")
    
    authenticator = BearerAuthenticator(jwt_secret="correct-secret")
    request = MockRequest(headers={"Authorization": f"Bearer {token}"})
    
    result = run_async(authenticator.authenticate(request))
    
    if result.status != AuthenticationStatus.FAILURE:
        errmsg = f"Expected FAILURE status, got {result.status}"
        raise AssertionError(errmsg)
    
    if result.error_code != "invalid_token":
        errmsg = f"Expected error_code 'invalid_token', got '{result.error_code}'"
        raise AssertionError(errmsg)
    
    return


def test_bearer_authenticator_authenticate_with_token_store():
    """
        Test authentication with token store.
    """
    token_store = MockTokenStore()
    token = "opaque-token-123"
    claims = {"sub": "user456", "name": "Token User"}
    token_store.add_token(token, claims)
    
    authenticator = BearerAuthenticator(token_store=token_store)
    request = MockRequest(headers={"Authorization": f"Bearer {token}"})
    
    result = run_async(authenticator.authenticate(request))
    
    if result.status != AuthenticationStatus.SUCCESS:
        errmsg = f"Expected SUCCESS status, got {result.status}"
        raise AssertionError(errmsg)
    
    if result.context.principal.identifier != "user456":
        errmsg = f"Expected principal identifier 'user456', got '{result.context.principal.identifier}'"
        raise AssertionError(errmsg)
    
    return


def test_bearer_authenticator_authenticate_invalid_token_store():
    """
        Test authentication with invalid token in token store.
    """
    token_store = MockTokenStore()
    # Don't add the token to the store
    
    authenticator = BearerAuthenticator(token_store=token_store)
    request = MockRequest(headers={"Authorization": "Bearer invalid-token"})
    
    result = run_async(authenticator.authenticate(request))
    
    if result.status != AuthenticationStatus.FAILURE:
        errmsg = f"Expected FAILURE status, got {result.status}"
        raise AssertionError(errmsg)
    
    if result.error_code != "invalid_token":
        errmsg = f"Expected error_code 'invalid_token', got '{result.error_code}'"
        raise AssertionError(errmsg)
    
    return


def test_bearer_authenticator_authenticate_no_header():
    """
        Test authentication without Authorization header returns SKIP.
    """
    authenticator = BearerAuthenticator(jwt_secret="secret")
    request = MockRequest(headers={})
    
    result = run_async(authenticator.authenticate(request))
    
    if result.status != AuthenticationStatus.SKIP:
        errmsg = f"Expected SKIP status, got {result.status}"
        raise AssertionError(errmsg)
    
    return


def test_bearer_authenticator_authenticate_basic_header_skips():
    """
        Test that Basic auth header results in SKIP status.
    """
    authenticator = BearerAuthenticator(jwt_secret="secret")
    request = MockRequest(headers={"Authorization": "Basic dXNlcjpwYXNz"})
    
    result = run_async(authenticator.authenticate(request))
    
    if result.status != AuthenticationStatus.SKIP:
        errmsg = f"Expected SKIP status for Basic header, got {result.status}"
        raise AssertionError(errmsg)
    
    return


def test_bearer_authenticator_jwt_with_issuer_validation():
    """
        Test JWT validation with issuer claim.
    """
    secret = "test-secret"
    claims = {
        "sub": "user123",
        "iss": "my-app",
        "exp": int(time.time()) + 3600
    }
    token = encode_jwt(claims, secret, "HS256")
    
    authenticator = BearerAuthenticator(jwt_secret=secret, jwt_issuer="my-app")
    request = MockRequest(headers={"Authorization": f"Bearer {token}"})
    
    result = run_async(authenticator.authenticate(request))
    
    if result.status != AuthenticationStatus.SUCCESS:
        errmsg = f"Expected SUCCESS status, got {result.status}"
        raise AssertionError(errmsg)
    
    return


def test_bearer_authenticator_jwt_with_wrong_issuer():
    """
        Test JWT validation fails with wrong issuer.
    """
    secret = "test-secret"
    claims = {
        "sub": "user123",
        "iss": "wrong-app",
        "exp": int(time.time()) + 3600
    }
    token = encode_jwt(claims, secret, "HS256")
    
    authenticator = BearerAuthenticator(jwt_secret=secret, jwt_issuer="my-app")
    request = MockRequest(headers={"Authorization": f"Bearer {token}"})
    
    result = run_async(authenticator.authenticate(request))
    
    if result.status != AuthenticationStatus.FAILURE:
        errmsg = f"Expected FAILURE status, got {result.status}"
        raise AssertionError(errmsg)
    
    return


def test_bearer_authenticator_jwt_fallback_to_token_store():
    """
        Test that non-JWT token falls back to token store.
    """
    token_store = MockTokenStore()
    opaque_token = "not-a-jwt-token"
    claims = {"sub": "user789"}
    token_store.add_token(opaque_token, claims)
    
    # Configure both JWT and token store
    authenticator = BearerAuthenticator(
        jwt_secret="secret",
        token_store=token_store
    )
    request = MockRequest(headers={"Authorization": f"Bearer {opaque_token}"})
    
    result = run_async(authenticator.authenticate(request))
    
    if result.status != AuthenticationStatus.SUCCESS:
        errmsg = f"Expected SUCCESS status with token store fallback, got {result.status}"
        raise AssertionError(errmsg)
    
    if result.context.principal.identifier != "user789":
        errmsg = f"Expected principal identifier 'user789', got '{result.context.principal.identifier}'"
        raise AssertionError(errmsg)
    
    return


def test_bearer_authenticator_with_dict_request():
    """
        Test that BearerAuthenticator works with dict-style request.
    """
    secret = "test-secret"
    claims = {"sub": "user123", "exp": int(time.time()) + 3600}
    token = encode_jwt(claims, secret, "HS256")
    
    authenticator = BearerAuthenticator(jwt_secret=secret)
    request = {"headers": {"Authorization": f"Bearer {token}"}}
    
    result = run_async(authenticator.authenticate(request))
    
    if result.status != AuthenticationStatus.SUCCESS:
        errmsg = f"Expected SUCCESS status with dict request, got {result.status}"
        raise AssertionError(errmsg)
    
    return


def test_bearer_authenticator_jwt_with_roles():
    """
        Test that JWT roles are extracted into Principal.
    """
    secret = "test-secret"
    claims = {
        "sub": "user123",
        "roles": ["admin", "user"],
        "exp": int(time.time()) + 3600
    }
    token = encode_jwt(claims, secret, "HS256")
    
    authenticator = BearerAuthenticator(jwt_secret=secret)
    request = MockRequest(headers={"Authorization": f"Bearer {token}"})
    
    result = run_async(authenticator.authenticate(request))
    
    if result.status != AuthenticationStatus.SUCCESS:
        errmsg = f"Expected SUCCESS status, got {result.status}"
        raise AssertionError(errmsg)
    
    expected_roles = {"admin", "user"}
    if result.context.principal.roles != expected_roles:
        errmsg = f"Expected roles {expected_roles}, got {result.context.principal.roles}"
        raise AssertionError(errmsg)
    
    return




# =============================================================================
# Property-Based Tests
# =============================================================================

# Feature: authentication, Property 10: Bearer Token Extraction
# *For any* request with an Authorization header of form "Bearer {token}",
# the Bearer_Authenticator SHALL extract exactly the token portion.
# **Validates: Requirements 4.1**

def test_property_10_bearer_token_extraction():
    """
        Property 10: Bearer Token Extraction
        
        For any request with an Authorization header of form "Bearer {token}",
        the Bearer_Authenticator SHALL extract exactly the token portion.
        
        **Validates: Requirements 4.1**
    """
    # Run 100 iterations with random data
    for iteration in range(100):
        # Generate a random token
        original_token = generate_random_token()
        
        # Create Authorization header
        auth_header = f"Bearer {original_token}"
        
        # Extract token using the utility function
        extracted_token = extract_bearer_token(auth_header)
        
        # Property: Extracted token must match original
        if extracted_token != original_token:
            errmsg = f"Iteration {iteration}: Token mismatch. Expected '{original_token}', got '{extracted_token}'"
            raise AssertionError(errmsg)
        
        # Also test case-insensitive scheme
        auth_header_lower = f"bearer {original_token}"
        extracted_lower = extract_bearer_token(auth_header_lower)
        
        if extracted_lower != original_token:
            errmsg = f"Iteration {iteration}: Token mismatch with lowercase scheme. Expected '{original_token}', got '{extracted_lower}'"
            raise AssertionError(errmsg)
        
        # Test with BEARER uppercase
        auth_header_upper = f"BEARER {original_token}"
        extracted_upper = extract_bearer_token(auth_header_upper)
        
        if extracted_upper != original_token:
            errmsg = f"Iteration {iteration}: Token mismatch with uppercase scheme. Expected '{original_token}', got '{extracted_upper}'"
            raise AssertionError(errmsg)
    
    return


# Feature: authentication, Property 11: JWT Validation Rejects Invalid Tokens
# *For any* JWT token with an invalid signature, expired timestamp, or
# mismatched issuer, the Bearer_Authenticator SHALL return FAILURE with
# error_code="invalid_token".
# **Validates: Requirements 4.4, 4.6, 4.7**

def test_property_11_jwt_validation_rejects_invalid_tokens():
    """
        Property 11: JWT Validation Rejects Invalid Tokens
        
        For any JWT token with an invalid signature, expired timestamp, or
        mismatched issuer, the Bearer_Authenticator SHALL return FAILURE
        with error_code="invalid_token".
        
        **Validates: Requirements 4.4, 4.6, 4.7**
    """
    correct_secret = "correct-secret-key"
    wrong_secret = "wrong-secret-key"
    correct_issuer = "correct-issuer"
    wrong_issuer = "wrong-issuer"
    
    # Run 100 iterations with random invalid tokens
    for iteration in range(100):
        # Randomly choose type of invalid token
        invalid_type = random.choice([
            "invalid_signature",
            "expired",
            "wrong_issuer"
        ])
        
        if invalid_type == "invalid_signature":
            # Create token with wrong secret
            claims = generate_random_jwt_claims()
            token = encode_jwt(claims, wrong_secret, "HS256")
            authenticator = BearerAuthenticator(jwt_secret=correct_secret)
            
        elif invalid_type == "expired":
            # Create expired token
            claims = generate_random_jwt_claims(include_exp=True, expired=True)
            token = encode_jwt(claims, correct_secret, "HS256")
            authenticator = BearerAuthenticator(jwt_secret=correct_secret)
            
        else:  # wrong_issuer
            # Create token with wrong issuer
            claims = generate_random_jwt_claims(include_iss=True, issuer=wrong_issuer)
            token = encode_jwt(claims, correct_secret, "HS256")
            authenticator = BearerAuthenticator(
                jwt_secret=correct_secret,
                jwt_issuer=correct_issuer
            )
        
        request = MockRequest(headers={"Authorization": f"Bearer {token}"})
        result = run_async(authenticator.authenticate(request))
        
        # Property: Status must be FAILURE
        if result.status != AuthenticationStatus.FAILURE:
            errmsg = f"Iteration {iteration} ({invalid_type}): Expected FAILURE status, got {result.status}"
            raise AssertionError(errmsg)
        
        # Property: Error code must be invalid_token
        if result.error_code != "invalid_token":
            errmsg = f"Iteration {iteration} ({invalid_type}): Expected error_code 'invalid_token', got '{result.error_code}'"
            raise AssertionError(errmsg)
        
        # Property: Context must NOT be present
        if result.context is not None:
            errmsg = f"Iteration {iteration} ({invalid_type}): Expected no context on failure"
            raise AssertionError(errmsg)
    
    return


# Feature: authentication, Property 12: Valid JWT Produces Context with Claims
# *For any* valid JWT token, the Bearer_Authenticator SHALL return SUCCESS
# with an Authentication_Context where the Principal identifier equals the
# "sub" claim and attributes contain all token claims.
# **Validates: Requirements 4.5**

def test_property_12_valid_jwt_produces_context_with_claims():
    """
        Property 12: Valid JWT Produces Context with Claims
        
        For any valid JWT token, the Bearer_Authenticator SHALL return SUCCESS
        with an Authentication_Context where the Principal identifier equals
        the "sub" claim and attributes contain all token claims.
        
        **Validates: Requirements 4.5**
    """
    secret = "test-secret-key"
    
    # Run 100 iterations with random valid tokens
    for iteration in range(100):
        # Generate random claims
        claims = generate_random_jwt_claims()
        original_sub = claims["sub"]
        original_name = claims.get("name")
        original_roles = claims.get("roles", [])
        
        # Create valid token
        token = encode_jwt(claims, secret, "HS256")
        
        authenticator = BearerAuthenticator(jwt_secret=secret)
        request = MockRequest(headers={"Authorization": f"Bearer {token}"})
        
        result = run_async(authenticator.authenticate(request))
        
        # Property: Status must be SUCCESS
        if result.status != AuthenticationStatus.SUCCESS:
            errmsg = f"Iteration {iteration}: Expected SUCCESS status, got {result.status}"
            raise AssertionError(errmsg)
        
        # Property: Context must be present
        if result.context is None:
            errmsg = f"Iteration {iteration}: Expected context to be present on success"
            raise AssertionError(errmsg)
        
        # Property: Principal identifier must equal "sub" claim
        if result.context.principal.identifier != original_sub:
            errmsg = f"Iteration {iteration}: Expected principal identifier '{original_sub}', got '{result.context.principal.identifier}'"
            raise AssertionError(errmsg)
        
        # Property: Scheme must be "Bearer"
        if result.context.scheme != "Bearer":
            errmsg = f"Iteration {iteration}: Expected scheme 'Bearer', got '{result.context.scheme}'"
            raise AssertionError(errmsg)
        
        # Property: Attributes must contain all original claims
        for key, value in claims.items():
            if key not in result.context.attributes:
                errmsg = f"Iteration {iteration}: Expected claim '{key}' in attributes"
                raise AssertionError(errmsg)
            if result.context.attributes[key] != value:
                errmsg = f"Iteration {iteration}: Expected attribute '{key}' = '{value}', got '{result.context.attributes[key]}'"
                raise AssertionError(errmsg)
        
        # Property: Principal roles must match "roles" claim
        expected_roles = set(original_roles)
        if result.context.principal.roles != expected_roles:
            errmsg = f"Iteration {iteration}: Expected roles {expected_roles}, got {result.context.principal.roles}"
            raise AssertionError(errmsg)
        
        # Property: Principal display_name must match "name" claim
        if original_name is not None:
            if result.context.principal.display_name != original_name:
                errmsg = f"Iteration {iteration}: Expected display_name '{original_name}', got '{result.context.principal.display_name}'"
                raise AssertionError(errmsg)
    
    return


# =============================================================================
# Regression Tests for BUG-7
# =============================================================================

def test_bearer_jwt_expiry_is_timezone_aware():
    """
        Regression test for BUG-7: BearerAuthenticator must produce a
        timezone-aware expires_at datetime from the JWT exp claim. A naive
        datetime.fromtimestamp() would create a timezone-unaware value that
        causes TypeError when compared with timezone-aware datetimes.
    """
    secret = "tz-regression-secret"
    claims = {
        "sub": "user-tz-test",
        "name": "TZ Regression",
        "exp": int(time.time()) + 3600
    }
    token = encode_jwt(claims, secret, "HS256")

    authenticator = BearerAuthenticator(jwt_secret=secret)
    request = MockRequest(headers={"Authorization": f"Bearer {token}"})

    result = run_async(authenticator.authenticate(request))

    if result.status != AuthenticationStatus.SUCCESS:
        errmsg = f"BUG-7 regression: Expected SUCCESS, got {result.status}"
        raise AssertionError(errmsg)

    if result.context is None:
        errmsg = "BUG-7 regression: Expected context, got None"
        raise AssertionError(errmsg)

    if result.context.expires_at is None:
        errmsg = "BUG-7 regression: Expected expires_at, got None"
        raise AssertionError(errmsg)

    if result.context.expires_at.tzinfo is None:
        errmsg = (
            "BUG-7 regression: expires_at must be timezone-aware, "
            f"got tzinfo=None for {result.context.expires_at!r}"
        )
        raise AssertionError(errmsg)

    return


# =============================================================================
# Constructor validation: must supply at least one validation method
# =============================================================================

def test_bearer_authenticator_rejects_no_validation_method_at_construction():
    """
        Property: BearerAuthenticator() with neither
        ``token_store`` nor ``jwt_secret`` raises ValueError at
        construction time. An authenticator with neither cannot
        validate any token and would silently reject every Bearer
        request — a footgun configuration that should fail
        loudly instead of mid-request.
    """
    raised = False
    try:
        BearerAuthenticator()
    except ValueError:
        raised = True

    if raised is not True:
        errmsg = (
            "Expected ValueError when constructing "
            "BearerAuthenticator() with no validation method, "
            "but no exception was raised."
        )
        raise AssertionError(errmsg)

    return


def test_bearer_authenticator_accepts_jwt_secret_only():
    """
        Property: BearerAuthenticator(jwt_secret=...) is valid
        construction (JWT-only deployment).
    """
    authenticator = BearerAuthenticator(jwt_secret="any-secret")
    if authenticator is None:
        errmsg = "Constructor returned None"
        raise AssertionError(errmsg)
    return


def test_bearer_authenticator_accepts_token_store_only():
    """
        Property: BearerAuthenticator(token_store=...) is valid
        construction (opaque-token-only deployment).
    """
    class _StubTokenStore:
        async def validate_token(self, token):
            return None

    authenticator = BearerAuthenticator(token_store=_StubTokenStore())
    if authenticator is None:
        errmsg = "Constructor returned None"
        raise AssertionError(errmsg)
    return


def test_bearer_authenticator_accepts_both_validation_methods():
    """
        Property: BearerAuthenticator(token_store=..., jwt_secret=...)
        is valid construction (hybrid deployment with JWT primary
        + opaque fallback).
    """
    class _StubTokenStore:
        async def validate_token(self, token):
            return None

    authenticator = BearerAuthenticator(
        token_store=_StubTokenStore(),
        jwt_secret="any-secret",
    )
    if authenticator is None:
        errmsg = "Constructor returned None"
        raise AssertionError(errmsg)
    return
