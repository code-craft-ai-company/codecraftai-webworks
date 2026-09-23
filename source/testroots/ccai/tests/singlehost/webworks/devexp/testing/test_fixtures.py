"""
    Tests for the test fixtures module.

    This module contains unit tests for the resource factory functions
    and helper classes in :mod:`ccai.webworks.devexp.testing.fixtures`.
"""

import json

from ccai.webworks.devexp.testing.fixtures import (
    MockRequest,
    TestApp,
    create_mock_request,
    create_mock_response,
    create_test_app,
    create_test_client,
)
from ccai.webworks.devexp.testing.testclient import TestClient
from ccai.webworks.devexp.testing.testresponse import TestResponse


# =============================================================================
# Unit Tests for MockRequest
# =============================================================================

def test_mock_request_defaults():
    """
        Test that MockRequest has sensible defaults.
    """
    request = MockRequest()

    if request.method != "GET":
        errmsg = "Expected default method 'GET', got '{}'".format(request.method)
        raise AssertionError(errmsg)

    if request.path != "/":
        errmsg = "Expected default path '/', got '{}'".format(request.path)
        raise AssertionError(errmsg)

    if request.headers != {}:
        errmsg = "Expected empty default headers, got {}".format(request.headers)
        raise AssertionError(errmsg)

    if request.body != b"":
        errmsg = "Expected empty default body, got {!r}".format(request.body)
        raise AssertionError(errmsg)

    return


def test_mock_request_custom_values():
    """
        Test that MockRequest stores custom values correctly.
    """
    request = MockRequest(
        method="POST",
        path="/api/users",
        headers={"Content-Type": "application/json"},
        body=b'{"name": "test"}',
    )

    if request.method != "POST":
        errmsg = "Expected method 'POST', got '{}'".format(request.method)
        raise AssertionError(errmsg)

    if request.path != "/api/users":
        errmsg = "Expected path '/api/users', got '{}'".format(request.path)
        raise AssertionError(errmsg)

    expected_headers = {"Content-Type": "application/json"}
    if request.headers != expected_headers:
        errmsg = "Expected headers {}, got {}".format(expected_headers, request.headers)
        raise AssertionError(errmsg)

    if request.body != b'{"name": "test"}':
        errmsg = "Expected body b'{{\"name\": \"test\"}}', got {!r}".format(request.body)
        raise AssertionError(errmsg)

    return


def test_mock_request_get_header_case_insensitive():
    """
        Test that MockRequest.get_header is case-insensitive.
    """
    request = MockRequest(headers={"Content-Type": "text/html"})

    result = request.get_header("content-type")

    if result != "text/html":
        errmsg = "Expected 'text/html', got '{}'".format(result)
        raise AssertionError(errmsg)

    return


def test_mock_request_get_header_returns_default():
    """
        Test that MockRequest.get_header returns default for missing headers.
    """
    request = MockRequest()

    result = request.get_header("X-Missing", default="fallback")

    if result != "fallback":
        errmsg = "Expected 'fallback', got '{}'".format(result)
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for TestApp
# =============================================================================

def test_testapp_default_config():
    """
        Test that TestApp has TESTING=True and DEBUG=False by default.
    """
    app = TestApp()

    if app.config.get("TESTING") is not True:
        errmsg = "Expected TESTING=True, got {}".format(app.config.get("TESTING"))
        raise AssertionError(errmsg)

    if app.config.get("DEBUG") is not False:
        errmsg = "Expected DEBUG=False, got {}".format(app.config.get("DEBUG"))
        raise AssertionError(errmsg)

    return


def test_testapp_custom_config():
    """
        Test that TestApp accepts custom configuration overrides.
    """
    config = {"DATABASE_URL": "sqlite:///:memory:", "SECRET_KEY": "test"}
    app = TestApp(config=config)

    if app.config.get("DATABASE_URL") != "sqlite:///:memory:":
        errmsg = "Expected DATABASE_URL 'sqlite:///:memory:', got '{}'".format(
            app.config.get("DATABASE_URL")
        )
        raise AssertionError(errmsg)

    if app.config.get("SECRET_KEY") != "test":
        errmsg = "Expected SECRET_KEY 'test', got '{}'".format(
            app.config.get("SECRET_KEY")
        )
        raise AssertionError(errmsg)

    # TESTING should still be set
    if app.config.get("TESTING") is not True:
        errmsg = "Expected TESTING=True even with custom config."
        raise AssertionError(errmsg)

    return


