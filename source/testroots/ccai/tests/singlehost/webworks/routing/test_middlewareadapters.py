"""
    Tests for the Middleware Adapters module.

    This module contains unit tests for the ASGI and WSGI protocol adapters
    that bridge between internal Middleware/AsyncMiddleware protocols and
    external ASGI/WSGI middleware protocols.
"""

import asyncio
from typing import Dict

from ccai.webworks.routing.middlewareadapters import (
    ASGIMiddlewareAdapter,
    AsyncMiddlewareToASGI,
    WSGIMiddlewareAdapter,
    MiddlewareToWSGI,
)
from ccai.webworks.routing.request import Request
from ccai.webworks.routing.response import Response


# =============================================================================
# Test Helpers
# =============================================================================

def _make_request(method: str = "GET", path: str = "/test", headers: Dict[str, str] = None, body: bytes = b"") -> Request:
    """
        Create a simple Request for testing.
    """
    return Request(method=method, path=path, headers=headers, body=body)


def _make_response(status_code: int = 200, headers: Dict[str, str] = None, body: bytes = b"OK") -> Response:
    """
        Create a simple Response for testing.
    """
    return Response(status_code=status_code, headers=headers, body=body)


# =============================================================================
# Tests for ASGIMiddlewareAdapter
# =============================================================================

def test_asgi_adapter_name():
    """
        Test that ASGIMiddlewareAdapter stores the name.
    """
    def dummy_asgi_factory(app):
        async def middleware(scope, receive, send):
            await app(scope, receive, send)
        return middleware

    adapter = ASGIMiddlewareAdapter(dummy_asgi_factory, name="test_asgi")

    if adapter.name != "test_asgi":
        errmsg = f"Expected name 'test_asgi', got '{adapter.name}'"
        raise AssertionError(errmsg)

    return


def test_asgi_adapter_default_name():
    """
        Test that ASGIMiddlewareAdapter defaults to empty name.
    """
    def dummy_asgi_factory(app):
        async def middleware(scope, receive, send):
            await app(scope, receive, send)
        return middleware

    adapter = ASGIMiddlewareAdapter(dummy_asgi_factory)

    if adapter.name != "":
        errmsg = f"Expected empty name, got '{adapter.name}'"
        raise AssertionError(errmsg)

    return


def test_asgi_adapter_passthrough():
    """
        Test that ASGIMiddlewareAdapter passes through to call_next
        when the ASGI middleware delegates to the inner app.
    """
    call_log = []

    def passthrough_asgi_factory(app):
        async def middleware(scope, receive, send):
            call_log.append("asgi_before")
            await app(scope, receive, send)
            call_log.append("asgi_after")
        return middleware

    adapter = ASGIMiddlewareAdapter(passthrough_asgi_factory, name="passthrough")

    request = _make_request()
    expected_response = _make_response(status_code=200, body=b"handler_response")

    async def call_next(req: Request) -> Response:
        call_log.append("call_next")
        return expected_response

    asyncio.run(adapter(request, call_next))

    if "call_next" not in call_log:
        errmsg = f"Expected call_next to be called, log: {call_log}"
        raise AssertionError(errmsg)

    if "asgi_before" not in call_log:
        errmsg = f"Expected asgi_before in log, got: {call_log}"
        raise AssertionError(errmsg)

    return


