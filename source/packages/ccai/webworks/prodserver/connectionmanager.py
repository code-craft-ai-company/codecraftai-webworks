"""
    Connection management module for the production server.

    This module provides the ConnectionManager class that tracks active
    connections, enforces connection limits, manages connection draining
    during graceful shutdown, and validates request size limits including
    request line size and header count.
"""

import logging
import time
import threading
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ccai.webworks.prodserver.serverconfig import ServerConfig


# Default logger for connection manager
_logger = logging.getLogger("webworks.prodserver.connectionmanager")


class ConnectionState(Enum):
    """
        Connection lifecycle states.

        Represents the possible states of a client connection during
        its lifecycle from active through closed.
    """
    ACTIVE = "active"
    IDLE = "idle"
    DRAINING = "draining"
    CLOSED = "closed"


@dataclass
class Connection:
    """
        Represents a client connection.

        Contains metadata about a single client connection including
        its identity, creation time, activity tracking, and keep-alive
        status.
    """

    conn_id: str
    created_at: float
    last_activity: float
    keep_alive: bool = True
    requests_handled: int = 0
    state: ConnectionState = ConnectionState.ACTIVE

    def as_dict(self) -> dict:
        """
            Convert the connection to a dictionary.

            :returns: Dictionary representation of the connection.
        """
        rtnval = {
            "conn_id": self.conn_id,
            "created_at": self.created_at,
            "last_activity": self.last_activity,
            "keep_alive": self.keep_alive,
            "requests_handled": self.requests_handled,
            "state": self.state.value,
        }

        return rtnval



class RequestValidationError(Exception):
    """
        Raised when a request fails size limit validation.

        Contains the HTTP status code that should be returned to the
        client and a descriptive error message.
    """

    def __init__(self, status_code: int, message: str):
        """
            Construct a RequestValidationError.

            :param status_code: The HTTP status code to return.
            :param message: Descriptive error message.
        """
        self._status_code = status_code
        self._message = message
        super().__init__(message)

        return

    @property
    def status_code(self) -> int:
        """
            Get the HTTP status code for this error.

            :returns: The HTTP status code.
        """
        return self._status_code


