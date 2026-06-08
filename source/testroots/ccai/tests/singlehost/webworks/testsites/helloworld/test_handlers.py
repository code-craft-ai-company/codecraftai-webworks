"""
    Tests for the helloworld endpoint handlers.

    This module tests that the hello_world and health_check handlers
    return the correct response types, status codes, and body content.

    Validates: Requirements 1.3, 3.2
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

from ccai.testbase.mocking import Mock

from ccai.webworks.routing.response import HTMLResponse
from ccai.webworks.routing.response import JSONResponse

from helloworld.endpoints.handlers import hello_world
from helloworld.endpoints.handlers import health_check


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


def test_hello_world_returns_html_response():
    """
        Test that hello_world returns an HTMLResponse instance.
    """

    request = _create_mock_request(method="GET", path="/")
    response = hello_world(request)

    if not isinstance(response, HTMLResponse):
        errmsg = f"Expected HTMLResponse, got {type(response).__name__}"
        raise AssertionError(errmsg)

    return


def test_hello_world_returns_status_200():
    """
        Test that hello_world returns status code 200.
    """

    request = _create_mock_request(method="GET", path="/")
    response = hello_world(request)

    if response.status_code != 200:
        errmsg = f"Expected status_code 200, got {response.status_code}"
        raise AssertionError(errmsg)

    return


def test_hello_world_returns_correct_body():
    """
        Test that hello_world returns body containing "Hello, World!".
    """

    request = _create_mock_request(method="GET", path="/")
    response = hello_world(request)

    expected_body = b"Hello, World!"

    if response.body != expected_body:
        errmsg = f"Expected body {expected_body!r}, got {response.body!r}"
        raise AssertionError(errmsg)

    return


def test_health_check_returns_json_response():
    """
        Test that health_check returns a JSONResponse instance.
    """

    request = _create_mock_request(method="GET", path="/health")
    response = health_check(request)

    if not isinstance(response, JSONResponse):
        errmsg = f"Expected JSONResponse, got {type(response).__name__}"
        raise AssertionError(errmsg)

    return


def test_health_check_returns_status_200():
    """
        Test that health_check returns status code 200.
    """

    request = _create_mock_request(method="GET", path="/health")
    response = health_check(request)

    if response.status_code != 200:
        errmsg = f"Expected status_code 200, got {response.status_code}"
        raise AssertionError(errmsg)

    return


def test_health_check_returns_correct_body():
    """
        Test that health_check returns body containing {"status": "ok"}.
    """

    request = _create_mock_request(method="GET", path="/health")
    response = health_check(request)

    body_content = json.loads(response.body.decode("utf-8"))
    expected_content = {"status": "ok"}

    if body_content != expected_content:
        errmsg = f"Expected body {expected_content}, got {body_content}"
        raise AssertionError(errmsg)

    return
