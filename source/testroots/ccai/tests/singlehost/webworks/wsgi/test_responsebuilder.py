"""
    Tests for the ResponseBuilder class.
    
    This module contains unit tests and property-based tests for the WSGI
    response builder functionality.
    
    **Feature: wsgi-layer, Property 3: Response Formatting Correctness**
    **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.7**
"""

import random
import string
from typing import Dict

from ccai.webworks.wsgi.response import Response, ResponseBuilder
from ccai.webworks.wsgi.exceptions import InvalidResponseHeader
from ccai.webworks.routing.response import Response as FrameworkResponse
from ccai.webworks.routing.response import StreamingResponse


# =============================================================================
# Test Helpers and Generators
# =============================================================================

def generate_random_string(min_length: int = 1, max_length: int = 50) -> str:
    """
        Generate a random alphanumeric string.
    """
    length = random.randint(min_length, max_length)
    chars = string.ascii_letters + string.digits
    rtnval = "".join(random.choice(chars) for _ in range(length))
    return rtnval


def generate_random_status_code() -> int:
    """
        Generate a random HTTP status code.
    """
    # Use common status codes
    common_codes = [200, 201, 204, 301, 302, 400, 401, 403, 404, 500, 502, 503]
    rtnval = random.choice(common_codes)
    return rtnval


def generate_random_headers() -> Dict[str, str]:
    """
        Generate random HTTP response headers.
    """
    num_headers = random.randint(0, 10)
    headers: Dict[str, str] = {}
    common_headers = [
        "X-Request-Id", "X-Correlation-Id", "Cache-Control",
        "ETag", "Last-Modified", "X-Custom-Header",
    ]
    
    for _ in range(num_headers):
        if random.random() < 0.7 and len(common_headers) > 0:
            header_name = random.choice(common_headers)
        else:
            header_name = "X-" + generate_random_string(3, 15).title()
        header_value = generate_random_string(1, 100)
        headers[header_name] = header_value
    
    return headers


def generate_random_body() -> bytes:
    """
        Generate a random response body.
    """
    if random.random() < 0.3:
        rtnval = b""
    else:
        length = random.randint(1, 1000)
        rtnval = bytes(random.randint(32, 126) for _ in range(length))
    
    return rtnval


def generate_random_content_type() -> str:
    """
        Generate a random content type.
    """
    content_types = [
        "application/json",
        "text/plain",
        "text/html",
        "application/xml",
        "application/octet-stream",
    ]
    rtnval = random.choice(content_types)
    return rtnval


def generate_random_response() -> Response:
    """
        Generate a random valid Response object.
    """
    status_code = generate_random_status_code()
    headers = generate_random_headers()
    body = generate_random_body()
    
    # Optionally set content type
    content_type = None
    if len(body) > 0 and random.random() < 0.7:
        content_type = generate_random_content_type()
    
    rtnval = Response(
        status_code=status_code,
        headers=headers,
        body=body,
        content_type=content_type
    )
    return rtnval


# =============================================================================
# Unit Tests for Response
# =============================================================================

def test_response_default_values():
    """
        Test that Response has correct default values.
    """
    response = Response()
    
    if response.status_code != 200:
        errmsg = f"Expected default status_code 200, got {response.status_code}"
        raise AssertionError(errmsg)
    
    if response.body != b"":
        errmsg = f"Expected empty body, got {response.body}"
        raise AssertionError(errmsg)
    
    if len(response.headers) != 0:
        errmsg = f"Expected empty headers, got {response.headers}"
        raise AssertionError(errmsg)
    
    return


def test_response_with_string_body():
    """
        Test that Response encodes string body to bytes.
    """
    response = Response(body="Hello, World!")
    
    expected = b"Hello, World!"
    if response.body != expected:
        errmsg = f"Expected body {expected}, got {response.body}"
        raise AssertionError(errmsg)
    
    return


