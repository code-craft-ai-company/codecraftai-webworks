"""
.. module:: automojo.webworks.endpoints.rest.middleware
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: REST middleware that handles request/response processing including
               serialization, validation, error handling, and content negotiation.

.. moduleauthor:: Automation Mojo LLC
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []

import logging

from typing import Any, Callable, Dict, Optional, Tuple, Type, TYPE_CHECKING

from automojo.webworks.endpoints.rest.serialization import SerializerRegistry
from automojo.webworks.endpoints.rest.validation import Validator
from automojo.webworks.endpoints.rest.errors import ErrorHandler, merge_error_maps
from automojo.webworks.endpoints.rest.negotiation import ContentNegotiator, DEFAULT_CONTENT_TYPE
from automojo.webworks.endpoints.rest.models import (
    RESTError,
    ErrorMapping,
    select_status_code,
    build_location_header,
)
from automojo.webworks.endpoints.rest.exceptions import (
    HTTPException,
    NotAcceptable,
    UnsupportedMediaType,
    ValidationError,
)


# Module-level logger. The REST middleware translates every
# uncaught exception into a structured JSON error via
# ``_handle_error``; without a log line the operator only sees
# the wire response and loses the underlying traceback.
logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from automojo.webworks.endpoints.descriptor import EndpointDescriptor
    from automojo.webworks.endpoints.rest.resourceendpoint import ResourceEndpoint


class RESTMiddleware:
    """
        Middleware that handles REST-specific request/response processing.
        
        This middleware provides a complete REST processing pipeline including:
        
        - Content negotiation (Accept and Content-Type headers)
        - Request deserialization and validation
        - Response serialization
        - Error handling and formatting
        - Status code selection
        - Location header generation for created resources
        
        The middleware integrates SerializerRegistry, Validator, ErrorHandler,
        and ContentNegotiator to provide a cohesive REST API experience.
        
        Attributes:
            name: Middleware identifier, always "rest".
            serializer_registry: Registry of serializers/deserializers.
            validator: Schema validator for request validation.
            error_handler: Handler for converting exceptions to REST errors.
            negotiator: Content negotiator for format selection.
    """
    
    name: str = "rest"
    
    def __init__(
        self,
        serializer_registry: SerializerRegistry,
        validator: Validator,
        error_handler: ErrorHandler
    ):
        """
            Initialize the REST middleware.
            
            Args:
                serializer_registry: Registry containing serializers and
                                     deserializers for content type handling.
                validator: Validator for request body validation.
                error_handler: Handler for exception-to-error conversion.
        """
        self.serializer_registry = serializer_registry
        self.validator = validator
        self.error_handler = error_handler
        self.negotiator = ContentNegotiator(serializer_registry)
    
    def __call__(
        self,
        request: "Request",
        call_next: Callable[["Request"], "Response"]
    ) -> "Response":
        """
            Process REST request/response.
            
            This method implements the full REST processing pipeline:
            
            1. Validate Content-Type and deserialize request body
            2. Call the handler via call_next
            3. Serialize response and set headers
            4. Handle any errors that occur
            
            Args:
                request: The incoming HTTP request object.
                call_next: Callable to invoke the next handler in the chain.
            
            Returns:
                HTTP response object with serialized body and headers.
        """
        try:
            # Step 1: Content negotiation for response format
            accept_header = self._get_header(request, "Accept")
            response_content_type = self.negotiator.select_response_format(accept_header)
            
            # Step 2: Validate and deserialize request body if present
            descriptor = self._get_endpoint_descriptor(request)
            if self._has_request_body(request):
                content_type = self._get_header(request, "Content-Type")
                self.negotiator.validate_request_format(content_type)
                
                # Deserialize request body
                request = self._deserialize_request(request, descriptor)
            
            # Step 3: Call the handler
            response = call_next(request)
            
            # Step 4: Process the response
            return self._process_response(
                request=request,
                response=response,
                descriptor=descriptor,
                response_content_type=response_content_type
            )
            
        except Exception as exc:
            # Step 5: Handle errors. Log unconditionally so the
            # journal carries the traceback even when ``_handle_error``
            # returns a clean JSON error body to the client.
            logger.exception(
                "REST middleware: handler raised %s during request processing",
                type(exc).__name__,
            )
            return self._handle_error(request, exc)
    
    def _get_header(self, request: Any, header_name: str) -> Optional[str]:
        """
            Get a header value from the request.
            
            Args:
                request: The HTTP request object.
                header_name: Name of the header to retrieve.
            
            Returns:
                Header value or None if not present.
        """
        # Try common request object patterns
        if hasattr(request, 'headers'):
            headers = request.headers
            if isinstance(headers, dict):
                # Case-insensitive lookup
                for key, value in headers.items():
                    if key.lower() == header_name.lower():
                        return value
            elif hasattr(headers, 'get'):
                return headers.get(header_name)
        
        # Try get_header method
        if hasattr(request, 'get_header'):
            return request.get_header(header_name)
        
        return None
    
    def _get_method(self, request: Any) -> str:
        """
            Get the HTTP method from the request.
            
            Args:
                request: The HTTP request object.
            
            Returns:
                HTTP method string (e.g., "GET", "POST").
        """
        if hasattr(request, 'method'):
            return str(request.method).upper()
        return "GET"
    
    def _get_body(self, request: Any) -> bytes:
        """
            Get the request body as bytes.
            
            Args:
                request: The HTTP request object.
            
            Returns:
                Request body as bytes.
        """
        if hasattr(request, 'body'):
            body = request.body
            if isinstance(body, bytes):
                return body
            elif isinstance(body, str):
                return body.encode('utf-8')
        
        if hasattr(request, 'get_body'):
            return request.get_body()
        
        return b''
    
    def _has_request_body(self, request: Any) -> bool:
        """
            Check if the request has a body.
            
            Args:
                request: The HTTP request object.
            
            Returns:
                True if the request has a body, False otherwise.
        """
        method = self._get_method(request)
        # Only POST, PUT, PATCH typically have bodies
        if method not in ("POST", "PUT", "PATCH"):
            return False
        
        body = self._get_body(request)
        return len(body) > 0
    
    def _get_endpoint_descriptor(self, request: Any) -> Optional["EndpointDescriptor"]:
        """
            Get the endpoint descriptor from the request.
            
            Args:
                request: The HTTP request object.
            
            Returns:
                EndpointDescriptor or None if not available.
        """
        if hasattr(request, 'endpoint_descriptor'):
            return request.endpoint_descriptor
        
        if hasattr(request, 'descriptor'):
            return request.descriptor
        
        return None
    
    def _get_endpoint(self, request: Any) -> Optional["ResourceEndpoint"]:
        """
            Get the endpoint instance from the request.
            
            Args:
                request: The HTTP request object.
            
            Returns:
                ResourceEndpoint instance or None if not available.
        """
        if hasattr(request, 'endpoint'):
            return request.endpoint
        
        descriptor = self._get_endpoint_descriptor(request)
        if descriptor is not None and hasattr(descriptor, 'endpoint'):
            return descriptor.endpoint
        
        return None
    
    def _get_request_schema(self, descriptor: Optional["EndpointDescriptor"]) -> Optional[Type]:
        """
            Get the request schema from the endpoint descriptor.
            
            Args:
                descriptor: The endpoint descriptor.
            
            Returns:
                Request schema type or None.
        """
        if descriptor is None:
            return None
        
        # Check extras for REST schema info
        if hasattr(descriptor, 'extras') and descriptor.extras:
            rest_extras = descriptor.extras.get('rest', {})
            if 'request_schema' in rest_extras:
                schema_info = rest_extras['request_schema']
                if isinstance(schema_info, type):
                    return schema_info
                elif isinstance(schema_info, dict) and 'type' in schema_info:
                    return schema_info['type']
        
        # Check handler for schema attribute
        if hasattr(descriptor, 'handler'):
            handler = descriptor.handler
            if hasattr(handler, 'request_schema'):
                return handler.request_schema
        
        return None
    
    def _get_response_schema(self, descriptor: Optional["EndpointDescriptor"]) -> Optional[Type]:
        """
            Get the response schema from the endpoint descriptor.
            
            Args:
                descriptor: The endpoint descriptor.
            
            Returns:
                Response schema type or None.
        """
        if descriptor is None:
            return None
        
        # Check extras for REST schema info
        if hasattr(descriptor, 'extras') and descriptor.extras:
            rest_extras = descriptor.extras.get('rest', {})
            if 'response_schema' in rest_extras:
                schema_info = rest_extras['response_schema']
                if isinstance(schema_info, type):
                    return schema_info
                elif isinstance(schema_info, dict) and 'type' in schema_info:
                    return schema_info['type']
        
        # Check handler for schema attribute
        if hasattr(descriptor, 'handler'):
            handler = descriptor.handler
            if hasattr(handler, 'response_schema'):
                return handler.response_schema
        
        return None
    
    def _get_endpoint_error_map(
        self,
        descriptor: Optional["EndpointDescriptor"]
    ) -> Optional[Dict[Type[Exception], ErrorMapping]]:
        """
            Get the error map from the endpoint, including inherited maps.
            
            Args:
                descriptor: The endpoint descriptor.
            
            Returns:
                Merged error map or None.
        """
        if descriptor is None:
            return None
        
        endpoint = None
        if hasattr(descriptor, 'handler'):
            handler = descriptor.handler
            if hasattr(handler, 'error_map'):
                endpoint = handler
            elif hasattr(handler, '__self__') and hasattr(handler.__self__, 'error_map'):
                endpoint = handler.__self__
        
        if endpoint is None:
            return None
        
        # Get the endpoint's error map
        child_map = getattr(endpoint, 'error_map', None)
        
        # Check for parent endpoint and merge error maps
        parent_map = None
        if hasattr(endpoint, '__class__'):
            # Walk up the MRO to find parent error maps
            for base in endpoint.__class__.__mro__[1:]:
                if hasattr(base, 'error_map') and base.error_map:
                    parent_map = base.error_map
                    break
        
        return merge_error_maps(parent_map, child_map)
    
    def _deserialize_request(
        self,
        request: Any,
        descriptor: Optional["EndpointDescriptor"]
    ) -> Any:
        """
            Deserialize and validate the request body.
            
            Args:
                request: The HTTP request object.
                descriptor: The endpoint descriptor.
            
            Returns:
                Request object with deserialized payload attached.
            
            Raises:
                ValidationError: If deserialization or validation fails.
        """
        schema = self._get_request_schema(descriptor)
        if schema is None:
            # No schema, return request as-is
            return request
        
        # Get content type and deserializer
        content_type = self._get_header(request, "Content-Type") or DEFAULT_CONTENT_TYPE
        base_type = content_type.split(";")[0].strip().lower()
        
        deserializer = self.serializer_registry.get_deserializer(base_type)
        if deserializer is None:
            raise UnsupportedMediaType(
                content_type,
                self.serializer_registry.supported_request_types
            )
        
        # Deserialize the body
        body = self._get_body(request)
        deserialized = deserializer.deserialize(body, schema)
        
        # Validate the deserialized data
        method = self._get_method(request)
        partial = method == "PATCH"
        validated = self.validator.validate(deserialized, schema, partial=partial)
        
        # Attach the validated payload to the request
        if hasattr(request, 'payload'):
            request.payload = validated
        elif hasattr(request, 'data'):
            request.data = validated
        else:
            # Create a wrapper or set attribute
            request._rest_payload = validated
        
        return request
    
    def _serialize_response(
        self,
        data: Any,
        descriptor: Optional["EndpointDescriptor"],
        content_type: str
    ) -> Tuple[bytes, str]:
        """
            Serialize response data to wire format.
            
            Args:
                data: Response data to serialize.
                descriptor: The endpoint descriptor.
                content_type: Target content type.
            
            Returns:
                Tuple of (serialized bytes, content type).
        """
        schema = self._get_response_schema(descriptor)
        
        serializer = self.serializer_registry.get_serializer(content_type)
        if serializer is None:
            # Fall back to JSON
            from automojo.webworks.endpoints.rest.serialization import JSONSerializer
            serializer = JSONSerializer()
            content_type = "application/json"
        
        serialized = serializer.serialize(data, schema)
        return serialized, content_type
    
    def _process_response(
        self,
        request: Any,
        response: Any,
        descriptor: Optional["EndpointDescriptor"],
        response_content_type: str
    ) -> Any:
        """
            Process and serialize the handler response.
            
            Args:
                request: The HTTP request object.
                response: The handler response.
                descriptor: The endpoint descriptor.
                response_content_type: Content type for response.
            
            Returns:
                Processed HTTP response object.
        """
        method = self._get_method(request)
        
        # Get status code override from endpoint
        status_code_override = None
        endpoint = self._get_endpoint(request)
        if endpoint is not None and hasattr(endpoint, 'status_code'):
            status_code_override = endpoint.status_code
        
        # Select status code
        data, status_code = select_status_code(method, response, status_code_override)
        
        # Handle None response (e.g., DELETE)
        if data is None:
            return self._create_response(
                body=b'',
                status_code=status_code,
                content_type=response_content_type,
                headers={}
            )
        
        # Serialize the response
        body, content_type = self._serialize_response(data, descriptor, response_content_type)
        
        # Build headers
        headers: Dict[str, str] = {
            "Content-Type": content_type
        }
        
        # Add Location header for created resources
        if method == "POST" and status_code == 201:
            location = self._build_location_header(request, data, endpoint)
            if location is not None:
                headers["Location"] = location
        
        return self._create_response(
            body=body,
            status_code=status_code,
            content_type=content_type,
            headers=headers
        )
    
    def _build_location_header(
        self,
        request: Any,
        data: Any,
        endpoint: Optional["ResourceEndpoint"]
    ) -> Optional[str]:
        """
            Build the Location header for created resources.
            
            Args:
                request: The HTTP request object.
                data: The created resource data.
                endpoint: The resource endpoint.
            
            Returns:
                Location URL or None.
        """
        # Try to use endpoint's get_resource_url method
        get_url_func = None
        if endpoint is not None and hasattr(endpoint, 'get_resource_url'):
            get_url_func = endpoint.get_resource_url
        
        # Use the build_location_header helper
        location = build_location_header(
            method="POST",
            status_code=201,
            resource=data,
            get_resource_url_func=get_url_func
        )
        
        if location is None:
            return None
        
        # If location is just an ID, build full URL
        if not location.startswith('/') and not location.startswith('http'):
            # Get base path from request or endpoint
            base_path = self._get_base_path(request, endpoint)
            if base_path:
                location = f"{base_path}/{location}"
        
        return location
    
    def _get_base_path(self, request: Any, endpoint: Optional["ResourceEndpoint"]) -> str:
        """
            Get the base path for URL construction.
            
            Args:
                request: The HTTP request object.
                endpoint: The resource endpoint.
            
            Returns:
                Base path string.
        """
        # Try to get from endpoint
        if endpoint is not None and hasattr(endpoint, 'resource_name'):
            resource_name = endpoint.resource_name
            if resource_name:
                return f"/{resource_name}"
        
        # Try to get from request path
        if hasattr(request, 'path'):
            return str(request.path).rstrip('/')
        
        return ""
    
    def _handle_error(self, request: Any, exception: Exception) -> Any:
        """
            Handle an exception and return an error response.
            
            Args:
                request: The HTTP request object.
                exception: The exception that occurred.
            
            Returns:
                HTTP error response.
        """
        # Get endpoint error map
        descriptor = self._get_endpoint_descriptor(request)
        endpoint_error_map = self._get_endpoint_error_map(descriptor)
        
        # Handle the exception
        rest_error, status_code = self.error_handler.handle(
            exception,
            endpoint_error_map=endpoint_error_map
        )
        
        # Serialize the error response
        error_dict = rest_error.to_dict()
        
        from automojo.webworks.endpoints.rest.serialization import JSONSerializer
        serializer = JSONSerializer()
        body = serializer.serialize(error_dict)
        
        return self._create_response(
            body=body,
            status_code=status_code,
            content_type="application/json",
            headers={"Content-Type": "application/json"}
        )
    
    def _create_response(
        self,
        body: bytes,
        status_code: int,
        content_type: str,
        headers: Dict[str, str]
    ) -> Any:
        """
            Create an HTTP response object.
            
            This method creates a response object compatible with the
            framework being used. Override in subclasses for specific
            framework integration.
            
            Args:
                body: Response body as bytes.
                status_code: HTTP status code.
                content_type: Content-Type header value.
                headers: Additional response headers.
            
            Returns:
                HTTP response object.
        """
        # Return a simple response dict that can be adapted
        return {
            "body": body,
            "status_code": status_code,
            "content_type": content_type,
            "headers": headers
        }


def create_rest_middleware(
    debug: bool = False,
    serializer_registry: Optional[SerializerRegistry] = None
) -> RESTMiddleware:
    """
        Create a RESTMiddleware with default configuration.
        
        This factory function creates a fully configured RESTMiddleware
        with default serializers, validator, and error handler.
        
        Args:
            debug: If True, include error details in 500 responses.
            serializer_registry: Optional custom serializer registry.
                                 If not provided, creates a default registry
                                 with JSON support.
        
        Returns:
            Configured RESTMiddleware instance.
    """
    from automojo.webworks.endpoints.rest.serialization import create_default_registry
    
    if serializer_registry is None:
        serializer_registry = create_default_registry()
    
    validator = Validator()
    error_handler = ErrorHandler(debug=debug)
    
    return RESTMiddleware(
        serializer_registry=serializer_registry,
        validator=validator,
        error_handler=error_handler
    )


__all__ = [
    "RESTMiddleware",
    "create_rest_middleware",
]
