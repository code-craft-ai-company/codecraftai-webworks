"""
    Tests for the :class:`RequestInspector` and :class:`RequestInfo` classes.

    This module tests request capturing, body size limiting and truncation,
    JSON and form data parsing, path pattern filtering, the debug endpoint,
    and the property-based test for request inspector size limits.
"""

import json
import random
import string

from datetime import datetime

from automojo.webworks.devexp.debug.inspector import (
    RequestInfo,
    RequestInspector,
)


# =============================================================================
# Helpers
# =============================================================================

def _make_request(
    method: str = "GET",
    path: str = "/",
    query_params: dict = None,
    headers: dict = None,
    body: bytes = None,
) -> dict:
    """
        Create a mock request dictionary.

        :param method: The HTTP method.
        :param path: The request path.
        :param query_params: Optional query parameters dictionary.
        :param headers: Optional headers dictionary.
        :param body: Optional body bytes.

        :returns: A request dictionary.
    """
    request = {
        "method": method,
        "path": path,
        "query_params": query_params if query_params is not None else {},
        "headers": headers if headers is not None else {},
        "body": body,
    }

    return request


# =============================================================================
# RequestInfo Tests
# =============================================================================

def test_request_info_construction():
    """
        Test that RequestInfo stores all provided attributes correctly.
    """
    now = datetime.now()
    info = RequestInfo(
        timestamp=now,
        method="POST",
        path="/api/users",
        query_params={"page": "1"},
        headers={"Content-Type": "application/json"},
        body=b'{"name": "test"}',
        body_truncated=False,
        parsed_body={"name": "test"},
    )

    if info.timestamp != now:
        errmsg = "Expected timestamp {}, got {}".format(now, info.timestamp)
        raise AssertionError(errmsg)

    if info.method != "POST":
        errmsg = "Expected method 'POST', got '{}'".format(info.method)
        raise AssertionError(errmsg)

    if info.path != "/api/users":
        errmsg = "Expected path '/api/users', got '{}'".format(info.path)
        raise AssertionError(errmsg)

    if info.query_params != {"page": "1"}:
        errmsg = "Expected query_params {{'page': '1'}}, got {}".format(info.query_params)
        raise AssertionError(errmsg)

    if info.headers != {"Content-Type": "application/json"}:
        errmsg = "Expected Content-Type header, got {}".format(info.headers)
        raise AssertionError(errmsg)

    if info.body != b'{"name": "test"}':
        errmsg = "Expected body bytes, got {}".format(info.body)
        raise AssertionError(errmsg)

    if info.body_truncated is not False:
        errmsg = "Expected body_truncated=False, got {}".format(info.body_truncated)
        raise AssertionError(errmsg)

    if info.parsed_body != {"name": "test"}:
        errmsg = "Expected parsed_body dict, got {}".format(info.parsed_body)
        raise AssertionError(errmsg)

    return


def test_request_info_defaults():
    """
        Test that RequestInfo uses sensible defaults for optional parameters.
    """
    now = datetime.now()
    info = RequestInfo(
        timestamp=now,
        method="GET",
        path="/",
    )

    if len(info.query_params) != 0:
        errmsg = "Expected empty query_params, got {}".format(info.query_params)
        raise AssertionError(errmsg)

    if len(info.headers) != 0:
        errmsg = "Expected empty headers, got {}".format(info.headers)
        raise AssertionError(errmsg)

    if info.body is not None:
        errmsg = "Expected body=None, got {}".format(info.body)
        raise AssertionError(errmsg)

    if info.body_truncated is not False:
        errmsg = "Expected body_truncated=False, got {}".format(info.body_truncated)
        raise AssertionError(errmsg)

    if info.parsed_body is not None:
        errmsg = "Expected parsed_body=None, got {}".format(info.parsed_body)
        raise AssertionError(errmsg)

    return