def test_asgi_adapter_short_circuit():
    """
        Test that ASGIMiddlewareAdapter supports short-circuit responses
        where the ASGI middleware sends a response without calling the inner app.
    """
    def short_circuit_asgi_factory(app):
        async def middleware(scope, receive, send):
            # Send response directly without calling app
            await send({
                "type": "http.response.start",
                "status": 403,
                "headers": [
                    [b"content-type", b"text/plain"],
                ],
            })
            await send({
                "type": "http.response.body",
                "body": b"Forbidden",
            })
        return middleware

    adapter = ASGIMiddlewareAdapter(short_circuit_asgi_factory, name="short_circuit")

    request = _make_request()
    call_next_called = [False]

    async def call_next(req: Request) -> Response:
        call_next_called[0] = True
        return _make_response()

    response = asyncio.run(adapter(request, call_next))

    if response.status_code != 403:
        errmsg = f"Expected status 403, got {response.status_code}"
        raise AssertionError(errmsg)

    if response.body != b"Forbidden":
        errmsg = f"Expected body b'Forbidden', got {response.body}"
        raise AssertionError(errmsg)

    if response.headers.get("content-type") != "text/plain":
        errmsg = f"Expected content-type header, got {response.headers}"
        raise AssertionError(errmsg)

    return


def test_asgi_adapter_modifies_scope():
    """
        Test that ASGIMiddlewareAdapter supports ASGI middleware that
        inspects or modifies the ASGI scope.
    """
    scope_captured = [None]

    def scope_inspecting_factory(app):
        async def middleware(scope, receive, send):
            scope_captured[0] = dict(scope)
            # Add a custom key to scope
            scope["custom_key"] = "custom_value"
            await app(scope, receive, send)
        return middleware

    adapter = ASGIMiddlewareAdapter(scope_inspecting_factory, name="scope_inspector")

    request = _make_request(method="POST", path="/api/data")

    async def call_next(req: Request) -> Response:
        return _make_response(status_code=200, body=b"OK")

    asyncio.run(adapter(request, call_next))

    if scope_captured[0] is None:
        errmsg = "Expected scope to be captured"
        raise AssertionError(errmsg)

    if scope_captured[0].get("method") != "POST":
        errmsg = f"Expected method 'POST' in scope, got '{scope_captured[0].get('method')}'"
        raise AssertionError(errmsg)

    if scope_captured[0].get("path") != "/api/data":
        errmsg = f"Expected path '/api/data' in scope, got '{scope_captured[0].get('path')}'"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Tests for AsyncMiddlewareToASGI
# =============================================================================

def test_async_to_asgi_passthrough():
    """
        Test that AsyncMiddlewareToASGI passes through to the inner ASGI app
        when the AsyncMiddleware calls call_next.
    """
    class PassthroughAsyncMiddleware:
        name = "passthrough"

        async def __call__(self, request, call_next):
            return await call_next(request)

    app_called = [False]
    sent_events = []

    async def inner_app(scope, receive, send):
        app_called[0] = True
        await send({
            "type": "http.response.start",
            "status": 200,
            "headers": [[b"content-type", b"text/plain"]],
        })
        await send({
            "type": "http.response.body",
            "body": b"inner_app_response",
        })

    middleware = PassthroughAsyncMiddleware()
    adapter = AsyncMiddlewareToASGI(middleware, inner_app)

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/test",
        "query_string": b"",
        "headers": [],
        "server": ("localhost", 80),
        "scheme": "http",
    }

    body_sent = [False]

    async def receive():
        if not body_sent[0]:
            body_sent[0] = True
            return {"type": "http.request", "body": b"", "more_body": False}
        return {"type": "http.disconnect"}

    async def send(event):
        sent_events.append(event)

    asyncio.run(adapter(scope, receive, send))

    if len(sent_events) < 2:
        errmsg = f"Expected at least 2 sent events, got {len(sent_events)}"
        raise AssertionError(errmsg)

    start_event = sent_events[0]
    if start_event.get("status") != 200:
        errmsg = f"Expected status 200, got {start_event.get('status')}"
        raise AssertionError(errmsg)

    return


