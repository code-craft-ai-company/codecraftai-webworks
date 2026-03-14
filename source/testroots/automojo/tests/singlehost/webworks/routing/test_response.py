"""
    Tests for the Response module.
    
    This module tests the Response class and its subclasses for building
    HTTP responses with status codes, headers, and body content.
"""

import json

from automojo.webworks.routing.response import (
    Response,
    JSONResponse,
    HTMLResponse,
    RedirectResponse,
    StreamingResponse,
    HTTP_STATUS_PHRASES,
)


# =============================================================================
# Response Base Class Tests
# =============================================================================

def test_response_default_construction():
    """
        Test Response construction with default values.
    """
    response = Response()
    
    if response.status_code != 200:
        errmsg = f"Expected status_code 200, got {response.status_code}"
        raise AssertionError(errmsg)
    
    if response.body != b"":
        errmsg = f"Expected empty body, got {response.body}"
        raise AssertionError(errmsg)
    
    if response.headers != {}:
        errmsg = f"Expected empty headers, got {response.headers}"
        raise AssertionError(errmsg)
    
    return


def test_response_construction_with_values():
    """
        Test Response construction with explicit values.
    """
    headers = {"Content-Type": "text/plain"}
    body = b"Hello, World!"
    
    response = Response(status_code=201, headers=headers, body=body)
    
    if response.status_code != 201:
        errmsg = f"Expected status_code 201, got {response.status_code}"
        raise AssertionError(errmsg)
    
    if response.body != body:
        errmsg = f"Expected body {body}, got {response.body}"
        raise AssertionError(errmsg)
    
    if response.headers.get("Content-Type") != "text/plain":
        errmsg = f"Expected Content-Type 'text/plain', got {response.headers.get('Content-Type')}"
        raise AssertionError(errmsg)
    
    return


def test_response_set_header():
    """
        Test Response.set_header() method.
    """
    response = Response()
    
    response.set_header("X-Custom-Header", "custom-value")
    
    if response.headers.get("X-Custom-Header") != "custom-value":
        errmsg = f"Expected 'custom-value', got {response.headers.get('X-Custom-Header')}"
        raise AssertionError(errmsg)
    
    return


def test_response_set_header_overwrites():
    """
        Test that set_header overwrites existing header.
    """
    response = Response(headers={"X-Header": "old-value"})
    
    response.set_header("X-Header", "new-value")
    
    if response.headers.get("X-Header") != "new-value":
        errmsg = f"Expected 'new-value', got {response.headers.get('X-Header')}"
        raise AssertionError(errmsg)
    
    return


def test_response_set_cookie_basic():
    """
        Test Response.set_cookie() with basic parameters.
    """
    response = Response()
    
    response.set_cookie("session", "abc123")
    
    # Verify cookie is set by checking to_wsgi output
    status, headers, body = response.to_wsgi()
    
    cookie_headers = [h for h in headers if h[0] == "Set-Cookie"]
    if len(cookie_headers) != 1:
        errmsg = f"Expected 1 Set-Cookie header, got {len(cookie_headers)}"
        raise AssertionError(errmsg)
    
    if "session=abc123" not in cookie_headers[0][1]:
        errmsg = f"Expected 'session=abc123' in cookie, got {cookie_headers[0][1]}"
        raise AssertionError(errmsg)
    
    return


def test_response_set_cookie_with_options():
    """
        Test Response.set_cookie() with all options.
    """
    response = Response()
    
    response.set_cookie(
        name="session",
        value="abc123",
        max_age=3600,
        path="/app",
        domain="example.com",
        secure=True,
        httponly=True,
        samesite="Strict"
    )
    
    status, headers, body = response.to_wsgi()
    
    cookie_headers = [h for h in headers if h[0] == "Set-Cookie"]
    if len(cookie_headers) != 1:
        errmsg = f"Expected 1 Set-Cookie header, got {len(cookie_headers)}"
        raise AssertionError(errmsg)
    
    cookie_value = cookie_headers[0][1]
    
    if "session=abc123" not in cookie_value:
        errmsg = f"Expected 'session=abc123' in cookie, got {cookie_value}"
        raise AssertionError(errmsg)
    
    if "Max-Age=3600" not in cookie_value:
        errmsg = f"Expected 'Max-Age=3600' in cookie, got {cookie_value}"
        raise AssertionError(errmsg)
    
    if "Path=/app" not in cookie_value:
        errmsg = f"Expected 'Path=/app' in cookie, got {cookie_value}"
        raise AssertionError(errmsg)
    
    if "Domain=example.com" not in cookie_value:
        errmsg = f"Expected 'Domain=example.com' in cookie, got {cookie_value}"
        raise AssertionError(errmsg)
    
    if "Secure" not in cookie_value:
        errmsg = f"Expected 'Secure' in cookie, got {cookie_value}"
        raise AssertionError(errmsg)
    
    if "HttpOnly" not in cookie_value:
        errmsg = f"Expected 'HttpOnly' in cookie, got {cookie_value}"
        raise AssertionError(errmsg)
    
    if "SameSite=Strict" not in cookie_value:
        errmsg = f"Expected 'SameSite=Strict' in cookie, got {cookie_value}"
        raise AssertionError(errmsg)
    
    return


