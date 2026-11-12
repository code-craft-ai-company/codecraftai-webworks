"""
    Extension host of an application.

    This module defines the ExtensionHost class: the extension machinery one
    application owns -- its ExtensionRegistry and HookManager, the lifecycle,
    request and component hooks -- and the once-only transitions the
    application drives it through as it starts, serves and stops.
"""

import inspect
import logging
import os
import threading

from typing import Any, Callable, Dict, List, Optional, Union

from ccai.errors.exceptions import ConfigurationError, SemanticError

from ccai.webworks.extensibility.applicationcontext import ApplicationContext
from ccai.webworks.extensibility.applifecyclehooks import AppLifecycleHooks
from ccai.webworks.extensibility.componenthooks import ComponentRegistrationHooks
from ccai.webworks.extensibility.datastructures import ExtensionState
from ccai.webworks.extensibility.exceptions import ExtensionAlreadyRegisteredError
from ccai.webworks.extensibility.exceptions import ExtensionConfigurationError
from ccai.webworks.extensibility.exceptions import ExtensionDependencyError
from ccai.webworks.extensibility.exceptions import ExtensionLoadError
from ccai.webworks.extensibility.exceptions import ExtensionManifestError
from ccai.webworks.extensibility.extension import Extension
from ccai.webworks.extensibility.extensionsettings import ExtensionSettings
from ccai.webworks.extensibility.extensionsettings import RESERVED_SETTING_NAMES
from ccai.webworks.extensibility.hookmanager import HookManager
from ccai.webworks.extensibility.loader import ExtensionLoader
from ccai.webworks.extensibility.registry import ExtensionRegistry
from ccai.webworks.extensibility.requestlifecyclehooks import RequestLifecycleHooks


logger = logging.getLogger("ccai.webworks.extensibility.extensionhost")


