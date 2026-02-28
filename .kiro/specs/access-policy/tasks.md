# Implementation Plan: Access Policy and Security

## Overview

This implementation plan creates the access policy and security system for web applications. The implementation follows a bottom-up approach, starting with core data structures (AccessPolicy, Security_Context), then building authentication providers, authorization engine, audit logging, and finally the security middleware and decorators.

## Tasks

- [x] 1. Set up project structure and core data models
  - [x] 1.1 Create `source/packages/automojo/webworks/security/` package directory
    - Create `__init__.py` with public exports
    - _Requirements: 1.1_
  - [x] 1.2 Implement `Security_Context` frozen dataclass
    - Fields: user_id, username, email, roles, scopes, provider, authenticated_at, expires_at, extra
    - Properties: is_authenticated, is_expired
    - Methods: has_role(), has_scope(), has_any_role(), has_all_scopes()
    - Classmethod: guest() for unauthenticated context
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.6, 8.7, 8.8_
  - [x] 1.3 Implement `AccessPolicy` frozen dataclass
    - Fields: roles, scopes, require_auth, constraints
    - Methods: merge_with(), check(), get_denial_reason()
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8_
  - [x] 1.4 Write property test for Security Context Integrity
    - **Property 6: Security Context Integrity**
    - **Validates: Requirements 8.6, 8.7**
  - [x] 1.5 Write property test for Policy Merge Behavior
    - **Property 1: Policy Merge Behavior**
    - **Validates: Requirements 1.5, 3.3, 3.4, 3.5, 3.6, 3.7**
  - [x] 1.6 Write property test for Policy Evaluation
    - **Property 2: Policy Evaluation**
    - **Validates: Requirements 1.6, 1.7, 5.1, 5.3, 5.4, 5.5**

- [x] 2. Implement policy factories and decorators
  - [x] 2.1 Implement policy factory functions
    - `public()` - returns AccessPolicy with require_auth=False
    - `authenticated()` - returns AccessPolicy with require_auth=True
    - `roles(*role_names)` - returns AccessPolicy with specified roles
    - `scopes(*scope_names)` - returns AccessPolicy with specified scopes
    - _Requirements: 6.4, 6.5, 6.6, 6.7, 9.7, 9.8_
  - [x] 2.2 Implement security decorators
    - `@require_auth` - enforces authentication
    - `@require_roles(*roles)` - enforces role requirements
    - `@require_scopes(*scopes)` - enforces scope requirements
    - `@public_endpoint` - marks endpoint as publicly accessible
    - Integrate with EndpointDescriptor system
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6_
  - [x] 2.3 Write property test for Security Decorator Behavior
    - **Property 7: Security Decorator Behavior**
    - **Validates: Requirements 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.8**

- [x] 3. Checkpoint - Core policy system complete
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Implement authentication providers
  - [x] 4.1 Define `Authentication_Provider` protocol
    - Properties: name, priority
    - Methods: authenticate(), authenticate_async()
    - _Requirements: 4.1, 4.2, 4.6_
  - [x] 4.2 Implement `JWTAuthProvider`
    - Extract and validate JWT from Authorization header
    - Return Security_Context on success, None on failure
    - _Requirements: 4.5, 4.7, 4.8_
  - [x] 4.3 Implement `SessionAuthProvider`
    - Extract and validate session from cookie
    - Return Security_Context on success, None on failure
    - _Requirements: 4.5, 4.7, 4.8_
  - [x] 4.4 Implement `APIKeyAuthProvider`
    - Extract and validate API key from header or query param
    - Return Security_Context on success, None on failure
    - _Requirements: 4.5, 4.7, 4.8_
  - [x] 4.5 Implement `Authentication_Manager`
    - Register providers with priority ordering
    - Try providers in order until success or all fail
    - Return guest context if all fail
    - _Requirements: 4.3, 4.4, 4.9_
  - [x] 4.6 Write property test for Authentication Provider Chain
    - **Property 4: Authentication Provider Chain**
    - **Validates: Requirements 4.4, 4.7, 4.8**

- [x] 5. Implement authorization engine
  - [x] 5.1 Implement `AuthorizationResult` dataclass
    - Fields: allowed, reason, policy, context
    - _Requirements: 5.2_
  - [x] 5.2 Implement `AuthorizationRule` protocol
    - Method: evaluate() returning Optional[AuthorizationResult]
    - _Requirements: 5.6_
  - [x] 5.3 Implement `Authorization_Engine` class
    - Method: evaluate() for policy evaluation
    - Method: check_roles() with OR logic
    - Method: check_scopes() with AND logic
    - Support for pre/post hooks
    - Support for custom rules
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.8, 5.9_
  - [x] 5.4 Write property test for Policy Inheritance Security
    - **Property 3: Policy Inheritance Security**
    - **Validates: Requirements 3.1, 3.2, 3.8, 3.9**

