"""
    Structured logging module for the production server.

    This module provides the StructuredLogger class that supports both
    JSON and standard log formats with configurable output destinations.
    Log entries include timestamp, level, message, and context fields
    such as request_id and worker_id for request correlation and
    worker identification.
"""

import json
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Optional, TextIO, TYPE_CHECKING

if TYPE_CHECKING:
    from ccai.webworks.prodserver.serverconfig import ServerConfig


# Valid log levels in order of severity
LOG_LEVELS = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")

# Valid log formats
LOG_FORMATS = ("standard", "json")

# Valid output destinations
LOG_OUTPUTS = ("stdout", "stderr")


class StructuredLogger:
    """
        Provides structured logging with JSON and standard format support.

        Supports configurable log formats, output destinations, and
        persistent context fields. Log entries include timestamp, level,
        message, and context fields. When JSON format is enabled, all
        entries are emitted as valid JSON objects.
    """

    def __init__(self, config: "ServerConfig"):
        """
            Construct a StructuredLogger.

            :param config: Server configuration containing logging settings.
        """
        self._config = config
        self._context: Dict[str, Any] = {}
        self._log_format: str = config.log_format
        self._log_level: str = config.log_level.upper()
        self._access_log_path: Optional[str] = config.access_log
        self._error_log_path: Optional[str] = config.error_log

        self._access_log_file: Optional[TextIO] = None
        self._error_log_file: Optional[TextIO] = None

        return

    @property
    def log_format(self) -> str:
        """
            Get the configured log format.

            :returns: The log format string, either 'standard' or 'json'.
        """
        return self._log_format

    @property
    def log_level(self) -> str:
        """
            Get the configured log level.

            :returns: The log level string.
        """
        return self._log_level

    def open_log_files(self) -> None:
        """
            Open configured log files for writing.

            Opens the access log and error log files if paths are
            configured. Files are opened in append mode.
        """
        if self._access_log_path is not None:
            self._access_log_file = open(self._access_log_path, "a", encoding="utf-8")

        if self._error_log_path is not None:
            self._error_log_file = open(self._error_log_path, "a", encoding="utf-8")

        return

    def close_log_files(self) -> None:
        """
            Close any open log files.
        """
        if self._access_log_file is not None:
            self._access_log_file.close()
            self._access_log_file = None

        if self._error_log_file is not None:
            self._error_log_file.close()
            self._error_log_file = None

        return

    def _should_log(self, level: str) -> bool:
        """
            Determine if a message at the given level should be logged.

            :param level: The log level to check.

            :returns: True if the level meets or exceeds the configured threshold.
        """
        level_upper = level.upper()

        if level_upper not in LOG_LEVELS:
            return True

        configured_idx = LOG_LEVELS.index(self._log_level) if self._log_level in LOG_LEVELS else 0
        message_idx = LOG_LEVELS.index(level_upper)

        rtnval = message_idx >= configured_idx

        return rtnval

    def log(self, level: str, message: str, **context: Any) -> str:
        """
            Log a message with context fields.

            Creates a log entry with timestamp, level, message, and any
            additional context fields. Persistent context fields set via
            set_context are merged with the provided context. The entry
            is formatted according to the configured log format.

            :param level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
            :param message: The log message.
            :param context: Additional context fields to include.

            :returns: The formatted log entry string.
        """
        if not self._should_log(level):
            return ""

        entry = self._build_entry(level, message, **context)
        formatted = self._format_entry(entry)

        self._write_output(formatted)

        return formatted

    def access_log(
        self,
        method: str,
        path: str,
        status_code: int,
        latency_ms: float,
        **context: Any
    ) -> str:
        """
            Log an access log entry for a completed request.

            :param method: The HTTP method.
            :param path: The request path.
            :param status_code: The response status code.
            :param latency_ms: Request latency in milliseconds.
            :param context: Additional context fields.

            :returns: The formatted access log entry string.
        """
        merged_context = dict(context)
        merged_context["method"] = method
        merged_context["path"] = path
        merged_context["status_code"] = status_code
        merged_context["latency_ms"] = round(latency_ms, 2)

        entry = self._build_entry(
            "INFO",
            f"{method} {path} {status_code} {latency_ms:.2f}ms",
            **merged_context
        )
        formatted = self._format_entry(entry)

        self._write_access_log(formatted)

        return formatted

    def error_log(
        self,
        exception: Exception,
        message: Optional[str] = None,
        **context: Any
    ) -> str:
        """
            Log an error with exception details.

            :param exception: The exception that occurred.
            :param message: Optional override message.
            :param context: Additional context fields.

            :returns: The formatted error log entry string.
        """
        error_message = message if message is not None else str(exception)

        merged_context = dict(context)
        merged_context["exception_type"] = type(exception).__name__
        merged_context["exception_message"] = str(exception)

        entry = self._build_entry("ERROR", error_message, **merged_context)
        formatted = self._format_entry(entry)

        self._write_error_log(formatted)

        return formatted

    def _build_entry(self, level: str, message: str, **context: Any) -> Dict[str, Any]:
        """
            Build a log entry dictionary.

            Merges persistent context with provided context fields.
            Provided context takes precedence over persistent context.

            :param level: Log level string.
            :param message: Log message.
            :param context: Additional context fields.

            :returns: Dictionary containing the complete log entry.
        """
        entry: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": level.upper(),
            "message": message,
        }

        # Merge persistent context first, then override with provided context
        for key, value in self._context.items():
            entry[key] = value

        for key, value in context.items():
            entry[key] = value

        return entry

    def _format_entry(self, entry: Dict[str, Any]) -> str:
        """
            Format a log entry according to the configured format.

            :param entry: The log entry dictionary.

            :returns: Formatted log entry string.
        """
        if self._log_format == "json":
            rtnval = self._format_json(entry)
        else:
            rtnval = self._format_standard(entry)

        return rtnval

    def _format_json(self, entry: Dict[str, Any]) -> str:
        """
            Format a log entry as a JSON string.

            :param entry: The log entry dictionary.

            :returns: JSON-formatted log entry string.
        """
        rtnval = json.dumps(entry, default=str)

        return rtnval

    def _format_standard(self, entry: Dict[str, Any]) -> str:
        """
            Format a log entry in standard text format.

            Format: [TIMESTAMP] LEVEL message key=value key=value ...

            :param entry: The log entry dictionary.

            :returns: Standard-formatted log entry string.
        """
        timestamp = entry.get("timestamp", "")
        level = entry.get("level", "INFO")
        message = entry.get("message", "")

        parts = [f"[{timestamp}]", level, message]

        # Append extra context fields
        for key, value in entry.items():
            if key not in ("timestamp", "level", "message"):
                parts.append(f"{key}={value}")

        rtnval = " ".join(parts)

        return rtnval

    def _write_output(self, formatted: str) -> None:
        """
            Write a formatted log entry to the default output.

            Writes to stdout by default.

            :param formatted: The formatted log entry string.
        """
        sys.stdout.write(formatted + "\n")
        sys.stdout.flush()

        return

    def _write_access_log(self, formatted: str) -> None:
        """
            Write a formatted entry to the access log destination.

            Writes to the access log file if configured, otherwise
            writes to stdout.

            :param formatted: The formatted log entry string.
        """
        if self._access_log_file is not None:
            self._access_log_file.write(formatted + "\n")
            self._access_log_file.flush()
        else:
            sys.stdout.write(formatted + "\n")
            sys.stdout.flush()

        return

    def _write_error_log(self, formatted: str) -> None:
        """
            Write a formatted entry to the error log destination.

            Writes to the error log file if configured, otherwise
            writes to stderr.

            :param formatted: The formatted log entry string.
        """
        if self._error_log_file is not None:
            self._error_log_file.write(formatted + "\n")
            self._error_log_file.flush()
        else:
            sys.stderr.write(formatted + "\n")
            sys.stderr.flush()

        return

    def set_context(self, **context: Any) -> None:
        """
            Set persistent context fields.

            These fields are included in all subsequent log entries
            until cleared. Useful for setting worker_id or request_id
            that should appear in every log entry.

            :param context: Key-value pairs to set as persistent context.
        """
        self._context.update(context)

        return

    def clear_context(self) -> None:
        """
            Clear all persistent context fields.
        """
        self._context.clear()

        return

    def get_context(self) -> Dict[str, Any]:
        """
            Get the current persistent context fields.

            :returns: Dictionary of persistent context fields.
        """
        rtnval = dict(self._context)

        return rtnval
