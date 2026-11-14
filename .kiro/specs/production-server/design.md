# Design Document: Production Server

## Overview

This design document describes the architecture and implementation approach for the Production Server feature. The feature provides production-grade server capabilities including worker management, concurrency options, and observability features for deploying web applications in production environments.

Key design principles:
- Reliability: Automatic worker recovery and graceful shutdown
- Scalability: Multiple concurrency models to match workload characteristics
- Observability: Comprehensive metrics, logging, and tracing
- Security: TLS support and resource limits
- Flexibility: Extensive configuration options for different deployment scenarios

## Architecture

The production server is the built-in WSGI server (`ccai.webworks.wsgi`) with a
production layer on top (revision of November 2026, audit finding WW-0174; the
first implementation had in-process stub workers and never bound a socket).
There is one socket server in the package: `wsgi.WSGIServer` binds, parses
HTTP/1.1, pre-forks the workers, runs their threads, terminates TLS, shuts down
gracefully and replaces workers; `ProductionServer` subclasses it.

```
                        master process
┌──────────────────────────────────────────────────────────────────────────┐
│ ProductionServer(WSGIServer)                                              │
│   serve(): validate ─ on_starting ─ chdir ─ daemon ─ TLS context (SSLManager)│
│            ─ bind (SocketListener) ─ _after_bind:                         │
│                PID file ─ log files ─ drop privileges ─ worker tmp dir    │
│                ─ load application (preload/object) ─ build pipeline       │
│            ─ spawn workers (wsgi.WorkerManager, fork) ─ when_ready        │
│            ─ main loop: reap/replace workers, SIGHUP -> replace_workers   │
│            ─ SIGTERM/SIGINT -> graceful shutdown ─ on_exit ─ cleanup      │
│   exit callback: MetricsStore.retire_worker(pid)                          │
└──────────────────────────────────────────────────────────────────────────┘
                 │ fork (shared listening socket)
                 ▼
                        worker process (xN)
┌──────────────────────────────────────────────────────────────────────────┐
│ wsgi.Worker: accept loop + `threads` handler threads, HTTPParser limits   │
│   (413/414/431 before the app), keep-alive, max_requests recycling        │
│   app = ProductionMiddleware(application)                                  │
│     on_worker_start: logger context, request-id log filter, health       │
│        checks, metrics snapshot writer, application.on_worker_start       │
│        (ASGIBridge: event loop thread + lifespan startup)                 │
│     per request: request ID ─ 431 per header field ─ /health ─ /metrics   │
│        ─ HTTPS redirect ─ request timeout into the environ ─ application  │
│        ─ access log, metrics, span, memory limit                          │
│   application = WebApplication.wsgi_app (ASGIBridge) or any WSGI callable │
└──────────────────────────────────────────────────────────────────────────┘
```

Removed in the revision, because the WSGI layer does the work for real:
`Worker`, `SyncWorker`, `AsyncWorker`, `GeventWorker`, the production
`WorkerManager`, `SignalHandler`, `ConnectionManager`, `ShutdownCoordinator`
and `ReloadCoordinator`. The `async` worker class is gone: ASGI applications
are served through the ASGI bridge, whose event loop runs in every worker. The
`gevent` worker class is the WSGI worker run after `gevent.monkey.patch_all()`
in the new worker process; selecting it without the `gevent` extra is a
ConfigurationError.

The ProductionServer only runs where `os.fork` exists (POSIX); elsewhere
`serve()` raises ConfigurationError.

## Components and Interfaces

### Server Configuration

```python
@dataclass
class ServerConfig:
    """
    Configuration for the production server.
    """
    
    # Binding
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Workers
    workers: int = 0  # 0 = auto-detect based on CPU cores
    threads: int = 1
    worker_class: str = "sync"
    max_requests: Optional[int] = None
    max_requests_jitter: int = 0
    timeout: int = 30
    graceful_timeout: int = 30
    
    # Connection
    backlog: int = 2048
    keep_alive: int = 5
    max_connections: Optional[int] = None
    
    # Limits
    limit_request_line: int = 4094
    limit_request_fields: int = 100
    limit_request_field_size: int = 8190
    limit_request_body: int = 16 * 1024 * 1024  # the body is held in memory; 0 = unlimited
    limit_memory: Optional[int] = None          # resident bytes per worker
    worker_tmp_dir: Optional[str] = None        # parent of the workers' shared directory
    
    # SSL/TLS
    ssl_certfile: Optional[str] = None
    ssl_keyfile: Optional[str] = None
    ssl_ca_certs: Optional[str] = None
    ssl_ciphers: str = "TLS_AES_256_GCM_SHA384:TLS_CHACHA20_POLY1305_SHA256"
    ssl_version: str = "TLSv1_2"
    ssl_redirect: bool = False
    
    # Process
    pid_file: Optional[str] = None
    daemon: bool = False
    user: Optional[str] = None
    group: Optional[str] = None
    umask: int = 0
    chdir: Optional[str] = None
    preload: bool = False
    
    # Logging
    log_format: str = "standard"  # "standard" or "json"
    access_log: Optional[str] = None
    error_log: Optional[str] = None
    log_level: str = "INFO"
    
    # Health checks
    health_check_path: str = "/health"
    
    # Metrics
    metrics_path: str = "/metrics"
    statsd_host: Optional[str] = None
    statsd_port: int = 8125
    
    # Tracing
    trace_header: str = "X-Request-ID"
    enable_tracing: bool = False
    
    # Hooks
    on_starting: Optional[Callable] = None
    on_reload: Optional[Callable] = None
    when_ready: Optional[Callable] = None
    on_exit: Optional[Callable] = None
```

