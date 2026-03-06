# Requirements Document

## Introduction

This document specifies the requirements for a blueprint test site that demonstrates the usage of the Blueprint system in automojo-webworks. The test site serves as a reference implementation showing two key patterns: (1) creating a Blueprint subclass with multiple pre-configured endpoints registered via `attach_at`, and (2) subclassing a Blueprint to override or extend an existing endpoint. The test site follows the same structural conventions as the existing helloworld test site at `source/testsites/helloworld/`.

## Glossary

- **Blueprint_Test_Site**: A standalone ASGI web application located at `source/testsites/blueprintdemo/` that demonstrates Blueprint usage patterns.
- **Blueprint**: An Endpoint composite class from `automojo.webworks.endpoints.blueprint` that groups related handlers under a shared parent path with inherited constraints.
- **Base_Blueprint**: A Blueprint subclass within the test site that defines multiple pre-configured endpoints under a shared base path using `attach_at`.
- **Extended_Blueprint**: A Blueprint subclass that inherits from Base_Blueprint and overrides or extends one or more endpoint handlers.
- **Endpoint**: The base class from `automojo.webworks.endpoints.endpoint` providing handler registration via the `attach_at` decorator.
- **EndpointRegistry**: The module-level registry from `automojo.webworks.endpoints.registry` that collects EndpointDescriptor records.
- **Router**: The routing component from `automojo.webworks.routing.router` that matches incoming requests to registered endpoint handlers.
- **Dispatcher**: The dispatch component from `automojo.webworks.routing.dispatcher` that invokes matched handlers and returns responses.
- **ASGIApplication**: The ASGI application wrapper from `automojo.webworks.asgi.application` that serves HTTP requests.

## Requirements

### Requirement 1: Test Site Project Structure

**User Story:** As a developer, I want the blueprint test site to follow the same project structure as the helloworld test site, so that I can use it as a consistent reference for building Blueprint-based applications.

#### Acceptance Criteria

1. THE Blueprint_Test_Site SHALL reside at `source/testsites/blueprintdemo/` with an `__init__.py`, an `app.py` module, and an `endpoints/` subpackage.
2. THE Blueprint_Test_Site SHALL contain an `endpoints/__init__.py` and an `endpoints/handlers.py` module that defines the Blueprint subclasses and their handler functions.
3. THE `app.py` module SHALL import the endpoints module to trigger `attach_at` registration, create a Router, load endpoints from the EndpointRegistry, create a Dispatcher, and create an ASGIApplication wired to the Dispatcher.
4. THE `app.py` module SHALL expose module-level `app`, `router`, and `dispatcher` variables for test access.

### Requirement 2: Base Blueprint with Multiple Endpoints

**User Story:** As a developer, I want to see a Blueprint subclass that registers multiple endpoints under a shared base path, so that I can understand how to group related handlers using the Blueprint pattern.

#### Acceptance Criteria

1. THE Base_Blueprint SHALL subclass Blueprint and set a `base_path` class attribute (e.g., `"/api/items"`).
2. THE Base_Blueprint SHALL register a minimum of three handler functions using `Blueprint.attach_at` with distinct leaf segments (e.g., list, detail, create).
3. WHEN the list endpoint receives a GET request, THE handler SHALL return a JSONResponse containing a list of item records with status code 200.
4. WHEN the detail endpoint receives a GET request, THE handler SHALL return a JSONResponse containing a single item record with status code 200.
5. WHEN the create endpoint receives a POST request, THE handler SHALL return a JSONResponse containing the created item record with status code 201.
6. THE Base_Blueprint SHALL set `methods` class attributes so that child handlers inherit default HTTP methods where appropriate.

### Requirement 3: Extended Blueprint with Endpoint Override

**User Story:** As a developer, I want to see a Blueprint subclass that inherits from the Base Blueprint and overrides an endpoint handler, so that I can understand how to extend or customize Blueprint behavior through subclassing.

#### Acceptance Criteria

1. THE Extended_Blueprint SHALL subclass Base_Blueprint and set a different `base_path` class attribute (e.g., `"/api/v2/items"`).
2. THE Extended_Blueprint SHALL override the list endpoint handler to return an augmented response (e.g., items with additional metadata fields) while preserving the same response structure.
3. THE Extended_Blueprint SHALL inherit all non-overridden endpoints from Base_Blueprint without re-declaring them.
4. WHEN the overridden list endpoint receives a GET request, THE handler SHALL return a JSONResponse with the augmented item records and status code 200.
5. THE Extended_Blueprint SHALL demonstrate that constraint inheritance from the parent Blueprint applies to the overridden endpoint.

### Requirement 4: Application Wiring and Routing

**User Story:** As a developer, I want the test site to wire both Blueprints into a single ASGI application, so that I can verify that multiple Blueprints coexist and route correctly.

#### Acceptance Criteria

1. THE Router SHALL contain registered endpoints from both Base_Blueprint and Extended_Blueprint after loading from the EndpointRegistry.
2. WHEN a request matches a Base_Blueprint endpoint path, THE Dispatcher SHALL route the request to the corresponding Base_Blueprint handler.
3. WHEN a request matches an Extended_Blueprint endpoint path, THE Dispatcher SHALL route the request to the corresponding Extended_Blueprint handler.
4. WHEN a request path does not match any registered endpoint, THE Dispatcher SHALL return a response with status code 404.
5. WHEN a request uses an HTTP method not allowed for a matched path, THE Dispatcher SHALL return a response with status code 405 and an Allow header listing permitted methods.

### Requirement 5: Test Coverage for Blueprint Test Site

**User Story:** As a developer, I want tests that validate the blueprint test site handlers, wiring, and routing, so that I can confirm the Blueprint patterns work correctly end-to-end.

#### Acceptance Criteria

1. THE test suite SHALL include handler-level tests that invoke each handler function directly and verify response type, status code, and body content.
2. THE test suite SHALL include wiring tests that verify the module-level `app`, `router`, and `dispatcher` objects are correctly instantiated and configured.
3. THE test suite SHALL include routing tests that verify the Router has registered endpoints for all Base_Blueprint and Extended_Blueprint paths.
4. THE test suite SHALL include dispatch tests that verify the Dispatcher routes requests to the correct handler for each Blueprint path.
5. THE test suite SHALL verify that the Extended_Blueprint overridden endpoint returns the augmented response while non-overridden endpoints return the Base_Blueprint response.
6. THE test suite SHALL reside at `source/testroots/automojo/tests/singlehost/webworks/testsites/blueprintdemo/` mirroring the source hierarchy.
7. THE test suite SHALL use the testbase framework with `test_` prefix functions and `automojo.testbase.mocking` for mock objects.
