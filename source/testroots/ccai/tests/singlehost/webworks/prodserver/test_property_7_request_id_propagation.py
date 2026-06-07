"""
    Property-Based Tests for Request ID Propagation (Property 7).

    Property 7: Request ID Propagation
    For any incoming request, the server SHALL either use the provided
    X-Request-ID header value or generate a unique request ID, include
    this ID in all log entries for that request, and return it in the
    response X-Request-ID header.

    Validates: Requirements 8.1, 8.2, 8.3, 8.4
"""

import json
import random
import string
import uuid

from ccai.webworks.prodserver.requesttracer import RequestTracer
from ccai.webworks.prodserver.structuredlogger import StructuredLogger
from ccai.webworks.prodserver.serverconfig import ServerConfig


# =============================================================================
# Helpers
# =============================================================================

TRACE_HEADERS = [
    "X-Request-ID",
    "X-Correlation-ID",
    "X-Trace-ID",
]

LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


# =============================================================================
# Random Generators
# =============================================================================

def generate_request_id() -> str:
    """
        Generate a random request ID string.
    """
    styles = [
        lambda: str(uuid.uuid4()),
        lambda: "req-" + "".join(random.choices(string.hexdigits.lower(), k=12)),
        lambda: "".join(random.choices(string.ascii_lowercase + string.digits, k=random.randint(8, 32))),
    ]
    return random.choice(styles)()


def generate_message() -> str:
    """
        Generate a random log message.
    """
    length = random.randint(1, 80)
    return "".join(random.choices(string.ascii_letters + string.digits + " ", k=length))


def generate_headers_with_id(trace_header: str) -> dict:
    """
        Generate request headers containing a request ID.
    """
    request_id = generate_request_id()
    return {trace_header: request_id}, request_id


def generate_headers_without_id() -> dict:
    """
        Generate request headers without a request ID.
    """
    headers = {}
    if random.random() < 0.5:
        headers["Content-Type"] = random.choice(["text/html", "application/json"])
    if random.random() < 0.3:
        headers["Accept"] = "*/*"
    return headers


# =============================================================================
# Property-Based Tests
# =============================================================================

# Feature: production-server, Property 7: Request ID Propagation
# *For any* incoming request, the server SHALL either use the provided
# X-Request-ID header value or generate a unique request ID, include
# this ID in all log entries for that request, and return it in the
# response X-Request-ID header.
# **Validates: Requirements 8.1, 8.2, 8.3, 8.4**


def test_property_7_existing_request_id_preserved():
    """
        Property 7: Existing Request ID Preserved

        For any incoming request with an existing request ID header,
        the tracer SHALL use that exact ID rather than generating
        a new one.

        **Validates: Requirement 8.2**
    """
    for iteration in range(100):
        trace_header = random.choice(TRACE_HEADERS)
        config = ServerConfig(log_format="json", trace_header=trace_header)
        tracer = RequestTracer(config=config)

        headers, expected_id = generate_headers_with_id(trace_header)
        actual_id = tracer.get_or_create_request_id(headers)

        if actual_id != expected_id:
            errmsg = (
                f"Iteration {iteration}: expected existing request ID "
                f"'{expected_id}', got '{actual_id}' "
                f"(trace_header={trace_header})"
            )
            raise AssertionError(errmsg)

    return


def test_property_7_generated_request_id_is_unique():
    """
        Property 7: Generated Request ID Uniqueness

        For any incoming request without a request ID header,
        the tracer SHALL generate a unique request ID.

        **Validates: Requirement 8.1**
    """
    config = ServerConfig(log_format="json", trace_header="X-Request-ID")
    tracer = RequestTracer(config=config)

    generated_ids = set()

    for iteration in range(100):
        headers = generate_headers_without_id()
        request_id = tracer.get_or_create_request_id(headers)

        if request_id in generated_ids:
            errmsg = (
                f"Iteration {iteration}: generated duplicate request ID "
                f"'{request_id}'"
            )
            raise AssertionError(errmsg)

        generated_ids.add(request_id)

        if len(request_id.strip()) == 0:
            errmsg = (
                f"Iteration {iteration}: generated empty request ID"
            )
            raise AssertionError(errmsg)

    return