def test_async_to_asgi_short_circuit():
    """
        Test that AsyncMiddlewareToASGI supports short-circuit responses
        from the AsyncMiddleware.
    """
    class ShortCircuitAsyncMiddleware:
        name = "short_circuit"

        async def __call__(self, request, call_next):
            return Response(status_code=401, headers={"Content-Type": "text/plain"}, body=b"Unauthorized")

    app_called = [False]

    async def inner_app(scope, receive, send):
        app_called[0] = True
        await send({
            "type": "http.response.start",
            "status": 200,
            "headers": [],
        })
        await send({
            "type": "http.response.body",
            "body": b"should_not_reach",
        })

    middleware = ShortCircuitAsyncMiddleware()
    adapter = AsyncMiddlewareToASGI(middleware, inner_app)

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/test",
        "query_string": b"",
        "headers": [],
        "server": ("localhost", 80),
        "scheme": "http",
    }

    body_sent = [False]

    async def receive():
        if not body_sent[0]:
            body_sent[0] = True
            return {"type": "http.request", "body": b"", "more_body": False}
        return {"type": "http.disconnect"}

    sent_events = []

    async def send(event):
        sent_events.append(event)

    asyncio.run(adapter(scope, receive, send))

    # The inner app should NOT have been called
    if app_called[0]:
        errmsg = "Expected inner app NOT to be called due to short-circuit"
        raise AssertionError(errmsg)

    # The response should be 401
    if len(sent_events) < 1:
        errmsg = "Expected at least 1 sent event"
        raise AssertionError(errmsg)

    start_event = sent_events[0]
    if start_event.get("status") != 401:
        errmsg = f"Expected status 401, got {start_event.get('status')}"
        raise AssertionError(errmsg)

    return


def test_async_to_asgi_non_http_passthrough():
    """
        Test that AsyncMiddlewareToASGI passes non-HTTP scopes directly
        to the inner app without middleware processing.
    """
    class ShouldNotBeCalledMiddleware:
        name = "should_not_call"

        async def __call__(self, request, call_next):
            raise AssertionError("Middleware should not be called for non-HTTP scopes")

    app_called = [False]

    async def inner_app(scope, receive, send):
        app_called[0] = True

    middleware = ShouldNotBeCalledMiddleware()
    adapter = AsyncMiddlewareToASGI(middleware, inner_app)

    scope = {"type": "websocket", "path": "/ws"}

    async def receive():
        return {"type": "websocket.connect"}

    async def send(event):
        pass

    asyncio.run(adapter(scope, receive, send))

    if not app_called[0]:
        errmsg = "Expected inner app to be called for non-HTTP scope"
        raise AssertionError(errmsg)

    return


def test_async_to_asgi_middleware_modifies_response():
    """
        Test that AsyncMiddlewareToASGI supports middleware that modifies
        the response from the inner app.
    """
    class HeaderAddingMiddleware:
        name = "header_adder"

        async def __call__(self, request, call_next):
            response = await call_next(request)
            response.set_header("X-Custom", "added-by-middleware")
            return response

    async def inner_app(scope, receive, send):
        await send({
            "type": "http.response.start",
            "status": 200,
            "headers": [[b"content-type", b"text/plain"]],
        })
        await send({
            "type": "http.response.body",
            "body": b"hello",
        })

    middleware = HeaderAddingMiddleware()
    adapter = AsyncMiddlewareToASGI(middleware, inner_app)

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/test",
        "query_string": b"",
        "headers": [],
        "server": ("localhost", 80),
        "scheme": "http",
    }

    body_sent = [False]

    async def receive():
        if not body_sent[0]:
            body_sent[0] = True
            return {"type": "http.request", "body": b"", "more_body": False}
        return {"type": "http.disconnect"}

    sent_events = []

    async def send(event):
        sent_events.append(event)

    asyncio.run(adapter(scope, receive, send))

    # Check that the custom header was added
    if len(sent_events) < 1:
        errmsg = "Expected at least 1 sent event"
        raise AssertionError(errmsg)

    start_event = sent_events[0]
    raw_headers = start_event.get("headers", [])

    found_custom = False
    for header_pair in raw_headers:
        h_name = header_pair[0]
        h_value = header_pair[1]
        if isinstance(h_name, bytes):
            h_name = h_name.decode("latin-1")
        if isinstance(h_value, bytes):
            h_value = h_value.decode("latin-1")
        if h_name.lower() == "x-custom" and h_value == "added-by-middleware":
            found_custom = True
            break

    if not found_custom:
        errmsg = f"Expected X-Custom header in response, got headers: {raw_headers}"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Tests for WSGIMiddlewareAdapter
