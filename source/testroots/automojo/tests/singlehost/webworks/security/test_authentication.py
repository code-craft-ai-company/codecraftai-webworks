"""
    Tests for authentication providers and the authentication manager.

    This module contains unit tests for the Authentication_Provider protocol,
    JWTAuthProvider, SessionAuthProvider, APIKeyAuthProvider, and
    Authentication_Manager classes.
"""

import base64
import hashlib
import hmac
import json
import time

from automojo.testbase.mocking import Mock

from automojo.webworks.security.authenticationprovider import (
    AuthenticationProvider,
    JWTAuthProvider,
    SessionAuthProvider,
    APIKeyAuthProvider,
)
from automojo.webworks.security.authenticationmanager import AuthenticationManager
from automojo.webworks.security.securitycontext import SecurityContext


# =============================================================================
# Test Helpers
# =============================================================================

TEST_SECRET_KEY = "test-secret-key-for-unit-tests"


def _create_jwt_token(payload: dict, secret_key: str = TEST_SECRET_KEY, algorithm: str = "HS256") -> str:
    """
        Create a JWT token for testing purposes.

        :param payload: The claims dictionary to encode.
        :param secret_key: The secret key for signing.
        :param algorithm: The signing algorithm.

        :returns: A signed JWT token string.
    """
    header = {"alg": algorithm, "typ": "JWT"}
    header_bytes = json.dumps(header, separators=(",", ":")).encode("utf-8")
    header_b64 = base64.urlsafe_b64encode(header_bytes).rstrip(b"=").decode("utf-8")

    payload_bytes = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    payload_b64 = base64.urlsafe_b64encode(payload_bytes).rstrip(b"=").decode("utf-8")

    signing_input = f"{header_b64}.{payload_b64}"

    algorithm_map = {
        "HS256": hashlib.sha256,
        "HS384": hashlib.sha384,
        "HS512": hashlib.sha512,
    }
    hash_func = algorithm_map[algorithm]
    signature = hmac.new(secret_key.encode("utf-8"), signing_input.encode("utf-8"), hash_func).digest()
    signature_b64 = base64.urlsafe_b64encode(signature).rstrip(b"=").decode("utf-8")

    rtnval = f"{header_b64}.{payload_b64}.{signature_b64}"
    return rtnval


def _create_mock_request(headers: dict = None, cookies: dict = None, query_params: dict = None) -> Mock:
    """
        Create a mock request object with the given attributes.

        :param headers: Dictionary of request headers.
        :param cookies: Dictionary of request cookies.
        :param query_params: Dictionary of query parameters.

        :returns: A Mock object configured as a request.
    """
    mock_request = Mock()
    ctx = mock_request.mock_context()

    if headers is not None:
        ctx.set_attribute("headers", headers)
    else:
        ctx.set_attribute("headers", {})

    if cookies is not None:
        ctx.set_attribute("cookies", cookies)

    if query_params is not None:
        ctx.set_attribute("query_params", query_params)

    return mock_request


def _create_mock_store(data: dict = None) -> Mock:
    """
        Create a mock store object with a get() method.

        :param data: Dictionary mapping keys to their stored data.

        :returns: A Mock object configured as a store.
    """
    if data is None:
        data = {}

    mock_store = Mock()
    mock_store.configure(recursive=True)

    def get_side_effect(key):
        rtnval = data.get(key)
        return rtnval

    mock_store.mock_context().mock_method("get", side_effect=get_side_effect)

    return mock_store


# =============================================================================
# Unit Tests for Authentication_Provider Protocol
# =============================================================================

def test_jwt_provider_implements_protocol():
    """
        Test that JWTAuthProvider satisfies the Authentication_Provider protocol.
    """
    provider = JWTAuthProvider(secret_key=TEST_SECRET_KEY)

    is_instance = isinstance(provider, AuthenticationProvider)
    if is_instance is not True:
        errmsg = "JWTAuthProvider should implement Authentication_Provider protocol"
        raise AssertionError(errmsg)

    return


