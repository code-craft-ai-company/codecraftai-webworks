"""
    Development HTTP server with debug features.

    This module provides the :class:`DevelopmentServer` class that wraps
    an ASGI application with development-friendly features such as debug
    mode, request logging, and auto-reload support.

    The server holds configuration for host, port, debug mode, reload
    behaviour, and file watch patterns. It provides :meth:`start` and
    :meth:`stop` methods for lifecycle management.

    When the application is a callable ASGI application, :meth:`start`
    creates an :class:`AsyncServerCore` and :class:`LifespanManager`,
    then runs the asyncio event loop to block the calling thread until
    the server is stopped via signal or programmatic call.
"""

import asyncio
import logging
import signal
import socket

from typing import Any, Callable, List, Optional, TYPE_CHECKING

from ccai.webworks.devexp.cli.exitcodes import EXIT_ERROR
from ccai.webworks.devexp.server.asyncservercore import AsyncServerCore
from ccai.webworks.devexp.server.lifespanmanager import LifespanManager

if TYPE_CHECKING:
    from ccai.webworks.asgi.application import ASGIApplication


logger = logging.getLogger(__name__)


# =============================================================================
# Default Patterns
# =============================================================================

DEFAULT_WATCH_PATTERNS: List[str] = ["**/*.py"]
"""Default file patterns to watch for changes during auto-reload."""

DEFAULT_EXCLUDE_PATTERNS: List[str] = [".git", "__pycache__", ".venv", "*.pyc"]
"""Default patterns to exclude from file watching."""


# =============================================================================
# Port Availability Check
# =============================================================================

class PortInUseError(Exception):
    """
        Exception raised when the configured port is already in use.

        The exception carries the host and port that could not be bound
        so that callers can produce a helpful error message.
    """

    def __init__(self, host: str, port: int):
        """
            Construct a PortInUseError.

            :param host: The host address that was attempted.
            :param port: The port number that was already in use.
        """
        self._host = host
        self._port = port
        message = "Port {} is already in use on host '{}'.".format(port, host)
        super().__init__(message)
        return

    @property
    def host(self) -> str:
        """
            The host address that was attempted.

            :returns: The host string.
        """
        return self._host

    @property
    def port(self) -> int:
        """
            The port number that was already in use.

            :returns: The port number.
        """
        return self._port


