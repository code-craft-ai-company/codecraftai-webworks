"""
    Tests for the LifespanHandler class.
    
    This module contains unit tests for the ASGI lifespan handler functionality.
"""

import asyncio
from typing import Any, Dict, List

from ccai.webworks.asgi.lifespanhandler import LifespanHandler


# =============================================================================
# Test Helpers
# =============================================================================

class MockLogger:
    """
        Mock logger that captures log messages for testing.
    """
    
    def __init__(self):
        self.error_messages: List[str] = []
        self.warning_messages: List[str] = []
        self.info_messages: List[str] = []
        return
    
    def error(self, message: str) -> None:
        self.error_messages.append(message)
        return
    
    def warning(self, message: str) -> None:
        self.warning_messages.append(message)
        return
    
    def info(self, message: str) -> None:
        self.info_messages.append(message)
        return


class MockReceive:
    """
        Mock receive callable for testing lifespan events.
    """
    
    def __init__(self, messages: List[Dict[str, Any]]):
        """
            Construct a MockReceive instance.
            
            :param messages: List of messages to return in order.
        """
        self._messages = messages
        self._index = 0
        return
    
    async def __call__(self) -> Dict[str, Any]:
        """
            Return the next message.
            
            :returns: Next message dictionary.
        """
        if self._index < len(self._messages):
            message = self._messages[self._index]
            self._index += 1
            return message
        
        # Return empty dict if no more messages
        return {}


class MockSend:
    """
        Mock send callable for testing lifespan responses.
    """
    
    def __init__(self):
        """
            Construct a MockSend instance.
        """
        self.messages: List[Dict[str, Any]] = []
        return
    
    async def __call__(self, message: Dict[str, Any]) -> None:
        """
            Record a sent message.
            
            :param message: Message dictionary to record.
        """
        self.messages.append(message)
        return


# =============================================================================
# Unit Tests for LifespanHandler - Construction (17.1)
# =============================================================================

def test_lifespanhandler_construction_with_defaults():
    """
        Test that LifespanHandler can be constructed with default values.
    """
    handler = LifespanHandler()
    
    if handler.startup_handler_count != 0:
        errmsg = f"Expected startup_handler_count=0, got {handler.startup_handler_count}"
        raise AssertionError(errmsg)
    
    if handler.shutdown_handler_count != 0:
        errmsg = f"Expected shutdown_handler_count=0, got {handler.shutdown_handler_count}"
        raise AssertionError(errmsg)
    
    if handler.startup_complete is not False:
        errmsg = f"Expected startup_complete=False, got {handler.startup_complete}"
        raise AssertionError(errmsg)
    
    if handler.startup_failed is not False:
        errmsg = f"Expected startup_failed=False, got {handler.startup_failed}"
        raise AssertionError(errmsg)
    
    return


def test_lifespanhandler_construction_with_custom_logger():
    """
        Test that LifespanHandler can be constructed with a custom logger.
    """
    mock_logger = MockLogger()
    handler = LifespanHandler(logger=mock_logger)
    
    if handler.startup_handler_count != 0:
        errmsg = f"Expected startup_handler_count=0, got {handler.startup_handler_count}"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for LifespanHandler - Event Handling (17.1)
# =============================================================================

def test_lifespanhandler_handle_receives_startup_event():
    """
        Test that handle() receives and processes lifespan.startup event.
    """
    handler = LifespanHandler()
    
    messages = [
        {"type": "lifespan.startup"},
        {"type": "lifespan.shutdown"},
    ]
    receive = MockReceive(messages)
    send = MockSend()
    scope = {"type": "lifespan"}
    
    asyncio.get_event_loop().run_until_complete(
        handler.handle(scope, receive, send)
    )
    
    # Should have sent startup.complete and shutdown.complete
    if len(send.messages) != 2:
        errmsg = f"Expected 2 messages, got {len(send.messages)}"
        raise AssertionError(errmsg)
    
    if send.messages[0].get("type") != "lifespan.startup.complete":
        errmsg = f"Expected lifespan.startup.complete, got {send.messages[0].get('type')}"
        raise AssertionError(errmsg)
    
    return


def test_lifespanhandler_handle_receives_shutdown_event():
    """
        Test that handle() receives and processes lifespan.shutdown event.
    """
    handler = LifespanHandler()
    
    messages = [
        {"type": "lifespan.startup"},
        {"type": "lifespan.shutdown"},
    ]
    receive = MockReceive(messages)
    send = MockSend()
    scope = {"type": "lifespan"}
    
    asyncio.get_event_loop().run_until_complete(
        handler.handle(scope, receive, send)
    )
    
    if send.messages[1].get("type") != "lifespan.shutdown.complete":
        errmsg = f"Expected lifespan.shutdown.complete, got {send.messages[1].get('type')}"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for LifespanHandler - Startup Handling (17.2)
