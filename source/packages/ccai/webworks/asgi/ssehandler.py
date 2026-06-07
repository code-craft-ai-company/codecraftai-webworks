"""
    ASGI Server-Sent Events (SSE) Handler module.
    
    This module provides the SSEHandler class that handles Server-Sent Events
    streaming over HTTP, supporting event formatting, connection keep-alive,
    and graceful error handling per ASGI specification.
"""

import logging
from dataclasses import dataclass
from typing import Any, AsyncGenerator, Awaitable, Callable, Dict, List, Optional, Tuple

from ccai.webworks.asgi.constants import (
    MESSAGE_HTTP_RESPONSE_START,
    MESSAGE_HTTP_RESPONSE_BODY,
    MESSAGE_HTTP_DISCONNECT,
)


# Type aliases for clarity
SendCallable = Callable[[Dict[str, Any]], Awaitable[None]]
ReceiveCallable = Callable[[], Awaitable[Dict[str, Any]]]


@dataclass
class SSEEvent:
    """
        Represents a Server-Sent Event.
        
        An SSE event consists of data and optional fields for event name,
        event ID, and retry interval.
    """
    
    data: str
    event: Optional[str] = None
    id: Optional[str] = None
    retry: Optional[int] = None
    
    def format(self) -> str:
        """
            Format event as SSE string.
            
            Formats the event with proper field prefixes ("data:", "event:",
            "id:", "retry:") and double newline termination per SSE spec.
            
            :returns: Formatted SSE event string.
        """
        lines: List[str] = []
        
        # Add event name if provided
        if self.event is not None:
            lines.append(f"event: {self.event}")
        
        # Add event ID if provided
        if self.id is not None:
            lines.append(f"id: {self.id}")
        
        # Add retry interval if provided
        if self.retry is not None:
            lines.append(f"retry: {self.retry}")
        
        # Add data lines - each line of data gets its own "data:" prefix
        for line in self.data.split("\n"):
            lines.append(f"data: {line}")
        
        # Add double newline termination
        lines.append("")
        lines.append("")
        
        return "\n".join(lines)


