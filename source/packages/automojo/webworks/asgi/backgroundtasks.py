"""
    ASGI Background Tasks module.
    
    This module provides the BackgroundTasks class that manages background tasks
    to run after response completion. Tasks are scheduled during request handling
    and executed asynchronously after the response is sent to the client.
"""

import asyncio
import logging
import traceback
from typing import Any, Awaitable, Callable, Dict, List, Optional, Tuple


# Type alias for async task functions
TaskCallable = Callable[..., Awaitable[Any]]


class BackgroundTasks:
    """
        Manages background tasks to run after response completion.
        
        Background tasks are async functions scheduled during request handling
        that execute after the response is sent. This allows for operations like
        sending emails, logging, or cleanup without delaying the response.
        
        Tasks are executed in the order they were added, and exceptions in one
        task do not prevent execution of subsequent tasks.
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
            Construct a BackgroundTasks instance.
            
            :param logger: Optional logger for error logging. If not provided,
                          a default logger will be created.
        """
        self._tasks: List[Tuple[TaskCallable, tuple, Dict[str, Any]]] = []
        self._running_tasks: List[asyncio.Task] = []
        
        if logger is None:
            self._logger = logging.getLogger(__name__)
        else:
            self._logger = logger
        
        return
    
    @property
    def task_count(self) -> int:
        """
            Get the number of pending tasks.
            
            :returns: Number of tasks scheduled but not yet executed.
        """
        return len(self._tasks)
    
    @property
    def has_tasks(self) -> bool:
        """
            Check if there are any pending tasks.
            
            :returns: True if there are pending tasks.
        """
        return len(self._tasks) > 0
    
    def add_task(
        self,
        func: TaskCallable,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """
            Schedule a background task.
            
            The task will be executed after the response is sent. Tasks are
            executed in the order they are added.
            
            :param func: Async function to run as a background task.
            :param args: Positional arguments to pass to the function.
            :param kwargs: Keyword arguments to pass to the function.
        """
        self._tasks.append((func, args, kwargs))
        return
    
    async def run(self) -> None:
        """
            Execute all scheduled background tasks.
            
            Tasks are executed in the order they were added. Exceptions in
            one task are logged but do not prevent execution of subsequent
            tasks.
            
            After execution, the task list is cleared.
        """
        tasks_to_run = self._tasks.copy()
        self._tasks.clear()
        
        for func, args, kwargs in tasks_to_run:
            try:
                await func(*args, **kwargs)
            except asyncio.CancelledError:
                # Re-raise cancellation to allow proper shutdown
                raise
            except Exception as err:
                # Log the error but continue with remaining tasks
                self._log_task_error(func, err)
        
        return
    
    def clear(self) -> None:
        """
            Clear all pending tasks without executing them.
            
            This removes all scheduled tasks from the queue.
        """
        self._tasks.clear()
        return
    
    async def cancel_all(self) -> None:
        """
            Cancel all pending and running tasks.
            
            This method cancels any currently running tasks and clears
            the pending task queue. Used during application shutdown.
        """
        # Clear pending tasks
        self._tasks.clear()
        
        # Cancel any running tasks
        for task in self._running_tasks:
            if not task.done():
                task.cancel()
        
        # Wait for cancellation to complete
        if self._running_tasks:
            await asyncio.gather(*self._running_tasks, return_exceptions=True)
            self._running_tasks.clear()
        
        return
    
    def _log_task_error(
        self,
        func: TaskCallable,
        error: Exception,
    ) -> None:
        """
            Log an error that occurred during task execution.
            
            :param func: The task function that raised the error.
            :param error: The exception that was raised.
        """
        func_name = getattr(func, "__name__", repr(func))
        tb_str = traceback.format_exc()
        
        self._logger.error(
            f"Background task '{func_name}' raised an exception: "
            f"{type(error).__name__}: {error}\n{tb_str}"
        )
        
        return

