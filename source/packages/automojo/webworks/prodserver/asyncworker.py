"""
    Asynchronous worker for ASGI applications in the production server.

    This module provides the AsyncWorker class that handles HTTP requests
    using an asyncio event loop for concurrent request handling. This
    worker class is designed for ASGI applications that use async/await.
"""

import asyncio
import logging
import os
from typing import Optional, TYPE_CHECKING

from automojo.webworks.prodserver.worker import Worker
from automojo.webworks.prodserver.workerstate import WorkerState

if TYPE_CHECKING:
    from automojo.webworks.prodserver.serverconfig import ServerConfig
    from automojo.webworks.routing.request import Request
    from automojo.webworks.routing.response import Response


# Default logger for async worker
_logger = logging.getLogger("webworks.prodserver.asyncworker")


class AsyncWorker(Worker):
    """
        Asynchronous worker for ASGI applications.

        Uses an asyncio event loop for concurrent request handling.
        Each request is processed as a coroutine, allowing many
        requests to be handled concurrently within a single worker
        process without threads.
    """

    def __init__(
        self,
        worker_id: int,
        app: object,
        config: "ServerConfig"
    ):
        """
            Construct an asynchronous worker.

            :param worker_id: Unique identifier for this worker.
            :param app: The ASGI application callable.
            :param config: Server configuration.
        """
        super().__init__(worker_id=worker_id, app=app, config=config)

        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._shutdown_requested: bool = False

        return

    @property
    def loop(self) -> Optional[asyncio.AbstractEventLoop]:
        """
            Get the asyncio event loop.

            :returns: The event loop instance, or None if not started.
        """
        return self._loop

    def run(self) -> None:
        """
            Main worker loop for asynchronous request handling.

            Creates a new asyncio event loop and marks the worker as
            active. The event loop is used to process incoming requests
            as coroutines.
        """
        self._pid = os.getpid()

        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)

        _logger.info(
            "AsyncWorker %d started (pid=%d)",
            self._worker_id,
            self._pid
        )

        self.mark_active()

        return

    def handle_request(self, request: "Request") -> "Response":
        """
            Handle a single request asynchronously.

            Runs the async application callable in the event loop
            and increments the request count.

            :param request: The incoming HTTP request.

            :returns: The HTTP response from the application.
        """
        self.increment_request_count()

        if self._loop is not None and self._loop.is_running():
            future = asyncio.ensure_future(
                self._handle_async(request),
                loop=self._loop
            )
            response = future.result()
        else:
            if self._loop is None:
                self._loop = asyncio.new_event_loop()
            response = self._loop.run_until_complete(
                self._handle_async(request)
            )

        return response

    async def _handle_async(self, request: "Request") -> "Response":
        """
            Internal async handler that invokes the application.

            :param request: The incoming HTTP request.

            :returns: The HTTP response from the application.
        """
        response = await self._app(request)

        return response

    def shutdown(self, graceful: bool = True) -> None:
        """
            Shutdown the asynchronous worker.

            Closes the event loop and transitions the worker to the
            stopped state. If graceful is True, pending tasks are
            allowed to complete before the loop is closed.

            :param graceful: If True, allow pending tasks to complete.
        """
        super().shutdown(graceful=graceful)

        self._shutdown_requested = True

        if self._loop is not None:
            if graceful and self._loop.is_running():
                self._loop.call_soon_threadsafe(self._loop.stop)
            else:
                if self._loop.is_running():
                    self._loop.stop()

            if not self._loop.is_closed():
                self._loop.close()

            self._loop = None

        self.mark_stopped()

        _logger.info(
            "AsyncWorker %d stopped (pid=%d)",
            self._worker_id,
            self._pid
        )

        return
