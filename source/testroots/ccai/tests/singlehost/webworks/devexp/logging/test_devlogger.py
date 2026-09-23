"""
    Tests for the development logging module.

    This module contains unit tests for the :class:`DevLogger` class,
    the :class:`ColoredFormatter`, and the request ID correlation
    functions.
"""

import logging
import os
import tempfile

from ccai.webworks.devexp.cli.output import (
    ANSI_CYAN,
    ANSI_GREEN,
    ANSI_RED,
    ANSI_YELLOW,
)
from ccai.webworks.devexp.logging.devlogger import (
    ColoredFormatter,
    DevLogger,
    LOG_LEVEL_COLORS,
    SQL_LOGGER_NAME,
    generate_request_id,
    get_request_id,
    set_request_id,
)


# =============================================================================
# Test Helpers
# =============================================================================

class _FakeTTYStream:
    """
        A fake stream that reports itself as a TTY.
    """

    def isatty(self) -> bool:
        return True


class _FakeNonTTYStream:
    """
        A fake stream that reports itself as not a TTY.
    """

    def isatty(self) -> bool:
        return False


def _without_no_color_env(func):
    """
        Run *func* with the NO_COLOR environment variable removed.
    """
    original = os.environ.get("NO_COLOR")

    try:
        os.environ.pop("NO_COLOR", None)
        result = func()
    finally:
        if original is None:
            os.environ.pop("NO_COLOR", None)
        else:
            os.environ["NO_COLOR"] = original

    return result


def _detach_root_logger_handlers():
    """
        Detach the root logger's handlers and return them, for isolation.

        The handlers are detached but NOT closed. The test runner owns the root
        logger for the duration of a run, so closing its handlers breaks the
        framework's own logging for everything that follows — the next log call
        writes to a closed stream and the run stops making progress rather than
        failing. Detaching gives a test the same isolation without taking the
        framework's logging down with it.

        :returns: The detached handlers and the level to restore.
    """
    root_logger = logging.getLogger()

    detached = root_logger.handlers[:]
    for handler in detached:
        root_logger.removeHandler(handler)

    return (detached, root_logger.level)


def _restore_root_logger_handlers(saved):
    """
        Restore handlers detached by :func:`_detach_root_logger_handlers`.

        Anything the test attached is removed first, and closed — those are the
        test's own handlers, so the test is responsible for them.

        :param saved: The tuple returned by _detach_root_logger_handlers.

        :returns: ``None``
    """
    detached, level = saved

    root_logger = logging.getLogger()

    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
        if handler not in detached:
            handler.close()

    for handler in detached:
        root_logger.addHandler(handler)

    root_logger.setLevel(level)

    return


# =============================================================================
# 19.1 - Tests for DEBUG Level Logging in Debug Mode
# =============================================================================

def test_devlogger_debug_mode_sets_debug_level():
    """
        Test that debug=True sets the log level to DEBUG by default.
    """
    dev_logger = DevLogger(debug=True)

    if dev_logger.log_level != "DEBUG":
        errmsg = "Expected log_level 'DEBUG', got '{}'".format(dev_logger.log_level)
        raise AssertionError(errmsg)

    return


def test_devlogger_non_debug_mode_sets_warning_level():
    """
        Test that debug=False sets the log level to WARNING by default.
    """
    dev_logger = DevLogger(debug=False)

    if dev_logger.log_level != "WARNING":
        errmsg = "Expected log_level 'WARNING', got '{}'".format(dev_logger.log_level)
        raise AssertionError(errmsg)

    return


def test_devlogger_explicit_level_overrides_debug():
    """
        Test that an explicit log_level overrides the debug mode default.
    """
    dev_logger = DevLogger(debug=True, log_level="INFO")

    if dev_logger.log_level != "INFO":
        errmsg = "Expected log_level 'INFO', got '{}'".format(dev_logger.log_level)
        raise AssertionError(errmsg)

    return


