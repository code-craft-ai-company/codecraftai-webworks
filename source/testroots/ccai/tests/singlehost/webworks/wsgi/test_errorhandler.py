"""
    Tests for the ErrorHandler class.
    
    This module contains unit tests and property-based tests for the WSGI
    error handler functionality.
    
    **Feature: wsgi-layer, Property 7: Error Response Correctness**
    **Validates: Requirements 8.1, 8.2, 8.3, 8.4, 8.5, 8.8**
"""

import logging
import random
import string
from typing import Any, Dict

from ccai.webworks.wsgi.errorhandler import ErrorHandler
from ccai.webworks.wsgi.response import Response
from ccai.webworks.wsgi.constants import HTTP_STATUS_PHRASES
from ccai.webworks.wsgi.exceptions import (
    HTTPException,
    RequestEntityTooLarge,
    BadRequestBody,
    RequestParseError,
    RequestTimeout,
)


# =============================================================================
# Test Helpers and Generators
# =============================================================================

def generate_random_string(min_length: int = 1, max_length: int = 50) -> str:
    """
        Generate a random alphanumeric string.
    """
    length = random.randint(min_length, max_length)
    chars = string.ascii_letters + string.digits
    rtnval = "".join(random.choice(chars) for _ in range(length))
    return rtnval


def generate_random_environ() -> Dict[str, Any]:
    """
        Generate a random WSGI environ dictionary.
    """
    methods = ["GET", "POST", "PUT", "DELETE", "PATCH"]
    paths = ["/", "/api", "/api/users", "/api/items/123", "/health"]
    
    environ: Dict[str, Any] = {
        "REQUEST_METHOD": random.choice(methods),
        "PATH_INFO": random.choice(paths),
        "QUERY_STRING": "",
        "SERVER_NAME": "localhost",
        "SERVER_PORT": "8000",
        "wsgi.url_scheme": "http",
    }
    
    # Optionally add query string
    if random.random() < 0.3:
        environ["QUERY_STRING"] = f"param={generate_random_string(3, 10)}"
    
    return environ


def generate_random_http_exception() -> HTTPException:
    """
        Generate a random HTTPException.
    """
    # Common HTTP error status codes
    status_codes = [400, 401, 403, 404, 405, 408, 409, 413, 415, 422, 429, 500, 502, 503]
    status_code = random.choice(status_codes)
    message = f"Error message: {generate_random_string(10, 50)}"
    
    rtnval = HTTPException(status_code, message)
    return rtnval


def generate_random_specific_http_exception() -> HTTPException:
    """
        Generate a random specific HTTPException subclass.
    """
    choice = random.randint(0, 3)
    
    if choice == 0:
        max_size = random.randint(1000, 10000)
        actual_size = max_size + random.randint(1, 5000)
        rtnval = RequestEntityTooLarge(max_size, actual_size)
    elif choice == 1:
        detail = f"Invalid field: {generate_random_string(5, 20)}"
        rtnval = BadRequestBody(detail)
    elif choice == 2:
        detail = f"Parse error: {generate_random_string(5, 20)}"
        rtnval = RequestParseError(detail)
    else:
        timeout = random.randint(10, 120)
        rtnval = RequestTimeout(timeout)
    
    return rtnval


def generate_random_unhandled_exception() -> Exception:
    """
        Generate a random unhandled exception (not HTTPException).
    """
    exception_types = [
        ValueError,
        TypeError,
        KeyError,
        RuntimeError,
        AttributeError,
    ]
    
    exc_type = random.choice(exception_types)
    message = f"Unhandled error: {generate_random_string(10, 50)}"
    
    rtnval = exc_type(message)
    return rtnval


# =============================================================================
# Unit Tests for ErrorHandler
# =============================================================================

def test_error_handler_default_values():
    """
        Test that ErrorHandler has correct default values.
    """
    handler = ErrorHandler()
    
    if handler.debug is not False:
        errmsg = f"Expected debug=False, got {handler.debug}"
        raise AssertionError(errmsg)
    
    if handler.logger is None:
        errmsg = "Expected logger to be set"
        raise AssertionError(errmsg)
    
    return


def test_error_handler_with_debug_mode():
    """
        Test that ErrorHandler respects debug mode setting.
    """
    handler = ErrorHandler(debug=True)
    
    if handler.debug is not True:
        errmsg = f"Expected debug=True, got {handler.debug}"
        raise AssertionError(errmsg)
    
    return