def test_session_provider_implements_protocol():
    """
        Test that SessionAuthProvider satisfies the Authentication_Provider protocol.
    """
    store = _create_mock_store()
    provider = SessionAuthProvider(session_store=store)

    is_instance = isinstance(provider, AuthenticationProvider)
    if is_instance is not True:
        errmsg = "SessionAuthProvider should implement Authentication_Provider protocol"
        raise AssertionError(errmsg)

    return


def test_api_key_provider_implements_protocol():
    """
        Test that APIKeyAuthProvider satisfies the Authentication_Provider protocol.
    """
    store = _create_mock_store()
    provider = APIKeyAuthProvider(key_store=store)

    is_instance = isinstance(provider, AuthenticationProvider)
    if is_instance is not True:
        errmsg = "APIKeyAuthProvider should implement Authentication_Provider protocol"
        raise AssertionError(errmsg)

    return


def test_provider_protocol_has_name_and_priority():
    """
        Test that providers expose name and priority properties.
    """
    jwt_provider = JWTAuthProvider(secret_key=TEST_SECRET_KEY, priority=5)

    name = jwt_provider.name
    if name != "jwt":
        errmsg = f"Expected JWT provider name to be 'jwt', got '{name}'"
        raise AssertionError(errmsg)

    priority = jwt_provider.priority
    if priority != 5:
        errmsg = f"Expected JWT provider priority to be 5, got {priority}"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for JWTAuthProvider
# =============================================================================

def test_jwt_provider_authenticates_valid_token():
    """
        Test that JWTAuthProvider returns a Security_Context for a valid JWT.
    """
    payload = {
        "sub": "user-123",
        "username": "testuser",
        "email": "test@example.com",
        "roles": ["admin", "editor"],
        "scopes": ["read", "write"],
        "exp": time.time() + 3600,
        "iat": time.time(),
    }
    token = _create_jwt_token(payload)
    request = _create_mock_request(headers={"Authorization": f"Bearer {token}"})

    provider = JWTAuthProvider(secret_key=TEST_SECRET_KEY)
    result = provider.authenticate(request)

    if result is None:
        errmsg = "Expected a Security_Context, got None"
        raise AssertionError(errmsg)

    if result.user_id != "user-123":
        errmsg = f"Expected user_id 'user-123', got '{result.user_id}'"
        raise AssertionError(errmsg)

    if result.username != "testuser":
        errmsg = f"Expected username 'testuser', got '{result.username}'"
        raise AssertionError(errmsg)

    if result.provider != "jwt":
        errmsg = f"Expected provider 'jwt', got '{result.provider}'"
        raise AssertionError(errmsg)

    if "admin" not in result.roles:
        errmsg = f"Expected 'admin' in roles, got {result.roles}"
        raise AssertionError(errmsg)

    if "read" not in result.scopes:
        errmsg = f"Expected 'read' in scopes, got {result.scopes}"
        raise AssertionError(errmsg)

    return


def test_jwt_provider_returns_none_for_missing_header():
    """
        Test that JWTAuthProvider returns None when Authorization header is missing.
    """
    request = _create_mock_request(headers={})

    provider = JWTAuthProvider(secret_key=TEST_SECRET_KEY)
    result = provider.authenticate(request)

    if result is not None:
        errmsg = f"Expected None for missing header, got {result}"
        raise AssertionError(errmsg)

    return


def test_jwt_provider_returns_none_for_invalid_prefix():
    """
        Test that JWTAuthProvider returns None when the header prefix is wrong.
    """
    request = _create_mock_request(headers={"Authorization": "Basic some-token"})

    provider = JWTAuthProvider(secret_key=TEST_SECRET_KEY)
    result = provider.authenticate(request)

    if result is not None:
        errmsg = f"Expected None for invalid prefix, got {result}"
        raise AssertionError(errmsg)

    return


def test_jwt_provider_returns_none_for_invalid_signature():
    """
        Test that JWTAuthProvider returns None when the JWT signature is invalid.
    """
    payload = {"sub": "user-123"}
    token = _create_jwt_token(payload, secret_key="wrong-secret")
    request = _create_mock_request(headers={"Authorization": f"Bearer {token}"})

    provider = JWTAuthProvider(secret_key=TEST_SECRET_KEY)
    result = provider.authenticate(request)

    if result is not None:
        errmsg = f"Expected None for invalid signature, got {result}"
        raise AssertionError(errmsg)

    return


