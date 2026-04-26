"""
    Tests for the APIKeyAuthenticator module.
    
    This module contains unit tests and property-based tests for the
    APIKeyAuthenticator class and related utility functions.
"""

import asyncio
import random
import string
from typing import Any, Dict, Optional, Set

from automojo.webworks.authentication import (
    AuthenticationStatus,
    AuthenticationResult,
    Principal,
    AuthenticationContext,
    APIKeyAuthenticator,
    APIKeyLocation,
    extract_api_key
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


def generate_random_api_key() -> str:
    """
        Generate a random API key string.
    """
    length = random.randint(16, 64)
    chars = string.ascii_letters + string.digits
    return ''.join(random.choices(chars, k=length))


def generate_random_key_name() -> str:
    """
        Generate a random key name for headers/query params/cookies.
    """
    prefixes = ["X-API-Key", "X-Auth-Token", "api_key", "apikey", "token", "key"]
    if random.random() < 0.5:
        return random.choice(prefixes)
    else:
        length = random.randint(3, 20)
        chars = string.ascii_letters + string.digits + "_-"
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
# Mock API Key Store
# =============================================================================

class MockAPIKeyStore:
    """
        A mock API key store for testing APIKeyAuthenticator.
        
        This store maintains a mapping of API keys to their metadata.
    """
    
    def __init__(self):
        self._keys: Dict[str, Dict[str, Any]] = {}
    
    def add_key(
        self,
        api_key: str,
        client_id: Optional[str] = None,
        name: Optional[str] = None,
        roles: Optional[Set[str]] = None,
        permissions: Optional[Set[str]] = None,
        **extra_attrs
    ) -> Dict[str, Any]:
        """
            Add an API key to the store.
            
            :returns: The key metadata dictionary.
        """
        key_info = {
            "client_id": client_id or f"client_{api_key[:8]}",
            "name": name,
            "roles": list(roles) if roles else [],
            "permissions": list(permissions) if permissions else [],
            **extra_attrs
        }
        self._keys[api_key] = key_info
        return key_info
    
    async def validate_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """
            Validate an API key and return its metadata if valid.
        """
        return self._keys.get(api_key)


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
        query_params: Optional[Dict[str, str]] = None,
        cookies: Optional[Dict[str, str]] = None
    ):
        self.headers = headers or {}
        self.query_params = query_params or {}
        self.cookies = cookies or {}


# =============================================================================
# Helper Functions
# =============================================================================

def run_async(coro):
    """
        Run an async coroutine synchronously for testing.
    """
    return asyncio.get_event_loop().run_until_complete(coro)


# =============================================================================
# Unit Tests for APIKeyLocation
# =============================================================================

def test_apikey_location_values():
    """
        Test that APIKeyLocation enum has expected values.
    """
    if APIKeyLocation.HEADER.value != "header":
        errmsg = f"Expected HEADER value 'header', got '{APIKeyLocation.HEADER.value}'"
        raise AssertionError(errmsg)
    
    if APIKeyLocation.QUERY.value != "query":
        errmsg = f"Expected QUERY value 'query', got '{APIKeyLocation.QUERY.value}'"
        raise AssertionError(errmsg)
    
    if APIKeyLocation.COOKIE.value != "cookie":
        errmsg = f"Expected COOKIE value 'cookie', got '{APIKeyLocation.COOKIE.value}'"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for APIKeyAuthenticator
# =============================================================================

def test_apikey_authenticator_scheme():
    """
        Test that APIKeyAuthenticator returns "APIKey" as scheme.
    """
    store = MockAPIKeyStore()
    authenticator = APIKeyAuthenticator(store)
    
    if authenticator.scheme != "APIKey":
        errmsg = f"Expected scheme 'APIKey', got '{authenticator.scheme}'"
        raise AssertionError(errmsg)
    
    return