# =============================================================================

def test_lifespanhandler_startup_success_sends_complete():
    """
        Test that successful startup sends lifespan.startup.complete.
    """
    handler = LifespanHandler()
    
    executed = []
    
    @handler.on_startup
    async def startup_handler():
        executed.append("startup")
    
    messages = [
        {"type": "lifespan.startup"},
        {"type": "lifespan.shutdown"},
    ]
    receive = MockReceive(messages)
    send = MockSend()
    scope = {"type": "lifespan"}
    
    asyncio.get_event_loop().run_until_complete(
        handler.handle(scope, receive, send)
    )
    
    if "startup" not in executed:
        errmsg = "Expected startup handler to be executed"
        raise AssertionError(errmsg)
    
    if send.messages[0].get("type") != "lifespan.startup.complete":
        errmsg = f"Expected lifespan.startup.complete, got {send.messages[0].get('type')}"
        raise AssertionError(errmsg)
    
    if handler.startup_complete is not True:
        errmsg = f"Expected startup_complete=True, got {handler.startup_complete}"
        raise AssertionError(errmsg)
    
    return


def test_lifespanhandler_startup_failure_sends_failed():
    """
        Test that startup failure sends lifespan.startup.failed with message.
    """
    mock_logger = MockLogger()
    handler = LifespanHandler(logger=mock_logger)
    
    @handler.on_startup
    async def failing_startup():
        raise ValueError("Startup failed")
    
    messages = [
        {"type": "lifespan.startup"},
        {"type": "lifespan.shutdown"},
    ]
    receive = MockReceive(messages)
    send = MockSend()
    scope = {"type": "lifespan"}
    
    asyncio.get_event_loop().run_until_complete(
        handler.handle(scope, receive, send)
    )
    
    if send.messages[0].get("type") != "lifespan.startup.failed":
        errmsg = f"Expected lifespan.startup.failed, got {send.messages[0].get('type')}"
        raise AssertionError(errmsg)
    
    error_message = send.messages[0].get("message", "")
    if "ValueError" not in error_message:
        errmsg = f"Expected ValueError in message, got {error_message}"
        raise AssertionError(errmsg)
    
    if "Startup failed" not in error_message:
        errmsg = f"Expected 'Startup failed' in message, got {error_message}"
        raise AssertionError(errmsg)
    
    if handler.startup_failed is not True:
        errmsg = f"Expected startup_failed=True, got {handler.startup_failed}"
        raise AssertionError(errmsg)
    
    return


def test_lifespanhandler_startup_failure_logs_error():
    """
        Test that startup failure logs the error.
    """
    mock_logger = MockLogger()
    handler = LifespanHandler(logger=mock_logger)
    
    @handler.on_startup
    async def failing_startup():
        raise RuntimeError("Database connection failed")
    
    messages = [
        {"type": "lifespan.startup"},
        {"type": "lifespan.shutdown"},
    ]
    receive = MockReceive(messages)
    send = MockSend()
    scope = {"type": "lifespan"}
    
    asyncio.get_event_loop().run_until_complete(
        handler.handle(scope, receive, send)
    )
    
    if len(mock_logger.error_messages) != 1:
        errmsg = f"Expected 1 error message, got {len(mock_logger.error_messages)}"
        raise AssertionError(errmsg)
    
    error_msg = mock_logger.error_messages[0]
    if "RuntimeError" not in error_msg:
        errmsg = f"Expected RuntimeError in log, got {error_msg}"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for LifespanHandler - Shutdown Handling (17.3)
# =============================================================================

def test_lifespanhandler_shutdown_success_sends_complete():
    """
        Test that successful shutdown sends lifespan.shutdown.complete.
    """
    handler = LifespanHandler()
    
    executed = []
    
    @handler.on_shutdown
    async def shutdown_handler():
        executed.append("shutdown")
    
    messages = [
        {"type": "lifespan.startup"},
        {"type": "lifespan.shutdown"},
    ]
    receive = MockReceive(messages)
    send = MockSend()
    scope = {"type": "lifespan"}
    
    asyncio.get_event_loop().run_until_complete(
        handler.handle(scope, receive, send)
    )
    
    if "shutdown" not in executed:
        errmsg = "Expected shutdown handler to be executed"
        raise AssertionError(errmsg)
    
    if send.messages[1].get("type") != "lifespan.shutdown.complete":
        errmsg = f"Expected lifespan.shutdown.complete, got {send.messages[1].get('type')}"
        raise AssertionError(errmsg)
    
    return


