"""
    WSGI Application module.
    
    This module provides the WSGIApplication class that implements the WSGI
    application interface per PEP 3333. It bridges WSGI servers to the framework
    by handling environ parsing, response building, and error handling.
"""

import sys
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple, TYPE_CHECKING

from automojo.webworks.wsgi.environparser import EnvironParser
from automojo.webworks.wsgi.response import Response, ResponseBuilder
from automojo.webworks.wsgi.responseiterator import ResponseIterator
from automojo.webworks.wsgi.errorhandler import ErrorHandler
from automojo.webworks.wsgi.constants import ENVIRON_REQUEST, ENVIRON_DEBUG


if TYPE_CHECKING:
    from automojo.webworks.wsgi.request import Request


# Type alias for WSGI start_response callable
StartResponseCallable = Callable[
    [str, List[Tuple[str, str]], Optional[Tuple[type, BaseException, Any]]],
    Callable[[bytes], None]
]


class WSGIApplication:
    """
        WSGI application callable that bridges WSGI servers to the framework.
        
        Implements PEP 3333 WSGI specification. This class accepts WSGI environ
        dictionaries and start_response callables, processes requests through
        the framework, and returns response iterators.
    """
    
    def __init__(
        self,
        handler: Optional[Callable[["Request"], Response]] = None,
        debug: bool = False,
        max_request_body_size: int = 0,
        error_handler: Optional[ErrorHandler] = None
    ):
        """
            Construct a WSGI application.
            
            :param handler: The request handler callable that processes requests.
            :param debug: If True, include stack traces in error responses.
            :param max_request_body_size: Maximum request body size in bytes (0 = unlimited).
            :param error_handler: Custom error handler for exceptions.
        """
        self._handler = handler
        self._debug = debug
        self._max_request_body_size = max_request_body_size
        
        # Create environ parser with body size limit
        self._environ_parser = EnvironParser(max_body_size=max_request_body_size)
        
        # Create response builder
        self._response_builder = ResponseBuilder()
        
        # Create or use provided error handler
        if error_handler is None:
            self._error_handler = ErrorHandler(debug=debug)
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
    def max_request_body_size(self) -> int:
        """
            Get the maximum request body size.
            
            :returns: Maximum body size in bytes (0 = unlimited).
        """
        return self._max_request_body_size
    
    @property
    def error_handler(self) -> ErrorHandler:
        """
            Get the error handler.
            
            :returns: ErrorHandler instance.
        """
        return self._error_handler
    
    def set_handler(self, handler: Callable[["Request"], Response]) -> None:
        """
            Set the request handler.
            
            :param handler: The request handler callable.
        """
        self._handler = handler
        return
    
    def __call__(
        self,
        environ: Dict[str, Any],
        start_response: StartResponseCallable
    ) -> Iterable[bytes]:
        """
            WSGI application entry point.
            
            This method is called by WSGI servers for each request. It parses
            the environ, processes the request through the handler, and returns
            a response iterator.
            
            :param environ: WSGI environ dictionary.
            :param start_response: WSGI start_response callable.
            
            :returns: Response iterator yielding bytes.
        """
        # Store debug flag in environ for middleware access
        environ[ENVIRON_DEBUG] = self._debug
        
        # Track whether start_response has been called
        response_started = False
        response_iterator: Optional[ResponseIterator] = None
        
        try:
            # Handle the request - this may raise exceptions
            status, headers, response_iterator = self._handle_request(environ)
            
            # Call start_response before yielding body content
            start_response(status, headers)
            response_started = True
            
            # Yield body chunks from the response iterator
            for chunk in response_iterator:
                yield chunk
            
        except Exception as exc:
            # Handle exception based on whether start_response was called
            if response_started:
                # Exception after start_response - use exc_info for error recovery
                exc_info = sys.exc_info()
                try:
                    error_status, error_headers, error_iterator = self._handle_error(
                        exc, environ
                    )
                    # Re-call start_response with exc_info
                    start_response(error_status, error_headers, exc_info)
                    
                    for chunk in error_iterator:
                        yield chunk
                finally:
                    # Clear exc_info to avoid circular references
                    exc_info = None
            else:
                # Exception before start_response - handle and return error response
                error_status, error_headers, error_iterator = self._handle_error(
                    exc, environ
                )
                start_response(error_status, error_headers)
                response_started = True
                
                for chunk in error_iterator:
                    yield chunk
        
        finally:
            # Call close() on response iterator for resource cleanup
            if response_iterator is not None:
                if hasattr(response_iterator, "close"):
                    response_iterator.close()
        
        return
    
    def _handle_request(
        self,
        environ: Dict[str, Any]
    ) -> Tuple[str, List[Tuple[str, str]], ResponseIterator]:
        """
            Handle a single request.
            
            Parses the environ, invokes the handler, and builds the response.
            
            :param environ: WSGI environ dictionary.
            
            :returns: Tuple of (status, headers, response_iterator).
            
            :raises: Any exception from parsing or handling.
        """
        # Parse environ into Request object
        request = self._environ_parser.parse(environ)
        
        # Store request in environ for middleware access
        self._environ_parser.set_framework_environ(environ, request)
        
        # Invoke handler if available
        if self._handler is not None:
            response = self._handler(request)
        else:
            # No handler - return 404
            response = Response(
                status_code=404,
                body=b"Not Found",
                content_type="text/plain; charset=utf-8"
            )
        
        # Build WSGI response format
        status, headers, body_iter = self._response_builder.build(response)
        
        # Wrap body in ResponseIterator for proper cleanup
        response_iterator = ResponseIterator(body_iter)
        
        rtnval = (status, headers, response_iterator)
        return rtnval
    
    def _handle_error(
        self,
        exc: Exception,
        environ: Dict[str, Any]
    ) -> Tuple[str, List[Tuple[str, str]], ResponseIterator]:
        """
            Handle an exception during request processing.
            
            :param exc: The exception that occurred.
            :param environ: WSGI environ dictionary.
            
            :returns: Tuple of (status, headers, response_iterator).
        """
        # Use error handler to create error response
        error_response = self._error_handler.handle(exc, environ)
        
        # Build WSGI response format
        status, headers, body_iter = self._response_builder.build(error_response)
        
        # Wrap body in ResponseIterator
        response_iterator = ResponseIterator(body_iter)
        
        rtnval = (status, headers, response_iterator)
        return rtnval


