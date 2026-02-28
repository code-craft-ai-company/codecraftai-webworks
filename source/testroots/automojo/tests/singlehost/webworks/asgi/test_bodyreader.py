"""
    Tests for the BodyReader class.
    
    This module contains unit tests for the ASGI body reader functionality
    including buffered reading, streaming, size limits, and disconnection handling.
"""

import asyncio
from typing import Any, Dict, List

from automojo.webworks.asgi.bodyreader import BodyReader
from automojo.webworks.asgi.constants import (
    MESSAGE_HTTP_REQUEST,
    MESSAGE_HTTP_DISCONNECT,
)
from automojo.webworks.asgi.exceptions import (
    ClientDisconnected,
    RequestEntityTooLarge,
)


# =============================================================================
# Helper Functions for Creating Mock Receive Callables
# =============================================================================

def create_receive_callable(messages: List[Dict[str, Any]]):
    """
        Create a mock receive callable that returns messages in sequence.
        
        :param messages: List of ASGI messages to return.
        
        :returns: Async callable that returns messages.
    """
    message_index = [0]
    
    async def receive() -> Dict[str, Any]:
        idx = message_index[0]
        if idx < len(messages):
            message_index[0] = idx + 1
            return messages[idx]
        else:
            # Return empty body with more_body=False if exhausted
            return {"type": MESSAGE_HTTP_REQUEST, "body": b"", "more_body": False}
    
    return receive


# =============================================================================
# Unit Tests for BodyReader - Constructor and Properties
# =============================================================================

def test_bodyreader_constructor_sets_max_size():
    """
        Test that BodyReader constructor sets max_size correctly.
    """
    reader = BodyReader(max_size=1024)
    
    result = reader.max_size
    expected = 1024
    
    if result != expected:
        errmsg = f"Expected max_size {expected}, got {result}"
        raise AssertionError(errmsg)
    
    return


def test_bodyreader_constructor_defaults_to_unlimited():
    """
        Test that BodyReader defaults to unlimited size (0).
    """
    reader = BodyReader()
    
    result = reader.max_size
    expected = 0
    
    if result != expected:
        errmsg = f"Expected default max_size {expected}, got {result}"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for BodyReader - read() Method
# =============================================================================

def test_read_returns_empty_body_when_no_content():
    """
        Test that read() returns empty bytes when body is empty.
    """
    reader = BodyReader()
    messages = [
        {"type": MESSAGE_HTTP_REQUEST, "body": b"", "more_body": False}
    ]
    receive = create_receive_callable(messages)
    
    result = asyncio.get_event_loop().run_until_complete(reader.read(receive))
    
    expected = b""
    if result != expected:
        errmsg = f"Expected empty body, got {len(result)} bytes"
        raise AssertionError(errmsg)
    
    return


def test_read_returns_single_chunk_body():
    """
        Test that read() returns body from single chunk.
    """
    reader = BodyReader()
    body_content = b"Hello, World!"
    messages = [
        {"type": MESSAGE_HTTP_REQUEST, "body": body_content, "more_body": False}
    ]
    receive = create_receive_callable(messages)
    
    result = asyncio.get_event_loop().run_until_complete(reader.read(receive))
    
    if result != body_content:
        errmsg = f"Expected body '{body_content}', got '{result}'"
        raise AssertionError(errmsg)
    
    return


def test_read_accumulates_multiple_chunks():
    """
        Test that read() accumulates body from multiple chunks.
    """
    reader = BodyReader()
    messages = [
        {"type": MESSAGE_HTTP_REQUEST, "body": b"Hello, ", "more_body": True},
        {"type": MESSAGE_HTTP_REQUEST, "body": b"World!", "more_body": False},
    ]
    receive = create_receive_callable(messages)
    
    result = asyncio.get_event_loop().run_until_complete(reader.read(receive))
    
    expected = b"Hello, World!"
    if result != expected:
        errmsg = f"Expected body '{expected}', got '{result}'"
        raise AssertionError(errmsg)
    
    return


def test_read_handles_many_small_chunks():
    """
        Test that read() handles many small body chunks.
    """
    reader = BodyReader()
    chunks = [b"a", b"b", b"c", b"d", b"e"]
    messages = []
    for i, chunk in enumerate(chunks):
        is_last = (i == len(chunks) - 1)
        messages.append({
            "type": MESSAGE_HTTP_REQUEST,
            "body": chunk,
            "more_body": not is_last
        })
    receive = create_receive_callable(messages)
    
    result = asyncio.get_event_loop().run_until_complete(reader.read(receive))
    
    expected = b"abcde"
    if result != expected:
        errmsg = f"Expected body '{expected}', got '{result}'"
        raise AssertionError(errmsg)
    
    return


def test_read_handles_empty_intermediate_chunks():
    """
        Test that read() handles empty intermediate chunks.
    """
    reader = BodyReader()
    messages = [
        {"type": MESSAGE_HTTP_REQUEST, "body": b"Hello", "more_body": True},
        {"type": MESSAGE_HTTP_REQUEST, "body": b"", "more_body": True},
        {"type": MESSAGE_HTTP_REQUEST, "body": b"World", "more_body": False},
    ]
    receive = create_receive_callable(messages)
    
    result = asyncio.get_event_loop().run_until_complete(reader.read(receive))
    
    expected = b"HelloWorld"
    if result != expected:
        errmsg = f"Expected body '{expected}', got '{result}'"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for BodyReader - Size Limiting
# =============================================================================

def test_read_raises_when_content_length_exceeds_max_size():
    """
        Test that read() raises RequestEntityTooLarge when content_length exceeds max_size.
    """
    reader = BodyReader(max_size=100)
    messages = [
        {"type": MESSAGE_HTTP_REQUEST, "body": b"x" * 200, "more_body": False}
    ]
    receive = create_receive_callable(messages)
    
    exception_raised = False
    exception_instance = None
    
    try:
        asyncio.get_event_loop().run_until_complete(
            reader.read(receive, content_length=200)
        )
    except RequestEntityTooLarge as exc:
        exception_raised = True
        exception_instance = exc
    
    if not exception_raised:
        errmsg = "Expected RequestEntityTooLarge exception"
        raise AssertionError(errmsg)
    
    if exception_instance.max_size != 100:
        errmsg = f"Expected max_size 100, got {exception_instance.max_size}"
        raise AssertionError(errmsg)
    
    if exception_instance.actual_size != 200:
        errmsg = f"Expected actual_size 200, got {exception_instance.actual_size}"
        raise AssertionError(errmsg)
    
    return


def test_read_raises_when_accumulated_size_exceeds_max_size():
    """
        Test that read() raises RequestEntityTooLarge when accumulated size exceeds max_size.
    """
    reader = BodyReader(max_size=10)
    messages = [
        {"type": MESSAGE_HTTP_REQUEST, "body": b"12345", "more_body": True},
        {"type": MESSAGE_HTTP_REQUEST, "body": b"67890", "more_body": True},
        {"type": MESSAGE_HTTP_REQUEST, "body": b"extra", "more_body": False},
    ]
    receive = create_receive_callable(messages)
    
    exception_raised = False
    exception_instance = None
    
    try:
        asyncio.get_event_loop().run_until_complete(reader.read(receive))
    except RequestEntityTooLarge as exc:
        exception_raised = True
        exception_instance = exc
    
    if not exception_raised:
        errmsg = "Expected RequestEntityTooLarge exception"
        raise AssertionError(errmsg)
    
    if exception_instance.max_size != 10:
        errmsg = f"Expected max_size 10, got {exception_instance.max_size}"
        raise AssertionError(errmsg)
    
    return


def test_read_allows_body_within_max_size():
    """
        Test that read() allows body within max_size limit.
    """
    reader = BodyReader(max_size=100)
    body_content = b"x" * 50
    messages = [
        {"type": MESSAGE_HTTP_REQUEST, "body": body_content, "more_body": False}
    ]
    receive = create_receive_callable(messages)
    
    result = asyncio.get_event_loop().run_until_complete(reader.read(receive))
    
    if result != body_content:
        errmsg = f"Expected body of {len(body_content)} bytes, got {len(result)} bytes"
        raise AssertionError(errmsg)
    
    return


