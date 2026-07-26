"""
    Tests for the HTTPHandler class.
    
    This module contains unit tests for the ASGI HTTP handler functionality.
"""

import asyncio
from typing import Any, Awaitable, Callable, Dict, List, Optional

from ccai.webworks.asgi.httphandler import HTTPHandler
from ccai.webworks.asgi.scopeparser import ScopeParser
from ccai.webworks.asgi.bodyreader import BodyReader
from ccai.webworks.asgi.responsesender import ResponseSender
from ccai.webworks.asgi.constants import (
    SCOPE_REQUEST,
    MESSAGE_HTTP_REQUEST,
    MESSAGE_HTTP_RESPONSE_START,
    MESSAGE_HTTP_RESPONSE_BODY,
    MESSAGE_HTTP_DISCONNECT,
)
from ccai.webworks.routing.request import Request
from ccai.webworks.wsgi.response import Response


# =============================================================================
# Test Helpers
# =============================================================================

def create_http_scope(
    method: str = "GET",
    path: str = "/",
    query_string: bytes = b"",
    headers: Optional[List[tuple]] = None,
    scheme: str = "http",
    server: tuple = ("localhost", 80),
) -> Dict[str, Any]:
    """
        Create a minimal HTTP scope for testing.
    """
    if headers is None:
        headers = []
    
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": method,
        "path": path,
        "query_string": query_string,
        "headers": headers,
        "scheme": scheme,
        "server": server,
    }
    return scope


def create_receive_callable(
    body: bytes = b"",
    disconnect: bool = False,
) -> Callable[[], Awaitable[Dict[str, Any]]]:
    """
        Create a receive callable that returns body chunks.
    """
    messages: List[Dict[str, Any]] = []
    
    if disconnect:
        messages.append({"type": MESSAGE_HTTP_DISCONNECT})
    else:
        messages.append({
            "type": MESSAGE_HTTP_REQUEST,
            "body": body,
            "more_body": False,
        })
    
    index = [0]
    
    async def receive() -> Dict[str, Any]:
        if index[0] < len(messages):
            msg = messages[index[0]]
            index[0] = index[0] + 1
            return msg
        # Return empty body if called again
        return {"type": MESSAGE_HTTP_REQUEST, "body": b"", "more_body": False}
    
    return receive


def create_send_callable() -> tuple:
    """
        Create a send callable that captures sent messages.
        
        Returns a tuple of (send_callable, sent_messages_list).
    """
    sent_messages: List[Dict[str, Any]] = []
    
    async def send(message: Dict[str, Any]) -> None:
        sent_messages.append(message)
        return
    
    return (send, sent_messages)


# =============================================================================
# Unit Tests for HTTPHandler - Construction
# =============================================================================

def test_httphandler_construction_with_defaults():
    """
        Test that HTTPHandler can be constructed with default values.
    """
    handler = HTTPHandler()
    
    if handler.debug is not False:
        errmsg = f"Expected debug=False, got {handler.debug}"
        raise AssertionError(errmsg)
    
    if handler.request_timeout is not None:
        errmsg = f"Expected request_timeout=None, got {handler.request_timeout}"
        raise AssertionError(errmsg)
    
    return


def test_httphandler_construction_with_custom_components():
    """
        Test that HTTPHandler can be constructed with custom components.
    """
    scope_parser = ScopeParser()
    body_reader = BodyReader(max_size=1024)
    response_sender = ResponseSender()
    
    handler = HTTPHandler(
        scope_parser=scope_parser,
        body_reader=body_reader,
        response_sender=response_sender,
        debug=True,
        request_timeout=30.0,
    )
    
    if handler.debug is not True:
        errmsg = f"Expected debug=True, got {handler.debug}"
        raise AssertionError(errmsg)
    
    if handler.request_timeout != 30.0:
        errmsg = f"Expected request_timeout=30.0, got {handler.request_timeout}"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for HTTPHandler - Handler Setting
# =============================================================================

def test_httphandler_set_handler():
    """
        Test that set_handler sets the request handler.
    """
    handler = HTTPHandler()
    
    async def my_handler(request: Request) -> Response:
        return Response(status_code=200, body=b"OK")
    
    handler.set_handler(my_handler)
    
    # Handler is set internally, we verify by running handle()
    # This test just ensures no exception is raised
    return


