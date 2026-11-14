"""
    Unit tests for the OAuth2Blueprint.

    Tests cover the authorize, token, callback, and revoke endpoints
    including Authorization Code flow, Client Credentials flow, PKCE
    support, state validation, and redirect URI validation.
"""

import base64
import hashlib
import secrets
import time

from base64 import urlsafe_b64encode
from urllib.parse import parse_qsl, urlencode, urlsplit

from ccai.webworks.authentication.bearer import (
    InMemoryTokenRevocationList,
    decode_jwt,
)
from ccai.webworks.authentication.core import AuthenticationContext, Principal
from ccai.webworks.routing.request import Request
from ccai.webworks.authentication.blueprints.oauth2 import (
    AuthorizationCodeStore,
    OAuth2Blueprint,
    OAuth2ClientStore,
)


# =============================================================================
# Test Helpers
# =============================================================================


RESOURCE_OWNER = Principal(identifier="resource-owner-1")


class MockJsonRequest:
    """
        A simple mock request that returns a JSON body dictionary
        and optionally carries query parameters.
    """

    def __init__(self, data=None, query_params=None):
        self._data = data or {}
        self.query_params = query_params or {}

        # The resource owner the authentication middleware established.
        # The authorization endpoint issues codes on this user's behalf.
        self.auth = AuthenticationContext(principal=RESOURCE_OWNER, scheme="Test")

    def json(self):
        return self._data


class MockClientStore(OAuth2ClientStore):
    """
        A mock client store backed by an in-memory dictionary.
    """

    def __init__(self, clients=None):
        self._clients = clients or {}

    async def get_client(self, client_id):
        return self._clients.get(client_id)

    async def validate_client_secret(self, client_id, client_secret):
        client = self._clients.get(client_id)
        if client is None:
            return False
        return client.get("client_secret") == client_secret


class MockCodeStore(AuthorizationCodeStore):
    """
        A mock authorization code store backed by an in-memory dictionary.
    """

    def __init__(self):
        self._codes = {}

    async def store_code(self, code, client_id, redirect_uri, scope,
                         state, code_challenge, code_challenge_method):
        self._codes[code] = {
            "code": code,
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "scope": scope,
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": code_challenge_method,
        }

    async def consume_code(self, code):
        return self._codes.pop(code, None)


def _create_fresh_blueprint(clients=None, jwt_secret="test-secret",
                            require_pkce=False):
    """
        Create a fresh OAuth2Blueprint subclass to avoid class-level
        state leakage between tests.

        :param clients: Dictionary of client_id -> client data.
        :param jwt_secret: JWT signing secret.
        :param require_pkce: Whether PKCE is required.

        :returns: The fresh blueprint class.
    """

    class FreshBlueprint(OAuth2Blueprint):
        pass

    FreshBlueprint.client_store = None
    FreshBlueprint.authorization_code_store = None
    FreshBlueprint.token_store = None
    FreshBlueprint.jwt_secret = jwt_secret
    FreshBlueprint.jwt_algorithm = "HS256"
    FreshBlueprint.access_token_expires = 3600
    FreshBlueprint.refresh_token_expires = 86400 * 7
    FreshBlueprint.supported_grant_types = [
        "authorization_code", "client_credentials", "refresh_token"
    ]
    FreshBlueprint.supported_response_types = ["code"]
    FreshBlueprint.require_pkce = require_pkce
    FreshBlueprint.enabled_endpoints = None
    FreshBlueprint.auth_system = None
    FreshBlueprint.base_path = "/oauth"
    FreshBlueprint._memory_code_store = {}
    FreshBlueprint._memory_client_store = {}
    FreshBlueprint._memory_token_store = {}

    if clients:
        FreshBlueprint._memory_client_store = dict(clients)

    return FreshBlueprint


def _make_pkce_pair(method="S256"):
    """
        Generate a PKCE code_verifier and code_challenge pair.

        :param method: The challenge method ("S256" or "plain").

        :returns: A tuple of (code_verifier, code_challenge, method).
    """
    code_verifier = secrets.token_urlsafe(32)

    if method == "S256":
        digest = hashlib.sha256(code_verifier.encode("ascii")).digest()
        code_challenge = urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    else:
        code_challenge = code_verifier

    return code_verifier, code_challenge, method


# =============================================================================
# Authorize Endpoint Tests
# =============================================================================


