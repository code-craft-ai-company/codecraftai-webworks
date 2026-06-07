# Implementation Plan: Development Server (ASGI)

## Overview

Implement a development ASGI server by creating three new modules (`asyncservercore.py`, `httpprotocolhandler.py`, `lifespanmanager.py`) and enhancing the existing `DevelopmentServer` class to bind a TCP socket, accept HTTP connections, parse HTTP/1.1 requests, construct ASGI scopes, and invoke the ASGI application. All code uses Python standard library only (`asyncio`, `socket`). Tests use the `testbase` framework.

## Tasks

- [x] 1. Implement HTTP/1.1 protocol handler
  - [x] 1.1 Create `source/packages/ccai/webworks/devexp/server/httpprotocolhandler.py` with the `HTTPProtocolHandler` class
    - Implement `asyncio.Protocol` subclass with `connection_made`, `data_received`, `connection_lost` callbacks
    - Implement `_ParseState` enum for incremental parsing states
    - Implement `_parse_request_line(line)` to extract method, target, version from request line bytes
    - Implement `_parse_headers(header_block)` to parse headers into list of `(name_bytes, value_bytes)` tuples
    - Implement chunked transfer decoding in `_decode_chunked(data)` method
    - Enforce request line limit of 8192 bytes (return 400) and header block limit of 32768 bytes (return 431)
    - Implement `_build_scope(method, path, query, version, headers)` to construct ASGI scope dictionary with all required keys: `type`, `asgi`, `http_version`, `method`, `path`, `raw_path`, `root_path`, `scheme`, `query_string`, `headers`, `server`, `client`
    - Implement `async _receive()` returning `http.request` messages with `body` and `more_body` flag
    - Implement `async _send(message)` with state machine enforcing `http.response.start` before `http.response.body`
    - Implement `_write_response(status, headers, body)` to serialize HTTP response bytes to transport
    - Implement `_should_keep_alive(version, headers)` for HTTP/1.0 and HTTP/1.1 connection persistence logic
    - Implement `_send_error_response(status_code, message)` for error responses with `Connection: close`
    - Implement `async _handle_request()` to call `app(scope, receive, send)` with debug/non-debug error handling
    - Implement 30-second keep-alive idle timeout using `asyncio.wait_for`
    - _Requirements: 1.2, 1.5, 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 8.2, 8.3, 11.1, 11.2, 11.3, 11.4, 12.2_

  - [x] 1.2 Write property test for HTTP request parsing round trip (`test_httpprotocolhandler.py`)
    - **Property 1: HTTP Request Parsing Round Trip**
    - Generate random valid HTTP methods, paths, versions, headers; serialize to raw bytes; parse with `_parse_request_line` and `_parse_headers`; verify recovery of original values
    - Minimum 100 iterations
    - **Validates: Requirements 2.1, 2.2**

  - [x] 1.3 Write property test for Content-Length body integrity (`test_httpprotocolhandler.py`)
    - **Property 2: Content-Length Body Integrity**
    - Generate random body bytes with matching Content-Length; parse; verify body length and content match
    - Minimum 100 iterations
    - **Validates: Requirements 2.3**

  - [x] 1.4 Write property test for chunked transfer decoding round trip (`test_httpprotocolhandler.py`)
    - **Property 3: Chunked Transfer Decoding Round Trip**
    - Generate random byte sequences; encode as chunked transfer; decode; verify identity
    - Minimum 100 iterations
    - **Validates: Requirements 2.4**

  - [x] 1.5 Write property test for ASGI scope completeness (`test_httpprotocolhandler.py`)
    - **Property 4: ASGI Scope Completeness and Type Correctness**
    - Generate random request parameters; build scope; verify all required keys present with correct types
    - Minimum 100 iterations
    - **Validates: Requirements 1.5, 3.1, 3.2, 3.4, 3.6, 3.7**

  - [x] 1.6 Write property test for query string separation (`test_httpprotocolhandler.py`)
    - **Property 5: Query String Separation**
    - Generate random paths with query strings containing `?`; build scope; verify `path` is portion before first `?` and `query_string` is bytes after
    - Minimum 100 iterations
    - **Validates: Requirements 3.3**

  - [x] 1.7 Write property test for header lowercase normalization (`test_httpprotocolhandler.py`)
    - **Property 6: Header Lowercase Normalization**
    - Generate random headers with mixed casing; build scope; verify all header names are lowercase bytes and values are preserved
    - Minimum 100 iterations
    - **Validates: Requirements 3.5**

  - [x] 1.8 Write property test for receive callable body delivery (`test_httpprotocolhandler.py`)
    - **Property 7: Receive Callable Body Delivery**
    - Generate random request bodies; call receive sequence; verify concatenation equals original body and final message has `more_body=False`
    - Minimum 100 iterations
    - **Validates: Requirements 4.1, 4.2**

  - [x] 1.9 Write property test for HTTP response serialization (`test_httpprotocolhandler.py`)
    - **Property 8: HTTP Response Serialization**
    - Generate random status codes, response headers, body bytes; serialize with `_write_response`; verify valid HTTP/1.1 response format
    - Minimum 100 iterations
    - **Validates: Requirements 4.4**

  - [x] 1.10 Write property test for debug mode error response detail control (`test_httpprotocolhandler.py`)
    - **Property 9: Debug Mode Error Response Detail Control**
    - Generate random exceptions; verify 500 response contains exception details when debug=True and excludes them when debug=False
    - Minimum 100 iterations
    - **Validates: Requirements 8.2, 8.3**

  - [x] 1.11 Write property test for keep-alive decision (`test_httpprotocolhandler.py`)
    - **Property 11: Keep-Alive Decision**
    - Test all combinations of HTTP version (`1.0`, `1.1`) and Connection header (absent, `keep-alive`, `close`); verify `_should_keep_alive` returns correct boolean
    - **Validates: Requirements 11.1, 11.2, 11.3**

  - [x] 1.12 Write unit tests for HTTP parsing edge cases (`test_httpprotocolhandler.py`)
    - Test malformed request line returns 400
    - Test request line exceeding 8192 bytes returns 400
    - Test header block exceeding 32768 bytes returns 431
    - Test empty body with Content-Length: 0
    - Test send `http.response.body` before `http.response.start` logs error and closes connection
    - _Requirements: 2.5, 2.6, 4.6_