def test_jwt_provider_returns_none_for_expired_token():
    """
        Test that JWTAuthProvider returns None when the JWT has expired.
    """
    payload = {
        "sub": "user-123",
        "exp": time.time() - 3600,
    }
    token = _create_jwt_token(payload)
    request = _create_mock_request(headers={"Authorization": f"Bearer {token}"})

    provider = JWTAuthProvider(secret_key=TEST_SECRET_KEY)
    result = provider.authenticate(request)

    if result is not None:
        errmsg = f"Expected None for expired token, got {result}"
        raise AssertionError(errmsg)

    return


def test_jwt_provider_returns_none_for_missing_sub_claim():
    """
        Test that JWTAuthProvider returns None when the sub claim is missing.
    """
    payload = {"username": "testuser"}
    token = _create_jwt_token(payload)
    request = _create_mock_request(headers={"Authorization": f"Bearer {token}"})

    provider = JWTAuthProvider(secret_key=TEST_SECRET_KEY)
    result = provider.authenticate(request)

    if result is not None:
        errmsg = f"Expected None for missing sub claim, got {result}"
        raise AssertionError(errmsg)

    return


def test_jwt_provider_returns_none_for_malformed_token():
    """
        Test that JWTAuthProvider returns None for a malformed token string.
    """
    request = _create_mock_request(headers={"Authorization": "Bearer not.a.valid.jwt"})

    provider = JWTAuthProvider(secret_key=TEST_SECRET_KEY)
    result = provider.authenticate(request)

    if result is not None:
        errmsg = f"Expected None for malformed token, got {result}"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for SessionAuthProvider
# =============================================================================

def test_session_provider_authenticates_valid_session():
    """
        Test that SessionAuthProvider returns a Security_Context for a valid session.
    """
    session_data = {
        "valid-session-id": {
            "user_id": "user-456",
            "username": "sessionuser",
            "email": "session@example.com",
            "roles": ["viewer"],
            "scopes": ["read"],
        }
    }
    store = _create_mock_store(data=session_data)
    provider = SessionAuthProvider(session_store=store)

    request = _create_mock_request(cookies={"session_id": "valid-session-id"})
    result = provider.authenticate(request)

    if result is None:
        errmsg = "Expected a Security_Context, got None"
        raise AssertionError(errmsg)

    if result.user_id != "user-456":
        errmsg = f"Expected user_id 'user-456', got '{result.user_id}'"
        raise AssertionError(errmsg)

    if result.provider != "session":
        errmsg = f"Expected provider 'session', got '{result.provider}'"
        raise AssertionError(errmsg)

    return


def test_session_provider_returns_none_for_missing_cookie():
    """
        Test that SessionAuthProvider returns None when the cookie is missing.
    """
    store = _create_mock_store()
    provider = SessionAuthProvider(session_store=store)

    request = _create_mock_request(cookies={})
    result = provider.authenticate(request)

    if result is not None:
        errmsg = f"Expected None for missing cookie, got {result}"
        raise AssertionError(errmsg)

    return


def test_session_provider_returns_none_for_no_cookies_attribute():
    """
        Test that SessionAuthProvider returns None when request has no cookies attribute.
    """
    store = _create_mock_store()
    provider = SessionAuthProvider(session_store=store)

    request = _create_mock_request()
    result = provider.authenticate(request)

    if result is not None:
        errmsg = f"Expected None for no cookies attribute, got {result}"
        raise AssertionError(errmsg)

    return


def test_session_provider_returns_none_for_invalid_session():
    """
        Test that SessionAuthProvider returns None when the session is not found in the store.
    """
    store = _create_mock_store(data={})
    provider = SessionAuthProvider(session_store=store)

    request = _create_mock_request(cookies={"session_id": "nonexistent-session"})
    result = provider.authenticate(request)

    if result is not None:
        errmsg = f"Expected None for invalid session, got {result}"
        raise AssertionError(errmsg)

    return