def test_apikey_authenticator_default_key_name():
    """
        Test that APIKeyAuthenticator has default key name "X-API-Key".
    """
    store = MockAPIKeyStore()
    authenticator = APIKeyAuthenticator(store)
    
    if authenticator.key_name != "X-API-Key":
        errmsg = f"Expected key_name 'X-API-Key', got '{authenticator.key_name}'"
        raise AssertionError(errmsg)
    
    return


def test_apikey_authenticator_default_location():
    """
        Test that APIKeyAuthenticator has default location HEADER.
    """
    store = MockAPIKeyStore()
    authenticator = APIKeyAuthenticator(store)
    
    if authenticator.location != APIKeyLocation.HEADER:
        errmsg = f"Expected location HEADER, got '{authenticator.location}'"
        raise AssertionError(errmsg)
    
    return


def test_apikey_authenticator_custom_key_name():
    """
        Test that APIKeyAuthenticator accepts custom key name.
    """
    store = MockAPIKeyStore()
    authenticator = APIKeyAuthenticator(store, key_name="My-Custom-Key")
    
    if authenticator.key_name != "My-Custom-Key":
        errmsg = f"Expected key_name 'My-Custom-Key', got '{authenticator.key_name}'"
        raise AssertionError(errmsg)
    
    return


def test_apikey_authenticator_custom_location():
    """
        Test that APIKeyAuthenticator accepts custom location.
    """
    store = MockAPIKeyStore()
    authenticator = APIKeyAuthenticator(store, location=APIKeyLocation.QUERY)
    
    if authenticator.location != APIKeyLocation.QUERY:
        errmsg = f"Expected location QUERY, got '{authenticator.location}'"
        raise AssertionError(errmsg)
    
    return


def test_apikey_authenticator_can_handle_with_header():
    """
        Test that can_handle returns True when API key is in header.
    """
    store = MockAPIKeyStore()
    authenticator = APIKeyAuthenticator(store)
    
    request = MockRequest(headers={"X-API-Key": "test-api-key-123"})
    
    if not authenticator.can_handle(request):
        errmsg = "Expected can_handle to return True when API key is in header"
        raise AssertionError(errmsg)
    
    return


def test_apikey_authenticator_can_handle_case_insensitive_header():
    """
        Test that can_handle is case-insensitive for header names.
    """
    store = MockAPIKeyStore()
    authenticator = APIKeyAuthenticator(store)
    
    request = MockRequest(headers={"x-api-key": "test-api-key-123"})
    
    if not authenticator.can_handle(request):
        errmsg = "Expected can_handle to return True for lowercase header name"
        raise AssertionError(errmsg)
    
    return


def test_apikey_authenticator_can_handle_without_key():
    """
        Test that can_handle returns False when no API key present.
    """
    store = MockAPIKeyStore()
    authenticator = APIKeyAuthenticator(store)
    
    request = MockRequest(headers={})
    
    if authenticator.can_handle(request):
        errmsg = "Expected can_handle to return False without API key"
        raise AssertionError(errmsg)
    
    return


def test_apikey_authenticator_can_handle_with_query():
    """
        Test that can_handle returns True when API key is in query params.
    """
    store = MockAPIKeyStore()
    authenticator = APIKeyAuthenticator(store, key_name="api_key", location=APIKeyLocation.QUERY)
    
    request = MockRequest(query_params={"api_key": "test-api-key-123"})
    
    if not authenticator.can_handle(request):
        errmsg = "Expected can_handle to return True when API key is in query params"
        raise AssertionError(errmsg)
    
    return


def test_apikey_authenticator_can_handle_with_cookie():
    """
        Test that can_handle returns True when API key is in cookie.
    """
    store = MockAPIKeyStore()
    authenticator = APIKeyAuthenticator(store, key_name="session_key", location=APIKeyLocation.COOKIE)
    
    request = MockRequest(cookies={"session_key": "test-api-key-123"})
    
    if not authenticator.can_handle(request):
        errmsg = "Expected can_handle to return True when API key is in cookie"
        raise AssertionError(errmsg)
    
    return


