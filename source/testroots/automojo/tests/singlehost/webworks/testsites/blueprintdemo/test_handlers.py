"""
    Tests for the blueprintdemo endpoint handlers.

    This module tests that the ItemsBlueprint and ItemsV2Blueprint handlers
    return the correct response types, status codes, and body content when
    invoked directly with a mock request.

    Validates: Requirements 5.1, 5.5, 5.7
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

from automojo.testbase.mocking import Mock

from automojo.webworks.routing.response import JSONResponse

from blueprintdemo.endpoints.handlers import ItemsBlueprint
from blueprintdemo.endpoints.handlers import ItemsV2Blueprint


def _create_mock_request(method: str = "GET", path: str = "/") -> Mock:
    """
        Create a mock Request object for testing.

        :param method: The HTTP method for the request.
        :param path: The URL path for the request.

        :returns: A configured Mock object.
    """

    mock_request = Mock()
    mock_request.configure(recursive=True)

    ctx = mock_request.mock_context()
    ctx.set_attribute("method", method)
    ctx.set_attribute("path", path)

    return mock_request


# ---- Base Blueprint: list_items ----

def test_list_items_returns_json_response():
    """
        Test that list_items returns a JSONResponse instance.
    """

    request = _create_mock_request(method="GET", path="/api/items/list")
    response = ItemsBlueprint.list_items(request)

    if not isinstance(response, JSONResponse):
        errmsg = f"Expected JSONResponse, got {type(response).__name__}"
        raise AssertionError(errmsg)

    return


def test_list_items_returns_status_200():
    """
        Test that list_items returns status code 200.
    """

    request = _create_mock_request(method="GET", path="/api/items/list")
    response = ItemsBlueprint.list_items(request)

    if response.status_code != 200:
        errmsg = f"Expected status_code 200, got {response.status_code}"
        raise AssertionError(errmsg)

    return


def test_list_items_returns_correct_body():
    """
        Test that list_items returns body containing items list.
    """

    request = _create_mock_request(method="GET", path="/api/items/list")
    response = ItemsBlueprint.list_items(request)

    body_content = json.loads(response.body.decode("utf-8"))
    expected_content = {"items": [{"id": 1, "name": "Widget"}, {"id": 2, "name": "Gadget"}]}

    if body_content != expected_content:
        errmsg = f"Expected body {expected_content}, got {body_content}"
        raise AssertionError(errmsg)

    return


# ---- Base Blueprint: get_item ----

def test_get_item_returns_json_response():
    """
        Test that get_item returns a JSONResponse instance.
    """

    request = _create_mock_request(method="GET", path="/api/items/detail")
    response = ItemsBlueprint.get_item(request)

    if not isinstance(response, JSONResponse):
        errmsg = f"Expected JSONResponse, got {type(response).__name__}"
        raise AssertionError(errmsg)

    return


def test_get_item_returns_status_200():
    """
        Test that get_item returns status code 200.
    """

    request = _create_mock_request(method="GET", path="/api/items/detail")
    response = ItemsBlueprint.get_item(request)

    if response.status_code != 200:
        errmsg = f"Expected status_code 200, got {response.status_code}"
        raise AssertionError(errmsg)

    return


def test_get_item_returns_correct_body():
    """
        Test that get_item returns body containing a single item.
    """

    request = _create_mock_request(method="GET", path="/api/items/detail")
    response = ItemsBlueprint.get_item(request)

    body_content = json.loads(response.body.decode("utf-8"))
    expected_content = {"id": 1, "name": "Widget"}

    if body_content != expected_content:
        errmsg = f"Expected body {expected_content}, got {body_content}"
        raise AssertionError(errmsg)

    return


# ---- Base Blueprint: create_item ----

def test_create_item_returns_json_response():
    """
        Test that create_item returns a JSONResponse instance.
    """

    request = _create_mock_request(method="POST", path="/api/items/create")
    response = ItemsBlueprint.create_item(request)

    if not isinstance(response, JSONResponse):
        errmsg = f"Expected JSONResponse, got {type(response).__name__}"
        raise AssertionError(errmsg)

    return


def test_create_item_returns_status_201():
    """
        Test that create_item returns status code 201.
    """

    request = _create_mock_request(method="POST", path="/api/items/create")
    response = ItemsBlueprint.create_item(request)

    if response.status_code != 201:
        errmsg = f"Expected status_code 201, got {response.status_code}"
        raise AssertionError(errmsg)

    return


def test_create_item_returns_correct_body():
    """
        Test that create_item returns body containing created item with created flag.
    """

    request = _create_mock_request(method="POST", path="/api/items/create")
    response = ItemsBlueprint.create_item(request)

    body_content = json.loads(response.body.decode("utf-8"))
    expected_content = {"id": 3, "name": "NewItem", "created": True}

    if body_content != expected_content:
        errmsg = f"Expected body {expected_content}, got {body_content}"
        raise AssertionError(errmsg)

    return


# ---- Extended Blueprint: list_items (v2) ----

def test_v2_list_items_returns_json_response():
    """
        Test that ItemsV2Blueprint.list_items returns a JSONResponse instance.
    """

    request = _create_mock_request(method="GET", path="/api/v2/items/list")
    response = ItemsV2Blueprint.list_items(request)

    if not isinstance(response, JSONResponse):
        errmsg = f"Expected JSONResponse, got {type(response).__name__}"
        raise AssertionError(errmsg)

    return


def test_v2_list_items_returns_status_200():
    """
        Test that ItemsV2Blueprint.list_items returns status code 200.
    """

    request = _create_mock_request(method="GET", path="/api/v2/items/list")
    response = ItemsV2Blueprint.list_items(request)

    if response.status_code != 200:
        errmsg = f"Expected status_code 200, got {response.status_code}"
        raise AssertionError(errmsg)

    return


def test_v2_list_items_returns_correct_body():
    """
        Test that ItemsV2Blueprint.list_items returns items with version field and total count.
    """

    request = _create_mock_request(method="GET", path="/api/v2/items/list")
    response = ItemsV2Blueprint.list_items(request)

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
