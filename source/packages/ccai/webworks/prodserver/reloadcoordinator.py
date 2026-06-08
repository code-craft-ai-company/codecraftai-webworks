"""
    Reload coordinator module for the production server.

    This module provides the ReloadCoordinator class that manages
    the configuration reload process. When a SIGHUP signal is received,
    the coordinator transitions the server state to RELOADING, calls
    the on_reload hook if configured, performs a rolling restart of
    workers without dropping connections, and transitions back to
    RUNNING state.
"""

import logging
import threading
from typing import TYPE_CHECKING

from ccai.webworks.prodserver.serverconfig import ServerState

if TYPE_CHECKING:
    from ccai.webworks.prodserver.serverconfig import ServerConfig
    from ccai.webworks.prodserver.workermanager import WorkerManager


# Default logger for reload coordinator
_logger = logging.getLogger("webworks.prodserver.reloadcoordinator")


class ReloadCoordinator:
    """
        Coordinates the configuration reload process for the production server.

        When a reload is initiated (typically via SIGHUP), the coordinator:
        1. Transitions the server state to RELOADING.
        2. Calls the on_reload hook if configured.
        3. Performs a rolling restart of workers, terminating each worker
           one at a time and spawning a replacement before moving to the
           next, so that connections are not dropped.
        4. Transitions the server state back to RUNNING.
    """

    def __init__(
        self,
        config: "ServerConfig",
        worker_manager: "WorkerManager"
    ):
        """
            Construct a ReloadCoordinator.

            :param config: Server configuration containing the on_reload hook.
            :param worker_manager: The WorkerManager instance for worker control.
        """
        self._config = config
        self._worker_manager = worker_manager
        self._state: ServerState = ServerState.STOPPED
        self._lock: threading.Lock = threading.Lock()

        return

    @property
    def state(self) -> ServerState:
        """
            Get the current server state.

            :returns: The current ServerState.
        """
        return self._state

    def start(self) -> None:
        """
            Mark the coordinator as started.

            Transitions the server state to RUNNING so that reload
            operations can be performed.
        """
        with self._lock:
            self._state = ServerState.RUNNING

        _logger.info("Reload coordinator started")

        return

    def reload(self) -> None:
        """
            Perform a configuration reload with rolling worker restart.

            Transitions the server state to RELOADING, calls the on_reload
            hook if configured, performs a rolling restart of workers one
            at a time to avoid dropping connections, and transitions back
            to RUNNING state.

            If the coordinator is not in RUNNING state, the reload is
            skipped. If a reload is already in progress, the request is
            ignored.
        """
        with self._lock:
            if self._state == ServerState.RELOADING:
                _logger.warning("Reload already in progress")
                return

            if self._state != ServerState.RUNNING:
                _logger.warning(
                    "Cannot reload in state %s, must be RUNNING",
                    self._state.value
                )
                return

            self._state = ServerState.RELOADING

        _logger.info("Configuration reload initiated")

        try:
            self._call_on_reload_hook()
            self._rolling_restart_workers()
        except Exception:
            _logger.exception("Error during configuration reload")
        finally:
            with self._lock:
                self._state = ServerState.RUNNING

        _logger.info("Configuration reload complete")

        return

    def _call_on_reload_hook(self) -> None:
        """
            Call the on_reload hook if configured.

            The hook is called with the server configuration as the
            argument. Any exception raised by the hook is logged but
            does not prevent the reload from continuing.
        """
        on_reload = self._config.on_reload

        if on_reload is None:
            return

        try:
            _logger.info("Calling on_reload hook")
            on_reload(self._config)
        except Exception:
            _logger.exception("Error in on_reload hook")

        return

    def _rolling_restart_workers(self) -> None:
        """
            Perform a rolling restart of all workers.

            Iterates through the current workers one at a time,
            terminating each worker gracefully and spawning a
            replacement before moving to the next. This ensures
            that connections are not dropped during the reload.
        """
        with self._worker_manager._lock:
            worker_ids = list(self._worker_manager._workers.keys())

        if len(worker_ids) == 0:
            _logger.info("No workers to restart during reload")
            return

        _logger.info(
            "Starting rolling restart of %d worker(s)",
            len(worker_ids)
        )

        for worker_id in worker_ids:
            _logger.info("Rolling restart: terminating worker %d", worker_id)
            self._worker_manager.terminate_worker(worker_id, graceful=True)

            _logger.info("Rolling restart: spawning replacement for worker %d", worker_id)
            self._worker_manager.spawn_worker()

        _logger.info("Rolling restart complete")

        return
