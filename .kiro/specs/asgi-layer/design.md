# Design Document: ASGI Layer

## Overview

This design document describes the architecture and implementation approach for the ASGI Layer feature. The feature provides the Asynchronous Server Gateway Interface (ASGI) application interface that enables the web framework to communicate with ASGI-compliant web servers, handling asynchronous request/response processing, WebSocket connections, Server-Sent Events, background tasks, and lifespan events.

Key design principles:
- ASGI 3.0 Compliance: Full adherence to the ASGI specification
- Server Agnostic: Works with any ASGI-compliant server (Uvicorn, Hypercorn, Daphne)
- Async-First: Native async/await support throughout the stack
- Protocol Support: HTTP, WebSocket, and SSE handling
- Lifecycle Management: Proper startup/shutdown via lifespan protocol
- Resource Safety: Proper cleanup on disconnection and shutdown

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           ASGI Layer Architecture                            │
│                                                                              │
│  ASGI Server (Uvicorn, Hypercorn, etc.)                                     │
│         │                                                                    │
│         ▼                                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    ASGIApplication                                   │    │
│  │  async __call__(scope, receive, send)                               │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│         │                                                                    │
│         ├──────────────────────┬──────────────────────┐                     │
│         ▼                      ▼                      ▼                     │
│  ┌───────────────┐      ┌───────────────┐      ┌───────────────┐           │
│  │ HTTPHandler   │      │WebSocketHandler│     │LifespanHandler│           │
│  │ - handle()   │      │ - handle()     │      │ - handle()    │           │
│  └───────────────┘      └───────────────┘      └───────────────┘           │
│         │                      │                      │                     │
│         ▼                      ▼                      ▼                     │
│  ┌───────────────┐      ┌───────────────┐      ┌───────────────┐           │
│  │ ScopeParser   │      │ SSEHandler    │      │BackgroundTasks│           │
│  │ - parse()    │      │ - stream()    │      │ - add_task()  │           │
│  └───────────────┘      └───────────────┘      └───────────────┘           │
│         │                                                                    │
│         ▼                                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                         Framework Core                               │    │
│  │  Request → Router → Async Middleware Pipeline → Handler → Response  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                         ASGI HTTP Request Flow                               │
│                                                                              │
│  1. Server calls app(scope, receive, send)                                  │
│  2. ASGIApplication dispatches based on scope['type']                       │
│  3. HTTPHandler parses scope into Request                                   │
│  4. Body chunks received via receive() until more_body=False                │
│  5. Request dispatched through async middleware pipeline                    │
│  6. Handler generates Response object                                       │
│  7. send({"type": "http.response.start", ...}) called                      │
│  8. send({"type": "http.response.body", ...}) called for each chunk        │
│  9. Background tasks executed after response complete                       │
│                                                                              │
│  scope ──▶ ScopeParser ──▶ Request ──▶ Handler ──▶ Response                │
│                                                          │                   │
│                                                          ▼                   │
│  send(response.start) ◀── ResponseSender ◀───────────────┘                  │
│         │                                                                    │
│         ▼                                                                    │
│  send(response.body) ──▶ BackgroundTasks.run()                             │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                         WebSocket Connection Flow                            │
│                                                                              │
│  1. Server calls app(scope, receive, send) with scope['type']='websocket'  │
│  2. WebSocketHandler receives "websocket.connect" via receive()            │
│  3. Handler decides to accept or reject connection                          │
│  4. send({"type": "websocket.accept"}) or send({"type": "websocket.close"})│
│  5. Bidirectional message loop:                                             │
│     - receive() returns {"type": "websocket.receive", "text"/"bytes": ...} │
│     - send({"type": "websocket.send", "text"/"bytes": ...})                │
│  6. Connection closed via send({"type": "websocket.close"})                │
│  7. Or receive() returns {"type": "websocket.disconnect"}                  │
│                                                                              │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐                   │
│  │   connect   │────▶│   accept    │────▶│  message    │◀──┐               │
│  └─────────────┘     └─────────────┘     │    loop     │───┘               │
│                             │            └─────────────┘                    │
│                             │                   │                           │
│                             ▼                   ▼                           │
│                      ┌─────────────┐     ┌─────────────┐                   │
│                      │   reject    │     │   close     │                   │
│                      └─────────────┘     └─────────────┘                   │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                         Lifespan Event Flow                                  │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    Startup Phase                                     │    │
│  │  receive() ──▶ {"type": "lifespan.startup"}                         │    │
│  │      │                                                               │    │
│  │      ▼                                                               │    │
│  │  Run startup handlers in order                                       │    │
│  │      │                                                               │    │
│  │      ├──▶ Success: send({"type": "lifespan.startup.complete"})      │    │
│  │      └──▶ Failure: send({"type": "lifespan.startup.failed", ...})   │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    Shutdown Phase                                    │    │
│  │  receive() ──▶ {"type": "lifespan.shutdown"}                        │    │
│  │      │                                                               │    │
│  │      ▼                                                               │    │
│  │  Run shutdown handlers in reverse order                              │    │
│  │      │                                                               │    │
│  │      ├──▶ Success: send({"type": "lifespan.shutdown.complete"})     │    │
│  │      └──▶ Failure: send({"type": "lifespan.shutdown.failed", ...})  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Components and Interfaces

