"""
.. module:: test_logging_properties
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Property-based tests for RequestLoggingMiddleware.

.. moduleauthor:: Automation Mojo LLC

This module contains property-based tests for the RequestLoggingMiddleware,
validating Property 13 (logging captures method, path, status, and duration),
Property 14 (logging path exclusion skips matching requests), and
Property 15 (logging includes only configured headers).
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []

import logging

from typing import Dict, List

import automojo.testbase as testbase

from automojo.testbase.properties import given
from automojo.testbase.properties import strategies as st

from automojo.webworks.routing.middleware.logging import RequestLoggingMiddleware
from automojo.webworks.routing.request import Request


# =============================================================================
# Test Helpers
# =============================================================================

class MockResponse:
    """
        Minimal Response implementation for property tests.
    """

    def __init__(self, status_code: int = 200, body: bytes = b"", headers: Dict[str, str] = None):
        self._status_code = status_code
        self._body = body
        self._headers = headers if headers is not None else {}
        return

    @property
    def status_code(self) -> int:
        return self._status_code

    @property
    def body(self) -> bytes:
        return self._body

    @property
    def headers(self) -> Dict[str, str]:
        return self._headers

    def set_header(self, name: str, value: str) -> None:
        self._headers[name] = value
        return


class CapturingHandler(logging.Handler):
    """
        A logging handler that captures log records for inspection.
    """

    def __init__(self):
        super().__init__()
        self.records: List[logging.LogRecord] = []
        return

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(record)
        return

    def get_messages(self) -> List[str]:
        return [self.format(r) for r in self.records]

    def clear(self) -> None:
        self.records.clear()
        return


def _make_logger(name: str) -> tuple:
    """
        Create a logger with a capturing handler for test use.

        :returns: Tuple of (logger, handler).
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    # Remove any existing handlers to avoid cross-test pollution
    logger.handlers.clear()
    handler = CapturingHandler()
    logger.addHandler(handler)
    return logger, handler


HTTP_METHODS = ["GET", "POST", "PUT", "DELETE", "PATCH"]

SAMPLE_PATHS = ["/api/users", "/api/orders/123", "/health", "/dashboard"]

STATUS_CODES = [200, 201, 400, 404, 500]


# =============================================================================
# Property 13: Request logging captures method, path, status, and duration
# =============================================================================

@given(
    method=st.sampled_from(HTTP_METHODS),
    path=st.sampled_from(SAMPLE_PATHS),
    status_code=st.sampled_from(STATUS_CODES),
    constraints={"max_examples": 10}
)
def test_logging_captures_method_path_status_and_duration(method, path, status_code):
    """
        For any request processed through the logging middleware whose path
        does not match an excluded pattern, the logger should receive entries
        containing the HTTP method, request path, response status code, and
        a non-negative processing duration.
    """
    logger, handler = _make_logger("test_completeness")

    middleware = RequestLoggingMiddleware(logger=logger)
    request = Request(method=method, path=path)

    def endpoint(req: Request) -> MockResponse:
        return MockResponse(status_code=status_code)

    response = middleware(request, endpoint)

    messages = handler.get_messages()

    testbase.assert_true(len(messages) >= 2,
        f"Expected at least 2 log messages, got {len(messages)} for {method} {path}.")

    request_msg = messages[0]
    response_msg = messages[1]

    testbase.assert_true(method in request_msg,
        f"Request log should contain method '{method}', got: {request_msg}")

    testbase.assert_true(path in request_msg,
        f"Request log should contain path '{path}', got: {request_msg}")

    testbase.assert_true(str(status_code) in response_msg,
        f"Response log should contain status code '{status_code}', got: {response_msg}")

    testbase.assert_true("duration=" in response_msg,
        f"Response log should contain 'duration=', got: {response_msg}")

    # Extract duration and verify non-negative
    duration_part = response_msg.split("duration=")[1]
    duration_str = duration_part.rstrip("s").strip()
    duration_val = float(duration_str)
    testbase.assert_true(duration_val >= 0.0,
        f"Duration should be non-negative, got {duration_val}.")

    testbase.assert_equal(response.status_code, status_code,
        f"Response status code should be {status_code}, got {response.status_code}.")


# =============================================================================
# Property 14: Logging path exclusion skips matching requests
# =============================================================================

EXCLUDE_PATTERNS = ["/health", "/metrics", "/internal/*"]

EXCLUDED_PATHS = ["/health", "/metrics", "/internal/status"]

NON_EXCLUDED_PATHS = ["/api/users", "/dashboard", "/api/orders/123"]


