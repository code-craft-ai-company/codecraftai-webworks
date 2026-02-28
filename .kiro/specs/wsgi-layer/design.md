# Design Document: WSGI Layer

## Overview

This design document describes the architecture and implementation approach for the WSGI Layer feature. The feature provides a complete Web Server Gateway Interface (WSGI) implementation including both the application interface and a built-in WSGI server. This enables the web framework to handle synchronous request/response processing with minimal external dependencies.

Key design principles:
- PEP 3333 Compliance: Full adherence to the WSGI specification
- Self-Contained: Built-in server eliminates need for external packages like Gunicorn
- Server Agnostic: Application interface remains compatible with external WSGI servers
- Middleware Compatible: Supports standard WSGI middleware wrapping
- Clean Abstraction: Bridges WSGI environ to framework Request/Response objects
- Resource Safety: Proper cleanup via response iterator close() method
- Production Ready: Worker process management, keep-alive, and graceful shutdown

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           WSGI Layer Architecture                            │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                      Built-in WSGI Server                            │    │
│  │  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐            │    │
│  │  │ SocketListener│  │ WorkerManager │  │ ServerConfig  │            │    │
│  │  │ - bind()      │  │ - spawn()     │  │ - host/port   │            │    │
│  │  │ - accept()    │  │ - monitor()   │  │ - workers     │            │    │
│  │  │ - close()     │  │ - shutdown()  │  │ - timeouts    │            │    │
│  │  └───────────────┘  └───────────────┘  └───────────────┘            │    │
│  │         │                   │                                        │    │
│  │         ▼                   ▼                                        │    │
│  │  ┌─────────────────────────────────────────────────────────────┐    │    │
│  │  │                    Worker Process                            │    │    │
│  │  │  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐    │    │    │
│  │  │  │ HTTPParser    │  │ HTTPWriter    │  │ ConnectionMgr │    │    │    │
│  │  │  │ - parse_req() │  │ - write_resp()│  │ - keep_alive  │    │    │    │
│  │  │  │ - to_environ()│  │ - chunked()   │  │ - timeout     │    │    │    │
│  │  │  └───────────────┘  └───────────────┘  └───────────────┘    │    │    │
│  │  └─────────────────────────────────────────────────────────────┘    │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│         │                                                                    │
│         ▼                                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    WSGIApplication                                   │    │
│  │  __call__(environ, start_response) -> ResponseIterator              │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│         │                                                                    │
│         ├──────────────────────┬──────────────────────┐                     │
│         ▼                      ▼                      ▼                     │
│  ┌───────────────┐      ┌───────────────┐      ┌───────────────┐           │
│  │EnvironParser │      │ ResponseBuilder│      │ ErrorHandler  │           │
│  │ - parse()    │      │ - build()      │      │ - handle()    │           │
│  │ - to_request │      │ - to_wsgi()    │      │ - format()    │           │
│  └───────────────┘      └───────────────┘      └───────────────┘           │
│         │                      │                      │                     │
│         ▼                      ▼                      ▼                     │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                         Framework Core                               │    │
│  │  Request → Router → Middleware Pipeline → Handler → Response        │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                         Built-in Server Flow                                 │
│                                                                              │
│  1. SocketListener binds to host:port                                       │
│  2. WorkerManager spawns worker processes                                   │
│  3. Each worker accepts connections from shared socket                      │
│  4. HTTPParser reads and parses HTTP request                                │
│  5. HTTPParser constructs WSGI environ dictionary                           │
│  6. Worker calls app(environ, start_response)                               │
│  7. HTTPWriter sends response status and headers                            │
│  8. HTTPWriter streams response body from iterator                          │
│  9. ConnectionManager handles keep-alive or close                           │
│                                                                              │
│  Socket ──▶ Accept ──▶ Parse HTTP ──▶ Build Environ ──▶ Call App           │
│                                                              │               │
│                                                              ▼               │
│  Close/Keep-Alive ◀── Write Response ◀── start_response ◀───┘              │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                         WSGI Request Flow                                    │
│                                                                              │
│  1. Server calls app(environ, start_response)                               │
│  2. EnvironParser extracts request data from environ                        │
│  3. Request object created from parsed environ                              │
│  4. Request dispatched through middleware pipeline                          │
│  5. Handler generates Response object                                       │
│  6. ResponseBuilder converts Response to WSGI format                        │
│  7. start_response(status, headers) called                                  │
│  8. ResponseIterator yields body chunks                                     │
│  9. close() called for cleanup                                              │
│                                                                              │
│  environ ──▶ EnvironParser ──▶ Request ──▶ Handler ──▶ Response            │
│                                                              │               │
│                                                              ▼               │
│  start_response(status, headers) ◀── ResponseBuilder ◀──────┘              │
│         │                                                                    │
│         ▼                                                                    │
│  ResponseIterator ──▶ yield body chunks ──▶ close()                        │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                         Worker Process Model                                 │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                       Master Process                                 │    │
│  │  - Binds socket                                                      │    │
│  │  - Spawns workers                                                    │    │
│  │  - Monitors health                                                   │    │
│  │  - Handles signals                                                   │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│         │                                                                    │
│         ├──────────────────┬──────────────────┬──────────────────┐          │
│         ▼                  ▼                  ▼                  ▼          │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐  │
│  │  Worker 1   │    │  Worker 2   │    │  Worker 3   │    │  Worker N   │  │
│  │  ┌───────┐  │    │  ┌───────┐  │    │  ┌───────┐  │    │  ┌───────┐  │  │
│  │  │Thread1│  │    │  │Thread1│  │    │  │Thread1│  │    │  │Thread1│  │  │
│  │  │Thread2│  │    │  │Thread2│  │    │  │Thread2│  │    │  │Thread2│  │  │
│  │  │  ...  │  │    │  │  ...  │  │    │  │  ...  │  │    │  │  ...  │  │  │
│  │  └───────┘  │    │  └───────┘  │    │  └───────┘  │    │  └───────┘  │  │
│  └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘  │
│                                                                              │
│  Each worker: accepts connections, parses HTTP, calls WSGI app              │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                         Middleware Wrapping                                  │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    Outer Middleware                                  │    │
│  │  def __call__(environ, start_response):                             │    │
│  │      # Modify environ                                               │    │
│  │      response = inner_app(environ, start_response)                  │    │
│  │      # Modify response                                              │    │
│  │      return response                                                │    │
│  │  ┌─────────────────────────────────────────────────────────────┐    │    │
│  │  │                  Inner Middleware                            │    │    │
│  │  │  ┌─────────────────────────────────────────────────────┐    │    │    │
│  │  │  │              WSGIApplication                         │    │    │    │
│  │  │  └─────────────────────────────────────────────────────┘    │    │    │
│  │  └─────────────────────────────────────────────────────────────┘    │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  Execution order: Outer.before → Inner.before → App → Inner.after → Outer.after
└─────────────────────────────────────────────────────────────────────────────┘
```

## Components and Interfaces

### WSGIApplication Class

```python
class WSGIApplication:
    """
    WSGI application callable that bridges WSGI servers to the framework.
    
    Implements PEP 3333 WSGI specification.
    """
    
    def __init__(
        self,
        dispatcher: "Dispatcher",
        debug: bool = False,
        max_request_body_size: int = 0,  # 0 = unlimited
        error_handler: Optional["ErrorHandler"] = None
    ):
        """
        Construct a WSGI application.
        
        Args:
            dispatcher: The framework dispatcher for request handling.
            debug: If True, include stack traces in error responses.
            max_request_body_size: Maximum request body size in bytes.
            error_handler: Custom error handler for exceptions.
        """
        pass
    
    def __call__(
        self,
        environ: Dict[str, Any],
        start_response: Callable[[str, List[Tuple[str, str]]], Callable]
    ) -> Iterable[bytes]:
        """
        WSGI application entry point.
        
        Args:
            environ: WSGI environ dictionary.
            start_response: WSGI start_response callable.
        
        Returns:
            Response iterator yielding bytes.
        """
        pass
    
    def _handle_request(
        self,
        environ: Dict[str, Any],
        start_response: Callable
    ) -> Iterable[bytes]:
        """
        Handle a single request.
        
        Args:
            environ: WSGI environ dictionary.
            start_response: WSGI start_response callable.
        
        Returns:
            Response iterator.
        """
        pass
    
    def _handle_error(
        self,
        exc: Exception,
        environ: Dict[str, Any],
        start_response: Callable,
        exc_info: Optional[Tuple] = None
    ) -> Iterable[bytes]:
        """
        Handle an exception during request processing.
        
        Args:
            exc: The exception that occurred.
            environ: WSGI environ dictionary.
            start_response: WSGI start_response callable.
            exc_info: Exception info tuple from sys.exc_info().
        
        Returns:
            Error response iterator.
        """
        pass