def test_response_delete_cookie():
    """
        Test Response.delete_cookie() method.
    """
    response = Response()
    
    response.delete_cookie("session")
    
    status, headers, body = response.to_wsgi()
    
    cookie_headers = [h for h in headers if h[0] == "Set-Cookie"]
    if len(cookie_headers) != 1:
        errmsg = f"Expected 1 Set-Cookie header, got {len(cookie_headers)}"
        raise AssertionError(errmsg)
    
    cookie_value = cookie_headers[0][1]
    
    if "session=" not in cookie_value:
        errmsg = f"Expected 'session=' in cookie, got {cookie_value}"
        raise AssertionError(errmsg)
    
    if "Max-Age=0" not in cookie_value:
        errmsg = f"Expected 'Max-Age=0' in cookie, got {cookie_value}"
        raise AssertionError(errmsg)
    
    if "1970" not in cookie_value:
        errmsg = f"Expected '1970' (expired date) in cookie, got {cookie_value}"
        raise AssertionError(errmsg)
    
    return


def test_response_delete_cookie_with_path_and_domain():
    """
        Test Response.delete_cookie() with path and domain.
    """
    response = Response()
    
    response.delete_cookie("session", path="/app", domain="example.com")
    
    status, headers, body = response.to_wsgi()
    
    cookie_headers = [h for h in headers if h[0] == "Set-Cookie"]
    cookie_value = cookie_headers[0][1]
    
    if "Path=/app" not in cookie_value:
        errmsg = f"Expected 'Path=/app' in cookie, got {cookie_value}"
        raise AssertionError(errmsg)
    
    if "Domain=example.com" not in cookie_value:
        errmsg = f"Expected 'Domain=example.com' in cookie, got {cookie_value}"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Response WSGI Conversion Tests
# =============================================================================

def test_response_to_wsgi_basic():
    """
        Test Response.to_wsgi() basic conversion.
    """
    response = Response(
        status_code=200,
        headers={"Content-Type": "text/plain"},
        body=b"Hello"
    )
    
    status, headers, body_iter = response.to_wsgi()
    
    if status != "200 OK":
        errmsg = f"Expected status '200 OK', got '{status}'"
        raise AssertionError(errmsg)
    
    if ("Content-Type", "text/plain") not in headers:
        errmsg = f"Expected Content-Type header in {headers}"
        raise AssertionError(errmsg)
    
    body_list = list(body_iter)
    if body_list != [b"Hello"]:
        errmsg = f"Expected body [b'Hello'], got {body_list}"
        raise AssertionError(errmsg)
    
    return


def test_response_to_wsgi_empty_body():
    """
        Test Response.to_wsgi() with empty body.
    """
    response = Response(status_code=204)
    
    status, headers, body_iter = response.to_wsgi()
    
    if status != "204 No Content":
        errmsg = f"Expected status '204 No Content', got '{status}'"
        raise AssertionError(errmsg)
    
    body_list = list(body_iter)
    if body_list != []:
        errmsg = f"Expected empty body list, got {body_list}"
        raise AssertionError(errmsg)
    
    return


