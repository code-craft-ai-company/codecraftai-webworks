"""
    Tests for the ExtensionContext class.

    This module contains unit tests and property-based tests for the
    ExtensionContext class including service access, service registration
    round-trip, and context immutability after freezing.
"""

import logging
import random
import string

from typing import Any, Dict, List, Optional

from automojo.webworks.extensibility.context import ExtensionContext
from automojo.webworks.extensibility.exceptions import ExtensionContextFrozenError


# =============================================================================
# Test Helpers
# =============================================================================

class _FakeEndpointRegistry:
    """
        A fake endpoint registry for testing purposes.
    """

    def __init__(self, name: str = "fake-endpoint-registry"):
        self.name = name
        return


class _FakeUrlNodeMap:
    """
        A fake URL node map for testing purposes.
    """

    def __init__(self, name: str = "fake-url-node-map"):
        self.name = name
        return


class _FakeMiddleware:
    """
        A fake middleware for testing purposes.
    """

    def __init__(self, name: str = "fake-middleware"):
        self.name = name
        return


class _FakeExtensionRegistry:
    """
        A fake extension registry for testing dependency lookups.
    """

    def __init__(self, extensions: Optional[Dict[str, Any]] = None):
        self._extensions = extensions if extensions is not None else {}
        return

    def get(self, name: str) -> Optional[Any]:
        """
            Get an extension by name.

            :param name: The extension name.

            :returns: The extension or None if not found.
        """
        rtnval = self._extensions.get(name, None)
        return rtnval


class _FakeAppContext:
    """
        A fake application context for testing purposes.

        Provides the duck-typed interface that ExtensionContext
        expects from the application context.
    """

    def __init__(
        self,
        config: Optional[Any] = None,
        endpoint_registry: Optional[Any] = None,
        url_node_map: Optional[Any] = None,
        middleware: Optional[List[Any]] = None,
        extension_registry: Optional[Any] = None
    ):
        self.config = config if config is not None else {"app_key": "app_value"}
        self.endpoint_registry = endpoint_registry if endpoint_registry is not None else _FakeEndpointRegistry()
        self.url_node_map = url_node_map if url_node_map is not None else _FakeUrlNodeMap()
        self.middleware = middleware if middleware is not None else []
        self.extension_registry = extension_registry if extension_registry is not None else _FakeExtensionRegistry()
        self._loggers: Dict[str, logging.Logger] = {}
        return

    def get_logger(self, name: str) -> logging.Logger:
        """
            Get a logger by name.

            :param name: The logger name.

            :returns: A Logger instance.
        """
        if name not in self._loggers:
            self._loggers[name] = logging.getLogger(name)

        rtnval = self._loggers[name]
        return rtnval


# =============================================================================
# Random Data Generators for Property Tests
# =============================================================================

def _generate_random_string(min_length: int = 1, max_length: int = 20) -> str:
    """
        Generate a random string of alphanumeric characters.

        :param min_length: Minimum length of the generated string.
        :param max_length: Maximum length of the generated string.

        :returns: A random alphanumeric string.
    """
    length = random.randint(min_length, max_length)
    result = "".join(random.choices(string.ascii_lowercase + string.digits, k=length))
    return result


def _generate_random_config() -> Dict[str, Any]:
    """
        Generate a random configuration dictionary.

        :returns: A dictionary with random string keys and values.
    """
    count = random.randint(0, 5)
    config = {}
    for _ in range(count):
        key = _generate_random_string(3, 10)
        value = _generate_random_string(1, 15)
        config[key] = value

    return config


def _generate_random_service() -> object:
    """
        Generate a random service object.

        :returns: An object with a random name attribute.
    """

    class _Service:
        def __init__(self, name: str):
            self.name = name
            return

    svc = _Service(name=_generate_random_string(3, 15))
    return svc


# =============================================================================
# Unit Tests for ExtensionContext __init__
# =============================================================================

def test_context_init_sets_extension_name():
    """
        Test that __init__ stores the extension name.
    """
    app_ctx = _FakeAppContext()
    ctx = ExtensionContext(extension_name="my-ext", app_context=app_ctx, config={"key": "val"})

    if ctx._extension_name != "my-ext":
        errmsg = "Expected extension_name 'my-ext', got '{}'".format(ctx._extension_name)
        raise AssertionError(errmsg)

    return