def test_read_allows_body_exactly_at_max_size():
    """
        Test that read() allows body exactly at max_size limit.
    """
    reader = BodyReader(max_size=50)
    body_content = b"x" * 50
    messages = [
        {"type": MESSAGE_HTTP_REQUEST, "body": body_content, "more_body": False}
    ]
    receive = create_receive_callable(messages)
    
    result = asyncio.get_event_loop().run_until_complete(reader.read(receive))
    
    if result != body_content:
        errmsg = f"Expected body of {len(body_content)} bytes, got {len(result)} bytes"
        raise AssertionError(errmsg)
    
    return


def test_read_unlimited_when_max_size_is_zero():
    """
        Test that read() allows any size when max_size is 0 (unlimited).
    """
    reader = BodyReader(max_size=0)
    body_content = b"x" * 10000
    messages = [
        {"type": MESSAGE_HTTP_REQUEST, "body": body_content, "more_body": False}
    ]
    receive = create_receive_callable(messages)
    
    result = asyncio.get_event_loop().run_until_complete(reader.read(receive))
    
    if result != body_content:
        errmsg = f"Expected body of {len(body_content)} bytes, got {len(result)} bytes"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for BodyReader - Client Disconnection
# =============================================================================

def test_read_raises_on_client_disconnect():
    """
        Test that read() raises ClientDisconnected on disconnect message.
    """
    reader = BodyReader()
    messages = [
        {"type": MESSAGE_HTTP_REQUEST, "body": b"partial", "more_body": True},
        {"type": MESSAGE_HTTP_DISCONNECT},
    ]
    receive = create_receive_callable(messages)
    
    exception_raised = False
    
    try:
        asyncio.get_event_loop().run_until_complete(reader.read(receive))
    except ClientDisconnected:
        exception_raised = True
    
    if not exception_raised:
        errmsg = "Expected ClientDisconnected exception"
        raise AssertionError(errmsg)
    
    return


def test_read_raises_on_immediate_disconnect():
    """
        Test that read() raises ClientDisconnected on immediate disconnect.
    """
    reader = BodyReader()
    messages = [
        {"type": MESSAGE_HTTP_DISCONNECT},
    ]
    receive = create_receive_callable(messages)
    
    exception_raised = False
    
    try:
        asyncio.get_event_loop().run_until_complete(reader.read(receive))
    except ClientDisconnected:
        exception_raised = True
    
    if not exception_raised:
        errmsg = "Expected ClientDisconnected exception"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for BodyReader - stream() Method
# =============================================================================

def test_stream_yields_single_chunk():
    """
        Test that stream() yields single body chunk.
    """
    reader = BodyReader()
    body_content = b"Hello, World!"
    messages = [
        {"type": MESSAGE_HTTP_REQUEST, "body": body_content, "more_body": False}
    ]
    receive = create_receive_callable(messages)
    
    async def collect_chunks():
        chunks = []
        async for chunk in reader.stream(receive):
            chunks.append(chunk)
        return chunks
    
    result = asyncio.get_event_loop().run_until_complete(collect_chunks())
    
    if len(result) != 1:
        errmsg = f"Expected 1 chunk, got {len(result)}"
        raise AssertionError(errmsg)
    
    if result[0] != body_content:
        errmsg = f"Expected chunk '{body_content}', got '{result[0]}'"
        raise AssertionError(errmsg)
    
    return


def test_stream_yields_multiple_chunks():
    """
        Test that stream() yields multiple body chunks.
    """
    reader = BodyReader()
    messages = [
        {"type": MESSAGE_HTTP_REQUEST, "body": b"Hello, ", "more_body": True},
        {"type": MESSAGE_HTTP_REQUEST, "body": b"World!", "more_body": False},
    ]
    receive = create_receive_callable(messages)
    
    async def collect_chunks():
        chunks = []
        async for chunk in reader.stream(receive):
            chunks.append(chunk)
        return chunks
    
    result = asyncio.get_event_loop().run_until_complete(collect_chunks())
    
    if len(result) != 2:
        errmsg = f"Expected 2 chunks, got {len(result)}"
        raise AssertionError(errmsg)
    
    if result[0] != b"Hello, ":
        errmsg = f"Expected first chunk 'Hello, ', got '{result[0]}'"
        raise AssertionError(errmsg)
    
    if result[1] != b"World!":
        errmsg = f"Expected second chunk 'World!', got '{result[1]}'"
        raise AssertionError(errmsg)
    
    return


def test_stream_skips_empty_chunks():
    """
        Test that stream() skips empty intermediate chunks.
    """
    reader = BodyReader()
    messages = [
        {"type": MESSAGE_HTTP_REQUEST, "body": b"Hello", "more_body": True},
        {"type": MESSAGE_HTTP_REQUEST, "body": b"", "more_body": True},
        {"type": MESSAGE_HTTP_REQUEST, "body": b"World", "more_body": False},
    ]
    receive = create_receive_callable(messages)
    
    async def collect_chunks():
        chunks = []
        async for chunk in reader.stream(receive):
            chunks.append(chunk)
        return chunks
    
    result = asyncio.get_event_loop().run_until_complete(collect_chunks())
    
    # Empty chunks should not be yielded
    if len(result) != 2:
        errmsg = f"Expected 2 non-empty chunks, got {len(result)}"
        raise AssertionError(errmsg)
    
    return


def test_stream_yields_nothing_for_empty_body():
    """
        Test that stream() yields nothing for empty body.
    """
    reader = BodyReader()
    messages = [
        {"type": MESSAGE_HTTP_REQUEST, "body": b"", "more_body": False}
    ]
    receive = create_receive_callable(messages)
    
    async def collect_chunks():
        chunks = []
        async for chunk in reader.stream(receive):
            chunks.append(chunk)
        return chunks
    
    result = asyncio.get_event_loop().run_until_complete(collect_chunks())
    
    if len(result) != 0:
        errmsg = f"Expected 0 chunks for empty body, got {len(result)}"
        raise AssertionError(errmsg)
    
    return


def test_stream_raises_on_size_exceeded():
    """
        Test that stream() raises RequestEntityTooLarge when size exceeded.
    """
    reader = BodyReader(max_size=10)
    messages = [
        {"type": MESSAGE_HTTP_REQUEST, "body": b"12345", "more_body": True},
        {"type": MESSAGE_HTTP_REQUEST, "body": b"67890", "more_body": True},
        {"type": MESSAGE_HTTP_REQUEST, "body": b"extra", "more_body": False},
    ]
    receive = create_receive_callable(messages)
    
    async def collect_chunks():
        chunks = []
        async for chunk in reader.stream(receive):
            chunks.append(chunk)
        return chunks
    
    exception_raised = False
    
    try:
        asyncio.get_event_loop().run_until_complete(collect_chunks())
    except RequestEntityTooLarge:
        exception_raised = True
    
    if not exception_raised:
        errmsg = "Expected RequestEntityTooLarge exception"
        raise AssertionError(errmsg)
    
    return


def test_stream_raises_on_client_disconnect():
    """
        Test that stream() raises ClientDisconnected on disconnect.
    """
    reader = BodyReader()
    messages = [
        {"type": MESSAGE_HTTP_REQUEST, "body": b"partial", "more_body": True},
        {"type": MESSAGE_HTTP_DISCONNECT},
    ]
    receive = create_receive_callable(messages)
    
    async def collect_chunks():
        chunks = []
        async for chunk in reader.stream(receive):
            chunks.append(chunk)
        return chunks
    
    exception_raised = False
    
    try:
        asyncio.get_event_loop().run_until_complete(collect_chunks())
    except ClientDisconnected:
        exception_raised = True
    
    if not exception_raised:
        errmsg = "Expected ClientDisconnected exception"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for BodyReader - Streaming Produces Same Content as Buffered
# =============================================================================