def test_session_provider_returns_none_for_session_without_user_id():
    """
        Test that SessionAuthProvider returns None when session data has no user_id.
    """
    session_data = {
        "bad-session": {"username": "nouser"}
    }
    store = _create_mock_store(data=session_data)
    provider = SessionAuthProvider(session_store=store)

    request = _create_mock_request(cookies={"session_id": "bad-session"})
    result = provider.authenticate(request)

    if result is not None:
        errmsg = f"Expected None for session without user_id, got {result}"
        raise AssertionError(errmsg)

    return


def test_session_provider_custom_cookie_name():
    """
        Test that SessionAuthProvider uses a custom cookie name.
    """
    session_data = {
        "my-session": {
            "user_id": "user-789",
            "username": "customcookie",
        }
    }
    store = _create_mock_store(data=session_data)
    provider = SessionAuthProvider(session_store=store, cookie_name="my_session")

    request = _create_mock_request(cookies={"my_session": "my-session"})
    result = provider.authenticate(request)

    if result is None:
        errmsg = "Expected a Security_Context for custom cookie name, got None"
        raise AssertionError(errmsg)

    if result.user_id != "user-789":
        errmsg = f"Expected user_id 'user-789', got '{result.user_id}'"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for APIKeyAuthProvider
# =============================================================================

def test_api_key_provider_authenticates_from_header():
    """
        Test that APIKeyAuthProvider returns a Security_Context for a valid API key in header.
    """
    key_data = {
        "valid-api-key-123": {
            "user_id": "service-001",
            "username": "api-service",
            "roles": ["service"],
            "scopes": ["read", "write"],
        }
    }
    store = _create_mock_store(data=key_data)
    provider = APIKeyAuthProvider(key_store=store)

    request = _create_mock_request(headers={"X-API-Key": "valid-api-key-123"})
    result = provider.authenticate(request)

    if result is None:
        errmsg = "Expected a Security_Context, got None"
        raise AssertionError(errmsg)

    if result.user_id != "service-001":
        errmsg = f"Expected user_id 'service-001', got '{result.user_id}'"
        raise AssertionError(errmsg)

    if result.provider != "api_key":
        errmsg = f"Expected provider 'api_key', got '{result.provider}'"
        raise AssertionError(errmsg)

    return


def test_api_key_provider_authenticates_from_query_param():
    """
        Test that APIKeyAuthProvider falls back to query parameter.
    """
    key_data = {
        "query-key-456": {
            "user_id": "service-002",
            "username": "query-service",
        }
    }
    store = _create_mock_store(data=key_data)
    provider = APIKeyAuthProvider(key_store=store)

    request = _create_mock_request(
        headers={},
        query_params={"api_key": "query-key-456"}
    )
    result = provider.authenticate(request)

    if result is None:
        errmsg = "Expected a Security_Context from query param, got None"
        raise AssertionError(errmsg)

    if result.user_id != "service-002":
        errmsg = f"Expected user_id 'service-002', got '{result.user_id}'"
        raise AssertionError(errmsg)

    return


def test_api_key_provider_returns_none_for_missing_key():
    """
        Test that APIKeyAuthProvider returns None when no API key is provided.
    """
    store = _create_mock_store()
    provider = APIKeyAuthProvider(key_store=store)

    request = _create_mock_request(headers={})
    result = provider.authenticate(request)

    if result is not None:
        errmsg = f"Expected None for missing key, got {result}"
        raise AssertionError(errmsg)

    return


def test_api_key_provider_returns_none_for_invalid_key():
    """
        Test that APIKeyAuthProvider returns None when the key is not in the store.
    """
    store = _create_mock_store(data={})
    provider = APIKeyAuthProvider(key_store=store)

    request = _create_mock_request(headers={"X-API-Key": "nonexistent-key"})
    result = provider.authenticate(request)

    if result is not None:
        errmsg = f"Expected None for invalid key, got {result}"
        raise AssertionError(errmsg)

    return


