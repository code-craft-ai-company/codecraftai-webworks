"""
    HTTP/1.1 protocol handler for the development ASGI server.

    This module provides the :class:`HTTPProtocolHandler` class, an
    ``asyncio.Protocol`` subclass that parses HTTP/1.1 requests from
    a TCP connection, constructs ASGI scope dictionaries, and bridges
    the ASGI receive/send interface to raw TCP transport.

    The handler supports keep-alive connections, chunked transfer
    decoding, request size limits, and debug-mode error reporting.
"""

import asyncio
import logging
import time
import traceback

from typing import Any, Callable, Dict, List, Optional, Tuple
from urllib.parse import unquote


logger = logging.getLogger(__name__)


# =============================================================================
# Constants
# =============================================================================

MAX_REQUEST_LINE_BYTES: int = 8192
"""Maximum allowed size of the HTTP request line in bytes."""

MAX_HEADER_BLOCK_BYTES: int = 32768
"""Maximum allowed size of the HTTP header block in bytes."""

KEEPALIVE_TIMEOUT_SECONDS: float = 30.0
"""Idle timeout in seconds for keep-alive connections."""

HEADER_TERMINATOR: bytes = b"\r\n\r\n"
"""Byte sequence that terminates the HTTP header block."""

LINE_TERMINATOR: bytes = b"\r\n"
"""Byte sequence that terminates an HTTP line."""


# =============================================================================
# HTTP Status Reason Phrases
# =============================================================================

HTTP_STATUS_REASONS: Dict[int, str] = {
    200: "OK",
    201: "Created",
    204: "No Content",
    301: "Moved Permanently",
    302: "Found",
    304: "Not Modified",
    400: "Bad Request",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Not Found",
    405: "Method Not Allowed",
    408: "Request Timeout",
    413: "Content Too Large",
    431: "Request Header Fields Too Large",
    500: "Internal Server Error",
    502: "Bad Gateway",
    503: "Service Unavailable",
}
"""Common HTTP status code to reason phrase mapping."""


def _get_reason_phrase(status_code: int) -> str:
    """
        Look up the reason phrase for an HTTP status code.

        Falls back to "Unknown" if the status code is not in the
        known mapping.

        :param status_code: The HTTP status code.

        :returns: The reason phrase string.
    """
    reason = HTTP_STATUS_REASONS.get(status_code, "Unknown")
    return reason


# =============================================================================
# Parse State
# =============================================================================

class _ParseState:
    """
        Enumeration of incremental HTTP parsing states.

        The handler transitions through these states as it receives
        and processes data from the TCP connection.
    """

    AWAITING_REQUEST_LINE = "awaiting_request_line"
    """Waiting for the complete request line to arrive."""

    AWAITING_HEADERS = "awaiting_headers"
    """Request line received, waiting for the header block terminator."""

    AWAITING_BODY = "awaiting_body"
    """Headers received, waiting for the request body."""

    PROCESSING = "processing"
    """Request fully received, ASGI application is being invoked."""

    RESPONSE_STARTED = "response_started"
    """The ASGI application has sent http.response.start."""

    RESPONSE_BODY = "response_body"
    """The ASGI application is sending http.response.body chunks."""

    DONE = "done"
    """The request/response cycle is complete."""


# =============================================================================
# HTTPProtocolHandler
# =============================================================================

