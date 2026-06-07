# Design Document: Developer Experience

## Overview

This design document describes the architecture and implementation approach for the Developer Experience feature. The feature provides CLI tooling for common development tasks, testing utilities for endpoint and integration testing, and debug/error pages for development-time troubleshooting.

Key design principles:
- Unified CLI: All development tools accessible through a single command interface
- Test-friendly: Testing utilities that integrate with the testbase framework
- Debug-first: Rich error information during development, secure in production
- Extensible: Plugin architecture for custom commands and tools
- Convention-based: Sensible defaults with override capabilities

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CLI Framework Layer                                │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                         WebworksCLI                                  │    │
│  │  - main entry point: `webworks`                                     │    │
│  │  - global options: --verbose, --config, --env                       │    │
│  │  - plugin loading and command registration                          │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                              │                                               │
│          ┌───────────────────┼───────────────────┐                          │
│          ▼                   ▼                   ▼                          │
│  ┌───────────────┐   ┌───────────────┐   ┌───────────────┐                 │
│  │ ServerGroup   │   │ GenerateGroup │   │ DatabaseGroup │                 │
│  │ - serve       │   │ - endpoint    │   │ - init        │                 │
│  │ - routes      │   │ - blueprint   │   │ - migrate     │                 │
│  │ - shell       │   │ - new         │   │ - rollback    │                 │
│  └───────────────┘   └───────────────┘   └───────────────┘                 │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                        Development Server Layer                              │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                      DevelopmentServer                               │    │
│  │  - host: str = "127.0.0.1"                                          │    │
│  │  - port: int = 8000                                                 │    │
│  │  - debug: bool = True                                               │    │
│  │  - reload: bool = False                                             │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                              │                                               │
│          ┌───────────────────┼───────────────────┐                          │
│          ▼                   ▼                   ▼                          │
│  ┌───────────────┐   ┌───────────────┐   ┌───────────────┐                 │
│  │ FileWatcher   │   │ RequestLogger │   │ DebugMiddleware│                │
│  │ - patterns    │   │ - format      │   │ - error_handler│                │
│  │ - excludes    │   │ - colors      │   │ - inspector    │                │
│  │ - callback    │   │ - timing      │   │ - debugger     │                │
│  └───────────────┘   └───────────────┘   └───────────────┘                 │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                         Testing Utilities Layer                              │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                         TestClient                                   │    │
│  │  - app: WebApplication                                              │    │
│  │  - cookies: CookieJar                                               │    │
│  │  - default_headers: Dict[str, str]                                  │    │
│  │                                                                      │    │
│  │  Methods: get(), post(), put(), patch(), delete(), head(), options()│    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                              │                                               │
│          ┌───────────────────┼───────────────────┐                          │
│          ▼                   ▼                   ▼                          │
│  ┌───────────────┐   ┌───────────────┐   ┌───────────────┐                 │
│  │ TestResponse  │   │ TestFixtures  │   │ Assertions    │                 │
│  │ - status_code │   │ - test_app    │   │ - assert_status│                │
│  │ - headers     │   │ - test_client │   │ - assert_json │                │
│  │ - body        │   │ - mock_request│   │ - assert_header│               │
│  │ - json        │   │ - mock_response│  │ - assert_redirect│             │
│  └───────────────┘   └───────────────┘   └───────────────┘                 │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                         Debug/Error Pages Layer                              │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                      DebugErrorHandler                               │    │
│  │  - debug: bool                                                      │    │
│  │  - interactive: bool                                                │    │
│  │  - pin: Optional[str]                                               │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                              │                                               │
│          ┌───────────────────┴───────────────────┐                          │
│          ▼                                       ▼                          │
│  ┌─────────────────────────┐         ┌─────────────────────────┐           │
│  │    DebugErrorPage       │         │   ProductionErrorPage   │           │
│  │  - exception info       │         │   - generic message     │           │
│  │  - stack trace          │         │   - error reference ID  │           │
│  │  - local variables      │         │   - custom templates    │           │
│  │  - request context      │         │   - server-side logging │           │
│  │  - interactive console  │         │                         │           │
│  └─────────────────────────┘         └─────────────────────────┘           │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Components and Interfaces

### CLI Framework

