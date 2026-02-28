"""
    Property-Based Tests for Background Task Execution Order (Property 9).

    Property 9: Background Task Execution Order
    For any sequence of background tasks added to a request, tasks SHALL
    execute in the order they were added, after the response is sent, and
    exceptions in one task SHALL NOT prevent execution of subsequent tasks.

    Validates: Requirements 7.1, 7.3, 7.4, 7.5, 7.6
"""

import asyncio
import random
from typing import Any, Dict, List, Optional

from automojo.webworks.asgi.backgroundtasks import BackgroundTasks


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


def make_recording_task(label: str, execution_log: List[str]):
    """Create an async task that appends its label to the execution log."""

    async def task():
        execution_log.append(label)

    return task


def make_failing_task(label: str, execution_log: List[str], error_message: str = "boom"):
    """Create an async task that records itself then raises an exception."""

    async def task():
        execution_log.append(label)
        raise RuntimeError(error_message)

    return task


def make_recording_task_with_args(label: str, execution_log: List[str]):
    """Create an async task that records its label and received arguments."""

    async def task(*args, **kwargs):
        execution_log.append((label, args, tuple(sorted(kwargs.items()))))

    return task



# =============================================================================
# Random Generators
# =============================================================================

def generate_task_count() -> int:
    """Generate a random number of tasks between 1 and 15."""
    return random.randint(1, 15)


def generate_failure_indices(task_count: int) -> List[int]:
    """Generate a random subset of indices that should fail."""
    failure_count = random.randint(0, task_count)
    return sorted(random.sample(range(task_count), failure_count))


# =============================================================================
# Property-Based Tests
# =============================================================================

# Feature: asgi-layer, Property 9: Background Task Execution Order
# *For any* sequence of background tasks added to a request, tasks SHALL
# execute in the order they were added, after the response is sent, and
# exceptions in one task SHALL NOT prevent execution of subsequent tasks.
# **Validates: Requirements 7.1, 7.3, 7.4, 7.5, 7.6**


def test_property_9_tasks_execute_in_addition_order():
    """
        Property 9: Task Execution Order

        For any N background tasks added in sequence, executing run() SHALL
        invoke them in the exact order they were added.

        **Validates: Requirements 7.1, 7.4, 7.5**
    """
    loop = asyncio.get_event_loop()

    for iteration in range(100):
        task_count = generate_task_count()
        execution_log: List[str] = []
        logger = MockLogger()
        bg = BackgroundTasks(logger=logger)

        labels = [f"task_{i}" for i in range(task_count)]
        for label in labels:
            bg.add_task(make_recording_task(label, execution_log))

        # Property: no tasks should execute before run()
        if len(execution_log) > 0:
            errmsg = (
                f"Iteration {iteration}: tasks executed before run() was called. "
                f"Execution log: {execution_log}"
            )
            raise AssertionError(errmsg)

        loop.run_until_complete(bg.run())

        # Property: execution order must match addition order
        if execution_log != labels:
            errmsg = (
                f"Iteration {iteration}: tasks executed in wrong order. "
                f"Expected {labels}, got {execution_log}"
            )
            raise AssertionError(errmsg)

    return


def test_property_9_exceptions_do_not_prevent_subsequent_tasks():
    """
        Property 9: Exception Isolation

        For any sequence of tasks where some tasks raise exceptions,
        ALL tasks SHALL still execute and exceptions SHALL be logged
        without preventing subsequent task execution.

        **Validates: Requirements 7.5, 7.6**
    """
    loop = asyncio.get_event_loop()

    for iteration in range(100):
        task_count = generate_task_count()
        failure_indices = generate_failure_indices(task_count)
        execution_log: List[str] = []
        logger = MockLogger()
        bg = BackgroundTasks(logger=logger)

        labels = [f"task_{i}" for i in range(task_count)]
        for i, label in enumerate(labels):
            if i in failure_indices:
                bg.add_task(make_failing_task(label, execution_log))
            else:
                bg.add_task(make_recording_task(label, execution_log))

        loop.run_until_complete(bg.run())

        # Property: ALL tasks must have executed regardless of failures
        if execution_log != labels:
            errmsg = (
                f"Iteration {iteration}: not all tasks executed. "
                f"Expected {labels}, got {execution_log}. "
                f"Failure indices: {failure_indices}"
            )
            raise AssertionError(errmsg)

        # Property: errors from failing tasks must be logged
        if len(logger.messages) != len(failure_indices):
            errmsg = (
                f"Iteration {iteration}: expected {len(failure_indices)} error logs "
                f"for failing tasks, got {len(logger.messages)}"
            )
            raise AssertionError(errmsg)

    return


