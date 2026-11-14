"""
    Unit tests for BearerAuthBlueprint.

    This module verifies the BearerAuthBlueprint endpoints including
    token issuance via password, refresh_token, and client_credentials
    grant types, token refresh, revocation, and introspection.

    **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8**
"""

import asyncio
import base64
import time

from ccai.webworks.authentication.blueprints.bearer import (
    BearerAuthBlueprint,
)
from ccai.webworks.authentication.bearer import (
    BearerAuthenticator,
    InMemoryTokenRevocationList,
    decode_jwt,
    encode_jwt,
    JWTError,
)
from ccai.webworks.authentication.core import AuthenticationStatus, Principal


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


# =============================================================================
# Client Credentials Grant Fails Closed
# =============================================================================

class MockClientStore:
    """
        A client store that knows one client, its secret and its scopes.
    """

    def __init__(self, client_id, client_secret, scopes=None):
        self._client_id = client_id
        self._client_secret = client_secret
        self._scopes = scopes or []

    async def validate_client_secret(self, client_id, client_secret):
        return client_id == self._client_id and client_secret == self._client_secret

    async def get_client(self, client_id):
        if client_id != self._client_id:
            return None
        return {"client_id": client_id, "scopes": list(self._scopes)}


def test_client_credentials_grant_refused_without_any_validator():
    """
        Verify that the client_credentials grant issues no token when
        neither a client store nor an identity provider is configured:
        nothing could have verified the client secret.
    """
    blueprint = _create_fresh_blueprint()

    request = MockJsonRequest({
        "grant_type": "client_credentials",
        "client_id": "admin",
        "client_secret": "x",
    })

    response = blueprint.token(request)

    if response["status"] != 400:
        errmsg = "Expected status 400, got {}".format(response["status"])
        raise AssertionError(errmsg)

    if "access_token" in response["body"]:
        errmsg = "Expected no access token for unverified client credentials"
        raise AssertionError(errmsg)

    if response["body"].get("error") != "unauthorized_client":
        errmsg = "Expected error 'unauthorized_client', got {!r}".format(
            response["body"].get("error")
        )
        raise AssertionError(errmsg)

    return


def test_client_credentials_grant_validates_against_client_store():
    """
        Verify that a configured client store authenticates the client and
        the token names the client as its subject.
    """
    blueprint = _create_fresh_blueprint()
    blueprint.client_store = MockClientStore("service-a", "s3cret")

    response = blueprint.token(MockJsonRequest({
        "grant_type": "client_credentials",
        "client_id": "service-a",
        "client_secret": "s3cret",
    }))

    if response["status"] != 200:
        errmsg = "Expected status 200, got {}".format(response["status"])
        raise AssertionError(errmsg)

    claims = decode_jwt(response["body"]["access_token"], JWT_SECRET, algorithms=[JWT_ALGORITHM])
    if claims.get("sub") != "service-a":
        errmsg = "Expected sub 'service-a', got {!r}".format(claims.get("sub"))
        raise AssertionError(errmsg)

    return


def test_client_credentials_grant_rejects_wrong_secret_with_client_store():
    """
        Verify that a wrong client secret is refused by the client store.
    """
    blueprint = _create_fresh_blueprint()
    blueprint.client_store = MockClientStore("service-a", "s3cret")

    response = blueprint.token(MockJsonRequest({
        "grant_type": "client_credentials",
        "client_id": "service-a",
        "client_secret": "wrong",
    }))

    if response["status"] != 401:
        errmsg = "Expected status 401, got {}".format(response["status"])
        raise AssertionError(errmsg)

    if response["body"].get("error") != "invalid_client":
        errmsg = "Expected error 'invalid_client', got {!r}".format(
            response["body"].get("error")
        )
        raise AssertionError(errmsg)

    return


class HeaderJsonRequest(MockJsonRequest):
    """
        A mock JSON request that also carries headers.
    """

    def __init__(self, data, headers):
        super().__init__(data)
        self.headers = headers