def test_stream_produces_same_content_as_read():
    """
        Test that streaming produces the same total content as buffered reading.
    """
    body_chunks = [b"Hello, ", b"World!", b" How ", b"are ", b"you?"]
    
    # Create messages for buffered read
    messages_for_read = []
    for i, chunk in enumerate(body_chunks):
        is_last = (i == len(body_chunks) - 1)
        messages_for_read.append({
            "type": MESSAGE_HTTP_REQUEST,
            "body": chunk,
            "more_body": not is_last
        })
    
    # Create messages for streaming (same content)
    messages_for_stream = []
    for i, chunk in enumerate(body_chunks):
        is_last = (i == len(body_chunks) - 1)
        messages_for_stream.append({
            "type": MESSAGE_HTTP_REQUEST,
            "body": chunk,
            "more_body": not is_last
        })
    
    reader = BodyReader()
    
    # Read using buffered method
    receive_read = create_receive_callable(messages_for_read)
    buffered_result = asyncio.get_event_loop().run_until_complete(
        reader.read(receive_read)
    )
    
    # Read using streaming method
    receive_stream = create_receive_callable(messages_for_stream)
    
    async def collect_and_join():
        chunks = []
        async for chunk in reader.stream(receive_stream):
            chunks.append(chunk)
        return b"".join(chunks)
    
    streamed_result = asyncio.get_event_loop().run_until_complete(collect_and_join())
    
    if buffered_result != streamed_result:
        errmsg = f"Buffered result '{buffered_result}' != streamed result '{streamed_result}'"
        raise AssertionError(errmsg)
    
    return



# =============================================================================
# Unit Tests for BodyReader - read_form() Method
# =============================================================================

def test_read_form_parses_simple_form_data():
    """
        Test that read_form() parses simple form-encoded data.
    """
    reader = BodyReader()
    body_content = b"name=John&age=30"
    messages = [
        {"type": MESSAGE_HTTP_REQUEST, "body": body_content, "more_body": False}
    ]
    receive = create_receive_callable(messages)
    
    result = asyncio.get_event_loop().run_until_complete(
        reader.read_form(receive, "application/x-www-form-urlencoded")
    )
    
    if result.get("name") != "John":
        errmsg = f"Expected name='John', got name='{result.get('name')}'"
        raise AssertionError(errmsg)
    
    if result.get("age") != "30":
        errmsg = f"Expected age='30', got age='{result.get('age')}'"
        raise AssertionError(errmsg)
    
    return


def test_read_form_handles_empty_values():
    """
        Test that read_form() handles empty form values.
    """
    reader = BodyReader()
    body_content = b"name=&age=30"
    messages = [
        {"type": MESSAGE_HTTP_REQUEST, "body": body_content, "more_body": False}
    ]
    receive = create_receive_callable(messages)
    
    result = asyncio.get_event_loop().run_until_complete(
        reader.read_form(receive, "application/x-www-form-urlencoded")
    )
    
    if result.get("name") != "":
        errmsg = f"Expected name='', got name='{result.get('name')}'"
        raise AssertionError(errmsg)
    
    return


def test_read_form_handles_url_encoded_values():
    """
        Test that read_form() handles URL-encoded values.
    """
    reader = BodyReader()
    body_content = b"message=Hello%20World&special=%26%3D%3F"
    messages = [
        {"type": MESSAGE_HTTP_REQUEST, "body": body_content, "more_body": False}
    ]
    receive = create_receive_callable(messages)
    
    result = asyncio.get_event_loop().run_until_complete(
        reader.read_form(receive, "application/x-www-form-urlencoded")
    )
    
    if result.get("message") != "Hello World":
        errmsg = f"Expected message='Hello World', got message='{result.get('message')}'"
        raise AssertionError(errmsg)
    
    if result.get("special") != "&=?":
        errmsg = f"Expected special='&=?', got special='{result.get('special')}'"
        raise AssertionError(errmsg)
    
    return


def test_read_form_returns_empty_dict_for_empty_body():
    """
        Test that read_form() returns empty dict for empty body.
    """
    reader = BodyReader()
    messages = [
        {"type": MESSAGE_HTTP_REQUEST, "body": b"", "more_body": False}
    ]
    receive = create_receive_callable(messages)
    
    result = asyncio.get_event_loop().run_until_complete(
        reader.read_form(receive, "application/x-www-form-urlencoded")
    )
    
    if len(result) != 0:
        errmsg = f"Expected empty dict, got {len(result)} items"
        raise AssertionError(errmsg)
    
    return


def test_read_form_raises_on_invalid_utf8():
    """
        Test that read_form() raises BadRequestBody on invalid UTF-8.
    """
    from automojo.webworks.asgi.exceptions import BadRequestBody
    
    reader = BodyReader()
    # Invalid UTF-8 sequence
    body_content = b"name=\xff\xfe"
    messages = [
        {"type": MESSAGE_HTTP_REQUEST, "body": body_content, "more_body": False}
    ]
    receive = create_receive_callable(messages)
    
    exception_raised = False
    
    try:
        asyncio.get_event_loop().run_until_complete(
            reader.read_form(receive, "application/x-www-form-urlencoded")
        )
    except BadRequestBody:
        exception_raised = True
    
    if not exception_raised:
        errmsg = "Expected BadRequestBody exception"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for BodyReader - read_json() Method
# =============================================================================

def test_read_json_parses_simple_object():
    """
        Test that read_json() parses simple JSON object.
    """
    reader = BodyReader()
    body_content = b'{"name": "John", "age": 30}'
    messages = [
        {"type": MESSAGE_HTTP_REQUEST, "body": body_content, "more_body": False}
    ]
    receive = create_receive_callable(messages)
    
    result = asyncio.get_event_loop().run_until_complete(reader.read_json(receive))
    
    if result.get("name") != "John":
        errmsg = f"Expected name='John', got name='{result.get('name')}'"
        raise AssertionError(errmsg)
    
    if result.get("age") != 30:
        errmsg = f"Expected age=30, got age={result.get('age')}"
        raise AssertionError(errmsg)
    
    return


def test_read_json_parses_array():
    """
        Test that read_json() parses JSON array.
    """
    reader = BodyReader()
    body_content = b'[1, 2, 3, 4, 5]'
    messages = [
        {"type": MESSAGE_HTTP_REQUEST, "body": body_content, "more_body": False}
    ]
    receive = create_receive_callable(messages)
    
    result = asyncio.get_event_loop().run_until_complete(reader.read_json(receive))
    
    expected = [1, 2, 3, 4, 5]
    if result != expected:
        errmsg = f"Expected {expected}, got {result}"
        raise AssertionError(errmsg)
    
    return


def test_read_json_parses_nested_object():
    """
        Test that read_json() parses nested JSON object.
    """
    reader = BodyReader()
    body_content = b'{"user": {"name": "John", "address": {"city": "NYC"}}}'
    messages = [
        {"type": MESSAGE_HTTP_REQUEST, "body": body_content, "more_body": False}
    ]
    receive = create_receive_callable(messages)
    
    result = asyncio.get_event_loop().run_until_complete(reader.read_json(receive))
    
    if result.get("user", {}).get("name") != "John":
        errmsg = f"Expected user.name='John', got {result}"
        raise AssertionError(errmsg)
    
    if result.get("user", {}).get("address", {}).get("city") != "NYC":
        errmsg = f"Expected user.address.city='NYC', got {result}"
        raise AssertionError(errmsg)
    
    return


def test_read_json_parses_primitive_values():
    """
        Test that read_json() parses primitive JSON values.
    """
    reader = BodyReader()
    
    # Test string
    messages = [{"type": MESSAGE_HTTP_REQUEST, "body": b'"hello"', "more_body": False}]
    receive = create_receive_callable(messages)
    result = asyncio.get_event_loop().run_until_complete(reader.read_json(receive))
    if result != "hello":
        errmsg = f"Expected 'hello', got {result}"
        raise AssertionError(errmsg)
    
    # Test number
    messages = [{"type": MESSAGE_HTTP_REQUEST, "body": b'42', "more_body": False}]
    receive = create_receive_callable(messages)
    result = asyncio.get_event_loop().run_until_complete(reader.read_json(receive))
    if result != 42:
        errmsg = f"Expected 42, got {result}"
        raise AssertionError(errmsg)
    
    # Test boolean
    messages = [{"type": MESSAGE_HTTP_REQUEST, "body": b'true', "more_body": False}]
    receive = create_receive_callable(messages)
    result = asyncio.get_event_loop().run_until_complete(reader.read_json(receive))
    if result is not True:
        errmsg = f"Expected True, got {result}"
        raise AssertionError(errmsg)
    
    # Test null
    messages = [{"type": MESSAGE_HTTP_REQUEST, "body": b'null', "more_body": False}]
    receive = create_receive_callable(messages)
    result = asyncio.get_event_loop().run_until_complete(reader.read_json(receive))
    if result is not None:
        errmsg = f"Expected None, got {result}"
        raise AssertionError(errmsg)
    
    return


