"""
    Request tracing module for the production server.

    This module provides the RequestTracer class for generating and
    propagating unique request IDs, creating tracing spans, and
    supporting OpenTelemetry trace context propagation. It also
    provides the Span dataclass for representing units of work
    within a request lifecycle.
"""

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from automojo.webworks.prodserver.serverconfig import ServerConfig


# W3C Trace Context header name
W3C_TRACEPARENT_HEADER = "traceparent"

# Default trace header name
DEFAULT_TRACE_HEADER = "X-Request-ID"


@dataclass
class Span:
    """
        A tracing span representing a unit of work.

        Spans track the start and end time of an operation along
        with arbitrary attributes. Spans can be nested via the
        parent_span_id field to form a trace tree.
    """
    span_id: str
    name: str
    request_id: str
    parent_span_id: Optional[str]
    start_time: float
    end_time: Optional[float] = None
    attributes: Dict[str, Any] = field(default_factory=dict)

    def end(self) -> None:
        """
            Mark the span as complete by recording the end time.
        """
        self.end_time = time.time()

        return

    def set_attribute(self, key: str, value: Any) -> None:
        """
            Set a span attribute.

            :param key: The attribute key.
            :param value: The attribute value.
        """
        self.attributes[key] = value

        return

    @property
    def duration_ms(self) -> Optional[float]:
        """
            Get the span duration in milliseconds.

            :returns: Duration in milliseconds, or None if span has not ended.
        """
        if self.end_time is None:
            return None

        rtnval = (self.end_time - self.start_time) * 1000.0

        return rtnval

    def as_dict(self) -> Dict[str, Any]:
        """
            Convert the span to a dictionary representation.

            :returns: Dictionary containing all span fields.
        """
        rtnval: Dict[str, Any] = {
            "span_id": self.span_id,
            "name": self.name,
            "request_id": self.request_id,
            "parent_span_id": self.parent_span_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "attributes": dict(self.attributes),
        }

        return rtnval


