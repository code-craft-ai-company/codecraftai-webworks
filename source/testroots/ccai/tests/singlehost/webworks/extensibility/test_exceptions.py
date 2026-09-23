"""
    Tests for the extensibility exception classes.

    This module contains unit tests for all exception classes in the
    extensibility system including inheritance, message formatting,
    and attribute storage.
"""

from pathlib import Path

from ccai.webworks.extensibility.exceptions import (
    ExtensionAlreadyRegisteredError,
    ExtensionConfigurationError,
    ExtensionContextFrozenError,
    ExtensionDependencyError,
    ExtensionError,
    ExtensionManifestError,
    ExtensionNotFoundError,
    ExtensionNotInitializedError,
    ExtensionPointError,
    HookOrderingError,
)


# =============================================================================
# Unit Tests for ExtensionError Base Exception
# =============================================================================

def test_extension_error_stores_message():
    """
        Test that ExtensionError stores the message string.
    """
    err = ExtensionError("something went wrong")

    if str(err) != "something went wrong":
        errmsg = f"Expected message 'something went wrong', got '{str(err)}'"
        raise AssertionError(errmsg)

    return


def test_extension_error_stores_extension_name():
    """
        Test that ExtensionError stores the optional extension_name.
    """
    err = ExtensionError("error", extension_name="my-ext")

    if err.extension_name != "my-ext":
        errmsg = f"Expected extension_name 'my-ext', got '{err.extension_name}'"
        raise AssertionError(errmsg)

    return


def test_extension_error_default_extension_name_is_none():
    """
        Test that ExtensionError defaults extension_name to None.
    """
    err = ExtensionError("error")

    if err.extension_name is not None:
        errmsg = f"Expected extension_name None, got '{err.extension_name}'"
        raise AssertionError(errmsg)

    return


def test_extension_error_is_exception():
    """
        Test that ExtensionError inherits from Exception.
    """
    err = ExtensionError("error")

    if not isinstance(err, Exception):
        errmsg = "Expected ExtensionError to be an instance of Exception"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for ExtensionNotFoundError
# =============================================================================

def test_extension_not_found_error_message_contains_name():
    """
        Test that ExtensionNotFoundError message contains the extension name.
    """
    err = ExtensionNotFoundError("missing-ext")

    if "missing-ext" not in str(err):
        errmsg = f"Expected 'missing-ext' in message, got '{str(err)}'"
        raise AssertionError(errmsg)

    return


def test_extension_not_found_error_stores_extension_name():
    """
        Test that ExtensionNotFoundError stores the extension name.
    """
    err = ExtensionNotFoundError("missing-ext")

    if err.extension_name != "missing-ext":
        errmsg = f"Expected extension_name 'missing-ext', got '{err.extension_name}'"
        raise AssertionError(errmsg)

    return


def test_extension_not_found_error_inherits_extension_error():
    """
        Test that ExtensionNotFoundError inherits from ExtensionError.
    """
    err = ExtensionNotFoundError("missing-ext")

    if not isinstance(err, ExtensionError):
        errmsg = "Expected ExtensionNotFoundError to be an instance of ExtensionError"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for ExtensionAlreadyRegisteredError
# =============================================================================

def test_already_registered_error_message_contains_name():
    """
        Test that ExtensionAlreadyRegisteredError message contains the extension name.
    """
    err = ExtensionAlreadyRegisteredError("dup-ext")

    if "dup-ext" not in str(err):
        errmsg = f"Expected 'dup-ext' in message, got '{str(err)}'"
        raise AssertionError(errmsg)

    return


def test_already_registered_error_stores_extension_name():
    """
        Test that ExtensionAlreadyRegisteredError stores the extension name.
    """
    err = ExtensionAlreadyRegisteredError("dup-ext")

    if err.extension_name != "dup-ext":
        errmsg = f"Expected extension_name 'dup-ext', got '{err.extension_name}'"
        raise AssertionError(errmsg)

    return