def test_response_to_wsgi_status_phrases():
    """
        Test Response.to_wsgi() generates correct status phrases.
    """
    test_cases = [
        (200, "200 OK"),
        (201, "201 Created"),
        (301, "301 Moved Permanently"),
        (400, "400 Bad Request"),
        (404, "404 Not Found"),
        (500, "500 Internal Server Error"),
    ]
    
    for status_code, expected_status in test_cases:
        response = Response(status_code=status_code)
        status, headers, body_iter = response.to_wsgi()
        if status != expected_status:
            errmsg = f"Expected status '{expected_status}', got '{status}'"
            raise AssertionError(errmsg)
    
    return


def test_response_to_wsgi_includes_cookies():
    """
        Test Response.to_wsgi() includes Set-Cookie headers.
    """
    response = Response()
    response.set_cookie("cookie1", "value1")
    response.set_cookie("cookie2", "value2")
    
    status, headers, body_iter = response.to_wsgi()
    
    cookie_headers = [h for h in headers if h[0] == "Set-Cookie"]
    if len(cookie_headers) != 2:
        errmsg = f"Expected 2 Set-Cookie headers, got {len(cookie_headers)}"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Response ASGI Conversion Tests
# =============================================================================

def test_response_to_asgi_basic():
    """
        Test Response.to_asgi() basic conversion.
    """
    response = Response(
        status_code=200,
        headers={"Content-Type": "text/plain"},
        body=b"Hello"
    )
    
    result = response.to_asgi()
    
    if "start" not in result:
        errmsg = "Expected 'start' key in ASGI result"
        raise AssertionError(errmsg)
    
    if "body" not in result:
        errmsg = "Expected 'body' key in ASGI result"
        raise AssertionError(errmsg)
    
    start_event = result["start"]
    if start_event["type"] != "http.response.start":
        errmsg = f"Expected type 'http.response.start', got {start_event['type']}"
        raise AssertionError(errmsg)
    
    if start_event["status"] != 200:
        errmsg = f"Expected status 200, got {start_event['status']}"
        raise AssertionError(errmsg)
    
    body_event = result["body"]
    if body_event["type"] != "http.response.body":
        errmsg = f"Expected type 'http.response.body', got {body_event['type']}"
        raise AssertionError(errmsg)
    
    if body_event["body"] != b"Hello":
        errmsg = f"Expected body b'Hello', got {body_event['body']}"
        raise AssertionError(errmsg)
    
    if body_event["more_body"] != False:
        errmsg = f"Expected more_body False, got {body_event['more_body']}"
        raise AssertionError(errmsg)
    
    return


def test_response_to_asgi_headers_encoded():
    """
        Test Response.to_asgi() encodes headers as bytes.
    """
    response = Response(headers={"Content-Type": "application/json"})
    
    result = response.to_asgi()
    
    headers = result["start"]["headers"]
    if len(headers) == 0:
        errmsg = "Expected at least one header"
        raise AssertionError(errmsg)
    
    # Headers should be lists of [name_bytes, value_bytes]
    for header in headers:
        if not isinstance(header[0], bytes):
            errmsg = f"Expected header name to be bytes, got {type(header[0])}"
            raise AssertionError(errmsg)
        if not isinstance(header[1], bytes):
            errmsg = f"Expected header value to be bytes, got {type(header[1])}"
            raise AssertionError(errmsg)
    
    return


def test_response_to_asgi_includes_cookies():
    """
        Test Response.to_asgi() includes Set-Cookie headers.
    """
    response = Response()
    response.set_cookie("session", "abc123")
    
    result = response.to_asgi()
    
    headers = result["start"]["headers"]
    cookie_headers = [h for h in headers if h[0] == b"Set-Cookie"]
    if len(cookie_headers) != 1:
        errmsg = f"Expected 1 Set-Cookie header, got {len(cookie_headers)}"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# JSONResponse Tests
# =============================================================================

def test_json_response_basic():
    """
        Test JSONResponse with basic dict content.
    """
    content = {"message": "Hello", "count": 42}
    
    response = JSONResponse(content)
    
    if response.status_code != 200:
        errmsg = f"Expected status_code 200, got {response.status_code}"
        raise AssertionError(errmsg)
    
    if response.headers.get("Content-Type") != "application/json; charset=utf-8":
        errmsg = f"Expected Content-Type 'application/json; charset=utf-8', got {response.headers.get('Content-Type')}"
        raise AssertionError(errmsg)
    
    # Verify body is valid JSON
    parsed = json.loads(response.body.decode("utf-8"))
    if parsed != content:
        errmsg = f"Expected {content}, got {parsed}"
        raise AssertionError(errmsg)
    
    return


