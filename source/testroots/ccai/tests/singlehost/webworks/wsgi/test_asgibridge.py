"""
    Tests for the ASGIBridge class.

    The bridge is driven the way a WSGI server drives an application: it is
    called with an environ and a start_response, its body is iterated and
    closed. Small ASGI applications record what they receive and when their
    send() calls return, so the tests can check the protocol on both sides.
    Serving a full WebApplication over real sockets is covered by
    test_webapplication_serving.
"""

import io
import os
import threading
import time

from typing import Any, Callable, Dict, List, Optional, Tuple

from ccai.errors.exceptions import SemanticError, SkipError

from ccai.webworks.asgi.exceptions import ClientDisconnected
from ccai.webworks.wsgi.asgibridge import (
    ASGIBridge,
    LIFESPAN_COMPLETE,
    LIFESPAN_FAILED,
    LIFESPAN_NOT_STARTED,
    LIFESPAN_UNSUPPORTED,
    is_asgi_application,
)
from ccai.webworks.wsgi.constants import ENVIRON_REQUEST_TIMEOUT
from ccai.webworks.wsgi.exceptions import IncompleteResponse


# =============================================================================
# Helpers
# =============================================================================

def make_environ(
    method: str = "GET",
    path: str = "/",
    body: bytes = b"",
    query: str = "",
    headers: Optional[Dict[str, str]] = None,
    content_length: Optional[int] = None,
) -> Dict[str, Any]:
    """
        Build a WSGI environ as a server builds it.
    """
    environ: Dict[str, Any] = {
        "REQUEST_METHOD": method,
        "SCRIPT_NAME": "",
        "PATH_INFO": path,
        "QUERY_STRING": query,
        "SERVER_NAME": "127.0.0.1",
        "SERVER_PORT": "8000",
        "SERVER_PROTOCOL": "HTTP/1.1",
        "REMOTE_ADDR": "10.1.2.3",
        "REMOTE_PORT": "55555",
        "wsgi.version": (1, 0),
        "wsgi.url_scheme": "http",
        "wsgi.input": io.BytesIO(body),
        "wsgi.errors": io.StringIO(),
        "wsgi.multithread": True,
        "wsgi.multiprocess": False,
        "wsgi.run_once": False,
    }

    if content_length is None and len(body) > 0:
        content_length = len(body)
    if content_length is not None:
        environ["CONTENT_LENGTH"] = str(content_length)

    for name, value in (headers or {}).items():
        if name.lower() == "content-type":
            environ["CONTENT_TYPE"] = value
        else:
            environ["HTTP_" + name.upper().replace("-", "_")] = value

    return environ


class StartResponseRecorder:
    """
        A start_response that records what the application passed.
    """

    def __init__(self):
        self.status: Optional[str] = None
        self.headers: List[Tuple[str, str]] = []
        self.calls = 0
        return

    def __call__(self, status: str, headers: List[Tuple[str, str]], exc_info: Any = None) -> Callable:
        self.status = status
        self.headers = list(headers)
        self.calls += 1
        return lambda data: None

    def header_values(self, name: str) -> List[str]:
        rtnval = [value for header_name, value in self.headers if header_name.lower() == name.lower()]
        return rtnval


def serve(bridge: ASGIBridge, environ: Dict[str, Any]) -> Tuple[StartResponseRecorder, bytes]:
    """
        Serve one request the way a WSGI server does.
    """
    recorder = StartResponseRecorder()
    body_iterable = bridge(environ, recorder)
    try:
        body = b"".join(body_iterable)
    finally:
        close_body = getattr(body_iterable, "close", None)
        if close_body is not None:
            close_body()
    return recorder, body


