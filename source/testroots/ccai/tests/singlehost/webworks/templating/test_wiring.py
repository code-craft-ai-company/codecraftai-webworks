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

from ccai.webworks.templating.cache import TemplateCache
from ccai.webworks.templating.config import TemplateConfig
from ccai.webworks.templating.filters import BUILTIN_FILTERS
from ccai.webworks.templating.jinja2_adapter import Jinja2Adapter
from ccai.webworks.templating.loader import TemplateLoader
from ccai.webworks.templating.mako_adapter import MakoAdapter
from ccai.webworks.templating.registry import TemplateEngineRegistry
from ccai.webworks.templating.renderer import TemplateRenderer
from ccai.webworks.templating.wiring import setup_templating, teardown_templating


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


def _write_template(directory: str, name: str, content: str) -> str:
    """
        Write a template file.

        :param directory: Directory to write into.
        :param name: Template file name.
        :param content: Template source.

        :returns: The path of the written file.
    """
    template_path = os.path.join(directory, name)
    with open(template_path, "w", encoding="utf-8") as f:
        f.write(content)
    return template_path


def _bump_mtime(path: str) -> None:
    """
        Move a file's modification time forward, so a change is visible to
        modification-time checks even within the file system's timestamp
        resolution.

        :param path: Path of the file to touch.
    """
    stat_result = os.stat(path)
    new_mtime = stat_result.st_mtime + 10
    os.utime(path, (new_mtime, new_mtime))
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

    # The renderer owns the TemplateCache built from the config
    cache = renderer.cache
    if not isinstance(cache, TemplateCache):
        raise AssertionError(f"Expected a TemplateCache on the renderer, got {cache!r}")

    if cache.max_size != 200 or cache.auto_reload is not False:
        raise AssertionError(
            f"Expected max_size=200, auto_reload=False, got "
            f"max_size={cache.max_size}, auto_reload={cache.auto_reload}"
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

    # A disabled cache stores nothing
    cache = renderer.cache
    if not isinstance(cache, TemplateCache):
        raise AssertionError(f"Expected a TemplateCache on the renderer, got {cache!r}")

    if cache.max_size != 0:
        raise AssertionError(f"Expected max_size 0 for a disabled cache, got {cache.max_size}")

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
# Loader and cache reach the renderer (docstring steps 5-7)
# =============================================================================

def test_setup_wires_loader_into_renderer():
    """
        Test that the TemplateLoader built from the config is the renderer's
        loader, with the configured directories, extensions and encoding.
    """
    _clean_state()

    with tempfile.TemporaryDirectory() as tmpdir:
        config = TemplateConfig(
            directories=[tmpdir],
            extensions=[".j2", ".html"],
            encoding="utf-8",
        )
        renderer = setup_templating(config)

        loader = renderer.loader
        if not isinstance(loader, TemplateLoader):
            raise AssertionError(f"Expected a TemplateLoader on the renderer, got {loader!r}")

        if loader.directories != [tmpdir]:
            raise AssertionError(f"Expected directories {[tmpdir]!r}, got {loader.directories!r}")

        if loader.extensions != [".j2", ".html"]:
            raise AssertionError(f"Expected extensions ['.j2', '.html'], got {loader.extensions!r}")

        if loader.encoding != "utf-8":
            raise AssertionError(f"Expected encoding 'utf-8', got {loader.encoding!r}")

    _clean_state()
    return


def test_setup_applies_configured_extension():
    """
        Test that config.extensions takes effect: a template named without its
        extension is found through a configured extension.
    """
    _clean_state()

    with tempfile.TemporaryDirectory() as tmpdir:
        _write_template(tmpdir, "greeting.j2", "Hello {{ name }}!")

        config = TemplateConfig(directories=[tmpdir], extensions=[".j2"])
        renderer = setup_templating(config)

        result = renderer.render("greeting", {"name": "World"})

        if result != "Hello World!":
            raise AssertionError(f"Expected 'Hello World!', got {result!r}")

    _clean_state()
    return


def test_setup_applies_configured_extension_with_mako():
    """
        Test that config.extensions takes effect for the Mako engine too.
    """
    _clean_state()

    with tempfile.TemporaryDirectory() as tmpdir:
        _write_template(tmpdir, "greeting.mako", "Hello ${name}!")

        config = TemplateConfig(engine="mako", directories=[tmpdir], extensions=[".mako"])
        renderer = setup_templating(config)

        result = renderer.render("greeting", {"name": "World"})

        if result != "Hello World!":
            raise AssertionError(f"Expected 'Hello World!', got {result!r}")

    _clean_state()
    return


def test_setup_reuses_cached_template():
    """
        Test that with caching enabled (and auto_reload off) the compiled
        template is cached on the first render and reused afterwards: the
        cache keeps the same object and a later change to the file is not
        reloaded.
    """
    _clean_state()

    with tempfile.TemporaryDirectory() as tmpdir:
        template_path = _write_template(tmpdir, "page.html", "first {{ n }}")

        config = TemplateConfig(directories=[tmpdir], cache_enabled=True, auto_reload=False)
        renderer = setup_templating(config)

        first = renderer.render("page.html", {"n": 1})
        cached = renderer.cache.get("page.html")

        _write_template(tmpdir, "page.html", "second {{ n }}")
        _bump_mtime(template_path)

        again = renderer.render("page", {"n": 2})

        if first != "first 1" or again != "first 2":
            raise AssertionError(f"Expected 'first 1' then 'first 2', got {first!r} then {again!r}")

        if cached is None or renderer.cache.get("page.html") is not cached:
            raise AssertionError("Expected the compiled template to be cached and reused")

        if renderer.cache.size != 1:
            raise AssertionError(f"Expected 1 cached template, got {renderer.cache.size}")

    _clean_state()
    return


def test_setup_reuses_cached_template_with_mako():
    """
        Test that the Mako engine's templates are cached and reused as well.
    """
    _clean_state()

    with tempfile.TemporaryDirectory() as tmpdir:
        template_path = _write_template(tmpdir, "page.html", "first ${n}")

        config = TemplateConfig(engine="mako", directories=[tmpdir], cache_enabled=True, auto_reload=False)
        renderer = setup_templating(config)

        first = renderer.render("page.html", {"n": 1})

        _write_template(tmpdir, "page.html", "second ${n}")
        _bump_mtime(template_path)

        again = renderer.render("page.html", {"n": 2})

        if first != "first 1" or again != "first 2":
            raise AssertionError(f"Expected 'first 1' then 'first 2', got {first!r} then {again!r}")

    _clean_state()
    return


def test_setup_auto_reload_reloads_modified_template():
    """
        Test that with auto_reload a modified template is recompiled.
    """
    _clean_state()

    with tempfile.TemporaryDirectory() as tmpdir:
        template_path = _write_template(tmpdir, "page.html", "first")

        config = TemplateConfig(directories=[tmpdir], cache_enabled=True, auto_reload=True)
        renderer = setup_templating(config)

        first = renderer.render("page.html")

        _write_template(tmpdir, "page.html", "second")
        _bump_mtime(template_path)

        second = renderer.render("page.html")

        if first != "first" or second != "second":
            raise AssertionError(f"Expected 'first' then 'second', got {first!r} then {second!r}")

    _clean_state()
    return


def test_setup_cache_disabled_reloads_modified_template():
    """
        Test that with caching disabled every render reloads the template, so
        a modified file is picked up even without auto_reload.
    """
    _clean_state()

    with tempfile.TemporaryDirectory() as tmpdir:
        _write_template(tmpdir, "page.html", "first")

        config = TemplateConfig(directories=[tmpdir], cache_enabled=False, auto_reload=False)
        renderer = setup_templating(config)

        first = renderer.render("page.html")

        _write_template(tmpdir, "page.html", "second")

        second = renderer.render("page.html")

        if first != "first" or second != "second":
            raise AssertionError(f"Expected 'first' then 'second', got {first!r} then {second!r}")

        if renderer.cache.size != 0:
            raise AssertionError(f"Expected nothing cached when caching is disabled, got {renderer.cache.size}")

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
    result = renderer.render_string("Hello {{ name }}!", {"name": "CodeCraftX"})

    if result != "Hello CodeCraftX!":
        raise AssertionError(
            f"Expected 'Hello CodeCraftX!', got '{result}'"
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
    result = renderer.render_string("Hello ${name}!", {"name": "CodeCraftX"})

    if result != "Hello CodeCraftX!":
        raise AssertionError(
            f"Expected 'Hello CodeCraftX!', got '{result}'"
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
