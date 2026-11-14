"""
    Jinja2 template engine adapter module.
    
    This module provides the Jinja2Adapter class, a concrete implementation
    of the TemplateEngine abstract base class that wraps the Jinja2 template
    engine. It provides template rendering, filter and global registration,
    auto-escaping configuration, and cache management through the unified
    template engine interface.
    
    The adapter creates and manages a Jinja2 Environment with configurable
    options for template directories, auto-escaping, caching, undefined
    variable behavior, and extensions.
    
    Templates located by a TemplateLoader are compiled with
    :meth:`Jinja2Adapter.compile_template` into a
    :class:`Jinja2CompiledTemplate`, which a TemplateCache can hold and
    :meth:`Jinja2Adapter.render_compiled` (and its async and streaming
    variants) can render any number of times.
"""

import os
import re

from types import TracebackType
from typing import Any, Callable, Dict, Iterator, Optional

import jinja2

from ccai.webworks.templating.engine import TemplateEngine
from ccai.webworks.templating.exceptions import (
    TemplateConfigurationError,
    TemplateError,
    TemplateFilterNotFoundError,
    TemplateNotFoundError,
    TemplateRenderError,
    TemplateSyntaxError,
    UndefinedVariableError,
)


# The name errors report for a template rendered from a string, which has
# no file name of its own.
STRING_TEMPLATE_NAME = "<string>"

# Jinja2 reports an undefined name as "'name' is undefined" and a missing
# filter as "No filter named 'name'." (optionally followed by a suggestion).
UNDEFINED_NAME_PATTERN = re.compile(r"^'(?P<name>[^']+)' is undefined")
MISSING_FILTER_PATTERN = re.compile(r"^No filter named '(?P<name>[^']+)'")

# The options the adapter sets on the Jinja2 Environment itself, from its own
# named parameters. They cannot be given a second time as an engine option.
RESERVED_ENVIRONMENT_OPTIONS = (
    "loader",
    "autoescape",
    "cache_size",
    "auto_reload",
    "undefined",
    "extensions",
    "enable_async",
)


class Jinja2CompiledTemplate:
    """
        A template compiled by a :class:`Jinja2Adapter` from loaded source.
        
        Holds the compiled Jinja2 template for synchronous and streaming
        rendering, plus the source so an async-enabled variant can be
        compiled the first time the template is rendered asynchronously
        (Jinja2 compiles async templates differently). The async variant
        is kept on this object, so a cached compiled template is reused
        for async renders as well.
        
        :ivar template_name: The resolved template name.
        :ivar filename: The template's filesystem path, if known.
        :ivar source: The template source code.
        :ivar template: The compiled synchronous Jinja2 template.
        :ivar async_template: The compiled async Jinja2 template, or None
            until the template is first rendered asynchronously.
    """
    
    def __init__(
        self,
        template_name: str,
        filename: Optional[str],
        source: str,
        template: jinja2.Template
    ) -> None:
        """
            Construct a Jinja2CompiledTemplate.
            
            :param template_name: The resolved template name.
            :param filename: The template's filesystem path, if known.
            :param source: The template source code.
            :param template: The compiled synchronous Jinja2 template.
        """
        self.template_name = template_name
        self.filename = filename
        self.source = source
        self.template = template
        self.async_template: Optional[jinja2.Template] = None
        return