class RequestTracer:
    """
        Provides request tracing with unique IDs and span creation.

        Generates unique request IDs for incoming requests, accepts
        existing request IDs from configurable headers, creates
        tracing spans for request handling, and supports exporting
        traces to configurable backends.
    """

    def __init__(self, config: "ServerConfig"):
        """
            Construct a RequestTracer.

            :param config: Server configuration containing tracing settings.
        """
        self._config = config
        self._trace_header: str = config.trace_header
        self._enable_tracing: bool = config.enable_tracing
        self._spans: List[Span] = []
        self._export_backends: List[Callable[[List[Dict[str, Any]]], None]] = []

        return

    @property
    def trace_header(self) -> str:
        """
            Get the configured trace header name.

            :returns: The trace header name string.
        """
        return self._trace_header

    @property
    def enable_tracing(self) -> bool:
        """
            Get whether tracing is enabled.

            :returns: True if tracing is enabled.
        """
        return self._enable_tracing

    @property
    def spans(self) -> List[Span]:
        """
            Get the list of collected spans.

            :returns: List of Span objects.
        """
        return list(self._spans)

    def generate_request_id(self) -> str:
        """
            Generate a new unique request ID.

            Uses UUID4 to produce a universally unique identifier.

            :returns: A unique request ID string.
        """
        rtnval = str(uuid.uuid4())

        return rtnval

    def get_or_create_request_id(self, headers: Dict[str, str]) -> str:
        """
            Get request ID from headers or generate a new one.

            Checks the configured trace header (and common variations)
            in the provided headers dictionary. If a request ID is found,
            it is returned as-is. Otherwise, a new unique ID is generated.

            :param headers: Dictionary of request headers.

            :returns: The request ID (existing or newly generated).
        """
        # Check the configured trace header (case-insensitive)
        trace_header_lower = self._trace_header.lower()

        for header_name, header_value in headers.items():
            if header_name.lower() == trace_header_lower:
                if header_value.strip():
                    return header_value.strip()

        # No existing request ID found, generate a new one
        rtnval = self.generate_request_id()

        return rtnval

    def inject_response_headers(
        self,
        headers: Dict[str, str],
        request_id: str
    ) -> Dict[str, str]:
        """
            Inject the request ID into response headers.

            Adds the request ID to the response headers using the
            configured trace header name.

            :param headers: The response headers dictionary.
            :param request_id: The request ID to inject.

            :returns: The updated response headers dictionary.
        """
        headers[self._trace_header] = request_id

        return headers

    def create_span(
        self,
        name: str,
        request_id: str,
        parent_span_id: Optional[str] = None
    ) -> Span:
        """
            Create a new tracing span.

            Creates a span representing a unit of work. The span is
            automatically added to the internal span collection when
            tracing is enabled.

            :param name: The span name describing the operation.
            :param request_id: The associated request ID.
            :param parent_span_id: Optional parent span ID for nesting.

            :returns: A new Span instance.
        """
        span_id = str(uuid.uuid4())

        span = Span(
            span_id=span_id,
            name=name,
            request_id=request_id,
            parent_span_id=parent_span_id,
            start_time=time.time(),
        )

        if self._enable_tracing:
            self._spans.append(span)

        return span

    def parse_traceparent(self, headers: Dict[str, str]) -> Optional[Dict[str, str]]:
        """
            Parse W3C traceparent header from request headers.

            The traceparent header format is:
            {version}-{trace-id}-{parent-id}-{trace-flags}

            :param headers: Dictionary of request headers.

            :returns: Dictionary with trace_id, parent_id, and trace_flags,
                      or None if the header is missing or malformed.
        """
        traceparent_value = None

        for header_name, header_value in headers.items():
            if header_name.lower() == W3C_TRACEPARENT_HEADER:
                traceparent_value = header_value.strip()
                break

        if traceparent_value is None:
            return None

        parts = traceparent_value.split("-")

        if len(parts) != 4:
            return None

        version, trace_id, parent_id, trace_flags = parts

        # Validate version is 2 hex chars
        if len(version) != 2:
            return None

        # Validate trace_id is 32 hex chars
        if len(trace_id) != 32:
            return None

        # Validate parent_id is 16 hex chars
        if len(parent_id) != 16:
            return None

        # Validate trace_flags is 2 hex chars
        if len(trace_flags) != 2:
            return None

        # Validate all parts are valid hex
        try:
            int(version, 16)
            int(trace_id, 16)
            int(parent_id, 16)
            int(trace_flags, 16)
        except ValueError:
            return None

        rtnval: Dict[str, str] = {
            "version": version,
            "trace_id": trace_id,
            "parent_id": parent_id,
            "trace_flags": trace_flags,
        }

        return rtnval

    def build_traceparent(self, trace_id: str, span_id: str, sampled: bool = True) -> str:
        """
            Build a W3C traceparent header value.

            :param trace_id: The 32-character hex trace ID.
            :param span_id: The 16-character hex span/parent ID.
            :param sampled: Whether the trace is sampled.

            :returns: The formatted traceparent header value.
        """
        version = "00"
        trace_flags = "01" if sampled else "00"

        rtnval = f"{version}-{trace_id}-{span_id}-{trace_flags}"

        return rtnval

    def register_export_backend(
        self,
        backend: Callable[[List[Dict[str, Any]]], None]
    ) -> None:
        """
            Register a trace export backend.

            The backend callable receives a list of span dictionaries
            when export_traces is called.

            :param backend: A callable that accepts a list of span dicts.
        """
        self._export_backends.append(backend)

        return

    def export_traces(self) -> List[Dict[str, Any]]:
        """
            Export collected traces to all registered backends.

            Converts all collected spans to dictionaries and sends
            them to each registered export backend. Clears the
            internal span collection after export.

            :returns: List of exported span dictionaries.
        """
        exported: List[Dict[str, Any]] = []

        for span in self._spans:
            exported.append(span.as_dict())

        for backend in self._export_backends:
            backend(exported)

        self._spans.clear()

        return exported

    def clear_spans(self) -> None:
        """
            Clear all collected spans without exporting.
        """
        self._spans.clear()

        return
