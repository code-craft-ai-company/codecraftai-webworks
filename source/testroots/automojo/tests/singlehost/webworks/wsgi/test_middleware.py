"""
    Tests for the WSGIMiddlewareWrapper class.
    
    This module contains unit tests and property-based tests for the WSGI
    middleware wrapping functionality.
    
    **Feature: wsgi-layer, Property 4: Middleware Compatibility**
    **Validates: Requirements 4.1, 4.2, 4.3, 4.5, 4.6, 4.7, 4.8**
"""

import random
import string
from io import BytesIO
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple

from automojo.webworks.wsgi.middleware import WSGIMiddlewareWrapper
from automojo.webworks.wsgi.application import WSGIApplication
from automojo.webworks.wsgi.response import Response
from automojo.webworks.wsgi.request import Request


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


def generate_random_environ() -> Dict[str, Any]:
    """
        Generate a random valid WSGI environ dictionary.
    """
    method = generate_random_method()
    path = generate_random_path()
    
    environ: Dict[str, Any] = {
        "REQUEST_METHOD": method,
        "PATH_INFO": path,
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
    
    return environ


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


def create_simple_app(status_code: int = 200, body: bytes = b"Hello") -> Callable:
    """
        Create a simple WSGI application for testing.
    """
    def app(environ: Dict[str, Any], start_response: Callable) -> Iterable[bytes]:
        status = f"{status_code} OK"
        headers = [("Content-Type", "text/plain")]
        start_response(status, headers)
        return [body]
    
    return app


def create_environ_reading_app(key: str) -> Callable:
    """
        Create a WSGI application that reads a specific environ key.
    """
    def app(environ: Dict[str, Any], start_response: Callable) -> Iterable[bytes]:
        value = environ.get(key, "NOT_FOUND")
        status = "200 OK"
        headers = [("Content-Type", "text/plain")]
        start_response(status, headers)
        return [str(value).encode("utf-8")]
    
    return app


def create_environ_modifying_middleware(key: str, value: str) -> Callable:
    """
        Create a middleware that modifies the environ.
    """
    def middleware_factory(app: Callable) -> Callable:
        def middleware(environ: Dict[str, Any], start_response: Callable) -> Iterable[bytes]:
            environ[key] = value
            return app(environ, start_response)
        return middleware
    
    return middleware_factory


def create_response_modifying_middleware(prefix: bytes) -> Callable:
    """
        Create a middleware that modifies the response body.
    """
    def middleware_factory(app: Callable) -> Callable:
        def middleware(environ: Dict[str, Any], start_response: Callable) -> Iterable[bytes]:
            response_iter = app(environ, start_response)
            
            # Yield prefix first, then original response
            yield prefix
            for chunk in response_iter:
                yield chunk
        
        return middleware
    
    return middleware_factory


def create_short_circuit_middleware(status_code: int, body: bytes) -> Callable:
    """
        Create a middleware that short-circuits without calling the app.
    """
    def middleware_factory(app: Callable) -> Callable:
        def middleware(environ: Dict[str, Any], start_response: Callable) -> Iterable[bytes]:
            # Don't call app - return our own response
            status = f"{status_code} Short-Circuited"
            headers = [("Content-Type", "text/plain")]
            start_response(status, headers)
            return [body]
        
        return middleware
    
    return middleware_factory


def create_order_tracking_middleware(name: str, tracker: List[str]) -> Callable:
    """
        Create a middleware that tracks execution order.
    """
    def middleware_factory(app: Callable) -> Callable:
        def middleware(environ: Dict[str, Any], start_response: Callable) -> Iterable[bytes]:
            # Track request phase
            tracker.append(f"{name}_request")
            
            # Call inner app
            response_iter = app(environ, start_response)
            
            # Consume and re-yield response, tracking response phase
            chunks = list(response_iter)
            tracker.append(f"{name}_response")
            
            for chunk in chunks:
                yield chunk
        
        return middleware
    
    return middleware_factory


# =============================================================================
# Unit Tests for WSGIMiddlewareWrapper
# =============================================================================

def test_wrap_single_middleware():
    """
        Test that wrap() applies a single middleware correctly.
    """
    app = create_simple_app(200, b"Original")
    
    def middleware_factory(inner_app: Callable) -> Callable:
        def middleware(environ: Dict[str, Any], start_response: Callable) -> Iterable[bytes]:
            return inner_app(environ, start_response)
        return middleware
    
    wrapped = WSGIMiddlewareWrapper.wrap(app, middleware_factory)
    
    environ = generate_random_environ()
    start_response = MockStartResponse()
    
    result = list(wrapped(environ, start_response))
    
    if result != [b"Original"]:
        errmsg = f"Expected [b'Original'], got {result}"
        raise AssertionError(errmsg)
    
    return


def test_wrap_multiple_middlewares():
    """
        Test that wrap_multiple() applies multiple middlewares correctly.
    """
    app = create_simple_app(200, b"Original")
    
    middleware1 = create_response_modifying_middleware(b"[M1]")
    middleware2 = create_response_modifying_middleware(b"[M2]")
    
    wrapped = WSGIMiddlewareWrapper.wrap_multiple(app, [middleware1, middleware2])
    
    environ = generate_random_environ()
    start_response = MockStartResponse()
    
    result = list(wrapped(environ, start_response))
    
    # M1 is outermost, so its prefix comes first
    # Then M2's prefix, then original
    expected = [b"[M1]", b"[M2]", b"Original"]
    
    if result != expected:
        errmsg = f"Expected {expected}, got {result}"
        raise AssertionError(errmsg)
    
    return


def test_environ_modification_propagation():
    """
        Test that environ modifications by middleware are visible to the app.
    """
    test_key = "test.middleware.value"
    test_value = "modified_value"
    
    app = create_environ_reading_app(test_key)
    middleware = create_environ_modifying_middleware(test_key, test_value)
    
    wrapped = WSGIMiddlewareWrapper.wrap(app, middleware)
    
    environ = generate_random_environ()
    start_response = MockStartResponse()
    
    result = list(wrapped(environ, start_response))
    
    expected_body = test_value.encode("utf-8")
    
    if result != [expected_body]:
        errmsg = f"Expected [{expected_body}], got {result}"
        raise AssertionError(errmsg)
    
    return


def test_response_modification_propagation():
    """
        Test that response modifications by middleware are returned.
    """
    app = create_simple_app(200, b"Original")
    middleware = create_response_modifying_middleware(b"PREFIX:")
    
    wrapped = WSGIMiddlewareWrapper.wrap(app, middleware)
    
    environ = generate_random_environ()
    start_response = MockStartResponse()
    
    result = list(wrapped(environ, start_response))
    
    expected = [b"PREFIX:", b"Original"]
    
    if result != expected:
        errmsg = f"Expected {expected}, got {result}"
        raise AssertionError(errmsg)
    
    return


def test_middleware_short_circuit():
    """
        Test that middleware can short-circuit without calling the app.
    """
    app_called = [False]
    
    def tracking_app(environ: Dict[str, Any], start_response: Callable) -> Iterable[bytes]:
        app_called[0] = True
        status = "200 OK"
        headers = [("Content-Type", "text/plain")]
        start_response(status, headers)
        return [b"App Response"]
    
    middleware = create_short_circuit_middleware(403, b"Forbidden")
    
    wrapped = WSGIMiddlewareWrapper.wrap(tracking_app, middleware)
    
    environ = generate_random_environ()
    start_response = MockStartResponse()
    
    result = list(wrapped(environ, start_response))
    
    if app_called[0]:
        errmsg = "Expected app to NOT be called when middleware short-circuits"
        raise AssertionError(errmsg)
    
    if result != [b"Forbidden"]:
        errmsg = f"Expected [b'Forbidden'], got {result}"
        raise AssertionError(errmsg)
    
    if not start_response.status.startswith("403"):
        errmsg = f"Expected 403 status, got {start_response.status}"
        raise AssertionError(errmsg)
    
    return


def test_middleware_execution_order():
    """
        Test that middlewares execute in correct order.
    """
    tracker: List[str] = []
    
    def tracking_app(environ: Dict[str, Any], start_response: Callable) -> Iterable[bytes]:
        tracker.append("app")
        status = "200 OK"
        headers = [("Content-Type", "text/plain")]
        start_response(status, headers)
        return [b"Response"]
    
    middleware_a = create_order_tracking_middleware("A", tracker)
    middleware_b = create_order_tracking_middleware("B", tracker)
    middleware_c = create_order_tracking_middleware("C", tracker)
    
    wrapped = WSGIMiddlewareWrapper.wrap_multiple(
        tracking_app,
        [middleware_a, middleware_b, middleware_c]
    )
    
    environ = generate_random_environ()
    start_response = MockStartResponse()
    
    list(wrapped(environ, start_response))
    
    # Expected order:
    # Request: A -> B -> C -> app
    # Response: C -> B -> A
    expected = [
        "A_request", "B_request", "C_request",
        "app",
        "C_response", "B_response", "A_response"
    ]
    
    if tracker != expected:
        errmsg = f"Expected execution order {expected}, got {tracker}"
        raise AssertionError(errmsg)
    
    return


def test_wrap_with_wsgi_application():
    """
        Test that WSGIMiddlewareWrapper works with WSGIApplication.
    """
    def handler(request: Request) -> Response:
        return Response(status_code=200, body=b"Handler Response")
    
    app = WSGIApplication(handler=handler)
    middleware = create_response_modifying_middleware(b"[MW]")
    
    wrapped = WSGIMiddlewareWrapper.wrap(app, middleware)
    
    environ = generate_random_environ()
    start_response = MockStartResponse()
    
    result = list(wrapped(environ, start_response))
    
    # Should have middleware prefix followed by handler response
    if len(result) < 2:
        errmsg = f"Expected at least 2 chunks, got {len(result)}"
        raise AssertionError(errmsg)
    
    if result[0] != b"[MW]":
        errmsg = f"Expected first chunk to be b'[MW]', got {result[0]}"
        raise AssertionError(errmsg)
    
    return


def test_wrap_multiple_empty_list():
    """
        Test that wrap_multiple with empty list returns original app.
    """
    app = create_simple_app(200, b"Original")
    
    wrapped = WSGIMiddlewareWrapper.wrap_multiple(app, [])
    
    environ = generate_random_environ()
    start_response = MockStartResponse()
    
    result = list(wrapped(environ, start_response))
    
    if result != [b"Original"]:
        errmsg = f"Expected [b'Original'], got {result}"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Property-Based Tests for Middleware Compatibility
# =============================================================================

def test_property_middleware_compatibility():
    """
        Property test: Middleware Compatibility
        
        For any WSGI application and any middleware:
        1. The application SHALL be wrappable by standard WSGI middleware (4.1)
        2. Environ modifications by middleware SHALL be visible to the app (4.2, 4.5)
        3. Response modifications by middleware SHALL be returned to server (4.3, 4.6)
        4. Middleware SHALL be able to short-circuit without calling app (4.7)
        5. Middleware execution order SHALL be maintained (4.8)
        
        **Feature: wsgi-layer, Property 4: Middleware Compatibility**
        **Validates: Requirements 4.1, 4.2, 4.3, 4.5, 4.6, 4.7, 4.8**
    """
    num_iterations = 100
    
    for iteration in range(num_iterations):
        # Generate random test data
        test_key = f"test.key.{generate_random_string(5, 10)}"
        test_value = generate_random_string(10, 30)
        response_prefix = generate_random_string(5, 15).encode("utf-8")
        original_body = generate_random_string(10, 50).encode("utf-8")
        
        # Test 1: Application is wrappable (Requirement 4.1)
        app = create_simple_app(200, original_body)
        
        def passthrough_middleware_factory(inner_app: Callable) -> Callable:
            def middleware(environ: Dict[str, Any], start_response: Callable) -> Iterable[bytes]:
                return inner_app(environ, start_response)
            return middleware
        
        try:
            wrapped = WSGIMiddlewareWrapper.wrap(app, passthrough_middleware_factory)
            environ = generate_random_environ()
            start_response = MockStartResponse()
            result = list(wrapped(environ, start_response))
            
            if result != [original_body]:
                errmsg = f"Iteration {iteration}: Passthrough middleware changed response"
                raise AssertionError(errmsg)
        except Exception as exc:
            errmsg = f"Iteration {iteration}: Failed to wrap application: {exc}"
            raise AssertionError(errmsg)
        
        # Test 2: Environ modifications propagate (Requirements 4.2, 4.5)
        app2 = create_environ_reading_app(test_key)
        middleware2 = create_environ_modifying_middleware(test_key, test_value)
        
        wrapped2 = WSGIMiddlewareWrapper.wrap(app2, middleware2)
        environ2 = generate_random_environ()
        start_response2 = MockStartResponse()
        
        result2 = list(wrapped2(environ2, start_response2))
        expected_body2 = test_value.encode("utf-8")
        
        if result2 != [expected_body2]:
            errmsg = f"Iteration {iteration}: Environ modification not propagated. Expected [{expected_body2}], got {result2}"
            raise AssertionError(errmsg)
        
        # Test 3: Response modifications propagate (Requirements 4.3, 4.6)
        app3 = create_simple_app(200, original_body)
        middleware3 = create_response_modifying_middleware(response_prefix)
        
        wrapped3 = WSGIMiddlewareWrapper.wrap(app3, middleware3)
        environ3 = generate_random_environ()
        start_response3 = MockStartResponse()
        
        result3 = list(wrapped3(environ3, start_response3))
        
        if len(result3) < 2:
            errmsg = f"Iteration {iteration}: Response modification not applied. Expected at least 2 chunks, got {len(result3)}"
            raise AssertionError(errmsg)
        
        if result3[0] != response_prefix:
            errmsg = f"Iteration {iteration}: Response prefix not found. Expected {response_prefix}, got {result3[0]}"
            raise AssertionError(errmsg)
        
        if result3[1] != original_body:
            errmsg = f"Iteration {iteration}: Original body not preserved. Expected {original_body}, got {result3[1]}"
            raise AssertionError(errmsg)
        
        # Test 4: Short-circuit support (Requirement 4.7)
        app_called = [False]
        
        def tracking_app(environ: Dict[str, Any], start_response: Callable) -> Iterable[bytes]:
            app_called[0] = True
            status = "200 OK"
            headers = [("Content-Type", "text/plain")]
            start_response(status, headers)
            return [b"Should not see this"]
        
        short_circuit_body = generate_random_string(10, 30).encode("utf-8")
        middleware4 = create_short_circuit_middleware(403, short_circuit_body)
        
        wrapped4 = WSGIMiddlewareWrapper.wrap(tracking_app, middleware4)
        environ4 = generate_random_environ()
        start_response4 = MockStartResponse()
        
        result4 = list(wrapped4(environ4, start_response4))
        
        if app_called[0]:
            errmsg = f"Iteration {iteration}: App was called despite short-circuit middleware"
            raise AssertionError(errmsg)
        
        if result4 != [short_circuit_body]:
            errmsg = f"Iteration {iteration}: Short-circuit response incorrect. Expected [{short_circuit_body}], got {result4}"
            raise AssertionError(errmsg)
        
        # Test 5: Middleware execution order (Requirement 4.8)
        tracker: List[str] = []
        
        def order_tracking_app(environ: Dict[str, Any], start_response: Callable) -> Iterable[bytes]:
            tracker.append("app")
            status = "200 OK"
            headers = [("Content-Type", "text/plain")]
            start_response(status, headers)
            return [b"Response"]
        
        num_middlewares = random.randint(2, 5)
        middlewares = []
        
        for i in range(num_middlewares):
            name = f"M{i}"
            middlewares.append(create_order_tracking_middleware(name, tracker))
        
        wrapped5 = WSGIMiddlewareWrapper.wrap_multiple(order_tracking_app, middlewares)
        environ5 = generate_random_environ()
        start_response5 = MockStartResponse()
        
        tracker.clear()
        list(wrapped5(environ5, start_response5))
        
        # Verify request order: M0 -> M1 -> ... -> Mn -> app
        expected_request_order = [f"M{i}_request" for i in range(num_middlewares)]
        actual_request_order = [t for t in tracker if t.endswith("_request")]
        
        if actual_request_order != expected_request_order:
            errmsg = f"Iteration {iteration}: Request order incorrect. Expected {expected_request_order}, got {actual_request_order}"
            raise AssertionError(errmsg)
        
        # Verify response order: Mn -> ... -> M1 -> M0
        expected_response_order = [f"M{i}_response" for i in range(num_middlewares - 1, -1, -1)]
        actual_response_order = [t for t in tracker if t.endswith("_response")]
        
        if actual_response_order != expected_response_order:
            errmsg = f"Iteration {iteration}: Response order incorrect. Expected {expected_response_order}, got {actual_response_order}"
            raise AssertionError(errmsg)
    
    return

