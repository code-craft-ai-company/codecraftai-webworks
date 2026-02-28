"""
    Worker process module for the WSGI layer.
    
    This module provides the Worker class for handling HTTP requests in the
    built-in WSGI server. Workers accept connections from the socket listener
    and process HTTP requests by invoking the WSGI application.
"""

import io
import logging
import os
import select
import socket
import sys
import threading
import time
import traceback
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple

from automojo.webworks.wsgi.serverconfig import ServerConfig
from automojo.webworks.wsgi.socketlistener import SocketListener
from automojo.webworks.wsgi.httpparser import HTTPParser
from automojo.webworks.wsgi.httpwriter import HTTPWriter
from automojo.webworks.wsgi.connectionmanager import ConnectionManager
from automojo.webworks.wsgi.startresponse import StartResponse
from automojo.webworks.wsgi.exceptions import (
    RequestParseError,
    RequestTimeout,
    WorkerError,
)


# Default logger for worker
_logger = logging.getLogger("webworks.wsgi.worker")


class Worker:
    """
        Worker process that handles HTTP requests.
        
        This class implements the worker process for the built-in WSGI server.
        Each worker accepts connections from the shared socket listener and
        processes HTTP requests by invoking the WSGI application.
        
        Workers support both synchronous and threaded request handling based
        on the server configuration.
    """
    
    def __init__(
        self,
        app: Callable[[Dict[str, Any], Callable], Iterable[bytes]],
        listener: SocketListener,
        config: Optional[ServerConfig] = None,
        worker_id: int = 0
    ):
        """
            Construct a worker.
            
            :param app: The WSGI application callable.
            :param listener: The socket listener for accepting connections.
            :param config: Server configuration. If None, uses defaults.
            :param worker_id: Unique identifier for this worker.
        """
        self._app = app
        self._listener = listener
        
        if config is not None:
            self._config = config
        else:
            self._config = ServerConfig()
        
        self._worker_id = worker_id
        
        # Create HTTP parser and connection manager
        self._parser = HTTPParser(self._config)
        self._connection_manager = ConnectionManager(self._config)
        
        # Worker state
        self._running = False
        self._shutdown_requested = False
        self._active_connections = 0
        self._total_requests = 0
        self._lock = threading.Lock()
        
        # Thread pool for threaded worker class
        self._thread_pool: Optional[ThreadPoolExecutor] = None
        
        # Server address for environ construction
        self._server_addr: Tuple[str, int] = (self._config.host, self._config.port)
        
        # Determine URL scheme
        if self._listener.ssl_enabled:
            self._scheme = "https"
        else:
            self._scheme = "http"
        
        return
    
    @property
    def worker_id(self) -> int:
        """
            Get the worker ID.
            
            :returns: Worker ID.
        """
        return self._worker_id
    
    @property
    def is_running(self) -> bool:
        """
            Check if the worker is running.
            
            :returns: True if worker is running.
        """
        return self._running
    
    @property
    def active_connections(self) -> int:
        """
            Get the number of active connections.
            
            :returns: Number of active connections.
        """
        with self._lock:
            rtnval = self._active_connections
        return rtnval
    
    @property
    def total_requests(self) -> int:
        """
            Get the total number of requests processed.
            
            :returns: Total request count.
        """
        with self._lock:
            rtnval = self._total_requests
        return rtnval
    
    @property
    def config(self) -> ServerConfig:
        """
            Get the server configuration.
            
            :returns: ServerConfig instance.
        """
        return self._config


    def run(self) -> None:
        """
            Main worker loop.
            
            Accepts connections from the socket listener and handles requests.
            Supports both synchronous and threaded request handling based on
            the worker_class configuration.
            
            This method blocks until shutdown() is called.
        """
        self._running = True
        self._shutdown_requested = False
        
        # Initialize thread pool if using threaded worker class
        if self._config.worker_class == "thread" and self._config.threads > 1:
            self._thread_pool = ThreadPoolExecutor(max_workers=self._config.threads)
        
        _logger.info(
            "Worker %d started (pid=%d, threads=%d)",
            self._worker_id,
            os.getpid(),
            self._config.threads
        )
        
        try:
            self._accept_loop()
        except Exception as exc:
            _logger.error(
                "Worker %d error: %s",
                self._worker_id,
                str(exc)
            )
        finally:
            self._cleanup()
        
        _logger.info(
            "Worker %d stopped (requests=%d)",
            self._worker_id,
            self._total_requests
        )
        
        return
    
    def _accept_loop(self) -> None:
        """
            Main accept loop for incoming connections.
            
            Uses select to wait for connections with a timeout to allow
            checking for shutdown requests.
        """
        listener_socket = self._listener.socket
        
        if listener_socket is None:
            errmsg = "Socket listener is not bound"
            raise WorkerError(self._worker_id, errmsg)
        
        # Set socket timeout for accept
        listener_socket.settimeout(1.0)
        
        while not self._shutdown_requested:
            try:
                # Use select to wait for connection with timeout
                readable, _, _ = select.select([listener_socket], [], [], 1.0)
                
                if len(readable) == 0:
                    # Timeout, check for shutdown and continue
                    self._cleanup_idle_connections()
                    continue
                
                # Accept connection
                try:
                    client_sock, client_addr = self._listener.accept()
                except socket.timeout:
                    continue
                except OSError as os_err:
                    if self._shutdown_requested:
                        break
                    _logger.warning(
                        "Worker %d accept error: %s",
                        self._worker_id,
                        str(os_err)
                    )
                    continue
                
                # Check if we can accept more connections
                if not self._connection_manager.can_accept_connection():
                    _logger.warning(
                        "Worker %d: max connections reached, rejecting",
                        self._worker_id
                    )
                    self._reject_connection(client_sock)
                    continue
                
                # Handle connection
                self._dispatch_connection(client_sock, client_addr)
                
            except select.error:
                if self._shutdown_requested:
                    break
                continue
        
        return
    
    def _dispatch_connection(
        self,
        client_sock: socket.socket,
        client_addr: Tuple[str, int]
    ) -> None:
        """
            Dispatch a connection for handling.
            
            Uses thread pool if configured, otherwise handles synchronously.
            
            :param client_sock: Client socket.
            :param client_addr: Client address tuple.
        """
        if self._thread_pool is not None:
            # Submit to thread pool
            self._thread_pool.submit(
                self._handle_connection_wrapper,
                client_sock,
                client_addr
            )
        else:
            # Handle synchronously
            self._handle_connection_wrapper(client_sock, client_addr)
        
        return
    
    def _handle_connection_wrapper(
        self,
        client_sock: socket.socket,
        client_addr: Tuple[str, int]
    ) -> None:
        """
            Wrapper for handle_connection with error handling.
            
            :param client_sock: Client socket.
            :param client_addr: Client address tuple.
        """
        with self._lock:
            self._active_connections += 1
        
        try:
            self.handle_connection(client_sock, client_addr)
        except Exception as exc:
            _logger.error(
                "Worker %d connection error from %s: %s",
                self._worker_id,
                client_addr,
                str(exc)
            )
        finally:
            with self._lock:
                self._active_connections -= 1
            
            # Ensure socket is closed
            try:
                client_sock.close()
            except OSError:
                pass
        
        return
    
    def _reject_connection(self, client_sock: socket.socket) -> None:
        """
            Reject a connection due to max connections limit.
            
            Sends HTTP 503 Service Unavailable and closes the socket.
            
            :param client_sock: Client socket to reject.
        """
        try:
            writer = HTTPWriter(client_sock, self._config)
            writer.write_error_response(503, "Server too busy")
        except Exception:
            pass
        finally:
            try:
                client_sock.close()
            except OSError:
                pass
        
        return
    
    def _cleanup_idle_connections(self) -> None:
        """
            Clean up idle connections.
            
            Removes connections that have exceeded the keepalive timeout.
        """
        idle_closed, timed_out_closed = self._connection_manager.cleanup()
        
        if len(idle_closed) > 0 or len(timed_out_closed) > 0:
            _logger.debug(
                "Worker %d: cleaned up %d idle, %d timed out connections",
                self._worker_id,
                len(idle_closed),
                len(timed_out_closed)
            )
        
        return
    
    def _cleanup(self) -> None:
        """
            Clean up worker resources.
            
            Shuts down thread pool and clears connection tracking.
        """
        self._running = False
        
        # Shutdown thread pool
        if self._thread_pool is not None:
            self._thread_pool.shutdown(wait=True)
            self._thread_pool = None
        
        # Clear connection tracking
        self._connection_manager.clear_all()
        
        return


    def handle_connection(
        self,
        client_sock: socket.socket,
        client_addr: Tuple[str, int]
    ) -> None:
        """
            Handle a single connection.
            
            May handle multiple requests if keep-alive is enabled. The connection
            is kept open until:
            - The client closes the connection
            - The keep-alive timeout expires
            - An error occurs
            - The server is shutting down
            
            :param client_sock: Client socket.
            :param client_addr: Client address tuple (host, port).
        """
        # Register connection
        conn_id = self._connection_manager.register_connection(
            client_addr,
            http_version="HTTP/1.1",
            is_keep_alive=True
        )
        
        if conn_id is None:
            # Max connections reached
            self._reject_connection(client_sock)
            return
        
        # Set socket timeout for reads
        client_sock.settimeout(self._config.timeout)
        
        try:
            keep_alive = True
            
            while keep_alive and not self._shutdown_requested:
                # Handle single request
                try:
                    keep_alive = self.handle_request(client_sock, client_addr)
                except socket.timeout:
                    # Connection timed out waiting for request
                    _logger.debug(
                        "Worker %d: connection from %s timed out",
                        self._worker_id,
                        client_addr
                    )
                    break
                except ConnectionResetError:
                    # Client closed connection
                    _logger.debug(
                        "Worker %d: connection from %s reset",
                        self._worker_id,
                        client_addr
                    )
                    break
                except BrokenPipeError:
                    # Client closed connection
                    _logger.debug(
                        "Worker %d: broken pipe from %s",
                        self._worker_id,
                        client_addr
                    )
                    break
                
                # Update connection activity
                self._connection_manager.update_connection_activity(conn_id)
                
                # If keep-alive, set shorter timeout for next request
                if keep_alive:
                    client_sock.settimeout(self._config.keepalive)
        
        finally:
            # Unregister connection
            self._connection_manager.unregister_connection(conn_id)
        
        return


    def handle_request(
        self,
        client_sock: socket.socket,
        client_addr: Tuple[str, int]
    ) -> bool:
        """
            Handle a single HTTP request.
            
            Parses the HTTP request, invokes the WSGI application, and writes
            the response back to the client.
            
            :param client_sock: Client socket.
            :param client_addr: Client address tuple (host, port).
            
            :returns: True if connection should be kept alive, False otherwise.
        """
        keep_alive = False
        start_time = time.time()
        method = "-"
        path = "-"
        status_code = 500
        
        try:
            # Parse HTTP request and build environ
            environ = self._parser.parse_request(
                client_sock,
                client_addr,
                self._server_addr,
                self._scheme
            )
            
            method = environ.get("REQUEST_METHOD", "-")
            path = environ.get("PATH_INFO", "-")
            http_version = environ.get("SERVER_PROTOCOL", "HTTP/1.1")
            
            # Determine keep-alive from request headers
            request_headers = self._extract_headers_from_environ(environ)
            keep_alive = self._connection_manager.should_keep_alive(
                http_version,
                request_headers
            )
            
            # Create start_response callable
            start_response = StartResponse(
                client_sock,
                self._config,
                keep_alive=keep_alive,
                http_version=http_version
            )
            
            # Invoke WSGI application
            try:
                response_iter = self._app(environ, start_response)
            except Exception as app_exc:
                # Application raised exception before start_response
                _logger.exception(
                    "Worker %d: application error for %s %s",
                    self._worker_id,
                    method,
                    path
                )
                self._send_error_response(client_sock, 500, "Internal Server Error")
                keep_alive = False
                status_code = 500
                return keep_alive
            
            # Write response body
            try:
                # Send headers if not already sent
                if not start_response.headers_sent:
                    start_response.send_headers()
                
                # Get status code for logging
                if start_response.status is not None:
                    status_code = self._parse_status_code(start_response.status)
                
                # Write response body
                writer = start_response.writer
                for chunk in response_iter:
                    if len(chunk) > 0:
                        writer.write_body(chunk)
                
                writer.flush()
                
            finally:
                # Call close() on response iterator if it has one
                if hasattr(response_iter, "close"):
                    try:
                        response_iter.close()
                    except Exception:
                        pass
            
            # Increment request count
            with self._lock:
                self._total_requests += 1
        
        except RequestParseError as parse_err:
            # Bad request
            _logger.warning(
                "Worker %d: parse error from %s: %s",
                self._worker_id,
                client_addr,
                str(parse_err)
            )
            self._send_error_response(client_sock, 400, str(parse_err.message))
            keep_alive = False
            status_code = 400
        
        except socket.timeout:
            # Request timeout
            _logger.debug(
                "Worker %d: request timeout from %s",
                self._worker_id,
                client_addr
            )
            raise
        
        except (ConnectionResetError, BrokenPipeError):
            # Client disconnected
            raise
        
        except Exception as exc:
            # Unexpected error
            _logger.exception(
                "Worker %d: unexpected error handling request from %s",
                self._worker_id,
                client_addr
            )
            try:
                self._send_error_response(client_sock, 500, "Internal Server Error")
            except Exception:
                pass
            keep_alive = False
            status_code = 500
        
        finally:
            # Log request
            if self._config.access_log:
                elapsed = time.time() - start_time
                self._log_request(client_addr, method, path, status_code, elapsed)
        
        return keep_alive
    
    def _extract_headers_from_environ(self, environ: Dict[str, Any]) -> Dict[str, str]:
        """
            Extract HTTP headers from WSGI environ.
            
            :param environ: WSGI environ dictionary.
            
            :returns: Dictionary of header names to values.
        """
        headers: Dict[str, str] = {}
        
        for key, value in environ.items():
            if key.startswith("HTTP_"):
                # Convert HTTP_HEADER_NAME to Header-Name
                header_name = key[5:].replace("_", "-").title()
                headers[header_name] = str(value)
            elif key == "CONTENT_TYPE":
                headers["Content-Type"] = str(value)
            elif key == "CONTENT_LENGTH":
                headers["Content-Length"] = str(value)
        
        return headers
    
    def _parse_status_code(self, status: str) -> int:
        """
            Parse status code from status string.
            
            :param status: Status string (e.g., "200 OK").
            
            :returns: Integer status code.
        """
        try:
            parts = status.split(None, 1)
            if len(parts) > 0:
                rtnval = int(parts[0])
            else:
                rtnval = 500
        except (ValueError, IndexError):
            rtnval = 500
        
        return rtnval
    
    def _send_error_response(
        self,
        client_sock: socket.socket,
        status_code: int,
        message: str
    ) -> None:
        """
            Send an HTTP error response.
            
            :param client_sock: Client socket.
            :param status_code: HTTP status code.
            :param message: Error message.
        """
        try:
            writer = HTTPWriter(client_sock, self._config)
            writer.write_error_response(status_code, message)
        except Exception:
            pass
        
        return
    
    def _log_request(
        self,
        client_addr: Tuple[str, int],
        method: str,
        path: str,
        status_code: int,
        elapsed: float
    ) -> None:
        """
            Log a request in common log format.
            
            :param client_addr: Client address tuple.
            :param method: HTTP method.
            :param path: Request path.
            :param status_code: Response status code.
            :param elapsed: Request processing time in seconds.
        """
        _logger.info(
            '%s - - "%s %s" %d %.3fs',
            client_addr[0],
            method,
            path,
            status_code,
            elapsed
        )
        
        return


    def shutdown(self, graceful: bool = True) -> None:
        """
            Gracefully shutdown the worker.
            
            Signals the worker to stop accepting new connections. If graceful
            is True, waits for active connections to complete before returning.
            
            :param graceful: If True, wait for active connections to complete.
        """
        _logger.info(
            "Worker %d: shutdown requested (graceful=%s)",
            self._worker_id,
            graceful
        )
        
        self._shutdown_requested = True
        
        if graceful:
            # Wait for active connections to complete
            timeout = self._config.graceful_timeout
            start_time = time.time()
            
            while self._active_connections > 0:
                elapsed = time.time() - start_time
                if elapsed >= timeout:
                    _logger.warning(
                        "Worker %d: graceful timeout exceeded, %d connections remaining",
                        self._worker_id,
                        self._active_connections
                    )
                    break
                
                time.sleep(0.1)
        
        # Cleanup resources
        self._cleanup()
        
        return
    
    def get_stats(self) -> Dict[str, Any]:
        """
            Get worker statistics.
            
            :returns: Dictionary with worker statistics.
        """
        with self._lock:
            rtnval = {
                "worker_id": self._worker_id,
                "pid": os.getpid(),
                "running": self._running,
                "active_connections": self._active_connections,
                "total_requests": self._total_requests,
                "connection_stats": self._connection_manager.get_connection_stats(),
            }
        
        return rtnval
