# Design Document: REST API Support

## Overview

This design document describes the architecture and implementation approach for the REST API Support feature. The feature provides resource-oriented helpers, serialization/validation infrastructure, and a standard REST error model to simplify building RESTful APIs on top of the endpoint abstractions framework.

Key design principles:
- Resource-oriented: CRUD operations follow REST conventions automatically
- Schema-driven: Request/response payloads are validated and serialized via schemas
- Consistent errors: All errors follow a standard structure for client reliability
- Extensible: Custom serializers, validators, and error mappings can be registered
- Composable: Builds on top of the endpoint-abstractions feature

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         REST API Support Layer                               │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                     ResourceEndpoint                                 │    │
│  │  - resource_name: str                                               │    │
│  │  - id_param: str = "{id:int}"                                       │    │
│  │  - allowed_methods: List[str]                                       │    │
│  │  - request_schema: Type                                             │    │
│  │  - response_schema: Type                                            │    │
│  │  - error_map: Dict[Type, ErrorMapping]                              │    │
│  │                                                                      │    │
│  │  Methods: get(), create(), update(), partial_update(), delete()     │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                              │                                               │
│                              ▼                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                     CollectionEndpoint                               │    │
│  │  - default_page_size: int = 20                                      │    │
│  │  - max_page_size: int = 100                                         │    │
│  │  - filter_fields: List[str]                                         │    │
│  │  - sort_fields: List[str]                                           │    │
│  │  - bulk_enabled: bool = False                                       │    │
│  │                                                                      │    │
│  │  Methods: list(), bulk_create(), bulk_update(), bulk_delete()       │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                    Serialization/Validation Pipeline                         │
│                                                                              │
│  Request Flow:                                                               │
│  ┌──────────┐    ┌──────────────┐    ┌───────────┐    ┌─────────┐          │
│  │ Raw Body │ -> │ Deserializer │ -> │ Validator │ -> │ Handler │          │
│  └──────────┘    └──────────────┘    └───────────┘    └─────────┘          │
│                                                                              │
│  Response Flow:                                                              │
│  ┌─────────┐    ┌────────────┐    ┌──────────────┐    ┌──────────┐         │
│  │ Handler │ -> │ Serializer │ -> │ Status Code  │ -> │ Response │         │
│  └─────────┘    └────────────┘    └──────────────┘    └──────────┘         │
│                                                                              │
│  Content Negotiation:                                                        │
│  ┌────────────────┐    ┌───────────────────┐    ┌──────────────────┐       │
│  │ Accept Header  │ -> │ SerializerRegistry│ -> │ Selected Format  │       │
│  └────────────────┘    └───────────────────┘    └──────────────────┘       │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                         Error Handling Flow                                  │
│                                                                              │
│  ┌───────────────┐                                                          │
│  │   Exception   │                                                          │
│  └───────┬───────┘                                                          │
│          │                                                                   │
│          ▼                                                                   │
│  ┌───────────────────────────────────────────────────────────────────┐     │
│  │                      Error Handler                                 │     │
│  │  1. Check endpoint error_map                                      │     │
│  │  2. Check global error_map                                        │     │
│  │  3. Fall back to default handling                                 │     │
│  └───────────────────────────────────────────────────────────────────┘     │
│          │                                                                   │
│          ▼                                                                   │
│  ┌───────────────────────────────────────────────────────────────────┐     │
│  │                      RESTError Response                            │     │
│  │  {                                                                 │     │
│  │    "error": "validation_error",                                   │     │
│  │    "message": "Request validation failed",                        │     │
│  │    "details": {...},                                              │     │
│  │    "field_errors": [                                              │     │
│  │      {"field": "email", "code": "invalid", "message": "..."}     │     │
│  │    ]                                                              │     │
│  │  }                                                                 │     │
│  └───────────────────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Components and Interfaces

### ResourceEndpoint Class

