"""
    Property tests for BasicAuthBlueprint login endpoint.

    This module verifies:

    Property 2: Valid Credentials Produce Success Response
        For any authentication blueprint and valid credentials, the login
        endpoint SHALL return a success response with authentication data.

    Property 3: Invalid Credentials Produce 401
        For any authentication blueprint and invalid credentials, the login
        endpoint SHALL return a 401 status response.

    **Validates: Requirements 2.2, 2.3**
"""

import random
import string

from ccai.webworks.authentication.blueprints.basic import (
    BasicAuthBlueprint,
)
from ccai.webworks.authentication.core import Principal


# =============================================================================
# Test Helpers
# =============================================================================

def _random_string(min_length=1, max_length=20):
    """
        Generate a random alphanumeric string with at least one character.
    """
    length = random.randint(min_length, max_length)
    rtnval = "".join(random.choices(string.ascii_lowercase + string.digits, k=length))
    return rtnval


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

        When ``validate_credentials`` is called with the known username
        and password, it returns the corresponding :class:`Principal`.
        For any other credentials it returns None.
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


def _create_fresh_blueprint():
    """
        Create a fresh BasicAuthBlueprint subclass to avoid class-level
        state leakage between iterations.

        :returns: A new BasicAuthBlueprint subclass with clean state.
    """

    class FreshBlueprint(BasicAuthBlueprint):
        pass

    FreshBlueprint.identity_provider = None
    FreshBlueprint.enabled_endpoints = None
    FreshBlueprint.base_path = "/auth/basic"

    return FreshBlueprint


# =============================================================================
# Property Tests
# =============================================================================

def test_property_2_valid_credentials_produce_success():
    """
        Property 2: Valid Credentials Produce Success Response.

        For any authentication blueprint and valid credentials, the login
        endpoint SHALL return a success response with authentication data.

        For each iteration:
        1. Generate random username, password, and display_name.
        2. Create a mock IdentityProvider that knows this user.
        3. Create a fresh BasicAuthBlueprint subclass with the provider.
        4. Create a mock request with the valid credentials.
        5. Call blueprint.login(request).
        6. Verify response status is 200.
        7. Verify response body contains authenticated == True.
        8. Verify response body contains the correct principal_id.

        **Validates: Requirements 2.2**
    """
    num_iterations = 100

    for iteration in range(num_iterations):
        username = _random_string(3, 15)
        password = _random_string(6, 25)
        display_name = f"User {_random_string(3, 10)}"
        identifier = f"user-{_random_string(4, 12)}"

        num_roles = random.randint(0, 3)
        roles = set(_random_string(3, 10) for _ in range(num_roles))

        num_perms = random.randint(0, 3)
        permissions = set(_random_string(3, 10) for _ in range(num_perms))

        principal = Principal(
            identifier=identifier,
            display_name=display_name,
            roles=roles,
            permissions=permissions,
        )

        provider = MockIdentityProvider(username, password, principal)

        blueprint_cls = _create_fresh_blueprint()
        blueprint_cls.identity_provider = provider

        request = MockJsonRequest({"username": username, "password": password})

        response = blueprint_cls.login(request)

        # Verify status is 200
        if response["status"] != 200:
            errmsg = (
                f"Iteration {iteration}: Expected status 200 for valid "
                f"credentials, got {response['status']}. "
                f"username={username!r}"
            )
            raise AssertionError(errmsg)

        body = response["body"]

        # Verify authenticated is True
        if body.get("authenticated") is not True:
            errmsg = (
                f"Iteration {iteration}: Expected body['authenticated'] "
                f"to be True, got {body.get('authenticated')!r}. "
                f"username={username!r}"
            )
            raise AssertionError(errmsg)

        # Verify principal_id matches
        if body.get("principal_id") != identifier:
            errmsg = (
                f"Iteration {iteration}: Expected body['principal_id'] "
                f"to be {identifier!r}, got {body.get('principal_id')!r}. "
                f"username={username!r}"
            )
            raise AssertionError(errmsg)

    return


def test_property_3_invalid_credentials_produce_401():
    """
        Property 3: Invalid Credentials Produce 401.

        For any authentication blueprint and invalid credentials, the login
        endpoint SHALL return a 401 status response.

        For each iteration:
        1. Generate random username and password.
        2. Create a mock IdentityProvider that does NOT know this user.
        3. Create a fresh BasicAuthBlueprint subclass with the provider.
        4. Create a mock request with the invalid credentials.
        5. Call blueprint.login(request).
        6. Verify response status is 401.
        7. Verify response body contains an error field.

        **Validates: Requirements 2.3**
    """
    num_iterations = 100

    for iteration in range(num_iterations):
        username = _random_string(3, 15)
        password = _random_string(6, 25)

        provider = RejectAllIdentityProvider()

        blueprint_cls = _create_fresh_blueprint()
        blueprint_cls.identity_provider = provider

        request = MockJsonRequest({"username": username, "password": password})

        response = blueprint_cls.login(request)

        # Verify status is 401
        if response["status"] != 401:
            errmsg = (
                f"Iteration {iteration}: Expected status 401 for invalid "
                f"credentials, got {response['status']}. "
                f"username={username!r}"
            )
            raise AssertionError(errmsg)

        body = response["body"]

        # Verify error field is present
        if "error" not in body:
            errmsg = (
                f"Iteration {iteration}: Expected body to contain 'error' "
                f"field for invalid credentials, got keys: {list(body.keys())}. "
                f"username={username!r}"
            )
            raise AssertionError(errmsg)

    return
