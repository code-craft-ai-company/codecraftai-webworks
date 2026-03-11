# Requirements Document

## Introduction

This document specifies the requirements for the Middleware Pipeline feature of the automojo-webworks package. The middleware pipeline provides a formal abstraction for composing request/response processing in an ordered chain, enabling cross-cutting concerns such as CORS, request logging, compression, rate limiting, and error normalization to be applied declaratively across routes, blueprints, or the entire application.

The existing codebase already contains a `MiddlewarePipeline` in `routing.middleware` with basic sync/async execution, a `WSGIMiddlewareWrapper` in `wsgi.middleware` for WSGI-style wrapping, and a `register_middleware` hook in the extensibility system's `ComponentRegistrationHooks`. This feature formalizes and unifies these pieces into a cohesive middleware layer that integrates with both ASGI and WSGI protocols, supports scoped middleware attachment (global, per-blueprint, per-route), and provides built-in middleware for common cross-cutting concerns.

## Glossary

- **Middleware**: A callable component that intercepts request/response processing, optionally modifying the request before the next handler and/or modifying the response after the next handler returns.
- **Middleware_Pipeline**: An ordered chain of Middleware components that processes requests sequentially before reaching the endpoint handler, and processes responses in reverse order.
- **Middleware_Registry**: A central registry that collects, orders, and provides access to all registered Middleware components across scopes.
- **Middleware_Scope**: The level at which a Middleware is applied: global (all requests), blueprint (all routes in a blueprint), or route (a single endpoint).
- **Middleware_Entry**: An internal record associating a Middleware callable with its name, priority, and scope metadata.
- **Call_Next**: A callable passed to each Middleware that invokes the next Middleware in the chain or the final endpoint handler.
- **Middleware_Context**: Contextual information available to Middleware during request processing, including the current scope, matched route metadata, and application configuration.
- **ASGI_Middleware**: A Middleware that conforms to the ASGI protocol, accepting scope, receive, and send callables.
- **WSGI_Middleware**: A Middleware that conforms to the WSGI protocol, wrapping a WSGI application callable.
- **Middleware_Factory**: A callable that accepts configuration parameters and returns a configured Middleware instance.
- **Middleware_Priority**: A numeric value determining the execution order of Middleware within the same scope (lower numbers execute first).
- **Short_Circuit**: The act of a Middleware returning a response without calling Call_Next, bypassing all subsequent Middleware and the endpoint handler.

## Requirements

### Requirement 1: Middleware Protocol Abstraction

**User Story:** As a framework developer, I want a formal protocol for middleware components, so that middleware authors have a clear contract to implement for both sync and async processing.

#### Acceptance Criteria

1. THE Middleware protocol SHALL define a `__call__` method that accepts a Request and a Call_Next callable and returns a Response.
2. THE Middleware protocol SHALL define a `name` attribute for identifying the middleware in the pipeline.
3. THE AsyncMiddleware protocol SHALL define an async `__call__` method that accepts a Request and an async Call_Next callable and returns a Response.
4. THE AsyncMiddleware protocol SHALL define a `name` attribute for identifying the middleware in the pipeline.
5. THE framework SHALL support middleware implemented as classes conforming to the Middleware or AsyncMiddleware protocol.
6. THE framework SHALL support middleware implemented as plain callables with the signature `(request, call_next) -> response`.
7. WHEN a middleware is registered, THE Middleware_Registry SHALL validate that the middleware conforms to the Middleware or AsyncMiddleware protocol using duck-typing.
8. IF a middleware does not conform to the required protocol, THEN THE Middleware_Registry SHALL raise a descriptive error identifying the missing interface.

### Requirement 2: Middleware Pipeline Execution

**User Story:** As a framework developer, I want an ordered middleware chain, so that requests flow through middleware in a predictable sequence before reaching the endpoint handler.

#### Acceptance Criteria