```python
class WebworksCLI:
    """
    Main CLI entry point providing command registration and execution.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path
        self.config: Dict[str, Any] = {}
        self._commands: Dict[str, "CLICommand"] = {}
        self._groups: Dict[str, "CLIGroup"] = {}
    
    def load_config(self) -> None:
        """
        Load configuration from file and environment variables.
        Environment variables take precedence over file config.
        """
        pass
    
    def register_command(self, command: "CLICommand") -> None:
        """Register a top-level command."""
        pass
    
    def register_group(self, group: "CLIGroup") -> None:
        """Register a command group."""
        pass
    
    def run(self, args: Optional[List[str]] = None) -> int:
        """
        Parse arguments and execute the appropriate command.
        
        Returns:
            Exit code (0 for success, non-zero for errors).
        """
        pass


class CLICommand:
    """
    Base class for CLI commands.
    """
    
    name: str  # Command name
    help: str  # Help text
    
    def add_arguments(self, parser: "ArgumentParser") -> None:
        """Add command-specific arguments to the parser."""
        pass
    
    def execute(self, args: "Namespace", config: Dict[str, Any]) -> int:
        """
        Execute the command.
        
        Args:
            args: Parsed command-line arguments.
            config: Loaded configuration.
        
        Returns:
            Exit code.
        """
        raise NotImplementedError()


class CLIGroup:
    """
    A group of related CLI commands.
    """
    
    name: str  # Group name (e.g., "server", "db")
    help: str  # Group help text
    commands: List[CLICommand]  # Commands in this group
    
    def register_commands(self, parser: "ArgumentParser") -> None:
        """Register all commands in this group."""
        pass
```

### Development Server

```python
class DevelopmentServer:
    """
    Development HTTP server with debug features.
    """
    
    def __init__(
        self,
        app: "WebApplication",
        host: str = "127.0.0.1",
        port: int = 8000,
        debug: bool = True,
        reload: bool = False,
        watch_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None
    ):
        self.app = app
        self.host = host
        self.port = port
        self.debug = debug
        self.reload = reload
        self.watch_patterns = watch_patterns or ["**/*.py"]
        self.exclude_patterns = exclude_patterns or [
            ".git", "__pycache__", ".venv", "*.pyc"
        ]
        self._watcher: Optional["FileWatcher"] = None
    
    def start(self) -> None:
        """
        Start the development server.
        
        If reload is enabled, starts the file watcher.
        Binds to host:port and begins serving requests.
        """
        pass
    
    def stop(self) -> None:
        """Stop the server and cleanup resources."""
        pass
    
    def _setup_debug_middleware(self) -> None:
        """Configure debug middleware for error handling."""
        pass
    
    def _setup_request_logging(self) -> None:
        """Configure request logging middleware."""
        pass


class FileWatcher:
    """
    Watches files for changes and triggers callbacks.
    """
    
    def __init__(
        self,
        patterns: List[str],
        excludes: List[str],
        callback: Callable[[], None]
    ):
        self.patterns = patterns
        self.excludes = excludes
        self.callback = callback
        self._running = False
    
    def start(self) -> None:
        """Start watching for file changes."""
        pass
    
    def stop(self) -> None:
        """Stop watching."""
        pass
    
    def _should_watch(self, path: str) -> bool:
        """Check if a path matches watch patterns and not excludes."""
        pass
    
    def _on_change(self, path: str) -> None:
        """Handle a file change event."""
        pass


class RequestLogger:
    """
    Middleware that logs request/response information.
    """
    
    def __init__(
        self,
        format: str = "%(method)s %(path)s %(status)s %(time)sms",
        use_colors: bool = True
    ):
        self.format = format
        self.use_colors = use_colors
    
    def __call__(
        self,
        request: "Request",
        call_next: Callable[["Request"], "Response"]
    ) -> "Response":
        """Log the request and response."""
        pass
    
    def _format_log(
        self,
        method: str,
        path: str,
        status: int,
        time_ms: float
    ) -> str:
        """Format the log message with optional colors."""
        pass
```

### Testing Utilities