def test_json_response_with_status_code():
    """
        Test JSONResponse with custom status code.
    """
    response = JSONResponse({"error": "Not found"}, status_code=404)
    
    if response.status_code != 404:
        errmsg = f"Expected status_code 404, got {response.status_code}"
        raise AssertionError(errmsg)
    
    return


def test_json_response_with_headers():
    """
        Test JSONResponse with additional headers.
    """
    response = JSONResponse(
        {"data": "value"},
        headers={"X-Custom": "header"}
    )
    
    if response.headers.get("X-Custom") != "header":
        errmsg = f"Expected X-Custom 'header', got {response.headers.get('X-Custom')}"
        raise AssertionError(errmsg)
    
    if response.headers.get("Content-Type") != "application/json; charset=utf-8":
        errmsg = f"Expected Content-Type 'application/json; charset=utf-8', got {response.headers.get('Content-Type')}"
        raise AssertionError(errmsg)
    
    return


def test_json_response_list_content():
    """
        Test JSONResponse with list content.
    """
    content = [1, 2, 3, "four"]
    
    response = JSONResponse(content)
    
    parsed = json.loads(response.body.decode("utf-8"))
    if parsed != content:
        errmsg = f"Expected {content}, got {parsed}"
        raise AssertionError(errmsg)
    
    return


def test_json_response_unicode_content():
    """
        Test JSONResponse with unicode content.
    """
    content = {"message": "Hello, 世界! 🌍"}
    
    response = JSONResponse(content)
    
    parsed = json.loads(response.body.decode("utf-8"))
    if parsed["message"] != "Hello, 世界! 🌍":
        errmsg = f"Expected 'Hello, 世界! 🌍', got {parsed['message']}"
        raise AssertionError(errmsg)
    
    return


def test_json_response_repr():
    """
        Test JSONResponse string representation.
    """
    response = JSONResponse({"key": "value"}, status_code=201)
    
    repr_str = repr(response)
    if repr_str != "JSONResponse(201)":
        errmsg = f"Expected 'JSONResponse(201)', got '{repr_str}'"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# HTMLResponse Tests
# =============================================================================

def test_html_response_basic():
    """
        Test HTMLResponse with basic HTML content.
    """
    html = "<html><body><h1>Hello</h1></body></html>"
    
    response = HTMLResponse(html)
    
    if response.status_code != 200:
        errmsg = f"Expected status_code 200, got {response.status_code}"
        raise AssertionError(errmsg)
    
    if response.headers.get("Content-Type") != "text/html; charset=utf-8":
        errmsg = f"Expected Content-Type 'text/html; charset=utf-8', got {response.headers.get('Content-Type')}"
        raise AssertionError(errmsg)
    
    if response.body != html.encode("utf-8"):
        errmsg = f"Expected body {html.encode('utf-8')}, got {response.body}"
        raise AssertionError(errmsg)
    
    return


def test_html_response_with_status_code():
    """
        Test HTMLResponse with custom status code.
    """
    response = HTMLResponse("<h1>Error</h1>", status_code=500)
    
    if response.status_code != 500:
        errmsg = f"Expected status_code 500, got {response.status_code}"
        raise AssertionError(errmsg)
    
    return


def test_html_response_unicode():
    """
        Test HTMLResponse with unicode content.
    """
    html = "<p>Hello, 世界!</p>"
    
    response = HTMLResponse(html)
    
    if response.body.decode("utf-8") != html:
        errmsg = f"Expected '{html}', got '{response.body.decode('utf-8')}'"
        raise AssertionError(errmsg)
    
    return


def test_html_response_repr():
    """
        Test HTMLResponse string representation.
    """
    response = HTMLResponse("<p>Test</p>", status_code=200)
    
    repr_str = repr(response)
    if repr_str != "HTMLResponse(200)":
        errmsg = f"Expected 'HTMLResponse(200)', got '{repr_str}'"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# RedirectResponse Tests
# =============================================================================