- [x] 2. Checkpoint - Ensure all HTTP protocol handler tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 3. Implement lifespan manager
  - [x] 3.1 Create `source/packages/ccai/webworks/devexp/server/lifespanmanager.py` with the `LifespanManager` class
    - Implement `__init__(app)` storing app reference
    - Implement `async startup()` that creates lifespan scope `{"type": "lifespan", "asgi": {"version": "3.0"}}`, calls `app(scope, receive, send)` using `asyncio.Queue` for receive/send channels, sends `lifespan.startup` event, waits for `lifespan.startup.complete` or `lifespan.startup.failed`
    - Implement `async shutdown()` that sends `lifespan.shutdown` event and waits for `lifespan.shutdown.complete` or `lifespan.shutdown.failed`
    - Implement `startup_complete`, `startup_failed`, `failure_message` properties
    - Catch exceptions from apps that don't support lifespan and proceed as successful
    - _Requirements: 5.1, 5.2, 5.3, 5.4_

  - [x] 3.2 Write unit tests for lifespan manager (`test_lifespanmanager.py`)
    - Test app that sends `lifespan.startup.complete` — startup succeeds
    - Test app that sends `lifespan.startup.failed` — startup fails with message
    - Test app that raises on lifespan scope — manager proceeds as successful
    - Test app that sends `lifespan.shutdown.complete` — shutdown succeeds
    - Test app that sends `lifespan.shutdown.failed` — shutdown fails with message
    - _Requirements: 5.1, 5.2, 5.3, 5.4_

- [x] 4. Implement async server core
  - [x] 4.1 Create `source/packages/ccai/webworks/devexp/server/asyncservercore.py` with the `AsyncServerCore` class
    - Implement `__init__(app, host, port, shutdown_timeout=5, keepalive_timeout=30)` storing config and initializing state
    - Implement `async start()` using `loop.create_server()` with protocol factory to bind TCP socket
    - Implement `async stop()` that calls `server.close()`, waits up to `shutdown_timeout` for active connections to drain, then forcibly closes remaining transports
    - Implement `_create_protocol()` factory method returning new `HTTPProtocolHandler` instances
    - Implement `register_connection(handler)` and `unregister_connection(handler)` for tracking active connections
    - Implement `server`, `is_running`, `active_connections` properties
    - _Requirements: 1.1, 1.2, 1.5, 6.1, 6.2, 6.5, 12.1_

  - [x] 4.2 Write property test for connection acceptance scaling (`test_asyncservercore.py`)
    - **Property 12: Connection Acceptance Scaling**
    - Generate random connection counts; connect; verify `active_connections` matches open connection count
    - Minimum 100 iterations
    - **Validates: Requirements 1.2**

  - [x] 4.3 Write unit tests for async server core (`test_asyncservercore.py`)
    - Test server binds to configured host and port
    - Test server stops accepting after `stop()` is called
    - Test port is released after shutdown
    - Test in-flight request completes within shutdown timeout
    - _Requirements: 1.1, 6.1, 6.2, 6.5_