def test_apikey_authenticator_authenticate_valid_key():
    """
        Test authentication with valid API key.
    """
    store = MockAPIKeyStore()
    store.add_key(
        "valid-api-key-12345",
        client_id="client-001",
        name="Test Client",
        roles={"admin", "user"},
        permissions={"read", "write"}
    )
    authenticator = APIKeyAuthenticator(store)
    
    request = MockRequest(headers={"X-API-Key": "valid-api-key-12345"})
    
    result = run_async(authenticator.authenticate(request))
    
    if result.status != AuthenticationStatus.SUCCESS:
        errmsg = f"Expected SUCCESS status, got {result.status}"
        raise AssertionError(errmsg)
    
    if result.context is None:
        errmsg = "Expected context to be present on success"
        raise AssertionError(errmsg)
    
    if result.context.principal.identifier != "client-001":
        errmsg = f"Expected principal identifier 'client-001', got '{result.context.principal.identifier}'"
        raise AssertionError(errmsg)
    
    if result.context.scheme != "APIKey":
        errmsg = f"Expected scheme 'APIKey', got '{result.context.scheme}'"
        raise AssertionError(errmsg)
    
    return


def test_apikey_authenticator_authenticate_invalid_key():
    """
        Test authentication with invalid API key.
    """
    store = MockAPIKeyStore()
    store.add_key("valid-key", client_id="client-001")
    authenticator = APIKeyAuthenticator(store)
    
    request = MockRequest(headers={"X-API-Key": "invalid-key"})
    
    result = run_async(authenticator.authenticate(request))
    
    if result.status != AuthenticationStatus.FAILURE:
        errmsg = f"Expected FAILURE status, got {result.status}"
        raise AssertionError(errmsg)
    
    if result.error_code != "invalid_api_key":
        errmsg = f"Expected error_code 'invalid_api_key', got '{result.error_code}'"
        raise AssertionError(errmsg)
    
    return


def test_apikey_authenticator_authenticate_missing_key():
    """
        Test authentication with missing API key.
    """
    store = MockAPIKeyStore()
    authenticator = APIKeyAuthenticator(store)
    
    request = MockRequest(headers={})
    
    result = run_async(authenticator.authenticate(request))
    
    if result.status != AuthenticationStatus.FAILURE:
        errmsg = f"Expected FAILURE status, got {result.status}"
        raise AssertionError(errmsg)
    
    if result.error_code != "missing_api_key":
        errmsg = f"Expected error_code 'missing_api_key', got '{result.error_code}'"
        raise AssertionError(errmsg)
    
    return


def test_apikey_authenticator_authenticate_from_query():
    """
        Test authentication with API key from query parameter.
    """
    store = MockAPIKeyStore()
    store.add_key("query-api-key", client_id="query-client")
    authenticator = APIKeyAuthenticator(store, key_name="api_key", location=APIKeyLocation.QUERY)
    
    request = MockRequest(query_params={"api_key": "query-api-key"})
    
    result = run_async(authenticator.authenticate(request))
    
    if result.status != AuthenticationStatus.SUCCESS:
        errmsg = f"Expected SUCCESS status, got {result.status}"
        raise AssertionError(errmsg)
    
    if result.context.principal.identifier != "query-client":
        errmsg = f"Expected principal identifier 'query-client', got '{result.context.principal.identifier}'"
        raise AssertionError(errmsg)
    
    return


def test_apikey_authenticator_authenticate_from_cookie():
    """
        Test authentication with API key from cookie.
    """
    store = MockAPIKeyStore()
    store.add_key("cookie-api-key", client_id="cookie-client")
    authenticator = APIKeyAuthenticator(store, key_name="auth_token", location=APIKeyLocation.COOKIE)
    
    request = MockRequest(cookies={"auth_token": "cookie-api-key"})
    
    result = run_async(authenticator.authenticate(request))
    
    if result.status != AuthenticationStatus.SUCCESS:
        errmsg = f"Expected SUCCESS status, got {result.status}"
        raise AssertionError(errmsg)
    
    if result.context.principal.identifier != "cookie-client":
        errmsg = f"Expected principal identifier 'cookie-client', got '{result.context.principal.identifier}'"
        raise AssertionError(errmsg)
    
    return