```python
class TestClient:
    """
    HTTP client for testing endpoints without a real server.
    """
    
    def __init__(
        self,
        app: "WebApplication",
        default_headers: Optional[Dict[str, str]] = None
    ):
        self.app = app
        self.default_headers = default_headers or {}
        self.cookies: "CookieJar" = CookieJar()
    
    def get(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> "TestResponse":
        """Send a GET request."""
        pass
    
    def post(
        self,
        path: str,
        json: Optional[Any] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> "TestResponse":
        """Send a POST request."""
        pass
    
    def put(
        self,
        path: str,
        json: Optional[Any] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> "TestResponse":
        """Send a PUT request."""
        pass
    
    def patch(
        self,
        path: str,
        json: Optional[Any] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> "TestResponse":
        """Send a PATCH request."""
        pass
    
    def delete(
        self,
        path: str,
        headers: Optional[Dict[str, str]] = None
    ) -> "TestResponse":
        """Send a DELETE request."""
        pass
    
    def head(
        self,
        path: str,
        headers: Optional[Dict[str, str]] = None
    ) -> "TestResponse":
        """Send a HEAD request."""
        pass
    
    def options(
        self,
        path: str,
        headers: Optional[Dict[str, str]] = None
    ) -> "TestResponse":
        """Send an OPTIONS request."""
        pass
    
    def _make_request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Any] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> "TestResponse":
        """
        Create and execute a request against the application.
        
        Merges default headers with request-specific headers.
        Handles cookie management across requests.
        """
        pass


@dataclass
class TestResponse:
    """
    Response object returned by TestClient.
    """
    
    status_code: int
    headers: Dict[str, str]
    body: bytes
    
    @property
    def text(self) -> str:
        """Decode body as UTF-8 text."""
        return self.body.decode("utf-8")
    
    @property
    def json(self) -> Any:
        """Parse body as JSON."""
        import json
        return json.loads(self.body)
    
    def get_header(self, name: str, default: Optional[str] = None) -> Optional[str]:
        """Get a header value (case-insensitive)."""
        pass
```

### Test Fixtures

```python
# Test fixtures for testbase framework integration

@testbase.register.resource_factory()
def create_test_app(
    constraints: Dict[str, Any] = None
) -> Generator["WebApplication", None, None]:
    """
    Create a test application instance.
    
    Args:
        constraints: Optional configuration overrides.
    
    Yields:
        Configured WebApplication instance.
    """
    config = constraints or {}
    app = WebApplication()
    # Apply test configuration
    app.config.update(config)
    app.config["TESTING"] = True
    app.config["DEBUG"] = False
    yield app
    # Cleanup


@testbase.register.resource_factory()
def create_test_client(
    app: "WebApplication",
    constraints: Dict[str, Any] = None
) -> Generator["TestClient", None, None]:
    """
    Create a test client bound to an application.
    
    Args:
        app: The application instance.
        constraints: Optional client configuration.
    
    Yields:
        TestClient instance.
    """
    config = constraints or {}
    client = TestClient(app, default_headers=config.get("headers"))
    yield client


@testbase.register.resource_factory()
def create_mock_request(
    constraints: Dict[str, Any] = None
) -> Generator["Request", None, None]:
    """
    Create a mock request object for testing.
    
    Args:
        constraints: Request attributes (method, path, headers, body).
    
    Yields:
        Mock Request instance.
    """
    config = constraints or {}
    request = MockRequest(
        method=config.get("method", "GET"),
        path=config.get("path", "/"),
        headers=config.get("headers", {}),
        body=config.get("body", b"")
    )
    yield request
```

### Assertion Helpers

```python
class TestAssertions:
    """
    Assertion helpers for endpoint testing.
    """
    
    @staticmethod
    def assert_status(response: TestResponse, expected: int) -> None:
        """
        Assert response status code matches expected.
        
        Args:
            response: The test response.
            expected: Expected status code.
        
        Raises:
            AssertionError: If status codes don't match.
        """
        if response.status_code != expected:
            raise AssertionError(
                f"Expected status {expected}, got {response.status_code}"
            )
    
    @staticmethod
    def assert_json(
        response: TestResponse,
        expected: Any,
        partial: bool = False
    ) -> None:
        """
        Assert response JSON matches expected.
        
        Args:
            response: The test response.
            expected: Expected JSON structure.
            partial: If True, only check that expected keys exist.
        
        Raises:
            AssertionError: If JSON doesn't match.
        """
        pass
    
    @staticmethod
    def assert_header(
        response: TestResponse,
        name: str,
        expected: str
    ) -> None:
        """
        Assert response header matches expected value.
        
        Args:
            response: The test response.
            name: Header name (case-insensitive).
            expected: Expected header value.
        
        Raises:
            AssertionError: If header doesn't match.
        """
        pass
    
    @staticmethod
    def assert_content_type(
        response: TestResponse,
        expected: str
    ) -> None:
        """
        Assert Content-Type header matches expected.
        
        Args:
            response: The test response.
            expected: Expected content type.
        
        Raises:
            AssertionError: If content type doesn't match.
        """
        pass
    
    @staticmethod
    def assert_redirect(
        response: TestResponse,
        expected_location: str,
        status: int = 302
    ) -> None:
        """
        Assert response is a redirect to expected location.
        
        Args:
            response: The test response.
            expected_location: Expected Location header value.
            status: Expected redirect status code.
        
        Raises:
            AssertionError: If not a redirect or location doesn't match.
        """
        pass
```

