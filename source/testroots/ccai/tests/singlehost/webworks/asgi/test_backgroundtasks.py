"""
    Tests for the BackgroundTasks class.
    
    This module contains unit tests for the ASGI background tasks functionality.
"""

import asyncio
import logging
from typing import Any, List

from ccai.webworks.asgi.backgroundtasks import BackgroundTasks


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


# =============================================================================
# Unit Tests for BackgroundTasks - Construction
# =============================================================================

def test_backgroundtasks_construction_with_defaults():
    """
        Test that BackgroundTasks can be constructed with default values.
    """
    tasks = BackgroundTasks()
    
    if tasks.task_count != 0:
        errmsg = f"Expected task_count=0, got {tasks.task_count}"
        raise AssertionError(errmsg)
    
    if tasks.has_tasks is not False:
        errmsg = f"Expected has_tasks=False, got {tasks.has_tasks}"
        raise AssertionError(errmsg)
    
    return


def test_backgroundtasks_construction_with_custom_logger():
    """
        Test that BackgroundTasks can be constructed with a custom logger.
    """
    mock_logger = MockLogger()
    tasks = BackgroundTasks(logger=mock_logger)
    
    if tasks.task_count != 0:
        errmsg = f"Expected task_count=0, got {tasks.task_count}"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for BackgroundTasks - Task Scheduling (15.1)
# =============================================================================

def test_backgroundtasks_add_task_increments_count():
    """
        Test that add_task increments the task count.
    """
    tasks = BackgroundTasks()
    
    async def my_task():
        pass
    
    tasks.add_task(my_task)
    
    if tasks.task_count != 1:
        errmsg = f"Expected task_count=1, got {tasks.task_count}"
        raise AssertionError(errmsg)
    
    if tasks.has_tasks is not True:
        errmsg = f"Expected has_tasks=True, got {tasks.has_tasks}"
        raise AssertionError(errmsg)
    
    return


def test_backgroundtasks_add_multiple_tasks():
    """
        Test that multiple tasks can be added.
    """
    tasks = BackgroundTasks()
    
    async def task_a():
        pass
    
    async def task_b():
        pass
    
    async def task_c():
        pass
    
    tasks.add_task(task_a)
    tasks.add_task(task_b)
    tasks.add_task(task_c)
    
    if tasks.task_count != 3:
        errmsg = f"Expected task_count=3, got {tasks.task_count}"
        raise AssertionError(errmsg)
    
    return


def test_backgroundtasks_add_task_with_args():
    """
        Test that add_task supports positional arguments.
    """
    tasks = BackgroundTasks()
    
    received_args = []
    
    async def my_task(a, b, c):
        received_args.extend([a, b, c])
    
    tasks.add_task(my_task, 1, 2, 3)
    
    asyncio.get_event_loop().run_until_complete(tasks.run())
    
    if received_args != [1, 2, 3]:
        errmsg = f"Expected args [1, 2, 3], got {received_args}"
        raise AssertionError(errmsg)
    
    return


def test_backgroundtasks_add_task_with_kwargs():
    """
        Test that add_task supports keyword arguments.
    """
    tasks = BackgroundTasks()
    
    received_kwargs = {}
    
    async def my_task(name=None, value=None):
        received_kwargs["name"] = name
        received_kwargs["value"] = value
    
    tasks.add_task(my_task, name="test", value=42)
    
    asyncio.get_event_loop().run_until_complete(tasks.run())
    
    if received_kwargs.get("name") != "test":
        errmsg = f"Expected name='test', got {received_kwargs.get('name')}"
        raise AssertionError(errmsg)
    
    if received_kwargs.get("value") != 42:
        errmsg = f"Expected value=42, got {received_kwargs.get('value')}"
        raise AssertionError(errmsg)
    
    return


def test_backgroundtasks_add_task_with_mixed_args_kwargs():
    """
        Test that add_task supports both positional and keyword arguments.
    """
    tasks = BackgroundTasks()
    
    received_data = {}
    
    async def my_task(a, b, c=None, d=None):
        received_data["a"] = a
        received_data["b"] = b
        received_data["c"] = c
        received_data["d"] = d
    
    tasks.add_task(my_task, "arg1", "arg2", c="kwarg1", d="kwarg2")
    
    asyncio.get_event_loop().run_until_complete(tasks.run())
    
    if received_data.get("a") != "arg1":
        errmsg = f"Expected a='arg1', got {received_data.get('a')}"
        raise AssertionError(errmsg)
    
    if received_data.get("b") != "arg2":
        errmsg = f"Expected b='arg2', got {received_data.get('b')}"
        raise AssertionError(errmsg)
    
    if received_data.get("c") != "kwarg1":
        errmsg = f"Expected c='kwarg1', got {received_data.get('c')}"
        raise AssertionError(errmsg)
    
    if received_data.get("d") != "kwarg2":
        errmsg = f"Expected d='kwarg2', got {received_data.get('d')}"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for BackgroundTasks - Task Execution (15.2)
# =============================================================================

