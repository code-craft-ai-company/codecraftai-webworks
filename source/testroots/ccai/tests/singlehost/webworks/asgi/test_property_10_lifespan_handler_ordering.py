"""
    Property-Based Tests for Lifespan Handler Ordering (Property 10).

    Property 10: Lifespan Handler Ordering
    For any set of registered startup and shutdown handlers, startup handlers
    SHALL execute in registration order, shutdown handlers SHALL execute in
    reverse registration order, and startup failure SHALL prevent the
    application from accepting requests.

    Validates: Requirements 8.8, 8.9, 8.10, 8.11, 8.12
"""

import asyncio
import random
from typing import Any, Awaitable, Callable, Dict, List

from ccai.webworks.asgi.lifespanhandler import LifespanHandler
from ccai.webworks.asgi.constants import (
    MESSAGE_LIFESPAN_STARTUP,
    MESSAGE_LIFESPAN_STARTUP_COMPLETE,
    MESSAGE_LIFESPAN_STARTUP_FAILED,
    MESSAGE_LIFESPAN_SHUTDOWN,
    MESSAGE_LIFESPAN_SHUTDOWN_COMPLETE,
    MESSAGE_LIFESPAN_SHUTDOWN_FAILED,
)


# =============================================================================
# Helpers
# =============================================================================

class MockLogger:
    """Mock logger that captures log messages."""

    def __init__(self):
        self.messages: List[str] = []
        return

    def error(self, message: str) -> None:
        self.messages.append(message)
        return

    def warning(self, message: str) -> None:
        return

    def info(self, message: str) -> None:
        return


class MockSend:
    """Mock send callable that captures sent messages."""

    def __init__(self):
        self.messages: List[Dict[str, Any]] = []
        return

    async def __call__(self, message: Dict[str, Any]) -> None:
        self.messages.append(message)
        return


def create_lifespan_receive(
    messages: List[Dict[str, Any]],
) -> Callable[[], Awaitable[Dict[str, Any]]]:
    """Create a receive callable that yields the given messages in order."""
    index = [0]

    async def receive() -> Dict[str, Any]:
        if index[0] < len(messages):
            msg = messages[index[0]]
            index[0] += 1
            return msg
        await asyncio.sleep(10)
        return {}

    return receive


def make_recording_handler(label: str, execution_log: List[str]):
    """Create an async handler that appends its label to the execution log."""

    async def handler():
        execution_log.append(label)

    return handler


def make_failing_handler(label: str, execution_log: List[str], error_message: str = "boom"):
    """Create an async handler that records itself then raises an exception."""

    async def handler():
        execution_log.append(label)
        raise RuntimeError(error_message)

    return handler


# =============================================================================
# Random Generators
# =============================================================================

def generate_handler_count() -> int:
    """Generate a random number of handlers between 1 and 10."""
    return random.randint(1, 10)


# =============================================================================
# Property-Based Tests
# =============================================================================

# Feature: asgi-layer, Property 10: Lifespan Handler Ordering
# *For any* set of registered startup and shutdown handlers, startup handlers
# SHALL execute in registration order, shutdown handlers SHALL execute in
# reverse registration order, and startup failure SHALL prevent the
# application from accepting requests.
# **Validates: Requirements 8.8, 8.9, 8.10, 8.11, 8.12**


def test_property_10_startup_handlers_execute_in_registration_order():
    """
        Property 10: Startup Handler Registration Order

        For any N startup handlers registered in sequence, executing the
        lifespan startup phase SHALL invoke them in the exact order they
        were registered.

        **Validates: Requirements 8.8, 8.10**
    """
    loop = asyncio.get_event_loop()

    for iteration in range(100):
        handler_count = generate_handler_count()
        execution_log: List[str] = []
        logger = MockLogger()
        handler = LifespanHandler(logger=logger)

        # Register N handlers in order
        labels = [f"startup_{i}" for i in range(handler_count)]
        for label in labels:
            handler.on_startup(make_recording_handler(label, execution_log))

        # Run startup
        send = MockSend()
        loop.run_until_complete(handler._run_startup(send))

        # Property: execution order must match registration order
        if execution_log != labels:
            errmsg = (
                f"Iteration {iteration}: startup handlers executed in wrong order. "
                f"Expected {labels}, got {execution_log}"
            )
            raise AssertionError(errmsg)

        # Property: startup.complete must be sent
        sent_types = [m.get("type") for m in send.messages]
        if MESSAGE_LIFESPAN_STARTUP_COMPLETE not in sent_types:
            errmsg = (
                f"Iteration {iteration}: expected '{MESSAGE_LIFESPAN_STARTUP_COMPLETE}' "
                f"in sent messages, got {sent_types}"
            )
            raise AssertionError(errmsg)

    return