def test_redirect_response_basic():
    """
        Test RedirectResponse with basic URL.
    """
    response = RedirectResponse("/new-location")
    
    if response.status_code != 307:
        errmsg = f"Expected status_code 307, got {response.status_code}"
        raise AssertionError(errmsg)
    
    if response.headers.get("Location") != "/new-location":
        errmsg = f"Expected Location '/new-location', got {response.headers.get('Location')}"
        raise AssertionError(errmsg)
    
    if response.body != b"":
        errmsg = f"Expected empty body, got {response.body}"
        raise AssertionError(errmsg)
    
    return


def test_redirect_response_permanent():
    """
        Test RedirectResponse with permanent redirect status.
    """
    response = RedirectResponse("/permanent", status_code=301)
    
    if response.status_code != 301:
        errmsg = f"Expected status_code 301, got {response.status_code}"
        raise AssertionError(errmsg)
    
    if response.headers.get("Location") != "/permanent":
        errmsg = f"Expected Location '/permanent', got {response.headers.get('Location')}"
        raise AssertionError(errmsg)
    
    return


def test_redirect_response_found():
    """
        Test RedirectResponse with 302 Found status.
    """
    response = RedirectResponse("/found", status_code=302)
    
    if response.status_code != 302:
        errmsg = f"Expected status_code 302, got {response.status_code}"
        raise AssertionError(errmsg)
    
    return


def test_redirect_response_see_other():
    """
        Test RedirectResponse with 303 See Other status.
    """
    response = RedirectResponse("/other", status_code=303)
    
    if response.status_code != 303:
        errmsg = f"Expected status_code 303, got {response.status_code}"
        raise AssertionError(errmsg)
    
    return


def test_redirect_response_absolute_url():
    """
        Test RedirectResponse with absolute URL.
    """
    response = RedirectResponse("https://example.com/path")
    
    if response.headers.get("Location") != "https://example.com/path":
        errmsg = f"Expected Location 'https://example.com/path', got {response.headers.get('Location')}"
        raise AssertionError(errmsg)
    
    return


def test_redirect_response_repr():
    """
        Test RedirectResponse string representation.
    """
    response = RedirectResponse("/target", status_code=302)
    
    repr_str = repr(response)
    if repr_str != "RedirectResponse(302, '/target')":
        errmsg = f"Expected \"RedirectResponse(302, '/target')\", got '{repr_str}'"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# StreamingResponse Tests
# =============================================================================

def test_streaming_response_basic():
    """
        Test StreamingResponse with basic content.
    """
    chunks = [b"chunk1", b"chunk2", b"chunk3"]
    
    response = StreamingResponse(iter(chunks))
    
    if response.status_code != 200:
        errmsg = f"Expected status_code 200, got {response.status_code}"
        raise AssertionError(errmsg)
    
    return


def test_streaming_response_with_media_type():
    """
        Test StreamingResponse with media type.
    """
    response = StreamingResponse(
        iter([b"data"]),
        media_type="application/octet-stream"
    )
    
    if response.headers.get("Content-Type") != "application/octet-stream":
        errmsg = f"Expected Content-Type 'application/octet-stream', got {response.headers.get('Content-Type')}"
        raise AssertionError(errmsg)
    
    return


def test_streaming_response_body_property():
    """
        Test StreamingResponse.body property consumes iterator.
    """
    chunks = [b"chunk1", b"chunk2"]
    
    response = StreamingResponse(iter(chunks))
    
    body = response.body
    if body != b"chunk1chunk2":
        errmsg = f"Expected b'chunk1chunk2', got {body}"
        raise AssertionError(errmsg)
    
    return


def test_streaming_response_to_wsgi():
    """
        Test StreamingResponse.to_wsgi() returns iterator.
    """
    chunks = [b"a", b"b", b"c"]
    
    response = StreamingResponse(iter(chunks))
    
    status, headers, body_iter = response.to_wsgi()
    
    if status != "200 OK":
        errmsg = f"Expected status '200 OK', got '{status}'"
        raise AssertionError(errmsg)
    
    body_list = list(body_iter)
    if body_list != chunks:
        errmsg = f"Expected {chunks}, got {body_list}"
        raise AssertionError(errmsg)
    
    return


def test_streaming_response_with_status_code():
    """
        Test StreamingResponse with custom status code.
    """
    response = StreamingResponse(iter([b"data"]), status_code=206)
    
    if response.status_code != 206:
        errmsg = f"Expected status_code 206, got {response.status_code}"
        raise AssertionError(errmsg)
    
    return