```python
class ResourceEndpoint(RestEndpoint):
    """
    Resource-oriented endpoint providing CRUD operation helpers.
    Automatically maps HTTP methods to resource operations.
    """
    
    # Class attributes for configuration
    resource_name: str = None  # URL leaf, e.g., "users"
    id_param: str = "{id:int}"  # Path parameter for single resource
    allowed_methods: List[str] = ["GET", "POST", "PUT", "PATCH", "DELETE"]
    request_schema: Type = None  # Schema for request body
    response_schema: Type = None  # Schema for response body
    partial_update_schema: Type = None  # Schema for PATCH (optional)
    error_map: Dict[Type[Exception], "ErrorMapping"] = {}
    status_code: int = None  # Override default status code
    
    def get(self, id: Any) -> Any:
        """
        Retrieve a single resource by ID.
        Override in subclass to implement.
        
        Args:
            id: Resource identifier from path parameter.
        
        Returns:
            Resource object to be serialized.
        
        Raises:
            NotFound: If resource does not exist.
        """
        raise NotImplementedError("Subclass must implement get()")
    
    def create(self, payload: Any) -> Any:
        """
        Create a new resource.
        Override in subclass to implement.
        
        Args:
            payload: Deserialized request body.
        
        Returns:
            Created resource object.
        """
        raise NotImplementedError("Subclass must implement create()")
    
    def update(self, id: Any, payload: Any) -> Any:
        """
        Fully update an existing resource.
        Override in subclass to implement.
        
        Args:
            id: Resource identifier from path parameter.
            payload: Deserialized request body.
        
        Returns:
            Updated resource object.
        """
        raise NotImplementedError("Subclass must implement update()")
    
    def partial_update(self, id: Any, payload: Any) -> Any:
        """
        Partially update an existing resource.
        Override in subclass to implement.
        
        Args:
            id: Resource identifier from path parameter.
            payload: Deserialized partial request body.
        
        Returns:
            Updated resource object.
        """
        raise NotImplementedError("Subclass must implement partial_update()")
    
    def delete(self, id: Any) -> None:
        """
        Delete a resource by ID.
        Override in subclass to implement.
        
        Args:
            id: Resource identifier from path parameter.
        """
        raise NotImplementedError("Subclass must implement delete()")
    
    def get_resource_url(self, resource: Any) -> Optional[str]:
        """
        Get the URL for a created resource (for Location header).
        Override to customize URL generation.
        
        Args:
            resource: The created resource object.
        
        Returns:
            URL string or None if no identifier.
        """
        pass
    
    @classmethod
    def register(cls, router: Optional["Router"] = None) -> List["EndpointDescriptor"]:
        """
        Register CRUD routes based on allowed_methods.
        
        Args:
            router: Optional router to register with.
        
        Returns:
            List of registered EndpointDescriptor objects.
        """
        pass
```

### CollectionEndpoint Class

```python
class CollectionEndpoint(ResourceEndpoint):
    """
    Collection-oriented endpoint with pagination, filtering, and sorting.
    Extends ResourceEndpoint with list and bulk operations.
    """
    
    # Pagination configuration
    default_page_size: int = 20
    max_page_size: int = 100
    
    # Filtering and sorting
    filter_fields: List[str] = []  # Allowed filter field names
    sort_fields: List[str] = []  # Allowed sort field names
    
    # Bulk operations
    bulk_enabled: bool = False
    atomic_bulk: bool = False  # Rollback all on any failure
    
    def list(
        self,
        page: int = 1,
        page_size: int = None,
        filters: Dict[str, Any] = None,
        sort: List[str] = None
    ) -> "PaginatedResponse":
        """
        List resources with pagination, filtering, and sorting.
        Override in subclass to implement.
        
        Args:
            page: Page number (1-indexed).
            page_size: Items per page.
            filters: Filter criteria from query params.
            sort: Sort fields with direction.
        
        Returns:
            PaginatedResponse with items and pagination info.
        """
        raise NotImplementedError("Subclass must implement list()")
    
    def bulk_create(self, payloads: List[Any]) -> "BulkOperationResult":
        """
        Create multiple resources in a single request.
        
        Args:
            payloads: List of deserialized request bodies.
        
        Returns:
            BulkOperationResult with per-item results.
        """
        raise NotImplementedError("Subclass must implement bulk_create()")
    
    def bulk_update(self, updates: List[Dict[str, Any]]) -> "BulkOperationResult":
        """
        Update multiple resources in a single request.
        
        Args:
            updates: List of {id, ...fields} update objects.
        
        Returns:
            BulkOperationResult with per-item results.
        """
        raise NotImplementedError("Subclass must implement bulk_update()")
    
    def bulk_delete(self, ids: List[Any]) -> "BulkOperationResult":
        """
        Delete multiple resources in a single request.
        
        Args:
            ids: List of resource identifiers.
        
        Returns:
            BulkOperationResult with per-item results.
        """
        raise NotImplementedError("Subclass must implement bulk_delete()")
```

