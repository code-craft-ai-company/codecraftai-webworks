"""
    Tests for error isolation in the extensibility system.

    This module contains unit tests and property-based tests verifying
    that extension errors during initialization and hook execution are
    properly isolated, logged, and reported through the on_extension_error
    hook. It also tests safe mode behavior.
"""

import logging
import random
import string

from typing import Any, Dict, List, Optional

from automojo.webworks.extensibility.context import ExtensionContext
from automojo.webworks.extensibility.datastructures import ExtensionErrorInfo
from automojo.webworks.extensibility.datastructures import ExtensionState
from automojo.webworks.extensibility.datastructures import HookPriority
from automojo.webworks.extensibility.extension import Extension
from automojo.webworks.extensibility.hookmanager import HookManager
from automojo.webworks.extensibility.registry import ExtensionRegistry


# =============================================================================
# Test Helpers
# =============================================================================

class _FakeAppContext:
    """
        A fake application context for testing purposes.
    """

    def __init__(
        self,
        config: Optional[Any] = None,
        endpoint_registry: Optional[Any] = None,
        url_node_map: Optional[Any] = None,
        middleware: Optional[List[Any]] = None,
        extension_registry: Optional[Any] = None
    ):
        self.config = config if config is not None else {}
        self.endpoint_registry = endpoint_registry
        self.url_node_map = url_node_map
        self.middleware = middleware if middleware is not None else []
        self.extension_registry = extension_registry
        self._loggers: Dict[str, logging.Logger] = {}
        return

    def get_logger(self, name: str) -> logging.Logger:
        if name not in self._loggers:
            self._loggers[name] = logging.getLogger(name)
        rtnval = self._loggers[name]
        return rtnval


class _GoodExtension(Extension):
    """
        A well-behaved extension that initializes without error.
    """

    name = "good-ext"
    version = "1.0.0"
    description = "A good extension"
    dependencies = []
    optional_dependencies = []


class _FailingInitExtension(Extension):
    """
        An extension that raises during initialize().
    """

    name = "failing-init"
    version = "1.0.0"
    description = "Fails on init"
    dependencies = []
    optional_dependencies = []

    def initialize(self, context: 'ExtensionContext') -> None:
        raise RuntimeError("Initialization exploded")


class _FailingHookExtension(Extension):
    """
        An extension whose hook callback raises.
    """

    name = "failing-hook"
    version = "1.0.0"
    description = "Fails in hook"
    dependencies = []
    optional_dependencies = []


class _CoreExtension(Extension):
    """
        A core extension for safe mode testing.
    """

    name = "core-ext"
    version = "1.0.0"
    description = "Core extension"
    dependencies = []
    optional_dependencies = []
    core = True


class _NonCoreExtension(Extension):
    """
        A non-core extension for safe mode testing.
    """

    name = "noncore-ext"
    version = "1.0.0"
    description = "Non-core extension"
    dependencies = []
    optional_dependencies = []
    core = False


def _create_named_extension(
    name: str,
    deps: Optional[List[str]] = None,
    opt_deps: Optional[List[str]] = None,
    fail_on_init: bool = False,
    is_core: bool = False
) -> Extension:
    """
        Create a concrete Extension instance with the given name.

        :param name: The extension name.
        :param deps: List of required dependency names.
        :param opt_deps: List of optional dependency names.
        :param fail_on_init: If True, the extension raises during initialize().
        :param is_core: If True, the extension is marked as core.

        :returns: An Extension instance.
    """
    if deps is None:
        deps = []

    if opt_deps is None:
        opt_deps = []

    attrs = {
        "name": name,
        "version": "1.0.0",
        "description": "Dynamic extension {}".format(name),
        "dependencies": deps,
        "optional_dependencies": opt_deps,
        "core": is_core,
    }

    if fail_on_init is True:
        def _failing_init(self, context):
            raise RuntimeError("Init failed for {}".format(name))
        attrs["initialize"] = _failing_init

    ext_cls = type(
        "DynExtension_{}".format(name),
        (Extension,),
        attrs
    )

    instance = ext_cls()
    return instance


def _generate_random_string(min_length: int = 3, max_length: int = 15) -> str:
    """
        Generate a random alphanumeric string.
    """
    length = random.randint(min_length, max_length)
    result = "".join(random.choices(string.ascii_lowercase + string.digits, k=length))
    return result


# =============================================================================
# Unit Tests for Error Isolation in Initialization
# =============================================================================

def test_failing_init_sets_error_state_and_continues():
    """
        Test that a failing extension during initialize_all() is marked
        ERROR and other extensions still initialize successfully.
    """
    app_ctx = _FakeAppContext()
    registry = ExtensionRegistry(app_context=app_ctx)

    good_ext = _GoodExtension()
    failing_ext = _FailingInitExtension()

    registry.register(good_ext)
    registry.register(failing_ext)

    registry.initialize_all()

    # The good extension should be INITIALIZED
    good_state = registry.get_state("good-ext")
    if good_state != ExtensionState.INITIALIZED:
        errmsg = "Expected good-ext to be INITIALIZED, got {}".format(good_state)
        raise AssertionError(errmsg)

    # The failing extension should be ERROR
    failing_state = registry.get_state("failing-init")
    if failing_state != ExtensionState.ERROR:
        errmsg = "Expected failing-init to be ERROR, got {}".format(failing_state)
        raise AssertionError(errmsg)

    # Error count should be incremented
    error_count = registry.get_error_count("failing-init")
    if error_count < 1:
        errmsg = "Expected error count >= 1 for failing-init, got {}".format(error_count)
        raise AssertionError(errmsg)

    return


