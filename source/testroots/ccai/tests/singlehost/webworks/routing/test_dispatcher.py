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
    JSONResponse,
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
    
    response = dispatcher.dispatch(request)
    
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
            f"Production mode should not expose error details"
        
        # Property: Debug mode should include traceback information
        # (either "Traceback" or the exception type name)
        body_debug = response_debug.body
        has_traceback = b"Traceback" in body_debug or b"ValueError" in body_debug
        assert has_traceback, \
            f"Debug mode should include traceback information"
    
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