```

### EnvironParser Class

```python
class EnvironParser:
    """
    Parses WSGI environ dictionary into framework Request objects.
    """
    
    def __init__(self, max_body_size: int = 0):
        """
        Construct an environ parser.
        
        Args:
            max_body_size: Maximum request body size (0 = unlimited).
        """
        pass
    
    def parse(self, environ: Dict[str, Any]) -> "Request":
        """
        Parse WSGI environ into a Request object.
        
        Args:
            environ: WSGI environ dictionary.
        
        Returns:
            Parsed Request object.
        
        Raises:
            RequestEntityTooLarge: If body exceeds max_body_size.
        """
        pass
    
    def get_method(self, environ: Dict[str, Any]) -> str:
        """Extract HTTP method from environ."""
        return environ.get("REQUEST_METHOD", "GET")
    
    def get_path(self, environ: Dict[str, Any]) -> str:
        """Extract request path from environ."""
        return environ.get("PATH_INFO", "/")
    
    def get_query_string(self, environ: Dict[str, Any]) -> str:
        """Extract query string from environ."""
        return environ.get("QUERY_STRING", "")
    
    def get_headers(self, environ: Dict[str, Any]) -> Dict[str, str]:
        """
        Extract HTTP headers from environ.
        
        Converts HTTP_* keys to header names.
        Also includes CONTENT_TYPE and CONTENT_LENGTH.
        """
        pass
    
    def get_body(self, environ: Dict[str, Any]) -> bytes:
        """
        Read request body from wsgi.input.
        
        Respects CONTENT_LENGTH if present.
        
        Raises:
            RequestEntityTooLarge: If body exceeds max_body_size.
        """
        pass
    
    def get_scheme(self, environ: Dict[str, Any]) -> str:
        """Extract URL scheme from environ."""
        return environ.get("wsgi.url_scheme", "http")
    
    def get_host(self, environ: Dict[str, Any]) -> str:
        """Extract server host from environ."""
        return environ.get("SERVER_NAME", "localhost")
    
    def get_port(self, environ: Dict[str, Any]) -> int:
        """Extract server port from environ."""
        return int(environ.get("SERVER_PORT", "80"))
    
    def set_framework_environ(
        self,
        environ: Dict[str, Any],
        request: "Request",
        route: Optional["RouteMatch"] = None
    ) -> None:
        """
        Set framework-specific environ keys.
        
        Sets:
        - webworks.request: The Request object
        - webworks.route: The matched route (if any)
        - webworks.path_params: Path parameters (if any)
        """
        pass