def test_streaming_response_repr():
    """
        Test StreamingResponse string representation.
    """
    response = StreamingResponse(iter([b"data"]), status_code=200)
    
    repr_str = repr(response)
    if repr_str != "StreamingResponse(200)":
        errmsg = f"Expected 'StreamingResponse(200)', got '{repr_str}'"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Response Status Code Setter Tests
# =============================================================================

def test_response_status_code_setter():
    """
        Test Response status_code setter.
    """
    response = Response(status_code=200)
    
    response.status_code = 404
    
    if response.status_code != 404:
        errmsg = f"Expected status_code 404, got {response.status_code}"
        raise AssertionError(errmsg)
    
    return


def test_response_body_setter():
    """
        Test Response body setter.
    """
    response = Response(body=b"original")
    
    response.body = b"modified"
    
    if response.body != b"modified":
        errmsg = f"Expected body b'modified', got {response.body}"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Response repr Tests
# =============================================================================

def test_response_repr():
    """
        Test Response string representation.
    """
    response = Response(status_code=201)
    
    repr_str = repr(response)
    if repr_str != "Response(201)":
        errmsg = f"Expected 'Response(201)', got '{repr_str}'"
        raise AssertionError(errmsg)
    
    return



# =============================================================================
# Property Tests
# =============================================================================

import random
import string


def _random_string(length: int = 8) -> str:
    """Generate a random alphanumeric string."""
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))


def _random_status_code() -> int:
    """Generate a random valid HTTP status code."""
    return random.choice([
        200, 201, 202, 204,
        301, 302, 303, 307, 308,
        400, 401, 403, 404, 405, 409, 422, 429,
        500, 501, 502, 503, 504
    ])


def _random_header_name() -> str:
    """Generate a random header name."""
    prefixes = ["X-", "Custom-", "App-", ""]
    prefix = random.choice(prefixes)
    name = ''.join(random.choices(string.ascii_letters, k=random.randint(4, 12)))
    return prefix + name.title()


def _random_header_value() -> str:
    """Generate a random header value."""
    return _random_string(random.randint(5, 20))


def _random_headers(count: int = None) -> dict:
    """Generate random headers dict."""
    if count is None:
        count = random.randint(0, 5)
    return {_random_header_name(): _random_header_value() for _ in range(count)}


def _random_body() -> bytes:
    """Generate random body bytes."""
    length = random.randint(0, 100)
    return bytes(random.choices(range(256), k=length))


def _random_ascii_body() -> bytes:
    """Generate random ASCII body bytes."""
    length = random.randint(0, 100)
    return ''.join(random.choices(string.ascii_letters + string.digits + ' ', k=length)).encode('utf-8')


# -----------------------------------------------------------------------------
# Property 7: Response Format Conversion
# **Validates: Requirements 4.5, 4.6**
#
# *For any* Response object with valid status_code, headers, and body, calling
# `to_wsgi()` SHALL produce a valid WSGI response tuple, and calling `to_asgi()`
# SHALL produce valid ASGI response events. The status code, headers, and body
# SHALL be preserved in both conversions.
# -----------------------------------------------------------------------------

