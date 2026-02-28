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

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Production Server                                  │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                      ProductionServer                                │    │
│  │  - config: ServerConfig                                             │    │
│  │  - worker_manager: WorkerManager                                    │    │
│  │  - signal_handler: SignalHandler                                    │    │
│  │  - metrics_collector: MetricsCollector                              │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                              │                                               │
│          ┌───────────────────┼───────────────────┐                          │
│          ▼                   ▼                   ▼                          │
│  ┌───────────────┐   ┌───────────────┐   ┌───────────────┐                 │
│  │ WorkerManager │   │ SignalHandler │   │HealthChecker  │                 │
│  │ - workers     │   │ - handlers    │   │ - liveness    │                 │
│  │ - spawn()     │   │ - register()  │   │ - readiness   │                 │
│  │ - terminate() │   │ - handle()    │   │ - status()    │                 │
│  └───────────────┘   └───────────────┘   └───────────────┘                 │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                         Worker Management Layer                              │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                       WorkerManager                                  │    │
│  │  - num_workers: int                                                 │    │
│  │  - max_requests: Optional[int]                                      │    │
│  │  - max_requests_jitter: int                                         │    │
│  │  - timeout: Optional[int]                                           │    │
│  │  - worker_class: Type[Worker]                                       │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                              │                                               │
│          ┌───────────────────┼───────────────────┐                          │
│          ▼                   ▼                   ▼                          │
│  ┌───────────────┐   ┌───────────────┐   ┌───────────────┐                 │
│  │ SyncWorker    │   │ AsyncWorker   │   │ GeventWorker  │                 │
│  │ - WSGI        │   │ - ASGI        │   │ - greenlets   │                 │
│  │ - threads     │   │ - async/await │   │ - cooperative │                 │
│  └───────────────┘   └───────────────┘   └───────────────┘                 │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                         Observability Layer                                  │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                      MetricsCollector                                │    │
│  │  - request_count: Counter                                           │    │
│  │  - request_latency: Histogram                                       │    │
│  │  - error_rate: Counter                                              │    │
│  │  - active_connections: Gauge                                        │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                              │                                               │
│          ┌───────────────────┼───────────────────┐                          │
│          ▼                   ▼                   ▼                          │
│  ┌───────────────┐   ┌───────────────┐   ┌───────────────┐                 │
│  │StructuredLogger│  │ RequestTracer │   │ PrometheusExp │                 │
│  │ - json format │   │ - request_id  │   │ - /metrics    │                 │
│  │ - context     │   │ - spans       │   │ - exposition  │                 │
│  └───────────────┘   └───────────────┘   └───────────────┘                 │
└─────────────────────────────────────────────────────────────────────────────┘
```

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
    limit_request_body: int = 0  # 0 = unlimited
    limit_memory: Optional[int] = None
    
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
class ProductionServer:
    """
    Main production server class that orchestrates all components.
    """
    
    def __init__(self, app: "WebApplication", config: ServerConfig):
        self.app = app
        self.config = config
        self.worker_manager: Optional["WorkerManager"] = None
        self.signal_handler: Optional["SignalHandler"] = None
        self.health_checker: Optional["HealthChecker"] = None
        self.metrics_collector: Optional["MetricsCollector"] = None
        self.structured_logger: Optional["StructuredLogger"] = None
        self.request_tracer: Optional["RequestTracer"] = None
        self._state: ServerState = ServerState.STOPPED
    
    def start(self) -> None:
        """
        Start the production server.
        
        1. Initialize components
        2. Set up signal handlers
        3. Spawn workers
        4. Begin accepting connections
        """
        pass
    
    def stop(self, graceful: bool = True) -> None:
        """
        Stop the production server.
        
        Args:
            graceful: If True, allow in-flight requests to complete.
        """
        pass
    
    def reload(self) -> None:
        """
        Reload configuration without dropping connections.
        """
        pass
    
    def _initialize_components(self) -> None:
        """Initialize all server components."""
        pass
    
    def _setup_signal_handlers(self) -> None:
        """Register signal handlers for SIGTERM, SIGINT, SIGHUP."""
        pass
    
    def _write_pid_file(self) -> None:
        """Write the master process PID to file."""
        pass
    
    def _cleanup_pid_file(self) -> None:
        """Remove the PID file on shutdown."""
        pass


class ServerState(Enum):
    """Server lifecycle states."""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    SHUTTING_DOWN = "shutting_down"
    RELOADING = "reloading"
```

