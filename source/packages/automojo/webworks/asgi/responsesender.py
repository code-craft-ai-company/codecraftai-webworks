"""
    ASGI Response Sender module.
    
    This module provides the ResponseSender class that sends HTTP responses
    via ASGI send callable, supporting both complete and streaming responses
    with proper message ordering per ASGI specification.
"""

from typing import Any, AsyncGenerator, Awaitable, Callable, Dict, List, Optional, Tuple

from automojo.webworks.asgi.constants import (
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
        body_stream: AsyncGenerator[bytes, None]
    ) -> None:
        """
            Send streaming response.
            
            Sends a response with a streaming body from an async generator.
            The response start is sent first, then body chunks are sent
            with more_body=True for intermediate chunks and more_body=False
            for the final chunk.
            
            :param send: ASGI send callable.
            :param status: HTTP status code.
            :param headers: Response headers as list of byte tuples.
            :param body_stream: Async generator yielding body chunks.
        """
        # Send the response start message first
        await self.send_start(send, status, headers)
        
        # Buffer to hold the previous chunk so we know when we're at the last one
        previous_chunk: Optional[bytes] = None
        
        async for chunk in body_stream:
            # If we have a previous chunk, send it with more_body=True
            if previous_chunk is not None:
                await self.send_body(send, previous_chunk, more_body=True)
            
            previous_chunk = chunk
        
        # Send the final chunk with more_body=False
        if previous_chunk is not None:
            await self.send_body(send, previous_chunk, more_body=False)
        else:
            # Empty stream - send empty body with more_body=False
            await self.send_body(send, b"", more_body=False)
        
        return
    
    async def send(
        self,
        send_callable: Callable[[Dict[str, Any]], Awaitable[None]],
        response: "Response"
    ) -> None:
        """
            Send complete response.
            
            Sends a complete Response object, ensuring the start message
            is sent before the body message. This method handles both
            regular and streaming response bodies.
            
            :param send_callable: ASGI send callable.
            :param response: Framework Response object with status, headers, and body.
        """
        # Format headers from dict to list of byte tuples
        headers = self.format_headers(response.headers)
        
        # Check if the response has a streaming body
        body = response.body
        
        if hasattr(body, "__aiter__"):
            # Streaming response - body is an async generator
            await self.send_streaming(
                send_callable,
                response.status_code,
                headers,
                body
            )
        else:
            # Regular response - body is bytes
            await self.send_start(send_callable, response.status_code, headers)
            
            # Ensure body is bytes
            if isinstance(body, str):
                body_bytes = body.encode("utf-8")
            elif isinstance(body, bytes):
                body_bytes = body
            else:
                body_bytes = b""
            
            await self.send_body(send_callable, body_bytes, more_body=False)
        
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
