"""
    WSGI to ASGI bridge module.

    This module provides the ASGIBridge class, a PEP 3333 application that
    serves an ASGI 3.0 application. It is how a WebApplication, which is built
    as an ASGI application, is served by a WSGI server: the built-in
    WSGIServer, the production server, or an external server such as Gunicorn.
    Serving through the bridge runs the application's own ASGI stack, so the
    routing, the middleware, authentication, sessions, CSRF protection, the
    request body limit, the error handlers and the lifespan handlers behave
    exactly as they do under an ASGI server.

    One event loop runs per process, on a thread of its own. Each WSGI request
    runs the ASGI application as a task on that loop while the thread the
    server called the bridge on waits for it and does the I/O:

    - the request body is read from ``wsgi.input`` on the server's thread, one
      chunk each time the application calls ``receive()``, so a body limit the
      application enforces stops the reading as soon as it is passed and the
      body is never collected by the bridge,
    - the response is handed to the server chunk by chunk as the application
      sends it, and ``send()`` returns only when the server has taken the
      chunk, so a streaming response is streamed and a slow client slows the
      application down instead of filling memory,
    - the lifespan startup of the application runs once per process, before
      the first request is served (or when a server starts a worker process
      and calls :meth:`ASGIBridge.on_worker_start`); its shutdown runs when
      the server stops the worker (:meth:`ASGIBridge.on_worker_exit`), when
      :meth:`ASGIBridge.shutdown` is called, or when the process exits.

    A process that forks after the bridge started (a pre-fork server that
    loaded the application first) starts a fresh loop and a fresh lifespan in
    the child; nothing of the parent's loop is used there.
"""

import asyncio
import atexit
import inspect
import logging
import os
import queue
import threading
import weakref

from typing import Any, Awaitable, Callable, Dict, Iterable, List, Optional, Tuple
from urllib.parse import quote, urlsplit

from ccai.errors.exceptions import SemanticError

from ccai.webworks.wsgi.constants import ENVIRON_REQUEST_TIMEOUT, HTTP_STATUS_PHRASES
from ccai.webworks.wsgi.exceptions import IncompleteResponse


logger = logging.getLogger(__name__)


ASGICallable = Callable[[Dict[str, Any], Callable[[], Awaitable[Dict[str, Any]]],
                         Callable[[Dict[str, Any]], Awaitable[None]]], Awaitable[None]]


# Size of the pieces 'wsgi.input' is read in for receive()
DEFAULT_BODY_CHUNK_SIZE: int = 65536

# Seconds the application is given to answer the lifespan events
DEFAULT_STARTUP_TIMEOUT: float = 60.0
DEFAULT_SHUTDOWN_TIMEOUT: float = 30.0

# Seconds the waiting server thread sleeps between checks that the loop
# thread is still alive
_EVENT_POLL_SECONDS: float = 1.0

# Headers that describe one connection and must not be passed to a WSGI
# server, PEP 3333 leaves them to the server.
HOP_BY_HOP_HEADERS = frozenset({
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
})

# Outcomes of the lifespan startup in one process
LIFESPAN_NOT_STARTED = "not-started"
LIFESPAN_COMPLETE = "complete"
LIFESPAN_UNSUPPORTED = "unsupported"
LIFESPAN_FAILED = "failed"

# Events the loop thread hands to the server thread of a request
_EVENT_READ = "read"
_EVENT_START = "start"
_EVENT_BODY = "body"
_EVENT_DONE = "done"

_DISCONNECT_MESSAGE: Dict[str, Any] = {"type": "http.disconnect"}


# Every bridge of the process, so that a fork can reset them in the child
_BRIDGES: "weakref.WeakSet[ASGIBridge]" = weakref.WeakSet()


def _reset_bridges_after_fork() -> None:
    """
        Forget the per-process state of every bridge in a forked child.

        The loop thread of the parent does not exist in the child, so its
        loop must not be used there, and a lock another thread of the parent
        held at the moment of the fork would never be released.
    """
    for bridge in list(_BRIDGES):
        bridge._forget_runtime_after_fork()
    return


if hasattr(os, "register_at_fork"):
    os.register_at_fork(after_in_child=_reset_bridges_after_fork)


def is_asgi_application(candidate: Any) -> bool:
    """
        Tell whether an object is an ASGI application.

        An ASGI application is an async function, or an object whose
        ``__call__`` is an async function, taking scope, receive and send.

        :param candidate: The object to look at.

        :returns: True if calling the object returns a coroutine.
    """
    rtnval = False

    if inspect.iscoroutinefunction(candidate):
        rtnval = True
    elif callable(candidate):
        call_method = getattr(candidate, "__call__", None)
        if call_method is not None and inspect.iscoroutinefunction(call_method):
            rtnval = True

    return rtnval


def _resolve_future(future: "asyncio.Future", result: Any = None, error: Optional[BaseException] = None) -> None:
    """
        Settle a loop future, unless it has been settled or cancelled already.

        Runs on the loop thread, scheduled with ``call_soon_threadsafe``.

        :param future: The future to settle.
        :param result: The result to set when no error is given.
        :param error: The exception to set instead of a result.
    """
    if not future.done():
        if error is not None:
            future.set_exception(error)
        else:
            future.set_result(result)
    return


def _status_line(status_code: int) -> str:
    """
        Build a WSGI status string from a status code.

        :param status_code: HTTP status code.

        :returns: The status string, for example "200 OK".
    """
    reason = HTTP_STATUS_PHRASES.get(status_code, "Unknown")
    rtnval = f"{status_code} {reason}"
    return rtnval


def _wsgi_text_to_bytes(value: Any) -> bytes:
    """
        Turn a WSGI native string into the bytes it carries.

        PEP 3333 carries request data in strings whose characters are the
        bytes of the request (latin-1).

        :param value: The WSGI string.

        :returns: The bytes. A string a server filled with characters beyond
            latin-1, against PEP 3333, is encoded as UTF-8.
    """
    text = str(value)
    try:
        rtnval = text.encode("latin-1")
    except UnicodeEncodeError:
        rtnval = text.encode("utf-8")
    return rtnval