def test_read_json_raises_on_invalid_json():
    """
        Test that read_json() raises BadRequestBody on invalid JSON.
    """
    from automojo.webworks.asgi.exceptions import BadRequestBody
    
    reader = BodyReader()
    body_content = b'{invalid json}'
    messages = [
        {"type": MESSAGE_HTTP_REQUEST, "body": body_content, "more_body": False}
    ]
    receive = create_receive_callable(messages)
    
    exception_raised = False
    
    try:
        asyncio.get_event_loop().run_until_complete(reader.read_json(receive))
    except BadRequestBody:
        exception_raised = True
    
    if not exception_raised:
        errmsg = "Expected BadRequestBody exception"
        raise AssertionError(errmsg)
    
    return


def test_read_json_raises_on_invalid_utf8():
    """
        Test that read_json() raises BadRequestBody on invalid UTF-8.
    """
    from automojo.webworks.asgi.exceptions import BadRequestBody
    
    reader = BodyReader()
    # Invalid UTF-8 sequence
    body_content = b'{"name": "\xff\xfe"}'
    messages = [
        {"type": MESSAGE_HTTP_REQUEST, "body": body_content, "more_body": False}
    ]
    receive = create_receive_callable(messages)
    
    exception_raised = False
    
    try:
        asyncio.get_event_loop().run_until_complete(reader.read_json(receive))
    except BadRequestBody:
        exception_raised = True
    
    if not exception_raised:
        errmsg = "Expected BadRequestBody exception"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for BodyReader - read_multipart() Method
# =============================================================================

def test_read_multipart_parses_simple_form_field():
    """
        Test that read_multipart() parses simple form field.
    """
    reader = BodyReader()
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    body_content = (
        b"------WebKitFormBoundary7MA4YWxkTrZu0gW\r\n"
        b'Content-Disposition: form-data; name="username"\r\n'
        b"\r\n"
        b"john_doe\r\n"
        b"------WebKitFormBoundary7MA4YWxkTrZu0gW--\r\n"
    )
    messages = [
        {"type": MESSAGE_HTTP_REQUEST, "body": body_content, "more_body": False}
    ]
    receive = create_receive_callable(messages)
    content_type = f"multipart/form-data; boundary={boundary}"
    
    form_fields, uploaded_files = asyncio.get_event_loop().run_until_complete(
        reader.read_multipart(receive, content_type)
    )
    
    if form_fields.get("username") != "john_doe":
        errmsg = f"Expected username='john_doe', got username='{form_fields.get('username')}'"
        raise AssertionError(errmsg)
    
    if len(uploaded_files) != 0:
        errmsg = f"Expected no uploaded files, got {len(uploaded_files)}"
        raise AssertionError(errmsg)
    
    return


def test_read_multipart_parses_multiple_form_fields():
    """
        Test that read_multipart() parses multiple form fields.
    """
    reader = BodyReader()
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    body_content = (
        b"------WebKitFormBoundary7MA4YWxkTrZu0gW\r\n"
        b'Content-Disposition: form-data; name="username"\r\n'
        b"\r\n"
        b"john_doe\r\n"
        b"------WebKitFormBoundary7MA4YWxkTrZu0gW\r\n"
        b'Content-Disposition: form-data; name="email"\r\n'
        b"\r\n"
        b"john@example.com\r\n"
        b"------WebKitFormBoundary7MA4YWxkTrZu0gW--\r\n"
    )
    messages = [
        {"type": MESSAGE_HTTP_REQUEST, "body": body_content, "more_body": False}
    ]
    receive = create_receive_callable(messages)
    content_type = f"multipart/form-data; boundary={boundary}"
    
    form_fields, uploaded_files = asyncio.get_event_loop().run_until_complete(
        reader.read_multipart(receive, content_type)
    )
    
    if form_fields.get("username") != "john_doe":
        errmsg = f"Expected username='john_doe', got username='{form_fields.get('username')}'"
        raise AssertionError(errmsg)
    
    if form_fields.get("email") != "john@example.com":
        errmsg = f"Expected email='john@example.com', got email='{form_fields.get('email')}'"
        raise AssertionError(errmsg)
    
    return


def test_read_multipart_parses_file_upload():
    """
        Test that read_multipart() parses file upload.
    """
    from automojo.webworks.asgi.bodyreader import UploadedFile
    
    reader = BodyReader()
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    file_content = b"Hello, this is file content!"
    body_content = (
        b"------WebKitFormBoundary7MA4YWxkTrZu0gW\r\n"
        b'Content-Disposition: form-data; name="file"; filename="test.txt"\r\n'
        b"Content-Type: text/plain\r\n"
        b"\r\n"
        + file_content +
        b"\r\n"
        b"------WebKitFormBoundary7MA4YWxkTrZu0gW--\r\n"
    )
    messages = [
        {"type": MESSAGE_HTTP_REQUEST, "body": body_content, "more_body": False}
    ]
    receive = create_receive_callable(messages)
    content_type = f"multipart/form-data; boundary={boundary}"
    
    form_fields, uploaded_files = asyncio.get_event_loop().run_until_complete(
        reader.read_multipart(receive, content_type)
    )
    
    if len(uploaded_files) != 1:
        errmsg = f"Expected 1 uploaded file, got {len(uploaded_files)}"
        raise AssertionError(errmsg)
    
    uploaded_file = uploaded_files.get("file")
    if uploaded_file is None:
        errmsg = "Expected uploaded file with name 'file'"
        raise AssertionError(errmsg)
    
    if uploaded_file.filename != "test.txt":
        errmsg = f"Expected filename='test.txt', got filename='{uploaded_file.filename}'"
        raise AssertionError(errmsg)
    
    if uploaded_file.content_type != "text/plain":
        errmsg = f"Expected content_type='text/plain', got content_type='{uploaded_file.content_type}'"
        raise AssertionError(errmsg)
    
    if uploaded_file.content != file_content:
        errmsg = f"Expected content='{file_content}', got content='{uploaded_file.content}'"
        raise AssertionError(errmsg)
    
    if uploaded_file.size != len(file_content):
        errmsg = f"Expected size={len(file_content)}, got size={uploaded_file.size}"
        raise AssertionError(errmsg)
    
    return


def test_read_multipart_parses_mixed_fields_and_files():
    """
        Test that read_multipart() parses mixed form fields and files.
    """
    reader = BodyReader()
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    file_content = b"File content here"
    body_content = (
        b"------WebKitFormBoundary7MA4YWxkTrZu0gW\r\n"
        b'Content-Disposition: form-data; name="description"\r\n'
        b"\r\n"
        b"My file description\r\n"
        b"------WebKitFormBoundary7MA4YWxkTrZu0gW\r\n"
        b'Content-Disposition: form-data; name="document"; filename="doc.pdf"\r\n'
        b"Content-Type: application/pdf\r\n"
        b"\r\n"
        + file_content +
        b"\r\n"
        b"------WebKitFormBoundary7MA4YWxkTrZu0gW--\r\n"
    )
    messages = [
        {"type": MESSAGE_HTTP_REQUEST, "body": body_content, "more_body": False}
    ]
    receive = create_receive_callable(messages)
    content_type = f"multipart/form-data; boundary={boundary}"
    
    form_fields, uploaded_files = asyncio.get_event_loop().run_until_complete(
        reader.read_multipart(receive, content_type)
    )
    
    if form_fields.get("description") != "My file description":
        errmsg = f"Expected description='My file description', got '{form_fields.get('description')}'"
        raise AssertionError(errmsg)
    
    if len(uploaded_files) != 1:
        errmsg = f"Expected 1 uploaded file, got {len(uploaded_files)}"
        raise AssertionError(errmsg)
    
    uploaded_file = uploaded_files.get("document")
    if uploaded_file is None:
        errmsg = "Expected uploaded file with name 'document'"
        raise AssertionError(errmsg)
    
    if uploaded_file.filename != "doc.pdf":
        errmsg = f"Expected filename='doc.pdf', got filename='{uploaded_file.filename}'"
        raise AssertionError(errmsg)
    
    return