def test_context_init_sets_config():
    """
        Test that __init__ stores the provided config.
    """
    app_ctx = _FakeAppContext()
    config = {"setting_a": "value_a"}
    ctx = ExtensionContext(extension_name="my-ext", app_context=app_ctx, config=config)

    if ctx._config != config:
        errmsg = "Expected config {}, got {}".format(config, ctx._config)
        raise AssertionError(errmsg)

    return


def test_context_init_defaults_config_to_empty_dict():
    """
        Test that __init__ defaults config to an empty dict when None.
    """
    app_ctx = _FakeAppContext()
    ctx = ExtensionContext(extension_name="my-ext", app_context=app_ctx)

    if ctx._config != {}:
        errmsg = "Expected config to default to empty dict, got {}".format(ctx._config)
        raise AssertionError(errmsg)

    return


def test_context_init_services_empty():
    """
        Test that __init__ initializes _services as an empty dict.
    """
    app_ctx = _FakeAppContext()
    ctx = ExtensionContext(extension_name="my-ext", app_context=app_ctx, config={})

    if len(ctx._services) != 0:
        errmsg = "Expected _services to be empty, got {}".format(ctx._services)
        raise AssertionError(errmsg)

    return


def test_context_init_not_frozen():
    """
        Test that __init__ initializes _frozen as False.
    """
    app_ctx = _FakeAppContext()
    ctx = ExtensionContext(extension_name="my-ext", app_context=app_ctx, config={})

    if ctx._frozen is not False:
        errmsg = "Expected _frozen to be False, got {}".format(ctx._frozen)
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for config property
# =============================================================================

def test_context_config_returns_extension_config():
    """
        Test that the config property returns the extension-specific configuration.
    """
    app_ctx = _FakeAppContext()
    config = {"debug": True, "timeout": 30}
    ctx = ExtensionContext(extension_name="my-ext", app_context=app_ctx, config=config)

    result = ctx.config
    if result is not config:
        errmsg = "Expected config to be the same instance provided during init"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for logger property
# =============================================================================

def test_context_logger_returns_logger_with_extension_namespace():
    """
        Test that the logger property returns a logger namespaced to the extension.
    """
    app_ctx = _FakeAppContext()
    ctx = ExtensionContext(extension_name="my-ext", app_context=app_ctx, config={})

    logger = ctx.logger

    if logger is None:
        errmsg = "Expected logger to not be None"
        raise AssertionError(errmsg)

    expected_name = "extension.my-ext"
    if logger.name != expected_name:
        errmsg = "Expected logger name '{}', got '{}'".format(expected_name, logger.name)
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for app_config property
# =============================================================================

def test_context_app_config_returns_application_config():
    """
        Test that the app_config property returns the application configuration.
    """
    app_config_data = {"app_setting": "app_value"}
    app_ctx = _FakeAppContext(config=app_config_data)
    ctx = ExtensionContext(extension_name="my-ext", app_context=app_ctx, config={})

    result = ctx.app_config
    if result is not app_config_data:
        errmsg = "Expected app_config to be the same instance from app context"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for endpoint_registry property
# =============================================================================

def test_context_endpoint_registry_returns_registry():
    """
        Test that the endpoint_registry property returns the endpoint registry.
    """
    fake_registry = _FakeEndpointRegistry(name="test-registry")
    app_ctx = _FakeAppContext(endpoint_registry=fake_registry)
    ctx = ExtensionContext(extension_name="my-ext", app_context=app_ctx, config={})

    result = ctx.endpoint_registry
    if result is not fake_registry:
        errmsg = "Expected endpoint_registry to be the same instance from app context"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for url_node_map property
# =============================================================================

def test_context_url_node_map_returns_map():
    """
        Test that the url_node_map property returns the URL node map.
    """
    fake_map = _FakeUrlNodeMap(name="test-map")
    app_ctx = _FakeAppContext(url_node_map=fake_map)
    ctx = ExtensionContext(extension_name="my-ext", app_context=app_ctx, config={})

    result = ctx.url_node_map
    if result is not fake_map:
        errmsg = "Expected url_node_map to be the same instance from app context"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for middleware property