def _wsgi_text_to_str(value: Any) -> str:
    """
        Turn a WSGI native string into the text it stands for.

        ASGI carries the decoded UTF-8 text of a path.

        :param value: The WSGI string.

        :returns: The decoded text. Bytes that are not UTF-8 become U+FFFD.
    """
    rtnval = _wsgi_text_to_bytes(value).decode("utf-8", errors="replace")
    return rtnval


class _ProcessRuntime:
    """
        What a bridge runs in one process: the loop, its thread, the ASGI
        application and the outcome of the lifespan startup.
    """

    def __init__(self, pid: int):
        """
            Construct the runtime of a process.

            :param pid: The process the runtime belongs to.
        """
        self.pid = pid
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.thread: Optional[threading.Thread] = None
        self.asgi_app: Optional[ASGICallable] = None
        self.lifespan_status: str = LIFESPAN_NOT_STARTED
        self.failure_message: Optional[str] = None
        self.lifespan_task: Optional["asyncio.Future"] = None
        self.lifespan_receive: Optional[asyncio.Queue] = None
        self.lifespan_send: Optional[asyncio.Queue] = None
        # The lifespan 'state' of ASGI 2.3: filled by the startup handlers,
        # a shallow copy of it is given to every request.
        self.app_state: Dict[str, Any] = {}
        self.active_tasks: "set[asyncio.Future]" = set()
        self.stopped: bool = False
        return

    @property
    def can_serve(self) -> bool:
        """
            Check whether requests are passed to the application.

            :returns: True when the lifespan startup completed, or the
                application does not take part in the lifespan protocol, and
                the runtime has not been stopped.
        """
        started = self.lifespan_status in (LIFESPAN_COMPLETE, LIFESPAN_UNSUPPORTED)
        rtnval = started and not self.stopped
        return rtnval


