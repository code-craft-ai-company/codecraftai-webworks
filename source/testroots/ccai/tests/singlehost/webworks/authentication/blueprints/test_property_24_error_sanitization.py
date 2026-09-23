"""
    Property test for error response sanitization.

    This module verifies Property 24: Error Response Sanitization.

    For any error response from a Security_Blueprint, the response body
    SHALL NOT contain credentials, tokens, secrets, or stack traces.

    **Validates: Requirements 10.2, 10.5**
"""

import random
import string

from ccai.webworks.authentication.blueprints.security import SecurityBlueprint
from ccai.webworks.authentication.blueprints.responses import AuthError


# =============================================================================
# Test Helpers
# =============================================================================

# Keys that are only caught by sanitize_dict (dict-level redaction) but
# not by sanitize_credentials (string-level regex).  These are used in
# dict-key tests but excluded from embedded-string tests.
_DICT_ONLY_KEYS = [
    "password", "passwd", "pwd", "secret", "token", "access_token",
    "refresh_token", "id_token", "api_key", "apikey", "client_secret",
    "credentials", "session_id", "nonce", "authorization",
]

# Keys whose values are reliably caught by sanitize_credentials when
# embedded in a string as key=value.
_STRING_EMBEDDABLE_KEYS = [
    "password", "passwd", "pwd", "secret", "token", "access_token",
    "refresh_token", "id_token", "api_key", "apikey", "client_secret",
    "credentials", "session_id", "nonce",
]

# Patterns that indicate a stack trace is present
_STACK_TRACE_INDICATORS = [
    "Traceback (most recent call last)",
    "File \"",
    "raise ",
]


def _random_string(min_length=4, max_length=20):
    """
        Generate a random alphanumeric string.
    """
    length = random.randint(min_length, max_length)
    rtnval = "".join(random.choices(string.ascii_letters + string.digits, k=length))
    return rtnval


def _random_sensitive_value():
    """
        Generate a random value that looks like a credential.
    """
    return _random_string(16, 40)


def _generate_error_with_sensitive_body():
    """
        Generate an AuthError whose description embeds a sensitive
        key=value pair.
    """
    key = random.choice(_STRING_EMBEDDABLE_KEYS)
    value = _random_sensitive_value()
    description = "Failed because {}={}".format(key, value)

    error = AuthError(
        error="invalid_request",
        error_description=description,
    )
    return error, key, value



# =============================================================================
# Property Tests
# =============================================================================

def test_property_24_sanitize_error_response_redacts_sensitive_keys():
    """
        Property 24: Error Response Sanitization - sensitive dict keys.

        For any error response whose body contains sensitive keys
        (password, token, secret, etc.), sanitize_error_response SHALL
        replace the values with '[REDACTED]'.

        **Validates: Requirements 10.2, 10.5**
    """
    num_iterations = 100

    for iteration in range(num_iterations):
        sensitive_key = random.choice(_DICT_ONLY_KEYS)
        sensitive_value = _random_sensitive_value()

        response = {
            "status": 400,
            "body": {
                "error": "invalid_request",
                "error_description": "Something went wrong",
                sensitive_key: sensitive_value,
            },
            "content_type": "application/json",
        }

        sanitized = SecurityBlueprint.sanitize_error_response(response)
        body = sanitized["body"]

        # The sensitive key's value must be redacted
        if sensitive_key in body and body[sensitive_key] == sensitive_value:
            errmsg = (
                "Iteration {}: Sensitive key '{}' was not redacted. "
                "Value '{}' still present in body.".format(
                    iteration, sensitive_key, sensitive_value
                )
            )
            raise AssertionError(errmsg)

        # The error field must still be present
        if "error" not in body:
            errmsg = (
                "Iteration {}: 'error' field missing from sanitized "
                "body.".format(iteration)
            )
            raise AssertionError(errmsg)

    return


