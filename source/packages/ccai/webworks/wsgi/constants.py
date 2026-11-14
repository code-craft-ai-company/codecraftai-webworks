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
    411: "Length Required",
    413: "Request Entity Too Large",
    414: "URI Too Long",
    415: "Unsupported Media Type",
    422: "Unprocessable Entity",
    429: "Too Many Requests",
    431: "Request Header Fields Too Large",
    500: "Internal Server Error",
    501: "Not Implemented",
    502: "Bad Gateway",
    503: "Service Unavailable",
    504: "Gateway Timeout",
    505: "HTTP Version Not Supported",
}


# Largest request body, in bytes, that is accepted when no limit is configured.
# Request bodies are held in memory, so an unlimited default lets any client
# exhaust the memory of the server. A limit of 0 turns the check off.
DEFAULT_MAX_REQUEST_BODY_SIZE: int = 16 * 1024 * 1024


# Framework-specific environ keys
ENVIRON_REQUEST: str = "webworks.request"
ENVIRON_ROUTE: str = "webworks.route"
ENVIRON_PATH_PARAMS: str = "webworks.path_params"
ENVIRON_ERROR: str = "webworks.error"
ENVIRON_DEBUG: str = "webworks.debug"
ENVIRON_REQUEST_ID: str = "webworks.request_id"

# Seconds an application is given to start its response. A server or a
# middleware sets this environ key to bound the handler time of one request;
# the ASGIBridge answers 504 Gateway Timeout when the application has not
# started its response in time.
ENVIRON_REQUEST_TIMEOUT: str = "webworks.request_timeout"

# Exit code of a worker process that could not start serving. The server
# stops when it sees it, a replacement worker would fail the same way.
WORKER_BOOT_ERROR_EXIT_CODE: int = 3
