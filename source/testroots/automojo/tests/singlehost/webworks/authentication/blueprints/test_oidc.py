"""
    Unit tests for the OIDCBlueprint class.

    Tests cover the OIDC-specific endpoints: discovery, userinfo, and
    jwks_endpoint, as well as the id_token inclusion in token responses.
"""

import json
import time

from automojo.webworks.authentication.bearer import decode_jwt, encode_jwt
from automojo.webworks.authentication.blueprints.oidc import OIDCBlueprint


# =============================================================================
# Test Helpers
# =============================================================================


class MockJsonRequest:
    """
        A simple mock request that returns a JSON body dictionary
        and optionally carries query parameters and host information.
    """

    def __init__(self, data=None, query_params=None, scheme="https",
                 host="example.com", subject=None):
        self._data = data or {}
        self.query_params = query_params or {}
        self.scheme = scheme
        self.host = host
        self.subject = subject

    def json(self):
        return self._data


def _create_fresh_blueprint(
    jwt_secret="test-oidc-secret",
    issuer=None,
    jwks=None,
    supported_scopes=None,
    supported_claims=None,
    id_token_lifetime=3600,
    claim_mappings=None,
    users=None,
    clients=None
):
    """
        Create a fresh OIDCBlueprint subclass to avoid class-level
        state leakage between tests.
    """

    class FreshBlueprint(OIDCBlueprint):
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
    FreshBlueprint.require_pkce = False
    FreshBlueprint.enabled_endpoints = None
    FreshBlueprint.auth_system = None
    FreshBlueprint.base_path = "/oidc"
    FreshBlueprint._memory_code_store = {}
    FreshBlueprint._memory_client_store = {}
    FreshBlueprint._memory_token_store = {}
    FreshBlueprint._memory_user_store = {}

    FreshBlueprint.issuer = issuer
    FreshBlueprint.jwks = jwks
    FreshBlueprint.id_token_lifetime = id_token_lifetime
    FreshBlueprint.claim_mappings = claim_mappings

    if supported_scopes is not None:
        FreshBlueprint.supported_scopes = supported_scopes
    else:
        FreshBlueprint.supported_scopes = ["openid", "profile", "email"]

    if supported_claims is not None:
        FreshBlueprint.supported_claims = supported_claims
    else:
        FreshBlueprint.supported_claims = [
            "sub", "name", "email", "email_verified"
        ]

    if users:
        FreshBlueprint._memory_user_store = dict(users)

    if clients:
        FreshBlueprint._memory_client_store = dict(clients)

    return FreshBlueprint


# =============================================================================
# Discovery Endpoint Tests
# =============================================================================


def test_discovery_returns_oidc_configuration():
    """
        The discovery endpoint should return a valid OIDC discovery
        document with all required fields.
    """
    blueprint = _create_fresh_blueprint(issuer="https://auth.example.com")

    request = MockJsonRequest(scheme="https", host="auth.example.com")
    response = blueprint.discovery(request)

    if response["status"] != 200:
        errmsg = "Expected status 200, got {}".format(response["status"])
        raise AssertionError(errmsg)

    body = response["body"]

    if body["issuer"] != "https://auth.example.com":
        errmsg = "Expected issuer 'https://auth.example.com', got {!r}".format(
            body["issuer"]
        )
        raise AssertionError(errmsg)

    required_fields = [
        "issuer",
        "authorization_endpoint",
        "token_endpoint",
        "userinfo_endpoint",
        "jwks_uri",
        "response_types_supported",
        "subject_types_supported",
        "id_token_signing_alg_values_supported",
        "scopes_supported",
        "claims_supported",
    ]
    for field_name in required_fields:
        if field_name not in body:
            errmsg = "Missing required field '{}' in discovery document".format(
                field_name
            )
            raise AssertionError(errmsg)

    return


def test_discovery_uses_request_base_url_when_no_issuer():
    """
        When no issuer is configured, the discovery endpoint should
        derive the issuer from the request.
    """
    blueprint = _create_fresh_blueprint(issuer=None)

    request = MockJsonRequest(scheme="https", host="myapp.example.com")
    response = blueprint.discovery(request)

    body = response["body"]

    if body["issuer"] != "https://myapp.example.com":
        errmsg = "Expected issuer derived from request, got {!r}".format(
            body["issuer"]
        )
        raise AssertionError(errmsg)

    return


