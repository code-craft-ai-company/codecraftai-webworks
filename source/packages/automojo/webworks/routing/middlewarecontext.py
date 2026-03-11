"""
.. module:: middlewarecontext
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Middleware context providing contextual information during request processing.

.. moduleauthor:: Automation Mojo LLC

This module provides the MiddlewareContext class that carries contextual
information available to middleware during request processing, including
the matched route descriptor, current scope, application configuration,
and a logger instance.
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []

import logging

from typing import Any, Optional

from automojo.webworks.endpoints.descriptor import EndpointDescriptor


logger = logging.getLogger(__name__)


class MiddlewareContext:
    """
        Contextual information available to middleware during request processing.

        The MiddlewareContext is attached to the Request object so middleware
        can access the matched route descriptor, current scope, application
        configuration, and a logger instance.

        :param endpoint_descriptor: The matched route's EndpointDescriptor,
            or None when middleware executes before routing.
        :param scope: The current middleware scope ("global", "blueprint", or "route").
        :param config: Application configuration object.
        :param logger: Logger instance. Defaults to the module-level logger
            when None is provided.
    """

    def __init__(
        self,
        endpoint_descriptor: Optional[EndpointDescriptor] = None,
        scope: str = "global",
        config: Optional[Any] = None,
        ctx_logger: Optional[logging.Logger] = None
    ):
        """
            Construct a MiddlewareContext.

            :param endpoint_descriptor: The matched route's EndpointDescriptor,
                or None when middleware executes before routing.
            :param scope: The current middleware scope. One of "global",
                "blueprint", or "route". Default is "global".
            :param config: Application configuration object. Default is None.
            :param ctx_logger: Logger instance. When None, defaults to the
                module-level logger.
        """
        self._endpoint_descriptor = endpoint_descriptor
        self._scope = scope
        self._config = config
        self._logger = ctx_logger if ctx_logger is not None else logger
        return

    @property
    def endpoint_descriptor(self) -> Optional[EndpointDescriptor]:
        """
            Get the matched route's EndpointDescriptor.

            Returns None when middleware is executing before routing
            has matched a route.

            :returns: The EndpointDescriptor or None.
        """
        rtnval = self._endpoint_descriptor
        return rtnval

    @property
    def scope(self) -> str:
        """
            Get the current middleware scope.

            :returns: The scope string ("global", "blueprint", or "route").
        """
        rtnval = self._scope
        return rtnval

    @property
    def config(self) -> Optional[Any]:
        """
            Get the application configuration.

            :returns: The configuration object or None.
        """
        rtnval = self._config
        return rtnval

    @property
    def logger(self) -> logging.Logger:
        """
            Get the logger instance.

            :returns: The logger instance.
        """
        rtnval = self._logger
        return rtnval

    def __repr__(self) -> str:
        """
            Get string representation.

            :returns: String representation.
        """
        descriptor_info = "None"
        if self._endpoint_descriptor is not None:
            path = self._endpoint_descriptor.path or self._endpoint_descriptor.leaf or "unknown"
            descriptor_info = f"EndpointDescriptor(path={path!r})"

        rtnval = (
            f"MiddlewareContext(endpoint_descriptor={descriptor_info}, "
            f"scope={self._scope!r})"
        )
        return rtnval
