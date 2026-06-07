# Design Document: Router and Request Handling

## Overview

This design document describes the architecture and implementation approach for the Router and Request Handling feature. The feature provides the core routing infrastructure that matches incoming HTTP requests to registered endpoint handlers, manages request/response primitives, and orchestrates middleware pipelines for cross-cutting concerns.

The design follows a layered architecture where the Router builds an efficient URL matching tree from EndpointDescriptors, the Dispatcher orchestrates the request flow through middleware and handlers, and Request/Response primitives provide clean abstractions over WSGI/ASGI details.

Key design principles:
- Clean abstractions: Request/Response hide WSGI/ASGI complexity
- Composable middleware: Cross-cutting concerns are reusable components
- Efficient matching: URL tree enables O(path_depth) routing
- Type-safe parameters: Converters validate and transform path segments
- Fail-fast errors: Invalid routes are detected at registration time

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Request Flow                                         │
│                                                                              │
│  WSGI/ASGI Request                                                          │
│         │                                                                    │
│         ▼                                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                         Request                                      │    │
│  │  method, path, query_params, headers, body, cookies, url            │    │
│  │  json(), form(), path_params                                        │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│         │                                                                    │
│         ▼                                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                        Dispatcher                                    │    │
│  │  - router: Router                                                   │    │
│  │  - pipeline: MiddlewarePipeline                                     │    │
│  │  - dispatch(request) -> Response                                    │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│         │                                                                    │
│         ├──────────────────────┐                                            │
│         ▼                      ▼                                            │
│  ┌─────────────┐      ┌─────────────────────────────────────────────┐      │
│  │   Router    │      │           MiddlewarePipeline                │      │
│  │             │      │  ┌─────┐  ┌─────┐  ┌─────┐  ┌─────────┐    │      │
│  │ match(req)  │      │  │ MW1 │→ │ MW2 │→ │ MW3 │→ │ Handler │    │      │
│  │     │       │      │  └─────┘  └─────┘  └─────┘  └─────────┘    │      │
│  │     ▼       │      └─────────────────────────────────────────────┘      │
│  │ RouteMatch  │                                                            │
│  └─────────────┘                                                            │
│         │                                                                    │
│         ▼                                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                         Response                                     │    │
│  │  status_code, headers, body                                         │    │
│  │  set_header(), set_cookie(), to_wsgi(), to_asgi()                  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                         Router URL Tree                                      │
│                                                                              │
│                              [root]                                          │
│                                │                                             │
│                 ┌──────────────┼──────────────┐                             │
│                 ▼              ▼              ▼                             │
│              [api]         [users]        [static]                          │
│                │              │              │                               │
│         ┌──────┼──────┐      │              │                               │
│         ▼      ▼      ▼      ▼              ▼                               │
│       [v1]   [v2]  [health] [{id}]      [{path:path}]                       │
│         │      │              │                                              │
│         ▼      ▼              ▼                                              │
│      [users] [users]      [profile]                                         │
│                                                                              │
│  Static segments: exact match                                               │
│  Parameter segments: {name} or {name:converter}                             │
│  Wildcard segments: {name:path} matches remaining path                      │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                    Middleware Execution Flow                                 │
│                                                                              │
│  Request ──▶ MW1.before ──▶ MW2.before ──▶ MW3.before ──▶ Handler          │
│                                                              │               │
│  Response ◀── MW1.after ◀── MW2.after ◀── MW3.after ◀───────┘              │
│                                                                              │
│  Each middleware:                                                            │
│  def __call__(request, call_next):                                          │
│      # before: modify request, check auth, log, etc.                        │
│      response = call_next(request)                                          │
│      # after: modify response, add headers, log, etc.                       │
│      return response                                                         │
│                                                                              │
│  Short-circuit (e.g., auth failure):                                        │
│  def __call__(request, call_next):                                          │
│      if not authenticated(request):                                         │
│          return Response(401, body="Unauthorized")  # skip call_next       │
│      return call_next(request)                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Components and Interfaces

