"""
    Routing exceptions module.
    
    This module defines the exception hierarchy for the routing layer including
    HTTP exceptions that should be converted to appropriate HTTP responses
    and routing-specific errors.
    
    The HTTPException class and its subclasses provide a clean way to signal
    HTTP error conditions from handlers and middleware. The Dispatcher will
    catch these exceptions and convert them to appropriate HTTP responses.
    
    The RoutingError exception is raised when route registration fails due
    to conflicts or invalid configuration.
"""

from typing import Callable, Dict, List, Optional


class HTTPException(Exception):
    """
        Base exception for HTTP errors that should be converted to responses.
        
        HTTP exceptions carry a status code, optional detail message, and
        optional headers. When raised from a handler or middleware, the
        Dispatcher will convert them to appropriate HTTP responses.
        
        :param status_code: HTTP status code (e.g., 404, 500).
        :param detail: Optional detail message describing the error.
        :param headers: Optional dict of additional headers to include.
        
        Example:
            raise HTTPException(404, "Resource not found")
            raise HTTPException(503, "Service unavailable", {"Retry-After": "60"})
    """
    
    def __init__(
        self,
        status_code: int,
        detail: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None
    ):
        """
            Construct an HTTPException.
            
            :param status_code: HTTP status code.
            :param detail: Optional detail message.
            :param headers: Optional dict of additional headers.
        """
        self._status_code = status_code
        self._detail = detail
        self._headers = headers if headers is not None else {}
        
        # Build the exception message
        message = self._build_message()
        super().__init__(message)
        return
    
    def _build_message(self) -> str:
        """
            Build the exception message from status code and detail.
            
            :returns: Formatted exception message.
        """
        # Common HTTP status phrases
        status_phrases = {
            400: "Bad Request",
            401: "Unauthorized",
            403: "Forbidden",
            404: "Not Found",
            405: "Method Not Allowed",
            406: "Not Acceptable",
            408: "Request Timeout",
            409: "Conflict",
            410: "Gone",
            413: "Payload Too Large",
            415: "Unsupported Media Type",
            422: "Unprocessable Entity",
            429: "Too Many Requests",
            500: "Internal Server Error",
            501: "Not Implemented",
            502: "Bad Gateway",
            503: "Service Unavailable",
            504: "Gateway Timeout",
        }
        
        phrase = status_phrases.get(self._status_code, "Error")
        
        if self._detail is not None:
            return f"{self._status_code} {phrase}: {self._detail}"
        
        return f"{self._status_code} {phrase}"
    
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
    
    @property
    def headers(self) -> Dict[str, str]:
        """
            Get the additional headers.
            
            :returns: Dict of header names to values.
        """
        return self._headers


class NotFound(HTTPException):
    """
        404 Not Found exception.
        
        Raised when a requested resource cannot be found.
        
        :param detail: Optional detail message (default: "Not Found").
        
        Example:
            raise NotFound()
            raise NotFound("User with ID 123 not found")
    """
    
    def __init__(self, detail: str = "Not Found"):
        """
            Construct a NotFound exception.
            
            :param detail: Detail message.
        """
        super().__init__(404, detail)
        return


class BadRequest(HTTPException):
    """
        400 Bad Request exception.
        
        Raised when the request is malformed or contains invalid data.
        
        :param detail: Optional detail message (default: "Bad Request").
        
        Example:
            raise BadRequest()
            raise BadRequest("Missing required field 'email'")
    """
    
    def __init__(self, detail: str = "Bad Request"):
        """
            Construct a BadRequest exception.
            
            :param detail: Detail message.
        """
        super().__init__(400, detail)
        return


class Unauthorized(HTTPException):
    """
        401 Unauthorized exception.
        
        Raised when authentication is required but not provided or invalid.
        
        :param detail: Optional detail message (default: "Unauthorized").
        
        Example:
            raise Unauthorized()
            raise Unauthorized("Invalid or expired token")
    """
    
    def __init__(self, detail: str = "Unauthorized"):
        """
            Construct an Unauthorized exception.
            
            :param detail: Detail message.
        """
        super().__init__(401, detail)
        return


class Forbidden(HTTPException):
    """
        403 Forbidden exception.
        
        Raised when the user is authenticated but not authorized to
        access the requested resource.
        
        :param detail: Optional detail message (default: "Forbidden").
        
        Example:
            raise Forbidden()
            raise Forbidden("You do not have permission to delete this resource")
    """
    
    def __init__(self, detail: str = "Forbidden"):
        """
            Construct a Forbidden exception.
            
            :param detail: Detail message.
        """
        super().__init__(403, detail)
        return


class MethodNotAllowed(HTTPException):
    """
        405 Method Not Allowed exception.
        
        Raised when the HTTP method is not supported for the requested
        resource. Includes an Allow header listing the allowed methods.
        
        :param detail: Optional detail message (default: "Method Not Allowed").
        :param allowed: Optional list of allowed HTTP methods.
        
        Example:
            raise MethodNotAllowed()
            raise MethodNotAllowed("POST not allowed", allowed=["GET", "HEAD"])
    """
    
    def __init__(
        self,
        detail: str = "Method Not Allowed",
        allowed: Optional[List[str]] = None
    ):
        """
            Construct a MethodNotAllowed exception.
            
            :param detail: Detail message.
            :param allowed: List of allowed HTTP methods.
        """
        headers = {}
        if allowed is not None:
            headers["Allow"] = ", ".join(allowed)
        
        super().__init__(405, detail, headers)
        self._allowed = allowed
        return
    
    @property
    def allowed(self) -> Optional[List[str]]:
        """
            Get the list of allowed HTTP methods.
            
            :returns: List of allowed methods or None.
        """
        return self._allowed



class RoutingError(Exception):
    """
        Raised when route registration fails due to conflicts or
        invalid configuration.
        
        This exception is raised during route registration when:
        - A route conflicts with an existing registration (same path + method)
        - The route pattern is invalid
        - Other routing configuration errors occur
        
        :param message: Error message describing the issue.
        :param path: The URL path involved in the error.
        :param method: The HTTP method involved in the error.
        :param existing_handler: The handler already registered (if conflict).
        
        Example:
            raise RoutingError(
                "Route conflict: GET /users already registered",
                path="/users",
                method="GET",
                existing_handler=existing_handler_func
            )
    """
    
    def __init__(
        self,
        message: str,
        path: Optional[str] = None,
        method: Optional[str] = None,
        existing_handler: Optional[Callable] = None
    ):
        """
            Construct a RoutingError.
            
            :param message: Error message describing the issue.
            :param path: The URL path involved in the error.
            :param method: The HTTP method involved in the error.
            :param existing_handler: The handler already registered (if conflict).
        """
        self._path = path
        self._method = method
        self._existing_handler = existing_handler
        super().__init__(message)
        return
    
    @property
    def path(self) -> Optional[str]:
        """
            Get the URL path involved in the error.
            
            :returns: URL path or None.
        """
        return self._path
    
    @property
    def method(self) -> Optional[str]:
        """
            Get the HTTP method involved in the error.
            
            :returns: HTTP method or None.
        """
        return self._method
    
    @property
    def existing_handler(self) -> Optional[Callable]:
        """
            Get the handler already registered (if conflict).
            
            :returns: Handler callable or None.
        """
        return self._existing_handler