### Production Server

```python
class ProductionServer(WSGIServer):
    def __init__(self, app=None, config: ServerConfig = None, app_factory=None): ...
        # exactly one of app (WebApplication, ASGI app or WSGI callable, loaded
        # already) and app_factory (called in the master with preload, else in
        # every worker)
    def serve(self) -> int: ...          # blocks; returns an EXIT_* code
    def stop(self, graceful=True): ...   # thread-safe
    def reload(self): ...                # as SIGHUP: replace the workers
    def get_status(self) -> dict: ...
    # WSGIServer hooks: _setup_ssl, _after_bind, _create_worker_manager,
    # _after_spawn, _handle_sigint (graceful), _handle_reload (replace workers)
```

Startup order: configuration validation (ConfigurationError ends the run),
`on_starting`, `chdir`, daemon, TLS context (the key is read while privileged),
bind, PID file (refuses to start when it names a running process), log files,
privilege drop (umask, group, user), worker temp directory, application
loading, workers, `when_ready`. Exit codes: `EXIT_SUCCESS`, `EXIT_BIND_ERROR`,
`EXIT_PID_FILE_ERROR`, `EXIT_APP_LOAD_ERROR` (the application could not be
loaded in the master, or a worker failed to boot: the server stops instead of
restarting workers that fail the same way), `EXIT_ERROR`.

### Production Middleware

`ProductionMiddleware` (WSGI middleware, `prodserver/productionmiddleware.py`)
puts the production features on the request path of every worker:

| Feature | How |
|---|---|
| Request ID | `RequestTracer.get_or_create_request_id`: a received plain token (≤128 chars of `[A-Za-z0-9._:/+=@-]`) is kept, otherwise a UUID is generated; written into the trace header of the environ (the application sees it), `environ["webworks.request_id"]`, the `current_request_id` contextvar (copied into the ASGI task by the bridge; `RequestIdLogFilter` adds `record.request_id`), the response header and the access log |
| Header field size | `ResourceLimiter.validate_header_field_size` per field → 431 |
| Health | `HealthChecker` at `health_check_path` (GET/HEAD), JSON, 200 or 503 when the worker drains or the application cannot serve (failed lifespan) |
| Metrics | `metrics_path` (GET/HEAD), Prometheus text of the totals of all workers (`MetricsStore`) |
| HTTPS redirect | `ssl_redirect`: requests whose scheme is http (X-Forwarded-Proto, else `wsgi.url_scheme`) get 301 to https |
| Request time limit | `timeout` into `environ["webworks.request_timeout"]`; the ASGI bridge answers 504 |
| Access log | `StructuredLogger.access_log` with request_id, worker_id, client, bytes |
| Tracing | with `enable_tracing`, a span per request (parent from `traceparent`), exported at the end of the request |
| Memory limit | `limit_memory`: resident memory after each request; over the limit the worker stops gracefully and is replaced |

### Metrics Store

`MetricsStore` (`prodserver/metricsstore.py`) adds up the metrics of the
worker processes through the worker temp directory: each worker writes
`worker-<pid>.json` (a writer thread once per second while counts change, plus
before a scrape and at exit); the master folds the file of an ended worker into
`retired.json` (which lists the pids it holds, so nothing is counted twice) so
counters never go down when workers are recycled. `MetricsCollector` keeps
bounded memory: a latency histogram plus a window of recent values, and at
most 1000 endpoint keys (more are counted under `__other__`).

### Health Checker

