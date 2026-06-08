# Requirements Document

## Introduction

This document specifies the requirements for the URL Node Map feature. The URL Node Map provides the foundational hierarchical tree structure for organizing and routing HTTP endpoints in the ccai web framework. It serves as the underlying data structure that endpoints attach to, supporting path-based addressing, inheritance of properties between parent and child nodes, and tree export capabilities for documentation and routing.

The URL Node Map enables declarative endpoint organization where each node in the tree can carry metadata (access policies, rate limits, tags, versions) that cascades to child nodes according to well-defined inheritance rules.

## Glossary

- **URL_Node_Map**: The hierarchical tree structure that organizes URL paths and their associated endpoint metadata.
- **URL_Node**: A single node in the URL tree representing a path segment with associated metadata and optional handler.
- **Root_Node**: The top-level node in the URL tree representing the base path (typically `/`).
- **Leaf_Node**: A terminal node in the URL tree that typically has an associated handler.
- **Path_Segment**: A single component of a URL path between slashes (e.g., `api` in `/api/v1/users`).
- **Node_Address**: A string or path-like identifier used to locate a specific node in the tree.
- **Node_Metadata**: The collection of properties attached to a node (access_policy, rate_limit, tags, version, etc.).
- **Inheritance_Merge**: The process of combining parent node metadata with child node metadata according to defined rules.
- **Tree_Export**: The serialization of the URL tree structure for documentation, routing tables, or security audits.

## Requirements

### Requirement 1: Hierarchical URL Routing Structure

**User Story:** As a framework developer, I want a hierarchical tree structure for URL paths, so that I can organize endpoints in a logical hierarchy that mirrors the URL structure.

#### Acceptance Criteria

1. THE URL_Node_Map SHALL represent URL paths as a hierarchical tree where each path segment corresponds to a node.
2. THE URL_Node_Map SHALL support a single Root_Node representing the base path `/`.
3. WHEN a path such as `/api/v1/users` is added, THE URL_Node_Map SHALL create intermediate nodes for each segment (`api`, `v1`, `users`).
4. THE URL_Node_Map SHALL allow multiple child nodes under any parent node.
5. THE URL_Node_Map SHALL support both intermediate nodes (no handler) and leaf nodes (with handler).
6. WHEN a node is created, THE URL_Node SHALL store its path segment, full path, parent reference, and children collection.
7. THE URL_Node_Map SHALL maintain path uniqueness such that no two nodes have the same full path.
8. IF a duplicate path is added, THEN THE URL_Node_Map SHALL raise a NodeConflictError with details about the existing node.

### Requirement 2: Node Addressing API

**User Story:** As a developer, I want to address nodes by path, so that I can retrieve, modify, or attach to specific locations in the URL tree.

#### Acceptance Criteria

1. THE URL_Node_Map SHALL provide a `get_node(path: str) -> URL_Node` method to retrieve a node by its full path.
2. THE URL_Node_Map SHALL provide a `get_or_create_node(path: str) -> URL_Node` method that returns an existing node or creates the path if it does not exist.
3. THE URL_Node_Map SHALL provide a `has_node(path: str) -> bool` method to check if a path exists in the tree.
4. THE URL_Node_Map SHALL provide a `remove_node(path: str) -> None` method to remove a node and optionally its descendants.
5. WHEN `get_node` is called with a non-existent path, THE method SHALL raise NodeNotFoundError.
6. WHEN `get_or_create_node` is called, THE method SHALL create all intermediate nodes necessary to reach the target path.
7. THE URL_Node SHALL provide a `get_child(segment: str) -> URL_Node` method to retrieve a direct child by segment name.
8. THE URL_Node SHALL provide an `add_child(segment: str, **metadata) -> URL_Node` method to add a new child node.
9. THE URL_Node_Map SHALL support path normalization to handle trailing slashes and redundant separators consistently.
10. WHEN a path with trailing slash is provided, THE URL_Node_Map SHALL normalize it to the canonical form without trailing slash (except for root `/`).

### Requirement 3: Node Metadata and Properties

**User Story:** As a developer, I want to attach metadata to nodes, so that I can define access policies, rate limits, and other properties at any level of the URL hierarchy.

#### Acceptance Criteria

1. THE URL_Node SHALL support storing metadata properties including: `access_policy`, `rate_limit`, `tags`, `version`, `methods`, and `handler`.
2. THE URL_Node SHALL support an `extras` dictionary for custom metadata that endpoint types can extend.
3. WHEN metadata is set on a node, THE URL_Node SHALL validate that the metadata types are correct.
4. THE URL_Node SHALL provide `get_metadata(key: str) -> Any` and `set_metadata(key: str, value: Any) -> None` methods.
5. THE URL_Node SHALL provide a `metadata` property that returns all metadata as a dictionary.
6. WHEN a handler is attached to a node, THE URL_Node SHALL store the handler reference and mark the node as a leaf endpoint.
7. THE URL_Node SHALL support multiple HTTP methods per node, each potentially with different handlers.

### Requirement 4: Inheritance Merge Rules

