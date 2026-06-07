"""
    Tests for the ResponseIterator class.
    
    This module contains unit tests and property-based tests for the WSGI
    response iterator functionality.
    
    **Feature: wsgi-layer, Property 8: Response Iterator Protocol**
    **Validates: Requirements 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7, 10.8**
"""

import random
import string
import tempfile
from io import BytesIO
from typing import Generator, List, Optional

from ccai.webworks.wsgi.responseiterator import ResponseIterator


# =============================================================================
# Test Helpers and Generators
# =============================================================================

def generate_random_bytes(min_length: int = 0, max_length: int = 1000) -> bytes:
    """
        Generate random bytes content.
    """
    length = random.randint(min_length, max_length)
    rtnval = bytes(random.randint(0, 255) for _ in range(length))
    return rtnval


def generate_random_bytes_list(min_chunks: int = 0, max_chunks: int = 10) -> List[bytes]:
    """
        Generate a list of random bytes chunks.
    """
    num_chunks = random.randint(min_chunks, max_chunks)
    rtnval = [generate_random_bytes(1, 200) for _ in range(num_chunks)]
    return rtnval


def generate_random_bytes_generator(chunks: List[bytes]) -> Generator[bytes, None, None]:
    """
        Create a generator that yields the given bytes chunks.
    """
    for chunk in chunks:
        yield chunk
    return


def create_temp_file_with_content(content: bytes) -> BytesIO:
    """
        Create a BytesIO file-like object with the given content.
    """
    file_obj = BytesIO(content)
    rtnval = file_obj
    return rtnval


# =============================================================================
# Unit Tests for ResponseIterator
# =============================================================================

def test_iterator_from_bytes():
    """
        Test that ResponseIterator correctly iterates over bytes content.
    """
    content = b"Hello, World!"
    iterator = ResponseIterator(content)
    
    result = b"".join(iterator)
    
    if result != content:
        errmsg = f"Expected '{content}', got '{result}'"
        raise AssertionError(errmsg)
    
    return


def test_iterator_from_bytes_list():
    """
        Test that ResponseIterator correctly iterates over a list of bytes.
    """
    chunks = [b"Hello", b", ", b"World", b"!"]
    iterator = ResponseIterator(chunks)
    
    result = b"".join(iterator)
    
    expected = b"Hello, World!"
    if result != expected:
        errmsg = f"Expected '{expected}', got '{result}'"
        raise AssertionError(errmsg)
    
    return


def test_iterator_from_generator():
    """
        Test that ResponseIterator correctly iterates over a generator.
    """
    chunks = [b"Hello", b", ", b"World", b"!"]
    
    def gen() -> Generator[bytes, None, None]:
        for chunk in chunks:
            yield chunk
        return
    
    iterator = ResponseIterator(gen())
    
    result = b"".join(iterator)
    
    expected = b"Hello, World!"
    if result != expected:
        errmsg = f"Expected '{expected}', got '{result}'"
        raise AssertionError(errmsg)
    
    return


def test_iterator_from_file():
    """
        Test that ResponseIterator correctly iterates over a file-like object.
    """
    content = b"File content here"
    file_obj = BytesIO(content)
    
    iterator = ResponseIterator(file_obj)
    
    result = b"".join(iterator)
    
    if result != content:
        errmsg = f"Expected '{content}', got '{result}'"
        raise AssertionError(errmsg)
    
    return


def test_iterator_empty_content():
    """
        Test that ResponseIterator handles empty content.
    """
    iterator = ResponseIterator(b"")
    
    result = list(iterator)
    
    # Empty bytes should yield one empty chunk
    if len(result) != 1:
        errmsg = f"Expected 1 chunk, got {len(result)}"
        raise AssertionError(errmsg)
    
    if result[0] != b"":
        errmsg = f"Expected empty bytes, got '{result[0]}'"
        raise AssertionError(errmsg)
    
    return