def test_client_credentials_grant_accepts_http_basic_client_authentication():
    """
        Verify that client credentials sent in an HTTP Basic Authorization
        header are accepted, as RFC 6749 clients send them.
    """
    blueprint = _create_fresh_blueprint()
    blueprint.client_store = MockClientStore("service-a", "s3cret")

    encoded = base64.b64encode(b"service-a:s3cret").decode("ascii")
    request = HeaderJsonRequest(
        {"grant_type": "client_credentials"},
        {"Authorization": "Basic {}".format(encoded)}
    )

    response = blueprint.token(request)

    if response["status"] != 200:
        errmsg = "Expected status 200, got {}".format(response["status"])
        raise AssertionError(errmsg)

    return


# =============================================================================
# Scope Validation
# =============================================================================

def _blueprint_with_user(permissions):
    """
        Create a blueprint whose identity provider knows one user holding
        the given permissions.
    """
    principal = Principal(identifier="user-123", permissions=set(permissions))
    blueprint = _create_fresh_blueprint()
    blueprint.identity_provider = MockIdentityProvider("testuser", "testpass", principal)
    return blueprint


def _password_grant(blueprint, scope=None):
    """
        Request tokens through the password grant.
    """
    data = {
        "grant_type": "password",
        "username": "testuser",
        "password": "testpass",
    }
    if scope is not None:
        data["scope"] = scope

    response = blueprint.token(MockJsonRequest(data))
    return response


def test_password_grant_refuses_scope_the_user_does_not_hold():
    """
        Verify that a user cannot obtain a scope simply by asking for it.
    """
    blueprint = _blueprint_with_user({"read"})

    response = _password_grant(blueprint, scope="admin")

    if response["status"] != 400:
        errmsg = "Expected status 400, got {}".format(response["status"])
        raise AssertionError(errmsg)

    if response["body"].get("error") != "invalid_scope":
        errmsg = "Expected error 'invalid_scope', got {!r}".format(
            response["body"].get("error")
        )
        raise AssertionError(errmsg)

    return


def test_password_grant_grants_only_scopes_the_user_holds():
    """
        Verify that a requested scope is reduced to the part the user holds
        and that the response reports the granted scope.
    """
    blueprint = _blueprint_with_user({"read", "write"})

    response = _password_grant(blueprint, scope="read admin")

    if response["status"] != 200:
        errmsg = "Expected status 200, got {}".format(response["status"])
        raise AssertionError(errmsg)

    if response["body"].get("scope") != "read":
        errmsg = "Expected granted scope 'read', got {!r}".format(response["body"].get("scope"))
        raise AssertionError(errmsg)

    claims = decode_jwt(response["body"]["access_token"], JWT_SECRET, algorithms=[JWT_ALGORITHM])
    if claims.get("scope") != "read":
        errmsg = "Expected token scope 'read', got {!r}".format(claims.get("scope"))
        raise AssertionError(errmsg)

    return


def test_refresh_grant_refuses_scope_wider_than_refresh_token():
    """
        Verify that a refresh request cannot name a scope the refresh token
        does not carry.
    """
    blueprint = _blueprint_with_user({"read", "admin"})

    issued = _password_grant(blueprint, scope="read")

    response = blueprint.refresh(MockJsonRequest({
        "refresh_token": issued["body"]["refresh_token"],
        "scope": "read admin",
    }))

    if response["status"] != 400:
        errmsg = "Expected status 400, got {}".format(response["status"])
        raise AssertionError(errmsg)

    if response["body"].get("error") != "invalid_scope":
        errmsg = "Expected error 'invalid_scope', got {!r}".format(
            response["body"].get("error")
        )
        raise AssertionError(errmsg)

    return


def test_refresh_grant_carries_scope_of_refresh_token():
    """
        Verify that a refresh without a scope keeps the scope the refresh
        token was issued with.
    """
    blueprint = _blueprint_with_user({"read", "write"})

    issued = _password_grant(blueprint, scope="read write")

    response = blueprint.refresh(MockJsonRequest({
        "refresh_token": issued["body"]["refresh_token"],
    }))

    if response["status"] != 200:
        errmsg = "Expected status 200, got {}".format(response["status"])
        raise AssertionError(errmsg)

    claims = decode_jwt(response["body"]["access_token"], JWT_SECRET, algorithms=[JWT_ALGORITHM])
    if claims.get("scope") != "read write":
        errmsg = "Expected token scope 'read write', got {!r}".format(claims.get("scope"))
        raise AssertionError(errmsg)

    return