def check_port_available(host: str, port: int) -> bool:
    """
        Check whether a given host and port combination is available for binding.

        Attempts to bind a TCP socket to the specified address. If the bind
        succeeds the port is available and the socket is immediately closed.

        :param host: The host address to check.
        :param port: The port number to check.

        :returns: ``True`` if the port is available, ``False`` otherwise.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        sock.bind((host, port))
        available = True
    except OSError:
        available = False
    finally:
        sock.close()

    return available


def format_port_in_use_message(host: str, port: int) -> str:
    """
        Format a user-friendly error message when a port is already in use.

        The message includes the attempted address and suggests three
        alternative ports that the user can try.

        :param host: The host address that was attempted.
        :param port: The port number that was already in use.

        :returns: A formatted error message string.
    """
    alt_ports = [port + 1, port + 10, port + 100]

    lines = [
        "Error: Port {} is already in use on '{}'.".format(port, host),
        "",
        "Suggestions:",
        "  - Stop the process using port {}".format(port),
        "  - Use a different port with --port, for example:",
    ]

    for alt in alt_ports:
        lines.append("      webworks serve --port {}".format(alt))

    message = "\n".join(lines)

    return message


# =============================================================================
# DevelopmentServer
# =============================================================================

class DevelopmentServer:
    """
        Development HTTP server with debug features.

        The server holds configuration for binding address, debug mode,
        auto-reload, and file watch patterns. The :meth:`start` method
        checks port availability before attempting to serve and raises
        :class:`PortInUseError` when the port is already bound.
    """

    def __init__(
        self,
        app: Any,
        host: str = "127.0.0.1",
        port: int = 8000,
        debug: bool = True,
        reload: bool = False,
        watch_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
    ):
        """
            Construct a DevelopmentServer.

            :param app: The ASGI application instance to serve.
            :param host: The host address to bind to.
            :param port: The port number to bind to.
            :param debug: Whether to enable debug mode.
            :param reload: Whether to enable auto-reload on file changes.
            :param watch_patterns: File patterns to watch for changes.
                Defaults to ``["**/*.py"]``.
            :param exclude_patterns: Patterns to exclude from watching.
                Defaults to ``[".git", "__pycache__", ".venv", "*.pyc"]``.
        """
        self._app = app
        self._host = host
        self._port = port
        self._debug = debug
        self._reload = reload
        self._running = False

        if watch_patterns is not None:
            self._watch_patterns = list(watch_patterns)
        else:
            self._watch_patterns = list(DEFAULT_WATCH_PATTERNS)

        if exclude_patterns is not None:
            self._exclude_patterns = list(exclude_patterns)
        else:
            self._exclude_patterns = list(DEFAULT_EXCLUDE_PATTERNS)

        self._request_logger: Optional[Any] = None
        self._watcher: Optional[Any] = None
        self._restart_count: int = 0
        self._last_reload_error: Optional[Exception] = None

        self._server_core: Optional[AsyncServerCore] = None
        self._lifespan_manager: Optional[LifespanManager] = None
        self._shutdown_event: Optional[asyncio.Event] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None

        return

    # -------------------------------------------------------------------------
    # Properties
    # -------------------------------------------------------------------------

    @property
    def app(self) -> Any:
        """
            The ASGI application being served.

            :returns: The application instance.
        """
        return self._app

    @property
    def host(self) -> str:
        """
            The host address the server binds to.

            :returns: The host string.
        """
        return self._host

    @property
    def port(self) -> int:
        """
            The port number the server binds to.

            :returns: The port number.
        """
        return self._port

    @property
    def debug(self) -> bool:
        """
            Whether debug mode is enabled.

            :returns: ``True`` if debug mode is on.
        """
        return self._debug

    @property
    def reload(self) -> bool:
        """
            Whether auto-reload is enabled.

            :returns: ``True`` if auto-reload is on.
        """
        return self._reload

    @property
    def watch_patterns(self) -> List[str]:
        """
            The file patterns being watched for changes.

            :returns: A list of glob pattern strings.
        """
        return list(self._watch_patterns)

    @property
    def exclude_patterns(self) -> List[str]:
        """
            The patterns excluded from file watching.

            :returns: A list of exclusion pattern strings.
        """
        return list(self._exclude_patterns)

    @property
    def running(self) -> bool:
        """
            Whether the server is currently running.

            :returns: ``True`` if the server is running.
        """
        return self._running

    @property
    def request_logger(self) -> Optional[Any]:
        """
            The request logging middleware instance, if configured.

            :returns: The request logger or ``None``.
        """
        return self._request_logger

    @property
    def watcher(self) -> Optional[Any]:
        """
            The file watcher instance, if auto-reload is enabled.

            :returns: The file watcher or ``None``.
        """
        return self._watcher

    @property
    def restart_count(self) -> int:
        """
            The number of times the server has been restarted by
            the file watcher.

            :returns: The restart count.
        """
        return self._restart_count

    @property
    def last_reload_error(self) -> Optional[Exception]:
        """
            The last error encountered during a reload attempt.

            When a syntax error or import error occurs during reload,
            it is stored here so callers can inspect it. The server
            continues watching for fixes.

            :returns: The exception or ``None``.
        """
        return self._last_reload_error

    # -------------------------------------------------------------------------
    # Lifecycle Methods
    # -------------------------------------------------------------------------

    def serve_forever(self, host: Optional[str] = None, port: Optional[int] = None) -> None:
        """
            Start the development server and block until shutdown.

            Checks that the configured port is available before starting.
            If the port is already in use, raises :class:`PortInUseError`.

            When debug mode is enabled, sets up debug middleware. Request
            logging is always configured. When reload is enabled, starts
            the file watcher to monitor for source changes.

            If the application is a callable ASGI application, creates an
            :class:`AsyncServerCore` and :class:`LifespanManager`, then
            runs the asyncio event loop to block the calling thread until
            the server is stopped.

            :param host: The interface IP to bind to.  Overrides the value
                passed to the constructor.  Defaults to ``None`` which
                uses the constructor value (``"127.0.0.1"``).
            :param port: The port number to bind to.  Overrides the value
                passed to the constructor.  Defaults to ``None`` which
                uses the constructor value (``8000``).

            :raises PortInUseError: If the configured port is already in use.
        """
        if host is not None:
            self._host = host

        if port is not None:
            self._port = port

        port_available = check_port_available(self._host, self._port)

        if not port_available:
            raise PortInUseError(self._host, self._port)

        if self._debug:
            self._setup_debug_middleware()

        self._setup_request_logging()

        if self._reload is True:
            self._setup_file_watcher()

        self._running = True

        scheme = "http"
        display_host = "localhost" if self._host in ("0.0.0.0", "127.0.0.1", "::1", "::") else self._host

        logger.info(
            "Development server started on %s:%d (debug=%s, reload=%s)",
            self._host, self._port, self._debug, self._reload,
        )
        logger.info("Serving on %s://%s:%d", scheme, display_host, self._port)

        # If the app is a callable ASGI application, run the async
        # server core. Otherwise, just set the running flag (backward
        # compatibility for tests using non-callable fake apps).
        if callable(self._app):
            try:
                asyncio.run(self._run_async())
            finally:
                self._running = False

        return

    def stop(self) -> None:
        """
            Stop the server and clean up resources.

            If a file watcher is running, it is stopped first. If the
            async server core is running, signals the shutdown event
            to trigger graceful shutdown of the event loop.
        """
        if self._watcher is not None:
            self._watcher.stop()
            self._watcher = None

        # Signal the async event loop to shut down.
        # Use call_soon_threadsafe when the event loop is running in
        # a different thread (e.g. when stop() is called from the
        # main thread while the event loop runs in a background thread).
        if self._shutdown_event is not None and self._loop is not None:
            try:
                self._loop.call_soon_threadsafe(self._shutdown_event.set)
            except RuntimeError:
                # The loop may already be closed.
                self._shutdown_event.set()

        self._running = False

        logger.info("Development server stopped.")

        return

    # -------------------------------------------------------------------------
    # Async Event Loop
    # -------------------------------------------------------------------------

    async def _run_async(self) -> None:
        """
            Run the async server core within an asyncio event loop.

            Creates a shutdown event, starts the lifespan manager, creates
            and starts the async server core, installs signal handlers,
            and awaits the shutdown event. On shutdown, runs lifespan
            shutdown and stops the server core.
        """
        self._shutdown_event = asyncio.Event()

        # Store the loop reference for cross-thread shutdown signaling.
        self._loop = asyncio.get_running_loop()

        # Run lifespan startup.
        self._lifespan_manager = LifespanManager(self._app)
        await self._lifespan_manager.startup()

        if self._lifespan_manager.startup_failed:
            logger.error(
                "Lifespan startup failed: %s. Stopping server.",
                self._lifespan_manager.failure_message,
            )
            self._running = False
            return

        # Create and start the async server core.
        self._server_core = AsyncServerCore(
            app=self._app,
            host=self._host,
            port=self._port,
            debug=self._debug,
            request_logger=self._request_logger,
        )
        await self._server_core.start()

        # Install signal handlers for graceful shutdown.
        loop = asyncio.get_running_loop()
        self._setup_signal_handlers(loop)

        logger.info(
            "Async server core running on %s:%d. Waiting for shutdown signal.",
            self._host,
            self._port,
        )

        # Block until the shutdown event is set.
        await self._shutdown_event.wait()

        # Run lifespan shutdown.
        await self._lifespan_manager.shutdown()

        # Stop the server core.
        await self._server_core.stop()
        self._server_core = None

        logger.info("Async event loop shutdown complete.")

        return

    def _setup_signal_handlers(self, loop: asyncio.AbstractEventLoop) -> None:
        """
            Register SIGINT and SIGTERM handlers on the event loop.

            Each signal sets the shutdown event to trigger graceful
            shutdown of the async server core.

            Signal handlers can only be installed from the main thread.
            If the event loop is running in a non-main thread, the
            handlers are skipped with a debug log message.

            :param loop: The running asyncio event loop.
        """
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(
                    sig,
                    self._shutdown_event.set,
                )
            except RuntimeError:
                logger.debug(
                    "Cannot install signal handler for %s: "
                    "not running in the main thread.",
                    sig.name,
                )
                return

        logger.debug("Signal handlers installed for SIGINT and SIGTERM.")

        return

    # -------------------------------------------------------------------------
    # Internal Setup
    # -------------------------------------------------------------------------

    def _setup_debug_middleware(self) -> None:
        """
            Configure debug middleware for error handling.

            This is a placeholder that will be expanded when the debug
            error handler is implemented.
        """
        logger.debug("Debug middleware configured.")
        return

    def _setup_request_logging(self) -> None:
        """
            Configure request logging middleware.

            Creates a :class:`RequestLogger` instance and stores it on
            the server for use during request processing.
        """
        from ccai.webworks.devexp.server.requestlogger import RequestLogger

        self._request_logger = RequestLogger(use_colors=self._debug)

        logger.debug("Request logging configured.")

        return

    def _setup_file_watcher(self) -> None:
        """
            Configure and start the file watcher for auto-reload.

            Creates a :class:`FileWatcher` that monitors files matching
            the configured watch patterns and excludes files matching
            the exclude patterns. When a change is detected, the
            server restart callback is invoked.
        """
        from ccai.webworks.devexp.server.filewatcher import FileWatcher

        self._watcher = FileWatcher(
            patterns=self._watch_patterns,
            excludes=self._exclude_patterns,
            callback=self._restart_server,
        )
        self._watcher.start()

        logger.debug(
            "File watcher configured with patterns=%s, excludes=%s.",
            self._watch_patterns,
            self._exclude_patterns,
        )

        return

    def _restart_server(self) -> None:
        """
            Restart the server in response to a file change.

            Preserves the bound host and port across the restart.
            Increments the restart counter. If a syntax error or
            import error occurs during the restart, the error is
            logged and the server continues watching for further
            changes.

            When an async server core is running, stops and restarts
            it. Otherwise, performs the legacy restart logic.
        """
        logger.info(
            "File change detected. Restarting server on %s:%d...",
            self._host,
            self._port,
        )

        # Preserve the bound address
        host = self._host
        port = self._port

        try:
            # Simulate stopping the application layer
            self._running = False

            # Re-setup middleware
            if self._debug is True:
                self._setup_debug_middleware()

            self._setup_request_logging()

            # If the async server core is running, stop and restart it.
            if self._server_core is not None:
                loop = asyncio.get_running_loop()
                loop.create_task(self._restart_server_core())
            else:
                self._running = True
                self._restart_count += 1

                logger.info(
                    "Server restarted successfully on %s:%d (restart #%d).",
                    host,
                    port,
                    self._restart_count,
                )
        except (SyntaxError, ImportError) as exc:
            # Display the error and continue watching for fixes
            self._last_reload_error = exc
            self._running = False

            logger.error(
                "Error during reload: %s: %s. Watching for fixes...",
                type(exc).__name__,
                exc,
            )
        except Exception as exc:
            self._last_reload_error = exc
            self._running = False

            logger.error(
                "Unexpected error during reload: %s: %s. Watching for fixes...",
                type(exc).__name__,
                exc,
            )

        return

    async def _restart_server_core(self) -> None:
        """
            Stop and restart the async server core during a file-change
            reload.

            Stops the current server core, creates a new one, and starts
            it. Increments the restart count on success. Catches
            ``SyntaxError`` and ``ImportError`` and logs on failure.
        """
        host = self._host
        port = self._port

        try:
            await self._server_core.stop()

            self._server_core = AsyncServerCore(
                app=self._app,
                host=host,
                port=port,
                debug=self._debug,
                request_logger=self._request_logger,
            )
            await self._server_core.start()

            self._running = True
            self._restart_count += 1

            logger.info(
                "Server restarted successfully on %s:%d (restart #%d).",
                host,
                port,
                self._restart_count,
            )
        except (SyntaxError, ImportError) as exc:
            self._last_reload_error = exc
            self._running = False

            logger.error(
                "Error during reload: %s: %s. Watching for fixes...",
                type(exc).__name__,
                exc,
            )
        except Exception as exc:
            self._last_reload_error = exc
            self._running = False

            logger.error(
                "Unexpected error during reload: %s: %s. Watching for fixes...",
                type(exc).__name__,
                exc,
            )

        return

    def format_reload_error(self, error: Exception) -> str:
        """
            Format a reload error into a user-friendly message.

            For :class:`SyntaxError` exceptions, includes the filename,
            line number, and the offending line of code. For other
            exceptions, includes the exception type and message.

            :param error: The exception that occurred during reload.

            :returns: A formatted error message string.
        """
        lines = []

        if isinstance(error, SyntaxError):
            lines.append("Syntax Error during reload:")
            if error.filename is not None:
                lines.append("  File: {}".format(error.filename))
            if error.lineno is not None:
                lines.append("  Line: {}".format(error.lineno))
            if error.text is not None:
                lines.append("  Code: {}".format(error.text.strip()))
            lines.append("  Message: {}".format(error.msg))
        elif isinstance(error, ImportError):
            lines.append("Import Error during reload:")
            lines.append("  Module: {}".format(error.name))
            lines.append("  Message: {}".format(str(error)))
        else:
            lines.append("Error during reload:")
            lines.append("  Type: {}".format(type(error).__name__))
            lines.append("  Message: {}".format(str(error)))

        lines.append("")
        lines.append("Watching for file changes to retry...")

        message = "\n".join(lines)

        return message
