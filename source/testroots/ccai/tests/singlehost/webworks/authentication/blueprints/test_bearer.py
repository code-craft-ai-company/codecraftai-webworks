"""
    Unit tests for BearerAuthBlueprint.

    This module verifies the BearerAuthBlueprint endpoints including
    token issuance via password, refresh_token, and client_credentials
    grant types, token refresh, revocation, and introspection.

    **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8**
"""

import time

from ccai.webworks.authentication.blueprints.bearer import (
    BearerAuthBlueprint,
)
from ccai.webworks.authentication.bearer import (
    decode_jwt,
    encode_jwt,
    JWTError,
)
from ccai.webworks.authentication.core import Principal


# =============================================================================
# Test Helpers
# =============================================================================

JWT_SECRET = "test-secret-key-for-bearer-tests"
JWT_ALGORITHM = "HS256"


class MockJsonRequest:
    """
        A simple mock request that returns a JSON body dictionary.
    """

    def __init__(self, data):
        self._data = data

    def json(self):
        return self._data


class MockIdentityProvider:
    """
        A mock identity provider that knows about a single user.
    """

    def __init__(self, known_username, known_password, principal):
        self._known_username = known_username
        self._known_password = known_password
        self._principal = principal

    async def validate_credentials(self, username, password):
        if username == self._known_username and password == self._known_password:
            return self._principal
        return None

    async def get_principal(self, identifier):
        if identifier == self._principal.identifier:
            return self._principal
        return None


class RejectAllIdentityProvider:
    """
        A mock identity provider that rejects every credential pair.
    """

    async def validate_credentials(self, username, password):
        return None

    async def get_principal(self, identifier):
        return None


class MockTokenStore:
    """
        A mock token store that stores tokens in memory.
    """

    def __init__(self):
        self._tokens = {}
        self._revoked = set()

    async def store_token(self, token, claims, expires_in):
        self._tokens[token] = claims

    async def validate_token(self, token):
        if token in self._revoked:
            return None
        return self._tokens.get(token)

    async def revoke_token(self, token):
        if token in self._tokens:
            self._revoked.add(token)
            return True
        return False


def _create_fresh_blueprint():
    """
        Create a fresh BearerAuthBlueprint subclass to avoid class-level
        state leakage between tests.
    """

    class FreshBlueprint(BearerAuthBlueprint):
        pass

    FreshBlueprint.jwt_secret = JWT_SECRET
    FreshBlueprint.jwt_algorithm = JWT_ALGORITHM
    FreshBlueprint.access_token_expires = 3600
    FreshBlueprint.refresh_token_expires = 86400 * 7
    FreshBlueprint.token_store = None
    FreshBlueprint.identity_provider = None
    FreshBlueprint.enabled_endpoints = None
    FreshBlueprint.auth_system = None
    FreshBlueprint.base_path = "/auth/token"

    return FreshBlueprint


# =============================================================================
# Token Endpoint Tests (Requirement 3.1, 3.4)
# =============================================================================

def test_token_password_grant_valid_credentials():
    """
        Verify that the token endpoint issues a JWT access token when
        valid credentials are provided via the password grant type.

        **Validates: Requirements 3.1, 3.4**
    """
    principal = Principal(
        identifier="user-123",
        display_name="Test User",
    )
    provider = MockIdentityProvider("testuser", "testpass", principal)

    blueprint = _create_fresh_blueprint()
    blueprint.identity_provider = provider

    request = MockJsonRequest({
        "grant_type": "password",
        "username": "testuser",
        "password": "testpass",
    })

    response = blueprint.token(request)

    if response["status"] != 200:
        errmsg = "Expected status 200, got {}".format(response["status"])
        raise AssertionError(errmsg)

    body = response["body"]

    if "access_token" not in body:
        errmsg = "Expected access_token in response body"
        raise AssertionError(errmsg)

    if body.get("token_type") != "Bearer":
        errmsg = "Expected token_type 'Bearer', got {!r}".format(
            body.get("token_type")
        )
        raise AssertionError(errmsg)

    # Verify the access token is a valid JWT
    claims = decode_jwt(
        body["access_token"],
        JWT_SECRET,
        algorithms=[JWT_ALGORITHM],
    )

    if claims.get("sub") != "user-123":
        errmsg = "Expected sub claim 'user-123', got {!r}".format(
            claims.get("sub")
        )
        raise AssertionError(errmsg)

    if claims.get("token_type") != "access":
        errmsg = "Expected token_type claim 'access', got {!r}".format(
            claims.get("token_type")
        )
        raise AssertionError(errmsg)

    return