def test_property_7_request_id_in_log_entries():
    """
        Property 7: Request ID in Log Entries

        For any request, the request_id SHALL be present in all
        log entries when set via the structured logger context.

        **Validates: Requirement 8.3**
    """
    for iteration in range(100):
        trace_header = random.choice(TRACE_HEADERS)
        config = ServerConfig(
            log_format="json",
            log_level="DEBUG",
            trace_header=trace_header
        )
        tracer = RequestTracer(config=config)
        logger = StructuredLogger(config=config)

        # Randomly decide if request has existing ID or not
        if random.random() < 0.5:
            headers, _ = generate_headers_with_id(trace_header)
        else:
            headers = generate_headers_without_id()

        request_id = tracer.get_or_create_request_id(headers)
        logger.set_context(request_id=request_id)

        # Log multiple messages and verify request_id in each
        num_logs = random.randint(1, 5)
        for log_idx in range(num_logs):
            level = random.choice(LOG_LEVELS)
            message = generate_message()

            result = logger.log(level, message)
            parsed = json.loads(result)

            actual_id = parsed.get("request_id")
            if actual_id != request_id:
                errmsg = (
                    f"Iteration {iteration}, log {log_idx}: expected "
                    f"request_id '{request_id}' in log entry, "
                    f"got '{actual_id}'"
                )
                raise AssertionError(errmsg)

        logger.clear_context()

    return


def test_property_7_request_id_in_response_headers():
    """
        Property 7: Request ID in Response Headers

        For any request, the request_id SHALL be included in the
        response headers using the configured trace header name.

        **Validates: Requirement 8.4**
    """
    for iteration in range(100):
        trace_header = random.choice(TRACE_HEADERS)
        config = ServerConfig(
            log_format="json",
            trace_header=trace_header
        )
        tracer = RequestTracer(config=config)

        # Randomly decide if request has existing ID or not
        if random.random() < 0.5:
            headers, _ = generate_headers_with_id(trace_header)
        else:
            headers = generate_headers_without_id()

        request_id = tracer.get_or_create_request_id(headers)

        response_headers = {}
        tracer.inject_response_headers(response_headers, request_id)

        actual_id = response_headers.get(trace_header)
        if actual_id != request_id:
            errmsg = (
                f"Iteration {iteration}: expected response header "
                f"'{trace_header}' = '{request_id}', got '{actual_id}'"
            )
            raise AssertionError(errmsg)

    return


def test_property_7_request_id_consistent_across_log_and_response():
    """
        Property 7: Request ID Consistency

        For any request, the request_id in log entries SHALL match
        the request_id in response headers.

        **Validates: Requirements 8.3, 8.4**
    """
    for iteration in range(100):
        trace_header = random.choice(TRACE_HEADERS)
        config = ServerConfig(
            log_format="json",
            log_level="DEBUG",
            trace_header=trace_header
        )
        tracer = RequestTracer(config=config)
        logger = StructuredLogger(config=config)

        # Simulate request flow
        if random.random() < 0.5:
            headers, _ = generate_headers_with_id(trace_header)
        else:
            headers = generate_headers_without_id()

        request_id = tracer.get_or_create_request_id(headers)

        # Propagate to logger
        logger.set_context(request_id=request_id)
        log_result = logger.log("INFO", generate_message())
        log_parsed = json.loads(log_result)
        log_request_id = log_parsed.get("request_id")

        # Inject into response
        response_headers = {}
        tracer.inject_response_headers(response_headers, request_id)
        response_request_id = response_headers.get(trace_header)

        if log_request_id != response_request_id:
            errmsg = (
                f"Iteration {iteration}: log request_id '{log_request_id}' "
                f"does not match response header '{response_request_id}'"
            )
            raise AssertionError(errmsg)

        logger.clear_context()

    return


def test_property_7_access_log_includes_request_id():
    """
        Property 7: Access Log Request ID

        For any access log entry, the request_id SHALL be present
        when set via persistent context.

        **Validates: Requirements 8.3**
    """
    http_methods = ["GET", "POST", "PUT", "DELETE", "PATCH"]
    endpoints = ["/api/users", "/api/items", "/health", "/", "/api/auth"]
    status_codes = [200, 201, 204, 400, 401, 404, 500]

    for iteration in range(100):
        config = ServerConfig(
            log_format="json",
            log_level="DEBUG",
            trace_header="X-Request-ID"
        )
        tracer = RequestTracer(config=config)
        logger = StructuredLogger(config=config)

        headers = generate_headers_without_id()
        request_id = tracer.get_or_create_request_id(headers)
        logger.set_context(request_id=request_id)

        method = random.choice(http_methods)
        endpoint = random.choice(endpoints)
        status_code = random.choice(status_codes)
        latency = round(random.uniform(0.1, 5000.0), 2)

        result = logger.access_log(method, endpoint, status_code, latency)
        parsed = json.loads(result)

        actual_id = parsed.get("request_id")
        if actual_id != request_id:
            errmsg = (
                f"Iteration {iteration}: expected request_id '{request_id}' "
                f"in access log, got '{actual_id}'"
            )
            raise AssertionError(errmsg)

        logger.clear_context()

    return