def test_read_multipart_raises_on_missing_boundary():
    """
        Test that read_multipart() raises BadRequestBody when boundary is missing.
    """
    from automojo.webworks.asgi.exceptions import BadRequestBody
    
    reader = BodyReader()
    body_content = b"some body content"
    messages = [
        {"type": MESSAGE_HTTP_REQUEST, "body": body_content, "more_body": False}
    ]
    receive = create_receive_callable(messages)
    content_type = "multipart/form-data"  # No boundary
    
    exception_raised = False
    
    try:
        asyncio.get_event_loop().run_until_complete(
            reader.read_multipart(receive, content_type)
        )
    except BadRequestBody:
        exception_raised = True
    
    if not exception_raised:
        errmsg = "Expected BadRequestBody exception"
        raise AssertionError(errmsg)
    
    return


def test_read_multipart_handles_quoted_boundary():
    """
        Test that read_multipart() handles quoted boundary parameter.
    """
    reader = BodyReader()
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    body_content = (
        b"------WebKitFormBoundary7MA4YWxkTrZu0gW\r\n"
        b'Content-Disposition: form-data; name="field"\r\n'
        b"\r\n"
        b"value\r\n"
        b"------WebKitFormBoundary7MA4YWxkTrZu0gW--\r\n"
    )
    messages = [
        {"type": MESSAGE_HTTP_REQUEST, "body": body_content, "more_body": False}
    ]
    receive = create_receive_callable(messages)
    # Boundary with quotes
    content_type = f'multipart/form-data; boundary="{boundary}"'
    
    form_fields, uploaded_files = asyncio.get_event_loop().run_until_complete(
        reader.read_multipart(receive, content_type)
    )
    
    if form_fields.get("field") != "value":
        errmsg = f"Expected field='value', got field='{form_fields.get('field')}'"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for UploadedFile
# =============================================================================

def test_uploaded_file_read_returns_content():
    """
        Test that UploadedFile.read() returns the file content.
    """
    from automojo.webworks.asgi.bodyreader import UploadedFile
    
    content = b"Hello, World!"
    uploaded_file = UploadedFile(
        filename="test.txt",
        content_type="text/plain",
        content=content,
        size=len(content)
    )
    
    result = uploaded_file.read()
    
    if result != content:
        errmsg = f"Expected content '{content}', got '{result}'"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Property-Based Tests
# =============================================================================

import os
import random


def generate_random_body_chunks(min_chunks: int = 1, max_chunks: int = 10,
                                 min_chunk_size: int = 0, max_chunk_size: int = 256) -> list:
    """
        Generate a random list of body chunks as bytes.

        :param min_chunks: Minimum number of chunks.
        :param max_chunks: Maximum number of chunks.
        :param min_chunk_size: Minimum size of each chunk in bytes.
        :param max_chunk_size: Maximum size of each chunk in bytes.

        :returns: List of bytes chunks.
    """
    num_chunks = random.randint(min_chunks, max_chunks)
    chunks = []
    for _ in range(num_chunks):
        size = random.randint(min_chunk_size, max_chunk_size)
        chunk = os.urandom(size)
        chunks.append(chunk)
    return chunks


def build_receive_messages(chunks: list, include_empty: bool = False) -> list:
    """
        Build ASGI receive messages from a list of body chunks.

        Each chunk becomes an "http.request" message with more_body=True
        except the last which has more_body=False.

        :param chunks: List of bytes chunks.
        :param include_empty: If True, randomly insert empty chunks.

        :returns: List of ASGI message dicts.
    """
    messages = []

    for i, chunk in enumerate(chunks):
        is_last = (i == len(chunks) - 1)

        if include_empty and not is_last and random.random() < 0.3:
            # Insert an empty intermediate chunk
            messages.append({
                "type": MESSAGE_HTTP_REQUEST,
                "body": b"",
                "more_body": True
            })

        messages.append({
            "type": MESSAGE_HTTP_REQUEST,
            "body": chunk,
            "more_body": not is_last
        })

    return messages


# Feature: asgi-layer, Property 4: Request Body Streaming
# *For any* request body received via multiple "http.request" messages,
# accumulating all body chunks until more_body=False SHALL produce the
# complete request body, and streaming SHALL yield the same total content
# as buffered reading.
# **Validates: Requirements 3.1, 3.2, 3.3**

def test_property_4_buffered_read_accumulates_all_chunks():
    """
        Property 4: Buffered Read Accumulation

        For any sequence of body chunks delivered via "http.request" messages,
        read() SHALL accumulate all chunks until more_body=False and return
        the concatenation of all chunks as the complete body.

        **Validates: Requirements 3.1, 3.2**
    """
    reader = BodyReader()

    for iteration in range(100):
        chunks = generate_random_body_chunks(min_chunks=1, max_chunks=8,
                                              min_chunk_size=0, max_chunk_size=200)
        expected_body = b"".join(chunks)
        messages = build_receive_messages(chunks)
        receive = create_receive_callable(messages)

        result = asyncio.get_event_loop().run_until_complete(reader.read(receive))

        if result != expected_body:
            errmsg = (
                f"Iteration {iteration}: buffered read mismatch. "
                f"Expected {len(expected_body)} bytes, got {len(result)} bytes."
            )
            raise AssertionError(errmsg)

    return


def test_property_4_streaming_yields_same_content_as_buffered():
    """
        Property 4: Streaming Equivalence

        For any sequence of body chunks, streaming via stream() and joining
        the yielded chunks SHALL produce the same total content as buffered
        reading via read().

        **Validates: Requirements 3.1, 3.2, 3.3**
    """
    reader = BodyReader()

    for iteration in range(100):
        chunks = generate_random_body_chunks(min_chunks=1, max_chunks=8,
                                              min_chunk_size=1, max_chunk_size=200)
        messages_for_read = build_receive_messages(chunks)
        messages_for_stream = build_receive_messages(chunks)

        # Buffered read
        receive_read = create_receive_callable(messages_for_read)
        buffered_result = asyncio.get_event_loop().run_until_complete(
            reader.read(receive_read)
        )

        # Streaming read
        receive_stream = create_receive_callable(messages_for_stream)

        async def collect_stream():
            collected = []
            async for chunk in reader.stream(receive_stream):
                collected.append(chunk)
            return b"".join(collected)

        streamed_result = asyncio.get_event_loop().run_until_complete(collect_stream())

        if buffered_result != streamed_result:
            errmsg = (
                f"Iteration {iteration}: stream/read mismatch. "
                f"Buffered: {len(buffered_result)} bytes, "
                f"Streamed: {len(streamed_result)} bytes."
            )
            raise AssertionError(errmsg)

    return


def test_property_4_streaming_preserves_chunk_boundaries():
    """
        Property 4: Streaming Chunk Preservation

        For any sequence of non-empty body chunks, stream() SHALL yield
        each chunk individually without merging or splitting, preserving
        the original chunk boundaries from the receive messages.

        **Validates: Requirement 3.3**
    """
    reader = BodyReader()

    for iteration in range(100):
        chunks = generate_random_body_chunks(min_chunks=1, max_chunks=8,
                                              min_chunk_size=1, max_chunk_size=200)
        messages = build_receive_messages(chunks)
        receive = create_receive_callable(messages)

        async def collect_individual_chunks():
            collected = []
            async for chunk in reader.stream(receive):
                collected.append(chunk)
            return collected

        yielded_chunks = asyncio.get_event_loop().run_until_complete(
            collect_individual_chunks()
        )

        # Filter out empty chunks from the original since stream() skips them
        non_empty_chunks = [c for c in chunks if len(c) > 0]

        if len(yielded_chunks) != len(non_empty_chunks):
            errmsg = (
                f"Iteration {iteration}: chunk count mismatch. "
                f"Expected {len(non_empty_chunks)} non-empty chunks, "
                f"got {len(yielded_chunks)} yielded chunks."
            )
            raise AssertionError(errmsg)

        for idx, (yielded, expected) in enumerate(zip(yielded_chunks, non_empty_chunks)):
            if yielded != expected:
                errmsg = (
                    f"Iteration {iteration}: chunk {idx} mismatch. "
                    f"Expected {len(expected)} bytes, got {len(yielded)} bytes."
                )
                raise AssertionError(errmsg)

    return


