"""
.. module:: automojo.webworks.endpoints.rest.resourceendpoint
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Resource-oriented endpoint class providing CRUD operation helpers
               and automatic HTTP method to operation mapping.

.. moduleauthor:: Automation Mojo LLC
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []

from typing import Any, Dict, List, Optional, Type, TYPE_CHECKING

from automojo.webworks.endpoints.restendpoint import RestEndpoint
from automojo.webworks.endpoints.rest.models import ErrorMapping

if TYPE_CHECKING:
    from automojo.webworks.endpoints.descriptor import EndpointDescriptor
    from automojo.webworks.endpoints.router import Router


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
                         in the payload should be updated.
            
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
    def register(cls, router: Optional["Router"] = None) -> List["EndpointDescriptor"]:
        """
            Register CRUD routes based on allowed_methods configuration.
            
            This method registers URL routes for the resource based on the
            configured allowed_methods. It creates two route patterns:
            
            1. Collection route: /{resource_name} for POST (create)
            2. Item route: /{resource_name}/{id_param} for GET, PUT, PATCH, DELETE
            
            Args:
                router: Optional router to register with. If not provided,
                        uses the global EndpointRegistry.
            
            Returns:
                List of registered EndpointDescriptor objects.
            
            Raises:
                ValueError: If resource_name is not configured.
        """
        from automojo.webworks.endpoints.descriptor import EndpointDescriptor
        from automojo.webworks.endpoints.constraints import EndpointConstraints
        from automojo.webworks.endpoints.registry import EndpointRegistry
        
        if not cls.resource_name:
            raise ValueError(
                f"{cls.__name__} must define resource_name for route registration"
            )
        
        descriptors: List[EndpointDescriptor] = []
        allowed = cls.get_effective_allowed_methods()
        
        # Build constraints
        constraints = EndpointConstraints(
            access_policy=cls.access_policy,
            rate_limit=cls.rate_limit,
            scopes=cls.access_policy.scopes if cls.access_policy else [],
            roles=cls.access_policy.roles if cls.access_policy else []
        )
        
        # Build extras with REST schema info
        extras: Dict[str, Any] = {}
        rest_extras: Dict[str, Any] = {}
        
        if cls.request_schema is not None:
            rest_extras["request_schema"] = cls._inspect_rest_schema(cls.request_schema)
        
        if cls.response_schema is not None:
            rest_extras["response_schema"] = cls._inspect_rest_schema(cls.response_schema)
        
        if rest_extras:
            extras["rest"] = rest_extras
        
        # Collection route for POST (create)
        if "POST" in allowed:
            collection_path = f"/{cls.resource_name}"
            
            # Create a handler wrapper for create
            instance = cls()
            
            def create_handler(payload: Any) -> Any:
                return instance.create(payload)
            
            collection_descriptor = EndpointDescriptor(
                handler=create_handler,
                module=cls.__module__,
                leaf=None,
                path=collection_path,
                methods=["POST"],
                version=cls.version,
                tags=list(cls.tags),
                constraints=constraints,
                doc=None,
                extras=extras
            )
            
            if router is not None:
                router.add_route(collection_descriptor)
            else:
                EndpointRegistry.register(collection_descriptor)
            
            descriptors.append(collection_descriptor)
        
        # Item route for GET, PUT, PATCH, DELETE
        item_methods = [m for m in allowed if m in ["GET", "PUT", "PATCH", "DELETE"]]
        
        if item_methods:
            item_path = f"/{cls.resource_name}/{cls.id_param}"
            
            # Create a handler wrapper for item operations
            instance = cls()
            
            def item_handler(id: Any, method: str, payload: Any = None) -> Any:
                operation = METHOD_TO_OPERATION.get(method)
                if operation == "get":
                    return instance.get(id)
                elif operation == "update":
                    return instance.update(id, payload)
                elif operation == "partial_update":
                    return instance.partial_update(id, payload)
                elif operation == "delete":
                    return instance.delete(id)
                else:
                    raise ValueError(f"Unknown operation for method: {method}")
            
            item_descriptor = EndpointDescriptor(
                handler=item_handler,
                module=cls.__module__,
                leaf=None,
                path=item_path,
                methods=item_methods,
                version=cls.version,
                tags=list(cls.tags),
                constraints=constraints,
                doc=None,
                extras=extras
            )
            
            if router is not None:
                router.add_route(item_descriptor)
            else:
                EndpointRegistry.register(item_descriptor)
            
            descriptors.append(item_descriptor)
        
        return descriptors


# Export the mapping constants for external use
__all__ = [
    "ResourceEndpoint",
    "METHOD_TO_OPERATION",
    "METHOD_STATUS_CODES",
    "ALL_CRUD_METHODS",
]
