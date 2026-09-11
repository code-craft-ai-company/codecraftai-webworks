"""
    Signal handler module for the production server.

    This module provides the SignalHandler class that registers and
    manages OS signal handlers for server control. It handles SIGTERM
    and SIGINT for graceful shutdown, and SIGHUP for configuration
    reload without dropping connections. SIGHUP is only registered on
    platforms that define it; Windows has no SIGHUP, so only SIGTERM
    and SIGINT are installed there.
"""

import logging
import signal
from typing import Any, Callable, Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from types import FrameType


# Default logger for signal handler
_logger = logging.getLogger("webworks.prodserver.signalhandler")


class SignalHandler:
    """
        Handles OS signals for server control.

        Registers signal handlers for SIGTERM, SIGINT, and SIGHUP to
        provide graceful shutdown and configuration reload capabilities.
        Previous signal handlers are stored so they can be restored
        via the unregister() method.
    """

    def __init__(self, server: object):
        """
            Construct a SignalHandler.

            The server object must provide stop(graceful=True) and
            reload() methods for signal handling to function correctly.

            :param server: The production server instance.
        """
        self._server = server
        self._previous_handlers: Dict[int, Any] = {}
        self._registered: bool = False

        return

    @property
    def server(self) -> object:
        """
            Get the server instance.

            :returns: The production server object.
        """
        return self._server

    @property
    def registered(self) -> bool:
        """
            Check whether signal handlers are currently registered.

            :returns: True if signal handlers are registered.
        """
        return self._registered

    def register(self) -> None:
        """
            Register signal handlers for SIGTERM, SIGINT, and SIGHUP.

            Stores the previous signal handlers so they can be restored
            later via unregister(). If handlers are already registered,
            this method does nothing.
        """
        if self._registered:
            _logger.warning("Signal handlers already registered")
            return

        handlers = self.supported_handlers()

        for signum in handlers:
            self._previous_handlers[signum] = signal.getsignal(signum)

        for signum, handler in handlers.items():
            signal.signal(signum, handler)

        self._registered = True

        names = ", ".join(signal.Signals(signum).name for signum in handlers)
        _logger.info("Signal handlers registered (%s)", names)

        return

    def supported_handlers(self) -> Dict[int, Callable[[int, Optional["FrameType"]], None]]:
        """
            Get the signals this platform supports and the handler for each.

            SIGTERM and SIGINT exist everywhere. SIGHUP is included only
            when the signal module defines it, so the reload handler is
            never registered on platforms that cannot deliver the signal.

            :returns: Mapping of signal number to handler method.
        """
        handlers: Dict[int, Callable[[int, Optional["FrameType"]], None]] = {
            signal.SIGTERM: self.handle_sigterm,
            signal.SIGINT: self.handle_sigint,
        }

        if hasattr(signal, "SIGHUP"):
            handlers[signal.SIGHUP] = self.handle_sighup

        return handlers

    def unregister(self) -> None:
        """
            Restore the previous signal handlers.

            Restores the signal handlers that were in place before
            register() was called. If handlers are not registered,
            this method does nothing.
        """
        if not self._registered:
            _logger.warning("Signal handlers not registered, nothing to unregister")
            return

        for signum, handler in self._previous_handlers.items():
            signal.signal(signum, handler)

        self._previous_handlers.clear()
        self._registered = False

        _logger.info("Signal handlers unregistered, previous handlers restored")

        return

    def handle_sigterm(self, signum: int, frame: Optional["FrameType"]) -> None:
        """
            Handle SIGTERM signal by initiating graceful shutdown.

            :param signum: The signal number received.
            :param frame: The current stack frame.
        """
        _logger.info("Received SIGTERM, initiating graceful shutdown")

        self._server.stop(graceful=True)

        return

    def handle_sigint(self, signum: int, frame: Optional["FrameType"]) -> None:
        """
            Handle SIGINT signal by initiating graceful shutdown.

            :param signum: The signal number received.
            :param frame: The current stack frame.
        """
        _logger.info("Received SIGINT, initiating graceful shutdown")

        self._server.stop(graceful=True)

        return

    def handle_sighup(self, signum: int, frame: Optional["FrameType"]) -> None:
        """
            Handle SIGHUP signal by reloading configuration.

            :param signum: The signal number received.
            :param frame: The current stack frame.
        """
        _logger.info("Received SIGHUP, reloading configuration")

        self._server.reload()

        return
