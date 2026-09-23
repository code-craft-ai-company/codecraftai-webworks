"""
    Property test for refresh token flow.

    Property 11: Refresh Token Flow
        For any valid refresh token submitted to the refresh endpoint,
        a new access token SHALL be issued with fresh expiration.

    **Validates: Requirements 3.7**
"""

import random
import string
import time

from ccai.webworks.authentication.blueprints.bearer import (
    BearerAuthBlueprint,
)
from ccai.webworks.authentication.bearer import (
    decode_jwt,
    encode_jwt,
)


# =============================================================================
# Test Helpers
# =============================================================================

JWT_SECRET = "property-test-secret-for-refresh"
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
        A mock identity provider that accepts a known credential pair.
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


def _random_string(min_length=3, max_length=12):
    """
        Generate a random alphanumeric string.
    """
    length = random.randint(min_length, max_length)
    rtnval = "".join(random.choices(string.ascii_lowercase + string.digits, k=length))
    return rtnval


def _create_fresh_blueprint():
    """
        Create a fresh BearerAuthBlueprint subclass to avoid class-level
        state leakage between iterations.
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
# Property Tests
# =============================================================================

def test_property_11_refresh_token_flow():
    """
        Property 11: Refresh Token Flow.

        For any valid refresh token submitted to the refresh endpoint,
        a new access token SHALL be issued with fresh expiration.

        For each iteration:
        1. Generate a random subject identifier.
        2. Generate a random access_token_expires value.
        3. Create a valid refresh token JWT with the subject.
        4. Submit the refresh token to the refresh endpoint.
        5. Verify a new access token is issued (status 200).
        6. Decode the new access token and verify:
           a. The sub claim matches the original subject.
           b. The exp claim equals iat + access_token_expires.
           c. The token_type claim is "access".

        **Validates: Requirements 3.7**
    """
    num_iterations = 100

    for iteration in range(num_iterations):
        subject = "user-{}".format(_random_string(4, 10))
        access_expires = random.randint(300, 7200)

        blueprint = _create_fresh_blueprint()
        blueprint.access_token_expires = access_expires

        # Create a valid refresh token
        now = time.time()
        refresh_payload = {
            "sub": subject,
            "iat": int(now),
            "exp": int(now) + 86400,
            "token_type": "refresh",
        }
        refresh_token = encode_jwt(
            refresh_payload, JWT_SECRET, algorithm=JWT_ALGORITHM
        )

        request = MockJsonRequest({
            "refresh_token": refresh_token,
        })

        response = blueprint.refresh(request)

        # Verify status is 200
        if response["status"] != 200:
            errmsg = (
                "Iteration {}: Expected status 200, got {}. "
                "subject={}".format(
                    iteration, response["status"], subject
                )
            )
            raise AssertionError(errmsg)

        body = response["body"]

        # Verify access_token is present
        if "access_token" not in body:
            errmsg = (
                "Iteration {}: Expected access_token in response body. "
                "subject={}".format(iteration, subject)
            )
            raise AssertionError(errmsg)

        # Decode the new access token
        access_claims = decode_jwt(
            body["access_token"],
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM],
        )

        # Verify sub claim matches original subject
        if access_claims.get("sub") != subject:
            errmsg = (
                "Iteration {}: Expected sub={!r}, got {!r}".format(
                    iteration, subject, access_claims.get("sub")
                )
            )
            raise AssertionError(errmsg)

        # Verify token_type is "access"
        if access_claims.get("token_type") != "access":
            errmsg = (
                "Iteration {}: Expected token_type='access', got {!r}".format(
                    iteration, access_claims.get("token_type")
                )
            )
            raise AssertionError(errmsg)

        # Verify exp = iat + access_token_expires
        access_iat = access_claims.get("iat")
        access_exp = access_claims.get("exp")

        if access_exp != access_iat + access_expires:
            errmsg = (
                "Iteration {}: Access token exp mismatch. "
                "Expected iat({}) + expires({}) = {}, got {}".format(
                    iteration, access_iat, access_expires,
                    access_iat + access_expires, access_exp
                )
            )
            raise AssertionError(errmsg)

        # Verify expires_in in response body
        if body.get("expires_in") != access_expires:
            errmsg = (
                "Iteration {}: Expected expires_in={}, got {}".format(
                    iteration, access_expires, body.get("expires_in")
                )
            )
            raise AssertionError(errmsg)

    return
