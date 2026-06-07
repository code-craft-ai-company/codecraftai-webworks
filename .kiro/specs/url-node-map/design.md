# Design Document: URL Node Map

## Overview

This design document describes the architecture and implementation approach for the URL Node Map feature. The URL Node Map provides the foundational hierarchical tree structure for organizing HTTP endpoints in the ccai web framework. It serves as the underlying data structure that endpoints attach to, supporting path-based addressing, metadata inheritance, and tree export capabilities.

The design follows a tree-based approach where each URL path segment corresponds to a node in the tree. Nodes can carry metadata (access policies, rate limits, tags) that cascades to child nodes according to well-defined inheritance rules. The tree supports both static path segments and dynamic parameter segments for flexible routing.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      URL Node Map                                │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                    URLNodeMap                            │    │
│  │  - root: URLNode                                         │    │
│  │  - frozen: bool                                          │    │
│  │  - lock: RLock                                           │    │
│  └─────────────────────────────────────────────────────────┘    │
│                              │                                   │
│                              ▼                                   │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                    URLNode (Root: /)                     │    │
│  │  - segment: ""                                           │    │
│  │  - path: "/"                                             │    │
│  │  - metadata: {}                                          │    │
│  │  - children: {}                                          │    │
│  └─────────────────────────────────────────────────────────┘    │
│           │                    │                    │            │
│           ▼                    ▼                    ▼            │
│  ┌─────────────┐      ┌─────────────┐      ┌─────────────┐      │
│  │ URLNode     │      │ URLNode     │      │ URLNode     │      │
│  │ segment:api │      │ segment:docs│      │ segment:    │      │
│  │ path:/api   │      │ path:/docs  │      │ static      │      │
│  └─────────────┘      └─────────────┘      └─────────────┘      │
│           │                                                      │
│           ▼                                                      │
│  ┌─────────────┐                                                │
│  │ URLNode     │                                                │
│  │ segment:v1  │                                                │
│  │ path:/api/v1│                                                │
│  └─────────────┘                                                │
│           │                                                      │
│           ▼                                                      │
│  ┌─────────────────┐                                            │
│  │ URLNode         │                                            │
│  │ segment:{id}    │  ← Parameter segment                       │
│  │ path:/api/v1/{id}│                                           │
│  │ is_parameter:True│                                           │
│  └─────────────────┘                                            │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    Metadata Inheritance                          │
│                                                                  │
│  Parent Node                    Child Node                       │
│  ┌──────────────┐              ┌──────────────┐                 │
│  │access_policy │──inherits──►│access_policy │                 │
│  │  (if not set)│              │  (override)  │                 │
│  │tags: [a, b]  │──merges────►│tags: [c]     │ = [a, b, c]     │
│  │rate_limit: 10│──restricts─►│rate_limit: 5 │ = 5 (stricter)  │
│  └──────────────┘              └──────────────┘                 │
└─────────────────────────────────────────────────────────────────┘
```

## Components and Interfaces

### URLNodeMap Class

```python
class URLNodeMap:
    """
    Hierarchical tree structure for organizing URL paths and endpoint metadata.
    """
    
    def __init__(self):
        """Initialize the URL node map with a root node."""
        self._root: URLNode = URLNode(segment="", path="/", parent=None)
        self._frozen: bool = False
        self._lock: threading.RLock = threading.RLock()
    
    @property
    def root(self) -> URLNode:
        """Return the root node of the tree."""
        return self._root
    
    def get_node(self, path: str) -> URLNode:
        """
        Retrieve a node by its full path.
        
        Args:
            path: The full path to the node (e.g., "/api/v1/users").
        
        Returns:
            The URLNode at the specified path.
        
        Raises:
            NodeNotFoundError: If the path does not exist in the tree.
        """
        pass
    
    def get_or_create_node(self, path: str) -> URLNode:
        """
        Retrieve an existing node or create the path if it does not exist.
        
        Args:
            path: The full path to the node.
        
        Returns:
            The URLNode at the specified path (created if necessary).
        
        Raises:
            FrozenTreeError: If the tree is frozen and creation is needed.
        """
        pass
    
    def has_node(self, path: str) -> bool:
        """
        Check if a path exists in the tree.
        
        Args:
            path: The full path to check.
        
        Returns:
            True if the path exists, False otherwise.
        """
        pass
    
    def remove_node(self, path: str, recursive: bool = False) -> None:
        """
        Remove a node from the tree.
        
        Args:
            path: The full path of the node to remove.
            recursive: If True, remove all descendants as well.
        
        Raises:
            NodeNotFoundError: If the path does not exist.
            FrozenTreeError: If the tree is frozen.
            NodeHasChildrenError: If recursive=False and node has children.
        """
        pass
    
    def iterate_nodes(self) -> Iterator[URLNode]:
        """
        Iterate over all nodes in depth-first order.
        
        Yields:
            URLNode instances in depth-first traversal order.
        """
        pass
    
    def iterate_leaves(self) -> Iterator[URLNode]:
        """
        Iterate over all leaf nodes (nodes with handlers).
        
        Yields:
            URLNode instances that have handlers attached.
        """
        pass
    
    def freeze(self) -> None:
        """
        Make the tree immutable for lock-free concurrent reads.
        
        After freezing, any modification attempt raises FrozenTreeError.
        """
        pass
    
    def export_tree(self) -> dict:
        """
        Serialize the tree structure to a dictionary.
        
        Returns:
            Dictionary representation of the tree.
        """
        pass
    
    def export_routes(self) -> list[dict]:
        """
        Export a flat list of all routes with their metadata.
        
        Returns:
            List of route dictionaries with resolved metadata.
        """
        pass
    
    def export_security_map(self, filter_tag: str = None) -> list[dict]:
        """
        Export security-focused route information for auditing.
        
        Args:
            filter_tag: Optional tag to filter routes.
        
        Returns:
            List of security map entries.
        """
        pass
