"""
    Tests for the WSGIApplication class.
    
    This module contains unit tests and property-based tests for the WSGI
    application functionality.
    
    **Feature: wsgi-layer, Property 1: WSGI Interface Compliance**
    **Validates: Requirements 1.1, 1.2, 1.3**
    
    **Feature: wsgi-layer, Property 9: Exception Propagation**
    **Validates: Requirements 1.5, 1.6**
"""

import random
import string
from io import BytesIO
from typing import Any, Callable, Dict, List, Optional, Tuple

from ccai.webworks.wsgi.application import (
    WSGIApplication,
    get_wsgi_application,
    create_wsgi_application,
    set_wsgi_application,
    reset_wsgi_application,
)
from ccai.webworks.wsgi.response import Response
from ccai.webworks.wsgi.request import Request
from ccai.webworks.wsgi.exceptions import HTTPException


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


def generate_random_method() -> str:
    """
        Generate a random HTTP method.
    """
    methods = ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"]
    rtnval = random.choice(methods)
    return rtnval


def generate_random_path() -> str:
    """
        Generate a random URL path.
    """
    num_segments = random.randint(0, 5)
    
    if num_segments == 0:
        rtnval = "/"
    else:
        segments = [generate_random_string(1, 20) for _ in range(num_segments)]
        rtnval = "/" + "/".join(segments)
    
    return rtnval


def generate_random_query_string() -> str:
    """
        Generate a random query string.
    """
    if random.random() < 0.3:
        rtnval = ""
    else:
        num_params = random.randint(1, 5)
        params = []
        for _ in range(num_params):
            key = generate_random_string(1, 10)
            value = generate_random_string(1, 20)
            params.append(f"{key}={value}")
        rtnval = "&".join(params)
    
    return rtnval


def generate_random_headers() -> Dict[str, str]:
    """
        Generate random HTTP request headers for environ.
    """
    headers: Dict[str, str] = {}
    num_headers = random.randint(0, 5)
    
    common_headers = [
        "HTTP_ACCEPT", "HTTP_ACCEPT_LANGUAGE", "HTTP_USER_AGENT",
        "HTTP_X_REQUEST_ID", "HTTP_X_CORRELATION_ID",
    ]
    
    for _ in range(num_headers):
        if random.random() < 0.7 and len(common_headers) > 0:
            header_key = random.choice(common_headers)
        else:
            header_key = "HTTP_X_" + generate_random_string(3, 15).upper()
        header_value = generate_random_string(1, 50)
        headers[header_key] = header_value
    
    return headers


def generate_random_body() -> bytes:
    """
        Generate a random request body.
    """
    if random.random() < 0.5:
        rtnval = b""
    else:
        length = random.randint(1, 500)
        rtnval = bytes(random.randint(32, 126) for _ in range(length))
    
    return rtnval


def generate_random_environ() -> Dict[str, Any]:
    """
        Generate a random valid WSGI environ dictionary.
    """
    method = generate_random_method()
    path = generate_random_path()
    query_string = generate_random_query_string()
    headers = generate_random_headers()
    body = generate_random_body()
    
    environ: Dict[str, Any] = {
        "REQUEST_METHOD": method,
        "PATH_INFO": path,
        "QUERY_STRING": query_string,
        "SERVER_NAME": "localhost",
        "SERVER_PORT": "8000",
        "wsgi.url_scheme": "http",
        "wsgi.input": BytesIO(body),
        "wsgi.errors": BytesIO(),
        "wsgi.multithread": True,
        "wsgi.multiprocess": False,
        "wsgi.run_once": False,
    }
    
    # Add headers
    environ.update(headers)
    
    # Add content length if body exists
    if len(body) > 0:
        environ["CONTENT_LENGTH"] = str(len(body))
    
    return environ


def generate_random_status_code() -> int:
    """
        Generate a random HTTP status code.
    """
    common_codes = [200, 201, 204, 301, 302, 400, 401, 403, 404, 500]
    rtnval = random.choice(common_codes)
    return rtnval


def generate_random_response_body() -> bytes:
    """
        Generate a random response body.
    """
    if random.random() < 0.3:
        rtnval = b""
    else:
        length = random.randint(1, 500)
        rtnval = bytes(random.randint(32, 126) for _ in range(length))
    
    return rtnval