def test_authorize_generates_code_and_redirects():
    """
        The authorize endpoint should generate an authorization code
        and redirect to the redirect_uri with code and state.
    """
    clients = {
        "test-client": {
            "client_id": "test-client",
            "client_secret": "secret",
            "redirect_uris": ["https://example.com/callback"],
            "grant_types": ["authorization_code"],
        }
    }
    blueprint = _create_fresh_blueprint(clients=clients)

    request = MockJsonRequest(query_params={
        "response_type": "code",
        "client_id": "test-client",
        "redirect_uri": "https://example.com/callback",
        "state": "abc123",
    })

    response = blueprint.authorize(request)

    assert response["status"] == 302, \
        "Expected 302 redirect, got {}".format(response["status"])

    location = response["headers"]["Location"]
    assert "code=" in location, \
        "Expected code in redirect URL"
    assert "state=abc123" in location, \
        "Expected state in redirect URL"

    return


def test_authorize_rejects_unknown_client():
    """
        The authorize endpoint should answer an unknown client directly and
        never redirect to the redirect_uri it supplied.
    """
    blueprint = _create_fresh_blueprint(clients={})

    request = MockJsonRequest(query_params={
        "response_type": "code",
        "client_id": "unknown-client",
        "redirect_uri": "https://example.com/callback",
        "state": "xyz",
    })

    response = blueprint.authorize(request)

    assert response["status"] == 400, \
        "Expected 400, got {}".format(response["status"])

    assert "Location" not in response.get("headers", {}), \
        "Expected no redirect for an unknown client"

    assert response["body"]["error"] == "invalid_client", \
        "Expected invalid_client error"

    return


def test_authorize_rejects_unsupported_response_type():
    """
        The authorize endpoint should redirect with error for unsupported
        response types.
    """
    clients = {
        "test-client": {
            "client_id": "test-client",
            "client_secret": "secret",
            "redirect_uris": ["https://example.com/callback"],
            "grant_types": ["authorization_code"],
        }
    }
    blueprint = _create_fresh_blueprint(clients=clients)

    request = MockJsonRequest(query_params={
        "response_type": "token",
        "client_id": "test-client",
        "redirect_uri": "https://example.com/callback",
    })

    response = blueprint.authorize(request)

    assert response["status"] == 302, \
        "Expected 302 redirect, got {}".format(response["status"])

    location = response["headers"]["Location"]
    assert "error=unsupported_response_type" in location, \
        "Expected unsupported_response_type error"

    return


def test_authorize_requires_redirect_uri():
    """
        The authorize endpoint should return 400 when redirect_uri is missing.
    """
    blueprint = _create_fresh_blueprint()

    request = MockJsonRequest(query_params={
        "response_type": "code",
        "client_id": "test-client",
    })

    response = blueprint.authorize(request)

    assert response["status"] == 400, \
        "Expected 400, got {}".format(response["status"])

    return


def test_authorize_requires_pkce_when_configured():
    """
        When require_pkce is True, the authorize endpoint should reject
        requests without a code_challenge.
    """
    clients = {
        "test-client": {
            "client_id": "test-client",
            "client_secret": "secret",
            "redirect_uris": ["https://example.com/callback"],
            "grant_types": ["authorization_code"],
        }
    }
    blueprint = _create_fresh_blueprint(clients=clients, require_pkce=True)

    request = MockJsonRequest(query_params={
        "response_type": "code",
        "client_id": "test-client",
        "redirect_uri": "https://example.com/callback",
    })

    response = blueprint.authorize(request)

    assert response["status"] == 302, \
        "Expected 302 redirect, got {}".format(response["status"])

    location = response["headers"]["Location"]
    assert "error=" in location, \
        "Expected error in redirect when PKCE is required"

    return


# =============================================================================
# Token Endpoint Tests
# =============================================================================


def test_token_authorization_code_grant():
    """
        The token endpoint should exchange an authorization code for tokens.
    """
    clients = {
        "test-client": {
            "client_id": "test-client",
            "client_secret": "secret",
            "redirect_uris": ["https://example.com/callback"],
            "grant_types": ["authorization_code"],
        }
    }
    blueprint = _create_fresh_blueprint(clients=clients)

    # First, authorize to get a code
    auth_request = MockJsonRequest(query_params={
        "response_type": "code",
        "client_id": "test-client",
        "redirect_uri": "https://example.com/callback",
        "state": "mystate",
    })
    auth_response = blueprint.authorize(auth_request)

    assert auth_response["status"] == 302, \
        "Expected 302, got {}".format(auth_response["status"])

    # Extract code from redirect URL
    location = auth_response["headers"]["Location"]
    code = None
    for part in location.split("?")[1].split("&"):
        if part.startswith("code="):
            code = part.split("=", 1)[1]
            break

    assert code is not None, "Expected code in redirect URL"

    # Exchange code for tokens
    token_request = MockJsonRequest(data={
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": "https://example.com/callback",
        "client_id": "test-client",
        "client_secret": "secret",
    })
    token_response = blueprint.token(token_request)

    assert token_response["status"] == 200, \
        "Expected 200, got {}".format(token_response["status"])
    assert "access_token" in token_response["body"], \
        "Expected access_token in response"
    assert "refresh_token" in token_response["body"], \
        "Expected refresh_token in response"

    return


