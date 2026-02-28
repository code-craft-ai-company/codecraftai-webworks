# Design Document: Blueprint Endpoints

## Overview

This design document describes the architecture and implementation approach for the Blueprint Endpoints feature. The feature provides a composable system for grouping related HTTP endpoints under shared parent paths with inherited constraints, enabling developers to organize CRUD handlers, versioned APIs, and related endpoint collections as cohesive units.

The design builds on the Endpoint Abstractions foundation, focusing specifically on:
- Blueprint class for grouping multiple endpoint attachments
- `attach_at` decorator for binding handlers to URL locations
- `attach_child` method for hierarchical parent-child composition
- Constraint inheritance and merge rules for security policies

Key design principles:
- Composition over configuration: Blueprints compose endpoints with predictable inheritance
- Fail-fast validation: Registration errors are raised immediately at decoration time
- Testability: Blueprints can generate descriptors without a live router instance
- Security by default: Parent constraints cascade to children unless explicitly overridden

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Blueprint Class Hierarchy                            │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                           Endpoint                                   │    │
│  │  - access_policy, rate_limit, methods, version, tags                │    │
│  │  - attach_at(**bindings) -> decorator                               │    │
│  │  - attach_child(child, **kwargs) -> EndpointDescriptor              │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                    │                                                         │
│         ┌─────────┴─────────┐                                               │
│         ▼                   ▼                                               │
│  ┌─────────────────┐  ┌─────────────────┐                                   │
│  │    Blueprint    │  │  RestEndpoint   │                                   │
│  │                 │  │                 │                                   │
│  │ - base_path     │  │ - schemas       │                                   │
│  │ - base_leaf     │  │ - CRUD helpers  │                                   │
│  │ - merge_tags    │  └─────────────────┘                                   │
│  │ - register()    │           │                                            │
│  └─────────────────┘           │                                            │
│         │                      │                                            │
│         └──────────┬───────────┘                                            │
│                    ▼                                                        │
│         ┌─────────────────────┐                                             │
│         │   RestBlueprint     │                                             │
│         │                     │                                             │
│         │ - add_crud()        │                                             │
│         │ - register()        │                                             │
│         └─────────────────────┘                                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                    Blueprint Registration Flow                               │
│                                                                              │
│  class UserBlueprint(Blueprint):                                            │
│      base_path = "/api/v1/users"                                            │
│      access_policy = AccessPolicy(roles=["user"])                           │
│                                                                              │
│      @classmethod                                                            │
│      def register(cls):                                                      │
│          cls.attach_at(leaf="list")(list_users)                             │
│          cls.attach_at(leaf="create")(create_user)                          │
│          return cls._collect_descriptors()                                  │
│                                                                              │
│         │                                                                    │
│         ▼                                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    EndpointDescriptor (list)                         │    │
│  │  path: /api/v1/users/list                                           │    │
│  │  access_policy: AccessPolicy(roles=["user"])                        │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    EndpointDescriptor (create)                       │    │
│  │  path: /api/v1/users/create                                         │    │
│  │  access_policy: AccessPolicy(roles=["user"])                        │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│         │                                                                    │
│         ▼                                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    EndpointRegistry                                  │    │
│  │  - collect() -> List[EndpointDescriptor]                            │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                    Constraint Inheritance Flow                               │
│                                                                              │
│  Parent Blueprint                                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  access_policy = AccessPolicy(roles=["user"])                       │    │
│  │  tags = ["api", "v1"]                                               │    │
│  │  rate_limit = RateLimit(requests=100, window=60)                    │    │
│  │  merge_tags = True                                                  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│         │                                                                    │
│         │ attach_at(leaf="admin", tags=["admin"])                           │
│         ▼                                                                    │
│  Child Descriptor (merged)                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  access_policy = AccessPolicy(roles=["user"])  # inherited          │    │
│  │  tags = ["api", "v1", "admin"]                 # merged             │    │
│  │  rate_limit = RateLimit(requests=100, window=60)  # inherited       │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│         │ attach_at(leaf="public", access_policy=AccessPolicy(roles=[]))    │
│         ▼                                                                    │
│  Child Descriptor (overridden)                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  access_policy = AccessPolicy(roles=[])        # overridden         │    │
│  │  tags = ["api", "v1"]                          # inherited          │    │
│  │  rate_limit = RateLimit(requests=100, window=60)  # inherited       │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                    Parent/Child Attachment Flow                              │
│                                                                              │
│  class PortalEndpoint(Endpoint):                                            │
│      leaf = "portals"                                                        │
│      version = "v1"                                                          │
│                                                                              │
│  class APIBlueprint(Blueprint):                                             │
│      base_path = "/api/v1"                                                  │
│                                                                              │
│  api_bp = APIBlueprint()                                                    │
│  api_bp.attach_child(PortalEndpoint)                                        │
│         │                                                                    │
│         ▼                                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  EndpointDescriptor                                                  │    │
│  │  path: /api/v1/portals  (base_path + child.leaf)                    │    │
│  │  version: v1            (from child)                                 │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Components and Interfaces

