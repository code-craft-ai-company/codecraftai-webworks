# Requirements Document

## Introduction

The codecraftai-webworks framework currently has a `DevelopmentServer` class that manages lifecycle and configuration (debug middleware, request logging, file watching) but does not actually bind a socket, accept connections, or serve HTTP requests. The existing `WSGIServer` provides real socket-based serving but only for WSGI applications. The framework needs a development-focused ASGI server that can accept HTTP connections, translate raw HTTP into ASGI scope dictionaries, invoke the `ASGIApplication` callable, and send responses back to clients. This server must integrate with the existing `DevelopmentServer` lifecycle, the `ServeCommand` CLI, and use only Python standard library (`asyncio`) with no external dependencies.

## Glossary

- **Development_Server**: The existing `DevelopmentServer` class at `devexp/server/devserver.py` that manages server lifecycle, debug middleware, request logging, and file watching.
- **ASGI_Application**: An async callable conforming to the ASGI protocol signature `async app(scope, receive, send)` as implemented by `ASGIApplication` in `asgi/application.py`.
- **ASGI_Scope**: A dictionary containing connection metadata (type, method, path, headers, query string, server, client) passed to the ASGI application for each request.
- **HTTP_Protocol_Handler**: An asyncio protocol implementation that parses incoming HTTP/1.1 data from a TCP connection and produces ASGI scope, receive, and send callables.
- **Async_Server_Core**: An asyncio-based TCP server component that binds a socket, accepts connections, and delegates each connection to the HTTP_Protocol_Handler.
- **Event_Loop_Runner**: The component responsible for creating, running, and stopping the asyncio event loop on the main thread.
- **Lifespan_Manager**: The component that sends ASGI lifespan startup and shutdown events to the ASGI_Application during server start and stop.
- **Request_Logger**: The existing request logging component at `devexp/server/requestlogger.py`.
- **File_Watcher**: The existing file watcher component at `devexp/server/filewatcher.py`.
- **Serve_Command**: The existing CLI command at `devexp/server/servecommand.py` that creates and starts the Development_Server.

## Requirements

### Requirement 1: TCP Socket Binding and Connection Acceptance

**User Story:** As a developer, I want the development server to bind a TCP socket and accept incoming connections, so that HTTP clients can connect to the server.

#### Acceptance Criteria

1. WHEN the Development_Server start method is called, THE Async_Server_Core SHALL bind a TCP socket to the configured host and port.
2. WHILE the Development_Server is running, THE Async_Server_Core SHALL accept incoming TCP connections and create an HTTP_Protocol_Handler instance for each connection.
3. IF the configured port is already in use, THEN THE Development_Server SHALL raise a PortInUseError before attempting to bind.
4. WHEN the Development_Server start method is called, THE Event_Loop_Runner SHALL create an asyncio event loop and block the calling thread until the server is stopped.
5. WHEN a client connects, THE Async_Server_Core SHALL record the client address (host, port) for use in the ASGI_Scope.

### Requirement 2: HTTP/1.1 Request Parsing

**User Story:** As a developer, I want the server to parse incoming HTTP/1.1 requests, so that the ASGI application receives well-formed scope dictionaries.

#### Acceptance Criteria

1. WHEN raw HTTP data is received on a connection, THE HTTP_Protocol_Handler SHALL parse the request line to extract the HTTP method, request target, and HTTP version.
2. WHEN raw HTTP data is received on a connection, THE HTTP_Protocol_Handler SHALL parse all header lines into a list of two-element byte-string tuples (name, value).
3. WHEN the request includes a body indicated by a Content-Length header, THE HTTP_Protocol_Handler SHALL read exactly the number of bytes specified by Content-Length.
4. WHEN the request uses Transfer-Encoding chunked, THE HTTP_Protocol_Handler SHALL decode the chunked body into a contiguous byte sequence.
5. IF the request line is malformed or exceeds 8192 bytes, THEN THE HTTP_Protocol_Handler SHALL respond with HTTP 400 Bad Request and close the connection.
6. IF a header block exceeds 32768 bytes total, THEN THE HTTP_Protocol_Handler SHALL respond with HTTP 431 Request Header Fields Too Large and close the connection.

### Requirement 3: ASGI Scope Construction