### ASGIApplication Class

```python
class ASGIApplication:
    """
    ASGI application callable that bridges ASGI servers to the framework.
    
    Implements ASGI 3.0 specification.
    """
    
    def __init__(
        self,
        dispatcher: "Dispatcher",
        debug: bool = False,
        max_request_body_size: int = 0,  # 0 = unlimited
        error_handler: Optional["ErrorHandler"] = None,
        lifespan_handler: Optional["LifespanHandler"] = None
    ):
        """
        Construct an ASGI application.
        
        Args:
            dispatcher: The framework dispatcher for request handling.
            debug: If True, include stack traces in error responses.
            max_request_body_size: Maximum request body size in bytes.
            error_handler: Custom error handler for exceptions.
            lifespan_handler: Handler for startup/shutdown events.
        """
        pass
    
    async def __call__(
        self,
        scope: Dict[str, Any],
        receive: Callable[[], Awaitable[Dict[str, Any]]],
        send: Callable[[Dict[str, Any]], Awaitable[None]]
    ) -> None:
        """
        ASGI application entry point.
        
        Args:
            scope: ASGI scope dictionary.
            receive: Async callable to receive messages.
            send: Async callable to send messages.
        """
        pass
    
    async def _handle_http(
        self,
        scope: Dict[str, Any],
        receive: Callable,
        send: Callable
    ) -> None:
        """Handle HTTP request/response cycle."""
        pass
    
    async def _handle_websocket(
        self,
        scope: Dict[str, Any],
        receive: Callable,
        send: Callable
    ) -> None:
        """Handle WebSocket connection."""
        pass
    
    async def _handle_lifespan(
        self,
        scope: Dict[str, Any],
        receive: Callable,
        send: Callable
    ) -> None:
        """Handle lifespan startup/shutdown events."""
        pass
```

### ScopeParser Class

```python
class ScopeParser:
    """
    Parses ASGI scope dictionary into framework Request objects.
    """
    
    def parse_http(self, scope: Dict[str, Any]) -> "Request":
        """
        Parse HTTP scope into a Request object.
        
        Args:
            scope: ASGI HTTP scope dictionary.
        
        Returns:
            Parsed Request object.
        """
        pass
    
    def get_method(self, scope: Dict[str, Any]) -> str:
        """Extract HTTP method from scope."""
        return scope.get("method", "GET")
    
    def get_path(self, scope: Dict[str, Any]) -> str:
        """Extract request path from scope."""
        return scope.get("path", "/")
    
    def get_query_string(self, scope: Dict[str, Any]) -> str:
        """Extract query string from scope (decoded from bytes)."""
        return scope.get("query_string", b"").decode("utf-8")
    
    def get_headers(self, scope: Dict[str, Any]) -> Dict[str, str]:
        """
        Extract HTTP headers from scope.
        
        Converts list of (name, value) byte tuples to dict.
        """
        pass
    
    def get_scheme(self, scope: Dict[str, Any]) -> str:
        """Extract URL scheme from scope."""
        return scope.get("scheme", "http")
    
    def get_server(self, scope: Dict[str, Any]) -> Tuple[str, int]:
        """Extract server (host, port) from scope."""
        return scope.get("server", ("localhost", 80))
    
    def get_client(self, scope: Dict[str, Any]) -> Optional[Tuple[str, int]]:
        """Extract client (host, port) from scope if available."""
        return scope.get("client")
    
    def get_http_version(self, scope: Dict[str, Any]) -> str:
        """Extract HTTP version from scope."""
        return scope.get("http_version", "1.1")
    
    def get_root_path(self, scope: Dict[str, Any]) -> str:
        """Extract root path for mounted applications."""
        return scope.get("root_path", "")
    
    def set_framework_scope(
        self,
        scope: Dict[str, Any],
        request: "Request",
        route: Optional["RouteMatch"] = None
    ) -> None:
        """
        Set framework-specific scope keys.
        
        Sets:
        - webworks.request: The Request object
        - webworks.route: The matched route (if any)
        - webworks.path_params: Path parameters (if any)
        """
        pass
```

