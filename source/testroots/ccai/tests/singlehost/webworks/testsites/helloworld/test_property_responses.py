"""
    Property-based tests for helloworld response correctness.

    This module validates that the Dispatcher produces correct responses
    across a variety of inputs for registered endpoints, unregistered
    paths, and unsupported HTTP methods.

    Validates: Requirements 1.3, 3.2, 4.1, 4.2, 6.1, 6.2
"""

import json
import os
import sys

# Add the testsites source directory to the import path so we can
# import the helloworld package directly.
_this_dir = os.path.dirname(os.path.abspath(__file__))
_source_dir = os.path.normpath(os.path.join(_this_dir, os.pardir, os.pardir, os.pardir,
    os.pardir, os.pardir, os.pardir, os.pardir))
_testsites_dir = os.path.join(_source_dir, "testsites")

if _testsites_dir not in sys.path:
    sys.path.insert(0, _testsites_dir)

from ccai.webworks.routing.request import Request
from ccai.webworks.routing.response import HTMLResponse
from ccai.webworks.routing.response import JSONResponse

from helloworld.app import dispatcher


# ---- Registered endpoint definitions used across property tests ----

REGISTERED_ENDPOINTS = {
    "/": {
        "methods": ["GET"],
        "response_type": HTMLResponse,
        "expected_body": b"Hello, World!",
        "expected_status": 200,
    },
    "/health": {
        "methods": ["GET"],
        "response_type": JSONResponse,
        "expected_body_json": {"status": "ok"},
        "expected_status": 200,
    },
}

# HTTP methods to test for 405 scenarios
ALL_HTTP_METHODS = ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"]

# Unregistered paths to test for 404 scenarios
UNREGISTERED_PATHS = [
    "/notfound",
    "/api",
    "/api/v1/resource",
    "/hello",
    "/health/check",
    "/a/b/c/d/e",
    "/index.html",
    "/%20space",
    "/path-with-dashes",
    "/path_with_underscores",
    "/UPPERCASE",
    "/MiXeD",
    "/trailing/",
    "/123/456",
]


# ---- Property 1: Endpoint Response Correctness ----
# Validates: Requirements 1.3, 3.2


def test_property_endpoint_response_correctness():
    """
        **Validates: Requirements 1.3, 3.2**

        Property 1: Endpoint Response Correctness

        For any GET request to a registered path, the Dispatcher SHALL
        return a Response whose status code is 200 and whose body matches
        the expected content for that path.
    """

    for path, spec in REGISTERED_ENDPOINTS.items():
        request = Request(method="GET", path=path)
        response = dispatcher.dispatch(request)

        if response.status_code != spec["expected_status"]:
            errmsg = (
                f"GET {path}: Expected status {spec['expected_status']}, "
                f"got {response.status_code}"
            )
            raise AssertionError(errmsg)

        if not isinstance(response, spec["response_type"]):
            errmsg = (
                f"GET {path}: Expected {spec['response_type'].__name__}, "
                f"got {type(response).__name__}"
            )
            raise AssertionError(errmsg)

        if "expected_body" in spec:
            if response.body != spec["expected_body"]:
                errmsg = (
                    f"GET {path}: Expected body {spec['expected_body']!r}, "
                    f"got {response.body!r}"
                )
                raise AssertionError(errmsg)

        if "expected_body_json" in spec:
            body_content = json.loads(response.body.decode("utf-8"))
            if body_content != spec["expected_body_json"]:
                errmsg = (
                    f"GET {path}: Expected JSON {spec['expected_body_json']}, "
                    f"got {body_content}"
                )
                raise AssertionError(errmsg)

    return


# ---- Property 2: Not Found Consistency ----
# Validates: Requirements 4.1, 4.2


def test_property_not_found_consistency():
    """
        **Validates: Requirements 4.1, 4.2**

        Property 2: Not Found Consistency

        For any request to a path that has no registered endpoint handler,
        the Dispatcher SHALL return a Response with status code 404 and a
        non-empty body.
    """

    for path in UNREGISTERED_PATHS:
        request = Request(method="GET", path=path)
        response = dispatcher.dispatch(request)

        if response.status_code != 404:
            errmsg = (
                f"GET {path}: Expected status 404, "
                f"got {response.status_code}"
            )
            raise AssertionError(errmsg)

        if len(response.body) == 0:
            errmsg = f"GET {path}: Expected non-empty body for 404 response"
            raise AssertionError(errmsg)

    return


# ---- Property 3: Method Not Allowed Consistency ----
# Validates: Requirements 6.1, 6.2


def test_property_method_not_allowed_consistency():
    """
        **Validates: Requirements 6.1, 6.2**

        Property 3: Method Not Allowed Consistency

        For any request to a registered path using an HTTP method that is
        not in the endpoint's registered methods list, the Dispatcher SHALL
        return a Response with status code 405 and an Allow header listing
        the permitted methods.
    """

    for path, spec in REGISTERED_ENDPOINTS.items():
        registered_methods = spec["methods"]
        disallowed_methods = [m for m in ALL_HTTP_METHODS if m not in registered_methods]

        for method in disallowed_methods:
            request = Request(method=method, path=path)
            response = dispatcher.dispatch(request)

            if response.status_code != 405:
                errmsg = (
                    f"{method} {path}: Expected status 405, "
                    f"got {response.status_code}"
                )
                raise AssertionError(errmsg)

            allow_header = response.headers.get("Allow", "")

            for allowed_method in registered_methods:
                if allowed_method not in allow_header:
                    errmsg = (
                        f"{method} {path}: Expected '{allowed_method}' in "
                        f"Allow header, got {allow_header!r}"
                    )
                    raise AssertionError(errmsg)

    return
