"""
.. module:: ccai.webworks.endpoints.rest.errors
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Error handling infrastructure for REST API support.
               Provides exception-to-HTTP-error mapping and production mode
               error hiding.

.. moduleauthor:: Code Craft AI LLC
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []

from typing import Any, Dict, Optional, Tuple, Type

from ccai.webworks.endpoints.rest.models import (
    ErrorMapping,
    RESTError,
)
from ccai.webworks.endpoints.rest.exceptions import HTTPException, ValidationError


# Error codes for the HTTP statuses an exception can carry. A status that is
# not listed is reported as ``http_<status>``.
HTTP_STATUS_ERROR_CODES: Dict[int, str] = {
    400: "bad_request",
    401: "unauthorized",
    403: "forbidden",
    404: "not_found",
    405: "method_not_allowed",
    406: "not_acceptable",
    409: "conflict",
    410: "gone",
    413: "payload_too_large",
    415: "unsupported_media_type",
    422: "unprocessable_entity",
    429: "too_many_requests",
    500: "internal_error",
    501: "not_implemented",
    503: "service_unavailable",
}


# The mappings of built-in exceptions that ErrorHandler applied by default
# in releases up to 1.6.0: ValueError -> 400 (with the exception text as
# the message), KeyError -> 404 and PermissionError -> 403. They are no
# longer defaults (see ErrorHandler.DEFAULT_MAPPINGS); an application that
# relies on them turns them back on with ErrorHandler(builtin_mappings=True),
# ErrorHandler.register_builtin_mappings(),
# create_rest_middleware(builtin_mappings=True) or, for one endpoint,
# error_map=BUILTIN_EXCEPTION_MAPPINGS. Doing so also brings back what they
# cost: an accidental ValueError, KeyError or PermissionError anywhere under a
# handler is answered as a client error, and a ValueError's text is sent to
# the client.
BUILTIN_EXCEPTION_MAPPINGS: Dict[Type[Exception], ErrorMapping] = {
    ValueError: ErrorMapping(
        status_code=400,
        error_code="bad_request",
        message_template=None  # Use exception message
    ),
    KeyError: ErrorMapping(
        status_code=404,
        error_code="not_found",
        message_template="Resource not found: {}"
    ),
    PermissionError: ErrorMapping(
        status_code=403,
        error_code="forbidden",
        message_template="Access denied"
    ),
}


def get_http_exception_status(exception: Exception) -> Optional[int]:
    """
        The HTTP status an exception asks for, when it is one of the
        framework's HTTP exceptions.

        Two families qualify: :class:`ccai.webworks.endpoints.rest.exceptions.HTTPException`
        (``NotAcceptable``, ``UnsupportedMediaType``) and
        :class:`ccai.webworks.routing.exceptions.HTTPException` (``NotFound``,
        ``BadRequest``, ``Forbidden`` and the rest). Both state their status
        and a detail message themselves, so no mapping has to be registered
        for them.

        Args:
            exception: The exception to inspect.

        Returns:
            The status code, or None if the exception is not a framework
            HTTP exception.
    """
    # Imported here: the routing package imports the endpoints package while
    # it is being initialised, so a module-level import would be circular.
    from ccai.webworks.routing.exceptions import HTTPException as RoutingHTTPException

    if not isinstance(exception, (HTTPException, RoutingHTTPException)):
        return None

    status_code: Any = getattr(exception, "status_code", None)
    if not isinstance(status_code, int) or isinstance(status_code, bool):
        return None

    if status_code < 400 or status_code > 599:
        return None

    return status_code


class ErrorHandler:
    """
        Handles exceptions and converts them to REST error responses.
        
        The ErrorHandler provides a centralized mechanism for converting
        Python exceptions to standardized REST error responses. It supports:
        
        - A default mapping for the framework's ValidationError; framework
          HTTP exceptions (NotFound, BadRequest, Forbidden, ...) carry
          their own status
        - Custom error mappings registered at runtime
        - Endpoint-specific error maps that override global mappings
        - Production mode error hiding for 500 errors
        - Error map inheritance with child overriding parent
        
        Attributes:
            debug: If False, internal error details are hidden for 500 errors.
            DEFAULT_MAPPINGS: Class-level default mappings: the framework's
                              own exceptions only.
    """
    
    # Only the framework's own exceptions are mapped by default. Built-in
    # exceptions such as ValueError, KeyError and PermissionError are not:
    # raised by accident anywhere under a handler (a failed int(), a missing
    # dict key, a file the server may not read) they are server bugs, and
    # mapped to 400/404/403 they were hidden from monitoring and sent the
    # exception text to the client. They fall back to 500; an application
    # that wants one mapped says so with error_map or register_mapping, or
    # raises NotFound, BadRequest or Forbidden. BUILTIN_EXCEPTION_MAPPINGS
    # holds the former mappings for an application that relies on them.
    DEFAULT_MAPPINGS: Dict[Type[Exception], ErrorMapping] = {
        ValidationError: ErrorMapping(
            status_code=400,
            error_code="validation_error",
            message_template="Request validation failed"
        ),
    }
    
    def __init__(self, debug: bool = False, builtin_mappings: bool = False):
        """
            Initialize an ErrorHandler.
            
            Args:
                debug: If True, include internal error details in 500 responses.
                       If False (production mode), hide internal error details.
                builtin_mappings: If True, also map ValueError, KeyError and
                                  PermissionError as BUILTIN_EXCEPTION_MAPPINGS
                                  does (the defaults up to 1.6.0).
        """
        self.debug = debug
        self._mappings: Dict[Type[Exception], ErrorMapping] = dict(self.DEFAULT_MAPPINGS)
        if builtin_mappings:
            self.register_builtin_mappings()

    def register_builtin_mappings(self) -> None:
        """
            Map ValueError to 400, KeyError to 404 and PermissionError to 403
            (BUILTIN_EXCEPTION_MAPPINGS), the defaults up to 1.6.0. A mapping
            already registered for one of these types is kept.

            For an application: ``app.rest_middleware.error_handler.register_builtin_mappings()``.
        """
        for exception_type, mapping in BUILTIN_EXCEPTION_MAPPINGS.items():
            if exception_type not in self._mappings:
                self._mappings[exception_type] = mapping
        return
    
    def register_mapping(
        self,
        exception_type: Type[Exception],
        mapping: ErrorMapping
    ) -> None:
        """
            Register a custom error mapping.
            
            This allows adding or overriding error mappings for specific
            exception types at runtime.
            
            Args:
                exception_type: The exception class to map.
                mapping: The ErrorMapping defining how to convert the exception.
        """
        self._mappings[exception_type] = mapping
    
    def handle(
        self,
        exception: Exception,
        endpoint_error_map: Optional[Dict[Type[Exception], ErrorMapping]] = None
    ) -> Tuple[RESTError, int]:
        """
            Handle an exception and return error response with status code.
            
            The error mapping lookup follows this priority:
            1. Endpoint-specific error_map (if provided)
            2. Global mappings registered with this handler
            3. The status and detail carried by a framework HTTP exception
               (``NotAcceptable`` -> 406, ``UnsupportedMediaType`` -> 415,
               the routing ``NotFound`` -> 404 and so on)
            4. Default fallback to 500 Internal Server Error
            
            For 500 errors in production mode (debug=False), internal error
            details are hidden to prevent information leakage.
            
            Args:
                exception: The caught exception to convert.
                endpoint_error_map: Optional endpoint-specific error mappings
                                    that take precedence over global mappings.
            
            Returns:
                Tuple of (RESTError, status_code) ready for response.
        """
        exception_type = type(exception)
        mapping: Optional[ErrorMapping] = None
        
        # Priority 1: Check endpoint-specific error_map first
        if endpoint_error_map is not None:
            # Check for exact type match
            if exception_type in endpoint_error_map:
                mapping = endpoint_error_map[exception_type]
            else:
                # Check for parent class matches in endpoint map
                for exc_type, exc_mapping in endpoint_error_map.items():
                    if isinstance(exception, exc_type):
                        mapping = exc_mapping
                        break
        
        # Priority 2: Check global mappings
        if mapping is None:
            # Check for exact type match
            if exception_type in self._mappings:
                mapping = self._mappings[exception_type]
            else:
                # Check for parent class matches in global mappings
                for exc_type, exc_mapping in self._mappings.items():
                    if isinstance(exception, exc_type):
                        mapping = exc_mapping
                        break
        
        # Priority 3: Framework HTTP exceptions carry their own status
        if mapping is None:
            http_status = get_http_exception_status(exception)
            if http_status is not None:
                return self._handle_http_exception(exception, http_status)

        # Priority 4: Fallback to 500 Internal Server Error
        if mapping is None:
            return self._handle_unhandled_exception(exception)
        
        # Build response using the mapping
        rest_error = mapping.build_response(exception)
        status_code = mapping.status_code
        
        # Apply production mode error hiding for 500 errors
        if status_code >= 500 and not self.debug:
            rest_error = self._hide_internal_details(rest_error)
        
        return rest_error, status_code
    
    def _handle_http_exception(self, exception: Exception, status_code: int) -> Tuple[RESTError, int]:
        """
            Convert a framework HTTP exception to a REST error using the
            status code and detail message it carries.

            Args:
                exception: The HTTP exception.
                status_code: The status code it carries (400-599).

            Returns:
                Tuple of (RESTError, status_code).
        """
        error_code = HTTP_STATUS_ERROR_CODES.get(status_code)
        if error_code is None:
            error_code = "http_{}".format(status_code)

        detail = getattr(exception, "detail", None)
        if detail is None or len(str(detail)) == 0:
            detail = str(exception)

        rest_error = RESTError(error=error_code, message=str(detail))

        if status_code >= 500 and not self.debug:
            rest_error = self._hide_internal_details(rest_error)

        return rest_error, status_code

    def _handle_unhandled_exception(self, exception: Exception) -> Tuple[RESTError, int]:
        """
            Handle an unhandled exception with 500 Internal Server Error.
            
            In debug mode, includes the exception details.
            In production mode, hides internal details.
            
            Args:
                exception: The unhandled exception.
            
            Returns:
                Tuple of (RESTError, 500).
        """
        if self.debug:
            # Include exception details in debug mode
            rest_error = RESTError(
                error="internal_error",
                message=str(exception),
                details={
                    "exception_type": type(exception).__name__,
                    "exception_message": str(exception)
                }
            )
        else:
            # Hide details in production mode
            rest_error = RESTError(
                error="internal_error",
                message="An internal error occurred"
            )
        
        return rest_error, 500
    
    def _hide_internal_details(self, rest_error: RESTError) -> RESTError:
        """
            Hide internal error details for production mode.
            
            Creates a new RESTError with generic message and no details
            to prevent information leakage in production.
            
            Args:
                rest_error: The original RESTError with details.
            
            Returns:
                New RESTError with hidden details.
        """
        return RESTError(
            error=rest_error.error,
            message="An internal error occurred"
        )


def merge_error_maps(
    parent_map: Optional[Dict[Type[Exception], ErrorMapping]],
    child_map: Optional[Dict[Type[Exception], ErrorMapping]]
) -> Dict[Type[Exception], ErrorMapping]:
    """
        Merge parent and child error maps with child override.
        
        This function implements error map inheritance where child mappings
        extend and override parent mappings. The resulting map contains
        all parent mappings plus all child mappings, with child mappings
        taking precedence for the same exception type.
        
        Args:
            parent_map: Parent endpoint's error map (or None).
            child_map: Child endpoint's error map (or None).
        
        Returns:
            Merged error map with child overrides.
    """
    result: Dict[Type[Exception], ErrorMapping] = {}
    
    # Start with parent mappings
    if parent_map is not None:
        result.update(parent_map)
    
    # Override with child mappings
    if child_map is not None:
        result.update(child_map)
    
    return result