```

### ResponseBuilder Class

```python
class ResponseBuilder:
    """
    Converts framework Response objects to WSGI format.
    """
    
    # Hop-by-hop headers that should not be included in responses
    HOP_BY_HOP_HEADERS = frozenset([
        "connection", "keep-alive", "proxy-authenticate",
        "proxy-authorization", "te", "trailers",
        "transfer-encoding", "upgrade"
    ])
    
    def build(
        self,
        response: "Response"
    ) -> Tuple[str, List[Tuple[str, str]], Iterable[bytes]]:
        """
        Convert Response to WSGI format.
        
        Args:
            response: Framework Response object.
        
        Returns:
            Tuple of (status, headers, body_iterator).
        """
        pass
    
    def format_status(self, status_code: int, reason: Optional[str] = None) -> str:
        """
        Format status code and reason phrase.
        
        Args:
            status_code: HTTP status code.
            reason: Optional reason phrase (uses default if not provided).
        
        Returns:
            Status string like "200 OK".
        """
        pass
    
    def format_headers(
        self,
        headers: Dict[str, str],
        body_length: Optional[int] = None,
        content_type: Optional[str] = None
    ) -> List[Tuple[str, str]]:
        """
        Format headers as list of tuples, filtering hop-by-hop headers.
        
        Args:
            headers: Response headers dict.
            body_length: Optional body length for Content-Length header.
            content_type: Optional content type if not in headers.
        
        Returns:
            List of (name, value) tuples.
        """
        pass
    
    def is_hop_by_hop(self, header_name: str) -> bool:
        """Check if header is a hop-by-hop header."""
        return header_name.lower() in self.HOP_BY_HOP_HEADERS
```

### ResponseIterator Class

```python
class ResponseIterator:
    """
    WSGI response iterator that yields body chunks and handles cleanup.
    
    Implements the iterator protocol and close() method per PEP 3333.
    """
    
    def __init__(
        self,
        content: Union[bytes, Iterable[bytes], Generator[bytes, None, None], IO[bytes]],
        close_callback: Optional[Callable[[], None]] = None
    ):
        """
        Construct a response iterator.
        
        Args:
            content: Response body content (bytes, iterable, generator, or file).
            close_callback: Optional callback to invoke on close().
        """
        pass
    
    def __iter__(self) -> "ResponseIterator":
        """Return self as iterator."""
        return self
    
    def __next__(self) -> bytes:
        """
        Yield next body chunk.
        
        Returns:
            Next bytes chunk.
        
        Raises:
            StopIteration: When iteration is complete.
        """
        pass
    
    def close(self) -> None:
        """
        Clean up resources.
        
        Closes file handles, releases resources, and invokes close_callback.
        """
        pass
    
    @classmethod
    def from_bytes(cls, data: bytes) -> "ResponseIterator":
        """Create iterator from bytes."""
        return cls([data])
    
    @classmethod
    def from_generator(
        cls,
        gen: Generator[bytes, None, None]
    ) -> "ResponseIterator":
        """Create iterator from generator."""
        return cls(gen)
    
    @classmethod
    def from_file(
        cls,
        file_obj: IO[bytes],
        chunk_size: int = 8192
    ) -> "ResponseIterator":
        """
        Create iterator from file-like object.
        
        Args:
            file_obj: File-like object to read from.
            chunk_size: Size of chunks to yield.
        """
        pass