### Blueprint Class

```python
class Blueprint(Endpoint):
    """
    Endpoint composite that emits multiple attachments in one declaration.
    Provides a shared parent path and constraint inheritance for grouped
    endpoints.
    """
    
    # Class-level attributes for path composition
    base_path: Optional[str] = None
    base_leaf: Optional[str] = None
    
    # Merge behavior flags
    merge_tags: bool = False
    replace_scopes: bool = False
    replace_roles: bool = False
    
    # Internal tracking of registered descriptors
    _registered_descriptors: List[EndpointDescriptor] = []
    
    @classmethod
    def register(
        cls,
        router: Optional["Router"] = None
    ) -> List[EndpointDescriptor]:
        """
        Register all child endpoints and return their descriptors.
        
        This method should be overridden by subclasses to define
        the endpoints that belong to this blueprint.
        
        Args:
            router: Optional router to add endpoints to. If None,
                   descriptors are returned without router registration.
        
        Returns:
            List of EndpointDescriptor objects for all registered endpoints.
        """
        pass
    
    @classmethod
    def attach_at(
        cls,
        leaf: Optional[str] = None,
        path: Optional[str] = None,
        **kwargs
    ) -> Callable[[F], F]:
        """
        Decorator that binds a handler to a URL location relative to
        the blueprint's base path.
        
        Overrides Endpoint.attach_at to compose paths with base_path/base_leaf.
        
        Args:
            leaf: URL leaf segment relative to base_path/base_leaf.
            path: Full URL path (overrides base_path composition).
            **kwargs: Additional parameters passed to parent attach_at.
        
        Returns:
            Decorator that returns the original function unchanged.
        """
        pass
    
    @classmethod
    def _compose_path(cls, leaf: Optional[str], path: Optional[str]) -> str:
        """
        Compose the full path from base_path/base_leaf and child leaf/path.
        
        Args:
            leaf: Child leaf segment.
            path: Child full path (if provided, overrides composition).
        
        Returns:
            Composed full path string.
        """
        pass
    
    @classmethod
    def _merge_constraints(
        cls,
        child_kwargs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Merge parent constraints with child kwargs following inheritance rules.
        
        Args:
            child_kwargs: Kwargs provided to attach_at.
        
        Returns:
            Merged kwargs with inherited values filled in.
        """
        pass
```

### attach_at Decorator Implementation

```python
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
    
    The decorator:
    1. Validates mandatory metadata (leaf or path required)
    2. Merges class attributes with provided kwargs
    3. Creates an EndpointDescriptor with merged metadata
    4. Registers the descriptor with EndpointRegistry
    5. Returns the original function unchanged
    
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
        EndpointRegistrationError: If mandatory metadata missing.
        EndpointConflictError: If path+method conflicts and on_conflict="error".
    """
    def decorator(handler: F) -> F:
        # Validate mandatory metadata
        if leaf is None and path is None:
            raise EndpointRegistrationError(
                "Either 'leaf' or 'path' must be provided",
                endpoint=cls,
                missing_fields=["leaf", "path"]
            )
        
        # Merge class attributes with kwargs
        merged_methods = methods if methods is not None else cls.methods
        merged_version = version if version is not None else cls.version
        merged_tags = tags if tags is not None else cls.tags
        merged_access_policy = access_policy if access_policy is not None else cls.access_policy
        merged_rate_limit = rate_limit if rate_limit is not None else cls.rate_limit
        
        # Create descriptor
        descriptor = EndpointDescriptor(
            handler=handler,
            module=handler.__module__,
            leaf=leaf,
            path=path,
            methods=merged_methods,
            version=merged_version,
            tags=merged_tags,
            constraints=EndpointConstraints(
                access_policy=merged_access_policy,
                rate_limit=merged_rate_limit,
                scopes=[],
                roles=[]
            ),
            doc=doc,
            extras=extras
        )
        
        # Register with EndpointRegistry
        EndpointRegistry.register(descriptor, on_conflict=on_conflict)
        
        # Return original function unchanged
        return handler
    
    return decorator
```

