"""
    Property-Based Tests for ASGI Interface Compliance (Property 1).

    Property 1: ASGI Interface Compliance
    For any valid ASGI scope dictionary, receive callable, and send callable,
    the ASGIApplication SHALL be an async callable that handles the connection
    without raising unhandled exceptions, dispatching to the appropriate handler
    based on scope['type'].

    Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7
"""

import asyncio
import inspect
import random
import string
from typing import Any, Awaitable, Callable, Dict, List, Optional, Tuple

from ccai.webworks.asgi.application import ASGIApplication, UnknownScopeTypeError
from ccai.webworks.asgi.constants import (
    SCOPE_TYPE_HTTP,
    SCOPE_TYPE_WEBSOCKET,
    SCOPE_TYPE_LIFESPAN,
    MESSAGE_HTTP_REQUEST,
    MESSAGE_HTTP_RESPONSE_START,
    MESSAGE_HTTP_RESPONSE_BODY,
    MESSAGE_WEBSOCKET_CONNECT,
    MESSAGE_WEBSOCKET_CLOSE,
    MESSAGE_LIFESPAN_STARTUP,
    MESSAGE_LIFESPAN_STARTUP_COMPLETE,
    MESSAGE_LIFESPAN_SHUTDOWN,
    MESSAGE_LIFESPAN_SHUTDOWN_COMPLETE,
)


# =============================================================================
# Random Generators
# =============================================================================

VALID_HTTP_METHODS = ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS", "TRACE"]
VALID_HTTP_VERSIONS = ["1.0", "1.1", "2"]
VALID_SCHEMES_HTTP = ["http", "https"]
VALID_SCHEMES_WS = ["ws", "wss"]


def generate_random_string(min_length: int = 1, max_length: int = 20) -> str:
    """Generate a random alphanumeric string."""
    length = random.randint(min_length, max_length)
    chars = string.ascii_lowercase + string.digits
    rtnval = "".join(random.choice(chars) for _ in range(length))
    return rtnval


def generate_random_path() -> str:
    """Generate a random URL path."""
    num_segments = random.randint(0, 5)
    if num_segments == 0:
        rtnval = "/"
    else:
        segments = [generate_random_string(1, 15) for _ in range(num_segments)]
        rtnval = "/" + "/".join(segments)
    return rtnval


def generate_random_headers() -> List[Tuple[bytes, bytes]]:
    """Generate random ASGI-format headers as list of byte tuples."""
    common_names = [
        "accept", "content-type", "host", "user-agent", "x-request-id",
    ]
    num_headers = random.randint(0, 4)
    headers: List[Tuple[bytes, bytes]] = []
    used: set = set()
    for _ in range(num_headers):
        name = random.choice(common_names)
        if name in used:
            continue
        used.add(name)
        value = generate_random_string(1, 20)
        headers.append((name.encode("latin-1"), value.encode("latin-1")))
    return headers


def generate_random_server() -> Tuple[str, int]:
    """Generate a random server (host, port) tuple."""
    host = generate_random_string(3, 10) + ".example.com"
    port = random.choice([80, 443, 8000, 8080])
    return (host, port)


def generate_random_http_scope() -> Dict[str, Any]:
    """Generate a random valid ASGI HTTP scope."""
    scope: Dict[str, Any] = {
        "type": SCOPE_TYPE_HTTP,
        "asgi": {"version": "3.0"},
        "http_version": random.choice(VALID_HTTP_VERSIONS),
        "method": random.choice(VALID_HTTP_METHODS),
        "path": generate_random_path(),
        "query_string": generate_random_string(0, 30).encode("utf-8"),
        "headers": generate_random_headers(),
        "scheme": random.choice(VALID_SCHEMES_HTTP),
        "server": generate_random_server(),
    }
    if random.random() > 0.3:
        octets = [str(random.randint(1, 254)) for _ in range(4)]
        scope["client"] = (".".join(octets), random.randint(1024, 65535))
    return scope


