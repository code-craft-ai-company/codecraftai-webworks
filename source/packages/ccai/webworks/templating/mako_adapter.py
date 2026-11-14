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
    
    Templates located by a TemplateLoader are compiled with
    :meth:`MakoAdapter.compile_template`; the compiled Mako template can be
    held in a TemplateCache and rendered repeatedly with
    :meth:`MakoAdapter.render_compiled`.
"""

import os
import re

from typing import Any, Callable, Dict, Optional

from mako import exceptions as mako_exceptions
from mako import filters as mako_filters
from mako.lookup import TemplateLookup
from mako.template import Template

from ccai.errors.exceptions import ConfigurationError, SemanticError

from ccai.webworks.templating.engine import TemplateEngine
from ccai.webworks.templating.exceptions import (
    TemplateConfigurationError,
    TemplateError,
    TemplateNotFoundError,
    TemplateRenderError,
    TemplateSyntaxError,
    UndefinedVariableError,
)


# The name errors report for a template rendered from a string, which has
# no file name of its own.
STRING_TEMPLATE_NAME = "<string>"

# With ``strict_undefined`` Mako reports an undefined name as
# "'name' is not defined".
UNDEFINED_NAME_PATTERN = re.compile(r"^'(?P<name>[^']+)' is not defined")

# The options the adapter sets on the Mako TemplateLookup itself, from its
# own named parameters. They cannot be given a second time as an engine option.
RESERVED_LOOKUP_OPTIONS = (
    "directories",
    "input_encoding",
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
        the same way: Mako resolves a filter name in an expression such as
        ``${value | myfilter}`` from the rendering context, so every
        registered filter is merged into the context of each render, below
        the globals and the caller's variables. A context variable with the
        same name as a filter therefore hides that filter for the render,
        and a template that reads a name it was not given finds the filter
        registered under that name instead of Mako's ``UNDEFINED``.
        
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
        default_filters: Optional[list] = None,
        **lookup_options: Any
    ):
        """
            Construct a MakoAdapter.
            
            Creates a Mako TemplateLookup configured with the specified options.
            The lookup searches the provided template directories for template
            files.
            
            When auto_escape is True and no explicit default_filters are
            provided, the 'h' filter is applied by default to escape HTML
            special characters in all expression output.
            
            Any other keyword argument is a native Mako option and is passed
            to :class:`mako.lookup.TemplateLookup` unchanged, for example
            ``strict_undefined=True``. This is how
            ``TemplateConfig.engine_options`` reaches Mako.
            
            :param template_dirs: List of directories to search for templates.
            :param auto_escape: Enable auto-escaping (default True).
            :param module_directory: Directory for compiled template modules.
            :param encoding: Template file encoding.
            :param default_filters: Default filters to apply to expressions.
                When None and auto_escape is True, defaults to ['h'].
            :param lookup_options: Native :class:`mako.lookup.TemplateLookup`
                options, passed through as given.
            
            :raises TemplateConfigurationError: If a lookup option names
                something the adapter configures from its own parameters, or
                Mako does not accept the options.
        """
        for option_name in lookup_options:
            if option_name in RESERVED_LOOKUP_OPTIONS:
                errmsg_lines = [
                    f"The Mako lookup option '{option_name}' cannot be passed as an engine option.",
                    "The MakoAdapter sets it from its own parameters: 'template_dirs' and 'encoding'.",
                ]
                errmsg = os.linesep.join(errmsg_lines)
                raise TemplateConfigurationError(errmsg, field_name="engine_options")
        
        self._template_dirs = list(template_dirs)
        self._auto_escape = auto_escape
        self._module_directory = module_directory
        self._encoding = encoding
        self._globals = {}
        self._filters = {}
        self._lookup_options = dict(lookup_options)

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
        except (mako_exceptions.SyntaxException, mako_exceptions.CompileException) as exc:
            syntax_error = self._translate_syntax_error(exc, template_name)
            raise syntax_error from exc

        merged_context = self._merge_context(context)

        try:
            return template.render(**merged_context)
        except TemplateError:
            raise
        except Exception as exc:
            render_error = self._translate_render_error(exc, template_name)
            raise render_error from exc

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
                lookup=self._lookup,
                **self._lookup.template_args
            )
        except (mako_exceptions.SyntaxException, mako_exceptions.CompileException) as exc:
            syntax_error = self._translate_syntax_error(exc, STRING_TEMPLATE_NAME)
            raise syntax_error from exc

        merged_context = self._merge_context(context)

        try:
            return template.render(**merged_context)
        except TemplateError:
            raise
        except Exception as exc:
            render_error = self._translate_render_error(exc, STRING_TEMPLATE_NAME)
            raise render_error from exc

    def compile_template(
        self,
        template_source: str,
        template_name: str,
        filename: Optional[str] = None
    ) -> Template:
        """
            Compile template source that was loaded by a TemplateLoader.
            
            The source is compiled with ``template_name`` as its URI and with
            this adapter's lookup, default filters and encoding, so the result
            behaves like a template the lookup loaded by name: ``inherit`` /
            ``include`` / ``namespace`` references resolve relative to it.
            
            :param template_source: Template source code read by the loader.
            :param template_name: Resolved template name, used as the URI.
            :param filename: Full filesystem path of the template, if known.
            
            :returns: The compiled Mako template.
            
            :raises TemplateError: If the template contains syntax errors.
        """
        try:
            template = Template(
                text=template_source,
                uri=template_name,
                filename=filename,
                lookup=self._lookup,
                **self._lookup.template_args
            )
        except (mako_exceptions.SyntaxException, mako_exceptions.CompileException) as exc:
            syntax_error = self._translate_syntax_error(exc, template_name)
            raise syntax_error from exc
        
        return template
    
    def render_compiled(
        self,
        compiled_template: Template,
        context: Dict[str, Any]
    ) -> str:
        """
            Render a template returned by :meth:`compile_template`.
            
            Global variables are merged into the context before rendering,
            as :meth:`render` does.
            
            :param compiled_template: The compiled Mako template.
            :param context: Dictionary of variables to pass to the template.
            
            :returns: Rendered template as a string.
            
            :raises TemplateError: If rendering fails, including when a
                template it inherits or includes cannot be located (the
                message names the missing URI), as :meth:`render` reports it.
        """
        merged_context = self._merge_context(context)
        
        try:
            rendered = compiled_template.render(**merged_context)
        except (TemplateError, SemanticError, ConfigurationError):
            raise
        except Exception as exc:
            render_error = self._translate_render_error(exc, compiled_template.uri)
            raise render_error from exc
        
        return rendered
    
    def add_filter(
        self,
        name: str,
        func: Callable[..., Any]
    ) -> None:
        """
            Register a Mako filter.
            
            Stores a custom filter function that can be used in Mako
            templates with the filter syntax (``${value | name}``). Mako
            looks the name up in the rendering context, so the filter is
            merged into the context of every render, below the globals and
            the variables the caller passes.
            
            :param name: Filter name to use in templates.
            :param func: Filter function that transforms values.
        """
        self._filters[name] = func
        return

    def has_filter(self, name: str) -> bool:
        """
            Check whether a filter name is already available to templates.
            
            True for Mako's own expression filters (``h``, ``u``, ``x``,
            ``trim``, ``entity``, ``n`` and so on), which Mako resolves at
            compile time before it looks at the context, and for every
            filter added with :meth:`add_filter`.
            
            :param name: Filter name as it is used in templates.
            
            :returns: True if a filter with this name is available.
        """
        is_present = name in self._filters or name in mako_filters.DEFAULT_ESCAPES
        return is_present

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
        try:
            lookup = TemplateLookup(
                directories=self._template_dirs,
                module_directory=self._module_directory,
                input_encoding=self._encoding,
                default_filters=self._default_filters,
                **self._lookup_options
            )
        except TypeError as exc:
            option_names = ", ".join(sorted(self._lookup_options))
            errmsg_lines = [
                "Mako did not accept the engine options given to the MakoAdapter.",
                f"OPTIONS: {option_names}",
                f"REASON: {exc}",
            ]
            errmsg = os.linesep.join(errmsg_lines)
            raise TemplateConfigurationError(errmsg, field_name="engine_options") from exc

        return lookup

    def _merge_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
            Build the context a Mako template is rendered with.
            
            Registered filters come first, then globals, then the caller's
            variables, so a global hides a filter of the same name and a
            caller's variable hides both.
            
            :param context: Dictionary of variables passed by the caller.
            
            :returns: The merged rendering context.
        """
        merged_context: Dict[str, Any] = dict(self._filters)
        merged_context.update(self._globals)
        merged_context.update(context)
        return merged_context

    def _translate_syntax_error(self, exc: Exception, template_name: str) -> TemplateSyntaxError:
        """
            Map a Mako syntax or compile exception to a TemplateSyntaxError.
            
            :param exc: The Mako SyntaxException or CompileException.
            :param template_name: Name of the template being compiled.
            
            :returns: The TemplateSyntaxError to raise in its place.
        """
        line_number = getattr(exc, "lineno", None)
        
        syntax_error = TemplateSyntaxError(
            template_name=template_name,
            line_number=line_number,
            message=str(exc)
        )
        return syntax_error

    def _translate_render_error(self, exc: Exception, template_name: str) -> TemplateError:
        """
            Map an exception raised while rendering to a templating exception.
            
            An undefined name reported by a ``strict_undefined`` template
            becomes :class:`UndefinedVariableError`. Everything else,
            including an ordinary Python exception raised by code the
            template runs and a missing inherited or included template,
            becomes :class:`TemplateRenderError` with the template name
            and, when Mako can map the traceback to it, the template line.
            
            The caller raises the result ``from`` the original exception, so
            the original stays available as ``__cause__``.
            
            :param exc: The exception that was raised.
            :param template_name: Name of the template being rendered.
            
            :returns: The templating exception to raise in its place.
        """
        translated_error: TemplateError
        
        line_number = self._find_template_line(exc)
        
        variable_name = None
        if isinstance(exc, NameError):
            undefined_match = UNDEFINED_NAME_PATTERN.match(str(exc))
            if undefined_match is not None:
                variable_name = undefined_match.group("name")
        
        if variable_name is not None:
            translated_error = UndefinedVariableError(
                variable_name=variable_name,
                template_name=template_name,
                line_number=line_number
            )
        else:
            translated_error = TemplateRenderError(
                template_name=template_name,
                message=f"{type(exc).__name__}: {exc}",
                line_number=line_number
            )
        
        return translated_error

    def _find_template_line(self, exc: Exception) -> Optional[int]:
        """
            Find the template line a rendering exception came from.
            
            Mako's RichTraceback maps the frames of compiled template
            modules back to template source lines; the innermost frame that
            maps is the template line that failed.
            
            :param exc: The exception raised while rendering.
            
            :returns: The template line number, or None when no frame of
                the traceback belongs to a template.
        """
        line_number = None
        
        rich_traceback = mako_exceptions.RichTraceback(error=exc, traceback=exc.__traceback__)
        
        for record in rich_traceback.records:
            # (filename, lineno, function, line,
            #  template_filename, template_lineno, template_line, template_source)
            template_lineno = record[5]
            if template_lineno is not None:
                line_number = template_lineno
        
        return line_number