class _Exchange:
    """
        The two halves of one request: the ASGI side on the loop thread and
        the WSGI side on the server's thread.

        The loop side posts events to a thread-safe queue: a request for the
        next piece of the body, the response start, a body chunk, and the end
        of the application task. The server's thread takes them in order and
        answers each one, so every blocking read and write stays on the
        server's thread and the loop never waits for a socket.
    """

    def __init__(
        self,
        environ: Dict[str, Any],
        loop: asyncio.AbstractEventLoop,
        chunk_size: int,
        loop_thread: Optional[threading.Thread],
    ):
        """
            Construct the exchange of one request.

            :param environ: The WSGI environ of the request.
            :param loop: The loop the application runs on.
            :param chunk_size: Size of the pieces the body is read in.
            :param loop_thread: The thread that runs the loop.
        """
        self._environ = environ
        self._loop = loop
        self._chunk_size = chunk_size
        self._loop_thread = loop_thread
        self._events: "queue.Queue[Tuple[Any, ...]]" = queue.Queue()
        self._lock = threading.Lock()
        self._closed = False

        # Request body, read on the server's thread
        self._input = environ.get("wsgi.input")
        self._remaining = self._content_length(environ)
        self._input_terminated = environ.get("wsgi.input_terminated", False) is True
        self._input_exhausted = False
        self.read_error: Optional[BaseException] = None

        # Loop side
        self._body_received = False
        self._start_sent = False
        self._body_finished = False
        self.timed_out = False
        self.started = asyncio.Event()
        self._disconnected = asyncio.Event()
        return

    # ------------------------------------------------------------------
    # Loop side
    # ------------------------------------------------------------------

    async def receive(self) -> Dict[str, Any]:
        """
            The ASGI receive callable of the request.

            Hands out the request body piece by piece. Once the body has been
            received, a further call waits until the response has been
            completed or the client has gone, and then reports the disconnect.

            :returns: An ``http.request`` or ``http.disconnect`` message.
        """
        if self._body_received:
            await self._disconnected.wait()
            return dict(_DISCONNECT_MESSAGE)

        reply = self._loop.create_future()
        if not self._post((_EVENT_READ, reply)):
            self._body_received = True
            return dict(_DISCONNECT_MESSAGE)

        message = await reply

        if message.get("type") == "http.disconnect" or message.get("more_body", False) is False:
            self._body_received = True

        return message

    async def send(self, message: Dict[str, Any]) -> None:
        """
            The ASGI send callable of the request.

            The response start is passed on at once. A body chunk is passed on
            and the call returns when the server has taken it.

            :param message: An ``http.response.start`` or ``http.response.body``
                message.

            :raises ClientDisconnected: If the client is gone, the response
                will never reach it.
            :raises RuntimeError: If the messages break the ASGI protocol.
        """
        # Imported here: the asgi package imports the wsgi package
        from ccai.webworks.asgi.exceptions import ClientDisconnected

        message_type = message.get("type", "")

        if message_type == "http.response.start":
            if self._start_sent:
                errmsg = "The ASGI application sent 'http.response.start' twice."
                raise RuntimeError(errmsg)

            self._start_sent = True
            self.started.set()

            status = int(message["status"])
            headers = list(message.get("headers", []))

            if not self._post((_EVENT_START, status, headers)):
                raise ClientDisconnected("The client disconnected before the response started.")

        elif message_type == "http.response.body":
            if not self._start_sent:
                errmsg = "The ASGI application sent a response body before 'http.response.start'."
                raise RuntimeError(errmsg)

            if self._body_finished:
                errmsg = "The ASGI application sent a response body after the response was complete."
                raise RuntimeError(errmsg)

            body = message.get("body", b"")
            more_body = message.get("more_body", False) is True

            if not more_body:
                self._body_finished = True

            acknowledged = self._loop.create_future()
            if not self._post((_EVENT_BODY, bytes(body), more_body, acknowledged)):
                raise ClientDisconnected("The client disconnected during the response.")

            await acknowledged

        else:
            errmsg = f"The ASGI application sent an unsupported message type {message_type!r}."
            raise RuntimeError(errmsg)

        return

    def _post(self, event: Tuple[Any, ...]) -> bool:
        """
            Hand an event to the server's thread.

            :param event: The event.

            :returns: False if the server's side has closed and will not take
                the event.
        """
        with self._lock:
            if self._closed:
                rtnval = False
            else:
                self._events.put(event)
                rtnval = True
        return rtnval

    # ------------------------------------------------------------------
    # Server side
    # ------------------------------------------------------------------

    def _call_on_loop(self, callback: Callable[..., Any], *args: Any) -> None:
        """
            Schedule a callback on the loop of the request from the server's thread.

            When the bridge has been shut down and its loop closed, nothing on
            the loop waits for the callback any more and it is dropped.

            :param callback: The callback.
            :param args: Its arguments.
        """
        if not self._loop.is_closed():
            self._loop.call_soon_threadsafe(callback, *args)
        return

    def post_done(self, task_future: Any) -> None:
        """
            Report the end of the application task to the server's thread.

            Called from the loop thread when the task future is settled.

            :param task_future: The concurrent future of the task.
        """
        posted = self._post((_EVENT_DONE, task_future))

        if not posted and not task_future.cancelled():
            # The response is complete and nobody waits for the task any
            # more. An error it raised afterwards, in a background task for
            # example, would otherwise go unseen.
            error = task_future.exception()
            if error is not None:
                logger.error(
                    "ASGI bridge: the application raised %s after its response was complete",
                    type(error).__name__,
                    exc_info=(type(error), error, error.__traceback__),
                )
        return

    def next_event(self) -> Tuple[Any, ...]:
        """
            Wait for the next event from the loop side.

            :returns: The event.

            :raises IncompleteResponse: If the loop thread has died, nothing
                will ever arrive.
        """
        while True:
            try:
                rtnval = self._events.get(timeout=_EVENT_POLL_SECONDS)
                break
            except queue.Empty:
                if self._loop_thread is not None and not self._loop_thread.is_alive():
                    errmsg = "The event loop of the ASGI bridge stopped while a request was being served."
                    raise IncompleteResponse(errmsg)
        return rtnval

    def serve_read(self, reply: "asyncio.Future") -> None:
        """
            Read the next piece of the request body and hand it to receive().

            Runs on the server's thread. A failed read, or a body that ends
            before its Content-Length, is reported to the application as a
            disconnect; the error is kept for the server.

            :param reply: The loop future receive() waits on.
        """
        message: Dict[str, Any]

        try:
            message = self._read_body_message()
        except Exception as read_err:
            # The client went away or stalled while the body was being read.
            # The application learns it as a disconnect, the server gets the
            # error once the application has finished.
            self.read_error = read_err
            message = dict(_DISCONNECT_MESSAGE)

        self._call_on_loop(_resolve_future, reply, message)
        return

    def _read_body_message(self) -> Dict[str, Any]:
        """
            Read one piece of the request body.

            The body is read only up to its Content-Length. A request without
            one has a body only when the server marked 'wsgi.input' as
            terminated, as PEP 3333 asks.

            :returns: An ``http.request`` or ``http.disconnect`` message.
        """
        if self._input_exhausted or self._input is None:
            rtnval = {"type": "http.request", "body": b"", "more_body": False}
            return rtnval

        if self._remaining is None:
            if not self._input_terminated:
                self._input_exhausted = True
                rtnval = {"type": "http.request", "body": b"", "more_body": False}
                return rtnval

            chunk = self._input.read(self._chunk_size)
            if len(chunk) == 0:
                self._input_exhausted = True
                rtnval = {"type": "http.request", "body": b"", "more_body": False}
            else:
                rtnval = {"type": "http.request", "body": chunk, "more_body": True}
            return rtnval

        if self._remaining <= 0:
            self._input_exhausted = True
            rtnval = {"type": "http.request", "body": b"", "more_body": False}
            return rtnval

        size = min(self._chunk_size, self._remaining)
        chunk = self._input.read(size)

        if len(chunk) == 0:
            # The body ended before its Content-Length: the client is gone
            self._input_exhausted = True
            errmsg = f"The request body ended {self._remaining} bytes before its Content-Length."
            self.read_error = ConnectionResetError(errmsg)
            rtnval = dict(_DISCONNECT_MESSAGE)
            return rtnval

        self._remaining -= len(chunk)
        more_body = self._remaining > 0
        if not more_body:
            self._input_exhausted = True

        rtnval = {"type": "http.request", "body": chunk, "more_body": more_body}
        return rtnval

    def acknowledge(self, acknowledged: "asyncio.Future") -> None:
        """
            Tell send() that the server has taken a body chunk.

            :param acknowledged: The loop future send() waits on.
        """
        self._call_on_loop(_resolve_future, acknowledged, None)
        return

    def fail_acknowledgement(self, acknowledged: "asyncio.Future") -> None:
        """
            Tell send() that a body chunk will not reach the client.

            :param acknowledged: The loop future send() waits on.
        """
        from ccai.webworks.asgi.exceptions import ClientDisconnected

        error = ClientDisconnected("The client disconnected during the response.")
        self._call_on_loop(_resolve_future, acknowledged, None, error)
        return

    def close(self, client_gone: bool) -> None:
        """
            End the server's side of the request.

            Events still queued are answered, so the loop side never waits for
            a server thread that has moved on: a pending read gets a
            disconnect and a pending body chunk fails with ClientDisconnected
            when the client is gone. From now on receive() reports the
            disconnect.

            :param client_gone: True if the response did not reach its end,
                because the client disconnected or the server stopped it.
        """
        from ccai.webworks.asgi.exceptions import ClientDisconnected

        with self._lock:
            if self._closed:
                return
            self._closed = True

        while True:
            try:
                event = self._events.get_nowait()
            except queue.Empty:
                break

            kind = event[0]
            if kind == _EVENT_READ:
                self._call_on_loop(_resolve_future, event[1], dict(_DISCONNECT_MESSAGE))
            elif kind == _EVENT_BODY:
                if client_gone:
                    error = ClientDisconnected("The client disconnected during the response.")
                    self._call_on_loop(_resolve_future, event[3], None, error)
                else:
                    self._call_on_loop(_resolve_future, event[3], None)

        self._call_on_loop(self._disconnected.set)
        return

    @staticmethod
    def _content_length(environ: Dict[str, Any]) -> Optional[int]:
        """
            Read the Content-Length of the request from the environ.

            :param environ: The WSGI environ.

            :returns: The length, or None when the request does not state one.
        """
        raw_value = environ.get("CONTENT_LENGTH", "")
        rtnval: Optional[int] = None

        if raw_value is not None and str(raw_value).strip() != "":
            try:
                rtnval = int(str(raw_value).strip())
            except ValueError:
                rtnval = 0
            if rtnval < 0:
                rtnval = 0

        return rtnval