def test_property_10_shutdown_handlers_execute_in_reverse_registration_order():
    """
        Property 10: Shutdown Handler Reverse Order

        For any N shutdown handlers registered in sequence, executing the
        lifespan shutdown phase SHALL invoke them in reverse registration
        order.

        **Validates: Requirements 8.9, 8.11**
    """
    loop = asyncio.get_event_loop()

    for iteration in range(100):
        handler_count = generate_handler_count()
        execution_log: List[str] = []
        logger = MockLogger()
        handler = LifespanHandler(logger=logger)

        # Register N handlers in order
        labels = [f"shutdown_{i}" for i in range(handler_count)]
        for label in labels:
            handler.on_shutdown(make_recording_handler(label, execution_log))

        # Run shutdown
        send = MockSend()
        loop.run_until_complete(handler._run_shutdown(send))

        # Property: execution order must be reverse of registration order
        expected = list(reversed(labels))
        if execution_log != expected:
            errmsg = (
                f"Iteration {iteration}: shutdown handlers executed in wrong order. "
                f"Expected {expected}, got {execution_log}"
            )
            raise AssertionError(errmsg)

        # Property: shutdown.complete must be sent
        sent_types = [m.get("type") for m in send.messages]
        if MESSAGE_LIFESPAN_SHUTDOWN_COMPLETE not in sent_types:
            errmsg = (
                f"Iteration {iteration}: expected '{MESSAGE_LIFESPAN_SHUTDOWN_COMPLETE}' "
                f"in sent messages, got {sent_types}"
            )
            raise AssertionError(errmsg)

    return


def test_property_10_startup_failure_prevents_accepting_requests():
    """
        Property 10: Startup Failure Prevents Request Acceptance

        For any set of startup handlers where one handler fails, the
        application SHALL signal startup failure and can_accept_requests()
        SHALL return False.

        **Validates: Requirement 8.12**
    """
    loop = asyncio.get_event_loop()

    for iteration in range(100):
        handler_count = generate_handler_count()
        # Pick a random handler index to fail at
        fail_index = random.randint(0, handler_count - 1)

        execution_log: List[str] = []
        logger = MockLogger()
        handler = LifespanHandler(logger=logger)

        labels = [f"startup_{i}" for i in range(handler_count)]
        for i, label in enumerate(labels):
            if i == fail_index:
                handler.on_startup(make_failing_handler(label, execution_log))
            else:
                handler.on_startup(make_recording_handler(label, execution_log))

        send = MockSend()
        loop.run_until_complete(handler._run_startup(send))

        # Property: can_accept_requests must be False after startup failure
        if handler.can_accept_requests():
            errmsg = (
                f"Iteration {iteration}: can_accept_requests() returned True "
                f"after startup failure at handler index {fail_index}"
            )
            raise AssertionError(errmsg)

        # Property: startup_failed must be True
        if not handler.startup_failed:
            errmsg = (
                f"Iteration {iteration}: startup_failed is False "
                f"after startup failure at handler index {fail_index}"
            )
            raise AssertionError(errmsg)

        # Property: startup.failed must be sent
        sent_types = [m.get("type") for m in send.messages]
        if MESSAGE_LIFESPAN_STARTUP_FAILED not in sent_types:
            errmsg = (
                f"Iteration {iteration}: expected '{MESSAGE_LIFESPAN_STARTUP_FAILED}' "
                f"in sent messages, got {sent_types}"
            )
            raise AssertionError(errmsg)

        # Property: only handlers up to and including the failing one should have run
        expected_executed = labels[:fail_index + 1]
        if execution_log != expected_executed:
            errmsg = (
                f"Iteration {iteration}: expected handlers {expected_executed} to run "
                f"before failure, got {execution_log}"
            )
            raise AssertionError(errmsg)

    return


