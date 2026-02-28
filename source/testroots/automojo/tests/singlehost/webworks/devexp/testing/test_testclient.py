"""
    Tests for the TestClient class.

    This module contains unit tests and property-based tests for the
    :class:`TestClient` class including HTTP method helpers, request
    body handling, headers, query parameters, cookie persistence,
    authentication helpers, and correctness properties.
"""

import base64
import json
import random
import string

from automojo.webworks.devexp.testing.testclient import CookieJar, TestClient
from automojo.webworks.devexp.testing.testresponse import TestResponse


# =============================================================================
# Test Helpers
# =============================================================================

def _echo_app(method, path, headers, body):
    """
        A simple echo application that returns request details in the
        response body as JSON.

        :returns: A tuple of (status_code, headers, body).
    """
    response_data = {
        "method": method,
        "path": path,
        "headers": headers,
        "body": body.decode("utf-8") if body else "",
    }
    response_body = json.dumps(response_data).encode("utf-8")
    response_headers = {"Content-Type": "application/json"}

    return 200, response_headers, response_body


def _status_app(method, path, headers, body):
    """
        An application that returns different status codes based on path.
    """
    status_map = {
        "/ok": 200,
        "/created": 201,
        "/not-found": 404,
        "/error": 500,
    }
    status = status_map.get(path, 200)

    return status, {}, b""


def _cookie_app(method, path, headers, body):
    """
        An application that sets and reads cookies.
    """
    if path == "/set-cookie":
        response_headers = {"Set-Cookie": "session=abc123; Path=/"}
        return 200, response_headers, b"cookie set"

    if path == "/set-multi-cookies":
        # Simulate multiple Set-Cookie headers by using a single one
        # (real HTTP allows multiple, but our dict model uses one)
        response_headers = {"Set-Cookie": "token=xyz789; Path=/"}
        return 200, response_headers, b"cookies set"

    if path == "/read-cookie":
        cookie_header = headers.get("Cookie", "")
        response_body = json.dumps({"cookies": cookie_header}).encode("utf-8")
        return 200, {"Content-Type": "application/json"}, response_body

    return 200, {}, b""


# =============================================================================
# Unit Tests for TestClient Construction
# =============================================================================

def test_testclient_stores_app():
    """
        Test that the app callable is stored correctly.
    """
    client = TestClient(app=_echo_app)

    if client.app is not _echo_app:
        errmsg = "Expected app to be the provided callable."
        raise AssertionError(errmsg)

    return


def test_testclient_default_headers_empty():
    """
        Test that default headers are empty when not provided.
    """
    client = TestClient(app=_echo_app)

    if client.default_headers != {}:
        errmsg = "Expected empty default headers, got {}".format(
            client.default_headers
        )
        raise AssertionError(errmsg)

    return


def test_testclient_custom_default_headers():
    """
        Test that custom default headers are stored correctly.
    """
    headers = {"Accept": "application/json"}
    client = TestClient(app=_echo_app, default_headers=headers)

    if client.default_headers != headers:
        errmsg = "Expected default headers {}, got {}".format(
            headers, client.default_headers
        )
        raise AssertionError(errmsg)

    return


def test_testclient_has_cookie_jar():
    """
        Test that the client has a CookieJar instance.
    """
    client = TestClient(app=_echo_app)

    if not isinstance(client.cookies, CookieJar):
        errmsg = "Expected cookies to be a CookieJar instance."
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for HTTP Methods
# =============================================================================

def test_testclient_get():
    """
        Test that get() sends a GET request.
    """
    client = TestClient(app=_echo_app)
    response = client.get("/test")

    data = response.json

    if data["method"] != "GET":
        errmsg = "Expected method 'GET', got '{}'".format(data["method"])
        raise AssertionError(errmsg)

    if data["path"] != "/test":
        errmsg = "Expected path '/test', got '{}'".format(data["path"])
        raise AssertionError(errmsg)

    return


def test_testclient_post():
    """
        Test that post() sends a POST request.
    """
    client = TestClient(app=_echo_app)
    response = client.post("/submit")

    data = response.json

    if data["method"] != "POST":
        errmsg = "Expected method 'POST', got '{}'".format(data["method"])
        raise AssertionError(errmsg)

    return