def test_request_info_to_dict():
    """
        Test that to_dict produces a serializable dictionary.
    """
    now = datetime.now()
    info = RequestInfo(
        timestamp=now,
        method="GET",
        path="/test",
        query_params={"q": "search"},
        headers={"Accept": "text/html"},
        body=b"hello",
        body_truncated=False,
        parsed_body=None,
    )

    result = info.to_dict()

    if result["method"] != "GET":
        errmsg = "Expected method 'GET' in dict, got '{}'".format(result["method"])
        raise AssertionError(errmsg)

    if result["path"] != "/test":
        errmsg = "Expected path '/test' in dict, got '{}'".format(result["path"])
        raise AssertionError(errmsg)

    if result["body"] != "hello":
        errmsg = "Expected body 'hello' in dict, got '{}'".format(result["body"])
        raise AssertionError(errmsg)

    if result["body_truncated"] is not False:
        errmsg = "Expected body_truncated=False in dict"
        raise AssertionError(errmsg)

    if result["timestamp"] != now.isoformat():
        errmsg = "Expected ISO timestamp in dict"
        raise AssertionError(errmsg)

    return


def test_request_info_to_dict_binary_body():
    """
        Test that to_dict handles non-UTF-8 binary body data.
    """
    now = datetime.now()
    binary_body = bytes(range(128, 256))
    info = RequestInfo(
        timestamp=now,
        method="POST",
        path="/upload",
        body=binary_body,
        body_truncated=False,
    )

    result = info.to_dict()

    if "binary data" not in result["body"]:
        errmsg = "Expected binary data indicator in dict body, got '{}'".format(result["body"])
        raise AssertionError(errmsg)

    return


def test_request_info_to_dict_none_body():
    """
        Test that to_dict handles None body correctly.
    """
    now = datetime.now()
    info = RequestInfo(
        timestamp=now,
        method="GET",
        path="/",
    )

    result = info.to_dict()

    if result["body"] is not None:
        errmsg = "Expected body=None in dict, got {}".format(result["body"])
        raise AssertionError(errmsg)

    return


# =============================================================================
# RequestInspector Construction Tests
# =============================================================================

def test_inspector_default_construction():
    """
        Test that RequestInspector uses sensible defaults.
    """
    inspector = RequestInspector()

    if inspector.max_requests != 100:
        errmsg = "Expected max_requests=100, got {}".format(inspector.max_requests)
        raise AssertionError(errmsg)

    if inspector.max_body_size != 10240:
        errmsg = "Expected max_body_size=10240, got {}".format(inspector.max_body_size)
        raise AssertionError(errmsg)

    if inspector.path_filter is not None:
        errmsg = "Expected path_filter=None, got {}".format(inspector.path_filter)
        raise AssertionError(errmsg)

    return


def test_inspector_custom_construction():
    """
        Test that RequestInspector accepts custom configuration.
    """
    inspector = RequestInspector(
        max_requests=50,
        max_body_size=2048,
        path_filter="/api/.*",
    )

    if inspector.max_requests != 50:
        errmsg = "Expected max_requests=50, got {}".format(inspector.max_requests)
        raise AssertionError(errmsg)

    if inspector.max_body_size != 2048:
        errmsg = "Expected max_body_size=2048, got {}".format(inspector.max_body_size)
        raise AssertionError(errmsg)

    if inspector.path_filter != "/api/.*":
        errmsg = "Expected path_filter='/api/.*', got '{}'".format(inspector.path_filter)
        raise AssertionError(errmsg)

    return


# =============================================================================
# Capture Tests
# =============================================================================

