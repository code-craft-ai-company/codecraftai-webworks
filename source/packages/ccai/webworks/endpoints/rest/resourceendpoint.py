"""
.. module:: ccai.webworks.endpoints.rest.resourceendpoint
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Resource-oriented endpoint class providing CRUD operation helpers
               and automatic HTTP method to operation mapping.

.. moduleauthor:: Code Craft AI LLC
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []

import re

from typing import Any, Callable, Dict, List, Optional, Type, TYPE_CHECKING

from ccai.webworks.endpoints.constraints import EndpointConstraints
from ccai.webworks.endpoints.descriptor import (
    REST_MANAGED_EXTRA,
    REST_QUERY_PARAMS_EXTRA,
    REST_REQUEST_SCHEMA_TYPE_EXTRA,
    REST_RESPONSE_SCHEMA_TYPE_EXTRA,
    EndpointDescriptor,
    mark_handler
)
from ccai.webworks.endpoints.doc import Doc
from ccai.webworks.endpoints.restendpoint import RestEndpoint
from ccai.webworks.endpoints.rest.middleware import (
    RESTMiddleware,
    create_rest_middleware,
    get_rest_payload,
)
from ccai.webworks.endpoints.rest.models import ErrorMapping

if TYPE_CHECKING:
    from ccai.webworks.endpoints.router import Router


# Extracts the parameter name from a path parameter specification such as
# "{id}" or "{id:int}".
_ID_PARAM_PATTERN = re.compile(r"^\{(\w+)(?::\w+)?\}$")


# HTTP method to CRUD operation mapping
# This defines the standard REST convention for mapping HTTP verbs to operations
METHOD_TO_OPERATION: Dict[str, str] = {
    "GET": "get",
    "POST": "create",
    "PUT": "update",
    "PATCH": "partial_update",
    "DELETE": "delete",
}

# Default status codes by HTTP method
METHOD_STATUS_CODES: Dict[str, int] = {
    "GET": 200,
    "POST": 201,  # Created
    "PUT": 200,
    "PATCH": 200,
    "DELETE": 204,  # No Content
}

# All supported CRUD methods
ALL_CRUD_METHODS: List[str] = ["GET", "POST", "PUT", "PATCH", "DELETE"]


class ResourceEndpoint(RestEndpoint):
    """
        Resource-oriented endpoint providing CRUD operation helpers.
        
        ResourceEndpoint extends RestEndpoint with automatic mapping of HTTP
        methods to CRUD operations. It provides a consistent pattern for
        building RESTful APIs with standard operations:
        
        - GET → get(id) - Retrieve a single resource
        - POST → create(payload) - Create a new resource
        - PUT → update(id, payload) - Fully update a resource
        - PATCH → partial_update(id, payload) - Partially update a resource
        - DELETE → delete(id) - Delete a resource
        
        Subclasses should override the CRUD methods to implement their
        specific business logic.
        
        Class Attributes:
            resource_name: URL leaf segment for the resource (e.g., "users").
            id_param: Path parameter specification for single-resource operations.
                      Default is "{id:int}" for integer IDs.
            allowed_methods: List of HTTP methods to enable. Defaults to all CRUD
                             operations when not specified.
            request_schema: Schema type for request body deserialization.
            response_schema: Schema type for response body serialization.
            partial_update_schema: Optional schema for PATCH requests. If not
                                   specified, request_schema is used with partial=True.
            error_map: Mapping of exception types to ErrorMapping for custom
                       error handling.
            status_code: Override default status code for responses.
            debug_errors: If True, 500 responses include the exception
                          details. Leave False in production.
    """
    
    # Resource configuration
    resource_name: Optional[str] = None
    id_param: str = "{id:int}"
    allowed_methods: Optional[List[str]] = None
    
    # Schema configuration (inherited from RestEndpoint, redeclared for clarity)
    request_schema: Optional[Type] = None
    response_schema: Optional[Type] = None
    partial_update_schema: Optional[Type] = None
    
    # Error handling
    error_map: Dict[Type[Exception], ErrorMapping] = {}
    
    # Response configuration
    status_code: Optional[int] = None
    debug_errors: bool = False
    
    def get(self, id: Any) -> Any:
        """
            Retrieve a single resource by ID.
            
            Override this method in subclasses to implement resource retrieval.
            The method receives the resource identifier extracted from the URL
            path parameter.
            
            Args:
                id: Resource identifier from the path parameter.
            
            Returns:
                The resource object to be serialized and returned.
            
            Raises:
                NotImplementedError: If not overridden in subclass.
                NotFound: If the resource does not exist (subclass should raise).
        """
        raise NotImplementedError("Subclass must implement get()")
    
    def create(self, payload: Any) -> Any:
        """
            Create a new resource.
            
            Override this method in subclasses to implement resource creation.
            The method receives the deserialized request body as the payload.
            
            Args:
                payload: Deserialized request body matching request_schema.
            
            Returns:
                The created resource object to be serialized and returned.
            
            Raises:
                NotImplementedError: If not overridden in subclass.
                ValidationError: If the payload is invalid (subclass should raise).
        """
        raise NotImplementedError("Subclass must implement create()")
    
    def update(self, id: Any, payload: Any) -> Any:
        """
            Fully update an existing resource.
            
            Override this method in subclasses to implement full resource updates.
            The method receives the resource identifier and the complete new
            state of the resource.
            
            Args:
                id: Resource identifier from the path parameter.
                payload: Deserialized request body matching request_schema.
            
            Returns:
                The updated resource object to be serialized and returned.
            
            Raises:
                NotImplementedError: If not overridden in subclass.
                NotFound: If the resource does not exist (subclass should raise).
        """
        raise NotImplementedError("Subclass must implement update()")
    
    def partial_update(self, id: Any, payload: Any) -> Any:
        """
            Partially update an existing resource.
            
            Override this method in subclasses to implement partial resource
            updates. The method receives the resource identifier and only the
            fields to be updated.
            
            Args:
                id: Resource identifier from the path parameter.
                payload: Deserialized partial request body. Only fields present
                         in the payload should be updated. Validated against
                         request_schema, it is a dict of the fields the body
                         sent, by field name (a dataclass or Pydantic schema
                         alike); against partial_update_schema, an instance
                         of that schema.
            
            Returns:
                The updated resource object to be serialized and returned.
            
            Raises:
                NotImplementedError: If not overridden in subclass.
                NotFound: If the resource does not exist (subclass should raise).
        """
        raise NotImplementedError("Subclass must implement partial_update()")
    
    def delete(self, id: Any) -> None:
        """
            Delete a resource by ID.
            
            Override this method in subclasses to implement resource deletion.
            The method receives the resource identifier to delete.
            
            Args:
                id: Resource identifier from the path parameter.
            
            Returns:
                None. DELETE operations typically return 204 No Content.
            
            Raises:
                NotImplementedError: If not overridden in subclass.
                NotFound: If the resource does not exist (subclass should raise).
        """
        raise NotImplementedError("Subclass must implement delete()")
    
    def get_resource_url(self, resource: Any) -> Optional[str]:
        """
            Get the URL for a created resource (for Location header).
            
            Override this method to customize URL generation for the Location
            header returned after resource creation. The default implementation
            attempts to extract an 'id' attribute from the resource and
            construct a URL using the resource_name.
            
            Args:
                resource: The created resource object.
            
            Returns:
                URL string for the created resource, or None if the resource
                has no identifier or URL cannot be determined.
        """
        if resource is None:
            return None
        
        # Try to get the resource ID
        resource_id = None
        
        # Try common ID attribute names
        for attr_name in ('id', 'pk', 'identifier', 'resource_id'):
            if hasattr(resource, attr_name):
                resource_id = getattr(resource, attr_name)
                if resource_id is not None:
                    break
        
        # Try dict-like access
        if resource_id is None and hasattr(resource, '__getitem__'):
            for key in ('id', 'pk', 'identifier', 'resource_id'):
                try:
                    resource_id = resource[key]
                    if resource_id is not None:
                        break
                except (KeyError, TypeError):
                    # Probing: the resource has no such key (or is not keyed by strings); try the next candidate.
                    pass
        
        if resource_id is None:
            return None
        
        # Build the URL
        if self.resource_name:
            return f"/{self.resource_name}/{resource_id}"
        
        return None
    
    @classmethod
    def get_operation_for_method(cls, method: str) -> Optional[str]:
        """
            Get the CRUD operation name for an HTTP method.
            
            This method provides the mapping from HTTP methods to CRUD
            operation names according to REST conventions.
            
            Args:
                method: HTTP method string (e.g., "GET", "POST").
            
            Returns:
                Operation name (e.g., "get", "create") or None if the
                method is not a standard CRUD method.
        """
        return METHOD_TO_OPERATION.get(method.upper())
    
    @classmethod
    def get_method_for_operation(cls, operation: str) -> Optional[str]:
        """
            Get the HTTP method for a CRUD operation name.
            
            This method provides the reverse mapping from CRUD operation
            names to HTTP methods.
            
            Args:
                operation: Operation name (e.g., "get", "create").
            
            Returns:
                HTTP method string (e.g., "GET", "POST") or None if the
                operation is not a standard CRUD operation.
        """
        for method, op in METHOD_TO_OPERATION.items():
            if op == operation:
                return method
        return None
    
    @classmethod
    def get_default_status_code(cls, method: str) -> int:
        """
            Get the default HTTP status code for a method.
            
            Args:
                method: HTTP method string (e.g., "GET", "POST").
            
            Returns:
                Default status code for the method (e.g., 200, 201, 204).
        """
        return METHOD_STATUS_CODES.get(method.upper(), 200)

    @classmethod
    def get_partial_update_schema(cls) -> tuple:
        """
            Get the schema and partial flag for PATCH operations.

            This method determines which schema to use for partial updates:
            - If partial_update_schema is specified, use it with partial=False
            - Otherwise, use request_schema with partial=True

            Returns:
                A tuple of (schema, partial_flag) where:
                - schema: The schema type to use for validation
                - partial_flag: Whether to use partial validation mode

            Note:
                If neither partial_update_schema nor request_schema is set,
                returns (None, False).
        """
        if cls.partial_update_schema is not None:
            # Use the dedicated partial update schema with full validation
            return (cls.partial_update_schema, False)
        elif cls.request_schema is not None:
            # Use the request schema with partial validation mode
            return (cls.request_schema, True)
        else:
            # No schema configured
            return (None, False)

    @classmethod
    def get_effective_allowed_methods(cls) -> List[str]:
        """
            Get the effective list of allowed HTTP methods.
            
            If allowed_methods is not specified (None), returns all CRUD
            methods. Otherwise, returns the configured allowed_methods.
            
            Returns:
                List of allowed HTTP method strings.
        """
        if cls.allowed_methods is None:
            return list(ALL_CRUD_METHODS)
        return list(cls.allowed_methods)
    
    @classmethod
    def create_middleware(cls) -> RESTMiddleware:
        """
            Create the REST middleware that processes this resource's
            requests: content negotiation, request validation, response
            serialization, status code selection and the REST error model.

            Override to supply custom serializers, a custom validator or
            application-wide error mappings.

            Returns:
                The RESTMiddleware the generated route handlers run inside.
        """
        rtnval = create_rest_middleware(debug=cls.debug_errors)
        return rtnval

    @classmethod
    def get_id_param_name(cls) -> str:
        """
            Get the name of the path parameter that carries the resource
            identifier, taken from ``id_param`` (``"{id:int}"`` -> ``"id"``).

            Returns:
                The path parameter name.

            Raises:
                ValueError: If ``id_param`` is not a single path parameter
                            placeholder.
        """
        match = _ID_PARAM_PATTERN.match(cls.id_param)
        if match is None:
            raise ValueError(
                f"{cls.__name__}.id_param must be a path parameter such as "
                f"'{{id}}' or '{{id:int}}', got '{cls.id_param}'"
            )

        rtnval = match.group(1)
        return rtnval

    @classmethod
    def build_route_constraints(cls) -> EndpointConstraints:
        """
            Build the constraints every route of this resource carries,
            from the class's access policy and rate limit.

            Returns:
                The EndpointConstraints for the resource's routes.
        """
        rtnval = EndpointConstraints(
            access_policy=cls.access_policy,
            rate_limit=cls.rate_limit,
            scopes=cls.access_policy.scopes if cls.access_policy else [],
            roles=cls.access_policy.roles if cls.access_policy else []
        )
        return rtnval

    @classmethod
    def build_route_extras(
        cls,
        with_request_schema: bool = True,
        with_response_schema: bool = True,
        query_params: Optional[Dict[str, Type]] = None
    ) -> Dict[str, Any]:
        """
            Build the ``extras`` of a route descriptor for this resource.

            The route is stamped as a REST endpoint whose handler runs the
            REST processing pipeline, and carries the resource's schemas
            both as inspected JSON schema (for documentation) and as the
            schema classes (for validation and OpenAPI components).

            Args:
                with_request_schema: Include the request schema. False for
                                     routes that take no body, or a body of
                                     another shape.
                with_response_schema: Include the response schema. False for
                                      routes whose response has another shape.
                query_params: Query parameters the route reads, as a mapping
                              of name to Python type.

            Returns:
                A new extras dictionary.
        """
        rest_extras: Dict[str, Any] = {REST_MANAGED_EXTRA: True}

        if with_request_schema and cls.request_schema is not None:
            rest_extras["request_schema"] = cls._inspect_rest_schema(cls.request_schema)
            rest_extras[REST_REQUEST_SCHEMA_TYPE_EXTRA] = cls.request_schema

        if with_response_schema and cls.response_schema is not None:
            rest_extras["response_schema"] = cls._inspect_rest_schema(cls.response_schema)
            rest_extras[REST_RESPONSE_SCHEMA_TYPE_EXTRA] = cls.response_schema

        if query_params is not None and len(query_params) > 0:
            rest_extras[REST_QUERY_PARAMS_EXTRA] = dict(query_params)

        rtnval: Dict[str, Any] = {
            "endpoint_type": "rest",
            "rest": rest_extras,
        }
        return rtnval

    @classmethod
    def build_route(
        cls,
        instance: "ResourceEndpoint",
        middleware: RESTMiddleware,
        operation: Callable[[Any], Any],
        name: str,
        path: str,
        methods: List[str],
        summary: str,
        extras: Dict[str, Any]
    ) -> EndpointDescriptor:
        """
            Build the descriptor for one route of this resource.

            ``operation`` is written against the resource (it reads the
            path parameter, the query string and the validated payload from
            the request and calls a CRUD method). It is wrapped so that the
            route's handler has the shape the dispatcher calls -- it takes
            the request and returns a response -- with REST processing
            applied around the operation.

            Args:
                instance: The resource endpoint instance the route serves.
                middleware: The REST middleware to run the operation inside.
                operation: Callable taking the request and returning the
                           operation's result.
                name: Name for the generated handler, used in documentation
                      and diagnostics.
                path: URL path pattern of the route.
                methods: HTTP methods of the route.
                summary: One-line summary for documentation.
                extras: The descriptor extras (see :meth:`build_route_extras`).

            Returns:
                The EndpointDescriptor for the route.
        """
        operation.__name__ = name
        operation.__module__ = cls.__module__

        handler = middleware.wrap_handler(operation, endpoint=instance)

        descriptor = EndpointDescriptor(
            handler=handler,
            module=cls.__module__,
            leaf=None,
            path=path,
            methods=list(methods),
            version=cls.version,
            tags=list(cls.tags),
            constraints=cls.build_route_constraints(),
            doc=Doc(summary=summary),
            extras=extras
        )

        # The handler needs the descriptor to find the route's schemas, and
        # the descriptor needs the handler to be built.
        handler.descriptor = descriptor

        return descriptor

    @classmethod
    def build_routes(
        cls,
        instance: "ResourceEndpoint",
        middleware: RESTMiddleware
    ) -> List[EndpointDescriptor]:
        """
            Build the descriptors for this resource's CRUD routes.

            Two routes are built, according to ``allowed_methods``:

            1. Collection route: /{resource_name} for POST (create)
            2. Item route: /{resource_name}/{id_param} for GET, PUT, PATCH, DELETE

            Subclasses extend this to add routes of their own.

            Args:
                instance: The resource endpoint instance the routes serve.
                middleware: The REST middleware to run the operations inside.

            Returns:
                List of EndpointDescriptor objects, one per route.
        """
        descriptors: List[EndpointDescriptor] = []
        allowed = [method.upper() for method in cls.get_effective_allowed_methods()]
        resource_title = cls.resource_name.replace("_", " ").replace("-", " ").title()

        # Collection route for POST (create)
        if "POST" in allowed:
            def create_operation(request: Any) -> Any:
                return instance.create(get_rest_payload(request))

            descriptors.append(cls.build_route(
                instance=instance,
                middleware=middleware,
                operation=create_operation,
                name=f"create_{cls.resource_name}",
                path=f"/{cls.resource_name}",
                methods=["POST"],
                summary=f"Create {resource_title}",
                extras=cls.build_route_extras()
            ))

        # Item route for GET, PUT, PATCH, DELETE
        item_methods = [m for m in allowed if m in ["GET", "PUT", "PATCH", "DELETE"]]

        if len(item_methods) > 0:
            id_name = cls.get_id_param_name()

            def item_operation(request: Any) -> Any:
                resource_id = request.path_params[id_name]
                operation_name = METHOD_TO_OPERATION.get(str(request.method).upper())
                if operation_name == "get":
                    return instance.get(resource_id)
                elif operation_name == "update":
                    return instance.update(resource_id, get_rest_payload(request))
                elif operation_name == "partial_update":
                    return instance.partial_update(resource_id, get_rest_payload(request))
                elif operation_name == "delete":
                    return instance.delete(resource_id)
                else:
                    raise ValueError(f"Unknown operation for method: {request.method}")

            descriptors.append(cls.build_route(
                instance=instance,
                middleware=middleware,
                operation=item_operation,
                name=f"{cls.resource_name}_item",
                path=f"/{cls.resource_name}/{cls.id_param}",
                methods=item_methods,
                summary=f"{resource_title} item",
                extras=cls.build_route_extras()
            ))

        return descriptors

    @classmethod
    def register(cls, router: Optional["Router"] = None) -> List["EndpointDescriptor"]:
        """
            Register CRUD routes based on allowed_methods configuration.
            
            This method registers URL routes for the resource based on the
            configured allowed_methods. It creates two route patterns:
            
            1. Collection route: /{resource_name} for POST (create)
            2. Item route: /{resource_name}/{id_param} for GET, PUT, PATCH, DELETE

            Each route's handler takes the request, as the dispatcher calls
            it. It reads the resource identifier from the path parameters,
            validates the request body into ``request_schema`` (partially
            for PATCH, or against ``partial_update_schema``), calls the CRUD
            method, and returns a response with the serialized result, the
            status code for the method (201 with a Location header for a
            create, 204 for a delete) or a RESTError body when the
            operation raises.
            
            Args:
                router: Optional router to add the routes to. If not
                        provided, the descriptors are only returned; add
                        them to a registry with ``EndpointRegistry.register``.
            
            Returns:
                List of registered EndpointDescriptor objects.
            
            Raises:
                ValueError: If resource_name is not configured.
        """
        if not cls.resource_name:
            raise ValueError(
                f"{cls.__name__} must define resource_name for route registration"
            )

        # One endpoint instance and one middleware serve all the routes
        instance = cls()
        middleware = cls.create_middleware()

        descriptors = cls.build_routes(instance, middleware)

        for descriptor in descriptors:
            if router is not None:
                router.add_endpoint(descriptor)
            else:
                mark_handler(descriptor.handler, descriptor)

        return descriptors


# Export the mapping constants for external use
__all__ = [
    "ResourceEndpoint",
    "METHOD_TO_OPERATION",
    "METHOD_STATUS_CODES",
    "ALL_CRUD_METHODS",
]
