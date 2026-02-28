"""
    Tests for the template wiring module.

    This module tests the setup_templating() and teardown_templating()
    functions that wire all templating components together, including:
    - Registration of built-in engine adapters (Jinja2, Mako)
    - Registration of built-in filters with engines
    - Integration of TemplateLoader with engines
    - Integration of TemplateCache with engines
    - Teardown and cleanup of registry state
"""

import os
import tempfile

from automojo.webworks.templating.config import TemplateConfig
from automojo.webworks.templating.filters import BUILTIN_FILTERS
from automojo.webworks.templating.jinja2_adapter import Jinja2Adapter
from automojo.webworks.templating.mako_adapter import MakoAdapter
from automojo.webworks.templating.registry import TemplateEngineRegistry
from automojo.webworks.templating.renderer import TemplateRenderer
from automojo.webworks.templating.wiring import setup_templating, teardown_templating


# =============================================================================
# Helpers
# =============================================================================

def _clean_state():
    """
        Clear registry state for a clean test.
    """
    TemplateEngineRegistry.clear()
    TemplateEngineRegistry._default_engine = "jinja2"
    return


# =============================================================================
# 19.1  Register built-in engine adapters
# =============================================================================

def test_setup_registers_jinja2_adapter():
    """
        Test that setup_templating registers Jinja2Adapter as "jinja2".
    """
    _clean_state()

    setup_templating()

    registered_class = TemplateEngineRegistry.get("jinja2")

    if registered_class is not Jinja2Adapter:
        raise AssertionError(
            f"Expected Jinja2Adapter, got {registered_class}"
        )

    _clean_state()
    return


def test_setup_registers_mako_adapter():
    """
        Test that setup_templating registers MakoAdapter as "mako".
    """
    _clean_state()

    setup_templating()

    registered_class = TemplateEngineRegistry.get("mako")

    if registered_class is not MakoAdapter:
        raise AssertionError(
            f"Expected MakoAdapter, got {registered_class}"
        )

    _clean_state()
    return


def test_setup_sets_jinja2_as_default():
    """
        Test that setup_templating sets Jinja2 as the default engine.
    """
    _clean_state()

    setup_templating()

    default_engine = TemplateEngineRegistry.get_default()

    if default_engine != "jinja2":
        raise AssertionError(
            f"Expected default engine 'jinja2', got '{default_engine}'"
        )

    _clean_state()
    return


def test_setup_returns_template_renderer():
    """
        Test that setup_templating returns a TemplateRenderer instance.
    """
    _clean_state()

    renderer = setup_templating()

    if not isinstance(renderer, TemplateRenderer):
        raise AssertionError(
            f"Expected TemplateRenderer, got {type(renderer)}"
        )

    _clean_state()
    return


def test_setup_default_config_uses_jinja2():
    """
        Test that setup_templating with no config uses Jinja2 engine.
    """
    _clean_state()

    renderer = setup_templating()

    if not isinstance(renderer.engine, Jinja2Adapter):
        raise AssertionError(
            f"Expected Jinja2Adapter engine, got {type(renderer.engine)}"
        )

    _clean_state()
    return


def test_setup_with_mako_config():
    """
        Test that setup_templating with mako config uses MakoAdapter.
    """
    _clean_state()

    config = TemplateConfig(engine="mako")
    renderer = setup_templating(config)

    if not isinstance(renderer.engine, MakoAdapter):
        raise AssertionError(
            f"Expected MakoAdapter engine, got {type(renderer.engine)}"
        )

    _clean_state()
    return


# =============================================================================
# 19.2  Register built-in filters
# =============================================================================

def test_setup_registers_builtin_filters_with_jinja2():
    """
        Test that all BUILTIN_FILTERS are registered with the Jinja2 engine.
    """
    _clean_state()

    renderer = setup_templating()
    engine = renderer.engine

    # Jinja2Adapter stores filters in its environment
    env_filters = engine._environment.filters

    for filter_name in BUILTIN_FILTERS:
        if filter_name not in env_filters:
            raise AssertionError(
                f"Built-in filter '{filter_name}' not registered with Jinja2 engine"
            )

    _clean_state()
    return


