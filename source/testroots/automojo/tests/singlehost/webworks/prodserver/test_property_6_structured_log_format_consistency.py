"""
    Property-Based Tests for Structured Log Format Consistency (Property 6).

    Property 6: Structured Log Format Consistency
    For any log entry with JSON format enabled, the output SHALL be valid
    JSON containing timestamp, level, message, and context fields, with
    request_id present for all request-related logs.

    Validates: Requirements 7.1, 7.2, 7.3, 7.4
"""

import json
import random
import string

from automojo.webworks.prodserver.structuredlogger import StructuredLogger
from automojo.webworks.prodserver.serverconfig import ServerConfig


# =============================================================================
# Helpers
# =============================================================================

LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

HTTP_METHODS = ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"]

ENDPOINTS = [
    "/api/users",
    "/api/items",
    "/api/orders",
    "/api/products",
    "/api/auth/login",
    "/health",
    "/metrics",
    "/",
]

STATUS_CODES = [200, 201, 204, 301, 400, 401, 403, 404, 500, 502, 503]


# =============================================================================
# Random Generators
# =============================================================================

def generate_level() -> str:
    """
        Generate a random log level.
    """
    return random.choice(LOG_LEVELS)


def generate_message() -> str:
    """
        Generate a random log message.
    """
    length = random.randint(1, 100)
    return "".join(random.choices(string.ascii_letters + string.digits + " ", k=length))


def generate_request_id() -> str:
    """
        Generate a random request ID.
    """
    return "req-" + "".join(random.choices(string.hexdigits.lower(), k=12))


def generate_worker_id() -> int:
    """
        Generate a random worker ID.
    """
    return random.randint(1, 100)


def generate_context() -> dict:
    """
        Generate a random context dictionary with 0-5 extra fields.
    """
    ctx = {}
    num_fields = random.randint(0, 5)
    for _ in range(num_fields):
        key = "".join(random.choices(string.ascii_lowercase, k=random.randint(3, 10)))
        ctx[key] = random.choice([
            random.randint(0, 1000),
            round(random.uniform(0.0, 100.0), 2),
            "".join(random.choices(string.ascii_letters, k=random.randint(1, 20))),
            True,
            False,
        ])
    return ctx


# =============================================================================
# Property-Based Tests
# =============================================================================

# Feature: production-server, Property 6: Structured Log Format Consistency
# *For any* log entry with JSON format enabled, the output SHALL be valid
# JSON containing timestamp, level, message, and context fields, with
# request_id present for all request-related logs.
# **Validates: Requirements 7.1, 7.2, 7.3, 7.4**


def test_property_6_json_output_is_valid_json():
    """
        Property 6: Valid JSON Output

        For any log level and message, the JSON-formatted output
        SHALL be valid JSON.

        **Validates: Requirement 7.1**
    """
    for iteration in range(100):
        config = ServerConfig(log_format="json", log_level="DEBUG")
        logger = StructuredLogger(config=config)

        level = generate_level()
        message = generate_message()
        context = generate_context()

        result = logger.log(level, message, **context)

        try:
            parsed = json.loads(result)
        except json.JSONDecodeError as exc:
            errmsg = (
                f"Iteration {iteration}: expected valid JSON for level={level}, "
                f"message='{message[:30]}...', got JSONDecodeError: {exc}"
            )
            raise AssertionError(errmsg)

    return


def test_property_6_json_contains_required_fields():
    """
        Property 6: Required Fields Present

        For any log entry with JSON format, the output SHALL contain
        timestamp, level, and message fields.

        **Validates: Requirement 7.2**
    """
    required_fields = ["timestamp", "level", "message"]

    for iteration in range(100):
        config = ServerConfig(log_format="json", log_level="DEBUG")
        logger = StructuredLogger(config=config)

        level = generate_level()
        message = generate_message()

        result = logger.log(level, message)
        parsed = json.loads(result)

        for field in required_fields:
            if field not in parsed:
                errmsg = (
                    f"Iteration {iteration}: required field '{field}' missing "
                    f"from JSON log entry for level={level}"
                )
                raise AssertionError(errmsg)

    return


def test_property_6_json_level_matches_input():
    """
        Property 6: Level Field Matches Input

        For any log entry, the level field SHALL match the input
        level in uppercase form.

        **Validates: Requirement 7.2**
    """
    for iteration in range(100):
        config = ServerConfig(log_format="json", log_level="DEBUG")
        logger = StructuredLogger(config=config)

        level = generate_level()
        message = generate_message()

        result = logger.log(level, message)
        parsed = json.loads(result)

        expected_level = level.upper()
        actual_level = parsed.get("level")

        if actual_level != expected_level:
            errmsg = (
                f"Iteration {iteration}: expected level '{expected_level}', "
                f"got '{actual_level}'"
            )
            raise AssertionError(errmsg)

    return


def test_property_6_json_message_matches_input():
    """
        Property 6: Message Field Matches Input

        For any log entry, the message field SHALL match the input message.

        **Validates: Requirement 7.2**
    """
    for iteration in range(100):
        config = ServerConfig(log_format="json", log_level="DEBUG")
        logger = StructuredLogger(config=config)

        level = generate_level()
        message = generate_message()

        result = logger.log(level, message)
        parsed = json.loads(result)

        actual_message = parsed.get("message")

        if actual_message != message:
            errmsg = (
                f"Iteration {iteration}: expected message '{message[:30]}...', "
                f"got '{str(actual_message)[:30]}...'"
            )
            raise AssertionError(errmsg)

    return