1. THE Middleware_Pipeline SHALL execute middleware in registration order, with each middleware wrapping the next.
2. THE Middleware_Pipeline SHALL pass the endpoint handler as the final Call_Next callable to the last middleware in the chain.
3. WHEN a middleware calls Call_Next, THE Middleware_Pipeline SHALL invoke the next middleware in the chain.
4. WHEN the last middleware calls Call_Next, THE Middleware_Pipeline SHALL invoke the endpoint handler.
5. WHEN a middleware returns a response without calling Call_Next, THE Middleware_Pipeline SHALL return that response as a Short_Circuit, bypassing remaining middleware and the handler.
6. THE Middleware_Pipeline SHALL support synchronous execution via an `execute(request, handler)` method.
7. THE Middleware_Pipeline SHALL support asynchronous execution via an `execute_async(request, handler)` method.
8. IF a middleware raises an exception, THEN THE Middleware_Pipeline SHALL propagate the exception to the caller without executing remaining middleware.

### Requirement 3: Middleware Registration and Ordering

**User Story:** As a framework user, I want to control where middleware is inserted in the pipeline, so that I can ensure correct execution order for dependent middleware.

#### Acceptance Criteria

1. THE Middleware_Pipeline SHALL support adding middleware at the start of the chain via `position="start"`.
2. THE Middleware_Pipeline SHALL support adding middleware at the end of the chain via `position="end"`.
3. THE Middleware_Pipeline SHALL support inserting middleware before a named middleware via `position="before:<name>"`.
4. THE Middleware_Pipeline SHALL support inserting middleware after a named middleware via `position="after:<name>"`.
5. IF a positional insertion references a middleware name that does not exist in the pipeline, THEN THE Middleware_Pipeline SHALL raise ValueError with a descriptive message.
6. THE Middleware_Pipeline SHALL support removing middleware by name via a `remove(name)` method.
7. IF a removal references a middleware name that does not exist, THEN THE Middleware_Pipeline SHALL raise KeyError with a descriptive message.
8. THE Middleware_Pipeline SHALL support numeric Middleware_Priority values for ordering middleware within the same positional group.
9. THE Middleware_Pipeline SHALL provide a `get_names()` method that returns the ordered list of middleware names in the chain.

### Requirement 4: Middleware Scoping

**User Story:** As a framework user, I want to apply middleware at different scopes, so that I can target cross-cutting concerns to specific routes or groups of routes.

#### Acceptance Criteria

1. THE Middleware_Registry SHALL support registering middleware at global scope, applying the middleware to all requests.
2. THE Middleware_Registry SHALL support registering middleware at blueprint scope, applying the middleware to all routes within a specific Blueprint.
3. THE Middleware_Registry SHALL support registering middleware at route scope, applying the middleware to a single endpoint.
4. WHEN a request is dispatched, THE Dispatcher SHALL compose the effective pipeline by combining global middleware, then blueprint middleware, then route middleware in that order.
5. THE Middleware_Registry SHALL support querying registered middleware by scope.
6. WHEN a blueprint defines middleware, THE middleware SHALL apply to all child endpoints registered under that blueprint.
7. WHEN a route defines middleware that overlaps with blueprint or global middleware, THE route-level middleware SHALL execute in addition to (not replace) the higher-scope middleware.

### Requirement 5: ASGI Middleware Integration

**User Story:** As a framework developer, I want middleware to integrate with the ASGI application layer, so that middleware can process ASGI HTTP requests and responses.

#### Acceptance Criteria

1. THE ASGI_Middleware protocol SHALL define an async `__call__` method accepting scope, receive, and send callables per the ASGI 3.0 specification.
2. THE framework SHALL provide an `ASGIMiddlewareAdapter` that wraps an ASGI_Middleware to conform to the AsyncMiddleware protocol used by the Middleware_Pipeline.
3. THE framework SHALL provide an `AsyncMiddlewareToASGI` adapter that wraps an AsyncMiddleware to conform to the ASGI_Middleware protocol for use with external ASGI servers.
4. WHEN the ASGIApplication processes an HTTP request, THE framework SHALL execute the composed middleware pipeline before dispatching to the endpoint handler.
5. THE ASGI middleware integration SHALL support middleware that inspects or modifies ASGI scope, receive, and send callables.
6. IF an ASGI_Middleware raises an exception, THEN THE framework SHALL delegate to the ASGIApplication error handler.

