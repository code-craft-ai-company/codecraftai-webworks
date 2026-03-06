# Implementation Plan: Blueprint Test Site

## Overview

Implement a blueprint demo test site at `source/testsites/blueprintdemo/` that demonstrates two Blueprint usage patterns: a base Blueprint with multiple endpoints and an extended Blueprint that overrides one endpoint. Follow the same structural conventions as the existing helloworld test site. Tests use the testbase framework exclusively.

## Tasks

- [x] 1. Create the blueprintdemo test site package structure and endpoint handlers
  - [x] 1.1 Create package init files and the endpoint handlers module
    - Create `source/testsites/blueprintdemo/__init__.py` (empty init)
    - Create `source/testsites/blueprintdemo/endpoints/__init__.py` (empty init)
    - Create `source/testsites/blueprintdemo/endpoints/handlers.py` with:
      - Static `ITEMS` data list
      - `ItemsBlueprint` subclassing `Blueprint` with `base_path = "/api/items"` and `methods = ["GET"]`
      - Three handlers via `Blueprint.attach_at`: `list_items` (GET, leaf="list"), `get_item` (GET, leaf="detail"), `create_item` (POST, leaf="create")
      - Each handler returns a `JSONResponse` with the correct status code and body per the design
    - _Requirements: 1.1, 1.2, 2.1, 2.2, 2.3, 2.4, 2.5, 2.6_

  - [x] 1.2 Add the Extended Blueprint to the handlers module
    - Add `ItemsV2Blueprint` subclassing `ItemsBlueprint` with `base_path = "/api/v2/items"`
    - Override `list_items` via `ItemsBlueprint.attach_at(leaf="list", methods=["GET"])` to return augmented items with `"version": "v2"` and `"total"` field
    - Non-overridden endpoints (`get_item`, `create_item`) remain inherited from `ItemsBlueprint`
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

  - [x] 1.3 Create the app.py application wiring module
    - Create `source/testsites/blueprintdemo/app.py` following the helloworld pattern:
      - Import `blueprintdemo.endpoints.handlers` to trigger `attach_at` registration
      - Create `Router`, call `router.load_from_registry(registry=EndpointRegistry)`
      - Create `Dispatcher(router=router)`
      - Create `app` via `create_asgi_application()`, wire `dispatcher.dispatch_async` to `app.http_handler.set_handler`
      - Expose module-level `app`, `router`, `dispatcher` variables
    - _Requirements: 1.3, 1.4, 4.1_

- [x] 2. Checkpoint - Verify source files
  - Ensure all source files are syntactically correct and imports resolve, ask the user if questions arise.

- [x] 3. Create handler unit tests
  - [x] 3.1 Create test package init files
    - Create `source/testroots/automojo/tests/singlehost/webworks/testsites/blueprintdemo/__init__.py` (empty init)
    - _Requirements: 5.6_

  - [x] 3.2 Create test_handlers.py with direct handler invocation tests
    - Create `source/testroots/automojo/tests/singlehost/webworks/testsites/blueprintdemo/test_handlers.py`
    - Add sys.path setup to include `source/testsites` (same pattern as helloworld tests)
    - Create `_create_mock_request` helper using `automojo.testbase.mocking.Mock`
    - Write tests for `list_items` (base): response type is JSONResponse, status 200, body contains items list
    - Write tests for `get_item`: response type is JSONResponse, status 200, body contains single item
    - Write tests for `create_item`: response type is JSONResponse, status 201, body contains created item with `"created": true`
    - Write tests for `list_items` (v2): response type is JSONResponse, status 200, body contains items with `"version"` field and `"total"` count
    - _Requirements: 5.1, 5.5, 5.7_

- [x] 4. Create app wiring and dispatch tests
  - [x] 4.1 Create test_app_wiring.py with wiring and route registration tests
    - Create `source/testroots/automojo/tests/singlehost/webworks/testsites/blueprintdemo/test_app_wiring.py`
    - Add sys.path setup to include `source/testsites`
    - Test `app` is `ASGIApplication` instance
    - Test `router` is `Router` instance (implicitly, via `get_allowed_methods`)
    - Test `dispatcher` is `Dispatcher` instance
    - Test router has registered endpoints for `/api/items/list`, `/api/items/detail`, `/api/items/create`, `/api/v2/items/list`
    - Test router reports correct allowed methods for each path (GET for list/detail, POST for create)
    - _Requirements: 5.2, 5.3_

  - [x] 4.2 Create test_dispatch.py with dispatcher routing tests
    - Create `source/testroots/automojo/tests/singlehost/webworks/testsites/blueprintdemo/test_dispatch.py`
    - Add sys.path setup to include `source/testsites`
    - Test dispatcher routes `GET /api/items/list` → base list response (status 200, items without version)
    - Test dispatcher routes `GET /api/items/detail` → detail response (status 200, single item)
    - Test dispatcher routes `POST /api/items/create` → create response (status 201, created item)
    - Test dispatcher routes `GET /api/v2/items/list` → v2 list response (status 200, items with version and total)
    - Test dispatcher returns 404 for `/api/items/nonexistent`
    - Test dispatcher returns 405 with Allow header for `POST /api/items/list`
    - _Requirements: 5.4, 5.5_

- [x] 5. Create property-based tests
  - [x] 5.1 Write property test for endpoint response correctness
    - Create `source/testroots/automojo/tests/singlehost/webworks/testsites/blueprintdemo/test_property_blueprint_responses.py`
    - Define `REGISTERED_ENDPOINTS` dict with all endpoint specs (path, method, expected status, expected body JSON)
    - **Property 1: Endpoint Response Correctness**
    - Iterate over all registered endpoints for both blueprints, dispatch request, verify status and body match
    - **Validates: Requirements 4.2, 4.3**

  - [x] 5.2 Write property test for not found consistency
    - In the same `test_property_blueprint_responses.py` file
    - Define `UNREGISTERED_PATHS` list with various non-matching paths
    - **Property 2: Not Found Consistency**
    - Iterate over unregistered paths, dispatch GET request, verify 404 status and non-empty body
    - **Validates: Requirements 4.4**

  - [x] 5.3 Write property test for method not allowed consistency
    - In the same `test_property_blueprint_responses.py` file
    - Define `ALL_HTTP_METHODS` list
    - **Property 3: Method Not Allowed Consistency**
    - Iterate over all registered paths and disallowed methods, verify 405 status and correct Allow header
    - **Validates: Requirements 4.5**

- [x] 6. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- The implementation language is Python, matching the existing codebase
- All tests use the testbase framework with `test_` prefix functions and `automojo.testbase.mocking` for mocks
- Test files mirror the source hierarchy under `source/testroots/automojo/tests/singlehost/webworks/testsites/blueprintdemo/`
- Property tests follow the same exhaustive enumeration pattern as `helloworld/test_property_responses.py`
