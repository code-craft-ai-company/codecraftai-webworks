"""
    Tests for the TestResponse class.

    This module contains unit tests for the :class:`TestResponse` class
    including status code, headers, body, text and json properties, and
    the case-insensitive get_header method.
"""

import json

from ccai.webworks.devexp.testing.testresponse import TestResponse


# =============================================================================
# Unit Tests for TestResponse Construction
# =============================================================================

def test_testresponse_stores_status_code():
    """
        Test that the status code is stored correctly.
    """
    response = TestResponse(status_code=200, headers={}, body=b"")

    if response.status_code != 200:
        errmsg = "Expected status_code 200, got {}".format(response.status_code)
        raise AssertionError(errmsg)

    return


def test_testresponse_stores_headers():
    """
        Test that headers are stored correctly.
    """
    headers = {"Content-Type": "text/html", "X-Custom": "value"}
    response = TestResponse(status_code=200, headers=headers, body=b"")

    if response.headers != headers:
        errmsg = "Expected headers {}, got {}".format(headers, response.headers)
        raise AssertionError(errmsg)

    return


def test_testresponse_stores_body():
    """
        Test that the body is stored correctly.
    """
    body = b"Hello, World!"
    response = TestResponse(status_code=200, headers={}, body=body)

    if response.body != body:
        errmsg = "Expected body {!r}, got {!r}".format(body, response.body)
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for TestResponse Properties
# =============================================================================

def test_testresponse_text_property():
    """
        Test that the text property decodes body as UTF-8.
    """
    body = "Hello, World!".encode("utf-8")
    response = TestResponse(status_code=200, headers={}, body=body)

    if response.text != "Hello, World!":
        errmsg = "Expected text 'Hello, World!', got '{}'".format(response.text)
        raise AssertionError(errmsg)

    return


def test_testresponse_json_property():
    """
        Test that the json property parses body as JSON.
    """
    data = {"key": "value", "count": 42}
    body = json.dumps(data).encode("utf-8")
    response = TestResponse(status_code=200, headers={}, body=body)

    result = response.json

    if result != data:
        errmsg = "Expected json {}, got {}".format(data, result)
        raise AssertionError(errmsg)

    return


def test_testresponse_json_property_raises_on_invalid_json():
    """
        Test that the json property raises ValueError for invalid JSON.
    """
    response = TestResponse(status_code=200, headers={}, body=b"not json")

    raised = False
    try:
        _ = response.json
    except ValueError:
        raised = True

    if raised is not True:
        errmsg = "Expected ValueError for invalid JSON body."
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for get_header
# =============================================================================

def test_testresponse_get_header_exact_case():
    """
        Test that get_header finds a header with exact case match.
    """
    headers = {"Content-Type": "application/json"}
    response = TestResponse(status_code=200, headers=headers, body=b"")

    result = response.get_header("Content-Type")

    if result != "application/json":
        errmsg = "Expected 'application/json', got '{}'".format(result)
        raise AssertionError(errmsg)

    return


def test_testresponse_get_header_case_insensitive():
    """
        Test that get_header is case-insensitive.
    """
    headers = {"Content-Type": "text/html"}
    response = TestResponse(status_code=200, headers=headers, body=b"")

    result = response.get_header("content-type")

    if result != "text/html":
        errmsg = "Expected 'text/html', got '{}'".format(result)
        raise AssertionError(errmsg)

    return


def test_testresponse_get_header_returns_default():
    """
        Test that get_header returns the default when header is missing.
    """
    response = TestResponse(status_code=200, headers={}, body=b"")

    result = response.get_header("X-Missing", default="fallback")

    if result != "fallback":
        errmsg = "Expected 'fallback', got '{}'".format(result)
        raise AssertionError(errmsg)

    return


def test_testresponse_get_header_returns_none_by_default():
    """
        Test that get_header returns None when header is missing
        and no default is provided.
    """
    response = TestResponse(status_code=200, headers={}, body=b"")

    result = response.get_header("X-Missing")

    if result is not None:
        errmsg = "Expected None, got '{}'".format(result)
        raise AssertionError(errmsg)

    return
