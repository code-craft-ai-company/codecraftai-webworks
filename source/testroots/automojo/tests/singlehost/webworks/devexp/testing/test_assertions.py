"""
    Tests for the assertion helpers module.

    This module contains unit tests and property-based tests for the
    :class:`TestAssertions` class in
    :mod:`automojo.webworks.devexp.testing.assertions`.
"""

import json
import random
import string

from automojo.webworks.devexp.testing.assertions import TestAssertions
from automojo.webworks.devexp.testing.testresponse import TestResponse


# =============================================================================
# Test Helpers
# =============================================================================

def _make_response(
    status_code=200,
    headers=None,
    body=b"",
):
    """
        Create a TestResponse with the given attributes.

        :param status_code: The HTTP status code.
        :param headers: Optional headers dictionary.
        :param body: The response body bytes.

        :returns: A :class:`TestResponse` instance.
    """
    if headers is None:
        headers = {}

    response = TestResponse(
        status_code=status_code,
        headers=headers,
        body=body,
    )

    return response


def _make_json_response(data, status_code=200, headers=None):
    """
        Create a TestResponse with a JSON body.

        :param data: The JSON-serializable data.
        :param status_code: The HTTP status code.
        :param headers: Optional additional headers.

        :returns: A :class:`TestResponse` instance.
    """
    if headers is None:
        headers = {}

    headers.setdefault("Content-Type", "application/json")
    body = json.dumps(data).encode("utf-8")

    response = TestResponse(
        status_code=status_code,
        headers=headers,
        body=body,
    )

    return response


# =============================================================================
# Unit Tests for assert_status
# =============================================================================

def test_assert_status_passes_on_match():
    """
        Test that assert_status does not raise when status matches.
    """
    response = _make_response(status_code=200)

    # Should not raise
    TestAssertions.assert_status(response, expected=200)

    return


def test_assert_status_fails_on_mismatch():
    """
        Test that assert_status raises AssertionError on mismatch.
    """
    response = _make_response(status_code=404)

    raised = False
    error_message = ""

    try:
        TestAssertions.assert_status(response, expected=200)
    except AssertionError as exc:
        raised = True
        error_message = str(exc)

    if raised is not True:
        errmsg = "Expected AssertionError for status mismatch."
        raise AssertionError(errmsg)

    if "200" not in error_message:
        errmsg = "Expected '200' in error message, got '{}'".format(error_message)
        raise AssertionError(errmsg)

    if "404" not in error_message:
        errmsg = "Expected '404' in error message, got '{}'".format(error_message)
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for assert_json
# =============================================================================

def test_assert_json_passes_on_exact_match():
    """
        Test that assert_json passes when JSON matches exactly.
    """
    data = {"name": "test", "value": 42}
    response = _make_json_response(data)

    TestAssertions.assert_json(response, expected=data)

    return


def test_assert_json_fails_on_mismatch():
    """
        Test that assert_json raises AssertionError on mismatch.
    """
    actual_data = {"name": "actual"}
    expected_data = {"name": "expected"}
    response = _make_json_response(actual_data)

    raised = False
    error_message = ""

    try:
        TestAssertions.assert_json(response, expected=expected_data)
    except AssertionError as exc:
        raised = True
        error_message = str(exc)

    if raised is not True:
        errmsg = "Expected AssertionError for JSON mismatch."
        raise AssertionError(errmsg)

    if "expected" not in error_message:
        errmsg = "Expected 'expected' in error message, got '{}'".format(
            error_message
        )
        raise AssertionError(errmsg)

    return


def test_assert_json_partial_match_passes():
    """
        Test that assert_json with partial=True passes when expected
        keys are present.
    """
    actual_data = {"name": "test", "value": 42, "extra": "ignored"}
    expected_data = {"name": "test", "value": 42}
    response = _make_json_response(actual_data)

    TestAssertions.assert_json(response, expected=expected_data, partial=True)

    return


def test_assert_json_partial_match_fails_on_missing_key():
    """
        Test that assert_json with partial=True fails when an expected
        key is missing.
    """
    actual_data = {"name": "test"}
    expected_data = {"name": "test", "missing_key": "value"}
    response = _make_json_response(actual_data)

    raised = False

    try:
        TestAssertions.assert_json(response, expected=expected_data, partial=True)
    except AssertionError:
        raised = True

    if raised is not True:
        errmsg = "Expected AssertionError for missing key in partial match."
        raise AssertionError(errmsg)

    return


