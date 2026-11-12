"""
    Socket reader module for the WSGI layer.

    This module provides the SocketReader class, a bounded, buffered reader over
    a client socket. The HTTP parser reads request lines, header lines and bodies
    through it so that line length limits are enforced while the bytes arrive and
    so that a total deadline can be placed on a read sequence.
"""

import socket
import time
from typing import Any, Optional

from ccai.webworks.wsgi.exceptions import LineTooLong


# Number of bytes requested from the socket in one receive
DEFAULT_READ_SIZE: int = 8192


class SocketReader:
    """
        Bounded, buffered reader over a client socket.

        The reader keeps the bytes it has received but not yet handed out, so one
        reader must be used for the whole life of a connection. Bytes of a second
        request that arrive together with the first stay in the buffer for the
        next call.

        End of stream is reported through the return values and never raised:
        'read_line' returns a line without its line feed and 'read_exact' returns
        fewer bytes than requested. Timeouts are not handled here, 'socket.timeout'
        is left to bubble to the caller that decides what a timeout means.
    """

    def __init__(
        self,
        sock: Any,
        read_ahead: bool = True,
        read_size: int = DEFAULT_READ_SIZE
    ):
        """
            Construct a socket reader.

            :param sock: Client socket to read from. Only 'recv' is required. The
                         'settimeout' method is used when a timeout or a deadline
                         has been set on the reader.
            :param read_ahead: If True, receive in blocks and keep what is left over
                               for the next read. If False, never take a byte from
                               the socket that the current read does not need, which
                               is what a caller that owns the socket and reads from
                               it afterwards requires.
            :param read_size: Number of bytes to request in one receive.
        """
        self._socket = sock
        self._read_ahead = read_ahead
        self._read_size = read_size
        self._buffer = bytearray()
        self._timeout: Optional[float] = None
        self._deadline: Optional[float] = None
        self._end_of_stream = False
        return

    @property
    def socket(self) -> Any:
        """
            Get the socket being read.

            :returns: The client socket.
        """
        return self._socket

    @property
    def buffered_size(self) -> int:
        """
            Get the number of bytes received but not yet handed out.

            :returns: Number of buffered bytes.
        """
        rtnval = len(self._buffer)
        return rtnval

    @property
    def has_buffered_data(self) -> bool:
        """
            Check whether bytes are waiting in the buffer.

            :returns: True if at least one byte is buffered.
        """
        rtnval = len(self._buffer) > 0
        return rtnval

    @property
    def end_of_stream(self) -> bool:
        """
            Check whether the peer has closed its side of the connection.

            :returns: True once a receive has returned no data.
        """
        return self._end_of_stream

    @property
    def timeout(self) -> Optional[float]:
        """
            Get the timeout applied to each receive.

            :returns: Timeout in seconds or None if the reader does not set one.
        """
        return self._timeout

    @property
    def deadline(self) -> Optional[float]:
        """
            Get the deadline for the current read sequence.

            :returns: Deadline as a 'time.monotonic' value or None if not set.
        """
        return self._deadline

    def set_timeout(self, timeout: Optional[float]) -> None:
        """
            Set the timeout applied to each receive.

            :param timeout: Timeout in seconds, or None to leave the timeout of
                            the socket as it is.
        """
        self._timeout = timeout
        return

    def set_deadline(self, seconds: Optional[float]) -> None:
        """
            Set a total time limit for the reads that follow.

            A timeout only limits the wait for the next byte, so a client that
            sends one byte at a time can hold a connection open for as long as it
            likes. A deadline limits the whole sequence of reads.

            :param seconds: Seconds from now until the deadline, or None to clear
                            the deadline.
        """
        if seconds is None:
            self._deadline = None
        else:
            self._deadline = time.monotonic() + seconds
        return

    def _receive(self, size: int) -> bytes:
        """
            Receive bytes from the socket, honouring the timeout and the deadline.

            :param size: Maximum number of bytes to receive.

            :returns: Bytes received. Empty when the peer closed the connection.

            :raises: socket.timeout if the deadline has passed or the receive
                     timed out.
        """
        wait_time = self._timeout

        if self._deadline is not None:
            remaining = self._deadline - time.monotonic()
            if remaining <= 0:
                errmsg = "The deadline for reading from the connection has passed"
                raise socket.timeout(errmsg)

            if wait_time is None or remaining < wait_time:
                wait_time = remaining

        if wait_time is not None:
            self._socket.settimeout(wait_time)

        data = self._socket.recv(size)

        if len(data) == 0:
            self._end_of_stream = True

        return data

    def read_line(self, max_size: int = 0) -> bytes:
        """
            Read one line, up to and including its line feed.

            The limit is checked as the bytes arrive, so a peer that never sends
            a line feed cannot make the reader hold more than 'max_size' bytes
            plus one receive block.

            :param max_size: Maximum line size in bytes including the line ending
                             (0 = unlimited).

            :returns: The line including its line feed. If the stream ended first,
                      the bytes read so far without a line feed, which is empty
                      when the stream ended before any byte of the line.

            :raises: LineTooLong if the line is longer than 'max_size'.
            :raises: socket.timeout if the deadline passed or a receive timed out.
        """
        search_from = 0

        while True:
            newline_pos = self._buffer.find(b"\n", search_from)

            if newline_pos >= 0:
                line_size = newline_pos + 1
                if max_size > 0 and line_size > max_size:
                    raise LineTooLong(max_size)

                line = bytes(self._buffer[:line_size])
                del self._buffer[:line_size]
                break

            # No line feed yet. The line is already at least one byte longer
            # than what is buffered.
            if max_size > 0 and len(self._buffer) >= max_size:
                raise LineTooLong(max_size)

            search_from = len(self._buffer)

            if self._read_ahead:
                data = self._receive(self._read_size)
            else:
                data = self._receive(1)

            if len(data) == 0:
                line = bytes(self._buffer)
                del self._buffer[:]
                break

            self._buffer.extend(data)

        return line

    def read_exact(self, size: int) -> bytes:
        """
            Read exactly the requested number of bytes.

            :param size: Number of bytes to read.

            :returns: The bytes read. Fewer than 'size' bytes only when the stream
                      ended first.

            :raises: socket.timeout if the deadline passed or a receive timed out.
        """
        parts = bytearray()
        remaining = size

        if remaining > 0 and len(self._buffer) > 0:
            taken = min(remaining, len(self._buffer))
            parts.extend(self._buffer[:taken])
            del self._buffer[:taken]
            remaining -= taken

        while remaining > 0:
            # Never ask for more than is needed, so nothing is read ahead here
            data = self._receive(min(remaining, self._read_size))

            if len(data) == 0:
                break

            parts.extend(data)
            remaining -= len(data)

        rtnval = bytes(parts)
        return rtnval

    def recv(self, size: int) -> bytes:
        """
            Receive up to 'size' bytes, buffered bytes first.

            This gives the reader the read side of the socket interface, so it can
            be handed to code that expects a socket.

            :param size: Maximum number of bytes to return.

            :returns: Bytes received. Empty when the peer closed the connection.
        """
        if len(self._buffer) > 0:
            taken = min(size, len(self._buffer))
            rtnval = bytes(self._buffer[:taken])
            del self._buffer[:taken]
        else:
            rtnval = self._receive(size)

        return rtnval