def test_devlogger_setup_configures_root_logger_level():
    """
        Test that setup() sets the root logger to the configured level.
    """
    _saved_logging = _detach_root_logger_handlers()

    dev_logger = DevLogger(debug=True)

    try:
        dev_logger.setup()

        root_logger = logging.getLogger()
        expected_level = logging.DEBUG

        if root_logger.level != expected_level:
            errmsg = "Expected root logger level {}, got {}".format(
                expected_level, root_logger.level
            )
            raise AssertionError(errmsg)
    finally:
        dev_logger.teardown()
        _restore_root_logger_handlers(_saved_logging)

    return


# =============================================================================
# 19.2 - Tests for Log Formatting with Timestamps and Source Location
# =============================================================================

def test_devlogger_default_format_includes_asctime():
    """
        Test that the default format includes the asctime placeholder.
    """
    dev_logger = DevLogger(debug=True)

    if "%(asctime)s" not in dev_logger.log_format:
        errmsg = "Expected '%(asctime)s' in format, got '{}'".format(
            dev_logger.log_format
        )
        raise AssertionError(errmsg)

    return


def test_devlogger_default_format_includes_levelname():
    """
        Test that the default format includes the levelname placeholder.
    """
    dev_logger = DevLogger(debug=True)

    if "%(levelname)s" not in dev_logger.log_format:
        errmsg = "Expected '%(levelname)s' in format, got '{}'".format(
            dev_logger.log_format
        )
        raise AssertionError(errmsg)

    return


def test_devlogger_default_format_includes_source_location():
    """
        Test that the default format includes filename and lineno.
    """
    dev_logger = DevLogger(debug=True)

    has_filename = "%(filename)s" in dev_logger.log_format
    has_lineno = "%(lineno)d" in dev_logger.log_format

    if not has_filename:
        errmsg = "Expected '%(filename)s' in format, got '{}'".format(
            dev_logger.log_format
        )
        raise AssertionError(errmsg)

    if not has_lineno:
        errmsg = "Expected '%(lineno)d' in format, got '{}'".format(
            dev_logger.log_format
        )
        raise AssertionError(errmsg)

    return


def test_devlogger_custom_format():
    """
        Test that a custom format string is stored correctly.
    """
    custom_format = "%(message)s"
    dev_logger = DevLogger(debug=True, log_format=custom_format)

    if dev_logger.log_format != custom_format:
        errmsg = "Expected format '{}', got '{}'".format(
            custom_format, dev_logger.log_format
        )
        raise AssertionError(errmsg)

    return


def test_colored_formatter_formats_record_with_location():
    """
        Test that the ColoredFormatter produces output with source location.
    """
    formatter = ColoredFormatter(use_colors=False)

    record = logging.LogRecord(
        name="test.logger",
        level=logging.INFO,
        pathname="test_file.py",
        lineno=42,
        msg="Test message",
        args=None,
        exc_info=None,
    )

    result = formatter.format(record)

    if "test_file.py" not in result:
        errmsg = "Expected 'test_file.py' in formatted output, got '{}'".format(result)
        raise AssertionError(errmsg)

    if "42" not in result:
        errmsg = "Expected '42' in formatted output, got '{}'".format(result)
        raise AssertionError(errmsg)

    return


# =============================================================================
# 19.3 - Tests for Colored Log Output
# =============================================================================

def test_colored_formatter_applies_color_on_tty():
    """
        Test that the ColoredFormatter applies ANSI colors on a TTY stream.
    """
    tty_stream = _FakeTTYStream()
    formatter = ColoredFormatter(use_colors=True, stream=tty_stream)

    record = logging.LogRecord(
        name="test.logger",
        level=logging.ERROR,
        pathname="test_file.py",
        lineno=10,
        msg="Error occurred",
        args=None,
        exc_info=None,
    )

    def check():
        return formatter.format(record)

    result = _without_no_color_env(check)

    if ANSI_RED not in result:
        errmsg = "Expected ANSI_RED in colored output for ERROR, got '{}'".format(
            repr(result)
        )
        raise AssertionError(errmsg)

    return