def test_api_key_provider_header_takes_precedence_over_query():
    """
        Test that the header API key is used when both header and query param are present.
    """
    key_data = {
        "header-key": {
            "user_id": "header-user",
            "username": "from-header",
        },
        "query-key": {
            "user_id": "query-user",
            "username": "from-query",
        },
    }
    store = _create_mock_store(data=key_data)
    provider = APIKeyAuthProvider(key_store=store)

    request = _create_mock_request(
        headers={"X-API-Key": "header-key"},
        query_params={"api_key": "query-key"}
    )
    result = provider.authenticate(request)

    if result is None:
        errmsg = "Expected a Security_Context, got None"
        raise AssertionError(errmsg)

    if result.user_id != "header-user":
        errmsg = f"Expected header key to take precedence, got user_id '{result.user_id}'"
        raise AssertionError(errmsg)

    return


def test_api_key_provider_query_param_disabled():
    """
        Test that APIKeyAuthProvider does not check query params when query_param is None.
    """
    key_data = {
        "query-only-key": {
            "user_id": "query-user",
        }
    }
    store = _create_mock_store(data=key_data)
    provider = APIKeyAuthProvider(key_store=store, query_param=None)

    request = _create_mock_request(
        headers={},
        query_params={"api_key": "query-only-key"}
    )
    result = provider.authenticate(request)

    if result is not None:
        errmsg = f"Expected None when query_param is disabled, got {result}"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for Authentication_Manager
# =============================================================================

def test_manager_returns_guest_when_no_providers():
    """
        Test that Authentication_Manager returns a guest context when no providers are registered.
    """
    manager = AuthenticationManager()
    request = _create_mock_request()

    result = manager.authenticate(request)

    if result.is_authenticated is True:
        errmsg = "Expected guest context (not authenticated) when no providers registered"
        raise AssertionError(errmsg)

    return


def test_manager_returns_context_from_successful_provider():
    """
        Test that Authentication_Manager returns the context from the first successful provider.
    """
    payload = {
        "sub": "jwt-user",
        "exp": time.time() + 3600,
    }
    token = _create_jwt_token(payload)
    request = _create_mock_request(headers={"Authorization": f"Bearer {token}"})

    manager = AuthenticationManager()
    provider = JWTAuthProvider(secret_key=TEST_SECRET_KEY)
    manager.register_provider(provider)

    result = manager.authenticate(request)

    if result is None:
        errmsg = "Expected a Security_Context, got None"
        raise AssertionError(errmsg)

    if result.user_id != "jwt-user":
        errmsg = f"Expected user_id 'jwt-user', got '{result.user_id}'"
        raise AssertionError(errmsg)

    return


def test_manager_tries_providers_in_priority_order():
    """
        Test that Authentication_Manager tries providers in priority order (lower first).
    """
    session_data = {
        "sess-id": {
            "user_id": "session-user",
        }
    }
    session_store = _create_mock_store(data=session_data)

    key_data = {
        "api-key-val": {
            "user_id": "apikey-user",
        }
    }
    key_store = _create_mock_store(data=key_data)

    # API key provider has lower priority number (higher priority)
    api_provider = APIKeyAuthProvider(key_store=key_store, priority=5)
    session_provider = SessionAuthProvider(session_store=session_store, priority=20)

    manager = AuthenticationManager()
    # Register in reverse order to verify sorting
    manager.register_provider(session_provider)
    manager.register_provider(api_provider)

    # Request has both API key and session cookie
    request = _create_mock_request(
        headers={"X-API-Key": "api-key-val"},
        cookies={"session_id": "sess-id"}
    )

    result = manager.authenticate(request)

    if result.user_id != "apikey-user":
        errmsg = f"Expected API key provider (priority 5) to win, got user_id '{result.user_id}'"
        raise AssertionError(errmsg)

    return


