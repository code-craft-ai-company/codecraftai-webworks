"""
    Tests for the production server RequestTracer class.

    This module contains unit tests for request tracing functionality
    including request ID generation, header extraction, response header
    injection, span creation, W3C traceparent parsing, and trace export.
"""

from automojo.webworks.prodserver.requesttracer import RequestTracer, Span
from automojo.webworks.prodserver.serverconfig import ServerConfig


# =============================================================================
# Unit Tests for RequestTracer - Request ID Generation
# =============================================================================

def test_generate_request_id_returns_string():
    """
        Test that generate_request_id returns a non-empty string.
    """
    config = ServerConfig()
    tracer = RequestTracer(config=config)

    request_id = tracer.generate_request_id()

    if not isinstance(request_id, str):
        errmsg = f"Expected string, got {type(request_id)}"
        raise AssertionError(errmsg)

    if len(request_id) == 0:
        errmsg = "Expected non-empty request ID"
        raise AssertionError(errmsg)

    return


def test_generate_request_id_is_unique():
    """
        Test that consecutive request IDs are unique.
    """
    config = ServerConfig()
    tracer = RequestTracer(config=config)

    ids = set()
    for _ in range(100):
        ids.add(tracer.generate_request_id())

    if len(ids) != 100:
        errmsg = f"Expected 100 unique IDs, got {len(ids)}"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for RequestTracer - Get or Create Request ID
# =============================================================================

def test_get_or_create_uses_existing_header():
    """
        Test that get_or_create_request_id uses an existing X-Request-ID header.
    """
    config = ServerConfig(trace_header="X-Request-ID")
    tracer = RequestTracer(config=config)

    headers = {"X-Request-ID": "existing-id-123"}
    request_id = tracer.get_or_create_request_id(headers)

    if request_id != "existing-id-123":
        errmsg = f"Expected 'existing-id-123', got '{request_id}'"
        raise AssertionError(errmsg)

    return


def test_get_or_create_case_insensitive_header():
    """
        Test that header lookup is case-insensitive.
    """
    config = ServerConfig(trace_header="X-Request-ID")
    tracer = RequestTracer(config=config)

    headers = {"x-request-id": "lower-case-id"}
    request_id = tracer.get_or_create_request_id(headers)

    if request_id != "lower-case-id":
        errmsg = f"Expected 'lower-case-id', got '{request_id}'"
        raise AssertionError(errmsg)

    return


def test_get_or_create_generates_when_missing():
    """
        Test that a new ID is generated when the header is missing.
    """
    config = ServerConfig(trace_header="X-Request-ID")
    tracer = RequestTracer(config=config)

    headers = {"Content-Type": "application/json"}
    request_id = tracer.get_or_create_request_id(headers)

    if len(request_id) == 0:
        errmsg = "Expected non-empty generated request ID"
        raise AssertionError(errmsg)

    return


def test_get_or_create_generates_when_empty():
    """
        Test that a new ID is generated when the header value is empty.
    """
    config = ServerConfig(trace_header="X-Request-ID")
    tracer = RequestTracer(config=config)

    headers = {"X-Request-ID": "   "}
    request_id = tracer.get_or_create_request_id(headers)

    if request_id.strip() == "":
        errmsg = "Expected non-empty generated request ID for blank header"
        raise AssertionError(errmsg)

    return


def test_get_or_create_custom_trace_header():
    """
        Test that a custom trace header name is respected.
    """
    config = ServerConfig(trace_header="X-Correlation-ID")
    tracer = RequestTracer(config=config)

    headers = {"X-Correlation-ID": "corr-456"}
    request_id = tracer.get_or_create_request_id(headers)

    if request_id != "corr-456":
        errmsg = f"Expected 'corr-456', got '{request_id}'"
        raise AssertionError(errmsg)

    return


def test_get_or_create_strips_whitespace():
    """
        Test that existing header values are stripped of whitespace.
    """
    config = ServerConfig(trace_header="X-Request-ID")
    tracer = RequestTracer(config=config)

    headers = {"X-Request-ID": "  trimmed-id  "}
    request_id = tracer.get_or_create_request_id(headers)

    if request_id != "trimmed-id":
        errmsg = f"Expected 'trimmed-id', got '{request_id}'"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for RequestTracer - Response Header Injection