def test_failing_init_fires_on_extension_error_hook():
    """
        Test that when an extension fails during initialization,
        the on_extension_error hook is fired with error info.
    """
    app_ctx = _FakeAppContext()
    registry = ExtensionRegistry(app_context=app_ctx)

    error_reports = []

    def error_handler(error_info):
        error_reports.append(error_info)

    registry.hook_manager.register(
        "on_extension_error",
        error_handler,
        priority=HookPriority.NORMAL,
        extension_name="error-monitor"
    )

    failing_ext = _FailingInitExtension()
    registry.register(failing_ext)

    registry.initialize_all()

    if len(error_reports) != 1:
        errmsg = "Expected 1 error report, got {}".format(len(error_reports))
        raise AssertionError(errmsg)

    report = error_reports[0]
    if not isinstance(report, ExtensionErrorInfo):
        errmsg = "Expected ExtensionErrorInfo, got {}".format(type(report))
        raise AssertionError(errmsg)

    if report.extension_name != "failing-init":
        errmsg = "Expected extension_name 'failing-init', got '{}'".format(report.extension_name)
        raise AssertionError(errmsg)

    if report.hook_name != "initialize":
        errmsg = "Expected hook_name 'initialize', got '{}'".format(report.hook_name)
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for Error Isolation in Hook Execution
# =============================================================================

def test_hook_error_continues_with_other_hooks():
    """
        Test that when a hook callback raises, execution continues
        with other hooks and the error is logged.
    """
    manager = HookManager()
    call_log = []

    def good_callback():
        call_log.append("good")
        return "good-result"

    def failing_callback():
        raise RuntimeError("Hook exploded")

    manager.register("test_hook", failing_callback, priority=HookPriority.HIGH, extension_name="ext-bad")
    manager.register("test_hook", good_callback, priority=HookPriority.LOW, extension_name="ext-good")

    results = manager.execute("test_hook")

    # Should have 2 results: None for failed, "good-result" for good
    if len(results) != 2:
        errmsg = "Expected 2 results, got {}".format(len(results))
        raise AssertionError(errmsg)

    if results[0] is not None:
        errmsg = "Expected None for failed callback, got {}".format(results[0])
        raise AssertionError(errmsg)

    if results[1] != "good-result":
        errmsg = "Expected 'good-result', got {}".format(results[1])
        raise AssertionError(errmsg)

    if "good" not in call_log:
        errmsg = "Expected 'good' in call_log, got {}".format(call_log)
        raise AssertionError(errmsg)

    return


def test_hook_error_callback_is_invoked():
    """
        Test that the error_callback parameter is invoked when a
        hook callback raises an exception.
    """
    manager = HookManager()
    error_reports = []

    def failing_callback():
        raise RuntimeError("Hook exploded")

    def good_callback():
        return "ok"

    def on_error(ext_name, hook_name, exc, tb_str):
        error_reports.append({
            "ext_name": ext_name,
            "hook_name": hook_name,
            "exception": exc,
        })

    manager.register("test_hook", failing_callback, priority=HookPriority.HIGH, extension_name="ext-bad")
    manager.register("test_hook", good_callback, priority=HookPriority.LOW, extension_name="ext-good")

    results = manager.execute("test_hook", error_callback=on_error)

    if len(error_reports) != 1:
        errmsg = "Expected 1 error report, got {}".format(len(error_reports))
        raise AssertionError(errmsg)

    report = error_reports[0]
    if report["ext_name"] != "ext-bad":
        errmsg = "Expected ext_name 'ext-bad', got '{}'".format(report["ext_name"])
        raise AssertionError(errmsg)

    if report["hook_name"] != "test_hook":
        errmsg = "Expected hook_name 'test_hook', got '{}'".format(report["hook_name"])
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for Safe Mode
# =============================================================================

def test_safe_mode_only_initializes_core_extensions():
    """
        Test that safe mode only initializes extensions marked as core.
    """
    app_ctx = _FakeAppContext()
    registry = ExtensionRegistry(app_context=app_ctx, safe_mode=True)

    core_ext = _CoreExtension()
    noncore_ext = _NonCoreExtension()

    registry.register(core_ext)
    registry.register(noncore_ext)

    registry.initialize_all()

    core_state = registry.get_state("core-ext")
    if core_state != ExtensionState.INITIALIZED:
        errmsg = "Expected core-ext to be INITIALIZED, got {}".format(core_state)
        raise AssertionError(errmsg)

    noncore_state = registry.get_state("noncore-ext")
    if noncore_state != ExtensionState.REGISTERED:
        errmsg = "Expected noncore-ext to remain REGISTERED, got {}".format(noncore_state)
        raise AssertionError(errmsg)

    return