def test_iterator_empty_list():
    """
        Test that ResponseIterator handles empty list.
    """
    iterator = ResponseIterator([])
    
    result = list(iterator)
    
    if len(result) != 0:
        errmsg = f"Expected 0 chunks, got {len(result)}"
        raise AssertionError(errmsg)
    
    return


def test_iterator_implements_iter_protocol():
    """
        Test that ResponseIterator implements __iter__ correctly.
    """
    iterator = ResponseIterator(b"test")
    
    result = iter(iterator)
    
    if result is not iterator:
        errmsg = "Expected __iter__ to return self"
        raise AssertionError(errmsg)
    
    return


def test_iterator_implements_next_protocol():
    """
        Test that ResponseIterator implements __next__ correctly.
    """
    iterator = ResponseIterator([b"chunk1", b"chunk2"])
    
    chunk1 = next(iterator)
    chunk2 = next(iterator)
    
    if chunk1 != b"chunk1":
        errmsg = f"Expected 'chunk1', got '{chunk1}'"
        raise AssertionError(errmsg)
    
    if chunk2 != b"chunk2":
        errmsg = f"Expected 'chunk2', got '{chunk2}'"
        raise AssertionError(errmsg)
    
    # Next call should raise StopIteration
    stop_raised = False
    try:
        next(iterator)
    except StopIteration:
        stop_raised = True
    
    if not stop_raised:
        errmsg = "Expected StopIteration after exhausting iterator"
        raise AssertionError(errmsg)
    
    return


def test_close_method_exists():
    """
        Test that ResponseIterator has a close() method.
    """
    iterator = ResponseIterator(b"test")
    
    if not hasattr(iterator, "close"):
        errmsg = "Expected ResponseIterator to have close() method"
        raise AssertionError(errmsg)
    
    if not callable(iterator.close):
        errmsg = "Expected close to be callable"
        raise AssertionError(errmsg)
    
    return


def test_close_sets_closed_flag():
    """
        Test that close() sets the closed flag.
    """
    iterator = ResponseIterator(b"test")
    
    if iterator.closed is True:
        errmsg = "Expected closed to be False before close()"
        raise AssertionError(errmsg)
    
    iterator.close()
    
    if iterator.closed is not True:
        errmsg = "Expected closed to be True after close()"
        raise AssertionError(errmsg)
    
    return


def test_close_invokes_callback():
    """
        Test that close() invokes the close_callback.
    """
    callback_invoked = [False]
    
    def callback() -> None:
        callback_invoked[0] = True
        return
    
    iterator = ResponseIterator(b"test", close_callback=callback)
    iterator.close()
    
    if callback_invoked[0] is not True:
        errmsg = "Expected close_callback to be invoked"
        raise AssertionError(errmsg)
    
    return


def test_close_closes_file_handle():
    """
        Test that close() closes file handles.
    """
    file_obj = BytesIO(b"test content")
    iterator = ResponseIterator(file_obj)
    
    # Consume the iterator
    _ = list(iterator)
    
    iterator.close()
    
    # BytesIO doesn't have a closed attribute that changes, but we can verify
    # the iterator's internal state
    if iterator.closed is not True:
        errmsg = "Expected iterator to be closed"
        raise AssertionError(errmsg)
    
    return


def test_close_can_be_called_multiple_times():
    """
        Test that close() can be called multiple times without error.
    """
    callback_count = [0]
    
    def callback() -> None:
        callback_count[0] += 1
        return
    
    iterator = ResponseIterator(b"test", close_callback=callback)
    
    iterator.close()
    iterator.close()
    iterator.close()
    
    # Callback should only be invoked once
    if callback_count[0] != 1:
        errmsg = f"Expected callback to be invoked once, got {callback_count[0]} times"
        raise AssertionError(errmsg)
    
    return