### attach_child Method Implementation

```python
@classmethod
def attach_child(
    cls,
    child_endpoint: Type["Endpoint"],
    leaf: Optional[str] = None,
    path: Optional[str] = None,
    methods: Optional[List[str]] = None,
    version: Optional[str] = None,
    tags: Optional[List[str]] = None,
    access_policy: Optional[AccessPolicy] = None,
    rate_limit: Optional[RateLimit] = None,
    **kwargs
) -> EndpointDescriptor:
    """
    Attach a child endpoint relative to this endpoint's base path.
    
    The method:
    1. Computes the child path relative to parent base_path/base_leaf
    2. Merges parent constraints with child attributes
    3. Applies any explicit overrides from kwargs
    4. Creates and registers the child descriptor
    
    Args:
        child_endpoint: The child endpoint class to attach.
        leaf: Override for child's leaf (relative to parent base).
        path: Override for child's path (relative to parent base).
        methods: Override for child's methods.
        version: Override for child's version.
        tags: Override for child's tags.
        access_policy: Override for child's access policy.
        rate_limit: Override for child's rate limit.
        **kwargs: Additional overrides for child descriptor.
    
    Returns:
        The merged EndpointDescriptor for the child.
    """
    # Determine child leaf/path
    child_leaf = leaf if leaf is not None else getattr(child_endpoint, 'leaf', None)
    child_path = path if path is not None else getattr(child_endpoint, 'path', None)
    
    # Compose path relative to parent
    composed_path = cls._compose_path(child_leaf, child_path)
    
    # Merge constraints: parent defaults, child overrides
    merged_access_policy = (
        access_policy if access_policy is not None
        else getattr(child_endpoint, 'access_policy', None)
        or cls.access_policy
    )
    
    merged_rate_limit = (
        rate_limit if rate_limit is not None
        else getattr(child_endpoint, 'rate_limit', None)
        or cls.rate_limit
    )
    
    # Handle tag merging
    child_tags = tags if tags is not None else getattr(child_endpoint, 'tags', [])
    if cls.merge_tags:
        merged_tags = list(cls.tags) + list(child_tags)
    else:
        merged_tags = child_tags if child_tags else cls.tags
    
    # Create descriptor
    descriptor = EndpointDescriptor(
        handler=None,  # Child endpoint class, not a handler
        module=child_endpoint.__module__,
        leaf=child_leaf,
        path=composed_path,
        methods=methods or getattr(child_endpoint, 'methods', cls.methods),
        version=version or getattr(child_endpoint, 'version', cls.version),
        tags=merged_tags,
        constraints=EndpointConstraints(
            access_policy=merged_access_policy,
            rate_limit=merged_rate_limit,
            scopes=[],
            roles=[]
        ),
        doc=kwargs.get('doc'),
        extras=kwargs
    )
    
    # Register with EndpointRegistry
    EndpointRegistry.register(descriptor)
    
    return descriptor
```

### Constraint Merge Logic

```python
class ConstraintMerger:
    """
    Utility class for merging parent and child constraints following
    the inheritance rules.
    """
    
    @staticmethod
    def merge_access_policies(
        parent: Optional[AccessPolicy],
        child: Optional[AccessPolicy],
        replace_roles: bool = False,
        replace_scopes: bool = False
    ) -> Optional[AccessPolicy]:
        """
        Merge parent and child access policies.
        
        Rules:
        - If child is None, inherit parent
        - If child is set, child overrides parent
        - For roles/scopes: union by default, replace if flag set
        - Combined policy enforces all constraints (logical AND)
        
        Args:
            parent: Parent access policy.
            child: Child access policy.
            replace_roles: If True, child roles replace parent roles.
            replace_scopes: If True, child scopes replace parent scopes.
        
        Returns:
            Merged AccessPolicy or None if both are None.
        """
        if child is None:
            return parent
        if parent is None:
            return child
        
        # Merge roles
        if replace_roles:
            merged_roles = child.roles
        else:
            merged_roles = list(set(parent.roles) | set(child.roles))
        
        # Merge scopes
        if replace_scopes:
            merged_scopes = child.scopes
        else:
            merged_scopes = list(set(parent.scopes) | set(child.scopes))
        
        return AccessPolicy(
            roles=merged_roles,
            scopes=merged_scopes,
            require_auth=parent.require_auth or child.require_auth
        )
    
    @staticmethod
    def merge_rate_limits(
        parent: Optional[RateLimit],
        child: Optional[RateLimit]
    ) -> Optional[RateLimit]:
        """
        Merge parent and child rate limits.
        
        Rules:
        - If child is None, inherit parent
        - If child explicitly set to None (opt-out), return None
        - Otherwise, return most restrictive limit
        
        Args:
            parent: Parent rate limit.
            child: Child rate limit.
        
        Returns:
            Most restrictive RateLimit or None.
        """
        if child is None:
            return parent
        
        return RateLimit.most_restrictive(parent, child)
    
    @staticmethod
    def merge_tags(
        parent: List[str],
        child: List[str],
        merge: bool = False,
        replace: bool = False
    ) -> List[str]:
        """
        Merge parent and child tags.
        
        Rules:
        - If replace=True, child tags fully replace parent
        - If merge=True, parent tags appended to child
        - Otherwise, child tags win if set, else inherit parent
        
        Args:
            parent: Parent tags.
            child: Child tags.
            merge: If True, merge parent and child tags.
            replace: If True, child replaces parent.
        
        Returns:
            Merged tag list.
        """
        if replace:
            return child
        if merge:
            return list(parent) + list(child)
        return child if child else parent
```

