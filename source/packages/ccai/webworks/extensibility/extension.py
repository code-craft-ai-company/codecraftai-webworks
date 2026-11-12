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
    from ccai.webworks.extensibility.manifest import ExtensionManifest


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
        self._manifest: Optional['ExtensionManifest'] = None
        return

    @property
    def manifest(self) -> Optional['ExtensionManifest']:
        """
            Get the manifest the extension was loaded from.

            :returns: The manifest, or None for an extension that was
                      created and registered without one.
        """
        rtnval = getattr(self, "_manifest", None)
        return rtnval

    def attach_manifest(self, manifest: 'ExtensionManifest') -> None:
        """
            Attach the manifest the extension was loaded from.

            The ExtensionLoader calls this for every extension it loads.
            The registry reads the manifest's configuration schema from it
            when the extension is initialized. Metadata the class leaves at
            its default (name, version, description and the dependency
            lists) is taken from the manifest.

            :param manifest: The manifest describing this extension.
        """
        self._manifest = manifest

        if self.name == "":
            self.name = manifest.name

        if self.version == "0.0.0":
            self.version = manifest.version

        if self.description == "":
            self.description = manifest.description

        if len(self.dependencies) == 0:
            self.dependencies = list(manifest.dependencies)

        if len(self.optional_dependencies) == 0:
            self.optional_dependencies = list(manifest.optional_dependencies)

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
