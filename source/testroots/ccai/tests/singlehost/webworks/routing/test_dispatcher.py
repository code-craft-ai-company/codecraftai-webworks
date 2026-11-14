"""
    Tests for the Dispatcher class.
    
    This module tests the Dispatcher class which orchestrates routing
    and middleware execution for incoming HTTP requests.
"""

from ccai.webworks.routing import (
    Dispatcher,
    Router,
    Request,
    Response,
    MiddlewarePipeline,
    HTTPException,
    NotFound,
    BadRequest,
    Unauthorized,
)
from ccai.webworks.endpoints.descriptor import EndpointDescriptor


# ============================================================================
# Test Fixtures
# ============================================================================

def create_test_handler(response_data):
    """
        Create a test handler that returns the given response data.
    """
    def handler(request):
        return response_data
    return handler


def create_response_handler(response):
    """
        Create a test handler that returns a Response object.
    """
    def handler(request):
        return response
    return handler


def create_exception_handler(exception):
    """
        Create a test handler that raises an exception.
    """
    def handler(request):
        raise exception
    return handler


def create_test_descriptor(path, methods, handler):
    """
        Create a test EndpointDescriptor.
    """
    return EndpointDescriptor(
        handler=handler,
        path=path,
        methods=methods,
        module="test_dispatcher",
    )


# ============================================================================
# Task 12.1: Dispatcher Constructor Tests
# ============================================================================

def test_dispatcher_constructor_with_defaults():
    """
        Test Dispatcher constructor with default values.
    """
    router = Router()
    dispatcher = Dispatcher(router)
    
    assert dispatcher.router is router
    assert dispatcher.pipeline is not None
    assert dispatcher.debug is False
    assert dispatcher.error_format == "json"
    return


def test_dispatcher_constructor_with_pipeline():
    """
        Test Dispatcher constructor with custom pipeline.
    """
    router = Router()
    pipeline = MiddlewarePipeline()
    dispatcher = Dispatcher(router, pipeline)
    
    assert dispatcher.router is router
    assert dispatcher.pipeline is pipeline
    return


def test_dispatcher_constructor_with_debug():
    """
        Test Dispatcher constructor with debug mode enabled.
    """
    router = Router()
    dispatcher = Dispatcher(router, debug=True)
    
    assert dispatcher.debug is True
    return


def test_dispatcher_constructor_with_error_format():
    """
        Test Dispatcher constructor with custom error format.
    """
    router = Router()
    dispatcher = Dispatcher(router, error_format="html")
    
    assert dispatcher.error_format == "html"
    return


def test_dispatcher_debug_setter():
    """
        Test Dispatcher debug property setter.
    """
    router = Router()
    dispatcher = Dispatcher(router)
    
    dispatcher.debug = True
    assert dispatcher.debug is True
    
    dispatcher.debug = False
    assert dispatcher.debug is False
    return


def test_dispatcher_error_format_setter():
    """
        Test Dispatcher error_format property setter.
    """
    router = Router()
    dispatcher = Dispatcher(router)
    
    dispatcher.error_format = "html"
    assert dispatcher.error_format == "html"
    
    dispatcher.error_format = "text"
    assert dispatcher.error_format == "text"
    return


def test_dispatcher_repr():
    """
        Test Dispatcher string representation.
    """
    router = Router()
    dispatcher = Dispatcher(router, debug=True, error_format="html")
    
    repr_str = repr(dispatcher)
    assert "Dispatcher" in repr_str
    assert "debug=True" in repr_str
    assert "html" in repr_str
    return


# ============================================================================
# Task 12.2: Dispatcher.dispatch() Tests
# ============================================================================

def test_dispatch_routes_to_handler():
    """
        Test that dispatch routes request to matching handler.
    """
    router = Router()
    
    def test_handler(request):
        return {"message": "success"}
    
    descriptor = create_test_descriptor("/test", ["GET"], test_handler)
    router.add_endpoint(descriptor)
    
    dispatcher = Dispatcher(router)
    request = Request(method="GET", path="/test")
    
    response = dispatcher.dispatch(request)
    
    assert response.status_code == 200
    return


def test_dispatch_populates_path_params():
    """
        Test that dispatch populates request.path_params from RouteMatch.
    """
    router = Router()
    captured_params = {}
    
    def test_handler(request):
        captured_params.update(request.path_params)
        return {"id": request.path_params.get("id")}
    
    descriptor = create_test_descriptor("/users/{id:int}", ["GET"], test_handler)
    router.add_endpoint(descriptor)
    
    dispatcher = Dispatcher(router)
    request = Request(method="GET", path="/users/123")
    
    response = dispatcher.dispatch(request)
    
    assert response.status_code == 200
    assert captured_params.get("id") == 123
    return


def test_dispatch_executes_middleware_pipeline():
    """
        Test that dispatch executes middleware pipeline with handler.
    """
    router = Router()
    pipeline = MiddlewarePipeline()
    
    middleware_called = []
    
    def test_middleware(request, call_next):
        middleware_called.append("before")
        response = call_next(request)
        middleware_called.append("after")
        return response
    
    pipeline.add(test_middleware, name="test")
    
    def test_handler(request):
        middleware_called.append("handler")
        return {"message": "success"}
    
    descriptor = create_test_descriptor("/test", ["GET"], test_handler)
    router.add_endpoint(descriptor)
    
    dispatcher = Dispatcher(router, pipeline)
    request = Request(method="GET", path="/test")
    
    dispatcher.dispatch(request)
    
    assert middleware_called == ["before", "handler", "after"]
    return


def test_dispatch_returns_404_on_no_match():
    """
        Test that dispatch returns 404 when no route matches.
    """
    router = Router()
    dispatcher = Dispatcher(router)
    
    request = Request(method="GET", path="/nonexistent")
    
    response = dispatcher.dispatch(request)
    
    assert response.status_code == 404
    return


def test_dispatch_handler_returns_response():
    """
        Test that dispatch handles handler returning Response object.
    """
    router = Router()
    
    def test_handler(request):
        return Response(status_code=201, body=b"Created")
    
    descriptor = create_test_descriptor("/test", ["GET"], test_handler)
    router.add_endpoint(descriptor)
    
    dispatcher = Dispatcher(router)
    request = Request(method="GET", path="/test")
    
    response = dispatcher.dispatch(request)
    
    assert response.status_code == 201
    assert response.body == b"Created"
    return


def test_dispatch_handler_returns_dict():
    """
        Test that dispatch wraps dict return value in JSONResponse.
    """
    router = Router()
    
    def test_handler(request):
        return {"key": "value"}
    
    descriptor = create_test_descriptor("/test", ["GET"], test_handler)
    router.add_endpoint(descriptor)
    
    dispatcher = Dispatcher(router)
    request = Request(method="GET", path="/test")
    
    response = dispatcher.dispatch(request)
    
    assert response.status_code == 200
    assert b"key" in response.body
    assert b"value" in response.body
    return


# ============================================================================
# Task 12.3: HTTPException Handling Tests
# ============================================================================

def test_dispatch_handles_http_exception_from_handler():
    """
        Test that dispatch converts HTTPException to response.
    """
    router = Router()
    
    def test_handler(request):
        raise NotFound("Resource not found")
    
    descriptor = create_test_descriptor("/test", ["GET"], test_handler)
    router.add_endpoint(descriptor)
    
    dispatcher = Dispatcher(router)
    request = Request(method="GET", path="/test")
    
    response = dispatcher.dispatch(request)
    
    assert response.status_code == 404
    return


