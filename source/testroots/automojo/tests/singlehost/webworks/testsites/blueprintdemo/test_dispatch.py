"""
    Tests for the blueprintdemo dispatcher routing.

    This module tests that the Dispatcher correctly routes requests to
    the appropriate handler for each Blueprint path, returns 404 for
    unregistered paths, and returns 405 with an Allow header for
    disallowed HTTP methods.

    Validates: Requirements 5.4, 5.5
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


def test_dispatcher_routes_get_items_list():
    """
        Test that the Dispatcher routes GET /api/items/list to the base
        list handler and returns status 200 with the items list.
    """

    request = Request(method="GET", path="/api/items/list")
    response = dispatcher.dispatch(request)

    if response.status_code != 200:
        errmsg = f"Expected status_code 200, got {response.status_code}"
        raise AssertionError(errmsg)

    body_content = json.loads(response.body.decode("utf-8"))
    expected_content = {"items": [{"id": 1, "name": "Widget"}, {"id": 2, "name": "Gadget"}]}

    if body_content != expected_content:
        errmsg = f"Expected body {expected_content}, got {body_content}"
        raise AssertionError(errmsg)

    return


def test_dispatcher_routes_get_items_detail():
    """
        Test that the Dispatcher routes GET /api/items/detail to the detail
        handler and returns status 200 with a single item.
    """

    request = Request(method="GET", path="/api/items/detail")
    response = dispatcher.dispatch(request)

    if response.status_code != 200:
        errmsg = f"Expected status_code 200, got {response.status_code}"
        raise AssertionError(errmsg)

    body_content = json.loads(response.body.decode("utf-8"))
    expected_content = {"id": 1, "name": "Widget"}

    if body_content != expected_content:
        errmsg = f"Expected body {expected_content}, got {body_content}"
        raise AssertionError(errmsg)

    return


def test_dispatcher_routes_post_items_create():
    """
        Test that the Dispatcher routes POST /api/items/create to the create
        handler and returns status 201 with the created item.
    """

    request = Request(method="POST", path="/api/items/create")
    response = dispatcher.dispatch(request)

    if response.status_code != 201:
        errmsg = f"Expected status_code 201, got {response.status_code}"
        raise AssertionError(errmsg)

    body_content = json.loads(response.body.decode("utf-8"))
    expected_content = {"id": 3, "name": "NewItem", "created": True}

    if body_content != expected_content:
        errmsg = f"Expected body {expected_content}, got {body_content}"
        raise AssertionError(errmsg)

    return


def test_dispatcher_routes_get_v2_items_list():
    """
        Test that the Dispatcher routes GET /api/v2/items/list to the v2
        list handler and returns status 200 with items containing version
        field and total count.
    """

    request = Request(method="GET", path="/api/v2/items/list")
    response = dispatcher.dispatch(request)

    if response.status_code != 200:
        errmsg = f"Expected status_code 200, got {response.status_code}"
        raise AssertionError(errmsg)

    body_content = json.loads(response.body.decode("utf-8"))
    expected_content = {
        "items": [
            {"id": 1, "name": "Widget", "version": "v2"},
            {"id": 2, "name": "Gadget", "version": "v2"}
        ],
        "total": 2
    }

    if body_content != expected_content:
        errmsg = f"Expected body {expected_content}, got {body_content}"
        raise AssertionError(errmsg)

    return


def test_dispatcher_returns_404_for_nonexistent_path():
    """
        Test that the Dispatcher returns a 404 response for a path
        that has no registered endpoint.
    """

    request = Request(method="GET", path="/api/items/nonexistent")
    response = dispatcher.dispatch(request)

    if response.status_code != 404:
        errmsg = f"Expected status_code 404, got {response.status_code}"
        raise AssertionError(errmsg)

    if len(response.body) == 0:
        errmsg = "Expected non-empty body for 404 response"
        raise AssertionError(errmsg)

    return


def test_dispatcher_returns_405_for_post_to_items_list():
    """
        Test that the Dispatcher returns a 405 response with an Allow
        header when POST is sent to /api/items/list which only supports GET.
    """

    request = Request(method="POST", path="/api/items/list")
    response = dispatcher.dispatch(request)

    if response.status_code != 405:
        errmsg = f"Expected status_code 405, got {response.status_code}"
        raise AssertionError(errmsg)

    allow_header = response.headers.get("Allow", "")

    if "GET" not in allow_header:
        errmsg = f"Expected 'GET' in Allow header, got {allow_header!r}"
        raise AssertionError(errmsg)

    return
