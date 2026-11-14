"""
    Tests for the extension system wired into a WebApplication.

    This module contains integration tests: extensions added in code and
    loaded from configuration, the application lifecycle hooks fired at the
    application's phases, the request lifecycle hooks fired by the
    dispatcher under ASGI, extension components on the application's
    registries, and shutdown.
"""

import asyncio

from typing import Any, Callable, Dict, List, Optional

import ccai.webworks.webapplication as webapp_module

from ccai.errors.exceptions import ConfigurationError
from ccai.testbase.mocking import create_instance_patch, create_module_patch

from ccai.webworks.devexp.testing.testclient import TestClient
from ccai.webworks.endpoints.descriptor import EndpointDescriptor
from ccai.webworks.extensibility.extension import Extension
from ccai.webworks.extensibility.requestlifecyclehooks import REQUEST_LIFECYCLE_HOOKS
from ccai.webworks.persona.lifecycle import LifecycleError
from ccai.webworks.routing.request import Request
from ccai.webworks.routing.response import JSONResponse
from ccai.webworks.webapplication import establish_webapp_persona, reset_webapp_persona


_THIS_MODULE = "ccai.tests.singlehost.webworks.extensibility.test_webapplication_extensions"

_APP_HOOKS = ("on_config_loaded", "on_app_init", "on_routes_registered", "on_app_ready", "on_app_shutdown")


# =============================================================================
# Configuration and application helpers
# =============================================================================

class _FlatConfig:
    """
        Stands in for the ManagedConfigRegistry: dot-notation keys offered
        through get() and items(), and the lifecycle calls the application
        makes on its configuration.
    """

    def __init__(self, values: Optional[Dict[str, Any]] = None):
        self._values: Dict[str, Any] = dict(values) if values is not None else {}
        return

    def setup_from_persona(self) -> None:
        return

    def cleanup(self) -> None:
        return

    def get(self, key: str, default: Any = None) -> Any:
        rtnval = self._values.get(key, default)
        return rtnval

    def items(self) -> List[Any]:
        rtnval = list(self._values.items())
        return rtnval


class _Events:
    """The events the test extensions record, in order."""
    log: List[Any] = []


def _run_app(
    config_values: Optional[Dict[str, Any]],
    prepare: Callable[[Any], None],
    check: Callable[[Any], None]
) -> None:
    """
        Establish a web application, prepare it, start it with the given
        configuration values and run ``check`` with it; always shut it down
        and reset the persona.

        :param config_values: The dot-notation configuration, or None.
        :param prepare: Called with the application before startup.
        :param check: Called with the started application.
    """
    reset_webapp_persona()
    _Events.log = []

    patch = None
    app = None

    try:
        app = establish_webapp_persona(name="extapp", logger_name="extapp", log_basename="extapp")

        prepare(app)

        patch = create_module_patch(webapp_module, "ManagedConfigRegistry")
        mock_cls = patch.activate()
        mock_cls.configure(return_value=_FlatConfig(config_values))

        app.startup()

        check(app)

    finally:
        if app is not None:
            app.shutdown()
        if patch is not None:
            patch.deactivate()
        reset_webapp_persona()

    return


def _expect(condition: bool, message: str) -> None:
    """
        Raise an AssertionError with ``message`` unless ``condition`` holds.

        :param condition: The checked condition.
        :param message: The failure message.
    """
    if condition is not True:
        raise AssertionError(message)
    return


# =============================================================================
# Extensions used by the tests
# =============================================================================

class _HookRecorder(Extension):
    """Records its lifecycle and every application and request hook."""

    name = "recorder"

    def initialize(self, context: Any) -> None:
        super().initialize(context)
        _Events.log.append("initialize")

        for hook_name in _APP_HOOKS:
            context.register_hook(hook_name, self._record_app_hook(hook_name))

        context.register_hook("before_first_request", self.before_first_request)
        context.register_hook("before_request", self.before_request)
        context.register_hook("on_request_error", self.on_request_error)
        context.register_hook("after_request", self.after_request)
        context.register_hook("teardown_request", self.teardown_request)
        return

    def activate(self) -> None:
        super().activate()
        _Events.log.append("activate")
        return

    def shutdown(self) -> None:
        _Events.log.append("shutdown")
        return

    def _record_app_hook(self, hook_name: str) -> Callable[[Any], None]:
        def record(app_context: Any) -> None:
            _Events.log.append(hook_name)
            return
        return record

    def before_first_request(self, request: Any) -> None:
        _Events.log.append("before_first_request")
        return

    def before_request(self, request: Any) -> Any:
        _Events.log.append("before_request")
        rtnval = None
        if request.path == "/blocked":
            rtnval = JSONResponse({"blocked": True}, status_code=403)
        return rtnval

    def on_request_error(self, request: Any, error: Exception) -> None:
        _Events.log.append(("on_request_error", type(error).__name__))
        return

    def after_request(self, request: Any, response: Any) -> Any:
        _Events.log.append("after_request")
        response.set_header("X-Recorder", "after")
        return None

    def teardown_request(self, request: Any, response: Any, error: Optional[Exception]) -> None:
        error_name = type(error).__name__ if error is not None else None
        _Events.log.append(("teardown_request", response.status_code, error_name))
        return


