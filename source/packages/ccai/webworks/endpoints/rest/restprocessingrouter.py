"""
.. module:: ccai.webworks.endpoints.rest.restprocessingrouter
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: The router of a web application, which serves every route
               that declares REST metadata through the REST request/response
               processing.

.. moduleauthor:: Code Craft AI LLC
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []

import dataclasses

from typing import Any, Dict, Optional

from ccai.webworks.endpoints.descriptor import (
    EndpointDescriptor,
    REST_MANAGED_EXTRA,
    declares_rest_processing,
)
from ccai.webworks.endpoints.rest.middleware import (
    RESTMiddleware,
    is_rest_processed_handler,
)
from ccai.webworks.routing.router import Router


def needs_rest_processing(descriptor: EndpointDescriptor) -> bool:
    """
        Whether a route still has to be wrapped in the REST processing: it
        declares REST metadata (a request schema, a response schema or an
        error map), did not opt out with ``rest_processing=False``, and its
        handler does not run the processing already (the generated routes
        of a :class:`ResourceEndpoint` do).

        :param descriptor: The route's descriptor.

        :returns: True when the route's handler has to be wrapped.
    """
    rtnval = False

    if declares_rest_processing(descriptor) is True:
        if is_rest_processed_handler(descriptor.handler) is False:
            rtnval = True

    return rtnval


def _find_error_map_owner(handler: Any) -> Optional[Any]:
    """
        Find the object whose ``error_map`` describes how the handler's
        exceptions are converted: the handler itself, or the endpoint
        instance (or class) a bound handler belongs to.

        :class:`RESTMiddleware` looks for it on the descriptor's handler,
        which after wrapping is the wrapper, so it is looked up here, on the
        handler as declared, and handed to the wrapper.

        :param handler: The handler as declared.

        :returns: The owner of the error map, or None.
    """
    rtnval = None

    if hasattr(handler, "error_map"):
        rtnval = handler
    else:
        owner = getattr(handler, "__self__", None)
        if owner is not None and hasattr(owner, "error_map"):
            rtnval = owner

    return rtnval


def apply_rest_processing(descriptor: EndpointDescriptor, middleware: RESTMiddleware) -> EndpointDescriptor:
    """
        Give a route whose descriptor declares REST metadata a handler that
        runs the REST request/response processing around the declared one.

        The declared descriptor is not modified -- it is the mark on the
        handler and may be served by another application as well. The route
        is served from a copy whose handler is
        ``middleware.wrap_handler(...)`` and whose ``extras["rest"]`` says
        it is REST managed; the copy is attached to the wrapper as its
        ``descriptor``, which is where the wrapper reads the route's schemas.

        A descriptor that needs no processing (see
        :func:`needs_rest_processing`) is returned as it is.

        :param descriptor: The route's descriptor as declared.
        :param middleware: The REST middleware of the application.

        :returns: The descriptor to serve the route from.
    """
    rtnval = descriptor

    if needs_rest_processing(descriptor) is True:
        declared_handler = descriptor.handler

        rest_extras: Dict[str, Any] = dict(descriptor.extras["rest"])
        rest_extras[REST_MANAGED_EXTRA] = True

        routed_extras: Dict[str, Any] = dict(descriptor.extras)
        routed_extras["rest"] = rest_extras

        routed = dataclasses.replace(descriptor, extras=routed_extras)

        wrapper = middleware.wrap_handler(
            declared_handler,
            descriptor=routed,
            endpoint=_find_error_map_owner(declared_handler)
        )
        routed.handler = wrapper

        rtnval = routed

    return rtnval


class RestProcessingRouter(Router):
    """
        The :class:`Router` a :class:`WebApplication` serves its routes from.

        It behaves like a plain router, except that every route it is given
        that declares REST metadata -- ``request_schema``,
        ``response_schema`` or ``error_map`` on ``attach_at``,
        ``attach_route`` or a blueprint route -- is served through the REST
        request/response processing: content negotiation (406/415),
        deserialization and validation of the body (400), serialization of
        the result with the status and ``Location`` the REST conventions
        select, and the ``RESTError`` error body.

        The processing is applied per route, once, when the route is added:
        the handler is wrapped with :meth:`RESTMiddleware.wrap_handler`. It
        is not a pipeline middleware, so the middleware contract of every
        other route is unchanged and only REST routes pay for it. Every way
        a route reaches the router -- :meth:`load_from_registry`, a
        blueprint's ``register(router=...)`` or :meth:`add_endpoint` -- goes
        through :meth:`add_endpoint`, so all of them are covered.

        Routes declared with ``rest_processing=False`` (the authentication
        blueprints, and handlers that parse the body and shape the response
        themselves), routes without REST metadata, and routes whose handler
        already runs the processing (:class:`ResourceEndpoint`) are added
        unchanged.

        :param rest_middleware: The REST middleware to run the routes inside.
        :param strict_slashes: If True, /path and /path/ are different routes.
        :param case_sensitive: If True, paths are matched case-sensitively.
        :param redirect_slashes: If True, redirect on trailing slash mismatch.
    """

    def __init__(
        self,
        rest_middleware: RESTMiddleware,
        strict_slashes: bool = True,
        case_sensitive: bool = True,
        redirect_slashes: bool = False
    ):
        """
            Construct a RestProcessingRouter.

            :param rest_middleware: The REST middleware to run the routes inside.
            :param strict_slashes: If True, /path and /path/ are different routes.
            :param case_sensitive: If True, paths are matched case-sensitively.
            :param redirect_slashes: If True, redirect on trailing slash mismatch.
        """
        super().__init__(
            strict_slashes=strict_slashes,
            case_sensitive=case_sensitive,
            redirect_slashes=redirect_slashes
        )
        self._rest_middleware = rest_middleware
        return

    @property
    def rest_middleware(self) -> RESTMiddleware:
        """
            The REST middleware the router's REST routes run inside.

            :returns: The RESTMiddleware instance.
        """
        rtnval = self._rest_middleware
        return rtnval

    def add_endpoint(self, descriptor: EndpointDescriptor) -> None:
        """
            Add a route, wrapping its handler in the REST processing when it
            declares REST metadata (see :func:`apply_rest_processing`).

            :param descriptor: The route's descriptor as declared.

            :raises RoutingError: If the route conflicts with an existing
                registration, or a ``path`` converter is used anywhere but
                the final segment.
        """
        routed = apply_rest_processing(descriptor, self._rest_middleware)

        super().add_endpoint(routed)

        return


__all__ = [
    "RestProcessingRouter",
    "apply_rest_processing",
    "needs_rest_processing",
]
