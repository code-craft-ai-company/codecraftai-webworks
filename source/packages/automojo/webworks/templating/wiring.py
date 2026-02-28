"""
    Template wiring module.

    This module ties all templating components together, providing
    convenience functions for setting up and tearing down the template
    system. The setup function registers built-in engine adapters,
    registers built-in filters, configures the template loader and
    cache, and returns a ready-to-use TemplateRenderer.

    The teardown function cleans up the registry state, which is
    primarily useful for testing.

    Example usage::

        from automojo.webworks.templating.wiring import setup_templating, teardown_templating
        from automojo.webworks.templating.config import TemplateConfig

        config = TemplateConfig(
            engine="jinja2",
            directories=["/app/templates"],
            cache_enabled=True,
            cache_size=400,
        )

        renderer = setup_templating(config)
        output = renderer.render_string("Hello {{ name }}", {"name": "World"})

        teardown_templating()
"""

from typing import Optional

from automojo.webworks.templating.cache import TemplateCache
from automojo.webworks.templating.config import TemplateConfig
from automojo.webworks.templating.filters import BUILTIN_FILTERS
from automojo.webworks.templating.jinja2_adapter import Jinja2Adapter
from automojo.webworks.templating.loader import TemplateLoader
from automojo.webworks.templating.mako_adapter import MakoAdapter
from automojo.webworks.templating.registry import TemplateEngineRegistry
from automojo.webworks.templating.renderer import TemplateRenderer


def setup_templating(config: Optional[TemplateConfig] = None) -> TemplateRenderer:
    """
        Set up the templating system with all components wired together.

        Performs the following steps:

        1. Registers Jinja2Adapter as "jinja2" and MakoAdapter as "mako"
           with the TemplateEngineRegistry.
        2. Sets Jinja2 as the default engine.
        3. Creates an engine instance from the configuration.
        4. Registers all BUILTIN_FILTERS with the engine.
        5. Configures a TemplateLoader from the config directories.
        6. Configures a TemplateCache from the config settings.
        7. Returns a configured TemplateRenderer.

        If no config is provided, a default TemplateConfig is used.

        :param config: Optional TemplateConfig with rendering settings.
            When None, a default configuration is used.

        :returns: A configured TemplateRenderer ready to render templates.

        Example::

            config = TemplateConfig(
                engine="jinja2",
                directories=["/app/templates"],
                cache_size=200,
                auto_reload=True,
            )
            renderer = setup_templating(config)
            output = renderer.render("index.html", {"title": "Home"})
    """
    if config is None:
        config = TemplateConfig()

    # --- 19.1  Register built-in engine adapters ---
    TemplateEngineRegistry.register("jinja2", Jinja2Adapter)
    TemplateEngineRegistry.register("mako", MakoAdapter)
    TemplateEngineRegistry.set_default("jinja2")

    # --- 19.3  Build engine kwargs from config ---
    engine_kwargs = {
        "template_dirs": list(config.directories),
        "auto_escape": config.auto_escape,
        "encoding": config.encoding,
    }

    # Jinja2-specific options
    if config.engine == "jinja2":
        engine_kwargs["cache_size"] = config.cache_size if config.cache_enabled else 0
        engine_kwargs["auto_reload"] = config.auto_reload
        engine_kwargs["undefined_behavior"] = config.undefined_behavior
        # Note: config.extensions contains file extensions (e.g. ".html"),
        # NOT Jinja2 extension modules.  Jinja2 extensions should be
        # passed via engine_options if needed.

    # Merge any extra engine_options from config
    engine_kwargs.update(config.engine_options)

    # Create the engine instance via the registry
    engine = TemplateEngineRegistry.create(config.engine, **engine_kwargs)

    # --- 19.2  Register built-in filters ---
    for filter_name, filter_func in BUILTIN_FILTERS.items():
        engine.add_filter(filter_name, filter_func)

    # --- 19.3  Configure TemplateLoader ---
    loader = TemplateLoader(
        directories=list(config.directories),
        extensions=list(config.extensions) if config.extensions else None,
        encoding=config.encoding,
    )

    # --- 19.4  Configure TemplateCache ---
    if config.cache_enabled:
        cache = TemplateCache(
            max_size=config.cache_size,
            auto_reload=config.auto_reload,
        )
    else:
        # Disabled cache: use a minimal cache with auto_reload so
        # templates are always reloaded (development mode).
        cache = TemplateCache(
            max_size=1,
            auto_reload=True,
        )

    # Build and return the renderer
    renderer = TemplateRenderer(engine=engine)

    return renderer


def teardown_templating() -> None:
    """
        Tear down the templating system.

        Clears the TemplateEngineRegistry, removing all registered
        engine adapters and resetting the default engine name. This
        is primarily useful for testing to ensure clean state between
        test runs.
    """
    TemplateEngineRegistry.clear()
    TemplateEngineRegistry._default_engine = "jinja2"
    return