# =============================================================================

def test_inject_response_headers_adds_request_id():
    """
        Test that inject_response_headers adds the request ID to headers.
    """
    config = ServerConfig(trace_header="X-Request-ID")
    tracer = RequestTracer(config=config)

    headers = {}
    result = tracer.inject_response_headers(headers, "resp-id-789")

    if result.get("X-Request-ID") != "resp-id-789":
        errmsg = f"Expected X-Request-ID 'resp-id-789', got '{result.get('X-Request-ID')}'"
        raise AssertionError(errmsg)

    return


def test_inject_response_headers_custom_header():
    """
        Test that inject_response_headers uses the configured header name.
    """
    config = ServerConfig(trace_header="X-Trace-ID")
    tracer = RequestTracer(config=config)

    headers = {"Content-Type": "application/json"}
    result = tracer.inject_response_headers(headers, "trace-abc")

    if result.get("X-Trace-ID") != "trace-abc":
        errmsg = f"Expected X-Trace-ID 'trace-abc', got '{result.get('X-Trace-ID')}'"
        raise AssertionError(errmsg)

    return


def test_inject_response_headers_preserves_existing():
    """
        Test that inject_response_headers preserves existing headers.
    """
    config = ServerConfig(trace_header="X-Request-ID")
    tracer = RequestTracer(config=config)

    headers = {"Content-Type": "text/html", "Server": "webworks"}
    result = tracer.inject_response_headers(headers, "id-123")

    if result.get("Content-Type") != "text/html":
        errmsg = "Expected existing Content-Type header to be preserved"
        raise AssertionError(errmsg)

    if result.get("Server") != "webworks":
        errmsg = "Expected existing Server header to be preserved"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for RequestTracer - Request ID Propagation to Logs
# =============================================================================

def test_request_id_propagation_to_structured_logger():
    """
        Test that request_id from tracer can be set on structured logger
        context for propagation to all log entries.
    """
    from automojo.webworks.prodserver.structuredlogger import StructuredLogger
    import json

    server_config = ServerConfig(log_format="json", trace_header="X-Request-ID")
    tracer = RequestTracer(config=server_config)
    logger = StructuredLogger(config=server_config)

    # Simulate request flow: extract or generate request ID
    headers = {"X-Request-ID": "propagated-id-001"}
    request_id = tracer.get_or_create_request_id(headers)

    # Set request_id on logger context for propagation
    logger.set_context(request_id=request_id)

    # Log a message and verify request_id is present
    result = logger.log("INFO", "handling request")
    parsed = json.loads(result)

    if parsed.get("request_id") != "propagated-id-001":
        errmsg = f"Expected request_id 'propagated-id-001', got '{parsed.get('request_id')}'"
        raise AssertionError(errmsg)

    return


def test_request_id_propagation_generated_id():
    """
        Test that a generated request_id propagates to log entries.
    """
    from automojo.webworks.prodserver.structuredlogger import StructuredLogger
    import json

    server_config = ServerConfig(log_format="json", trace_header="X-Request-ID")
    tracer = RequestTracer(config=server_config)
    logger = StructuredLogger(config=server_config)

    # No X-Request-ID header, so a new one is generated
    headers = {}
    request_id = tracer.get_or_create_request_id(headers)

    logger.set_context(request_id=request_id)

    result = logger.log("INFO", "processing")
    parsed = json.loads(result)

    if parsed.get("request_id") != request_id:
        errmsg = f"Expected request_id '{request_id}', got '{parsed.get('request_id')}'"
        raise AssertionError(errmsg)

    return