def test_colored_formatter_warning_is_yellow():
    """
        Test that WARNING level is colored yellow.
    """
    tty_stream = _FakeTTYStream()
    formatter = ColoredFormatter(use_colors=True, stream=tty_stream)

    record = logging.LogRecord(
        name="test.logger",
        level=logging.WARNING,
        pathname="test_file.py",
        lineno=10,
        msg="Warning message",
        args=None,
        exc_info=None,
    )

    def check():
        return formatter.format(record)

    result = _without_no_color_env(check)

    if ANSI_YELLOW not in result:
        errmsg = "Expected ANSI_YELLOW in colored output for WARNING, got '{}'".format(
            repr(result)
        )
        raise AssertionError(errmsg)

    return


def test_colored_formatter_info_is_green():
    """
        Test that INFO level is colored green.
    """
    tty_stream = _FakeTTYStream()
    formatter = ColoredFormatter(use_colors=True, stream=tty_stream)

    record = logging.LogRecord(
        name="test.logger",
        level=logging.INFO,
        pathname="test_file.py",
        lineno=10,
        msg="Info message",
        args=None,
        exc_info=None,
    )

    def check():
        return formatter.format(record)

    result = _without_no_color_env(check)

    if ANSI_GREEN not in result:
        errmsg = "Expected ANSI_GREEN in colored output for INFO, got '{}'".format(
            repr(result)
        )
        raise AssertionError(errmsg)

    return


def test_colored_formatter_debug_is_cyan():
    """
        Test that DEBUG level is colored cyan.
    """
    tty_stream = _FakeTTYStream()
    formatter = ColoredFormatter(use_colors=True, stream=tty_stream)

    record = logging.LogRecord(
        name="test.logger",
        level=logging.DEBUG,
        pathname="test_file.py",
        lineno=10,
        msg="Debug message",
        args=None,
        exc_info=None,
    )

    def check():
        return formatter.format(record)

    result = _without_no_color_env(check)

    if ANSI_CYAN not in result:
        errmsg = "Expected ANSI_CYAN in colored output for DEBUG, got '{}'".format(
            repr(result)
        )
        raise AssertionError(errmsg)

    return


def test_colored_formatter_no_color_when_disabled():
    """
        Test that no ANSI codes appear when use_colors is False.
    """
    formatter = ColoredFormatter(use_colors=False)

    record = logging.LogRecord(
        name="test.logger",
        level=logging.ERROR,
        pathname="test_file.py",
        lineno=10,
        msg="Error message",
        args=None,
        exc_info=None,
    )

    result = formatter.format(record)

    if "\033[" in result:
        errmsg = "Expected no ANSI codes when colors disabled, got '{}'".format(
            repr(result)
        )
        raise AssertionError(errmsg)

    return


def test_colored_formatter_no_color_on_non_tty():
    """
        Test that no ANSI codes appear on a non-TTY stream.
    """
    non_tty_stream = _FakeNonTTYStream()
    formatter = ColoredFormatter(use_colors=True, stream=non_tty_stream)

    record = logging.LogRecord(
        name="test.logger",
        level=logging.ERROR,
        pathname="test_file.py",
        lineno=10,
        msg="Error message",
        args=None,
        exc_info=None,
    )

    result = formatter.format(record)

    if "\033[" in result:
        errmsg = "Expected no ANSI codes on non-TTY, got '{}'".format(
            repr(result)
        )
        raise AssertionError(errmsg)

    return


def test_log_level_colors_mapping():
    """
        Test that all standard log levels have color mappings.
    """
    expected_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

    for level in expected_levels:
        if level not in LOG_LEVEL_COLORS:
            errmsg = "Expected '{}' in LOG_LEVEL_COLORS".format(level)
            raise AssertionError(errmsg)

    return