def test_token_password_grant_invalid_credentials():
    """
        Verify that the token endpoint returns an error when invalid
        credentials are provided via the password grant type.

        **Validates: Requirements 3.1**
    """
    provider = RejectAllIdentityProvider()

    blueprint = _create_fresh_blueprint()
    blueprint.identity_provider = provider

    request = MockJsonRequest({
        "grant_type": "password",
        "username": "baduser",
        "password": "badpass",
    })

    response = blueprint.token(request)

    if response["status"] != 401:
        errmsg = "Expected status 401, got {}".format(response["status"])
        raise AssertionError(errmsg)

    body = response["body"]

    if "error" not in body:
        errmsg = "Expected error field in response body"
        raise AssertionError(errmsg)

    return


def test_token_password_grant_missing_credentials():
    """
        Verify that the token endpoint returns 400 when username or
        password is missing from a password grant request.

        **Validates: Requirements 3.1**
    """
    blueprint = _create_fresh_blueprint()
    blueprint.identity_provider = RejectAllIdentityProvider()

    request = MockJsonRequest({
        "grant_type": "password",
        "username": "testuser",
    })

    response = blueprint.token(request)

    if response["status"] != 400:
        errmsg = "Expected status 400, got {}".format(response["status"])
        raise AssertionError(errmsg)

    return


def test_token_unsupported_grant_type():
    """
        Verify that the token endpoint returns 400 for unsupported
        grant types.

        **Validates: Requirements 3.1**
    """
    blueprint = _create_fresh_blueprint()

    request = MockJsonRequest({
        "grant_type": "authorization_code",
    })

    response = blueprint.token(request)

    if response["status"] != 400:
        errmsg = "Expected status 400, got {}".format(response["status"])
        raise AssertionError(errmsg)

    body = response["body"]

    if body.get("error") != "unsupported_grant_type":
        errmsg = "Expected error 'unsupported_grant_type', got {!r}".format(
            body.get("error")
        )
        raise AssertionError(errmsg)

    return


# =============================================================================
# Refresh Endpoint Tests (Requirement 3.2, 3.7)
# =============================================================================

