"""
    Tests for the ResponseSender class.
    
    This module contains unit tests for the ASGI response sender functionality
    including message sending, header formatting, and streaming responses.
"""

import asyncio
from typing import Any, Dict, List

from ccai.webworks.asgi.responsesender import ResponseSender
from ccai.webworks.asgi.constants import (
    MESSAGE_HTTP_RESPONSE_START,
    MESSAGE_HTTP_RESPONSE_BODY,
)


# =============================================================================
# Helper Functions for Creating Mock Send Callables
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


# =============================================================================
# Helper Functions for Creating Mock Response Objects
# =============================================================================

class MockResponse:
    """
        Mock Response object for testing.
    """
    
    def __init__(
        self,
        status_code: int,
        headers: Dict[str, str],
        body: Any
    ):
        """
            Construct a MockResponse.
            
            :param status_code: HTTP status code.
            :param headers: Dict of header names to values.
            :param body: Response body (bytes, str, or async generator).
        """
        self.status_code = status_code
        self.headers = headers
        self.body = body
        return


async def create_async_body_generator(chunks: List[bytes]):
    """
        Create an async generator that yields body chunks.
        
        :param chunks: List of byte chunks to yield.
        
        :yields: Body chunks.
    """
    for chunk in chunks:
        yield chunk
    return


# =============================================================================
# Unit Tests for ResponseSender - Constructor
# =============================================================================

def test_responsesender_constructor():
    """
        Test that ResponseSender constructor creates instance.
    """
    sender = ResponseSender()
    
    if sender is None:
        errmsg = "Expected ResponseSender instance, got None"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for ResponseSender - send_start() Method
# =============================================================================

def test_send_start_sends_correct_message_type():
    """
        Test that send_start() sends http.response.start message type.
    """
    sender = ResponseSender()
    send, sent_messages = create_send_callable()
    
    asyncio.get_event_loop().run_until_complete(
        sender.send_start(send, status=200, headers=[])
    )
    
    if len(sent_messages) != 1:
        errmsg = f"Expected 1 message, got {len(sent_messages)}"
        raise AssertionError(errmsg)
    
    message = sent_messages[0]
    expected_type = MESSAGE_HTTP_RESPONSE_START
    
    if message.get("type") != expected_type:
        errmsg = f"Expected type '{expected_type}', got '{message.get('type')}'"
        raise AssertionError(errmsg)
    
    return


def test_send_start_includes_status_code():
    """
        Test that send_start() includes status code in message.
    """
    sender = ResponseSender()
    send, sent_messages = create_send_callable()
    
    asyncio.get_event_loop().run_until_complete(
        sender.send_start(send, status=404, headers=[])
    )
    
    message = sent_messages[0]
    
    if message.get("status") != 404:
        errmsg = f"Expected status 404, got {message.get('status')}"
        raise AssertionError(errmsg)
    
    return


def test_send_start_includes_headers():
    """
        Test that send_start() includes headers in message.
    """
    sender = ResponseSender()
    send, sent_messages = create_send_callable()
    
    headers = [
        (b"content-type", b"text/html"),
        (b"x-custom", b"value")
    ]
    
    asyncio.get_event_loop().run_until_complete(
        sender.send_start(send, status=200, headers=headers)
    )
    
    message = sent_messages[0]
    
    if message.get("headers") != headers:
        errmsg = f"Expected headers {headers}, got {message.get('headers')}"
        raise AssertionError(errmsg)
    
    return


def test_send_start_with_various_status_codes():
    """
        Test that send_start() works with various HTTP status codes.
    """
    sender = ResponseSender()
    
    status_codes = [200, 201, 204, 301, 400, 401, 403, 404, 500, 502, 503]
    
    for status_code in status_codes:
        send, sent_messages = create_send_callable()
        
        asyncio.get_event_loop().run_until_complete(
            sender.send_start(send, status=status_code, headers=[])
        )
        
        message = sent_messages[0]
        
        if message.get("status") != status_code:
            errmsg = f"Expected status {status_code}, got {message.get('status')}"
            raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for ResponseSender - send_body() Method
# =============================================================================

def test_send_body_sends_correct_message_type():
    """
        Test that send_body() sends http.response.body message type.
    """
    sender = ResponseSender()
    send, sent_messages = create_send_callable()
    
    asyncio.get_event_loop().run_until_complete(
        sender.send_body(send, body=b"Hello", more_body=False)
    )
    
    if len(sent_messages) != 1:
        errmsg = f"Expected 1 message, got {len(sent_messages)}"
        raise AssertionError(errmsg)
    
    message = sent_messages[0]
    expected_type = MESSAGE_HTTP_RESPONSE_BODY
    
    if message.get("type") != expected_type:
        errmsg = f"Expected type '{expected_type}', got '{message.get('type')}'"
        raise AssertionError(errmsg)
    
    return