### Requirement 6: WSGI Middleware Integration

**User Story:** As a framework developer, I want middleware to integrate with the WSGI application layer, so that middleware can process WSGI requests and responses.

#### Acceptance Criteria

1. THE WSGI_Middleware protocol SHALL follow the standard WSGI middleware pattern where a factory accepts a WSGI application and returns a wrapped WSGI application.
2. THE framework SHALL provide a `WSGIMiddlewareAdapter` that wraps a WSGI_Middleware factory to conform to the Middleware protocol used by the Middleware_Pipeline.
3. THE framework SHALL provide a `MiddlewareToWSGI` adapter that wraps a Middleware to conform to the WSGI_Middleware factory pattern for use with external WSGI servers.
4. WHEN the WSGIApplication processes a request, THE framework SHALL execute the composed middleware pipeline before dispatching to the endpoint handler.
5. THE WSGI middleware integration SHALL support middleware that inspects or modifies the WSGI environ dictionary.
6. IF a WSGI_Middleware raises an exception, THEN THE framework SHALL delegate to the WSGIApplication error handler.

### Requirement 7: Extensibility System Integration

**User Story:** As a plugin developer, I want to register middleware through the extensibility system, so that extensions can inject middleware without modifying application code.

#### Acceptance Criteria

1. THE framework SHALL integrate with the existing `register_middleware` hook in ComponentRegistrationHooks so that extensions can register middleware via the extensibility system.
2. WHEN an extension registers middleware via the `register_middleware` hook, THE Middleware_Registry SHALL add the middleware to the global pipeline.
3. THE `register_middleware` hook SHALL validate that the registered component implements the `process_request` and `process_response` methods as defined in COMPONENT_REQUIRED_METHODS.
4. THE framework SHALL support extensions specifying middleware priority and position when registering via the hook.
5. WHEN the application initializes, THE framework SHALL collect all extension-registered middleware and compose them into the global pipeline in priority order.
6. THE Middleware_Registry SHALL provide a `get_registered_components(hook_name)` method for retrieving all middleware registered via the extensibility system.

### Requirement 8: Middleware Context

**User Story:** As a middleware author, I want access to contextual information during request processing, so that my middleware can make informed decisions based on the matched route and application state.

#### Acceptance Criteria

1. THE Middleware_Context SHALL provide access to the matched route's EndpointDescriptor when available.
2. THE Middleware_Context SHALL provide access to the current Middleware_Scope (global, blueprint, or route).
3. THE Middleware_Context SHALL provide access to the application's configuration.
4. THE Middleware_Context SHALL provide access to a logger instance.
5. THE Middleware_Context SHALL be attached to the Request object so middleware can access the context via `request.middleware_context`.
6. WHEN no route has been matched yet (middleware executing before routing), THE Middleware_Context SHALL set the EndpointDescriptor to None.

### Requirement 9: Built-in CORS Middleware

**User Story:** As a framework user, I want built-in CORS middleware, so that I can configure cross-origin resource sharing without writing custom middleware.

#### Acceptance Criteria

1. THE CORS Middleware SHALL accept a list of allowed origins.
2. THE CORS Middleware SHALL accept a list of allowed HTTP methods.
3. THE CORS Middleware SHALL accept a list of allowed request headers.
4. THE CORS Middleware SHALL accept a list of exposed response headers.
5. THE CORS Middleware SHALL accept a boolean flag for allowing credentials.
6. THE CORS Middleware SHALL accept a max age value in seconds for preflight cache duration.
7. WHEN a preflight OPTIONS request is received, THE CORS Middleware SHALL return a 204 response with the appropriate CORS headers without calling Call_Next.
8. WHEN a regular request is received from an allowed origin, THE CORS Middleware SHALL add the appropriate CORS response headers to the response.
9. WHEN a request is received from a disallowed origin, THE CORS Middleware SHALL omit CORS headers from the response.
10. THE CORS Middleware SHALL support wildcard origin matching via `"*"`.

### Requirement 10: Built-in Request Logging Middleware

**User Story:** As a framework user, I want built-in request logging middleware, so that I can log request and response details for debugging and auditing.

#### Acceptance Criteria