```

### URLNode Class

```python
class URLNode:
    """
    A single node in the URL tree representing a path segment.
    """
    
    def __init__(
        self,
        segment: str,
        path: str,
        parent: Optional[URLNode] = None
    ):
        """
        Args:
            segment: The path segment this node represents.
            path: The full path from root to this node.
            parent: Reference to the parent node (None for root).
        """
        self._segment: str = segment
        self._path: str = path
        self._parent: Optional[URLNode] = parent
        self._children: Dict[str, URLNode] = {}
        self._metadata: Dict[str, Any] = {}
        self._handlers: Dict[str, Callable] = {}  # method -> handler
        self._is_parameter: bool = segment.startswith("{") and segment.endswith("}")
        self._parameter_name: Optional[str] = None
        if self._is_parameter:
            self._parameter_name = segment[1:-1]
    
    @property
    def segment(self) -> str:
        """Return the path segment for this node."""
        return self._segment
    
    @property
    def path(self) -> str:
        """Return the full path from root to this node."""
        return self._path
    
    @property
    def parent(self) -> Optional[URLNode]:
        """Return the parent node or None for root."""
        return self._parent
    
    @property
    def children(self) -> Mapping[str, URLNode]:
        """Return an immutable view of child nodes."""
        return MappingProxyType(self._children)
    
    @property
    def is_parameter(self) -> bool:
        """Return True if this is a parameter segment."""
        return self._is_parameter
    
    @property
    def parameter_name(self) -> Optional[str]:
        """Return the parameter name if this is a parameter segment."""
        return self._parameter_name
    
    @property
    def is_leaf(self) -> bool:
        """Return True if this node has handlers attached."""
        return len(self._handlers) > 0
    
    @property
    def metadata(self) -> Dict[str, Any]:
        """Return a copy of the node's metadata."""
        return dict(self._metadata)
    
    def get_child(self, segment: str) -> URLNode:
        """
        Retrieve a direct child by segment name.
        
        Args:
            segment: The segment name of the child.
        
        Returns:
            The child URLNode.
        
        Raises:
            NodeNotFoundError: If no child with that segment exists.
        """
        pass
    
    def add_child(self, segment: str, **metadata) -> URLNode:
        """
        Add a new child node.
        
        Args:
            segment: The segment name for the new child.
            **metadata: Initial metadata for the child node.
        
        Returns:
            The newly created child URLNode.
        
        Raises:
            NodeConflictError: If a child with that segment already exists.
            PathConflictError: If parameter conflicts with literal segment.
        """
        pass
    
    def get_metadata(self, key: str) -> Any:
        """
        Get a metadata value by key.
        
        Args:
            key: The metadata key.
        
        Returns:
            The metadata value or None if not set.
        """
        return self._metadata.get(key)
    
    def set_metadata(self, key: str, value: Any) -> None:
        """
        Set a metadata value.
        
        Args:
            key: The metadata key.
            value: The metadata value.
        """
        self._metadata[key] = value
    
    def get_effective_metadata(self, key: str) -> Any:
        """
        Get metadata value with inheritance resolution.
        
        Args:
            key: The metadata key.
        
        Returns:
            The effective value considering inheritance from ancestors.
        """
        pass
    
    def get_effective_access_policy(self) -> Optional[AccessPolicy]:
        """
        Compute the combined access policy from the inheritance chain.
        
        Returns:
            The combined AccessPolicy or None if no policy is set.
        """
        pass
    
    def get_effective_tags(self) -> List[str]:
        """
        Get merged tags from the inheritance chain.
        
        Returns:
            List of tags merged from ancestors and this node.
        """
        pass
    
    def attach_handler(self, method: str, handler: Callable) -> None:
        """
        Attach a handler for a specific HTTP method.
        
        Args:
            method: The HTTP method (GET, POST, etc.).
            handler: The handler callable.
        
        Raises:
            HandlerConflictError: If a handler already exists for this method.
        """
        pass
    
    def get_handler(self, method: str) -> Optional[Callable]:
        """
        Get the handler for a specific HTTP method.
        
        Args:
            method: The HTTP method.
        
        Returns:
            The handler callable or None if not set.
        """
        return self._handlers.get(method.upper())
    
    def ancestors(self) -> Iterator[URLNode]:
        """
        Iterate from this node up to the root.
        
        Yields:
            URLNode instances from parent to root.
        """
        pass
    
    def descendants(self) -> Iterator[URLNode]:
        """
        Iterate over all descendants in depth-first order.
        
        Yields:
            URLNode instances that are descendants of this node.
        """
        pass
