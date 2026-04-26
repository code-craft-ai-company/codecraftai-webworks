"""
    Tests for the DigestAuthenticator module.
    
    This module contains unit tests and property-based tests for the
    DigestAuthenticator class and related utility functions.
"""

import asyncio
import hashlib
import random
import re
import secrets
import string
import time
from typing import Any, Dict, Optional, Set

from automojo.webworks.authentication import (
    AuthenticationStatus,
    AuthenticationResult,
    Principal,
    AuthenticationContext,
    DigestAlgorithm,
    DigestAuthenticator,
    DigestCredentials,
    NonceStore,
    compute_digest_response,
    compute_ha1,
    create_digest_auth_header
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


def generate_random_username() -> str:
    """
        Generate a random username (alphanumeric).
    """
    length = random.randint(1, 30)
    chars = string.ascii_letters + string.digits + "_-."
    return ''.join(random.choices(chars, k=length))


def generate_random_password() -> str:
    """
        Generate a random password.
    """
    length = random.randint(1, 50)
    chars = string.ascii_letters + string.digits + "!@#$%^&*()-_=+[]{}|;',.<>?"
    return ''.join(random.choices(chars, k=length))


def generate_random_realm() -> str:
    """
        Generate a random realm string.
    """
    length = random.randint(1, 30)
    chars = string.ascii_letters + string.digits + " _-."
    return ''.join(random.choices(chars, k=length))


def generate_random_uri() -> str:
    """
        Generate a random URI path.
    """
    segments = random.randint(1, 5)
    parts = [generate_random_string(1, 15) for _ in range(segments)]
    return "/" + "/".join(parts)


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


# =============================================================================
# Mock Identity Provider
# =============================================================================

class MockDigestIdentityProvider:
    """
        A mock identity provider for testing DigestAuthenticator.
        
        This provider stores a mapping of (username, realm) -> (ha1, Principal)
        and validates credentials against this mapping.
    """
    
    def __init__(self):
        self._credentials: Dict[tuple, tuple] = {}
    
    def add_user(
        self,
        username: str,
        realm: str,
        password: str,
        display_name: Optional[str] = None,
        roles: Optional[Set[str]] = None,
        permissions: Optional[Set[str]] = None
    ) -> Principal:
        """
            Add a user to the identity provider.
            
            :returns: The created Principal.
        """
        principal = Principal(
            identifier=username,
            display_name=display_name or username,
            roles=roles or set(),
            permissions=permissions or set()
        )
        
        # Compute HA1 for both MD5 and SHA-256
        ha1_md5 = compute_ha1(username, realm, password, "MD5")
        ha1_sha256 = compute_ha1(username, realm, password, "SHA-256")
        
        self._credentials[(username, realm)] = (ha1_md5, ha1_sha256, principal)
        return principal
    
    async def get_ha1(
        self,
        username: str,
        realm: str,
        algorithm: str
    ) -> Optional[str]:
        """
            Get the HA1 hash for a user.
        """
        key = (username, realm)
        if key not in self._credentials:
            return None
        
        ha1_md5, ha1_sha256, _ = self._credentials[key]
        
        if algorithm.upper() == "SHA-256":
            return ha1_sha256
        return ha1_md5
    
    async def get_principal(
        self,
        username: str,
        realm: str
    ) -> Optional[Principal]:
        """
            Retrieve a principal by username and realm.
        """
        key = (username, realm)
        if key not in self._credentials:
            return None
        
        _, _, principal = self._credentials[key]
        return principal


# =============================================================================
# Mock Request Object
# =============================================================================

class MockRequest:
    """
        A mock HTTP request object for testing.
    """
    
    def __init__(
        self,
        headers: Optional[Dict[str, str]] = None,
        method: str = "GET"
    ):
        self.headers = headers or {}
        self.method = method


# =============================================================================
# Helper Functions
# =============================================================================

def run_async(coro):
    """
        Run an async coroutine synchronously for testing.
    """
    return asyncio.get_event_loop().run_until_complete(coro)


def extract_nonce_from_challenge(challenge: str) -> Optional[str]:
    """
        Extract the nonce value from a WWW-Authenticate challenge.
    """
    match = re.search(r'nonce="([^"]+)"', challenge)
    if match:
        return match.group(1)
    return None


def extract_realm_from_challenge(challenge: str) -> Optional[str]:
    """
        Extract the realm value from a WWW-Authenticate challenge.
    """
    match = re.search(r'realm="([^"]+)"', challenge)
    if match:
        return match.group(1)
    return None


def extract_algorithm_from_challenge(challenge: str) -> Optional[str]:
    """
        Extract the algorithm value from a WWW-Authenticate challenge.
    """
    match = re.search(r'algorithm=(\S+?)(?:,|$)', challenge)
    if match:
        return match.group(1)
    return None


def extract_qop_from_challenge(challenge: str) -> Optional[str]:
    """
        Extract the qop value from a WWW-Authenticate challenge.
    """
    match = re.search(r'qop="([^"]+)"', challenge)
    if match:
        return match.group(1)
    return None


def extract_opaque_from_challenge(challenge: str) -> Optional[str]:
    """
        Extract the opaque value from a WWW-Authenticate challenge.
    """
    match = re.search(r'opaque="([^"]+)"', challenge)
    if match:
        return match.group(1)
    return None


def extract_stale_from_challenge(challenge: str) -> bool:
    """
        Check if stale=true is present in the challenge.
    """
    return "stale=true" in challenge.lower()


# =============================================================================
# Unit Tests for compute_ha1
# =============================================================================

def test_compute_ha1_md5():
    """
        Test computing HA1 with MD5 algorithm.
    """
    ha1 = compute_ha1("user", "realm", "password", "MD5")
    
    # Verify it's a valid MD5 hex string (32 characters)
    if len(ha1) != 32:
        errmsg = f"Expected 32 character MD5 hash, got {len(ha1)} characters"
        raise AssertionError(errmsg)
    
    # Verify it matches expected value
    expected = hashlib.md5(b"user:realm:password").hexdigest()
    if ha1 != expected:
        errmsg = f"Expected '{expected}', got '{ha1}'"
        raise AssertionError(errmsg)
    
    return


def test_compute_ha1_sha256():
    """
        Test computing HA1 with SHA-256 algorithm.
    """
    ha1 = compute_ha1("user", "realm", "password", "SHA-256")
    
    # Verify it's a valid SHA-256 hex string (64 characters)
    if len(ha1) != 64:
        errmsg = f"Expected 64 character SHA-256 hash, got {len(ha1)} characters"
        raise AssertionError(errmsg)
    
    # Verify it matches expected value
    expected = hashlib.sha256(b"user:realm:password").hexdigest()
    if ha1 != expected:
        errmsg = f"Expected '{expected}', got '{ha1}'"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for NonceStore
# =============================================================================

def test_nonce_store_create_nonce():
    """
        Test that NonceStore creates unique nonces.
    """
    store = NonceStore()
    
    nonce1 = store.create_nonce()
    nonce2 = store.create_nonce()
    
    if nonce1 == nonce2:
        errmsg = "Expected unique nonces, got duplicates"
        raise AssertionError(errmsg)
    
    return


def test_nonce_store_validate_fresh_nonce():
    """
        Test that fresh nonces are valid.
    """
    store = NonceStore(max_age_seconds=300.0)
    
    nonce = store.create_nonce()
    is_valid, is_stale = store.validate_nonce(nonce)
    
    if not is_valid:
        errmsg = "Expected fresh nonce to be valid"
        raise AssertionError(errmsg)
    
    if is_stale:
        errmsg = "Expected fresh nonce to not be stale"
        raise AssertionError(errmsg)
    
    return


def test_nonce_store_validate_unknown_nonce():
    """
        Test that unknown nonces are invalid.
    """
    store = NonceStore()
    
    is_valid, is_stale = store.validate_nonce("unknown-nonce")
    
    if is_valid:
        errmsg = "Expected unknown nonce to be invalid"
        raise AssertionError(errmsg)
    
    if is_stale:
        errmsg = "Expected unknown nonce to not be stale"
        raise AssertionError(errmsg)
    
    return


def test_nonce_store_increment_count():
    """
        Test nonce count incrementing.
    """
    store = NonceStore()
    
    nonce = store.create_nonce()
    
    count1 = store.increment_count(nonce)
    count2 = store.increment_count(nonce)
    count3 = store.increment_count(nonce)
    
    if count1 != 1:
        errmsg = f"Expected count 1, got {count1}"
        raise AssertionError(errmsg)
    
    if count2 != 2:
        errmsg = f"Expected count 2, got {count2}"
        raise AssertionError(errmsg)
    
    if count3 != 3:
        errmsg = f"Expected count 3, got {count3}"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for DigestAuthenticator
# =============================================================================

def test_digest_authenticator_scheme():
    """
        Test that DigestAuthenticator returns "Digest" as scheme.
    """
    provider = MockDigestIdentityProvider()
    authenticator = DigestAuthenticator(provider)
    
    if authenticator.scheme != "Digest":
        errmsg = f"Expected scheme 'Digest', got '{authenticator.scheme}'"
        raise AssertionError(errmsg)
    
    return


def test_digest_authenticator_default_realm():
    """
        Test that DigestAuthenticator has default realm "Restricted".
    """
    provider = MockDigestIdentityProvider()
    authenticator = DigestAuthenticator(provider)
    
    if authenticator.realm != "Restricted":
        errmsg = f"Expected realm 'Restricted', got '{authenticator.realm}'"
        raise AssertionError(errmsg)
    
    return


def test_digest_authenticator_custom_realm():
    """
        Test that DigestAuthenticator accepts custom realm.
    """
    provider = MockDigestIdentityProvider()
    authenticator = DigestAuthenticator(provider, realm="MyApp")
    
    if authenticator.realm != "MyApp":
        errmsg = f"Expected realm 'MyApp', got '{authenticator.realm}'"
        raise AssertionError(errmsg)
    
    return


def test_digest_authenticator_can_handle_with_digest_header():
    """
        Test that can_handle returns True for Digest auth header.
    """
    provider = MockDigestIdentityProvider()
    authenticator = DigestAuthenticator(provider)
    
    request = MockRequest(headers={"Authorization": "Digest username=\"user\""})
    
    if not authenticator.can_handle(request):
        errmsg = "Expected can_handle to return True for Digest auth header"
        raise AssertionError(errmsg)
    
    return


def test_digest_authenticator_can_handle_case_insensitive():
    """
        Test that can_handle is case-insensitive for scheme.
    """
    provider = MockDigestIdentityProvider()
    authenticator = DigestAuthenticator(provider)
    
    request = MockRequest(headers={"Authorization": "digest username=\"user\""})
    
    if not authenticator.can_handle(request):
        errmsg = "Expected can_handle to return True for lowercase 'digest'"
        raise AssertionError(errmsg)
    
    return


def test_digest_authenticator_can_handle_without_header():
    """
        Test that can_handle returns False when no Authorization header.
    """
    provider = MockDigestIdentityProvider()
    authenticator = DigestAuthenticator(provider)
    
    request = MockRequest(headers={})
    
    if authenticator.can_handle(request):
        errmsg = "Expected can_handle to return False without Authorization header"
        raise AssertionError(errmsg)
    
    return


def test_digest_authenticator_can_handle_with_basic_header():
    """
        Test that can_handle returns False for Basic auth header.
    """
    provider = MockDigestIdentityProvider()
    authenticator = DigestAuthenticator(provider)
    
    request = MockRequest(headers={"Authorization": "Basic dXNlcjpwYXNz"})
    
    if authenticator.can_handle(request):
        errmsg = "Expected can_handle to return False for Basic auth header"
        raise AssertionError(errmsg)
    
    return


def test_digest_authenticator_challenge_on_no_header():
    """
        Test that missing Authorization header returns challenge.
    """
    provider = MockDigestIdentityProvider()
    authenticator = DigestAuthenticator(provider, realm="TestRealm")
    
    request = MockRequest(headers={})
    
    result = run_async(authenticator.authenticate(request))
    
    if result.status != AuthenticationStatus.CHALLENGE:
        errmsg = f"Expected CHALLENGE status, got {result.status}"
        raise AssertionError(errmsg)
    
    if result.challenge is None:
        errmsg = "Expected challenge to be present"
        raise AssertionError(errmsg)
    
    if not result.challenge.startswith("Digest "):
        errmsg = f"Expected challenge to start with 'Digest ', got '{result.challenge}'"
        raise AssertionError(errmsg)
    
    return


def test_digest_authenticator_challenge_contains_realm():
    """
        Test that challenge contains the configured realm.
    """
    provider = MockDigestIdentityProvider()
    authenticator = DigestAuthenticator(provider, realm="TestRealm")
    
    request = MockRequest(headers={})
    
    result = run_async(authenticator.authenticate(request))
    
    realm = extract_realm_from_challenge(result.challenge)
    if realm != "TestRealm":
        errmsg = f"Expected realm 'TestRealm' in challenge, got '{realm}'"
        raise AssertionError(errmsg)
    
    return


def test_digest_authenticator_challenge_contains_nonce():
    """
        Test that challenge contains a nonce.
    """
    provider = MockDigestIdentityProvider()
    authenticator = DigestAuthenticator(provider)
    
    request = MockRequest(headers={})
    
    result = run_async(authenticator.authenticate(request))
    
    nonce = extract_nonce_from_challenge(result.challenge)
    if nonce is None or nonce == "":
        errmsg = "Expected non-empty nonce in challenge"
        raise AssertionError(errmsg)
    
    return


def test_digest_authenticator_challenge_contains_algorithm():
    """
        Test that challenge contains the algorithm.
    """
    provider = MockDigestIdentityProvider()
    authenticator = DigestAuthenticator(provider, algorithm=DigestAlgorithm.SHA256)
    
    request = MockRequest(headers={})
    
    result = run_async(authenticator.authenticate(request))
    
    algorithm = extract_algorithm_from_challenge(result.challenge)
    if algorithm != "SHA-256":
        errmsg = f"Expected algorithm 'SHA-256' in challenge, got '{algorithm}'"
        raise AssertionError(errmsg)
    
    return


def test_digest_authenticator_valid_credentials():
    """
        Test authentication with valid credentials.
    """
    realm = "TestRealm"
    username = "testuser"
    password = "testpass"
    uri = "/protected/resource"
    method = "GET"
    
    provider = MockDigestIdentityProvider()
    provider.add_user(username, realm, password, display_name="Test User")
    authenticator = DigestAuthenticator(provider, realm=realm)
    
    # First, get a challenge to obtain a valid nonce
    request1 = MockRequest(headers={})
    result1 = run_async(authenticator.authenticate(request1))
    
    nonce = extract_nonce_from_challenge(result1.challenge)
    opaque = extract_opaque_from_challenge(result1.challenge)
    
    # Compute the response
    response = compute_digest_response(
        username=username,
        realm=realm,
        password=password,
        nonce=nonce,
        uri=uri,
        method=method,
        algorithm="MD5"
    )
    
    # Create authorization header
    auth_header = create_digest_auth_header(
        username=username,
        realm=realm,
        nonce=nonce,
        uri=uri,
        response=response,
        algorithm="MD5",
        opaque=opaque
    )
    
    request2 = MockRequest(headers={"Authorization": auth_header}, method=method)
    result2 = run_async(authenticator.authenticate(request2))
    
    if result2.status != AuthenticationStatus.SUCCESS:
        errmsg = f"Expected SUCCESS status, got {result2.status}"
        raise AssertionError(errmsg)
    
    if result2.context is None:
        errmsg = "Expected context to be present on success"
        raise AssertionError(errmsg)
    
    if result2.context.principal.identifier != username:
        errmsg = f"Expected principal identifier '{username}', got '{result2.context.principal.identifier}'"
        raise AssertionError(errmsg)
    
    return


def test_digest_authenticator_invalid_password():
    """
        Test authentication with invalid password.
    """
    realm = "TestRealm"
    username = "testuser"
    correct_password = "correctpass"
    wrong_password = "wrongpass"
    uri = "/protected/resource"
    method = "GET"
    
    provider = MockDigestIdentityProvider()
    provider.add_user(username, realm, correct_password)
    authenticator = DigestAuthenticator(provider, realm=realm)
    
    # Get a challenge
    request1 = MockRequest(headers={})
    result1 = run_async(authenticator.authenticate(request1))
    
    nonce = extract_nonce_from_challenge(result1.challenge)
    opaque = extract_opaque_from_challenge(result1.challenge)
    
    # Compute response with WRONG password
    response = compute_digest_response(
        username=username,
        realm=realm,
        password=wrong_password,
        nonce=nonce,
        uri=uri,
        method=method,
        algorithm="MD5"
    )
    
    auth_header = create_digest_auth_header(
        username=username,
        realm=realm,
        nonce=nonce,
        uri=uri,
        response=response,
        algorithm="MD5",
        opaque=opaque
    )
    
    request2 = MockRequest(headers={"Authorization": auth_header}, method=method)
    result2 = run_async(authenticator.authenticate(request2))
    
    if result2.status != AuthenticationStatus.FAILURE:
        errmsg = f"Expected FAILURE status, got {result2.status}"
        raise AssertionError(errmsg)
    
    if result2.error_code != "invalid_credentials":
        errmsg = f"Expected error_code 'invalid_credentials', got '{result2.error_code}'"
        raise AssertionError(errmsg)
    
    return


def test_digest_authenticator_unknown_user():
    """
        Test authentication with unknown username.
    """
    realm = "TestRealm"
    uri = "/protected/resource"
    method = "GET"
    
    provider = MockDigestIdentityProvider()
    provider.add_user("knownuser", realm, "password")
    authenticator = DigestAuthenticator(provider, realm=realm)
    
    # Get a challenge
    request1 = MockRequest(headers={})
    result1 = run_async(authenticator.authenticate(request1))
    
    nonce = extract_nonce_from_challenge(result1.challenge)
    opaque = extract_opaque_from_challenge(result1.challenge)
    
    # Compute response for unknown user
    response = compute_digest_response(
        username="unknownuser",
        realm=realm,
        password="anypassword",
        nonce=nonce,
        uri=uri,
        method=method,
        algorithm="MD5"
    )
    
    auth_header = create_digest_auth_header(
        username="unknownuser",
        realm=realm,
        nonce=nonce,
        uri=uri,
        response=response,
        algorithm="MD5",
        opaque=opaque
    )
    
    request2 = MockRequest(headers={"Authorization": auth_header}, method=method)
    result2 = run_async(authenticator.authenticate(request2))
    
    if result2.status != AuthenticationStatus.FAILURE:
        errmsg = f"Expected FAILURE status, got {result2.status}"
        raise AssertionError(errmsg)
    
    if result2.error_code != "invalid_credentials":
        errmsg = f"Expected error_code 'invalid_credentials', got '{result2.error_code}'"
        raise AssertionError(errmsg)
    
    return


def test_digest_authenticator_sha256_algorithm():
    """
        Test authentication with SHA-256 algorithm.
    """
    realm = "TestRealm"
    username = "testuser"
    password = "testpass"
    uri = "/protected/resource"
    method = "GET"
    
    provider = MockDigestIdentityProvider()
    provider.add_user(username, realm, password)
    authenticator = DigestAuthenticator(
        provider, realm=realm, algorithm=DigestAlgorithm.SHA256
    )
    
    # Get a challenge
    request1 = MockRequest(headers={})
    result1 = run_async(authenticator.authenticate(request1))
    
    nonce = extract_nonce_from_challenge(result1.challenge)
    opaque = extract_opaque_from_challenge(result1.challenge)
    
    # Compute response with SHA-256
    response = compute_digest_response(
        username=username,
        realm=realm,
        password=password,
        nonce=nonce,
        uri=uri,
        method=method,
        algorithm="SHA-256"
    )
    
    auth_header = create_digest_auth_header(
        username=username,
        realm=realm,
        nonce=nonce,
        uri=uri,
        response=response,
        algorithm="SHA-256",
        opaque=opaque
    )
    
    request2 = MockRequest(headers={"Authorization": auth_header}, method=method)
    result2 = run_async(authenticator.authenticate(request2))
    
    if result2.status != AuthenticationStatus.SUCCESS:
        errmsg = f"Expected SUCCESS status with SHA-256, got {result2.status}"
        raise AssertionError(errmsg)
    
    return


def test_digest_authenticator_bearer_header_skips():
    """
        Test that Bearer auth header results in SKIP status.
    """
    provider = MockDigestIdentityProvider()
    authenticator = DigestAuthenticator(provider)
    
    request = MockRequest(headers={"Authorization": "Bearer sometoken"})
    
    result = run_async(authenticator.authenticate(request))
    
    if result.status != AuthenticationStatus.SKIP:
        errmsg = f"Expected SKIP status for Bearer header, got {result.status}"
        raise AssertionError(errmsg)
    
    return


def test_digest_authenticator_with_dict_request():
    """
        Test that DigestAuthenticator works with dict-style request.
    """
    realm = "TestRealm"
    username = "testuser"
    password = "testpass"
    uri = "/protected/resource"
    method = "GET"
    
    provider = MockDigestIdentityProvider()
    provider.add_user(username, realm, password)
    authenticator = DigestAuthenticator(provider, realm=realm)
    
    # Get a challenge
    request1 = {"headers": {}, "method": method}
    result1 = run_async(authenticator.authenticate(request1))
    
    nonce = extract_nonce_from_challenge(result1.challenge)
    opaque = extract_opaque_from_challenge(result1.challenge)
    
    # Compute response
    response = compute_digest_response(
        username=username,
        realm=realm,
        password=password,
        nonce=nonce,
        uri=uri,
        method=method,
        algorithm="MD5"
    )
    
    auth_header = create_digest_auth_header(
        username=username,
        realm=realm,
        nonce=nonce,
        uri=uri,
        response=response,
        algorithm="MD5",
        opaque=opaque
    )
    
    request2 = {"headers": {"Authorization": auth_header}, "method": method}
    result2 = run_async(authenticator.authenticate(request2))
    
    if result2.status != AuthenticationStatus.SUCCESS:
        errmsg = f"Expected SUCCESS status with dict request, got {result2.status}"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Property-Based Tests
# =============================================================================

# Feature: authentication, Property 8: Digest Auth Challenge Contains Nonce
# *For any* unauthenticated request to a Digest-protected endpoint, the response
# SHALL include a WWW-Authenticate header with a non-empty nonce value.
# **Validates: Requirements 3.1**

def test_property_8_digest_auth_challenge_contains_nonce():
    """
        Property 8: Digest Auth Challenge Contains Nonce
        
        For any unauthenticated request to a Digest-protected endpoint,
        the response SHALL include a WWW-Authenticate header with a
        non-empty nonce value.
        
        **Validates: Requirements 3.1**
    """
    # Run 100 iterations with random configurations
    for iteration in range(100):
        # Generate random realm
        realm = generate_random_realm()
        
        # Randomly choose algorithm
        algorithm = random.choice([DigestAlgorithm.MD5, DigestAlgorithm.SHA256])
        
        # Create authenticator with random configuration
        provider = MockDigestIdentityProvider()
        authenticator = DigestAuthenticator(
            provider,
            realm=realm,
            algorithm=algorithm
        )
        
        # Create unauthenticated request (no Authorization header)
        request = MockRequest(headers={})
        
        # Authenticate
        result = run_async(authenticator.authenticate(request))
        
        # Property: Status must be CHALLENGE
        if result.status != AuthenticationStatus.CHALLENGE:
            errmsg = f"Iteration {iteration}: Expected CHALLENGE status, got {result.status}"
            raise AssertionError(errmsg)
        
        # Property: Challenge must be present
        if result.challenge is None:
            errmsg = f"Iteration {iteration}: Expected challenge to be present"
            raise AssertionError(errmsg)
        
        # Property: Challenge must start with "Digest "
        if not result.challenge.startswith("Digest "):
            errmsg = f"Iteration {iteration}: Expected challenge to start with 'Digest '"
            raise AssertionError(errmsg)
        
        # Property: Challenge must contain a non-empty nonce
        nonce = extract_nonce_from_challenge(result.challenge)
        if nonce is None or nonce == "":
            errmsg = f"Iteration {iteration}: Expected non-empty nonce in challenge"
            raise AssertionError(errmsg)
        
        # Property: Challenge must contain the configured realm
        extracted_realm = extract_realm_from_challenge(result.challenge)
        if extracted_realm != realm:
            errmsg = f"Iteration {iteration}: Expected realm '{realm}', got '{extracted_realm}'"
            raise AssertionError(errmsg)
        
        # Property: Challenge must contain algorithm
        extracted_algorithm = extract_algorithm_from_challenge(result.challenge)
        if extracted_algorithm != algorithm.value:
            errmsg = f"Iteration {iteration}: Expected algorithm '{algorithm.value}', got '{extracted_algorithm}'"
            raise AssertionError(errmsg)
        
        # Property: Challenge must contain qop
        qop = extract_qop_from_challenge(result.challenge)
        if qop is None:
            errmsg = f"Iteration {iteration}: Expected qop in challenge"
            raise AssertionError(errmsg)
        
        # Property: Challenge must contain opaque
        opaque = extract_opaque_from_challenge(result.challenge)
        if opaque is None or opaque == "":
            errmsg = f"Iteration {iteration}: Expected non-empty opaque in challenge"
            raise AssertionError(errmsg)
    
    return


# Feature: authentication, Property 9: Digest Auth Nonce Freshness Validation
# *For any* Digest authentication attempt with a nonce older than the configured
# maximum age, the Digest_Authenticator SHALL reject the request and indicate
# stale=true.
# **Validates: Requirements 3.4, 3.6**

def test_property_9_digest_auth_nonce_freshness_validation():
    """
        Property 9: Digest Auth Nonce Freshness Validation
        
        For any Digest authentication attempt with a nonce older than the
        configured maximum age, the Digest_Authenticator SHALL reject the
        request and indicate stale=true.
        
        **Validates: Requirements 3.4, 3.6**
    """
    # Run 100 iterations with random configurations
    for iteration in range(100):
        # Generate random user credentials
        realm = generate_random_realm()
        username = generate_random_username()
        password = generate_random_password()
        uri = generate_random_uri()
        method = random.choice(["GET", "POST", "PUT", "DELETE"])
        
        # Use a very short nonce max age for testing (0.01 seconds)
        nonce_max_age = 0.01
        
        provider = MockDigestIdentityProvider()
        provider.add_user(username, realm, password)
        authenticator = DigestAuthenticator(
            provider,
            realm=realm,
            nonce_max_age=nonce_max_age
        )
        
        # Get a challenge to obtain a nonce
        request1 = MockRequest(headers={})
        result1 = run_async(authenticator.authenticate(request1))
        
        nonce = extract_nonce_from_challenge(result1.challenge)
        opaque = extract_opaque_from_challenge(result1.challenge)
        
        # Wait for the nonce to expire
        time.sleep(nonce_max_age + 0.02)
        
        # Compute valid response with the now-stale nonce
        response = compute_digest_response(
            username=username,
            realm=realm,
            password=password,
            nonce=nonce,
            uri=uri,
            method=method,
            algorithm="MD5"
        )
        
        auth_header = create_digest_auth_header(
            username=username,
            realm=realm,
            nonce=nonce,
            uri=uri,
            response=response,
            algorithm="MD5",
            opaque=opaque
        )
        
        request2 = MockRequest(headers={"Authorization": auth_header}, method=method)
        result2 = run_async(authenticator.authenticate(request2))
        
        # Property: Status must be CHALLENGE (not SUCCESS, not FAILURE)
        if result2.status != AuthenticationStatus.CHALLENGE:
            errmsg = f"Iteration {iteration}: Expected CHALLENGE status for stale nonce, got {result2.status}"
            raise AssertionError(errmsg)
        
        # Property: Challenge must contain stale=true
        if result2.challenge is None:
            errmsg = f"Iteration {iteration}: Expected challenge to be present"
            raise AssertionError(errmsg)
        
        if not extract_stale_from_challenge(result2.challenge):
            errmsg = f"Iteration {iteration}: Expected stale=true in challenge for expired nonce"
            raise AssertionError(errmsg)
        
        # Property: New challenge must contain a fresh nonce
        new_nonce = extract_nonce_from_challenge(result2.challenge)
        if new_nonce is None or new_nonce == "":
            errmsg = f"Iteration {iteration}: Expected new nonce in stale challenge"
            raise AssertionError(errmsg)
        
        # Property: New nonce must be different from the stale one
        if new_nonce == nonce:
            errmsg = f"Iteration {iteration}: Expected new nonce to be different from stale nonce"
            raise AssertionError(errmsg)

    return


# =============================================================================
# Constant-time response-hash comparison (CVE-class regression)
# =============================================================================

def test_digest_response_compare_uses_constant_time_compare():
    """
        Property: response-hash comparison must use
        ``hmac.compare_digest`` so an attacker can't infer the
        correct hash byte-by-byte from response-time variations.

        Implementation guard: this test reads the digest module
        source and asserts that ``hmac.compare_digest`` appears in
        the body of ``DigestAuthenticator.authenticate``.
        Removing the constant-time check or reverting to ``!=`` /
        ``==`` would re-introduce the timing-attack vulnerability;
        this test fails fast in that case.
    """
    import inspect
    source = inspect.getsource(DigestAuthenticator.authenticate)
    if "hmac.compare_digest" not in source:
        errmsg = (
            "DigestAuthenticator.authenticate must use "
            "hmac.compare_digest for the response-hash comparison "
            "to defend against timing attacks."
        )
        raise AssertionError(errmsg)
    return


def test_digest_authenticator_rejects_response_hash_off_by_one_char():
    """
        Property: a response hash that differs from the expected
        value by a single character (e.g. last hex digit flipped)
        is rejected with the same FAILURE outcome a fully-wrong
        hash would produce.

        Why: with a non-constant-time compare, a single-character
        difference at the end of the hash would take measurably
        longer than a difference at the start. With
        ``hmac.compare_digest`` both paths must funnel into the
        same ``invalid_credentials`` outcome.
    """
    realm = "TestRealm"
    username = "testuser"
    password = "secret"
    uri = "/protected/resource"
    method = "GET"

    provider = MockDigestIdentityProvider()
    provider.add_user(username, realm, password)
    authenticator = DigestAuthenticator(provider, realm=realm)

    request1 = MockRequest(headers={})
    result1 = run_async(authenticator.authenticate(request1))
    nonce = extract_nonce_from_challenge(result1.challenge)
    opaque = extract_opaque_from_challenge(result1.challenge)

    correct_response = compute_digest_response(
        username=username,
        realm=realm,
        password=password,
        nonce=nonce,
        uri=uri,
        method=method,
        algorithm="MD5",
    )
    # Flip the last hex digit so the hash is one character off.
    if correct_response[-1] == "0":
        tampered_last = "1"
    else:
        tampered_last = "0"
    tampered_response = correct_response[:-1] + tampered_last

    auth_header = create_digest_auth_header(
        username=username,
        realm=realm,
        nonce=nonce,
        uri=uri,
        response=tampered_response,
        algorithm="MD5",
        opaque=opaque,
    )
    request2 = MockRequest(
        headers={"Authorization": auth_header}, method=method,
    )
    result2 = run_async(authenticator.authenticate(request2))

    if result2.status != AuthenticationStatus.FAILURE:
        errmsg = (
            "Expected FAILURE for response hash differing by one "
            "char, got {}".format(result2.status)
        )
        raise AssertionError(errmsg)
    if result2.error_code != "invalid_credentials":
        errmsg = (
            "Expected error_code 'invalid_credentials' for "
            "tampered hash, got '{}'".format(result2.error_code)
        )
        raise AssertionError(errmsg)
    return


def test_digest_authenticator_accepts_uppercase_response_hash():
    """
        Property: a correct response hash submitted in uppercase
        hex still authenticates. Confirms the case-normalization
        on both sides of the comparison survived the switch to
        ``hmac.compare_digest``.

        Why: ``hmac.compare_digest`` requires the two inputs to
        be the same length AND the same byte values; if the code
        only lowercased one side, an uppercase-but-correct hash
        would silently be rejected. RFC 7616 says response is
        lowercase but tolerant servers normalize.
    """
    realm = "TestRealm"
    username = "testuser"
    password = "secret"
    uri = "/protected/resource"
    method = "GET"

    provider = MockDigestIdentityProvider()
    provider.add_user(username, realm, password)
    authenticator = DigestAuthenticator(provider, realm=realm)

    request1 = MockRequest(headers={})
    result1 = run_async(authenticator.authenticate(request1))
    nonce = extract_nonce_from_challenge(result1.challenge)
    opaque = extract_opaque_from_challenge(result1.challenge)

    response = compute_digest_response(
        username=username,
        realm=realm,
        password=password,
        nonce=nonce,
        uri=uri,
        method=method,
        algorithm="MD5",
    )
    upper_response = response.upper()
    auth_header = create_digest_auth_header(
        username=username,
        realm=realm,
        nonce=nonce,
        uri=uri,
        response=upper_response,
        algorithm="MD5",
        opaque=opaque,
    )
    request2 = MockRequest(
        headers={"Authorization": auth_header}, method=method,
    )
    result2 = run_async(authenticator.authenticate(request2))

    if result2.status != AuthenticationStatus.SUCCESS:
        errmsg = (
            "Expected SUCCESS for uppercase-hex correct response, "
            "got {} (error_code={})".format(
                result2.status, getattr(result2, "error_code", None),
            )
        )
        raise AssertionError(errmsg)
    return