class _ConfiguredExtension(Extension):
    """An extension the configuration names by import string."""

    name = "configured"

    def initialize(self, context: Any) -> None:
        super().initialize(context)
        _Events.log.append(("configured.initialize", dict(context.config)))
        return


class _MiddlewareComponent:
    """A middleware component an extension registers."""

    name = "audit-middleware"

    def process_request(self, request: Any) -> Any:
        _Events.log.append("middleware.process_request")
        return None

    def process_response(self, request: Any, response: Any) -> Any:
        _Events.log.append("middleware.process_response")
        response.set_header("X-Audited", "yes")
        return None


class _MiddlewareExtension(Extension):
    """Registers a middleware component through the register_middleware hook."""

    name = "middleware-ext"

    def initialize(self, context: Any) -> None:
        super().initialize(context)
        context.component_hooks.fire_register_middleware(_MiddlewareComponent())
        return


def _shutdown_extension(name: str, dependencies: List[str], fail: bool) -> type:
    """
        Build an extension class that records its shutdown and may fail it.

        :param name: The extension name.
        :param dependencies: The names it depends on.
        :param fail: Whether its shutdown raises.

        :returns: The extension class.
    """
    def shutdown(self) -> None:
        _Events.log.append(("shutdown", self.name))
        if fail is True:
            raise RuntimeError("shutdown of {} failed".format(self.name))
        return

    rtnval = type(
        "_Shutdown_" + name,
        (Extension,),
        {"name": name, "dependencies": list(dependencies), "shutdown": shutdown}
    )
    return rtnval


# =============================================================================
# Extensions from code and from configuration
# =============================================================================

def test_extension_added_in_code_and_extension_from_config_both_initialise():
    """
        An extension added with add_extension and one named in the
        extensions section both initialise; the configured one gets its own
        settings from extensions.<name>.
    """
    config_values = {
        "extensions.load": [_THIS_MODULE + ":_ConfiguredExtension"],
        "extensions.allowed_packages": [_THIS_MODULE],
        "extensions.configured.level": "full",
    }

    def prepare(app):
        app.add_extension(_HookRecorder)
        return

    def check(app):
        registry = app.extension_registry
        names = sorted(extension.name for extension in registry.list())
        _expect(names == ["configured", "recorder"], "Expected both extensions, got {}".format(names))
        _expect(("configured.initialize", {"level": "full"}) in _Events.log,
                "Expected the configured extension to initialise with its settings, got {}".format(_Events.log))
        _expect("initialize" in _Events.log, "Expected the code-added extension to initialise")
        for name in names:
            _expect(registry.get_state(name).value == "active", "Expected {} to be active".format(name))
        return

    _run_app(config_values, prepare, check)

    return


def test_disallowed_configured_extension_fails_startup():
    """
        An extension outside extensions.allowed_packages fails the startup
        with ConfigurationError before its module is imported.
    """
    config_values = {
        "extensions.load": ["nosuchpackage.extensions.never_imported:Extension"],
        "extensions.allowed_packages": ["mycompany"],
    }

    caught = None

    def prepare(app):
        return

    def check(app):
        return

    try:
        _run_app(config_values, prepare, check)
    except ConfigurationError as err:
        caught = err

    _expect(caught is not None, "Expected ConfigurationError for a disallowed extension")
    _expect("allowed extension packages" in str(caught),
            "Expected the allow-list refusal, got {}".format(caught))

    return


def test_no_configured_extensions_means_no_extensions():
    """
        Without an extensions section nothing is loaded, and no hook has a callback.
    """
    def prepare(app):
        return

    def check(app):
        _expect(app.extension_registry.list() == [], "Expected no extensions")
        _expect(app.hook_manager.has_any_callbacks(REQUEST_LIFECYCLE_HOOKS + list(_APP_HOOKS)) is False,
                "Expected no hook callbacks")
        return

    _run_app(None, prepare, check)

    return


