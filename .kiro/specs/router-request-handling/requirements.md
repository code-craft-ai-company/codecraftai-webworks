# Requirements Document

## Introduction

This document specifies the requirements for the Router and Request Handling feature. This feature provides the core routing infrastructure that matches incoming HTTP requests to registered endpoint handlers, manages request/response primitives, and orchestrates middleware pipelines for cross-cutting concerns.

The router integrates with the EndpointRegistry to consume endpoint descriptors and build an efficient URL matching tree. It provides a clean abstraction over WSGI/ASGI request objects and supports middleware composition for authentication, logging, error handling, and other cross-cutting concerns.

## Glossary

- **Router**: The core component that matches incoming HTTP requests to registered endpoint handlers based on URL path and HTTP method.
- **Matcher**: A component that performs URL pattern matching against registered routes, supporting static paths, parameterized segments, and wildcards.
- **Request**: An abstraction over the raw WSGI/ASGI request object providing a clean API for accessing headers, body, query parameters, and path parameters.
- **Response**: An abstraction for building HTTP responses with status codes, headers, and body content.
- **Middleware**: A composable component that wraps request handling to provide cross-cutting functionality such as authentication, logging, or error handling.
- **MiddlewarePipeline**: An ordered chain of middleware components that process requests before and after the endpoint handler.
- **RouteMatch**: The result of a successful URL match containing the matched handler, path parameters, and associated endpoint descriptor.
- **PathParameter**: A dynamic segment in a URL pattern (e.g., `/users/{id}`) that captures values from the request path.
- **EndpointDescriptor**: A dataclass record from the endpoint-abstractions feature containing handler reference and metadata.
- **URLNode**: A node in the URL tree from the url-node-map feature representing a path segment.

## Requirements

### Requirement 1: Router Core

**User Story:** As a framework author, I want a router that consumes endpoint descriptors and matches requests to handlers, so that incoming HTTP requests are dispatched to the correct endpoint.

#### Acceptance Criteria

1. THE Router class SHALL consume EndpointDescriptor objects via `add_endpoint(descriptor: EndpointDescriptor) -> None`.
2. THE Router class SHALL build an internal URL matching tree from registered descriptors.
3. WHEN a request arrives, THE Router SHALL match the request path and method against registered routes.
4. WHEN a match is found, THE Router SHALL return a RouteMatch containing the handler, path parameters, and descriptor.
5. WHEN no match is found, THE Router SHALL return None or raise a RoutingError depending on configuration.
6. THE Router SHALL support multiple handlers for the same path with different HTTP methods.
7. THE Router SHALL integrate with the EndpointRegistry via `load_from_registry(registry: EndpointRegistry) -> None` to bulk-load descriptors.

### Requirement 2: URL Pattern Matching

**User Story:** As a developer, I want flexible URL pattern matching with support for parameters and wildcards, so that I can define dynamic routes that capture values from the URL.

#### Acceptance Criteria

1. THE Matcher SHALL support static path segments (e.g., `/api/users`).
2. THE Matcher SHALL support parameterized path segments using curly braces (e.g., `/users/{id}`).
3. THE Matcher SHALL support typed parameters with converters (e.g., `/users/{id:int}`, `/posts/{slug:str}`).
4. THE Matcher SHALL support wildcard segments that match any remaining path (e.g., `/files/{path:path}`).
5. THE Matcher SHALL support optional trailing slashes based on configuration.
6. WHEN multiple routes could match, THE Matcher SHALL prefer more specific routes over parameterized routes.
7. WHEN multiple routes could match with equal specificity, THE Matcher SHALL use registration order as tiebreaker.
8. THE Matcher SHALL extract path parameters and return them in the RouteMatch.

### Requirement 3: Request Primitive

**User Story:** As an endpoint handler author, I want a clean request abstraction, so that I can access request data without dealing with raw WSGI/ASGI details.

#### Acceptance Criteria

1. THE Request class SHALL provide access to the HTTP method via `method` property.
2. THE Request class SHALL provide access to the request path via `path` property.
3. THE Request class SHALL provide access to query parameters via `query_params` property returning a dict-like object.
4. THE Request class SHALL provide access to headers via `headers` property returning a case-insensitive dict-like object.
5. THE Request class SHALL provide access to the request body via `body` property returning bytes.
6. THE Request class SHALL provide `json()` method to parse JSON body content.
7. THE Request class SHALL provide `form()` method to parse form-encoded body content.
8. THE Request class SHALL provide access to path parameters via `path_params` property (populated after routing).
9. THE Request class SHALL provide access to cookies via `cookies` property.
10. THE Request class SHALL provide `url` property returning the full request URL.
11. THE Request class SHALL be constructible from both WSGI environ dict and ASGI scope dict.

### Requirement 4: Response Primitive

**User Story:** As an endpoint handler author, I want a clean response abstraction, so that I can build HTTP responses without dealing with raw WSGI/ASGI details.

#### Acceptance Criteria

1. THE Response class SHALL accept status_code, headers, and body in its constructor.
2. THE Response class SHALL provide `set_header(name: str, value: str)` method.
3. THE Response class SHALL provide `set_cookie(name: str, value: str, **options)` method.
4. THE Response class SHALL provide `delete_cookie(name: str)` method.
5. THE Response class SHALL be convertible to WSGI response format via `to_wsgi()` method.
6. THE Response class SHALL be convertible to ASGI response format via `to_asgi()` method.
7. THE system SHALL provide `JSONResponse` subclass for JSON content with automatic Content-Type header.
8. THE system SHALL provide `HTMLResponse` subclass for HTML content with automatic Content-Type header.
9. THE system SHALL provide `RedirectResponse` subclass for HTTP redirects.
10. THE system SHALL provide `StreamingResponse` subclass for streaming large responses.