def test_capture_basic_request():
    """
        Test that a basic request is captured with correct attributes.
    """
    inspector = RequestInspector()
    request = _make_request(
        method="GET",
        path="/api/users",
        query_params={"page": "1"},
        headers={"Accept": "application/json"},
    )

    inspector.capture(request)

    captured = inspector.get_requests()

    if len(captured) != 1:
        errmsg = "Expected 1 captured request, got {}".format(len(captured))
        raise AssertionError(errmsg)

    info = captured[0]

    if info.method != "GET":
        errmsg = "Expected method 'GET', got '{}'".format(info.method)
        raise AssertionError(errmsg)

    if info.path != "/api/users":
        errmsg = "Expected path '/api/users', got '{}'".format(info.path)
        raise AssertionError(errmsg)

    if info.query_params != {"page": "1"}:
        errmsg = "Expected query_params, got {}".format(info.query_params)
        raise AssertionError(errmsg)

    return


def test_capture_request_with_body():
    """
        Test that a request with body is captured correctly.
    """
    inspector = RequestInspector()
    body_data = b'{"name": "test"}'
    request = _make_request(
        method="POST",
        path="/api/users",
        headers={"Content-Type": "application/json"},
        body=body_data,
    )

    inspector.capture(request)

    captured = inspector.get_requests()
    info = captured[0]

    if info.body != body_data:
        errmsg = "Expected body bytes to match"
        raise AssertionError(errmsg)

    if info.body_truncated is not False:
        errmsg = "Expected body_truncated=False"
        raise AssertionError(errmsg)

    return


def test_capture_request_with_string_body():
    """
        Test that a string body is converted to bytes.
    """
    inspector = RequestInspector()
    request = _make_request(
        method="POST",
        path="/api/data",
        body=b"plain text body",
    )

    inspector.capture(request)

    captured = inspector.get_requests()
    info = captured[0]

    if info.body is None:
        errmsg = "Expected body to be captured"
        raise AssertionError(errmsg)

    return


def test_capture_multiple_requests():
    """
        Test that multiple requests are captured in order.
    """
    inspector = RequestInspector()

    for idx in range(5):
        request = _make_request(
            method="GET",
            path="/api/item/{}".format(idx),
        )
        inspector.capture(request)

    captured = inspector.get_requests()

    if len(captured) != 5:
        errmsg = "Expected 5 captured requests, got {}".format(len(captured))
        raise AssertionError(errmsg)

    for idx in range(5):
        expected_path = "/api/item/{}".format(idx)
        if captured[idx].path != expected_path:
            errmsg = "Expected path '{}', got '{}'".format(expected_path, captured[idx].path)
            raise AssertionError(errmsg)

    return


# =============================================================================
# Body Size Limiting Tests
# =============================================================================

def test_body_truncation_when_exceeding_limit():
    """
        Test that bodies exceeding max_body_size are truncated.
    """
    max_size = 64
    inspector = RequestInspector(max_body_size=max_size)

    large_body = b"x" * 200
    request = _make_request(
        method="POST",
        path="/upload",
        body=large_body,
    )

    inspector.capture(request)

    captured = inspector.get_requests()
    info = captured[0]

    if info.body_truncated is not True:
        errmsg = "Expected body_truncated=True for oversized body"
        raise AssertionError(errmsg)

    if len(info.body) != max_size:
        errmsg = "Expected body length {}, got {}".format(max_size, len(info.body))
        raise AssertionError(errmsg)

    return


def test_body_not_truncated_when_within_limit():
    """
        Test that bodies within max_body_size are not truncated.
    """
    inspector = RequestInspector(max_body_size=1024)

    small_body = b"small"
    request = _make_request(
        method="POST",
        path="/data",
        body=small_body,
    )

    inspector.capture(request)

    captured = inspector.get_requests()
    info = captured[0]

    if info.body_truncated is not False:
        errmsg = "Expected body_truncated=False for small body"
        raise AssertionError(errmsg)

    if info.body != small_body:
        errmsg = "Expected body to be unchanged"
        raise AssertionError(errmsg)

    return


