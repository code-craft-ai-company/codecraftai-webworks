"""
    Tests for the SSEHandler class.
    
    This module contains unit tests for the ASGI Server-Sent Events handler
    functionality including event formatting, streaming, and connection handling.
"""

import asyncio
from typing import Any, Dict, List

from ccai.webworks.asgi.ssehandler import SSEHandler, SSEEvent
from ccai.webworks.asgi.constants import (
    MESSAGE_HTTP_RESPONSE_START,
    MESSAGE_HTTP_RESPONSE_BODY,
    MESSAGE_HTTP_DISCONNECT,
)


# =============================================================================
# Helper Functions for Creating Mock Callables
# =============================================================================

def create_send_callable() -> tuple:
    """
        Create a mock send callable that records sent messages.
        
        :returns: Tuple of (send_callable, sent_messages_list).
    """
    sent_messages: List[Dict[str, Any]] = []
    
    async def send(message: Dict[str, Any]) -> None:
        sent_messages.append(message)
        return
    
    return send, sent_messages


def create_receive_callable(messages: List[Dict[str, Any]]) -> tuple:
    """
        Create a mock receive callable that returns messages in order.
        
        :param messages: List of messages to return.
        
        :returns: Tuple of (receive_callable, call_count_list).
    """
    call_count = [0]
    
    async def receive() -> Dict[str, Any]:
        if call_count[0] < len(messages):
            message = messages[call_count[0]]
            call_count[0] += 1
            return message
        # Block indefinitely if no more messages
        await asyncio.sleep(10000)
        return {}
    
    return receive, call_count


async def create_async_event_generator(events: List[SSEEvent]):
    """
        Create an async generator that yields SSE events.
        
        :param events: List of SSE events to yield.
        
        :yields: SSE events.
    """
    for event in events:
        yield event
    return


# =============================================================================
# Unit Tests for SSEEvent - Constructor and Properties
# =============================================================================

def test_sseevent_constructor_with_data_only():
    """
        Test that SSEEvent constructor works with data only.
    """
    event = SSEEvent(data="Hello, World!")
    
    if event.data != "Hello, World!":
        errmsg = f"Expected data 'Hello, World!', got '{event.data}'"
        raise AssertionError(errmsg)
    
    if event.event is not None:
        errmsg = f"Expected event to be None, got '{event.event}'"
        raise AssertionError(errmsg)
    
    if event.id is not None:
        errmsg = f"Expected id to be None, got '{event.id}'"
        raise AssertionError(errmsg)
    
    if event.retry is not None:
        errmsg = f"Expected retry to be None, got '{event.retry}'"
        raise AssertionError(errmsg)
    
    return


def test_sseevent_constructor_with_all_fields():
    """
        Test that SSEEvent constructor works with all fields.
    """
    event = SSEEvent(
        data="Test data",
        event="message",
        id="123",
        retry=5000
    )
    
    if event.data != "Test data":
        errmsg = f"Expected data 'Test data', got '{event.data}'"
        raise AssertionError(errmsg)
    
    if event.event != "message":
        errmsg = f"Expected event 'message', got '{event.event}'"
        raise AssertionError(errmsg)
    
    if event.id != "123":
        errmsg = f"Expected id '123', got '{event.id}'"
        raise AssertionError(errmsg)
    
    if event.retry != 5000:
        errmsg = f"Expected retry 5000, got '{event.retry}'"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for SSEEvent - format() Method
# =============================================================================

def test_sseevent_format_data_only():
    """
        Test that SSEEvent.format() formats data-only event correctly.
    """
    event = SSEEvent(data="Hello")
    formatted = event.format()
    
    expected = "data: Hello\n\n"
    
    if formatted != expected:
        errmsg = f"Expected '{expected!r}', got '{formatted!r}'"
        raise AssertionError(errmsg)
    
    return


def test_sseevent_format_with_event_name():
    """
        Test that SSEEvent.format() includes event name.
    """
    event = SSEEvent(data="Hello", event="greeting")
    formatted = event.format()
    
    if "event: greeting" not in formatted:
        errmsg = f"Expected 'event: greeting' in formatted output, got '{formatted!r}'"
        raise AssertionError(errmsg)
    
    if "data: Hello" not in formatted:
        errmsg = f"Expected 'data: Hello' in formatted output, got '{formatted!r}'"
        raise AssertionError(errmsg)
    
    return


