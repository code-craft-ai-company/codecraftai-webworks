"""
    Tests for the :class:`DebugErrorHandler` and :class:`FrameInfo` classes.

    This module tests debug error page rendering, production error page
    rendering, traceback extraction, local variable formatting, request
    info extraction, custom templates, and the security boundary between
    debug and production modes.
"""

import random
import string

from ccai.webworks.devexp.debug.errorhandler import (
    DebugErrorHandler,
    FrameInfo,
)


# =============================================================================
# Helpers
# =============================================================================

def _make_request(
    method: str = "GET",
    path: str = "/",
    headers: dict = None,
    body: str = "",
) -> dict:
    """
        Create a mock request dictionary.

        :param method: The HTTP method.
        :param path: The request path.
        :param headers: Optional headers dictionary.
        :param body: The request body string.

        :returns: A request dictionary.
    """
    request = {
        "method": method,
        "path": path,
        "headers": headers if headers is not None else {},
        "body": body,
    }

    return request


def _raise_exception(message: str = "test error") -> Exception:
    """
        Create and raise an exception to capture a real traceback.

        :param message: The exception message.

        :returns: The exception with traceback attached.
    """
    try:
        local_var_a = 42
        local_var_b = "hello"
        raise ValueError(message)
    except ValueError as exc:
        return exc


def _raise_nested_exception(message: str = "nested error") -> Exception:
    """
        Create a nested exception with multiple frames.

        :param message: The exception message.

        :returns: The exception with traceback attached.
    """
    try:
        def inner_function():
            inner_local = "inner_value"
            raise RuntimeError(message)

        inner_function()
    except RuntimeError as exc:
        return exc


# =============================================================================
# FrameInfo Tests
# =============================================================================

def test_frame_info_construction():
    """
        Test that FrameInfo stores all provided attributes correctly.
    """
    frame = FrameInfo(
        filename="/path/to/file.py",
        lineno=42,
        function="test_func",
        code_context=["line1\n", "line2\n", "line3\n"],
        highlight_line=1,
        locals={"x": "10", "y": "'hello'"},
    )

    if frame.filename != "/path/to/file.py":
        errmsg = "Expected filename '/path/to/file.py', got '{}'".format(frame.filename)
        raise AssertionError(errmsg)

    if frame.lineno != 42:
        errmsg = "Expected lineno 42, got {}".format(frame.lineno)
        raise AssertionError(errmsg)

    if frame.function != "test_func":
        errmsg = "Expected function 'test_func', got '{}'".format(frame.function)
        raise AssertionError(errmsg)

    if len(frame.code_context) != 3:
        errmsg = "Expected 3 code context lines, got {}".format(len(frame.code_context))
        raise AssertionError(errmsg)

    if frame.highlight_line != 1:
        errmsg = "Expected highlight_line 1, got {}".format(frame.highlight_line)
        raise AssertionError(errmsg)

    if len(frame.locals) != 2:
        errmsg = "Expected 2 local variables, got {}".format(len(frame.locals))
        raise AssertionError(errmsg)

    return


def test_frame_info_defaults():
    """
        Test that FrameInfo uses sensible defaults for optional parameters.
    """
    frame = FrameInfo(
        filename="test.py",
        lineno=1,
        function="func",
    )

    if len(frame.code_context) != 0:
        errmsg = "Expected empty code_context, got {}".format(frame.code_context)
        raise AssertionError(errmsg)

    if frame.highlight_line != 0:
        errmsg = "Expected highlight_line 0, got {}".format(frame.highlight_line)
        raise AssertionError(errmsg)

    if len(frame.locals) != 0:
        errmsg = "Expected empty locals, got {}".format(frame.locals)
        raise AssertionError(errmsg)

    return


# =============================================================================
# DebugErrorHandler Construction Tests
# =============================================================================

def test_handler_default_construction():
    """
        Test that DebugErrorHandler defaults to production mode.
    """
    handler = DebugErrorHandler()

    if handler.debug is not False:
        errmsg = "Expected debug=False, got {}".format(handler.debug)
        raise AssertionError(errmsg)

    if handler.interactive is not False:
        errmsg = "Expected interactive=False, got {}".format(handler.interactive)
        raise AssertionError(errmsg)

    if handler.pin is not None:
        errmsg = "Expected pin=None, got {}".format(handler.pin)
        raise AssertionError(errmsg)

    if handler.template_path is not None:
        errmsg = "Expected template_path=None, got {}".format(handler.template_path)
        raise AssertionError(errmsg)

    return


