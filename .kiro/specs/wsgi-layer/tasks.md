# Implementation Plan: WSGI Layer

## Overview

This implementation plan creates the WSGI Layer feature providing both the WSGI application interface and a built-in WSGI server. The implementation follows PEP 3333 specification and minimizes external dependencies by providing a complete, self-contained WSGI stack.

## Tasks

- [x] 1. Create environ parsing foundation
  - [x] 1.1 Create `EnvironParser` class with basic environ extraction
    - Implement get_method(), get_path(), get_query_string()
    - Implement get_scheme(), get_host(), get_port()
    - _Requirements: 2.1, 2.2, 2.3, 2.8, 2.9, 2.10_

  - [x] 1.2 Implement header extraction from environ
    - Extract HTTP_* prefixed headers
    - Handle CONTENT_TYPE and CONTENT_LENGTH specially
    - _Requirements: 2.4, 2.5, 2.6_

  - [x] 1.3 Implement request body reading from wsgi.input
    - Read body respecting Content-Length
    - Handle missing Content-Length gracefully
    - _Requirements: 2.7, 2.11_

  - [x] 1.4 Implement parse() method to create Request objects
    - Combine all environ data into Request
    - Handle missing optional keys with defaults
    - _Requirements: 2.11_

  - [x] 1.5 Write property test for environ parsing round-trip
    - **Property 2: Environ Parsing Round-Trip**
    - **Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 2.9, 2.10, 2.11**

- [x] 2. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 3. Create response building components
  - [x] 3.1 Create `ResponseBuilder` class with status formatting
    - Implement format_status() with code and reason phrase
    - Use HTTP_STATUS_PHRASES lookup table
    - _Requirements: 3.1_

  - [x] 3.2 Implement header formatting and filtering
    - Format headers as list of (name, value) tuples
    - Filter out hop-by-hop headers
    - _Requirements: 3.2, 3.3_

  - [x] 3.3 Implement automatic header setting
    - Set Content-Type for responses with body
    - Set Content-Length when body size is known
    - _Requirements: 3.4, 3.5_

  - [x] 3.4 Implement build() method for full response conversion
    - Convert Response to (status, headers, body_iterator) tuple
    - Ensure body is encoded as bytes
    - _Requirements: 3.7_

  - [x] 3.5 Write property test for response formatting correctness
    - **Property 3: Response Formatting Correctness**
    - **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.7**

- [x] 4. Create response iterator
  - [x] 4.1 Create `ResponseIterator` class with iterator protocol
    - Implement __iter__() and __next__()
    - Support bytes, list, generator, and file inputs
    - _Requirements: 10.1, 10.5, 10.6, 10.7_

  - [x] 4.2 Implement close() method for resource cleanup
    - Close file handles
    - Invoke close_callback if provided
    - _Requirements: 10.3, 10.4_

  - [x] 4.3 Implement factory methods for different content types
    - from_bytes(), from_generator(), from_file()
    - _Requirements: 10.5, 10.6, 10.7_

  - [x] 4.4 Ensure all yielded content is bytes
    - Validate and encode content as needed
    - _Requirements: 10.2_

  - [x] 4.5 Write property test for response iterator protocol
    - **Property 8: Response Iterator Protocol**
    - **Validates: Requirements 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7, 10.8**

- [x] 5. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 6. Create request body parser
  - [x] 6.1 Create `RequestBodyParser` class with raw body reading
    - Implement parse_raw() with size limit enforcement
    - _Requirements: 7.1, 7.2_

  - [x] 6.2 Implement form-encoded body parsing
    - Parse application/x-www-form-urlencoded
    - _Requirements: 7.3_

  - [x] 6.3 Implement multipart form data parsing
    - Parse multipart/form-data for file uploads
    - Create UploadedFile objects
    - _Requirements: 7.4_

  - [x] 6.4 Implement JSON body parsing
    - Parse application/json bodies
    - Handle invalid JSON with BadRequest
    - _Requirements: 7.5_

  - [x] 6.5 Implement request body size limiting
    - Enforce max_request_body_size configuration
    - Return HTTP 413 when exceeded
    - _Requirements: 7.6, 7.7_

  - [x] 6.6 Write property test for request body parsing round-trip
    - **Property 5: Request Body Parsing Round-Trip**
    - **Validates: Requirements 7.1, 7.2, 7.3, 7.4, 7.5**

  - [x] 6.7 Write property test for request body size enforcement
    - **Property 6: Request Body Size Enforcement**
    - **Validates: Requirements 7.6, 7.7**

