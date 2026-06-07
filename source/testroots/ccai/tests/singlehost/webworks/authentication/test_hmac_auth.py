"""
    Tests for the HMACAuthenticator module.
    
    This module contains unit tests and property-based tests for the
    HMACAuthenticator class and related utility functions.
"""

import asyncio
import hashlib
import hmac
import random
import string
import time
from typing import Any, Dict, List, Optional, Set

from ccai.webworks.authentication import (
    AuthenticationStatus,
    AuthenticationResult,
    Principal,
    AuthenticationContext,
    HMACAlgorithm,
    HMACAuthenticator,
    HMACCredentials,
    compute_hmac_signature,
    create_hmac_auth_header
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


def generate_random_key_id() -> str:
    """
        Generate a random key ID (alphanumeric).
    """
    length = random.randint(8, 32)
    chars = string.ascii_letters + string.digits + "_-"
    return ''.join(random.choices(chars, k=length))


def generate_random_secret() -> str:
    """
        Generate a random secret key.
    """
    length = random.randint(32, 64)
    chars = string.ascii_letters + string.digits + "!@#$%^&*()-_=+[]{}|;',.<>?"
    return ''.join(random.choices(chars, k=length))


def generate_random_path() -> str:
    """
        Generate a random URI path.
    """
    segments = random.randint(1, 5)
    parts = [generate_random_string(1, 15) for _ in range(segments)]
    return "/" + "/".join(parts)


def generate_random_method() -> str:
    """
        Generate a random HTTP method.
    """
    return random.choice(["GET", "POST", "PUT", "DELETE", "PATCH"])


def generate_random_headers() -> Dict[str, str]:
    """
        Generate random request headers.
    """
    headers = {
        "host": f"{generate_random_string(3, 15)}.example.com",
        "date": time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime()),
        "content-type": random.choice([
            "application/json",
            "text/plain",
            "application/xml"
        ])
    }
    return headers


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
# Mock Key Store
# =============================================================================

class MockHMACKeyStore:
    """
        A mock key store for testing HMACAuthenticator.
        
        This store maintains a mapping of key_id -> (secret, Principal)
        and validates keys against this mapping.
    """
    
    def __init__(self):
        self._keys: Dict[str, tuple] = {}
    
    def add_key(
        self,
        key_id: str,
        secret: str,
        display_name: Optional[str] = None,
        roles: Optional[Set[str]] = None,
        permissions: Optional[Set[str]] = None
    ) -> Principal:
        """
            Add a key to the store.
            
            :returns: The created Principal.
        """
        principal = Principal(
            identifier=key_id,
            display_name=display_name or key_id,
            roles=roles or set(),
            permissions=permissions or set()
        )
        
        self._keys[key_id] = (secret, principal)
        return principal
    
    async def get_secret(self, key_id: str) -> Optional[str]:
        """
            Get the secret for a key ID.
        """
        if key_id not in self._keys:
            return None
        
        secret, _ = self._keys[key_id]
        return secret
    
    async def get_principal(self, key_id: str) -> Optional[Principal]:
        """
            Retrieve a principal by key ID.
        """
        if key_id not in self._keys:
            return None
        
        _, principal = self._keys[key_id]
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
        method: str = "GET",
        path: str = "/"
    ):
        self.headers = headers or {}
        self.method = method
        self.path = path


# =============================================================================
# Helper Functions
# =============================================================================

def run_async(coro):
    """
        Run an async coroutine synchronously for testing.
    """
    return asyncio.run(coro)


# =============================================================================
# Unit Tests for compute_hmac_signature
# =============================================================================

def test_compute_hmac_signature_sha256():
    """
        Test computing HMAC signature with SHA-256 algorithm.
    """
    secret = "test-secret"
    method = "GET"
    path = "/api/resource"
    timestamp = "1234567890"
    headers = {"host": "example.com", "date": "Mon, 01 Jan 2024 00:00:00 GMT"}
    signed_headers = ["host", "date"]
    
    signature = compute_hmac_signature(
        secret=secret,
        method=method,
        path=path,
        timestamp=timestamp,
        headers=headers,
        signed_headers=signed_headers,
        algorithm="HMAC-SHA256"
    )
    
    # Verify it's a valid SHA-256 hex string (64 characters)
    if len(signature) != 64:
        errmsg = f"Expected 64 character SHA-256 signature, got {len(signature)} characters"
        raise AssertionError(errmsg)
    
    # Verify it's deterministic
    signature2 = compute_hmac_signature(
        secret=secret,
        method=method,
        path=path,
        timestamp=timestamp,
        headers=headers,
        signed_headers=signed_headers,
        algorithm="HMAC-SHA256"
    )
    
    if signature != signature2:
        errmsg = "Expected deterministic signature"
        raise AssertionError(errmsg)
    
    return


