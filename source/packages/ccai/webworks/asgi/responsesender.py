"""
    ASGI Response Sender module.
    
    This module provides the ResponseSender class that sends HTTP responses
    via ASGI send callable, supporting both complete and streaming responses
    with proper message ordering per ASGI specification.
"""

import asyncio
from typing import Any, AsyncIterator, Awaitable, Callable, Dict, Iterator, List, Optional, Tuple

from ccai.webworks.asgi.constants import (
    MESSAGE_HTTP_RESPONSE_START,
    MESSAGE_HTTP_RESPONSE_BODY,
)


class ResponseSender:
    """
        Sends HTTP responses via ASGI send callable.
        
        This class provides methods to send HTTP responses following the
        ASGI specification, ensuring proper message ordering with the
        response start message sent before any body messages.
    """
    
    def __init__(self):
        """
            Construct a ResponseSender instance.
        """
        return
    
    async def send_start(
        self,
        send: Callable[[Dict[str, Any]], Awaitable[None]],
        status: int,
        headers: List[Tuple[bytes, bytes]]
    ) -> None:
        """
            Send response start message.
            
            Sends the http.response.start message containing the status code
            and headers. This must be called before any body messages.
            
            :param send: ASGI send callable.
            :param status: HTTP status code (e.g., 200, 404, 500).
            :param headers: List of (name, value) byte tuples for headers.
        """
        message = {
            "type": MESSAGE_HTTP_RESPONSE_START,
            "status": status,
            "headers": headers
        }
        await send(message)
        return
    
    async def send_body(
        self,
        send: Callable[[Dict[str, Any]], Awaitable[None]],
        body: bytes,
        more_body: bool = False
    ) -> None:
        """
            Send response body chunk.
            
            Sends the http.response.body message containing a body chunk.
            The more_body flag indicates whether additional chunks follow.
            
            :param send: ASGI send callable.
            :param body: Body chunk as bytes.
            :param more_body: True if more chunks follow, False for final chunk.
        """
        message = {
            "type": MESSAGE_HTTP_RESPONSE_BODY,
            "body": body,
            "more_body": more_body
        }
        await send(message)
        return

    
    def format_headers(
        self,
        headers: Dict[str, str]
    ) -> List[Tuple[bytes, bytes]]:
        """
            Convert header dict to list of byte tuples.
            
            Converts a dictionary of header names and values to the ASGI
            format of a list of (name, value) byte tuples.
            
            :param headers: Dict of header names to values.
            
            :returns: List of (name, value) byte tuples.
        """
        rtnval: List[Tuple[bytes, bytes]] = []
        
        for name, value in headers.items():
            name_bytes = name.lower().encode("utf-8")
            value_bytes = value.encode("utf-8")
            header_tuple = (name_bytes, value_bytes)
            rtnval.append(header_tuple)
        
        return rtnval
    
    async def send_streaming(
        self,
        send: Callable[[Dict[str, Any]], Awaitable[None]],
        status: int,
        headers: List[Tuple[bytes, bytes]],
        body_stream: AsyncIterator[bytes]
    ) -> None:
        """
            Send streaming response.
            
            Sends a response with a streaming body from an async generator.
            The response start is sent first. Every chunk is sent as soon as
            the stream produces it, with more_body=True, and the response is
            ended with an empty message with more_body=False. Nothing is held
            back, so a client that follows a live stream sees each chunk when
            it was produced.
            
            :param send: ASGI send callable.
            :param status: HTTP status code.
            :param headers: Response headers as list of byte tuples.
            :param body_stream: Async generator yielding body chunks.
        """
        # Send the response start message first
        await self.send_start(send, status, headers)
        
        async for chunk in body_stream:
            chunk_bytes = self._chunk_to_bytes(chunk)
            if len(chunk_bytes) > 0:
                await self.send_body(send, chunk_bytes, more_body=True)
        
        # End the response
        await self.send_body(send, b"", more_body=False)
        
        return
    
    async def send_streaming_iterator(
        self,
        send: Callable[[Dict[str, Any]], Awaitable[None]],
        status: int,
        headers: List[Tuple[bytes, bytes]],
        body_iterator: Iterator[bytes]
    ) -> None:
        """
            Send streaming response from an ordinary (blocking) iterator.
            
            Each chunk is taken from the iterator on a worker thread, so an
            iterator that reads a file or waits for data does not stop the
            event loop, and is sent as soon as it is available.
            
            :param send: ASGI send callable.
            :param status: HTTP status code.
            :param headers: Response headers as list of byte tuples.
            :param body_iterator: Iterator yielding body chunks.
        """
        loop = asyncio.get_running_loop()
        exhausted = object()
        
        def next_chunk() -> Any:
            # StopIteration cannot cross a thread boundary through a
            # future, the end of the iterator is reported with a marker.
            chunk = next(body_iterator, exhausted)
            return chunk
        
        # Send the response start message first
        await self.send_start(send, status, headers)
        
        try:
            while True:
                chunk = await loop.run_in_executor(None, next_chunk)
                if chunk is exhausted:
                    break
                
                chunk_bytes = self._chunk_to_bytes(chunk)
                if len(chunk_bytes) > 0:
                    await self.send_body(send, chunk_bytes, more_body=True)
        finally:
            # Let a generator release what it holds, also when the client
            # went away in the middle of the stream.
            close_iterator = getattr(body_iterator, "close", None)
            if callable(close_iterator):
                close_iterator()
        
        # End the response
        await self.send_body(send, b"", more_body=False)
        
        return
    
    def _chunk_to_bytes(self, chunk: Any) -> bytes:
        """
            Convert a body or a chunk of a body to bytes.
            
            :param chunk: The value to convert.
            
            :returns: The value as bytes.
            
            :raises: TypeError if the value is not text or bytes-like.
        """
        if isinstance(chunk, bytes):
            rtnval = chunk
        elif isinstance(chunk, str):
            rtnval = chunk.encode("utf-8")
        elif isinstance(chunk, (bytearray, memoryview)):
            rtnval = bytes(chunk)
        else:
            errmsg = f"Unsupported response body type: {type(chunk).__name__}"
            raise TypeError(errmsg)
        return rtnval
    
    def _get_content_stream(self, response: "Response") -> Optional[Any]:
        """
            Get the stream of a streaming response.
            
            A streaming response offers its chunks through 'iter_content'. Its
            'body' property is not used: reading it would collect the whole
            stream in memory first.
            
            :param response: Framework Response object.
            
            :returns: The iterator or async iterator of chunks, or None if the
                      response is not a streaming response.
        """
        rtnval: Optional[Any] = None
        
        iter_content = getattr(response, "iter_content", None)
        
        if callable(iter_content):
            try:
                rtnval = iter_content()
            except TypeError:
                # The response was given an async generator, which cannot
                # be iterated the ordinary way. Stream it as it is.
                content = getattr(response, "_content_iterator", None)
                if content is None or not hasattr(content, "__aiter__"):
                    raise
                rtnval = content
        
        return rtnval
    
    async def send(
        self,
        send_callable: Callable[[Dict[str, Any]], Awaitable[None]],
        response: "Response"
    ) -> None:
        """
            Send complete response.
            
            Sends a complete Response object, ensuring the start message
            is sent before the body message. This method handles both
            regular and streaming response bodies. A streaming body is sent
            chunk by chunk and is never collected in memory.
            
            :param send_callable: ASGI send callable.
            :param response: Framework Response object with status, headers, and body.
            
            :raises: TypeError if the body is of a type that cannot be sent.
                     Nothing has been sent in that case.
        """
        # Serialize headers to a list of byte tuples. The framework
        # Response carries cookies OUTSIDE the plain headers dict (a
        # SimpleCookie jar plus raw Set-Cookie lines), and each
        # cookie must go on the wire as its own Set-Cookie header —
        # a dict cannot represent that. Prefer the full accessor and
        # fall back to the dict for duck-typed response objects.
        header_items = getattr(response, "_get_all_headers", None)
        if callable(header_items):
            headers = []
            for name, value in header_items():
                headers.append(
                    (name.encode("latin-1"), str(value).encode("latin-1"))
                )
        else:
            headers = self.format_headers(response.headers)
        
        # A streaming response is recognised before its body is looked at
        stream = self._get_content_stream(response)
        
        if stream is None:
            body = response.body
            
            if isinstance(body, (bytes, str, bytearray, memoryview)):
                # Regular response - the body is complete
                body_bytes = self._chunk_to_bytes(body)
                
                await self.send_start(send_callable, response.status_code, headers)
                await self.send_body(send_callable, body_bytes, more_body=False)
                return
            
            if body is None:
                await self.send_start(send_callable, response.status_code, headers)
                await self.send_body(send_callable, b"", more_body=False)
                return
            
            # A duck-typed response may carry its stream as the body
            stream = body
        
        if hasattr(stream, "__aiter__"):
            # Streaming response - the body is an async generator
            await self.send_streaming(
                send_callable,
                response.status_code,
                headers,
                stream
            )
        elif hasattr(stream, "__next__") or isinstance(stream, (list, tuple)):
            # Streaming response - the body is an ordinary iterator of chunks
            await self.send_streaming_iterator(
                send_callable,
                response.status_code,
                headers,
                iter(stream)
            )
        else:
            # Sending an empty body here would turn a programming error
            # into a response that looks fine.
            errmsg = f"Unsupported response body type: {type(stream).__name__}"
            raise TypeError(errmsg)
        
        return


# Type hint for Response to avoid circular imports
# The actual Response class will be imported at runtime
class Response:
    """
        Type stub for Response class.
        
        This is a placeholder for type hints. The actual Response class
        is defined in the framework core.
    """
    
    status_code: int
    headers: Dict[str, str]
    body: Any
