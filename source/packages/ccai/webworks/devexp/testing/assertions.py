"""
    Assertion helpers for endpoint testing.

    This module provides the :class:`TestAssertions` class with static
    methods for common response verification patterns. Each assertion
    raises an :class:`AssertionError` with a clear message containing
    both the expected and actual values when the check fails.

    Available assertions:

    - :meth:`TestAssertions.assert_status` -- Verify response status code.
    - :meth:`TestAssertions.assert_json` -- Verify response JSON body
      with optional partial matching.
    - :meth:`TestAssertions.assert_header` -- Verify a response header
      value (case-insensitive lookup).
    - :meth:`TestAssertions.assert_content_type` -- Verify the
      Content-Type header.
    - :meth:`TestAssertions.assert_redirect` -- Verify a redirect
      response with status code and Location header.
"""

import json as _json_module

from typing import Any

from ccai.webworks.devexp.testing.testresponse import TestResponse


class TestAssertions:
    """
        Assertion helpers for endpoint testing.

        All methods are static and raise :class:`AssertionError` with
        descriptive messages showing expected vs actual values when
        the assertion fails.
    """

    @staticmethod
    def assert_status(response: TestResponse, expected: int) -> None:
        """
            Assert that the response status code matches the expected value.

            :param response: The test response to check.
            :param expected: The expected HTTP status code.

            :raises AssertionError: If the status code does not match.
        """
        actual = response.status_code

        if actual != expected:
            errmsg = (
                "Expected status {}, got {}"
            ).format(expected, actual)
            raise AssertionError(errmsg)

        return

    @staticmethod
    def assert_json(
        response: TestResponse,
        expected: Any,
        partial: bool = False,
    ) -> None:
        """
            Assert that the response JSON body matches the expected value.

            When *partial* is ``False``, the entire JSON body must match
            the expected value exactly. When *partial* is ``True``, only
            the keys present in *expected* are checked, and extra keys
            in the response are allowed.

            :param response: The test response to check.
            :param expected: The expected JSON structure.
            :param partial: If True, perform partial matching.

            :raises AssertionError: If the JSON body does not match.
            :raises ValueError: If the response body is not valid JSON.
        """
        actual = response.json

        if partial:
            _check_partial_match(expected, actual, path="$")
        else:
            if actual != expected:
                expected_str = _json_module.dumps(expected, sort_keys=True, default=str)
                actual_str = _json_module.dumps(actual, sort_keys=True, default=str)
                errmsg = (
                    "Expected JSON {}, got {}"
                ).format(expected_str, actual_str)
                raise AssertionError(errmsg)

        return

    @staticmethod
    def assert_header(
        response: TestResponse,
        name: str,
        expected: str,
    ) -> None:
        """
            Assert that a response header matches the expected value.

            The header lookup is case-insensitive.

            :param response: The test response to check.
            :param name: The header name to look up.
            :param expected: The expected header value.

            :raises AssertionError: If the header is missing or does
                not match.
        """
        actual = response.get_header(name)

        if actual is None:
            errmsg = (
                "Expected header '{}' with value '{}', "
                "but header was not found"
            ).format(name, expected)
            raise AssertionError(errmsg)

        if actual != expected:
            errmsg = (
                "Expected header '{}' value '{}', got '{}'"
            ).format(name, expected, actual)
            raise AssertionError(errmsg)

        return

    @staticmethod
    def assert_content_type(
        response: TestResponse,
        expected: str,
    ) -> None:
        """
            Assert that the Content-Type header matches the expected value.

            :param response: The test response to check.
            :param expected: The expected Content-Type value.

            :raises AssertionError: If the Content-Type header is missing
                or does not match.
        """
        actual = response.get_header("Content-Type")

        if actual is None:
            errmsg = (
                "Expected Content-Type '{}', "
                "but Content-Type header was not found"
            ).format(expected)
            raise AssertionError(errmsg)

        if actual != expected:
            errmsg = (
                "Expected Content-Type '{}', got '{}'"
            ).format(expected, actual)
            raise AssertionError(errmsg)

        return

    @staticmethod
    def assert_redirect(
        response: TestResponse,
        expected_location: str,
        status: int = 302,
    ) -> None:
        """
            Assert that the response is a redirect to the expected location.

            Checks both the status code and the Location header value.

            :param response: The test response to check.
            :param expected_location: The expected Location header value.
            :param status: The expected redirect status code (default 302).

            :raises AssertionError: If the status code or Location header
                does not match.
        """
        actual_status = response.status_code

        if actual_status != status:
            errmsg = (
                "Expected redirect status {}, got {}"
            ).format(status, actual_status)
            raise AssertionError(errmsg)

        actual_location = response.get_header("Location")

        if actual_location is None:
            errmsg = (
                "Expected Location header '{}', "
                "but Location header was not found"
            ).format(expected_location)
            raise AssertionError(errmsg)

        if actual_location != expected_location:
            errmsg = (
                "Expected Location '{}', got '{}'"
            ).format(expected_location, actual_location)
            raise AssertionError(errmsg)

        return


# =============================================================================
# Partial Match Helper
# =============================================================================

def _check_partial_match(expected: Any, actual: Any, path: str) -> None:
    """
        Recursively check that all keys in *expected* exist in *actual*
        with matching values. Extra keys in *actual* are allowed.

        :param expected: The expected value or structure.
        :param actual: The actual value or structure.
        :param path: The JSON path string for error messages.

        :raises AssertionError: If a mismatch is found.
    """
    if isinstance(expected, dict):
        if not isinstance(actual, dict):
            errmsg = (
                "At {}: Expected a dict, got {}"
            ).format(path, type(actual).__name__)
            raise AssertionError(errmsg)

        for key in expected:
            if key not in actual:
                errmsg = (
                    "At {}: Expected key '{}' not found in response. "
                    "Available keys: {}"
                ).format(path, key, list(actual.keys()))
                raise AssertionError(errmsg)

            child_path = "{}.{}".format(path, key)
            _check_partial_match(expected[key], actual[key], path=child_path)

    elif isinstance(expected, list):
        if not isinstance(actual, list):
            errmsg = (
                "At {}: Expected a list, got {}"
            ).format(path, type(actual).__name__)
            raise AssertionError(errmsg)

        if len(actual) != len(expected):
            errmsg = (
                "At {}: Expected list length {}, got {}"
            ).format(path, len(expected), len(actual))
            raise AssertionError(errmsg)

        for idx in range(len(expected)):
            child_path = "{}[{}]".format(path, idx)
            _check_partial_match(expected[idx], actual[idx], path=child_path)

    else:
        if actual != expected:
            errmsg = (
                "At {}: Expected {!r}, got {!r}"
            ).format(path, expected, actual)
            raise AssertionError(errmsg)

    return
