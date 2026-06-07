"""
    Constants for the ASGI layer.
    
    This module contains ASGI-specific constants including scope keys,
    message types, and framework-specific scope extensions.
"""

from typing import Dict


# Standard HTTP status codes and reason phrases
HTTP_STATUS_PHRASES: Dict[int, str] = {
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


# Framework-specific scope keys
SCOPE_REQUEST: str = "webworks.request"
SCOPE_ROUTE: str = "webworks.route"
SCOPE_PATH_PARAMS: str = "webworks.path_params"
SCOPE_ERROR: str = "webworks.error"
SCOPE_DEBUG: str = "webworks.debug"
SCOPE_STATE: str = "state"  # Standard ASGI state key


# ASGI scope types
SCOPE_TYPE_HTTP: str = "http"
SCOPE_TYPE_WEBSOCKET: str = "websocket"
SCOPE_TYPE_LIFESPAN: str = "lifespan"


# ASGI message types - HTTP
MESSAGE_HTTP_REQUEST: str = "http.request"
MESSAGE_HTTP_RESPONSE_START: str = "http.response.start"
MESSAGE_HTTP_RESPONSE_BODY: str = "http.response.body"
MESSAGE_HTTP_DISCONNECT: str = "http.disconnect"


# ASGI message types - WebSocket
MESSAGE_WEBSOCKET_CONNECT: str = "websocket.connect"
MESSAGE_WEBSOCKET_ACCEPT: str = "websocket.accept"
MESSAGE_WEBSOCKET_RECEIVE: str = "websocket.receive"
MESSAGE_WEBSOCKET_SEND: str = "websocket.send"
MESSAGE_WEBSOCKET_DISCONNECT: str = "websocket.disconnect"
MESSAGE_WEBSOCKET_CLOSE: str = "websocket.close"


# ASGI message types - Lifespan
MESSAGE_LIFESPAN_STARTUP: str = "lifespan.startup"
MESSAGE_LIFESPAN_STARTUP_COMPLETE: str = "lifespan.startup.complete"
MESSAGE_LIFESPAN_STARTUP_FAILED: str = "lifespan.startup.failed"
MESSAGE_LIFESPAN_SHUTDOWN: str = "lifespan.shutdown"
MESSAGE_LIFESPAN_SHUTDOWN_COMPLETE: str = "lifespan.shutdown.complete"
MESSAGE_LIFESPAN_SHUTDOWN_FAILED: str = "lifespan.shutdown.failed"


# WebSocket close codes
WS_CLOSE_NORMAL: int = 1000
WS_CLOSE_GOING_AWAY: int = 1001
WS_CLOSE_PROTOCOL_ERROR: int = 1002
WS_CLOSE_UNSUPPORTED_DATA: int = 1003
WS_CLOSE_NO_STATUS: int = 1005
WS_CLOSE_ABNORMAL: int = 1006
WS_CLOSE_INVALID_DATA: int = 1007
WS_CLOSE_POLICY_VIOLATION: int = 1008
WS_CLOSE_MESSAGE_TOO_BIG: int = 1009
WS_CLOSE_MANDATORY_EXTENSION: int = 1010
WS_CLOSE_INTERNAL_ERROR: int = 1011
WS_CLOSE_SERVICE_RESTART: int = 1012
WS_CLOSE_TRY_AGAIN_LATER: int = 1013