def test_dispatch_handles_http_exception_from_middleware():
    """
        Test that dispatch handles HTTPException from middleware.
    """
    router = Router()
    pipeline = MiddlewarePipeline()
    
    def auth_middleware(request, call_next):
        raise Unauthorized("Not authenticated")
    
    pipeline.add(auth_middleware, name="auth")
    
    def test_handler(request):
        return {"message": "success"}
    
    descriptor = create_test_descriptor("/test", ["GET"], test_handler)
    router.add_endpoint(descriptor)
    
    dispatcher = Dispatcher(router, pipeline)
    request = Request(method="GET", path="/test")
    
    response = dispatcher.dispatch(request)
    
    assert response.status_code == 401
    return


def test_dispatch_error_format_json():
    """
        Test that dispatch returns JSON error response.
    """
    router = Router()
    
    def test_handler(request):
        raise BadRequest("Invalid input")
    
    descriptor = create_test_descriptor("/test", ["GET"], test_handler)
    router.add_endpoint(descriptor)
    
    dispatcher = Dispatcher(router, error_format="json")
    request = Request(method="GET", path="/test")
    
    response = dispatcher.dispatch(request)
    
    assert response.status_code == 400
    assert b"Invalid input" in response.body
    assert b"400" in response.body
    return


def test_dispatch_error_format_html():
    """
        Test that dispatch returns HTML error response.
    """
    router = Router()
    
    def test_handler(request):
        raise NotFound("Page not found")
    
    descriptor = create_test_descriptor("/test", ["GET"], test_handler)
    router.add_endpoint(descriptor)
    
    dispatcher = Dispatcher(router, error_format="html")
    request = Request(method="GET", path="/test")
    
    response = dispatcher.dispatch(request)
    
    assert response.status_code == 404
    assert b"<html>" in response.body or b"<!DOCTYPE html>" in response.body
    assert b"Page not found" in response.body
    return


def test_dispatch_error_format_text():
    """
        Test that dispatch returns plain text error response.
    """
    router = Router()
    
    def test_handler(request):
        raise NotFound("Resource missing")
    
    descriptor = create_test_descriptor("/test", ["GET"], test_handler)
    router.add_endpoint(descriptor)
    
    dispatcher = Dispatcher(router, error_format="text")
    request = Request(method="GET", path="/test")
    
    response = dispatcher.dispatch(request)
    
    assert response.status_code == 404
    assert response.body == b"Resource missing"
    return


def test_dispatch_http_exception_with_headers():
    """
        Test that HTTPException headers are included in response.
    """
    router = Router()
    
    def test_handler(request):
        raise HTTPException(
            status_code=429,
            detail="Too many requests",
            headers={"Retry-After": "60"}
        )
    
    descriptor = create_test_descriptor("/test", ["GET"], test_handler)
    router.add_endpoint(descriptor)
    
    dispatcher = Dispatcher(router)
    request = Request(method="GET", path="/test")
    
    response = dispatcher.dispatch(request)
    
    assert response.status_code == 429
    assert response.headers.get("Retry-After") == "60"
    return


# ============================================================================
# Task 12.4: Unhandled Exception Handling Tests
# ============================================================================

def test_dispatch_handles_unhandled_exception():
    """
        Test that dispatch returns 500 for unhandled exceptions.
    """
    router = Router()
    
    def test_handler(request):
        raise ValueError("Something went wrong")
    
    descriptor = create_test_descriptor("/test", ["GET"], test_handler)
    router.add_endpoint(descriptor)
    
    dispatcher = Dispatcher(router)
    request = Request(method="GET", path="/test")
    
    response = dispatcher.dispatch(request)
    
    assert response.status_code == 500
    return


def test_dispatch_hides_details_in_production():
    """
        Test that dispatch hides error details when debug=False.
    """
    router = Router()
    
    def test_handler(request):
        raise ValueError("Secret error message")
    
    descriptor = create_test_descriptor("/test", ["GET"], test_handler)
    router.add_endpoint(descriptor)
    
    dispatcher = Dispatcher(router, debug=False)
    request = Request(method="GET", path="/test")
    
    response = dispatcher.dispatch(request)
    
    assert response.status_code == 500
    # Should not contain the secret error message
    assert b"Secret error message" not in response.body
    # Should contain generic message
    assert b"Internal Server Error" in response.body
    return


def test_dispatch_shows_stack_trace_in_debug():
    """
        Test that dispatch shows stack trace when debug=True.
    """
    router = Router()
    
    def test_handler(request):
        raise ValueError("Debug error message")
    
    descriptor = create_test_descriptor("/test", ["GET"], test_handler)
    router.add_endpoint(descriptor)
    
    dispatcher = Dispatcher(router, debug=True)
    request = Request(method="GET", path="/test")
    
    response = dispatcher.dispatch(request)
    
    assert response.status_code == 500
    # Should contain traceback information
    assert b"Traceback" in response.body or b"ValueError" in response.body
    return


def test_dispatch_unhandled_exception_json_format():
    """
        Test unhandled exception with JSON error format.
    """
    router = Router()
    
    def test_handler(request):
        raise RuntimeError("Runtime error")
    
    descriptor = create_test_descriptor("/test", ["GET"], test_handler)
    router.add_endpoint(descriptor)
    
    dispatcher = Dispatcher(router, error_format="json", debug=False)
    request = Request(method="GET", path="/test")
    
    response = dispatcher.dispatch(request)
    
    assert response.status_code == 500
    assert b"500" in response.body
    return


def test_dispatch_unhandled_exception_html_format():
    """
        Test unhandled exception with HTML error format.
    """
    router = Router()
    
    def test_handler(request):
        raise RuntimeError("Runtime error")
    
    descriptor = create_test_descriptor("/test", ["GET"], test_handler)
    router.add_endpoint(descriptor)
    
    dispatcher = Dispatcher(router, error_format="html", debug=False)
    request = Request(method="GET", path="/test")
    
    response = dispatcher.dispatch(request)
    
    assert response.status_code == 500
    assert b"<html>" in response.body or b"<!DOCTYPE html>" in response.body
    return


def test_dispatch_unhandled_exception_text_format():
    """
        Test unhandled exception with text error format.
    """
    router = Router()
    
    def test_handler(request):
        raise RuntimeError("Runtime error")
    
    descriptor = create_test_descriptor("/test", ["GET"], test_handler)
    router.add_endpoint(descriptor)
    
    dispatcher = Dispatcher(router, error_format="text", debug=False)
    request = Request(method="GET", path="/test")
    
    response = dispatcher.dispatch(request)
    
    assert response.status_code == 500
    assert b"Internal Server Error" in response.body
    return


def test_dispatch_debug_json_includes_exception_info():
    """
        Test that debug mode JSON includes exception type and message.
    """
    router = Router()
    
    def test_handler(request):
        raise ValueError("Test error")
    
    descriptor = create_test_descriptor("/test", ["GET"], test_handler)
    router.add_endpoint(descriptor)
    
    dispatcher = Dispatcher(router, error_format="json", debug=True)
    request = Request(method="GET", path="/test")
    
    response = dispatcher.dispatch(request)
    
    assert response.status_code == 500
    assert b"ValueError" in response.body
    return


# ============================================================================
# Task 12.5: Dispatcher.dispatch_async() Tests
# ============================================================================

import asyncio


