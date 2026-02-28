"""
    Property test for SecurityBlueprint method override behavior.

    This module verifies Property 19: Method Override Behavior.

    For any SecurityBlueprint subclass that overrides a default handler
    method, requests to that endpoint SHALL invoke the overridden
    implementation.

    **Validates: Requirements 8.1, 8.5**
"""

import random
import string

from automojo.testbase.mocking import Mock

from automojo.webworks.authentication.blueprints.security import SecurityBlueprint
from automojo.webworks.authentication.blueprints.responses import (
    AuthError,
    AuthResponse,
)
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


def _create_mock_request(body=None):
    """
        Create a mock request object with optional JSON body.

        :param body: Optional dictionary to return from request.json().

        :returns: A Mock object configured as a request.
    """
    mock_request = Mock()
    ctx = mock_request.mock_context()
    ctx.set_attribute("headers", {})
    ctx.set_attribute("path", "/" + _random_string(3, 15))

    if body is not None:
        ctx.mock_method("json", return_value=body)

    return mock_request


def _create_random_principal():
    """
        Create a Principal with random identity data.

        :returns: A Principal instance with random identifier and display name.
    """
    identifier = f"user-{_random_string(4, 12)}"
    display_name = f"User {_random_string(3, 8)}"

    principal = Principal(
        identifier=identifier,
        display_name=display_name,
        roles=set(),
        permissions=set(),
    )
    return principal


# =============================================================================
# Property Tests
# =============================================================================