def test_response_with_bytes_body():
    """
        Test that Response preserves bytes body.
    """
    body_content = b"Binary content"
    response = Response(body=body_content)
    
    if response.body != body_content:
        errmsg = f"Expected body {body_content}, got {response.body}"
        raise AssertionError(errmsg)
    
    return


def test_response_content_type_in_headers():
    """
        Test that content_type is added to headers.
    """
    response = Response(content_type="application/json")
    
    if "Content-Type" not in response.headers:
        errmsg = "Expected Content-Type in headers"
        raise AssertionError(errmsg)
    
    if response.headers["Content-Type"] != "application/json":
        errmsg = f"Expected Content-Type 'application/json', got '{response.headers['Content-Type']}'"
        raise AssertionError(errmsg)
    
    return


def test_response_set_header():
    """
        Test that set_header adds headers correctly.
    """
    response = Response()
    response.set_header("X-Custom", "value")
    
    if "X-Custom" not in response.headers:
        errmsg = "Expected X-Custom in headers"
        raise AssertionError(errmsg)
    
    if response.headers["X-Custom"] != "value":
        errmsg = f"Expected X-Custom 'value', got '{response.headers['X-Custom']}'"
        raise AssertionError(errmsg)
    
    return


def test_response_get_header():
    """
        Test that get_header retrieves headers correctly.
    """
    response = Response(headers={"X-Custom": "value"})
    
    result = response.get_header("X-Custom")
    if result != "value":
        errmsg = f"Expected 'value', got '{result}'"
        raise AssertionError(errmsg)
    
    return


def test_response_get_header_default():
    """
        Test that get_header returns default for missing headers.
    """
    response = Response()
    
    result = response.get_header("X-Missing", "default")
    if result != "default":
        errmsg = f"Expected 'default', got '{result}'"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for ResponseBuilder
# =============================================================================

def test_format_status_with_known_code():
    """
        Test that format_status returns correct status string for known codes.
    """
    builder = ResponseBuilder()
    
    result = builder.format_status(200)
    
    expected = "200 OK"
    if result != expected:
        errmsg = f"Expected '{expected}', got '{result}'"
        raise AssertionError(errmsg)
    
    return


def test_format_status_with_custom_reason():
    """
        Test that format_status uses custom reason phrase.
    """
    builder = ResponseBuilder()
    
    result = builder.format_status(200, "Custom Reason")
    
    expected = "200 Custom Reason"
    if result != expected:
        errmsg = f"Expected '{expected}', got '{result}'"
        raise AssertionError(errmsg)
    
    return


def test_format_status_with_unknown_code():
    """
        Test that format_status handles unknown status codes.
    """
    builder = ResponseBuilder()
    
    result = builder.format_status(999)
    
    expected = "999 Unknown"
    if result != expected:
        errmsg = f"Expected '{expected}', got '{result}'"
        raise AssertionError(errmsg)
    
    return


def test_is_hop_by_hop_returns_true_for_hop_headers():
    """
        Test that is_hop_by_hop returns True for hop-by-hop headers.
    """
    builder = ResponseBuilder()
    
    hop_headers = [
        "Connection", "Keep-Alive", "Proxy-Authenticate",
        "Proxy-Authorization", "TE", "Trailers",
        "Transfer-Encoding", "Upgrade",
    ]
    
    for header in hop_headers:
        result = builder.is_hop_by_hop(header)
        if result is not True:
            errmsg = f"Expected True for hop-by-hop header '{header}', got {result}"
            raise AssertionError(errmsg)
    
    return


def test_is_hop_by_hop_returns_false_for_regular_headers():
    """
        Test that is_hop_by_hop returns False for regular headers.
    """
    builder = ResponseBuilder()
    
    regular_headers = [
        "Content-Type", "Content-Length", "Cache-Control",
        "X-Custom-Header", "Accept", "Authorization",
    ]
    
    for header in regular_headers:
        result = builder.is_hop_by_hop(header)
        if result is not False:
            errmsg = f"Expected False for regular header '{header}', got {result}"
            raise AssertionError(errmsg)
    
    return