def test_dispatch_async_routes_to_handler():
    """
        Test that dispatch_async routes request to matching handler.
    """
    router = Router()
    
    async def test_handler(request):
        return {"message": "async success"}
    
    descriptor = create_test_descriptor("/test", ["GET"], test_handler)
    router.add_endpoint(descriptor)
    
    dispatcher = Dispatcher(router)
    request = Request(method="GET", path="/test")
    
    # Run the async dispatch
    loop = asyncio.new_event_loop()
    try:
        response = loop.run_until_complete(dispatcher.dispatch_async(request))
    finally:
        loop.close()
    
    assert response.status_code == 200
    return


def test_dispatch_async_populates_path_params():
    """
        Test that dispatch_async populates request.path_params.
    """
    router = Router()
    captured_params = {}
    
    async def test_handler(request):
        captured_params.update(request.path_params)
        return {"id": request.path_params.get("id")}
    
    descriptor = create_test_descriptor("/items/{id:int}", ["GET"], test_handler)
    router.add_endpoint(descriptor)
    
    dispatcher = Dispatcher(router)
    request = Request(method="GET", path="/items/456")
    
    loop = asyncio.new_event_loop()
    try:
        response = loop.run_until_complete(dispatcher.dispatch_async(request))
    finally:
        loop.close()
    
    assert response.status_code == 200
    assert captured_params.get("id") == 456
    return


def test_dispatch_async_returns_404_on_no_match():
    """
        Test that dispatch_async returns 404 when no route matches.
    """
    router = Router()
    dispatcher = Dispatcher(router)
    
    request = Request(method="GET", path="/nonexistent")
    
    loop = asyncio.new_event_loop()
    try:
        response = loop.run_until_complete(dispatcher.dispatch_async(request))
    finally:
        loop.close()
    
    assert response.status_code == 404
    return


def test_dispatch_async_handles_http_exception():
    """
        Test that dispatch_async handles HTTPException.
    """
    router = Router()
    
    async def test_handler(request):
        raise NotFound("Async not found")
    
    descriptor = create_test_descriptor("/test", ["GET"], test_handler)
    router.add_endpoint(descriptor)
    
    dispatcher = Dispatcher(router)
    request = Request(method="GET", path="/test")
    
    loop = asyncio.new_event_loop()
    try:
        response = loop.run_until_complete(dispatcher.dispatch_async(request))
    finally:
        loop.close()
    
    assert response.status_code == 404
    return


def test_dispatch_async_handles_unhandled_exception():
    """
        Test that dispatch_async handles unhandled exceptions.
    """
    router = Router()
    
    async def test_handler(request):
        raise ValueError("Async error")
    
    descriptor = create_test_descriptor("/test", ["GET"], test_handler)
    router.add_endpoint(descriptor)
    
    dispatcher = Dispatcher(router, debug=False)
    request = Request(method="GET", path="/test")
    
    loop = asyncio.new_event_loop()
    try:
        response = loop.run_until_complete(dispatcher.dispatch_async(request))
    finally:
        loop.close()
    
    assert response.status_code == 500
    return


def test_dispatch_async_with_sync_handler():
    """
        Test that dispatch_async works with synchronous handlers.
    """
    router = Router()
    
    def test_handler(request):
        return {"message": "sync handler"}
    
    descriptor = create_test_descriptor("/test", ["GET"], test_handler)
    router.add_endpoint(descriptor)
    
    dispatcher = Dispatcher(router)
    request = Request(method="GET", path="/test")
    
    loop = asyncio.new_event_loop()
    try:
        response = loop.run_until_complete(dispatcher.dispatch_async(request))
    finally:
        loop.close()
    
    assert response.status_code == 200
    return


# =============================================================================
# Property Tests
# =============================================================================

import random
import string


def _random_string(length: int = 8) -> str:
    """Generate a random alphanumeric string."""
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))


def _random_path_segment() -> str:
    """Generate a random path segment."""
    return _random_string(random.randint(3, 10))


def _random_static_path(depth: int = None) -> str:
    """Generate a random static path."""
    if depth is None:
        depth = random.randint(1, 4)
    segments = [_random_path_segment() for _ in range(depth)]
    return "/" + "/".join(segments)


def _random_method() -> str:
    """Generate a random HTTP method."""
    return random.choice(["GET", "POST", "PUT", "DELETE", "PATCH"])


def _random_status_code() -> int:
    """Generate a random HTTP error status code."""
    return random.choice([400, 401, 403, 404, 405, 409, 422, 429, 500, 502, 503])


def _random_error_format() -> str:
    """Generate a random error format."""
    return random.choice(["json", "html", "text"])


# -----------------------------------------------------------------------------
# Property 12: Dispatcher Error Handling
# **Validates: Requirements 8.6, 8.7, 9.2, 9.5**
#
# *For any* request that matches no route, the Dispatcher SHALL return a 404
# response. *For any* HTTPException raised by a handler, the Dispatcher SHALL
# return a response with the exception's status_code. *For any* unhandled
# exception, the Dispatcher SHALL return a 500 response.
# -----------------------------------------------------------------------------

def test_property_dispatcher_404_on_no_match():
    """
    Property 12: Dispatcher Error Handling - 404 on No Match
    
    For any request that matches no route, the Dispatcher SHALL return a 404
    response regardless of the error format configuration.
    
    **Feature: router-request-handling, Property 12: Dispatcher Error Handling**
    **Validates: Requirements 8.6, 8.7, 9.2, 9.5**
    """
    # Run 100 iterations
    for _ in range(100):
        router = Router()
        error_format = _random_error_format()
        dispatcher = Dispatcher(router, error_format=error_format)
        
        # Generate a random path that won't match any route
        path = _random_static_path()
        method = _random_method()
        
        request = Request(method=method, path=path)
        response = dispatcher.dispatch(request)
        
        # Property: No match should return 404
        assert response.status_code == 404, \
            f"Expected 404 for unmatched route, got {response.status_code}"
    
    return


def test_property_dispatcher_http_exception_status_code():
    """
    Property 12: Dispatcher Error Handling - HTTPException Status Code
    
    For any HTTPException raised by a handler, the Dispatcher SHALL return a
    response with the exception's status_code.
    
    **Feature: router-request-handling, Property 12: Dispatcher Error Handling**
    **Validates: Requirements 8.6, 8.7, 9.2, 9.5**
    """
    # Run 100 iterations
    for _ in range(100):
        router = Router()
        error_format = _random_error_format()
        dispatcher = Dispatcher(router, error_format=error_format)
        
        # Generate random path and method
        path = _random_static_path()
        method = _random_method()
        
        # Generate random status code for HTTPException
        status_code = _random_status_code()
        detail = f"Error detail {_random_string()}"
        
        # Create handler that raises HTTPException
        def create_exception_handler(sc, dt):
            def handler(request):
                raise HTTPException(sc, dt)
            return handler
        
        handler = create_exception_handler(status_code, detail)
        descriptor = create_test_descriptor(path, [method], handler)
        router.add_endpoint(descriptor)
        
        request = Request(method=method, path=path)
        response = dispatcher.dispatch(request)
        
        # Property: HTTPException status code should be preserved
        assert response.status_code == status_code, \
            f"Expected {status_code} for HTTPException, got {response.status_code}"
    
    return


