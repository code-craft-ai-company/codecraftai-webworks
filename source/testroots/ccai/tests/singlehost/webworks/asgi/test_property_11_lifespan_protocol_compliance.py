"""
    Property-Based Tests for Lifespan Protocol Compliance (Property 11).

    Property 11: Lifespan Protocol Compliance
    For any lifespan scope, the LifespanHandler SHALL correctly receive
    "lifespan.startup" and "lifespan.shutdown" events, and SHALL respond
    with the appropriate completion or failure messages according to the
    ASGI lifespan protocol.

    Validates: Requirements 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7
"""

import asyncio
import random
import string
from typing import Any, Awaitable, Callable, Dict, List, Optional


from ccai.webworks.asgi.lifespanhandler import LifespanHandler
from ccai.webworks.asgi.constants import (
    SCOPE_TYPE_LIFESPAN,
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
        # Block indefinitely if no more messages (simulates server waiting)
        await asyncio.sleep(10)
        return {}

    return receive


def make_successful_handler():
    """Create an async handler that succeeds."""

    async def handler():
        pass

    return handler


def make_failing_handler_with_message(error_message: str):
    """Create an async handler that raises RuntimeError with the given message."""

    async def handler():
        raise RuntimeError(error_message)

    return handler


# =============================================================================
# Random Generators
# =============================================================================

def generate_handler_count() -> int:
    """Generate a random number of handlers between 0 and 8."""
    return random.randint(0, 8)


def generate_error_message() -> str:
    """Generate a random error message string."""
    length = random.randint(3, 30)
    return "".join(random.choices(string.ascii_letters + string.digits + " ", k=length))


# =============================================================================
# Property-Based Tests
# =============================================================================

# Feature: asgi-layer, Property 11: Lifespan Protocol Compliance
# *For any* lifespan scope, the LifespanHandler SHALL correctly handle
# "lifespan.startup" and "lifespan.shutdown" events per the ASGI protocol.
# **Validates: Requirements 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7**


def test_property_11_handle_receives_lifespan_scope_type():
    """
        Property 11: Lifespan Scope Type Handling

        For any lifespan scope dictionary with type "lifespan", the
        LifespanHandler.handle() SHALL process the scope and respond
        to startup and shutdown events.

        **Validates: Requirement 8.1**
    """
    loop = asyncio.get_event_loop()

    for iteration in range(50):
        logger = MockLogger()
        handler = LifespanHandler(logger=logger)

        # Register a handler so startup does something
        handler.on_startup(make_successful_handler())
        handler.on_shutdown(make_successful_handler())

        scope = {"type": SCOPE_TYPE_LIFESPAN}
        receive = create_lifespan_receive([
            {"type": MESSAGE_LIFESPAN_STARTUP},
            {"type": MESSAGE_LIFESPAN_SHUTDOWN},
        ])
        send = MockSend()

        loop.run_until_complete(handler.handle(scope, receive, send))

        # Property: handle() must complete without error for lifespan scope
        sent_types = [m.get("type") for m in send.messages]
        if len(sent_types) < 2:
            errmsg = (
                f"Iteration {iteration}: expected at least 2 sent messages "
                f"for lifespan scope, got {len(sent_types)}: {sent_types}"
            )
            raise AssertionError(errmsg)

    return


def test_property_11_startup_event_received_and_acknowledged():
    """
        Property 11: Startup Event Reception

        For any number of registered startup handlers that all succeed,
        the LifespanHandler SHALL receive the "lifespan.startup" event
        and respond with "lifespan.startup.complete".

        **Validates: Requirements 8.2, 8.3**
    """
    loop = asyncio.get_event_loop()

    for iteration in range(100):
        handler_count = generate_handler_count()
        logger = MockLogger()
        handler = LifespanHandler(logger=logger)

        for _ in range(handler_count):
            handler.on_startup(make_successful_handler())

        receive = create_lifespan_receive([
            {"type": MESSAGE_LIFESPAN_STARTUP},
            {"type": MESSAGE_LIFESPAN_SHUTDOWN},
        ])
        send = MockSend()

        loop.run_until_complete(
            handler.handle({"type": SCOPE_TYPE_LIFESPAN}, receive, send)
        )

        sent_types = [m.get("type") for m in send.messages]

        # Property: "lifespan.startup.complete" must be the first sent message
        if len(sent_types) == 0 or sent_types[0] != MESSAGE_LIFESPAN_STARTUP_COMPLETE:
            errmsg = (
                f"Iteration {iteration}: expected first sent message to be "
                f"'{MESSAGE_LIFESPAN_STARTUP_COMPLETE}', got {sent_types}"
            )
            raise AssertionError(errmsg)

        # Property: startup_complete must be True
        if not handler.startup_complete:
            errmsg = (
                f"Iteration {iteration}: startup_complete is False after "
                f"successful startup with {handler_count} handlers"
            )
            raise AssertionError(errmsg)

    return


def test_property_11_startup_failure_sends_failed_with_message():
    """
        Property 11: Startup Failure Signaling

        For any startup handler that raises an exception, the LifespanHandler
        SHALL send "lifespan.startup.failed" with a "message" key containing
        the error description.

        **Validates: Requirement 8.4**
    """
    loop = asyncio.get_event_loop()

    for iteration in range(100):
        error_message = generate_error_message()
        logger = MockLogger()
        handler = LifespanHandler(logger=logger)

        handler.on_startup(make_failing_handler_with_message(error_message))

        receive = create_lifespan_receive([
            {"type": MESSAGE_LIFESPAN_STARTUP},
            {"type": MESSAGE_LIFESPAN_SHUTDOWN},
        ])
        send = MockSend()

        loop.run_until_complete(
            handler.handle({"type": SCOPE_TYPE_LIFESPAN}, receive, send)
        )

        # Find the startup.failed message
        failed_messages = [
            m for m in send.messages
            if m.get("type") == MESSAGE_LIFESPAN_STARTUP_FAILED
        ]

        # Property: exactly one startup.failed message must be sent
        if len(failed_messages) != 1:
            errmsg = (
                f"Iteration {iteration}: expected exactly 1 "
                f"'{MESSAGE_LIFESPAN_STARTUP_FAILED}' message, "
                f"got {len(failed_messages)}"
            )
            raise AssertionError(errmsg)

        # Property: the failed message must contain a "message" key
        failed_msg = failed_messages[0]
        if "message" not in failed_msg:
            errmsg = (
                f"Iteration {iteration}: '{MESSAGE_LIFESPAN_STARTUP_FAILED}' "
                f"message missing 'message' key: {failed_msg}"
            )
            raise AssertionError(errmsg)

        # Property: the message must contain the error description
        msg_text = failed_msg["message"]
        if error_message not in msg_text:
            errmsg = (
                f"Iteration {iteration}: expected error message to contain "
                f"'{error_message}', got '{msg_text}'"
            )
            raise AssertionError(errmsg)

        # Property: startup_failed must be True
        if not handler.startup_failed:
            errmsg = (
                f"Iteration {iteration}: startup_failed is False after "
                f"startup failure"
            )
            raise AssertionError(errmsg)

        # Property: no startup.complete should have been sent
        complete_messages = [
            m for m in send.messages
            if m.get("type") == MESSAGE_LIFESPAN_STARTUP_COMPLETE
        ]
        if len(complete_messages) != 0:
            errmsg = (
                f"Iteration {iteration}: unexpected "
                f"'{MESSAGE_LIFESPAN_STARTUP_COMPLETE}' sent after startup failure"
            )
            raise AssertionError(errmsg)

    return


def test_property_11_shutdown_event_received_and_acknowledged():
    """
        Property 11: Shutdown Event Reception

        For any number of registered shutdown handlers that all succeed,
        the LifespanHandler SHALL receive the "lifespan.shutdown" event
        and respond with "lifespan.shutdown.complete".

        **Validates: Requirements 8.5, 8.6**
    """
    loop = asyncio.get_event_loop()

    for iteration in range(100):
        handler_count = generate_handler_count()
        logger = MockLogger()
        handler = LifespanHandler(logger=logger)

        for _ in range(handler_count):
            handler.on_shutdown(make_successful_handler())

        # Also register a startup handler so startup succeeds
        handler.on_startup(make_successful_handler())

        receive = create_lifespan_receive([
            {"type": MESSAGE_LIFESPAN_STARTUP},
            {"type": MESSAGE_LIFESPAN_SHUTDOWN},
        ])
        send = MockSend()

        loop.run_until_complete(
            handler.handle({"type": SCOPE_TYPE_LIFESPAN}, receive, send)
        )

        sent_types = [m.get("type") for m in send.messages]

        # Property: "lifespan.shutdown.complete" must be present in sent messages
        if MESSAGE_LIFESPAN_SHUTDOWN_COMPLETE not in sent_types:
            errmsg = (
                f"Iteration {iteration}: expected "
                f"'{MESSAGE_LIFESPAN_SHUTDOWN_COMPLETE}' in sent messages, "
                f"got {sent_types}"
            )
            raise AssertionError(errmsg)

        # Property: shutdown.complete must come after startup.complete
        startup_idx = sent_types.index(MESSAGE_LIFESPAN_STARTUP_COMPLETE)
        shutdown_idx = sent_types.index(MESSAGE_LIFESPAN_SHUTDOWN_COMPLETE)
        if shutdown_idx <= startup_idx:
            errmsg = (
                f"Iteration {iteration}: shutdown.complete (index {shutdown_idx}) "
                f"must come after startup.complete (index {startup_idx})"
            )
            raise AssertionError(errmsg)

    return


def test_property_11_shutdown_failure_sends_failed_with_message():
    """
        Property 11: Shutdown Failure Signaling

        For any shutdown handler that raises an exception, the LifespanHandler
        SHALL send "lifespan.shutdown.failed" with a "message" key containing
        the error description.

        **Validates: Requirement 8.7**
    """
    loop = asyncio.get_event_loop()

    for iteration in range(100):
        error_message = generate_error_message()
        logger = MockLogger()
        handler = LifespanHandler(logger=logger)

        # Startup succeeds
        handler.on_startup(make_successful_handler())
        # Shutdown fails
        handler.on_shutdown(make_failing_handler_with_message(error_message))

        receive = create_lifespan_receive([
            {"type": MESSAGE_LIFESPAN_STARTUP},
            {"type": MESSAGE_LIFESPAN_SHUTDOWN},
        ])
        send = MockSend()

        loop.run_until_complete(
            handler.handle({"type": SCOPE_TYPE_LIFESPAN}, receive, send)
        )

        # Find the shutdown.failed message
        failed_messages = [
            m for m in send.messages
            if m.get("type") == MESSAGE_LIFESPAN_SHUTDOWN_FAILED
        ]

        # Property: exactly one shutdown.failed message must be sent
        if len(failed_messages) != 1:
            errmsg = (
                f"Iteration {iteration}: expected exactly 1 "
                f"'{MESSAGE_LIFESPAN_SHUTDOWN_FAILED}' message, "
                f"got {len(failed_messages)}"
            )
            raise AssertionError(errmsg)

        # Property: the failed message must contain a "message" key
        failed_msg = failed_messages[0]
        if "message" not in failed_msg:
            errmsg = (
                f"Iteration {iteration}: '{MESSAGE_LIFESPAN_SHUTDOWN_FAILED}' "
                f"message missing 'message' key: {failed_msg}"
            )
            raise AssertionError(errmsg)

        # Property: the message must contain the error description
        msg_text = failed_msg["message"]
        if error_message not in msg_text:
            errmsg = (
                f"Iteration {iteration}: expected error message to contain "
                f"'{error_message}', got '{msg_text}'"
            )
            raise AssertionError(errmsg)

        # Property: no shutdown.complete should have been sent
        complete_messages = [
            m for m in send.messages
            if m.get("type") == MESSAGE_LIFESPAN_SHUTDOWN_COMPLETE
        ]
        if len(complete_messages) != 0:
            errmsg = (
                f"Iteration {iteration}: unexpected "
                f"'{MESSAGE_LIFESPAN_SHUTDOWN_COMPLETE}' sent after shutdown failure"
            )
            raise AssertionError(errmsg)

    return


def test_property_11_full_protocol_message_sequence():
    """
        Property 11: Full Protocol Message Sequence

        For any successful lifespan lifecycle, the sent message sequence
        SHALL be exactly: "lifespan.startup.complete" followed by
        "lifespan.shutdown.complete", with no other lifespan messages.

        **Validates: Requirements 8.1, 8.2, 8.3, 8.5, 8.6**
    """
    loop = asyncio.get_event_loop()

    for iteration in range(100):
        startup_count = generate_handler_count()
        shutdown_count = generate_handler_count()
        logger = MockLogger()
        handler = LifespanHandler(logger=logger)

        for _ in range(startup_count):
            handler.on_startup(make_successful_handler())
        for _ in range(shutdown_count):
            handler.on_shutdown(make_successful_handler())

        receive = create_lifespan_receive([
            {"type": MESSAGE_LIFESPAN_STARTUP},
            {"type": MESSAGE_LIFESPAN_SHUTDOWN},
        ])
        send = MockSend()

        loop.run_until_complete(
            handler.handle({"type": SCOPE_TYPE_LIFESPAN}, receive, send)
        )

        sent_types = [m.get("type") for m in send.messages]

        # Property: exactly two messages must be sent for a successful lifecycle
        expected_sequence = [
            MESSAGE_LIFESPAN_STARTUP_COMPLETE,
            MESSAGE_LIFESPAN_SHUTDOWN_COMPLETE,
        ]
        if sent_types != expected_sequence:
            errmsg = (
                f"Iteration {iteration}: expected message sequence "
                f"{expected_sequence}, got {sent_types} "
                f"(startup_handlers={startup_count}, shutdown_handlers={shutdown_count})"
            )
            raise AssertionError(errmsg)

    return


def test_property_11_startup_failure_still_processes_shutdown():
    """
        Property 11: Startup Failure Still Processes Shutdown

        When startup fails, the LifespanHandler SHALL still process the
        shutdown event and send the appropriate shutdown response message.

        **Validates: Requirements 8.4, 8.5, 8.6, 8.7**
    """
    loop = asyncio.get_event_loop()

    for iteration in range(100):
        error_message = generate_error_message()
        shutdown_count = generate_handler_count()
        logger = MockLogger()
        handler = LifespanHandler(logger=logger)

        # Startup will fail
        handler.on_startup(make_failing_handler_with_message(error_message))

        # Register shutdown handlers that succeed
        for _ in range(shutdown_count):
            handler.on_shutdown(make_successful_handler())

        receive = create_lifespan_receive([
            {"type": MESSAGE_LIFESPAN_STARTUP},
            {"type": MESSAGE_LIFESPAN_SHUTDOWN},
        ])
        send = MockSend()

        loop.run_until_complete(
            handler.handle({"type": SCOPE_TYPE_LIFESPAN}, receive, send)
        )

        sent_types = [m.get("type") for m in send.messages]

        # Property: startup.failed must be sent first
        if len(sent_types) == 0 or sent_types[0] != MESSAGE_LIFESPAN_STARTUP_FAILED:
            errmsg = (
                f"Iteration {iteration}: expected first message to be "
                f"'{MESSAGE_LIFESPAN_STARTUP_FAILED}', got {sent_types}"
            )
            raise AssertionError(errmsg)

        # Property: shutdown.complete must still be sent after startup failure
        if MESSAGE_LIFESPAN_SHUTDOWN_COMPLETE not in sent_types:
            errmsg = (
                f"Iteration {iteration}: expected "
                f"'{MESSAGE_LIFESPAN_SHUTDOWN_COMPLETE}' after startup failure, "
                f"got {sent_types}"
            )
            raise AssertionError(errmsg)

        # Property: the sequence must be startup.failed then shutdown.complete
        expected_sequence = [
            MESSAGE_LIFESPAN_STARTUP_FAILED,
            MESSAGE_LIFESPAN_SHUTDOWN_COMPLETE,
        ]
        if sent_types != expected_sequence:
            errmsg = (
                f"Iteration {iteration}: expected message sequence "
                f"{expected_sequence}, got {sent_types}"
            )
            raise AssertionError(errmsg)

    return