### Debug Error Handler

```python
class DebugErrorHandler:
    """
    Handles exceptions and generates appropriate error pages.
    """
    
    def __init__(
        self,
        debug: bool = False,
        interactive: bool = False,
        pin: Optional[str] = None,
        template_path: Optional[str] = None
    ):
        self.debug = debug
        self.interactive = interactive
        self.pin = pin
        self.template_path = template_path
        self._request_store: List["RequestInfo"] = []
    
    def handle_exception(
        self,
        request: "Request",
        exception: Exception
    ) -> "Response":
        """
        Handle an exception and return appropriate error response.
        
        In debug mode, returns detailed error page.
        In production, returns generic error page and logs details.
        """
        pass
    
    def _render_debug_page(
        self,
        request: "Request",
        exception: Exception
    ) -> str:
        """Render the debug error page HTML."""
        pass
    
    def _render_production_page(
        self,
        request: "Request",
        exception: Exception,
        error_id: str
    ) -> str:
        """Render the production error page HTML."""
        pass
    
    def _extract_traceback(
        self,
        exception: Exception
    ) -> List["FrameInfo"]:
        """Extract stack frames with source context."""
        pass
    
    def _get_local_variables(
        self,
        frame: "FrameType"
    ) -> Dict[str, str]:
        """Get formatted local variables from a frame."""
        pass


@dataclass
class FrameInfo:
    """
    Information about a single stack frame.
    """
    
    filename: str
    lineno: int
    function: str
    code_context: List[str]  # Lines of source code around the error
    highlight_line: int  # Index of the error line in code_context
    locals: Dict[str, str]  # Formatted local variables


class InteractiveDebugger:
    """
    Browser-based interactive debugger for error pages.
    """
    
    def __init__(self, pin: str, timeout: int = 300):
        self.pin = pin
        self.timeout = timeout
        self._sessions: Dict[str, "DebugSession"] = {}
    
    def create_session(
        self,
        exception: Exception,
        frames: List["FrameInfo"]
    ) -> str:
        """
        Create a debug session for an exception.
        
        Returns:
            Session ID for the debug console.
        """
        pass
    
    def evaluate(
        self,
        session_id: str,
        frame_index: int,
        expression: str,
        pin: str
    ) -> Dict[str, Any]:
        """
        Evaluate an expression in a frame context.
        
        Args:
            session_id: Debug session ID.
            frame_index: Index of the stack frame.
            expression: Python expression to evaluate.
            pin: Security PIN for authorization.
        
        Returns:
            Dict with 'result' or 'error' key.
        """
        pass
    
    def _cleanup_expired(self) -> None:
        """Remove expired debug sessions."""
        pass
```

### Request Inspector

```python
class RequestInspector:
    """
    Development tool for inspecting incoming requests.
    """
    
    def __init__(
        self,
        max_requests: int = 100,
        max_body_size: int = 10240,
        path_filter: Optional[str] = None
    ):
        self.max_requests = max_requests
        self.max_body_size = max_body_size
        self.path_filter = path_filter
        self._requests: List["RequestInfo"] = []
    
    def capture(self, request: "Request") -> None:
        """
        Capture request information for inspection.
        
        Args:
            request: The incoming request.
        """
        pass
    
    def get_requests(
        self,
        limit: Optional[int] = None,
        path_filter: Optional[str] = None
    ) -> List["RequestInfo"]:
        """
        Get captured requests.
        
        Args:
            limit: Maximum number of requests to return.
            path_filter: Filter by path pattern.
        
        Returns:
            List of captured request info.
        """
        pass
    
    def clear(self) -> None:
        """Clear all captured requests."""
        pass


@dataclass
class RequestInfo:
    """
    Captured request information.
    """
    
    timestamp: datetime
    method: str
    path: str
    query_params: Dict[str, Any]
    headers: Dict[str, str]
    body: Optional[bytes]
    body_truncated: bool
    parsed_body: Optional[Any]  # JSON or form data if applicable
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        pass
```

## Data Models

### CLI Exit Codes

```python
# Standard CLI exit codes
EXIT_SUCCESS = 0
EXIT_ERROR = 1
EXIT_USAGE_ERROR = 2
EXIT_CONFIG_ERROR = 3
EXIT_NOT_FOUND = 4
```

### Default Configuration