```

### ErrorHandler Class

```python
class ErrorHandler:
    """
    Handles exceptions during WSGI request processing.
    """
    
    def __init__(
        self,
        debug: bool = False,
        logger: Optional["Logger"] = None
    ):
        """
        Construct an error handler.
        
        Args:
            debug: If True, include stack traces in responses.
            logger: Logger for error logging.
        """
        pass
    
    def handle(
        self,
        exc: Exception,
        environ: Dict[str, Any]
    ) -> "Response":
        """
        Handle an exception and return an error response.
        
        Args:
            exc: The exception that occurred.
            environ: WSGI environ for context.
        
        Returns:
            Error Response object.
        """
        pass
    
    def handle_http_exception(self, exc: "HTTPException") -> "Response":
        """Handle HTTPException subclasses."""
        pass
    
    def handle_unhandled_exception(
        self,
        exc: Exception,
        environ: Dict[str, Any]
    ) -> "Response":
        """Handle unhandled exceptions with 500 response."""
        pass
    
    def format_error_body(
        self,
        status_code: int,
        message: str,
        exc: Optional[Exception] = None
    ) -> bytes:
        """
        Format error response body.
        
        In debug mode, includes stack trace.
        In production mode, includes only status and message.
        """
        pass
    
    def log_exception(
        self,
        exc: Exception,
        environ: Dict[str, Any]
    ) -> None:
        """Log exception with stack trace."""
        pass
    
    def register_handler(
        self,
        exc_type: Type[Exception],
        handler: Callable[[Exception], "Response"]
    ) -> None:
        """
        Register a custom handler for an exception type.
        
        Args:
            exc_type: Exception type to handle.
            handler: Handler function returning Response.
        """
        pass
```

### RequestBodyParser Class

```python
class RequestBodyParser:
    """
    Parses request bodies in various formats.
    """
    
    def __init__(self, max_size: int = 0):
        """
        Construct a body parser.
        
        Args:
            max_size: Maximum body size (0 = unlimited).
        """
        pass
    
    def parse_raw(self, wsgi_input: IO[bytes], content_length: Optional[int]) -> bytes:
        """
        Read raw bytes from wsgi.input.
        
        Args:
            wsgi_input: The wsgi.input file-like object.
            content_length: Content-Length header value.
        
        Returns:
            Raw body bytes.
        
        Raises:
            RequestEntityTooLarge: If body exceeds max_size.
        """
        pass
    
    def parse_form(self, body: bytes, content_type: str) -> Dict[str, str]:
        """
        Parse application/x-www-form-urlencoded body.
        
        Args:
            body: Raw body bytes.
            content_type: Content-Type header value.
        
        Returns:
            Dict of form fields.
        """
        pass
    
    def parse_multipart(
        self,
        wsgi_input: IO[bytes],
        content_type: str,
        content_length: Optional[int]
    ) -> Tuple[Dict[str, str], Dict[str, "UploadedFile"]]:
        """
        Parse multipart/form-data body.
        
        Args:
            wsgi_input: The wsgi.input file-like object.
            content_type: Content-Type header with boundary.
            content_length: Content-Length header value.
        
        Returns:
            Tuple of (form_fields, uploaded_files).
        """
        pass
    
    def parse_json(self, body: bytes) -> Any:
        """
        Parse application/json body.
        
        Args:
            body: Raw body bytes.
        
        Returns:
            Parsed JSON value.
        
        Raises:
            BadRequest: If JSON is invalid.
        """
        pass
```

### WSGIMiddlewareWrapper Class

```python
class WSGIMiddlewareWrapper:
    """
    Helper for wrapping WSGI applications with middleware.
    """
    
    @staticmethod
    def wrap(
        app: Callable,
        middleware: Callable
    ) -> Callable:
        """
        Wrap a WSGI application with middleware.
        
        Args:
            app: The inner WSGI application.
            middleware: The middleware to wrap with.
        
        Returns:
            Wrapped WSGI application.
        """
        return middleware(app)
    
    @staticmethod
    def wrap_multiple(
        app: Callable,
        middlewares: List[Callable]
    ) -> Callable:
        """
        Wrap a WSGI application with multiple middlewares.
        
        Middlewares are applied in order, so the first middleware
        in the list is the outermost wrapper.
        
        Args:
            app: The inner WSGI application.
            middlewares: List of middlewares to apply.
        
        Returns:
            Wrapped WSGI application.
        """
        pass
```

### Application Factory

```python
def get_wsgi_application() -> WSGIApplication:
    """
    Get the WSGI application callable.
    
    This is the main entry point for WSGI servers.
    
    Returns:
        Configured WSGIApplication instance.
    """
    pass


def create_wsgi_application(
    config: Optional[Dict[str, Any]] = None
) -> WSGIApplication:
    """
    Application factory for creating WSGI applications.
    
    Each call creates a new application instance.
    
    Args:
        config: Optional configuration dict.
    
    Returns:
        New WSGIApplication instance.
    """
    pass


# Module-level application variable for WSGI servers
application: Optional[WSGIApplication] = None
```

### WSGIServer Class

```python
class WSGIServer:
    """
    Built-in WSGI server for running applications without external dependencies.
    
    Provides process-based concurrency with optional threading per worker.
    """
    
    def __init__(
        self,
        app: Callable,
        config: Optional["ServerConfig"] = None
    ):
        """
        Construct a WSGI server.
        
        Args:
            app: The WSGI application callable.
            config: Server configuration (uses defaults if not provided).
        """
        pass
    
    def serve_forever(self) -> None:
        """
        Start the server and block until shutdown.
        
        Binds socket, spawns workers, and enters main loop.
        """
        pass
    
    def shutdown(self, graceful: bool = True) -> None:
        """
        Shutdown the server.
        
        Args:
            graceful: If True, wait for active requests to complete.
        """
        pass
    
    def _setup_signals(self) -> None:
        """Setup signal handlers for SIGTERM, SIGINT, SIGHUP."""
        pass
    
    def _spawn_workers(self) -> None:
        """Spawn worker processes."""
        pass
    
    def _monitor_workers(self) -> None:
        """Monitor worker health and restart failed workers."""
        pass