class HTTPProtocolHandler(asyncio.Protocol):
    """
        An ``asyncio.Protocol`` subclass that handles a single TCP connection.

        Parses HTTP/1.1 requests incrementally, constructs ASGI scope
        dictionaries, and provides ``receive`` and ``send`` callables
        to the ASGI application. Supports keep-alive connections with
        a configurable idle timeout.

        :param app: The ASGI application callable.
        :param server_host: The host address the server is bound to.
        :param server_port: The port number the server is bound to.
        :param debug: Whether debug mode is enabled for error reporting.
        :param on_close: Callback invoked when the connection is closed.
    """

    def __init__(
        self,
        app: Any,
        server_host: str,
        server_port: int,
        debug: bool,
        on_close: Optional[Callable] = None,
        request_logger: Optional[Any] = None,
    ):
        """
            Construct an HTTPProtocolHandler.

            :param app: The ASGI application callable.
            :param server_host: The host address the server is bound to.
            :param server_port: The port number the server is bound to.
            :param debug: Whether debug mode is enabled for error reporting.
            :param on_close: Optional callback invoked when the connection is closed.
            :param request_logger: Optional request logger instance for logging
                request method, path, status code, and elapsed time.
        """
        self._app = app
        self._server_host = server_host
        self._server_port = server_port
        self._debug = debug
        self._on_close = on_close
        self._request_logger = request_logger

        self._transport: Optional[asyncio.Transport] = None
        self._client_host: str = ""
        self._client_port: int = 0

        self._buffer: bytes = b""
        self._state: str = _ParseState.AWAITING_REQUEST_LINE

        # Parsed request components
        self._request_method: str = ""
        self._request_target: str = ""
        self._http_version: str = ""
        self._headers: List[Tuple[bytes, bytes]] = []
        self._body: bytes = b""
        self._content_length: int = 0
        self._chunked: bool = False

        # ASGI send state
        self._response_status: int = 0
        self._response_headers: List[Tuple[bytes, bytes]] = []
        self._response_started: bool = False
        self._response_complete: bool = False

        # Body delivery event for receive callable
        self._body_received: Optional[asyncio.Event] = None
        self._body_delivered: bool = False

        # Keep-alive task handle
        self._keepalive_task: Optional[asyncio.Task] = None

        # Request timing for logging
        self._request_start_time: float = 0.0

        return


    # -------------------------------------------------------------------------
    # asyncio.Protocol Callbacks
    # -------------------------------------------------------------------------

    def connection_made(self, transport: asyncio.BaseTransport) -> None:
        """
            Called when a new TCP connection is established.

            Records the client address and stores the transport for
            writing response data.

            :param transport: The transport representing the connection.
        """
        self._transport = transport
        peername = transport.get_extra_info("peername")

        if peername is not None:
            self._client_host = peername[0]
            self._client_port = peername[1]
        else:
            self._client_host = "unknown"
            self._client_port = 0

        logger.debug(
            "Connection established from %s:%d",
            self._client_host,
            self._client_port,
        )

        return

    def data_received(self, data: bytes) -> None:
        """
            Called when data is received on the TCP connection.

            Appends the data to the internal buffer and attempts to
            advance the incremental HTTP parser. When a complete
            request is assembled, schedules the ASGI application
            invocation.

            :param data: The raw bytes received from the client.
        """
        self._buffer += data
        self._process_buffer()
        return

    def connection_lost(self, exc: Optional[Exception]) -> None:
        """
            Called when the TCP connection is lost or closed.

            Cleans up internal state and invokes the ``on_close``
            callback if one was provided.

            :param exc: The exception that caused the loss, or ``None``
                for a clean close.
        """
        if exc is not None:
            logger.debug(
                "Connection lost from %s:%d with error: %s",
                self._client_host,
                self._client_port,
                exc,
            )
        else:
            logger.debug(
                "Connection closed from %s:%d",
                self._client_host,
                self._client_port,
            )

        if self._keepalive_task is not None:
            self._keepalive_task.cancel()
            self._keepalive_task = None

        self._transport = None

        if self._on_close is not None:
            self._on_close(self)

        return

    # -------------------------------------------------------------------------
    # Buffer Processing
    # -------------------------------------------------------------------------

    def _process_buffer(self) -> None:
        """
            Advance the incremental HTTP parser based on the current
            buffer contents and parse state.

            Transitions through states as complete request components
            are identified in the buffer. Enforces size limits on the
            request line and header block.
        """
        if self._state == _ParseState.AWAITING_REQUEST_LINE:
            self._try_parse_request_line()

        if self._state == _ParseState.AWAITING_HEADERS:
            self._try_parse_headers()

        if self._state == _ParseState.AWAITING_BODY:
            self._try_read_body()

        return

    def _try_parse_request_line(self) -> None:
        """
            Attempt to extract the request line from the buffer.

            Looks for the first CRLF in the buffer. If the request
            line exceeds the maximum allowed size, sends a 400 error
            and closes the connection.
        """
        crlf_pos = self._buffer.find(LINE_TERMINATOR)

        if crlf_pos < 0:
            # No complete line yet; check if buffer exceeds limit
            if len(self._buffer) > MAX_REQUEST_LINE_BYTES:
                self._send_error_response(400, "Request line too long")
            return

        request_line = self._buffer[:crlf_pos]

        if len(request_line) > MAX_REQUEST_LINE_BYTES:
            self._send_error_response(400, "Request line too long")
            return

        parsed = self._parse_request_line(request_line)

        if parsed is None:
            self._send_error_response(400, "Malformed request line")
            return

        self._request_method, self._request_target, self._http_version = parsed
        self._buffer = self._buffer[crlf_pos + len(LINE_TERMINATOR):]
        self._state = _ParseState.AWAITING_HEADERS

        return

    def _try_parse_headers(self) -> None:
        """
            Attempt to extract the header block from the buffer.

            Looks for the double-CRLF header terminator. If the header
            block exceeds the maximum allowed size, sends a 431 error
            and closes the connection.
        """
        term_pos = self._buffer.find(HEADER_TERMINATOR)

        if term_pos < 0:
            # No complete header block yet; check if buffer exceeds limit
            if len(self._buffer) > MAX_HEADER_BLOCK_BYTES:
                self._send_error_response(431, "Request header fields too large")
            return

        header_block = self._buffer[:term_pos]

        if len(header_block) > MAX_HEADER_BLOCK_BYTES:
            self._send_error_response(431, "Request header fields too large")
            return

        self._headers = self._parse_headers(header_block)
        self._buffer = self._buffer[term_pos + len(HEADER_TERMINATOR):]

        # Determine body handling
        self._content_length = 0
        self._chunked = False

        for name, value in self._headers:
            lower_name = name.lower()
            if lower_name == b"content-length":
                try:
                    self._content_length = int(value)
                except ValueError:
                    self._send_error_response(400, "Invalid Content-Length")
                    return
            elif lower_name == b"transfer-encoding":
                if b"chunked" in value.lower():
                    self._chunked = True

        if self._content_length > 0 or self._chunked:
            self._state = _ParseState.AWAITING_BODY
        else:
            self._body = b""
            self._state = _ParseState.PROCESSING
            self._schedule_request_handling()

        return

    def _try_read_body(self) -> None:
        """
            Attempt to read the request body from the buffer.

            Handles both Content-Length and chunked transfer encoding.
            When the complete body is available, transitions to the
            processing state.
        """
        if self._chunked:
            decoded = self._decode_chunked(self._buffer)
            if decoded is not None:
                self._body = decoded
                self._buffer = b""
                self._state = _ParseState.PROCESSING
                self._schedule_request_handling()
        else:
            if len(self._buffer) >= self._content_length:
                self._body = self._buffer[:self._content_length]
                self._buffer = self._buffer[self._content_length:]
                self._state = _ParseState.PROCESSING
                self._schedule_request_handling()

        return


    # -------------------------------------------------------------------------
    # HTTP Parsing Methods
    # -------------------------------------------------------------------------

    def _parse_request_line(self, line: bytes) -> Optional[Tuple[str, str, str]]:
        """
            Parse an HTTP request line into its components.

            Extracts the method, request target, and HTTP version from
            the raw request line bytes. Returns ``None`` if the line
            is malformed.

            :param line: The raw request line bytes (without trailing CRLF).

            :returns: A tuple of (method, target, version) strings, or
                ``None`` if the line cannot be parsed.
        """
        parts = line.split(b" ")

        if len(parts) != 3:
            return None

        method_bytes = parts[0]
        target_bytes = parts[1]
        version_bytes = parts[2]

        method = method_bytes.decode("ascii", errors="replace")
        target = target_bytes.decode("ascii", errors="replace")
        version = version_bytes.decode("ascii", errors="replace")

        return (method, target, version)

    def _parse_headers(self, header_block: bytes) -> List[Tuple[bytes, bytes]]:
        """
            Parse an HTTP header block into a list of name/value tuples.

            Each header line is split on the first colon. Header names
            are stripped of whitespace and lowercased. Header values are
            stripped of leading and trailing whitespace.

            :param header_block: The raw header block bytes (without the
                trailing double-CRLF).

            :returns: A list of (name_bytes, value_bytes) tuples.
        """
        headers = []

        if len(header_block) == 0:
            return headers

        lines = header_block.split(LINE_TERMINATOR)

        for line in lines:
            if len(line) == 0:
                continue

            colon_pos = line.find(b":")

            if colon_pos < 0:
                # Malformed header line, skip it
                continue

            name = line[:colon_pos].strip().lower()
            value = line[colon_pos + 1:].strip()

            headers.append((name, value))

        return headers

    def _decode_chunked(self, data: bytes) -> Optional[bytes]:
        """
            Decode an HTTP chunked transfer-encoded body.

            Parses chunk size lines and concatenates chunk data until
            the terminal zero-length chunk is found. Returns ``None``
            if the data is incomplete.

            :param data: The raw chunked body bytes.

            :returns: The decoded body bytes, or ``None`` if the
                chunked body is not yet complete.
        """
        result = bytearray()
        remaining = data

        while True:
            crlf_pos = remaining.find(LINE_TERMINATOR)

            if crlf_pos < 0:
                # Incomplete chunk size line
                return None

            size_line = remaining[:crlf_pos]

            # Chunk extensions (after semicolon) are ignored
            semicolon_pos = size_line.find(b";")
            if semicolon_pos >= 0:
                size_line = size_line[:semicolon_pos]

            try:
                chunk_size = int(size_line.strip(), 16)
            except ValueError:
                # Invalid chunk size
                return None

            remaining = remaining[crlf_pos + len(LINE_TERMINATOR):]

            if chunk_size == 0:
                # Terminal chunk found
                break

            # Need chunk_size bytes plus trailing CRLF
            needed = chunk_size + len(LINE_TERMINATOR)

            if len(remaining) < needed:
                # Incomplete chunk data
                return None

            result.extend(remaining[:chunk_size])
            remaining = remaining[needed:]

        decoded = bytes(result)

        return decoded


    # -------------------------------------------------------------------------
    # ASGI Scope Construction
    # -------------------------------------------------------------------------

    def _build_scope(
        self,
        method: str,
        path: str,
        query: str,
        version: str,
        headers: List[Tuple[bytes, bytes]],
    ) -> Dict[str, Any]:
        """
            Construct an ASGI HTTP connection scope dictionary.

            Builds the scope with all required keys as specified by
            the ASGI 3.0 HTTP connection scope specification.

            :param method: The HTTP method string (e.g. "GET").
            :param path: The request path string (e.g. "/some/path").
            :param query: The query string without the leading "?".
            :param version: The HTTP version string (e.g. "HTTP/1.1").
            :param headers: The parsed headers as (name, value) byte tuples.

            :returns: The ASGI scope dictionary.
        """
        # Extract the HTTP version number from the version string
        if version.upper().startswith("HTTP/"):
            http_version = version[5:]
        else:
            http_version = "1.1"

        # Build the headers list as two-element lists of byte strings
        scope_headers = []
        for name, value in headers:
            scope_headers.append([name, value])

        scope = {
            "type": "http",
            "asgi": {"version": "3.0"},
            "http_version": http_version,
            "method": method,
            "path": unquote(path),
            "raw_path": path.encode("ascii", errors="replace"),
            "root_path": "",
            "scheme": "http",
            "query_string": query.encode("ascii", errors="replace"),
            "headers": scope_headers,
            "server": [self._server_host, self._server_port],
            "client": [self._client_host, self._client_port],
        }

        return scope

    # -------------------------------------------------------------------------
    # ASGI Receive / Send Callables
    # -------------------------------------------------------------------------

    async def _receive(self) -> Dict[str, Any]:
        """
            ASGI receive callable.

            Returns an ``http.request`` message containing the request
            body bytes and a ``more_body`` flag. On the first call,
            delivers the full body with ``more_body`` set to ``False``.

            :returns: An ASGI ``http.request`` message dictionary.
        """
        if not self._body_delivered:
            self._body_delivered = True
            message = {
                "type": "http.request",
                "body": self._body,
                "more_body": False,
            }
        else:
            # Subsequent calls return empty body
            message = {
                "type": "http.request",
                "body": b"",
                "more_body": False,
            }

        return message

    async def _send(self, message: Dict[str, Any]) -> None:
        """
            ASGI send callable with state machine enforcement.

            Expects ``http.response.start`` before ``http.response.body``.
            When ``more_body`` is ``False`` or absent in the body message,
            the response is finalized and written to the transport.

            :param message: An ASGI message dictionary.
        """
        message_type = message.get("type", "")

        if message_type == "http.response.start":
            if self._response_started:
                logger.error(
                    "Received duplicate http.response.start from application."
                )
                return

            self._response_status = message.get("status", 500)
            raw_headers = message.get("headers", [])

            self._response_headers = []
            for header_pair in raw_headers:
                if len(header_pair) == 2:
                    name = header_pair[0]
                    value = header_pair[1]
                    # Ensure bytes
                    if isinstance(name, str):
                        name = name.encode("latin-1")
                    if isinstance(value, str):
                        value = value.encode("latin-1")
                    self._response_headers.append((name, value))

            self._response_started = True
            self._state = _ParseState.RESPONSE_STARTED

        elif message_type == "http.response.body":
            if not self._response_started:
                logger.error(
                    "Received http.response.body before http.response.start. "
                    "Closing connection."
                )
                self._close_transport()
                return

            body = message.get("body", b"")
            more_body = message.get("more_body", False)

            if isinstance(body, str):
                body = body.encode("utf-8")

            # When this is the final (or only) body chunk, ensure a
            # Content-Length header is present so the browser knows
            # the response is complete on keep-alive connections.
            if not more_body:
                has_content_length = False
                for hdr_name, _ in self._response_headers:
                    if hdr_name.lower() == b"content-length":
                        has_content_length = True
                        break

                if not has_content_length:
                    self._response_headers.append(
                        (b"content-length", str(len(body)).encode("ascii"))
                    )

            self._write_response(
                self._response_status,
                self._response_headers,
                body,
            )

            if not more_body:
                self._response_complete = True
                self._state = _ParseState.DONE

        else:
            logger.warning(
                "Received unknown ASGI message type: %s",
                message_type,
            )

        return


    # -------------------------------------------------------------------------
    # Response Writing
    # -------------------------------------------------------------------------

    def _write_response(
        self,
        status: int,
        headers: List[Tuple[bytes, bytes]],
        body: bytes,
    ) -> None:
        """
            Serialize and write an HTTP response to the transport.

            Constructs the status line, header lines, and body into
            a single byte sequence and writes it to the transport.

            :param status: The HTTP status code.
            :param headers: The response headers as (name, value) byte tuples.
            :param body: The response body bytes.
        """
        if self._transport is None:
            return

        reason = _get_reason_phrase(status)
        status_line = "HTTP/1.1 {} {}\r\n".format(status, reason)

        parts = [status_line.encode("ascii")]

        for name, value in headers:
            if isinstance(name, str):
                name = name.encode("latin-1")
            if isinstance(value, str):
                value = value.encode("latin-1")
            parts.append(name + b": " + value + b"\r\n")

        parts.append(b"\r\n")
        parts.append(body)

        response_bytes = b"".join(parts)

        self._transport.write(response_bytes)

        return

    # -------------------------------------------------------------------------
    # Keep-Alive Logic
    # -------------------------------------------------------------------------

    def _should_keep_alive(
        self,
        version: str,
        headers: List[Tuple[bytes, bytes]],
    ) -> bool:
        """
            Determine whether the connection should be kept alive.

            For HTTP/1.1, connections are kept alive by default unless
            the Connection header is set to "close". For HTTP/1.0,
            connections are closed by default unless the Connection
            header is set to "keep-alive".

            :param version: The HTTP version string (e.g. "1.1" or "1.0").
            :param headers: The parsed headers as (name, value) byte tuples.

            :returns: ``True`` if the connection should be kept alive.
        """
        connection_value = None

        for name, value in headers:
            if name.lower() == b"connection":
                connection_value = value.decode("ascii", errors="replace").lower().strip()
                break

        if version == "1.1":
            if connection_value == "close":
                keep_alive = False
            else:
                keep_alive = True
        elif version == "1.0":
            if connection_value == "keep-alive":
                keep_alive = True
            else:
                keep_alive = False
        else:
            # Default to close for unknown versions
            keep_alive = False

        return keep_alive

    # -------------------------------------------------------------------------
    # Error Response
    # -------------------------------------------------------------------------

    def _send_error_response(self, status_code: int, message: str) -> None:
        """
            Write a simple error response and close the connection.

            The response includes Content-Type, Content-Length, and
            Connection: close headers.

            :param status_code: The HTTP status code for the error.
            :param message: The error message body text.
        """
        body = message.encode("utf-8")

        headers = [
            (b"content-type", b"text/plain; charset=utf-8"),
            (b"content-length", str(len(body)).encode("ascii")),
            (b"connection", b"close"),
        ]

        self._write_response(status_code, headers, body)
        self._close_transport()

        return

    # -------------------------------------------------------------------------
    # Request Handling
    # -------------------------------------------------------------------------

    def _schedule_request_handling(self) -> None:
        """
            Schedule the ASGI application invocation on the event loop.

            Creates an asyncio task that calls ``_handle_request`` to
            process the parsed HTTP request through the ASGI application.
        """
        loop = asyncio.get_event_loop()
        loop.create_task(self._handle_request())
        return

    async def _handle_request(self) -> None:
        """
            Invoke the ASGI application with the parsed request.

            Constructs the ASGI scope, then calls the application with
            the scope, receive, and send callables. Handles errors
            differently based on the debug mode setting.

            In debug mode, unhandled exceptions produce a 500 response
            containing the exception type, message, and traceback. In
            non-debug mode, a generic 500 response is returned.

            When a request logger is configured, logs the method, path,
            status code, and elapsed time in milliseconds after each
            request completes or errors.
        """
        # Record the start time for request logging.
        self._request_start_time = time.monotonic()

        # Split the request target into path and query string
        target = self._request_target
        query = ""

        question_pos = target.find("?")
        if question_pos >= 0:
            path = target[:question_pos]
            query = target[question_pos + 1:]
        else:
            path = target

        # Extract the HTTP version number
        version = self._http_version
        if version.upper().startswith("HTTP/"):
            version_number = version[5:]
        else:
            version_number = "1.1"

        scope = self._build_scope(
            method=self._request_method,
            path=path,
            query=query,
            version=self._http_version,
            headers=self._headers,
        )

        # Reset send state for this request
        self._response_started = False
        self._response_complete = False
        self._response_status = 0
        self._response_headers = []
        self._body_delivered = False

        try:
            await self._app(scope, self._receive, self._send)
        except Exception as exc:
            if not self._response_started:
                error_status = 500

                if self._debug:
                    exc_type = type(exc).__name__
                    exc_message = str(exc)
                    exc_traceback = traceback.format_exc()

                    error_body = "{}: {}\n\n{}".format(
                        exc_type, exc_message, exc_traceback
                    )

                    self._send_error_response(error_status, error_body)
                else:
                    self._send_error_response(error_status, "Internal Server Error")

                # Log the error request if a request logger is configured.
                self._log_request(self._request_method, path, error_status)
            else:
                logger.error(
                    "Exception after response started: %s: %s",
                    type(exc).__name__,
                    exc,
                )
                self._close_transport()

            return

        # Log the completed request if a request logger is configured.
        self._log_request(self._request_method, path, self._response_status)

        # Handle keep-alive after successful response
        if self._response_complete:
            keep_alive = self._should_keep_alive(version_number, self._headers)

            if keep_alive:
                self._reset_for_next_request()
                await self._wait_for_next_request()
            else:
                self._close_transport()
        else:
            self._close_transport()

        return

    # -------------------------------------------------------------------------
    # Request Logging
    # -------------------------------------------------------------------------

    def _log_request(
        self,
        method: str,
        path: str,
        status_code: int,
    ) -> None:
        """
            Log a completed request using the request logger.

            Calculates the elapsed time since the request started and
            delegates formatting and logging to the request logger
            instance. Does nothing if no request logger is configured.

            :param method: The HTTP method string.
            :param path: The request path string.
            :param status_code: The HTTP response status code.
        """
        if self._request_logger is None:
            return

        elapsed = time.monotonic() - self._request_start_time
        elapsed_ms = round(elapsed * 1000, 2)

        log_line = self._request_logger._format_log(
            method, path, status_code, elapsed_ms,
        )

        logger.info(log_line)

        return

    # -------------------------------------------------------------------------
    # Keep-Alive Management
    # -------------------------------------------------------------------------

    def _reset_for_next_request(self) -> None:
        """
            Reset the handler state to accept a new request on the
            same connection.

            Clears all parsed request data and resets the parse state
            to await a new request line.
        """
        self._state = _ParseState.AWAITING_REQUEST_LINE
        self._request_method = ""
        self._request_target = ""
        self._http_version = ""
        self._headers = []
        self._body = b""
        self._content_length = 0
        self._chunked = False
        self._response_status = 0
        self._response_headers = []
        self._response_started = False
        self._response_complete = False
        self._body_delivered = False

        return

    async def _wait_for_next_request(self) -> None:
        """
            Wait for the next request on a keep-alive connection.

            If data is already in the buffer from a pipelined request,
            processes it immediately. Otherwise, waits up to the
            keep-alive timeout for new data. If the timeout expires,
            the connection is closed silently.
        """
        # Check if there is already data in the buffer
        if len(self._buffer) > 0:
            self._process_buffer()
            return

        # Wait for new data with a timeout
        try:
            data_event = asyncio.Event()
            original_data_received = self.data_received

            def _on_data(data: bytes) -> None:
                self._buffer += data
                data_event.set()
                return

            self.data_received = _on_data

            await asyncio.wait_for(
                data_event.wait(),
                timeout=KEEPALIVE_TIMEOUT_SECONDS,
            )

            # Restore original data_received and process
            self.data_received = original_data_received
            self._process_buffer()

        except asyncio.TimeoutError:
            # Keep-alive timeout expired, close the connection
            self.data_received = original_data_received
            logger.debug(
                "Keep-alive timeout for %s:%d",
                self._client_host,
                self._client_port,
            )
            self._close_transport()

        return

    # -------------------------------------------------------------------------
    # Transport Helpers
    # -------------------------------------------------------------------------

    def _close_transport(self) -> None:
        """
            Close the underlying TCP transport if it is still open.
        """
        if self._transport is not None:
            self._transport.close()

        return