class _ResponseBody:
    """
        The WSGI response iterable of a bridged request.

        Each item is a body chunk the application sent. The chunk the server
        took last is acknowledged when the server asks for the next one, so
        send() returns once the chunk has been written. close() ends the
        exchange; a response the server stopped early is reported to the
        application as a disconnect.
    """

    def __init__(self, exchange: _Exchange, discard_body: bool):
        """
            Construct the body iterable.

            :param exchange: The exchange of the request.
            :param discard_body: True for a HEAD request: the chunks are taken
                from the application and dropped.
        """
        self._exchange = exchange
        self._discard_body = discard_body
        self._pending_ack: Optional["asyncio.Future"] = None
        self._final_seen = False
        self._finished = False
        self._closed = False
        return

    def __iter__(self) -> "_ResponseBody":
        """
            :returns: The iterable itself.
        """
        return self

    def __next__(self) -> bytes:
        """
            Wait for the next body chunk of the application.

            :returns: The next non-empty chunk.

            :raises StopIteration: When the application sent the end of the body.
            :raises IncompleteResponse: If the application stopped before the
                end of the body; the server closes the connection.
        """
        if self._pending_ack is not None:
            self._exchange.acknowledge(self._pending_ack)
            self._pending_ack = None

        if self._finished or self._final_seen:
            self._finished = True
            raise StopIteration

        while True:
            event = self._exchange.next_event()
            kind = event[0]

            if kind == _EVENT_READ:
                self._exchange.serve_read(event[1])
                continue

            if kind == _EVENT_BODY:
                body, more_body, acknowledged = event[1], event[2], event[3]

                if not more_body:
                    self._final_seen = True

                if len(body) > 0 and not self._discard_body:
                    self._pending_ack = acknowledged
                    return body

                self._exchange.acknowledge(acknowledged)

                if not more_body:
                    self._finished = True
                    raise StopIteration

                continue

            if kind == _EVENT_DONE:
                self._finished = True
                task_future = event[1]
                error = None
                if not task_future.cancelled():
                    error = task_future.exception()

                if error is not None and not isinstance(error, Exception):
                    # ConfigurationError, SemanticError and their kin end the run
                    raise error

                errmsg = "The ASGI application ended the response before it sent the end of the body."
                if error is not None:
                    raise IncompleteResponse(errmsg) from error
                raise IncompleteResponse(errmsg)

            # A second response start is refused by send(), nothing else is posted
            errmsg = f"The ASGI bridge received an unexpected event {kind!r}."
            raise IncompleteResponse(errmsg)

    def close(self) -> None:
        """
            End the response.

            Called by the server when it is done with the iterable, at the end
            of the body or earlier when the client went away or writing failed.
        """
        if self._closed:
            return
        self._closed = True

        client_gone = not self._final_seen

        if self._pending_ack is not None:
            if client_gone:
                # The server stopped before it asked for the next chunk, the
                # chunk it took last may not have been written.
                self._exchange.fail_acknowledgement(self._pending_ack)
            else:
                self._exchange.acknowledge(self._pending_ack)
            self._pending_ack = None

        self._exchange.close(client_gone=client_gone)
        return