# =============================================================================

def test_wsgi_adapter_name():
    """
        Test that WSGIMiddlewareAdapter stores the name.
    """
    def dummy_factory(app):
        return app

    adapter = WSGIMiddlewareAdapter(dummy_factory, name="test_wsgi")

    if adapter.name != "test_wsgi":
        errmsg = f"Expected name 'test_wsgi', got '{adapter.name}'"
        raise AssertionError(errmsg)

    return


def test_wsgi_adapter_default_name():
    """
        Test that WSGIMiddlewareAdapter defaults to empty name.
    """
    def dummy_factory(app):
        return app

    adapter = WSGIMiddlewareAdapter(dummy_factory)

    if adapter.name != "":
        errmsg = f"Expected empty name, got '{adapter.name}'"
        raise AssertionError(errmsg)

    return


def test_wsgi_adapter_passthrough():
    """
        Test that WSGIMiddlewareAdapter passes through to call_next
        when the WSGI middleware delegates to the inner app.
    """
    call_log = []

    def passthrough_factory(app):
        def middleware(environ, start_response):
            call_log.append("wsgi_before")
            result = app(environ, start_response)
            call_log.append("wsgi_after")
            return result
        return middleware

    adapter = WSGIMiddlewareAdapter(passthrough_factory, name="passthrough")

    request = _make_request()
    expected_response = _make_response(status_code=200, body=b"handler_response")

    def call_next(req: Request) -> Response:
        call_log.append("call_next")
        return expected_response

    response = adapter(request, call_next)

    if "call_next" not in call_log:
        errmsg = f"Expected call_next to be called, log: {call_log}"
        raise AssertionError(errmsg)

    if response.status_code != 200:
        errmsg = f"Expected status 200, got {response.status_code}"
        raise AssertionError(errmsg)

    return


def test_wsgi_adapter_short_circuit():
    """
        Test that WSGIMiddlewareAdapter supports short-circuit responses
        where the WSGI middleware returns a response without calling the inner app.
    """
    def short_circuit_factory(app):
        def middleware(environ, start_response):
            start_response("403 Forbidden", [("Content-Type", "text/plain")])
            return [b"Forbidden"]
        return middleware

    adapter = WSGIMiddlewareAdapter(short_circuit_factory, name="short_circuit")

    request = _make_request()
    call_next_called = [False]

    def call_next(req: Request) -> Response:
        call_next_called[0] = True
        return _make_response()

    response = adapter(request, call_next)

    if call_next_called[0]:
        errmsg = "Expected call_next NOT to be called due to short-circuit"
        raise AssertionError(errmsg)

    if response.status_code != 403:
        errmsg = f"Expected status 403, got {response.status_code}"
        raise AssertionError(errmsg)

    if response.body != b"Forbidden":
        errmsg = f"Expected body b'Forbidden', got {response.body}"
        raise AssertionError(errmsg)

    return


def test_wsgi_adapter_modifies_environ():
    """
        Test that WSGIMiddlewareAdapter supports WSGI middleware that
        inspects or modifies the WSGI environ dictionary.
    """
    environ_captured = [None]

    def environ_modifying_factory(app):
        def middleware(environ, start_response):
            environ_captured[0] = dict(environ)
            environ["HTTP_X_CUSTOM"] = "injected"
            return app(environ, start_response)
        return middleware

    adapter = WSGIMiddlewareAdapter(environ_modifying_factory, name="environ_modifier")

    request = _make_request(method="POST", path="/api/data")

    def call_next(req: Request) -> Response:
        return _make_response(status_code=200, body=b"OK")

    adapter(request, call_next)

    if environ_captured[0] is None:
        errmsg = "Expected environ to be captured"
        raise AssertionError(errmsg)

    if environ_captured[0].get("REQUEST_METHOD") != "POST":
        errmsg = f"Expected REQUEST_METHOD 'POST', got '{environ_captured[0].get('REQUEST_METHOD')}'"
        raise AssertionError(errmsg)

    if environ_captured[0].get("PATH_INFO") != "/api/data":
        errmsg = f"Expected PATH_INFO '/api/data', got '{environ_captured[0].get('PATH_INFO')}'"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Tests for MiddlewareToWSGI