def test_already_registered_error_inherits_extension_error():
    """
        Test that ExtensionAlreadyRegisteredError inherits from ExtensionError.
    """
    err = ExtensionAlreadyRegisteredError("dup-ext")

    if not isinstance(err, ExtensionError):
        errmsg = "Expected ExtensionAlreadyRegisteredError to be an instance of ExtensionError"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for ExtensionDependencyError
# =============================================================================

def test_dependency_error_stores_message():
    """
        Test that ExtensionDependencyError stores the message.
    """
    err = ExtensionDependencyError(
        message="Circular dependency detected",
        extension_name="ext-a"
    )

    if "Circular dependency detected" not in str(err):
        errmsg = f"Expected message to contain 'Circular dependency detected', got '{str(err)}'"
        raise AssertionError(errmsg)

    return


def test_dependency_error_stores_extension_name():
    """
        Test that ExtensionDependencyError stores the extension name.
    """
    err = ExtensionDependencyError(
        message="Missing deps",
        extension_name="ext-a"
    )

    if err.extension_name != "ext-a":
        errmsg = f"Expected extension_name 'ext-a', got '{err.extension_name}'"
        raise AssertionError(errmsg)

    return


def test_dependency_error_stores_missing_deps():
    """
        Test that ExtensionDependencyError stores the missing dependencies list.
    """
    err = ExtensionDependencyError(
        message="Missing deps",
        extension_name="ext-a",
        missing_deps=["ext-b", "ext-c"]
    )

    if err.missing_deps != ["ext-b", "ext-c"]:
        errmsg = f"Expected missing_deps ['ext-b', 'ext-c'], got {err.missing_deps}"
        raise AssertionError(errmsg)

    return


def test_dependency_error_default_missing_deps_is_empty():
    """
        Test that ExtensionDependencyError defaults missing_deps to empty list.
    """
    err = ExtensionDependencyError(
        message="Circular dependency",
        extension_name="ext-a"
    )

    if len(err.missing_deps) != 0:
        errmsg = f"Expected empty missing_deps, got {err.missing_deps}"
        raise AssertionError(errmsg)

    return


def test_dependency_error_inherits_extension_error():
    """
        Test that ExtensionDependencyError inherits from ExtensionError.
    """
    err = ExtensionDependencyError(
        message="error",
        extension_name="ext-a"
    )

    if not isinstance(err, ExtensionError):
        errmsg = "Expected ExtensionDependencyError to be an instance of ExtensionError"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for ExtensionManifestError
# =============================================================================

def test_manifest_error_stores_message():
    """
        Test that ExtensionManifestError stores the message.
    """
    err = ExtensionManifestError("Missing required field: name")

    if "Missing required field: name" not in str(err):
        errmsg = f"Expected message to contain 'Missing required field: name', got '{str(err)}'"
        raise AssertionError(errmsg)

    return


def test_manifest_error_stores_path():
    """
        Test that ExtensionManifestError stores the file path.
    """
    manifest_path = Path("/extensions/bad-ext/manifest.yaml")
    err = ExtensionManifestError("Invalid manifest", path=manifest_path)

    if err.path != manifest_path:
        errmsg = f"Expected path '{manifest_path}', got '{err.path}'"
        raise AssertionError(errmsg)

    return


def test_manifest_error_default_path_is_none():
    """
        Test that ExtensionManifestError defaults path to None.
    """
    err = ExtensionManifestError("Invalid manifest")

    if err.path is not None:
        errmsg = f"Expected path None, got '{err.path}'"
        raise AssertionError(errmsg)

    return


def test_manifest_error_inherits_extension_error():
    """
        Test that ExtensionManifestError inherits from ExtensionError.
    """
    err = ExtensionManifestError("error")

    if not isinstance(err, ExtensionError):
        errmsg = "Expected ExtensionManifestError to be an instance of ExtensionError"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for ExtensionConfigurationError
# =============================================================================

def test_configuration_error_stores_message():
    """
        Test that ExtensionConfigurationError stores the message.
    """
    err = ExtensionConfigurationError(
        message="Invalid value for 'timeout'",
        extension_name="my-ext"
    )

    if "Invalid value for 'timeout'" not in str(err):
        errmsg = f"Expected message to contain 'Invalid value for timeout', got '{str(err)}'"
        raise AssertionError(errmsg)

    return