# =============================================================================

def test_context_middleware_returns_middleware_list():
    """
        Test that the middleware property returns the middleware list.
    """
    mw_a = _FakeMiddleware(name="mw-a")
    mw_b = _FakeMiddleware(name="mw-b")
    middleware_list = [mw_a, mw_b]
    app_ctx = _FakeAppContext(middleware=middleware_list)
    ctx = ExtensionContext(extension_name="my-ext", app_context=app_ctx, config={})

    result = ctx.middleware
    if result is not middleware_list:
        errmsg = "Expected middleware to be the same instance from app context"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for register_service() and get_service()
# =============================================================================

def test_context_register_service_stores_service():
    """
        Test that register_service() stores a service retrievable by get_service().
    """
    app_ctx = _FakeAppContext()
    ctx = ExtensionContext(extension_name="my-ext", app_context=app_ctx, config={})

    service = {"type": "cache"}
    ctx.register_service("cache-service", service)

    result = ctx.get_service("cache-service")
    if result is not service:
        errmsg = "Expected get_service to return the registered service"
        raise AssertionError(errmsg)

    return


def test_context_get_service_returns_none_for_unknown():
    """
        Test that get_service() returns None for an unregistered service name.
    """
    app_ctx = _FakeAppContext()
    ctx = ExtensionContext(extension_name="my-ext", app_context=app_ctx, config={})

    result = ctx.get_service("nonexistent")
    if result is not None:
        errmsg = "Expected get_service to return None for unknown service, got {}".format(result)
        raise AssertionError(errmsg)

    return


def test_context_register_service_raises_when_frozen():
    """
        Test that register_service() raises ExtensionContextFrozenError when frozen.
    """
    app_ctx = _FakeAppContext()
    ctx = ExtensionContext(extension_name="my-ext", app_context=app_ctx, config={})

    ctx.freeze()

    raised = False
    try:
        ctx.register_service("new-service", {"type": "new"})
    except ExtensionContextFrozenError:
        raised = True

    if raised is not True:
        errmsg = "Expected ExtensionContextFrozenError to be raised when registering on frozen context"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for has_dependency() and get_dependency()
# =============================================================================

def test_context_has_dependency_returns_true_when_available():
    """
        Test that has_dependency() returns True when the dependency is registered.
    """
    fake_ext = {"name": "dep-ext"}
    ext_registry = _FakeExtensionRegistry(extensions={"dep-ext": fake_ext})
    app_ctx = _FakeAppContext(extension_registry=ext_registry)
    ctx = ExtensionContext(extension_name="my-ext", app_context=app_ctx, config={})

    result = ctx.has_dependency("dep-ext")
    if result is not True:
        errmsg = "Expected has_dependency to return True for registered extension"
        raise AssertionError(errmsg)

    return


def test_context_has_dependency_returns_false_when_not_available():
    """
        Test that has_dependency() returns False when the dependency is not registered.
    """
    ext_registry = _FakeExtensionRegistry(extensions={})
    app_ctx = _FakeAppContext(extension_registry=ext_registry)
    ctx = ExtensionContext(extension_name="my-ext", app_context=app_ctx, config={})

    result = ctx.has_dependency("missing-ext")
    if result is not False:
        errmsg = "Expected has_dependency to return False for unregistered extension"
        raise AssertionError(errmsg)

    return


def test_context_get_dependency_returns_extension_when_available():
    """
        Test that get_dependency() returns the extension when registered.
    """
    fake_ext = {"name": "dep-ext"}
    ext_registry = _FakeExtensionRegistry(extensions={"dep-ext": fake_ext})
    app_ctx = _FakeAppContext(extension_registry=ext_registry)
    ctx = ExtensionContext(extension_name="my-ext", app_context=app_ctx, config={})

    result = ctx.get_dependency("dep-ext")
    if result is not fake_ext:
        errmsg = "Expected get_dependency to return the registered extension"
        raise AssertionError(errmsg)

    return


