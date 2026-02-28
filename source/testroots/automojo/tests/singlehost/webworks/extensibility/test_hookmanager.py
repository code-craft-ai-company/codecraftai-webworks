"""
    Tests for the HookManager class.

    This module contains unit tests and property-based tests for the
    HookManager class including hook registration, priority ordering,
    before/after constraint resolution, execution, and error handling.
"""

import random
import string

from typing import List, Optional

from automojo.webworks.extensibility.datastructures import HookPriority
from automojo.webworks.extensibility.datastructures import HookRegistration
from automojo.webworks.extensibility.exceptions import HookOrderingError
from automojo.webworks.extensibility.hookmanager import HookManager


# =============================================================================
# Test Helpers
# =============================================================================

def _generate_random_string(min_length: int = 3, max_length: int = 15) -> str:
    """
        Generate a random string of lowercase alphanumeric characters.

        :param min_length: Minimum length of the generated string.
        :param max_length: Maximum length of the generated string.

        :returns: A random alphanumeric string.
    """
    length = random.randint(min_length, max_length)
    result = "".join(random.choices(string.ascii_lowercase + string.digits, k=length))
    return result


def _make_callback(label: str):
    """
        Create a callback function that appends its label to a shared list.

        :param label: The label to append when the callback is invoked.

        :returns: A callable that accepts a call_log list and appends the label.
    """
    def callback(call_log: list):
        call_log.append(label)
        return label
    return callback


def _make_failing_callback(label: str):
    """
        Create a callback function that raises a RuntimeError.

        :param label: The label used in the error message.

        :returns: A callable that raises RuntimeError when invoked.
    """
    def callback(call_log: list):
        raise RuntimeError("Error from {}".format(label))
    return callback


# =============================================================================
# Unit Tests for HookManager.__init__
# =============================================================================

def test_hookmanager_initial_hooks_is_empty():
    """
        Test that a newly created HookManager has an empty hooks dict.
    """
    manager = HookManager()

    if len(manager._hooks) != 0:
        errmsg = "Expected empty _hooks dict, got {} entries".format(len(manager._hooks))
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for register()
# =============================================================================

def test_hookmanager_register_adds_hook():
    """
        Test that register() adds a callback to the hooks dict.
    """
    manager = HookManager()

    def my_callback():
        return None

    manager.register("test_hook", my_callback, extension_name="ext-a")

    if "test_hook" not in manager._hooks:
        errmsg = "Expected 'test_hook' key in _hooks"
        raise AssertionError(errmsg)

    if len(manager._hooks["test_hook"]) != 1:
        errmsg = "Expected 1 registration, got {}".format(len(manager._hooks["test_hook"]))
        raise AssertionError(errmsg)

    reg = manager._hooks["test_hook"][0]
    if reg.callback is not my_callback:
        errmsg = "Expected callback to be the registered function"
        raise AssertionError(errmsg)

    if reg.extension_name != "ext-a":
        errmsg = "Expected extension_name 'ext-a', got '{}'".format(reg.extension_name)
        raise AssertionError(errmsg)

    if reg.priority != HookPriority.NORMAL:
        errmsg = "Expected default priority NORMAL (50), got {}".format(reg.priority)
        raise AssertionError(errmsg)

    return


def test_hookmanager_register_multiple_hooks_same_name():
    """
        Test that multiple callbacks can be registered for the same hook name.
    """
    manager = HookManager()

    def cb_a():
        return None

    def cb_b():
        return None

    manager.register("test_hook", cb_a, extension_name="ext-a")
    manager.register("test_hook", cb_b, extension_name="ext-b")

    if len(manager._hooks["test_hook"]) != 2:
        errmsg = "Expected 2 registrations, got {}".format(len(manager._hooks["test_hook"]))
        raise AssertionError(errmsg)

    return