@given(
    path=st.sampled_from(EXCLUDED_PATHS),
    method=st.sampled_from(HTTP_METHODS),
    constraints={"max_examples": 10}
)
def test_logging_path_exclusion_skips_matching_requests(path, method):
    """
        For any request whose path matches a pattern in the exclude list,
        the logging middleware should not produce any log entries.
    """
    logger, handler = _make_logger("test_exclusion")

    middleware = RequestLoggingMiddleware(logger=logger, exclude_paths=EXCLUDE_PATTERNS)
    request = Request(method=method, path=path)

    def endpoint(req: Request) -> MockResponse:
        return MockResponse(status_code=200)

    response = middleware(request, endpoint)

    messages = handler.get_messages()

    testbase.assert_equal(len(messages), 0,
        f"No log messages should be produced for excluded path '{path}', "
        f"but got {len(messages)} messages: {messages}")

    testbase.assert_equal(response.status_code, 200,
        f"Response should still be returned for excluded path '{path}'.")


@given(
    path=st.sampled_from(NON_EXCLUDED_PATHS),
    method=st.sampled_from(HTTP_METHODS),
    constraints={"max_examples": 10}
)
def test_logging_non_excluded_paths_are_logged(path, method):
    """
        For any request whose path does NOT match an exclusion pattern,
        the logging middleware should produce log entries.
    """
    logger, handler = _make_logger("test_non_excluded")

    middleware = RequestLoggingMiddleware(logger=logger, exclude_paths=EXCLUDE_PATTERNS)
    request = Request(method=method, path=path)

    def endpoint(req: Request) -> MockResponse:
        return MockResponse(status_code=200)

    middleware(request, endpoint)

    messages = handler.get_messages()

    testbase.assert_true(len(messages) >= 2,
        f"Log messages should be produced for non-excluded path '{path}', "
        f"but got {len(messages)} messages.")


# =============================================================================
# Property 15: Logging includes only configured headers
# =============================================================================

ALL_HEADERS = {
    "Content-Type": "application/json",
    "Authorization": "Bearer token123",
    "X-Request-Id": "req-abc-123",
    "Accept": "text/html",
    "User-Agent": "TestAgent/1.0",
}

HEADER_SUBSETS = [
    ["Content-Type"],
    ["Authorization", "X-Request-Id"],
    ["Accept", "User-Agent", "Content-Type"],
]


@given(
    include_idx=st.integers(0, 2),
    constraints={"max_examples": 6}
)
def test_logging_includes_only_configured_headers(include_idx):
    """
        For any request with headers and a configured include_headers list,
        the log output should contain only the headers specified in the
        include list and no others.
    """
    include_headers = HEADER_SUBSETS[include_idx]
    excluded_headers = [h for h in ALL_HEADERS if h not in include_headers]

    logger, handler = _make_logger("test_headers")

    middleware = RequestLoggingMiddleware(logger=logger, include_headers=include_headers)
    request = Request(method="GET", path="/api/test", headers=dict(ALL_HEADERS))

    def endpoint(req: Request) -> MockResponse:
        return MockResponse(status_code=200)

    middleware(request, endpoint)

    messages = handler.get_messages()
    request_msg = messages[0]

    for header_name in include_headers:
        header_value = ALL_HEADERS[header_name]
        testbase.assert_true(header_name in request_msg,
            f"Included header '{header_name}' should appear in log, got: {request_msg}")
        testbase.assert_true(header_value in request_msg,
            f"Included header value '{header_value}' should appear in log, got: {request_msg}")

    for header_name in excluded_headers:
        header_value = ALL_HEADERS[header_name]
        testbase.assert_false(header_value in request_msg,
            f"Excluded header value '{header_value}' for '{header_name}' should NOT appear "
            f"in log when include_headers={include_headers}, got: {request_msg}")


@given(
    method=st.sampled_from(HTTP_METHODS),
    constraints={"max_examples": 5}
)
def test_logging_no_headers_when_include_headers_is_none(method):
    """
        When include_headers is None, no header information should appear
        in the request log message.
    """
    logger, handler = _make_logger("test_no_headers")

    middleware = RequestLoggingMiddleware(logger=logger, include_headers=None)
    request = Request(method=method, path="/api/test", headers=dict(ALL_HEADERS))

    def endpoint(req: Request) -> MockResponse:
        return MockResponse(status_code=200)

    middleware(request, endpoint)

    messages = handler.get_messages()
    request_msg = messages[0]

    testbase.assert_false("headers=" in request_msg,
        f"No header info should appear when include_headers is None, got: {request_msg}")


if __name__ == "__main__":
    from automojo.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
