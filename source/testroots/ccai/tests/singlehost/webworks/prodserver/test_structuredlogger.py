"""
    Tests for the production server StructuredLogger class.

    This module contains unit tests for structured logging functionality
    including JSON and standard log formats, log entry formatting with
    timestamp, level, message, and context fields, configurable output
    destinations, and access/error log file support.
"""

import json
import os
import tempfile

from ccai.webworks.prodserver.structuredlogger import StructuredLogger
from ccai.webworks.prodserver.serverconfig import ServerConfig


# =============================================================================
# Unit Tests for StructuredLogger - JSON Format
# =============================================================================

def test_log_json_format_returns_valid_json():
    """
        Test that log with JSON format returns a valid JSON string.
    """
    config = ServerConfig(log_format="json")
    logger = StructuredLogger(config=config)

    result = logger.log("INFO", "test message")

    try:
        json.loads(result)
    except json.JSONDecodeError:
        errmsg = f"Expected valid JSON, got: {result}"
        raise AssertionError(errmsg)

    return


def test_log_json_format_contains_timestamp():
    """
        Test that JSON log entries contain a timestamp field.
    """
    config = ServerConfig(log_format="json")
    logger = StructuredLogger(config=config)

    result = logger.log("INFO", "test message")
    parsed = json.loads(result)

    if "timestamp" not in parsed:
        errmsg = "Expected 'timestamp' field in JSON log entry"
        raise AssertionError(errmsg)

    return


def test_log_json_format_contains_level():
    """
        Test that JSON log entries contain a level field.
    """
    config = ServerConfig(log_format="json")
    logger = StructuredLogger(config=config)

    result = logger.log("WARNING", "test message")
    parsed = json.loads(result)

    if parsed.get("level") != "WARNING":
        errmsg = f"Expected level 'WARNING', got '{parsed.get('level')}'"
        raise AssertionError(errmsg)

    return


def test_log_json_format_contains_message():
    """
        Test that JSON log entries contain a message field.
    """
    config = ServerConfig(log_format="json")
    logger = StructuredLogger(config=config)

    result = logger.log("INFO", "hello world")
    parsed = json.loads(result)

    if parsed.get("message") != "hello world":
        errmsg = f"Expected message 'hello world', got '{parsed.get('message')}'"
        raise AssertionError(errmsg)

    return


def test_log_json_format_contains_context_fields():
    """
        Test that JSON log entries include additional context fields.
    """
    config = ServerConfig(log_format="json")
    logger = StructuredLogger(config=config)

    result = logger.log("INFO", "test", request_id="abc-123", worker_id=5)
    parsed = json.loads(result)

    if parsed.get("request_id") != "abc-123":
        errmsg = f"Expected request_id 'abc-123', got '{parsed.get('request_id')}'"
        raise AssertionError(errmsg)

    if parsed.get("worker_id") != 5:
        errmsg = f"Expected worker_id 5, got '{parsed.get('worker_id')}'"
        raise AssertionError(errmsg)

    return


def test_log_json_format_level_is_uppercase():
    """
        Test that the level field is always uppercase in JSON format.
    """
    config = ServerConfig(log_format="json")
    logger = StructuredLogger(config=config)

    result = logger.log("info", "test message")
    parsed = json.loads(result)

    if parsed.get("level") != "INFO":
        errmsg = f"Expected level 'INFO', got '{parsed.get('level')}'"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for StructuredLogger - Standard Format
# =============================================================================

def test_log_standard_format_contains_timestamp():
    """
        Test that standard format log entries contain a timestamp.
    """
    config = ServerConfig(log_format="standard")
    logger = StructuredLogger(config=config)

    result = logger.log("INFO", "test message")

    if "[" not in result or "]" not in result:
        errmsg = f"Expected timestamp in brackets, got: {result}"
        raise AssertionError(errmsg)

    return


def test_log_standard_format_contains_level():
    """
        Test that standard format log entries contain the level.
    """
    config = ServerConfig(log_format="standard")
    logger = StructuredLogger(config=config)

    result = logger.log("ERROR", "test message")

    if "ERROR" not in result:
        errmsg = f"Expected 'ERROR' in standard log entry, got: {result}"
        raise AssertionError(errmsg)

    return