**User Story:** As a developer, I want HTTP requests to be translated into correct ASGI scope dictionaries, so that the ASGI application can process requests using the standard protocol.

#### Acceptance Criteria

1. WHEN an HTTP request is parsed, THE HTTP_Protocol_Handler SHALL construct an ASGI_Scope dictionary with type set to "http".
2. THE HTTP_Protocol_Handler SHALL populate the ASGI_Scope with the following keys: asgi (dict with version "3.0"), http_version, method, path, raw_path, root_path, scheme, query_string, headers, server, and client.
3. WHEN the request target contains a query string, THE HTTP_Protocol_Handler SHALL split the path and query_string into separate ASGI_Scope entries.
4. THE HTTP_Protocol_Handler SHALL encode the path as a string and the query_string as bytes in the ASGI_Scope.
5. THE HTTP_Protocol_Handler SHALL encode each header as a two-element list of byte strings (lowercase name, value) in the ASGI_Scope headers list.
6. THE HTTP_Protocol_Handler SHALL set the server key to a two-element list containing the server host as a string and the server port as an integer.
7. THE HTTP_Protocol_Handler SHALL set the client key to a two-element list containing the client host as a string and the client port as an integer.

### Requirement 4: ASGI Receive and Send Callables

**User Story:** As a developer, I want the server to provide correct receive and send callables to the ASGI application, so that the application can read request bodies and write responses using the standard ASGI message protocol.

#### Acceptance Criteria

1. WHEN the ASGI_Application calls the receive callable, THE HTTP_Protocol_Handler SHALL return an "http.request" message containing the request body bytes and a more_body flag.
2. WHEN the full request body has been delivered, THE HTTP_Protocol_Handler SHALL set more_body to False in the final "http.request" message.
3. WHEN the ASGI_Application calls the send callable with an "http.response.start" message, THE HTTP_Protocol_Handler SHALL buffer the status code and response headers.
4. WHEN the ASGI_Application calls the send callable with an "http.response.body" message, THE HTTP_Protocol_Handler SHALL write the complete HTTP response (status line, headers, body) to the TCP connection.
5. WHEN the "http.response.body" message has more_body set to False or omitted, THE HTTP_Protocol_Handler SHALL finalize the response and allow the connection to be closed or reused.
6. IF the ASGI_Application sends an "http.response.body" message before an "http.response.start" message, THEN THE HTTP_Protocol_Handler SHALL log an error and close the connection.

### Requirement 5: ASGI Lifespan Protocol Support

**User Story:** As a developer, I want the server to send lifespan events to the ASGI application, so that the application can perform startup initialization and shutdown cleanup.

#### Acceptance Criteria

1. WHEN the Async_Server_Core starts accepting connections, THE Lifespan_Manager SHALL send a lifespan.startup event to the ASGI_Application and wait for a lifespan.startup.complete or lifespan.startup.failed response.
2. IF the ASGI_Application responds with lifespan.startup.failed, THEN THE Development_Server SHALL log the failure message and stop the server.
3. WHEN the Development_Server stop method is called, THE Lifespan_Manager SHALL send a lifespan.shutdown event to the ASGI_Application and wait for a lifespan.shutdown.complete or lifespan.shutdown.failed response.
4. IF the ASGI_Application does not implement lifespan handling, THEN THE Lifespan_Manager SHALL proceed without error and treat startup as successful.

### Requirement 6: Graceful Shutdown

**User Story:** As a developer, I want the server to shut down gracefully when requested, so that in-flight requests complete and resources are released cleanly.

#### Acceptance Criteria

1. WHEN the Development_Server stop method is called, THE Async_Server_Core SHALL stop accepting new connections.
2. WHILE in-flight requests are being processed during shutdown, THE Async_Server_Core SHALL allow those requests up to 5 seconds to complete before forcibly closing connections.
3. WHEN a SIGINT or SIGTERM signal is received, THE Development_Server SHALL initiate a graceful shutdown.
4. WHEN all connections are closed and the lifespan shutdown is complete, THE Event_Loop_Runner SHALL stop the asyncio event loop and unblock the calling thread.
5. THE Development_Server SHALL release the bound TCP socket during shutdown so the port becomes available immediately.