def test_token_client_credentials_grant():
    """
        The token endpoint should issue tokens for valid client credentials.
    """
    clients = {
        "test-client": {
            "client_id": "test-client",
            "client_secret": "secret",
            "redirect_uris": [],
            "grant_types": ["client_credentials"],
        }
    }
    blueprint = _create_fresh_blueprint(clients=clients)

    request = MockJsonRequest(data={
        "grant_type": "client_credentials",
        "client_id": "test-client",
        "client_secret": "secret",
    })

    response = blueprint.token(request)

    assert response["status"] == 200, \
        "Expected 200, got {}".format(response["status"])
    assert "access_token" in response["body"], \
        "Expected access_token in response"
    # Client credentials should not issue refresh token
    assert "refresh_token" not in response["body"], \
        "Expected no refresh_token for client_credentials grant"

    return


def test_token_rejects_invalid_client_credentials():
    """
        The token endpoint should reject invalid client credentials.
    """
    clients = {
        "test-client": {
            "client_id": "test-client",
            "client_secret": "secret",
            "redirect_uris": [],
            "grant_types": ["client_credentials"],
        }
    }
    blueprint = _create_fresh_blueprint(clients=clients)

    request = MockJsonRequest(data={
        "grant_type": "client_credentials",
        "client_id": "test-client",
        "client_secret": "wrong-secret",
    })

    response = blueprint.token(request)

    assert response["status"] == 401, \
        "Expected 401, got {}".format(response["status"])
    assert response["body"]["error"] == "invalid_client", \
        "Expected invalid_client error"

    return


def test_token_rejects_unsupported_grant_type():
    """
        The token endpoint should reject unsupported grant types.
    """
    blueprint = _create_fresh_blueprint()

    request = MockJsonRequest(data={
        "grant_type": "implicit",
    })

    response = blueprint.token(request)

    assert response["status"] == 400, \
        "Expected 400, got {}".format(response["status"])
    assert response["body"]["error"] == "unsupported_grant_type", \
        "Expected unsupported_grant_type error"

    return


def test_token_pkce_s256_verification():
    """
        The token endpoint should verify PKCE S256 code_verifier.
    """
    code_verifier, code_challenge, method = _make_pkce_pair("S256")

    clients = {
        "test-client": {
            "client_id": "test-client",
            "client_secret": "secret",
            "redirect_uris": ["https://example.com/callback"],
            "grant_types": ["authorization_code"],
        }
    }
    blueprint = _create_fresh_blueprint(clients=clients)

    # Authorize with PKCE
    auth_request = MockJsonRequest(query_params={
        "response_type": "code",
        "client_id": "test-client",
        "redirect_uri": "https://example.com/callback",
        "code_challenge": code_challenge,
        "code_challenge_method": method,
    })
    auth_response = blueprint.authorize(auth_request)

    assert auth_response["status"] == 302

    # Extract code
    location = auth_response["headers"]["Location"]
    code = None
    for part in location.split("?")[1].split("&"):
        if part.startswith("code="):
            code = part.split("=", 1)[1]
            break

    # Exchange with correct verifier
    token_request = MockJsonRequest(data={
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": "https://example.com/callback",
        "client_id": "test-client",
        "client_secret": "secret",
        "code_verifier": code_verifier,
    })
    token_response = blueprint.token(token_request)

    assert token_response["status"] == 200, \
        "Expected 200, got {}".format(token_response["status"])
    assert "access_token" in token_response["body"], \
        "Expected access_token in response"

    return


def test_token_pkce_rejects_wrong_verifier():
    """
        The token endpoint should reject an incorrect PKCE code_verifier.
    """
    _, code_challenge, method = _make_pkce_pair("S256")

    clients = {
        "test-client": {
            "client_id": "test-client",
            "client_secret": "secret",
            "redirect_uris": ["https://example.com/callback"],
            "grant_types": ["authorization_code"],
        }
    }
    blueprint = _create_fresh_blueprint(clients=clients)

    # Authorize with PKCE
    auth_request = MockJsonRequest(query_params={
        "response_type": "code",
        "client_id": "test-client",
        "redirect_uri": "https://example.com/callback",
        "code_challenge": code_challenge,
        "code_challenge_method": method,
    })
    auth_response = blueprint.authorize(auth_request)

    location = auth_response["headers"]["Location"]
    code = None
    for part in location.split("?")[1].split("&"):
        if part.startswith("code="):
            code = part.split("=", 1)[1]
            break

    # Exchange with wrong verifier
    token_request = MockJsonRequest(data={
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": "https://example.com/callback",
        "client_id": "test-client",
        "client_secret": "secret",
        "code_verifier": "wrong-verifier",
    })
    token_response = blueprint.token(token_request)

    assert token_response["status"] == 400, \
        "Expected 400, got {}".format(token_response["status"])
    assert "invalid_grant" in token_response["body"]["error"], \
        "Expected invalid_grant error for PKCE failure"

    return


