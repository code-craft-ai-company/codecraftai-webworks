"""
    Tests for the SignalHandler class.

    This module contains unit tests for the production server SignalHandler
    class including signal registration, handler invocation for SIGTERM,
    SIGINT, and SIGHUP, and handler unregistration.
"""

import signal

from ccai.errors.exceptions import SkipError
from ccai.testbase.mocking import Mock
from ccai.webworks.prodserver.signalhandler import SignalHandler


def _require_sighup() -> None:
    """
        Skip the calling test on platforms whose signal module has no SIGHUP.

        :raises SkipError: When SIGHUP is not defined (Windows).
    """
    if not hasattr(signal, "SIGHUP"):
        raise SkipError("SIGHUP is not defined on this platform")
    return


def _create_mock_server():
    """
        Create a mock server object with stop() and reload() methods.

        :returns: A tuple of (mock_server, stop_mock, reload_mock).
    """
    mock_server = Mock()
    mock_server.configure(recursive=True)

    ctx = mock_server.mock_context()
    stop_mock = ctx.mock_method("stop")
    reload_mock = ctx.mock_method("reload")

    return mock_server, stop_mock, reload_mock


# =============================================================================
# Unit Tests for SignalHandler Initialization
# =============================================================================

def test_signal_handler_stores_server_reference():
    """
        Test that the SignalHandler stores the server reference.
    """
    mock_server, _, _ = _create_mock_server()
    handler = SignalHandler(mock_server)

    if handler.server is not mock_server:
        errmsg = "Expected handler.server to be the same object as the provided server"
        raise AssertionError(errmsg)

    return


def test_signal_handler_not_registered_initially():
    """
        Test that a new SignalHandler is not registered initially.
    """
    mock_server, _, _ = _create_mock_server()
    handler = SignalHandler(mock_server)

    if handler.registered is not False:
        errmsg = "Expected handler.registered to be False initially"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for Signal Registration
# =============================================================================

def test_signal_handler_register_sets_registered_flag():
    """
        Test that register() sets the registered flag to True.
    """
    mock_server, _, _ = _create_mock_server()
    handler = SignalHandler(mock_server)
    handler.register()

    try:
        if handler.registered is not True:
            errmsg = "Expected handler.registered to be True after register()"
            raise AssertionError(errmsg)
    finally:
        handler.unregister()

    return


def test_signal_handler_register_installs_sigterm_handler():
    """
        Test that register() installs a custom SIGTERM handler
        that is not the default handler.
    """
    mock_server, _, _ = _create_mock_server()
    handler = SignalHandler(mock_server)

    previous_handler = signal.getsignal(signal.SIGTERM)
    handler.register()

    try:
        current_handler = signal.getsignal(signal.SIGTERM)

        if current_handler is previous_handler:
            errmsg = "Expected SIGTERM handler to be changed after register()"
            raise AssertionError(errmsg)
    finally:
        handler.unregister()

    return


def test_signal_handler_register_installs_sigint_handler():
    """
        Test that register() installs a custom SIGINT handler
        that is not the default handler.
    """
    mock_server, _, _ = _create_mock_server()
    handler = SignalHandler(mock_server)

    previous_handler = signal.getsignal(signal.SIGINT)
    handler.register()

    try:
        current_handler = signal.getsignal(signal.SIGINT)

        if current_handler is previous_handler:
            errmsg = "Expected SIGINT handler to be changed after register()"
            raise AssertionError(errmsg)
    finally:
        handler.unregister()

    return


def test_signal_handler_register_installs_sighup_handler():
    """
        Test that register() installs a custom SIGHUP handler
        that is not the default handler.
    """
    _require_sighup()

    mock_server, _, _ = _create_mock_server()
    handler = SignalHandler(mock_server)

    previous_handler = signal.getsignal(signal.SIGHUP)
    handler.register()

    try:
        current_handler = signal.getsignal(signal.SIGHUP)

        if current_handler is previous_handler:
            errmsg = "Expected SIGHUP handler to be changed after register()"
            raise AssertionError(errmsg)
    finally:
        handler.unregister()

    return


def test_signal_handler_double_register_is_safe():
    """
        Test that calling register() twice does not raise an error.
    """
    mock_server, _, _ = _create_mock_server()
    handler = SignalHandler(mock_server)
    handler.register()

    try:
        handler.register()

        if handler.registered is not True:
            errmsg = "Expected handler.registered to remain True after double register"
            raise AssertionError(errmsg)
    finally:
        handler.unregister()

    return


