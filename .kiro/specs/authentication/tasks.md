# Implementation Plan: Authentication System

## Overview

This implementation plan breaks down the authentication system into incremental tasks that build upon each other. The implementation follows the existing webworks package structure and integrates with the ASGI/WSGI layers. Each task produces working, testable code.

## Tasks

- [x] 1. Create authentication module structure and core interfaces
  - Create `source/packages/automojo/webworks/authentication/` directory
  - Create `__init__.py` with module exports
  - Implement `AuthenticationStatus` enum
  - Implement `AuthenticationResult` dataclass
  - Implement `Principal` dataclass with `has_role()` and `has_permission()` methods
  - Implement `AuthenticationContext` dataclass with `is_expired` property
  - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5, 11.6_

- [x] 1.1 Write property test for Principal and AuthenticationContext
  - **Property 28: Authentication Context Structure Completeness**
  - **Property 29: Principal Structure Completeness**
  - **Validates: Requirements 11.1, 11.2, 11.3, 11.4, 11.5, 11.6**

- [x] 2. Implement Authenticator protocol and AuthenticationSystem registry
  - Create `authenticator.py` with `Authenticator` protocol
  - Create `system.py` with `AuthenticationSystem` class
  - Implement `register()`, `unregister()` methods
  - Implement `authenticate()` method with priority-based iteration
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6_

- [x] 2.1 Write property test for AuthenticationSystem registry
  - **Property 1: Authenticator Registry Consistency**
  - **Validates: Requirements 1.1, 1.2, 1.3**

- [x] 2.2 Write property test for authentication iteration
  - **Property 2: Authentication Iteration Terminates on Success**
  - **Property 3: Authentication Failure When All Fail**
  - **Validates: Requirements 1.4, 1.5, 1.6**

- [x] 3. Implement IdentityProvider and TokenStore protocols
  - Create `providers.py` with `IdentityProvider` protocol
  - Create `tokenstore.py` with `TokenStore` protocol
  - Implement `InMemoryIdentityProvider` for testing
  - Implement `InMemoryTokenStore` for testing
  - _Requirements: 2.3, 4.2_
  - **Note**: Protocols are defined in basic.py (IdentityProvider) and bearer.py (TokenStore). InMemory implementations are not needed as tests use mock implementations.

- [x] 4. Implement BasicAuthenticator
  - Create `basic.py` with `BasicAuthenticator` class
  - Implement `scheme` property returning "Basic"
  - Implement `can_handle()` to check Authorization header
  - Implement `authenticate()` with Base64 decoding and validation
  - Implement challenge response with WWW-Authenticate header
  - Handle malformed credentials with appropriate errors
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6_

- [x] 4.1 Write property test for Basic auth credential round-trip
  - **Property 4: Basic Auth Credential Round-Trip**
  - **Validates: Requirements 2.1, 2.2**

- [x] 4.2 Write property test for Basic auth validation
  - **Property 5: Basic Auth Valid Credentials Produce Context**
  - **Property 6: Basic Auth Invalid Credentials Produce 401**
  - **Property 7: Basic Auth Malformed Header Produces Error**
  - **Validates: Requirements 2.3, 2.4, 2.5, 2.6**

- [x] 5. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 6. Implement BearerAuthenticator with JWT support
  - Create `bearer.py` with `BearerAuthenticator` class
  - Implement token extraction from Authorization header
  - Implement JWT validation with configurable algorithms
  - Implement signature, expiration, and issuer claim verification
  - Implement token store fallback validation
  - Return appropriate error codes for different failure modes
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7_

- [x] 6.1 Write property test for Bearer token extraction
  - **Property 10: Bearer Token Extraction**
  - **Validates: Requirements 4.1**

- [x] 6.2 Write property test for JWT validation
  - **Property 11: JWT Validation Rejects Invalid Tokens**
  - **Property 12: Valid JWT Produces Context with Claims**
  - **Validates: Requirements 4.4, 4.5, 4.6, 4.7**

- [x] 7. Implement APIKeyAuthenticator
  - Create `apikey.py` with `APIKeyLocation` enum
  - Implement `APIKeyAuthenticator` class
  - Implement key extraction from header, query, and cookie
  - Implement configurable key name
  - Implement key store validation
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7_

- [x] 7.1 Write property test for API key extraction
  - **Property 13: API Key Extraction from All Locations**
  - **Validates: Requirements 5.1, 5.2, 5.3, 5.4**

- [x] 7.2 Write property test for API key validation
  - **Property 14: Valid API Key Produces Context**
  - **Property 15: Invalid API Key Produces 401**
  - **Validates: Requirements 5.5, 5.6, 5.7**

- [x] 8. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 9. Implement SessionAuthenticator
  - Create `session.py` with `SessionData` dataclass
  - Implement `SessionStore` protocol
  - Implement `InMemorySessionStore` for testing
  - Implement `SessionAuthenticator` class
  - Implement secure session ID generation
  - Implement session creation, restoration, and invalidation
  - Implement configurable expiration and renewal
  - Implement secure cookie attributes (HttpOnly, Secure, SameSite)
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7, 8.8_

- [x] 9.1 Write property test for session round-trip
  - **Property 20: Session Round-Trip**
  - **Validates: Requirements 8.1, 8.2, 8.3**

- [x] 9.2 Write property test for session expiration
  - **Property 21: Session Expiration Enforcement**
  - **Validates: Requirements 8.4, 8.8**

- [x] 9.3 Write property test for session cookie security
  - **Property 22: Session Cookie Security Attributes**
  - **Validates: Requirements 8.6**

