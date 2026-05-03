"""
    Web templating module.

    This module provides template engine integration and rendering
    capabilities for the web framework, enabling dynamic HTML
    generation with support for template inheritance, context
    passing, and security features like auto-escaping.

    The module provides a pluggable architecture supporting multiple
    template engines (Jinja2, Mako) through a unified interface.

    Adapter import policy
    ---------------------

    Neither ``jinja2`` nor ``mako`` is declared as a webworks
    dependency: each consumer is expected to install whichever
    template engine it actually uses. :class:`Jinja2Adapter` and
    :class:`MakoAdapter` are therefore both available via *lazy*
    attribute access (``__getattr__``) rather than eager imports
    here — greedy-importing either adapter at package-import time
    would crash on any consumer that uses the *other* engine, or no
    template engine at all, with a ``ModuleNotFoundError`` from the
    adapter module's top-level ``from jinja2 import …`` /
    ``from mako import …`` lines. Lazy access defers each adapter's
    library import to the first reference so consumers pay only for
    what they touch.
"""

from typing import Any

from automojo.webworks.templating.cache import TemplateCache
from automojo.webworks.templating.config import TemplateConfig
from automojo.webworks.templating.context import (
    ContextProcessorRegistry,
    GlobalContext,
    RequestContext,
    TemplateContext,
)
from automojo.webworks.templating.engine import TemplateEngine
from automojo.webworks.templating.escaping import SafeString, safe
from automojo.webworks.templating.filters import (
    BUILTIN_FILTERS,
    apply_filters,
    filter_date,
    filter_default,
    filter_escape,
    filter_first,
    filter_format,
    filter_join,
    filter_json,
    filter_last,
    filter_length,
    filter_lower,
    filter_reverse,
    filter_safe,
    filter_sort,
    filter_title,
    filter_trim,
    filter_upper,
)
from automojo.webworks.templating.exceptions import (
    TemplateConfigurationError,
    TemplateEngineNotFoundError,
    TemplateError,
    TemplateFilterNotFoundError,
    TemplateInheritanceError,
    TemplateNotFoundError,
    TemplateRenderError,
    TemplateSyntaxError,
    UndefinedVariableError,
)
from automojo.webworks.templating.loader import TemplateLoader
from automojo.webworks.templating.registry import TemplateEngineRegistry
from automojo.webworks.templating.renderer import TemplateRenderer
from automojo.webworks.templating.response import (
    StreamingTemplateResponse,
    TemplateResponse,
    render_template,
    render_template_stream,
)
from automojo.webworks.templating.wiring import (
    setup_templating,
    teardown_templating,
)


def __getattr__(name: str) -> Any:
    """
        Lazily resolve template-engine adapters so consumers pay
        only for the engine they actually use.

        ``Jinja2Adapter`` and ``MakoAdapter`` each top-level-import
        their respective engine library (``jinja2`` /  ``mako``).
        Neither library is declared as a webworks dependency —
        consumers that pick Jinja2 ``pip install jinja2`` and
        consumers that pick Mako ``pip install mako``. Resolving the
        adapter classes on first attribute access defers the engine
        import to the call site so importing the package itself
        succeeds even when the consumer hasn't installed either
        engine, and Jinja2-only consumers never trigger the Mako
        import (and vice versa).

        :param name: Attribute name being looked up on the module.

        :returns: The resolved attribute value.
        :raises AttributeError: When the requested name is not a
                                lazily-resolvable export.
    """
    if name == "Jinja2Adapter":
        from automojo.webworks.templating.jinja2_adapter import (
            Jinja2Adapter as _Jinja2Adapter,
        )
        return _Jinja2Adapter

    if name == "MakoAdapter":
        from automojo.webworks.templating.mako_adapter import (
            MakoAdapter as _MakoAdapter,
        )
        return _MakoAdapter

    errmsg = "module {!r} has no attribute {!r}".format(__name__, name)
    raise AttributeError(errmsg)


__all__ = [
    "BUILTIN_FILTERS",
    "ContextProcessorRegistry",
    "GlobalContext",
    "Jinja2Adapter",
    "MakoAdapter",
    "RequestContext",
    "SafeString",
    "TemplateCache",
    "TemplateConfig",
    "TemplateConfigurationError",
    "TemplateContext",
    "TemplateEngine",
    "TemplateEngineNotFoundError",
    "TemplateEngineRegistry",
    "TemplateError",
    "TemplateFilterNotFoundError",
    "TemplateInheritanceError",
    "TemplateLoader",
    "TemplateNotFoundError",
    "TemplateRenderError",
    "TemplateRenderer",
    "TemplateResponse",
    "StreamingTemplateResponse",
    "TemplateSyntaxError",
    "UndefinedVariableError",
    "apply_filters",
    "filter_date",
    "filter_default",
    "filter_escape",
    "filter_first",
    "filter_format",
    "filter_join",
    "filter_json",
    "filter_last",
    "filter_length",
    "filter_lower",
    "filter_reverse",
    "filter_safe",
    "filter_sort",
    "filter_title",
    "filter_trim",
    "filter_upper",
    "render_template",
    "render_template_stream",
    "safe",
    "setup_templating",
    "teardown_templating",
]