# =============================================================================
# Callback Endpoint Tests
# =============================================================================


def test_callback_validates_state():
    """
        The callback endpoint should validate the state parameter
        against the stored authorization request.
    """
    clients = {
        "test-client": {
            "client_id": "test-client",
            "client_secret": "secret",
            "redirect_uris": ["https://example.com/callback"],
            "grant_types": ["authorization_code"],
        }
    }
    blueprint = _create_fresh_blueprint(clients=clients)

    # Authorize with state
    auth_request = MockJsonRequest(query_params={
        "response_type": "code",
        "client_id": "test-client",
        "redirect_uri": "https://example.com/callback",
        "state": "original-state",
    })
    auth_response = blueprint.authorize(auth_request)

    location = auth_response["headers"]["Location"]
    code = None
    for part in location.split("?")[1].split("&"):
        if part.startswith("code="):
            code = part.split("=", 1)[1]
            break

    # Callback with matching state
    callback_request = MockJsonRequest(query_params={
        "code": code,
        "state": "original-state",
    })
    callback_response = blueprint.callback(callback_request)

    assert callback_response["status"] == 200, \
        "Expected 200, got {}".format(callback_response["status"])
    assert callback_response["body"]["state"] == "original-state", \
        "Expected state in callback response"

    return


def test_callback_rejects_mismatched_state():
    """
        The callback endpoint should reject requests with mismatched state.
    """
    clients = {
        "test-client": {
            "client_id": "test-client",
            "client_secret": "secret",
            "redirect_uris": ["https://example.com/callback"],
            "grant_types": ["authorization_code"],
        }
    }
    blueprint = _create_fresh_blueprint(clients=clients)

    # Authorize with state
    auth_request = MockJsonRequest(query_params={
        "response_type": "code",
        "client_id": "test-client",
        "redirect_uri": "https://example.com/callback",
        "state": "original-state",
    })
    auth_response = blueprint.authorize(auth_request)

    location = auth_response["headers"]["Location"]
    code = None
    for part in location.split("?")[1].split("&"):
        if part.startswith("code="):
            code = part.split("=", 1)[1]
            break

    # Callback with wrong state
    callback_request = MockJsonRequest(query_params={
        "code": code,
        "state": "wrong-state",
    })
    callback_response = blueprint.callback(callback_request)

    assert callback_response["status"] == 400, \
        "Expected 400, got {}".format(callback_response["status"])
    assert callback_response["body"]["error"] == "invalid_request", \
        "Expected invalid_request error for state mismatch"

    return


def test_callback_handles_error_from_provider():
    """
        The callback endpoint should handle error responses from the
        OAuth provider.
    """
    blueprint = _create_fresh_blueprint()

    request = MockJsonRequest(query_params={
        "error": "access_denied",
        "error_description": "User denied access",
        "state": "mystate",
    })

    response = blueprint.callback(request)

    assert response["status"] == 400, \
        "Expected 400, got {}".format(response["status"])
    assert response["body"]["error"] == "access_denied", \
        "Expected access_denied error"

    return


# =============================================================================
# Revoke Endpoint Tests
# =============================================================================


def test_revoke_token():
    """
        The revoke endpoint should accept and revoke a token.
    """
    blueprint = _create_fresh_blueprint()

    # Add a token to the memory store
    blueprint._memory_token_store["test-token"] = {
        "sub": "user1",
        "token_type": "refresh",
    }

    request = MockJsonRequest(data={"token": "test-token"})
    response = blueprint.revoke(request)

    assert response["status"] == 200, \
        "Expected 200, got {}".format(response["status"])
    assert "test-token" not in blueprint._memory_token_store, \
        "Expected token to be removed from store"

    return


def test_revoke_requires_token():
    """
        The revoke endpoint should return 400 when token is missing.
    """
    blueprint = _create_fresh_blueprint()

    request = MockJsonRequest(data={})
    response = blueprint.revoke(request)

    assert response["status"] == 400, \
        "Expected 400, got {}".format(response["status"])

    return


# =============================================================================
# Endpoint Enable/Disable Tests
# =============================================================================