def test_request_id_in_response_matches_log():
    """
        Test that the request_id in response headers matches what
        was propagated to log entries.
    """
    from automojo.webworks.prodserver.structuredlogger import StructuredLogger
    import json

    server_config = ServerConfig(log_format="json", trace_header="X-Request-ID")
    tracer = RequestTracer(config=server_config)
    logger = StructuredLogger(config=server_config)

    headers = {"X-Request-ID": "round-trip-id"}
    request_id = tracer.get_or_create_request_id(headers)

    # Propagate to logger
    logger.set_context(request_id=request_id)
    log_result = logger.log("INFO", "request handled")
    log_parsed = json.loads(log_result)

    # Inject into response
    response_headers = {}
    tracer.inject_response_headers(response_headers, request_id)

    # Verify both match
    if log_parsed.get("request_id") != response_headers.get("X-Request-ID"):
        errmsg = (
            f"Log request_id '{log_parsed.get('request_id')}' does not match "
            f"response header '{response_headers.get('X-Request-ID')}'"
        )
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for RequestTracer - Properties
# =============================================================================

def test_trace_header_property():
    """
        Test that trace_header property returns the configured value.
    """
    config = ServerConfig(trace_header="X-Custom-Trace")
    tracer = RequestTracer(config=config)

    if tracer.trace_header != "X-Custom-Trace":
        errmsg = f"Expected 'X-Custom-Trace', got '{tracer.trace_header}'"
        raise AssertionError(errmsg)

    return


def test_enable_tracing_property():
    """
        Test that enable_tracing property returns the configured value.
    """
    config = ServerConfig(enable_tracing=True)
    tracer = RequestTracer(config=config)

    if tracer.enable_tracing is not True:
        errmsg = f"Expected True, got {tracer.enable_tracing}"
        raise AssertionError(errmsg)

    return


def test_enable_tracing_default_false():
    """
        Test that enable_tracing defaults to False.
    """
    config = ServerConfig()
    tracer = RequestTracer(config=config)

    if tracer.enable_tracing is not False:
        errmsg = f"Expected False, got {tracer.enable_tracing}"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for RequestTracer - Span Creation
# =============================================================================

def test_create_span_returns_span():
    """
        Test that create_span returns a Span instance.
    """
    config = ServerConfig(enable_tracing=True)
    tracer = RequestTracer(config=config)

    span = tracer.create_span("handle_request", "req-001")

    if not isinstance(span, Span):
        errmsg = f"Expected Span instance, got {type(span)}"
        raise AssertionError(errmsg)

    return


def test_create_span_has_unique_id():
    """
        Test that each span gets a unique span_id.
    """
    config = ServerConfig(enable_tracing=True)
    tracer = RequestTracer(config=config)

    span_ids = set()
    for _ in range(50):
        span = tracer.create_span("operation", "req-001")
        span_ids.add(span.span_id)

    if len(span_ids) != 50:
        errmsg = f"Expected 50 unique span IDs, got {len(span_ids)}"
        raise AssertionError(errmsg)

    return


def test_create_span_sets_name():
    """
        Test that the span name matches the provided name.
    """
    config = ServerConfig(enable_tracing=True)
    tracer = RequestTracer(config=config)

    span = tracer.create_span("process_request", "req-002")

    if span.name != "process_request":
        errmsg = f"Expected name 'process_request', got '{span.name}'"
        raise AssertionError(errmsg)

    return


def test_create_span_sets_request_id():
    """
        Test that the span request_id matches the provided value.
    """
    config = ServerConfig(enable_tracing=True)
    tracer = RequestTracer(config=config)

    span = tracer.create_span("handle", "req-abc")

    if span.request_id != "req-abc":
        errmsg = f"Expected request_id 'req-abc', got '{span.request_id}'"
        raise AssertionError(errmsg)

    return


def test_create_span_with_parent():
    """
        Test that a span can reference a parent span.
    """
    config = ServerConfig(enable_tracing=True)
    tracer = RequestTracer(config=config)

    parent = tracer.create_span("parent_op", "req-001")
    child = tracer.create_span("child_op", "req-001", parent_span_id=parent.span_id)

    if child.parent_span_id != parent.span_id:
        errmsg = f"Expected parent_span_id '{parent.span_id}', got '{child.parent_span_id}'"
        raise AssertionError(errmsg)

    return