def test_apikey_authenticator_with_dict_request():
    """
        Test that APIKeyAuthenticator works with dict-style request.
    """
    store = MockAPIKeyStore()
    store.add_key("dict-api-key", client_id="dict-client")
    authenticator = APIKeyAuthenticator(store)
    
    request = {"headers": {"X-API-Key": "dict-api-key"}}
    
    result = run_async(authenticator.authenticate(request))
    
    if result.status != AuthenticationStatus.SUCCESS:
        errmsg = f"Expected SUCCESS status with dict request, got {result.status}"
        raise AssertionError(errmsg)
    
    return


def test_apikey_authenticator_principal_roles_and_permissions():
    """
        Test that principal has correct roles and permissions.
    """
    store = MockAPIKeyStore()
    store.add_key(
        "role-key",
        client_id="role-client",
        roles={"admin", "editor"},
        permissions={"read", "write", "delete"}
    )
    authenticator = APIKeyAuthenticator(store)
    
    request = MockRequest(headers={"X-API-Key": "role-key"})
    
    result = run_async(authenticator.authenticate(request))
    
    if result.status != AuthenticationStatus.SUCCESS:
        errmsg = f"Expected SUCCESS status, got {result.status}"
        raise AssertionError(errmsg)
    
    principal = result.context.principal
    
    if principal.roles != {"admin", "editor"}:
        errmsg = f"Expected roles {{'admin', 'editor'}}, got {principal.roles}"
        raise AssertionError(errmsg)
    
    if principal.permissions != {"read", "write", "delete"}:
        errmsg = f"Expected permissions {{'read', 'write', 'delete'}}, got {principal.permissions}"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for extract_api_key utility
# =============================================================================

def test_extract_api_key_from_header():
    """
        Test extract_api_key utility function with header.
    """
    request = MockRequest(headers={"X-API-Key": "test-key-123"})
    
    key = extract_api_key(request)
    
    if key != "test-key-123":
        errmsg = f"Expected 'test-key-123', got '{key}'"
        raise AssertionError(errmsg)
    
    return


def test_extract_api_key_from_query():
    """
        Test extract_api_key utility function with query param.
    """
    request = MockRequest(query_params={"api_key": "query-key-456"})
    
    key = extract_api_key(request, key_name="api_key", location=APIKeyLocation.QUERY)
    
    if key != "query-key-456":
        errmsg = f"Expected 'query-key-456', got '{key}'"
        raise AssertionError(errmsg)
    
    return


def test_extract_api_key_from_cookie():
    """
        Test extract_api_key utility function with cookie.
    """
    request = MockRequest(cookies={"session": "cookie-key-789"})
    
    key = extract_api_key(request, key_name="session", location=APIKeyLocation.COOKIE)
    
    if key != "cookie-key-789":
        errmsg = f"Expected 'cookie-key-789', got '{key}'"
        raise AssertionError(errmsg)
    
    return


def test_extract_api_key_missing():
    """
        Test extract_api_key returns None when key is missing.
    """
    request = MockRequest(headers={})
    
    key = extract_api_key(request)
    
    if key is not None:
        errmsg = f"Expected None, got '{key}'"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Property-Based Tests
# =============================================================================

# Feature: authentication, Property 13: API Key Extraction from All Locations
# *For any* API key placed in a header, query parameter, or cookie with the
# configured key name, the API_Key_Authenticator SHALL extract the same key
# value regardless of location.
# **Validates: Requirements 5.1, 5.2, 5.3, 5.4**

