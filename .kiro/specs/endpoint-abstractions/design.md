# Design Document: Endpoint Abstractions

## Overview

This design document describes the architecture and implementation approach for the Endpoint Abstractions feature. The feature provides a declarative, composable system for defining HTTP endpoints with centralized access control, metadata, and routing configuration.

The design follows a hierarchical class structure where `Endpoint` serves as the base class, with specialized subclasses (`RestEndpoint`, `Blueprint`, `RestBlueprint`) adding domain-specific functionality. The `EndpointRegistry` collects all endpoint descriptors at import time, enabling routers and documentation generators to consume the full endpoint map without executing handlers.

Key design principles:
- Declarative over imperative: Endpoint metadata is captured at decoration time
- Composition over inheritance: Constraints flow from parent to child with predictable override rules
- Fail-fast validation: Registration errors are raised immediately at decoration time
- Testability: Blueprints can generate descriptors without a live router instance

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Endpoint Class Hierarchy                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                           Endpoint                                   │    │
│  │  - access_policy, rate_limit, serializers, metadata                 │    │
│  │  - attach_at(**bindings) -> decorator                               │    │
│  │  - attach_child(child, **kwargs) -> EndpointDescriptor              │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                    │                              │                          │
│         ┌─────────┴─────────┐          ┌────────┴────────┐                  │
│         ▼                   ▼          ▼                 ▼                  │
│  ┌─────────────┐    ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │
│  │  Blueprint  │    │RestEndpoint │  │   Custom    │  │   Custom    │      │
│  │             │    │             │  │  Endpoint   │  │  Endpoint   │      │
│  │ - register()│    │ - schemas   │  │  Subclass   │  │  Subclass   │      │
│  │ - base_path │    │ - CRUD      │  └─────────────┘  └─────────────┘      │
│  └─────────────┘    └─────────────┘                                         │
│         │                   │                                                │
│         └─────────┬─────────┘                                                │
│                   ▼                                                          │
│         ┌─────────────────┐                                                  │
│         │  RestBlueprint  │                                                  │
│         │                 │                                                  │
│         │ - add_crud()    │                                                  │
│         │ - register()    │                                                  │
│         └─────────────────┘                                                  │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                         Registration Flow                                    │
│                                                                              │
│  @Endpoint.attach_at(leaf="status")                                         │
│  def handler(): ...                                                          │
│         │                                                                    │
│         ▼                                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    EndpointDescriptor                                │    │
│  │  handler, module, leaf, path, methods, version, tags,               │    │
│  │  constraints: {access_policy, rate_limit, ...},                     │    │
│  │  doc: {summary, description}, extras: {rest: {...}}                 │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│         │                                                                    │
│         ▼                                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    EndpointRegistry                                  │    │
│  │  - _descriptors: List[EndpointDescriptor]                           │    │
│  │  - collect() -> List[EndpointDescriptor]                            │    │
│  │  - export_security_map(filter_tag) -> str                           │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│         │                                                                    │
│         ▼                                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                         Router                                       │    │
│  │  - add_endpoint(descriptor: EndpointDescriptor) -> None             │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                    Constraint Inheritance Flow                               │
│                                                                              │
│  Parent (Blueprint/Endpoint)                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  access_policy = AccessPolicy(roles=["user"])                       │    │
│  │  tags = ["api", "v1"]                                               │    │
│  │  rate_limit = RateLimit(requests=100, window=60)                    │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│         │                                                                    │
│         │ attach_child(child, tags=["admin"])                               │
│         ▼                                                                    │
│  Child Descriptor (merged)                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  access_policy = AccessPolicy(roles=["user"])  # inherited          │    │
│  │  tags = ["api", "v1", "admin"]                 # merged (default)   │    │
│  │  rate_limit = RateLimit(requests=100, window=60)  # inherited       │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Components and Interfaces

### Endpoint Base Class