def test_add_extension_after_startup_raises_lifecycle_error():
    """
        Extensions are started in setup_infrastructure; adding one later is refused.
    """
    def prepare(app):
        return

    def check(app):
        caught = None
        try:
            app.add_extension(_HookRecorder)
        except LifecycleError as err:
            caught = err
        _expect(caught is not None, "Expected LifecycleError")
        return

    _run_app(None, prepare, check)

    return


# =============================================================================
# Hook order under ASGI
# =============================================================================

def test_app_and_request_hooks_fire_in_order_under_asgi():
    """
        Every application and request hook fires in order when the
        application is served through asgi_app with a lifespan: on_app_ready
        after the lifespan startup handlers, on_app_shutdown and the
        extension shutdown before the lifespan shutdown handlers.
    """
    def prepare(app):
        app.add_extension(_HookRecorder)

        @app.attach_route("/hello", methods=["GET"])
        def hello(request):
            _Events.log.append("handler")
            return {"hello": "world"}

        return

    def check(app):
        lifespan = app.asgi_app.lifespan_handler
        lifespan.on_startup(lambda: _Events.log.append("lifespan.startup"))
        lifespan.on_shutdown(lambda: _Events.log.append("lifespan.shutdown"))

        with TestClient(app.asgi_app) as client:
            first = client.get("/hello")
            second = client.get("/hello")

        _expect(first.status_code == 200 and first.json == {"hello": "world"}, "Unexpected response {}".format(first.text))
        _expect(second.headers.get("X-Recorder") == "after", "Expected after_request to tag the response")

        expected = [
            "initialize",
            "activate",
            "on_config_loaded",
            "on_app_init",
            "on_routes_registered",
            "lifespan.startup",
            "on_app_ready",
            "before_first_request",
            "before_request",
            "handler",
            "after_request",
            ("teardown_request", 200, None),
            "before_request",
            "handler",
            "after_request",
            ("teardown_request", 200, None),
            "on_app_shutdown",
            "shutdown",
            "lifespan.shutdown",
        ]
        _expect(_Events.log == expected, "Expected {}, got {}".format(expected, _Events.log))
        return

    _run_app(None, prepare, check)

    # app.shutdown() after the lifespan shutdown does not stop the extensions twice.
    _expect(_Events.log.count("on_app_shutdown") == 1 and _Events.log.count("shutdown") == 1,
            "Expected one on_app_shutdown and one shutdown, got {}".format(_Events.log))

    return


def test_on_app_ready_fires_before_the_first_request_without_a_lifespan():
    """
        Served without a lifespan startup, the application fires
        on_app_ready once, before its first request.
    """
    def prepare(app):
        app.add_extension(_HookRecorder)

        @app.attach_route("/hello", methods=["GET"])
        def hello(request):
            return {"hello": "world"}

        return

    def check(app):
        client = TestClient(app.asgi_app)
        try:
            client.get("/hello")
            client.get("/hello")
        finally:
            client.close()

        ready_index = _Events.log.index("on_app_ready")
        first_index = _Events.log.index("before_first_request")
        _expect(ready_index < first_index, "Expected on_app_ready before the first request, got {}".format(_Events.log))
        _expect(_Events.log.count("on_app_ready") == 1, "Expected on_app_ready once, got {}".format(_Events.log))
        return

    _run_app(None, prepare, check)

    _expect(_Events.log[-2:] == ["on_app_shutdown", "shutdown"],
            "Expected app.shutdown() to stop the extensions, got {}".format(_Events.log))

    return


def test_before_request_short_circuit_skips_the_handler():
    """
        A response returned by before_request is sent instead of running the
        handler; after_request and teardown_request still run.
    """
    def prepare(app):
        app.add_extension(_HookRecorder)

        @app.attach_route("/blocked", methods=["GET"])
        def blocked(request):
            _Events.log.append("handler")
            return {"reached": True}

        return

    def check(app):
        with TestClient(app.asgi_app) as client:
            response = client.get("/blocked")

        _expect(response.status_code == 403 and response.json == {"blocked": True},
                "Expected the short-circuit response, got {} {}".format(response.status_code, response.text))
        _expect("handler" not in _Events.log, "Expected the handler not to run, got {}".format(_Events.log))

        request_events = _Events.log[_Events.log.index("before_request"):_Events.log.index("on_app_shutdown")]
        _expect(request_events == ["before_request", "after_request", ("teardown_request", 403, None)],
                "Unexpected request events {}".format(request_events))
        return

    _run_app(None, prepare, check)

    return