# =============================================================================
# 19.4 - Tests for SQL Query Logging Option
# =============================================================================

def test_devlogger_enable_sql_logging():
    """
        Test that enable_sql_logging sets the SQL logger to DEBUG.
    """
    dev_logger = DevLogger(debug=True)

    dev_logger.enable_sql_logging()

    sql_logger = logging.getLogger(SQL_LOGGER_NAME)

    if sql_logger.level != logging.DEBUG:
        errmsg = "Expected SQL logger level {}, got {}".format(
            logging.DEBUG, sql_logger.level
        )
        raise AssertionError(errmsg)

    if dev_logger.sql_logging_enabled is not True:
        errmsg = "Expected sql_logging_enabled=True"
        raise AssertionError(errmsg)

    # Cleanup
    dev_logger.disable_sql_logging()

    return


def test_devlogger_enable_sql_logging_custom_level():
    """
        Test that enable_sql_logging accepts a custom level.
    """
    dev_logger = DevLogger(debug=True)

    dev_logger.enable_sql_logging(level="INFO")

    sql_logger = logging.getLogger(SQL_LOGGER_NAME)

    if sql_logger.level != logging.INFO:
        errmsg = "Expected SQL logger level {}, got {}".format(
            logging.INFO, sql_logger.level
        )
        raise AssertionError(errmsg)

    # Cleanup
    dev_logger.disable_sql_logging()

    return


def test_devlogger_disable_sql_logging():
    """
        Test that disable_sql_logging resets the SQL logger to WARNING.
    """
    dev_logger = DevLogger(debug=True)

    dev_logger.enable_sql_logging()
    dev_logger.disable_sql_logging()

    sql_logger = logging.getLogger(SQL_LOGGER_NAME)

    if sql_logger.level != logging.WARNING:
        errmsg = "Expected SQL logger level {}, got {}".format(
            logging.WARNING, sql_logger.level
        )
        raise AssertionError(errmsg)

    if dev_logger.sql_logging_enabled is not False:
        errmsg = "Expected sql_logging_enabled=False"
        raise AssertionError(errmsg)

    return


# =============================================================================
# 19.5 - Tests for --log-level CLI Option
# =============================================================================

def test_devlogger_log_level_option_info():
    """
        Test that log_level='INFO' is stored correctly.
    """
    dev_logger = DevLogger(debug=True, log_level="INFO")

    if dev_logger.log_level != "INFO":
        errmsg = "Expected log_level 'INFO', got '{}'".format(dev_logger.log_level)
        raise AssertionError(errmsg)

    return


def test_devlogger_log_level_option_case_insensitive():
    """
        Test that log_level is normalized to uppercase.
    """
    dev_logger = DevLogger(debug=True, log_level="info")

    if dev_logger.log_level != "INFO":
        errmsg = "Expected log_level 'INFO', got '{}'".format(dev_logger.log_level)
        raise AssertionError(errmsg)

    return


def test_devlogger_log_level_applied_on_setup():
    """
        Test that the configured log level is applied to the root logger.
    """
    _saved_logging = _detach_root_logger_handlers()

    dev_logger = DevLogger(debug=False, log_level="ERROR")

    try:
        dev_logger.setup()

        root_logger = logging.getLogger()

        if root_logger.level != logging.ERROR:
            errmsg = "Expected root logger level {}, got {}".format(
                logging.ERROR, root_logger.level
            )
            raise AssertionError(errmsg)
    finally:
        dev_logger.teardown()
        _restore_root_logger_handlers(_saved_logging)

    return


# =============================================================================
# 19.6 - Tests for --log-file CLI Option
# =============================================================================

def test_devlogger_log_file_property():
    """
        Test that the log_file property returns the configured path.
    """
    dev_logger = DevLogger(debug=True, log_file="/tmp/test.log")

    if dev_logger.log_file != "/tmp/test.log":
        errmsg = "Expected log_file '/tmp/test.log', got '{}'".format(
            dev_logger.log_file
        )
        raise AssertionError(errmsg)

    return


