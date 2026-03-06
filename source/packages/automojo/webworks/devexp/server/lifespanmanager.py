"""
    ASGI lifespan protocol manager for the development server.

    This module provides the :class:`LifespanManager` class, which
    manages ASGI lifespan startup and shutdown events against the
    application. It sends ``lifespan.startup`` and ``lifespan.shutdown``
    events and waits for the corresponding complete or failed responses.

    If the application does not implement lifespan handling and raises
    an exception, the manager catches it and proceeds as if startup
    succeeded.
"""

import asyncio
import logging

from typing import Any, Dict, Optional


logger = logging.getLogger(__name__)


# =============================================================================
# LifespanManager
# =============================================================================

class LifespanManager:
    """
        Manages ASGI lifespan protocol events for the development server.

        The manager creates a lifespan scope and calls the ASGI application
        with ``asyncio.Queue`` objects for the receive and send channels.
        It tracks whether startup completed or failed, and provides
        properties to inspect the result.

        :param app: The ASGI application callable.
    """

    def __init__(self, app: Any) -> None:
        self._app = app
        self._startup_complete: bool = False
        self._startup_failed: bool = False
        self._shutdown_complete: bool = False
        self._shutdown_failed: bool = False
        self._failure_message: Optional[str] = None
        self._receive_queue: Optional[asyncio.Queue] = None
        self._send_queue: Optional[asyncio.Queue] = None
        self._app_task: Optional[asyncio.Task] = None
        return

    @property
    def startup_complete(self) -> bool:
        """
            Whether the lifespan startup succeeded.

            :returns: True if the application responded with
                ``lifespan.startup.complete``, False otherwise.
        """
        return self._startup_complete

    @property
    def startup_failed(self) -> bool:
        """
            Whether the lifespan startup failed.

            :returns: True if the application responded with
                ``lifespan.startup.failed``, False otherwise.
        """
        return self._startup_failed

    @property
    def failure_message(self) -> Optional[str]:
        """
            The error message if startup or shutdown failed.

            :returns: The failure message string, or None if no failure
                occurred.
        """
        return self._failure_message

    async def startup(self) -> None:
        """
            Send a ``lifespan.startup`` event to the ASGI application.

            Creates a lifespan scope and invokes the application with
            ``asyncio.Queue`` objects for the receive and send channels.
            Sends the ``lifespan.startup`` event and waits for either
            ``lifespan.startup.complete`` or ``lifespan.startup.failed``.

            If the application raises an exception (indicating it does
            not support lifespan), the manager catches it and proceeds
            as if startup succeeded.
        """
        scope: Dict[str, Any] = {
            "type": "lifespan",
            "asgi": {"version": "3.0"},
        }

        self._receive_queue = asyncio.Queue()
        self._send_queue = asyncio.Queue()

        async def receive() -> Dict[str, Any]:
            """
                Receive callable for the ASGI lifespan protocol.

                :returns: The next message from the receive queue.
            """
            message = await self._receive_queue.get()
            return message

        async def send(message: Dict[str, Any]) -> None:
            """
                Send callable for the ASGI lifespan protocol.

                :param message: The ASGI message to send.
            """
            await self._send_queue.put(message)
            return

        # Start the application in a background task so we can
        # exchange messages with it via the queues.
        self._app_task = asyncio.create_task(
            self._app(scope, receive, send)
        )

        # Send the startup event to the application.
        await self._receive_queue.put({"type": "lifespan.startup"})

        # Wait for either a response on the send queue or the app
        # task to complete (which happens when the app raises).
        send_future = asyncio.ensure_future(self._send_queue.get())
        app_task = self._app_task

        done, _pending = await asyncio.wait(
            [send_future, app_task],
            return_when=asyncio.FIRST_COMPLETED,
        )

        if send_future in done:
            # The application sent a response.
            response = send_future.result()
            response_type = response.get("type", "")

            if response_type == "lifespan.startup.complete":
                self._startup_complete = True
                logger.info("ASGI lifespan startup complete.")
            elif response_type == "lifespan.startup.failed":
                self._startup_failed = True
                self._failure_message = response.get("message", "")
                logger.error(
                    "ASGI lifespan startup failed: %s",
                    self._failure_message,
                )
            else:
                logger.warning(
                    "Unexpected lifespan response type: %s",
                    response_type,
                )
        else:
            # The app task completed before sending a response.
            # This means the app raised an exception or does not
            # support lifespan. Cancel the pending send future.
            send_future.cancel()

            # Consume the exception from the app task to prevent
            # the "Task exception was never retrieved" warning.
            if app_task.done() and not app_task.cancelled():
                try:
                    app_task.exception()
                except Exception:
                    pass

            self._startup_complete = True
            logger.info(
                "ASGI application does not support lifespan protocol. "
                "Proceeding as successful."
            )

        return

    async def shutdown(self) -> None:
        """
            Send a ``lifespan.shutdown`` event to the ASGI application.

            Sends the ``lifespan.shutdown`` event and waits for either
            ``lifespan.shutdown.complete`` or ``lifespan.shutdown.failed``.
        """
        if self._receive_queue is None:
            logger.warning(
                "Cannot send lifespan shutdown: startup was not called."
            )
            return

        # If the app task already completed (e.g. it raised during
        # startup or does not support lifespan), skip shutdown.
        if self._app_task is not None and self._app_task.done():
            self._shutdown_complete = True
            logger.info(
                "ASGI application task already completed. "
                "Skipping lifespan shutdown."
            )
            return

        # Send the shutdown event to the application.
        await self._receive_queue.put({"type": "lifespan.shutdown"})

        # Wait for either a response on the send queue or the app
        # task to complete.
        send_future = asyncio.ensure_future(self._send_queue.get())
        app_task = self._app_task

        done, _pending = await asyncio.wait(
            [send_future, app_task],
            return_when=asyncio.FIRST_COMPLETED,
        )

        if send_future in done:
            response = send_future.result()
            response_type = response.get("type", "")

            if response_type == "lifespan.shutdown.complete":
                self._shutdown_complete = True
                logger.info("ASGI lifespan shutdown complete.")
            elif response_type == "lifespan.shutdown.failed":
                self._shutdown_failed = True
                self._failure_message = response.get("message", "")
                logger.error(
                    "ASGI lifespan shutdown failed: %s",
                    self._failure_message,
                )
            else:
                logger.warning(
                    "Unexpected lifespan response type: %s",
                    response_type,
                )
        else:
            # The app task completed before sending a response.
            send_future.cancel()
            self._shutdown_complete = True
            logger.info(
                "ASGI application raised during lifespan shutdown. "
                "Proceeding as complete."
            )

        # Wait for the app task to finish if it is still running.
        if self._app_task is not None and not self._app_task.done():
            try:
                await asyncio.wait_for(self._app_task, timeout=5.0)
            except asyncio.TimeoutError:
                logger.warning(
                    "ASGI lifespan app task did not finish within timeout. "
                    "Cancelling."
                )
                self._app_task.cancel()
            except Exception:
                pass

        return