def test_lifespanhandler_shutdown_failure_sends_failed():
    """
        Test that shutdown failure sends lifespan.shutdown.failed with message.
    """
    mock_logger = MockLogger()
    handler = LifespanHandler(logger=mock_logger)
    
    @handler.on_shutdown
    async def failing_shutdown():
        raise ValueError("Shutdown failed")
    
    messages = [
        {"type": "lifespan.startup"},
        {"type": "lifespan.shutdown"},
    ]
    receive = MockReceive(messages)
    send = MockSend()
    scope = {"type": "lifespan"}
    
    asyncio.get_event_loop().run_until_complete(
        handler.handle(scope, receive, send)
    )
    
    if send.messages[1].get("type") != "lifespan.shutdown.failed":
        errmsg = f"Expected lifespan.shutdown.failed, got {send.messages[1].get('type')}"
        raise AssertionError(errmsg)
    
    error_message = send.messages[1].get("message", "")
    if "ValueError" not in error_message:
        errmsg = f"Expected ValueError in message, got {error_message}"
        raise AssertionError(errmsg)
    
    return


def test_lifespanhandler_shutdown_failure_logs_error():
    """
        Test that shutdown failure logs the error.
    """
    mock_logger = MockLogger()
    handler = LifespanHandler(logger=mock_logger)
    
    @handler.on_shutdown
    async def failing_shutdown():
        raise RuntimeError("Cleanup failed")
    
    messages = [
        {"type": "lifespan.startup"},
        {"type": "lifespan.shutdown"},
    ]
    receive = MockReceive(messages)
    send = MockSend()
    scope = {"type": "lifespan"}
    
    asyncio.get_event_loop().run_until_complete(
        handler.handle(scope, receive, send)
    )
    
    if len(mock_logger.error_messages) != 1:
        errmsg = f"Expected 1 error message, got {len(mock_logger.error_messages)}"
        raise AssertionError(errmsg)
    
    error_msg = mock_logger.error_messages[0]
    if "RuntimeError" not in error_msg:
        errmsg = f"Expected RuntimeError in log, got {error_msg}"
        raise AssertionError(errmsg)
    
    return



# =============================================================================
# Unit Tests for LifespanHandler - Handler Registration (17.4)
# =============================================================================

def test_lifespanhandler_on_startup_registers_handler():
    """
        Test that on_startup() registers a startup handler.
    """
    handler = LifespanHandler()
    
    @handler.on_startup
    async def my_startup():
        pass
    
    if handler.startup_handler_count != 1:
        errmsg = f"Expected startup_handler_count=1, got {handler.startup_handler_count}"
        raise AssertionError(errmsg)
    
    return


def test_lifespanhandler_on_shutdown_registers_handler():
    """
        Test that on_shutdown() registers a shutdown handler.
    """
    handler = LifespanHandler()
    
    @handler.on_shutdown
    async def my_shutdown():
        pass
    
    if handler.shutdown_handler_count != 1:
        errmsg = f"Expected shutdown_handler_count=1, got {handler.shutdown_handler_count}"
        raise AssertionError(errmsg)
    
    return


def test_lifespanhandler_on_startup_returns_handler():
    """
        Test that on_startup() returns the handler for decorator use.
    """
    handler = LifespanHandler()
    
    async def my_startup():
        pass
    
    result = handler.on_startup(my_startup)
    
    if result is not my_startup:
        errmsg = "Expected on_startup to return the handler"
        raise AssertionError(errmsg)
    
    return


def test_lifespanhandler_on_shutdown_returns_handler():
    """
        Test that on_shutdown() returns the handler for decorator use.
    """
    handler = LifespanHandler()
    
    async def my_shutdown():
        pass
    
    result = handler.on_shutdown(my_shutdown)
    
    if result is not my_shutdown:
        errmsg = "Expected on_shutdown to return the handler"
        raise AssertionError(errmsg)
    
    return


def test_lifespanhandler_multiple_startup_handlers():
    """
        Test that multiple startup handlers can be registered.
    """
    handler = LifespanHandler()
    
    @handler.on_startup
    async def startup_a():
        pass
    
    @handler.on_startup
    async def startup_b():
        pass
    
    @handler.on_startup
    async def startup_c():
        pass
    
    if handler.startup_handler_count != 3:
        errmsg = f"Expected startup_handler_count=3, got {handler.startup_handler_count}"
        raise AssertionError(errmsg)
    
    return