def test_assert_json_partial_match_fails_on_value_mismatch():
    """
        Test that assert_json with partial=True fails when a value
        does not match.
    """
    actual_data = {"name": "actual"}
    expected_data = {"name": "expected"}
    response = _make_json_response(actual_data)

    raised = False

    try:
        TestAssertions.assert_json(response, expected=expected_data, partial=True)
    except AssertionError:
        raised = True

    if raised is not True:
        errmsg = "Expected AssertionError for value mismatch in partial match."
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for assert_header
# =============================================================================

def test_assert_header_passes_on_match():
    """
        Test that assert_header passes when header matches.
    """
    response = _make_response(headers={"X-Custom": "my-value"})

    TestAssertions.assert_header(response, name="X-Custom", expected="my-value")

    return


def test_assert_header_fails_on_mismatch():
    """
        Test that assert_header raises AssertionError on value mismatch.
    """
    response = _make_response(headers={"X-Custom": "actual"})

    raised = False
    error_message = ""

    try:
        TestAssertions.assert_header(response, name="X-Custom", expected="expected")
    except AssertionError as exc:
        raised = True
        error_message = str(exc)

    if raised is not True:
        errmsg = "Expected AssertionError for header mismatch."
        raise AssertionError(errmsg)

    if "expected" not in error_message:
        errmsg = "Expected 'expected' in error message, got '{}'".format(
            error_message
        )
        raise AssertionError(errmsg)

    if "actual" not in error_message:
        errmsg = "Expected 'actual' in error message, got '{}'".format(
            error_message
        )
        raise AssertionError(errmsg)

    return


def test_assert_header_fails_on_missing():
    """
        Test that assert_header raises AssertionError when header is missing.
    """
    response = _make_response(headers={})

    raised = False
    error_message = ""

    try:
        TestAssertions.assert_header(response, name="X-Missing", expected="value")
    except AssertionError as exc:
        raised = True
        error_message = str(exc)

    if raised is not True:
        errmsg = "Expected AssertionError for missing header."
        raise AssertionError(errmsg)

    if "not found" not in error_message:
        errmsg = "Expected 'not found' in error message, got '{}'".format(
            error_message
        )
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for assert_content_type
# =============================================================================

def test_assert_content_type_passes_on_match():
    """
        Test that assert_content_type passes when Content-Type matches.
    """
    response = _make_response(headers={"Content-Type": "application/json"})

    TestAssertions.assert_content_type(response, expected="application/json")

    return


def test_assert_content_type_fails_on_mismatch():
    """
        Test that assert_content_type raises AssertionError on mismatch.
    """
    response = _make_response(headers={"Content-Type": "text/html"})

    raised = False
    error_message = ""

    try:
        TestAssertions.assert_content_type(response, expected="application/json")
    except AssertionError as exc:
        raised = True
        error_message = str(exc)

    if raised is not True:
        errmsg = "Expected AssertionError for Content-Type mismatch."
        raise AssertionError(errmsg)

    if "application/json" not in error_message:
        errmsg = "Expected 'application/json' in error message."
        raise AssertionError(errmsg)

    if "text/html" not in error_message:
        errmsg = "Expected 'text/html' in error message."
        raise AssertionError(errmsg)

    return


def test_assert_content_type_fails_on_missing():
    """
        Test that assert_content_type raises when Content-Type is missing.
    """
    response = _make_response(headers={})

    raised = False

    try:
        TestAssertions.assert_content_type(response, expected="application/json")
    except AssertionError:
        raised = True

    if raised is not True:
        errmsg = "Expected AssertionError for missing Content-Type."
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for assert_redirect
# =============================================================================

def test_assert_redirect_passes_on_match():
    """
        Test that assert_redirect passes for a valid redirect.
    """
    response = _make_response(
        status_code=302,
        headers={"Location": "/new-location"},
    )

    TestAssertions.assert_redirect(response, expected_location="/new-location")

    return


def test_assert_redirect_custom_status():
    """
        Test that assert_redirect supports custom redirect status codes.
    """
    response = _make_response(
        status_code=301,
        headers={"Location": "/permanent"},
    )

    TestAssertions.assert_redirect(
        response,
        expected_location="/permanent",
        status=301,
    )

    return


def test_assert_redirect_fails_on_wrong_status():
    """
        Test that assert_redirect raises on wrong status code.
    """
    response = _make_response(
        status_code=200,
        headers={"Location": "/somewhere"},
    )

    raised = False
    error_message = ""

    try:
        TestAssertions.assert_redirect(response, expected_location="/somewhere")
    except AssertionError as exc:
        raised = True
        error_message = str(exc)

    if raised is not True:
        errmsg = "Expected AssertionError for wrong redirect status."
        raise AssertionError(errmsg)

    if "302" not in error_message:
        errmsg = "Expected '302' in error message, got '{}'".format(error_message)
        raise AssertionError(errmsg)

    if "200" not in error_message:
        errmsg = "Expected '200' in error message, got '{}'".format(error_message)
        raise AssertionError(errmsg)

    return