def test_testclient_put():
    """
        Test that put() sends a PUT request.
    """
    client = TestClient(app=_echo_app)
    response = client.put("/update")

    data = response.json

    if data["method"] != "PUT":
        errmsg = "Expected method 'PUT', got '{}'".format(data["method"])
        raise AssertionError(errmsg)

    return


def test_testclient_patch():
    """
        Test that patch() sends a PATCH request.
    """
    client = TestClient(app=_echo_app)
    response = client.patch("/modify")

    data = response.json

    if data["method"] != "PATCH":
        errmsg = "Expected method 'PATCH', got '{}'".format(data["method"])
        raise AssertionError(errmsg)

    return


def test_testclient_delete():
    """
        Test that delete() sends a DELETE request.
    """
    client = TestClient(app=_echo_app)
    response = client.delete("/remove")

    data = response.json

    if data["method"] != "DELETE":
        errmsg = "Expected method 'DELETE', got '{}'".format(data["method"])
        raise AssertionError(errmsg)

    return


def test_testclient_head():
    """
        Test that head() sends a HEAD request.
    """
    client = TestClient(app=_echo_app)
    response = client.head("/info")

    data = response.json

    if data["method"] != "HEAD":
        errmsg = "Expected method 'HEAD', got '{}'".format(data["method"])
        raise AssertionError(errmsg)

    return


def test_testclient_options():
    """
        Test that options() sends an OPTIONS request.
    """
    client = TestClient(app=_echo_app)
    response = client.options("/cors")

    data = response.json

    if data["method"] != "OPTIONS":
        errmsg = "Expected method 'OPTIONS', got '{}'".format(data["method"])
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for Request Body Handling
# =============================================================================

def test_testclient_post_json_body():
    """
        Test that json parameter sends JSON-encoded body.
    """
    client = TestClient(app=_echo_app)
    payload = {"name": "test", "value": 42}
    response = client.post("/api", json=payload)

    data = response.json
    sent_body = json.loads(data["body"])

    if sent_body != payload:
        errmsg = "Expected body {}, got {}".format(payload, sent_body)
        raise AssertionError(errmsg)

    if data["headers"].get("Content-Type") != "application/json":
        errmsg = "Expected Content-Type 'application/json'."
        raise AssertionError(errmsg)

    return


def test_testclient_post_form_data():
    """
        Test that data parameter sends URL-encoded form data.
    """
    client = TestClient(app=_echo_app)
    form_data = {"username": "admin", "password": "secret"}
    response = client.post("/login", data=form_data)

    data = response.json

    if data["headers"].get("Content-Type") != "application/x-www-form-urlencoded":
        errmsg = "Expected Content-Type 'application/x-www-form-urlencoded'."
        raise AssertionError(errmsg)

    # The body should contain URL-encoded form data
    body_str = data["body"]
    if "username=admin" not in body_str:
        errmsg = "Expected 'username=admin' in body, got '{}'".format(body_str)
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for Headers and Query Parameters
# =============================================================================

def test_testclient_custom_headers():
    """
        Test that custom headers are sent with the request.
    """
    client = TestClient(app=_echo_app)
    response = client.get("/test", headers={"X-Custom": "my-value"})

    data = response.json

    if data["headers"].get("X-Custom") != "my-value":
        errmsg = "Expected X-Custom header 'my-value'."
        raise AssertionError(errmsg)

    return


def test_testclient_default_headers_sent():
    """
        Test that default headers are included in requests.
    """
    client = TestClient(
        app=_echo_app,
        default_headers={"Accept": "application/json"},
    )
    response = client.get("/test")

    data = response.json

    if data["headers"].get("Accept") != "application/json":
        errmsg = "Expected Accept header 'application/json'."
        raise AssertionError(errmsg)

    return


def test_testclient_request_headers_override_defaults():
    """
        Test that request-specific headers override default headers.
    """
    client = TestClient(
        app=_echo_app,
        default_headers={"Accept": "text/html"},
    )
    response = client.get("/test", headers={"Accept": "application/json"})

    data = response.json

    if data["headers"].get("Accept") != "application/json":
        errmsg = "Expected Accept header 'application/json' (override)."
        raise AssertionError(errmsg)

    return


