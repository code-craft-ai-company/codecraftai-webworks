"""
    Tests for the HTTP/1.1 protocol handler.

    This module contains property-based tests and unit tests for the
    :class:`HTTPProtocolHandler` class, covering HTTP request parsing,
    ASGI scope construction, receive/send callables, response
    serialization, keep-alive logic, and error handling.
"""

import asyncio
import random
import string

from ccai.webworks.devexp.server.httpprotocolhandler import (
    HTTPProtocolHandler,
    _ParseState,
    _get_reason_phrase,
    MAX_REQUEST_LINE_BYTES,
    MAX_HEADER_BLOCK_BYTES,
    LINE_TERMINATOR,
    HEADER_TERMINATOR,
)


# =============================================================================
# Test Helpers
# =============================================================================

# Valid HTTP methods for random generation
_HTTP_METHODS = ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"]

# Valid HTTP versions for random generation
_HTTP_VERSIONS = ["HTTP/1.0", "HTTP/1.1"]

# Safe characters for path generation (ASCII printable, no spaces or control chars)
_PATH_CHARS = string.ascii_letters + string.digits + "/-_.~"

# Safe characters for query string values
_QUERY_CHARS = string.ascii_letters + string.digits + "-_.~"

# Safe characters for header names (token chars per RFC 7230)
_HEADER_NAME_CHARS = string.ascii_letters + string.digits + "-_"

# Safe characters for header values (visible ASCII + space + tab)
_HEADER_VALUE_CHARS = string.ascii_letters + string.digits + " -_.~:;,/=+!@#$%^&*()"


def _random_method():
    """
        Return a random HTTP method string.
    """
    return random.choice(_HTTP_METHODS)


def _random_path():
    """
        Return a random URL path string starting with '/'.
    """
    length = random.randint(1, 50)
    path = "/" + "".join(random.choice(_PATH_CHARS) for _ in range(length))
    return path


def _random_version():
    """
        Return a random HTTP version string.
    """
    return random.choice(_HTTP_VERSIONS)


def _random_header_name():
    """
        Return a random header name string with mixed casing.
    """
    length = random.randint(1, 20)
    name = "".join(random.choice(_HEADER_NAME_CHARS) for _ in range(length))
    # Ensure at least one character and mixed casing
    if len(name) > 1:
        name = name[0].upper() + name[1:]
    return name


def _random_header_value():
    """
        Return a random header value string.
    """
    length = random.randint(1, 40)
    value = "".join(random.choice(_HEADER_VALUE_CHARS) for _ in range(length))
    return value


def _random_headers(count=None):
    """
        Return a list of random (name, value) header tuples.
    """
    if count is None:
        count = random.randint(0, 5)
    headers = []
    for _ in range(count):
        name = _random_header_name()
        value = _random_header_value()
        headers.append((name, value))
    return headers


def _random_query_string():
    """
        Return a random query string (without leading '?').
    """
    param_count = random.randint(1, 4)
    params = []
    for _ in range(param_count):
        key_len = random.randint(1, 10)
        val_len = random.randint(1, 10)
        key = "".join(random.choice(_QUERY_CHARS) for _ in range(key_len))
        val = "".join(random.choice(_QUERY_CHARS) for _ in range(val_len))
        params.append("{}={}".format(key, val))
    return "&".join(params)


def _random_body(max_size=256):
    """
        Return random body bytes.
    """
    length = random.randint(0, max_size)
    return bytes(random.randint(0, 255) for _ in range(length))


def _create_handler(app=None, debug=False, server_host="127.0.0.1", server_port=8000):
    """
        Create an HTTPProtocolHandler with a mock app and transport.
    """
    if app is None:
        async def _noop_app(scope, receive, send):
            return
        app = _noop_app

    handler = HTTPProtocolHandler(
        app=app,
        server_host=server_host,
        server_port=server_port,
        debug=debug,
    )
    return handler