## Data Models

### EndpointDescriptor (from endpoint-abstractions)

```python
@dataclass
class EndpointDescriptor:
    """
    Record containing handler reference plus merged metadata for
    routing and documentation generation.
    """
    
    handler: Optional[Callable]
    module: str
    leaf: Optional[str]
    path: Optional[str]
    methods: List[str]
    version: Optional[str]
    tags: List[str]
    constraints: EndpointConstraints
    doc: Optional[Doc]
    extras: Dict[str, Any]
```

### EndpointConstraints (from endpoint-abstractions)

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
```

### BlueprintConfig

```python
@dataclass
class BlueprintConfig:
    """
    Configuration options for blueprint behavior.
    """
    
    base_path: Optional[str] = None
    base_leaf: Optional[str] = None
    merge_tags: bool = False
    replace_tags: bool = False
    replace_scopes: bool = False
    replace_roles: bool = False
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Decorator Identity Preservation

*For any* handler function decorated with `attach_at`, the returned function SHALL be identical (same object identity) to the original function, ensuring decorator stacking works correctly.

**Validates: Requirements 3.1, 5.3**

### Property 2: Class Default Inheritance and Override

*For any* Endpoint subclass with class-level attributes and any `attach_at` call:
- If a kwarg is explicitly provided, it SHALL override the class attribute
- If a kwarg is not provided, the class attribute value SHALL be used
- Class attributes SHALL remain unchanged after attachment

**Validates: Requirements 3.8, 3.9, 3.10**

### Property 3: Extra Kwargs Preservation

*For any* additional kwargs passed to `attach_at` beyond the standard parameters, those kwargs SHALL appear verbatim in the descriptor's `extras` field.

**Validates: Requirements 3.7**

### Property 4: Path Composition

*For any* Blueprint with `base_path` and any child endpoint with `leaf`:
- The resulting path SHALL be the composition of base_path and leaf
- If child provides absolute `path`, it SHALL override the composition

**Validates: Requirements 1.7, 4.3, 4.4**

### Property 5: Security Constraint Inheritance

*For any* parent-child endpoint relationship:
- If the child does not set a security attribute, it SHALL inherit the parent's value
- Security constraints (access_policy, scopes, rate_limit) SHALL follow "parent defaults, child overrides"

**Validates: Requirements 2.3, 2.4, 2.5, 6.5**

### Property 6: List Field Merge Behavior

*For any* list-like fields (tags, roles, scopes) in parent-child relationships:
- By default, child tags SHALL win unless `merge_tags=True`
- When `merge_tags=True`, parent tags SHALL be appended to child tags
- For roles/scopes, default behavior SHALL be union
- When `replace_roles=True` or `replace_scopes=True`, child list SHALL fully replace parent

**Validates: Requirements 2.1, 2.2, 2.6, 2.7**

### Property 7: Security Policy Composition

*For any* endpoint with multiple applicable policies (e.g., blueprint policy + handler policy), the combined policy SHALL enforce all constraints via logical AND, ensuring nested definitions do not inadvertently weaken security.

**Validates: Requirements 2.8**

### Property 8: Rate Limit Stacking

*For any* endpoint with parent and child rate limits, the most restrictive rate limit SHALL apply unless the child explicitly opts out via `rate_limit=None`.

**Validates: Requirements 2.9**

### Property 9: Descriptor Emission