def test_send_body_includes_body_content():
    """
        Test that send_body() includes body content in message.
    """
    sender = ResponseSender()
    send, sent_messages = create_send_callable()
    
    body_content = b"Hello, World!"
    
    asyncio.get_event_loop().run_until_complete(
        sender.send_body(send, body=body_content, more_body=False)
    )
    
    message = sent_messages[0]
    
    if message.get("body") != body_content:
        errmsg = f"Expected body '{body_content}', got '{message.get('body')}'"
        raise AssertionError(errmsg)
    
    return


def test_send_body_includes_more_body_true():
    """
        Test that send_body() includes more_body=True when specified.
    """
    sender = ResponseSender()
    send, sent_messages = create_send_callable()
    
    asyncio.get_event_loop().run_until_complete(
        sender.send_body(send, body=b"chunk", more_body=True)
    )
    
    message = sent_messages[0]
    
    if message.get("more_body") is not True:
        errmsg = f"Expected more_body=True, got {message.get('more_body')}"
        raise AssertionError(errmsg)
    
    return


def test_send_body_includes_more_body_false():
    """
        Test that send_body() includes more_body=False when specified.
    """
    sender = ResponseSender()
    send, sent_messages = create_send_callable()
    
    asyncio.get_event_loop().run_until_complete(
        sender.send_body(send, body=b"final", more_body=False)
    )
    
    message = sent_messages[0]
    
    if message.get("more_body") is not False:
        errmsg = f"Expected more_body=False, got {message.get('more_body')}"
        raise AssertionError(errmsg)
    
    return


def test_send_body_defaults_more_body_to_false():
    """
        Test that send_body() defaults more_body to False.
    """
    sender = ResponseSender()
    send, sent_messages = create_send_callable()
    
    asyncio.get_event_loop().run_until_complete(
        sender.send_body(send, body=b"content")
    )
    
    message = sent_messages[0]
    
    if message.get("more_body") is not False:
        errmsg = f"Expected more_body=False by default, got {message.get('more_body')}"
        raise AssertionError(errmsg)
    
    return


def test_send_body_handles_empty_body():
    """
        Test that send_body() handles empty body.
    """
    sender = ResponseSender()
    send, sent_messages = create_send_callable()
    
    asyncio.get_event_loop().run_until_complete(
        sender.send_body(send, body=b"", more_body=False)
    )
    
    message = sent_messages[0]
    
    if message.get("body") != b"":
        errmsg = f"Expected empty body, got '{message.get('body')}'"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for ResponseSender - format_headers() Method
# =============================================================================

def test_format_headers_converts_dict_to_byte_tuples():
    """
        Test that format_headers() converts dict to list of byte tuples.
    """
    sender = ResponseSender()
    
    headers = {
        "Content-Type": "text/html",
        "X-Custom": "value"
    }
    
    result = sender.format_headers(headers)
    
    if not isinstance(result, list):
        errmsg = f"Expected list, got {type(result)}"
        raise AssertionError(errmsg)
    
    if len(result) != 2:
        errmsg = f"Expected 2 headers, got {len(result)}"
        raise AssertionError(errmsg)
    
    return


def test_format_headers_lowercases_header_names():
    """
        Test that format_headers() lowercases header names.
    """
    sender = ResponseSender()
    
    headers = {
        "Content-Type": "text/html",
        "X-CUSTOM-HEADER": "value"
    }
    
    result = sender.format_headers(headers)
    
    # Convert to dict for easier checking
    result_dict = {name: value for name, value in result}
    
    if b"content-type" not in result_dict:
        errmsg = "Expected 'content-type' (lowercase) in result"
        raise AssertionError(errmsg)
    
    if b"x-custom-header" not in result_dict:
        errmsg = "Expected 'x-custom-header' (lowercase) in result"
        raise AssertionError(errmsg)
    
    return


def test_format_headers_encodes_values_as_bytes():
    """
        Test that format_headers() encodes values as bytes.
    """
    sender = ResponseSender()
    
    headers = {
        "Content-Type": "application/json"
    }
    
    result = sender.format_headers(headers)
    
    name, value = result[0]
    
    if not isinstance(name, bytes):
        errmsg = f"Expected name to be bytes, got {type(name)}"
        raise AssertionError(errmsg)
    
    if not isinstance(value, bytes):
        errmsg = f"Expected value to be bytes, got {type(value)}"
        raise AssertionError(errmsg)
    
    if value != b"application/json":
        errmsg = f"Expected value b'application/json', got {value}"
        raise AssertionError(errmsg)
    
    return


def test_format_headers_handles_empty_dict():
    """
        Test that format_headers() handles empty dict.
    """
    sender = ResponseSender()
    
    headers = {}
    
    result = sender.format_headers(headers)
    
    if len(result) != 0:
        errmsg = f"Expected empty list, got {len(result)} items"
        raise AssertionError(errmsg)
    
    return