def test_testclient_query_parameters():
    """
        Test that query parameters are appended to the path.
    """
    client = TestClient(app=_echo_app)
    response = client.get("/search", params={"q": "hello", "page": "1"})

    data = response.json
    path = data["path"]

    if "q=hello" not in path:
        errmsg = "Expected 'q=hello' in path, got '{}'".format(path)
        raise AssertionError(errmsg)

    if "page=1" not in path:
        errmsg = "Expected 'page=1' in path, got '{}'".format(path)
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for Cookie Handling
# =============================================================================

def test_testclient_cookies_persisted():
    """
        Test that cookies set by the server are persisted across requests.
    """
    client = TestClient(app=_cookie_app)

    # First request sets a cookie
    client.get("/set-cookie")

    # Second request should include the cookie
    response = client.get("/read-cookie")
    data = response.json

    if "session=abc123" not in data["cookies"]:
        errmsg = "Expected 'session=abc123' in cookies, got '{}'".format(
            data["cookies"]
        )
        raise AssertionError(errmsg)

    return


def test_testclient_cookies_updated():
    """
        Test that cookies are updated when new Set-Cookie headers arrive.
    """
    client = TestClient(app=_cookie_app)

    # Set first cookie
    client.get("/set-cookie")

    # Set second cookie
    client.get("/set-multi-cookies")

    # Both cookies should be present
    response = client.get("/read-cookie")
    data = response.json
    cookie_str = data["cookies"]

    if "session=abc123" not in cookie_str:
        errmsg = "Expected 'session=abc123' in cookies."
        raise AssertionError(errmsg)

    if "token=xyz789" not in cookie_str:
        errmsg = "Expected 'token=xyz789' in cookies."
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for Authentication Helpers
# =============================================================================

def test_testclient_basic_auth():
    """
        Test that set_basic_auth adds Authorization header.
    """
    client = TestClient(app=_echo_app)
    client.set_basic_auth("user", "pass")

    response = client.get("/protected")
    data = response.json

    auth_header = data["headers"].get("Authorization", "")

    if not auth_header.startswith("Basic "):
        errmsg = "Expected 'Basic ' prefix in Authorization header."
        raise AssertionError(errmsg)

    # Decode and verify
    encoded = auth_header[len("Basic "):]
    decoded = base64.b64decode(encoded).decode("utf-8")

    if decoded != "user:pass":
        errmsg = "Expected 'user:pass', got '{}'".format(decoded)
        raise AssertionError(errmsg)

    return


def test_testclient_bearer_token():
    """
        Test that set_bearer_token adds Authorization header.
    """
    client = TestClient(app=_echo_app)
    client.set_bearer_token("my-token-123")

    response = client.get("/protected")
    data = response.json

    auth_header = data["headers"].get("Authorization", "")

    if auth_header != "Bearer my-token-123":
        errmsg = "Expected 'Bearer my-token-123', got '{}'".format(auth_header)
        raise AssertionError(errmsg)

    return


def test_testclient_clear_auth():
    """
        Test that clear_auth removes the Authorization header.
    """
    client = TestClient(app=_echo_app)
    client.set_bearer_token("my-token")
    client.clear_auth()

    response = client.get("/test")
    data = response.json

    if "Authorization" in data["headers"]:
        errmsg = "Expected no Authorization header after clear_auth."
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for TestResponse
# =============================================================================

def test_testclient_returns_testresponse():
    """
        Test that all methods return TestResponse instances.
    """
    client = TestClient(app=_echo_app)
    response = client.get("/test")

    if not isinstance(response, TestResponse):
        errmsg = "Expected TestResponse instance, got {}".format(type(response))
        raise AssertionError(errmsg)

    return


def test_testclient_response_status_code():
    """
        Test that the response status code is correct.
    """
    client = TestClient(app=_status_app)

    response_ok = client.get("/ok")
    response_404 = client.get("/not-found")
    response_500 = client.get("/error")

    if response_ok.status_code != 200:
        errmsg = "Expected 200, got {}".format(response_ok.status_code)
        raise AssertionError(errmsg)

    if response_404.status_code != 404:
        errmsg = "Expected 404, got {}".format(response_404.status_code)
        raise AssertionError(errmsg)

    if response_500.status_code != 500:
        errmsg = "Expected 500, got {}".format(response_500.status_code)
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for CookieJar
# =============================================================================