class LifespanApp:
    """
        An ASGI application with a lifespan and a simple HTTP answer.
    """

    def __init__(self, fail_startup: bool = False):
        self.events: List[str] = []
        self.fail_startup = fail_startup
        self.scopes: List[Dict[str, Any]] = []
        return

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] == "lifespan":
            while True:
                message = await receive()
                self.events.append(message["type"])
                if message["type"] == "lifespan.startup":
                    if self.fail_startup:
                        await send({"type": "lifespan.startup.failed", "message": "no database"})
                    else:
                        scope["state"]["started_by"] = "lifespan"
                        await send({"type": "lifespan.startup.complete"})
                elif message["type"] == "lifespan.shutdown":
                    await send({"type": "lifespan.shutdown.complete"})
                    return

        self.scopes.append(scope)
        await send({"type": "http.response.start", "status": 200, "headers": [(b"content-type", b"text/plain")]})
        await send({"type": "http.response.body", "body": b"ok", "more_body": False})
        return


async def no_lifespan_app(scope, receive, send) -> None:
    """
        An ASGI application that rejects the lifespan scope.
    """
    if scope["type"] == "lifespan":
        raise RuntimeError("lifespan is not supported")

    await send({"type": "http.response.start", "status": 204, "headers": []})
    await send({"type": "http.response.body", "body": b""})
    return


# =============================================================================
# Construction
# =============================================================================

def test_bridge_needs_exactly_one_application_source():
    """
        The bridge takes an ASGI application or a provider, not both or neither.
    """
    for kwargs in ({}, {"asgi_app": no_lifespan_app, "app_provider": lambda: no_lifespan_app}):
        try:
            ASGIBridge(**kwargs)
        except SemanticError:
            continue
        errmsg = f"Expected SemanticError for ASGIBridge(**{kwargs})"
        raise AssertionError(errmsg)

    return


def test_is_asgi_application_tells_asgi_from_wsgi():
    """
        Async callables are ASGI applications, a bridge (a WSGI callable) is not.
    """
    bridge = ASGIBridge(asgi_app=no_lifespan_app)

    checks = [
        (no_lifespan_app, True),
        (LifespanApp(), True),
        (bridge, False),
        (lambda environ, start_response: [], False),
        ("not callable", False),
    ]

    for candidate, expected in checks:
        if is_asgi_application(candidate) is not expected:
            errmsg = f"is_asgi_application({candidate!r}) should be {expected}"
            raise AssertionError(errmsg)

    return


# =============================================================================
# Lifespan
# =============================================================================

def test_lifespan_startup_runs_once_before_the_first_request():
    """
        The first request starts the bridge; the startup event is sent once.
    """
    app = LifespanApp()
    bridge = ASGIBridge(asgi_app=app)

    try:
        if bridge.lifespan_status != LIFESPAN_NOT_STARTED:
            errmsg = f"Expected the bridge not to be started yet, got {bridge.lifespan_status}"
            raise AssertionError(errmsg)

        for _ in range(3):
            recorder, body = serve(bridge, make_environ())
            if recorder.status != "200 OK" or body != b"ok":
                errmsg = f"Expected 200 ok, got {recorder.status} {body!r}"
                raise AssertionError(errmsg)

        if app.events != ["lifespan.startup"]:
            errmsg = f"Expected one startup event, got {app.events}"
            raise AssertionError(errmsg)

        if bridge.lifespan_status != LIFESPAN_COMPLETE:
            errmsg = f"Expected lifespan status complete, got {bridge.lifespan_status}"
            raise AssertionError(errmsg)
    finally:
        bridge.shutdown()

    return


def test_lifespan_state_is_copied_into_every_request_scope():
    """
        What the startup handlers put in the lifespan state is in the request scope.
    """
    app = LifespanApp()
    bridge = ASGIBridge(asgi_app=app)

    try:
        serve(bridge, make_environ())
    finally:
        bridge.shutdown()

    state = app.scopes[0]["state"]
    if state.get("started_by") != "lifespan":
        errmsg = f"Expected the lifespan state in the request scope, got {state}"
        raise AssertionError(errmsg)

    return


def test_shutdown_runs_the_lifespan_shutdown_and_refuses_later_requests():
    """
        shutdown() sends the shutdown event; requests after it get 503.
    """
    app = LifespanApp()
    bridge = ASGIBridge(asgi_app=app)

    bridge.startup()
    bridge.shutdown()

    if app.events != ["lifespan.startup", "lifespan.shutdown"]:
        errmsg = f"Expected startup then shutdown, got {app.events}"
        raise AssertionError(errmsg)

    recorder, body = serve(bridge, make_environ())
    if recorder.status != "503 Service Unavailable":
        errmsg = f"Expected 503 after shutdown, got {recorder.status}"
        raise AssertionError(errmsg)

    # A second shutdown does nothing
    bridge.shutdown()

    return