# =============================================================================

def test_middleware_to_wsgi_passthrough():
    """
        Test that MiddlewareToWSGI wraps a Middleware as a WSGI factory
        that passes through to the inner WSGI app.
    """
    class PassthroughMiddleware:
        name = "passthrough"

        def __call__(self, request, call_next):
            return call_next(request)

    middleware = PassthroughMiddleware()
    factory = MiddlewareToWSGI(middleware)

    app_called = [False]

    def inner_app(environ, start_response):
        app_called[0] = True
        start_response("200 OK", [("Content-Type", "text/plain")])
        return [b"inner_response"]

    wrapped_app = factory(inner_app)

    # Build a minimal WSGI environ
    import io
    environ = {
        "REQUEST_METHOD": "GET",
        "PATH_INFO": "/test",
        "QUERY_STRING": "",
        "SERVER_NAME": "localhost",
        "SERVER_PORT": "80",
        "wsgi.url_scheme": "http",
        "wsgi.input": io.BytesIO(b""),
        "wsgi.errors": io.BytesIO(),
    }

    captured_status = [None]
    captured_headers = []

    def start_response(status, headers, exc_info=None):
        captured_status[0] = status
        captured_headers.extend(headers)

    list(wrapped_app(environ, start_response))

    if not app_called[0]:
        errmsg = "Expected inner app to be called"
        raise AssertionError(errmsg)

    if "200" not in (captured_status[0] or ""):
        errmsg = f"Expected status containing '200', got '{captured_status[0]}'"
        raise AssertionError(errmsg)

    return


def test_middleware_to_wsgi_short_circuit():
    """
        Test that MiddlewareToWSGI supports short-circuit responses
        from the Middleware.
    """
    class ShortCircuitMiddleware:
        name = "short_circuit"

        def __call__(self, request, call_next):
            return Response(status_code=401, headers={"Content-Type": "text/plain"}, body=b"Unauthorized")

    middleware = ShortCircuitMiddleware()
    factory = MiddlewareToWSGI(middleware)

    app_called = [False]

    def inner_app(environ, start_response):
        app_called[0] = True
        start_response("200 OK", [])
        return [b"should_not_reach"]

    wrapped_app = factory(inner_app)

    import io
    environ = {
        "REQUEST_METHOD": "GET",
        "PATH_INFO": "/test",
        "QUERY_STRING": "",
        "SERVER_NAME": "localhost",
        "SERVER_PORT": "80",
        "wsgi.url_scheme": "http",
        "wsgi.input": io.BytesIO(b""),
        "wsgi.errors": io.BytesIO(),
    }

    captured_status = [None]
    captured_headers = []

    def start_response(status, headers, exc_info=None):
        captured_status[0] = status
        captured_headers.extend(headers)

    list(wrapped_app(environ, start_response))

    if app_called[0]:
        errmsg = "Expected inner app NOT to be called due to short-circuit"
        raise AssertionError(errmsg)

    if "401" not in (captured_status[0] or ""):
        errmsg = f"Expected status containing '401', got '{captured_status[0]}'"
        raise AssertionError(errmsg)

    return


