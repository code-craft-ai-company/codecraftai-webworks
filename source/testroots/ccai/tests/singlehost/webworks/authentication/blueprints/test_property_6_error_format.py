"""
    Property test for error response format consistency.

    This module verifies Property 6: Error Response Format Consistency.

    For any authentication failure across all blueprint types, the error
    response SHALL contain "error" field and optionally "error_description"
    per RFC 6749 format.

    **Validates: Requirements 1.4, 1.6, 10.1**
"""

import random
import string

from ccai.webworks.authentication.blueprints.security import SecurityBlueprint
from ccai.webworks.authentication.blueprints.responses import AuthError


# =============================================================================
# Test Helpers
# =============================================================================

# RFC 6749 Section 5.2 standard error codes
_RFC6749_ERROR_CODES = [
    "invalid_request",
    "invalid_client",
    "invalid_grant",
    "unauthorized_client",
    "unsupported_grant_type",
    "invalid_scope",
    "access_denied",
    "server_error",
    "temporarily_unavailable",
]

_VALID_STATUS_CODES = [400, 401, 403, 404, 429, 500]


def _random_string(min_length=1, max_length=20):
    """
        Generate a random alphanumeric string.
    """
    length = random.randint(min_length, max_length)
    rtnval = "".join(random.choices(string.ascii_lowercase + string.digits, k=length))
    return rtnval


def _random_error_code():
    """
        Generate a random error code, choosing from RFC 6749 standard codes
        or a random custom string.
    """
    if random.random() < 0.7:
        code = random.choice(_RFC6749_ERROR_CODES)
    else:
        code = _random_string(3, 15)
    return code


def _random_description():
    """
        Generate a random error description or None.
    """
    if random.random() < 0.4:
        return None
    desc = " ".join(_random_string(3, 10) for _ in range(random.randint(2, 6)))
    return desc


def _random_uri():
    """
        Generate a random error URI or None.
    """
    if random.random() < 0.5:
        return None
    uri = f"https://example.com/errors/{_random_string(5, 15)}"
    return uri


# =============================================================================
# Property Tests
# =============================================================================

def test_property_6_error_response_format_consistency():
    """
        Property 6: Error Response Format Consistency.

        For any authentication failure across all blueprint types, the error
        response SHALL contain "error" field and optionally
        "error_description" per RFC 6749 format.

        This test verifies:
        1. The response dict always has "status", "body", "content_type" keys.
        2. The body always contains the "error" field.
        3. The body contains "error_description" only when provided.
        4. The body contains "error_uri" only when provided.
        5. The content_type is always "application/json".
        6. The status code matches what was passed.

        **Validates: Requirements 1.4, 1.6, 10.1**
    """
    num_iterations = 100

    for iteration in range(num_iterations):
        error_code = _random_error_code()
        error_description = _random_description()
        error_uri = _random_uri()
        status_code = random.choice(_VALID_STATUS_CODES)

        auth_error = AuthError(
            error=error_code,
            error_description=error_description,
            error_uri=error_uri,
        )

        response = SecurityBlueprint.format_error(auth_error, status_code=status_code)

        # Verify top-level keys exist
        for key in ("status", "body", "content_type"):
            if key not in response:
                errmsg = (
                    f"Iteration {iteration}: Response missing required "
                    f"key '{key}'. Got keys: {list(response.keys())}"
                )
                raise AssertionError(errmsg)

        # Verify status code matches
        if response["status"] != status_code:
            errmsg = (
                f"Iteration {iteration}: Expected status {status_code}, "
                f"got {response['status']}."
            )
            raise AssertionError(errmsg)

        # Verify content_type is application/json
        if response["content_type"] != "application/json":
            errmsg = (
                f"Iteration {iteration}: Expected content_type "
                f"'application/json', got '{response['content_type']}'."
            )
            raise AssertionError(errmsg)

        body = response["body"]

        # Verify body always contains "error" field
        if "error" not in body:
            errmsg = (
                f"Iteration {iteration}: Response body missing required "
                f"'error' field. Body: {body}"
            )
            raise AssertionError(errmsg)

        # Verify error value matches
        if body["error"] != error_code:
            errmsg = (
                f"Iteration {iteration}: Expected error '{error_code}', "
                f"got '{body['error']}'."
            )
            raise AssertionError(errmsg)

        # Verify error_description presence matches input
        if error_description is not None:
            if "error_description" not in body:
                errmsg = (
                    f"Iteration {iteration}: error_description was provided "
                    f"('{error_description}') but missing from body."
                )
                raise AssertionError(errmsg)
            if body["error_description"] != error_description:
                errmsg = (
                    f"Iteration {iteration}: Expected error_description "
                    f"'{error_description}', got '{body['error_description']}'."
                )
                raise AssertionError(errmsg)
        else:
            if "error_description" in body:
                errmsg = (
                    f"Iteration {iteration}: error_description was None "
                    f"but appeared in body with value "
                    f"'{body['error_description']}'."
                )
                raise AssertionError(errmsg)

        # Verify error_uri presence matches input
        if error_uri is not None:
            if "error_uri" not in body:
                errmsg = (
                    f"Iteration {iteration}: error_uri was provided "
                    f"('{error_uri}') but missing from body."
                )
                raise AssertionError(errmsg)
            if body["error_uri"] != error_uri:
                errmsg = (
                    f"Iteration {iteration}: Expected error_uri "
                    f"'{error_uri}', got '{body['error_uri']}'."
                )
                raise AssertionError(errmsg)
        else:
            if "error_uri" in body:
                errmsg = (
                    f"Iteration {iteration}: error_uri was None "
                    f"but appeared in body with value "
                    f"'{body['error_uri']}'."
                )
                raise AssertionError(errmsg)

    return