def test_manager_falls_through_to_next_provider():
    """
        Test that Authentication_Manager tries the next provider when the first returns None.
    """
    session_data = {
        "valid-session": {
            "user_id": "session-user",
        }
    }
    session_store = _create_mock_store(data=session_data)

    # JWT provider will fail (no Authorization header)
    jwt_provider = JWTAuthProvider(secret_key=TEST_SECRET_KEY, priority=10)
    session_provider = SessionAuthProvider(session_store=session_store, priority=20)

    manager = AuthenticationManager()
    manager.register_provider(jwt_provider)
    manager.register_provider(session_provider)

    # Request only has session cookie, no JWT
    request = _create_mock_request(
        headers={},
        cookies={"session_id": "valid-session"}
    )

    result = manager.authenticate(request)

    if result.user_id != "session-user":
        errmsg = f"Expected fallthrough to session provider, got user_id '{result.user_id}'"
        raise AssertionError(errmsg)

    return


def test_manager_returns_guest_when_all_providers_fail():
    """
        Test that Authentication_Manager returns guest context when all providers fail.
    """
    jwt_provider = JWTAuthProvider(secret_key=TEST_SECRET_KEY, priority=10)
    store = _create_mock_store(data={})
    session_provider = SessionAuthProvider(session_store=store, priority=20)
    api_provider = APIKeyAuthProvider(key_store=store, priority=30)

    manager = AuthenticationManager()
    manager.register_provider(jwt_provider)
    manager.register_provider(session_provider)
    manager.register_provider(api_provider)

    # Request has no valid credentials
    request = _create_mock_request(headers={})

    result = manager.authenticate(request)

    if result.is_authenticated is True:
        errmsg = "Expected guest context when all providers fail"
        raise AssertionError(errmsg)

    return


def test_manager_providers_property_returns_sorted_list():
    """
        Test that the providers property returns providers sorted by priority.
    """
    store = _create_mock_store()

    provider_a = APIKeyAuthProvider(key_store=store, priority=30)
    provider_b = JWTAuthProvider(secret_key=TEST_SECRET_KEY, priority=10)
    provider_c = SessionAuthProvider(session_store=store, priority=20)

    manager = AuthenticationManager()
    manager.register_provider(provider_a)
    manager.register_provider(provider_b)
    manager.register_provider(provider_c)

    providers = manager.providers
    if len(providers) != 3:
        errmsg = f"Expected 3 providers, got {len(providers)}"
        raise AssertionError(errmsg)

    if providers[0].priority != 10:
        errmsg = f"Expected first provider priority 10, got {providers[0].priority}"
        raise AssertionError(errmsg)

    if providers[1].priority != 20:
        errmsg = f"Expected second provider priority 20, got {providers[1].priority}"
        raise AssertionError(errmsg)

    if providers[2].priority != 30:
        errmsg = f"Expected third provider priority 30, got {providers[2].priority}"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Property-Based Tests for Authentication Provider Chain
# **Validates: Requirements 4.4, 4.7, 4.8**
# =============================================================================

import random
import string


def _random_string(min_length=1, max_length=20):
    """
        Generate a random alphanumeric string.
    """
    length = random.randint(min_length, max_length)
    rtnval = "".join(random.choices(string.ascii_lowercase + string.digits, k=length))
    return rtnval


class _MockProvider:
    """
        A mock authentication provider that tracks whether authenticate was called
        and returns a configurable result.

        :param name: The provider name.
        :param priority: The provider priority (lower = higher priority).
        :param result: The Security_Context to return, or None to indicate failure.
    """

    def __init__(self, name: str, priority: int, result):
        self._name = name
        self._priority = priority
        self._result = result
        self.called = False
        return

    @property
    def name(self) -> str:
        return self._name

    @property
    def priority(self) -> int:
        return self._priority

    def authenticate(self, request):
        self.called = True
        return self._result

    async def authenticate_async(self, request):
        self.called = True
        return self._result


