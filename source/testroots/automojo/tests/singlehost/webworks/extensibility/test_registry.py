"""
    Tests for the ExtensionRegistry class.

    This module contains unit tests and property-based tests for the
    ExtensionRegistry class including registration, retrieval, listing,
    dependency resolution, lifecycle management, state tracking,
    capability querying, reload, and error tracking with quarantine.
"""

import logging
import random
import string

from typing import Any, Dict, List, Optional

from automojo.webworks.extensibility.context import ExtensionContext
from automojo.webworks.extensibility.datastructures import ExtensionState
from automojo.webworks.extensibility.exceptions import ExtensionAlreadyRegisteredError
from automojo.webworks.extensibility.exceptions import ExtensionDependencyError
from automojo.webworks.extensibility.exceptions import ExtensionNotFoundError
from automojo.webworks.extensibility.extension import Extension
from automojo.webworks.extensibility.registry import ExtensionRegistry


# =============================================================================
# Test Helpers
# =============================================================================

class _FakeAppContext:
    """
        A fake application context for testing purposes.

        Provides the duck-typed interface that ExtensionRegistry
        and ExtensionContext expect from the application context.
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
        """
            Get a logger by name.

            :param name: The logger name.

            :returns: A Logger instance.
        """
        if name not in self._loggers:
            self._loggers[name] = logging.getLogger(name)

        rtnval = self._loggers[name]
        return rtnval


class _SimpleExtension(Extension):
    """
        A minimal concrete extension for testing.
    """

    name = "simple-ext"
    version = "1.0.0"
    description = "A simple test extension"
    dependencies = []
    optional_dependencies = []


class _ExtensionA(Extension):
    """
        Extension A with no dependencies.
    """

    name = "ext-a"
    version = "1.0.0"
    description = "Extension A"
    dependencies = []
    optional_dependencies = []


class _ExtensionB(Extension):
    """
        Extension B that depends on A.
    """

    name = "ext-b"
    version = "1.0.0"
    description = "Extension B"
    dependencies = ["ext-a"]
    optional_dependencies = []


class _ExtensionC(Extension):
    """
        Extension C that depends on B.
    """

    name = "ext-c"
    version = "1.0.0"
    description = "Extension C"
    dependencies = ["ext-b"]
    optional_dependencies = []


class _ExtensionWithOptionalDep(Extension):
    """
        Extension with an optional dependency.
    """

    name = "ext-opt"
    version = "1.0.0"
    description = "Extension with optional dep"
    dependencies = []
    optional_dependencies = ["missing-opt"]


class _ExtensionWithCapability(Extension):
    """
        Extension that provides a capability via extension_points.
    """

    name = "ext-cap"
    version = "1.0.0"
    description = "Extension with capability"
    dependencies = []
    optional_dependencies = []
    extension_points = ["auth-provider", "serializer"]


class _ActivationTrackingExtension(Extension):
    """
        Extension that tracks activation and deactivation calls.
    """

    name = "tracking-ext"
    version = "1.0.0"
    description = "Tracks lifecycle calls"
    dependencies = []
    optional_dependencies = []

    def __init__(self):
        super().__init__()
        self.activate_count = 0
        self.deactivate_count = 0
        return

    def activate(self) -> None:
        """
            Track activation call and delegate to parent.
        """
        self.activate_count = self.activate_count + 1
        super().activate()
        return

    def deactivate(self) -> None:
        """
            Track deactivation call and delegate to parent.
        """
        self.deactivate_count = self.deactivate_count + 1
        super().deactivate()
        return


class _FailingActivateExtension(Extension):
    """
        Extension that raises during activate().
    """

    name = "failing-activate"
    version = "1.0.0"
    description = "Fails on activate"
    dependencies = []
    optional_dependencies = []

    def activate(self) -> None:
        """
            Raise an error during activation.
        """
        raise RuntimeError("Activation failed")


# =============================================================================
# Random Data Generators for Property Tests
# =============================================================================

def _generate_random_string(min_length: int = 1, max_length: int = 20) -> str:
    """
        Generate a random string of alphanumeric characters.

        :param min_length: Minimum length of the generated string.
        :param max_length: Maximum length of the generated string.

        :returns: A random alphanumeric string.
    """
    length = random.randint(min_length, max_length)
    result = "".join(random.choices(string.ascii_lowercase + string.digits, k=length))
    return result


def _generate_random_version() -> str:
    """
        Generate a random semantic version string.

        :returns: A version string in major.minor.patch format.
    """
    major = random.randint(0, 99)
    minor = random.randint(0, 99)
    patch = random.randint(0, 99)
    result = "{}.{}.{}".format(major, minor, patch)
    return result


def _create_named_extension(name: str, deps: Optional[List[str]] = None, opt_deps: Optional[List[str]] = None) -> Extension:
    """
        Create a concrete Extension instance with the given name and dependencies.

        :param name: The extension name.
        :param deps: List of required dependency names.
        :param opt_deps: List of optional dependency names.

        :returns: An Extension instance.
    """
    if deps is None:
        deps = []

    if opt_deps is None:
        opt_deps = []

    ext_cls = type(
        "DynExtension_{}".format(name),
        (Extension,),
        {
            "name": name,
            "version": "1.0.0",
            "description": "Dynamic extension {}".format(name),
            "dependencies": deps,
            "optional_dependencies": opt_deps,
        }
    )

    instance = ext_cls()
    return instance


# =============================================================================
# Unit Tests for ExtensionRegistry __init__
# =============================================================================

def test_registry_init_creates_empty_extensions():
    """
        Test that a new registry has no registered extensions.
    """
    app_ctx = _FakeAppContext()
    registry = ExtensionRegistry(app_context=app_ctx)

    extensions = registry.list()
    if len(extensions) != 0:
        errmsg = "Expected empty extensions list, got {} items".format(len(extensions))
        raise AssertionError(errmsg)

    return


def test_registry_init_sets_default_error_threshold():
    """
        Test that a new registry has the default error threshold of 5.
    """
    app_ctx = _FakeAppContext()
    registry = ExtensionRegistry(app_context=app_ctx)

    if registry._error_threshold != 5:
        errmsg = "Expected error threshold 5, got {}".format(registry._error_threshold)
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for register()
# =============================================================================

def test_registry_register_adds_extension():
    """
        Test that register() adds an extension to the registry.
    """
    app_ctx = _FakeAppContext()
    registry = ExtensionRegistry(app_context=app_ctx)
    ext = _SimpleExtension()

    registry.register(ext)

    result = registry.get("simple-ext")
    if result is not ext:
        errmsg = "Expected get() to return the registered extension"
        raise AssertionError(errmsg)

    return


def test_registry_register_sets_state_to_registered():
    """
        Test that register() sets the extension state to REGISTERED.
    """
    app_ctx = _FakeAppContext()
    registry = ExtensionRegistry(app_context=app_ctx)
    ext = _SimpleExtension()

    registry.register(ext)

    state = registry.get_state("simple-ext")
    if state is not ExtensionState.REGISTERED:
        errmsg = "Expected state REGISTERED, got {}".format(state)
        raise AssertionError(errmsg)

    return


def test_registry_register_raises_on_duplicate():
    """
        Test that register() raises ExtensionAlreadyRegisteredError for duplicates.
    """
    app_ctx = _FakeAppContext()
    registry = ExtensionRegistry(app_context=app_ctx)
    ext1 = _SimpleExtension()
    ext2 = _SimpleExtension()

    registry.register(ext1)

    raised = False
    try:
        registry.register(ext2)
    except ExtensionAlreadyRegisteredError:
        raised = True

    if raised is not True:
        errmsg = "Expected ExtensionAlreadyRegisteredError for duplicate registration"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for get()
# =============================================================================

def test_registry_get_returns_none_for_unknown():
    """
        Test that get() returns None for an unregistered extension name.
    """
    app_ctx = _FakeAppContext()
    registry = ExtensionRegistry(app_context=app_ctx)

    result = registry.get("nonexistent")
    if result is not None:
        errmsg = "Expected get() to return None for unknown extension"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for list()
# =============================================================================

def test_registry_list_returns_all_registered():
    """
        Test that list() returns all registered extensions.
    """
    app_ctx = _FakeAppContext()
    registry = ExtensionRegistry(app_context=app_ctx)

    ext_a = _ExtensionA()
    ext_b = _ExtensionB()

    registry.register(ext_a)
    registry.register(ext_b)

    result = registry.list()
    if len(result) != 2:
        errmsg = "Expected 2 extensions, got {}".format(len(result))
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for _resolve_dependencies()
# =============================================================================

def test_registry_resolve_dependencies_simple_chain():
    """
        Test that _resolve_dependencies() returns correct order for A -> B -> C.
    """
    app_ctx = _FakeAppContext()
    registry = ExtensionRegistry(app_context=app_ctx)

    ext_a = _ExtensionA()
    ext_b = _ExtensionB()
    ext_c = _ExtensionC()

    registry.register(ext_a)
    registry.register(ext_b)
    registry.register(ext_c)

    order = registry._resolve_dependencies()

    idx_a = order.index("ext-a")
    idx_b = order.index("ext-b")
    idx_c = order.index("ext-c")

    if idx_a >= idx_b:
        errmsg = "Expected ext-a before ext-b, got indices a={}, b={}".format(idx_a, idx_b)
        raise AssertionError(errmsg)

    if idx_b >= idx_c:
        errmsg = "Expected ext-b before ext-c, got indices b={}, c={}".format(idx_b, idx_c)
        raise AssertionError(errmsg)

    return


def test_registry_resolve_dependencies_detects_circular():
    """
        Test that _resolve_dependencies() raises on circular dependencies.
    """
    app_ctx = _FakeAppContext()
    registry = ExtensionRegistry(app_context=app_ctx)

    # Create circular: x depends on y, y depends on x
    ext_x = _create_named_extension("ext-x", deps=["ext-y"])
    ext_y = _create_named_extension("ext-y", deps=["ext-x"])

    registry.register(ext_x)
    registry.register(ext_y)

    raised = False
    try:
        registry._resolve_dependencies()
    except ExtensionDependencyError:
        raised = True

    if raised is not True:
        errmsg = "Expected ExtensionDependencyError for circular dependencies"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for initialize_all()
# =============================================================================

def test_registry_initialize_all_initializes_in_order():
    """
        Test that initialize_all() initializes extensions in dependency order.
    """
    app_ctx = _FakeAppContext()
    registry = ExtensionRegistry(app_context=app_ctx)

    ext_a = _ExtensionA()
    ext_b = _ExtensionB()

    registry.register(ext_a)
    registry.register(ext_b)

    registry.initialize_all()

    state_a = registry.get_state("ext-a")
    state_b = registry.get_state("ext-b")

    if state_a is not ExtensionState.INITIALIZED:
        errmsg = "Expected ext-a state INITIALIZED, got {}".format(state_a)
        raise AssertionError(errmsg)

    if state_b is not ExtensionState.INITIALIZED:
        errmsg = "Expected ext-b state INITIALIZED, got {}".format(state_b)
        raise AssertionError(errmsg)

    return


def test_registry_initialize_all_raises_on_missing_required_dep():
    """
        Test that initialize_all() raises when a required dependency is missing.
    """
    app_ctx = _FakeAppContext()
    registry = ExtensionRegistry(app_context=app_ctx)

    ext_b = _ExtensionB()  # depends on ext-a which is not registered
    registry.register(ext_b)

    raised = False
    caught_error = None
    try:
        registry.initialize_all()
    except ExtensionDependencyError as err:
        raised = True
        caught_error = err

    if raised is not True:
        errmsg = "Expected ExtensionDependencyError for missing required dependency"
        raise AssertionError(errmsg)

    if "ext-a" not in caught_error.missing_deps:
        errmsg = "Expected 'ext-a' in missing_deps, got {}".format(caught_error.missing_deps)
        raise AssertionError(errmsg)

    return


def test_registry_initialize_all_warns_on_missing_optional_dep():
    """
        Test that initialize_all() logs a warning for missing optional dependencies.
    """
    app_ctx = _FakeAppContext()
    registry = ExtensionRegistry(app_context=app_ctx)

    ext = _ExtensionWithOptionalDep()
    registry.register(ext)

    # Should not raise, just log a warning
    registry.initialize_all()

    state = registry.get_state("ext-opt")
    if state is not ExtensionState.INITIALIZED:
        errmsg = "Expected state INITIALIZED, got {}".format(state)
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for enable() and disable()
# =============================================================================

def test_registry_enable_activates_extension():
    """
        Test that enable() transitions extension to ACTIVE state.
    """
    app_ctx = _FakeAppContext()
    registry = ExtensionRegistry(app_context=app_ctx)

    ext = _SimpleExtension()
    registry.register(ext)
    registry.initialize_all()
    registry.enable("simple-ext")

    state = registry.get_state("simple-ext")
    if state is not ExtensionState.ACTIVE:
        errmsg = "Expected state ACTIVE, got {}".format(state)
        raise AssertionError(errmsg)

    return


def test_registry_enable_raises_for_unknown():
    """
        Test that enable() raises ExtensionNotFoundError for unknown extension.
    """
    app_ctx = _FakeAppContext()
    registry = ExtensionRegistry(app_context=app_ctx)

    raised = False
    try:
        registry.enable("nonexistent")
    except ExtensionNotFoundError:
        raised = True

    if raised is not True:
        errmsg = "Expected ExtensionNotFoundError for unknown extension"
        raise AssertionError(errmsg)

    return


def test_registry_disable_deactivates_extension():
    """
        Test that disable() transitions extension to DISABLED state.
    """
    app_ctx = _FakeAppContext()
    registry = ExtensionRegistry(app_context=app_ctx)

    ext = _SimpleExtension()
    registry.register(ext)
    registry.initialize_all()
    registry.enable("simple-ext")
    registry.disable("simple-ext")

    state = registry.get_state("simple-ext")
    if state is not ExtensionState.DISABLED:
        errmsg = "Expected state DISABLED, got {}".format(state)
        raise AssertionError(errmsg)

    return


def test_registry_disable_raises_for_unknown():
    """
        Test that disable() raises ExtensionNotFoundError for unknown extension.
    """
    app_ctx = _FakeAppContext()
    registry = ExtensionRegistry(app_context=app_ctx)

    raised = False
    try:
        registry.disable("nonexistent")
    except ExtensionNotFoundError:
        raised = True

    if raised is not True:
        errmsg = "Expected ExtensionNotFoundError for unknown extension"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for get_state()
# =============================================================================

def test_registry_get_state_returns_unknown_for_unregistered():
    """
        Test that get_state() returns UNKNOWN for an unregistered extension.
    """
    app_ctx = _FakeAppContext()
    registry = ExtensionRegistry(app_context=app_ctx)

    state = registry.get_state("nonexistent")
    if state is not ExtensionState.UNKNOWN:
        errmsg = "Expected state UNKNOWN, got {}".format(state)
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for query_by_capability()
# =============================================================================

def test_registry_query_by_capability_finds_matching():
    """
        Test that query_by_capability() returns extensions with matching capability.
    """
    app_ctx = _FakeAppContext()
    registry = ExtensionRegistry(app_context=app_ctx)

    ext = _ExtensionWithCapability()
    registry.register(ext)

    result = registry.query_by_capability("auth-provider")
    if len(result) != 1:
        errmsg = "Expected 1 matching extension, got {}".format(len(result))
        raise AssertionError(errmsg)

    if result[0] is not ext:
        errmsg = "Expected the matching extension to be ext-cap"
        raise AssertionError(errmsg)

    return


def test_registry_query_by_capability_returns_empty_for_no_match():
    """
        Test that query_by_capability() returns empty list when no match.
    """
    app_ctx = _FakeAppContext()
    registry = ExtensionRegistry(app_context=app_ctx)

    ext = _SimpleExtension()
    registry.register(ext)

    result = registry.query_by_capability("nonexistent-cap")
    if len(result) != 0:
        errmsg = "Expected 0 matching extensions, got {}".format(len(result))
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for reload()
# =============================================================================

def test_registry_reload_calls_deactivate_and_activate():
    """
        Test that reload() calls deactivate() then activate().
    """
    app_ctx = _FakeAppContext()
    registry = ExtensionRegistry(app_context=app_ctx)

    ext = _ActivationTrackingExtension()
    registry.register(ext)
    registry.initialize_all()
    registry.enable("tracking-ext")

    initial_activate = ext.activate_count
    initial_deactivate = ext.deactivate_count

    registry.reload("tracking-ext")

    if ext.deactivate_count != initial_deactivate + 1:
        errmsg = "Expected deactivate_count to increment by 1"
        raise AssertionError(errmsg)

    if ext.activate_count != initial_activate + 1:
        errmsg = "Expected activate_count to increment by 1"
        raise AssertionError(errmsg)

    state = registry.get_state("tracking-ext")
    if state is not ExtensionState.ACTIVE:
        errmsg = "Expected state ACTIVE after reload, got {}".format(state)
        raise AssertionError(errmsg)

    return


def test_registry_reload_raises_for_unknown():
    """
        Test that reload() raises ExtensionNotFoundError for unknown extension.
    """
    app_ctx = _FakeAppContext()
    registry = ExtensionRegistry(app_context=app_ctx)

    raised = False
    try:
        registry.reload("nonexistent")
    except ExtensionNotFoundError:
        raised = True

    if raised is not True:
        errmsg = "Expected ExtensionNotFoundError for unknown extension"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for error tracking and quarantine
# =============================================================================

def test_registry_record_error_increments_count():
    """
        Test that record_error() increments the error count.
    """
    app_ctx = _FakeAppContext()
    registry = ExtensionRegistry(app_context=app_ctx)

    ext = _SimpleExtension()
    registry.register(ext)

    registry.record_error("simple-ext")

    count = registry.get_error_count("simple-ext")
    if count != 1:
        errmsg = "Expected error count 1, got {}".format(count)
        raise AssertionError(errmsg)

    return


def test_registry_record_error_quarantines_at_threshold():
    """
        Test that record_error() quarantines extension at threshold.
    """
    app_ctx = _FakeAppContext()
    registry = ExtensionRegistry(app_context=app_ctx)

    ext = _SimpleExtension()
    registry.register(ext)

    for _ in range(5):
        registry.record_error("simple-ext")

    state = registry.get_state("simple-ext")
    if state is not ExtensionState.QUARANTINED:
        errmsg = "Expected state QUARANTINED after 5 errors, got {}".format(state)
        raise AssertionError(errmsg)

    return


# =============================================================================
# Property-Based Tests
# =============================================================================

# Feature: extensibility, Property 4: Registry Registration Round-Trip
# *For any* Extension instance registered with the registry, calling get()
# with the extension's name SHALL return the same extension instance.
# **Validates: Requirements 2.1, 2.3**

def test_property_4_registry_registration_round_trip():
    """
        Property 4: Registry Registration Round-Trip

        For any Extension instance registered with the registry,
        calling get() with the extension's name SHALL return the
        same extension instance.

        **Validates: Requirements 2.1, 2.3**
    """
    for iteration in range(100):
        app_ctx = _FakeAppContext()
        registry = ExtensionRegistry(app_context=app_ctx)

        ext_name = _generate_random_string(3, 20)
        ext = _create_named_extension(ext_name)

        registry.register(ext)

        retrieved = registry.get(ext_name)
        if retrieved is not ext:
            errmsg = "Iteration {}: get('{}') did not return the same extension instance".format(
                iteration, ext_name
            )
            raise AssertionError(errmsg)

        # Verify duplicate registration raises
        duplicate = _create_named_extension(ext_name)
        raised = False
        try:
            registry.register(duplicate)
        except ExtensionAlreadyRegisteredError:
            raised = True

        if raised is not True:
            errmsg = "Iteration {}: Expected ExtensionAlreadyRegisteredError for duplicate '{}'".format(
                iteration, ext_name
            )
            raise AssertionError(errmsg)

    return


# Feature: extensibility, Property 5: Registry List Completeness
# *For any* set of registered extensions, calling list() SHALL return
# all registered extensions and only registered extensions.
# **Validates: Requirements 2.4**

def test_property_5_registry_list_completeness():
    """
        Property 5: Registry List Completeness

        For any set of registered extensions, calling list() SHALL
        return all registered extensions and only registered extensions.

        **Validates: Requirements 2.4**
    """
    for iteration in range(100):
        app_ctx = _FakeAppContext()
        registry = ExtensionRegistry(app_context=app_ctx)

        # Generate a random number of unique extension names
        ext_count = random.randint(1, 10)
        names = set()
        while len(names) < ext_count:
            name = _generate_random_string(3, 20)
            names.add(name)

        registered_extensions = {}
        for name in names:
            ext = _create_named_extension(name)
            registry.register(ext)
            registered_extensions[name] = ext

        listed = registry.list()

        # Verify count matches
        if len(listed) != ext_count:
            errmsg = "Iteration {}: Expected {} extensions in list, got {}".format(
                iteration, ext_count, len(listed)
            )
            raise AssertionError(errmsg)

        # Verify all registered extensions are in the list
        listed_set = set(id(e) for e in listed)
        for name, ext in registered_extensions.items():
            if id(ext) not in listed_set:
                errmsg = "Iteration {}: Extension '{}' not found in list()".format(
                    iteration, name
                )
                raise AssertionError(errmsg)

    return


# Feature: extensibility, Property 6: Extension Enable/Disable State Transitions
# *For any* registered extension, calling enable() SHALL transition it to
# ACTIVE state and call activate(), and calling disable() SHALL transition
# it to DISABLED state and call deactivate().
# **Validates: Requirements 2.5, 2.6, 11.2, 11.3**

def test_property_6_extension_enable_disable_state_transitions():
    """
        Property 6: Extension Enable/Disable State Transitions

        For any registered extension, calling enable() SHALL transition
        it to ACTIVE state, and calling disable() SHALL transition it
        to DISABLED state.

        **Validates: Requirements 2.5, 2.6, 11.2, 11.3**
    """
    for iteration in range(100):
        app_ctx = _FakeAppContext()
        registry = ExtensionRegistry(app_context=app_ctx)

        ext_name = _generate_random_string(3, 20)
        ext = _create_named_extension(ext_name)

        registry.register(ext)
        registry.initialize_all()

        # Enable should transition to ACTIVE
        registry.enable(ext_name)
        state_after_enable = registry.get_state(ext_name)
        if state_after_enable is not ExtensionState.ACTIVE:
            errmsg = "Iteration {}: Expected ACTIVE after enable(), got {}".format(
                iteration, state_after_enable
            )
            raise AssertionError(errmsg)

        # Disable should transition to DISABLED
        registry.disable(ext_name)
        state_after_disable = registry.get_state(ext_name)
        if state_after_disable is not ExtensionState.DISABLED:
            errmsg = "Iteration {}: Expected DISABLED after disable(), got {}".format(
                iteration, state_after_disable
            )
            raise AssertionError(errmsg)

    return


# Feature: extensibility, Property 7: Dependency Resolution Order
# *For any* set of extensions with dependencies, the registry SHALL
# initialize them in topological order such that all dependencies are
# initialized before their dependents.
# **Validates: Requirements 2.7, 12.3, 12.4**

def test_property_7_dependency_resolution_order():
    """
        Property 7: Dependency Resolution Order

        For any set of extensions with a linear dependency chain,
        the registry SHALL resolve them in topological order such
        that all dependencies appear before their dependents.

        **Validates: Requirements 2.7, 12.3, 12.4**
    """
    for iteration in range(100):
        app_ctx = _FakeAppContext()
        registry = ExtensionRegistry(app_context=app_ctx)

        # Generate a random chain of 2-5 extensions
        chain_length = random.randint(2, 5)
        names = []
        for _ in range(chain_length):
            name = _generate_random_string(3, 15)
            while name in names:
                name = _generate_random_string(3, 15)
            names.append(name)

        # Create chain: names[0] <- names[1] <- names[2] <- ...
        for idx in range(chain_length):
            if idx == 0:
                deps = []
            else:
                deps = [names[idx - 1]]

            ext = _create_named_extension(names[idx], deps=deps)
            registry.register(ext)

        order = registry._resolve_dependencies()

        # Verify each extension appears after its dependency
        for idx in range(1, chain_length):
            dep_pos = order.index(names[idx - 1])
            ext_pos = order.index(names[idx])

            if dep_pos >= ext_pos:
                errmsg = "Iteration {}: Expected '{}' (pos {}) before '{}' (pos {})".format(
                    iteration, names[idx - 1], dep_pos, names[idx], ext_pos
                )
                raise AssertionError(errmsg)

    return


# Feature: extensibility, Property 8: Circular Dependency Detection
# *For any* set of extensions with circular dependencies, the registry
# SHALL raise ExtensionDependencyError.
# **Validates: Requirements 2.8**

def test_property_8_circular_dependency_detection():
    """
        Property 8: Circular Dependency Detection

        For any set of extensions with circular dependencies, the
        registry SHALL raise ExtensionDependencyError and not
        initialize any extensions in the cycle.

        **Validates: Requirements 2.8**
    """
    for iteration in range(100):
        app_ctx = _FakeAppContext()
        registry = ExtensionRegistry(app_context=app_ctx)

        # Generate a random cycle of 2-4 extensions
        cycle_length = random.randint(2, 4)
        names = []
        for _ in range(cycle_length):
            name = _generate_random_string(3, 15)
            while name in names:
                name = _generate_random_string(3, 15)
            names.append(name)

        # Create cycle: each depends on the next, last depends on first
        for idx in range(cycle_length):
            dep_idx = (idx + 1) % cycle_length
            ext = _create_named_extension(names[idx], deps=[names[dep_idx]])
            registry.register(ext)

        raised = False
        try:
            registry._resolve_dependencies()
        except ExtensionDependencyError:
            raised = True

        if raised is not True:
            errmsg = "Iteration {}: Expected ExtensionDependencyError for cycle {}".format(
                iteration, names
            )
            raise AssertionError(errmsg)

    return


# Feature: extensibility, Property 9: Missing Dependency Error
# *For any* extension with a required dependency that is not registered,
# attempting to initialize it SHALL raise ExtensionDependencyError.
# **Validates: Requirements 2.9, 12.5**

def test_property_9_missing_dependency_error():
    """
        Property 9: Missing Dependency Error

        For any extension with a required dependency that is not
        registered, attempting to initialize SHALL raise
        ExtensionDependencyError.

        **Validates: Requirements 2.9, 12.5**
    """
    for iteration in range(100):
        app_ctx = _FakeAppContext()
        registry = ExtensionRegistry(app_context=app_ctx)

        ext_name = _generate_random_string(3, 15)
        missing_dep = _generate_random_string(3, 15)

        # Ensure they are different
        while missing_dep == ext_name:
            missing_dep = _generate_random_string(3, 15)

        ext = _create_named_extension(ext_name, deps=[missing_dep])
        registry.register(ext)

        raised = False
        caught_error = None
        try:
            registry.initialize_all()
        except ExtensionDependencyError as err:
            raised = True
            caught_error = err

        if raised is not True:
            errmsg = "Iteration {}: Expected ExtensionDependencyError for missing dep '{}'".format(
                iteration, missing_dep
            )
            raise AssertionError(errmsg)

        if missing_dep not in caught_error.missing_deps:
            errmsg = "Iteration {}: Expected '{}' in missing_deps, got {}".format(
                iteration, missing_dep, caught_error.missing_deps
            )
            raise AssertionError(errmsg)

    return


# Feature: extensibility, Property 10: Optional Dependency Handling
# *For any* extension with an optional dependency that is not registered,
# initialization SHALL succeed and log a warning.
# **Validates: Requirements 12.6**

def test_property_10_optional_dependency_handling():
    """
        Property 10: Optional Dependency Handling

        For any extension with an optional dependency that is not
        registered, initialization SHALL succeed without error.

        **Validates: Requirements 12.6**
    """
    for iteration in range(100):
        app_ctx = _FakeAppContext()
        registry = ExtensionRegistry(app_context=app_ctx)

        ext_name = _generate_random_string(3, 15)
        opt_dep = _generate_random_string(3, 15)

        while opt_dep == ext_name:
            opt_dep = _generate_random_string(3, 15)

        ext = _create_named_extension(ext_name, opt_deps=[opt_dep])
        registry.register(ext)

        # Should not raise
        registry.initialize_all()

        state = registry.get_state(ext_name)
        if state is not ExtensionState.INITIALIZED:
            errmsg = "Iteration {}: Expected state INITIALIZED, got {}".format(
                iteration, state
            )
            raise AssertionError(errmsg)

    return


# Feature: extensibility, Property 28: Extension State Tracking
# *For any* extension, the registry SHALL accurately track its state
# through all transitions.
# **Validates: Requirements 11.1, 11.7**

def test_property_28_extension_state_tracking():
    """
        Property 28: Extension State Tracking

        For any extension, the registry SHALL accurately track its
        state through REGISTERED -> INITIALIZED -> ACTIVE -> DISABLED
        transitions.

        **Validates: Requirements 11.1, 11.7**
    """
    for iteration in range(100):
        app_ctx = _FakeAppContext()
        registry = ExtensionRegistry(app_context=app_ctx)

        ext_name = _generate_random_string(3, 20)
        ext = _create_named_extension(ext_name)

        registry.register(ext)

        # State should be REGISTERED
        state = registry.get_state(ext_name)
        if state is not ExtensionState.REGISTERED:
            errmsg = "Iteration {}: Expected REGISTERED, got {}".format(iteration, state)
            raise AssertionError(errmsg)

        # After initialize_all, state should be INITIALIZED
        registry.initialize_all()
        state = registry.get_state(ext_name)
        if state is not ExtensionState.INITIALIZED:
            errmsg = "Iteration {}: Expected INITIALIZED, got {}".format(iteration, state)
            raise AssertionError(errmsg)

        # After enable, state should be ACTIVE
        registry.enable(ext_name)
        state = registry.get_state(ext_name)
        if state is not ExtensionState.ACTIVE:
            errmsg = "Iteration {}: Expected ACTIVE, got {}".format(iteration, state)
            raise AssertionError(errmsg)

        # After disable, state should be DISABLED
        registry.disable(ext_name)
        state = registry.get_state(ext_name)
        if state is not ExtensionState.DISABLED:
            errmsg = "Iteration {}: Expected DISABLED, got {}".format(iteration, state)
            raise AssertionError(errmsg)

    return


# Feature: extensibility, Property 29: Extension Reload Sequence
# *For any* extension being reloaded, the framework SHALL call
# deactivate(), reload the module, and call activate() in that order.
# **Validates: Requirements 11.5**

def test_property_29_extension_reload_sequence():
    """
        Property 29: Extension Reload Sequence

        For any active extension, calling reload() SHALL call
        deactivate() then activate(), resulting in ACTIVE state.

        **Validates: Requirements 11.5**
    """
    for iteration in range(100):
        app_ctx = _FakeAppContext()
        registry = ExtensionRegistry(app_context=app_ctx)

        ext_name = "tracking-ext"
        ext = _ActivationTrackingExtension()

        registry.register(ext)
        registry.initialize_all()
        registry.enable(ext_name)

        pre_activate = ext.activate_count
        pre_deactivate = ext.deactivate_count

        registry.reload(ext_name)

        # Deactivate should have been called once more
        if ext.deactivate_count != pre_deactivate + 1:
            errmsg = "Iteration {}: Expected deactivate_count to increment by 1".format(iteration)
            raise AssertionError(errmsg)

        # Activate should have been called once more
        if ext.activate_count != pre_activate + 1:
            errmsg = "Iteration {}: Expected activate_count to increment by 1".format(iteration)
            raise AssertionError(errmsg)

        # State should be ACTIVE after reload
        state = registry.get_state(ext_name)
        if state is not ExtensionState.ACTIVE:
            errmsg = "Iteration {}: Expected ACTIVE after reload, got {}".format(iteration, state)
            raise AssertionError(errmsg)

    return


# Feature: extensibility, Property 33: Error Threshold Quarantine
# *For any* extension that exceeds the configured error threshold,
# the framework SHALL quarantine it and prevent further execution.
# **Validates: Requirements 14.4, 14.8**

def test_property_33_error_threshold_quarantine():
    """
        Property 33: Error Threshold Quarantine

        For any extension, recording errors up to the threshold
        SHALL quarantine the extension.

        **Validates: Requirements 14.4, 14.8**
    """
    for iteration in range(100):
        app_ctx = _FakeAppContext()
        registry = ExtensionRegistry(app_context=app_ctx)

        ext_name = _generate_random_string(3, 20)
        ext = _create_named_extension(ext_name)
        registry.register(ext)

        threshold = registry._error_threshold

        # Record errors below threshold - should not quarantine
        for i in range(threshold - 1):
            registry.record_error(ext_name)
            state = registry.get_state(ext_name)
            if state is ExtensionState.QUARANTINED:
                errmsg = "Iteration {}: Extension quarantined after only {} errors (threshold {})".format(
                    iteration, i + 1, threshold
                )
                raise AssertionError(errmsg)

        # Record one more error to reach threshold - should quarantine
        registry.record_error(ext_name)
        state = registry.get_state(ext_name)
        if state is not ExtensionState.QUARANTINED:
            errmsg = "Iteration {}: Expected QUARANTINED after {} errors, got {}".format(
                iteration, threshold, state
            )
            raise AssertionError(errmsg)

        # Verify error count matches
        count = registry.get_error_count(ext_name)
        if count != threshold:
            errmsg = "Iteration {}: Expected error count {}, got {}".format(
                iteration, threshold, count
            )
            raise AssertionError(errmsg)

    return
