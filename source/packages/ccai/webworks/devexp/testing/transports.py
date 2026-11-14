"""
    Transports that carry a :class:`TestClient` request to an application.

    The test client builds a request (method, target, headers, body) and a
    transport delivers it in-process, without a socket:

    - :class:`ASGITransport` calls an ASGI application with a real
      ``http`` scope and ``receive``/``send`` callables, so routing,
      middleware, sessions and CSRF protection run exactly as they do
      under a server. This is the transport for the framework's own
      ``ASGIApplication``.
    - :class:`WSGITransport` calls a WSGI application with a PEP 3333
      ``environ`` and ``start_response``.
    - :class:`CallableTransport` calls a plain function with the signature
      ``(method, path, headers, body) -> (status_code, headers, body)``,
      which is convenient for unit tests of the client itself.

    Every transport returns the response as ``(status_code, headers,
    body_chunks)`` where *headers* is a list of ``(name, value)`` string
    tuples -- a list, because a response may carry several headers with
    the same name (``Set-Cookie``).
"""

import asyncio
import inspect
import io
import sys
import threading

from typing import Any, Callable, Dict, List, Optional, Tuple
from urllib.parse import unquote_to_bytes

from ccai.webworks.devexp.server.lifespanmanager import LifespanManager


HeaderList = List[Tuple[str, str]]
"""Headers as an ordered list of (name, value) string tuples."""

TransportResponse = Tuple[int, HeaderList, List[bytes]]
"""A transport result: status code, headers, and the body as it was sent, piece by piece."""

TRANSPORT_ASGI = "asgi"
"""Name of the ASGI transport."""

TRANSPORT_WSGI = "wsgi"
"""Name of the WSGI transport."""

TRANSPORT_CALLABLE = "callable"
"""Name of the plain-callable transport."""

DEFAULT_CLIENT_ADDRESS = ("testclient", 50000)
"""The client address reported to the application."""


class TransportError(Exception):
    """
        Raised when an application does not behave as its interface requires.

        For example an ASGI application that returns without sending a
        response, or a WSGI application that never calls ``start_response``.
    """


def detect_transport(app: Any) -> str:
    """
        Work out which interface an application implements.

        An application whose call is a coroutine function is ASGI. A
        synchronous callable that takes two arguments (``environ``,
        ``start_response``) is WSGI. Anything else is treated as the plain
        ``(method, path, headers, body)`` callable.

        :param app: The application object.

        :returns: One of :data:`TRANSPORT_ASGI`, :data:`TRANSPORT_WSGI` or
            :data:`TRANSPORT_CALLABLE`.
    """
    if inspect.iscoroutinefunction(app):
        return TRANSPORT_ASGI

    call_method = getattr(type(app), "__call__", None)

    if call_method is not None and inspect.iscoroutinefunction(call_method):
        return TRANSPORT_ASGI

    try:
        signature = inspect.signature(app)
    except (TypeError, ValueError):
        return TRANSPORT_CALLABLE

    positional_kinds = (
        inspect.Parameter.POSITIONAL_ONLY,
        inspect.Parameter.POSITIONAL_OR_KEYWORD,
    )

    positional_count = 0
    for parameter in signature.parameters.values():
        if parameter.kind in positional_kinds:
            positional_count += 1

    if positional_count == 2:
        return TRANSPORT_WSGI

    return TRANSPORT_CALLABLE


def split_target(target: str) -> Tuple[str, str]:
    """
        Split a request target into its path and query string.

        :param target: The path with an optional ``?query``.

        :returns: A tuple of (path, query) where the query has no leading ``?``.
    """
    question_pos = target.find("?")

    if question_pos >= 0:
        path = target[:question_pos]
        query = target[question_pos + 1:]
    else:
        path = target
        query = ""

    return path, query


def has_header(headers: HeaderList, name: str) -> bool:
    """
        Check whether a header list contains a header, ignoring case.

        :param headers: The header list.
        :param name: The header name to look for.

        :returns: ``True`` if the header is present.
    """
    lower_name = name.lower()

    for header_name, _header_value in headers:
        if header_name.lower() == lower_name:
            return True

    return False


# =============================================================================
# CallableTransport
# =============================================================================