def test_failed_lifespan_startup_answers_503():
    """
        A startup the application reports as failed refuses every request.
    """
    app = LifespanApp(fail_startup=True)
    bridge = ASGIBridge(asgi_app=app)

    try:
        can_serve = bridge.startup()
        recorder, body = serve(bridge, make_environ())
    finally:
        bridge.shutdown()

    if can_serve is not False:
        errmsg = "Expected startup() to report that the bridge cannot serve"
        raise AssertionError(errmsg)

    if recorder.status != "503 Service Unavailable":
        errmsg = f"Expected 503 after a failed startup, got {recorder.status}"
        raise AssertionError(errmsg)

    if app.scopes != []:
        errmsg = "Expected the request not to reach the application"
        raise AssertionError(errmsg)

    return


def test_failed_lifespan_startup_is_reported():
    """
        lifespan_status and failure_message say why the bridge refuses requests.
    """
    bridge = ASGIBridge(asgi_app=LifespanApp(fail_startup=True))

    try:
        bridge.startup()
        status = bridge.lifespan_status
        message = bridge.failure_message
    finally:
        bridge.shutdown()

    if status != LIFESPAN_FAILED or message != "no database":
        errmsg = f"Expected a failed startup with its message, got {status} {message!r}"
        raise AssertionError(errmsg)

    return


def test_application_without_lifespan_is_served():
    """
        An application that rejects the lifespan scope is served all the same.
    """
    bridge = ASGIBridge(asgi_app=no_lifespan_app)

    try:
        recorder, body = serve(bridge, make_environ())
        status = bridge.lifespan_status
    finally:
        bridge.shutdown()

    if recorder.status != "204 No Content":
        errmsg = f"Expected 204, got {recorder.status}"
        raise AssertionError(errmsg)

    if status != LIFESPAN_UNSUPPORTED:
        errmsg = f"Expected lifespan status unsupported, got {status}"
        raise AssertionError(errmsg)

    return


def test_provider_is_called_when_the_bridge_starts():
    """
        An app_provider is resolved at the start, not at construction.
    """
    calls: List[int] = []

    def provider():
        calls.append(1)
        return no_lifespan_app

    bridge = ASGIBridge(app_provider=provider)

    if calls != []:
        errmsg = "Expected the provider not to be called by the constructor"
        raise AssertionError(errmsg)

    try:
        serve(bridge, make_environ())
        serve(bridge, make_environ())
    finally:
        bridge.shutdown()

    if calls != [1]:
        errmsg = f"Expected the provider to be called once, got {len(calls)} calls"
        raise AssertionError(errmsg)

    return


def test_worker_hooks_start_and_stop_the_bridge():
    """
        on_worker_start runs the startup, on_worker_exit the shutdown.
    """
    app = LifespanApp()
    bridge = ASGIBridge(asgi_app=app)

    bridge.on_worker_start(None)
    started = bridge.is_started
    bridge.on_worker_exit(None)

    if not started or app.events != ["lifespan.startup", "lifespan.shutdown"]:
        errmsg = f"Expected the worker hooks to run the lifespan, got {app.events}"
        raise AssertionError(errmsg)

    return


def test_semantic_error_of_the_lifespan_is_raised():
    """
        A SemanticError of the application is never turned into a failed startup.
    """
    async def app(scope, receive, send):
        await receive()
        raise SemanticError("the application is wired wrongly")

    bridge = ASGIBridge(asgi_app=app)

    try:
        bridge.startup()
    except SemanticError:
        return

    errmsg = "Expected the SemanticError to be raised by startup()"
    raise AssertionError(errmsg)