```python
class HealthChecker:
    """
    Provides health check endpoints for load balancers and orchestrators.
    """
    
    def __init__(self, server: "ProductionServer", config: ServerConfig):
        self.server = server
        self.config = config
        self._custom_checks: List[Callable[[], bool]] = []
    
    def check_liveness(self) -> bool:
        """
        Check if the server process is alive.
        
        Returns:
            True if the process is running.
        """
        return True
    
    def check_readiness(self) -> bool:
        """
        Check if the server is ready to handle requests.
        
        Returns:
            True if the server is ready.
        """
        pass
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get detailed server status.
        
        Returns:
            Dict with status information including:
            - status: "healthy" or "unhealthy"
            - workers: worker count and status
            - uptime: server uptime in seconds
            - version: application version
        """
        pass
    
    def handle_health_request(self, request: "Request") -> "Response":
        """
        Handle a health check request.
        
        Returns HTTP 200 if healthy, 503 if unhealthy or shutting down.
        """
        pass
    
    def register_check(self, check: Callable[[], bool]) -> None:
        """Register a custom health check."""
        self._custom_checks.append(check)
```

### Metrics Collector

```python
class MetricsCollector:
    """
    Collects and exposes server metrics.
    """
    
    def __init__(self, config: ServerConfig):
        self.config = config
        self._request_count: Dict[str, int] = {}  # endpoint -> count
        self._request_latency: Dict[str, List[float]] = {}  # endpoint -> latencies
        self._error_count: Dict[int, int] = {}  # status_code -> count
        self._active_connections: int = 0
        self._worker_status: Dict[int, WorkerState] = {}
    
    def record_request(
        self,
        endpoint: str,
        method: str,
        status_code: int,
        latency_ms: float
    ) -> None:
        """
        Record metrics for a completed request.
        
        Args:
            endpoint: The request endpoint path.
            method: HTTP method.
            status_code: Response status code.
            latency_ms: Request latency in milliseconds.
        """
        pass
    
    def increment_connections(self) -> None:
        """Increment active connection count."""
        self._active_connections += 1
    
    def decrement_connections(self) -> None:
        """Decrement active connection count."""
        self._active_connections -= 1
    
    def update_worker_status(self, worker_id: int, state: WorkerState) -> None:
        """Update the status of a worker."""
        self._worker_status[worker_id] = state
    
    def get_prometheus_metrics(self) -> str:
        """
        Export metrics in Prometheus exposition format.
        
        Returns:
            Prometheus-formatted metrics string.
        """
        pass
    
    def send_to_statsd(self) -> None:
        """Send metrics to StatsD server."""
        pass
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """
        Get a summary of all metrics.
        
        Returns:
            Dict with aggregated metrics.
        """
        pass
```

### Structured Logger

```python
class StructuredLogger:
    """
    Provides structured logging with JSON output support.
    """
    
    def __init__(self, config: ServerConfig):
        self.config = config
        self._context: Dict[str, Any] = {}
    
    def log(
        self,
        level: str,
        message: str,
        **context: Any
    ) -> None:
        """
        Log a message with context.
        
        Args:
            level: Log level (DEBUG, INFO, WARNING, ERROR).
            message: Log message.
            **context: Additional context fields.
        """
        pass
    
    def access_log(
        self,
        request: "Request",
        response: "Response",
        latency_ms: float
    ) -> None:
        """
        Log an access log entry.
        
        Args:
            request: The incoming request.
            response: The outgoing response.
            latency_ms: Request latency in milliseconds.
        """
        pass
    
    def error_log(
        self,
        exception: Exception,
        request: Optional["Request"] = None
    ) -> None:
        """
        Log an error with exception details.
        
        Args:
            exception: The exception that occurred.
            request: Optional request context.
        """
        pass
    
    def _format_json(self, entry: Dict[str, Any]) -> str:
        """Format a log entry as JSON."""
        pass
    
    def _format_standard(self, entry: Dict[str, Any]) -> str:
        """Format a log entry in standard format."""
        pass
    
    def set_context(self, **context: Any) -> None:
        """Set persistent context fields."""
        self._context.update(context)
    
    def clear_context(self) -> None:
        """Clear persistent context fields."""
        self._context.clear()
```

### Request Tracer

