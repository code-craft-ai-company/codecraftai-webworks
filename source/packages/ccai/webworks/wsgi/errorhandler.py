"""
    WSGI Error Handler module.
    
    This module provides the ErrorHandler class that handles exceptions during
    WSGI request processing and converts them to appropriate HTTP error responses.
"""

import logging
import sys
import traceback
from typing import Any, Callable, Dict, Optional, Type

from ccai.webworks.wsgi.constants import HTTP_STATUS_PHRASES
from ccai.webworks.wsgi.exceptions import HTTPException
from ccai.webworks.wsgi.response import Response


class ErrorHandler:
    """
        Handles exceptions during WSGI request processing.
        
        This class provides centralized exception handling for the WSGI layer,
        converting exceptions to appropriate HTTP error responses. It supports
        both debug and production modes, custom exception handlers, and proper
        exception logging.
    """
    
    def __init__(
        self,
        debug: bool = False,
        logger: Optional[logging.Logger] = None
    ):
        """
            Construct an error handler.
            
            :param debug: If True, include stack traces in responses.
            :param logger: Logger for error logging. If None, uses module logger.
        """
        self._debug = debug
        
        if logger is None:
            self._logger = logging.getLogger(__name__)
        else:
            self._logger = logger
        
        # Registry of custom exception handlers
        self._custom_handlers: Dict[Type[Exception], Callable[[Exception], Response]] = {}
        
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

    def handle(
        self,
        exc: Exception,
        environ: Dict[str, Any]
    ) -> Response:
        """
            Handle an exception and return an error response.
            
            This method dispatches exceptions to the appropriate handler based on
            the exception type. It first checks for custom registered handlers,
            then handles HTTPException subclasses, and finally handles unhandled
            exceptions with a 500 response.
            
            :param exc: The exception that occurred.
            :param environ: WSGI environ for context.
            
            :returns: Error Response object.
        """
        # Check for custom handlers first (most specific type match)
        exc_type = type(exc)
        
        # Look for exact type match first
        if exc_type in self._custom_handlers:
            handler = self._custom_handlers[exc_type]
            rtnval = handler(exc)
            return rtnval
        
        # Look for parent type matches
        for registered_type, handler in self._custom_handlers.items():
            if isinstance(exc, registered_type):
                rtnval = handler(exc)
                return rtnval
        
        # Handle HTTPException subclasses
        if isinstance(exc, HTTPException):
            rtnval = self.handle_http_exception(exc)
            return rtnval
        
        # Handle all other exceptions as unhandled
        rtnval = self.handle_unhandled_exception(exc, environ)
        return rtnval
    
    def handle_http_exception(self, exc: HTTPException) -> Response:
        """
            Handle HTTPException subclasses.
            
            Creates an error response with the status code and message from
            the HTTPException.
            
            :param exc: The HTTPException that occurred.
            
            :returns: Error Response object.
        """
        status_code = exc.status_code
        message = exc.message
        
        body = self.format_error_body(status_code, message, exc)
        
        rtnval = Response(
            status_code=status_code,
            body=body,
            content_type="text/plain; charset=utf-8"
        )
        
        return rtnval

    def handle_unhandled_exception(
        self,
        exc: Exception,
        environ: Dict[str, Any]
    ) -> Response:
        """
            Handle unhandled exceptions with 500 response.
            
            Logs the exception with stack trace and returns an HTTP 500
            Internal Server Error response.
            
            :param exc: The exception that occurred.
            :param environ: WSGI environ for context.
            
            :returns: Error Response object with status 500.
        """
        # Log the exception with stack trace
        self.log_exception(exc, environ)
        
        status_code = 500
        message = HTTP_STATUS_PHRASES.get(status_code, "Internal Server Error")
        
        body = self.format_error_body(status_code, message, exc)
        
        rtnval = Response(
            status_code=status_code,
            body=body,
            content_type="text/plain; charset=utf-8"
        )
        
        return rtnval
    
    def format_error_body(
        self,
        status_code: int,
        message: str,
        exc: Optional[Exception] = None
    ) -> bytes:
        """
            Format error response body.
            
            In debug mode, includes stack trace.
            In production mode, includes only status and message.
            
            :param status_code: HTTP status code.
            :param message: Error message.
            :param exc: Optional exception for stack trace in debug mode.
            
            :returns: Formatted error body as bytes.
        """
        reason = HTTP_STATUS_PHRASES.get(status_code, "Error")
        
        lines = [
            f"{status_code} {reason}",
            "",
            message,
        ]
        
        if self._debug and exc is not None:
            lines.append("")
            lines.append("--- Stack Trace ---")
            
            # Get the full traceback
            tb_lines = traceback.format_exception(type(exc), exc, exc.__traceback__)
            for tb_line in tb_lines:
                # Remove trailing newlines and add each line
                for line in tb_line.rstrip("\n").split("\n"):
                    lines.append(line)
        
        body_text = "\n".join(lines)
        rtnval = body_text.encode("utf-8")
        
        return rtnval
    
    def log_exception(
        self,
        exc: Exception,
        environ: Dict[str, Any]
    ) -> None:
        """
            Log exception with stack trace.
            
            Logs the exception at ERROR level with full stack trace and
            request context from the environ.
            
            :param exc: The exception that occurred.
            :param environ: WSGI environ for context.
        """
        # Extract request context from environ
        method = environ.get("REQUEST_METHOD", "UNKNOWN")
        path = environ.get("PATH_INFO", "/")
        query = environ.get("QUERY_STRING", "")
        
        if query:
            request_line = f"{method} {path}?{query}"
        else:
            request_line = f"{method} {path}"
        
        # Format the exception with traceback
        exc_info = (type(exc), exc, exc.__traceback__)
        
        self._logger.error(
            "Unhandled exception during request: %s",
            request_line,
            exc_info=exc_info
        )
        
        return
    
    def register_handler(
        self,
        exc_type: Type[Exception],
        handler: Callable[[Exception], Response]
    ) -> None:
        """
            Register a custom handler for an exception type.
            
            Custom handlers take precedence over the default handling for
            HTTPException and unhandled exceptions.
            
            :param exc_type: Exception type to handle.
            :param handler: Handler function that takes an exception and returns a Response.
        """
        self._custom_handlers[exc_type] = handler
        return
    
    def unregister_handler(self, exc_type: Type[Exception]) -> bool:
        """
            Unregister a custom handler for an exception type.
            
            :param exc_type: Exception type to unregister.
            
            :returns: True if handler was removed, False if not found.
        """
        if exc_type in self._custom_handlers:
            del self._custom_handlers[exc_type]
            rtnval = True
        else:
            rtnval = False
        
        return rtnval
    
    def has_custom_handler(self, exc_type: Type[Exception]) -> bool:
        """
            Check if a custom handler is registered for an exception type.
            
            :param exc_type: Exception type to check.
            
            :returns: True if a custom handler is registered.
        """
        rtnval = exc_type in self._custom_handlers
        return rtnval