def test_property_response_format_conversion():
    """
    Property 7: Response Format Conversion
    
    For any Response object with valid status_code, headers, and body:
    - to_wsgi() produces a valid WSGI response tuple (status, headers, body)
    - to_asgi() produces valid ASGI response events
    - Status code, headers, and body are preserved in both conversions
    
    **Feature: router-request-handling, Property 7: Response Format Conversion**
    **Validates: Requirements 4.5, 4.6**
    """
    # Run 100 iterations
    for _ in range(100):
        # Generate random response components
        status_code = _random_status_code()
        headers = _random_headers()
        body = _random_ascii_body()
        
        # Create response
        response = Response(status_code=status_code, headers=headers, body=body)
        
        # Property: to_wsgi() produces valid WSGI response tuple
        wsgi_status, wsgi_headers, wsgi_body_iter = response.to_wsgi()
        
        # Verify WSGI status format
        if not isinstance(wsgi_status, str):
            errmsg = f"WSGI status should be string, got {type(wsgi_status)}"
            raise AssertionError(errmsg)
        
        if not wsgi_status.startswith(str(status_code)):
            errmsg = f"WSGI status should start with {status_code}, got {wsgi_status}"
            raise AssertionError(errmsg)
        
        # Verify WSGI headers format
        if not isinstance(wsgi_headers, list):
            errmsg = f"WSGI headers should be list, got {type(wsgi_headers)}"
            raise AssertionError(errmsg)
        
        for header in wsgi_headers:
            if not isinstance(header, tuple) or len(header) != 2:
                errmsg = f"WSGI header should be 2-tuple, got {header}"
                raise AssertionError(errmsg)
            if not isinstance(header[0], str) or not isinstance(header[1], str):
                errmsg = f"WSGI header name and value should be strings, got {type(header[0])}, {type(header[1])}"
                raise AssertionError(errmsg)
        
        # Verify headers are preserved
        for name, value in headers.items():
            found = False
            for h_name, h_value in wsgi_headers:
                if h_name == name and h_value == value:
                    found = True
                    break
            if not found:
                errmsg = f"Header {name}={value} not found in WSGI headers"
                raise AssertionError(errmsg)
        
        # Verify WSGI body
        wsgi_body_list = list(wsgi_body_iter)
        if body:
            if wsgi_body_list != [body]:
                errmsg = f"WSGI body should be [{body}], got {wsgi_body_list}"
                raise AssertionError(errmsg)
        else:
            if wsgi_body_list != []:
                errmsg = f"WSGI body should be empty for empty body, got {wsgi_body_list}"
                raise AssertionError(errmsg)
        
        # Property: to_asgi() produces valid ASGI response events
        asgi_result = response.to_asgi()
        
        if "start" not in asgi_result:
            errmsg = "ASGI result should have 'start' key"
            raise AssertionError(errmsg)
        
        if "body" not in asgi_result:
            errmsg = "ASGI result should have 'body' key"
            raise AssertionError(errmsg)
        
        start_event = asgi_result["start"]
        body_event = asgi_result["body"]
        
        # Verify ASGI start event
        if start_event.get("type") != "http.response.start":
            errmsg = f"ASGI start event type should be 'http.response.start', got {start_event.get('type')}"
            raise AssertionError(errmsg)
        
        if start_event.get("status") != status_code:
            errmsg = f"ASGI status should be {status_code}, got {start_event.get('status')}"
            raise AssertionError(errmsg)
        
        # Verify ASGI headers format (list of [bytes, bytes])
        asgi_headers = start_event.get("headers", [])
        for header in asgi_headers:
            if not isinstance(header, list) or len(header) != 2:
                errmsg = f"ASGI header should be 2-element list, got {header}"
                raise AssertionError(errmsg)
            if not isinstance(header[0], bytes) or not isinstance(header[1], bytes):
                errmsg = f"ASGI header name and value should be bytes, got {type(header[0])}, {type(header[1])}"
                raise AssertionError(errmsg)
        
        # Verify headers are preserved in ASGI
        for name, value in headers.items():
            found = False
            for h in asgi_headers:
                if h[0].decode("latin-1") == name and h[1].decode("latin-1") == value:
                    found = True
                    break
            if not found:
                errmsg = f"Header {name}={value} not found in ASGI headers"
                raise AssertionError(errmsg)
        
        # Verify ASGI body event
        if body_event.get("type") != "http.response.body":
            errmsg = f"ASGI body event type should be 'http.response.body', got {body_event.get('type')}"
            raise AssertionError(errmsg)
        
        if body_event.get("body") != body:
            errmsg = f"ASGI body should be {body}, got {body_event.get('body')}"
            raise AssertionError(errmsg)
        
        if body_event.get("more_body") != False:
            errmsg = f"ASGI more_body should be False, got {body_event.get('more_body')}"
            raise AssertionError(errmsg)
    
    return


# -----------------------------------------------------------------------------
# Property 8: JSONResponse Serialization Round-Trip
# **Validates: Requirements 4.7**
#
# *For any* Python object that is JSON-serializable, constructing a JSONResponse
# and parsing its body as JSON SHALL produce an equivalent object.
# -----------------------------------------------------------------------------