### HTTPHandler Class

```python
class HTTPHandler:
    """
    Handles HTTP request/response cycles over ASGI.
    """
    
    def __init__(
        self,
        dispatcher: "Dispatcher",
        scope_parser: ScopeParser,
        body_reader: "BodyReader",
        response_sender: "ResponseSender",
        error_handler: "ErrorHandler",
        background_tasks: "BackgroundTasks"
    ):
        """Construct HTTP handler with dependencies."""
        pass
    
    async def handle(
        self,
        scope: Dict[str, Any],
        receive: Callable,
        send: Callable
    ) -> None:
        """
        Handle a complete HTTP request/response cycle.
        
        Args:
            scope: ASGI HTTP scope.
            receive: Async receive callable.
            send: Async send callable.
        """
        pass
    
    async def _read_body(
        self,
        receive: Callable,
        content_length: Optional[int]
    ) -> bytes:
        """Read complete request body from receive()."""
        pass
    
    async def _send_response(
        self,
        send: Callable,
        response: "Response"
    ) -> None:
        """Send response via send() callable."""
        pass
```

### BodyReader Class

```python
class BodyReader:
    """
    Reads request body from ASGI receive callable.
    """
    
    def __init__(self, max_size: int = 0):
        """
        Construct body reader.
        
        Args:
            max_size: Maximum body size (0 = unlimited).
        """
        pass
    
    async def read(
        self,
        receive: Callable,
        content_length: Optional[int] = None
    ) -> bytes:
        """
        Read complete request body.
        
        Args:
            receive: ASGI receive callable.
            content_length: Expected content length.
        
        Returns:
            Complete body as bytes.
        
        Raises:
            RequestEntityTooLarge: If body exceeds max_size.
            ClientDisconnected: If client disconnects during read.
        """
        pass
    
    async def stream(
        self,
        receive: Callable
    ) -> AsyncGenerator[bytes, None]:
        """
        Stream request body chunks.
        
        Args:
            receive: ASGI receive callable.
        
        Yields:
            Body chunks as bytes.
        """
        pass
    
    async def read_form(
        self,
        receive: Callable,
        content_type: str
    ) -> Dict[str, str]:
        """Parse form-encoded body asynchronously."""
        pass
    
    async def read_multipart(
        self,
        receive: Callable,
        content_type: str
    ) -> Tuple[Dict[str, str], Dict[str, "UploadedFile"]]:
        """Parse multipart form data asynchronously."""
        pass
    
    async def read_json(
        self,
        receive: Callable
    ) -> Any:
        """Parse JSON body asynchronously."""
        pass
```

### ResponseSender Class

```python
class ResponseSender:
    """
    Sends HTTP responses via ASGI send callable.
    """
    
    async def send(
        self,
        send: Callable,
        response: "Response"
    ) -> None:
        """
        Send complete response.
        
        Args:
            send: ASGI send callable.
            response: Framework Response object.
        """
        pass
    
    async def send_start(
        self,
        send: Callable,
        status: int,
        headers: List[Tuple[bytes, bytes]]
    ) -> None:
        """
        Send response start message.
        
        Args:
            send: ASGI send callable.
            status: HTTP status code.
            headers: List of (name, value) byte tuples.
        """
        await send({
            "type": "http.response.start",
            "status": status,
            "headers": headers
        })
    
    async def send_body(
        self,
        send: Callable,
        body: bytes,
        more_body: bool = False
    ) -> None:
        """
        Send response body chunk.
        
        Args:
            send: ASGI send callable.
            body: Body chunk as bytes.
            more_body: True if more chunks follow.
        """
        await send({
            "type": "http.response.body",
            "body": body,
            "more_body": more_body
        })
    
    async def send_streaming(
        self,
        send: Callable,
        status: int,
        headers: List[Tuple[bytes, bytes]],
        body_stream: AsyncGenerator[bytes, None]
    ) -> None:
        """
        Send streaming response.
        
        Args:
            send: ASGI send callable.
            status: HTTP status code.
            headers: Response headers.
            body_stream: Async generator yielding body chunks.
        """
        pass
    
    def format_headers(
        self,
        headers: Dict[str, str]
    ) -> List[Tuple[bytes, bytes]]:
        """Convert header dict to list of byte tuples."""
        pass
```