def test_forked_child_runs_its_own_lifespan():
    """
        A process forked after the bridge started runs a lifespan of its own.
    """
    if not hasattr(os, "fork"):
        raise SkipError("os.fork is not available on this platform.")

    app = LifespanApp()
    bridge = ASGIBridge(asgi_app=app)
    bridge.startup()

    read_fd, write_fd = os.pipe()

    try:
        pid = os.fork()

        if pid == 0:
            exit_code = 1
            try:
                recorder, body = serve(bridge, make_environ())
                child_events = ",".join(app.events)
                os.write(write_fd, f"{recorder.status}|{child_events}".encode("utf-8"))
                bridge.shutdown()
                exit_code = 0
            finally:
                os._exit(exit_code)

        os.close(write_fd)
        _, status = os.waitpid(pid, 0)
        with os.fdopen(read_fd, "rb") as reader:
            report = reader.read().decode("utf-8")
    finally:
        bridge.shutdown()

    if os.WEXITSTATUS(status) != 0:
        errmsg = f"The child process failed: {report!r}"
        raise AssertionError(errmsg)

    # The child inherited the parent's startup event and ran one of its own
    if report != "200 OK|lifespan.startup,lifespan.startup":
        errmsg = f"Expected the child to serve after its own startup, got {report!r}"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Scope
# =============================================================================

def test_scope_is_built_from_the_environ():
    """
        Method, path, query, headers, client and server reach the scope.
    """
    app = LifespanApp()
    bridge = ASGIBridge(asgi_app=app)

    environ = make_environ(
        method="POST",
        path="/caf\xc3\xa9",
        query="a=1&b=2",
        body=b"xyz",
        headers={"Content-Type": "text/plain", "X-Token": "abc"},
    )
    environ["SCRIPT_NAME"] = "/mount"
    environ["REQUEST_URI"] = "/mount/caf%C3%A9?a=1&b=2"

    try:
        serve(bridge, environ)
    finally:
        bridge.shutdown()

    scope = app.scopes[0]
    headers = dict(scope["headers"])

    expectations = [
        ("type", scope["type"], "http"),
        ("method", scope["method"], "POST"),
        ("path", scope["path"], "/café"),
        ("root_path", scope["root_path"], "/mount"),
        ("raw_path", scope["raw_path"], b"/mount/caf%C3%A9"),
        ("query_string", scope["query_string"], b"a=1&b=2"),
        ("http_version", scope["http_version"], "1.1"),
        ("scheme", scope["scheme"], "http"),
        ("client", scope["client"], ("10.1.2.3", 55555)),
        ("server", scope["server"], ("127.0.0.1", 8000)),
        ("content-type", headers.get(b"content-type"), b"text/plain"),
        ("content-length", headers.get(b"content-length"), b"3"),
        ("x-token", headers.get(b"x-token"), b"abc"),
    ]

    for name, actual, expected in expectations:
        if actual != expected:
            errmsg = f"Scope {name}: expected {expected!r}, got {actual!r}"
            raise AssertionError(errmsg)

    return


# =============================================================================
# Request body
# =============================================================================

def test_body_is_received_in_chunks():
    """
        The body is handed to receive() piece by piece, up to its Content-Length.
    """
    received: List[Tuple[int, bool]] = []

    async def app(scope, receive, send):
        if scope["type"] == "lifespan":
            raise RuntimeError("no lifespan")
        total = b""
        while True:
            message = await receive()
            received.append((len(message.get("body", b"")), message.get("more_body", False)))
            total += message.get("body", b"")
            if not message.get("more_body", False):
                break
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": str(len(total)).encode("ascii")})

    bridge = ASGIBridge(asgi_app=app, body_chunk_size=10)
    environ = make_environ(method="POST", body=b"a" * 25 + b"TRAILING", content_length=25)

    try:
        recorder, body = serve(bridge, environ)
    finally:
        bridge.shutdown()

    if body != b"25":
        errmsg = f"Expected the application to receive 25 bytes, got {body!r}"
        raise AssertionError(errmsg)

    if received != [(10, True), (10, True), (5, False)]:
        errmsg = f"Expected chunks of 10, 10 and 5 bytes, got {received}"
        raise AssertionError(errmsg)

    if environ["wsgi.input"].read() != b"TRAILING":
        errmsg = "Expected the bridge not to read beyond the Content-Length"
        raise AssertionError(errmsg)

    return


