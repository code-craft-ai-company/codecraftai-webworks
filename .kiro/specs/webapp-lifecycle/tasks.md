# Implementation Plan: WebApplication Lifecycle

## Overview

Extend the `WebApplication` singleton to orchestrate the full lifecycle of a web application — including configuration, credentials, data profiles, authentication, and web infrastructure wiring — so that applications can be stood up with minimal boilerplate. Implementation adds a `LifecyclePhase` enum, error classes, lifecycle methods, registration APIs (`attach_route`, `attach_blueprint_to_route`), and authentication management to the existing `WebApplication` class. All new source goes in `source/packages/automojo/webworks/persona/`, all tests in `source/testroots/automojo/tests/singlehost/webworks/persona/`.

## Tasks

- [x] 1. Create lifecycle support module with LifecyclePhase enum and error classes
  - [x] 1.1 Create `source/packages/automojo/webworks/persona/lifecycle.py`
    - Define `LifecyclePhase(str, Enum)` with members: `CREATED`, `CONFIGURED`, `CREDENTIALS_LOADED`, `DATA_PROFILES_LOADED`, `DATABASE_READY`, `AUTHENTICATION_READY`, `INFRASTRUCTURE_READY`, `READY`, `SHUTDOWN`
    - Define `LifecycleError(SemanticError)` with `operation`, `required_phase`, `current_phase` attributes and descriptive message
    - Define `BlueprintAlreadyRegisteredError(SemanticError)` with `blueprint_cls` attribute and descriptive message
    - Define `EndpointConflictError(SemanticError)` as a lifecycle-scoped conflict error (wraps routing conflicts from `attach_route`)
    - Import `SemanticError` from `automojo.errors.exceptions`
    - _Requirements: 8.1, 8.2, 2.2, 3.2_

  - [x] 1.2 Write unit tests for LifecyclePhase and error classes
    - Create `source/testroots/automojo/tests/singlehost/webworks/persona/test_lifecycle.py`
    - Test `LifecyclePhase` enum has all expected members in correct order
    - Test `LifecycleError` message includes operation, required phase, and current phase
    - Test `BlueprintAlreadyRegisteredError` message includes blueprint class name
    - Test `EndpointConflictError` message includes path and method details
    - _Requirements: 8.1, 8.2, 2.2, 3.2_

- [x] 2. Extend WebApplication with lifecycle state and phase enforcement
  - [x] 2.1 Add lifecycle private attributes and phase tracking to `WebApplication.__init__`
    - In `source/packages/automojo/webworks/persona/webapplication.py`:
    - Add `_current_phase` initialized to `LifecyclePhase.CREATED`
    - Add `_config`, `_credential_manager`, `_data_profile_manager`, `_auth_system`, `_auth_middleware`, `_router`, `_dispatcher`, `_asgi_app` (all `None`)
    - Add `_pending_routes` list, `_pending_blueprints` list, `_registered_blueprints` set
    - Add `current_phase` read-only property
    - Add `_require_phase(required, operation)` method that raises `LifecycleError` if current phase ordinal is below required
    - Add `_advance_phase(phase)` method that sets `_current_phase`
    - _Requirements: 8.1, 8.2_

  - [x] 2.2 Add read-only properties for all subsystem references
    - Add `router` property — raises `LifecycleError` if phase < `INFRASTRUCTURE_READY`, else returns `_router`
    - Add `dispatcher` property — raises `LifecycleError` if phase < `INFRASTRUCTURE_READY`, else returns `_dispatcher`
    - Add `asgi_app` property — raises `LifecycleError` if phase < `INFRASTRUCTURE_READY`, else returns `_asgi_app`
    - Add `config` property — raises `LifecycleError` if phase < `CONFIGURED`, else returns `_config`
    - Add `credentials` property — raises `LifecycleError` if phase < `CREDENTIALS_LOADED`, else returns `_credential_manager`
    - Add `data_profiles` property — raises `LifecycleError` if phase < `DATA_PROFILES_LOADED`, else returns `_data_profile_manager`
    - Add `auth_system` property — raises `LifecycleError` if phase < `AUTHENTICATION_READY`, else returns `_auth_system`
    - _Requirements: 1.1, 1.2, 1.3, 4.1, 5.1, 6.1, 7.1, 8.2_

  - [x] 2.3 Write property test for lifecycle phase ordering enforcement
    - Create `source/testroots/automojo/tests/singlehost/webworks/persona/test_property_lifecycle.py`
    - **Property 10: Lifecycle phase ordering enforcement**
    - For each pair of (lifecycle method, prerequisite phase), call the method before the prerequisite and verify `LifecycleError` is raised with the correct phase names
    - **Validates: Requirements 8.1, 8.2, 7.4**