```

### ServerConfig Dataclass

```python
@dataclass
class ServerConfig:
    """
    Configuration for the built-in WSGI server.
    """
    
    # Network binding
    host: str = "127.0.0.1"
    port: int = 8000
    unix_socket: Optional[str] = None
    backlog: int = 2048
    
    # Worker configuration
    workers: int = 1  # Number of worker processes
    threads: int = 1  # Threads per worker
    worker_class: str = "sync"  # sync, thread
    
    # Timeouts
    timeout: int = 30  # Request timeout in seconds
    keepalive: int = 2  # Keep-alive timeout in seconds
    graceful_timeout: int = 30  # Graceful shutdown timeout
    
    # Limits
    max_request_size: int = 0  # 0 = unlimited
    max_header_size: int = 8192  # 8KB default
    max_headers: int = 100
    max_connections: int = 1000  # Per worker
    
    # SSL/TLS
    ssl_certfile: Optional[str] = None
    ssl_keyfile: Optional[str] = None
    ssl_ca_certs: Optional[str] = None
    
    # Development options
    reload: bool = False  # Auto-reload on code changes
    debug: bool = False
    
    # Logging
    access_log: bool = True
    error_log: bool = True
    log_level: str = "info"
    
    @classmethod
    def from_environ(cls) -> "ServerConfig":
        """Create config from environment variables."""
        pass
    
    @classmethod
    def from_file(cls, path: str) -> "ServerConfig":
        """Load config from file."""
        pass
    
    def validate(self) -> None:
        """Validate configuration and raise on errors."""
        pass
```

### SocketListener Class

```python
class SocketListener:
    """
    Manages server socket binding and connection acceptance.
    """
    
    def __init__(self, config: ServerConfig):
        """
        Construct a socket listener.
        
        Args:
            config: Server configuration.
        """
        pass
    
    def bind(self) -> None:
        """
        Bind to configured address.
        
        Supports IPv4, IPv6, and Unix domain sockets.
        """
        pass
    
    def accept(self) -> Tuple[socket.socket, Tuple[str, int]]:
        """
        Accept a new connection.
        
        Returns:
            Tuple of (client_socket, client_address).
        """
        pass
    
    def close(self) -> None:
        """Close the server socket."""
        pass
    
    def fileno(self) -> int:
        """Return socket file descriptor for select/poll."""
        pass
    
    def _create_socket(self) -> socket.socket:
        """Create and configure the server socket."""
        pass
    
    def _setup_ssl(self, sock: socket.socket) -> ssl.SSLSocket:
        """Wrap socket with SSL if configured."""
        pass
```

### WorkerManager Class

```python
class WorkerManager:
    """
    Manages worker process lifecycle.
    """
    
    def __init__(
        self,
        app: Callable,
        listener: SocketListener,
        config: ServerConfig
    ):
        """
        Construct a worker manager.
        
        Args:
            app: The WSGI application.
            listener: The socket listener.
            config: Server configuration.
        """
        pass
    
    def spawn(self, num_workers: int) -> None:
        """
        Spawn worker processes.
        
        Args:
            num_workers: Number of workers to spawn.
        """
        pass
    
    def monitor(self) -> None:
        """
        Monitor worker health.
        
        Restarts failed workers and handles memory limits.
        """
        pass
    
    def shutdown(self, graceful: bool = True) -> None:
        """
        Shutdown all workers.
        
        Args:
            graceful: If True, wait for active requests.
        """
        pass
    
    def signal_workers(self, sig: int) -> None:
        """
        Send signal to all workers.
        
        Args:
            sig: Signal number to send.
        """
        pass
    
    def _spawn_worker(self) -> int:
        """Spawn a single worker and return its PID."""
        pass
    
    def _reap_workers(self) -> None:
        """Reap terminated worker processes."""
        pass
```

### Worker Class

```python
class Worker:
    """
    Worker process that handles HTTP requests.
    """
    
    def __init__(
        self,
        app: Callable,
        listener: SocketListener,
        config: ServerConfig
    ):
        """
        Construct a worker.
        
        Args:
            app: The WSGI application.
            listener: The socket listener.
            config: Server configuration.
        """
        pass
    
    def run(self) -> None:
        """
        Main worker loop.
        
        Accepts connections and handles requests.
        """
        pass
    
    def handle_connection(
        self,
        client_sock: socket.socket,
        client_addr: Tuple[str, int]
    ) -> None:
        """
        Handle a single connection.
        
        May handle multiple requests if keep-alive is enabled.
        """
        pass
    
    def handle_request(
        self,
        client_sock: socket.socket,
        client_addr: Tuple[str, int]
    ) -> bool:
        """
        Handle a single HTTP request.
        
        Returns:
            True if connection should be kept alive.
        """
        pass
    
    def shutdown(self) -> None:
        """Gracefully shutdown the worker."""
        pass