def test_devlogger_log_file_none_by_default():
    """
        Test that log_file is None when not configured.
    """
    dev_logger = DevLogger(debug=True)

    if dev_logger.log_file is not None:
        errmsg = "Expected log_file None, got '{}'".format(dev_logger.log_file)
        raise AssertionError(errmsg)

    return


def test_devlogger_setup_creates_file_handler():
    """
        Test that setup() creates a file handler when log_file is set.
    """
    _saved_logging = _detach_root_logger_handlers()

    tmp_file = tempfile.NamedTemporaryFile(
        mode="w", suffix=".log", delete=False
    )
    tmp_path = tmp_file.name
    tmp_file.close()

    dev_logger = DevLogger(debug=True, log_file=tmp_path, use_colors=False)

    try:
        dev_logger.setup()

        root_logger = logging.getLogger()

        file_handlers = [
            h for h in root_logger.handlers
            if isinstance(h, logging.FileHandler)
        ]

        if len(file_handlers) == 0:
            errmsg = "Expected at least one FileHandler on root logger"
            raise AssertionError(errmsg)
    finally:
        dev_logger.teardown()
        _restore_root_logger_handlers(_saved_logging)
        os.unlink(tmp_path)

    return


def test_devlogger_add_file_handler_writes_to_file():
    """
        Test that the file handler actually writes log messages to the file.
    """
    _saved_logging = _detach_root_logger_handlers()

    tmp_file = tempfile.NamedTemporaryFile(
        mode="w", suffix=".log", delete=False
    )
    tmp_path = tmp_file.name
    tmp_file.close()

    dev_logger = DevLogger(debug=True, use_colors=False)

    try:
        dev_logger.setup()
        dev_logger.add_file_handler(tmp_path)

        test_logger = logging.getLogger("test.file_handler")
        test_logger.debug("File handler test message")

        # Flush handlers
        for handler in logging.getLogger().handlers:
            handler.flush()

        with open(tmp_path, "r") as log_file:
            content = log_file.read()

        if "File handler test message" not in content:
            errmsg = "Expected log message in file, got '{}'".format(content)
            raise AssertionError(errmsg)
    finally:
        dev_logger.teardown()
        _restore_root_logger_handlers(_saved_logging)
        os.unlink(tmp_path)

    return


# =============================================================================
# 19.7 - Tests for Request ID Correlation
# =============================================================================

def test_get_request_id_default_is_none():
    """
        Test that the default request ID is None.
    """
    # Reset to default
    set_request_id(None)

    request_id = get_request_id()

    if request_id is not None:
        errmsg = "Expected None, got '{}'".format(request_id)
        raise AssertionError(errmsg)

    return


def test_set_and_get_request_id():
    """
        Test that set_request_id stores the value and get_request_id
        retrieves it.
    """
    set_request_id("abc12345")

    try:
        request_id = get_request_id()

        if request_id != "abc12345":
            errmsg = "Expected 'abc12345', got '{}'".format(request_id)
            raise AssertionError(errmsg)
    finally:
        set_request_id(None)

    return


def test_generate_request_id_returns_string():
    """
        Test that generate_request_id returns a non-empty string.
    """
    request_id = generate_request_id()

    if not isinstance(request_id, str):
        errmsg = "Expected str, got {}".format(type(request_id))
        raise AssertionError(errmsg)

    if len(request_id) == 0:
        errmsg = "Expected non-empty request ID"
        raise AssertionError(errmsg)

    return


def test_generate_request_id_is_8_chars():
    """
        Test that generate_request_id returns an 8-character string.
    """
    request_id = generate_request_id()

    if len(request_id) != 8:
        errmsg = "Expected 8 characters, got {} ({})".format(
            len(request_id), request_id
        )
        raise AssertionError(errmsg)

    return


