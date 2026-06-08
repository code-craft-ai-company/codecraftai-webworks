"""
.. module:: test_errornormalization_properties
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Property-based tests for ErrorNormalizationMiddleware.

.. moduleauthor:: Code Craft AI LLC

This module contains property-based tests for the ErrorNormalizationMiddleware,
validating:
- Property 16: Error normalization produces structured JSON response
- Property 17: Error status code mapping
- Property 18: Traceback inclusion determined by debug mode
- Property 27: Error normalization logs all caught exceptions
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []

import json
import logging

from typing import Callable, Dict

import ccai.testbase as testbase

from ccai.testbase.properties import given
from ccai.testbase.properties import strategies as st

from ccai.webworks.routing.middleware.errornormalization import ErrorNormalizationMiddleware
from ccai.webworks.routing.exceptions import HTTPException
from ccai.webworks.routing.request import Request
from ccai.webworks.routing.response import Response


# =============================================================================
# Test Helpers
# =============================================================================

def _make_request() -> Request:
    """
        Create a minimal request for testing.
    """
    return Request(method="GET", path="/test")


def _make_raising_handler(exc: Exception) -> Callable:
    """
        Create a handler that raises the given exception.
    """
    def handler(request: Request) -> Response:
        raise exc
    return handler


class _CapturingHandler(logging.Handler):
    """
        Logging handler that captures log records for assertion.
    """

    def __init__(self):
        super().__init__()
        self.records = []
        return

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(record)
        return


def _create_capturing_logger(name: str = "test_errornorm") -> tuple:
    """
        Create a logger with a capturing handler.

        :returns: Tuple of (logger, capturing_handler).
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    handler = _CapturingHandler()
    logger.addHandler(handler)
    return logger, handler


# =============================================================================
# Property 16: Error normalization produces structured JSON response
# =============================================================================

@given(
    status_code=st.sampled_from([400, 401, 403, 404, 405, 409, 422, 429, 500, 502, 503]),
    detail=st.text(min_size=1, max_size=50, alphabet="abcdefghijklmnopqrstuvwxyz "),
    constraints={"max_examples": 15}
)
def test_error_normalization_produces_structured_json_for_http_exception(status_code, detail):
    """
        For any HTTPException raised by the handler, the error normalization
        middleware should return a response with a JSON body containing
        'error', 'error_description', and 'status_code' fields.
    """
    middleware = ErrorNormalizationMiddleware()
    request = _make_request()
    handler = _make_raising_handler(HTTPException(status_code, detail))

    response = middleware(request, handler)
    body = json.loads(response.body)

    testbase.assert_true("error" in body,
        f"Response body should contain 'error' field. Body: {body}")

    testbase.assert_true("error_description" in body,
        f"Response body should contain 'error_description' field. Body: {body}")

    testbase.assert_true("status_code" in body,
        f"Response body should contain 'status_code' field. Body: {body}")


@given(
    message=st.text(min_size=1, max_size=50, alphabet="abcdefghijklmnopqrstuvwxyz "),
    constraints={"max_examples": 10}
)
def test_error_normalization_produces_structured_json_for_generic_exception(message):
    """
        For any generic exception raised by the handler, the error normalization
        middleware should return a response with a JSON body containing
        'error', 'error_description', and 'status_code' fields.
    """
    middleware = ErrorNormalizationMiddleware()
    request = _make_request()
    handler = _make_raising_handler(RuntimeError(message))

    response = middleware(request, handler)
    body = json.loads(response.body)

    testbase.assert_true("error" in body,
        f"Response body should contain 'error' field for generic exception. Body: {body}")

    testbase.assert_true("error_description" in body,
        f"Response body should contain 'error_description' field for generic exception. Body: {body}")

    testbase.assert_true("status_code" in body,
        f"Response body should contain 'status_code' field for generic exception. Body: {body}")


# =============================================================================
# Property 17: Error status code mapping
# =============================================================================

@given(
    status_code=st.sampled_from([400, 401, 403, 404, 405, 409, 422, 429, 500, 502, 503]),
    constraints={"max_examples": 15}
)
def test_http_exception_maps_to_its_status_code(status_code):
    """
        For any HTTPException with status code S, the error normalization
        middleware should return a response with status code S.
    """
    middleware = ErrorNormalizationMiddleware()
    request = _make_request()
    handler = _make_raising_handler(HTTPException(status_code, "test detail"))

    response = middleware(request, handler)

    testbase.assert_equal(response.status_code, status_code,
        f"Response status should match HTTPException status_code={status_code}, "
        f"got {response.status_code}.")

    body = json.loads(response.body)
    testbase.assert_equal(body["status_code"], status_code,
        f"Body status_code should match HTTPException status_code={status_code}, "
        f"got {body['status_code']}.")


@given(
    message=st.text(min_size=1, max_size=50, alphabet="abcdefghijklmnopqrstuvwxyz "),
    constraints={"max_examples": 10}
)
def test_generic_exception_maps_to_500(message):
    """
        For any non-HTTPException, the error normalization middleware should
        return a response with status code 500.
    """
    middleware = ErrorNormalizationMiddleware()
    request = _make_request()
    handler = _make_raising_handler(ValueError(message))

    response = middleware(request, handler)

    testbase.assert_equal(response.status_code, 500,
        f"Generic exception should map to 500, got {response.status_code}.")

    body = json.loads(response.body)
    testbase.assert_equal(body["status_code"], 500,
        f"Body status_code should be 500 for generic exception, got {body['status_code']}.")


