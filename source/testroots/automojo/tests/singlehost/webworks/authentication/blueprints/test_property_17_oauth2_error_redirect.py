"""
    Property test for OAuth2 error redirect.

    Property 17: OAuth2 Error Redirect
        When authorization fails, the response SHALL redirect with
        appropriate error parameters.

    **Validates: Requirements 6.8**
"""

import random
import string

from urllib.parse import urlparse, parse_qs

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


def _parse_redirect_params(location):
    """
        Parse query parameters from a redirect Location header.

        :param location: The Location header value.

        :returns: A dictionary of query parameter name -> value.
    """
    parsed = urlparse(location)
    params = parse_qs(parsed.query)
    # parse_qs returns lists; flatten single values
    result = {}
    for key, values in params.items():
        result[key] = values[0] if len(values) == 1 else values
    return result


# =============================================================================
# Property Tests
# =============================================================================


def test_property_17_oauth2_error_redirect():
    """
        Property 17: OAuth2 Error Redirect.

        When authorization fails, the response SHALL redirect to the
        redirect_uri with error and error_description query parameters.

        For each iteration, tests multiple failure scenarios:
        A. Unknown client — should redirect with error=invalid_client.
        B. Unsupported response_type — should redirect with
           error=unsupported_response_type.
        C. PKCE required but missing — should redirect with error.
        D. State parameter should be preserved in error redirects.

        **Validates: Requirements 6.8**
    """
    num_iterations = 100

    for iteration in range(num_iterations):
        # Generate random values
        redirect_uri = "https://{}.example.com/callback".format(
            _random_string(3, 10)
        )
        state = _random_string(8, 30)
        valid_client_id = _random_string(5, 15)

        clients = {
            valid_client_id: {
                "client_id": valid_client_id,
                "client_secret": _random_string(10, 20),
                "redirect_uris": [redirect_uri],
                "grant_types": ["authorization_code"],
            }
        }

        # --- Part A: Unknown client should produce error redirect ---
        blueprint_a = _create_fresh_blueprint(clients=clients)

        unknown_client = _random_string(5, 15) + "_unknown"

        auth_request_a = MockJsonRequest(query_params={
            "response_type": "code",
            "client_id": unknown_client,
            "redirect_uri": redirect_uri,
            "state": state,
        })
        auth_response_a = blueprint_a.authorize(auth_request_a)

        if auth_response_a["status"] != 302:
            errmsg = (
                "Iteration {} Part A: Expected 302 redirect for unknown "
                "client, got {}".format(iteration, auth_response_a["status"])
            )
            raise AssertionError(errmsg)

        location_a = auth_response_a["headers"]["Location"]
        params_a = _parse_redirect_params(location_a)

        if "error" not in params_a:
            errmsg = (
                "Iteration {} Part A: Expected 'error' parameter in "
                "redirect URL for unknown client, got params={!r}".format(
                    iteration, params_a
                )
            )
            raise AssertionError(errmsg)

        if "error_description" not in params_a:
            errmsg = (
                "Iteration {} Part A: Expected 'error_description' "
                "parameter in redirect URL, got params={!r}".format(
                    iteration, params_a
                )
            )
            raise AssertionError(errmsg)

        # State should be preserved in error redirect
        if params_a.get("state") != state:
            errmsg = (
                "Iteration {} Part A: Expected state={!r} in error "
                "redirect, got {!r}".format(
                    iteration, state, params_a.get("state")
                )
            )
            raise AssertionError(errmsg)

        # --- Part B: Unsupported response_type should produce error redirect ---
        blueprint_b = _create_fresh_blueprint(clients=clients)

        bad_response_type = random.choice(["token", "id_token", "none"])

        auth_request_b = MockJsonRequest(query_params={
            "response_type": bad_response_type,
            "client_id": valid_client_id,
            "redirect_uri": redirect_uri,
            "state": state,
        })
        auth_response_b = blueprint_b.authorize(auth_request_b)

        if auth_response_b["status"] != 302:
            errmsg = (
                "Iteration {} Part B: Expected 302 redirect for "
                "unsupported response_type, got {}".format(
                    iteration, auth_response_b["status"]
                )
            )
            raise AssertionError(errmsg)

        location_b = auth_response_b["headers"]["Location"]
        params_b = _parse_redirect_params(location_b)

        if "error" not in params_b:
            errmsg = (
                "Iteration {} Part B: Expected 'error' parameter in "
                "redirect URL for unsupported response_type".format(iteration)
            )
            raise AssertionError(errmsg)

        if "error_description" not in params_b:
            errmsg = (
                "Iteration {} Part B: Expected 'error_description' "
                "parameter in redirect URL".format(iteration)
            )
            raise AssertionError(errmsg)

        # State should be preserved
        if params_b.get("state") != state:
            errmsg = (
                "Iteration {} Part B: Expected state={!r} in error "
                "redirect, got {!r}".format(
                    iteration, state, params_b.get("state")
                )
            )
            raise AssertionError(errmsg)

        # --- Part C: PKCE required but missing should produce error redirect ---
        blueprint_c = _create_fresh_blueprint(
            clients=clients, require_pkce=True
        )

        auth_request_c = MockJsonRequest(query_params={
            "response_type": "code",
            "client_id": valid_client_id,
            "redirect_uri": redirect_uri,
            "state": state,
        })
        auth_response_c = blueprint_c.authorize(auth_request_c)

        if auth_response_c["status"] != 302:
            errmsg = (
                "Iteration {} Part C: Expected 302 redirect when PKCE "
                "required but missing, got {}".format(
                    iteration, auth_response_c["status"]
                )
            )
            raise AssertionError(errmsg)

        location_c = auth_response_c["headers"]["Location"]
        params_c = _parse_redirect_params(location_c)

        if "error" not in params_c:
            errmsg = (
                "Iteration {} Part C: Expected 'error' parameter in "
                "redirect URL when PKCE required".format(iteration)
            )
            raise AssertionError(errmsg)

        if "error_description" not in params_c:
            errmsg = (
                "Iteration {} Part C: Expected 'error_description' "
                "parameter in redirect URL".format(iteration)
            )
            raise AssertionError(errmsg)

        # State should be preserved
        if params_c.get("state") != state:
            errmsg = (
                "Iteration {} Part C: Expected state={!r} in error "
                "redirect, got {!r}".format(
                    iteration, state, params_c.get("state")
                )
            )
            raise AssertionError(errmsg)

    return