def test_format_headers_preserves_header_values():
    """
        Test that format_headers() preserves header values.
    """
    sender = ResponseSender()
    
    headers = {
        "Content-Length": "1234",
        "Cache-Control": "no-cache, no-store"
    }
    
    result = sender.format_headers(headers)
    result_dict = {name: value for name, value in result}
    
    if result_dict.get(b"content-length") != b"1234":
        errmsg = f"Expected content-length='1234', got {result_dict.get(b'content-length')}"
        raise AssertionError(errmsg)
    
    if result_dict.get(b"cache-control") != b"no-cache, no-store":
        errmsg = f"Expected cache-control='no-cache, no-store', got {result_dict.get(b'cache-control')}"
        raise AssertionError(errmsg)
    
    return



# =============================================================================
# Unit Tests for ResponseSender - send_streaming() Method
# =============================================================================

def test_send_streaming_sends_start_message_first():
    """
        Test that send_streaming() sends start message before body.
    """
    sender = ResponseSender()
    send, sent_messages = create_send_callable()
    
    async def run_test():
        body_stream = create_async_body_generator([b"Hello"])
        await sender.send_streaming(
            send,
            status=200,
            headers=[(b"content-type", b"text/plain")],
            body_stream=body_stream
        )
        return
    
    asyncio.get_event_loop().run_until_complete(run_test())
    
    if len(sent_messages) < 2:
        errmsg = f"Expected at least 2 messages, got {len(sent_messages)}"
        raise AssertionError(errmsg)
    
    first_message = sent_messages[0]
    
    if first_message.get("type") != MESSAGE_HTTP_RESPONSE_START:
        errmsg = f"Expected first message to be response start, got {first_message.get('type')}"
        raise AssertionError(errmsg)
    
    return


def test_send_streaming_sends_body_messages_after_start():
    """
        Test that send_streaming() sends body messages after start.
    """
    sender = ResponseSender()
    send, sent_messages = create_send_callable()
    
    async def run_test():
        body_stream = create_async_body_generator([b"Hello", b"World"])
        await sender.send_streaming(
            send,
            status=200,
            headers=[],
            body_stream=body_stream
        )
        return
    
    asyncio.get_event_loop().run_until_complete(run_test())
    
    # First message should be start
    if sent_messages[0].get("type") != MESSAGE_HTTP_RESPONSE_START:
        errmsg = "Expected first message to be response start"
        raise AssertionError(errmsg)
    
    # Remaining messages should be body
    for i in range(1, len(sent_messages)):
        if sent_messages[i].get("type") != MESSAGE_HTTP_RESPONSE_BODY:
            errmsg = f"Expected message {i} to be response body"
            raise AssertionError(errmsg)
    
    return


def test_send_streaming_sets_more_body_true_for_intermediate_chunks():
    """
        Test that send_streaming() sets more_body=True for intermediate chunks.
    """
    sender = ResponseSender()
    send, sent_messages = create_send_callable()
    
    async def run_test():
        body_stream = create_async_body_generator([b"chunk1", b"chunk2", b"chunk3"])
        await sender.send_streaming(
            send,
            status=200,
            headers=[],
            body_stream=body_stream
        )
        return
    
    asyncio.get_event_loop().run_until_complete(run_test())
    
    # Skip the start message (index 0)
    body_messages = sent_messages[1:]
    
    if len(body_messages) < 2:
        errmsg = f"Expected at least 2 body messages, got {len(body_messages)}"
        raise AssertionError(errmsg)
    
    # All intermediate chunks should have more_body=True
    for i in range(len(body_messages) - 1):
        if body_messages[i].get("more_body") is not True:
            errmsg = f"Expected more_body=True for chunk {i}, got {body_messages[i].get('more_body')}"
            raise AssertionError(errmsg)
    
    return


def test_send_streaming_sets_more_body_false_for_final_chunk():
    """
        Test that send_streaming() sets more_body=False for final chunk.
    """
    sender = ResponseSender()
    send, sent_messages = create_send_callable()
    
    async def run_test():
        body_stream = create_async_body_generator([b"chunk1", b"chunk2", b"final"])
        await sender.send_streaming(
            send,
            status=200,
            headers=[],
            body_stream=body_stream
        )
        return
    
    asyncio.get_event_loop().run_until_complete(run_test())
    
    # Last message should have more_body=False
    last_message = sent_messages[-1]
    
    if last_message.get("more_body") is not False:
        errmsg = f"Expected more_body=False for final chunk, got {last_message.get('more_body')}"
        raise AssertionError(errmsg)
    
    return


def test_send_streaming_handles_single_chunk():
    """
        Test that send_streaming() handles single chunk stream.
    """
    sender = ResponseSender()
    send, sent_messages = create_send_callable()
    
    async def run_test():
        body_stream = create_async_body_generator([b"only chunk"])
        await sender.send_streaming(
            send,
            status=200,
            headers=[],
            body_stream=body_stream
        )
        return
    
    asyncio.get_event_loop().run_until_complete(run_test())
    
    # Should have start + 1 body message
    if len(sent_messages) != 2:
        errmsg = f"Expected 2 messages, got {len(sent_messages)}"
        raise AssertionError(errmsg)
    
    # Body message should have more_body=False
    body_message = sent_messages[1]
    
    if body_message.get("more_body") is not False:
        errmsg = f"Expected more_body=False for single chunk, got {body_message.get('more_body')}"
        raise AssertionError(errmsg)
    
    if body_message.get("body") != b"only chunk":
        errmsg = f"Expected body 'only chunk', got {body_message.get('body')}"
        raise AssertionError(errmsg)
    
    return