def test_setup_registers_builtin_filters_with_mako():
    """
        Test that all BUILTIN_FILTERS are registered with the Mako engine.
    """
    _clean_state()

    config = TemplateConfig(engine="mako")
    renderer = setup_templating(config)
    engine = renderer.engine

    # MakoAdapter stores filters in its _filters dict
    for filter_name in BUILTIN_FILTERS:
        if filter_name not in engine._filters:
            raise AssertionError(
                f"Built-in filter '{filter_name}' not registered with Mako engine"
            )

    _clean_state()
    return


def test_setup_filters_are_callable():
    """
        Test that registered filters are callable functions.
    """
    _clean_state()

    renderer = setup_templating()
    engine = renderer.engine

    env_filters = engine._environment.filters

    for filter_name in BUILTIN_FILTERS:
        if not callable(env_filters[filter_name]):
            raise AssertionError(
                f"Filter '{filter_name}' is not callable"
            )

    _clean_state()
    return


# =============================================================================
# 19.3  Integrate TemplateLoader with engines
# =============================================================================

def test_setup_with_template_directories():
    """
        Test that setup_templating configures template directories from config.
    """
    _clean_state()

    with tempfile.TemporaryDirectory() as tmpdir:
        config = TemplateConfig(directories=[tmpdir])
        renderer = setup_templating(config)

        # The engine should have the configured directories
        engine = renderer.engine
        if isinstance(engine, Jinja2Adapter):
            loader = engine._environment.loader
            if tmpdir not in loader.searchpath:
                raise AssertionError(
                    f"Template directory '{tmpdir}' not configured in engine loader"
                )

    _clean_state()
    return


def test_setup_with_multiple_directories():
    """
        Test that setup_templating supports multiple template directories.
    """
    _clean_state()

    with tempfile.TemporaryDirectory() as dir1:
        with tempfile.TemporaryDirectory() as dir2:
            config = TemplateConfig(directories=[dir1, dir2])
            renderer = setup_templating(config)

            engine = renderer.engine
            if isinstance(engine, Jinja2Adapter):
                loader = engine._environment.loader
                if dir1 not in loader.searchpath:
                    raise AssertionError(
                        f"First directory '{dir1}' not in engine loader"
                    )
                if dir2 not in loader.searchpath:
                    raise AssertionError(
                        f"Second directory '{dir2}' not in engine loader"
                    )

    _clean_state()
    return


def test_setup_renders_template_from_directory():
    """
        Test that a renderer from setup_templating can render templates
        from configured directories.
    """
    _clean_state()

    with tempfile.TemporaryDirectory() as tmpdir:
        # Write a template file
        template_path = os.path.join(tmpdir, "hello.html")
        with open(template_path, "w", encoding="utf-8") as f:
            f.write("Hello {{ name }}!")

        config = TemplateConfig(directories=[tmpdir])
        renderer = setup_templating(config)

        result = renderer.render("hello.html", {"name": "World"})

        if result != "Hello World!":
            raise AssertionError(
                f"Expected 'Hello World!', got '{result}'"
            )

    _clean_state()
    return


# =============================================================================
# 19.4  Integrate TemplateCache with engines
# =============================================================================

def test_setup_with_cache_enabled():
    """
        Test that setup_templating configures caching when cache_enabled is True.
    """
    _clean_state()

    config = TemplateConfig(cache_enabled=True, cache_size=200)
    renderer = setup_templating(config)

    # Jinja2 stores cache_size on the adapter instance
    engine = renderer.engine
    if isinstance(engine, Jinja2Adapter):
        if engine._cache_size != 200:
            raise AssertionError(
                f"Expected cache_size 200, got {engine._cache_size}"
            )

    _clean_state()
    return


def test_setup_with_cache_disabled():
    """
        Test that setup_templating disables caching when cache_enabled is False.
    """
    _clean_state()

    config = TemplateConfig(cache_enabled=False)
    renderer = setup_templating(config)

    # When cache is disabled, Jinja2 should have cache_size=0
    engine = renderer.engine
    if isinstance(engine, Jinja2Adapter):
        # cache_size=0 means no caching in Jinja2
        if engine._cache_size != 0:
            raise AssertionError(
                f"Expected cache_size 0 for disabled cache, got {engine._cache_size}"
            )

    _clean_state()
    return


