"""
    WSGI Layer package for the webworks framework.
    
    This package provides a complete Web Server Gateway Interface (WSGI) implementation
    including both the application interface and a built-in WSGI server.
"""

from ccai.webworks.wsgi.environparser import EnvironParser
from ccai.webworks.routing.request import Request
from ccai.webworks.wsgi.response import Response, ResponseBuilder
from ccai.webworks.wsgi.responseiterator import ResponseIterator
from ccai.webworks.wsgi.bodyparser import RequestBodyParser, UploadedFile
from ccai.webworks.wsgi.errorhandler import ErrorHandler
from ccai.webworks.wsgi.application import (
    WSGIApplication,
    get_wsgi_application,
    create_wsgi_application,
    set_wsgi_application,
    reset_wsgi_application,
)
from ccai.webworks.wsgi.middleware import WSGIMiddlewareWrapper
from ccai.webworks.wsgi.constants import (
    HTTP_STATUS_PHRASES,
    ENVIRON_REQUEST,
    ENVIRON_ROUTE,
    ENVIRON_PATH_PARAMS,
    ENVIRON_ERROR,
    ENVIRON_DEBUG,
)
from ccai.webworks.wsgi.exceptions import (
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
from ccai.webworks.wsgi.serverconfig import (
    ServerConfig,
    ConfigurationError,
)
from ccai.webworks.wsgi.socketlistener import SocketListener
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