class ASGIBridge:
    """
        A WSGI application that serves an ASGI application.

        The bridge is created for an ASGI application, or for a provider that
        returns it. The provider is called when the bridge starts in a
        process, so an application whose outermost layer changes until it is
        served (``WebApplication.asgi_app`` once authentication middleware is
        configured) is resolved as it is served.

        Requests are refused with 503 Service Unavailable when the lifespan
        startup of the application failed in this process, and after the
        bridge was shut down. A request whose application has not started its
        response within the request timeout is answered with 504 Gateway
        Timeout; the timeout is the constructor argument, or the value a
        server or middleware put under ``webworks.request_timeout`` in the
        environ.

        Example, served by the built-in server::

            from ccai.webworks.wsgi import WSGIServer, ServerConfig

            server = WSGIServer(webapp.wsgi_app, ServerConfig(port=8000))
            server.serve_forever()
    """

    def __init__(
        self,
        asgi_app: Optional[ASGICallable] = None,
        app_provider: Optional[Callable[[], ASGICallable]] = None,
        request_timeout: Optional[float] = None,
        startup_timeout: float = DEFAULT_STARTUP_TIMEOUT,
        shutdown_timeout: float = DEFAULT_SHUTDOWN_TIMEOUT,
        body_chunk_size: int = DEFAULT_BODY_CHUNK_SIZE,
    ):
        """
            Construct a bridge.

            :param asgi_app: The ASGI application to serve.
            :param app_provider: A callable without arguments that returns the
                ASGI application, called when the bridge starts in a process.
                Give either this or asgi_app.
            :param request_timeout: Seconds the application is given to start
                its response, None for no limit.
            :param startup_timeout: Seconds the application is given to answer
                the lifespan startup event.
            :param shutdown_timeout: Seconds given to the requests in flight
                and then to the lifespan shutdown when the bridge shuts down.
            :param body_chunk_size: Size of the pieces the request body is
                read in.

            :raises SemanticError: If not exactly one of asgi_app and
                app_provider is given, or a size or timeout is not positive.
        """
        if (asgi_app is None) == (app_provider is None):
            errmsg = "ASGIBridge needs exactly one of 'asgi_app' and 'app_provider'."
            raise SemanticError(errmsg)

        if body_chunk_size < 1:
            errmsg = f"ASGIBridge 'body_chunk_size' must be at least 1, got {body_chunk_size}."
            raise SemanticError(errmsg)

        if request_timeout is not None and request_timeout <= 0:
            errmsg = f"ASGIBridge 'request_timeout' must be positive or None, got {request_timeout}."
            raise SemanticError(errmsg)

        self._asgi_app = asgi_app
        self._app_provider = app_provider
        self._request_timeout = request_timeout
        self._startup_timeout = startup_timeout
        self._shutdown_timeout = shutdown_timeout
        self._body_chunk_size = body_chunk_size

        self._lock = threading.Lock()
        self._runtime: Optional[_ProcessRuntime] = None
        self._atexit_registered = False

        _BRIDGES.add(self)
        return

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def request_timeout(self) -> Optional[float]:
        """
            Seconds the application is given to start its response.

            :returns: The timeout, or None for no limit.
        """
        return self._request_timeout

    @property
    def is_started(self) -> bool:
        """
            Check whether the bridge has started in this process.

            :returns: True once the lifespan startup has run in this process.
        """
        runtime = self._runtime
        rtnval = runtime is not None and runtime.pid == os.getpid()
        return rtnval

    @property
    def lifespan_status(self) -> str:
        """
            The outcome of the lifespan startup in this process.

            :returns: One of LIFESPAN_NOT_STARTED, LIFESPAN_COMPLETE,
                LIFESPAN_UNSUPPORTED (the application does not take part in
                the lifespan protocol) and LIFESPAN_FAILED.
        """
        runtime = self._runtime
        if runtime is None or runtime.pid != os.getpid():
            rtnval = LIFESPAN_NOT_STARTED
        else:
            rtnval = runtime.lifespan_status
        return rtnval

    @property
    def can_serve(self) -> bool:
        """
            Check whether requests are passed to the application in this process.

            :returns: True once the bridge started here, its lifespan startup
                did not fail and it has not been shut down.
        """
        runtime = self._runtime
        rtnval = runtime is not None and runtime.pid == os.getpid() and runtime.can_serve
        return rtnval

    @property
    def failure_message(self) -> Optional[str]:
        """
            Why the lifespan startup failed in this process.

            :returns: The message, or None when it did not fail.
        """
        runtime = self._runtime
        rtnval = None
        if runtime is not None and runtime.pid == os.getpid():
            rtnval = runtime.failure_message
        return rtnval

    # ------------------------------------------------------------------
    # Process lifecycle
    # ------------------------------------------------------------------

    def startup(self) -> bool:
        """
            Start the bridge in this process, if it has not started yet.

            Starts the event loop thread and runs the lifespan startup of the
            application. The first request does this by itself; a server calls
            it when a worker process starts, so the startup is done before the
            worker accepts connections.

            :returns: True if requests will be passed to the application,
                False if the lifespan startup failed or the bridge was shut down.
        """
        runtime = self._ensure_runtime()
        rtnval = runtime.can_serve
        return rtnval

    def shutdown(self) -> None:
        """
            Shut the bridge down in this process.

            The requests in flight are given the shutdown timeout to finish,
            then the lifespan shutdown of the application runs and the loop
            thread stops. Requests that arrive afterwards are answered with
            503. Does nothing when the bridge has not started in this process
            or was shut down already.
        """
        with self._lock:
            runtime = self._runtime
            if runtime is None or runtime.pid != os.getpid() or runtime.stopped:
                return
            runtime.stopped = True

        loop = runtime.loop
        thread = runtime.thread

        if loop is not None and thread is not None and thread.is_alive():
            future = asyncio.run_coroutine_threadsafe(self._shut_down_on_loop(runtime), loop)
            future.result()

            loop.call_soon_threadsafe(loop.stop)
            thread.join(timeout=self._shutdown_timeout)

            if not thread.is_alive():
                loop.close()

        logger.info("ASGI bridge stopped in process %d", runtime.pid)
        return

    def on_worker_start(self, worker: Any) -> None:
        """
            Start the bridge when a server starts a worker process.

            The built-in WSGI server calls this in each worker process before
            the worker accepts connections.

            :param worker: The worker that is starting.
        """
        self.startup()
        return

    def on_worker_exit(self, worker: Any) -> None:
        """
            Shut the bridge down when a server stops a worker process.

            :param worker: The worker that has stopped serving.
        """
        self.shutdown()
        return

    def _forget_runtime_after_fork(self) -> None:
        """
            Drop the state of the parent process in a forked child.
        """
        self._lock = threading.Lock()
        self._runtime = None
        return

    def _ensure_runtime(self) -> _ProcessRuntime:
        """
            Get the runtime of this process, starting it when needed.

            :returns: The runtime.
        """
        pid = os.getpid()
        runtime = self._runtime

        if runtime is not None and runtime.pid == pid:
            return runtime

        with self._lock:
            runtime = self._runtime
            if runtime is None or runtime.pid != pid:
                runtime = self._start_runtime(pid)
                self._runtime = runtime

        return runtime

    def _start_runtime(self, pid: int) -> _ProcessRuntime:
        """
            Start the loop thread and run the lifespan startup.

            :param pid: The current process.

            :returns: The started runtime.
        """
        runtime = _ProcessRuntime(pid)

        if self._asgi_app is not None:
            runtime.asgi_app = self._asgi_app
        else:
            runtime.asgi_app = self._app_provider()

        loop = asyncio.new_event_loop()
        loop_ready = threading.Event()

        thread = threading.Thread(
            target=self._run_loop,
            args=(loop, loop_ready),
            name=f"wsgi-asgi-bridge-{pid}",
            daemon=True,
        )
        thread.start()
        loop_ready.wait()

        runtime.loop = loop
        runtime.thread = thread

        future = asyncio.run_coroutine_threadsafe(self._lifespan_startup(runtime), loop)

        started = False
        try:
            future.result()
            started = True
        finally:
            if not started:
                # The error is raised on; the loop of this attempt is not
                # left running behind it.
                loop.call_soon_threadsafe(loop.stop)
                thread.join(timeout=self._shutdown_timeout)

        if not self._atexit_registered:
            atexit.register(self._shutdown_at_exit)
            self._atexit_registered = True

        logger.info(
            "ASGI bridge started in process %d (lifespan: %s)",
            pid,
            runtime.lifespan_status,
        )

        return runtime

    @staticmethod
    def _run_loop(loop: asyncio.AbstractEventLoop, loop_ready: threading.Event) -> None:
        """
            Run the event loop of the bridge until it is stopped.

            :param loop: The loop.
            :param loop_ready: Set once the loop is about to run.
        """
        asyncio.set_event_loop(loop)
        loop.call_soon(loop_ready.set)
        loop.run_forever()
        return

    def _shutdown_at_exit(self) -> None:
        """
            Shut the bridge down when the interpreter exits.

            External servers such as Gunicorn end a worker by letting its
            interpreter exit; this runs the lifespan shutdown there.
        """
        runtime = self._runtime
        if runtime is not None and runtime.pid == os.getpid():
            self.shutdown()
        return

    # ------------------------------------------------------------------
    # Lifespan, on the loop
    # ------------------------------------------------------------------

    async def _lifespan_startup(self, runtime: _ProcessRuntime) -> None:
        """
            Send the lifespan startup event and record the outcome.

            An application that ends without reading the startup event does
            not take part in the lifespan protocol; it is served all the same.
            An application that read the event and then raised failed its
            startup, as did one that does not answer within the startup
            timeout.

            :param runtime: The runtime of this process.

            :raises BaseException: An exception of the application that is
                not an Exception (ConfigurationError, SemanticError) is
                raised on, it ends the run.
        """
        receive_queue: asyncio.Queue = asyncio.Queue()
        send_queue: asyncio.Queue = asyncio.Queue()
        runtime.lifespan_receive = receive_queue
        runtime.lifespan_send = send_queue

        startup_event_read = False

        async def receive() -> Dict[str, Any]:
            nonlocal startup_event_read
            message = await receive_queue.get()
            if message.get("type") == "lifespan.startup":
                startup_event_read = True
            return message

        async def send(message: Dict[str, Any]) -> None:
            await send_queue.put(message)
            return

        scope = {
            "type": "lifespan",
            "asgi": {"version": "3.0", "spec_version": "2.0"},
            "state": runtime.app_state,
        }

        task = asyncio.ensure_future(runtime.asgi_app(scope, receive, send))
        runtime.lifespan_task = task

        await receive_queue.put({"type": "lifespan.startup"})

        reply_future = asyncio.ensure_future(send_queue.get())
        done, _pending = await asyncio.wait(
            {reply_future, task},
            timeout=self._startup_timeout,
            return_when=asyncio.FIRST_COMPLETED,
        )

        if reply_future in done:
            reply_type = reply_future.result().get("type", "")

            if reply_type == "lifespan.startup.complete":
                runtime.lifespan_status = LIFESPAN_COMPLETE
            elif reply_type == "lifespan.startup.failed":
                runtime.lifespan_status = LIFESPAN_FAILED
                runtime.failure_message = reply_future.result().get("message", "")
                logger.error("ASGI lifespan startup failed: %s", runtime.failure_message)
            else:
                runtime.lifespan_status = LIFESPAN_FAILED
                runtime.failure_message = f"Unexpected reply to the lifespan startup event: {reply_type!r}"
                logger.error("ASGI lifespan startup failed: %s", runtime.failure_message)

        elif task in done:
            reply_future.cancel()

            app_error = None
            if not task.cancelled():
                app_error = task.exception()

            if app_error is not None and not isinstance(app_error, Exception):
                raise app_error

            if app_error is not None and startup_event_read:
                runtime.lifespan_status = LIFESPAN_FAILED
                runtime.failure_message = f"{type(app_error).__name__}: {app_error}"
                logger.error(
                    "ASGI lifespan startup raised an exception.",
                    exc_info=(type(app_error), app_error, app_error.__traceback__),
                )
            else:
                # The application rejected the lifespan scope
                runtime.lifespan_status = LIFESPAN_UNSUPPORTED
                logger.info("The ASGI application does not take part in the lifespan protocol.")

        else:
            reply_future.cancel()
            task.cancel()
            runtime.lifespan_status = LIFESPAN_FAILED
            runtime.failure_message = (
                f"The application did not answer the lifespan startup event within "
                f"{self._startup_timeout} seconds."
            )
            logger.error("ASGI lifespan startup failed: %s", runtime.failure_message)

        return

    async def _shut_down_on_loop(self, runtime: _ProcessRuntime) -> None:
        """
            Let the requests in flight finish, then run the lifespan shutdown.

            :param runtime: The runtime of this process.
        """
        active = set(runtime.active_tasks)

        if len(active) > 0:
            _done, still_running = await asyncio.wait(active, timeout=self._shutdown_timeout)
            for task in still_running:
                task.cancel()
            if len(still_running) > 0:
                logger.warning(
                    "ASGI bridge: %d requests did not finish within %.1f seconds and were cancelled",
                    len(still_running),
                    self._shutdown_timeout,
                )
                await asyncio.wait(still_running)

        task = runtime.lifespan_task

        if runtime.lifespan_status == LIFESPAN_COMPLETE and task is not None and not task.done():
            await runtime.lifespan_receive.put({"type": "lifespan.shutdown"})

            reply_future = asyncio.ensure_future(runtime.lifespan_send.get())
            done, _pending = await asyncio.wait(
                {reply_future, task},
                timeout=self._shutdown_timeout,
                return_when=asyncio.FIRST_COMPLETED,
            )

            if reply_future in done:
                reply = reply_future.result()
                if reply.get("type") == "lifespan.shutdown.failed":
                    logger.error("ASGI lifespan shutdown failed: %s", reply.get("message", ""))
            else:
                reply_future.cancel()
                if task not in done:
                    logger.error(
                        "The application did not answer the lifespan shutdown event within %.1f seconds.",
                        self._shutdown_timeout,
                    )

        if task is not None and not task.done():
            task.cancel()
            await asyncio.wait({task})

        if task is not None and task.done() and not task.cancelled():
            lifespan_error = task.exception()
            if lifespan_error is not None and not isinstance(lifespan_error, Exception):
                raise lifespan_error
            if lifespan_error is not None:
                logger.error(
                    "ASGI lifespan shutdown raised an exception.",
                    exc_info=(type(lifespan_error), lifespan_error, lifespan_error.__traceback__),
                )

        return

    # ------------------------------------------------------------------
    # Requests
    # ------------------------------------------------------------------

    def __call__(
        self,
        environ: Dict[str, Any],
        start_response: Callable[..., Any],
    ) -> Iterable[bytes]:
        """
            Serve one request through the ASGI application.

            :param environ: The WSGI environ.
            :param start_response: The WSGI start_response callable.

            :returns: The response body iterable.
        """
        runtime = self._ensure_runtime()

        if not runtime.can_serve:
            rtnval = self._plain_response(start_response, 503, "Service Unavailable")
            return rtnval

        exchange = _Exchange(environ, runtime.loop, self._body_chunk_size, runtime.thread)
        scope = self._build_scope(environ, runtime)
        timeout = self._request_timeout_for(environ)

        task_future = asyncio.run_coroutine_threadsafe(
            self._run_request(runtime, scope, exchange, timeout),
            runtime.loop,
        )
        task_future.add_done_callback(exchange.post_done)

        while True:
            event = exchange.next_event()
            kind = event[0]

            if kind == _EVENT_READ:
                exchange.serve_read(event[1])
                continue

            if kind == _EVENT_START:
                status, raw_headers = event[1], event[2]
                headers = self._wsgi_headers(raw_headers)

                response_started = False
                try:
                    start_response(_status_line(status), headers)
                    response_started = True
                finally:
                    if not response_started:
                        # The server refused the response, the application
                        # must not wait for it to take the body.
                        exchange.close(client_gone=True)

                discard_body = environ.get("REQUEST_METHOD", "GET").upper() == "HEAD"
                rtnval = _ResponseBody(exchange, discard_body)
                return rtnval

            if kind == _EVENT_DONE:
                rtnval = self._answer_without_response(event[1], exchange, environ, start_response)
                return rtnval

            # A body chunk before the start is refused by send()
            exchange.close(client_gone=False)
            errmsg = f"The ASGI bridge received an unexpected event {kind!r} before the response started."
            raise IncompleteResponse(errmsg)

    def _answer_without_response(
        self,
        task_future: Any,
        exchange: _Exchange,
        environ: Dict[str, Any],
        start_response: Callable[..., Any],
    ) -> Iterable[bytes]:
        """
            Answer a request whose application ended without starting a response.

            :param task_future: The settled future of the application task.
            :param exchange: The exchange of the request.
            :param environ: The WSGI environ.
            :param start_response: The WSGI start_response callable.

            :returns: The body of the answer.
        """
        exchange.close(client_gone=False)

        error = None
        if not task_future.cancelled():
            error = task_future.exception()

        if error is not None and not isinstance(error, Exception):
            # ConfigurationError, SemanticError and their kin end the run
            raise error

        if exchange.timed_out:
            logger.warning(
                "ASGI bridge: %s %s did not start its response within %s seconds, answered 504",
                environ.get("REQUEST_METHOD", "?"),
                environ.get("PATH_INFO", "?"),
                self._request_timeout_for(environ),
            )
            rtnval = self._plain_response(start_response, 504, "Gateway Timeout")
            return rtnval

        if exchange.read_error is not None:
            # The client went away while its body was being read. The server
            # deals with the connection as it does for any failed read.
            raise exchange.read_error

        if error is not None:
            logger.error(
                "ASGI bridge: the application raised %s for %s %s without starting a response",
                type(error).__name__,
                environ.get("REQUEST_METHOD", "?"),
                environ.get("PATH_INFO", "?"),
                exc_info=(type(error), error, error.__traceback__),
            )
        else:
            logger.error(
                "ASGI bridge: the application returned without starting a response for %s %s",
                environ.get("REQUEST_METHOD", "?"),
                environ.get("PATH_INFO", "?"),
            )

        rtnval = self._plain_response(start_response, 500, "Internal Server Error")
        return rtnval

    async def _run_request(
        self,
        runtime: _ProcessRuntime,
        scope: Dict[str, Any],
        exchange: _Exchange,
        timeout: Optional[float],
    ) -> None:
        """
            Run the ASGI application for one request, on the loop.

            :param runtime: The runtime of this process.
            :param scope: The HTTP scope of the request.
            :param exchange: The exchange of the request.
            :param timeout: Seconds the application is given to start its
                response, None for no limit.
        """
        this_task = asyncio.current_task()
        runtime.active_tasks.add(this_task)

        try:
            app_task = asyncio.ensure_future(runtime.asgi_app(scope, exchange.receive, exchange.send))

            if timeout is not None:
                started_waiter = asyncio.ensure_future(exchange.started.wait())
                done, _pending = await asyncio.wait(
                    {app_task, started_waiter},
                    timeout=timeout,
                    return_when=asyncio.FIRST_COMPLETED,
                )
                started_waiter.cancel()

                if len(done) == 0:
                    exchange.timed_out = True
                    app_task.cancel()
                    await asyncio.wait({app_task})
                    return

            await app_task
        finally:
            runtime.active_tasks.discard(this_task)

        return

    def _request_timeout_for(self, environ: Dict[str, Any]) -> Optional[float]:
        """
            Decide the request timeout of one request.

            :param environ: The WSGI environ.

            :returns: The timeout a server or middleware set in the environ,
                else the timeout of the bridge.
        """
        rtnval = self._request_timeout
        environ_timeout = environ.get(ENVIRON_REQUEST_TIMEOUT)

        if environ_timeout is not None:
            try:
                seconds = float(environ_timeout)
            except (TypeError, ValueError):
                seconds = 0.0
            if seconds > 0:
                rtnval = seconds

        return rtnval

    def _build_scope(self, environ: Dict[str, Any], runtime: _ProcessRuntime) -> Dict[str, Any]:
        """
            Build the ASGI HTTP scope of a request from its WSGI environ.

            ``path`` is PATH_INFO and ``root_path`` is SCRIPT_NAME, both as
            text, so an application mounted below a prefix routes the same
            path it would route at the root.

            :param environ: The WSGI environ.
            :param runtime: The runtime of this process.

            :returns: The scope.
        """
        script_name = environ.get("SCRIPT_NAME", "")
        path_info = environ.get("PATH_INFO", "")
        if path_info == "":
            path_info = "/"

        protocol = environ.get("SERVER_PROTOCOL", "HTTP/1.1")
        if protocol.upper().startswith("HTTP/"):
            http_version = protocol[5:]
        else:
            http_version = "1.1"
        if http_version not in ("1.0", "1.1", "2", "2.0"):
            http_version = "1.1"

        headers: List[Tuple[bytes, bytes]] = []
        for key, value in environ.items():
            if key.startswith("HTTP_"):
                if key in ("HTTP_CONTENT_TYPE", "HTTP_CONTENT_LENGTH"):
                    continue
                name = key[5:].replace("_", "-").lower()
                headers.append((name.encode("latin-1"), _wsgi_text_to_bytes(value)))

        content_type = environ.get("CONTENT_TYPE", "")
        if content_type is not None and content_type != "":
            headers.append((b"content-type", _wsgi_text_to_bytes(content_type)))

        content_length = environ.get("CONTENT_LENGTH", "")
        if content_length is not None and str(content_length).strip() != "":
            headers.append((b"content-length", _wsgi_text_to_bytes(str(content_length).strip())))

        server = None
        server_name = environ.get("SERVER_NAME")
        if server_name is not None:
            try:
                server = (server_name, int(environ.get("SERVER_PORT", "0")))
            except ValueError:
                server = (server_name, None)

        client = None
        remote_addr = environ.get("REMOTE_ADDR")
        if remote_addr is not None and remote_addr != "":
            try:
                client = (remote_addr, int(environ.get("REMOTE_PORT", "0")))
            except ValueError:
                client = (remote_addr, 0)

        rtnval = {
            "type": "http",
            "asgi": {"version": "3.0", "spec_version": "2.3"},
            "http_version": http_version,
            "method": environ.get("REQUEST_METHOD", "GET").upper(),
            "scheme": environ.get("wsgi.url_scheme", "http"),
            "path": _wsgi_text_to_str(path_info),
            "raw_path": self._raw_path(environ, script_name, path_info),
            "root_path": _wsgi_text_to_str(script_name),
            "query_string": _wsgi_text_to_bytes(environ.get("QUERY_STRING", "")),
            "headers": headers,
            "client": client,
            "server": server,
            "state": dict(runtime.app_state),
            "extensions": {},
        }
        return rtnval

    @staticmethod
    def _raw_path(environ: Dict[str, Any], script_name: str, path_info: str) -> bytes:
        """
            Get the path of the request as the client sent it.

            :param environ: The WSGI environ.
            :param script_name: SCRIPT_NAME of the request.
            :param path_info: PATH_INFO of the request.

            :returns: The percent-encoded path, without the query string.
        """
        request_uri = environ.get("RAW_URI") or environ.get("REQUEST_URI")

        if request_uri:
            target = request_uri.split("?", 1)[0]
            if target.lower().startswith(("http://", "https://")):
                target = urlsplit(target).path or "/"
            rtnval = _wsgi_text_to_bytes(target)
        else:
            rtnval = quote(_wsgi_text_to_bytes(script_name + path_info), safe="/").encode("ascii")

        return rtnval

    @staticmethod
    def _wsgi_headers(raw_headers: List[Tuple[Any, Any]]) -> List[Tuple[str, str]]:
        """
            Convert the headers of an ASGI response start into WSGI headers.

            Every field is kept, so repeated headers such as Set-Cookie stay
            separate. Hop-by-hop headers are left to the server.

            :param raw_headers: The (name, value) byte pairs of the application.

            :returns: The (name, value) string pairs for start_response.
        """
        rtnval: List[Tuple[str, str]] = []

        for raw_name, raw_value in raw_headers:
            if isinstance(raw_name, (bytes, bytearray)):
                name = bytes(raw_name).decode("latin-1")
            else:
                name = str(raw_name)

            if isinstance(raw_value, (bytes, bytearray)):
                value = bytes(raw_value).decode("latin-1")
            else:
                value = str(raw_value)

            if name.lower() in HOP_BY_HOP_HEADERS:
                continue

            rtnval.append((name, value))

        return rtnval

    @staticmethod
    def _plain_response(start_response: Callable[..., Any], status_code: int, message: str) -> List[bytes]:
        """
            Answer a request with a short text response.

            :param start_response: The WSGI start_response callable.
            :param status_code: HTTP status code.
            :param message: The body text.

            :returns: The body iterable.
        """
        body = message.encode("utf-8")
        headers = [
            ("Content-Type", "text/plain; charset=utf-8"),
            ("Content-Length", str(len(body))),
        ]
        start_response(_status_line(status_code), headers)
        rtnval = [body]
        return rtnval
