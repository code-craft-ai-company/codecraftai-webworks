"""
    Extension registry for the extensibility system.

    This module provides the ExtensionRegistry class which serves as
    the central registry for managing extensions. It handles extension
    registration, dependency resolution, lifecycle management, state
    tracking, capability querying, and error isolation.
"""

import importlib
import logging
import traceback

from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from automojo.webworks.extensibility.configuration import apply_config_defaults
from automojo.webworks.extensibility.configuration import apply_env_overrides
from automojo.webworks.extensibility.configuration import load_extension_config
from automojo.webworks.extensibility.configuration import validate_extension_config
from automojo.webworks.extensibility.context import ExtensionContext
from automojo.webworks.extensibility.datastructures import ExtensionErrorInfo
from automojo.webworks.extensibility.datastructures import ExtensionPointDefinition
from automojo.webworks.extensibility.datastructures import ExtensionState
from automojo.webworks.extensibility.exceptions import ExtensionAlreadyRegisteredError
from automojo.webworks.extensibility.exceptions import ExtensionDependencyError
from automojo.webworks.extensibility.exceptions import ExtensionNotFoundError
from automojo.webworks.extensibility.exceptions import ExtensionPointError
from automojo.webworks.extensibility.hookmanager import HookManager

if TYPE_CHECKING:
    from automojo.webworks.extensibility.extension import Extension


logger = logging.getLogger("automojo.webworks.extensibility.registry")