def test_log_standard_format_contains_message():
    """
        Test that standard format log entries contain the message.
    """
    config = ServerConfig(log_format="standard")
    logger = StructuredLogger(config=config)

    result = logger.log("INFO", "hello world")

    if "hello world" not in result:
        errmsg = f"Expected 'hello world' in standard log entry, got: {result}"
        raise AssertionError(errmsg)

    return


def test_log_standard_format_contains_context_fields():
    """
        Test that standard format log entries include context key=value pairs.
    """
    config = ServerConfig(log_format="standard")
    logger = StructuredLogger(config=config)

    result = logger.log("INFO", "test", request_id="abc-123")

    if "request_id=abc-123" not in result:
        errmsg = f"Expected 'request_id=abc-123' in standard log entry, got: {result}"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for StructuredLogger - Persistent Context
# =============================================================================

def test_set_context_includes_fields_in_log():
    """
        Test that persistent context fields appear in log entries.
    """
    config = ServerConfig(log_format="json")
    logger = StructuredLogger(config=config)

    logger.set_context(worker_id=3)
    result = logger.log("INFO", "test message")
    parsed = json.loads(result)

    if parsed.get("worker_id") != 3:
        errmsg = f"Expected worker_id 3, got '{parsed.get('worker_id')}'"
        raise AssertionError(errmsg)

    return


def test_set_context_request_id_in_log():
    """
        Test that persistent request_id appears in log entries.
    """
    config = ServerConfig(log_format="json")
    logger = StructuredLogger(config=config)

    logger.set_context(request_id="req-456")
    result = logger.log("INFO", "handling request")
    parsed = json.loads(result)

    if parsed.get("request_id") != "req-456":
        errmsg = f"Expected request_id 'req-456', got '{parsed.get('request_id')}'"
        raise AssertionError(errmsg)

    return


def test_clear_context_removes_fields():
    """
        Test that clear_context removes persistent context fields.
    """
    config = ServerConfig(log_format="json")
    logger = StructuredLogger(config=config)

    logger.set_context(worker_id=3)
    logger.clear_context()
    result = logger.log("INFO", "test message")
    parsed = json.loads(result)

    if "worker_id" in parsed:
        errmsg = "Expected worker_id to be absent after clear_context"
        raise AssertionError(errmsg)

    return


def test_context_override_by_log_kwargs():
    """
        Test that log kwargs override persistent context fields.
    """
    config = ServerConfig(log_format="json")
    logger = StructuredLogger(config=config)

    logger.set_context(worker_id=1)
    result = logger.log("INFO", "test", worker_id=99)
    parsed = json.loads(result)

    if parsed.get("worker_id") != 99:
        errmsg = f"Expected worker_id 99 (override), got '{parsed.get('worker_id')}'"
        raise AssertionError(errmsg)

    return


def test_get_context_returns_copy():
    """
        Test that get_context returns a copy of the persistent context.
    """
    config = ServerConfig(log_format="json")
    logger = StructuredLogger(config=config)

    logger.set_context(worker_id=5, request_id="abc")
    ctx = logger.get_context()

    if ctx.get("worker_id") != 5:
        errmsg = f"Expected worker_id 5, got '{ctx.get('worker_id')}'"
        raise AssertionError(errmsg)

    if ctx.get("request_id") != "abc":
        errmsg = f"Expected request_id 'abc', got '{ctx.get('request_id')}'"
        raise AssertionError(errmsg)

    # Modifying the returned dict should not affect the logger
    ctx["worker_id"] = 999
    ctx2 = logger.get_context()

    if ctx2.get("worker_id") != 5:
        errmsg = "Expected get_context to return a copy, not a reference"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for StructuredLogger - Log Level Filtering
# =============================================================================

def test_log_level_filters_below_threshold():
    """
        Test that messages below the configured log level are filtered.
    """
    config = ServerConfig(log_format="json", log_level="WARNING")
    logger = StructuredLogger(config=config)

    result = logger.log("DEBUG", "should be filtered")

    if result != "":
        errmsg = f"Expected empty string for filtered log, got: {result}"
        raise AssertionError(errmsg)

    return