class _MockTransport:
    """
        A mock asyncio transport that captures written bytes.
    """

    def __init__(self):
        self._data = bytearray()
        self._closed = False
        self._extra = {}

    def write(self, data):
        self._data.extend(data)

    def close(self):
        self._closed = True

    def get_extra_info(self, key, default=None):
        return self._extra.get(key, default)

    @property
    def written_data(self):
        return bytes(self._data)

    @property
    def is_closed(self):
        return self._closed


def _connect_handler(handler, client_host="192.168.1.1", client_port=54321):
    """
        Simulate a connection by calling connection_made with a mock transport.
    """
    transport = _MockTransport()
    transport._extra["peername"] = (client_host, client_port)
    handler.connection_made(transport)
    return transport


def _serialize_request_line(method, target, version):
    """
        Serialize an HTTP request line to bytes.
    """
    line = "{} {} {}".format(method, target, version)
    return line.encode("ascii")


def _serialize_headers(headers):
    """
        Serialize a list of (name, value) header tuples to bytes.
        Headers are string tuples.
    """
    parts = []
    for name, value in headers:
        parts.append("{}: {}".format(name, value).encode("ascii"))
    return LINE_TERMINATOR.join(parts)


def _build_raw_request(method, target, version, headers, body=b""):
    """
        Build a complete raw HTTP request as bytes.
    """
    request_line = _serialize_request_line(method, target, version)
    header_block = _serialize_headers(headers)

    parts = [request_line, LINE_TERMINATOR]
    if header_block:
        parts.append(header_block)
    parts.append(HEADER_TERMINATOR)
    parts.append(body)

    return b"".join(parts)


def _encode_chunked(data):
    """
        Encode bytes as HTTP chunked transfer encoding.
    """
    if len(data) == 0:
        return b"0\r\n\r\n"

    parts = []
    offset = 0

    while offset < len(data):
        chunk_size = random.randint(1, max(1, len(data) - offset))
        chunk = data[offset:offset + chunk_size]
        size_hex = format(len(chunk), "x")
        parts.append(size_hex.encode("ascii"))
        parts.append(LINE_TERMINATOR)
        parts.append(chunk)
        parts.append(LINE_TERMINATOR)
        offset += chunk_size

    # Terminal chunk
    parts.append(b"0")
    parts.append(LINE_TERMINATOR)

    return b"".join(parts)


def _run_async(coro):
    """
        Run an async coroutine synchronously.

        This built a loop with new_event_loop() but never made it the current
        one, so anything inside the coroutine that asked asyncio for the
        running loop found none and raised. Whether that happened depended on
        which test had run first and left a loop installed, which is why
        these failed only in a full run. asyncio.run installs the loop it
        creates and tears it down afterwards.
    """
    return asyncio.run(coro)


# =============================================================================
# Property 1: HTTP Request Parsing Round Trip
# Validates: Requirements 2.1, 2.2
# =============================================================================

def test_property_parse_request_round_trip():
    """
        Property 1: HTTP Request Parsing Round Trip.
        Feature: development-server

        **Validates: Requirements 2.1, 2.2**

        For any valid HTTP method, path, version, and headers, serializing
        to raw bytes and parsing with _parse_request_line and _parse_headers
        should recover the original values.
    """
    handler = _create_handler()

    for _ in range(100):
        method = _random_method()
        path = _random_path()
        version = _random_version()
        headers = _random_headers()

        # Serialize and parse request line
        request_line_bytes = _serialize_request_line(method, path, version)
        parsed = handler._parse_request_line(request_line_bytes)

        if parsed is None:
            errmsg = "Failed to parse request line: {}".format(request_line_bytes)
            raise AssertionError(errmsg)

        parsed_method, parsed_target, parsed_version = parsed

        if parsed_method != method:
            errmsg = "Method mismatch: expected '{}', got '{}'".format(method, parsed_method)
            raise AssertionError(errmsg)

        if parsed_target != path:
            errmsg = "Target mismatch: expected '{}', got '{}'".format(path, parsed_target)
            raise AssertionError(errmsg)

        if parsed_version != version:
            errmsg = "Version mismatch: expected '{}', got '{}'".format(version, parsed_version)
            raise AssertionError(errmsg)

        # Serialize and parse headers
        header_block_bytes = _serialize_headers(headers)
        parsed_headers = handler._parse_headers(header_block_bytes)

        if len(parsed_headers) != len(headers):
            errmsg = "Header count mismatch: expected {}, got {}".format(
                len(headers), len(parsed_headers)
            )
            raise AssertionError(errmsg)

        for idx in range(len(headers)):
            orig_name, orig_value = headers[idx]
            parsed_name, parsed_value = parsed_headers[idx]

            # _parse_headers lowercases names and strips whitespace from values
            expected_name = orig_name.strip().lower().encode("ascii")
            expected_value = orig_value.strip().encode("ascii")

            if parsed_name != expected_name:
                errmsg = "Header name mismatch at index {}: expected {}, got {}".format(
                    idx, expected_name, parsed_name
                )
                raise AssertionError(errmsg)

            if parsed_value != expected_value:
                errmsg = "Header value mismatch at index {}: expected {}, got {}".format(
                    idx, expected_value, parsed_value
                )
                raise AssertionError(errmsg)

    return