def test_property_dispatcher_500_on_unhandled_exception():
    """
    Property 12: Dispatcher Error Handling - 500 on Unhandled Exception
    
    For any unhandled exception raised by a handler, the Dispatcher SHALL
    return a 500 response.
    
    **Feature: router-request-handling, Property 12: Dispatcher Error Handling**
    **Validates: Requirements 8.6, 8.7, 9.2, 9.5**
    """
    # Define various exception types to test
    exception_types = [
        ValueError,
        TypeError,
        RuntimeError,
        KeyError,
        IndexError,
        AttributeError,
        ZeroDivisionError,
    ]
    
    # Run 100 iterations
    for _ in range(100):
        router = Router()
        error_format = _random_error_format()
        debug = random.choice([True, False])
        dispatcher = Dispatcher(router, error_format=error_format, debug=debug)
        
        # Generate random path and method
        path = _random_static_path()
        method = _random_method()
        
        # Pick a random exception type
        exc_type = random.choice(exception_types)
        exc_message = f"Error message {_random_string()}"
        
        # Create handler that raises unhandled exception
        def create_exception_handler(et, msg):
            def handler(request):
                raise et(msg)
            return handler
        
        handler = create_exception_handler(exc_type, exc_message)
        descriptor = create_test_descriptor(path, [method], handler)
        router.add_endpoint(descriptor)
        
        request = Request(method=method, path=path)
        response = dispatcher.dispatch(request)
        
        # Property: Unhandled exception should return 500
        assert response.status_code == 500, \
            f"Expected 500 for unhandled {exc_type.__name__}, got {response.status_code}"
    
    return


def test_property_dispatcher_debug_mode_hides_details():
    """
    Property 12: Dispatcher Error Handling - Debug Mode Detail Visibility
    
    For any unhandled exception, when debug=False the response SHALL NOT
    expose internal error details. When debug=True, the response SHALL
    include stack trace information.
    
    **Feature: router-request-handling, Property 12: Dispatcher Error Handling**
    **Validates: Requirements 8.6, 8.7, 9.2, 9.5**
    """
    # Run 100 iterations
    for _ in range(100):
        router_prod = Router()
        router_debug = Router()
        
        error_format = _random_error_format()
        dispatcher_prod = Dispatcher(router_prod, error_format=error_format, debug=False)
        dispatcher_debug = Dispatcher(router_debug, error_format=error_format, debug=True)
        
        # Generate random path and method
        path = _random_static_path()
        method = _random_method()
        
        # Generate a unique secret message that should not appear in production
        secret_message = f"SECRET_{_random_string(16)}"
        
        # Create handler that raises exception with secret message
        def create_exception_handler(msg):
            def handler(request):
                raise ValueError(msg)
            return handler
        
        handler_prod = create_exception_handler(secret_message)
        handler_debug = create_exception_handler(secret_message)
        
        descriptor_prod = create_test_descriptor(path, [method], handler_prod)
        descriptor_debug = create_test_descriptor(path, [method], handler_debug)
        
        router_prod.add_endpoint(descriptor_prod)
        router_debug.add_endpoint(descriptor_debug)
        
        request_prod = Request(method=method, path=path)
        request_debug = Request(method=method, path=path)
        
        response_prod = dispatcher_prod.dispatch(request_prod)
        response_debug = dispatcher_debug.dispatch(request_debug)
        
        # Property: Production mode should NOT expose secret message
        assert secret_message.encode() not in response_prod.body, \
            "Production mode should not expose error details"
        
        # Property: Debug mode should include traceback information
        # (either "Traceback" or the exception type name)
        body_debug = response_debug.body
        has_traceback = b"Traceback" in body_debug or b"ValueError" in body_debug
        assert has_traceback, \
            "Debug mode should include traceback information"
    
    return



# =============================================================================
# Regression: handlers returning TemplateResponse / StreamingTemplateResponse
# =============================================================================
#
# Before the dispatcher accepted these types, handlers that returned a
# rendered template (the canonical webworks pattern for HTML pages)
# silently produced 500s in production. The dispatcher's
# ``handler_wrapper`` did ``isinstance(result, Response)``, which is False
# for ``TemplateResponse`` (a parallel hierarchy with the same duck-typed
# shape but no shared base class). The wrapper then fell through to
# ``JSONResponse(result)``, which raised at JSON serialisation, the
# dispatcher's outer ``except Exception`` swallowed it, and the client
# got "Internal Server Error". The ASGI ``ResponseSender`` already
# duck-types these — only the dispatcher's isinstance check stood in
# the way.


def test_dispatch_handler_returns_template_response():
    """
        Handlers returning :class:`TemplateResponse` flow through the
        dispatcher unchanged (no JSONResponse wrap, no 500).
    """
    from ccai.webworks.templating.response import TemplateResponse

    def template_handler(request):
        return TemplateResponse(
            body="<h1>Hello</h1>",
            status_code=200,
            content_type="text/html; charset=utf-8",
        )

    router = Router()
    descriptor = create_test_descriptor("/page", ["GET"], template_handler)
    router.add_endpoint(descriptor)

    dispatcher = Dispatcher(router)

    request = Request(method="GET", path="/page")
    response = dispatcher.dispatch(request)

    if not isinstance(response, TemplateResponse):
        errmsg = "Expected TemplateResponse to flow through verbatim, got {!r}".format(
            type(response).__name__
        )
        raise AssertionError(errmsg)

    if response.status_code != 200:
        errmsg = "Expected 200, got {}".format(response.status_code)
        raise AssertionError(errmsg)

    if response.body != "<h1>Hello</h1>":
        errmsg = "Expected body to round-trip, got {!r}".format(response.body)
        raise AssertionError(errmsg)

    return


def test_dispatch_handler_returns_streaming_template_response():
    """
        Handlers returning :class:`StreamingTemplateResponse` also flow
        through unchanged.
    """
    from ccai.webworks.templating.response import StreamingTemplateResponse

    def streaming_handler(request):
        def chunks():
            yield "<h1>"
            yield "Hello"
            yield "</h1>"
        return StreamingTemplateResponse(
            body_iterator=chunks(),
            status_code=200,
            content_type="text/html; charset=utf-8",
        )

    router = Router()
    descriptor = create_test_descriptor("/stream", ["GET"], streaming_handler)
    router.add_endpoint(descriptor)

    dispatcher = Dispatcher(router)

    request = Request(method="GET", path="/stream")
    response = dispatcher.dispatch(request)

    if not isinstance(response, StreamingTemplateResponse):
        errmsg = "Expected StreamingTemplateResponse, got {!r}".format(
            type(response).__name__
        )
        raise AssertionError(errmsg)

    if response.status_code != 200:
        errmsg = "Expected 200, got {}".format(response.status_code)
        raise AssertionError(errmsg)

    return


# ============================================================================
# Access policy enforcement
# ============================================================================

import threading

from datetime import datetime, timedelta, timezone

from ccai.webworks.authentication.core import AuthenticationContext, Principal
from ccai.webworks.endpoints.constraints import EndpointConstraints
from ccai.webworks.endpoints.endpoint import Endpoint
from ccai.webworks.routing.middlewarecontext import MiddlewareContext
from ccai.webworks.routing.middlewareregistry import MiddlewareRegistry
from ccai.webworks.routing.middleware.cors import CORSMiddleware
from ccai.webworks.security.accesspolicy import AccessPolicy
from ccai.webworks.security.decorators import require_roles
from ccai.webworks.security.securitycontext import SECURITY_CONTEXT_SCOPE_KEY, SecurityContext


def create_auth_scope(roles=None, permissions=None, expires_at=None):
    """
        Create a request scope carrying an authentication context, the way
        the authentication middleware leaves it.
    """
    principal = Principal(
        identifier="tester",
        roles=set(roles or []),
        permissions=set(permissions or [])
    )
    context = AuthenticationContext(principal=principal, scheme="Test", expires_at=expires_at)
    return {"auth": context}


