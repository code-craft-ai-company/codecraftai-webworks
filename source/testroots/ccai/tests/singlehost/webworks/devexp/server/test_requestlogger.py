"""
    Tests for the RequestLogger middleware.

    This module contains unit tests for the RequestLogger class including
    log formatting, color support, and the callable middleware interface.
"""

import os
import time

from ccai.webworks.devexp.cli.output import (
    ANSI_GREEN,
    ANSI_RED,
    ANSI_YELLOW,
)
from ccai.webworks.devexp.server.requestlogger import (
    RequestLogger,
    _method_color,
    _status_color,
)


# =============================================================================
# Test Helpers
# =============================================================================

class _FakeRequest:
    """
        A minimal fake request object for testing.
    """

    def __init__(self, method: str = "GET", path: str = "/"):
        self.method = method
        self.path = path


class _FakeResponse:
    """
        A minimal fake response object for testing.
    """

    def __init__(self, status_code: int = 200):
        self.status_code = status_code


class _FakeTTYStream:
    """
        A fake stream that reports itself as a TTY.
    """

    def isatty(self) -> bool:
        return True


class _FakeNonTTYStream:
    """
        A fake stream that reports itself as not a TTY.
    """

    def isatty(self) -> bool:
        return False


def _without_no_color_env(func):
    """
        Run *func* with the NO_COLOR environment variable removed.
    """
    original = os.environ.get("NO_COLOR")

    try:
        os.environ.pop("NO_COLOR", None)
        result = func()
    finally:
        if original is None:
            os.environ.pop("NO_COLOR", None)
        else:
            os.environ["NO_COLOR"] = original

    return result


# =============================================================================
# Unit Tests for RequestLogger Construction
# =============================================================================

def test_request_logger_default_format():
    """
        Test that the default format string is used when none is provided.
    """
    rl = RequestLogger()

    expected = RequestLogger.DEFAULT_FORMAT
    if rl.format != expected:
        errmsg = "Expected format '{}', got '{}'".format(expected, rl.format)
        raise AssertionError(errmsg)

    return


def test_request_logger_custom_format():
    """
        Test that a custom format string is stored correctly.
    """
    custom = "%(method)s %(path)s"
    rl = RequestLogger(format=custom)

    if rl.format != custom:
        errmsg = "Expected format '{}', got '{}'".format(custom, rl.format)
        raise AssertionError(errmsg)

    return


def test_request_logger_default_use_colors():
    """
        Test that colors are enabled by default.
    """
    rl = RequestLogger()

    if rl.use_colors is not True:
        errmsg = "Expected use_colors=True, got {}".format(rl.use_colors)
        raise AssertionError(errmsg)

    return


def test_request_logger_colors_disabled():
    """
        Test that colors can be disabled.
    """
    rl = RequestLogger(use_colors=False)

    if rl.use_colors is not False:
        errmsg = "Expected use_colors=False, got {}".format(rl.use_colors)
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for _format_log
# =============================================================================

def test_format_log_without_colors():
    """
        Test that _format_log produces plain text when colors are disabled.
    """
    rl = RequestLogger(use_colors=False)

    result = rl._format_log("GET", "/api/test", 200, 12.5)

    if "GET" not in result:
        errmsg = "Expected 'GET' in log line, got '{}'".format(result)
        raise AssertionError(errmsg)

    if "/api/test" not in result:
        errmsg = "Expected '/api/test' in log line, got '{}'".format(result)
        raise AssertionError(errmsg)

    if "200" not in result:
        errmsg = "Expected '200' in log line, got '{}'".format(result)
        raise AssertionError(errmsg)

    if "12.5" not in result:
        errmsg = "Expected '12.5' in log line, got '{}'".format(result)
        raise AssertionError(errmsg)

    return