# =============================================================================
# Property 2: Content-Length Body Integrity
# Validates: Requirements 2.3
# =============================================================================

def test_property_content_length_body():
    """
        Property 2: Content-Length Body Integrity.
        Feature: development-server

        **Validates: Requirements 2.3**

        For any body bytes with a matching Content-Length header, the
        handler should parse a body whose length and content match.
    """
    for _ in range(100):
        body = _random_body(max_size=512)
        content_length = len(body)

        method = _random_method()
        path = _random_path()
        version = _random_version()

        headers = [("Content-Length", str(content_length))]
        raw_request = _build_raw_request(method, path, version, headers, body)

        handler = _create_handler()
        transport = _connect_handler(handler)

        handler.data_received(raw_request)

        if handler._body != body:
            errmsg = "Body mismatch: expected {} bytes, got {} bytes".format(
                len(body), len(handler._body)
            )
            raise AssertionError(errmsg)

        if len(handler._body) != content_length:
            errmsg = "Body length mismatch: expected {}, got {}".format(
                content_length, len(handler._body)
            )
            raise AssertionError(errmsg)

    return


# =============================================================================
# Property 3: Chunked Transfer Decoding Round Trip
# Validates: Requirements 2.4
# =============================================================================

def test_property_chunked_round_trip():
    """
        Property 3: Chunked Transfer Decoding Round Trip.
        Feature: development-server

        **Validates: Requirements 2.4**

        For any byte sequence, encoding as chunked transfer and decoding
        should produce the original byte sequence.
    """
    handler = _create_handler()

    for _ in range(100):
        original = _random_body(max_size=512)
        encoded = _encode_chunked(original)
        decoded = handler._decode_chunked(encoded)

        if decoded is None:
            errmsg = "Chunked decode returned None for {} bytes of input".format(
                len(original)
            )
            raise AssertionError(errmsg)

        if decoded != original:
            errmsg = "Chunked round trip failed: expected {} bytes, got {} bytes".format(
                len(original), len(decoded)
            )
            raise AssertionError(errmsg)

    return


# =============================================================================
# Property 4: ASGI Scope Completeness and Type Correctness
# Validates: Requirements 1.5, 3.1, 3.2, 3.4, 3.6, 3.7
# =============================================================================