def test_hookmanager_register_with_before_after():
    """
        Test that register() stores before and after constraints.
    """
    manager = HookManager()

    def my_callback():
        return None

    manager.register(
        "test_hook",
        my_callback,
        extension_name="ext-a",
        before=["ext-b"],
        after=["ext-c"]
    )

    reg = manager._hooks["test_hook"][0]

    if reg.before != ["ext-b"]:
        errmsg = "Expected before=['ext-b'], got {}".format(reg.before)
        raise AssertionError(errmsg)

    if reg.after != ["ext-c"]:
        errmsg = "Expected after=['ext-c'], got {}".format(reg.after)
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for unregister()
# =============================================================================

def test_hookmanager_unregister_removes_callback():
    """
        Test that unregister() removes the specified callback.
    """
    manager = HookManager()

    def cb_a():
        return None

    def cb_b():
        return None

    manager.register("test_hook", cb_a, extension_name="ext-a")
    manager.register("test_hook", cb_b, extension_name="ext-b")

    manager.unregister("test_hook", cb_a)

    if len(manager._hooks["test_hook"]) != 1:
        errmsg = "Expected 1 registration after unregister, got {}".format(
            len(manager._hooks["test_hook"])
        )
        raise AssertionError(errmsg)

    if manager._hooks["test_hook"][0].callback is not cb_b:
        errmsg = "Expected remaining callback to be cb_b"
        raise AssertionError(errmsg)

    return


def test_hookmanager_unregister_last_callback_removes_key():
    """
        Test that unregistering the last callback removes the hook name key.
    """
    manager = HookManager()

    def my_callback():
        return None

    manager.register("test_hook", my_callback, extension_name="ext-a")
    manager.unregister("test_hook", my_callback)

    if "test_hook" in manager._hooks:
        errmsg = "Expected 'test_hook' key to be removed from _hooks"
        raise AssertionError(errmsg)

    return


def test_hookmanager_unregister_nonexistent_hook_does_nothing():
    """
        Test that unregistering from a nonexistent hook name does not raise.
    """
    manager = HookManager()

    def my_callback():
        return None

    # Should not raise
    manager.unregister("nonexistent_hook", my_callback)

    return


# =============================================================================
# Unit Tests for execute()
# =============================================================================

def test_hookmanager_execute_calls_callbacks_in_priority_order():
    """
        Test that execute() calls callbacks in ascending priority order.
    """
    manager = HookManager()
    call_log = []

    cb_low = _make_callback("low")
    cb_high = _make_callback("high")
    cb_normal = _make_callback("normal")

    manager.register("test_hook", cb_low, priority=HookPriority.LOW, extension_name="ext-low")
    manager.register("test_hook", cb_high, priority=HookPriority.HIGH, extension_name="ext-high")
    manager.register("test_hook", cb_normal, priority=HookPriority.NORMAL, extension_name="ext-normal")

    manager.execute("test_hook", call_log)

    expected = ["high", "normal", "low"]
    if call_log != expected:
        errmsg = "Expected call order {}, got {}".format(expected, call_log)
        raise AssertionError(errmsg)

    return


def test_hookmanager_execute_returns_callback_results():
    """
        Test that execute() returns a list of callback return values.
    """
    manager = HookManager()
    call_log = []

    cb_a = _make_callback("a")
    cb_b = _make_callback("b")

    manager.register("test_hook", cb_a, extension_name="ext-a")
    manager.register("test_hook", cb_b, extension_name="ext-b")

    results = manager.execute("test_hook", call_log)

    if results != ["a", "b"]:
        errmsg = "Expected results ['a', 'b'], got {}".format(results)
        raise AssertionError(errmsg)

    return


def test_hookmanager_execute_stop_on_result():
    """
        Test that execute() stops when stop_on_result is True and a callback returns non-None.
    """
    manager = HookManager()
    call_log = []

    cb_a = _make_callback("a")
    cb_b = _make_callback("b")

    manager.register("test_hook", cb_a, priority=HookPriority.HIGH, extension_name="ext-a")
    manager.register("test_hook", cb_b, priority=HookPriority.LOW, extension_name="ext-b")

    results = manager.execute("test_hook", call_log, stop_on_result=True)

    if len(results) != 1:
        errmsg = "Expected 1 result with stop_on_result, got {}".format(len(results))
        raise AssertionError(errmsg)

    if call_log != ["a"]:
        errmsg = "Expected only 'a' to be called, got {}".format(call_log)
        raise AssertionError(errmsg)

    return