def test_send_streaming_handles_empty_stream():
    """
        Test that send_streaming() handles empty stream.
    """
    sender = ResponseSender()
    send, sent_messages = create_send_callable()
    
    async def run_test():
        body_stream = create_async_body_generator([])
        await sender.send_streaming(
            send,
            status=204,
            headers=[],
            body_stream=body_stream
        )
        return
    
    asyncio.get_event_loop().run_until_complete(run_test())
    
    # Should have start + 1 empty body message
    if len(sent_messages) != 2:
        errmsg = f"Expected 2 messages, got {len(sent_messages)}"
        raise AssertionError(errmsg)
    
    # Body message should be empty with more_body=False
    body_message = sent_messages[1]
    
    if body_message.get("body") != b"":
        errmsg = f"Expected empty body, got {body_message.get('body')}"
        raise AssertionError(errmsg)
    
    if body_message.get("more_body") is not False:
        errmsg = f"Expected more_body=False, got {body_message.get('more_body')}"
        raise AssertionError(errmsg)
    
    return


def test_send_streaming_preserves_chunk_content():
    """
        Test that send_streaming() preserves chunk content.
    """
    sender = ResponseSender()
    send, sent_messages = create_send_callable()
    
    chunks = [b"Hello, ", b"World!", b" How are you?"]
    
    async def run_test():
        body_stream = create_async_body_generator(chunks)
        await sender.send_streaming(
            send,
            status=200,
            headers=[],
            body_stream=body_stream
        )
        return
    
    asyncio.get_event_loop().run_until_complete(run_test())
    
    # Extract body content from messages
    body_messages = sent_messages[1:]
    received_chunks = [msg.get("body") for msg in body_messages]
    
    if received_chunks != chunks:
        errmsg = f"Expected chunks {chunks}, got {received_chunks}"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for ResponseSender - send() Method
# =============================================================================

def test_send_sends_complete_response():
    """
        Test that send() sends complete response with start and body.
    """
    sender = ResponseSender()
    send, sent_messages = create_send_callable()
    
    response = MockResponse(
        status_code=200,
        headers={"Content-Type": "text/plain"},
        body=b"Hello, World!"
    )
    
    asyncio.get_event_loop().run_until_complete(
        sender.send(send, response)
    )
    
    if len(sent_messages) != 2:
        errmsg = f"Expected 2 messages, got {len(sent_messages)}"
        raise AssertionError(errmsg)
    
    return


def test_send_sends_start_before_body():
    """
        Test that send() sends start message before body message.
    """
    sender = ResponseSender()
    send, sent_messages = create_send_callable()
    
    response = MockResponse(
        status_code=200,
        headers={"Content-Type": "text/plain"},
        body=b"Hello"
    )
    
    asyncio.get_event_loop().run_until_complete(
        sender.send(send, response)
    )
    
    first_message = sent_messages[0]
    second_message = sent_messages[1]
    
    if first_message.get("type") != MESSAGE_HTTP_RESPONSE_START:
        errmsg = f"Expected first message to be start, got {first_message.get('type')}"
        raise AssertionError(errmsg)
    
    if second_message.get("type") != MESSAGE_HTTP_RESPONSE_BODY:
        errmsg = f"Expected second message to be body, got {second_message.get('type')}"
        raise AssertionError(errmsg)
    
    return


def test_send_includes_status_code_from_response():
    """
        Test that send() includes status code from response.
    """
    sender = ResponseSender()
    send, sent_messages = create_send_callable()
    
    response = MockResponse(
        status_code=404,
        headers={},
        body=b"Not Found"
    )
    
    asyncio.get_event_loop().run_until_complete(
        sender.send(send, response)
    )
    
    start_message = sent_messages[0]
    
    if start_message.get("status") != 404:
        errmsg = f"Expected status 404, got {start_message.get('status')}"
        raise AssertionError(errmsg)
    
    return


def test_send_formats_headers_from_response():
    """
        Test that send() formats headers from response dict.
    """
    sender = ResponseSender()
    send, sent_messages = create_send_callable()
    
    response = MockResponse(
        status_code=200,
        headers={"Content-Type": "application/json", "X-Custom": "value"},
        body=b"{}"
    )
    
    asyncio.get_event_loop().run_until_complete(
        sender.send(send, response)
    )
    
    start_message = sent_messages[0]
    headers = start_message.get("headers", [])
    
    # Convert to dict for easier checking
    headers_dict = {name: value for name, value in headers}
    
    if b"content-type" not in headers_dict:
        errmsg = "Expected 'content-type' header in message"
        raise AssertionError(errmsg)
    
    if headers_dict.get(b"content-type") != b"application/json":
        errmsg = f"Expected content-type='application/json', got {headers_dict.get(b'content-type')}"
        raise AssertionError(errmsg)
    
    return