def test_property_scope_completeness():
    """
        Property 4: ASGI Scope Completeness and Type Correctness.
        Feature: development-server

        **Validates: Requirements 1.5, 3.1, 3.2, 3.4, 3.6, 3.7**

        For any valid request parameters, the constructed ASGI scope
        should contain all required keys with correct types.
    """
    for _ in range(100):
        method = _random_method()
        path = _random_path()
        query = _random_query_string()
        version = _random_version()
        headers = _random_headers()

        server_host = "127.0.0.1"
        server_port = random.randint(1024, 65535)
        client_host = "192.168.1.{}".format(random.randint(1, 254))
        client_port = random.randint(1024, 65535)

        handler = _create_handler(server_host=server_host, server_port=server_port)
        handler._client_host = client_host
        handler._client_port = client_port

        # Build headers as byte tuples (as _parse_headers would produce)
        byte_headers = [(n.lower().encode("ascii"), v.encode("ascii")) for n, v in headers]

        scope = handler._build_scope(method, path, query, version, byte_headers)

        # Check all required keys are present
        required_keys = [
            "type", "asgi", "http_version", "method", "path",
            "raw_path", "root_path", "scheme", "query_string",
            "headers", "server", "client",
        ]

        for key in required_keys:
            if key not in scope:
                errmsg = "Missing required key '{}' in ASGI scope".format(key)
                raise AssertionError(errmsg)

        # Check type is "http"
        if scope["type"] != "http":
            errmsg = "Expected type 'http', got '{}'".format(scope["type"])
            raise AssertionError(errmsg)

        # Check asgi version
        if scope["asgi"] != {"version": "3.0"}:
            errmsg = "Expected asgi {{'version': '3.0'}}, got {}".format(scope["asgi"])
            raise AssertionError(errmsg)

        # Check path is str
        if not isinstance(scope["path"], str):
            errmsg = "Expected path to be str, got {}".format(type(scope["path"]))
            raise AssertionError(errmsg)

        # Check query_string is bytes
        if not isinstance(scope["query_string"], bytes):
            errmsg = "Expected query_string to be bytes, got {}".format(type(scope["query_string"]))
            raise AssertionError(errmsg)

        # Check raw_path is bytes
        if not isinstance(scope["raw_path"], bytes):
            errmsg = "Expected raw_path to be bytes, got {}".format(type(scope["raw_path"]))
            raise AssertionError(errmsg)

        # Check server is [str, int]
        server = scope["server"]
        if not isinstance(server, list) or len(server) != 2:
            errmsg = "Expected server to be a 2-element list, got {}".format(server)
            raise AssertionError(errmsg)
        if not isinstance(server[0], str):
            errmsg = "Expected server[0] to be str, got {}".format(type(server[0]))
            raise AssertionError(errmsg)
        if not isinstance(server[1], int):
            errmsg = "Expected server[1] to be int, got {}".format(type(server[1]))
            raise AssertionError(errmsg)

        # Check client is [str, int]
        client = scope["client"]
        if not isinstance(client, list) or len(client) != 2:
            errmsg = "Expected client to be a 2-element list, got {}".format(client)
            raise AssertionError(errmsg)
        if not isinstance(client[0], str):
            errmsg = "Expected client[0] to be str, got {}".format(type(client[0]))
            raise AssertionError(errmsg)
        if not isinstance(client[1], int):
            errmsg = "Expected client[1] to be int, got {}".format(type(client[1]))
            raise AssertionError(errmsg)

        # Check server and client values
        if server[0] != server_host:
            errmsg = "Expected server host '{}', got '{}'".format(server_host, server[0])
            raise AssertionError(errmsg)
        if server[1] != server_port:
            errmsg = "Expected server port {}, got {}".format(server_port, server[1])
            raise AssertionError(errmsg)
        if client[0] != client_host:
            errmsg = "Expected client host '{}', got '{}'".format(client_host, client[0])
            raise AssertionError(errmsg)
        if client[1] != client_port:
            errmsg = "Expected client port {}, got {}".format(client_port, client[1])
            raise AssertionError(errmsg)

        # Check method is str
        if not isinstance(scope["method"], str):
            errmsg = "Expected method to be str, got {}".format(type(scope["method"]))
            raise AssertionError(errmsg)

    return


# =============================================================================
# Property 5: Query String Separation
# Validates: Requirements 3.3
# =============================================================================