def generate_random_websocket_scope() -> Dict[str, Any]:
    """Generate a random valid ASGI WebSocket scope."""
    scope: Dict[str, Any] = {
        "type": SCOPE_TYPE_WEBSOCKET,
        "asgi": {"version": "3.0"},
        "path": generate_random_path(),
        "query_string": generate_random_string(0, 20).encode("utf-8"),
        "headers": generate_random_headers(),
        "scheme": random.choice(VALID_SCHEMES_WS),
        "server": generate_random_server(),
        "subprotocols": [],
    }
    if random.random() > 0.3:
        octets = [str(random.randint(1, 254)) for _ in range(4)]
        scope["client"] = (".".join(octets), random.randint(1024, 65535))
    return scope


def generate_random_lifespan_scope() -> Dict[str, Any]:
    """Generate a random valid ASGI lifespan scope."""
    scope: Dict[str, Any] = {
        "type": SCOPE_TYPE_LIFESPAN,
        "asgi": {"version": "3.0"},
    }
    return scope


def generate_random_unknown_scope() -> Dict[str, Any]:
    """Generate a scope with a random unknown type."""
    unknown_type = generate_random_string(3, 15)
    # Ensure it does not collide with known types
    while unknown_type in (SCOPE_TYPE_HTTP, SCOPE_TYPE_WEBSOCKET, SCOPE_TYPE_LIFESPAN):
        unknown_type = generate_random_string(3, 15)
    scope: Dict[str, Any] = {
        "type": unknown_type,
        "asgi": {"version": "3.0"},
    }
    return scope


def create_http_receive(body: bytes = b"") -> Callable[[], Awaitable[Dict[str, Any]]]:
    """Create a receive callable for HTTP requests."""
    messages = [
        {"type": MESSAGE_HTTP_REQUEST, "body": body, "more_body": False},
    ]
    index = [0]

    async def receive() -> Dict[str, Any]:
        if index[0] < len(messages):
            msg = messages[index[0]]
            index[0] += 1
            return msg
        return {"type": MESSAGE_HTTP_REQUEST, "body": b"", "more_body": False}

    return receive


def create_websocket_receive() -> Callable[[], Awaitable[Dict[str, Any]]]:
    """Create a receive callable for WebSocket that connects then disconnects."""
    messages = [
        {"type": MESSAGE_WEBSOCKET_CONNECT},
    ]
    index = [0]

    async def receive() -> Dict[str, Any]:
        if index[0] < len(messages):
            msg = messages[index[0]]
            index[0] += 1
            return msg
        return {"type": "websocket.disconnect", "code": 1000}

    return receive


def create_lifespan_receive() -> Callable[[], Awaitable[Dict[str, Any]]]:
    """Create a receive callable for lifespan startup then shutdown."""
    messages = [
        {"type": MESSAGE_LIFESPAN_STARTUP},
        {"type": MESSAGE_LIFESPAN_SHUTDOWN},
    ]
    index = [0]

    async def receive() -> Dict[str, Any]:
        if index[0] < len(messages):
            msg = messages[index[0]]
            index[0] += 1
            return msg
        await asyncio.sleep(10)
        return {}

    return receive


def create_send_callable() -> Tuple[Callable, List[Dict[str, Any]]]:
    """Create a send callable that captures sent messages."""
    sent: List[Dict[str, Any]] = []

    async def send(message: Dict[str, Any]) -> None:
        sent.append(message)

    return (send, sent)


# =============================================================================
# Property-Based Tests
# =============================================================================

# Feature: asgi-layer, Property 1: ASGI Interface Compliance
# *For any* valid ASGI scope dictionary, receive callable, and send callable,
# the ASGIApplication SHALL be an async callable that handles the connection
# without raising unhandled exceptions, dispatching to the appropriate handler
# based on scope['type'].
# **Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7**


