"""
.. module:: webapplication
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module containing the `WebApplication` class, the
        `establish_webapp_persona` factory function, and the
        `reset_webapp_persona` test helper.

.. moduleauthor:: Code Craft AI LLC
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


import functools
import logging
import os

from typing import Any, Callable, Dict, List, Optional, Pattern, Set, Tuple, Type, Union

from ccai.thisapp.persona import AppPersona, reset_app_persona
from ccai.thisapp.wellknown import (
    SINGLETON_LOCK,
    PersonaVariablesDesc,
    ThisApplication,
)
from ccai.errors.exceptions import SemanticError
from ccai.webworks.persona.lifecycle import (
    BlueprintAlreadyRegisteredError,
    EndpointConflictError,
    LifecycleError,
    LifecyclePhase,
)
from ccai.webworks.configuration.lifecycle import ManagedConfigRegistry
from ccai.webworks.authentication.middleware import AuthenticationMiddleware
from ccai.webworks.authentication.system import AuthenticationSystem
from ccai.webworks.endpoints.accesspolicy import AccessPolicy
from ccai.webworks.endpoints.constraints import EndpointConstraints
from ccai.webworks.endpoints.descriptor import EndpointDescriptor
from ccai.webworks.endpoints.doc import Doc
from ccai.webworks.endpoints.endpoint import Endpoint
from ccai.webworks.endpoints.ratelimit import RateLimit
from ccai.webworks.endpoints.descriptor import (
    REST_ERROR_MAP_TYPES_EXTRA,
    REST_REQUEST_SCHEMA_TYPE_EXTRA,
    REST_RESPONSE_SCHEMA_TYPE_EXTRA,
    record_rest_processing,
)
from ccai.webworks.endpoints.rest.middleware import RESTMiddleware, create_rest_middleware
from ccai.webworks.endpoints.rest.restprocessingrouter import RestProcessingRouter
from ccai.webworks.extensibility.applicationcontext import ApplicationContext
from ccai.webworks.extensibility.componenthooks import (
    REGISTER_AUTH_PROVIDER,
    REGISTER_MIDDLEWARE,
    REGISTER_SERIALIZER,
)
from ccai.webworks.extensibility.exceptions import ExtensionPointError
from ccai.webworks.extensibility.extension import Extension
from ccai.webworks.extensibility.extensionhost import ExtensionHost
from ccai.webworks.extensibility.extensionmiddleware import register_extension_middleware
from ccai.webworks.extensibility.extensionsettings import ExtensionSettings
from ccai.webworks.extensibility.hookmanager import HookManager
from ccai.webworks.extensibility.registry import ExtensionRegistry
from ccai.webworks.routing.dispatcher import Dispatcher
from ccai.webworks.routing.exceptions import RoutingError
from ccai.webworks.routing.middlewareregistry import MiddlewareRegistry
from ccai.webworks.asgi.application import create_asgi_application
from ccai.webworks.endpoints.registry import EndpointRegistry
from ccai.webworks.security.decorators import get_handler_policy

import ccai.webworks.wellknown as webworks_wellknown
import ccai.thisapp.wellknown as thisapp_wellknown


# Module-level logger. Lifecycle setup steps reclassify exceptions
# into ``SemanticError`` for the caller (startup must bubble); the
# operator wants the underlying traceback in the journal so a failed
# startup is debuggable from the systemd / supervisor logs alone.
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Module-level flag to prevent double establishment
# ---------------------------------------------------------------------------
WEBAPP_PERSONA_ESTABLISHED: bool = False


#: Configuration key holding the largest request body, in bytes, the ASGI
#: application reads into memory (``0`` = unlimited). When the key is not
#: set the ASGI layer's default limit applies (16 MiB, see
#: :data:`ccai.webworks.asgi.constants.DEFAULT_MAX_REQUEST_BODY_SIZE`).
MAX_REQUEST_BODY_SIZE_CONFIG_KEY: str = "server.max_request_body_size"


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------
class PersonaAlreadyEstablishedError(Exception):
    """
        Raised when attempting to establish a persona that already exists.
    """

    def __init__(self, existing_name: str):
        self.existing_name = existing_name
        super().__init__(
            f"Persona already established with name '{existing_name}'. "
            "Cannot establish a new persona."
        )
        return


# ---------------------------------------------------------------------------
# Authentication middleware bound to the router's path rules
# ---------------------------------------------------------------------------
class WebAppAuthenticationMiddleware(AuthenticationMiddleware):
    """
        The :class:`AuthenticationMiddleware` a :class:`WebApplication`
        puts in front of its ASGI application.

        The middleware decides by request path: which paths are excluded,
        which are optional, which :class:`AccessPolicy` applies. The router
        behind it matches the canonical form of a path, so ``//admin/users``
        reaches the handler registered for ``/admin/users``. The base
        :class:`AuthenticationMiddleware` compares that same canonical form
        and hands the normalised scope on to the application, and redirects
        a path with ``.`` segments, so the policy checks and the router see
        one path. This class used to add that normalisation; it is kept as
        the name of the middleware the application builds.
    """


# ---------------------------------------------------------------------------
# WebApplication
# ---------------------------------------------------------------------------
class WebApplication(ThisApplication):
    """
        Root class for web applications extending ThisApplication with
        database lifecycle hooks.

        This class provides the foundational infrastructure for web applications
        in the ccai framework, including database preparation, connection,
        startup, and readiness verification hooks.

        Routes declaring REST metadata (``request_schema``,
        ``response_schema`` or ``error_map``) are served through the REST
        request/response processing (:attr:`rest_middleware`) unless they opt
        out with ``rest_processing=False``. The application owns its
        extensions (:meth:`add_extension`, the ``extensions`` configuration
        section, :attr:`extension_registry`, :attr:`hook_manager`) and starts,
        hooks in and stops them as it goes through its lifecycle.
    """

    def __init__(self, *, name: str, logger_name: str, log_basename: str,
                 presence_dir: str, log_directory: str, settings_file: str,
                 extensions: str, service_name: str, **other):
        """
            Constructs a WebApplication object.

            :param name: A one-word short name for the application.
            :param logger_name: Name for the logger.
            :param log_basename: Base name for log files.
            :param presence_dir: The directory for application presence.
            :param log_directory: The directory for log files.
            :param settings_file: The path to the settings file.
            :param extensions: Extension modules to load.
            :param service_name: Service identifier for distributed systems.

            :raises SemanticError: If `from_establish_webapp_persona` is not passed.
        """
        if "from_establish_webapp_persona" not in other:
            errmsg = "The `WebApplication` singleton object should not be instantiated directly. " \
                     "Call `establish_webapp_persona` to establish application wide presence settings " \
                     "and then use the wellknown singleton to access the application presence instance."
            raise SemanticError(errmsg)

        # Pass from_establish_app_persona=True to satisfy parent's instantiation guard
        super().__init__(
            name=name,
            logger_name=logger_name,
            log_basename=log_basename,
            presence_dir=presence_dir,
            log_directory=log_directory,
            settings_file=settings_file,
            extensions=extensions,
            service_name=service_name,
            from_establish_app_persona=True
        )

        # Lifecycle tracking
        self._current_phase: LifecyclePhase = LifecyclePhase.CREATED

        # The endpoints belonging to THIS application. A registry is per
        # application rather than process-global, so two applications in one
        # process no longer contend for one endpoint map.
        self._registry: EndpointRegistry = EndpointRegistry()

        # The scoped middleware of this application (global, blueprint and
        # route scopes). The dispatcher composes it into every request;
        # extensions register their middleware here.
        self._middleware_registry: MiddlewareRegistry = MiddlewareRegistry()

        # The REST request/response processing the router applies to every
        # route that declares REST metadata (request_schema, response_schema
        # or error_map) and did not opt out with rest_processing=False.
        self._rest_middleware: RESTMiddleware = create_rest_middleware()

        # The extension machinery: one ExtensionRegistry and the one
        # HookManager it owns, given the application context extensions see.
        # Components extensions register are handed to this application's
        # registries by the forwarders.
        self._app_context: ApplicationContext = ApplicationContext(
            logger_name=logger_name,
            endpoint_registry=self._registry,
            middleware_registry=self._middleware_registry
        )
        self._extension_host: ExtensionHost = ExtensionHost(
            app_context=self._app_context,
            component_forwarders={
                REGISTER_MIDDLEWARE: self._register_extension_middleware,
                REGISTER_AUTH_PROVIDER: self._register_extension_auth_provider,
                REGISTER_SERIALIZER: self._register_extension_serializer,
            }
        )

        # Subsystem references (None until their setup phase completes)
        self._config = None
        self._credential_manager = None
        self._data_profile_manager = None
        self._auth_system = None
        self._auth_middleware = None
        self._router = None
        self._dispatcher = None
        self._asgi_app = None

        # The WSGI bridge, built the first time wsgi_app is read
        self._wsgi_bridge = None

        # Deferred registration queues
        self._pending_routes: List = []
        self._pending_blueprints: List = []
        self._registered_blueprints: Set = set()

        return

    @property
    def registry(self) -> EndpointRegistry:
        """
            The :class:`EndpointRegistry` holding this application's endpoints.

            Handlers decorated with ``@Endpoint.attach_at`` are only marked;
            an application declares which of them are its own by collecting
            the modules that define them, before ``startup()``::

                webapp.registry.collect_from(myapp.endpoints)
                webapp.startup()

            Available from construction -- it is not gated on a lifecycle
            phase, because collection has to happen before the router is
            built.

            :returns: This application's endpoint registry.
        """
        rtnval = self._registry
        return rtnval

    @property
    def middleware_registry(self) -> MiddlewareRegistry:
        """
            The :class:`MiddlewareRegistry` of this application.

            Middleware registered at ``scope="global"`` runs for every
            request; at ``scope="blueprint"`` (keyed by the blueprint's
            name) or ``scope="route"`` (keyed by the route's path pattern)
            it runs for the matched routes it is registered for. Middleware
            extensions register through the ``register_middleware`` hook is
            added here as global middleware.

            Available from construction; middleware registered before or
            after ``startup()`` applies to the requests that follow.

            :returns: This application's middleware registry.
        """
        rtnval = self._middleware_registry
        return rtnval

    @property
    def rest_middleware(self) -> RESTMiddleware:
        """
            The :class:`RESTMiddleware` the router applies to every route
            that declares REST metadata -- ``request_schema``,
            ``response_schema`` or ``error_map`` on ``attach_at``,
            ``attach_route`` or a blueprint route -- and did not opt out
            with ``rest_processing=False``.

            Register additional serializers on its ``serializer_registry``
            before ``startup()``; extensions do it through the
            ``register_serializer`` hook.

            :returns: This application's REST middleware.
        """
        rtnval = self._rest_middleware
        return rtnval

    @property
    def app_context(self) -> ApplicationContext:
        """
            The :class:`ApplicationContext` this application gives its
            extensions: its logger namespace, configuration, endpoint
            registry, URL node map, middleware registry, extension registry
            and component registration hooks.

            :returns: This application's context.
        """
        rtnval = self._app_context
        return rtnval

    @property
    def extension_registry(self) -> ExtensionRegistry:
        """
            The :class:`ExtensionRegistry` of this application, created with
            it. It holds the extensions added with :meth:`add_extension` and
            the ones the configuration names (the ``extensions`` section).

            :returns: This application's extension registry.
        """
        rtnval = self._extension_host.extension_registry
        return rtnval

    @property
    def hook_manager(self) -> HookManager:
        """
            The :class:`HookManager` every hook of this application runs on:
            the application lifecycle hooks, the request lifecycle hooks the
            dispatcher fires, and the component registration hooks.

            :returns: This application's hook manager.
        """
        rtnval = self._extension_host.hook_manager
        return rtnval

    @property
    def current_phase(self) -> LifecyclePhase:
        """
            Returns the current lifecycle phase of the web application.

            :returns: The current lifecycle phase.
        """
        rtnval = self._current_phase
        return rtnval

    @property
    def router(self):
        """
            Returns the Router instance owned by this web application.

            :returns: The Router instance.

            :raises LifecycleError: If the application has not yet reached
                the ``INFRASTRUCTURE_READY`` phase.
        """
        self._require_phase(LifecyclePhase.INFRASTRUCTURE_READY, "router")
        rtnval = self._router
        return rtnval

    @property
    def dispatcher(self):
        """
            Returns the Dispatcher instance owned by this web application.

            :returns: The Dispatcher instance.

            :raises LifecycleError: If the application has not yet reached
                the ``INFRASTRUCTURE_READY`` phase.
        """
        self._require_phase(LifecyclePhase.INFRASTRUCTURE_READY, "dispatcher")
        rtnval = self._dispatcher
        return rtnval

    @property
    def asgi_app(self):
        """
            Returns the ASGI callable to serve for this web application.

            This is the outermost layer of the application: the
            ASGIApplication itself, or -- once
            :meth:`configure_auth_middleware` has been called -- the
            authentication middleware wrapped around it. Read the property
            after configuring authentication; a reference taken before
            that still points at the unwrapped application.

            :returns: The ASGIApplication instance, or the
                AuthenticationMiddleware in front of it when one has been
                configured.

            :raises LifecycleError: If the application has not yet reached
                the ``INFRASTRUCTURE_READY`` phase.
        """
        self._require_phase(LifecyclePhase.INFRASTRUCTURE_READY, "asgi_app")

        if self._auth_middleware is not None:
            rtnval = self._auth_middleware
        else:
            rtnval = self._asgi_app

        return rtnval

    @property
    def wsgi_app(self):
        """
            Returns the WSGI callable (PEP 3333) to serve for this web
            application.

            The callable is an :class:`ccai.webworks.wsgi.asgibridge.ASGIBridge`
            that runs :attr:`asgi_app` on one event loop per process, so a
            request served over WSGI goes through exactly the pipeline it
            goes through over ASGI: routing, middleware, authentication
            middleware when configured, sessions and CSRF, the
            ``server.max_request_body_size`` limit, the error handlers, and
            the lifespan startup and shutdown handlers.

            :attr:`asgi_app` is read when the bridge starts in a process (at
            the first request, or when a server starts a worker), so
            authentication configured after this property was read is still
            served. The lifespan startup runs once per process before the
            first request is served; a failed startup answers every request
            with 503. The lifespan shutdown runs when the server stops the
            worker, or when the process exits.

            The same object is returned on every call. Serve it with the
            built-in server, ``prodserver``, or any WSGI server::

                server = WSGIServer(webapp.wsgi_app, ServerConfig(port=8000))
                server.serve_forever()

            WebSocket routes are served over ASGI only; WSGI has no way to
            carry them.

            :returns: The ASGIBridge serving this application.

            :raises LifecycleError: If the application has not yet reached
                the ``INFRASTRUCTURE_READY`` phase.
        """
        # Imported here: the WSGI bridge is only needed by applications
        # served over WSGI.
        from ccai.webworks.wsgi.asgibridge import ASGIBridge

        self._require_phase(LifecyclePhase.INFRASTRUCTURE_READY, "wsgi_app")

        bridge = self._wsgi_bridge

        if bridge is None:
            bridge = ASGIBridge(app_provider=lambda: self.asgi_app)
            self._wsgi_bridge = bridge

        rtnval = bridge
        return rtnval

    @property
    def config(self):
        """
            Returns the ManagedConfigRegistry instance owned by this web
            application.

            :returns: The ManagedConfigRegistry instance.

            :raises LifecycleError: If the application has not yet reached
                the ``CONFIGURED`` phase.
        """
        self._require_phase(LifecyclePhase.CONFIGURED, "config")
        rtnval = self._config
        return rtnval

    @property
    def credentials(self):
        """
            Returns the credential manager instance owned by this web
            application.

            :returns: The credential manager instance.

            :raises LifecycleError: If the application has not yet reached
                the ``CREDENTIALS_LOADED`` phase.
            :raises SemanticError: If no credential manager is integrated.
                ``setup_credentials`` is a placeholder until the
                ``codecraftai-credentials`` integration exists, so there is
                no manager to return; returning None would let a caller
                carry on as if credentials had been loaded.
        """
        self._require_phase(LifecyclePhase.CREDENTIALS_LOADED, "credentials")

        if self._credential_manager is None:
            errmsg = (
                "No credential manager is available: WebApplication.setup_credentials "
                "is a placeholder that loads no credential store until the "
                "codecraftai-credentials integration is wired in. Override "
                "setup_credentials to provide one."
            )
            raise SemanticError(errmsg)

        rtnval = self._credential_manager
        return rtnval

    @property
    def data_profiles(self):
        """
            Returns the data profile manager instance owned by this web
            application.

            :returns: The data profile manager instance.

            :raises LifecycleError: If the application has not yet reached
                the ``DATA_PROFILES_LOADED`` phase.
            :raises SemanticError: If no data profile manager is integrated.
                ``setup_data_profiles`` is a placeholder until the
                ``codecraftai-dataprofiles`` integration exists, so there is
                no manager to return.
        """
        self._require_phase(LifecyclePhase.DATA_PROFILES_LOADED, "data_profiles")

        if self._data_profile_manager is None:
            errmsg = (
                "No data profile manager is available: WebApplication.setup_data_profiles "
                "is a placeholder that loads no data profile source until the "
                "codecraftai-dataprofiles integration is wired in. Override "
                "setup_data_profiles to provide one."
            )
            raise SemanticError(errmsg)

        rtnval = self._data_profile_manager
        return rtnval

    @property
    def auth_system(self):
        """
            Returns the AuthenticationSystem instance owned by this web
            application.

            :returns: The AuthenticationSystem instance.

            :raises LifecycleError: If the application has not yet reached
                the ``AUTHENTICATION_READY`` phase.
        """
        self._require_phase(LifecyclePhase.AUTHENTICATION_READY, "auth_system")
        rtnval = self._auth_system
        return rtnval

    def _require_phase(self, required: LifecyclePhase, operation: str) -> None:
        """
            Verifies that the application has reached at least the required
            lifecycle phase, and has not been shut down, before allowing an
            operation to proceed.

            ``SHUTDOWN`` is terminal: it is the last phase in order, but the
            subsystems have been released by then, so an operation that
            needs them is refused rather than handed ``None``.

            :param required: The minimum lifecycle phase that must have been
                reached.
            :param operation: A descriptive name for the operation being
                attempted, used in the error message if the check fails.

            :raises LifecycleError: If the current phase ordinal is below the
                required phase ordinal, or the application has been shut
                down.
        """
        phase_order = list(LifecyclePhase)
        current_index = phase_order.index(self._current_phase)
        required_index = phase_order.index(required)

        is_shut_down = self._current_phase == LifecyclePhase.SHUTDOWN and required != LifecyclePhase.SHUTDOWN

        if current_index < required_index or is_shut_down:
            raise LifecycleError(
                operation=operation,
                required_phase=required,
                current_phase=self._current_phase
            )

        return

    def _require_exact_phase(self, required: LifecyclePhase, operation: str) -> None:
        """
            Verifies that the application is in exactly the required
            lifecycle phase.

            Each setup step runs once, right after its predecessor. Running
            one again later would move the phase backwards (a second
            ``setup_configuration`` at ``READY`` would report ``CONFIGURED``)
            and rebuild a subsystem the others already hold.

            :param required: The phase the application must be in.
            :param operation: A descriptive name for the operation being
                attempted, used in the error message if the check fails.

            :raises LifecycleError: If the current phase is any other phase.
        """
        if self._current_phase != required:
            raise LifecycleError(
                operation=operation,
                required_phase=required,
                current_phase=self._current_phase
            )

        return

    def _is_infrastructure_ready(self, operation: str) -> bool:
        """
            Tells whether routes are added to the router directly (the
            infrastructure is built) or queued for ``setup_infrastructure``.

            :param operation: A descriptive name for the operation being
                attempted, used in the error message if the check fails.

            :returns: True once the phase has reached ``INFRASTRUCTURE_READY``.

            :raises LifecycleError: If the application has been shut down;
                its router is gone and routes can not be added any more.
        """
        if self._current_phase == LifecyclePhase.SHUTDOWN:
            raise LifecycleError(
                operation=operation,
                required_phase=LifecyclePhase.INFRASTRUCTURE_READY,
                current_phase=self._current_phase
            )

        phase_order = list(LifecyclePhase)
        current_index = phase_order.index(self._current_phase)
        infra_index = phase_order.index(LifecyclePhase.INFRASTRUCTURE_READY)

        rtnval = current_index >= infra_index
        return rtnval

    def _record_in_registry(self, descriptors: Any) -> None:
        """
            Records descriptors that were added to the router outside the
            registry -- by ``attach_route`` or a mounted blueprint -- in this
            application's :class:`EndpointRegistry`, so they appear in the
            OpenAPI document and the security map like collected endpoints.

            The router has already accepted the descriptors, and it is the
            one that decides conflicts; the registry mirrors what is served.

            When the application has extensions and its routes have been
            finalised, the descriptors are also described in the URL node
            map extensions read (see :meth:`_describe_routes_for_extensions`).

            :param descriptors: The descriptors, or whatever a blueprint's
                ``register()`` returned (a value that is not a list of
                descriptors records nothing).
        """
        recorded: List[EndpointDescriptor] = []

        if isinstance(descriptors, (list, tuple)):
            for descriptor in descriptors:
                if isinstance(descriptor, EndpointDescriptor):
                    self._registry.register(descriptor, on_conflict="replace")
                    recorded.append(descriptor)

        if self._is_infrastructure_ready("record routes") is True:
            # Routes added once the infrastructure is built; the ones queued
            # before are described when setup_infrastructure finalises them.
            self._describe_routes_for_extensions(recorded)

        return

    def _describe_routes_for_extensions(self, descriptors: List[EndpointDescriptor]) -> None:
        """
            Describe served routes in the URL node map of the application
            context, which extensions read.

            The map exists for extensions, so an application without
            extensions leaves it empty.

            :param descriptors: The descriptors of the routes being served.

            :raises HandlerConflictError: If two routes differing only by a
                trailing slash have different handlers for one method; the
                URL node map does not tell such paths apart.
        """
        if self._extension_host.has_extensions() is True:
            self._app_context.url_node_map.load_descriptors(descriptors)

        return

    def _advance_phase(self, phase: LifecyclePhase) -> None:
        """
            Advances the application to the specified lifecycle phase.

            :param phase: The lifecycle phase to advance to.
        """
        self._current_phase = phase
        return

    # ------------------------------------------------------------------
    # Registration API
    # ------------------------------------------------------------------

    def attach_route(
        self,
        path: str,
        methods: Optional[List[str]] = None,
        version: Optional[str] = None,
        tags: Optional[List[str]] = None,
        access_policy: Optional[AccessPolicy] = None,
        rate_limit: Optional[RateLimit] = None,
        request_schema: Optional[Type] = None,
        response_schema: Optional[Type] = None,
        error_map: Optional[Dict[int, Type]] = None,
        doc: Optional[Doc] = None,
        rest_processing: bool = True
    ) -> Callable:
        """
            Decorator that registers a handler function as an endpoint on
            this web application.

            Creates an :class:`EndpointDescriptor` from the given *path*,
            *methods*, metadata and the decorated function.  If the
            application has already reached the ``INFRASTRUCTURE_READY``
            phase the descriptor is added directly to the
            :class:`Router`; otherwise it is queued in ``_pending_routes``
            and flushed during ``setup_infrastructure``.

            The metadata is the same that :meth:`Endpoint.attach_at`
            records, and it has the same effect: the access policy is
            enforced when the route is requested, and the tags, summary and
            schemas appear in the security map and the OpenAPI document.
            A policy attached to the handler by ``@require_auth``,
            ``@require_roles``, ``@require_scopes`` or ``@public_endpoint``
            is merged with *access_policy*. A keyword argument that is not
            listed here is an error rather than being dropped, so a
            mistyped ``access_policy`` can not leave a route unprotected.

            A route declared with a ``request_schema``, ``response_schema``
            or ``error_map`` is served through the REST request/response
            processing, like an ``attach_at`` route: content negotiation
            (406/415), body validation (400; the handler reads the validated
            payload with ``get_rest_payload(request)``), serialization of
            the result with the status the REST conventions select (201 for
            a POST, 204 for a DELETE without content) and ``RESTError``
            bodies for errors. ``rest_processing=False`` opts a handler that
            parses the body and shapes the response itself out; its schemas
            then only document it.

            The decorator preserves the original function's ``__name__``
            and ``__doc__`` via :func:`functools.wraps`.

            :param path: The URL path pattern for the endpoint (e.g.
                ``"/api/status"``).
            :param methods: A list of HTTP methods the endpoint responds
                to.  Defaults to ``["GET"]`` when *None*.
            :param version: API version string.
            :param tags: Documentation tags.
            :param access_policy: Security policy for the endpoint.
            :param rate_limit: Rate limiting configuration.
            :param request_schema: Request body schema (dataclass or Pydantic).
            :param response_schema: Response body schema.
            :param error_map: Mapping of status codes to error schemas.
            :param doc: Documentation object with summary/description.
            :param rest_processing: False to serve a handler declared with
                REST metadata without the REST request/response processing.

            :returns: A decorator that wraps the handler and registers it.

            :raises EndpointConflictError: If the path and method
                combination conflicts with an already-registered endpoint.

            Example::

                @app.attach_route("/api/status", methods=["GET"])
                def get_status(request):
                    return {"status": "ok"}

                @app.attach_route("/admin", access_policy=AccessPolicy(roles=["admin"]))
                def admin_home(request):
                    return {"area": "admin"}
        """

        resolved_methods = methods if methods is not None else ["GET"]

        def decorator(func: Callable) -> Callable:

            @functools.wraps(func)
            def wrapper(*args, **kw):
                return func(*args, **kw)

            # Honor any AccessPolicy attached to the handler by a security
            # decorator, combined with the explicit access_policy so both
            # must be satisfied.
            merged_access_policy = access_policy
            handler_policy = get_handler_policy(func)
            if handler_policy is not None:
                if merged_access_policy is None:
                    merged_access_policy = handler_policy
                else:
                    merged_access_policy = merged_access_policy.merge_with(handler_policy)

            constraints = EndpointConstraints(
                access_policy=merged_access_policy,
                rate_limit=rate_limit,
                scopes=merged_access_policy.scopes if merged_access_policy else [],
                roles=merged_access_policy.roles if merged_access_policy else []
            )

            extras_dict: Dict[str, Any] = {}

            if request_schema is not None or response_schema is not None or error_map is not None:
                # Recorded as Endpoint.attach_at records it: the inspected
                # JSON schema for documentation, and the schema class beside
                # it, which validation and serialization need.
                rest_extras: Dict[str, Any] = {}
                if request_schema is not None:
                    rest_extras["request_schema"] = Endpoint._inspect_schema(request_schema)
                    rest_extras[REST_REQUEST_SCHEMA_TYPE_EXTRA] = request_schema
                if response_schema is not None:
                    rest_extras["response_schema"] = Endpoint._inspect_schema(response_schema)
                    rest_extras[REST_RESPONSE_SCHEMA_TYPE_EXTRA] = response_schema
                if error_map is not None:
                    rest_extras["error_map"] = {
                        code: Endpoint._inspect_schema(schema)
                        for code, schema in error_map.items()
                    }
                    rest_extras[REST_ERROR_MAP_TYPES_EXTRA] = dict(error_map)
                record_rest_processing(rest_extras, rest_processing)
                extras_dict["rest"] = rest_extras

            descriptor = EndpointDescriptor(
                handler=wrapper,
                module=func.__module__,
                path=path,
                methods=resolved_methods,
                version=version,
                tags=list(tags) if tags is not None else [],
                constraints=constraints,
                doc=doc,
                extras=extras_dict,
            )

            if self._is_infrastructure_ready("attach_route"):
                try:
                    self._router.add_endpoint(descriptor)
                except RoutingError as exc:
                    raise EndpointConflictError(
                        path=path,
                        method=", ".join(resolved_methods),
                        detail=str(exc)
                    ) from exc
                self._record_in_registry([descriptor])
            else:
                self._pending_routes.append(descriptor)

            return wrapper

        return decorator

    def attach_blueprint_to_route(self, blueprint) -> None:
        """
            Registers all endpoints of a blueprint into this web
            application's :class:`Router` and its :class:`EndpointRegistry`.

            *blueprint* is either a :class:`Blueprint` / :class:`RestBlueprint`
            subclass, or a configured blueprint instance whose
            ``register(router=...)`` serves the instance itself -- a
            :class:`SwaggerUIBlueprint` or :class:`ReDocBlueprint` built
            with its generator, for example.

            If the application has already reached the
            ``INFRASTRUCTURE_READY`` phase the blueprint is registered
            immediately via ``blueprint.register(router=self._router)``;
            otherwise it is queued in ``_pending_blueprints`` and flushed
            during ``setup_infrastructure``. The descriptors ``register()``
            returns are also recorded in the application's registry, so the
            blueprint's routes appear in the OpenAPI document and the
            security map.

            Duplicate registration of the same blueprint is not allowed.

            :param blueprint: The blueprint class, or a configured blueprint
                instance, whose endpoints should be registered.

            :raises BlueprintAlreadyRegisteredError: If *blueprint* has
                already been registered with this web application.
            :raises LifecycleError: If the application has been shut down.

            Example::

                app.attach_blueprint_to_route(ItemsBlueprint)
                app.attach_blueprint_to_route(SwaggerUIBlueprint(generator))
        """
        infrastructure_ready = self._is_infrastructure_ready("attach_blueprint_to_route")

        if blueprint in self._registered_blueprints:
            raise BlueprintAlreadyRegisteredError(blueprint_cls=blueprint)

        self._registered_blueprints.add(blueprint)

        if infrastructure_ready:
            descriptors = blueprint.register(router=self._router)
            self._record_in_registry(descriptors)
        else:
            self._pending_blueprints.append(blueprint)

        return

    # ------------------------------------------------------------------
    # Extension API
    # ------------------------------------------------------------------

    def add_extension(self, extension: Union[Extension, Type[Extension]]) -> Extension:
        """
            Adds an extension to this application.

            Extensions come from two places, both explicit: the ones the
            application's code adds here, and the ones its configuration
            names in the ``extensions`` section (see
            :class:`ExtensionSettings`). Nothing is discovered otherwise.

            Every extension is initialized and activated in
            ``setup_infrastructure``, before the routes are finalised, so it
            can register hooks (``context.register_hook``), middleware and
            other components (``context.component_hooks``) and routes
            (``context.endpoint_registry``). Its application lifecycle hooks
            fire as the application starts (``on_config_loaded``,
            ``on_app_init``, ``on_routes_registered``), starts serving
            (``on_app_ready``) and stops (``on_app_shutdown``); its request
            hooks fire for every request.

            :param extension: An Extension instance, or an Extension
                subclass to instantiate without arguments.

            :returns: The registered extension instance.

            :raises LifecycleError: If the application has reached
                ``INFRASTRUCTURE_READY`` (its extensions have started) or
                has been shut down.
            :raises SemanticError: If the argument is not an Extension or an
                Extension subclass, or the extension has no name.
            :raises ConfigurationError: If the extension's name is a setting
                of the ``extensions`` configuration section.
            :raises ExtensionAlreadyRegisteredError: If an extension with the
                same name has been added.

            Example::

                webapp.add_extension(AuditExtension)
                webapp.startup()
        """
        if self._is_infrastructure_ready("add_extension") is True:
            raise LifecycleError(
                operation="add_extension",
                required_phase=LifecyclePhase.AUTHENTICATION_READY,
                current_phase=self._current_phase
            )

        rtnval = self._extension_host.add_extension(extension)

        return rtnval

    def _register_extension_middleware(self, component: Any) -> None:
        """
            Forwarder of the ``register_middleware`` hook: put an extension's
            middleware component on this application's pipeline as global
            middleware (see :class:`ExtensionMiddleware`).

            :param component: The middleware component, implementing
                ``process_request`` and ``process_response``.
        """
        register_extension_middleware(self._middleware_registry, component)
        return

    def _register_extension_auth_provider(self, component: Any) -> None:
        """
            Forwarder of the ``register_auth_provider`` hook: register an
            extension's authenticator with this application's
            :class:`AuthenticationSystem`, under its ``scheme`` and with its
            ``priority`` attribute (0 when it has none).

            :param component: The authenticator.

            :raises LifecycleError: If the authentication system has not been
                set up yet.
            :raises ExtensionPointError: If the authenticator has no
                ``scheme``.
        """
        self._require_phase(LifecyclePhase.AUTHENTICATION_READY, "register_auth_provider")

        scheme = getattr(component, "scheme", None)
        if not isinstance(scheme, str) or scheme == "":
            errmsg = (
                "An authentication provider registered through 'register_auth_provider' "
                "must have a non-empty 'scheme' attribute; {!r} has {!r}."
            ).format(component, scheme)
            raise ExtensionPointError(message=errmsg, point_name=REGISTER_AUTH_PROVIDER)

        priority = getattr(component, "priority", 0)
        self._auth_system.register(component, priority=priority)

        return

    def _register_extension_serializer(self, component: Any) -> None:
        """
            Forwarder of the ``register_serializer`` hook: register an
            extension's serializer with the serializer registry of this
            application's REST processing, both to serialize responses and
            to deserialize request bodies of its ``content_type``.

            :param component: The serializer, implementing ``serialize`` and
                ``deserialize``.

            :raises ExtensionPointError: If the serializer has no
                ``content_type``.
        """
        content_type = getattr(component, "content_type", None)
        if not isinstance(content_type, str) or content_type == "":
            errmsg = (
                "A serializer registered through 'register_serializer' must have a "
                "non-empty 'content_type' attribute; {!r} has {!r}."
            ).format(component, content_type)
            raise ExtensionPointError(message=errmsg, point_name=REGISTER_SERIALIZER)

        serializer_registry = self._rest_middleware.serializer_registry
        serializer_registry.register_serializer(component)
        serializer_registry.register_deserializer(component)

        return

    # ------------------------------------------------------------------
    # Authentication API
    # ------------------------------------------------------------------

    def register_authenticator(self, authenticator, priority: int = 0) -> None:
        """
            Registers an authenticator with the application's
            :class:`AuthenticationSystem`.

            The application must have reached the
            ``AUTHENTICATION_READY`` phase before this method is
            called.  The call is delegated directly to
            ``self._auth_system.register``.

            :param authenticator: The :class:`Authenticator` instance
                to register.
            :param priority: Optional priority integer controlling the
                order in which authenticators are consulted.  Lower
                values are consulted first.  Defaults to ``0``.

            :raises LifecycleError: If the current phase has not
                reached ``AUTHENTICATION_READY``.

            Example::

                app.register_authenticator(MyAuthenticator(), priority=10)
        """
        self._require_phase(LifecyclePhase.AUTHENTICATION_READY, "register_authenticator")
        self._auth_system.register(authenticator, priority=priority)

        return

    def configure_auth_middleware(
        self,
        exclude_paths: Optional[Set[str]] = None,
        optional_paths: Optional[Set[str]] = None,
        path_policies: Optional[Dict[str, AccessPolicy]] = None,
        default_policy: Optional[AccessPolicy] = None,
        realm: str = "Restricted",
        exclude_patterns: Optional[List[Union[str, Pattern]]] = None,
        optional_patterns: Optional[List[Union[str, Pattern]]] = None,
        policy_patterns: Optional[List[Tuple[Union[str, Pattern], AccessPolicy]]] = None
    ) -> AuthenticationMiddleware:
        """
            Creates an :class:`AuthenticationMiddleware` wired to this
            application's :class:`ASGIApplication` and
            :class:`AuthenticationSystem`, and puts it in front of the
            application: from this call on :attr:`asgi_app` returns the
            middleware, so serving ``webapp.asgi_app`` authenticates every
            request.

            The application must have reached the
            ``INFRASTRUCTURE_READY`` phase before this method is
            called because the middleware wraps the ASGI application.

            The middleware authenticates the request and stores the
            :class:`AuthenticationContext` on the request scope. Access to
            an endpoint is then decided twice, and both must allow it: by
            the path policies given here, and by the endpoint's own
            :class:`AccessPolicy` (``@require_roles``,
            ``attach_at(access_policy=...)``), which the dispatcher
            enforces for the matched route. An application that declares
            its policies on its endpoints can make authentication optional
            everywhere -- ``optional_patterns=["/**"]`` -- and leave the
            decision to them.

            Paths are compared in their canonical form (see
            :func:`ccai.webworks.routing.router.canonicalize_path`), the
            same form the router matches.

            :param exclude_paths: Optional set of exact URL paths that
                should bypass authentication entirely.
            :param optional_paths: Optional set of exact URL paths
                where authentication is attempted but not required.
            :param path_policies: Optional dictionary mapping exact
                URL paths to :class:`AccessPolicy` instances.
            :param default_policy: Optional default
                :class:`AccessPolicy` applied to paths without a
                specific policy.
            :param realm: The realm string used in
                ``WWW-Authenticate`` challenge headers.  Defaults to
                ``"Restricted"``.
            :param exclude_patterns: Optional list of glob strings or
                compiled patterns for paths that bypass authentication.
            :param optional_patterns: Optional list of glob strings or
                compiled patterns for paths where authentication is
                attempted but not required.
            :param policy_patterns: Optional list of
                ``(pattern, AccessPolicy)`` tuples for paths matched by
                pattern.

            :returns: The newly created
                :class:`AuthenticationMiddleware` instance.

            :raises LifecycleError: If the current phase has not
                reached ``INFRASTRUCTURE_READY``.

            Example::

                app.configure_auth_middleware(
                    exclude_paths={"/health", "/public"},
                    default_policy=AccessPolicy(require_auth=True),
                    realm="MyApp"
                )

                serve(app.asgi_app)
        """
        self._require_phase(LifecyclePhase.INFRASTRUCTURE_READY, "configure_auth_middleware")

        middleware = WebAppAuthenticationMiddleware(
            app=self._asgi_app,
            auth_system=self._auth_system,
            exclude_paths=exclude_paths,
            optional_paths=optional_paths,
            exclude_patterns=exclude_patterns,
            optional_patterns=optional_patterns,
            path_policies=path_policies,
            policy_patterns=policy_patterns,
            default_policy=default_policy,
            realm=realm,
        )

        self._auth_middleware = middleware

        return middleware

    # ------------------------------------------------------------------
    # Database hooks (overridable)
    # ------------------------------------------------------------------

    def prepare_database(self) -> None:
        """
            Hook for database preparation tasks such as running migrations.
            Override in subclasses to implement project-specific logic.
        """
        pass

    def connect_database(self) -> None:
        """
            Hook for establishing database connections and session pools.
            Override in subclasses to implement project-specific logic.
        """
        pass

    def startup_database(self) -> None:
        """
            Hook for database startup operations.
            Override in subclasses to implement project-specific logic.
        """
        pass

    def ensure_database_ready(self) -> bool:
        """
            Hook for verifying database readiness.
            Override in subclasses to implement project-specific logic.

            :returns: True if database is ready, False otherwise.
        """
        return True

    # ------------------------------------------------------------------
    # Lifecycle setup methods
    # ------------------------------------------------------------------

    def setup_configuration(self) -> None:
        """
            Initializes the application configuration subsystem.

            Creates a :class:`ManagedConfigRegistry` instance and populates
            it from the persona system via ``setup_from_persona``.  On
            success the registry is stored in ``_config`` and the lifecycle
            phase advances to ``CONFIGURED``.

            :raises SemanticError: If configuration loading or validation
                fails.  The error message includes the configuration source
                path and validation details.
        """
        self._require_exact_phase(LifecyclePhase.CREATED, "setup_configuration")

        try:
            registry = ManagedConfigRegistry()
            registry.setup_from_persona()
            self._config = registry
        except Exception as exc:
            presence_dir = AppPersona.AM_PRESENCE_DIR or "(unknown)"
            logger.exception(
                "WebApplication.setup_configuration: failed for presence_dir=%s",
                presence_dir,
            )
            errmsg = (
                f"Configuration setup failed for presence directory "
                f"'{presence_dir}': {exc}"
            )
            raise SemanticError(errmsg) from exc

        # Extensions read the application configuration (and their own
        # settings under extensions.<name>) through the application context.
        self._app_context.bind_config(self._config)

        self._advance_phase(LifecyclePhase.CONFIGURED)

        return

    def setup_credentials(self) -> None:
        """
            Initializes the credential management subsystem.

            Requires the ``CONFIGURED`` phase.  Uses the presence directory
            from the persona settings to locate credential stores.  The
            credential manager reference is stored in ``_credential_manager``
            and the lifecycle phase advances to ``CREDENTIALS_LOADED``.

            .. note::
                This is a placeholder implementation.  The actual
                ``codecraftai-credentials`` integration will be wired in when
                the package is available.  Until then no manager is stored
                and the :attr:`credentials` property raises a
                :class:`SemanticError` that says so.

            :raises LifecycleError: If the current phase is not
                ``CONFIGURED``.
            :raises SemanticError: If the credential store cannot be located
                or loaded.  The error message includes the expected
                credential store path.
        """
        self._require_exact_phase(LifecyclePhase.CONFIGURED, "setup_credentials")

        # Placeholder — store None until codecraftai-credentials is integrated.
        # A real implementation would locate and load credential stores from
        # the presence directory.
        self._credential_manager = None

        self._advance_phase(LifecyclePhase.CREDENTIALS_LOADED)

        return

    def setup_data_profiles(self) -> None:
        """
            Initializes the data profile management subsystem.

            Requires the ``CREDENTIALS_LOADED`` phase.  Uses the presence
            directory from the persona settings to locate data profile
            sources.  The data profile manager reference is stored in
            ``_data_profile_manager`` and the lifecycle phase advances to
            ``DATA_PROFILES_LOADED``.

            .. note::
                This is a placeholder implementation.  The actual
                ``codecraftai-dataprofiles`` integration will be wired in when
                the package is available.  Until then no manager is stored
                and the :attr:`data_profiles` property raises a
                :class:`SemanticError` that says so.

            :raises LifecycleError: If the current phase is not
                ``CREDENTIALS_LOADED``.
            :raises SemanticError: If the data profile source cannot be
                located or loaded.  The error message includes the expected
                data profile source path.
        """
        self._require_exact_phase(LifecyclePhase.CREDENTIALS_LOADED, "setup_data_profiles")

        # Placeholder — store None until codecraftai-dataprofiles is integrated.
        # A real implementation would locate and load data profile sources
        # from the presence directory.
        self._data_profile_manager = None

        self._advance_phase(LifecyclePhase.DATA_PROFILES_LOADED)

        return

    def setup_database(self) -> None:
        """
            Executes the database lifecycle hooks in order.

            Requires the ``DATA_PROFILES_LOADED`` phase.  Calls the
            overridable hooks ``prepare_database``, ``connect_database``,
            ``startup_database``, and ``ensure_database_ready`` in sequence.
            On success the lifecycle phase advances to ``DATABASE_READY``.

            :raises LifecycleError: If the current phase is not
                ``DATA_PROFILES_LOADED``.
            :raises SemanticError: If ``ensure_database_ready`` does not
                return True. The phase does not advance, so startup stops
                instead of serving requests against a database that
                reported itself not ready.
        """
        self._require_exact_phase(LifecyclePhase.DATA_PROFILES_LOADED, "setup_database")

        self.prepare_database()
        self.connect_database()
        self.startup_database()

        database_ready = self.ensure_database_ready()

        if database_ready is not True:
            errmsg = (
                f"Database setup failed: {type(self).__name__}.ensure_database_ready() "
                f"returned {database_ready!r}, so the database is not ready and "
                f"startup can not continue."
            )
            raise SemanticError(errmsg)

        self._advance_phase(LifecyclePhase.DATABASE_READY)

        return

    def setup_authentication(self) -> None:
        """
            Initializes the authentication subsystem.

            Requires the ``DATABASE_READY`` phase.  Creates an
            :class:`AuthenticationSystem` instance, stores it in
            ``_auth_system``, and advances the lifecycle phase to
            ``AUTHENTICATION_READY``.

            :raises LifecycleError: If the current phase is not
                ``DATABASE_READY``.
        """
        self._require_exact_phase(LifecyclePhase.DATABASE_READY, "setup_authentication")

        self._auth_system = AuthenticationSystem()

        self._advance_phase(LifecyclePhase.AUTHENTICATION_READY)

        return

    def setup_infrastructure(self) -> None:
        """
            Starts the extensions and wires the web infrastructure: Router,
            Dispatcher, and ASGIApplication.

            Requires the ``AUTHENTICATION_READY`` phase.  This method:

            1. Starts the extensions (:meth:`_start_extensions`): loads the
               ones the ``extensions`` configuration section names,
               initializes and activates every extension, then fires
               ``on_config_loaded`` and ``on_app_init``. Routes, middleware
               and other components the extensions register are in place
               before the routes are finalised.
            2. Creates a :class:`RestProcessingRouter`, a :class:`Router`
               that serves every route declaring REST metadata through the
               application's REST processing (:attr:`rest_middleware`).
            3. Loads this application's :class:`EndpointRegistry` into the
               Router.
            4. Flushes any pending routes queued via ``attach_route`` into
               the Router.
            5. Flushes any pending blueprints queued via
               ``attach_blueprint_to_route`` into the Router.
            6. Creates a :class:`Dispatcher` configured with the Router, the
               application's :attr:`middleware_registry` and the request
               lifecycle hooks. The dispatcher enforces the access policy of
               every endpoint that declares one, so no further wiring is
               needed for ``@require_roles`` and its siblings to take
               effect.
            7. Creates an :class:`ASGIApplication` via
               ``create_asgi_application()``, with the request body limit
               configured under :data:`MAX_REQUEST_BODY_SIZE_CONFIG_KEY`
               (the ASGI default of 16 MiB when it is not set), wires its
               HTTP handler to ``dispatcher.dispatch_async`` and its
               lifespan to the extensions: ``on_app_ready`` once the
               lifespan startup handlers have succeeded, ``on_app_shutdown``
               and the extensions' shutdown when the lifespan shutdown
               begins.
            8. Advances the lifecycle phase to ``INFRASTRUCTURE_READY`` and
               fires ``on_routes_registered``.

            An application served without a lifespan startup fires
            ``on_app_ready`` before its first request instead; either way it
            fires once.

            The routes queued by ``attach_route`` and the blueprints queued
            by ``attach_blueprint_to_route`` are also recorded in the
            application's registry. Nothing is published until every step
            has succeeded: if one fails, the queues are kept and the phase
            stays ``AUTHENTICATION_READY`` (the extensions, once started,
            are not started again).

            :raises LifecycleError: If the current phase is not
                ``AUTHENTICATION_READY``.
            :raises SemanticError: If the configured request body limit is
                not a non-negative integer.
            :raises ConfigurationError: If the extension configuration is
                invalid, or a configured extension is not allowed, can not
                be loaded, or misses a required dependency.
        """
        self._require_exact_phase(LifecyclePhase.AUTHENTICATION_READY, "setup_infrastructure")

        max_request_body_size = self._get_max_request_body_size()

        # 1. Start the extensions before the routes are finalised.
        self._start_extensions()

        # The infrastructure is built in locals and published only when
        # every step has succeeded, so a failed attempt leaves the pending
        # routes and blueprints queued and the phase unchanged.

        # 2. Create the Router. Every route reaches it through add_endpoint,
        # which wraps a route declaring REST metadata in the REST processing.
        router = RestProcessingRouter(rest_middleware=self._rest_middleware)

        # 3. Load this application's own endpoints into the router.
        router.load_from_registry(registry=self._registry)

        # 4. Flush pending routes
        for descriptor in self._pending_routes:
            router.add_endpoint(descriptor)

        # 5. Flush pending blueprints
        blueprint_descriptors: List[Any] = []
        for blueprint in self._pending_blueprints:
            registered = blueprint.register(router=router)
            blueprint_descriptors.append(registered)

        # 6. Create the Dispatcher
        dispatcher = Dispatcher(
            router=router,
            config=self._config,
            registry=self._middleware_registry,
            request_hooks=self._extension_host.request_hooks,
            on_first_request=self._extension_host.fire_app_ready
        )

        # 7. Create the ASGIApplication, wire the HTTP handler and tie the
        # extensions' serving lifecycle to the lifespan.
        asgi_app = create_asgi_application(max_request_body_size=max_request_body_size)
        asgi_app.http_handler.set_handler(dispatcher.dispatch_async)
        asgi_app.lifespan_handler.on_ready(self._extension_host.fire_app_ready)
        asgi_app.lifespan_handler.on_stopping(self._extension_host.stop)

        self._router = router
        self._dispatcher = dispatcher
        self._asgi_app = asgi_app

        # The routes added outside the registry are recorded in it, so the
        # OpenAPI document and the security map describe them as well.
        self._record_in_registry(self._pending_routes)
        for registered in blueprint_descriptors:
            self._record_in_registry(registered)

        self._pending_routes.clear()
        self._pending_blueprints.clear()

        # 8. Advance phase; the routes are final.
        self._advance_phase(LifecyclePhase.INFRASTRUCTURE_READY)

        self._describe_routes_for_extensions(self._registry.collect())
        self._extension_host.fire_routes_registered()

        return

    def _start_extensions(self) -> None:
        """
            Starts the extensions, once: loads the extensions the
            ``extensions`` configuration section names (nothing is imported
            when it names none), initializes and activates every registered
            extension in dependency order, and fires ``on_config_loaded``
            and ``on_app_init`` with the application context.

            :raises ConfigurationError: If the extension configuration is
                invalid, or a configured extension is not allowed, can not
                be loaded, or misses a required dependency.
        """
        host = self._extension_host

        if host.started is True:
            return

        settings = ExtensionSettings.from_config(self._config)
        host.load_configured(settings)

        host.start()

        host.fire_config_loaded()
        host.fire_app_init()

        return

    def _get_max_request_body_size(self) -> Optional[int]:
        """
            Reads the request body limit from the application configuration.

            The value is an integer, or a string of decimal digits: the
            environment configuration source yields every value as a string
            (``APP_SERVER__MAX_REQUEST_BODY_SIZE=65536``).

            :returns: The limit in bytes (``0`` = unlimited), or None when the
                configuration does not set one, which leaves the ASGI
                layer's default in place.

            :raises SemanticError: If the configured value is not a
                non-negative integer.
        """
        rtnval: Optional[int] = None

        if self._config is not None:
            configured = self._config.get(MAX_REQUEST_BODY_SIZE_CONFIG_KEY, None)

            if isinstance(configured, str):
                text = configured.strip()

                # Only plain decimal digits: int() would also accept '+5',
                # '5_0' and surrounding whitespace inside the digits.
                if text.isascii() and text.isdigit():
                    configured = int(text)

            if configured is not None:
                is_integer = isinstance(configured, int) and not isinstance(configured, bool)

                if not is_integer or configured < 0:
                    errmsg = (
                        f"The configuration value '{MAX_REQUEST_BODY_SIZE_CONFIG_KEY}' must be "
                        f"a non-negative integer number of bytes (0 for unlimited), "
                        f"got {configured!r}."
                    )
                    raise SemanticError(errmsg)

                rtnval = configured

        return rtnval

    def verify_readiness(self) -> None:
        """
            Verifies that all critical subsystems have been initialized.

            Requires the ``INFRASTRUCTURE_READY`` phase.  Checks that the
            core infrastructure references — ``_router``, ``_dispatcher``,
            ``_asgi_app``, and ``_auth_system`` — are non-None.  If any
            critical subsystem is missing, a :class:`SemanticError` is raised
            with a message listing the uninitialized subsystems.

            :raises LifecycleError: If the current phase has not reached
                ``INFRASTRUCTURE_READY``.
            :raises SemanticError: If one or more critical subsystems are
                None after infrastructure setup.
        """
        self._require_phase(LifecyclePhase.INFRASTRUCTURE_READY, "verify_readiness")

        missing = []

        if self._router is None:
            missing.append("router")
        if self._dispatcher is None:
            missing.append("dispatcher")
        if self._asgi_app is None:
            missing.append("asgi_app")
        if self._auth_system is None:
            missing.append("auth_system")

        if len(missing) > 0:
            errmsg = (
                f"Readiness verification failed. The following critical "
                f"subsystems are not initialized: {', '.join(missing)}"
            )
            raise SemanticError(errmsg)

        return

    def startup(self) -> 'WebApplication':
        """
            Executes all lifecycle phases in dependency order and returns
            the fully initialized web application.

            Calls each setup method in sequence:

            1. ``setup_configuration``
            2. ``setup_credentials``
            3. ``setup_data_profiles``
            4. ``setup_database``
            5. ``setup_authentication``
            6. ``setup_infrastructure``
            7. ``verify_readiness``

            After all phases complete successfully the lifecycle phase
            advances to ``READY``.  If any phase raises an exception,
            startup halts and the exception propagates to the caller.

            Startup runs once: each phase requires exactly its predecessor,
            so calling ``startup()`` on an application that has started, or
            has been shut down, raises :class:`LifecycleError`.

            :returns: The fully initialized WebApplication instance (``self``).

            :raises LifecycleError: If the application is not in the
                ``CREATED`` phase.
        """
        self.setup_configuration()
        self.setup_credentials()
        self.setup_data_profiles()
        self.setup_database()
        self.setup_authentication()
        self.setup_infrastructure()
        self.verify_readiness()

        self._advance_phase(LifecyclePhase.READY)

        return self

    def shutdown(self) -> None:
        """
            Tears down all subsystems in reverse lifecycle order and
            releases their resources.

            The teardown sequence is:

            0. The WSGI bridge, when :attr:`wsgi_app` has served requests in
               this process: requests in flight finish, then the ASGI
               lifespan shutdown runs (extensions and the application's
               shutdown handlers), and the bridge answers 503 from then on.
            1. Extensions: ``on_app_shutdown`` fires, then every started
               extension's ``shutdown()`` runs in reverse dependency order
               (one that raises is logged and the rest still shut down).
               Skipped when the ASGI lifespan shutdown already stopped them.
            2. ASGIApplication
            3. Dispatcher
            4. Router
            5. AuthenticationMiddleware
            6. AuthenticationSystem
            7. Database hooks (no-op — hooks are stateless by default)
            8. DataProfile_Manager
            9. Credential_Manager
            10. ManagedConfigRegistry (calls ``cleanup()`` before release)

            After all subsystems have been released the lifecycle phase
            advances to ``SHUTDOWN``, which is terminal: the subsystem
            properties, route registration and ``startup()`` raise
            :class:`LifecycleError` from then on. Calling ``shutdown()``
            again does nothing.
        """
        if self._current_phase == LifecyclePhase.SHUTDOWN:
            return

        # A WSGI-served application runs its lifespan shutdown through the
        # bridge, while the ASGI application it drives is still in place.
        # The bridge does nothing if it never started in this process.
        if self._wsgi_bridge is not None:
            self._wsgi_bridge.shutdown()

        # The extensions stop first, while the subsystems they use are
        # still in place. Once only: the lifespan shutdown may have done it.
        self._extension_host.stop()

        # Reverse order teardown — infrastructure first, then services
        self._asgi_app = None
        self._dispatcher = None
        self._router = None

        self._auth_middleware = None
        self._auth_system = None

        # Database hooks are stateless by default; nothing to release.

        self._data_profile_manager = None
        self._credential_manager = None

        # ManagedConfigRegistry requires explicit cleanup before release
        if self._config is not None:
            self._config.cleanup()
        self._config = None

        self._advance_phase(LifecyclePhase.SHUTDOWN)

        return


# ---------------------------------------------------------------------------
# Factory / Reset Functions
# ---------------------------------------------------------------------------

# The AppPersona class attributes establish_webapp_persona sets, in the
# order it sets them.
_APP_PERSONA_ATTRIBUTES: Tuple[str, ...] = (
    "AM_NAME",
    "AM_LOGGER_NAME",
    "AM_LOG_BASENAME",
    "AM_PRESENCE_DIR",
    "AM_LOG_DIRECTORY",
    "AM_SETTINGS_FILENAME",
    "AM_EXTENSIONS",
    "AM_SERVICE_NAME",
)


def _capture_app_persona() -> Dict[str, Any]:
    """
        Capture the AppPersona class attributes, so a failed
        ``establish_webapp_persona`` can put them back.

        :returns: The attribute values by name.
    """
    rtnval: Dict[str, Any] = {}

    for attribute_name in _APP_PERSONA_ATTRIBUTES:
        rtnval[attribute_name] = getattr(AppPersona, attribute_name, None)

    return rtnval


def _restore_app_persona(values: Dict[str, Any]) -> None:
    """
        Put back AppPersona class attributes captured by
        :func:`_capture_app_persona`.

        :param values: The attribute values by name.
    """
    for attribute_name, attribute_value in values.items():
        setattr(AppPersona, attribute_name, attribute_value)

    return

def establish_webapp_persona(
    *,
    name: str,
    logger_name: str,
    log_basename: str,
    presence_dir: Optional[str] = None,
    log_directory: Optional[str] = None,
    settings_file: Optional[str] = None,
    extensions: Optional[str] = None,
    service_name: Optional[str] = None,
    application_cls: Optional[Type['WebApplication']] = None
) -> 'WebApplication':
    """
        Establish the web application persona and initialize the singleton.

        Mirrors the pattern used by ccai.thisapp.persona.establish_app_persona
        but instantiates WebApplication and wires it into both wellknown modules.

        :param name: Application name used for defaults and identification.
        :param logger_name: Name for the logger.
        :param log_basename: Base name for log files.
        :param presence_dir: Root directory for app presence (defaults to ~/<name>).
        :param log_directory: Directory for log files (defaults to <presence_dir>/logs).
        :param settings_file: Path to settings file (defaults to <presence_dir>/settings.config).
        :param extensions: Extension modules to load.
        :param service_name: Service identifier for distributed systems.
        :param application_cls: Custom WebApplication subclass to instantiate.

        :returns: The initialized WebApplication singleton.

        The checks, the construction and the wiring of the singletons run
        under ``SINGLETON_LOCK``, and the persona counts as established only
        once all of it has succeeded. A call that fails -- the singleton was
        already set, the application class raised -- leaves no persona
        behind, and a later call can establish one.

        :raises PersonaAlreadyEstablishedError: If persona was already established.
        :raises SemanticError: If THISAPPLICATION_SINGLETON is already set.
    """
    global WEBAPP_PERSONA_ESTABLISHED

    # Compute default paths
    # Default presence_dir to ~/<appname>
    if presence_dir is not None:
        resolved_presence_dir = presence_dir
    else:
        resolved_presence_dir = os.path.join("~", name.lower())

    # Default log_directory to <presence_dir>/logs
    if log_directory is not None:
        resolved_log_directory = log_directory
    else:
        resolved_log_directory = os.path.join(resolved_presence_dir, "logs")

    # Default settings_file to <presence_dir>/settings.config
    if settings_file is not None:
        # If we are only given the filename, the file must be located in the presence directory
        if os.path.basename(settings_file) == settings_file:
            resolved_settings_file = os.path.join(resolved_presence_dir, settings_file)
        else:
            resolved_settings_file = os.path.abspath(
                os.path.expandvars(os.path.expanduser(settings_file))
            )
    else:
        resolved_settings_file = os.path.join(resolved_presence_dir, "settings.config")

    # Determine which class to instantiate
    if application_cls is None:
        application_cls = WebApplication

    # The checks, the construction and the wiring of the singletons happen
    # under one lock, so two threads can not both pass the checks. The
    # established flag is set only once the persona is complete: if anything
    # fails, the persona state is put back as it was and a later call can
    # try again.
    SINGLETON_LOCK.acquire()
    try:
        if WEBAPP_PERSONA_ESTABLISHED:
            raise PersonaAlreadyEstablishedError(AppPersona.AM_NAME)

        # Check that THISAPPLICATION_SINGLETON is not already set
        if thisapp_wellknown.THISAPPLICATION_SINGLETON is not None:
            errmsg = "The singleton 'wellknown.THISAPPLICATION_SINGLETON' must not be set " \
                     "when calling 'establish_webapp_persona'"
            raise SemanticError(errmsg)

        previous_persona = _capture_app_persona()
        previous_webapp_singleton = webworks_wellknown.THISWEBAPPLICATION_SINGLETON

        try:
            # Populate AppPersona class attributes (same pattern as establish_app_persona)
            AppPersona.AM_NAME = name
            AppPersona.AM_LOGGER_NAME = logger_name
            AppPersona.AM_LOG_BASENAME = log_basename
            AppPersona.AM_PRESENCE_DIR = resolved_presence_dir
            AppPersona.AM_LOG_DIRECTORY = resolved_log_directory
            AppPersona.AM_SETTINGS_FILENAME = resolved_settings_file
            AppPersona.AM_EXTENSIONS = extensions
            AppPersona.AM_SERVICE_NAME = service_name

            # Create the singleton instance
            this_app = application_cls(
                name=name,
                logger_name=logger_name,
                log_basename=log_basename,
                presence_dir=resolved_presence_dir,
                log_directory=resolved_log_directory,
                settings_file=resolved_settings_file,
                extensions=extensions,
                service_name=service_name,
                from_establish_webapp_persona=True
            )

            # Wire into both wellknown modules
            webworks_wellknown.THISWEBAPPLICATION_SINGLETON = this_app
            thisapp_wellknown.THISAPPLICATION_SINGLETON = this_app

            # Override variable values for PersonaVariablesDesc
            this_app.override_variable_value(PersonaVariablesDesc.AM_NAME, this_app.name)
            this_app.override_variable_value(PersonaVariablesDesc.AM_LOGGER_NAME, logger_name)
            this_app.override_variable_value(PersonaVariablesDesc.AM_LOG_BASENAME, log_basename)
            this_app.override_variable_value(PersonaVariablesDesc.AM_LOG_DIRECTORY, resolved_log_directory)
            this_app.override_variable_value(PersonaVariablesDesc.AM_PRESENCE_DIR, resolved_presence_dir)
            this_app.override_variable_value(PersonaVariablesDesc.AM_SERVICE_NAME, service_name)
            this_app.override_variable_value(PersonaVariablesDesc.AM_EXTENSIONS, extensions)

        except BaseException:
            # Leave no half-established persona behind.
            webworks_wellknown.THISWEBAPPLICATION_SINGLETON = previous_webapp_singleton
            thisapp_wellknown.THISAPPLICATION_SINGLETON = None
            _restore_app_persona(previous_persona)
            raise

        WEBAPP_PERSONA_ESTABLISHED = True

    finally:
        SINGLETON_LOCK.release()

    return this_app


def reset_webapp_persona() -> None:
    """
        Reset the webapp persona state for testing purposes.

        This function resets the WEBAPP_PERSONA_ESTABLISHED flag and clears
        the singleton references. It should only be used in test scenarios.

        .. warning::
            This function is intended for testing purposes only. Do not use
            in production code.
    """
    global WEBAPP_PERSONA_ESTABLISHED

    SINGLETON_LOCK.acquire()
    try:
        WEBAPP_PERSONA_ESTABLISHED = False
        webworks_wellknown.THISWEBAPPLICATION_SINGLETON = None

        # There is no endpoint registry to reset. A registry belongs to the
        # application that built it, so it goes away with the application
        # rather than needing to be scrubbed here.
        #
        # This used to call EndpointRegistry.clear(), and its placement was an
        # unwinnable choice: @Endpoint.attach_at registered into a global at
        # decoration time, so resetting after a site's endpoint imports
        # discarded the registrations it had just made and left the router
        # empty, while resetting before them let the endpoints outlive the
        # reset and collide with the next application. Registration is now
        # explicit and per-application, so neither happens.

        # Call down rather than clearing THISAPPLICATION_SINGLETON here.
        # establish_webapp_persona populates AppPersona's class attributes and
        # the base tier's singleton, so undoing only the singleton left the
        # persona attributes and APP_PERSONA_ESTABLISHED behind — enough state
        # for the next establish to trip a guard or inherit the last
        # persona's extensions.
        reset_app_persona()
    finally:
        SINGLETON_LOCK.release()

    return