- [x] 7. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 8. Create error handler
  - [x] 8.1 Create `ErrorHandler` class with exception handling
    - Implement handle() method for exception dispatch
    - Support HTTPException subclasses
    - _Requirements: 8.1_

  - [x] 8.2 Implement unhandled exception handling
    - Return HTTP 500 for unhandled exceptions
    - Log exceptions with stack traces
    - _Requirements: 8.2, 8.3_

  - [x] 8.3 Implement debug vs production error formatting
    - Hide internal details in production mode
    - Include stack traces in debug mode
    - _Requirements: 8.4, 8.5_

  - [x] 8.4 Implement custom error handler registration
    - Support register_handler() for specific exception types
    - _Requirements: 8.8_

  - [x] 8.5 Write property test for error response correctness
    - **Property 7: Error Response Correctness**
    - **Validates: Requirements 8.1, 8.2, 8.3, 8.4, 8.5, 8.8**

- [x] 9. Create WSGI application core
  - [x] 9.1 Create `WSGIApplication` class with __call__ method
    - Accept environ and start_response arguments
    - Return response iterator
    - _Requirements: 1.1, 1.2_

  - [x] 9.2 Implement start_response calling
    - Call start_response before yielding body content
    - Support exc_info argument for error recovery
    - _Requirements: 1.3, 1.4_

  - [x] 9.3 Implement exception propagation
    - Propagate exceptions before start_response
    - Use exc_info for exceptions after start_response
    - _Requirements: 1.5, 1.6_

  - [x] 9.4 Implement response iterator close() calling
    - Call close() on response iterator when iteration completes
    - _Requirements: 1.7_

  - [x] 9.5 Write property test for WSGI interface compliance
    - **Property 1: WSGI Interface Compliance**
    - **Validates: Requirements 1.1, 1.2, 1.3**

  - [x] 9.6 Write property test for exception propagation
    - **Property 9: Exception Propagation**
    - **Validates: Requirements 1.5, 1.6**

- [x] 10. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 11. Implement middleware support
  - [x] 11.1 Create `WSGIMiddlewareWrapper` class
    - Implement wrap() for single middleware
    - Implement wrap_multiple() for middleware chain
    - _Requirements: 4.4_

  - [x] 11.2 Ensure environ modification propagation
    - Middleware environ changes visible to application
    - _Requirements: 4.2, 4.5_

  - [x] 11.3 Ensure response modification propagation
    - Middleware response changes returned to server
    - _Requirements: 4.3, 4.6_

  - [x] 11.4 Support middleware short-circuiting
    - Allow middleware to return without calling application
    - _Requirements: 4.7_

  - [x] 11.5 Maintain middleware execution order
    - Outer middleware wraps inner middleware
    - _Requirements: 4.8_

  - [x] 11.6 Write property test for middleware compatibility
    - **Property 4: Middleware Compatibility**
    - **Validates: Requirements 4.1, 4.2, 4.3, 4.5, 4.6, 4.7, 4.8**

- [x] 12. Implement framework environ extensions
  - [x] 12.1 Implement set_framework_environ() method
    - Set webworks.request with Request object
    - Set webworks.route with matched route
    - Set webworks.path_params with path parameters
    - _Requirements: 9.2, 9.3, 9.4_

  - [x] 12.2 Support custom environ keys from middleware
    - Preserve framework namespace keys
    - _Requirements: 9.1, 9.5_

  - [x] 12.3 Preserve standard WSGI environ keys
    - Do not modify standard keys
    - _Requirements: 9.6_

  - [x] 12.4 Write property test for framework environ extensions
    - **Property 10: Framework Environ Extensions**
    - **Validates: Requirements 9.1, 9.2, 9.3, 9.4, 9.5, 9.6**

- [x] 13. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.


- [x] 14. Create server configuration
  - [x] 14.1 Create `ServerConfig` dataclass
    - Define all configuration fields with defaults
    - Include network, worker, timeout, limit, and SSL settings
    - _Requirements: 15.1, 15.4, 15.6_

  - [x] 14.2 Implement from_environ() class method
    - Load configuration from environment variables
    - _Requirements: 15.2_

  - [x] 14.3 Implement from_file() class method
    - Load configuration from config file
    - _Requirements: 15.3_

  - [x] 14.4 Implement validate() method
    - Validate configuration values
    - Report errors clearly
    - _Requirements: 15.5_