### Worker Manager

```python
class WorkerManager:
    """
    Manages worker processes including spawning, monitoring, and termination.
    """
    
    def __init__(self, config: ServerConfig, app: "WebApplication"):
        self.config = config
        self.app = app
        self._workers: Dict[int, "Worker"] = {}
        self._worker_pids: Dict[int, int] = {}  # worker_id -> pid
        self._request_counts: Dict[int, int] = {}  # worker_id -> count
        self._min_workers: int = 1
    
    def spawn_workers(self) -> None:
        """
        Spawn all worker processes (prefork model).
        
        Spawns config.workers processes before accepting any requests.
        """
        pass
    
    def spawn_worker(self, worker_id: int) -> "Worker":
        """
        Spawn a single worker process.
        
        Args:
            worker_id: Unique identifier for the worker.
        
        Returns:
            The spawned Worker instance.
        """
        pass
    
    def terminate_worker(self, worker_id: int, graceful: bool = True) -> None:
        """
        Terminate a worker process.
        
        Args:
            worker_id: ID of the worker to terminate.
            graceful: If True, allow in-flight requests to complete.
        """
        pass
    
    def restart_worker(self, worker_id: int) -> None:
        """
        Restart a worker process.
        
        Terminates the existing worker and spawns a new one.
        """
        pass
    
    def monitor_workers(self) -> None:
        """
        Monitor worker health and restart crashed workers.
        
        Runs in a loop, checking worker status and restarting
        any that have crashed within 5 seconds.
        """
        pass
    
    def increment_request_count(self, worker_id: int) -> None:
        """
        Increment the request count for a worker.
        
        If max_requests is configured and exceeded, schedules
        the worker for restart.
        """
        pass
    
    def get_worker_count(self) -> int:
        """Return the number of active workers."""
        return len(self._workers)
    
    def get_worker_status(self) -> Dict[int, "WorkerStatus"]:
        """Return status information for all workers."""
        pass
    
    def _calculate_max_requests(self, worker_id: int) -> int:
        """
        Calculate max requests for a worker with jitter.
        
        Returns:
            max_requests + random(-jitter, +jitter)
        """
        pass
    
    def _get_default_worker_count(self) -> int:
        """
        Get default worker count based on CPU cores.
        
        Returns:
            Number of CPU cores * 2 + 1
        """
        pass
```

### Worker Classes

```python
class Worker(ABC):
    """
    Abstract base class for worker implementations.
    """
    
    def __init__(
        self,
        worker_id: int,
        app: "WebApplication",
        config: ServerConfig
    ):
        self.worker_id = worker_id
        self.app = app
        self.config = config
        self._request_count = 0
        self._state: WorkerState = WorkerState.IDLE
    
    @abstractmethod
    def run(self) -> None:
        """Main worker loop."""
        pass
    
    @abstractmethod
    def handle_request(self, request: "Request") -> "Response":
        """Handle a single request."""
        pass
    
    def shutdown(self, graceful: bool = True) -> None:
        """Shutdown the worker."""
        pass
    
    @property
    def state(self) -> "WorkerState":
        """Return current worker state."""
        return self._state


class SyncWorker(Worker):
    """
    Synchronous worker for WSGI applications.
    
    Uses threading for concurrent request handling within the worker.
    """
    
    def __init__(
        self,
        worker_id: int,
        app: "WebApplication",
        config: ServerConfig
    ):
        super().__init__(worker_id, app, config)
        self._thread_pool: Optional["ThreadPoolExecutor"] = None
    
    def run(self) -> None:
        """
        Main worker loop.
        
        Accepts connections and dispatches to thread pool.
        """
        pass
    
    def handle_request(self, request: "Request") -> "Response":
        """Handle request synchronously."""
        pass


class AsyncWorker(Worker):
    """
    Asynchronous worker for ASGI applications.
    
    Uses asyncio for concurrent request handling.
    """
    
    def __init__(
        self,
        worker_id: int,
        app: "WebApplication",
        config: ServerConfig
    ):
        super().__init__(worker_id, app, config)
        self._loop: Optional["asyncio.AbstractEventLoop"] = None
    
    def run(self) -> None:
        """
        Main worker loop.
        
        Runs the asyncio event loop.
        """
        pass
    
    async def handle_request(self, request: "Request") -> "Response":
        """Handle request asynchronously."""
        pass


class GeventWorker(Worker):
    """
    Gevent-based worker using greenlets.
    
    Requires gevent to be installed.
    """
    
    def __init__(
        self,
        worker_id: int,
        app: "WebApplication",
        config: ServerConfig
    ):
        super().__init__(worker_id, app, config)
        self._pool: Optional["gevent.pool.Pool"] = None
    
    def run(self) -> None:
        """
        Main worker loop.
        
        Uses gevent pool for cooperative multitasking.
        """
        pass
    
    def handle_request(self, request: "Request") -> "Response":
        """Handle request in a greenlet."""
        pass


class WorkerState(Enum):
    """Worker lifecycle states."""
    IDLE = "idle"
    ACTIVE = "active"
    SHUTTING_DOWN = "shutting_down"
    STOPPED = "stopped"


@dataclass
class WorkerStatus:
    """Status information for a worker."""
    worker_id: int
    pid: int
    state: WorkerState
    request_count: int
    memory_usage: int
    uptime: float
```

