"""
    ASGI Layer package.
    
    This package provides the Asynchronous Server Gateway Interface (ASGI)
    application interface that enables the web framework to communicate with
    ASGI-compliant web servers.
"""

from automojo.webworks.asgi.scopeparser import ScopeParser
from automojo.webworks.asgi.bodyreader import BodyReader, UploadedFile
from automojo.webworks.asgi.responsesender import ResponseSender
from automojo.webworks.asgi.httphandler import HTTPHandler
from automojo.webworks.asgi.websockethandler import WebSocketHandler, WebSocketConnection
from automojo.webworks.asgi.errorhandler import ErrorHandler, ErrorResponse, HTTPException
from automojo.webworks.asgi.ssehandler import SSEHandler, SSEEvent
from automojo.webworks.asgi.backgroundtasks import BackgroundTasks
from automojo.webworks.asgi.lifespanhandler import LifespanHandler
from automojo.webworks.asgi.application import (
    ASGIApplication,
    UnknownScopeTypeError,
    get_asgi_application,
    create_asgi_application,
    reset_singleton_application,
    get_application_variable,
)
from automojo.webworks.asgi.constants import (
    SCOPE_REQUEST,
    SCOPE_ROUTE,
    SCOPE_PATH_PARAMS,
    SCOPE_ERROR,
    SCOPE_DEBUG,
    WS_CLOSE_NORMAL,
    WS_CLOSE_GOING_AWAY,
    WS_CLOSE_PROTOCOL_ERROR,
    WS_CLOSE_UNSUPPORTED_DATA,
    WS_CLOSE_INTERNAL_ERROR,
)
from automojo.webworks.asgi.exceptions import (
    ASGIError,
    BadRequestBody,
    ClientDisconnected,
    RequestEntityTooLarge,
    WebSocketError,
    LifespanError,
    StartupError,
    ShutdownError,
)


__all__ = [
    "ASGIApplication",
    "UnknownScopeTypeError",
    "get_asgi_application",
    "create_asgi_application",
    "reset_singleton_application",
    "get_application_variable",
    "ScopeParser",
    "BodyReader",
    "UploadedFile",
    "ResponseSender",
    "HTTPHandler",
    "WebSocketHandler",
    "WebSocketConnection",
    "ErrorHandler",
    "ErrorResponse",
    "HTTPException",
    "SSEHandler",
    "SSEEvent",
    "BackgroundTasks",
    "LifespanHandler",
    "SCOPE_REQUEST",
    "SCOPE_ROUTE",
    "SCOPE_PATH_PARAMS",
    "SCOPE_ERROR",
    "SCOPE_DEBUG",
    "WS_CLOSE_NORMAL",
    "WS_CLOSE_GOING_AWAY",
    "WS_CLOSE_PROTOCOL_ERROR",
    "WS_CLOSE_UNSUPPORTED_DATA",
    "WS_CLOSE_INTERNAL_ERROR",
    "ASGIError",
    "BadRequestBody",
    "ClientDisconnected",
    "RequestEntityTooLarge",
    "WebSocketError",
    "LifespanError",
    "StartupError",
    "ShutdownError",
]
