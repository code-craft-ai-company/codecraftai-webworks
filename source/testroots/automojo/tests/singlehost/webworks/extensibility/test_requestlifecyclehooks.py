"""
    Tests for the RequestLifecycleHooks class.

    This module contains unit tests and property-based tests for the
    RequestLifecycleHooks class including hook name constants, lifecycle
    hook execution ordering, before_first_request idempotency, and
    before_request short-circuiting behavior.
"""

import random
import string

from typing import Any, List, Optional

from automojo.webworks.extensibility.datastructures import HookPriority
from automojo.webworks.extensibility.hookmanager import HookManager
from automojo.webworks.extensibility.requestlifecyclehooks import (
    AFTER_REQUEST,
    BEFORE_FIRST_REQUEST,
    BEFORE_REQUEST,
    ON_REQUEST_ERROR,
    REQUEST_LIFECYCLE_HOOKS,
    TEARDOWN_REQUEST,
    RequestLifecycleHooks,
)


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


def _make_logging_callback(label: str):
    """
        Create a callback that appends its label to a shared call log list.

        :param label: The label to append when the callback is invoked.

        :returns: A callable that accepts a call_log list and appends the label.
    """
    def callback(call_log: list):
        call_log.append(label)
        return None
    return callback



# =============================================================================
# Unit Tests for Hook Name Constants
# =============================================================================

def test_hook_name_constants_are_strings():
    """
        Test that all request lifecycle hook name constants are strings.
    """
    if not isinstance(BEFORE_REQUEST, str):
        errmsg = "BEFORE_REQUEST should be a string, got {}".format(type(BEFORE_REQUEST))
        raise AssertionError(errmsg)

    if not isinstance(AFTER_REQUEST, str):
        errmsg = "AFTER_REQUEST should be a string, got {}".format(type(AFTER_REQUEST))
        raise AssertionError(errmsg)

    if not isinstance(BEFORE_FIRST_REQUEST, str):
        errmsg = "BEFORE_FIRST_REQUEST should be a string, got {}".format(type(BEFORE_FIRST_REQUEST))
        raise AssertionError(errmsg)

    if not isinstance(ON_REQUEST_ERROR, str):
        errmsg = "ON_REQUEST_ERROR should be a string, got {}".format(type(ON_REQUEST_ERROR))
        raise AssertionError(errmsg)

    if not isinstance(TEARDOWN_REQUEST, str):
        errmsg = "TEARDOWN_REQUEST should be a string, got {}".format(type(TEARDOWN_REQUEST))
        raise AssertionError(errmsg)

    return


def test_hook_name_constants_have_expected_values():
    """
        Test that hook name constants have the expected string values.
    """
    if BEFORE_REQUEST != "before_request":
        errmsg = "BEFORE_REQUEST should be 'before_request', got '{}'".format(BEFORE_REQUEST)
        raise AssertionError(errmsg)

    if AFTER_REQUEST != "after_request":
        errmsg = "AFTER_REQUEST should be 'after_request', got '{}'".format(AFTER_REQUEST)
        raise AssertionError(errmsg)

    if BEFORE_FIRST_REQUEST != "before_first_request":
        errmsg = "BEFORE_FIRST_REQUEST should be 'before_first_request', got '{}'".format(BEFORE_FIRST_REQUEST)
        raise AssertionError(errmsg)

    if ON_REQUEST_ERROR != "on_request_error":
        errmsg = "ON_REQUEST_ERROR should be 'on_request_error', got '{}'".format(ON_REQUEST_ERROR)
        raise AssertionError(errmsg)

    if TEARDOWN_REQUEST != "teardown_request":
        errmsg = "TEARDOWN_REQUEST should be 'teardown_request', got '{}'".format(TEARDOWN_REQUEST)
        raise AssertionError(errmsg)

    return


def test_request_lifecycle_hooks_list_contains_all_hooks():
    """
        Test that REQUEST_LIFECYCLE_HOOKS contains all five hook names.
    """
    expected_hooks = [
        BEFORE_REQUEST,
        AFTER_REQUEST,
        BEFORE_FIRST_REQUEST,
        ON_REQUEST_ERROR,
        TEARDOWN_REQUEST,
    ]

    if len(REQUEST_LIFECYCLE_HOOKS) != len(expected_hooks):
        errmsg = "Expected {} hooks in list, got {}".format(
            len(expected_hooks), len(REQUEST_LIFECYCLE_HOOKS)
        )
        raise AssertionError(errmsg)

    for hook_name in expected_hooks:
        if hook_name not in REQUEST_LIFECYCLE_HOOKS:
            errmsg = "Hook '{}' not found in REQUEST_LIFECYCLE_HOOKS".format(hook_name)
            raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for RequestLifecycleHooks
