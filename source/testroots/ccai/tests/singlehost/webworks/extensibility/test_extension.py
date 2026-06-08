"""
    Tests for the Extension abstract base class.

    This module contains unit tests and property-based tests for the
    Extension class lifecycle methods, state transitions, metadata
    attributes, and context access.
"""

import random
import string

from typing import List, Optional

from ccai.webworks.extensibility.datastructures import ExtensionState
from ccai.webworks.extensibility.exceptions import ExtensionNotInitializedError
from ccai.webworks.extensibility.extension import Extension


# =============================================================================
# Test Helpers
# =============================================================================

class _ConcreteExtension(Extension):
    """
        A minimal concrete subclass of Extension for testing purposes.
    """

    name = "test-extension"
    version = "1.0.0"
    description = "A test extension"
    dependencies = []
    optional_dependencies = []


class _CustomMetadataExtension(Extension):
    """
        A concrete extension with custom metadata for testing.
    """

    name = "custom-ext"
    version = "2.3.1"
    description = "Custom extension for testing"
    dependencies = ["dep-a", "dep-b"]
    optional_dependencies = ["opt-c"]


class _FakeExtensionContext:
    """
        A fake extension context for testing purposes.

        Provides a minimal stand-in for ExtensionContext so that
        the Extension lifecycle can be tested without the full
        framework context infrastructure.
    """

    def __init__(self, extension_name: str = "test"):
        self.extension_name = extension_name
        return


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


def _generate_random_dep_list(max_count: int = 5) -> List[str]:
    """
        Generate a random list of dependency names.

        :param max_count: Maximum number of dependencies to generate.

        :returns: A list of random dependency name strings.
    """
    count = random.randint(0, max_count)
    deps = [_generate_random_string(3, 15) for _ in range(count)]
    return deps


def _create_random_extension_class() -> type:
    """
        Create a random concrete Extension subclass with random metadata.

        :returns: A new Extension subclass type with random class attributes.
    """
    ext_name = _generate_random_string(3, 20)
    ext_version = _generate_random_version()
    ext_description = _generate_random_string(5, 50)
    ext_deps = _generate_random_dep_list()
    ext_opt_deps = _generate_random_dep_list()

    ext_cls = type(
        "RandomExtension",
        (Extension,),
        {
            "name": ext_name,
            "version": ext_version,
            "description": ext_description,
            "dependencies": ext_deps,
            "optional_dependencies": ext_opt_deps,
        }
    )

    return ext_cls


# =============================================================================
# Unit Tests for Extension Class Attributes
# =============================================================================

def test_extension_has_name_attribute():
    """
        Test that a concrete Extension subclass exposes the name attribute.
    """
    ext = _ConcreteExtension()

    if ext.name != "test-extension":
        errmsg = "Expected name 'test-extension', got '{}'".format(ext.name)
        raise AssertionError(errmsg)

    return


def test_extension_has_version_attribute():
    """
        Test that a concrete Extension subclass exposes the version attribute.
    """
    ext = _ConcreteExtension()

    if ext.version != "1.0.0":
        errmsg = "Expected version '1.0.0', got '{}'".format(ext.version)
        raise AssertionError(errmsg)

    return


def test_extension_has_description_attribute():
    """
        Test that a concrete Extension subclass exposes the description attribute.
    """
    ext = _ConcreteExtension()

    if ext.description != "A test extension":
        errmsg = "Expected description 'A test extension', got '{}'".format(ext.description)
        raise AssertionError(errmsg)

    return


def test_extension_has_dependencies_attribute():
    """
        Test that a concrete Extension subclass exposes the dependencies attribute.
    """
    ext = _CustomMetadataExtension()

    if ext.dependencies != ["dep-a", "dep-b"]:
        errmsg = "Expected dependencies ['dep-a', 'dep-b'], got {}".format(ext.dependencies)
        raise AssertionError(errmsg)

    return


def test_extension_has_optional_dependencies_attribute():
    """
        Test that a concrete Extension subclass exposes the optional_dependencies attribute.
    """
    ext = _CustomMetadataExtension()

    if ext.optional_dependencies != ["opt-c"]:
        errmsg = "Expected optional_dependencies ['opt-c'], got {}".format(ext.optional_dependencies)
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for Extension __init__
# =============================================================================

def test_extension_initial_context_is_none():
    """
        Test that a newly created Extension has _context set to None.
    """
    ext = _ConcreteExtension()

    if ext._context is not None:
        errmsg = "Expected _context to be None, got {}".format(ext._context)
        raise AssertionError(errmsg)

    return


def test_extension_initial_state_is_registered():
    """
        Test that a newly created Extension has state REGISTERED.
    """
    ext = _ConcreteExtension()

    if ext.state is not ExtensionState.REGISTERED:
        errmsg = "Expected state REGISTERED, got {}".format(ext.state)
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for context property
# =============================================================================

def test_extension_context_raises_when_not_initialized():
    """
        Test that accessing context before initialization raises ExtensionNotInitializedError.
    """
    ext = _ConcreteExtension()

    raised = False
    try:
        _ = ext.context
    except ExtensionNotInitializedError:
        raised = True

    if raised is not True:
        errmsg = "Expected ExtensionNotInitializedError to be raised"
        raise AssertionError(errmsg)

    return


