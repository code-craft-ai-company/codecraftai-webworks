"""
    Property test for OAuth2 state validation.

    Property 15: OAuth2 State Validation
        For any OAuth2 authorization callback, the state parameter SHALL
        be validated against the original request, and mismatched states
        SHALL result in an error.

    **Validates: Requirements 6.4**
"""

import random
import string

from automojo.webworks.authentication.blueprints.oauth2 import (
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


def _create_fresh_blueprint(clients=None):
    """
        Create a fresh OAuth2Blueprint subclass to avoid class-level
        state leakage between iterations.

        :param clients: Dictionary of client_id -> client data.

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
    FreshBlueprint.require_pkce = False
    FreshBlueprint.enabled_endpoints = None
    FreshBlueprint.auth_system = None
    FreshBlueprint.base_path = "/oauth"
    FreshBlueprint._memory_code_store = {}
    FreshBlueprint._memory_client_store = {}
    FreshBlueprint._memory_token_store = {}

    if clients:
        FreshBlueprint._memory_client_store = dict(clients)

    return FreshBlueprint


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


def test_property_15_oauth2_state_validation():
    """
        Property 15: OAuth2 State Validation.

        For any OAuth2 authorization callback, the state parameter SHALL
        be validated against the original request, and mismatched states
        SHALL result in an error.

        For each iteration:
        1. Generate a random state value and client configuration.
        2. Issue an authorization request with the state.
        3. Verify the redirect includes the same state value.
        4. Call the callback with the correct state and verify success.
        5. Issue another authorization request with a new state.
        6. Call the callback with a different (wrong) state and verify
           an error is returned.
        7. Issue an authorization request without a state parameter.
        8. Verify the callback succeeds without state validation.

        **Validates: Requirements 6.4**
    """
    num_iterations = 100

    for iteration in range(num_iterations):
        # Generate random values
        client_id = _random_string(5, 20)
        redirect_uri = "https://{}.example.com/callback".format(
            _random_string(3, 10)
        )
        original_state = _random_string(8, 40)

        clients = {
            client_id: {
                "client_id": client_id,
                "client_secret": _random_string(10, 30),
                "redirect_uris": [redirect_uri],
                "grant_types": ["authorization_code"],
            }
        }

        # --- Part A: Matching state should succeed ---
        blueprint = _create_fresh_blueprint(clients=clients)

        auth_request = MockJsonRequest(query_params={
            "response_type": "code",
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "state": original_state,
        })
        auth_response = blueprint.authorize(auth_request)

        if auth_response["status"] != 302:
            errmsg = (
                "Iteration {} Part A: Expected 302 redirect from authorize, "
                "got {}".format(iteration, auth_response["status"])
            )
            raise AssertionError(errmsg)

        location = auth_response["headers"]["Location"]

        # Verify state is echoed in the redirect
        if "state={}".format(original_state) not in location:
            errmsg = (
                "Iteration {} Part A: Expected state={} in redirect URL, "
                "got {!r}".format(iteration, original_state, location)
            )
            raise AssertionError(errmsg)

        code = _extract_code_from_location(location)
        if code is None:
            errmsg = (
                "Iteration {} Part A: Expected code in redirect URL, "
                "got {!r}".format(iteration, location)
            )
            raise AssertionError(errmsg)

        # Callback with matching state should succeed
        callback_request = MockJsonRequest(query_params={
            "code": code,
            "state": original_state,
        })
        callback_response = blueprint.callback(callback_request)

        if callback_response["status"] != 200:
            errmsg = (
                "Iteration {} Part A: Expected 200 from callback with "
                "matching state, got {}. body={}".format(
                    iteration, callback_response["status"],
                    callback_response.get("body")
                )
            )
            raise AssertionError(errmsg)

        # Verify state is included in callback response
        response_state = callback_response["body"].get("state")
        if response_state != original_state:
            errmsg = (
                "Iteration {} Part A: Expected state={!r} in callback "
                "response, got {!r}".format(
                    iteration, original_state, response_state
                )
            )
            raise AssertionError(errmsg)

        # --- Part B: Mismatched state should fail ---
        blueprint_b = _create_fresh_blueprint(clients=clients)

        wrong_state = original_state + "_wrong"

        auth_request_b = MockJsonRequest(query_params={
            "response_type": "code",
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "state": original_state,
        })
        auth_response_b = blueprint_b.authorize(auth_request_b)

        code_b = _extract_code_from_location(
            auth_response_b["headers"]["Location"]
        )

        callback_request_b = MockJsonRequest(query_params={
            "code": code_b,
            "state": wrong_state,
        })
        callback_response_b = blueprint_b.callback(callback_request_b)

        if callback_response_b["status"] == 200:
            errmsg = (
                "Iteration {} Part B: Expected error for mismatched state, "
                "but got 200. original_state={!r}, wrong_state={!r}".format(
                    iteration, original_state, wrong_state
                )
            )
            raise AssertionError(errmsg)

        error_body = callback_response_b.get("body", {})
        if "error" not in error_body:
            errmsg = (
                "Iteration {} Part B: Expected error field in response "
                "body for mismatched state, got {!r}".format(
                    iteration, error_body
                )
            )
            raise AssertionError(errmsg)

        # --- Part C: No state should succeed without validation ---
        blueprint_c = _create_fresh_blueprint(clients=clients)

        auth_request_c = MockJsonRequest(query_params={
            "response_type": "code",
            "client_id": client_id,
            "redirect_uri": redirect_uri,
        })
        auth_response_c = blueprint_c.authorize(auth_request_c)

        code_c = _extract_code_from_location(
            auth_response_c["headers"]["Location"]
        )

        callback_request_c = MockJsonRequest(query_params={
            "code": code_c,
        })
        callback_response_c = blueprint_c.callback(callback_request_c)

        if callback_response_c["status"] != 200:
            errmsg = (
                "Iteration {} Part C: Expected 200 from callback without "
                "state, got {}".format(
                    iteration, callback_response_c["status"]
                )
            )
            raise AssertionError(errmsg)

    return