*For any* `attach_at` or `attach_child` call, an EndpointDescriptor SHALL be emitted to the EndpointRegistry containing the handler reference and merged metadata.

**Validates: Requirements 5.1, 5.6**

### Property 10: Handler Non-Execution During Registration

*For any* handler decorated with `attach_at`, the handler SHALL NOT be executed during decoration or import; only descriptor generation SHALL occur.

**Validates: Requirements 5.4, 5.7**

### Property 11: Conflict Detection and Replace

*For any* `attach_at` call:
- If mandatory metadata (leaf or path) is missing, EndpointRegistrationError SHALL be raised
- If path+method conflicts with existing registration and `on_conflict="error"`, EndpointConflictError SHALL be raised
- If `on_conflict="replace"`, existing registration SHALL be replaced without error

**Validates: Requirements 3.4, 3.5, 6.3, 6.4**

### Property 12: Blueprint Multi-Attachment

*For any* Blueprint with a `register()` method that calls `attach_at` multiple times, each call SHALL emit a separate EndpointDescriptor, and `register()` SHALL return all descriptors.

**Validates: Requirements 1.1, 1.3, 1.4**

### Property 13: Blueprint Router Integration

*For any* Blueprint `register(router)` call:
- If router is provided, `router.add_endpoint()` SHALL be called for each descriptor
- If router is None, descriptors SHALL be returned without router interaction

**Validates: Requirements 1.5, 1.6**

### Property 14: Child Attribute Preservation

*For any* `attach_child` call without explicit overrides, the child endpoint's class attributes SHALL be preserved in the resulting descriptor.

**Validates: Requirements 4.6, 6.6**

### Property 15: Blueprint Idempotency

*For any* Blueprint, calling `register()` multiple times SHALL return equivalent descriptor lists (same paths, methods, constraints).

**Validates: Requirements 6.7**

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
- Invalid constraint types

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

## Testing Strategy

### Unit Tests

Unit tests should cover:

1. **Blueprint Structure Tests**
   - Verify Blueprint class extends Endpoint
   - Verify Blueprint has base_path, base_leaf, merge_tags attributes
   - Verify Blueprint has register() method
   - Verify attach_at returns original function

2. **Path Composition Tests**
   - Verify base_path + leaf composition
   - Verify base_leaf + leaf composition
   - Verify absolute path override

3. **Constraint Inheritance Tests**
   - Verify child inherits parent access_policy when not set
   - Verify child overrides parent access_policy when set
   - Verify tag merge behavior with merge_tags flag
   - Verify role/scope union and replace behavior

4. **Error Condition Tests**
   - Verify EndpointRegistrationError on missing leaf/path
   - Verify EndpointConflictError on duplicate registration
   - Verify on_conflict="replace" allows override

5. **Router Integration Tests**
   - Verify register(router) calls router.add_endpoint
   - Verify register(None) returns descriptors without router

### Property-Based Tests

Property-based tests should use the `testbase` framework with minimum 100 iterations per property. Each test should be tagged with the property it validates.

**Testing Framework**: testbase (as specified in AGENTS.md)

**Property Test Configuration**:
- Minimum iterations: 100
- Tag format: `Feature: blueprint-endpoints, Property N: <property_text>`

**Generator Requirements**:
- Generate valid Blueprint subclasses with random base_path/base_leaf
- Generate valid Endpoint subclasses with random attributes
- Generate valid path/leaf strings (alphanumeric with slashes)
- Generate valid method lists from ["GET", "POST", "PUT", "PATCH", "DELETE"]
- Generate AccessPolicy objects with random roles/scopes
- Generate RateLimit objects with random requests/window values
- Generate random tag lists
- Generate random extra kwargs

### Test Organization

Following the repository conventions from AGENTS.md:

```
source/testroots/automojo/tests/singlehost/webworks/
├── blueprints/
│   ├── test_blueprint.py           # Blueprint class tests
│   ├── test_attach_at.py           # attach_at decorator tests
│   ├── test_attach_child.py        # attach_child method tests
│   ├── test_constraint_merge.py    # Constraint inheritance tests
│   ├── test_path_composition.py    # Path composition tests
│   └── test_router_integration.py  # Router integration tests
```

### Integration Points

- Integration with EndpointRegistry for descriptor collection
- Integration with Router implementations for endpoint registration
- Integration with AccessPolicy for security constraint enforcement
- Integration with RateLimit for throttling configuration
- Integration with endpoint-abstractions feature for base Endpoint class

</content>
</invoke>