- [x] 3. Checkpoint - Verify lifecycle state and phase enforcement
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Implement lifecycle setup methods
  - [x] 4.1 Implement `setup_configuration` method
    - Create `ManagedConfigRegistry` instance, call `setup_from_persona` using persona settings
    - Store in `_config`, advance phase to `CONFIGURED`
    - On failure, raise descriptive error with configuration source path and validation details
    - _Requirements: 4.1, 4.2, 4.3_

  - [x] 4.2 Implement `setup_credentials` method
    - Require phase `CONFIGURED`
    - Use presence directory from persona settings to locate credential stores
    - Store credential manager in `_credential_manager`, advance phase to `CREDENTIALS_LOADED`
    - On failure, raise descriptive error with expected credential store path
    - _Requirements: 5.1, 5.2, 5.3_

  - [x] 4.3 Implement `setup_data_profiles` method
    - Require phase `CREDENTIALS_LOADED`
    - Use presence directory from persona settings to locate data profile sources
    - Store data profile manager in `_data_profile_manager`, advance phase to `DATA_PROFILES_LOADED`
    - On failure, raise descriptive error with expected data profile source path
    - _Requirements: 6.1, 6.2, 6.3_

  - [x] 4.4 Implement `setup_database` method
    - Require phase `DATA_PROFILES_LOADED`
    - Call existing `prepare_database()`, `connect_database()`, `startup_database()`, `ensure_database_ready()` hooks
    - Advance phase to `DATABASE_READY`
    - _Requirements: 8.1_

  - [x] 4.5 Implement `setup_authentication` method
    - Require phase `DATABASE_READY`
    - Create `AuthenticationSystem` instance, store in `_auth_system`
    - Advance phase to `AUTHENTICATION_READY`
    - _Requirements: 7.1, 8.1_

  - [x] 4.6 Implement `setup_infrastructure` method
    - Require phase `AUTHENTICATION_READY`
    - Create `Router` instance, store in `_router`
    - Load all `EndpointDescriptor` instances from `EndpointRegistry` into the Router via `router.load_from_registry`
    - Flush `_pending_routes` into the Router
    - Flush `_pending_blueprints` into the Router (calling `blueprint_cls.register(router=self._router)`)
    - Create `Dispatcher(router=self._router)`, store in `_dispatcher`
    - Create `ASGIApplication` via `create_asgi_application()`, store in `_asgi_app`
    - Wire `self._asgi_app.http_handler.set_handler(self._dispatcher.dispatch_async)`
    - Advance phase to `INFRASTRUCTURE_READY`
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6_

  - [x] 4.7 Write unit tests for lifecycle setup methods
    - Add tests to `source/testroots/automojo/tests/singlehost/webworks/persona/test_webapplication_lifecycle.py`
    - Test `setup_configuration` creates `ManagedConfigRegistry` and calls `setup_from_persona` (mock the registry)
    - Test `setup_credentials` uses presence directory (mock credential manager)
    - Test `setup_data_profiles` uses presence directory (mock data profile manager)
    - Test `setup_database` calls all four database hook methods
    - Test `setup_authentication` creates `AuthenticationSystem`
    - Test `setup_infrastructure` creates Router, Dispatcher, ASGIApplication and wires them
    - Test configuration failure propagates with source path in message
    - Test credential store not found raises error with expected path
    - Test data profile source not found raises error with expected path
    - _Requirements: 4.2, 4.3, 5.2, 5.3, 6.2, 6.3, 8.1_