def test_httphandler_add_middleware():
    """
        Test that add_middleware adds middleware to the pipeline.
    """
    handler = HTTPHandler()
    
    async def my_middleware(request: Request, next_handler) -> Response:
        response = await next_handler(request)
        return response
    
    handler.add_middleware(my_middleware)
    
    # Middleware is added internally, we verify by running handle()
    # This test just ensures no exception is raised
    return


# =============================================================================
# Unit Tests for HTTPHandler - Request Handling
# =============================================================================

def test_httphandler_handle_returns_404_when_no_handler():
    """
        Test that handle returns 404 when no handler is set.
    """
    handler = HTTPHandler()
    
    scope = create_http_scope(method="GET", path="/test")
    receive = create_receive_callable()
    send, sent_messages = create_send_callable()
    
    asyncio.get_event_loop().run_until_complete(
        handler.handle(scope, receive, send)
    )
    
    # Check that response start was sent
    if len(sent_messages) < 1:
        errmsg = "Expected at least one message to be sent"
        raise AssertionError(errmsg)
    
    start_message = sent_messages[0]
    if start_message.get("type") != MESSAGE_HTTP_RESPONSE_START:
        errmsg = f"Expected response start message, got {start_message.get('type')}"
        raise AssertionError(errmsg)
    
    if start_message.get("status") != 404:
        errmsg = f"Expected status 404, got {start_message.get('status')}"
        raise AssertionError(errmsg)
    
    return


def test_httphandler_handle_calls_handler():
    """
        Test that handle calls the registered handler.
    """
    handler = HTTPHandler()
    
    handler_called = [False]
    
    async def my_handler(request: Request) -> Response:
        handler_called[0] = True
        return Response(status_code=200, body=b"Hello")
    
    handler.set_handler(my_handler)
    
    scope = create_http_scope(method="GET", path="/test")
    receive = create_receive_callable()
    send, sent_messages = create_send_callable()
    
    asyncio.get_event_loop().run_until_complete(
        handler.handle(scope, receive, send)
    )
    
    if not handler_called[0]:
        errmsg = "Expected handler to be called"
        raise AssertionError(errmsg)
    
    # Check response status
    start_message = sent_messages[0]
    if start_message.get("status") != 200:
        errmsg = f"Expected status 200, got {start_message.get('status')}"
        raise AssertionError(errmsg)
    
    return


def test_httphandler_handle_passes_request_to_handler():
    """
        Test that handle passes the correct request to the handler.
    """
    handler = HTTPHandler()
    
    received_request = [None]
    
    async def my_handler(request: Request) -> Response:
        received_request[0] = request
        return Response(status_code=200, body=b"OK")
    
    handler.set_handler(my_handler)
    
    scope = create_http_scope(
        method="POST",
        path="/api/users",
        query_string=b"id=123",
    )
    receive = create_receive_callable(body=b"test body")
    send, sent_messages = create_send_callable()
    
    asyncio.get_event_loop().run_until_complete(
        handler.handle(scope, receive, send)
    )
    
    request = received_request[0]
    if request is None:
        errmsg = "Expected request to be passed to handler"
        raise AssertionError(errmsg)
    
    if request.method != "POST":
        errmsg = f"Expected method 'POST', got '{request.method}'"
        raise AssertionError(errmsg)
    
    if request.path != "/api/users":
        errmsg = f"Expected path '/api/users', got '{request.path}'"
        raise AssertionError(errmsg)
    
    if request.query_string != "id=123":
        errmsg = f"Expected query_string 'id=123', got '{request.query_string}'"
        raise AssertionError(errmsg)
    
    if request.body != b"test body":
        errmsg = f"Expected body 'test body', got '{request.body}'"
        raise AssertionError(errmsg)
    
    return