### Request Class

```python
class Request:
    """
    Abstraction over WSGI/ASGI request providing clean access to
    request data without exposing raw protocol details.
    """
    
    def __init__(
        self,
        method: str,
        path: str,
        query_string: bytes = b"",
        headers: Optional[Dict[str, str]] = None,
        body: bytes = b"",
        scheme: str = "http",
        host: str = "localhost",
        port: int = 80
    ):
        """
        Construct a Request from components.
        
        For WSGI/ASGI construction, use from_wsgi() or from_asgi().
        """
        pass
    
    @classmethod
    def from_wsgi(cls, environ: Dict[str, Any]) -> "Request":
        """Construct Request from WSGI environ dict."""
        pass
    
    @classmethod
    def from_asgi(cls, scope: Dict[str, Any], body: bytes = b"") -> "Request":
        """Construct Request from ASGI scope dict."""
        pass
    
    @property
    def method(self) -> str:
        """HTTP method (GET, POST, etc.)."""
        pass
    
    @property
    def path(self) -> str:
        """Request path without query string."""
        pass
    
    @property
    def query_params(self) -> "QueryParams":
        """Query parameters as dict-like object."""
        pass
    
    @property
    def headers(self) -> "Headers":
        """Request headers as case-insensitive dict-like object."""
        pass
    
    @property
    def body(self) -> bytes:
        """Raw request body as bytes."""
        pass
    
    def json(self) -> Any:
        """Parse body as JSON and return Python object."""
        pass
    
    def form(self) -> Dict[str, str]:
        """Parse body as form-encoded data and return dict."""
        pass
    
    @property
    def path_params(self) -> Dict[str, Any]:
        """Path parameters extracted during routing."""
        pass
    
    @path_params.setter
    def path_params(self, value: Dict[str, Any]) -> None:
        """Set path parameters (called by dispatcher after routing)."""
        pass
    
    @property
    def cookies(self) -> Dict[str, str]:
        """Request cookies parsed from Cookie header."""
        pass
    
    @property
    def url(self) -> str:
        """Full request URL including scheme, host, path, and query."""
        pass
```

### Response Class

```python
class Response:
    """
    HTTP response abstraction for building responses with status,
    headers, and body content.
    """
    
    def __init__(
        self,
        status_code: int = 200,
        headers: Optional[Dict[str, str]] = None,
        body: bytes = b""
    ):
        """
        Construct a Response.
        
        Args:
            status_code: HTTP status code (default 200).
            headers: Response headers dict.
            body: Response body as bytes.
        """
        pass
    
    def set_header(self, name: str, value: str) -> None:
        """Set a response header."""
        pass
    
    def set_cookie(
        self,
        name: str,
        value: str,
        max_age: Optional[int] = None,
        expires: Optional[str] = None,
        path: str = "/",
        domain: Optional[str] = None,
        secure: bool = False,
        httponly: bool = False,
        samesite: Optional[str] = None
    ) -> None:
        """Set a response cookie."""
        pass
    
    def delete_cookie(self, name: str, path: str = "/", domain: Optional[str] = None) -> None:
        """Delete a cookie by setting it to expire."""
        pass
    
    def to_wsgi(self) -> Tuple[str, List[Tuple[str, str]], Iterable[bytes]]:
        """Convert to WSGI response format (status, headers, body)."""
        pass
    
    def to_asgi(self) -> Dict[str, Any]:
        """Convert to ASGI response events."""
        pass


class JSONResponse(Response):
    """Response with JSON body and automatic Content-Type header."""
    
    def __init__(
        self,
        content: Any,
        status_code: int = 200,
        headers: Optional[Dict[str, str]] = None
    ):
        """
        Construct a JSON response.
        
        Args:
            content: Python object to serialize as JSON.
            status_code: HTTP status code.
            headers: Additional headers.
        """
        pass


class HTMLResponse(Response):
    """Response with HTML body and automatic Content-Type header."""
    
    def __init__(
        self,
        content: str,
        status_code: int = 200,
        headers: Optional[Dict[str, str]] = None
    ):
        pass


class RedirectResponse(Response):
    """HTTP redirect response."""
    
    def __init__(
        self,
        url: str,
        status_code: int = 307,
        headers: Optional[Dict[str, str]] = None
    ):
        pass


class StreamingResponse(Response):
    """Response that streams body content."""
    
    def __init__(
        self,
        content: Iterable[bytes],
        status_code: int = 200,
        headers: Optional[Dict[str, str]] = None,
        media_type: Optional[str] = None
    ):
        pass
```

