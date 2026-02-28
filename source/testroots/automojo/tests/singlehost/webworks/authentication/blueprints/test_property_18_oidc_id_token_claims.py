"""
    Property test for OIDC ID token claims.

    Property 18: OIDC ID Token Claims
        When issuing tokens, the OIDC blueprint SHALL include id_token
        with standard claims (iss, sub, aud, exp, iat).

    **Validates: Requirements 7.5**
"""

import random
import string
import time

from urllib.parse import urlparse, parse_qs

from automojo.webworks.authentication.bearer import decode_jwt
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
                 host="example.com"):
        self._data = data or {}
        self.query_params = query_params or {}
        self.scheme = scheme
        self.host = host

    def json(self):
        return self._data


def _random_string(min_len=1, max_len=30):
    """
        Generate a random alphanumeric string.

        :param min_len: Minimum string length.
        :param max_len: Maximum string length.

        :returns: A random string.
    """
    length = random.randint(min_len, max_len)
    chars = string.ascii_letters + string.digits
    result = "".join(random.choice(chars) for _ in range(length))
    return result


def _create_fresh_blueprint(issuer=None, jwt_secret="test-oidc-secret",
                            id_token_lifetime=3600, clients=None):
    """
        Create a fresh OIDCBlueprint subclass to avoid class-level
        state leakage between iterations.

        :param issuer: The OIDC issuer identifier.
        :param jwt_secret: The JWT signing secret.
        :param id_token_lifetime: Lifetime of ID tokens in seconds.
        :param clients: Dictionary of client_id -> client data.

        :returns: The fresh blueprint class.
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
    FreshBlueprint.jwks = None
    FreshBlueprint.id_token_lifetime = id_token_lifetime
    FreshBlueprint.claim_mappings = None
    FreshBlueprint.supported_scopes = ["openid", "profile", "email"]
    FreshBlueprint.supported_claims = [
        "sub", "name", "email", "email_verified"
    ]

    if clients:
        FreshBlueprint._memory_client_store = dict(clients)

    return FreshBlueprint


# =============================================================================
# Property Tests
# =============================================================================


def test_property_18_oidc_id_token_claims():
    """
        Property 18: OIDC ID Token Claims.

        For any OIDC token response, the id_token SHALL contain at
        minimum the sub, iss, aud, exp, and iat claims.

        For each iteration, generates a random issuer, client, and
        redirect URI, then performs an authorization code flow and
        verifies the id_token contains all required standard claims.

        **Validates: Requirements 7.5**
    """
    num_iterations = 100

    for iteration in range(num_iterations):
        # Generate random values for this iteration
        issuer_domain = _random_string(3, 12).lower()
        issuer = "https://{}.example.com".format(issuer_domain)
        jwt_secret = _random_string(16, 32)
        id_token_lifetime = random.randint(300, 7200)

        client_id = _random_string(5, 20)
        redirect_domain = _random_string(3, 10).lower()
        redirect_uri = "https://{}.example.com/callback".format(
            redirect_domain
        )

        clients = {
            client_id: {
                "client_id": client_id,
                "client_secret": _random_string(10, 20),
                "redirect_uris": [redirect_uri],
                "grant_types": ["authorization_code"],
            }
        }

        blueprint = _create_fresh_blueprint(
            issuer=issuer,
            jwt_secret=jwt_secret,
            id_token_lifetime=id_token_lifetime,
            clients=clients
        )

        # Step 1: Authorize to get an authorization code
        state = _random_string(8, 20)
        auth_request = MockJsonRequest(query_params={
            "response_type": "code",
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "state": state,
        })
        auth_response = blueprint.authorize(auth_request)

        if auth_response["status"] != 302:
            errmsg = (
                "Iteration {}: Expected 302 redirect from authorize, "
                "got {}".format(iteration, auth_response["status"])
            )
            raise AssertionError(errmsg)

        # Extract the authorization code from the redirect URL
        location = auth_response["headers"]["Location"]
        parsed = urlparse(location)
        params = parse_qs(parsed.query)

        if "code" not in params:
            errmsg = (
                "Iteration {}: Expected 'code' parameter in redirect "
                "URL".format(iteration)
            )
            raise AssertionError(errmsg)

        code = params["code"][0]

        # Step 2: Exchange the code for tokens
        before_time = int(time.time())
        token_request = MockJsonRequest(data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": client_id,
        })
        token_response = blueprint.token(token_request)
        after_time = int(time.time())

        if token_response["status"] != 200:
            errmsg = (
                "Iteration {}: Expected status 200 from token endpoint, "
                "got {}".format(iteration, token_response["status"])
            )
            raise AssertionError(errmsg)

        body = token_response["body"]

        # Step 3: Verify id_token is present
        if "id_token" not in body:
            errmsg = (
                "Iteration {}: Expected 'id_token' in token response "
                "body, got keys: {!r}".format(iteration, list(body.keys()))
            )
            raise AssertionError(errmsg)

        # Step 4: Decode and verify the id_token claims
        id_token = body["id_token"]
        claims = decode_jwt(
            id_token,
            jwt_secret,
            algorithms=["HS256"],
            verify_exp=False
        )

        # Verify all required standard claims are present
        required_claims = ["iss", "sub", "aud", "exp", "iat"]
        for claim_name in required_claims:
            if claim_name not in claims:
                errmsg = (
                    "Iteration {}: Missing required claim '{}' in "
                    "id_token. Present claims: {!r}".format(
                        iteration, claim_name, list(claims.keys())
                    )
                )
                raise AssertionError(errmsg)

        # Verify iss matches the configured issuer
        if claims["iss"] != issuer:
            errmsg = (
                "Iteration {}: Expected iss={!r}, got {!r}".format(
                    iteration, issuer, claims["iss"]
                )
            )
            raise AssertionError(errmsg)

        # Verify sub is present and non-empty
        if not claims["sub"]:
            errmsg = (
                "Iteration {}: Expected non-empty 'sub' claim in "
                "id_token".format(iteration)
            )
            raise AssertionError(errmsg)

        # Verify exp is in the future relative to iat
        if claims["exp"] <= claims["iat"]:
            errmsg = (
                "Iteration {}: Expected exp ({}) > iat ({})".format(
                    iteration, claims["exp"], claims["iat"]
                )
            )
            raise AssertionError(errmsg)

        # Verify exp matches the configured id_token_lifetime
        expected_exp_min = before_time + id_token_lifetime
        expected_exp_max = after_time + id_token_lifetime

        if claims["exp"] < expected_exp_min or claims["exp"] > expected_exp_max:
            errmsg = (
                "Iteration {}: Expected exp between {} and {}, "
                "got {}".format(
                    iteration, expected_exp_min, expected_exp_max,
                    claims["exp"]
                )
            )
            raise AssertionError(errmsg)

        # Verify iat is reasonable (within the test window)
        if claims["iat"] < before_time or claims["iat"] > after_time:
            errmsg = (
                "Iteration {}: Expected iat between {} and {}, "
                "got {}".format(
                    iteration, before_time, after_time, claims["iat"]
                )
            )
            raise AssertionError(errmsg)

    return