def test_handler_debug_mode_construction():
    """
        Test that DebugErrorHandler can be constructed in debug mode.
    """
    handler = DebugErrorHandler(debug=True, interactive=True, pin="1234")

    if handler.debug is not True:
        errmsg = "Expected debug=True, got {}".format(handler.debug)
        raise AssertionError(errmsg)

    if handler.interactive is not True:
        errmsg = "Expected interactive=True, got {}".format(handler.interactive)
        raise AssertionError(errmsg)

    if handler.pin != "1234":
        errmsg = "Expected pin='1234', got '{}'".format(handler.pin)
        raise AssertionError(errmsg)

    return


# =============================================================================
# Debug Mode Tests
# =============================================================================

def test_debug_mode_returns_detailed_page():
    """
        Test that debug mode returns a page with exception details.
    """
    handler = DebugErrorHandler(debug=True)
    request = _make_request(method="POST", path="/api/test")
    exception = _raise_exception("something went wrong")

    response = handler.handle_exception(request, exception)

    if response["status_code"] != 500:
        errmsg = "Expected status 500, got {}".format(response["status_code"])
        raise AssertionError(errmsg)

    body = response["body"]

    if "ValueError" not in body:
        errmsg = "Expected 'ValueError' in debug page body"
        raise AssertionError(errmsg)

    if "something went wrong" not in body:
        errmsg = "Expected exception message in debug page body"
        raise AssertionError(errmsg)

    if "Traceback" not in body:
        errmsg = "Expected 'Traceback' section in debug page body"
        raise AssertionError(errmsg)

    return


def test_debug_mode_shows_local_variables():
    """
        Test that debug mode page includes local variable information.
    """
    handler = DebugErrorHandler(debug=True)
    request = _make_request()
    exception = _raise_exception("var test")

    response = handler.handle_exception(request, exception)
    body = response["body"]

    if "Local Variables" not in body:
        errmsg = "Expected 'Local Variables' section in debug page"
        raise AssertionError(errmsg)

    return


def test_debug_mode_shows_request_info():
    """
        Test that debug mode page includes request information.
    """
    handler = DebugErrorHandler(debug=True)
    request = _make_request(
        method="PUT",
        path="/api/items/5",
        headers={"Content-Type": "application/json"},
    )
    exception = _raise_exception("request info test")

    response = handler.handle_exception(request, exception)
    body = response["body"]

    if "Request Information" not in body:
        errmsg = "Expected 'Request Information' section in debug page"
        raise AssertionError(errmsg)

    if "PUT" not in body:
        errmsg = "Expected request method 'PUT' in debug page"
        raise AssertionError(errmsg)

    if "/api/items/5" not in body:
        errmsg = "Expected request path in debug page"
        raise AssertionError(errmsg)

    return


def test_debug_mode_shows_source_context():
    """
        Test that debug mode page includes source code context with
        line highlighting.
    """
    handler = DebugErrorHandler(debug=True)
    request = _make_request()
    exception = _raise_exception("source context test")

    response = handler.handle_exception(request, exception)
    body = response["body"]

    # The page should contain source code in a pre block
    if '<pre class="source">' not in body:
        errmsg = "Expected source code block in debug page"
        raise AssertionError(errmsg)

    # Should have a highlighted line
    if 'class="line highlight"' not in body:
        errmsg = "Expected highlighted error line in debug page"
        raise AssertionError(errmsg)

    return


def test_debug_mode_html_escapes_exception():
    """
        Test that exception messages with HTML characters are escaped.
    """
    handler = DebugErrorHandler(debug=True)
    request = _make_request()
    exception = _raise_exception("<script>alert('xss')</script>")

    response = handler.handle_exception(request, exception)
    body = response["body"]

    if "<script>" in body:
        errmsg = "Expected HTML-escaped exception message, found raw <script> tag"
        raise AssertionError(errmsg)

    if "&lt;script&gt;" not in body:
        errmsg = "Expected escaped script tag in body"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Production Mode Tests
# =============================================================================