def create_policy_dispatcher(policy, path="/admin/users", calls=None, **dispatcher_options):
    """
        Create a dispatcher with one GET route protected by the given policy.
        The handler records each call in ``calls``.
    """
    def handler(request):
        if calls is not None:
            calls.append(request.path)
        return {"secret": "data"}

    descriptor = EndpointDescriptor(
        handler=handler,
        module="test",
        path=path,
        methods=["GET"],
        constraints=EndpointConstraints(access_policy=policy),
    )

    router = Router()
    router.add_endpoint(descriptor)

    return Dispatcher(router, **dispatcher_options)


def test_dispatch_refuses_anonymous_request_to_protected_endpoint():
    """
        An endpoint with an access policy answers 401 to a request without
        an authentication context and does not run its handler.
    """
    calls = []
    dispatcher = create_policy_dispatcher(AccessPolicy(roles=["system-admin"]), calls=calls)

    response = dispatcher.dispatch(Request(method="GET", path="/admin/users"))

    assert response.status_code == 401, f"Expected 401, got {response.status_code}"
    assert len(calls) == 0, "The handler must not run for an anonymous request"
    assert "WWW-Authenticate" in response.headers, "A 401 response must carry a challenge"
    return


def test_dispatch_refuses_authenticated_request_without_required_role():
    """
        An authenticated request that lacks the required role is answered 403.
    """
    calls = []
    dispatcher = create_policy_dispatcher(AccessPolicy(roles=["system-admin"]), calls=calls)

    request = Request(method="GET", path="/admin/users", scope=create_auth_scope(roles=["viewer"]))
    response = dispatcher.dispatch(request)

    assert response.status_code == 403, f"Expected 403, got {response.status_code}"
    assert len(calls) == 0, "The handler must not run without the required role"
    return


def test_dispatch_allows_request_that_satisfies_the_policy():
    """
        A request whose authentication context satisfies the policy reaches
        the handler.
    """
    calls = []
    dispatcher = create_policy_dispatcher(AccessPolicy(roles=["system-admin"]), calls=calls)

    request = Request(method="GET", path="/admin/users", scope=create_auth_scope(roles=["system-admin"]))
    response = dispatcher.dispatch(request)

    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    assert calls == ["/admin/users"], f"Expected the handler to run once, got {calls}"
    return


def test_dispatch_async_enforces_the_policy():
    """
        dispatch_async, the path WebApplication serves, enforces the policy too.
    """
    calls = []
    dispatcher = create_policy_dispatcher(AccessPolicy(roles=["system-admin"]), calls=calls)

    anonymous = asyncio.run(dispatcher.dispatch_async(Request(method="GET", path="/admin/users")))
    viewer = asyncio.run(dispatcher.dispatch_async(
        Request(method="GET", path="/admin/users", scope=create_auth_scope(roles=["viewer"]))))
    admin = asyncio.run(dispatcher.dispatch_async(
        Request(method="GET", path="/admin/users", scope=create_auth_scope(roles=["system-admin"]))))

    assert anonymous.status_code == 401, f"Expected 401, got {anonymous.status_code}"
    assert viewer.status_code == 403, f"Expected 403, got {viewer.status_code}"
    assert admin.status_code == 200, f"Expected 200, got {admin.status_code}"
    assert len(calls) == 1, f"Only the admin request may reach the handler, got {calls}"
    return


def test_dispatch_enforces_policy_from_security_decorator():
    """
        A policy attached by @require_roles and recorded by attach_at is
        enforced for the route.
    """
    @Endpoint.attach_at(path="/decorated", methods=["GET"])
    @require_roles("system-admin")
    def decorated(request):
        return {"ok": True}

    descriptor = Endpoint._find_descriptors_for_handler(decorated)[0]

    router = Router()
    router.add_endpoint(descriptor)
    dispatcher = Dispatcher(router)

    anonymous = dispatcher.dispatch(Request(method="GET", path="/decorated"))
    admin = dispatcher.dispatch(
        Request(method="GET", path="/decorated", scope=create_auth_scope(roles=["system-admin"])))

    assert anonymous.status_code == 401, f"Expected 401, got {anonymous.status_code}"
    assert admin.status_code == 200, f"Expected 200, got {admin.status_code}"
    return


def test_dispatch_refuses_expired_authentication_context():
    """
        An expired authentication context authenticates nobody.
    """
    dispatcher = create_policy_dispatcher(AccessPolicy(roles=["system-admin"]))

    expired = datetime.now(timezone.utc) - timedelta(minutes=1)
    scope = create_auth_scope(roles=["system-admin"], expires_at=expired)
    response = dispatcher.dispatch(Request(method="GET", path="/admin/users", scope=scope))

    assert response.status_code == 401, f"Expected 401, got {response.status_code}"
    return


def test_dispatch_requires_scopes_of_the_policy():
    """
        A policy with scopes is satisfied only by a principal holding all of them.
    """
    dispatcher = create_policy_dispatcher(AccessPolicy(scopes=["users:read", "users:write"]))

    partial = dispatcher.dispatch(
        Request(method="GET", path="/admin/users", scope=create_auth_scope(permissions=["users:read"])))
    full = dispatcher.dispatch(
        Request(method="GET", path="/admin/users",
                scope=create_auth_scope(permissions=["users:read", "users:write"])))

    assert partial.status_code == 403, f"Expected 403, got {partial.status_code}"
    assert full.status_code == 200, f"Expected 200, got {full.status_code}"
    return


def test_dispatch_denies_when_policy_can_not_be_evaluated():
    """
        A policy whose check raises grants nothing: the request is refused
        and the handler does not run.
    """
    class BrokenPolicy:
        def check(self, subject):
            raise RuntimeError("policy backend unavailable")

    calls = []
    dispatcher = create_policy_dispatcher(BrokenPolicy(), calls=calls)

    request = Request(method="GET", path="/admin/users", scope=create_auth_scope(roles=["system-admin"]))
    response = dispatcher.dispatch(request)

    assert response.status_code == 403, f"Expected 403, got {response.status_code}"
    assert len(calls) == 0, "The handler must not run when the policy fails to evaluate"
    return


def test_dispatch_enforces_roles_listed_on_constraints():
    """
        Roles listed on the constraints without an AccessPolicy are enforced.
    """
    descriptor = EndpointDescriptor(
        handler=create_test_handler({"ok": True}),
        module="test",
        path="/listed",
        methods=["GET"],
        constraints=EndpointConstraints(roles=["auditor"]),
    )
    router = Router()
    router.add_endpoint(descriptor)
    dispatcher = Dispatcher(router)

    anonymous = dispatcher.dispatch(Request(method="GET", path="/listed"))
    auditor = dispatcher.dispatch(
        Request(method="GET", path="/listed", scope=create_auth_scope(roles=["auditor"])))

    assert anonymous.status_code == 401, f"Expected 401, got {anonymous.status_code}"
    assert auditor.status_code == 200, f"Expected 200, got {auditor.status_code}"
    return


def test_dispatch_leaves_endpoint_without_policy_public():
    """
        An endpoint that declares no policy is served to anonymous requests.
    """
    router = Router()
    router.add_endpoint(create_test_descriptor("/public", ["GET"], create_test_handler({"ok": True})))
    dispatcher = Dispatcher(router)

    response = dispatcher.dispatch(Request(method="GET", path="/public"))

    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    return


