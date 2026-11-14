# Requirements Document

## Introduction

This document specifies the requirements for the WSGI Layer feature. This feature provides a complete Web Server Gateway Interface (WSGI) implementation including both the application interface and a built-in WSGI server. The WSGI layer handles synchronous request/response processing and provides compatibility with standard WSGI middleware.

WSGI (PEP 3333) is the standard Python interface between web servers and web applications. This feature implements both sides of the WSGI specification:
1. The application-side interface for handling HTTP requests
2. A built-in WSGI server for development and production use, reducing dependencies on external packages like Gunicorn or uWSGI

A key goal of this implementation is to minimize external dependencies by providing a complete, self-contained WSGI stack that can serve applications without requiring third-party server packages.

A WebApplication is built as an ASGI application (`asgi_app`). It is served over WSGI by `WebApplication.wsgi_app`, an ASGI_Bridge that runs the application's own ASGI pipeline, so a route behaves the same under WSGI and ASGI and authentication, sessions, CSRF and limits are implemented once (decision of 2026-11-12, audit finding WW-0175; Requirement 16). `WSGIApplication` remains the lower-level adapter for code that handles framework Requests synchronously itself.

## Glossary

- **WSGI_Application**: A callable object that accepts two arguments (environ, start_response) and returns an iterable yielding response body chunks.
- **WSGI_Environ**: A dictionary containing CGI-style environment variables plus WSGI-specific variables describing the HTTP request.
- **Start_Response**: A callable provided by the server that the application calls to begin the HTTP response with status and headers.
- **WSGI_Middleware**: A component that wraps a WSGI application to add functionality, acting as both server and application.
- **WSGI_Server**: A server that implements the server-side of the WSGI specification and invokes WSGI applications. This feature includes a built-in WSGI server implementation.
- **Worker_Process**: A child process spawned by the WSGI server to handle requests, providing process-based concurrency.
- **Worker_Thread**: A thread within a worker process that handles individual requests, providing thread-based concurrency.
- **Socket_Listener**: A component that binds to a network address and accepts incoming TCP connections.
- **Response_Iterator**: An iterable returned by the WSGI application that yields response body chunks as bytes.
- **Write_Callable**: A callable returned by start_response for legacy applications that write response body directly.
- **Environ_Key**: A key in the WSGI environ dictionary following CGI or WSGI naming conventions.
- **Content_Length**: The HTTP header indicating the size of the response body in bytes.
- **Chunked_Transfer**: A transfer encoding where the response body is sent in chunks without a predetermined Content-Length.
- **ASGI_Bridge**: `ccai.webworks.wsgi.asgibridge.ASGIBridge`, a WSGI_Application that serves an ASGI application by running it on one event loop per process.
- **Worker_Lifecycle_Methods**: The optional `on_worker_start(worker)` and `on_worker_exit(worker)` methods of an application object, which the built-in server calls in each worker process.

## Requirements

### Requirement 1: WSGI Application Interface

**User Story:** As a framework author, I want a WSGI-compliant application interface, so that the framework can be deployed on any WSGI-compliant server.

#### Acceptance Criteria

1. THE WSGI_Application SHALL be a callable accepting `environ` dict and `start_response` callable as arguments.
2. THE WSGI_Application SHALL return a Response_Iterator yielding bytes objects.
3. THE WSGI_Application SHALL call `start_response(status, response_headers)` before yielding any body content.
4. THE WSGI_Application SHALL support the optional `exc_info` argument to start_response for error handling.
5. WHEN the application raises an exception before calling start_response, THE WSGI_Application SHALL allow the exception to propagate to the server.
6. WHEN the application raises an exception after calling start_response, THE WSGI_Application SHALL re-raise the exception using exc_info if headers have not been sent.
7. THE WSGI_Application SHALL implement the `close()` method on the response iterator for resource cleanup.
8. THE WSGI_Application SHALL NOT use the write callable returned by start_response except for legacy compatibility.

### Requirement 2: Environ Dictionary Processing

**User Story:** As a framework author, I want proper environ dictionary processing, so that request data is correctly extracted from the WSGI environment.

#### Acceptance Criteria