def test_compute_hmac_signature_sha512():
    """
        Test computing HMAC signature with SHA-512 algorithm.
    """
    secret = "test-secret"
    method = "POST"
    path = "/api/resource"
    timestamp = "1234567890"
    headers = {"host": "example.com"}
    signed_headers = ["host"]
    
    signature = compute_hmac_signature(
        secret=secret,
        method=method,
        path=path,
        timestamp=timestamp,
        headers=headers,
        signed_headers=signed_headers,
        algorithm="HMAC-SHA512"
    )
    
    # Verify it's a valid SHA-512 hex string (128 characters)
    if len(signature) != 128:
        errmsg = f"Expected 128 character SHA-512 signature, got {len(signature)} characters"
        raise AssertionError(errmsg)
    
    return


def test_compute_hmac_signature_different_secrets():
    """
        Test that different secrets produce different signatures.
    """
    method = "GET"
    path = "/api/resource"
    timestamp = "1234567890"
    headers = {"host": "example.com"}
    signed_headers = ["host"]
    
    signature1 = compute_hmac_signature(
        secret="secret1",
        method=method,
        path=path,
        timestamp=timestamp,
        headers=headers,
        signed_headers=signed_headers
    )
    
    signature2 = compute_hmac_signature(
        secret="secret2",
        method=method,
        path=path,
        timestamp=timestamp,
        headers=headers,
        signed_headers=signed_headers
    )
    
    if signature1 == signature2:
        errmsg = "Expected different signatures for different secrets"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for create_hmac_auth_header
# =============================================================================

def test_create_hmac_auth_header_basic():
    """
        Test creating HMAC Authorization header.
    """
    header = create_hmac_auth_header(
        key_id="test-key",
        signature="abc123",
        timestamp="1234567890"
    )
    
    if not header.startswith("HMAC "):
        errmsg = f"Expected header to start with 'HMAC ', got '{header}'"
        raise AssertionError(errmsg)
    
    if 'KeyId="test-key"' not in header:
        errmsg = f"Expected KeyId in header, got '{header}'"
        raise AssertionError(errmsg)
    
    if 'Signature="abc123"' not in header:
        errmsg = f"Expected Signature in header, got '{header}'"
        raise AssertionError(errmsg)
    
    if 'Timestamp="1234567890"' not in header:
        errmsg = f"Expected Timestamp in header, got '{header}'"
        raise AssertionError(errmsg)
    
    return


def test_create_hmac_auth_header_with_signed_headers():
    """
        Test creating HMAC Authorization header with signed headers.
    """
    header = create_hmac_auth_header(
        key_id="test-key",
        signature="abc123",
        timestamp="1234567890",
        signed_headers=["host", "date"]
    )
    
    if 'SignedHeaders="host;date"' not in header:
        errmsg = f"Expected SignedHeaders in header, got '{header}'"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for HMACAuthenticator
# =============================================================================

def test_hmac_authenticator_scheme():
    """
        Test that HMACAuthenticator returns "HMAC" as scheme.
    """
    key_store = MockHMACKeyStore()
    authenticator = HMACAuthenticator(key_store)
    
    if authenticator.scheme != "HMAC":
        errmsg = f"Expected scheme 'HMAC', got '{authenticator.scheme}'"
        raise AssertionError(errmsg)
    
    return


def test_hmac_authenticator_default_timestamp_window():
    """
        Test that HMACAuthenticator has default timestamp window of 300 seconds.
    """
    key_store = MockHMACKeyStore()
    authenticator = HMACAuthenticator(key_store)
    
    if authenticator.timestamp_window != 300.0:
        errmsg = f"Expected timestamp_window 300.0, got {authenticator.timestamp_window}"
        raise AssertionError(errmsg)
    
    return


def test_hmac_authenticator_custom_timestamp_window():
    """
        Test that HMACAuthenticator accepts custom timestamp window.
    """
    key_store = MockHMACKeyStore()
    authenticator = HMACAuthenticator(key_store, timestamp_window=600.0)
    
    if authenticator.timestamp_window != 600.0:
        errmsg = f"Expected timestamp_window 600.0, got {authenticator.timestamp_window}"
        raise AssertionError(errmsg)
    
    return


