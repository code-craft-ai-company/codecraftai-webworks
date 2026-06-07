"""
    Tests for the helloworld application wiring.

    This module tests that the app module correctly wires together the
    ASGIApplication, Router, Dispatcher, and registered endpoints. It
    verifies that the module-level ``app`` variable is an ASGIApplication
    instance, that the Router has the expected endpoints registered, and
    that the Dispatcher correctly dispatches requests and handles error
    cases (404 and 405).

    Validates: Requirements 2.5, 4.1, 4.2, 6.1, 6.2
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

from ccai.webworks.asgi.application import ASGIApplication
from ccai.webworks.routing.request import Request
from ccai.webworks.routing.response import HTMLResponse
from ccai.webworks.routing.response import JSONResponse

from helloworld.app import app
from helloworld.app import router
from helloworld.app import dispatcher


def test_app_is_asgi_application_instance():
    """
        Test that the module-level app variable is an ASGIApplication instance.
    """

    if not isinstance(app, ASGIApplication):
        errmsg = f"Expected ASGIApplication instance, got {type(app).__name__}"
        raise AssertionError(errmsg)

    return


def test_router_has_root_endpoint():
    """
        Test that the Router has a registered endpoint for the / path.
    """

    allowed = router.get_allowed_methods("/")

    if "GET" not in allowed:
        errmsg = f"Expected GET in allowed methods for /, got {allowed}"
        raise AssertionError(errmsg)

    return


def test_router_has_health_endpoint():
    """
        Test that the Router has a registered endpoint for the /health path.
    """

    allowed = router.get_allowed_methods("/health")

    if "GET" not in allowed:
        errmsg = f"Expected GET in allowed methods for /health, got {allowed}"
        raise AssertionError(errmsg)

    return


def test_dispatcher_dispatches_get_root():
    """
        Test that the Dispatcher dispatches GET / to the hello_world handler
        and returns an HTMLResponse with status 200 and body "Hello, World!".
    """

    request = Request(method="GET", path="/")
    response = dispatcher.dispatch(request)

    if response.status_code != 200:
        errmsg = f"Expected status_code 200, got {response.status_code}"
        raise AssertionError(errmsg)

    if not isinstance(response, HTMLResponse):
        errmsg = f"Expected HTMLResponse, got {type(response).__name__}"
        raise AssertionError(errmsg)

    if response.body != b"Hello, World!":
        errmsg = f"Expected body b'Hello, World!', got {response.body!r}"
        raise AssertionError(errmsg)

    return


def test_dispatcher_dispatches_get_health():
    """
        Test that the Dispatcher dispatches GET /health to the health_check
        handler and returns a JSONResponse with status 200 and body
        {"status": "ok"}.
    """

    request = Request(method="GET", path="/health")
    response = dispatcher.dispatch(request)

    if response.status_code != 200:
        errmsg = f"Expected status_code 200, got {response.status_code}"
        raise AssertionError(errmsg)

    body_content = json.loads(response.body.decode("utf-8"))
    expected_content = {"status": "ok"}

    if body_content != expected_content:
        errmsg = f"Expected body {expected_content}, got {body_content}"
        raise AssertionError(errmsg)

    return


def test_dispatcher_returns_404_for_unregistered_path():
    """
        Test that the Dispatcher returns a 404 response for a path
        that has no registered endpoint.
    """

    request = Request(method="GET", path="/nonexistent")
    response = dispatcher.dispatch(request)

    if response.status_code != 404:
        errmsg = f"Expected status_code 404, got {response.status_code}"
        raise AssertionError(errmsg)

    if len(response.body) == 0:
        errmsg = "Expected non-empty body for 404 response"
        raise AssertionError(errmsg)

    return


def test_dispatcher_returns_405_for_post_to_root():
    """
        Test that the Dispatcher returns a 405 response with an Allow
        header when POST is sent to / which only supports GET.
    """

    request = Request(method="POST", path="/")
    response = dispatcher.dispatch(request)

    if response.status_code != 405:
        errmsg = f"Expected status_code 405, got {response.status_code}"
        raise AssertionError(errmsg)

    allow_header = response.headers.get("Allow", "")

    if "GET" not in allow_header:
        errmsg = f"Expected 'GET' in Allow header, got {allow_header!r}"
        raise AssertionError(errmsg)

    return
