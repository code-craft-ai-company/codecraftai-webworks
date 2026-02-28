"""
    Connection manager module for the WSGI layer.
    
    This module provides the ConnectionManager class for managing HTTP connections
    including keep-alive handling, connection tracking, and timeout management.
"""

import threading
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Set, Tuple

from automojo.webworks.wsgi.serverconfig import ServerConfig


@dataclass
class ConnectionInfo:
    """
        Information about an active connection.
        
        Tracks connection state including creation time, last activity,
        and request count for keep-alive management.
    """
    
    connection_id: str
    client_address: Tuple[str, int]
    created_at: float = field(default_factory=time.time)
    last_activity: float = field(default_factory=time.time)
    request_count: int = 0
    is_keep_alive: bool = False
    http_version: str = "HTTP/1.1"
    
    def update_activity(self) -> None:
        """
            Update the last activity timestamp.
        """
        self.last_activity = time.time()
        return
    
    def increment_request_count(self) -> None:
        """
            Increment the request count for this connection.
        """
        self.request_count += 1
        self.update_activity()
        return
    
    def idle_time(self) -> float:
        """
            Get the time since last activity.
            
            :returns: Idle time in seconds.
        """
        rtnval = time.time() - self.last_activity
        return rtnval
    
    def age(self) -> float:
        """
            Get the age of the connection.
            
            :returns: Connection age in seconds.
        """
        rtnval = time.time() - self.created_at
        return rtnval


