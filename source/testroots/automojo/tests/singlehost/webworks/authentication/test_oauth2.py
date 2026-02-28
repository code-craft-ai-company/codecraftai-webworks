"""
    Tests for the OAuth2Authenticator module.
    
    This module contains unit tests and property-based tests for the
    OAuth2Authenticator class and related utility functions.
"""

import asyncio
import random
import string
import time
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Set

from automojo.webworks.authentication import (
    AuthenticationStatus,
    AuthenticationResult,
    Principal,
    AuthenticationContext,
    OAuth2Authenticator,
    OAuth2AuthorizationCode,
    OAuth2Error,
    OAuth2GrantType,
    OAuth2Token,
    PKCEMethod,
    create_oauth2_error_response,
    generate_code_challenge,
    generate_code_verifier,
    generate_state,
    validate_state,
    verify_code_challenge
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


def generate_random_client_id() -> str:
    """
        Generate a random client ID.
    """
    return f"client_{generate_random_identifier()}"


def generate_random_client_secret() -> str:
    """
        Generate a random client secret.
    """
    length = random.randint(32, 64)
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(random.choices(chars, k=length))


def generate_random_redirect_uri() -> str:
    """
        Generate a random redirect URI.
    """
    domain = generate_random_string(5, 15)
    path = generate_random_string(3, 10)
    return f"https://{domain}.example.com/{path}/callback"


def generate_random_scope() -> Set[str]:
    """
        Generate a random set of scope strings.
    """
    num_scopes = random.randint(1, 5)
    scopes = ["read", "write", "delete", "admin", "profile", "email", "openid"]
    return set(random.sample(scopes, min(num_scopes, len(scopes))))


def generate_random_token() -> str:
    """
        Generate a random token string.
    """
    length = random.randint(32, 64)
    chars = string.ascii_letters + string.digits + "-_"
    return ''.join(random.choices(chars, k=length))


# =============================================================================
# Mock Stores
# =============================================================================

class MockOAuth2ClientStore:
    """
        A mock OAuth2 client store for testing.
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
        
        # If client has a secret, verify it
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


class MockOAuth2TokenStore:
    """
        A mock OAuth2 token store for testing.
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
    
    def add_refresh_token(
        self,
        token: str,
        client_id: str,
        user_id: Optional[str] = None,
        scope: Optional[Set[str]] = None,
        **kwargs
    ) -> None:
        """
            Add a refresh token to the store.
        """
        self._refresh_tokens[token] = {
            "refresh_token": token,
            "client_id": client_id,
            "user_id": user_id,
            "scope": scope,
            **kwargs
        }
    
    async def store_token(
        self,
        token: OAuth2Token,
        client_id: str,
        user_id: Optional[str] = None
    ) -> None:
        """
            Store an OAuth2 token.
        """
        expires_at = None
        if token.expires_in:
            expires_at = datetime.utcnow() + timedelta(seconds=token.expires_in)
        
        self._access_tokens[token.access_token] = {
            "access_token": token.access_token,
            "client_id": client_id,
            "user_id": user_id,
            "scope": token.scope,
            "expires_at": expires_at
        }
        
        if token.refresh_token:
            self._refresh_tokens[token.refresh_token] = {
                "refresh_token": token.refresh_token,
                "client_id": client_id,
                "user_id": user_id,
                "scope": token.scope
            }
    
    async def validate_access_token(
        self,
        access_token: str
    ) -> Optional[Dict[str, Any]]:
        """
            Validate an access token.
        """
        token_data = self._access_tokens.get(access_token)
        if token_data is None:
            return None
        
        # Check expiration
        expires_at = token_data.get("expires_at")
        if expires_at and datetime.utcnow() > expires_at:
            return None
        
        return token_data
    
    async def validate_refresh_token(
        self,
        refresh_token: str
    ) -> Optional[Dict[str, Any]]:
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
        if token in self._refresh_tokens:
            del self._refresh_tokens[token]
            return True
        return False


class MockOAuth2AuthorizationCodeStore:
    """
        A mock authorization code store for testing.
    """
    
    def __init__(self):
        self._codes: Dict[str, OAuth2AuthorizationCode] = {}
    
    def add_code(self, auth_code: OAuth2AuthorizationCode) -> None:
        """
            Add an authorization code to the store.
        """
        self._codes[auth_code.code] = auth_code
    
    async def store_code(self, auth_code: OAuth2AuthorizationCode) -> None:
        """
            Store an authorization code.
        """
        self._codes[auth_code.code] = auth_code
    
    async def get_code(self, code: str) -> Optional[OAuth2AuthorizationCode]:
        """
            Retrieve an authorization code.
        """
        return self._codes.get(code)
    
    async def delete_code(self, code: str) -> bool:
        """
            Delete an authorization code.
        """
        if code in self._codes:
            del self._codes[code]
            return True
        return False


class MockOAuth2UserAuthenticator:
    """
        A mock user authenticator for testing Password flow.
    """
    
    def __init__(self):
        self._users: Dict[str, Dict[str, Any]] = {}
    
    def add_user(
        self,
        username: str,
        password: str,
        user_id: Optional[str] = None,
        **kwargs
    ) -> None:
        """
            Add a user to the store.
        """
        self._users[username] = {
            "username": username,
            "password": password,
            "id": user_id or username,
            **kwargs
        }
    
    async def authenticate_user(
        self,
        username: str,
        password: str
    ) -> Optional[Dict[str, Any]]:
        """
            Authenticate a user.
        """
        user = self._users.get(username)
        if user is None:
            return None
        
        if user["password"] != password:
            return None
        
        # Return user info without password
        return {k: v for k, v in user.items() if k != "password"}


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
    return asyncio.get_event_loop().run_until_complete(coro)



# =============================================================================
# Unit Tests for PKCE Functions
# =============================================================================

def test_generate_code_verifier_default_length():
    """
        Test generating code verifier with default length.
    """
    verifier = generate_code_verifier()
    
    if len(verifier) != 64:
        errmsg = f"Expected length 64, got {len(verifier)}"
        raise AssertionError(errmsg)
    
    return


def test_generate_code_verifier_custom_length():
    """
        Test generating code verifier with custom length.
    """
    verifier = generate_code_verifier(length=43)
    
    if len(verifier) != 43:
        errmsg = f"Expected length 43, got {len(verifier)}"
        raise AssertionError(errmsg)
    
    return


def test_generate_code_verifier_invalid_length():
    """
        Test that invalid length raises ValueError.
    """
    try:
        generate_code_verifier(length=42)  # Too short
        raise AssertionError("Expected ValueError for length < 43")
    except ValueError:
        pass
    
    try:
        generate_code_verifier(length=129)  # Too long
        raise AssertionError("Expected ValueError for length > 128")
    except ValueError:
        pass
    
    return


def test_generate_code_challenge_plain():
    """
        Test generating code challenge with plain method.
    """
    verifier = "test_verifier_string"
    challenge = generate_code_challenge(verifier, PKCEMethod.PLAIN)
    
    if challenge != verifier:
        errmsg = f"Expected challenge to equal verifier for plain method"
        raise AssertionError(errmsg)
    
    return


def test_generate_code_challenge_s256():
    """
        Test generating code challenge with S256 method.
    """
    verifier = "test_verifier_string"
    challenge = generate_code_challenge(verifier, PKCEMethod.S256)
    
    # Challenge should be different from verifier
    if challenge == verifier:
        errmsg = "Expected challenge to differ from verifier for S256 method"
        raise AssertionError(errmsg)
    
    # Challenge should be base64url encoded (no padding)
    if '=' in challenge:
        errmsg = "Expected no padding in base64url encoded challenge"
        raise AssertionError(errmsg)
    
    return


def test_verify_code_challenge_plain():
    """
        Test verifying code challenge with plain method.
    """
    verifier = "test_verifier_string"
    challenge = verifier  # Plain method
    
    result = verify_code_challenge(verifier, challenge, "plain")
    
    if not result:
        errmsg = "Expected verification to succeed for plain method"
        raise AssertionError(errmsg)
    
    return


def test_verify_code_challenge_s256():
    """
        Test verifying code challenge with S256 method.
    """
    verifier = "test_verifier_string"
    challenge = generate_code_challenge(verifier, PKCEMethod.S256)
    
    result = verify_code_challenge(verifier, challenge, "S256")
    
    if not result:
        errmsg = "Expected verification to succeed for S256 method"
        raise AssertionError(errmsg)
    
    return


def test_verify_code_challenge_wrong_verifier():
    """
        Test that wrong verifier fails verification.
    """
    verifier = "correct_verifier"
    challenge = generate_code_challenge(verifier, PKCEMethod.S256)
    
    result = verify_code_challenge("wrong_verifier", challenge, "S256")
    
    if result:
        errmsg = "Expected verification to fail for wrong verifier"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for State Functions
# =============================================================================

def test_generate_state_default_length():
    """
        Test generating state with default length.
    """
    state = generate_state()
    
    if len(state) != 32:
        errmsg = f"Expected length 32, got {len(state)}"
        raise AssertionError(errmsg)
    
    return


def test_generate_state_custom_length():
    """
        Test generating state with custom length.
    """
    state = generate_state(length=64)
    
    if len(state) != 64:
        errmsg = f"Expected length 64, got {len(state)}"
        raise AssertionError(errmsg)
    
    return


def test_validate_state_matching():
    """
        Test validating matching state values.
    """
    state = generate_state()
    
    result = validate_state(state, state)
    
    if not result:
        errmsg = "Expected validation to succeed for matching states"
        raise AssertionError(errmsg)
    
    return


def test_validate_state_mismatched():
    """
        Test validating mismatched state values.
    """
    state1 = generate_state()
    state2 = generate_state()
    
    result = validate_state(state1, state2)
    
    if result:
        errmsg = "Expected validation to fail for mismatched states"
        raise AssertionError(errmsg)
    
    return


def test_validate_state_none():
    """
        Test validating None state value.
    """
    state = generate_state()
    
    result = validate_state(state, None)
    
    if result:
        errmsg = "Expected validation to fail for None state"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for OAuth2Token
# =============================================================================

def test_oauth2_token_to_dict():
    """
        Test converting OAuth2Token to dictionary.
    """
    token = OAuth2Token(
        access_token="access123",
        token_type="Bearer",
        expires_in=3600,
        refresh_token="refresh456",
        scope={"read", "write"}
    )
    
    result = token.to_dict()
    
    if result["access_token"] != "access123":
        errmsg = f"Expected access_token 'access123', got '{result['access_token']}'"
        raise AssertionError(errmsg)
    
    if result["token_type"] != "Bearer":
        errmsg = f"Expected token_type 'Bearer', got '{result['token_type']}'"
        raise AssertionError(errmsg)
    
    if result["expires_in"] != 3600:
        errmsg = f"Expected expires_in 3600, got {result['expires_in']}"
        raise AssertionError(errmsg)
    
    if result["refresh_token"] != "refresh456":
        errmsg = f"Expected refresh_token 'refresh456', got '{result['refresh_token']}'"
        raise AssertionError(errmsg)
    
    # Scope should be space-separated string
    scope_parts = set(result["scope"].split())
    if scope_parts != {"read", "write"}:
        errmsg = f"Expected scope 'read write', got '{result['scope']}'"
        raise AssertionError(errmsg)
    
    return


def test_oauth2_token_from_dict():
    """
        Test creating OAuth2Token from dictionary.
    """
    data = {
        "access_token": "access123",
        "token_type": "Bearer",
        "expires_in": 3600,
        "refresh_token": "refresh456",
        "scope": "read write"
    }
    
    token = OAuth2Token.from_dict(data)
    
    if token.access_token != "access123":
        errmsg = f"Expected access_token 'access123', got '{token.access_token}'"
        raise AssertionError(errmsg)
    
    if token.scope != {"read", "write"}:
        errmsg = f"Expected scope {{'read', 'write'}}, got {token.scope}"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for OAuth2Error
# =============================================================================

def test_oauth2_error_to_dict():
    """
        Test converting OAuth2Error to dictionary.
    """
    error = OAuth2Error(
        error="invalid_request",
        error_description="Missing required parameter",
        error_uri="https://example.com/errors/invalid_request"
    )
    
    result = error.to_dict()
    
    if result["error"] != "invalid_request":
        errmsg = f"Expected error 'invalid_request', got '{result['error']}'"
        raise AssertionError(errmsg)
    
    if result["error_description"] != "Missing required parameter":
        errmsg = f"Unexpected error_description: {result['error_description']}"
        raise AssertionError(errmsg)
    
    if result["error_uri"] != "https://example.com/errors/invalid_request":
        errmsg = f"Unexpected error_uri: {result['error_uri']}"
        raise AssertionError(errmsg)
    
    return


def test_oauth2_error_to_dict_minimal():
    """
        Test converting minimal OAuth2Error to dictionary.
    """
    error = OAuth2Error(error="server_error")
    
    result = error.to_dict()
    
    if result != {"error": "server_error"}:
        errmsg = f"Expected minimal error dict, got {result}"
        raise AssertionError(errmsg)
    
    return


def test_create_oauth2_error_response():
    """
        Test creating OAuth2 error response.
    """
    error = OAuth2Error(
        error="invalid_client",
        error_description="Client authentication failed"
    )
    
    response = create_oauth2_error_response(error)
    
    if response["error"] != "invalid_client":
        errmsg = f"Expected error 'invalid_client', got '{response['error']}'"
        raise AssertionError(errmsg)
    
    return



# =============================================================================
# Unit Tests for OAuth2Authenticator
# =============================================================================

def test_oauth2_authenticator_scheme():
    """
        Test that OAuth2Authenticator returns "OAuth2" as scheme.
    """
    client_store = MockOAuth2ClientStore()
    token_store = MockOAuth2TokenStore()
    
    authenticator = OAuth2Authenticator(
        client_store=client_store,
        token_store=token_store
    )
    
    if authenticator.scheme != "OAuth2":
        errmsg = f"Expected scheme 'OAuth2', got '{authenticator.scheme}'"
        raise AssertionError(errmsg)
    
    return


def test_oauth2_authenticator_can_handle_with_bearer():
    """
        Test that can_handle returns True for Bearer auth header.
    """
    client_store = MockOAuth2ClientStore()
    token_store = MockOAuth2TokenStore()
    
    authenticator = OAuth2Authenticator(
        client_store=client_store,
        token_store=token_store
    )
    
    request = MockRequest(headers={"Authorization": "Bearer token123"})
    
    if not authenticator.can_handle(request):
        errmsg = "Expected can_handle to return True for Bearer auth header"
        raise AssertionError(errmsg)
    
    return


def test_oauth2_authenticator_can_handle_without_header():
    """
        Test that can_handle returns False when no Authorization header.
    """
    client_store = MockOAuth2ClientStore()
    token_store = MockOAuth2TokenStore()
    
    authenticator = OAuth2Authenticator(
        client_store=client_store,
        token_store=token_store
    )
    
    request = MockRequest(headers={})
    
    if authenticator.can_handle(request):
        errmsg = "Expected can_handle to return False without Authorization header"
        raise AssertionError(errmsg)
    
    return


def test_oauth2_authenticator_authenticate_valid_token():
    """
        Test authentication with valid access token.
    """
    client_store = MockOAuth2ClientStore()
    token_store = MockOAuth2TokenStore()
    
    # Add a valid token
    token_store.add_access_token(
        token="valid_token_123",
        client_id="test_client",
        user_id="user123",
        scope={"read", "write"}
    )
    
    authenticator = OAuth2Authenticator(
        client_store=client_store,
        token_store=token_store
    )
    
    request = MockRequest(headers={"Authorization": "Bearer valid_token_123"})
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
    
    return


def test_oauth2_authenticator_authenticate_invalid_token():
    """
        Test authentication with invalid access token.
    """
    client_store = MockOAuth2ClientStore()
    token_store = MockOAuth2TokenStore()
    
    authenticator = OAuth2Authenticator(
        client_store=client_store,
        token_store=token_store
    )
    
    request = MockRequest(headers={"Authorization": "Bearer invalid_token"})
    result = run_async(authenticator.authenticate(request))
    
    if result.status != AuthenticationStatus.FAILURE:
        errmsg = f"Expected FAILURE status, got {result.status}"
        raise AssertionError(errmsg)
    
    if result.error_code != "invalid_token":
        errmsg = f"Expected error_code 'invalid_token', got '{result.error_code}'"
        raise AssertionError(errmsg)
    
    return


def test_oauth2_authenticator_authenticate_no_header():
    """
        Test authentication without Authorization header returns SKIP.
    """
    client_store = MockOAuth2ClientStore()
    token_store = MockOAuth2TokenStore()
    
    authenticator = OAuth2Authenticator(
        client_store=client_store,
        token_store=token_store
    )
    
    request = MockRequest(headers={})
    result = run_async(authenticator.authenticate(request))
    
    if result.status != AuthenticationStatus.SKIP:
        errmsg = f"Expected SKIP status, got {result.status}"
        raise AssertionError(errmsg)
    
    return


def test_oauth2_authenticator_create_authorization_url():
    """
        Test creating authorization URL.
    """
    client_store = MockOAuth2ClientStore()
    token_store = MockOAuth2TokenStore()
    
    authenticator = OAuth2Authenticator(
        client_store=client_store,
        token_store=token_store,
        authorization_endpoint="/oauth/authorize"
    )
    
    url = authenticator.create_authorization_url(
        client_id="test_client",
        redirect_uri="https://example.com/callback",
        scope={"read", "write"},
        state="test_state"
    )
    
    if "/oauth/authorize?" not in url:
        errmsg = f"Expected authorization endpoint in URL, got '{url}'"
        raise AssertionError(errmsg)
    
    if "client_id=test_client" not in url:
        errmsg = f"Expected client_id in URL, got '{url}'"
        raise AssertionError(errmsg)
    
    if "response_type=code" not in url:
        errmsg = f"Expected response_type=code in URL, got '{url}'"
        raise AssertionError(errmsg)
    
    if "state=test_state" not in url:
        errmsg = f"Expected state in URL, got '{url}'"
        raise AssertionError(errmsg)
    
    return


def test_oauth2_authenticator_create_authorization_url_with_pkce():
    """
        Test creating authorization URL with PKCE.
    """
    client_store = MockOAuth2ClientStore()
    token_store = MockOAuth2TokenStore()
    
    authenticator = OAuth2Authenticator(
        client_store=client_store,
        token_store=token_store
    )
    
    code_verifier = generate_code_verifier()
    code_challenge = generate_code_challenge(code_verifier, PKCEMethod.S256)
    
    url = authenticator.create_authorization_url(
        client_id="test_client",
        redirect_uri="https://example.com/callback",
        code_challenge=code_challenge,
        code_challenge_method="S256"
    )
    
    if "code_challenge=" not in url:
        errmsg = f"Expected code_challenge in URL, got '{url}'"
        raise AssertionError(errmsg)
    
    if "code_challenge_method=S256" not in url:
        errmsg = f"Expected code_challenge_method in URL, got '{url}'"
        raise AssertionError(errmsg)
    
    return


def test_oauth2_authenticator_client_credentials_grant():
    """
        Test Client Credentials grant flow.
    """
    client_store = MockOAuth2ClientStore()
    token_store = MockOAuth2TokenStore()
    
    # Add a client
    client_store.add_client(
        client_id="test_client",
        client_secret="test_secret"
    )
    
    authenticator = OAuth2Authenticator(
        client_store=client_store,
        token_store=token_store,
        supported_grant_types={OAuth2GrantType.CLIENT_CREDENTIALS}
    )
    
    token, error = run_async(authenticator.client_credentials_grant(
        client_id="test_client",
        client_secret="test_secret",
        scope={"read"}
    ))
    
    if error is not None:
        errmsg = f"Expected no error, got {error.to_dict()}"
        raise AssertionError(errmsg)
    
    if token is None:
        errmsg = "Expected token to be present"
        raise AssertionError(errmsg)
    
    if not token.access_token:
        errmsg = "Expected access_token to be present"
        raise AssertionError(errmsg)
    
    # Client credentials should not have refresh token
    if token.refresh_token is not None:
        errmsg = "Expected no refresh_token for client credentials"
        raise AssertionError(errmsg)
    
    return


def test_oauth2_authenticator_client_credentials_invalid_client():
    """
        Test Client Credentials grant with invalid client.
    """
    client_store = MockOAuth2ClientStore()
    token_store = MockOAuth2TokenStore()
    
    authenticator = OAuth2Authenticator(
        client_store=client_store,
        token_store=token_store,
        supported_grant_types={OAuth2GrantType.CLIENT_CREDENTIALS}
    )
    
    token, error = run_async(authenticator.client_credentials_grant(
        client_id="invalid_client",
        client_secret="invalid_secret"
    ))
    
    if token is not None:
        errmsg = "Expected no token for invalid client"
        raise AssertionError(errmsg)
    
    if error is None:
        errmsg = "Expected error for invalid client"
        raise AssertionError(errmsg)
    
    if error.error != "invalid_client":
        errmsg = f"Expected error 'invalid_client', got '{error.error}'"
        raise AssertionError(errmsg)
    
    return


def test_oauth2_authenticator_password_grant():
    """
        Test Resource Owner Password Credentials grant flow.
    """
    client_store = MockOAuth2ClientStore()
    token_store = MockOAuth2TokenStore()
    user_authenticator = MockOAuth2UserAuthenticator()
    
    # Add a client and user
    client_store.add_client(client_id="test_client")
    user_authenticator.add_user(
        username="testuser",
        password="testpass",
        user_id="user123"
    )
    
    authenticator = OAuth2Authenticator(
        client_store=client_store,
        token_store=token_store,
        user_authenticator=user_authenticator,
        supported_grant_types={OAuth2GrantType.PASSWORD}
    )
    
    token, error = run_async(authenticator.password_grant(
        client_id="test_client",
        client_secret=None,
        username="testuser",
        password="testpass"
    ))
    
    if error is not None:
        errmsg = f"Expected no error, got {error.to_dict()}"
        raise AssertionError(errmsg)
    
    if token is None:
        errmsg = "Expected token to be present"
        raise AssertionError(errmsg)
    
    if not token.access_token:
        errmsg = "Expected access_token to be present"
        raise AssertionError(errmsg)
    
    # Password grant should have refresh token
    if token.refresh_token is None:
        errmsg = "Expected refresh_token for password grant"
        raise AssertionError(errmsg)
    
    return


def test_oauth2_authenticator_password_grant_invalid_user():
    """
        Test Password grant with invalid user credentials.
    """
    client_store = MockOAuth2ClientStore()
    token_store = MockOAuth2TokenStore()
    user_authenticator = MockOAuth2UserAuthenticator()
    
    client_store.add_client(client_id="test_client")
    
    authenticator = OAuth2Authenticator(
        client_store=client_store,
        token_store=token_store,
        user_authenticator=user_authenticator,
        supported_grant_types={OAuth2GrantType.PASSWORD}
    )
    
    token, error = run_async(authenticator.password_grant(
        client_id="test_client",
        client_secret=None,
        username="invalid",
        password="invalid"
    ))
    
    if token is not None:
        errmsg = "Expected no token for invalid user"
        raise AssertionError(errmsg)
    
    if error is None:
        errmsg = "Expected error for invalid user"
        raise AssertionError(errmsg)
    
    if error.error != "invalid_grant":
        errmsg = f"Expected error 'invalid_grant', got '{error.error}'"
        raise AssertionError(errmsg)
    
    return


def test_oauth2_authenticator_authorization_code_exchange():
    """
        Test Authorization Code exchange.
    """
    client_store = MockOAuth2ClientStore()
    token_store = MockOAuth2TokenStore()
    code_store = MockOAuth2AuthorizationCodeStore()
    
    # Add a client
    client_store.add_client(
        client_id="test_client",
        client_secret="test_secret"
    )
    
    # Add an authorization code
    auth_code = OAuth2AuthorizationCode(
        code="auth_code_123",
        client_id="test_client",
        redirect_uri="https://example.com/callback",
        scope={"read", "write"},
        user_id="user123",
        expires_at=datetime.utcnow() + timedelta(minutes=10)
    )
    code_store.add_code(auth_code)
    
    authenticator = OAuth2Authenticator(
        client_store=client_store,
        token_store=token_store,
        code_store=code_store
    )
    
    token, error = run_async(authenticator.exchange_authorization_code(
        code="auth_code_123",
        client_id="test_client",
        client_secret="test_secret",
        redirect_uri="https://example.com/callback"
    ))
    
    if error is not None:
        errmsg = f"Expected no error, got {error.to_dict()}"
        raise AssertionError(errmsg)
    
    if token is None:
        errmsg = "Expected token to be present"
        raise AssertionError(errmsg)
    
    if not token.access_token:
        errmsg = "Expected access_token to be present"
        raise AssertionError(errmsg)
    
    if token.refresh_token is None:
        errmsg = "Expected refresh_token for authorization code grant"
        raise AssertionError(errmsg)
    
    return


def test_oauth2_authenticator_authorization_code_with_pkce():
    """
        Test Authorization Code exchange with PKCE.
    """
    client_store = MockOAuth2ClientStore()
    token_store = MockOAuth2TokenStore()
    code_store = MockOAuth2AuthorizationCodeStore()
    
    # Add a client (public client, no secret)
    client_store.add_client(client_id="public_client")
    
    # Generate PKCE values
    code_verifier = generate_code_verifier()
    code_challenge = generate_code_challenge(code_verifier, PKCEMethod.S256)
    
    # Add an authorization code with PKCE
    auth_code = OAuth2AuthorizationCode(
        code="auth_code_pkce",
        client_id="public_client",
        redirect_uri="https://example.com/callback",
        scope={"read"},
        user_id="user123",
        code_challenge=code_challenge,
        code_challenge_method="S256",
        expires_at=datetime.utcnow() + timedelta(minutes=10)
    )
    code_store.add_code(auth_code)
    
    authenticator = OAuth2Authenticator(
        client_store=client_store,
        token_store=token_store,
        code_store=code_store
    )
    
    token, error = run_async(authenticator.exchange_authorization_code(
        code="auth_code_pkce",
        client_id="public_client",
        redirect_uri="https://example.com/callback",
        code_verifier=code_verifier
    ))
    
    if error is not None:
        errmsg = f"Expected no error, got {error.to_dict()}"
        raise AssertionError(errmsg)
    
    if token is None:
        errmsg = "Expected token to be present"
        raise AssertionError(errmsg)
    
    return


def test_oauth2_authenticator_authorization_code_pkce_wrong_verifier():
    """
        Test Authorization Code exchange with wrong PKCE verifier.
    """
    client_store = MockOAuth2ClientStore()
    token_store = MockOAuth2TokenStore()
    code_store = MockOAuth2AuthorizationCodeStore()
    
    client_store.add_client(client_id="public_client")
    
    code_verifier = generate_code_verifier()
    code_challenge = generate_code_challenge(code_verifier, PKCEMethod.S256)
    
    auth_code = OAuth2AuthorizationCode(
        code="auth_code_pkce",
        client_id="public_client",
        redirect_uri="https://example.com/callback",
        code_challenge=code_challenge,
        code_challenge_method="S256",
        expires_at=datetime.utcnow() + timedelta(minutes=10)
    )
    code_store.add_code(auth_code)
    
    authenticator = OAuth2Authenticator(
        client_store=client_store,
        token_store=token_store,
        code_store=code_store
    )
    
    # Use wrong verifier
    wrong_verifier = generate_code_verifier()
    
    token, error = run_async(authenticator.exchange_authorization_code(
        code="auth_code_pkce",
        client_id="public_client",
        redirect_uri="https://example.com/callback",
        code_verifier=wrong_verifier
    ))
    
    if token is not None:
        errmsg = "Expected no token for wrong PKCE verifier"
        raise AssertionError(errmsg)
    
    if error is None:
        errmsg = "Expected error for wrong PKCE verifier"
        raise AssertionError(errmsg)
    
    if error.error != "invalid_grant":
        errmsg = f"Expected error 'invalid_grant', got '{error.error}'"
        raise AssertionError(errmsg)
    
    return


def test_oauth2_authenticator_refresh_token_grant():
    """
        Test Refresh Token grant flow.
    """
    client_store = MockOAuth2ClientStore()
    token_store = MockOAuth2TokenStore()
    
    client_store.add_client(client_id="test_client")
    
    # Add a refresh token
    token_store.add_refresh_token(
        token="refresh_token_123",
        client_id="test_client",
        user_id="user123",
        scope={"read", "write"}
    )
    
    authenticator = OAuth2Authenticator(
        client_store=client_store,
        token_store=token_store,
        supported_grant_types={OAuth2GrantType.REFRESH_TOKEN}
    )
    
    token, error = run_async(authenticator.refresh_token_grant(
        client_id="test_client",
        client_secret=None,
        refresh_token="refresh_token_123"
    ))
    
    if error is not None:
        errmsg = f"Expected no error, got {error.to_dict()}"
        raise AssertionError(errmsg)
    
    if token is None:
        errmsg = "Expected token to be present"
        raise AssertionError(errmsg)
    
    if not token.access_token:
        errmsg = "Expected access_token to be present"
        raise AssertionError(errmsg)
    
    return


def test_oauth2_authenticator_refresh_token_invalid():
    """
        Test Refresh Token grant with invalid token.
    """
    client_store = MockOAuth2ClientStore()
    token_store = MockOAuth2TokenStore()
    
    client_store.add_client(client_id="test_client")
    
    authenticator = OAuth2Authenticator(
        client_store=client_store,
        token_store=token_store,
        supported_grant_types={OAuth2GrantType.REFRESH_TOKEN}
    )
    
    token, error = run_async(authenticator.refresh_token_grant(
        client_id="test_client",
        client_secret=None,
        refresh_token="invalid_refresh_token"
    ))
    
    if token is not None:
        errmsg = "Expected no token for invalid refresh token"
        raise AssertionError(errmsg)
    
    if error is None:
        errmsg = "Expected error for invalid refresh token"
        raise AssertionError(errmsg)
    
    if error.error != "invalid_grant":
        errmsg = f"Expected error 'invalid_grant', got '{error.error}'"
        raise AssertionError(errmsg)
    
    return



# =============================================================================
# Property-Based Tests
# =============================================================================

# Feature: authentication, Property 16: OAuth2 State Parameter Round-Trip
# *For any* OAuth2 authorization request, the state parameter generated during
# initiation SHALL be validated during callback, and mismatched states SHALL
# be rejected.
# **Validates: Requirements 6.5**

def test_property_16_oauth2_state_parameter_round_trip():
    """
        Property 16: OAuth2 State Parameter Round-Trip
        
        For any OAuth2 authorization request, the state parameter generated
        during initiation SHALL be validated during callback, and mismatched
        states SHALL be rejected.
        
        **Validates: Requirements 6.5**
    """
    # Run 100 iterations with random data
    for iteration in range(100):
        # Generate a random state
        original_state = generate_state(length=random.randint(16, 64))
        
        # Property 1: State should validate against itself
        if not validate_state(original_state, original_state):
            errmsg = f"Iteration {iteration}: State should validate against itself"
            raise AssertionError(errmsg)
        
        # Generate a different state
        different_state = generate_state(length=random.randint(16, 64))
        
        # Property 2: Different states should not validate
        # (with very high probability they are different)
        if original_state != different_state:
            if validate_state(original_state, different_state):
                errmsg = f"Iteration {iteration}: Different states should not validate"
                raise AssertionError(errmsg)
        
        # Property 3: None state should not validate
        if validate_state(original_state, None):
            errmsg = f"Iteration {iteration}: None state should not validate"
            raise AssertionError(errmsg)
        
        # Property 4: Empty string should not validate against non-empty
        if original_state and validate_state(original_state, ""):
            errmsg = f"Iteration {iteration}: Empty string should not validate"
            raise AssertionError(errmsg)
        
        # Property 5: State should be included in authorization URL
        client_store = MockOAuth2ClientStore()
        token_store = MockOAuth2TokenStore()
        
        authenticator = OAuth2Authenticator(
            client_store=client_store,
            token_store=token_store
        )
        
        url = authenticator.create_authorization_url(
            client_id=generate_random_client_id(),
            redirect_uri=generate_random_redirect_uri(),
            state=original_state
        )
        
        if f"state={original_state}" not in url:
            # URL encoding might change some characters
            from urllib.parse import parse_qs, urlparse
            parsed = urlparse(url)
            params = parse_qs(parsed.query)
            if params.get("state", [None])[0] != original_state:
                errmsg = f"Iteration {iteration}: State not found in authorization URL"
                raise AssertionError(errmsg)
    
    return


# Feature: authentication, Property 17: PKCE Code Challenge Verification
# *For any* PKCE-enabled OAuth2 flow, the code_verifier provided during token
# exchange SHALL correctly verify against the code_challenge from authorization,
# using the specified method (plain or S256).
# **Validates: Requirements 6.6**

def test_property_17_pkce_code_challenge_verification():
    """
        Property 17: PKCE Code Challenge Verification
        
        For any PKCE-enabled OAuth2 flow, the code_verifier provided during
        token exchange SHALL correctly verify against the code_challenge from
        authorization, using the specified method (plain or S256).
        
        **Validates: Requirements 6.6**
    """
    # Run 100 iterations with random data
    for iteration in range(100):
        # Generate a random code verifier (length 43-128)
        verifier_length = random.randint(43, 128)
        code_verifier = generate_code_verifier(length=verifier_length)
        
        # Test both PKCE methods
        for method in [PKCEMethod.PLAIN, PKCEMethod.S256]:
            # Generate code challenge
            code_challenge = generate_code_challenge(code_verifier, method)
            
            # Property 1: Correct verifier should validate
            method_str = method.value
            if not verify_code_challenge(code_verifier, code_challenge, method_str):
                errmsg = f"Iteration {iteration}: Correct verifier should validate for {method_str}"
                raise AssertionError(errmsg)
            
            # Property 2: Wrong verifier should not validate
            wrong_verifier = generate_code_verifier(length=verifier_length)
            if wrong_verifier != code_verifier:
                if verify_code_challenge(wrong_verifier, code_challenge, method_str):
                    errmsg = f"Iteration {iteration}: Wrong verifier should not validate for {method_str}"
                    raise AssertionError(errmsg)
            
            # Property 3: For S256, challenge should differ from verifier
            if method == PKCEMethod.S256:
                if code_challenge == code_verifier:
                    errmsg = f"Iteration {iteration}: S256 challenge should differ from verifier"
                    raise AssertionError(errmsg)
            
            # Property 4: For PLAIN, challenge should equal verifier
            if method == PKCEMethod.PLAIN:
                if code_challenge != code_verifier:
                    errmsg = f"Iteration {iteration}: PLAIN challenge should equal verifier"
                    raise AssertionError(errmsg)
        
        # Property 5: Test full OAuth2 flow with PKCE
        client_store = MockOAuth2ClientStore()
        token_store = MockOAuth2TokenStore()
        code_store = MockOAuth2AuthorizationCodeStore()
        
        client_id = generate_random_client_id()
        client_store.add_client(client_id=client_id)
        
        # Generate PKCE values
        code_challenge = generate_code_challenge(code_verifier, PKCEMethod.S256)
        
        # Create authorization code with PKCE
        auth_code = OAuth2AuthorizationCode(
            code=generate_random_token(),
            client_id=client_id,
            redirect_uri=generate_random_redirect_uri(),
            code_challenge=code_challenge,
            code_challenge_method="S256",
            expires_at=datetime.utcnow() + timedelta(minutes=10)
        )
        code_store.add_code(auth_code)
        
        authenticator = OAuth2Authenticator(
            client_store=client_store,
            token_store=token_store,
            code_store=code_store
        )
        
        # Exchange with correct verifier should succeed
        token, error = run_async(authenticator.exchange_authorization_code(
            code=auth_code.code,
            client_id=client_id,
            redirect_uri=auth_code.redirect_uri,
            code_verifier=code_verifier
        ))
        
        if error is not None:
            errmsg = f"Iteration {iteration}: PKCE exchange should succeed with correct verifier: {error.to_dict()}"
            raise AssertionError(errmsg)
        
        if token is None:
            errmsg = f"Iteration {iteration}: Token should be present after successful PKCE exchange"
            raise AssertionError(errmsg)
    
    return


# Feature: authentication, Property 18: OAuth2 Error Response Format
# *For any* failed OAuth2 token exchange, the error response SHALL contain
# "error" and optionally "error_description" fields per RFC 6749.
# **Validates: Requirements 6.9**

def test_property_18_oauth2_error_response_format():
    """
        Property 18: OAuth2 Error Response Format
        
        For any failed OAuth2 token exchange, the error response SHALL contain
        "error" and optionally "error_description" fields per RFC 6749.
        
        **Validates: Requirements 6.9**
    """
    # Define standard OAuth2 error codes per RFC 6749
    standard_error_codes = [
        "invalid_request",
        "invalid_client",
        "invalid_grant",
        "unauthorized_client",
        "unsupported_grant_type",
        "invalid_scope",
        "server_error"
    ]
    
    # Run 100 iterations with random data
    for iteration in range(100):
        # Test 1: Create OAuth2Error with random error code
        error_code = random.choice(standard_error_codes)
        error_description = generate_random_string(10, 100) if random.choice([True, False]) else None
        error_uri = f"https://example.com/errors/{error_code}" if random.choice([True, False]) else None
        
        error = OAuth2Error(
            error=error_code,
            error_description=error_description,
            error_uri=error_uri
        )
        
        # Convert to dict
        error_dict = error.to_dict()
        
        # Property 1: Error dict must contain "error" field
        if "error" not in error_dict:
            errmsg = f"Iteration {iteration}: Error dict must contain 'error' field"
            raise AssertionError(errmsg)
        
        # Property 2: Error code must match
        if error_dict["error"] != error_code:
            errmsg = f"Iteration {iteration}: Error code mismatch"
            raise AssertionError(errmsg)
        
        # Property 3: If error_description was provided, it must be in dict
        if error_description is not None:
            if "error_description" not in error_dict:
                errmsg = f"Iteration {iteration}: error_description should be in dict"
                raise AssertionError(errmsg)
            if error_dict["error_description"] != error_description:
                errmsg = f"Iteration {iteration}: error_description mismatch"
                raise AssertionError(errmsg)
        
        # Property 4: If error_uri was provided, it must be in dict
        if error_uri is not None:
            if "error_uri" not in error_dict:
                errmsg = f"Iteration {iteration}: error_uri should be in dict"
                raise AssertionError(errmsg)
            if error_dict["error_uri"] != error_uri:
                errmsg = f"Iteration {iteration}: error_uri mismatch"
                raise AssertionError(errmsg)
        
        # Property 5: If error_description was not provided, it should not be in dict
        if error_description is None:
            if "error_description" in error_dict:
                errmsg = f"Iteration {iteration}: error_description should not be in dict when not provided"
                raise AssertionError(errmsg)
        
        # Property 6: create_oauth2_error_response should produce same result
        response = create_oauth2_error_response(error)
        if response != error_dict:
            errmsg = f"Iteration {iteration}: create_oauth2_error_response should match to_dict"
            raise AssertionError(errmsg)
    
    # Test actual OAuth2 flow errors
    client_store = MockOAuth2ClientStore()
    token_store = MockOAuth2TokenStore()
    
    authenticator = OAuth2Authenticator(
        client_store=client_store,
        token_store=token_store,
        supported_grant_types={OAuth2GrantType.CLIENT_CREDENTIALS}
    )
    
    # Test invalid client error
    token, error = run_async(authenticator.client_credentials_grant(
        client_id="nonexistent_client",
        client_secret="wrong_secret"
    ))
    
    if error is None:
        errmsg = "Expected error for invalid client"
        raise AssertionError(errmsg)
    
    error_dict = error.to_dict()
    
    # Property 7: Real error must have "error" field
    if "error" not in error_dict:
        errmsg = "Real OAuth2 error must have 'error' field"
        raise AssertionError(errmsg)
    
    # Property 8: Error code should be a standard code
    if error_dict["error"] not in standard_error_codes:
        errmsg = f"Error code '{error_dict['error']}' should be a standard OAuth2 error code"
        raise AssertionError(errmsg)
    
    return
