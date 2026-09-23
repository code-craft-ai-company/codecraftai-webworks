"""
    Development logging module for the webworks framework.

    This module provides the :class:`DevLogger` class that configures
    enhanced logging for development. It supports:

    - DEBUG level logging when debug mode is enabled (Requirement 15.1)
    - Log formatting with timestamps and source location (Requirement 15.2)
    - Colored log output for different log levels (Requirement 15.3)
    - SQL query logging when database debugging is enabled (Requirement 15.4)
    - ``--log-level`` CLI option to adjust verbosity (Requirement 15.5)
    - ``--log-file`` option for logging to file (Requirement 15.6)
    - Request ID correlation for tracing log entries (Requirement 15.7)

    The module uses Python's standard :mod:`logging` module as the
    foundation and extends it with colored formatting and request ID
    context tracking via :mod:`contextvars`.
"""

import contextvars
import logging
import sys
import uuid

from typing import Any, Dict, Optional


from ccai.webworks.devexp.cli.output import colorize


# =============================================================================
# Request ID Context Variable
# =============================================================================

_request_id_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "request_id", default=None
)


def get_request_id() -> Optional[str]:
    """
        Get the current request ID from the context.

        :returns: The current request ID string, or ``None`` if no
            request is active.
    """
    request_id = _request_id_var.get()

    return request_id


def set_request_id(request_id: Optional[str]) -> contextvars.Token:
    """
        Set the current request ID in the context.

        :param request_id: The request ID string to set, or ``None``
            to clear the current request ID.

        :returns: A token that can be used to reset the context variable
            to its previous value.
    """
    token = _request_id_var.set(request_id)

    return token


def generate_request_id() -> str:
    """
        Generate a new unique request ID.

        Uses a UUID4 truncated to 8 characters for brevity while
        maintaining sufficient uniqueness for development logging.

        :returns: A short unique request ID string.
    """
    request_id = uuid.uuid4().hex[:8]

    return request_id


# =============================================================================
# Log Level Color Mapping
# =============================================================================

LOG_LEVEL_COLORS: Dict[str, str] = {
    "DEBUG": "cyan",
    "INFO": "green",
    "WARNING": "yellow",
    "ERROR": "red",
    "CRITICAL": "magenta",
}


# =============================================================================
# Default Log Format
# =============================================================================

DEFAULT_LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
"""Default log format string with timestamp, level, logger name, and message."""

DEFAULT_LOG_FORMAT_WITH_LOCATION = (
    "%(asctime)s [%(levelname)s] %(name)s (%(filename)s:%(lineno)d): %(message)s"
)
"""Log format string that includes source file location."""

SQL_LOGGER_NAME = "sqlalchemy.engine"
"""Logger name used for SQL query logging."""


# =============================================================================
# ColoredFormatter
# =============================================================================

class ColoredFormatter(logging.Formatter):
    """
        A logging formatter that applies ANSI colors to log level names.

        When colors are enabled and the output stream supports them,
        the log level name in each record is wrapped in the appropriate
        ANSI color code. The color mapping is defined by
        :data:`LOG_LEVEL_COLORS`.

        When colors are not supported or are disabled, the formatter
        behaves identically to the standard :class:`logging.Formatter`.
    """

    def __init__(
        self,
        fmt: Optional[str] = None,
        datefmt: Optional[str] = None,
        use_colors: bool = True,
        stream: Optional[object] = None,
    ):
        """
            Construct a ColoredFormatter.

            :param fmt: The log format string. Uses
                :data:`DEFAULT_LOG_FORMAT_WITH_LOCATION` when ``None``.
            :param datefmt: The date format string for timestamps.
            :param use_colors: Whether to apply ANSI colors to the
                log level name.
            :param stream: Optional output stream for color detection.
                When ``None``, color detection uses ``sys.stderr``.
        """
        if fmt is None:
            fmt = DEFAULT_LOG_FORMAT_WITH_LOCATION

        super().__init__(fmt=fmt, datefmt=datefmt)

        self._use_colors = use_colors
        self._stream = stream

        return

    @property
    def use_colors(self) -> bool:
        """
            Whether colored output is enabled.

            :returns: ``True`` if colors are enabled.
        """
        return self._use_colors

    def format(self, record: logging.LogRecord) -> str:
        """
            Format the log record with optional colored level name.

            If colors are enabled and the output stream supports them,
            the level name is wrapped in the appropriate ANSI color.
            The request ID is appended to the message when one is
            active in the current context.

            :param record: The log record to format.

            :returns: The formatted log string.
        """
        # Inject request ID into the record if available
        request_id = get_request_id()
        if request_id is not None:
            record.msg = "[{}] {}".format(request_id, record.msg)

        if self._use_colors:
            original_levelname = record.levelname
            color = LOG_LEVEL_COLORS.get(record.levelname)

            if color is not None:
                record.levelname = colorize(
                    record.levelname, color, stream=self._stream
                )

            result = super().format(record)

            record.levelname = original_levelname
        else:
            result = super().format(record)

        return result