def test_create_span_no_parent_default():
    """
        Test that parent_span_id defaults to None.
    """
    config = ServerConfig(enable_tracing=True)
    tracer = RequestTracer(config=config)

    span = tracer.create_span("root_op", "req-001")

    if span.parent_span_id is not None:
        errmsg = f"Expected None parent_span_id, got '{span.parent_span_id}'"
        raise AssertionError(errmsg)

    return


def test_create_span_has_start_time():
    """
        Test that a span has a start_time set.
    """
    import time

    config = ServerConfig(enable_tracing=True)
    tracer = RequestTracer(config=config)

    before = time.time()
    span = tracer.create_span("timed_op", "req-001")
    after = time.time()

    if span.start_time < before or span.start_time > after:
        errmsg = f"Expected start_time between {before} and {after}, got {span.start_time}"
        raise AssertionError(errmsg)

    return


def test_create_span_end_time_initially_none():
    """
        Test that a new span has end_time as None.
    """
    config = ServerConfig(enable_tracing=True)
    tracer = RequestTracer(config=config)

    span = tracer.create_span("op", "req-001")

    if span.end_time is not None:
        errmsg = f"Expected end_time None, got {span.end_time}"
        raise AssertionError(errmsg)

    return


def test_span_end_sets_end_time():
    """
        Test that calling end() on a span sets the end_time.
    """
    config = ServerConfig(enable_tracing=True)
    tracer = RequestTracer(config=config)

    span = tracer.create_span("op", "req-001")
    span.end()

    if span.end_time is None:
        errmsg = "Expected end_time to be set after end()"
        raise AssertionError(errmsg)

    if span.end_time < span.start_time:
        errmsg = f"Expected end_time >= start_time, got {span.end_time} < {span.start_time}"
        raise AssertionError(errmsg)

    return


def test_span_duration_ms():
    """
        Test that duration_ms returns the correct value after end().
    """
    config = ServerConfig(enable_tracing=True)
    tracer = RequestTracer(config=config)

    span = tracer.create_span("op", "req-001")
    span.end()

    duration = span.duration_ms

    if duration is None:
        errmsg = "Expected duration_ms to be set after end()"
        raise AssertionError(errmsg)

    if duration < 0:
        errmsg = f"Expected non-negative duration, got {duration}"
        raise AssertionError(errmsg)

    return


def test_span_duration_ms_none_before_end():
    """
        Test that duration_ms returns None before end() is called.
    """
    config = ServerConfig(enable_tracing=True)
    tracer = RequestTracer(config=config)

    span = tracer.create_span("op", "req-001")

    if span.duration_ms is not None:
        errmsg = f"Expected None duration before end(), got {span.duration_ms}"
        raise AssertionError(errmsg)

    return


def test_span_set_attribute():
    """
        Test that set_attribute stores key-value pairs on the span.
    """
    config = ServerConfig(enable_tracing=True)
    tracer = RequestTracer(config=config)

    span = tracer.create_span("op", "req-001")
    span.set_attribute("http.method", "GET")
    span.set_attribute("http.status_code", 200)

    if span.attributes.get("http.method") != "GET":
        errmsg = f"Expected 'GET', got '{span.attributes.get('http.method')}'"
        raise AssertionError(errmsg)

    if span.attributes.get("http.status_code") != 200:
        errmsg = f"Expected 200, got {span.attributes.get('http.status_code')}"
        raise AssertionError(errmsg)

    return


def test_span_as_dict():
    """
        Test that as_dict returns a complete dictionary representation.
    """
    config = ServerConfig(enable_tracing=True)
    tracer = RequestTracer(config=config)

    span = tracer.create_span("op", "req-001")
    span.set_attribute("key", "value")
    span.end()

    d = span.as_dict()

    required_keys = ["span_id", "name", "request_id", "parent_span_id",
                     "start_time", "end_time", "attributes"]

    for key in required_keys:
        if key not in d:
            errmsg = f"Expected key '{key}' in span dict"
            raise AssertionError(errmsg)

    return