```python
class Endpoint:
    """
    Base class providing a reusable container for endpoint constraints
    and metadata. Supports both direct attachment via attach_at() and
    hierarchical composition via attach_child().
    """
    
    # Class-level defaults that subclasses can override
    access_policy: Optional[AccessPolicy] = None
    rate_limit: Optional[RateLimit] = None
    methods: List[str] = ["GET"]
    version: Optional[str] = None
    tags: List[str] = []
    serializers: Dict[str, Any] = {}
    
    @classmethod
    def attach_at(
        cls,
        leaf: Optional[str] = None,
        path: Optional[str] = None,
        methods: Optional[List[str]] = None,
        version: Optional[str] = None,
        tags: Optional[List[str]] = None,
        access_policy: Optional[AccessPolicy] = None,
        rate_limit: Optional[RateLimit] = None,
        request_schema: Optional[Type] = None,
        response_schema: Optional[Type] = None,
        error_map: Optional[Dict[int, Type]] = None,
        doc: Optional[Doc] = None,
        on_conflict: str = "error",
        **extras
    ) -> Callable[[F], F]:
        """
        Decorator that binds a handler to an absolute URL location.
        
        Args:
            leaf: URL leaf segment (e.g., "status" -> /status)
            path: Full URL path (alternative to leaf)
            methods: HTTP methods (defaults to class attribute)
            version: API version string
            tags: Documentation tags
            access_policy: Security policy (defaults to class attribute)
            rate_limit: Rate limiting config (defaults to class attribute)
            request_schema: Request body schema (dataclass or Pydantic)
            response_schema: Response body schema
            error_map: Mapping of status codes to error schemas
            doc: Documentation object with summary/description
            on_conflict: "error" to raise on conflict, "replace" to override
            **extras: Additional kwargs stored in descriptor.extras
        
        Returns:
            Decorator that returns the original function unchanged.
        
        Raises:
            EndpointRegistrationError: If mandatory metadata missing or conflict.
        """
        pass
    
    @classmethod
    def attach_child(
        cls,
        child_endpoint: Type["Endpoint"],
        leaf: Optional[str] = None,
        path: Optional[str] = None,
        **kwargs
    ) -> EndpointDescriptor:
        """
        Attach a child endpoint relative to this endpoint's base path.
        
        Args:
            child_endpoint: The child endpoint class to attach.
            leaf: Override for child's leaf (relative to parent base).
            path: Override for child's path (relative to parent base).
            **kwargs: Additional overrides for child descriptor.
        
        Returns:
            The merged EndpointDescriptor for the child.
        """
        pass
```

### Blueprint Class

```python
class Blueprint(Endpoint):
    """
    Endpoint composite that emits multiple attachments in one declaration.
    Provides a shared parent path and constraint inheritance for grouped
    endpoints.
    """
    
    base_path: Optional[str] = None
    base_leaf: Optional[str] = None
    merge_tags: bool = False
    
    @classmethod
    def register(
        cls,
        router: Optional["Router"] = None
    ) -> List[EndpointDescriptor]:
        """
        Register all child endpoints and return their descriptors.
        
        Args:
            router: Optional router to add endpoints to. If None,
                   descriptors are returned without router registration.
        
        Returns:
            List of EndpointDescriptor objects for all registered endpoints.
        """
        pass
```

### RestEndpoint Class

```python
class RestEndpoint(Endpoint):
    """
    Endpoint subclass with REST-specific metadata for auto-generating
    API descriptions (OpenAPI paths, verbs, payload schemas).
    """
    
    request_schema: Optional[Type] = None
    response_schema: Optional[Type] = None
    error_map: Dict[int, Type] = {}
    summary: Optional[str] = None
    description: Optional[str] = None
    
    @classmethod
    def read(cls, **kwargs) -> Callable[[F], F]:
        """Helper for GET endpoints with pre-populated documentation."""
        return cls.attach_at(methods=["GET"], **kwargs)
    
    @classmethod
    def create(cls, **kwargs) -> Callable[[F], F]:
        """Helper for POST endpoints with pre-populated documentation."""
        return cls.attach_at(methods=["POST"], **kwargs)
    
    @classmethod
    def update(cls, **kwargs) -> Callable[[F], F]:
        """Helper for PUT/PATCH endpoints with pre-populated documentation."""
        return cls.attach_at(methods=["PUT", "PATCH"], **kwargs)
    
    @classmethod
    def delete(cls, **kwargs) -> Callable[[F], F]:
        """Helper for DELETE endpoints with pre-populated documentation."""
        return cls.attach_at(methods=["DELETE"], **kwargs)
```

