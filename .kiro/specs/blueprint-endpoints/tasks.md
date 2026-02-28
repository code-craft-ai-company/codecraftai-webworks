# Implementation Plan: Blueprint Endpoints

## Overview

This implementation plan creates the Blueprint Endpoints system for grouping related HTTP endpoints under shared parent paths with inherited constraints. The implementation builds on the endpoint-abstractions foundation and follows a bottom-up approach, starting with constraint merge utilities and building up to the full Blueprint class hierarchy.

## Tasks

- [x] 1. Implement constraint merge utilities
  - [x] 1.1 Create `source/packages/automojo/webworks/endpoints/merging.py` module
    - Create `ConstraintMerger` class with static methods
    - _Requirements: 2.3, 2.4, 2.5_
  - [x] 1.2 Implement `merge_access_policies()` method
    - Handle None cases (inherit parent)
    - Implement role/scope union by default
    - Implement replace_roles/replace_scopes flags
    - Combine policies with logical AND
    - _Requirements: 2.6, 2.7, 2.8_
  - [x] 1.3 Implement `merge_rate_limits()` method
    - Handle None cases (inherit parent)
    - Return most restrictive limit
    - Handle explicit opt-out via None
    - _Requirements: 2.9_
  - [x] 1.4 Implement `merge_tags()` method
    - Handle merge=True (append parent to child)
    - Handle replace=True (child replaces parent)
    - Default: child wins if set, else inherit
    - _Requirements: 2.1, 2.2_
  - [x] 1.5 Write property test for security policy composition
    - **Property 7: Security Policy Composition**
    - **Validates: Requirements 2.8**
  - [x] 1.6 Write property test for rate limit stacking
    - **Property 8: Rate Limit Stacking**
    - **Validates: Requirements 2.9**
  - [x] 1.7 Write property test for list field merge behavior
    - **Property 6: List Field Merge Behavior**
    - **Validates: Requirements 2.1, 2.2, 2.6, 2.7**

- [x] 2. Implement Blueprint base class
  - [x] 2.1 Create `source/packages/automojo/webworks/endpoints/blueprint.py` module
    - Import Endpoint base class from endpoint-abstractions
    - _Requirements: 1.2_
  - [x] 2.2 Implement `Blueprint` class extending Endpoint
    - Add class attributes: base_path, base_leaf, merge_tags
    - Add replace_scopes, replace_roles flags
    - Add _registered_descriptors tracking list
    - _Requirements: 1.1, 1.7_
  - [x] 2.3 Implement `_compose_path()` classmethod
    - Compose base_path/base_leaf with child leaf/path
    - Handle absolute path override
    - Normalize path separators
    - _Requirements: 1.7, 4.3, 4.4_
  - [x] 2.4 Implement `_merge_constraints()` classmethod
    - Use ConstraintMerger utilities
    - Apply merge_tags, replace_scopes, replace_roles flags
    - _Requirements: 1.8, 2.3, 2.4, 2.5_
  - [x] 2.5 Write property test for path composition
    - **Property 4: Path Composition**
    - **Validates: Requirements 1.7, 4.3, 4.4**
  - [x] 2.6 Write property test for security constraint inheritance
    - **Property 5: Security Constraint Inheritance**
    - **Validates: Requirements 2.3, 2.4, 2.5, 6.5**

- [x] 3. Checkpoint - Constraint merging complete
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Implement attach_at decorator
  - [x] 4.1 Override `attach_at()` in Blueprint class
    - Compose path using _compose_path()
    - Merge constraints using _merge_constraints()
    - Call parent attach_at with merged values
    - _Requirements: 3.2, 3.6_
  - [x] 4.2 Implement mandatory metadata validation
    - Raise EndpointRegistrationError if leaf and path both missing
    - Include endpoint class and missing_fields in error
    - _Requirements: 3.4_
  - [x] 4.3 Implement class default inheritance
    - Use class attributes when kwargs not provided
    - Override class attributes when kwargs provided
    - Preserve class attributes unchanged
    - _Requirements: 3.8, 3.9, 3.10_
  - [x] 4.4 Implement extra kwargs preservation
    - Store additional kwargs in descriptor.extras
    - Preserve unknown keys for downstream consumers
    - _Requirements: 3.7_
  - [x] 4.5 Write property test for decorator identity preservation
    - **Property 1: Decorator Identity Preservation**
    - **Validates: Requirements 3.1, 5.3**
  - [x] 4.6 Write property test for class default inheritance and override
    - **Property 2: Class Default Inheritance and Override**
    - **Validates: Requirements 3.8, 3.9, 3.10**
  - [x] 4.7 Write property test for extra kwargs preservation
    - **Property 3: Extra Kwargs Preservation**
    - **Validates: Requirements 3.7**

