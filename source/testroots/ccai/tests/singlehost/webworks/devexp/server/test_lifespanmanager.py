"""
    Tests for the ASGI lifespan protocol manager.

    This module contains unit tests for the :class:`LifespanManager`
    class, covering startup success, startup failure, shutdown success,
    shutdown failure, and applications that do not support lifespan.
"""

import asyncio

from typing import Any, Dict

from ccai.webworks.devexp.server.lifespanmanager import LifespanManager


# =============================================================================
# Test Helper Applications
# =============================================================================

async def _app_startup_complete(
    scope: Dict[str, Any],
    receive: Any,
    send: Any,
) -> None:
    """
        A test ASGI application that responds with
        ``lifespan.startup.complete`` and ``lifespan.shutdown.complete``.
    """
    while True:
        message = await receive()
        message_type = message.get("type", "")

        if message_type == "lifespan.startup":
            await send({"type": "lifespan.startup.complete"})
        elif message_type == "lifespan.shutdown":
            await send({"type": "lifespan.shutdown.complete"})
            return

    return


async def _app_startup_failed(
    scope: Dict[str, Any],
    receive: Any,
    send: Any,
) -> None:
    """
        A test ASGI application that responds with
        ``lifespan.startup.failed`` with an error message.
    """
    while True:
        message = await receive()
        message_type = message.get("type", "")

        if message_type == "lifespan.startup":
            await send({
                "type": "lifespan.startup.failed",
                "message": "Database connection failed",
            })
            return

    return



async def _app_raises_on_lifespan(
    scope: Dict[str, Any],
    receive: Any,
    send: Any,
) -> None:
    """
        A test ASGI application that raises an exception when it
        receives a lifespan scope, simulating an app that does not
        support the lifespan protocol.
    """
    if scope.get("type") == "lifespan":
        raise RuntimeError("Lifespan not supported")

    return


async def _app_shutdown_complete(
    scope: Dict[str, Any],
    receive: Any,
    send: Any,
) -> None:
    """
        A test ASGI application that responds with
        ``lifespan.startup.complete`` and ``lifespan.shutdown.complete``.
    """
    while True:
        message = await receive()
        message_type = message.get("type", "")

        if message_type == "lifespan.startup":
            await send({"type": "lifespan.startup.complete"})
        elif message_type == "lifespan.shutdown":
            await send({"type": "lifespan.shutdown.complete"})
            return

    return


async def _app_shutdown_failed(
    scope: Dict[str, Any],
    receive: Any,
    send: Any,
) -> None:
    """
        A test ASGI application that responds with
        ``lifespan.startup.complete`` on startup and
        ``lifespan.shutdown.failed`` on shutdown.
    """
    while True:
        message = await receive()
        message_type = message.get("type", "")

        if message_type == "lifespan.startup":
            await send({"type": "lifespan.startup.complete"})
        elif message_type == "lifespan.shutdown":
            await send({
                "type": "lifespan.shutdown.failed",
                "message": "Cleanup error occurred",
            })
            return

    return


# =============================================================================
# Async Test Runner Helper
# =============================================================================

def _run_async(coro):
    """
        Run an async coroutine synchronously using a new event loop.

        :param coro: The coroutine to run.

        :returns: The result of the coroutine.
    """
    loop = asyncio.new_event_loop()
    try:
        result = loop.run_until_complete(coro)
    finally:
        loop.close()

    return result


# =============================================================================
# Unit Tests
# =============================================================================

def test_startup_complete():
    """
        Test that an app sending ``lifespan.startup.complete`` results
        in a successful startup.

        Validates: Requirements 5.1
    """

    async def _run():
        manager = LifespanManager(app=_app_startup_complete)
        await manager.startup()

        if manager.startup_complete is not True:
            errmsg = "Expected startup_complete to be True, got {}".format(
                manager.startup_complete,
            )
            raise AssertionError(errmsg)

        if manager.startup_failed is not False:
            errmsg = "Expected startup_failed to be False, got {}".format(
                manager.startup_failed,
            )
            raise AssertionError(errmsg)

        if manager.failure_message is not None:
            errmsg = "Expected failure_message to be None, got {!r}".format(
                manager.failure_message,
            )
            raise AssertionError(errmsg)

        await manager.shutdown()
        return

    _run_async(_run())
    return