def test_client_credentials_grant_limits_scope_to_client_registration():
    """
        Verify that a client is granted only scopes it is registered for.
    """
    blueprint = _create_fresh_blueprint()
    blueprint.client_store = MockClientStore("service-a", "s3cret", scopes=["reports"])

    response = blueprint.token(MockJsonRequest({
        "grant_type": "client_credentials",
        "client_id": "service-a",
        "client_secret": "s3cret",
        "scope": "admin",
    }))

    if response["status"] != 400 or response["body"].get("error") != "invalid_scope":
        errmsg = "Expected 400 invalid_scope, got {} {!r}".format(
            response["status"], response["body"]
        )
        raise AssertionError(errmsg)

    return


# =============================================================================
# Revocation
# =============================================================================

def _isolated_revocation(blueprint):
    """
        Give a blueprint its own revocation list so tests do not see each
        other's revocations.
    """
    blueprint.revocation_list = InMemoryTokenRevocationList()
    return blueprint.revocation_list


def test_issued_tokens_carry_distinct_jti():
    """
        Verify that access and refresh tokens carry a jti claim, which is
        what a revocation names.
    """
    blueprint = _blueprint_with_user(set())

    body = _password_grant(blueprint)["body"]

    access_claims = decode_jwt(body["access_token"], JWT_SECRET, algorithms=[JWT_ALGORITHM])
    refresh_claims = decode_jwt(body["refresh_token"], JWT_SECRET, algorithms=[JWT_ALGORITHM])

    if not access_claims.get("jti") or not refresh_claims.get("jti"):
        errmsg = "Expected a jti claim on both tokens"
        raise AssertionError(errmsg)

    if access_claims["jti"] == refresh_claims["jti"]:
        errmsg = "Expected the access and refresh tokens to have different jti values"
        raise AssertionError(errmsg)

    return


def test_revoked_access_token_is_rejected_by_bearer_authenticator():
    """
        Verify that an access token revoked at the revoke endpoint is no
        longer accepted by a BearerAuthenticator that shares the
        blueprint's revocation list, even without a token store.
    """
    blueprint = _blueprint_with_user(set())
    _isolated_revocation(blueprint)

    access_token = _password_grant(blueprint)["body"]["access_token"]

    authenticator = BearerAuthenticator(
        jwt_secret=JWT_SECRET,
        revocation_list=blueprint.get_revocation_list()
    )
    request = {"headers": {"Authorization": "Bearer {}".format(access_token)}}

    before = asyncio.run(authenticator.authenticate(request))
    if before.status != AuthenticationStatus.SUCCESS:
        errmsg = "Expected the fresh token to authenticate, got {}".format(before.status)
        raise AssertionError(errmsg)

    blueprint.revoke(MockJsonRequest({"token": access_token}))

    after = asyncio.run(authenticator.authenticate(request))
    if after.status != AuthenticationStatus.FAILURE:
        errmsg = "Expected the revoked token to be rejected, got {}".format(after.status)
        raise AssertionError(errmsg)

    return


def test_revoked_refresh_token_cannot_be_refreshed():
    """
        Verify that a revoked refresh token no longer mints access tokens.
    """
    blueprint = _blueprint_with_user(set())
    _isolated_revocation(blueprint)

    refresh_token = _password_grant(blueprint)["body"]["refresh_token"]

    blueprint.revoke(MockJsonRequest({"token": refresh_token}))

    response = blueprint.refresh(MockJsonRequest({"refresh_token": refresh_token}))

    if response["status"] != 401:
        errmsg = "Expected status 401 for a revoked refresh token, got {}".format(response["status"])
        raise AssertionError(errmsg)

    if response["body"].get("error") != "invalid_grant":
        errmsg = "Expected error 'invalid_grant', got {!r}".format(response["body"].get("error"))
        raise AssertionError(errmsg)

    return


