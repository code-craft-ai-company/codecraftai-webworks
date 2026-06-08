"""
    Extension base class for the extensibility system.

    This module defines the abstract base class that all extensions
    must subclass. It provides the lifecycle methods, metadata
    attributes, and state management that the framework uses to
    manage extensions.
"""

from abc import ABC
from typing import List, Optional, TYPE_CHECKING

from ccai.webworks.extensibility.datastructures import ExtensionState
from ccai.webworks.extensibility.exceptions import ExtensionNotInitializedError

if TYPE_CHECKING:
    from ccai.webworks.extensibility.context import ExtensionContext


class Extension(ABC):
    """
        Base class for all extensions.

        Subclass this to create custom extensions that integrate with
        the ccai web framework. Extensions declare metadata via
        class attributes and implement lifecycle methods for initialization,
        activation, deactivation, and shutdown.

        Class attributes:
            name: The unique identifier for the extension.
            version: The version string for the extension.
            description: A human-readable description of the extension.
            dependencies: List of required extension names.
            optional_dependencies: List of optional extension names.
    """

    name: str = ""
    version: str = "0.0.0"
    description: str = ""
    dependencies: List[str] = []
    optional_dependencies: List[str] = []

    def __init__(self):
        self._context: Optional['ExtensionContext'] = None
        self._state: ExtensionState = ExtensionState.REGISTERED
        return

    @property
    def context(self) -> 'ExtensionContext':
        """
            Get the extension context.

            The context provides access to framework services and is
            only available after the initialize() method has been called.

            :returns: The extension context providing access to framework services.

            :raises: ExtensionNotInitializedError
        """
        if self._context is None:
            raise ExtensionNotInitializedError(self.name)

        rtnval = self._context
        return rtnval

    @property
    def state(self) -> ExtensionState:
        """
            Get the current extension state.

            :returns: The current state of the extension.
        """
        rtnval = self._state
        return rtnval

    def initialize(self, context: 'ExtensionContext') -> None:
        """
            Initialize the extension with the provided context.

            Sets the extension context and transitions the state
            to INITIALIZED. Override this method to perform custom
            initialization logic, but call super().initialize(context)
            to ensure proper state management.

            :param context: The extension context providing framework services.
        """
        self._context = context
        self._state = ExtensionState.INITIALIZED
        return

    def activate(self) -> None:
        """
            Activate the extension.

            Called when the extension is enabled. Transitions the state
            to ACTIVE. Override this method to perform custom activation
            logic, but call super().activate() to ensure proper state
            management.
        """
        self._state = ExtensionState.ACTIVE
        return

    def deactivate(self) -> None:
        """
            Deactivate the extension.

            Called when the extension is disabled. Transitions the state
            to DISABLED. Override this method to perform custom deactivation
            logic, but call super().deactivate() to ensure proper state
            management.
        """
        self._state = ExtensionState.DISABLED
        return

    def shutdown(self) -> None:
        """
            Shutdown the extension.

            Called during application shutdown for cleanup. Override this
            method to perform custom cleanup logic such as releasing
            resources or closing connections.
        """
        return