class ConnectionManager:
    """
        Manages HTTP connections for the WSGI server.
        
        This class handles keep-alive connection management, connection tracking,
        and timeout handling. It enforces maximum connection limits and closes
        idle connections based on the configured keepalive timeout.
    """
    
    def __init__(self, config: Optional[ServerConfig] = None):
        """
            Construct a connection manager.
            
            :param config: Server configuration. If None, uses defaults.
        """
        if config is not None:
            self._config = config
        else:
            self._config = ServerConfig()
        
        self._keepalive_timeout = self._config.keepalive
        self._max_connections = self._config.max_connections
        self._request_timeout = self._config.timeout
        
        # Connection tracking
        self._connections: Dict[str, ConnectionInfo] = {}
        self._lock = threading.Lock()
        
        # Connection ID counter
        self._next_id = 0
        self._id_lock = threading.Lock()
        return
    
    @property
    def keepalive_timeout(self) -> int:
        """
            Get the keep-alive timeout in seconds.
            
            :returns: Keep-alive timeout.
        """
        return self._keepalive_timeout
    
    @property
    def max_connections(self) -> int:
        """
            Get the maximum number of connections.
            
            :returns: Maximum connections limit.
        """
        return self._max_connections
    
    @property
    def request_timeout(self) -> int:
        """
            Get the request timeout in seconds.
            
            :returns: Request timeout.
        """
        return self._request_timeout
    
    @property
    def active_connection_count(self) -> int:
        """
            Get the number of active connections.
            
            :returns: Number of active connections.
        """
        with self._lock:
            rtnval = len(self._connections)
        return rtnval


    def _generate_connection_id(self) -> str:
        """
            Generate a unique connection ID.
            
            :returns: Unique connection ID string.
        """
        with self._id_lock:
            conn_id = self._next_id
            self._next_id += 1
        
        rtnval = f"conn-{conn_id}"
        return rtnval
    
    def should_keep_alive(
        self,
        http_version: str,
        headers: Dict[str, str]
    ) -> bool:
        """
            Determine if a connection should be kept alive.
            
            Keep-alive behavior depends on HTTP version and Connection header:
            - HTTP/1.1: Keep-alive by default unless Connection: close
            - HTTP/1.0: Close by default unless Connection: keep-alive
            
            :param http_version: HTTP version string (e.g., "HTTP/1.1").
            :param headers: Request headers dictionary.
            
            :returns: True if connection should be kept alive, False otherwise.
        """
        # If keepalive timeout is 0, never keep alive
        if self._keepalive_timeout <= 0:
            return False
        
        # Normalize header lookup (case-insensitive)
        connection_header = None
        for header_name, header_value in headers.items():
            if header_name.lower() == "connection":
                connection_header = header_value.lower().strip()
                break
        
        # Determine keep-alive based on HTTP version
        http_version_upper = http_version.upper()
        
        if http_version_upper == "HTTP/1.1":
            # HTTP/1.1 defaults to keep-alive
            if connection_header == "close":
                rtnval = False
            else:
                rtnval = True
        elif http_version_upper == "HTTP/1.0":
            # HTTP/1.0 defaults to close
            if connection_header == "keep-alive":
                rtnval = True
            else:
                rtnval = False
        else:
            # Unknown version, default to close
            rtnval = False
        
        return rtnval
    
    def register_connection(
        self,
        client_address: Tuple[str, int],
        http_version: str = "HTTP/1.1",
        is_keep_alive: bool = False
    ) -> Optional[str]:
        """
            Register a new connection.
            
            :param client_address: Client address tuple (host, port).
            :param http_version: HTTP version string.
            :param is_keep_alive: Whether the connection is keep-alive.
            
            :returns: Connection ID if registered, None if max connections reached.
        """
        with self._lock:
            # Check if max connections reached
            if len(self._connections) >= self._max_connections:
                return None
            
            # Generate connection ID
            conn_id = self._generate_connection_id()
            
            # Create connection info
            conn_info = ConnectionInfo(
                connection_id=conn_id,
                client_address=client_address,
                http_version=http_version,
                is_keep_alive=is_keep_alive
            )
            
            self._connections[conn_id] = conn_info
        
        rtnval = conn_id
        return rtnval
    
    def unregister_connection(self, connection_id: str) -> bool:
        """
            Unregister a connection.
            
            :param connection_id: Connection ID to unregister.
            
            :returns: True if connection was unregistered, False if not found.
        """
        with self._lock:
            if connection_id in self._connections:
                del self._connections[connection_id]
                rtnval = True
            else:
                rtnval = False
        
        return rtnval
    
    def get_connection(self, connection_id: str) -> Optional[ConnectionInfo]:
        """
            Get connection information.
            
            :param connection_id: Connection ID to look up.
            
            :returns: ConnectionInfo if found, None otherwise.
        """
        with self._lock:
            rtnval = self._connections.get(connection_id)
        
        return rtnval
    
    def update_connection_activity(self, connection_id: str) -> bool:
        """
            Update the last activity time for a connection.
            
            :param connection_id: Connection ID to update.
            
            :returns: True if connection was updated, False if not found.
        """
        with self._lock:
            conn_info = self._connections.get(connection_id)
            if conn_info is not None:
                conn_info.update_activity()
                rtnval = True
            else:
                rtnval = False
        
        return rtnval
    
    def increment_request_count(self, connection_id: str) -> bool:
        """
            Increment the request count for a connection.
            
            :param connection_id: Connection ID to update.
            
            :returns: True if connection was updated, False if not found.
        """
        with self._lock:
            conn_info = self._connections.get(connection_id)
            if conn_info is not None:
                conn_info.increment_request_count()
                rtnval = True
            else:
                rtnval = False
        
        return rtnval
    
    def set_keep_alive(self, connection_id: str, is_keep_alive: bool) -> bool:
        """
            Set the keep-alive status for a connection.
            
            :param connection_id: Connection ID to update.
            :param is_keep_alive: Whether the connection should be kept alive.
            
            :returns: True if connection was updated, False if not found.
        """
        with self._lock:
            conn_info = self._connections.get(connection_id)
            if conn_info is not None:
                conn_info.is_keep_alive = is_keep_alive
                rtnval = True
            else:
                rtnval = False
        
        return rtnval
    
    def can_accept_connection(self) -> bool:
        """
            Check if a new connection can be accepted.
            
            :returns: True if under max connections limit, False otherwise.
        """
        with self._lock:
            rtnval = len(self._connections) < self._max_connections
        
        return rtnval


    def is_connection_idle(self, connection_id: str) -> bool:
        """
            Check if a connection is idle beyond the keepalive timeout.
            
            :param connection_id: Connection ID to check.
            
            :returns: True if connection is idle, False otherwise.
        """
        with self._lock:
            conn_info = self._connections.get(connection_id)
            if conn_info is None:
                return False
            
            idle_time = conn_info.idle_time()
            rtnval = idle_time > self._keepalive_timeout
        
        return rtnval
    
    def is_connection_timed_out(self, connection_id: str) -> bool:
        """
            Check if a connection has exceeded the request timeout.
            
            :param connection_id: Connection ID to check.
            
            :returns: True if connection has timed out, False otherwise.
        """
        if self._request_timeout <= 0:
            return False
        
        with self._lock:
            conn_info = self._connections.get(connection_id)
            if conn_info is None:
                return False
            
            idle_time = conn_info.idle_time()
            rtnval = idle_time > self._request_timeout
        
        return rtnval
    
    def get_idle_connections(self) -> Set[str]:
        """
            Get all connections that are idle beyond the keepalive timeout.
            
            :returns: Set of connection IDs that are idle.
        """
        idle_connections: Set[str] = set()
        
        with self._lock:
            for conn_id, conn_info in self._connections.items():
                if conn_info.is_keep_alive:
                    idle_time = conn_info.idle_time()
                    if idle_time > self._keepalive_timeout:
                        idle_connections.add(conn_id)
        
        rtnval = idle_connections
        return rtnval
    
    def get_timed_out_connections(self) -> Set[str]:
        """
            Get all connections that have exceeded the request timeout.
            
            :returns: Set of connection IDs that have timed out.
        """
        if self._request_timeout <= 0:
            return set()
        
        timed_out_connections: Set[str] = set()
        
        with self._lock:
            for conn_id, conn_info in self._connections.items():
                idle_time = conn_info.idle_time()
                if idle_time > self._request_timeout:
                    timed_out_connections.add(conn_id)
        
        rtnval = timed_out_connections
        return rtnval
    
    def close_idle_connections(self) -> Set[str]:
        """
            Close all idle connections and return their IDs.
            
            This method removes connections that have been idle beyond
            the keepalive timeout from the tracking dictionary.
            
            :returns: Set of connection IDs that were closed.
        """
        closed_connections: Set[str] = set()
        
        with self._lock:
            # Find idle connections
            to_close: Set[str] = set()
            for conn_id, conn_info in self._connections.items():
                if conn_info.is_keep_alive:
                    idle_time = conn_info.idle_time()
                    if idle_time > self._keepalive_timeout:
                        to_close.add(conn_id)
            
            # Remove idle connections
            for conn_id in to_close:
                del self._connections[conn_id]
                closed_connections.add(conn_id)
        
        rtnval = closed_connections
        return rtnval
    
    def close_timed_out_connections(self) -> Set[str]:
        """
            Close all timed out connections and return their IDs.
            
            This method removes connections that have exceeded the request
            timeout from the tracking dictionary.
            
            :returns: Set of connection IDs that were closed.
        """
        if self._request_timeout <= 0:
            return set()
        
        closed_connections: Set[str] = set()
        
        with self._lock:
            # Find timed out connections
            to_close: Set[str] = set()
            for conn_id, conn_info in self._connections.items():
                idle_time = conn_info.idle_time()
                if idle_time > self._request_timeout:
                    to_close.add(conn_id)
            
            # Remove timed out connections
            for conn_id in to_close:
                del self._connections[conn_id]
                closed_connections.add(conn_id)
        
        rtnval = closed_connections
        return rtnval
    
    def cleanup(self) -> Tuple[Set[str], Set[str]]:
        """
            Perform cleanup of idle and timed out connections.
            
            :returns: Tuple of (idle_closed, timed_out_closed) connection ID sets.
        """
        idle_closed = self.close_idle_connections()
        timed_out_closed = self.close_timed_out_connections()
        
        rtnval = (idle_closed, timed_out_closed)
        return rtnval
    
    def clear_all(self) -> int:
        """
            Clear all tracked connections.
            
            :returns: Number of connections that were cleared.
        """
        with self._lock:
            count = len(self._connections)
            self._connections.clear()
        
        rtnval = count
        return rtnval
    
    def get_all_connection_ids(self) -> Set[str]:
        """
            Get all active connection IDs.
            
            :returns: Set of all connection IDs.
        """
        with self._lock:
            rtnval = set(self._connections.keys())
        
        return rtnval
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """
            Get statistics about current connections.
            
            :returns: Dictionary with connection statistics.
        """
        with self._lock:
            total = len(self._connections)
            keep_alive_count = sum(
                1 for conn in self._connections.values() if conn.is_keep_alive
            )
            
            if total > 0:
                total_requests = sum(
                    conn.request_count for conn in self._connections.values()
                )
                avg_requests = total_requests / total
            else:
                total_requests = 0
                avg_requests = 0.0
        
        rtnval = {
            "total_connections": total,
            "keep_alive_connections": keep_alive_count,
            "max_connections": self._max_connections,
            "total_requests": total_requests,
            "avg_requests_per_connection": avg_requests,
            "keepalive_timeout": self._keepalive_timeout,
            "request_timeout": self._request_timeout,
        }
        return rtnval