def test_production_mode_hides_details():
    """
        Test that production mode does not expose internal details.
    """
    handler = DebugErrorHandler(debug=False)
    request = _make_request(method="GET", path="/secret/path")
    exception = _raise_exception("internal secret error")

    response = handler.handle_exception(request, exception)
    body = response["body"]

    if "internal secret error" in body:
        errmsg = "Production page should not contain exception message"
        raise AssertionError(errmsg)

    if "ValueError" in body:
        errmsg = "Production page should not contain exception type"
        raise AssertionError(errmsg)

    if "Traceback" in body:
        errmsg = "Production page should not contain traceback"
        raise AssertionError(errmsg)

    if "Local Variables" in body:
        errmsg = "Production page should not contain local variables"
        raise AssertionError(errmsg)

    return


def test_production_mode_includes_error_id():
    """
        Test that production mode includes an error reference ID.
    """
    handler = DebugErrorHandler(debug=False)
    request = _make_request()
    exception = _raise_exception("error id test")

    response = handler.handle_exception(request, exception)
    body = response["body"]

    if "Error Reference:" not in body:
        errmsg = "Expected 'Error Reference:' in production page"
        raise AssertionError(errmsg)

    return


def test_production_mode_user_friendly_message():
    """
        Test that production mode shows a user-friendly message.
    """
    handler = DebugErrorHandler(debug=False)
    request = _make_request()
    exception = _raise_exception("hidden error")

    response = handler.handle_exception(request, exception)
    body = response["body"]

    if "Internal Server Error" not in body:
        errmsg = "Expected 'Internal Server Error' title in production page"
        raise AssertionError(errmsg)

    return


def test_production_mode_custom_status_codes():
    """
        Test that production mode uses appropriate messages for
        different status codes.
    """
    handler = DebugErrorHandler(debug=False)
    request = _make_request()
    exception = _raise_exception("not found")

    response = handler.handle_exception(
        request, exception, status_code=404,
    )
    body = response["body"]

    if "Not Found" not in body:
        errmsg = "Expected 'Not Found' title for 404 status"
        raise AssertionError(errmsg)

    return


def test_production_mode_no_file_paths():
    """
        Test that production mode does not expose internal file paths.
    """
    handler = DebugErrorHandler(debug=False)
    request = _make_request()
    exception = _raise_exception("path leak test")

    response = handler.handle_exception(request, exception)
    body = response["body"]

    # Should not contain any .py file references
    if ".py" in body:
        errmsg = "Production page should not contain file path references"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Custom Template Tests
# =============================================================================

def test_custom_template_registration():
    """
        Test that custom templates can be registered and used for
        specific status codes.
    """
    handler = DebugErrorHandler(debug=False)

    custom_template = (
        "<html><body>"
        "<h1>{error_title}</h1>"
        "<p>{error_message}</p>"
        "<p>Ref: {error_id}</p>"
        "<p>Code: {status_code}</p>"
        "</body></html>"
    )
    handler.register_template(404, custom_template)

    request = _make_request()
    exception = _raise_exception("custom template test")

    response = handler.handle_exception(
        request, exception, status_code=404,
    )
    body = response["body"]

    if "Not Found" not in body:
        errmsg = "Expected 'Not Found' in custom template output"
        raise AssertionError(errmsg)

    if "Ref:" not in body:
        errmsg = "Expected 'Ref:' in custom template output"
        raise AssertionError(errmsg)

    return


def test_custom_template_does_not_leak_details():
    """
        Test that custom templates in production mode do not expose
        internal details.
    """
    handler = DebugErrorHandler(debug=False)

    custom_template = (
        "<html><body>"
        "<h1>{error_title}</h1>"
        "<p>{error_message}</p>"
        "</body></html>"
    )
    handler.register_template(500, custom_template)

    request = _make_request()
    exception = _raise_exception("secret internal error")

    response = handler.handle_exception(request, exception)
    body = response["body"]

    if "secret internal error" in body:
        errmsg = "Custom template should not contain exception message"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Traceback Extraction Tests
# =============================================================================

def test_extract_traceback_returns_frames():
    """
        Test that traceback extraction returns a non-empty list of frames.
    """
    handler = DebugErrorHandler(debug=True)
    exception = _raise_exception("traceback test")

    frames = handler._extract_traceback(exception)

    if len(frames) == 0:
        errmsg = "Expected at least one frame from traceback extraction"
        raise AssertionError(errmsg)

    return