- [x] 15. Create socket listener
  - [x] 15.1 Create `SocketListener` class
    - Implement bind() for IPv4 and IPv6
    - Support Unix domain sockets
    - _Requirements: 14.1, 14.2_

  - [x] 15.2 Implement socket options configuration
    - Set SO_REUSEADDR, SO_REUSEPORT
    - Configure backlog
    - _Requirements: 14.3_

  - [x] 15.3 Implement accept() method
    - Accept incoming connections
    - Return client socket and address
    - _Requirements: 5.2_

  - [x] 15.4 Implement SSL/TLS support
    - Wrap socket with SSL if configured
    - _Requirements: 14.6_

  - [x] 15.5 Implement close() method
    - Clean up server socket
    - _Requirements: 5.1_

- [x] 16. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 17. Create HTTP parser
  - [x] 17.1 Create `HTTPParser` class
    - Initialize with server config for limits
    - _Requirements: 11.4, 11.5_

  - [x] 17.2 Implement parse_request_line()
    - Parse HTTP method, path, and version
    - Support HTTP/1.0 and HTTP/1.1
    - _Requirements: 11.1, 11.9_

  - [x] 17.3 Implement parse_headers()
    - Parse HTTP headers according to RFC 7230
    - Handle header continuation lines
    - Enforce header size and count limits
    - _Requirements: 11.2, 11.3, 11.4, 11.5_

  - [x] 17.4 Implement chunked transfer encoding parsing
    - Parse chunked request bodies
    - _Requirements: 11.6_

  - [x] 17.5 Implement build_environ()
    - Construct valid WSGI environ from parsed request
    - Include all CGI and WSGI required keys
    - _Requirements: 5.3, 11.10_

  - [x] 17.6 Implement error handling for invalid requests
    - Return HTTP 400 for malformed requests
    - _Requirements: 11.7, 11.8_

  - [x] 17.7 Write property test for HTTP request parsing
    - **Property 11: HTTP Request Parsing Correctness**
    - **Validates: Requirements 11.1, 11.2, 11.3, 11.8, 11.9, 11.10**

  - [x] 17.8 Write property test for server environ construction
    - **Property 13: Server Environ Construction**
    - **Validates: Requirements 5.3, 5.4**

- [x] 18. Create HTTP writer
  - [x] 18.1 Create `HTTPWriter` class
    - Initialize with client socket and config
    - _Requirements: 12.1_

  - [x] 18.2 Implement write_status_line()
    - Write valid HTTP/1.1 status line
    - _Requirements: 12.1_

  - [x] 18.3 Implement write_headers()
    - Write headers in correct HTTP format
    - Add Date and Server headers
    - _Requirements: 12.2, 12.5, 12.6_

  - [x] 18.4 Implement write_body()
    - Write response body with Content-Length
    - _Requirements: 12.3_

  - [x] 18.5 Implement write_chunked()
    - Write response body using chunked transfer encoding
    - _Requirements: 12.4_

  - [x] 18.6 Implement flush()
    - Flush buffered data for streaming
    - _Requirements: 12.8_

  - [x] 18.7 Write property test for HTTP response generation
    - **Property 12: HTTP Response Generation Correctness**
    - **Validates: Requirements 12.1, 12.2, 12.3, 12.4, 12.5, 12.6**

- [x] 19. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 20. Create connection manager
  - [x] 20.1 Create `ConnectionManager` class
    - Initialize with server config
    - _Requirements: 5.9_

  - [x] 20.2 Implement should_keep_alive()
    - Determine keep-alive based on HTTP version and headers
    - _Requirements: 5.9, 14.7_

  - [x] 20.3 Implement connection tracking
    - Track active connections
    - Enforce max connections limit
    - _Requirements: 14.5_

  - [x] 20.4 Implement timeout handling
    - Handle connection timeouts
    - Close idle connections
    - _Requirements: 14.4, 14.7_

  - [x] 20.5 Write property test for keep-alive handling
    - **Property 14: Keep-Alive Connection Handling**
    - **Validates: Requirements 5.9, 14.7**

- [x] 21. Create StartResponse callable
  - [x] 21.1 Create `StartResponse` class
    - Capture status and headers
    - Track headers_sent state
    - _Requirements: 1.3_

  - [x] 21.2 Implement __call__() method
    - Accept status, headers, and optional exc_info
    - Return write callable for legacy support
    - _Requirements: 1.4, 5.4_

  - [x] 21.3 Implement write() method
    - Send headers if not sent
    - Write data to socket
    - _Requirements: 1.8_

  - [x] 21.4 Implement send_headers()
    - Write status and headers to client
    - Set Connection header for keep-alive
    - _Requirements: 12.7_

