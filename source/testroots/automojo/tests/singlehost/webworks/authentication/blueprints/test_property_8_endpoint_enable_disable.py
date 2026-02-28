"""
    Property test for SecurityBlueprint endpoint enable/disable.

    This module verifies Property 8: Endpoint Enable/Disable.

    For any SecurityBlueprint with enabled_endpoints configured, only
    endpoints in that set SHALL respond to requests; disabled endpoints
    SHALL return 404.

    **Validates: Requirements 2.6, 8.6**
"""

import random
import string

from automojo.webworks.authentication.blueprints.security import SecurityBlueprint
from automojo.webworks.authentication.blueprints.responses import AuthError


# =============================================================================
# Test Helpers
# =============================================================================

def _random_string(min_length=1, max_length=20):
    """
        Generate a random alphanumeric string.
    """
    length = random.randint(min_length, max_length)
    rtnval = "".join(random.choices(string.ascii_lowercase + string.digits, k=length))
    return rtnval


def _random_endpoint_names(count):
    """
        Generate a list of random endpoint names.

        :param count: Number of endpoint names to generate.

        :returns: A list of unique endpoint name strings.
    """
    names = set()
    while len(names) < count:
        names.add(_random_string(3, 12))
    return list(names)


# =============================================================================
# Property Tests
# =============================================================================

def test_property_8_endpoint_enable_disable():
    """
        Property 8: Endpoint Enable/Disable.

        For any SecurityBlueprint with enabled_endpoints configured, only
        endpoints in that set SHALL respond to requests; disabled endpoints
        SHALL return 404.

        This test verifies:
        1. When enabled_endpoints is None (default), all endpoints are
           enabled (is_endpoint_enabled returns True for any name).
        2. When enabled_endpoints contains "all", all endpoints are enabled.
        3. When enabled_endpoints contains specific names, only those
           endpoints are enabled.
        4. Endpoints not in the enabled set return False from
           is_endpoint_enabled.
        5. configure() with enabled_endpoints updates the set correctly.
        6. A blueprint handler that checks is_endpoint_enabled returns
           a 404 response for disabled endpoints.

        **Validates: Requirements 2.6, 8.6**
    """
    num_iterations = 100

    for iteration in range(num_iterations):
        # Generate random endpoint names
        total_endpoints = random.randint(2, 8)
        all_endpoint_names = _random_endpoint_names(total_endpoints)

        # Decide how many to enable (at least 1, fewer than total)
        num_enabled = random.randint(1, max(1, total_endpoints - 1))
        enabled_names = set(random.sample(all_endpoint_names, num_enabled))
        disabled_names = set(all_endpoint_names) - enabled_names

        # --- Test 1: Default (None) enables all ---

        class DefaultBlueprint(SecurityBlueprint):
            pass

        DefaultBlueprint.enabled_endpoints = None

        for name in all_endpoint_names:
            is_enabled = DefaultBlueprint.is_endpoint_enabled(name)
            if not is_enabled:
                errmsg = (
                    f"Iteration {iteration}: With enabled_endpoints=None, "
                    f"endpoint '{name}' should be enabled but "
                    f"is_endpoint_enabled returned False."
                )
                raise AssertionError(errmsg)

        # --- Test 2: "all" enables everything ---

        class AllEnabledBlueprint(SecurityBlueprint):
            pass

        AllEnabledBlueprint.enabled_endpoints = {"all"}

        for name in all_endpoint_names:
            is_enabled = AllEnabledBlueprint.is_endpoint_enabled(name)
            if not is_enabled:
                errmsg = (
                    f"Iteration {iteration}: With enabled_endpoints={{'all'}}, "
                    f"endpoint '{name}' should be enabled but "
                    f"is_endpoint_enabled returned False."
                )
                raise AssertionError(errmsg)

        # Also test with a random name not in the list
        random_name = _random_string(15, 20) + "_extra"
        is_enabled = AllEnabledBlueprint.is_endpoint_enabled(random_name)
        if not is_enabled:
            errmsg = (
                f"Iteration {iteration}: With enabled_endpoints={{'all'}}, "
                f"arbitrary endpoint '{random_name}' should be enabled."
            )
            raise AssertionError(errmsg)

        # --- Test 3: Specific set enables only those endpoints ---

        class SelectiveBlueprint(SecurityBlueprint):
            pass

        SelectiveBlueprint.enabled_endpoints = enabled_names

        for name in enabled_names:
            is_enabled = SelectiveBlueprint.is_endpoint_enabled(name)
            if not is_enabled:
                errmsg = (
                    f"Iteration {iteration}: Endpoint '{name}' is in "
                    f"enabled_endpoints but is_endpoint_enabled returned "
                    f"False. enabled_endpoints={enabled_names}."
                )
                raise AssertionError(errmsg)

        # --- Test 4: Disabled endpoints return False ---

        for name in disabled_names:
            is_enabled = SelectiveBlueprint.is_endpoint_enabled(name)
            if is_enabled:
                errmsg = (
                    f"Iteration {iteration}: Endpoint '{name}' is NOT in "
                    f"enabled_endpoints but is_endpoint_enabled returned "
                    f"True. enabled_endpoints={enabled_names}."
                )
                raise AssertionError(errmsg)

        # --- Test 5: configure() updates enabled_endpoints ---

        class ConfigurableBlueprint(SecurityBlueprint):
            pass

        ConfigurableBlueprint.enabled_endpoints = {"all"}
        ConfigurableBlueprint.auth_system = None

        from automojo.testbase.mocking import Mock
        mock_auth = Mock()
        mock_auth.configure(recursive=True)

        ConfigurableBlueprint.configure(
            auth_system=mock_auth,
            enabled_endpoints=enabled_names,
        )

        for name in enabled_names:
            is_enabled = ConfigurableBlueprint.is_endpoint_enabled(name)
            if not is_enabled:
                errmsg = (
                    f"Iteration {iteration}: After configure(), endpoint "
                    f"'{name}' should be enabled but is_endpoint_enabled "
                    f"returned False."
                )
                raise AssertionError(errmsg)

        for name in disabled_names:
            is_enabled = ConfigurableBlueprint.is_endpoint_enabled(name)
            if is_enabled:
                errmsg = (
                    f"Iteration {iteration}: After configure(), endpoint "
                    f"'{name}' should be disabled but is_endpoint_enabled "
                    f"returned True."
                )
                raise AssertionError(errmsg)

        # --- Test 6: Disabled endpoint produces 404 response ---

        if len(disabled_names) > 0:
            disabled_name = list(disabled_names)[0]

            # Simulate what a handler does when checking is_endpoint_enabled
            if not SelectiveBlueprint.is_endpoint_enabled(disabled_name):
                error = AuthError(
                    error="endpoint_disabled",
                    error_description=f"{disabled_name} endpoint is disabled",
                )
                response = SelectiveBlueprint.format_error(
                    error, status_code=404
                )

                if response["status"] != 404:
                    errmsg = (
                        f"Iteration {iteration}: Disabled endpoint "
                        f"'{disabled_name}' should produce status 404, "
                        f"got {response['status']}."
                    )
                    raise AssertionError(errmsg)

                if response["body"].get("error") != "endpoint_disabled":
                    errmsg = (
                        f"Iteration {iteration}: Disabled endpoint error "
                        f"response should have error='endpoint_disabled', "
                        f"got '{response['body'].get('error')}'."
                    )
                    raise AssertionError(errmsg)

    return
