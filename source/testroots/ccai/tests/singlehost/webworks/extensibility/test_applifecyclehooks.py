"""
    Tests for the AppLifecycleHooks class.

    This module contains unit tests and property-based tests for the
    AppLifecycleHooks class including hook name constants, application
    lifecycle hook execution ordering, and error continuation behavior.
"""

import random

from ccai.webworks.extensibility.datastructures import HookPriority
from ccai.webworks.extensibility.hookmanager import HookManager
from ccai.webworks.extensibility.applifecyclehooks import (
    APP_LIFECYCLE_HOOKS,
    ON_APP_INIT,
    ON_APP_READY,
    ON_APP_SHUTDOWN,
    ON_CONFIG_LOADED,
    ON_ROUTES_REGISTERED,
    AppLifecycleHooks,
)


# =============================================================================
# Test Helpers
# =============================================================================

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
        Test that all application lifecycle hook name constants are strings.
    """
    if not isinstance(ON_APP_INIT, str):
        errmsg = "ON_APP_INIT should be a string, got {}".format(type(ON_APP_INIT))
        raise AssertionError(errmsg)

    if not isinstance(ON_APP_READY, str):
        errmsg = "ON_APP_READY should be a string, got {}".format(type(ON_APP_READY))
        raise AssertionError(errmsg)

    if not isinstance(ON_APP_SHUTDOWN, str):
        errmsg = "ON_APP_SHUTDOWN should be a string, got {}".format(type(ON_APP_SHUTDOWN))
        raise AssertionError(errmsg)

    if not isinstance(ON_CONFIG_LOADED, str):
        errmsg = "ON_CONFIG_LOADED should be a string, got {}".format(type(ON_CONFIG_LOADED))
        raise AssertionError(errmsg)

    if not isinstance(ON_ROUTES_REGISTERED, str):
        errmsg = "ON_ROUTES_REGISTERED should be a string, got {}".format(type(ON_ROUTES_REGISTERED))
        raise AssertionError(errmsg)

    return


def test_hook_name_constants_have_expected_values():
    """
        Test that hook name constants have the expected string values.
    """
    if ON_APP_INIT != "on_app_init":
        errmsg = "ON_APP_INIT should be 'on_app_init', got '{}'".format(ON_APP_INIT)
        raise AssertionError(errmsg)

    if ON_APP_READY != "on_app_ready":
        errmsg = "ON_APP_READY should be 'on_app_ready', got '{}'".format(ON_APP_READY)
        raise AssertionError(errmsg)

    if ON_APP_SHUTDOWN != "on_app_shutdown":
        errmsg = "ON_APP_SHUTDOWN should be 'on_app_shutdown', got '{}'".format(ON_APP_SHUTDOWN)
        raise AssertionError(errmsg)

    if ON_CONFIG_LOADED != "on_config_loaded":
        errmsg = "ON_CONFIG_LOADED should be 'on_config_loaded', got '{}'".format(ON_CONFIG_LOADED)
        raise AssertionError(errmsg)

    if ON_ROUTES_REGISTERED != "on_routes_registered":
        errmsg = "ON_ROUTES_REGISTERED should be 'on_routes_registered', got '{}'".format(ON_ROUTES_REGISTERED)
        raise AssertionError(errmsg)

    return


def test_app_lifecycle_hooks_list_contains_all_hooks():
    """
        Test that APP_LIFECYCLE_HOOKS contains all five hook names.
    """
    expected_hooks = [
        ON_APP_INIT,
        ON_APP_READY,
        ON_APP_SHUTDOWN,
        ON_CONFIG_LOADED,
        ON_ROUTES_REGISTERED,
    ]

    if len(APP_LIFECYCLE_HOOKS) != len(expected_hooks):
        errmsg = "Expected {} hooks in list, got {}".format(
            len(expected_hooks), len(APP_LIFECYCLE_HOOKS)
        )
        raise AssertionError(errmsg)

    for hook_name in expected_hooks:
        if hook_name not in APP_LIFECYCLE_HOOKS:
            errmsg = "Hook '{}' not found in APP_LIFECYCLE_HOOKS".format(hook_name)
            raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for AppLifecycleHooks
# =============================================================================

def test_app_lifecycle_hooks_initial_state():
    """
        Test that a newly created AppLifecycleHooks has correct initial state.
    """
    manager = HookManager()
    lifecycle = AppLifecycleHooks(hook_manager=manager)

    if lifecycle.hook_manager is not manager:
        errmsg = "hook_manager property should return the provided HookManager"
        raise AssertionError(errmsg)

    return


def test_fire_on_app_init_calls_all_callbacks():
    """
        Test that fire_on_app_init calls all registered callbacks.
    """
    manager = HookManager()
    lifecycle = AppLifecycleHooks(hook_manager=manager)

    call_log = []
    manager.register(ON_APP_INIT, _make_logging_callback("init-a"), extension_name="ext-a")
    manager.register(ON_APP_INIT, _make_logging_callback("init-b"), extension_name="ext-b")

    results = lifecycle.fire_on_app_init(call_log)

    if len(call_log) != 2:
        errmsg = "Expected 2 calls, got {}".format(len(call_log))
        raise AssertionError(errmsg)

    if len(results) != 2:
        errmsg = "Expected 2 results, got {}".format(len(results))
        raise AssertionError(errmsg)

    return


def test_fire_on_app_ready_calls_all_callbacks():
    """
        Test that fire_on_app_ready calls all registered callbacks.
    """
    manager = HookManager()
    lifecycle = AppLifecycleHooks(hook_manager=manager)

    call_log = []
    manager.register(ON_APP_READY, _make_logging_callback("ready-a"), extension_name="ext-a")
    manager.register(ON_APP_READY, _make_logging_callback("ready-b"), extension_name="ext-b")

    results = lifecycle.fire_on_app_ready(call_log)

    if len(call_log) != 2:
        errmsg = "Expected 2 calls, got {}".format(len(call_log))
        raise AssertionError(errmsg)

    if len(results) != 2:
        errmsg = "Expected 2 results, got {}".format(len(results))
        raise AssertionError(errmsg)

    return


def test_fire_on_app_shutdown_calls_all_callbacks():
    """
        Test that fire_on_app_shutdown calls all registered callbacks.
    """
    manager = HookManager()
    lifecycle = AppLifecycleHooks(hook_manager=manager)

    call_log = []
    manager.register(ON_APP_SHUTDOWN, _make_logging_callback("shutdown-a"), extension_name="ext-a")

    lifecycle.fire_on_app_shutdown(call_log)

    if len(call_log) != 1:
        errmsg = "Expected 1 call, got {}".format(len(call_log))
        raise AssertionError(errmsg)

    return


def test_fire_on_config_loaded_calls_all_callbacks():
    """
        Test that fire_on_config_loaded calls all registered callbacks.
    """
    manager = HookManager()
    lifecycle = AppLifecycleHooks(hook_manager=manager)

    call_log = []
    manager.register(ON_CONFIG_LOADED, _make_logging_callback("config-a"), extension_name="ext-a")
    manager.register(ON_CONFIG_LOADED, _make_logging_callback("config-b"), extension_name="ext-b")

    lifecycle.fire_on_config_loaded(call_log)

    if len(call_log) != 2:
        errmsg = "Expected 2 calls, got {}".format(len(call_log))
        raise AssertionError(errmsg)

    return


def test_fire_on_routes_registered_calls_all_callbacks():
    """
        Test that fire_on_routes_registered calls all registered callbacks.
    """
    manager = HookManager()
    lifecycle = AppLifecycleHooks(hook_manager=manager)

    call_log = []
    manager.register(ON_ROUTES_REGISTERED, _make_logging_callback("routes-a"), extension_name="ext-a")

    lifecycle.fire_on_routes_registered(call_log)

    if len(call_log) != 1:
        errmsg = "Expected 1 call, got {}".format(len(call_log))
        raise AssertionError(errmsg)

    return


def test_fire_hooks_with_no_registrations():
    """
        Test that firing hooks with no registered callbacks does not raise errors.
    """
    manager = HookManager()
    lifecycle = AppLifecycleHooks(hook_manager=manager)

    call_log = []

    lifecycle.fire_on_app_init(call_log)
    lifecycle.fire_on_app_ready(call_log)
    lifecycle.fire_on_app_shutdown(call_log)
    lifecycle.fire_on_config_loaded(call_log)
    lifecycle.fire_on_routes_registered(call_log)

    if len(call_log) != 0:
        errmsg = "Expected empty call log with no hooks, got {} entries".format(len(call_log))
        raise AssertionError(errmsg)

    return


def test_fire_on_app_init_continues_on_hook_error():
    """
        Test that fire_on_app_init continues executing remaining callbacks
        when one callback raises an exception. This validates requirement 6.8.
    """
    manager = HookManager()
    lifecycle = AppLifecycleHooks(hook_manager=manager)

    call_log = []

    def failing_callback(log: list):
        log.append("failing")
        raise RuntimeError("Hook failure")

    manager.register(
        ON_APP_INIT, _make_logging_callback("before-fail"),
        priority=HookPriority.HIGH, extension_name="ext-before"
    )
    manager.register(
        ON_APP_INIT, failing_callback,
        priority=HookPriority.NORMAL, extension_name="ext-fail"
    )
    manager.register(
        ON_APP_INIT, _make_logging_callback("after-fail"),
        priority=HookPriority.LOW, extension_name="ext-after"
    )

    results = lifecycle.fire_on_app_init(call_log)

    if len(call_log) != 3:
        errmsg = (
            "Expected 3 callbacks to execute (error should not stop others), "
            "got {}. Call log: {}"
        ).format(len(call_log), call_log)
        raise AssertionError(errmsg)

    if len(results) != 3:
        errmsg = "Expected 3 results (including None for failed callback), got {}".format(
            len(results)
        )
        raise AssertionError(errmsg)

    return



# =============================================================================
# Property Tests
# =============================================================================

def test_property_19_application_lifecycle_hooks_execution():
    """
        Property 19: Application Lifecycle Hooks Execution

        For any application startup, the on_app_init hook SHALL be called
        during initialization, on_config_loaded after configuration loading,
        on_routes_registered after route registration, and on_app_ready when
        ready to serve.

        This property verifies that when the application lifecycle hooks are
        fired in the expected order (init -> config_loaded -> routes_registered
        -> ready), the callbacks for each phase execute in the correct sequence
        and all registered callbacks are invoked.

        **Validates: Requirements 6.1, 6.2, 6.4, 6.5**
    """
    for iteration in range(100):
        manager = HookManager()
        lifecycle = AppLifecycleHooks(hook_manager=manager)

        # Generate a random number of extensions (1 to 5)
        num_extensions = random.randint(1, 5)

        # Track the global call order across all hook types
        global_call_log = []

        for ext_idx in range(num_extensions):
            ext_name = "ext-{}-{}".format(iteration, ext_idx)
            priority = random.randint(0, 100)

            def make_init_cb(name):
                def cb(log: list):
                    log.append(("on_app_init", name))
                    return None
                return cb

            def make_config_cb(name):
                def cb(log: list):
                    log.append(("on_config_loaded", name))
                    return None
                return cb

            def make_routes_cb(name):
                def cb(log: list):
                    log.append(("on_routes_registered", name))
                    return None
                return cb

            def make_ready_cb(name):
                def cb(log: list):
                    log.append(("on_app_ready", name))
                    return None
                return cb

            manager.register(
                ON_APP_INIT, make_init_cb(ext_name),
                priority=priority, extension_name=ext_name
            )
            manager.register(
                ON_CONFIG_LOADED, make_config_cb(ext_name),
                priority=priority, extension_name=ext_name
            )
            manager.register(
                ON_ROUTES_REGISTERED, make_routes_cb(ext_name),
                priority=priority, extension_name=ext_name
            )
            manager.register(
                ON_APP_READY, make_ready_cb(ext_name),
                priority=priority, extension_name=ext_name
            )

        # Simulate application lifecycle:
        # init -> config_loaded -> routes_registered -> ready
        lifecycle.fire_on_app_init(global_call_log)
        lifecycle.fire_on_config_loaded(global_call_log)
        lifecycle.fire_on_routes_registered(global_call_log)
        lifecycle.fire_on_app_ready(global_call_log)

        # Collect indices for each hook type
        init_indices = []
        config_indices = []
        routes_indices = []
        ready_indices = []

        for idx, entry in enumerate(global_call_log):
            hook_type = entry[0]
            if hook_type == "on_app_init":
                init_indices.append(idx)
            elif hook_type == "on_config_loaded":
                config_indices.append(idx)
            elif hook_type == "on_routes_registered":
                routes_indices.append(idx)
            elif hook_type == "on_app_ready":
                ready_indices.append(idx)

        # Verify we got the expected number of calls for each hook type
        if len(init_indices) != num_extensions:
            errmsg = "Iteration {}: Expected {} on_app_init calls, got {}".format(
                iteration, num_extensions, len(init_indices)
            )
            raise AssertionError(errmsg)

        if len(config_indices) != num_extensions:
            errmsg = "Iteration {}: Expected {} on_config_loaded calls, got {}".format(
                iteration, num_extensions, len(config_indices)
            )
            raise AssertionError(errmsg)

        if len(routes_indices) != num_extensions:
            errmsg = "Iteration {}: Expected {} on_routes_registered calls, got {}".format(
                iteration, num_extensions, len(routes_indices)
            )
            raise AssertionError(errmsg)

        if len(ready_indices) != num_extensions:
            errmsg = "Iteration {}: Expected {} on_app_ready calls, got {}".format(
                iteration, num_extensions, len(ready_indices)
            )
            raise AssertionError(errmsg)

        # Verify ordering: all init < all config < all routes < all ready
        if len(init_indices) > 0 and len(config_indices) > 0:
            max_init = max(init_indices)
            min_config = min(config_indices)
            if max_init >= min_config:
                errmsg = (
                    "Iteration {}: on_app_init hooks must all execute before "
                    "on_config_loaded hooks. Max init index: {}, min config index: {}"
                ).format(iteration, max_init, min_config)
                raise AssertionError(errmsg)

        if len(config_indices) > 0 and len(routes_indices) > 0:
            max_config = max(config_indices)
            min_routes = min(routes_indices)
            if max_config >= min_routes:
                errmsg = (
                    "Iteration {}: on_config_loaded hooks must all execute before "
                    "on_routes_registered hooks. Max config index: {}, min routes index: {}"
                ).format(iteration, max_config, min_routes)
                raise AssertionError(errmsg)

        if len(routes_indices) > 0 and len(ready_indices) > 0:
            max_routes = max(routes_indices)
            min_ready = min(ready_indices)
            if max_routes >= min_ready:
                errmsg = (
                    "Iteration {}: on_routes_registered hooks must all execute before "
                    "on_app_ready hooks. Max routes index: {}, min ready index: {}"
                ).format(iteration, max_routes, min_ready)
                raise AssertionError(errmsg)

    return
