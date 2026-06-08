"""
    Hook manager for the extensibility system.

    This module provides the HookManager class which handles hook
    registration, priority-based ordering, before/after constraint
    resolution, and callback execution for the extension framework.
"""

import logging
import traceback

from collections import defaultdict
from typing import Any, Callable, Dict, List, Optional

from ccai.webworks.extensibility.datastructures import HookPriority
from ccai.webworks.extensibility.datastructures import HookRegistration
from ccai.webworks.extensibility.exceptions import HookOrderingError


logger = logging.getLogger("ccai.webworks.extensibility.hookmanager")


class HookManager:
    """
        Manages hook registration and execution for the extensibility system.

        The HookManager maintains a registry of hook callbacks organized by
        hook name. It supports priority-based ordering, before/after constraints
        between extensions, and error-isolated callback execution.
    """

    def __init__(self):
        self._hooks: Dict[str, List[HookRegistration]] = {}
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
        """
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

            Removes the first registration matching the given callback
            from the hook's registration list. If the hook name does not
            exist or the callback is not found, the method does nothing.

            :param hook_name: The name of the hook to unregister from.
            :param callback: The callback to remove.
        """
        if hook_name not in self._hooks:
            return

        registrations = self._hooks[hook_name]
        updated_registrations = [
            reg for reg in registrations if reg.callback is not callback
        ]

        if len(updated_registrations) == 0:
            del self._hooks[hook_name]
        else:
            self._hooks[hook_name] = updated_registrations

        return


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
        error_callback: Optional[Callable] = None,
        **kwargs
    ) -> List[Any]:
        """
            Execute all callbacks registered for the specified hook.

            Callbacks are executed in the resolved order (by priority and
            before/after constraints). Exceptions raised by individual
            callbacks are caught and logged so that one failing callback
            does not prevent other callbacks from executing.

            :param hook_name: The name of the hook to execute.
            :param args: Positional arguments to pass to each callback.
            :param stop_on_result: If True, stop execution when a callback
                returns a non-None value.
            :param error_callback: Optional callable invoked with
                (extension_name, hook_name, exception, traceback_str)
                when a callback raises an exception.
            :param kwargs: Keyword arguments to pass to each callback.

            :returns: A list of return values from each executed callback.
        """
        ordered_registrations = self._resolve_execution_order(hook_name)

        results = []

        for reg in ordered_registrations:
            try:
                result = reg.callback(*args, **kwargs)
                results.append(result)

                if stop_on_result is True and result is not None:
                    break

            except Exception as err:
                ext_label = reg.extension_name if reg.extension_name is not None else "unknown"
                tb_str = traceback.format_exc()
                logger.error(
                    "Hook '%s' callback from extension '%s' raised an exception: %s\n%s",
                    hook_name, ext_label, err, tb_str
                )
                results.append(None)

                if error_callback is not None:
                    try:
                        error_callback(ext_label, hook_name, err, tb_str)
                    except Exception as cb_err:
                        logger.error(
                            "Error callback failed for hook '%s' extension '%s': %s",
                            hook_name, ext_label, cb_err
                        )

        return results


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