def test_property_13_api_key_extraction_from_all_locations():
    """
        Property 13: API Key Extraction from All Locations
        
        For any API key placed in a header, query parameter, or cookie with
        the configured key name, the API_Key_Authenticator SHALL extract the
        same key value regardless of location.
        
        **Validates: Requirements 5.1, 5.2, 5.3, 5.4**
    """
    # Run 100 iterations with random data
    for iteration in range(100):
        # Generate random API key and key name
        api_key = generate_random_api_key()
        key_name = generate_random_key_name()
        
        # Create a store (not used for extraction, but required)
        store = MockAPIKeyStore()
        
        # Test extraction from HEADER
        header_authenticator = APIKeyAuthenticator(
            store, key_name=key_name, location=APIKeyLocation.HEADER
        )
        header_request = MockRequest(headers={key_name: api_key})
        header_extracted = header_authenticator._extract_key(header_request)
        
        if header_extracted != api_key:
            errmsg = f"Iteration {iteration}: Header extraction failed. Expected '{api_key}', got '{header_extracted}'"
            raise AssertionError(errmsg)
        
        # Test extraction from QUERY
        query_authenticator = APIKeyAuthenticator(
            store, key_name=key_name, location=APIKeyLocation.QUERY
        )
        query_request = MockRequest(query_params={key_name: api_key})
        query_extracted = query_authenticator._extract_key(query_request)
        
        if query_extracted != api_key:
            errmsg = f"Iteration {iteration}: Query extraction failed. Expected '{api_key}', got '{query_extracted}'"
            raise AssertionError(errmsg)
        
        # Test extraction from COOKIE
        cookie_authenticator = APIKeyAuthenticator(
            store, key_name=key_name, location=APIKeyLocation.COOKIE
        )
        cookie_request = MockRequest(cookies={key_name: api_key})
        cookie_extracted = cookie_authenticator._extract_key(cookie_request)
        
        if cookie_extracted != api_key:
            errmsg = f"Iteration {iteration}: Cookie extraction failed. Expected '{api_key}', got '{cookie_extracted}'"
            raise AssertionError(errmsg)
        
        # Property: All three extractions should yield the same key value
        if not (header_extracted == query_extracted == cookie_extracted == api_key):
            errmsg = f"Iteration {iteration}: Extraction inconsistency. Header: '{header_extracted}', Query: '{query_extracted}', Cookie: '{cookie_extracted}'"
            raise AssertionError(errmsg)
    
    return


# Feature: authentication, Property 14: Valid API Key Produces Context
# *For any* valid API key recognized by the key store, the API_Key_Authenticator
# SHALL return SUCCESS with an Authentication_Context.
# **Validates: Requirements 5.5, 5.6**

def test_property_14_valid_api_key_produces_context():
    """
        Property 14: Valid API Key Produces Context
        
        For any valid API key recognized by the key store, the
        API_Key_Authenticator SHALL return SUCCESS with an
        Authentication_Context.
        
        **Validates: Requirements 5.5, 5.6**
    """
    # Run 100 iterations with random data
    for iteration in range(100):
        # Generate random API key and metadata
        api_key = generate_random_api_key()
        client_id = generate_random_string(5, 20)
        name = generate_random_string(1, 30)
        roles = generate_random_roles()
        permissions = generate_random_permissions()
        
        # Create store with the key
        store = MockAPIKeyStore()
        store.add_key(
            api_key,
            client_id=client_id,
            name=name,
            roles=roles,
            permissions=permissions
        )
        
        # Randomly choose a location
        location = random.choice([APIKeyLocation.HEADER, APIKeyLocation.QUERY, APIKeyLocation.COOKIE])
        key_name = generate_random_key_name()
        
        authenticator = APIKeyAuthenticator(store, key_name=key_name, location=location)
        
        # Create request with key at the chosen location
        if location == APIKeyLocation.HEADER:
            request = MockRequest(headers={key_name: api_key})
        elif location == APIKeyLocation.QUERY:
            request = MockRequest(query_params={key_name: api_key})
        else:
            request = MockRequest(cookies={key_name: api_key})
        
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
        
        # Property: Principal identifier must match client_id
        if result.context.principal.identifier != client_id:
            errmsg = f"Iteration {iteration}: Expected principal identifier '{client_id}', got '{result.context.principal.identifier}'"
            raise AssertionError(errmsg)
        
        # Property: Scheme must be "APIKey"
        if result.context.scheme != "APIKey":
            errmsg = f"Iteration {iteration}: Expected scheme 'APIKey', got '{result.context.scheme}'"
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