def test_assert_redirect_fails_on_missing_location():
    """
        Test that assert_redirect raises when Location header is missing.
    """
    response = _make_response(status_code=302, headers={})

    raised = False

    try:
        TestAssertions.assert_redirect(response, expected_location="/target")
    except AssertionError:
        raised = True

    if raised is not True:
        errmsg = "Expected AssertionError for missing Location header."
        raise AssertionError(errmsg)

    return


def test_assert_redirect_fails_on_wrong_location():
    """
        Test that assert_redirect raises on wrong Location value.
    """
    response = _make_response(
        status_code=302,
        headers={"Location": "/actual"},
    )

    raised = False
    error_message = ""

    try:
        TestAssertions.assert_redirect(response, expected_location="/expected")
    except AssertionError as exc:
        raised = True
        error_message = str(exc)

    if raised is not True:
        errmsg = "Expected AssertionError for wrong Location."
        raise AssertionError(errmsg)

    if "/expected" not in error_message:
        errmsg = "Expected '/expected' in error message."
        raise AssertionError(errmsg)

    if "/actual" not in error_message:
        errmsg = "Expected '/actual' in error message."
        raise AssertionError(errmsg)

    return


# =============================================================================
# Property Test Helpers
# =============================================================================

_PROPERTY_ITERATIONS = 100


def _random_string(min_len=1, max_len=20):
    """
        Generate a random alphanumeric string.

        :param min_len: Minimum string length.
        :param max_len: Maximum string length.

        :returns: A random string.
    """
    length = random.randint(min_len, max_len)
    value = "".join(random.choices(string.ascii_letters + string.digits, k=length))
    return value


def _random_status_code():
    """
        Generate a random HTTP status code in the range 100-599.

        :returns: An integer status code.
    """
    code = random.randint(100, 599)
    return code


def _random_header_name():
    """
        Generate a random header name.

        :returns: A header name string.
    """
    name = "X-" + _random_string(min_len=3, max_len=12)
    return name


def _random_content_type():
    """
        Generate a random content type string.

        :returns: A content type string.
    """
    types = [
        "text/html",
        "text/plain",
        "application/json",
        "application/xml",
        "image/png",
        "multipart/form-data",
    ]
    content_type = random.choice(types)
    return content_type


def _random_path():
    """
        Generate a random URL path.

        :returns: A path string starting with /.
    """
    depth = random.randint(1, 4)
    parts = []

    for _ in range(depth):
        part = _random_string(min_len=2, max_len=10)
        parts.append(part)

    path = "/" + "/".join(parts)
    return path


# =============================================================================
# Property 2: Test Assertion Error Messages
# Feature: developer-experience, Property 2: Test Assertion Error Messages
# Validates: Requirements 7.7
# =============================================================================

def test_property_2_assert_status_error_messages():
    """
        Property 2: Test Assertion Error Messages (assert_status)

        For any assertion failure in assert_status, the AssertionError
        message SHALL contain both the expected and actual status code
        values.

        This test generates random mismatched status codes across 100
        iterations and verifies the error message content.

        **Feature: developer-experience, Property 2: Test Assertion Error Messages**
        **Validates: Requirements 7.7**
    """
    for iteration in range(_PROPERTY_ITERATIONS):
        expected_status = _random_status_code()

        # Generate a different actual status
        actual_status = _random_status_code()
        while actual_status == expected_status:
            actual_status = _random_status_code()

        response = _make_response(status_code=actual_status)

        raised = False
        error_message = ""

        try:
            TestAssertions.assert_status(response, expected=expected_status)
        except AssertionError as exc:
            raised = True
            error_message = str(exc)

        if raised is not True:
            errmsg = (
                "Iteration {}: Expected AssertionError for status "
                "mismatch (expected={}, actual={})"
            ).format(iteration, expected_status, actual_status)
            raise AssertionError(errmsg)

        expected_str = str(expected_status)
        actual_str = str(actual_status)

        if expected_str not in error_message:
            errmsg = (
                "Iteration {}: Expected '{}' in error message, "
                "got '{}'"
            ).format(iteration, expected_str, error_message)
            raise AssertionError(errmsg)

        if actual_str not in error_message:
            errmsg = (
                "Iteration {}: Expected '{}' in error message, "
                "got '{}'"
            ).format(iteration, actual_str, error_message)
            raise AssertionError(errmsg)

    return