def test_send_includes_body_content():
    """
        Test that send() includes body content from response.
    """
    sender = ResponseSender()
    send, sent_messages = create_send_callable()
    
    body_content = b"Response body content"
    response = MockResponse(
        status_code=200,
        headers={},
        body=body_content
    )
    
    asyncio.get_event_loop().run_until_complete(
        sender.send(send, response)
    )
    
    body_message = sent_messages[1]
    
    if body_message.get("body") != body_content:
        errmsg = f"Expected body '{body_content}', got '{body_message.get('body')}'"
        raise AssertionError(errmsg)
    
    return


def test_send_sets_more_body_false_for_complete_response():
    """
        Test that send() sets more_body=False for complete response.
    """
    sender = ResponseSender()
    send, sent_messages = create_send_callable()
    
    response = MockResponse(
        status_code=200,
        headers={},
        body=b"Complete"
    )
    
    asyncio.get_event_loop().run_until_complete(
        sender.send(send, response)
    )
    
    body_message = sent_messages[1]
    
    if body_message.get("more_body") is not False:
        errmsg = f"Expected more_body=False, got {body_message.get('more_body')}"
        raise AssertionError(errmsg)
    
    return


def test_send_handles_string_body():
    """
        Test that send() handles string body by encoding to UTF-8.
    """
    sender = ResponseSender()
    send, sent_messages = create_send_callable()
    
    response = MockResponse(
        status_code=200,
        headers={},
        body="Hello, World!"
    )
    
    asyncio.get_event_loop().run_until_complete(
        sender.send(send, response)
    )
    
    body_message = sent_messages[1]
    
    if body_message.get("body") != b"Hello, World!":
        errmsg = f"Expected body b'Hello, World!', got {body_message.get('body')}"
        raise AssertionError(errmsg)
    
    return


def test_send_handles_empty_body():
    """
        Test that send() handles empty body.
    """
    sender = ResponseSender()
    send, sent_messages = create_send_callable()
    
    response = MockResponse(
        status_code=204,
        headers={},
        body=b""
    )
    
    asyncio.get_event_loop().run_until_complete(
        sender.send(send, response)
    )
    
    body_message = sent_messages[1]
    
    if body_message.get("body") != b"":
        errmsg = f"Expected empty body, got {body_message.get('body')}"
        raise AssertionError(errmsg)
    
    return


def test_send_handles_streaming_response():
    """
        Test that send() handles streaming response with async generator body.
    """
    sender = ResponseSender()
    send, sent_messages = create_send_callable()
    
    async def run_test():
        body_stream = create_async_body_generator([b"chunk1", b"chunk2"])
        response = MockResponse(
            status_code=200,
            headers={"Content-Type": "text/plain"},
            body=body_stream
        )
        await sender.send(send, response)
        return
    
    asyncio.get_event_loop().run_until_complete(run_test())
    
    # Should have start + 2 body messages
    if len(sent_messages) != 3:
        errmsg = f"Expected 3 messages, got {len(sent_messages)}"
        raise AssertionError(errmsg)
    
    # First should be start
    if sent_messages[0].get("type") != MESSAGE_HTTP_RESPONSE_START:
        errmsg = "Expected first message to be response start"
        raise AssertionError(errmsg)
    
    # Last body message should have more_body=False
    if sent_messages[-1].get("more_body") is not False:
        errmsg = "Expected last body message to have more_body=False"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for ResponseSender - Message Ordering (Property 3)
# =============================================================================

def test_message_ordering_start_before_body():
    """
        Test that response start is always sent before body messages.
        
        This validates Property 3: HTTP Response Message Ordering.
    """
    sender = ResponseSender()
    send, sent_messages = create_send_callable()
    
    response = MockResponse(
        status_code=200,
        headers={"Content-Type": "text/html"},
        body=b"<html><body>Hello</body></html>"
    )
    
    asyncio.get_event_loop().run_until_complete(
        sender.send(send, response)
    )
    
    # Find indices of start and body messages
    start_indices = []
    body_indices = []
    
    for i, msg in enumerate(sent_messages):
        if msg.get("type") == MESSAGE_HTTP_RESPONSE_START:
            start_indices.append(i)
        elif msg.get("type") == MESSAGE_HTTP_RESPONSE_BODY:
            body_indices.append(i)
    
    # Should have exactly one start message
    if len(start_indices) != 1:
        errmsg = f"Expected exactly 1 start message, got {len(start_indices)}"
        raise AssertionError(errmsg)
    
    # All body messages should come after start
    start_index = start_indices[0]
    for body_index in body_indices:
        if body_index <= start_index:
            errmsg = f"Body message at index {body_index} came before start at {start_index}"
            raise AssertionError(errmsg)
    
    return