def test_context_get_dependency_returns_none_when_not_available():
    """
        Test that get_dependency() returns None when the dependency is not registered.
    """
    ext_registry = _FakeExtensionRegistry(extensions={})
    app_ctx = _FakeAppContext(extension_registry=ext_registry)
    ctx = ExtensionContext(extension_name="my-ext", app_context=app_ctx, config={})

    result = ctx.get_dependency("missing-ext")
    if result is not None:
        errmsg = "Expected get_dependency to return None for unregistered extension"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for freeze()
# =============================================================================

def test_context_freeze_sets_frozen_flag():
    """
        Test that freeze() sets the _frozen flag to True.
    """
    app_ctx = _FakeAppContext()
    ctx = ExtensionContext(extension_name="my-ext", app_context=app_ctx, config={})

    ctx.freeze()

    if ctx._frozen is not True:
        errmsg = "Expected _frozen to be True after freeze(), got {}".format(ctx._frozen)
        raise AssertionError(errmsg)

    return


def test_context_freeze_error_includes_extension_name():
    """
        Test that ExtensionContextFrozenError includes the extension name.
    """
    app_ctx = _FakeAppContext()
    ctx = ExtensionContext(extension_name="my-ext", app_context=app_ctx, config={})

    ctx.freeze()

    caught_error = None
    try:
        ctx.register_service("svc", "value")
    except ExtensionContextFrozenError as err:
        caught_error = err

    if caught_error is None:
        errmsg = "Expected ExtensionContextFrozenError to be raised"
        raise AssertionError(errmsg)

    if caught_error.extension_name != "my-ext":
        errmsg = "Expected extension_name 'my-ext' in error, got '{}'".format(caught_error.extension_name)
        raise AssertionError(errmsg)

    return


# =============================================================================
# Property-Based Tests
# =============================================================================

# Feature: extensibility, Property 25: Extension Context Services
# *For any* ExtensionContext, the app_config, logger, endpoint_registry,
# url_node_map, and middleware properties SHALL return the corresponding
# framework services.
# **Validates: Requirements 10.1, 10.2, 10.3, 10.4, 10.5**

def test_property_25_extension_context_services():
    """
        Property 25: Extension Context Services

        For any ExtensionContext created with a random extension name
        and random app context services, the app_config, logger,
        endpoint_registry, url_node_map, and middleware properties
        SHALL return the corresponding framework services.

        **Validates: Requirements 10.1, 10.2, 10.3, 10.4, 10.5**
    """
    for iteration in range(100):
        ext_name = _generate_random_string(3, 20)
        ext_config = _generate_random_config()

        fake_app_config = {"iteration": iteration, "key": _generate_random_string()}
        fake_endpoint_registry = _FakeEndpointRegistry(name=_generate_random_string())
        fake_url_node_map = _FakeUrlNodeMap(name=_generate_random_string())

        mw_count = random.randint(0, 5)
        fake_middleware = [_FakeMiddleware(name=_generate_random_string()) for _ in range(mw_count)]

        app_ctx = _FakeAppContext(
            config=fake_app_config,
            endpoint_registry=fake_endpoint_registry,
            url_node_map=fake_url_node_map,
            middleware=fake_middleware
        )

        ctx = ExtensionContext(
            extension_name=ext_name,
            app_context=app_ctx,
            config=ext_config
        )

        # Verify app_config returns the application configuration
        result_app_config = ctx.app_config
        if result_app_config is not fake_app_config:
            errmsg = "Iteration {}: app_config did not return the expected app config".format(iteration)
            raise AssertionError(errmsg)

        # Verify logger returns a logger with the correct namespace
        result_logger = ctx.logger
        expected_logger_name = "extension.{}".format(ext_name)
        if result_logger.name != expected_logger_name:
            errmsg = "Iteration {}: Expected logger name '{}', got '{}'".format(
                iteration, expected_logger_name, result_logger.name
            )
            raise AssertionError(errmsg)

        # Verify endpoint_registry returns the endpoint registry
        result_endpoint_registry = ctx.endpoint_registry
        if result_endpoint_registry is not fake_endpoint_registry:
            errmsg = "Iteration {}: endpoint_registry did not return the expected registry".format(iteration)
            raise AssertionError(errmsg)

        # Verify url_node_map returns the URL node map
        result_url_node_map = ctx.url_node_map
        if result_url_node_map is not fake_url_node_map:
            errmsg = "Iteration {}: url_node_map did not return the expected map".format(iteration)
            raise AssertionError(errmsg)

        # Verify middleware returns the middleware list
        result_middleware = ctx.middleware
        if result_middleware is not fake_middleware:
            errmsg = "Iteration {}: middleware did not return the expected list".format(iteration)
            raise AssertionError(errmsg)

    return