def test_testapp_default_echo_callable():
    """
        Test that TestApp with no callable uses the default echo app.
    """
    app = TestApp()

    status_code, headers, body = app("GET", "/test", {}, b"")

    if status_code != 200:
        errmsg = "Expected status 200, got {}".format(status_code)
        raise AssertionError(errmsg)

    data = json.loads(body)

    if data["method"] != "GET":
        errmsg = "Expected method 'GET' in echo response."
        raise AssertionError(errmsg)

    if data["path"] != "/test":
        errmsg = "Expected path '/test' in echo response."
        raise AssertionError(errmsg)

    return


def test_testapp_custom_callable():
    """
        Test that TestApp delegates to a custom callable.
    """
    def custom_app(method, path, headers, body):
        return 201, {"X-Custom": "yes"}, b"created"

    app = TestApp(app_callable=custom_app)

    status_code, headers, body = app("POST", "/create", {}, b"")

    if status_code != 201:
        errmsg = "Expected status 201, got {}".format(status_code)
        raise AssertionError(errmsg)

    if body != b"created":
        errmsg = "Expected body b'created', got {!r}".format(body)
        raise AssertionError(errmsg)

    return


def test_testapp_cleanup():
    """
        Test that TestApp.cleanup sets the cleanup flag.
    """
    app = TestApp()

    if app.is_cleaned_up is not False:
        errmsg = "Expected is_cleaned_up=False before cleanup."
        raise AssertionError(errmsg)

    app.cleanup()

    if app.is_cleaned_up is not True:
        errmsg = "Expected is_cleaned_up=True after cleanup."
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for create_test_app Factory
# =============================================================================

def test_create_test_app_yields_testapp():
    """
        Test that create_test_app yields a TestApp instance.
    """
    gen = create_test_app()
    app = next(gen)

    if not isinstance(app, TestApp):
        errmsg = "Expected TestApp instance, got {}".format(type(app))
        raise AssertionError(errmsg)

    # Exhaust the generator for cleanup
    try:
        next(gen)
    except StopIteration:
        pass

    return


def test_create_test_app_with_config():
    """
        Test that create_test_app applies configuration overrides.
    """
    constraints = {"config": {"SECRET_KEY": "my-secret"}}
    gen = create_test_app(constraints=constraints)
    app = next(gen)

    if app.config.get("SECRET_KEY") != "my-secret":
        errmsg = "Expected SECRET_KEY 'my-secret', got '{}'".format(
            app.config.get("SECRET_KEY")
        )
        raise AssertionError(errmsg)

    try:
        next(gen)
    except StopIteration:
        pass

    return


def test_create_test_app_cleanup_on_exhaust():
    """
        Test that create_test_app performs cleanup when generator is exhausted.
    """
    gen = create_test_app()
    app = next(gen)

    if app.is_cleaned_up is not False:
        errmsg = "Expected is_cleaned_up=False before generator exhaust."
        raise AssertionError(errmsg)

    try:
        next(gen)
    except StopIteration:
        pass

    if app.is_cleaned_up is not True:
        errmsg = "Expected is_cleaned_up=True after generator exhaust."
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for create_test_client Factory
# =============================================================================

def test_create_test_client_yields_testclient():
    """
        Test that create_test_client yields a TestClient instance.
    """
    gen = create_test_client()
    client = next(gen)

    if not isinstance(client, TestClient):
        errmsg = "Expected TestClient instance, got {}".format(type(client))
        raise AssertionError(errmsg)

    try:
        next(gen)
    except StopIteration:
        pass

    return


def test_create_test_client_with_custom_app():
    """
        Test that create_test_client uses a provided app.
    """
    def my_app(method, path, headers, body):
        return 418, {}, b"teapot"

    constraints = {"app": my_app}
    gen = create_test_client(constraints=constraints)
    client = next(gen)

    response = client.get("/brew")

    if response.status_code != 418:
        errmsg = "Expected status 418, got {}".format(response.status_code)
        raise AssertionError(errmsg)

    try:
        next(gen)
    except StopIteration:
        pass

    return