def test_introspect_reports_revoked_token_inactive():
    """
        Verify that introspection reports a revoked token as inactive.
    """
    blueprint = _blueprint_with_user(set())
    _isolated_revocation(blueprint)

    access_token = _password_grant(blueprint)["body"]["access_token"]

    blueprint.revoke(MockJsonRequest({"token": access_token}))

    response = blueprint.introspect(MockJsonRequest({"token": access_token}))

    if response["body"] != {"active": False}:
        errmsg = "Expected {{'active': False}}, got {!r}".format(response["body"])
        raise AssertionError(errmsg)

    return


def test_revoke_ignores_token_not_signed_by_this_server():
    """
        Verify that a string that is not one of this server's tokens does
        not grow the revocation list.
    """
    blueprint = _create_fresh_blueprint()
    revocation_list = _isolated_revocation(blueprint)

    forged = encode_jwt({"sub": "x", "exp": int(time.time()) + 60}, "another-secret")
    response = blueprint.revoke(MockJsonRequest({"token": forged}))

    if response["status"] != 200:
        errmsg = "Expected status 200, got {}".format(response["status"])
        raise AssertionError(errmsg)

    if revocation_list.get_entry_count() != 0:
        errmsg = "Expected no revocation to be recorded for a foreign token"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Request Body Parsing
# =============================================================================

class FormRequest:
    """
        A mock request with an application/x-www-form-urlencoded body.
    """

    def __init__(self, fields):
        self.headers = {"Content-Type": "application/x-www-form-urlencoded"}
        self._fields = fields

    def form(self):
        return self._fields

    def json(self):
        errmsg = "body is not JSON"
        raise ValueError(errmsg)


def test_token_accepts_form_encoded_body():
    """
        Verify that the token endpoint reads a form-encoded body, which is
        what OAuth 2.0 clients send.
    """
    blueprint = _blueprint_with_user(set())

    response = blueprint.token(FormRequest({
        "grant_type": "password",
        "username": "testuser",
        "password": "testpass",
    }))

    if response["status"] != 200:
        errmsg = "Expected status 200, got {}".format(response["status"])
        raise AssertionError(errmsg)

    return


def test_token_rejects_non_object_json_body():
    """
        Verify that a JSON body that is not an object is answered with 400
        invalid_request instead of an unhandled error.
    """
    blueprint = _create_fresh_blueprint()

    response = blueprint.token(MockJsonRequest([]))

    if response["status"] != 400:
        errmsg = "Expected status 400, got {}".format(response["status"])
        raise AssertionError(errmsg)

    if response["body"].get("error") != "invalid_request":
        errmsg = "Expected error 'invalid_request', got {!r}".format(
            response["body"].get("error")
        )
        raise AssertionError(errmsg)

    return


def test_introspect_rejects_unparseable_body():
    """
        Verify that a body that is not valid JSON is answered with 400.
    """
    class BrokenJsonRequest:
        def json(self):
            errmsg = "Expecting value"
            raise ValueError(errmsg)

    blueprint = _create_fresh_blueprint()

    response = blueprint.introspect(BrokenJsonRequest())

    if response["status"] != 400:
        errmsg = "Expected status 400, got {}".format(response["status"])
        raise AssertionError(errmsg)

    return


def test_default_bearer_authenticator_refuses_token_revoked_at_blueprint():
    """
        Verify that, with neither side configured with a revocation list,
        a token revoked at the revoke endpoint is refused by a
        BearerAuthenticator: both use the process-wide default list.
    """
    blueprint = _blueprint_with_user(set())
    blueprint.revocation_list = None

    access_token = _password_grant(blueprint)["body"]["access_token"]

    authenticator = BearerAuthenticator(jwt_secret=JWT_SECRET)
    request = {"headers": {"Authorization": "Bearer {}".format(access_token)}}

    blueprint.revoke(MockJsonRequest({"token": access_token}))

    result = asyncio.run(authenticator.authenticate(request))
    if result.status != AuthenticationStatus.FAILURE:
        errmsg = "Expected the revoked token to be refused by default, got {}".format(result.status)
        raise AssertionError(errmsg)

    return