### RestBlueprint Class

```python
class RestBlueprint(RestEndpoint):
    """
    Blueprint for REST API collections with shared versioning, tags,
    and authentication requirements.
    """
    
    base_path: Optional[str] = None
    base_leaf: Optional[str] = None
    replace_tags: bool = False
    
    @classmethod
    def add_crud(
        cls,
        resource: str,
        schema: Type,
        list_handler: Optional[Callable] = None,
        create_handler: Optional[Callable] = None,
        read_handler: Optional[Callable] = None,
        update_handler: Optional[Callable] = None,
        delete_handler: Optional[Callable] = None
    ) -> List[EndpointDescriptor]:
        """
        Register standardized CRUD routes for a resource.
        
        Args:
            resource: Resource name (e.g., "users")
            schema: Pydantic/dataclass schema for the resource
            list_handler: Handler for GET /resource (list)
            create_handler: Handler for POST /resource (create)
            read_handler: Handler for GET /resource/{id} (read)
            update_handler: Handler for PUT /resource/{id} (update)
            delete_handler: Handler for DELETE /resource/{id} (delete)
        
        Returns:
            List of EndpointDescriptor objects for registered routes.
        """
        pass
```

### EndpointDescriptor Dataclass

```python
@dataclass
class EndpointDescriptor:
    """
    Record containing handler reference plus merged metadata for
    routing and documentation generation.
    """
    
    handler: Callable
    module: str
    leaf: Optional[str]
    path: Optional[str]
    methods: List[str]
    version: Optional[str]
    tags: List[str]
    constraints: EndpointConstraints
    doc: Optional[Doc]
    extras: Dict[str, Any]
    
    def to_openapi_path(self) -> Dict[str, Any]:
        """Convert descriptor to OpenAPI path item."""
        pass
    
    def to_security_row(self) -> Dict[str, Any]:
        """Convert descriptor to security audit row."""
        pass
```

### EndpointConstraints Dataclass

```python
@dataclass
class EndpointConstraints:
    """
    Normalized constraint objects for policy engines to introspect.
    """
    
    access_policy: Optional[AccessPolicy]
    rate_limit: Optional[RateLimit]
    scopes: List[str]
    roles: List[str]
    
    @classmethod
    def merge(
        cls,
        parent: "EndpointConstraints",
        child: "EndpointConstraints",
        replace_scopes: bool = False,
        replace_roles: bool = False
    ) -> "EndpointConstraints":
        """
        Merge parent and child constraints following inheritance rules.
        
        Args:
            parent: Parent constraint set.
            child: Child constraint set.
            replace_scopes: If True, child scopes replace parent scopes.
            replace_roles: If True, child roles replace parent roles.
        
        Returns:
            Merged EndpointConstraints with combined policies.
        """
        pass
```

### EndpointRegistry Class