def test_body_is_read_only_as_far_as_the_application_asks():
    """
        An application that refuses a body after its first chunk stops the reading.
    """
    async def app(scope, receive, send):
        if scope["type"] == "lifespan":
            raise RuntimeError("no lifespan")
        await receive()
        await send({"type": "http.response.start", "status": 413, "headers": []})
        await send({"type": "http.response.body", "body": b"too large"})

    bridge = ASGIBridge(asgi_app=app, body_chunk_size=16)
    environ = make_environ(method="POST", body=b"b" * 1000)

    try:
        recorder, body = serve(bridge, environ)
    finally:
        bridge.shutdown()

    if recorder.status != "413 Request Entity Too Large":
        errmsg = f"Expected 413, got {recorder.status}"
        raise AssertionError(errmsg)

    if environ["wsgi.input"].tell() != 16:
        errmsg = f"Expected only the first chunk to be read, read {environ['wsgi.input'].tell()} bytes"
        raise AssertionError(errmsg)

    return


def test_body_that_ends_early_is_a_disconnect_and_the_read_error_is_raised():
    """
        A body shorter than its Content-Length is a client that went away.
    """
    messages: List[str] = []

    async def app(scope, receive, send):
        if scope["type"] == "lifespan":
            raise RuntimeError("no lifespan")
        while True:
            message = await receive()
            messages.append(message["type"])
            if message["type"] == "http.disconnect" or not message.get("more_body"):
                return

    bridge = ASGIBridge(asgi_app=app, body_chunk_size=4)
    environ = make_environ(method="POST", body=b"12345678", content_length=100)

    try:
        bridge(environ, StartResponseRecorder())
    except ConnectionResetError:
        pass
    else:
        errmsg = "Expected the read error to be raised to the server"
        raise AssertionError(errmsg)
    finally:
        bridge.shutdown()

    if messages[-1] != "http.disconnect":
        errmsg = f"Expected the application to see a disconnect, got {messages}"
        raise AssertionError(errmsg)

    return


def test_receive_after_the_body_waits_for_the_end_of_the_response():
    """
        A second receive() returns http.disconnect once the response is complete.
    """
    seen: List[str] = []

    async def app(scope, receive, send):
        if scope["type"] == "lifespan":
            raise RuntimeError("no lifespan")
        await receive()
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b"done"})
        message = await receive()
        seen.append(message["type"])

    bridge = ASGIBridge(asgi_app=app)

    try:
        serve(bridge, make_environ())
        deadline = time.monotonic() + 5.0
        while len(seen) == 0 and time.monotonic() < deadline:
            time.sleep(0.01)
    finally:
        bridge.shutdown()

    if seen != ["http.disconnect"]:
        errmsg = f"Expected http.disconnect after the response, got {seen}"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Response
# =============================================================================

def test_repeated_headers_are_kept_and_hop_by_hop_headers_dropped():
    """
        Every Set-Cookie field reaches the server; Connection is left to it.
    """
    async def app(scope, receive, send):
        if scope["type"] == "lifespan":
            raise RuntimeError("no lifespan")
        await send({
            "type": "http.response.start",
            "status": 200,
            "headers": [
                (b"set-cookie", b"a=1; Path=/"),
                (b"set-cookie", b"b=2; Path=/"),
                (b"connection", b"close"),
                (b"transfer-encoding", b"chunked"),
                (b"content-type", b"text/plain"),
            ],
        })
        await send({"type": "http.response.body", "body": b"x"})

    bridge = ASGIBridge(asgi_app=app)

    try:
        recorder, body = serve(bridge, make_environ())
    finally:
        bridge.shutdown()

    if recorder.header_values("set-cookie") != ["a=1; Path=/", "b=2; Path=/"]:
        errmsg = f"Expected both cookies, got {recorder.headers}"
        raise AssertionError(errmsg)

    names = [name.lower() for name, _ in recorder.headers]
    if "connection" in names or "transfer-encoding" in names:
        errmsg = f"Expected hop-by-hop headers to be dropped, got {recorder.headers}"
        raise AssertionError(errmsg)

    return