def test_spans_collected_when_tracing_enabled():
    """
        Test that spans are collected internally when tracing is enabled.
    """
    config = ServerConfig(enable_tracing=True)
    tracer = RequestTracer(config=config)

    tracer.create_span("op1", "req-001")
    tracer.create_span("op2", "req-001")

    if len(tracer.spans) != 2:
        errmsg = f"Expected 2 spans, got {len(tracer.spans)}"
        raise AssertionError(errmsg)

    return


def test_spans_not_collected_when_tracing_disabled():
    """
        Test that spans are not collected when tracing is disabled.
    """
    config = ServerConfig(enable_tracing=False)
    tracer = RequestTracer(config=config)

    tracer.create_span("op1", "req-001")
    tracer.create_span("op2", "req-001")

    if len(tracer.spans) != 0:
        errmsg = f"Expected 0 spans when tracing disabled, got {len(tracer.spans)}"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for RequestTracer - W3C Traceparent
# =============================================================================

def test_parse_traceparent_valid():
    """
        Test parsing a valid W3C traceparent header.
    """
    config = ServerConfig()
    tracer = RequestTracer(config=config)

    headers = {"traceparent": "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"}
    result = tracer.parse_traceparent(headers)

    if result is None:
        errmsg = "Expected parsed traceparent, got None"
        raise AssertionError(errmsg)

    if result["trace_id"] != "4bf92f3577b34da6a3ce929d0e0e4736":
        errmsg = f"Expected trace_id '4bf92f3577b34da6a3ce929d0e0e4736', got '{result['trace_id']}'"
        raise AssertionError(errmsg)

    if result["parent_id"] != "00f067aa0ba902b7":
        errmsg = f"Expected parent_id '00f067aa0ba902b7', got '{result['parent_id']}'"
        raise AssertionError(errmsg)

    return


def test_parse_traceparent_missing_header():
    """
        Test that parse_traceparent returns None when header is missing.
    """
    config = ServerConfig()
    tracer = RequestTracer(config=config)

    headers = {"Content-Type": "text/html"}
    result = tracer.parse_traceparent(headers)

    if result is not None:
        errmsg = f"Expected None for missing traceparent, got {result}"
        raise AssertionError(errmsg)

    return


def test_parse_traceparent_malformed():
    """
        Test that parse_traceparent returns None for malformed values.
    """
    config = ServerConfig()
    tracer = RequestTracer(config=config)

    headers = {"traceparent": "invalid-format"}
    result = tracer.parse_traceparent(headers)

    if result is not None:
        errmsg = f"Expected None for malformed traceparent, got {result}"
        raise AssertionError(errmsg)

    return


def test_parse_traceparent_wrong_length_trace_id():
    """
        Test that parse_traceparent rejects trace_id with wrong length.
    """
    config = ServerConfig()
    tracer = RequestTracer(config=config)

    # trace_id too short (only 16 chars instead of 32)
    headers = {"traceparent": "00-4bf92f3577b34da6-00f067aa0ba902b7-01"}
    result = tracer.parse_traceparent(headers)

    if result is not None:
        errmsg = f"Expected None for short trace_id, got {result}"
        raise AssertionError(errmsg)

    return


def test_parse_traceparent_case_insensitive():
    """
        Test that traceparent header lookup is case-insensitive.
    """
    config = ServerConfig()
    tracer = RequestTracer(config=config)

    headers = {"Traceparent": "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"}
    result = tracer.parse_traceparent(headers)

    if result is None:
        errmsg = "Expected parsed traceparent with mixed-case header"
        raise AssertionError(errmsg)

    return


def test_build_traceparent():
    """
        Test building a W3C traceparent header value.
    """
    config = ServerConfig()
    tracer = RequestTracer(config=config)

    result = tracer.build_traceparent(
        "4bf92f3577b34da6a3ce929d0e0e4736",
        "00f067aa0ba902b7",
        sampled=True
    )

    expected = "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"

    if result != expected:
        errmsg = f"Expected '{expected}', got '{result}'"
        raise AssertionError(errmsg)

    return