### Serialization Classes

```python
class Serializer(Protocol):
    """
    Protocol for response serializers.
    """
    
    content_type: str  # MIME type, e.g., "application/json"
    
    def serialize(self, data: Any, schema: Optional[Type] = None) -> bytes:
        """
        Serialize data to wire format.
        
        Args:
            data: Python object to serialize.
            schema: Optional schema for type hints.
        
        Returns:
            Serialized bytes.
        """
        ...


class Deserializer(Protocol):
    """
    Protocol for request deserializers.
    """
    
    content_type: str  # MIME type, e.g., "application/json"
    
    def deserialize(self, data: bytes, schema: Type) -> Any:
        """
        Deserialize wire format to Python object.
        
        Args:
            data: Raw bytes from request body.
            schema: Target schema type.
        
        Returns:
            Deserialized object.
        
        Raises:
            ValidationError: If deserialization fails.
        """
        ...


class JSONSerializer:
    """
    JSON serializer supporting dataclasses and Pydantic models.
    """
    
    content_type = "application/json"
    
    def serialize(self, data: Any, schema: Optional[Type] = None) -> bytes:
        """
        Serialize to JSON bytes.
        
        Handles:
        - dict: Direct JSON encoding
        - dataclass: Convert to dict via asdict()
        - Pydantic model: Use model_dump()
        - list: Serialize each item
        """
        pass


class JSONDeserializer:
    """
    JSON deserializer supporting dataclasses and Pydantic models.
    """
    
    content_type = "application/json"
    
    def deserialize(self, data: bytes, schema: Type) -> Any:
        """
        Deserialize JSON bytes to schema instance.
        
        Handles:
        - dict schema: Return parsed JSON dict
        - dataclass: Construct from parsed dict
        - Pydantic model: Use model_validate()
        
        Raises:
            ValidationError: On parse or type errors.
        """
        pass


class SerializerRegistry:
    """
    Registry of serializers/deserializers by content type.
    """
    
    def __init__(self):
        self._serializers: Dict[str, Serializer] = {}
        self._deserializers: Dict[str, Deserializer] = {}
    
    def register_serializer(self, serializer: Serializer) -> None:
        """Register a serializer for its content type."""
        pass
    
    def register_deserializer(self, deserializer: Deserializer) -> None:
        """Register a deserializer for its content type."""
        pass
    
    def get_serializer(self, content_type: str) -> Optional[Serializer]:
        """Get serializer for content type."""
        pass
    
    def get_deserializer(self, content_type: str) -> Optional[Deserializer]:
        """Get deserializer for content type."""
        pass
    
    def negotiate_content_type(self, accept_header: str) -> Optional[str]:
        """
        Select best content type from Accept header.
        
        Args:
            accept_header: HTTP Accept header value.
        
        Returns:
            Selected content type or None if no match.
        """
        pass
```

### Validation Classes

