# Requirements Document

## Introduction

The helloworld test site is the first in a series of test sites designed to exercise the automojo-webworks framework. It provides a minimal, working web application that validates the core request-response pipeline end-to-end. The site lives under `source/testsites/helloworld` and uses the ASGI application layer, the Endpoint registration system, the Router, and the Dispatcher to serve a simple "Hello, World!" response. This site serves as a baseline for verifying that the framework's fundamental wiring — from ASGI scope through routing to response delivery — functions correctly before more complex test sites are built.

## Glossary

- **HelloWorld_Site**: The minimal test web application located at `source/testsites/helloworld` that demonstrates basic webworks capabilities.
- **ASGI_Application**: The `ASGIApplication` class from `automojo.webworks.asgi.application` that receives ASGI scope, receive, and send callables and dispatches to handlers.
- **Endpoint**: The `Endpoint` class from `automojo.webworks.endpoints.endpoint` used to register handler functions with URL paths and HTTP methods via the `attach_at` decorator.
- **Router**: The `Router` class from `automojo.webworks.routing.router` that matches incoming request paths and methods to registered endpoint descriptors.
- **Dispatcher**: The `Dispatcher` class from `automojo.webworks.routing.dispatcher` that executes the matched handler and returns a Response.
- **Response**: The `Response` class from `automojo.webworks.routing.response` used to construct HTTP responses with status code, headers, and body.
- **HTMLResponse**: The `HTMLResponse` subclass of Response that sets `Content-Type: text/html` and accepts a string body.
- **JSONResponse**: The `JSONResponse` subclass of Response that sets `Content-Type: application/json` and serializes a dictionary body.
- **EndpointRegistry**: The global registry from `automojo.webworks.endpoints.registry` where endpoint descriptors are stored after `attach_at` decoration.
- **App_Module**: The `source/testsites/helloworld/app.py` module that serves as the entry point for the helloworld test site, wiring together the ASGI_Application, Router, Dispatcher, and registered Endpoints.

## Requirements

### Requirement 1: Root Endpoint Registration

**User Story:** As a developer, I want the helloworld site to register a root endpoint at `/`, so that I can verify the Endpoint registration and routing pipeline works.

#### Acceptance Criteria

1. THE HelloWorld_Site SHALL register an endpoint handler at the URL path `/` for the HTTP GET method using the Endpoint `attach_at` decorator.
2. WHEN the Router receives a GET request for the path `/`, THE Router SHALL match the request to the registered root endpoint handler.
3. WHEN the root endpoint handler is invoked, THE root endpoint handler SHALL return an HTMLResponse with status code 200 and a body containing the text "Hello, World!".

### Requirement 2: ASGI Application Wiring

**User Story:** As a developer, I want the helloworld site to provide a fully wired ASGI application, so that I can serve the site using any ASGI server.

#### Acceptance Criteria

1. THE App_Module SHALL create an ASGI_Application instance using the `create_asgi_application` factory function.
2. THE App_Module SHALL create a Router instance and load registered endpoints from the EndpointRegistry into the Router.
3. THE App_Module SHALL create a Dispatcher instance configured with the Router.
4. THE App_Module SHALL configure the ASGI_Application HTTP handler to use the Dispatcher for request processing.
5. THE App_Module SHALL expose the ASGI_Application instance as a module-level variable named `app`.

### Requirement 3: Health Check Endpoint

**User Story:** As a developer, I want the helloworld site to include a `/health` endpoint, so that I can verify the site is running and responsive.

#### Acceptance Criteria

1. THE HelloWorld_Site SHALL register an endpoint handler at the URL path `/health` for the HTTP GET method.
2. WHEN the health endpoint handler is invoked, THE health endpoint handler SHALL return a JSONResponse with status code 200 and a body containing `{"status": "ok"}`.

### Requirement 4: Not Found Handling

**User Story:** As a developer, I want the helloworld site to return a proper 404 response for unregistered paths, so that I can verify the framework's error handling pipeline.

#### Acceptance Criteria

1. WHEN the Router receives a request for a path that has no registered endpoint, THE Dispatcher SHALL return a Response with status code 404.
2. WHEN the Router receives a request for a path that has no registered endpoint, THE Response body SHALL contain a message indicating the path was not found.

### Requirement 5: Test Site Directory Structure

**User Story:** As a developer, I want the helloworld site to follow a consistent directory layout under `source/testsites/helloworld`, so that future test sites can follow the same pattern.

#### Acceptance Criteria

1. THE HelloWorld_Site SHALL place the application entry point module at `source/testsites/helloworld/app.py`.
2. THE HelloWorld_Site SHALL place endpoint handler definitions in `source/testsites/helloworld/endpoints/`.
3. THE HelloWorld_Site SHALL include a `source/testsites/helloworld/__init__.py` module to make the site importable as a Python package.
4. THE HelloWorld_Site SHALL include a `source/testsites/helloworld/endpoints/__init__.py` module to make the endpoints directory importable.

### Requirement 6: Method Not Allowed Handling

**User Story:** As a developer, I want the helloworld site to return a 405 response when a registered path is accessed with an unsupported HTTP method, so that I can verify method-based routing enforcement.

#### Acceptance Criteria

1. WHEN the Router receives a POST request for the path `/`, THE Dispatcher SHALL return a Response with status code 405.
2. WHEN the Dispatcher returns a 405 Response, THE Response SHALL include an `Allow` header listing the permitted HTTP methods for the requested path.