def test_property_query_string_split():
    """
        Property 5: Query String Separation.
        Feature: development-server

        **Validates: Requirements 3.3**

        For any path with a query string containing '?', the scope
        should have path as the portion before the first '?' and
        query_string as bytes of the portion after.
    """
    for _ in range(100):
        base_path = _random_path()
        query = _random_query_string()
        full_target = "{}?{}".format(base_path, query)

        handler = _create_handler()
        handler._client_host = "127.0.0.1"
        handler._client_port = 12345

        byte_headers = []

        scope = handler._build_scope(
            method="GET",
            path=base_path,
            query=query,
            version="HTTP/1.1",
            headers=byte_headers,
        )

        # path should be the portion before '?'
        expected_path = base_path
        if scope["path"] != expected_path:
            errmsg = "Expected path '{}', got '{}'".format(expected_path, scope["path"])
            raise AssertionError(errmsg)

        # query_string should be bytes of the portion after '?'
        expected_query = query.encode("ascii")
        if scope["query_string"] != expected_query:
            errmsg = "Expected query_string {}, got {}".format(
                expected_query, scope["query_string"]
            )
            raise AssertionError(errmsg)

    return


# =============================================================================
# Property 6: Header Lowercase Normalization
# Validates: Requirements 3.5
# =============================================================================

def test_property_header_lowercase():
    """
        Property 6: Header Lowercase Normalization.
        Feature: development-server

        **Validates: Requirements 3.5**

        For any headers with mixed casing, the scope headers should
        have all names as lowercase bytes and values preserved.
    """
    for _ in range(100):
        headers = _random_headers(count=random.randint(1, 8))

        handler = _create_handler()
        handler._client_host = "127.0.0.1"
        handler._client_port = 12345

        # Simulate what _parse_headers does: lowercase names
        byte_headers = [(n.lower().encode("ascii"), v.encode("ascii")) for n, v in headers]

        scope = handler._build_scope(
            method="GET",
            path="/test",
            query="",
            version="HTTP/1.1",
            headers=byte_headers,
        )

        scope_headers = scope["headers"]

        if len(scope_headers) != len(headers):
            errmsg = "Header count mismatch: expected {}, got {}".format(
                len(headers), len(scope_headers)
            )
            raise AssertionError(errmsg)

        for idx in range(len(headers)):
            orig_name, orig_value = headers[idx]
            scope_name = scope_headers[idx][0]
            scope_value = scope_headers[idx][1]

            expected_name = orig_name.lower().encode("ascii")
            expected_value = orig_value.encode("ascii")

            if scope_name != expected_name:
                errmsg = "Header name at index {} not lowercase: expected {}, got {}".format(
                    idx, expected_name, scope_name
                )
                raise AssertionError(errmsg)

            if scope_value != expected_value:
                errmsg = "Header value at index {} not preserved: expected {}, got {}".format(
                    idx, expected_value, scope_value
                )
                raise AssertionError(errmsg)

    return


# =============================================================================
# Property 7: Receive Callable Body Delivery
# Validates: Requirements 4.1, 4.2
# =============================================================================

def test_property_receive_body_delivery():
    """
        Property 7: Receive Callable Body Delivery.
        Feature: development-server

        **Validates: Requirements 4.1, 4.2**

        For any request body, calling receive should return the full
        body with more_body=False.
    """
    for _ in range(100):
        body = _random_body(max_size=512)

        handler = _create_handler()
        handler._body = body
        handler._body_delivered = False

        async def _check():
            msg = await handler._receive()

            if msg["type"] != "http.request":
                errmsg = "Expected type 'http.request', got '{}'".format(msg["type"])
                raise AssertionError(errmsg)

            if msg["body"] != body:
                errmsg = "Body mismatch: expected {} bytes, got {} bytes".format(
                    len(body), len(msg["body"])
                )
                raise AssertionError(errmsg)

            if msg["more_body"] is not False:
                errmsg = "Expected more_body=False, got {}".format(msg["more_body"])
                raise AssertionError(errmsg)

            # Second call should return empty body with more_body=False
            msg2 = await handler._receive()

            if msg2["body"] != b"":
                errmsg = "Expected empty body on second receive, got {} bytes".format(
                    len(msg2["body"])
                )
                raise AssertionError(errmsg)

            if msg2["more_body"] is not False:
                errmsg = "Expected more_body=False on second receive, got {}".format(
                    msg2["more_body"]
                )
                raise AssertionError(errmsg)

        _run_async(_check())

    return