def test_body_exactly_at_limit():
    """
        Test that a body exactly at max_body_size is not truncated.
    """
    max_size = 100
    inspector = RequestInspector(max_body_size=max_size)

    exact_body = b"a" * max_size
    request = _make_request(
        method="POST",
        path="/exact",
        body=exact_body,
    )

    inspector.capture(request)

    captured = inspector.get_requests()
    info = captured[0]

    if info.body_truncated is not False:
        errmsg = "Expected body_truncated=False for body at exact limit"
        raise AssertionError(errmsg)

    if len(info.body) != max_size:
        errmsg = "Expected body length {}, got {}".format(max_size, len(info.body))
        raise AssertionError(errmsg)

    return


def test_none_body_not_truncated():
    """
        Test that None body is handled without truncation.
    """
    inspector = RequestInspector()
    request = _make_request(method="GET", path="/")

    inspector.capture(request)

    captured = inspector.get_requests()
    info = captured[0]

    if info.body is not None:
        errmsg = "Expected body=None, got {}".format(info.body)
        raise AssertionError(errmsg)

    if info.body_truncated is not False:
        errmsg = "Expected body_truncated=False for None body"
        raise AssertionError(errmsg)

    return


# =============================================================================
# JSON/Form Data Parsing Tests
# =============================================================================

def test_parse_json_body():
    """
        Test that JSON bodies are parsed when Content-Type is application/json.
    """
    inspector = RequestInspector()
    json_data = {"key": "value", "count": 42}
    body = json.dumps(json_data).encode("utf-8")
    request = _make_request(
        method="POST",
        path="/api/data",
        headers={"Content-Type": "application/json"},
        body=body,
    )

    inspector.capture(request)

    captured = inspector.get_requests()
    info = captured[0]

    if info.parsed_body is None:
        errmsg = "Expected parsed JSON body, got None"
        raise AssertionError(errmsg)

    if info.parsed_body["key"] != "value":
        errmsg = "Expected parsed_body['key']='value', got '{}'".format(info.parsed_body["key"])
        raise AssertionError(errmsg)

    if info.parsed_body["count"] != 42:
        errmsg = "Expected parsed_body['count']=42, got {}".format(info.parsed_body["count"])
        raise AssertionError(errmsg)

    return


def test_parse_form_data_body():
    """
        Test that form data bodies are parsed when Content-Type is
        application/x-www-form-urlencoded.
    """
    inspector = RequestInspector()
    body = b"name=test&value=123"
    request = _make_request(
        method="POST",
        path="/form",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        body=body,
    )

    inspector.capture(request)

    captured = inspector.get_requests()
    info = captured[0]

    if info.parsed_body is None:
        errmsg = "Expected parsed form body, got None"
        raise AssertionError(errmsg)

    if "name" not in info.parsed_body:
        errmsg = "Expected 'name' key in parsed form data"
        raise AssertionError(errmsg)

    if info.parsed_body["name"] != ["test"]:
        errmsg = "Expected parsed name=['test'], got {}".format(info.parsed_body["name"])
        raise AssertionError(errmsg)

    return


def test_no_parsing_without_content_type():
    """
        Test that body is not parsed when no Content-Type header is present.
    """
    inspector = RequestInspector()
    body = b'{"key": "value"}'
    request = _make_request(
        method="POST",
        path="/data",
        body=body,
    )

    inspector.capture(request)

    captured = inspector.get_requests()
    info = captured[0]

    if info.parsed_body is not None:
        errmsg = "Expected parsed_body=None without Content-Type, got {}".format(info.parsed_body)
        raise AssertionError(errmsg)

    return


def test_invalid_json_body_returns_none():
    """
        Test that invalid JSON body results in parsed_body=None.
    """
    inspector = RequestInspector()
    body = b"not valid json {"
    request = _make_request(
        method="POST",
        path="/data",
        headers={"Content-Type": "application/json"},
        body=body,
    )

    inspector.capture(request)

    captured = inspector.get_requests()
    info = captured[0]

    if info.parsed_body is not None:
        errmsg = "Expected parsed_body=None for invalid JSON, got {}".format(info.parsed_body)
        raise AssertionError(errmsg)

    return