class CallableTransport:
    """
        Transport for a plain ``(method, path, headers, body)`` callable.

        The callable receives the headers as a dictionary and returns
        ``(status_code, headers, body)`` where *headers* is a dictionary or
        a list of ``(name, value)`` tuples and *body* is ``bytes``.

        :param app: The application callable.
    """

    name = TRANSPORT_CALLABLE

    def __init__(self, app: Callable):
        """
            Construct a CallableTransport.

            :param app: The application callable.
        """
        self._app = app
        return

    def send(
        self,
        method: str,
        target: str,
        headers: HeaderList,
        body: bytes,
        scheme: str,
        host: str,
    ) -> TransportResponse:
        """
            Call the application with one request.

            :param method: The HTTP method.
            :param target: The path with its query string.
            :param headers: The request headers.
            :param body: The request body.
            :param scheme: The URL scheme of the request (unused).
            :param host: The host of the request (unused).

            :returns: The status code, response headers and body pieces.
        """
        header_dict: Dict[str, str] = {}
        for header_name, header_value in headers:
            header_dict[header_name] = header_value

        status_code, response_headers, response_body = self._app(
            method, target, header_dict, body,
        )

        if isinstance(response_headers, dict):
            header_list = [(str(key), str(value)) for key, value in response_headers.items()]
        else:
            header_list = [(str(key), str(value)) for key, value in response_headers]

        return status_code, header_list, [bytes(response_body)]

    def startup(self) -> None:
        """
            Nothing to start for a plain callable.
        """
        return

    def shutdown(self) -> None:
        """
            Nothing to shut down for a plain callable.
        """
        return

    def close(self) -> None:
        """
            Nothing to release for a plain callable.
        """
        return


# =============================================================================
# ASGITransport
# =============================================================================

