"""
    ASGI Application module.
    
    This module provides the ASGIApplication class that serves as the main
    entry point for ASGI servers. It implements the ASGI 3.0 specification
    and dispatches requests to the appropriate handlers based on scope type.
    
    This module also provides server integration functions:
    - get_asgi_application(): Returns a configured ASGIApplication instance
    - create_asgi_application(): Factory function for creating new instances
    - application: Module-level variable for ASGI server convention
"""

import logging
from typing import Any, Awaitable, Callable, Dict, Optional, Union

from automojo.webworks.asgi.constants import (
    SCOPE_TYPE_HTTP,
    SCOPE_TYPE_WEBSOCKET,
    SCOPE_TYPE_LIFESPAN,
)
from automojo.webworks.asgi.httphandler import HTTPHandler
from automojo.webworks.asgi.websockethandler import WebSocketHandler
from automojo.webworks.asgi.lifespanhandler import LifespanHandler
from automojo.webworks.asgi.errorhandler import ErrorHandler
from automojo.webworks.asgi.exceptions import ASGIError


# Type aliases for clarity
ReceiveCallable = Callable[[], Awaitable[Dict[str, Any]]]
SendCallable = Callable[[Dict[str, Any]], Awaitable[None]]


class UnknownScopeTypeError(ASGIError):
    """
        Exception raised when an unknown scope type is received.
        
        This exception is raised when the ASGI application receives a scope
        with a type that it does not know how to handle.
    """
    
    def __init__(self, scope_type: str):
        """
            Construct an UnknownScopeTypeError.
            
            :param scope_type: The unknown scope type that was received.
        """
        self._scope_type = scope_type
        message = f"Unknown ASGI scope type: {scope_type}"
        super().__init__(message)
        return
    
    @property
    def scope_type(self) -> str:
        """
            Get the unknown scope type.
            
            :returns: The unknown scope type string.
        """
        return self._scope_type