# =============================================================================

def test_request_lifecycle_hooks_initial_state():
    """
        Test that a newly created RequestLifecycleHooks has correct initial state.
    """
    manager = HookManager()
    lifecycle = RequestLifecycleHooks(hook_manager=manager)

    if lifecycle.hook_manager is not manager:
        errmsg = "hook_manager property should return the provided HookManager"
        raise AssertionError(errmsg)

    if lifecycle.first_request_handled is not False:
        errmsg = "first_request_handled should be False initially"
        raise AssertionError(errmsg)

    return


def test_fire_before_first_request_fires_once():
    """
        Test that fire_before_first_request only fires the hook on the first call.
    """
    manager = HookManager()
    lifecycle = RequestLifecycleHooks(hook_manager=manager)

    call_log = []
    callback = _make_logging_callback("first-req")
    manager.register(BEFORE_FIRST_REQUEST, callback, extension_name="ext-a")

    lifecycle.fire_before_first_request(call_log)

    if len(call_log) != 1:
        errmsg = "Expected 1 call after first fire, got {}".format(len(call_log))
        raise AssertionError(errmsg)

    if lifecycle.first_request_handled is not True:
        errmsg = "first_request_handled should be True after first fire"
        raise AssertionError(errmsg)

    # Second call should not fire the hook again
    lifecycle.fire_before_first_request(call_log)

    if len(call_log) != 1:
        errmsg = "Expected 1 call after second fire (idempotent), got {}".format(len(call_log))
        raise AssertionError(errmsg)

    return


def test_fire_before_request_returns_none_when_no_short_circuit():
    """
        Test that fire_before_request returns None when no callback returns a value.
    """
    manager = HookManager()
    lifecycle = RequestLifecycleHooks(hook_manager=manager)

    call_log = []
    callback = _make_logging_callback("before-req")
    manager.register(BEFORE_REQUEST, callback, extension_name="ext-a")

    result = lifecycle.fire_before_request(call_log)

    if result is not None:
        errmsg = "Expected None when no callback returns a value, got {}".format(result)
        raise AssertionError(errmsg)

    if len(call_log) != 1:
        errmsg = "Expected 1 call, got {}".format(len(call_log))
        raise AssertionError(errmsg)

    return


def test_fire_before_request_short_circuits_on_response():
    """
        Test that fire_before_request short-circuits when a callback returns a response.
    """
    manager = HookManager()
    lifecycle = RequestLifecycleHooks(hook_manager=manager)

    call_log = []
    short_circuit_response = {"status": 403, "body": "Forbidden"}

    def short_circuit_callback(log: list):
        log.append("short-circuit")
        return short_circuit_response

    def second_callback(log: list):
        log.append("should-not-run")
        return None

    manager.register(
        BEFORE_REQUEST, short_circuit_callback,
        priority=HookPriority.HIGH, extension_name="ext-auth"
    )
    manager.register(
        BEFORE_REQUEST, second_callback,
        priority=HookPriority.LOW, extension_name="ext-other"
    )

    result = lifecycle.fire_before_request(call_log)

    if result is not short_circuit_response:
        errmsg = "Expected short-circuit response, got {}".format(result)
        raise AssertionError(errmsg)

    if len(call_log) != 1:
        errmsg = "Expected only 1 callback to run (short-circuit), got {}".format(len(call_log))
        raise AssertionError(errmsg)

    if call_log[0] != "short-circuit":
        errmsg = "Expected 'short-circuit' in call log, got '{}'".format(call_log[0])
        raise AssertionError(errmsg)

    return


def test_fire_after_request_calls_all_callbacks():
    """
        Test that fire_after_request calls all registered callbacks.
    """
    manager = HookManager()
    lifecycle = RequestLifecycleHooks(hook_manager=manager)

    call_log = []
    manager.register(AFTER_REQUEST, _make_logging_callback("after-a"), extension_name="ext-a")
    manager.register(AFTER_REQUEST, _make_logging_callback("after-b"), extension_name="ext-b")

    results = lifecycle.fire_after_request(call_log)

    if len(call_log) != 2:
        errmsg = "Expected 2 calls, got {}".format(len(call_log))
        raise AssertionError(errmsg)

    if len(results) != 2:
        errmsg = "Expected 2 results, got {}".format(len(results))
        raise AssertionError(errmsg)

    return