def test_extension_context_returns_context_after_initialization():
    """
        Test that accessing context after initialization returns the provided context.
    """
    ext = _ConcreteExtension()
    fake_ctx = _FakeExtensionContext(extension_name="test-extension")

    ext.initialize(fake_ctx)

    ctx = ext.context
    if ctx is not fake_ctx:
        errmsg = "Expected context to be the same instance provided during initialization"
        raise AssertionError(errmsg)

    return


def test_extension_context_error_includes_extension_name():
    """
        Test that ExtensionNotInitializedError includes the extension name.
    """
    ext = _ConcreteExtension()

    caught_error = None
    try:
        _ = ext.context
    except ExtensionNotInitializedError as err:
        caught_error = err

    if caught_error is None:
        errmsg = "Expected ExtensionNotInitializedError to be raised"
        raise AssertionError(errmsg)

    if caught_error.extension_name != "test-extension":
        errmsg = "Expected extension_name 'test-extension', got '{}'".format(caught_error.extension_name)
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for state property
# =============================================================================

def test_extension_state_returns_current_state():
    """
        Test that the state property returns the current extension state.
    """
    ext = _ConcreteExtension()

    state = ext.state
    if state is not ExtensionState.REGISTERED:
        errmsg = "Expected state REGISTERED, got {}".format(state)
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for initialize() method
# =============================================================================

def test_extension_initialize_sets_context():
    """
        Test that initialize() sets the extension context.
    """
    ext = _ConcreteExtension()
    fake_ctx = _FakeExtensionContext()

    ext.initialize(fake_ctx)

    if ext._context is not fake_ctx:
        errmsg = "Expected _context to be the provided context instance"
        raise AssertionError(errmsg)

    return


def test_extension_initialize_transitions_to_initialized():
    """
        Test that initialize() transitions state to INITIALIZED.
    """
    ext = _ConcreteExtension()
    fake_ctx = _FakeExtensionContext()

    ext.initialize(fake_ctx)

    if ext.state is not ExtensionState.INITIALIZED:
        errmsg = "Expected state INITIALIZED, got {}".format(ext.state)
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for activate() method
# =============================================================================

def test_extension_activate_transitions_to_active():
    """
        Test that activate() transitions state to ACTIVE.
    """
    ext = _ConcreteExtension()
    fake_ctx = _FakeExtensionContext()

    ext.initialize(fake_ctx)
    ext.activate()

    if ext.state is not ExtensionState.ACTIVE:
        errmsg = "Expected state ACTIVE, got {}".format(ext.state)
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for deactivate() method
# =============================================================================

def test_extension_deactivate_transitions_to_disabled():
    """
        Test that deactivate() transitions state to DISABLED.
    """
    ext = _ConcreteExtension()
    fake_ctx = _FakeExtensionContext()

    ext.initialize(fake_ctx)
    ext.activate()
    ext.deactivate()

    if ext.state is not ExtensionState.DISABLED:
        errmsg = "Expected state DISABLED, got {}".format(ext.state)
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for shutdown() method
# =============================================================================

def test_extension_shutdown_does_not_raise():
    """
        Test that shutdown() executes without error.
    """
    ext = _ConcreteExtension()
    fake_ctx = _FakeExtensionContext()

    ext.initialize(fake_ctx)
    ext.activate()
    ext.deactivate()
    ext.shutdown()

    return


# =============================================================================
# Unit Tests for full lifecycle
# =============================================================================

def test_extension_full_lifecycle_state_transitions():
    """
        Test the full lifecycle: REGISTERED -> INITIALIZED -> ACTIVE -> DISABLED.
    """
    ext = _ConcreteExtension()
    fake_ctx = _FakeExtensionContext()

    if ext.state is not ExtensionState.REGISTERED:
        errmsg = "Expected initial state REGISTERED, got {}".format(ext.state)
        raise AssertionError(errmsg)

    ext.initialize(fake_ctx)
    if ext.state is not ExtensionState.INITIALIZED:
        errmsg = "Expected state INITIALIZED after initialize(), got {}".format(ext.state)
        raise AssertionError(errmsg)

    ext.activate()
    if ext.state is not ExtensionState.ACTIVE:
        errmsg = "Expected state ACTIVE after activate(), got {}".format(ext.state)
        raise AssertionError(errmsg)

    ext.deactivate()
    if ext.state is not ExtensionState.DISABLED:
        errmsg = "Expected state DISABLED after deactivate(), got {}".format(ext.state)
        raise AssertionError(errmsg)

    ext.shutdown()

    return


# =============================================================================
# Property-Based Tests
# =============================================================================

# Feature: extensibility, Property 1: Extension Lifecycle Methods
# *For any* Extension subclass, calling initialize() with a valid context,
# then activate(), then deactivate(), then shutdown() SHALL execute without
# error and transition the extension through the expected states
# (REGISTERED -> INITIALIZED -> ACTIVE -> DISABLED).
# **Validates: Requirements 1.1, 1.2, 1.3, 1.4**