class ASGIApplication:
    """
        ASGI application callable that bridges ASGI servers to the framework.
        
        This class implements the ASGI 3.0 specification and serves as the
        main entry point for ASGI servers. It dispatches requests to the
        appropriate handlers based on the scope type (http, websocket, lifespan).
        
        The application supports:
        - HTTP request/response cycles
        - WebSocket connections
        - Lifespan events (startup/shutdown)
        - Async handlers and middleware
        - Custom error handling
    """
    
    def __init__(
        self,
        http_handler: Optional[HTTPHandler] = None,
        websocket_handler: Optional[WebSocketHandler] = None,
        lifespan_handler: Optional[LifespanHandler] = None,
        error_handler: Optional[ErrorHandler] = None,
        debug: bool = False,
        logger: Optional[logging.Logger] = None,
    ):
        """
            Construct an ASGI application.
            
            :param http_handler: Handler for HTTP requests. If None, a default
                                handler will be created.
            :param websocket_handler: Handler for WebSocket connections. If None,
                                     a default handler will be created.
            :param lifespan_handler: Handler for lifespan events. If None, a
                                    default handler will be created.
            :param error_handler: Handler for errors. If None, a default handler
                                 will be created.
            :param debug: If True, include stack traces in error responses.
            :param logger: Logger for application logging. If None, a default
                          logger will be created.
        """
        self._debug = debug
        
        if logger is None:
            self._logger = logging.getLogger(__name__)
        else:
            self._logger = logger
        
        if http_handler is None:
            self._http_handler = HTTPHandler(debug=debug)
        else:
            self._http_handler = http_handler
        
        if websocket_handler is None:
            self._websocket_handler = WebSocketHandler(debug=debug, logger=self._logger)
        else:
            self._websocket_handler = websocket_handler
        
        if lifespan_handler is None:
            self._lifespan_handler = LifespanHandler(logger=self._logger)
        else:
            self._lifespan_handler = lifespan_handler
        
        if error_handler is None:
            self._error_handler = ErrorHandler(debug=debug, logger=self._logger)
        else:
            self._error_handler = error_handler
        
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
    
    @property
    def http_handler(self) -> HTTPHandler:
        """
            Get the HTTP handler.
            
            :returns: HTTPHandler instance.
        """
        return self._http_handler
    
    @property
    def websocket_handler(self) -> WebSocketHandler:
        """
            Get the WebSocket handler.
            
            :returns: WebSocketHandler instance.
        """
        return self._websocket_handler
    
    @property
    def lifespan_handler(self) -> LifespanHandler:
        """
            Get the lifespan handler.
            
            :returns: LifespanHandler instance.
        """
        return self._lifespan_handler
    
    @property
    def error_handler(self) -> ErrorHandler:
        """
            Get the error handler.
            
            :returns: ErrorHandler instance.
        """
        return self._error_handler

    async def __call__(
        self,
        scope: Dict[str, Any],
        receive: ReceiveCallable,
        send: SendCallable,
    ) -> None:
        """
            ASGI application entry point.
            
            This method is called by the ASGI server for each connection.
            It dispatches to the appropriate handler based on the scope type.
            
            :param scope: ASGI scope dictionary containing connection metadata.
            :param receive: Async callable to receive messages from the client.
            :param send: Async callable to send messages to the client.
            
            :raises UnknownScopeTypeError: If the scope type is not recognized.
        """
        scope_type = scope.get("type", "")
        
        if scope_type == SCOPE_TYPE_HTTP:
            await self._handle_http(scope, receive, send)
        elif scope_type == SCOPE_TYPE_WEBSOCKET:
            await self._handle_websocket(scope, receive, send)
        elif scope_type == SCOPE_TYPE_LIFESPAN:
            await self._handle_lifespan(scope, receive, send)
        else:
            await self._handle_unknown(scope, receive, send)
        
        return
    
    async def _handle_http(
        self,
        scope: Dict[str, Any],
        receive: ReceiveCallable,
        send: SendCallable,
    ) -> None:
        """
            Handle HTTP request/response cycle.
            
            Delegates to the HTTP handler and uses the error handler for
            any unhandled exceptions that propagate up.
            
            :param scope: ASGI HTTP scope dictionary.
            :param receive: Async receive callable.
            :param send: Async send callable.
        """
        try:
            await self._http_handler.handle(scope, receive, send)
        except Exception as exc:
            # Use the error handler for any exceptions that propagate up
            await self._error_handler.handle_http_error(exc, send, scope)
        return
    
    async def _handle_websocket(
        self,
        scope: Dict[str, Any],
        receive: ReceiveCallable,
        send: SendCallable,
    ) -> None:
        """
            Handle WebSocket connection.
            
            Delegates to the WebSocket handler and uses the error handler for
            any unhandled exceptions that propagate up.
            
            :param scope: ASGI WebSocket scope dictionary.
            :param receive: Async receive callable.
            :param send: Async send callable.
        """
        try:
            await self._websocket_handler.handle(scope, receive, send)
        except Exception as exc:
            # Use the error handler for any exceptions that propagate up
            await self._error_handler.handle_websocket_error(exc, send, scope)
        return
    
    async def _handle_lifespan(
        self,
        scope: Dict[str, Any],
        receive: ReceiveCallable,
        send: SendCallable,
    ) -> None:
        """
            Handle lifespan startup/shutdown events.
            
            :param scope: ASGI lifespan scope dictionary.
            :param receive: Async receive callable.
            :param send: Async send callable.
        """
        await self._lifespan_handler.handle(scope, receive, send)
        return
    
    async def _handle_unknown(
        self,
        scope: Dict[str, Any],
        receive: ReceiveCallable,
        send: SendCallable,
    ) -> None:
        """
            Handle unknown scope type.
            
            This method is called when the scope type is not recognized.
            It raises an UnknownScopeTypeError.
            
            :param scope: ASGI scope dictionary.
            :param receive: Async receive callable.
            :param send: Async send callable.
            
            :raises UnknownScopeTypeError: Always raised for unknown scope types.
        """
        scope_type = scope.get("type", "")
        self._logger.warning(f"Received unknown ASGI scope type: {scope_type}")
        raise UnknownScopeTypeError(scope_type)


# =============================================================================
# Module-level application variable for ASGI server convention
# =============================================================================

# Module-level application variable for ASGI servers.
# This follows the convention used by ASGI servers like Uvicorn, Hypercorn,
# and Daphne where they look for an 'application' variable in the module.
# This variable is initialized to None and can be set by calling
# get_asgi_application() or create_asgi_application().
application: Optional[ASGIApplication] = None


# =============================================================================
# Singleton instance for get_asgi_application()
# =============================================================================

_singleton_application: Optional[ASGIApplication] = None


# =============================================================================
# Server Integration Functions
# =============================================================================

def get_asgi_application(
    debug: bool = False,
    lifespan_enabled: bool = True,
    **kwargs: Any,
) -> ASGIApplication:
    """
        Get the ASGI application callable.
        
        This is the main entry point for ASGI servers. It returns a singleton
        ASGIApplication instance, creating it on first call. Subsequent calls
        return the same instance.
        
        This function is useful when you want to ensure only one application
        instance exists throughout the application lifecycle.
        
        :param debug: If True, include stack traces in error responses.
                     Only used on first call when creating the instance.
        :param lifespan_enabled: If True, enable lifespan protocol support.
                                Only used on first call when creating the instance.
        :param kwargs: Additional keyword arguments passed to ASGIApplication.
                      Only used on first call when creating the instance.
        
        :returns: Configured ASGIApplication instance.
        
        Example usage with Uvicorn:
        
            # In your application module (e.g., app.py):
            from automojo.webworks.asgi import get_asgi_application
            
            application = get_asgi_application(debug=True)
            
            # Run with: uvicorn app:application
    """
    global _singleton_application
    global application
    
    if _singleton_application is None:
        _singleton_application = create_asgi_application(
            debug=debug,
            lifespan_enabled=lifespan_enabled,
            **kwargs,
        )
        # Also set the module-level application variable
        application = _singleton_application
    
    return _singleton_application