# =============================================================================
# DevLogger
# =============================================================================

class DevLogger:
    """
        Development logging configurator for the webworks framework.

        The :class:`DevLogger` sets up Python's standard logging module
        with development-friendly defaults including colored output,
        source location in log messages, and request ID correlation.

        It supports configuration through a dictionary (typically loaded
        from the webworks configuration system) and provides methods for
        enabling SQL query logging and file-based logging.

        Usage::

            logger_config = DevLogger(debug=True)
            logger_config.setup()

            # Enable SQL logging
            logger_config.enable_sql_logging()

            # Add file output
            logger_config.add_file_handler("/tmp/webworks.log")
    """

    def __init__(
        self,
        debug: bool = False,
        log_level: Optional[str] = None,
        log_format: Optional[str] = None,
        use_colors: bool = True,
        log_file: Optional[str] = None,
        stream: Optional[object] = None,
    ):
        """
            Construct a DevLogger.

            When *debug* is ``True`` and no explicit *log_level* is
            provided, the log level defaults to ``DEBUG``. Otherwise
            the default level is ``WARNING``.

            :param debug: Whether debug mode is enabled.
            :param log_level: Explicit log level name (e.g. ``"INFO"``).
                Overrides the debug mode default when provided.
            :param log_format: The log format string. Uses the default
                format with source location when ``None``.
            :param use_colors: Whether to apply ANSI colors to output.
            :param log_file: Optional path to a log file. When provided,
                a file handler is added during :meth:`setup`.
            :param stream: Optional output stream for color detection.
        """
        self._debug = debug
        self._use_colors = use_colors
        self._log_file = log_file
        self._stream = stream
        self._handlers: list = []
        self._sql_logging_enabled = False

        if log_level is not None:
            self._log_level = log_level.upper()
        elif debug:
            self._log_level = "DEBUG"
        else:
            self._log_level = "WARNING"

        if log_format is not None:
            self._log_format = log_format
        else:
            self._log_format = DEFAULT_LOG_FORMAT_WITH_LOCATION

        return

    # -------------------------------------------------------------------------
    # Properties
    # -------------------------------------------------------------------------

    @property
    def debug(self) -> bool:
        """
            Whether debug mode is enabled.

            :returns: ``True`` if debug mode is active.
        """
        return self._debug

    @property
    def log_level(self) -> str:
        """
            The configured log level name.

            :returns: The log level string (e.g. ``"DEBUG"``).
        """
        return self._log_level

    @property
    def log_format(self) -> str:
        """
            The configured log format string.

            :returns: The format string.
        """
        return self._log_format

    @property
    def use_colors(self) -> bool:
        """
            Whether colored output is enabled.

            :returns: ``True`` if colors are enabled.
        """
        return self._use_colors

    @property
    def log_file(self) -> Optional[str]:
        """
            The configured log file path.

            :returns: The log file path or ``None``.
        """
        return self._log_file

    @property
    def sql_logging_enabled(self) -> bool:
        """
            Whether SQL query logging is enabled.

            :returns: ``True`` if SQL logging is active.
        """
        return self._sql_logging_enabled

    # -------------------------------------------------------------------------
    # Setup
    # -------------------------------------------------------------------------

    def setup(self) -> None:
        """
            Configure the root logger with the development settings.

            Sets the root logger level, creates a colored stream handler,
            and optionally adds a file handler if a log file path was
            provided.

            This method should be called once during application startup.
        """
        root_logger = logging.getLogger()

        numeric_level = getattr(logging, self._log_level, logging.WARNING)
        root_logger.setLevel(numeric_level)

        # Create the console handler with colored formatter
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setLevel(numeric_level)

        formatter = ColoredFormatter(
            fmt=self._log_format,
            use_colors=self._use_colors,
            stream=self._stream,
        )
        console_handler.setFormatter(formatter)

        root_logger.addHandler(console_handler)
        self._handlers.append(console_handler)

        # Add file handler if configured
        if self._log_file is not None:
            self.add_file_handler(self._log_file)

        return

    def add_file_handler(self, file_path: str) -> logging.FileHandler:
        """
            Add a file handler to the root logger.

            The file handler uses a plain (non-colored) formatter since
            ANSI codes are not useful in log files.

            :param file_path: Path to the log file.

            :returns: The created file handler.
        """
        root_logger = logging.getLogger()

        file_handler = logging.FileHandler(file_path)

        numeric_level = getattr(logging, self._log_level, logging.WARNING)
        file_handler.setLevel(numeric_level)

        # File handler uses plain formatter (no colors)
        plain_formatter = logging.Formatter(
            fmt=self._log_format,
        )
        file_handler.setFormatter(plain_formatter)

        root_logger.addHandler(file_handler)
        self._handlers.append(file_handler)

        return file_handler

    def enable_sql_logging(self, level: Optional[str] = None) -> None:
        """
            Enable SQL query logging.

            Configures the SQLAlchemy engine logger to output SQL
            queries at the specified level. When no level is provided,
            ``DEBUG`` is used.

            :param level: The log level for SQL queries. Defaults to
                ``"DEBUG"``.
        """
        if level is not None:
            sql_level = level.upper()
        else:
            sql_level = "DEBUG"

        numeric_level = getattr(logging, sql_level, logging.DEBUG)

        sql_logger = logging.getLogger(SQL_LOGGER_NAME)
        sql_logger.setLevel(numeric_level)

        self._sql_logging_enabled = True

        return

    def disable_sql_logging(self) -> None:
        """
            Disable SQL query logging.

            Resets the SQLAlchemy engine logger to ``WARNING`` level.
        """
        sql_logger = logging.getLogger(SQL_LOGGER_NAME)
        sql_logger.setLevel(logging.WARNING)

        self._sql_logging_enabled = False

        return

    def teardown(self) -> None:
        """
            Remove all handlers added by this DevLogger from the root
            logger.

            This is useful for cleanup in tests or when reconfiguring
            logging.
        """
        root_logger = logging.getLogger()

        for handler in self._handlers:
            root_logger.removeHandler(handler)
            handler.close()

        self._handlers.clear()

        return

    # -------------------------------------------------------------------------
    # Factory
    # -------------------------------------------------------------------------

    @classmethod
    def from_config(cls, config: Dict[str, Any], debug: bool = False) -> "DevLogger":
        """
            Create a DevLogger from a configuration dictionary.

            The configuration dictionary is expected to have a
            ``"logging"`` section with optional keys for ``"level"``,
            ``"format"``, and ``"colors"``.

            :param config: The full configuration dictionary.
            :param debug: Whether debug mode is enabled.

            :returns: A configured :class:`DevLogger` instance.
        """
        logging_config = config.get("logging", {})

        log_level = logging_config.get("level")
        log_format = logging_config.get("format")
        use_colors = logging_config.get("colors", True)
        log_file = logging_config.get("file")

        instance = cls(
            debug=debug,
            log_level=log_level,
            log_format=log_format,
            use_colors=use_colors,
            log_file=log_file,
        )

        return instance
