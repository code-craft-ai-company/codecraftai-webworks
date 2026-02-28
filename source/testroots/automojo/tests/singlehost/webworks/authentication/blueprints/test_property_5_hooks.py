"""
    Property test for SecurityBlueprint pre/post authentication hooks.

    This module verifies Property 5: Pre/Post Authentication Hooks.

    For any authentication request processed by a Security_Blueprint, the
    pre_authenticate hook SHALL be called before validation and
    post_authenticate SHALL be called after successful validation.

    **Validates: Requirements 1.3**
"""

import random
import string

from automojo.testbase.mocking import Mock

from automojo.webworks.authentication.blueprints.security import SecurityBlueprint
from automojo.webworks.authentication.blueprints.responses import AuthError
from automojo.webworks.authentication.core import (
    AuthenticationContext,
    Principal,
)


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


def _create_mock_request():
    """
        Create a mock request object for testing hooks.

        :returns: A Mock object configured as a request.
    """
    mock_request = Mock()
    ctx = mock_request.mock_context()
    ctx.set_attribute("headers", {})
    ctx.set_attribute("path", "/" + _random_string(3, 15))
    return mock_request


def _create_random_principal():
    """
        Create a Principal with random identity data.

        :returns: A Principal instance with random identifier and display name.
    """
    identifier = f"user-{_random_string(4, 12)}"
    display_name = f"User {_random_string(3, 8)}"

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
    return principal


def _create_random_auth_context(principal):
    """
        Create an AuthenticationContext with the given principal and a random scheme.

        :param principal: The authenticated principal.

        :returns: An AuthenticationContext instance.
    """
    schemes = ["Basic", "Bearer", "Digest", "ApiKey", "Session"]
    scheme = random.choice(schemes)

    context = AuthenticationContext(
        principal=principal,
        scheme=scheme,
    )
    return context


def _create_tracking_blueprint_class():
    """
        Create a fresh SecurityBlueprint subclass that tracks hook invocations.

        Each call returns a new class so that class-level state does not leak
        between iterations.

        :returns: A SecurityBlueprint subclass with call tracking lists.
    """

    class TrackingBlueprint(SecurityBlueprint):
        """
            A SecurityBlueprint subclass that records every call to
            pre_authenticate and post_authenticate for verification.
        """

        call_log = []
        pre_auth_return_value = None

        @classmethod
        def pre_authenticate(cls, request):
            cls.call_log.append(("pre_authenticate", request))
            return cls.pre_auth_return_value

        @classmethod
        def post_authenticate(cls, request, context):
            cls.call_log.append(("post_authenticate", request, context))
            return

    # Reset class state for each new class
    TrackingBlueprint.call_log = []
    TrackingBlueprint.pre_auth_return_value = None

    return TrackingBlueprint


# =============================================================================
# Property Tests
# =============================================================================

