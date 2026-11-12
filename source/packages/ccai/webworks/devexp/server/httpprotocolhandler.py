"""
    HTTP/1.1 protocol handler for the development ASGI server.

    This module provides the :class:`HTTPProtocolHandler` class, an
    ``asyncio.Protocol`` subclass that parses HTTP/1.1 requests from
    a TCP connection, constructs ASGI scope dictionaries, and bridges
    the ASGI receive/send interface to raw TCP transport.

    The handler supports keep-alive connections, incremental chunked
    transfer decoding, a request body size limit, streamed responses
    (``Transfer-Encoding: chunked`` when the application does not declare
    a ``Content-Length``), ``http.disconnect`` delivery, per-request ID
    correlation and debug-mode error reporting.
"""

import asyncio
import logging
import re
import time
import traceback

from typing import Any, Callable, Dict, List, Optional, Tuple
from urllib.parse import unquote_to_bytes

from ccai.webworks.devexp.logging.devlogger import generate_request_id
from ccai.webworks.devexp.logging.devlogger import set_request_id


logger = logging.getLogger(__name__)


# =============================================================================
# Constants
# =============================================================================

MAX_REQUEST_LINE_BYTES: int = 8192
"""Maximum allowed size of the HTTP request line in bytes."""

MAX_HEADER_BLOCK_BYTES: int = 32768
"""Maximum allowed size of the HTTP header block in bytes."""

MAX_REQUEST_BODY_BYTES: int = 16 * 1024 * 1024
"""Default maximum allowed size of a request body in bytes (16 MiB)."""

MAX_CHUNK_SIZE_LINE_BYTES: int = 1024
"""Maximum allowed size of one chunk-size line, including chunk extensions."""

KEEPALIVE_TIMEOUT_SECONDS: float = 30.0
"""Idle timeout in seconds for keep-alive connections."""

HEADER_TERMINATOR: bytes = b"\r\n\r\n"
"""Byte sequence that terminates the HTTP header block."""

LINE_TERMINATOR: bytes = b"\r\n"
"""Byte sequence that terminates an HTTP line."""

REQUEST_ID_HEADER: bytes = b"x-request-id"
"""Header that carries the request ID in both directions."""

_METHOD_PATTERN = re.compile(r"^[!#$%&'*+\-.^_`|~0-9A-Za-z]+$")
"""An HTTP method is a token (RFC 9110 section 5.6.2)."""

_VERSION_PATTERN = re.compile(r"^HTTP/[0-9]\.[0-9]$")
"""The HTTP-version field of a request line."""

_HEADER_NAME_PATTERN = re.compile(rb"^[!#$%&'*+\-.^_`|~0-9A-Za-z]+$")
"""A header field name is a token (RFC 9110 section 5.1)."""

_HEADER_VALUE_FORBIDDEN = re.compile(rb"[\r\n\x00]")
"""Bytes that would end a header line early and let a value inject headers."""

_CHUNK_SIZE_PATTERN = re.compile(rb"^[0-9A-Fa-f]{1,16}$")
"""A chunk size is one or more hexadecimal digits and nothing else."""

_REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9._\-]{1,64}$")
"""Shape of a client-supplied request ID the server is willing to echo."""

_BODYLESS_STATUS_CODES = (204, 304)
"""Status codes whose responses never carry a body."""


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
# Errors
# =============================================================================

class ClientDisconnectedError(OSError):
    """
        Raised by the ASGI ``send`` callable when the client has gone away.

        The ASGI specification asks servers to raise an ``OSError`` subclass
        when an application sends on a closed connection, so a handler that
        only ever sends (a stream that never calls ``receive``) still learns
        that nobody is listening.
    """


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


_READING_STATES = (
    _ParseState.AWAITING_REQUEST_LINE,
    _ParseState.AWAITING_HEADERS,
    _ParseState.AWAITING_BODY,
)
"""States in which bytes from the client belong to the request being read."""


# =============================================================================
# Chunked Transfer Decoding
# =============================================================================

