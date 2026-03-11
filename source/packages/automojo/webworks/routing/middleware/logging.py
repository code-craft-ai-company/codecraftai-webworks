"""
    Request logging middleware module.

    This module provides the RequestLoggingMiddleware class for logging
    HTTP request and response details in the middleware pipeline. It supports
    configurable log levels, header filtering, and path exclusion patterns.

.. moduleauthor:: Automation Mojo LLC
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []

import fnmatch
import logging
import time

from typing import Callable, Dict, List, Optional

from automojo.webworks.routing.request import Request
from automojo.webworks.routing.response import Response


_module_logger = logging.getLogger(__name__)


class RequestLoggingMiddleware:
    """
        Request/response logging middleware.

        Logs the HTTP method, path, and query parameters before the handler
        is invoked, and logs the response status code and processing duration
        after the handler returns. Supports configurable log level, header
        filtering, and path exclusion patterns.

        :param logger: Logger instance to use. Defaults to the module logger.
        :param log_level: Log level for request/response messages. Defaults
            to ``logging.INFO``.
        :param include_headers: List of header names to include in log output.
            When ``None``, no headers are logged.
        :param exclude_paths: List of path patterns to exclude from logging.
            Patterns use fnmatch-style wildcards. When ``None``, all paths
            are logged.
    """

    name: str = "request_logging"

    def __init__(
        self,
        logger: Optional[logging.Logger] = None,
        log_level: int = logging.INFO,
        include_headers: Optional[List[str]] = None,
        exclude_paths: Optional[List[str]] = None
    ):
        """
            Construct a RequestLoggingMiddleware.

            :param logger: Logger instance to use. Defaults to the module logger.
            :param log_level: Log level for request/response messages.
            :param include_headers: List of header names to include in log output.
            :param exclude_paths: List of path patterns to exclude from logging.
        """
        self._logger: logging.Logger = logger if logger is not None else _module_logger
        self._log_level: int = log_level
        self._include_headers: Optional[List[str]] = include_headers
        self._exclude_paths: Optional[List[str]] = exclude_paths
        return

    def _is_path_excluded(self, path: str) -> bool:
        """
            Check whether the given path matches any exclusion pattern.

            :param path: The request path to check.

            :returns: True if the path should be excluded from logging.
        """
        if self._exclude_paths is None:
            return False

        for pattern in self._exclude_paths:
            if fnmatch.fnmatch(path, pattern):
                return True

        return False

    def _format_headers(self, request: Request) -> Optional[Dict[str, str]]:
        """
            Extract the configured headers from the request.

            :param request: The incoming request.

            :returns: Dictionary of filtered headers, or None if no headers
                are configured for inclusion.
        """
        if self._include_headers is None:
            return None

        filtered: Dict[str, str] = {}
        for header_name in self._include_headers:
            value = request.headers.get(header_name)
            if value is not None:
                filtered[header_name] = value

        return filtered

    def __call__(self, request: Request, call_next: Callable) -> Response:
        """
            Process a request through the logging middleware.

            Logs request details before calling the next handler and logs
            response details with processing duration after the handler
            returns. Skips logging entirely when the request path matches
            an excluded pattern.

            :param request: The incoming Request.
            :param call_next: Callable to invoke the next middleware/handler.

            :returns: Response from the next handler.
        """
        if self._is_path_excluded(request.path):
            response = call_next(request)
            return response

        # Build the request log message
        query_params_repr = repr(request.query_params) if len(request.query_params) > 0 else ""
        request_msg = f"Request: {request.method} {request.path}"
        if query_params_repr:
            request_msg += f" query={query_params_repr}"

        # Include filtered headers if configured
        filtered_headers = self._format_headers(request)
        if filtered_headers:
            request_msg += f" headers={filtered_headers}"

        self._logger.log(self._log_level, request_msg)

        # Invoke the next handler and measure duration
        start_time = time.monotonic()
        response = call_next(request)
        duration = time.monotonic() - start_time

        # Log response details
        response_msg = f"Response: {response.status_code} duration={duration:.4f}s"
        self._logger.log(self._log_level, response_msg)

        return response