def test_teardown_request_runs_after_an_error():
    """
        An unhandled handler exception is reported to on_request_error before
        the 500 response is made; after_request and teardown_request run, the
        teardown with the error.
    """
    def prepare(app):
        app.add_extension(_HookRecorder)

        @app.attach_route("/boom", methods=["GET"])
        def boom(request):
            raise RuntimeError("handler failed")

        return

    def check(app):
        with TestClient(app.asgi_app) as client:
            response = client.get("/boom")

        _expect(response.status_code == 500, "Expected 500, got {}".format(response.status_code))

        request_events = _Events.log[_Events.log.index("before_request"):_Events.log.index("on_app_shutdown")]
        expected = [
            "before_request",
            ("on_request_error", "RuntimeError"),
            "after_request",
            ("teardown_request", 500, "RuntimeError"),
        ]
        _expect(request_events == expected, "Expected {}, got {}".format(expected, request_events))
        return

    _run_app(None, prepare, check)

    return


def test_failing_before_request_hook_answers_500_and_is_reported():
    """
        A before_request callback that raises makes the request a 500, is
        counted against its extension, and the request is still torn down.
    """
    class _FailingBefore(Extension):
        name = "failing-before"

        def initialize(self, context: Any) -> None:
            super().initialize(context)
            context.register_hook("before_request", self.before_request)
            context.register_hook("teardown_request", self.teardown_request)
            return

        def before_request(self, request: Any) -> Any:
            raise ValueError("hook failed")

        def teardown_request(self, request: Any, response: Any, error: Any) -> None:
            _Events.log.append(("teardown", response.status_code, type(error).__name__))
            return

    def prepare(app):
        app.add_extension(_FailingBefore)

        @app.attach_route("/hello", methods=["GET"])
        def hello(request):
            _Events.log.append("handler")
            return {"hello": "world"}

        return

    def check(app):
        with TestClient(app.asgi_app) as client:
            response = client.get("/hello")

        _expect(response.status_code == 500, "Expected 500, got {}".format(response.status_code))
        _expect("handler" not in _Events.log, "Expected the handler not to run")
        _expect(("teardown", 500, "HookExecutionError") in _Events.log, "Unexpected events {}".format(_Events.log))
        _expect(app.extension_registry.get_error_count("failing-before") == 1,
                "Expected the hook failure to count against the extension")
        return

    _run_app(None, prepare, check)

    return


def test_sync_dispatch_fires_the_same_request_hooks():
    """
        The synchronous dispatch (the WSGI path) fires the request hooks in
        the same order as the asynchronous one.
    """
    def prepare(app):
        app.add_extension(_HookRecorder)

        @app.attach_route("/hello", methods=["GET"])
        def hello(request):
            _Events.log.append("handler")
            return {"hello": "world"}

        return

    def check(app):
        sync_response = app.dispatcher.dispatch(Request("GET", "/hello"))
        sync_events = list(_Events.log[_Events.log.index("before_first_request"):])

        del _Events.log[:]
        async_response = asyncio.run(app.dispatcher.dispatch_async(Request("GET", "/hello")))
        async_events = list(_Events.log)

        _expect(sync_response.status_code == 200 and async_response.status_code == 200, "Expected 200 twice")
        _expect(sync_events[1:] == async_events,
                "Expected the same request events, got {} and {}".format(sync_events, async_events))
        _expect(async_events == ["before_request", "handler", "after_request", ("teardown_request", 200, None)],
                "Unexpected request events {}".format(async_events))
        return

    _run_app(None, prepare, check)

    return


# =============================================================================
# Components, routes and shutdown
# =============================================================================

def test_extension_middleware_runs_on_requests():
    """
        Middleware an extension registers through register_middleware runs
        on the real request pipeline.
    """
    def prepare(app):
        app.add_extension(_MiddlewareExtension)

        @app.attach_route("/hello", methods=["GET"])
        def hello(request):
            _Events.log.append("handler")
            return {"hello": "world"}

        return

    def check(app):
        with TestClient(app.asgi_app) as client:
            response = client.get("/hello")

        _expect(response.headers.get("X-Audited") == "yes", "Expected the middleware to tag the response")
        _expect(_Events.log == ["middleware.process_request", "handler", "middleware.process_response"],
                "Unexpected events {}".format(_Events.log))

        names = app.middleware_registry.export_effective_pipeline("/hello")
        _expect(names == ["audit-middleware"], "Expected the middleware in the global pipeline, got {}".format(names))
        return

    _run_app(None, prepare, check)

    return


