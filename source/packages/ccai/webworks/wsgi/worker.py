"""
    Worker process module for the WSGI layer.
    
    This module provides the Worker class for handling HTTP requests in the
    built-in WSGI server. Workers accept connections from the socket listener
    and process HTTP requests by invoking the WSGI application.
"""

import logging
import os
import random
import selectors
import socket
import ssl
import threading
import time
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable, Deque, Dict, Iterable, Optional, Tuple

from ccai.webworks.wsgi.clientconnection import ClientConnection
from ccai.webworks.wsgi.serverconfig import ServerConfig
from ccai.webworks.wsgi.socketlistener import SocketListener
from ccai.webworks.wsgi.socketreader import SocketReader
from ccai.webworks.wsgi.httpparser import HTTPParser
from ccai.webworks.wsgi.httpwriter import HTTPWriter
from ccai.webworks.wsgi.connectionmanager import ConnectionManager
from ccai.webworks.wsgi.startresponse import StartResponse
from ccai.webworks.wsgi.exceptions import (
    ConnectionClosed,
    HTTPException,
    WorkerBootError,
    WorkerError,
)


# Default logger for worker
_logger = logging.getLogger("webworks.wsgi.worker")

# Markers stored as selector data for the two sockets that are not connections
_LISTENER_KEY = "listener"
_WAKEUP_KEY = "wakeup"

# Seconds the accept loop waits before it checks for shutdown and expired connections
_POLL_INTERVAL: float = 1.0

# Bounds for reading what a client is still sending after an error response
_LINGER_SECONDS: float = 1.0
_LINGER_BYTES: int = 262144