def test_setup_with_auto_reload():
    """
        Test that setup_templating configures auto_reload for development.
    """
    _clean_state()

    config = TemplateConfig(auto_reload=True)
    renderer = setup_templating(config)

    engine = renderer.engine
    if isinstance(engine, Jinja2Adapter):
        if not engine._environment.auto_reload:
            raise AssertionError(
                "Expected auto_reload to be True on the Jinja2 environment"
            )

    _clean_state()
    return


def test_setup_with_auto_reload_disabled():
    """
        Test that setup_templating configures auto_reload=False for production.
    """
    _clean_state()

    config = TemplateConfig(auto_reload=False)
    renderer = setup_templating(config)

    engine = renderer.engine
    if isinstance(engine, Jinja2Adapter):
        if engine._environment.auto_reload:
            raise AssertionError(
                "Expected auto_reload to be False on the Jinja2 environment"
            )

    _clean_state()
    return


# =============================================================================
# Teardown Tests
# =============================================================================

def test_teardown_clears_registry():
    """
        Test that teardown_templating clears all registered engines.
    """
    _clean_state()

    setup_templating()

    # Verify engines are registered
    if not TemplateEngineRegistry.is_registered("jinja2"):
        raise AssertionError("jinja2 should be registered after setup")

    teardown_templating()

    engines = TemplateEngineRegistry.list_engines()
    if len(engines) != 0:
        raise AssertionError(
            f"Expected empty registry after teardown, got {engines}"
        )

    _clean_state()
    return


def test_teardown_resets_default_engine():
    """
        Test that teardown_templating resets the default engine to jinja2.
    """
    _clean_state()

    setup_templating()
    teardown_templating()

    default_name = TemplateEngineRegistry.get_default()

    if default_name != "jinja2":
        raise AssertionError(
            f"Expected default 'jinja2' after teardown, got '{default_name}'"
        )

    _clean_state()
    return


# =============================================================================
# Integration / End-to-End Tests
# =============================================================================

def test_setup_render_string_with_jinja2():
    """
        Test that a renderer from setup_templating can render string templates.
    """
    _clean_state()

    renderer = setup_templating()
    result = renderer.render_string("Hello {{ name }}!", {"name": "AutomationX"})

    if result != "Hello AutomationX!":
        raise AssertionError(
            f"Expected 'Hello AutomationX!', got '{result}'"
        )

    _clean_state()
    return


def test_setup_render_string_with_mako():
    """
        Test that a renderer from setup_templating with Mako can render strings.
    """
    _clean_state()

    config = TemplateConfig(engine="mako")
    renderer = setup_templating(config)
    result = renderer.render_string("Hello ${name}!", {"name": "AutomationX"})

    if result != "Hello AutomationX!":
        raise AssertionError(
            f"Expected 'Hello AutomationX!', got '{result}'"
        )

    _clean_state()
    return


def test_setup_with_custom_engine_options():
    """
        Test that engine_options from config are passed to the engine.
    """
    _clean_state()

    config = TemplateConfig(
        engine="jinja2",
        engine_options={"auto_reload": True},
    )
    renderer = setup_templating(config)

    engine = renderer.engine
    if isinstance(engine, Jinja2Adapter):
        if not engine._environment.auto_reload:
            raise AssertionError(
                "Expected auto_reload from engine_options to be applied"
            )

    _clean_state()
    return


def test_setup_teardown_cycle():
    """
        Test that setup and teardown can be called multiple times cleanly.
    """
    _clean_state()

    # First cycle
    renderer1 = setup_templating()
    result1 = renderer1.render_string("{{ x }}", {"x": "one"})
    teardown_templating()

    # Second cycle
    renderer2 = setup_templating()
    result2 = renderer2.render_string("{{ x }}", {"x": "two"})
    teardown_templating()

    if result1 != "one":
        raise AssertionError(f"Expected 'one', got '{result1}'")

    if result2 != "two":
        raise AssertionError(f"Expected 'two', got '{result2}'")

    _clean_state()
    return
