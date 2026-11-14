"""
    Template wiring module.

    This module ties all templating components together, providing
    convenience functions for setting up and tearing down the template
    system. The setup function registers the built-in engine adapters
    whose engine library is installed, registers the built-in filters the
    engine does not already provide, configures the template loader and
    cache, and returns a ready-to-use TemplateRenderer that renders
    named templates through that loader and cache.

    The teardown function cleans up the registry state, which is
    primarily useful for testing.

    Example usage::

        from ccai.webworks.templating.wiring import setup_templating, teardown_templating
        from ccai.webworks.templating.config import TemplateConfig

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

import importlib
import os

from typing import Optional

from ccai.webworks.templating.cache import TemplateCache
from ccai.webworks.templating.config import TemplateConfig
from ccai.webworks.templating.exceptions import TemplateConfigurationError
from ccai.webworks.templating.filters import BUILTIN_FILTERS
from ccai.webworks.templating.loader import TemplateLoader
from ccai.webworks.templating.registry import TemplateEngineRegistry
from ccai.webworks.templating.renderer import TemplateRenderer

# Note: ``Jinja2Adapter`` and ``MakoAdapter`` are imported lazily
# inside :func:`setup_templating` rather than at module scope.
# Each adapter's module top-level-imports its engine library
# (``jinja2`` / ``mako``); webworks declares them as separate optional
# extras, so an eager import here would crash any consumer that
# doesn't have BOTH engines installed. :func:`setup_templating`
# registers each built-in adapter whose library is installed and
# only insists on the one named by the configuration.
# Same rationale as the lazy ``__getattr__`` in
# :mod:`ccai.webworks.templating.__init__`.

# Built-in adapters: engine name -> (adapter module, adapter class,
# engine library the adapter imports, optional extra that installs it).
BUILTIN_ADAPTERS = {
    "jinja2": ("ccai.webworks.templating.jinja2_adapter", "Jinja2Adapter", "jinja2", "jinja2"),
    "mako": ("ccai.webworks.templating.mako_adapter", "MakoAdapter", "mako", "mako"),
}


def _register_builtin_adapters(configured_engine: str) -> None:
    """
        Register the built-in engine adapters whose engine library is installed.

        ``jinja2`` and ``mako`` are separate optional extras. An adapter
        whose library is missing is skipped, unless it is the engine the
        configuration names: that is reported as a configuration error
        naming the extra to install.

        :param configured_engine: The engine name from the TemplateConfig.

        :raises TemplateConfigurationError: If the library of the configured
            built-in engine is not installed.
    """
    for engine_name, adapter_info in BUILTIN_ADAPTERS.items():
        module_name, class_name, library_name, extra_name = adapter_info

        try:
            adapter_module = importlib.import_module(module_name)
        except ModuleNotFoundError as exc:
            missing_name = exc.name or ""
            missing_root = missing_name.split(".")[0]

            # Only a missing engine library is an "engine not installed"
            # condition; any other missing module is a real defect.
            if missing_root != library_name:
                raise

            if engine_name == configured_engine:
                errmsg_lines = [
                    f"The template engine '{engine_name}' is configured but the '{library_name}' package is not installed.",
                    f"Install it with the '{extra_name}' extra, for example: pip install codecraftai-webworks[{extra_name}]",
                ]
                errmsg = os.linesep.join(errmsg_lines)
                raise TemplateConfigurationError(errmsg, field_name="engine") from exc

            continue

        adapter_class = getattr(adapter_module, class_name)
        TemplateEngineRegistry.register(engine_name, adapter_class)

    return


def setup_templating(config: Optional[TemplateConfig] = None) -> TemplateRenderer:
    """
        Set up the templating system with all components wired together.

        Performs the following steps:

        1. Validates the configuration.
        2. Registers Jinja2Adapter as "jinja2" and MakoAdapter as "mako"
           with the TemplateEngineRegistry. An adapter whose engine library
           is not installed is skipped, unless it is the configured engine.
        3. Sets Jinja2 as the default engine, when it is installed.
        4. Creates an engine instance from the configuration; the
           ``engine_options`` are passed to the engine as native options.
        5. Registers each of the BUILTIN_FILTERS the engine does not
           already provide. Jinja2 ships its own ``escape``, ``default``,
           ``sort``, ``join`` and so on, which are kept; for Jinja2 only
           ``date`` and ``json`` are added.
        6. Configures a TemplateLoader from the config directories,
           extensions and encoding.
        7. Configures a TemplateCache from the config settings. When
           ``cache_enabled`` is False the cache has a size of 0, so every
           render reloads and recompiles the template.
        8. Returns a TemplateRenderer wired to the engine, the loader and
           the cache: a named template is resolved by the loader (a name
           without an extension is tried with each configured extension),
           compiled by the engine, and reused from the cache.

        If no config is provided, a default TemplateConfig is used.

        :param config: Optional TemplateConfig with rendering settings.
            When None, a default configuration is used.

        :returns: A configured TemplateRenderer ready to render templates.

        :raises TemplateConfigurationError: If the configuration is invalid,
            the configured engine's library is not installed, or the engine
            does not accept the ``engine_options``.

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

    config.validate()

    # --- 19.1  Register built-in engine adapters ---
    #
    # Lazy import: see the module-level note. Each adapter's library
    # import (``import jinja2`` / ``from mako import ...``) only
    # runs when :func:`setup_templating` is actually called, and an
    # engine that is not installed is only an error when it is the
    # one the configuration asks for.
    _register_builtin_adapters(config.engine)

    # Jinja2 is the default engine when it is installed; on a Mako-only
    # install there is no "jinja2" adapter to make the default.
    if TemplateEngineRegistry.is_registered("jinja2"):
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
        # NOT Jinja2 extension modules; they go to the TemplateLoader
        # below.  Jinja2 extensions should be passed via engine_options
        # if needed.

    # Merge any extra engine_options from config
    engine_kwargs.update(config.engine_options)

    # Create the engine instance via the registry
    engine = TemplateEngineRegistry.create(config.engine, **engine_kwargs)

    # --- 19.2  Register built-in filters ---
    #
    # A filter the engine already provides is left alone: replacing
    # Jinja2's own ``escape`` / ``default`` / ``format`` / ``sort`` with
    # differently behaving functions breaks ordinary Jinja2 templates.
    for filter_name, filter_func in BUILTIN_FILTERS.items():
        if engine.has_filter(filter_name) is False:
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
        # Disabled cache (development mode): a TemplateCache with a
        # max_size of 0 stores nothing, so every render reloads and
        # recompiles the template.
        cache = TemplateCache(
            max_size=0,
            auto_reload=True,
        )

    # Build and return the renderer. The loader and cache are what make
    # config.extensions and the cache settings take effect: the renderer
    # resolves names through the loader and keeps compiled templates in
    # the cache (template_name -> Loader -> Cache -> Engine).
    renderer = TemplateRenderer(engine=engine, loader=loader, cache=cache)

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