```python
class RequestTracer:
    """
    Provides request tracing with unique IDs and span creation.
    """
    
    def __init__(self, config: ServerConfig):
        self.config = config
        self._trace_header = config.trace_header
    
    def get_or_create_request_id(self, request: "Request") -> str:
        """
        Get request ID from header or generate a new one.
        
        Args:
            request: The incoming request.
        
        Returns:
            The request ID (existing or newly generated).
        """
        pass
    
    def create_span(
        self,
        name: str,
        request_id: str,
        parent_span_id: Optional[str] = None
    ) -> "Span":
        """
        Create a tracing span.
        
        Args:
            name: Span name.
            request_id: Associated request ID.
            parent_span_id: Optional parent span ID.
        
        Returns:
            A new Span instance.
        """
        pass
    
    def inject_trace_context(
        self,
        response: "Response",
        request_id: str
    ) -> "Response":
        """
        Inject trace context into response headers.
        
        Args:
            response: The outgoing response.
            request_id: The request ID to include.
        
        Returns:
            Response with trace headers added.
        """
        pass
    
    def export_traces(self) -> None:
        """Export collected traces to configured backend."""
        pass


@dataclass
class Span:
    """A tracing span representing a unit of work."""
    span_id: str
    name: str
    request_id: str
    parent_span_id: Optional[str]
    start_time: float
    end_time: Optional[float] = None
    attributes: Dict[str, Any] = field(default_factory=dict)
    
    def end(self) -> None:
        """Mark the span as complete."""
        self.end_time = time.time()
    
    def set_attribute(self, key: str, value: Any) -> None:
        """Set a span attribute."""
        self.attributes[key] = value
```

### Connections and Limits

