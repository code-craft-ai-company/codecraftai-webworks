"""
    Tests for the SocketReader class in the WSGI layer.
    
    This module contains tests for the bounded, buffered reader the HTTP parser
    reads requests through.
"""

import socket
from typing import List

from ccai.webworks.wsgi.exceptions import LineTooLong
from ccai.webworks.wsgi.socketreader import SocketReader


class RecordingSocket:
    """
        Socket stand-in that serves fixed data and records how it was read.
    """
    
    def __init__(self, data: bytes):
        """
            Construct a recording socket with data to read.
        """
        self._data = data
        self._position = 0
        self.recv_sizes: List[int] = []
        self.timeouts: List[float] = []
        return
    
    def recv(self, size: int) -> bytes:
        """
            Read data from the socket.
        """
        self.recv_sizes.append(size)
        end = min(self._position + size, len(self._data))
        rtnval = self._data[self._position:end]
        self._position = end
        return rtnval
    
    def settimeout(self, timeout: float) -> None:
        """
            Record the timeout that was set.
        """
        self.timeouts.append(timeout)
        return
    
    @property
    def bytes_taken(self) -> int:
        """
            Number of bytes that have been read from the socket.
        """
        return self._position


def test_read_line_returns_line_with_line_feed():
    """
        Test that read_line returns one line including its line ending.
    """
    reader = SocketReader(RecordingSocket(b"GET / HTTP/1.1\r\nHost: x\r\n"))
    
    line = reader.read_line()
    
    if line != b"GET / HTTP/1.1\r\n":
        errmsg = f"Expected the first line with its line ending, got {line!r}"
        raise AssertionError(errmsg)
    
    return


def test_read_line_keeps_bytes_read_ahead_for_next_read():
    """
        Test that bytes received with one line are returned by the next read.
    """
    reader = SocketReader(RecordingSocket(b"first\r\nsecond\r\n"))
    
    reader.read_line()
    line = reader.read_line()
    
    if line != b"second\r\n":
        errmsg = f"Expected the second line from the buffer, got {line!r}"
        raise AssertionError(errmsg)
    
    return


def test_read_line_raises_when_line_exceeds_limit():
    """
        Test that a line without a line feed is refused once it passes the limit.
    """
    sock = RecordingSocket(b"a" * 100000)
    reader = SocketReader(sock)
    
    raised = False
    try:
        reader.read_line(max_size=1024)
    except LineTooLong:
        raised = True
    
    if not raised:
        errmsg = "Expected LineTooLong for a line longer than the limit"
        raise AssertionError(errmsg)
    
    return


def test_read_line_stops_reading_at_the_limit():
    """
        Test that an over-long line is not accumulated beyond the limit.
    """
    sock = RecordingSocket(b"a" * 100000)
    reader = SocketReader(sock, read_size=512)
    
    try:
        reader.read_line(max_size=1024)
    except LineTooLong:
        pass
    
    # The limit plus at most one receive block may have been taken
    if sock.bytes_taken > 1024 + 512:
        errmsg = f"Expected reading to stop near the 1024 byte limit, {sock.bytes_taken} bytes were read"
        raise AssertionError(errmsg)
    
    return


def test_read_line_accepts_line_of_exactly_the_limit():
    """
        Test that a line whose size equals the limit is returned.
    """
    reader = SocketReader(RecordingSocket(b"abc\r\n"))
    
    line = reader.read_line(max_size=5)
    
    if line != b"abc\r\n":
        errmsg = f"Expected the line of exactly 5 bytes, got {line!r}"
        raise AssertionError(errmsg)
    
    return


def test_read_line_returns_partial_line_at_end_of_stream():
    """
        Test that read_line returns the bytes without a line feed when the stream ends.
    """
    reader = SocketReader(RecordingSocket(b"GET / HT"))
    
    line = reader.read_line()
    
    if line != b"GET / HT":
        errmsg = f"Expected the partial line, got {line!r}"
        raise AssertionError(errmsg)
    
    if reader.end_of_stream is not True:
        errmsg = "Expected end_of_stream to be True after the stream ended"
        raise AssertionError(errmsg)
    
    return


def test_read_exact_returns_fewer_bytes_at_end_of_stream():
    """
        Test that read_exact returns what there is when the stream ends early.
    """
    reader = SocketReader(RecordingSocket(b"short"))
    
    data = reader.read_exact(100)
    
    if data != b"short":
        errmsg = f"Expected the 5 bytes that were available, got {data!r}"
        raise AssertionError(errmsg)
    
    return


def test_read_exact_uses_buffered_bytes_first():
    """
        Test that read_exact returns bytes read ahead by read_line before new ones.
    """
    reader = SocketReader(RecordingSocket(b"line\r\nbody-bytes"))
    
    reader.read_line()
    data = reader.read_exact(10)
    
    if data != b"body-bytes":
        errmsg = f"Expected the body bytes, got {data!r}"
        raise AssertionError(errmsg)
    
    return


def test_reader_without_read_ahead_takes_only_the_line():
    """
        Test that a reader that must not read ahead leaves the rest in the socket.
    """
    sock = RecordingSocket(b"first\r\nsecond\r\n")
    reader = SocketReader(sock, read_ahead=False)
    
    reader.read_line()
    
    if sock.bytes_taken != len(b"first\r\n"):
        errmsg = f"Expected exactly the first line to be taken, {sock.bytes_taken} bytes were read"
        raise AssertionError(errmsg)
    
    return


def test_passed_deadline_raises_timeout_without_reading():
    """
        Test that a read after the deadline raises socket.timeout.
    """
    sock = RecordingSocket(b"data\r\n")
    reader = SocketReader(sock)
    reader.set_deadline(-1.0)
    
    raised = False
    try:
        reader.read_line()
    except socket.timeout:
        raised = True
    
    if not raised:
        errmsg = "Expected socket.timeout once the deadline has passed"
        raise AssertionError(errmsg)
    
    if len(sock.recv_sizes) != 0:
        errmsg = "Expected no receive after the deadline has passed"
        raise AssertionError(errmsg)
    
    return


def test_deadline_shortens_the_receive_timeout():
    """
        Test that the time left until the deadline limits the wait of a receive.
    """
    sock = RecordingSocket(b"data\r\n")
    reader = SocketReader(sock)
    reader.set_timeout(30.0)
    reader.set_deadline(2.0)
    
    reader.read_line()
    
    if len(sock.timeouts) == 0 or sock.timeouts[0] > 2.0:
        errmsg = f"Expected a receive timeout of at most 2 seconds, got {sock.timeouts}"
        raise AssertionError(errmsg)
    
    return


def test_reader_does_not_set_timeout_when_none_configured():
    """
        Test that the reader leaves the timeout of the socket alone by default.
    """
    sock = RecordingSocket(b"data\r\n")
    reader = SocketReader(sock)
    
    reader.read_line()
    
    if len(sock.timeouts) != 0:
        errmsg = f"Expected settimeout not to be called, got {sock.timeouts}"
        raise AssertionError(errmsg)
    
    return