def test_property_19_method_override_behavior():
    """
        Property 19: Method Override Behavior.

        For any SecurityBlueprint subclass that overrides a default handler
        method, requests to that endpoint SHALL invoke the overridden
        implementation.

        This test verifies:
        1. Overriding format_error in a subclass causes the subclass
           implementation to be used instead of the base class version.
        2. Overriding format_success in a subclass causes the subclass
           implementation to be used instead of the base class version.
        3. Overriding pre_authenticate in a subclass causes the subclass
           implementation to be used.
        4. Overriding post_authenticate in a subclass causes the subclass
           implementation to be used.
        5. Multiple levels of override (grandchild) use the most derived
           implementation.

        **Validates: Requirements 8.1, 8.5**
    """
    num_iterations = 100

    for iteration in range(num_iterations):
        # Generate a random custom status code and marker for this iteration
        custom_status = random.randint(400, 599)
        custom_marker = _random_string(5, 15)
        custom_content_type = random.choice([
            "application/json",
            "application/xml",
            "text/plain",
        ])

        # --- Test format_error override ---

        class ErrorOverrideBlueprint(SecurityBlueprint):
            """
                Subclass that overrides format_error with a custom format.
            """

            @classmethod
            def format_error(cls, error, status_code=401):
                response = {
                    "status": custom_status,
                    "body": {
                        "custom_error": error.error,
                        "marker": custom_marker,
                    },
                    "content_type": custom_content_type,
                }
                return response

        error = AuthError(
            error="test_error",
            error_description="Test error description",
        )

        result = ErrorOverrideBlueprint.format_error(error)

        if result["status"] != custom_status:
            errmsg = (
                f"Iteration {iteration}: format_error override not invoked. "
                f"Expected status {custom_status}, got {result['status']}."
            )
            raise AssertionError(errmsg)

        if result["body"].get("marker") != custom_marker:
            errmsg = (
                f"Iteration {iteration}: format_error override not invoked. "
                f"Expected marker '{custom_marker}', got "
                f"'{result['body'].get('marker')}'."
            )
            raise AssertionError(errmsg)

        if result["content_type"] != custom_content_type:
            errmsg = (
                f"Iteration {iteration}: format_error override not invoked. "
                f"Expected content_type '{custom_content_type}', got "
                f"'{result['content_type']}'."
            )
            raise AssertionError(errmsg)

        # Verify base class is NOT affected
        base_result = SecurityBlueprint.format_error(error)

        if base_result["status"] != 401:
            errmsg = (
                f"Iteration {iteration}: Base class format_error was "
                f"modified by subclass override. Expected status 401, "
                f"got {base_result['status']}."
            )
            raise AssertionError(errmsg)

        # --- Test format_success override ---

        success_marker = _random_string(5, 15)

        class SuccessOverrideBlueprint(SecurityBlueprint):
            """
                Subclass that overrides format_success with a custom format.
            """

            @classmethod
            def format_success(cls, response, status_code=200):
                result = {
                    "status": status_code,
                    "body": {
                        "custom_success": True,
                        "marker": success_marker,
                    },
                    "content_type": "application/json",
                }
                return result

        auth_response = AuthResponse(access_token="test-token")
        success_result = SuccessOverrideBlueprint.format_success(auth_response)

        if success_result["body"].get("marker") != success_marker:
            errmsg = (
                f"Iteration {iteration}: format_success override not "
                f"invoked. Expected marker '{success_marker}', got "
                f"'{success_result['body'].get('marker')}'."
            )
            raise AssertionError(errmsg)

        # --- Test pre_authenticate override ---

        pre_auth_marker = _random_string(5, 15)
        pre_auth_calls = []

        class PreAuthOverrideBlueprint(SecurityBlueprint):
            """
                Subclass that overrides pre_authenticate.
            """

            @classmethod
            def pre_authenticate(cls, request):
                pre_auth_calls.append(pre_auth_marker)
                return None

        mock_request = _create_mock_request()
        PreAuthOverrideBlueprint.pre_authenticate(mock_request)

        if len(pre_auth_calls) != 1:
            errmsg = (
                f"Iteration {iteration}: pre_authenticate override not "
                f"invoked. Expected 1 call, got {len(pre_auth_calls)}."
            )
            raise AssertionError(errmsg)

        if pre_auth_calls[0] != pre_auth_marker:
            errmsg = (
                f"Iteration {iteration}: pre_authenticate override "
                f"recorded wrong marker."
            )
            raise AssertionError(errmsg)

        # --- Test post_authenticate override ---

        post_auth_calls = []
        post_auth_marker = _random_string(5, 15)

        class PostAuthOverrideBlueprint(SecurityBlueprint):
            """
                Subclass that overrides post_authenticate.
            """

            @classmethod
            def post_authenticate(cls, request, context):
                post_auth_calls.append((post_auth_marker, context))
                return

        principal = _create_random_principal()
        context = AuthenticationContext(principal=principal, scheme="Bearer")
        PostAuthOverrideBlueprint.post_authenticate(mock_request, context)

        if len(post_auth_calls) != 1:
            errmsg = (
                f"Iteration {iteration}: post_authenticate override not "
                f"invoked. Expected 1 call, got {len(post_auth_calls)}."
            )
            raise AssertionError(errmsg)

        if post_auth_calls[0][0] != post_auth_marker:
            errmsg = (
                f"Iteration {iteration}: post_authenticate override "
                f"recorded wrong marker."
            )
            raise AssertionError(errmsg)

        if post_auth_calls[0][1] is not context:
            errmsg = (
                f"Iteration {iteration}: post_authenticate override "
                f"did not receive the correct context."
            )
            raise AssertionError(errmsg)

        # --- Test multi-level override (grandchild) ---

        grandchild_marker = _random_string(5, 15)

        class ChildBlueprint(SecurityBlueprint):
            """
                First-level subclass with a format_error override.
            """

            @classmethod
            def format_error(cls, error, status_code=401):
                return {
                    "status": 450,
                    "body": {"level": "child"},
                    "content_type": "application/json",
                }

        class GrandchildBlueprint(ChildBlueprint):
            """
                Second-level subclass that further overrides format_error.
            """

            @classmethod
            def format_error(cls, error, status_code=401):
                return {
                    "status": 460,
                    "body": {"level": "grandchild", "marker": grandchild_marker},
                    "content_type": "application/json",
                }

        grandchild_result = GrandchildBlueprint.format_error(error)

        if grandchild_result["body"].get("level") != "grandchild":
            errmsg = (
                f"Iteration {iteration}: Multi-level override failed. "
                f"Expected level 'grandchild', got "
                f"'{grandchild_result['body'].get('level')}'."
            )
            raise AssertionError(errmsg)

        if grandchild_result["body"].get("marker") != grandchild_marker:
            errmsg = (
                f"Iteration {iteration}: Multi-level override failed. "
                f"Expected marker '{grandchild_marker}', got "
                f"'{grandchild_result['body'].get('marker')}'."
            )
            raise AssertionError(errmsg)

        # Verify the child class still uses its own override
        child_result = ChildBlueprint.format_error(error)

        if child_result["body"].get("level") != "child":
            errmsg = (
                f"Iteration {iteration}: Child override was affected by "
                f"grandchild. Expected level 'child', got "
                f"'{child_result['body'].get('level')}'."
            )
            raise AssertionError(errmsg)

    return
