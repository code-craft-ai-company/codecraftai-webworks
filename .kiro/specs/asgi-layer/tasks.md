# Implementation Plan: ASGI Layer

## Overview

This implementation plan creates the ASGI Layer feature providing the Asynchronous Server Gateway Interface application interface for the web framework. The implementation follows ASGI 3.0 specification and enables deployment on any ASGI-compliant server with support for HTTP, WebSocket, SSE, background tasks, and lifespan events.

## Tasks

- [x] 1. Create scope parsing foundation
  - [x] 1.1 Create `ScopeParser` class with basic HTTP scope extraction
    - Implement get_method(), get_path(), get_query_string()
    - Implement get_scheme(), get_server(), get_client()
    - Implement get_http_version(), get_root_path()
    - _Requirements: 2.1, 2.2, 2.3, 2.5, 2.6, 2.7, 2.8, 2.9_

  - [x] 1.2 Implement header extraction from scope
    - Convert list of (name, value) byte tuples to dict
    - Handle header name case normalization
    - _Requirements: 2.4_

  - [x] 1.3 Implement parse_http() method to create Request objects
    - Combine all scope data into Request
    - Handle missing optional keys with defaults
    - _Requirements: 2.10_

  - [x] 1.4 Write property test for HTTP scope parsing round-trip
    - **Property 2: HTTP Scope Parsing Round-Trip**
    - **Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 2.9, 2.10**

- [x] 2. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 3. Create request body reader
  - [x] 3.1 Create `BodyReader` class with async body reading
    - Implement read() to accumulate body chunks from receive()
    - Handle more_body flag to detect end of body
    - _Requirements: 3.1, 3.2_

  - [x] 3.2 Implement streaming body reader
    - Implement stream() as async generator yielding chunks
    - Support processing without buffering entire body
    - _Requirements: 3.3_

  - [x] 3.3 Implement request body size limiting
    - Enforce max_request_body_size configuration
    - Return HTTP 413 when exceeded
    - _Requirements: 3.7, 3.8_

  - [x] 3.4 Implement client disconnection handling
    - Detect "http.disconnect" message during body reading
    - Raise ClientDisconnected exception
    - _Requirements: 3.9_

  - [x] 3.5 Write property test for request body streaming
    - **Property 4: Request Body Streaming**
    - **Validates: Requirements 3.1, 3.2, 3.3**

  - [x] 3.6 Write property test for request body size enforcement
    - **Property 6: Request Body Size Enforcement**
    - **Validates: Requirements 3.7, 3.8**

- [x] 4. Create async body parsers
  - [x] 4.1 Implement async form-encoded body parsing
    - Parse application/x-www-form-urlencoded asynchronously
    - _Requirements: 3.4_

  - [x] 4.2 Implement async multipart form data parsing
    - Parse multipart/form-data for file uploads asynchronously
    - Create UploadedFile objects
    - _Requirements: 3.5_

  - [x] 4.3 Implement async JSON body parsing
    - Parse application/json bodies asynchronously
    - Handle invalid JSON with BadRequest
    - _Requirements: 3.6_

  - [x] 4.4 Write property test for request body parsing round-trip
    - **Property 5: Request Body Parsing Round-Trip**
    - **Validates: Requirements 3.4, 3.5, 3.6**

- [x] 5. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 6. Create response sender
  - [x] 6.1 Create `ResponseSender` class with message sending
    - Implement send_start() for http.response.start message
    - Implement send_body() for http.response.body message
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6_

  - [x] 6.2 Implement streaming response support
    - Implement send_streaming() for async generator bodies
    - Set more_body=True for intermediate chunks, False for final
    - _Requirements: 4.7, 4.9_

  - [x] 6.3 Implement header formatting
    - Convert header dict to list of byte tuples
    - _Requirements: 4.3_

  - [x] 6.4 Implement complete response sending
    - Implement send() to send full Response object
    - Ensure start message sent before body messages
    - _Requirements: 4.8_

  - [x] 6.5 Write property test for HTTP response message ordering
    - **Property 3: HTTP Response Message Ordering**
    - **Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.8, 4.9**

- [x] 7. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 8. Create HTTP handler
  - [x] 8.1 Create `HTTPHandler` class with request handling
    - Implement handle() for complete HTTP request/response cycle
    - Integrate ScopeParser, BodyReader, ResponseSender
    - _Requirements: 1.2, 9.1, 9.2_

  - [x] 8.2 Implement async middleware integration
    - Support async middleware in request pipeline
    - _Requirements: 9.3_

  - [x] 8.3 Implement async handler support
    - Support async request handlers
    - Support async database queries and external API calls
    - _Requirements: 9.2, 9.5_

  - [x] 8.4 Implement timeout support
    - Support timeouts for long-running async operations
    - _Requirements: 9.8_