def test_cookiejar_set_and_get():
    """
        Test that CookieJar stores and retrieves cookies.
    """
    jar = CookieJar()
    jar.set("name", "value")

    result = jar.get("name")

    if result != "value":
        errmsg = "Expected 'value', got '{}'".format(result)
        raise AssertionError(errmsg)

    return


def test_cookiejar_get_missing_returns_default():
    """
        Test that CookieJar returns default for missing cookies.
    """
    jar = CookieJar()

    result = jar.get("missing", default="fallback")

    if result != "fallback":
        errmsg = "Expected 'fallback', got '{}'".format(result)
        raise AssertionError(errmsg)

    return


def test_cookiejar_to_header():
    """
        Test that CookieJar formats cookies as a header string.
    """
    jar = CookieJar()
    jar.set("a", "1")
    jar.set("b", "2")

    header = jar.to_header()

    if "a=1" not in header:
        errmsg = "Expected 'a=1' in header, got '{}'".format(header)
        raise AssertionError(errmsg)

    if "b=2" not in header:
        errmsg = "Expected 'b=2' in header, got '{}'".format(header)
        raise AssertionError(errmsg)

    return


def test_cookiejar_update_from_headers():
    """
        Test that CookieJar extracts cookies from Set-Cookie headers.
    """
    jar = CookieJar()
    headers = {"Set-Cookie": "session=abc123; Path=/; HttpOnly"}

    jar.update_from_headers(headers)

    result = jar.get("session")

    if result != "abc123":
        errmsg = "Expected 'abc123', got '{}'".format(result)
        raise AssertionError(errmsg)

    return


def test_cookiejar_clear():
    """
        Test that CookieJar.clear removes all cookies.
    """
    jar = CookieJar()
    jar.set("a", "1")
    jar.clear()

    if jar.cookies != {}:
        errmsg = "Expected empty cookies after clear, got {}".format(jar.cookies)
        raise AssertionError(errmsg)

    return


def test_cookiejar_delete():
    """
        Test that CookieJar.delete removes a specific cookie.
    """
    jar = CookieJar()
    jar.set("a", "1")
    jar.set("b", "2")
    jar.delete("a")

    if jar.get("a") is not None:
        errmsg = "Expected cookie 'a' to be deleted."
        raise AssertionError(errmsg)

    if jar.get("b") != "2":
        errmsg = "Expected cookie 'b' to still exist."
        raise AssertionError(errmsg)

    return


# =============================================================================
# Property Test Helpers
# =============================================================================

_HTTP_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"]

_PROPERTY_ITERATIONS = 100


def _random_path():
    """
        Generate a random URL path.

        :returns: A path string starting with /.
    """
    depth = random.randint(1, 5)
    parts = []

    for _ in range(depth):
        length = random.randint(1, 12)
        part = "".join(random.choices(string.ascii_lowercase + string.digits, k=length))
        parts.append(part)

    path = "/" + "/".join(parts)

    return path


def _random_headers():
    """
        Generate a random set of request headers.

        :returns: A dictionary of header name-value pairs.
    """
    num_headers = random.randint(0, 5)
    headers = {}

    for _ in range(num_headers):
        name_len = random.randint(3, 10)
        name = "X-" + "".join(random.choices(string.ascii_letters, k=name_len))
        value_len = random.randint(1, 20)
        value = "".join(random.choices(string.ascii_letters + string.digits, k=value_len))
        headers[name] = value

    return headers


def _make_property_app(status_code, response_headers=None, response_body=None):
    """
        Create an application callable that returns a fixed response.

        :param status_code: The status code to return.
        :param response_headers: Optional response headers.
        :param response_body: Optional response body bytes.

        :returns: An application callable.
    """
    if response_headers is None:
        response_headers = {}
    if response_body is None:
        response_body = b""

    def app(method, path, headers, body):
        return status_code, response_headers, response_body

    return app


# =============================================================================
# Property 1: TestClient Request-Response Consistency
# Feature: developer-experience, Property 1: TestClient Request-Response Consistency
# Validates: Requirements 5.1, 5.2, 5.3
# =============================================================================