# =============================================================================
# Path Pattern Filtering Tests
# =============================================================================

def test_path_filter_captures_matching_requests():
    """
        Test that only requests matching the path filter are captured.
    """
    inspector = RequestInspector(path_filter="/api/.*")

    inspector.capture(_make_request(method="GET", path="/api/users"))
    inspector.capture(_make_request(method="GET", path="/static/style.css"))
    inspector.capture(_make_request(method="GET", path="/api/items"))

    captured = inspector.get_requests()

    if len(captured) != 2:
        errmsg = "Expected 2 captured requests with /api/ filter, got {}".format(len(captured))
        raise AssertionError(errmsg)

    if captured[0].path != "/api/users":
        errmsg = "Expected first captured path '/api/users', got '{}'".format(captured[0].path)
        raise AssertionError(errmsg)

    if captured[1].path != "/api/items":
        errmsg = "Expected second captured path '/api/items', got '{}'".format(captured[1].path)
        raise AssertionError(errmsg)

    return


def test_path_filter_excludes_non_matching():
    """
        Test that requests not matching the path filter are excluded.
    """
    inspector = RequestInspector(path_filter="^/admin")

    inspector.capture(_make_request(method="GET", path="/api/users"))
    inspector.capture(_make_request(method="GET", path="/home"))

    captured = inspector.get_requests()

    if len(captured) != 0:
        errmsg = "Expected 0 captured requests, got {}".format(len(captured))
        raise AssertionError(errmsg)

    return


def test_no_path_filter_captures_all():
    """
        Test that all requests are captured when no path filter is set.
    """
    inspector = RequestInspector()

    inspector.capture(_make_request(method="GET", path="/a"))
    inspector.capture(_make_request(method="GET", path="/b"))
    inspector.capture(_make_request(method="GET", path="/c"))

    captured = inspector.get_requests()

    if len(captured) != 3:
        errmsg = "Expected 3 captured requests, got {}".format(len(captured))
        raise AssertionError(errmsg)

    return


def test_get_requests_with_path_filter():
    """
        Test that get_requests supports path_filter parameter.
    """
    inspector = RequestInspector()

    inspector.capture(_make_request(method="GET", path="/api/users"))
    inspector.capture(_make_request(method="GET", path="/static/file.js"))
    inspector.capture(_make_request(method="POST", path="/api/items"))

    filtered = inspector.get_requests(path_filter="/api/.*")

    if len(filtered) != 2:
        errmsg = "Expected 2 filtered requests, got {}".format(len(filtered))
        raise AssertionError(errmsg)

    return


def test_get_requests_with_limit():
    """
        Test that get_requests supports limit parameter.
    """
    inspector = RequestInspector()

    for idx in range(10):
        inspector.capture(_make_request(method="GET", path="/item/{}".format(idx)))

    limited = inspector.get_requests(limit=3)

    if len(limited) != 3:
        errmsg = "Expected 3 limited requests, got {}".format(len(limited))
        raise AssertionError(errmsg)

    # Should return the most recent 3
    if limited[0].path != "/item/7":
        errmsg = "Expected most recent requests, got path '{}'".format(limited[0].path)
        raise AssertionError(errmsg)

    return


# =============================================================================
# Max Requests Limit Tests
# =============================================================================

def test_max_requests_limit_enforced():
    """
        Test that the inspector enforces the max_requests limit.
    """
    inspector = RequestInspector(max_requests=5)

    for idx in range(10):
        inspector.capture(_make_request(method="GET", path="/item/{}".format(idx)))

    captured = inspector.get_requests()

    if len(captured) != 5:
        errmsg = "Expected 5 captured requests (max), got {}".format(len(captured))
        raise AssertionError(errmsg)

    # Should keep the most recent 5 (indices 5-9)
    if captured[0].path != "/item/5":
        errmsg = "Expected oldest kept request at /item/5, got '{}'".format(captured[0].path)
        raise AssertionError(errmsg)

    return