def test_hookmanager_execute_handles_exceptions():
    """
        Test that execute() catches exceptions and continues with other callbacks.
    """
    manager = HookManager()
    call_log = []

    cb_good = _make_callback("good")
    cb_bad = _make_failing_callback("bad")

    manager.register("test_hook", cb_bad, priority=HookPriority.HIGH, extension_name="ext-bad")
    manager.register("test_hook", cb_good, priority=HookPriority.LOW, extension_name="ext-good")

    results = manager.execute("test_hook", call_log)

    # The failing callback should produce None, the good one should produce "good"
    if len(results) != 2:
        errmsg = "Expected 2 results, got {}".format(len(results))
        raise AssertionError(errmsg)

    if results[0] is not None:
        errmsg = "Expected None for failed callback, got {}".format(results[0])
        raise AssertionError(errmsg)

    if results[1] != "good":
        errmsg = "Expected 'good' for successful callback, got {}".format(results[1])
        raise AssertionError(errmsg)

    if call_log != ["good"]:
        errmsg = "Expected only 'good' in call_log, got {}".format(call_log)
        raise AssertionError(errmsg)

    return


def test_hookmanager_execute_empty_hook():
    """
        Test that execute() returns an empty list for a nonexistent hook.
    """
    manager = HookManager()

    results = manager.execute("nonexistent_hook")

    if results != []:
        errmsg = "Expected empty results for nonexistent hook, got {}".format(results)
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for get_execution_order()
# =============================================================================

def test_hookmanager_get_execution_order_returns_extension_names():
    """
        Test that get_execution_order() returns extension names in order.
    """
    manager = HookManager()

    def cb_a():
        return None

    def cb_b():
        return None

    manager.register("test_hook", cb_a, priority=HookPriority.LOW, extension_name="ext-a")
    manager.register("test_hook", cb_b, priority=HookPriority.HIGH, extension_name="ext-b")

    order = manager.get_execution_order("test_hook")

    expected = ["ext-b", "ext-a"]
    if order != expected:
        errmsg = "Expected order {}, got {}".format(expected, order)
        raise AssertionError(errmsg)

    return


def test_hookmanager_get_execution_order_empty_for_nonexistent():
    """
        Test that get_execution_order() returns empty list for nonexistent hook.
    """
    manager = HookManager()

    order = manager.get_execution_order("nonexistent_hook")

    if order != []:
        errmsg = "Expected empty list, got {}".format(order)
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for before/after constraints
# =============================================================================

def test_hookmanager_before_constraint_ordering():
    """
        Test that a before constraint causes a hook to execute before the target.
    """
    manager = HookManager()
    call_log = []

    cb_a = _make_callback("a")
    cb_b = _make_callback("b")

    # Both same priority, but ext-a declares it should run before ext-b
    manager.register("test_hook", cb_a, priority=HookPriority.NORMAL, extension_name="ext-a", before=["ext-b"])
    manager.register("test_hook", cb_b, priority=HookPriority.NORMAL, extension_name="ext-b")

    manager.execute("test_hook", call_log)

    if call_log != ["a", "b"]:
        errmsg = "Expected ['a', 'b'] with before constraint, got {}".format(call_log)
        raise AssertionError(errmsg)

    return


def test_hookmanager_after_constraint_ordering():
    """
        Test that an after constraint causes a hook to execute after the source.
    """
    manager = HookManager()
    call_log = []

    cb_a = _make_callback("a")
    cb_b = _make_callback("b")

    # Both same priority, but ext-b declares it should run after ext-a
    manager.register("test_hook", cb_a, priority=HookPriority.NORMAL, extension_name="ext-a")
    manager.register("test_hook", cb_b, priority=HookPriority.NORMAL, extension_name="ext-b", after=["ext-a"])

    manager.execute("test_hook", call_log)

    if call_log != ["a", "b"]:
        errmsg = "Expected ['a', 'b'] with after constraint, got {}".format(call_log)
        raise AssertionError(errmsg)

    return


