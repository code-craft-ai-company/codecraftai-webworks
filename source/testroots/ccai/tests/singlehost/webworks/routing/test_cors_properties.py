"""
.. module:: test_cors_properties
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Property-based tests for CORSMiddleware.

.. moduleauthor:: Code Craft AI LLC

This module contains property-based tests for the CORSMiddleware,
validating Property 11 (CORS preflight returns 204 without calling handler)
and Property 12 (CORS headers present if and only if origin is allowed).
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []

from typing import Callable, Dict, List

import ccai.testbase as testbase

from ccai.testbase.properties import given
from ccai.testbase.properties import strategies as st

from ccai.webworks.routing.middleware.cors import CORSMiddleware
from ccai.webworks.routing.request import Request
from ccai.webworks.routing.response import Response


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
        self._headers = headers if headers is not None else {}
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

    def set_header(self, name: str, value: str) -> None:
        self._headers[name] = value
        return


# Pre-defined origin pools for sampling
ALLOWED_ORIGINS = [
    "http://alpha.example.com",
    "http://bravo.example.com",
    "http://charlie.example.com",
    "http://delta.example.com",
    "http://echo.example.com",
]

DISALLOWED_ORIGINS = [
    "http://xray.blocked.net",
    "http://yankee.blocked.net",
    "http://zulu.blocked.net",
    "http://foxtrot.blocked.net",
    "http://golf.blocked.net",
]


# =============================================================================
# Property 11: CORS preflight returns 204 without calling handler
# =============================================================================

@given(
    origin=st.sampled_from(ALLOWED_ORIGINS),
    num_allowed=st.integers(1, 5),
    constraints={"max_examples": 20}
)
def test_cors_preflight_returns_204_without_calling_handler(origin, num_allowed):
    """
        For any OPTIONS request with an Origin header matching an allowed origin,
        the CORS middleware should return a 204 response with CORS headers,
        without invoking call_next.
    """
    # Build allowed list that always includes the chosen origin
    allowed = ALLOWED_ORIGINS[:num_allowed]
    if origin not in allowed:
        allowed = allowed + [origin]

    cors = CORSMiddleware(allowed_origins=allowed)

    request = Request(
        method="OPTIONS",
        path="/test",
        headers={"Origin": origin}
    )

    handler_called = [False]

    def handler(req: Request) -> MockResponse:
        handler_called[0] = True
        return MockResponse(status_code=200, body=b"handler")

    response = cors(request, handler)

    testbase.assert_false(handler_called[0],
        f"Handler should not be called for preflight request from origin={origin}.")

    testbase.assert_equal(response.status_code, 204,
        f"Preflight response should have status 204, got {response.status_code}.")

    testbase.assert_true("Access-Control-Allow-Origin" in response.headers,
        "Preflight response should contain Access-Control-Allow-Origin header.")

    testbase.assert_true("Access-Control-Allow-Methods" in response.headers,
        "Preflight response should contain Access-Control-Allow-Methods header.")

    testbase.assert_true("Access-Control-Max-Age" in response.headers,
        "Preflight response should contain Access-Control-Max-Age header.")


@given(
    max_age=st.integers(0, 86400),
    constraints={"max_examples": 15}
)
def test_cors_preflight_wildcard_returns_204(max_age):
    """
        For any OPTIONS request when allowed_origins contains '*',
        the CORS middleware should return a 204 response without calling handler.
    """
    cors = CORSMiddleware(allowed_origins=["*"], max_age=max_age)

    request = Request(
        method="OPTIONS",
        path="/anything",
        headers={"Origin": "http://any-origin.example.com"}
    )

    handler_called = [False]

    def handler(req: Request) -> MockResponse:
        handler_called[0] = True
        return MockResponse(status_code=200)

    response = cors(request, handler)

    testbase.assert_false(handler_called[0],
        "Handler should not be called for wildcard preflight.")

    testbase.assert_equal(response.status_code, 204,
        f"Wildcard preflight should return 204, got {response.status_code}.")

    testbase.assert_equal(response.headers.get("Access-Control-Max-Age"), str(max_age),
        f"Max-Age header should be {max_age}.")


# =============================================================================
# Property 12: CORS headers present if and only if origin is allowed
# =============================================================================

@given(
    origin=st.sampled_from(ALLOWED_ORIGINS),
    num_allowed=st.integers(1, 5),
    constraints={"max_examples": 20}
)
def test_cors_headers_present_when_origin_allowed(origin, num_allowed):
    """
        For any non-OPTIONS request from an allowed origin, the response
        should contain Access-Control-Allow-Origin header.
    """
    allowed = ALLOWED_ORIGINS[:num_allowed]
    if origin not in allowed:
        allowed = allowed + [origin]

    cors = CORSMiddleware(allowed_origins=allowed)

    request = Request(
        method="GET",
        path="/resource",
        headers={"Origin": origin}
    )

    def handler(req: Request) -> MockResponse:
        return MockResponse(status_code=200, body=b"ok")

    response = cors(request, handler)

    testbase.assert_true("Access-Control-Allow-Origin" in response.headers,
        f"Response should contain Access-Control-Allow-Origin for allowed origin={origin}.")


@given(
    disallowed=st.sampled_from(DISALLOWED_ORIGINS),
    num_allowed=st.integers(1, 5),
    constraints={"max_examples": 20}
)
def test_cors_headers_absent_when_origin_disallowed(disallowed, num_allowed):
    """
        For any non-OPTIONS request from a disallowed origin, the response
        should NOT contain Access-Control-Allow-Origin header.
    """
    allowed = ALLOWED_ORIGINS[:num_allowed]

    cors = CORSMiddleware(allowed_origins=allowed)

    request = Request(
        method="GET",
        path="/resource",
        headers={"Origin": disallowed}
    )

    def handler(req: Request) -> MockResponse:
        return MockResponse(status_code=200, body=b"ok")

    response = cors(request, handler)

    has_cors_header = "Access-Control-Allow-Origin" in response.headers

    testbase.assert_false(has_cors_header,
        f"Response should NOT contain Access-Control-Allow-Origin for disallowed origin={disallowed}, "
        f"allowed={allowed}.")


@given(
    origin=st.sampled_from(DISALLOWED_ORIGINS + ALLOWED_ORIGINS),
    constraints={"max_examples": 15}
)
def test_cors_wildcard_allows_any_origin(origin):
    """
        When allowed_origins contains '*', any origin should receive CORS headers.
    """
    cors = CORSMiddleware(allowed_origins=["*"])

    request = Request(
        method="GET",
        path="/resource",
        headers={"Origin": origin}
    )

    def handler(req: Request) -> MockResponse:
        return MockResponse(status_code=200, body=b"ok")

    response = cors(request, handler)

    testbase.assert_true("Access-Control-Allow-Origin" in response.headers,
        f"Wildcard should allow any origin, but CORS header missing for origin={origin}.")


@given(
    num_allowed=st.integers(1, 5),
    constraints={"max_examples": 10}
)
def test_cors_no_origin_header_no_cors_headers(num_allowed):
    """
        When no Origin header is present, no CORS headers should be added.
    """
    allowed = ALLOWED_ORIGINS[:num_allowed]

    cors = CORSMiddleware(allowed_origins=allowed)

    # Request without Origin header
    request = Request(
        method="GET",
        path="/resource"
    )

    def handler(req: Request) -> MockResponse:
        return MockResponse(status_code=200, body=b"ok")

    response = cors(request, handler)

    has_cors_header = "Access-Control-Allow-Origin" in response.headers

    testbase.assert_false(has_cors_header,
        "Response should NOT contain CORS headers when no Origin header is present.")


if __name__ == "__main__":
    from ccai.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