**User Story:** As a security architect, I want predictable inheritance rules for node metadata, so that child nodes inherit parent properties unless explicitly overridden.

#### Acceptance Criteria

1. WHEN a child node does not define a metadata property, THE child node SHALL inherit the value from its nearest ancestor that defines it.
2. WHEN a child node explicitly defines a metadata property, THE child value SHALL override the inherited value.
3. FOR the `access_policy` property, THE inheritance SHALL follow "parent defaults, child overrides" semantics.
4. FOR list-like properties such as `tags` and `scopes`, THE default behavior SHALL be union (parent values merged with child values).
5. WHEN `replace_tags=True` is set on a child node, THE child tags SHALL fully replace the inherited tags.
6. WHEN `replace_scopes=True` is set on a child node, THE child scopes SHALL fully replace the inherited scopes.
7. FOR the `rate_limit` property, THE most restrictive limit SHALL apply unless the child explicitly sets `rate_limit=None` to opt out.
8. WHEN multiple access policies apply in the inheritance chain, THE combined policy SHALL enforce all constraints via logical AND.
9. THE URL_Node SHALL provide a `get_effective_metadata(key: str) -> Any` method that resolves inheritance.
10. THE URL_Node SHALL provide a `get_effective_access_policy() -> AccessPolicy` method that computes the combined policy from the inheritance chain.

### Requirement 5: Tree Traversal and Iteration

**User Story:** As a framework author, I want to traverse the URL tree, so that I can collect all endpoints for routing or documentation generation.

#### Acceptance Criteria

1. THE URL_Node_Map SHALL provide an `iterate_nodes() -> Iterator[URL_Node]` method for depth-first traversal.
2. THE URL_Node_Map SHALL provide an `iterate_leaves() -> Iterator[URL_Node]` method to iterate only over nodes with handlers.
3. THE URL_Node SHALL provide a `children` property that returns an iterable of child nodes.
4. THE URL_Node SHALL provide a `descendants() -> Iterator[URL_Node]` method for iterating all descendants.
5. THE URL_Node SHALL provide an `ancestors() -> Iterator[URL_Node]` method for iterating from the node up to the root.
6. THE URL_Node_Map SHALL support filtering during traversal by metadata properties (e.g., by tag, by version).

### Requirement 6: Tree Export

**User Story:** As a documentation generator, I want to export the URL tree structure, so that I can produce routing tables, security maps, and API documentation.

#### Acceptance Criteria

1. THE URL_Node_Map SHALL provide an `export_tree() -> dict` method that serializes the tree structure to a dictionary.
2. THE URL_Node_Map SHALL provide an `export_routes() -> list[dict]` method that returns a flat list of all routes with their metadata.
3. THE export SHALL include for each route: `path`, `methods`, `handler`, `access_policy`, `rate_limit`, `tags`, `version`, and `extras`.
4. THE URL_Node_Map SHALL provide an `export_security_map(filter_tag: str = None) -> list[dict]` method for security auditing.
5. THE security map export SHALL include columns: `path`, `methods`, `handler`, `access_policy`, `scopes`, `rate_limit`.
6. WHEN `filter_tag` is provided to `export_security_map`, THE export SHALL include only routes matching that tag.
7. THE URL_Node_Map SHALL support exporting to multiple formats including dict, JSON string, and Markdown table.
8. THE export methods SHALL resolve inheritance so that exported metadata reflects the effective values at each node.

### Requirement 7: Path Pattern Support

**User Story:** As a developer, I want to define path patterns with parameters, so that I can create dynamic routes like `/users/{user_id}`.

#### Acceptance Criteria

1. THE URL_Node_Map SHALL support path segments with parameter placeholders in the format `{param_name}`.
2. WHEN a path segment contains `{param_name}`, THE URL_Node SHALL mark that segment as a parameter segment.
3. THE URL_Node SHALL store parameter metadata including name and optional type hint.
4. THE URL_Node_Map SHALL support wildcard segments using `*` for single-segment wildcards and `**` for multi-segment wildcards.
5. WHEN resolving paths for routing, THE URL_Node_Map SHALL match parameter segments against any value.
6. THE URL_Node_Map SHALL enforce that parameter segments do not conflict with literal segments at the same level.
7. IF a parameter segment conflicts with a literal segment, THEN THE URL_Node_Map SHALL raise PathConflictError.

### Requirement 8: Thread Safety

**User Story:** As a framework author, I want the URL Node Map to be thread-safe, so that it can be safely accessed during concurrent request handling.

#### Acceptance Criteria

1. THE URL_Node_Map SHALL support concurrent read access from multiple threads without locking.
2. WHEN modifications are made to the tree structure, THE URL_Node_Map SHALL use appropriate locking to prevent data corruption.
3. THE URL_Node_Map SHALL provide a `freeze()` method that makes the tree immutable after initial construction.
4. WHEN the tree is frozen, THE URL_Node_Map SHALL raise FrozenTreeError on any modification attempt.
5. THE frozen state SHALL allow lock-free concurrent reads for optimal routing performance.