class ExtensionRegistry:
    """
        Central registry for managing extensions.

        The ExtensionRegistry handles extension registration, dependency
        resolution via topological sort, lifecycle management (initialize,
        activate, deactivate, reload), state tracking, capability querying,
        and error tracking with quarantine support.

        :param app_context: The application context for creating extension contexts.
    """

    def __init__(self, app_context: Any, safe_mode: bool = False):
        self._app_context = app_context
        self._extensions: Dict[str, 'Extension'] = {}
        self._extension_states: Dict[str, ExtensionState] = {}
        self._hook_manager: HookManager = HookManager()
        self._extension_points: Dict[str, ExtensionPointDefinition] = {}
        self._contributions: Dict[str, List[Any]] = {}
        self._error_counts: Dict[str, int] = {}
        self._error_threshold: int = 5
        self._safe_mode: bool = safe_mode
        return

    def register(self, extension: 'Extension') -> None:
        """
            Register an extension manually.

            Adds the extension to the registry and sets its state to
            REGISTERED. If an extension with the same name is already
            registered, raises ExtensionAlreadyRegisteredError.

            :param extension: The extension instance to register.

            :raises: ExtensionAlreadyRegisteredError
        """
        ext_name = extension.name

        if ext_name in self._extensions:
            raise ExtensionAlreadyRegisteredError(ext_name)

        self._extensions[ext_name] = extension
        self._extension_states[ext_name] = ExtensionState.REGISTERED
        self._error_counts[ext_name] = 0

        return

    def get(self, name: str) -> Optional['Extension']:
        """
            Get a registered extension by name.

            :param name: The extension name.

            :returns: The extension instance or None if not found.
        """
        rtnval = self._extensions.get(name, None)
        return rtnval

    def list(self) -> List['Extension']:
        """
            List all registered extensions.

            :returns: A list of all registered extension instances.
        """
        rtnval = list(self._extensions.values())
        return rtnval

    def _resolve_dependencies(self) -> List[str]:
        """
            Resolve extension dependencies and return initialization order.

            Builds a dependency graph from all registered extensions and
            performs a topological sort using Kahn's algorithm. If a
            circular dependency is detected, raises ExtensionDependencyError.

            :returns: A list of extension names in dependency-resolved order.

            :raises: ExtensionDependencyError
        """
        # Build adjacency list and in-degree map
        # An edge from A to B means A must be initialized before B
        # (B depends on A)
        adjacency: Dict[str, List[str]] = defaultdict(list)
        in_degree: Dict[str, int] = {}

        for ext_name in self._extensions:
            in_degree[ext_name] = 0

        for ext_name, extension in self._extensions.items():
            for dep_name in extension.dependencies:
                if dep_name in self._extensions:
                    adjacency[dep_name].append(ext_name)
                    in_degree[ext_name] = in_degree[ext_name] + 1

        # Kahn's algorithm for topological sort
        queue = []
        for ext_name in self._extensions:
            if in_degree[ext_name] == 0:
                queue.append(ext_name)

        # Sort the initial queue for deterministic ordering
        queue.sort()

        ordered = []

        while len(queue) > 0:
            current = queue.pop(0)
            ordered.append(current)

            neighbors = adjacency[current]
            # Sort neighbors for deterministic ordering
            sorted_neighbors = sorted(neighbors)

            for neighbor in sorted_neighbors:
                in_degree[neighbor] = in_degree[neighbor] - 1
                if in_degree[neighbor] == 0:
                    # Insert in sorted position to maintain deterministic order
                    inserted = False
                    for insert_pos in range(len(queue)):
                        if neighbor < queue[insert_pos]:
                            queue.insert(insert_pos, neighbor)
                            inserted = True
                            break
                    if inserted is not True:
                        queue.append(neighbor)

        if len(ordered) != len(self._extensions):
            # Circular dependency detected
            remaining = set(self._extensions.keys()) - set(ordered)
            remaining_list = sorted(remaining)
            cycle_names = ", ".join(remaining_list)

            errmsg = "Circular dependency detected among extensions: {}".format(cycle_names)
            raise ExtensionDependencyError(
                message=errmsg,
                extension_name=remaining_list[0],
                missing_deps=remaining_list
            )

        return ordered

    def initialize_all(self) -> None:
        """
            Initialize all registered extensions in dependency order.

            Resolves dependencies via topological sort, checks for missing
            required dependencies, logs warnings for missing optional
            dependencies, creates an ExtensionContext for each extension,
            and calls initialize() in the resolved order.

            When safe_mode is enabled, only extensions with a truthy
            ``core`` attribute are initialized.

            :raises: ExtensionDependencyError
        """
        # Determine which extensions to initialize
        if self._safe_mode is True:
            names_to_init = set()
            for ext_name, extension in self._extensions.items():
                is_core = getattr(extension, 'core', False)
                if is_core is True:
                    names_to_init.add(ext_name)
        else:
            names_to_init = set(self._extensions.keys())

        # Check for missing required dependencies before resolving
        for ext_name in names_to_init:
            extension = self._extensions[ext_name]
            missing_required = []
            for dep_name in extension.dependencies:
                if dep_name not in names_to_init:
                    missing_required.append(dep_name)

            if len(missing_required) > 0:
                dep_list = ", ".join(missing_required)
                errmsg = "Extension '{}' has missing required dependencies: {}".format(
                    ext_name, dep_list
                )
                raise ExtensionDependencyError(
                    message=errmsg,
                    extension_name=ext_name,
                    missing_deps=missing_required
                )

        # Log warnings for missing optional dependencies
        for ext_name in names_to_init:
            extension = self._extensions[ext_name]
            for opt_dep_name in extension.optional_dependencies:
                if opt_dep_name not in self._extensions:
                    logger.warning(
                        "Extension '%s' has missing optional dependency: '%s'",
                        ext_name, opt_dep_name
                    )

        # Resolve dependency order
        ordered_names = self._resolve_dependencies()

        # Filter to only the names we want to initialize
        ordered_names = [n for n in ordered_names if n in names_to_init]

        # Initialize extensions in dependency order
        for ext_name in ordered_names:
            extension = self._extensions[ext_name]

            # Load extension-specific config from app context
            app_config = None
            if hasattr(self._app_context, 'config'):
                app_config = self._app_context.config

            ext_config = load_extension_config(ext_name, app_config)

            # Look up the manifest config_schema if available
            config_schema = None
            manifest = getattr(extension, '_manifest', None)
            if manifest is not None:
                config_schema = getattr(manifest, 'config_schema', None)

            # Apply defaults from schema
            ext_config = apply_config_defaults(ext_config, config_schema)

            # Apply environment variable overrides
            ext_config = apply_env_overrides(ext_name, ext_config, config_schema)

            # Validate configuration against schema
            validate_extension_config(ext_name, ext_config, config_schema)

            context = ExtensionContext(
                extension_name=ext_name,
                app_context=self._app_context,
                config=ext_config
            )

            try:
                extension.initialize(context)
                self._extension_states[ext_name] = ExtensionState.INITIALIZED
            except Exception as err:
                tb_str = traceback.format_exc()
                logger.error(
                    "Extension '%s' failed during initialization: %s\n%s",
                    ext_name, err, tb_str
                )
                self._extension_states[ext_name] = ExtensionState.ERROR
                self.record_error(ext_name)
                self._fire_on_extension_error(ext_name, "initialize", err, tb_str)

        return

    def enable(self, name: str) -> None:
        """
            Enable a registered extension.

            Checks that all required dependencies are satisfied (registered
            and in ACTIVE or INITIALIZED state), then calls the extension's
            activate() method and updates the state to ACTIVE.

            :param name: The extension name.

            :raises: ExtensionNotFoundError, ExtensionDependencyError
        """
        if name not in self._extensions:
            raise ExtensionNotFoundError(name)

        extension = self._extensions[name]

        # Check that all required dependencies are satisfied
        unsatisfied_deps = []
        for dep_name in extension.dependencies:
            if dep_name not in self._extensions:
                unsatisfied_deps.append(dep_name)
            else:
                dep_state = self._extension_states.get(dep_name, ExtensionState.UNKNOWN)
                if dep_state not in (ExtensionState.ACTIVE, ExtensionState.INITIALIZED):
                    unsatisfied_deps.append(dep_name)

        if len(unsatisfied_deps) > 0:
            dep_list = ", ".join(unsatisfied_deps)
            errmsg = "Cannot enable extension '{}': unsatisfied dependencies: {}".format(
                name, dep_list
            )
            raise ExtensionDependencyError(
                message=errmsg,
                extension_name=name,
                missing_deps=unsatisfied_deps
            )

        try:
            extension.activate()
            self._extension_states[name] = ExtensionState.ACTIVE
        except Exception as err:
            tb_str = traceback.format_exc()
            logger.error(
                "Extension '%s' failed during activation: %s\n%s",
                name, err, tb_str
            )
            self._extension_states[name] = ExtensionState.ERROR
            self.record_error(name)
            self._fire_on_extension_error(name, "activate", err, tb_str)

        return

    def disable(self, name: str) -> None:
        """
            Disable an active extension.

            Calls the extension's deactivate() method and updates the
            state to DISABLED.

            :param name: The extension name.

            :raises: ExtensionNotFoundError
        """
        if name not in self._extensions:
            raise ExtensionNotFoundError(name)

        extension = self._extensions[name]

        try:
            extension.deactivate()
            self._extension_states[name] = ExtensionState.DISABLED
        except Exception as err:
            tb_str = traceback.format_exc()
            logger.error(
                "Extension '%s' failed during deactivation: %s\n%s",
                name, err, tb_str
            )
            self._extension_states[name] = ExtensionState.ERROR
            self.record_error(name)
            self._fire_on_extension_error(name, "deactivate", err, tb_str)

        return

    def get_state(self, name: str) -> ExtensionState:
        """
            Get the state of an extension.

            :param name: The extension name.

            :returns: The extension state, or UNKNOWN if not found.
        """
        rtnval = self._extension_states.get(name, ExtensionState.UNKNOWN)
        return rtnval

    def query_by_capability(self, capability: str) -> List['Extension']:
        """
            Query extensions that provide a specific capability.

            Searches through registered extension points to find
            extensions that provide the specified capability name.

            :param capability: The capability name to search for.

            :returns: A list of extensions providing the capability.
        """
        result = []

        for ext_name, extension in self._extensions.items():
            # Check if the extension has extension_points attribute
            # that declares provided capabilities
            ext_points = getattr(extension, 'extension_points', None)
            if ext_points is not None:
                if isinstance(ext_points, (list, tuple)):
                    if capability in ext_points:
                        result.append(extension)
                elif isinstance(ext_points, dict):
                    if capability in ext_points:
                        result.append(extension)

        return result

    def reload(self, name: str) -> None:
        """
            Hot-reload an extension.

            Calls deactivate() on the extension, reloads the module
            containing the extension class, and calls activate().

            :param name: The extension name.

            :raises: ExtensionNotFoundError
        """
        if name not in self._extensions:
            raise ExtensionNotFoundError(name)

        extension = self._extensions[name]

        # Step 1: Deactivate
        try:
            extension.deactivate()
            self._extension_states[name] = ExtensionState.DISABLED
        except Exception as err:
            tb_str = traceback.format_exc()
            logger.error(
                "Extension '%s' failed during deactivation in reload: %s\n%s",
                name, err, tb_str
            )
            self._extension_states[name] = ExtensionState.ERROR
            return

        # Step 2: Reload the module
        ext_module = type(extension).__module__
        try:
            module = importlib.import_module(ext_module)
            importlib.reload(module)
        except Exception as err:
            tb_str = traceback.format_exc()
            logger.error(
                "Extension '%s' failed during module reload: %s\n%s",
                name, err, tb_str
            )
            self._extension_states[name] = ExtensionState.ERROR
            return

        # Step 3: Activate
        try:
            extension.activate()
            self._extension_states[name] = ExtensionState.ACTIVE
        except Exception as err:
            tb_str = traceback.format_exc()
            logger.error(
                "Extension '%s' failed during activation in reload: %s\n%s",
                name, err, tb_str
            )
            self._extension_states[name] = ExtensionState.ERROR

        return

    def record_error(self, name: str) -> None:
        """
            Record an error for an extension and quarantine if threshold exceeded.

            Increments the error count for the named extension. If the
            error count exceeds the configured threshold, the extension
            is quarantined and its state is set to QUARANTINED.

            :param name: The extension name.
        """
        if name not in self._error_counts:
            self._error_counts[name] = 0

        self._error_counts[name] = self._error_counts[name] + 1

        current_count = self._error_counts[name]

        if current_count >= self._error_threshold:
            self._extension_states[name] = ExtensionState.QUARANTINED
            logger.warning(
                "Extension '%s' has been quarantined after %d errors (threshold: %d)",
                name, current_count, self._error_threshold
            )

        return

    def _fire_on_extension_error(
        self,
        extension_name: str,
        hook_name: str,
        exception: Exception,
        stack_trace: str
    ) -> None:
        """
            Fire the on_extension_error hook with error information.

            Creates an ExtensionErrorInfo and executes the
            on_extension_error hook so that other extensions can
            observe and react to extension errors.

            :param extension_name: The name of the extension that errored.
            :param hook_name: The hook or lifecycle phase where the error occurred.
            :param exception: The exception that was raised.
            :param stack_trace: The formatted stack trace string.
        """
        error_info = ExtensionErrorInfo(
            extension_name=extension_name,
            hook_name=hook_name,
            exception=exception,
            timestamp=datetime.utcnow(),
            stack_trace=stack_trace
        )

        try:
            self._hook_manager.execute("on_extension_error", error_info)
        except Exception as err:
            logger.error(
                "Error while firing on_extension_error hook for '%s': %s",
                extension_name, err
            )

        return

    @property
    def safe_mode(self) -> bool:
        """
            Get the safe mode flag.

            :returns: True if safe mode is enabled.
        """
        rtnval = self._safe_mode
        return rtnval

    def get_error_count(self, name: str) -> int:
        """
            Get the error count for an extension.

            :param name: The extension name.

            :returns: The number of errors recorded for the extension.
        """
        rtnval = self._error_counts.get(name, 0)
        return rtnval

    @property
    def hook_manager(self) -> HookManager:
        """
            Get the hook manager for this registry.

            :returns: The HookManager instance.
        """
        rtnval = self._hook_manager
        return rtnval

    def register_extension_point(self, definition: ExtensionPointDefinition) -> None:
        """
            Register an extension point definition.

            Adds the extension point definition to the registry so that
            contributions can be made to it via contribute_to().

            :param definition: The extension point definition to register.
        """
        self._extension_points[definition.name] = definition

        if definition.name not in self._contributions:
            self._contributions[definition.name] = []

        return

    def contribute_to(self, point_name: str, contribution: Any) -> None:
        """
            Add a contribution to an extension point.

            Validates that the contribution implements the required interface
            if one is defined for the extension point. If the extension point
            does not exist, raises ExtensionPointError. If the contribution
            does not implement the required interface, raises ExtensionPointError.

            :param point_name: The name of the extension point to contribute to.
            :param contribution: The contribution to add.

            :raises: ExtensionPointError
        """
        if point_name not in self._extension_points:
            errmsg = "Extension point '{}' is not registered".format(point_name)
            raise ExtensionPointError(message=errmsg, point_name=point_name)

        definition = self._extension_points[point_name]

        # Validate interface implementation
        required_interface = definition.interface
        if required_interface is not None:
            if not isinstance(contribution, required_interface):
                errmsg = (
                    "Contribution to extension point '{}' does not implement "
                    "the required interface '{}'".format(
                        point_name, required_interface.__name__
                    )
                )
                raise ExtensionPointError(message=errmsg, point_name=point_name)

        if point_name not in self._contributions:
            self._contributions[point_name] = []

        self._contributions[point_name].append(contribution)

        return

    def get_contributions(self, point_name: str) -> List[Any]:
        """
            Return all contributions for an extension point.

            :param point_name: The name of the extension point.

            :returns: A list of all contributions for the extension point.
        """
        rtnval = list(self._contributions.get(point_name, []))
        return rtnval

