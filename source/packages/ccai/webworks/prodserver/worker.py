"""
    Abstract worker base class for the production server.

    This module provides the abstract Worker base class that defines the
    interface for all worker implementations. Concrete worker classes
    such as SyncWorker, AsyncWorker, and GeventWorker extend this base
    to provide specific concurrency models.
"""

import logging
import time
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from ccai.webworks.prodserver.workerstate import WorkerState, WorkerStatus

if TYPE_CHECKING:
    from ccai.webworks.prodserver.serverconfig import ServerConfig
    from ccai.webworks.routing.request import Request
    from ccai.webworks.routing.response import Response


# Default logger for worker
_logger = logging.getLogger("webworks.prodserver.worker")


class Worker(ABC):
    """
        Abstract base class for worker implementations.

        Defines the interface that all production server workers must
        implement. Workers are responsible for accepting and handling
        HTTP requests using their specific concurrency model.

        Subclasses must implement the run() and handle_request() methods.
    """

    def __init__(
        self,
        worker_id: int,
        app: object,
        config: "ServerConfig"
    ):
        """
            Construct a worker.

            :param worker_id: Unique identifier for this worker.
            :param app: The web application instance.
            :param config: Server configuration.
        """
        self._worker_id = worker_id
        self._app = app
        self._config = config
        self._request_count = 0
        self._state: WorkerState = WorkerState.IDLE
        self._start_time: float = 0.0
        self._pid: int = 0

        return

    @property
    def worker_id(self) -> int:
        """
            Get the unique identifier for this worker.

            :returns: The worker ID.
        """
        return self._worker_id

    @property
    def state(self) -> WorkerState:
        """
            Get the current worker state.

            :returns: The current WorkerState.
        """
        return self._state

    @property
    def request_count(self) -> int:
        """
            Get the total number of requests handled by this worker.

            :returns: The request count.
        """
        return self._request_count

    @property
    def app(self) -> object:
        """
            Get the web application instance.

            :returns: The application object.
        """
        return self._app

    @property
    def config(self) -> "ServerConfig":
        """
            Get the server configuration.

            :returns: The ServerConfig instance.
        """
        return self._config

    @property
    def pid(self) -> int:
        """
            Get the process ID of this worker.

            :returns: The process ID.
        """
        return self._pid

    @property
    def start_time(self) -> float:
        """
            Get the time when this worker started.

            :returns: The start time as a Unix timestamp.
        """
        return self._start_time

    @abstractmethod
    def run(self) -> None:
        """
            Main worker loop.

            Subclasses must implement this method to define how the worker
            accepts and processes incoming requests. This method should
            run until shutdown is requested.
        """
        pass

    @abstractmethod
    def handle_request(self, request: "Request") -> "Response":
        """
            Handle a single incoming request.

            Subclasses must implement this method to define how individual
            requests are processed using their specific concurrency model.

            :param request: The incoming HTTP request.

            :returns: The HTTP response.
        """
        pass

    def shutdown(self, graceful: bool = True) -> None:
        """
            Shutdown the worker.

            Transitions the worker to SHUTTING_DOWN state. If graceful is
            True, the worker should allow in-flight requests to complete
            before stopping.

            :param graceful: If True, allow in-flight requests to complete.
        """
        _logger.info(
            "Worker %d shutting down (graceful=%s)",
            self._worker_id,
            graceful
        )

        self._state = WorkerState.SHUTTING_DOWN

        return

    def increment_request_count(self) -> None:
        """
            Increment the request count for this worker.

            Called after each request is handled to track the total
            number of requests processed by this worker.
        """
        self._request_count += 1

        return

    def mark_active(self) -> None:
        """
            Transition the worker to the ACTIVE state.

            Called when the worker begins processing requests.
        """
        self._state = WorkerState.ACTIVE
        self._start_time = time.time()

        return

    def mark_stopped(self) -> None:
        """
            Transition the worker to the STOPPED state.

            Called when the worker has fully stopped processing.
        """
        self._state = WorkerState.STOPPED

        return

    def get_status(self) -> WorkerStatus:
        """
            Get the current status of this worker.

            :returns: A WorkerStatus dataclass with current worker information.
        """
        if self._start_time > 0:
            uptime = time.time() - self._start_time
        else:
            uptime = 0.0

        rtnval = WorkerStatus(
            worker_id=self._worker_id,
            pid=self._pid,
            state=self._state,
            request_count=self._request_count,
            memory_usage=0,
            uptime=uptime,
        )

        return rtnval