def test_format_log_with_colors_on_tty():
    """
        Test that _format_log applies ANSI colors on a TTY stream.
    """
    tty_stream = _FakeTTYStream()
    rl = RequestLogger(use_colors=True, stream=tty_stream)

    def check():
        return rl._format_log("GET", "/", 200, 5.0)

    result = _without_no_color_env(check)

    # GET should be green, 200 should be green
    if ANSI_GREEN not in result:
        errmsg = "Expected ANSI_GREEN in colored log line, got '{}'".format(repr(result))
        raise AssertionError(errmsg)

    return


def test_format_log_500_status_is_red():
    """
        Test that a 500 status code is colored red.
    """
    tty_stream = _FakeTTYStream()
    rl = RequestLogger(use_colors=True, stream=tty_stream)

    def check():
        return rl._format_log("GET", "/error", 500, 100.0)

    result = _without_no_color_env(check)

    if ANSI_RED not in result:
        errmsg = "Expected ANSI_RED for 500 status, got '{}'".format(repr(result))
        raise AssertionError(errmsg)

    return


def test_format_log_404_status_is_yellow():
    """
        Test that a 404 status code is colored yellow.
    """
    tty_stream = _FakeTTYStream()
    rl = RequestLogger(use_colors=True, stream=tty_stream)

    def check():
        return rl._format_log("GET", "/missing", 404, 3.0)

    result = _without_no_color_env(check)

    if ANSI_YELLOW not in result:
        errmsg = "Expected ANSI_YELLOW for 404 status, got '{}'".format(repr(result))
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for Callable Interface
# =============================================================================

def test_request_logger_calls_next_and_returns_response():
    """
        Test that the logger calls call_next and returns its response.
    """
    rl = RequestLogger(use_colors=False)

    request = _FakeRequest("GET", "/test")
    expected_response = _FakeResponse(200)

    called = [False]

    def call_next(req):
        called[0] = True
        return expected_response

    response = rl(request, call_next)

    if called[0] is not True:
        errmsg = "Expected call_next to be called."
        raise AssertionError(errmsg)

    if response is not expected_response:
        errmsg = "Expected the response from call_next to be returned."
        raise AssertionError(errmsg)

    return


def test_request_logger_measures_time():
    """
        Test that the logger measures elapsed time around call_next.
    """
    rl = RequestLogger(use_colors=False)

    request = _FakeRequest("POST", "/slow")

    def slow_handler(req):
        time.sleep(0.01)
        return _FakeResponse(201)

    # Just verify it doesn't raise - timing is logged internally
    response = rl(request, slow_handler)

    if response.status_code != 201:
        errmsg = "Expected status 201, got {}".format(response.status_code)
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for Color Helper Functions
# =============================================================================

def test_status_color_2xx_is_green():
    """
        Test that 2xx status codes map to green.
    """
    color = _status_color(200)

    if color != "green":
        errmsg = "Expected 'green' for 200, got '{}'".format(color)
        raise AssertionError(errmsg)

    return


def test_status_color_3xx_is_cyan():
    """
        Test that 3xx status codes map to cyan.
    """
    color = _status_color(301)

    if color != "cyan":
        errmsg = "Expected 'cyan' for 301, got '{}'".format(color)
        raise AssertionError(errmsg)

    return


def test_status_color_4xx_is_yellow():
    """
        Test that 4xx status codes map to yellow.
    """
    color = _status_color(404)

    if color != "yellow":
        errmsg = "Expected 'yellow' for 404, got '{}'".format(color)
        raise AssertionError(errmsg)

    return


def test_status_color_5xx_is_red():
    """
        Test that 5xx status codes map to red.
    """
    color = _status_color(500)

    if color != "red":
        errmsg = "Expected 'red' for 500, got '{}'".format(color)
        raise AssertionError(errmsg)

    return


def test_method_color_get_is_green():
    """
        Test that GET maps to green.
    """
    color = _method_color("GET")

    if color != "green":
        errmsg = "Expected 'green' for GET, got '{}'".format(color)
        raise AssertionError(errmsg)

    return


