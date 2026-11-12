"""
    Tests for the test client transports.

    This module contains unit tests for detecting which interface an
    application implements and for creating the matching transport.
"""

from ccai.webworks.devexp.testing.transports import ASGITransport
from ccai.webworks.devexp.testing.transports import CallableTransport
from ccai.webworks.devexp.testing.transports import TRANSPORT_ASGI
from ccai.webworks.devexp.testing.transports import TRANSPORT_CALLABLE
from ccai.webworks.devexp.testing.transports import TRANSPORT_WSGI
from ccai.webworks.devexp.testing.transports import TransportError
from ccai.webworks.devexp.testing.transports import WSGITransport
from ccai.webworks.devexp.testing.transports import create_transport
from ccai.webworks.devexp.testing.transports import detect_transport


# =============================================================================
# Test Helpers
# =============================================================================

async def _asgi_function(scope, receive, send):
    """
        An ASGI application written as a coroutine function.
    """
    return


class _AsgiObject:
    """
        An ASGI application written as an object with an async __call__.
    """

    async def __call__(self, scope, receive, send):
        return


def _wsgi_function(environ, start_response):
    """
        A WSGI application.
    """
    start_response("200 OK", [])
    return [b""]


def _plain_callable(method, path, headers, body):
    """
        A plain application callable.
    """
    return 200, {}, b""


# =============================================================================
# Unit Tests for detect_transport
# =============================================================================

def test_detect_transport_recognises_asgi_function():
    """
        Test that a coroutine function is detected as ASGI.
    """
    result = detect_transport(_asgi_function)

    if result != TRANSPORT_ASGI:
        errmsg = "Expected '{}', got '{}'".format(TRANSPORT_ASGI, result)
        raise AssertionError(errmsg)

    return


def test_detect_transport_recognises_asgi_object():
    """
        Test that an object with an async __call__ is detected as ASGI.
    """
    result = detect_transport(_AsgiObject())

    if result != TRANSPORT_ASGI:
        errmsg = "Expected '{}', got '{}'".format(TRANSPORT_ASGI, result)
        raise AssertionError(errmsg)

    return


def test_detect_transport_recognises_framework_asgi_application():
    """
        Test that the framework's ASGIApplication is detected as ASGI.
    """
    from ccai.webworks.asgi.application import create_asgi_application

    result = detect_transport(create_asgi_application())

    if result != TRANSPORT_ASGI:
        errmsg = "Expected '{}', got '{}'".format(TRANSPORT_ASGI, result)
        raise AssertionError(errmsg)

    return


def test_detect_transport_recognises_wsgi_function():
    """
        Test that a synchronous two-argument callable is detected as WSGI.
    """
    result = detect_transport(_wsgi_function)

    if result != TRANSPORT_WSGI:
        errmsg = "Expected '{}', got '{}'".format(TRANSPORT_WSGI, result)
        raise AssertionError(errmsg)

    return


def test_detect_transport_recognises_plain_callable():
    """
        Test that a four-argument callable is detected as the plain callable.
    """
    result = detect_transport(_plain_callable)

    if result != TRANSPORT_CALLABLE:
        errmsg = "Expected '{}', got '{}'".format(TRANSPORT_CALLABLE, result)
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for create_transport
# =============================================================================

def test_create_transport_builds_the_detected_transport():
    """
        Test that each kind of application gets its transport class.
    """
    expectations = [
        (_asgi_function, ASGITransport),
        (_wsgi_function, WSGITransport),
        (_plain_callable, CallableTransport),
    ]

    for application, expected_class in expectations:
        transport = create_transport(application)

        if not isinstance(transport, expected_class):
            errmsg = "Expected {} for {}, got {}".format(
                expected_class.__name__, application.__name__, type(transport).__name__
            )
            raise AssertionError(errmsg)

        transport.close()

    return


def test_create_transport_honours_explicit_name():
    """
        Test that an explicit transport name overrides detection.
    """
    transport = create_transport(_wsgi_function, transport=TRANSPORT_CALLABLE)

    if not isinstance(transport, CallableTransport):
        errmsg = "Expected CallableTransport, got {}".format(type(transport).__name__)
        raise AssertionError(errmsg)

    return


def test_create_transport_rejects_unknown_name():
    """
        Test that an unknown transport name raises ValueError.
    """
    raised = False

    try:
        create_transport(_plain_callable, transport="carrier-pigeon")
    except ValueError:
        raised = True

    if raised is not True:
        errmsg = "Expected ValueError for an unknown transport name."
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for Misbehaving Applications
# =============================================================================

def test_asgi_transport_reports_application_without_response():
    """
        Test that an ASGI application that returns without responding
        raises TransportError.
    """
    transport = ASGITransport(_asgi_function)

    try:
        raised = False
        try:
            transport.send("GET", "/", [], b"", "http", "testserver")
        except TransportError:
            raised = True
    finally:
        transport.close()

    if raised is not True:
        errmsg = "Expected TransportError for an application that sent no response."
        raise AssertionError(errmsg)

    return


def test_wsgi_transport_reports_missing_start_response():
    """
        Test that a WSGI application that never calls start_response
        raises TransportError.
    """
    def _silent_wsgi(environ, start_response):
        return [b"body without a status"]

    transport = WSGITransport(_silent_wsgi)

    raised = False
    try:
        transport.send("GET", "/", [], b"", "http", "testserver")
    except TransportError:
        raised = True

    if raised is not True:
        errmsg = "Expected TransportError for an application that did not call start_response."
        raise AssertionError(errmsg)

    return