def _random_json_value(depth: int = 0, max_depth: int = 3):
    """Generate a random JSON-serializable value."""
    if depth >= max_depth:
        # At max depth, only generate primitives
        choice = random.randint(0, 4)
    else:
        choice = random.randint(0, 6)
    
    if choice == 0:
        # String
        return _random_string(random.randint(1, 20))
    elif choice == 1:
        # Integer
        return random.randint(-10000, 10000)
    elif choice == 2:
        # Float
        return random.uniform(-1000.0, 1000.0)
    elif choice == 3:
        # Boolean
        return random.choice([True, False])
    elif choice == 4:
        # None
        return None
    elif choice == 5:
        # List
        length = random.randint(0, 5)
        return [_random_json_value(depth + 1, max_depth) for _ in range(length)]
    else:
        # Dict
        length = random.randint(0, 5)
        return {_random_string(random.randint(3, 10)): _random_json_value(depth + 1, max_depth) for _ in range(length)}


def test_property_json_response_round_trip():
    """
    Property 8: JSONResponse Serialization Round-Trip
    
    For any Python object that is JSON-serializable:
    - Constructing a JSONResponse serializes the object to JSON
    - Parsing the body as JSON produces an equivalent object
    
    **Feature: router-request-handling, Property 8: JSONResponse Serialization Round-Trip**
    **Validates: Requirements 4.7**
    """
    # Run 100 iterations
    for _ in range(100):
        # Generate random JSON-serializable content
        content = _random_json_value()
        
        # Create JSONResponse
        response = JSONResponse(content)
        
        # Property: Content-Type should be application/json
        content_type = response.headers.get("Content-Type")
        if content_type != "application/json; charset=utf-8":
            errmsg = f"Content-Type should be 'application/json; charset=utf-8', got {content_type}"
            raise AssertionError(errmsg)
        
        # Property: Round-trip - parse body as JSON and compare
        parsed = json.loads(response.body.decode("utf-8"))
        
        # For floats, we need approximate comparison due to floating point precision
        if not _json_equal(content, parsed):
            errmsg = f"Round-trip failed: original={content}, parsed={parsed}"
            raise AssertionError(errmsg)
    
    return


def _json_equal(a, b, epsilon: float = 1e-9) -> bool:
    """
    Compare two JSON values for equality, with approximate comparison for floats.
    """
    if type(a) != type(b):
        # Special case: int vs float comparison
        if isinstance(a, (int, float)) and isinstance(b, (int, float)):
            return abs(float(a) - float(b)) < epsilon
        return False
    
    if isinstance(a, dict):
        if set(a.keys()) != set(b.keys()):
            return False
        return all(_json_equal(a[k], b[k], epsilon) for k in a.keys())
    
    if isinstance(a, list):
        if len(a) != len(b):
            return False
        return all(_json_equal(x, y, epsilon) for x, y in zip(a, b))
    
    if isinstance(a, float):
        return abs(a - b) < epsilon
    
    return a == b


# =============================================================================
# BUG-3 Regression: StreamingResponse generator double-consumption
# =============================================================================

def test_streaming_response_body_then_iter_content():
    """
        Test that calling iter_content() after .body returns the cached data
        rather than yielding nothing from an exhausted generator.
    """
    chunks = [b"chunk1", b"chunk2", b"chunk3"]
    
    response = StreamingResponse(iter(chunks))
    
    # Consume via .body
    body = response.body
    if body != b"chunk1chunk2chunk3":
        errmsg = f"Expected b'chunk1chunk2chunk3', got {body}"
        raise AssertionError(errmsg)
    
    # iter_content() must still return data from the cache
    iter_chunks = list(response.iter_content())
    if len(iter_chunks) == 0:
        errmsg = "iter_content() returned no data after .body consumed the generator"
        raise AssertionError(errmsg)
    
    joined = b"".join(iter_chunks)
    if joined != body:
        errmsg = f"Expected iter_content to yield cached body {body}, got {joined}"
        raise AssertionError(errmsg)
    
    return


def test_streaming_response_iter_content_before_body():
    """
        Test that iter_content() works correctly when called before .body.
    """
    chunks = [b"a", b"b", b"c"]
    
    response = StreamingResponse(iter(chunks))
    
    # Consume via iter_content first
    iter_chunks = list(response.iter_content())
    if iter_chunks != chunks:
        errmsg = f"Expected {chunks}, got {iter_chunks}"
        raise AssertionError(errmsg)
    
    return


