# Implementation Plan: Endpoint Abstractions

## Overview

This implementation plan creates the endpoint abstractions system for declarative HTTP endpoint definition with centralized access control, metadata, and routing configuration. The implementation follows a bottom-up approach, starting with core data structures and building up to the full endpoint class hierarchy.

## Tasks

- [x] 1. Set up project structure and core data models
  - [x] 1.1 Create `source/packages/automojo/webworks/endpoints/` package directory
    - Create `__init__.py` with public exports
    - _Requirements: 1.1, 5.1_
  - [x] 1.2 Implement `Doc` dataclass for documentation metadata
    - Fields: summary, description, deprecated, external_docs
    - _Requirements: 5.1_
  - [x] 1.3 Implement `RateLimit` dataclass
    - Fields: requests, window
    - Implement `most_restrictive()` classmethod for comparing limits
    - _Requirements: 7.8_
  - [x] 1.4 Implement `AccessPolicy` dataclass
    - Fields: roles, scopes, require_auth
    - Implement `merge_with()` method for policy combination
    - Implement `check()` method for user validation
    - _Requirements: 7.1, 7.4, 7.5, 7.6_
  - [x] 1.5 Write property test for AccessPolicy merge behavior
    - **Property 7: Security Policy Composition**
    - **Validates: Requirements 7.6, 7.7**
  - [x] 1.6 Write property test for RateLimit stacking
    - **Property 8: Rate Limit Stacking**
    - **Validates: Requirements 7.8**

- [x] 2. Implement EndpointConstraints and EndpointDescriptor
  - [x] 2.1 Implement `EndpointConstraints` dataclass
    - Fields: access_policy, rate_limit, scopes, roles
    - Implement `merge()` classmethod for constraint inheritance
    - _Requirements: 5.2, 7.1, 7.2, 7.3_
  - [x] 2.2 Implement `EndpointDescriptor` dataclass
    - Fields: handler, module, leaf, path, methods, version, tags, constraints, doc, extras
    - Implement `to_openapi_path()` method
    - Implement `to_security_row()` method
    - _Requirements: 5.1, 5.2, 5.3, 5.4_
  - [x] 2.3 Write property test for constraint inheritance
    - **Property 5: Constraint Inheritance**
    - **Validates: Requirements 3.6, 6.7, 7.1, 7.2, 7.3, 9.4, 10.6**
  - [x] 2.4 Write property test for list field merge behavior
    - **Property 6: List Field Merge Behavior**
    - **Validates: Requirements 3.7, 3.8, 7.4, 7.5, 9.9**

- [x] 3. Implement EndpointRegistry
  - [x] 3.1 Implement `EndpointRegistry` class
    - Module-level singleton pattern
    - `_descriptors` list and `_path_method_index` dict
    - Implement `register()` method with conflict detection
    - Implement `collect()` method
    - Implement `clear()` method for testing
    - _Requirements: 6.1, 6.2, 6.3, 6.5, 6.6_
  - [x] 3.2 Implement `export_security_map()` method
    - Support markdown, csv, json formats
    - Support filter_tag parameter
    - _Requirements: 11.1, 11.2, 11.4_
  - [x] 3.3 Write property test for registration error handling
    - **Property 9: Registration Error Handling**
    - **Validates: Requirements 2.4, 2.5, 6.5, 6.6**

- [x] 4. Checkpoint - Core infrastructure complete
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Implement Endpoint base class
  - [x] 5.1 Implement `Endpoint` class with class-level defaults
    - Attributes: access_policy, rate_limit, methods, version, tags, serializers
    - _Requirements: 1.1, 1.2, 1.5_
  - [x] 5.2 Implement `attach_at()` classmethod decorator
    - Accept all documented parameters (leaf, path, methods, version, tags, etc.)
    - Merge class attributes with kwargs (kwargs override)
    - Create EndpointDescriptor and register with EndpointRegistry
    - Return original function unchanged
    - Raise EndpointRegistrationError on missing mandatory metadata
    - _Requirements: 1.2, 1.3, 1.4, 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7_
  - [x] 5.3 Implement `attach_child()` classmethod
    - Copy child descriptor with optional placement overrides
    - Compute relative paths from parent base_path/base_leaf
    - Merge constraints following inheritance rules
    - _Requirements: 10.2, 10.3, 10.4, 10.5, 10.6_
  - [x] 5.4 Write property test for decorator identity preservation
    - **Property 1: Decorator Identity Preservation**
    - **Validates: Requirements 2.1, 4.3**
  - [x] 5.5 Write property test for attribute inheritance and override
    - **Property 2: Attribute Inheritance and Override**
    - **Validates: Requirements 1.3, 1.4, 1.6, 2.3, 2.8**
  - [x] 5.6 Write property test for descriptor emission
    - **Property 3: Descriptor Emission**
    - **Validates: Requirements 4.1, 6.1**
  - [x] 5.7 Write property test for extra kwargs preservation
    - **Property 4: Extra Kwargs Preservation**
    - **Validates: Requirements 2.7, 5.4**