def test_refresh_endpoint_with_valid_refresh_token():
    """
        Verify that the refresh endpoint issues a new access token when
        a valid refresh token is provided.

        **Validates: Requirements 3.2, 3.7**
    """
    blueprint = _create_fresh_blueprint()

    # Create a valid refresh token
    now = time.time()
    refresh_payload = {
        "sub": "user-456",
        "iat": int(now),
        "exp": int(now) + 86400,
        "token_type": "refresh",
    }
    refresh_token = encode_jwt(refresh_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    request = MockJsonRequest({
        "refresh_token": refresh_token,
    })

    response = blueprint.refresh(request)

    if response["status"] != 200:
        errmsg = "Expected status 200, got {}".format(response["status"])
        raise AssertionError(errmsg)

    body = response["body"]

    if "access_token" not in body:
        errmsg = "Expected access_token in response body"
        raise AssertionError(errmsg)

    # Verify the new access token has the correct subject
    claims = decode_jwt(
        body["access_token"],
        JWT_SECRET,
        algorithms=[JWT_ALGORITHM],
    )

    if claims.get("sub") != "user-456":
        errmsg = "Expected sub claim 'user-456', got {!r}".format(
            claims.get("sub")
        )
        raise AssertionError(errmsg)

    return


def test_refresh_endpoint_missing_refresh_token():
    """
        Verify that the refresh endpoint returns 400 when no refresh
        token is provided.

        **Validates: Requirements 3.2**
    """
    blueprint = _create_fresh_blueprint()

    request = MockJsonRequest({})

    response = blueprint.refresh(request)

    if response["status"] != 400:
        errmsg = "Expected status 400, got {}".format(response["status"])
        raise AssertionError(errmsg)

    return


def test_refresh_endpoint_with_invalid_token():
    """
        Verify that the refresh endpoint returns 401 when an invalid
        refresh token is provided.

        **Validates: Requirements 3.2**
    """
    blueprint = _create_fresh_blueprint()

    request = MockJsonRequest({
        "refresh_token": "invalid-token-value",
    })

    response = blueprint.refresh(request)

    # Should return 401 for invalid token
    if response["status"] != 401:
        errmsg = "Expected status 401, got {}".format(response["status"])
        raise AssertionError(errmsg)

    return


# =============================================================================
# Revoke Endpoint Tests (Requirement 3.3)
# =============================================================================

def test_revoke_endpoint_with_token_store():
    """
        Verify that the revoke endpoint revokes a token via the token store.

        **Validates: Requirements 3.3**
    """
    token_store = MockTokenStore()
    blueprint = _create_fresh_blueprint()
    blueprint.token_store = token_store

    # Store a token first
    import asyncio
    asyncio.run(
        token_store.store_token("test-token", {"sub": "user"}, 3600)
    )

    request = MockJsonRequest({
        "token": "test-token",
    })

    response = blueprint.revoke(request)

    if response["status"] != 200:
        errmsg = "Expected status 200, got {}".format(response["status"])
        raise AssertionError(errmsg)

    # Verify the token was revoked
    result = asyncio.run(token_store.validate_token("test-token"))
    if result is not None:
        errmsg = "Expected token to be revoked (validate_token should return None)"
        raise AssertionError(errmsg)

    return


def test_revoke_endpoint_missing_token():
    """
        Verify that the revoke endpoint returns 400 when no token is provided.

        **Validates: Requirements 3.3**
    """
    blueprint = _create_fresh_blueprint()

    request = MockJsonRequest({})

    response = blueprint.revoke(request)

    if response["status"] != 400:
        errmsg = "Expected status 400, got {}".format(response["status"])
        raise AssertionError(errmsg)

    return


def test_revoke_endpoint_without_token_store():
    """
        Verify that the revoke endpoint succeeds even without a token store.

        **Validates: Requirements 3.3**
    """
    blueprint = _create_fresh_blueprint()
    blueprint.token_store = None

    request = MockJsonRequest({
        "token": "some-token",
    })

    response = blueprint.revoke(request)

    if response["status"] != 200:
        errmsg = "Expected status 200, got {}".format(response["status"])
        raise AssertionError(errmsg)

    return



# =============================================================================
# Introspect Endpoint Tests (Requirement 3.8)
# =============================================================================

def test_introspect_endpoint_with_valid_token():
    """
        Verify that the introspect endpoint returns active=True and claims
        for a valid token.

        **Validates: Requirements 3.8**
    """
    blueprint = _create_fresh_blueprint()

    # Create a valid access token
    now = time.time()
    payload = {
        "sub": "user-789",
        "iat": int(now),
        "exp": int(now) + 3600,
        "token_type": "access",
    }
    token = encode_jwt(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    request = MockJsonRequest({
        "token": token,
    })

    response = blueprint.introspect(request)

    if response["status"] != 200:
        errmsg = "Expected status 200, got {}".format(response["status"])
        raise AssertionError(errmsg)

    body = response["body"]

    if body.get("active") is not True:
        errmsg = "Expected active=True, got {!r}".format(body.get("active"))
        raise AssertionError(errmsg)

    if body.get("sub") != "user-789":
        errmsg = "Expected sub='user-789', got {!r}".format(body.get("sub"))
        raise AssertionError(errmsg)

    return


def test_introspect_endpoint_with_invalid_token():
    """
        Verify that the introspect endpoint returns active=False for an
        invalid token.

        **Validates: Requirements 3.8**
    """
    blueprint = _create_fresh_blueprint()

    request = MockJsonRequest({
        "token": "not-a-valid-jwt",
    })

    response = blueprint.introspect(request)

    if response["status"] != 200:
        errmsg = "Expected status 200, got {}".format(response["status"])
        raise AssertionError(errmsg)

    body = response["body"]

    if body.get("active") is not False:
        errmsg = "Expected active=False, got {!r}".format(body.get("active"))
        raise AssertionError(errmsg)

    return


def test_introspect_endpoint_with_expired_token():
    """
        Verify that the introspect endpoint returns active=False for an
        expired token.

        **Validates: Requirements 3.8**
    """
    blueprint = _create_fresh_blueprint()

    # Create an expired token
    now = time.time()
    payload = {
        "sub": "user-expired",
        "iat": int(now) - 7200,
        "exp": int(now) - 3600,
        "token_type": "access",
    }
    token = encode_jwt(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    request = MockJsonRequest({
        "token": token,
    })

    response = blueprint.introspect(request)

    if response["status"] != 200:
        errmsg = "Expected status 200, got {}".format(response["status"])
        raise AssertionError(errmsg)

    body = response["body"]

    if body.get("active") is not False:
        errmsg = "Expected active=False for expired token, got {!r}".format(
            body.get("active")
        )
        raise AssertionError(errmsg)

    return


def test_introspect_endpoint_missing_token():
    """
        Verify that the introspect endpoint returns 400 when no token
        is provided.

        **Validates: Requirements 3.8**
    """
    blueprint = _create_fresh_blueprint()

    request = MockJsonRequest({})

    response = blueprint.introspect(request)

    if response["status"] != 400:
        errmsg = "Expected status 400, got {}".format(response["status"])
        raise AssertionError(errmsg)

    return


# =============================================================================
# JWT Configuration Tests (Requirement 3.5, 3.6)
# =============================================================================

def test_token_expiration_configuration():
    """
        Verify that issued tokens have exp claims matching the configured
        access_token_expires value.

        **Validates: Requirements 3.5**
    """
    principal = Principal(
        identifier="user-exp",
        display_name="Expiry User",
    )
    provider = MockIdentityProvider("expuser", "exppass", principal)

    blueprint = _create_fresh_blueprint()
    blueprint.identity_provider = provider
    blueprint.access_token_expires = 1800  # 30 minutes

    request = MockJsonRequest({
        "grant_type": "password",
        "username": "expuser",
        "password": "exppass",
    })

    before = time.time()
    response = blueprint.token(request)
    after = time.time()

    body = response["body"]
    claims = decode_jwt(
        body["access_token"],
        JWT_SECRET,
        algorithms=[JWT_ALGORITHM],
    )

    expected_min = int(before) + 1800
    expected_max = int(after) + 1800 + 1

    exp_claim = claims.get("exp")
    if exp_claim < expected_min or exp_claim > expected_max:
        errmsg = (
            "Expected exp claim between {} and {}, got {}".format(
                expected_min, expected_max, exp_claim
            )
        )
        raise AssertionError(errmsg)

    if body.get("expires_in") != 1800:
        errmsg = "Expected expires_in=1800, got {!r}".format(
            body.get("expires_in")
        )
        raise AssertionError(errmsg)

    return


def test_jwt_algorithm_configuration():
    """
        Verify that tokens are signed with the configured algorithm.

        **Validates: Requirements 3.6**
    """
    principal = Principal(
        identifier="user-alg",
        display_name="Algorithm User",
    )
    provider = MockIdentityProvider("alguser", "algpass", principal)

    blueprint = _create_fresh_blueprint()
    blueprint.identity_provider = provider
    blueprint.jwt_algorithm = "HS384"

    request = MockJsonRequest({
        "grant_type": "password",
        "username": "alguser",
        "password": "algpass",
    })

    response = blueprint.token(request)
    body = response["body"]

    # Verify the token can be decoded with HS384
    claims = decode_jwt(
        body["access_token"],
        JWT_SECRET,
        algorithms=["HS384"],
    )

    if claims.get("sub") != "user-alg":
        errmsg = "Expected sub='user-alg', got {!r}".format(claims.get("sub"))
        raise AssertionError(errmsg)

    # Verify the token cannot be decoded with HS256
    try:
        decode_jwt(
            body["access_token"],
            JWT_SECRET,
            algorithms=["HS256"],
        )
        errmsg = "Expected JWTError when decoding HS384 token with HS256"
        raise AssertionError(errmsg)
    except JWTError:
        pass

    return


# =============================================================================
# Client Credentials Grant Tests (Requirement 3.1)
# =============================================================================

def test_token_client_credentials_grant():
    """
        Verify that the token endpoint issues a token for valid client
        credentials.

        **Validates: Requirements 3.1**
    """
    principal = Principal(
        identifier="client-app",
        display_name="Client App",
    )
    provider = MockIdentityProvider("client-id", "client-secret", principal)

    blueprint = _create_fresh_blueprint()
    blueprint.identity_provider = provider

    request = MockJsonRequest({
        "grant_type": "client_credentials",
        "client_id": "client-id",
        "client_secret": "client-secret",
    })

    response = blueprint.token(request)

    if response["status"] != 200:
        errmsg = "Expected status 200, got {}".format(response["status"])
        raise AssertionError(errmsg)

    body = response["body"]

    if "access_token" not in body:
        errmsg = "Expected access_token in response body"
        raise AssertionError(errmsg)

    # Client credentials should NOT issue a refresh token
    if "refresh_token" in body:
        errmsg = "Client credentials grant should not issue a refresh token"
        raise AssertionError(errmsg)

    return


def test_token_client_credentials_missing_fields():
    """
        Verify that the token endpoint returns 400 when client_id or
        client_secret is missing from a client_credentials grant.

        **Validates: Requirements 3.1**
    """
    blueprint = _create_fresh_blueprint()

    request = MockJsonRequest({
        "grant_type": "client_credentials",
        "client_id": "client-id",
    })

    response = blueprint.token(request)

    if response["status"] != 400:
        errmsg = "Expected status 400, got {}".format(response["status"])
        raise AssertionError(errmsg)

    return


# =============================================================================
# Endpoint Enable/Disable Tests
# =============================================================================

def test_disabled_token_endpoint():
    """
        Verify that the token endpoint returns 404 when disabled.
    """
    blueprint = _create_fresh_blueprint()
    blueprint.enabled_endpoints = {"refresh", "revoke", "introspect"}

    request = MockJsonRequest({
        "grant_type": "password",
        "username": "user",
        "password": "pass",
    })

    response = blueprint.token(request)

    if response["status"] != 404:
        errmsg = "Expected status 404 for disabled endpoint, got {}".format(
            response["status"]
        )
        raise AssertionError(errmsg)

    return


def test_disabled_introspect_endpoint():
    """
        Verify that the introspect endpoint returns 404 when disabled.
    """
    blueprint = _create_fresh_blueprint()
    blueprint.enabled_endpoints = {"token", "refresh", "revoke"}

    request = MockJsonRequest({
        "token": "some-token",
    })

    response = blueprint.introspect(request)

    if response["status"] != 404:
        errmsg = "Expected status 404 for disabled endpoint, got {}".format(
            response["status"]
        )
        raise AssertionError(errmsg)

    return


# =============================================================================
# Password Grant with Token Store (Requirement 3.4)
# =============================================================================

def test_password_grant_issues_refresh_token():
    """
        Verify that the password grant issues both access and refresh tokens.

        **Validates: Requirements 3.4**
    """
    principal = Principal(
        identifier="user-refresh",
        display_name="Refresh User",
    )
    provider = MockIdentityProvider("refuser", "refpass", principal)

    blueprint = _create_fresh_blueprint()
    blueprint.identity_provider = provider

    request = MockJsonRequest({
        "grant_type": "password",
        "username": "refuser",
        "password": "refpass",
    })

    response = blueprint.token(request)

    if response["status"] != 200:
        errmsg = "Expected status 200, got {}".format(response["status"])
        raise AssertionError(errmsg)

    body = response["body"]

    if "access_token" not in body:
        errmsg = "Expected access_token in response body"
        raise AssertionError(errmsg)

    if "refresh_token" not in body:
        errmsg = "Expected refresh_token in response body for password grant"
        raise AssertionError(errmsg)

    # Verify the refresh token is a valid JWT with token_type=refresh
    refresh_claims = decode_jwt(
        body["refresh_token"],
        JWT_SECRET,
        algorithms=[JWT_ALGORITHM],
    )

    if refresh_claims.get("token_type") != "refresh":
        errmsg = "Expected refresh token_type='refresh', got {!r}".format(
            refresh_claims.get("token_type")
        )
        raise AssertionError(errmsg)

    if refresh_claims.get("sub") != "user-refresh":
        errmsg = "Expected refresh sub='user-refresh', got {!r}".format(
            refresh_claims.get("sub")
        )
        raise AssertionError(errmsg)

    return


def test_no_jwt_secret_returns_server_error():
    """
        Verify that endpoints return 500 when jwt_secret is not configured.
    """
    principal = Principal(
        identifier="user-nosecret",
        display_name="No Secret User",
    )
    provider = MockIdentityProvider("nsuser", "nspass", principal)

    blueprint = _create_fresh_blueprint()
    blueprint.identity_provider = provider
    blueprint.jwt_secret = None

    request = MockJsonRequest({
        "grant_type": "password",
        "username": "nsuser",
        "password": "nspass",
    })

    response = blueprint.token(request)

    if response["status"] != 500:
        errmsg = "Expected status 500 when jwt_secret is None, got {}".format(
            response["status"]
        )
        raise AssertionError(errmsg)

    body = response["body"]

    if body.get("error") != "server_error":
        errmsg = "Expected error 'server_error', got {!r}".format(
            body.get("error")
        )
        raise AssertionError(errmsg)

    return