def test_sseevent_format_with_id():
    """
        Test that SSEEvent.format() includes event ID.
    """
    event = SSEEvent(data="Hello", id="msg-123")
    formatted = event.format()
    
    if "id: msg-123" not in formatted:
        errmsg = f"Expected 'id: msg-123' in formatted output, got '{formatted!r}'"
        raise AssertionError(errmsg)
    
    return


def test_sseevent_format_with_retry():
    """
        Test that SSEEvent.format() includes retry interval.
    """
    event = SSEEvent(data="Hello", retry=3000)
    formatted = event.format()
    
    if "retry: 3000" not in formatted:
        errmsg = f"Expected 'retry: 3000' in formatted output, got '{formatted!r}'"
        raise AssertionError(errmsg)
    
    return


def test_sseevent_format_with_all_fields():
    """
        Test that SSEEvent.format() includes all fields.
    """
    event = SSEEvent(
        data="Test message",
        event="update",
        id="456",
        retry=1000
    )
    formatted = event.format()
    
    if "event: update" not in formatted:
        errmsg = f"Expected 'event: update' in formatted output"
        raise AssertionError(errmsg)
    
    if "id: 456" not in formatted:
        errmsg = f"Expected 'id: 456' in formatted output"
        raise AssertionError(errmsg)
    
    if "retry: 1000" not in formatted:
        errmsg = f"Expected 'retry: 1000' in formatted output"
        raise AssertionError(errmsg)
    
    if "data: Test message" not in formatted:
        errmsg = f"Expected 'data: Test message' in formatted output"
        raise AssertionError(errmsg)
    
    return


def test_sseevent_format_ends_with_double_newline():
    """
        Test that SSEEvent.format() ends with double newline.
    """
    event = SSEEvent(data="Hello")
    formatted = event.format()
    
    if not formatted.endswith("\n\n"):
        errmsg = f"Expected formatted output to end with double newline, got '{formatted!r}'"
        raise AssertionError(errmsg)
    
    return


def test_sseevent_format_multiline_data():
    """
        Test that SSEEvent.format() handles multiline data.
    """
    event = SSEEvent(data="Line 1\nLine 2\nLine 3")
    formatted = event.format()
    
    if "data: Line 1" not in formatted:
        errmsg = f"Expected 'data: Line 1' in formatted output"
        raise AssertionError(errmsg)
    
    if "data: Line 2" not in formatted:
        errmsg = f"Expected 'data: Line 2' in formatted output"
        raise AssertionError(errmsg)
    
    if "data: Line 3" not in formatted:
        errmsg = f"Expected 'data: Line 3' in formatted output"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for SSEHandler - Constructor
# =============================================================================

def test_ssehandler_constructor():
    """
        Test that SSEHandler constructor creates instance.
    """
    handler = SSEHandler()
    
    if handler is None:
        errmsg = "Expected SSEHandler instance, got None"
        raise AssertionError(errmsg)
    
    return


def test_ssehandler_constructor_with_logger():
    """
        Test that SSEHandler constructor accepts custom logger.
    """
    import logging
    
    custom_logger = logging.getLogger("test_sse")
    handler = SSEHandler(logger=custom_logger)
    
    if handler.logger is not custom_logger:
        errmsg = "Expected custom logger to be used"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for SSEHandler - SSE Headers
# =============================================================================

def test_ssehandler_sse_content_type():
    """
        Test that SSEHandler has correct SSE content type.
    """
    handler = SSEHandler()
    
    expected = "text/event-stream"
    
    if handler.SSE_CONTENT_TYPE != expected:
        errmsg = f"Expected SSE_CONTENT_TYPE '{expected}', got '{handler.SSE_CONTENT_TYPE}'"
        raise AssertionError(errmsg)
    
    return


def test_ssehandler_sse_headers_include_content_type():
    """
        Test that SSE_HEADERS includes content-type header.
    """
    handler = SSEHandler()
    
    headers_dict = {name: value for name, value in handler.SSE_HEADERS}
    
    if b"content-type" not in headers_dict:
        errmsg = "Expected 'content-type' in SSE_HEADERS"
        raise AssertionError(errmsg)
    
    if headers_dict[b"content-type"] != b"text/event-stream":
        errmsg = f"Expected content-type 'text/event-stream', got {headers_dict[b'content-type']}"
        raise AssertionError(errmsg)
    
    return


