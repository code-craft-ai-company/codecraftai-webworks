"""
    Tests for the BasicAuthenticator module.
    
    This module contains unit tests and property-based tests for the
    BasicAuthenticator class and related utility functions.
"""

import asyncio
import base64
import random
import string
from typing import Any, Dict, Optional, Set

from automojo.webworks.authentication import (
    AuthenticationStatus,
    AuthenticationResult,
    Principal,
    AuthenticationContext,
    BasicAuthenticator,
    encode_basic_credentials,
    create_basic_auth_header
)


# =============================================================================
# Test Data Generators
# =============================================================================

def generate_random_string(min_length: int = 1, max_length: int = 50) -> str:
    """
        Generate a random string of printable characters.
    """
    length = random.randint(min_length, max_length)
    # Use printable characters but exclude some problematic ones
    chars = string.ascii_letters + string.digits + "!@#$%^&*()-_=+[]{}|;',.<>?`~"
    return ''.join(random.choices(chars, k=length))


def generate_random_username() -> str:
    """
        Generate a random username (alphanumeric, no colons).
    """
    length = random.randint(1, 30)
    chars = string.ascii_letters + string.digits + "_-."
    return ''.join(random.choices(chars, k=length))


def generate_random_password() -> str:
    """
        Generate a random password (may contain colons and special chars).
    """
    length = random.randint(1, 50)
    # Passwords can contain any printable character including colons
    chars = string.ascii_letters + string.digits + "!@#$%^&*()-_=+[]{}|;':,.<>?`~"
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


# =============================================================================
# Mock Identity Provider
# =============================================================================