def test_hookmanager_circular_constraint_raises_error():
    """
        Test that circular before/after constraints raise HookOrderingError.
    """
    manager = HookManager()

    def cb_a():
        return None

    def cb_b():
        return None

    # ext-a before ext-b, ext-b before ext-a => cycle
    manager.register("test_hook", cb_a, extension_name="ext-a", before=["ext-b"])
    manager.register("test_hook", cb_b, extension_name="ext-b", before=["ext-a"])

    raised = False
    caught_error = None
    try:
        manager.execute("test_hook")
    except HookOrderingError as err:
        raised = True
        caught_error = err

    if raised is not True:
        errmsg = "Expected HookOrderingError for circular constraints"
        raise AssertionError(errmsg)

    if caught_error.hook_name != "test_hook":
        errmsg = "Expected hook_name 'test_hook', got '{}'".format(caught_error.hook_name)
        raise AssertionError(errmsg)

    return


def test_hookmanager_same_priority_registration_order():
    """
        Test that hooks with the same priority execute in registration order.
    """
    manager = HookManager()
    call_log = []

    cb_first = _make_callback("first")
    cb_second = _make_callback("second")
    cb_third = _make_callback("third")

    manager.register("test_hook", cb_first, priority=HookPriority.NORMAL, extension_name="ext-first")
    manager.register("test_hook", cb_second, priority=HookPriority.NORMAL, extension_name="ext-second")
    manager.register("test_hook", cb_third, priority=HookPriority.NORMAL, extension_name="ext-third")

    manager.execute("test_hook", call_log)

    expected = ["first", "second", "third"]
    if call_log != expected:
        errmsg = "Expected registration order {}, got {}".format(expected, call_log)
        raise AssertionError(errmsg)

    return



# =============================================================================
# Property-Based Tests
# =============================================================================

# Feature: extensibility, Property 15: Hook Priority Ordering
# *For any* set of hooks registered for the same event with different priorities,
# executing the hook SHALL call callbacks in ascending priority order (lower
# numbers first), and callbacks with the same priority SHALL execute in
# registration order.
# **Validates: Requirements 5.6, 6.7, 8.1, 8.3, 8.5**

def test_property_15_hook_priority_ordering():
    """
        Property 15: Hook Priority Ordering

        For any set of hooks registered with varying priorities, executing
        the hook SHALL call callbacks in ascending priority order. Callbacks
        with the same priority SHALL execute in registration order.

        **Validates: Requirements 5.6, 6.7, 8.1, 8.3, 8.5**
    """
    for iteration in range(100):
        manager = HookManager()
        hook_name = "test_hook_{}".format(iteration)

        # Generate a random number of registrations (2 to 10)
        num_registrations = random.randint(2, 10)

        # Track registration order and priorities
        registration_info = []

        for reg_idx in range(num_registrations):
            priority = random.randint(0, 100)
            ext_name = "ext-{}-{}".format(iteration, reg_idx)

            def make_cb(name):
                def cb(log: list):
                    log.append(name)
                    return name
                return cb

            callback = make_cb(ext_name)
            manager.register(
                hook_name,
                callback,
                priority=priority,
                extension_name=ext_name
            )
            registration_info.append((reg_idx, priority, ext_name))

        # Execute the hook
        call_log = []
        manager.execute(hook_name, call_log)

        # Verify all callbacks were called
        if len(call_log) != num_registrations:
            errmsg = "Iteration {}: Expected {} callbacks, got {}".format(
                iteration, num_registrations, len(call_log)
            )
            raise AssertionError(errmsg)

        # Build expected order: sort by priority, then by registration order
        sorted_info = sorted(registration_info, key=lambda item: (item[1], item[0]))
        expected_order = [info[2] for info in sorted_info]

        if call_log != expected_order:
            errmsg = (
                "Iteration {}: Priority ordering violated.\n"
                "Registrations (idx, priority, name): {}\n"
                "Expected order: {}\n"
                "Actual order: {}"
            ).format(iteration, registration_info, expected_order, call_log)
            raise AssertionError(errmsg)

    return


