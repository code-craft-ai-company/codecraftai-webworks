"""
.. module:: test_middleware_properties
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Property-based tests for MiddlewarePipeline execution order.

.. moduleauthor:: Code Craft AI LLC

This module contains property-based tests for the MiddlewarePipeline,
validating Property 1: Pipeline execution preserves registration order
across many randomly generated inputs.
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []

from typing import Callable, Dict

import ccai.testbase as testbase

from ccai.testbase.properties import given
from ccai.testbase.properties import strategies as st
from ccai.testbase.properties.strategies import composite

from ccai.webworks.routing.middleware import MiddlewarePipeline
from ccai.webworks.routing.request import Request


# =============================================================================
# Test Helpers
# =============================================================================

class MockResponse:
    """
        Minimal Response implementation for property tests.
    """

    def __init__(self, status_code: int = 200, body: bytes = b"", headers: Dict[str, str] = None):
        self._status_code = status_code
        self._body = body
        self._headers = headers or {}
        return

    @property
    def status_code(self) -> int:
        return self._status_code

    @property
    def body(self) -> bytes:
        return self._body

    @property
    def headers(self) -> Dict[str, str]:
        return self._headers


class OrderTrackingMiddleware:
    """
        Middleware that records before/after markers into request.path_params["order"].
    """

    def __init__(self, marker: str, name: str = None):
        self.marker = marker
        self.name = name
        return

    def __call__(self, request: Request, call_next: Callable) -> MockResponse:
        if "order" not in request.path_params:
            request.path_params["order"] = []
        request.path_params["order"].append(f"{self.marker}_before")

        response = call_next(request)

        request.path_params["order"].append(f"{self.marker}_after")

        return response


# Strategy: unique middleware marker names (lowercase alpha, 3-8 chars)
marker_strategy = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyz",
    min_size=3,
    max_size=8,
)


@composite
def unique_marker_lists(draw, min_size=1, max_size=6):
    """
        Generate a list of unique middleware marker strings.
    """
    size = draw(st.integers(min_size, max_size))
    markers = []
    seen = set()
    for _ in range(size):
        marker = draw(marker_strategy)
        # Ensure uniqueness by appending index if needed
        base = marker
        idx = 0
        while marker in seen:
            idx += 1
            marker = f"{base}{idx}"
        seen.add(marker)
        markers.append(marker)
    return markers


# =============================================================================
# Property 1: Pipeline execution preserves registration order
# Feature: middleware-pipeline, Property 1
# Validates: Requirements 2.1, 2.2, 2.3, 2.4
# =============================================================================

@given(
    markers=unique_marker_lists(min_size=1, max_size=6),
    constraints={"max_examples": 10},
)
def test_property_pipeline_execution_preserves_registration_order(markers):
    """
        Property 1: Pipeline execution preserves registration order.

        For any list of N middleware added to a pipeline in sequence,
        executing the pipeline should invoke each middleware in the order
        it was registered, with the endpoint handler invoked last (after
        all middleware have called call_next).

        The expected execution trace is:
        MW1_before -> MW2_before -> ... -> MWN_before -> handler ->
        MWN_after -> ... -> MW2_after -> MW1_after

        **Feature: middleware-pipeline, Property 1: Pipeline execution preserves registration order**
        **Validates: Requirements 2.1, 2.2, 2.3, 2.4**
    """
    pipeline = MiddlewarePipeline()

    for i, marker in enumerate(markers):
        mw = OrderTrackingMiddleware(marker, name=f"mw_{i}")
        pipeline.add(mw, name=f"mw_{i}")

    request = Request("GET", "/test")
    request.path_params = {}

    def handler(req: Request) -> MockResponse:
        if "order" not in req.path_params:
            req.path_params["order"] = []
        req.path_params["order"].append("handler")
        return MockResponse(status_code=200)

    pipeline.execute(request, handler)

    actual_order = request.path_params.get("order", [])

    # Build expected order: before markers in registration order,
    # then handler, then after markers in reverse registration order
    expected_order = []
    for marker in markers:
        expected_order.append(f"{marker}_before")
    expected_order.append("handler")
    for marker in reversed(markers):
        expected_order.append(f"{marker}_after")

    testbase.assert_equal(actual_order, expected_order,
        f"Pipeline execution order mismatch for {len(markers)} middleware. "
        f"Expected {expected_order}, got {actual_order}.")


@given(
    markers=unique_marker_lists(min_size=1, max_size=6),
    constraints={"max_examples": 10},
)
def test_property_pipeline_handler_invoked_after_all_middleware(markers):
    """
        Property 1 (handler invocation): The endpoint handler is invoked
        exactly once, after all middleware before-phases complete.

        **Feature: middleware-pipeline, Property 1: Pipeline execution preserves registration order**
        **Validates: Requirements 2.2, 2.4**
    """
    pipeline = MiddlewarePipeline()

    for i, marker in enumerate(markers):
        mw = OrderTrackingMiddleware(marker, name=f"mw_{i}")
        pipeline.add(mw, name=f"mw_{i}")

    request = Request("GET", "/test")
    request.path_params = {}

    handler_call_count = [0]

    def handler(req: Request) -> MockResponse:
        if "order" not in req.path_params:
            req.path_params["order"] = []
        handler_call_count[0] += 1
        req.path_params["order"].append("handler")
        return MockResponse(status_code=200)

    pipeline.execute(request, handler)

    actual_order = request.path_params.get("order", [])

    # Handler should be called exactly once
    testbase.assert_equal(handler_call_count[0], 1,
        f"Handler should be called exactly once, was called {handler_call_count[0]} times.")

    # Handler should appear at position N (after N before-markers)
    handler_pos = actual_order.index("handler")
    testbase.assert_equal(handler_pos, len(markers),
        f"Handler should be at position {len(markers)} (after all before-markers), "
        f"but was at position {handler_pos}. Order: {actual_order}.")


@given(
    markers=unique_marker_lists(min_size=2, max_size=6),
    constraints={"max_examples": 10},
)
def test_property_pipeline_call_next_chains_to_next_middleware(markers):
    """
        Property 1 (call_next chaining): When a middleware calls call_next,
        the next middleware in the chain is invoked. Each middleware's
        before-phase appears in strict registration order.

        **Feature: middleware-pipeline, Property 1: Pipeline execution preserves registration order**
        **Validates: Requirements 2.1, 2.3**
    """
    pipeline = MiddlewarePipeline()

    for i, marker in enumerate(markers):
        mw = OrderTrackingMiddleware(marker, name=f"mw_{i}")
        pipeline.add(mw, name=f"mw_{i}")

    request = Request("GET", "/test")
    request.path_params = {}

    def handler(req: Request) -> MockResponse:
        if "order" not in req.path_params:
            req.path_params["order"] = []
        req.path_params["order"].append("handler")
        return MockResponse(status_code=200)

    pipeline.execute(request, handler)

    actual_order = request.path_params.get("order", [])

    # Extract only the before-markers and verify they are in registration order
    before_markers = [entry for entry in actual_order if entry.endswith("_before")]
    expected_before = [f"{m}_before" for m in markers]

    testbase.assert_equal(before_markers, expected_before,
        f"Before-phase order should match registration order. "
        f"Expected {expected_before}, got {before_markers}.")

    # Extract only the after-markers and verify they are in reverse registration order
    after_markers = [entry for entry in actual_order if entry.endswith("_after")]
    expected_after = [f"{m}_after" for m in reversed(markers)]

    testbase.assert_equal(after_markers, expected_after,
        f"After-phase order should be reverse of registration order. "
        f"Expected {expected_after}, got {after_markers}.")


@given(
    markers=unique_marker_lists(min_size=1, max_size=6),
    constraints={"max_examples": 10},
)
def test_property_pipeline_total_trace_length(markers):
    """
        Property 1 (trace completeness): The execution trace should contain
        exactly 2*N + 1 entries (N before-markers + handler + N after-markers).

        **Feature: middleware-pipeline, Property 1: Pipeline execution preserves registration order**
        **Validates: Requirements 2.1, 2.2, 2.3, 2.4**
    """
    pipeline = MiddlewarePipeline()

    for i, marker in enumerate(markers):
        mw = OrderTrackingMiddleware(marker, name=f"mw_{i}")
        pipeline.add(mw, name=f"mw_{i}")

    request = Request("GET", "/test")
    request.path_params = {}

    def handler(req: Request) -> MockResponse:
        if "order" not in req.path_params:
            req.path_params["order"] = []
        req.path_params["order"].append("handler")
        return MockResponse(status_code=200)

    pipeline.execute(request, handler)

    actual_order = request.path_params.get("order", [])
    n = len(markers)
    expected_length = 2 * n + 1

    testbase.assert_equal(len(actual_order), expected_length,
        f"Execution trace should have {expected_length} entries "
        f"(2*{n} + 1) but had {len(actual_order)}. Trace: {actual_order}.")




# =============================================================================
# Property 2: Short-circuit bypasses remaining middleware and handler
# Feature: middleware-pipeline, Property 2
# Validates: Requirements 2.5
# =============================================================================

class ShortCircuitMiddleware:
    """
        Middleware that returns a response without calling call_next,
        short-circuiting the pipeline.
    """

    def __init__(self, marker: str, name: str = None):
        self.marker = marker
        self.name = name
        return

    def __call__(self, request: Request, call_next: Callable) -> MockResponse:
        if "order" not in request.path_params:
            request.path_params["order"] = []
        request.path_params["order"].append(f"{self.marker}_shortcircuit")
        # Return without calling call_next
        return MockResponse(status_code=403)


@given(
    markers=unique_marker_lists(min_size=2, max_size=6),
    short_circuit_index=st.integers(0, 5),
    constraints={"max_examples": 10},
)
def test_property_short_circuit_bypasses_remaining_middleware_and_handler(markers, short_circuit_index):
    """
        Property 2: Short-circuit bypasses remaining middleware and handler.

        For any pipeline with N middleware where middleware at position K
        returns a response without calling call_next, middleware at positions
        K+1 through N and the endpoint handler should not be invoked, and
        the pipeline should return the short-circuit response.

        **Feature: middleware-pipeline, Property 2: Short-circuit bypasses remaining middleware and handler**
        **Validates: Requirements 2.5**
    """
    # Clamp short_circuit_index to valid range for the generated markers
    k = short_circuit_index % len(markers)

    pipeline = MiddlewarePipeline()

    for i, marker in enumerate(markers):
        if i == k:
            mw = ShortCircuitMiddleware(marker, name=f"mw_{i}")
        else:
            mw = OrderTrackingMiddleware(marker, name=f"mw_{i}")
        pipeline.add(mw, name=f"mw_{i}")

    request = Request("GET", "/test")
    request.path_params = {}

    handler_called = [False]

    def handler(req: Request) -> MockResponse:
        handler_called[0] = True
        if "order" not in req.path_params:
            req.path_params["order"] = []
        req.path_params["order"].append("handler")
        return MockResponse(status_code=200)

    response = pipeline.execute(request, handler)

    actual_order = request.path_params.get("order", [])

    # The handler should NOT be called
    testbase.assert_false(handler_called[0],
        f"Handler should not be called when middleware at position {k} short-circuits. "
        f"Markers: {markers}, trace: {actual_order}.")

    # The short-circuit response status code should be returned
    testbase.assert_equal(response.status_code, 403,
        f"Pipeline should return the short-circuit response (403), "
        f"got {response.status_code}. Markers: {markers}, k={k}.")

    # Middleware before position K should have their before-markers recorded
    for i in range(k):
        expected_entry = f"{markers[i]}_before"
        testbase.assert_true(expected_entry in actual_order,
            f"Middleware at position {i} ('{markers[i]}') should have executed "
            f"before the short-circuit at position {k}. Trace: {actual_order}.")

    # The short-circuit middleware should have its marker recorded
    short_circuit_entry = f"{markers[k]}_shortcircuit"
    testbase.assert_true(short_circuit_entry in actual_order,
        f"Short-circuit middleware at position {k} ('{markers[k]}') should have "
        f"recorded its marker. Trace: {actual_order}.")

    # Middleware after position K should NOT have any markers recorded
    for i in range(k + 1, len(markers)):
        before_entry = f"{markers[i]}_before"
        after_entry = f"{markers[i]}_after"
        testbase.assert_false(before_entry in actual_order,
            f"Middleware at position {i} ('{markers[i]}') should NOT have executed "
            f"after short-circuit at position {k}. Trace: {actual_order}.")
        testbase.assert_false(after_entry in actual_order,
            f"Middleware at position {i} ('{markers[i]}') after-phase should NOT have "
            f"executed after short-circuit at position {k}. Trace: {actual_order}.")


@given(
    markers=unique_marker_lists(min_size=2, max_size=6),
    short_circuit_index=st.integers(0, 5),
    constraints={"max_examples": 10},
)
def test_property_short_circuit_returns_short_circuit_response(markers, short_circuit_index):
    """
        Property 2 (response identity): The pipeline returns the exact
        response produced by the short-circuiting middleware, not a
        modified or default response.

        **Feature: middleware-pipeline, Property 2: Short-circuit bypasses remaining middleware and handler**
        **Validates: Requirements 2.5**
    """
    k = short_circuit_index % len(markers)

    pipeline = MiddlewarePipeline()

    for i, marker in enumerate(markers):
        if i == k:
            mw = ShortCircuitMiddleware(marker, name=f"mw_{i}")
        else:
            mw = OrderTrackingMiddleware(marker, name=f"mw_{i}")
        pipeline.add(mw, name=f"mw_{i}")

    request = Request("GET", "/test")
    request.path_params = {}

    def handler(req: Request) -> MockResponse:
        return MockResponse(status_code=200)

    response = pipeline.execute(request, handler)

    # The response should be the 403 from the short-circuit middleware,
    # not the 200 from the handler
    testbase.assert_equal(response.status_code, 403,
        f"Pipeline should return the short-circuit response (403), "
        f"got {response.status_code}. Short-circuit at position {k} "
        f"of {len(markers)} middleware.")


@given(
    markers=unique_marker_lists(min_size=2, max_size=6),
    short_circuit_index=st.integers(0, 5),
    constraints={"max_examples": 10},
)
def test_property_short_circuit_trace_length(markers, short_circuit_index):
    """
        Property 2 (trace length): When middleware at position K
        short-circuits, the trace should contain exactly K before-markers
        + 1 short-circuit marker + K after-markers = 2*K + 1 entries.

        **Feature: middleware-pipeline, Property 2: Short-circuit bypasses remaining middleware and handler**
        **Validates: Requirements 2.5**
    """
    k = short_circuit_index % len(markers)

    pipeline = MiddlewarePipeline()

    for i, marker in enumerate(markers):
        if i == k:
            mw = ShortCircuitMiddleware(marker, name=f"mw_{i}")
        else:
            mw = OrderTrackingMiddleware(marker, name=f"mw_{i}")
        pipeline.add(mw, name=f"mw_{i}")

    request = Request("GET", "/test")
    request.path_params = {}

    def handler(req: Request) -> MockResponse:
        if "order" not in req.path_params:
            req.path_params["order"] = []
        req.path_params["order"].append("handler")
        return MockResponse(status_code=200)

    pipeline.execute(request, handler)

    actual_order = request.path_params.get("order", [])

    # K middleware before the short-circuit each contribute a before-marker,
    # the short-circuit middleware contributes 1 marker,
    # then K middleware unwind with after-markers
    expected_length = 2 * k + 1

    testbase.assert_equal(len(actual_order), expected_length,
        f"Trace should have {expected_length} entries (2*{k} + 1) when "
        f"short-circuiting at position {k}, but had {len(actual_order)}. "
        f"Trace: {actual_order}.")


# =============================================================================
# Property 3: Exception propagation stops pipeline execution
# Feature: middleware-pipeline, Property 3
# Validates: Requirements 2.8
# =============================================================================

class ExceptionMiddleware:
    """
        Middleware that raises an exception without calling call_next,
        simulating an error during request processing.
    """

    def __init__(self, marker: str, name: str = None):
        self.marker = marker
        self.name = name
        return

    def __call__(self, request: Request, call_next: Callable) -> MockResponse:
        if "order" not in request.path_params:
            request.path_params["order"] = []
        request.path_params["order"].append(f"{self.marker}_exception")
        raise RuntimeError(f"Exception from middleware '{self.marker}'")


@given(
    markers=unique_marker_lists(min_size=2, max_size=6),
    exception_index=st.integers(0, 5),
    constraints={"max_examples": 10},
)
def test_property_exception_propagation_stops_pipeline_execution(markers, exception_index):
    """
        Property 3: Exception propagation stops pipeline execution.

        For any pipeline with N middleware where middleware at position K
        raises an exception, middleware at positions K+1 through N and the
        endpoint handler should not be invoked, and the exception should
        propagate to the caller.

        **Feature: middleware-pipeline, Property 3: Exception propagation stops pipeline execution**
        **Validates: Requirements 2.8**
    """
    k = exception_index % len(markers)

    pipeline = MiddlewarePipeline()

    for i, marker in enumerate(markers):
        if i == k:
            mw = ExceptionMiddleware(marker, name=f"mw_{i}")
        else:
            mw = OrderTrackingMiddleware(marker, name=f"mw_{i}")
        pipeline.add(mw, name=f"mw_{i}")

    request = Request("GET", "/test")
    request.path_params = {}

    handler_called = [False]

    def handler(req: Request) -> MockResponse:
        handler_called[0] = True
        if "order" not in req.path_params:
            req.path_params["order"] = []
        req.path_params["order"].append("handler")
        return MockResponse(status_code=200)

    # The exception should propagate to the caller
    caught_exception = None
    try:
        pipeline.execute(request, handler)
    except RuntimeError as exc:
        caught_exception = exc

    actual_order = request.path_params.get("order", [])

    # The exception must have propagated
    testbase.assert_true(caught_exception is not None,
        f"Pipeline should propagate the RuntimeError from middleware at position {k}. "
        f"Markers: {markers}, trace: {actual_order}.")

    # The exception message should identify the raising middleware
    testbase.assert_true(markers[k] in str(caught_exception),
        f"Propagated exception should contain the middleware marker '{markers[k]}'. "
        f"Got: {caught_exception}.")

    # The handler should NOT be called
    testbase.assert_false(handler_called[0],
        f"Handler should not be called when middleware at position {k} raises. "
        f"Markers: {markers}, trace: {actual_order}.")

    # Middleware before position K should have their before-markers recorded
    for i in range(k):
        expected_entry = f"{markers[i]}_before"
        testbase.assert_true(expected_entry in actual_order,
            f"Middleware at position {i} ('{markers[i]}') should have executed "
            f"before the exception at position {k}. Trace: {actual_order}.")

    # The exception middleware should have its marker recorded
    exception_entry = f"{markers[k]}_exception"
    testbase.assert_true(exception_entry in actual_order,
        f"Exception middleware at position {k} ('{markers[k]}') should have "
        f"recorded its marker before raising. Trace: {actual_order}.")

    # Middleware after position K should NOT have any markers recorded
    for i in range(k + 1, len(markers)):
        before_entry = f"{markers[i]}_before"
        after_entry = f"{markers[i]}_after"
        testbase.assert_false(before_entry in actual_order,
            f"Middleware at position {i} ('{markers[i]}') should NOT have executed "
            f"after exception at position {k}. Trace: {actual_order}.")
        testbase.assert_false(after_entry in actual_order,
            f"Middleware at position {i} ('{markers[i]}') after-phase should NOT have "
            f"executed after exception at position {k}. Trace: {actual_order}.")


@given(
    markers=unique_marker_lists(min_size=2, max_size=6),
    exception_index=st.integers(0, 5),
    constraints={"max_examples": 10},
)
def test_property_exception_propagation_no_after_markers_for_preceding_middleware(markers, exception_index):
    """
        Property 3 (unwinding): When middleware at position K raises an
        exception, the after-phase of middleware at positions 0 through K-1
        should NOT execute because the exception propagates immediately
        without returning a response through the chain.

        **Feature: middleware-pipeline, Property 3: Exception propagation stops pipeline execution**
        **Validates: Requirements 2.8**
    """
    k = exception_index % len(markers)

    pipeline = MiddlewarePipeline()

    for i, marker in enumerate(markers):
        if i == k:
            mw = ExceptionMiddleware(marker, name=f"mw_{i}")
        else:
            mw = OrderTrackingMiddleware(marker, name=f"mw_{i}")
        pipeline.add(mw, name=f"mw_{i}")

    request = Request("GET", "/test")
    request.path_params = {}

    def handler(req: Request) -> MockResponse:
        return MockResponse(status_code=200)

    try:
        pipeline.execute(request, handler)
    except RuntimeError:
        # Expected: ExceptionMiddleware raises RuntimeError; the trace recorded before
        # it propagated is what this property checks.
        pass

    actual_order = request.path_params.get("order", [])

    # Preceding middleware should NOT have after-markers because the exception
    # propagates up through call_next without returning a response
    for i in range(k):
        after_entry = f"{markers[i]}_after"
        testbase.assert_false(after_entry in actual_order,
            f"Middleware at position {i} ('{markers[i]}') after-phase should NOT "
            f"execute when middleware at position {k} raises an exception. "
            f"The exception propagates through call_next. Trace: {actual_order}.")


@given(
    markers=unique_marker_lists(min_size=2, max_size=6),
    exception_index=st.integers(0, 5),
    constraints={"max_examples": 10},
)
def test_property_exception_propagation_trace_length(markers, exception_index):
    """
        Property 3 (trace length): When middleware at position K raises an
        exception, the trace should contain exactly K before-markers + 1
        exception marker = K + 1 entries. No after-markers should be present
        because the exception propagates without returning through the chain.

        **Feature: middleware-pipeline, Property 3: Exception propagation stops pipeline execution**
        **Validates: Requirements 2.8**
    """
    k = exception_index % len(markers)

    pipeline = MiddlewarePipeline()

    for i, marker in enumerate(markers):
        if i == k:
            mw = ExceptionMiddleware(marker, name=f"mw_{i}")
        else:
            mw = OrderTrackingMiddleware(marker, name=f"mw_{i}")
        pipeline.add(mw, name=f"mw_{i}")

    request = Request("GET", "/test")
    request.path_params = {}

    def handler(req: Request) -> MockResponse:
        if "order" not in req.path_params:
            req.path_params["order"] = []
        req.path_params["order"].append("handler")
        return MockResponse(status_code=200)

    try:
        pipeline.execute(request, handler)
    except RuntimeError:
        # Expected: ExceptionMiddleware raises RuntimeError; the trace recorded before
        # it propagated is what this property checks.
        pass

    actual_order = request.path_params.get("order", [])

    # K before-markers from preceding middleware + 1 exception marker
    expected_length = k + 1

    testbase.assert_equal(len(actual_order), expected_length,
        f"Trace should have {expected_length} entries ({k} before-markers + 1 "
        f"exception marker) when exception at position {k}, but had "
        f"{len(actual_order)}. Trace: {actual_order}.")


# =============================================================================
# Property 4: Positional insertion places middleware correctly
# Feature: middleware-pipeline, Property 4
# Validates: Requirements 3.1, 3.2, 3.3, 3.4
# =============================================================================

@given(
    markers=unique_marker_lists(min_size=2, max_size=6),
    constraints={"max_examples": 10},
)
def test_property_positional_insertion_start_places_at_index_zero(markers):
    """
        Property 4a: Adding middleware with position="start" places it at index 0.

        For any pipeline with existing middleware, adding a new middleware with
        position="start" should make it the first entry in the pipeline.
    """
    pipeline = MiddlewarePipeline()

    # Add initial middleware at default position
    for marker in markers:
        mw = OrderTrackingMiddleware(marker, name=marker)
        pipeline.add(mw, name=marker)

    # Add a new middleware at the start
    start_marker = "start_inserted"
    start_mw = OrderTrackingMiddleware(start_marker, name=start_marker)
    pipeline.add(start_mw, name=start_marker, position="start")

    names = pipeline.get_names()

    testbase.assert_equal(names[0], start_marker,
        f"Middleware added with position='start' should be at index 0, "
        f"but get_names() returned {names}.")


@given(
    markers=unique_marker_lists(min_size=2, max_size=6),
    constraints={"max_examples": 10},
)
def test_property_positional_insertion_end_places_at_last_index(markers):
    """
        Property 4b: Adding middleware with position="end" places it at the last index.

        For any pipeline with existing middleware, adding a new middleware with
        position="end" should make it the last entry in the pipeline.
    """
    pipeline = MiddlewarePipeline()

    # Add initial middleware at the start so they don't compete with end-position priority
    for marker in markers:
        mw = OrderTrackingMiddleware(marker, name=marker)
        pipeline.add(mw, name=marker, position="start")

    # Add a new middleware at the end
    end_marker = "end_inserted"
    end_mw = OrderTrackingMiddleware(end_marker, name=end_marker)
    pipeline.add(end_mw, name=end_marker, position="end")

    names = pipeline.get_names()

    testbase.assert_equal(names[-1], end_marker,
        f"Middleware added with position='end' should be at the last index, "
        f"but get_names() returned {names}.")


@given(
    markers=unique_marker_lists(min_size=2, max_size=6),
    constraints={"max_examples": 10},
)
def test_property_positional_insertion_before_places_immediately_before_target(markers):
    """
        Property 4c: Adding middleware with position="before:<name>" places it
        immediately before the named middleware.

        For any pipeline with named middleware, inserting before a target name
        should place the new middleware at the index where the target was,
        pushing the target one position later.
    """
    pipeline = MiddlewarePipeline()

    for marker in markers:
        mw = OrderTrackingMiddleware(marker, name=marker)
        pipeline.add(mw, name=marker)

    # Pick a target from the existing markers
    target_index = len(markers) // 2
    target_name = markers[target_index]

    before_marker = "before_inserted"
    before_mw = OrderTrackingMiddleware(before_marker, name=before_marker)
    pipeline.add(before_mw, name=before_marker, position=f"before:{target_name}")

    names = pipeline.get_names()
    new_index = names.index(before_marker)
    target_new_index = names.index(target_name)

    testbase.assert_equal(target_new_index, new_index + 1,
        f"Middleware inserted before '{target_name}' should be immediately "
        f"before it. Expected '{before_marker}' at index {new_index} and "
        f"'{target_name}' at index {new_index + 1}, but target is at "
        f"{target_new_index}. Names: {names}.")


@given(
    markers=unique_marker_lists(min_size=2, max_size=6),
    constraints={"max_examples": 10},
)
def test_property_positional_insertion_after_places_immediately_after_target(markers):
    """
        Property 4d: Adding middleware with position="after:<name>" places it
        immediately after the named middleware.

        For any pipeline with named middleware, inserting after a target name
        should place the new middleware at the index right after the target.
    """
    pipeline = MiddlewarePipeline()

    for marker in markers:
        mw = OrderTrackingMiddleware(marker, name=marker)
        pipeline.add(mw, name=marker)

    # Pick a target from the existing markers
    target_index = len(markers) // 2
    target_name = markers[target_index]

    after_marker = "after_inserted"
    after_mw = OrderTrackingMiddleware(after_marker, name=after_marker)
    pipeline.add(after_mw, name=after_marker, position=f"after:{target_name}")

    names = pipeline.get_names()
    target_new_index = names.index(target_name)
    new_index = names.index(after_marker)

    testbase.assert_equal(new_index, target_new_index + 1,
        f"Middleware inserted after '{target_name}' should be immediately "
        f"after it. Expected '{target_name}' at index {target_new_index} and "
        f"'{after_marker}' at index {target_new_index + 1}, but "
        f"'{after_marker}' is at {new_index}. Names: {names}.")


@given(
    markers=unique_marker_lists(min_size=3, max_size=6),
    constraints={"max_examples": 10},
)
def test_property_positional_insertion_preserves_execution_order(markers):
    """
        Property 4e: Positional insertion produces correct execution order.

        For any pipeline where middleware is inserted at various positions,
        executing the pipeline should invoke middleware in the order reflected
        by get_names().
    """
    pipeline = MiddlewarePipeline()

    # Add the first middleware normally
    first_marker = markers[0]
    pipeline.add(OrderTrackingMiddleware(first_marker, name=first_marker), name=first_marker)

    # Add the second middleware normally
    second_marker = markers[1]
    pipeline.add(OrderTrackingMiddleware(second_marker, name=second_marker), name=second_marker)

    # Insert a third middleware before the second
    third_marker = markers[2]
    pipeline.add(
        OrderTrackingMiddleware(third_marker, name=third_marker),
        name=third_marker,
        position=f"before:{second_marker}",
    )

    # Verify execution order matches get_names() order
    expected_names = pipeline.get_names()

    request = Request(method="GET", path="/test")
    request._path_params = {}

    handler_called = [False]

    def handler(req):
        if "order" not in req.path_params:
            req.path_params["order"] = []
        req.path_params["order"].append("handler")
        handler_called[0] = True
        return MockResponse(200)

    pipeline.execute(request, handler)

    actual_order = request.path_params.get("order", [])
    before_markers = [entry for entry in actual_order if entry.endswith("_before")]
    execution_names = [entry.replace("_before", "") for entry in before_markers]

    testbase.assert_equal(execution_names, expected_names,
        f"Execution order should match get_names() order after positional "
        f"insertion. Expected {expected_names}, got {execution_names}.")

    testbase.assert_true(handler_called[0],
        "Handler should have been called after all middleware executed.")


# =============================================================================
# Property 5: Missing name references raise appropriate errors
# Feature: middleware-pipeline, Property 5
# Validates: Requirements 3.5, 3.7
# =============================================================================

@composite
def pipeline_with_names_and_absent_name(draw, min_size=1, max_size=5):
    """
        Generate a list of unique middleware names for a pipeline and a name
        that is guaranteed not to be in the pipeline.
    """
    present = draw(unique_marker_lists(min_size=min_size, max_size=max_size))
    absent = draw(marker_strategy)
    base = absent
    idx = 0
    while absent in present:
        idx += 1
        absent = f"{base}{idx}"
    return present, absent


@given(
    data=pipeline_with_names_and_absent_name(min_size=1, max_size=5),
    constraints={"max_examples": 10},
)
def test_property_missing_name_before_raises_value_error(data):
    """
        Property 5a: Inserting with position='before:<name>' where the name
        does not exist in the pipeline raises ValueError.
    """
    present_names, absent_name = data

    pipeline = MiddlewarePipeline()
    for name in present_names:
        pipeline.add(OrderTrackingMiddleware(name, name=name), name=name)

    raised = False
    try:
        pipeline.add(
            OrderTrackingMiddleware("extra", name="extra"),
            name="extra",
            position=f"before:{absent_name}",
        )
    except ValueError:
        raised = True

    testbase.assert_true(raised,
        f"Expected ValueError when inserting before absent name "
        f"'{absent_name}' in pipeline with names {present_names}.")


@given(
    data=pipeline_with_names_and_absent_name(min_size=1, max_size=5),
    constraints={"max_examples": 10},
)
def test_property_missing_name_after_raises_value_error(data):
    """
        Property 5b: Inserting with position='after:<name>' where the name
        does not exist in the pipeline raises ValueError.
    """
    present_names, absent_name = data

    pipeline = MiddlewarePipeline()
    for name in present_names:
        pipeline.add(OrderTrackingMiddleware(name, name=name), name=name)

    raised = False
    try:
        pipeline.add(
            OrderTrackingMiddleware("extra", name="extra"),
            name="extra",
            position=f"after:{absent_name}",
        )
    except ValueError:
        raised = True

    testbase.assert_true(raised,
        f"Expected ValueError when inserting after absent name "
        f"'{absent_name}' in pipeline with names {present_names}.")


@given(
    data=pipeline_with_names_and_absent_name(min_size=1, max_size=5),
    constraints={"max_examples": 10},
)
def test_property_missing_name_remove_raises_key_error(data):
    """
        Property 5c: Calling remove(name) where the name does not exist
        in the pipeline raises KeyError.
    """
    present_names, absent_name = data

    pipeline = MiddlewarePipeline()
    for name in present_names:
        pipeline.add(OrderTrackingMiddleware(name, name=name), name=name)

    raised = False
    try:
        pipeline.remove(absent_name)
    except KeyError:
        raised = True

    testbase.assert_true(raised,
        f"Expected KeyError when removing absent name "
        f"'{absent_name}' from pipeline with names {present_names}.")


# =============================================================================
# Property 6: Remove by name reduces pipeline correctly
# Feature: middleware-pipeline, Property 6
# Validates: Requirements 3.6
# =============================================================================

@composite
def pipeline_names_with_removal_target(draw, min_size=2, max_size=6):
    """
        Generate a list of unique middleware names and pick one name
        from the list as the removal target.
    """
    names = draw(unique_marker_lists(min_size=min_size, max_size=max_size))
    target_index = draw(st.integers(0, len(names) - 1))
    return names, names[target_index]


@given(
    data=pipeline_names_with_removal_target(min_size=2, max_size=6),
    constraints={"max_examples": 10},
)
def test_property_remove_by_name_reduces_pipeline_length_by_one(data):
    """
        Property 6a: Removing a middleware by name reduces the pipeline
        length by exactly 1.
    """
    names, target_name = data

    pipeline = MiddlewarePipeline()
    for name in names:
        pipeline.add(OrderTrackingMiddleware(name, name=name), name=name)

    length_before = len(pipeline)

    pipeline.remove(target_name)

    length_after = len(pipeline)

    testbase.assert_equal(length_after, length_before - 1,
        f"Expected pipeline length to decrease by 1 after removing '{target_name}'. "
        f"Before: {length_before}, After: {length_after}.")


@given(
    data=pipeline_names_with_removal_target(min_size=2, max_size=6),
    constraints={"max_examples": 10},
)
def test_property_remove_by_name_removes_name_from_get_names(data):
    """
        Property 6b: After removing a middleware by name, the name no longer
        appears in get_names().
    """
    names, target_name = data

    pipeline = MiddlewarePipeline()
    for name in names:
        pipeline.add(OrderTrackingMiddleware(name, name=name), name=name)

    pipeline.remove(target_name)

    remaining_names = pipeline.get_names()

    testbase.assert_false(target_name in remaining_names,
        f"Expected '{target_name}' to be absent from get_names() after removal. "
        f"Remaining names: {remaining_names}.")


@given(
    data=pipeline_names_with_removal_target(min_size=2, max_size=6),
    constraints={"max_examples": 10},
)
def test_property_remove_by_name_preserves_other_middleware_order(data):
    """
        Property 6c: Removing a middleware by name preserves the relative
        order of all other middleware in the pipeline.
    """
    names, target_name = data

    pipeline = MiddlewarePipeline()
    for name in names:
        pipeline.add(OrderTrackingMiddleware(name, name=name), name=name)

    expected_remaining = [n for n in names if n != target_name]

    pipeline.remove(target_name)

    remaining_names = pipeline.get_names()

    testbase.assert_equal(remaining_names, expected_remaining,
        f"Expected remaining middleware order {expected_remaining} after removing "
        f"'{target_name}', but got {remaining_names}.")


# =============================================================================
# Property 7: Priority ordering within positional groups
# Validates: Requirements 3.8
# =============================================================================

@composite
def priority_middleware_list(draw, min_size=2, max_size=6):
    """
        Generate a list of (name, priority) tuples with unique names and
        distinct priorities for testing priority-based ordering.
    """
    size = draw(st.integers(min_size, max_size))
    names = []
    seen = set()
    while len(names) < size:
        candidate = draw(st.text(
            alphabet="abcdefghijklmnopqrstuvwxyz",
            min_size=3,
            max_size=8,
        ))
        if candidate not in seen:
            seen.add(candidate)
            names.append(candidate)

    priorities = []
    used_priorities = set()
    while len(priorities) < size:
        candidate = draw(st.integers(1, 200))
        if candidate not in used_priorities:
            used_priorities.add(candidate)
            priorities.append(candidate)

    return list(zip(names, priorities))


@given(
    items=priority_middleware_list(min_size=2, max_size=6),
    constraints={"max_examples": 10}
)
def test_property_priority_ordering_end_position(items):
    """
        Property 7a: When multiple middleware are added at position="end"
        with different priorities, they execute in ascending priority order
        (lower priority values execute first).
    """
    pipeline = MiddlewarePipeline()

    for name, priority in items:
        mw = OrderTrackingMiddleware(name, name=name)
        pipeline.add(mw, name=name, position="end", priority=priority)

    expected_order = [name for name, _ in sorted(items, key=lambda x: x[1])]
    actual_order = pipeline.get_names()

    testbase.assert_equal(actual_order, expected_order,
        f"Expected middleware ordered by ascending priority {expected_order}, "
        f"but got {actual_order}. Input items: {items}.")


@given(
    items=priority_middleware_list(min_size=2, max_size=6),
    constraints={"max_examples": 10}
)
def test_property_priority_ordering_start_position(items):
    """
        Property 7b: When multiple middleware are added at position="start"
        with different priorities, they execute in ascending priority order
        (lower priority values execute first).
    """
    pipeline = MiddlewarePipeline()

    for name, priority in items:
        mw = OrderTrackingMiddleware(name, name=name)
        pipeline.add(mw, name=name, position="start", priority=priority)

    expected_order = [name for name, _ in sorted(items, key=lambda x: x[1])]
    actual_order = pipeline.get_names()

    testbase.assert_equal(actual_order, expected_order,
        f"Expected middleware ordered by ascending priority {expected_order}, "
        f"but got {actual_order}. Input items: {items}.")


@given(
    items=priority_middleware_list(min_size=2, max_size=6),
    constraints={"max_examples": 10}
)
def test_property_priority_ordering_execution_matches_get_names(items):
    """
        Property 7c: The actual execution order of middleware matches the
        order reported by get_names() when priority ordering is applied.
    """
    pipeline = MiddlewarePipeline()

    for name, priority in items:
        mw = OrderTrackingMiddleware(name, name=name)
        pipeline.add(mw, name=name, position="end", priority=priority)

    request = Request("GET", "/test")
    request.path_params = {}

    def handler(req):
        return MockResponse(200, b"ok")

    pipeline.execute(request, handler)

    trace = request.path_params.get("order", [])
    before_markers = [m.replace("_before", "") for m in trace if m.endswith("_before")]

    expected_order = pipeline.get_names()

    testbase.assert_equal(before_markers, expected_order,
        f"Execution order {before_markers} does not match get_names() order "
        f"{expected_order}. Input items: {items}.")


# =============================================================================
# Property 8: get_names matches iteration order
# Feature: middleware-pipeline, Property 8
# Validates: Requirements 3.9, 12.1, 12.2
# =============================================================================

@given(
    markers=unique_marker_lists(min_size=1, max_size=8),
    constraints={"max_examples": 10},
)
def test_property_get_names_length_matches_len(markers):
    """
        Property 8a: The length of get_names() equals len(pipeline).
    """
    pipeline = MiddlewarePipeline()

    for marker in markers:
        mw = OrderTrackingMiddleware(marker, name=marker)
        pipeline.add(mw, name=marker)

    names = pipeline.get_names()

    testbase.assert_equal(len(names), len(pipeline),
        f"get_names() returned {len(names)} names but len(pipeline) is "
        f"{len(pipeline)}. Markers: {markers}.")


@given(
    markers=unique_marker_lists(min_size=1, max_size=8),
    constraints={"max_examples": 10},
)
def test_property_get_names_matches_iteration_order(markers):
    """
        Property 8b: Each name from get_names() corresponds to the name of
        the entry at the same index when iterating over the pipeline.
    """
    pipeline = MiddlewarePipeline()

    for marker in markers:
        mw = OrderTrackingMiddleware(marker, name=marker)
        pipeline.add(mw, name=marker)

    names = pipeline.get_names()
    iter_names = [entry.name for entry in pipeline]

    testbase.assert_equal(names, iter_names,
        f"get_names() {names} does not match iteration order {iter_names}. "
        f"Markers: {markers}.")


@given(
    markers=unique_marker_lists(min_size=2, max_size=8),
    constraints={"max_examples": 10},
)
def test_property_get_names_consistent_after_removal(markers):
    """
        Property 8c: After removing a middleware by name, get_names() still
        matches iteration order and len(pipeline).
    """
    pipeline = MiddlewarePipeline()

    for marker in markers:
        mw = OrderTrackingMiddleware(marker, name=marker)
        pipeline.add(mw, name=marker)

    # Remove the first middleware
    removed = markers[0]
    pipeline.remove(removed)

    names = pipeline.get_names()
    iter_names = [entry.name for entry in pipeline]

    testbase.assert_equal(len(names), len(pipeline),
        f"After removing '{removed}', get_names() returned {len(names)} names "
        f"but len(pipeline) is {len(pipeline)}. Markers: {markers}.")

    testbase.assert_equal(names, iter_names,
        f"After removing '{removed}', get_names() {names} does not match "
        f"iteration order {iter_names}. Markers: {markers}.")


# =============================================================================
# Property 19: Pipeline repr contains all middleware names
# Feature: middleware-pipeline, Property 19
# Validates: Requirements 12.3
# =============================================================================

@given(
    markers=unique_marker_lists(min_size=1, max_size=8),
    constraints={"max_examples": 10},
)
def test_property_pipeline_repr_contains_all_middleware_names(markers):
    """
        Property 19: For any pipeline with named middleware, repr(pipeline)
        contains every middleware name present in the pipeline.
    """
    pipeline = MiddlewarePipeline()

    for marker in markers:
        mw = OrderTrackingMiddleware(marker, name=marker)
        pipeline.add(mw, name=marker)

    pipeline_repr = repr(pipeline)

    for marker in markers:
        testbase.assert_true(marker in pipeline_repr,
            f"repr(pipeline) should contain middleware name '{marker}' but got: "
            f"{pipeline_repr}. Markers: {markers}.")


@given(
    markers=unique_marker_lists(min_size=1, max_size=8),
    constraints={"max_examples": 10},
)
def test_property_pipeline_repr_name_count_matches_pipeline_length(markers):
    """
        Property 19b: The number of names visible in repr matches the pipeline
        length, ensuring no middleware is omitted or duplicated in the repr.
    """
    pipeline = MiddlewarePipeline()

    for marker in markers:
        mw = OrderTrackingMiddleware(marker, name=marker)
        pipeline.add(mw, name=marker)

    pipeline_repr = repr(pipeline)

    # The repr format is MiddlewarePipeline([name1, name2, ...])
    # Extract the list portion between the brackets
    inner = pipeline_repr.split("[", 1)[1].rsplit("]", 1)[0]
    repr_names = [n.strip() for n in inner.split(",")]

    testbase.assert_equal(len(repr_names), len(markers),
        f"repr shows {len(repr_names)} names but pipeline has {len(markers)} "
        f"middleware. repr: {pipeline_repr}. Markers: {markers}.")


# =============================================================================
# Property 24: as_dict returns entries with required keys
# Validates: Requirements 14.1
# =============================================================================

VALID_SCOPES = ["global", "blueprint", "route"]

@composite
def pipeline_with_varied_entries(draw, min_size=1, max_size=6):
    """
        Generate a list of (name, priority, scope) tuples with unique names
        for building a pipeline with varied entry metadata.
    """
    size = draw(st.integers(min_size, max_size))
    entries = []
    seen = set()
    for _ in range(size):
        while True:
            candidate = draw(st.text(
                alphabet="abcdefghijklmnopqrstuvwxyz",
                min_size=3,
                max_size=8,
            ))
            if candidate not in seen:
                seen.add(candidate)
                break
        priority = draw(st.integers(1, 200))
        scope = draw(st.sampled_from(VALID_SCOPES))
        entries.append((candidate, priority, scope))
    return entries


@given(
    entries=pipeline_with_varied_entries(min_size=1, max_size=6),
    constraints={"max_examples": 10}
)
def test_property_as_dict_length_matches_pipeline_length(entries):
    """
        Property 24a: as_dict() returns a list whose length equals len(pipeline).
    """
    pipeline = MiddlewarePipeline()

    for name, priority, scope in entries:
        mw = OrderTrackingMiddleware(name, name=name)
        pipeline.add(mw, name=name, priority=priority, scope=scope)

    result = pipeline.as_dict()

    testbase.assert_equal(len(result), len(pipeline),
        f"as_dict() returned {len(result)} entries but pipeline has "
        f"{len(pipeline)} middleware. Entries: {entries}.")


@given(
    entries=pipeline_with_varied_entries(min_size=1, max_size=6),
    constraints={"max_examples": 10}
)
def test_property_as_dict_entries_contain_required_keys(entries):
    """
        Property 24b: Each dictionary in as_dict() contains exactly the keys
        'name', 'priority', and 'scope'.
    """
    pipeline = MiddlewarePipeline()

    for name, priority, scope in entries:
        mw = OrderTrackingMiddleware(name, name=name)
        pipeline.add(mw, name=name, priority=priority, scope=scope)

    required_keys = {"name", "priority", "scope"}
    result = pipeline.as_dict()

    for idx, entry_dict in enumerate(result):
        actual_keys = set(entry_dict.keys())
        testbase.assert_equal(actual_keys, required_keys,
            f"Entry at index {idx} has keys {actual_keys} but expected "
            f"{required_keys}. Entry: {entry_dict}.")


@given(
    entries=pipeline_with_varied_entries(min_size=1, max_size=6),
    constraints={"max_examples": 10}
)
def test_property_as_dict_names_match_get_names(entries):
    """
        Property 24c: The names in as_dict() match the names returned by
        get_names() in the same order.
    """
    pipeline = MiddlewarePipeline()

    for name, priority, scope in entries:
        mw = OrderTrackingMiddleware(name, name=name)
        pipeline.add(mw, name=name, priority=priority, scope=scope)

    result = pipeline.as_dict()
    dict_names = [d["name"] for d in result]
    pipeline_names = pipeline.get_names()

    testbase.assert_equal(dict_names, pipeline_names,
        f"as_dict() names {dict_names} do not match get_names() "
        f"{pipeline_names}. Entries: {entries}.")


# =============================================================================
# Property 23: Pipeline serialization round trip
# Validates: Requirements 14.4
# =============================================================================

@given(
    entries=pipeline_with_varied_entries(min_size=1, max_size=6),
    constraints={"max_examples": 10}
)
def test_property_serialization_round_trip_preserves_names(entries):
    """
        Property 23a: Serializing via as_dict() then reconstructing via
        from_config() with a factory registry produces a pipeline with the
        same middleware names in the same order.
    """
    pipeline = MiddlewarePipeline()

    for name, priority, scope in entries:
        mw = OrderTrackingMiddleware(name, name=name)
        pipeline.add(mw, name=name, priority=priority, scope=scope)

    serialized = pipeline.as_dict()

    # Build a factory registry that produces middleware with the correct names
    factory_registry = {}
    for name, _priority, _scope in entries:
        def _make_factory(n):
            def factory():
                return OrderTrackingMiddleware(n, name=n)
            return factory
        factory_registry[name] = _make_factory(name)

    restored = MiddlewarePipeline.from_config(serialized, factory_registry=factory_registry)

    original_names = pipeline.get_names()
    restored_names = restored.get_names()

    testbase.assert_equal(restored_names, original_names,
        f"Round-trip names mismatch. Original: {original_names}, "
        f"Restored: {restored_names}. Serialized config: {serialized}.")


@given(
    entries=pipeline_with_varied_entries(min_size=1, max_size=6),
    constraints={"max_examples": 10}
)
def test_property_serialization_round_trip_preserves_length(entries):
    """
        Property 23b: The reconstructed pipeline has the same length as the
        original pipeline.
    """
    pipeline = MiddlewarePipeline()

    for name, priority, scope in entries:
        mw = OrderTrackingMiddleware(name, name=name)
        pipeline.add(mw, name=name, priority=priority, scope=scope)

    serialized = pipeline.as_dict()

    factory_registry = {}
    for name, _priority, _scope in entries:
        def _make_factory(n):
            def factory():
                return OrderTrackingMiddleware(n, name=n)
            return factory
        factory_registry[name] = _make_factory(name)

    restored = MiddlewarePipeline.from_config(serialized, factory_registry=factory_registry)

    testbase.assert_equal(len(restored), len(pipeline),
        f"Round-trip length mismatch. Original: {len(pipeline)}, "
        f"Restored: {len(restored)}. Entries: {entries}.")


@given(
    entries=pipeline_with_varied_entries(min_size=1, max_size=6),
    constraints={"max_examples": 10}
)
def test_property_serialization_round_trip_preserves_priority_and_scope(entries):
    """
        Property 23c: The reconstructed pipeline preserves priority and scope
        metadata for each entry.
    """
    pipeline = MiddlewarePipeline()

    for name, priority, scope in entries:
        mw = OrderTrackingMiddleware(name, name=name)
        pipeline.add(mw, name=name, priority=priority, scope=scope)

    serialized = pipeline.as_dict()

    factory_registry = {}
    for name, _priority, _scope in entries:
        def _make_factory(n):
            def factory():
                return OrderTrackingMiddleware(n, name=n)
            return factory
        factory_registry[name] = _make_factory(name)

    restored = MiddlewarePipeline.from_config(serialized, factory_registry=factory_registry)

    original_dicts = pipeline.as_dict()
    restored_dicts = restored.as_dict()

    testbase.assert_equal(len(restored_dicts), len(original_dicts),
        f"Round-trip as_dict() length mismatch. Original: {len(original_dicts)}, "
        f"Restored: {len(restored_dicts)}.")

    for idx, (orig, rest) in enumerate(zip(original_dicts, restored_dicts)):
        testbase.assert_equal(rest["name"], orig["name"],
            f"Name mismatch at index {idx}. Original: {orig}, Restored: {rest}.")
        testbase.assert_equal(rest["priority"], orig["priority"],
            f"Priority mismatch at index {idx}. Original: {orig}, Restored: {rest}.")
        testbase.assert_equal(rest["scope"], orig["scope"],
            f"Scope mismatch at index {idx}. Original: {orig}, Restored: {rest}.")

# =============================================================================
# Property 26: Protocol validation rejects non-conforming middleware
# Validates: Requirements 1.7, 1.8
# =============================================================================


@given(
    value=st.sampled_from([
        42,
        3.14,
        True,
        "not_a_middleware",
        None,
        [1, 2, 3],
        {"key": "value"},
        (1, 2),
    ]),
    constraints={"max_examples": 10}
)
def test_property_protocol_validation_rejects_non_callable_objects(value):
    """
        Non-callable objects should be rejected by the pipeline with a TypeError.
    """
    pipeline = MiddlewarePipeline()

    raised = False
    error_msg = ""

    try:
        pipeline.add(value, name="invalid")
    except TypeError as terr:
        raised = True
        error_msg = str(terr)

    testbase.assert_true(raised,
        f"Expected TypeError for non-conforming middleware {value!r}, but no exception was raised.")

    testbase.assert_true("does not conform" in error_msg,
        f"TypeError message should contain 'does not conform', got: {error_msg}")


class _ZeroArgCallable:
    """Callable with zero required parameters — not a valid middleware."""

    def __call__(self):
        return None


class _OneArgCallable:
    """Callable with one required parameter — not a valid middleware."""

    def __call__(self, request):
        return None


@given(
    choice=st.sampled_from(["zero_arg", "one_arg"]),
    constraints={"max_examples": 20}
)
def test_property_protocol_validation_rejects_callable_with_wrong_arity(choice):
    """
        Callables that do not accept at least two positional parameters
        (request, call_next) should be rejected with a TypeError.
    """
    if choice == "zero_arg":
        bad_middleware = _ZeroArgCallable()
    else:
        bad_middleware = _OneArgCallable()

    pipeline = MiddlewarePipeline()

    raised = False
    error_msg = ""

    try:
        pipeline.add(bad_middleware, name="bad")
    except TypeError as terr:
        raised = True
        error_msg = str(terr)

    testbase.assert_true(raised,
        f"Expected TypeError for callable with wrong arity ({choice}), "
        f"but no exception was raised.")

    testbase.assert_true("does not conform" in error_msg,
        f"TypeError message should contain 'does not conform', got: {error_msg}")


class _ValidProtocolMiddleware:
    """Conforms to the Middleware protocol: has name and __call__(request, call_next)."""

    def __init__(self, name: str):
        self.name = name

    def __call__(self, request, call_next):
        return call_next(request)


@given(
    name=st.text(min_size=1, max_size=10, alphabet="abcdefghijklmnopqrstuvwxyz"),
    constraints={"max_examples": 10}
)
def test_property_protocol_validation_accepts_conforming_middleware(name):
    """
        Objects conforming to the Middleware protocol should be accepted
        without raising any exception.
    """
    middleware = _ValidProtocolMiddleware(name=name)
    pipeline = MiddlewarePipeline()

    raised = False
    error_info = ""

    try:
        pipeline.add(middleware, name=name)
    except TypeError as terr:
        raised = True
        error_info = str(terr)

    testbase.assert_false(raised,
        f"Valid middleware '{name}' should not raise TypeError, but got: {error_info}")

    names = pipeline.get_names()
    testbase.assert_true(name in names,
        f"Valid middleware '{name}' should appear in pipeline names after add(). "
        f"Got names: {names}")


@given(
    name=st.text(min_size=1, max_size=10, alphabet="abcdefghijklmnopqrstuvwxyz"),
    constraints={"max_examples": 10}
)
def test_property_protocol_validation_accepts_plain_callable(name):
    """
        Plain callables with (request, call_next) signature should be
        accepted without raising any exception.
    """
    def plain_middleware(request, call_next):
        return call_next(request)

    pipeline = MiddlewarePipeline()

    raised = False
    error_info = ""

    try:
        pipeline.add(plain_middleware, name=name)
    except TypeError as terr:
        raised = True
        error_info = str(terr)

    testbase.assert_false(raised,
        f"Plain callable middleware should not raise TypeError, but got: {error_info}")

    names = pipeline.get_names()
    testbase.assert_true(name in names,
        f"Plain callable middleware '{name}' should appear in pipeline names. "
        f"Got names: {names}")



# =============================================================================
# Property 25: Middleware context attached to request during pipeline execution
# Feature: middleware-pipeline, Property 25
# Validates: Requirements 8.5
# =============================================================================

from ccai.webworks.routing.middlewarecontext import MiddlewareContext


class ContextCapturingMiddleware:
    """
        Middleware that captures the middleware_context from the request
        during pipeline execution.
    """

    def __init__(self, name: str = "context_capturer"):
        self.name = name
        self.captured_context = None
        return

    def __call__(self, request: Request, call_next: Callable) -> MockResponse:
        self.captured_context = request.middleware_context
        return call_next(request)


@given(
    scope=st.sampled_from(["global", "blueprint", "route"]),
    markers=unique_marker_lists(min_size=1, max_size=4),
    constraints={"max_examples": 10},
)
def test_property_middleware_context_attached_to_request_during_pipeline_execution(scope, markers):
    """
        Property 25: Middleware context attached to request during pipeline execution.

        For any request processed through the pipeline with a MiddlewareContext
        attached, the request.middleware_context attribute should be set to a
        MiddlewareContext instance (not None) by the time middleware executes.

        **Feature: middleware-pipeline, Property 25: Middleware context attached to request during pipeline execution**
        **Validates: Requirements 8.5**
    """
    pipeline = MiddlewarePipeline()

    # Add some regular middleware before the capturing middleware
    for i, marker in enumerate(markers):
        mw = OrderTrackingMiddleware(marker, name=f"mw_{i}")
        pipeline.add(mw, name=f"mw_{i}")

    # Add a context-capturing middleware at the start
    capturer = ContextCapturingMiddleware(name="capturer")
    pipeline.add(capturer, name="capturer", position="start")

    request = Request("GET", "/test")
    request.path_params = {}

    # Attach a MiddlewareContext before execution (as the Dispatcher would)
    ctx = MiddlewareContext(endpoint_descriptor=None, scope=scope)
    request.middleware_context = ctx

    def handler(req: Request) -> MockResponse:
        return MockResponse(status_code=200)

    pipeline.execute(request, handler)

    # The capturing middleware should have seen the context
    testbase.assert_true(capturer.captured_context is not None,
        f"Middleware should see a non-None middleware_context on the request "
        f"during pipeline execution. scope={scope}, markers={markers}.")

    testbase.assert_true(isinstance(capturer.captured_context, MiddlewareContext),
        f"request.middleware_context should be a MiddlewareContext instance, "
        f"got {type(capturer.captured_context).__name__}.")

    testbase.assert_equal(capturer.captured_context.scope, scope,
        f"MiddlewareContext scope should be '{scope}', "
        f"got '{capturer.captured_context.scope}'.")

    testbase.assert_equal(capturer.captured_context.endpoint_descriptor, None,
        f"MiddlewareContext endpoint_descriptor should be None when middleware "
        f"executes before routing, got {capturer.captured_context.endpoint_descriptor}.")


@given(
    markers=unique_marker_lists(min_size=1, max_size=4),
    constraints={"max_examples": 10},
)
def test_property_middleware_context_default_is_none(markers):
    """
        Property 25 (default): When no MiddlewareContext is attached to the
        request, request.middleware_context should be None by default.

        **Feature: middleware-pipeline, Property 25: Middleware context attached to request during pipeline execution**
        **Validates: Requirements 8.5**
    """
    pipeline = MiddlewarePipeline()

    capturer = ContextCapturingMiddleware(name="capturer")
    pipeline.add(capturer, name="capturer")

    for i, marker in enumerate(markers):
        mw = OrderTrackingMiddleware(marker, name=f"mw_{i}")
        pipeline.add(mw, name=f"mw_{i}")

    request = Request("GET", "/test")
    request.path_params = {}
    # Do NOT attach middleware_context — it should default to None

    def handler(req: Request) -> MockResponse:
        return MockResponse(status_code=200)

    pipeline.execute(request, handler)

    testbase.assert_equal(capturer.captured_context, None,
        f"request.middleware_context should default to None when not explicitly set. "
        f"Got: {capturer.captured_context}.")


@given(
    scope=st.sampled_from(["global", "blueprint", "route"]),
    markers=unique_marker_lists(min_size=2, max_size=5),
    constraints={"max_examples": 10},
)
def test_property_middleware_context_visible_to_all_middleware_in_chain(scope, markers):
    """
        Property 25 (visibility): When a MiddlewareContext is attached to the
        request, every middleware in the chain should see the same context
        instance.

        **Feature: middleware-pipeline, Property 25: Middleware context attached to request during pipeline execution**
        **Validates: Requirements 8.5**
    """
    pipeline = MiddlewarePipeline()

    capturers = []
    for i, marker in enumerate(markers):
        cap = ContextCapturingMiddleware(name=f"cap_{i}")
        capturers.append(cap)
        pipeline.add(cap, name=f"cap_{i}")

    request = Request("GET", "/test")
    request.path_params = {}

    ctx = MiddlewareContext(endpoint_descriptor=None, scope=scope)
    request.middleware_context = ctx

    def handler(req: Request) -> MockResponse:
        return MockResponse(status_code=200)

    pipeline.execute(request, handler)

    for i, cap in enumerate(capturers):
        testbase.assert_true(cap.captured_context is ctx,
            f"Middleware at position {i} should see the same MiddlewareContext "
            f"instance (identity check). scope={scope}, markers={markers}.")


if __name__ == "__main__":
    from ccai.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