def test_configuration_error_stores_extension_name():
    """
        Test that ExtensionConfigurationError stores the extension name.
    """
    err = ExtensionConfigurationError(
        message="error",
        extension_name="my-ext"
    )

    if err.extension_name != "my-ext":
        errmsg = f"Expected extension_name 'my-ext', got '{err.extension_name}'"
        raise AssertionError(errmsg)

    return


def test_configuration_error_stores_key():
    """
        Test that ExtensionConfigurationError stores the configuration key.
    """
    err = ExtensionConfigurationError(
        message="error",
        extension_name="my-ext",
        key="timeout"
    )

    if err.key != "timeout":
        errmsg = f"Expected key 'timeout', got '{err.key}'"
        raise AssertionError(errmsg)

    return


def test_configuration_error_default_key_is_none():
    """
        Test that ExtensionConfigurationError defaults key to None.
    """
    err = ExtensionConfigurationError(
        message="error",
        extension_name="my-ext"
    )

    if err.key is not None:
        errmsg = f"Expected key None, got '{err.key}'"
        raise AssertionError(errmsg)

    return


def test_configuration_error_inherits_extension_error():
    """
        Test that ExtensionConfigurationError inherits from ExtensionError.
    """
    err = ExtensionConfigurationError(
        message="error",
        extension_name="my-ext"
    )

    if not isinstance(err, ExtensionError):
        errmsg = "Expected ExtensionConfigurationError to be an instance of ExtensionError"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for ExtensionNotInitializedError
# =============================================================================

def test_not_initialized_error_message_contains_name():
    """
        Test that ExtensionNotInitializedError message contains the extension name.
    """
    err = ExtensionNotInitializedError("uninit-ext")

    if "uninit-ext" not in str(err):
        errmsg = f"Expected 'uninit-ext' in message, got '{str(err)}'"
        raise AssertionError(errmsg)

    return


def test_not_initialized_error_stores_extension_name():
    """
        Test that ExtensionNotInitializedError stores the extension name.
    """
    err = ExtensionNotInitializedError("uninit-ext")

    if err.extension_name != "uninit-ext":
        errmsg = f"Expected extension_name 'uninit-ext', got '{err.extension_name}'"
        raise AssertionError(errmsg)

    return


def test_not_initialized_error_inherits_extension_error():
    """
        Test that ExtensionNotInitializedError inherits from ExtensionError.
    """
    err = ExtensionNotInitializedError("uninit-ext")

    if not isinstance(err, ExtensionError):
        errmsg = "Expected ExtensionNotInitializedError to be an instance of ExtensionError"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for ExtensionContextFrozenError
# =============================================================================

def test_context_frozen_error_message_contains_name():
    """
        Test that ExtensionContextFrozenError message contains the extension name.
    """
    err = ExtensionContextFrozenError("frozen-ext")

    if "frozen-ext" not in str(err):
        errmsg = f"Expected 'frozen-ext' in message, got '{str(err)}'"
        raise AssertionError(errmsg)

    return


def test_context_frozen_error_stores_extension_name():
    """
        Test that ExtensionContextFrozenError stores the extension name.
    """
    err = ExtensionContextFrozenError("frozen-ext")

    if err.extension_name != "frozen-ext":
        errmsg = f"Expected extension_name 'frozen-ext', got '{err.extension_name}'"
        raise AssertionError(errmsg)

    return


def test_context_frozen_error_inherits_extension_error():
    """
        Test that ExtensionContextFrozenError inherits from ExtensionError.
    """
    err = ExtensionContextFrozenError("frozen-ext")

    if not isinstance(err, ExtensionError):
        errmsg = "Expected ExtensionContextFrozenError to be an instance of ExtensionError"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for HookOrderingError
# =============================================================================