### WebSocketHandler Class

```python
class WebSocketHandler:
    """
    Handles WebSocket connections over ASGI.
    """
    
    def __init__(
        self,
        dispatcher: "Dispatcher",
        error_handler: "ErrorHandler"
    ):
        """Construct WebSocket handler."""
        pass
    
    async def handle(
        self,
        scope: Dict[str, Any],
        receive: Callable,
        send: Callable
    ) -> None:
        """
        Handle WebSocket connection lifecycle.
        
        Args:
            scope: ASGI WebSocket scope.
            receive: Async receive callable.
            send: Async send callable.
        """
        pass
    
    async def accept(
        self,
        send: Callable,
        subprotocol: Optional[str] = None,
        headers: Optional[List[Tuple[bytes, bytes]]] = None
    ) -> None:
        """
        Accept WebSocket connection.
        
        Args:
            send: ASGI send callable.
            subprotocol: Optional subprotocol to accept.
            headers: Optional additional headers.
        """
        await send({
            "type": "websocket.accept",
            "subprotocol": subprotocol,
            "headers": headers or []
        })
    
    async def reject(
        self,
        send: Callable,
        code: int = 403
    ) -> None:
        """
        Reject WebSocket connection.
        
        Args:
            send: ASGI send callable.
            code: Close code (default 403 Forbidden).
        """
        await send({
            "type": "websocket.close",
            "code": code
        })
    
    async def send_text(
        self,
        send: Callable,
        text: str
    ) -> None:
        """Send text message."""
        await send({
            "type": "websocket.send",
            "text": text
        })
    
    async def send_bytes(
        self,
        send: Callable,
        data: bytes
    ) -> None:
        """Send binary message."""
        await send({
            "type": "websocket.send",
            "bytes": data
        })
    
    async def close(
        self,
        send: Callable,
        code: int = 1000,
        reason: str = ""
    ) -> None:
        """
        Close WebSocket connection.
        
        Args:
            send: ASGI send callable.
            code: WebSocket close code.
            reason: Close reason string.
        """
        await send({
            "type": "websocket.close",
            "code": code,
            "reason": reason
        })
    
    async def receive_message(
        self,
        receive: Callable
    ) -> Optional[Union[str, bytes]]:
        """
        Receive next message from client.
        
        Returns:
            Text or bytes message, or None if disconnected.
        """
        pass
```

### SSEHandler Class

```python
class SSEHandler:
    """
    Handles Server-Sent Events streaming over HTTP.
    """
    
    SSE_CONTENT_TYPE = "text/event-stream"
    SSE_HEADERS = [
        (b"content-type", b"text/event-stream"),
        (b"cache-control", b"no-cache"),
        (b"connection", b"keep-alive")
    ]
    
    async def stream(
        self,
        send: Callable,
        event_source: AsyncGenerator["SSEEvent", None],
        headers: Optional[List[Tuple[bytes, bytes]]] = None
    ) -> None:
        """
        Stream SSE events to client.
        
        Args:
            send: ASGI send callable.
            event_source: Async generator yielding SSE events.
            headers: Optional additional headers.
        """
        pass
    
    def format_event(self, event: "SSEEvent") -> bytes:
        """
        Format SSE event as bytes.
        
        Args:
            event: SSE event to format.
        
        Returns:
            Formatted event bytes with proper field prefixes.
        """
        pass
    
    async def send_event(
        self,
        send: Callable,
        data: str,
        event: Optional[str] = None,
        id: Optional[str] = None,
        retry: Optional[int] = None
    ) -> None:
        """
        Send single SSE event.
        
        Args:
            send: ASGI send callable.
            data: Event data.
            event: Optional event name.
            id: Optional event ID.
            retry: Optional retry interval in milliseconds.
        """
        pass
```

