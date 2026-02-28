"""
    Web templating module.
    
    This module provides template engine integration and rendering capabilities
    for the web framework, enabling dynamic HTML generation with support for
    template inheritance, context passing, and security features like auto-escaping.
    
    The module provides a pluggable architecture supporting multiple template
    engines (Jinja2, Mako) through a unified interface.
"""

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
from automojo.webworks.templating.jinja2_adapter import Jinja2Adapter
from automojo.webworks.templating.mako_adapter import MakoAdapter
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
