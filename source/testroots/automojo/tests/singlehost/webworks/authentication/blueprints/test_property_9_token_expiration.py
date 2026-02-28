"""
    Property test for token expiration configuration.

    Property 9: Token Expiration Configuration
        For any Bearer_Auth_Blueprint with configured expiration times,
        issued tokens SHALL have exp claims matching the configuration.

    **Validates: Requirements 3.5**
"""

import random
import time

from automojo.webworks.authentication.blueprints.bearer import (
    BearerAuthBlueprint,
)
from automojo.webworks.authentication.bearer import (
    decode_jwt,
    encode_jwt,
)
from automojo.webworks.authentication.core import Principal


# =============================================================================
# Test Helpers
# =============================================================================

JWT_SECRET = "property-test-secret-for-expiration"
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

def test_property_9_token_expiration_configuration():
    """
        Property 9: Token Expiration Configuration.

        For any Bearer_Auth_Blueprint with configured expiration times,
        issued tokens SHALL have exp claims matching the configuration.

        For each iteration:
        1. Generate a random access_token_expires value (60 to 86400 seconds).
        2. Generate a random refresh_token_expires value (3600 to 604800 seconds).
        3. Create a fresh BearerAuthBlueprint with the configured expiration.
        4. Issue tokens via the password grant.
        5. Decode the access token and verify the exp claim matches
           iat + access_token_expires.
        6. Decode the refresh token and verify the exp claim matches
           iat + refresh_token_expires.
        7. Verify the response body expires_in matches access_token_expires.

        **Validates: Requirements 3.5**
    """
    num_iterations = 100

    username = "propuser"
    password = "proppass"
    principal = Principal(
        identifier="prop-user-9",
        display_name="Property User 9",
    )
    provider = MockIdentityProvider(username, password, principal)

    for iteration in range(num_iterations):
        access_expires = random.randint(60, 86400)
        refresh_expires = random.randint(3600, 604800)

        blueprint = _create_fresh_blueprint()
        blueprint.identity_provider = provider
        blueprint.access_token_expires = access_expires
        blueprint.refresh_token_expires = refresh_expires

        request = MockJsonRequest({
            "grant_type": "password",
            "username": username,
            "password": password,
        })

        response = blueprint.token(request)

        if response["status"] != 200:
            errmsg = (
                "Iteration {}: Expected status 200, got {}. "
                "access_expires={}, refresh_expires={}".format(
                    iteration, response["status"],
                    access_expires, refresh_expires
                )
            )
            raise AssertionError(errmsg)

        body = response["body"]

        # Verify expires_in in response body matches access_token_expires
        if body.get("expires_in") != access_expires:
            errmsg = (
                "Iteration {}: Expected expires_in={}, got {}".format(
                    iteration, access_expires, body.get("expires_in")
                )
            )
            raise AssertionError(errmsg)

        # Decode access token and verify exp claim
        access_claims = decode_jwt(
            body["access_token"],
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM],
        )

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

        # Decode refresh token and verify exp claim
        refresh_claims = decode_jwt(
            body["refresh_token"],
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM],
        )

        refresh_iat = refresh_claims.get("iat")
        refresh_exp = refresh_claims.get("exp")

        if refresh_exp != refresh_iat + refresh_expires:
            errmsg = (
                "Iteration {}: Refresh token exp mismatch. "
                "Expected iat({}) + expires({}) = {}, got {}".format(
                    iteration, refresh_iat, refresh_expires,
                    refresh_iat + refresh_expires, refresh_exp
                )
            )
            raise AssertionError(errmsg)

    return