def test_format_headers_filters_hop_by_hop():
    """
        Test that format_headers filters out hop-by-hop headers.
    """
    builder = ResponseBuilder()
    
    headers = {
        "Content-Type": "application/json",
        "Connection": "keep-alive",
        "X-Custom": "value",
        "Transfer-Encoding": "chunked",
    }
    
    result = builder.format_headers(headers)
    
    # Check that hop-by-hop headers are filtered
    result_names = [name for name, _ in result]
    
    if "Connection" in result_names:
        errmsg = "Expected Connection header to be filtered"
        raise AssertionError(errmsg)
    
    if "Transfer-Encoding" in result_names:
        errmsg = "Expected Transfer-Encoding header to be filtered"
        raise AssertionError(errmsg)
    
    # Check that regular headers are preserved
    if "Content-Type" not in result_names:
        errmsg = "Expected Content-Type header to be preserved"
        raise AssertionError(errmsg)
    
    if "X-Custom" not in result_names:
        errmsg = "Expected X-Custom header to be preserved"
        raise AssertionError(errmsg)
    
    return


def test_format_headers_adds_content_length():
    """
        Test that format_headers adds Content-Length when body_length is provided.
    """
    builder = ResponseBuilder()
    
    headers: Dict[str, str] = {}
    
    result = builder.format_headers(headers, body_length=100)
    
    result_dict = dict(result)
    
    if "Content-Length" not in result_dict:
        errmsg = "Expected Content-Length header to be added"
        raise AssertionError(errmsg)
    
    if result_dict["Content-Length"] != "100":
        errmsg = f"Expected Content-Length '100', got '{result_dict['Content-Length']}'"
        raise AssertionError(errmsg)
    
    return


def test_format_headers_adds_content_type():
    """
        Test that format_headers adds Content-Type when provided.
    """
    builder = ResponseBuilder()
    
    headers: Dict[str, str] = {}
    
    result = builder.format_headers(headers, content_type="application/json")
    
    result_dict = dict(result)
    
    if "Content-Type" not in result_dict:
        errmsg = "Expected Content-Type header to be added"
        raise AssertionError(errmsg)
    
    if result_dict["Content-Type"] != "application/json":
        errmsg = f"Expected Content-Type 'application/json', got '{result_dict['Content-Type']}'"
        raise AssertionError(errmsg)
    
    return


def test_format_headers_does_not_duplicate_content_type():
    """
        Test that format_headers does not duplicate Content-Type.
    """
    builder = ResponseBuilder()
    
    headers = {"Content-Type": "text/html"}
    
    result = builder.format_headers(headers, content_type="application/json")
    
    # Count Content-Type occurrences
    content_type_count = sum(1 for name, _ in result if name.lower() == "content-type")
    
    if content_type_count != 1:
        errmsg = f"Expected 1 Content-Type header, got {content_type_count}"
        raise AssertionError(errmsg)
    
    return


def test_build_returns_correct_tuple():
    """
        Test that build returns (status, headers, body_iterator) tuple.
    """
    builder = ResponseBuilder()
    response = Response(
        status_code=200,
        body=b"Hello",
        content_type="text/plain"
    )
    
    status, headers, body_iter = builder.build(response)
    
    # Check status format
    if not status.startswith("200"):
        errmsg = f"Expected status to start with '200', got '{status}'"
        raise AssertionError(errmsg)
    
    # Check headers is list of tuples
    if not isinstance(headers, list):
        errmsg = f"Expected headers to be list, got {type(headers)}"
        raise AssertionError(errmsg)
    
    for item in headers:
        if not isinstance(item, tuple):
            errmsg = f"Expected header item to be tuple, got {type(item)}"
            raise AssertionError(errmsg)
        if len(item) != 2:
            errmsg = f"Expected header tuple length 2, got {len(item)}"
            raise AssertionError(errmsg)
    
    # Check body iterator yields bytes
    body_content = b"".join(body_iter)
    if body_content != b"Hello":
        errmsg = f"Expected body 'Hello', got '{body_content}'"
        raise AssertionError(errmsg)
    
    return