def test_property_1_request_response_consistency():
    """
        Property 1: TestClient Request-Response Consistency

        For any HTTP method and path, the TestClient SHALL return a
        TestResponse with a valid status_code (100-599), headers
        dictionary, and body bytes.

        This test generates random HTTP methods, paths, and status codes
        across 100 iterations and verifies the response structure.

        **Feature: developer-experience, Property 1: TestClient Request-Response Consistency**
        **Validates: Requirements 5.1, 5.2, 5.3**
    """
    for iteration in range(_PROPERTY_ITERATIONS):
        # Generate random inputs
        method = random.choice(_HTTP_METHODS)
        path = _random_path()
        status_code = random.randint(100, 599)
        response_headers = _random_headers()
        body_length = random.randint(0, 200)
        response_body = bytes(random.getrandbits(8) for _ in range(body_length))

        app = _make_property_app(status_code, response_headers, response_body)
        client = TestClient(app=app)

        # Call the appropriate method
        if method == "GET":
            response = client.get(path)
        elif method == "POST":
            response = client.post(path)
        elif method == "PUT":
            response = client.put(path)
        elif method == "PATCH":
            response = client.patch(path)
        elif method == "DELETE":
            response = client.delete(path)
        elif method == "HEAD":
            response = client.head(path)
        elif method == "OPTIONS":
            response = client.options(path)
        else:
            continue

        # Verify response is a TestResponse
        if not isinstance(response, TestResponse):
            errmsg = (
                "Iteration {}: Expected TestResponse, got {}"
            ).format(iteration, type(response))
            raise AssertionError(errmsg)

        # Verify status_code is valid (100-599)
        if response.status_code < 100 or response.status_code > 599:
            errmsg = (
                "Iteration {}: status_code {} is outside valid range 100-599"
            ).format(iteration, response.status_code)
            raise AssertionError(errmsg)

        # Verify status_code matches what the app returned
        if response.status_code != status_code:
            errmsg = (
                "Iteration {}: Expected status_code {}, got {}"
            ).format(iteration, status_code, response.status_code)
            raise AssertionError(errmsg)

        # Verify headers is a dict
        if not isinstance(response.headers, dict):
            errmsg = (
                "Iteration {}: Expected headers to be a dict, got {}"
            ).format(iteration, type(response.headers))
            raise AssertionError(errmsg)

        # Verify body is bytes
        if not isinstance(response.body, bytes):
            errmsg = (
                "Iteration {}: Expected body to be bytes, got {}"
            ).format(iteration, type(response.body))
            raise AssertionError(errmsg)

        # Verify body matches what the app returned
        if response.body != response_body:
            errmsg = (
                "Iteration {}: Body mismatch. Expected {} bytes, got {} bytes"
            ).format(iteration, len(response_body), len(response.body))
            raise AssertionError(errmsg)

    return


# =============================================================================
# Property 7: Cookie Persistence Across Requests
# Feature: developer-experience, Property 7: Cookie Persistence Across Requests
# Validates: Requirements 5.8
# =============================================================================

def _make_cookie_setting_app(cookies_to_set):
    """
        Create an application that sets cookies on the first request
        and echoes the Cookie header on subsequent requests.

        :param cookies_to_set: A list of (name, value) tuples.

        :returns: An application callable.
    """
    call_count = [0]

    def app(method, path, headers, body):
        call_count[0] += 1

        if call_count[0] == 1:
            # First request: set cookies via Set-Cookie headers
            # Since our dict model only supports one Set-Cookie header,
            # we set them one at a time across multiple requests
            if len(cookies_to_set) > 0:
                name, value = cookies_to_set[0]
                resp_headers = {
                    "Set-Cookie": "{}={}; Path=/".format(name, value),
                }
                return 200, resp_headers, b"cookie set"

        # Subsequent requests: echo the Cookie header
        cookie_header = headers.get("Cookie", "")
        resp_body = json.dumps({"cookies": cookie_header}).encode("utf-8")
        return 200, {"Content-Type": "application/json"}, resp_body

    return app


def _random_cookie_name():
    """
        Generate a random cookie name.

        :returns: A string suitable for use as a cookie name.
    """
    length = random.randint(3, 12)
    name = "".join(random.choices(string.ascii_lowercase, k=length))
    return name