def test_method_color_post_is_cyan():
    """
        Test that POST maps to cyan.
    """
    color = _method_color("POST")

    if color != "cyan":
        errmsg = "Expected 'cyan' for POST, got '{}'".format(color)
        raise AssertionError(errmsg)

    return


def test_method_color_delete_is_red():
    """
        Test that DELETE maps to red.
    """
    color = _method_color("DELETE")

    if color != "red":
        errmsg = "Expected 'red' for DELETE, got '{}'".format(color)
        raise AssertionError(errmsg)

    return


def test_method_color_options_is_white():
    """
        Test that OPTIONS maps to white.
    """
    color = _method_color("OPTIONS")

    if color != "white":
        errmsg = "Expected 'white' for OPTIONS, got '{}'".format(color)
        raise AssertionError(errmsg)

    return


# =============================================================================
# Property-Based Tests
# =============================================================================

import random
import string


# Characters for generating random HTTP methods and paths
_METHOD_CHARS = string.ascii_uppercase
_PATH_CHARS = string.ascii_letters + string.digits + "/-_.~"


def _random_method():
    """
        Return a random HTTP method string of 3 to 7 uppercase letters.
    """
    length = random.randint(3, 7)
    method = "".join(random.choice(_METHOD_CHARS) for _ in range(length))
    return method


def _random_path():
    """
        Return a random URL path string starting with '/'.
    """
    length = random.randint(1, 50)
    path = "/" + "".join(random.choice(_PATH_CHARS) for _ in range(length))
    return path


def _random_status_code():
    """
        Return a random HTTP status code between 100 and 599.
    """
    return random.randint(100, 599)


def _random_elapsed_ms():
    """
        Return a random elapsed time in milliseconds as a float.
    """
    return round(random.uniform(0.01, 9999.99), 2)


def test_property_log_format():
    """
        Property 10: Request Log Format

        For any HTTP method, request path, status code, and elapsed time,
        the RequestLogger._format_log output should be a single line
        matching the format "{method} {path} {status_code} {elapsed_ms}ms"
        and should contain all four values.

        **Validates: Requirements 9.1, 9.2**
    """
    # Feature: development-server, Property 10: Request Log Format
    rl = RequestLogger(use_colors=False)

    for iteration in range(100):
        method = _random_method()
        path = _random_path()
        status_code = _random_status_code()
        elapsed_ms = _random_elapsed_ms()

        result = rl._format_log(method, path, status_code, elapsed_ms)

        # Verify single line (no newlines)
        if "\n" in result:
            errmsg = (
                "Iteration {}: Expected single line, got multi-line: '{}'"
                .format(iteration, repr(result))
            )
            raise AssertionError(errmsg)

        # Build the expected format string
        expected = "{} {} {} {}ms".format(method, path, status_code, elapsed_ms)

        if result != expected:
            errmsg = (
                "Iteration {}: Expected '{}', got '{}'"
                .format(iteration, expected, result)
            )
            raise AssertionError(errmsg)

        # Verify all four values are present in the result
        if method not in result:
            errmsg = (
                "Iteration {}: Method '{}' not found in '{}'"
                .format(iteration, method, result)
            )
            raise AssertionError(errmsg)

        if path not in result:
            errmsg = (
                "Iteration {}: Path '{}' not found in '{}'"
                .format(iteration, path, result)
            )
            raise AssertionError(errmsg)

        if str(status_code) not in result:
            errmsg = (
                "Iteration {}: Status code '{}' not found in '{}'"
                .format(iteration, status_code, result)
            )
            raise AssertionError(errmsg)

        if str(elapsed_ms) not in result:
            errmsg = (
                "Iteration {}: Elapsed time '{}' not found in '{}'"
                .format(iteration, elapsed_ms, result)
            )
            raise AssertionError(errmsg)

    return
