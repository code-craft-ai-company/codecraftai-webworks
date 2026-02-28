"""
    WSGI Layer package for the webworks framework.
    
    This package provides a complete Web Server Gateway Interface (WSGI) implementation
    including both the application interface and a built-in WSGI server.
"""

from automojo.webworks.wsgi.environparser import EnvironParser
from automojo.webworks.wsgi.request import Request
from automojo.webworks.wsgi.response import Response, ResponseBuilder
from automojo.webworks.wsgi.responseiterator import ResponseIterator
from automojo.webworks.wsgi.bodyparser import RequestBodyParser, UploadedFile
from automojo.webworks.wsgi.errorhandler import ErrorHandler
from automojo.webworks.wsgi.application import (
    WSGIApplication,
    get_wsgi_application,
    create_wsgi_application,
    set_wsgi_application,
    reset_wsgi_application,
)
from automojo.webworks.wsgi.middleware import WSGIMiddlewareWrapper
from automojo.webworks.wsgi.constants import (
    HTTP_STATUS_PHRASES,
    ENVIRON_REQUEST,
    ENVIRON_ROUTE,
    ENVIRON_PATH_PARAMS,
    ENVIRON_ERROR,
    ENVIRON_DEBUG,
)
from automojo.webworks.wsgi.exceptions import (
    WSGIError,
    HTTPException,
    RequestEntityTooLarge,
    BadRequestBody,
    RequestParseError,
    HeaderTooLarge,
    TooManyHeaders,
    RequestTimeout,
    ServerError,
    BindError,
    WorkerError,
)
from automojo.webworks.wsgi.serverconfig import (
    ServerConfig,
    ConfigurationError,
)
from automojo.webworks.wsgi.socketlistener import SocketListener
from automojo.webworks.wsgi.httpparser import HTTPParser
from automojo.webworks.wsgi.httpwriter import HTTPWriter
from automojo.webworks.wsgi.connectionmanager import ConnectionManager, ConnectionInfo
from automojo.webworks.wsgi.startresponse import StartResponse
from automojo.webworks.wsgi.worker import Worker
from automojo.webworks.wsgi.workermanager import WorkerManager, WorkerInfo
from automojo.webworks.wsgi.server import WSGIServer, run_server

__all__ = [
    "EnvironParser",
    "Request",
    "Response",
    "ResponseBuilder",
    "ResponseIterator",
    "RequestBodyParser",
    "UploadedFile",
    "ErrorHandler",
    "WSGIApplication",
    "WSGIMiddlewareWrapper",
    "get_wsgi_application",
    "create_wsgi_application",
    "set_wsgi_application",
    "reset_wsgi_application",
    "HTTP_STATUS_PHRASES",
    "ENVIRON_REQUEST",
    "ENVIRON_ROUTE",
    "ENVIRON_PATH_PARAMS",
    "ENVIRON_ERROR",
    "ENVIRON_DEBUG",
    "WSGIError",
    "HTTPException",
    "RequestEntityTooLarge",
    "BadRequestBody",
    "RequestParseError",
    "HeaderTooLarge",
    "TooManyHeaders",
    "RequestTimeout",
    "ServerError",
    "BindError",
    "WorkerError",
    "ServerConfig",
    "ConfigurationError",
    "SocketListener",
    "HTTPParser",
    "HTTPWriter",
    "ConnectionManager",
    "ConnectionInfo",
    "StartResponse",
    "Worker",
    "WorkerManager",
    "WorkerInfo",
    "WSGIServer",
    "run_server",
]