def test_property_24_sanitize_error_response_redacts_embedded_credentials():
    """
        Property 24: Error Response Sanitization - embedded credentials.

        For any error response whose description contains embedded
        credential patterns (e.g. password=secret123), the sanitized
        response SHALL have those patterns redacted.

        **Validates: Requirements 10.2, 10.5**
    """
    num_iterations = 100

    for iteration in range(num_iterations):
        auth_error, key, value = _generate_error_with_sensitive_body()
        response = SecurityBlueprint.format_error(auth_error, status_code=400)

        sanitized = SecurityBlueprint.sanitize_error_response(response)
        body = sanitized["body"]
        description = body.get("error_description", "")

        # The raw sensitive value must not appear in the description
        if value in description:
            errmsg = (
                "Iteration {}: Sensitive value '{}' for key '{}' "
                "still present in error_description after "
                "sanitization.".format(iteration, value, key)
            )
            raise AssertionError(errmsg)

    return


def test_property_24_handle_internal_error_no_stack_traces():
    """
        Property 24: Error Response Sanitization - internal errors.

        For any internal exception, handle_internal_error SHALL return
        a generic error response that does not contain stack traces,
        exception class names, or the original error message.

        **Validates: Requirements 10.2, 10.5**
    """
    num_iterations = 100

    for iteration in range(num_iterations):
        # Generate a random exception with a message that could leak info
        exc_message = "Database connection failed: password={} host=db.internal".format(
            _random_sensitive_value()
        )
        exception = RuntimeError(exc_message)

        response = SecurityBlueprint.handle_internal_error(exception)

        # Verify status is 500
        if response["status"] != 500:
            errmsg = (
                "Iteration {}: Expected status 500, got {}.".format(
                    iteration, response["status"]
                )
            )
            raise AssertionError(errmsg)

        body = response["body"]

        # Verify the body uses a generic error code
        if body.get("error") != "server_error":
            errmsg = (
                "Iteration {}: Expected error 'server_error', "
                "got '{}'.".format(iteration, body.get("error"))
            )
            raise AssertionError(errmsg)

        # Verify the original exception message is not in the response
        body_str = str(body)
        if exc_message in body_str:
            errmsg = (
                "Iteration {}: Original exception message leaked "
                "into error response body.".format(iteration)
            )
            raise AssertionError(errmsg)

        # Verify no stack trace indicators are present
        for indicator in _STACK_TRACE_INDICATORS:
            if indicator in body_str:
                errmsg = (
                    "Iteration {}: Stack trace indicator '{}' found "
                    "in error response body.".format(iteration, indicator)
                )
                raise AssertionError(errmsg)

        # Verify the exception class name is not in the response
        if "RuntimeError" in body_str:
            errmsg = (
                "Iteration {}: Exception class name 'RuntimeError' "
                "found in error response body.".format(iteration)
            )
            raise AssertionError(errmsg)

    return


def test_property_24_sanitize_preserves_error_structure():
    """
        Property 24: Error Response Sanitization - structure preservation.

        For any sanitized error response, the top-level structure
        (status, body, content_type) SHALL be preserved and the body
        SHALL still contain the 'error' field.

        **Validates: Requirements 10.2, 10.5**
    """
    num_iterations = 100

    for iteration in range(num_iterations):
        status_code = random.choice([400, 401, 403, 500])
        error_code = random.choice([
            "invalid_request", "invalid_client", "server_error",
            "access_denied", "invalid_grant",
        ])

        auth_error = AuthError(
            error=error_code,
            error_description="password={} leaked".format(_random_sensitive_value()),
        )
        response = SecurityBlueprint.format_error(auth_error, status_code=status_code)
        sanitized = SecurityBlueprint.sanitize_error_response(response)

        # Verify top-level keys are preserved
        for key in ("status", "body", "content_type"):
            if key not in sanitized:
                errmsg = (
                    "Iteration {}: Sanitized response missing key "
                    "'{}'.".format(iteration, key)
                )
                raise AssertionError(errmsg)

        # Verify status code is preserved
        if sanitized["status"] != status_code:
            errmsg = (
                "Iteration {}: Status code changed from {} to {} "
                "after sanitization.".format(
                    iteration, status_code, sanitized["status"]
                )
            )
            raise AssertionError(errmsg)

        # Verify error field is preserved in body
        if "error" not in sanitized["body"]:
            errmsg = (
                "Iteration {}: 'error' field missing from sanitized "
                "body.".format(iteration)
            )
            raise AssertionError(errmsg)

        if sanitized["body"]["error"] != error_code:
            errmsg = (
                "Iteration {}: Error code changed from '{}' to '{}' "
                "after sanitization.".format(
                    iteration, error_code, sanitized["body"]["error"]
                )
            )
            raise AssertionError(errmsg)

    return