def test_startup_failed():
    """
        Test that an app sending ``lifespan.startup.failed`` results
        in a failed startup with the correct error message.

        Validates: Requirements 5.2
    """

    async def _run():
        manager = LifespanManager(app=_app_startup_failed)
        await manager.startup()

        if manager.startup_complete is not False:
            errmsg = "Expected startup_complete to be False, got {}".format(
                manager.startup_complete,
            )
            raise AssertionError(errmsg)

        if manager.startup_failed is not True:
            errmsg = "Expected startup_failed to be True, got {}".format(
                manager.startup_failed,
            )
            raise AssertionError(errmsg)

        expected_message = "Database connection failed"
        if manager.failure_message != expected_message:
            errmsg = "Expected failure_message to be {!r}, got {!r}".format(
                expected_message,
                manager.failure_message,
            )
            raise AssertionError(errmsg)

        return

    _run_async(_run())
    return


def test_app_raises_on_lifespan_proceeds_as_successful():
    """
        Test that an app that raises an exception on the lifespan scope
        is treated as a successful startup.

        Validates: Requirements 5.4
    """

    async def _run():
        manager = LifespanManager(app=_app_raises_on_lifespan)

        # Give the event loop a moment to process the app task
        await manager.startup()

        if manager.startup_complete is not True:
            errmsg = "Expected startup_complete to be True, got {}".format(
                manager.startup_complete,
            )
            raise AssertionError(errmsg)

        if manager.startup_failed is not False:
            errmsg = "Expected startup_failed to be False, got {}".format(
                manager.startup_failed,
            )
            raise AssertionError(errmsg)

        return

    _run_async(_run())
    return


def test_shutdown_complete():
    """
        Test that an app sending ``lifespan.shutdown.complete`` results
        in a successful shutdown.

        Validates: Requirements 5.3
    """

    async def _run():
        manager = LifespanManager(app=_app_shutdown_complete)
        await manager.startup()

        if manager.startup_complete is not True:
            errmsg = "Expected startup_complete to be True, got {}".format(
                manager.startup_complete,
            )
            raise AssertionError(errmsg)

        await manager.shutdown()

        if manager._shutdown_complete is not True:
            errmsg = "Expected shutdown_complete to be True, got {}".format(
                manager._shutdown_complete,
            )
            raise AssertionError(errmsg)

        if manager._shutdown_failed is not False:
            errmsg = "Expected shutdown_failed to be False, got {}".format(
                manager._shutdown_failed,
            )
            raise AssertionError(errmsg)

        return

    _run_async(_run())
    return


def test_shutdown_failed():
    """
        Test that an app sending ``lifespan.shutdown.failed`` results
        in a failed shutdown with the correct error message.

        Validates: Requirements 5.3
    """

    async def _run():
        manager = LifespanManager(app=_app_shutdown_failed)
        await manager.startup()

        if manager.startup_complete is not True:
            errmsg = "Expected startup_complete to be True, got {}".format(
                manager.startup_complete,
            )
            raise AssertionError(errmsg)

        await manager.shutdown()

        if manager._shutdown_failed is not True:
            errmsg = "Expected shutdown_failed to be True, got {}".format(
                manager._shutdown_failed,
            )
            raise AssertionError(errmsg)

        expected_message = "Cleanup error occurred"
        if manager.failure_message != expected_message:
            errmsg = "Expected failure_message to be {!r}, got {!r}".format(
                expected_message,
                manager.failure_message,
            )
            raise AssertionError(errmsg)

        return

    _run_async(_run())
    return
