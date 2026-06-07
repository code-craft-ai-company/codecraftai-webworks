"""
    Request logging middleware for the development server.

    This module provides the :class:`RequestLogger` middleware that logs
    request method, path, response status code, and response time for
    every request processed by the development server.

    The logger supports colored output via the webworks CLI output module
    and formats log entries using a configurable format string.
"""

import logging
import time

from typing import Any, Callable, Optional

from ccai.webworks.devexp.cli.output import colorize


logger = logging.getLogger(__name__)


# =============================================================================
# Status Code Color Mapping
# =============================================================================

def _status_color(status_code: int) -> str:
    """
        Determine the color name for a given HTTP status code.

        Informational (1xx) and success (2xx) responses are green,
        redirects (3xx) are cyan, client errors (4xx) are yellow,
        and server errors (5xx) are red.

        :param status_code: The HTTP status code.

        :returns: A color name string suitable for :func:`colorize`.
    """
    if status_code < 200:
        color = "cyan"
    elif status_code < 300:
        color = "green"
    elif status_code < 400:
        color = "cyan"
    elif status_code < 500:
        color = "yellow"
    else:
        color = "red"

    return color


def _method_color(method: str) -> str:
    """
        Determine the color name for a given HTTP method.

        GET requests are green, POST/PUT/PATCH are cyan,
        DELETE is red, and other methods are white.

        :param method: The HTTP method string.

        :returns: A color name string suitable for :func:`colorize`.
    """
    method_upper = method.upper()

    if method_upper == "GET":
        color = "green"
    elif method_upper in ("POST", "PUT", "PATCH"):
        color = "cyan"
    elif method_upper == "DELETE":
        color = "red"
    else:
        color = "white"

    return color


# =============================================================================
# RequestLogger
# =============================================================================

class RequestLogger:
    """
        Middleware that logs request and response information.

        The logger records the HTTP method, request path, response status
        code, and the time taken to process the request. When colors are
        enabled, status codes and methods are colored according to their
        category.

        The logger is a callable that wraps request handling. It measures
        the elapsed time around the ``call_next`` invocation and formats
        a log line after the response is produced.
    """

    DEFAULT_FORMAT = "%(method)s %(path)s %(status)s %(time)sms"
    """Default log format string."""

    def __init__(
        self,
        format: Optional[str] = None,
        use_colors: bool = True,
        stream: Optional[object] = None,
    ):
        """
            Construct a RequestLogger.

            :param format: The log format string. Uses ``DEFAULT_FORMAT``
                when ``None``.
            :param use_colors: Whether to apply ANSI colors to the output.
            :param stream: Optional output stream for color detection.
                When ``None``, color detection uses ``sys.stdout``.
        """
        if format is not None:
            self._format = format
        else:
            self._format = self.DEFAULT_FORMAT

        self._use_colors = use_colors
        self._stream = stream

        return

    # -------------------------------------------------------------------------
    # Properties
    # -------------------------------------------------------------------------

    @property
    def format(self) -> str:
        """
            The log format string.

            :returns: The format string.
        """
        return self._format

    @property
    def use_colors(self) -> bool:
        """
            Whether colored output is enabled.

            :returns: ``True`` if colors are enabled.
        """
        return self._use_colors

    # -------------------------------------------------------------------------
    # Callable Interface
    # -------------------------------------------------------------------------

    def __call__(
        self,
        request: Any,
        call_next: Callable[[Any], Any],
    ) -> Any:
        """
            Log the request and response.

            Measures the time taken by ``call_next`` and logs the
            method, path, status code, and elapsed time.

            :param request: The incoming request object. Expected to have
                ``method`` and ``path`` attributes.
            :param call_next: A callable that processes the request and
                returns a response object with a ``status_code`` attribute.

            :returns: The response object from ``call_next``.
        """
        method = getattr(request, "method", "UNKNOWN")
        path = getattr(request, "path", "/")

        start_time = time.monotonic()

        response = call_next(request)

        elapsed = time.monotonic() - start_time
        elapsed_ms = round(elapsed * 1000, 2)

        status_code = getattr(response, "status_code", 0)

        log_line = self._format_log(method, path, status_code, elapsed_ms)

        logger.info(log_line)

        return response

    # -------------------------------------------------------------------------
    # Formatting
    # -------------------------------------------------------------------------

    def _format_log(
        self,
        method: str,
        path: str,
        status: int,
        time_ms: float,
    ) -> str:
        """
            Format the log message with optional colors.

            Substitutes the format placeholders with the provided values.
            When colors are enabled, the method and status code are
            wrapped in ANSI color codes based on their category.

            :param method: The HTTP method string.
            :param path: The request path.
            :param status: The HTTP response status code.
            :param time_ms: The elapsed time in milliseconds.

            :returns: The formatted log line.
        """
        if self._use_colors:
            method_str = colorize(method, _method_color(method), stream=self._stream)
            status_str = colorize(str(status), _status_color(status), stream=self._stream)
        else:
            method_str = method
            status_str = str(status)

        values = {
            "method": method_str,
            "path": path,
            "status": status_str,
            "time": str(time_ms),
        }

        log_line = self._format % values

        return log_line
