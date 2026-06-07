"""
    Tests for the blueprintdemo application wiring.

    This module tests that the app module correctly wires together the
    ASGIApplication, Router, Dispatcher, and registered endpoints. It
    verifies that the module-level ``app``, ``router``, and ``dispatcher``
    variables are correctly instantiated and that the Router has the
    expected endpoints registered with the correct allowed methods.

    Validates: Requirements 5.2, 5.3
"""

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

from ccai.webworks.asgi.application import ASGIApplication
from ccai.webworks.routing.dispatcher import Dispatcher

from blueprintdemo.app import app, router, dispatcher


def test_app_is_asgi_application_instance():
    """
        Test that the module-level app variable is an ASGIApplication instance.
    """

    if not isinstance(app, ASGIApplication):
        errmsg = f"Expected ASGIApplication instance, got {type(app).__name__}"
        raise AssertionError(errmsg)

    return


def test_dispatcher_is_dispatcher_instance():
    """
        Test that the module-level dispatcher variable is a Dispatcher instance.
    """

    if not isinstance(dispatcher, Dispatcher):
        errmsg = f"Expected Dispatcher instance, got {type(dispatcher).__name__}"
        raise AssertionError(errmsg)

    return


def test_router_has_items_list_endpoint():
    """
        Test that the Router has a registered endpoint for /api/items/list
        with GET as an allowed method.
    """

    allowed = router.get_allowed_methods("/api/items/list")

    if "GET" not in allowed:
        errmsg = f"Expected GET in allowed methods for /api/items/list, got {allowed}"
        raise AssertionError(errmsg)

    return


def test_router_has_items_detail_endpoint():
    """
        Test that the Router has a registered endpoint for /api/items/detail
        with GET as an allowed method.
    """

    allowed = router.get_allowed_methods("/api/items/detail")

    if "GET" not in allowed:
        errmsg = f"Expected GET in allowed methods for /api/items/detail, got {allowed}"
        raise AssertionError(errmsg)

    return


def test_router_has_items_create_endpoint():
    """
        Test that the Router has a registered endpoint for /api/items/create
        with POST as an allowed method.
    """

    allowed = router.get_allowed_methods("/api/items/create")

    if "POST" not in allowed:
        errmsg = f"Expected POST in allowed methods for /api/items/create, got {allowed}"
        raise AssertionError(errmsg)

    return


def test_router_has_v2_items_list_endpoint():
    """
        Test that the Router has a registered endpoint for /api/v2/items/list
        with GET as an allowed method.
    """

    allowed = router.get_allowed_methods("/api/v2/items/list")

    if "GET" not in allowed:
        errmsg = f"Expected GET in allowed methods for /api/v2/items/list, got {allowed}"
        raise AssertionError(errmsg)

    return


def test_router_list_endpoint_allows_only_get():
    """
        Test that the /api/items/list endpoint only allows GET requests.
    """

    allowed = router.get_allowed_methods("/api/items/list")

    if allowed != ["GET"]:
        errmsg = f"Expected allowed methods ['GET'] for /api/items/list, got {allowed}"
        raise AssertionError(errmsg)

    return


def test_router_detail_endpoint_allows_only_get():
    """
        Test that the /api/items/detail endpoint only allows GET requests.
    """

    allowed = router.get_allowed_methods("/api/items/detail")

    if allowed != ["GET"]:
        errmsg = f"Expected allowed methods ['GET'] for /api/items/detail, got {allowed}"
        raise AssertionError(errmsg)

    return


def test_router_create_endpoint_allows_only_post():
    """
        Test that the /api/items/create endpoint only allows POST requests.
    """

    allowed = router.get_allowed_methods("/api/items/create")

    if allowed != ["POST"]:
        errmsg = f"Expected allowed methods ['POST'] for /api/items/create, got {allowed}"
        raise AssertionError(errmsg)

    return


def test_router_v2_list_endpoint_allows_only_get():
    """
        Test that the /api/v2/items/list endpoint only allows GET requests.
    """

    allowed = router.get_allowed_methods("/api/v2/items/list")

    if allowed != ["GET"]:
        errmsg = f"Expected allowed methods ['GET'] for /api/v2/items/list, got {allowed}"
        raise AssertionError(errmsg)

    return