def test_discovery_endpoint_paths():
    """
        The discovery document should contain correct endpoint paths
        relative to the base URL and base_path.
    """
    blueprint = _create_fresh_blueprint(issuer="https://auth.example.com")

    request = MockJsonRequest(scheme="https", host="auth.example.com")
    response = blueprint.discovery(request)

    body = response["body"]

    expected_auth = "https://auth.example.com/oidc/authorize"
    if body["authorization_endpoint"] != expected_auth:
        errmsg = "Expected authorization_endpoint {!r}, got {!r}".format(
            expected_auth, body["authorization_endpoint"]
        )
        raise AssertionError(errmsg)

    expected_token = "https://auth.example.com/oidc/token"
    if body["token_endpoint"] != expected_token:
        errmsg = "Expected token_endpoint {!r}, got {!r}".format(
            expected_token, body["token_endpoint"]
        )
        raise AssertionError(errmsg)

    expected_userinfo = "https://auth.example.com/oidc/userinfo"
    if body["userinfo_endpoint"] != expected_userinfo:
        errmsg = "Expected userinfo_endpoint {!r}, got {!r}".format(
            expected_userinfo, body["userinfo_endpoint"]
        )
        raise AssertionError(errmsg)

    expected_jwks = "https://auth.example.com/.well-known/jwks.json"
    if body["jwks_uri"] != expected_jwks:
        errmsg = "Expected jwks_uri {!r}, got {!r}".format(
            expected_jwks, body["jwks_uri"]
        )
        raise AssertionError(errmsg)

    return


def test_discovery_disabled_returns_404():
    """
        When the discovery endpoint is disabled, it should return 404.
    """
    blueprint = _create_fresh_blueprint()
    blueprint.enabled_endpoints = {"token", "authorize"}

    request = MockJsonRequest()
    response = blueprint.discovery(request)

    if response["status"] != 404:
        errmsg = "Expected status 404 for disabled endpoint, got {}".format(
            response["status"]
        )
        raise AssertionError(errmsg)

    return


# =============================================================================
# JWKS Endpoint Tests
# =============================================================================


def test_jwks_returns_configured_keys():
    """
        The JWKS endpoint should return the configured JWKS document.
    """
    test_jwks = {
        "keys": [
            {
                "kty": "RSA",
                "kid": "test-key-1",
                "use": "sig",
                "n": "test-modulus",
                "e": "AQAB"
            }
        ]
    }
    blueprint = _create_fresh_blueprint(jwks=test_jwks)

    request = MockJsonRequest()
    response = blueprint.jwks_endpoint(request)

    if response["status"] != 200:
        errmsg = "Expected status 200, got {}".format(response["status"])
        raise AssertionError(errmsg)

    if response["body"] != test_jwks:
        errmsg = "Expected JWKS body to match configured keys"
        raise AssertionError(errmsg)

    return


def test_jwks_returns_empty_keys_when_not_configured():
    """
        When no JWKS is configured, the endpoint should return an
        empty keys array.
    """
    blueprint = _create_fresh_blueprint(jwks=None)

    request = MockJsonRequest()
    response = blueprint.jwks_endpoint(request)

    if response["status"] != 200:
        errmsg = "Expected status 200, got {}".format(response["status"])
        raise AssertionError(errmsg)

    if response["body"] != {"keys": []}:
        errmsg = "Expected empty keys array, got {!r}".format(
            response["body"]
        )
        raise AssertionError(errmsg)

    return


def test_jwks_disabled_returns_404():
    """
        When the JWKS endpoint is disabled, it should return 404.
    """
    blueprint = _create_fresh_blueprint()
    blueprint.enabled_endpoints = {"token"}

    request = MockJsonRequest()
    response = blueprint.jwks_endpoint(request)

    if response["status"] != 404:
        errmsg = "Expected status 404 for disabled endpoint, got {}".format(
            response["status"]
        )
        raise AssertionError(errmsg)

    return


# =============================================================================
# UserInfo Endpoint Tests
# =============================================================================


def test_userinfo_returns_claims_for_authenticated_user():
    """
        The userinfo endpoint should return claims for an authenticated
        user identified by the request subject.
    """
    users = {
        "user-123": {
            "name": "Test User",
            "email": "test@example.com",
            "email_verified": True,
        }
    }
    blueprint = _create_fresh_blueprint(users=users)

    request = MockJsonRequest(subject="user-123")
    response = blueprint.userinfo(request)

    if response["status"] != 200:
        errmsg = "Expected status 200, got {}".format(response["status"])
        raise AssertionError(errmsg)

    body = response["body"]

    if body.get("sub") != "user-123":
        errmsg = "Expected sub='user-123', got {!r}".format(body.get("sub"))
        raise AssertionError(errmsg)

    if body.get("name") != "Test User":
        errmsg = "Expected name='Test User', got {!r}".format(
            body.get("name")
        )
        raise AssertionError(errmsg)

    if body.get("email") != "test@example.com":
        errmsg = "Expected email='test@example.com', got {!r}".format(
            body.get("email")
        )
        raise AssertionError(errmsg)

    return


