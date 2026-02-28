"""
    Tests for the security error classes.

    This module contains unit tests and property-based tests for
    SecurityError, AuthenticationError, AuthorizationError,
    PolicyValidationError, and SecurityCompletenessError.
"""

import random
import string

from automojo.webworks.security.errors import (
    SecurityError,
    AuthenticationError,
    AuthorizationError,
    PolicyValidationError,
    SecurityCompletenessError,
)


# =============================================================================
# Unit Tests for SecurityError Base Class
# =============================================================================

def test_security_error_fields():
    """
        Test that SecurityError stores all provided fields correctly.
    """
    details = {"key": "value"}
    err = SecurityError(
        message="test error",
        error_code="TEST_ERROR",
        status_code=500,
        details=details,
    )

    if err.message != "test error":
        errmsg = f"Expected message 'test error', got {err.message!r}"
        raise AssertionError(errmsg)

    if err.error_code != "TEST_ERROR":
        errmsg = f"Expected error_code 'TEST_ERROR', got {err.error_code!r}"
        raise AssertionError(errmsg)

    if err.status_code != 500:
        errmsg = f"Expected status_code 500, got {err.status_code}"
        raise AssertionError(errmsg)

    if err.details != {"key": "value"}:
        errmsg = f"Expected details {{'key': 'value'}}, got {err.details}"
        raise AssertionError(errmsg)

    return


def test_security_error_default_details():
    """
        Test that SecurityError defaults details to an empty dict.
    """
    err = SecurityError(
        message="msg",
        error_code="CODE",
        status_code=400,
    )

    if err.details != {}:
        errmsg = f"Expected empty dict for details, got {err.details}"
        raise AssertionError(errmsg)

    return


def test_security_error_is_exception():
    """
        Test that SecurityError is a subclass of Exception.
    """
    err = SecurityError(
        message="test",
        error_code="CODE",
        status_code=500,
    )

    if isinstance(err, Exception) is not True:
        errmsg = "SecurityError should be an instance of Exception"
        raise AssertionError(errmsg)

    caught = False
    try:
        raise err
    except SecurityError:
        caught = True

    if caught is not True:
        errmsg = "SecurityError should be catchable as SecurityError"
        raise AssertionError(errmsg)

    return


def test_security_error_to_response_body():
    """
        Test that to_response_body returns error and message keys.
    """
    err = SecurityError(
        message="something went wrong",
        error_code="SOME_ERROR",
        status_code=500,
        details={"extra": "info"},
    )

    body = err.to_response_body()

    if "error" not in body:
        errmsg = "Response body missing 'error' key"
        raise AssertionError(errmsg)

    if "message" not in body:
        errmsg = "Response body missing 'message' key"
        raise AssertionError(errmsg)

    if body["error"] != "SOME_ERROR":
        errmsg = f"Expected error 'SOME_ERROR', got {body['error']!r}"
        raise AssertionError(errmsg)

    if body["message"] != "something went wrong":
        errmsg = f"Expected message 'something went wrong', got {body['message']!r}"
        raise AssertionError(errmsg)

    if "details" in body:
        errmsg = "Response body should not include details by default"
        raise AssertionError(errmsg)

    return


def test_security_error_to_response_body_with_details():
    """
        Test that to_response_body includes details when requested.
    """
    err = SecurityError(
        message="msg",
        error_code="CODE",
        status_code=500,
        details={"extra": "info"},
    )

    body = err.to_response_body(include_details=True)

    if "details" not in body:
        errmsg = "Response body should include details when include_details=True"
        raise AssertionError(errmsg)

    if body["details"] != {"extra": "info"}:
        errmsg = f"Expected details {{'extra': 'info'}}, got {body['details']}"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for AuthenticationError
# =============================================================================

def test_authentication_error_defaults():
    """
        Test that AuthenticationError has correct default values.
    """
    err = AuthenticationError()

    if err.status_code != 401:
        errmsg = f"Expected status_code 401, got {err.status_code}"
        raise AssertionError(errmsg)

    if err.error_code != "AUTHENTICATION_REQUIRED":
        errmsg = f"Expected error_code 'AUTHENTICATION_REQUIRED', got {err.error_code!r}"
        raise AssertionError(errmsg)

    if err.message != "Authentication required":
        errmsg = f"Expected default message 'Authentication required', got {err.message!r}"
        raise AssertionError(errmsg)

    if err.schemes != []:
        errmsg = f"Expected empty schemes list, got {err.schemes}"
        raise AssertionError(errmsg)

    return