def test_hmac_authenticator_can_handle_with_hmac_header():
    """
        Test that can_handle returns True for HMAC auth header.
    """
    key_store = MockHMACKeyStore()
    authenticator = HMACAuthenticator(key_store)
    
    request = MockRequest(headers={"Authorization": 'HMAC KeyId="test"'})
    
    if not authenticator.can_handle(request):
        errmsg = "Expected can_handle to return True for HMAC auth header"
        raise AssertionError(errmsg)
    
    return


def test_hmac_authenticator_can_handle_case_insensitive():
    """
        Test that can_handle is case-insensitive for scheme.
    """
    key_store = MockHMACKeyStore()
    authenticator = HMACAuthenticator(key_store)
    
    request = MockRequest(headers={"Authorization": 'hmac KeyId="test"'})
    
    if not authenticator.can_handle(request):
        errmsg = "Expected can_handle to return True for lowercase 'hmac'"
        raise AssertionError(errmsg)
    
    return


def test_hmac_authenticator_can_handle_without_header():
    """
        Test that can_handle returns False when no Authorization header.
    """
    key_store = MockHMACKeyStore()
    authenticator = HMACAuthenticator(key_store)
    
    request = MockRequest(headers={})
    
    if authenticator.can_handle(request):
        errmsg = "Expected can_handle to return False without Authorization header"
        raise AssertionError(errmsg)
    
    return


def test_hmac_authenticator_can_handle_with_basic_header():
    """
        Test that can_handle returns False for Basic auth header.
    """
    key_store = MockHMACKeyStore()
    authenticator = HMACAuthenticator(key_store)
    
    request = MockRequest(headers={"Authorization": "Basic dXNlcjpwYXNz"})
    
    if authenticator.can_handle(request):
        errmsg = "Expected can_handle to return False for Basic auth header"
        raise AssertionError(errmsg)
    
    return


def test_hmac_authenticator_skip_on_no_header():
    """
        Test that missing Authorization header returns SKIP.
    """
    key_store = MockHMACKeyStore()
    authenticator = HMACAuthenticator(key_store)
    
    request = MockRequest(headers={})
    
    result = run_async(authenticator.authenticate(request))
    
    if result.status != AuthenticationStatus.SKIP:
        errmsg = f"Expected SKIP status, got {result.status}"
        raise AssertionError(errmsg)
    
    return


def test_hmac_authenticator_valid_signature():
    """
        Test authentication with valid signature.
    """
    key_id = "test-key"
    secret = "test-secret-key"
    method = "GET"
    path = "/api/resource"
    timestamp = str(time.time())
    headers = {"host": "example.com", "date": "Mon, 01 Jan 2024 00:00:00 GMT"}
    signed_headers = ["host", "date"]
    
    key_store = MockHMACKeyStore()
    key_store.add_key(key_id, secret, display_name="Test Key")
    authenticator = HMACAuthenticator(
        key_store,
        signed_headers=signed_headers
    )
    
    # Compute signature
    signature = compute_hmac_signature(
        secret=secret,
        method=method,
        path=path,
        timestamp=timestamp,
        headers=headers,
        signed_headers=signed_headers,
        algorithm="HMAC-SHA256"
    )
    
    # Create authorization header
    auth_header = create_hmac_auth_header(
        key_id=key_id,
        signature=signature,
        timestamp=timestamp,
        algorithm="HMAC-SHA256",
        signed_headers=signed_headers
    )
    
    request_headers = dict(headers)
    request_headers["Authorization"] = auth_header
    
    request = MockRequest(headers=request_headers, method=method, path=path)
    result = run_async(authenticator.authenticate(request))
    
    if result.status != AuthenticationStatus.SUCCESS:
        errmsg = f"Expected SUCCESS status, got {result.status}"
        raise AssertionError(errmsg)
    
    if result.context is None:
        errmsg = "Expected context to be present on success"
        raise AssertionError(errmsg)
    
    if result.context.principal.identifier != key_id:
        errmsg = f"Expected principal identifier '{key_id}', got '{result.context.principal.identifier}'"
        raise AssertionError(errmsg)
    
    return