### LifespanHandler Class

```python
class LifespanHandler:
    """
    Handles ASGI lifespan startup/shutdown events.
    """
    
    def __init__(self):
        """Construct lifespan handler."""
        self._startup_handlers: List[Callable[[], Awaitable[None]]] = []
        self._shutdown_handlers: List[Callable[[], Awaitable[None]]] = []
    
    def on_startup(
        self,
        handler: Callable[[], Awaitable[None]]
    ) -> Callable[[], Awaitable[None]]:
        """
        Register startup handler.
        
        Args:
            handler: Async function to run on startup.
        
        Returns:
            The handler (for decorator use).
        """
        pass
    
    def on_shutdown(
        self,
        handler: Callable[[], Awaitable[None]]
    ) -> Callable[[], Awaitable[None]]:
        """
        Register shutdown handler.
        
        Args:
            handler: Async function to run on shutdown.
        
        Returns:
            The handler (for decorator use).
        """
        pass
    
    async def handle(
        self,
        scope: Dict[str, Any],
        receive: Callable,
        send: Callable
    ) -> None:
        """
        Handle lifespan events.
        
        Args:
            scope: ASGI lifespan scope.
            receive: Async receive callable.
            send: Async send callable.
        """
        pass
    
    async def _run_startup(self, send: Callable) -> None:
        """Run startup handlers in registration order."""
        pass
    
    async def _run_shutdown(self, send: Callable) -> None:
        """Run shutdown handlers in reverse registration order."""
        pass
```

### BackgroundTasks Class

```python
class BackgroundTasks:
    """
    Manages background tasks to run after response completion.
    """
    
    def __init__(self):
        """Construct background tasks manager."""
        self._tasks: List[Tuple[Callable, tuple, dict]] = []
    
    def add_task(
        self,
        func: Callable[..., Awaitable[Any]],
        *args: Any,
        **kwargs: Any
    ) -> None:
        """
        Schedule a background task.
        
        Args:
            func: Async function to run.
            *args: Positional arguments for the function.
            **kwargs: Keyword arguments for the function.
        """
        pass
    
    async def run(self) -> None:
        """
        Execute all scheduled background tasks.
        
        Tasks are executed in the order they were added.
        Exceptions are logged but do not propagate.
        """
        pass
    
    def clear(self) -> None:
        """Clear all pending tasks."""
        pass
    
    async def cancel_all(self) -> None:
        """Cancel all pending tasks (for shutdown)."""
        pass
```

### ErrorHandler Class

```python
class ErrorHandler:
    """
    Handles exceptions during ASGI request processing.
    """
    
    def __init__(
        self,
        debug: bool = False,
        logger: Optional["Logger"] = None
    ):
        """
        Construct error handler.
        
        Args:
            debug: If True, include stack traces in responses.
            logger: Logger for error logging.
        """
        pass
    
    async def handle_http_error(
        self,
        exc: Exception,
        send: Callable,
        scope: Dict[str, Any]
    ) -> None:
        """
        Handle HTTP error and send error response.
        
        Args:
            exc: The exception that occurred.
            send: ASGI send callable.
            scope: ASGI scope for context.
        """
        pass
    
    async def handle_websocket_error(
        self,
        exc: Exception,
        send: Callable,
        scope: Dict[str, Any]
    ) -> None:
        """
        Handle WebSocket error and close connection.
        
        Args:
            exc: The exception that occurred.
            send: ASGI send callable.
            scope: ASGI scope for context.
        """
        pass
    
    def format_error_body(
        self,
        status_code: int,
        message: str,
        exc: Optional[Exception] = None
    ) -> bytes:
        """Format error response body."""
        pass
    
    def log_exception(
        self,
        exc: Exception,
        scope: Dict[str, Any]
    ) -> None:
        """Log exception with stack trace."""
        pass
    
    def register_handler(
        self,
        exc_type: Type[Exception],
        handler: Callable[[Exception], Awaitable["Response"]]
    ) -> None:
        """Register custom handler for exception type."""
        pass
```

### Application Factory