def test_dispatch_applies_default_policy_to_endpoint_without_policy():
    """
        With a default policy configured, an endpoint without a policy of
        its own is protected by the default.
    """
    router = Router()
    router.add_endpoint(create_test_descriptor("/implicit", ["GET"], create_test_handler({"ok": True})))
    dispatcher = Dispatcher(router, default_policy=AccessPolicy(require_auth=True))

    anonymous = dispatcher.dispatch(Request(method="GET", path="/implicit"))
    authenticated = dispatcher.dispatch(
        Request(method="GET", path="/implicit", scope=create_auth_scope()))

    assert anonymous.status_code == 401, f"Expected 401, got {anonymous.status_code}"
    assert authenticated.status_code == 200, f"Expected 200, got {authenticated.status_code}"
    return


def test_dispatch_accepts_security_context_published_on_scope():
    """
        The SecurityContext stored on the scope by the SecurityMiddleware
        is a valid subject for the policy check.
    """
    dispatcher = create_policy_dispatcher(AccessPolicy(roles=["system-admin"]))

    context = SecurityContext(user_id="u1", roles=("system-admin",))
    request = Request(method="GET", path="/admin/users", scope={SECURITY_CONTEXT_SCOPE_KEY: context})
    response = dispatcher.dispatch(request)

    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    return


# ============================================================================
# Path normalisation
# ============================================================================

def test_dispatch_applies_policy_to_every_spelling_of_a_path():
    """
        //admin/users and /admin//users reach the /admin/users handler and
        are checked against its policy.
    """
    calls = []
    dispatcher = create_policy_dispatcher(AccessPolicy(roles=["system-admin"]), calls=calls)

    for path in ["//admin/users", "/admin//users", "///admin///users"]:
        anonymous = dispatcher.dispatch(Request(method="GET", path=path))
        assert anonymous.status_code == 401, f"{path}: expected 401, got {anonymous.status_code}"

        viewer = dispatcher.dispatch(
            Request(method="GET", path=path, scope=create_auth_scope(roles=["viewer"])))
        assert viewer.status_code == 403, f"{path}: expected 403, got {viewer.status_code}"

    assert len(calls) == 0, f"No refused request may reach the handler, got {calls}"
    return


def test_dispatch_publishes_canonical_path_on_request():
    """
        Middleware and handlers see the canonical path, the one the router matched.
    """
    seen = []

    def recording_middleware(request, call_next):
        seen.append(request.path)
        return call_next(request)

    router = Router()
    router.add_endpoint(create_test_descriptor("/a/b", ["GET"], create_test_handler({"ok": True})))
    pipeline = MiddlewarePipeline()
    pipeline.add(recording_middleware)
    dispatcher = Dispatcher(router, pipeline)

    response = dispatcher.dispatch(Request(method="GET", path="//a//b"))

    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    assert seen == ["/a/b"], f"Expected middleware to see the canonical path, got {seen}"
    return


def test_dispatch_answers_404_for_path_with_dot_segments():
    """
        A path with '..' segments names no route.
    """
    router = Router()
    router.add_endpoint(create_test_descriptor("/files/{name}", ["GET"], create_test_handler({"ok": True})))
    dispatcher = Dispatcher(router)

    response = dispatcher.dispatch(Request(method="GET", path="/files/.."))

    assert response.status_code == 404, f"Expected 404, got {response.status_code}"
    return


# ============================================================================
# Middleware around routing
# ============================================================================

def test_dispatch_runs_middleware_for_unmatched_route():
    """
        Global middleware runs for a request no route matches and sees the
        404 response.
    """
    seen = []

    def recording_middleware(request, call_next):
        response = call_next(request)
        seen.append(response.status_code)
        return response

    pipeline = MiddlewarePipeline()
    pipeline.add(recording_middleware)
    dispatcher = Dispatcher(Router(), pipeline)

    response = dispatcher.dispatch(Request(method="GET", path="/missing"))

    assert response.status_code == 404, f"Expected 404, got {response.status_code}"
    assert seen == [404], f"Expected the middleware to see the 404 response, got {seen}"
    return


def test_dispatch_async_answers_cors_preflight_for_registered_route():
    """
        A CORS preflight for a route registered for GET and POST is answered
        by the CORS middleware with 204 and CORS headers, not with 405.
    """
    router = Router()
    router.add_endpoint(create_test_descriptor("/api/items", ["GET", "POST"], create_test_handler({"ok": True})))
    pipeline = MiddlewarePipeline()
    pipeline.add(CORSMiddleware(allowed_origins=["https://app.example"], allowed_methods=["GET", "POST"]))
    dispatcher = Dispatcher(router, pipeline)

    request = Request(
        method="OPTIONS",
        path="/api/items",
        headers={"Origin": "https://app.example", "Access-Control-Request-Method": "POST"}
    )
    response = asyncio.run(dispatcher.dispatch_async(request))

    assert response.status_code == 204, f"Expected 204, got {response.status_code}"
    assert response.headers.get("Access-Control-Allow-Origin") == "https://app.example", \
        f"Expected the allowed origin to be echoed, got {response.headers}"
    return


def test_dispatch_adds_cors_headers_to_404_response():
    """
        A 404 passes back through the CORS middleware and receives CORS headers.
    """
    pipeline = MiddlewarePipeline()
    pipeline.add(CORSMiddleware(allowed_origins=["https://app.example"]))
    dispatcher = Dispatcher(Router(), pipeline)

    request = Request(method="GET", path="/missing", headers={"Origin": "https://app.example"})
    response = dispatcher.dispatch(request)

    assert response.status_code == 404, f"Expected 404, got {response.status_code}"
    assert response.headers.get("Access-Control-Allow-Origin") == "https://app.example", \
        f"Expected CORS headers on the 404, got {response.headers}"
    return


def test_dispatch_sets_middleware_context_without_descriptor_before_routing():
    """
        Global middleware runs before routing, so its middleware context has
        no endpoint descriptor.
    """
    seen = []

    def recording_middleware(request, call_next):
        seen.append(request.middleware_context)
        return call_next(request)

    router = Router()
    router.add_endpoint(create_test_descriptor("/ctx", ["GET"], create_test_handler({"ok": True})))
    pipeline = MiddlewarePipeline()
    pipeline.add(recording_middleware)
    dispatcher = Dispatcher(router, pipeline)

    dispatcher.dispatch(Request(method="GET", path="/ctx"))

    assert isinstance(seen[0], MiddlewareContext), f"Expected a MiddlewareContext, got {seen[0]!r}"
    assert seen[0].endpoint_descriptor is None, "No descriptor is known before routing"
    return


def test_dispatch_runs_route_pipeline_with_matched_descriptor():
    """
        Middleware of the route pipeline runs after routing and can read
        the matched descriptor.
    """
    seen = []

    def recording_middleware(request, call_next):
        seen.append(request.middleware_context.endpoint_descriptor)
        return call_next(request)

    descriptor = create_test_descriptor("/ctx", ["GET"], create_test_handler({"ok": True}))
    router = Router()
    router.add_endpoint(descriptor)
    dispatcher = Dispatcher(router)
    dispatcher.route_pipeline.add(recording_middleware)

    dispatcher.dispatch(Request(method="GET", path="/ctx"))

    assert seen == [descriptor], f"Expected the matched descriptor, got {seen}"
    return