- [x] 10. Implement DigestAuthenticator
  - Create `digest.py` with `DigestAuthenticator` class
  - Implement nonce generation and validation
  - Implement MD5 and SHA-256 hash algorithm support
  - Implement challenge-response flow
  - Implement nonce freshness validation
  - Implement stale nonce handling with stale=true
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

- [x] 10.1 Write property test for Digest auth challenge
  - **Property 8: Digest Auth Challenge Contains Nonce**
  - **Validates: Requirements 3.1**

- [x] 10.2 Write property test for Digest nonce validation
  - **Property 9: Digest Auth Nonce Freshness Validation**
  - **Validates: Requirements 3.4, 3.6**

- [x] 11. Implement HMACAuthenticator
  - Create `hmac_auth.py` with `HMACAuthenticator` class
  - Implement signature extraction from Authorization header
  - Implement HMAC-SHA256 and HMAC-SHA512 algorithm support
  - Implement canonical request string reconstruction
  - Implement timestamp validation with configurable window
  - Implement configurable signed headers
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7, 9.8_

- [x] 11.1 Write property test for HMAC signature validation
  - **Property 23: HMAC Signature Validation**
  - **Validates: Requirements 9.1, 9.5, 9.6**

- [x] 11.2 Write property test for HMAC timestamp validation
  - **Property 24: HMAC Timestamp Window Enforcement**
  - **Validates: Requirements 9.3, 9.8**

- [x] 12. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 13. Implement OAuth2Authenticator
  - Create `oauth2.py` with OAuth2 token models
  - Implement `OAuth2Token` and `OAuth2AuthorizationCode` dataclasses
  - Implement `OAuth2Authenticator` class
  - Implement Authorization Code flow support
  - Implement Client Credentials flow support
  - Implement Resource Owner Password Credentials flow support
  - Implement state parameter generation and validation
  - Implement PKCE support (code_challenge, code_verifier)
  - Implement token refresh support
  - Implement configurable endpoints
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8, 6.9_

- [x] 13.1 Write property test for OAuth2 state parameter
  - **Property 16: OAuth2 State Parameter Round-Trip**
  - **Validates: Requirements 6.5**

- [x] 13.2 Write property test for PKCE verification
  - **Property 17: PKCE Code Challenge Verification**
  - **Validates: Requirements 6.6**

- [x] 13.3 Write property test for OAuth2 error responses
  - **Property 18: OAuth2 Error Response Format**
  - **Validates: Requirements 6.9**

- [x] 14. Implement OIDCAuthenticator
  - Create `oidc.py` with `OIDCAuthenticator` class extending OAuth2
  - Implement id_token validation
  - Implement signature verification using provider public keys
  - Implement issuer, audience, and expiration claim validation
  - Implement standard claim extraction (sub, name, email)
  - Implement discovery endpoint support
  - Implement UserInfo endpoint support
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7_

- [x] 14.1 Write property test for OIDC claim extraction
  - **Property 19: OIDC ID Token Claim Extraction**
  - **Validates: Requirements 7.4, 7.5**

- [x] 15. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 16. Implement AuthenticationMiddleware
  - Create `middleware.py` with `AuthenticationMiddleware` class
  - Implement ASGI middleware interface
  - Implement request interception before endpoint handlers
  - Implement Authentication_Context attachment to request scope
  - Implement protected path enforcement
  - Implement optional authentication path support
  - Implement exclude path configuration
  - Implement challenge and unauthorized response sending
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.7_

- [x] 16.1 Write property test for middleware context attachment
  - **Property 25: Middleware Context Attachment**
  - **Validates: Requirements 10.1, 10.2**

- [x] 16.2 Write property test for middleware enforcement
  - **Property 26: Middleware Protected Endpoint Enforcement**
  - **Property 27: Middleware Optional Authentication**
  - **Validates: Requirements 10.4, 10.5, 10.7**

- [x] 17. Implement error handling and security features
  - Create `errors.py` with `AuthenticationError` class
  - Implement error response sanitization
  - Implement rate limiting support with configurable limits
  - Implement account lockout policy support
  - Ensure internal errors return safe 500 responses
  - _Requirements: 12.1, 12.3, 12.4, 12.6_

- [x] 17.1 Write property test for error sanitization
  - **Property 31: Error Response Credential Sanitization**
  - **Validates: Requirements 12.1**

- [x] 17.2 Write property test for rate limiting
  - **Property 32: Rate Limiting Enforcement**
  - **Validates: Requirements 12.3**

- [x] 17.3 Write property test for internal error safety
  - **Property 33: Internal Error Response Safety**
  - **Validates: Requirements 12.6**

- [x] 18. Implement cross-scheme context consistency
  - Ensure all authenticators produce consistent Authentication_Context interface
  - Add type hints and protocol compliance verification
  - _Requirements: 11.7_

- [x] 18.1 Write property test for cross-scheme consistency
  - **Property 30: Cross-Scheme Context Interface Consistency**
  - **Validates: Requirements 11.7**

- [x] 19. Integration with Access Policy system
  - Update `accesspolicy.py` to accept Authentication_Context
  - Implement role-based and permission-based policy checks
  - Wire authentication middleware with access policy enforcement
  - _Requirements: 10.6_

- [x] 20. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 21. Update module exports and documentation
  - Update `authentication/__init__.py` with all public exports
  - Update `webworks/__init__.py` to expose authentication module
  - Add docstrings to all public classes and methods

## Notes

- All tasks are required for comprehensive implementation
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties
- Unit tests validate specific examples and edge cases
- The testbase framework is used for all tests (not pytest/unittest/hypothesis)