- [x] 5. Implement attach_child method
  - [x] 5.1 Implement `attach_child()` classmethod in Blueprint
    - Accept child_endpoint class and optional overrides
    - Compose path relative to parent base_path/base_leaf
    - _Requirements: 4.2, 4.3_
  - [x] 5.2 Implement child attribute preservation
    - Use child class attributes when overrides not provided
    - Apply overrides only to specified attributes
    - _Requirements: 4.5, 4.6_
  - [x] 5.3 Implement constraint inheritance for attach_child
    - Inherit parent constraints when child doesn't set them
    - Apply merge rules for tags, roles, scopes
    - _Requirements: 6.5, 6.6_
  - [x] 5.4 Write property test for child attribute preservation
    - **Property 14: Child Attribute Preservation**
    - **Validates: Requirements 4.6, 6.6**

- [x] 6. Implement Blueprint register() method
  - [x] 6.1 Implement `register()` classmethod
    - Return list of EndpointDescriptor objects
    - Track registered descriptors in _registered_descriptors
    - _Requirements: 1.4_
  - [x] 6.2 Implement router integration
    - Call router.add_endpoint() for each descriptor when router provided
    - Return descriptors without router interaction when router is None
    - _Requirements: 1.5, 1.6_
  - [x] 6.3 Implement idempotency
    - Return same descriptors on repeated calls
    - Clear and re-register if needed
    - _Requirements: 6.7_
  - [x] 6.4 Write property test for blueprint multi-attachment
    - **Property 12: Blueprint Multi-Attachment**
    - **Validates: Requirements 1.1, 1.3, 1.4**
  - [x] 6.5 Write property test for blueprint router integration
    - **Property 13: Blueprint Router Integration**
    - **Validates: Requirements 1.5, 1.6**
  - [x] 6.6 Write property test for blueprint idempotency
    - **Property 15: Blueprint Idempotency**
    - **Validates: Requirements 6.7**

- [x] 7. Checkpoint - Blueprint class complete
  - Ensure all tests pass, ask the user if questions arise.

- [x] 8. Implement descriptor emission and registry integration
  - [x] 8.1 Implement descriptor emission in attach_at
    - Create EndpointDescriptor with merged metadata
    - Push descriptor to EndpointRegistry
    - _Requirements: 5.1, 5.6_
  - [x] 8.2 Implement conflict detection
    - Check for existing path+method in registry
    - Raise EndpointConflictError naming both handlers
    - _Requirements: 6.3_
  - [x] 8.3 Implement on_conflict="replace" behavior
    - Allow override of existing registration
    - Replace descriptor in registry without error
    - _Requirements: 6.4_
  - [x] 8.4 Write property test for descriptor emission
    - **Property 9: Descriptor Emission**
    - **Validates: Requirements 5.1, 5.6**
  - [x] 8.5 Write property test for conflict detection and replace
    - **Property 11: Conflict Detection and Replace**
    - **Validates: Requirements 3.4, 3.5, 6.3, 6.4**

- [x] 9. Implement handler non-execution guarantee
  - [x] 9.1 Ensure handlers not called during decoration
    - Descriptor generation only, no handler invocation
    - _Requirements: 5.4, 5.7_
  - [x] 9.2 Write property test for handler non-execution
    - **Property 10: Handler Non-Execution During Registration**
    - **Validates: Requirements 5.4, 5.7**

- [x] 10. Update package exports
  - [x] 10.1 Update `source/packages/automojo/webworks/endpoints/__init__.py`
    - Export Blueprint class
    - Export ConstraintMerger class
    - Export BlueprintConfig dataclass
    - _Requirements: 1.1_

- [x] 11. Final checkpoint - All components complete
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties
- Unit tests validate specific examples and edge cases
- Testing framework: testbase (per AGENTS.md)
- Test location: `source/testroots/automojo/tests/singlehost/webworks/blueprints/`
- This feature depends on endpoint-abstractions feature being implemented first

</content>