- [x] 9. Create error handler
  - [x] 9.1 Create `ErrorHandler` class with async exception handling
    - Implement handle_http_error() for HTTP errors
    - Support HTTPException subclasses
    - _Requirements: 10.1_

  - [x] 9.2 Implement unhandled exception handling
    - Return HTTP 500 for unhandled exceptions
    - Log exceptions with stack traces
    - _Requirements: 10.2, 10.3_

  - [x] 9.3 Implement debug vs production error formatting
    - Hide internal details in production mode
    - Include stack traces in debug mode
    - _Requirements: 10.4, 10.5_

  - [x] 9.4 Implement custom error handler registration
    - Support register_handler() for specific exception types
    - _Requirements: 10.8_

  - [x] 9.5 Write property test for error response correctness
    - **Property 12: Error Response Correctness**
    - **Validates: Requirements 10.1, 10.2, 10.3, 10.4, 10.5, 10.8**

- [x] 10. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 11. Create WebSocket handler
  - [x] 11.1 Create `WebSocketHandler` class with connection handling
    - Implement handle() for WebSocket connection lifecycle
    - Receive "websocket.connect" event
    - _Requirements: 5.1, 5.2_

  - [x] 11.2 Implement connection accept/reject
    - Implement accept() to send "websocket.accept"
    - Implement reject() to send "websocket.close" before accept
    - Support subprotocol negotiation
    - _Requirements: 5.3, 5.4, 5.12_

  - [x] 11.3 Implement message sending
    - Implement send_text() for text messages
    - Implement send_bytes() for binary messages
    - _Requirements: 5.7, 5.8_

  - [x] 11.4 Implement message receiving
    - Implement receive_message() to get text or bytes
    - Handle "websocket.receive" messages
    - _Requirements: 5.5, 5.6_

  - [x] 11.5 Implement connection closing
    - Implement close() to send "websocket.close"
    - Handle "websocket.disconnect" event
    - Handle unexpected disconnections gracefully
    - _Requirements: 5.9, 5.10, 5.11_

  - [x] 11.6 Implement WebSocket error handling
    - Close connection with appropriate code on error
    - _Requirements: 10.6_

  - [x] 11.7 Write property test for WebSocket connection lifecycle
    - **Property 7: WebSocket Connection Lifecycle**
    - **Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8, 5.9, 5.10, 5.11**
C
- [x] 12. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 13. Create SSE handler
  - [x] 13.1 Create `SSEHandler` class with event streaming
    - Implement stream() for async generator event sources
    - Set Content-Type to "text/event-stream"
    - _Requirements: 6.1, 6.9_

  - [x] 13.2 Implement SSE event formatting
    - Format events with "data:", "event:", "id:", "retry:" fields
    - Separate events with double newline
    - _Requirements: 6.2, 6.3, 6.4, 6.5, 6.6_

  - [x] 13.3 Implement connection keep-alive
    - Keep connection open until explicitly closed
    - Detect client disconnection and clean up
    - _Requirements: 6.7, 6.8_

  - [x] 13.4 Implement SSE error handling
    - Close stream gracefully on error
    - _Requirements: 10.7_

  - [x] 13.5 Write property test for SSE event formatting
    - **Property 8: SSE Event Formatting**
    - **Validates: Requirements 6.2, 6.3, 6.4, 6.5, 6.6**

- [x] 14. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 15. Create background tasks manager
  - [x] 15.1 Create `BackgroundTasks` class with task scheduling
    - Implement add_task() to schedule async functions
    - Support passing arguments to tasks
    - _Requirements: 7.1, 7.7_

  - [x] 15.2 Implement task execution
    - Implement run() to execute tasks after response
    - Execute in same event loop as request
    - Execute in order of scheduling
    - _Requirements: 7.2, 7.4, 7.5_

  - [x] 15.3 Implement non-blocking response delivery
    - Ensure response is not delayed by background tasks
    - _Requirements: 7.3_

  - [x] 15.4 Implement error handling for background tasks
    - Log errors without affecting response
    - _Requirements: 7.6_

  - [x] 15.5 Implement task cancellation
    - Support cancellation of pending tasks on shutdown
    - _Requirements: 7.8_

  - [x] 15.6 Write property test for background task execution order
    - **Property 9: Background Task Execution Order**
    - **Validates: Requirements 7.1, 7.3, 7.4, 7.5, 7.6**