### Requirement 7: ServeCommand CLI Integration

**User Story:** As a developer, I want the serve CLI command to start a blocking development server, so that I can run the server from the command line and have it serve requests until interrupted.

#### Acceptance Criteria

1. WHEN the Serve_Command execute method is called, THE Development_Server start method SHALL block the calling thread until the server is stopped.
2. THE Serve_Command SHALL pass the configured host, port, debug, reload, and watch_patterns arguments to the Development_Server.
3. WHEN the server is stopped via signal or programmatic call, THE Serve_Command execute method SHALL return EXIT_SUCCESS.
4. IF a PortInUseError is raised during start, THEN THE Serve_Command SHALL print the port-in-use message and return EXIT_ERROR.

### Requirement 8: Debug Mode Integration

**User Story:** As a developer, I want the server to provide enhanced error information in debug mode, so that I can diagnose issues during development.

#### Acceptance Criteria

1. WHILE debug mode is enabled, THE Development_Server SHALL configure debug middleware on the ASGI_Application before starting the Async_Server_Core.
2. WHILE debug mode is enabled AND an unhandled exception occurs during request processing, THE HTTP_Protocol_Handler SHALL return an HTTP 500 response containing the exception type, message, and traceback as plain text.
3. WHILE debug mode is disabled AND an unhandled exception occurs during request processing, THE HTTP_Protocol_Handler SHALL return a generic HTTP 500 Internal Server Error response without exception details.

### Requirement 9: Request Logging Integration

**User Story:** As a developer, I want all HTTP requests to be logged with method, path, status, and timing, so that I can observe server activity during development.

#### Acceptance Criteria

1. WHEN an HTTP request is completed, THE Request_Logger SHALL log the HTTP method, request path, response status code, and response time in milliseconds.
2. THE Request_Logger SHALL log each request on a single line in the format: "{method} {path} {status_code} {elapsed_ms}ms".
3. WHEN an HTTP request results in an error before a response is sent, THE Request_Logger SHALL log the request with the error status code.

### Requirement 10: File Watching and Auto-Reload Integration

**User Story:** As a developer, I want the server to automatically restart when source files change, so that I can see code changes reflected without manually restarting.

#### Acceptance Criteria

1. WHILE reload mode is enabled, THE File_Watcher SHALL monitor files matching the configured watch_patterns for modifications.
2. WHEN the File_Watcher detects a file change, THE Development_Server SHALL stop the Async_Server_Core, re-import the ASGI_Application, and start a new Async_Server_Core on the same host and port.
3. IF a SyntaxError or ImportError occurs during reload, THEN THE Development_Server SHALL log the error and continue watching for further file changes without crashing.
4. WHEN the File_Watcher detects a file change AND the reload succeeds, THE Development_Server SHALL increment the restart_count property.

### Requirement 11: Connection Keep-Alive Support

**User Story:** As a developer, I want the server to support HTTP/1.1 keep-alive connections, so that multiple requests can be served over a single TCP connection for faster development iteration.

#### Acceptance Criteria

1. WHILE an HTTP/1.1 connection has the Connection header set to "keep-alive" or the header is absent, THE HTTP_Protocol_Handler SHALL keep the connection open after sending the response and wait for the next request.
2. WHEN an HTTP/1.1 connection has the Connection header set to "close", THE HTTP_Protocol_Handler SHALL close the connection after sending the response.
3. WHEN an HTTP/1.0 request is received, THE HTTP_Protocol_Handler SHALL close the connection after sending the response unless the Connection header is set to "keep-alive".
4. WHILE a keep-alive connection is idle for more than 30 seconds, THE HTTP_Protocol_Handler SHALL close the connection.

### Requirement 12: Standard Library Only Constraint

**User Story:** As a developer, I want the server to use only the Python standard library, so that no additional dependencies are required for development use.

#### Acceptance Criteria

1. THE Async_Server_Core SHALL use only the asyncio module from the Python standard library for asynchronous I/O and TCP server functionality.
2. THE HTTP_Protocol_Handler SHALL implement HTTP/1.1 parsing without importing any third-party HTTP parsing libraries.
3. THE Development_Server SHALL not add any new entries to the project dependency list for server functionality.
