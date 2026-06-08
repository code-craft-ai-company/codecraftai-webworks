# Implementation Plan: Middleware Pipeline

## Overview

This implementation plan builds the middleware pipeline feature bottom-up, starting from core data structures (MiddlewareEntry enhancements), through pipeline execution improvements, context, registry, protocol adapters, factory helpers, and built-in middleware, finishing with dispatcher and extensibility integration wiring. The existing `MiddlewarePipeline` in `routing/middleware.py` is enhanced rather than replaced.

## Tasks

- [x] 1. Enhance MiddlewareEntry and MiddlewarePipeline core
  - [x] 1.1 Enhance `MiddlewareEntry` with `priority` and `scope` fields
    - Add `priority: int = 50` and `scope: str = "global"` parameters to `__init__`
    - Add `priority` and `scope` read-only properties
    - Add `as_dict()` method returning `{"name": ..., "priority": ..., "scope": ...}`
    - Update `__repr__` to include priority and scope
    - File: `source/packages/ccai/webworks/routing/middleware.py`
    - _Requirements: 3.8, 14.1_

  - [x] 1.2 Enhance `MiddlewarePipeline.add()` with priority and scope parameters
    - Accept `priority: int = 50` and `scope: str = "global"` parameters
    - Pass priority and scope through to `MiddlewareEntry` constructor
    - Implement priority-based ordering within the same positional group (lower priority executes first)
    - File: `source/packages/ccai/webworks/routing/middleware.py`
    - _Requirements: 3.8_

  - [x] 1.3 Add protocol validation to `MiddlewarePipeline.add()`
    - Validate that middleware conforms to `Middleware` or `AsyncMiddleware` protocol via duck-typing
    - Also accept plain callables with `(request, call_next) -> response` signature
    - Raise `TypeError` with descriptive message if middleware does not conform
    - File: `source/packages/ccai/webworks/routing/middleware.py`
    - _Requirements: 1.5, 1.6, 1.7, 1.8_

  - [x] 1.4 Add serialization methods to `MiddlewarePipeline`
    - Implement `as_dict()` returning list of entry dictionaries via `MiddlewareEntry.as_dict()`
    - Implement `to_json()` serializing `as_dict()` to JSON string
    - Implement `from_config(config, factory_registry=None)` classmethod to reconstruct pipeline from config dicts
    - File: `source/packages/ccai/webworks/routing/middleware.py`
    - _Requirements: 14.1, 14.2, 14.3, 14.4_

  - [x] 1.5 Write property tests for pipeline execution order
    - **Property 1: Pipeline execution preserves registration order**
    - **Validates: Requirements 2.1, 2.2, 2.3, 2.4**

  - [x] 1.6 Write property test for short-circuit behavior
    - **Property 2: Short-circuit bypasses remaining middleware and handler**
    - **Validates: Requirements 2.5**

  - [x] 1.7 Write property test for exception propagation
    - **Property 3: Exception propagation stops pipeline execution**
    - **Validates: Requirements 2.8**

  - [x] 1.8 Write property test for positional insertion
    - **Property 4: Positional insertion places middleware correctly**
    - **Validates: Requirements 3.1, 3.2, 3.3, 3.4**

  - [x] 1.9 Write property test for missing name errors
    - **Property 5: Missing name references raise appropriate errors**
    - **Validates: Requirements 3.5, 3.7**

  - [x] 1.10 Write property test for remove by name
    - **Property 6: Remove by name reduces pipeline correctly**
    - **Validates: Requirements 3.6**

  - [x] 1.11 Write property test for priority ordering
    - **Property 7: Priority ordering within positional groups**
    - **Validates: Requirements 3.8**

  - [x] 1.12 Write property test for get_names consistency
    - **Property 8: get_names matches iteration order**
    - **Validates: Requirements 3.9, 12.1, 12.2**

  - [x] 1.13 Write property test for pipeline repr
    - **Property 19: Pipeline repr contains all middleware names**
    - **Validates: Requirements 12.3**

  - [x] 1.14 Write property test for as_dict structure
    - **Property 24: as_dict returns entries with required keys**
    - **Validates: Requirements 14.1**

  - [x] 1.15 Write property test for serialization round trip
    - **Property 23: Pipeline serialization round trip**
    - **Validates: Requirements 14.4**

  - [x] 1.16 Write property test for protocol validation
    - **Property 26: Protocol validation rejects non-conforming middleware**
    - **Validates: Requirements 1.7, 1.8**