- [x] 6. Implement Blueprint class
  - [x] 6.1 Implement `Blueprint` class extending Endpoint
    - Attributes: base_path, base_leaf, merge_tags
    - _Requirements: 3.1, 3.2_
  - [x] 6.2 Implement `register()` method
    - Return list of EndpointDescriptor objects
    - Optionally call router.add_endpoint() for each descriptor
    - _Requirements: 3.3, 3.4, 3.5_
  - [x] 6.3 Write property test for path composition
    - **Property 10: Path Composition**
    - **Validates: Requirements 9.6, 9.7, 10.3, 10.4**

- [x] 7. Checkpoint - Base endpoint system complete
  - Ensure all tests pass, ask the user if questions arise.

- [x] 8. Implement RestEndpoint class
  - [x] 8.1 Implement `RestEndpoint` class extending Endpoint
    - Attributes: request_schema, response_schema, error_map, summary, description
    - _Requirements: 8.1, 8.2_
  - [x] 8.2 Implement schema inspection in attach_at
    - Inspect `.model_json_schema()` for Pydantic models
    - Inspect `__dataclass_fields__` for dataclasses
    - Store JSON-schema fragments in descriptor extras["rest"]
    - _Requirements: 8.3, 8.7, 8.8_
  - [x] 8.3 Implement CRUD helper methods
    - `read()` - GET with pre-populated docs
    - `create()` - POST with pre-populated docs
    - `update()` - PUT/PATCH with pre-populated docs
    - `delete()` - DELETE with pre-populated docs
    - _Requirements: 8.4, 8.5_
  - [x] 8.4 Write property test for schema inspection
    - **Property 12: Schema Inspection**
    - **Validates: Requirements 8.7**

- [x] 9. Implement RestBlueprint class
  - [x] 9.1 Implement `RestBlueprint` class extending RestEndpoint
    - Attributes: base_path, base_leaf, replace_tags
    - _Requirements: 9.1, 9.6_
  - [x] 9.2 Implement `register()` method with REST context inheritance
    - Ensure children inherit tags, security schemes, version
    - _Requirements: 9.2, 9.4, 9.5, 9.8_
  - [x] 9.3 Implement `add_crud()` helper method
    - Register standardized CRUD routes (list, create, read, update, delete)
    - Auto-populate documentation fields
    - _Requirements: 9.3_

- [x] 10. Implement exception classes
  - [x] 10.1 Implement `EndpointRegistrationError`
    - Include endpoint reference and missing_fields list
    - _Requirements: 2.4_
  - [x] 10.2 Implement `EndpointConflictError`
    - Include path, method, existing_handler, new_handler
    - _Requirements: 2.5, 6.5_
  - [x] 10.3 Implement `SchemaInspectionError`
    - Include schema type and reason
    - _Requirements: 8.7_

- [x] 11. Implement Router protocol and integration
  - [x] 11.1 Define `Router` Protocol
    - `add_endpoint(descriptor: EndpointDescriptor) -> None`
    - _Requirements: 6.4_
  - [x] 11.2 Write property test for handler non-execution during import
    - **Property 11: Handler Non-Execution During Import**
    - **Validates: Requirements 6.2**
  - [x] 11.3 Write property test for descriptor metadata completeness
    - **Property 13: Descriptor Metadata Completeness**
    - **Validates: Requirements 11.1**

- [x] 12. Final checkpoint - All components complete
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties
- Unit tests validate specific examples and edge cases
- Testing framework: testbase (per AGENTS.md)
- Test location: `source/testroots/automojo/tests/singlehost/webworks/endpoints/`
