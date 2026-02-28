"""
    Property test for JWT algorithm configuration.

    Property 10: JWT Algorithm Configuration
        For any Bearer_Auth_Blueprint with configured signing algorithm,
        issued JWTs SHALL be signed with that algorithm and verifiable
        with the configured secret/key.

    **Validates: Requirements 3.6**
"""

import random

from automojo.webworks.authentication.blueprints.bearer import (
    BearerAuthBlueprint,
)
from automojo.webworks.authentication.bearer import (
    decode_jwt,
    JWTError,
)
from automojo.webworks.authentication.core import Principal


# =============================================================================
# Test Helpers
# =============================================================================

JWT_SECRET = "property-test-secret-for-algorithm"

SUPPORTED_ALGORITHMS = ["HS256", "HS384", "HS512"]


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
    FreshBlueprint.jwt_algorithm = "HS256"
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

def test_property_10_jwt_algorithm_configuration():
    """
        Property 10: JWT Algorithm Configuration.

        For any Bearer_Auth_Blueprint with configured signing algorithm,
        issued JWTs SHALL be signed with that algorithm and verifiable
        with the configured secret/key.

        For each iteration:
        1. Randomly select an algorithm from the supported set.
        2. Create a fresh BearerAuthBlueprint with the selected algorithm.
        3. Issue a token via the password grant.
        4. Verify the token can be decoded with the selected algorithm.
        5. Verify the token CANNOT be decoded with a different algorithm.

        **Validates: Requirements 3.6**
    """
    num_iterations = 100

    username = "alguser"
    password = "algpass"
    principal = Principal(
        identifier="prop-user-10",
        display_name="Property User 10",
    )
    provider = MockIdentityProvider(username, password, principal)

    for iteration in range(num_iterations):
        chosen_algorithm = random.choice(SUPPORTED_ALGORITHMS)

        blueprint = _create_fresh_blueprint()
        blueprint.identity_provider = provider
        blueprint.jwt_algorithm = chosen_algorithm

        request = MockJsonRequest({
            "grant_type": "password",
            "username": username,
            "password": password,
        })

        response = blueprint.token(request)

        if response["status"] != 200:
            errmsg = (
                "Iteration {}: Expected status 200, got {}. "
                "algorithm={}".format(
                    iteration, response["status"], chosen_algorithm
                )
            )
            raise AssertionError(errmsg)

        body = response["body"]
        access_token = body["access_token"]

        # Verify the token can be decoded with the chosen algorithm
        try:
            claims = decode_jwt(
                access_token,
                JWT_SECRET,
                algorithms=[chosen_algorithm],
            )
        except JWTError as exc:
            errmsg = (
                "Iteration {}: Failed to decode token with algorithm {}. "
                "Error: {}".format(iteration, chosen_algorithm, exc)
            )
            raise AssertionError(errmsg)

        if claims.get("sub") != "prop-user-10":
            errmsg = (
                "Iteration {}: Expected sub='prop-user-10', got {!r}. "
                "algorithm={}".format(
                    iteration, claims.get("sub"), chosen_algorithm
                )
            )
            raise AssertionError(errmsg)

        # Verify the token CANNOT be decoded with a different algorithm
        other_algorithms = [
            alg for alg in SUPPORTED_ALGORITHMS if alg != chosen_algorithm
        ]
        if other_algorithms:
            wrong_algorithm = random.choice(other_algorithms)
            try:
                decode_jwt(
                    access_token,
                    JWT_SECRET,
                    algorithms=[wrong_algorithm],
                )
                errmsg = (
                    "Iteration {}: Token signed with {} should not decode "
                    "with {}".format(
                        iteration, chosen_algorithm, wrong_algorithm
                    )
                )
                raise AssertionError(errmsg)
            except JWTError:
                # Expected: token signed with one algorithm should not
                # validate with a different algorithm
                pass

    return