```

### HTTPParser Class

```python
class HTTPParser:
    """
    Parses HTTP requests from socket data.
    """
    
    def __init__(self, config: ServerConfig):
        """
        Construct an HTTP parser.
        
        Args:
            config: Server configuration for limits.
        """
        pass
    
    def parse_request(
        self,
        sock: socket.socket
    ) -> Tuple[str, str, str, Dict[str, str], IO[bytes]]:
        """
        Parse an HTTP request from socket.
        
        Returns:
            Tuple of (method, path, http_version, headers, body_stream).
        
        Raises:
            BadRequest: If request is malformed.
        """
        pass
    
    def parse_request_line(self, line: bytes) -> Tuple[str, str, str]:
        """
        Parse HTTP request line.
        
        Args:
            line: Raw request line bytes.
        
        Returns:
            Tuple of (method, path, http_version).
        """
        pass
    
    def parse_headers(self, sock: socket.socket) -> Dict[str, str]:
        """
        Parse HTTP headers from socket.
        
        Handles header continuation lines.
        
        Returns:
            Dict of header name to value.
        """
        pass
    
    def build_environ(
        self,
        method: str,
        path: str,
        headers: Dict[str, str],
        body_stream: IO[bytes],
        client_addr: Tuple[str, int],
        server_addr: Tuple[str, int],
        scheme: str = "http"
    ) -> Dict[str, Any]:
        """
        Build WSGI environ dictionary from parsed request.
        
        Returns:
            Complete WSGI environ dict.
        """
        pass
```

### HTTPWriter Class

```python
class HTTPWriter:
    """
    Writes HTTP responses to socket.
    """
    
    def __init__(self, sock: socket.socket, config: ServerConfig):
        """
        Construct an HTTP writer.
        
        Args:
            sock: Client socket to write to.
            config: Server configuration.
        """
        pass
    
    def write_response(
        self,
        status: str,
        headers: List[Tuple[str, str]],
        body_iter: Iterable[bytes]
    ) -> None:
        """
        Write complete HTTP response.
        
        Args:
            status: Status line (e.g., "200 OK").
            headers: Response headers.
            body_iter: Response body iterator.
        """
        pass
    
    def write_status_line(self, status: str) -> None:
        """Write HTTP status line."""
        pass
    
    def write_headers(self, headers: List[Tuple[str, str]]) -> None:
        """Write HTTP headers."""
        pass
    
    def write_body(self, body_iter: Iterable[bytes]) -> None:
        """Write response body from iterator."""
        pass
    
    def write_chunked(self, body_iter: Iterable[bytes]) -> None:
        """Write response body using chunked transfer encoding."""
        pass
    
    def flush(self) -> None:
        """Flush buffered data to socket."""
        pass
```

### ConnectionManager Class

```python
class ConnectionManager:
    """
    Manages HTTP connection state and keep-alive.
    """
    
    def __init__(self, config: ServerConfig):
        """
        Construct a connection manager.
        
        Args:
            config: Server configuration.
        """
        pass
    
    def should_keep_alive(
        self,
        http_version: str,
        headers: Dict[str, str]
    ) -> bool:
        """
        Determine if connection should be kept alive.
        
        Args:
            http_version: HTTP version string.
            headers: Request headers.
        
        Returns:
            True if connection should be kept alive.
        """
        pass
    
    def get_timeout(self) -> float:
        """Get keep-alive timeout in seconds."""
        pass
    
    def track_connection(self, conn_id: str) -> None:
        """Track an active connection."""
        pass
    
    def release_connection(self, conn_id: str) -> None:
        """Release a connection."""
        pass
    
    def get_active_count(self) -> int:
        """Get number of active connections."""
        pass
```

### StartResponse Callable

```python
class StartResponse:
    """
    WSGI start_response callable implementation.
    
    Captures status and headers for later writing.
    """
    
    def __init__(self, writer: HTTPWriter):
        """
        Construct start_response callable.
        
        Args:
            writer: HTTP writer for response output.
        """
        self.writer = writer
        self.status: Optional[str] = None
        self.headers: Optional[List[Tuple[str, str]]] = None
        self.headers_sent: bool = False
        self.exc_info: Optional[Tuple] = None
    
    def __call__(
        self,
        status: str,
        response_headers: List[Tuple[str, str]],
        exc_info: Optional[Tuple] = None
    ) -> Callable[[bytes], None]:
        """
        WSGI start_response implementation.
        
        Args:
            status: HTTP status string.
            response_headers: List of (name, value) header tuples.
            exc_info: Optional exception info for error recovery.
        
        Returns:
            Write callable for legacy compatibility.
        """
        pass
    
    def write(self, data: bytes) -> None:
        """
        Legacy write callable.
        
        Sends headers if not already sent, then writes data.
        """
        pass
    
    def send_headers(self) -> None:
        """Send status and headers to client."""
        pass