def _generate_random_provider_chain():
    """
        Generate a random set of mock providers with random priorities and
        random success/failure outcomes.

        :returns: A tuple of (providers_list, expected_result_user_id_or_none,
            expected_called_indices) where providers_list is sorted by priority.
    """
    num_providers = random.randint(1, 5)

    # Generate unique priorities
    priorities = random.sample(range(1, 100), num_providers)

    providers = []
    for idx in range(num_providers):
        provider_name = f"provider-{_random_string(3, 8)}"
        priority = priorities[idx]
        will_succeed = random.random() < 0.4

        if will_succeed:
            user_id = f"user-{_random_string(4, 10)}"
            result = SecurityContext(
                user_id=user_id,
                provider=provider_name,
                roles=tuple(),
                scopes=tuple()
            )
        else:
            user_id = None
            result = None

        provider = _MockProvider(name=provider_name, priority=priority, result=result)
        providers.append((provider, user_id))

    # Sort by priority (lower first) to determine expected behavior
    providers.sort(key=lambda item: item[0].priority)

    # Determine expected outcome: first provider in priority order that succeeds
    expected_user_id = None
    expected_called_count = 0
    for provider, user_id in providers:
        expected_called_count += 1
        if user_id is not None:
            expected_user_id = user_id
            break

    return providers, expected_user_id, expected_called_count


def test_property_authentication_provider_chain():
    """
        Property 4: Authentication Provider Chain.

        For any set of registered Authentication_Providers and any request:
        - Providers SHALL be tried in priority order (lower priority number first)
        - If a provider returns a Security_Context, subsequent providers SHALL NOT be called
        - If a provider returns None, the next provider SHALL be tried
        - If all providers return None, a guest Security_Context SHALL be returned

        **Validates: Requirements 4.4, 4.7, 4.8**
    """
    num_iterations = 100

    for iteration in range(num_iterations):
        providers_with_ids, expected_user_id, expected_called_count = _generate_random_provider_chain()

        manager = AuthenticationManager()
        mock_providers = []

        # Register providers in random order to verify sorting
        shuffled = list(providers_with_ids)
        random.shuffle(shuffled)
        for provider, _ in shuffled:
            manager.register_provider(provider)

        mock_providers = [p for p, _ in providers_with_ids]

        request = _create_mock_request()
        result = manager.authenticate(request)

        # Verify priority ordering: providers list should be sorted by priority
        registered = manager.providers
        for reg_idx in range(len(registered) - 1):
            if registered[reg_idx].priority > registered[reg_idx + 1].priority:
                errmsg = (
                    f"Iteration {iteration}: Providers not in priority order. "
                    f"Provider at index {reg_idx} has priority {registered[reg_idx].priority} "
                    f"but next has {registered[reg_idx + 1].priority}"
                )
                raise AssertionError(errmsg)

        # Verify the correct result
        if expected_user_id is not None:
            # A provider succeeded: result should be that provider's context
            if result.user_id != expected_user_id:
                errmsg = (
                    f"Iteration {iteration}: Expected user_id '{expected_user_id}', "
                    f"got '{result.user_id}'. Providers (priority, succeeds): "
                    f"{[(p.priority, p._result is not None) for p in mock_providers]}"
                )
                raise AssertionError(errmsg)

            if result.is_authenticated is not True:
                errmsg = (
                    f"Iteration {iteration}: Expected authenticated context "
                    f"but is_authenticated is False"
                )
                raise AssertionError(errmsg)
        else:
            # All providers failed: result should be a guest context
            if result.is_authenticated is True:
                errmsg = (
                    f"Iteration {iteration}: Expected guest context when all "
                    f"providers fail, but got authenticated context with "
                    f"user_id='{result.user_id}'"
                )
                raise AssertionError(errmsg)

        # Verify short-circuit behavior: only providers up to and including
        # the first successful one should have been called
        for call_idx, provider in enumerate(mock_providers):
            if call_idx < expected_called_count:
                if provider.called is not True:
                    errmsg = (
                        f"Iteration {iteration}: Provider '{provider.name}' at "
                        f"priority {provider.priority} (index {call_idx}) should "
                        f"have been called but was not"
                    )
                    raise AssertionError(errmsg)
            else:
                if provider.called is True:
                    errmsg = (
                        f"Iteration {iteration}: Provider '{provider.name}' at "
                        f"priority {provider.priority} (index {call_idx}) should "
                        f"NOT have been called after a successful provider"
                    )
                    raise AssertionError(errmsg)

    return