def test_disabled_endpoints_return_404():
    """
        Disabled endpoints should return 404.
    """
    blueprint = _create_fresh_blueprint()
    blueprint.enabled_endpoints = {"token"}

    # Authorize should be disabled
    request = MockJsonRequest(query_params={
        "response_type": "code",
        "client_id": "test",
        "redirect_uri": "https://example.com/callback",
    })
    response = blueprint.authorize(request)
    assert response["status"] == 404, \
        "Expected 404 for disabled authorize endpoint"

    # Revoke should be disabled
    request = MockJsonRequest(data={"token": "test"})
    response = blueprint.revoke(request)
    assert response["status"] == 404, \
        "Expected 404 for disabled revoke endpoint"

    return


# =============================================================================
# Shared helpers for the flow hardening tests
# =============================================================================

REDIRECT_URI = "https://example.com/callback"

CONFIDENTIAL_CLIENT = {
    "client_id": "test-client",
    "client_secret": "secret",
    "redirect_uris": [REDIRECT_URI],
    "grant_types": ["authorization_code", "client_credentials", "refresh_token"],
    "scopes": ["read", "write"],
}

PUBLIC_CLIENT = {
    "client_id": "spa-client",
    "client_type": "public",
    "redirect_uris": [REDIRECT_URI],
    "grant_types": ["authorization_code"],
    "scopes": ["read"],
}


class AnonymousRequest(MockJsonRequest):
    """
        A request the authentication middleware did not authenticate.
    """

    def __init__(self, data=None, query_params=None):
        super().__init__(data=data, query_params=query_params)
        self.auth = None


def _authorize(blueprint, client_id="test-client", **extra_params):
    """
        Send an authorization request for the resource owner.
    """
    query_params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": REDIRECT_URI,
    }
    query_params.update(extra_params)

    response = blueprint.authorize(MockJsonRequest(query_params=query_params))
    return response


def _code_from(response):
    """
        Extract the authorization code from a redirect response.
    """
    location = response["headers"]["Location"]
    query = dict(parse_qsl(urlsplit(location).query))
    return query["code"]


def _exchange(blueprint, code, **overrides):
    """
        Exchange an authorization code as the confidential test client.
    """
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "client_id": "test-client",
        "client_secret": "secret",
    }
    data.update(overrides)
    data = {key: value for key, value in data.items() if value is not None}

    response = blueprint.token(MockJsonRequest(data=data))
    return response


def _clients(*clients):
    """
        Build a client registry from client records.
    """
    return {client["client_id"]: dict(client) for client in clients}


# =============================================================================
# Query Parameters From Framework Requests
# =============================================================================

def test_authorize_reads_query_parameters_from_framework_request():
    """
        The authorize endpoint must read its parameters from the framework
        Request, whose query_params object is not a dict.
    """
    blueprint = _create_fresh_blueprint(clients=_clients(CONFIDENTIAL_CLIENT))

    query_string = urlencode({
        "response_type": "code",
        "client_id": "test-client",
        "redirect_uri": REDIRECT_URI,
        "state": "abc123",
    })
    context = AuthenticationContext(principal=RESOURCE_OWNER, scheme="Test")
    request = Request(
        method="GET",
        path="/oauth/authorize",
        query_string=query_string.encode("utf-8"),
        scope={"auth": context},
    )

    response = blueprint.authorize(request)

    assert response["status"] == 302, \
        "Expected 302 redirect, got {} {!r}".format(response["status"], response["body"])

    assert "state=abc123" in response["headers"]["Location"], \
        "Expected state in redirect URL"

    return


# =============================================================================
# No Redirect To an Unvalidated URI
# =============================================================================

def test_authorize_does_not_redirect_missing_response_type_for_unknown_client():
    """
        A request that names an unknown client must be answered directly:
        redirecting to its redirect_uri would be an open redirect.
    """
    blueprint = _create_fresh_blueprint(clients={})

    response = blueprint.authorize(MockJsonRequest(query_params={
        "client_id": "x",
        "redirect_uri": "https://evil.example/landing",
    }))

    assert response["status"] == 400, \
        "Expected 400, got {}".format(response["status"])

    assert "Location" not in response.get("headers", {}), \
        "Expected no redirect to an unvalidated redirect_uri"

    return


def test_authorize_rejects_redirect_uri_not_registered_for_client():
    """
        A redirect_uri that is not one of the client's registered URIs is
        refused without redirecting.
    """
    blueprint = _create_fresh_blueprint(clients=_clients(CONFIDENTIAL_CLIENT))

    response = blueprint.authorize(MockJsonRequest(query_params={
        "response_type": "code",
        "client_id": "test-client",
        "redirect_uri": "https://evil.example/landing",
    }))

    assert response["status"] == 400, \
        "Expected 400, got {}".format(response["status"])

    assert "Location" not in response.get("headers", {}), \
        "Expected no redirect to an unregistered redirect_uri"

    return