def test_middleware_to_wsgi_modifies_response():
    """
        Test that MiddlewareToWSGI supports middleware that modifies
        the response from the inner app.
    """
    class HeaderAddingMiddleware:
        name = "header_adder"

        def __call__(self, request, call_next):
            response = call_next(request)
            response.set_header("X-Custom", "added-by-middleware")
            return response

    middleware = HeaderAddingMiddleware()
    factory = MiddlewareToWSGI(middleware)

    def inner_app(environ, start_response):
        start_response("200 OK", [("Content-Type", "text/plain")])
        return [b"hello"]

    wrapped_app = factory(inner_app)

    import io
    environ = {
        "REQUEST_METHOD": "GET",
        "PATH_INFO": "/test",
        "QUERY_STRING": "",
        "SERVER_NAME": "localhost",
        "SERVER_PORT": "80",
        "wsgi.url_scheme": "http",
        "wsgi.input": io.BytesIO(b""),
        "wsgi.errors": io.BytesIO(),
    }

    captured_status = [None]
    captured_headers = []

    def start_response(status, headers, exc_info=None):
        captured_status[0] = status
        captured_headers.extend(headers)

    list(wrapped_app(environ, start_response))

    # Check that the custom header was added
    header_names = [h[0] for h in captured_headers]
    header_dict = {h[0]: h[1] for h in captured_headers}

    if "X-Custom" not in header_names:
        errmsg = f"Expected X-Custom header in response, got headers: {captured_headers}"
        raise AssertionError(errmsg)

    if header_dict.get("X-Custom") != "added-by-middleware":
        errmsg = f"Expected X-Custom value 'added-by-middleware', got '{header_dict.get('X-Custom')}'"
        raise AssertionError(errmsg)

    return


if __name__ == "__main__":
    from ccai.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()


# =============================================================================
# Duplicate headers, streaming content and request carry-through
# =============================================================================

from ccai.webworks.authentication.core import AuthenticationContext, Principal
from ccai.webworks.routing.response import StreamingResponse


def test_asgi_adapter_keeps_every_set_cookie_header():
    """
        A response that sets two cookies still carries both after passing
        through an adapted ASGI middleware.
    """
    def passthrough_asgi(app):
        async def middleware(scope, receive, send):
            await app(scope, receive, send)
        return middleware

    async def call_next(request):
        response = _make_response()
        response.set_cookie("first", "1")
        response.set_cookie("second", "2")
        return response

    adapter = ASGIMiddlewareAdapter(passthrough_asgi, name="passthrough")
    response = asyncio.run(adapter(_make_request(), call_next))

    cookie_headers = [value for name, value in response._get_all_headers() if name.lower() == "set-cookie"]

    assert len(cookie_headers) == 2, f"Expected two Set-Cookie headers, got {cookie_headers}"
    return


def test_asgi_adapter_passes_streaming_content_through():
    """
        The content of a streaming response is not lost by the adapter.
    """
    def passthrough_asgi(app):
        async def middleware(scope, receive, send):
            await app(scope, receive, send)
        return middleware

    async def call_next(request):
        return StreamingResponse(iter([b"part-1;", b"part-2"]))

    adapter = ASGIMiddlewareAdapter(passthrough_asgi, name="passthrough")
    response = asyncio.run(adapter(_make_request(), call_next))

    assert response.body == b"part-1;part-2", f"Unexpected body {response.body!r}"
    return


def test_async_middleware_to_asgi_forwards_real_receive_after_body():
    """
        After the buffered body the inner app receives what the client
        really sends, not a fabricated disconnect.
    """
    events = []

    async def inner_app(scope, receive, send):
        events.append(await receive())
        events.append(await receive())
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b"", "more_body": False})

    async def middleware(request, call_next):
        return await call_next(request)

    pending = [
        {"type": "http.request", "body": b"payload", "more_body": False},
        {"type": "custom.marker"},
    ]

    async def receive():
        return pending.pop(0)

    async def send(event):
        return

    adapter = AsyncMiddlewareToASGI(middleware, inner_app)
    scope = {"type": "http", "method": "POST", "path": "/", "headers": []}
    asyncio.run(adapter(scope, receive, send))

    assert events[0]["body"] == b"payload", f"Unexpected first event {events[0]}"
    assert events[1] == {"type": "custom.marker"}, f"Expected the real channel, got {events[1]}"
    return


