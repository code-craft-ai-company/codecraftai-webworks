"""
    Shutdown coordinator module for the production server.

    This module provides the ShutdownCoordinator class that manages
    the graceful shutdown process. When a shutdown signal is received,
    the coordinator transitions the server state to SHUTTING_DOWN,
    stops accepting new connections, and allows in-flight requests
    to complete before terminating workers.
"""

import logging
import threading
import time
from typing import Optional, TYPE_CHECKING

from automojo.webworks.prodserver.serverconfig import ServerState

if TYPE_CHECKING:
    from automojo.webworks.prodserver.serverconfig import ServerConfig
    from automojo.webworks.prodserver.workermanager import WorkerManager


# Default logger for shutdown coordinator
_logger = logging.getLogger("webworks.prodserver.shutdowncoordinator")



class ShutdownCoordinator:
    """
        Coordinates the graceful shutdown process for the production server.

        When a shutdown is initiated, the coordinator:
        1. Transitions the server state to SHUTTING_DOWN.
        2. Stops accepting new connections by setting the accepting flag.
        3. Waits for in-flight requests to complete within the graceful
           timeout period.
        4. Terminates workers gracefully through the WorkerManager.
    """

    def __init__(
        self,
        config: "ServerConfig",
        worker_manager: "WorkerManager"
    ):
        """
            Construct a ShutdownCoordinator.

            :param config: Server configuration containing graceful_timeout.
            :param worker_manager: The WorkerManager instance for worker control.
        """
        self._config = config
        self._worker_manager = worker_manager
        self._state: ServerState = ServerState.STOPPED
        self._accepting: bool = False
        self._shutdown_complete: threading.Event = threading.Event()
        self._lock: threading.Lock = threading.Lock()
        self._shutdown_start_time: Optional[float] = None

        return

    @property
    def state(self) -> ServerState:
        """
            Get the current server state.

            :returns: The current ServerState.
        """
        return self._state

    @property
    def is_accepting(self) -> bool:
        """
            Check whether the server is accepting new connections.

            :returns: True if the server is accepting new connections.
        """
        return self._accepting

    @property
    def is_shutdown_complete(self) -> bool:
        """
            Check whether the shutdown process has completed.

            :returns: True if shutdown is complete.
        """
        return self._shutdown_complete.is_set()

    def start(self) -> None:
        """
            Mark the server as started and accepting connections.

            Transitions the server state to RUNNING and enables
            the accepting flag so new connections are allowed.
        """
        with self._lock:
            self._state = ServerState.RUNNING
            self._accepting = True
            self._shutdown_complete.clear()
            self._shutdown_start_time = None

        _logger.info("Shutdown coordinator started, server is accepting connections")

        return

    def get_shutdown_progress(self) -> dict:
        """
            Get the current shutdown progress information.

            Returns a dictionary containing the current state of the
            shutdown process including worker counts, elapsed time,
            and in-flight request counts.

            :returns: Dictionary with shutdown progress details.
        """
        inflight_count = self._get_inflight_count()
        worker_status = self._worker_manager.get_worker_status()

        active_count = 0
        idle_count = 0
        shutting_down_count = 0

        for status in worker_status.values():
            state_value = status.state.value
            if state_value == "active":
                active_count += 1
            elif state_value == "idle":
                idle_count += 1
            elif state_value == "shutting_down":
                shutting_down_count += 1

        elapsed = 0.0
        if self._shutdown_start_time is not None:
            elapsed = time.time() - self._shutdown_start_time

        progress = {
            "state": self._state.value,
            "inflight_requests": inflight_count,
            "total_workers": len(worker_status),
            "active_workers": active_count,
            "idle_workers": idle_count,
            "shutting_down_workers": shutting_down_count,
            "elapsed_time": round(elapsed, 1),
            "graceful_timeout": self._config.graceful_timeout,
        }

        return progress

    def initiate_shutdown(self) -> None:
        """
            Initiate the graceful shutdown process.

            Transitions the server state to SHUTTING_DOWN, stops
            accepting new connections, waits for in-flight requests
            to complete within the graceful timeout, and then
            terminates all workers gracefully.
        """
        with self._lock:
            if self._state == ServerState.SHUTTING_DOWN:
                _logger.warning("Shutdown already in progress")
                return

            if self._state == ServerState.STOPPED:
                _logger.warning("Server is already stopped")
                return

            self._state = ServerState.SHUTTING_DOWN
            self._accepting = False
            self._shutdown_start_time = time.time()

        total_workers = self._worker_manager.get_worker_count()

        _logger.info(
            "Graceful shutdown initiated, no longer accepting new connections"
        )
        _logger.info(
            "Shutdown starting with %d worker(s) active",
            total_workers
        )

        self._log_shutdown_progress()

        graceful_timeout = self._config.graceful_timeout

        all_completed = self._wait_for_inflight_requests(graceful_timeout)

        shutdown_elapsed = time.time() - self._shutdown_start_time

        if all_completed:
            self._worker_manager.terminate_all(graceful=True)
            _logger.info(
                "Graceful shutdown complete, total time: %.1fs",
                shutdown_elapsed
            )
        else:
            _logger.warning(
                "Forcefully terminating remaining workers after timeout"
            )
            self._worker_manager.terminate_all(graceful=False)
            _logger.info(
                "Forceful shutdown complete, total time: %.1fs",
                shutdown_elapsed
            )

        with self._lock:
            self._state = ServerState.STOPPED

        self._shutdown_complete.set()

        return

    def _log_shutdown_progress(self) -> None:
        """
            Log a summary of worker status during shutdown.

            Queries the worker manager for current worker status and
            logs the counts of active, idle, and shutting-down workers.
        """
        worker_status = self._worker_manager.get_worker_status()

        active_count = 0
        idle_count = 0
        shutting_down_count = 0

        for status in worker_status.values():
            state_value = status.state.value
            if state_value == "active":
                active_count += 1
            elif state_value == "idle":
                idle_count += 1
            elif state_value == "shutting_down":
                shutting_down_count += 1

        _logger.info(
            "Worker status: %d active, %d idle, %d shutting down",
            active_count,
            idle_count,
            shutting_down_count
        )

        return

    def _wait_for_inflight_requests(self, timeout: float) -> bool:
        """
            Wait for in-flight requests to complete.

            Polls the worker manager for active workers that are still
            processing requests. Waits up to the specified timeout for
            all workers to become idle.

            :param timeout: Maximum time in seconds to wait for requests
                            to complete.

            :returns: True if all in-flight requests completed within the
                      timeout, False if the timeout was exceeded.
        """
        start_time = time.time()

        while True:
            elapsed = time.time() - start_time

            if elapsed >= timeout:
                inflight_count = self._get_inflight_count()
                _logger.warning(
                    "Graceful timeout (%.1fs) exceeded with %d request(s) still pending",
                    timeout,
                    inflight_count
                )
                return False

            active_count = self._get_inflight_count()

            if active_count == 0:
                _logger.info("All in-flight requests completed")
                return True

            _logger.info(
                "Waiting for %d in-flight request(s) to complete (%.1fs / %.1fs)",
                active_count,
                elapsed,
                timeout
            )

            self._log_shutdown_progress()

            time.sleep(0.5)

    def _get_inflight_count(self) -> int:
        """
            Get the number of workers currently processing requests.

            Checks the worker manager's request start times to determine
            how many workers have active in-flight requests.

            :returns: The number of workers with active requests.
        """
        count = 0

        with self._worker_manager._lock:
            for start_time in self._worker_manager._request_start_times.values():
                if start_time is not None:
                    count += 1

        return count