```python
# Default CLI configuration
DEFAULT_CONFIG = {
    "server": {
        "host": "127.0.0.1",
        "port": 8000,
        "debug": True,
        "reload": False,
    },
    "logging": {
        "level": "DEBUG",
        "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        "colors": True,
    },
    "debug": {
        "interactive": False,
        "pin": None,  # Auto-generated if interactive enabled
        "timeout": 300,
    },
    "inspector": {
        "enabled": False,
        "max_requests": 100,
        "max_body_size": 10240,
    },
}
```

### Project Templates

```python
# Available project templates for scaffolding
PROJECT_TEMPLATES = {
    "minimal": {
        "description": "Minimal project with single endpoint",
        "files": ["app.py", "config.py"],
    },
    "api": {
        "description": "REST API project with blueprints",
        "files": ["app.py", "config.py", "blueprints/", "models/", "tests/"],
    },
    "webapp": {
        "description": "Full web application with templates",
        "files": ["app.py", "config.py", "blueprints/", "models/", "templates/", "static/", "tests/"],
    },
}
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: TestClient Request-Response Consistency

*For any* HTTP method and path, the TestClient SHALL return a TestResponse with a valid status_code (100-599), headers dictionary, and body bytes.

**Validates: Requirements 5.1, 5.2, 5.3**

### Property 2: Test Assertion Error Messages

*For any* assertion failure, the assertion helper SHALL raise an AssertionError with a message containing both the expected and actual values.

**Validates: Requirements 7.7**

### Property 3: Debug Page Security Boundary

*For any* exception in production mode (debug=False), the error response SHALL NOT contain stack traces, local variables, or internal file paths.

**Validates: Requirements 8.8, 10.2**

### Property 4: CLI Exit Code Consistency

*For any* CLI command execution, the exit code SHALL be 0 if and only if the command completed successfully without errors.

**Validates: Requirements 1.8**

### Property 5: Auto-Reload File Exclusion

*For any* file path matching an exclude pattern, the FileWatcher SHALL NOT trigger a reload callback when that file changes.

**Validates: Requirements 4.4**

### Property 6: Request Inspector Size Limits

*For any* captured request with body size exceeding max_body_size, the RequestInfo SHALL have body_truncated=True and body containing at most max_body_size bytes.

**Validates: Requirements 11.4**

### Property 7: Cookie Persistence Across Requests

*For any* sequence of TestClient requests where a response sets a cookie, subsequent requests SHALL include that cookie in the request headers.

**Validates: Requirements 5.8**

### Property 8: Configuration Precedence

*For any* configuration option, command-line arguments SHALL take precedence over environment variables, which SHALL take precedence over config file values.

**Validates: Requirements 1.5, 1.6**

## Error Handling

### CLI Error Handling

- Invalid command arguments: Display usage help and exit with `EXIT_USAGE_ERROR`
- Configuration file not found: Use defaults and log warning
- Configuration parse error: Display error and exit with `EXIT_CONFIG_ERROR`
- Port already in use: Display error with suggestion and exit with `EXIT_ERROR`
- File generation conflict: Prompt for overwrite or exit with `EXIT_ERROR`

### Development Server Error Handling

- Syntax error during reload: Display error, continue watching for fixes
- Import error during reload: Display error, continue watching for fixes
- Unhandled exception in handler: Display debug page (debug mode) or generic error (production)
- File watcher error: Log warning, continue serving

### Test Client Error Handling

- Application raises exception: Propagate to test for assertion
- Invalid JSON in response: Raise `ValueError` when accessing `.json` property
- Connection error: Should not occur (in-process), raise `RuntimeError` if it does

## Testing Strategy

### Unit Tests

Unit tests should cover:
- CLI argument parsing and validation
- Configuration loading and merging
- File watcher pattern matching
- Request logger formatting
- Test assertion helpers
- Error page rendering (without interactive debugger)

### Property-Based Tests

Property tests should verify:
- TestClient returns valid responses for all HTTP methods
- Assertion helpers provide informative error messages
- Debug pages don't leak sensitive info in production mode
- CLI exit codes are consistent with command success/failure
- File watcher correctly excludes patterns
- Request inspector respects size limits
- Cookies persist across TestClient requests
- Configuration precedence is maintained

### Integration Tests

Integration tests should cover:
- Full CLI command execution
- Development server startup and request handling
- Auto-reload triggering on file changes
- Test fixtures with testbase framework
- Debug page rendering with real exceptions

### Test Configuration

- Use testbase framework per repository conventions
- Test files located at `source/testroots/ccai/tests/singlehost/webworks/devexp/`
- Property tests should run minimum 100 iterations
- Each property test must reference its design document property