```

### Path Utilities

```python
def normalize_path(path: str) -> str:
    """
    Normalize a URL path to canonical form.
    
    - Removes trailing slashes (except for root "/")
    - Collapses multiple consecutive slashes
    - Ensures path starts with "/"
    
    Args:
        path: The path to normalize.
    
    Returns:
        The normalized path string.
    """
    pass


def split_path(path: str) -> List[str]:
    """
    Split a path into its component segments.
    
    Args:
        path: The path to split (e.g., "/api/v1/users").
    
    Returns:
        List of segments (e.g., ["api", "v1", "users"]).
    """
    pass


def is_parameter_segment(segment: str) -> bool:
    """
    Check if a segment is a parameter placeholder.
    
    Args:
        segment: The segment to check.
    
    Returns:
        True if segment matches {param_name} pattern.
    """
    return segment.startswith("{") and segment.endswith("}")


def extract_parameter_name(segment: str) -> Optional[str]:
    """
    Extract the parameter name from a parameter segment.
    
    Args:
        segment: The segment (e.g., "{user_id}").
    
    Returns:
        The parameter name (e.g., "user_id") or None if not a parameter.
    """
    pass
```

## Data Models

### NodeMetadata

```python
@dataclass
class NodeMetadata:
    """
    Structured metadata for a URL node.
    """
    access_policy: Optional[AccessPolicy] = None
    rate_limit: Optional[RateLimit] = None
    tags: List[str] = field(default_factory=list)
    version: Optional[str] = None
    methods: List[str] = field(default_factory=list)
    scopes: List[str] = field(default_factory=list)
    extras: Dict[str, Any] = field(default_factory=dict)
    
    # Inheritance control flags
    replace_tags: bool = False
    replace_scopes: bool = False
