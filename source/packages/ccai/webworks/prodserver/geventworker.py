"""
    Gevent-based worker for the production server.

    This module provides the GeventWorker class that handles HTTP requests
    using gevent greenlets for cooperative multitasking. This worker class
    requires gevent to be installed and is suitable for I/O-bound workloads
    that benefit from cooperative scheduling.
"""

import logging
import os
from typing import Any, Optional, TYPE_CHECKING

from ccai.webworks.prodserver.worker import Worker

if TYPE_CHECKING:
    from ccai.webworks.prodserver.serverconfig import ServerConfig
    from ccai.webworks.routing.request import Request
    from ccai.webworks.routing.response import Response


# Default logger for gevent worker
_logger = logging.getLogger("webworks.prodserver.geventworker")


# Gevent availability flag
_GEVENT_AVAILABLE = False

try:
    import gevent
    import gevent.pool
    _GEVENT_AVAILABLE = True
except ImportError:
    # gevent is an optional dependency; _GEVENT_AVAILABLE stays False and GeventWorker reports it when constructed.
    pass


class GeventWorker(Worker):
    """
        Gevent-based worker using greenlets for cooperative multitasking.

        Uses a gevent pool to handle requests concurrently via greenlets.
        This worker is suitable for I/O-bound workloads where cooperative
        scheduling provides better throughput than threading.

        Requires gevent to be installed. If gevent is not available,
        the worker will raise an ImportError when run() is called.
    """

    def __init__(
        self,
        worker_id: int,
        app: object,
        config: "ServerConfig"
    ):
        """
            Construct a gevent worker.

            :param worker_id: Unique identifier for this worker.
            :param app: The web application callable.
            :param config: Server configuration.
        """
        super().__init__(worker_id=worker_id, app=app, config=config)

        self._pool: Optional[Any] = None
        self._shutdown_requested: bool = False

        return

    @property
    def pool(self) -> Optional[Any]:
        """
            Get the gevent pool.

            :returns: The gevent Pool instance, or None if not started.
        """
        return self._pool

    def run(self) -> None:
        """
            Main worker loop for gevent-based request handling.

            Creates a gevent pool and marks the worker as active.
            The pool size is determined by the threads configuration
            option, which controls the number of concurrent greenlets.

            :raises ImportError: If gevent is not installed.
        """
        if not _GEVENT_AVAILABLE:
            errmsg = (
                "GeventWorker requires gevent to be installed. "
                "Install it with: pip install gevent"
            )
            raise ImportError(errmsg)

        self._pid = os.getpid()

        pool_size = self._config.threads
        self._pool = gevent.pool.Pool(size=pool_size)

        _logger.info(
            "GeventWorker %d started (pid=%d, pool_size=%d)",
            self._worker_id,
            self._pid,
            pool_size
        )

        self.mark_active()

        return

    def handle_request(self, request: "Request") -> "Response":
        """
            Handle a single request in a greenlet.

            Spawns a greenlet in the pool to process the request
            and increments the request count.

            :param request: The incoming HTTP request.

            :returns: The HTTP response from the application.
        """
        self.increment_request_count()

        if self._pool is not None:
            greenlet = self._pool.spawn(self._app, request)
            response = greenlet.get()
        else:
            response = self._app(request)

        return response

    def shutdown(self, graceful: bool = True) -> None:
        """
            Shutdown the gevent worker.

            Kills or joins the gevent pool and transitions the worker
            to the stopped state. If graceful is True, the pool waits
            for active greenlets to complete.

            :param graceful: If True, allow active greenlets to complete.
        """
        super().shutdown(graceful=graceful)

        self._shutdown_requested = True

        if self._pool is not None:
            if graceful:
                self._pool.join()
            else:
                self._pool.kill()

            self._pool = None

        self.mark_stopped()

        _logger.info(
            "GeventWorker %d stopped (pid=%d)",
            self._worker_id,
            self._pid
        )

        return
