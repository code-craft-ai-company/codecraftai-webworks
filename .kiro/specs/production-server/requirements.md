# Requirements Document

## Introduction

This document specifies the requirements for the Production Server feature. This feature provides production-grade server capabilities including worker management, concurrency options, and observability features for deploying web applications in production environments.

The feature enables reliable, scalable, and observable deployment of web applications with support for multiple worker processes, various concurrency models, and comprehensive monitoring and logging capabilities.

The production server is built on the built-in WSGI server (`ccai.webworks.wsgi`) and serves a WebApplication through its `wsgi_app` (revision of November 2026, audit finding WW-0174). It is run with `webworks prodserve` (every `--option` below is an option of that command, and a key of the `prodserver` configuration section) or with `ProductionServer(app, ServerConfig(...)).serve()`. The status of each requirement after the revision is listed at the end of this document.

## Glossary

- **Production_Server**: A server optimized for production deployment with features like worker management, graceful shutdown, and observability.
- **Worker**: An independent process or thread that handles incoming requests.
- **Worker_Manager**: A component responsible for spawning, monitoring, and managing worker processes.
- **Worker_Pool**: A collection of workers that collectively handle incoming requests.
- **Concurrency_Model**: The strategy used for handling multiple simultaneous requests (e.g., multi-process, multi-thread, async).
- **Graceful_Shutdown**: A shutdown procedure that allows in-flight requests to complete before terminating workers.
- **Health_Check**: An endpoint or mechanism that reports the server's operational status.
- **Metrics_Collector**: A component that gathers and exposes performance and operational metrics.
- **Request_Tracing**: The ability to track requests through the system with unique identifiers.
- **Structured_Logging**: Logging in a machine-parseable format (e.g., JSON) for log aggregation systems.
- **Signal_Handler**: A component that responds to OS signals for server control (e.g., SIGTERM, SIGHUP).
- **Prefork_Model**: A concurrency model where worker processes are spawned before accepting requests.
- **Connection_Draining**: The process of allowing existing connections to complete while refusing new ones during shutdown.

## Requirements

### Requirement 1: Worker Management

**User Story:** As a system administrator, I want worker process management, so that I can scale request handling capacity and ensure reliability.

#### Acceptance Criteria

1. THE Worker_Manager SHALL support configuring the number of worker processes via `--workers` option.
2. THE Worker_Manager SHALL default to a worker count based on available CPU cores when not specified.
3. WHEN a worker process crashes, THE Worker_Manager SHALL automatically restart it within 5 seconds.
4. THE Worker_Manager SHALL implement the Prefork_Model, spawning all workers before accepting requests.
5. THE Worker_Manager SHALL support `--max-requests` option to restart workers after handling a specified number of requests.
6. THE Worker_Manager SHALL support `--max-requests-jitter` option to add randomness to max-requests to prevent thundering herd.
7. WHEN `--timeout` is specified, THE Worker_Manager SHALL terminate workers that exceed the timeout for a single request.
8. THE Worker_Manager SHALL maintain a minimum number of workers even during high failure rates.

### Requirement 2: Graceful Shutdown

**User Story:** As a system administrator, I want graceful shutdown capabilities, so that in-flight requests complete without errors during deployments.

#### Acceptance Criteria