def test_fire_on_request_error_calls_all_callbacks():
    """
        Test that fire_on_request_error calls all registered callbacks.
    """
    manager = HookManager()
    lifecycle = RequestLifecycleHooks(hook_manager=manager)

    call_log = []
    manager.register(ON_REQUEST_ERROR, _make_logging_callback("error-a"), extension_name="ext-a")

    results = lifecycle.fire_on_request_error(call_log)

    if len(call_log) != 1:
        errmsg = "Expected 1 call, got {}".format(len(call_log))
        raise AssertionError(errmsg)

    return


def test_fire_teardown_request_calls_all_callbacks():
    """
        Test that fire_teardown_request calls all registered callbacks.
    """
    manager = HookManager()
    lifecycle = RequestLifecycleHooks(hook_manager=manager)

    call_log = []
    manager.register(TEARDOWN_REQUEST, _make_logging_callback("teardown-a"), extension_name="ext-a")
    manager.register(TEARDOWN_REQUEST, _make_logging_callback("teardown-b"), extension_name="ext-b")

    results = lifecycle.fire_teardown_request(call_log)

    if len(call_log) != 2:
        errmsg = "Expected 2 calls, got {}".format(len(call_log))
        raise AssertionError(errmsg)

    return


def test_fire_hooks_with_no_registrations():
    """
        Test that firing hooks with no registered callbacks does not raise errors.
    """
    manager = HookManager()
    lifecycle = RequestLifecycleHooks(hook_manager=manager)

    call_log = []

    lifecycle.fire_before_first_request(call_log)
    result = lifecycle.fire_before_request(call_log)
    lifecycle.fire_after_request(call_log)
    lifecycle.fire_on_request_error(call_log)
    lifecycle.fire_teardown_request(call_log)

    if result is not None:
        errmsg = "Expected None from fire_before_request with no hooks, got {}".format(result)
        raise AssertionError(errmsg)

    if len(call_log) != 0:
        errmsg = "Expected empty call log with no hooks, got {} entries".format(len(call_log))
        raise AssertionError(errmsg)

    return



# =============================================================================
# Property Tests
# =============================================================================

def test_property_17_request_lifecycle_hooks_execution():
    """
        Property 17: Request Lifecycle Hooks Execution

        For any request processed by the framework, the before_request hooks
        SHALL be called before processing, after_request hooks SHALL be called
        after processing, and teardown_request hooks SHALL be called after the
        response is sent.

        **Validates: Requirements 5.1, 5.2, 5.5**
    """
    for iteration in range(100):
        manager = HookManager()
        lifecycle = RequestLifecycleHooks(hook_manager=manager)

        # Generate a random number of extensions (1 to 5)
        num_extensions = random.randint(1, 5)

        # Track the global call order across all hook types
        global_call_log = []

        for ext_idx in range(num_extensions):
            ext_name = "ext-{}-{}".format(iteration, ext_idx)
            priority = random.randint(0, 100)

            def make_before_cb(name):
                def cb(log: list):
                    log.append(("before_request", name))
                    return None
                return cb

            def make_after_cb(name):
                def cb(log: list):
                    log.append(("after_request", name))
                    return None
                return cb

            def make_teardown_cb(name):
                def cb(log: list):
                    log.append(("teardown_request", name))
                    return None
                return cb

            manager.register(
                BEFORE_REQUEST, make_before_cb(ext_name),
                priority=priority, extension_name=ext_name
            )
            manager.register(
                AFTER_REQUEST, make_after_cb(ext_name),
                priority=priority, extension_name=ext_name
            )
            manager.register(
                TEARDOWN_REQUEST, make_teardown_cb(ext_name),
                priority=priority, extension_name=ext_name
            )

        # Simulate request lifecycle: before -> (processing) -> after -> teardown
        lifecycle.fire_before_request(global_call_log)
        lifecycle.fire_after_request(global_call_log)
        lifecycle.fire_teardown_request(global_call_log)

        # Verify that all before_request calls come before all after_request calls
        # and all after_request calls come before all teardown_request calls
        before_indices = []
        after_indices = []
        teardown_indices = []

        for idx, entry in enumerate(global_call_log):
            hook_type = entry[0]
            if hook_type == "before_request":
                before_indices.append(idx)
            elif hook_type == "after_request":
                after_indices.append(idx)
            elif hook_type == "teardown_request":
                teardown_indices.append(idx)

        # Verify we got the expected number of calls
        if len(before_indices) != num_extensions:
            errmsg = "Iteration {}: Expected {} before_request calls, got {}".format(
                iteration, num_extensions, len(before_indices)
            )
            raise AssertionError(errmsg)

        if len(after_indices) != num_extensions:
            errmsg = "Iteration {}: Expected {} after_request calls, got {}".format(
                iteration, num_extensions, len(after_indices)
            )
            raise AssertionError(errmsg)

        if len(teardown_indices) != num_extensions:
            errmsg = "Iteration {}: Expected {} teardown_request calls, got {}".format(
                iteration, num_extensions, len(teardown_indices)
            )
            raise AssertionError(errmsg)

        # Verify ordering: all before < all after < all teardown
        if len(before_indices) > 0 and len(after_indices) > 0:
            max_before = max(before_indices)
            min_after = min(after_indices)
            if max_before >= min_after:
                errmsg = (
                    "Iteration {}: before_request hooks must all execute before "
                    "after_request hooks. Max before index: {}, min after index: {}"
                ).format(iteration, max_before, min_after)
                raise AssertionError(errmsg)

        if len(after_indices) > 0 and len(teardown_indices) > 0:
            max_after = max(after_indices)
            min_teardown = min(teardown_indices)
            if max_after >= min_teardown:
                errmsg = (
                    "Iteration {}: after_request hooks must all execute before "
                    "teardown_request hooks. Max after index: {}, min teardown index: {}"
                ).format(iteration, max_after, min_teardown)
                raise AssertionError(errmsg)

    return


