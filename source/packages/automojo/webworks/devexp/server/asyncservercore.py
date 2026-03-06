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
        """
        self._app = app
        self._host = host
        self._port = port
        self._shutdown_timeout = shutdown_timeout
        self._keepalive_timeout = keepalive_timeout
        self._debug = debug
        self._request_logger = request_logger

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
        from automojo.webworks.devexp.server.httpprotocolhandler import HTTPProtocolHandler

        handler = HTTPProtocolHandler(
            app=self._app,
            server_host=self._host,
            server_port=self._port,
            debug=self._debug,
            on_close=lambda h=None: self.unregister_connection(handler),
            request_logger=self._request_logger,
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

            Calls ``server.close()`` to stop accepting, then waits up to
            ``shutdown_timeout`` seconds for active connections to drain.
            Any connections still open after the timeout are forcibly closed
            by closing their transports.
        """
        if self._server is None:
            return

        # Stop accepting new connections.
        self._server.close()
        await self._server.wait_closed()

        logger.info("Server stopped accepting new connections.")

        # Wait for active connections to drain.
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

            # Forcibly close remaining connections.
            if len(self._connections) > 0:
                logger.warning(
                    "Forcibly closing %d remaining connection(s) after timeout.",
                    len(self._connections),
                )

                remaining = set(self._connections)
                for handler in remaining:
                    transport = getattr(handler, "_transport", None)
                    if transport is not None and not transport.is_closing():
                        transport.close()

                # Give the event loop a moment to process the close callbacks.
                await asyncio.sleep(0.05)

        self._server = None

        logger.info("AsyncServerCore stopped.")

        return
