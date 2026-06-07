# Implementation Plan: HelloWorld Test Site

## Overview

This implementation plan creates the helloworld test site — a minimal ASGI web application that validates the core request-response pipeline of the codecraftai-webworks framework. The implementation follows a bottom-up approach: first creating the directory structure, then the endpoint handlers, then the application wiring, and finally the tests.

## Tasks

- [x] 1. Create test site directory structure
  - [x] 1.1 Create `source/testsites/helloworld/` package
    - Create `source/testsites/__init__.py`
    - Create `source/testsites/helloworld/__init__.py`
    - Create `source/testsites/helloworld/endpoints/__init__.py`
    - _Requirements: 5.1, 5.2, 5.3, 5.4_

- [x] 2. Implement endpoint handlers
  - [x] 2.1 Create `source/testsites/helloworld/endpoints/handlers.py`
    - Implement `hello_world(request) -> HTMLResponse` decorated with `@Endpoint.attach_at(path="/", methods=["GET"])`
    - Implement `health_check(request) -> JSONResponse` decorated with `@Endpoint.attach_at(path="/health", methods=["GET"])`
    - _Requirements: 1.1, 1.3, 3.1, 3.2_

- [x] 3. Implement application wiring
  - [x] 3.1 Create `source/testsites/helloworld/app.py`
    - Import `endpoints.handlers` to trigger registration
    - Create Router and load from EndpointRegistry
    - Create Dispatcher with the Router
    - Create ASGIApplication via `create_asgi_application()`
    - Set HTTP handler to use `dispatcher.dispatch_async`
    - Expose `app` as module-level variable
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [x] 4. Enhance Dispatcher for 405 Method Not Allowed
  - [x] 4.1 Add `get_allowed_methods(path)` method to Router
    - Check all registered routes for the given path
    - Return list of HTTP methods registered for that path
    - Return empty list if path has no registrations
    - _Requirements: 6.1, 6.2_

  - [x] 4.2 Update Dispatcher to differentiate 404 vs 405
    - When `router.match()` returns None, call `router.get_allowed_methods(request.path)`
    - If allowed methods exist, raise `MethodNotAllowed(allowed=allowed_methods)`
    - If no allowed methods, raise `NotFound()` as before
    - Apply to both `dispatch()` and `dispatch_async()` methods
    - _Requirements: 6.1, 6.2_

- [x] 5. Write unit tests for endpoint handlers
  - [x] 5.1 Create `source/testroots/ccai/tests/singlehost/webworks/testsites/helloworld/test_handlers.py`
    - Test `hello_world` returns HTMLResponse with status 200 and body "Hello, World!"
    - Test `health_check` returns JSONResponse with status 200 and body `{"status": "ok"}`
    - _Requirements: 1.3, 3.2_

- [x] 6. Write unit tests for application wiring
  - [x] 6.1 Create `source/testroots/ccai/tests/singlehost/webworks/testsites/helloworld/test_app_wiring.py`
    - Test `app` is an ASGIApplication instance
    - Test Router has registered endpoints for `/` and `/health`
    - Test Dispatcher dispatches GET `/` to hello_world handler
    - Test Dispatcher dispatches GET `/health` to health_check handler
    - Test Dispatcher returns 404 for unregistered path
    - Test Dispatcher returns 405 for POST to `/` with Allow header
    - _Requirements: 2.5, 4.1, 4.2, 6.1, 6.2_

- [x] 7. Write property tests for response correctness
  - [x] 7.1 Create `source/testroots/ccai/tests/singlehost/webworks/testsites/helloworld/test_property_responses.py`
    - **Property 1: Endpoint Response Correctness**
    - **Property 2: Not Found Consistency**
    - **Property 3: Method Not Allowed Consistency**
    - **Validates: Requirements 1.3, 3.2, 4.1, 4.2, 6.1, 6.2**

- [x] 8. Checkpoint - Verify complete implementation
  - Run all tests and ensure they pass
  - Verify the helloworld site can be imported and the `app` variable is accessible

## Notes

- All tests use the `testbase` framework per repository conventions
- Tests mirror the source hierarchy under `source/testroots/ccai/tests/singlehost/webworks/testsites/helloworld/`
- The 405 enhancement (Task 4) modifies framework code in `Router` and `Dispatcher` — these changes benefit all sites, not just helloworld
- Endpoint handlers are synchronous; the Dispatcher handles async wrapping transparently