def test_hmac_authenticator_invalid_signature():
    """
        Test authentication with invalid signature.
    """
    key_id = "test-key"
    secret = "test-secret-key"
    method = "GET"
    path = "/api/resource"
    timestamp = str(time.time())
    headers = {"host": "example.com"}
    signed_headers = ["host"]
    
    key_store = MockHMACKeyStore()
    key_store.add_key(key_id, secret)
    authenticator = HMACAuthenticator(key_store, signed_headers=signed_headers)
    
    # Create authorization header with WRONG signature
    auth_header = create_hmac_auth_header(
        key_id=key_id,
        signature="invalid-signature",
        timestamp=timestamp,
        algorithm="HMAC-SHA256",
        signed_headers=signed_headers
    )
    
    request_headers = dict(headers)
    request_headers["Authorization"] = auth_header
    
    request = MockRequest(headers=request_headers, method=method, path=path)
    result = run_async(authenticator.authenticate(request))
    
    if result.status != AuthenticationStatus.FAILURE:
        errmsg = f"Expected FAILURE status, got {result.status}"
        raise AssertionError(errmsg)
    
    if result.error_code != "invalid_signature":
        errmsg = f"Expected error_code 'invalid_signature', got '{result.error_code}'"
        raise AssertionError(errmsg)
    
    return


def test_hmac_authenticator_unknown_key():
    """
        Test authentication with unknown key ID.
    """
    timestamp = str(time.time())
    
    key_store = MockHMACKeyStore()
    key_store.add_key("known-key", "secret")
    authenticator = HMACAuthenticator(key_store)
    
    auth_header = create_hmac_auth_header(
        key_id="unknown-key",
        signature="some-signature",
        timestamp=timestamp
    )
    
    request = MockRequest(headers={"Authorization": auth_header})
    result = run_async(authenticator.authenticate(request))
    
    if result.status != AuthenticationStatus.FAILURE:
        errmsg = f"Expected FAILURE status, got {result.status}"
        raise AssertionError(errmsg)
    
    if result.error_code != "invalid_key":
        errmsg = f"Expected error_code 'invalid_key', got '{result.error_code}'"
        raise AssertionError(errmsg)
    
    return


def test_hmac_authenticator_expired_timestamp():
    """
        Test authentication with expired timestamp.
    """
    key_id = "test-key"
    secret = "test-secret"
    
    key_store = MockHMACKeyStore()
    key_store.add_key(key_id, secret)
    authenticator = HMACAuthenticator(key_store, timestamp_window=60.0)
    
    # Use a timestamp from 2 minutes ago
    old_timestamp = str(time.time() - 120)
    
    signature = compute_hmac_signature(
        secret=secret,
        method="GET",
        path="/",
        timestamp=old_timestamp,
        headers={},
        signed_headers=[]
    )
    
    auth_header = create_hmac_auth_header(
        key_id=key_id,
        signature=signature,
        timestamp=old_timestamp
    )
    
    request = MockRequest(headers={"Authorization": auth_header})
    result = run_async(authenticator.authenticate(request))
    
    if result.status != AuthenticationStatus.FAILURE:
        errmsg = f"Expected FAILURE status for expired timestamp, got {result.status}"
        raise AssertionError(errmsg)
    
    if result.error_code != "invalid_timestamp":
        errmsg = f"Expected error_code 'invalid_timestamp', got '{result.error_code}'"
        raise AssertionError(errmsg)
    
    return


def test_hmac_authenticator_sha512_algorithm():
    """
        Test authentication with SHA-512 algorithm.
    """
    key_id = "test-key"
    secret = "test-secret-key"
    method = "POST"
    path = "/api/resource"
    timestamp = str(time.time())
    headers = {"host": "example.com"}
    signed_headers = ["host"]
    
    key_store = MockHMACKeyStore()
    key_store.add_key(key_id, secret)
    authenticator = HMACAuthenticator(
        key_store,
        signed_headers=signed_headers,
        algorithm=HMACAlgorithm.HMAC_SHA512
    )
    
    # Compute signature with SHA-512
    signature = compute_hmac_signature(
        secret=secret,
        method=method,
        path=path,
        timestamp=timestamp,
        headers=headers,
        signed_headers=signed_headers,
        algorithm="HMAC-SHA512"
    )
    
    auth_header = create_hmac_auth_header(
        key_id=key_id,
        signature=signature,
        timestamp=timestamp,
        algorithm="HMAC-SHA512",
        signed_headers=signed_headers
    )
    
    request_headers = dict(headers)
    request_headers["Authorization"] = auth_header
    
    request = MockRequest(headers=request_headers, method=method, path=path)
    result = run_async(authenticator.authenticate(request))
    
    if result.status != AuthenticationStatus.SUCCESS:
        errmsg = f"Expected SUCCESS status with SHA-512, got {result.status}"
        raise AssertionError(errmsg)
    
    return