class Jinja2Adapter(TemplateEngine):
    """
        Template engine adapter for Jinja2.
        
        Wraps the Jinja2 template engine to provide template rendering
        through the unified TemplateEngine interface. Supports configuration
        of template directories, auto-escaping, caching, undefined variable
        behavior, and Jinja2 extensions.
        
        The adapter creates a Jinja2 Environment with a FileSystemLoader
        configured to search the specified template directories. Auto-escaping
        is enabled by default for HTML and XML file extensions.
        
        Example usage::
        
            adapter = Jinja2Adapter(
                template_dirs=["/path/to/templates"],
                auto_escape=True,
                cache_size=400,
            )
            
            output = adapter.render("index.html", {"title": "Home"})
    """

    def __init__(
        self,
        template_dirs: list,
        auto_escape: bool = True,
        cache_size: int = 400,
        auto_reload: bool = False,
        encoding: str = "utf-8",
        undefined_behavior: str = "silent",
        extensions: Optional[list] = None,
        **environment_options: Any
    ):
        """
            Construct a Jinja2Adapter.
            
            Creates a Jinja2 Environment configured with the specified options.
            The environment uses a FileSystemLoader to search the provided
            template directories for template files.
            
            Any other keyword argument is a native Jinja2 option and is
            passed to :class:`jinja2.Environment` unchanged, for example
            ``trim_blocks=True`` or ``lstrip_blocks=True``. This is how
            ``TemplateConfig.engine_options`` reaches Jinja2.
            
            :param template_dirs: List of directories to search for templates.
            :param auto_escape: Enable auto-escaping (default True).
            :param cache_size: Maximum number of cached templates.
            :param auto_reload: Reload templates when modified (debug mode).
            :param encoding: Template file encoding.
            :param undefined_behavior: How to handle undefined variables.
                Supported values: "silent", "strict", "debug".
            :param extensions: List of Jinja2 extensions to enable.
            :param environment_options: Native :class:`jinja2.Environment`
                options, passed through as given.
            
            :raises TemplateConfigurationError: If an environment option
                names something the adapter configures from its own
                parameters, or Jinja2 does not accept the options.
        """
        for option_name in environment_options:
            if option_name in RESERVED_ENVIRONMENT_OPTIONS:
                errmsg_lines = [
                    f"The Jinja2 environment option '{option_name}' cannot be passed as an engine option.",
                    "The Jinja2Adapter sets it from its own parameters: 'template_dirs', 'auto_escape',",
                    "'cache_size', 'auto_reload', 'undefined_behavior' and 'extensions'.",
                ]
                errmsg = os.linesep.join(errmsg_lines)
                raise TemplateConfigurationError(errmsg, field_name="engine_options")
        
        self._template_dirs = list(template_dirs)
        self._auto_escape = auto_escape
        self._cache_size = cache_size
        self._auto_reload = auto_reload
        self._encoding = encoding
        self._undefined_behavior = undefined_behavior
        self._extensions = extensions or []
        self._environment_options = dict(environment_options)
        
        self._environment = self._create_environment()
        
        # Lazy-loaded async environment for render_async
        self._async_environment = None
        return
    
    @property
    def _async_env(self) -> jinja2.Environment:
        """
            Get the async Jinja2 Environment, creating it lazily on first access.
            
            Copies any filters and globals that were registered on the sync
            environment so the async environment stays in sync.
            
            :returns: Async-enabled Jinja2 Environment instance.
        """
        if self._async_environment is None:
            self._async_environment = self._create_environment(enable_async=True)
            # Copy custom filters and globals from the sync environment
            self._async_environment.filters.update(self._environment.filters)
            self._async_environment.globals.update(self._environment.globals)
        return self._async_environment
    
    def render(
        self,
        template_name: str,
        context: Dict[str, Any]
    ) -> str:
        """
            Render a Jinja2 template with the given context.
            
            Loads the template by name from the configured directories and
            renders it with the provided context variables.
            
            :param template_name: Name/path of the template file.
            :param context: Dictionary of variables to pass to the template.
            
            :returns: Rendered template as a string.
            
            :raises TemplateNotFoundError: If template file does not exist.
            :raises TemplateError: If template contains syntax errors or
                rendering fails.
        """
        try:
            template = self._environment.get_template(template_name)
            return template.render(**context)
        except TemplateError:
            raise
        except Exception as exc:
            translated_error = self._translate_error(exc, template_name)
            raise translated_error from exc
    
    def render_string(
        self,
        template_source: str,
        context: Dict[str, Any]
    ) -> str:
        """
            Render a Jinja2 template string directly.
            
            Compiles the provided template source code and renders it with
            the given context variables.
            
            :param template_source: Template source code as a string.
            :param context: Dictionary of variables to pass to the template.
            
            :returns: Rendered template as a string.
            
            :raises TemplateError: If template contains syntax errors or
                rendering fails.
        """
        try:
            template = self._environment.from_string(template_source)
            return template.render(**context)
        except TemplateError:
            raise
        except Exception as exc:
            translated_error = self._translate_error(exc, STRING_TEMPLATE_NAME)
            raise translated_error from exc

    async def render_async(
        self,
        template_name: str,
        context: Dict[str, Any]
    ) -> str:
        """
            Render a Jinja2 template asynchronously.
            
            Uses Jinja2's async rendering support with an async-enabled
            environment for true asynchronous template rendering.
            
            :param template_name: Name/path of the template file.
            :param context: Dictionary of variables to pass to the template.
            
            :returns: Rendered template as a string.
            
            :raises TemplateNotFoundError: If template file does not exist.
            :raises TemplateError: If template contains syntax errors or
                rendering fails.
        """
        try:
            template = self._async_env.get_template(template_name)
            return await template.render_async(**context)
        except TemplateError:
            raise
        except Exception as exc:
            translated_error = self._translate_error(exc, template_name)
            raise translated_error from exc
    
    def render_stream(
        self,
        template_name: str,
        context: Dict[str, Any]
    ) -> Iterator[str]:
        """
            Render a Jinja2 template as a stream of chunks.
            
            Uses Jinja2's generate() method to produce template output
            incrementally, which is useful for large templates.
            
            :param template_name: Name/path of the template file.
            :param context: Dictionary of variables to pass to the template.
            
            :yields: Chunks of rendered template output.
            
            :raises TemplateNotFoundError: If template file does not exist.
            :raises TemplateError: If template contains syntax errors or
                rendering fails.
        """
        try:
            template = self._environment.get_template(template_name)
            for chunk in template.generate(**context):
                yield chunk
        except TemplateError:
            raise
        except Exception as exc:
            translated_error = self._translate_error(exc, template_name)
            raise translated_error from exc
    
    def compile_template(
        self,
        template_source: str,
        template_name: str,
        filename: Optional[str] = None
    ) -> Jinja2CompiledTemplate:
        """
            Compile template source that was loaded by a TemplateLoader.
            
            The source is compiled under ``template_name`` so the result
            behaves like a template Jinja2 loaded by name itself: the
            per-extension auto-escaping applies (an ``.html`` template is
            escaped, a ``.txt`` template is not), error messages name the
            template, and ``extends`` / ``include`` references resolve
            through this adapter's environment.
            
            :param template_source: Template source code read by the loader.
            :param template_name: Resolved template name.
            :param filename: Full filesystem path of the template, if known.
            
            :returns: The compiled template.
            
            :raises TemplateError: If the template contains syntax errors.
        """
        try:
            template = self._compile_in_environment(
                environment=self._environment,
                template_source=template_source,
                template_name=template_name,
                filename=filename
            )
        except jinja2.TemplateError as exc:
            translated_error = self._translate_error(exc, template_name)
            raise translated_error from exc
        
        compiled_template = Jinja2CompiledTemplate(
            template_name=template_name,
            filename=filename,
            source=template_source,
            template=template
        )
        
        return compiled_template
    
    def render_compiled(
        self,
        compiled_template: Jinja2CompiledTemplate,
        context: Dict[str, Any]
    ) -> str:
        """
            Render a template returned by :meth:`compile_template`.
            
            :param compiled_template: The compiled template.
            :param context: Dictionary of variables to pass to the template.
            
            :returns: Rendered template as a string.
            
            :raises TemplateNotFoundError: If a template it extends or
                includes does not exist.
            :raises TemplateError: If rendering fails.
        """
        template_name = compiled_template.template_name
        
        try:
            rendered = compiled_template.template.render(**context)
        except TemplateError:
            raise
        except Exception as exc:
            translated_error = self._translate_error(exc, template_name)
            raise translated_error from exc
        
        return rendered
    
    async def render_compiled_async(
        self,
        compiled_template: Jinja2CompiledTemplate,
        context: Dict[str, Any]
    ) -> str:
        """
            Render a template returned by :meth:`compile_template` asynchronously.
            
            The first async render compiles an async-enabled variant of the
            template in the async environment (the same one
            :meth:`render_async` uses) and keeps it on ``compiled_template``
            for later async renders.
            
            :param compiled_template: The compiled template.
            :param context: Dictionary of variables to pass to the template.
            
            :returns: Rendered template as a string.
            
            :raises TemplateNotFoundError: If a template it extends or
                includes does not exist.
            :raises TemplateError: If compiling or rendering fails.
        """
        template_name = compiled_template.template_name
        
        try:
            if compiled_template.async_template is None:
                compiled_template.async_template = self._compile_in_environment(
                    environment=self._async_env,
                    template_source=compiled_template.source,
                    template_name=template_name,
                    filename=compiled_template.filename
                )
            rendered = await compiled_template.async_template.render_async(**context)
        except TemplateError:
            raise
        except Exception as exc:
            translated_error = self._translate_error(exc, template_name)
            raise translated_error from exc
        
        return rendered
    
    def render_compiled_stream(
        self,
        compiled_template: Jinja2CompiledTemplate,
        context: Dict[str, Any]
    ) -> Iterator[str]:
        """
            Render a template returned by :meth:`compile_template` as chunks.
            
            Uses Jinja2's generate() so output is produced incrementally.
            
            :param compiled_template: The compiled template.
            :param context: Dictionary of variables to pass to the template.
            
            :yields: Chunks of rendered template output.
            
            :raises TemplateNotFoundError: If a template it extends or
                includes does not exist.
            :raises TemplateError: If rendering fails.
        """
        template_name = compiled_template.template_name
        
        try:
            for chunk in compiled_template.template.generate(**context):
                yield chunk
        except TemplateError:
            raise
        except Exception as exc:
            translated_error = self._translate_error(exc, template_name)
            raise translated_error from exc
    
    def add_filter(
        self,
        name: str,
        func: Callable[..., Any]
    ) -> None:
        """
            Register a Jinja2 filter.
            
            Adds a custom filter function to the Jinja2 environment. The
            filter becomes available in templates using the pipe syntax
            (e.g., {{ value|filter_name }}).
            
            :param name: Filter name to use in templates.
            :param func: Filter function that transforms values.
        """
        self._environment.filters[name] = func
        if self._async_environment is not None:
            self._async_environment.filters[name] = func
        return
    
    def has_filter(self, name: str) -> bool:
        """
            Check whether the Jinja2 environment already has a filter.
            
            True for the filters Jinja2 ships (``escape``, ``default``,
            ``sort``, ``join`` and the rest) and for every filter added
            with :meth:`add_filter`.
            
            :param name: Filter name as it is used in templates.
            
            :returns: True if the environment has a filter with this name.
        """
        is_present = name in self._environment.filters
        return is_present
    
    def add_global(
        self,
        name: str,
        value: Any
    ) -> None:
        """
            Register a Jinja2 global variable or function.
            
            Adds a global variable or function to the Jinja2 environment.
            The global becomes available in all templates without needing
            to pass it in the context.
            
            :param name: Global name to use in templates.
            :param value: Global value (can be callable).
        """
        self._environment.globals[name] = value
        if self._async_environment is not None:
            self._async_environment.globals[name] = value
        return
    
    def clear_cache(self) -> None:
        """
            Clear the Jinja2 template cache.
            
            Removes all compiled templates from the Jinja2 environment
            cache (sync and async) and from the bytecode cache if one is
            configured, forcing them to be reloaded and recompiled on next
            access.
        """
        # Jinja2 keeps the templates it loaded by name (including the
        # targets of extends / include) in Environment.cache, which is
        # None when the environment was created with a cache size of 0.
        if self._environment.cache is not None:
            self._environment.cache.clear()
        if self._async_environment is not None:
            if self._async_environment.cache is not None:
                self._async_environment.cache.clear()
        
        # Also clear the bytecode cache if one is configured
        if self._environment.bytecode_cache is not None:
            self._environment.bytecode_cache.clear()
        if self._async_environment is not None and self._async_environment.bytecode_cache is not None:
            self._async_environment.bytecode_cache.clear()
        return
    
    def _create_environment(self, enable_async: bool = False) -> jinja2.Environment:
        """
            Create and configure a Jinja2 Environment.
            
            Builds a Jinja2 Environment with the configured options including
            template loader, auto-escaping, caching, undefined behavior, and
            extensions.
            
            :param enable_async: Enable async support in the environment.
            
            :returns: Configured Jinja2 Environment instance.
        """
        loader = jinja2.FileSystemLoader(
            searchpath=self._template_dirs,
            encoding=self._encoding
        )
        
        if self._auto_escape:
            autoescape_func = jinja2.select_autoescape(
                enabled_extensions=("html", "htm", "xml"),
                default_for_string=True,
                default=True
            )
        else:
            autoescape_func = False
        
        undefined_class = self._get_undefined_class(self._undefined_behavior)
        
        # cache_size is Jinja2's own compiled-template cache for templates it
        # loads by name (including extends/include targets); 0 disables it,
        # which is what a disabled TemplateConfig cache asks for.
        try:
            environment = jinja2.Environment(
                loader=loader,
                autoescape=autoescape_func,
                cache_size=self._cache_size,
                auto_reload=self._auto_reload,
                undefined=undefined_class,
                extensions=self._extensions,
                enable_async=enable_async,
                **self._environment_options
            )
        except TypeError as exc:
            option_names = ", ".join(sorted(self._environment_options))
            errmsg_lines = [
                "Jinja2 did not accept the engine options given to the Jinja2Adapter.",
                f"OPTIONS: {option_names}",
                f"REASON: {exc}",
            ]
            errmsg = os.linesep.join(errmsg_lines)
            raise TemplateConfigurationError(errmsg, field_name="engine_options") from exc
        
        return environment
    
    def _compile_in_environment(
        self,
        environment: jinja2.Environment,
        template_source: str,
        template_name: str,
        filename: Optional[str]
    ) -> jinja2.Template:
        """
            Compile template source into a template bound to an environment.
            
            This is what a Jinja2 loader does for a template it reads itself,
            so the result is named, auto-escaped per its extension, and
            resolves ``extends`` / ``include`` through ``environment``.
            
            :param environment: The environment to compile in (sync or async).
            :param template_source: Template source code.
            :param template_name: Resolved template name.
            :param filename: Full filesystem path of the template, if known.
            
            :returns: The compiled Jinja2 template.
            
            :raises jinja2.TemplateSyntaxError: If the source has syntax errors.
        """
        code = environment.compile(
            template_source,
            name=template_name,
            filename=filename
        )
        template_globals = environment.make_globals(None)
        template = environment.template_class.from_code(
            environment,
            code,
            template_globals,
            uptodate=None
        )
        return template
    
    def _translate_error(self, exc: Exception, template_name: str) -> TemplateError:
        """
            Map an exception raised while compiling or rendering a template
            to the templating exception that describes it.
            
            - A missing template becomes :class:`TemplateNotFoundError`.
            - A reference to an unknown filter becomes
              :class:`TemplateFilterNotFoundError`.
            - A syntax error becomes :class:`TemplateSyntaxError` with the
              template name and line number.
            - An undefined variable becomes :class:`UndefinedVariableError`
              in strict mode and :class:`TemplateRenderError` (naming the
              variable) otherwise.
            - Everything else, including an ordinary Python exception raised
              by code the template runs, becomes :class:`TemplateRenderError`
              with the template name and, when it can be found, the line.
            
            The caller raises the result ``from`` the original exception, so
            the original stays available as ``__cause__``.
            
            :param exc: The exception that was raised.
            :param template_name: Name of the template being processed.
            
            :returns: The templating exception to raise in its place.
        """
        translated_error: TemplateError
        
        if isinstance(exc, jinja2.TemplateNotFound):
            translated_error = TemplateNotFoundError(
                template_name=exc.name or template_name,
                searched_paths=self._template_dirs
            )
        
        elif isinstance(exc, jinja2.TemplateSyntaxError):
            error_template_name = exc.name or template_name
            error_message = exc.message or str(exc)
            
            filter_match = MISSING_FILTER_PATTERN.match(error_message)
            if filter_match is not None:
                available_filters = list(self._environment.filters.keys())
                translated_error = TemplateFilterNotFoundError(
                    filter_name=filter_match.group("name"),
                    available_filters=available_filters
                )
            else:
                translated_error = TemplateSyntaxError(
                    template_name=error_template_name,
                    line_number=exc.lineno,
                    message=error_message
                )
        
        elif isinstance(exc, jinja2.UndefinedError):
            error_message = exc.message or str(exc)
            error_template_name, line_number = self._find_template_frame(exc.__traceback__, template_name)
            
            variable_name = None
            undefined_match = UNDEFINED_NAME_PATTERN.match(error_message)
            if undefined_match is not None:
                variable_name = undefined_match.group("name")
            
            if self._undefined_behavior == "strict" and variable_name is not None:
                translated_error = UndefinedVariableError(
                    variable_name=variable_name,
                    template_name=error_template_name,
                    line_number=line_number
                )
            else:
                translated_error = TemplateRenderError(
                    template_name=error_template_name,
                    message=error_message,
                    variable_name=variable_name,
                    line_number=line_number
                )
        
        else:
            error_template_name, line_number = self._find_template_frame(exc.__traceback__, template_name)
            
            if isinstance(exc, jinja2.TemplateError):
                error_message = exc.message or str(exc)
            else:
                error_message = f"{type(exc).__name__}: {exc}"
            
            translated_error = TemplateRenderError(
                template_name=error_template_name,
                message=error_message,
                line_number=line_number
            )
        
        return translated_error
    
    def _find_template_frame(
        self,
        traceback: Optional[TracebackType],
        template_name: str
    ) -> tuple:
        """
            Find the template and line a rendering exception came from.
            
            Jinja2 rewrites the traceback of an exception raised during a
            render so the frames of compiled template code are replaced by
            frames that carry the template's file name and source line. The
            innermost such frame is the template line that failed, which may
            be in a parent or included template.
            
            :param traceback: The traceback of the exception.
            :param template_name: Name of the template that was rendered,
                used when the frame does not name a template.
            
            :returns: A ``(template_name, line_number)`` tuple. The line
                number is None when no template frame is found.
        """
        found_name = template_name
        found_line = None
        
        current = traceback
        while current is not None:
            frame_globals = current.tb_frame.f_globals
            
            # Jinja2 marks the frames it substitutes for template code.
            if "__jinja_exception__" in frame_globals:
                found_line = current.tb_lineno
                
                frame_file = frame_globals.get("__file__")
                if isinstance(frame_file, str) and frame_file not in ("<template>", "<unknown>"):
                    found_name = self._template_name_for_file(frame_file, template_name)
            
            current = current.tb_next
        
        return found_name, found_line
    
    def _template_name_for_file(self, filename: str, template_name: str) -> str:
        """
            Turn a template file path from a traceback into a template name.
            
            :param filename: File path recorded for a template frame.
            :param template_name: Name of the template that was rendered.
            
            :returns: The path relative to the template directory holding the
                file, or ``template_name`` when no directory holds it.
        """
        found_name = template_name
        
        for template_dir in self._template_dirs:
            directory_prefix = os.path.join(os.path.abspath(template_dir), "")
            absolute_filename = os.path.abspath(filename)
            
            if absolute_filename.startswith(directory_prefix):
                relative_name = absolute_filename[len(directory_prefix):]
                found_name = relative_name.replace(os.sep, "/")
                break
        
        return found_name
    
    def _get_undefined_class(self, behavior: str) -> type:
        """
            Get the Jinja2 Undefined class for the specified behavior.
            
            Maps the undefined behavior string to the corresponding Jinja2
            Undefined class:
            
            - "silent": jinja2.Undefined (returns empty string)
            - "strict": jinja2.StrictUndefined (raises UndefinedError)
            - "debug": jinja2.DebugUndefined (returns debug string)
            
            :param behavior: Undefined behavior mode.
            
            :returns: Jinja2 Undefined class.
        """
        behavior_map = {
            "silent": jinja2.Undefined,
            "strict": jinja2.StrictUndefined,
            "debug": jinja2.DebugUndefined,
        }
        
        return behavior_map.get(behavior, jinja2.Undefined)