def test_create_test_client_with_default_headers():
    """
        Test that create_test_client applies default headers.
    """
    def echo_app(method, path, headers, body):
        resp_body = json.dumps({"headers": headers}).encode("utf-8")
        return 200, {}, resp_body

    constraints = {
        "app": echo_app,
        "headers": {"Accept": "application/json"},
    }
    gen = create_test_client(constraints=constraints)
    client = next(gen)

    response = client.get("/test")
    data = response.json

    if data["headers"].get("Accept") != "application/json":
        errmsg = "Expected Accept header 'application/json'."
        raise AssertionError(errmsg)

    try:
        next(gen)
    except StopIteration:
        pass

    return


# =============================================================================
# Unit Tests for create_mock_request Factory
# =============================================================================

def test_create_mock_request_defaults():
    """
        Test that create_mock_request yields a MockRequest with defaults.
    """
    gen = create_mock_request()
    request = next(gen)

    if not isinstance(request, MockRequest):
        errmsg = "Expected MockRequest instance, got {}".format(type(request))
        raise AssertionError(errmsg)

    if request.method != "GET":
        errmsg = "Expected default method 'GET', got '{}'".format(request.method)
        raise AssertionError(errmsg)

    if request.path != "/":
        errmsg = "Expected default path '/', got '{}'".format(request.path)
        raise AssertionError(errmsg)

    try:
        next(gen)
    except StopIteration:
        pass

    return


def test_create_mock_request_custom():
    """
        Test that create_mock_request applies custom constraints.
    """
    constraints = {
        "method": "POST",
        "path": "/api/data",
        "headers": {"Authorization": "Bearer token"},
        "body": b"payload",
    }
    gen = create_mock_request(constraints=constraints)
    request = next(gen)

    if request.method != "POST":
        errmsg = "Expected method 'POST', got '{}'".format(request.method)
        raise AssertionError(errmsg)

    if request.path != "/api/data":
        errmsg = "Expected path '/api/data', got '{}'".format(request.path)
        raise AssertionError(errmsg)

    if request.body != b"payload":
        errmsg = "Expected body b'payload', got {!r}".format(request.body)
        raise AssertionError(errmsg)

    try:
        next(gen)
    except StopIteration:
        pass

    return


# =============================================================================
# Unit Tests for create_mock_response Factory
# =============================================================================

def test_create_mock_response_defaults():
    """
        Test that create_mock_response yields a TestResponse with defaults.
    """
    gen = create_mock_response()
    response = next(gen)

    if not isinstance(response, TestResponse):
        errmsg = "Expected TestResponse instance, got {}".format(type(response))
        raise AssertionError(errmsg)

    if response.status_code != 200:
        errmsg = "Expected default status 200, got {}".format(response.status_code)
        raise AssertionError(errmsg)

    if response.body != b"":
        errmsg = "Expected empty default body, got {!r}".format(response.body)
        raise AssertionError(errmsg)

    try:
        next(gen)
    except StopIteration:
        pass

    return


def test_create_mock_response_custom():
    """
        Test that create_mock_response applies custom constraints.
    """
    constraints = {
        "status_code": 404,
        "headers": {"X-Error": "not-found"},
        "body": b"Not Found",
    }
    gen = create_mock_response(constraints=constraints)
    response = next(gen)

    if response.status_code != 404:
        errmsg = "Expected status 404, got {}".format(response.status_code)
        raise AssertionError(errmsg)

    if response.body != b"Not Found":
        errmsg = "Expected body b'Not Found', got {!r}".format(response.body)
        raise AssertionError(errmsg)

    try:
        next(gen)
    except StopIteration:
        pass

    return


def test_create_mock_response_with_json():
    """
        Test that create_mock_response encodes JSON body.
    """
    constraints = {
        "json": {"message": "hello", "count": 42},
    }
    gen = create_mock_response(constraints=constraints)
    response = next(gen)

    data = response.json

    if data.get("message") != "hello":
        errmsg = "Expected message 'hello', got '{}'".format(data.get("message"))
        raise AssertionError(errmsg)

    if data.get("count") != 42:
        errmsg = "Expected count 42, got {}".format(data.get("count"))
        raise AssertionError(errmsg)

    # Content-Type should be set automatically
    content_type = response.get_header("Content-Type")
    if content_type != "application/json":
        errmsg = "Expected Content-Type 'application/json', got '{}'".format(
            content_type
        )
        raise AssertionError(errmsg)

    try:
        next(gen)
    except StopIteration:
        pass

    return
