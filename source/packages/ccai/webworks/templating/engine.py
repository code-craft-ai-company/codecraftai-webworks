"""
    Template engine abstract base class module.
    
    This module defines the abstract interface for template engine adapters.
    The TemplateEngine class provides a unified interface for different template
    engines (Jinja2, Mako, etc.) enabling pluggable template rendering.
    
    Concrete implementations must implement the abstract methods:
    - render(): Render a template file with context
    - render_string(): Render a template string with context
    - add_filter(): Register a custom filter function
    - add_global(): Register a global variable or function
    - clear_cache(): Clear the template cache
    
    Default implementations are provided for:
    - render_async(): Asynchronous rendering (falls back to sync)
    - render_stream(): Streaming rendering (yields single chunk)
"""

from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, Iterator


class TemplateEngine(ABC):
    """
        Abstract base class for template engine adapters.
        
        Provides a unified interface for different template engines.
        Concrete implementations should wrap specific template engines
        (Jinja2, Mako, etc.) and implement the abstract methods.
        
        The class defines the core template rendering operations:
        - render(): Render a template file with context variables
        - render_string(): Render a template string directly
        - render_async(): Asynchronous template rendering
        - render_stream(): Streaming template rendering
        
        And template customization operations:
        - add_filter(): Register custom filter functions
        - add_global(): Register global variables/functions
        - clear_cache(): Clear compiled template cache
        
        Example:
            class MyTemplateEngine(TemplateEngine):
                def render(self, template_name, context):
                    # Implementation here
                    pass
                
                # ... implement other abstract methods
    """
    
    @abstractmethod
    def render(
        self,
        template_name: str,
        context: Dict[str, Any]
    ) -> str:
        """
            Render a template with the given context.
            
            Loads the template file by name and renders it with the provided
            context variables. The template is looked up in the configured
            template directories.
            
            :param template_name: Name/path of the template file.
            :param context: Dictionary of variables to pass to the template.
            
            :returns: Rendered template as a string.
            
            :raises TemplateNotFoundError: If template file does not exist.
            :raises TemplateSyntaxError: If template contains syntax errors.
            :raises TemplateRenderError: If rendering fails due to context errors.
            
            Example:
                output = engine.render("index.html", {"title": "Home"})
        """
        pass
    
    @abstractmethod
    def render_string(
        self,
        template_source: str,
        context: Dict[str, Any]
    ) -> str:
        """
            Render a template string directly.
            
            Compiles and renders the provided template source code with the
            given context variables. Useful for rendering templates that are
            not stored in files.
            
            :param template_source: Template source code as a string.
            :param context: Dictionary of variables to pass to the template.
            
            :returns: Rendered template as a string.
            
            :raises TemplateSyntaxError: If template contains syntax errors.
            :raises TemplateRenderError: If rendering fails due to context errors.
            
            Example:
                output = engine.render_string("Hello {{ name }}!", {"name": "World"})
        """
        pass
    
    async def render_async(
        self,
        template_name: str,
        context: Dict[str, Any]
    ) -> str:
        """
            Render a template asynchronously.
            
            Provides asynchronous template rendering for use in async contexts.
            The default implementation falls back to synchronous rendering.
            Subclasses may override to provide true async rendering if the
            underlying template engine supports it.
            
            :param template_name: Name/path of the template file.
            :param context: Dictionary of variables to pass to the template.
            
            :returns: Rendered template as a string.
            
            :raises TemplateNotFoundError: If template file does not exist.
            :raises TemplateSyntaxError: If template contains syntax errors.
            :raises TemplateRenderError: If rendering fails due to context errors.
            
            Example:
                output = await engine.render_async("index.html", {"title": "Home"})
        """
        # Default implementation falls back to sync render
        return self.render(template_name, context)
    
    def render_stream(
        self,
        template_name: str,
        context: Dict[str, Any]
    ) -> Iterator[str]:
        """
            Render a template as a stream of chunks.
            
            Provides streaming template rendering for large templates or
            when progressive output is desired. The default implementation
            yields the entire output as a single chunk. Subclasses may
            override to provide true streaming if the underlying template
            engine supports it.
            
            :param template_name: Name/path of the template file.
            :param context: Dictionary of variables to pass to the template.
            
            :yields: Chunks of rendered template output.
            
            :raises TemplateNotFoundError: If template file does not exist.
            :raises TemplateSyntaxError: If template contains syntax errors.
            :raises TemplateRenderError: If rendering fails due to context errors.
            
            Example:
                for chunk in engine.render_stream("large.html", context):
                    response.write(chunk)
        """
        # Default implementation yields entire output as single chunk
        yield self.render(template_name, context)
    
    @abstractmethod
    def add_filter(
        self,
        name: str,
        func: Callable[..., Any]
    ) -> None:
        """
            Register a custom filter function.
            
            Filters are functions that transform template variable values
            during rendering. They can be used in templates with the pipe
            syntax (e.g., {{ value|filter_name }}).
            
            :param name: Filter name to use in templates.
            :param func: Filter function that transforms values.
            
            Example:
                def uppercase(value):
                    return str(value).upper()
                
                engine.add_filter("uppercase", uppercase)
                # In template: {{ name|uppercase }}
        """
        pass
    
    @abstractmethod
    def add_global(
        self,
        name: str,
        value: Any
    ) -> None:
        """
            Register a global variable or function.
            
            Globals are variables or functions available in all templates
            without needing to pass them in the context. Useful for
            application-wide values or utility functions.
            
            :param name: Global name to use in templates.
            :param value: Global value (can be callable).
            
            Example:
                engine.add_global("app_name", "My Application")
                engine.add_global("now", datetime.now)
                # In template: {{ app_name }}, {{ now() }}
        """
        pass
    
    @abstractmethod
    def clear_cache(self) -> None:
        """
            Clear the template cache.
            
            Removes all compiled templates from the cache, forcing them
            to be reloaded and recompiled on next access. Useful during
            development when templates are being modified.
            
            Example:
                engine.clear_cache()
        """
        pass