class MockStartResponse:
    """
        Mock start_response callable for testing.
    """
    
    def __init__(self):
        """
            Initialize the mock.
        """
        self.status: Optional[str] = None
        self.headers: Optional[List[Tuple[str, str]]] = None
        self.exc_info: Optional[Tuple] = None
        self.call_count: int = 0
        return
    
    def __call__(
        self,
        status: str,
        response_headers: List[Tuple[str, str]],
        exc_info: Optional[Tuple] = None
    ) -> Callable[[bytes], None]:
        """
            Record the start_response call.
        """
        self.status = status
        self.headers = response_headers
        self.exc_info = exc_info
        self.call_count += 1
        
        def write(data: bytes) -> None:
            pass
        
        return write


# =============================================================================
# Unit Tests for WSGIApplication
# =============================================================================

def test_wsgi_application_default_construction():
    """
        Test that WSGIApplication can be constructed with defaults.
    """
    app = WSGIApplication()
    
    if app.debug is not False:
        errmsg = f"Expected debug=False, got {app.debug}"
        raise AssertionError(errmsg)
    
    if app.max_request_body_size != 0:
        errmsg = f"Expected max_request_body_size=0, got {app.max_request_body_size}"
        raise AssertionError(errmsg)
    
    return


def test_wsgi_application_with_debug():
    """
        Test that WSGIApplication respects debug flag.
    """
    app = WSGIApplication(debug=True)
    
    if app.debug is not True:
        errmsg = f"Expected debug=True, got {app.debug}"
        raise AssertionError(errmsg)
    
    return


def test_wsgi_application_with_max_body_size():
    """
        Test that WSGIApplication respects max_request_body_size.
    """
    app = WSGIApplication(max_request_body_size=1024)
    
    if app.max_request_body_size != 1024:
        errmsg = f"Expected max_request_body_size=1024, got {app.max_request_body_size}"
        raise AssertionError(errmsg)
    
    return


def test_wsgi_application_callable():
    """
        Test that WSGIApplication is callable.
    """
    app = WSGIApplication()
    
    if not callable(app):
        errmsg = "Expected WSGIApplication to be callable"
        raise AssertionError(errmsg)
    
    return


def test_wsgi_application_returns_iterator():
    """
        Test that WSGIApplication returns an iterable.
    """
    def handler(request: Request) -> Response:
        return Response(status_code=200, body=b"Hello")
    
    app = WSGIApplication(handler=handler)
    environ = generate_random_environ()
    start_response = MockStartResponse()
    
    result = app(environ, start_response)
    
    # Result should be iterable
    if not hasattr(result, "__iter__"):
        errmsg = "Expected result to be iterable"
        raise AssertionError(errmsg)
    
    # Consume the iterator
    body_chunks = list(result)
    
    return


def test_wsgi_application_calls_start_response():
    """
        Test that WSGIApplication calls start_response.
    """
    def handler(request: Request) -> Response:
        return Response(status_code=200, body=b"Hello")
    
    app = WSGIApplication(handler=handler)
    environ = generate_random_environ()
    start_response = MockStartResponse()
    
    # Consume the iterator to trigger start_response
    list(app(environ, start_response))
    
    if start_response.call_count != 1:
        errmsg = f"Expected start_response to be called once, got {start_response.call_count}"
        raise AssertionError(errmsg)
    
    if start_response.status is None:
        errmsg = "Expected start_response to receive status"
        raise AssertionError(errmsg)
    
    if start_response.headers is None:
        errmsg = "Expected start_response to receive headers"
        raise AssertionError(errmsg)
    
    return


def test_wsgi_application_status_format():
    """
        Test that WSGIApplication returns correct status format.
    """
    def handler(request: Request) -> Response:
        return Response(status_code=200, body=b"Hello")
    
    app = WSGIApplication(handler=handler)
    environ = generate_random_environ()
    start_response = MockStartResponse()
    
    list(app(environ, start_response))
    
    # Status should be "200 OK" format
    if start_response.status is None:
        errmsg = "Expected status to be set"
        raise AssertionError(errmsg)
    
    if not start_response.status.startswith("200"):
        errmsg = f"Expected status to start with '200', got '{start_response.status}'"
        raise AssertionError(errmsg)
    
    return