def test_httphandler_handle_sends_response_body():
    """
        Test that handle sends the response body.
    """
    handler = HTTPHandler()
    
    async def my_handler(request: Request) -> Response:
        return Response(status_code=200, body=b"Hello World")
    
    handler.set_handler(my_handler)
    
    scope = create_http_scope()
    receive = create_receive_callable()
    send, sent_messages = create_send_callable()
    
    asyncio.get_event_loop().run_until_complete(
        handler.handle(scope, receive, send)
    )
    
    # Check that body was sent
    if len(sent_messages) < 2:
        errmsg = "Expected at least two messages (start and body)"
        raise AssertionError(errmsg)
    
    body_message = sent_messages[1]
    if body_message.get("type") != MESSAGE_HTTP_RESPONSE_BODY:
        errmsg = f"Expected response body message, got {body_message.get('type')}"
        raise AssertionError(errmsg)
    
    if body_message.get("body") != b"Hello World":
        errmsg = f"Expected body 'Hello World', got {body_message.get('body')}"
        raise AssertionError(errmsg)
    
    return


def test_httphandler_handle_sets_request_in_scope():
    """
        Test that handle sets the request in the scope.
    """
    handler = HTTPHandler()
    
    async def my_handler(request: Request) -> Response:
        return Response(status_code=200, body=b"OK")
    
    handler.set_handler(my_handler)
    
    scope = create_http_scope()
    receive = create_receive_callable()
    send, sent_messages = create_send_callable()
    
    asyncio.get_event_loop().run_until_complete(
        handler.handle(scope, receive, send)
    )
    
    if SCOPE_REQUEST not in scope:
        errmsg = f"Expected '{SCOPE_REQUEST}' key in scope"
        raise AssertionError(errmsg)
    
    if not isinstance(scope[SCOPE_REQUEST], Request):
        errmsg = f"Expected Request object in scope, got {type(scope[SCOPE_REQUEST])}"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for HTTPHandler - Error Handling
# =============================================================================

def test_httphandler_handle_returns_500_on_handler_exception():
    """
        Test that handle returns 500 when handler raises exception.
    """
    handler = HTTPHandler()
    
    async def my_handler(request: Request) -> Response:
        raise ValueError("Something went wrong")
    
    handler.set_handler(my_handler)
    
    scope = create_http_scope()
    receive = create_receive_callable()
    send, sent_messages = create_send_callable()
    
    asyncio.get_event_loop().run_until_complete(
        handler.handle(scope, receive, send)
    )
    
    start_message = sent_messages[0]
    if start_message.get("status") != 500:
        errmsg = f"Expected status 500, got {start_message.get('status')}"
        raise AssertionError(errmsg)
    
    return


def test_httphandler_handle_includes_debug_info_when_debug_enabled():
    """
        Test that handle includes debug info in error response when debug=True.
    """
    handler = HTTPHandler(debug=True)
    
    async def my_handler(request: Request) -> Response:
        raise ValueError("Test error message")
    
    handler.set_handler(my_handler)
    
    scope = create_http_scope()
    receive = create_receive_callable()
    send, sent_messages = create_send_callable()
    
    asyncio.get_event_loop().run_until_complete(
        handler.handle(scope, receive, send)
    )
    
    # Check that body contains error details
    body_message = sent_messages[1]
    body = body_message.get("body", b"")
    body_str = body.decode("utf-8")
    
    if "ValueError" not in body_str:
        errmsg = f"Expected 'ValueError' in error body, got: {body_str}"
        raise AssertionError(errmsg)
    
    if "Test error message" not in body_str:
        errmsg = f"Expected 'Test error message' in error body, got: {body_str}"
        raise AssertionError(errmsg)
    
    return


def test_httphandler_handle_hides_debug_info_when_debug_disabled():
    """
        Test that handle hides debug info in error response when debug=False.
    """
    handler = HTTPHandler(debug=False)
    
    async def my_handler(request: Request) -> Response:
        raise ValueError("Secret error message")
    
    handler.set_handler(my_handler)
    
    scope = create_http_scope()
    receive = create_receive_callable()
    send, sent_messages = create_send_callable()
    
    asyncio.get_event_loop().run_until_complete(
        handler.handle(scope, receive, send)
    )
    
    # Check that body does not contain error details
    body_message = sent_messages[1]
    body = body_message.get("body", b"")
    body_str = body.decode("utf-8")
    
    if "Secret error message" in body_str:
        errmsg = f"Did not expect error details in body: {body_str}"
        raise AssertionError(errmsg)
    
    if "ValueError" in body_str:
        errmsg = f"Did not expect exception type in body: {body_str}"
        raise AssertionError(errmsg)
    
    return