def test_property_1_asgi_application_is_async_callable():
    """
        Property 1: ASGI Application Is Async Callable

        The ASGIApplication __call__ method SHALL be a coroutine function
        accepting scope, receive, and send arguments, conforming to the
        ASGI 3.0 interface specification.

        **Validates: Requirements 1.1, 1.6, 1.7**
    """
    app = ASGIApplication()

    # Property: __call__ must be a coroutine function (Req 1.6)
    if not inspect.iscoroutinefunction(app.__call__):
        errmsg = "ASGIApplication.__call__ must be a coroutine function"
        raise AssertionError(errmsg)

    # Property: __call__ must accept exactly 3 parameters (scope, receive, send) (Req 1.1)
    sig = inspect.signature(app.__call__)
    params = [p for p in sig.parameters if p != "self"]
    if len(params) != 3:
        errmsg = (
            f"ASGIApplication.__call__ must accept 3 parameters "
            f"(scope, receive, send), got {len(params)}: {params}"
        )
        raise AssertionError(errmsg)

    # Property: parameter names should follow ASGI convention (Req 1.7)
    expected_names = ["scope", "receive", "send"]
    if params != expected_names:
        errmsg = (
            f"ASGIApplication.__call__ parameters should be {expected_names}, "
            f"got {params}"
        )
        raise AssertionError(errmsg)

    return


def test_property_1_http_scope_dispatches_to_http_handler():
    """
        Property 1: HTTP Scope Dispatch

        For any valid HTTP scope, the ASGIApplication SHALL dispatch to the
        HTTP handler and produce at least one response message without
        raising unhandled exceptions.

        **Validates: Requirements 1.1, 1.2, 1.6**
    """
    app = ASGIApplication()
    loop = asyncio.get_event_loop()

    for iteration in range(100):
        scope = generate_random_http_scope()
        receive = create_http_receive()
        send, sent_messages = create_send_callable()

        # Property: calling with HTTP scope must not raise unhandled exceptions
        try:
            loop.run_until_complete(app(scope, receive, send))
        except Exception as exc:
            errmsg = (
                f"Iteration {iteration}: HTTP scope raised unhandled exception "
                f"{type(exc).__name__}: {exc}"
            )
            raise AssertionError(errmsg)

        # Property: at least one message must be sent (response start) (Req 1.2)
        if len(sent_messages) < 1:
            errmsg = (
                f"Iteration {iteration}: HTTP scope produced no sent messages"
            )
            raise AssertionError(errmsg)

        # Property: first message must be http.response.start (Req 1.2)
        first_msg_type = sent_messages[0].get("type")
        if first_msg_type != MESSAGE_HTTP_RESPONSE_START:
            errmsg = (
                f"Iteration {iteration}: first message type should be "
                f"'{MESSAGE_HTTP_RESPONSE_START}', got '{first_msg_type}'"
            )
            raise AssertionError(errmsg)

        # Property: response start must include a status code (Req 1.2)
        status = sent_messages[0].get("status")
        if not isinstance(status, int):
            errmsg = (
                f"Iteration {iteration}: response start must include integer "
                f"status, got {type(status).__name__}: {status}"
            )
            raise AssertionError(errmsg)

    return


def test_property_1_websocket_scope_dispatches_to_websocket_handler():
    """
        Property 1: WebSocket Scope Dispatch

        For any valid WebSocket scope, the ASGIApplication SHALL dispatch to
        the WebSocket handler without raising unhandled exceptions.

        **Validates: Requirements 1.1, 1.3, 1.6**
    """
    app = ASGIApplication()
    loop = asyncio.get_event_loop()

    for iteration in range(100):
        scope = generate_random_websocket_scope()
        receive = create_websocket_receive()
        send, sent_messages = create_send_callable()

        # Property: calling with WebSocket scope must not raise unhandled exceptions
        try:
            loop.run_until_complete(app(scope, receive, send))
        except Exception as exc:
            errmsg = (
                f"Iteration {iteration}: WebSocket scope raised unhandled "
                f"exception {type(exc).__name__}: {exc}"
            )
            raise AssertionError(errmsg)

        # Property: at least one message must be sent (accept or close) (Req 1.3)
        if len(sent_messages) < 1:
            errmsg = (
                f"Iteration {iteration}: WebSocket scope produced no sent messages"
            )
            raise AssertionError(errmsg)

    return