class ConnectionManager:
    """
        Manages connection lifecycle, limits, and request validation.

        Tracks active connections, enforces the max connections limit,
        provides connection draining during graceful shutdown, and
        validates request size limits including request line size and
        header count.
    """

    def __init__(self, config: "ServerConfig"):
        """
            Construct a ConnectionManager.

            :param config: Server configuration containing connection
                           limits and keep-alive settings.
        """
        self._config = config
        self._connections: Dict[str, Connection] = {}
        self._connection_count: int = 0
        self._lock: threading.Lock = threading.Lock()
        self._draining: bool = False

        return

    @property
    def connection_count(self) -> int:
        """
            Get the current number of tracked connections.

            :returns: The number of active connections.
        """
        return self._connection_count

    @property
    def is_draining(self) -> bool:
        """
            Check whether the connection manager is in draining mode.

            :returns: True if connection draining is active.
        """
        return self._draining

    @property
    def max_connections(self) -> Optional[int]:
        """
            Get the configured maximum connections limit.

            :returns: The max connections limit, or None if unlimited.
        """
        return self._config.max_connections

    @property
    def backlog(self) -> int:
        """
            Get the configured connection backlog size.

            :returns: The backlog queue size.
        """
        return self._config.backlog

    @property
    def keep_alive_timeout(self) -> int:
        """
            Get the configured keep-alive timeout in seconds.

            :returns: The keep-alive timeout value.
        """
        return self._config.keep_alive

    def accept_connection(self, conn_id: str) -> bool:
        """
            Accept a new connection if within the configured limits.

            Creates a new Connection record and tracks it. If the
            max_connections limit is configured and has been reached,
            the connection is rejected.

            :param conn_id: Unique identifier for the connection.

            :returns: True if the connection was accepted, False if
                      rejected due to limits or draining.
        """
        with self._lock:
            if self._draining:
                _logger.debug(
                    "Rejecting connection %s: server is draining",
                    conn_id
                )
                return False

            max_conns = self._config.max_connections
            if max_conns is not None and self._connection_count >= max_conns:
                _logger.warning(
                    "Rejecting connection %s: max connections limit reached (%d)",
                    conn_id,
                    max_conns
                )
                return False

            now = time.time()
            connection = Connection(
                conn_id=conn_id,
                created_at=now,
                last_activity=now,
                keep_alive=True,
                requests_handled=0,
                state=ConnectionState.ACTIVE,
            )

            self._connections[conn_id] = connection
            self._connection_count += 1

            _logger.debug(
                "Accepted connection %s (total: %d)",
                conn_id,
                self._connection_count
            )

        return True

    def close_connection(self, conn_id: str) -> None:
        """
            Close and remove a tracked connection.

            Marks the connection as closed and removes it from the
            active connections registry.

            :param conn_id: The identifier of the connection to close.
        """
        with self._lock:
            if conn_id in self._connections:
                self._connections[conn_id].state = ConnectionState.CLOSED
                del self._connections[conn_id]
                self._connection_count -= 1

                _logger.debug(
                    "Closed connection %s (total: %d)",
                    conn_id,
                    self._connection_count
                )

        return

    def record_activity(self, conn_id: str) -> None:
        """
            Record activity on a connection.

            Updates the last_activity timestamp and increments the
            requests_handled counter for the specified connection.

            :param conn_id: The identifier of the connection.
        """
        with self._lock:
            if conn_id in self._connections:
                conn = self._connections[conn_id]
                conn.last_activity = time.time()
                conn.requests_handled += 1
                conn.state = ConnectionState.ACTIVE

        return

    def mark_idle(self, conn_id: str) -> None:
        """
            Mark a connection as idle.

            Transitions the connection state to IDLE, indicating it
            is not currently processing a request.

            :param conn_id: The identifier of the connection.
        """
        with self._lock:
            if conn_id in self._connections:
                self._connections[conn_id].state = ConnectionState.IDLE

        return

    def get_connection(self, conn_id: str) -> Optional[Connection]:
        """
            Get a connection by its identifier.

            :param conn_id: The identifier of the connection.

            :returns: The Connection object, or None if not found.
        """
        with self._lock:
            rtnval = self._connections.get(conn_id)

        return rtnval

    def get_all_connections(self) -> Dict[str, Connection]:
        """
            Get a snapshot of all tracked connections.

            :returns: Dictionary mapping connection IDs to Connection objects.
        """
        with self._lock:
            rtnval = dict(self._connections)

        return rtnval

    def get_connection_count(self) -> int:
        """
            Get the current number of active connections.

            :returns: The connection count.
        """
        return self._connection_count

    def close_idle_connections(self) -> int:
        """
            Close all idle keep-alive connections.

            Identifies connections that are in the IDLE state with
            keep-alive enabled and closes them. This is used during
            graceful shutdown to release idle connections.

            :returns: The number of connections that were closed.
        """
        closed_count = 0

        with self._lock:
            idle_conn_ids = []

            for conn_id, conn in self._connections.items():
                if conn.state == ConnectionState.IDLE and conn.keep_alive:
                    idle_conn_ids.append(conn_id)

            for conn_id in idle_conn_ids:
                self._connections[conn_id].state = ConnectionState.CLOSED
                del self._connections[conn_id]
                self._connection_count -= 1
                closed_count += 1

        if closed_count > 0:
            _logger.info(
                "Closed %d idle keep-alive connection(s)",
                closed_count
            )

        return closed_count

    def close_expired_keep_alive_connections(self) -> int:
        """
            Close keep-alive connections that have exceeded the timeout.

            Identifies idle connections whose last activity is older
            than the configured keep-alive timeout and closes them.

            :returns: The number of connections that were closed.
        """
        closed_count = 0
        keep_alive_timeout = self._config.keep_alive
        now = time.time()

        with self._lock:
            expired_conn_ids = []

            for conn_id, conn in self._connections.items():
                if conn.keep_alive and conn.state == ConnectionState.IDLE:
                    idle_duration = now - conn.last_activity
                    if idle_duration > keep_alive_timeout:
                        expired_conn_ids.append(conn_id)

            for conn_id in expired_conn_ids:
                self._connections[conn_id].state = ConnectionState.CLOSED
                del self._connections[conn_id]
                self._connection_count -= 1
                closed_count += 1

        if closed_count > 0:
            _logger.info(
                "Closed %d expired keep-alive connection(s)",
                closed_count
            )

        return closed_count

    def drain_connections(self, timeout: float) -> bool:
        """
            Drain all connections during graceful shutdown.

            Sets the draining flag to reject new connections, closes
            idle keep-alive connections immediately, then waits for
            remaining active connections to complete within the
            specified timeout.

            :param timeout: Maximum time in seconds to wait for
                            active connections to close.

            :returns: True if all connections drained within the
                      timeout, False if the timeout was exceeded.
        """
        self._draining = True

        _logger.info("Connection draining started (timeout=%.1fs)", timeout)

        self.close_idle_connections()

        start_time = time.time()

        while True:
            elapsed = time.time() - start_time

            if elapsed >= timeout:
                remaining = self._connection_count
                if remaining > 0:
                    _logger.warning(
                        "Connection drain timeout exceeded with %d connection(s) remaining",
                        remaining
                    )
                    return False

                return True

            if self._connection_count == 0:
                _logger.info("All connections drained successfully")
                return True

            _logger.debug(
                "Waiting for %d connection(s) to drain (%.1fs / %.1fs)",
                self._connection_count,
                elapsed,
                timeout
            )

            time.sleep(0.25)

    def validate_request_line(self, request_line: str) -> None:
        """
            Validate the size of an HTTP request line.

            Checks that the request line does not exceed the configured
            limit_request_line value.

            :param request_line: The HTTP request line string.

            :raises: RequestValidationError if the request line exceeds
                     the configured limit.
        """
        limit = self._config.limit_request_line

        if limit > 0 and len(request_line) > limit:
            errmsg = (
                f"Request line too long: {len(request_line)} bytes "
                f"exceeds limit of {limit} bytes"
            )
            _logger.warning(errmsg)
            raise RequestValidationError(status_code=414, message=errmsg)

        return

    def validate_request_headers(self, header_count: int) -> None:
        """
            Validate the number of HTTP request headers.

            Checks that the number of headers does not exceed the
            configured limit_request_fields value.

            :param header_count: The number of headers in the request.

            :raises: RequestValidationError if the header count exceeds
                     the configured limit.
        """
        limit = self._config.limit_request_fields

        if limit > 0 and header_count > limit:
            errmsg = (
                f"Too many request headers: {header_count} "
                f"exceeds limit of {limit}"
            )
            _logger.warning(errmsg)
            raise RequestValidationError(status_code=431, message=errmsg)

        return

    def get_status(self) -> dict:
        """
            Get a summary of the connection manager status.

            :returns: Dictionary with connection status information.
        """
        with self._lock:
            active_count = 0
            idle_count = 0
            draining_count = 0

            for conn in self._connections.values():
                if conn.state == ConnectionState.ACTIVE:
                    active_count += 1
                elif conn.state == ConnectionState.IDLE:
                    idle_count += 1
                elif conn.state == ConnectionState.DRAINING:
                    draining_count += 1

            rtnval = {
                "total_connections": self._connection_count,
                "active_connections": active_count,
                "idle_connections": idle_count,
                "draining_connections": draining_count,
                "max_connections": self._config.max_connections,
                "backlog": self._config.backlog,
                "keep_alive_timeout": self._config.keep_alive,
                "is_draining": self._draining,
            }

        return rtnval

    def reset(self) -> None:
        """
            Reset the connection manager to its initial state.

            Clears all tracked connections and resets the draining flag.
            This is primarily used for testing purposes.
        """
        with self._lock:
            self._connections.clear()
            self._connection_count = 0
            self._draining = False

        return
