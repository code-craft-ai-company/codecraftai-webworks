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

from typing import Callable, Dict, List, Optional, Set, Type

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
from ccai.webworks.endpoints.descriptor import EndpointDescriptor
from ccai.webworks.routing.router import Router
from ccai.webworks.routing.dispatcher import Dispatcher
from ccai.webworks.routing.exceptions import RoutingError
from ccai.webworks.asgi.application import create_asgi_application
from ccai.webworks.endpoints.registry import EndpointRegistry

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
# WebApplication
# ---------------------------------------------------------------------------
class WebApplication(ThisApplication):
    """
        Root class for web applications extending ThisApplication with
        database lifecycle hooks.

        This class provides the foundational infrastructure for web applications
        in the ccai framework, including database preparation, connection,
        startup, and readiness verification hooks.
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

        # Subsystem references (None until their setup phase completes)
        self._config = None
        self._credential_manager = None
        self._data_profile_manager = None
        self._auth_system = None
        self._auth_middleware = None
        self._router = None
        self._dispatcher = None
        self._asgi_app = None

        # Deferred registration queues
        self._pending_routes: List = []
        self._pending_blueprints: List = []
        self._registered_blueprints: Set = set()

        return

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
            Returns the ASGIApplication instance owned by this web application.

            :returns: The ASGIApplication instance.

            :raises LifecycleError: If the application has not yet reached
                the ``INFRASTRUCTURE_READY`` phase.
        """
        self._require_phase(LifecyclePhase.INFRASTRUCTURE_READY, "asgi_app")
        rtnval = self._asgi_app
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
        """
        self._require_phase(LifecyclePhase.CREDENTIALS_LOADED, "credentials")
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
        """
        self._require_phase(LifecyclePhase.DATA_PROFILES_LOADED, "data_profiles")
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
            lifecycle phase before allowing an operation to proceed.

            :param required: The minimum lifecycle phase that must have been
                reached.
            :param operation: A descriptive name for the operation being
                attempted, used in the error message if the check fails.

            :raises LifecycleError: If the current phase ordinal is below the
                required phase ordinal.
        """
        phase_order = list(LifecyclePhase)
        current_index = phase_order.index(self._current_phase)
        required_index = phase_order.index(required)

        if current_index < required_index:
            raise LifecycleError(
                operation=operation,
                required_phase=required,
                current_phase=self._current_phase
            )

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

    def attach_route(self, path: str, methods: Optional[List[str]] = None,
                     **kwargs) -> Callable:
        """
            Decorator that registers a handler function as an endpoint on
            this web application.

            Creates an :class:`EndpointDescriptor` from the given *path*,
            *methods*, and the decorated function.  If the application has
            already reached the ``INFRASTRUCTURE_READY`` phase the
            descriptor is added directly to the :class:`Router`; otherwise
            it is queued in ``_pending_routes`` and flushed during
            ``setup_infrastructure``.

            The decorator preserves the original function's ``__name__``
            and ``__doc__`` via :func:`functools.wraps`.

            :param path: The URL path pattern for the endpoint (e.g.
                ``"/api/status"``).
            :param methods: A list of HTTP methods the endpoint responds
                to.  Defaults to ``["GET"]`` when *None*.
            :param kwargs: Reserved for future extension; currently unused.

            :returns: A decorator that wraps the handler and registers it.

            :raises EndpointConflictError: If the path and method
                combination conflicts with an already-registered endpoint.

            Example::

                @app.attach_route("/api/status", methods=["GET"])
                def get_status(request):
                    return {"status": "ok"}
        """

        resolved_methods = methods if methods is not None else ["GET"]

        def decorator(func: Callable) -> Callable:

            @functools.wraps(func)
            def wrapper(*args, **kw):
                return func(*args, **kw)

            descriptor = EndpointDescriptor(
                handler=wrapper,
                module=func.__module__,
                path=path,
                methods=resolved_methods,
            )

            phase_order = list(LifecyclePhase)
            current_index = phase_order.index(self._current_phase)
            infra_index = phase_order.index(LifecyclePhase.INFRASTRUCTURE_READY)

            if current_index >= infra_index:
                try:
                    self._router.add_endpoint(descriptor)
                except RoutingError as exc:
                    raise EndpointConflictError(
                        path=path,
                        method=", ".join(resolved_methods),
                        detail=str(exc)
                    ) from exc
            else:
                self._pending_routes.append(descriptor)

            return wrapper

        return decorator

    def attach_blueprint_to_route(self, blueprint_cls) -> None:
        """
            Registers all endpoints from a :class:`Blueprint` subclass
            into this web application's :class:`Router`.

            If the application has already reached the
            ``INFRASTRUCTURE_READY`` phase the blueprint is registered
            immediately via ``blueprint_cls.register(router=self._router)``;
            otherwise the class is queued in ``_pending_blueprints`` and
            flushed during ``setup_infrastructure``.

            Duplicate registration of the same blueprint class is not
            allowed.

            :param blueprint_cls: The :class:`Blueprint` class (not an
                instance) whose endpoints should be registered.

            :raises BlueprintAlreadyRegisteredError: If *blueprint_cls*
                has already been registered with this web application.

            Example::

                app.attach_blueprint_to_route(ItemsBlueprint)
        """
        if blueprint_cls in self._registered_blueprints:
            raise BlueprintAlreadyRegisteredError(blueprint_cls=blueprint_cls)

        self._registered_blueprints.add(blueprint_cls)

        phase_order = list(LifecyclePhase)
        current_index = phase_order.index(self._current_phase)
        infra_index = phase_order.index(LifecyclePhase.INFRASTRUCTURE_READY)

        if current_index >= infra_index:
            blueprint_cls.register(router=self._router)
        else:
            self._pending_blueprints.append(blueprint_cls)

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
        realm: str = "Restricted"
    ) -> AuthenticationMiddleware:
        """
            Creates and stores an :class:`AuthenticationMiddleware`
            instance wired to this application's
            :class:`ASGIApplication` and :class:`AuthenticationSystem`.

            The application must have reached the
            ``INFRASTRUCTURE_READY`` phase before this method is
            called because the middleware wraps the ASGI application.

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

            :returns: The newly created
                :class:`AuthenticationMiddleware` instance.

            :raises LifecycleError: If the current phase has not
                reached ``INFRASTRUCTURE_READY``.

            Example::

                middleware = app.configure_auth_middleware(
                    exclude_paths={"/health", "/public"},
                    default_policy=AccessPolicy(require_auth=True),
                    realm="MyApp"
                )
        """
        self._require_phase(LifecyclePhase.INFRASTRUCTURE_READY, "configure_auth_middleware")

        middleware = AuthenticationMiddleware(
            app=self._asgi_app,
            auth_system=self._auth_system,
            exclude_paths=exclude_paths,
            optional_paths=optional_paths,
            path_policies=path_policies,
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
        self._require_phase(LifecyclePhase.CREATED, "setup_configuration")

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
                the package is available.

            :raises LifecycleError: If the current phase has not reached
                ``CONFIGURED``.
            :raises SemanticError: If the credential store cannot be located
                or loaded.  The error message includes the expected
                credential store path.
        """
        self._require_phase(LifecyclePhase.CONFIGURED, "setup_credentials")

        presence_dir = AppPersona.AM_PRESENCE_DIR or "(unknown)"

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
                the package is available.

            :raises LifecycleError: If the current phase has not reached
                ``CREDENTIALS_LOADED``.
            :raises SemanticError: If the data profile source cannot be
                located or loaded.  The error message includes the expected
                data profile source path.
        """
        self._require_phase(LifecyclePhase.CREDENTIALS_LOADED, "setup_data_profiles")

        presence_dir = AppPersona.AM_PRESENCE_DIR or "(unknown)"

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

            :raises LifecycleError: If the current phase has not reached
                ``DATA_PROFILES_LOADED``.
        """
        self._require_phase(LifecyclePhase.DATA_PROFILES_LOADED, "setup_database")

        self.prepare_database()
        self.connect_database()
        self.startup_database()
        self.ensure_database_ready()

        self._advance_phase(LifecyclePhase.DATABASE_READY)

        return

    def setup_authentication(self) -> None:
        """
            Initializes the authentication subsystem.

            Requires the ``DATABASE_READY`` phase.  Creates an
            :class:`AuthenticationSystem` instance, stores it in
            ``_auth_system``, and advances the lifecycle phase to
            ``AUTHENTICATION_READY``.

            :raises LifecycleError: If the current phase has not reached
                ``DATABASE_READY``.
        """
        self._require_phase(LifecyclePhase.DATABASE_READY, "setup_authentication")

        self._auth_system = AuthenticationSystem()

        self._advance_phase(LifecyclePhase.AUTHENTICATION_READY)

        return

    def setup_infrastructure(self) -> None:
        """
            Wires the web infrastructure: Router, Dispatcher, and
            ASGIApplication.

            Requires the ``AUTHENTICATION_READY`` phase.  This method:

            1. Creates a :class:`Router` instance.
            2. Loads all :class:`EndpointDescriptor` instances from the
               global :class:`EndpointRegistry` into the Router.
            3. Flushes any pending routes queued via ``attach_route`` into
               the Router.
            4. Flushes any pending blueprints queued via
               ``attach_blueprint_to_route`` into the Router.
            5. Creates a :class:`Dispatcher` configured with the Router.
            6. Creates an :class:`ASGIApplication` via
               ``create_asgi_application()``.
            7. Wires the ASGIApplication HTTP handler to
               ``dispatcher.dispatch_async``.
            8. Advances the lifecycle phase to ``INFRASTRUCTURE_READY``.

            :raises LifecycleError: If the current phase has not reached
                ``AUTHENTICATION_READY``.
        """
        self._require_phase(LifecyclePhase.AUTHENTICATION_READY, "setup_infrastructure")

        # 1. Create the Router
        router = Router()
        self._router = router

        # 2. Load descriptors from the global EndpointRegistry
        router.load_from_registry(registry=EndpointRegistry)

        # 3. Flush pending routes
        for descriptor in self._pending_routes:
            router.add_endpoint(descriptor)
        self._pending_routes.clear()

        # 4. Flush pending blueprints
        for blueprint_cls in self._pending_blueprints:
            blueprint_cls.register(router=self._router)
        self._pending_blueprints.clear()

        # 5. Create the Dispatcher
        dispatcher = Dispatcher(router=self._router)
        self._dispatcher = dispatcher

        # 6. Create the ASGIApplication
        asgi_app = create_asgi_application()
        self._asgi_app = asgi_app

        # 7. Wire the HTTP handler
        self._asgi_app.http_handler.set_handler(self._dispatcher.dispatch_async)

        # 8. Advance phase
        self._advance_phase(LifecyclePhase.INFRASTRUCTURE_READY)

        return

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

            :returns: The fully initialized WebApplication instance (``self``).
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

            1. ASGIApplication
            2. Dispatcher
            3. Router
            4. AuthenticationMiddleware
            5. AuthenticationSystem
            6. Database hooks (no-op — hooks are stateless by default)
            7. DataProfile_Manager
            8. Credential_Manager
            9. ManagedConfigRegistry (calls ``cleanup()`` before release)

            After all subsystems have been released the lifecycle phase
            advances to ``SHUTDOWN``.
        """
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

        :raises PersonaAlreadyEstablishedError: If persona was already established.
        :raises SemanticError: If THISAPPLICATION_SINGLETON is already set.
    """
    global WEBAPP_PERSONA_ESTABLISHED

    # Check if persona is already established
    if WEBAPP_PERSONA_ESTABLISHED:
        raise PersonaAlreadyEstablishedError(AppPersona.AM_NAME)

    # Mark as established early to prevent race conditions
    WEBAPP_PERSONA_ESTABLISHED = True

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

    # Populate AppPersona class attributes (same pattern as establish_app_persona)
    AppPersona.AM_NAME = name
    AppPersona.AM_LOGGER_NAME = logger_name
    AppPersona.AM_LOG_BASENAME = log_basename
    AppPersona.AM_PRESENCE_DIR = resolved_presence_dir
    AppPersona.AM_LOG_DIRECTORY = resolved_log_directory
    AppPersona.AM_SETTINGS_FILENAME = resolved_settings_file
    AppPersona.AM_EXTENSIONS = extensions
    AppPersona.AM_SERVICE_NAME = service_name

    # Check that THISAPPLICATION_SINGLETON is not already set
    if thisapp_wellknown.THISAPPLICATION_SINGLETON is not None:
        errmsg = "The singleton 'wellknown.THISAPPLICATION_SINGLETON' must not be set " \
                 "when calling 'establish_webapp_persona'"
        raise SemanticError(errmsg)

    # Determine which class to instantiate
    if application_cls is None:
        application_cls = WebApplication

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

    # Wire into both wellknown modules under the lock
    SINGLETON_LOCK.acquire()
    try:
        webworks_wellknown.THISWEBAPPLICATION_SINGLETON = this_app
        thisapp_wellknown.THISAPPLICATION_SINGLETON = this_app
    finally:
        SINGLETON_LOCK.release()

    # Override variable values for PersonaVariablesDesc
    this_app.override_variable_value(PersonaVariablesDesc.AM_NAME, this_app.name)
    this_app.override_variable_value(PersonaVariablesDesc.AM_LOGGER_NAME, logger_name)
    this_app.override_variable_value(PersonaVariablesDesc.AM_LOG_BASENAME, log_basename)
    this_app.override_variable_value(PersonaVariablesDesc.AM_LOG_DIRECTORY, resolved_log_directory)
    this_app.override_variable_value(PersonaVariablesDesc.AM_PRESENCE_DIR, resolved_presence_dir)
    this_app.override_variable_value(PersonaVariablesDesc.AM_SERVICE_NAME, service_name)
    this_app.override_variable_value(PersonaVariablesDesc.AM_EXTENSIONS, extensions)

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
