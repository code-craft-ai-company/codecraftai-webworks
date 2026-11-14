"""
    Tests for the ApplicationContext class.

    This module contains unit tests for the application context an
    application gives its extensions.
"""

from ccai.webworks.endpoints.registry import EndpointRegistry
from ccai.webworks.extensibility.applicationcontext import ApplicationContext
from ccai.webworks.routing.middlewareregistry import MiddlewareRegistry
from ccai.webworks.urlnodemap.urlnodemap import URLNodeMap


def _make_context() -> ApplicationContext:
    """
        Create an ApplicationContext with fresh registries.

        :returns: The context.
    """
    rtnval = ApplicationContext(
        logger_name="myapp",
        endpoint_registry=EndpointRegistry(),
        middleware_registry=MiddlewareRegistry()
    )
    return rtnval


def test_context_exposes_the_services_it_was_created_with():
    """
        Test that the endpoint registry, the middleware registry and a URL
        node map are available from construction.
    """
    endpoint_registry = EndpointRegistry()
    middleware_registry = MiddlewareRegistry()
    url_node_map = URLNodeMap()

    context = ApplicationContext(
        logger_name="myapp",
        endpoint_registry=endpoint_registry,
        middleware_registry=middleware_registry,
        url_node_map=url_node_map
    )

    if context.endpoint_registry is not endpoint_registry:
        raise AssertionError("Expected the endpoint registry given")

    if context.middleware is not middleware_registry:
        raise AssertionError("Expected the middleware registry given")

    if context.url_node_map is not url_node_map:
        raise AssertionError("Expected the URL node map given")

    if context.logger_name != "myapp":
        raise AssertionError("Expected the logger name 'myapp', got {}".format(context.logger_name))

    return


def test_context_creates_an_empty_url_node_map_by_default():
    """
        Test that a context created without a URL node map has an empty one.
    """
    context = _make_context()

    if not isinstance(context.url_node_map, URLNodeMap):
        raise AssertionError("Expected a URLNodeMap")

    leaves = list(context.url_node_map.iterate_leaves())
    if len(leaves) != 0:
        raise AssertionError("Expected an empty map, got {}".format(leaves))

    return


def test_context_config_and_extensions_are_bound_later():
    """
        Test that the configuration and the extension machinery are None
        until they are bound.
    """
    context = _make_context()

    if context.config is not None or context.extension_registry is not None or context.component_hooks is not None:
        raise AssertionError("Expected nothing bound yet")

    config = {"server": {"port": 8000}}
    registry = object()
    component_hooks = object()

    context.bind_config(config)
    context.bind_extensions(registry, component_hooks)

    if context.config is not config:
        raise AssertionError("Expected the bound configuration")

    if context.extension_registry is not registry or context.component_hooks is not component_hooks:
        raise AssertionError("Expected the bound extension registry and component hooks")

    return


def test_get_logger_is_namespaced_under_the_application_logger():
    """
        Test that loggers are named <application logger>.<name>.
    """
    context = _make_context()

    logger = context.get_logger("extension.audit")

    if logger.name != "myapp.extension.audit":
        raise AssertionError("Expected 'myapp.extension.audit', got {}".format(logger.name))

    return