```

### RouteExport

```python
@dataclass
class RouteExport:
    """
    Exported route information for documentation and routing.
    """
    path: str
    methods: List[str]
    handler: Optional[str]  # Handler name/reference
    access_policy: Optional[str]  # Policy description
    rate_limit: Optional[str]  # Rate limit description
    tags: List[str]
    version: Optional[str]
    scopes: List[str]
    extras: Dict[str, Any]
```

### SecurityMapEntry

```python
@dataclass
class SecurityMapEntry:
    """
    Security-focused route information for auditing.
    """
    path: str
    methods: List[str]
    handler: str
    access_policy: str
    scopes: List[str]
    rate_limit: str
    summary: str
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Path Uniqueness

*For any* URL Node Map, no two nodes SHALL have the same full path. Adding a node with a duplicate path SHALL raise NodeConflictError.

**Validates: Requirements 1.7, 1.8**

### Property 2: Path Normalization Idempotence

*For any* valid path string, normalizing it multiple times SHALL produce the same result as normalizing it once. `normalize_path(normalize_path(path)) == normalize_path(path)`.

**Validates: Requirements 2.9, 2.10**

### Property 3: Intermediate Node Creation

*For any* path with multiple segments, calling `get_or_create_node(path)` SHALL create all intermediate nodes such that traversing from root to the target node visits each segment in order.

**Validates: Requirements 1.3, 2.6**

### Property 4: Parent-Child Consistency

*For any* node in the tree (except root), the node's parent's children collection SHALL contain the node, and the node's path SHALL equal the parent's path plus "/" plus the node's segment.

**Validates: Requirements 1.6**

### Property 5: Inheritance Resolution

*For any* node and metadata key, `get_effective_metadata(key)` SHALL return the node's own value if set, otherwise the nearest ancestor's value, otherwise None.

**Validates: Requirements 4.1, 4.2**

### Property 6: Tag Merge Semantics

*For any* node with `replace_tags=False`, `get_effective_tags()` SHALL return the union of all ancestor tags plus the node's own tags. With `replace_tags=True`, only the node's own tags SHALL be returned.

**Validates: Requirements 4.4, 4.5**

### Property 7: Rate Limit Restriction

*For any* inheritance chain with rate limits, the effective rate limit SHALL be the most restrictive (lowest) value unless a child explicitly sets `rate_limit=None`.

**Validates: Requirements 4.7**

### Property 8: Traversal Completeness

*For any* URL Node Map, `iterate_nodes()` SHALL yield every node in the tree exactly once, and `iterate_leaves()` SHALL yield exactly those nodes where `is_leaf` is True.

**Validates: Requirements 5.1, 5.2**

### Property 9: Export Consistency

*For any* URL Node Map, `export_routes()` SHALL return one entry for each leaf node, and each entry's metadata SHALL match `get_effective_metadata()` for that node.

**Validates: Requirements 6.2, 6.3, 6.8**

### Property 10: Frozen Immutability

*For any* frozen URL Node Map, all modification operations (add_child, remove_node, set_metadata, attach_handler) SHALL raise FrozenTreeError without modifying the tree.

**Validates: Requirements 8.3, 8.4**

### Property 11: Parameter Segment Detection

*For any* segment string, `is_parameter_segment(segment)` SHALL return True if and only if the segment matches the pattern `{name}` where name is non-empty.

**Validates: Requirements 7.1, 7.2**

### Property 12: Ancestor Chain Integrity

*For any* node, iterating `ancestors()` SHALL yield nodes in order from parent to root, and the final node SHALL be the root node with path "/".

**Validates: Requirements 5.5**

## Error Handling

### NodeNotFoundError

Raised when attempting to access a node that does not exist in the tree.

```python
class NodeNotFoundError(Exception):
    """Raised when a node path does not exist in the tree."""
    
    def __init__(self, path: str):
        self.path = path
        super().__init__(f"Node not found at path: {path}")
```

### NodeConflictError

Raised when attempting to add a node that conflicts with an existing node.