- [x] 5. Checkpoint - Ensure all server core and lifespan tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 6. Enhance DevelopmentServer and integrate components
  - [x] 6.1 Update `source/packages/ccai/webworks/devexp/server/devserver.py` to integrate async server core
    - Add `_server_core`, `_lifespan_manager`, `_shutdown_event` instance variables
    - Update `start()` to create `AsyncServerCore` and `LifespanManager`, then run `asyncio.run(self._run_async())` to block the calling thread
    - Implement `async _run_async()` that runs lifespan startup, starts server core, installs signal handlers, awaits shutdown event, runs lifespan shutdown, stops server core
    - Implement `_setup_signal_handlers(loop)` to register SIGINT/SIGTERM handlers that set the shutdown event
    - Update `stop()` to signal the shutdown event
    - Update `_setup_debug_middleware()` to configure debug middleware on the ASGI application before starting the server core
    - Update `_restart_server()` to stop/start the `AsyncServerCore` for file-change reload, incrementing `restart_count` on success, catching `SyntaxError`/`ImportError` and logging on failure
    - _Requirements: 1.1, 1.4, 5.1, 5.2, 5.3, 6.1, 6.2, 6.3, 6.4, 6.5, 7.1, 8.1, 10.2, 10.3, 10.4_

  - [x] 6.2 Write property test for reload restart count increment (`test_devserver.py`)
    - **Property 13: Reload Restart Count Increment**
    - Perform random number of successful reloads; verify `restart_count` equals number of reloads
    - Minimum 100 iterations
    - **Validates: Requirements 10.4**

  - [x] 6.3 Write unit tests for DevelopmentServer integration (`test_devserver.py`)
    - Test `start()` blocks the calling thread until stopped
    - Test SIGINT/SIGTERM triggers graceful shutdown
    - Test lifespan startup failure stops the server
    - Test SyntaxError during reload logs error and continues watching
    - Test successful reload increments `restart_count`
    - _Requirements: 1.4, 5.2, 6.3, 6.4, 10.3, 10.4_

- [x] 7. Integrate request logging with HTTP protocol handler
  - [x] 7.1 Update `HTTPProtocolHandler` to call `RequestLogger` after each request completes
    - Pass the request logger instance from `DevelopmentServer` through `AsyncServerCore` to each `HTTPProtocolHandler`
    - Log method, path, status code, and elapsed time in milliseconds after each response is sent
    - Log error status code when request results in error before response is sent
    - _Requirements: 9.1, 9.2, 9.3_

  - [x] 7.2 Write property test for request log format (`test_requestlogger.py`)
    - **Property 10: Request Log Format**
    - Generate random method, path, status code, elapsed time; format log; verify single line matching `"{method} {path} {status_code} {elapsed_ms}ms"`
    - Minimum 100 iterations
    - **Validates: Requirements 9.1, 9.2**

- [x] 8. Update ServeCommand CLI integration
  - [x] 8.1 Update `source/packages/ccai/webworks/devexp/server/servecommand.py` if needed
    - Verify `ServeCommand.execute()` correctly passes host, port, debug, reload, and watch_patterns to `DevelopmentServer`
    - Verify `start()` blocks until server is stopped and returns `EXIT_SUCCESS`
    - Verify `PortInUseError` is caught and returns `EXIT_ERROR`
    - _Requirements: 7.1, 7.2, 7.3, 7.4_

  - [x] 8.2 Write unit tests for ServeCommand integration (`test_servecommand.py`)
    - Test `PortInUseError` returns `EXIT_ERROR`
    - Test normal shutdown returns `EXIT_SUCCESS`
    - Test arguments are passed correctly to `DevelopmentServer`
    - _Requirements: 7.1, 7.2, 7.3, 7.4_

- [x] 9. Update package `__init__.py` exports
  - [x] 9.1 Update `source/packages/ccai/webworks/devexp/server/__init__.py` to export new classes
    - Export `AsyncServerCore`, `HTTPProtocolHandler`, `LifespanManager`
    - Ensure no new third-party dependencies are added
    - _Requirements: 12.1, 12.2, 12.3_

- [x] 10. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties using loop-based iteration (min 100 iterations), not hypothesis
- All tests use the `testbase` framework (not pytest/unittest/hypothesis)
- Test files go under `source/testroots/ccai/tests/singlehost/webworks/devexp/server/`
- Source files go under `source/packages/ccai/webworks/devexp/server/`