def test_authorize_rejects_client_without_registered_redirect_uris():
    """
        A client with an empty redirect_uris list has no valid redirect
        URI; it must not be treated as "any URI is allowed".
    """
    client = dict(CONFIDENTIAL_CLIENT)
    client["redirect_uris"] = []
    blueprint = _create_fresh_blueprint(clients=_clients(client))

    response = _authorize(blueprint)

    assert response["status"] == 400, \
        "Expected 400, got {}".format(response["status"])

    assert "Location" not in response.get("headers", {}), \
        "Expected no redirect for a client without registered redirect URIs"

    return


def test_authorize_redirects_errors_once_redirect_uri_is_validated():
    """
        After the client and redirect_uri are validated, protocol errors
        are reported to the redirect URI.
    """
    blueprint = _create_fresh_blueprint(clients=_clients(CONFIDENTIAL_CLIENT))

    response = _authorize(blueprint, response_type="token", state="s1")

    assert response["status"] == 302, \
        "Expected 302, got {}".format(response["status"])

    location = response["headers"]["Location"]
    assert location.startswith(REDIRECT_URI), \
        "Expected a redirect to the registered URI, got {!r}".format(location)
    assert "error=unsupported_response_type" in location, \
        "Expected the error in the redirect, got {!r}".format(location)

    return


# =============================================================================
# Resource Owner Authentication and Code Binding
# =============================================================================

def test_authorize_requires_logged_in_resource_owner():
    """
        Without an authenticated user there is nobody to authorize the
        client, so no code is issued.
    """
    blueprint = _create_fresh_blueprint(clients=_clients(CONFIDENTIAL_CLIENT))

    response = blueprint.authorize(AnonymousRequest(query_params={
        "response_type": "code",
        "client_id": "test-client",
        "redirect_uri": REDIRECT_URI,
    }))

    assert response["status"] == 401, \
        "Expected 401, got {}".format(response["status"])

    assert response["body"]["error"] == "login_required", \
        "Expected login_required, got {!r}".format(response["body"])

    return


def test_tokens_are_issued_for_the_resource_owner_not_the_client():
    """
        The tokens obtained for a code name the user who approved the
        request as subject and the client as client_id.
    """
    blueprint = _create_fresh_blueprint(clients=_clients(CONFIDENTIAL_CLIENT))

    code = _code_from(_authorize(blueprint))
    token_response = _exchange(blueprint, code)

    assert token_response["status"] == 200, \
        "Expected 200, got {} {!r}".format(token_response["status"], token_response["body"])

    claims = decode_jwt(
        token_response["body"]["access_token"], "test-secret", algorithms=["HS256"]
    )

    assert claims["sub"] == RESOURCE_OWNER.identifier, \
        "Expected sub to be the resource owner, got {!r}".format(claims["sub"])
    assert claims["client_id"] == "test-client", \
        "Expected client_id claim, got {!r}".format(claims.get("client_id"))

    return


def test_authorize_honours_denied_consent():
    """
        When approve_authorization returns False the client receives
        access_denied instead of a code.
    """
    blueprint = _create_fresh_blueprint(clients=_clients(CONFIDENTIAL_CLIENT))
    blueprint.approve_authorization = classmethod(
        lambda cls, request, principal, client, scope: False
    )

    response = _authorize(blueprint)

    location = response["headers"]["Location"]
    assert "error=access_denied" in location and "code=" not in location, \
        "Expected access_denied and no code, got {!r}".format(location)

    return


# =============================================================================
# Client Authentication at the Token Endpoint
# =============================================================================

def test_token_requires_secret_from_confidential_client():
    """
        A confidential client that does not present its secret cannot
        exchange a code, even one it intercepted.
    """
    blueprint = _create_fresh_blueprint(clients=_clients(CONFIDENTIAL_CLIENT))

    code = _code_from(_authorize(blueprint))
    response = _exchange(blueprint, code, client_secret=None)

    assert response["status"] == 401, \
        "Expected 401, got {}".format(response["status"])
    assert response["body"]["error"] == "invalid_client", \
        "Expected invalid_client, got {!r}".format(response["body"])

    return


def test_token_rejects_wrong_client_secret():
    """
        A wrong client secret is refused.
    """
    blueprint = _create_fresh_blueprint(clients=_clients(CONFIDENTIAL_CLIENT))

    code = _code_from(_authorize(blueprint))
    response = _exchange(blueprint, code, client_secret="wrong")

    assert response["status"] == 401, \
        "Expected 401, got {}".format(response["status"])

    return