def test_error_handler_with_custom_logger():
    """
        Test that ErrorHandler uses custom logger.
    """
    custom_logger = logging.getLogger("custom_test_logger")
    handler = ErrorHandler(logger=custom_logger)
    
    if handler.logger is not custom_logger:
        errmsg = "Expected custom logger to be used"
        raise AssertionError(errmsg)
    
    return


def test_handle_http_exception_returns_correct_status():
    """
        Test that handle_http_exception returns correct status code.
    """
    handler = ErrorHandler()
    exc = HTTPException(404, "Not Found")
    
    response = handler.handle_http_exception(exc)
    
    if response.status_code != 404:
        errmsg = f"Expected status_code 404, got {response.status_code}"
        raise AssertionError(errmsg)
    
    return


def test_handle_http_exception_includes_message():
    """
        Test that handle_http_exception includes error message in body.
    """
    handler = ErrorHandler()
    exc = HTTPException(400, "Bad Request: missing field")
    
    response = handler.handle_http_exception(exc)
    
    body_text = response.body.decode("utf-8")
    if "Bad Request: missing field" not in body_text:
        errmsg = f"Expected message in body, got: {body_text}"
        raise AssertionError(errmsg)
    
    return


def test_handle_unhandled_exception_returns_500():
    """
        Test that handle_unhandled_exception returns 500 status.
    """
    handler = ErrorHandler()
    exc = ValueError("Something went wrong")
    environ = {"REQUEST_METHOD": "GET", "PATH_INFO": "/test"}
    
    response = handler.handle_unhandled_exception(exc, environ)
    
    if response.status_code != 500:
        errmsg = f"Expected status_code 500, got {response.status_code}"
        raise AssertionError(errmsg)
    
    return


def test_handle_dispatches_to_http_exception_handler():
    """
        Test that handle() dispatches HTTPException to handle_http_exception.
    """
    handler = ErrorHandler()
    exc = HTTPException(403, "Forbidden")
    environ = {"REQUEST_METHOD": "GET", "PATH_INFO": "/test"}
    
    response = handler.handle(exc, environ)
    
    if response.status_code != 403:
        errmsg = f"Expected status_code 403, got {response.status_code}"
        raise AssertionError(errmsg)
    
    return


def test_handle_dispatches_unhandled_to_500():
    """
        Test that handle() dispatches unhandled exceptions to 500 handler.
    """
    handler = ErrorHandler()
    exc = RuntimeError("Unexpected error")
    environ = {"REQUEST_METHOD": "POST", "PATH_INFO": "/api"}
    
    response = handler.handle(exc, environ)
    
    if response.status_code != 500:
        errmsg = f"Expected status_code 500, got {response.status_code}"
        raise AssertionError(errmsg)
    
    return


def test_format_error_body_production_mode():
    """
        Test that format_error_body hides stack trace in production mode.
    """
    handler = ErrorHandler(debug=False)
    
    try:
        raise ValueError("Test error")
    except ValueError as exc:
        body = handler.format_error_body(500, "Internal Server Error", exc)
    
    body_text = body.decode("utf-8")
    
    # Should not contain stack trace markers
    if "Traceback" in body_text:
        errmsg = "Expected no traceback in production mode"
        raise AssertionError(errmsg)
    
    if "Stack Trace" in body_text:
        errmsg = "Expected no stack trace header in production mode"
        raise AssertionError(errmsg)
    
    return


def test_format_error_body_debug_mode():
    """
        Test that format_error_body includes stack trace in debug mode.
    """
    handler = ErrorHandler(debug=True)
    
    try:
        raise ValueError("Test error for debug")
    except ValueError as exc:
        body = handler.format_error_body(500, "Internal Server Error", exc)
    
    body_text = body.decode("utf-8")
    
    # Should contain stack trace
    if "Stack Trace" not in body_text:
        errmsg = "Expected stack trace header in debug mode"
        raise AssertionError(errmsg)
    
    if "ValueError" not in body_text:
        errmsg = "Expected exception type in debug mode"
        raise AssertionError(errmsg)
    
    if "Test error for debug" not in body_text:
        errmsg = "Expected exception message in debug mode"
        raise AssertionError(errmsg)
    
    return


