"""
    Error normalization middleware module.

    This module provides the ErrorNormalizationMiddleware class for catching
    unhandled exceptions in the middleware pipeline and converting them to
    structured JSON error responses. It supports debug mode for traceback
    inclusion, custom exception-to-status mappings, and configurable logging.

.. moduleauthor:: Code Craft AI LLC
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []

import json
import logging
import traceback as tb_module

from typing import Callable, Dict, Optional, Tuple

from ccai.webworks.routing.exceptions import HTTPException
from ccai.webworks.routing.request import Request
from ccai.webworks.routing.response import Response


_module_logger = logging.getLogger(__name__)


# Common HTTP status phrases used for error descriptions
_STATUS_PHRASES: Dict[int, str] = {
    400: "Bad Request",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Not Found",
    405: "Method Not Allowed",
    406: "Not Acceptable",
    408: "Request Timeout",
    409: "Conflict",
    410: "Gone",
    413: "Payload Too Large",
    415: "Unsupported Media Type",
    422: "Unprocessable Entity",
    429: "Too Many Requests",
    500: "Internal Server Error",
    501: "Not Implemented",
    502: "Bad Gateway",
    503: "Service Unavailable",
    504: "Gateway Timeout",
}


class ErrorNormalizationMiddleware:
    """
        Catches unhandled exceptions and returns structured JSON error responses.

        Wraps the downstream handler in a try/except block. HTTPException
        instances are mapped to their status code, custom-mapped exceptions
        use the configured status code and message, and all other exceptions
        are mapped to 500 Internal Server Error. In debug mode the full
        traceback is included in the response body.

        :param debug: Whether to include tracebacks in error responses.
        :param logger: Logger instance for caught exceptions. Defaults to
            the module logger.
        :param exception_map: Optional mapping of exception types to
            ``(status_code, error_message)`` tuples for custom handling.
    """

    name: str = "error_normalization"

    def __init__(
        self,
        debug: bool = False,
        logger: Optional[logging.Logger] = None,
        exception_map: Optional[Dict[type, Tuple[int, str]]] = None
    ):
        """
            Construct an ErrorNormalizationMiddleware.

            :param debug: Whether to include tracebacks in error responses.
            :param logger: Logger instance for caught exceptions.
            :param exception_map: Optional mapping of exception types to
                ``(status_code, error_message)`` tuples.
        """
        self._debug: bool = debug
        self._logger: logging.Logger = logger if logger is not None else _module_logger
        self._exception_map: Dict[type, Tuple[int, str]] = exception_map if exception_map is not None else {}
        return

    def __call__(self, request: Request, call_next: Callable) -> Response:
        """
            Process a request through the error normalization middleware.

            Wraps ``call_next`` in a try/except. Caught exceptions are
            converted to structured JSON responses with ``error``,
            ``error_description``, and ``status_code`` fields. In debug
            mode a ``traceback`` field is also included.

            :param request: The incoming Request.
            :param call_next: Callable to invoke the next middleware/handler.

            :returns: Response from the next handler, or a JSON error response.
        """
        try:
            response = call_next(request)
            return response
        except Exception as exc:
            self._logger.exception("Caught exception in middleware pipeline: %s", exc)
            return self._build_error_response(exc)

    def _build_error_response(self, exc: Exception) -> Response:
        """
            Build a structured JSON error response from an exception.

            :param exc: The caught exception.

            :returns: A Response with JSON error body.
        """
        status_code: int
        error: str
        error_description: str

        # Check custom exception map first (exact type match)
        exc_type = type(exc)
        if exc_type in self._exception_map:
            status_code, error = self._exception_map[exc_type]
            error_description = str(exc) if str(exc) else error
        elif isinstance(exc, HTTPException):
            status_code = exc.status_code
            error = _STATUS_PHRASES.get(status_code, "Error")
            error_description = exc.detail if exc.detail is not None else error
        else:
            status_code = 500
            error = "Internal Server Error"
            error_description = "Internal Server Error"

        body: Dict = {
            "error": error,
            "error_description": error_description,
            "status_code": status_code,
        }

        if self._debug:
            body["traceback"] = tb_module.format_exception(type(exc), exc, exc.__traceback__)

        json_body = json.dumps(body, ensure_ascii=False).encode("utf-8")

        response = Response(
            status_code=status_code,
            headers={"Content-Type": "application/json; charset=utf-8"},
            body=json_body,
        )

        return response