class MockIdentityProvider:
    """
        A mock identity provider for testing BasicAuthenticator.
        
        This provider stores a mapping of username -> (password, Principal)
        and validates credentials against this mapping.
    """
    
    def __init__(self):
        self._credentials: Dict[str, tuple] = {}
    
    def add_user(
        self,
        username: str,
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
        self._credentials[username] = (password, principal)
        return principal
    
    async def validate_credentials(
        self,
        username: str,
        password: str
    ) -> Optional[Principal]:
        """
            Validate username/password credentials.
        """
        if username not in self._credentials:
            return None
        
        stored_password, principal = self._credentials[username]
        if password != stored_password:
            return None
        
        return principal
    
    async def get_principal(self, identifier: str) -> Optional[Principal]:
        """
            Retrieve a principal by identifier.
        """
        if identifier not in self._credentials:
            return None
        
        _, principal = self._credentials[identifier]
        return principal


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
# Unit Tests for encode_basic_credentials
# =============================================================================

def test_encode_basic_credentials_simple():
    """
        Test encoding simple username and password.
    """
    encoded = encode_basic_credentials("user", "pass")
    
    # Decode and verify
    decoded = base64.b64decode(encoded).decode("utf-8")
    if decoded != "user:pass":
        errmsg = f"Expected 'user:pass', got '{decoded}'"
        raise AssertionError(errmsg)
    
    return


def test_encode_basic_credentials_with_colon_in_password():
    """
        Test encoding password containing colons.
    """
    encoded = encode_basic_credentials("user", "pass:word:with:colons")
    
    decoded = base64.b64decode(encoded).decode("utf-8")
    if decoded != "user:pass:word:with:colons":
        errmsg = f"Expected 'user:pass:word:with:colons', got '{decoded}'"
        raise AssertionError(errmsg)
    
    return


def test_encode_basic_credentials_empty_password():
    """
        Test encoding with empty password.
    """
    encoded = encode_basic_credentials("user", "")
    
    decoded = base64.b64decode(encoded).decode("utf-8")
    if decoded != "user:":
        errmsg = f"Expected 'user:', got '{decoded}'"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for create_basic_auth_header
# =============================================================================

def test_create_basic_auth_header_format():
    """
        Test that create_basic_auth_header produces correct format.
    """
    header = create_basic_auth_header("user", "pass")
    
    if not header.startswith("Basic "):
        errmsg = f"Expected header to start with 'Basic ', got '{header}'"
        raise AssertionError(errmsg)
    
    # Extract and decode the credentials part
    credentials = header[6:]  # Remove "Basic " prefix
    decoded = base64.b64decode(credentials).decode("utf-8")
    if decoded != "user:pass":
        errmsg = f"Expected decoded credentials 'user:pass', got '{decoded}'"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for BasicAuthenticator
# =============================================================================

def test_basic_authenticator_scheme():
    """
        Test that BasicAuthenticator returns "Basic" as scheme.
    """
    provider = MockIdentityProvider()
    authenticator = BasicAuthenticator(provider)
    
    if authenticator.scheme != "Basic":
        errmsg = f"Expected scheme 'Basic', got '{authenticator.scheme}'"
        raise AssertionError(errmsg)
    
    return


def test_basic_authenticator_default_realm():
    """
        Test that BasicAuthenticator has default realm "Restricted".
    """
    provider = MockIdentityProvider()
    authenticator = BasicAuthenticator(provider)
    
    if authenticator.realm != "Restricted":
        errmsg = f"Expected realm 'Restricted', got '{authenticator.realm}'"
        raise AssertionError(errmsg)
    
    return


def test_basic_authenticator_custom_realm():
    """
        Test that BasicAuthenticator accepts custom realm.
    """
    provider = MockIdentityProvider()
    authenticator = BasicAuthenticator(provider, realm="MyApp")
    
    if authenticator.realm != "MyApp":
        errmsg = f"Expected realm 'MyApp', got '{authenticator.realm}'"
        raise AssertionError(errmsg)
    
    return


def test_basic_authenticator_can_handle_with_basic_header():
    """
        Test that can_handle returns True for Basic auth header.
    """
    provider = MockIdentityProvider()
    authenticator = BasicAuthenticator(provider)
    
    request = MockRequest(headers={"Authorization": "Basic dXNlcjpwYXNz"})
    
    if not authenticator.can_handle(request):
        errmsg = "Expected can_handle to return True for Basic auth header"
        raise AssertionError(errmsg)
    
    return


def test_basic_authenticator_can_handle_case_insensitive():
    """
        Test that can_handle is case-insensitive for scheme.
    """
    provider = MockIdentityProvider()
    authenticator = BasicAuthenticator(provider)
    
    request = MockRequest(headers={"Authorization": "basic dXNlcjpwYXNz"})
    
    if not authenticator.can_handle(request):
        errmsg = "Expected can_handle to return True for lowercase 'basic'"
        raise AssertionError(errmsg)
    
    return


def test_basic_authenticator_can_handle_without_header():
    """
        Test that can_handle returns False when no Authorization header.
    """
    provider = MockIdentityProvider()
    authenticator = BasicAuthenticator(provider)
    
    request = MockRequest(headers={})
    
    if authenticator.can_handle(request):
        errmsg = "Expected can_handle to return False without Authorization header"
        raise AssertionError(errmsg)
    
    return


def test_basic_authenticator_can_handle_with_bearer_header():
    """
        Test that can_handle returns False for Bearer auth header.
    """
    provider = MockIdentityProvider()
    authenticator = BasicAuthenticator(provider)
    
    request = MockRequest(headers={"Authorization": "Bearer token123"})
    
    if authenticator.can_handle(request):
        errmsg = "Expected can_handle to return False for Bearer auth header"
        raise AssertionError(errmsg)
    
    return


def test_basic_authenticator_authenticate_valid_credentials():
    """
        Test authentication with valid credentials.
    """
    provider = MockIdentityProvider()
    provider.add_user("testuser", "testpass", display_name="Test User")
    authenticator = BasicAuthenticator(provider)
    
    auth_header = create_basic_auth_header("testuser", "testpass")
    request = MockRequest(headers={"Authorization": auth_header})
    
    result = run_async(authenticator.authenticate(request))
    
    if result.status != AuthenticationStatus.SUCCESS:
        errmsg = f"Expected SUCCESS status, got {result.status}"
        raise AssertionError(errmsg)
    
    if result.context is None:
        errmsg = "Expected context to be present on success"
        raise AssertionError(errmsg)
    
    if result.context.principal.identifier != "testuser":
        errmsg = f"Expected principal identifier 'testuser', got '{result.context.principal.identifier}'"
        raise AssertionError(errmsg)
    
    if result.context.scheme != "Basic":
        errmsg = f"Expected scheme 'Basic', got '{result.context.scheme}'"
        raise AssertionError(errmsg)
    
    return


def test_basic_authenticator_authenticate_invalid_password():
    """
        Test authentication with invalid password.
    """
    provider = MockIdentityProvider()
    provider.add_user("testuser", "correctpass")
    authenticator = BasicAuthenticator(provider)
    
    auth_header = create_basic_auth_header("testuser", "wrongpass")
    request = MockRequest(headers={"Authorization": auth_header})
    
    result = run_async(authenticator.authenticate(request))
    
    if result.status != AuthenticationStatus.FAILURE:
        errmsg = f"Expected FAILURE status, got {result.status}"
        raise AssertionError(errmsg)
    
    if result.error_code != "invalid_credentials":
        errmsg = f"Expected error_code 'invalid_credentials', got '{result.error_code}'"
        raise AssertionError(errmsg)
    
    return


def test_basic_authenticator_authenticate_unknown_user():
    """
        Test authentication with unknown username.
    """
    provider = MockIdentityProvider()
    provider.add_user("knownuser", "pass")
    authenticator = BasicAuthenticator(provider)
    
    auth_header = create_basic_auth_header("unknownuser", "pass")
    request = MockRequest(headers={"Authorization": auth_header})
    
    result = run_async(authenticator.authenticate(request))
    
    if result.status != AuthenticationStatus.FAILURE:
        errmsg = f"Expected FAILURE status, got {result.status}"
        raise AssertionError(errmsg)
    
    if result.error_code != "invalid_credentials":
        errmsg = f"Expected error_code 'invalid_credentials', got '{result.error_code}'"
        raise AssertionError(errmsg)
    
    return


def test_basic_authenticator_authenticate_no_header():
    """
        Test authentication without Authorization header returns challenge.
    """
    provider = MockIdentityProvider()
    authenticator = BasicAuthenticator(provider, realm="TestRealm")
    
    request = MockRequest(headers={})
    
    result = run_async(authenticator.authenticate(request))
    
    if result.status != AuthenticationStatus.CHALLENGE:
        errmsg = f"Expected CHALLENGE status, got {result.status}"
        raise AssertionError(errmsg)
    
    expected_challenge = 'Basic realm="TestRealm"'
    if result.challenge != expected_challenge:
        errmsg = f"Expected challenge '{expected_challenge}', got '{result.challenge}'"
        raise AssertionError(errmsg)
    
    return


def test_basic_authenticator_authenticate_malformed_base64():
    """
        Test authentication with invalid Base64 encoding.
    """
    provider = MockIdentityProvider()
    authenticator = BasicAuthenticator(provider)
    
    # Invalid Base64 string
    request = MockRequest(headers={"Authorization": "Basic not-valid-base64!!!"})
    
    result = run_async(authenticator.authenticate(request))
    
    if result.status != AuthenticationStatus.FAILURE:
        errmsg = f"Expected FAILURE status, got {result.status}"
        raise AssertionError(errmsg)
    
    if result.error_code != "bad_request":
        errmsg = f"Expected error_code 'bad_request', got '{result.error_code}'"
        raise AssertionError(errmsg)
    
    return


def test_basic_authenticator_authenticate_missing_colon():
    """
        Test authentication with credentials missing colon separator.
    """
    provider = MockIdentityProvider()
    authenticator = BasicAuthenticator(provider)
    
    # Base64 encode "userpassword" (no colon)
    encoded = base64.b64encode(b"userpassword").decode("utf-8")
    request = MockRequest(headers={"Authorization": f"Basic {encoded}"})
    
    result = run_async(authenticator.authenticate(request))
    
    if result.status != AuthenticationStatus.FAILURE:
        errmsg = f"Expected FAILURE status, got {result.status}"
        raise AssertionError(errmsg)
    
    if result.error_code != "bad_request":
        errmsg = f"Expected error_code 'bad_request', got '{result.error_code}'"
        raise AssertionError(errmsg)
    
    return


def test_basic_authenticator_authenticate_bearer_header_skips():
    """
        Test that Bearer auth header results in SKIP status.
    """
    provider = MockIdentityProvider()
    authenticator = BasicAuthenticator(provider)
    
    request = MockRequest(headers={"Authorization": "Bearer sometoken"})
    
    result = run_async(authenticator.authenticate(request))
    
    if result.status != AuthenticationStatus.SKIP:
        errmsg = f"Expected SKIP status for Bearer header, got {result.status}"
        raise AssertionError(errmsg)
    
    return


def test_basic_authenticator_authenticate_password_with_colons():
    """
        Test authentication with password containing colons.
    """
    provider = MockIdentityProvider()
    provider.add_user("user", "pass:with:colons")
    authenticator = BasicAuthenticator(provider)
    
    auth_header = create_basic_auth_header("user", "pass:with:colons")
    request = MockRequest(headers={"Authorization": auth_header})
    
    result = run_async(authenticator.authenticate(request))
    
    if result.status != AuthenticationStatus.SUCCESS:
        errmsg = f"Expected SUCCESS status, got {result.status}"
        raise AssertionError(errmsg)
    
    return


def test_basic_authenticator_with_dict_request():
    """
        Test that BasicAuthenticator works with dict-style request.
    """
    provider = MockIdentityProvider()
    provider.add_user("user", "pass")
    authenticator = BasicAuthenticator(provider)
    
    auth_header = create_basic_auth_header("user", "pass")
    request = {"headers": {"Authorization": auth_header}}
    
    result = run_async(authenticator.authenticate(request))
    
    if result.status != AuthenticationStatus.SUCCESS:
        errmsg = f"Expected SUCCESS status with dict request, got {result.status}"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Property-Based Tests
# =============================================================================

# Feature: authentication, Property 4: Basic Auth Credential Round-Trip
# *For any* valid username and password pair, encoding them as a Basic
# Authorization header and then extracting/decoding SHALL produce the
# original username and password.
# **Validates: Requirements 2.1, 2.2**

def test_property_4_basic_auth_credential_round_trip():
    """
        Property 4: Basic Auth Credential Round-Trip
        
        For any valid username and password pair, encoding them as a Basic
        Authorization header and then extracting/decoding SHALL produce the
        original username and password.
        
        **Validates: Requirements 2.1, 2.2**
    """
    # Run 100 iterations with random data
    for iteration in range(100):
        # Generate random username (no colons to avoid ambiguity)
        username = generate_random_username()
        # Generate random password (may contain colons)
        password = generate_random_password()
        
        # Encode as Basic auth header
        auth_header = create_basic_auth_header(username, password)
        
        # Verify header format
        if not auth_header.startswith("Basic "):
            errmsg = f"Iteration {iteration}: Header doesn't start with 'Basic '"
            raise AssertionError(errmsg)
        
        # Extract credentials part
        credentials_b64 = auth_header[6:]
        
        # Decode Base64
        try:
            decoded = base64.b64decode(credentials_b64).decode("utf-8")
        except Exception as e:
            errmsg = f"Iteration {iteration}: Failed to decode Base64: {e}"
            raise AssertionError(errmsg)
        
        # Split on first colon
        if ":" not in decoded:
            errmsg = f"Iteration {iteration}: Decoded credentials missing colon separator"
            raise AssertionError(errmsg)
        
        extracted_username, extracted_password = decoded.split(":", 1)
        
        # Verify round-trip
        if extracted_username != username:
            errmsg = f"Iteration {iteration}: Username mismatch. Expected '{username}', got '{extracted_username}'"
            raise AssertionError(errmsg)
        
        if extracted_password != password:
            errmsg = f"Iteration {iteration}: Password mismatch. Expected '{password}', got '{extracted_password}'"
            raise AssertionError(errmsg)
    
    return



# Feature: authentication, Property 5: Basic Auth Valid Credentials Produce Context
# *For any* request with valid Basic credentials where the Identity_Provider
# confirms the credentials, the Basic_Authenticator SHALL return SUCCESS with
# an Authentication_Context containing a Principal with the correct identifier.
# **Validates: Requirements 2.3, 2.4**

def test_property_5_basic_auth_valid_credentials_produce_context():
    """
        Property 5: Basic Auth Valid Credentials Produce Context
        
        For any request with valid Basic credentials where the Identity_Provider
        confirms the credentials, the Basic_Authenticator SHALL return SUCCESS
        with an Authentication_Context containing a Principal with the correct
        identifier.
        
        **Validates: Requirements 2.3, 2.4**
    """
    # Run 100 iterations with random data
    for iteration in range(100):
        # Generate random user credentials
        username = generate_random_username()
        password = generate_random_password()
        display_name = generate_random_string(1, 30)
        roles = generate_random_roles()
        permissions = generate_random_permissions()
        
        # Create identity provider with the user
        provider = MockIdentityProvider()
        provider.add_user(
            username=username,
            password=password,
            display_name=display_name,
            roles=roles,
            permissions=permissions
        )
        
        # Create authenticator
        authenticator = BasicAuthenticator(provider)
        
        # Create request with valid credentials
        auth_header = create_basic_auth_header(username, password)
        request = MockRequest(headers={"Authorization": auth_header})
        
        # Authenticate
        result = run_async(authenticator.authenticate(request))
        
        # Property: Status must be SUCCESS
        if result.status != AuthenticationStatus.SUCCESS:
            errmsg = f"Iteration {iteration}: Expected SUCCESS status, got {result.status}"
            raise AssertionError(errmsg)
        
        # Property: Context must be present
        if result.context is None:
            errmsg = f"Iteration {iteration}: Expected context to be present on success"
            raise AssertionError(errmsg)
        
        # Property: Principal identifier must match username
        if result.context.principal.identifier != username:
            errmsg = f"Iteration {iteration}: Expected principal identifier '{username}', got '{result.context.principal.identifier}'"
            raise AssertionError(errmsg)
        
        # Property: Scheme must be "Basic"
        if result.context.scheme != "Basic":
            errmsg = f"Iteration {iteration}: Expected scheme 'Basic', got '{result.context.scheme}'"
            raise AssertionError(errmsg)
        
        # Property: Principal must have the correct roles
        if result.context.principal.roles != roles:
            errmsg = f"Iteration {iteration}: Expected roles {roles}, got {result.context.principal.roles}"
            raise AssertionError(errmsg)
        
        # Property: Principal must have the correct permissions
        if result.context.principal.permissions != permissions:
            errmsg = f"Iteration {iteration}: Expected permissions {permissions}, got {result.context.principal.permissions}"
            raise AssertionError(errmsg)
    
    return


# Feature: authentication, Property 6: Basic Auth Invalid Credentials Produce 401
# *For any* request with Basic credentials where the Identity_Provider rejects
# the credentials, the Basic_Authenticator SHALL return FAILURE with error
# indicating invalid credentials.
# **Validates: Requirements 2.5**

def test_property_6_basic_auth_invalid_credentials_produce_401():
    """
        Property 6: Basic Auth Invalid Credentials Produce 401
        
        For any request with Basic credentials where the Identity_Provider
        rejects the credentials, the Basic_Authenticator SHALL return FAILURE
        with error indicating invalid credentials.
        
        **Validates: Requirements 2.5**
    """
    # Run 100 iterations with random data
    for iteration in range(100):
        # Generate random user credentials
        username = generate_random_username()
        correct_password = generate_random_password()
        wrong_password = generate_random_password()
        
        # Ensure wrong password is different
        while wrong_password == correct_password:
            wrong_password = generate_random_password()
        
        # Create identity provider with the user
        provider = MockIdentityProvider()
        provider.add_user(username=username, password=correct_password)
        
        # Create authenticator
        authenticator = BasicAuthenticator(provider)
        
        # Create request with WRONG password
        auth_header = create_basic_auth_header(username, wrong_password)
        request = MockRequest(headers={"Authorization": auth_header})
        
        # Authenticate
        result = run_async(authenticator.authenticate(request))
        
        # Property: Status must be FAILURE
        if result.status != AuthenticationStatus.FAILURE:
            errmsg = f"Iteration {iteration}: Expected FAILURE status for invalid password, got {result.status}"
            raise AssertionError(errmsg)
        
        # Property: Error code must indicate invalid credentials
        if result.error_code != "invalid_credentials":
            errmsg = f"Iteration {iteration}: Expected error_code 'invalid_credentials', got '{result.error_code}'"
            raise AssertionError(errmsg)
        
        # Property: Context must NOT be present
        if result.context is not None:
            errmsg = f"Iteration {iteration}: Expected no context on failure"
            raise AssertionError(errmsg)
    
    return


# Feature: authentication, Property 7: Basic Auth Malformed Header Produces Error
# *For any* Authorization header that starts with "Basic " but contains invalid
# Base64 or lacks the ":" separator, the Basic_Authenticator SHALL return
# FAILURE with a bad request error.
# **Validates: Requirements 2.6**

def test_property_7_basic_auth_malformed_header_produces_error():
    """
        Property 7: Basic Auth Malformed Header Produces Error
        
        For any Authorization header that starts with "Basic " but contains
        invalid Base64 or lacks the ":" separator, the Basic_Authenticator
        SHALL return FAILURE with a bad request error.
        
        **Validates: Requirements 2.6**
    """
    provider = MockIdentityProvider()
    authenticator = BasicAuthenticator(provider)
    
    # Run 100 iterations with random malformed data
    for iteration in range(100):
        # Randomly choose type of malformed header
        malform_type = random.choice(["invalid_base64", "missing_colon", "empty_credentials"])
        
        if malform_type == "invalid_base64":
            # Generate invalid Base64 string
            invalid_chars = "!@#$%^&*(){}[]|\\:;<>?/"
            invalid_b64 = ''.join(random.choices(invalid_chars, k=random.randint(5, 20)))
            auth_header = f"Basic {invalid_b64}"
            
        elif malform_type == "missing_colon":
            # Generate valid Base64 but without colon in decoded content
            no_colon_content = generate_random_username()  # No colons
            encoded = base64.b64encode(no_colon_content.encode("utf-8")).decode("utf-8")
            auth_header = f"Basic {encoded}"
            
        else:  # empty_credentials
            # Empty credentials after "Basic "
            auth_header = "Basic "
        
        request = MockRequest(headers={"Authorization": auth_header})
        
        # Authenticate
        result = run_async(authenticator.authenticate(request))
        
        # Property: Status must be FAILURE
        if result.status != AuthenticationStatus.FAILURE:
            errmsg = f"Iteration {iteration} ({malform_type}): Expected FAILURE status for malformed header, got {result.status}"
            raise AssertionError(errmsg)
        
        # Property: Error code must be bad_request
        if result.error_code != "bad_request":
            errmsg = f"Iteration {iteration} ({malform_type}): Expected error_code 'bad_request', got '{result.error_code}'"
            raise AssertionError(errmsg)
        
        # Property: Context must NOT be present
        if result.context is not None:
            errmsg = f"Iteration {iteration} ({malform_type}): Expected no context on malformed request"
            raise AssertionError(errmsg)
    
    return