def test_dispatch_composes_global_blueprint_and_route_middleware_from_registry():
    """
        With a registry, global middleware runs first, then the blueprint
        middleware, then the route middleware of the matched route.
    """
    order = []

    def make_middleware(label):
        def middleware(request, call_next):
            order.append(label)
            return call_next(request)
        return middleware

    registry = MiddlewareRegistry()
    registry.register(make_middleware("route"), scope="route", scope_key="/bp/items", priority=5)
    registry.register(make_middleware("blueprint"), scope="blueprint", scope_key="shop", priority=10)
    registry.register(make_middleware("global"), scope="global", priority=50)

    descriptor = EndpointDescriptor(
        handler=create_test_handler({"ok": True}),
        module="test",
        path="/bp/items",
        methods=["GET"],
        extras={"blueprint": "shop"},
    )
    router = Router()
    router.add_endpoint(descriptor)
    router.add_endpoint(create_test_descriptor("/other", ["GET"], create_test_handler({"ok": True})))
    dispatcher = Dispatcher(router, registry=registry)

    dispatcher.dispatch(Request(method="GET", path="/bp/items"))
    assert order == ["global", "blueprint", "route"], f"Unexpected order {order}"

    del order[:]
    dispatcher.dispatch(Request(method="GET", path="/other"))
    assert order == ["global"], f"Scoped middleware must not run for another route, got {order}"
    return


# ============================================================================
# HEAD, OPTIONS and trailing slash redirects
# ============================================================================

def test_dispatch_answers_head_from_get_handler_without_body():
    """
        HEAD on a GET-only route returns the GET status and headers and no body.
    """
    router = Router()
    router.add_endpoint(create_test_descriptor("/health", ["GET"], create_test_handler({"status": "ok"})))
    dispatcher = Dispatcher(router)

    response = dispatcher.dispatch(Request(method="HEAD", path="/health"))

    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    assert response.body == b"", f"A HEAD response must have no body, got {response.body!r}"
    assert "json" in response.headers.get("Content-Type", ""), \
        f"Expected the GET headers to be kept, got {response.headers}"
    return


def test_dispatch_answers_options_with_allow_header():
    """
        OPTIONS on a route without an OPTIONS handler is answered 204 with
        the methods the path supports.
    """
    router = Router()
    router.add_endpoint(create_test_descriptor("/items", ["GET", "POST"], create_test_handler({"ok": True})))
    dispatcher = Dispatcher(router)

    response = dispatcher.dispatch(Request(method="OPTIONS", path="/items"))

    assert response.status_code == 204, f"Expected 204, got {response.status_code}"
    allow = response.headers.get("Allow", "")
    for method in ["GET", "HEAD", "OPTIONS", "POST"]:
        assert method in allow, f"Expected {method} in Allow, got {allow!r}"
    return


def test_dispatch_method_not_allowed_lists_automatic_methods():
    """
        The Allow header of a 405 lists HEAD and OPTIONS next to the
        registered methods.
    """
    router = Router()
    router.add_endpoint(create_test_descriptor("/items", ["GET"], create_test_handler({"ok": True})))
    dispatcher = Dispatcher(router)

    response = dispatcher.dispatch(Request(method="DELETE", path="/items"))

    assert response.status_code == 405, f"Expected 405, got {response.status_code}"
    assert response.headers.get("Allow") == "GET, HEAD, OPTIONS", \
        f"Unexpected Allow header {response.headers.get('Allow')!r}"
    return


def test_dispatch_redirects_to_registered_slash_variant():
    """
        With redirect_slashes, /docs/ is redirected with 308 to the
        registered /docs, keeping the query string.
    """
    router = Router(redirect_slashes=True)
    router.add_endpoint(create_test_descriptor("/docs", ["GET"], create_test_handler({"ok": True})))
    dispatcher = Dispatcher(router)

    response = dispatcher.dispatch(Request(method="GET", path="/docs/", query_string=b"page=2"))

    assert response.status_code == 308, f"Expected 308, got {response.status_code}"
    assert response.headers.get("Location") == "/docs?page=2", \
        f"Unexpected Location {response.headers.get('Location')!r}"
    return


def test_dispatch_does_not_redirect_without_redirect_slashes():
    """
        Without redirect_slashes a trailing slash mismatch stays a 404.
    """
    router = Router()
    router.add_endpoint(create_test_descriptor("/docs", ["GET"], create_test_handler({"ok": True})))
    dispatcher = Dispatcher(router)

    response = dispatcher.dispatch(Request(method="GET", path="/docs/"))

    assert response.status_code == 404, f"Expected 404, got {response.status_code}"
    return


# ============================================================================
# Sync and async handlers
# ============================================================================

def test_dispatch_async_runs_sync_handler_off_the_event_loop():
    """
        dispatch_async runs a handler that is not a coroutine function on a
        worker thread, so it can block without stalling the event loop.
    """
    threads = {}

    def blocking_handler(request):
        threads["handler"] = threading.get_ident()
        return {"ok": True}

    router = Router()
    router.add_endpoint(create_test_descriptor("/blocking", ["GET"], blocking_handler))
    dispatcher = Dispatcher(router)

    async def run():
        threads["loop"] = threading.get_ident()
        return await dispatcher.dispatch_async(Request(method="GET", path="/blocking"))

    response = asyncio.run(run())

    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    assert threads["handler"] != threads["loop"], "The sync handler ran on the event loop thread"
    return


def test_dispatch_async_keeps_sync_handler_inline_when_offloading_disabled():
    """
        With offload_sync_handlers=False a sync handler runs on the event loop thread.
    """
    threads = {}

    def handler(request):
        threads["handler"] = threading.get_ident()
        return {"ok": True}

    router = Router()
    router.add_endpoint(create_test_descriptor("/inline", ["GET"], handler))
    dispatcher = Dispatcher(router, offload_sync_handlers=False)

    async def run():
        threads["loop"] = threading.get_ident()
        return await dispatcher.dispatch_async(Request(method="GET", path="/inline"))

    asyncio.run(run())

    assert threads["handler"] == threads["loop"], "The handler should have run on the loop thread"
    return


def test_dispatch_drives_async_handler_to_completion():
    """
        Synchronous dispatch awaits a coroutine handler instead of trying to
        serialise the coroutine.
    """
    async def async_handler(request):
        await asyncio.sleep(0)
        return {"from": "async"}

    router = Router()
    router.add_endpoint(create_test_descriptor("/async", ["GET"], async_handler))
    dispatcher = Dispatcher(router)

    response = dispatcher.dispatch(Request(method="GET", path="/async"))

    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    assert b"async" in response.body, f"Unexpected body {response.body!r}"
    return


def test_dispatch_async_publishes_application_loop_to_offloaded_handler():
    """
        A handler running on a worker thread can reach the dispatcher's
        event loop and drive a coroutine on it.
    """
    from ccai.webworks.routing.dispatcher import get_application_loop

    seen = {}

    async def loop_bound_lookup():
        seen["lookup_loop"] = asyncio.get_running_loop()
        return "value"

    def handler(request):
        loop = get_application_loop()
        seen["handler_loop"] = loop
        future = asyncio.run_coroutine_threadsafe(loop_bound_lookup(), loop)
        return {"result": future.result(timeout=5)}

    router = Router()
    router.add_endpoint(create_test_descriptor("/lookup", ["GET"], handler))
    dispatcher = Dispatcher(router)

    async def run():
        seen["dispatch_loop"] = asyncio.get_running_loop()
        return await dispatcher.dispatch_async(Request(method="GET", path="/lookup"))

    response = asyncio.run(run())

    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.body!r}"
    assert seen["handler_loop"] is seen["dispatch_loop"], "The handler did not receive the dispatcher's loop"
    assert seen["lookup_loop"] is seen["dispatch_loop"], "The coroutine did not run on the dispatcher's loop"
    assert get_application_loop() is None, "The loop must not be published outside a handler call"
    return