# Feature: extensibility, Property 26: Service Registration Round-Trip
# *For any* service registered via register_service(), calling get_service()
# with the same name SHALL return the registered service.
# **Validates: Requirements 10.6, 10.7**

def test_property_26_service_registration_round_trip():
    """
        Property 26: Service Registration Round-Trip

        For any set of randomly named services registered via
        register_service(), calling get_service() with the same
        name SHALL return the exact same service instance.

        **Validates: Requirements 10.6, 10.7**
    """
    for iteration in range(100):
        ext_name = _generate_random_string(3, 20)
        app_ctx = _FakeAppContext()
        ctx = ExtensionContext(
            extension_name=ext_name,
            app_context=app_ctx,
            config={}
        )

        # Register a random number of services
        service_count = random.randint(1, 10)
        registered_services = {}

        for _ in range(service_count):
            svc_name = _generate_random_string(3, 15)
            svc = _generate_random_service()
            ctx.register_service(svc_name, svc)
            registered_services[svc_name] = svc

        # Verify all registered services can be retrieved
        for svc_name, expected_svc in registered_services.items():
            result = ctx.get_service(svc_name)
            if result is not expected_svc:
                errmsg = "Iteration {}: get_service('{}') did not return the registered service".format(
                    iteration, svc_name
                )
                raise AssertionError(errmsg)

        # Verify an unregistered name returns None
        unknown_name = _generate_random_string(20, 30)
        result = ctx.get_service(unknown_name)
        if result is not None:
            errmsg = "Iteration {}: get_service('{}') should return None for unregistered service".format(
                iteration, unknown_name
            )
            raise AssertionError(errmsg)

    return


# Feature: extensibility, Property 27: Context Immutability After Init
# *For any* ExtensionContext that has been frozen, attempting to register
# a service SHALL raise ExtensionContextFrozenError.
# **Validates: Requirements 10.8**

def test_property_27_context_immutability_after_freeze():
    """
        Property 27: Context Immutability After Init

        For any ExtensionContext that has been frozen, attempting to
        register a service SHALL raise ExtensionContextFrozenError,
        and previously registered services SHALL still be accessible.

        **Validates: Requirements 10.8**
    """
    for iteration in range(100):
        ext_name = _generate_random_string(3, 20)
        app_ctx = _FakeAppContext()
        ctx = ExtensionContext(
            extension_name=ext_name,
            app_context=app_ctx,
            config={}
        )

        # Register some services before freezing
        pre_freeze_count = random.randint(0, 5)
        pre_freeze_services = {}
        for _ in range(pre_freeze_count):
            svc_name = _generate_random_string(3, 15)
            svc = _generate_random_service()
            ctx.register_service(svc_name, svc)
            pre_freeze_services[svc_name] = svc

        # Freeze the context
        ctx.freeze()

        # Verify that registering a new service raises ExtensionContextFrozenError
        new_svc_name = _generate_random_string(3, 15)
        new_svc = _generate_random_service()

        raised = False
        caught_error = None
        try:
            ctx.register_service(new_svc_name, new_svc)
        except ExtensionContextFrozenError as err:
            raised = True
            caught_error = err

        if raised is not True:
            errmsg = "Iteration {}: Expected ExtensionContextFrozenError after freeze()".format(iteration)
            raise AssertionError(errmsg)

        if caught_error.extension_name != ext_name:
            errmsg = "Iteration {}: Expected extension_name '{}' in error, got '{}'".format(
                iteration, ext_name, caught_error.extension_name
            )
            raise AssertionError(errmsg)

        # Verify previously registered services are still accessible
        for svc_name, expected_svc in pre_freeze_services.items():
            result = ctx.get_service(svc_name)
            if result is not expected_svc:
                errmsg = "Iteration {}: Pre-freeze service '{}' should still be accessible after freeze".format(
                    iteration, svc_name
                )
                raise AssertionError(errmsg)

    return