def test_property_9_tasks_do_not_execute_before_run():
    """
        Property 9: Response-First Guarantee

        For any number of added tasks, no task SHALL execute until run()
        is called, ensuring the response is not delayed by background work.

        **Validates: Requirement 7.3**
    """
    loop = asyncio.get_event_loop()

    for iteration in range(100):
        task_count = generate_task_count()
        execution_log: List[str] = []
        logger = MockLogger()
        bg = BackgroundTasks(logger=logger)

        labels = [f"task_{i}" for i in range(task_count)]
        for label in labels:
            bg.add_task(make_recording_task(label, execution_log))

        # Property: no tasks should have executed yet
        if len(execution_log) != 0:
            errmsg = (
                f"Iteration {iteration}: {len(execution_log)} tasks executed "
                f"before run() was called"
            )
            raise AssertionError(errmsg)

        # Property: task_count should reflect pending tasks
        if bg.task_count != task_count:
            errmsg = (
                f"Iteration {iteration}: expected task_count={task_count}, "
                f"got {bg.task_count}"
            )
            raise AssertionError(errmsg)

        # Now run and verify they all execute
        loop.run_until_complete(bg.run())

        if len(execution_log) != task_count:
            errmsg = (
                f"Iteration {iteration}: expected {task_count} tasks to execute "
                f"after run(), got {len(execution_log)}"
            )
            raise AssertionError(errmsg)

    return


def test_property_9_tasks_receive_correct_arguments():
    """
        Property 9: Task Argument Passing

        For any background task added with positional and keyword arguments,
        the task SHALL receive exactly those arguments when executed.

        **Validates: Requirement 7.1**
    """
    loop = asyncio.get_event_loop()

    for iteration in range(100):
        task_count = generate_task_count()
        execution_log: List = []
        logger = MockLogger()
        bg = BackgroundTasks(logger=logger)

        expected_records = []
        for i in range(task_count):
            label = f"task_{i}"
            # Generate random args
            num_args = random.randint(0, 3)
            args = tuple(random.randint(0, 100) for _ in range(num_args))
            # Generate random kwargs
            num_kwargs = random.randint(0, 3)
            kwargs = {f"key_{j}": random.randint(0, 100) for j in range(num_kwargs)}

            bg.add_task(make_recording_task_with_args(label, execution_log), *args, **kwargs)
            expected_records.append((label, args, tuple(sorted(kwargs.items()))))

        loop.run_until_complete(bg.run())

        # Property: each task must have received its exact arguments in order
        if execution_log != expected_records:
            errmsg = (
                f"Iteration {iteration}: task arguments mismatch. "
                f"Expected {expected_records}, got {execution_log}"
            )
            raise AssertionError(errmsg)

    return


def test_property_9_run_clears_task_queue():
    """
        Property 9: Queue Cleared After Execution

        For any sequence of tasks, after run() completes, the task queue
        SHALL be empty and a subsequent run() SHALL execute no tasks.

        **Validates: Requirements 7.4, 7.5**
    """
    loop = asyncio.get_event_loop()

    for iteration in range(100):
        task_count = generate_task_count()
        execution_log: List[str] = []
        logger = MockLogger()
        bg = BackgroundTasks(logger=logger)

        labels = [f"task_{i}" for i in range(task_count)]
        for label in labels:
            bg.add_task(make_recording_task(label, execution_log))

        loop.run_until_complete(bg.run())

        # Property: queue must be empty after run
        if bg.task_count != 0:
            errmsg = (
                f"Iteration {iteration}: task_count is {bg.task_count} after run(), "
                f"expected 0"
            )
            raise AssertionError(errmsg)

        # Property: second run should not execute anything new
        execution_log.clear()
        loop.run_until_complete(bg.run())

        if len(execution_log) != 0:
            errmsg = (
                f"Iteration {iteration}: second run() executed {len(execution_log)} "
                f"tasks, expected 0"
            )
            raise AssertionError(errmsg)

    return