### Router Class

```python
class Router:
    """
    URL router that matches requests to endpoint handlers.
    Builds an efficient URL tree from registered descriptors.
    """
    
    def __init__(
        self,
        strict_slashes: bool = True,
        case_sensitive: bool = True,
        redirect_slashes: bool = False
    ):
        """
        Construct a Router.
        
        Args:
            strict_slashes: If True, /path and /path/ are different routes.
            case_sensitive: If True, paths are matched case-sensitively.
            redirect_slashes: If True, redirect on trailing slash mismatch.
        """
        pass
    
    def add_endpoint(self, descriptor: "EndpointDescriptor") -> None:
        """
        Add an endpoint descriptor to the router.
        
        Args:
            descriptor: EndpointDescriptor from endpoint-abstractions.
        
        Raises:
            RoutingError: If route conflicts with existing registration.
        """
        pass
    
    def load_from_registry(self, registry: "EndpointRegistry") -> None:
        """
        Bulk-load all descriptors from an EndpointRegistry.
        
        Args:
            registry: EndpointRegistry to load from.
        """
        pass
    
    def match(self, request: Request) -> Optional["RouteMatch"]:
        """
        Match a request to a registered route.
        
        Args:
            request: The incoming Request.
        
        Returns:
            RouteMatch if found, None otherwise.
        """
        pass
```

### RouteMatch Dataclass

```python
@dataclass
class RouteMatch:
    """
    Result of a successful route match containing all information
    needed to dispatch the request.
    """
    
    handler: Callable
    path_params: Dict[str, Any]
    descriptor: "EndpointDescriptor"
    matched_path: str


### Matcher Class

```python
class Matcher:
    """
    URL pattern matcher supporting static, parameterized, and
    wildcard path segments.
    """
    
    def __init__(self, pattern: str, converters: Optional[Dict[str, "Converter"]] = None):
        """
        Construct a Matcher from a URL pattern.
        
        Args:
            pattern: URL pattern (e.g., "/users/{id:int}").
            converters: Custom converters to use.
        """
        pass
    
    def match(self, path: str) -> Optional[Dict[str, Any]]:
        """
        Match a path against this pattern.
        
        Args:
            path: URL path to match.
        
        Returns:
            Dict of extracted parameters if match, None otherwise.
        """
        pass
    
    @property
    def specificity(self) -> int:
        """
        Return specificity score for route precedence.
        Higher = more specific (static > param > wildcard).
        """
        pass
```

### Converter Protocol

```python
class Converter(Protocol):
    """
    Protocol for path parameter converters that validate and
    transform path segments.
    """
    
    regex: str  # Regex pattern to match
    
    def convert(self, value: str) -> Any:
        """
        Convert a matched string value to the target type.
        
        Args:
            value: String value from path segment.
        
        Returns:
            Converted value.
        
        Raises:
            ValueError: If conversion fails.
        """
        ...


class StringConverter:
    """Matches any non-empty string segment."""
    regex = r"[^/]+"
    
    def convert(self, value: str) -> str:
        return value


class IntConverter:
    """Matches integer values and converts to int."""
    regex = r"\d+"
    
    def convert(self, value: str) -> int:
        return int(value)


class FloatConverter:
    """Matches numeric values and converts to float."""
    regex = r"\d+\.?\d*"
    
    def convert(self, value: str) -> float:
        return float(value)