1. WHEN SIGTERM is received, THE Production_Server SHALL initiate graceful shutdown.
2. WHEN SIGINT is received, THE Production_Server SHALL initiate graceful shutdown.
3. DURING graceful shutdown, THE Production_Server SHALL stop accepting new connections.
4. DURING graceful shutdown, THE Production_Server SHALL allow in-flight requests to complete.
5. THE Production_Server SHALL support `--graceful-timeout` option to limit the graceful shutdown period.
6. IF graceful timeout is exceeded, THEN THE Production_Server SHALL forcefully terminate remaining workers.
7. WHEN SIGHUP is received, THE Production_Server SHALL replace its workers without dropping connections: the `on_reload` hook runs, new workers start, the old ones stop gracefully. (The server's own options are fixed at start; an application loaded by the workers from a factory is loaded again.)
8. THE Production_Server SHALL log shutdown progress including pending request counts.

### Requirement 3: Concurrency Options

**User Story:** As a developer, I want multiple concurrency options, so that I can choose the best model for my application's workload.

#### Acceptance Criteria

1. THE Production_Server SHALL support multi-process concurrency via `--workers` option.
2. THE Production_Server SHALL support multi-thread concurrency via `--threads` option.
3. THE Production_Server SHALL support async/await concurrency for ASGI applications. (Every worker class serves ASGI applications through the WSGI layer's ASGI bridge, whose event loop runs in each worker.)
4. THE Production_Server SHALL support combining processes and threads via `--workers` and `--threads` together.
5. WHEN `--worker-class` is specified, THE Production_Server SHALL use the specified worker implementation.
6. THE Production_Server SHALL provide sync worker class for WSGI applications.
7. THE Production_Server SHALL serve ASGI applications with its worker classes. (There is no separate `async` worker class; see 3.3.)
8. THE Production_Server SHALL support gevent worker class when gevent is installed, and SHALL refuse to start with a ConfigurationError naming the `gevent` extra when it is selected and gevent is not installed.

### Requirement 4: Connection Management

**User Story:** As a system administrator, I want connection management controls, so that I can optimize resource usage and prevent overload.

#### Acceptance Criteria

1. THE Production_Server SHALL support `--backlog` option to configure the connection queue size.
2. THE Production_Server SHALL support `--keep-alive` option to configure HTTP keep-alive timeout.
3. THE Production_Server SHALL support `--max-connections` option to limit concurrent connections per worker.
4. WHEN max connections is reached, THE Production_Server SHALL queue or reject new connections based on configuration.
5. THE Production_Server SHALL support Connection_Draining during graceful shutdown.
6. THE Production_Server SHALL close idle keep-alive connections during graceful shutdown.
7. THE Production_Server SHALL support `--limit-request-line` option to limit HTTP request line size.
8. THE Production_Server SHALL support `--limit-request-fields` option to limit number of HTTP headers.

### Requirement 5: Health Checks

**User Story:** As a system administrator, I want health check endpoints, so that load balancers and orchestrators can monitor server status.

#### Acceptance Criteria

1. THE Production_Server SHALL expose a health check endpoint at a configurable path.
2. THE health check endpoint SHALL return HTTP 200 when the server is healthy.
3. THE health check endpoint SHALL return HTTP 503 when the server is unhealthy or shutting down.
4. THE health check response SHALL include server status information in JSON format.
5. THE Production_Server SHALL support liveness checks that verify the process is running.
6. THE Production_Server SHALL support readiness checks that verify the application can handle requests.
7. THE health check endpoint SHALL be configurable via `--health-check-path` option.
8. THE health check endpoint SHALL bypass normal application routing for reliability.

### Requirement 6: Metrics Collection

**User Story:** As a system administrator, I want metrics collection, so that I can monitor server performance and resource usage.

#### Acceptance Criteria

1. THE Metrics_Collector SHALL track request count per endpoint.
2. THE Metrics_Collector SHALL track request latency histograms.
3. THE Metrics_Collector SHALL track error rates by status code.
4. THE Metrics_Collector SHALL track active connection count.
5. THE Metrics_Collector SHALL track worker process status (active, idle, restarting).
6. THE Metrics_Collector SHALL expose metrics in Prometheus format via configurable endpoint.
7. THE Metrics_Collector SHALL support StatsD export for metrics aggregation.
8. THE Production_Server SHALL support `--statsd-host` and `--statsd-port` options for StatsD configuration.

### Requirement 7: Structured Logging

**User Story:** As a system administrator, I want structured logging, so that logs can be easily parsed and aggregated.

#### Acceptance Criteria

1. THE Production_Server SHALL support JSON-formatted log output via `--log-format json` option.
2. THE structured logs SHALL include timestamp, level, message, and context fields.
3. THE structured logs SHALL include request_id for request correlation.
4. THE structured logs SHALL include worker_id to identify the source worker.
5. THE Production_Server SHALL support configurable log fields via `--log-config` option.
6. THE Production_Server SHALL support log output to stdout, stderr, or file.
7. THE Production_Server SHALL support `--access-log` option for access log file path.
8. THE Production_Server SHALL support `--error-log` option for error log file path.

### Requirement 8: Request Tracing

**User Story:** As a developer, I want request tracing, so that I can debug and monitor request flow through the system.

#### Acceptance Criteria

1. THE Production_Server SHALL generate a unique request_id for each incoming request.
2. THE Production_Server SHALL accept incoming request_id from `X-Request-ID` header if present.
3. THE Production_Server SHALL include request_id in all log entries for that request.
4. THE Production_Server SHALL include request_id in response headers via `X-Request-ID`.
5. THE Production_Server SHALL support OpenTelemetry trace context propagation.
6. THE Production_Server SHALL support `--trace-header` option to configure the trace header name.
7. WHEN tracing is enabled, THE Production_Server SHALL create spans for request handling.
8. THE Production_Server SHALL support exporting traces to configurable backends.

### Requirement 9: Process Management

**User Story:** As a system administrator, I want process management features, so that I can control and monitor the server reliably.

#### Acceptance Criteria

1. THE Production_Server SHALL support `--pid-file` option to write the master process PID.
2. THE Production_Server SHALL support `--daemon` option to run as a background daemon.
3. THE Production_Server SHALL support `--user` option to drop privileges after binding.
4. THE Production_Server SHALL support `--group` option to set the worker process group.
5. THE Production_Server SHALL support `--umask` option to set the file creation mask.
6. THE Production_Server SHALL clean up the PID file on shutdown.
7. IF the PID file already exists with a running process, THEN THE Production_Server SHALL refuse to start.
8. THE Production_Server SHALL support `--chdir` option to change working directory before loading the application.

### Requirement 10: SSL/TLS Support

**User Story:** As a system administrator, I want SSL/TLS support, so that I can serve HTTPS traffic directly.

#### Acceptance Criteria

1. THE Production_Server SHALL support `--ssl-certfile` option for the SSL certificate path.
2. THE Production_Server SHALL support `--ssl-keyfile` option for the SSL private key path.
3. THE Production_Server SHALL support `--ssl-ca-certs` option for client certificate verification.
4. THE Production_Server SHALL support `--ssl-ciphers` option to configure allowed cipher suites.
5. THE Production_Server SHALL support TLS 1.2 and TLS 1.3 protocols.
6. THE Production_Server SHALL reject connections using deprecated SSL/TLS versions.
7. THE Production_Server SHALL support `--ssl-version` option to set minimum TLS version.
8. WHEN `--ssl-redirect` is enabled, THE Production_Server SHALL redirect requests made over HTTP to HTTPS (301), whether TLS is terminated by the server or by a proxy in front of it that reports the client's scheme in `X-Forwarded-Proto`.

### Requirement 11: Resource Limits

**User Story:** As a system administrator, I want resource limit controls, so that I can prevent resource exhaustion.

#### Acceptance Criteria

1. THE Production_Server SHALL support `--limit-memory` option to set worker memory limits.
2. WHEN a worker exceeds memory limit, THE Worker_Manager SHALL restart that worker.
3. THE Production_Server SHALL support `--limit-request-body` option to limit request body size.
4. THE Production_Server SHALL return HTTP 413 when request body exceeds the limit.
5. THE Production_Server SHALL support `--limit-request-field-size` option to limit header value size.
6. THE Production_Server SHALL support file descriptor limits per worker.
7. THE Production_Server SHALL log warnings when approaching resource limits.
8. THE Production_Server SHALL support `--worker-tmp-dir` option for worker temporary files.

### Requirement 12: Startup and Initialization

**User Story:** As a developer, I want controlled startup behavior, so that the application initializes correctly before accepting traffic.

#### Acceptance Criteria

1. THE Production_Server SHALL support `--preload` option to load the application before forking workers.
2. WHEN preload is enabled, THE Production_Server SHALL share application code across workers.
3. THE Production_Server SHALL support application factory pattern via `--factory` option.
4. THE Production_Server SHALL support `--on-starting` hook for pre-startup initialization.
5. THE Production_Server SHALL support `--on-reload` hook for configuration reload handling.
6. THE Production_Server SHALL support `--when-ready` hook for post-startup actions.
7. THE Production_Server SHALL support `--on-exit` hook for cleanup on shutdown.
8. IF application loading fails, THEN THE Production_Server SHALL exit with non-zero status and error message.

## Implementation Status (November 2026)

Every criterion is implemented on the real request path unless noted here.

| Criterion | Status |
|---|---|
| 1.7 timeout per request | A WebApplication served through the ASGI bridge is answered 504 when its handler does not start a response within `--timeout`; `--timeout` is also the socket I/O timeout. A worker whose thread hangs inside a plain WSGI application is not killed. |
| 2.7 SIGHUP | Workers are replaced (see the criterion); the server's options are not re-read. |
| 3.3, 3.7 async | No `async` worker class; ASGI applications run on the ASGI bridge's event loop in every worker. |
| 3.8 gevent | Implemented (the WSGI worker after `gevent.monkey.patch_all()`), not exercised by the test suite because gevent is not installed in the development environment. |
| 6.7, 6.8 StatsD | `MetricsCollector.send_to_statsd()` and the options exist; the server does not send to StatsD by itself. |
| 7.5 `--log-config` | Not implemented. |
| 8.5, 8.8 tracing | The `traceparent` parent span ID is taken over; spans are exported to backends registered with `RequestTracer.register_export_backend` (in code); no OpenTelemetry exporter is bundled. |
| 11.6 file descriptor limits | Not implemented beyond `--max-connections` per worker. |
| 9.x, 10.x on Windows | The production server forks its workers, so it runs on POSIX only; on Windows `serve()` raises ConfigurationError. |
