"""
    Hook manager for the extensibility system.

    This module provides the HookManager class which handles hook
    registration, priority-based ordering, before/after constraint
    resolution, and callback execution for the extension framework.
"""

import inspect
import logging
import traceback

from collections import defaultdict
from typing import Any, Callable, Dict, Iterable, List, Optional, Set

from ccai.errors.exceptions import SemanticError

from ccai.webworks.extensibility.datastructures import HookPriority
from ccai.webworks.extensibility.datastructures import HookRegistration
from ccai.webworks.extensibility.exceptions import HookExecutionError
from ccai.webworks.extensibility.exceptions import HookOrderingError


logger = logging.getLogger("ccai.webworks.extensibility.hookmanager")


class HookManager:
    """
        Manages hook registration and execution for the extensibility system.

        The HookManager maintains a registry of hook callbacks organized by
        hook name. It supports priority-based ordering, before/after constraints
        between extensions, and error-isolated callback execution.

        The callbacks of an extension can be suspended as a group, which is
        what the ExtensionRegistry does when the extension is disabled or
        quarantined: they stay registered, are skipped by execute() and run
        again once the extension is resumed.

        Callbacks are called synchronously, so a coroutine function can not
        be registered: it would return a coroutine that nothing awaits.

        :param error_callback: Optional callable invoked with
            (extension_name, hook_name, exception, traceback_str) whenever a
            callback raises, for every execute() call that does not pass an
            error callback of its own.
    """

    def __init__(self, error_callback: Optional[Callable] = None):
        self._hooks: Dict[str, List[HookRegistration]] = {}
        self._error_callback: Optional[Callable] = error_callback
        self._suspended_extensions: Set[str] = set()
        return


    def set_error_callback(self, error_callback: Optional[Callable]) -> None:
        """
            Set the callable that is told about every callback failure.

            :param error_callback: Callable invoked with
                (extension_name, hook_name, exception, traceback_str), or
                None to remove it.
        """
        self._error_callback = error_callback
        return


    def register(
        self,
        hook_name: str,
        callback: Callable,
        priority: int = HookPriority.NORMAL,
        extension_name: Optional[str] = None,
        before: Optional[List[str]] = None,
        after: Optional[List[str]] = None
    ) -> None:
        """
            Register a hook callback for the specified hook name.

            The callback will be invoked when the hook is executed. Callbacks
            are ordered by priority (lower values execute first) and can
            specify before/after constraints relative to other extensions.

            :param hook_name: The name of the hook to register for.
            :param callback: The callable to invoke when the hook fires.
            :param priority: Numeric priority value (lower executes first).
            :param extension_name: The name of the registering extension.
            :param before: List of extension names this hook should run before.
            :param after: List of extension names this hook should run after.

            :raises SemanticError: If the callback is a coroutine function.
                Callbacks are called synchronously; its coroutine would
                never run.
        """
        if inspect.iscoroutinefunction(callback) or inspect.iscoroutinefunction(getattr(callback, "__call__", None)):
            errmsg = (
                "The callback {!r} registered for hook '{}' (extension '{}') is a coroutine "
                "function. Hook callbacks are called synchronously and their result is not "
                "awaited, so its body would never run. Register a plain function."
            ).format(callback, hook_name, extension_name)
            raise SemanticError(errmsg)

        if before is None:
            before = []

        if after is None:
            after = []

        registration = HookRegistration(
            callback=callback,
            priority=priority,
            extension_name=extension_name,
            before=before,
            after=after
        )

        if hook_name not in self._hooks:
            self._hooks[hook_name] = []

        self._hooks[hook_name].append(registration)

        return


    def unregister(self, hook_name: str, callback: Callable) -> None:
        """
            Unregister a hook callback from the specified hook name.

            Removes the registrations matching the given callback
            from the hook's registration list. If the hook name does not
            exist or the callback is not found, the method does nothing.

            Callbacks are compared by equality, not identity. Every access
            to a bound method (``self.on_request``) creates a new object, so
            the object passed here is never the one that was registered;
            two bound methods are equal when they are the same function
            bound to the same instance.

            :param hook_name: The name of the hook to unregister from.
            :param callback: The callback to remove.
        """
        if hook_name not in self._hooks:
            return

        registrations = self._hooks[hook_name]
        updated_registrations = []
        for reg in registrations:
            if reg.callback != callback:
                updated_registrations.append(reg)

        if len(updated_registrations) == 0:
            del self._hooks[hook_name]
        else:
            self._hooks[hook_name] = updated_registrations

        return


    def unregister_extension(self, extension_name: str) -> int:
        """
            Unregister every hook callback an extension registered.

            :param extension_name: The name of the extension.

            :returns: The number of registrations removed.
        """
        removed_count = 0

        for hook_name in list(self._hooks.keys()):
            registrations = self._hooks[hook_name]

            kept_registrations = []
            for reg in registrations:
                if reg.extension_name == extension_name:
                    removed_count += 1
                else:
                    kept_registrations.append(reg)

            if len(kept_registrations) == 0:
                del self._hooks[hook_name]
            else:
                self._hooks[hook_name] = kept_registrations

        return removed_count


    def has_callbacks(self, hook_name: str) -> bool:
        """
            Check whether any callback is registered for a hook.

            Cheap enough to be asked for every request: a dictionary lookup,
            nothing is allocated.

            :param hook_name: The name of the hook.

            :returns: True if at least one callback is registered for it
                      (suspended callbacks count).
        """
        rtnval = hook_name in self._hooks
        return rtnval


    def has_any_callbacks(self, hook_names: Iterable[str]) -> bool:
        """
            Check whether any callback is registered for any of the hooks.

            Answers False without looking at the names when no callback is
            registered at all, which is the state of an application without
            extensions.

            :param hook_names: The names of the hooks.

            :returns: True if at least one of the hooks has a callback.
        """
        rtnval = False

        if len(self._hooks) > 0:
            for hook_name in hook_names:
                if hook_name in self._hooks:
                    rtnval = True
                    break

        return rtnval


    def suspend_extension(self, extension_name: str) -> None:
        """
            Stop running the hook callbacks of an extension.

            The registrations are kept; execute() skips them until
            resume_extension() is called for the extension.

            :param extension_name: The name of the extension.
        """
        self._suspended_extensions.add(extension_name)
        return


    def resume_extension(self, extension_name: str) -> None:
        """
            Run the hook callbacks of a suspended extension again.

            :param extension_name: The name of the extension.
        """
        self._suspended_extensions.discard(extension_name)
        return


    def is_suspended(self, extension_name: str) -> bool:
        """
            Check whether the hook callbacks of an extension are suspended.

            :param extension_name: The name of the extension.

            :returns: True if the extension's callbacks are skipped.
        """
        rtnval = extension_name in self._suspended_extensions
        return rtnval


    def _resolve_execution_order(self, hook_name: str) -> List[HookRegistration]:
        """
            Resolve the execution order for all registrations of a hook.

            The resolution process has two phases:
            1. Sort registrations by priority (lower numeric value first).
               Registrations with the same priority maintain their registration order.
            2. Apply before/after constraints using topological sort.
               If constraints create a cycle, HookOrderingError is raised.

            :param hook_name: The name of the hook to resolve ordering for.

            :returns: A list of HookRegistration objects in resolved execution order.

            :raises: HookOrderingError
        """
        if hook_name not in self._hooks:
            return []

        registrations = self._hooks[hook_name]

        if len(registrations) <= 1:
            return list(registrations)

        # Phase 1: Sort by priority, preserving registration order for equal priorities
        sorted_registrations = sorted(
            registrations,
            key=lambda reg: reg.priority
        )

        # Phase 2: Apply before/after constraints via topological sort
        # Build a mapping from extension_name to list of indices in sorted_registrations
        ext_name_to_indices: Dict[str, List[int]] = defaultdict(list)
        for idx, reg in enumerate(sorted_registrations):
            if reg.extension_name is not None:
                ext_name_to_indices[reg.extension_name].append(idx)

        # Build adjacency list for topological sort
        # edge (a, b) means a must execute before b
        num_regs = len(sorted_registrations)
        adjacency: Dict[int, List[int]] = defaultdict(list)
        in_degree: Dict[int, int] = {}

        for idx in range(num_regs):
            in_degree[idx] = 0

        for idx, reg in enumerate(sorted_registrations):
            # "before" constraint: this registration should run before the named extensions
            for target_name in reg.before:
                if target_name in ext_name_to_indices:
                    for target_idx in ext_name_to_indices[target_name]:
                        if target_idx != idx:
                            adjacency[idx].append(target_idx)
                            in_degree[target_idx] = in_degree[target_idx] + 1

            # "after" constraint: this registration should run after the named extensions
            for source_name in reg.after:
                if source_name in ext_name_to_indices:
                    for source_idx in ext_name_to_indices[source_name]:
                        if source_idx != idx:
                            adjacency[source_idx].append(idx)
                            in_degree[idx] = in_degree[idx] + 1

        # Kahn's algorithm for topological sort
        # Use a list-based queue that processes nodes in their sorted order
        # to maintain priority ordering as a tiebreaker
        queue = []
        for idx in range(num_regs):
            if in_degree[idx] == 0:
                queue.append(idx)

        ordered_indices = []

        while len(queue) > 0:
            # Pick the first available node (preserves priority ordering)
            current = queue.pop(0)
            ordered_indices.append(current)

            for neighbor in adjacency[current]:
                in_degree[neighbor] = in_degree[neighbor] - 1
                if in_degree[neighbor] == 0:
                    # Insert in sorted position to maintain priority order
                    inserted = False
                    for insert_pos in range(len(queue)):
                        if neighbor < queue[insert_pos]:
                            queue.insert(insert_pos, neighbor)
                            inserted = True
                            break
                    if inserted is not True:
                        queue.append(neighbor)

        if len(ordered_indices) != num_regs:
            # Cycle detected - collect the conflicting extension names
            remaining_indices = set(range(num_regs)) - set(ordered_indices)
            conflicting_names = []
            for idx in remaining_indices:
                reg = sorted_registrations[idx]
                if reg.extension_name is not None:
                    conflicting_names.append(reg.extension_name)
                else:
                    conflicting_names.append("unnamed-hook-{}".format(idx))

            raise HookOrderingError(
                hook_name=hook_name,
                conflicting_constraints=conflicting_names
            )

        result = [sorted_registrations[idx] for idx in ordered_indices]

        return result


    def execute(
        self,
        hook_name: str,
        *args,
        stop_on_result: bool = False,
        stop_on_error: bool = False,
        error_callback: Optional[Callable] = None,
        **kwargs
    ) -> List[Any]:
        """
            Execute all callbacks registered for the specified hook.

            Callbacks are executed in the resolved order (by priority and
            before/after constraints). Exceptions raised by individual
            callbacks are caught and logged so that one failing callback
            does not prevent other callbacks from executing. The callbacks
            of a suspended extension are skipped.

            ``ConfigurationError`` and ``SemanticError`` derive from
            ``BaseException`` and are never caught: they end the run.

            :param hook_name: The name of the hook to execute.
            :param args: Positional arguments to pass to each callback.
            :param stop_on_result: If True, stop execution when a callback
                returns a non-None value.
            :param stop_on_error: If True, a callback that raises is
                reported (logged and passed to the error callback) like any
                other failure and then ends the execution:
                :class:`HookExecutionError` is raised from its exception.
                For hooks whose caller can not carry on past a failed
                callback, such as ``before_request``.
            :param error_callback: Optional callable invoked with
                (extension_name, hook_name, exception, traceback_str)
                when a callback raises an exception. When None, the
                manager's own error callback is used, if it has one.
            :param kwargs: Keyword arguments to pass to each callback.

            :returns: A list of return values from each executed callback.

            :raises HookExecutionError: If ``stop_on_error`` is True and a
                callback raised.
        """
        ordered_registrations = self._resolve_execution_order(hook_name)

        if error_callback is None:
            error_callback = self._error_callback

        results = []

        for reg in ordered_registrations:
            if reg.extension_name is not None and reg.extension_name in self._suspended_extensions:
                continue

            try:
                result = reg.callback(*args, **kwargs)
                results.append(result)

                if stop_on_result is True and result is not None:
                    break

            except Exception as err:
                ext_label = self._report_failure(reg, hook_name, err, error_callback)
                results.append(None)

                if stop_on_error is True:
                    raise HookExecutionError(hook_name=hook_name, extension_name=ext_label) from err

        return results


    def execute_chain(
        self,
        hook_name: str,
        value: Any,
        *args,
        stop_on_error: bool = False,
        error_callback: Optional[Callable] = None,
        **kwargs
    ) -> Any:
        """
            Pass a value through every callback registered for a hook.

            Each callback is called with the positional arguments followed
            by the current value. A callback that returns something other
            than None replaces the value, and the next callback receives the
            replacement; a callback that returns None leaves it as it was
            (it may have changed the value in place). The ``after_request``
            hook runs this way: every callback sees the response the one
            before it produced.

            Order, suspension and error reporting are those of
            :meth:`execute`.

            :param hook_name: The name of the hook to execute.
            :param value: The value to pass through the callbacks.
            :param args: Positional arguments passed before the value.
            :param stop_on_error: If True, a callback that raises is
                reported and then ends the execution with
                :class:`HookExecutionError`. Otherwise the value is passed
                on to the next callback as it was.
            :param error_callback: Optional callable invoked with
                (extension_name, hook_name, exception, traceback_str) when a
                callback raises. When None, the manager's own error callback
                is used, if it has one.
            :param kwargs: Keyword arguments to pass to each callback.

            :returns: The value as the last callback left it.

            :raises HookExecutionError: If ``stop_on_error`` is True and a
                callback raised.
        """
        ordered_registrations = self._resolve_execution_order(hook_name)

        if error_callback is None:
            error_callback = self._error_callback

        current_value = value

        for reg in ordered_registrations:
            if reg.extension_name is not None and reg.extension_name in self._suspended_extensions:
                continue

            try:
                result = reg.callback(*args, current_value, **kwargs)

                if result is not None:
                    current_value = result

            except Exception as err:
                ext_label = self._report_failure(reg, hook_name, err, error_callback)

                if stop_on_error is True:
                    raise HookExecutionError(hook_name=hook_name, extension_name=ext_label) from err

        return current_value


    def _report_failure(
        self,
        reg: HookRegistration,
        hook_name: str,
        err: Exception,
        error_callback: Optional[Callable]
    ) -> str:
        """
            Report a callback that raised: log it with its extension's name
            and hand it to the error callback.

            Must be called from the ``except`` block that caught the
            exception, so the traceback is the callback's.

            :param reg: The registration of the callback that raised.
            :param hook_name: The hook that was being executed.
            :param err: The exception the callback raised.
            :param error_callback: The error callback to notify, or None.

            :returns: The extension name the failure was reported under
                      (``"unknown"`` for a callback without one).
        """
        ext_label = reg.extension_name if reg.extension_name is not None else "unknown"
        tb_str = traceback.format_exc()
        logger.error(
            "Hook '%s' callback from extension '%s' raised an exception: %s\n%s",
            hook_name, ext_label, err, tb_str
        )

        if error_callback is not None:
            try:
                error_callback(ext_label, hook_name, err, tb_str)
            except Exception as cb_err:
                logger.error(
                    "Error callback failed for hook '%s' extension '%s': %s",
                    hook_name, ext_label, cb_err
                )

        return ext_label


    def get_execution_order(self, hook_name: str) -> List[str]:
        """
            Get the execution order for a hook's callbacks as extension names.

            Returns the list of extension names in the order their callbacks
            would be executed. Registrations without an extension name are
            represented as empty strings.

            :param hook_name: The name of the hook.

            :returns: A list of extension names in execution order.
        """
        ordered_registrations = self._resolve_execution_order(hook_name)

        result = []
        for reg in ordered_registrations:
            if reg.extension_name is not None:
                result.append(reg.extension_name)
            else:
                result.append("")

        return result