```

## Data Models

### HTTP Status Codes

```python
# Standard HTTP status codes and reason phrases
HTTP_STATUS_PHRASES = {
    100: "Continue",
    101: "Switching Protocols",
    200: "OK",
    201: "Created",
    202: "Accepted",
    204: "No Content",
    301: "Moved Permanently",
    302: "Found",
    303: "See Other",
    304: "Not Modified",
    307: "Temporary Redirect",
    308: "Permanent Redirect",
    400: "Bad Request",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Not Found",
    405: "Method Not Allowed",
    406: "Not Acceptable",
    408: "Request Timeout",
    409: "Conflict",
    410: "Gone",
    413: "Request Entity Too Large",
    415: "Unsupported Media Type",
    422: "Unprocessable Entity",
    429: "Too Many Requests",
    500: "Internal Server Error",
    501: "Not Implemented",
    502: "Bad Gateway",
    503: "Service Unavailable",
    504: "Gateway Timeout",
}
```

### Framework Environ Keys

```python
# Framework-specific environ keys
ENVIRON_REQUEST = "webworks.request"
ENVIRON_ROUTE = "webworks.route"
ENVIRON_PATH_PARAMS = "webworks.path_params"
ENVIRON_ERROR = "webworks.error"
ENVIRON_DEBUG = "webworks.debug"
```

### UploadedFile Dataclass

```python
@dataclass
class UploadedFile:
    """
    Represents an uploaded file from multipart form data.
    """
    
    filename: str
    content_type: str
    content: bytes
    size: int
    
    def save(self, path: str) -> None:
        """Save the uploaded file to disk."""
        pass
    
    def read(self) -> bytes:
        """Read the file content."""
        return self.content
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: WSGI Interface Compliance

*For any* valid WSGI environ dictionary and start_response callable, the WSGIApplication SHALL be callable with these arguments and return an iterable that yields only bytes objects, with start_response called exactly once before any body content is yielded.

**Validates: Requirements 1.1, 1.2, 1.3**

### Property 2: Environ Parsing Round-Trip

*For any* valid WSGI environ dictionary containing REQUEST_METHOD, PATH_INFO, QUERY_STRING, HTTP_* headers, CONTENT_TYPE, CONTENT_LENGTH, wsgi.input, wsgi.url_scheme, SERVER_NAME, and SERVER_PORT, parsing the environ into a Request object SHALL preserve all values such that they can be reconstructed from the Request.

**Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 2.9, 2.10, 2.11**

### Property 3: Response Formatting Correctness

*For any* valid Response object with status_code, headers, and body, converting to WSGI format SHALL produce a status string matching "NNN Reason", headers as a list of (name, value) tuples excluding hop-by-hop headers, and body content encoded as bytes with correct Content-Length when body size is known.

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.7**

### Property 4: Middleware Compatibility

*For any* WSGI middleware that wraps the application, environ modifications made by the middleware SHALL be visible to the application, response modifications made by the middleware SHALL be returned to the server, and middleware execution order SHALL follow the wrapping order (outer before inner on request, inner before outer on response).

**Validates: Requirements 4.1, 4.2, 4.3, 4.5, 4.6, 4.7, 4.8**

### Property 5: Request Body Parsing Round-Trip

*For any* valid request body in form-encoded, multipart, or JSON format, parsing the body SHALL produce data that, when re-encoded in the same format, produces equivalent content.

**Validates: Requirements 7.1, 7.2, 7.3, 7.4, 7.5**

### Property 6: Request Body Size Enforcement

*For any* request body exceeding the configured max_request_body_size, the application SHALL return HTTP 413 Request Entity Too Large without processing the full body.

**Validates: Requirements 7.6, 7.7**

### Property 7: Error Response Correctness

*For any* HTTPException raised during request handling, the application SHALL return a response with the exception's status code. *For any* unhandled exception, the application SHALL return HTTP 500 and log the exception with stack trace. In production mode, error responses SHALL NOT contain internal details; in debug mode, they SHALL contain stack traces.

**Validates: Requirements 8.1, 8.2, 8.3, 8.4, 8.5, 8.8**

### Property 8: Response Iterator Protocol

*For any* response body (bytes, list, generator, or file), the ResponseIterator SHALL implement __iter__ and __next__ yielding only bytes, implement close() for resource cleanup, and the application SHALL call close() when iteration completes.

**Validates: Requirements 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7, 10.8**

### Property 9: Exception Propagation

*For any* exception raised before start_response is called, the exception SHALL propagate to the WSGI server unchanged. *For any* exception raised after start_response but before headers are sent, the application SHALL use exc_info to re-raise.

**Validates: Requirements 1.5, 1.6**

### Property 10: Framework Environ Extensions

*For any* request processed by the application, the environ dictionary SHALL contain webworks.request with the Request object, and after routing, SHALL contain webworks.route and webworks.path_params with the matched route information.

**Validates: Requirements 9.1, 9.2, 9.3, 9.4, 9.5, 9.6**

### Property 11: HTTP Request Parsing Correctness

*For any* valid HTTP/1.0 or HTTP/1.1 request, the HTTPParser SHALL correctly extract method, path, headers, and body, and construct a valid WSGI environ dictionary that preserves all request information.

**Validates: Requirements 11.1, 11.2, 11.3, 11.8, 11.9, 11.10**

### Property 12: HTTP Response Generation Correctness