def test_authentication_error_is_security_error():
    """
        Test that AuthenticationError is a subclass of SecurityError.
    """
    err = AuthenticationError()

    if isinstance(err, SecurityError) is not True:
        errmsg = "AuthenticationError should be a subclass of SecurityError"
        raise AssertionError(errmsg)

    return


def test_authentication_error_www_authenticate_default():
    """
        Test that get_www_authenticate_header defaults to Bearer.
    """
    err = AuthenticationError()
    header = err.get_www_authenticate_header()

    if header != "Bearer":
        errmsg = f"Expected 'Bearer', got {header!r}"
        raise AssertionError(errmsg)

    return


def test_authentication_error_www_authenticate_with_schemes():
    """
        Test that get_www_authenticate_header lists provided schemes.
    """
    err = AuthenticationError(schemes=["Bearer", "Basic"])
    header = err.get_www_authenticate_header()

    if header != "Bearer, Basic":
        errmsg = f"Expected 'Bearer, Basic', got {header!r}"
        raise AssertionError(errmsg)

    return


def test_authentication_error_custom_message():
    """
        Test that AuthenticationError accepts a custom message.
    """
    err = AuthenticationError(message="Token expired")

    if err.message != "Token expired":
        errmsg = f"Expected message 'Token expired', got {err.message!r}"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for AuthorizationError
# =============================================================================

def test_authorization_error_defaults():
    """
        Test that AuthorizationError has correct default values.
    """
    err = AuthorizationError()

    if err.status_code != 403:
        errmsg = f"Expected status_code 403, got {err.status_code}"
        raise AssertionError(errmsg)

    if err.error_code != "ACCESS_DENIED":
        errmsg = f"Expected error_code 'ACCESS_DENIED', got {err.error_code!r}"
        raise AssertionError(errmsg)

    if err.message != "Access denied":
        errmsg = f"Expected default message 'Access denied', got {err.message!r}"
        raise AssertionError(errmsg)

    return


def test_authorization_error_is_security_error():
    """
        Test that AuthorizationError is a subclass of SecurityError.
    """
    err = AuthorizationError()

    if isinstance(err, SecurityError) is not True:
        errmsg = "AuthorizationError should be a subclass of SecurityError"
        raise AssertionError(errmsg)

    return


def test_authorization_error_does_not_expose_reason():
    """
        Test that AuthorizationError does not expose internal reason
        in the response body.
    """
    err = AuthorizationError(
        message="Access denied",
        reason="User lacks admin role",
    )

    body = err.to_response_body()

    body_str = str(body)
    if "admin" in body_str:
        errmsg = "Response body should not contain internal reason details"
        raise AssertionError(errmsg)

    if "lacks" in body_str:
        errmsg = "Response body should not contain internal reason details"
        raise AssertionError(errmsg)

    return


def test_authorization_error_does_not_expose_reason_with_details():
    """
        Test that AuthorizationError does not expose internal reason
        even when include_details is True.
    """
    err = AuthorizationError(
        message="Access denied",
        reason="Missing scope: write",
    )

    body = err.to_response_body(include_details=True)

    body_str = str(body)
    if "Missing scope" in body_str:
        errmsg = "Response body should not contain internal reason even with details"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for PolicyValidationError
# =============================================================================

def test_policy_validation_error_fields():
    """
        Test that PolicyValidationError stores the policy reference.
    """
    bad_policy = {"not": "a real policy"}
    err = PolicyValidationError(
        message="Invalid policy type",
        policy=bad_policy,
    )

    if err.status_code != 500:
        errmsg = f"Expected status_code 500, got {err.status_code}"
        raise AssertionError(errmsg)

    if err.error_code != "INVALID_POLICY":
        errmsg = f"Expected error_code 'INVALID_POLICY', got {err.error_code!r}"
        raise AssertionError(errmsg)

    if err.policy is not bad_policy:
        errmsg = "Expected policy reference to be preserved"
        raise AssertionError(errmsg)

    return


def test_policy_validation_error_is_security_error():
    """
        Test that PolicyValidationError is a subclass of SecurityError.
    """
    err = PolicyValidationError(message="bad", policy=None)

    if isinstance(err, SecurityError) is not True:
        errmsg = "PolicyValidationError should be a subclass of SecurityError"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for SecurityCompletenessError
