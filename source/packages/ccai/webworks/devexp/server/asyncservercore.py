"""
    Asyncio-based TCP server core for the development server.

    This module provides the :class:`AsyncServerCore` class, which binds
    a TCP socket using ``asyncio.Server`` and accepts incoming connections.
    Each connection is delegated to an :class:`HTTPProtocolHandler` instance
    that parses HTTP/1.1 requests and invokes the ASGI application.

    The server core tracks active connections and supports graceful shutdown
    with a configurable timeout for draining in-flight requests.
"""

import asyncio
import logging

from typing import Any, Optional, Set


logger = logging.getLogger(__name__)


WAIT_CLOSED_TIMEOUT_SECONDS: float = 2.0
"""Seconds to wait for the listening server to report closed once every connection was closed."""


# =============================================================================
# AsyncServerCore
# =============================================================================

class AsyncServerCore:
    """
        Asyncio-based TCP server that binds a socket and manages connections.

        The server creates an ``asyncio.Server`` via ``loop.create_server()``
        using a protocol factory that produces :class:`HTTPProtocolHandler`
        instances. Active connections are tracked so that graceful shutdown
        can wait for in-flight requests to complete before forcibly closing
        remaining transports.

        :param app: The ASGI application callable.
        :param host: The host address to bind to.
        :param port: The port number to bind to.
        :param shutdown_timeout: Maximum seconds to wait for active connections
            to drain during shutdown. Defaults to 5.
        :param keepalive_timeout: Seconds to keep idle connections open.
            Defaults to 30.
        :param debug: Whether debug mode is enabled for error reporting.
            Defaults to False.
        :param request_logger: Optional request logger instance to pass
            through to protocol handlers.
        :param max_body_bytes: The largest request body accepted, in bytes.
            ``None`` uses the protocol handler's default.
    """

    def __init__(
        self,
        app: Any,
        host: str,
        port: int,
        shutdown_timeout: float = 5,
        keepalive_timeout: float = 30,
        debug: bool = False,
        request_logger: Any = None,
        max_body_bytes: Optional[int] = None,
    ) -> None:
        """
            Construct an AsyncServerCore.

            :param app: The ASGI application callable.
            :param host: The host address to bind to.
            :param port: The port number to bind to.
            :param shutdown_timeout: Maximum seconds to wait for active
                connections to drain during shutdown.
            :param keepalive_timeout: Seconds to keep idle connections open.
            :param debug: Whether debug mode is enabled for error reporting.
            :param request_logger: Optional request logger instance.
            :param max_body_bytes: The largest request body accepted, in
                bytes. ``None`` uses the protocol handler's default.
        """
        self._app = app
        self._host = host
        self._port = port
        self._shutdown_timeout = shutdown_timeout
        self._keepalive_timeout = keepalive_timeout
        self._debug = debug
        self._request_logger = request_logger
        self._max_body_bytes = max_body_bytes

        self._server: Optional[asyncio.AbstractServer] = None
        self._connections: Set[Any] = set()

        return

    # -------------------------------------------------------------------------
    # Properties
    # -------------------------------------------------------------------------

    @property
    def server(self) -> Optional[asyncio.AbstractServer]:
        """
            The underlying ``asyncio.Server`` instance, or ``None`` if the
            server has not been started.

            :returns: The asyncio server instance or None.
        """
        return self._server

    @property
    def is_running(self) -> bool:
        """
            Whether the server is currently accepting connections.

            :returns: True if the server is serving, False otherwise.
        """
        if self._server is not None:
            return self._server.is_serving()

        return False

    @property
    def active_connections(self) -> int:
        """
            The count of active HTTPProtocolHandler instances.

            :returns: The number of currently tracked connections.
        """
        return len(self._connections)

    # -------------------------------------------------------------------------
    # Connection Tracking
    # -------------------------------------------------------------------------

    def register_connection(self, handler: Any) -> None:
        """
            Track an active connection.

            Called by the protocol factory after creating a new
            :class:`HTTPProtocolHandler` instance.

            :param handler: The protocol handler to track.
        """
        self._connections.add(handler)

        logger.debug(
            "Connection registered. Active connections: %d",
            len(self._connections),
        )

        return

    def unregister_connection(self, handler: Any) -> None:
        """
            Remove a tracked connection.

            Called via the ``on_close`` callback when a connection is lost.

            :param handler: The protocol handler to remove.
        """
        self._connections.discard(handler)

        logger.debug(
            "Connection unregistered. Active connections: %d",
            len(self._connections),
        )

        return

    # -------------------------------------------------------------------------
    # Protocol Factory
    # -------------------------------------------------------------------------

    def _create_protocol(self) -> Any:
        """
            Factory method returning a new HTTPProtocolHandler instance.

            Creates a handler with the app, host, port, debug flag, and
            an ``on_close`` callback that calls :meth:`unregister_connection`.
            After creating the handler, registers it as an active connection.

            :returns: A new HTTPProtocolHandler instance.
        """
        from ccai.webworks.devexp.server.httpprotocolhandler import HTTPProtocolHandler

        handler = HTTPProtocolHandler(
            app=self._app,
            server_host=self._host,
            server_port=self._port,
            debug=self._debug,
            on_close=lambda h=None: self.unregister_connection(handler),
            request_logger=self._request_logger,
            max_body_bytes=self._max_body_bytes,
            keepalive_timeout=self._keepalive_timeout,
        )

        self.register_connection(handler)

        return handler

    # -------------------------------------------------------------------------
    # Lifecycle Methods
    # -------------------------------------------------------------------------

    async def start(self) -> None:
        """
            Create an ``asyncio.Server``, bind the socket, and start
            accepting connections.

            Uses ``loop.create_server()`` with the protocol factory to
            bind a TCP socket to the configured host and port.

            :raises OSError: If the socket cannot be bound.
        """
        loop = asyncio.get_running_loop()

        self._server = await loop.create_server(
            protocol_factory=self._create_protocol,
            host=self._host,
            port=self._port,
            reuse_address=True,
        )

        logger.info(
            "AsyncServerCore started on %s:%d",
            self._host,
            self._port,
        )

        return

    async def stop(self) -> None:
        """
            Stop accepting new connections and gracefully shut down.

            Calls ``server.close()`` to stop accepting, closes idle
            keep-alive connections at once, then waits up to
            ``shutdown_timeout`` seconds for requests that are in flight to
            finish. Any connections still open after the timeout are
            forcibly closed by closing their transports.

            ``server.wait_closed()`` is awaited last. Since Python 3.12.1 it
            returns only once every accepted connection has closed, so
            awaiting it before the connections are drained would make
            shutdown wait on an idle browser tab or a long-lived stream.
        """
        if self._server is None:
            return

        server = self._server

        # Stop accepting new connections.
        server.close()

        logger.info("Server stopped accepting new connections.")

        # An idle keep-alive connection has no work to lose.
        self._close_connections(idle_only=True)

        # Wait for requests that are in flight to finish. A connection that
        # becomes idle while we wait is closed on the next pass.
        if len(self._connections) > 0:
            logger.info(
                "Waiting up to %s seconds for %d active connection(s) to drain.",
                self._shutdown_timeout,
                len(self._connections),
            )

            elapsed = 0.0
            interval = 0.1

            while len(self._connections) > 0 and elapsed < self._shutdown_timeout:
                await asyncio.sleep(interval)
                elapsed += interval
                self._close_connections(idle_only=True)

            # Forcibly close remaining connections.
            if len(self._connections) > 0:
                logger.warning(
                    "Forcibly closing %d remaining connection(s) after timeout.",
                    len(self._connections),
                )

                self._close_connections(idle_only=False)

        # Every transport has been asked to close; give the event loop the
        # chance to run the close callbacks, but never wait on a peer.
        try:
            await asyncio.wait_for(server.wait_closed(), timeout=WAIT_CLOSED_TIMEOUT_SECONDS)
        except asyncio.TimeoutError:
            logger.warning(
                "The listening server did not finish closing within %s seconds.",
                WAIT_CLOSED_TIMEOUT_SECONDS,
            )

        self._server = None

        logger.info("AsyncServerCore stopped.")

        return

    def _close_connections(self, idle_only: bool) -> None:
        """
            Close tracked connections.

            :param idle_only: When ``True``, close only connections that
                are between requests; when ``False``, close all of them.
        """
        for handler in set(self._connections):
            if idle_only and not getattr(handler, "is_idle", False):
                continue

            handler.close()

        return