def test_signal_handler_supported_handlers_follow_platform():
    """
        Test that supported_handlers() lists SIGTERM and SIGINT everywhere
        and SIGHUP only where the signal module defines it.
    """
    mock_server, _, _ = _create_mock_server()
    handler = SignalHandler(mock_server)

    handlers = handler.supported_handlers()

    if handlers.get(signal.SIGTERM) != handler.handle_sigterm:
        errmsg = "Expected SIGTERM to map to handle_sigterm"
        raise AssertionError(errmsg)

    if handlers.get(signal.SIGINT) != handler.handle_sigint:
        errmsg = "Expected SIGINT to map to handle_sigint"
        raise AssertionError(errmsg)

    expected_count = 3 if hasattr(signal, "SIGHUP") else 2
    if len(handlers) != expected_count:
        errmsg = f"Expected {expected_count} supported signals, got {sorted(handlers)}"
        raise AssertionError(errmsg)

    if hasattr(signal, "SIGHUP") and handlers.get(signal.SIGHUP) != handler.handle_sighup:
        errmsg = "Expected SIGHUP to map to handle_sighup"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for Signal Handler Invocation
# =============================================================================

def test_handle_sigterm_calls_server_stop_graceful():
    """
        Test that handle_sigterm calls server.stop(graceful=True).

        Validates: Requirements 2.1
    """
    mock_server, stop_mock, _ = _create_mock_server()
    handler = SignalHandler(mock_server)

    handler.handle_sigterm(signal.SIGTERM, None)

    stop_mock.mock_context().assert_called_once_with(graceful=True)

    return


def test_handle_sigint_calls_server_stop_graceful():
    """
        Test that handle_sigint calls server.stop(graceful=True).

        Validates: Requirements 2.2
    """
    mock_server, stop_mock, _ = _create_mock_server()
    handler = SignalHandler(mock_server)

    handler.handle_sigint(signal.SIGINT, None)

    stop_mock.mock_context().assert_called_once_with(graceful=True)

    return


def test_handle_sighup_calls_server_reload():
    """
        Test that handle_sighup calls server.reload().

        Validates: Requirements 2.7
    """
    _require_sighup()

    mock_server, _, reload_mock = _create_mock_server()
    handler = SignalHandler(mock_server)

    handler.handle_sighup(signal.SIGHUP, None)

    reload_mock.mock_context().assert_called_once()

    return


# =============================================================================
# Unit Tests for Signal Unregistration
# =============================================================================

def test_signal_handler_unregister_clears_registered_flag():
    """
        Test that unregister() sets the registered flag to False.
    """
    mock_server, _, _ = _create_mock_server()
    handler = SignalHandler(mock_server)
    handler.register()

    handler.unregister()

    if handler.registered is not False:
        errmsg = "Expected handler.registered to be False after unregister()"
        raise AssertionError(errmsg)

    return


def test_signal_handler_unregister_restores_previous_handlers():
    """
        Test that unregister() restores the previous signal handlers.
    """
    has_sighup = hasattr(signal, "SIGHUP")

    previous_sigterm = signal.getsignal(signal.SIGTERM)
    previous_sigint = signal.getsignal(signal.SIGINT)
    previous_sighup = signal.getsignal(signal.SIGHUP) if has_sighup else None

    mock_server, _, _ = _create_mock_server()
    handler = SignalHandler(mock_server)
    handler.register()
    handler.unregister()

    restored_sigterm = signal.getsignal(signal.SIGTERM)
    restored_sigint = signal.getsignal(signal.SIGINT)
    restored_sighup = signal.getsignal(signal.SIGHUP) if has_sighup else None

    if restored_sigterm != previous_sigterm:
        errmsg = "Expected SIGTERM handler to be restored to previous handler"
        raise AssertionError(errmsg)

    if restored_sigint != previous_sigint:
        errmsg = "Expected SIGINT handler to be restored to previous handler"
        raise AssertionError(errmsg)

    # SIGHUP is only registered where the platform defines it
    if has_sighup and restored_sighup != previous_sighup:
        errmsg = "Expected SIGHUP handler to be restored to previous handler"
        raise AssertionError(errmsg)

    return


def test_signal_handler_unregister_without_register_is_safe():
    """
        Test that calling unregister() without register() does not raise.
    """
    mock_server, _, _ = _create_mock_server()
    handler = SignalHandler(mock_server)

    handler.unregister()

    if handler.registered is not False:
        errmsg = "Expected handler.registered to remain False"
        raise AssertionError(errmsg)

    return