def test_property_6_request_id_present_in_request_logs():
    """
        Property 6: Request ID in Request-Related Logs

        For any request-related log entry, the request_id field
        SHALL be present when set via persistent context.

        **Validates: Requirement 7.3**
    """
    for iteration in range(100):
        config = ServerConfig(log_format="json", log_level="DEBUG")
        logger = StructuredLogger(config=config)

        request_id = generate_request_id()
        logger.set_context(request_id=request_id)

        level = generate_level()
        message = generate_message()

        result = logger.log(level, message)
        parsed = json.loads(result)

        actual_request_id = parsed.get("request_id")

        if actual_request_id != request_id:
            errmsg = (
                f"Iteration {iteration}: expected request_id '{request_id}', "
                f"got '{actual_request_id}'"
            )
            raise AssertionError(errmsg)

    return


def test_property_6_worker_id_present_in_worker_logs():
    """
        Property 6: Worker ID in Worker Logs

        For any log entry with worker_id set via persistent context,
        the worker_id field SHALL be present in the output.

        **Validates: Requirement 7.4**
    """
    for iteration in range(100):
        config = ServerConfig(log_format="json", log_level="DEBUG")
        logger = StructuredLogger(config=config)

        worker_id = generate_worker_id()
        logger.set_context(worker_id=worker_id)

        level = generate_level()
        message = generate_message()

        result = logger.log(level, message)
        parsed = json.loads(result)

        actual_worker_id = parsed.get("worker_id")

        if actual_worker_id != worker_id:
            errmsg = (
                f"Iteration {iteration}: expected worker_id {worker_id}, "
                f"got {actual_worker_id}"
            )
            raise AssertionError(errmsg)

    return


def test_property_6_context_fields_preserved_in_json():
    """
        Property 6: Context Fields Preserved

        For any additional context fields provided to a log call,
        all fields SHALL be present in the JSON output.

        **Validates: Requirements 7.2, 7.3, 7.4**
    """
    for iteration in range(100):
        config = ServerConfig(log_format="json", log_level="DEBUG")
        logger = StructuredLogger(config=config)

        level = generate_level()
        message = generate_message()
        context = generate_context()

        result = logger.log(level, message, **context)
        parsed = json.loads(result)

        for key, value in context.items():
            if key not in parsed:
                errmsg = (
                    f"Iteration {iteration}: context field '{key}' missing "
                    f"from JSON output"
                )
                raise AssertionError(errmsg)

            if parsed[key] != value:
                errmsg = (
                    f"Iteration {iteration}: context field '{key}' expected "
                    f"'{value}', got '{parsed[key]}'"
                )
                raise AssertionError(errmsg)

    return


def test_property_6_access_log_json_is_valid():
    """
        Property 6: Access Log JSON Validity

        For any access log entry with JSON format, the output SHALL
        be valid JSON containing method, path, status_code, and
        latency_ms fields.

        **Validates: Requirements 7.1, 7.2**
    """
    for iteration in range(100):
        config = ServerConfig(log_format="json", log_level="DEBUG")
        logger = StructuredLogger(config=config)

        method = random.choice(HTTP_METHODS)
        endpoint = random.choice(ENDPOINTS)
        status_code = random.choice(STATUS_CODES)
        latency = round(random.uniform(0.1, 5000.0), 2)

        request_id = generate_request_id()
        worker_id = generate_worker_id()
        logger.set_context(request_id=request_id, worker_id=worker_id)

        result = logger.access_log(method, endpoint, status_code, latency)

        try:
            parsed = json.loads(result)
        except json.JSONDecodeError as exc:
            errmsg = (
                f"Iteration {iteration}: expected valid JSON for access log, "
                f"got JSONDecodeError: {exc}"
            )
            raise AssertionError(errmsg)

        # Verify required access log fields
        if parsed.get("method") != method:
            errmsg = (
                f"Iteration {iteration}: expected method '{method}', "
                f"got '{parsed.get('method')}'"
            )
            raise AssertionError(errmsg)

        if parsed.get("path") != endpoint:
            errmsg = (
                f"Iteration {iteration}: expected path '{endpoint}', "
                f"got '{parsed.get('path')}'"
            )
            raise AssertionError(errmsg)

        if parsed.get("status_code") != status_code:
            errmsg = (
                f"Iteration {iteration}: expected status_code {status_code}, "
                f"got {parsed.get('status_code')}"
            )
            raise AssertionError(errmsg)

        # Verify request_id and worker_id from persistent context
        if parsed.get("request_id") != request_id:
            errmsg = (
                f"Iteration {iteration}: expected request_id '{request_id}', "
                f"got '{parsed.get('request_id')}'"
            )
            raise AssertionError(errmsg)

        if parsed.get("worker_id") != worker_id:
            errmsg = (
                f"Iteration {iteration}: expected worker_id {worker_id}, "
                f"got {parsed.get('worker_id')}"
            )
            raise AssertionError(errmsg)

    return


def test_property_6_timestamp_is_iso_format():
    """
        Property 6: Timestamp ISO Format

        For any log entry, the timestamp field SHALL be in ISO 8601
        format.

        **Validates: Requirement 7.2**
    """
    from datetime import datetime

    for iteration in range(100):
        config = ServerConfig(log_format="json", log_level="DEBUG")
        logger = StructuredLogger(config=config)

        level = generate_level()
        message = generate_message()

        result = logger.log(level, message)
        parsed = json.loads(result)

        timestamp_str = parsed.get("timestamp", "")

        try:
            datetime.fromisoformat(timestamp_str)
        except ValueError:
            errmsg = (
                f"Iteration {iteration}: expected ISO 8601 timestamp, "
                f"got '{timestamp_str}'"
            )
            raise AssertionError(errmsg)

    return