# =============================================================================

def test_security_completeness_error_fields():
    """
        Test that SecurityCompletenessError stores unprotected endpoints.
    """
    endpoints = ["/api/users", "/api/admin"]
    err = SecurityCompletenessError(unprotected_endpoints=endpoints)

    if err.status_code != 500:
        errmsg = f"Expected status_code 500, got {err.status_code}"
        raise AssertionError(errmsg)

    if err.error_code != "SECURITY_INCOMPLETE":
        errmsg = f"Expected error_code 'SECURITY_INCOMPLETE', got {err.error_code!r}"
        raise AssertionError(errmsg)

    if err.unprotected_endpoints != endpoints:
        errmsg = f"Expected endpoints {endpoints}, got {err.unprotected_endpoints}"
        raise AssertionError(errmsg)

    if "2" not in err.message:
        errmsg = f"Expected message to contain endpoint count '2', got {err.message!r}"
        raise AssertionError(errmsg)

    return


def test_security_completeness_error_is_security_error():
    """
        Test that SecurityCompletenessError is a subclass of SecurityError.
    """
    err = SecurityCompletenessError(unprotected_endpoints=[])

    if isinstance(err, SecurityError) is not True:
        errmsg = "SecurityCompletenessError should be a subclass of SecurityError"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Helper Functions for Property-Based Tests
# =============================================================================

def _random_string(min_length: int = 1, max_length: int = 20) -> str:
    """
        Generate a random alphanumeric string.

        :param min_length: Minimum string length.
        :param max_length: Maximum string length.

        :returns: A random string of lowercase letters and digits.
    """
    length = random.randint(min_length, max_length)
    chars = string.ascii_lowercase + string.digits
    rtnval = "".join(random.choices(chars, k=length))
    return rtnval


def _random_scheme() -> str:
    """
        Generate a random authentication scheme name.

        :returns: A random scheme name from a realistic set.
    """
    schemes = ["Bearer", "Basic", "Digest", "HOBA", "Mutual", "Negotiate", "OAuth", "SCRAM-SHA-256"]
    rtnval = random.choice(schemes)
    return rtnval


def _random_schemes_list() -> list:
    """
        Generate a random list of authentication schemes.

        :returns: A list of 0 to 4 random scheme names.
    """
    count = random.randint(0, 4)
    rtnval = [_random_scheme() for _ in range(count)]
    return rtnval


def _random_endpoint_path() -> str:
    """
        Generate a random endpoint path.

        :returns: A random URL path string.
    """
    segment_count = random.randint(1, 4)
    segments = [_random_string(min_length=2, max_length=10) for _ in range(segment_count)]
    rtnval = "/" + "/".join(segments)
    return rtnval


# =============================================================================
# Property-Based Test for Security Error Response
# =============================================================================

