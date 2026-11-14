"""
    Extension context for the extensibility system.

    This module defines the ExtensionContext class that provides
    extensions with access to framework services, configuration,
    and dependency information. The context is provided to extensions
    during initialization and can be frozen to prevent modifications
    after setup is complete.
"""

import logging

from typing import Any, Callable, Dict, List, Optional, TYPE_CHECKING

from ccai.webworks.extensibility.datastructures import HookPriority
from ccai.webworks.extensibility.exceptions import ExtensionContextFrozenError

if TYPE_CHECKING:
    from ccai.webworks.extensibility.extension import Extension


class ExtensionContext:
    """
        Context provided to extensions for accessing framework services.

        The ExtensionContext is created by the framework and passed to
        each extension during initialization. It provides access to
        application configuration, logging, endpoint registry, URL
        node map, middleware, and a service registry for inter-extension
        communication.

        After initialization is complete, the context can be frozen
        to prevent further modifications.

        An extension hooks into the application through its context, during
        :meth:`Extension.initialize`:

        * :meth:`register_hook` registers a callback for an application
          lifecycle hook (``on_config_loaded``, ``on_app_init``,
          ``on_routes_registered``, ``on_app_ready``, ``on_app_shutdown``),
          a request lifecycle hook (``before_first_request``,
          ``before_request``, ``after_request``, ``on_request_error``,
          ``teardown_request``) or ``on_extension_error``;
        * :attr:`component_hooks` registers components -- middleware,
          authentication providers, serializers -- with the application;
        * :attr:`endpoint_registry` takes routes, which the application
          serves when its routes are finalised.

        The service registry is what extensions use to reach each other:
        a service registered through one extension's context is found
        through every context that shares the same ``services`` map. The
        ExtensionRegistry gives all the contexts it creates one map. A
        context created without a map has a private one.

        :param extension_name: The name of the extension this context belongs to.
        :param app_context: The application context providing framework services.
        :param config: Extension-specific configuration dictionary.
        :param services: The service map shared with the contexts of other
            extensions. When None, the context keeps a map of its own.
    """

    def __init__(
        self,
        extension_name: str,
        app_context: Any,
        config: Optional[Dict[str, Any]] = None,
        services: Optional[Dict[str, Any]] = None
    ):
        self._extension_name = extension_name
        self._app_context = app_context
        self._config = config if config is not None else {}

        if services is None:
            services = {}
        self._services: Dict[str, Any] = services

        self._frozen = False
        return

    @property
    def config(self) -> Dict[str, Any]:
        """
            Get extension-specific configuration.

            :returns: A dictionary of extension-specific configuration values.
        """
        rtnval = self._config
        return rtnval

    @property
    def logger(self) -> logging.Logger:
        """
            Get a logger for this extension.

            The logger is namespaced under the extension name to
            allow filtering and identification of log messages
            from specific extensions.

            :returns: A Logger instance for this extension.
        """
        logger_name = "extension.{}".format(self._extension_name)
        rtnval = self._app_context.get_logger(logger_name)
        return rtnval

    @property
    def app_config(self) -> Any:
        """
            Get the application configuration.

            :returns: The application configuration object.
        """
        rtnval = self._app_context.config
        return rtnval

    @property
    def endpoint_registry(self) -> Any:
        """
            Get the endpoint registry.

            :returns: The endpoint registry from the application context.
        """
        rtnval = self._app_context.endpoint_registry
        return rtnval

    @property
    def url_node_map(self) -> Any:
        """
            Get the URL node map.

            :returns: The URL node map from the application context.
        """
        rtnval = self._app_context.url_node_map
        return rtnval

    @property
    def middleware(self) -> Any:
        """
            Get the application's middleware.

            For a web application this is its :class:`MiddlewareRegistry`;
            components registered through ``component_hooks`` are added
            to it.

            :returns: The middleware of the application context.
        """
        rtnval = self._app_context.middleware
        return rtnval

    @property
    def component_hooks(self) -> Any:
        """
            Get the application's component registration hooks.

            ``context.component_hooks.fire_register_middleware(component)``
            validates the component and hands it to the application's
            registry for its kind (see :class:`ComponentRegistrationHooks`).

            :returns: The ComponentRegistrationHooks of the application.
        """
        rtnval = self._app_context.component_hooks
        return rtnval

    def register_hook(
        self,
        hook_name: str,
        callback: Callable,
        priority: int = HookPriority.NORMAL,
        before: Optional[List[str]] = None,
        after: Optional[List[str]] = None
    ) -> None:
        """
            Register a callback for a hook on behalf of this extension.

            The callback is registered under this extension's name, so it is
            suspended while the extension is disabled or quarantined and its
            failures count against this extension. Hooks are registered
            while the extension initializes; the context is frozen
            afterwards.

            :param hook_name: The hook to register for, e.g. ``"before_request"``.
            :param callback: The synchronous callable to run when the hook fires.
            :param priority: Numeric priority (lower runs first).
            :param before: Names of extensions this callback runs before.
            :param after: Names of extensions this callback runs after.

            :raises ExtensionContextFrozenError: If the context is frozen.
            :raises SemanticError: If the callback is a coroutine function.
        """
        if self._frozen is True:
            raise ExtensionContextFrozenError(self._extension_name)

        hook_manager = self._app_context.extension_registry.hook_manager
        hook_manager.register(
            hook_name,
            callback,
            priority=priority,
            extension_name=self._extension_name,
            before=before,
            after=after
        )

        return

    def register_service(self, name: str, service: Any) -> None:
        """
            Register a service for other extensions to use.

            Services provide a mechanism for extensions to expose
            functionality to other extensions through a named
            registry. The service is visible through the context of
            every extension that shares this context's service map.

            :param name: The service name.
            :param service: The service instance.

            :raises: ExtensionContextFrozenError
        """
        if self._frozen is True:
            raise ExtensionContextFrozenError(self._extension_name)

        self._services[name] = service
        return

    def get_service(self, name: str) -> Optional[Any]:
        """
            Get a registered service by name, whichever extension
            registered it.

            :param name: The service name.

            :returns: The service instance or None if not found.
        """
        rtnval = self._services.get(name, None)
        return rtnval

    def has_dependency(self, name: str) -> bool:
        """
            Check if a dependency extension is available.

            Delegates to the application context registry to
            determine if the named extension is registered and
            available.

            :param name: The dependency extension name.

            :returns: True if the dependency is available, False otherwise.
        """
        registry = self._app_context.extension_registry
        extension = registry.get(name)
        rtnval = extension is not None
        return rtnval

    def get_dependency(self, name: str) -> Optional['Extension']:
        """
            Get a reference to a dependency extension.

            Delegates to the application context registry to
            retrieve the named extension instance.

            :param name: The dependency extension name.

            :returns: The dependency extension or None if not available.
        """
        registry = self._app_context.extension_registry
        rtnval = registry.get(name)
        return rtnval

    def freeze(self) -> None:
        """
            Freeze the context to prevent further modifications.

            Once frozen, any attempt to register a service will
            raise ExtensionContextFrozenError.
        """
        self._frozen = True
        return

    @property
    def frozen(self) -> bool:
        """
            Whether the context has been frozen.

            :returns: True once freeze() has been called.
        """
        rtnval = self._frozen
        return rtnval
