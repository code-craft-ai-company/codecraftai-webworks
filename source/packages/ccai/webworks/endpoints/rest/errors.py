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
from ccai.webworks.endpoints.rest.exceptions import ValidationError


class ErrorHandler:
    """
        Handles exceptions and converts them to REST error responses.
        
        The ErrorHandler provides a centralized mechanism for converting
        Python exceptions to standardized REST error responses. It supports:
        
        - Default mappings for common exceptions (ValueError, KeyError, etc.)
        - Custom error mappings registered at runtime
        - Endpoint-specific error maps that override global mappings
        - Production mode error hiding for 500 errors
        - Error map inheritance with child overriding parent
        
        Attributes:
            debug: If False, internal error details are hidden for 500 errors.
            DEFAULT_MAPPINGS: Class-level default mappings for common exceptions.
    """
    
    # Default mappings for common exceptions
    # These provide sensible defaults that can be overridden
    DEFAULT_MAPPINGS: Dict[Type[Exception], ErrorMapping] = {
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
        ValidationError: ErrorMapping(
            status_code=400,
            error_code="validation_error",
            message_template="Request validation failed"
        ),
    }
    
    def __init__(self, debug: bool = False):
        """
            Initialize an ErrorHandler.
            
            Args:
                debug: If True, include internal error details in 500 responses.
                       If False (production mode), hide internal error details.
        """
        self.debug = debug
        self._mappings: Dict[Type[Exception], ErrorMapping] = dict(self.DEFAULT_MAPPINGS)
    
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
            3. Default fallback to 500 Internal Server Error
            
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
        
        # Priority 3: Fallback to 500 Internal Server Error
        if mapping is None:
            return self._handle_unhandled_exception(exception)
        
        # Build response using the mapping
        rest_error = mapping.build_response(exception)
        status_code = mapping.status_code
        
        # Apply production mode error hiding for 500 errors
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