def test_property_4_empty_body_consistent_across_methods():
    """
        Property 4: Empty Body Consistency

        For any request with an empty body (single message with empty body
        and more_body=False), both read() and stream() SHALL produce empty
        content.

        **Validates: Requirements 3.1, 3.2, 3.3**
    """
    reader = BodyReader()

    for iteration in range(100):
        # Randomly choose between truly empty body and body with empty chunks
        num_empty_chunks = random.randint(0, 3)
        messages = []
        for i in range(num_empty_chunks):
            messages.append({
                "type": MESSAGE_HTTP_REQUEST,
                "body": b"",
                "more_body": True
            })
        # Final message
        messages.append({
            "type": MESSAGE_HTTP_REQUEST,
            "body": b"",
            "more_body": False
        })

        # Buffered read
        receive_read = create_receive_callable(list(messages))
        buffered_result = asyncio.get_event_loop().run_until_complete(
            reader.read(receive_read)
        )

        # Streaming read
        receive_stream = create_receive_callable(list(messages))

        async def collect_stream():
            collected = []
            async for chunk in reader.stream(receive_stream):
                collected.append(chunk)
            return b"".join(collected)

        streamed_result = asyncio.get_event_loop().run_until_complete(collect_stream())

        if buffered_result != b"":
            errmsg = (
                f"Iteration {iteration}: buffered read of empty body "
                f"returned {len(buffered_result)} bytes instead of 0."
            )
            raise AssertionError(errmsg)

        if streamed_result != b"":
            errmsg = (
                f"Iteration {iteration}: streamed read of empty body "
                f"returned {len(streamed_result)} bytes instead of 0."
            )
            raise AssertionError(errmsg)

    return


# Feature: asgi-layer, Property 6: Request Body Size Enforcement
# *For any* request body exceeding the configured max_request_body_size,
# the application SHALL return HTTP 413 Request Entity Too Large without
# processing the full body.
# **Validates: Requirements 3.7, 3.8**


def test_property_6_read_rejects_body_exceeding_max_size():
    """
        Property 6: Buffered Read Size Enforcement

        For any randomly generated max_size and any request body whose total
        size exceeds that max_size, read() SHALL raise RequestEntityTooLarge
        with status_code 413.

        **Validates: Requirements 3.7, 3.8**
    """

    for iteration in range(100):
        # Generate a random max_size between 1 and 512 bytes
        max_size = random.randint(1, 512)
        reader = BodyReader(max_size=max_size)

        # Generate a body that exceeds max_size by a random amount (1 to 256 bytes)
        overshoot = random.randint(1, 256)
        total_body_size = max_size + overshoot
        body_data = os.urandom(total_body_size)

        # Split into random chunks
        chunks = []
        offset = 0
        while offset < total_body_size:
            chunk_size = random.randint(1, min(128, total_body_size - offset))
            chunks.append(body_data[offset:offset + chunk_size])
            offset += chunk_size

        messages = build_receive_messages(chunks)
        receive = create_receive_callable(messages)

        raised = False
        try:
            asyncio.get_event_loop().run_until_complete(reader.read(receive))
        except RequestEntityTooLarge as exc:
            raised = True
            if exc.status_code != 413:
                errmsg = (
                    f"Iteration {iteration}: expected status_code 413, "
                    f"got {exc.status_code}."
                )
                raise AssertionError(errmsg)
            if exc.max_size != max_size:
                errmsg = (
                    f"Iteration {iteration}: expected max_size {max_size}, "
                    f"got {exc.max_size}."
                )
                raise AssertionError(errmsg)

        if not raised:
            errmsg = (
                f"Iteration {iteration}: read() did not raise RequestEntityTooLarge "
                f"for body of {total_body_size} bytes with max_size {max_size}."
            )
            raise AssertionError(errmsg)

    return


def test_property_6_stream_rejects_body_exceeding_max_size():
    """
        Property 6: Streaming Size Enforcement

        For any randomly generated max_size and any request body whose total
        size exceeds that max_size, stream() SHALL raise RequestEntityTooLarge
        with status_code 413 during iteration.

        **Validates: Requirements 3.7, 3.8**
    """

    for iteration in range(100):
        max_size = random.randint(1, 512)
        reader = BodyReader(max_size=max_size)

        overshoot = random.randint(1, 256)
        total_body_size = max_size + overshoot
        body_data = os.urandom(total_body_size)

        # Split into random chunks
        chunks = []
        offset = 0
        while offset < total_body_size:
            chunk_size = random.randint(1, min(128, total_body_size - offset))
            chunks.append(body_data[offset:offset + chunk_size])
            offset += chunk_size

        messages = build_receive_messages(chunks)
        receive = create_receive_callable(messages)

        async def consume_stream():
            collected = []
            async for chunk in reader.stream(receive):
                collected.append(chunk)
            return b"".join(collected)

        raised = False
        try:
            asyncio.get_event_loop().run_until_complete(consume_stream())
        except RequestEntityTooLarge as exc:
            raised = True
            if exc.status_code != 413:
                errmsg = (
                    f"Iteration {iteration}: expected status_code 413, "
                    f"got {exc.status_code}."
                )
                raise AssertionError(errmsg)

        if not raised:
            errmsg = (
                f"Iteration {iteration}: stream() did not raise RequestEntityTooLarge "
                f"for body of {total_body_size} bytes with max_size {max_size}."
            )
            raise AssertionError(errmsg)

    return


def test_property_6_content_length_precheck_rejects_before_reading():
    """
        Property 6: Content-Length Pre-Check

        For any randomly generated max_size and any content_length that
        exceeds max_size, read() SHALL raise RequestEntityTooLarge before
        consuming any body chunks from receive().

        **Validates: Requirements 3.7, 3.8**
    """

    for iteration in range(100):
        max_size = random.randint(1, 512)
        reader = BodyReader(max_size=max_size)

        # Content-length exceeds max_size
        content_length = max_size + random.randint(1, 256)

        # Track whether receive was called
        receive_called = [False]

        async def receive():
            receive_called[0] = True
            return {"type": MESSAGE_HTTP_REQUEST, "body": b"", "more_body": False}

        raised = False
        try:
            asyncio.get_event_loop().run_until_complete(
                reader.read(receive, content_length=content_length)
            )
        except RequestEntityTooLarge as exc:
            raised = True
            if exc.max_size != max_size:
                errmsg = (
                    f"Iteration {iteration}: expected max_size {max_size}, "
                    f"got {exc.max_size}."
                )
                raise AssertionError(errmsg)
            if exc.actual_size != content_length:
                errmsg = (
                    f"Iteration {iteration}: expected actual_size {content_length}, "
                    f"got {exc.actual_size}."
                )
                raise AssertionError(errmsg)

        if not raised:
            errmsg = (
                f"Iteration {iteration}: read() did not raise RequestEntityTooLarge "
                f"for content_length {content_length} with max_size {max_size}."
            )
            raise AssertionError(errmsg)

        if receive_called[0]:
            errmsg = (
                f"Iteration {iteration}: receive() was called despite "
                f"content_length {content_length} exceeding max_size {max_size}. "
                f"Pre-check should reject before reading."
            )
            raise AssertionError(errmsg)

    return


def test_property_6_body_within_limit_is_accepted():
    """
        Property 6: Bodies Within Limit Accepted

        For any randomly generated max_size and any request body whose total
        size is at or below max_size, read() SHALL return the complete body
        without raising RequestEntityTooLarge.

        **Validates: Requirements 3.7, 3.8**
    """

    for iteration in range(100):
        max_size = random.randint(1, 512)
        reader = BodyReader(max_size=max_size)

        # Generate a body that fits within max_size
        body_size = random.randint(0, max_size)
        body_data = os.urandom(body_size)

        # Split into random chunks
        if body_size == 0:
            chunks = [b""]
        else:
            chunks = []
            offset = 0
            while offset < body_size:
                chunk_size = random.randint(1, min(64, body_size - offset))
                chunks.append(body_data[offset:offset + chunk_size])
                offset += chunk_size

        messages = build_receive_messages(chunks)
        receive = create_receive_callable(messages)

        try:
            result = asyncio.get_event_loop().run_until_complete(reader.read(receive))
        except RequestEntityTooLarge:
            errmsg = (
                f"Iteration {iteration}: read() raised RequestEntityTooLarge "
                f"for body of {body_size} bytes with max_size {max_size}."
            )
            raise AssertionError(errmsg)

        if result != body_data:
            errmsg = (
                f"Iteration {iteration}: body mismatch. "
                f"Expected {len(body_data)} bytes, got {len(result)} bytes."
            )
            raise AssertionError(errmsg)

    return

import json
import string
from urllib.parse import urlencode


# =============================================================================
# Property 5: Request Body Parsing Round-Trip
# =============================================================================