```python
class NodeConflictError(Exception):
    """Raised when a node already exists at the specified path."""
    
    def __init__(self, path: str, existing_node: URLNode):
        self.path = path
        self.existing_node = existing_node
        super().__init__(f"Node already exists at path: {path}")
```

### PathConflictError

Raised when a parameter segment conflicts with a literal segment.

```python
class PathConflictError(Exception):
    """Raised when parameter and literal segments conflict."""
    
    def __init__(self, path: str, parameter_segment: str, literal_segment: str):
        self.path = path
        self.parameter_segment = parameter_segment
        self.literal_segment = literal_segment
        super().__init__(
            f"Parameter segment '{parameter_segment}' conflicts with "
            f"literal segment '{literal_segment}' at path: {path}"
        )
```

### FrozenTreeError

Raised when attempting to modify a frozen tree.

```python
class FrozenTreeError(Exception):
    """Raised when attempting to modify a frozen URL node map."""
    
    def __init__(self):
        super().__init__("Cannot modify frozen URL node map")
```

### HandlerConflictError

Raised when attempting to attach a handler that conflicts with an existing one.

```python
class HandlerConflictError(Exception):
    """Raised when a handler already exists for the specified method."""
    
    def __init__(self, path: str, method: str, existing_handler: Callable):
        self.path = path
        self.method = method
        self.existing_handler = existing_handler
        super().__init__(
            f"Handler already exists for {method} at path: {path}"
        )
```

### NodeHasChildrenError

Raised when attempting to remove a node that has children without recursive flag.

```python
class NodeHasChildrenError(Exception):
    """Raised when attempting to remove a node with children."""
    
    def __init__(self, path: str, child_count: int):
        self.path = path
        self.child_count = child_count
        super().__init__(
            f"Cannot remove node at {path}: has {child_count} children. "
            "Use recursive=True to remove with children."
        )
```

## Testing Strategy

### Unit Tests

Unit tests should cover:

1. **Tree Structure Tests**
   - Verify root node creation
   - Verify intermediate node creation
   - Verify path uniqueness enforcement
   - Verify parent-child relationships

2. **Node Addressing Tests**
   - Verify get_node returns correct node
   - Verify get_or_create_node creates missing nodes
   - Verify has_node returns correct boolean
   - Verify remove_node removes correctly

3. **Metadata Tests**
   - Verify metadata get/set operations
   - Verify inheritance resolution
   - Verify tag merging behavior
   - Verify rate limit restriction logic

4. **Export Tests**
   - Verify export_tree structure
   - Verify export_routes completeness
   - Verify export_security_map filtering

5. **Error Condition Tests**
   - Verify NodeNotFoundError on missing path
   - Verify NodeConflictError on duplicate
   - Verify FrozenTreeError on frozen modification
   - Verify PathConflictError on parameter conflict

### Property-Based Tests

Property-based tests should use the `testbase` framework with minimum 100 iterations per property. Each test should be tagged with the property it validates.

**Testing Framework**: testbase (as specified in AGENTS.md)

**Property Test Configuration**:
- Minimum iterations: 100
- Tag format: `Feature: url-node-map, Property N: <property_text>`

**Generator Requirements**:
- Generate valid path strings (sequences of valid segments)
- Generate valid segment names (alphanumeric, underscores, hyphens)
- Generate parameter segments in `{name}` format
- Generate metadata dictionaries with valid types
- Generate tag lists and scope lists

### Test Organization

Following the repository conventions from AGENTS.md:

```
source/testroots/ccai/tests/singlehost/webworks/urlnodemap/
├── test_urlnodemap.py          # URLNodeMap class tests
├── test_urlnode.py             # URLNode class tests
├── test_path_utils.py          # Path utility function tests
├── test_inheritance.py         # Metadata inheritance tests
├── test_export.py              # Tree export tests
└── test_thread_safety.py       # Concurrency tests
```

### Integration Points

- Integration with `AccessPolicy` for security metadata
- Integration with `RateLimit` for throttling metadata
- Integration with endpoint attachment system
- Integration with router for path matching