1. THE WSGI_Application SHALL read the HTTP method from `environ['REQUEST_METHOD']`.
2. THE WSGI_Application SHALL read the request path from `environ['PATH_INFO']`.
3. THE WSGI_Application SHALL read the query string from `environ['QUERY_STRING']`.
4. THE WSGI_Application SHALL read HTTP headers from environ keys prefixed with `HTTP_`.
5. THE WSGI_Application SHALL read Content-Type from `environ['CONTENT_TYPE']` when present.
6. THE WSGI_Application SHALL read Content-Length from `environ['CONTENT_LENGTH']` when present.
7. THE WSGI_Application SHALL read the request body from `environ['wsgi.input']` file-like object.
8. THE WSGI_Application SHALL read the URL scheme from `environ['wsgi.url_scheme']`.
9. THE WSGI_Application SHALL read the server name from `environ['SERVER_NAME']`.
10. THE WSGI_Application SHALL read the server port from `environ['SERVER_PORT']`.
11. THE WSGI_Application SHALL handle missing optional environ keys gracefully with default values.

### Requirement 3: Response Generation

**User Story:** As a framework author, I want proper response generation, so that HTTP responses are correctly formatted for WSGI servers.

#### Acceptance Criteria

1. THE WSGI_Application SHALL format the status as a string with status code and reason phrase (e.g., "200 OK").
2. THE WSGI_Application SHALL format response headers as a list of (name, value) tuples.
3. THE WSGI_Application SHALL NOT include hop-by-hop headers in the response headers.
4. THE WSGI_Application SHALL set Content-Type header for all responses with body content.
5. THE WSGI_Application SHALL set Content-Length header when the response body size is known.
6. WHEN Content-Length is not set, THE WSGI_Application SHALL support chunked transfer encoding if the server supports it.
7. THE WSGI_Application SHALL encode response body content as bytes.
8. THE WSGI_Application SHALL support streaming responses via the response iterator.

### Requirement 4: WSGI Middleware Compatibility

**User Story:** As a developer, I want WSGI middleware compatibility, so that I can use standard WSGI middleware with the framework.

#### Acceptance Criteria

1. THE WSGI_Application SHALL be wrappable by standard WSGI middleware.
2. THE WSGI_Application SHALL correctly propagate environ modifications made by middleware.
3. THE WSGI_Application SHALL correctly propagate response modifications made by middleware.
4. THE system SHALL provide a `wrap_middleware(app, middleware)` helper for applying middleware.
5. THE system SHALL support middleware that modifies the environ before calling the application.
6. THE system SHALL support middleware that modifies the response after the application returns.
7. THE system SHALL support middleware that short-circuits the request without calling the application.
8. THE system SHALL maintain middleware execution order (outer middleware wraps inner middleware).

### Requirement 5: Built-in WSGI Server

**User Story:** As a developer, I want a built-in WSGI server, so that I can run applications without external server dependencies.

#### Acceptance Criteria

1. THE WSGI_Server SHALL bind to a configurable host address and port.
2. THE WSGI_Server SHALL accept incoming TCP connections and parse HTTP requests.
3. THE WSGI_Server SHALL construct valid WSGI environ dictionaries from HTTP requests.
4. THE WSGI_Server SHALL invoke the WSGI application with environ and start_response.
5. THE WSGI_Server SHALL send HTTP responses based on start_response and response iterator.
6. THE WSGI_Server SHALL support configurable number of Worker_Process instances for concurrency.
7. THE WSGI_Server SHALL support configurable number of Worker_Thread instances per process.
8. THE WSGI_Server SHALL handle graceful shutdown on SIGTERM and SIGINT signals.
9. THE WSGI_Server SHALL support keep-alive connections per HTTP/1.1 specification.
10. THE WSGI_Server SHALL log request information including method, path, status, and timing.
11. THE WSGI_Server SHALL provide a simple API for starting and stopping the server programmatically.
12. THE WSGI_Server SHALL support both development mode (auto-reload) and production mode.

### Requirement 5a: External Server Compatibility

**User Story:** As a system administrator, I want optional external WSGI server compatibility, so that I can deploy on existing infrastructure when needed.

#### Acceptance Criteria

1. THE system SHALL provide a `get_wsgi_application()` function returning the WSGI callable for external servers, so that `gunicorn 'ccai.webworks.wsgi.application:get_wsgi_application()'` serves the application.
2. THE WSGI_Application SHALL remain compatible with Gunicorn, uWSGI, mod_wsgi, and Waitress.
3. THE system SHALL support the `application` module-level variable convention for external WSGI servers; reading `ccai.webworks.wsgi.application.application` SHALL give the callable `get_wsgi_application()` returns.
4. THE system SHALL provide application factory pattern support for external WSGI servers (`create_wsgi_application()` for a WSGIApplication around a handler).
5. WHEN the application factory is used, THE system SHALL create a new application instance per call.
6. `get_wsgi_application()` SHALL find the application once, in this order: the application set with `set_wsgi_application()`; the import target (`module:attribute`) in the `WEBWORKS_SERVER_APP` environment variable, the variable the `webworks` command line reads for `server.app`; the established web application persona.
7. WHEN the target names a WebApplication, or the ASGI application of the established persona (the `app` a site module exports), THE system SHALL serve the persona's `wsgi_app`; any other ASGI application SHALL be served through an ASGI_Bridge of its own and any other callable as a WSGI application.
8. WHEN there is no application to serve, or the target cannot be imported, THE system SHALL raise `ConfigurationError` (fail early) instead of serving an application that answers 404.

