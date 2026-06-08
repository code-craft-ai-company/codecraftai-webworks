"""
    Property test for PKCE verification.

    Property 16: PKCE Verification
        For any authorization code issued with a code_challenge, the token
        endpoint SHALL verify the code_verifier.

    **Validates: Requirements 6.6**
"""

import hashlib
import random
import secrets
import string

from base64 import urlsafe_b64encode

from ccai.webworks.authentication.blueprints.oauth2 import (
    OAuth2Blueprint,
)


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


def _create_fresh_blueprint(clients=None, require_pkce=False):
    """
        Create a fresh OAuth2Blueprint subclass to avoid class-level
        state leakage between iterations.

        :param clients: Dictionary of client_id -> client data.
        :param require_pkce: Whether PKCE is required.

        :returns: The fresh blueprint class.
    """

    class FreshBlueprint(OAuth2Blueprint):
        pass

    FreshBlueprint.client_store = None
    FreshBlueprint.authorization_code_store = None
    FreshBlueprint.token_store = None
    FreshBlueprint.jwt_secret = "test-secret-key"
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


def _make_pkce_pair_s256(code_verifier):
    """
        Compute the S256 code_challenge for a given code_verifier.

        :param code_verifier: The code verifier string.

        :returns: The base64url-encoded SHA-256 hash of the verifier.
    """
    digest = hashlib.sha256(code_verifier.encode("ascii")).digest()
    code_challenge = urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    return code_challenge


def _extract_code_from_location(location):
    """
        Extract the authorization code from a redirect Location header.

        :param location: The Location header value.

        :returns: The authorization code string, or None.
    """
    if "?" not in location:
        return None

    query_part = location.split("?", 1)[1]
    for pair in query_part.split("&"):
        if pair.startswith("code="):
            code = pair.split("=", 1)[1]
            return code

    return None


# =============================================================================
# Property Tests
# =============================================================================


def test_property_16_pkce_verification():
    """
        Property 16: PKCE Verification.

        For any authorization code issued with a code_challenge, the token
        endpoint SHALL verify the code_verifier.

        For each iteration:
        1. Generate a random code_verifier.
        2. Randomly choose S256 or plain method.
        3. Compute the code_challenge.
        4. Issue an authorization request with the code_challenge.
        5. Exchange the code with the correct code_verifier — expect success.
        6. Issue another authorization request with the same challenge.
        7. Exchange the code with a wrong code_verifier — expect failure.
        8. Issue another authorization request with the same challenge.
        9. Exchange the code without a code_verifier — expect failure.

        **Validates: Requirements 6.6**
    """
    num_iterations = 100

    for iteration in range(num_iterations):
        # Generate random values
        client_id = _random_string(5, 15)
        redirect_uri = "https://{}.example.com/cb".format(
            _random_string(3, 8)
        )

        # Generate a random code_verifier (43-128 chars per RFC 7636)
        verifier_length = random.randint(43, 80)
        unreserved = string.ascii_letters + string.digits + "-._~"
        code_verifier = "".join(
            random.choice(unreserved) for _ in range(verifier_length)
        )

        # Randomly choose method
        method = random.choice(["S256", "plain"])

        if method == "S256":
            code_challenge = _make_pkce_pair_s256(code_verifier)
        else:
            code_challenge = code_verifier

        clients = {
            client_id: {
                "client_id": client_id,
                "client_secret": _random_string(10, 20),
                "redirect_uris": [redirect_uri],
                "grant_types": ["authorization_code"],
            }
        }

        # --- Part A: Correct verifier should succeed ---
        blueprint_a = _create_fresh_blueprint(clients=clients)

        auth_request_a = MockJsonRequest(query_params={
            "response_type": "code",
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "code_challenge": code_challenge,
            "code_challenge_method": method,
        })
        auth_response_a = blueprint_a.authorize(auth_request_a)

        if auth_response_a["status"] != 302:
            errmsg = (
                "Iteration {} Part A: Expected 302, got {}".format(
                    iteration, auth_response_a["status"]
                )
            )
            raise AssertionError(errmsg)

        code_a = _extract_code_from_location(
            auth_response_a["headers"]["Location"]
        )

        token_request_a = MockJsonRequest(data={
            "grant_type": "authorization_code",
            "code": code_a,
            "redirect_uri": redirect_uri,
            "client_id": client_id,
            "code_verifier": code_verifier,
        })
        token_response_a = blueprint_a.token(token_request_a)

        if token_response_a["status"] != 200:
            errmsg = (
                "Iteration {} Part A: Expected 200 with correct verifier, "
                "got {}. method={}, body={}".format(
                    iteration, token_response_a["status"], method,
                    token_response_a.get("body")
                )
            )
            raise AssertionError(errmsg)

        if "access_token" not in token_response_a["body"]:
            errmsg = (
                "Iteration {} Part A: Expected access_token in response "
                "body".format(iteration)
            )
            raise AssertionError(errmsg)

        # --- Part B: Wrong verifier should fail ---
        blueprint_b = _create_fresh_blueprint(clients=clients)

        auth_request_b = MockJsonRequest(query_params={
            "response_type": "code",
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "code_challenge": code_challenge,
            "code_challenge_method": method,
        })
        auth_response_b = blueprint_b.authorize(auth_request_b)

        code_b = _extract_code_from_location(
            auth_response_b["headers"]["Location"]
        )

        wrong_verifier = code_verifier + "X"

        token_request_b = MockJsonRequest(data={
            "grant_type": "authorization_code",
            "code": code_b,
            "redirect_uri": redirect_uri,
            "client_id": client_id,
            "code_verifier": wrong_verifier,
        })
        token_response_b = blueprint_b.token(token_request_b)

        if token_response_b["status"] == 200:
            errmsg = (
                "Iteration {} Part B: Expected error with wrong verifier, "
                "but got 200. method={}".format(iteration, method)
            )
            raise AssertionError(errmsg)

        error_body_b = token_response_b.get("body", {})
        if "error" not in error_body_b:
            errmsg = (
                "Iteration {} Part B: Expected error field in response "
                "for wrong verifier, got {!r}".format(
                    iteration, error_body_b
                )
            )
            raise AssertionError(errmsg)

        # --- Part C: Missing verifier should fail ---
        blueprint_c = _create_fresh_blueprint(clients=clients)

        auth_request_c = MockJsonRequest(query_params={
            "response_type": "code",
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "code_challenge": code_challenge,
            "code_challenge_method": method,
        })
        auth_response_c = blueprint_c.authorize(auth_request_c)

        code_c = _extract_code_from_location(
            auth_response_c["headers"]["Location"]
        )

        token_request_c = MockJsonRequest(data={
            "grant_type": "authorization_code",
            "code": code_c,
            "redirect_uri": redirect_uri,
            "client_id": client_id,
        })
        token_response_c = blueprint_c.token(token_request_c)

        if token_response_c["status"] == 200:
            errmsg = (
                "Iteration {} Part C: Expected error with missing verifier, "
                "but got 200. method={}".format(iteration, method)
            )
            raise AssertionError(errmsg)

        error_body_c = token_response_c.get("body", {})
        if "error" not in error_body_c:
            errmsg = (
                "Iteration {} Part C: Expected error field in response "
                "for missing verifier, got {!r}".format(
                    iteration, error_body_c
                )
            )
            raise AssertionError(errmsg)

    return