def test_ssehandler_sse_headers_include_cache_control():
    """
        Test that SSE_HEADERS includes cache-control header.
    """
    handler = SSEHandler()
    
    headers_dict = {name: value for name, value in handler.SSE_HEADERS}
    
    if b"cache-control" not in headers_dict:
        errmsg = "Expected 'cache-control' in SSE_HEADERS"
        raise AssertionError(errmsg)
    
    if headers_dict[b"cache-control"] != b"no-cache":
        errmsg = f"Expected cache-control 'no-cache', got {headers_dict[b'cache-control']}"
        raise AssertionError(errmsg)
    
    return


def test_ssehandler_sse_headers_include_connection():
    """
        Test that SSE_HEADERS includes connection header.
    """
    handler = SSEHandler()
    
    headers_dict = {name: value for name, value in handler.SSE_HEADERS}
    
    if b"connection" not in headers_dict:
        errmsg = "Expected 'connection' in SSE_HEADERS"
        raise AssertionError(errmsg)
    
    if headers_dict[b"connection"] != b"keep-alive":
        errmsg = f"Expected connection 'keep-alive', got {headers_dict[b'connection']}"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for SSEHandler - format_event() Method
# =============================================================================

def test_format_event_returns_bytes():
    """
        Test that format_event() returns bytes.
    """
    handler = SSEHandler()
    event = SSEEvent(data="Hello")
    
    result = handler.format_event(event)
    
    if not isinstance(result, bytes):
        errmsg = f"Expected bytes, got {type(result)}"
        raise AssertionError(errmsg)
    
    return


def test_format_event_encodes_utf8():
    """
        Test that format_event() encodes as UTF-8.
    """
    handler = SSEHandler()
    event = SSEEvent(data="Hello, 世界!")
    
    result = handler.format_event(event)
    
    # Should be valid UTF-8
    decoded = result.decode("utf-8")
    
    if "Hello, 世界!" not in decoded:
        errmsg = f"Expected 'Hello, 世界!' in decoded output"
        raise AssertionError(errmsg)
    
    return


def test_format_event_includes_data_prefix():
    """
        Test that format_event() includes data: prefix.
    """
    handler = SSEHandler()
    event = SSEEvent(data="Test message")
    
    result = handler.format_event(event)
    
    if b"data: Test message" not in result:
        errmsg = f"Expected 'data: Test message' in result"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for SSEHandler - format_event_fields() Method
# =============================================================================

def test_format_event_fields_with_data_only():
    """
        Test that format_event_fields() works with data only.
    """
    handler = SSEHandler()
    
    result = handler.format_event_fields(data="Hello")
    
    if b"data: Hello" not in result:
        errmsg = f"Expected 'data: Hello' in result"
        raise AssertionError(errmsg)
    
    return


def test_format_event_fields_with_all_fields():
    """
        Test that format_event_fields() works with all fields.
    """
    handler = SSEHandler()
    
    result = handler.format_event_fields(
        data="Test",
        event="update",
        id="123",
        retry=5000
    )
    
    if b"event: update" not in result:
        errmsg = f"Expected 'event: update' in result"
        raise AssertionError(errmsg)
    
    if b"id: 123" not in result:
        errmsg = f"Expected 'id: 123' in result"
        raise AssertionError(errmsg)
    
    if b"retry: 5000" not in result:
        errmsg = f"Expected 'retry: 5000' in result"
        raise AssertionError(errmsg)
    
    if b"data: Test" not in result:
        errmsg = f"Expected 'data: Test' in result"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for SSEHandler - get_sse_headers() Method
# =============================================================================

def test_get_sse_headers_returns_default_headers():
    """
        Test that get_sse_headers() returns default SSE headers.
    """
    handler = SSEHandler()
    
    headers = handler.get_sse_headers()
    
    if len(headers) != 3:
        errmsg = f"Expected 3 default headers, got {len(headers)}"
        raise AssertionError(errmsg)
    
    return


def test_get_sse_headers_includes_additional_headers():
    """
        Test that get_sse_headers() includes additional headers.
    """
    handler = SSEHandler()
    
    additional = [(b"x-custom", b"value")]
    headers = handler.get_sse_headers(additional_headers=additional)
    
    if len(headers) != 4:
        errmsg = f"Expected 4 headers, got {len(headers)}"
        raise AssertionError(errmsg)
    
    headers_dict = {name: value for name, value in headers}
    
    if b"x-custom" not in headers_dict:
        errmsg = "Expected 'x-custom' in headers"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for SSEHandler - stream() Method
# =============================================================================