def test_build_sets_content_length_for_body():
    """
        Test that build sets Content-Length for responses with body.
    """
    builder = ResponseBuilder()
    response = Response(
        status_code=200,
        body=b"Hello, World!"
    )
    
    _, headers, _ = builder.build(response)
    
    headers_dict = dict(headers)
    
    if "Content-Length" not in headers_dict:
        errmsg = "Expected Content-Length header"
        raise AssertionError(errmsg)
    
    expected_length = str(len(b"Hello, World!"))
    if headers_dict["Content-Length"] != expected_length:
        errmsg = f"Expected Content-Length '{expected_length}', got '{headers_dict['Content-Length']}'"
        raise AssertionError(errmsg)
    
    return


def test_build_sets_default_content_type_for_body():
    """
        Test that build sets default Content-Type for responses with body.
    """
    builder = ResponseBuilder()
    response = Response(
        status_code=200,
        body=b"Hello"
    )
    
    _, headers, _ = builder.build(response)
    
    headers_dict = dict(headers)
    
    if "Content-Type" not in headers_dict:
        errmsg = "Expected Content-Type header"
        raise AssertionError(errmsg)
    
    return


def test_build_empty_body_no_content_headers():
    """
        Test that build does not set Content-Length for empty body.
    """
    builder = ResponseBuilder()
    response = Response(status_code=204)
    
    _, headers, body_iter = builder.build(response)
    
    headers_dict = dict(headers)
    
    # Empty body should not have Content-Length
    if "Content-Length" in headers_dict:
        errmsg = "Expected no Content-Length header for empty body"
        raise AssertionError(errmsg)
    
    # Body iterator should be empty
    body_content = list(body_iter)
    if len(body_content) != 0:
        errmsg = f"Expected empty body iterator, got {len(body_content)} items"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Property-Based Tests for ResponseBuilder
# =============================================================================