- [x] 5. Implement startup, shutdown, and verify_readiness
  - [x] 5.1 Implement `startup` method
    - Call `setup_configuration`, `setup_credentials`, `setup_data_profiles`, `setup_database`, `setup_authentication`, `setup_infrastructure`, `verify_readiness` in order
    - Advance phase to `READY` after `verify_readiness`
    - Return `self`
    - _Requirements: 8.1, 8.3_

  - [x] 5.2 Implement `shutdown` method
    - Tear down subsystems in reverse lifecycle order: ASGIApplication, Dispatcher, Router, AuthenticationMiddleware, AuthenticationSystem, database hooks, DataProfile_Manager, Credential_Manager, ManagedConfigRegistry (call `cleanup()`)
    - Set all references to `None`
    - Advance phase to `SHUTDOWN`
    - _Requirements: 8.4_

  - [x] 5.3 Implement `verify_readiness` method
    - Require phase `INFRASTRUCTURE_READY`
    - Verify all critical subsystem references are non-None
    - _Requirements: 8.1_

  - [x] 5.4 Write property test for startup initializes all subsystems
    - In `source/testroots/automojo/tests/singlehost/webworks/persona/test_property_lifecycle.py`
    - **Property 1: Startup initializes all subsystems**
    - For valid persona configurations, after calling `startup()`, verify `router`, `dispatcher`, `asgi_app`, `config`, `credentials`, `data_profiles`, `auth_system` are all non-None and of correct types, and `current_phase` is `READY`
    - **Validates: Requirements 1.1, 1.2, 1.3, 4.1, 5.1, 6.1, 7.1, 8.3**

  - [x] 5.5 Write property test for infrastructure wiring consistency
    - In `source/testroots/automojo/tests/singlehost/webworks/persona/test_property_lifecycle.py`
    - **Property 2: Infrastructure wiring consistency**
    - After `startup()`, verify the Dispatcher's `router` property returns the same Router object as `WebApplication.router` (identity check), and EndpointDescriptors from the EndpointRegistry are matchable via the Router
    - **Validates: Requirements 1.4, 1.5, 1.6**

  - [x] 5.6 Write property test for shutdown releases all resources
    - In `source/testroots/automojo/tests/singlehost/webworks/persona/test_property_lifecycle.py`
    - **Property 11: Shutdown releases all resources**
    - After `startup()` then `shutdown()`, verify `current_phase` is `SHUTDOWN` and config `cleanup()` was called
    - **Validates: Requirements 8.4**

- [x] 6. Checkpoint - Verify startup and shutdown
  - Ensure all tests pass, ask the user if questions arise.

- [x] 7. Implement endpoint registration APIs
  - [x] 7.1 Implement `attach_route` decorator method
    - Returns a decorator that creates an `EndpointDescriptor` from the path, methods, and handler
    - If infrastructure is ready, registers directly into the Router; otherwise queues in `_pending_routes`
    - Catches `RoutingError` from Router conflict detection and re-raises as `EndpointConflictError`
    - Uses `functools.wraps` to preserve original function `__name__` and `__doc__`
    - _Requirements: 2.1, 2.2, 2.3_

  - [x] 7.2 Implement `attach_blueprint_to_route` method
    - Accepts a `RestBlueprint` class
    - Checks `_registered_blueprints` set for duplicates, raises `BlueprintAlreadyRegisteredError` if already registered
    - If infrastructure is ready, calls `blueprint_cls.register(router=self._router)`; otherwise queues in `_pending_blueprints`
    - Adds blueprint class to `_registered_blueprints`
    - _Requirements: 3.1, 3.2, 3.3_

  - [x] 7.3 Write unit tests for attach_route and attach_blueprint_to_route
    - Create `source/testroots/automojo/tests/singlehost/webworks/persona/test_webapplication_routing.py`
    - Test `attach_route` with a specific path and method makes the handler routable after startup
    - Test `attach_route` conflict raises `EndpointConflictError` with descriptive message
    - Test `attach_route` preserves function `__name__` and `__doc__`
    - Test `attach_route` called before startup queues the route and flushes during startup
    - Test `attach_blueprint_to_route` loads all blueprint endpoints after startup
    - Test duplicate blueprint registration raises `BlueprintAlreadyRegisteredError`
    - Test `attach_blueprint_to_route` called before startup queues and flushes during startup
    - _Requirements: 2.1, 2.2, 2.3, 3.1, 3.2, 3.3_

  - [x] 7.4 Write property tests for routing
    - Create `source/testroots/automojo/tests/singlehost/webworks/persona/test_property_routing.py`
    - **Property 3: attach_route registers routable endpoints**
    - Generate valid URL paths and HTTP methods, apply `attach_route`, call `startup()`, verify Router matches each path+method to the correct handler
    - **Validates: Requirements 2.1**
    - **Property 4: attach_route conflict detection**
    - Register a handler at a path+method, attempt to register again, verify `EndpointConflictError` is raised
    - **Validates: Requirements 2.2**
    - **Property 5: attach_route preserves function metadata**
    - Generate functions with `__name__` and `__doc__`, apply `attach_route`, verify both are preserved
    - **Validates: Requirements 2.3**
    - **Property 6: attach_blueprint_to_route registers all blueprint endpoints**
    - Create `RestBlueprint` subclasses with endpoints, call `attach_blueprint_to_route`, call `startup()`, verify all paths are matchable
    - **Validates: Requirements 3.1, 3.3**
    - **Property 7: Duplicate blueprint registration raises error**
    - Call `attach_blueprint_to_route` twice with the same class, verify `BlueprintAlreadyRegisteredError` on second call
    - **Validates: Requirements 3.2**