def test_stream_sends_response_start_first():
    """
        Test that stream() sends response start message first.
    """
    handler = SSEHandler()
    send, sent_messages = create_send_callable()
    
    events = [SSEEvent(data="Hello")]
    
    async def run_test():
        event_source = create_async_event_generator(events)
        await handler.stream(send, event_source)
        return
    
    asyncio.get_event_loop().run_until_complete(run_test())
    
    if len(sent_messages) < 1:
        errmsg = "Expected at least 1 message"
        raise AssertionError(errmsg)
    
    first_message = sent_messages[0]
    
    if first_message.get("type") != MESSAGE_HTTP_RESPONSE_START:
        errmsg = f"Expected first message to be response start, got {first_message.get('type')}"
        raise AssertionError(errmsg)
    
    return


def test_stream_sends_200_status():
    """
        Test that stream() sends 200 OK status.
    """
    handler = SSEHandler()
    send, sent_messages = create_send_callable()
    
    events = [SSEEvent(data="Hello")]
    
    async def run_test():
        event_source = create_async_event_generator(events)
        await handler.stream(send, event_source)
        return
    
    asyncio.get_event_loop().run_until_complete(run_test())
    
    start_message = sent_messages[0]
    
    if start_message.get("status") != 200:
        errmsg = f"Expected status 200, got {start_message.get('status')}"
        raise AssertionError(errmsg)
    
    return


def test_stream_sends_sse_headers():
    """
        Test that stream() sends SSE headers.
    """
    handler = SSEHandler()
    send, sent_messages = create_send_callable()
    
    events = [SSEEvent(data="Hello")]
    
    async def run_test():
        event_source = create_async_event_generator(events)
        await handler.stream(send, event_source)
        return
    
    asyncio.get_event_loop().run_until_complete(run_test())
    
    start_message = sent_messages[0]
    headers = start_message.get("headers", [])
    headers_dict = {name: value for name, value in headers}
    
    if b"content-type" not in headers_dict:
        errmsg = "Expected 'content-type' header"
        raise AssertionError(errmsg)
    
    if headers_dict[b"content-type"] != b"text/event-stream":
        errmsg = f"Expected content-type 'text/event-stream', got {headers_dict[b'content-type']}"
        raise AssertionError(errmsg)
    
    return


def test_stream_sends_events_as_body_messages():
    """
        Test that stream() sends events as body messages.
    """
    handler = SSEHandler()
    send, sent_messages = create_send_callable()
    
    events = [
        SSEEvent(data="Event 1"),
        SSEEvent(data="Event 2"),
    ]
    
    async def run_test():
        event_source = create_async_event_generator(events)
        await handler.stream(send, event_source)
        return
    
    asyncio.get_event_loop().run_until_complete(run_test())
    
    # Should have: start + 2 events + final close
    body_messages = [
        msg for msg in sent_messages
        if msg.get("type") == MESSAGE_HTTP_RESPONSE_BODY
    ]
    
    if len(body_messages) < 2:
        errmsg = f"Expected at least 2 body messages, got {len(body_messages)}"
        raise AssertionError(errmsg)
    
    return


def test_stream_sets_more_body_true_for_events():
    """
        Test that stream() sets more_body=True for event messages.
    """
    handler = SSEHandler()
    send, sent_messages = create_send_callable()
    
    events = [
        SSEEvent(data="Event 1"),
        SSEEvent(data="Event 2"),
    ]
    
    async def run_test():
        event_source = create_async_event_generator(events)
        await handler.stream(send, event_source)
        return
    
    asyncio.get_event_loop().run_until_complete(run_test())
    
    # Get body messages (excluding final close)
    body_messages = [
        msg for msg in sent_messages
        if msg.get("type") == MESSAGE_HTTP_RESPONSE_BODY
    ]
    
    # All but the last should have more_body=True
    for i in range(len(body_messages) - 1):
        if body_messages[i].get("more_body") is not True:
            errmsg = f"Expected more_body=True for message {i}"
            raise AssertionError(errmsg)
    
    return


def test_stream_sends_final_close_message():
    """
        Test that stream() sends final close message with more_body=False.
    """
    handler = SSEHandler()
    send, sent_messages = create_send_callable()
    
    events = [SSEEvent(data="Hello")]
    
    async def run_test():
        event_source = create_async_event_generator(events)
        await handler.stream(send, event_source)
        return
    
    asyncio.get_event_loop().run_until_complete(run_test())
    
    # Last message should have more_body=False
    last_message = sent_messages[-1]
    
    if last_message.get("more_body") is not False:
        errmsg = f"Expected more_body=False for final message, got {last_message.get('more_body')}"
        raise AssertionError(errmsg)
    
    return