```python
class EndpointRegistry:
    """
    Module-level registry that collects all endpoint descriptors
    from attach_at/attach_child calls.
    """
    
    _descriptors: List[EndpointDescriptor] = []
    _path_method_index: Dict[Tuple[str, str], EndpointDescriptor] = {}
    
    @classmethod
    def register(
        cls,
        descriptor: EndpointDescriptor,
        on_conflict: str = "error"
    ) -> None:
        """
        Register a descriptor, checking for conflicts.
        
        Args:
            descriptor: The EndpointDescriptor to register.
            on_conflict: "error" to raise on conflict, "replace" to override.
        
        Raises:
            EndpointConflictError: If path+method already registered
                                  and on_conflict="error".
        """
        pass
    
    @classmethod
    def collect(cls) -> List[EndpointDescriptor]:
        """
        Return all registered descriptors.
        
        Returns:
            List of all EndpointDescriptor objects.
        """
        return cls._descriptors.copy()
    
    @classmethod
    def export_security_map(
        cls,
        filter_tag: Optional[str] = None,
        format: str = "markdown"
    ) -> str:
        """
        Export security audit map for review.
        
        Args:
            filter_tag: Optional tag to filter endpoints.
            format: Output format ("markdown", "csv", "json").
        
        Returns:
            Formatted security map string.
        """
        pass
    
    @classmethod
    def clear(cls) -> None:
        """Clear all registered descriptors (for testing)."""
        cls._descriptors.clear()
        cls._path_method_index.clear()
```

### AccessPolicy Class

```python
@dataclass
class AccessPolicy:
    """
    Security constraint defining roles, scopes, and authentication
    requirements for an endpoint.
    """
    
    roles: List[str] = field(default_factory=list)
    scopes: List[str] = field(default_factory=list)
    require_auth: bool = True
    
    def merge_with(
        self,
        other: "AccessPolicy",
        replace_roles: bool = False,
        replace_scopes: bool = False
    ) -> "AccessPolicy":
        """
        Merge this policy with another, combining constraints.
        
        The merged policy enforces all constraints (logical AND).
        
        Args:
            other: Policy to merge with.
            replace_roles: If True, other.roles replaces self.roles.
            replace_scopes: If True, other.scopes replaces self.scopes.
        
        Returns:
            New AccessPolicy with combined constraints.
        """
        pass
    
    def check(self, user: "User") -> bool:
        """
        Check if a user satisfies this policy.
        
        Args:
            user: User to check against policy.
        
        Returns:
            True if user satisfies all constraints.
        """
        pass
```

### RateLimit Class

```python
@dataclass
class RateLimit:
    """
    Rate limiting constraint for an endpoint.
    """
    
    requests: int
    window: int  # seconds
    
    @classmethod
    def most_restrictive(
        cls,
        *limits: Optional["RateLimit"]
    ) -> Optional["RateLimit"]:
        """
        Return the most restrictive rate limit from a set.
        
        Args:
            *limits: Rate limits to compare (None values ignored).
        
        Returns:
            The most restrictive RateLimit, or None if all are None.
        """
        pass
```

### Doc Class

```python
@dataclass
class Doc:
    """
    Documentation metadata for an endpoint.
    """
    
    summary: Optional[str] = None
    description: Optional[str] = None
    deprecated: bool = False
    external_docs: Optional[str] = None
```

## Data Models

### Router Protocol

```python
class Router(Protocol):
    """
    Protocol defining the minimal router interface for endpoint
    registration.
    """
    
    def add_endpoint(self, descriptor: EndpointDescriptor) -> None:
        """
        Add an endpoint descriptor to the router.
        
        Args:
            descriptor: The EndpointDescriptor to add.
        """
        ...
```

### Exception Classes