- [x] 2. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 3. Create MiddlewareContext
  - [x] 3.1 Create `MiddlewareContext` class in `routing/middlewarecontext.py`
    - Implement `__init__` accepting `endpoint_descriptor`, `scope`, `config`, and `logger` parameters
    - Implement read-only properties for each field
    - Default `logger` to a module-level logger when `None` is provided
    - Default `endpoint_descriptor` to `None` (middleware executing before routing)
    - File: `source/packages/ccai/webworks/routing/middlewarecontext.py`
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.6_

  - [x] 3.2 Add `middleware_context` attribute to the `Request` class
    - Add `middleware_context: Optional[MiddlewareContext] = None` to the Request constructor
    - Ensure backward compatibility with existing Request usage
    - File: `source/packages/ccai/webworks/routing/request.py`
    - _Requirements: 8.5_

  - [x] 3.3 Write property test for middleware context attached to request
    - **Property 25: Middleware context attached to request during pipeline execution**
    - **Validates: Requirements 8.5**

- [x] 4. Create MiddlewareRegistry
  - [x] 4.1 Create `MiddlewareRegistry` class in `routing/middlewareregistry.py`
    - Implement `__init__` with internal storage for global, blueprint, and route scopes
    - Implement `register()` accepting middleware, name, scope, scope_key, priority, and position
    - Validate middleware conforms to protocol on registration (raise `TypeError` if not)
    - File: `source/packages/ccai/webworks/routing/middlewareregistry.py`
    - _Requirements: 4.1, 4.2, 4.3, 1.7, 1.8_

  - [x] 4.2 Implement `get_middleware_by_scope()` and `compose_pipeline()` methods
    - `get_middleware_by_scope(scope, scope_key)` returns entries for a specific scope
    - `compose_pipeline(blueprint_name, route_path)` composes effective pipeline: global → blueprint → route
    - File: `source/packages/ccai/webworks/routing/middlewareregistry.py`
    - _Requirements: 4.4, 4.5, 4.6, 4.7_

  - [x] 4.3 Implement introspection methods on `MiddlewareRegistry`
    - `list_by_scope()` returns all middleware grouped by scope
    - `export_effective_pipeline(route_path, blueprint_name)` returns ordered list of middleware names
    - `get_registered_components(hook_name)` returns middleware registered via extensibility system
    - File: `source/packages/ccai/webworks/routing/middlewareregistry.py`
    - _Requirements: 12.4, 12.5, 7.6_

  - [x] 4.4 Write property test for scoped pipeline composition order
    - **Property 9: Scoped pipeline composition order**
    - **Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.6, 4.7**

  - [x] 4.5 Write property test for query by scope
    - **Property 10: Query by scope returns correct middleware**
    - **Validates: Requirements 4.5**

  - [x] 4.6 Write property test for registry grouped listing
    - **Property 20: Registry grouped listing partitions by scope**
    - **Validates: Requirements 12.4**

  - [x] 4.7 Write property test for export matches composition
    - **Property 21: Effective pipeline export matches composition**
    - **Validates: Requirements 12.5**

