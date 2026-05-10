"""
    ASGI Error Handler module.
    
    This module provides the ErrorHandler class that handles exceptions during
    ASGI request processing, supporting HTTP errors, unhandled exceptions,
    debug/production formatting, and custom error handler registration.
"""

import json
import logging
import traceback
from typing import Any, Awaitable, Callable, Dict, List, Optional, Type, Union

from automojo.webworks.asgi.constants import (
    HTTP_STATUS_PHRASES,
    MESSAGE_HTTP_RESPONSE_START,
    MESSAGE_HTTP_RESPONSE_BODY,
    MESSAGE_WEBSOCKET_CLOSE,
    WS_CLOSE_INTERNAL_ERROR,
)


# Type aliases for clarity
SendCallable = Callable[[Dict[str, Any]], Awaitable[None]]
ErrorHandlerCallable = Callable[[Exception], Awaitable["ErrorResponse"]]


class ErrorResponse:
    """
        Represents an error response to be sent to the client.
        
        This class encapsulates the status code, headers, and body
        for an error response.
    """
    
    def __init__(
        self,
        status_code: int,
        body: bytes,
        headers: Optional[Dict[str, str]] = None,
    ):
        """
            Construct an ErrorResponse.
            
            :param status_code: HTTP status code.
            :param body: Response body as bytes.
            :param headers: Optional dict of header names to values.
        """
        self._status_code = status_code
        self._body = body
        
        if headers is None:
            self._headers = {
                "Content-Type": "application/json; charset=utf-8",
                "Content-Length": str(len(body)),
            }
        else:
            self._headers = headers
        
        return
    
    @property
    def status_code(self) -> int:
        """
            Get the HTTP status code.
            
            :returns: HTTP status code.
        """
        return self._status_code
    
    @property
    def body(self) -> bytes:
        """
            Get the response body.
            
            :returns: Response body as bytes.
        """
        return self._body
    
    @property
    def headers(self) -> Dict[str, str]:
        """
            Get the response headers.
            
            :returns: Dict of header names to values.
        """
        return self._headers


class HTTPException(Exception):
    """
        Base class for HTTP exceptions.
        
        HTTP exceptions have a status code and optional detail message
        that can be used to generate error responses.
    """
    
    def __init__(
        self,
        status_code: int,
        detail: Optional[str] = None,
    ):
        """
            Construct an HTTPException.
            
            :param status_code: HTTP status code.
            :param detail: Optional detail message.
        """
        self._status_code = status_code
        self._detail = detail
        
        message = HTTP_STATUS_PHRASES.get(status_code, "Unknown Error")
        if detail is not None:
            message = f"{message}: {detail}"
        
        super().__init__(message)
        return
    
    @property
    def status_code(self) -> int:
        """
            Get the HTTP status code.
            
            :returns: HTTP status code.
        """
        return self._status_code
    
    @property
    def detail(self) -> Optional[str]:
        """
            Get the detail message.
            
            :returns: Detail message or None.
        """
        return self._detail