# =============================================================================
# Property 8: HTTP Response Serialization
# Validates: Requirements 4.4
# =============================================================================

def test_property_response_serialization():
    """
        Property 8: HTTP Response Serialization.
        Feature: development-server

        **Validates: Requirements 4.4**

        For any valid status code, response headers, and body bytes,
        _write_response should produce a valid HTTP/1.1 response.
    """
    # Status codes that have known reason phrases
    _KNOWN_STATUS_CODES = [200, 201, 204, 301, 302, 304, 400, 401, 403,
                           404, 405, 408, 413, 431, 500, 502, 503]

    for _ in range(100):
        status = random.choice(_KNOWN_STATUS_CODES)
        body = _random_body(max_size=256)

        # Generate random response headers as byte tuples
        header_count = random.randint(0, 5)
        resp_headers = []
        for _ in range(header_count):
            name = _random_header_name().lower().encode("ascii")
            value = _random_header_value().encode("ascii")
            resp_headers.append((name, value))

        handler = _create_handler()
        transport = _connect_handler(handler)

        handler._write_response(status, resp_headers, body)

        written = transport.written_data

        # Should start with HTTP/1.1 status line
        expected_reason = _get_reason_phrase(status)
        expected_status_line = "HTTP/1.1 {} {}".format(status, expected_reason)
        status_line_bytes = expected_status_line.encode("ascii")

        if not written.startswith(status_line_bytes):
            errmsg = "Response does not start with expected status line. Expected '{}', got '{}'".format(
                expected_status_line, written[:80].decode("ascii", errors="replace")
            )
            raise AssertionError(errmsg)

        # Should contain header/body separator
        if HEADER_TERMINATOR not in written and b"\r\n\r\n" not in written:
            errmsg = "Response missing header/body separator"
            raise AssertionError(errmsg)

        # Find the separator position
        sep_pos = written.find(b"\r\n\r\n")
        if sep_pos < 0:
            errmsg = "Could not find header/body separator in response"
            raise AssertionError(errmsg)

        # Body should follow the separator
        response_body = written[sep_pos + 4:]
        if response_body != body:
            errmsg = "Body mismatch: expected {} bytes, got {} bytes".format(
                len(body), len(response_body)
            )
            raise AssertionError(errmsg)

        # All response headers should be present in the header section
        header_section = written[:sep_pos]
        for name, value in resp_headers:
            header_line = name + b": " + value
            if header_line not in header_section:
                errmsg = "Missing header '{}' in response".format(
                    header_line.decode("ascii", errors="replace")
                )
                raise AssertionError(errmsg)

    return


# =============================================================================
# Property 9: Debug Mode Error Response Detail Control
# Validates: Requirements 8.2, 8.3
# =============================================================================

