"""
    Worker manager module for the production server.

    This module provides the WorkerManager class that manages worker
    processes including spawning, monitoring, crash recovery, request
    counting with max-requests recycling, and timeout handling.
    It implements the prefork model where all workers are spawned
    before accepting requests.
"""

import logging
import random
import threading
import time
from typing import Dict, Optional, Type, TYPE_CHECKING

from ccai.webworks.prodserver.worker import Worker
from ccai.webworks.prodserver.workerstate import WorkerState, WorkerStatus
from ccai.webworks.prodserver.syncworker import SyncWorker
from ccai.webworks.prodserver.asyncworker import AsyncWorker
from ccai.webworks.prodserver.geventworker import GeventWorker

if TYPE_CHECKING:
    from ccai.webworks.prodserver.serverconfig import ServerConfig


# Default logger for worker manager
_logger = logging.getLogger("webworks.prodserver.workermanager")


# Worker class registry mapping names to classes
WORKER_CLASSES: Dict[str, Type[Worker]] = {
    "sync": SyncWorker,
    "async": AsyncWorker,
    "gevent": GeventWorker,
}


class WorkerManager:
    """
        Manages worker processes including spawning, monitoring,
        and termination.

        Implements the prefork model where all workers are spawned
        before accepting requests. Provides crash recovery, max-requests
        recycling with jitter, and request timeout handling.
    """

    def __init__(self, config: "ServerConfig", app: object):
        """
            Construct a WorkerManager.

            :param config: Server configuration.
            :param app: The web application instance.
        """
        self._config = config
        self._app = app
        self._workers: Dict[int, Worker] = {}
        self._request_counts: Dict[int, int] = {}
        self._max_requests_limits: Dict[int, Optional[int]] = {}
        self._request_start_times: Dict[int, Optional[float]] = {}
        self._num_workers: int = config.resolve_workers()
        self._min_workers: int = 1
        self._next_worker_id: int = 0
        self._monitor_thread: Optional[threading.Thread] = None
        self._monitor_running: bool = False
        self._lock: threading.Lock = threading.Lock()

        return

    @property
    def num_workers(self) -> int:
        """
            Get the configured number of workers.

            :returns: The target worker count.
        """
        return self._num_workers

    @property
    def min_workers(self) -> int:
        """
            Get the minimum number of workers to maintain.

            :returns: The minimum worker count.
        """
        return self._min_workers

    def get_worker_count(self) -> int:
        """
            Get the number of currently active workers.

            :returns: The count of workers that are not in STOPPED state.
        """
        with self._lock:
            count = 0
            for worker in self._workers.values():
                if worker.state != WorkerState.STOPPED:
                    count += 1

        return count

    def get_workers(self) -> Dict[int, Worker]:
        """
            Get the dictionary of all managed workers.

            :returns: Dictionary mapping worker IDs to Worker instances.
        """
        return self._workers

    def get_worker_status(self) -> Dict[int, WorkerStatus]:
        """
            Get status information for all workers.

            :returns: Dictionary mapping worker IDs to WorkerStatus instances.
        """
        with self._lock:
            rtnval: Dict[int, WorkerStatus] = {}
            for worker_id, worker in self._workers.items():
                rtnval[worker_id] = worker.get_status()

        return rtnval

    def _resolve_worker_class(self) -> Type[Worker]:
        """
            Resolve the worker class from the configuration.

            :returns: The worker class to use for spawning workers.

            :raises ValueError: If the worker class name is not recognized.
        """
        class_name = self._config.worker_class

        if class_name not in WORKER_CLASSES:
            errmsg = f"Unknown worker class '{class_name}'. Available: {list(WORKER_CLASSES.keys())}"
            raise ValueError(errmsg)

        rtnval = WORKER_CLASSES[class_name]

        return rtnval

    def _calculate_max_requests(self, worker_id: int) -> Optional[int]:
        """
            Calculate the max requests limit for a worker with jitter.

            When max_requests is configured, adds a random jitter value
            in the range [-jitter, +jitter] to prevent thundering herd
            restarts.

            :param worker_id: The worker ID (used for logging).

            :returns: The max requests limit with jitter applied, or None
                      if max_requests is not configured.
        """
        max_requests = self._config.max_requests

        if max_requests is None:
            return None

        jitter = self._config.max_requests_jitter

        if jitter > 0:
            jitter_value = random.randint(-jitter, jitter)
            limit = max(1, max_requests + jitter_value)
        else:
            limit = max_requests

        return limit

    def spawn_worker(self, worker_id: Optional[int] = None) -> Worker:
        """
            Spawn a single worker.

            Creates a new worker instance using the configured worker class,
            assigns it a unique ID, initializes its request tracking, and
            starts it.

            :param worker_id: Optional specific worker ID. If None, the next
                              available ID is assigned.

            :returns: The spawned Worker instance.
        """
        worker_class = self._resolve_worker_class()

        with self._lock:
            if worker_id is None:
                worker_id = self._next_worker_id
                self._next_worker_id += 1

            worker = worker_class(
                worker_id=worker_id,
                app=self._app,
                config=self._config
            )

            self._workers[worker_id] = worker
            self._request_counts[worker_id] = 0
            self._max_requests_limits[worker_id] = self._calculate_max_requests(worker_id)
            self._request_start_times[worker_id] = None

        worker.run()

        _logger.info(
            "Spawned worker %d (class=%s)",
            worker_id,
            self._config.worker_class
        )

        return worker

    def spawn_workers(self) -> None:
        """
            Spawn all worker processes using the prefork model.

            Spawns the configured number of workers before accepting
            any requests. All workers are started sequentially.
        """
        _logger.info(
            "Spawning %d workers (prefork model)",
            self._num_workers
        )

        for _ in range(self._num_workers):
            self.spawn_worker()

        _logger.info(
            "All %d workers spawned successfully",
            self._num_workers
        )

        return

    def terminate_worker(self, worker_id: int, graceful: bool = True) -> None:
        """
            Terminate a worker.

            Shuts down the worker and removes it from the managed set.

            :param worker_id: ID of the worker to terminate.
            :param graceful: If True, allow in-flight requests to complete.
        """
        with self._lock:
            if worker_id not in self._workers:
                _logger.warning("Attempted to terminate unknown worker %d", worker_id)
                return

            worker = self._workers[worker_id]

        worker.shutdown(graceful=graceful)

        with self._lock:
            self._workers.pop(worker_id, None)
            self._request_counts.pop(worker_id, None)
            self._max_requests_limits.pop(worker_id, None)
            self._request_start_times.pop(worker_id, None)

        _logger.info(
            "Terminated worker %d (graceful=%s)",
            worker_id,
            graceful
        )

        return

    def restart_worker(self, worker_id: int) -> Worker:
        """
            Restart a worker.

            Terminates the existing worker and spawns a new one with
            a fresh worker ID.

            :param worker_id: ID of the worker to restart.

            :returns: The newly spawned Worker instance.
        """
        _logger.info("Restarting worker %d", worker_id)

        self.terminate_worker(worker_id, graceful=True)

        new_worker = self.spawn_worker()

        return new_worker

    def terminate_all(self, graceful: bool = True) -> None:
        """
            Terminate all managed workers.

            :param graceful: If True, allow in-flight requests to complete.
        """
        self.stop_monitor()

        with self._lock:
            worker_ids = list(self._workers.keys())

        for worker_id in worker_ids:
            self.terminate_worker(worker_id, graceful=graceful)

        _logger.info("All workers terminated (graceful=%s)", graceful)

        return

    def increment_request_count(self, worker_id: int) -> None:
        """
            Increment the request count for a worker.

            If max_requests is configured and the worker has exceeded
            its limit, the worker is scheduled for restart.

            :param worker_id: ID of the worker to increment.
        """
        with self._lock:
            if worker_id not in self._request_counts:
                return

            self._request_counts[worker_id] += 1
            count = self._request_counts[worker_id]
            limit = self._max_requests_limits.get(worker_id)

        if limit is not None and count >= limit:
            _logger.info(
                "Worker %d reached max requests (%d/%d), scheduling restart",
                worker_id,
                count,
                limit
            )
            self.restart_worker(worker_id)

        return

    def mark_request_start(self, worker_id: int) -> None:
        """
            Mark the start of a request for timeout tracking.

            :param worker_id: ID of the worker handling the request.
        """
        with self._lock:
            self._request_start_times[worker_id] = time.time()

        return

    def mark_request_end(self, worker_id: int) -> None:
        """
            Mark the end of a request for timeout tracking.

            :param worker_id: ID of the worker that completed the request.
        """
        with self._lock:
            self._request_start_times[worker_id] = None

        return

    def check_timeouts(self) -> None:
        """
            Check for workers that have exceeded the request timeout.

            Workers that have been processing a single request for longer
            than the configured timeout are terminated and restarted.
        """
        timeout = self._config.timeout

        if timeout <= 0:
            return

        now = time.time()
        timed_out_workers = []

        with self._lock:
            for worker_id, start_time in self._request_start_times.items():
                if start_time is not None:
                    elapsed = now - start_time
                    if elapsed > timeout:
                        timed_out_workers.append(worker_id)

        for worker_id in timed_out_workers:
            _logger.warning(
                "Worker %d exceeded request timeout (%ds), terminating",
                worker_id,
                timeout
            )
            self.restart_worker(worker_id)

        return

    def _monitor_loop(self) -> None:
        """
            Background monitoring loop for worker health.

            Runs continuously while monitoring is active, checking for
            crashed workers and restarting them. Also checks for request
            timeouts. Sleeps for 1 second between checks.
        """
        while self._monitor_running:
            try:
                self._check_worker_health()
                self.check_timeouts()
            except Exception:
                _logger.exception("Error in worker monitor loop")

            time.sleep(1.0)

        return

    def _check_worker_health(self) -> None:
        """
            Check the health of all workers and restart crashed ones.

            A worker is considered crashed if its state is STOPPED
            while the manager is still running. Crashed workers are
            restarted to maintain the configured worker count.
        """
        with self._lock:
            crashed_ids = []
            for worker_id, worker in self._workers.items():
                if worker.state == WorkerState.STOPPED:
                    crashed_ids.append(worker_id)

        for worker_id in crashed_ids:
            _logger.warning(
                "Worker %d detected as crashed, restarting",
                worker_id
            )
            self.restart_worker(worker_id)

        # Ensure minimum worker count is maintained
        active_count = self.get_worker_count()
        while active_count < self._min_workers:
            _logger.warning(
                "Active workers (%d) below minimum (%d), spawning replacement",
                active_count,
                self._min_workers
            )
            self.spawn_worker()
            active_count = self.get_worker_count()

        return

    def start_monitor(self) -> None:
        """
            Start the background worker monitoring thread.

            The monitor thread periodically checks worker health,
            restarts crashed workers, and enforces request timeouts.
        """
        if self._monitor_running:
            return

        self._monitor_running = True
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            name="worker-monitor",
            daemon=True
        )
        self._monitor_thread.start()

        _logger.info("Worker monitor started")

        return

    def stop_monitor(self) -> None:
        """
            Stop the background worker monitoring thread.
        """
        if not self._monitor_running:
            return

        self._monitor_running = False

        if self._monitor_thread is not None:
            self._monitor_thread.join(timeout=5.0)
            self._monitor_thread = None

        _logger.info("Worker monitor stopped")

        return
