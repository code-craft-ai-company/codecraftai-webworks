"""
.. module:: test_webapplication_routing
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Unit tests for the WebApplication endpoint registration APIs:
        ``attach_route`` and ``attach_blueprint_to_route``.

.. moduleauthor:: Code Craft AI LLC
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


import ccai.webworks.webapplication as webapp_module

from ccai.testbase.mocking import Mock, create_module_patch

from ccai.webworks.webapplication import (
    establish_webapp_persona,
    reset_webapp_persona,
)
from ccai.webworks.persona.lifecycle import (
    EndpointConflictError,
    BlueprintAlreadyRegisteredError,
)
from ccai.webworks.routing.request import Request


# =============================================================================
# Helpers
# =============================================================================

def _create_app():
    """
        Creates a fresh WebApplication via ``establish_webapp_persona``
        after resetting any prior singleton state.

        :returns: A freshly created WebApplication instance.
    """
    reset_webapp_persona()

    app = establish_webapp_persona(
        name="testapp",
        logger_name="testapp",
        log_basename="testapp",
    )

    return app


def _startup_app(app):
    """
        Runs the full startup sequence on the given WebApplication
        with ManagedConfigRegistry mocked to avoid filesystem access.

        :param app: The WebApplication instance to start up.

        :returns: The patch object so the caller can deactivate it.
    """
    mock_registry_instance = Mock()
    mock_registry_instance.configure(recursive=True)

    patch = create_module_patch(webapp_module, "ManagedConfigRegistry")
    mock_cls = patch.activate()
    mock_cls.configure(return_value=mock_registry_instance)

    app.startup()

    return patch


# =============================================================================
# Unit Tests for attach_route
# =============================================================================

def test_attach_route_makes_handler_routable_after_startup():
    """
        Test that ``attach_route`` with a specific path and method makes
        the handler routable after ``startup()`` completes.  A request
        matching the registered path and method should resolve to the
        decorated handler.

        _Requirements: 2.1_
    """
    app = _create_app()
    patch = None

    try:
        @app.attach_route("/api/status", methods=["GET"])
        def get_status(request):
            """Return application status."""
            return {"status": "ok"}

        patch = _startup_app(app)

        request = Request(method="GET", path="/api/status")
        match = app.router.match(request)

        if match is None:
            errmsg = (
                "Expected router to match GET /api/status but got None"
            )
            raise AssertionError(errmsg)

        if match.handler is not get_status:
            errmsg = (
                "Expected matched handler to be the get_status function, "
                f"got {match.handler}"
            )
            raise AssertionError(errmsg)

    finally:
        if patch is not None:
            patch.deactivate()
        reset_webapp_persona()

    return


def test_attach_route_conflict_raises_endpoint_conflict_error():
    """
        Test that registering two handlers at the same path and method
        after infrastructure is ready raises ``EndpointConflictError``
        with a descriptive message.

        _Requirements: 2.2_
    """
    app = _create_app()
    patch = None

    try:
        patch = _startup_app(app)

        @app.attach_route("/api/conflict", methods=["GET"])
        def handler_one(request):
            """First handler."""
            return {"handler": "one"}

        caught_error = None

        try:
            @app.attach_route("/api/conflict", methods=["GET"])
            def handler_two(request):
                """Second handler."""
                return {"handler": "two"}
        except EndpointConflictError as err:
            caught_error = err

        if caught_error is None:
            errmsg = (
                "Expected EndpointConflictError when registering a "
                "duplicate route at GET /api/conflict"
            )
            raise AssertionError(errmsg)

        error_message = str(caught_error)

        if "/api/conflict" not in error_message:
            errmsg = (
                "Expected EndpointConflictError message to include the "
                f"conflicting path '/api/conflict', got: {error_message}"
            )
            raise AssertionError(errmsg)

        if "GET" not in error_message:
            errmsg = (
                "Expected EndpointConflictError message to include the "
                f"conflicting method 'GET', got: {error_message}"
            )
            raise AssertionError(errmsg)

    finally:
        if patch is not None:
            patch.deactivate()
        reset_webapp_persona()

    return


def test_attach_route_preserves_function_name_and_doc():
    """
        Test that ``attach_route`` preserves the original function's
        ``__name__`` and ``__doc__`` on the decorated handler.

        _Requirements: 2.3_
    """
    app = _create_app()

    try:
        @app.attach_route("/api/preserved", methods=["POST"])
        def my_special_handler(request):
            """This is the special handler docstring."""
            return {"preserved": True}

        if my_special_handler.__name__ != "my_special_handler":
            errmsg = (
                "Expected decorated function __name__ to be "
                f"'my_special_handler', got '{my_special_handler.__name__}'"
            )
            raise AssertionError(errmsg)

        expected_doc = "This is the special handler docstring."
        if my_special_handler.__doc__ != expected_doc:
            errmsg = (
                "Expected decorated function __doc__ to be "
                f"'{expected_doc}', got '{my_special_handler.__doc__}'"
            )
            raise AssertionError(errmsg)

    finally:
        reset_webapp_persona()

    return


def test_attach_route_before_startup_queues_and_flushes():
    """
        Test that ``attach_route`` called before ``startup()`` queues
        the route in ``_pending_routes`` and flushes it into the Router
        during ``startup()``.

        _Requirements: 2.1_
    """
    app = _create_app()
    patch = None

    try:
        @app.attach_route("/api/queued", methods=["GET"])
        def queued_handler(request):
            """A handler registered before startup."""
            return {"queued": True}

        # Before startup, the route should be in _pending_routes
        if len(app._pending_routes) == 0:
            errmsg = (
                "Expected _pending_routes to contain the queued route "
                "before startup"
            )
            raise AssertionError(errmsg)

        patch = _startup_app(app)

        # After startup, _pending_routes should be empty
        if len(app._pending_routes) != 0:
            errmsg = (
                "Expected _pending_routes to be empty after startup, "
                f"got {len(app._pending_routes)} pending routes"
            )
            raise AssertionError(errmsg)

        # The route should now be matchable in the Router
        request = Request(method="GET", path="/api/queued")
        match = app.router.match(request)

        if match is None:
            errmsg = (
                "Expected router to match GET /api/queued after startup "
                "flushed pending routes"
            )
            raise AssertionError(errmsg)

        if match.handler is not queued_handler:
            errmsg = (
                "Expected matched handler to be the queued_handler function"
            )
            raise AssertionError(errmsg)

    finally:
        if patch is not None:
            patch.deactivate()
        reset_webapp_persona()

    return


# =============================================================================
# Unit Tests for attach_blueprint_to_route
# =============================================================================

def test_attach_blueprint_loads_endpoints_after_startup():
    """
        Test that ``attach_blueprint_to_route`` called after ``startup()``
        loads all blueprint endpoints into the Router by calling
        ``blueprint_cls.register(router=...)``.

        _Requirements: 3.1, 3.3_
    """
    app = _create_app()
    patch = None

    try:
        patch = _startup_app(app)

        register_called_with = []

        class FakeBlueprint:
            """A fake blueprint class for testing registration."""

            @classmethod
            def register(cls, router=None):
                register_called_with.append(router)

        app.attach_blueprint_to_route(FakeBlueprint)

        # Verify register was called with the app's router
        if len(register_called_with) != 1:
            errmsg = (
                "Expected blueprint register to be called once, "
                f"got {len(register_called_with)} calls"
            )
            raise AssertionError(errmsg)

        if register_called_with[0] is not app._router:
            errmsg = (
                "Expected blueprint register to be called with the "
                "app's router instance"
            )
            raise AssertionError(errmsg)

    finally:
        if patch is not None:
            patch.deactivate()
        reset_webapp_persona()

    return


def test_duplicate_blueprint_registration_raises_error():
    """
        Test that calling ``attach_blueprint_to_route`` twice with the
        same blueprint class raises ``BlueprintAlreadyRegisteredError``
        with a descriptive message including the class name.

        _Requirements: 3.2_
    """
    app = _create_app()
    patch = None

    try:
        patch = _startup_app(app)

        class FakeBlueprint:
            """A fake blueprint class for testing duplicate detection."""

            @classmethod
            def register(cls, router=None):
                pass

        # First registration should succeed
        app.attach_blueprint_to_route(FakeBlueprint)

        caught_error = None

        try:
            app.attach_blueprint_to_route(FakeBlueprint)
        except BlueprintAlreadyRegisteredError as err:
            caught_error = err

        if caught_error is None:
            errmsg = (
                "Expected BlueprintAlreadyRegisteredError when registering "
                "the same blueprint class twice"
            )
            raise AssertionError(errmsg)

        if caught_error.blueprint_cls is not FakeBlueprint:
            errmsg = (
                "Expected BlueprintAlreadyRegisteredError.blueprint_cls to "
                "reference the duplicate blueprint class"
            )
            raise AssertionError(errmsg)

        error_message = str(caught_error)

        if "FakeBlueprint" not in error_message:
            errmsg = (
                "Expected error message to include the blueprint class name "
                f"'FakeBlueprint', got: {error_message}"
            )
            raise AssertionError(errmsg)

    finally:
        if patch is not None:
            patch.deactivate()
        reset_webapp_persona()

    return


def test_attach_blueprint_before_startup_queues_and_flushes():
    """
        Test that ``attach_blueprint_to_route`` called before ``startup()``
        queues the blueprint class in ``_pending_blueprints`` and flushes
        it during ``startup()`` by calling ``blueprint_cls.register``.

        _Requirements: 3.1, 3.3_
    """
    app = _create_app()
    patch = None

    try:
        register_called_with = []

        class FakeBlueprint:
            """A fake blueprint class for testing deferred registration."""

            @classmethod
            def register(cls, router=None):
                register_called_with.append(router)

        app.attach_blueprint_to_route(FakeBlueprint)

        # Before startup, the blueprint should be in _pending_blueprints
        if len(app._pending_blueprints) == 0:
            errmsg = (
                "Expected _pending_blueprints to contain the queued "
                "blueprint before startup"
            )
            raise AssertionError(errmsg)

        # register should not have been called yet
        if len(register_called_with) != 0:
            errmsg = (
                "Expected blueprint register to not be called before "
                f"startup, got {len(register_called_with)} calls"
            )
            raise AssertionError(errmsg)

        patch = _startup_app(app)

        # After startup, _pending_blueprints should be empty
        if len(app._pending_blueprints) != 0:
            errmsg = (
                "Expected _pending_blueprints to be empty after startup, "
                f"got {len(app._pending_blueprints)} pending blueprints"
            )
            raise AssertionError(errmsg)

        # Verify register was called during startup with the router
        if len(register_called_with) != 1:
            errmsg = (
                "Expected blueprint register to be called once during "
                f"startup, got {len(register_called_with)} calls"
            )
            raise AssertionError(errmsg)

        if register_called_with[0] is not app._router:
            errmsg = (
                "Expected blueprint register to be called with the "
                "app's router instance during startup"
            )
            raise AssertionError(errmsg)

    finally:
        if patch is not None:
            patch.deactivate()
        reset_webapp_persona()

    return


# =============================================================================
# attach_route metadata
# =============================================================================

from ccai.webworks.endpoints.accesspolicy import AccessPolicy
from ccai.webworks.endpoints.doc import Doc
from ccai.webworks.security.decorators import require_roles


def test_attach_route_records_access_policy_on_descriptor():
    """
        The access_policy given to attach_route is stored on the route's
        descriptor, where the dispatcher enforces it.
    """
    app = _create_app()
    patch = None

    try:
        policy = AccessPolicy(roles=["admin"])

        @app.attach_route("/admin", access_policy=policy)
        def admin_home(request):
            return {"area": "admin"}

        patch = _startup_app(app)

        match = app.router.match(Request(method="GET", path="/admin"))

        if match.descriptor.constraints.access_policy != policy:
            errmsg = (
                "Expected the descriptor to carry the access policy, got "
                f"{match.descriptor.constraints.access_policy!r}"
            )
            raise AssertionError(errmsg)

        if match.descriptor.constraints.roles != ["admin"]:
            errmsg = f"Expected the roles to be listed, got {match.descriptor.constraints.roles!r}"
            raise AssertionError(errmsg)

    finally:
        if patch is not None:
            patch.deactivate()
        reset_webapp_persona()

    return


def test_attach_route_honors_security_decorator_on_handler():
    """
        A policy attached by a stacked @require_roles is recorded on the
        descriptor of a route registered with attach_route.
    """
    app = _create_app()
    patch = None

    try:
        @app.attach_route("/decorated")
        @require_roles("system-admin")
        def decorated(request):
            return {"ok": True}

        patch = _startup_app(app)

        match = app.router.match(Request(method="GET", path="/decorated"))
        policy = match.descriptor.constraints.access_policy

        if policy is None or policy.roles != ("system-admin",):
            errmsg = f"Expected the decorator's policy on the descriptor, got {policy!r}"
            raise AssertionError(errmsg)

    finally:
        if patch is not None:
            patch.deactivate()
        reset_webapp_persona()

    return


def test_attach_route_records_tags_and_doc():
    """
        Tags and documentation given to attach_route reach the descriptor.
    """
    app = _create_app()
    patch = None

    try:
        @app.attach_route("/tagged", tags=["reports"], doc=Doc(summary="Tagged route"))
        def tagged(request):
            return {"ok": True}

        patch = _startup_app(app)

        match = app.router.match(Request(method="GET", path="/tagged"))

        if match.descriptor.tags != ["reports"]:
            errmsg = f"Expected tags ['reports'], got {match.descriptor.tags!r}"
            raise AssertionError(errmsg)

        if match.descriptor.doc is None or match.descriptor.doc.summary != "Tagged route":
            errmsg = f"Expected the doc to be recorded, got {match.descriptor.doc!r}"
            raise AssertionError(errmsg)

    finally:
        if patch is not None:
            patch.deactivate()
        reset_webapp_persona()

    return


def test_attach_route_rejects_unknown_keyword_argument():
    """
        A keyword argument attach_route does not know is an error, so a
        mistyped access_policy can not silently leave a route unprotected.
    """
    app = _create_app()

    try:
        raised = False

        try:
            app.attach_route("/typo", acess_policy=AccessPolicy(roles=["admin"]))
        except TypeError:
            raised = True

        if not raised:
            errmsg = "Expected TypeError for an unknown keyword argument"
            raise AssertionError(errmsg)

    finally:
        reset_webapp_persona()

    return


# =============================================================================
# Routes added outside the registry are recorded in it
# =============================================================================

def _registered_paths(app):
    """
        The paths of the descriptors in the application's registry.

        :param app: The WebApplication.

        :returns: Sorted list of paths.
    """
    rtnval = sorted(descriptor.path for descriptor in app.registry.collect())
    return rtnval


def test_attach_route_records_the_route_in_the_registry():
    """
        Test that routes added with ``attach_route`` before and after
        ``startup()`` are in the application's registry, which the OpenAPI
        document and the security map are built from.
    """
    app = _create_app()
    patch = None

    try:
        @app.attach_route("/early")
        def early(request):
            return {}

        patch = _startup_app(app)

        @app.attach_route("/late")
        def late(request):
            return {}

        paths = _registered_paths(app)
        if paths != ["/early", "/late"]:
            errmsg = f"Expected both routes in the registry, got {paths}"
            raise AssertionError(errmsg)

    finally:
        if patch is not None:
            patch.deactivate()
        reset_webapp_persona()

    return


def test_attach_blueprint_records_the_blueprint_routes_in_the_registry():
    """
        Test that the routes of blueprints mounted before and after
        ``startup()`` are in the application's registry.
    """
    from ccai.webworks.endpoints.blueprint import Blueprint

    class EarlyRegistryBlueprint(Blueprint):
        base_path = "/early-bp"

    @EarlyRegistryBlueprint.attach_at(leaf="items", methods=["GET"])
    def early_items(request):
        return {}

    class LateRegistryBlueprint(Blueprint):
        base_path = "/late-bp"

    @LateRegistryBlueprint.attach_at(leaf="items", methods=["GET"])
    def late_items(request):
        return {}

    app = _create_app()
    patch = None

    try:
        app.attach_blueprint_to_route(EarlyRegistryBlueprint)
        patch = _startup_app(app)
        app.attach_blueprint_to_route(LateRegistryBlueprint)

        paths = _registered_paths(app)
        if paths != ["/early-bp/items", "/late-bp/items"]:
            errmsg = f"Expected both blueprints' routes in the registry, got {paths}"
            raise AssertionError(errmsg)

        match = app.router.match(Request(method="GET", path="/late-bp/items"))
        if match is None:
            raise AssertionError("Expected the late blueprint's route to be routable")

    finally:
        if patch is not None:
            patch.deactivate()
        reset_webapp_persona()

    return


def test_attach_blueprint_accepts_a_configured_instance():
    """
        Test that a configured blueprint instance, whose ``register`` serves
        the instance itself, can be mounted and is routable.
    """
    from ccai.webworks.endpoints.descriptor import EndpointDescriptor

    class ConfiguredBlueprint:
        def __init__(self, path):
            self._path = path
            return

        def handle(self, request):
            return {"path": self._path}

        def register(self, router=None):
            descriptor = EndpointDescriptor(
                handler=self.handle, module=__name__, path=self._path, methods=["GET"]
            )
            if router is not None:
                router.add_endpoint(descriptor)
            return [descriptor]

    app = _create_app()
    patch = None

    try:
        patch = _startup_app(app)
        app.attach_blueprint_to_route(ConfiguredBlueprint("/configured"))

        match = app.router.match(Request(method="GET", path="/configured"))
        if match is None:
            raise AssertionError("Expected the configured instance's route to be routable")

        if _registered_paths(app) != ["/configured"]:
            errmsg = f"Expected the instance's route in the registry, got {_registered_paths(app)}"
            raise AssertionError(errmsg)

    finally:
        if patch is not None:
            patch.deactivate()
        reset_webapp_persona()

    return