# Feature: extensibility, Property 16: Hook Before/After Constraints
# *For any* hook with before/after constraints referencing other extensions,
# the hook SHALL execute in an order satisfying those constraints, or raise
# HookOrderingError if constraints cannot be satisfied.
# **Validates: Requirements 8.6, 8.7**

def test_property_16_hook_before_after_constraints_satisfied():
    """
        Property 16: Hook Before/After Constraints (satisfiable)

        For any set of hooks with non-circular before/after constraints,
        the execution order SHALL satisfy all constraints.

        **Validates: Requirements 8.6, 8.7**
    """
    for iteration in range(100):
        manager = HookManager()
        hook_name = "test_hook_{}".format(iteration)

        # Generate a chain of 3 to 6 extensions with before constraints
        chain_length = random.randint(3, 6)
        ext_names = ["ext-{}-{}".format(iteration, idx) for idx in range(chain_length)]

        callbacks = {}
        for idx, ext_name in enumerate(ext_names):
            def make_cb(name):
                def cb(log: list):
                    log.append(name)
                    return name
                return cb

            callbacks[ext_name] = make_cb(ext_name)

        # Register in random order, but with before constraints forming a chain
        # ext_names[0] before ext_names[1], ext_names[1] before ext_names[2], etc.
        indices = list(range(chain_length))
        random.shuffle(indices)

        for idx in indices:
            ext_name = ext_names[idx]
            before_list = []
            if idx < chain_length - 1:
                before_list = [ext_names[idx + 1]]

            manager.register(
                hook_name,
                callbacks[ext_name],
                priority=HookPriority.NORMAL,
                extension_name=ext_name,
                before=before_list
            )

        # Execute the hook
        call_log = []
        manager.execute(hook_name, call_log)

        # Verify all callbacks were called
        if len(call_log) != chain_length:
            errmsg = "Iteration {}: Expected {} callbacks, got {}".format(
                iteration, chain_length, len(call_log)
            )
            raise AssertionError(errmsg)

        # Verify the chain ordering is satisfied
        for idx in range(chain_length - 1):
            pos_current = call_log.index(ext_names[idx])
            pos_next = call_log.index(ext_names[idx + 1])
            if pos_current >= pos_next:
                errmsg = (
                    "Iteration {}: Before constraint violated. "
                    "'{}' (pos {}) should execute before '{}' (pos {}). "
                    "Actual order: {}"
                ).format(
                    iteration, ext_names[idx], pos_current,
                    ext_names[idx + 1], pos_next, call_log
                )
                raise AssertionError(errmsg)

    return


def test_property_16_hook_circular_constraints_raise_error():
    """
        Property 16: Hook Before/After Constraints (circular detection)

        For any set of hooks with circular before/after constraints,
        executing the hook SHALL raise HookOrderingError.

        **Validates: Requirements 8.6, 8.7**
    """
    for iteration in range(100):
        manager = HookManager()
        hook_name = "test_hook_{}".format(iteration)

        # Create a cycle of 2 to 4 extensions
        cycle_length = random.randint(2, 4)
        ext_names = ["ext-{}-{}".format(iteration, idx) for idx in range(cycle_length)]

        for idx in range(cycle_length):
            ext_name = ext_names[idx]
            # Each extension declares it should run before the next one in the cycle
            next_idx = (idx + 1) % cycle_length
            before_list = [ext_names[next_idx]]

            def make_cb(name):
                def cb():
                    return name
                return cb

            manager.register(
                hook_name,
                make_cb(ext_name),
                priority=HookPriority.NORMAL,
                extension_name=ext_name,
                before=before_list
            )

        raised = False
        caught_error = None
        try:
            manager.execute(hook_name)
        except HookOrderingError as err:
            raised = True
            caught_error = err

        if raised is not True:
            errmsg = (
                "Iteration {}: Expected HookOrderingError for circular constraints "
                "among extensions: {}"
            ).format(iteration, ext_names)
            raise AssertionError(errmsg)

        if caught_error.hook_name != hook_name:
            errmsg = "Iteration {}: Expected hook_name '{}', got '{}'".format(
                iteration, hook_name, caught_error.hook_name
            )
            raise AssertionError(errmsg)

    return