- [x] 22. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 23. Create worker process
  - [x] 23.1 Create `Worker` class
    - Initialize with app, listener, and config
    - _Requirements: 5.6, 5.7_

  - [x] 23.2 Implement run() main loop
    - Accept connections and handle requests
    - Support threading if configured
    - _Requirements: 5.2, 5.7_

  - [x] 23.3 Implement handle_connection()
    - Handle single connection with keep-alive support
    - _Requirements: 5.9_

  - [x] 23.4 Implement handle_request()
    - Parse HTTP, call app, write response
    - _Requirements: 5.4, 5.5_

  - [x] 23.5 Implement shutdown()
    - Graceful worker shutdown
    - _Requirements: 5.8_

- [x] 24. Create worker manager
  - [x] 24.1 Create `WorkerManager` class
    - Initialize with app, listener, and config
    - _Requirements: 13.1_

  - [x] 24.2 Implement spawn()
    - Spawn worker processes using fork/spawn
    - _Requirements: 13.1, 13.8_

  - [x] 24.3 Implement monitor()
    - Monitor worker health
    - Restart failed workers
    - _Requirements: 13.3, 13.5_

  - [x] 24.4 Implement shutdown()
    - Graceful shutdown of all workers
    - _Requirements: 13.4, 13.7_

  - [x] 24.5 Implement signal_workers()
    - Propagate signals to workers
    - _Requirements: 13.7_

  - [x] 24.6 Implement worker timeout handling
    - Kill workers that exceed timeout
    - _Requirements: 13.6_

- [x] 25. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 26. Create WSGI server
  - [x] 26.1 Create `WSGIServer` class
    - Initialize with app and config
    - _Requirements: 5.1_

  - [x] 26.2 Implement serve_forever()
    - Bind socket, spawn workers, enter main loop
    - _Requirements: 5.1, 5.2_

  - [x] 26.3 Implement shutdown()
    - Graceful and immediate shutdown support
    - _Requirements: 5.8_

  - [x] 26.4 Implement signal handlers
    - Handle SIGTERM, SIGINT, SIGHUP
    - _Requirements: 5.8_

  - [x] 26.5 Implement request logging
    - Log method, path, status, timing
    - _Requirements: 5.10_

  - [x] 26.6 Implement development mode
    - Auto-reload on code changes
    - _Requirements: 5.12_

  - [x] 26.7 Write property test for request size limit enforcement
    - **Property 15: Request Size Limit Enforcement**
    - **Validates: Requirements 11.4, 11.5, 7.6, 7.7**

  - [x] 26.8 Write property test for graceful shutdown
    - **Property 16: Graceful Shutdown**
    - **Validates: Requirements 5.8, 13.4, 13.7**

- [x] 27. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 28. Implement server integration helpers
  - [x] 28.1 Implement get_wsgi_application() function
    - Return configured WSGIApplication instance
    - _Requirements: 5a.1_

  - [x] 28.2 Implement create_wsgi_application() factory
    - Create new application instance per call
    - Support optional configuration dict
    - _Requirements: 5a.4, 5a.5_

  - [x] 28.3 Create module-level application variable
    - Set application variable for WSGI server convention
    - _Requirements: 5a.3_

  - [x] 28.4 Ensure external server compatibility
    - Verify compatibility with Gunicorn, uWSGI, etc.
    - _Requirements: 5a.2_

- [x] 29. Wire all components together
  - [x] 29.1 Integrate EnvironParser with WSGIApplication
    - Parse environ on each request
    - _Requirements: 2.1-2.11_

  - [x] 29.2 Integrate ResponseBuilder with WSGIApplication
    - Build WSGI response from framework Response
    - _Requirements: 3.1-3.7_

  - [x] 29.3 Integrate ErrorHandler with WSGIApplication
    - Handle all exceptions during request processing
    - _Requirements: 8.1-8.8_

  - [x] 29.4 Integrate RequestBodyParser with EnvironParser
    - Parse request bodies based on Content-Type
    - _Requirements: 7.1-7.7_

  - [x] 29.5 Integrate all server components
    - Wire HTTPParser, HTTPWriter, Worker, WorkerManager, WSGIServer
    - _Requirements: 5.1-5.12, 11.1-11.10, 12.1-12.8, 13.1-13.8, 14.1-14.8_

- [x] 30. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- All tasks are required for comprehensive implementation
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties
- Unit tests validate specific examples and edge cases
- Implementation uses Python with testbase framework per repository conventions
- Test files should be located at `source/testroots/automojo/tests/singlehost/webworks/wsgi/`
- WSGI specification reference: PEP 3333
- The built-in server reduces dependencies on external packages like Gunicorn
- Server components (tasks 14-27) implement the complete WSGI server stack
- Application components (tasks 1-13) implement the WSGI application interface