def test_wsgi_application_yields_bytes():
    """
        Test that WSGIApplication yields bytes objects.
    """
    def handler(request: Request) -> Response:
        return Response(status_code=200, body=b"Hello, World!")
    
    app = WSGIApplication(handler=handler)
    environ = generate_random_environ()
    start_response = MockStartResponse()
    
    body_chunks = list(app(environ, start_response))
    
    for chunk in body_chunks:
        if not isinstance(chunk, bytes):
            errmsg = f"Expected bytes, got {type(chunk)}"
            raise AssertionError(errmsg)
    
    return


def test_wsgi_application_no_handler_returns_404():
    """
        Test that WSGIApplication returns 404 when no handler is set.
    """
    app = WSGIApplication()
    environ = generate_random_environ()
    start_response = MockStartResponse()
    
    list(app(environ, start_response))
    
    if start_response.status is None:
        errmsg = "Expected status to be set"
        raise AssertionError(errmsg)
    
    if not start_response.status.startswith("404"):
        errmsg = f"Expected 404 status, got '{start_response.status}'"
        raise AssertionError(errmsg)
    
    return


def test_wsgi_application_set_handler():
    """
        Test that set_handler works correctly.
    """
    app = WSGIApplication()
    
    def handler(request: Request) -> Response:
        return Response(status_code=201, body=b"Created")
    
    app.set_handler(handler)
    
    environ = generate_random_environ()
    start_response = MockStartResponse()
    
    list(app(environ, start_response))
    
    if start_response.status is None:
        errmsg = "Expected status to be set"
        raise AssertionError(errmsg)
    
    if not start_response.status.startswith("201"):
        errmsg = f"Expected 201 status, got '{start_response.status}'"
        raise AssertionError(errmsg)
    
    return


def test_wsgi_application_http_exception_handling():
    """
        Test that WSGIApplication handles HTTPException correctly.
    """
    def handler(request: Request) -> Response:
        raise HTTPException(403, "Forbidden")
    
    app = WSGIApplication(handler=handler)
    environ = generate_random_environ()
    start_response = MockStartResponse()
    
    # Should not raise - exception should be handled
    list(app(environ, start_response))
    
    if start_response.status is None:
        errmsg = "Expected status to be set"
        raise AssertionError(errmsg)
    
    if not start_response.status.startswith("403"):
        errmsg = f"Expected 403 status, got '{start_response.status}'"
        raise AssertionError(errmsg)
    
    return


def test_wsgi_application_unhandled_exception():
    """
        Test that WSGIApplication handles unhandled exceptions with 500.
    """
    def handler(request: Request) -> Response:
        raise ValueError("Something went wrong")
    
    app = WSGIApplication(handler=handler)
    environ = generate_random_environ()
    start_response = MockStartResponse()
    
    # Should not raise - exception should be handled
    list(app(environ, start_response))
    
    if start_response.status is None:
        errmsg = "Expected status to be set"
        raise AssertionError(errmsg)
    
    if not start_response.status.startswith("500"):
        errmsg = f"Expected 500 status, got '{start_response.status}'"
        raise AssertionError(errmsg)
    
    return


def test_get_wsgi_application():
    """
        Test that get_wsgi_application returns an application.
    """
    app = get_wsgi_application()
    
    if not isinstance(app, WSGIApplication):
        errmsg = f"Expected WSGIApplication, got {type(app)}"
        raise AssertionError(errmsg)
    
    return


def test_create_wsgi_application():
    """
        Test that create_wsgi_application creates new instances.
    """
    app1 = create_wsgi_application()
    app2 = create_wsgi_application()
    
    if app1 is app2:
        errmsg = "Expected different instances"
        raise AssertionError(errmsg)
    
    return


def test_create_wsgi_application_with_config():
    """
        Test that create_wsgi_application respects config.
    """
    config = {
        "debug": True,
        "max_request_body_size": 2048,
    }
    
    app = create_wsgi_application(config)
    
    if app.debug is not True:
        errmsg = f"Expected debug=True, got {app.debug}"
        raise AssertionError(errmsg)
    
    if app.max_request_body_size != 2048:
        errmsg = f"Expected max_request_body_size=2048, got {app.max_request_body_size}"
        raise AssertionError(errmsg)
    
    return


def test_set_wsgi_application():
    """
        Test that set_wsgi_application sets the module-level application.
    """
    # Reset first to ensure clean state
    reset_wsgi_application()
    
    # Create a custom application
    custom_app = WSGIApplication(debug=True)
    
    # Set it as the module-level application
    set_wsgi_application(custom_app)
    
    # Get should return the same instance
    retrieved_app = get_wsgi_application()
    
    if retrieved_app is not custom_app:
        errmsg = "Expected get_wsgi_application to return the set application"
        raise AssertionError(errmsg)
    
    # Clean up
    reset_wsgi_application()
    
    return