def test_hmac_authenticator_bearer_header_skips():
    """
        Test that Bearer auth header results in SKIP status.
    """
    key_store = MockHMACKeyStore()
    authenticator = HMACAuthenticator(key_store)
    
    request = MockRequest(headers={"Authorization": "Bearer sometoken"})
    
    result = run_async(authenticator.authenticate(request))
    
    if result.status != AuthenticationStatus.SKIP:
        errmsg = f"Expected SKIP status for Bearer header, got {result.status}"
        raise AssertionError(errmsg)
    
    return


def test_hmac_authenticator_with_dict_request():
    """
        Test that HMACAuthenticator works with dict-style request.
    """
    key_id = "test-key"
    secret = "test-secret-key"
    method = "GET"
    path = "/api/resource"
    timestamp = str(time.time())
    headers = {"host": "example.com"}
    signed_headers = ["host"]
    
    key_store = MockHMACKeyStore()
    key_store.add_key(key_id, secret)
    authenticator = HMACAuthenticator(key_store, signed_headers=signed_headers)
    
    # Compute signature
    signature = compute_hmac_signature(
        secret=secret,
        method=method,
        path=path,
        timestamp=timestamp,
        headers=headers,
        signed_headers=signed_headers
    )
    
    auth_header = create_hmac_auth_header(
        key_id=key_id,
        signature=signature,
        timestamp=timestamp,
        signed_headers=signed_headers
    )
    
    request_headers = dict(headers)
    request_headers["Authorization"] = auth_header
    
    request = {"headers": request_headers, "method": method, "path": path}
    result = run_async(authenticator.authenticate(request))
    
    if result.status != AuthenticationStatus.SUCCESS:
        errmsg = f"Expected SUCCESS status with dict request, got {result.status}"
        raise AssertionError(errmsg)
    
    return



# =============================================================================
# Property-Based Tests
# =============================================================================

# Feature: authentication, Property 23: HMAC Signature Validation
# *For any* request with a valid HMAC signature computed over the canonical
# request string with the correct secret, the HMAC_Authenticator SHALL return
# SUCCESS.
# **Validates: Requirements 9.1, 9.5, 9.6**

def test_property_23_hmac_signature_validation():
    """
        Property 23: HMAC Signature Validation
        
        For any request with a valid HMAC signature computed over the
        canonical request string with the correct secret, the
        HMAC_Authenticator SHALL return SUCCESS.
        
        **Validates: Requirements 9.1, 9.5, 9.6**
    """
    # Run 100 iterations with random configurations
    for iteration in range(100):
        # Generate random key and secret
        key_id = generate_random_key_id()
        secret = generate_random_secret()
        
        # Generate random request parameters
        method = generate_random_method()
        path = generate_random_path()
        timestamp = str(time.time())
        headers = generate_random_headers()
        
        # Randomly choose algorithm
        algorithm = random.choice(["HMAC-SHA256", "HMAC-SHA512"])
        
        # Randomly choose signed headers (subset of available headers)
        available_headers = list(headers.keys())
        num_signed = random.randint(0, len(available_headers))
        signed_headers = random.sample(available_headers, num_signed)
        
        # Create key store and authenticator
        key_store = MockHMACKeyStore()
        key_store.add_key(key_id, secret)
        authenticator = HMACAuthenticator(
            key_store,
            signed_headers=signed_headers,
            algorithm=HMACAlgorithm.HMAC_SHA256 if algorithm == "HMAC-SHA256" else HMACAlgorithm.HMAC_SHA512
        )
        
        # Compute valid signature
        signature = compute_hmac_signature(
            secret=secret,
            method=method,
            path=path,
            timestamp=timestamp,
            headers=headers,
            signed_headers=signed_headers,
            algorithm=algorithm
        )
        
        # Create authorization header
        auth_header = create_hmac_auth_header(
            key_id=key_id,
            signature=signature,
            timestamp=timestamp,
            algorithm=algorithm,
            signed_headers=signed_headers
        )
        
        # Build request
        request_headers = dict(headers)
        request_headers["Authorization"] = auth_header
        
        request = MockRequest(headers=request_headers, method=method, path=path)
        
        # Authenticate
        result = run_async(authenticator.authenticate(request))
        
        # Property: Status must be SUCCESS for valid signature
        if result.status != AuthenticationStatus.SUCCESS:
            errmsg = f"Iteration {iteration}: Expected SUCCESS status for valid signature, got {result.status}"
            if result.error_description:
                errmsg += f" - {result.error_description}"
            raise AssertionError(errmsg)
        
        # Property: Context must be present
        if result.context is None:
            errmsg = f"Iteration {iteration}: Expected context to be present on success"
            raise AssertionError(errmsg)
        
        # Property: Principal identifier must match key_id
        if result.context.principal.identifier != key_id:
            errmsg = f"Iteration {iteration}: Expected principal identifier '{key_id}', got '{result.context.principal.identifier}'"
            raise AssertionError(errmsg)
        
        # Property: Scheme must be "HMAC"
        if result.context.scheme != "HMAC":
            errmsg = f"Iteration {iteration}: Expected scheme 'HMAC', got '{result.context.scheme}'"
            raise AssertionError(errmsg)
        
        # Property: Attributes must contain key_id
        if result.context.attributes.get("key_id") != key_id:
            errmsg = f"Iteration {iteration}: Expected key_id in attributes"
            raise AssertionError(errmsg)
        
        # Property: Attributes must contain algorithm
        if result.context.attributes.get("algorithm") != algorithm:
            errmsg = f"Iteration {iteration}: Expected algorithm '{algorithm}' in attributes"
            raise AssertionError(errmsg)
    
    return