# Feature: asgi-layer, Property 5: Request Body Parsing Round-Trip
# *For any* valid request body in form-encoded, multipart, or JSON format,
# parsing the body asynchronously SHALL produce data that, when re-encoded
# in the same format, produces equivalent content.
# **Validates: Requirements 3.4, 3.5, 3.6**


def _generate_form_key() -> str:
    """
        Generate a random form field key using safe URL characters.

        :returns: A non-empty string suitable for use as a form field name.
    """
    length = random.randint(1, 20)
    chars = string.ascii_letters + string.digits + "_"
    return "".join(random.choice(chars) for _ in range(length))


def _generate_form_value() -> str:
    """
        Generate a random form field value using printable ASCII characters.

        :returns: A string suitable for use as a form field value.
    """
    length = random.randint(0, 50)
    chars = string.ascii_letters + string.digits + " _-.,!@#$%^&*()"
    return "".join(random.choice(chars) for _ in range(length))


def _build_form_body(fields: Dict[str, str]) -> bytes:
    """
        Encode a dict of fields as application/x-www-form-urlencoded body.

        :param fields: Dict of field names to values.

        :returns: URL-encoded body as bytes.
    """
    return urlencode(fields).encode("utf-8")


def _build_multipart_body(
    fields: Dict[str, str],
    files: Dict[str, tuple],
    boundary: str
) -> bytes:
    """
        Build a multipart/form-data body from fields and files.

        :param fields: Dict of field names to string values.
        :param files: Dict of field names to (filename, content_type, content_bytes) tuples.
        :param boundary: Multipart boundary string.

        :returns: Complete multipart body as bytes.
    """
    parts = []

    for name, value in fields.items():
        part = (
            f"--{boundary}\r\n"
            f"Content-Disposition: form-data; name=\"{name}\"\r\n"
            f"\r\n"
            f"{value}\r\n"
        )
        parts.append(part.encode("utf-8"))

    for name, (filename, content_type, content) in files.items():
        header = (
            f"--{boundary}\r\n"
            f"Content-Disposition: form-data; name=\"{name}\"; filename=\"{filename}\"\r\n"
            f"Content-Type: {content_type}\r\n"
            f"\r\n"
        )
        parts.append(header.encode("utf-8") + content + b"\r\n")

    # Closing boundary
    parts.append(f"--{boundary}--\r\n".encode("utf-8"))

    return b"".join(parts)


def _generate_json_value(depth: int = 0) -> Any:
    """
        Generate a random JSON-serializable value.

        :param depth: Current nesting depth to limit recursion.

        :returns: A JSON-serializable Python value.
    """
    if depth > 2:
        # At max depth, only produce primitives
        choice = random.randint(0, 3)
    else:
        choice = random.randint(0, 5)

    if choice == 0:
        return random.randint(-1000, 1000)
    elif choice == 1:
        return round(random.uniform(-1000.0, 1000.0), 4)
    elif choice == 2:
        length = random.randint(0, 30)
        chars = string.ascii_letters + string.digits + " _-."
        return "".join(random.choice(chars) for _ in range(length))
    elif choice == 3:
        return random.choice([True, False, None])
    elif choice == 4:
        # Generate a list
        size = random.randint(0, 4)
        return [_generate_json_value(depth + 1) for _ in range(size)]
    else:
        # Generate a dict
        size = random.randint(0, 4)
        result = {}
        for _ in range(size):
            key = _generate_form_key()
            result[key] = _generate_json_value(depth + 1)
        return result


def _create_body_receive(body: bytes):
    """
        Create a receive callable that delivers a body in a single message.

        :param body: The complete body bytes.

        :returns: Async receive callable.
    """
    messages = [
        {"type": MESSAGE_HTTP_REQUEST, "body": body, "more_body": False}
    ]
    return create_receive_callable(messages)


def test_property_5_form_encoded_round_trip():
    """
        Property 5: Form-Encoded Round-Trip

        For any dict of form fields with safe ASCII keys and values,
        URL-encoding the fields and parsing via read_form() SHALL produce
        a dict equivalent to the original fields.

        **Validates: Requirement 3.4**
    """
    reader = BodyReader()
    content_type = "application/x-www-form-urlencoded"

    for iteration in range(100):
        # Generate random form fields (1 to 6 fields)
        num_fields = random.randint(1, 6)
        original_fields: Dict[str, str] = {}
        for _ in range(num_fields):
            key = _generate_form_key()
            value = _generate_form_value()
            original_fields[key] = value

        # Encode to form body
        body = _build_form_body(original_fields)

        # Parse via read_form
        receive = _create_body_receive(body)
        parsed_fields = asyncio.get_event_loop().run_until_complete(
            reader.read_form(receive, content_type)
        )

        # Verify round-trip: parsed fields should match original
        for key, expected_value in original_fields.items():
            if key not in parsed_fields:
                errmsg = (
                    f"Iteration {iteration}: missing key '{key}' in parsed form data."
                )
                raise AssertionError(errmsg)

            if parsed_fields[key] != expected_value:
                errmsg = (
                    f"Iteration {iteration}: value mismatch for key '{key}'. "
                    f"Expected '{expected_value}', got '{parsed_fields[key]}'."
                )
                raise AssertionError(errmsg)

        # Verify no extra keys
        for key in parsed_fields:
            if key not in original_fields:
                errmsg = (
                    f"Iteration {iteration}: unexpected key '{key}' in parsed form data."
                )
                raise AssertionError(errmsg)

    return


def test_property_5_form_encoded_re_encode_equivalence():
    """
        Property 5: Form-Encoded Re-Encode Equivalence

        For any dict of form fields, encoding to URL form, parsing via
        read_form(), then re-encoding the parsed result SHALL produce
        a body that parses to the same fields.

        **Validates: Requirement 3.4**
    """
    reader = BodyReader()
    content_type = "application/x-www-form-urlencoded"

    for iteration in range(100):
        num_fields = random.randint(1, 6)
        original_fields: Dict[str, str] = {}
        for _ in range(num_fields):
            key = _generate_form_key()
            value = _generate_form_value()
            original_fields[key] = value

        # First encode and parse
        body1 = _build_form_body(original_fields)
        receive1 = _create_body_receive(body1)
        parsed1 = asyncio.get_event_loop().run_until_complete(
            reader.read_form(receive1, content_type)
        )

        # Re-encode and parse again
        body2 = _build_form_body(parsed1)
        receive2 = _create_body_receive(body2)
        parsed2 = asyncio.get_event_loop().run_until_complete(
            reader.read_form(receive2, content_type)
        )

        # Both parses should produce identical results
        if parsed1 != parsed2:
            errmsg = (
                f"Iteration {iteration}: re-encode round-trip mismatch. "
                f"First parse: {parsed1}, second parse: {parsed2}."
            )
            raise AssertionError(errmsg)

    return


def test_property_5_json_round_trip():
    """
        Property 5: JSON Round-Trip

        For any JSON-serializable value, encoding to JSON and parsing via
        read_json() SHALL produce a value equal to the original.

        **Validates: Requirement 3.6**
    """
    reader = BodyReader()

    for iteration in range(100):
        original_value = _generate_json_value()

        # Encode to JSON body
        body = json.dumps(original_value).encode("utf-8")

        # Parse via read_json
        receive = _create_body_receive(body)
        parsed_value = asyncio.get_event_loop().run_until_complete(
            reader.read_json(receive)
        )

        if parsed_value != original_value:
            errmsg = (
                f"Iteration {iteration}: JSON round-trip mismatch. "
                f"Original: {original_value!r}, parsed: {parsed_value!r}."
            )
            raise AssertionError(errmsg)

    return


def test_property_5_json_re_encode_equivalence():
    """
        Property 5: JSON Re-Encode Equivalence

        For any JSON-serializable value, encoding to JSON, parsing via
        read_json(), then re-encoding and parsing again SHALL produce
        an identical value.

        **Validates: Requirement 3.6**
    """
    reader = BodyReader()

    for iteration in range(100):
        original_value = _generate_json_value()

        # First encode and parse
        body1 = json.dumps(original_value).encode("utf-8")
        receive1 = _create_body_receive(body1)
        parsed1 = asyncio.get_event_loop().run_until_complete(
            reader.read_json(receive1)
        )

        # Re-encode and parse again
        body2 = json.dumps(parsed1).encode("utf-8")
        receive2 = _create_body_receive(body2)
        parsed2 = asyncio.get_event_loop().run_until_complete(
            reader.read_json(receive2)
        )

        if parsed1 != parsed2:
            errmsg = (
                f"Iteration {iteration}: JSON re-encode round-trip mismatch. "
                f"First parse: {parsed1!r}, second parse: {parsed2!r}."
            )
            raise AssertionError(errmsg)

    return