```python
class EndpointRegistrationError(Exception):
    """
    Raised when endpoint registration fails due to missing
    mandatory metadata or invalid configuration.
    """
    
    def __init__(self, message: str, endpoint: Optional[Type] = None):
        self.endpoint = endpoint
        super().__init__(message)


class EndpointConflictError(Exception):
    """
    Raised when two descriptors target the same path+method
    combination.
    """
    
    def __init__(
        self,
        path: str,
        method: str,
        existing_handler: Callable,
        new_handler: Callable
    ):
        self.path = path
        self.method = method
        self.existing_handler = existing_handler
        self.new_handler = new_handler
        super().__init__(
            f"Conflict at {method} {path}: "
            f"{existing_handler.__name__} vs {new_handler.__name__}"
        )
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Decorator Identity Preservation

*For any* handler function decorated with `attach_at`, the returned function SHALL be identical (same object identity) to the original function, ensuring decorator stacking works correctly.

**Validates: Requirements 2.1, 4.3**

### Property 2: Attribute Inheritance and Override

*For any* Endpoint subclass with class-level attributes and any `attach_at` call:
- If a kwarg is explicitly provided, it SHALL override the class attribute
- If a kwarg is not provided, the class attribute value SHALL be used
- Class attributes SHALL remain unchanged after attachment

**Validates: Requirements 1.3, 1.4, 1.6, 2.3, 2.8**

### Property 3: Descriptor Emission

*For any* `attach_at` or `attach_child` call, an EndpointDescriptor SHALL be emitted to the EndpointRegistry containing the handler reference and merged metadata from both class attributes and call kwargs.

**Validates: Requirements 4.1, 6.1**

### Property 4: Extra Kwargs Preservation

*For any* additional kwargs passed to `attach_at` beyond the standard parameters, those kwargs SHALL appear verbatim in the descriptor's `extras` field, and unknown keys SHALL be preserved for downstream consumers.

**Validates: Requirements 2.7, 5.4**

### Property 5: Constraint Inheritance

*For any* parent-child endpoint relationship via `attach_child`:
- If the child does not set a constraint attribute, it SHALL inherit the parent's value
- Security constraints (access_policy, scopes, rate_limit) SHALL follow "parent defaults, child overrides"
- Unsupplied attributes SHALL remain as defined on the child endpoint class

**Validates: Requirements 3.6, 6.7, 7.1, 7.2, 7.3, 9.4, 10.6**

### Property 6: List Field Merge Behavior

*For any* list-like fields (tags, roles, scopes) in parent-child relationships:
- By default, the child list SHALL be merged with the parent list (union)
- When `replace_tags=True`, `replace_roles=True`, or `replace_scopes=True` is set, the child list SHALL fully replace the parent list
- When `merge_tags=True` is set on a blueprint, parent tags SHALL be appended to child tags

**Validates: Requirements 3.7, 3.8, 7.4, 7.5, 9.9**

### Property 7: Security Policy Composition

*For any* endpoint with multiple applicable policies (e.g., blueprint policy + handler policy), the combined policy SHALL enforce all constraints via logical AND, ensuring nested definitions do not inadvertently weaken security.

**Validates: Requirements 7.6, 7.7**

### Property 8: Rate Limit Stacking

*For any* endpoint with parent and child rate limits, the most restrictive rate limit SHALL apply unless the child explicitly opts out via `rate_limit=None`.

**Validates: Requirements 7.8**

### Property 9: Registration Error Handling

*For any* `attach_at` call:
- If mandatory metadata (leaf or path) is missing, EndpointRegistrationError SHALL be raised
- If the path+method combination conflicts with an existing registration and `on_conflict="error"`, EndpointConflictError SHALL be raised
- If `on_conflict="replace"`, the existing registration SHALL be replaced without error

**Validates: Requirements 2.4, 2.5, 6.5, 6.6**

### Property 10: Path Composition

*For any* `attach_child` call on a parent with `base_path` or `base_leaf`:
- The child's path SHALL be computed relative to the parent's base
- If parent has `base_path="/api/v1"` and child has `leaf="portals"`, the result SHALL be `/api/v1/portals`
- If child passes `absolute=True`, the child's path SHALL override the parent prefix

**Validates: Requirements 9.6, 9.7, 10.3, 10.4**

### Property 11: Handler Non-Execution During Import

*For any* package import that registers endpoints, the handlers SHALL NOT be executed during import; only descriptor generation SHALL occur.

**Validates: Requirements 6.2**

### Property 12: Schema Inspection

*For any* `attach_at` call with `request_schema` or `response_schema` that is a dataclass or Pydantic model, the decorator SHALL inspect `.model_json_schema()` or `__dataclass_fields__` to capture JSON-schema fragments in the descriptor.

**Validates: Requirements 8.7**

### Property 13: Descriptor Metadata Completeness

*For any* call to `EndpointRegistry.collect()`, each returned descriptor SHALL include consolidated metadata: path, methods, access_policy, scopes, rate_limits, and all other constraint fields.

**Validates: Requirements 11.1**

## Error Handling

### EndpointRegistrationError

Raised when `attach_at` is called with invalid or missing configuration:

```python
class EndpointRegistrationError(Exception):
    """Raised when endpoint registration fails."""
    
    def __init__(
        self,
        message: str,
        endpoint: Optional[Type] = None,
        missing_fields: Optional[List[str]] = None
    ):
        self.endpoint = endpoint
        self.missing_fields = missing_fields or []
        super().__init__(message)