### Signal Handler

```python
class SignalHandler:
    """
    Handles OS signals for server control.
    """
    
    def __init__(self, server: "ProductionServer"):
        self.server = server
        self._handlers: Dict[int, Callable] = {}
    
    def register(self) -> None:
        """
        Register signal handlers.
        
        - SIGTERM: Graceful shutdown
        - SIGINT: Graceful shutdown
        - SIGHUP: Reload configuration
        """
        pass
    
    def handle_sigterm(self, signum: int, frame: Any) -> None:
        """Handle SIGTERM signal."""
        self.server.stop(graceful=True)
    
    def handle_sigint(self, signum: int, frame: Any) -> None:
        """Handle SIGINT signal."""
        self.server.stop(graceful=True)
    
    def handle_sighup(self, signum: int, frame: Any) -> None:
        """Handle SIGHUP signal."""
        self.server.reload()
```

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

### Connection Manager

```python
class ConnectionManager:
    """
    Manages connection lifecycle and limits.
    """
    
    def __init__(self, config: ServerConfig):
        self.config = config
        self._connections: Dict[str, "Connection"] = {}
        self._connection_count: int = 0
    
    def accept_connection(self, conn: "Connection") -> bool:
        """
        Accept a new connection if within limits.
        
        Args:
            conn: The incoming connection.
        
        Returns:
            True if accepted, False if rejected due to limits.
        """
        pass
    
    def close_connection(self, conn_id: str) -> None:
        """Close and remove a connection."""
        pass
    
    def drain_connections(self, timeout: float) -> None:
        """
        Drain all connections during graceful shutdown.
        
        Args:
            timeout: Maximum time to wait for connections to close.
        """
        pass
    
    def close_idle_connections(self) -> int:
        """
        Close idle keep-alive connections.
        
        Returns:
            Number of connections closed.
        """
        pass
    
    def get_connection_count(self) -> int:
        """Return current connection count."""
        return self._connection_count


@dataclass
class Connection:
    """Represents a client connection."""
    conn_id: str
    socket: Any
    created_at: float
    last_activity: float
    keep_alive: bool = True
    requests_handled: int = 0
```

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

### Worker Class Registry

```python
# Available worker classes
WORKER_CLASSES = {
    "sync": SyncWorker,
    "async": AsyncWorker,
    "gevent": GeventWorker,
}
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Worker Configuration Consistency

*For any* valid worker count N specified via `--workers`, the WorkerManager SHALL spawn exactly N worker processes before accepting requests, and maintain N workers during normal operation.

**Validates: Requirements 1.1, 1.4, 1.8**

### Property 2: Worker Restart on Crash

*For any* worker process that crashes, the WorkerManager SHALL spawn a replacement worker within 5 seconds, maintaining the configured worker count.

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
- Invalid configuration: Exit with `EXIT_CONFIG_ERROR` and descriptive message
- Port already in use: Exit with `EXIT_BIND_ERROR` and suggestion
- Application load failure: Exit with `EXIT_APP_LOAD_ERROR` and stack trace
- PID file conflict: Exit with `EXIT_PID_FILE_ERROR` and existing PID info
- SSL certificate error: Exit with `EXIT_CONFIG_ERROR` and certificate details

### Worker Errors

- Worker crash: Log error, restart worker within 5 seconds
- Worker timeout: Terminate worker, log timeout details, restart
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
- Test files located at `source/testroots/automojo/tests/singlehost/webworks/prodserver/`
- Property tests should run minimum 100 iterations
- Each property test must reference its design document property