def test_hook_ordering_error_stores_hook_name():
    """
        Test that HookOrderingError stores the hook name.
    """
    err = HookOrderingError(
        hook_name="before_request",
        conflicting_constraints=["ext-a before ext-b", "ext-b before ext-a"]
    )

    if err.hook_name != "before_request":
        errmsg = f"Expected hook_name 'before_request', got '{err.hook_name}'"
        raise AssertionError(errmsg)

    return


def test_hook_ordering_error_stores_conflicting_constraints():
    """
        Test that HookOrderingError stores the conflicting constraints.
    """
    constraints = ["ext-a before ext-b", "ext-b before ext-a"]
    err = HookOrderingError(
        hook_name="before_request",
        conflicting_constraints=constraints
    )

    if err.conflicting_constraints != constraints:
        errmsg = f"Expected conflicting_constraints {constraints}, got {err.conflicting_constraints}"
        raise AssertionError(errmsg)

    return


def test_hook_ordering_error_message_contains_hook_name():
    """
        Test that HookOrderingError message contains the hook name.
    """
    err = HookOrderingError(
        hook_name="after_request",
        conflicting_constraints=["conflict"]
    )

    if "after_request" not in str(err):
        errmsg = f"Expected 'after_request' in message, got '{str(err)}'"
        raise AssertionError(errmsg)

    return


def test_hook_ordering_error_inherits_extension_error():
    """
        Test that HookOrderingError inherits from ExtensionError.
    """
    err = HookOrderingError(
        hook_name="before_request",
        conflicting_constraints=["conflict"]
    )

    if not isinstance(err, ExtensionError):
        errmsg = "Expected HookOrderingError to be an instance of ExtensionError"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for ExtensionPointError
# =============================================================================

def test_extension_point_error_stores_message():
    """
        Test that ExtensionPointError stores the message.
    """
    err = ExtensionPointError(
        message="Invalid contribution",
        point_name="my.point"
    )

    if "Invalid contribution" not in str(err):
        errmsg = f"Expected message to contain 'Invalid contribution', got '{str(err)}'"
        raise AssertionError(errmsg)

    return


def test_extension_point_error_stores_point_name():
    """
        Test that ExtensionPointError stores the point name.
    """
    err = ExtensionPointError(
        message="error",
        point_name="my.extension.point"
    )

    if err.point_name != "my.extension.point":
        errmsg = f"Expected point_name 'my.extension.point', got '{err.point_name}'"
        raise AssertionError(errmsg)

    return


def test_extension_point_error_inherits_extension_error():
    """
        Test that ExtensionPointError inherits from ExtensionError.
    """
    err = ExtensionPointError(
        message="error",
        point_name="my.point"
    )

    if not isinstance(err, ExtensionError):
        errmsg = "Expected ExtensionPointError to be an instance of ExtensionError"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for Exception Raising and Catching
# =============================================================================

def test_extension_error_can_be_raised_and_caught():
    """
        Test that ExtensionError can be raised and caught as Exception.
    """
    try:
        raise ExtensionError("test error")
    except Exception as exc:
        if not isinstance(exc, ExtensionError):
            errmsg = "Expected caught exception to be ExtensionError"
            raise AssertionError(errmsg)

    return


def test_subclass_exceptions_caught_by_base():
    """
        Test that all subclass exceptions can be caught by ExtensionError.
    """
    exceptions_to_test = [
        ExtensionNotFoundError("ext"),
        ExtensionAlreadyRegisteredError("ext"),
        ExtensionDependencyError(message="dep error", extension_name="ext"),
        ExtensionManifestError("manifest error"),
        ExtensionConfigurationError(message="config error", extension_name="ext"),
        ExtensionNotInitializedError("ext"),
        ExtensionContextFrozenError("ext"),
        HookOrderingError(hook_name="hook", conflicting_constraints=["c"]),
        ExtensionPointError(message="point error", point_name="point"),
    ]

    for exc in exceptions_to_test:
        try:
            raise exc
        except ExtensionError:
            # Expected: every extension exception derives from ExtensionError.
            pass
        except Exception:
            exc_type = type(exc).__name__
            errmsg = f"Expected {exc_type} to be caught by ExtensionError handler"
            raise AssertionError(errmsg)

    return