def test_property_response_formatting_correctness():
    """
        Property test: Response Formatting Correctness
        
        For any valid Response object with status_code, headers, and body,
        converting to WSGI format SHALL produce a status string matching
        "NNN Reason", headers as a list of (name, value) tuples excluding
        hop-by-hop headers, and body content encoded as bytes with correct
        Content-Length when body size is known.
        
        **Feature: wsgi-layer, Property 3: Response Formatting Correctness**
        **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.7**
    """
    builder = ResponseBuilder()
    
    # Run 100 iterations with random Response objects
    num_iterations = 100
    
    for iteration in range(num_iterations):
        # Generate random response
        response = generate_random_response()
        
        # Build WSGI format
        status, headers, body_iter = builder.build(response)
        
        # Property 1: Status string matches "NNN Reason" format (Requirement 3.1)
        status_parts = status.split(" ", 1)
        if len(status_parts) < 2:
            errmsg = f"Iteration {iteration}: Status '{status}' does not match 'NNN Reason' format"
            raise AssertionError(errmsg)
        
        status_code_str = status_parts[0]
        if not status_code_str.isdigit():
            errmsg = f"Iteration {iteration}: Status code '{status_code_str}' is not numeric"
            raise AssertionError(errmsg)
        
        if int(status_code_str) != response.status_code:
            errmsg = f"Iteration {iteration}: Status code mismatch. Expected {response.status_code}, got {status_code_str}"
            raise AssertionError(errmsg)
        
        # Property 2: Headers is list of (name, value) tuples (Requirement 3.2)
        if not isinstance(headers, list):
            errmsg = f"Iteration {iteration}: Headers is not a list"
            raise AssertionError(errmsg)
        
        for idx, header in enumerate(headers):
            if not isinstance(header, tuple):
                errmsg = f"Iteration {iteration}: Header {idx} is not a tuple"
                raise AssertionError(errmsg)
            
            if len(header) != 2:
                errmsg = f"Iteration {iteration}: Header {idx} tuple length is {len(header)}, expected 2"
                raise AssertionError(errmsg)
            
            name, value = header
            if not isinstance(name, str):
                errmsg = f"Iteration {iteration}: Header {idx} name is not a string"
                raise AssertionError(errmsg)
            
            if not isinstance(value, str):
                errmsg = f"Iteration {iteration}: Header {idx} value is not a string"
                raise AssertionError(errmsg)
        
        # Property 3: No hop-by-hop headers in output (Requirement 3.3)
        hop_by_hop = {"connection", "keep-alive", "proxy-authenticate",
                      "proxy-authorization", "te", "trailers",
                      "transfer-encoding", "upgrade"}
        
        for name, _ in headers:
            if name.lower() in hop_by_hop:
                errmsg = f"Iteration {iteration}: Hop-by-hop header '{name}' found in output"
                raise AssertionError(errmsg)
        
        # Property 4: Content-Type set for responses with body (Requirement 3.4)
        body_content = b"".join(body_iter)
        headers_dict = {name.lower(): value for name, value in headers}
        
        if len(body_content) > 0:
            if "content-type" not in headers_dict:
                errmsg = f"Iteration {iteration}: Content-Type not set for response with body"
                raise AssertionError(errmsg)
        
        # Property 5: Content-Length correct when body size is known (Requirement 3.5)
        if len(body_content) > 0:
            if "content-length" not in headers_dict:
                errmsg = f"Iteration {iteration}: Content-Length not set for response with body"
                raise AssertionError(errmsg)
            
            expected_length = str(len(body_content))
            if headers_dict["content-length"] != expected_length:
                errmsg = f"Iteration {iteration}: Content-Length mismatch. Expected {expected_length}, got {headers_dict['content-length']}"
                raise AssertionError(errmsg)
        
        # Property 6: Body content is bytes (Requirement 3.7)
        if not isinstance(body_content, bytes):
            errmsg = f"Iteration {iteration}: Body content is not bytes"
            raise AssertionError(errmsg)
        
        # Property 7: Body content matches original response body. A 204
        # or 304 response never carries a body, whatever the response holds.
        if response.status_code in (204, 304):
            expected_body = b""
        else:
            expected_body = response.body
        
        if body_content != expected_body:
            errmsg = f"Iteration {iteration}: Body content mismatch. Expected {len(expected_body)} bytes, got {len(body_content)} bytes"
            raise AssertionError(errmsg)
    
    return


# =============================================================================
# Tests for Content-Length, header validation and framework responses
# =============================================================================

def test_build_sets_content_length_zero_for_empty_body():
    """
        Test that build states a Content-Length of zero for a response without a body.
    """
    builder = ResponseBuilder()
    response = Response(status_code=302, headers={"Location": "/next"})
    
    _, headers, body_iter = builder.build(response)
    
    headers_dict = dict(headers)
    
    if headers_dict.get("Content-Length") != "0":
        errmsg = f"Expected Content-Length '0' for an empty body, got {headers_dict.get('Content-Length')!r}"
        raise AssertionError(errmsg)
    
    if "Content-Type" in headers_dict:
        errmsg = "Expected no Content-Type header for an empty body"
        raise AssertionError(errmsg)
    
    return


def test_build_sets_no_content_length_for_304():
    """
        Test that build does not state a Content-Length for a 304 response.
    """
    builder = ResponseBuilder()
    response = Response(status_code=304)
    
    _, headers, _ = builder.build(response)
    
    if "Content-Length" in dict(headers):
        errmsg = "Expected no Content-Length header for a 304 response"
        raise AssertionError(errmsg)
    
    return


def test_build_strips_body_of_204_response():
    """
        Test that build does not pass on a body given to a 204 response.
    """
    builder = ResponseBuilder()
    response = Response(status_code=204, body=b"must not be sent")
    
    _, _, body_iter = builder.build(response)
    
    body_content = b"".join(body_iter)
    
    if body_content != b"":
        errmsg = f"Expected no body for a 204 response, got {body_content!r}"
        raise AssertionError(errmsg)
    
    return


