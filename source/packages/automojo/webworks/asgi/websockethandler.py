"""
    ASGI WebSocket Handler module.
    
    This module provides the WebSocketHandler class that handles WebSocket
    connections over ASGI, supporting connection lifecycle management,
    message sending/receiving, and error handling.
"""

import logging
from typing import Any, Awaitable, Callable, Dict, List, Optional, Union

from automojo.webworks.asgi.constants import (
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
from automojo.webworks.asgi.exceptions import (
    WebSocketError,
    ClientDisconnected,
)


# Module-level logger for the WebSocketConnection helper. The
# WebSocketHandler keeps its own ``self._logger`` so applications
# can route websocket errors to a dedicated handler — this module
# logger is the default fallback for the connection-level close
# path (which has no handler reference).
logger = logging.getLogger(__name__)


# Type aliases for clarity
ReceiveCallable = Callable[[], Awaitable[Dict[str, Any]]]
SendCallable = Callable[[Dict[str, Any]], Awaitable[None]]
WebSocketHandlerCallable = Callable[["WebSocketConnection"], Awaitable[None]]


class WebSocketConnection:
    """
        Represents an active WebSocket connection.
        
        This class provides methods for sending and receiving messages,
        accepting/rejecting connections, and closing the connection.
    """
    
    def __init__(
        self,
        scope: Dict[str, Any],
        receive: ReceiveCallable,
        send: SendCallable,
    ):
        """
            Construct a WebSocketConnection.
            
            :param scope: ASGI WebSocket scope dictionary.
            :param receive: ASGI receive callable.
            :param send: ASGI send callable.
        """
        self._scope = scope
        self._receive = receive
        self._send = send
        self._accepted = False
        self._closed = False
        
        return
    
    @property
    def scope(self) -> Dict[str, Any]:
        """
            Get the ASGI scope dictionary.
            
            :returns: ASGI scope dictionary.
        """
        return self._scope
    
    @property
    def path(self) -> str:
        """
            Get the WebSocket path.
            
            :returns: Request path string.
        """
        return self._scope.get("path", "/")
    
    @property
    def query_string(self) -> str:
        """
            Get the query string.
            
            :returns: Query string decoded from bytes.
        """
        query_bytes = self._scope.get("query_string", b"")
        return query_bytes.decode("utf-8")
    
    @property
    def headers(self) -> Dict[str, str]:
        """
            Get the request headers.
            
            :returns: Dict of header names to values.
        """
        headers_list = self._scope.get("headers", [])
        headers_dict: Dict[str, str] = {}
        
        for name_bytes, value_bytes in headers_list:
            name = name_bytes.decode("utf-8").lower()
            value = value_bytes.decode("utf-8")
            headers_dict[name] = value
        
        return headers_dict
    
    @property
    def subprotocols(self) -> List[str]:
        """
            Get the requested subprotocols.
            
            :returns: List of subprotocol strings.
        """
        return self._scope.get("subprotocols", [])
    
    @property
    def is_accepted(self) -> bool:
        """
            Check if the connection has been accepted.
            
            :returns: True if accepted.
        """
        return self._accepted
    
    @property
    def is_closed(self) -> bool:
        """
            Check if the connection has been closed.
            
            :returns: True if closed.
        """
        return self._closed

    async def accept(
        self,
        subprotocol: Optional[str] = None,
        headers: Optional[List[tuple]] = None,
    ) -> None:
        """
            Accept the WebSocket connection.
            
            This must be called before sending or receiving messages.
            
            :param subprotocol: Optional subprotocol to accept.
            :param headers: Optional list of (name, value) byte tuples.
            
            :raises WebSocketError: If connection already accepted or closed.
        """
        if self._accepted:
            raise WebSocketError(
                code=WS_CLOSE_INTERNAL_ERROR,
                reason="Connection already accepted",
            )
        
        if self._closed:
            raise WebSocketError(
                code=WS_CLOSE_INTERNAL_ERROR,
                reason="Connection already closed",
            )
        
        accept_message: Dict[str, Any] = {
            "type": MESSAGE_WEBSOCKET_ACCEPT,
        }
        
        if subprotocol is not None:
            accept_message["subprotocol"] = subprotocol
        
        if headers is not None:
            accept_message["headers"] = headers
        else:
            accept_message["headers"] = []
        
        await self._send(accept_message)
        self._accepted = True
        
        return
    
    async def reject(
        self,
        code: int = 403,
    ) -> None:
        """
            Reject the WebSocket connection.
            
            This closes the connection before accepting it.
            
            :param code: Close code (default 403 Forbidden).
            
            :raises WebSocketError: If connection already accepted or closed.
        """
        if self._accepted:
            raise WebSocketError(
                code=WS_CLOSE_INTERNAL_ERROR,
                reason="Cannot reject after accepting",
            )
        
        if self._closed:
            raise WebSocketError(
                code=WS_CLOSE_INTERNAL_ERROR,
                reason="Connection already closed",
            )
        
        close_message = {
            "type": MESSAGE_WEBSOCKET_CLOSE,
            "code": code,
        }
        
        await self._send(close_message)
        self._closed = True
        
        return
    
    async def send_text(self, text: str) -> None:
        """
            Send a text message.
            
            :param text: Text message to send.
            
            :raises WebSocketError: If connection not accepted or closed.
        """
        if not self._accepted:
            raise WebSocketError(
                code=WS_CLOSE_INTERNAL_ERROR,
                reason="Connection not accepted",
            )
        
        if self._closed:
            raise WebSocketError(
                code=WS_CLOSE_INTERNAL_ERROR,
                reason="Connection closed",
            )
        
        send_message = {
            "type": MESSAGE_WEBSOCKET_SEND,
            "text": text,
        }
        
        await self._send(send_message)
        
        return
    
    async def send_bytes(self, data: bytes) -> None:
        """
            Send a binary message.
            
            :param data: Binary data to send.
            
            :raises WebSocketError: If connection not accepted or closed.
        """
        if not self._accepted:
            raise WebSocketError(
                code=WS_CLOSE_INTERNAL_ERROR,
                reason="Connection not accepted",
            )
        
        if self._closed:
            raise WebSocketError(
                code=WS_CLOSE_INTERNAL_ERROR,
                reason="Connection closed",
            )
        
        send_message = {
            "type": MESSAGE_WEBSOCKET_SEND,
            "bytes": data,
        }
        
        await self._send(send_message)
        
        return

    async def receive_message(self) -> Optional[Union[str, bytes]]:
        """
            Receive the next message from the client.
            
            :returns: Text or bytes message, or None if disconnected.
            
            :raises WebSocketError: If connection not accepted.
            :raises ClientDisconnected: If client disconnects.
        """
        if not self._accepted:
            raise WebSocketError(
                code=WS_CLOSE_INTERNAL_ERROR,
                reason="Connection not accepted",
            )
        
        if self._closed:
            return None
        
        message = await self._receive()
        message_type = message.get("type", "")
        
        if message_type == MESSAGE_WEBSOCKET_DISCONNECT:
            self._closed = True
            raise ClientDisconnected("WebSocket client disconnected")
        
        if message_type == MESSAGE_WEBSOCKET_RECEIVE:
            # Check for text message
            if "text" in message:
                return message["text"]
            
            # Check for binary message
            if "bytes" in message:
                return message["bytes"]
        
        # Unknown message type or empty message
        return None
    
    async def close(
        self,
        code: int = WS_CLOSE_NORMAL,
        reason: str = "",
    ) -> None:
        """
            Close the WebSocket connection.
            
            :param code: WebSocket close code (default 1000 Normal Closure).
            :param reason: Close reason string.
        """
        if self._closed:
            return
        
        close_message: Dict[str, Any] = {
            "type": MESSAGE_WEBSOCKET_CLOSE,
            "code": code,
        }
        
        if reason:
            close_message["reason"] = reason
        
        try:
            await self._send(close_message)
        except Exception as exc:
            # Connection may already be closed — log at debug so
            # the journal carries the breadcrumb without overwhelming
            # a busy server with normal "client gone" lines.
            logger.debug(
                "WebSocketConnection.close: send raised (connection likely closed): %s",
                exc,
            )

        self._closed = True

        return


class WebSocketHandler:
    """
        Handles WebSocket connections over ASGI.
        
        This class manages the WebSocket connection lifecycle including
        connection events, message handling, and error handling.
    """
    
    def __init__(
        self,
        debug: bool = False,
        logger: Optional[logging.Logger] = None,
    ):
        """
            Construct a WebSocketHandler.
            
            :param debug: If True, include detailed error information.
            :param logger: Logger for error logging. If None, uses module logger.
        """
        self._debug = debug
        
        if logger is None:
            self._logger = logging.getLogger(__name__)
        else:
            self._logger = logger
        
        self._handler: Optional[WebSocketHandlerCallable] = None
        
        return
    
    @property
    def debug(self) -> bool:
        """
            Get the debug mode setting.
            
            :returns: True if debug mode is enabled.
        """
        return self._debug
    
    @property
    def logger(self) -> logging.Logger:
        """
            Get the logger instance.
            
            :returns: Logger instance.
        """
        return self._logger
    
    def set_handler(self, handler: WebSocketHandlerCallable) -> None:
        """
            Set the WebSocket handler.
            
            The handler is an async function that receives a WebSocketConnection
            and handles the connection lifecycle.
            
            :param handler: Async handler function.
        """
        self._handler = handler
        return

    async def handle(
        self,
        scope: Dict[str, Any],
        receive: ReceiveCallable,
        send: SendCallable,
    ) -> None:
        """
            Handle a WebSocket connection lifecycle.
            
            This method receives the "websocket.connect" event, creates a
            WebSocketConnection, and invokes the registered handler.
            
            :param scope: ASGI WebSocket scope dictionary.
            :param receive: ASGI receive callable.
            :param send: ASGI send callable.
        """
        # Wait for the connect event
        message = await receive()
        message_type = message.get("type", "")
        
        if message_type != MESSAGE_WEBSOCKET_CONNECT:
            # Unexpected message type, log and return
            self._logger.warning(
                f"Expected websocket.connect, got {message_type}"
            )
            return
        
        # Create the connection object
        connection = WebSocketConnection(scope, receive, send)
        
        # If no handler is set, reject the connection
        if self._handler is None:
            await connection.reject(code=403)
            return
        
        try:
            # Invoke the handler
            await self._handler(connection)
            
        except ClientDisconnected:
            # Client disconnected, this is expected
            pass
        
        except WebSocketError as err:
            # WebSocket error, close with the error code
            await self._handle_websocket_error(connection, err)
        
        except Exception as err:
            # Unhandled exception, close with internal error
            await self._handle_unhandled_error(connection, err, scope)
        
        finally:
            # Ensure connection is closed
            if not connection.is_closed:
                await connection.close(code=WS_CLOSE_GOING_AWAY)
        
        return
    
    async def _handle_websocket_error(
        self,
        connection: WebSocketConnection,
        err: WebSocketError,
    ) -> None:
        """
            Handle a WebSocket error.
            
            :param connection: The WebSocket connection.
            :param err: The WebSocket error.
        """
        if connection.is_closed:
            return
        
        reason = err.reason
        if self._debug and not reason:
            reason = str(err)
        
        await connection.close(code=err.code, reason=reason)
        
        return
    
    async def _handle_unhandled_error(
        self,
        connection: WebSocketConnection,
        err: Exception,
        scope: Dict[str, Any],
    ) -> None:
        """
            Handle an unhandled exception.
            
            :param connection: The WebSocket connection.
            :param err: The exception.
            :param scope: ASGI scope for logging context.
        """
        # Log the exception
        self._log_exception(err, scope)
        
        if connection.is_closed:
            return
        
        reason = "Internal Server Error"
        if self._debug:
            reason = f"{type(err).__name__}: {err}"
        
        await connection.close(code=WS_CLOSE_INTERNAL_ERROR, reason=reason)
        
        return
    
    def _log_exception(
        self,
        err: Exception,
        scope: Dict[str, Any],
    ) -> None:
        """
            Log an exception with context.
            
            :param err: The exception to log.
            :param scope: ASGI scope for context.
        """
        import traceback
        
        path = scope.get("path", "unknown")
        
        tb_lines = traceback.format_exception(type(err), err, err.__traceback__)
        tb_str = "".join(tb_lines)
        
        self._logger.error(
            f"Exception during WebSocket {path}: {type(err).__name__}: {err}\n{tb_str}"
        )
        
        return