def test_property_security_error_response():
    """
        Property test for Security Error Response.

        **Validates: Requirements 10.1, 10.2, 10.3, 10.4, 10.6**

        For any SecurityError subclass:
        - to_response_body() SHALL return a dict with 'error' and 'message' keys
        - AuthenticationError SHALL have status_code 401
        - AuthorizationError SHALL have status_code 403
        - AuthorizationError SHALL NOT expose internal reason in to_response_body()
        - AuthenticationError.get_www_authenticate_header() SHALL return valid header value
    """
    iteration_count = 100

    for iteration in range(iteration_count):

        # --- Test SecurityError base class ---
        message = _random_string()
        error_code = _random_string(min_length=3, max_length=15).upper()
        status_code = random.choice([400, 401, 403, 404, 500, 502, 503])
        details = {"key_" + _random_string(max_length=5): _random_string() for _ in range(random.randint(0, 3))}

        base_err = SecurityError(
            message=message,
            error_code=error_code,
            status_code=status_code,
            details=details,
        )

        body = base_err.to_response_body()

        # Property: to_response_body() SHALL return dict with 'error' and 'message' keys
        if "error" not in body:
            errmsg = (
                f"Iteration {iteration}: SecurityError.to_response_body() "
                f"missing 'error' key. body={body}"
            )
            raise AssertionError(errmsg)

        if "message" not in body:
            errmsg = (
                f"Iteration {iteration}: SecurityError.to_response_body() "
                f"missing 'message' key. body={body}"
            )
            raise AssertionError(errmsg)

        if body["error"] != error_code:
            errmsg = (
                f"Iteration {iteration}: Expected error={error_code!r}, "
                f"got {body['error']!r}"
            )
            raise AssertionError(errmsg)

        if body["message"] != message:
            errmsg = (
                f"Iteration {iteration}: Expected message={message!r}, "
                f"got {body['message']!r}"
            )
            raise AssertionError(errmsg)

        # --- Test AuthenticationError ---
        authn_message = _random_string()
        authn_schemes = _random_schemes_list()

        authn_err = AuthenticationError(
            message=authn_message,
            schemes=authn_schemes,
        )

        # Property: AuthenticationError SHALL have status_code 401
        if authn_err.status_code != 401:
            errmsg = (
                f"Iteration {iteration}: AuthenticationError.status_code "
                f"should be 401, got {authn_err.status_code}"
            )
            raise AssertionError(errmsg)

        authn_body = authn_err.to_response_body()

        # Property: to_response_body() SHALL return dict with 'error' and 'message' keys
        if "error" not in authn_body:
            errmsg = (
                f"Iteration {iteration}: AuthenticationError.to_response_body() "
                f"missing 'error' key"
            )
            raise AssertionError(errmsg)

        if "message" not in authn_body:
            errmsg = (
                f"Iteration {iteration}: AuthenticationError.to_response_body() "
                f"missing 'message' key"
            )
            raise AssertionError(errmsg)

        # Property: get_www_authenticate_header() SHALL return valid header value
        header = authn_err.get_www_authenticate_header()

        if not isinstance(header, str):
            errmsg = (
                f"Iteration {iteration}: get_www_authenticate_header() "
                f"should return str, got {type(header).__name__}"
            )
            raise AssertionError(errmsg)

        if len(header) == 0:
            errmsg = (
                f"Iteration {iteration}: get_www_authenticate_header() "
                f"should not return empty string"
            )
            raise AssertionError(errmsg)

        # When schemes are provided, each scheme should appear in the header
        if len(authn_schemes) > 0:
            for scheme in authn_schemes:
                if scheme not in header:
                    errmsg = (
                        f"Iteration {iteration}: Scheme {scheme!r} not found "
                        f"in WWW-Authenticate header {header!r}. "
                        f"schemes={authn_schemes}"
                    )
                    raise AssertionError(errmsg)

        # --- Test AuthorizationError ---
        authz_message = _random_string()
        internal_reason = "secret_" + _random_string()

        authz_err = AuthorizationError(
            message=authz_message,
            reason=internal_reason,
        )

        # Property: AuthorizationError SHALL have status_code 403
        if authz_err.status_code != 403:
            errmsg = (
                f"Iteration {iteration}: AuthorizationError.status_code "
                f"should be 403, got {authz_err.status_code}"
            )
            raise AssertionError(errmsg)

        authz_body = authz_err.to_response_body()

        # Property: to_response_body() SHALL return dict with 'error' and 'message' keys
        if "error" not in authz_body:
            errmsg = (
                f"Iteration {iteration}: AuthorizationError.to_response_body() "
                f"missing 'error' key"
            )
            raise AssertionError(errmsg)

        if "message" not in authz_body:
            errmsg = (
                f"Iteration {iteration}: AuthorizationError.to_response_body() "
                f"missing 'message' key"
            )
            raise AssertionError(errmsg)

        # Property: AuthorizationError SHALL NOT expose internal reason in to_response_body()
        authz_body_str = str(authz_body)
        if internal_reason in authz_body_str:
            errmsg = (
                f"Iteration {iteration}: AuthorizationError.to_response_body() "
                f"leaked internal reason {internal_reason!r} in body {authz_body}"
            )
            raise AssertionError(errmsg)

        # Also check with include_details=True
        authz_body_detailed = authz_err.to_response_body(include_details=True)
        authz_body_detailed_str = str(authz_body_detailed)
        if internal_reason in authz_body_detailed_str:
            errmsg = (
                f"Iteration {iteration}: AuthorizationError.to_response_body(include_details=True) "
                f"leaked internal reason {internal_reason!r} in body {authz_body_detailed}"
            )
            raise AssertionError(errmsg)

    return