# Feature: authentication, Property 15: Invalid API Key Produces 401
# *For any* API key not recognized by the key store, the API_Key_Authenticator
# SHALL return FAILURE.
# **Validates: Requirements 5.7**

def test_property_15_invalid_api_key_produces_401():
    """
        Property 15: Invalid API Key Produces 401
        
        For any API key not recognized by the key store, the
        API_Key_Authenticator SHALL return FAILURE.
        
        **Validates: Requirements 5.7**
    """
    # Run 100 iterations with random data
    for iteration in range(100):
        # Generate random valid and invalid API keys
        valid_key = generate_random_api_key()
        invalid_key = generate_random_api_key()
        
        # Ensure invalid key is different from valid key
        while invalid_key == valid_key:
            invalid_key = generate_random_api_key()
        
        # Create store with only the valid key
        store = MockAPIKeyStore()
        store.add_key(valid_key, client_id="valid-client")
        
        # Randomly choose a location
        location = random.choice([APIKeyLocation.HEADER, APIKeyLocation.QUERY, APIKeyLocation.COOKIE])
        key_name = generate_random_key_name()
        
        authenticator = APIKeyAuthenticator(store, key_name=key_name, location=location)
        
        # Create request with INVALID key at the chosen location
        if location == APIKeyLocation.HEADER:
            request = MockRequest(headers={key_name: invalid_key})
        elif location == APIKeyLocation.QUERY:
            request = MockRequest(query_params={key_name: invalid_key})
        else:
            request = MockRequest(cookies={key_name: invalid_key})
        
        # Authenticate
        result = run_async(authenticator.authenticate(request))
        
        # Property: Status must be FAILURE
        if result.status != AuthenticationStatus.FAILURE:
            errmsg = f"Iteration {iteration}: Expected FAILURE status for invalid key, got {result.status}"
            raise AssertionError(errmsg)
        
        # Property: Error code must indicate invalid API key
        if result.error_code != "invalid_api_key":
            errmsg = f"Iteration {iteration}: Expected error_code 'invalid_api_key', got '{result.error_code}'"
            raise AssertionError(errmsg)
        
        # Property: Context must NOT be present
        if result.context is not None:
            errmsg = f"Iteration {iteration}: Expected no context on failure"
            raise AssertionError(errmsg)

    return


# =============================================================================
# Empty / whitespace API key handling
# =============================================================================

def test_apikey_authenticator_treats_empty_string_header_as_missing():
    """
        Property: a request with an empty-string API key header
        (``X-API-Key: ``) yields FAILURE / missing_api_key, not
        a generic invalid_api_key. The intent is that the
        APIKeyStore should never see a blank key — the
        authenticator boundary normalizes it to a missing-key
        outcome.
    """
    store = MockAPIKeyStore()
    authenticator = APIKeyAuthenticator(
        key_store=store, key_name="X-API-Key",
    )
    request = MockRequest(headers={"X-API-Key": ""})
    result = run_async(authenticator.authenticate(request))

    if result.status != AuthenticationStatus.FAILURE:
        errmsg = f"Expected FAILURE, got {result.status}"
        raise AssertionError(errmsg)
    if result.error_code != "missing_api_key":
        errmsg = (
            "Expected error_code='missing_api_key' for empty "
            "header value, got '{}'".format(result.error_code)
        )
        raise AssertionError(errmsg)
    return