def test_message_ordering_final_body_has_more_body_false():
    """
        Test that final body message has more_body=False.
        
        This validates Property 3: HTTP Response Message Ordering.
    """
    sender = ResponseSender()
    send, sent_messages = create_send_callable()
    
    async def run_test():
        body_stream = create_async_body_generator([b"a", b"b", b"c", b"d"])
        response = MockResponse(
            status_code=200,
            headers={},
            body=body_stream
        )
        await sender.send(send, response)
        return
    
    asyncio.get_event_loop().run_until_complete(run_test())
    
    # Find all body messages
    body_messages = [
        msg for msg in sent_messages
        if msg.get("type") == MESSAGE_HTTP_RESPONSE_BODY
    ]
    
    if len(body_messages) == 0:
        errmsg = "Expected at least one body message"
        raise AssertionError(errmsg)
    
    # Last body message should have more_body=False
    last_body = body_messages[-1]
    
    if last_body.get("more_body") is not False:
        errmsg = f"Expected final body to have more_body=False, got {last_body.get('more_body')}"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Random Generators for Property-Based Tests
# =============================================================================

import random
import string


# Valid HTTP status codes for response generation
VALID_STATUS_CODES = [
    200, 201, 202, 204, 301, 302, 304, 307, 308,
    400, 401, 403, 404, 405, 409, 413, 422, 429,
    500, 501, 502, 503, 504,
]

# Common header names for generation
COMMON_RESPONSE_HEADERS = [
    "content-type", "content-length", "cache-control", "etag",
    "x-request-id", "server", "date", "vary", "location",
]


def generate_random_string(min_length: int = 1, max_length: int = 20) -> str:
    """Generate a random alphanumeric string."""
    length = random.randint(min_length, max_length)
    chars = string.ascii_lowercase + string.digits
    rtnval = "".join(random.choice(chars) for _ in range(length))
    return rtnval


def generate_random_status_code() -> int:
    """Generate a random valid HTTP status code."""
    rtnval = random.choice(VALID_STATUS_CODES)
    return rtnval


def generate_random_headers_dict() -> Dict[str, str]:
    """Generate a random dict of response headers."""
    num_headers = random.randint(0, 5)
    headers: Dict[str, str] = {}
    used_names: set = set()

    for _ in range(num_headers):
        name = random.choice(COMMON_RESPONSE_HEADERS)
        if name in used_names:
            continue
        used_names.add(name)
        value = generate_random_string(1, 30)
        headers[name] = value

    return headers


def generate_random_body_bytes() -> bytes:
    """Generate random body content as bytes."""
    length = random.randint(0, 500)
    rtnval = bytes(random.randint(0, 255) for _ in range(length))
    return rtnval


def generate_random_body_chunks() -> List[bytes]:
    """Generate a random list of body chunks for streaming."""
    num_chunks = random.randint(0, 8)
    chunks: List[bytes] = []
    for _ in range(num_chunks):
        chunk_size = random.randint(1, 200)
        chunk = bytes(random.randint(0, 255) for _ in range(chunk_size))
        chunks.append(chunk)
    return chunks


# =============================================================================
# Property-Based Tests
# =============================================================================

# Feature: asgi-layer, Property 3: HTTP Response Message Ordering
# *For any* HTTP response, the application SHALL send exactly one
# "http.response.start" message before any "http.response.body" messages,
# and the final body message SHALL have more_body=False.
# **Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.8, 4.9**