# =============================================================================
# Clear Tests
# =============================================================================

def test_clear_removes_all_requests():
    """
        Test that clear removes all captured requests.
    """
    inspector = RequestInspector()

    for idx in range(5):
        inspector.capture(_make_request(method="GET", path="/item/{}".format(idx)))

    inspector.clear()

    captured = inspector.get_requests()

    if len(captured) != 0:
        errmsg = "Expected 0 requests after clear, got {}".format(len(captured))
        raise AssertionError(errmsg)

    return


# =============================================================================
# Debug Endpoint Tests
# =============================================================================

def test_debug_endpoint_returns_json_response():
    """
        Test that the debug endpoint returns a valid JSON response.
    """
    inspector = RequestInspector()

    inspector.capture(_make_request(method="GET", path="/api/test"))
    inspector.capture(_make_request(method="POST", path="/api/data"))

    response = inspector.handle_debug_endpoint()

    if response["status_code"] != 200:
        errmsg = "Expected status 200, got {}".format(response["status_code"])
        raise AssertionError(errmsg)

    content_type = response["headers"].get("Content-Type", "")
    if "application/json" not in content_type:
        errmsg = "Expected JSON content type, got '{}'".format(content_type)
        raise AssertionError(errmsg)

    body = json.loads(response["body"])

    if body["total"] != 2:
        errmsg = "Expected total=2, got {}".format(body["total"])
        raise AssertionError(errmsg)

    if body["returned"] != 2:
        errmsg = "Expected returned=2, got {}".format(body["returned"])
        raise AssertionError(errmsg)

    if len(body["requests"]) != 2:
        errmsg = "Expected 2 requests in body, got {}".format(len(body["requests"]))
        raise AssertionError(errmsg)

    return


def test_debug_endpoint_with_limit():
    """
        Test that the debug endpoint respects the limit parameter.
    """
    inspector = RequestInspector()

    for idx in range(10):
        inspector.capture(_make_request(method="GET", path="/item/{}".format(idx)))

    response = inspector.handle_debug_endpoint(limit=3)
    body = json.loads(response["body"])

    if body["total"] != 10:
        errmsg = "Expected total=10, got {}".format(body["total"])
        raise AssertionError(errmsg)

    if body["returned"] != 3:
        errmsg = "Expected returned=3, got {}".format(body["returned"])
        raise AssertionError(errmsg)

    return


def test_debug_endpoint_with_path_filter():
    """
        Test that the debug endpoint respects the path_filter parameter.
    """
    inspector = RequestInspector()

    inspector.capture(_make_request(method="GET", path="/api/users"))
    inspector.capture(_make_request(method="GET", path="/static/file.js"))
    inspector.capture(_make_request(method="POST", path="/api/items"))

    response = inspector.handle_debug_endpoint(path_filter="/api/.*")
    body = json.loads(response["body"])

    if body["returned"] != 2:
        errmsg = "Expected returned=2 with path filter, got {}".format(body["returned"])
        raise AssertionError(errmsg)

    return


def test_debug_endpoint_stores_recent_requests():
    """
        Test that the debug endpoint provides access to stored recent
        requests in memory for review.
    """
    inspector = RequestInspector(max_requests=5)

    for idx in range(8):
        inspector.capture(_make_request(method="GET", path="/req/{}".format(idx)))

    response = inspector.handle_debug_endpoint()
    body = json.loads(response["body"])

    if body["total"] != 5:
        errmsg = "Expected total=5 (max_requests), got {}".format(body["total"])
        raise AssertionError(errmsg)

    # Verify the stored requests are the most recent ones
    first_path = body["requests"][0]["path"]
    if first_path != "/req/3":
        errmsg = "Expected oldest stored request at /req/3, got '{}'".format(first_path)
        raise AssertionError(errmsg)

    return