def test_stream_handles_empty_event_source():
    """
        Test that stream() handles empty event source.
    """
    handler = SSEHandler()
    send, sent_messages = create_send_callable()
    
    events: List[SSEEvent] = []
    
    async def run_test():
        event_source = create_async_event_generator(events)
        await handler.stream(send, event_source)
        return
    
    asyncio.get_event_loop().run_until_complete(run_test())
    
    # Should have: start + final close
    if len(sent_messages) != 2:
        errmsg = f"Expected 2 messages, got {len(sent_messages)}"
        raise AssertionError(errmsg)
    
    return


def test_stream_includes_additional_headers():
    """
        Test that stream() includes additional headers.
    """
    handler = SSEHandler()
    send, sent_messages = create_send_callable()
    
    events = [SSEEvent(data="Hello")]
    additional_headers = [(b"x-custom", b"value")]
    
    async def run_test():
        event_source = create_async_event_generator(events)
        await handler.stream(send, event_source, headers=additional_headers)
        return
    
    asyncio.get_event_loop().run_until_complete(run_test())
    
    start_message = sent_messages[0]
    headers = start_message.get("headers", [])
    headers_dict = {name: value for name, value in headers}
    
    if b"x-custom" not in headers_dict:
        errmsg = "Expected 'x-custom' header"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for SSEHandler - send_event() Method
# =============================================================================

def test_send_event_sends_body_message():
    """
        Test that send_event() sends body message.
    """
    handler = SSEHandler()
    send, sent_messages = create_send_callable()
    
    async def run_test():
        await handler.send_event(send, data="Hello")
        return
    
    asyncio.get_event_loop().run_until_complete(run_test())
    
    if len(sent_messages) != 1:
        errmsg = f"Expected 1 message, got {len(sent_messages)}"
        raise AssertionError(errmsg)
    
    message = sent_messages[0]
    
    if message.get("type") != MESSAGE_HTTP_RESPONSE_BODY:
        errmsg = f"Expected body message, got {message.get('type')}"
        raise AssertionError(errmsg)
    
    return


def test_send_event_sets_more_body_true():
    """
        Test that send_event() sets more_body=True.
    """
    handler = SSEHandler()
    send, sent_messages = create_send_callable()
    
    async def run_test():
        await handler.send_event(send, data="Hello")
        return
    
    asyncio.get_event_loop().run_until_complete(run_test())
    
    message = sent_messages[0]
    
    if message.get("more_body") is not True:
        errmsg = f"Expected more_body=True, got {message.get('more_body')}"
        raise AssertionError(errmsg)
    
    return


def test_send_event_includes_formatted_event():
    """
        Test that send_event() includes formatted event in body.
    """
    handler = SSEHandler()
    send, sent_messages = create_send_callable()
    
    async def run_test():
        await handler.send_event(send, data="Test message", event="update")
        return
    
    asyncio.get_event_loop().run_until_complete(run_test())
    
    message = sent_messages[0]
    body = message.get("body", b"")
    
    if b"event: update" not in body:
        errmsg = f"Expected 'event: update' in body"
        raise AssertionError(errmsg)
    
    if b"data: Test message" not in body:
        errmsg = f"Expected 'data: Test message' in body"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for SSEHandler - close_stream() Method
# =============================================================================

def test_close_stream_sends_final_message():
    """
        Test that close_stream() sends final message.
    """
    handler = SSEHandler()
    send, sent_messages = create_send_callable()
    
    async def run_test():
        await handler.close_stream(send)
        return
    
    asyncio.get_event_loop().run_until_complete(run_test())
    
    if len(sent_messages) != 1:
        errmsg = f"Expected 1 message, got {len(sent_messages)}"
        raise AssertionError(errmsg)
    
    return


def test_close_stream_sets_more_body_false():
    """
        Test that close_stream() sets more_body=False.
    """
    handler = SSEHandler()
    send, sent_messages = create_send_callable()
    
    async def run_test():
        await handler.close_stream(send)
        return
    
    asyncio.get_event_loop().run_until_complete(run_test())
    
    message = sent_messages[0]
    
    if message.get("more_body") is not False:
        errmsg = f"Expected more_body=False, got {message.get('more_body')}"
        raise AssertionError(errmsg)
    
    return


