"""
    WSGI Middleware module.
    
    This module provides the WSGIMiddlewareWrapper class that helps wrap WSGI
    applications with middleware. It supports single middleware wrapping and
    chaining multiple middlewares together.
"""

from typing import Any, Callable, Dict, Iterable, List, Tuple


# Type alias for WSGI application callable
WSGIAppCallable = Callable[
    [Dict[str, Any], Callable[[str, List[Tuple[str, str]]], Callable[[bytes], None]]],
    Iterable[bytes]
]

# Type alias for WSGI middleware factory
WSGIMiddlewareFactory = Callable[[WSGIAppCallable], WSGIAppCallable]


class WSGIMiddlewareWrapper:
    """
        Helper for wrapping WSGI applications with middleware.
        
        This class provides static methods for applying WSGI middleware to
        applications. Middleware follows the standard WSGI pattern where a
        middleware factory accepts an application and returns a wrapped
        application.
        
        Middleware can:
        - Modify the environ before calling the application
        - Modify the response after the application returns
        - Short-circuit the request without calling the application
        
        Example middleware factory::
        
            def logging_middleware(app):
                def middleware(environ, start_response):
                    print(f"Request: {environ['REQUEST_METHOD']} {environ['PATH_INFO']}")
                    return app(environ, start_response)
                return middleware
    """
    
    @staticmethod
    def wrap(
        app: WSGIAppCallable,
        middleware: WSGIMiddlewareFactory
    ) -> WSGIAppCallable:
        """
            Wrap a WSGI application with middleware.
            
            The middleware factory is called with the application and should
            return a new callable that wraps the original application.
            
            :param app: The inner WSGI application.
            :param middleware: The middleware factory to wrap with.
            
            :returns: Wrapped WSGI application.
        """
        wrapped_app = middleware(app)
        return wrapped_app
    
    @staticmethod
    def wrap_multiple(
        app: WSGIAppCallable,
        middlewares: List[WSGIMiddlewareFactory]
    ) -> WSGIAppCallable:
        """
            Wrap a WSGI application with multiple middlewares.
            
            Middlewares are applied in order, so the first middleware in the
            list is the outermost wrapper. This means the first middleware
            receives the request first and the response last.
            
            For example, with middlewares [A, B, C]:
            - Request flow: A -> B -> C -> app
            - Response flow: app -> C -> B -> A
            
            :param app: The inner WSGI application.
            :param middlewares: List of middleware factories to apply.
            
            :returns: Wrapped WSGI application.
        """
        # Apply middlewares in reverse order so the first middleware
        # in the list becomes the outermost wrapper
        wrapped_app = app
        
        for middleware in reversed(middlewares):
            wrapped_app = middleware(wrapped_app)
        
        return wrapped_app