def test_generate_request_id_unique():
    """
        Test that consecutive calls produce different IDs.
    """
    id_one = generate_request_id()
    id_two = generate_request_id()

    if id_one == id_two:
        errmsg = "Expected unique IDs, got '{}' twice".format(id_one)
        raise AssertionError(errmsg)

    return


def test_colored_formatter_includes_request_id():
    """
        Test that the ColoredFormatter includes the request ID in output.
    """
    set_request_id("req-test1")

    try:
        formatter = ColoredFormatter(use_colors=False)

        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="test_file.py",
            lineno=10,
            msg="Test message",
            args=None,
            exc_info=None,
        )

        result = formatter.format(record)

        if "req-test1" not in result:
            errmsg = "Expected 'req-test1' in formatted output, got '{}'".format(
                result
            )
            raise AssertionError(errmsg)
    finally:
        set_request_id(None)

    return


def test_colored_formatter_no_request_id_when_none():
    """
        Test that no request ID prefix appears when request ID is None.
    """
    set_request_id(None)

    formatter = ColoredFormatter(use_colors=False)

    record = logging.LogRecord(
        name="test.logger",
        level=logging.INFO,
        pathname="test_file.py",
        lineno=10,
        msg="Plain message",
        args=None,
        exc_info=None,
    )

    result = formatter.format(record)

    # Should not have the bracket prefix pattern
    if result.count("[") > 1:
        errmsg = "Expected no request ID prefix, got '{}'".format(result)
        raise AssertionError(errmsg)

    return


# =============================================================================
# Tests for from_config Factory
# =============================================================================

def test_from_config_with_logging_section():
    """
        Test that from_config reads the logging section correctly.
    """
    config = {
        "logging": {
            "level": "ERROR",
            "format": "%(message)s",
            "colors": False,
            "file": "/tmp/test.log",
        }
    }

    dev_logger = DevLogger.from_config(config, debug=True)

    if dev_logger.log_level != "ERROR":
        errmsg = "Expected log_level 'ERROR', got '{}'".format(dev_logger.log_level)
        raise AssertionError(errmsg)

    if dev_logger.log_format != "%(message)s":
        errmsg = "Expected format '%(message)s', got '{}'".format(dev_logger.log_format)
        raise AssertionError(errmsg)

    if dev_logger.use_colors is not False:
        errmsg = "Expected use_colors=False"
        raise AssertionError(errmsg)

    if dev_logger.log_file != "/tmp/test.log":
        errmsg = "Expected log_file '/tmp/test.log', got '{}'".format(
            dev_logger.log_file
        )
        raise AssertionError(errmsg)

    return


def test_from_config_with_empty_config():
    """
        Test that from_config uses defaults when config is empty.
    """
    config = {}

    dev_logger = DevLogger.from_config(config, debug=True)

    if dev_logger.log_level != "DEBUG":
        errmsg = "Expected log_level 'DEBUG', got '{}'".format(dev_logger.log_level)
        raise AssertionError(errmsg)

    if dev_logger.use_colors is not True:
        errmsg = "Expected use_colors=True"
        raise AssertionError(errmsg)

    return


def test_devlogger_teardown_removes_handlers():
    """
        Test that teardown removes all handlers added by DevLogger.
    """
    _saved_logging = _detach_root_logger_handlers()

    dev_logger = DevLogger(debug=True, use_colors=False)

    dev_logger.setup()

    root_logger = logging.getLogger()
    handler_count_before = len(root_logger.handlers)

    if handler_count_before == 0:
        errmsg = "Expected handlers after setup"
        raise AssertionError(errmsg)

    dev_logger.teardown()

    handler_count_after = len(root_logger.handlers)

    if handler_count_after != 0:
        errmsg = "Expected 0 handlers after teardown, got {}".format(
            handler_count_after
        )
        raise AssertionError(errmsg)

    _restore_root_logger_handlers(_saved_logging)

    return