- [x] 8. Checkpoint - Verify routing APIs
  - Ensure all tests pass, ask the user if questions arise.

- [x] 9. Implement authentication management APIs
  - [x] 9.1 Implement `register_authenticator` method
    - Accept an `Authenticator` instance and optional `priority` integer
    - Delegate to `self._auth_system.register(authenticator, priority=priority)`
    - Require phase `AUTHENTICATION_READY`
    - _Requirements: 7.2_

  - [x] 9.2 Implement `configure_auth_middleware` method
    - Accept `exclude_paths`, `optional_paths`, `path_policies`, `default_policy`, `realm`
    - Require phase `INFRASTRUCTURE_READY` — raise `LifecycleError` if not met
    - Create `AuthenticationMiddleware` wired to `self._asgi_app` and `self._auth_system`
    - Store in `_auth_middleware`, return the middleware instance
    - _Requirements: 7.3, 7.4_

  - [x] 9.3 Write unit tests for authentication management
    - Create `source/testroots/automojo/tests/singlehost/webworks/persona/test_webapplication_auth.py`
    - Test `register_authenticator` adds authenticator to auth system
    - Test `configure_auth_middleware` creates middleware with correct `app` and `auth_system` properties
    - Test `configure_auth_middleware` before infrastructure raises `LifecycleError`
    - _Requirements: 7.1, 7.2, 7.3, 7.4_

  - [x] 9.4 Write property tests for authentication
    - Create `source/testroots/automojo/tests/singlehost/webworks/persona/test_property_auth.py`
    - **Property 8: register_authenticator delegates to AuthenticationSystem**
    - Generate mock Authenticator instances with random scheme names and priorities, call `register_authenticator`, verify the AuthenticationSystem contains each authenticator by scheme
    - **Validates: Requirements 7.2**
    - **Property 9: configure_auth_middleware creates properly wired middleware**
    - Generate random sets of exclude paths, optional paths, policies, and realm strings, call `configure_auth_middleware` after startup, verify the returned middleware's `app` and `auth_system` properties match the WebApplication's
    - **Validates: Requirements 7.3**

- [x] 10. Implement subclass override support and verify extensibility
  - [x] 10.1 Verify `establish_webapp_persona` with `application_cls` creates the correct subclass
    - Ensure the existing `application_cls` parameter on `establish_webapp_persona` works with the new lifecycle methods
    - No code changes expected — this validates the existing mechanism works with the extended class
    - _Requirements: 9.3_

  - [x] 10.2 Write property test for subclass overrides
    - In `source/testroots/automojo/tests/singlehost/webworks/persona/test_property_lifecycle.py`
    - **Property 12: Subclass overrides are invoked during startup**
    - Create subclasses that override each lifecycle method with a tracking wrapper, call `startup()`, verify each override was called in the correct order
    - **Validates: Requirements 9.2**

- [x] 11. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- All tests use the `testbase` framework with `test_` prefix functions and `automojo.testbase.mocking` for mocks
- Test files go in `source/testroots/automojo/tests/singlehost/webworks/persona/`
- Property tests use data-driven iteration over generated inputs (minimum 100 iterations per property) since hypothesis is not used
- Checkpoints ensure incremental validation
- The `reset_webapp_persona` helper in `establish.py` should be used in tests to reset singleton state between test runs