def test_log_level_allows_at_threshold():
    """
        Test that messages at the configured log level are allowed.
    """
    config = ServerConfig(log_format="json", log_level="WARNING")
    logger = StructuredLogger(config=config)

    result = logger.log("WARNING", "should pass")

    if result == "":
        errmsg = "Expected non-empty string for log at threshold level"
        raise AssertionError(errmsg)

    return


def test_log_level_allows_above_threshold():
    """
        Test that messages above the configured log level are allowed.
    """
    config = ServerConfig(log_format="json", log_level="WARNING")
    logger = StructuredLogger(config=config)

    result = logger.log("ERROR", "should pass")

    if result == "":
        errmsg = "Expected non-empty string for log above threshold level"
        raise AssertionError(errmsg)

    return


def test_log_level_info_filters_debug():
    """
        Test that INFO level filters DEBUG messages.
    """
    config = ServerConfig(log_format="json", log_level="INFO")
    logger = StructuredLogger(config=config)

    result = logger.log("DEBUG", "debug message")

    if result != "":
        errmsg = f"Expected empty string for DEBUG at INFO level, got: {result}"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for StructuredLogger - Access Log
# =============================================================================

def test_access_log_returns_formatted_entry():
    """
        Test that access_log returns a formatted log entry.
    """
    config = ServerConfig(log_format="json")
    logger = StructuredLogger(config=config)

    result = logger.access_log("GET", "/api/users", 200, 15.5)
    parsed = json.loads(result)

    if parsed.get("method") != "GET":
        errmsg = f"Expected method 'GET', got '{parsed.get('method')}'"
        raise AssertionError(errmsg)

    if parsed.get("path") != "/api/users":
        errmsg = f"Expected path '/api/users', got '{parsed.get('path')}'"
        raise AssertionError(errmsg)

    if parsed.get("status_code") != 200:
        errmsg = f"Expected status_code 200, got '{parsed.get('status_code')}'"
        raise AssertionError(errmsg)

    return


def test_access_log_includes_latency():
    """
        Test that access_log includes latency_ms in the entry.
    """
    config = ServerConfig(log_format="json")
    logger = StructuredLogger(config=config)

    result = logger.access_log("POST", "/api/items", 201, 42.75)
    parsed = json.loads(result)

    if parsed.get("latency_ms") != 42.75:
        errmsg = f"Expected latency_ms 42.75, got '{parsed.get('latency_ms')}'"
        raise AssertionError(errmsg)

    return


def test_access_log_includes_persistent_context():
    """
        Test that access_log includes persistent context fields.
    """
    config = ServerConfig(log_format="json")
    logger = StructuredLogger(config=config)

    logger.set_context(worker_id=2, request_id="req-789")
    result = logger.access_log("GET", "/health", 200, 1.0)
    parsed = json.loads(result)

    if parsed.get("worker_id") != 2:
        errmsg = f"Expected worker_id 2, got '{parsed.get('worker_id')}'"
        raise AssertionError(errmsg)

    if parsed.get("request_id") != "req-789":
        errmsg = f"Expected request_id 'req-789', got '{parsed.get('request_id')}'"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for StructuredLogger - Error Log
# =============================================================================

def test_error_log_returns_formatted_entry():
    """
        Test that error_log returns a formatted log entry.
    """
    config = ServerConfig(log_format="json")
    logger = StructuredLogger(config=config)

    exc = ValueError("something went wrong")
    result = logger.error_log(exc)
    parsed = json.loads(result)

    if parsed.get("level") != "ERROR":
        errmsg = f"Expected level 'ERROR', got '{parsed.get('level')}'"
        raise AssertionError(errmsg)

    if parsed.get("exception_type") != "ValueError":
        errmsg = f"Expected exception_type 'ValueError', got '{parsed.get('exception_type')}'"
        raise AssertionError(errmsg)

    return


