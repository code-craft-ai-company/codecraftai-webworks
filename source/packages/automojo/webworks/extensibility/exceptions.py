"""
    Exception classes for the extensibility system.

    This module defines the exception hierarchy for extension-related
    errors including registration failures, dependency issues, manifest
    parsing errors, and configuration problems.
"""

from pathlib import Path
from typing import List, Optional


class ExtensionError(Exception):
    """
        Base exception for extension errors.

        All extension-specific exceptions inherit from this class
        to allow broad exception handling when needed.

        :param message: A human-readable error description.
        :param extension_name: The name of the extension involved, if applicable.
    """

    def __init__(self, message: str, extension_name: Optional[str] = None):
        self.extension_name = extension_name
        super().__init__(message)
        return


class ExtensionNotFoundError(ExtensionError):
    """
        Raised when an extension is not found in the registry.

        :param name: The name of the extension that was not found.
    """

    def __init__(self, name: str):
        super().__init__(
            f"Extension not found: {name}",
            extension_name=name
        )
        return


class ExtensionAlreadyRegisteredError(ExtensionError):
    """
        Raised when attempting to register an extension with a duplicate name.

        :param name: The name of the extension that is already registered.
    """

    def __init__(self, name: str):
        super().__init__(
            f"Extension already registered: {name}",
            extension_name=name
        )
        return


class ExtensionDependencyError(ExtensionError):
    """
        Raised when extension dependencies cannot be resolved.

        This includes circular dependencies, missing required dependencies,
        and version conflicts.

        :param message: A human-readable error description.
        :param extension_name: The name of the extension with the dependency issue.
        :param missing_deps: List of missing dependency names, if applicable.
    """

    def __init__(self, message: str, extension_name: str, missing_deps: Optional[List[str]] = None):
        self.missing_deps = missing_deps or []
        super().__init__(message, extension_name=extension_name)
        return


class ExtensionManifestError(ExtensionError):
    """
        Raised when an extension manifest is invalid.

        This covers missing required fields, malformed content,
        and unsupported manifest formats.

        :param message: A human-readable error description.
        :param path: The file path of the invalid manifest, if applicable.
    """

    def __init__(self, message: str, path: Optional[Path] = None):
        self.path = path
        super().__init__(message)
        return


class ExtensionConfigurationError(ExtensionError):
    """
        Raised when extension configuration is invalid.

        This covers schema validation failures and missing required
        configuration values.

        :param message: A human-readable error description.
        :param extension_name: The name of the extension with the configuration issue.
        :param key: The specific configuration key that is invalid, if applicable.
    """

    def __init__(self, message: str, extension_name: str, key: Optional[str] = None):
        self.key = key
        super().__init__(message, extension_name=extension_name)
        return


class ExtensionNotInitializedError(ExtensionError):
    """
        Raised when accessing extension context before initialization.

        The extension context is only available after the initialize()
        method has been called with a valid ExtensionContext.

        :param name: The name of the extension that has not been initialized.
    """

    def __init__(self, name: str):
        super().__init__(
            f"Extension '{name}' has not been initialized. "
            "Context is only available after initialize() is called.",
            extension_name=name
        )
        return


class ExtensionContextFrozenError(ExtensionError):
    """
        Raised when attempting to modify a frozen extension context.

        Once an extension context is frozen after initialization,
        no further service registrations are allowed.

        :param extension_name: The name of the extension whose context is frozen.
    """

    def __init__(self, extension_name: str):
        super().__init__(
            f"Cannot modify context for extension '{extension_name}': context is frozen",
            extension_name=extension_name
        )
        return


class HookOrderingError(ExtensionError):
    """
        Raised when hook ordering constraints cannot be satisfied.

        This occurs when before/after constraints create circular
        dependencies or reference non-existent extensions.

        :param hook_name: The name of the hook with the ordering conflict.
        :param conflicting_constraints: List of constraint descriptions that conflict.
    """

    def __init__(self, hook_name: str, conflicting_constraints: List[str]):
        self.hook_name = hook_name
        self.conflicting_constraints = conflicting_constraints
        super().__init__(
            f"Cannot satisfy ordering constraints for hook '{hook_name}': "
            f"{', '.join(conflicting_constraints)}"
        )
        return


class ExtensionPointError(ExtensionError):
    """
        Raised when an extension point operation fails.

        This covers invalid contributions, missing extension points,
        and interface validation failures.

        :param message: A human-readable error description.
        :param point_name: The name of the extension point involved.
    """

    def __init__(self, message: str, point_name: str):
        self.point_name = point_name
        super().__init__(message)
        return