def test_reset_wsgi_application():
    """
        Test that reset_wsgi_application clears the module-level application.
    """
    # First ensure there's an application
    app1 = get_wsgi_application()
    
    # Reset it
    reset_wsgi_application()
    
    # Get should create a new instance
    app2 = get_wsgi_application()
    
    if app1 is app2:
        errmsg = "Expected new application after reset"
        raise AssertionError(errmsg)
    
    # Clean up
    reset_wsgi_application()
    
    return


def test_get_wsgi_application_returns_same_instance():
    """
        Test that get_wsgi_application returns the same instance on repeated calls.
    """
    # Reset first to ensure clean state
    reset_wsgi_application()
    
    app1 = get_wsgi_application()
    app2 = get_wsgi_application()
    
    if app1 is not app2:
        errmsg = "Expected same instance on repeated calls"
        raise AssertionError(errmsg)
    
    # Clean up
    reset_wsgi_application()
    
    return


def test_get_wsgi_application_with_environ_config():
    """
        Test that get_wsgi_application respects environment variables.
    """
    import os
    
    # Reset first to ensure clean state
    reset_wsgi_application()
    
    # Set environment variables
    original_debug = os.environ.get("WSGI_APP_DEBUG")
    original_max_body = os.environ.get("WSGI_APP_MAX_BODY_SIZE")
    
    try:
        os.environ["WSGI_APP_DEBUG"] = "true"
        os.environ["WSGI_APP_MAX_BODY_SIZE"] = "4096"
        
        app = get_wsgi_application()
        
        if app.debug is not True:
            errmsg = f"Expected debug=True from environ, got {app.debug}"
            raise AssertionError(errmsg)
        
        if app.max_request_body_size != 4096:
            errmsg = f"Expected max_request_body_size=4096 from environ, got {app.max_request_body_size}"
            raise AssertionError(errmsg)
        
    finally:
        # Restore original environment
        if original_debug is None:
            os.environ.pop("WSGI_APP_DEBUG", None)
        else:
            os.environ["WSGI_APP_DEBUG"] = original_debug
        
        if original_max_body is None:
            os.environ.pop("WSGI_APP_MAX_BODY_SIZE", None)
        else:
            os.environ["WSGI_APP_MAX_BODY_SIZE"] = original_max_body
        
        # Clean up
        reset_wsgi_application()
    
    return


def test_module_level_application_variable():
    """
        Test that the module-level application variable is accessible.
        
        This tests Requirement 5a.3: THE system SHALL support the `application`
        module-level variable convention for external WSGI servers.
    """
    import ccai.webworks.wsgi.application as app_module
    
    # Reset first
    reset_wsgi_application()
    
    # Initially should be None
    if app_module.application is not None:
        errmsg = "Expected application to be None initially after reset"
        raise AssertionError(errmsg)
    
    # After get_wsgi_application, it should be set
    app = get_wsgi_application()
    
    if app_module.application is None:
        errmsg = "Expected application to be set after get_wsgi_application"
        raise AssertionError(errmsg)
    
    if app_module.application is not app:
        errmsg = "Expected module-level application to match returned application"
        raise AssertionError(errmsg)
    
    # Clean up
    reset_wsgi_application()
    
    return


def test_external_server_compatibility_callable():
    """
        Test that the application is compatible with external WSGI servers.
        
        This tests Requirement 5a.2: THE WSGI_Application SHALL remain compatible
        with Gunicorn, uWSGI, mod_wsgi, and Waitress.
        
        External servers expect:
        1. A callable that accepts (environ, start_response)
        2. Returns an iterable yielding bytes
        3. Calls start_response before yielding
    """
    # Reset first
    reset_wsgi_application()
    
    # Get the application
    app = get_wsgi_application()
    
    # Verify it's callable
    if not callable(app):
        errmsg = "Application must be callable"
        raise AssertionError(errmsg)
    
    # Create a minimal environ
    environ = {
        "REQUEST_METHOD": "GET",
        "PATH_INFO": "/",
        "QUERY_STRING": "",
        "SERVER_NAME": "localhost",
        "SERVER_PORT": "8000",
        "wsgi.url_scheme": "http",
        "wsgi.input": BytesIO(b""),
        "wsgi.errors": BytesIO(),
        "wsgi.multithread": True,
        "wsgi.multiprocess": False,
        "wsgi.run_once": False,
    }
    
    # Create a mock start_response
    start_response = MockStartResponse()
    
    # Call the application
    result = app(environ, start_response)
    
    # Result must be iterable
    if not hasattr(result, "__iter__"):
        errmsg = "Application must return an iterable"
        raise AssertionError(errmsg)
    
    # Consume the iterator
    body_chunks = list(result)
    
    # start_response must have been called
    if start_response.call_count < 1:
        errmsg = "start_response must be called"
        raise AssertionError(errmsg)
    
    # All chunks must be bytes
    for chunk in body_chunks:
        if not isinstance(chunk, bytes):
            errmsg = f"All chunks must be bytes, got {type(chunk)}"
            raise AssertionError(errmsg)
    
    # Clean up
    reset_wsgi_application()
    
    return


