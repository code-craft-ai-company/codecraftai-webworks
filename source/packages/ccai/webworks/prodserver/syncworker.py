"""
    Synchronous worker for WSGI applications in the production server.

    This module provides the SyncWorker class that handles HTTP requests
    using a thread pool for concurrent request handling within a single
    worker process. This is the default worker class for WSGI applications.
"""

import logging
import os
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, TYPE_CHECKING

from ccai.webworks.prodserver.worker import Worker
from ccai.webworks.prodserver.workerstate import WorkerState

if TYPE_CHECKING:
    from ccai.webworks.prodserver.serverconfig import ServerConfig
    from ccai.webworks.routing.request import Request
    from ccai.webworks.routing.response import Response


# Default logger for sync worker
_logger = logging.getLogger("webworks.prodserver.syncworker")


class SyncWorker(Worker):
    """
        Synchronous worker for WSGI applications.

        Uses a thread pool for concurrent request handling within the
        worker process. Each request is dispatched to a thread from the
        pool, allowing multiple requests to be handled simultaneously
        within a single worker.
    """

    def __init__(
        self,
        worker_id: int,
        app: object,
        config: "ServerConfig"
    ):
        """
            Construct a synchronous worker.

            :param worker_id: Unique identifier for this worker.
            :param app: The WSGI application callable.
            :param config: Server configuration.
        """
        super().__init__(worker_id=worker_id, app=app, config=config)

        self._thread_pool: Optional[ThreadPoolExecutor] = None
        self._shutdown_requested: bool = False

        return

    @property
    def thread_pool(self) -> Optional[ThreadPoolExecutor]:
        """
            Get the thread pool executor.

            :returns: The ThreadPoolExecutor instance, or None if not started.
        """
        return self._thread_pool

    def run(self) -> None:
        """
            Main worker loop for synchronous request handling.

            Initializes the thread pool and marks the worker as active.
            The thread pool size is determined by the threads configuration
            option. The worker runs until shutdown is requested.
        """
        self._pid = os.getpid()

        thread_count = self._config.threads
        self._thread_pool = ThreadPoolExecutor(max_workers=thread_count)

        _logger.info(
            "SyncWorker %d started (pid=%d, threads=%d)",
            self._worker_id,
            self._pid,
            thread_count
        )

        self.mark_active()

        return

    def handle_request(self, request: "Request") -> "Response":
        """
            Handle a single request synchronously.

            Invokes the application callable with the request and
            increments the request count. If the thread pool is
            available, the request can be dispatched to a thread.

            :param request: The incoming HTTP request.

            :returns: The HTTP response from the application.
        """
        self.increment_request_count()

        response = self._app(request)

        return response

    def shutdown(self, graceful: bool = True) -> None:
        """
            Shutdown the synchronous worker.

            Shuts down the thread pool and transitions the worker to
            the stopped state. If graceful is True, the thread pool
            waits for pending tasks to complete.

            :param graceful: If True, allow pending tasks to complete.
        """
        super().shutdown(graceful=graceful)

        self._shutdown_requested = True

        if self._thread_pool is not None:
            self._thread_pool.shutdown(wait=graceful)
            self._thread_pool = None

        self.mark_stopped()

        _logger.info(
            "SyncWorker %d stopped (pid=%d)",
            self._worker_id,
            self._pid
        )

        return
