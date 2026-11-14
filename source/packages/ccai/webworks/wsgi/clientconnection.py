"""
    Client connection module for the WSGI layer.
    
    This module provides the ClientConnection class, the state a worker keeps
    for one accepted connection while it moves between waiting for a request
    and being served by a handler thread.
"""

import socket
from typing import Optional, Tuple

from ccai.webworks.wsgi.socketreader import SocketReader


class ClientConnection:
    """
        State of one accepted client connection.
        
        The reader belongs to the connection for its whole life, so bytes of a
        following request that were read ahead are not lost between requests.
    """
    
    def __init__(
        self,
        sock: socket.socket,
        address: Tuple[str, int],
        connection_id: Optional[str] = None,
        handshake_pending: bool = False
    ):
        """
            Construct a client connection.
            
            :param sock: The accepted client socket.
            :param address: Client address tuple (host, port).
            :param connection_id: ID the connection manager gave the connection.
            :param handshake_pending: True if the socket is a TLS socket whose
                                      handshake has not been performed yet.
        """
        self._socket = sock
        self._address = address
        self._connection_id = connection_id
        self._handshake_pending = handshake_pending
        self._reader = SocketReader(sock)
        self._idle_deadline: float = 0.0
        self._request_count: int = 0
        self._closed = False
        return
    
    @property
    def socket(self) -> socket.socket:
        """
            Get the client socket.
            
            :returns: The client socket.
        """
        return self._socket
    
    @property
    def address(self) -> Tuple[str, int]:
        """
            Get the client address.
            
            :returns: Client address tuple (host, port).
        """
        return self._address
    
    @property
    def connection_id(self) -> Optional[str]:
        """
            Get the ID the connection manager gave the connection.
            
            :returns: Connection ID or None if the connection is not registered.
        """
        return self._connection_id
    
    @property
    def reader(self) -> SocketReader:
        """
            Get the reader of the connection.
            
            :returns: The SocketReader that owns the read side of the socket.
        """
        return self._reader
    
    @property
    def handshake_pending(self) -> bool:
        """
            Check if the TLS handshake still has to be performed.
            
            :returns: True if the handshake has not been performed yet.
        """
        return self._handshake_pending
    
    @property
    def idle_deadline(self) -> float:
        """
            Get the time at which the connection is closed if it stays silent.
            
            :returns: Deadline as a 'time.monotonic' value.
        """
        return self._idle_deadline
    
    @property
    def request_count(self) -> int:
        """
            Get the number of requests served on the connection.
            
            :returns: Number of requests.
        """
        return self._request_count
    
    @property
    def closed(self) -> bool:
        """
            Check if the connection has been closed by the worker.
            
            :returns: True if the connection was closed.
        """
        return self._closed
    
    def set_handshake_done(self) -> None:
        """
            Record that the TLS handshake has been performed.
        """
        self._handshake_pending = False
        return
    
    def set_idle_deadline(self, deadline: float) -> None:
        """
            Set the time at which the connection is closed if it stays silent.
            
            :param deadline: Deadline as a 'time.monotonic' value.
        """
        self._idle_deadline = deadline
        return
    
    def increment_request_count(self) -> None:
        """
            Count one more request served on the connection.
        """
        self._request_count += 1
        return
    
    def has_pending_input(self) -> bool:
        """
            Check if input is waiting that the operating system will not report.
            
            Bytes the reader read ahead, and bytes a TLS socket has already
            decrypted, do not make the socket readable again. A connection with
            such input has to be served at once and not parked until it becomes
            readable.
            
            :returns: True if a read would return data without waiting.
        """
        rtnval = self._reader.has_buffered_data
        
        if not rtnval:
            pending = getattr(self._socket, "pending", None)
            if pending is not None and not self._handshake_pending:
                try:
                    rtnval = pending() > 0
                except (OSError, ValueError):
                    rtnval = False
        
        return rtnval
    
    def mark_closed(self) -> bool:
        """
            Record that the connection is being closed.
            
            :returns: True if this call closed it, False if it was closed before.
        """
        rtnval = not self._closed
        self._closed = True
        return rtnval
