"""
.. module:: automojo.webworks.endpoints.rest.exceptions
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Exception classes for REST API support.

.. moduleauthor:: Automation Mojo LLC
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []

from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from automojo.webworks.endpoints.rest.models import FieldError


class HTTPException(Exception):
    """
        Base class for HTTP-related exceptions.
        
        This exception class provides a base for HTTP error responses
        with a status code and detail message.
        
        Attributes:
            status_code: HTTP status code for the error response.
            detail: Human-readable description of the error.
    """
    
    def __init__(self, status_code: int, detail: str):
        """
            Initialize an HTTPException.
            
            Args:
                status_code: HTTP status code for the error response.
                detail: Human-readable description of the error.
        """
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


class NotAcceptable(HTTPException):
    """
        406 Not Acceptable - requested format not supported.
        
        This exception is raised when the client requests a response format
        (via Accept header) that the server cannot provide.
        
        Attributes:
            status_code: Always 406.
            detail: Description including supported formats.
            supported_types: List of content types the server supports.
    """
    
    def __init__(self, supported_types: List[str]):
        """
            Initialize a NotAcceptable exception.
            
            Args:
                supported_types: List of content types the server supports.
        """
        self.supported_types = supported_types
        detail = f"Supported formats: {', '.join(supported_types)}"
        super().__init__(406, detail)


class UnsupportedMediaType(HTTPException):
    """
        415 Unsupported Media Type - request format not supported.
        
        This exception is raised when the client sends a request body
        with a Content-Type that the server cannot process.
        
        Attributes:
            status_code: Always 415.
            detail: Description including the unsupported type and supported formats.
            content_type: The unsupported Content-Type from the request.
            supported_types: List of content types the server supports.
    """
    
    def __init__(self, content_type: str, supported_types: List[str]):
        """
            Initialize an UnsupportedMediaType exception.
            
            Args:
                content_type: The unsupported Content-Type from the request.
                supported_types: List of content types the server supports.
        """
        self.content_type = content_type
        self.supported_types = supported_types
        detail = f"Unsupported Content-Type: {content_type}. Supported: {', '.join(supported_types)}"
        super().__init__(415, detail)


class ValidationError(Exception):
    """
        Exception raised when request validation fails.
        
        This exception contains field-level error details that describe
        which fields failed validation and why. It is typically raised
        during request deserialization or schema validation.
        
        Attributes:
            message: Human-readable description of the validation failure.
            field_errors: List of FieldError objects describing individual
                          field validation failures.
    """
    
    def __init__(
        self,
        message: str,
        field_errors: Optional[List["FieldError"]] = None
    ):
        """
            Initialize a ValidationError.
            
            Args:
                message: Human-readable description of the validation failure.
                field_errors: Optional list of FieldError objects describing
                              individual field validation failures.
        """
        self.message = message
        self.field_errors = field_errors if field_errors is not None else []
        super().__init__(message)