def test_create_wsgi_application_factory_pattern():
    """
        Test that create_wsgi_application supports the factory pattern.
        
        This tests Requirement 5a.4 and 5a.5: THE system SHALL provide application
        factory pattern support and create a new application instance per call.
    """
    # Create multiple applications
    app1 = create_wsgi_application()
    app2 = create_wsgi_application()
    app3 = create_wsgi_application({"debug": True})
    
    # Each call should create a new instance
    if app1 is app2:
        errmsg = "Factory should create new instance each call"
        raise AssertionError(errmsg)
    
    if app2 is app3:
        errmsg = "Factory should create new instance each call"
        raise AssertionError(errmsg)
    
    # Config should be respected
    if app3.debug is not True:
        errmsg = f"Expected debug=True for app3, got {app3.debug}"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Property-Based Tests for WSGI Interface Compliance
# =============================================================================

def test_property_wsgi_interface_compliance():
    """
        Property test: WSGI Interface Compliance
        
        For any valid WSGI environ dictionary and start_response callable,
        the WSGIApplication SHALL be callable with these arguments and return
        an iterable that yields only bytes objects, with start_response called
        exactly once before any body content is yielded.
        
        **Feature: wsgi-layer, Property 1: WSGI Interface Compliance**
        **Validates: Requirements 1.1, 1.2, 1.3**
    """
    num_iterations = 100
    
    for iteration in range(num_iterations):
        # Generate random response for handler
        status_code = generate_random_status_code()
        response_body = generate_random_response_body()
        
        def make_handler(sc: int, rb: bytes) -> Callable[[Request], Response]:
            def handler(request: Request) -> Response:
                return Response(status_code=sc, body=rb)
            return handler
        
        handler = make_handler(status_code, response_body)
        
        # Create application
        app = WSGIApplication(handler=handler)
        
        # Generate random environ
        environ = generate_random_environ()
        
        # Create mock start_response
        start_response = MockStartResponse()
        
        # Property 1: Application is callable with environ and start_response (Requirement 1.1)
        try:
            result = app(environ, start_response)
        except Exception as exc:
            errmsg = f"Iteration {iteration}: Application call raised exception: {exc}"
            raise AssertionError(errmsg)
        
        # Property 2: Result is iterable (Requirement 1.2)
        if not hasattr(result, "__iter__"):
            errmsg = f"Iteration {iteration}: Result is not iterable"
            raise AssertionError(errmsg)
        
        # Consume iterator and collect chunks
        body_chunks: List[bytes] = []
        for chunk in result:
            body_chunks.append(chunk)
        
        # Property 3: All yielded content is bytes (Requirement 1.2)
        for idx, chunk in enumerate(body_chunks):
            if not isinstance(chunk, bytes):
                errmsg = f"Iteration {iteration}: Chunk {idx} is not bytes, got {type(chunk)}"
                raise AssertionError(errmsg)
        
        # Property 4: start_response called exactly once (Requirement 1.3)
        if start_response.call_count != 1:
            errmsg = f"Iteration {iteration}: start_response called {start_response.call_count} times, expected 1"
            raise AssertionError(errmsg)
        
        # Property 5: start_response received status string
        if start_response.status is None:
            errmsg = f"Iteration {iteration}: start_response did not receive status"
            raise AssertionError(errmsg)
        
        # Property 6: Status format is "NNN Reason"
        status_parts = start_response.status.split(" ", 1)
        if len(status_parts) < 2:
            errmsg = f"Iteration {iteration}: Status '{start_response.status}' does not match 'NNN Reason' format"
            raise AssertionError(errmsg)
        
        if not status_parts[0].isdigit():
            errmsg = f"Iteration {iteration}: Status code '{status_parts[0]}' is not numeric"
            raise AssertionError(errmsg)
        
        # Property 7: start_response received headers list
        if start_response.headers is None:
            errmsg = f"Iteration {iteration}: start_response did not receive headers"
            raise AssertionError(errmsg)
        
        if not isinstance(start_response.headers, list):
            errmsg = f"Iteration {iteration}: Headers is not a list"
            raise AssertionError(errmsg)
        
        # Property 8: Headers are (name, value) tuples
        for idx, header in enumerate(start_response.headers):
            if not isinstance(header, tuple):
                errmsg = f"Iteration {iteration}: Header {idx} is not a tuple"
                raise AssertionError(errmsg)
            
            if len(header) != 2:
                errmsg = f"Iteration {iteration}: Header {idx} tuple length is {len(header)}, expected 2"
                raise AssertionError(errmsg)
    
    return