def test_build_traceparent_not_sampled():
    """
        Test building a traceparent with sampled=False.
    """
    config = ServerConfig()
    tracer = RequestTracer(config=config)

    result = tracer.build_traceparent(
        "4bf92f3577b34da6a3ce929d0e0e4736",
        "00f067aa0ba902b7",
        sampled=False
    )

    if not result.endswith("-00"):
        errmsg = f"Expected trace_flags '00' for not sampled, got '{result}'"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for RequestTracer - Trace Export
# =============================================================================

def test_export_traces_returns_span_dicts():
    """
        Test that export_traces returns a list of span dictionaries.
    """
    config = ServerConfig(enable_tracing=True)
    tracer = RequestTracer(config=config)

    span1 = tracer.create_span("op1", "req-001")
    span1.end()
    span2 = tracer.create_span("op2", "req-001")
    span2.end()

    exported = tracer.export_traces()

    if len(exported) != 2:
        errmsg = f"Expected 2 exported spans, got {len(exported)}"
        raise AssertionError(errmsg)

    if exported[0]["name"] != "op1":
        errmsg = f"Expected first span name 'op1', got '{exported[0]['name']}'"
        raise AssertionError(errmsg)

    return


def test_export_traces_clears_spans():
    """
        Test that export_traces clears the internal span collection.
    """
    config = ServerConfig(enable_tracing=True)
    tracer = RequestTracer(config=config)

    tracer.create_span("op1", "req-001")
    tracer.export_traces()

    if len(tracer.spans) != 0:
        errmsg = f"Expected 0 spans after export, got {len(tracer.spans)}"
        raise AssertionError(errmsg)

    return


def test_export_traces_calls_backends():
    """
        Test that export_traces sends spans to registered backends.
    """
    config = ServerConfig(enable_tracing=True)
    tracer = RequestTracer(config=config)

    received = []

    def mock_backend(spans):
        received.extend(spans)

    tracer.register_export_backend(mock_backend)

    span = tracer.create_span("op1", "req-001")
    span.set_attribute("http.method", "GET")
    span.end()

    tracer.export_traces()

    if len(received) != 1:
        errmsg = f"Expected 1 span sent to backend, got {len(received)}"
        raise AssertionError(errmsg)

    if received[0]["name"] != "op1":
        errmsg = f"Expected span name 'op1', got '{received[0]['name']}'"
        raise AssertionError(errmsg)

    return


def test_export_traces_multiple_backends():
    """
        Test that export_traces sends spans to all registered backends.
    """
    config = ServerConfig(enable_tracing=True)
    tracer = RequestTracer(config=config)

    received_a = []
    received_b = []

    tracer.register_export_backend(lambda spans: received_a.extend(spans))
    tracer.register_export_backend(lambda spans: received_b.extend(spans))

    tracer.create_span("op1", "req-001")
    tracer.export_traces()

    if len(received_a) != 1:
        errmsg = f"Expected 1 span in backend A, got {len(received_a)}"
        raise AssertionError(errmsg)

    if len(received_b) != 1:
        errmsg = f"Expected 1 span in backend B, got {len(received_b)}"
        raise AssertionError(errmsg)

    return


def test_export_traces_empty_when_no_spans():
    """
        Test that export_traces returns empty list when no spans exist.
    """
    config = ServerConfig(enable_tracing=True)
    tracer = RequestTracer(config=config)

    exported = tracer.export_traces()

    if len(exported) != 0:
        errmsg = f"Expected 0 exported spans, got {len(exported)}"
        raise AssertionError(errmsg)

    return


def test_clear_spans():
    """
        Test that clear_spans removes all collected spans.
    """
    config = ServerConfig(enable_tracing=True)
    tracer = RequestTracer(config=config)

    tracer.create_span("op1", "req-001")
    tracer.create_span("op2", "req-001")
    tracer.clear_spans()

    if len(tracer.spans) != 0:
        errmsg = f"Expected 0 spans after clear, got {len(tracer.spans)}"
        raise AssertionError(errmsg)

    return