```python
class Validator:
    """
    Schema validator supporting dataclasses and Pydantic models.
    """
    
    def validate(
        self,
        data: Any,
        schema: Type,
        partial: bool = False
    ) -> Any:
        """
        Validate data against schema.
        
        Args:
            data: Data to validate (usually dict from JSON).
            schema: Schema type to validate against.
            partial: If True, required fields are optional.
        
        Returns:
            Validated and coerced data.
        
        Raises:
            ValidationError: If validation fails.
        """
        pass
    
    def _validate_pydantic(
        self,
        data: Any,
        schema: Type,
        partial: bool
    ) -> Any:
        """Validate using Pydantic model."""
        pass
    
    def _validate_dataclass(
        self,
        data: Any,
        schema: Type,
        partial: bool
    ) -> Any:
        """Validate using dataclass fields."""
        pass


class ValidationError(Exception):
    """
    Exception raised when request validation fails.
    Contains field-level error details.
    """
    
    def __init__(
        self,
        message: str,
        field_errors: Optional[List["FieldError"]] = None
    ):
        self.message = message
        self.field_errors = field_errors or []
        super().__init__(message)


@dataclass
class FieldError:
    """
    Single field validation error.
    """
    
    field: str  # Field path, e.g., "user.email" for nested
    code: str  # Error code, e.g., "required", "invalid"
    message: str  # Human-readable message
```

### Error Handling Classes

```python
@dataclass
class RESTError:
    """
    Standard REST error response structure.
    """
    
    error: str  # Error code, e.g., "validation_error"
    message: str  # Human-readable description
    details: Optional[Dict[str, Any]] = None  # Additional context
    field_errors: Optional[List[FieldError]] = None  # Field-level errors
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for serialization."""
        result = {
            "error": self.error,
            "message": self.message
        }
        if self.details:
            result["details"] = self.details
        if self.field_errors:
            result["field_errors"] = [
                {"field": e.field, "code": e.code, "message": e.message}
                for e in self.field_errors
            ]
        return result


@dataclass
class ErrorMapping:
    """
    Mapping from exception type to HTTP error response.
    """
    
    status_code: int
    error_code: str
    message_template: Optional[str] = None  # Supports {attr} interpolation
    
    def build_response(self, exception: Exception) -> RESTError:
        """
        Build RESTError from exception using this mapping.
        
        Args:
            exception: The caught exception.
        
        Returns:
            RESTError with interpolated message.
        """
        pass


class ErrorHandler:
    """
    Handles exceptions and converts them to REST error responses.
    """
    
    # Default mappings for common exceptions
    DEFAULT_MAPPINGS: Dict[Type[Exception], ErrorMapping] = {
        ValueError: ErrorMapping(400, "bad_request"),
        KeyError: ErrorMapping(404, "not_found"),
        PermissionError: ErrorMapping(403, "forbidden"),
        ValidationError: ErrorMapping(400, "validation_error"),
    }
    
    def __init__(self, debug: bool = False):
        self.debug = debug
        self._mappings = dict(self.DEFAULT_MAPPINGS)
    
    def register_mapping(
        self,
        exception_type: Type[Exception],
        mapping: ErrorMapping
    ) -> None:
        """Register a custom error mapping."""
        pass
    
    def handle(
        self,
        exception: Exception,
        endpoint_error_map: Optional[Dict[Type[Exception], ErrorMapping]] = None
    ) -> Tuple[RESTError, int]:
        """
        Handle an exception and return error response with status code.
        
        Args:
            exception: The caught exception.
            endpoint_error_map: Endpoint-specific error mappings.
        
        Returns:
            Tuple of (RESTError, status_code).
        """
        pass
```

### Response Helper Classes