def test_register_handler_for_custom_exception():
    """
        Test that register_handler registers custom exception handlers.
    """
    handler = ErrorHandler()
    
    def custom_handler(exc: Exception) -> Response:
        return Response(status_code=418, body=b"I'm a teapot")
    
    handler.register_handler(ValueError, custom_handler)
    
    if not handler.has_custom_handler(ValueError):
        errmsg = "Expected custom handler to be registered"
        raise AssertionError(errmsg)
    
    return


def test_custom_handler_takes_precedence():
    """
        Test that custom handlers take precedence over default handling.
    """
    handler = ErrorHandler()
    
    def custom_handler(exc: Exception) -> Response:
        return Response(status_code=418, body=b"Custom handled")
    
    handler.register_handler(ValueError, custom_handler)
    
    exc = ValueError("Test error")
    environ = {"REQUEST_METHOD": "GET", "PATH_INFO": "/test"}
    
    response = handler.handle(exc, environ)
    
    if response.status_code != 418:
        errmsg = f"Expected status_code 418, got {response.status_code}"
        raise AssertionError(errmsg)
    
    if response.body != b"Custom handled":
        errmsg = f"Expected custom body, got {response.body}"
        raise AssertionError(errmsg)
    
    return


def test_custom_handler_for_http_exception_subclass():
    """
        Test that custom handlers work for HTTPException subclasses.
    """
    handler = ErrorHandler()
    
    def custom_handler(exc: Exception) -> Response:
        return Response(status_code=413, body=b"Custom 413 response")
    
    handler.register_handler(RequestEntityTooLarge, custom_handler)
    
    exc = RequestEntityTooLarge(1000, 2000)
    environ = {"REQUEST_METHOD": "POST", "PATH_INFO": "/upload"}
    
    response = handler.handle(exc, environ)
    
    if response.status_code != 413:
        errmsg = f"Expected status_code 413, got {response.status_code}"
        raise AssertionError(errmsg)
    
    if response.body != b"Custom 413 response":
        errmsg = f"Expected custom body, got {response.body}"
        raise AssertionError(errmsg)
    
    return


def test_unregister_handler():
    """
        Test that unregister_handler removes custom handlers.
    """
    handler = ErrorHandler()
    
    def custom_handler(exc: Exception) -> Response:
        return Response(status_code=418, body=b"Custom")
    
    handler.register_handler(ValueError, custom_handler)
    
    result = handler.unregister_handler(ValueError)
    
    if result is not True:
        errmsg = "Expected unregister to return True"
        raise AssertionError(errmsg)
    
    if handler.has_custom_handler(ValueError):
        errmsg = "Expected custom handler to be removed"
        raise AssertionError(errmsg)
    
    return


def test_unregister_nonexistent_handler():
    """
        Test that unregister_handler returns False for nonexistent handlers.
    """
    handler = ErrorHandler()
    
    result = handler.unregister_handler(ValueError)
    
    if result is not False:
        errmsg = "Expected unregister to return False for nonexistent handler"
        raise AssertionError(errmsg)
    
    return


def test_response_content_type_is_text_plain():
    """
        Test that error responses have text/plain content type.
    """
    handler = ErrorHandler()
    exc = HTTPException(404, "Not Found")
    
    response = handler.handle_http_exception(exc)
    
    expected_content_type = "text/plain; charset=utf-8"
    if response.content_type != expected_content_type:
        errmsg = f"Expected content_type '{expected_content_type}', got '{response.content_type}'"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Property-Based Tests for ErrorHandler
# =============================================================================