class Worker:
    """
        Worker process that handles HTTP requests.
        
        This class implements the worker process for the built-in WSGI server.
        Each worker accepts connections from the shared socket listener and
        processes HTTP requests by invoking the WSGI application.
        
        The accept loop never reads from a client. An accepted connection is
        watched until the client has sent something, and only then is it given
        to one of the handler threads. When a response has been sent on a
        connection that is kept alive, the connection goes back to being
        watched. A client that connects and stays silent, or that idles between
        requests, therefore does not hold a handler thread and does not stop
        other clients from being served.
        
        The number of handler threads is the 'threads' setting of the server
        configuration, for every worker class.
        
        An application object may take part in the life of the worker by
        defining two methods, which the worker calls in its own process:
        'on_worker_start(worker)' before the worker accepts connections, and
        'on_worker_exit(worker)' after it has stopped serving. The ASGIBridge
        uses them to run the lifespan of an ASGI application once per worker.
        An exception from 'on_worker_start' means the worker cannot serve: it
        is raised as WorkerBootError.
        
        With 'max_requests' configured the worker stops gracefully after that
        many requests (plus a random part of 'max_requests_jitter'), and the
        worker manager starts a fresh one in its place. The last request is
        answered with 'Connection: close'.
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
        self._shutdown_graceful = True
        
        # True while the accept loop runs. A handler thread hands a
        # connection back to the accept loop only while this is set.
        self._accepting = False
        self._active_connections = 0
        self._total_requests = 0
        self._lock = threading.Lock()
        
        # Thread pool that serves the connections
        self._thread_pool: Optional[ThreadPoolExecutor] = None
        
        # Connections that wait for the client to send something. Only the
        # thread that runs the accept loop touches the selector and this map.
        self._selector: Optional[selectors.BaseSelector] = None
        self._waiting: Dict[int, ClientConnection] = {}
        
        # Connections being served, and connections the handler threads hand
        # back to the accept loop. Both are guarded by the lock.
        self._serving: Dict[int, ClientConnection] = {}
        self._returned: Deque[ClientConnection] = deque()
        
        # Socket pair used to wake the accept loop from another thread or
        # from a signal handler.
        self._wakeup_recv: Optional[socket.socket] = None
        self._wakeup_send: Optional[socket.socket] = None
        
        # Set whenever the worker is not inside run()
        self._stopped = threading.Event()
        self._stopped.set()
        self._run_thread_ident: Optional[int] = None
        
        # Server address for environ construction
        self._server_addr: Tuple[str, int] = (self._config.host, self._config.port)
        
        # Number of requests after which the worker recycles itself, None
        # for no limit. The jitter keeps workers that started together from
        # all stopping at the same moment.
        self._max_requests_limit: Optional[int] = None
        self._requests_taken = 0
        if self._config.max_requests > 0:
            jitter = 0
            if self._config.max_requests_jitter > 0:
                jitter = random.randint(0, self._config.max_requests_jitter)
            self._max_requests_limit = self._config.max_requests + jitter
        
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
    def shutdown_requested(self) -> bool:
        """
            Check if the worker has been asked to shut down.
            
            :returns: True if a shutdown was requested and is not finished.
        """
        return self._shutdown_requested
    
    @property
    def active_connections(self) -> int:
        """
            Get the number of active connections.
            
            :returns: Number of connections that are being served.
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
    
    @property
    def app(self) -> Callable[[Dict[str, Any], Callable], Iterable[bytes]]:
        """
            Get the WSGI application the worker serves.
            
            :returns: The application callable.
        """
        return self._app
    
    @property
    def max_requests_limit(self) -> Optional[int]:
        """
            Get the number of requests after which the worker recycles itself.
            
            :returns: The limit with its jitter, or None when there is none.
        """
        return self._max_requests_limit


    def run(self) -> None:
        """
            Main worker loop.
            
            Accepts connections from the socket listener and handles requests
            on a pool of 'threads' handler threads.
            
            This method blocks until a shutdown is requested, then finishes the
            requests that are in flight (for a graceful shutdown) and returns.
            
            The application's 'on_worker_start' runs first and its
            'on_worker_exit' last, when the application defines them.
            
            :raises WorkerBootError: If the application could not be started
                in this worker.
        """
        self._running = True
        self._stopped.clear()
        self._run_thread_ident = threading.get_ident()
        
        booted = False
        try:
            self._start_application()
            booted = True
        finally:
            if not booted:
                self._running = False
                self._run_thread_ident = None
                self._stopped.set()
        
        thread_count = self._config.threads
        if thread_count < 1:
            thread_count = 1
        
        self._thread_pool = ThreadPoolExecutor(
            max_workers=thread_count,
            thread_name_prefix=f"wsgi-worker-{self._worker_id}"
        )
        self._selector = selectors.DefaultSelector()
        
        wakeup_recv, wakeup_send = socket.socketpair()
        wakeup_recv.setblocking(False)
        wakeup_send.setblocking(False)
        self._wakeup_recv = wakeup_recv
        self._wakeup_send = wakeup_send
        
        _logger.info(
            "Worker %d started (pid=%d, threads=%d)",
            self._worker_id,
            os.getpid(),
            thread_count
        )
        
        try:
            self._accept_loop()
        except Exception as exc:
            _logger.exception(
                "Worker %d error: %s",
                self._worker_id,
                str(exc)
            )
        finally:
            self._drain_connections()
            self._cleanup()
            self._stop_application()
            self._run_thread_ident = None
            self._stopped.set()
        
        _logger.info(
            "Worker %d stopped (requests=%d)",
            self._worker_id,
            self._total_requests
        )
        
        return
    
    def _start_application(self) -> None:
        """
            Let the application prepare itself in this worker process.
            
            Calls 'on_worker_start(worker)' when the application defines it.
            
            :raises WorkerBootError: If the application raised.
        """
        start_hook = getattr(self._app, "on_worker_start", None)
        
        if start_hook is None:
            return
        
        try:
            start_hook(self)
        except Exception as boot_err:
            errmsg = f"the application could not be started: {type(boot_err).__name__}: {boot_err}"
            raise WorkerBootError(self._worker_id, errmsg) from boot_err
        
        return
    
    def _stop_application(self) -> None:
        """
            Let the application release what it holds in this worker process.
            
            Calls 'on_worker_exit(worker)' when the application defines it.
            The worker is ending either way, so an error of the application
            is logged and does not stop the rest of the cleanup.
        """
        exit_hook = getattr(self._app, "on_worker_exit", None)
        
        if exit_hook is None:
            return
        
        try:
            exit_hook(self)
        except Exception as exit_err:
            _logger.exception(
                "Worker %d: the application failed to stop: %s",
                self._worker_id,
                str(exit_err)
            )
        
        return
    
    def _accept_loop(self) -> None:
        """
            Main accept loop for incoming connections.
            
            Waits for the listener and for the connections that are being
            watched. The wait has a timeout so that a shutdown request and
            connections that stayed silent too long are noticed.
        """
        listener_socket = self._listener.socket
        
        if listener_socket is None:
            errmsg = "Socket listener is not bound"
            raise WorkerError(self._worker_id, errmsg)
        
        # The listener is shared by the workers. Another worker may take a
        # connection between the moment the listener is reported readable
        # and the accept, so the accept must not wait: while it waited,
        # the connections this worker is watching would not be served.
        listener_socket.setblocking(False)
        
        self._selector.register(listener_socket, selectors.EVENT_READ, _LISTENER_KEY)
        self._selector.register(self._wakeup_recv, selectors.EVENT_READ, _WAKEUP_KEY)
        
        self._accepting = True
        
        while not self._shutdown_requested:
            try:
                events = self._selector.select(timeout=_POLL_INTERVAL)
            except OSError as os_err:
                if self._shutdown_requested:
                    break
                _logger.warning(
                    "Worker %d: waiting for connections failed: %s",
                    self._worker_id,
                    str(os_err)
                )
                time.sleep(0.1)
                continue
            
            for key, _ in events:
                if key.data is _LISTENER_KEY:
                    # A worker that is stopping leaves new connections to
                    # the other workers and to its replacement
                    if not self._shutdown_requested:
                        self._accept_connection()
                elif key.data is _WAKEUP_KEY:
                    self._drain_wakeup()
                else:
                    # The client has sent something, serve the connection
                    conn = key.data
                    self._stop_waiting(conn)
                    self._submit_connection(conn)
            
            self._collect_returned_connections()
            self._close_expired_connections()
        
        with self._lock:
            self._accepting = False
        
        return
    
    def _accept_connection(self) -> None:
        """
            Accept one connection and start watching it.
            
            Nothing is read from the client here. For a TLS listener the
            handshake is left to the handler thread as well.
        """
        try:
            client_sock, client_addr = self._listener.accept()
        except (BlockingIOError, InterruptedError, socket.timeout):
            # Another worker took the connection
            return
        except OSError as os_err:
            if not self._shutdown_requested:
                _logger.warning(
                    "Worker %d accept error: %s",
                    self._worker_id,
                    str(os_err)
                )
            return
        
        conn_id = self._connection_manager.register_connection(
            client_addr,
            http_version="HTTP/1.1",
            is_keep_alive=True
        )
        
        if conn_id is None:
            _logger.warning(
                "Worker %d: max connections reached, rejecting",
                self._worker_id
            )
            self._reject_connection(client_sock)
            return
        
        handshake_pending = isinstance(client_sock, ssl.SSLSocket)
        
        conn = ClientConnection(
            client_sock,
            client_addr,
            connection_id=conn_id,
            handshake_pending=handshake_pending
        )
        conn.set_idle_deadline(self._idle_deadline_for(conn))
        
        self._start_waiting(conn)
        
        return
    
    def _idle_deadline_for(self, conn: ClientConnection) -> float:
        """
            Work out until when a silent connection is kept open.
            
            A connection that has not sent a request yet is given the request
            timeout, a connection that is kept alive between requests is given
            the keep-alive timeout.
            
            :param conn: The connection.
            
            :returns: Deadline as a 'time.monotonic' value.
        """
        if conn.request_count > 0:
            idle_seconds = self._config.keepalive
        else:
            idle_seconds = self._config.timeout
        
        if idle_seconds > 0:
            rtnval = time.monotonic() + idle_seconds
        else:
            rtnval = float("inf")
        
        return rtnval
    
    def _start_waiting(self, conn: ClientConnection) -> None:
        """
            Watch a connection until its client sends something.
            
            :param conn: The connection to watch.
        """
        try:
            self._selector.register(conn.socket, selectors.EVENT_READ, conn)
        except (KeyError, ValueError, OSError) as reg_err:
            _logger.debug(
                "Worker %d: cannot watch connection from %s: %s",
                self._worker_id,
                conn.address,
                reg_err,
            )
            self._close_connection(conn)
            return
        
        self._waiting[id(conn)] = conn
        return
    
    def _stop_waiting(self, conn: ClientConnection) -> None:
        """
            Stop watching a connection.
            
            :param conn: The connection to stop watching.
        """
        self._waiting.pop(id(conn), None)
        
        try:
            self._selector.unregister(conn.socket)
        except (KeyError, ValueError, OSError) as unreg_err:
            _logger.debug(
                "Worker %d: connection from %s was not being watched: %s",
                self._worker_id,
                conn.address,
                unreg_err,
            )
        
        return
    
    def _submit_connection(self, conn: ClientConnection) -> None:
        """
            Give a connection that has input waiting to a handler thread.
            
            :param conn: The connection to serve.
        """
        with self._lock:
            self._serving[id(conn)] = conn
            self._active_connections += 1
        
        try:
            self._thread_pool.submit(self._serve_connection, conn)
        except RuntimeError as submit_err:
            # The pool no longer takes work, the worker is stopping
            _logger.debug(
                "Worker %d: connection from %s not served: %s",
                self._worker_id,
                conn.address,
                submit_err,
            )
            with self._lock:
                self._serving.pop(id(conn), None)
                self._active_connections -= 1
            self._close_connection(conn)
        
        return
    
    def _serve_connection(self, conn: ClientConnection) -> None:
        """
            Serve a connection on a handler thread.
            
            Serves the requests whose bytes have arrived. Afterwards the
            connection is either handed back to the accept loop, to wait for
            the next request, or closed.
            
            :param conn: The connection to serve.
        """
        keep_open = False
        
        try:
            keep_open = self._serve_ready_requests(conn)
        except Exception as exc:
            _logger.exception(
                "Worker %d connection error from %s: %s",
                self._worker_id,
                conn.address,
                str(exc)
            )
        
        handed_back = False
        
        with self._lock:
            self._serving.pop(id(conn), None)
            self._active_connections -= 1
            
            if keep_open and self._accepting:
                # Appended under the same lock as the count, so the drain
                # at shutdown sees the connection in one place or the other.
                self._returned.append(conn)
                handed_back = True
        
        if handed_back:
            self._wake_accept_loop()
        else:
            self._close_connection(conn)
        
        return
    
    def _serve_ready_requests(self, conn: ClientConnection) -> bool:
        """
            Serve the requests of a connection whose bytes have arrived.
            
            Performs the TLS handshake first if it is still pending. Then
            requests are served one after the other for as long as input is
            already waiting, which covers requests a client sent together.
            
            :param conn: The connection to serve.
            
            :returns: True if the connection stays open and waits for another
                      request, False if it has to be closed.
        """
        timeout = self._timeout_or_none(self._config.timeout)
        
        if conn.handshake_pending:
            try:
                self._listener.perform_handshake(conn.socket, timeout)
            except (ssl.SSLError, OSError) as handshake_err:
                _logger.debug(
                    "Worker %d: TLS handshake with %s failed: %s",
                    self._worker_id,
                    conn.address,
                    handshake_err,
                )
                return False
            
            conn.set_handshake_done()
            
            if not conn.has_pending_input():
                # The request has not arrived yet, wait for it without
                # holding a handler thread.
                return True
        
        keep_open = True
        
        while keep_open:
            keep_open = self.handle_request(conn.socket, conn.address, reader=conn.reader)
            
            if not keep_open:
                break
            
            conn.increment_request_count()
            self._connection_manager.update_connection_activity(conn.connection_id)
            
            if self._shutdown_requested:
                keep_open = False
                break
            
            if not conn.has_pending_input():
                break
        
        return keep_open
    
    def _collect_returned_connections(self) -> None:
        """
            Start watching the connections the handler threads handed back.
        """
        while True:
            with self._lock:
                if len(self._returned) == 0:
                    break
                conn = self._returned.popleft()
            
            conn.set_idle_deadline(self._idle_deadline_for(conn))
            
            if conn.has_pending_input():
                self._submit_connection(conn)
            else:
                self._start_waiting(conn)
        
        return
    
    def _close_expired_connections(self) -> None:
        """
            Close the watched connections that stayed silent for too long.
            
            These are clients that connected without sending a request and
            keep-alive connections whose client did not send another one.
            Nothing is written to them.
        """
        now = time.monotonic()
        expired = []
        
        for conn in self._waiting.values():
            if now >= conn.idle_deadline:
                expired.append(conn)
        
        for conn in expired:
            self._stop_waiting(conn)
            self._close_connection(conn)
        
        if len(expired) > 0:
            _logger.debug(
                "Worker %d: closed %d idle connections",
                self._worker_id,
                len(expired)
            )
        
        return
    
    def _drain_wakeup(self) -> None:
        """
            Empty the wake up socket.
        """
        try:
            while True:
                data = self._wakeup_recv.recv(4096)
                if len(data) == 0:
                    break
        except (BlockingIOError, InterruptedError):
            # Nothing left to read, which is the state this method is after
            pass
        except OSError as os_err:
            _logger.debug(
                "Worker %d: reading the wake up socket failed: %s",
                self._worker_id,
                os_err,
            )
        return
    
    def _wake_accept_loop(self) -> None:
        """
            Make the accept loop return from its wait.
            
            Safe to call from any thread and from a signal handler: it does
            not log, lock or block.
        """
        wakeup_send = self._wakeup_send
        
        if wakeup_send is not None:
            try:
                wakeup_send.send(b"\x00")
            except OSError:
                # A full socket means a wake up is already pending and a
                # closed one means the loop has ended, either way there
                # is nobody left to wake.
                pass
        
        return
    
    def _timeout_or_none(self, seconds: float) -> Optional[float]:
        """
            Convert a configured timeout into a socket timeout.
            
            :param seconds: Configured timeout in seconds, 0 meaning none.
            
            :returns: The timeout, or None when no timeout is configured.
        """
        if seconds > 0:
            rtnval: Optional[float] = seconds
        else:
            rtnval = None
        return rtnval
    
    def _close_connection(self, conn: ClientConnection) -> None:
        """
            Close a connection and remove it from the connection manager.
            
            :param conn: The connection to close.
        """
        if not conn.mark_closed():
            return
        
        if conn.connection_id is not None:
            self._connection_manager.unregister_connection(conn.connection_id)
        
        try:
            conn.socket.close()
        except OSError as close_exc:
            _logger.debug(
                "Worker %d: socket close raised: %s",
                self._worker_id,
                close_exc,
            )
        
        return

    def _reject_connection(self, client_sock: socket.socket) -> None:
        """
            Reject a connection due to max connections limit.
            
            Sends HTTP 503 Service Unavailable and closes the socket. A TLS
            connection whose handshake has not been done is closed without
            a response, the handshake is not worth a handler thread here.
            
            :param client_sock: Client socket to reject.
        """
        try:
            if not isinstance(client_sock, ssl.SSLSocket):
                writer = HTTPWriter(client_sock, self._config)
                writer.write_error_response(503, "Server too busy")
        except Exception as exc:
            # The 503 write may fail if the client has already closed
            # the socket; log at debug because this is the expected
            # outcome for over-quota traffic.
            _logger.debug(
                "Worker %d: failed to send 503 reject response: %s",
                self._worker_id,
                exc,
            )
        finally:
            try:
                client_sock.close()
            except OSError as exc:
                _logger.debug(
                    "Worker %d: socket close raised during reject: %s",
                    self._worker_id,
                    exc,
                )
        
        return
    
    def _drain_connections(self) -> None:
        """
            Bring every connection to an end when the accept loop has stopped.
            
            Connections that idle between requests are closed at once. For a
            graceful shutdown, a connection that was accepted but whose first
            request has not been served yet is served, and the requests that
            are being served get the graceful timeout to finish. Whatever is
            still being served after that is cut off.
        """
        # From here on no handler thread hands a connection back, also
        # when the accept loop ended with an error and not by request.
        with self._lock:
            self._accepting = False
        
        for conn in list(self._waiting.values()):
            self._stop_waiting(conn)
            
            if self._shutdown_graceful and conn.request_count == 0:
                # Accepted, but its first request has not been served. The
                # client sent it, or is sending it, to this worker: it is
                # served (and the connection then closed, as the worker is
                # stopping) instead of being dropped.
                self._submit_connection(conn)
            else:
                # Idle between requests on a kept-alive connection
                self._close_connection(conn)
        
        if self._shutdown_graceful:
            deadline = time.monotonic() + self._config.graceful_timeout
            
            while True:
                with self._lock:
                    remaining = self._active_connections
                
                if remaining == 0:
                    break
                
                if time.monotonic() >= deadline:
                    _logger.warning(
                        "Worker %d: graceful timeout exceeded, %d connections remaining",
                        self._worker_id,
                        remaining
                    )
                    break
                
                time.sleep(0.05)
        
        with self._lock:
            still_serving = list(self._serving.values())
            handed_back = list(self._returned)
            self._returned.clear()
        
        for conn in still_serving:
            # Shutting the socket down makes the handler thread fail out of
            # whatever read or write it is waiting in. The operating system
            # socket is shut down directly: SSLSocket.shutdown would also
            # drop the SSL object the handler thread is still using, and the
            # thread would fail with an AttributeError (for example inside
            # the TLS handshake) instead of the OSError of a closed connection.
            try:
                socket.socket.shutdown(conn.socket, socket.SHUT_RDWR)
            except OSError as shutdown_exc:
                _logger.debug(
                    "Worker %d: socket shutdown raised: %s",
                    self._worker_id,
                    shutdown_exc,
                )
        
        for conn in handed_back:
            self._close_connection(conn)
        
        return
    
    def _cleanup(self) -> None:
        """
            Clean up worker resources.
            
            Shuts down thread pool, releases the selector and the wake up
            sockets and clears connection tracking.
        """
        self._running = False
        self._accepting = False
        
        # Shutdown thread pool. The connections have been drained: what is
        # still queued or running finds its socket shut down and ends by
        # closing it. A thread that is busy inside the application is not
        # waited for.
        if self._thread_pool is not None:
            self._thread_pool.shutdown(wait=False)
            self._thread_pool = None
        
        if self._selector is not None:
            self._selector.close()
            self._selector = None
        
        wakeup_send = self._wakeup_send
        wakeup_recv = self._wakeup_recv
        self._wakeup_send = None
        self._wakeup_recv = None
        
        for wakeup_sock in (wakeup_send, wakeup_recv):
            if wakeup_sock is not None:
                wakeup_sock.close()
        
        self._waiting.clear()
        
        # Clear connection tracking
        self._connection_manager.clear_all()
        
        # The request has been carried out, the worker can be run again
        self._shutdown_requested = False
        self._shutdown_graceful = True
        
        return


    def handle_connection(
        self,
        client_sock: socket.socket,
        client_addr: Tuple[str, int]
    ) -> None:
        """
            Handle a single connection.
            
            Serves the connection on the calling thread until it ends, which
            may be several requests if keep-alive is enabled. The connection
            is kept open until:
            - The client closes the connection
            - The keep-alive timeout expires
            - An error occurs
            - The server is shutting down
            
            The worker itself does not use this method, it serves connections
            through its accept loop without tying a thread to an idle client.
            The socket is not closed here, it belongs to the caller.
            
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
        
        handshake_pending = isinstance(client_sock, ssl.SSLSocket)
        
        conn = ClientConnection(
            client_sock,
            client_addr,
            connection_id=conn_id,
            handshake_pending=handshake_pending
        )
        
        try:
            keep_open = True
            
            while keep_open and not self._shutdown_requested:
                if not conn.has_pending_input() and not conn.handshake_pending:
                    if conn.request_count > 0:
                        idle_seconds = self._config.keepalive
                    else:
                        idle_seconds = self._config.timeout
                    
                    if not self._wait_readable(client_sock, idle_seconds):
                        _logger.debug(
                            "Worker %d: connection from %s timed out",
                            self._worker_id,
                            client_addr
                        )
                        break
                
                keep_open = self._serve_ready_requests(conn)
        
        finally:
            # Unregister connection
            self._connection_manager.unregister_connection(conn_id)
        
        return
    
    def _wait_readable(self, client_sock: socket.socket, seconds: float) -> bool:
        """
            Wait until a socket has input.
            
            :param client_sock: Socket to wait for.
            :param seconds: Seconds to wait, 0 meaning without limit.
            
            :returns: True if the socket has input, False if the wait timed out.
        """
        wait_time = self._timeout_or_none(seconds)
        
        with selectors.DefaultSelector() as selector:
            selector.register(client_sock, selectors.EVENT_READ)
            events = selector.select(timeout=wait_time)
        
        rtnval = len(events) > 0
        return rtnval


    def handle_request(
        self,
        client_sock: socket.socket,
        client_addr: Tuple[str, int],
        reader: Optional[SocketReader] = None
    ) -> bool:
        """
            Handle a single HTTP request.
            
            Parses the HTTP request, invokes the WSGI application, and writes
            the response back to the client.
            
            :param client_sock: Client socket.
            :param client_addr: Client address tuple (host, port).
            :param reader: The reader of the connection. Pass it when several
                           requests are served on one connection, so input read
                           ahead is kept. If None, the request is read from the
                           socket without reading ahead.
            
            :returns: True if connection should be kept alive, False otherwise.
        """
        keep_alive = False
        start_time = time.time()
        method = "-"
        path = "-"
        status_code = 500
        
        if reader is None:
            reader = SocketReader(client_sock, read_ahead=False)
        
        timeout = self._timeout_or_none(self._config.timeout)
        
        # Each read is limited by the timeout. The request line and the
        # headers together are limited by a deadline as well, so a client
        # that sends a byte at a time cannot hold the thread indefinitely.
        reader.set_timeout(timeout)
        reader.set_deadline(timeout)
        
        try:
            # Parse HTTP request and build environ
            environ = self._parser.parse_request(
                reader,
                client_addr,
                self._server_addr,
                self._scheme
            )
        
        except ConnectionClosed:
            # The client closed a connection it was not using. This is how
            # a keep-alive connection normally ends, nothing is sent back.
            _logger.debug(
                "Worker %d: connection from %s closed by the client",
                self._worker_id,
                client_addr
            )
            return keep_alive
        
        except socket.timeout:
            # No request arrived in time, the connection is closed quietly
            _logger.debug(
                "Worker %d: connection from %s timed out",
                self._worker_id,
                client_addr
            )
            return keep_alive
        
        except HTTPException as http_err:
            # The request was refused: malformed, too large, cut short or
            # stalled. It is answered with its status and never reaches
            # the application.
            status_code = http_err.status_code
            _logger.warning(
                "Worker %d: request from %s refused with %d: %s",
                self._worker_id,
                client_addr,
                status_code,
                str(http_err)
            )
            self._send_error_response(client_sock, status_code, str(http_err.message))
            self._linger(client_sock)
            
            if self._config.access_log:
                elapsed = time.time() - start_time
                self._log_request(client_addr, method, path, status_code, elapsed)
            
            return keep_alive
        
        except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError) as conn_err:
            # Windows often reports a connection the client dropped as
            # aborted (WSAECONNABORTED) rather than reset.
            _logger.debug(
                "Worker %d: connection from %s lost: %s",
                self._worker_id,
                client_addr,
                conn_err
            )
            return keep_alive
        
        finally:
            reader.set_deadline(None)
        
        method = environ.get("REQUEST_METHOD", "-")
        # The raw request target is logged. The decoded path may hold line
        # breaks a client put there to forge log lines.
        path = environ.get("REQUEST_URI", environ.get("PATH_INFO", "-"))
        http_version = environ.get("SERVER_PROTOCOL", "HTTP/1.1")
        
        # Determine keep-alive from request headers
        request_headers = self._extract_headers_from_environ(environ)
        keep_alive = self._connection_manager.should_keep_alive(
            http_version,
            request_headers
        )
        
        # The request that reaches max_requests is the last one this worker
        # serves, the client is told so instead of finding the connection
        # closed under its next request. The worker stops accepting before
        # the response goes out, so a client that connects again as soon as
        # it has the answer reaches the worker that replaces this one.
        if self._max_requests_limit is not None:
            # Counted when the request is taken on, not when it is done: a
            # client may send its next request before the thread that served
            # the previous one has finished its bookkeeping.
            with self._lock:
                self._requests_taken += 1
                requests_taken = self._requests_taken
            if requests_taken >= self._max_requests_limit:
                keep_alive = False
                self._recycle_if_limit_reached(requests_taken)
        
        # Create start_response callable
        start_response = StartResponse(
            client_sock,
            self._config,
            keep_alive=keep_alive,
            http_version=http_version,
            request_method=method
        )
        
        response_iter: Optional[Iterable[bytes]] = None
        
        try:
            # Writes are limited by the timeout as well
            client_sock.settimeout(timeout)
            
            # Invoke WSGI application
            response_iter = self._app(environ, start_response)
            
            self._write_response(response_iter, start_response)
            
            keep_alive = start_response.keep_alive
            status_code = self._parse_status_code(start_response.status)
            
            # Increment request count
            with self._lock:
                self._total_requests += 1
        
        except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError, socket.timeout) as conn_err:
            # The client went away or stopped reading. The application is
            # not asked for more and the connection is closed. Windows often
            # reports a dropped connection as aborted (WSAECONNABORTED).
            _logger.debug(
                "Worker %d: client %s lost while responding: %s",
                self._worker_id,
                client_addr,
                conn_err
            )
            keep_alive = False
            if start_response.status is not None:
                status_code = self._parse_status_code(start_response.status)
        
        except Exception:
            _logger.exception(
                "Worker %d: application error for %s %s",
                self._worker_id,
                method,
                path
            )
            keep_alive = False
            
            if start_response.headers_sent:
                # Part of a response is on the wire. A second response
                # written now would land inside the body of the first, so
                # the connection is closed and the client sees the response
                # end early.
                status_code = self._parse_status_code(start_response.status)
            else:
                status_code = 500
                self._send_error_response(client_sock, 500, "Internal Server Error")
        
        finally:
            # Call close() on response iterator if it has one
            if response_iter is not None and hasattr(response_iter, "close"):
                try:
                    response_iter.close()
                except Exception as close_exc:
                    # Iterator close errors don't change the
                    # response we sent, but a sustained pattern
                    # suggests a leaking resource — log at debug
                    # so it's at least visible in the journal.
                    _logger.debug(
                        "Worker %d: response iterator close raised: %s",
                        self._worker_id,
                        close_exc,
                    )
            
            # Log request
            if self._config.access_log:
                elapsed = time.time() - start_time
                self._log_request(client_addr, method, path, status_code, elapsed)
        
        return keep_alive
    
    def _write_response(
        self,
        response_iter: Iterable[bytes],
        start_response: StartResponse
    ) -> None:
        """
            Write the body the application returned.
            
            The headers are sent with the first body bytes and not before, as
            PEP 3333 requires. An application written as a generator has not
            called start_response when it returns its iterable, it does so
            when the first item is asked for. Waiting also lets an application
            replace its headers with an error response, by calling
            start_response again with exc_info, for as long as nothing was sent.
            
            :param response_iter: The iterable the application returned.
            :param start_response: The start_response object of the request.
        """
        # A body that is a list of one item has a known size, which lets
        # the response carry a Content-Length the application did not set.
        known_size: Optional[int] = None
        if isinstance(response_iter, (list, tuple)) and len(response_iter) == 1:
            only_item = response_iter[0]
            known_size = len(only_item)
        
        writer = start_response.writer
        
        for chunk in response_iter:
            if len(chunk) == 0:
                continue
            
            if not start_response.headers_sent:
                if known_size is not None:
                    start_response.set_known_body_size(known_size)
                start_response.send_headers()
            
            writer.write_body(chunk)
            
            # Each item is sent before the next one is asked for, an
            # application that streams relies on that.
            writer.flush()
        
        # Sends the headers of a response without a body, ends the body
        start_response.finish()
        
        if writer.body_truncated:
            _logger.warning(
                "Worker %d: the application wrote more than the Content-Length "
                "it declared, the excess was dropped",
                self._worker_id
            )
        
        if not writer.body_complete:
            _logger.warning(
                "Worker %d: the application wrote %d of the %d bytes it declared, "
                "closing the connection",
                self._worker_id,
                writer.body_bytes_written,
                writer.body_limit
            )
        
        return
    
    def _recycle_if_limit_reached(self, served: int) -> None:
        """
            Stop the worker gracefully once it reaches max_requests requests.
            
            Called when the last request is taken on, before its response is
            written, so the worker accepts no further connection: a client
            that connects again once it has the answer reaches the worker
            that replaces this one. The worker manager replaces a worker that
            stopped, so this recycles the worker process.
            
            :param served: The number of requests taken on, the one in hand included.
        """
        limit = self._max_requests_limit
        
        if limit is None or served < limit or self._shutdown_requested:
            return
        
        _logger.info(
            "Worker %d reached its request limit (request %d of max_requests %d), stopping so it is replaced",
            self._worker_id,
            served,
            limit
        )
        self.request_shutdown(graceful=True)
        
        return
    
    def _linger(self, client_sock: socket.socket) -> None:
        """
            Let a client finish sending before a refused connection is closed.
            
            Closing a socket that still has unread input makes the operating
            system reset the connection, and the reset can destroy the error
            response before the client has read it. The write side is shut
            down and what the client is still sending is read and dropped,
            within small limits of time and size.
            
            :param client_sock: Client socket that is about to be closed.
        """
        deadline = time.monotonic() + _LINGER_SECONDS
        discarded = 0
        
        try:
            client_sock.shutdown(socket.SHUT_WR)
            
            while discarded < _LINGER_BYTES:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    break
                
                client_sock.settimeout(remaining)
                data = client_sock.recv(65536)
                if len(data) == 0:
                    break
                
                discarded += len(data)
        except OSError as linger_exc:
            # The client is gone or silent, there is nothing left to wait for
            _logger.debug(
                "Worker %d: lingering close ended: %s",
                self._worker_id,
                linger_exc,
            )
        
        return
    
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
        except Exception as exc:
            _logger.debug(
                "Worker %d: failed to send %d error response: %s",
                self._worker_id,
                status_code,
                exc,
            )

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


    def request_shutdown(self, graceful: bool = True) -> None:
        """
            Ask the worker to shut down, without waiting for it.
            
            Only records the request and wakes the accept loop, so it is safe
            to call from a signal handler. The thread inside run() stops
            accepting, finishes the requests in flight when the shutdown is
            graceful, and then returns from run().
            
            :param graceful: If True, requests in flight are allowed to finish.
        """
        self._shutdown_graceful = graceful
        self._shutdown_requested = True
        self._wake_accept_loop()
        return
    
    def shutdown(self, graceful: bool = True) -> None:
        """
            Gracefully shutdown the worker.
            
            Signals the worker to stop accepting new connections and waits
            until run() has returned. If graceful is True, the requests in
            flight are allowed to finish first.
            
            The wait is skipped when this is called on the thread that is
            inside run(), which is the case in a signal handler: waiting
            there would stop the very thread that has to finish the requests.
            Use request_shutdown() from a signal handler.
            
            :param graceful: If True, wait for active connections to complete.
        """
        _logger.info(
            "Worker %d: shutdown requested (graceful=%s)",
            self._worker_id,
            graceful
        )
        
        if not self._running:
            # Nothing is running, release whatever is left
            self._cleanup()
            return
        
        self.request_shutdown(graceful=graceful)
        
        if threading.get_ident() != self._run_thread_ident:
            wait_time = _POLL_INTERVAL + 5.0
            if graceful:
                wait_time += self._config.graceful_timeout
            
            stopped = self._stopped.wait(timeout=wait_time)
            if not stopped:
                _logger.warning(
                    "Worker %d: did not stop within %.1f seconds",
                    self._worker_id,
                    wait_time
                )
        
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
                "max_requests_limit": self._max_requests_limit,
                "connection_stats": self._connection_manager.get_connection_stats(),
            }
        
        return rtnval