@given(
    status_code=st.sampled_from([418, 451, 503, 507]),
    error_label=st.text(min_size=1, max_size=20, alphabet="abcdefghijklmnopqrstuvwxyz "),
    constraints={"max_examples": 10}
)
def test_custom_exception_map_overrides_default(status_code, error_label):
    """
        When a custom exception_map is provided, exceptions matching the map
        should use the configured status code and error label.
    """
    exception_map = {RuntimeError: (status_code, error_label)}
    middleware = ErrorNormalizationMiddleware(exception_map=exception_map)
    request = _make_request()
    handler = _make_raising_handler(RuntimeError("custom mapped"))

    response = middleware(request, handler)

    testbase.assert_equal(response.status_code, status_code,
        f"Custom-mapped exception should return status {status_code}, "
        f"got {response.status_code}.")

    body = json.loads(response.body)
    testbase.assert_equal(body["error"], error_label,
        f"Custom-mapped exception error should be '{error_label}', got '{body['error']}'.")


# =============================================================================
# Property 18: Traceback inclusion determined by debug mode
# =============================================================================

@given(
    status_code=st.sampled_from([400, 404, 500, 503]),
    constraints={"max_examples": 10}
)
def test_traceback_included_when_debug_true(status_code):
    """
        For any exception caught by the error normalization middleware,
        the response body should contain a 'traceback' field when debug=True.
    """
    middleware = ErrorNormalizationMiddleware(debug=True)
    request = _make_request()
    handler = _make_raising_handler(HTTPException(status_code, "debug test"))

    response = middleware(request, handler)
    body = json.loads(response.body)

    testbase.assert_true("traceback" in body,
        f"Response body should contain 'traceback' field when debug=True. Body keys: {list(body.keys())}")


@given(
    status_code=st.sampled_from([400, 404, 500, 503]),
    constraints={"max_examples": 10}
)
def test_traceback_excluded_when_debug_false(status_code):
    """
        For any exception caught by the error normalization middleware,
        the response body should NOT contain a 'traceback' field when debug=False.
    """
    middleware = ErrorNormalizationMiddleware(debug=False)
    request = _make_request()
    handler = _make_raising_handler(HTTPException(status_code, "production test"))

    response = middleware(request, handler)
    body = json.loads(response.body)

    testbase.assert_false("traceback" in body,
        f"Response body should NOT contain 'traceback' field when debug=False. Body keys: {list(body.keys())}")


@given(
    debug=st.booleans(),
    message=st.text(min_size=1, max_size=30, alphabet="abcdefghijklmnopqrstuvwxyz"),
    constraints={"max_examples": 10}
)
def test_traceback_presence_matches_debug_flag(debug, message):
    """
        For any exception and any debug setting, the 'traceback' field should
        be present if and only if debug=True.
    """
    middleware = ErrorNormalizationMiddleware(debug=debug)
    request = _make_request()
    handler = _make_raising_handler(RuntimeError(message))

    response = middleware(request, handler)
    body = json.loads(response.body)

    has_traceback = "traceback" in body

    testbase.assert_equal(has_traceback, debug,
        f"Traceback presence ({has_traceback}) should match debug flag ({debug}) "
        f"for exception message='{message}'.")


# =============================================================================
# Property 27: Error normalization logs all caught exceptions
# =============================================================================

@given(
    status_code=st.sampled_from([400, 401, 403, 404, 500, 502, 503]),
    detail=st.text(min_size=1, max_size=30, alphabet="abcdefghijklmnopqrstuvwxyz "),
    constraints={"max_examples": 10}
)
def test_http_exception_is_logged(status_code, detail):
    """
        For any HTTPException caught by the error normalization middleware,
        the configured logger should receive at least one log entry.
    """
    logger, capture = _create_capturing_logger(f"test_log_http_{status_code}")

    try:
        middleware = ErrorNormalizationMiddleware(logger=logger)
        request = _make_request()
        handler = _make_raising_handler(HTTPException(status_code, detail))

        middleware(request, handler)

        testbase.assert_true(len(capture.records) >= 1,
            f"Logger should have at least 1 record for HTTPException(status={status_code}), "
            f"got {len(capture.records)} records.")
    finally:
        logger.removeHandler(capture)


@given(
    message=st.text(min_size=1, max_size=30, alphabet="abcdefghijklmnopqrstuvwxyz "),
    constraints={"max_examples": 10}
)
def test_generic_exception_is_logged(message):
    """
        For any generic exception caught by the error normalization middleware,
        the configured logger should receive at least one log entry.
    """
    logger, capture = _create_capturing_logger("test_log_generic")

    try:
        middleware = ErrorNormalizationMiddleware(logger=logger)
        request = _make_request()
        handler = _make_raising_handler(RuntimeError(message))

        middleware(request, handler)

        testbase.assert_true(len(capture.records) >= 1,
            f"Logger should have at least 1 record for RuntimeError('{message}'), "
            f"got {len(capture.records)} records.")
    finally:
        logger.removeHandler(capture)


if __name__ == "__main__":
    from ccai.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