def test_property_18_before_request_short_circuit():
    """
        Property 18: Before Request Short-Circuit

        For any before_request hook that returns a response, the framework
        SHALL short-circuit request processing and return that response
        without calling subsequent hooks or the handler.

        **Validates: Requirements 5.8**
    """
    for iteration in range(100):
        manager = HookManager()
        lifecycle = RequestLifecycleHooks(hook_manager=manager)

        # Generate a random number of extensions (2 to 6)
        num_extensions = random.randint(2, 6)

        # Randomly pick which extension will short-circuit
        short_circuit_idx = random.randint(0, num_extensions - 1)
        short_circuit_response = "response-{}-{}".format(iteration, short_circuit_idx)

        call_log = []

        # Register callbacks with ascending priorities so execution order
        # matches registration order
        for ext_idx in range(num_extensions):
            ext_name = "ext-{}-{}".format(iteration, ext_idx)
            priority = ext_idx  # Lower index = higher priority = runs first

            if ext_idx == short_circuit_idx:
                def make_short_circuit_cb(name, response):
                    def cb(log: list):
                        log.append(name)
                        return response
                    return cb

                manager.register(
                    BEFORE_REQUEST,
                    make_short_circuit_cb(ext_name, short_circuit_response),
                    priority=priority,
                    extension_name=ext_name
                )
            else:
                def make_normal_cb(name):
                    def cb(log: list):
                        log.append(name)
                        return None
                    return cb

                manager.register(
                    BEFORE_REQUEST,
                    make_normal_cb(ext_name),
                    priority=priority,
                    extension_name=ext_name
                )

        result = lifecycle.fire_before_request(call_log)

        # Verify the short-circuit response was returned
        if result != short_circuit_response:
            errmsg = (
                "Iteration {}: Expected short-circuit response '{}', got '{}'"
            ).format(iteration, short_circuit_response, result)
            raise AssertionError(errmsg)

        # Verify that only callbacks up to and including the short-circuit
        # callback were executed
        expected_call_count = short_circuit_idx + 1
        if len(call_log) != expected_call_count:
            errmsg = (
                "Iteration {}: Expected {} callbacks to run before short-circuit "
                "(short-circuit at index {}), got {} callbacks. Call log: {}"
            ).format(
                iteration, expected_call_count, short_circuit_idx,
                len(call_log), call_log
            )
            raise AssertionError(errmsg)

        # Verify no callbacks after the short-circuit index were called
        for log_idx, logged_name in enumerate(call_log):
            expected_ext = "ext-{}-{}".format(iteration, log_idx)
            if logged_name != expected_ext:
                errmsg = (
                    "Iteration {}: Expected callback '{}' at position {}, "
                    "got '{}'. Call log: {}"
                ).format(iteration, expected_ext, log_idx, logged_name, call_log)
                raise AssertionError(errmsg)

    return