def test_error_log_includes_exception_message():
    """
        Test that error_log includes the exception message.
    """
    config = ServerConfig(log_format="json")
    logger = StructuredLogger(config=config)

    exc = RuntimeError("connection refused")
    result = logger.error_log(exc)
    parsed = json.loads(result)

    if parsed.get("exception_message") != "connection refused":
        errmsg = f"Expected exception_message 'connection refused', got '{parsed.get('exception_message')}'"
        raise AssertionError(errmsg)

    return


def test_error_log_custom_message():
    """
        Test that error_log supports a custom message override.
    """
    config = ServerConfig(log_format="json")
    logger = StructuredLogger(config=config)

    exc = ValueError("original")
    result = logger.error_log(exc, message="custom error message")
    parsed = json.loads(result)

    if parsed.get("message") != "custom error message":
        errmsg = f"Expected message 'custom error message', got '{parsed.get('message')}'"
        raise AssertionError(errmsg)

    return


def test_error_log_includes_persistent_context():
    """
        Test that error_log includes persistent context fields.
    """
    config = ServerConfig(log_format="json")
    logger = StructuredLogger(config=config)

    logger.set_context(worker_id=7)
    exc = ValueError("test")
    result = logger.error_log(exc)
    parsed = json.loads(result)

    if parsed.get("worker_id") != 7:
        errmsg = f"Expected worker_id 7, got '{parsed.get('worker_id')}'"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for StructuredLogger - File Output
# =============================================================================

def test_access_log_writes_to_file():
    """
        Test that access_log writes to the configured access log file.
    """
    with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        config = ServerConfig(log_format="json", access_log=tmp_path)
        logger = StructuredLogger(config=config)
        logger.open_log_files()

        logger.access_log("GET", "/api/test", 200, 5.0)

        logger.close_log_files()

        with open(tmp_path, "r", encoding="utf-8") as f:
            content = f.read()

        if content.strip() == "":
            errmsg = "Expected access log file to contain content"
            raise AssertionError(errmsg)

        parsed = json.loads(content.strip())
        if parsed.get("method") != "GET":
            errmsg = f"Expected method 'GET' in access log file, got '{parsed.get('method')}'"
            raise AssertionError(errmsg)
    finally:
        os.unlink(tmp_path)

    return


def test_error_log_writes_to_file():
    """
        Test that error_log writes to the configured error log file.
    """
    with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        config = ServerConfig(log_format="json", error_log=tmp_path)
        logger = StructuredLogger(config=config)
        logger.open_log_files()

        exc = ValueError("test error")
        logger.error_log(exc)

        logger.close_log_files()

        with open(tmp_path, "r", encoding="utf-8") as f:
            content = f.read()

        if content.strip() == "":
            errmsg = "Expected error log file to contain content"
            raise AssertionError(errmsg)

        parsed = json.loads(content.strip())
        if parsed.get("level") != "ERROR":
            errmsg = f"Expected level 'ERROR' in error log file, got '{parsed.get('level')}'"
            raise AssertionError(errmsg)
    finally:
        os.unlink(tmp_path)

    return


def test_close_log_files_closes_handles():
    """
        Test that close_log_files properly closes file handles.
    """
    with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        config = ServerConfig(log_format="json", access_log=tmp_path)
        logger = StructuredLogger(config=config)
        logger.open_log_files()
        logger.close_log_files()

        if logger._access_log_file is not None:
            errmsg = "Expected access log file handle to be None after close"
            raise AssertionError(errmsg)
    finally:
        os.unlink(tmp_path)

    return


# =============================================================================
# Unit Tests for StructuredLogger - Properties
# =============================================================================

def test_log_format_property():
    """
        Test that log_format property returns the configured format.
    """
    config = ServerConfig(log_format="json")
    logger = StructuredLogger(config=config)

    if logger.log_format != "json":
        errmsg = f"Expected log_format 'json', got '{logger.log_format}'"
        raise AssertionError(errmsg)

    return


def test_log_level_property():
    """
        Test that log_level property returns the configured level.
    """
    config = ServerConfig(log_level="WARNING")
    logger = StructuredLogger(config=config)

    if logger.log_level != "WARNING":
        errmsg = f"Expected log_level 'WARNING', got '{logger.log_level}'"
        raise AssertionError(errmsg)

    return