def test_property_1_lifespan_scope_dispatches_to_lifespan_handler():
    """
        Property 1: Lifespan Scope Dispatch

        For any valid lifespan scope, the ASGIApplication SHALL dispatch to
        the lifespan handler and produce startup/shutdown completion messages
        without raising unhandled exceptions.

        **Validates: Requirements 1.1, 1.4, 1.6**
    """
    app = ASGIApplication()
    loop = asyncio.get_event_loop()

    for iteration in range(100):
        scope = generate_random_lifespan_scope()
        receive = create_lifespan_receive()
        send, sent_messages = create_send_callable()

        # Property: calling with lifespan scope must not raise unhandled exceptions
        try:
            loop.run_until_complete(app(scope, receive, send))
        except Exception as exc:
            errmsg = (
                f"Iteration {iteration}: lifespan scope raised unhandled "
                f"exception {type(exc).__name__}: {exc}"
            )
            raise AssertionError(errmsg)

        # Property: startup.complete or startup.failed must be sent (Req 1.4)
        startup_types = {MESSAGE_LIFESPAN_STARTUP_COMPLETE, "lifespan.startup.failed"}
        startup_msgs = [m for m in sent_messages if m.get("type") in startup_types]
        if len(startup_msgs) < 1:
            errmsg = (
                f"Iteration {iteration}: lifespan scope did not produce "
                f"startup complete/failed message"
            )
            raise AssertionError(errmsg)

        # Property: shutdown.complete or shutdown.failed must be sent (Req 1.4)
        shutdown_types = {MESSAGE_LIFESPAN_SHUTDOWN_COMPLETE, "lifespan.shutdown.failed"}
        shutdown_msgs = [m for m in sent_messages if m.get("type") in shutdown_types]
        if len(shutdown_msgs) < 1:
            errmsg = (
                f"Iteration {iteration}: lifespan scope did not produce "
                f"shutdown complete/failed message"
            )
            raise AssertionError(errmsg)

    return


def test_property_1_unknown_scope_raises_error():
    """
        Property 1: Unknown Scope Type Handling

        For any scope with an unknown type, the ASGIApplication SHALL raise
        an UnknownScopeTypeError containing the unrecognized scope type.

        **Validates: Requirements 1.1, 1.5**
    """
    app = ASGIApplication()
    loop = asyncio.get_event_loop()

    for iteration in range(100):
        scope = generate_random_unknown_scope()
        expected_type = scope["type"]

        async def dummy_receive() -> Dict[str, Any]:
            return {}

        async def dummy_send(message: Dict[str, Any]) -> None:
            return

        # Property: unknown scope type must raise UnknownScopeTypeError (Req 1.5)
        raised = False
        raised_type = None
        try:
            loop.run_until_complete(app(scope, dummy_receive, dummy_send))
        except UnknownScopeTypeError as exc:
            raised = True
            raised_type = exc.scope_type
        except Exception as exc:
            errmsg = (
                f"Iteration {iteration}: expected UnknownScopeTypeError, "
                f"got {type(exc).__name__}: {exc}"
            )
            raise AssertionError(errmsg)

        if not raised:
            errmsg = (
                f"Iteration {iteration}: unknown scope type '{expected_type}' "
                f"did not raise UnknownScopeTypeError"
            )
            raise AssertionError(errmsg)

        # Property: exception must contain the unknown scope type (Req 1.5)
        if raised_type != expected_type:
            errmsg = (
                f"Iteration {iteration}: UnknownScopeTypeError.scope_type "
                f"'{raised_type}' != expected '{expected_type}'"
            )
            raise AssertionError(errmsg)

    return