def test_build_refuses_header_value_with_line_break():
    """
        Test that build refuses a header that would split the response.
    """
    builder = ResponseBuilder()
    response = Response(status_code=302, headers={"Location": "/x\r\nSet-Cookie: sid=evil"})
    
    raised = False
    try:
        builder.build(response)
    except InvalidResponseHeader:
        raised = True
    
    if not raised:
        errmsg = "Expected InvalidResponseHeader for a header value containing CRLF"
        raise AssertionError(errmsg)
    
    return


def test_format_headers_refuses_header_name_with_line_break():
    """
        Test that format_headers refuses a header name that contains a line break.
    """
    builder = ResponseBuilder()
    
    raised = False
    try:
        builder.format_headers({"X-A\r\nX-B": "value"})
    except InvalidResponseHeader:
        raised = True
    
    if not raised:
        errmsg = "Expected InvalidResponseHeader for a header name containing CRLF"
        raise AssertionError(errmsg)
    
    return


def test_format_header_list_keeps_repeated_headers():
    """
        Test that a header given more than once is kept once per value.
    """
    builder = ResponseBuilder()
    
    result = builder.format_header_list([("Set-Cookie", "a=1"), ("Set-Cookie", "b=2")])
    
    if result != [("Set-Cookie", "a=1"), ("Set-Cookie", "b=2")]:
        errmsg = f"Expected both Set-Cookie headers, got {result}"
        raise AssertionError(errmsg)
    
    return


def test_build_accepts_framework_response_with_body():
    """
        Test that build converts the response class of the framework.
    """
    builder = ResponseBuilder()
    response = FrameworkResponse(status_code=200, headers={"Content-Type": "text/html"}, body=b"<p>hi</p>")
    
    status, headers, body_iter = builder.build(response)
    
    headers_dict = dict(headers)
    
    if status != "200 OK":
        errmsg = f"Expected status '200 OK', got {status!r}"
        raise AssertionError(errmsg)
    
    if headers_dict.get("Content-Type") != "text/html":
        errmsg = f"Expected Content-Type 'text/html', got {headers_dict.get('Content-Type')!r}"
        raise AssertionError(errmsg)
    
    if b"".join(body_iter) != b"<p>hi</p>":
        errmsg = "Expected the body of the framework response"
        raise AssertionError(errmsg)
    
    return


def test_build_includes_cookies_of_framework_response():
    """
        Test that every cookie of a framework response becomes a Set-Cookie header.
    """
    builder = ResponseBuilder()
    response = FrameworkResponse(status_code=200, body=b"ok")
    response.set_cookie("session", "abc")
    response.set_cookie("theme", "dark")
    
    _, headers, _ = builder.build(response)
    
    cookie_headers = [value for name, value in headers if name == "Set-Cookie"]
    
    if len(cookie_headers) != 2:
        errmsg = f"Expected two Set-Cookie headers, got {cookie_headers}"
        raise AssertionError(errmsg)
    
    return


def test_build_passes_streaming_response_on_as_iterator():
    """
        Test that a streaming response is not collected and gets no Content-Length.
    """
    builder = ResponseBuilder()
    produced = []
    
    def generate():
        for chunk in (b"one", b"two"):
            produced.append(chunk)
            yield chunk
    
    response = StreamingResponse(generate(), media_type="text/plain")
    
    _, headers, body_iter = builder.build(response)
    
    if len(produced) != 0:
        errmsg = f"Expected the stream not to be read by build, it produced {produced}"
        raise AssertionError(errmsg)
    
    if "Content-Length" in dict(headers):
        errmsg = "Expected no Content-Length header for a streaming response"
        raise AssertionError(errmsg)
    
    if b"".join(body_iter) != b"onetwo":
        errmsg = "Expected the chunks of the stream from the body iterator"
        raise AssertionError(errmsg)
    
    return