def test_close_stream_sends_empty_body():
    """
        Test that close_stream() sends empty body.
    """
    handler = SSEHandler()
    send, sent_messages = create_send_callable()
    
    async def run_test():
        await handler.close_stream(send)
        return
    
    asyncio.get_event_loop().run_until_complete(run_test())
    
    message = sent_messages[0]
    
    if message.get("body") != b"":
        errmsg = f"Expected empty body, got {message.get('body')}"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for SSEHandler - stream_with_receive() Method
# =============================================================================

def test_stream_with_receive_sends_response_start():
    """
        Test that stream_with_receive() sends response start.
    """
    handler = SSEHandler()
    send, sent_messages = create_send_callable()
    
    # Create receive that returns disconnect after a delay
    receive, _ = create_receive_callable([
        {"type": MESSAGE_HTTP_DISCONNECT}
    ])
    
    events = [SSEEvent(data="Hello")]
    
    async def run_test():
        event_source = create_async_event_generator(events)
        await handler.stream_with_receive(send, receive, event_source)
        return
    
    asyncio.get_event_loop().run_until_complete(run_test())
    
    if len(sent_messages) < 1:
        errmsg = "Expected at least 1 message"
        raise AssertionError(errmsg)
    
    first_message = sent_messages[0]
    
    if first_message.get("type") != MESSAGE_HTTP_RESPONSE_START:
        errmsg = f"Expected response start, got {first_message.get('type')}"
        raise AssertionError(errmsg)
    
    return


def test_stream_with_receive_streams_events():
    """
        Test that stream_with_receive() streams events.
    """
    handler = SSEHandler()
    send, sent_messages = create_send_callable()
    
    # Create receive that returns disconnect after events are sent
    receive, _ = create_receive_callable([
        {"type": MESSAGE_HTTP_DISCONNECT}
    ])
    
    events = [
        SSEEvent(data="Event 1"),
        SSEEvent(data="Event 2"),
    ]
    
    async def run_test():
        event_source = create_async_event_generator(events)
        await handler.stream_with_receive(send, receive, event_source)
        return
    
    asyncio.get_event_loop().run_until_complete(run_test())
    
    # Should have body messages for events
    body_messages = [
        msg for msg in sent_messages
        if msg.get("type") == MESSAGE_HTTP_RESPONSE_BODY
    ]
    
    if len(body_messages) < 2:
        errmsg = f"Expected at least 2 body messages, got {len(body_messages)}"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for SSE Event Formatting (Property 8)
# =============================================================================

def test_sse_event_formatting_property_data_prefix():
    """
        Test that SSE events have proper data: prefix.
        
        This validates Property 8: SSE Event Formatting.
    """
    handler = SSEHandler()
    
    test_data = [
        "Simple message",
        "Message with special chars: <>&\"'",
        "Unicode: 日本語 中文 한국어",
        "",
        "   spaces   ",
    ]
    
    for data in test_data:
        event = SSEEvent(data=data)
        formatted = handler.format_event(event)
        
        # Each line of data should have data: prefix
        for line in data.split("\n"):
            expected = f"data: {line}".encode("utf-8")
            if expected not in formatted:
                errmsg = f"Expected '{expected}' in formatted output for data '{data}'"
                raise AssertionError(errmsg)
    
    return


def test_sse_event_formatting_property_double_newline():
    """
        Test that SSE events end with double newline.
        
        This validates Property 8: SSE Event Formatting.
    """
    handler = SSEHandler()
    
    test_events = [
        SSEEvent(data="Simple"),
        SSEEvent(data="With event", event="test"),
        SSEEvent(data="With id", id="123"),
        SSEEvent(data="With retry", retry=5000),
        SSEEvent(data="All fields", event="test", id="123", retry=5000),
    ]
    
    for event in test_events:
        formatted = handler.format_event(event)
        
        if not formatted.endswith(b"\n\n"):
            errmsg = f"Expected double newline termination for event {event}"
            raise AssertionError(errmsg)
    
    return


