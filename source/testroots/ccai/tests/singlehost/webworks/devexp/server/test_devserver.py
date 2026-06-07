"""
    Tests for the DevelopmentServer class and port-in-use handling.

    This module contains unit tests for the DevelopmentServer configuration,
    lifecycle methods, port availability checking, and the user-friendly
    port-in-use error message formatting.
"""

import signal
import socket

from ccai.webworks.devexp.server.devserver import (
    DEFAULT_EXCLUDE_PATTERNS,
    DEFAULT_WATCH_PATTERNS,
    DevelopmentServer,
    PortInUseError,
    check_port_available,
    format_port_in_use_message,
)


# =============================================================================
# Test Helpers
# =============================================================================

class _FakeApp:
    """
        A minimal fake application for testing DevelopmentServer.
    """
    pass


# =============================================================================
# Unit Tests for DevelopmentServer Configuration
# =============================================================================

def test_devserver_default_host():
    """
        Test that the default host is 127.0.0.1.
    """
    server = DevelopmentServer(app=_FakeApp())

    if server.host != "127.0.0.1":
        errmsg = "Expected host '127.0.0.1', got '{}'".format(server.host)
        raise AssertionError(errmsg)

    return


def test_devserver_default_port():
    """
        Test that the default port is 8000.
    """
    server = DevelopmentServer(app=_FakeApp())

    if server.port != 8000:
        errmsg = "Expected port 8000, got {}".format(server.port)
        raise AssertionError(errmsg)

    return


def test_devserver_default_debug_is_true():
    """
        Test that debug mode is enabled by default.
    """
    server = DevelopmentServer(app=_FakeApp())

    if server.debug is not True:
        errmsg = "Expected debug=True, got {}".format(server.debug)
        raise AssertionError(errmsg)

    return


def test_devserver_default_reload_is_false():
    """
        Test that auto-reload is disabled by default.
    """
    server = DevelopmentServer(app=_FakeApp())

    if server.reload is not False:
        errmsg = "Expected reload=False, got {}".format(server.reload)
        raise AssertionError(errmsg)

    return


def test_devserver_custom_host():
    """
        Test that a custom host is stored correctly.
    """
    server = DevelopmentServer(app=_FakeApp(), host="0.0.0.0")

    if server.host != "0.0.0.0":
        errmsg = "Expected host '0.0.0.0', got '{}'".format(server.host)
        raise AssertionError(errmsg)

    return


def test_devserver_custom_port():
    """
        Test that a custom port is stored correctly.
    """
    server = DevelopmentServer(app=_FakeApp(), port=9000)

    if server.port != 9000:
        errmsg = "Expected port 9000, got {}".format(server.port)
        raise AssertionError(errmsg)

    return


def test_devserver_debug_disabled():
    """
        Test that debug mode can be disabled.
    """
    server = DevelopmentServer(app=_FakeApp(), debug=False)

    if server.debug is not False:
        errmsg = "Expected debug=False, got {}".format(server.debug)
        raise AssertionError(errmsg)

    return


def test_devserver_reload_enabled():
    """
        Test that auto-reload can be enabled.
    """
    server = DevelopmentServer(app=_FakeApp(), reload=True)

    if server.reload is not True:
        errmsg = "Expected reload=True, got {}".format(server.reload)
        raise AssertionError(errmsg)

    return


def test_devserver_default_watch_patterns():
    """
        Test that default watch patterns are used when none are provided.
    """
    server = DevelopmentServer(app=_FakeApp())

    if server.watch_patterns != DEFAULT_WATCH_PATTERNS:
        errmsg = "Expected default watch patterns {}, got {}".format(
            DEFAULT_WATCH_PATTERNS, server.watch_patterns
        )
        raise AssertionError(errmsg)

    return


def test_devserver_custom_watch_patterns():
    """
        Test that custom watch patterns are stored correctly.
    """
    patterns = ["**/*.py", "**/*.html"]
    server = DevelopmentServer(app=_FakeApp(), watch_patterns=patterns)

    if server.watch_patterns != patterns:
        errmsg = "Expected watch patterns {}, got {}".format(
            patterns, server.watch_patterns
        )
        raise AssertionError(errmsg)

    return


def test_devserver_default_exclude_patterns():
    """
        Test that default exclude patterns are used when none are provided.
    """
    server = DevelopmentServer(app=_FakeApp())

    if server.exclude_patterns != DEFAULT_EXCLUDE_PATTERNS:
        errmsg = "Expected default exclude patterns {}, got {}".format(
            DEFAULT_EXCLUDE_PATTERNS, server.exclude_patterns
        )
        raise AssertionError(errmsg)

    return