def create_asgi_application(
    config: Optional[Dict[str, Any]] = None,
    debug: bool = False,
    lifespan_enabled: bool = True,
    http_handler: Optional[HTTPHandler] = None,
    websocket_handler: Optional[WebSocketHandler] = None,
    lifespan_handler: Optional[LifespanHandler] = None,
    error_handler: Optional[ErrorHandler] = None,
    logger: Optional[logging.Logger] = None,
) -> ASGIApplication:
    """
        Application factory for creating ASGI applications.
        
        Each call creates a new application instance. This is useful for
        testing or when you need multiple isolated application instances.
        
        The factory supports two ways of configuration:
        1. Using the config dict parameter
        2. Using individual keyword arguments
        
        If both are provided, keyword arguments take precedence over config dict.
        
        :param config: Optional configuration dictionary with keys:
                      - debug: bool - Enable debug mode
                      - lifespan_enabled: bool - Enable lifespan protocol
                      - http_handler: HTTPHandler instance
                      - websocket_handler: WebSocketHandler instance
                      - lifespan_handler: LifespanHandler instance
                      - error_handler: ErrorHandler instance
                      - logger: Logger instance
        :param debug: If True, include stack traces in error responses.
        :param lifespan_enabled: If True, enable lifespan protocol support.
                                If False, lifespan events are ignored.
        :param http_handler: Custom HTTP handler instance.
        :param websocket_handler: Custom WebSocket handler instance.
        :param lifespan_handler: Custom lifespan handler instance.
        :param error_handler: Custom error handler instance.
        :param logger: Logger instance for application logging.
        
        :returns: New ASGIApplication instance.
        
        Example usage:
        
            # Create application with config dict
            app = create_asgi_application(config={
                "debug": True,
                "lifespan_enabled": True,
            })
            
            # Create application with keyword arguments
            app = create_asgi_application(debug=True, lifespan_enabled=True)
            
            # Create application for testing (new instance each time)
            def test_something():
                app = create_asgi_application(debug=True)
                # ... test code ...
    """
    # Merge config dict with keyword arguments (kwargs take precedence)
    effective_config: Dict[str, Any] = {}
    
    if config is not None:
        effective_config.update(config)
    
    # Override with explicit keyword arguments
    effective_debug = debug
    if "debug" in effective_config and debug is False:
        effective_debug = effective_config["debug"]
    
    effective_lifespan_enabled = lifespan_enabled
    if "lifespan_enabled" in effective_config and lifespan_enabled is True:
        effective_lifespan_enabled = effective_config["lifespan_enabled"]
    
    effective_http_handler = http_handler
    if effective_http_handler is None and "http_handler" in effective_config:
        effective_http_handler = effective_config["http_handler"]
    
    effective_websocket_handler = websocket_handler
    if effective_websocket_handler is None and "websocket_handler" in effective_config:
        effective_websocket_handler = effective_config["websocket_handler"]
    
    effective_lifespan_handler = lifespan_handler
    if effective_lifespan_handler is None and "lifespan_handler" in effective_config:
        effective_lifespan_handler = effective_config["lifespan_handler"]
    
    effective_error_handler = error_handler
    if effective_error_handler is None and "error_handler" in effective_config:
        effective_error_handler = effective_config["error_handler"]
    
    effective_logger = logger
    if effective_logger is None and "logger" in effective_config:
        effective_logger = effective_config["logger"]
    
    # Create the lifespan handler with enabled/disabled support
    if effective_lifespan_handler is None:
        effective_lifespan_handler = LifespanHandler(
            logger=effective_logger,
            enabled=effective_lifespan_enabled,
        )
    
    # Create the application
    app = ASGIApplication(
        http_handler=effective_http_handler,
        websocket_handler=effective_websocket_handler,
        lifespan_handler=effective_lifespan_handler,
        error_handler=effective_error_handler,
        debug=effective_debug,
        logger=effective_logger,
    )
    
    return app


def reset_singleton_application() -> None:
    """
        Reset the singleton application instance.
        
        This function is primarily intended for testing purposes. It clears
        the singleton instance so that the next call to get_asgi_application()
        will create a new instance.
        
        :returns: None
    """
    global _singleton_application
    global application
    
    _singleton_application = None
    application = None
    
    return


def get_application_variable() -> Optional[ASGIApplication]:
    """
        Get the current value of the module-level application variable.
        
        This function provides a way to access the module-level application
        variable from other modules without import-time binding issues.
        
        :returns: The current ASGIApplication instance, or None if not set.
    """
    return application