class UUIDConverter:
    """Matches UUID strings and converts to UUID."""
    regex = r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
    
    def convert(self, value: str) -> UUID:
        return UUID(value)


class PathConverter:
    """Matches any remaining path including slashes."""
    regex = r".+"
    
    def convert(self, value: str) -> str:
        return value
```

### Middleware Protocol

```python
class Middleware(Protocol):
    """
    Protocol for middleware components that wrap request handling.
    """
    
    name: str  # Optional name for positional insertion/removal
    
    def __call__(
        self,
        request: Request,
        call_next: Callable[[Request], Response]
    ) -> Response:
        """
        Process a request, optionally calling the next handler.
        
        Args:
            request: The incoming Request.
            call_next: Callable to invoke next middleware/handler.
        
        Returns:
            Response from handler or short-circuit response.
        """
        ...


class AsyncMiddleware(Protocol):
    """
    Protocol for async middleware components.
    """
    
    name: str
    
    async def __call__(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        ...
```

### MiddlewarePipeline Class

```python
class MiddlewarePipeline:
    """
    Ordered chain of middleware components that process requests
    before and after the endpoint handler.
    """
    
    def __init__(self):
        """Construct an empty middleware pipeline."""
        pass
    
    def add(
        self,
        middleware: Middleware,
        name: Optional[str] = None,
        position: str = "end"
    ) -> None:
        """
        Add middleware to the pipeline.
        
        Args:
            middleware: Middleware component to add.
            name: Optional name for later reference.
            position: Where to insert:
                - "start": Beginning of pipeline
                - "end": End of pipeline (default)
                - "before:<name>": Before named middleware
                - "after:<name>": After named middleware
        
        Raises:
            ValueError: If position references unknown middleware.
        """
        pass
    
    def remove(self, name: str) -> None:
        """
        Remove middleware by name.
        
        Args:
            name: Name of middleware to remove.
        
        Raises:
            KeyError: If name not found.
        """
        pass
    
    def execute(
        self,
        request: Request,
        handler: Callable[[Request], Response]
    ) -> Response:
        """
        Execute the pipeline with the given handler as final callable.
        
        Args:
            request: The incoming Request.
            handler: The endpoint handler to wrap.
        
        Returns:
            Response from the pipeline.
        """
        pass
    
    async def execute_async(
        self,
        request: Request,
        handler: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """
        Execute the pipeline asynchronously.
        
        Args:
            request: The incoming Request.
            handler: The async endpoint handler to wrap.
        
        Returns:
            Response from the pipeline.
        """
        pass
```

### Dispatcher Class

```python
class Dispatcher:
    """
    Orchestrates routing and middleware execution for incoming requests.
    """
    
    def __init__(
        self,
        router: Router,
        pipeline: MiddlewarePipeline,
        debug: bool = False,
        error_format: str = "json"
    ):
        """
        Construct a Dispatcher.
        
        Args:
            router: Router for URL matching.
            pipeline: MiddlewarePipeline for request processing.
            debug: If True, include stack traces in error responses.
            error_format: Format for error responses ("json", "html", "text").
        """
        pass
    
    def dispatch(self, request: Request) -> Response:
        """
        Dispatch a request through routing and middleware.
        
        Args:
            request: The incoming Request.
        
        Returns:
            Response from handler or error response.
        """
        pass
    
    async def dispatch_async(self, request: Request) -> Response:
        """
        Dispatch a request asynchronously.
        
        Args:
            request: The incoming Request.
        
        Returns:
            Response from handler or error response.
        """
        pass
```

### Exception Classes

```python
class HTTPException(Exception):
    """
    Base exception for HTTP errors that should be converted to responses.
    """
    
    def __init__(
        self,
        status_code: int,
        detail: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None
    ):
        self.status_code = status_code
        self.detail = detail
        self.headers = headers or {}
        super().__init__(detail)


class NotFound(HTTPException):
    """404 Not Found."""
    def __init__(self, detail: str = "Not Found"):
        super().__init__(404, detail)


class BadRequest(HTTPException):
    """400 Bad Request."""
    def __init__(self, detail: str = "Bad Request"):
        super().__init__(400, detail)


class Unauthorized(HTTPException):
    """401 Unauthorized."""
    def __init__(self, detail: str = "Unauthorized"):
        super().__init__(401, detail)


class Forbidden(HTTPException):
    """403 Forbidden."""
    def __init__(self, detail: str = "Forbidden"):
        super().__init__(403, detail)


class MethodNotAllowed(HTTPException):
    """405 Method Not Allowed."""
    def __init__(self, detail: str = "Method Not Allowed", allowed: Optional[List[str]] = None):
        headers = {"Allow": ", ".join(allowed)} if allowed else {}
        super().__init__(405, detail, headers)


class RoutingError(Exception):
    """Raised when route registration fails."""
    
    def __init__(self, message: str, path: Optional[str] = None, method: Optional[str] = None):
        self.path = path
        self.method = method
        super().__init__(message)
```

### Helper Classes

```python
class QueryParams:
    """
    Dict-like object for query parameters supporting multi-value keys.
    """
    
    def __init__(self, query_string: bytes):
        """Parse query string into parameters."""
        pass
    
    def __getitem__(self, key: str) -> str:
        """Get first value for key."""
        pass
    
    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get first value for key with default."""
        pass
    
    def getlist(self, key: str) -> List[str]:
        """Get all values for key."""
        pass
    
    def keys(self) -> Iterable[str]:
        """Return all keys."""
        pass
    
    def items(self) -> Iterable[Tuple[str, str]]:
        """Return all key-value pairs (first value per key)."""
        pass


class Headers:
    """
    Case-insensitive dict-like object for HTTP headers.
    """
    
    def __init__(self, headers: Optional[Dict[str, str]] = None):
        """Initialize with optional headers dict."""
        pass
    
    def __getitem__(self, key: str) -> str:
        """Get header value (case-insensitive)."""
        pass
    
    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get header value with default (case-insensitive)."""
        pass
    
    def __contains__(self, key: str) -> bool:
        """Check if header exists (case-insensitive)."""
        pass
```

## Data Models

### Converter Registry

```python
# Global converter registry with built-in converters
CONVERTERS: Dict[str, Converter] = {
    "str": StringConverter(),
    "int": IntConverter(),
    "float": FloatConverter(),
    "uuid": UUIDConverter(),
    "path": PathConverter(),
}

def register_converter(name: str, converter: Converter) -> None:
    """Register a custom converter."""
    CONVERTERS[name] = converter
```

### URL Tree Node

```python
@dataclass
class URLNode:
    """
    Node in the URL matching tree.
    """
    
    segment: str  # Static segment or parameter pattern
    is_param: bool = False
    param_name: Optional[str] = None
    converter: Optional[Converter] = None
    children: Dict[str, "URLNode"] = field(default_factory=dict)
    handlers: Dict[str, Tuple[Callable, "EndpointDescriptor"]] = field(default_factory=dict)
    # handlers keyed by HTTP method
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Route Matching Correctness

*For any* registered route with path P and method M, and any request with matching path P and method M, the Router SHALL return a RouteMatch containing the correct handler and descriptor. *For any* request with non-matching path or method, the Router SHALL return None.

**Validates: Requirements 1.3, 1.4, 1.5, 1.6**

### Property 2: Path Parameter Extraction

*For any* route with parameterized segments (e.g., `/users/{id}`) and any matching request path, the extracted path_params dict SHALL contain all parameter names as keys with their corresponding path segment values, converted to the correct type by the specified converter.

**Validates: Requirements 2.2, 2.3, 2.4**

### Property 3: Route Precedence

*For any* set of registered routes where multiple could match a given path, the Router SHALL prefer more specific routes (static > parameterized > wildcard). *For any* routes with equal specificity, the Router SHALL use registration order as tiebreaker, returning the first registered route.

**Validates: Requirements 2.6, 2.7**

### Property 4: Request Query/Form Parsing

*For any* valid query string or form-encoded body, parsing SHALL produce a dict where each key maps to its value(s), and the original data can be reconstructed from the parsed result (round-trip for single-value keys).

**Validates: Requirements 3.3, 3.7**

### Property 5: Request JSON Round-Trip

*For any* valid JSON body, calling `request.json()` SHALL return a Python object that, when serialized back to JSON, produces equivalent JSON content.

**Validates: Requirements 3.6**

### Property 6: Request Header Case-Insensitivity

*For any* header name in any case variation (e.g., "Content-Type", "content-type", "CONTENT-TYPE"), accessing `request.headers[name]` SHALL return the same value.

**Validates: Requirements 3.4**

### Property 7: Response Format Conversion

*For any* Response object with valid status_code, headers, and body, calling `to_wsgi()` SHALL produce a valid WSGI response tuple, and calling `to_asgi()` SHALL produce valid ASGI response events. The status code, headers, and body SHALL be preserved in both conversions.

**Validates: Requirements 4.5, 4.6**

### Property 8: JSONResponse Serialization Round-Trip

*For any* Python object that is JSON-serializable, constructing a JSONResponse and parsing its body as JSON SHALL produce an equivalent object.

**Validates: Requirements 4.7**

### Property 9: Middleware Pipeline Execution Order

*For any* middleware pipeline with N middleware components, execution SHALL proceed in order: MW1.before → MW2.before → ... → MWN.before → handler → MWN.after → ... → MW2.after → MW1.after. Each middleware SHALL receive the request (possibly modified by previous middleware) and return a response (possibly modified by subsequent middleware).

**Validates: Requirements 5.2, 5.3, 5.4, 6.8**

### Property 10: Middleware Short-Circuit

*For any* middleware that returns a response without calling `call_next`, subsequent middleware and the handler SHALL NOT be executed, and the returned response SHALL be passed back through preceding middleware.

**Validates: Requirements 5.5**

### Property 11: Middleware Positioning

*For any* middleware added with position="start", it SHALL execute before all previously added middleware. *For any* middleware added with position="before:X", it SHALL execute immediately before middleware X. *For any* middleware added with position="after:X", it SHALL execute immediately after middleware X.

**Validates: Requirements 6.3, 6.4, 6.5, 6.6**

### Property 12: Dispatcher Error Handling

*For any* request that matches no route, the Dispatcher SHALL return a 404 response. *For any* HTTPException raised by a handler, the Dispatcher SHALL return a response with the exception's status_code. *For any* unhandled exception, the Dispatcher SHALL return a 500 response.

**Validates: Requirements 8.6, 8.7, 9.2, 9.5**

### Property 13: Path Parameter Conversion

*For any* typed path parameter with converter C, if the path segment matches C's regex and C.convert() succeeds, the converted value SHALL be of the correct type. If the segment doesn't match or conversion fails, the route SHALL be treated as non-matching.

**Validates: Requirements 10.2, 10.3, 10.4, 10.5, 10.6, 10.7**

### Property 14: Router Configuration Behavior

*For any* Router with `strict_slashes=True`, paths `/foo` and `/foo/` SHALL be treated as different routes. *For any* Router with `strict_slashes=False`, both variants SHALL match the same handler. *For any* Router with `case_sensitive=False`, paths `/Foo` and `/foo` SHALL match the same handler.

**Validates: Requirements 11.2, 11.3, 11.5**

## Error Handling

### RoutingError

Raised when route registration fails:

```python
class RoutingError(Exception):
    """Raised when route registration or matching fails."""
    
    def __init__(
        self,
        message: str,
        path: Optional[str] = None,
        method: Optional[str] = None,
        existing_handler: Optional[Callable] = None
    ):
        self.path = path
        self.method = method
        self.existing_handler = existing_handler
        super().__init__(message)
```

Common scenarios:
- Duplicate route registration (same path + method)
- Invalid path pattern syntax
- Unknown converter name

### HTTPException Handling

The Dispatcher converts HTTPException to responses:

```python
def _handle_http_exception(self, exc: HTTPException) -> Response:
    """Convert HTTPException to appropriate response."""
    if self.error_format == "json":
        return JSONResponse(
            {"detail": exc.detail, "status_code": exc.status_code},
            status_code=exc.status_code,
            headers=exc.headers
        )
    elif self.error_format == "html":
        return HTMLResponse(
            f"<h1>{exc.status_code}</h1><p>{exc.detail}</p>",
            status_code=exc.status_code,
            headers=exc.headers
        )
    else:
        return Response(
            status_code=exc.status_code,
            body=exc.detail.encode() if exc.detail else b"",
            headers=exc.headers
        )
```

### Unhandled Exception Handling

```python
def _handle_unhandled_exception(self, exc: Exception) -> Response:
    """Handle unhandled exceptions."""
    if self.debug:
        import traceback
        detail = traceback.format_exc()
    else:
        detail = "Internal Server Error"
    
    if self.error_format == "json":
        return JSONResponse(
            {"detail": detail, "status_code": 500},
            status_code=500
        )
    else:
        return Response(status_code=500, body=detail.encode())
```

## Testing Strategy

### Unit Tests

Unit tests should cover:

1. **Request Construction Tests**
   - Verify Request construction from components
   - Verify Request.from_wsgi() parses WSGI environ correctly
   - Verify Request.from_asgi() parses ASGI scope correctly
   - Verify property accessors return correct values

2. **Response Construction Tests**
   - Verify Response construction with status, headers, body
   - Verify set_header() and set_cookie() methods
   - Verify specialized response classes (JSONResponse, HTMLResponse, etc.)

3. **Router Registration Tests**
   - Verify add_endpoint() accepts valid descriptors
   - Verify load_from_registry() bulk-loads descriptors
   - Verify RoutingError on duplicate registration

4. **Matcher Pattern Tests**
   - Verify static path matching
   - Verify parameterized path matching
   - Verify typed parameter conversion
   - Verify wildcard matching

5. **Middleware Pipeline Tests**
   - Verify add() with different positions
   - Verify remove() by name
   - Verify execution order

6. **Dispatcher Tests**
   - Verify dispatch() routes and executes handler
   - Verify 404 on no match
   - Verify HTTPException handling
   - Verify unhandled exception handling

7. **Exception Tests**
   - Verify HTTPException subclasses have correct status codes
   - Verify RoutingError contains path/method info

### Property-Based Tests

Property-based tests should use the `testbase` framework with minimum 100 iterations per property. Each test should be tagged with the property it validates.

**Testing Framework**: testbase (as specified in AGENTS.md)

**Property Test Configuration**:
- Minimum iterations: 100
- Tag format: `Feature: router-request-handling, Property N: <property_text>`

**Generator Requirements**:
- Generate valid URL paths with static and parameterized segments
- Generate valid HTTP methods
- Generate valid query strings and form bodies
- Generate valid JSON bodies
- Generate valid header dicts with various case combinations
- Generate middleware chains with different orderings
- Generate route sets with varying specificity

### Test Organization

Following the repository conventions from AGENTS.md:

```
source/testroots/ccai/tests/singlehost/webworks/
├── routing/
│   ├── test_request.py           # Request class tests
│   ├── test_response.py          # Response class tests
│   ├── test_router.py            # Router class tests
│   ├── test_matcher.py           # Matcher class tests
│   ├── test_converters.py        # Converter tests
│   ├── test_middleware.py        # Middleware tests
│   ├── test_pipeline.py          # MiddlewarePipeline tests
│   ├── test_dispatcher.py        # Dispatcher tests
│   └── test_exceptions.py        # Exception tests
```

### Integration Points

- Integration with EndpointRegistry from endpoint-abstractions feature
- Integration with EndpointDescriptor for handler metadata
- Integration with WSGI/ASGI application interfaces
- Integration with AccessPolicy for security enforcement in middleware