def test_property_debug_error_control():
    """
        Property 9: Debug Mode Error Response Detail Control.
        Feature: development-server

        **Validates: Requirements 8.2, 8.3**

        For any exception, the 500 response should contain exception
        details when debug=True and exclude them when debug=False.
    """
    _EXCEPTION_TYPES = [ValueError, TypeError, RuntimeError, KeyError, AttributeError]

    for _ in range(100):
        exc_class = random.choice(_EXCEPTION_TYPES)
        msg_len = random.randint(5, 50)
        exc_message = "".join(random.choice(string.ascii_letters + " ") for _ in range(msg_len))
        exc_type_name = exc_class.__name__

        # Test debug=True: error details should be present
        async def _failing_app_debug(scope, receive, send):
            raise exc_class(exc_message)

        handler_debug = _create_handler(app=_failing_app_debug, debug=True)
        transport_debug = _connect_handler(handler_debug)

        # Set up handler state as if a request was parsed
        handler_debug._request_method = "GET"
        handler_debug._request_target = "/test"
        handler_debug._http_version = "HTTP/1.1"
        handler_debug._headers = []
        handler_debug._body = b""
        handler_debug._body_delivered = False
        handler_debug._response_started = False
        handler_debug._response_complete = False

        _run_async(handler_debug._handle_request())

        debug_response = transport_debug.written_data.decode("utf-8", errors="replace")

        if exc_type_name not in debug_response:
            errmsg = "Debug response missing exception type '{}' in response".format(
                exc_type_name
            )
            raise AssertionError(errmsg)

        if exc_message not in debug_response:
            errmsg = "Debug response missing exception message '{}' in response".format(
                exc_message
            )
            raise AssertionError(errmsg)

        # Test debug=False: error details should NOT be present
        async def _failing_app_nodebug(scope, receive, send):
            raise exc_class(exc_message)

        handler_nodebug = _create_handler(app=_failing_app_nodebug, debug=False)
        transport_nodebug = _connect_handler(handler_nodebug)

        handler_nodebug._request_method = "GET"
        handler_nodebug._request_target = "/test"
        handler_nodebug._http_version = "HTTP/1.1"
        handler_nodebug._headers = []
        handler_nodebug._body = b""
        handler_nodebug._body_delivered = False
        handler_nodebug._response_started = False
        handler_nodebug._response_complete = False

        _run_async(handler_nodebug._handle_request())

        nodebug_response = transport_nodebug.written_data.decode("utf-8", errors="replace")

        if exc_type_name in nodebug_response:
            errmsg = "Non-debug response should not contain exception type '{}'".format(
                exc_type_name
            )
            raise AssertionError(errmsg)

        if exc_message in nodebug_response:
            errmsg = "Non-debug response should not contain exception message '{}'".format(
                exc_message
            )
            raise AssertionError(errmsg)

    return


# =============================================================================
# Property 11: Keep-Alive Decision
# Validates: Requirements 11.1, 11.2, 11.3
# =============================================================================

def test_property_keep_alive_decision():
    """
        Property 11: Keep-Alive Decision.
        Feature: development-server

        **Validates: Requirements 11.1, 11.2, 11.3**

        Test all combinations of HTTP version and Connection header
        to verify _should_keep_alive returns the correct boolean.
    """
    handler = _create_handler()

    # Define all expected combinations
    test_cases = [
        # (version, connection_header_value, expected_keep_alive)
        # HTTP/1.1: keep-alive by default
        ("1.1", None, True),
        ("1.1", "keep-alive", True),
        ("1.1", "close", False),
        # HTTP/1.0: close by default
        ("1.0", None, False),
        ("1.0", "keep-alive", True),
        ("1.0", "close", False),
    ]

    for version, conn_value, expected in test_cases:
        headers = []
        if conn_value is not None:
            headers.append((b"connection", conn_value.encode("ascii")))

        result = handler._should_keep_alive(version, headers)

        if result != expected:
            errmsg = (
                "Keep-alive mismatch for version='{}', connection='{}': "
                "expected {}, got {}"
            ).format(version, conn_value, expected, result)
            raise AssertionError(errmsg)

    # Also test with mixed-case Connection header values
    for _ in range(100):
        version = random.choice(["1.0", "1.1"])
        conn_options = [None, "keep-alive", "close", "Keep-Alive", "Close", "KEEP-ALIVE", "CLOSE"]
        conn_value = random.choice(conn_options)

        headers = []
        if conn_value is not None:
            headers.append((b"connection", conn_value.encode("ascii")))

        result = handler._should_keep_alive(version, headers)

        # Determine expected result
        if conn_value is not None:
            normalized = conn_value.lower().strip()
        else:
            normalized = None

        if version == "1.1":
            if normalized == "close":
                expected = False
            else:
                expected = True
        elif version == "1.0":
            if normalized == "keep-alive":
                expected = True
            else:
                expected = False
        else:
            expected = False

        if result != expected:
            errmsg = (
                "Keep-alive mismatch for version='{}', connection='{}': "
                "expected {}, got {}"
            ).format(version, conn_value, expected, result)
            raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests: HTTP Parsing Edge Cases (Task 1.12)
# Requirements: 2.5, 2.6, 4.6
# =============================================================================