def test_property_2_assert_header_error_messages():
    """
        Property 2: Test Assertion Error Messages (assert_header)

        For any assertion failure in assert_header, the AssertionError
        message SHALL contain both the expected and actual header values.

        **Feature: developer-experience, Property 2: Test Assertion Error Messages**
        **Validates: Requirements 7.7**
    """
    for iteration in range(_PROPERTY_ITERATIONS):
        header_name = _random_header_name()
        expected_value = _random_string()

        # Generate a different actual value
        actual_value = _random_string()
        while actual_value == expected_value:
            actual_value = _random_string()

        response = _make_response(headers={header_name: actual_value})

        raised = False
        error_message = ""

        try:
            TestAssertions.assert_header(
                response,
                name=header_name,
                expected=expected_value,
            )
        except AssertionError as exc:
            raised = True
            error_message = str(exc)

        if raised is not True:
            errmsg = (
                "Iteration {}: Expected AssertionError for header "
                "mismatch (expected='{}', actual='{}')"
            ).format(iteration, expected_value, actual_value)
            raise AssertionError(errmsg)

        if expected_value not in error_message:
            errmsg = (
                "Iteration {}: Expected '{}' in error message, "
                "got '{}'"
            ).format(iteration, expected_value, error_message)
            raise AssertionError(errmsg)

        if actual_value not in error_message:
            errmsg = (
                "Iteration {}: Expected '{}' in error message, "
                "got '{}'"
            ).format(iteration, actual_value, error_message)
            raise AssertionError(errmsg)

    return


def test_property_2_assert_content_type_error_messages():
    """
        Property 2: Test Assertion Error Messages (assert_content_type)

        For any assertion failure in assert_content_type, the
        AssertionError message SHALL contain both the expected and
        actual content type values.

        **Feature: developer-experience, Property 2: Test Assertion Error Messages**
        **Validates: Requirements 7.7**
    """
    for iteration in range(_PROPERTY_ITERATIONS):
        expected_ct = _random_content_type()

        # Generate a different actual content type
        actual_ct = _random_content_type()
        while actual_ct == expected_ct:
            actual_ct = _random_content_type()

        response = _make_response(headers={"Content-Type": actual_ct})

        raised = False
        error_message = ""

        try:
            TestAssertions.assert_content_type(response, expected=expected_ct)
        except AssertionError as exc:
            raised = True
            error_message = str(exc)

        if raised is not True:
            errmsg = (
                "Iteration {}: Expected AssertionError for content type "
                "mismatch (expected='{}', actual='{}')"
            ).format(iteration, expected_ct, actual_ct)
            raise AssertionError(errmsg)

        if expected_ct not in error_message:
            errmsg = (
                "Iteration {}: Expected '{}' in error message, "
                "got '{}'"
            ).format(iteration, expected_ct, error_message)
            raise AssertionError(errmsg)

        if actual_ct not in error_message:
            errmsg = (
                "Iteration {}: Expected '{}' in error message, "
                "got '{}'"
            ).format(iteration, actual_ct, error_message)
            raise AssertionError(errmsg)

    return


def test_property_2_assert_redirect_error_messages():
    """
        Property 2: Test Assertion Error Messages (assert_redirect)

        For any assertion failure in assert_redirect, the AssertionError
        message SHALL contain both the expected and actual values.

        **Feature: developer-experience, Property 2: Test Assertion Error Messages**
        **Validates: Requirements 7.7**
    """
    for iteration in range(_PROPERTY_ITERATIONS):
        expected_location = _random_path()

        # Generate a different actual location
        actual_location = _random_path()
        while actual_location == expected_location:
            actual_location = _random_path()

        # Test with correct status but wrong location
        response = _make_response(
            status_code=302,
            headers={"Location": actual_location},
        )

        raised = False
        error_message = ""

        try:
            TestAssertions.assert_redirect(
                response,
                expected_location=expected_location,
            )
        except AssertionError as exc:
            raised = True
            error_message = str(exc)

        if raised is not True:
            errmsg = (
                "Iteration {}: Expected AssertionError for redirect "
                "location mismatch (expected='{}', actual='{}')"
            ).format(iteration, expected_location, actual_location)
            raise AssertionError(errmsg)

        if expected_location not in error_message:
            errmsg = (
                "Iteration {}: Expected '{}' in error message, "
                "got '{}'"
            ).format(iteration, expected_location, error_message)
            raise AssertionError(errmsg)

        if actual_location not in error_message:
            errmsg = (
                "Iteration {}: Expected '{}' in error message, "
                "got '{}'"
            ).format(iteration, actual_location, error_message)
            raise AssertionError(errmsg)

    return
