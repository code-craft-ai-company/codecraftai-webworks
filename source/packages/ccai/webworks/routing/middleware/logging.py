"""
    Request logging middleware module.

    This module provides the RequestLoggingMiddleware class for logging
    HTTP request and response details in the middleware pipeline. It supports
    configurable log levels, header filtering, and path exclusion patterns.

.. moduleauthor:: Code Craft AI LLC
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []

import fnmatch
import logging
import time

from typing import Any, Awaitable, Callable, Dict, Iterable, List, Optional

from ccai.webworks.routing.request import Request
from ccai.webworks.routing.response import Response


_module_logger = logging.getLogger(__name__)


#: Text written to the log in place of a sensitive value.
REDACTED = "[REDACTED]"

#: Query parameters whose values are credentials. Their values are never
#: written to the log.
DEFAULT_SENSITIVE_PARAMS = (
    "access_token",
    "api_key",
    "apikey",
    "auth",
    "authorization",
    "client_secret",
    "code",
    "id_token",
    "key",
    "passwd",
    "password",
    "refresh_token",
    "secret",
    "session",
    "session_id",
    "sig",
    "signature",
    "token",
)

def escape_log_text(text: Any) -> str:
    """
        Make a value taken from a request safe to write on one log line.

        Request paths arrive percent-decoded, so ``/x%0aINFO forged entry``
        carries a real line feed. Written as it is, it would start a second
        log line that looks like a genuine entry. Every character that is
        not printable is written as its escape sequence instead.

        :param text: The value to log.

        :returns: The value with control characters escaped.
    """
    parts: List[str] = []

    for character in str(text):
        if character.isprintable():
            parts.append(character)
        else:
            parts.append(character.encode("unicode_escape").decode("ascii"))

    rtnval = "".join(parts)
    return rtnval


class RequestLoggingMiddleware:
    """
        Request/response logging middleware.

        Logs the HTTP method, path, and query parameters before the handler
        is invoked, and logs the response status code and processing duration
        after the handler returns. Supports configurable log level, header
        filtering, and path exclusion patterns.

        What is logged comes from the client, so it is made safe first:
        control characters are escaped so a request can not forge a log
        line, and the values of sensitive query parameters -- API keys,
        tokens, magic-link codes -- are replaced by ``[REDACTED]``.

        A completion line is logged for every request, including the ones
        whose handler raises.

        The middleware runs in the synchronous pipeline through ``__call__``
        and in the asynchronous pipeline through ``call_async``.

        :param logger: Logger instance to use. Defaults to the module logger.
        :param log_level: Log level for request/response messages. Defaults
            to ``logging.INFO``.
        :param include_headers: List of header names to include in log output.
            When ``None``, no headers are logged.
        :param exclude_paths: List of path patterns to exclude from logging.
            Patterns use fnmatch-style wildcards. When ``None``, all paths
            are logged.
        :param sensitive_params: Names of query parameters whose values are
            redacted, compared without regard to case. When ``None``,
            :data:`DEFAULT_SENSITIVE_PARAMS` is used.
    """

    name: str = "request_logging"

    def __init__(
        self,
        logger: Optional[logging.Logger] = None,
        log_level: int = logging.INFO,
        include_headers: Optional[List[str]] = None,
        exclude_paths: Optional[List[str]] = None,
        sensitive_params: Optional[Iterable[str]] = None
    ):
        """
            Construct a RequestLoggingMiddleware.

            :param logger: Logger instance to use. Defaults to the module logger.
            :param log_level: Log level for request/response messages.
            :param include_headers: List of header names to include in log output.
            :param exclude_paths: List of path patterns to exclude from logging.
            :param sensitive_params: Names of query parameters to redact.
        """
        self._logger: logging.Logger = logger if logger is not None else _module_logger
        self._log_level: int = log_level
        self._include_headers: Optional[List[str]] = include_headers
        self._exclude_paths: Optional[List[str]] = exclude_paths

        if sensitive_params is None:
            sensitive_params = DEFAULT_SENSITIVE_PARAMS

        self._sensitive_params = frozenset(name.lower() for name in sensitive_params)
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

            Only the headers the operator listed are logged. Control
            characters in their values are escaped.

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
                filtered[header_name] = escape_log_text(value)

        return filtered

    def _format_query_params(self, request: Request) -> str:
        """
            Describe the query parameters of a request for the log.

            :param request: The incoming request.

            :returns: Text of the form ``{'page': '2', 'token': '[REDACTED]'}``,
                      or an empty string when there are no parameters.
        """
        rtnval = ""

        if len(request.query_params) > 0:
            described: Dict[str, str] = {}

            for param_name, param_value in request.query_params.items():
                safe_name = escape_log_text(param_name)

                if param_name.lower() in self._sensitive_params:
                    described[safe_name] = REDACTED
                else:
                    described[safe_name] = escape_log_text(param_value)

            rtnval = repr(described)

        return rtnval

    def _log_request(self, request: Request) -> None:
        """
            Log the request line.

            :param request: The incoming request.
        """
        # Build the request log message
        request_msg = f"Request: {escape_log_text(request.method)} {escape_log_text(request.path)}"

        query_params_repr = self._format_query_params(request)
        if query_params_repr:
            request_msg += f" query={query_params_repr}"

        # Include filtered headers if configured
        filtered_headers = self._format_headers(request)
        if filtered_headers:
            request_msg += f" headers={filtered_headers}"

        self._logger.log(self._log_level, request_msg)
        return

    def _log_completion(
        self,
        response: Optional[Any],
        error: Optional[BaseException],
        start_time: float
    ) -> None:
        """
            Log the completion line.

            :param response: The response from the next handler, or None
                when it raised.
            :param error: The exception the next handler raised, or None.
            :param start_time: ``time.monotonic()`` value taken before the
                next handler was called.
        """
        duration = time.monotonic() - start_time

        if response is not None:
            response_msg = f"Response: {response.status_code} duration={duration:.4f}s"
        else:
            error_name = type(error).__name__ if error is not None else "unknown"
            response_msg = f"Response: failed with {error_name} duration={duration:.4f}s"

        self._logger.log(self._log_level, response_msg)
        return

    def __call__(self, request: Request, call_next: Callable) -> Response:
        """
            Process a request through the logging middleware.

            Logs request details before calling the next handler and logs
            response details with processing duration after the handler
            returns or raises. Skips logging entirely when the request path
            matches an excluded pattern.

            :param request: The incoming Request.
            :param call_next: Callable to invoke the next middleware/handler.

            :returns: Response from the next handler.
        """
        if self._is_path_excluded(request.path):
            response = call_next(request)
            return response

        self._log_request(request)

        # Invoke the next handler and measure duration
        start_time = time.monotonic()
        response = None
        error: Optional[BaseException] = None

        try:
            response = call_next(request)
        except BaseException as exc:
            error = exc
            raise
        finally:
            self._log_completion(response, error, start_time)

        return response

    async def call_async(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """
            Process a request through the logging middleware in the
            asynchronous pipeline. Behaves as :meth:`__call__`.

            :param request: The incoming Request.
            :param call_next: Async callable to invoke the next middleware/handler.

            :returns: Response from the next handler.
        """
        if self._is_path_excluded(request.path):
            response = await call_next(request)
            return response

        self._log_request(request)

        # Invoke the next handler and measure duration
        start_time = time.monotonic()
        response = None
        error: Optional[BaseException] = None

        try:
            response = await call_next(request)
        except BaseException as exc:
            error = exc
            raise
        finally:
            self._log_completion(response, error, start_time)

        return response
