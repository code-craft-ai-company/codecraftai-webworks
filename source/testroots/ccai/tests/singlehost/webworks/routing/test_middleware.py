"""
    Tests for the Middleware module.
    
    This module contains unit tests for the Middleware protocol,
    AsyncMiddleware protocol, and MiddlewarePipeline class.
"""

from typing import Callable, Dict

from ccai.webworks.routing.middleware import (
    Middleware,
    AsyncMiddleware,
    MiddlewareEntry,
    MiddlewarePipeline,
)
from ccai.webworks.routing.request import Request


# =============================================================================
# Helper Classes for Testing
# =============================================================================

class MockResponse:
    """
        Mock Response class for testing middleware.
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


class SimpleMiddleware:
    """
        Simple middleware that adds a marker to the request path_params.
    """
    
    def __init__(self, marker: str, name: str = None):
        self.marker = marker
        self.name = name
        self.before_called = False
        self.after_called = False
        return
    
    def __call__(self, request: Request, call_next: Callable) -> MockResponse:
        # Before: mark that we were called
        self.before_called = True
        if "markers" not in request.path_params:
            request.path_params["markers"] = []
        request.path_params["markers"].append(f"{self.marker}_before")
        
        # Call next
        response = call_next(request)
        
        # After: mark that we processed the response
        self.after_called = True
        request.path_params["markers"].append(f"{self.marker}_after")
        
        return response


class ShortCircuitMiddleware:
    """
        Middleware that short-circuits the pipeline.
    """
    
    def __init__(self, status_code: int = 401, name: str = None):
        self.status_code = status_code
        self.name = name
        return
    
    def __call__(self, request: Request, call_next: Callable) -> MockResponse:
        # Short-circuit: return response without calling call_next
        return MockResponse(status_code=self.status_code, body=b"Short-circuited")


class ModifyingMiddleware:
    """
        Middleware that modifies request and response.
    """
    
    def __init__(self, request_header: str = None, response_header: str = None, name: str = None):
        self.request_header = request_header
        self.response_header = response_header
        self.name = name
        return
    
    def __call__(self, request: Request, call_next: Callable) -> MockResponse:
        # Modify request (add to path_params since headers are immutable)
        if self.request_header:
            request.path_params["added_header"] = self.request_header
        
        # Call next
        response = call_next(request)
        
        # Modify response (create new response with added header)
        if self.response_header:
            new_headers = dict(response.headers)
            new_headers["X-Modified"] = self.response_header
            return MockResponse(
                status_code=response.status_code,
                body=response.body,
                headers=new_headers
            )
        
        return response


# =============================================================================
# Unit Tests for MiddlewareEntry
# =============================================================================

def test_middleware_entry_stores_middleware():
    """
        Test that MiddlewareEntry stores the middleware callable.
    """
    mw = SimpleMiddleware("test")
    entry = MiddlewareEntry(mw)
    
    if entry.middleware is not mw:
        errmsg = "Expected middleware to be stored"
        raise AssertionError(errmsg)
    
    return


def test_middleware_entry_stores_explicit_name():
    """
        Test that MiddlewareEntry stores explicit name.
    """
    mw = SimpleMiddleware("test")
    entry = MiddlewareEntry(mw, name="explicit_name")
    
    if entry.name != "explicit_name":
        errmsg = f"Expected name 'explicit_name', got '{entry.name}'"
        raise AssertionError(errmsg)
    
    return


def test_middleware_entry_extracts_name_from_middleware():
    """
        Test that MiddlewareEntry extracts name from middleware.
    """
    mw = SimpleMiddleware("test", name="mw_name")
    entry = MiddlewareEntry(mw)
    
    if entry.name != "mw_name":
        errmsg = f"Expected name 'mw_name', got '{entry.name}'"
        raise AssertionError(errmsg)
    
    return


def test_middleware_entry_explicit_name_overrides():
    """
        Test that explicit name overrides middleware name.
    """
    mw = SimpleMiddleware("test", name="mw_name")
    entry = MiddlewareEntry(mw, name="explicit_name")
    
    if entry.name != "explicit_name":
        errmsg = f"Expected name 'explicit_name', got '{entry.name}'"
        raise AssertionError(errmsg)
    
    return


def test_middleware_entry_name_is_none_when_not_provided():
    """
        Test that name is None when not provided.
    """
    mw = SimpleMiddleware("test")  # name defaults to None
    entry = MiddlewareEntry(mw)
    
    if entry.name is not None:
        errmsg = f"Expected name None, got '{entry.name}'"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for MiddlewarePipeline - Basic Operations
# =============================================================================

def test_pipeline_starts_empty():
    """
        Test that pipeline starts empty.
    """
    pipeline = MiddlewarePipeline()
    
    if len(pipeline) != 0:
        errmsg = f"Expected empty pipeline, got length {len(pipeline)}"
        raise AssertionError(errmsg)
    
    return


def test_pipeline_add_increases_length():
    """
        Test that add() increases pipeline length.
    """
    pipeline = MiddlewarePipeline()
    mw = SimpleMiddleware("test")
    
    pipeline.add(mw)
    
    if len(pipeline) != 1:
        errmsg = f"Expected length 1, got {len(pipeline)}"
        raise AssertionError(errmsg)
    
    return


def test_pipeline_add_multiple():
    """
        Test that multiple middleware can be added.
    """
    pipeline = MiddlewarePipeline()
    
    pipeline.add(SimpleMiddleware("a"))
    pipeline.add(SimpleMiddleware("b"))
    pipeline.add(SimpleMiddleware("c"))
    
    if len(pipeline) != 3:
        errmsg = f"Expected length 3, got {len(pipeline)}"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for MiddlewarePipeline - Positioning
# =============================================================================

def test_pipeline_add_end_appends():
    """
        Test that position='end' appends middleware.
    """
    pipeline = MiddlewarePipeline()
    
    pipeline.add(SimpleMiddleware("a", name="a"), name="a")
    pipeline.add(SimpleMiddleware("b", name="b"), name="b", position="end")
    
    names = pipeline.get_names()
    
    if names != ["a", "b"]:
        errmsg = f"Expected ['a', 'b'], got {names}"
        raise AssertionError(errmsg)
    
    return


def test_pipeline_add_start_prepends():
    """
        Test that position='start' prepends middleware.
    """
    pipeline = MiddlewarePipeline()
    
    pipeline.add(SimpleMiddleware("a", name="a"), name="a")
    pipeline.add(SimpleMiddleware("b", name="b"), name="b", position="start")
    
    names = pipeline.get_names()
    
    if names != ["b", "a"]:
        errmsg = f"Expected ['b', 'a'], got {names}"
        raise AssertionError(errmsg)
    
    return


def test_pipeline_add_before_inserts_before():
    """
        Test that position='before:<name>' inserts before named middleware.
    """
    pipeline = MiddlewarePipeline()
    
    pipeline.add(SimpleMiddleware("a", name="a"), name="a")
    pipeline.add(SimpleMiddleware("c", name="c"), name="c")
    pipeline.add(SimpleMiddleware("b", name="b"), name="b", position="before:c")
    
    names = pipeline.get_names()
    
    if names != ["a", "b", "c"]:
        errmsg = f"Expected ['a', 'b', 'c'], got {names}"
        raise AssertionError(errmsg)
    
    return


def test_pipeline_add_after_inserts_after():
    """
        Test that position='after:<name>' inserts after named middleware.
    """
    pipeline = MiddlewarePipeline()
    
    pipeline.add(SimpleMiddleware("a", name="a"), name="a")
    pipeline.add(SimpleMiddleware("c", name="c"), name="c")
    pipeline.add(SimpleMiddleware("b", name="b"), name="b", position="after:a")
    
    names = pipeline.get_names()
    
    if names != ["a", "b", "c"]:
        errmsg = f"Expected ['a', 'b', 'c'], got {names}"
        raise AssertionError(errmsg)
    
    return


def test_pipeline_add_before_unknown_raises():
    """
        Test that position='before:<unknown>' raises ValueError.
    """
    pipeline = MiddlewarePipeline()
    pipeline.add(SimpleMiddleware("a", name="a"), name="a")
    
    try:
        pipeline.add(SimpleMiddleware("b"), position="before:unknown")
        errmsg = "Expected ValueError for unknown middleware"
        raise AssertionError(errmsg)
    except ValueError as e:
        if "unknown" not in str(e):
            errmsg = f"Expected error message to mention 'unknown', got '{e}'"
            raise AssertionError(errmsg)
    
    return


def test_pipeline_add_after_unknown_raises():
    """
        Test that position='after:<unknown>' raises ValueError.
    """
    pipeline = MiddlewarePipeline()
    pipeline.add(SimpleMiddleware("a", name="a"), name="a")
    
    try:
        pipeline.add(SimpleMiddleware("b"), position="after:unknown")
        errmsg = "Expected ValueError for unknown middleware"
        raise AssertionError(errmsg)
    except ValueError as e:
        if "unknown" not in str(e):
            errmsg = f"Expected error message to mention 'unknown', got '{e}'"
            raise AssertionError(errmsg)
    
    return


def test_pipeline_add_invalid_position_raises():
    """
        Test that invalid position raises ValueError.
    """
    pipeline = MiddlewarePipeline()
    
    try:
        pipeline.add(SimpleMiddleware("a"), position="invalid")
        errmsg = "Expected ValueError for invalid position"
        raise AssertionError(errmsg)
    except ValueError as e:
        if "invalid" not in str(e).lower():
            errmsg = f"Expected error message to mention 'invalid', got '{e}'"
            raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for MiddlewarePipeline - Remove
# =============================================================================

def test_pipeline_remove_by_name():
    """
        Test that remove() removes middleware by name.
    """
    pipeline = MiddlewarePipeline()
    
    pipeline.add(SimpleMiddleware("a", name="a"), name="a")
    pipeline.add(SimpleMiddleware("b", name="b"), name="b")
    pipeline.add(SimpleMiddleware("c", name="c"), name="c")
    
    pipeline.remove("b")
    
    names = pipeline.get_names()
    
    if names != ["a", "c"]:
        errmsg = f"Expected ['a', 'c'], got {names}"
        raise AssertionError(errmsg)
    
    return


def test_pipeline_remove_unknown_raises():
    """
        Test that remove() raises KeyError for unknown name.
    """
    pipeline = MiddlewarePipeline()
    pipeline.add(SimpleMiddleware("a", name="a"), name="a")
    
    try:
        pipeline.remove("unknown")
        errmsg = "Expected KeyError for unknown middleware"
        raise AssertionError(errmsg)
    except KeyError as e:
        if "unknown" not in str(e):
            errmsg = f"Expected error message to mention 'unknown', got '{e}'"
            raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for MiddlewarePipeline - Execute
# =============================================================================

def test_pipeline_execute_calls_handler():
    """
        Test that execute() calls the handler.
    """
    pipeline = MiddlewarePipeline()
    request = Request("GET", "/test")
    
    handler_called = [False]
    
    def handler(req: Request) -> MockResponse:
        handler_called[0] = True
        return MockResponse(status_code=200, body=b"OK")
    
    response = pipeline.execute(request, handler)
    
    if not handler_called[0]:
        errmsg = "Expected handler to be called"
        raise AssertionError(errmsg)
    
    if response.status_code != 200:
        errmsg = f"Expected status 200, got {response.status_code}"
        raise AssertionError(errmsg)
    
    return


def test_pipeline_execute_middleware_order():
    """
        Test that middleware executes in correct order.
    """
    pipeline = MiddlewarePipeline()
    
    mw_a = SimpleMiddleware("a", name="a")
    mw_b = SimpleMiddleware("b", name="b")
    mw_c = SimpleMiddleware("c", name="c")
    
    pipeline.add(mw_a, name="a")
    pipeline.add(mw_b, name="b")
    pipeline.add(mw_c, name="c")
    
    request = Request("GET", "/test")
    request.path_params = {}
    
    def handler(req: Request) -> MockResponse:
        req.path_params["markers"].append("handler")
        return MockResponse(status_code=200)
    
    pipeline.execute(request, handler)
    
    expected_markers = [
        "a_before", "b_before", "c_before",
        "handler",
        "c_after", "b_after", "a_after"
    ]
    
    actual_markers = request.path_params.get("markers", [])
    
    if actual_markers != expected_markers:
        errmsg = f"Expected {expected_markers}, got {actual_markers}"
        raise AssertionError(errmsg)
    
    return


def test_pipeline_execute_short_circuit():
    """
        Test that middleware can short-circuit the pipeline.
    """
    pipeline = MiddlewarePipeline()
    
    mw_a = SimpleMiddleware("a", name="a")
    mw_short = ShortCircuitMiddleware(status_code=401, name="short")
    mw_c = SimpleMiddleware("c", name="c")
    
    pipeline.add(mw_a, name="a")
    pipeline.add(mw_short, name="short")
    pipeline.add(mw_c, name="c")
    
    request = Request("GET", "/test")
    request.path_params = {}
    
    handler_called = [False]
    
    def handler(req: Request) -> MockResponse:
        handler_called[0] = True
        return MockResponse(status_code=200)
    
    response = pipeline.execute(request, handler)
    
    # Handler should not be called
    if handler_called[0]:
        errmsg = "Expected handler NOT to be called due to short-circuit"
        raise AssertionError(errmsg)
    
    # Response should be from short-circuit middleware
    if response.status_code != 401:
        errmsg = f"Expected status 401, got {response.status_code}"
        raise AssertionError(errmsg)
    
    # Middleware after short-circuit should not be called
    if mw_c.before_called:
        errmsg = "Expected middleware after short-circuit NOT to be called"
        raise AssertionError(errmsg)
    
    return


def test_pipeline_execute_request_modification():
    """
        Test that middleware can modify the request.
    """
    pipeline = MiddlewarePipeline()
    
    mw = ModifyingMiddleware(request_header="modified_value", name="modifier")
    pipeline.add(mw, name="modifier")
    
    request = Request("GET", "/test")
    request.path_params = {}
    
    received_header = [None]
    
    def handler(req: Request) -> MockResponse:
        received_header[0] = req.path_params.get("added_header")
        return MockResponse(status_code=200)
    
    pipeline.execute(request, handler)
    
    if received_header[0] != "modified_value":
        errmsg = f"Expected 'modified_value', got '{received_header[0]}'"
        raise AssertionError(errmsg)
    
    return


def test_pipeline_execute_response_modification():
    """
        Test that middleware can modify the response.
    """
    pipeline = MiddlewarePipeline()
    
    mw = ModifyingMiddleware(response_header="added_value", name="modifier")
    pipeline.add(mw, name="modifier")
    
    request = Request("GET", "/test")
    
    def handler(req: Request) -> MockResponse:
        return MockResponse(status_code=200, body=b"OK")
    
    response = pipeline.execute(request, handler)
    
    if response.headers.get("X-Modified") != "added_value":
        errmsg = f"Expected 'added_value', got '{response.headers.get('X-Modified')}'"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for MiddlewarePipeline - Iteration
# =============================================================================

def test_pipeline_iteration():
    """
        Test that pipeline can be iterated.
    """
    pipeline = MiddlewarePipeline()
    
    mw_a = SimpleMiddleware("a", name="a")
    mw_b = SimpleMiddleware("b", name="b")
    
    pipeline.add(mw_a, name="a")
    pipeline.add(mw_b, name="b")
    
    entries = list(pipeline)
    
    if len(entries) != 2:
        errmsg = f"Expected 2 entries, got {len(entries)}"
        raise AssertionError(errmsg)
    
    if entries[0].name != "a":
        errmsg = f"Expected first entry name 'a', got '{entries[0].name}'"
        raise AssertionError(errmsg)
    
    if entries[1].name != "b":
        errmsg = f"Expected second entry name 'b', got '{entries[1].name}'"
        raise AssertionError(errmsg)
    
    return


def test_pipeline_get_names():
    """
        Test that get_names() returns middleware names in order.
    """
    pipeline = MiddlewarePipeline()
    
    pipeline.add(SimpleMiddleware("a", name="a"), name="a")
    pipeline.add(SimpleMiddleware("b"), name="b")  # Explicit name
    pipeline.add(SimpleMiddleware("c"))  # No name
    
    names = pipeline.get_names()
    
    if names != ["a", "b", None]:
        errmsg = f"Expected ['a', 'b', None], got {names}"
        raise AssertionError(errmsg)
    
    return


def test_pipeline_repr():
    """
        Test that __repr__ shows middleware names.
    """
    pipeline = MiddlewarePipeline()
    
    pipeline.add(SimpleMiddleware("a", name="a"), name="a")
    pipeline.add(SimpleMiddleware("b"), name="b")
    
    result = repr(pipeline)
    
    if "MiddlewarePipeline" not in result:
        errmsg = f"Expected 'MiddlewarePipeline' in repr, got '{result}'"
        raise AssertionError(errmsg)
    
    if "a" not in result or "b" not in result:
        errmsg = f"Expected middleware names in repr, got '{result}'"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for Protocol Compliance
# =============================================================================

def test_middleware_protocol_compliance():
    """
        Test that SimpleMiddleware complies with Middleware protocol.
    """
    mw = SimpleMiddleware("test", name="test_mw")
    
    # Check that it has the required attributes
    if not hasattr(mw, "name"):
        errmsg = "Expected middleware to have 'name' attribute"
        raise AssertionError(errmsg)
    
    if not callable(mw):
        errmsg = "Expected middleware to be callable"
        raise AssertionError(errmsg)
    
    return


def test_middleware_without_name_works():
    """
        Test that middleware without name attribute works.
    """
    def simple_func(request: Request, call_next: Callable) -> MockResponse:
        return call_next(request)
    
    pipeline = MiddlewarePipeline()
    pipeline.add(simple_func)
    
    request = Request("GET", "/test")
    
    def handler(req: Request) -> MockResponse:
        return MockResponse(status_code=200)
    
    response = pipeline.execute(request, handler)
    
    if response.status_code != 200:
        errmsg = f"Expected status 200, got {response.status_code}"
        raise AssertionError(errmsg)
    
    return



# =============================================================================
# Property Tests
# =============================================================================

import random
import string


def _random_string(length: int = 8) -> str:
    """Generate a random alphanumeric string."""
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))


def _random_middleware_name() -> str:
    """Generate a random middleware name."""
    return f"mw_{_random_string(6)}"


class OrderTrackingMiddleware:
    """
        Middleware that tracks execution order by appending markers.
    """
    
    def __init__(self, marker: str, name: str = None):
        self.marker = marker
        self.name = name
        return
    
    def __call__(self, request: Request, call_next: Callable) -> MockResponse:
        # Before: append marker
        if "order" not in request.path_params:
            request.path_params["order"] = []
        request.path_params["order"].append(f"{self.marker}_before")
        
        # Call next
        response = call_next(request)
        
        # After: append marker
        request.path_params["order"].append(f"{self.marker}_after")
        
        return response


class ShortCircuitAtPositionMiddleware:
    """
        Middleware that short-circuits at a specific position.
    """
    
    def __init__(self, marker: str, short_circuit: bool = False, name: str = None):
        self.marker = marker
        self.short_circuit = short_circuit
        self.name = name
        return
    
    def __call__(self, request: Request, call_next: Callable) -> MockResponse:
        # Before: append marker
        if "order" not in request.path_params:
            request.path_params["order"] = []
        request.path_params["order"].append(f"{self.marker}_before")
        
        if self.short_circuit:
            # Short-circuit: return without calling call_next
            return MockResponse(status_code=401, body=b"Short-circuited")
        
        # Call next
        response = call_next(request)
        
        # After: append marker
        request.path_params["order"].append(f"{self.marker}_after")
        
        return response


# -----------------------------------------------------------------------------
# Property 9: Middleware Pipeline Execution Order
# **Validates: Requirements 5.2, 5.3, 5.4, 6.8**
#
# *For any* middleware pipeline with N middleware components, execution SHALL
# proceed in order: MW1.before → MW2.before → ... → MWN.before → handler →
# MWN.after → ... → MW2.after → MW1.after. Each middleware SHALL receive the
# request (possibly modified by previous middleware) and return a response
# (possibly modified by subsequent middleware).
# -----------------------------------------------------------------------------

def test_property_middleware_execution_order():
    """
    Property 9: Middleware Pipeline Execution Order
    
    For any middleware pipeline with N middleware components, execution should
    proceed in order: MW1.before → MW2.before → ... → MWN.before → handler →
    MWN.after → ... → MW2.after → MW1.after.
    
    **Feature: router-request-handling, Property 9: Middleware Pipeline Execution Order**
    **Validates: Requirements 5.2, 5.3, 5.4, 6.8**
    """
    # Run 100 iterations
    for _ in range(100):
        pipeline = MiddlewarePipeline()
        
        # Generate random number of middleware (1-5)
        num_middleware = random.randint(1, 5)
        markers = [_random_string(4) for _ in range(num_middleware)]
        
        # Add middleware in order
        for i, marker in enumerate(markers):
            mw = OrderTrackingMiddleware(marker, name=f"mw_{i}")
            pipeline.add(mw, name=f"mw_{i}")
        
        # Create request
        request = Request("GET", "/test")
        request.path_params = {}
        
        # Create handler that adds its own marker
        def handler(req: Request) -> MockResponse:
            req.path_params["order"].append("handler")
            return MockResponse(status_code=200)
        
        # Execute pipeline
        pipeline.execute(request, handler)
        
        # Build expected order
        expected_order = []
        for marker in markers:
            expected_order.append(f"{marker}_before")
        expected_order.append("handler")
        for marker in reversed(markers):
            expected_order.append(f"{marker}_after")
        
        # Property: Execution order should match expected
        actual_order = request.path_params.get("order", [])
        
        if actual_order != expected_order:
            errmsg = f"Expected order {expected_order}, got {actual_order}"
            raise AssertionError(errmsg)
    
    return


def test_property_middleware_request_modification():
    """
    Property 9: Middleware Request Modification
    
    Each middleware should receive the request possibly modified by previous
    middleware.
    
    **Feature: router-request-handling, Property 9: Middleware Pipeline Execution Order**
    **Validates: Requirements 5.2, 5.3, 5.4, 6.8**
    """
    # Run 100 iterations
    for _ in range(100):
        pipeline = MiddlewarePipeline()
        
        # Generate random number of middleware (2-4)
        num_middleware = random.randint(2, 4)
        
        # Create middleware that adds cumulative values
        class CumulativeMiddleware:
            def __init__(self, value: int, name: str = None):
                self.value = value
                self.name = name
            
            def __call__(self, request: Request, call_next: Callable) -> MockResponse:
                # Add our value to the cumulative sum
                current = request.path_params.get("cumulative", 0)
                request.path_params["cumulative"] = current + self.value
                return call_next(request)
        
        # Add middleware with random values
        values = [random.randint(1, 100) for _ in range(num_middleware)]
        for i, value in enumerate(values):
            mw = CumulativeMiddleware(value, name=f"mw_{i}")
            pipeline.add(mw, name=f"mw_{i}")
        
        # Create request
        request = Request("GET", "/test")
        request.path_params = {}
        
        # Create handler that records the final cumulative value
        final_value = [None]
        
        def handler(req: Request) -> MockResponse:
            final_value[0] = req.path_params.get("cumulative", 0)
            return MockResponse(status_code=200)
        
        # Execute pipeline
        pipeline.execute(request, handler)
        
        # Property: Handler should see cumulative sum of all middleware values
        expected_sum = sum(values)
        
        if final_value[0] != expected_sum:
            errmsg = f"Expected cumulative value {expected_sum}, got {final_value[0]}"
            raise AssertionError(errmsg)
    
    return


# -----------------------------------------------------------------------------
# Property 10: Middleware Short-Circuit
# **Validates: Requirements 5.5**
#
# *For any* middleware that returns a response without calling `call_next`,
# subsequent middleware and the handler SHALL NOT be executed, and the returned
# response SHALL be passed back through preceding middleware.
# -----------------------------------------------------------------------------

def test_property_middleware_short_circuit():
    """
    Property 10: Middleware Short-Circuit
    
    For any middleware that returns a response without calling call_next,
    subsequent middleware and the handler should NOT be executed.
    
    **Feature: router-request-handling, Property 10: Middleware Short-Circuit**
    **Validates: Requirements 5.5**
    """
    # Run 100 iterations
    for _ in range(100):
        pipeline = MiddlewarePipeline()
        
        # Generate random number of middleware (3-6)
        num_middleware = random.randint(3, 6)
        
        # Pick a random position to short-circuit (not the last one)
        short_circuit_pos = random.randint(0, num_middleware - 2)
        
        markers = [_random_string(4) for _ in range(num_middleware)]
        
        # Add middleware, with one that short-circuits
        for i, marker in enumerate(markers):
            should_short_circuit = (i == short_circuit_pos)
            mw = ShortCircuitAtPositionMiddleware(
                marker,
                short_circuit=should_short_circuit,
                name=f"mw_{i}"
            )
            pipeline.add(mw, name=f"mw_{i}")
        
        # Create request
        request = Request("GET", "/test")
        request.path_params = {}
        
        # Create handler that adds its own marker
        handler_called = [False]
        
        def handler(req: Request) -> MockResponse:
            handler_called[0] = True
            req.path_params["order"].append("handler")
            return MockResponse(status_code=200)
        
        # Execute pipeline
        response = pipeline.execute(request, handler)
        
        # Property: Handler should NOT be called
        if handler_called[0]:
            errmsg = "Handler should NOT be called when middleware short-circuits"
            raise AssertionError(errmsg)
        
        # Property: Response should be from short-circuit middleware
        if response.status_code != 401:
            errmsg = f"Expected status 401 from short-circuit, got {response.status_code}"
            raise AssertionError(errmsg)
        
        # Property: Middleware after short-circuit should NOT be called
        actual_order = request.path_params.get("order", [])
        
        # Only middleware before and including short-circuit should have "before" markers
        for i, marker in enumerate(markers):
            before_marker = f"{marker}_before"
            if i <= short_circuit_pos:
                if before_marker not in actual_order:
                    errmsg = f"Expected {before_marker} to be called"
                    raise AssertionError(errmsg)
            else:
                if before_marker in actual_order:
                    errmsg = f"Expected {before_marker} NOT to be called after short-circuit"
                    raise AssertionError(errmsg)
        
        # Property: "after" markers should only be for middleware before short-circuit
        for i, marker in enumerate(markers):
            after_marker = f"{marker}_after"
            if i < short_circuit_pos:
                if after_marker not in actual_order:
                    errmsg = f"Expected {after_marker} to be called for preceding middleware"
                    raise AssertionError(errmsg)
            else:
                if after_marker in actual_order:
                    errmsg = f"Expected {after_marker} NOT to be called"
                    raise AssertionError(errmsg)
    
    return


# -----------------------------------------------------------------------------
# Property 11: Middleware Positioning
# **Validates: Requirements 6.3, 6.4, 6.5, 6.6**
#
# *For any* middleware added with position="start", it SHALL execute before all
# previously added middleware. *For any* middleware added with position="before:X",
# it SHALL execute immediately before middleware X. *For any* middleware added
# with position="after:X", it SHALL execute immediately after middleware X.
# -----------------------------------------------------------------------------

def test_property_middleware_positioning_start():
    """
    Property 11: Middleware Positioning - position="start"
    
    For any middleware added with position="start", it should execute before
    all previously added middleware.
    
    **Feature: router-request-handling, Property 11: Middleware Positioning**
    **Validates: Requirements 6.3, 6.4, 6.5, 6.6**
    """
    # Run 100 iterations
    for _ in range(100):
        pipeline = MiddlewarePipeline()
        
        # Generate random number of initial middleware (2-4)
        num_initial = random.randint(2, 4)
        initial_markers = [_random_string(4) for _ in range(num_initial)]
        
        # Add initial middleware
        for i, marker in enumerate(initial_markers):
            mw = OrderTrackingMiddleware(marker, name=f"initial_{i}")
            pipeline.add(mw, name=f"initial_{i}")
        
        # Add middleware at start
        start_marker = _random_string(4)
        start_mw = OrderTrackingMiddleware(start_marker, name="start_mw")
        pipeline.add(start_mw, name="start_mw", position="start")
        
        # Create request
        request = Request("GET", "/test")
        request.path_params = {}
        
        def handler(req: Request) -> MockResponse:
            req.path_params["order"].append("handler")
            return MockResponse(status_code=200)
        
        # Execute pipeline
        pipeline.execute(request, handler)
        
        # Property: Start middleware should execute first
        actual_order = request.path_params.get("order", [])
        
        if actual_order[0] != f"{start_marker}_before":
            errmsg = f"Expected start middleware to execute first, got {actual_order[0]}"
            raise AssertionError(errmsg)
        
        # Property: Start middleware "after" should execute last
        if actual_order[-1] != f"{start_marker}_after":
            errmsg = f"Expected start middleware 'after' to execute last, got {actual_order[-1]}"
            raise AssertionError(errmsg)
    
    return


def test_property_middleware_positioning_before():
    """
    Property 11: Middleware Positioning - position="before:<name>"
    
    For any middleware added with position="before:X", it should execute
    immediately before middleware X.
    
    **Feature: router-request-handling, Property 11: Middleware Positioning**
    **Validates: Requirements 6.3, 6.4, 6.5, 6.6**
    """
    # Run 100 iterations
    for _ in range(100):
        pipeline = MiddlewarePipeline()
        
        # Generate random number of middleware (3-5)
        num_middleware = random.randint(3, 5)
        markers = [_random_string(4) for _ in range(num_middleware)]
        names = [f"mw_{i}" for i in range(num_middleware)]
        
        # Add middleware
        for i, (marker, name) in enumerate(zip(markers, names)):
            mw = OrderTrackingMiddleware(marker, name=name)
            pipeline.add(mw, name=name)
        
        # Pick a random target (not the first one)
        target_idx = random.randint(1, num_middleware - 1)
        target_name = names[target_idx]
        
        # Add new middleware before target
        new_marker = _random_string(4)
        new_mw = OrderTrackingMiddleware(new_marker, name="new_mw")
        pipeline.add(new_mw, name="new_mw", position=f"before:{target_name}")
        
        # Create request
        request = Request("GET", "/test")
        request.path_params = {}
        
        def handler(req: Request) -> MockResponse:
            req.path_params["order"].append("handler")
            return MockResponse(status_code=200)
        
        # Execute pipeline
        pipeline.execute(request, handler)
        
        actual_order = request.path_params.get("order", [])
        
        # Find positions of new middleware and target middleware
        new_before_pos = actual_order.index(f"{new_marker}_before")
        target_before_pos = actual_order.index(f"{markers[target_idx]}_before")
        
        # Property: New middleware should execute immediately before target
        if new_before_pos != target_before_pos - 1:
            errmsg = f"Expected new middleware at position {target_before_pos - 1}, got {new_before_pos}"
            raise AssertionError(errmsg)
    
    return


def test_property_middleware_positioning_after():
    """
    Property 11: Middleware Positioning - position="after:<name>"
    
    For any middleware added with position="after:X", it should execute
    immediately after middleware X.
    
    **Feature: router-request-handling, Property 11: Middleware Positioning**
    **Validates: Requirements 6.3, 6.4, 6.5, 6.6**
    """
    # Run 100 iterations
    for _ in range(100):
        pipeline = MiddlewarePipeline()
        
        # Generate random number of middleware (3-5)
        num_middleware = random.randint(3, 5)
        markers = [_random_string(4) for _ in range(num_middleware)]
        names = [f"mw_{i}" for i in range(num_middleware)]
        
        # Add middleware
        for i, (marker, name) in enumerate(zip(markers, names)):
            mw = OrderTrackingMiddleware(marker, name=name)
            pipeline.add(mw, name=name)
        
        # Pick a random target (not the last one)
        target_idx = random.randint(0, num_middleware - 2)
        target_name = names[target_idx]
        
        # Add new middleware after target
        new_marker = _random_string(4)
        new_mw = OrderTrackingMiddleware(new_marker, name="new_mw")
        pipeline.add(new_mw, name="new_mw", position=f"after:{target_name}")
        
        # Create request
        request = Request("GET", "/test")
        request.path_params = {}
        
        def handler(req: Request) -> MockResponse:
            req.path_params["order"].append("handler")
            return MockResponse(status_code=200)
        
        # Execute pipeline
        pipeline.execute(request, handler)
        
        actual_order = request.path_params.get("order", [])
        
        # Find positions of new middleware and target middleware
        new_before_pos = actual_order.index(f"{new_marker}_before")
        target_before_pos = actual_order.index(f"{markers[target_idx]}_before")
        
        # Property: New middleware should execute immediately after target
        if new_before_pos != target_before_pos + 1:
            errmsg = f"Expected new middleware at position {target_before_pos + 1}, got {new_before_pos}"
            raise AssertionError(errmsg)
    
    return


def test_property_middleware_positioning_end():
    """
    Property 11: Middleware Positioning - position="end" (default)
    
    For any middleware added with position="end", it should execute after
    all previously added middleware.
    
    **Feature: router-request-handling, Property 11: Middleware Positioning**
    **Validates: Requirements 6.3, 6.4, 6.5, 6.6**
    """
    # Run 100 iterations
    for _ in range(100):
        pipeline = MiddlewarePipeline()
        
        # Generate random number of initial middleware (2-4)
        num_initial = random.randint(2, 4)
        initial_markers = [_random_string(4) for _ in range(num_initial)]
        
        # Add initial middleware
        for i, marker in enumerate(initial_markers):
            mw = OrderTrackingMiddleware(marker, name=f"initial_{i}")
            pipeline.add(mw, name=f"initial_{i}")
        
        # Add middleware at end (default position)
        end_marker = _random_string(4)
        end_mw = OrderTrackingMiddleware(end_marker, name="end_mw")
        pipeline.add(end_mw, name="end_mw", position="end")
        
        # Create request
        request = Request("GET", "/test")
        request.path_params = {}
        
        def handler(req: Request) -> MockResponse:
            req.path_params["order"].append("handler")
            return MockResponse(status_code=200)
        
        # Execute pipeline
        pipeline.execute(request, handler)
        
        actual_order = request.path_params.get("order", [])
        
        # Find position of end middleware "before" marker
        end_before_pos = actual_order.index(f"{end_marker}_before")
        
        # Property: End middleware should execute last (just before handler)
        # The handler is at position num_initial + 1 (0-indexed)
        expected_pos = num_initial
        
        if end_before_pos != expected_pos:
            errmsg = f"Expected end middleware at position {expected_pos}, got {end_before_pos}"
            raise AssertionError(errmsg)
    
    return