# Module-level application variable for WSGI server convention
# This variable is used by external WSGI servers (Gunicorn, uWSGI, etc.)
# that look for an 'application' variable in the module.
application: Optional[WSGIApplication] = None


def _get_config_from_environ() -> Dict[str, Any]:
    """
        Get application configuration from environment variables.
        
        Environment variables:
        - WSGI_APP_DEBUG: Enable debug mode (true/false/1/0)
        - WSGI_APP_MAX_BODY_SIZE: Maximum request body size in bytes
        
        :returns: Configuration dictionary.
    """
    import os
    
    config: Dict[str, Any] = {}
    
    # Debug mode
    debug_value = os.environ.get("WSGI_APP_DEBUG", "").lower()
    if debug_value in ("true", "1", "yes", "on"):
        config["debug"] = True
    elif debug_value in ("false", "0", "no", "off"):
        config["debug"] = False
    
    # Max body size
    max_body_value = os.environ.get("WSGI_APP_MAX_BODY_SIZE")
    if max_body_value is not None:
        try:
            config["max_request_body_size"] = int(max_body_value)
        except ValueError:
            pass  # Ignore invalid values
    
    return config


def get_wsgi_application() -> WSGIApplication:
    """
        Get the WSGI application callable.
        
        This is the main entry point for external WSGI servers such as Gunicorn,
        uWSGI, mod_wsgi, and Waitress. Returns the module-level application
        instance, creating one if it doesn't exist.
        
        The application is configured from environment variables:
        - WSGI_APP_DEBUG: Enable debug mode (true/false/1/0)
        - WSGI_APP_MAX_BODY_SIZE: Maximum request body size in bytes
        
        Example usage with Gunicorn:
            gunicorn 'automojo.webworks.wsgi.application:get_wsgi_application()'
        
        Example usage with uWSGI:
            uwsgi --module automojo.webworks.wsgi.application:application
        
        :returns: Configured WSGIApplication instance.
    """
    global application
    
    if application is None:
        # Load configuration from environment variables
        config = _get_config_from_environ()
        application = create_wsgi_application(config)
    
    rtnval = application
    return rtnval


def create_wsgi_application(
    config: Optional[Dict[str, Any]] = None
) -> WSGIApplication:
    """
        Application factory for creating WSGI applications.
        
        Each call creates a new application instance. This is useful for
        testing, when multiple application instances are needed, or when
        using application factory patterns with external WSGI servers.
        
        This function supports the application factory pattern used by
        external WSGI servers like Gunicorn:
            gunicorn 'automojo.webworks.wsgi.application:create_wsgi_application()'
        
        :param config: Optional configuration dict with keys:
            - handler: Request handler callable that accepts Request and returns Response
            - debug: Debug mode flag (default: False)
            - max_request_body_size: Maximum body size in bytes (default: 0 = unlimited)
            - error_handler: Custom ErrorHandler instance
        
        :returns: New WSGIApplication instance.
    """
    if config is None:
        config = {}
    
    handler = config.get("handler")
    debug = config.get("debug", False)
    max_request_body_size = config.get("max_request_body_size", 0)
    error_handler = config.get("error_handler")
    
    rtnval = WSGIApplication(
        handler=handler,
        debug=debug,
        max_request_body_size=max_request_body_size,
        error_handler=error_handler
    )
    
    return rtnval


def set_wsgi_application(app: WSGIApplication) -> None:
    """
        Set the module-level WSGI application.
        
        This function allows setting a pre-configured application instance
        as the module-level application. This is useful when you need to
        configure the application before it's accessed by external WSGI servers.
        
        :param app: The WSGIApplication instance to set.
    """
    global application
    application = app
    return


def reset_wsgi_application() -> None:
    """
        Reset the module-level WSGI application to None.
        
        This function is primarily useful for testing to ensure a clean state
        between tests.
    """
    global application
    application = None
    return

