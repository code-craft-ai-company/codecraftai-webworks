"""
    WSGI Application module.
    
    This module provides the WSGIApplication class, a PEP 3333 adapter around a
    synchronous handler that takes framework Requests, and the functions that
    give external WSGI servers the application to serve:

    - get_wsgi_application() finds the application once (the one set with
      set_wsgi_application(), the import target in WEBWORKS_SERVER_APP, or the
      established web application persona) and returns its WSGI callable; a
      WebApplication is served by its ``wsgi_app``, which runs the full ASGI
      pipeline of the application through an ASGIBridge,
    - the module attribute 'application' is the same callable, for servers
      that load a module-level variable,
    - resolve_wsgi_application() and as_wsgi_application() do the resolution
      for other callers, such as the production server.
"""

import logging
import os
import sys
import threading

from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple, TYPE_CHECKING

from ccai.errors.exceptions import ConfigurationError

from ccai.webworks.wsgi.asgibridge import ASGIBridge, is_asgi_application
from ccai.webworks.wsgi.environparser import EnvironParser
from ccai.webworks.wsgi.response import Response, ResponseBuilder
from ccai.webworks.wsgi.responseiterator import ResponseIterator
from ccai.webworks.wsgi.errorhandler import ErrorHandler
from ccai.webworks.wsgi.constants import (
    DEFAULT_MAX_REQUEST_BODY_SIZE,
    ENVIRON_DEBUG,
)


# Module-level logger. The WSGI generator translates handler
# exceptions into error responses but the operator wants the
# traceback in the journal so a 500 isn't opaque.
logger = logging.getLogger(__name__)