```python
@dataclass
class PaginationInfo:
    """
    Pagination metadata for collection responses.
    """
    
    total: int  # Total number of items
    page: int  # Current page (1-indexed)
    page_size: int  # Items per page
    total_pages: int  # Total number of pages
    
    # Navigation links
    next: Optional[str] = None  # URL to next page
    prev: Optional[str] = None  # URL to previous page
    first: Optional[str] = None  # URL to first page
    last: Optional[str] = None  # URL to last page
    
    @classmethod
    def create(
        cls,
        total: int,
        page: int,
        page_size: int,
        base_url: str
    ) -> "PaginationInfo":
        """
        Create PaginationInfo with computed fields and links.
        
        Args:
            total: Total item count.
            page: Current page number.
            page_size: Items per page.
            base_url: Base URL for navigation links.
        
        Returns:
            PaginationInfo with all fields populated.
        """
        pass


@dataclass
class PaginatedResponse:
    """
    Paginated collection response.
    """
    
    items: List[Any]  # Items for current page
    pagination: PaginationInfo  # Pagination metadata
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for serialization."""
        return {
            "items": self.items,
            "pagination": {
                "total": self.pagination.total,
                "page": self.pagination.page,
                "page_size": self.pagination.page_size,
                "total_pages": self.pagination.total_pages,
                "links": {
                    "next": self.pagination.next,
                    "prev": self.pagination.prev,
                    "first": self.pagination.first,
                    "last": self.pagination.last,
                }
            }
        }


@dataclass
class BulkOperationResult:
    """
    Result of a bulk operation with per-item status.
    """
    
    succeeded: List[Any]  # Successfully processed items
    failed: List["BulkItemError"]  # Failed items with errors
    
    @property
    def success_count(self) -> int:
        return len(self.succeeded)
    
    @property
    def failure_count(self) -> int:
        return len(self.failed)
    
    @property
    def all_succeeded(self) -> bool:
        return len(self.failed) == 0


@dataclass
class BulkItemError:
    """
    Error for a single item in a bulk operation.
    """
    
    index: int  # Index in the original request list
    item: Any  # The item that failed
    error: RESTError  # Error details
```

### Content Negotiation

```python
class ContentNegotiator:
    """
    Handles HTTP content negotiation for request/response formats.
    """
    
    def __init__(self, registry: SerializerRegistry):
        self.registry = registry
    
    def select_response_format(self, accept_header: Optional[str]) -> str:
        """
        Select response format from Accept header.
        
        Args:
            accept_header: HTTP Accept header value.
        
        Returns:
            Selected content type.
        
        Raises:
            NotAcceptable: If no supported format matches.
        """
        pass
    
    def validate_request_format(self, content_type: Optional[str]) -> str:
        """
        Validate request Content-Type is supported.
        
        Args:
            content_type: HTTP Content-Type header value.
        
        Returns:
            Validated content type.
        
        Raises:
            UnsupportedMediaType: If format not supported.
        """
        pass


class NotAcceptable(HTTPException):
    """406 Not Acceptable - requested format not supported."""
    
    def __init__(self, supported_types: List[str]):
        detail = f"Supported formats: {', '.join(supported_types)}"
        super().__init__(406, detail)


class UnsupportedMediaType(HTTPException):
    """415 Unsupported Media Type - request format not supported."""
    
    def __init__(self, content_type: str, supported_types: List[str]):
        detail = f"Unsupported Content-Type: {content_type}. Supported: {', '.join(supported_types)}"
        super().__init__(415, detail)
```

### Request/Response Middleware

