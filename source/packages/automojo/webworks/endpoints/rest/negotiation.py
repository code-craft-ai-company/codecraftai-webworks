"""
.. module:: automojo.webworks.endpoints.rest.negotiation
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Content negotiation infrastructure for REST API support.
               Handles HTTP Accept and Content-Type header processing.

.. moduleauthor:: Automation Mojo LLC
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []

from typing import Optional

from automojo.webworks.endpoints.rest.serialization import SerializerRegistry
from automojo.webworks.endpoints.rest.exceptions import (
    NotAcceptable,
    UnsupportedMediaType,
)


# Default content type when no Accept header is provided
DEFAULT_CONTENT_TYPE = "application/json"


class ContentNegotiator:
    """
        Handles HTTP content negotiation for request/response formats.
        
        The ContentNegotiator uses a SerializerRegistry to determine which
        content types are supported and selects the appropriate format based
        on HTTP Accept and Content-Type headers.
        
        Attributes:
            registry: SerializerRegistry containing available serializers/deserializers.
    """
    
    def __init__(self, registry: SerializerRegistry):
        """
            Initialize a ContentNegotiator.
            
            Args:
                registry: SerializerRegistry containing available serializers
                          and deserializers for content type negotiation.
        """
        self.registry = registry
    
    def select_response_format(self, accept_header: Optional[str]) -> str:
        """
            Select response format from Accept header.
            
            Parses the Accept header and selects the most appropriate supported
            content type based on quality values. If no Accept header is provided
            or is empty, defaults to application/json.
            
            Args:
                accept_header: HTTP Accept header value, or None if not provided.
            
            Returns:
                Selected content type string (e.g., "application/json").
            
            Raises:
                NotAcceptable: If no supported format matches the Accept header.
        """
        # Default to application/json when no Accept header is provided
        if accept_header is None or not accept_header.strip():
            return DEFAULT_CONTENT_TYPE
        
        # Use the registry to negotiate content type
        selected = self.registry.negotiate_content_type(accept_header)
        
        if selected is not None:
            return selected
        
        # No supported format matches - raise 406 Not Acceptable
        supported_types = self.registry.supported_content_types
        if not supported_types:
            # If no serializers registered, default to JSON
            supported_types = [DEFAULT_CONTENT_TYPE]
        
        raise NotAcceptable(supported_types)
    
    def validate_request_format(self, content_type: Optional[str]) -> str:
        """
            Validate request Content-Type is supported.
            
            Checks if the request's Content-Type header specifies a format
            that the server can deserialize. If no Content-Type is provided,
            defaults to application/json.
            
            Args:
                content_type: HTTP Content-Type header value, or None if not provided.
            
            Returns:
                Validated content type string (e.g., "application/json").
            
            Raises:
                UnsupportedMediaType: If the Content-Type is not supported.
        """
        # Default to application/json when no Content-Type is provided
        if content_type is None or not content_type.strip():
            return DEFAULT_CONTENT_TYPE
        
        # Extract base content type (remove parameters like charset)
        base_type = content_type.split(";")[0].strip().lower()
        
        # Check if we have a deserializer for this content type
        deserializer = self.registry.get_deserializer(base_type)
        
        if deserializer is not None:
            return base_type
        
        # Unsupported content type - raise 415 Unsupported Media Type
        supported_types = self.registry.supported_request_types
        if not supported_types:
            # If no deserializers registered, default to JSON
            supported_types = [DEFAULT_CONTENT_TYPE]
        
        raise UnsupportedMediaType(content_type, supported_types)