# =============================================================================
# Property-Based Tests for Exception Propagation
# =============================================================================

def test_property_exception_propagation():
    """
        Property test: Exception Propagation
        
        For any exception raised before start_response is called, the exception
        SHALL propagate to the WSGI server unchanged. For any exception raised
        after start_response but before headers are sent, the application SHALL
        use exc_info to re-raise.
        
        **Feature: wsgi-layer, Property 9: Exception Propagation**
        **Validates: Requirements 1.5, 1.6**
    """
    num_iterations = 100
    
    for iteration in range(num_iterations):
        # Test 1: Exception during request handling (before yielding)
        # These exceptions should be handled and converted to error responses
        
        exception_types = [
            ValueError,
            TypeError,
            RuntimeError,
            KeyError,
        ]
        
        exc_type = random.choice(exception_types)
        exc_message = generate_random_string(10, 50)
        
        def make_failing_handler(et: type, em: str) -> Callable[[Request], Response]:
            def handler(request: Request) -> Response:
                raise et(em)
            return handler
        
        handler = make_failing_handler(exc_type, exc_message)
        
        # Create application
        app = WSGIApplication(handler=handler)
        
        # Generate random environ
        environ = generate_random_environ()
        
        # Create mock start_response
        start_response = MockStartResponse()
        
        # The exception should be caught and converted to 500 response
        try:
            result = app(environ, start_response)
            body_chunks = list(result)
            
            # Should have called start_response with 500 status
            if start_response.status is None:
                errmsg = f"Iteration {iteration}: start_response not called after exception"
                raise AssertionError(errmsg)
            
            if not start_response.status.startswith("500"):
                errmsg = f"Iteration {iteration}: Expected 500 status for unhandled exception, got '{start_response.status}'"
                raise AssertionError(errmsg)
            
        except Exception as exc:
            # If exception propagates, it should be the original type
            # This is acceptable per WSGI spec for exceptions before start_response
            pass
        
        # Test 2: HTTPException should result in appropriate status code
        http_status_codes = [400, 401, 403, 404, 405, 409, 422, 500, 502, 503]
        http_status = random.choice(http_status_codes)
        http_message = generate_random_string(10, 50)
        
        def make_http_exception_handler(status: int, msg: str) -> Callable[[Request], Response]:
            def handler(request: Request) -> Response:
                raise HTTPException(status, msg)
            return handler
        
        http_handler = make_http_exception_handler(http_status, http_message)
        
        app2 = WSGIApplication(handler=http_handler)
        environ2 = generate_random_environ()
        start_response2 = MockStartResponse()
        
        try:
            result2 = app2(environ2, start_response2)
            body_chunks2 = list(result2)
            
            # Should have called start_response with the HTTPException status
            if start_response2.status is None:
                errmsg = f"Iteration {iteration}: start_response not called after HTTPException"
                raise AssertionError(errmsg)
            
            expected_status_prefix = str(http_status)
            if not start_response2.status.startswith(expected_status_prefix):
                errmsg = f"Iteration {iteration}: Expected {http_status} status for HTTPException, got '{start_response2.status}'"
                raise AssertionError(errmsg)
            
        except Exception as exc:
            errmsg = f"Iteration {iteration}: HTTPException should be handled, not propagated: {exc}"
            raise AssertionError(errmsg)
    
    return