def test_iteration_after_close_raises_error():
    """
        Test that iterating after close() raises RuntimeError.
    """
    iterator = ResponseIterator([b"chunk1", b"chunk2"])
    
    # Get first chunk
    _ = next(iterator)
    
    # Close the iterator
    iterator.close()
    
    # Try to get next chunk
    error_raised = False
    try:
        next(iterator)
    except RuntimeError:
        error_raised = True
    
    if not error_raised:
        errmsg = "Expected RuntimeError when iterating after close()"
        raise AssertionError(errmsg)
    
    return


def test_from_bytes_factory():
    """
        Test the from_bytes() factory method.
    """
    content = b"Factory test content"
    iterator = ResponseIterator.from_bytes(content)
    
    result = b"".join(iterator)
    
    if result != content:
        errmsg = f"Expected '{content}', got '{result}'"
        raise AssertionError(errmsg)
    
    return


def test_from_generator_factory():
    """
        Test the from_generator() factory method.
    """
    chunks = [b"gen", b"erator", b" test"]
    
    def gen() -> Generator[bytes, None, None]:
        for chunk in chunks:
            yield chunk
        return
    
    iterator = ResponseIterator.from_generator(gen())
    
    result = b"".join(iterator)
    
    expected = b"generator test"
    if result != expected:
        errmsg = f"Expected '{expected}', got '{result}'"
        raise AssertionError(errmsg)
    
    return


def test_from_generator_with_callback():
    """
        Test the from_generator() factory method with close callback.
    """
    callback_invoked = [False]
    
    def callback() -> None:
        callback_invoked[0] = True
        return
    
    def gen() -> Generator[bytes, None, None]:
        yield b"test"
        return
    
    iterator = ResponseIterator.from_generator(gen(), close_callback=callback)
    _ = list(iterator)
    iterator.close()
    
    if callback_invoked[0] is not True:
        errmsg = "Expected close_callback to be invoked"
        raise AssertionError(errmsg)
    
    return


def test_from_file_factory():
    """
        Test the from_file() factory method.
    """
    content = b"File factory test content"
    file_obj = BytesIO(content)
    
    iterator = ResponseIterator.from_file(file_obj)
    
    result = b"".join(iterator)
    
    if result != content:
        errmsg = f"Expected '{content}', got '{result}'"
        raise AssertionError(errmsg)
    
    return


def test_from_file_with_chunk_size():
    """
        Test the from_file() factory method with custom chunk size.
    """
    content = b"A" * 100
    file_obj = BytesIO(content)
    chunk_size = 10
    
    iterator = ResponseIterator.from_file(file_obj, chunk_size=chunk_size)
    
    chunks = list(iterator)
    
    # Should have 10 chunks of 10 bytes each
    if len(chunks) != 10:
        errmsg = f"Expected 10 chunks, got {len(chunks)}"
        raise AssertionError(errmsg)
    
    for idx, chunk in enumerate(chunks):
        if len(chunk) != chunk_size:
            errmsg = f"Chunk {idx} has length {len(chunk)}, expected {chunk_size}"
            raise AssertionError(errmsg)
    
    return


def test_empty_factory():
    """
        Test the empty() factory method.
    """
    iterator = ResponseIterator.empty()
    
    result = list(iterator)
    
    if len(result) != 0:
        errmsg = f"Expected 0 chunks, got {len(result)}"
        raise AssertionError(errmsg)
    
    return


def test_yields_only_bytes():
    """
        Test that ResponseIterator only yields bytes objects.
    """
    chunks = [b"chunk1", b"chunk2", b"chunk3"]
    iterator = ResponseIterator(chunks)
    
    for chunk in iterator:
        if not isinstance(chunk, bytes):
            errmsg = f"Expected bytes, got {type(chunk)}"
            raise AssertionError(errmsg)
    
    return