- [x] 5. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 6. Create protocol adapters
  - [x] 6.1 Create ASGI adapters in `routing/middlewareadapters.py`
    - Implement `ASGIMiddlewareAdapter` wrapping ASGI middleware (scope, receive, send) to `AsyncMiddleware` protocol
    - Implement `AsyncMiddlewareToASGI` wrapping `AsyncMiddleware` to ASGI middleware protocol
    - File: `source/packages/ccai/webworks/routing/middlewareadapters.py`
    - _Requirements: 5.1, 5.2, 5.3, 5.5_

  - [x] 6.2 Create WSGI adapters in `routing/middlewareadapters.py`
    - Implement `WSGIMiddlewareAdapter` wrapping WSGI middleware factory to `Middleware` protocol
    - Implement `MiddlewareToWSGI` wrapping `Middleware` to WSGI middleware factory pattern
    - File: `source/packages/ccai/webworks/routing/middlewareadapters.py`
    - _Requirements: 6.1, 6.2, 6.3, 6.5_

  - [x] 6.3 Write unit tests for ASGI and WSGI adapters
    - Test `ASGIMiddlewareAdapter` with mock ASGI middleware
    - Test `AsyncMiddlewareToASGI` with mock AsyncMiddleware
    - Test `WSGIMiddlewareAdapter` with mock WSGI factory
    - Test `MiddlewareToWSGI` with mock Middleware
    - File: `source/testroots/ccai/tests/singlehost/webworks/routing/test_middlewareadapters.py`
    - _Requirements: 5.1, 5.2, 5.3, 6.1, 6.2, 6.3_

- [x] 7. Create middleware factory helpers
  - [x] 7.1 Create `create_middleware()` function in `routing/middlewarefactory.py`
    - Accept a factory callable and config kwargs
    - Invoke factory to produce middleware instance
    - Validate returned instance conforms to `Middleware` or `AsyncMiddleware` protocol
    - Raise `TypeError` if factory returns non-conforming object
    - File: `source/packages/ccai/webworks/routing/middlewarefactory.py`
    - _Requirements: 13.1, 13.2, 13.3, 13.5_

  - [x] 7.2 Integrate factory pattern with `MiddlewareRegistry`
    - When a factory is registered with the registry, invoke it to produce the middleware instance before adding to pipeline
    - File: `source/packages/ccai/webworks/routing/middlewareregistry.py`
    - _Requirements: 13.4_

  - [x] 7.3 Write property test for factory conformance
    - **Property 22: create_middleware returns protocol-conforming instance**
    - **Validates: Requirements 13.2**

- [x] 8. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 9. Implement built-in CORS middleware
  - [x] 9.1 Create `CORSMiddleware` class in `routing/middleware/cors.py`
    - Create `routing/middleware/__init__.py` package
    - Implement `__init__` accepting `allowed_origins`, `allowed_methods`, `allowed_headers`, `exposed_headers`, `allow_credentials`, `max_age`
    - Implement `__call__` handling preflight OPTIONS requests (return 204 with CORS headers, short-circuit)
    - Implement `__call__` adding CORS headers to regular responses for allowed origins
    - Omit CORS headers when origin is not allowed
    - Support wildcard `"*"` origin matching
    - File: `source/packages/ccai/webworks/routing/middleware/cors.py`
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7, 9.8, 9.9, 9.10_

  - [x] 9.2 Write property test for CORS preflight
    - **Property 11: CORS preflight returns 204 without calling handler**
    - **Validates: Requirements 9.7**

  - [x] 9.3 Write property test for CORS origin matching
    - **Property 12: CORS headers present if and only if origin is allowed**
    - **Validates: Requirements 9.8, 9.9, 9.10**

- [x] 10. Implement built-in request logging middleware
  - [x] 10.1 Create `RequestLoggingMiddleware` class in `routing/middleware/logging.py`
    - Implement `__init__` accepting `logger`, `log_level`, `include_headers`, `exclude_paths`
    - Implement `__call__` logging HTTP method, path, query params before handler
    - Log response status code and processing duration after handler
    - Skip logging when request path matches an excluded pattern
    - Include only configured headers in log output
    - File: `source/packages/ccai/webworks/routing/middleware/logging.py`
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7_

  - [x] 10.2 Write property test for logging completeness
    - **Property 13: Request logging captures method, path, status, and duration**
    - **Validates: Requirements 10.1, 10.2**

  - [x] 10.3 Write property test for logging path exclusion
    - **Property 14: Logging path exclusion skips matching requests**
    - **Validates: Requirements 10.6, 10.7**

  - [x] 10.4 Write property test for logging header filtering
    - **Property 15: Logging includes only configured headers**
    - **Validates: Requirements 10.5**

