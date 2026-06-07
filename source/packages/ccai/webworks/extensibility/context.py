"""
    Extension context for the extensibility system.

    This module defines the ExtensionContext class that provides
    extensions with access to framework services, configuration,
    and dependency information. The context is provided to extensions
    during initialization and can be frozen to prevent modifications
    after setup is complete.
"""

import logging

from typing import Any, Dict, List, Optional, TYPE_CHECKING

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

        :param extension_name: The name of the extension this context belongs to.
        :param app_context: The application context providing framework services.
        :param config: Extension-specific configuration dictionary.
    """

    def __init__(
        self,
        extension_name: str,
        app_context: Any,
        config: Optional[Dict[str, Any]] = None
    ):
        self._extension_name = extension_name
        self._app_context = app_context
        self._config = config if config is not None else {}
        self._services: Dict[str, Any] = {}
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
    def middleware(self) -> List[Any]:
        """
            Get registered middleware.

            :returns: A list of registered middleware from the application context.
        """
        rtnval = self._app_context.middleware
        return rtnval

    def register_service(self, name: str, service: Any) -> None:
        """
            Register a service for other extensions to use.

            Services provide a mechanism for extensions to expose
            functionality to other extensions through a named
            registry.

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
            Get a registered service by name.

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