def test_body_is_streamed_and_send_waits_for_the_server():
    """
        Each chunk reaches the server before the application can send the next one.
    """
    sent_marks: List[int] = []

    async def app(scope, receive, send):
        if scope["type"] == "lifespan":
            raise RuntimeError("no lifespan")
        await send({"type": "http.response.start", "status": 200, "headers": []})
        for index in range(3):
            await send({"type": "http.response.body", "body": f"chunk{index}".encode("ascii"), "more_body": True})
            sent_marks.append(index)
        await send({"type": "http.response.body", "body": b"", "more_body": False})

    bridge = ASGIBridge(asgi_app=app)
    recorder = StartResponseRecorder()

    try:
        body_iterable = bridge(make_environ(), recorder)
        iterator = iter(body_iterable)

        first = next(iterator)
        time.sleep(0.2)
        marks_after_first = list(sent_marks)

        rest = list(iterator)
        body_iterable.close()
    finally:
        bridge.shutdown()

    if first != b"chunk0" or rest != [b"chunk1", b"chunk2"]:
        errmsg = f"Expected the chunks one by one, got {first!r} then {rest!r}"
        raise AssertionError(errmsg)

    if marks_after_first != []:
        errmsg = f"Expected send() to wait until the server took the chunk, got {marks_after_first}"
        raise AssertionError(errmsg)

    return


def test_head_request_drops_the_body_and_keeps_the_headers():
    """
        A HEAD response keeps its Content-Length but has no body.
    """
    async def app(scope, receive, send):
        if scope["type"] == "lifespan":
            raise RuntimeError("no lifespan")
        await send({"type": "http.response.start", "status": 200, "headers": [(b"content-length", b"5")]})
        await send({"type": "http.response.body", "body": b"hello"})

    bridge = ASGIBridge(asgi_app=app)

    try:
        recorder, body = serve(bridge, make_environ(method="HEAD"))
    finally:
        bridge.shutdown()

    if body != b"" or recorder.header_values("content-length") != ["5"]:
        errmsg = f"Expected no body and Content-Length 5, got {body!r} {recorder.headers}"
        raise AssertionError(errmsg)

    return


def test_exception_before_the_response_answers_500():
    """
        An application that raises without a response gets a 500.
    """
    async def app(scope, receive, send):
        if scope["type"] == "lifespan":
            raise RuntimeError("no lifespan")
        raise ValueError("broken handler")

    bridge = ASGIBridge(asgi_app=app)

    try:
        recorder, body = serve(bridge, make_environ())
    finally:
        bridge.shutdown()

    if recorder.status != "500 Internal Server Error":
        errmsg = f"Expected 500, got {recorder.status}"
        raise AssertionError(errmsg)

    return


def test_application_returning_without_a_response_answers_500():
    """
        An application that ends without starting a response gets a 500.
    """
    async def app(scope, receive, send):
        if scope["type"] == "lifespan":
            raise RuntimeError("no lifespan")
        return

    bridge = ASGIBridge(asgi_app=app)

    try:
        recorder, body = serve(bridge, make_environ())
    finally:
        bridge.shutdown()

    if recorder.status != "500 Internal Server Error":
        errmsg = f"Expected 500, got {recorder.status}"
        raise AssertionError(errmsg)

    return


def test_exception_after_the_response_started_breaks_the_body():
    """
        The server learns that the response is incomplete and closes the connection.
    """
    async def app(scope, receive, send):
        if scope["type"] == "lifespan":
            raise RuntimeError("no lifespan")
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b"part", "more_body": True})
        raise ValueError("failed in the middle")

    bridge = ASGIBridge(asgi_app=app)
    recorder = StartResponseRecorder()
    chunks: List[bytes] = []

    try:
        body_iterable = bridge(make_environ(), recorder)
        try:
            for chunk in body_iterable:
                chunks.append(chunk)
        except IncompleteResponse:
            pass
        else:
            errmsg = "Expected IncompleteResponse from the body iterator"
            raise AssertionError(errmsg)
        finally:
            body_iterable.close()
    finally:
        bridge.shutdown()

    if recorder.status != "200 OK" or chunks != [b"part"]:
        errmsg = f"Expected the started response and its first part, got {recorder.status} {chunks}"
        raise AssertionError(errmsg)

    return