- [x] 11. Implement built-in error normalization middleware
  - [x] 11.1 Create `ErrorNormalizationMiddleware` class in `routing/middleware/errornormalization.py`
    - Implement `__init__` accepting `debug`, `logger`, `exception_map`
    - Implement `__call__` wrapping `call_next` in try/except
    - Map `HTTPException` to its status code, other exceptions to 500
    - Return JSON body with `error`, `error_description`, `status_code` fields
    - Include `traceback` field only when `debug=True`
    - Log all caught exceptions via configured logger
    - Support custom exception-to-status mappings via `exception_map`
    - File: `source/packages/ccai/webworks/routing/middleware/errornormalization.py`
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5, 11.6, 11.7, 11.8_

  - [x] 11.2 Write property test for error normalization JSON structure
    - **Property 16: Error normalization produces structured JSON response**
    - **Validates: Requirements 11.1, 11.2**

  - [x] 11.3 Write property test for error status code mapping
    - **Property 17: Error status code mapping**
    - **Validates: Requirements 11.3, 11.4**

  - [x] 11.4 Write property test for traceback inclusion by debug mode
    - **Property 18: Traceback inclusion determined by debug mode**
    - **Validates: Requirements 11.5, 11.6**

  - [x] 11.5 Write property test for error logging
    - **Property 27: Error normalization logs all caught exceptions**
    - **Validates: Requirements 11.7**

- [ ] 12. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 13. Integrate with Dispatcher and extensibility system
  - [ ] 13.1 Update `Dispatcher` to accept optional `MiddlewareRegistry`
    - Add `MiddlewareRegistry` parameter to `Dispatcher.__init__`
    - Before pipeline execution, compose effective pipeline from registry using matched route's blueprint and path
    - Create `MiddlewareContext` and attach to `request.middleware_context` before pipeline execution
    - Set `endpoint_descriptor` to `None` when no route matched yet
    - File: `source/packages/ccai/webworks/routing/dispatcher.py`
    - _Requirements: 4.4, 8.1, 8.2, 8.3, 8.4, 8.5, 8.6_

  - [ ] 13.2 Bridge extensibility system `register_middleware` hook to `MiddlewareRegistry`
    - When extension registers middleware via `fire_register_middleware`, add to global pipeline in registry
    - Continue validating `process_request` and `process_response` methods per `COMPONENT_REQUIRED_METHODS`
    - Support extensions specifying priority and position via attributes on registered component
    - Implement `get_registered_components(hook_name)` to retrieve extension-registered middleware
    - File: `source/packages/ccai/webworks/routing/middlewareregistry.py`
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6_

  - [ ] 13.3 Integrate middleware pipeline with ASGI application layer
    - Ensure `ASGIApplication` executes composed middleware pipeline before dispatching to endpoint handler
    - Delegate ASGI middleware exceptions to `ASGIApplication` error handler
    - File: `source/packages/ccai/webworks/asgi/httphandler.py`
    - _Requirements: 5.4, 5.6_

  - [ ] 13.4 Integrate middleware pipeline with WSGI application layer
    - Ensure `WSGIApplication` executes composed middleware pipeline before dispatching to endpoint handler
    - Delegate WSGI middleware exceptions to `WSGIApplication` error handler
    - File: `source/packages/ccai/webworks/wsgi/` (relevant files)
    - _Requirements: 6.4, 6.6_

  - [ ] 13.5 Write integration tests for dispatcher and extensibility wiring
    - Test that dispatcher composes pipeline from registry for matched routes
    - Test that middleware context is attached to request during execution
    - Test that extension-registered middleware appears in global pipeline
    - File: `source/testroots/ccai/tests/singlehost/webworks/routing/test_middlewareregistry.py`
    - _Requirements: 4.4, 7.1, 7.2, 8.5_

- [ ] 14. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties from the design document
- Unit tests validate specific examples and edge cases
- Implementation uses Python 3.10+ with testbase framework per repository conventions
- The existing `MiddlewarePipeline` in `routing/middleware.py` is enhanced, not replaced
- Test files go under `source/testroots/ccai/tests/singlehost/webworks/routing/`
- Property test files use the `_properties` suffix convention
