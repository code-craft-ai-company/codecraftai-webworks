"""
    Router and Request Handling package.
    
    This package provides the core routing infrastructure that matches incoming
    HTTP requests to registered endpoint handlers, manages request/response
    primitives, and orchestrates middleware pipelines for cross-cutting concerns.
"""

from automojo.webworks.routing.queryparams import QueryParams
from automojo.webworks.routing.headers import Headers
from automojo.webworks.routing.request import Request
from automojo.webworks.routing.response import (
    Response,
    JSONResponse,
    HTMLResponse,
    RedirectResponse,
    StreamingResponse,
)
from automojo.webworks.routing.converters import (
    Converter,
    StringConverter,
    IntConverter,
    FloatConverter,
    UUIDConverter,
    PathConverter,
    CONVERTERS,
    register_converter,
    get_converter,
)
from automojo.webworks.routing.matcher import Matcher, Segment, SegmentType
from automojo.webworks.routing.router import (
    Router,
    RouteMatch,
    URLNode,
)
from automojo.webworks.routing.middleware import (
    Middleware,
    AsyncMiddleware,
    MiddlewareEntry,
    MiddlewarePipeline,
)
from automojo.webworks.routing.middlewarecontext import MiddlewareContext
from automojo.webworks.routing.middlewareregistry import MiddlewareRegistry
from automojo.webworks.routing.exceptions import (
    HTTPException,
    NotFound,
    BadRequest,
    Unauthorized,
    Forbidden,
    MethodNotAllowed,
    RoutingError,
)
from automojo.webworks.routing.dispatcher import Dispatcher


__all__ = [
    "QueryParams",
    "Headers",
    "Request",
    # Response
    "Response",
    "JSONResponse",
    "HTMLResponse",
    "RedirectResponse",
    "StreamingResponse",
    # Converters
    "Converter",
    "StringConverter",
    "IntConverter",
    "FloatConverter",
    "UUIDConverter",
    "PathConverter",
    "CONVERTERS",
    "register_converter",
    "get_converter",
    # Matcher
    "Matcher",
    "Segment",
    "SegmentType",
    # Router
    "Router",
    "RouteMatch",
    "RoutingError",
    "URLNode",
    # Middleware
    "Middleware",
    "AsyncMiddleware",
    "MiddlewareEntry",
    "MiddlewarePipeline",
    "MiddlewareContext",
    "MiddlewareRegistry",
    # Exceptions
    "HTTPException",
    "NotFound",
    "BadRequest",
    "Unauthorized",
    "Forbidden",
    "MethodNotAllowed",
    # Dispatcher
    "Dispatcher",
]