def test_wsgi_adapter_keeps_path_params_and_auth_of_the_request():
    """
        A handler behind an adapted WSGI middleware still sees the path
        parameters and the authentication context of the request.
    """
    def passthrough_wsgi(app):
        def middleware(environ, start_response):
            return app(environ, start_response)
        return middleware

    context = AuthenticationContext(principal=Principal(identifier="u1"), scheme="Test")
    request = Request(method="GET", path="/items/7", scope={"auth": context})
    request.path_params = {"id": 7}

    seen = {}

    def call_next(inner_request):
        seen["path_params"] = inner_request.path_params
        seen["auth"] = inner_request.auth
        seen["same_object"] = inner_request is request
        return _make_response()

    adapter = WSGIMiddlewareAdapter(passthrough_wsgi, name="passthrough")
    adapter(request, call_next)

    assert seen["path_params"] == {"id": 7}, f"Unexpected path params {seen['path_params']}"
    assert seen["auth"] is context, "The authentication context was lost"
    assert seen["same_object"] is True, "An unchanged request should be passed on as it is"
    return


def test_wsgi_adapter_overlays_what_the_middleware_changed():
    """
        A header added and a key set by the WSGI middleware reach the
        handler, on a request that keeps its path parameters.
    """
    def tagging_wsgi(app):
        def middleware(environ, start_response):
            environ["HTTP_X_TAGGED"] = "yes"
            environ["myapp.user"] = "alice"
            return app(environ, start_response)
        return middleware

    request = Request(method="GET", path="/items/7")
    request.path_params = {"id": 7}

    seen = {}

    def call_next(inner_request):
        seen["header"] = inner_request.headers.get("X-Tagged")
        seen["state"] = inner_request.scope.get("myapp.user")
        seen["path_params"] = inner_request.path_params
        return _make_response()

    adapter = WSGIMiddlewareAdapter(tagging_wsgi, name="tagging")
    adapter(request, call_next)

    assert seen["header"] == "yes", f"Expected the added header, got {seen['header']!r}"
    assert seen["state"] == "alice", f"Expected the environ key on the scope, got {seen['state']!r}"
    assert seen["path_params"] == {"id": 7}, f"Unexpected path params {seen['path_params']}"
    return


def test_wsgi_adapter_environ_has_required_keys():
    """
        The synthesised environ carries the keys PEP 3333 requires.
    """
    captured = {}

    def capturing_wsgi(app):
        def middleware(environ, start_response):
            captured.update(environ)
            return app(environ, start_response)
        return middleware

    adapter = WSGIMiddlewareAdapter(capturing_wsgi, name="capturing")
    adapter(_make_request(), lambda inner_request: _make_response())

    for key in ["SCRIPT_NAME", "SERVER_PROTOCOL", "wsgi.version", "wsgi.input", "wsgi.errors"]:
        assert key in captured, f"Expected {key} in the environ"
    return


def test_wsgi_adapter_keeps_every_set_cookie_header():
    """
        Two Set-Cookie headers survive the WSGI adapter.
    """
    def passthrough_wsgi(app):
        def middleware(environ, start_response):
            return app(environ, start_response)
        return middleware

    def call_next(inner_request):
        response = _make_response()
        response.set_cookie("first", "1")
        response.set_cookie("second", "2")
        return response

    adapter = WSGIMiddlewareAdapter(passthrough_wsgi, name="passthrough")
    response = adapter(_make_request(), call_next)

    cookie_headers = [value for name, value in response._get_all_headers() if name.lower() == "set-cookie"]

    assert len(cookie_headers) == 2, f"Expected two Set-Cookie headers, got {cookie_headers}"
    return
