"""
    Property-based tests for blueprintdemo response correctness.

    This module validates that the Dispatcher produces correct responses
    across a variety of inputs for registered endpoints across both
    ItemsBlueprint and ItemsV2Blueprint.

    Validates: Requirements 4.2, 4.3
"""

import json
import os
import sys

# Add the testsites source directory to the import path so we can
# import the blueprintdemo package directly.
_this_dir = os.path.dirname(os.path.abspath(__file__))
_source_dir = os.path.normpath(os.path.join(_this_dir, os.pardir, os.pardir, os.pardir,
    os.pardir, os.pardir, os.pardir, os.pardir))
_testsites_dir = os.path.join(_source_dir, "testsites")

if _testsites_dir not in sys.path:
    sys.path.insert(0, _testsites_dir)

from automojo.webworks.routing.request import Request

from blueprintdemo.app import dispatcher


# ---- Registered endpoint definitions used across property tests ----

REGISTERED_ENDPOINTS = [
    ("/api/items/list", "GET", 200, {"items": [{"id": 1, "name": "Widget"}, {"id": 2, "name": "Gadget"}]}),
    ("/api/items/detail", "GET", 200, {"id": 1, "name": "Widget"}),
    ("/api/items/create", "POST", 201, {"id": 3, "name": "NewItem", "created": True}),
    ("/api/v2/items/list", "GET", 200, {"items": [{"id": 1, "name": "Widget", "version": "v2"}, {"id": 2, "name": "Gadget", "version": "v2"}], "total": 2}),
]


# ---- Property 1: Endpoint Response Correctness ----
# Feature: blueprint-testsite, Property 1: Endpoint Response Correctness
# Validates: Requirements 4.2, 4.3


def test_property_endpoint_response_correctness():
    """
        **Validates: Requirements 4.2, 4.3**

        Feature: blueprint-testsite, Property 1: Endpoint Response Correctness

        For any registered endpoint path and its allowed HTTP method across
        both ItemsBlueprint and ItemsV2Blueprint, the Dispatcher SHALL return
        a response whose status code and body content match the expected
        values for that endpoint.
    """

    for path, method, expected_status, expected_body in REGISTERED_ENDPOINTS:
        request = Request(method=method, path=path)
        response = dispatcher.dispatch(request)

        if response.status_code != expected_status:
            errmsg = (
                f"{method} {path}: Expected status {expected_status}, "
                f"got {response.status_code}"
            )
            raise AssertionError(errmsg)

        body_content = json.loads(response.body.decode("utf-8"))

        if body_content != expected_body:
            errmsg = (
                f"{method} {path}: Expected body {expected_body}, "
                f"got {body_content}"
            )
            raise AssertionError(errmsg)

    return


# ---- Unregistered paths used for 404 property tests ----

UNREGISTERED_PATHS = [
    "/api/items/nonexistent",
    "/api/v2/items/detail",
    "/api/v2/items/create",
    "/nonexistent",
    "/api/items",
    "/api",
    "/nowhere",
]


# ---- Property 2: Not Found Consistency ----
# Feature: blueprint-testsite, Property 2: Not Found Consistency
# Validates: Requirements 4.4


def test_property_not_found_consistency():
    """
        **Validates: Requirements 4.4**

        Feature: blueprint-testsite, Property 2: Not Found Consistency

        For any request path that does not match any registered endpoint,
        the Dispatcher SHALL return a response with status code 404 and
        a non-empty body.
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


# ---- All HTTP methods used for 405 property tests ----

ALL_HTTP_METHODS = ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"]


# ---- Property 3: Method Not Allowed Consistency ----
# Feature: blueprint-testsite, Property 3: Method Not Allowed Consistency
# Validates: Requirements 4.5


def test_property_method_not_allowed_consistency():
    """
        **Validates: Requirements 4.5**

        Feature: blueprint-testsite, Property 3: Method Not Allowed Consistency

        For any registered endpoint path and any HTTP method not in that
        endpoint's allowed methods list, the Dispatcher SHALL return a
        response with status code 405 and an Allow header that contains
        all permitted methods for that path.
    """

    # Build a dict of path -> set of allowed methods from REGISTERED_ENDPOINTS
    path_allowed_methods = {}

    for path, method, _status, _body in REGISTERED_ENDPOINTS:
        if path not in path_allowed_methods:
            path_allowed_methods[path] = set()
        path_allowed_methods[path].add(method)

    for path, allowed_methods in path_allowed_methods.items():
        disallowed_methods = [m for m in ALL_HTTP_METHODS if m not in allowed_methods]

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

            for allowed_method in allowed_methods:
                if allowed_method not in allow_header:
                    errmsg = (
                        f"{method} {path}: Expected '{allowed_method}' in "
                        f"Allow header, got {allow_header!r}"
                    )
                    raise AssertionError(errmsg)

    return
