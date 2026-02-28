Ye# Implementation Plan: Authentication Blueprints

## Overview

This implementation plan creates authentication blueprint classes that provide pre-built endpoints for each authentication method. The blueprints extend RestBlueprint and integrate with the authentication system created in the authentication spec.

## Tasks

- [x] 1. Create authentication blueprints module structure
  - Create `source/packages/automojo/webworks/authentication/blueprints/` directory
  - Create `__init__.py` with module exports
  - Create `responses.py` with AuthResponse and AuthError dataclasses
  - Create `schemas.py` with common request/response schemas
  - _Requirements: 1.4, 1.6_

- [x] 2. Implement SecurityBlueprint base class
  - Create `security.py` with SecurityBlueprint class
  - Extend RestBlueprint with authentication-specific functionality
  - Implement `configure()` class method for auth_system association
  - Implement `is_endpoint_enabled()` for selective endpoint control
  - Implement `pre_authenticate()` and `post_authenticate()` hooks
  - Implement `format_error()` and `format_success()` response formatters
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6_

- [x] 2.1 Write property test for SecurityBlueprint hooks
  - **Property 5: Pre/Post Authentication Hooks**
  - **Validates: Requirements 1.3**

- [x] 2.2 Write property test for error response format
  - **Property 6: Error Response Format Consistency**
  - **Validates: Requirements 1.4, 1.6, 10.1**

- [x] 3. Implement BasicAuthBlueprint
  - Create `basic.py` with BasicAuthBlueprint class
  - Implement LoginRequest and LoginResponse schemas
  - Implement `login()` endpoint at POST /login
  - Implement `logout()` endpoint at POST /logout
  - Support configurable Identity_Provider
  - Support path customization via base_path
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6_

- [x] 3.1 Write property test for Basic auth endpoints
  - **Property 2: Valid Credentials Produce Success Response**
  - **Property 3: Invalid Credentials Produce 401**
  - **Validates: Requirements 2.2, 2.3**

- [x] 4. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Implement BearerAuthBlueprint
  - Create `bearer.py` with BearerAuthBlueprint class
  - Implement TokenRequest and TokenResponse schemas
  - Implement `token()` endpoint at POST /token
  - Implement `refresh()` endpoint at POST /token/refresh
  - Implement `revoke()` endpoint at POST /token/revoke
  - Implement `introspect()` endpoint at POST /token/introspect
  - Support configurable JWT signing (algorithm, secret, expiration)
  - Implement password, refresh_token, and client_credentials grant types
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8_


- [x] 5.1 Write property test for token expiration configuration
  - **Property 9: Token Expiration Configuration**
  - **Validates: Requirements 3.5**

- [x] 5.2 Write property test for JWT algorithm configuration
  - **Property 10: JWT Algorithm Configuration**
  - **Validates: Requirements 3.6**

- [x] 5.3 Write property test for refresh token flow
  - **Property 11: Refresh Token Flow**
  - **Validates: Requirements 3.7**

- [x] 6. Implement APIKeyBlueprint
  - Create `apikey.py` with APIKeyBlueprint class
  - Implement APIKeyCreateRequest and APIKeyResponse schemas
  - Implement `create_key()` endpoint at POST /keys
  - Implement `list_keys()` endpoint at GET /keys
  - Implement `get_key()` endpoint at GET /keys/{key_id}
  - Implement `revoke_key()` endpoint at DELETE /keys/{key_id}
  - Support configurable key expiration and scoping
  - Ensure key value only returned on creation
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7_

- [x] 6.1 Write property test for API key single exposure
  - **Property 12: API Key Single Exposure**
  - **Validates: Requirements 4.5**

- [x] 7. Implement SessionAuthBlueprint
  - Create `session.py` with SessionAuthBlueprint class
  - Implement SessionLoginRequest and SessionInfo schemas
  - Implement `login()` endpoint at POST /session/login
  - Implement `logout()` endpoint at POST /session/logout
  - Implement `info()` endpoint at GET /session
  - Implement secure cookie setting with HttpOnly, Secure, SameSite
  - Support configurable session duration and renewal
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7_

- [x] 7.1 Write property test for session cookie security
  - **Property 13: Session Cookie Security**
  - **Validates: Requirements 5.4**

- [x] 7.2 Write property test for session invalidation
  - **Property 14: Session Invalidation**
  - **Validates: Requirements 5.5**