```

Common scenarios:
- Missing `leaf` or `path` parameter
- Invalid method names
- Schema inspection failure

### EndpointConflictError

Raised when two handlers attempt to register at the same path+method:

```python
class EndpointConflictError(Exception):
    """Raised when endpoint path+method conflicts."""
    
    def __init__(
        self,
        path: str,
        method: str,
        existing_handler: Callable,
        new_handler: Callable
    ):
        self.path = path
        self.method = method
        self.existing_handler = existing_handler
        self.new_handler = new_handler
        super().__init__(
            f"Conflict at {method} {path}: "
            f"existing={existing_handler.__module__}.{existing_handler.__name__}, "
            f"new={new_handler.__module__}.{new_handler.__name__}"
        )
```

### SchemaInspectionError

Raised when schema inspection fails for request/response schemas:

```python
class SchemaInspectionError(Exception):
    """Raised when schema inspection fails."""
    
    def __init__(self, schema: Type, reason: str):
        self.schema = schema
        self.reason = reason
        super().__init__(
            f"Failed to inspect schema {schema.__name__}: {reason}"
        )
```

## Testing Strategy

### Unit Tests

Unit tests should cover:

1. **Class Structure Tests**
   - Verify Endpoint class has attach_at and attach_child methods
   - Verify Blueprint extends Endpoint with register method
   - Verify RestEndpoint has CRUD helper methods
   - Verify RestBlueprint has add_crud method
   - Verify EndpointDescriptor has all required fields

2. **Parameter Acceptance Tests**
   - Verify attach_at accepts all documented parameters
   - Verify extra kwargs are stored in extras
   - Verify REST-specific parameters are handled

3. **Error Condition Tests**
   - Verify EndpointRegistrationError on missing leaf/path
   - Verify EndpointConflictError on duplicate registration
   - Verify on_conflict="replace" allows override

4. **Export Tests**
   - Verify export_security_map produces valid output
   - Verify filtering by tag works correctly

### Property-Based Tests

Property-based tests should use the `testbase` framework with minimum 100 iterations per property. Each test should be tagged with the property it validates.

**Testing Framework**: testbase (as specified in AGENTS.md)

**Property Test Configuration**:
- Minimum iterations: 100
- Tag format: `Feature: endpoint-abstractions, Property N: <property_text>`

**Generator Requirements**:
- Generate valid endpoint class hierarchies with random attributes
- Generate valid path/leaf strings
- Generate valid method lists
- Generate AccessPolicy objects with random roles/scopes
- Generate RateLimit objects with random values
- Generate random extra kwargs

### Test Organization

Following the repository conventions from AGENTS.md:

```
source/testroots/ccai/tests/singlehost/webworks/
├── endpoints/
│   ├── test_endpoint.py           # Endpoint base class tests
│   ├── test_blueprint.py          # Blueprint tests
│   ├── test_rest_endpoint.py      # RestEndpoint tests
│   ├── test_rest_blueprint.py     # RestBlueprint tests
│   ├── test_endpoint_descriptor.py # EndpointDescriptor tests
│   ├── test_endpoint_registry.py  # EndpointRegistry tests
│   ├── test_access_policy.py      # AccessPolicy tests
│   └── test_rate_limit.py         # RateLimit tests
```

### Integration Points

- Integration with Router implementations for endpoint registration
- Integration with OpenAPI generators for documentation
- Integration with security audit tooling for CI/CD
- Integration with AccessPolicy enforcement in request handling