def test_userinfo_returns_401_when_not_authenticated():
    """
        The userinfo endpoint should return 401 when no authenticated
        user is present in the request.
    """
    blueprint = _create_fresh_blueprint()

    request = MockJsonRequest()
    response = blueprint.userinfo(request)

    if response["status"] != 401:
        errmsg = "Expected status 401, got {}".format(response["status"])
        raise AssertionError(errmsg)

    return


def test_userinfo_returns_401_for_unknown_user():
    """
        The userinfo endpoint should return 401 when the authenticated
        subject is not found in the user store.
    """
    blueprint = _create_fresh_blueprint(users={})

    request = MockJsonRequest(subject="unknown-user")
    response = blueprint.userinfo(request)

    if response["status"] != 401:
        errmsg = "Expected status 401, got {}".format(response["status"])
        raise AssertionError(errmsg)

    return


def test_userinfo_disabled_returns_404():
    """
        When the userinfo endpoint is disabled, it should return 404.
    """
    blueprint = _create_fresh_blueprint()
    blueprint.enabled_endpoints = {"token"}

    request = MockJsonRequest(subject="user-123")
    response = blueprint.userinfo(request)

    if response["status"] != 404:
        errmsg = "Expected status 404 for disabled endpoint, got {}".format(
            response["status"]
        )
        raise AssertionError(errmsg)

    return


# =============================================================================
# Token Response with id_token Tests
# =============================================================================


def test_token_response_includes_id_token():
    """
        When issuing tokens via the authorization code grant, the
        response should include an id_token with standard OIDC claims.
    """
    client_id = "test-client"
    redirect_uri = "https://app.example.com/callback"

    clients = {
        client_id: {
            "client_id": client_id,
            "client_secret": "test-secret",
            "redirect_uris": [redirect_uri],
            "grant_types": ["authorization_code"],
        }
    }

    blueprint = _create_fresh_blueprint(
        issuer="https://auth.example.com",
        clients=clients
    )

    # First, create an authorization code
    auth_request = MockJsonRequest(query_params={
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "state": "test-state",
    })
    auth_response = blueprint.authorize(auth_request)

    if auth_response["status"] != 302:
        errmsg = "Expected 302 redirect, got {}".format(
            auth_response["status"]
        )
        raise AssertionError(errmsg)

    # Extract the code from the redirect URL
    location = auth_response["headers"]["Location"]
    from urllib.parse import urlparse, parse_qs
    parsed = urlparse(location)
    params = parse_qs(parsed.query)
    code = params["code"][0]

    # Exchange the code for tokens
    token_request = MockJsonRequest(data={
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
        "client_id": client_id,
    })
    token_response = blueprint.token(token_request)

    if token_response["status"] != 200:
        errmsg = "Expected status 200, got {}".format(
            token_response["status"]
        )
        raise AssertionError(errmsg)

    body = token_response["body"]

    if "id_token" not in body:
        errmsg = "Expected id_token in token response body"
        raise AssertionError(errmsg)

    # Decode and verify the id_token claims
    id_token = body["id_token"]
    claims = decode_jwt(
        id_token,
        "test-oidc-secret",
        algorithms=["HS256"],
        verify_exp=False
    )

    required_claims = ["iss", "sub", "aud", "exp", "iat"]
    for claim_name in required_claims:
        if claim_name not in claims:
            errmsg = "Missing required claim '{}' in id_token".format(
                claim_name
            )
            raise AssertionError(errmsg)

    if claims["iss"] != "https://auth.example.com":
        errmsg = "Expected iss='https://auth.example.com', got {!r}".format(
            claims["iss"]
        )
        raise AssertionError(errmsg)

    return