def test_backgroundtasks_run_executes_tasks():
    """
        Test that run() executes all scheduled tasks.
    """
    tasks = BackgroundTasks()
    
    executed = []
    
    async def task_a():
        executed.append("a")
    
    async def task_b():
        executed.append("b")
    
    tasks.add_task(task_a)
    tasks.add_task(task_b)
    
    asyncio.get_event_loop().run_until_complete(tasks.run())
    
    if "a" not in executed:
        errmsg = "Expected task_a to be executed"
        raise AssertionError(errmsg)
    
    if "b" not in executed:
        errmsg = "Expected task_b to be executed"
        raise AssertionError(errmsg)
    
    return


def test_backgroundtasks_run_executes_in_order():
    """
        Test that run() executes tasks in the order they were added.
    """
    tasks = BackgroundTasks()
    
    execution_order: List[str] = []
    
    async def task_a():
        execution_order.append("a")
    
    async def task_b():
        execution_order.append("b")
    
    async def task_c():
        execution_order.append("c")
    
    tasks.add_task(task_a)
    tasks.add_task(task_b)
    tasks.add_task(task_c)
    
    asyncio.get_event_loop().run_until_complete(tasks.run())
    
    expected_order = ["a", "b", "c"]
    if execution_order != expected_order:
        errmsg = f"Expected execution order {expected_order}, got {execution_order}"
        raise AssertionError(errmsg)
    
    return


def test_backgroundtasks_run_clears_tasks_after_execution():
    """
        Test that run() clears the task list after execution.
    """
    tasks = BackgroundTasks()
    
    async def my_task():
        pass
    
    tasks.add_task(my_task)
    tasks.add_task(my_task)
    
    if tasks.task_count != 2:
        errmsg = f"Expected task_count=2 before run, got {tasks.task_count}"
        raise AssertionError(errmsg)
    
    asyncio.get_event_loop().run_until_complete(tasks.run())
    
    if tasks.task_count != 0:
        errmsg = f"Expected task_count=0 after run, got {tasks.task_count}"
        raise AssertionError(errmsg)
    
    return


def test_backgroundtasks_run_executes_in_same_event_loop():
    """
        Test that run() executes tasks in the same event loop.
    """
    tasks = BackgroundTasks()
    
    captured_loop = [None]
    
    async def capture_loop_task():
        captured_loop[0] = asyncio.get_running_loop()
    
    tasks.add_task(capture_loop_task)
    
    loop = asyncio.get_event_loop()
    loop.run_until_complete(tasks.run())
    
    if captured_loop[0] is None:
        errmsg = "Expected task to capture the event loop"
        raise AssertionError(errmsg)
    
    if captured_loop[0] is not loop:
        errmsg = "Expected task to run in the same event loop"
        raise AssertionError(errmsg)
    
    return


def test_backgroundtasks_run_with_no_tasks():
    """
        Test that run() handles empty task list gracefully.
    """
    tasks = BackgroundTasks()
    
    # Should not raise any exception
    asyncio.get_event_loop().run_until_complete(tasks.run())
    
    if tasks.task_count != 0:
        errmsg = f"Expected task_count=0, got {tasks.task_count}"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for BackgroundTasks - Non-blocking Response (15.3)
# =============================================================================

def test_backgroundtasks_does_not_block_before_run():
    """
        Test that adding tasks does not block execution.
    """
    tasks = BackgroundTasks()
    
    async def slow_task():
        await asyncio.sleep(10)  # Would block if executed immediately
    
    # Adding tasks should be instant
    tasks.add_task(slow_task)
    tasks.add_task(slow_task)
    tasks.add_task(slow_task)
    
    # If we get here, tasks were not executed during add_task
    if tasks.task_count != 3:
        errmsg = f"Expected task_count=3, got {tasks.task_count}"
        raise AssertionError(errmsg)
    
    # Clear tasks to avoid actually running them
    tasks.clear()
    
    return


# =============================================================================
# Unit Tests for BackgroundTasks - Error Handling (15.4)
# =============================================================================

def test_backgroundtasks_logs_errors():
    """
        Test that run() logs errors from failed tasks.
    """
    mock_logger = MockLogger()
    tasks = BackgroundTasks(logger=mock_logger)
    
    async def failing_task():
        raise ValueError("Task failed")
    
    tasks.add_task(failing_task)
    
    asyncio.get_event_loop().run_until_complete(tasks.run())
    
    if len(mock_logger.error_messages) != 1:
        errmsg = f"Expected 1 error message, got {len(mock_logger.error_messages)}"
        raise AssertionError(errmsg)
    
    error_msg = mock_logger.error_messages[0]
    if "failing_task" not in error_msg:
        errmsg = f"Expected task name in error message, got: {error_msg}"
        raise AssertionError(errmsg)
    
    if "ValueError" not in error_msg:
        errmsg = f"Expected exception type in error message, got: {error_msg}"
        raise AssertionError(errmsg)
    
    if "Task failed" not in error_msg:
        errmsg = f"Expected exception message in error message, got: {error_msg}"
        raise AssertionError(errmsg)
    
    return