### Requirement 5: Middleware Protocol

**User Story:** As a framework author, I want a middleware protocol for composable request processing, so that cross-cutting concerns can be implemented as reusable components.

#### Acceptance Criteria

1. THE Middleware protocol SHALL define `__call__(request: Request, call_next: Callable) -> Response`.
2. THE Middleware SHALL receive the request and a `call_next` callable to invoke the next middleware or handler.
3. THE Middleware SHALL be able to modify the request before calling `call_next`.
4. THE Middleware SHALL be able to modify the response after calling `call_next`.
5. THE Middleware SHALL be able to short-circuit the pipeline by returning a response without calling `call_next`.
6. THE Middleware SHALL support both synchronous and asynchronous implementations.

### Requirement 6: Middleware Pipeline

**User Story:** As a framework author, I want an ordered middleware pipeline, so that middleware components execute in a predictable order around endpoint handlers.

#### Acceptance Criteria

1. THE MiddlewarePipeline class SHALL maintain an ordered list of middleware components.
2. THE MiddlewarePipeline class SHALL provide `add(middleware: Middleware, position: str = "end")` method.
3. WHEN `position="start"` is specified, THE middleware SHALL be added at the beginning of the pipeline.
4. WHEN `position="end"` is specified, THE middleware SHALL be added at the end of the pipeline.
5. WHEN `position="before:<name>"` is specified, THE middleware SHALL be added before the named middleware.
6. WHEN `position="after:<name>"` is specified, THE middleware SHALL be added after the named middleware.
7. THE MiddlewarePipeline class SHALL provide `remove(name: str)` method to remove middleware by name.
8. THE MiddlewarePipeline class SHALL execute middleware in order, with each middleware wrapping the next.
9. THE MiddlewarePipeline class SHALL support named middleware for positional insertion and removal.

### Requirement 7: Route Match Result

**User Story:** As a framework author, I want a structured route match result, so that the dispatcher has all information needed to invoke the handler.

#### Acceptance Criteria

1. THE RouteMatch class SHALL be a dataclass with fields: handler, path_params, descriptor, and matched_path.
2. THE `handler` field SHALL contain the callable endpoint handler.
3. THE `path_params` field SHALL contain a dict of extracted path parameters.
4. THE `descriptor` field SHALL contain the EndpointDescriptor for accessing metadata.
5. THE `matched_path` field SHALL contain the URL pattern that matched.

### Requirement 8: Request Dispatcher

**User Story:** As a framework author, I want a dispatcher that orchestrates routing and middleware execution, so that requests flow through the complete handling pipeline.

#### Acceptance Criteria

1. THE Dispatcher class SHALL accept a Router and MiddlewarePipeline in its constructor.
2. THE Dispatcher class SHALL provide `dispatch(request: Request) -> Response` method.
3. WHEN `dispatch` is called, THE Dispatcher SHALL first route the request to find a matching handler.
4. WHEN a match is found, THE Dispatcher SHALL populate `request.path_params` from the RouteMatch.
5. WHEN a match is found, THE Dispatcher SHALL execute the middleware pipeline with the handler as the final callable.
6. WHEN no match is found, THE Dispatcher SHALL return a 404 Not Found response.
7. WHEN the handler raises an exception, THE Dispatcher SHALL allow middleware to handle it or return a 500 response.
8. THE Dispatcher SHALL support both synchronous and asynchronous request handling.

### Requirement 9: Error Responses

**User Story:** As a developer, I want consistent error responses, so that clients receive predictable error information when requests fail.

#### Acceptance Criteria

1. THE system SHALL provide `HTTPException` class with status_code, detail, and headers fields.
2. WHEN an HTTPException is raised, THE Dispatcher SHALL convert it to an appropriate HTTP response.
3. THE system SHALL provide standard exception subclasses: `NotFound`, `BadRequest`, `Unauthorized`, `Forbidden`, `MethodNotAllowed`.
4. THE error response format SHALL be configurable (JSON, HTML, or custom).
5. WHEN an unhandled exception occurs, THE Dispatcher SHALL return a 500 Internal Server Error response.
6. THE 500 response SHALL NOT expose internal error details in production mode.
7. THE 500 response SHALL include stack traces in debug mode.

### Requirement 10: Path Parameter Converters

**User Story:** As a developer, I want typed path parameters, so that parameter values are automatically converted to the correct type.

#### Acceptance Criteria

1. THE system SHALL provide built-in converters: `str`, `int`, `float`, `uuid`, `path`.
2. THE `str` converter SHALL match any non-empty string segment.
3. THE `int` converter SHALL match integer values and convert to Python int.
4. THE `float` converter SHALL match numeric values and convert to Python float.
5. THE `uuid` converter SHALL match UUID strings and convert to Python UUID.
6. THE `path` converter SHALL match any remaining path segments including slashes.
7. WHEN a converter fails to match or convert, THE Matcher SHALL treat the route as non-matching.
8. THE system SHALL support custom converter registration via `register_converter(name: str, converter: Converter)`.

### Requirement 11: Router Configuration

**User Story:** As a framework author, I want configurable router behavior, so that the routing system can be adapted to different application needs.

#### Acceptance Criteria

1. THE Router SHALL support `strict_slashes` configuration to control trailing slash handling.
2. WHEN `strict_slashes=True`, THE Router SHALL treat `/path` and `/path/` as different routes.
3. WHEN `strict_slashes=False`, THE Router SHALL redirect or match both variants.
4. THE Router SHALL support `case_sensitive` configuration for path matching.
5. WHEN `case_sensitive=False`, THE Router SHALL match paths case-insensitively.
6. THE Router SHALL support `redirect_slashes` configuration to auto-redirect trailing slash mismatches.

</content>
</invoke>