*For any* WSGI response (status, headers, body iterator), the HTTPWriter SHALL produce a valid HTTP/1.1 response with correct status line, properly formatted headers, and complete body content.

**Validates: Requirements 12.1, 12.2, 12.3, 12.4, 12.5, 12.6**

### Property 13: Server Environ Construction

*For any* HTTP request received by the built-in server, the constructed WSGI environ dictionary SHALL contain all required CGI and WSGI keys with correct values matching the original HTTP request.

**Validates: Requirements 5.3, 5.4**

### Property 14: Keep-Alive Connection Handling

*For any* HTTP/1.1 request without Connection: close header, the server SHALL keep the connection open for subsequent requests until the keep-alive timeout expires or the client closes the connection.

**Validates: Requirements 5.9, 14.7**

### Property 15: Request Size Limit Enforcement

*For any* HTTP request with headers or body exceeding configured limits, the server SHALL return HTTP 400 Bad Request or HTTP 413 Request Entity Too Large without processing the full request.

**Validates: Requirements 11.4, 11.5, 7.6, 7.7**

### Property 16: Graceful Shutdown

*For any* shutdown signal (SIGTERM, SIGINT), the server SHALL stop accepting new connections, allow active requests to complete within the graceful timeout, and then terminate all workers.

**Validates: Requirements 5.8, 13.4, 13.7**

## Error Handling

### Exception Hierarchy

```python
class WSGIError(Exception):
    """Base exception for WSGI layer errors."""
    pass


class RequestEntityTooLarge(WSGIError, HTTPException):
    """Request body exceeds configured limit."""
    def __init__(self, max_size: int, actual_size: int):
        self.max_size = max_size
        self.actual_size = actual_size
        super().__init__(413, f"Request body too large: {actual_size} > {max_size}")


class BadRequestBody(WSGIError, HTTPException):
    """Request body is malformed."""
    def __init__(self, detail: str):
        super().__init__(400, f"Bad request body: {detail}")


class ServerError(WSGIError):
    """Base exception for server errors."""
    pass


class BindError(ServerError):
    """Failed to bind to address."""
    def __init__(self, address: str, detail: str):
        self.address = address
        super().__init__(f"Failed to bind to {address}: {detail}")


class WorkerError(ServerError):
    """Worker process error."""
    def __init__(self, worker_id: int, detail: str):
        self.worker_id = worker_id
        super().__init__(f"Worker {worker_id} error: {detail}")


class RequestParseError(WSGIError, HTTPException):
    """Failed to parse HTTP request."""
    def __init__(self, detail: str):
        super().__init__(400, f"Bad request: {detail}")


class HeaderTooLarge(RequestParseError):
    """Request headers exceed size limit."""
    def __init__(self, max_size: int):
        super().__init__(f"Headers exceed maximum size of {max_size} bytes")


class TooManyHeaders(RequestParseError):
    """Too many request headers."""
    def __init__(self, max_headers: int):
        super().__init__(f"Request has more than {max_headers} headers")


class RequestTimeout(WSGIError, HTTPException):
    """Request processing timed out."""
    def __init__(self, timeout: int):
        super().__init__(408, f"Request timeout after {timeout} seconds")
```

### Error Response Format

```python
# Production error response (no details)
{
    "error": {
        "status": 500,
        "message": "Internal Server Error"
    }
}

# Debug error response (with details)
{
    "error": {
        "status": 500,
        "message": "Internal Server Error",
        "type": "ValueError",
        "detail": "invalid literal for int()",
        "traceback": [
            "File \"app.py\", line 42, in handler",
            "    value = int(request.query_params['id'])",
            "ValueError: invalid literal for int() with base 10: 'abc'"
        ]
    }
}
```

## Testing Strategy

### Unit Tests

Unit tests should cover:
- EnvironParser extraction of individual environ keys
- ResponseBuilder formatting of status and headers
- ResponseIterator iteration and close() behavior
- ErrorHandler exception type dispatch
- RequestBodyParser format detection and parsing
- HTTPParser request line and header parsing
- HTTPWriter response formatting
- ServerConfig validation and defaults
- ConnectionManager keep-alive logic

### Property-Based Tests

Property tests should verify:
- WSGI interface compliance across random valid environs
- Environ parsing preserves all request data
- Response formatting produces valid WSGI output
- Middleware wrapping maintains execution order
- Body parsing round-trips for all supported formats
- Size limits are enforced correctly
- Error responses match exception types
- HTTP request parsing produces valid environ
- HTTP response generation produces valid HTTP
- Keep-alive decisions match HTTP specification

### Integration Tests

Integration tests should verify:
- Full request/response cycle through WSGI interface
- Middleware chain execution
- Error handling and recovery
- Resource cleanup via close()
- Built-in server request handling
- Worker process spawning and management
- Graceful shutdown behavior
- Keep-alive connection reuse
- SSL/TLS connections

### Test Configuration

- Use testbase framework per repository conventions
- Minimum 100 iterations for property-based tests
- Test files at `source/testroots/automojo/tests/singlehost/webworks/wsgi/`
- Server tests should use ephemeral ports to avoid conflicts