# ============================================================================
# Request lifecycle hooks
# ============================================================================

import asyncio as _hooks_asyncio

from ccai.webworks.extensibility.hookmanager import HookManager
from ccai.webworks.extensibility.requestlifecyclehooks import RequestLifecycleHooks
from ccai.webworks.routing.response import JSONResponse as _HooksJSONResponse


def _hooked_dispatcher(events, handler, register=None, on_first_request=None):
    """
        Build a dispatcher serving ``handler`` at /item with request hooks
        that record into ``events``.

        :param events: The list the hooks append to.
        :param handler: The route handler.
        :param register: Called with the HookManager to register more callbacks.
        :param on_first_request: The dispatcher's first-request callable.

        :returns: The dispatcher.
    """
    router = Router()
    router.add_endpoint(create_test_descriptor("/item", ["GET"], handler))

    manager = HookManager()
    manager.register("before_first_request", lambda request: events.append("before_first_request"), extension_name="rec")
    manager.register("before_request", lambda request: events.append("before_request"), extension_name="rec")
    manager.register(
        "on_request_error",
        lambda request, error: events.append(("on_request_error", type(error).__name__)),
        extension_name="rec"
    )
    manager.register("after_request", lambda request, response: events.append("after_request"), extension_name="rec")
    manager.register(
        "teardown_request",
        lambda request, response, error: events.append(
            ("teardown_request", response.status_code, type(error).__name__ if error is not None else None)
        ),
        extension_name="rec"
    )

    if register is not None:
        register(manager)

    rtnval = Dispatcher(
        router,
        request_hooks=RequestLifecycleHooks(hook_manager=manager),
        on_first_request=on_first_request
    )
    return rtnval


def test_dispatch_fires_request_hooks_in_order_sync_and_async():
    """
        Test that dispatch and dispatch_async fire the request hooks in the
        same order, before_first_request only for the first request.
    """
    events = []

    def handler(request):
        events.append("handler")
        return {"ok": True}

    dispatcher = _hooked_dispatcher(events, handler)

    sync_response = dispatcher.dispatch(Request("GET", "/item"))
    async_response = _hooks_asyncio.run(dispatcher.dispatch_async(Request("GET", "/item")))

    expected = [
        "before_first_request",
        "before_request", "handler", "after_request", ("teardown_request", 200, None),
        "before_request", "handler", "after_request", ("teardown_request", 200, None),
    ]
    assert events == expected, f"Expected {expected}, got {events}"
    assert sync_response.status_code == 200 and async_response.status_code == 200
    return


def test_dispatch_on_first_request_runs_once_before_before_first_request():
    """
        Test that the first-request callable runs once, before before_first_request.
    """
    events = []
    dispatcher = _hooked_dispatcher(
        events, create_test_handler({"ok": True}), on_first_request=lambda: events.append("on_first_request")
    )

    dispatcher.dispatch(Request("GET", "/item"))
    _hooks_asyncio.run(dispatcher.dispatch_async(Request("GET", "/item")))

    assert events.count("on_first_request") == 1, f"Expected one call, got {events}"
    assert events.index("on_first_request") < events.index("before_first_request"), f"Unexpected order {events}"
    return


def test_dispatch_before_request_response_short_circuits_routing():
    """
        Test that a response from before_request is sent without routing,
        even for a path no route matches, and after_request still runs.
    """
    events = []

    def register(manager):
        manager.register(
            "before_request", lambda request: _HooksJSONResponse({"maintenance": True}, status_code=503),
            extension_name="gate"
        )

    dispatcher = _hooked_dispatcher(events, create_test_handler({"ok": True}), register=register)

    response = _hooks_asyncio.run(dispatcher.dispatch_async(Request("GET", "/no-such-route")))

    assert response.status_code == 503, f"Expected the short-circuit 503, got {response.status_code}"
    assert events[-2:] == ["after_request", ("teardown_request", 503, None)], f"Unexpected events {events}"
    return


def test_dispatch_reports_an_unhandled_error_before_the_500():
    """
        Test that on_request_error sees the handler's exception, and teardown
        gets the 500 response and the exception, in both dispatch modes.
    """
    for mode in ("sync", "async"):
        events = []
        dispatcher = _hooked_dispatcher(events, create_exception_handler(RuntimeError("broken")))

        if mode == "sync":
            response = dispatcher.dispatch(Request("GET", "/item"))
        else:
            response = _hooks_asyncio.run(dispatcher.dispatch_async(Request("GET", "/item")))

        expected = [
            "before_first_request",
            "before_request",
            ("on_request_error", "RuntimeError"),
            "after_request",
            ("teardown_request", 500, "RuntimeError"),
        ]
        assert response.status_code == 500, f"{mode}: expected 500, got {response.status_code}"
        assert events == expected, f"{mode}: expected {expected}, got {events}"

    return


def test_dispatch_after_request_may_replace_the_response():
    """
        Test that a response returned by after_request is the one sent.
    """
    events = []

    def register(manager):
        manager.register(
            "after_request",
            lambda request, response: _HooksJSONResponse({"replaced": True}, status_code=202),
            extension_name="replacer"
        )

    dispatcher = _hooked_dispatcher(events, create_test_handler({"ok": True}), register=register)

    response = dispatcher.dispatch(Request("GET", "/item"))

    assert response.status_code == 202, f"Expected the replacement, got {response.status_code}"
    assert events[-1] == ("teardown_request", 202, None), f"Expected teardown to see the replacement, got {events}"
    return


def test_dispatch_failing_hook_answers_500_and_still_tears_down():
    """
        Test that a failing after_request callback turns the request into a
        500, reported to on_request_error, and the teardown still runs.
    """
    events = []

    def failing(request, response):
        raise ValueError("after failed")

    def register(manager):
        manager.register("after_request", failing, extension_name="bad")

    dispatcher = _hooked_dispatcher(events, create_test_handler({"ok": True}), register=register)

    response = _hooks_asyncio.run(dispatcher.dispatch_async(Request("GET", "/item")))

    assert response.status_code == 500, f"Expected 500, got {response.status_code}"
    assert ("on_request_error", "HookExecutionError") in events, f"Expected the hook failure reported, got {events}"
    assert events[-1] == ("teardown_request", 500, "HookExecutionError"), f"Unexpected teardown {events}"
    return


def test_dispatch_head_response_has_no_body_after_hooks():
    """
        Test that a HEAD response is emptied after the after_request hooks.
    """
    events = []
    dispatcher = _hooked_dispatcher(events, create_test_handler({"ok": True}))

    response = dispatcher.dispatch(Request("HEAD", "/item"))

    assert response.status_code == 200 and response.body == b"", f"Expected an empty 200, got {response.body!r}"
    return


def test_dispatch_without_callbacks_takes_the_plain_path():
    """
        Test that with no request hook callback the hooks are not consulted
        after the first request.
    """
    router = Router()
    router.add_endpoint(create_test_descriptor("/item", ["GET"], create_test_handler({"ok": True})))

    manager = HookManager()
    hooks = RequestLifecycleHooks(hook_manager=manager)
    dispatcher = Dispatcher(router, request_hooks=hooks)

    dispatcher.dispatch(Request("GET", "/item"))

    assert hooks.first_request_handled is True, "Expected the first request to be handled"
    assert dispatcher._uses_request_hooks() is False, "Expected the plain path without callbacks"

    manager.register("before_request", lambda request: None, extension_name="late")

    assert dispatcher._uses_request_hooks() is True, "Expected the hooks path once a callback is registered"
    return