def test_httphandler_handle_gracefully_handles_client_disconnect():
    """
        Test that handle gracefully handles client disconnection.
    """
    handler = HTTPHandler()
    
    async def my_handler(request: Request) -> Response:
        return Response(status_code=200, body=b"OK")
    
    handler.set_handler(my_handler)
    
    scope = create_http_scope()
    receive = create_receive_callable(disconnect=True)
    send, sent_messages = create_send_callable()
    
    # Should not raise an exception
    asyncio.get_event_loop().run_until_complete(
        handler.handle(scope, receive, send)
    )
    
    # No response should be sent when client disconnects
    if len(sent_messages) != 0:
        errmsg = f"Expected no messages sent on disconnect, got {len(sent_messages)}"
        raise AssertionError(errmsg)
    
    return


def test_httphandler_handle_returns_413_on_body_too_large():
    """
        Test that handle returns 413 when body exceeds max size.
    """
    body_reader = BodyReader(max_size=10)
    handler = HTTPHandler(body_reader=body_reader)
    
    async def my_handler(request: Request) -> Response:
        return Response(status_code=200, body=b"OK")
    
    handler.set_handler(my_handler)
    
    scope = create_http_scope(
        headers=[(b"content-length", b"100")]
    )
    receive = create_receive_callable(body=b"x" * 100)
    send, sent_messages = create_send_callable()
    
    asyncio.get_event_loop().run_until_complete(
        handler.handle(scope, receive, send)
    )
    
    start_message = sent_messages[0]
    if start_message.get("status") != 413:
        errmsg = f"Expected status 413, got {start_message.get('status')}"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for HTTPHandler - Middleware
# =============================================================================

def test_httphandler_middleware_is_called():
    """
        Test that middleware is called during request handling.
    """
    handler = HTTPHandler()
    
    middleware_called = [False]
    
    async def my_middleware(request: Request, next_handler) -> Response:
        middleware_called[0] = True
        response = await next_handler(request)
        return response
    
    async def my_handler(request: Request) -> Response:
        return Response(status_code=200, body=b"OK")
    
    handler.add_middleware(my_middleware)
    handler.set_handler(my_handler)
    
    scope = create_http_scope()
    receive = create_receive_callable()
    send, sent_messages = create_send_callable()
    
    asyncio.get_event_loop().run_until_complete(
        handler.handle(scope, receive, send)
    )
    
    if not middleware_called[0]:
        errmsg = "Expected middleware to be called"
        raise AssertionError(errmsg)
    
    return


def test_httphandler_middleware_can_modify_request():
    """
        Test that middleware can modify the request.
    """
    handler = HTTPHandler()
    
    received_header = [None]
    
    async def my_middleware(request: Request, next_handler) -> Response:
        # Add a custom header to the request
        request.headers["X-Custom"] = "middleware-value"
        response = await next_handler(request)
        return response
    
    async def my_handler(request: Request) -> Response:
        received_header[0] = request.headers.get("X-Custom")
        return Response(status_code=200, body=b"OK")
    
    handler.add_middleware(my_middleware)
    handler.set_handler(my_handler)
    
    scope = create_http_scope()
    receive = create_receive_callable()
    send, sent_messages = create_send_callable()
    
    asyncio.get_event_loop().run_until_complete(
        handler.handle(scope, receive, send)
    )
    
    if received_header[0] != "middleware-value":
        errmsg = f"Expected header 'middleware-value', got '{received_header[0]}'"
        raise AssertionError(errmsg)
    
    return


def test_httphandler_middleware_can_modify_response():
    """
        Test that middleware can modify the response.
    """
    handler = HTTPHandler()
    
    async def my_middleware(request: Request, next_handler) -> Response:
        response = await next_handler(request)
        response.set_header("X-Middleware", "added")
        return response
    
    async def my_handler(request: Request) -> Response:
        return Response(status_code=200, body=b"OK")
    
    handler.add_middleware(my_middleware)
    handler.set_handler(my_handler)
    
    scope = create_http_scope()
    receive = create_receive_callable()
    send, sent_messages = create_send_callable()
    
    asyncio.get_event_loop().run_until_complete(
        handler.handle(scope, receive, send)
    )
    
    # Check that the middleware header was added
    start_message = sent_messages[0]
    headers = start_message.get("headers", [])
    
    found_header = False
    for name, value in headers:
        if name == b"x-middleware" and value == b"added":
            found_header = True
            break
    
    if not found_header:
        errmsg = "Expected 'X-Middleware' header in response"
        raise AssertionError(errmsg)
    
    return