def test_extract_traceback_frame_has_filename():
    """
        Test that extracted frames have filename information.
    """
    handler = DebugErrorHandler(debug=True)
    exception = _raise_exception("filename test")

    frames = handler._extract_traceback(exception)
    last_frame = frames[-1]

    if last_frame.filename == "":
        errmsg = "Expected non-empty filename in frame"
        raise AssertionError(errmsg)

    return


def test_extract_traceback_nested_exception():
    """
        Test that nested exceptions produce multiple frames.
    """
    handler = DebugErrorHandler(debug=True)
    exception = _raise_nested_exception("nested test")

    frames = handler._extract_traceback(exception)

    if len(frames) < 2:
        errmsg = "Expected at least 2 frames for nested exception, got {}".format(
            len(frames),
        )
        raise AssertionError(errmsg)

    return


# =============================================================================
# Property 3: Debug Page Security Boundary
# =============================================================================

_PROPERTY_ITERATIONS = 100


def _random_string(min_len: int = 1, max_len: int = 30) -> str:
    """
        Generate a random alphanumeric string.

        :param min_len: Minimum string length.
        :param max_len: Maximum string length.

        :returns: A random string.
    """
    length = random.randint(min_len, max_len)
    value = "".join(random.choices(string.ascii_letters + string.digits, k=length))

    return value


def _random_path() -> str:
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


def _random_exception_type():
    """
        Generate a random exception with a random message.

        :returns: An exception instance with traceback attached.
    """
    exc_types = [ValueError, RuntimeError, TypeError, KeyError, AttributeError]
    exc_class = random.choice(exc_types)
    message = _random_string(min_len=5, max_len=50)

    try:
        # Create some local variables that should NOT appear in production
        secret_var = _random_string(min_len=10, max_len=30)
        internal_path = "/internal/secret/" + _random_string()
        raise exc_class(message)
    except Exception as exc:
        return exc


def test_property_3_debug_page_security_boundary():
    """
        Property 3: Debug Page Security Boundary

        For any exception in production mode (debug=False), the error
        response SHALL NOT contain stack traces, local variables, or
        internal file paths.

        This test generates random exceptions across 100 iterations
        and verifies that no sensitive information leaks into the
        production error page.

        **Feature: developer-experience, Property 3: Debug Page Security Boundary**
        **Validates: Requirements 8.8, 10.2**
    """
    handler = DebugErrorHandler(debug=False)

    for iteration in range(_PROPERTY_ITERATIONS):
        request = _make_request(
            method=random.choice(["GET", "POST", "PUT", "DELETE", "PATCH"]),
            path=_random_path(),
            headers={"X-Custom": _random_string()},
        )

        exception = _random_exception_type()
        exc_type_name = type(exception).__name__
        exc_message = str(exception)

        status_code = random.choice([400, 403, 404, 500, 502, 503])
        response = handler.handle_exception(
            request, exception, status_code=status_code,
        )

        body = response["body"]

        # The production page must NOT contain the exception message
        if exc_message in body:
            errmsg = (
                "Iteration {}: Production page contains exception message '{}'"
            ).format(iteration, exc_message)
            raise AssertionError(errmsg)

        # The production page must NOT contain the exception type name
        # (unless it happens to match a common word in the template)
        if exc_type_name in body:
            errmsg = (
                "Iteration {}: Production page contains exception type '{}'"
            ).format(iteration, exc_type_name)
            raise AssertionError(errmsg)

        # The production page must NOT contain stack trace markers
        if "Traceback" in body:
            errmsg = (
                "Iteration {}: Production page contains 'Traceback'"
            ).format(iteration)
            raise AssertionError(errmsg)

        # The production page must NOT contain local variable sections
        if "Local Variables" in body:
            errmsg = (
                "Iteration {}: Production page contains 'Local Variables'"
            ).format(iteration)
            raise AssertionError(errmsg)

        # The production page must NOT contain .py file paths
        if ".py" in body:
            errmsg = (
                "Iteration {}: Production page contains '.py' file path reference"
            ).format(iteration)
            raise AssertionError(errmsg)

        # The production page must NOT contain 'File "' traceback markers
        if 'File "' in body:
            errmsg = (
                "Iteration {}: Production page contains traceback file reference"
            ).format(iteration)
            raise AssertionError(errmsg)

        # The production page MUST contain an error reference ID
        if "Error Reference:" not in body:
            errmsg = (
                "Iteration {}: Production page missing error reference ID"
            ).format(iteration)
            raise AssertionError(errmsg)

    return
