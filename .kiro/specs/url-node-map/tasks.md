# Implementation Plan: URL Node Map

## Overview

This implementation plan creates the URL Node Map feature, which provides the foundational hierarchical tree structure for organizing HTTP endpoints in the ccai web framework. The implementation follows a bottom-up approach, starting with path utilities, then building the core node and map classes, followed by metadata inheritance, and finally export capabilities.

## Tasks

- [x] 1. Create path utility functions
  - [x] 1.1 Create `source/packages/ccai/webworks/urlnodemap/pathutils.py`
    - Implement `normalize_path(path: str) -> str` function
    - Implement `split_path(path: str) -> List[str]` function
    - Implement `is_parameter_segment(segment: str) -> bool` function
    - Implement `extract_parameter_name(segment: str) -> Optional[str]` function
    - _Requirements: 2.9, 2.10, 7.1, 7.2_
  - [x] 1.2 Write property test for path normalization idempotence
    - **Property 2: Path Normalization Idempotence**
    - **Validates: Requirements 2.9, 2.10**
  - [x] 1.3 Write property test for parameter segment detection
    - **Property 11: Parameter Segment Detection**
    - **Validates: Requirements 7.1, 7.2**

- [x] 2. Create exception classes
  - [x] 2.1 Create `source/packages/ccai/webworks/urlnodemap/exceptions.py`
    - Implement `NodeNotFoundError` exception
    - Implement `NodeConflictError` exception
    - Implement `PathConflictError` exception
    - Implement `FrozenTreeError` exception
    - Implement `HandlerConflictError` exception
    - Implement `NodeHasChildrenError` exception
    - _Requirements: 1.8, 2.5, 7.7, 8.4_

- [x] 3. Create URLNode class
  - [x] 3.1 Create `source/packages/ccai/webworks/urlnodemap/urlnode.py`
    - Implement `URLNode` class with segment, path, parent, children properties
    - Implement parameter segment detection (`is_parameter`, `parameter_name`)
    - Implement `get_child(segment: str) -> URLNode` method
    - Implement `add_child(segment: str, **metadata) -> URLNode` method
    - _Requirements: 1.6, 2.7, 2.8, 7.2, 7.3_
  - [x] 3.2 Write property test for parent-child consistency
    - **Property 4: Parent-Child Consistency**
    - **Validates: Requirements 1.6**

- [x] 4. Implement node metadata operations
  - [x] 4.1 Add metadata methods to URLNode
    - Implement `get_metadata(key: str) -> Any` method
    - Implement `set_metadata(key: str, value: Any) -> None` method
    - Implement `metadata` property returning dictionary copy
    - _Requirements: 3.1, 3.2, 3.4, 3.5_
  - [x] 4.2 Add handler attachment to URLNode
    - Implement `attach_handler(method: str, handler: Callable) -> None` method
    - Implement `get_handler(method: str) -> Optional[Callable]` method
    - Implement `is_leaf` property
    - _Requirements: 3.6, 3.7_

- [x] 5. Create URLNodeMap class
  - [x] 5.1 Create `source/packages/ccai/webworks/urlnodemap/urlnodemap.py`
    - Implement `URLNodeMap` class with root node initialization
    - Implement `get_node(path: str) -> URLNode` method
    - Implement `get_or_create_node(path: str) -> URLNode` method
    - Implement `has_node(path: str) -> bool` method
    - Implement `remove_node(path: str, recursive: bool) -> None` method
    - _Requirements: 1.1, 1.2, 1.3, 1.7, 2.1, 2.2, 2.3, 2.4_
  - [x] 5.2 Write property test for path uniqueness
    - **Property 1: Path Uniqueness**
    - **Validates: Requirements 1.7, 1.8**
  - [x] 5.3 Write property test for intermediate node creation
    - **Property 3: Intermediate Node Creation**
    - **Validates: Requirements 1.3, 2.6**

- [x] 6. Checkpoint - Ensure core structure tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 7. Implement metadata inheritance
  - [x] 7.1 Add inheritance methods to URLNode
    - Implement `get_effective_metadata(key: str) -> Any` method
    - Implement `get_effective_access_policy() -> Optional[AccessPolicy]` method
    - Implement `get_effective_tags() -> List[str]` method with merge logic
    - Implement `get_effective_rate_limit() -> Optional[RateLimit]` method
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8, 4.9, 4.10_
  - [x] 7.2 Write property test for inheritance resolution
    - **Property 5: Inheritance Resolution**
    - **Validates: Requirements 4.1, 4.2**
  - [x] 7.3 Write property test for tag merge semantics
    - **Property 6: Tag Merge Semantics**
    - **Validates: Requirements 4.4, 4.5**
  - [x] 7.4 Write property test for rate limit restriction
    - **Property 7: Rate Limit Restriction**
    - **Validates: Requirements 4.7**

- [x] 8. Implement tree traversal
  - [x] 8.1 Add traversal methods to URLNode
    - Implement `ancestors() -> Iterator[URLNode]` method
    - Implement `descendants() -> Iterator[URLNode]` method
    - _Requirements: 5.4, 5.5_
  - [x] 8.2 Add traversal methods to URLNodeMap
    - Implement `iterate_nodes() -> Iterator[URLNode]` method
    - Implement `iterate_leaves() -> Iterator[URLNode]` method
    - _Requirements: 5.1, 5.2, 5.3, 5.6_
  - [x] 8.3 Write property test for traversal completeness
    - **Property 8: Traversal Completeness**
    - **Validates: Requirements 5.1, 5.2**
  - [x] 8.4 Write property test for ancestor chain integrity
    - **Property 12: Ancestor Chain Integrity**
    - **Validates: Requirements 5.5**

- [x] 9. Implement tree export
  - [x] 9.1 Add export methods to URLNodeMap
    - Implement `export_tree() -> dict` method
    - Implement `export_routes() -> list[dict]` method
    - Implement `export_security_map(filter_tag: str = None) -> list[dict]` method
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8_
  - [x] 9.2 Write property test for export consistency
    - **Property 9: Export Consistency**
    - **Validates: Requirements 6.2, 6.3, 6.8**

- [x] 10. Implement thread safety
  - [x] 10.1 Add thread safety to URLNodeMap
    - Add RLock for modification operations
    - Implement `freeze() -> None` method
    - Add frozen state checks to all modification methods
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_
  - [x] 10.2 Write property test for frozen immutability
    - **Property 10: Frozen Immutability**
    - **Validates: Requirements 8.3, 8.4**

- [x] 11. Create package structure and exports
  - [x] 11.1 Create `source/packages/ccai/webworks/urlnodemap/__init__.py`
    - Export `URLNodeMap`, `URLNode` classes
    - Export exception classes
    - Export path utility functions
    - _Requirements: All_

- [x] 12. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties
- Unit tests validate specific examples and edge cases
- Use the `testbase` framework for all tests as specified in AGENTS.md
- Test files should be placed in `source/testroots/ccai/tests/singlehost/webworks/urlnodemap/`