def test_httphandler_multiple_middleware_execute_in_order():
    """
        Test that multiple middleware execute in the order they were added.
    """
    handler = HTTPHandler()
    
    execution_order: List[str] = []
    
    async def middleware_a(request: Request, next_handler) -> Response:
        execution_order.append("A-before")
        response = await next_handler(request)
        execution_order.append("A-after")
        return response
    
    async def middleware_b(request: Request, next_handler) -> Response:
        execution_order.append("B-before")
        response = await next_handler(request)
        execution_order.append("B-after")
        return response
    
    async def my_handler(request: Request) -> Response:
        execution_order.append("handler")
        return Response(status_code=200, body=b"OK")
    
    handler.add_middleware(middleware_a)
    handler.add_middleware(middleware_b)
    handler.set_handler(my_handler)
    
    scope = create_http_scope()
    receive = create_receive_callable()
    send, sent_messages = create_send_callable()
    
    asyncio.get_event_loop().run_until_complete(
        handler.handle(scope, receive, send)
    )
    
    expected_order = ["A-before", "B-before", "handler", "B-after", "A-after"]
    if execution_order != expected_order:
        errmsg = f"Expected execution order {expected_order}, got {execution_order}"
        raise AssertionError(errmsg)
    
    return


def test_httphandler_middleware_can_short_circuit():
    """
        Test that middleware can short-circuit the request pipeline.
    """
    handler = HTTPHandler()
    
    handler_called = [False]
    
    async def auth_middleware(request: Request, next_handler) -> Response:
        # Short-circuit without calling next_handler
        return Response(status_code=401, body=b"Unauthorized")
    
    async def my_handler(request: Request) -> Response:
        handler_called[0] = True
        return Response(status_code=200, body=b"OK")
    
    handler.add_middleware(auth_middleware)
    handler.set_handler(my_handler)
    
    scope = create_http_scope()
    receive = create_receive_callable()
    send, sent_messages = create_send_callable()
    
    asyncio.get_event_loop().run_until_complete(
        handler.handle(scope, receive, send)
    )
    
    if handler_called[0]:
        errmsg = "Expected handler to NOT be called when middleware short-circuits"
        raise AssertionError(errmsg)
    
    start_message = sent_messages[0]
    if start_message.get("status") != 401:
        errmsg = f"Expected status 401, got {start_message.get('status')}"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for HTTPHandler - Async Handler Support
# =============================================================================

def test_httphandler_supports_async_handler():
    """
        Test that HTTPHandler supports async handlers.
    """
    handler = HTTPHandler()
    
    async def async_handler(request: Request) -> Response:
        # Simulate async operation
        await asyncio.sleep(0.01)
        return Response(status_code=200, body=b"Async OK")
    
    handler.set_handler(async_handler)
    
    scope = create_http_scope()
    receive = create_receive_callable()
    send, sent_messages = create_send_callable()
    
    asyncio.get_event_loop().run_until_complete(
        handler.handle(scope, receive, send)
    )
    
    start_message = sent_messages[0]
    if start_message.get("status") != 200:
        errmsg = f"Expected status 200, got {start_message.get('status')}"
        raise AssertionError(errmsg)
    
    body_message = sent_messages[1]
    if body_message.get("body") != b"Async OK":
        errmsg = f"Expected body 'Async OK', got {body_message.get('body')}"
        raise AssertionError(errmsg)
    
    return