# Feature: authentication, Property 24: HMAC Timestamp Window Enforcement
# *For any* HMAC-signed request with a timestamp outside the configured window,
# the HMAC_Authenticator SHALL return FAILURE.
# **Validates: Requirements 9.3, 9.8**

def test_property_24_hmac_timestamp_window_enforcement():
    """
        Property 24: HMAC Timestamp Window Enforcement
        
        For any HMAC-signed request with a timestamp outside the configured
        window, the HMAC_Authenticator SHALL return FAILURE.
        
        **Validates: Requirements 9.3, 9.8**
    """
    # Run 100 iterations with random configurations
    for iteration in range(100):
        # Generate random key and secret
        key_id = generate_random_key_id()
        secret = generate_random_secret()
        
        # Generate random request parameters
        method = generate_random_method()
        path = generate_random_path()
        headers = generate_random_headers()
        
        # Use a short timestamp window for testing
        timestamp_window = random.uniform(10.0, 60.0)
        
        # Generate a timestamp outside the window
        # Either too old or too far in the future
        if random.choice([True, False]):
            # Too old
            offset = timestamp_window + random.uniform(1.0, 100.0)
            timestamp = str(time.time() - offset)
        else:
            # Too far in the future
            offset = timestamp_window + random.uniform(1.0, 100.0)
            timestamp = str(time.time() + offset)
        
        # Create key store and authenticator
        key_store = MockHMACKeyStore()
        key_store.add_key(key_id, secret)
        authenticator = HMACAuthenticator(
            key_store,
            timestamp_window=timestamp_window
        )
        
        # Compute signature (even though timestamp is invalid)
        signature = compute_hmac_signature(
            secret=secret,
            method=method,
            path=path,
            timestamp=timestamp,
            headers=headers,
            signed_headers=[]
        )
        
        # Create authorization header
        auth_header = create_hmac_auth_header(
            key_id=key_id,
            signature=signature,
            timestamp=timestamp
        )
        
        # Build request
        request_headers = dict(headers)
        request_headers["Authorization"] = auth_header
        
        request = MockRequest(headers=request_headers, method=method, path=path)
        
        # Authenticate
        result = run_async(authenticator.authenticate(request))
        
        # Property: Status must be FAILURE for expired timestamp
        if result.status != AuthenticationStatus.FAILURE:
            errmsg = f"Iteration {iteration}: Expected FAILURE status for timestamp outside window, got {result.status}"
            raise AssertionError(errmsg)
        
        # Property: Error code must indicate timestamp issue
        if result.error_code != "invalid_timestamp":
            errmsg = f"Iteration {iteration}: Expected error_code 'invalid_timestamp', got '{result.error_code}'"
            raise AssertionError(errmsg)
        
        # Property: Context must NOT be present
        if result.context is not None:
            errmsg = f"Iteration {iteration}: Expected no context on failure"
            raise AssertionError(errmsg)
    
    return
