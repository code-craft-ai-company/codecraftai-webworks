"""
    Application context for the extensibility system.

    This module defines the ApplicationContext class: the small, explicit
    object through which an application offers its services to its
    extensions. The ExtensionRegistry creates every ExtensionContext from
    it, and an ExtensionContext reads the application's services from it.
"""

import logging

from typing import Any, Optional

from ccai.webworks.urlnodemap.urlnodemap import URLNodeMap


class ApplicationContext:
    """
        What an application offers its extensions.

        :class:`ExtensionContext` and :class:`ExtensionRegistry` read
        exactly these members:

        * :meth:`get_logger` -- loggers namespaced under the application's
          logger (an extension's is ``<app logger>.extension.<name>``);
        * :attr:`config` -- the application configuration (the
          ``ManagedConfigRegistry`` once the configuration is loaded, None
          before); extension settings are read from its ``extensions``
          section;
        * :attr:`endpoint_registry` -- the application's
          :class:`EndpointRegistry`; routes an extension registers there
          before the routes are finalised are served;
        * :attr:`url_node_map` -- a :class:`URLNodeMap` of the routes the
          application serves, filled when the routes are finalised;
        * :attr:`middleware` -- the application's :class:`MiddlewareRegistry`;
        * :attr:`extension_registry` -- the :class:`ExtensionRegistry`;
        * :attr:`component_hooks` -- the :class:`ComponentRegistrationHooks`
          that hand registered components to the application's registries.

        The application creates the context with the services it has at
        construction, then binds the configuration when it is loaded
        (:meth:`bind_config`) and the extension machinery once it exists
        (:meth:`bind_extensions`); the registry needs the context to be
        created, so the two can not be passed in together.

        :param logger_name: The name of the application's logger.
        :param endpoint_registry: The application's endpoint registry.
        :param middleware_registry: The application's middleware registry.
        :param url_node_map: The URL node map to describe the application's
            routes in. A new, empty one when None.
    """

    def __init__(
        self,
        logger_name: str,
        endpoint_registry: Any,
        middleware_registry: Any,
        url_node_map: Optional[URLNodeMap] = None
    ):
        self._logger_name = logger_name
        self._config: Optional[Any] = None
        self._endpoint_registry = endpoint_registry
        self._middleware_registry = middleware_registry

        if url_node_map is None:
            url_node_map = URLNodeMap()
        self._url_node_map = url_node_map

        self._extension_registry: Optional[Any] = None
        self._component_hooks: Optional[Any] = None
        return

    @property
    def logger_name(self) -> str:
        """
            The name of the application's logger.

            :returns: The logger name extension loggers are namespaced under.
        """
        rtnval = self._logger_name
        return rtnval

    @property
    def config(self) -> Optional[Any]:
        """
            The application configuration.

            :returns: The configuration registry, or None before the
                      application has loaded its configuration.
        """
        rtnval = self._config
        return rtnval

    @property
    def endpoint_registry(self) -> Any:
        """
            The application's endpoint registry.

            :returns: The EndpointRegistry.
        """
        rtnval = self._endpoint_registry
        return rtnval

    @property
    def url_node_map(self) -> URLNodeMap:
        """
            The URL node map of the routes the application serves.

            It is filled when the application finalises its routes, so it
            is complete from the ``on_routes_registered`` hook on.

            :returns: The URLNodeMap.
        """
        rtnval = self._url_node_map
        return rtnval

    @property
    def middleware(self) -> Any:
        """
            The application's middleware registry. Middleware registered
            there at ``scope="global"`` runs for every request, at
            ``scope="blueprint"`` or ``scope="route"`` for the routes it is
            registered for.

            :returns: The MiddlewareRegistry.
        """
        rtnval = self._middleware_registry
        return rtnval

    @property
    def extension_registry(self) -> Optional[Any]:
        """
            The application's extension registry.

            :returns: The ExtensionRegistry, or None before it is bound.
        """
        rtnval = self._extension_registry
        return rtnval

    @property
    def component_hooks(self) -> Optional[Any]:
        """
            The component registration hooks of the application.

            :returns: The ComponentRegistrationHooks, or None before they
                      are bound.
        """
        rtnval = self._component_hooks
        return rtnval

    def get_logger(self, name: str) -> logging.Logger:
        """
            Get a logger namespaced under the application's logger.

            :param name: The name relative to the application's logger,
                         such as ``"extension.audit"``.

            :returns: The logger named ``<application logger>.<name>``.
        """
        logger_name = "{}.{}".format(self._logger_name, name)
        rtnval = logging.getLogger(logger_name)
        return rtnval

    def bind_config(self, config: Any) -> None:
        """
            Bind the application configuration, once it has been loaded.

            :param config: The configuration registry.
        """
        self._config = config
        return

    def bind_extensions(self, extension_registry: Any, component_hooks: Any) -> None:
        """
            Bind the extension registry and the component registration
            hooks, which are created with this context.

            :param extension_registry: The ExtensionRegistry.
            :param component_hooks: The ComponentRegistrationHooks.
        """
        self._extension_registry = extension_registry
        self._component_hooks = component_hooks
        return