def test_property_5_multipart_form_fields_round_trip():
    """
        Property 5: Multipart Form Fields Round-Trip

        For any dict of form fields, building a multipart/form-data body
        and parsing via read_multipart() SHALL produce form fields
        equivalent to the originals.

        **Validates: Requirement 3.5**
    """
    reader = BodyReader()
    boundary = "----TestBoundary" + str(random.randint(100000, 999999))

    for iteration in range(100):
        # Use a unique boundary per iteration to avoid collisions
        iter_boundary = boundary + str(iteration)
        content_type = f"multipart/form-data; boundary={iter_boundary}"

        # Generate random form fields
        num_fields = random.randint(1, 5)
        original_fields: Dict[str, str] = {}
        for _ in range(num_fields):
            key = _generate_form_key()
            value = _generate_form_value()
            original_fields[key] = value

        # Build multipart body with fields only
        body = _build_multipart_body(original_fields, {}, iter_boundary)

        # Parse via read_multipart
        receive = _create_body_receive(body)
        parsed_fields, parsed_files = asyncio.get_event_loop().run_until_complete(
            reader.read_multipart(receive, content_type)
        )

        # Verify form fields match
        for key, expected_value in original_fields.items():
            if key not in parsed_fields:
                errmsg = (
                    f"Iteration {iteration}: missing field '{key}' in parsed multipart data."
                )
                raise AssertionError(errmsg)

            if parsed_fields[key] != expected_value:
                errmsg = (
                    f"Iteration {iteration}: field value mismatch for '{key}'. "
                    f"Expected '{expected_value}', got '{parsed_fields[key]}'."
                )
                raise AssertionError(errmsg)

        # Verify no extra fields
        for key in parsed_fields:
            if key not in original_fields:
                errmsg = (
                    f"Iteration {iteration}: unexpected field '{key}' in parsed multipart data."
                )
                raise AssertionError(errmsg)

        # Verify no files were parsed
        if len(parsed_files) != 0:
            errmsg = (
                f"Iteration {iteration}: expected 0 files, got {len(parsed_files)}."
            )
            raise AssertionError(errmsg)

    return


def test_property_5_multipart_file_upload_round_trip():
    """
        Property 5: Multipart File Upload Round-Trip

        For any set of file uploads with random binary content, building
        a multipart/form-data body and parsing via read_multipart() SHALL
        produce UploadedFile objects with content, filename, and content_type
        matching the originals.

        **Validates: Requirement 3.5**
    """
    reader = BodyReader()
    boundary = "----FileBoundary" + str(random.randint(100000, 999999))

    for iteration in range(100):
        iter_boundary = boundary + str(iteration)
        content_type = f"multipart/form-data; boundary={iter_boundary}"

        # Generate random file uploads (1 to 3 files)
        num_files = random.randint(1, 3)
        original_files: Dict[str, tuple] = {}
        for _ in range(num_files):
            field_name = _generate_form_key()
            filename = _generate_form_key() + ".bin"
            file_content = os.urandom(random.randint(1, 200))
            file_ct = "application/octet-stream"
            original_files[field_name] = (filename, file_ct, file_content)

        # Build multipart body with files only
        body = _build_multipart_body({}, original_files, iter_boundary)

        # Parse via read_multipart
        receive = _create_body_receive(body)
        parsed_fields, parsed_files = asyncio.get_event_loop().run_until_complete(
            reader.read_multipart(receive, content_type)
        )

        # Verify no form fields
        if len(parsed_fields) != 0:
            errmsg = (
                f"Iteration {iteration}: expected 0 form fields, got {len(parsed_fields)}."
            )
            raise AssertionError(errmsg)

        # Verify file uploads match
        for field_name, (orig_filename, orig_ct, orig_content) in original_files.items():
            if field_name not in parsed_files:
                errmsg = (
                    f"Iteration {iteration}: missing file field '{field_name}' in parsed data."
                )
                raise AssertionError(errmsg)

            uploaded = parsed_files[field_name]

            if uploaded.filename != orig_filename:
                errmsg = (
                    f"Iteration {iteration}: filename mismatch for '{field_name}'. "
                    f"Expected '{orig_filename}', got '{uploaded.filename}'."
                )
                raise AssertionError(errmsg)

            if uploaded.content_type != orig_ct:
                errmsg = (
                    f"Iteration {iteration}: content_type mismatch for '{field_name}'. "
                    f"Expected '{orig_ct}', got '{uploaded.content_type}'."
                )
                raise AssertionError(errmsg)

            if uploaded.content != orig_content:
                errmsg = (
                    f"Iteration {iteration}: content mismatch for '{field_name}'. "
                    f"Expected {len(orig_content)} bytes, got {len(uploaded.content)} bytes."
                )
                raise AssertionError(errmsg)

            if uploaded.size != len(orig_content):
                errmsg = (
                    f"Iteration {iteration}: size mismatch for '{field_name}'. "
                    f"Expected {len(orig_content)}, got {uploaded.size}."
                )
                raise AssertionError(errmsg)

    return


def test_property_5_multipart_mixed_fields_and_files_round_trip():
    """
        Property 5: Multipart Mixed Content Round-Trip

        For any combination of form fields and file uploads, building
        a multipart/form-data body and parsing via read_multipart() SHALL
        correctly separate and preserve both field values and file content.

        **Validates: Requirement 3.5**
    """
    reader = BodyReader()
    boundary = "----MixedBoundary" + str(random.randint(100000, 999999))

    for iteration in range(100):
        iter_boundary = boundary + str(iteration)
        content_type = f"multipart/form-data; boundary={iter_boundary}"

        # Generate random form fields
        num_fields = random.randint(1, 3)
        original_fields: Dict[str, str] = {}
        for _ in range(num_fields):
            key = _generate_form_key()
            value = _generate_form_value()
            original_fields[key] = value

        # Generate random file uploads ensuring no key collision with fields
        num_files = random.randint(1, 2)
        original_files: Dict[str, tuple] = {}
        for _ in range(num_files):
            field_name = "file_" + _generate_form_key()
            filename = _generate_form_key() + ".dat"
            file_content = os.urandom(random.randint(1, 150))
            original_files[field_name] = (filename, "application/octet-stream", file_content)

        # Build multipart body
        body = _build_multipart_body(original_fields, original_files, iter_boundary)

        # Parse via read_multipart
        receive = _create_body_receive(body)
        parsed_fields, parsed_files = asyncio.get_event_loop().run_until_complete(
            reader.read_multipart(receive, content_type)
        )

        # Verify form fields
        if len(parsed_fields) != len(original_fields):
            errmsg = (
                f"Iteration {iteration}: field count mismatch. "
                f"Expected {len(original_fields)}, got {len(parsed_fields)}."
            )
            raise AssertionError(errmsg)

        for key, expected_value in original_fields.items():
            if key not in parsed_fields:
                errmsg = (
                    f"Iteration {iteration}: missing field '{key}'."
                )
                raise AssertionError(errmsg)
            if parsed_fields[key] != expected_value:
                errmsg = (
                    f"Iteration {iteration}: field '{key}' value mismatch. "
                    f"Expected '{expected_value}', got '{parsed_fields[key]}'."
                )
                raise AssertionError(errmsg)

        # Verify file uploads
        if len(parsed_files) != len(original_files):
            errmsg = (
                f"Iteration {iteration}: file count mismatch. "
                f"Expected {len(original_files)}, got {len(parsed_files)}."
            )
            raise AssertionError(errmsg)

        for field_name, (orig_filename, orig_ct, orig_content) in original_files.items():
            if field_name not in parsed_files:
                errmsg = (
                    f"Iteration {iteration}: missing file '{field_name}'."
                )
                raise AssertionError(errmsg)
            uploaded = parsed_files[field_name]
            if uploaded.content != orig_content:
                errmsg = (
                    f"Iteration {iteration}: file '{field_name}' content mismatch. "
                    f"Expected {len(orig_content)} bytes, got {len(uploaded.content)} bytes."
                )
                raise AssertionError(errmsg)

    return