```python
class RESTMiddleware:
    """
    Middleware that handles REST-specific request/response processing.
    
    Responsibilities:
    - Content negotiation
    - Request deserialization and validation
    - Response serialization
    - Error handling and formatting
    - Status code selection
    - Location header for created resources
    """
    
    name = "rest"
    
    def __init__(
        self,
        serializer_registry: SerializerRegistry,
        validator: Validator,
        error_handler: ErrorHandler
    ):
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
        
        1. Validate Content-Type and deserialize request body
        2. Call handler
        3. Serialize response and set headers
        4. Handle any errors
        """
        pass
    
    def _deserialize_request(
        self,
        request: "Request",
        descriptor: "EndpointDescriptor"
    ) -> Any:
        """Deserialize and validate request body."""
        pass
    
    def _serialize_response(
        self,
        data: Any,
        descriptor: "EndpointDescriptor",
        accept_header: Optional[str]
    ) -> Tuple[bytes, str]:
        """Serialize response data to wire format."""
        pass
    
    def _select_status_code(
        self,
        method: str,
        data: Any,
        descriptor: "EndpointDescriptor"
    ) -> int:
        """Select appropriate HTTP status code."""
        pass
    
    def _build_location_header(
        self,
        request: "Request",
        data: Any,
        endpoint: "ResourceEndpoint"
    ) -> Optional[str]:
        """Build Location header for created resources."""
        pass
```

## Data Models

### HTTP Method to CRUD Mapping

```python
# Default mapping of HTTP methods to CRUD operations
METHOD_TO_OPERATION = {
    "GET": "get",      # Retrieve (single or list)
    "POST": "create",  # Create new resource
    "PUT": "update",   # Full update
    "PATCH": "partial_update",  # Partial update
    "DELETE": "delete",  # Delete resource
}

# Default status codes by method
METHOD_STATUS_CODES = {
    "GET": 200,
    "POST": 201,  # Created
    "PUT": 200,
    "PATCH": 200,
    "DELETE": 204,  # No Content
}

# Status code for POST that doesn't create (action endpoints)
ACTION_POST_STATUS = 200
```

### Default Error Mappings