```python
def get_asgi_application() -> ASGIApplication:
    """
    Get the ASGI application callable.
    
    This is the main entry point for ASGI servers.
    
    Returns:
        Configured ASGIApplication instance.
    """
    pass


def create_asgi_application(
    config: Optional[Dict[str, Any]] = None
) -> ASGIApplication:
    """
    Application factory for creating ASGI applications.
    
    Each call creates a new application instance.
    
    Args:
        config: Optional configuration dict.
    
    Returns:
        New ASGIApplication instance.
    """
    pass


# Module-level application variable for ASGI servers
application: Optional[ASGIApplication] = None
```

## Data Models

### SSEEvent Dataclass

```python
@dataclass
class SSEEvent:
    """
    Represents a Server-Sent Event.
    """
    
    data: str
    event: Optional[str] = None
    id: Optional[str] = None
    retry: Optional[int] = None
    
    def format(self) -> str:
        """Format event as SSE string."""
        lines = []
        if self.event:
            lines.append(f"event: {self.event}")
        if self.id:
            lines.append(f"id: {self.id}")
        if self.retry is not None:
            lines.append(f"retry: {self.retry}")
        for line in self.data.split("\n"):
            lines.append(f"data: {line}")
        lines.append("")
        lines.append("")
        return "\n".join(lines)
```

### WebSocket Close Codes

```python
# Standard WebSocket close codes
WS_CLOSE_NORMAL = 1000
WS_CLOSE_GOING_AWAY = 1001
WS_CLOSE_PROTOCOL_ERROR = 1002
WS_CLOSE_UNSUPPORTED_DATA = 1003
WS_CLOSE_NO_STATUS = 1005
WS_CLOSE_ABNORMAL = 1006
WS_CLOSE_INVALID_DATA = 1007
WS_CLOSE_POLICY_VIOLATION = 1008
WS_CLOSE_MESSAGE_TOO_BIG = 1009
WS_CLOSE_MANDATORY_EXTENSION = 1010
WS_CLOSE_INTERNAL_ERROR = 1011
WS_CLOSE_SERVICE_RESTART = 1012
WS_CLOSE_TRY_AGAIN_LATER = 1013
```

### Framework Scope Keys

```python
# Framework-specific scope keys
SCOPE_REQUEST = "webworks.request"
SCOPE_ROUTE = "webworks.route"
SCOPE_PATH_PARAMS = "webworks.path_params"
SCOPE_ERROR = "webworks.error"
SCOPE_DEBUG = "webworks.debug"
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
    
    async def save(self, path: str) -> None:
        """Save the uploaded file to disk asynchronously."""
        pass
    
    def read(self) -> bytes:
        """Read the file content."""
        return self.content
```



## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: ASGI Interface Compliance

*For any* valid ASGI scope dictionary, receive callable, and send callable, the ASGIApplication SHALL be an async callable that handles the connection without raising unhandled exceptions, dispatching to the appropriate handler based on scope['type'].

**Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7**

### Property 2: HTTP Scope Parsing Round-Trip

*For any* valid ASGI HTTP scope containing method, path, query_string, headers, scheme, server, client, http_version, and root_path, parsing the scope into a Request object SHALL preserve all values such that they can be reconstructed from the Request.

**Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 2.9, 2.10**

### Property 3: HTTP Response Message Ordering

*For any* HTTP response, the application SHALL send exactly one "http.response.start" message before any "http.response.body" messages, and the final body message SHALL have more_body=False.

**Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.8, 4.9**

### Property 4: Request Body Streaming

*For any* request body received via multiple "http.request" messages, accumulating all body chunks until more_body=False SHALL produce the complete request body, and streaming SHALL yield the same total content as buffered reading.

**Validates: Requirements 3.1, 3.2, 3.3**

### Property 5: Request Body Parsing Round-Trip

*For any* valid request body in form-encoded, multipart, or JSON format, parsing the body asynchronously SHALL produce data that, when re-encoded in the same format, produces equivalent content.

**Validates: Requirements 3.4, 3.5, 3.6**

### Property 6: Request Body Size Enforcement

*For any* request body exceeding the configured max_request_body_size, the application SHALL return HTTP 413 Request Entity Too Large without processing the full body.

**Validates: Requirements 3.7, 3.8**

### Property 7: WebSocket Connection Lifecycle

*For any* WebSocket connection, the application SHALL receive "websocket.connect" before any messages, SHALL send either "websocket.accept" or "websocket.close" in response, and after accept SHALL handle "websocket.receive" and "websocket.send" messages until "websocket.disconnect" is received or "websocket.close" is sent.

**Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 5.8, 5.9, 5.10, 5.11**

### Property 8: SSE Event Formatting

*For any* SSE event with data, optional event name, optional id, and optional retry, formatting the event SHALL produce a string with proper field prefixes ("data:", "event:", "id:", "retry:") and double newline termination.

**Validates: Requirements 6.2, 6.3, 6.4, 6.5, 6.6**

### Property 9: Background Task Execution Order

*For any* sequence of background tasks added to a request, tasks SHALL execute in the order they were added, after the response is sent, and exceptions in one task SHALL NOT prevent execution of subsequent tasks.

**Validates: Requirements 7.1, 7.3, 7.4, 7.5, 7.6**

### Property 10: Lifespan Handler Ordering

*For any* set of registered startup and shutdown handlers, startup handlers SHALL execute in registration order, shutdown handlers SHALL execute in reverse registration order, and startup failure SHALL prevent the application from accepting requests.

**Validates: Requirements 8.8, 8.9, 8.10, 8.11, 8.12**

### Property 11: Lifespan Protocol Compliance

*For any* lifespan scope, receiving "lifespan.startup" SHALL result in either "lifespan.startup.complete" or "lifespan.startup.failed" being sent, and receiving "lifespan.shutdown" SHALL result in either "lifespan.shutdown.complete" or "lifespan.shutdown.failed" being sent.

**Validates: Requirements 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7**

### Property 12: Error Response Correctness

*For any* HTTPException raised during request handling, the application SHALL return a response with the exception's status code. *For any* unhandled exception, the application SHALL return HTTP 500 and log the exception with stack trace. In production mode, error responses SHALL NOT contain internal details; in debug mode, they SHALL contain stack traces.

**Validates: Requirements 10.1, 10.2, 10.3, 10.4, 10.5, 10.8**

### Property 13: Framework Scope Extensions

*For any* request processed by the application, the scope dictionary SHALL contain webworks.request with the Request object, and after routing, SHALL contain webworks.route and webworks.path_params with the matched route information.

**Validates: Requirements 12.1, 12.2, 12.3, 12.4, 12.5, 12.6, 12.7**

## Error Handling

### Exception Hierarchy

```python
class ASGIError(Exception):
    """Base exception for ASGI layer errors."""
    pass


class RequestEntityTooLarge(ASGIError, HTTPException):
    """Request body exceeds configured limit."""
    def __init__(self, max_size: int, actual_size: int):
        self.max_size = max_size
        self.actual_size = actual_size
        super().__init__(413, f"Request body too large: {actual_size} > {max_size}")


class ClientDisconnected(ASGIError):
    """Client disconnected during request processing."""
    pass


class WebSocketError(ASGIError):
    """Error during WebSocket handling."""
    def __init__(self, code: int, reason: str = ""):
        self.code = code
        self.reason = reason
        super().__init__(f"WebSocket error {code}: {reason}")


class LifespanError(ASGIError):
    """Error during lifespan handling."""
    pass


class StartupError(LifespanError):
    """Error during application startup."""
    pass


class ShutdownError(LifespanError):
    """Error during application shutdown."""
    pass
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
- ScopeParser extraction of individual scope keys
- ResponseSender message formatting
- SSEHandler event formatting
- WebSocketHandler message handling
- LifespanHandler event sequencing
- BackgroundTasks scheduling and execution
- ErrorHandler exception type dispatch
- BodyReader chunk accumulation

### Property-Based Tests

Property tests should verify:
- ASGI interface compliance across random valid scopes
- HTTP scope parsing preserves all request data
- Response message ordering is always correct
- Body streaming produces same content as buffered reading
- Body parsing round-trips for all supported formats
- Size limits are enforced correctly
- WebSocket lifecycle follows protocol
- SSE events are correctly formatted
- Background tasks execute in order
- Lifespan handlers execute in correct order
- Error responses match exception types
- Framework scope extensions are set correctly

### Integration Tests

Integration tests should verify:
- Full HTTP request/response cycle through ASGI interface
- WebSocket connection lifecycle
- SSE streaming with client disconnection
- Background task execution after response
- Lifespan startup/shutdown sequence
- Error handling and recovery
- Concurrent request handling

### Test Configuration

- Use testbase framework per repository conventions
- Minimum 100 iterations for property-based tests
- Test files at `source/testroots/automojo/tests/singlehost/webworks/asgi/`