def test_safe_mode_flag_property():
    """
        Test that the safe_mode property reflects the constructor argument.
    """
    app_ctx = _FakeAppContext()

    registry_normal = ExtensionRegistry(app_context=app_ctx)
    if registry_normal.safe_mode is not False:
        errmsg = "Expected safe_mode False by default, got {}".format(registry_normal.safe_mode)
        raise AssertionError(errmsg)

    registry_safe = ExtensionRegistry(app_context=app_ctx, safe_mode=True)
    if registry_safe.safe_mode is not True:
        errmsg = "Expected safe_mode True, got {}".format(registry_safe.safe_mode)
        raise AssertionError(errmsg)

    return


# =============================================================================
# Property Test: Property 32 - Error Isolation
# =============================================================================

def test_property_32_error_isolation():
    """
        Property 32: Error Isolation

        For any extension that raises an exception during initialization
        or in a hook, the framework SHALL log the error, mark the
        extension as errored, and continue with other extensions/hooks.

        **Validates: Requirements 14.1, 14.2, 6.8**
    """
    for iteration in range(100):
        app_ctx = _FakeAppContext()
        registry = ExtensionRegistry(app_context=app_ctx)

        # Generate a random mix of good and failing extensions
        num_good = random.randint(1, 5)
        num_failing = random.randint(1, 3)

        good_names = set()
        while len(good_names) < num_good:
            name = "good-" + _generate_random_string(3, 10)
            good_names.add(name)

        failing_names = set()
        while len(failing_names) < num_failing:
            name = "fail-" + _generate_random_string(3, 10)
            if name not in good_names:
                failing_names.add(name)

        # Register good extensions
        for name in good_names:
            ext = _create_named_extension(name)
            registry.register(ext)

        # Register failing extensions
        for name in failing_names:
            ext = _create_named_extension(name, fail_on_init=True)
            registry.register(ext)

        # Track on_extension_error hook calls
        error_reports = []

        def error_handler(error_info):
            error_reports.append(error_info)

        registry.hook_manager.register(
            "on_extension_error",
            error_handler,
            priority=HookPriority.NORMAL,
            extension_name="error-monitor"
        )

        # Initialize all - should not raise
        registry.initialize_all()

        # Verify: all good extensions should be INITIALIZED
        for name in good_names:
            state = registry.get_state(name)
            if state != ExtensionState.INITIALIZED:
                errmsg = (
                    "Iteration {}: Expected good extension '{}' to be INITIALIZED, "
                    "got {}".format(iteration, name, state)
                )
                raise AssertionError(errmsg)

        # Verify: all failing extensions should be ERROR
        for name in failing_names:
            state = registry.get_state(name)
            if state != ExtensionState.ERROR:
                errmsg = (
                    "Iteration {}: Expected failing extension '{}' to be ERROR, "
                    "got {}".format(iteration, name, state)
                )
                raise AssertionError(errmsg)

        # Verify: error counts should be incremented for failing extensions
        for name in failing_names:
            count = registry.get_error_count(name)
            if count < 1:
                errmsg = (
                    "Iteration {}: Expected error count >= 1 for '{}', "
                    "got {}".format(iteration, name, count)
                )
                raise AssertionError(errmsg)

        # Verify: on_extension_error hook was fired for each failing extension
        reported_names = set()
        for report in error_reports:
            reported_names.add(report.extension_name)

        for name in failing_names:
            if name not in reported_names:
                errmsg = (
                    "Iteration {}: Expected on_extension_error for '{}' "
                    "but it was not reported".format(iteration, name)
                )
                raise AssertionError(errmsg)

        # Verify: hook execution continues after errors (Req 14.2, 6.8)
        hook_manager = registry.hook_manager
        hook_call_log = []

        def failing_hook():
            raise RuntimeError("Hook failure")

        def good_hook():
            hook_call_log.append("executed")
            return "ok"

        hook_manager.register(
            "test_hook_{}".format(iteration),
            failing_hook,
            priority=HookPriority.HIGH,
            extension_name="ext-failing"
        )
        hook_manager.register(
            "test_hook_{}".format(iteration),
            good_hook,
            priority=HookPriority.LOW,
            extension_name="ext-good"
        )

        results = hook_manager.execute("test_hook_{}".format(iteration))

        if len(results) != 2:
            errmsg = (
                "Iteration {}: Expected 2 hook results, got {}".format(
                    iteration, len(results)
                )
            )
            raise AssertionError(errmsg)

        if results[1] != "ok":
            errmsg = (
                "Iteration {}: Expected good hook to return 'ok', "
                "got {}".format(iteration, results[1])
            )
            raise AssertionError(errmsg)

        if "executed" not in hook_call_log:
            errmsg = (
                "Iteration {}: Good hook was not executed after failing hook".format(
                    iteration
                )
            )
            raise AssertionError(errmsg)

    return
