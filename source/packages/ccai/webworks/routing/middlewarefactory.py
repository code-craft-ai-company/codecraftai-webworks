"""
    .. module:: middlewarefactory
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Factory helpers for creating configurable middleware instances.

    .. moduleauthor:: Code Craft AI LLC

    This module provides the ``create_middleware`` helper function for
    instantiating middleware from factory callables with configuration
    parameters. The factory pattern enables reusable, configurable
    middleware that can be registered with the MiddlewareRegistry.
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []

from typing import Any, Callable, Union

from ccai.webworks.routing.middleware import (
    AsyncMiddleware,
    Middleware,
    _validate_middleware,
)


def create_middleware(
    factory: Callable[..., Union[Middleware, AsyncMiddleware]],
    **config: Any
) -> Union[Middleware, AsyncMiddleware]:
    """
        Instantiate middleware from a factory callable with configuration.

        The factory is invoked with the provided keyword arguments to produce
        a middleware instance. The returned instance is validated to ensure
        it conforms to the Middleware or AsyncMiddleware protocol (or is a
        plain callable with the correct signature).

        :param factory: A callable that accepts config kwargs and returns
            a middleware instance.
        :param config: Configuration keyword arguments passed to the factory.

        :returns: A configured middleware instance.

        :raises TypeError: If the factory returns an object that does not
            conform to the Middleware or AsyncMiddleware protocol and is
            not a valid callable with (request, call_next) signature.
    """
    instance = factory(**config)

    _validate_middleware(instance)

    return instance
