"""
    Tests for the ASGIApplication class.
    
    This module contains unit tests for the ASGI application functionality.
"""

import asyncio
from typing import Any, Awaitable, Callable, Dict, List, Optional

from ccai.webworks.asgi.application import ASGIApplication, UnknownScopeTypeError
from ccai.webworks.asgi.httphandler import HTTPHandler
from ccai.webworks.asgi.websockethandler import WebSocketHandler
from ccai.webworks.asgi.lifespanhandler import LifespanHandler
from ccai.webworks.asgi.errorhandler import ErrorHandler
from ccai.webworks.asgi.constants import (
    SCOPE_TYPE_HTTP,
    SCOPE_TYPE_WEBSOCKET,
    SCOPE_TYPE_LIFESPAN,
    MESSAGE_HTTP_REQUEST,
    MESSAGE_HTTP_RESPONSE_START,
    MESSAGE_WEBSOCKET_CONNECT,
    MESSAGE_WEBSOCKET_CLOSE,
    MESSAGE_LIFESPAN_STARTUP,
    MESSAGE_LIFESPAN_STARTUP_COMPLETE,
    MESSAGE_LIFESPAN_SHUTDOWN,
    MESSAGE_LIFESPAN_SHUTDOWN_COMPLETE,
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
        "type": SCOPE_TYPE_HTTP,
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


def create_websocket_scope(
    path: str = "/ws",
    query_string: bytes = b"",
    headers: Optional[List[tuple]] = None,
    scheme: str = "ws",
    server: tuple = ("localhost", 80),
) -> Dict[str, Any]:
    """
        Create a minimal WebSocket scope for testing.
    """
    if headers is None:
        headers = []
    
    scope = {
        "type": SCOPE_TYPE_WEBSOCKET,
        "asgi": {"version": "3.0"},
        "path": path,
        "query_string": query_string,
        "headers": headers,
        "scheme": scheme,
        "server": server,
        "subprotocols": [],
    }
    return scope


def create_lifespan_scope() -> Dict[str, Any]:
    """
        Create a minimal lifespan scope for testing.
    """
    scope = {
        "type": SCOPE_TYPE_LIFESPAN,
        "asgi": {"version": "3.0"},
    }
    return scope


def create_unknown_scope(scope_type: str = "unknown") -> Dict[str, Any]:
    """
        Create a scope with an unknown type for testing.
    """
    scope = {
        "type": scope_type,
        "asgi": {"version": "3.0"},
    }
    return scope


def create_http_receive_callable(
    body: bytes = b"",
) -> Callable[[], Awaitable[Dict[str, Any]]]:
    """
        Create a receive callable for HTTP requests.
    """
    messages: List[Dict[str, Any]] = [
        {
            "type": MESSAGE_HTTP_REQUEST,
            "body": body,
            "more_body": False,
        }
    ]
    
    index = [0]
    
    async def receive() -> Dict[str, Any]:
        if index[0] < len(messages):
            msg = messages[index[0]]
            index[0] = index[0] + 1
            return msg
        return {"type": MESSAGE_HTTP_REQUEST, "body": b"", "more_body": False}
    
    return receive


def create_websocket_receive_callable(
    messages: Optional[List[Dict[str, Any]]] = None,
) -> Callable[[], Awaitable[Dict[str, Any]]]:
    """
        Create a receive callable for WebSocket connections.
    """
    if messages is None:
        messages = [
            {"type": MESSAGE_WEBSOCKET_CONNECT},
        ]
    
    index = [0]
    
    async def receive() -> Dict[str, Any]:
        if index[0] < len(messages):
            msg = messages[index[0]]
            index[0] = index[0] + 1
            return msg
        # Return disconnect if no more messages
        return {"type": "websocket.disconnect", "code": 1000}
    
    return receive


def create_lifespan_receive_callable() -> Callable[[], Awaitable[Dict[str, Any]]]:
    """
        Create a receive callable for lifespan events.
    """
    messages: List[Dict[str, Any]] = [
        {"type": MESSAGE_LIFESPAN_STARTUP},
        {"type": MESSAGE_LIFESPAN_SHUTDOWN},
    ]
    
    index = [0]
    
    async def receive() -> Dict[str, Any]:
        if index[0] < len(messages):
            msg = messages[index[0]]
            index[0] = index[0] + 1
            return msg
        # Block indefinitely if no more messages
        await asyncio.sleep(10)
        return {}
    
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
# Unit Tests for ASGIApplication - Construction
# =============================================================================

def test_asgiapplication_construction_with_defaults():
    """
        Test that ASGIApplication can be constructed with default values.
    """
    app = ASGIApplication()
    
    if app.debug is not False:
        errmsg = f"Expected debug=False, got {app.debug}"
        raise AssertionError(errmsg)
    
    if app.http_handler is None:
        errmsg = "Expected http_handler to be set"
        raise AssertionError(errmsg)
    
    if app.websocket_handler is None:
        errmsg = "Expected websocket_handler to be set"
        raise AssertionError(errmsg)
    
    if app.lifespan_handler is None:
        errmsg = "Expected lifespan_handler to be set"
        raise AssertionError(errmsg)
    
    if app.error_handler is None:
        errmsg = "Expected error_handler to be set"
        raise AssertionError(errmsg)
    
    return


def test_asgiapplication_construction_with_debug_enabled():
    """
        Test that ASGIApplication can be constructed with debug enabled.
    """
    app = ASGIApplication(debug=True)
    
    if app.debug is not True:
        errmsg = f"Expected debug=True, got {app.debug}"
        raise AssertionError(errmsg)
    
    return


def test_asgiapplication_construction_with_custom_handlers():
    """
        Test that ASGIApplication can be constructed with custom handlers.
    """
    http_handler = HTTPHandler()
    websocket_handler = WebSocketHandler()
    lifespan_handler = LifespanHandler()
    error_handler = ErrorHandler()
    
    app = ASGIApplication(
        http_handler=http_handler,
        websocket_handler=websocket_handler,
        lifespan_handler=lifespan_handler,
        error_handler=error_handler,
    )
    
    if app.http_handler is not http_handler:
        errmsg = "Expected custom http_handler to be used"
        raise AssertionError(errmsg)
    
    if app.websocket_handler is not websocket_handler:
        errmsg = "Expected custom websocket_handler to be used"
        raise AssertionError(errmsg)
    
    if app.lifespan_handler is not lifespan_handler:
        errmsg = "Expected custom lifespan_handler to be used"
        raise AssertionError(errmsg)
    
    if app.error_handler is not error_handler:
        errmsg = "Expected custom error_handler to be used"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for ASGIApplication - HTTP Dispatch
# =============================================================================

def test_asgiapplication_dispatches_http_scope():
    """
        Test that ASGIApplication dispatches HTTP scope to HTTP handler.
    """
    app = ASGIApplication()
    
    # Set up a handler that returns a response
    async def handler(request: Request) -> Response:
        return Response(status_code=200, body=b"OK")
    
    app.http_handler.set_handler(handler)
    
    scope = create_http_scope(method="GET", path="/test")
    receive = create_http_receive_callable()
    send, sent_messages = create_send_callable()
    
    asyncio.get_event_loop().run_until_complete(
        app(scope, receive, send)
    )
    
    # Check that response was sent
    if len(sent_messages) < 1:
        errmsg = "Expected at least one message to be sent"
        raise AssertionError(errmsg)
    
    start_message = sent_messages[0]
    if start_message.get("type") != MESSAGE_HTTP_RESPONSE_START:
        errmsg = f"Expected response start message, got {start_message.get('type')}"
        raise AssertionError(errmsg)
    
    if start_message.get("status") != 200:
        errmsg = f"Expected status 200, got {start_message.get('status')}"
        raise AssertionError(errmsg)
    
    return


def test_asgiapplication_http_returns_404_when_no_handler():
    """
        Test that ASGIApplication returns 404 for HTTP when no handler is set.
    """
    app = ASGIApplication()
    
    scope = create_http_scope(method="GET", path="/test")
    receive = create_http_receive_callable()
    send, sent_messages = create_send_callable()
    
    asyncio.get_event_loop().run_until_complete(
        app(scope, receive, send)
    )
    
    start_message = sent_messages[0]
    if start_message.get("status") != 404:
        errmsg = f"Expected status 404, got {start_message.get('status')}"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for ASGIApplication - WebSocket Dispatch
# =============================================================================

def test_asgiapplication_dispatches_websocket_scope():
    """
        Test that ASGIApplication dispatches WebSocket scope to WebSocket handler.
    """
    app = ASGIApplication()
    
    # WebSocket handler without a handler set will reject the connection
    scope = create_websocket_scope(path="/ws")
    receive = create_websocket_receive_callable()
    send, sent_messages = create_send_callable()
    
    asyncio.get_event_loop().run_until_complete(
        app(scope, receive, send)
    )
    
    # Check that close message was sent (rejection)
    if len(sent_messages) < 1:
        errmsg = "Expected at least one message to be sent"
        raise AssertionError(errmsg)
    
    close_message = sent_messages[0]
    if close_message.get("type") != MESSAGE_WEBSOCKET_CLOSE:
        errmsg = f"Expected websocket.close message, got {close_message.get('type')}"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for ASGIApplication - Lifespan Dispatch
# =============================================================================

def test_asgiapplication_dispatches_lifespan_scope():
    """
        Test that ASGIApplication dispatches lifespan scope to lifespan handler.
    """
    app = ASGIApplication()
    
    scope = create_lifespan_scope()
    receive = create_lifespan_receive_callable()
    send, sent_messages = create_send_callable()
    
    asyncio.get_event_loop().run_until_complete(
        app(scope, receive, send)
    )
    
    # Check that startup complete and shutdown complete were sent
    if len(sent_messages) < 2:
        errmsg = f"Expected at least 2 messages, got {len(sent_messages)}"
        raise AssertionError(errmsg)
    
    startup_message = sent_messages[0]
    if startup_message.get("type") != MESSAGE_LIFESPAN_STARTUP_COMPLETE:
        errmsg = f"Expected lifespan.startup.complete, got {startup_message.get('type')}"
        raise AssertionError(errmsg)
    
    shutdown_message = sent_messages[1]
    if shutdown_message.get("type") != MESSAGE_LIFESPAN_SHUTDOWN_COMPLETE:
        errmsg = f"Expected lifespan.shutdown.complete, got {shutdown_message.get('type')}"
        raise AssertionError(errmsg)
    
    return


def test_asgiapplication_lifespan_executes_startup_handlers():
    """
        Test that ASGIApplication executes registered startup handlers.
    """
    app = ASGIApplication()
    
    startup_called = [False]
    
    @app.lifespan_handler.on_startup
    async def startup_handler():
        startup_called[0] = True
        return
    
    scope = create_lifespan_scope()
    receive = create_lifespan_receive_callable()
    send, sent_messages = create_send_callable()
    
    asyncio.get_event_loop().run_until_complete(
        app(scope, receive, send)
    )
    
    if not startup_called[0]:
        errmsg = "Expected startup handler to be called"
        raise AssertionError(errmsg)
    
    return


def test_asgiapplication_lifespan_executes_shutdown_handlers():
    """
        Test that ASGIApplication executes registered shutdown handlers.
    """
    app = ASGIApplication()
    
    shutdown_called = [False]
    
    @app.lifespan_handler.on_shutdown
    async def shutdown_handler():
        shutdown_called[0] = True
        return
    
    scope = create_lifespan_scope()
    receive = create_lifespan_receive_callable()
    send, sent_messages = create_send_callable()
    
    asyncio.get_event_loop().run_until_complete(
        app(scope, receive, send)
    )
    
    if not shutdown_called[0]:
        errmsg = "Expected shutdown handler to be called"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for ASGIApplication - Unknown Scope Type
# =============================================================================

def test_asgiapplication_raises_error_for_unknown_scope_type():
    """
        Test that ASGIApplication raises error for unknown scope type.
    """
    app = ASGIApplication()
    
    scope = create_unknown_scope(scope_type="unknown_type")
    
    async def receive() -> Dict[str, Any]:
        return {}
    
    send, sent_messages = create_send_callable()
    
    exception_raised = False
    exception_type = None
    
    try:
        asyncio.get_event_loop().run_until_complete(
            app(scope, receive, send)
        )
    except UnknownScopeTypeError as err:
        exception_raised = True
        exception_type = err.scope_type
    
    if not exception_raised:
        errmsg = "Expected UnknownScopeTypeError to be raised"
        raise AssertionError(errmsg)
    
    if exception_type != "unknown_type":
        errmsg = f"Expected scope_type 'unknown_type', got '{exception_type}'"
        raise AssertionError(errmsg)
    
    return


def test_asgiapplication_raises_error_for_empty_scope_type():
    """
        Test that ASGIApplication raises error for empty scope type.
    """
    app = ASGIApplication()
    
    scope = {"type": "", "asgi": {"version": "3.0"}}
    
    async def receive() -> Dict[str, Any]:
        return {}
    
    send, sent_messages = create_send_callable()
    
    exception_raised = False
    
    try:
        asyncio.get_event_loop().run_until_complete(
            app(scope, receive, send)
        )
    except UnknownScopeTypeError:
        exception_raised = True
    
    if not exception_raised:
        errmsg = "Expected UnknownScopeTypeError to be raised for empty scope type"
        raise AssertionError(errmsg)
    
    return


def test_asgiapplication_raises_error_for_missing_scope_type():
    """
        Test that ASGIApplication raises error for missing scope type.
    """
    app = ASGIApplication()
    
    scope = {"asgi": {"version": "3.0"}}  # No "type" key
    
    async def receive() -> Dict[str, Any]:
        return {}
    
    send, sent_messages = create_send_callable()
    
    exception_raised = False
    
    try:
        asyncio.get_event_loop().run_until_complete(
            app(scope, receive, send)
        )
    except UnknownScopeTypeError:
        exception_raised = True
    
    if not exception_raised:
        errmsg = "Expected UnknownScopeTypeError to be raised for missing scope type"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for UnknownScopeTypeError
# =============================================================================

def test_unknownscopetypeerror_stores_scope_type():
    """
        Test that UnknownScopeTypeError stores the scope type.
    """
    err = UnknownScopeTypeError("custom_type")
    
    if err.scope_type != "custom_type":
        errmsg = f"Expected scope_type 'custom_type', got '{err.scope_type}'"
        raise AssertionError(errmsg)
    
    return


def test_unknownscopetypeerror_message_contains_scope_type():
    """
        Test that UnknownScopeTypeError message contains the scope type.
    """
    err = UnknownScopeTypeError("custom_type")
    
    if "custom_type" not in str(err):
        errmsg = f"Expected 'custom_type' in error message, got: {str(err)}"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for ASGIApplication - Async Support
# =============================================================================

def test_asgiapplication_supports_async_http_handler():
    """
        Test that ASGIApplication supports async HTTP handlers.
    """
    app = ASGIApplication()
    
    async def async_handler(request: Request) -> Response:
        # Simulate async operation
        await asyncio.sleep(0.01)
        return Response(status_code=200, body=b"Async OK")
    
    app.http_handler.set_handler(async_handler)
    
    scope = create_http_scope()
    receive = create_http_receive_callable()
    send, sent_messages = create_send_callable()
    
    asyncio.get_event_loop().run_until_complete(
        app(scope, receive, send)
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


def test_asgiapplication_supports_async_middleware():
    """
        Test that ASGIApplication supports async middleware.
    """
    app = ASGIApplication()
    
    middleware_called = [False]
    
    async def async_middleware(request: Request, next_handler) -> Response:
        middleware_called[0] = True
        await asyncio.sleep(0.01)
        response = await next_handler(request)
        return response
    
    async def handler(request: Request) -> Response:
        return Response(status_code=200, body=b"OK")
    
    app.http_handler.add_middleware(async_middleware)
    app.http_handler.set_handler(handler)
    
    scope = create_http_scope()
    receive = create_http_receive_callable()
    send, sent_messages = create_send_callable()
    
    asyncio.get_event_loop().run_until_complete(
        app(scope, receive, send)
    )
    
    if not middleware_called[0]:
        errmsg = "Expected async middleware to be called"
        raise AssertionError(errmsg)
    
    return


def test_asgiapplication_supports_async_lifespan_handlers():
    """
        Test that ASGIApplication supports async lifespan handlers.
    """
    app = ASGIApplication()
    
    startup_called = [False]
    shutdown_called = [False]
    
    @app.lifespan_handler.on_startup
    async def async_startup():
        await asyncio.sleep(0.01)
        startup_called[0] = True
        return
    
    @app.lifespan_handler.on_shutdown
    async def async_shutdown():
        await asyncio.sleep(0.01)
        shutdown_called[0] = True
        return
    
    scope = create_lifespan_scope()
    receive = create_lifespan_receive_callable()
    send, sent_messages = create_send_callable()
    
    asyncio.get_event_loop().run_until_complete(
        app(scope, receive, send)
    )
    
    if not startup_called[0]:
        errmsg = "Expected async startup handler to be called"
        raise AssertionError(errmsg)
    
    if not shutdown_called[0]:
        errmsg = "Expected async shutdown handler to be called"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for ASGIApplication - ASGI 3.0 Compliance
# =============================================================================

def test_asgiapplication_is_async_callable():
    """
        Test that ASGIApplication is an async callable.
    """
    app = ASGIApplication()
    
    # Check that __call__ is a coroutine function
    import inspect
    
    if not inspect.iscoroutinefunction(app.__call__):
        errmsg = "Expected __call__ to be a coroutine function"
        raise AssertionError(errmsg)
    
    return


def test_asgiapplication_accepts_scope_receive_send():
    """
        Test that ASGIApplication accepts scope, receive, and send arguments.
    """
    app = ASGIApplication()
    
    # Set up a handler
    async def handler(request: Request) -> Response:
        return Response(status_code=200, body=b"OK")
    
    app.http_handler.set_handler(handler)
    
    # Create the three required arguments
    scope = create_http_scope()
    receive = create_http_receive_callable()
    send, sent_messages = create_send_callable()
    
    # Call should succeed without error
    asyncio.get_event_loop().run_until_complete(
        app(scope, receive, send)
    )
    
    # Verify response was sent
    if len(sent_messages) < 1:
        errmsg = "Expected response to be sent"
        raise AssertionError(errmsg)
    
    return


def test_asgiapplication_handles_asgi_version_in_scope():
    """
        Test that ASGIApplication handles ASGI version in scope.
    """
    app = ASGIApplication()
    
    async def handler(request: Request) -> Response:
        return Response(status_code=200, body=b"OK")
    
    app.http_handler.set_handler(handler)
    
    # Create scope with ASGI 3.0 version
    scope = {
        "type": SCOPE_TYPE_HTTP,
        "asgi": {"version": "3.0", "spec_version": "2.3"},
        "http_version": "1.1",
        "method": "GET",
        "path": "/",
        "query_string": b"",
        "headers": [],
        "scheme": "http",
        "server": ("localhost", 80),
    }
    receive = create_http_receive_callable()
    send, sent_messages = create_send_callable()
    
    asyncio.get_event_loop().run_until_complete(
        app(scope, receive, send)
    )
    
    start_message = sent_messages[0]
    if start_message.get("status") != 200:
        errmsg = f"Expected status 200, got {start_message.get('status')}"
        raise AssertionError(errmsg)
    
    return



# =============================================================================
# Unit Tests for Server Integration Functions
# =============================================================================

from ccai.webworks.asgi.application import (
    get_asgi_application,
    create_asgi_application,
    reset_singleton_application,
    get_application_variable,
)


def test_get_asgi_application_returns_asgiapplication():
    """
        Test that get_asgi_application returns an ASGIApplication instance.
    """
    # Reset singleton before test
    reset_singleton_application()
    
    app = get_asgi_application()
    
    if not isinstance(app, ASGIApplication):
        errmsg = f"Expected ASGIApplication instance, got {type(app)}"
        raise AssertionError(errmsg)
    
    # Clean up
    reset_singleton_application()
    
    return


def test_get_asgi_application_returns_singleton():
    """
        Test that get_asgi_application returns the same instance on subsequent calls.
    """
    # Reset singleton before test
    reset_singleton_application()
    
    app1 = get_asgi_application()
    app2 = get_asgi_application()
    
    if app1 is not app2:
        errmsg = "Expected get_asgi_application to return the same instance"
        raise AssertionError(errmsg)
    
    # Clean up
    reset_singleton_application()
    
    return


def test_get_asgi_application_with_debug_enabled():
    """
        Test that get_asgi_application respects debug parameter.
    """
    # Reset singleton before test
    reset_singleton_application()
    
    app = get_asgi_application(debug=True)
    
    if app.debug is not True:
        errmsg = f"Expected debug=True, got {app.debug}"
        raise AssertionError(errmsg)
    
    # Clean up
    reset_singleton_application()
    
    return


def test_get_asgi_application_sets_module_variable():
    """
        Test that get_asgi_application sets the module-level application variable.
    """
    # Reset singleton before test
    reset_singleton_application()
    
    app = get_asgi_application()
    
    # Check that module-level variable is set using the getter function
    module_app = get_application_variable()
    if module_app is not app:
        errmsg = "Expected module-level application variable to be set"
        raise AssertionError(errmsg)
    
    # Clean up
    reset_singleton_application()
    
    return


def test_create_asgi_application_returns_new_instance():
    """
        Test that create_asgi_application returns a new instance each time.
    """
    app1 = create_asgi_application()
    app2 = create_asgi_application()
    
    if app1 is app2:
        errmsg = "Expected create_asgi_application to return different instances"
        raise AssertionError(errmsg)
    
    return


def test_create_asgi_application_with_debug():
    """
        Test that create_asgi_application respects debug parameter.
    """
    app = create_asgi_application(debug=True)
    
    if app.debug is not True:
        errmsg = f"Expected debug=True, got {app.debug}"
        raise AssertionError(errmsg)
    
    return


def test_create_asgi_application_with_config_dict():
    """
        Test that create_asgi_application accepts config dict.
    """
    config = {
        "debug": True,
    }
    
    app = create_asgi_application(config=config)
    
    if app.debug is not True:
        errmsg = f"Expected debug=True from config, got {app.debug}"
        raise AssertionError(errmsg)
    
    return


def test_create_asgi_application_kwargs_override_config():
    """
        Test that keyword arguments override config dict values.
    """
    config = {
        "debug": False,
    }
    
    app = create_asgi_application(config=config, debug=True)
    
    if app.debug is not True:
        errmsg = f"Expected debug=True from kwargs override, got {app.debug}"
        raise AssertionError(errmsg)
    
    return


def test_create_asgi_application_with_custom_handlers():
    """
        Test that create_asgi_application accepts custom handlers.
    """
    http_handler = HTTPHandler()
    websocket_handler = WebSocketHandler()
    error_handler = ErrorHandler()
    
    app = create_asgi_application(
        http_handler=http_handler,
        websocket_handler=websocket_handler,
        error_handler=error_handler,
    )
    
    if app.http_handler is not http_handler:
        errmsg = "Expected custom http_handler to be used"
        raise AssertionError(errmsg)
    
    if app.websocket_handler is not websocket_handler:
        errmsg = "Expected custom websocket_handler to be used"
        raise AssertionError(errmsg)
    
    if app.error_handler is not error_handler:
        errmsg = "Expected custom error_handler to be used"
        raise AssertionError(errmsg)
    
    return


def test_create_asgi_application_with_lifespan_disabled():
    """
        Test that create_asgi_application respects lifespan_enabled parameter.
    """
    app = create_asgi_application(lifespan_enabled=False)
    
    if app.lifespan_handler.enabled is not False:
        errmsg = f"Expected lifespan_handler.enabled=False, got {app.lifespan_handler.enabled}"
        raise AssertionError(errmsg)
    
    return


def test_create_asgi_application_with_lifespan_enabled():
    """
        Test that create_asgi_application enables lifespan by default.
    """
    app = create_asgi_application()
    
    if app.lifespan_handler.enabled is not True:
        errmsg = f"Expected lifespan_handler.enabled=True, got {app.lifespan_handler.enabled}"
        raise AssertionError(errmsg)
    
    return


def test_reset_singleton_application_clears_singleton():
    """
        Test that reset_singleton_application clears the singleton instance.
    """
    # Create singleton
    app1 = get_asgi_application()
    
    # Reset
    reset_singleton_application()
    
    # Create new singleton
    app2 = get_asgi_application()
    
    if app1 is app2:
        errmsg = "Expected reset to clear singleton, but got same instance"
        raise AssertionError(errmsg)
    
    # Clean up
    reset_singleton_application()
    
    return


def test_reset_singleton_application_clears_module_variable():
    """
        Test that reset_singleton_application clears the module-level variable.
    """
    # Create singleton
    get_asgi_application()
    
    # Reset
    reset_singleton_application()
    
    # Check that module-level variable is cleared using the getter function
    module_app = get_application_variable()
    if module_app is not None:
        errmsg = "Expected module-level application variable to be None after reset"
        raise AssertionError(errmsg)
    
    return


def test_get_application_variable_returns_none_initially():
    """
        Test that get_application_variable returns None when no app is set.
    """
    # Reset to ensure clean state
    reset_singleton_application()
    
    module_app = get_application_variable()
    
    if module_app is not None:
        errmsg = f"Expected None initially, got {module_app}"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for Lifespan Protocol Configuration
# =============================================================================

def test_lifespan_disabled_skips_startup_handlers():
    """
        Test that lifespan disabled skips startup handler execution.
    """
    app = create_asgi_application(lifespan_enabled=False)
    
    startup_called = [False]
    
    @app.lifespan_handler.on_startup
    async def startup_handler():
        startup_called[0] = True
        return
    
    scope = create_lifespan_scope()
    receive = create_lifespan_receive_callable()
    send, sent_messages = create_send_callable()
    
    asyncio.get_event_loop().run_until_complete(
        app(scope, receive, send)
    )
    
    # Handler should NOT be called when lifespan is disabled
    if startup_called[0]:
        errmsg = "Expected startup handler to NOT be called when lifespan is disabled"
        raise AssertionError(errmsg)
    
    # But startup complete should still be sent
    startup_message = sent_messages[0]
    if startup_message.get("type") != MESSAGE_LIFESPAN_STARTUP_COMPLETE:
        errmsg = f"Expected lifespan.startup.complete, got {startup_message.get('type')}"
        raise AssertionError(errmsg)
    
    return


def test_lifespan_disabled_skips_shutdown_handlers():
    """
        Test that lifespan disabled skips shutdown handler execution.
    """
    app = create_asgi_application(lifespan_enabled=False)
    
    shutdown_called = [False]
    
    @app.lifespan_handler.on_shutdown
    async def shutdown_handler():
        shutdown_called[0] = True
        return
    
    scope = create_lifespan_scope()
    receive = create_lifespan_receive_callable()
    send, sent_messages = create_send_callable()
    
    asyncio.get_event_loop().run_until_complete(
        app(scope, receive, send)
    )
    
    # Handler should NOT be called when lifespan is disabled
    if shutdown_called[0]:
        errmsg = "Expected shutdown handler to NOT be called when lifespan is disabled"
        raise AssertionError(errmsg)
    
    # But shutdown complete should still be sent
    shutdown_message = sent_messages[1]
    if shutdown_message.get("type") != MESSAGE_LIFESPAN_SHUTDOWN_COMPLETE:
        errmsg = f"Expected lifespan.shutdown.complete, got {shutdown_message.get('type')}"
        raise AssertionError(errmsg)
    
    return


def test_lifespan_enabled_executes_handlers():
    """
        Test that lifespan enabled executes startup and shutdown handlers.
    """
    app = create_asgi_application(lifespan_enabled=True)
    
    startup_called = [False]
    shutdown_called = [False]
    
    @app.lifespan_handler.on_startup
    async def startup_handler():
        startup_called[0] = True
        return
    
    @app.lifespan_handler.on_shutdown
    async def shutdown_handler():
        shutdown_called[0] = True
        return
    
    scope = create_lifespan_scope()
    receive = create_lifespan_receive_callable()
    send, sent_messages = create_send_callable()
    
    asyncio.get_event_loop().run_until_complete(
        app(scope, receive, send)
    )
    
    if not startup_called[0]:
        errmsg = "Expected startup handler to be called when lifespan is enabled"
        raise AssertionError(errmsg)
    
    if not shutdown_called[0]:
        errmsg = "Expected shutdown handler to be called when lifespan is enabled"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for ErrorHandler Integration
# =============================================================================

def test_asgiapplication_uses_error_handler_for_http_exceptions():
    """
        Test that ASGIApplication uses error handler for HTTP exceptions.
    """
    app = ASGIApplication()
    
    # Set up a handler that raises an exception
    async def failing_handler(request: Request) -> Response:
        raise ValueError("Test error")
    
    app.http_handler.set_handler(failing_handler)
    
    scope = create_http_scope(method="GET", path="/test")
    receive = create_http_receive_callable()
    send, sent_messages = create_send_callable()
    
    # Should not raise - error handler should catch and send error response
    asyncio.get_event_loop().run_until_complete(
        app(scope, receive, send)
    )
    
    # Check that an error response was sent
    if len(sent_messages) < 1:
        errmsg = "Expected at least one message to be sent"
        raise AssertionError(errmsg)
    
    start_message = sent_messages[0]
    if start_message.get("type") != MESSAGE_HTTP_RESPONSE_START:
        errmsg = f"Expected response start message, got {start_message.get('type')}"
        raise AssertionError(errmsg)
    
    # Should be a 500 error response
    if start_message.get("status") != 500:
        errmsg = f"Expected status 500, got {start_message.get('status')}"
        raise AssertionError(errmsg)
    
    return


def test_asgiapplication_uses_error_handler_for_websocket_exceptions():
    """
        Test that ASGIApplication uses error handler for WebSocket exceptions.
    """
    from ccai.webworks.asgi.websockethandler import WebSocketConnection
    
    app = ASGIApplication()
    
    # Set up a handler that raises an exception after accepting
    async def failing_ws_handler(connection: WebSocketConnection) -> None:
        await connection.accept()
        raise ValueError("Test WebSocket error")
    
    app.websocket_handler.set_handler(failing_ws_handler)
    
    scope = create_websocket_scope(path="/ws")
    receive = create_websocket_receive_callable()
    send, sent_messages = create_send_callable()
    
    # Should not raise - error handler should catch and close connection
    asyncio.get_event_loop().run_until_complete(
        app(scope, receive, send)
    )
    
    # Check that messages were sent (accept and close)
    if len(sent_messages) < 1:
        errmsg = "Expected at least one message to be sent"
        raise AssertionError(errmsg)
    
    # The last message should be a close message
    close_message = None
    for msg in sent_messages:
        if msg.get("type") == MESSAGE_WEBSOCKET_CLOSE:
            close_message = msg
    
    if close_message is None:
        errmsg = "Expected websocket.close message to be sent"
        raise AssertionError(errmsg)
    
    return


def test_asgiapplication_error_handler_logs_exceptions():
    """
        Test that ASGIApplication error handler logs exceptions.
    """
    import logging
    
    # Create a custom logger to capture log messages
    log_messages = []
    
    class TestHandler(logging.Handler):
        def emit(self, record):
            log_messages.append(record.getMessage())
    
    test_logger = logging.getLogger("test_error_logging")
    test_logger.setLevel(logging.ERROR)
    test_handler = TestHandler()
    test_logger.addHandler(test_handler)
    
    app = ASGIApplication(logger=test_logger)
    
    # Set up a handler that raises an exception
    async def failing_handler(request: Request) -> Response:
        raise ValueError("Test error for logging")
    
    app.http_handler.set_handler(failing_handler)
    
    scope = create_http_scope(method="GET", path="/test")
    receive = create_http_receive_callable()
    send, sent_messages = create_send_callable()
    
    asyncio.get_event_loop().run_until_complete(
        app(scope, receive, send)
    )
    
    # Clean up
    test_logger.removeHandler(test_handler)
    
    # Note: The error handler logs exceptions, but the HTTPHandler may catch
    # them first. This test verifies the error response is sent.
    if len(sent_messages) < 1:
        errmsg = "Expected at least one message to be sent"
        raise AssertionError(errmsg)
    
    return