class ASGITransport:
    """
        Transport that calls an ASGI application in-process.

        Each request builds an ASGI 3.0 ``http`` scope and runs the
        application to completion on an event loop owned by the transport.
        The loop runs in its own thread and lives as long as the transport,
        so the client works from synchronous tests and from tests that are
        themselves running inside an event loop, and state the application
        binds to its loop survives from one request to the next.

        ``receive`` delivers the request body once and then waits for the
        response to complete before it reports ``http.disconnect``, as a
        server does.

        :param app: The ASGI application.
        :param raise_app_exceptions: When ``True`` an exception raised by
            the application is re-raised in the test. When ``False`` it is
            turned into a ``500`` response, which is what a server would
            send.
    """

    name = TRANSPORT_ASGI

    def __init__(self, app: Any, raise_app_exceptions: bool = True):
        """
            Construct an ASGITransport.

            :param app: The ASGI application.
            :param raise_app_exceptions: Whether application exceptions
                propagate into the test.
        """
        self._app = app
        self._raise_app_exceptions = raise_app_exceptions
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None
        self._lifespan: Optional[LifespanManager] = None
        return

    # -------------------------------------------------------------------------
    # Event Loop
    # -------------------------------------------------------------------------

    def _ensure_loop(self) -> asyncio.AbstractEventLoop:
        """
            Start the transport's event loop thread on first use.

            :returns: The running event loop.
        """
        if self._loop is None:
            loop = asyncio.new_event_loop()

            thread = threading.Thread(
                target=loop.run_forever,
                name="testclient-asgi-loop",
                daemon=True,
            )
            thread.start()

            self._loop = loop
            self._thread = thread

        return self._loop

    def _run(self, coroutine: Any) -> Any:
        """
            Run a coroutine on the transport's loop and wait for its result.

            :param coroutine: The coroutine to run.

            :returns: The coroutine's result.
        """
        loop = self._ensure_loop()
        future = asyncio.run_coroutine_threadsafe(coroutine, loop)
        result = future.result()

        return result

    # -------------------------------------------------------------------------
    # Request
    # -------------------------------------------------------------------------

    def send(
        self,
        method: str,
        target: str,
        headers: HeaderList,
        body: bytes,
        scheme: str,
        host: str,
    ) -> TransportResponse:
        """
            Call the application with one request.

            :param method: The HTTP method.
            :param target: The path with its query string.
            :param headers: The request headers.
            :param body: The request body.
            :param scheme: The URL scheme of the request.
            :param host: The host (and optional port) of the request.

            :returns: The status code, response headers and body pieces.

            :raises TransportError: If the application returns without
                sending a complete response.
        """
        response = self._run(
            self._call_application(method, target, headers, body, scheme, host)
        )

        return response

    def _build_scope(
        self,
        method: str,
        target: str,
        headers: HeaderList,
        body: bytes,
        scheme: str,
        host: str,
    ) -> Dict[str, Any]:
        """
            Build the ASGI ``http`` scope for a request.

            ``Host`` and ``Content-Length`` headers are added when the test
            did not set them, as an HTTP client would.

            :param method: The HTTP method.
            :param target: The path with its query string.
            :param headers: The request headers.
            :param body: The request body.
            :param scheme: The URL scheme of the request.
            :param host: The host (and optional port) of the request.

            :returns: The scope dictionary.
        """
        path, query = split_target(target)

        raw_path = path.encode("utf-8")
        decoded_path = unquote_to_bytes(raw_path).decode("utf-8", errors="replace")

        request_headers = list(headers)

        if not has_header(request_headers, "host"):
            request_headers.insert(0, ("host", host))

        if len(body) > 0 and not has_header(request_headers, "content-length"):
            request_headers.append(("content-length", str(len(body))))

        scope_headers = []
        for header_name, header_value in request_headers:
            scope_headers.append([
                header_name.lower().encode("latin-1"),
                header_value.encode("latin-1"),
            ])

        server_host, separator, server_port_text = host.partition(":")

        if len(separator) > 0 and server_port_text.isdigit():
            server_port = int(server_port_text)
        elif scheme == "https":
            server_port = 443
        else:
            server_port = 80

        scope = {
            "type": "http",
            "asgi": {"version": "3.0", "spec_version": "2.3"},
            "http_version": "1.1",
            "method": method.upper(),
            "scheme": scheme,
            "path": decoded_path,
            "raw_path": raw_path,
            "query_string": query.encode("utf-8"),
            "root_path": "",
            "headers": scope_headers,
            "server": [server_host, server_port],
            "client": list(DEFAULT_CLIENT_ADDRESS),
        }

        return scope

    async def _call_application(
        self,
        method: str,
        target: str,
        headers: HeaderList,
        body: bytes,
        scheme: str,
        host: str,
    ) -> TransportResponse:
        """
            Run the application for one request and collect its response.

            :param method: The HTTP method.
            :param target: The path with its query string.
            :param headers: The request headers.
            :param body: The request body.
            :param scheme: The URL scheme of the request.
            :param host: The host (and optional port) of the request.

            :returns: The status code, response headers and body pieces.
        """
        scope = self._build_scope(method, target, headers, body, scheme, host)

        state: Dict[str, Any] = {
            "request_delivered": False,
            "status": None,
            "headers": [],
            "chunks": [],
            "complete": False,
        }
        response_complete = asyncio.Event()

        async def receive() -> Dict[str, Any]:
            """
                ASGI receive callable: the body once, then the disconnect.

                :returns: The next ASGI message.
            """
            if not state["request_delivered"]:
                state["request_delivered"] = True
                message = {"type": "http.request", "body": body, "more_body": False}
            else:
                await response_complete.wait()
                message = {"type": "http.disconnect"}

            return message

        async def send(message: Dict[str, Any]) -> None:
            """
                ASGI send callable: records the response as it is sent.

                :param message: The ASGI message from the application.
            """
            message_type = message.get("type", "")

            if message_type == "http.response.start":
                state["status"] = message.get("status", 500)

                for header_pair in message.get("headers", []):
                    header_name = header_pair[0]
                    header_value = header_pair[1]

                    if isinstance(header_name, bytes):
                        header_name = header_name.decode("latin-1")
                    if isinstance(header_value, bytes):
                        header_value = header_value.decode("latin-1")

                    state["headers"].append((header_name, header_value))

            elif message_type == "http.response.body":
                if state["status"] is None:
                    errmsg = "The application sent http.response.body before http.response.start."
                    raise TransportError(errmsg)

                piece = message.get("body", b"")
                if isinstance(piece, str):
                    piece = piece.encode("utf-8")

                if len(piece) > 0:
                    state["chunks"].append(bytes(piece))

                if not message.get("more_body", False):
                    state["complete"] = True
                    response_complete.set()

            return

        try:
            await self._app(scope, receive, send)
        except TransportError:
            raise
        except Exception as err:
            if self._raise_app_exceptions:
                raise

            if not state["complete"]:
                error_text = "{}: {}".format(type(err).__name__, err).encode("utf-8")
                state["status"] = 500
                state["headers"] = [("content-type", "text/plain; charset=utf-8")]
                state["chunks"] = [error_text]
                state["complete"] = True
        finally:
            response_complete.set()

        if not state["complete"]:
            errmsg = "The ASGI application returned without sending a complete response for {} {}.".format(
                method, target
            )
            raise TransportError(errmsg)

        return state["status"], state["headers"], state["chunks"]

    # -------------------------------------------------------------------------
    # Lifespan
    # -------------------------------------------------------------------------

    def startup(self) -> None:
        """
            Send the application its ``lifespan.startup`` event.

            :raises TransportError: If the application reports that its
                startup failed.
        """
        self._lifespan = LifespanManager(self._app)
        self._run(self._lifespan.startup())

        if self._lifespan.startup_failed:
            errmsg = "The application's lifespan startup failed: {}".format(
                self._lifespan.failure_message
            )
            raise TransportError(errmsg)

        return

    def shutdown(self) -> None:
        """
            Send the application its ``lifespan.shutdown`` event, if it was started.
        """
        if self._lifespan is not None:
            self._run(self._lifespan.shutdown())
            self._lifespan = None

        return

    def close(self) -> None:
        """
            Stop the transport's event loop thread.
        """
        loop = self._loop
        thread = self._thread

        self._loop = None
        self._thread = None

        if loop is not None:
            loop.call_soon_threadsafe(loop.stop)

            if thread is not None:
                thread.join(timeout=5.0)

            if not loop.is_running():
                loop.close()

        return