def test_client_disconnect_reaches_the_application():
    """
        A server that stops iterating makes the next send() raise ClientDisconnected.
    """
    outcome: List[str] = []
    finished = threading.Event()

    async def app(scope, receive, send):
        if scope["type"] == "lifespan":
            raise RuntimeError("no lifespan")
        await send({"type": "http.response.start", "status": 200, "headers": []})
        try:
            for index in range(1000):
                await send({"type": "http.response.body", "body": b"tick", "more_body": True})
        except ClientDisconnected:
            outcome.append("disconnected")
        finally:
            finished.set()

    bridge = ASGIBridge(asgi_app=app)

    try:
        body_iterable = bridge(make_environ(), StartResponseRecorder())
        iterator = iter(body_iterable)
        next(iterator)
        next(iterator)
        # The client went away: the server closes the body without finishing it
        body_iterable.close()
        finished.wait(timeout=5.0)
    finally:
        bridge.shutdown()

    if outcome != ["disconnected"]:
        errmsg = f"Expected the application to see the disconnect, got {outcome}"
        raise AssertionError(errmsg)

    return


def test_request_timeout_answers_504():
    """
        An application that does not start its response in time gets a 504.
    """
    cancelled = threading.Event()

    async def app(scope, receive, send):
        import asyncio
        if scope["type"] == "lifespan":
            raise RuntimeError("no lifespan")
        try:
            await asyncio.sleep(30)
        except asyncio.CancelledError:
            cancelled.set()
            raise

    for bridge, environ in (
        (ASGIBridge(asgi_app=app, request_timeout=0.2), make_environ()),
        (ASGIBridge(asgi_app=app), dict(make_environ(), **{ENVIRON_REQUEST_TIMEOUT: 0.2})),
    ):
        cancelled.clear()
        started = time.monotonic()
        try:
            recorder, body = serve(bridge, environ)
        finally:
            bridge.shutdown()

        if recorder.status != "504 Gateway Timeout":
            errmsg = f"Expected 504, got {recorder.status}"
            raise AssertionError(errmsg)

        if time.monotonic() - started > 10.0 or not cancelled.is_set():
            errmsg = "Expected the handler to be cancelled at the timeout"
            raise AssertionError(errmsg)

    return


def test_semantic_error_of_a_request_is_raised():
    """
        A SemanticError raised while serving is not turned into a 500.
    """
    async def app(scope, receive, send):
        if scope["type"] == "lifespan":
            raise RuntimeError("no lifespan")
        raise SemanticError("wired wrongly")

    bridge = ASGIBridge(asgi_app=app)

    try:
        bridge(make_environ(), StartResponseRecorder())
    except SemanticError:
        return
    finally:
        bridge.shutdown()

    errmsg = "Expected the SemanticError to reach the server"
    raise AssertionError(errmsg)


def test_concurrent_requests_share_one_loop():
    """
        Requests from several server threads are served side by side.
    """
    import asyncio

    in_flight: List[int] = []
    peak: List[int] = [0]

    async def app(scope, receive, send):
        if scope["type"] == "lifespan":
            raise RuntimeError("no lifespan")
        in_flight.append(1)
        peak[0] = max(peak[0], len(in_flight))
        await asyncio.sleep(0.3)
        in_flight.pop()
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b"ok"})

    bridge = ASGIBridge(asgi_app=app)
    results: List[str] = []

    def one_request():
        recorder, _ = serve(bridge, make_environ())
        results.append(recorder.status)

    try:
        threads = [threading.Thread(target=one_request) for _ in range(5)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=10.0)
    finally:
        bridge.shutdown()

    if results != ["200 OK"] * 5:
        errmsg = f"Expected five 200 responses, got {results}"
        raise AssertionError(errmsg)

    if peak[0] < 2:
        errmsg = f"Expected the requests to overlap on the loop, peak was {peak[0]}"
        raise AssertionError(errmsg)

    return


if __name__ == "__main__":
    from ccai.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