def test_backgroundtasks_continues_after_error():
    """
        Test that run() continues executing tasks after an error.
    """
    mock_logger = MockLogger()
    tasks = BackgroundTasks(logger=mock_logger)
    
    execution_order: List[str] = []
    
    async def task_a():
        execution_order.append("a")
    
    async def failing_task():
        execution_order.append("fail")
        raise ValueError("Task failed")
    
    async def task_b():
        execution_order.append("b")
    
    tasks.add_task(task_a)
    tasks.add_task(failing_task)
    tasks.add_task(task_b)
    
    asyncio.get_event_loop().run_until_complete(tasks.run())
    
    expected_order = ["a", "fail", "b"]
    if execution_order != expected_order:
        errmsg = f"Expected execution order {expected_order}, got {execution_order}"
        raise AssertionError(errmsg)
    
    return


def test_backgroundtasks_multiple_errors_all_logged():
    """
        Test that multiple errors are all logged.
    """
    mock_logger = MockLogger()
    tasks = BackgroundTasks(logger=mock_logger)
    
    async def failing_task_1():
        raise ValueError("Error 1")
    
    async def failing_task_2():
        raise RuntimeError("Error 2")
    
    async def failing_task_3():
        raise TypeError("Error 3")
    
    tasks.add_task(failing_task_1)
    tasks.add_task(failing_task_2)
    tasks.add_task(failing_task_3)
    
    asyncio.get_event_loop().run_until_complete(tasks.run())
    
    if len(mock_logger.error_messages) != 3:
        errmsg = f"Expected 3 error messages, got {len(mock_logger.error_messages)}"
        raise AssertionError(errmsg)
    
    return


def test_backgroundtasks_error_does_not_affect_response():
    """
        Test that errors in background tasks do not propagate.
    """
    tasks = BackgroundTasks()
    
    async def failing_task():
        raise ValueError("This should not propagate")
    
    tasks.add_task(failing_task)
    
    # run() should not raise an exception
    try:
        asyncio.get_event_loop().run_until_complete(tasks.run())
    except ValueError:
        errmsg = "Background task error should not propagate"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for BackgroundTasks - Task Cancellation (15.5)
# =============================================================================

def test_backgroundtasks_clear_removes_pending_tasks():
    """
        Test that clear() removes all pending tasks.
    """
    tasks = BackgroundTasks()
    
    async def my_task():
        pass
    
    tasks.add_task(my_task)
    tasks.add_task(my_task)
    tasks.add_task(my_task)
    
    if tasks.task_count != 3:
        errmsg = f"Expected task_count=3, got {tasks.task_count}"
        raise AssertionError(errmsg)
    
    tasks.clear()
    
    if tasks.task_count != 0:
        errmsg = f"Expected task_count=0 after clear, got {tasks.task_count}"
        raise AssertionError(errmsg)
    
    return


def test_backgroundtasks_cancel_all_clears_pending_tasks():
    """
        Test that cancel_all() clears pending tasks.
    """
    tasks = BackgroundTasks()
    
    async def my_task():
        pass
    
    tasks.add_task(my_task)
    tasks.add_task(my_task)
    
    asyncio.get_event_loop().run_until_complete(tasks.cancel_all())
    
    if tasks.task_count != 0:
        errmsg = f"Expected task_count=0 after cancel_all, got {tasks.task_count}"
        raise AssertionError(errmsg)
    
    return


def test_backgroundtasks_cancel_all_with_no_tasks():
    """
        Test that cancel_all() handles empty task list gracefully.
    """
    tasks = BackgroundTasks()
    
    # Should not raise any exception
    asyncio.get_event_loop().run_until_complete(tasks.cancel_all())
    
    if tasks.task_count != 0:
        errmsg = f"Expected task_count=0, got {tasks.task_count}"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for BackgroundTasks - Async Task Support
# =============================================================================

def test_backgroundtasks_supports_async_tasks():
    """
        Test that BackgroundTasks supports async task functions.
    """
    tasks = BackgroundTasks()
    
    result = []
    
    async def async_task():
        await asyncio.sleep(0.01)
        result.append("done")
    
    tasks.add_task(async_task)
    
    asyncio.get_event_loop().run_until_complete(tasks.run())
    
    if result != ["done"]:
        errmsg = f"Expected result ['done'], got {result}"
        raise AssertionError(errmsg)
    
    return


def test_backgroundtasks_supports_async_tasks_with_await():
    """
        Test that async tasks can await other coroutines.
    """
    tasks = BackgroundTasks()
    
    result = []
    
    async def helper_coroutine():
        await asyncio.sleep(0.01)
        return "helper_result"
    
    async def main_task():
        value = await helper_coroutine()
        result.append(value)
    
    tasks.add_task(main_task)
    
    asyncio.get_event_loop().run_until_complete(tasks.run())
    
    if result != ["helper_result"]:
        errmsg = f"Expected result ['helper_result'], got {result}"
        raise AssertionError(errmsg)
    
    return

