# Implementation Plan: Production Server

## Overview

This implementation plan creates the Production Server feature providing worker management, concurrency options, and observability features for production deployments. The implementation builds on the webapp-persona feature and provides production-grade server capabilities.

## Tasks

- [x] 1. Create server configuration foundation
  - [x] 1.1 Create `ServerConfig` dataclass with all configuration options
    - Include binding, workers, connection, limits, SSL, process, logging, health, metrics, and tracing options
    - _Requirements: 1.1, 3.1, 3.2, 4.1, 4.2, 4.3, 10.1, 10.2_

  - [x] 1.2 Implement configuration validation and defaults
    - Auto-detect worker count based on CPU cores
    - Validate SSL configuration when provided
    - _Requirements: 1.2_

  - [x] 1.3 Create `ServerState` enum for lifecycle states
    - States: STOPPED, STARTING, RUNNING, SHUTTING_DOWN, RELOADING
    - _Requirements: 2.1, 2.7_

- [x] 2. Implement worker base classes
  - [x] 2.1 Create abstract `Worker` base class
    - Define run(), handle_request(), shutdown() methods
    - Include worker_id, state, request_count tracking
    - _Requirements: 1.1, 1.5_

  - [x] 2.2 Create `WorkerState` enum and `WorkerStatus` dataclass
    - States: IDLE, ACTIVE, SHUTTING_DOWN, STOPPED
    - _Requirements: 6.5_

  - [x] 2.3 Implement `SyncWorker` for WSGI applications
    - Thread pool for concurrent request handling
    - _Requirements: 3.1, 3.2, 3.6_

  - [x] 2.4 Implement `AsyncWorker` for ASGI applications
    - Asyncio event loop integration
    - _Requirements: 3.3, 3.7_

  - [x] 2.5 Implement `GeventWorker` for gevent-based concurrency
    - Greenlet pool for cooperative multitasking
    - _Requirements: 3.8_

- [x] 3. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Implement worker manager
  - [x] 4.1 Create `WorkerManager` class with worker spawning
    - Implement prefork model (spawn all workers before accepting requests)
    - Support configurable worker count
    - _Requirements: 1.1, 1.4_

  - [x] 4.2 Implement worker monitoring and crash recovery
    - Monitor worker health in background
    - Restart crashed workers within 5 seconds
    - _Requirements: 1.3, 1.8_

  - [x] 4.3 Implement max-requests worker recycling
    - Track request counts per worker
    - Restart workers after max-requests with jitter
    - _Requirements: 1.5, 1.6_

  - [x] 4.4 Implement worker timeout handling
    - Terminate workers exceeding request timeout
    - _Requirements: 1.7_

  - [x] 4.5 Write property test for worker configuration consistency
    - **Property 1: Worker Configuration Consistency**
    - **Validates: Requirements 1.1, 1.4, 1.8**

  - [x] 4.6 Write property test for worker restart on crash
    - **Property 2: Worker Restart on Crash**
    - **Validates: Requirements 1.3**

- [x] 5. Implement signal handling
  - [x] 5.1 Create `SignalHandler` class
    - Register handlers for SIGTERM, SIGINT, SIGHUP
    - _Requirements: 2.1, 2.2, 2.7_

  - [x] 5.2 Implement graceful shutdown on SIGTERM/SIGINT
    - Stop accepting new connections
    - Allow in-flight requests to complete
    - _Requirements: 2.1, 2.2, 2.3, 2.4_

  - [x] 5.3 Implement graceful timeout handling
    - Force terminate workers after timeout
    - _Requirements: 2.5, 2.6_

  - [x] 5.4 Implement configuration reload on SIGHUP
    - Reload without dropping connections
    - _Requirements: 2.7_

  - [x] 5.5 Implement shutdown progress logging
    - Log pending request counts during shutdown
    - _Requirements: 2.8_

  - [x] 5.6 Write property test for graceful shutdown behavior
    - **Property 3: Graceful Shutdown Behavior**
    - **Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 2.6**

- [x] 6. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 7. Implement connection management
  - [x] 7.1 Create `ConnectionManager` class
    - Track active connections
    - Enforce max connections limit
    - _Requirements: 4.3, 4.4_

  - [x] 7.2 Implement connection draining
    - Allow existing connections to complete during shutdown
    - Close idle keep-alive connections
    - _Requirements: 4.5, 4.6_

  - [x] 7.3 Implement request size limits
    - Limit request line size
    - Limit number of headers
    - _Requirements: 4.7, 4.8_

  - [x] 7.4 Implement backlog and keep-alive configuration
    - _Requirements: 4.1, 4.2_

- [x] 8. Implement health checks
  - [x] 8.1 Create `HealthChecker` class
    - Implement liveness and readiness checks
    - _Requirements: 5.5, 5.6_

  - [x] 8.2 Implement health check endpoint
    - Return HTTP 200 when healthy, 503 when unhealthy
    - Return JSON status information
    - _Requirements: 5.1, 5.2, 5.3, 5.4_

  - [x] 8.3 Implement configurable health check path
    - Bypass normal application routing
    - _Requirements: 5.7, 5.8_

  - [x] 8.4 Write property test for health check consistency
    - **Property 4: Health Check Consistency**
    - **Validates: Requirements 5.2, 5.3, 5.4, 5.7, 5.8**