def test_property_10_successful_startup_enables_accepting_requests():
    """
        Property 10: Successful Startup Enables Request Acceptance

        For any set of startup handlers that all succeed, the application
        SHALL signal startup complete and can_accept_requests() SHALL
        return True.

        **Validates: Requirements 8.10, 8.12**
    """
    loop = asyncio.get_event_loop()

    for iteration in range(100):
        handler_count = generate_handler_count()
        execution_log: List[str] = []
        logger = MockLogger()
        handler = LifespanHandler(logger=logger)

        labels = [f"startup_{i}" for i in range(handler_count)]
        for label in labels:
            handler.on_startup(make_recording_handler(label, execution_log))

        send = MockSend()
        loop.run_until_complete(handler._run_startup(send))

        # Property: can_accept_requests must be True after successful startup
        if not handler.can_accept_requests():
            errmsg = (
                f"Iteration {iteration}: can_accept_requests() returned False "
                f"after successful startup with {handler_count} handlers"
            )
            raise AssertionError(errmsg)

        # Property: all handlers must have executed
        if len(execution_log) != handler_count:
            errmsg = (
                f"Iteration {iteration}: expected {handler_count} handlers to run, "
                f"got {len(execution_log)}"
            )
            raise AssertionError(errmsg)

    return


def test_property_10_full_lifecycle_ordering():
    """
        Property 10: Full Lifecycle Startup and Shutdown Ordering

        For any set of registered startup and shutdown handlers, running
        the full lifespan lifecycle (startup then shutdown) SHALL execute
        startup handlers in registration order followed by shutdown handlers
        in reverse registration order.

        **Validates: Requirements 8.8, 8.9, 8.10, 8.11**
    """
    loop = asyncio.get_event_loop()

    for iteration in range(100):
        startup_count = generate_handler_count()
        shutdown_count = generate_handler_count()

        execution_log: List[str] = []
        logger = MockLogger()
        handler = LifespanHandler(logger=logger)

        # Register startup handlers
        startup_labels = [f"startup_{i}" for i in range(startup_count)]
        for label in startup_labels:
            handler.on_startup(make_recording_handler(label, execution_log))

        # Register shutdown handlers
        shutdown_labels = [f"shutdown_{i}" for i in range(shutdown_count)]
        for label in shutdown_labels:
            handler.on_shutdown(make_recording_handler(label, execution_log))

        # Run full lifespan via handle()
        receive = create_lifespan_receive([
            {"type": MESSAGE_LIFESPAN_STARTUP},
            {"type": MESSAGE_LIFESPAN_SHUTDOWN},
        ])
        send = MockSend()
        loop.run_until_complete(handler.handle({"type": "lifespan"}, receive, send))

        # Property: startup handlers run first in registration order,
        # then shutdown handlers in reverse registration order
        expected = startup_labels + list(reversed(shutdown_labels))
        if execution_log != expected:
            errmsg = (
                f"Iteration {iteration}: full lifecycle execution order wrong. "
                f"Expected {expected}, got {execution_log}"
            )
            raise AssertionError(errmsg)

        # Property: both startup.complete and shutdown.complete must be sent
        sent_types = [m.get("type") for m in send.messages]
        if MESSAGE_LIFESPAN_STARTUP_COMPLETE not in sent_types:
            errmsg = (
                f"Iteration {iteration}: missing '{MESSAGE_LIFESPAN_STARTUP_COMPLETE}' "
                f"in sent messages"
            )
            raise AssertionError(errmsg)
        if MESSAGE_LIFESPAN_SHUTDOWN_COMPLETE not in sent_types:
            errmsg = (
                f"Iteration {iteration}: missing '{MESSAGE_LIFESPAN_SHUTDOWN_COMPLETE}' "
                f"in sent messages"
            )
            raise AssertionError(errmsg)

    return