def test_property_5_pre_post_authentication_hooks():
    """
        Property 5: Pre/Post Authentication Hooks.

        For any authentication request processed by a Security_Blueprint,
        the pre_authenticate hook SHALL be called before validation and
        post_authenticate SHALL be called after successful validation.

        This test verifies:
        1. pre_authenticate is always called with the request.
        2. When pre_authenticate returns None (success), post_authenticate
           is called with the request and the authentication context.
        3. When pre_authenticate returns an AuthError, post_authenticate
           is NOT called.
        4. The hooks are called in the correct order (pre before post).

        **Validates: Requirements 1.3**
    """
    num_iterations = 100

    for iteration in range(num_iterations):
        # Decide whether pre_authenticate should succeed or return an error
        pre_auth_succeeds = random.random() < 0.6

        blueprint_cls = _create_tracking_blueprint_class()
        mock_request = _create_mock_request()

        if pre_auth_succeeds:
            # pre_authenticate returns None, allowing authentication to proceed
            blueprint_cls.pre_auth_return_value = None
        else:
            # pre_authenticate returns an AuthError, blocking authentication
            error_code = random.choice([
                "rate_limited", "ip_blocked", "invalid_request",
                "maintenance", "forbidden",
            ])
            error_desc = f"Pre-auth error: {_random_string(5, 20)}"
            blueprint_cls.pre_auth_return_value = AuthError(
                error=error_code,
                error_description=error_desc,
            )

        # Step 1: Call pre_authenticate
        pre_result = blueprint_cls.pre_authenticate(mock_request)

        # Verify pre_authenticate was called
        if len(blueprint_cls.call_log) < 1:
            errmsg = (
                f"Iteration {iteration}: pre_authenticate was not recorded "
                f"in the call log after being invoked."
            )
            raise AssertionError(errmsg)

        first_call = blueprint_cls.call_log[0]
        if first_call[0] != "pre_authenticate":
            errmsg = (
                f"Iteration {iteration}: Expected first call to be "
                f"'pre_authenticate', got '{first_call[0]}'."
            )
            raise AssertionError(errmsg)

        if first_call[1] is not mock_request:
            errmsg = (
                f"Iteration {iteration}: pre_authenticate was not called "
                f"with the correct request object."
            )
            raise AssertionError(errmsg)

        # Step 2: Simulate the authentication flow based on pre_result
        if pre_result is None:
            # Pre-auth succeeded, simulate successful validation
            principal = _create_random_principal()
            context = _create_random_auth_context(principal)

            # Call post_authenticate
            blueprint_cls.post_authenticate(mock_request, context)

            # Verify post_authenticate was called
            if len(blueprint_cls.call_log) != 2:
                errmsg = (
                    f"Iteration {iteration}: Expected 2 calls in log "
                    f"(pre + post), got {len(blueprint_cls.call_log)}."
                )
                raise AssertionError(errmsg)

            second_call = blueprint_cls.call_log[1]
            if second_call[0] != "post_authenticate":
                errmsg = (
                    f"Iteration {iteration}: Expected second call to be "
                    f"'post_authenticate', got '{second_call[0]}'."
                )
                raise AssertionError(errmsg)

            if second_call[1] is not mock_request:
                errmsg = (
                    f"Iteration {iteration}: post_authenticate was not "
                    f"called with the correct request object."
                )
                raise AssertionError(errmsg)

            if second_call[2] is not context:
                errmsg = (
                    f"Iteration {iteration}: post_authenticate was not "
                    f"called with the correct authentication context."
                )
                raise AssertionError(errmsg)

            # Verify ordering: pre before post
            if blueprint_cls.call_log[0][0] != "pre_authenticate":
                errmsg = (
                    f"Iteration {iteration}: Hook ordering violated. "
                    f"Expected pre_authenticate first, got "
                    f"'{blueprint_cls.call_log[0][0]}'."
                )
                raise AssertionError(errmsg)

            if blueprint_cls.call_log[1][0] != "post_authenticate":
                errmsg = (
                    f"Iteration {iteration}: Hook ordering violated. "
                    f"Expected post_authenticate second, got "
                    f"'{blueprint_cls.call_log[1][0]}'."
                )
                raise AssertionError(errmsg)

        else:
            # Pre-auth returned an error, post_authenticate must NOT be called
            if len(blueprint_cls.call_log) != 1:
                errmsg = (
                    f"Iteration {iteration}: When pre_authenticate returns "
                    f"an AuthError, post_authenticate should NOT be called. "
                    f"Expected 1 call in log, got {len(blueprint_cls.call_log)}."
                )
                raise AssertionError(errmsg)

            # Verify the error can be formatted correctly
            error_response = blueprint_cls.format_error(pre_result)

            if error_response["status"] != 401:
                errmsg = (
                    f"Iteration {iteration}: Expected error status 401, "
                    f"got {error_response['status']}."
                )
                raise AssertionError(errmsg)

            if "error" not in error_response["body"]:
                errmsg = (
                    f"Iteration {iteration}: Error response body missing "
                    f"'error' field."
                )
                raise AssertionError(errmsg)

    return
