"""
    WSGI Layer package for the webworks framework.
    
    This package provides a complete Web Server Gateway Interface (WSGI) implementation
    including both the application interface and a built-in WSGI server.
    
    A WebApplication is served over WSGI by its 'wsgi_app', an ASGIBridge that runs
    the application's ASGI pipeline. get_wsgi_application() gives external WSGI
    servers (Gunicorn, uWSGI, mod_wsgi, Waitress) the application to serve.
"""

from ccai.webworks.wsgi.environparser import EnvironParser
from ccai.webworks.routing.request import Request
from ccai.webworks.wsgi.response import Response, ResponseBuilder
from ccai.webworks.wsgi.responseiterator import ResponseIterator
from ccai.webworks.wsgi.bodyparser import RequestBodyParser, UploadedFile
from ccai.webworks.wsgi.errorhandler import ErrorHandler
from ccai.webworks.wsgi.asgibridge import ASGIBridge, is_asgi_application
from ccai.webworks.wsgi.application import (
    WSGIApplication,
    as_wsgi_application,
    get_wsgi_application,
    create_wsgi_application,
    resolve_wsgi_application,
    set_wsgi_application,
    reset_wsgi_application,
)
from ccai.webworks.wsgi.middleware import WSGIMiddlewareWrapper
from ccai.webworks.wsgi.constants import (
    DEFAULT_MAX_REQUEST_BODY_SIZE,
    HTTP_STATUS_PHRASES,
    ENVIRON_REQUEST,
    ENVIRON_ROUTE,
    ENVIRON_PATH_PARAMS,
    ENVIRON_ERROR,
    ENVIRON_DEBUG,
    ENVIRON_REQUEST_ID,
    ENVIRON_REQUEST_TIMEOUT,
    WORKER_BOOT_ERROR_EXIT_CODE,
)
from ccai.webworks.wsgi.exceptions import (
    WSGIError,
    HTTPException,
    RequestEntityTooLarge,
    BadRequestBody,
    RequestParseError,
    RequestLineTooLong,
    HeaderTooLarge,
    TooManyHeaders,
    IncompleteRequest,
    ConnectionClosed,
    InvalidResponseHeader,
    RequestTimeout,
    ServerError,
    BindError,
    WorkerError,
    WorkerBootError,
    IncompleteResponse,
)
from ccai.webworks.wsgi.serverconfig import (
    ServerConfig,
    ConfigurationError,
)
from ccai.webworks.wsgi.socketlistener import SocketListener
from ccai.webworks.wsgi.socketreader import SocketReader
from ccai.webworks.wsgi.httpparser import HTTPParser
from ccai.webworks.wsgi.httpwriter import HTTPWriter
from ccai.webworks.wsgi.connectionmanager import ConnectionManager, ConnectionInfo
from ccai.webworks.wsgi.startresponse import StartResponse
from ccai.webworks.wsgi.worker import Worker
from ccai.webworks.wsgi.workermanager import WorkerManager, WorkerInfo
from ccai.webworks.wsgi.server import WSGIServer, run_server

__all__ = [
    "EnvironParser",
    "Request",
    "Response",
    "ResponseBuilder",
    "ResponseIterator",
    "RequestBodyParser",
    "UploadedFile",
    "ErrorHandler",
    "ASGIBridge",
    "is_asgi_application",
    "WSGIApplication",
    "WSGIMiddlewareWrapper",
    "as_wsgi_application",
    "get_wsgi_application",
    "resolve_wsgi_application",
    "create_wsgi_application",
    "set_wsgi_application",
    "reset_wsgi_application",
    "DEFAULT_MAX_REQUEST_BODY_SIZE",
    "HTTP_STATUS_PHRASES",
    "ENVIRON_REQUEST",
    "ENVIRON_ROUTE",
    "ENVIRON_PATH_PARAMS",
    "ENVIRON_ERROR",
    "ENVIRON_DEBUG",
    "ENVIRON_REQUEST_ID",
    "ENVIRON_REQUEST_TIMEOUT",
    "WORKER_BOOT_ERROR_EXIT_CODE",
    "WSGIError",
    "HTTPException",
    "RequestEntityTooLarge",
    "BadRequestBody",
    "RequestParseError",
    "RequestLineTooLong",
    "HeaderTooLarge",
    "TooManyHeaders",
    "IncompleteRequest",
    "ConnectionClosed",
    "InvalidResponseHeader",
    "RequestTimeout",
    "ServerError",
    "BindError",
    "WorkerError",
    "WorkerBootError",
    "IncompleteResponse",
    "ServerConfig",
    "ConfigurationError",
    "SocketListener",
    "SocketReader",
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