# =============================================================================
# Property 6: Request Inspector Size Limits
# =============================================================================

_PROPERTY_ITERATIONS = 100


def _random_bytes(min_len: int = 0, max_len: int = 50000) -> bytes:
    """
        Generate random bytes of a random length.

        :param min_len: Minimum byte length.
        :param max_len: Maximum byte length.

        :returns: Random bytes.
    """
    length = random.randint(min_len, max_len)
    data = bytes(random.getrandbits(8) for _ in range(length))

    return data


def _random_max_body_size() -> int:
    """
        Generate a random max_body_size value.

        :returns: A positive integer for max body size.
    """
    size = random.randint(1, 20000)

    return size


def test_property_6_request_inspector_size_limits():
    """
        Property 6: Request Inspector Size Limits

        For any captured request with body size exceeding max_body_size,
        the RequestInfo SHALL have body_truncated=True and body containing
        at most max_body_size bytes.

        This test generates random body sizes and max_body_size values
        across 100 iterations and verifies the truncation invariant.

        **Feature: developer-experience, Property 6: Request Inspector Size Limits**
        **Validates: Requirements 11.4**
    """
    for iteration in range(_PROPERTY_ITERATIONS):
        max_body_size = _random_max_body_size()
        inspector = RequestInspector(max_body_size=max_body_size)

        body = _random_bytes(min_len=0, max_len=max_body_size * 3)
        body_len = len(body)

        request = _make_request(
            method=random.choice(["GET", "POST", "PUT", "PATCH", "DELETE"]),
            path="/test/{}".format(iteration),
            body=body if body_len > 0 else None,
        )

        inspector.capture(request)

        captured = inspector.get_requests()

        if len(captured) != 1:
            errmsg = "Iteration {}: Expected 1 captured request, got {}".format(
                iteration, len(captured),
            )
            raise AssertionError(errmsg)

        info = captured[0]

        if body_len > max_body_size:
            # Body exceeds limit: must be truncated
            if info.body_truncated is not True:
                errmsg = (
                    "Iteration {}: body size {} exceeds max_body_size {}, "
                    "but body_truncated is False"
                ).format(iteration, body_len, max_body_size)
                raise AssertionError(errmsg)

            if info.body is None:
                errmsg = (
                    "Iteration {}: body_truncated=True but body is None"
                ).format(iteration)
                raise AssertionError(errmsg)

            actual_body_len = len(info.body)
            if actual_body_len > max_body_size:
                errmsg = (
                    "Iteration {}: truncated body length {} exceeds "
                    "max_body_size {}"
                ).format(iteration, actual_body_len, max_body_size)
                raise AssertionError(errmsg)

            if actual_body_len != max_body_size:
                errmsg = (
                    "Iteration {}: truncated body length {} does not equal "
                    "max_body_size {}"
                ).format(iteration, actual_body_len, max_body_size)
                raise AssertionError(errmsg)
        elif body_len == 0 and body is None:
            # No body: should not be truncated
            if info.body_truncated is not False:
                errmsg = (
                    "Iteration {}: None body should not be truncated"
                ).format(iteration)
                raise AssertionError(errmsg)
        else:
            # Body within limit: should not be truncated
            if info.body_truncated is not False:
                errmsg = (
                    "Iteration {}: body size {} within max_body_size {}, "
                    "but body_truncated is True"
                ).format(iteration, body_len, max_body_size)
                raise AssertionError(errmsg)

            if info.body is not None:
                actual_body_len = len(info.body)
                if actual_body_len != body_len:
                    errmsg = (
                        "Iteration {}: non-truncated body length {} does not "
                        "match original length {}"
                    ).format(iteration, actual_body_len, body_len)
                    raise AssertionError(errmsg)

    return