- [x] 8. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 9. Implement OAuth2Blueprint
  - Create `oauth2.py` with OAuth2Blueprint class
  - Implement OAuth2AuthorizeRequest and OAuth2TokenRequest schemas
  - Implement `authorize()` endpoint at GET /oauth/authorize
  - Implement `token()` endpoint at POST /oauth/token
  - Implement `callback()` endpoint at GET /oauth/callback
  - Implement `revoke()` endpoint at POST /oauth/revoke
  - Support Authorization Code flow with state validation
  - Support Client Credentials flow
  - Support PKCE (code_challenge, code_verifier)
  - Support configurable redirect URI validation
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8, 6.9_

- [x] 9.1 Write property test for OAuth2 state validation
  - **Property 15: OAuth2 State Validation**
  - **Validates: Requirements 6.4**

- [x] 9.2 Write property test for PKCE verification
  - **Property 16: PKCE Verification**
  - **Validates: Requirements 6.6**

- [x] 9.3 Write property test for OAuth2 error redirect
  - **Property 17: OAuth2 Error Redirect**
  - **Validates: Requirements 6.8**

- [x] 10. Implement OIDCBlueprint
  - Create `oidc.py` with OIDCBlueprint class extending OAuth2Blueprint
  - Implement OIDCDiscovery and UserInfo schemas
  - Implement `discovery()` endpoint at GET /.well-known/openid-configuration
  - Implement `userinfo()` endpoint at GET /userinfo
  - Implement `jwks_endpoint()` endpoint at GET /.well-known/jwks.json
  - Include id_token with standard claims in token responses
  - Support configurable claim mappings
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7_

- [x] 10.1 Write property test for OIDC ID token claims
  - **Property 18: OIDC ID Token Claims**
  - **Validates: Requirements 7.5**

- [x] 11. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 12. Implement blueprint customization features
  - Add method override support in SecurityBlueprint
  - Implement path prefix customization via base_path
  - Implement attach_at decorator for additional endpoints
  - Support custom request/response schemas
  - Implement selective endpoint disabling via enabled_endpoints
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6_

- [x] 12.1 Write property test for method override behavior
  - **Property 19: Method Override Behavior**
  - **Validates: Requirements 8.1, 8.5**

- [x] 12.2 Write property test for path customization
  - **Property 7: Path Customization**
  - **Validates: Requirements 2.5, 8.2**

- [x] 12.3 Write property test for endpoint enable/disable
  - **Property 8: Endpoint Enable/Disable**
  - **Validates: Requirements 2.6, 8.6**

- [x] 12.4 Write property test for custom endpoint addition
  - **Property 20: Custom Endpoint Addition**
  - **Validates: Requirements 8.3**

- [x] 13. Implement blueprint integration with webworks infrastructure
  - Integrate with EndpointRegistry for endpoint registration
  - Integrate with Router for request routing
  - Integrate with Authentication_Middleware
  - Support access policy configuration
  - Support rate limiting configuration
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6_

- [x] 13.1 Write property test for blueprint endpoint registration
  - **Property 1: Blueprint Endpoint Registration**
  - **Validates: Requirements 2.1, 3.1, 3.2, 3.3, 3.8, 4.1, 4.2, 4.3, 4.4, 5.1, 5.2, 5.3, 6.1, 6.2, 6.3, 6.7, 7.2, 7.3, 7.4**

- [x] 13.2 Write property test for router integration
  - **Property 21: Blueprint Router Integration**
  - **Validates: Requirements 9.1, 9.2, 9.6**

- [x] 13.3 Write property test for access policy application
  - **Property 22: Access Policy Application**
  - **Validates: Requirements 9.4**

- [x] 13.4 Write property test for rate limiting
  - **Property 23: Rate Limiting Application**
  - **Validates: Requirements 9.5, 10.4**

- [x] 14. Implement error handling and security features
  - Implement RFC 6749 compliant error responses
  - Implement error response sanitization (no credentials/secrets)
  - Implement internal error handling (no stack traces)
  - Implement CORS configuration support
  - _Requirements: 10.1, 10.2, 10.4, 10.5, 10.6_

- [x] 14.1 Write property test for error sanitization
  - **Property 24: Error Response Sanitization**
  - **Validates: Requirements 10.2, 10.5**

- [x] 14.2 Write property test for CORS configuration
  - **Property 25: CORS Header Configuration**
  - **Validates: Requirements 10.6**

- [x] 15. Implement authenticator configuration property test
  - **Property 4: Authenticator Configuration**
  - **Validates: Requirements 1.2, 1.5, 2.4**

- [x] 16. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 17. Update module exports and documentation
  - Update `blueprints/__init__.py` with all public exports
  - Update `authentication/__init__.py` to expose blueprints module
  - Add docstrings to all public classes and methods

## Notes

- All tasks are required for comprehensive implementation
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties
- The testbase framework is used for all tests (not pytest/unittest/hypothesis)
- This spec depends on the authentication spec being implemented first