def test_token_requires_client_id():
    """
        The token request must name the client; the code alone is not
        enough.
    """
    blueprint = _create_fresh_blueprint(clients=_clients(CONFIDENTIAL_CLIENT))

    code = _code_from(_authorize(blueprint))
    response = _exchange(blueprint, code, client_id=None, client_secret=None)

    assert response["status"] == 400, \
        "Expected 400, got {}".format(response["status"])
    assert response["body"]["error"] == "invalid_request", \
        "Expected invalid_request, got {!r}".format(response["body"])

    return


def test_token_requires_matching_redirect_uri():
    """
        The token request must repeat the redirect URI the code was issued
        for.
    """
    blueprint = _create_fresh_blueprint(clients=_clients(CONFIDENTIAL_CLIENT))

    code = _code_from(_authorize(blueprint))
    response = _exchange(blueprint, code, redirect_uri=None)

    assert response["status"] == 400, \
        "Expected 400, got {}".format(response["status"])
    assert response["body"]["error"] == "invalid_grant", \
        "Expected invalid_grant, got {!r}".format(response["body"])

    return


def test_authorize_requires_pkce_from_public_client():
    """
        A public client has no secret, so it must use PKCE.
    """
    blueprint = _create_fresh_blueprint(clients=_clients(PUBLIC_CLIENT))

    response = _authorize(blueprint, client_id="spa-client")

    location = response["headers"]["Location"]
    assert "error=invalid_request" in location and "code=" not in location, \
        "Expected invalid_request without a code, got {!r}".format(location)

    return


def test_public_client_exchanges_code_with_pkce_verifier():
    """
        A public client exchanges its code by presenting the PKCE verifier
        instead of a secret.
    """
    code_verifier, code_challenge, method = _make_pkce_pair("S256")
    blueprint = _create_fresh_blueprint(clients=_clients(PUBLIC_CLIENT))

    code = _code_from(_authorize(
        blueprint,
        client_id="spa-client",
        code_challenge=code_challenge,
        code_challenge_method=method,
    ))

    response = blueprint.token(MockJsonRequest(data={
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "client_id": "spa-client",
        "code_verifier": code_verifier,
    }))

    assert response["status"] == 200, \
        "Expected 200, got {} {!r}".format(response["status"], response["body"])

    return


def test_token_accepts_http_basic_client_authentication():
    """
        The client may authenticate with an HTTP Basic Authorization
        header instead of body fields.
    """
    blueprint = _create_fresh_blueprint(clients=_clients(CONFIDENTIAL_CLIENT))

    code = _code_from(_authorize(blueprint))

    request = MockJsonRequest(data={
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
    })
    encoded = base64.b64encode(b"test-client:secret").decode("ascii")
    request.headers = {"Authorization": "Basic {}".format(encoded)}

    response = blueprint.token(request)

    assert response["status"] == 200, \
        "Expected 200, got {} {!r}".format(response["status"], response["body"])

    return


# =============================================================================
# Authorization Code Lifetime
# =============================================================================

def test_expired_authorization_code_is_refused():
    """
        A code older than authorization_code_lifetime can no longer be
        exchanged.
    """
    blueprint = _create_fresh_blueprint(clients=_clients(CONFIDENTIAL_CLIENT))

    code = _code_from(_authorize(blueprint))

    # Age the stored code beyond its lifetime
    stored = blueprint._memory_code_store[code]
    stored["created_at"] = time.time() - blueprint.authorization_code_lifetime - 1
    stored["expires_at"] = time.time() - 1

    response = _exchange(blueprint, code)

    assert response["status"] == 400, \
        "Expected 400, got {}".format(response["status"])
    assert response["body"]["error"] == "invalid_grant", \
        "Expected invalid_grant, got {!r}".format(response["body"])

    return


def test_authorization_code_can_be_exchanged_only_once():
    """
        A code is single use.
    """
    blueprint = _create_fresh_blueprint(clients=_clients(CONFIDENTIAL_CLIENT))

    code = _code_from(_authorize(blueprint))

    first = _exchange(blueprint, code)
    second = _exchange(blueprint, code)

    assert first["status"] == 200, \
        "Expected 200 for the first exchange, got {}".format(first["status"])
    assert second["status"] == 400, \
        "Expected 400 for the second exchange, got {}".format(second["status"])

    return


def test_authorize_refuses_code_store_that_cannot_keep_the_user():
    """
        A code store whose store_code has no user_id argument would lose
        the resource owner, so no code is issued through it.
    """
    store = MockCodeStore()
    blueprint = _create_fresh_blueprint(clients=_clients(CONFIDENTIAL_CLIENT))
    blueprint.authorization_code_store = store

    response = _authorize(blueprint)

    location = response["headers"]["Location"]
    assert "error=server_error" in location and "code=" not in location, \
        "Expected server_error without a code, got {!r}".format(location)
    assert len(store._codes) == 0, \
        "Expected nothing to be stored"

    return


# =============================================================================
# Scopes
# =============================================================================

