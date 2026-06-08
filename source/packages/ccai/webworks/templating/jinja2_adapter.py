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
"""

from typing import Any, Callable, Dict, Iterator, Optional

import jinja2

from ccai.webworks.templating.engine import TemplateEngine
from ccai.webworks.templating.exceptions import (
    TemplateError,
    TemplateNotFoundError,
)


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
        extensions: Optional[list] = None
    ):
        """
            Construct a Jinja2Adapter.
            
            Creates a Jinja2 Environment configured with the specified options.
            The environment uses a FileSystemLoader to search the provided
            template directories for template files.
            
            :param template_dirs: List of directories to search for templates.
            :param auto_escape: Enable auto-escaping (default True).
            :param cache_size: Maximum number of cached templates.
            :param auto_reload: Reload templates when modified (debug mode).
            :param encoding: Template file encoding.
            :param undefined_behavior: How to handle undefined variables.
                Supported values: "silent", "strict", "debug".
            :param extensions: List of Jinja2 extensions to enable.
        """
        self._template_dirs = list(template_dirs)
        self._auto_escape = auto_escape
        self._cache_size = cache_size
        self._auto_reload = auto_reload
        self._encoding = encoding
        self._undefined_behavior = undefined_behavior
        self._extensions = extensions or []
        
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
        except jinja2.TemplateNotFound as exc:
            raise TemplateNotFoundError(
                template_name=template_name,
                searched_paths=self._template_dirs
            ) from exc
        except jinja2.TemplateSyntaxError as exc:
            raise TemplateError(
                f"Syntax error in '{exc.name or template_name}' "
                f"at line {exc.lineno}: {exc.message}"
            ) from exc
        except jinja2.TemplateError as exc:
            raise TemplateError(
                f"Render error in '{template_name}': {exc}"
            ) from exc
    
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
        except jinja2.TemplateSyntaxError as exc:
            raise TemplateError(
                f"Syntax error in template string "
                f"at line {exc.lineno}: {exc.message}"
            ) from exc
        except jinja2.TemplateError as exc:
            raise TemplateError(
                f"Render error in template string: {exc}"
            ) from exc

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
        except jinja2.TemplateNotFound as exc:
            raise TemplateNotFoundError(
                template_name=template_name,
                searched_paths=self._template_dirs
            ) from exc
        except jinja2.TemplateSyntaxError as exc:
            raise TemplateError(
                f"Syntax error in '{exc.name or template_name}' "
                f"at line {exc.lineno}: {exc.message}"
            ) from exc
        except jinja2.TemplateError as exc:
            raise TemplateError(
                f"Render error in '{template_name}': {exc}"
            ) from exc
    
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
        except jinja2.TemplateNotFound as exc:
            raise TemplateNotFoundError(
                template_name=template_name,
                searched_paths=self._template_dirs
            ) from exc
        except jinja2.TemplateSyntaxError as exc:
            raise TemplateError(
                f"Syntax error in '{exc.name or template_name}' "
                f"at line {exc.lineno}: {exc.message}"
            ) from exc
        except jinja2.TemplateError as exc:
            raise TemplateError(
                f"Render error in '{template_name}': {exc}"
            ) from exc
    
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
            
            Removes all compiled templates from the Jinja2 bytecode cache,
            forcing them to be reloaded and recompiled on next access.
        """
        # Clear the internal Jinja2 cache by resetting the environment cache
        if hasattr(self._environment, '_cache'):
            self._environment._cache.clear()
        if self._async_environment is not None:
            if hasattr(self._async_environment, '_cache'):
                self._async_environment._cache.clear()
        
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
        
        environment = jinja2.Environment(
            loader=loader,
            autoescape=autoescape_func,
            auto_reload=self._auto_reload,
            undefined=undefined_class,
            extensions=self._extensions,
            enable_async=enable_async
        )
        
        return environment
    
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