def test_lifespanhandler_multiple_shutdown_handlers():
    """
        Test that multiple shutdown handlers can be registered.
    """
    handler = LifespanHandler()
    
    @handler.on_shutdown
    async def shutdown_a():
        pass
    
    @handler.on_shutdown
    async def shutdown_b():
        pass
    
    @handler.on_shutdown
    async def shutdown_c():
        pass
    
    if handler.shutdown_handler_count != 3:
        errmsg = f"Expected shutdown_handler_count=3, got {handler.shutdown_handler_count}"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for LifespanHandler - Handler Execution Ordering (17.5)
# =============================================================================

def test_lifespanhandler_startup_handlers_execute_in_order():
    """
        Test that startup handlers execute in registration order.
    """
    handler = LifespanHandler()
    
    execution_order: List[str] = []
    
    @handler.on_startup
    async def startup_a():
        execution_order.append("a")
    
    @handler.on_startup
    async def startup_b():
        execution_order.append("b")
    
    @handler.on_startup
    async def startup_c():
        execution_order.append("c")
    
    messages = [
        {"type": "lifespan.startup"},
        {"type": "lifespan.shutdown"},
    ]
    receive = MockReceive(messages)
    send = MockSend()
    scope = {"type": "lifespan"}
    
    asyncio.get_event_loop().run_until_complete(
        handler.handle(scope, receive, send)
    )
    
    expected_order = ["a", "b", "c"]
    if execution_order != expected_order:
        errmsg = f"Expected execution order {expected_order}, got {execution_order}"
        raise AssertionError(errmsg)
    
    return


def test_lifespanhandler_shutdown_handlers_execute_in_reverse_order():
    """
        Test that shutdown handlers execute in reverse registration order.
    """
    handler = LifespanHandler()
    
    execution_order: List[str] = []
    
    @handler.on_shutdown
    async def shutdown_a():
        execution_order.append("a")
    
    @handler.on_shutdown
    async def shutdown_b():
        execution_order.append("b")
    
    @handler.on_shutdown
    async def shutdown_c():
        execution_order.append("c")
    
    messages = [
        {"type": "lifespan.startup"},
        {"type": "lifespan.shutdown"},
    ]
    receive = MockReceive(messages)
    send = MockSend()
    scope = {"type": "lifespan"}
    
    asyncio.get_event_loop().run_until_complete(
        handler.handle(scope, receive, send)
    )
    
    # Shutdown handlers should execute in reverse order: c, b, a
    expected_order = ["c", "b", "a"]
    if execution_order != expected_order:
        errmsg = f"Expected execution order {expected_order}, got {execution_order}"
        raise AssertionError(errmsg)
    
    return


def test_lifespanhandler_can_accept_requests_after_startup():
    """
        Test that can_accept_requests() returns True after successful startup.
    """
    handler = LifespanHandler()
    
    @handler.on_startup
    async def startup_handler():
        pass
    
    messages = [
        {"type": "lifespan.startup"},
        {"type": "lifespan.shutdown"},
    ]
    receive = MockReceive(messages)
    send = MockSend()
    scope = {"type": "lifespan"}
    
    # Before startup
    if handler.can_accept_requests() is not False:
        errmsg = "Expected can_accept_requests=False before startup"
        raise AssertionError(errmsg)
    
    asyncio.get_event_loop().run_until_complete(
        handler.handle(scope, receive, send)
    )
    
    # After successful startup
    if handler.can_accept_requests() is not True:
        errmsg = "Expected can_accept_requests=True after startup"
        raise AssertionError(errmsg)
    
    return


def test_lifespanhandler_cannot_accept_requests_after_startup_failure():
    """
        Test that can_accept_requests() returns False after startup failure.
    """
    mock_logger = MockLogger()
    handler = LifespanHandler(logger=mock_logger)
    
    @handler.on_startup
    async def failing_startup():
        raise ValueError("Startup failed")
    
    messages = [
        {"type": "lifespan.startup"},
        {"type": "lifespan.shutdown"},
    ]
    receive = MockReceive(messages)
    send = MockSend()
    scope = {"type": "lifespan"}
    
    asyncio.get_event_loop().run_until_complete(
        handler.handle(scope, receive, send)
    )
    
    # After failed startup
    if handler.can_accept_requests() is not False:
        errmsg = "Expected can_accept_requests=False after startup failure"
        raise AssertionError(errmsg)
    
    return