class SSEHandler:
    """
        Handles Server-Sent Events streaming over HTTP.
        
        This class provides methods to stream SSE events to clients,
        format events according to the SSE specification, and handle
        connection keep-alive and client disconnection.
    """
    
    # SSE Content-Type header value
    SSE_CONTENT_TYPE: str = "text/event-stream"
    
    # Default SSE headers as list of byte tuples
    SSE_HEADERS: List[Tuple[bytes, bytes]] = [
        (b"content-type", b"text/event-stream"),
        (b"cache-control", b"no-cache"),
        (b"connection", b"keep-alive"),
    ]
    
    def __init__(
        self,
        logger: Optional[logging.Logger] = None,
    ):
        """
            Construct an SSEHandler.
            
            :param logger: Logger for error logging. If None, uses module logger.
        """
        if logger is None:
            self._logger = logging.getLogger(__name__)
        else:
            self._logger = logger
        
        return
    
    @property
    def logger(self) -> logging.Logger:
        """
            Get the logger instance.
            
            :returns: Logger instance.
        """
        return self._logger

    def format_event(self, event: SSEEvent) -> bytes:
        """
            Format SSE event as bytes.
            
            Formats the event with proper field prefixes and double newline
            termination, then encodes to UTF-8 bytes.
            
            :param event: SSE event to format.
            
            :returns: Formatted event bytes.
        """
        formatted_str = event.format()
        formatted_bytes = formatted_str.encode("utf-8")
        
        return formatted_bytes
    
    def format_event_fields(
        self,
        data: str,
        event: Optional[str] = None,
        id: Optional[str] = None,
        retry: Optional[int] = None,
    ) -> bytes:
        """
            Format SSE event fields as bytes.
            
            Creates an SSEEvent from the provided fields and formats it.
            
            :param data: Event data.
            :param event: Optional event name.
            :param id: Optional event ID.
            :param retry: Optional retry interval in milliseconds.
            
            :returns: Formatted event bytes.
        """
        sse_event = SSEEvent(
            data=data,
            event=event,
            id=id,
            retry=retry,
        )
        
        return self.format_event(sse_event)
    
    def get_sse_headers(
        self,
        additional_headers: Optional[List[Tuple[bytes, bytes]]] = None,
    ) -> List[Tuple[bytes, bytes]]:
        """
            Get SSE headers with optional additional headers.
            
            Returns the standard SSE headers (Content-Type, Cache-Control,
            Connection) merged with any additional headers provided.
            
            :param additional_headers: Optional additional headers to include.
            
            :returns: List of (name, value) byte tuples.
        """
        headers = list(self.SSE_HEADERS)
        
        if additional_headers is not None:
            headers.extend(additional_headers)
        
        return headers
    
    async def stream(
        self,
        send: SendCallable,
        event_source: AsyncGenerator[SSEEvent, None],
        headers: Optional[List[Tuple[bytes, bytes]]] = None,
    ) -> None:
        """
            Stream SSE events to client.
            
            Sends the response start with SSE headers, then streams events
            from the async generator until it is exhausted or an error occurs.
            
            :param send: ASGI send callable.
            :param event_source: Async generator yielding SSE events.
            :param headers: Optional additional headers.
        """
        # Get SSE headers with any additional headers
        response_headers = self.get_sse_headers(headers)
        
        # Send response start with 200 OK and SSE headers
        start_message = {
            "type": MESSAGE_HTTP_RESPONSE_START,
            "status": 200,
            "headers": response_headers,
        }
        await send(start_message)
        
        # Stream events from the generator
        try:
            async for event in event_source:
                # Format the event as bytes
                event_bytes = self.format_event(event)
                
                # Send the event with more_body=True to keep connection open
                body_message = {
                    "type": MESSAGE_HTTP_RESPONSE_BODY,
                    "body": event_bytes,
                    "more_body": True,
                }
                await send(body_message)
        
        except Exception as exc:
            # Log the error
            self._logger.error(
                f"Error during SSE streaming: {type(exc).__name__}: {exc}"
            )
            # Re-raise to allow caller to handle
            raise
        
        finally:
            # Send final empty body with more_body=False to close stream
            final_message = {
                "type": MESSAGE_HTTP_RESPONSE_BODY,
                "body": b"",
                "more_body": False,
            }
            
            try:
                await send(final_message)
            except Exception as send_exc:
                self._logger.debug(
                    "SSE: final-body send failed (connection likely closed): %s",
                    send_exc,
                )
        
        return

    async def send_event(
        self,
        send: SendCallable,
        data: str,
        event: Optional[str] = None,
        id: Optional[str] = None,
        retry: Optional[int] = None,
    ) -> None:
        """
            Send single SSE event.
            
            Formats and sends a single SSE event. This method assumes the
            response start has already been sent.
            
            :param send: ASGI send callable.
            :param data: Event data.
            :param event: Optional event name.
            :param id: Optional event ID.
            :param retry: Optional retry interval in milliseconds.
        """
        # Format the event
        event_bytes = self.format_event_fields(
            data=data,
            event=event,
            id=id,
            retry=retry,
        )
        
        # Send the event with more_body=True to keep connection open
        body_message = {
            "type": MESSAGE_HTTP_RESPONSE_BODY,
            "body": event_bytes,
            "more_body": True,
        }
        await send(body_message)
        
        return
    
    async def stream_with_receive(
        self,
        send: SendCallable,
        receive: ReceiveCallable,
        event_source: AsyncGenerator[SSEEvent, None],
        headers: Optional[List[Tuple[bytes, bytes]]] = None,
    ) -> None:
        """
            Stream SSE events with client disconnection detection.
            
            Streams events from the async generator while monitoring for
            client disconnection via the receive callable. When the client
            disconnects, the stream is closed gracefully.
            
            :param send: ASGI send callable.
            :param receive: ASGI receive callable for disconnect detection.
            :param event_source: Async generator yielding SSE events.
            :param headers: Optional additional headers.
        """
        import asyncio
        
        # Get SSE headers with any additional headers
        response_headers = self.get_sse_headers(headers)
        
        # Send response start with 200 OK and SSE headers
        start_message = {
            "type": MESSAGE_HTTP_RESPONSE_START,
            "status": 200,
            "headers": response_headers,
        }
        await send(start_message)
        
        # Flag to track if client disconnected
        client_disconnected = False
        
        async def check_disconnect() -> None:
            """Monitor for client disconnection."""
            nonlocal client_disconnected
            
            try:
                message = await receive()
                if message.get("type") == MESSAGE_HTTP_DISCONNECT:
                    client_disconnected = True
            except Exception as recv_exc:
                # Receive errors here are usually "client gone" — log
                # at debug so a sustained surge of disconnect-detect
                # failures is still recoverable from the journal.
                self._logger.debug(
                    "SSE: receive() raised during disconnect monitoring: %s",
                    recv_exc,
                )
                client_disconnected = True
            
            return
        
        # Start disconnect monitoring task
        disconnect_task = asyncio.create_task(check_disconnect())
        
        try:
            async for event in event_source:
                # Check if client disconnected
                if client_disconnected:
                    self._logger.debug("Client disconnected, stopping SSE stream")
                    break
                
                # Format the event as bytes
                event_bytes = self.format_event(event)
                
                # Send the event with more_body=True to keep connection open
                body_message = {
                    "type": MESSAGE_HTTP_RESPONSE_BODY,
                    "body": event_bytes,
                    "more_body": True,
                }
                
                try:
                    await send(body_message)
                except Exception as send_exc:
                    # Client likely disconnected
                    self._logger.debug(
                        f"Send failed, client likely disconnected: {send_exc}"
                    )
                    break
        
        except Exception as exc:
            # Log the error
            self._logger.error(
                f"Error during SSE streaming: {type(exc).__name__}: {exc}"
            )
            raise
        
        finally:
            # Cancel disconnect monitoring task
            if not disconnect_task.done():
                disconnect_task.cancel()
                try:
                    await disconnect_task
                except asyncio.CancelledError:
                    pass
            
            # Send final empty body with more_body=False to close stream
            if not client_disconnected:
                final_message = {
                    "type": MESSAGE_HTTP_RESPONSE_BODY,
                    "body": b"",
                    "more_body": False,
                }
                
                try:
                    await send(final_message)
                except Exception:
                    # Connection may already be closed
                    pass
        
        return
    
    async def close_stream(
        self,
        send: SendCallable,
    ) -> None:
        """
            Close an SSE stream gracefully.
            
            Sends the final body message with more_body=False to signal
            the end of the stream.
            
            :param send: ASGI send callable.
        """
        final_message = {
            "type": MESSAGE_HTTP_RESPONSE_BODY,
            "body": b"",
            "more_body": False,
        }
        
        try:
            await send(final_message)
        except Exception:
            # Connection may already be closed
            pass
        
        return