Connections are managed by the WSGI layer (`wsgi.ConnectionManager`, the
Worker's accept loop): `max_connections` per worker (503 beyond it),
keep-alive timeout, closing idle keep-alive connections and draining at
shutdown. `limit_request_line`, `limit_request_fields`, the header section
(fields × field size) and `limit_request_body` are enforced by the WSGI
HTTPParser before the application is called (414, 431, 413);
`ServerConfig.to_wsgi_config()` maps them.

### SSL/TLS Manager

```python
class SSLManager:
    """
    Manages SSL/TLS configuration and context.
    """
    
    def __init__(self, config: ServerConfig):
        self.config = config
        self._ssl_context: Optional["ssl.SSLContext"] = None
    
    def create_ssl_context(self) -> "ssl.SSLContext":
        """
        Create and configure SSL context.
        
        Returns:
            Configured SSLContext.
        
        Raises:
            SSLConfigError: If SSL configuration is invalid.
        """
        pass
    
    def wrap_socket(self, sock: "socket.socket") -> "ssl.SSLSocket":
        """
        Wrap a socket with SSL.
        
        Args:
            sock: The socket to wrap.
        
        Returns:
            SSL-wrapped socket.
        """
        pass
    
    def validate_config(self) -> None:
        """
        Validate SSL configuration.
        
        Raises:
            SSLConfigError: If configuration is invalid.
        """
        pass
    
    def should_redirect_http(self, request: "Request") -> bool:
        """
        Check if HTTP request should be redirected to HTTPS.
        
        Args:
            request: The incoming request.
        
        Returns:
            True if redirect is needed.
        """
        pass
```

## Data Models

### Exit Codes

```python
# Server exit codes
EXIT_SUCCESS = 0
EXIT_ERROR = 1
EXIT_CONFIG_ERROR = 2
EXIT_BIND_ERROR = 3
EXIT_APP_LOAD_ERROR = 4
EXIT_PID_FILE_ERROR = 5
```

### Default Configuration

```python
# Default server configuration
DEFAULT_CONFIG = {
    "host": "0.0.0.0",
    "port": 8000,
    "workers": 0,  # Auto-detect
    "threads": 1,
    "worker_class": "sync",
    "timeout": 30,
    "graceful_timeout": 30,
    "keep_alive": 5,
    "backlog": 2048,
    "limit_request_line": 4094,
    "limit_request_fields": 100,
    "limit_request_field_size": 8190,
    "log_level": "INFO",
    "log_format": "standard",
    "health_check_path": "/health",
    "metrics_path": "/metrics",
    "trace_header": "X-Request-ID",
}
```

### Worker Classes

```python
VALID_WORKER_CLASSES = {"sync", "gevent"}   # "gevent" needs the gevent extra
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Worker Configuration Consistency

*For any* valid worker count N specified via `--workers`, the WorkerManager SHALL spawn exactly N worker processes before accepting requests, and maintain N workers during normal operation. (Tested on a real server: the metrics endpoint reports the status of each worker.)

**Validates: Requirements 1.1, 1.4, 1.8**

### Property 2: Worker Restart on Crash

*For any* worker process that crashes, the WorkerManager SHALL spawn a replacement worker within 5 seconds, maintaining the configured worker count. A worker that fails to boot is not replaced; the server stops with EXIT_APP_LOAD_ERROR.

**Validates: Requirements 1.3**

### Property 3: Graceful Shutdown Behavior

*For any* graceful shutdown initiated by SIGTERM or SIGINT, the server SHALL stop accepting new connections while allowing all in-flight requests to complete within the graceful timeout period.

**Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 2.6**

### Property 4: Health Check Consistency

*For any* server state, the health check endpoint SHALL return HTTP 200 when the server is healthy and running, and HTTP 503 when the server is unhealthy or shutting down, with response body containing valid JSON status information.

**Validates: Requirements 5.2, 5.3, 5.4, 5.7, 5.8**

### Property 5: Metrics Collection Completeness

*For any* completed request, the MetricsCollector SHALL record the request count, latency, and status code, and these metrics SHALL be accurately reflected in the Prometheus exposition format output.

**Validates: Requirements 6.1, 6.2, 6.3, 6.6**

### Property 6: Structured Log Format Consistency

*For any* log entry with JSON format enabled, the output SHALL be valid JSON containing timestamp, level, message, and context fields, with request_id present for all request-related logs.

**Validates: Requirements 7.1, 7.2, 7.3, 7.4**

### Property 7: Request ID Propagation

*For any* incoming request, the server SHALL either use the provided X-Request-ID header value or generate a unique request ID, include this ID in all log entries for that request, and return it in the response X-Request-ID header.

**Validates: Requirements 8.1, 8.2, 8.3, 8.4**

### Property 8: Resource Limit Enforcement

*For any* request body exceeding the configured limit, the server SHALL return HTTP 413 without processing the request body, and for any worker exceeding memory limits, the WorkerManager SHALL restart that worker.

**Validates: Requirements 11.2, 11.3, 11.4**

### Property 9: TLS Security Enforcement

*For any* connection attempt using deprecated TLS versions (SSLv2, SSLv3, TLS 1.0, TLS 1.1), the server SHALL reject the connection when SSL is configured with minimum version TLS 1.2 or higher.

**Validates: Requirements 10.5, 10.6**

## Error Handling

### Server Startup Errors

- Configuration file not found: Use defaults and log warning
- Invalid configuration (including the gevent worker class without gevent, a TLS certificate that cannot be loaded, a platform without fork): raise `ConfigurationError` (a `ccai.errors` ConfigurationError, BaseException), which ends the run; it is never caught
- Port already in use: Exit with `EXIT_BIND_ERROR` and suggestion
- Application load failure: Exit with `EXIT_APP_LOAD_ERROR` and stack trace
- PID file conflict: Exit with `EXIT_PID_FILE_ERROR` and existing PID info
- A worker that cannot load or start the application: the server stops with `EXIT_APP_LOAD_ERROR`

### Worker Errors

- Worker crash: Log error, restart worker within 5 seconds
- Request timeout: the ASGI bridge cancels the handler and answers 504 (a hung thread in a plain WSGI application is not killed)
- Memory limit exceeded: Log warning, restart worker
- Max requests reached: Gracefully restart worker

### Request Errors

- Request body too large: Return HTTP 413 immediately
- Request line too long: Return HTTP 414
- Too many headers: Return HTTP 431
- Malformed request: Return HTTP 400

### Shutdown Errors

- Graceful timeout exceeded: Force terminate remaining workers
- PID file cleanup failure: Log warning, continue shutdown

## Testing Strategy

### Unit Tests

Unit tests should cover:
- ServerConfig validation and defaults
- Worker spawning and termination
- Signal handler registration
- Health check response generation
- Metrics collection and aggregation
- Structured log formatting
- Request ID generation and propagation
- SSL context creation
- Connection limit enforcement

### Property-Based Tests

Property tests should verify:
- Worker count consistency across configurations
- Worker restart timing after crashes
- Graceful shutdown behavior with in-flight requests
- Health check response consistency
- Metrics accuracy across request patterns
- Structured log format validity
- Request ID uniqueness and propagation
- Resource limit enforcement
- TLS version rejection

### Integration Tests

The integration tests (`test_productionserver.py`, `devexp/cli/test_prodserve.py`)
start real servers in child processes on ports 18100-18199 and use
`http.client`; the shared helpers are in `ccai.testshared.servers`.

Integration tests should cover:
- Full server startup and shutdown cycle
- Worker process management under load
- Signal handling (SIGTERM, SIGINT, SIGHUP)
- Health check endpoint behavior
- Metrics endpoint exposition
- SSL/TLS handshake and communication
- Connection draining during shutdown

### Test Configuration

- Use testbase framework per repository conventions
- Test files located at `source/testroots/ccai/tests/singlehost/webworks/prodserver/`
- Property tests should run minimum 100 iterations
- Each property test must reference its design document property