def _random_cookie_value():
    """
        Generate a random cookie value.

        :returns: A string suitable for use as a cookie value.
    """
    length = random.randint(1, 20)
    value = "".join(random.choices(string.ascii_letters + string.digits, k=length))
    return value


def test_property_7_cookie_persistence():
    """
        Property 7: Cookie Persistence Across Requests

        For any sequence of TestClient requests where a response sets
        a cookie, subsequent requests SHALL include that cookie in the
        request headers.

        This test generates random cookie names and values, sets them
        via Set-Cookie response headers, and verifies they appear in
        subsequent request Cookie headers across 100 iterations.

        **Feature: developer-experience, Property 7: Cookie Persistence Across Requests**
        **Validates: Requirements 5.8**
    """
    for iteration in range(_PROPERTY_ITERATIONS):
        # Generate a random cookie
        cookie_name = _random_cookie_name()
        cookie_value = _random_cookie_value()

        # Create an app that sets the cookie on the first path
        # and echoes cookies on the second path
        def make_app(c_name, c_value):
            def app(method, path, headers, body):
                if path == "/set":
                    resp_headers = {
                        "Set-Cookie": "{}={}; Path=/".format(c_name, c_value),
                    }
                    return 200, resp_headers, b"set"
                else:
                    cookie_header = headers.get("Cookie", "")
                    resp_body = json.dumps(
                        {"cookies": cookie_header}
                    ).encode("utf-8")
                    return 200, {"Content-Type": "application/json"}, resp_body
            return app

        app = make_app(cookie_name, cookie_value)
        client = TestClient(app=app)

        # Set the cookie
        client.get("/set")

        # Verify the cookie is sent in subsequent requests
        response = client.get("/check")
        data = response.json
        cookie_header = data["cookies"]

        expected_pair = "{}={}".format(cookie_name, cookie_value)

        if expected_pair not in cookie_header:
            errmsg = (
                "Iteration {}: Expected '{}' in Cookie header, "
                "got '{}'"
            ).format(iteration, expected_pair, cookie_header)
            raise AssertionError(errmsg)

    return


def test_property_7_multiple_cookies_persist():
    """
        Property 7: Cookie Persistence Across Requests

        For any sequence of requests that each set a different cookie,
        all previously set cookies SHALL be included in subsequent
        request headers.

        **Feature: developer-experience, Property 7: Cookie Persistence Across Requests**
        **Validates: Requirements 5.8**
    """
    for iteration in range(_PROPERTY_ITERATIONS):
        # Generate 2-4 random cookies
        num_cookies = random.randint(2, 4)
        cookie_pairs = []

        for _ in range(num_cookies):
            name = _random_cookie_name()
            value = _random_cookie_value()
            cookie_pairs.append((name, value))

        # Create an app where each path sets a different cookie
        def make_app(pairs):
            def app(method, path, headers, body):
                # Path format: /set/0, /set/1, etc.
                if path.startswith("/set/"):
                    idx_str = path[len("/set/"):]
                    try:
                        idx = int(idx_str)
                    except ValueError:
                        idx = 0

                    if idx < len(pairs):
                        c_name, c_value = pairs[idx]
                        resp_headers = {
                            "Set-Cookie": "{}={}".format(c_name, c_value),
                        }
                        return 200, resp_headers, b"set"

                # Echo cookies
                cookie_header = headers.get("Cookie", "")
                resp_body = json.dumps(
                    {"cookies": cookie_header}
                ).encode("utf-8")
                return 200, {"Content-Type": "application/json"}, resp_body

            return app

        app = make_app(cookie_pairs)
        client = TestClient(app=app)

        # Set each cookie via separate requests
        for idx in range(num_cookies):
            client.get("/set/{}".format(idx))

        # Verify all cookies are present
        response = client.get("/check")
        data = response.json
        cookie_header = data["cookies"]

        for c_name, c_value in cookie_pairs:
            expected = "{}={}".format(c_name, c_value)
            if expected not in cookie_header:
                errmsg = (
                    "Iteration {}: Expected '{}' in Cookie header '{}'. "
                    "All cookies: {}"
                ).format(iteration, expected, cookie_header, cookie_pairs)
                raise AssertionError(errmsg)

    return