class ErrorHandler:
    """
        Handles exceptions during ASGI request processing.
        
        This class provides methods to handle HTTP errors, unhandled exceptions,
        and WebSocket errors. It supports debug vs production error formatting
        and custom error handler registration for specific exception types.
    """
    
    def __init__(
        self,
        debug: bool = False,
        logger: Optional[logging.Logger] = None,
    ):
        """
            Construct an ErrorHandler.
            
            :param debug: If True, include stack traces in error responses.
            :param logger: Logger for error logging. If None, uses module logger.
        """
        self._debug = debug
        
        if logger is None:
            self._logger = logging.getLogger(__name__)
        else:
            self._logger = logger
        
        # Registry of custom error handlers by exception type
        self._custom_handlers: Dict[Type[Exception], ErrorHandlerCallable] = {}
        
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

    def register_handler(
        self,
        exc_type: Type[Exception],
        handler: ErrorHandlerCallable,
    ) -> None:
        """
            Register a custom handler for a specific exception type.
            
            When an exception of the registered type is raised, the custom
            handler will be called instead of the default error handling.
            
            :param exc_type: The exception type to handle.
            :param handler: Async function that takes the exception and returns
                           an ErrorResponse.
        """
        self._custom_handlers[exc_type] = handler
        return
    
    def unregister_handler(
        self,
        exc_type: Type[Exception],
    ) -> None:
        """
            Unregister a custom handler for a specific exception type.
            
            :param exc_type: The exception type to unregister.
        """
        if exc_type in self._custom_handlers:
            del self._custom_handlers[exc_type]
        
        return
    
    def get_handler(
        self,
        exc_type: Type[Exception],
    ) -> Optional[ErrorHandlerCallable]:
        """
            Get the custom handler for a specific exception type.
            
            :param exc_type: The exception type to look up.
            
            :returns: The custom handler or None if not registered.
        """
        return self._custom_handlers.get(exc_type)
    
    async def handle_http_error(
        self,
        exc: Exception,
        send: SendCallable,
        scope: Dict[str, Any],
    ) -> None:
        """
            Handle HTTP error and send error response.
            
            This method handles exceptions during HTTP request processing.
            It checks for custom handlers first, then handles HTTPException
            subclasses, and finally handles unhandled exceptions.
            
            :param exc: The exception that occurred.
            :param send: ASGI send callable.
            :param scope: ASGI scope for context.
        """
        # Check for custom handler first
        exc_type = type(exc)
        
        # Look for exact match first, then check parent classes
        handler = self._find_custom_handler(exc_type)
        
        if handler is not None:
            try:
                error_response = await handler(exc)
                await self._send_error_response(send, error_response)
                return
            except Exception as handler_exc:
                # If custom handler fails, log and fall through to default handling
                self.log_exception(handler_exc, scope)
        
        # Handle HTTPException subclasses
        if self._is_http_exception(exc):
            status_code = self._get_status_code(exc)
            detail = self._get_detail(exc)
            
            error_response = self._create_error_response(
                status_code=status_code,
                message=HTTP_STATUS_PHRASES.get(status_code, "Error"),
                exc=exc if self._debug else None,
                detail=detail,
            )
            
            await self._send_error_response(send, error_response)
            return
        
        # Handle unhandled exceptions
        self.log_exception(exc, scope)
        
        error_response = self._create_error_response(
            status_code=500,
            message="Internal Server Error",
            exc=exc if self._debug else None,
        )
        
        await self._send_error_response(send, error_response)
        return
    
    async def handle_websocket_error(
        self,
        exc: Exception,
        send: SendCallable,
        scope: Dict[str, Any],
    ) -> None:
        """
            Handle WebSocket error and close connection.
            
            This method handles exceptions during WebSocket handling by
            closing the connection with an appropriate close code.
            
            :param exc: The exception that occurred.
            :param send: ASGI send callable.
            :param scope: ASGI scope for context.
        """
        # Log the exception
        self.log_exception(exc, scope)
        
        # Determine close code based on exception type
        close_code = WS_CLOSE_INTERNAL_ERROR
        reason = "Internal Server Error"
        
        if self._debug:
            reason = f"{type(exc).__name__}: {exc}"
        
        # Send WebSocket close message
        close_message = {
            "type": MESSAGE_WEBSOCKET_CLOSE,
            "code": close_code,
            "reason": reason,
        }
        
        try:
            await send(close_message)
        except Exception as send_exc:
            # Connection may already be closed — keep the breadcrumb
            # at debug level so the journal carries the context
            # without overwhelming a busy server.
            self._logger.debug(
                "WebSocket close send failed (connection likely closed): %s",
                send_exc,
            )
        
        return
    
    def log_exception(
        self,
        exc: Exception,
        scope: Dict[str, Any],
    ) -> None:
        """
            Log exception with stack trace.
            
            :param exc: The exception to log.
            :param scope: ASGI scope for context.
        """
        # Extract context information from scope
        scope_type = scope.get("type", "unknown")
        path = scope.get("path", "unknown")
        method = scope.get("method", "")
        
        # Format the log message
        if method:
            context = f"{method} {path}"
        else:
            context = f"{scope_type} {path}"
        
        # Get the full traceback
        tb_lines = traceback.format_exception(type(exc), exc, exc.__traceback__)
        tb_str = "".join(tb_lines)
        
        # Log the exception
        self._logger.error(
            f"Exception during {context}: {type(exc).__name__}: {exc}\n{tb_str}"
        )
        
        return
    
    def format_error_body(
        self,
        status_code: int,
        message: str,
        exc: Optional[Exception] = None,
        detail: Optional[str] = None,
    ) -> bytes:
        """
            Format error response body.
            
            In production mode, returns a simple error message.
            In debug mode, includes exception type, detail, and traceback.
            
            :param status_code: HTTP status code.
            :param message: Error message.
            :param exc: Optional exception for debug mode.
            :param detail: Optional detail message.
            
            :returns: Formatted error body as bytes.
        """
        error_dict: Dict[str, Any] = {
            "error": {
                "status": status_code,
                "message": message,
            }
        }
        
        # Add detail if provided
        if detail is not None:
            error_dict["error"]["detail"] = detail
        
        # Add debug information if exception provided
        if exc is not None:
            error_dict["error"]["type"] = type(exc).__name__
            
            # Get exception detail if not already provided
            if detail is None:
                error_dict["error"]["detail"] = str(exc)
            
            # Add traceback
            tb_lines = traceback.format_exception(
                type(exc), exc, exc.__traceback__
            )
            # Clean up traceback lines
            formatted_tb = []
            for line in tb_lines:
                # Split multi-line entries and strip whitespace
                for subline in line.rstrip().split("\n"):
                    if subline.strip():
                        formatted_tb.append(subline)
            
            error_dict["error"]["traceback"] = formatted_tb
        
        # Serialize to JSON
        body_str = json.dumps(error_dict, indent=2)
        body_bytes = body_str.encode("utf-8")
        
        return body_bytes

    def _create_error_response(
        self,
        status_code: int,
        message: str,
        exc: Optional[Exception] = None,
        detail: Optional[str] = None,
    ) -> ErrorResponse:
        """
            Create an ErrorResponse object.
            
            :param status_code: HTTP status code.
            :param message: Error message.
            :param exc: Optional exception for debug mode.
            :param detail: Optional detail message.
            
            :returns: ErrorResponse object.
        """
        body = self.format_error_body(status_code, message, exc, detail)
        
        headers = {
            "Content-Type": "application/json; charset=utf-8",
            "Content-Length": str(len(body)),
        }
        
        error_response = ErrorResponse(
            status_code=status_code,
            body=body,
            headers=headers,
        )
        
        return error_response
    
    async def _send_error_response(
        self,
        send: SendCallable,
        error_response: ErrorResponse,
    ) -> None:
        """
            Send an error response via ASGI send callable.
            
            :param send: ASGI send callable.
            :param error_response: ErrorResponse to send.
        """
        # Format headers as list of byte tuples
        headers: List[tuple] = []
        for name, value in error_response.headers.items():
            name_bytes = name.lower().encode("utf-8")
            value_bytes = value.encode("utf-8")
            headers.append((name_bytes, value_bytes))
        
        # Send response start
        start_message = {
            "type": MESSAGE_HTTP_RESPONSE_START,
            "status": error_response.status_code,
            "headers": headers,
        }
        await send(start_message)
        
        # Send response body
        body_message = {
            "type": MESSAGE_HTTP_RESPONSE_BODY,
            "body": error_response.body,
            "more_body": False,
        }
        await send(body_message)
        
        return
    
    def _find_custom_handler(
        self,
        exc_type: Type[Exception],
    ) -> Optional[ErrorHandlerCallable]:
        """
            Find a custom handler for an exception type.
            
            Checks for exact match first, then walks up the MRO to find
            a handler for a parent class.
            
            :param exc_type: The exception type to look up.
            
            :returns: The custom handler or None if not found.
        """
        # Check exact match first
        if exc_type in self._custom_handlers:
            return self._custom_handlers[exc_type]
        
        # Walk up the MRO to find a handler for a parent class
        for parent_type in exc_type.__mro__:
            if parent_type in self._custom_handlers:
                return self._custom_handlers[parent_type]
        
        return None
    
    def _is_http_exception(self, exc: Exception) -> bool:
        """
            Check if an exception is an HTTP exception.
            
            An HTTP exception is one that has a status_code attribute.
            
            :param exc: The exception to check.
            
            :returns: True if the exception is an HTTP exception.
        """
        return hasattr(exc, "status_code")
    
    def _get_status_code(self, exc: Exception) -> int:
        """
            Get the status code from an HTTP exception.
            
            :param exc: The exception to get the status code from.
            
            :returns: HTTP status code.
        """
        status_code = getattr(exc, "status_code", 500)
        
        if callable(status_code):
            status_code = status_code()
        
        return status_code
    
    def _get_detail(self, exc: Exception) -> Optional[str]:
        """
            Get the detail message from an HTTP exception.
            
            :param exc: The exception to get the detail from.
            
            :returns: Detail message or None.
        """
        # Try common attribute names for detail
        for attr_name in ("detail", "message", "reason"):
            if hasattr(exc, attr_name):
                detail = getattr(exc, attr_name)
                if detail is not None:
                    return str(detail)
        
        return None