def test_httphandler_supports_async_middleware():
    """
        Test that HTTPHandler supports async middleware.
    """
    handler = HTTPHandler()
    
    async def async_middleware(request: Request, next_handler) -> Response:
        # Simulate async operation before handler
        await asyncio.sleep(0.01)
        response = await next_handler(request)
        # Simulate async operation after handler
        await asyncio.sleep(0.01)
        return response
    
    async def my_handler(request: Request) -> Response:
        return Response(status_code=200, body=b"OK")
    
    handler.add_middleware(async_middleware)
    handler.set_handler(my_handler)
    
    scope = create_http_scope()
    receive = create_receive_callable()
    send, sent_messages = create_send_callable()
    
    asyncio.get_event_loop().run_until_complete(
        handler.handle(scope, receive, send)
    )
    
    start_message = sent_messages[0]
    if start_message.get("status") != 200:
        errmsg = f"Expected status 200, got {start_message.get('status')}"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for HTTPHandler - Timeout Support
# =============================================================================

def test_httphandler_timeout_returns_504_on_timeout():
    """
        Test that HTTPHandler returns 504 when request times out.
    """
    handler = HTTPHandler(request_timeout=0.05)
    
    async def slow_handler(request: Request) -> Response:
        # Simulate slow operation that exceeds timeout
        await asyncio.sleep(0.2)
        return Response(status_code=200, body=b"OK")
    
    handler.set_handler(slow_handler)
    
    scope = create_http_scope()
    receive = create_receive_callable()
    send, sent_messages = create_send_callable()
    
    asyncio.get_event_loop().run_until_complete(
        handler.handle(scope, receive, send)
    )
    
    start_message = sent_messages[0]
    if start_message.get("status") != 504:
        errmsg = f"Expected status 504, got {start_message.get('status')}"
        raise AssertionError(errmsg)
    
    return


def test_httphandler_timeout_allows_fast_requests():
    """
        Test that HTTPHandler allows requests that complete within timeout.
    """
    handler = HTTPHandler(request_timeout=1.0)
    
    async def fast_handler(request: Request) -> Response:
        # Fast operation that completes within timeout
        await asyncio.sleep(0.01)
        return Response(status_code=200, body=b"Fast OK")
    
    handler.set_handler(fast_handler)
    
    scope = create_http_scope()
    receive = create_receive_callable()
    send, sent_messages = create_send_callable()
    
    asyncio.get_event_loop().run_until_complete(
        handler.handle(scope, receive, send)
    )
    
    start_message = sent_messages[0]
    if start_message.get("status") != 200:
        errmsg = f"Expected status 200, got {start_message.get('status')}"
        raise AssertionError(errmsg)
    
    body_message = sent_messages[1]
    if body_message.get("body") != b"Fast OK":
        errmsg = f"Expected body 'Fast OK', got {body_message.get('body')}"
        raise AssertionError(errmsg)
    
    return


def test_httphandler_no_timeout_when_not_configured():
    """
        Test that HTTPHandler does not timeout when timeout is not configured.
    """
    handler = HTTPHandler(request_timeout=None)
    
    async def handler_func(request: Request) -> Response:
        # This would timeout if timeout was set to a small value
        await asyncio.sleep(0.05)
        return Response(status_code=200, body=b"OK")
    
    handler.set_handler(handler_func)
    
    scope = create_http_scope()
    receive = create_receive_callable()
    send, sent_messages = create_send_callable()
    
    asyncio.get_event_loop().run_until_complete(
        handler.handle(scope, receive, send)
    )
    
    start_message = sent_messages[0]
    if start_message.get("status") != 200:
        errmsg = f"Expected status 200, got {start_message.get('status')}"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for HTTPHandler - Background Tasks Integration
# =============================================================================

def test_httphandler_provides_background_tasks_to_handler():
    """
        Test that HTTPHandler provides background tasks to the handler.
    """
    handler = HTTPHandler()
    
    received_background_tasks = [None]
    
    async def my_handler(request: Request) -> Response:
        received_background_tasks[0] = request.background_tasks
        return Response(status_code=200, body=b"OK")
    
    handler.set_handler(my_handler)
    
    scope = create_http_scope()
    receive = create_receive_callable()
    send, sent_messages = create_send_callable()
    
    asyncio.get_event_loop().run_until_complete(
        handler.handle(scope, receive, send)
    )
    
    if received_background_tasks[0] is None:
        errmsg = "Expected background_tasks to be provided to handler"
        raise AssertionError(errmsg)
    
    return


