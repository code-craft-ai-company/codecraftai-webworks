"""
    Mako template engine adapter module.
    
    This module provides the MakoAdapter class, a concrete implementation
    of the TemplateEngine abstract base class that wraps the Mako template
    engine. It provides template rendering, filter and global registration,
    auto-escaping configuration, and cache management through the unified
    template engine interface.
    
    The adapter creates and manages a Mako TemplateLookup with configurable
    options for template directories, auto-escaping, module directory for
    compiled templates, encoding, and default filters.
"""

from typing import Any, Callable, Dict, Optional

from mako import exceptions as mako_exceptions
from mako.lookup import TemplateLookup
from mako.template import Template

from automojo.webworks.templating.engine import TemplateEngine
from automojo.webworks.templating.exceptions import (
    TemplateError,
    TemplateNotFoundError,
)


class MakoAdapter(TemplateEngine):
    """
        Template engine adapter for Mako.
        
        Wraps the Mako template engine to provide template rendering
        through the unified TemplateEngine interface. Supports configuration
        of template directories, auto-escaping, compiled module directory,
        encoding, and default filters.
        
        The adapter creates a Mako TemplateLookup configured to search
        the specified template directories. Auto-escaping is enabled by
        default using Mako's default_filters mechanism with the 'h' filter.
        
        Global variables are stored internally and injected into the
        rendering context on each render call. Custom filters are stored
        and made available to templates via Mako's imports mechanism.
        
        Example usage::
        
            adapter = MakoAdapter(
                template_dirs=["/path/to/templates"],
                auto_escape=True,
            )
            
            output = adapter.render("index.html", {"title": "Home"})
    """

    def __init__(
        self,
        template_dirs: list,
        auto_escape: bool = True,
        module_directory: Optional[str] = None,
        encoding: str = "utf-8",
        default_filters: Optional[list] = None
    ):
        """
            Construct a MakoAdapter.
            
            Creates a Mako TemplateLookup configured with the specified options.
            The lookup searches the provided template directories for template
            files.
            
            When auto_escape is True and no explicit default_filters are
            provided, the 'h' filter is applied by default to escape HTML
            special characters in all expression output.
            
            :param template_dirs: List of directories to search for templates.
            :param auto_escape: Enable auto-escaping (default True).
            :param module_directory: Directory for compiled template modules.
            :param encoding: Template file encoding.
            :param default_filters: Default filters to apply to expressions.
                When None and auto_escape is True, defaults to ['h'].
        """
        self._template_dirs = list(template_dirs)
        self._auto_escape = auto_escape
        self._module_directory = module_directory
        self._encoding = encoding
        self._globals = {}
        self._filters = {}

        if default_filters is not None:
            self._default_filters = list(default_filters)
        elif auto_escape:
            self._default_filters = ["h"]
        else:
            self._default_filters = ["str"]

        self._lookup = self._create_lookup()
        return

    def render(
        self,
        template_name: str,
        context: Dict[str, Any]
    ) -> str:
        """
            Render a Mako template with the given context.
            
            Loads the template by name from the configured directories and
            renders it with the provided context variables. Global variables
            are merged into the context before rendering.
            
            :param template_name: Name/path of the template file.
            :param context: Dictionary of variables to pass to the template.
            
            :returns: Rendered template as a string.
            
            :raises TemplateNotFoundError: If template file does not exist.
            :raises TemplateError: If template contains syntax errors or
                rendering fails.
        """
        try:
            template = self._lookup.get_template(template_name)
        except mako_exceptions.TopLevelLookupException as exc:
            raise TemplateNotFoundError(
                template_name=template_name,
                searched_paths=self._template_dirs
            ) from exc

        merged_context = dict(self._globals)
        merged_context.update(context)

        try:
            return template.render(**merged_context)
        except Exception as exc:
            if isinstance(exc, (TemplateNotFoundError, TemplateError)):
                raise
            raise TemplateError(
                f"Render error in '{template_name}': {exc}"
            ) from exc

    def render_string(
        self,
        template_source: str,
        context: Dict[str, Any]
    ) -> str:
        """
            Render a Mako template string directly.
            
            Compiles the provided template source code and renders it with
            the given context variables. Global variables are merged into
            the context before rendering.
            
            :param template_source: Template source code as a string.
            :param context: Dictionary of variables to pass to the template.
            
            :returns: Rendered template as a string.
            
            :raises TemplateError: If template contains syntax errors or
                rendering fails.
        """
        try:
            template = Template(
                text=template_source,
                default_filters=self._default_filters,
                input_encoding=self._encoding,
                lookup=self._lookup,
            )
        except mako_exceptions.SyntaxException as exc:
            raise TemplateError(
                f"Syntax error in template string: {exc}"
            ) from exc

        merged_context = dict(self._globals)
        merged_context.update(context)

        try:
            return template.render(**merged_context)
        except Exception as exc:
            if isinstance(exc, (TemplateNotFoundError, TemplateError)):
                raise
            raise TemplateError(
                f"Render error in template string: {exc}"
            ) from exc

    def add_filter(
        self,
        name: str,
        func: Callable[..., Any]
    ) -> None:
        """
            Register a Mako filter.
            
            Stores a custom filter function that can be used in Mako
            templates. The filter is made available in the template
            namespace and can be applied using Mako's filter syntax.
            
            :param name: Filter name to use in templates.
            :param func: Filter function that transforms values.
        """
        self._filters[name] = func
        return

    def add_global(
        self,
        name: str,
        value: Any
    ) -> None:
        """
            Register a Mako global variable or function.
            
            Stores a global variable or function that is automatically
            injected into the rendering context for all templates. The
            global becomes available in all templates without needing
            to pass it in the context.
            
            :param name: Global name to use in templates.
            :param value: Global value (can be callable).
        """
        self._globals[name] = value
        return

    def clear_cache(self) -> None:
        """
            Clear the Mako template cache.
            
            Recreates the TemplateLookup to clear all cached templates,
            forcing them to be reloaded and recompiled on next access.
        """
        self._lookup = self._create_lookup()
        return

    def _create_lookup(self) -> TemplateLookup:
        """
            Create and configure a Mako TemplateLookup.
            
            Builds a TemplateLookup with the configured options including
            template directories, module directory, encoding, and default
            filters for auto-escaping.
            
            :returns: Configured Mako TemplateLookup instance.
        """
        lookup = TemplateLookup(
            directories=self._template_dirs,
            module_directory=self._module_directory,
            input_encoding=self._encoding,
            default_filters=self._default_filters,
        )

        return lookup