def test_property_1_extension_lifecycle_state_transitions():
    """
        Property 1: Extension Lifecycle Methods (state transitions)

        For any Extension subclass with random metadata, calling
        initialize(), activate(), deactivate(), shutdown() SHALL
        transition through REGISTERED -> INITIALIZED -> ACTIVE -> DISABLED
        without error.

        **Validates: Requirements 1.1, 1.2, 1.3, 1.4**
    """
    for iteration in range(100):
        ext_cls = _create_random_extension_class()
        ext = ext_cls()
        fake_ctx = _FakeExtensionContext(extension_name=ext.name)

        # Verify initial state is REGISTERED
        if ext.state is not ExtensionState.REGISTERED:
            errmsg = "Iteration {}: Expected initial state REGISTERED, got {}".format(iteration, ext.state)
            raise AssertionError(errmsg)

        # initialize() -> INITIALIZED
        ext.initialize(fake_ctx)
        if ext.state is not ExtensionState.INITIALIZED:
            errmsg = "Iteration {}: Expected state INITIALIZED after initialize(), got {}".format(iteration, ext.state)
            raise AssertionError(errmsg)

        # activate() -> ACTIVE
        ext.activate()
        if ext.state is not ExtensionState.ACTIVE:
            errmsg = "Iteration {}: Expected state ACTIVE after activate(), got {}".format(iteration, ext.state)
            raise AssertionError(errmsg)

        # deactivate() -> DISABLED
        ext.deactivate()
        if ext.state is not ExtensionState.DISABLED:
            errmsg = "Iteration {}: Expected state DISABLED after deactivate(), got {}".format(iteration, ext.state)
            raise AssertionError(errmsg)

        # shutdown() should not raise
        ext.shutdown()

    return


def test_property_1_extension_lifecycle_context_preserved():
    """
        Property 1: Extension Lifecycle Methods (context preserved through lifecycle)

        For any Extension subclass, the context provided during initialize()
        SHALL remain accessible throughout the full lifecycle.

        **Validates: Requirements 1.1, 1.2, 1.3, 1.4**
    """
    for iteration in range(100):
        ext_cls = _create_random_extension_class()
        ext = ext_cls()
        fake_ctx = _FakeExtensionContext(extension_name=ext.name)

        ext.initialize(fake_ctx)

        # Context should be accessible after initialize
        ctx_after_init = ext.context
        if ctx_after_init is not fake_ctx:
            errmsg = "Iteration {}: Context changed after initialize()".format(iteration)
            raise AssertionError(errmsg)

        ext.activate()

        # Context should be accessible after activate
        ctx_after_activate = ext.context
        if ctx_after_activate is not fake_ctx:
            errmsg = "Iteration {}: Context changed after activate()".format(iteration)
            raise AssertionError(errmsg)

        ext.deactivate()

        # Context should be accessible after deactivate
        ctx_after_deactivate = ext.context
        if ctx_after_deactivate is not fake_ctx:
            errmsg = "Iteration {}: Context changed after deactivate()".format(iteration)
            raise AssertionError(errmsg)

        ext.shutdown()

    return


# Feature: extensibility, Property 2: Extension Context Access
# *For any* initialized Extension, accessing the context property SHALL
# return the ExtensionContext provided during initialization, and accessing
# it before initialization SHALL raise ExtensionNotInitializedError.
# **Validates: Requirements 1.5**

def test_property_2_extension_context_access_before_init():
    """
        Property 2: Extension Context Access (before initialization)

        For any Extension subclass, accessing the context property before
        initialization SHALL raise ExtensionNotInitializedError.

        **Validates: Requirements 1.5**
    """
    for iteration in range(100):
        ext_cls = _create_random_extension_class()
        ext = ext_cls()

        raised = False
        caught_error = None
        try:
            _ = ext.context
        except ExtensionNotInitializedError as err:
            raised = True
            caught_error = err

        if raised is not True:
            errmsg = "Iteration {}: Expected ExtensionNotInitializedError for extension '{}'".format(
                iteration, ext.name
            )
            raise AssertionError(errmsg)

        if caught_error.extension_name != ext.name:
            errmsg = "Iteration {}: Expected extension_name '{}' in error, got '{}'".format(
                iteration, ext.name, caught_error.extension_name
            )
            raise AssertionError(errmsg)

    return


def test_property_2_extension_context_access_after_init():
    """
        Property 2: Extension Context Access (after initialization)

        For any initialized Extension, accessing the context property SHALL
        return the exact ExtensionContext provided during initialization.

        **Validates: Requirements 1.5**
    """
    for iteration in range(100):
        ext_cls = _create_random_extension_class()
        ext = ext_cls()
        fake_ctx = _FakeExtensionContext(extension_name=ext.name)

        ext.initialize(fake_ctx)

        ctx = ext.context
        if ctx is not fake_ctx:
            errmsg = "Iteration {}: Expected context to be the same instance for extension '{}'".format(
                iteration, ext.name
            )
            raise AssertionError(errmsg)

    return