def test_apikey_authenticator_treats_whitespace_only_header_as_missing():
    """
        Property: a whitespace-only API key header value (e.g.
        "   " or "\\t\\n") is normalized to missing rather than
        passed through to the store. Whitespace-only keys
        survive the empty-string short-circuit in
        ``_extract_from_header`` (because " " is truthy in
        Python) — the authenticate() boundary catches them.
    """
    store = MockAPIKeyStore()
    authenticator = APIKeyAuthenticator(
        key_store=store, key_name="X-API-Key",
    )
    request = MockRequest(headers={"X-API-Key": "   \t  "})
    result = run_async(authenticator.authenticate(request))

    if result.status != AuthenticationStatus.FAILURE:
        errmsg = f"Expected FAILURE, got {result.status}"
        raise AssertionError(errmsg)
    if result.error_code != "missing_api_key":
        errmsg = (
            "Expected error_code='missing_api_key' for "
            "whitespace-only header value, got '{}'".format(
                result.error_code,
            )
        )
        raise AssertionError(errmsg)
    return


def test_apikey_authenticator_treats_whitespace_only_query_as_missing():
    """
        Property: a whitespace-only API key query parameter is
        also normalized to missing. The same property holds
        regardless of where the key was extracted from.
    """
    store = MockAPIKeyStore()
    authenticator = APIKeyAuthenticator(
        key_store=store,
        key_name="api_key",
        location=APIKeyLocation.QUERY,
    )
    request = MockRequest(query_params={"api_key": "  "})
    result = run_async(authenticator.authenticate(request))

    if result.error_code != "missing_api_key":
        errmsg = (
            "Expected error_code='missing_api_key' for "
            "whitespace-only query value, got '{}'".format(
                result.error_code,
            )
        )
        raise AssertionError(errmsg)
    return


def test_apikey_store_never_receives_blank_key():
    """
        Property: a malicious / misconfigured client supplying
        whitespace-only or empty-string API keys never reaches
        the APIKeyStore.validate_key call. Store implementors
        should be able to assume their input is a non-blank
        string.
    """
    received_keys = []

    class _RecordingStore:
        async def validate_key(
                self, api_key: str
            ) -> Optional[Dict[str, Any]]:
            received_keys.append(api_key)
            return None

    authenticator = APIKeyAuthenticator(
        key_store=_RecordingStore(), key_name="X-API-Key",
    )
    for blank_value in ("", " ", "\t", "\n", "  \t\n  "):
        request = MockRequest(headers={"X-API-Key": blank_value})
        run_async(authenticator.authenticate(request))

    if len(received_keys) > 0:
        errmsg = (
            "APIKeyStore.validate_key was called with blank "
            "values: {!r}".format(received_keys)
        )
        raise AssertionError(errmsg)
    return


def test_extract_api_key_helper_returns_none_for_whitespace():
    """
        Property: the standalone extract_api_key helper applies
        the same empty / whitespace normalization as the
        authenticator boundary, so callers using the helper
        independently see consistent None semantics.
    """
    request = MockRequest(headers={"X-API-Key": "   "})
    result = extract_api_key(request, key_name="X-API-Key")
    if result is not None:
        errmsg = (
            "Expected None from extract_api_key for "
            "whitespace-only header, got {!r}".format(result)
        )
        raise AssertionError(errmsg)
    return


def test_extract_api_key_helper_returns_value_for_non_blank():
    """
        Property: the standalone extract_api_key helper still
        passes through real API key values unchanged.
    """
    request = MockRequest(headers={"X-API-Key": "real-key-abc123"})
    result = extract_api_key(request, key_name="X-API-Key")
    if result != "real-key-abc123":
        errmsg = (
            "Expected 'real-key-abc123', got {!r}".format(result)
        )
        raise AssertionError(errmsg)
    return