def test_authorize_refuses_scope_not_registered_for_client():
    """
        A client cannot obtain a scope it is not registered for.
    """
    blueprint = _create_fresh_blueprint(clients=_clients(CONFIDENTIAL_CLIENT))

    response = _authorize(blueprint, scope="admin")

    location = response["headers"]["Location"]
    assert "error=invalid_scope" in location and "code=" not in location, \
        "Expected invalid_scope without a code, got {!r}".format(location)

    return


def test_client_credentials_scope_is_limited_to_client_registration():
    """
        The client credentials grant grants only registered scopes.
    """
    blueprint = _create_fresh_blueprint(clients=_clients(CONFIDENTIAL_CLIENT))

    response = blueprint.token(MockJsonRequest(data={
        "grant_type": "client_credentials",
        "client_id": "test-client",
        "client_secret": "secret",
        "scope": "read admin",
    }))

    assert response["status"] == 200, \
        "Expected 200, got {} {!r}".format(response["status"], response["body"])
    assert response["body"]["scope"] == "read", \
        "Expected the granted scope 'read', got {!r}".format(response["body"].get("scope"))

    return


def test_refresh_cannot_widen_scope():
    """
        A refresh request cannot name a scope the refresh token does not
        carry.
    """
    blueprint = _create_fresh_blueprint(clients=_clients(CONFIDENTIAL_CLIENT))

    code = _code_from(_authorize(blueprint, scope="read"))
    refresh_token = _exchange(blueprint, code)["body"]["refresh_token"]

    response = blueprint.token(MockJsonRequest(data={
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "scope": "read write",
    }))

    assert response["status"] == 400, \
        "Expected 400, got {}".format(response["status"])
    assert response["body"]["error"] == "invalid_scope", \
        "Expected invalid_scope, got {!r}".format(response["body"])

    return


def test_refresh_keeps_scope_and_subject_of_refresh_token():
    """
        A refresh issues an access token for the same user with the scope
        of the refresh token.
    """
    blueprint = _create_fresh_blueprint(clients=_clients(CONFIDENTIAL_CLIENT))

    code = _code_from(_authorize(blueprint, scope="read"))
    refresh_token = _exchange(blueprint, code)["body"]["refresh_token"]

    response = blueprint.token(MockJsonRequest(data={
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }))

    assert response["status"] == 200, \
        "Expected 200, got {} {!r}".format(response["status"], response["body"])

    claims = decode_jwt(response["body"]["access_token"], "test-secret", algorithms=["HS256"])
    assert claims["sub"] == RESOURCE_OWNER.identifier and claims.get("scope") == "read", \
        "Expected the user and scope of the refresh token, got {!r}".format(claims)

    return


def test_revoked_refresh_token_is_refused():
    """
        A refresh token revoked at the revoke endpoint mints no more
        access tokens.
    """
    blueprint = _create_fresh_blueprint(clients=_clients(CONFIDENTIAL_CLIENT))
    blueprint.revocation_list = InMemoryTokenRevocationList()

    code = _code_from(_authorize(blueprint))
    refresh_token = _exchange(blueprint, code)["body"]["refresh_token"]

    blueprint.revoke(MockJsonRequest(data={"token": refresh_token}))

    response = blueprint.token(MockJsonRequest(data={
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }))

    assert response["status"] == 401, \
        "Expected 401, got {}".format(response["status"])

    return


# =============================================================================
# Token Request Bodies
# =============================================================================

def test_token_accepts_form_encoded_body_from_framework_request():
    """
        The token endpoint must read application/x-www-form-urlencoded
        bodies, which is what OAuth 2.0 clients send.
    """
    blueprint = _create_fresh_blueprint(clients=_clients(CONFIDENTIAL_CLIENT))

    body = urlencode({
        "grant_type": "client_credentials",
        "client_id": "test-client",
        "client_secret": "secret",
    })
    request = Request(
        method="POST",
        path="/oauth/token",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        body=body.encode("utf-8"),
    )

    response = blueprint.token(request)

    assert response["status"] == 200, \
        "Expected 200, got {} {!r}".format(response["status"], response["body"])

    return


def test_token_rejects_body_that_is_not_an_object():
    """
        A JSON array body is answered with 400 invalid_request.
    """
    blueprint = _create_fresh_blueprint(clients=_clients(CONFIDENTIAL_CLIENT))

    request = Request(
        method="POST",
        path="/oauth/token",
        headers={"Content-Type": "application/json"},
        body=b"[]",
    )

    response = blueprint.token(request)

    assert response["status"] == 400, \
        "Expected 400, got {}".format(response["status"])
    assert response["body"]["error"] == "invalid_request", \
        "Expected invalid_request, got {!r}".format(response["body"])

    return