def test_sse_event_formatting_property_field_prefixes():
    """
        Test that SSE events have proper field prefixes.
        
        This validates Property 8: SSE Event Formatting.
    """
    handler = SSEHandler()
    
    event = SSEEvent(
        data="Test data",
        event="custom_event",
        id="event-123",
        retry=3000
    )
    
    formatted = handler.format_event(event)
    
    # Check all field prefixes
    if b"event: custom_event" not in formatted:
        errmsg = "Expected 'event: custom_event' prefix"
        raise AssertionError(errmsg)
    
    if b"id: event-123" not in formatted:
        errmsg = "Expected 'id: event-123' prefix"
        raise AssertionError(errmsg)
    
    if b"retry: 3000" not in formatted:
        errmsg = "Expected 'retry: 3000' prefix"
        raise AssertionError(errmsg)
    
    if b"data: Test data" not in formatted:
        errmsg = "Expected 'data: Test data' prefix"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for SSEHandler - Connection Keep-Alive (Requirements 6.7, 6.8)
# =============================================================================

def test_stream_keeps_connection_open_during_events():
    """
        Test that stream() keeps connection open during event streaming.
        
        This validates Requirement 6.7: Keep connection open until explicitly closed.
    """
    handler = SSEHandler()
    send, sent_messages = create_send_callable()
    
    events = [
        SSEEvent(data="Event 1"),
        SSEEvent(data="Event 2"),
        SSEEvent(data="Event 3"),
    ]
    
    async def run_test():
        event_source = create_async_event_generator(events)
        await handler.stream(send, event_source)
        return
    
    asyncio.get_event_loop().run_until_complete(run_test())
    
    # Get all body messages
    body_messages = [
        msg for msg in sent_messages
        if msg.get("type") == MESSAGE_HTTP_RESPONSE_BODY
    ]
    
    # All event messages (not the final close) should have more_body=True
    event_messages = body_messages[:-1]  # Exclude final close message
    
    for i, msg in enumerate(event_messages):
        if msg.get("more_body") is not True:
            errmsg = f"Expected more_body=True for event {i}, got {msg.get('more_body')}"
            raise AssertionError(errmsg)
    
    return


def test_stream_closes_connection_after_events_exhausted():
    """
        Test that stream() closes connection after events are exhausted.
        
        This validates Requirement 6.7: Keep connection open until explicitly closed.
    """
    handler = SSEHandler()
    send, sent_messages = create_send_callable()
    
    events = [SSEEvent(data="Final event")]
    
    async def run_test():
        event_source = create_async_event_generator(events)
        await handler.stream(send, event_source)
        return
    
    asyncio.get_event_loop().run_until_complete(run_test())
    
    # Last message should close the connection
    last_message = sent_messages[-1]
    
    if last_message.get("type") != MESSAGE_HTTP_RESPONSE_BODY:
        errmsg = f"Expected last message to be body, got {last_message.get('type')}"
        raise AssertionError(errmsg)
    
    if last_message.get("more_body") is not False:
        errmsg = f"Expected more_body=False for final message"
        raise AssertionError(errmsg)
    
    return


def test_stream_with_receive_detects_client_disconnect():
    """
        Test that stream_with_receive() detects client disconnection.
        
        This validates Requirement 6.8: Detect client disconnection and clean up.
    """
    handler = SSEHandler()
    send, sent_messages = create_send_callable()
    
    # Create receive that returns disconnect immediately
    receive, call_count = create_receive_callable([
        {"type": MESSAGE_HTTP_DISCONNECT}
    ])
    
    # Create a simple generator with a few events
    events = [
        SSEEvent(data="Event 1"),
        SSEEvent(data="Event 2"),
    ]
    
    async def run_test():
        event_source = create_async_event_generator(events)
        await handler.stream_with_receive(send, receive, event_source)
        return
    
    asyncio.get_event_loop().run_until_complete(run_test())
    
    # The stream should complete - verify we got the response start
    if len(sent_messages) < 1:
        errmsg = "Expected at least 1 message"
        raise AssertionError(errmsg)
    
    # First message should be response start
    if sent_messages[0].get("type") != MESSAGE_HTTP_RESPONSE_START:
        errmsg = f"Expected response start, got {sent_messages[0].get('type')}"
        raise AssertionError(errmsg)
    
    return


def test_stream_includes_keep_alive_header():
    """
        Test that stream() includes Connection: keep-alive header.
        
        This validates Requirement 6.7: Keep connection open.
    """
    handler = SSEHandler()
    send, sent_messages = create_send_callable()
    
    events = [SSEEvent(data="Hello")]
    
    async def run_test():
        event_source = create_async_event_generator(events)
        await handler.stream(send, event_source)
        return
    
    asyncio.get_event_loop().run_until_complete(run_test())
    
    start_message = sent_messages[0]
    headers = start_message.get("headers", [])
    headers_dict = {name: value for name, value in headers}
    
    if b"connection" not in headers_dict:
        errmsg = "Expected 'connection' header"
        raise AssertionError(errmsg)
    
    if headers_dict[b"connection"] != b"keep-alive":
        errmsg = f"Expected connection 'keep-alive', got {headers_dict[b'connection']}"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for SSEHandler - Error Handling (Requirement 10.7)
