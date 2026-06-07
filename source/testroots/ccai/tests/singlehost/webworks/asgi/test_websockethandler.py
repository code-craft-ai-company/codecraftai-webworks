"""
    Tests for the WebSocketHandler class.
    
    This module contains unit tests for the ASGI WebSocket handler functionality.
"""

import asyncio
from typing import Any, Awaitable, Callable, Dict, List, Optional

from ccai.webworks.asgi.websockethandler import (
    WebSocketHandler,
    WebSocketConnection,
)
from ccai.webworks.asgi.constants import (
    MESSAGE_WEBSOCKET_CONNECT,
    MESSAGE_WEBSOCKET_ACCEPT,
    MESSAGE_WEBSOCKET_RECEIVE,
    MESSAGE_WEBSOCKET_SEND,
    MESSAGE_WEBSOCKET_DISCONNECT,
    MESSAGE_WEBSOCKET_CLOSE,
    WS_CLOSE_NORMAL,
    WS_CLOSE_GOING_AWAY,
    WS_CLOSE_INTERNAL_ERROR,
)
from ccai.webworks.asgi.exceptions import (
    WebSocketError,
    ClientDisconnected,
)


# =============================================================================
# Test Helpers
# =============================================================================

def create_websocket_scope(
    path: str = "/ws",
    query_string: bytes = b"",
    headers: Optional[List[tuple]] = None,
    subprotocols: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
        Create a minimal WebSocket scope for testing.
    """
    if headers is None:
        headers = []
    
    if subprotocols is None:
        subprotocols = []
    
    scope = {
        "type": "websocket",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "path": path,
        "query_string": query_string,
        "headers": headers,
        "scheme": "ws",
        "server": ("localhost", 80),
        "subprotocols": subprotocols,
    }
    return scope


def create_receive_callable(
    messages: Optional[List[Dict[str, Any]]] = None,
) -> Callable[[], Awaitable[Dict[str, Any]]]:
    """
        Create a receive callable that returns messages in sequence.
    """
    if messages is None:
        messages = [{"type": MESSAGE_WEBSOCKET_CONNECT}]
    
    index = [0]
    
    async def receive() -> Dict[str, Any]:
        if index[0] < len(messages):
            msg = messages[index[0]]
            index[0] = index[0] + 1
            return msg
        # Return disconnect if called after all messages
        return {"type": MESSAGE_WEBSOCKET_DISCONNECT}
    
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
# Unit Tests for WebSocketConnection - Construction
# =============================================================================

def test_websocketconnection_construction():
    """
        Test that WebSocketConnection can be constructed.
    """
    scope = create_websocket_scope(path="/test")
    receive = create_receive_callable()
    send, _ = create_send_callable()
    
    connection = WebSocketConnection(scope, receive, send)
    
    if connection.path != "/test":
        errmsg = f"Expected path '/test', got '{connection.path}'"
        raise AssertionError(errmsg)
    
    if connection.is_accepted:
        errmsg = "Expected is_accepted=False"
        raise AssertionError(errmsg)
    
    if connection.is_closed:
        errmsg = "Expected is_closed=False"
        raise AssertionError(errmsg)
    
    return


def test_websocketconnection_properties():
    """
        Test WebSocketConnection property accessors.
    """
    scope = create_websocket_scope(
        path="/chat",
        query_string=b"room=123",
        headers=[
            (b"host", b"example.com"),
            (b"sec-websocket-protocol", b"chat"),
        ],
        subprotocols=["chat", "json"],
    )
    receive = create_receive_callable()
    send, _ = create_send_callable()
    
    connection = WebSocketConnection(scope, receive, send)
    
    if connection.path != "/chat":
        errmsg = f"Expected path '/chat', got '{connection.path}'"
        raise AssertionError(errmsg)
    
    if connection.query_string != "room=123":
        errmsg = f"Expected query_string 'room=123', got '{connection.query_string}'"
        raise AssertionError(errmsg)
    
    headers = connection.headers
    if headers.get("host") != "example.com":
        errmsg = f"Expected host 'example.com', got '{headers.get('host')}'"
        raise AssertionError(errmsg)
    
    if connection.subprotocols != ["chat", "json"]:
        errmsg = f"Expected subprotocols ['chat', 'json'], got {connection.subprotocols}"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for WebSocketConnection - Accept/Reject
# =============================================================================

def test_websocketconnection_accept():
    """
        Test that accept() sends websocket.accept message.
    """
    scope = create_websocket_scope()
    receive = create_receive_callable()
    send, sent_messages = create_send_callable()
    
    connection = WebSocketConnection(scope, receive, send)
    
    asyncio.get_event_loop().run_until_complete(
        connection.accept()
    )
    
    if len(sent_messages) != 1:
        errmsg = f"Expected 1 message sent, got {len(sent_messages)}"
        raise AssertionError(errmsg)
    
    msg = sent_messages[0]
    if msg.get("type") != MESSAGE_WEBSOCKET_ACCEPT:
        errmsg = f"Expected type '{MESSAGE_WEBSOCKET_ACCEPT}', got '{msg.get('type')}'"
        raise AssertionError(errmsg)
    
    if not connection.is_accepted:
        errmsg = "Expected is_accepted=True after accept()"
        raise AssertionError(errmsg)
    
    return


def test_websocketconnection_accept_with_subprotocol():
    """
        Test that accept() can specify a subprotocol.
    """
    scope = create_websocket_scope(subprotocols=["chat", "json"])
    receive = create_receive_callable()
    send, sent_messages = create_send_callable()
    
    connection = WebSocketConnection(scope, receive, send)
    
    asyncio.get_event_loop().run_until_complete(
        connection.accept(subprotocol="chat")
    )
    
    msg = sent_messages[0]
    if msg.get("subprotocol") != "chat":
        errmsg = f"Expected subprotocol 'chat', got '{msg.get('subprotocol')}'"
        raise AssertionError(errmsg)
    
    return


def test_websocketconnection_accept_with_headers():
    """
        Test that accept() can include additional headers.
    """
    scope = create_websocket_scope()
    receive = create_receive_callable()
    send, sent_messages = create_send_callable()
    
    connection = WebSocketConnection(scope, receive, send)
    
    custom_headers = [(b"x-custom", b"value")]
    asyncio.get_event_loop().run_until_complete(
        connection.accept(headers=custom_headers)
    )
    
    msg = sent_messages[0]
    if msg.get("headers") != custom_headers:
        errmsg = f"Expected headers {custom_headers}, got {msg.get('headers')}"
        raise AssertionError(errmsg)
    
    return


def test_websocketconnection_accept_twice_raises_error():
    """
        Test that calling accept() twice raises WebSocketError.
    """
    scope = create_websocket_scope()
    receive = create_receive_callable()
    send, _ = create_send_callable()
    
    connection = WebSocketConnection(scope, receive, send)
    
    asyncio.get_event_loop().run_until_complete(
        connection.accept()
    )
    
    try:
        asyncio.get_event_loop().run_until_complete(
            connection.accept()
        )
        errmsg = "Expected WebSocketError when accepting twice"
        raise AssertionError(errmsg)
    except WebSocketError:
        pass
    
    return


def test_websocketconnection_reject():
    """
        Test that reject() sends websocket.close message.
    """
    scope = create_websocket_scope()
    receive = create_receive_callable()
    send, sent_messages = create_send_callable()
    
    connection = WebSocketConnection(scope, receive, send)
    
    asyncio.get_event_loop().run_until_complete(
        connection.reject(code=403)
    )
    
    if len(sent_messages) != 1:
        errmsg = f"Expected 1 message sent, got {len(sent_messages)}"
        raise AssertionError(errmsg)
    
    msg = sent_messages[0]
    if msg.get("type") != MESSAGE_WEBSOCKET_CLOSE:
        errmsg = f"Expected type '{MESSAGE_WEBSOCKET_CLOSE}', got '{msg.get('type')}'"
        raise AssertionError(errmsg)
    
    if msg.get("code") != 403:
        errmsg = f"Expected code 403, got {msg.get('code')}"
        raise AssertionError(errmsg)
    
    if not connection.is_closed:
        errmsg = "Expected is_closed=True after reject()"
        raise AssertionError(errmsg)
    
    return


def test_websocketconnection_reject_after_accept_raises_error():
    """
        Test that calling reject() after accept() raises WebSocketError.
    """
    scope = create_websocket_scope()
    receive = create_receive_callable()
    send, _ = create_send_callable()
    
    connection = WebSocketConnection(scope, receive, send)
    
    asyncio.get_event_loop().run_until_complete(
        connection.accept()
    )
    
    try:
        asyncio.get_event_loop().run_until_complete(
            connection.reject()
        )
        errmsg = "Expected WebSocketError when rejecting after accept"
        raise AssertionError(errmsg)
    except WebSocketError:
        pass
    
    return


# =============================================================================
# Unit Tests for WebSocketConnection - Message Sending
# =============================================================================

def test_websocketconnection_send_text():
    """
        Test that send_text() sends a text message.
    """
    scope = create_websocket_scope()
    receive = create_receive_callable()
    send, sent_messages = create_send_callable()
    
    connection = WebSocketConnection(scope, receive, send)
    
    asyncio.get_event_loop().run_until_complete(
        connection.accept()
    )
    
    asyncio.get_event_loop().run_until_complete(
        connection.send_text("Hello, World!")
    )
    
    if len(sent_messages) != 2:
        errmsg = f"Expected 2 messages sent, got {len(sent_messages)}"
        raise AssertionError(errmsg)
    
    msg = sent_messages[1]
    if msg.get("type") != MESSAGE_WEBSOCKET_SEND:
        errmsg = f"Expected type '{MESSAGE_WEBSOCKET_SEND}', got '{msg.get('type')}'"
        raise AssertionError(errmsg)
    
    if msg.get("text") != "Hello, World!":
        errmsg = f"Expected text 'Hello, World!', got '{msg.get('text')}'"
        raise AssertionError(errmsg)
    
    return


def test_websocketconnection_send_bytes():
    """
        Test that send_bytes() sends a binary message.
    """
    scope = create_websocket_scope()
    receive = create_receive_callable()
    send, sent_messages = create_send_callable()
    
    connection = WebSocketConnection(scope, receive, send)
    
    asyncio.get_event_loop().run_until_complete(
        connection.accept()
    )
    
    asyncio.get_event_loop().run_until_complete(
        connection.send_bytes(b"\x00\x01\x02\x03")
    )
    
    if len(sent_messages) != 2:
        errmsg = f"Expected 2 messages sent, got {len(sent_messages)}"
        raise AssertionError(errmsg)
    
    msg = sent_messages[1]
    if msg.get("type") != MESSAGE_WEBSOCKET_SEND:
        errmsg = f"Expected type '{MESSAGE_WEBSOCKET_SEND}', got '{msg.get('type')}'"
        raise AssertionError(errmsg)
    
    if msg.get("bytes") != b"\x00\x01\x02\x03":
        errmsg = f"Expected bytes, got '{msg.get('bytes')}'"
        raise AssertionError(errmsg)
    
    return


def test_websocketconnection_send_text_before_accept_raises_error():
    """
        Test that send_text() before accept() raises WebSocketError.
    """
    scope = create_websocket_scope()
    receive = create_receive_callable()
    send, _ = create_send_callable()
    
    connection = WebSocketConnection(scope, receive, send)
    
    try:
        asyncio.get_event_loop().run_until_complete(
            connection.send_text("Hello")
        )
        errmsg = "Expected WebSocketError when sending before accept"
        raise AssertionError(errmsg)
    except WebSocketError:
        pass
    
    return


def test_websocketconnection_send_bytes_before_accept_raises_error():
    """
        Test that send_bytes() before accept() raises WebSocketError.
    """
    scope = create_websocket_scope()
    receive = create_receive_callable()
    send, _ = create_send_callable()
    
    connection = WebSocketConnection(scope, receive, send)
    
    try:
        asyncio.get_event_loop().run_until_complete(
            connection.send_bytes(b"data")
        )
        errmsg = "Expected WebSocketError when sending before accept"
        raise AssertionError(errmsg)
    except WebSocketError:
        pass
    
    return


def test_websocketconnection_send_after_close_raises_error():
    """
        Test that sending after close() raises WebSocketError.
    """
    scope = create_websocket_scope()
    receive = create_receive_callable()
    send, _ = create_send_callable()
    
    connection = WebSocketConnection(scope, receive, send)
    
    asyncio.get_event_loop().run_until_complete(
        connection.accept()
    )
    
    asyncio.get_event_loop().run_until_complete(
        connection.close()
    )
    
    try:
        asyncio.get_event_loop().run_until_complete(
            connection.send_text("Hello")
        )
        errmsg = "Expected WebSocketError when sending after close"
        raise AssertionError(errmsg)
    except WebSocketError:
        pass
    
    return


# =============================================================================
# Unit Tests for WebSocketConnection - Message Receiving
# =============================================================================

def test_websocketconnection_receive_text_message():
    """
        Test that receive_message() returns text messages.
    """
    scope = create_websocket_scope()
    messages = [
        {"type": MESSAGE_WEBSOCKET_CONNECT},
        {"type": MESSAGE_WEBSOCKET_RECEIVE, "text": "Hello from client"},
    ]
    receive = create_receive_callable(messages)
    send, _ = create_send_callable()
    
    connection = WebSocketConnection(scope, receive, send)
    
    # Consume the connect message
    asyncio.get_event_loop().run_until_complete(receive())
    
    asyncio.get_event_loop().run_until_complete(
        connection.accept()
    )
    
    result = asyncio.get_event_loop().run_until_complete(
        connection.receive_message()
    )
    
    if result != "Hello from client":
        errmsg = f"Expected 'Hello from client', got '{result}'"
        raise AssertionError(errmsg)
    
    return


def test_websocketconnection_receive_bytes_message():
    """
        Test that receive_message() returns binary messages.
    """
    scope = create_websocket_scope()
    messages = [
        {"type": MESSAGE_WEBSOCKET_CONNECT},
        {"type": MESSAGE_WEBSOCKET_RECEIVE, "bytes": b"\x00\x01\x02"},
    ]
    receive = create_receive_callable(messages)
    send, _ = create_send_callable()
    
    connection = WebSocketConnection(scope, receive, send)
    
    # Consume the connect message
    asyncio.get_event_loop().run_until_complete(receive())
    
    asyncio.get_event_loop().run_until_complete(
        connection.accept()
    )
    
    result = asyncio.get_event_loop().run_until_complete(
        connection.receive_message()
    )
    
    if result != b"\x00\x01\x02":
        errmsg = f"Expected bytes, got '{result}'"
        raise AssertionError(errmsg)
    
    return


def test_websocketconnection_receive_before_accept_raises_error():
    """
        Test that receive_message() before accept() raises WebSocketError.
    """
    scope = create_websocket_scope()
    receive = create_receive_callable()
    send, _ = create_send_callable()
    
    connection = WebSocketConnection(scope, receive, send)
    
    try:
        asyncio.get_event_loop().run_until_complete(
            connection.receive_message()
        )
        errmsg = "Expected WebSocketError when receiving before accept"
        raise AssertionError(errmsg)
    except WebSocketError:
        pass
    
    return


def test_websocketconnection_receive_disconnect_raises_client_disconnected():
    """
        Test that receive_message() raises ClientDisconnected on disconnect.
    """
    scope = create_websocket_scope()
    messages = [
        {"type": MESSAGE_WEBSOCKET_CONNECT},
        {"type": MESSAGE_WEBSOCKET_DISCONNECT},
    ]
    receive = create_receive_callable(messages)
    send, _ = create_send_callable()
    
    connection = WebSocketConnection(scope, receive, send)
    
    # Consume the connect message
    asyncio.get_event_loop().run_until_complete(receive())
    
    asyncio.get_event_loop().run_until_complete(
        connection.accept()
    )
    
    try:
        asyncio.get_event_loop().run_until_complete(
            connection.receive_message()
        )
        errmsg = "Expected ClientDisconnected on disconnect"
        raise AssertionError(errmsg)
    except ClientDisconnected:
        pass
    
    if not connection.is_closed:
        errmsg = "Expected is_closed=True after disconnect"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for WebSocketConnection - Close
# =============================================================================

def test_websocketconnection_close():
    """
        Test that close() sends websocket.close message.
    """
    scope = create_websocket_scope()
    receive = create_receive_callable()
    send, sent_messages = create_send_callable()
    
    connection = WebSocketConnection(scope, receive, send)
    
    asyncio.get_event_loop().run_until_complete(
        connection.accept()
    )
    
    asyncio.get_event_loop().run_until_complete(
        connection.close(code=WS_CLOSE_NORMAL, reason="Goodbye")
    )
    
    if len(sent_messages) != 2:
        errmsg = f"Expected 2 messages sent, got {len(sent_messages)}"
        raise AssertionError(errmsg)
    
    msg = sent_messages[1]
    if msg.get("type") != MESSAGE_WEBSOCKET_CLOSE:
        errmsg = f"Expected type '{MESSAGE_WEBSOCKET_CLOSE}', got '{msg.get('type')}'"
        raise AssertionError(errmsg)
    
    if msg.get("code") != WS_CLOSE_NORMAL:
        errmsg = f"Expected code {WS_CLOSE_NORMAL}, got {msg.get('code')}"
        raise AssertionError(errmsg)
    
    if msg.get("reason") != "Goodbye":
        errmsg = f"Expected reason 'Goodbye', got '{msg.get('reason')}'"
        raise AssertionError(errmsg)
    
    if not connection.is_closed:
        errmsg = "Expected is_closed=True after close()"
        raise AssertionError(errmsg)
    
    return


def test_websocketconnection_close_twice_is_safe():
    """
        Test that calling close() twice is safe (no error).
    """
    scope = create_websocket_scope()
    receive = create_receive_callable()
    send, sent_messages = create_send_callable()
    
    connection = WebSocketConnection(scope, receive, send)
    
    asyncio.get_event_loop().run_until_complete(
        connection.accept()
    )
    
    asyncio.get_event_loop().run_until_complete(
        connection.close()
    )
    
    # Second close should not raise
    asyncio.get_event_loop().run_until_complete(
        connection.close()
    )
    
    # Only one close message should be sent
    close_messages = [m for m in sent_messages if m.get("type") == MESSAGE_WEBSOCKET_CLOSE]
    if len(close_messages) != 1:
        errmsg = f"Expected 1 close message, got {len(close_messages)}"
        raise AssertionError(errmsg)
    
    return


def test_websocketconnection_close_without_accept():
    """
        Test that close() works without prior accept().
    """
    scope = create_websocket_scope()
    receive = create_receive_callable()
    send, sent_messages = create_send_callable()
    
    connection = WebSocketConnection(scope, receive, send)
    
    asyncio.get_event_loop().run_until_complete(
        connection.close(code=WS_CLOSE_GOING_AWAY)
    )
    
    if len(sent_messages) != 1:
        errmsg = f"Expected 1 message sent, got {len(sent_messages)}"
        raise AssertionError(errmsg)
    
    msg = sent_messages[0]
    if msg.get("type") != MESSAGE_WEBSOCKET_CLOSE:
        errmsg = f"Expected type '{MESSAGE_WEBSOCKET_CLOSE}', got '{msg.get('type')}'"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for WebSocketHandler - Construction
# =============================================================================

def test_websockethandler_construction_with_defaults():
    """
        Test that WebSocketHandler can be constructed with default values.
    """
    handler = WebSocketHandler()
    
    if handler.debug is not False:
        errmsg = f"Expected debug=False, got {handler.debug}"
        raise AssertionError(errmsg)
    
    return


def test_websockethandler_construction_with_debug():
    """
        Test that WebSocketHandler can be constructed with debug=True.
    """
    handler = WebSocketHandler(debug=True)
    
    if handler.debug is not True:
        errmsg = f"Expected debug=True, got {handler.debug}"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for WebSocketHandler - Handler Setting
# =============================================================================

def test_websockethandler_set_handler():
    """
        Test that set_handler sets the WebSocket handler.
    """
    handler = WebSocketHandler()
    
    async def my_handler(connection: WebSocketConnection) -> None:
        await connection.accept()
        return
    
    handler.set_handler(my_handler)
    
    # Handler is set internally, we verify by running handle()
    # This test just ensures no exception is raised
    return


# =============================================================================
# Unit Tests for WebSocketHandler - Connection Handling
# =============================================================================

def test_websockethandler_handle_receives_connect_event():
    """
        Test that handle() receives the websocket.connect event.
    """
    handler = WebSocketHandler()
    
    connect_received = [False]
    
    async def my_handler(connection: WebSocketConnection) -> None:
        connect_received[0] = True
        await connection.accept()
        return
    
    handler.set_handler(my_handler)
    
    scope = create_websocket_scope()
    receive = create_receive_callable()
    send, _ = create_send_callable()
    
    asyncio.get_event_loop().run_until_complete(
        handler.handle(scope, receive, send)
    )
    
    if not connect_received[0]:
        errmsg = "Expected handler to be called after connect event"
        raise AssertionError(errmsg)
    
    return


def test_websockethandler_handle_rejects_when_no_handler():
    """
        Test that handle() rejects connection when no handler is set.
    """
    handler = WebSocketHandler()
    
    scope = create_websocket_scope()
    receive = create_receive_callable()
    send, sent_messages = create_send_callable()
    
    asyncio.get_event_loop().run_until_complete(
        handler.handle(scope, receive, send)
    )
    
    if len(sent_messages) != 1:
        errmsg = f"Expected 1 message sent, got {len(sent_messages)}"
        raise AssertionError(errmsg)
    
    msg = sent_messages[0]
    if msg.get("type") != MESSAGE_WEBSOCKET_CLOSE:
        errmsg = f"Expected type '{MESSAGE_WEBSOCKET_CLOSE}', got '{msg.get('type')}'"
        raise AssertionError(errmsg)
    
    if msg.get("code") != 403:
        errmsg = f"Expected code 403, got {msg.get('code')}"
        raise AssertionError(errmsg)
    
    return


def test_websockethandler_handle_passes_connection_to_handler():
    """
        Test that handle() passes the connection to the handler.
    """
    handler = WebSocketHandler()
    
    received_connection = [None]
    
    async def my_handler(connection: WebSocketConnection) -> None:
        received_connection[0] = connection
        await connection.accept()
        return
    
    handler.set_handler(my_handler)
    
    scope = create_websocket_scope(path="/chat")
    receive = create_receive_callable()
    send, _ = create_send_callable()
    
    asyncio.get_event_loop().run_until_complete(
        handler.handle(scope, receive, send)
    )
    
    connection = received_connection[0]
    if connection is None:
        errmsg = "Expected connection to be passed to handler"
        raise AssertionError(errmsg)
    
    if connection.path != "/chat":
        errmsg = f"Expected path '/chat', got '{connection.path}'"
        raise AssertionError(errmsg)
    
    return


def test_websockethandler_handle_closes_connection_after_handler():
    """
        Test that handle() closes connection after handler completes.
    """
    handler = WebSocketHandler()
    
    async def my_handler(connection: WebSocketConnection) -> None:
        await connection.accept()
        # Handler completes without closing
        return
    
    handler.set_handler(my_handler)
    
    scope = create_websocket_scope()
    receive = create_receive_callable()
    send, sent_messages = create_send_callable()
    
    asyncio.get_event_loop().run_until_complete(
        handler.handle(scope, receive, send)
    )
    
    # Should have accept and close messages
    close_messages = [m for m in sent_messages if m.get("type") == MESSAGE_WEBSOCKET_CLOSE]
    if len(close_messages) != 1:
        errmsg = f"Expected 1 close message, got {len(close_messages)}"
        raise AssertionError(errmsg)
    
    return


def test_websockethandler_handle_gracefully_handles_client_disconnect():
    """
        Test that handle() gracefully handles client disconnection.
    """
    handler = WebSocketHandler()
    
    async def my_handler(connection: WebSocketConnection) -> None:
        await connection.accept()
        # This will raise ClientDisconnected
        await connection.receive_message()
        return
    
    handler.set_handler(my_handler)
    
    scope = create_websocket_scope()
    messages = [
        {"type": MESSAGE_WEBSOCKET_CONNECT},
        {"type": MESSAGE_WEBSOCKET_DISCONNECT},
    ]
    receive = create_receive_callable(messages)
    send, _ = create_send_callable()
    
    # Should not raise an exception
    asyncio.get_event_loop().run_until_complete(
        handler.handle(scope, receive, send)
    )
    
    return


# =============================================================================
# Unit Tests for WebSocketHandler - Error Handling
# =============================================================================

def test_websockethandler_handle_closes_on_websocket_error():
    """
        Test that handle() closes connection on WebSocketError.
    """
    handler = WebSocketHandler()
    
    async def my_handler(connection: WebSocketConnection) -> None:
        await connection.accept()
        raise WebSocketError(code=1008, reason="Policy violation")
    
    handler.set_handler(my_handler)
    
    scope = create_websocket_scope()
    receive = create_receive_callable()
    send, sent_messages = create_send_callable()
    
    asyncio.get_event_loop().run_until_complete(
        handler.handle(scope, receive, send)
    )
    
    close_messages = [m for m in sent_messages if m.get("type") == MESSAGE_WEBSOCKET_CLOSE]
    if len(close_messages) != 1:
        errmsg = f"Expected 1 close message, got {len(close_messages)}"
        raise AssertionError(errmsg)
    
    msg = close_messages[0]
    if msg.get("code") != 1008:
        errmsg = f"Expected code 1008, got {msg.get('code')}"
        raise AssertionError(errmsg)
    
    return


def test_websockethandler_handle_closes_on_unhandled_exception():
    """
        Test that handle() closes connection on unhandled exception.
    """
    handler = WebSocketHandler()
    
    async def my_handler(connection: WebSocketConnection) -> None:
        await connection.accept()
        raise ValueError("Something went wrong")
    
    handler.set_handler(my_handler)
    
    scope = create_websocket_scope()
    receive = create_receive_callable()
    send, sent_messages = create_send_callable()
    
    asyncio.get_event_loop().run_until_complete(
        handler.handle(scope, receive, send)
    )
    
    close_messages = [m for m in sent_messages if m.get("type") == MESSAGE_WEBSOCKET_CLOSE]
    if len(close_messages) != 1:
        errmsg = f"Expected 1 close message, got {len(close_messages)}"
        raise AssertionError(errmsg)
    
    msg = close_messages[0]
    if msg.get("code") != WS_CLOSE_INTERNAL_ERROR:
        errmsg = f"Expected code {WS_CLOSE_INTERNAL_ERROR}, got {msg.get('code')}"
        raise AssertionError(errmsg)
    
    return


def test_websockethandler_handle_includes_debug_info_when_debug_enabled():
    """
        Test that handle() includes debug info in close reason when debug=True.
    """
    handler = WebSocketHandler(debug=True)
    
    async def my_handler(connection: WebSocketConnection) -> None:
        await connection.accept()
        raise ValueError("Test error message")
    
    handler.set_handler(my_handler)
    
    scope = create_websocket_scope()
    receive = create_receive_callable()
    send, sent_messages = create_send_callable()
    
    asyncio.get_event_loop().run_until_complete(
        handler.handle(scope, receive, send)
    )
    
    close_messages = [m for m in sent_messages if m.get("type") == MESSAGE_WEBSOCKET_CLOSE]
    msg = close_messages[0]
    reason = msg.get("reason", "")
    
    if "ValueError" not in reason:
        errmsg = f"Expected 'ValueError' in reason, got '{reason}'"
        raise AssertionError(errmsg)
    
    if "Test error message" not in reason:
        errmsg = f"Expected 'Test error message' in reason, got '{reason}'"
        raise AssertionError(errmsg)
    
    return


def test_websockethandler_handle_hides_debug_info_when_debug_disabled():
    """
        Test that handle() hides debug info in close reason when debug=False.
    """
    handler = WebSocketHandler(debug=False)
    
    async def my_handler(connection: WebSocketConnection) -> None:
        await connection.accept()
        raise ValueError("Secret error message")
    
    handler.set_handler(my_handler)
    
    scope = create_websocket_scope()
    receive = create_receive_callable()
    send, sent_messages = create_send_callable()
    
    asyncio.get_event_loop().run_until_complete(
        handler.handle(scope, receive, send)
    )
    
    close_messages = [m for m in sent_messages if m.get("type") == MESSAGE_WEBSOCKET_CLOSE]
    msg = close_messages[0]
    reason = msg.get("reason", "")
    
    if "Secret error message" in reason:
        errmsg = f"Did not expect error details in reason: {reason}"
        raise AssertionError(errmsg)
    
    if "ValueError" in reason:
        errmsg = f"Did not expect exception type in reason: {reason}"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for WebSocketHandler - Message Loop
# =============================================================================

def test_websockethandler_handle_supports_message_loop():
    """
        Test that handle() supports a message loop pattern.
    """
    handler = WebSocketHandler()
    
    received_messages: List[str] = []
    
    async def my_handler(connection: WebSocketConnection) -> None:
        await connection.accept()
        
        try:
            while True:
                msg = await connection.receive_message()
                if isinstance(msg, str):
                    received_messages.append(msg)
                    await connection.send_text(f"Echo: {msg}")
        except ClientDisconnected:
            pass
        
        return
    
    handler.set_handler(my_handler)
    
    scope = create_websocket_scope()
    messages = [
        {"type": MESSAGE_WEBSOCKET_CONNECT},
        {"type": MESSAGE_WEBSOCKET_RECEIVE, "text": "Hello"},
        {"type": MESSAGE_WEBSOCKET_RECEIVE, "text": "World"},
        {"type": MESSAGE_WEBSOCKET_DISCONNECT},
    ]
    receive = create_receive_callable(messages)
    send, sent_messages = create_send_callable()
    
    asyncio.get_event_loop().run_until_complete(
        handler.handle(scope, receive, send)
    )
    
    if received_messages != ["Hello", "World"]:
        errmsg = f"Expected ['Hello', 'World'], got {received_messages}"
        raise AssertionError(errmsg)
    
    # Check echo responses were sent
    send_messages = [m for m in sent_messages if m.get("type") == MESSAGE_WEBSOCKET_SEND]
    if len(send_messages) != 2:
        errmsg = f"Expected 2 send messages, got {len(send_messages)}"
        raise AssertionError(errmsg)
    
    if send_messages[0].get("text") != "Echo: Hello":
        errmsg = f"Expected 'Echo: Hello', got '{send_messages[0].get('text')}'"
        raise AssertionError(errmsg)
    
    if send_messages[1].get("text") != "Echo: World":
        errmsg = f"Expected 'Echo: World', got '{send_messages[1].get('text')}'"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Property-Based Test Helpers
# =============================================================================

import random
import string


def generate_random_string(min_length: int = 1, max_length: int = 20) -> str:
    """
        Generate a random alphanumeric string.
    """
    length = random.randint(min_length, max_length)
    chars = string.ascii_lowercase + string.digits
    rtnval = "".join(random.choice(chars) for _ in range(length))
    return rtnval


def generate_random_path() -> str:
    """
        Generate a random WebSocket path.
    """
    num_segments = random.randint(1, 4)
    segments = [generate_random_string(1, 10) for _ in range(num_segments)]
    rtnval = "/" + "/".join(segments)
    return rtnval


def generate_random_query_string() -> bytes:
    """
        Generate a random query string as bytes.
    """
    num_params = random.randint(0, 3)
    if num_params == 0:
        return b""
    
    params = []
    for _ in range(num_params):
        key = generate_random_string(1, 8)
        value = generate_random_string(1, 10)
        params.append(f"{key}={value}")
    
    rtnval = "&".join(params).encode("utf-8")
    return rtnval


def generate_random_headers() -> List[tuple]:
    """
        Generate random WebSocket headers as byte tuples.
    """
    num_headers = random.randint(0, 4)
    headers: List[tuple] = []
    
    header_names = [
        "host", "origin", "user-agent", "x-request-id",
        "x-custom-header", "accept-language",
    ]
    
    used_names: set = set()
    for _ in range(num_headers):
        name = random.choice(header_names)
        if name in used_names:
            continue
        used_names.add(name)
        value = generate_random_string(1, 20)
        headers.append((name.encode("utf-8"), value.encode("utf-8")))
    
    return headers


COMMON_SUBPROTOCOLS = ["chat", "json", "graphql-ws", "mqtt", "wamp"]


def generate_random_subprotocols() -> List[str]:
    """
        Generate a random list of subprotocols.
    """
    num = random.randint(0, 3)
    if num == 0:
        return []
    
    rtnval = random.sample(COMMON_SUBPROTOCOLS, min(num, len(COMMON_SUBPROTOCOLS)))
    return rtnval


def generate_random_text_messages(count: int) -> List[str]:
    """
        Generate a list of random text messages.
    """
    rtnval = [generate_random_string(1, 50) for _ in range(count)]
    return rtnval


def generate_random_binary_messages(count: int) -> List[bytes]:
    """
        Generate a list of random binary messages.
    """
    rtnval = []
    for _ in range(count):
        length = random.randint(1, 100)
        data = bytes(random.randint(0, 255) for _ in range(length))
        rtnval.append(data)
    return rtnval


def generate_random_websocket_scope() -> Dict[str, Any]:
    """
        Generate a random valid WebSocket scope dictionary.
    """
    scope = create_websocket_scope(
        path=generate_random_path(),
        query_string=generate_random_query_string(),
        headers=generate_random_headers(),
        subprotocols=generate_random_subprotocols(),
    )
    return scope


# =============================================================================
# Property-Based Tests
# =============================================================================

# Feature: asgi-layer, Property 7: WebSocket Connection Lifecycle
# *For any* WebSocket connection, the application SHALL receive
# "websocket.connect" before any messages, SHALL send either
# "websocket.accept" or "websocket.close" in response, and after accept
# SHALL handle "websocket.receive" and "websocket.send" messages until
# "websocket.disconnect" is received or "websocket.close" is sent.
# **Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8, 5.9, 5.10, 5.11**


def test_property_7_accept_lifecycle_sends_correct_messages():
    """
        Property 7: WebSocket Connection Lifecycle - Accept Path

        For any random WebSocket scope and sequence of text/binary messages,
        accepting the connection and exchanging messages SHALL produce sent
        messages where the first is websocket.accept, followed by
        websocket.send messages for each reply. When the client disconnects,
        the connection is already marked closed so no explicit close message
        is sent by the server.

        **Validates: Requirements 5.1, 5.2, 5.3, 5.5, 5.6, 5.7, 5.8, 5.10, 5.11**
    """
    handler = WebSocketHandler()

    for iteration in range(100):
        scope = generate_random_websocket_scope()

        num_text = random.randint(0, 5)
        num_binary = random.randint(0, 3)
        text_messages = generate_random_text_messages(num_text)
        binary_messages = generate_random_binary_messages(num_binary)

        # Build receive message sequence: connect, then text, then binary, then disconnect
        receive_messages: List[Dict[str, Any]] = [
            {"type": MESSAGE_WEBSOCKET_CONNECT},
        ]
        for txt in text_messages:
            receive_messages.append({"type": MESSAGE_WEBSOCKET_RECEIVE, "text": txt})
        for bdata in binary_messages:
            receive_messages.append({"type": MESSAGE_WEBSOCKET_RECEIVE, "bytes": bdata})
        receive_messages.append({"type": MESSAGE_WEBSOCKET_DISCONNECT})

        received_texts: List[str] = []
        received_binaries: List[bytes] = []

        async def my_handler(connection: WebSocketConnection) -> None:
            await connection.accept()
            try:
                while True:
                    msg = await connection.receive_message()
                    if isinstance(msg, str):
                        received_texts.append(msg)
                        await connection.send_text(f"echo:{msg}")
                    elif isinstance(msg, bytes):
                        received_binaries.append(msg)
                        await connection.send_bytes(msg)
            except ClientDisconnected:
                pass
            return

        handler.set_handler(my_handler)

        receive = create_receive_callable(receive_messages)
        send, sent_messages = create_send_callable()

        asyncio.get_event_loop().run_until_complete(
            handler.handle(scope, receive, send)
        )

        # Property: first sent message is websocket.accept (Req 5.2, 5.3)
        if len(sent_messages) < 1:
            errmsg = (
                f"Iteration {iteration}: expected at least 1 sent message, "
                f"got {len(sent_messages)}"
            )
            raise AssertionError(errmsg)

        first_msg = sent_messages[0]
        if first_msg.get("type") != MESSAGE_WEBSOCKET_ACCEPT:
            errmsg = (
                f"Iteration {iteration}: first message should be "
                f"'{MESSAGE_WEBSOCKET_ACCEPT}', got '{first_msg.get('type')}'"
            )
            raise AssertionError(errmsg)

        # Property: all received text messages were captured (Req 5.5)
        if received_texts != text_messages:
            errmsg = (
                f"Iteration {iteration}: received texts {received_texts} "
                f"!= expected {text_messages}"
            )
            raise AssertionError(errmsg)

        # Property: all received binary messages were captured (Req 5.6)
        if received_binaries != binary_messages:
            errmsg = (
                f"Iteration {iteration}: received binaries count "
                f"{len(received_binaries)} != expected {len(binary_messages)}"
            )
            raise AssertionError(errmsg)

        # Property: send messages match expected count (Req 5.7, 5.8)
        send_msgs = [
            m for m in sent_messages
            if m.get("type") == MESSAGE_WEBSOCKET_SEND
        ]
        expected_send_count = num_text + num_binary
        if len(send_msgs) != expected_send_count:
            errmsg = (
                f"Iteration {iteration}: expected {expected_send_count} send "
                f"messages, got {len(send_msgs)}"
            )
            raise AssertionError(errmsg)

        # Property: text send messages have 'text' key (Req 5.7)
        for i in range(num_text):
            msg = send_msgs[i]
            if "text" not in msg:
                errmsg = (
                    f"Iteration {iteration}: send message {i} missing 'text' key"
                )
                raise AssertionError(errmsg)

        # Property: binary send messages have 'bytes' key (Req 5.8)
        for i in range(num_text, num_text + num_binary):
            msg = send_msgs[i]
            if "bytes" not in msg:
                errmsg = (
                    f"Iteration {iteration}: send message {i} missing 'bytes' key"
                )
                raise AssertionError(errmsg)

        # Property: accept comes before all send messages
        accept_idx = next(
            i for i, m in enumerate(sent_messages)
            if m.get("type") == MESSAGE_WEBSOCKET_ACCEPT
        )
        for i, m in enumerate(sent_messages):
            if m.get("type") == MESSAGE_WEBSOCKET_SEND and i <= accept_idx:
                errmsg = (
                    f"Iteration {iteration}: send message at index {i} "
                    f"came before accept at index {accept_idx}"
                )
                raise AssertionError(errmsg)

        # Property: no messages of unexpected types
        valid_types = {
            MESSAGE_WEBSOCKET_ACCEPT,
            MESSAGE_WEBSOCKET_SEND,
            MESSAGE_WEBSOCKET_CLOSE,
        }
        for i, m in enumerate(sent_messages):
            if m.get("type") not in valid_types:
                errmsg = (
                    f"Iteration {iteration}: unexpected message type "
                    f"'{m.get('type')}' at index {i}"
                )
                raise AssertionError(errmsg)

    return


def test_property_7_reject_lifecycle_sends_close_only():
    """
        Property 7: WebSocket Connection Lifecycle - Reject Path

        For any random WebSocket scope, rejecting the connection SHALL
        produce exactly one sent message of type websocket.close with
        the rejection code, and no websocket.accept or websocket.send
        messages.

        **Validates: Requirements 5.1, 5.2, 5.4**
    """
    handler = WebSocketHandler()

    for iteration in range(100):
        scope = generate_random_websocket_scope()

        reject_code = random.choice([403, 1000, 1001, 1008])

        async def my_handler(connection: WebSocketConnection, _code=reject_code) -> None:
            await connection.reject(code=_code)
            return

        handler.set_handler(my_handler)

        receive = create_receive_callable([
            {"type": MESSAGE_WEBSOCKET_CONNECT},
        ])
        send, sent_messages = create_send_callable()

        asyncio.get_event_loop().run_until_complete(
            handler.handle(scope, receive, send)
        )

        # Property: exactly one message sent (Req 5.4)
        if len(sent_messages) != 1:
            errmsg = (
                f"Iteration {iteration}: expected exactly 1 sent message, "
                f"got {len(sent_messages)}"
            )
            raise AssertionError(errmsg)

        # Property: the message is websocket.close (Req 5.4)
        msg = sent_messages[0]
        if msg.get("type") != MESSAGE_WEBSOCKET_CLOSE:
            errmsg = (
                f"Iteration {iteration}: expected type "
                f"'{MESSAGE_WEBSOCKET_CLOSE}', got '{msg.get('type')}'"
            )
            raise AssertionError(errmsg)

        # Property: close code matches rejection code
        if msg.get("code") != reject_code:
            errmsg = (
                f"Iteration {iteration}: expected code {reject_code}, "
                f"got {msg.get('code')}"
            )
            raise AssertionError(errmsg)

        # Property: no accept messages sent
        accept_msgs = [
            m for m in sent_messages
            if m.get("type") == MESSAGE_WEBSOCKET_ACCEPT
        ]
        if len(accept_msgs) != 0:
            errmsg = (
                f"Iteration {iteration}: expected 0 accept messages, "
                f"got {len(accept_msgs)}"
            )
            raise AssertionError(errmsg)

        # Property: no send messages sent
        send_msgs = [
            m for m in sent_messages
            if m.get("type") == MESSAGE_WEBSOCKET_SEND
        ]
        if len(send_msgs) != 0:
            errmsg = (
                f"Iteration {iteration}: expected 0 send messages, "
                f"got {len(send_msgs)}"
            )
            raise AssertionError(errmsg)

    return


def test_property_7_disconnect_during_message_loop_closes_gracefully():
    """
        Property 7: WebSocket Connection Lifecycle - Disconnect Handling

        For any random WebSocket scope and random number of messages
        followed by a disconnect, the handler SHALL close the connection
        gracefully without raising unhandled exceptions, and the handler
        SHALL complete successfully. When the client disconnects, the
        connection is marked closed by the disconnect event itself.

        **Validates: Requirements 5.10, 5.11**
    """
    handler = WebSocketHandler()

    for iteration in range(100):
        scope = generate_random_websocket_scope()

        num_messages = random.randint(0, 5)
        text_messages = generate_random_text_messages(num_messages)

        receive_messages: List[Dict[str, Any]] = [
            {"type": MESSAGE_WEBSOCKET_CONNECT},
        ]
        for txt in text_messages:
            receive_messages.append({"type": MESSAGE_WEBSOCKET_RECEIVE, "text": txt})
        receive_messages.append({"type": MESSAGE_WEBSOCKET_DISCONNECT})

        handler_completed = [False]

        async def my_handler(connection: WebSocketConnection) -> None:
            await connection.accept()
            try:
                while True:
                    await connection.receive_message()
            except ClientDisconnected:
                pass
            handler_completed[0] = True
            return

        handler.set_handler(my_handler)

        receive = create_receive_callable(receive_messages)
        send, sent_messages = create_send_callable()

        # Property: no unhandled exception raised
        asyncio.get_event_loop().run_until_complete(
            handler.handle(scope, receive, send)
        )

        # Property: handler completed successfully
        if not handler_completed[0]:
            errmsg = (
                f"Iteration {iteration}: handler did not complete"
            )
            raise AssertionError(errmsg)

        # Property: accept message was sent
        accept_msgs = [
            m for m in sent_messages
            if m.get("type") == MESSAGE_WEBSOCKET_ACCEPT
        ]
        if len(accept_msgs) != 1:
            errmsg = (
                f"Iteration {iteration}: expected 1 accept message, "
                f"got {len(accept_msgs)}"
            )
            raise AssertionError(errmsg)

        # Property: no unexpected message types
        valid_types = {
            MESSAGE_WEBSOCKET_ACCEPT,
            MESSAGE_WEBSOCKET_SEND,
            MESSAGE_WEBSOCKET_CLOSE,
        }
        for i, m in enumerate(sent_messages):
            if m.get("type") not in valid_types:
                errmsg = (
                    f"Iteration {iteration}: unexpected message type "
                    f"'{m.get('type')}' at index {i}"
                )
                raise AssertionError(errmsg)

    return


def test_property_7_subprotocol_negotiation_preserved():
    """
        Property 7: WebSocket Connection Lifecycle - Subprotocol Negotiation

        For any random WebSocket scope with subprotocols, accepting with
        a chosen subprotocol SHALL include that subprotocol in the accept
        message.

        **Validates: Requirements 5.3, 5.12**
    """
    for iteration in range(100):
        subprotocols = generate_random_subprotocols()
        if len(subprotocols) == 0:
            subprotocols = ["chat"]

        scope = create_websocket_scope(
            path=generate_random_path(),
            subprotocols=subprotocols,
        )

        chosen = random.choice(subprotocols)

        receive = create_receive_callable([
            {"type": MESSAGE_WEBSOCKET_CONNECT},
        ])
        send, sent_messages = create_send_callable()

        connection = WebSocketConnection(scope, receive, send)

        asyncio.get_event_loop().run_until_complete(
            connection.accept(subprotocol=chosen)
        )

        # Property: accept message contains chosen subprotocol
        if len(sent_messages) != 1:
            errmsg = (
                f"Iteration {iteration}: expected 1 sent message, "
                f"got {len(sent_messages)}"
            )
            raise AssertionError(errmsg)

        msg = sent_messages[0]
        if msg.get("type") != MESSAGE_WEBSOCKET_ACCEPT:
            errmsg = (
                f"Iteration {iteration}: expected type "
                f"'{MESSAGE_WEBSOCKET_ACCEPT}', got '{msg.get('type')}'"
            )
            raise AssertionError(errmsg)

        if msg.get("subprotocol") != chosen:
            errmsg = (
                f"Iteration {iteration}: expected subprotocol '{chosen}', "
                f"got '{msg.get('subprotocol')}'"
            )
            raise AssertionError(errmsg)

        # Property: connection is accepted
        if not connection.is_accepted:
            errmsg = (
                f"Iteration {iteration}: expected is_accepted=True"
            )
            raise AssertionError(errmsg)

    return


def test_property_7_message_ordering_accept_before_send_before_close():
    """
        Property 7: WebSocket Connection Lifecycle - Message Ordering

        For any random WebSocket connection where the handler explicitly
        closes the connection (not via client disconnect), the sent message
        sequence SHALL always follow the order: websocket.accept, then
        zero or more websocket.send, then websocket.close.

        **Validates: Requirements 5.2, 5.3, 5.7, 5.8, 5.9**
    """
    handler = WebSocketHandler()

    for iteration in range(100):
        scope = generate_random_websocket_scope()

        num_messages = random.randint(0, 5)
        text_messages = generate_random_text_messages(num_messages)

        # Build receive messages: connect, then text messages, then more
        # messages that won't be consumed (handler closes before reading them)
        receive_messages: List[Dict[str, Any]] = [
            {"type": MESSAGE_WEBSOCKET_CONNECT},
        ]
        for txt in text_messages:
            receive_messages.append({"type": MESSAGE_WEBSOCKET_RECEIVE, "text": txt})
        # Add extra disconnect in case handler tries to read more
        receive_messages.append({"type": MESSAGE_WEBSOCKET_DISCONNECT})

        async def my_handler(connection: WebSocketConnection, _count=num_messages) -> None:
            await connection.accept()
            for _ in range(_count):
                msg = await connection.receive_message()
                if isinstance(msg, str):
                    await connection.send_text(msg)
            # Handler explicitly closes (not via disconnect)
            await connection.close()
            return

        handler.set_handler(my_handler)

        receive = create_receive_callable(receive_messages)
        send, sent_messages = create_send_callable()

        asyncio.get_event_loop().run_until_complete(
            handler.handle(scope, receive, send)
        )

        # Classify sent messages by type
        msg_types = [m.get("type") for m in sent_messages]

        # Property: first message is accept
        if len(msg_types) < 1:
            errmsg = (
                f"Iteration {iteration}: expected at least 1 message"
            )
            raise AssertionError(errmsg)

        if msg_types[0] != MESSAGE_WEBSOCKET_ACCEPT:
            errmsg = (
                f"Iteration {iteration}: first message should be accept, "
                f"got '{msg_types[0]}'"
            )
            raise AssertionError(errmsg)

        # Property: last message is close
        if msg_types[-1] != MESSAGE_WEBSOCKET_CLOSE:
            errmsg = (
                f"Iteration {iteration}: last message should be close, "
                f"got '{msg_types[-1]}'"
            )
            raise AssertionError(errmsg)

        # Property: only one accept message
        accept_count = msg_types.count(MESSAGE_WEBSOCKET_ACCEPT)
        if accept_count != 1:
            errmsg = (
                f"Iteration {iteration}: expected 1 accept, got {accept_count}"
            )
            raise AssertionError(errmsg)

        # Property: only one close message
        close_count = msg_types.count(MESSAGE_WEBSOCKET_CLOSE)
        if close_count != 1:
            errmsg = (
                f"Iteration {iteration}: expected 1 close, got {close_count}"
            )
            raise AssertionError(errmsg)

        # Property: all messages between accept and close are send messages
        for i in range(1, len(msg_types) - 1):
            if msg_types[i] != MESSAGE_WEBSOCKET_SEND:
                errmsg = (
                    f"Iteration {iteration}: message at index {i} should be "
                    f"'{MESSAGE_WEBSOCKET_SEND}', got '{msg_types[i]}'"
                )
                raise AssertionError(errmsg)

    return
