"""
.. module:: ccai.webworks.endpoints.rest.middleware
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: REST middleware that handles request/response processing including
               serialization, validation, error handling, and content negotiation.

.. moduleauthor:: Code Craft AI LLC
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []

import inspect
import logging

from typing import Any, Callable, Dict, Optional, Tuple, Type, TYPE_CHECKING

from ccai.webworks.endpoints.descriptor import (
    REST_REQUEST_SCHEMA_TYPE_EXTRA,
    REST_RESPONSE_SCHEMA_TYPE_EXTRA,
)
from ccai.webworks.endpoints.rest.serialization import JSONSerializer, SerializerRegistry
from ccai.webworks.endpoints.rest.validation import Validator
from ccai.webworks.endpoints.rest.errors import ErrorHandler, merge_error_maps
from ccai.webworks.endpoints.rest.negotiation import ContentNegotiator, DEFAULT_CONTENT_TYPE
from ccai.webworks.endpoints.rest.models import (
    ErrorMapping,
    select_status_code,
    build_location_header,
)
from ccai.webworks.endpoints.rest.exceptions import UnsupportedMediaType
from ccai.webworks.routing.response import Response


# Module-level logger. The REST middleware translates every
# uncaught exception into a structured JSON error via
# ``_handle_error``; without a log line the operator only sees
# the wire response and loses the underlying traceback.
logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from ccai.webworks.endpoints.descriptor import EndpointDescriptor
    from ccai.webworks.endpoints.rest.resourceendpoint import ResourceEndpoint
    from ccai.webworks.routing.request import Request


#: Attribute the validated request payload is stored under on a request
#: object that offers neither a ``payload`` nor a ``data`` attribute, such as
#: :class:`ccai.webworks.routing.request.Request`.
REST_PAYLOAD_ATTR = "_rest_payload"

#: Attribute set to True on every handler :meth:`RESTMiddleware.wrap_handler`
#: returns. A handler carrying it already runs the REST processing, so it is
#: never wrapped a second time (see :func:`is_rest_processed_handler`).
REST_PROCESSED_HANDLER_ATTR = "__webworks_rest_processed__"

# Marks "no payload was attached" apart from a payload that is None.
_NO_PAYLOAD = object()


def is_rest_processed_handler(handler: Any) -> bool:
    """
        Whether a handler already runs the REST processing: it is a handler
        :meth:`RESTMiddleware.wrap_handler` built.

        :param handler: The route handler.

        :returns: True when the handler is a REST processing wrapper.
    """
    rtnval = getattr(handler, REST_PROCESSED_HANDLER_ATTR, False) is True
    return rtnval


def is_coroutine_handler(handler: Any) -> bool:
    """
        Whether calling a handler returns a coroutine straight away.

        Looks through ``functools.wraps`` wrappers and at the ``__call__`` of
        callable objects, the way the dispatcher decides whether a handler
        runs on the event loop.

        :param handler: The route handler.

        :returns: True when the handler is a coroutine function.
    """
    rtnval = False

    try:
        unwrapped = inspect.unwrap(handler)
    except ValueError:
        unwrapped = handler

    if inspect.iscoroutinefunction(unwrapped):
        rtnval = True
    elif not inspect.isfunction(unwrapped) and not inspect.ismethod(unwrapped):
        call_method = getattr(unwrapped, "__call__", None)
        if call_method is not None and inspect.iscoroutinefunction(call_method):
            rtnval = True

    return rtnval


def get_rest_payload(request: Any, default: Any = None) -> Any:
    """
        The validated request payload :class:`RESTMiddleware` attached to a
        request.

        Args:
            request: The request object passed to the handler.
            default: Value to return when no payload was attached (the
                     request had no body, or its endpoint declares no
                     request schema).

        Returns:
            The validated payload -- an instance of the endpoint's request
            schema, or a dict of the supplied fields for a partial (PATCH)
            validation -- or ``default``.
    """
    payload = getattr(request, REST_PAYLOAD_ATTR, _NO_PAYLOAD)
    if payload is _NO_PAYLOAD:
        return default

    return payload


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

            The matched endpoint descriptor is read from the request (see
            :meth:`_get_endpoint_descriptor`).
            
            Args:
                request: The incoming HTTP request object.
                call_next: Callable to invoke the next handler in the chain.
            
            Returns:
                HTTP response object with serialized body and headers.
        """
        rtnval = self.process(request, call_next)
        return rtnval

    def wrap_handler(
        self,
        handler: Callable[[Any], Any],
        descriptor: Optional["EndpointDescriptor"] = None,
        endpoint: Optional["ResourceEndpoint"] = None
    ) -> Callable[[Any], Any]:
        """
            Build a request handler that runs ``handler`` inside the REST
            processing pipeline.

            The returned callable has the signature a router dispatches to --
            it takes the request and returns a response -- so REST processing
            can be applied to a single endpoint without installing the
            middleware for a whole application. ``handler`` receives the
            request with the validated payload attached (read it with
            :func:`get_rest_payload`) and returns plain data, a
            ``(data, status_code)`` tuple, or a finished response object,
            which is passed through untouched.

            The returned callable is a coroutine function when ``handler``
            is one, so the dispatcher runs it on the event loop; otherwise
            it is a plain function. It carries
            :data:`REST_PROCESSED_HANDLER_ATTR`, so it is never wrapped a
            second time.

            Args:
                handler: The endpoint handler to wrap.
                descriptor: The endpoint's descriptor, naming its request and
                            response schemas. May be attached later through
                            the ``descriptor`` attribute of the returned
                            callable, since a descriptor usually needs its
                            handler to be built first.
                endpoint: The resource endpoint instance the handler belongs
                          to, supplying ``status_code``, ``error_map`` and
                          ``get_resource_url``.

            Returns:
                A callable taking the request and returning the response.
        """
        middleware = self

        if is_coroutine_handler(handler):
            # An asynchronous handler gets an asynchronous wrapper, so the
            # dispatcher calls it on the event loop instead of moving it to
            # a worker thread, and the response is awaited there.
            async def rest_handler(request: Any) -> Any:
                result = middleware.process(
                    request,
                    handler,
                    descriptor=rest_handler.descriptor,
                    endpoint=endpoint
                )
                if inspect.isawaitable(result):
                    result = await result
                return result
        else:
            def rest_handler(request: Any) -> Any:
                result = middleware.process(
                    request,
                    handler,
                    descriptor=rest_handler.descriptor,
                    endpoint=endpoint
                )
                return result

        rest_handler.__name__ = getattr(handler, "__name__", "rest_handler")
        rest_handler.__qualname__ = getattr(handler, "__qualname__", rest_handler.__name__)
        rest_handler.__module__ = getattr(handler, "__module__", __name__)
        rest_handler.__doc__ = getattr(handler, "__doc__", None)
        rest_handler.descriptor = descriptor
        setattr(rest_handler, REST_PROCESSED_HANDLER_ATTR, True)

        return rest_handler

    def process(
        self,
        request: Any,
        call_next: Callable[[Any], Any],
        descriptor: Optional["EndpointDescriptor"] = None,
        endpoint: Optional["ResourceEndpoint"] = None
    ) -> Any:
        """
            Run one request through the REST processing pipeline.

            Args:
                request: The incoming HTTP request object.
                call_next: The handler (or next middleware) to call with the
                           request once its body has been validated.
                descriptor: The matched endpoint descriptor. Looked up on the
                            request when not given.
                endpoint: The resource endpoint instance serving the request.
                          Looked up on the request when not given.

            Returns:
                The HTTP response. When ``call_next`` is asynchronous this is
                an awaitable that produces the response.
        """
        if descriptor is None:
            descriptor = self._get_endpoint_descriptor(request)
        if endpoint is None:
            endpoint = self._get_endpoint(request)

        try:
            # Step 1: Content negotiation for response format
            accept_header = self._get_header(request, "Accept")
            response_content_type = self.negotiator.select_response_format(accept_header)
            
            # Step 2: Validate and deserialize request body if present
            if self._has_request_body(request):
                content_type = self._get_header(request, "Content-Type")
                self.negotiator.validate_request_format(content_type)
                
                # Deserialize request body
                request = self._deserialize_request(request, descriptor, endpoint=endpoint)
            elif self._requires_request_body(request, descriptor):
                # The endpoint declares a request schema and the request
                # carries no body: reject it here rather than hand the
                # handler a missing payload.
                self.validator.validate(None, self._get_request_schema(descriptor))
            
            # Step 3: Call the handler
            response = call_next(request)

            if inspect.isawaitable(response):
                # An asynchronous handler: the response is processed once
                # the caller awaits it.
                return self._process_awaitable(
                    request=request,
                    awaitable=response,
                    descriptor=descriptor,
                    response_content_type=response_content_type,
                    endpoint=endpoint
                )
            
            # Step 4: Process the response
            return self._process_response(
                request=request,
                response=response,
                descriptor=descriptor,
                response_content_type=response_content_type,
                endpoint=endpoint
            )
            
        except Exception as exc:
            # Step 5: Handle errors (see _handle_failure for the logging).
            return self._handle_failure(request, exc, descriptor=descriptor, endpoint=endpoint)

    async def _process_awaitable(
        self,
        request: Any,
        awaitable: Any,
        descriptor: Optional["EndpointDescriptor"],
        response_content_type: str,
        endpoint: Optional["ResourceEndpoint"]
    ) -> Any:
        """
            Finish processing for an asynchronous handler: await its result,
            then serialize it or convert the exception it raised.

            Args:
                request: The HTTP request object.
                awaitable: What the handler returned.
                descriptor: The endpoint descriptor.
                response_content_type: Content type for response.
                endpoint: The resource endpoint instance, if any.

            Returns:
                Processed HTTP response object.
        """
        try:
            response = await awaitable

            return self._process_response(
                request=request,
                response=response,
                descriptor=descriptor,
                response_content_type=response_content_type,
                endpoint=endpoint
            )

        except Exception as exc:
            return self._handle_failure(request, exc, descriptor=descriptor, endpoint=endpoint)

    def _handle_failure(
        self,
        request: Any,
        exception: Exception,
        descriptor: Optional["EndpointDescriptor"],
        endpoint: Optional[Any]
    ) -> Any:
        """
            Convert an exception raised while processing a request into its
            error response, and log it.

            A server error (5xx) is logged with its traceback, so the journal
            carries it even though the client only sees a clean
            ``RESTError`` body. A client error (4xx: an invalid body, an
            unsupported media type, a mapped domain exception) is the
            expected answer to a bad request and is logged at debug level
            only, as the dispatcher does for its 4xx responses.

            Must be called from the ``except`` block that caught the
            exception, so the logged traceback is its own.

            Args:
                request: The HTTP request object.
                exception: The exception that was raised.
                descriptor: The endpoint descriptor.
                endpoint: The resource endpoint instance, if any.

            Returns:
                The HTTP error response.
        """
        response = self._handle_error(request, exception, descriptor=descriptor, endpoint=endpoint)

        status_code = getattr(response, "status_code", 500)
        if status_code >= 500:
            logger.exception(
                "REST middleware: handler raised %s during request processing",
                type(exception).__name__,
            )
        else:
            logger.debug(
                "REST middleware: request answered %d (%s: %s)",
                status_code, type(exception).__name__, exception,
            )

        return response
    
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
    
    def _requires_request_body(
        self,
        request: Any,
        descriptor: Optional["EndpointDescriptor"]
    ) -> bool:
        """
            Check if the request must carry a body: its method takes one
            and the endpoint declares a request schema.

            Args:
                request: The HTTP request object.
                descriptor: The endpoint descriptor.

            Returns:
                True if a body is required, False otherwise.
        """
        method = self._get_method(request)
        if method not in ("POST", "PUT", "PATCH"):
            return False

        rtnval = self._get_request_schema(descriptor) is not None
        return rtnval
    
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

        # A routing Request carries the matched descriptor on its
        # middleware context, when the dispatcher has set one.
        middleware_context = getattr(request, 'middleware_context', None)
        if middleware_context is not None:
            return getattr(middleware_context, 'endpoint_descriptor', None)
        
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
        rtnval = self._get_schema_type(descriptor, REST_REQUEST_SCHEMA_TYPE_EXTRA, 'request_schema')
        return rtnval
    
    def _get_response_schema(self, descriptor: Optional["EndpointDescriptor"]) -> Optional[Type]:
        """
            Get the response schema from the endpoint descriptor.
            
            Args:
                descriptor: The endpoint descriptor.
            
            Returns:
                Response schema type or None.
        """
        rtnval = self._get_schema_type(descriptor, REST_RESPONSE_SCHEMA_TYPE_EXTRA, 'response_schema')
        return rtnval

    def _get_schema_type(
        self,
        descriptor: Optional["EndpointDescriptor"],
        type_key: str,
        schema_key: str
    ) -> Optional[Type]:
        """
            Get a schema class from the endpoint descriptor.

            ``attach_at`` records two things under ``extras["rest"]``: the
            inspected JSON-schema dict (for documentation) under
            ``schema_key`` and the schema class under ``type_key``. Only the
            class can validate or build an instance, so the class is what is
            returned. A descriptor built by hand may hold the class directly
            under ``schema_key``; that is accepted too. The inspected dict
            is never returned -- its ``"type"`` entry is the JSON type name
            ``"object"``, not a schema.

            Args:
                descriptor: The endpoint descriptor.
                type_key: Key in ``extras["rest"]`` holding the schema class.
                schema_key: Key in ``extras["rest"]`` holding the inspected
                            schema, and the name of the handler attribute to
                            fall back to.

            Returns:
                The schema class or None.
        """
        if descriptor is None:
            return None

        # Check extras for REST schema info
        extras = getattr(descriptor, 'extras', None)
        if isinstance(extras, dict):
            rest_extras = extras.get('rest')
            if isinstance(rest_extras, dict):
                schema_type = rest_extras.get(type_key)
                if isinstance(schema_type, type):
                    return schema_type

                schema_info = rest_extras.get(schema_key)
                if isinstance(schema_info, type):
                    return schema_info

        # Check handler for schema attribute
        handler = getattr(descriptor, 'handler', None)
        if handler is not None:
            handler_schema = getattr(handler, schema_key, None)
            if isinstance(handler_schema, type):
                return handler_schema

        return None
    
    def _get_endpoint_error_map(
        self,
        descriptor: Optional["EndpointDescriptor"],
        endpoint: Optional[Any] = None
    ) -> Optional[Dict[Type[Exception], ErrorMapping]]:
        """
            Get the error map from the endpoint, including inherited maps.
            
            Args:
                descriptor: The endpoint descriptor.
                endpoint: The endpoint instance serving the request, when
                          known. Otherwise it is looked for on the
                          descriptor's handler.
            
            Returns:
                Merged error map or None.
        """
        if descriptor is None and endpoint is None:
            return None
        
        if endpoint is None and hasattr(descriptor, 'handler'):
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
        
        merged_map = merge_error_maps(parent_map, child_map)

        # ``error_map`` has a second, older meaning on RestEndpoint: status
        # code to documentation schema. Only exception-to-ErrorMapping
        # entries describe how to convert an exception.
        rtnval: Dict[Type[Exception], ErrorMapping] = {}
        for exception_type, mapping in merged_map.items():
            if not isinstance(exception_type, type) or not issubclass(exception_type, BaseException):
                continue
            if not isinstance(mapping, ErrorMapping):
                continue
            rtnval[exception_type] = mapping

        return rtnval
    
    def _deserialize_request(
        self,
        request: Any,
        descriptor: Optional["EndpointDescriptor"],
        endpoint: Optional[Any] = None
    ) -> Any:
        """
            Deserialize and validate the request body.

            The body is parsed to plain data first and then validated into
            the schema exactly once. (It used to be deserialized into a
            schema instance and that instance then handed to the validator,
            which only accepts plain data and so rejected every valid body.)
            
            Args:
                request: The HTTP request object.
                descriptor: The endpoint descriptor.
                endpoint: The resource endpoint instance, if any. For a
                          PATCH request its partial-update schema is used.
            
            Returns:
                Request object with deserialized payload attached.
            
            Raises:
                ValidationError: If deserialization or validation fails.
        """
        method = self._get_method(request)
        schema = self._get_request_schema(descriptor)
        partial = method == "PATCH"

        if partial and endpoint is not None and hasattr(endpoint, 'get_partial_update_schema'):
            # A resource endpoint may name a dedicated schema for PATCH,
            # which is then validated in full.
            partial_schema, partial_flag = endpoint.get_partial_update_schema()
            if partial_schema is not None:
                schema = partial_schema
                partial = partial_flag

        if schema is None:
            # No schema, return request as-is
            return request
        
        # Parse the body to plain data
        parsed = self.read_body(request)
        
        # Validate the parsed data into the schema
        validated = self.validator.validate(parsed, schema, partial=partial)
        
        # Attach the validated payload to the request
        self._attach_payload(request, validated)
        
        return request

    def read_body(self, request: Any) -> Any:
        """
            Parse the request body to plain data (dicts, lists and scalars)
            using the deserializer registered for its Content-Type.

            Args:
                request: The HTTP request object.

            Returns:
                The parsed body.

            Raises:
                UnsupportedMediaType: If no deserializer handles the
                                      request's Content-Type.
                ValidationError: If the body cannot be parsed.
        """
        content_type = self._get_header(request, "Content-Type") or DEFAULT_CONTENT_TYPE
        base_type = content_type.split(";")[0].strip().lower()
        
        deserializer = self.serializer_registry.get_deserializer(base_type)
        if deserializer is None:
            raise UnsupportedMediaType(
                content_type,
                self.serializer_registry.supported_request_types
            )
        
        # ``object`` asks the deserializer for the parsed data as it is,
        # without building a schema instance from it.
        body = self._get_body(request)
        rtnval = deserializer.deserialize(body, object)

        return rtnval

    def _attach_payload(self, request: Any, payload: Any) -> None:
        """
            Attach the validated payload to the request for the handler.

            The payload is always readable with :func:`get_rest_payload`. A
            request object that offers a ``payload`` or ``data`` attribute
            also has it set there.

            Args:
                request: The HTTP request object.
                payload: The validated payload.
        """
        setattr(request, REST_PAYLOAD_ATTR, payload)

        if hasattr(request, 'payload'):
            request.payload = payload
        elif hasattr(request, 'data'):
            request.data = payload

        return
    
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
            serializer = JSONSerializer()
            content_type = "application/json"
        
        serialized = serializer.serialize(data, schema)
        return serialized, content_type
    
    def _process_response(
        self,
        request: Any,
        response: Any,
        descriptor: Optional["EndpointDescriptor"],
        response_content_type: str,
        endpoint: Optional[Any] = None
    ) -> Any:
        """
            Process and serialize the handler response.

            A handler (or the rest of a middleware chain) that returns a
            finished response object has already decided its status, headers
            and body; it is returned as it is. Anything else is response
            data: it is given a status code and serialized.
            
            Args:
                request: The HTTP request object.
                response: The handler response.
                descriptor: The endpoint descriptor.
                response_content_type: Content type for response.
                endpoint: The resource endpoint instance, if any. Looked up
                          on the request when not given.
            
            Returns:
                Processed HTTP response object.
        """
        if self._is_response_object(response):
            return response

        method = self._get_method(request)
        
        # Get status code override from endpoint
        status_code_override = None
        if endpoint is None:
            endpoint = self._get_endpoint(request)
        if endpoint is not None and hasattr(endpoint, 'status_code'):
            status_code_override = endpoint.status_code
        
        # Select status code
        data, status_code = select_status_code(method, response, status_code_override)

        if self._is_response_object(data):
            # (response, status) from a handler: the status wins
            data.status_code = status_code
            return data
        
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

    @staticmethod
    def _is_response_object(candidate: Any) -> bool:
        """
            Whether a handler result is a finished HTTP response rather than
            response data.

            Any object exposing ``status_code``, ``headers`` and ``body`` is
            a response: :class:`ccai.webworks.routing.response.Response` and
            its subclasses, and the template responses the dispatcher also
            accepts.

            Args:
                candidate: What the handler returned.

            Returns:
                True if the result is a response object.
        """
        if isinstance(candidate, Response):
            return True

        if isinstance(candidate, (dict, list, tuple, str, bytes)):
            return False

        rtnval = (hasattr(candidate, 'status_code')
                  and hasattr(candidate, 'headers')
                  and hasattr(candidate, 'body'))
        return rtnval
    
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
    
    def _handle_error(
        self,
        request: Any,
        exception: Exception,
        descriptor: Optional["EndpointDescriptor"] = None,
        endpoint: Optional[Any] = None
    ) -> Any:
        """
            Handle an exception and return an error response.
            
            Args:
                request: The HTTP request object.
                exception: The exception that occurred.
                descriptor: The endpoint descriptor. Looked up on the
                            request when not given.
                endpoint: The resource endpoint instance, if any.
            
            Returns:
                HTTP error response.
        """
        # Get endpoint error map
        if descriptor is None:
            descriptor = self._get_endpoint_descriptor(request)
        endpoint_error_map = self._get_endpoint_error_map(descriptor, endpoint=endpoint)
        
        # Handle the exception
        rest_error, status_code = self.error_handler.handle(
            exception,
            endpoint_error_map=endpoint_error_map
        )
        
        # Serialize the error response
        error_dict = rest_error.to_dict()
        
        serializer = JSONSerializer()
        body = serializer.serialize(error_dict)

        headers: Dict[str, str] = {"Content-Type": "application/json"}

        # An HTTP exception may carry headers the response must have, such
        # as the Allow header of a 405.
        exception_headers = getattr(exception, 'headers', None)
        if isinstance(exception_headers, dict):
            for header_name, header_value in exception_headers.items():
                headers[str(header_name)] = str(header_value)
        
        return self._create_response(
            body=body,
            status_code=status_code,
            content_type="application/json",
            headers=headers
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
            
            This method creates the :class:`ccai.webworks.routing.response.Response`
            the dispatcher and the ASGI layer send. Override in subclasses
            for integration with another framework.

            A response with a body always carries a Content-Type. A response
            without one (204 No Content, or a handler that returned nothing)
            carries none.
            
            Args:
                body: Response body as bytes.
                status_code: HTTP status code.
                content_type: Content-Type header value.
                headers: Additional response headers.
            
            Returns:
                HTTP response object.
        """
        response_headers: Dict[str, str] = dict(headers)

        has_content_type = False
        for header_name in response_headers:
            if header_name.lower() == "content-type":
                has_content_type = True
                break

        if len(body) > 0 and not has_content_type:
            response_headers["Content-Type"] = content_type

        rtnval = Response(
            status_code=status_code,
            headers=response_headers,
            body=body
        )

        return rtnval


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
    from ccai.webworks.endpoints.rest.serialization import create_default_registry

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
    "REST_PAYLOAD_ATTR",
    "REST_PROCESSED_HANDLER_ATTR",
    "RESTMiddleware",
    "create_rest_middleware",
    "get_rest_payload",
    "is_coroutine_handler",
    "is_rest_processed_handler",
]