1. THE Request Logging Middleware SHALL log the HTTP method, path, and query parameters for each request.
2. THE Request Logging Middleware SHALL log the response status code and processing duration for each response.
3. THE Request Logging Middleware SHALL accept a configurable logger instance.
4. THE Request Logging Middleware SHALL accept a configurable log level for request and response messages.
5. THE Request Logging Middleware SHALL accept a list of header names to include in log output.
6. THE Request Logging Middleware SHALL accept a list of path patterns to exclude from logging.
7. WHEN a request path matches an excluded pattern, THE Request Logging Middleware SHALL skip logging for that request.

### Requirement 11: Built-in Error Normalization Middleware

**User Story:** As a framework user, I want built-in error normalization middleware, so that unhandled exceptions are converted to consistent error responses.

#### Acceptance Criteria

1. WHEN an exception propagates through the middleware pipeline, THE Error Normalization Middleware SHALL catch the exception and return a structured error response.
2. THE Error Normalization Middleware SHALL return a JSON response body containing `error`, `error_description`, and `status_code` fields.
3. THE Error Normalization Middleware SHALL map HTTPException instances to their corresponding status codes.
4. THE Error Normalization Middleware SHALL map unhandled exceptions to a 500 status code.
5. WHILE the application is in debug mode, THE Error Normalization Middleware SHALL include the exception traceback in the error response.
6. WHILE the application is in production mode, THE Error Normalization Middleware SHALL omit the exception traceback from the error response.
7. THE Error Normalization Middleware SHALL log all caught exceptions using the configured logger.
8. THE Error Normalization Middleware SHALL accept a configurable mapping of exception types to status codes and error messages.

### Requirement 12: Middleware Pipeline Introspection

**User Story:** As a framework user, I want to inspect the composed middleware pipeline, so that I can verify the middleware execution order during development and debugging.

#### Acceptance Criteria

1. THE Middleware_Pipeline SHALL provide a `__len__` method returning the number of middleware in the chain.
2. THE Middleware_Pipeline SHALL provide an `__iter__` method for iterating over Middleware_Entry objects in execution order.
3. THE Middleware_Pipeline SHALL provide a `__repr__` method returning a human-readable string showing the middleware names in order.
4. THE Middleware_Registry SHALL provide a method to list all registered middleware grouped by scope.
5. THE Middleware_Registry SHALL provide a method to export the effective pipeline for a given route path as an ordered list of middleware names.

### Requirement 13: Middleware Factory Pattern

**User Story:** As a middleware author, I want a factory pattern for creating configurable middleware, so that I can provide reusable middleware with customizable behavior.

#### Acceptance Criteria

1. THE framework SHALL support Middleware_Factory callables that accept configuration parameters and return a configured Middleware instance.
2. THE framework SHALL provide a `create_middleware(factory, **config)` helper function for instantiating middleware from factories.
3. THE Middleware_Factory pattern SHALL support factories that return either sync Middleware or async AsyncMiddleware instances.
4. WHEN a Middleware_Factory is registered with the Middleware_Registry, THE registry SHALL invoke the factory to produce the Middleware instance before adding the middleware to the pipeline.
5. THE framework SHALL validate that the Middleware instance returned by a factory conforms to the Middleware or AsyncMiddleware protocol.

### Requirement 14: Middleware Pipeline Serialization

**User Story:** As a framework developer, I want to serialize the middleware pipeline configuration, so that the pipeline can be reconstructed from a configuration file or exported for documentation.

#### Acceptance Criteria

1. THE Middleware_Pipeline SHALL provide an `as_dict()` method that returns a list of dictionaries describing each Middleware_Entry with keys `name`, `priority`, and `scope`.
2. THE Middleware_Pipeline SHALL provide a `to_json()` method that serializes the pipeline configuration to a JSON string.
3. THE Middleware_Pipeline SHALL provide a `from_config(config)` class method that reconstructs a pipeline from a list of middleware configuration dictionaries.
4. FOR ALL valid Middleware_Pipeline configurations, serializing via `as_dict()` then reconstructing via `from_config()` SHALL produce a pipeline with the same middleware names in the same order (round-trip property).