class ExtensionHost:
    """
        The extension machinery of one application.

        A :class:`WebApplication` creates one in its constructor. It owns
        the application's :class:`ExtensionRegistry` and, through it, the
        one :class:`HookManager` every hook of the application runs on, and
        wraps that manager in the application lifecycle, request lifecycle
        and component registration hooks.

        The application drives it through its phases, each once:

        1. :meth:`add_extension` -- extensions the application's code adds,
           before the extensions start;
        2. :meth:`load_configured` -- the extensions the configuration names
           (see :class:`ExtensionSettings`);
        3. :meth:`start` -- every extension is initialized in dependency
           order and activated;
        4. :meth:`fire_config_loaded`, :meth:`fire_app_init`,
           :meth:`fire_routes_registered` -- as the application finalises
           its configuration and routes;
        5. :meth:`fire_app_ready` -- when the application starts serving;
           the first call fires ``on_app_ready``, later ones do nothing;
        6. :meth:`stop` -- ``on_app_shutdown``, then every extension's
           ``shutdown()`` in reverse dependency order; the first call does
           it, later ones do nothing.

        An application without extensions loads nothing, imports nothing
        and fires hooks that have no callbacks.

        :param app_context: The application context the extensions are given.
        :param component_forwarders: Mapping of component registration hook
            name to the callable that hands a component to the application's
            registry for it (see :class:`ComponentRegistrationHooks`).
    """

    def __init__(
        self,
        app_context: ApplicationContext,
        component_forwarders: Optional[Dict[str, Callable[[Any], None]]] = None
    ):
        self._app_context = app_context

        self._registry = ExtensionRegistry(app_context=app_context)
        self._hook_manager = self._registry.hook_manager

        self._app_hooks = AppLifecycleHooks(hook_manager=self._hook_manager)
        self._request_hooks = RequestLifecycleHooks(hook_manager=self._hook_manager)
        self._component_hooks = ComponentRegistrationHooks(
            hook_manager=self._hook_manager,
            forwarders=component_forwarders
        )

        app_context.bind_extensions(self._registry, self._component_hooks)

        # The phase transitions are made once each, whichever thread or
        # server event gets to them first. Re-entrant, so a hook callback
        # that reaches back into the host does not deadlock its own thread.
        self._transition_lock = threading.RLock()
        self._started = False
        self._ready_fired = False
        self._stopped = False
        return

    @property
    def app_context(self) -> ApplicationContext:
        """
            The application context the extensions are given.

            :returns: The ApplicationContext.
        """
        rtnval = self._app_context
        return rtnval

    @property
    def extension_registry(self) -> ExtensionRegistry:
        """
            The application's extension registry.

            :returns: The ExtensionRegistry.
        """
        rtnval = self._registry
        return rtnval

    @property
    def hook_manager(self) -> HookManager:
        """
            The hook manager every hook of the application runs on.

            :returns: The HookManager.
        """
        rtnval = self._hook_manager
        return rtnval

    @property
    def app_hooks(self) -> AppLifecycleHooks:
        """
            The application lifecycle hooks.

            :returns: The AppLifecycleHooks.
        """
        rtnval = self._app_hooks
        return rtnval

    @property
    def request_hooks(self) -> RequestLifecycleHooks:
        """
            The request lifecycle hooks the dispatcher fires.

            :returns: The RequestLifecycleHooks.
        """
        rtnval = self._request_hooks
        return rtnval

    @property
    def component_hooks(self) -> ComponentRegistrationHooks:
        """
            The component registration hooks.

            :returns: The ComponentRegistrationHooks.
        """
        rtnval = self._component_hooks
        return rtnval

    @property
    def started(self) -> bool:
        """
            Whether the extensions have been started.

            :returns: True once :meth:`start` has run.
        """
        rtnval = self._started
        return rtnval

    @property
    def ready_fired(self) -> bool:
        """
            Whether ``on_app_ready`` has fired.

            :returns: True once :meth:`fire_app_ready` has fired it.
        """
        rtnval = self._ready_fired
        return rtnval

    @property
    def stopped(self) -> bool:
        """
            Whether the extensions have been stopped.

            :returns: True once :meth:`stop` has run.
        """
        rtnval = self._stopped
        return rtnval

    def has_extensions(self) -> bool:
        """
            Whether any extension is registered.

            :returns: True when at least one extension is registered.
        """
        rtnval = len(self._registry.list()) > 0
        return rtnval

    def add_extension(self, extension: Union[Extension, type]) -> Extension:
        """
            Register an extension the application's code adds.

            :param extension: An Extension instance, or an Extension
                subclass, which is instantiated without arguments.

            :returns: The registered extension instance.

            :raises SemanticError: If the extensions have already been
                started, the argument is neither an Extension nor an
                Extension subclass, or the extension has no name.
            :raises ConfigurationError: If the extension's name is one of
                the settings of the ``extensions`` configuration section.
            :raises ExtensionAlreadyRegisteredError: If an extension with
                the same name is registered.
        """
        if self._started is True:
            errmsg = (
                "Extensions can only be added before the application starts them "
                "(in setup_infrastructure); {!r} was added afterwards."
            ).format(extension)
            raise SemanticError(errmsg)

        if inspect.isclass(extension) and issubclass(extension, Extension):
            instance = extension()
        elif isinstance(extension, Extension):
            instance = extension
        else:
            errmsg = "add_extension() takes an Extension instance or an Extension subclass, got {!r}".format(
                extension
            )
            raise SemanticError(errmsg)

        if not isinstance(instance.name, str) or instance.name == "":
            errmsg = "The extension {!r} has no name; set the 'name' class attribute of {}.".format(
                instance, type(instance).__name__
            )
            raise SemanticError(errmsg)

        self._check_name_is_not_reserved(instance.name, source=type(instance).__name__)

        self._registry.register(instance)

        return instance

    def load_configured(self, settings: ExtensionSettings) -> List[str]:
        """
            Load and register the extensions the configuration names: the
            import strings, the entry points, then the extensions whose
            manifests are found in the configured directories.

            Settings that ask for nothing load nothing and import nothing.
            Every extension is loaded through an :class:`ExtensionLoader`
            restricted to the configured ``allowed_packages``.

            :param settings: The application's extension settings.

            :returns: The names of the extensions that were registered.

            :raises SemanticError: If the extensions have already been started.
            :raises ConfigurationError: If a configured extension is outside
                the allowed packages, cannot be loaded, has no name, has the
                name of a setting, or has the name of an extension already
                registered.
        """
        if self._started is True:
            errmsg = "The configured extensions must be loaded before the extensions are started."
            raise SemanticError(errmsg)

        loaded_names: List[str] = []

        if settings.requests_loading() is False:
            return loaded_names

        loader = ExtensionLoader(self._registry, allowed_packages=settings.allowed_packages)

        for import_string in settings.load:
            try:
                extension = loader.load_from_import_string(import_string)
            except ExtensionLoadError as err:
                errmsg = "The extension '{}' listed in 'extensions.load' can not be loaded: {}".format(
                    import_string, err
                )
                raise ConfigurationError(errmsg) from err

            self._register_configured(extension, source="extensions.load entry '{}'".format(import_string))
            loaded_names.append(extension.name)

        for entry_point_name in settings.entry_points:
            try:
                extension = loader.load_from_entry_point(entry_point_name)
            except ExtensionLoadError as err:
                errmsg = "The extension entry point '{}' listed in 'extensions.entry_points' can not be loaded: {}".format(
                    entry_point_name, err
                )
                raise ConfigurationError(errmsg) from err

            self._register_configured(
                extension, source="extensions.entry_points entry '{}'".format(entry_point_name)
            )
            loaded_names.append(extension.name)

        for search_path in settings.paths:
            manifests = loader.discover_from_paths([search_path])

            for manifest in manifests:
                try:
                    extension = loader.load_extension(manifest)
                except ExtensionManifestError as err:
                    errmsg = "The extension '{}' found in '{}' (extensions.paths) can not be loaded: {}".format(
                        manifest.name, search_path, err
                    )
                    raise ConfigurationError(errmsg) from err

                self._register_configured(
                    extension, source="manifest of '{}' in '{}'".format(manifest.name, search_path)
                )
                loaded_names.append(extension.name)

        logger.info("Loaded configured extensions: %s", ", ".join(loaded_names))

        return loaded_names

    def start(self) -> None:
        """
            Initialize every registered extension in dependency order, then
            activate the ones that initialized. Runs once; later calls do
            nothing.

            An extension whose ``initialize()`` or ``activate()`` raises is
            logged, put in the ERROR state and left out; the others start.

            :raises ConfigurationError: If an extension's required
                dependency is missing, the dependencies are circular, or an
                extension's configuration does not satisfy its schema.
        """
        with self._transition_lock:
            if self._started is True:
                return

            self._started = True

            try:
                self._registry.initialize_all()
            except ExtensionDependencyError as err:
                errmsg = "The extensions can not be started: {}".format(err)
                raise ConfigurationError(errmsg) from err
            except ExtensionConfigurationError as err:
                errmsg = "The configuration of extension '{}' is invalid: {}".format(err.extension_name, err)
                raise ConfigurationError(errmsg) from err

            for ext_name in self._registry.initialized_names():
                if self._registry.get_state(ext_name) == ExtensionState.INITIALIZED:
                    self._registry.enable(ext_name)

        return

    def fire_config_loaded(self) -> None:
        """
            Fire ``on_config_loaded`` with the application context.
        """
        self._app_hooks.fire_on_config_loaded(self._app_context)
        return

    def fire_app_init(self) -> None:
        """
            Fire ``on_app_init`` with the application context.
        """
        self._app_hooks.fire_on_app_init(self._app_context)
        return

    def fire_routes_registered(self) -> None:
        """
            Fire ``on_routes_registered`` with the application context.
        """
        self._app_hooks.fire_on_routes_registered(self._app_context)
        return

    def fire_app_ready(self) -> None:
        """
            Fire ``on_app_ready`` with the application context, the first
            time the application starts serving. Later calls do nothing, so
            the ASGI lifespan startup and the first request -- the two places
            an application can start serving -- can both call it. Nothing
            fires once the extensions have been stopped.
        """
        if self._ready_fired is True:
            return

        with self._transition_lock:
            if self._ready_fired is True or self._stopped is True:
                return

            try:
                self._app_hooks.fire_on_app_ready(self._app_context)
            finally:
                self._ready_fired = True

        return

    def stop(self) -> None:
        """
            Stop the extensions: fire ``on_app_shutdown`` with the
            application context, then call every started extension's
            ``shutdown()`` in reverse dependency order, continuing past an
            extension whose shutdown raises (it is logged). Runs once, and
            only when the extensions were started; later calls do nothing.
        """
        with self._transition_lock:
            if self._stopped is True:
                return

            self._stopped = True

            if self._started is False:
                return

            self._app_hooks.fire_on_app_shutdown(self._app_context)

            failed_names = self._registry.shutdown_all()

        if len(failed_names) > 0:
            logger.error("Extensions whose shutdown failed: %s", ", ".join(failed_names))

        return

    def _register_configured(self, extension: Extension, source: str) -> None:
        """
            Register an extension the configuration named.

            :param extension: The loaded extension.
            :param source: Where the configuration named it, for messages.

            :raises ConfigurationError: If the extension has no name, the
                name of a setting, or the name of a registered extension.
        """
        if not isinstance(extension.name, str) or extension.name == "":
            errmsg = "The extension loaded from {} ({}) has no name; its class must set 'name'.".format(
                source, type(extension).__name__
            )
            raise ConfigurationError(errmsg)

        self._check_name_is_not_reserved(extension.name, source=source)

        try:
            self._registry.register(extension)
        except ExtensionAlreadyRegisteredError as err:
            errmsg = "The extension '{}' loaded from {} has the name of an extension that is already registered.".format(
                extension.name, source
            )
            raise ConfigurationError(errmsg) from err

        return

    def _check_name_is_not_reserved(self, extension_name: str, source: str) -> None:
        """
            Refuse an extension named like a setting of the ``extensions``
            configuration section: its configuration namespace
            (``extensions.<name>``) would be that setting.

            :param extension_name: The extension's name.
            :param source: Where the extension came from, for messages.

            :raises ConfigurationError: If the name is reserved.
        """
        if extension_name in RESERVED_SETTING_NAMES:
            errmsg_lines = [
                "The extension '{}' ({}) can not be used: its name is a setting of the "
                "'extensions' configuration section.".format(extension_name, source),
                "Reserved names: {}".format(", ".join(RESERVED_SETTING_NAMES)),
            ]
            errmsg = os.linesep.join(errmsg_lines)
            raise ConfigurationError(errmsg)

        return