def test_malformed_request_line_returns_400():
    """
        Test that a malformed request line results in a 400 response.

        Requirements: 2.5
    """
    handler = _create_handler()
    transport = _connect_handler(handler)

    # Send a malformed request line (missing version)
    malformed = b"GET /path\r\n\r\n"
    handler.data_received(malformed)

    response = transport.written_data.decode("utf-8", errors="replace")

    if "400" not in response:
        errmsg = "Expected 400 status in response, got: {}".format(response[:200])
        raise AssertionError(errmsg)

    if not transport.is_closed:
        errmsg = "Expected transport to be closed after malformed request"
        raise AssertionError(errmsg)

    return


def test_request_line_exceeding_limit_returns_400():
    """
        Test that a request line exceeding 8192 bytes returns 400.

        Requirements: 2.5
    """
    handler = _create_handler()
    transport = _connect_handler(handler)

    # Create a request line that exceeds MAX_REQUEST_LINE_BYTES
    long_path = "/" + "a" * (MAX_REQUEST_LINE_BYTES + 100)
    long_line = "GET {} HTTP/1.1\r\n\r\n".format(long_path).encode("ascii")
    handler.data_received(long_line)

    response = transport.written_data.decode("utf-8", errors="replace")

    if "400" not in response:
        errmsg = "Expected 400 status for oversized request line, got: {}".format(
            response[:200]
        )
        raise AssertionError(errmsg)

    if not transport.is_closed:
        errmsg = "Expected transport to be closed after oversized request line"
        raise AssertionError(errmsg)

    return


def test_header_block_exceeding_limit_returns_431():
    """
        Test that a header block exceeding 32768 bytes returns 431.

        Requirements: 2.6
    """
    handler = _create_handler()
    transport = _connect_handler(handler)

    # Build a valid request line first
    request_line = b"GET / HTTP/1.1\r\n"

    # Create a header block that exceeds MAX_HEADER_BLOCK_BYTES
    # Each header line: "X-Pad-NNNN: <value>\r\n"
    header_lines = []
    total_size = 0
    idx = 0
    while total_size < MAX_HEADER_BLOCK_BYTES + 1000:
        header_line = "X-Pad-{}: {}".format(idx, "x" * 200)
        header_lines.append(header_line)
        total_size += len(header_line) + 2  # +2 for \r\n
        idx += 1

    header_block = "\r\n".join(header_lines).encode("ascii")
    raw_data = request_line + header_block + HEADER_TERMINATOR

    handler.data_received(raw_data)

    response = transport.written_data.decode("utf-8", errors="replace")

    if "431" not in response:
        errmsg = "Expected 431 status for oversized header block, got: {}".format(
            response[:200]
        )
        raise AssertionError(errmsg)

    if not transport.is_closed:
        errmsg = "Expected transport to be closed after oversized header block"
        raise AssertionError(errmsg)

    return


def test_empty_body_with_content_length_zero():
    """
        Test that Content-Length: 0 results in an empty body.

        Requirements: 2.3
    """
    handler = _create_handler()
    transport = _connect_handler(handler)

    headers = [("Content-Length", "0")]
    raw_request = _build_raw_request("POST", "/empty", "HTTP/1.1", headers, b"")

    handler.data_received(raw_request)

    # With Content-Length: 0, the body should be empty and state should
    # transition to PROCESSING (no body to wait for)
    if handler._body != b"":
        errmsg = "Expected empty body with Content-Length: 0, got {} bytes".format(
            len(handler._body)
        )
        raise AssertionError(errmsg)

    return


def test_send_body_before_start_closes_connection():
    """
        Test that sending http.response.body before http.response.start
        logs an error and closes the connection.

        Requirements: 4.6
    """
    handler = _create_handler()
    transport = _connect_handler(handler)

    # Ensure response_started is False
    handler._response_started = False

    async def _check():
        # Send body without start
        await handler._send({
            "type": "http.response.body",
            "body": b"some body",
            "more_body": False,
        })

    _run_async(_check())

    if not transport.is_closed:
        errmsg = "Expected transport to be closed when body sent before start"
        raise AssertionError(errmsg)

    return