def test_devserver_custom_exclude_patterns():
    """
        Test that custom exclude patterns are stored correctly.
    """
    patterns = [".git", "node_modules"]
    server = DevelopmentServer(app=_FakeApp(), exclude_patterns=patterns)

    if server.exclude_patterns != patterns:
        errmsg = "Expected exclude patterns {}, got {}".format(
            patterns, server.exclude_patterns
        )
        raise AssertionError(errmsg)

    return


def test_devserver_stores_app():
    """
        Test that the app instance is stored correctly.
    """
    app = _FakeApp()
    server = DevelopmentServer(app=app)

    if server.app is not app:
        errmsg = "Expected server.app to be the provided app instance."
        raise AssertionError(errmsg)

    return


def test_devserver_not_running_initially():
    """
        Test that the server is not running after construction.
    """
    server = DevelopmentServer(app=_FakeApp())

    if server.running is not False:
        errmsg = "Expected running=False initially, got {}".format(server.running)
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for DevelopmentServer Lifecycle
# =============================================================================

def test_devserver_start_sets_running():
    """
        Test that start() sets the running flag to True.
    """
    server = DevelopmentServer(app=_FakeApp(), host="127.0.0.1", port=0)

    server.serve_forever()

    try:
        if server.running is not True:
            errmsg = "Expected running=True after start, got {}".format(server.running)
            raise AssertionError(errmsg)
    finally:
        server.stop()

    return


def test_devserver_stop_clears_running():
    """
        Test that stop() sets the running flag to False.
    """
    server = DevelopmentServer(app=_FakeApp(), host="127.0.0.1", port=0)

    server.serve_forever()
    server.stop()

    if server.running is not False:
        errmsg = "Expected running=False after stop, got {}".format(server.running)
        raise AssertionError(errmsg)

    return


def test_devserver_start_configures_request_logger():
    """
        Test that start() configures the request logger.
    """
    server = DevelopmentServer(app=_FakeApp(), host="127.0.0.1", port=0)

    server.serve_forever()

    try:
        if server.request_logger is None:
            errmsg = "Expected request_logger to be configured after start."
            raise AssertionError(errmsg)
    finally:
        server.stop()

    return


def test_devserver_start_raises_port_in_use():
    """
        Test that start() raises PortInUseError when the port is occupied.
    """
    # Bind a socket to occupy a port
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("127.0.0.1", 0))
    occupied_port = sock.getsockname()[1]

    try:
        server = DevelopmentServer(
            app=_FakeApp(), host="127.0.0.1", port=occupied_port
        )

        raised = False
        try:
            server.serve_forever()
        except PortInUseError as exc:
            raised = True
            if exc.port != occupied_port:
                errmsg = "Expected port {}, got {}".format(occupied_port, exc.port)
                raise AssertionError(errmsg)
            if exc.host != "127.0.0.1":
                errmsg = "Expected host '127.0.0.1', got '{}'".format(exc.host)
                raise AssertionError(errmsg)

        if raised is not True:
            errmsg = "Expected PortInUseError to be raised."
            raise AssertionError(errmsg)
    finally:
        sock.close()

    return


# =============================================================================
# Unit Tests for check_port_available
# =============================================================================

def test_check_port_available_returns_true_for_free_port():
    """
        Test that check_port_available returns True for an unoccupied port.
    """
    # Use port 0 to let the OS assign a free port, then check that port
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 0))
    free_port = sock.getsockname()[1]
    sock.close()

    result = check_port_available("127.0.0.1", free_port)

    if result is not True:
        errmsg = "Expected True for free port {}, got {}".format(free_port, result)
        raise AssertionError(errmsg)

    return