def test_lifespanhandler_startup_failure_stops_at_first_error():
    """
        Test that startup stops at the first handler that fails.
    """
    mock_logger = MockLogger()
    handler = LifespanHandler(logger=mock_logger)
    
    execution_order: List[str] = []
    
    @handler.on_startup
    async def startup_a():
        execution_order.append("a")
    
    @handler.on_startup
    async def failing_startup():
        execution_order.append("fail")
        raise ValueError("Startup failed")
    
    @handler.on_startup
    async def startup_b():
        execution_order.append("b")
    
    messages = [
        {"type": "lifespan.startup"},
        {"type": "lifespan.shutdown"},
    ]
    receive = MockReceive(messages)
    send = MockSend()
    scope = {"type": "lifespan"}
    
    asyncio.get_event_loop().run_until_complete(
        handler.handle(scope, receive, send)
    )
    
    # Should stop at the failing handler, not execute startup_b
    expected_order = ["a", "fail"]
    if execution_order != expected_order:
        errmsg = f"Expected execution order {expected_order}, got {execution_order}"
        raise AssertionError(errmsg)
    
    return


def test_lifespanhandler_shutdown_failure_stops_at_first_error():
    """
        Test that shutdown stops at the first handler that fails.
    """
    mock_logger = MockLogger()
    handler = LifespanHandler(logger=mock_logger)
    
    execution_order: List[str] = []
    
    @handler.on_shutdown
    async def shutdown_a():
        execution_order.append("a")
    
    @handler.on_shutdown
    async def failing_shutdown():
        execution_order.append("fail")
        raise ValueError("Shutdown failed")
    
    @handler.on_shutdown
    async def shutdown_b():
        execution_order.append("b")
    
    messages = [
        {"type": "lifespan.startup"},
        {"type": "lifespan.shutdown"},
    ]
    receive = MockReceive(messages)
    send = MockSend()
    scope = {"type": "lifespan"}
    
    asyncio.get_event_loop().run_until_complete(
        handler.handle(scope, receive, send)
    )
    
    # Shutdown handlers execute in reverse order: b, fail, a
    # Should stop at the failing handler
    expected_order = ["b", "fail"]
    if execution_order != expected_order:
        errmsg = f"Expected execution order {expected_order}, got {execution_order}"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for LifespanHandler - Edge Cases
# =============================================================================

def test_lifespanhandler_no_handlers_succeeds():
    """
        Test that lifespan succeeds with no registered handlers.
    """
    handler = LifespanHandler()
    
    messages = [
        {"type": "lifespan.startup"},
        {"type": "lifespan.shutdown"},
    ]
    receive = MockReceive(messages)
    send = MockSend()
    scope = {"type": "lifespan"}
    
    asyncio.get_event_loop().run_until_complete(
        handler.handle(scope, receive, send)
    )
    
    if send.messages[0].get("type") != "lifespan.startup.complete":
        errmsg = f"Expected lifespan.startup.complete, got {send.messages[0].get('type')}"
        raise AssertionError(errmsg)
    
    if send.messages[1].get("type") != "lifespan.shutdown.complete":
        errmsg = f"Expected lifespan.shutdown.complete, got {send.messages[1].get('type')}"
        raise AssertionError(errmsg)
    
    return


def test_lifespanhandler_ignores_unknown_message_types():
    """
        Test that handle() ignores unknown message types.
    """
    handler = LifespanHandler()
    
    messages = [
        {"type": "unknown.message"},
        {"type": "lifespan.startup"},
        {"type": "another.unknown"},
        {"type": "lifespan.shutdown"},
    ]
    receive = MockReceive(messages)
    send = MockSend()
    scope = {"type": "lifespan"}
    
    asyncio.get_event_loop().run_until_complete(
        handler.handle(scope, receive, send)
    )
    
    # Should still process startup and shutdown correctly
    if len(send.messages) != 2:
        errmsg = f"Expected 2 messages, got {len(send.messages)}"
        raise AssertionError(errmsg)
    
    return


def test_lifespanhandler_async_handlers_with_await():
    """
        Test that async handlers can await other coroutines.
    """
    handler = LifespanHandler()
    
    result = []
    
    async def helper_coroutine():
        await asyncio.sleep(0.01)
        return "helper_result"
    
    @handler.on_startup
    async def startup_with_await():
        value = await helper_coroutine()
        result.append(value)
    
    messages = [
        {"type": "lifespan.startup"},
        {"type": "lifespan.shutdown"},
    ]
    receive = MockReceive(messages)
    send = MockSend()
    scope = {"type": "lifespan"}
    
    asyncio.get_event_loop().run_until_complete(
        handler.handle(scope, receive, send)
    )
    
    if result != ["helper_result"]:
        errmsg = f"Expected result ['helper_result'], got {result}"
        raise AssertionError(errmsg)
    
    return