class _RouteExtension(Extension):
    """Registers a route through the endpoint registry and reads the URL node map."""

    name = "route-ext"

    def initialize(self, context: Any) -> None:
        super().initialize(context)

        def extension_status(request: Any) -> Any:
            return {"from": "extension"}

        descriptor = EndpointDescriptor(handler=extension_status, module=__name__, path="/ext/status", methods=["GET"])
        context.endpoint_registry.register(descriptor)
        context.register_hook("on_routes_registered", self.on_routes_registered)
        self._url_node_map = context.url_node_map
        return

    def on_routes_registered(self, app_context: Any) -> None:
        has_node = self._url_node_map.has_node("/ext/status")
        _Events.log.append(("url_node_map", has_node))
        return


def test_extension_routes_are_served_and_described():
    """
        A route an extension registers while it initialises is served, and
        the URL node map describes it by on_routes_registered.
    """
    def prepare(app):
        app.add_extension(_RouteExtension)
        return

    def check(app):
        with TestClient(app.asgi_app) as client:
            response = client.get("/ext/status")

        _expect(response.status_code == 200 and response.json == {"from": "extension"},
                "Expected the extension's route to be served, got {} {}".format(response.status_code, response.text))
        _expect(("url_node_map", True) in _Events.log, "Expected the URL node map to hold the route, got {}".format(_Events.log))
        return

    _run_app(None, prepare, check)

    return


class _AuthProvider:
    """An authentication provider an extension registers."""

    scheme = "extension-token"
    priority = 5

    def authenticate(self, request: Any) -> Any:
        return None


class _YamlLikeSerializer:
    """A serializer an extension registers."""

    content_type = "application/x-test"

    def serialize(self, data: Any, schema: Any = None) -> bytes:
        return b"serialized"

    def deserialize(self, data: bytes, schema: Any = None) -> Any:
        return {}


class _ComponentExtension(Extension):
    """Registers an authentication provider and a serializer."""

    name = "component-ext"

    def initialize(self, context: Any) -> None:
        super().initialize(context)
        context.component_hooks.fire_register_auth_provider(_AuthProvider())
        context.component_hooks.fire_register_serializer(_YamlLikeSerializer())
        return


def test_auth_provider_and_serializer_components_reach_the_application_registries():
    """
        An authentication provider is registered with the authentication
        system and a serializer with the REST processing's registry.
    """
    def prepare(app):
        app.add_extension(_ComponentExtension)
        return

    def check(app):
        _expect("extension-token" in app.auth_system.get_registered_schemes(),
                "Expected the provider's scheme, got {}".format(app.auth_system.get_registered_schemes()))

        serializer_registry = app.rest_middleware.serializer_registry
        _expect(serializer_registry.get_serializer("application/x-test") is not None, "Expected the serializer")
        _expect(serializer_registry.get_deserializer("application/x-test") is not None, "Expected the deserializer")
        return

    _run_app(None, prepare, check)

    return


def test_shutdown_reaches_every_extension_when_one_raises():
    """
        app.shutdown() fires on_app_shutdown and shuts every extension down in
        reverse dependency order, past one whose shutdown raises.
    """
    def prepare(app):
        app.add_extension(_shutdown_extension("base", [], fail=False))
        app.add_extension(_shutdown_extension("middle", ["base"], fail=True))
        app.add_extension(_shutdown_extension("top", ["middle"], fail=False))
        return

    def check(app):
        return

    _run_app(None, prepare, check)

    expected = [("shutdown", "top"), ("shutdown", "middle"), ("shutdown", "base")]
    _expect(_Events.log == expected, "Expected {}, got {}".format(expected, _Events.log))

    return


# =============================================================================
# No extensions: no hook overhead, no behaviour change
# =============================================================================

def test_application_without_extensions_does_not_run_hooks_per_request():
    """
        Without extensions the dispatcher takes its plain path after the
        first request: the hook manager is not consulted for a request.
    """
    def prepare(app):
        @app.attach_route("/hello", methods=["GET"])
        def hello(request):
            return {"hello": "world"}

        return

    def check(app):
        with TestClient(app.asgi_app) as client:
            first = client.get("/hello")

            execute_patch = create_instance_patch(app.hook_manager, "execute")
            chain_patch = create_instance_patch(app.hook_manager, "execute_chain")
            execute_mock = execute_patch.activate()
            chain_mock = chain_patch.activate()
            try:
                second = client.get("/hello")
            finally:
                execute_patch.deactivate()
                chain_patch.deactivate()

        _expect(first.status_code == 200 and second.status_code == 200, "Expected 200 twice")
        _expect(first.json == {"hello": "world"} and second.json == {"hello": "world"}, "Unexpected bodies")
        _expect(execute_mock.mock_context().call_count == 0 and chain_mock.mock_context().call_count == 0,
                "Expected no hook execution for a request without extensions")
        return

    _run_app(None, prepare, check)

    return
