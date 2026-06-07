"""
    Constants for the WSGI layer.
    
    This module contains HTTP status codes, reason phrases, and framework-specific
    environ keys used throughout the WSGI layer implementation.
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


# Framework-specific environ keys
ENVIRON_REQUEST: str = "webworks.request"
ENVIRON_ROUTE: str = "webworks.route"
ENVIRON_PATH_PARAMS: str = "webworks.path_params"
ENVIRON_ERROR: str = "webworks.error"
ENVIRON_DEBUG: str = "webworks.debug"