def test_check_port_available_returns_false_for_occupied_port():
    """
        Test that check_port_available returns False for an occupied port.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("127.0.0.1", 0))
    occupied_port = sock.getsockname()[1]

    try:
        result = check_port_available("127.0.0.1", occupied_port)

        if result is not False:
            errmsg = "Expected False for occupied port {}, got {}".format(
                occupied_port, result
            )
            raise AssertionError(errmsg)
    finally:
        sock.close()

    return


# =============================================================================
# Unit Tests for PortInUseError
# =============================================================================

def test_port_in_use_error_has_host():
    """
        Test that PortInUseError stores the host.
    """
    exc = PortInUseError("localhost", 8080)

    if exc.host != "localhost":
        errmsg = "Expected host 'localhost', got '{}'".format(exc.host)
        raise AssertionError(errmsg)

    return


def test_port_in_use_error_has_port():
    """
        Test that PortInUseError stores the port.
    """
    exc = PortInUseError("localhost", 8080)

    if exc.port != 8080:
        errmsg = "Expected port 8080, got {}".format(exc.port)
        raise AssertionError(errmsg)

    return


def test_port_in_use_error_message():
    """
        Test that PortInUseError has a descriptive message.
    """
    exc = PortInUseError("127.0.0.1", 8000)
    message = str(exc)

    if "8000" not in message:
        errmsg = "Expected port in message, got '{}'".format(message)
        raise AssertionError(errmsg)

    if "127.0.0.1" not in message:
        errmsg = "Expected host in message, got '{}'".format(message)
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for format_port_in_use_message
# =============================================================================

def test_format_port_in_use_message_contains_port():
    """
        Test that the formatted message contains the port number.
    """
    message = format_port_in_use_message("127.0.0.1", 8000)

    if "8000" not in message:
        errmsg = "Expected '8000' in message, got:\n{}".format(message)
        raise AssertionError(errmsg)

    return


def test_format_port_in_use_message_contains_host():
    """
        Test that the formatted message contains the host address.
    """
    message = format_port_in_use_message("127.0.0.1", 8000)

    if "127.0.0.1" not in message:
        errmsg = "Expected '127.0.0.1' in message, got:\n{}".format(message)
        raise AssertionError(errmsg)

    return


def test_format_port_in_use_message_contains_suggestions():
    """
        Test that the formatted message contains alternative port suggestions.
    """
    message = format_port_in_use_message("127.0.0.1", 8000)

    if "8001" not in message:
        errmsg = "Expected alternative port 8001 in message."
        raise AssertionError(errmsg)

    if "--port" not in message:
        errmsg = "Expected '--port' flag in suggestions."
        raise AssertionError(errmsg)

    return


def test_format_port_in_use_message_contains_stop_suggestion():
    """
        Test that the formatted message suggests stopping the existing process.
    """
    message = format_port_in_use_message("127.0.0.1", 8000)

    if "Stop" not in message and "stop" not in message.lower():
        errmsg = "Expected suggestion to stop existing process."
        raise AssertionError(errmsg)

    return


# =============================================================================
# Property Tests for DevelopmentServer
# =============================================================================

def test_property_reload_restart_count():
    """
        Property 13: Reload Restart Count Increment.

        For any sequence of successful file-change reloads, the
        restart_count property should equal the number of successful
        reloads performed.

        **Validates: Requirements 10.4**
    """
    import random

    for _ in range(100):
        server = DevelopmentServer(app=_FakeApp(), host="127.0.0.1", port=0)
        server.serve_forever()

        try:
            num_reloads = random.randint(0, 20)

            for _ in range(num_reloads):
                server._restart_server()

            if server.restart_count != num_reloads:
                errmsg = (
                    "Expected restart_count={} after {} reloads, got {}"
                    .format(num_reloads, num_reloads, server.restart_count)
                )
                raise AssertionError(errmsg)
        finally:
            server.stop()

    return


# =============================================================================
# Unit Tests for DevelopmentServer Integration
# =============================================================================

def test_devserver_start_blocks_until_stopped():
    """
        Test that start() blocks the calling thread until stop() is called
        when the app is a callable ASGI application.

        Requirements: 1.4
    """
    import threading
    import time

    async def _simple_asgi_app(scope, receive, send):
        """A minimal ASGI app that handles lifespan and HTTP."""
        if scope["type"] == "lifespan":
            message = await receive()
            if message["type"] == "lifespan.startup":
                await send({"type": "lifespan.startup.complete"})
            message = await receive()
            if message["type"] == "lifespan.shutdown":
                await send({"type": "lifespan.shutdown.complete"})
            return
        return

    server = DevelopmentServer(
        app=_simple_asgi_app, host="127.0.0.1", port=0, debug=False,
    )

    started = threading.Event()
    finished = threading.Event()

    def run_server():
        started.set()
        server.serve_forever()
        finished.set()

    thread = threading.Thread(target=run_server, daemon=True)
    thread.start()

    # Wait for the thread to start.
    started.wait(timeout=2.0)
    # Give the server a moment to enter the event loop.
    time.sleep(0.5)

    # The thread should still be blocked in start().
    if finished.is_set():
        raise AssertionError("Expected start() to block, but it returned early.")

    # Now stop the server.
    server.stop()

    # Wait for the thread to finish.
    thread.join(timeout=5.0)

    if not finished.is_set():
        raise AssertionError("Expected start() to unblock after stop(), but it did not.")

    return


def test_devserver_sigint_triggers_graceful_shutdown():
    """
        Test that SIGINT/SIGTERM signal handling is configured when running
        in the main thread. We verify this by testing the _setup_signal_handlers
        method directly with a mock loop and shutdown event.

        Requirements: 6.3
    """
    import asyncio

    server = DevelopmentServer(
        app=_FakeApp(), host="127.0.0.1", port=0, debug=False,
    )

    # Create a shutdown event and assign it to the server.
    shutdown_event = asyncio.Event()
    server._shutdown_event = shutdown_event

    # Track which signals were registered.
    registered_signals = []

    class _FakeLoop:
        """A fake event loop that records add_signal_handler calls."""
        def add_signal_handler(self, sig, callback):
            registered_signals.append((sig, callback))

    fake_loop = _FakeLoop()
    server._setup_signal_handlers(fake_loop)

    # Verify that SIGINT and SIGTERM were registered.
    registered_sigs = [sig for sig, _ in registered_signals]

    if signal.SIGINT not in registered_sigs:
        raise AssertionError("Expected SIGINT to be registered.")

    if signal.SIGTERM not in registered_sigs:
        raise AssertionError("Expected SIGTERM to be registered.")

    # Verify that the callback sets the shutdown event.
    for sig, callback in registered_signals:
        callback()

    if not shutdown_event.is_set():
        raise AssertionError(
            "Expected shutdown event to be set after signal callback."
        )

    return


def test_devserver_lifespan_startup_failure_stops_server():
    """
        Test that lifespan startup failure stops the server.

        Requirements: 5.2
    """
    import threading

    async def _failing_lifespan_app(scope, receive, send):
        """An ASGI app that fails lifespan startup."""
        if scope["type"] == "lifespan":
            message = await receive()
            if message["type"] == "lifespan.startup":
                await send({
                    "type": "lifespan.startup.failed",
                    "message": "Database connection failed",
                })
            return
        return

    server = DevelopmentServer(
        app=_failing_lifespan_app, host="127.0.0.1", port=0, debug=False,
    )

    finished = threading.Event()

    def run_server():
        server.serve_forever()
        finished.set()

    thread = threading.Thread(target=run_server, daemon=True)
    thread.start()

    # The server should stop quickly because lifespan startup failed.
    thread.join(timeout=5.0)

    if not finished.is_set():
        raise AssertionError(
            "Expected start() to return after lifespan startup failure."
        )

    if server.running is not False:
        raise AssertionError(
            "Expected running=False after lifespan startup failure, got True."
        )

    return


def test_devserver_syntax_error_during_reload_logs_error():
    """
        Test that a SyntaxError during reload logs the error and the
        server continues watching for fixes.

        Requirements: 10.3
    """
    server = DevelopmentServer(app=_FakeApp(), host="127.0.0.1", port=0)
    server.serve_forever()

    try:
        # Patch _setup_request_logging to raise SyntaxError to simulate
        # a reload failure.
        original_setup = server._setup_request_logging

        def _raise_syntax_error():
            raise SyntaxError("invalid syntax")

        server._setup_request_logging = _raise_syntax_error

        server._restart_server()

        # The server should have recorded the error.
        if server.last_reload_error is None:
            raise AssertionError(
                "Expected last_reload_error to be set after SyntaxError."
            )

        if not isinstance(server.last_reload_error, SyntaxError):
            raise AssertionError(
                "Expected last_reload_error to be SyntaxError, got {}".format(
                    type(server.last_reload_error).__name__
                )
            )

        # The server should not be running after a failed reload.
        if server.running is not False:
            raise AssertionError(
                "Expected running=False after SyntaxError during reload."
            )
    finally:
        server._setup_request_logging = original_setup
        server.stop()

    return


def test_devserver_successful_reload_increments_restart_count():
    """
        Test that a successful reload increments the restart_count.

        Requirements: 10.4
    """
    server = DevelopmentServer(app=_FakeApp(), host="127.0.0.1", port=0)
    server.serve_forever()

    try:
        initial_count = server.restart_count

        server._restart_server()

        if server.restart_count != initial_count + 1:
            errmsg = (
                "Expected restart_count={} after reload, got {}"
                .format(initial_count + 1, server.restart_count)
            )
            raise AssertionError(errmsg)
    finally:
        server.stop()

    return
