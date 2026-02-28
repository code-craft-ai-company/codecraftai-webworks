"""
    Template renderer module.
    
    This module provides the TemplateRenderer class, a high-level rendering
    interface that coordinates template engines with context processors.
    The renderer wraps a TemplateEngine instance and adds context processor
    support, providing a convenient API for rendering templates with
    automatic context building.
    
    The TemplateRenderer handles:
    - Building the final context by merging context processor output,
      passed context, and keyword arguments
    - Delegating rendering to the underlying template engine
    - Supporting synchronous, asynchronous, string, and streaming rendering
    
    Context processors are functions that receive the current context
    dictionary and return additional variables to merge. They are applied
    before the passed context and keyword arguments, allowing overrides.
"""

from typing import Any, Callable, Dict, Iterator, Optional


from automojo.webworks.templating.engine import TemplateEngine


class TemplateRenderer:
    """
        High-level template rendering interface.
        
        Coordinates template loading, caching, and rendering by wrapping
        a TemplateEngine instance and adding context processor support.
        Context processors are functions that receive the current context
        and return additional variables to merge into every render call.
        
        The context building order is:
        1. Start with an empty dictionary
        2. Apply context processors (each receives current state, returns additions)
        3. Merge the passed context dictionary
        4. Merge keyword arguments (highest priority, overrides context)
        
        Example usage::
        
            from automojo.webworks.templating.jinja2_adapter import Jinja2Adapter
            
            engine = Jinja2Adapter(template_dirs=["/templates"])
            renderer = TemplateRenderer(engine)
            
            # Add a context processor
            renderer.add_context_processor(lambda ctx: {"year": 2024})
            
            # Render a template
            output = renderer.render("index.html", {"title": "Home"})
    """

    def __init__(
        self,
        engine: TemplateEngine,
        context_processors: Optional[list] = None
    ) -> None:
        """
            Construct a template renderer.
            
            :param engine: The template engine to use for rendering.
            :param context_processors: Optional list of context processor
                functions. Each processor is a callable that receives a
                context dictionary and returns a dictionary of additional
                variables to merge.
        """
        self._engine = engine
        self._context_processors: list = []
        
        if context_processors is not None:
            for processor in context_processors:
                self._context_processors.append(processor)
        
        return
    
    @property
    def engine(self) -> TemplateEngine:
        """
            Get the underlying template engine.
            
            :returns: The TemplateEngine instance used by this renderer.
        """
        return self._engine
    
    @property
    def context_processors(self) -> list:
        """
            Get the list of registered context processors.
            
            :returns: A copy of the context processors list.
        """
        return list(self._context_processors)
    
    def _build_context(
        self,
        context: Optional[Dict[str, Any]],
        kwargs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
            Build the final context by merging processor output, passed context,
            and keyword arguments.
            
            The merge order is:
            1. Start with an empty dictionary
            2. Apply each context processor in order (each receives the current
               state and returns additional variables to merge)
            3. Merge the passed context dictionary
            4. Merge keyword arguments (highest priority)
            
            :param context: Optional dictionary of variables passed by the caller.
            :param kwargs: Additional keyword arguments to merge with highest priority.
            
            :returns: The final merged context dictionary.
        """
        result: Dict[str, Any] = {}
        
        # Apply context processors
        for processor in self._context_processors:
            additional = processor(result)
            if additional is not None:
                result.update(additional)
        
        # Merge passed context
        if context is not None:
            result.update(context)
        
        # Merge kwargs (highest priority)
        if kwargs:
            result.update(kwargs)
        
        return result
    
    def render(
        self,
        template_name: str,
        context: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> str:
        """
            Render a template with context.
            
            Builds the final context by applying context processors, merging
            the passed context, and merging keyword arguments. Then delegates
            rendering to the underlying template engine.
            
            :param template_name: Name/path of the template file.
            :param context: Optional dictionary of variables.
            :param kwargs: Additional variables merged into context with
                highest priority.
            
            :returns: Rendered template as a string.
            
            :raises TemplateNotFoundError: If template file does not exist.
            :raises TemplateError: If template contains syntax errors or
                rendering fails.
        """
        merged_context = self._build_context(context, kwargs)
        return self._engine.render(template_name, merged_context)
    
    async def render_async(
        self,
        template_name: str,
        context: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> str:
        """
            Render a template asynchronously.
            
            Builds the final context and delegates to the engine's async
            rendering method.
            
            :param template_name: Name/path of the template file.
            :param context: Optional dictionary of variables.
            :param kwargs: Additional variables merged into context with
                highest priority.
            
            :returns: Rendered template as a string.
            
            :raises TemplateNotFoundError: If template file does not exist.
            :raises TemplateError: If template contains syntax errors or
                rendering fails.
        """
        merged_context = self._build_context(context, kwargs)
        return await self._engine.render_async(template_name, merged_context)
    
    def render_string(
        self,
        template_source: str,
        context: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> str:
        """
            Render a template string directly.
            
            Builds the final context and delegates to the engine's string
            rendering method.
            
            :param template_source: Template source code as a string.
            :param context: Optional dictionary of variables.
            :param kwargs: Additional variables merged into context with
                highest priority.
            
            :returns: Rendered template as a string.
            
            :raises TemplateError: If template contains syntax errors or
                rendering fails.
        """
        merged_context = self._build_context(context, kwargs)
        return self._engine.render_string(template_source, merged_context)
    
    def render_stream(
        self,
        template_name: str,
        context: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> Iterator[str]:
        """
            Render a template as a stream of chunks.
            
            Builds the final context and delegates to the engine's streaming
            rendering method.
            
            :param template_name: Name/path of the template file.
            :param context: Optional dictionary of variables.
            :param kwargs: Additional variables merged into context with
                highest priority.
            
            :yields: Chunks of rendered template output.
            
            :raises TemplateNotFoundError: If template file does not exist.
            :raises TemplateError: If template contains syntax errors or
                rendering fails.
        """
        merged_context = self._build_context(context, kwargs)
        return self._engine.render_stream(template_name, merged_context)
    
    def add_context_processor(
        self,
        processor: Callable[[Dict[str, Any]], Dict[str, Any]]
    ) -> None:
        """
            Add a context processor function.
            
            Context processors are functions that receive the current context
            dictionary and return a dictionary of additional variables to merge.
            Processors are applied in the order they are added, before the
            passed context and keyword arguments.
            
            :param processor: A callable that receives a context dictionary
                and returns a dictionary of additional variables.
        """
        self._context_processors.append(processor)
        return