if TYPE_CHECKING:
    from ccai.webworks.routing.request import Request


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
        max_request_body_size: int = DEFAULT_MAX_REQUEST_BODY_SIZE,
        error_handler: Optional[ErrorHandler] = None
    ):
        """
            Construct a WSGI application.
            
            :param handler: The request handler callable that processes requests.
            :param debug: If True, include stack traces in error responses.
            :param max_request_body_size: Maximum request body size in bytes. The body
                                          is held in memory, so the default is a limit
                                          and not unlimited. Pass 0 for unlimited.
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
            # Log unconditionally — the WSGI generator turns this
            # into a structured error response, but the journal
            # needs to carry the underlying traceback so the
            # operator can debug a 500 without re-running the
            # request.
            logger.exception(
                "WSGIApplication: handler raised %s for %s %s",
                type(exc).__name__,
                environ.get("REQUEST_METHOD", "?"),
                environ.get("PATH_INFO", "?"),
            )
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
                    # Drop the exc_info reference to avoid circular references
                    del exc_info
            else:
                # Exception before start_response - handle and return error response
                error_status, error_headers, error_iterator = self._handle_error(
                    exc, environ
                )
                start_response(error_status, error_headers)
                
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


# The application the module serves to external WSGI servers, once it has
# been resolved or set. Read it through get_wsgi_application(), or as the
# module attribute 'application' (see __getattr__ below).
_application: Optional[Callable[..., Iterable[bytes]]] = None
_application_lock = threading.RLock()


# Environment variable naming the application to serve, the same import
# target ('module:attribute') the webworks command line reads from the
# 'server.app' configuration key.
APP_TARGET_ENVIRON_KEY: str = "WEBWORKS_SERVER_APP"


def __getattr__(name: str) -> Any:
    """
        Resolve the module attribute 'application' when it is first read.

        Servers that load a module-level variable (uWSGI's
        ``--module ccai.webworks.wsgi.application:application``) get the
        same application as get_wsgi_application() returns.

        :param name: The attribute being read.

        :returns: The WSGI application for 'application'.

        :raises AttributeError: For any other name.
    """
    if name == "application":
        rtnval = get_wsgi_application()
        return rtnval

    errmsg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(errmsg)


def as_wsgi_application(candidate: Any) -> Callable[..., Iterable[bytes]]:
    """
        Turn an application object into the WSGI callable that serves it.

        - A :class:`WebApplication` is served by its ``wsgi_app``.
        - The ASGI application of the established web application persona
          (the ``app`` a site module exports) is served by the persona's
          ``wsgi_app``, so the persona's lifespan runs once.
        - Any other ASGI application is served by an :class:`ASGIBridge`
          of its own.
        - Any other callable is taken to be a WSGI application already.

        :param candidate: The application object.

        :returns: The WSGI callable.

        :raises ConfigurationError: If the object is not an application.
    """
    # Imported here: the web application imports this package
    from ccai.webworks.webapplication import WebApplication
    from ccai.webworks.persona.lifecycle import LifecyclePhase
    import ccai.webworks.wellknown as webworks_wellknown

    if isinstance(candidate, WebApplication):
        rtnval = candidate.wsgi_app
        return rtnval

    if is_asgi_application(candidate):
        persona = webworks_wellknown.THISWEBAPPLICATION_SINGLETON
        serving_phases = (LifecyclePhase.INFRASTRUCTURE_READY, LifecyclePhase.READY)

        if persona is not None and persona.current_phase in serving_phases and candidate is persona.asgi_app:
            rtnval = persona.wsgi_app
        else:
            rtnval = ASGIBridge(asgi_app=candidate)
        return rtnval

    if callable(candidate):
        rtnval = candidate
        return rtnval

    errmsg = (
        f"A {type(candidate).__name__} object is not an application that can be served over WSGI. "
        f"Expected a WebApplication, an ASGI application or a WSGI callable."
    )
    raise ConfigurationError(errmsg)


def resolve_wsgi_application(target: Optional[str] = None) -> Callable[..., Iterable[bytes]]:
    """
        Find the application to serve and return its WSGI callable.

        When a target is given, its module is imported (which establishes
        the persona of a webworks site) and the object it names is served,
        see :func:`as_wsgi_application`. Without a target, the established
        web application persona is served.

        :param target: An import target 'module:attribute', for example
            'mysite.app:webapp' or 'mysite.app:app'.

        :returns: The WSGI callable.

        :raises ConfigurationError: If the target cannot be imported, or no
            target is given and no web application persona is established.
    """
    # Imported here: the command line tools import the framework packages
    from ccai.webworks.devexp.apploader import ApplicationLoadError, load_application
    import ccai.webworks.wellknown as webworks_wellknown

    if target is not None and target.strip() != "":
        try:
            candidate = load_application(target)
        except ApplicationLoadError as load_err:
            errmsg = f"The WSGI application target {target!r} cannot be loaded: {load_err}"
            raise ConfigurationError(errmsg) from load_err

        rtnval = as_wsgi_application(candidate)
        return rtnval

    persona = webworks_wellknown.THISWEBAPPLICATION_SINGLETON

    if persona is None:
        errmsg = (
            f"There is no application to serve. Set {APP_TARGET_ENVIRON_KEY} to an import "
            f"target ('module:attribute', for example 'mysite.app:webapp'), or establish the "
            f"web application persona before the WSGI application is requested."
        )
        raise ConfigurationError(errmsg)

    rtnval = persona.wsgi_app
    return rtnval


def get_wsgi_application() -> Callable[..., Iterable[bytes]]:
    """
        Get the WSGI application callable for external WSGI servers.

        This is the entry point for servers such as Gunicorn, uWSGI,
        mod_wsgi and Waitress. The application is found once and the same
        callable is returned afterwards:

        1. the application set with :func:`set_wsgi_application`,
        2. the import target in the ``WEBWORKS_SERVER_APP`` environment
           variable (the variable the ``webworks`` command line reads for
           'server.app'): a WebApplication or the ASGI application of a site
           is served through its ``wsgi_app``,
        3. the established web application persona.

        Example usage with Gunicorn::

            WEBWORKS_SERVER_APP=mysite.app:webapp \
                gunicorn 'ccai.webworks.wsgi.application:get_wsgi_application()'

        Example usage with uWSGI::

            WEBWORKS_SERVER_APP=mysite.app:webapp \
                uwsgi --module ccai.webworks.wsgi.application:application

        :returns: The WSGI callable.

        :raises ConfigurationError: If there is no application to serve.
    """
    global _application

    with _application_lock:
        if _application is None:
            target = os.environ.get(APP_TARGET_ENVIRON_KEY)
            _application = resolve_wsgi_application(target)

        rtnval = _application

    return rtnval


def create_wsgi_application(
    config: Optional[Dict[str, Any]] = None
) -> WSGIApplication:
    """
        Application factory for a WSGIApplication around a synchronous handler.

        Each call creates a new application instance. This is the lower-level
        adapter for code that handles framework Requests itself; a
        WebApplication is served by its ``wsgi_app`` instead (see
        :func:`get_wsgi_application`).

        :param config: Optional configuration dict with keys:
            - handler: Request handler callable that accepts Request and returns Response
            - debug: Debug mode flag (default: False)
            - max_request_body_size: Maximum body size in bytes
              (default: DEFAULT_MAX_REQUEST_BODY_SIZE, 0 = unlimited)
            - error_handler: Custom ErrorHandler instance
        
        :returns: New WSGIApplication instance.
    """
    if config is None:
        config = {}
    
    handler = config.get("handler")
    debug = config.get("debug", False)
    max_request_body_size = config.get("max_request_body_size", DEFAULT_MAX_REQUEST_BODY_SIZE)
    error_handler = config.get("error_handler")
    
    rtnval = WSGIApplication(
        handler=handler,
        debug=debug,
        max_request_body_size=max_request_body_size,
        error_handler=error_handler
    )
    
    return rtnval


def set_wsgi_application(app: Callable[..., Iterable[bytes]]) -> None:
    """
        Set the application the module serves to external WSGI servers.

        Use this to serve a pre-configured application: get_wsgi_application()
        and the module attribute 'application' return it from then on.

        :param app: The WSGI callable.
    """
    global _application

    with _application_lock:
        _application = app

    return


def reset_wsgi_application() -> None:
    """
        Forget the application the module serves.

        The next get_wsgi_application() call finds it again. Mainly useful
        for tests.
    """
    global _application

    with _application_lock:
        _application = None

    return