# =============================================================================

def test_stream_closes_gracefully_on_generator_error():
    """
        Test that stream() closes gracefully when generator raises error.
        
        This validates Requirement 10.7: Close stream gracefully on error.
    """
    handler = SSEHandler()
    send, sent_messages = create_send_callable()
    
    async def error_generator():
        yield SSEEvent(data="Event 1")
        raise ValueError("Test error")
    
    async def run_test():
        try:
            await handler.stream(send, error_generator())
        except ValueError:
            pass  # Expected
        return
    
    asyncio.get_event_loop().run_until_complete(run_test())
    
    # Should have sent response start
    if len(sent_messages) < 1:
        errmsg = "Expected at least 1 message"
        raise AssertionError(errmsg)
    
    # Last message should close the stream
    last_message = sent_messages[-1]
    
    if last_message.get("type") != MESSAGE_HTTP_RESPONSE_BODY:
        errmsg = f"Expected body message, got {last_message.get('type')}"
        raise AssertionError(errmsg)
    
    if last_message.get("more_body") is not False:
        errmsg = f"Expected more_body=False for final message"
        raise AssertionError(errmsg)
    
    return


def test_stream_raises_exception_after_cleanup():
    """
        Test that stream() raises exception after cleanup.
    """
    handler = SSEHandler()
    send, sent_messages = create_send_callable()
    
    async def error_generator():
        yield SSEEvent(data="Event 1")
        raise RuntimeError("Test runtime error")
    
    exception_raised = [False]
    
    async def run_test():
        try:
            await handler.stream(send, error_generator())
        except RuntimeError as e:
            if "Test runtime error" in str(e):
                exception_raised[0] = True
        return
    
    asyncio.get_event_loop().run_until_complete(run_test())
    
    if not exception_raised[0]:
        errmsg = "Expected RuntimeError to be raised"
        raise AssertionError(errmsg)
    
    return


def test_stream_sends_events_before_error():
    """
        Test that stream() sends events before error occurs.
    """
    handler = SSEHandler()
    send, sent_messages = create_send_callable()
    
    async def error_generator():
        yield SSEEvent(data="Event 1")
        yield SSEEvent(data="Event 2")
        raise ValueError("Test error")
    
    async def run_test():
        try:
            await handler.stream(send, error_generator())
        except ValueError:
            # Expected: error_generator() raises ValueError after two events; this
            # test only verifies the messages that were sent before the error.
            pass
        return
    
    asyncio.get_event_loop().run_until_complete(run_test())
    
    # Should have: start + 2 events + final close
    body_messages = [
        msg for msg in sent_messages
        if msg.get("type") == MESSAGE_HTTP_RESPONSE_BODY
    ]
    
    # Should have at least 2 event messages plus final close
    if len(body_messages) < 3:
        errmsg = f"Expected at least 3 body messages, got {len(body_messages)}"
        raise AssertionError(errmsg)
    
    return


def test_close_stream_handles_send_error():
    """
        Test that close_stream() handles send errors gracefully.
    """
    handler = SSEHandler()
    
    async def failing_send(message):
        raise ConnectionError("Connection closed")
    
    async def run_test():
        # Should not raise - errors are caught
        await handler.close_stream(failing_send)
        return
    
    # Should complete without raising
    asyncio.get_event_loop().run_until_complete(run_test())
    
    return


def test_stream_handles_send_error_in_finally():
    """
        Test that stream() handles send error in finally block.
    """
    handler = SSEHandler()
    
    call_count = [0]
    
    async def failing_send_on_close(message):
        call_count[0] += 1
        # Fail on the final close message
        if message.get("more_body") is False:
            raise ConnectionError("Connection closed")
        return
    
    events = [SSEEvent(data="Hello")]
    
    async def run_test():
        event_source = create_async_event_generator(events)
        # Should complete without raising
        await handler.stream(failing_send_on_close, event_source)
        return
    
    asyncio.get_event_loop().run_until_complete(run_test())
    
    # Should have attempted to send messages
    if call_count[0] < 2:
        errmsg = f"Expected at least 2 send calls, got {call_count[0]}"
        raise AssertionError(errmsg)
    
    return