### Requirement 6: Synchronous Request Handling

**User Story:** As a developer, I want synchronous request handling, so that I can write straightforward blocking code for request processing.

#### Acceptance Criteria

1. THE WSGI_Application SHALL process requests synchronously from the point of view of the calling thread: the thread the server called the application on blocks until the response is produced. Under the ASGI_Bridge the handlers run where they run under ASGI (coroutine handlers on the process's event loop, other handlers on its worker threads), and the calling thread does the request's socket I/O.
2. THE WSGI_Application SHALL block until the response is fully generated (or, for a streaming response, hand each chunk to the server as it is produced).
3. THE WSGI_Application SHALL support blocking I/O operations within request handlers.
4. THE WSGI_Application SHALL support database queries and external API calls within handlers.
5. THE WSGI_Application SHALL NOT require async/await syntax for request handlers.
6. THE WSGI_Application SHALL integrate with the framework's synchronous middleware pipeline.
7. WHEN an exception occurs during request handling, THE WSGI_Application SHALL handle it synchronously.

### Requirement 7: Request Body Handling

**User Story:** As a developer, I want proper request body handling, so that I can process POST data, file uploads, and JSON payloads.

#### Acceptance Criteria

1. THE WSGI_Application SHALL read the request body from `wsgi.input` respecting Content-Length.
2. THE WSGI_Application SHALL support reading the request body as raw bytes.
3. THE WSGI_Application SHALL support parsing form-encoded request bodies.
4. THE WSGI_Application SHALL support parsing multipart form data for file uploads.
5. THE WSGI_Application SHALL support parsing JSON request bodies.
6. THE WSGI_Application SHALL limit request body size based on configuration.
7. WHEN the request body exceeds the size limit, THE WSGI_Application SHALL return HTTP 413 Request Entity Too Large.
8. THE WSGI_Application SHALL handle chunked transfer encoding for request bodies when supported by the server.

### Requirement 8: Error Handling

**User Story:** As a developer, I want proper error handling in the WSGI layer, so that errors are correctly reported to clients and logged.

#### Acceptance Criteria

1. WHEN an HTTPException is raised, THE WSGI_Application SHALL return the appropriate HTTP error response.
2. WHEN an unhandled exception occurs, THE WSGI_Application SHALL return HTTP 500 Internal Server Error.
3. THE WSGI_Application SHALL log all unhandled exceptions with stack traces.
4. THE WSGI_Application SHALL NOT expose internal error details to clients in production mode.
5. THE WSGI_Application SHALL include stack traces in error responses in debug mode.
6. THE WSGI_Application SHALL use the `exc_info` parameter to start_response for error recovery.
7. WHEN headers have already been sent, THE WSGI_Application SHALL log the error and close the connection.
8. THE WSGI_Application SHALL support custom error handlers for specific exception types.

### Requirement 9: WSGI Environ Extensions

**User Story:** As a framework author, I want WSGI environ extensions, so that framework-specific data can be passed through the WSGI interface.

#### Acceptance Criteria

1. THE WSGI_Application SHALL support custom environ keys prefixed with the framework namespace.
2. THE WSGI_Application SHALL store the Request object in `environ['webworks.request']`.
3. THE WSGI_Application SHALL store the matched route in `environ['webworks.route']`.
4. THE WSGI_Application SHALL store path parameters in `environ['webworks.path_params']`.
5. THE WSGI_Application SHALL support middleware adding custom environ keys.
6. THE WSGI_Application SHALL preserve all standard WSGI environ keys unmodified.
7. THE WSGI_Application SHALL document all framework-specific environ keys.

### Requirement 10: Response Iterator Protocol

**User Story:** As a framework author, I want proper response iterator protocol implementation, so that responses are correctly streamed to clients.

#### Acceptance Criteria

1. THE Response_Iterator SHALL implement the iterator protocol (`__iter__` and `__next__`).
2. THE Response_Iterator SHALL yield bytes objects only.
3. THE Response_Iterator SHALL implement `close()` method for resource cleanup.
4. WHEN `close()` is called, THE Response_Iterator SHALL release all held resources.
5. THE Response_Iterator SHALL support generators as response bodies.
6. THE Response_Iterator SHALL support file-like objects as response bodies.
7. THE Response_Iterator SHALL support list of bytes as response bodies.
8. THE WSGI_Application SHALL call `close()` on the response iterator when iteration completes.

### Requirement 11: HTTP Request Parsing

**User Story:** As a framework author, I want robust HTTP request parsing, so that the built-in server correctly handles all valid HTTP requests.

#### Acceptance Criteria

1. THE WSGI_Server SHALL parse HTTP/1.0 and HTTP/1.1 request lines.
2. THE WSGI_Server SHALL parse HTTP headers according to RFC 7230.
3. THE WSGI_Server SHALL handle header continuation lines (folded headers).
4. THE WSGI_Server SHALL enforce configurable maximum header size limits.
5. THE WSGI_Server SHALL enforce configurable maximum number of headers.
6. THE WSGI_Server SHALL parse chunked transfer encoding for request bodies.
7. WHEN an invalid HTTP request is received, THE WSGI_Server SHALL return HTTP 400 Bad Request.
8. THE WSGI_Server SHALL handle requests with and without Content-Length header.
9. THE WSGI_Server SHALL support HTTP methods: GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS.
10. THE WSGI_Server SHALL preserve header case for HTTP_* environ keys while normalizing for lookup.

### Requirement 12: HTTP Response Generation

**User Story:** As a framework author, I want correct HTTP response generation, so that the built-in server produces valid HTTP responses.

#### Acceptance Criteria

1. THE WSGI_Server SHALL generate valid HTTP/1.1 response status lines.
2. THE WSGI_Server SHALL write response headers in correct HTTP format.
3. THE WSGI_Server SHALL support Content-Length based response bodies.
4. THE WSGI_Server SHALL support chunked transfer encoding for streaming responses.
5. THE WSGI_Server SHALL set appropriate Date header on all responses.
6. THE WSGI_Server SHALL set Server header identifying the framework.
7. WHEN keep-alive is enabled, THE WSGI_Server SHALL set Connection: keep-alive header.
8. THE WSGI_Server SHALL flush response data appropriately for streaming.

### Requirement 13: Worker Process Management

**User Story:** As a system administrator, I want worker process management, so that the server can handle concurrent requests efficiently.

#### Acceptance Criteria

1. THE WSGI_Server SHALL spawn configurable number of worker processes using fork (Unix) or spawn (Windows).
2. THE WSGI_Server SHALL distribute incoming connections across worker processes.
3. THE WSGI_Server SHALL monitor worker process health and restart failed workers.
4. THE WSGI_Server SHALL support graceful worker restart without dropping connections.
5. WHEN a worker process exceeds memory limits, THE WSGI_Server SHALL restart that worker. (The production server measures the memory after each request and stops the worker gracefully; the WSGI_Server replaces it.)
6. THE WSGI_Server SHALL support worker process timeout for hung requests. (A WebApplication served through the ASGI_Bridge is given the request timeout under `webworks.request_timeout` and answered 504; killing a worker whose thread hangs in a plain WSGI application is not implemented.)
7. THE WSGI_Server SHALL propagate signals to worker processes for coordinated shutdown.
8. THE WSGI_Server SHALL support pre-fork and lazy-fork worker initialization modes. (The production server loads the application in the master with `preload`, or in each worker from a factory.)
9. THE Worker SHALL call the application's Worker_Lifecycle_Methods when it defines them: `on_worker_start(worker)` before the worker accepts connections, `on_worker_exit(worker)` after it stopped serving.
10. WHEN `on_worker_start` raises, THE Worker SHALL raise `WorkerBootError`, the worker process SHALL end with `WORKER_BOOT_ERROR_EXIT_CODE` (3), and THE WSGI_Server SHALL stop instead of starting replacements that would fail the same way (`boot_failed`).
11. WHEN `max_requests` is configured, a worker SHALL stop gracefully after serving `max_requests` plus a random `0..max_requests_jitter` requests, answer its last request with `Connection: close`, and be replaced.
12. THE WorkerManager SHALL replace all workers without dropping connections (`replace_workers()`: new workers first, then the old ones are stopped gracefully) and SHALL report every ended worker (pid, worker id, exit code) to an optional exit callback.
13. DURING a graceful shutdown, a connection the worker accepted but has not served yet SHALL be served (and then closed); a worker that is stopping SHALL NOT accept new connections.

### Requirement 14: Socket and Connection Management

**User Story:** As a framework author, I want proper socket management, so that the server handles network connections reliably.

#### Acceptance Criteria

1. THE Socket_Listener SHALL bind to IPv4 and IPv6 addresses.
2. THE Socket_Listener SHALL support Unix domain sockets.
3. THE Socket_Listener SHALL configure SO_REUSEADDR. It SHALL NOT set SO_REUSEPORT: the workers share one listening socket, and a second server started on the same address SHALL fail to bind instead of silently taking part of the connections.
9. THE Socket_Listener SHALL accept a TLS context built elsewhere (`set_ssl_context`), so a layer above it decides the TLS policy.
4. THE WSGI_Server SHALL handle connection timeouts gracefully.
5. THE WSGI_Server SHALL limit maximum concurrent connections per worker.
6. THE WSGI_Server SHALL support SSL/TLS connections with configurable certificates.
7. WHEN a connection is idle beyond keep-alive timeout, THE WSGI_Server SHALL close it.
8. THE WSGI_Server SHALL handle partial reads and writes correctly.

### Requirement 15: Server Configuration

**User Story:** As a system administrator, I want comprehensive server configuration, so that I can tune the server for different deployment scenarios.

#### Acceptance Criteria

1. THE WSGI_Server SHALL accept configuration via constructor arguments.
2. THE WSGI_Server SHALL accept configuration via environment variables.
3. THE WSGI_Server SHALL accept configuration via configuration file.
4. THE WSGI_Server SHALL support the following configurable parameters:
   - bind address and port
   - number of worker processes
   - number of threads per worker
   - request timeout
   - keep-alive timeout
   - maximum request body size
   - maximum header size
   - backlog size
   - SSL certificate and key paths
   - worker class (`sync`, its alias `thread`, or `gevent` when the gevent package is installed)
   - worker recycling (`max_requests`, `max_requests_jitter`)
5. THE WSGI_Server SHALL validate configuration and report errors clearly.
6. THE WSGI_Server SHALL provide sensible defaults for all configuration options.

</content>
</invoke>

### Requirement 16: Serving a WebApplication over WSGI

**User Story:** As a developer, I want to serve my WebApplication with any WSGI server, so that it behaves exactly as it does under an ASGI server.

#### Acceptance Criteria

1. THE WebApplication SHALL expose `wsgi_app`, a PEP 3333 callable (an ASGI_Bridge around `asgi_app`), available from the `INFRASTRUCTURE_READY` phase and the same object on every call.
2. A request served through `wsgi_app` SHALL go through the application's ASGI pipeline: routing, middleware, the authentication middleware when configured, sessions and CSRF middleware wrapped around the ASGI application, the `server.max_request_body_size` limit, the error handling and the lifespan startup and shutdown handlers. The same request SHALL get the same answer through `asgi_app` and `wsgi_app`.
3. THE ASGI_Bridge SHALL run one event loop per process, on a thread of its own, and SHALL resolve the ASGI application when it starts in a process, so authentication configured after `wsgi_app` was read is served.
4. THE ASGI_Bridge SHALL feed `wsgi.input` to `receive()` in chunks, one each time the application asks, reading no further than the Content-Length (or to the end of a terminated input), so the application's body limit stops the reading as soon as it is passed.
5. THE ASGI_Bridge SHALL hand each body chunk of `send()` to the server as it arrives, and `send()` SHALL return only once the server has taken the chunk.
6. THE lifespan startup SHALL run once per process, before the first request is served or when the server starts a worker (`on_worker_start`); the lifespan shutdown SHALL run when the server stops the worker (`on_worker_exit`), when `shutdown()` is called, or when the process exits. A process forked after the bridge started SHALL run a lifespan of its own.
7. WHEN the lifespan startup failed, THE ASGI_Bridge SHALL answer every request with 503; after `shutdown()` it SHALL answer 503 as well.
8. WHEN the application has not started its response within the request timeout (the bridge's, or `environ['webworks.request_timeout']`), THE ASGI_Bridge SHALL cancel it and answer 504.
9. A HEAD response SHALL keep its headers and carry no body; repeated header fields (Set-Cookie) SHALL all reach the server; hop-by-hop headers SHALL be left to the server.
10. WHEN the application raises before it starts a response, THE ASGI_Bridge SHALL answer 500; WHEN it ends a started response early, the body iterator SHALL raise `IncompleteResponse` so the server closes the connection.
11. WHEN the client disconnects (the server closes the body early), `send()` SHALL raise `ClientDisconnected` and `receive()` SHALL report `http.disconnect`; WHEN reading the request body fails, the application SHALL see `http.disconnect` and the read error SHALL be raised to the server.
12. `ConfigurationError`, `SemanticError` and other exceptions that are not `Exception`s, raised by the application, SHALL propagate and not be turned into a 500 or a failed startup.
13. WebSocket routes SHALL be served over ASGI only; WSGI cannot carry them.