def test_httphandler_executes_background_tasks_after_response():
    """
        Test that HTTPHandler executes background tasks after response is sent.
    """
    handler = HTTPHandler()
    
    task_executed = [False]
    response_sent_before_task = [False]
    
    async def background_task():
        task_executed[0] = True
        return
    
    async def my_handler(request: Request) -> Response:
        request.background_tasks.add_task(background_task)
        return Response(status_code=200, body=b"OK")
    
    handler.set_handler(my_handler)
    
    scope = create_http_scope()
    receive = create_receive_callable()
    
    # Custom send that tracks when response is sent
    sent_messages: List[Dict[str, Any]] = []
    
    async def send(message: Dict[str, Any]) -> None:
        sent_messages.append(message)
        # Check if task was executed before response body was sent
        if message.get("type") == MESSAGE_HTTP_RESPONSE_BODY:
            response_sent_before_task[0] = not task_executed[0]
        return
    
    asyncio.get_event_loop().run_until_complete(
        handler.handle(scope, receive, send)
    )
    
    if not task_executed[0]:
        errmsg = "Expected background task to be executed"
        raise AssertionError(errmsg)
    
    if not response_sent_before_task[0]:
        errmsg = "Expected response to be sent before background task executed"
        raise AssertionError(errmsg)
    
    return


def test_httphandler_executes_multiple_background_tasks_in_order():
    """
        Test that HTTPHandler executes multiple background tasks in order.
    """
    handler = HTTPHandler()
    
    execution_order: List[str] = []
    
    async def task_a():
        execution_order.append("A")
        return
    
    async def task_b():
        execution_order.append("B")
        return
    
    async def task_c():
        execution_order.append("C")
        return
    
    async def my_handler(request: Request) -> Response:
        request.background_tasks.add_task(task_a)
        request.background_tasks.add_task(task_b)
        request.background_tasks.add_task(task_c)
        return Response(status_code=200, body=b"OK")
    
    handler.set_handler(my_handler)
    
    scope = create_http_scope()
    receive = create_receive_callable()
    send, sent_messages = create_send_callable()
    
    asyncio.get_event_loop().run_until_complete(
        handler.handle(scope, receive, send)
    )
    
    expected_order = ["A", "B", "C"]
    if execution_order != expected_order:
        errmsg = f"Expected execution order {expected_order}, got {execution_order}"
        raise AssertionError(errmsg)
    
    return


def test_httphandler_background_task_with_arguments():
    """
        Test that HTTPHandler passes arguments to background tasks.
    """
    handler = HTTPHandler()
    
    received_args = [None, None]
    
    async def task_with_args(arg1, arg2):
        received_args[0] = arg1
        received_args[1] = arg2
        return
    
    async def my_handler(request: Request) -> Response:
        request.background_tasks.add_task(task_with_args, "value1", arg2="value2")
        return Response(status_code=200, body=b"OK")
    
    handler.set_handler(my_handler)
    
    scope = create_http_scope()
    receive = create_receive_callable()
    send, sent_messages = create_send_callable()
    
    asyncio.get_event_loop().run_until_complete(
        handler.handle(scope, receive, send)
    )
    
    if received_args[0] != "value1":
        errmsg = f"Expected arg1='value1', got '{received_args[0]}'"
        raise AssertionError(errmsg)
    
    if received_args[1] != "value2":
        errmsg = f"Expected arg2='value2', got '{received_args[1]}'"
        raise AssertionError(errmsg)
    
    return


def test_httphandler_background_task_error_does_not_affect_response():
    """
        Test that background task errors do not affect the response.
    """
    handler = HTTPHandler()
    
    async def failing_task():
        raise ValueError("Task error")
    
    async def my_handler(request: Request) -> Response:
        request.background_tasks.add_task(failing_task)
        return Response(status_code=200, body=b"OK")
    
    handler.set_handler(my_handler)
    
    scope = create_http_scope()
    receive = create_receive_callable()
    send, sent_messages = create_send_callable()
    
    # Should not raise even though background task fails
    asyncio.get_event_loop().run_until_complete(
        handler.handle(scope, receive, send)
    )
    
    # Response should still be 200 OK
    start_message = sent_messages[0]
    if start_message.get("status") != 200:
        errmsg = f"Expected status 200, got {start_message.get('status')}"
        raise AssertionError(errmsg)
    
    return