def test_token_response_id_token_has_correct_expiration():
    """
        The id_token should have an expiration matching the configured
        id_token_lifetime.
    """
    client_id = "test-client"
    redirect_uri = "https://app.example.com/callback"
    id_token_lifetime = 1800

    clients = {
        client_id: {
            "client_id": client_id,
            "client_secret": "test-secret",
            "redirect_uris": [redirect_uri],
            "grant_types": ["authorization_code"],
        }
    }

    blueprint = _create_fresh_blueprint(
        issuer="https://auth.example.com",
        clients=clients,
        id_token_lifetime=id_token_lifetime
    )

    # Create an authorization code
    auth_request = MockJsonRequest(query_params={
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
    })
    auth_response = blueprint.authorize(auth_request)
    location = auth_response["headers"]["Location"]
    from urllib.parse import urlparse, parse_qs
    parsed = urlparse(location)
    params = parse_qs(parsed.query)
    code = params["code"][0]

    # Exchange for tokens
    before_time = int(time.time())
    token_request = MockJsonRequest(data={
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
        "client_id": client_id,
    })
    token_response = blueprint.token(token_request)
    after_time = int(time.time())

    id_token = token_response["body"]["id_token"]
    claims = decode_jwt(
        id_token,
        "test-oidc-secret",
        algorithms=["HS256"],
        verify_exp=False
    )

    expected_min = before_time + id_token_lifetime
    expected_max = after_time + id_token_lifetime

    if claims["exp"] < expected_min or claims["exp"] > expected_max:
        errmsg = (
            "Expected exp between {} and {}, got {}".format(
                expected_min, expected_max, claims["exp"]
            )
        )
        raise AssertionError(errmsg)

    return


def test_claim_mappings_applied_to_id_token():
    """
        When claim_mappings are configured, the id_token should include
        the mapped claims from user data.
    """
    client_id = "test-client"
    redirect_uri = "https://app.example.com/callback"

    clients = {
        client_id: {
            "client_id": client_id,
            "client_secret": "test-secret",
            "redirect_uris": [redirect_uri],
            "grant_types": ["authorization_code"],
        }
    }

    users = {
        client_id: {
            "full_name": "Test User",
            "mail": "test@example.com",
        }
    }

    mappings = {
        "name": lambda data: data.get("full_name"),
        "email": lambda data: data.get("mail"),
    }

    blueprint = _create_fresh_blueprint(
        issuer="https://auth.example.com",
        clients=clients,
        users=users,
        claim_mappings=mappings
    )

    # Create an authorization code
    auth_request = MockJsonRequest(query_params={
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
    })
    auth_response = blueprint.authorize(auth_request)
    location = auth_response["headers"]["Location"]
    from urllib.parse import urlparse, parse_qs
    parsed = urlparse(location)
    params = parse_qs(parsed.query)
    code = params["code"][0]

    # Exchange for tokens
    token_request = MockJsonRequest(data={
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
        "client_id": client_id,
    })
    token_response = blueprint.token(token_request)

    id_token = token_response["body"]["id_token"]
    claims = decode_jwt(
        id_token,
        "test-oidc-secret",
        algorithms=["HS256"],
        verify_exp=False
    )

    if claims.get("name") != "Test User":
        errmsg = "Expected name='Test User' in id_token, got {!r}".format(
            claims.get("name")
        )
        raise AssertionError(errmsg)

    if claims.get("email") != "test@example.com":
        errmsg = "Expected email='test@example.com' in id_token, got {!r}".format(
            claims.get("email")
        )
        raise AssertionError(errmsg)

    return


# =============================================================================
# Inherited OAuth2 Endpoint Tests
# =============================================================================


def test_oidc_inherits_oauth2_authorize():
    """
        The OIDCBlueprint should inherit the authorize endpoint from
        OAuth2Blueprint.
    """
    client_id = "test-client"
    redirect_uri = "https://app.example.com/callback"

    clients = {
        client_id: {
            "client_id": client_id,
            "client_secret": "test-secret",
            "redirect_uris": [redirect_uri],
            "grant_types": ["authorization_code"],
        }
    }

    blueprint = _create_fresh_blueprint(clients=clients)

    request = MockJsonRequest(query_params={
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "state": "test-state",
    })
    response = blueprint.authorize(request)

    if response["status"] != 302:
        errmsg = "Expected 302 redirect from inherited authorize, got {}".format(
            response["status"]
        )
        raise AssertionError(errmsg)

    return


def test_oidc_inherits_oauth2_revoke():
    """
        The OIDCBlueprint should inherit the revoke endpoint from
        OAuth2Blueprint.
    """
    blueprint = _create_fresh_blueprint()

    request = MockJsonRequest(data={"token": "some-token"})
    response = blueprint.revoke(request)

    if response["status"] != 200:
        errmsg = "Expected status 200 from inherited revoke, got {}".format(
            response["status"]
        )
        raise AssertionError(errmsg)

    return