- [x] 9. Implement metrics collection
  - [x] 9.1 Create `MetricsCollector` class
    - Track request count, latency, error rates
    - Track active connections and worker status
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

  - [x] 9.2 Implement Prometheus metrics endpoint
    - Expose metrics in Prometheus exposition format
    - _Requirements: 6.6_

  - [x] 9.3 Implement StatsD export
    - Support configurable StatsD host and port
    - _Requirements: 6.7, 6.8_

  - [x] 9.4 Write property test for metrics collection completeness
    - **Property 5: Metrics Collection Completeness**
    - **Validates: Requirements 6.1, 6.2, 6.3, 6.6**

- [x] 10. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 11. Implement structured logging
  - [x] 11.1 Create `StructuredLogger` class
    - Support JSON and standard log formats
    - _Requirements: 7.1_

  - [x] 11.2 Implement log entry formatting
    - Include timestamp, level, message, context fields
    - Include request_id and worker_id
    - _Requirements: 7.2, 7.3, 7.4_

  - [x] 11.3 Implement configurable log fields and output
    - Support stdout, stderr, and file output
    - Support access log and error log files
    - _Requirements: 7.5, 7.6, 7.7, 7.8_

  - [x] 11.4 Write property test for structured log format consistency
    - **Property 6: Structured Log Format Consistency**
    - **Validates: Requirements 7.1, 7.2, 7.3, 7.4**

- [x] 12. Implement request tracing
  - [x] 12.1 Create `RequestTracer` class
    - Generate unique request IDs
    - Accept incoming X-Request-ID header
    - _Requirements: 8.1, 8.2_

  - [x] 12.2 Implement request ID propagation
    - Include request_id in all log entries
    - Include request_id in response headers
    - _Requirements: 8.3, 8.4_

  - [x] 12.3 Implement span creation and tracing
    - Support OpenTelemetry trace context
    - Support configurable trace header
    - _Requirements: 8.5, 8.6, 8.7_

  - [x] 12.4 Implement trace export
    - Export traces to configurable backends
    - _Requirements: 8.8_

  - [x] 12.5 Write property test for request ID propagation
    - **Property 7: Request ID Propagation**
    - **Validates: Requirements 8.1, 8.2, 8.3, 8.4**

- [x] 13. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 14. Implement process management
  - [x] 14.1 Implement PID file handling
    - Write PID file on startup
    - Clean up PID file on shutdown
    - Refuse to start if PID file exists with running process
    - _Requirements: 9.1, 9.6, 9.7_

  - [x] 14.2 Implement daemon mode
    - Support running as background daemon
    - _Requirements: 9.2_

  - [x] 14.3 Implement privilege dropping
    - Support user and group options
    - Support umask configuration
    - _Requirements: 9.3, 9.4, 9.5_

  - [x] 14.4 Implement working directory change
    - Support chdir option
    - _Requirements: 9.8_

- [x] 15. Implement SSL/TLS support
  - [x] 15.1 Create `SSLManager` class
    - Create and configure SSL context
    - _Requirements: 10.1, 10.2, 10.3_

  - [x] 15.2 Implement cipher suite configuration
    - Support configurable cipher suites
    - _Requirements: 10.4_

  - [x] 15.3 Implement TLS version enforcement
    - Support TLS 1.2 and TLS 1.3
    - Reject deprecated versions
    - _Requirements: 10.5, 10.6, 10.7_

  - [x] 15.4 Implement HTTP to HTTPS redirect
    - Redirect when ssl-redirect is enabled
    - _Requirements: 10.8_

  - [x] 15.5 Write property test for TLS security enforcement
    - **Property 9: TLS Security Enforcement**
    - **Validates: Requirements 10.5, 10.6**

- [x] 16. Implement resource limits
  - [x] 16.1 Implement memory limit enforcement
    - Monitor worker memory usage
    - Restart workers exceeding limit
    - _Requirements: 11.1, 11.2_

  - [x] 16.2 Implement request body limit
    - Return HTTP 413 when exceeded
    - _Requirements: 11.3, 11.4_

  - [x] 16.3 Implement header size limits
    - Limit request field size
    - _Requirements: 11.5_

  - [x] 16.4 Implement resource limit warnings
    - Log warnings when approaching limits
    - Support worker temp directory
    - _Requirements: 11.6, 11.7, 11.8_

  - [x] 16.5 Write property test for resource limit enforcement
    - **Property 8: Resource Limit Enforcement**
    - **Validates: Requirements 11.2, 11.3, 11.4**

- [x] 17. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 18. Implement startup and initialization
  - [x] 18.1 Implement application preloading
    - Load application before forking workers
    - Share application code across workers
    - _Requirements: 12.1, 12.2_

  - [x] 18.2 Implement application factory support
    - Support factory pattern for application creation
    - _Requirements: 12.3_

  - [x] 18.3 Implement lifecycle hooks
    - Support on_starting, on_reload, when_ready, on_exit hooks
    - _Requirements: 12.4, 12.5, 12.6, 12.7_

  - [x] 18.4 Implement application load error handling
    - Exit with non-zero status and error message on failure
    - _Requirements: 12.8_

- [x] 19. Implement ProductionServer main class
  - [x] 19.1 Create `ProductionServer` class
    - Orchestrate all components
    - Implement start(), stop(), reload() methods
    - _Requirements: 1.1, 2.1, 2.7_

  - [x] 19.2 Wire all components together
    - Initialize worker manager, signal handler, health checker
    - Initialize metrics collector, structured logger, request tracer
    - _Requirements: All_

- [x] 20. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties
- Unit tests validate specific examples and edge cases
- Implementation uses Python with testbase framework per repository conventions
- Test files should be located at `source/testroots/ccai/tests/singlehost/webworks/prodserver/`