class _ChunkedDecoder:
    """
        Incremental decoder for a ``Transfer-Encoding: chunked`` request body.

        The decoder consumes bytes from the front of the connection buffer as
        they become complete and keeps its position between calls, so each
        packet is examined once. It stops exactly at the end of the chunked
        body -- after the trailer section and its terminating CRLF -- and
        leaves whatever follows (a pipelined request) in the buffer.

        :param max_body_bytes: The largest decoded body that is accepted.
    """

    INCOMPLETE = "incomplete"
    """More bytes are needed before the body is complete."""

    COMPLETE = "complete"
    """The terminating chunk, the trailers and the final CRLF were consumed."""

    MALFORMED = "malformed"
    """The framing is invalid; the request must be rejected with 400."""

    TOO_LARGE = "too_large"
    """The decoded body exceeds the limit; the request must be rejected with 413."""

    _EXPECT_SIZE = "size"
    _EXPECT_DATA = "data"
    _EXPECT_DATA_END = "data_end"
    _EXPECT_TRAILER = "trailer"

    def __init__(self, max_body_bytes: int):
        """
            Construct a _ChunkedDecoder.

            :param max_body_bytes: The largest decoded body that is accepted.
        """
        self._max_body_bytes = max_body_bytes
        self._body = bytearray()
        self._expect = self._EXPECT_SIZE
        self._chunk_remaining = 0
        self._trailer_bytes = 0
        return

    @property
    def body(self) -> bytes:
        """
            The body bytes decoded so far.

            :returns: The decoded bytes.
        """
        return bytes(self._body)

    def feed(self, buffer: bytearray) -> str:
        """
            Decode as much of the buffer as is complete.

            Consumed bytes are removed from the front of *buffer*.

            :param buffer: The connection buffer.

            :returns: One of :attr:`INCOMPLETE`, :attr:`COMPLETE`,
                :attr:`MALFORMED` or :attr:`TOO_LARGE`.
        """
        outcome = None

        while outcome is None:
            if self._expect == self._EXPECT_SIZE:
                outcome = self._read_size_line(buffer)
            elif self._expect == self._EXPECT_DATA:
                outcome = self._read_chunk_data(buffer)
            elif self._expect == self._EXPECT_DATA_END:
                outcome = self._read_chunk_end(buffer)
            else:
                outcome = self._read_trailer_line(buffer)

        return outcome

    def _read_size_line(self, buffer: bytearray) -> Optional[str]:
        """
            Read one chunk-size line.

            :param buffer: The connection buffer.

            :returns: An outcome when decoding must stop, else ``None``.
        """
        crlf_pos = buffer.find(LINE_TERMINATOR)

        if crlf_pos < 0:
            if len(buffer) > MAX_CHUNK_SIZE_LINE_BYTES:
                return self.MALFORMED
            return self.INCOMPLETE

        if crlf_pos > MAX_CHUNK_SIZE_LINE_BYTES:
            return self.MALFORMED

        size_line = bytes(buffer[:crlf_pos])

        # Chunk extensions (after a semicolon) carry no meaning here.
        semicolon_pos = size_line.find(b";")
        if semicolon_pos >= 0:
            size_line = size_line[:semicolon_pos]

        size_text = size_line.strip(b" \t")

        if _CHUNK_SIZE_PATTERN.match(size_text) is None:
            return self.MALFORMED

        chunk_size = int(size_text, 16)

        del buffer[:crlf_pos + len(LINE_TERMINATOR)]

        if chunk_size == 0:
            self._expect = self._EXPECT_TRAILER
            return None

        if len(self._body) + chunk_size > self._max_body_bytes:
            return self.TOO_LARGE

        self._chunk_remaining = chunk_size
        self._expect = self._EXPECT_DATA

        return None

    def _read_chunk_data(self, buffer: bytearray) -> Optional[str]:
        """
            Read the data of the current chunk.

            :param buffer: The connection buffer.

            :returns: An outcome when decoding must stop, else ``None``.
        """
        if len(buffer) == 0:
            return self.INCOMPLETE

        take = min(self._chunk_remaining, len(buffer))

        self._body.extend(buffer[:take])
        del buffer[:take]
        self._chunk_remaining -= take

        if self._chunk_remaining > 0:
            return self.INCOMPLETE

        self._expect = self._EXPECT_DATA_END

        return None

    def _read_chunk_end(self, buffer: bytearray) -> Optional[str]:
        """
            Read the CRLF that ends the data of a chunk.

            :param buffer: The connection buffer.

            :returns: An outcome when decoding must stop, else ``None``.
        """
        if len(buffer) < len(LINE_TERMINATOR):
            return self.INCOMPLETE

        if bytes(buffer[:len(LINE_TERMINATOR)]) != LINE_TERMINATOR:
            return self.MALFORMED

        del buffer[:len(LINE_TERMINATOR)]
        self._expect = self._EXPECT_SIZE

        return None

    def _read_trailer_line(self, buffer: bytearray) -> Optional[str]:
        """
            Read one line of the trailer section.

            Trailer fields are consumed and discarded. The empty line that
            ends the section ends the body.

            :param buffer: The connection buffer.

            :returns: An outcome when decoding must stop, else ``None``.
        """
        crlf_pos = buffer.find(LINE_TERMINATOR)

        if crlf_pos < 0:
            if self._trailer_bytes + len(buffer) > MAX_HEADER_BLOCK_BYTES:
                return self.MALFORMED
            return self.INCOMPLETE

        self._trailer_bytes += crlf_pos + len(LINE_TERMINATOR)

        if self._trailer_bytes > MAX_HEADER_BLOCK_BYTES:
            return self.MALFORMED

        del buffer[:crlf_pos + len(LINE_TERMINATOR)]

        if crlf_pos == 0:
            return self.COMPLETE

        return None


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
        max_body_bytes: Optional[int] = None,
        keepalive_timeout: Optional[float] = None,
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
            :param max_body_bytes: The largest request body accepted, in bytes.
                A larger body is answered with ``413``. Defaults to
                :data:`MAX_REQUEST_BODY_BYTES`.
            :param keepalive_timeout: Seconds an idle keep-alive connection is
                kept open. Defaults to :data:`KEEPALIVE_TIMEOUT_SECONDS`.
        """
        self._app = app
        self._server_host = server_host
        self._server_port = server_port
        self._debug = debug
        self._on_close = on_close
        self._request_logger = request_logger

        if max_body_bytes is not None:
            self._max_body_bytes = max_body_bytes
        else:
            self._max_body_bytes = MAX_REQUEST_BODY_BYTES

        if keepalive_timeout is not None:
            self._keepalive_timeout = keepalive_timeout
        else:
            self._keepalive_timeout = KEEPALIVE_TIMEOUT_SECONDS

        self._transport: Optional[asyncio.Transport] = None
        self._client_host: str = ""
        self._client_port: int = 0
        self._connection_closed: bool = False

        self._buffer: bytearray = bytearray()
        self._state: str = _ParseState.AWAITING_REQUEST_LINE

        # Parsed request components
        self._request_method: str = ""
        self._request_target: str = ""
        self._http_version: str = ""
        self._headers: List[Tuple[bytes, bytes]] = []
        self._body: bytes = b""
        self._content_length: int = 0
        self._chunked: bool = False
        self._chunk_decoder: Optional[_ChunkedDecoder] = None

        # ASGI send state
        self._response_status: int = 0
        self._response_headers: List[Tuple[bytes, bytes]] = []
        self._response_started: bool = False
        self._response_head_written: bool = False
        self._response_chunked: bool = False
        self._response_suppress_body: bool = False
        self._response_complete: bool = False
        self._keep_alive: bool = False

        # ASGI receive state
        self._body_delivered: bool = False
        self._disconnect_event: Optional[asyncio.Event] = None

        # Keep-alive idle timer handle
        self._keepalive_handle: Optional[asyncio.TimerHandle] = None

        # Request timing and correlation for logging
        self._request_start_time: float = 0.0
        self._request_id: Optional[str] = None

        return

    # -------------------------------------------------------------------------
    # Properties
    # -------------------------------------------------------------------------

    @property
    def is_idle(self) -> bool:
        """
            Whether the connection is between requests.

            An idle connection has no request in flight and no unread bytes,
            so closing it cannot lose work. The server core closes idle
            keep-alive connections immediately at shutdown.

            :returns: ``True`` if no request is being read or handled.
        """
        idle = self._state == _ParseState.AWAITING_REQUEST_LINE and len(self._buffer) == 0
        return idle

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
        self._cancel_keepalive_timer()

        if self._state not in _READING_STATES:
            # A request is being handled, so these bytes belong to a
            # pipelined request. They wait in the buffer, but only up to the
            # size of one complete request: a client must not be able to
            # grow the buffer without bound while a handler is running.
            pipelined_limit = MAX_REQUEST_LINE_BYTES + MAX_HEADER_BLOCK_BYTES + self._max_body_bytes

            if len(self._buffer) + len(data) > pipelined_limit:
                logger.warning(
                    "Closing connection from %s:%d: too many bytes received while a request was in progress.",
                    self._client_host,
                    self._client_port,
                )
                self._close_transport()
                return

        self._buffer.extend(data)
        self._process_buffer()

        return

    def connection_lost(self, exc: Optional[Exception]) -> None:
        """
            Called when the TCP connection is lost or closed.

            Cleans up internal state, releases any ``receive`` call that is
            waiting so the application sees ``http.disconnect``, and invokes
            the ``on_close`` callback if one was provided.

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

        self._cancel_keepalive_timer()

        self._connection_closed = True
        self._transport = None

        if self._disconnect_event is not None:
            self._disconnect_event.set()

        if self._on_close is not None:
            self._on_close(self)

        return

    def close(self) -> None:
        """
            Close the connection.

            Used by the server core at shutdown. Closing is idempotent.
        """
        self._close_transport()
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
            request line, the header block and the body.
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
        # A client may send an empty line before a request line; RFC 9112
        # section 2.2 asks servers to ignore it.
        while self._buffer.startswith(LINE_TERMINATOR):
            del self._buffer[:len(LINE_TERMINATOR)]

        crlf_pos = self._buffer.find(LINE_TERMINATOR)

        if crlf_pos < 0:
            # No complete line yet; check if buffer exceeds limit
            if len(self._buffer) > MAX_REQUEST_LINE_BYTES:
                self._send_error_response(400, "Request line too long")
            return

        request_line = bytes(self._buffer[:crlf_pos])

        if len(request_line) > MAX_REQUEST_LINE_BYTES:
            self._send_error_response(400, "Request line too long")
            return

        parsed = self._parse_request_line(request_line)

        if parsed is None:
            self._send_error_response(400, "Malformed request line")
            return

        self._request_method, self._request_target, self._http_version = parsed
        del self._buffer[:crlf_pos + len(LINE_TERMINATOR)]
        self._state = _ParseState.AWAITING_HEADERS

        return

    def _try_parse_headers(self) -> None:
        """
            Attempt to extract the header block from the buffer.

            Looks for the double-CRLF header terminator. If the header
            block exceeds the maximum allowed size, sends a 431 error
            and closes the connection. The body framing is then validated:
            a ``Content-Length`` must be a plain non-negative decimal number
            no larger than the body limit, and a ``Transfer-Encoding`` must
            be ``chunked``.
        """
        if self._buffer.startswith(LINE_TERMINATOR):
            # A request without header fields: the request line is followed
            # directly by the empty line.
            header_block = b""
            consumed = len(LINE_TERMINATOR)
        else:
            term_pos = self._buffer.find(HEADER_TERMINATOR)

            if term_pos < 0:
                # No complete header block yet; check if buffer exceeds limit
                if len(self._buffer) > MAX_HEADER_BLOCK_BYTES:
                    self._send_error_response(431, "Request header fields too large")
                return

            header_block = bytes(self._buffer[:term_pos])
            consumed = term_pos + len(HEADER_TERMINATOR)

        if len(header_block) > MAX_HEADER_BLOCK_BYTES:
            self._send_error_response(431, "Request header fields too large")
            return

        self._headers = self._parse_headers(header_block)
        del self._buffer[:consumed]

        # Determine body handling
        self._content_length = 0
        self._chunked = False
        self._chunk_decoder = None

        content_length_values = []
        transfer_encoding_values = []
        expects_continue = False

        for name, value in self._headers:
            lower_name = name.lower()
            if lower_name == b"content-length":
                content_length_values.append(value)
            elif lower_name == b"transfer-encoding":
                transfer_encoding_values.append(value)
            elif lower_name == b"expect":
                if value.strip().lower() == b"100-continue":
                    expects_continue = True

        if len(transfer_encoding_values) > 0:
            if len(content_length_values) > 0:
                # A message with both framings is the classic request
                # smuggling vector; refuse it rather than pick one.
                self._send_error_response(400, "Both Content-Length and Transfer-Encoding were sent")
                return

            codings = []
            for value in transfer_encoding_values:
                for coding in value.split(b","):
                    codings.append(coding.strip().lower())

            if codings != [b"chunked"]:
                self._send_error_response(400, "Unsupported Transfer-Encoding")
                return

            self._chunked = True
            self._chunk_decoder = _ChunkedDecoder(self._max_body_bytes)

        elif len(content_length_values) > 0:
            first_value = content_length_values[0]

            for value in content_length_values:
                if value != first_value:
                    self._send_error_response(400, "Invalid Content-Length")
                    return

            # int() would also accept a sign, underscores and surrounding
            # whitespace; only plain decimal digits are a valid length.
            if not first_value.isdigit() or len(first_value) > 18:
                self._send_error_response(400, "Invalid Content-Length")
                return

            self._content_length = int(first_value)

            if self._content_length > self._max_body_bytes:
                self._send_error_response(413, "Request body too large")
                return

        if self._content_length > 0 or self._chunked:
            if expects_continue and self._transport is not None:
                self._transport.write(b"HTTP/1.1 100 Continue\r\n\r\n")

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
            processing state. Bytes that follow the body stay in the
            buffer for the next request on the connection.
        """
        if self._chunked:
            outcome = self._chunk_decoder.feed(self._buffer)

            if outcome == _ChunkedDecoder.COMPLETE:
                self._body = self._chunk_decoder.body
                self._chunk_decoder = None
                self._state = _ParseState.PROCESSING
                self._schedule_request_handling()
            elif outcome == _ChunkedDecoder.MALFORMED:
                self._send_error_response(400, "Malformed chunked request body")
            elif outcome == _ChunkedDecoder.TOO_LARGE:
                self._send_error_response(413, "Request body too large")
        else:
            if len(self._buffer) >= self._content_length:
                self._body = bytes(self._buffer[:self._content_length])
                del self._buffer[:self._content_length]
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

            The target is decoded as Latin-1 so that every byte survives
            unchanged; :meth:`_build_scope` turns it back into the raw path
            and decodes the percent-encoded form as UTF-8.

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

        method = method_bytes.decode("latin-1")
        target = target_bytes.decode("latin-1")
        version = version_bytes.decode("latin-1")

        if _METHOD_PATTERN.match(method) is None:
            return None

        if _VERSION_PATTERN.match(version) is None:
            return None

        if len(target) == 0:
            return None

        for char in target:
            # Control characters have no place in a request target.
            if ord(char) < 0x21 or ord(char) == 0x7F:
                return None

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
            Decode a complete HTTP chunked transfer-encoded body.

            Parses chunk size lines and concatenates chunk data until
            the terminal zero-length chunk, its trailers and the final
            CRLF are found. Returns ``None`` if the data is incomplete
            or malformed.

            The connection itself is decoded incrementally by
            :class:`_ChunkedDecoder`; this method decodes a body that is
            already fully in hand.

            :param data: The raw chunked body bytes.

            :returns: The decoded body bytes, or ``None`` if the
                chunked body is not complete and well formed.
        """
        decoder = _ChunkedDecoder(self._max_body_bytes)
        outcome = decoder.feed(bytearray(data))

        decoded = None

        if outcome == _ChunkedDecoder.COMPLETE:
            decoded = decoder.body

        return decoded

    def _split_request_target(self, target: str) -> Tuple[str, str]:
        """
            Split a request target into its path and query string.

            Handles the origin form (``/path?query``), the absolute form a
            proxy sends (``http://host/path?query``, from which the scheme
            and authority are dropped) and the asterisk form (``*``).

            :param target: The request target from the request line.

            :returns: A tuple of (path, query) strings. The query has no
                leading ``?``.
        """
        remainder = target
        lowered = target.lower()

        for scheme_prefix in ("http://", "https://"):
            if lowered.startswith(scheme_prefix):
                after_scheme = target[len(scheme_prefix):]
                slash_pos = after_scheme.find("/")
                question_pos = after_scheme.find("?")

                if slash_pos >= 0 and (question_pos < 0 or slash_pos < question_pos):
                    remainder = after_scheme[slash_pos:]
                elif question_pos >= 0:
                    remainder = "/" + after_scheme[question_pos:]
                else:
                    remainder = "/"
                break

        query = ""

        question_pos = remainder.find("?")
        if question_pos >= 0:
            path = remainder[:question_pos]
            query = remainder[question_pos + 1:]
        else:
            path = remainder

        if len(path) == 0:
            path = "/"

        return path, query


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

        # The target was decoded as Latin-1, so encoding it the same way
        # restores the exact bytes the client sent. The decoded path is
        # those bytes percent-decoded and read as UTF-8, as ASGI requires.
        raw_path = path.encode("latin-1", errors="replace")
        decoded_path = unquote_to_bytes(raw_path).decode("utf-8", errors="replace")

        scope = {
            "type": "http",
            "asgi": {"version": "3.0"},
            "http_version": http_version,
            "method": method,
            "path": decoded_path,
            "raw_path": raw_path,
            "root_path": "",
            "scheme": "http",
            "query_string": query.encode("latin-1", errors="replace"),
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

            The first call returns an ``http.request`` message containing
            the full request body with ``more_body`` set to ``False``.

            Every later call waits until the client disconnects or the
            response has been sent in full, and then returns
            ``http.disconnect``. A handler can therefore await ``receive``
            to learn that the client has gone away, and a handler that
            loops on ``receive`` waits instead of spinning.

            :returns: An ASGI ``http.request`` or ``http.disconnect``
                message dictionary.
        """
        if not self._body_delivered:
            self._body_delivered = True
            message = {
                "type": "http.request",
                "body": self._body,
                "more_body": False,
            }
        else:
            disconnect_event = self._get_disconnect_event()
            await disconnect_event.wait()
            message = {"type": "http.disconnect"}

        return message

    def _get_disconnect_event(self) -> asyncio.Event:
        """
            Get the event that marks the end of the current request cycle.

            The event is created on first use and is already set when the
            connection has closed or the response is complete.

            :returns: The disconnect event for the current request.
        """
        if self._disconnect_event is None:
            self._disconnect_event = asyncio.Event()

            if self._connection_closed or self._response_complete:
                self._disconnect_event.set()

        return self._disconnect_event

    async def _send(self, message: Dict[str, Any]) -> None:
        """
            ASGI send callable with state machine enforcement.

            Expects ``http.response.start`` before ``http.response.body``.
            The status line and headers are written once, with the first
            body message. A response whose headers carry no
            ``Content-Length`` and whose first body message has
            ``more_body`` set is streamed with ``Transfer-Encoding:
            chunked`` (or, for an HTTP/1.0 client, delimited by closing the
            connection).

            :param message: An ASGI message dictionary.

            :raises ValueError: If the status code or a header name or value
                is not valid; nothing is written in that case.
            :raises ClientDisconnectedError: If the client has disconnected.
        """
        message_type = message.get("type", "")

        if message_type == "http.response.start":
            if self._response_started:
                logger.error(
                    "Received duplicate http.response.start from application."
                )
                return

            status = message.get("status", 500)

            if not isinstance(status, int) or status < 100 or status > 999:
                errmsg = "Invalid HTTP status code in http.response.start: {!r}".format(status)
                raise ValueError(errmsg)

            raw_headers = message.get("headers", [])

            response_headers = []
            for header_pair in raw_headers:
                if len(header_pair) == 2:
                    name = header_pair[0]
                    value = header_pair[1]
                    # Ensure bytes
                    if isinstance(name, str):
                        name = name.encode("latin-1")
                    if isinstance(value, str):
                        value = value.encode("latin-1")

                    self._validate_response_header(name, value)

                    response_headers.append((bytes(name), bytes(value)))

            self._response_status = status
            self._response_headers = response_headers
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

            if self._response_complete:
                logger.error(
                    "Received http.response.body after the response was completed."
                )
                return

            if self._transport is None:
                raise ClientDisconnectedError("The client disconnected before the response was complete.")

            body = message.get("body", b"")
            more_body = message.get("more_body", False)

            if isinstance(body, str):
                body = body.encode("utf-8")

            if not self._response_head_written:
                self._begin_response(body, more_body)

            self._write_body_chunk(body)
            self._state = _ParseState.RESPONSE_BODY

            if not more_body:
                self._finish_response()

        else:
            logger.warning(
                "Received unknown ASGI message type: %s",
                message_type,
            )

        return

    def _validate_response_header(self, name: bytes, value: bytes) -> None:
        """
            Reject a response header that could corrupt the response.

            A CR, LF or NUL in a name or value would end the header line
            early, so a value built from user input (a redirect ``Location``
            for example) could inject headers or a second response.

            :param name: The header name bytes.
            :param value: The header value bytes.

            :raises ValueError: If the name is not a token or the value
                contains CR, LF or NUL.
        """
        if not isinstance(name, (bytes, bytearray)) or not isinstance(value, (bytes, bytearray)):
            errmsg = "Response header names and values must be bytes or str."
            raise ValueError(errmsg)

        if _HEADER_NAME_PATTERN.match(bytes(name)) is None:
            errmsg = "Invalid response header name: {!r}".format(bytes(name))
            raise ValueError(errmsg)

        if _HEADER_VALUE_FORBIDDEN.search(bytes(value)) is not None:
            errmsg = "The value of response header {!r} contains CR, LF or NUL.".format(bytes(name))
            raise ValueError(errmsg)

        return


    # -------------------------------------------------------------------------
    # Response Writing
    # -------------------------------------------------------------------------

    def _begin_response(self, first_body: bytes, more_body: bool) -> None:
        """
            Decide how the response body is framed and write the response head.

            Called once, with the first ``http.response.body`` message.

            :param first_body: The first body bytes.
            :param more_body: Whether more body messages will follow.
        """
        headers = list(self._response_headers)

        has_content_length = False
        has_transfer_encoding = False
        has_connection = False
        has_request_id = False
        app_requests_close = False

        for hdr_name, hdr_value in headers:
            lower_name = hdr_name.lower()
            if lower_name == b"content-length":
                has_content_length = True
            elif lower_name == b"transfer-encoding":
                has_transfer_encoding = True
            elif lower_name == b"connection":
                has_connection = True
                if hdr_value.strip().lower() == b"close":
                    app_requests_close = True
            elif lower_name == REQUEST_ID_HEADER:
                has_request_id = True

        version_number = self._get_version_number()
        keep_alive = self._should_keep_alive(version_number, self._headers)

        if app_requests_close:
            keep_alive = False

        status = self._response_status
        is_bodyless = status in _BODYLESS_STATUS_CODES or 100 <= status < 200

        self._response_chunked = False
        self._response_suppress_body = False

        if self._request_method == "HEAD" or is_bodyless:
            # The response carries headers only. A HEAD response still
            # reports the length the matching GET would have had.
            self._response_suppress_body = True

            if not is_bodyless and not has_content_length and not has_transfer_encoding and not more_body:
                headers.append((b"content-length", str(len(first_body)).encode("ascii")))

        elif has_content_length or has_transfer_encoding:
            # The application declared the framing; the body is passed
            # through as it is sent.
            pass

        elif not more_body:
            # The whole body is in hand, so its length can be declared and
            # the connection stays usable for the next request.
            headers.append((b"content-length", str(len(first_body)).encode("ascii")))

        elif version_number == "1.1":
            headers.append((b"transfer-encoding", b"chunked"))
            self._response_chunked = True

        else:
            # HTTP/1.0 has no chunked encoding: the end of the body is the
            # end of the connection.
            keep_alive = False

        if not keep_alive and not has_connection:
            headers.append((b"connection", b"close"))

        if self._request_id is not None and not has_request_id:
            headers.append((REQUEST_ID_HEADER, self._request_id.encode("ascii")))

        self._keep_alive = keep_alive

        if self._transport is not None:
            self._transport.write(self._serialize_head(status, headers))

        self._response_head_written = True

        return

    def _write_body_chunk(self, body: bytes) -> None:
        """
            Write one piece of the response body with the chosen framing.

            :param body: The body bytes of one ``http.response.body`` message.
        """
        if self._transport is None:
            return

        if self._response_suppress_body:
            return

        if len(body) == 0:
            # In chunked framing a zero-length chunk ends the body, so an
            # empty message writes nothing.
            return

        if self._response_chunked:
            size_line = format(len(body), "x").encode("ascii") + LINE_TERMINATOR
            self._transport.write(size_line + bytes(body) + LINE_TERMINATOR)
        else:
            self._transport.write(bytes(body))

        return

    def _finish_response(self) -> None:
        """
            Complete the response after the final body message.

            Writes the terminating chunk of a chunked body, marks the
            response complete and releases any waiting ``receive`` call.
        """
        if self._response_chunked and self._transport is not None:
            self._transport.write(b"0" + LINE_TERMINATOR + LINE_TERMINATOR)

        self._response_complete = True
        self._state = _ParseState.DONE

        if self._disconnect_event is not None:
            self._disconnect_event.set()

        return

    def _serialize_head(
        self,
        status: int,
        headers: List[Tuple[bytes, bytes]],
    ) -> bytes:
        """
            Serialize the status line and header block of a response.

            :param status: The HTTP status code.
            :param headers: The response headers as (name, value) byte tuples.

            :returns: The response head, ending with the empty line.
        """
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

        head_bytes = b"".join(parts)

        return head_bytes

    def _write_response(
        self,
        status: int,
        headers: List[Tuple[bytes, bytes]],
        body: bytes,
    ) -> None:
        """
            Serialize and write a complete HTTP response to the transport.

            Constructs the status line, header lines, and body into
            a single byte sequence and writes it to the transport. This
            writes a whole response at once and is used for the server's
            own error responses; application responses go through
            :meth:`_send`, which writes the head once and then the body
            pieces as they arrive.

            :param status: The HTTP status code.
            :param headers: The response headers as (name, value) byte tuples.
            :param body: The response body bytes.
        """
        if self._transport is None:
            return

        response_bytes = self._serialize_head(status, headers) + bytes(body)

        self._transport.write(response_bytes)

        return

    # -------------------------------------------------------------------------
    # Keep-Alive Logic
    # -------------------------------------------------------------------------

    def _get_version_number(self) -> str:
        """
            The HTTP version number of the current request.

            :returns: The version number such as ``"1.1"``.
        """
        version = self._http_version

        if version.upper().startswith("HTTP/"):
            version_number = version[5:]
        else:
            version_number = "1.1"

        return version_number

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
            Connection: close headers. No further bytes from the client
            are parsed afterwards.

            :param status_code: The HTTP status code for the error.
            :param message: The error message body text.
        """
        body = message.encode("utf-8")

        headers = [
            (b"content-type", b"text/plain; charset=utf-8"),
            (b"content-length", str(len(body)).encode("ascii")),
            (b"connection", b"close"),
        ]

        if self._request_id is not None:
            headers.append((REQUEST_ID_HEADER, self._request_id.encode("ascii")))

        self._write_response(status_code, headers, body)
        self._response_status = status_code
        self._state = _ParseState.DONE
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

            Asks for the *running* loop rather than the current one. This
            runs from a protocol callback, which asyncio only ever invokes
            from inside a running loop, so the stricter call says what is
            actually required. ``get_event_loop`` no longer returns a loop
            in 3.12 when none is set, and would either raise here or, worse,
            hand back a loop that is not the one driving this connection.
        """
        loop = asyncio.get_running_loop()
        loop.create_task(self._handle_request())
        return

    def _resolve_request_id(self) -> str:
        """
            Choose the ID that correlates the log lines of this request.

            A well-formed ``X-Request-ID`` sent by the client is honoured so
            a trace can span services; anything else is replaced by a
            generated ID.

            :returns: The request ID string.
        """
        request_id = None

        for name, value in self._headers:
            if name.lower() == REQUEST_ID_HEADER:
                candidate = value.decode("latin-1")
                if _REQUEST_ID_PATTERN.match(candidate) is not None:
                    request_id = candidate
                break

        if request_id is None:
            request_id = generate_request_id()

        return request_id

    async def _handle_request(self) -> None:
        """
            Invoke the ASGI application with the parsed request.

            Constructs the ASGI scope, then calls the application with
            the scope, receive, and send callables. Handles errors
            differently based on the debug mode setting.

            In debug mode, unhandled exceptions produce a 500 response
            containing the exception type, message, and traceback. In
            non-debug mode, a generic 500 response is returned. An
            application that returns without sending a response also
            produces a 500.

            A request ID is set for the duration of the call so every log
            line written while the request is handled carries it, and it is
            returned to the client in the ``X-Request-ID`` response header.

            When a request logger is configured, logs the method, path,
            status code, and elapsed time in milliseconds after each
            request completes or errors.
        """
        # Record the start time for request logging.
        self._request_start_time = time.monotonic()

        # Split the request target into path and query string
        path, query = self._split_request_target(self._request_target)

        scope = self._build_scope(
            method=self._request_method,
            path=path,
            query=query,
            version=self._http_version,
            headers=self._headers,
        )

        # Reset send state for this request
        self._response_started = False
        self._response_head_written = False
        self._response_chunked = False
        self._response_suppress_body = False
        self._response_complete = False
        self._response_status = 0
        self._response_headers = []
        self._keep_alive = False
        self._body_delivered = False
        self._disconnect_event = None

        # This coroutine runs as its own task, so the context variable is
        # private to this request and needs no reset afterwards.
        self._request_id = self._resolve_request_id()
        set_request_id(self._request_id)

        try:
            await self._app(scope, self._receive, self._send)
        except ClientDisconnectedError:
            logger.debug(
                "Client %s:%d disconnected before the response was complete.",
                self._client_host,
                self._client_port,
            )
            self._close_transport()
            return
        except Exception as exc:
            if not self._response_head_written:
                error_status = 500

                logger.error(
                    "Unhandled exception in application for %s %s",
                    self._request_method,
                    path,
                    exc_info=True,
                )

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

        if not self._response_complete:
            if not self._response_head_written and not self._connection_closed:
                # Nothing has reached the client, so it can still be told
                # that the request failed instead of receiving an empty reply.
                logger.error(
                    "The application returned without sending a response for %s %s.",
                    self._request_method,
                    path,
                )

                if self._debug:
                    error_body = "The application returned without sending a complete response."
                else:
                    error_body = "Internal Server Error"

                self._send_error_response(500, error_body)
                self._log_request(self._request_method, path, 500)
            elif self._connection_closed:
                # The client left and the application stopped streaming to
                # it, which is how a stream normally ends.
                logger.debug(
                    "The application stopped after the client disconnected from %s %s.",
                    self._request_method,
                    path,
                )
                self._log_request(self._request_method, path, self._response_status)
            else:
                logger.error(
                    "The application returned before completing the response for %s %s.",
                    self._request_method,
                    path,
                )
                self._close_transport()

            return

        # Log the completed request if a request logger is configured.
        self._log_request(self._request_method, path, self._response_status)

        # Handle keep-alive after successful response
        if self._keep_alive and self._transport is not None:
            self._reset_for_next_request()
            self._await_next_request()
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
            to await a new request line. Bytes already received for the
            next request stay in the buffer.
        """
        self._state = _ParseState.AWAITING_REQUEST_LINE
        self._request_method = ""
        self._request_target = ""
        self._http_version = ""
        self._headers = []
        self._body = b""
        self._content_length = 0
        self._chunked = False
        self._chunk_decoder = None
        self._response_status = 0
        self._response_headers = []
        self._response_started = False
        self._response_head_written = False
        self._response_chunked = False
        self._response_suppress_body = False
        self._response_complete = False
        self._keep_alive = False
        self._body_delivered = False
        self._disconnect_event = None
        self._request_id = None

        return

    def _await_next_request(self) -> None:
        """
            Prepare a keep-alive connection for its next request.

            If a pipelined request is already in the buffer it is
            processed immediately. Otherwise an idle timer is started;
            when it expires before any data arrives the connection is
            closed silently.
        """
        if len(self._buffer) > 0:
            self._process_buffer()

        if self._state == _ParseState.AWAITING_REQUEST_LINE and self._transport is not None:
            loop = asyncio.get_running_loop()
            self._keepalive_handle = loop.call_later(
                self._keepalive_timeout,
                self._on_keepalive_timeout,
            )

        return

    def _on_keepalive_timeout(self) -> None:
        """
            Close a keep-alive connection that stayed idle for too long.
        """
        self._keepalive_handle = None

        logger.debug(
            "Keep-alive timeout for %s:%d",
            self._client_host,
            self._client_port,
        )

        self._close_transport()

        return

    def _cancel_keepalive_timer(self) -> None:
        """
            Cancel the idle timer of a keep-alive connection, if one is running.
        """
        if self._keepalive_handle is not None:
            self._keepalive_handle.cancel()
            self._keepalive_handle = None

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