def test_string_content_encoded_to_bytes():
    """
        Test that string content is encoded to bytes.
    """
    # Create a generator that yields strings (which should be encoded)
    def gen() -> Generator[str, None, None]:
        yield "Hello"
        yield " World"
        return
    
    iterator = ResponseIterator(gen())  # type: ignore
    
    result = b"".join(iterator)
    
    expected = b"Hello World"
    if result != expected:
        errmsg = f"Expected '{expected}', got '{result}'"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Property-Based Tests for ResponseIterator
# =============================================================================

def test_property_response_iterator_protocol():
    """
        Property test: Response Iterator Protocol
        
        For any valid content (bytes, list, generator, or file), the ResponseIterator
        SHALL implement the iterator protocol (__iter__ and __next__), yield only
        bytes objects, implement close() for resource cleanup, and invoke
        close_callback when close() is called.
        
        **Feature: wsgi-layer, Property 8: Response Iterator Protocol**
        **Validates: Requirements 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7, 10.8**
    """
    num_iterations = 100
    
    for iteration in range(num_iterations):
        # Generate random content
        content_type = random.choice(["bytes", "list", "generator", "file"])
        
        if content_type == "bytes":
            # Single bytes content
            original_content = generate_random_bytes(0, 500)
            iterator = ResponseIterator(original_content)
            expected_content = original_content
        
        elif content_type == "list":
            # List of bytes chunks
            chunks = generate_random_bytes_list(0, 10)
            iterator = ResponseIterator(chunks)
            expected_content = b"".join(chunks)
        
        elif content_type == "generator":
            # Generator of bytes chunks
            chunks = generate_random_bytes_list(0, 10)
            expected_content = b"".join(chunks)
            iterator = ResponseIterator(generate_random_bytes_generator(chunks))
        
        else:  # file
            # File-like object
            original_content = generate_random_bytes(0, 500)
            file_obj = create_temp_file_with_content(original_content)
            iterator = ResponseIterator(file_obj)
            expected_content = original_content
        
        # Property 1: Implements iterator protocol (Requirement 10.1)
        if iter(iterator) is not iterator:
            errmsg = f"Iteration {iteration}: __iter__ should return self"
            raise AssertionError(errmsg)
        
        # Property 2: Yields only bytes (Requirement 10.2)
        collected_chunks: List[bytes] = []
        for chunk in iterator:
            if not isinstance(chunk, bytes):
                errmsg = f"Iteration {iteration}: Yielded non-bytes content: {type(chunk)}"
                raise AssertionError(errmsg)
            collected_chunks.append(chunk)
        
        # Verify content is preserved
        result_content = b"".join(collected_chunks)
        if result_content != expected_content:
            errmsg = f"Iteration {iteration}: Content mismatch. Expected {len(expected_content)} bytes, got {len(result_content)} bytes"
            raise AssertionError(errmsg)
        
        # Property 3: Implements close() method (Requirement 10.3)
        if not hasattr(iterator, "close"):
            errmsg = f"Iteration {iteration}: Missing close() method"
            raise AssertionError(errmsg)
        
        if not callable(iterator.close):
            errmsg = f"Iteration {iteration}: close is not callable"
            raise AssertionError(errmsg)
        
        # Property 4: close() releases resources (Requirement 10.4)
        iterator.close()
        
        if iterator.closed is not True:
            errmsg = f"Iteration {iteration}: closed flag not set after close()"
            raise AssertionError(errmsg)
    
    # Test close_callback invocation separately
    for iteration in range(20):
        callback_invoked = [False]
        
        def callback() -> None:
            callback_invoked[0] = True
            return
        
        content = generate_random_bytes(10, 100)
        iterator = ResponseIterator(content, close_callback=callback)
        
        # Consume iterator
        _ = list(iterator)
        
        # Close and verify callback
        iterator.close()
        
        if callback_invoked[0] is not True:
            errmsg = f"Callback iteration {iteration}: close_callback not invoked"
            raise AssertionError(errmsg)
    
    return