def test_property_1_dispatch_correctness_across_all_scope_types():
    """
        Property 1: Dispatch Correctness Across All Scope Types

        For any randomly chosen scope type from the set {http, websocket,
        lifespan, unknown}, the ASGIApplication SHALL dispatch to the
        correct handler. HTTP and WebSocket scopes produce response messages,
        lifespan scopes produce lifecycle messages, and unknown scopes raise
        UnknownScopeTypeError.

        **Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7**
    """
    app = ASGIApplication()
    loop = asyncio.get_event_loop()

    scope_generators = [
        ("http", generate_random_http_scope, create_http_receive),
        ("websocket", generate_random_websocket_scope, create_websocket_receive),
        ("lifespan", generate_random_lifespan_scope, create_lifespan_receive),
    ]

    for iteration in range(100):
        # Randomly pick a scope type including unknown
        choice = random.randint(0, 3)

        if choice < 3:
            scope_kind, gen_scope, gen_receive = scope_generators[choice]
            scope = gen_scope()
            receive = gen_receive()
            send, sent_messages = create_send_callable()

            try:
                loop.run_until_complete(app(scope, receive, send))
            except Exception as exc:
                errmsg = (
                    f"Iteration {iteration}: {scope_kind} scope raised "
                    f"unhandled exception {type(exc).__name__}: {exc}"
                )
                raise AssertionError(errmsg)

            # Property: known scope types must produce at least one sent message
            if len(sent_messages) < 1:
                errmsg = (
                    f"Iteration {iteration}: {scope_kind} scope produced "
                    f"no sent messages"
                )
                raise AssertionError(errmsg)

            # Property: scope type in scope dict must match expected type
            actual_type = scope.get("type")
            if scope_kind == "http" and actual_type != SCOPE_TYPE_HTTP:
                errmsg = f"Iteration {iteration}: HTTP scope type mismatch"
                raise AssertionError(errmsg)
            elif scope_kind == "websocket" and actual_type != SCOPE_TYPE_WEBSOCKET:
                errmsg = f"Iteration {iteration}: WebSocket scope type mismatch"
                raise AssertionError(errmsg)
            elif scope_kind == "lifespan" and actual_type != SCOPE_TYPE_LIFESPAN:
                errmsg = f"Iteration {iteration}: lifespan scope type mismatch"
                raise AssertionError(errmsg)

        else:
            # Unknown scope type
            scope = generate_random_unknown_scope()

            async def dummy_receive() -> Dict[str, Any]:
                return {}

            async def dummy_send(message: Dict[str, Any]) -> None:
                return

            raised = False
            try:
                loop.run_until_complete(app(scope, dummy_receive, dummy_send))
            except UnknownScopeTypeError:
                raised = True
            except Exception as exc:
                errmsg = (
                    f"Iteration {iteration}: unknown scope raised "
                    f"{type(exc).__name__} instead of UnknownScopeTypeError"
                )
                raise AssertionError(errmsg)

            if not raised:
                errmsg = (
                    f"Iteration {iteration}: unknown scope type "
                    f"'{scope.get('type')}' did not raise UnknownScopeTypeError"
                )
                raise AssertionError(errmsg)

    return


def test_property_1_asgi_version_in_scope_is_preserved():
    """
        Property 1: ASGI 3.0 Compatibility

        For any valid scope containing an asgi version key, the application
        SHALL process the scope without modifying or rejecting the version
        information, maintaining ASGI 3.0 compatibility.

        **Validates: Requirement 1.7**
    """
    app = ASGIApplication()
    loop = asyncio.get_event_loop()

    asgi_versions = [
        {"version": "3.0"},
        {"version": "3.0", "spec_version": "2.1"},
        {"version": "3.0", "spec_version": "2.3"},
    ]

    for iteration in range(100):
        scope = generate_random_http_scope()
        scope["asgi"] = random.choice(asgi_versions)
        original_asgi = dict(scope["asgi"])

        receive = create_http_receive()
        send, sent_messages = create_send_callable()

        try:
            loop.run_until_complete(app(scope, receive, send))
        except Exception as exc:
            errmsg = (
                f"Iteration {iteration}: ASGI version {original_asgi} "
                f"caused exception {type(exc).__name__}: {exc}"
            )
            raise AssertionError(errmsg)

        # Property: asgi key in scope must not be modified
        if scope.get("asgi") != original_asgi:
            errmsg = (
                f"Iteration {iteration}: asgi scope key was modified from "
                f"{original_asgi} to {scope.get('asgi')}"
            )
            raise AssertionError(errmsg)

    return