def test_property_3_complete_response_message_ordering():
    """
        Property 3: HTTP Response Message Ordering - Complete Responses

        For any complete (non-streaming) HTTP response with random status
        code, headers, and body, the ResponseSender SHALL send exactly one
        http.response.start message followed by exactly one http.response.body
        message, and the body message SHALL have more_body=False.

        **Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.8**
    """
    sender = ResponseSender()

    for iteration in range(100):
        send, sent_messages = create_send_callable()

        status_code = generate_random_status_code()
        headers = generate_random_headers_dict()
        body = generate_random_body_bytes()

        response = MockResponse(
            status_code=status_code,
            headers=headers,
            body=body
        )

        asyncio.get_event_loop().run_until_complete(sender.send(send, response))

        # Property: at least two messages sent (start + body)
        if len(sent_messages) < 2:
            errmsg = (
                f"Iteration {iteration}: expected at least 2 messages, "
                f"got {len(sent_messages)}"
            )
            raise AssertionError(errmsg)

        # Property: exactly one start message (Req 4.1)
        start_messages = [
            msg for msg in sent_messages
            if msg.get("type") == MESSAGE_HTTP_RESPONSE_START
        ]
        if len(start_messages) != 1:
            errmsg = (
                f"Iteration {iteration}: expected exactly 1 start message, "
                f"got {len(start_messages)}"
            )
            raise AssertionError(errmsg)

        # Property: start message contains status code (Req 4.2)
        start_msg = start_messages[0]
        if start_msg.get("status") != status_code:
            errmsg = (
                f"Iteration {iteration}: start status {start_msg.get('status')} "
                f"!= expected {status_code}"
            )
            raise AssertionError(errmsg)

        # Property: start message contains headers as byte tuples (Req 4.3)
        msg_headers = start_msg.get("headers", [])
        if not isinstance(msg_headers, list):
            errmsg = (
                f"Iteration {iteration}: headers should be a list, "
                f"got {type(msg_headers).__name__}"
            )
            raise AssertionError(errmsg)

        for header_pair in msg_headers:
            if not isinstance(header_pair, tuple) or len(header_pair) != 2:
                errmsg = (
                    f"Iteration {iteration}: header should be (name, value) tuple, "
                    f"got {header_pair!r}"
                )
                raise AssertionError(errmsg)
            if not isinstance(header_pair[0], bytes) or not isinstance(header_pair[1], bytes):
                errmsg = (
                    f"Iteration {iteration}: header name and value should be bytes, "
                    f"got ({type(header_pair[0]).__name__}, {type(header_pair[1]).__name__})"
                )
                raise AssertionError(errmsg)

        # Property: at least one body message (Req 4.4)
        body_messages = [
            msg for msg in sent_messages
            if msg.get("type") == MESSAGE_HTTP_RESPONSE_BODY
        ]
        if len(body_messages) < 1:
            errmsg = (
                f"Iteration {iteration}: expected at least 1 body message, "
                f"got {len(body_messages)}"
            )
            raise AssertionError(errmsg)

        # Property: start message comes before all body messages (Req 4.8)
        start_index = next(
            i for i, msg in enumerate(sent_messages)
            if msg.get("type") == MESSAGE_HTTP_RESPONSE_START
        )
        for i, msg in enumerate(sent_messages):
            if msg.get("type") == MESSAGE_HTTP_RESPONSE_BODY and i <= start_index:
                errmsg = (
                    f"Iteration {iteration}: body message at index {i} "
                    f"came before or at start message index {start_index}"
                )
                raise AssertionError(errmsg)

        # Property: body messages contain bytes (Req 4.5)
        for body_msg in body_messages:
            if not isinstance(body_msg.get("body"), bytes):
                errmsg = (
                    f"Iteration {iteration}: body should be bytes, "
                    f"got {type(body_msg.get('body')).__name__}"
                )
                raise AssertionError(errmsg)

        # Property: final body message has more_body=False (Req 4.6, 4.9)
        last_body = body_messages[-1]
        if last_body.get("more_body") is not False:
            errmsg = (
                f"Iteration {iteration}: final body more_body should be False, "
                f"got {last_body.get('more_body')}"
            )
            raise AssertionError(errmsg)

    return


def test_property_3_streaming_response_message_ordering():
    """
        Property 3: HTTP Response Message Ordering - Streaming Responses

        For any streaming HTTP response with random status code, headers,
        and body chunks, the ResponseSender SHALL send exactly one
        http.response.start message before all http.response.body messages,
        intermediate body messages SHALL have more_body=True, and the final
        body message SHALL have more_body=False.

        **Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.8, 4.9**
    """
    sender = ResponseSender()

    for iteration in range(100):
        send, sent_messages = create_send_callable()

        status_code = generate_random_status_code()
        headers = generate_random_headers_dict()
        chunks = generate_random_body_chunks()

        async def run_streaming():
            body_stream = create_async_body_generator(chunks)
            await sender.send_streaming(
                send,
                status_code,
                sender.format_headers(headers),
                body_stream
            )
            return

        asyncio.get_event_loop().run_until_complete(run_streaming())

        # Property: at least two messages sent (start + at least one body)
        if len(sent_messages) < 2:
            errmsg = (
                f"Iteration {iteration}: expected at least 2 messages, "
                f"got {len(sent_messages)}"
            )
            raise AssertionError(errmsg)

        # Property: exactly one start message (Req 4.1)
        start_messages = [
            msg for msg in sent_messages
            if msg.get("type") == MESSAGE_HTTP_RESPONSE_START
        ]
        if len(start_messages) != 1:
            errmsg = (
                f"Iteration {iteration}: expected exactly 1 start message, "
                f"got {len(start_messages)}"
            )
            raise AssertionError(errmsg)

        # Property: start message contains correct status code (Req 4.2)
        if start_messages[0].get("status") != status_code:
            errmsg = (
                f"Iteration {iteration}: start status {start_messages[0].get('status')} "
                f"!= expected {status_code}"
            )
            raise AssertionError(errmsg)

        # Property: start message is the first message sent (Req 4.8)
        if sent_messages[0].get("type") != MESSAGE_HTTP_RESPONSE_START:
            errmsg = (
                f"Iteration {iteration}: first message should be start, "
                f"got type '{sent_messages[0].get('type')}'"
            )
            raise AssertionError(errmsg)

        # Property: all remaining messages are body messages
        body_messages = [
            msg for msg in sent_messages
            if msg.get("type") == MESSAGE_HTTP_RESPONSE_BODY
        ]

        if len(body_messages) < 1:
            errmsg = (
                f"Iteration {iteration}: expected at least 1 body message, "
                f"got {len(body_messages)}"
            )
            raise AssertionError(errmsg)

        # Property: all body messages contain bytes (Req 4.5)
        for body_msg in body_messages:
            if not isinstance(body_msg.get("body"), bytes):
                errmsg = (
                    f"Iteration {iteration}: body should be bytes, "
                    f"got {type(body_msg.get('body')).__name__}"
                )
                raise AssertionError(errmsg)

        # Property: all body messages have more_body boolean (Req 4.6)
        for body_msg in body_messages:
            if not isinstance(body_msg.get("more_body"), bool):
                errmsg = (
                    f"Iteration {iteration}: more_body should be bool, "
                    f"got {type(body_msg.get('more_body')).__name__}"
                )
                raise AssertionError(errmsg)

        # Property: intermediate body messages have more_body=True (Req 4.9)
        for body_msg in body_messages[:-1]:
            if body_msg.get("more_body") is not True:
                errmsg = (
                    f"Iteration {iteration}: intermediate body more_body "
                    f"should be True, got {body_msg.get('more_body')}"
                )
                raise AssertionError(errmsg)

        # Property: final body message has more_body=False (Req 4.9)
        last_body = body_messages[-1]
        if last_body.get("more_body") is not False:
            errmsg = (
                f"Iteration {iteration}: final body more_body should be False, "
                f"got {last_body.get('more_body')}"
            )
            raise AssertionError(errmsg)

        # Property: streamed content matches original chunks
        if len(chunks) > 0:
            streamed_content = b"".join(
                msg.get("body", b"") for msg in body_messages
            )
            original_content = b"".join(chunks)
            if streamed_content != original_content:
                errmsg = (
                    f"Iteration {iteration}: streamed content length "
                    f"{len(streamed_content)} != original {len(original_content)}"
                )
                raise AssertionError(errmsg)

    return