```python
# Default exception to HTTP error mappings
DEFAULT_ERROR_MAPPINGS = {
    ValidationError: ErrorMapping(
        status_code=400,
        error_code="validation_error",
        message_template="Request validation failed"
    ),
    ValueError: ErrorMapping(
        status_code=400,
        error_code="bad_request",
        message_template="{}"
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
    NotFound: ErrorMapping(
        status_code=404,
        error_code="not_found",
        message_template="{detail}"
    ),
    Unauthorized: ErrorMapping(
        status_code=401,
        error_code="unauthorized",
        message_template="{detail}"
    ),
    Forbidden: ErrorMapping(
        status_code=403,
        error_code="forbidden",
        message_template="{detail}"
    ),
}
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: HTTP Method to CRUD Operation Mapping

*For any* ResourceEndpoint and any HTTP method in allowed_methods, the method SHALL be correctly mapped to its corresponding CRUD operation (GET→get, POST→create, PUT→update, PATCH→partial_update, DELETE→delete).

**Validates: Requirements 1.2, 1.3, 1.7**

### Property 2: Request Deserialization Round-Trip

*For any* valid JSON request body and any schema (dataclass, Pydantic model, or dict), deserializing the JSON to a schema instance and then serializing it back to JSON SHALL produce equivalent JSON content.

**Validates: Requirements 3.1, 3.2, 3.3, 3.4**

### Property 3: Response Serialization Round-Trip

*For any* valid response object (dataclass, Pydantic model, dict, or list) and any schema, serializing to JSON and then deserializing back SHALL produce an equivalent object.

**Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5**

### Property 4: Validation Error Structure

*For any* validation failure, the raised ValidationError SHALL contain a list of FieldError objects where each error includes the field path, error code, and human-readable message.

**Validates: Requirements 5.4, 5.5**

### Property 5: Partial Update Field Preservation

*For any* PATCH request with a subset of fields, only the fields present in the request body SHALL be updated, and all other fields SHALL retain their original values.

**Validates: Requirements 11.2, 11.4**

### Property 6: Content Negotiation Selection

*For any* Accept header value, the content negotiator SHALL select the most appropriate supported format, or return 406 Not Acceptable if no format matches. *For any* missing Accept header, the system SHALL default to application/json.

**Validates: Requirements 6.1, 6.4, 6.5**

### Property 7: Error Response Status Code Mapping

*For any* exception type with a registered error mapping, the error handler SHALL return the mapped status code and error code. *For any* ValidationError, the response SHALL be 400 with field_errors populated. *For any* NotFound, the response SHALL be 404. *For any* unhandled exception, the response SHALL be 500.

**Validates: Requirements 7.3, 7.4, 7.5, 7.6, 7.7, 7.8, 8.1, 8.2**

### Property 8: HTTP Method to Status Code Mapping

*For any* successful request, the response status code SHALL match the HTTP method convention: GET→200, POST (create)→201, PUT→200, PATCH→200, DELETE→204. *For any* endpoint with a custom status_code attribute, that value SHALL override the default.

**Validates: Requirements 9.1, 9.2, 9.3, 9.4, 9.5**

### Property 9: Pagination Consistency

*For any* collection endpoint with total items T, page P, and page_size S, the PaginationInfo SHALL correctly compute total_pages as ceil(T/S), and the navigation links SHALL be valid URLs that return the correct pages when followed.

**Validates: Requirements 2.2, 2.3, 2.6**

### Property 10: Bulk Operation Results

*For any* bulk operation (create, update, delete) with N items, the BulkOperationResult SHALL contain exactly N results split between succeeded and failed lists, with each failed item including its index and error details.

**Validates: Requirements 12.1, 12.2, 12.3, 12.5, 12.6**

### Property 11: Location Header for Created Resources

*For any* POST request that creates a resource with an identifier, the response SHALL include a Location header containing a valid URL constructed from the resource endpoint path and the resource identifier.

**Validates: Requirements 10.1, 10.2, 10.4**

### Property 12: Error Map Inheritance

*For any* endpoint with a parent endpoint, the effective error_map SHALL be the parent's error_map merged with the child's error_map, where child mappings override parent mappings for the same exception type.

**Validates: Requirements 8.6**

## Error Handling

### Request Processing Errors

| Error Condition | HTTP Status | Error Code | Response |
|----------------|-------------|------------|----------|
| Malformed JSON | 400 | `parse_error` | RESTError with parse details |
| Schema validation failure | 400 | `validation_error` | RESTError with field_errors |
| Unsupported Content-Type | 415 | `unsupported_media_type` | RESTError with supported types |
| Unsupported Accept type | 406 | `not_acceptable` | RESTError with supported types |

### Resource Operation Errors

| Error Condition | HTTP Status | Error Code | Response |
|----------------|-------------|------------|----------|
| Resource not found | 404 | `not_found` | RESTError |
| Method not allowed | 405 | `method_not_allowed` | RESTError with Allow header |
| Authentication required | 401 | `unauthorized` | RESTError |
| Authorization denied | 403 | `forbidden` | RESTError |

### Server Errors

| Error Condition | HTTP Status | Error Code | Response |
|----------------|-------------|------------|----------|
| Unhandled exception | 500 | `internal_error` | RESTError (no details in production) |
| Serialization failure | 500 | `serialization_error` | RESTError |

## Testing Strategy

### Unit Tests

Unit tests verify specific examples and edge cases:

- ResourceEndpoint method availability and signatures
- Default allowed_methods behavior
- JSONSerializer/JSONDeserializer with various types
- Validator with valid and invalid data
- ErrorHandler with mapped and unmapped exceptions
- PaginationInfo computation
- ContentNegotiator Accept header parsing

### Property-Based Tests

Property-based tests verify universal properties across all inputs:

1. **Serialization Round-Trip**: For any valid schema instance, serialize then deserialize produces equivalent object
2. **Validation Error Completeness**: For any invalid input, all validation errors are captured
3. **Status Code Mapping**: For any HTTP method and success/failure, correct status code is returned
4. **Pagination Math**: For any total/page/page_size, pagination info is mathematically correct
5. **Error Map Merge**: For any parent/child error maps, merge produces correct effective map

### Test Configuration

- Property tests: Minimum 100 iterations per property
- Test framework: testbase (per repository conventions)
- Test location: `source/testroots/automojo/tests/singlehost/webworks/rest/`