- [x] 6. Checkpoint - Authentication and authorization complete
  - Ensure all tests pass, ask the user if questions arise.

- [x] 7. Implement audit logging
  - [x] 7.1 Implement `AuditLevel` enum
    - Values: NONE, FAILURES_ONLY, ALL
    - _Requirements: 7.5_
  - [x] 7.2 Implement `Audit_Entry` dataclass
    - Fields: timestamp, event_type, outcome, user_id, endpoint, policy, reason
    - Fields: ip_address, user_agent, request_id, correlation_id, extra
    - Method: to_json() for serialization
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.7_
  - [x] 7.3 Implement `AuditDestination` protocol
    - Methods: write(), write_async()
    - _Requirements: 7.6_
  - [x] 7.4 Implement `Audit_Logger` class
    - Methods: log_authentication(), log_authorization(), log_violation()
    - Method: add_destination() for multiple destinations
    - Method: query() for historical retrieval
    - Async logging to avoid blocking
    - _Requirements: 7.1, 7.2, 7.3, 7.8, 7.9, 7.10_
  - [x] 7.5 Write property test for Audit Log Completeness
    - **Property 5: Audit Log Completeness**
    - **Validates: Requirements 7.1, 7.2, 7.3, 7.4, 7.7**

- [x] 8. Implement security error handling
  - [x] 8.1 Implement `SecurityError` base class
    - Fields: message, error_code, status_code, details
    - Method: to_response_body()
    - _Requirements: 10.3_
  - [x] 8.2 Implement `AuthenticationError` class
    - Status code: 401
    - Method: get_www_authenticate_header()
    - _Requirements: 10.1, 10.4_
  - [x] 8.3 Implement `AuthorizationError` class
    - Status code: 403
    - Internal reason not exposed in response
    - _Requirements: 10.2, 10.6_
  - [x] 8.4 Implement `PolicyValidationError` class
    - For invalid policy attachments
    - _Requirements: 2.6_
  - [x] 8.5 Implement `SecurityCompletenessError` class
    - List of unprotected endpoints
    - _Requirements: 6.9_
  - [x] 8.6 Write property test for Security Error Response
    - **Property 8: Security Error Response**
    - **Validates: Requirements 10.1, 10.2, 10.3, 10.4, 10.6**

- [x] 9. Implement policy attachment and inheritance
  - [x] 9.1 Implement policy attachment to URL nodes
    - Support access_policy parameter in attach_at() and attach_child()
    - Store policy in EndpointDescriptor constraints field
    - Validate attached policies
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6_
  - [x] 9.2 Implement policy inheritance chain
    - PolicyInheritanceNode for debugging
    - get_chain() for traversal
    - get_effective_policy() for merged policy
    - _Requirements: 3.1, 3.2, 3.10_
  - [x] 9.3 Write property test for Policy Attachment Storage
    - **Property 10: Policy Attachment Storage**
    - **Validates: Requirements 2.2, 2.4, 2.5**

- [x] 10. Checkpoint - Core security features complete
  - Ensure all tests pass, ask the user if questions arise.

- [x] 11. Implement security middleware and default-deny
  - [x] 11.1 Implement `SecurityMiddleware` class
    - Authenticate requests via Authentication_Manager
    - Get policy for endpoint
    - Authorize via Authorization_Engine
    - Log via Audit_Logger
    - Return appropriate error responses
    - _Requirements: 6.1, 6.2_
  - [x] 11.2 Implement default policy configuration
    - default_access_policy setting at application level
    - security_audit_mode for gradual migration
    - _Requirements: 6.3, 6.10_
  - [x] 11.3 Implement security completeness validation
    - Validate all endpoints have policies at startup
    - Raise SecurityCompletenessError or log warnings
    - _Requirements: 6.8, 6.9_
  - [x] 11.4 Write property test for Default-Deny Enforcement
    - **Property 9: Default-Deny Enforcement**
    - **Validates: Requirements 6.1, 6.2**

- [x] 12. Final checkpoint - All security components complete
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties
- Unit tests validate specific examples and edge cases
- Testing framework: testbase (per AGENTS.md)
- Test location: `source/testroots/automojo/tests/singlehost/webworks/security/`