def test_property_3_send_via_response_object_message_ordering():
    """
        Property 3: HTTP Response Message Ordering - Via send() Method

        For any Response object (with bytes, str, or streaming body),
        the send() method SHALL produce exactly one http.response.start
        followed by body messages, with the final body having more_body=False.

        **Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.8, 4.9**
    """
    sender = ResponseSender()

    for iteration in range(100):
        send, sent_messages = create_send_callable()

        status_code = generate_random_status_code()
        headers = generate_random_headers_dict()

        # Randomly choose body type: bytes, str, or streaming
        body_type = random.choice(["bytes", "str", "streaming"])

        if body_type == "bytes":
            body = generate_random_body_bytes()
        elif body_type == "str":
            body = generate_random_string(0, 200)
        else:
            chunks = generate_random_body_chunks()
            body = create_async_body_generator(chunks)

        response = MockResponse(
            status_code=status_code,
            headers=headers,
            body=body
        )

        asyncio.get_event_loop().run_until_complete(sender.send(send, response))

        # Property: exactly one start message (Req 4.1)
        start_messages = [
            msg for msg in sent_messages
            if msg.get("type") == MESSAGE_HTTP_RESPONSE_START
        ]
        if len(start_messages) != 1:
            errmsg = (
                f"Iteration {iteration} (body_type={body_type}): "
                f"expected exactly 1 start message, got {len(start_messages)}"
            )
            raise AssertionError(errmsg)

        # Property: start is first message (Req 4.8)
        if sent_messages[0].get("type") != MESSAGE_HTTP_RESPONSE_START:
            errmsg = (
                f"Iteration {iteration} (body_type={body_type}): "
                f"first message should be start, got '{sent_messages[0].get('type')}'"
            )
            raise AssertionError(errmsg)

        # Property: at least one body message (Req 4.4)
        body_messages = [
            msg for msg in sent_messages
            if msg.get("type") == MESSAGE_HTTP_RESPONSE_BODY
        ]
        if len(body_messages) < 1:
            errmsg = (
                f"Iteration {iteration} (body_type={body_type}): "
                f"expected at least 1 body message, got {len(body_messages)}"
            )
            raise AssertionError(errmsg)

        # Property: final body has more_body=False (Req 4.6, 4.9)
        last_body = body_messages[-1]
        if last_body.get("more_body") is not False:
            errmsg = (
                f"Iteration {iteration} (body_type={body_type}): "
                f"final body more_body should be False, got {last_body.get('more_body')}"
            )
            raise AssertionError(errmsg)

        # Property: no messages have unknown types
        valid_types = {MESSAGE_HTTP_RESPONSE_START, MESSAGE_HTTP_RESPONSE_BODY}
        for msg in sent_messages:
            if msg.get("type") not in valid_types:
                errmsg = (
                    f"Iteration {iteration} (body_type={body_type}): "
                    f"unexpected message type '{msg.get('type')}'"
                )
                raise AssertionError(errmsg)

    return
