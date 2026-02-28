"""
    Unit tests for the OAuth2Blueprint.

    Tests cover the authorize, token, callback, and revoke endpoints
    including Authorization Code flow, Client Credentials flow, PKCE
    support, state validation, and redirect URI validation.
"""

import hashlib
import secrets

from base64 import urlsafe_b64encode
from typing import Any, Dict, List, Optional

from automojo.webworks.authentication.blueprints.oauth2 import (
    AuthorizationCodeStore,
    OAuth2Blueprint,
    OAuth2ClientStore,
)
from automojo.webworks.authentication.blueprints.responses import AuthError


# =============================================================================
# Test Helpers
# =============================================================================


class MockJsonRequest:
    """
        A simple mock request that returns a JSON body dictionary
        and optionally carries query parameters.
    """

    def __init__(self, data=None, query_params=None):
        self._data = data or {}
        self.query_params = query_params or {}

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
        The authorize endpoint should redirect with error for unknown clients.
    """
    blueprint = _create_fresh_blueprint(clients={})

    request = MockJsonRequest(query_params={
        "response_type": "code",
        "client_id": "unknown-client",
        "redirect_uri": "https://example.com/callback",
        "state": "xyz",
    })

    response = blueprint.authorize(request)

    assert response["status"] == 302, \
        "Expected 302 redirect, got {}".format(response["status"])

    location = response["headers"]["Location"]
    assert "error=invalid_client" in location, \
        "Expected invalid_client error in redirect"

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