# =============================================================================
# WSGITransport
# =============================================================================

class WSGITransport:
    """
        Transport that calls a WSGI application in-process.

        Each request builds a PEP 3333 ``environ`` and collects the status,
        the headers and the body the application produces.

        :param app: The WSGI application.
        :param raise_app_exceptions: When ``True`` an exception raised by
            the application is re-raised in the test. When ``False`` it is
            turned into a ``500`` response.
    """

    name = TRANSPORT_WSGI

    def __init__(self, app: Callable, raise_app_exceptions: bool = True):
        """
            Construct a WSGITransport.

            :param app: The WSGI application.
            :param raise_app_exceptions: Whether application exceptions
                propagate into the test.
        """
        self._app = app
        self._raise_app_exceptions = raise_app_exceptions
        return

    def _build_environ(
        self,
        method: str,
        target: str,
        headers: HeaderList,
        body: bytes,
        scheme: str,
        host: str,
    ) -> Dict[str, Any]:
        """
            Build the WSGI environ for a request.

            :param method: The HTTP method.
            :param target: The path with its query string.
            :param headers: The request headers.
            :param body: The request body.
            :param scheme: The URL scheme of the request.
            :param host: The host (and optional port) of the request.

            :returns: The environ dictionary.
        """
        path, query = split_target(target)

        server_name, separator, server_port_text = host.partition(":")

        if len(separator) > 0 and server_port_text.isdigit():
            server_port = server_port_text
        elif scheme == "https":
            server_port = "443"
        else:
            server_port = "80"

        environ: Dict[str, Any] = {
            "REQUEST_METHOD": method.upper(),
            "SCRIPT_NAME": "",
            # PEP 3333: the path is percent-decoded and carried as Latin-1.
            "PATH_INFO": unquote_to_bytes(path.encode("utf-8")).decode("latin-1"),
            "QUERY_STRING": query,
            "SERVER_NAME": server_name,
            "SERVER_PORT": server_port,
            "SERVER_PROTOCOL": "HTTP/1.1",
            "REMOTE_ADDR": DEFAULT_CLIENT_ADDRESS[0],
            "REMOTE_PORT": str(DEFAULT_CLIENT_ADDRESS[1]),
            "HTTP_HOST": host,
            "CONTENT_LENGTH": str(len(body)),
            "wsgi.version": (1, 0),
            "wsgi.url_scheme": scheme,
            "wsgi.input": io.BytesIO(body),
            "wsgi.errors": sys.stderr,
            "wsgi.multithread": False,
            "wsgi.multiprocess": False,
            "wsgi.run_once": False,
        }

        for header_name, header_value in headers:
            lower_name = header_name.lower()

            if lower_name == "content-type":
                environ["CONTENT_TYPE"] = header_value
            elif lower_name == "content-length":
                environ["CONTENT_LENGTH"] = header_value
            else:
                key = "HTTP_" + header_name.upper().replace("-", "_")

                if key in environ and lower_name != "host":
                    # Repeated headers are joined, cookies with "; ".
                    joiner = "; " if lower_name == "cookie" else ","
                    environ[key] = environ[key] + joiner + header_value
                else:
                    environ[key] = header_value

        return environ

    def send(
        self,
        method: str,
        target: str,
        headers: HeaderList,
        body: bytes,
        scheme: str,
        host: str,
    ) -> TransportResponse:
        """
            Call the application with one request.

            :param method: The HTTP method.
            :param target: The path with its query string.
            :param headers: The request headers.
            :param body: The request body.
            :param scheme: The URL scheme of the request.
            :param host: The host (and optional port) of the request.

            :returns: The status code, response headers and body pieces.

            :raises TransportError: If the application never calls
                ``start_response``.
        """
        environ = self._build_environ(method, target, headers, body, scheme, host)

        state: Dict[str, Any] = {"status": None, "headers": [], "chunks": []}

        def start_response(status: str, response_headers: List[Tuple[str, str]], exc_info: Any = None) -> Callable:
            """
                WSGI start_response callable.

                :param status: The status line, such as ``"200 OK"``.
                :param response_headers: The response headers.
                :param exc_info: Exception information when the application
                    replaces a response it had started.

                :returns: The legacy ``write`` callable.
            """
            state["status"] = int(status.split(" ", 1)[0])
            state["headers"] = [(str(key), str(value)) for key, value in response_headers]

            def write(data: bytes) -> None:
                state["chunks"].append(bytes(data))
                return

            return write

        try:
            result = self._app(environ, start_response)

            try:
                for piece in result:
                    if len(piece) > 0:
                        state["chunks"].append(bytes(piece))
            finally:
                close_method = getattr(result, "close", None)
                if close_method is not None:
                    close_method()
        except Exception as err:
            if self._raise_app_exceptions:
                raise

            error_text = "{}: {}".format(type(err).__name__, err).encode("utf-8")
            state["status"] = 500
            state["headers"] = [("Content-Type", "text/plain; charset=utf-8")]
            state["chunks"] = [error_text]

        if state["status"] is None:
            errmsg = "The WSGI application did not call start_response for {} {}.".format(method, target)
            raise TransportError(errmsg)

        return state["status"], state["headers"], state["chunks"]

    def startup(self) -> None:
        """
            WSGI has no lifespan protocol; nothing to start.
        """
        return

    def shutdown(self) -> None:
        """
            WSGI has no lifespan protocol; nothing to shut down.
        """
        return

    def close(self) -> None:
        """
            Nothing to release for a WSGI application.
        """
        return


def create_transport(app: Any, transport: Optional[str] = None, raise_app_exceptions: bool = True) -> Any:
    """
        Create the transport for an application.

        :param app: The application object.
        :param transport: The transport name, or ``None`` to detect it from
            the application (see :func:`detect_transport`).
        :param raise_app_exceptions: Whether application exceptions
            propagate into the test.

        :returns: A transport instance.

        :raises ValueError: If the transport name is not known.
    """
    if transport is None:
        transport = detect_transport(app)

    if transport == TRANSPORT_ASGI:
        instance = ASGITransport(app, raise_app_exceptions=raise_app_exceptions)
    elif transport == TRANSPORT_WSGI:
        instance = WSGITransport(app, raise_app_exceptions=raise_app_exceptions)
    elif transport == TRANSPORT_CALLABLE:
        instance = CallableTransport(app)
    else:
        errmsg = "Unknown transport '{}'. Expected '{}', '{}' or '{}'.".format(
            transport, TRANSPORT_ASGI, TRANSPORT_WSGI, TRANSPORT_CALLABLE
        )
        raise ValueError(errmsg)

    return instance