- [x] 16. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 17. Create lifespan handler
  - [x] 17.1 Create `LifespanHandler` class with event handling
    - Implement handle() for lifespan scope
    - Receive "lifespan.startup" and "lifespan.shutdown" events
    - _Requirements: 8.1, 8.2, 8.5_

  - [x] 17.2 Implement startup handling
    - Send "lifespan.startup.complete" on success
    - Send "lifespan.startup.failed" with message on failure
    - _Requirements: 8.3, 8.4_

  - [x] 17.3 Implement shutdown handling
    - Send "lifespan.shutdown.complete" on success
    - Send "lifespan.shutdown.failed" with message on failure
    - _Requirements: 8.6, 8.7_

  - [x] 17.4 Implement handler registration
    - Implement on_startup() decorator for startup handlers
    - Implement on_shutdown() decorator for shutdown handlers
    - Support multiple handlers
    - _Requirements: 8.8, 8.9_

  - [x] 17.5 Implement handler execution ordering
    - Execute startup handlers in registration order
    - Execute shutdown handlers in reverse registration order
    - Prevent request acceptance on startup failure
    - _Requirements: 8.10, 8.11, 8.12_

  - [x] 17.6 Write property test for lifespan handler ordering
    - **Property 10: Lifespan Handler Ordering**
    - **Validates: Requirements 8.8, 8.9, 8.10, 8.11, 8.12**

  - [x] 17.7 Write property test for lifespan protocol compliance
    - **Property 11: Lifespan Protocol Compliance**
    - **Validates: Requirements 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7**

- [x] 18. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 19. Create ASGI application core
  - [x] 19.1 Create `ASGIApplication` class with __call__ method
    - Accept scope, receive, and send arguments
    - Dispatch based on scope['type']
    - _Requirements: 1.1, 1.2, 1.3, 1.4_

  - [x] 19.2 Implement unknown scope type handling
    - Raise exception or return gracefully for unknown types
    - _Requirements: 1.5_

  - [x] 19.3 Implement async/await support throughout
    - Support async handlers and middleware
    - Integrate with asyncio event loop
    - _Requirements: 1.6, 9.6_

  - [x] 19.4 Ensure ASGI 3.0 compatibility
    - Verify compliance with ASGI 3.0 specification
    - _Requirements: 1.7_

  - [x] 19.5 Write property test for ASGI interface compliance
    - **Property 1: ASGI Interface Compliance**
    - **Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7**

- [x] 20. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 21. Implement framework scope extensions
  - [x] 21.1 Implement set_framework_scope() method
    - Set webworks.request with Request object
    - Set webworks.route with matched route
    - Set webworks.path_params with path parameters
    - _Requirements: 12.2, 12.3, 12.4_

  - [x] 21.2 Support custom scope keys from middleware
    - Preserve framework namespace keys
    - _Requirements: 12.1, 12.5_

  - [x] 21.3 Preserve standard ASGI scope keys
    - Do not modify standard keys
    - Support state key per ASGI spec
    - _Requirements: 12.6, 12.7_

  - [x] 21.4 Write property test for framework scope extensions
    - **Property 13: Framework Scope Extensions**
    - **Validates: Requirements 12.1, 12.2, 12.3, 12.4, 12.5, 12.6, 12.7**

- [x] 22. Implement server integration
  - [x] 22.1 Implement get_asgi_application() function
    - Return configured ASGIApplication instance
    - _Requirements: 11.1_

  - [x] 22.2 Implement create_asgi_application() factory
    - Create new application instance per call
    - Support optional configuration dict
    - _Requirements: 11.5, 11.6_

  - [x] 22.3 Create module-level application variable
    - Set application variable for ASGI server convention
    - _Requirements: 11.7_

  - [x] 22.4 Support lifespan protocol configuration
    - Support running with lifespan enabled or disabled
    - _Requirements: 11.8_

- [x] 23. Wire all components together
  - [x] 23.1 Integrate ScopeParser with ASGIApplication
    - Parse scope on each HTTP request
    - _Requirements: 2.1-2.10_

  - [x] 23.2 Integrate HTTPHandler with ASGIApplication
    - Handle HTTP scope type
    - _Requirements: 1.2_

  - [x] 23.3 Integrate WebSocketHandler with ASGIApplication
    - Handle WebSocket scope type
    - _Requirements: 1.3_

  - [x] 23.4 Integrate LifespanHandler with ASGIApplication
    - Handle lifespan scope type
    - _Requirements: 1.4_

  - [x] 23.5 Integrate ErrorHandler with all handlers
    - Handle exceptions in HTTP, WebSocket, and SSE
    - _Requirements: 10.1-10.8_

  - [x] 23.6 Integrate BackgroundTasks with HTTPHandler
    - Execute background tasks after response
    - _Requirements: 7.1-7.8_

- [x] 24. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties
- Unit tests validate specific examples and edge cases
- Implementation uses Python with testbase framework per repository conventions
- Test files should be located at `source/testroots/automojo/tests/singlehost/webworks/asgi/`
- ASGI specification reference: https://asgi.readthedocs.io/