def test_property_error_response_correctness():
    """
        Property test: Error Response Correctness
        
        For any HTTPException, the ErrorHandler SHALL return a Response with
        the same status code as the exception. For any unhandled exception,
        the ErrorHandler SHALL return a Response with status code 500.
        In debug mode, stack traces SHALL be included. In production mode,
        internal details SHALL be hidden.
        
        **Feature: wsgi-layer, Property 7: Error Response Correctness**
        **Validates: Requirements 8.1, 8.2, 8.3, 8.4, 8.5, 8.8**
    """
    num_iterations = 100
    
    for iteration in range(num_iterations):
        # Test both debug and production modes
        debug_mode = random.choice([True, False])
        handler = ErrorHandler(debug=debug_mode)
        environ = generate_random_environ()
        
        # Randomly choose exception type
        exc_type_choice = random.randint(0, 2)
        
        if exc_type_choice == 0:
            # Test generic HTTPException
            exc = generate_random_http_exception()
            expected_status = exc.status_code
        elif exc_type_choice == 1:
            # Test specific HTTPException subclass
            exc = generate_random_specific_http_exception()
            expected_status = exc.status_code
        else:
            # Test unhandled exception
            exc = generate_random_unhandled_exception()
            expected_status = 500
        
        # Handle the exception
        response = handler.handle(exc, environ)
        
        # Property 1: Response is a Response object
        if not isinstance(response, Response):
            errmsg = f"Iteration {iteration}: Expected Response object, got {type(response)}"
            raise AssertionError(errmsg)
        
        # Property 2: Status code matches expected (Requirement 8.1, 8.2)
        if response.status_code != expected_status:
            errmsg = f"Iteration {iteration}: Expected status {expected_status}, got {response.status_code}"
            raise AssertionError(errmsg)
        
        # Property 3: Response body is bytes
        if not isinstance(response.body, bytes):
            errmsg = f"Iteration {iteration}: Expected body to be bytes, got {type(response.body)}"
            raise AssertionError(errmsg)
        
        # Property 4: Response has content type
        if response.content_type is None:
            errmsg = f"Iteration {iteration}: Expected content_type to be set"
            raise AssertionError(errmsg)
        
        # Property 5: Body contains status code
        body_text = response.body.decode("utf-8")
        if str(expected_status) not in body_text:
            errmsg = f"Iteration {iteration}: Expected status code {expected_status} in body"
            raise AssertionError(errmsg)
        
        # Property 6: Debug mode includes stack trace for exceptions with traceback
        if debug_mode and exc.__traceback__ is not None:
            if "Stack Trace" not in body_text:
                errmsg = f"Iteration {iteration}: Expected stack trace in debug mode"
                raise AssertionError(errmsg)
        
        # Property 7: Production mode hides stack trace (Requirement 8.4)
        if not debug_mode:
            if "Traceback" in body_text:
                errmsg = f"Iteration {iteration}: Expected no traceback in production mode"
                raise AssertionError(errmsg)
    
    return


def test_property_custom_handler_precedence():
    """
        Property test: Custom Handler Precedence
        
        For any exception type with a registered custom handler, the custom
        handler SHALL be invoked instead of the default handling.
        
        **Feature: wsgi-layer, Property 7: Error Response Correctness**
        **Validates: Requirements 8.8**
    """
    num_iterations = 100
    
    for iteration in range(num_iterations):
        handler = ErrorHandler()
        environ = generate_random_environ()
        
        # Generate a random custom status code
        custom_status = random.randint(400, 599)
        custom_body = f"Custom response {iteration}".encode("utf-8")
        
        def make_custom_handler(status: int, body: bytes):
            def custom_handler(exc: Exception) -> Response:
                return Response(status_code=status, body=body)
            return custom_handler
        
        # Register custom handler for ValueError
        handler.register_handler(ValueError, make_custom_handler(custom_status, custom_body))
        
        # Create a ValueError exception
        exc = ValueError(f"Test error {iteration}")
        
        # Handle the exception
        response = handler.handle(exc, environ)
        
        # Property 1: Custom handler status code is used
        if response.status_code != custom_status:
            errmsg = f"Iteration {iteration}: Expected custom status {custom_status}, got {response.status_code}"
            raise AssertionError(errmsg)
        
        # Property 2: Custom handler body is used
        if response.body != custom_body:
            errmsg = f"Iteration {iteration}: Expected custom body"
            raise AssertionError(errmsg)
    
    return


def test_property_http_exception_subclass_handling():
    """
        Property test: HTTPException Subclass Handling
        
        For any HTTPException subclass, the ErrorHandler SHALL return a
        Response with the status code from the exception.
        
        **Feature: wsgi-layer, Property 7: Error Response Correctness**
        **Validates: Requirements 8.1**
    """
    num_iterations = 100
    
    for iteration in range(num_iterations):
        handler = ErrorHandler()
        environ = generate_random_environ()
        
        # Generate a specific HTTPException subclass
        exc = generate_random_specific_http_exception()
        expected_status = exc.status_code
        
        # Handle the exception
        response = handler.handle(exc, environ)
        
        # Property 1: Status code matches exception status code
        if response.status_code != expected_status:
            errmsg = f"Iteration {iteration}: Expected status {expected_status}, got {response.status_code}"
            raise AssertionError(errmsg)
        
        # Property 2: Body contains the exception message
        body_text = response.body.decode("utf-8")
        if exc.message not in body_text:
            errmsg = f"Iteration {iteration}: Expected exception message in body"
            raise AssertionError(errmsg)
    
    return
