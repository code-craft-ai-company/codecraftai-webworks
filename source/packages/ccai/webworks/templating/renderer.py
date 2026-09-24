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
    - Locating templates with an optional TemplateLoader and keeping their
      compiled form in an optional TemplateCache
    - Delegating rendering to the underlying template engine
    - Supporting synchronous, asynchronous, string, and streaming rendering
    
    Context processors are functions that receive the current context
    dictionary and return additional variables to merge. They are applied
    before the passed context and keyword arguments, allowing overrides.
    
    When a TemplateLoader is supplied, rendering a template by name follows
    the flow ``template_name -> Loader -> Cache -> Engine``: the loader
    resolves the name (applying its recognized extensions and directory
    priorities), the cache is checked for a compiled template, and only on a
    miss is the source loaded and compiled by the engine and stored in the
    cache. Without a loader the renderer passes the template name straight
    to the engine, as it always has.
"""

import os

from typing import Any, Callable, Dict, Iterator, Optional

from ccai.webworks.templating.cache import TemplateCache
from ccai.webworks.templating.engine import TemplateEngine
from ccai.webworks.templating.exceptions import TemplateNotFoundError
from ccai.webworks.templating.loader import TemplateLoader


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
        
        Template loading and caching are optional. With a ``loader``, named
        templates are located and read by the loader and compiled by the
        engine (:meth:`TemplateEngine.compile_template`); with a ``cache`` as
        well, the compiled template is kept and reused by later renders until
        it is evicted or, in auto-reload mode, its file changes. ``extends`` /
        ``include`` references inside a template are resolved by the engine
        from its own configured directories.
        
        Example usage::
        
            from ccai.webworks.templating.jinja2_adapter import Jinja2Adapter
            
            engine = Jinja2Adapter(template_dirs=["/templates"])
            renderer = TemplateRenderer(
                engine,
                loader=TemplateLoader(directories=["/templates"]),
                cache=TemplateCache(max_size=400),
            )
            
            # Add a context processor
            renderer.add_context_processor(lambda ctx: {"year": 2024})
            
            # Render a template ("index" resolves to "index.html")
            output = renderer.render("index", {"title": "Home"})
    """

    def __init__(
        self,
        engine: TemplateEngine,
        context_processors: Optional[list] = None,
        loader: Optional[TemplateLoader] = None,
        cache: Optional[TemplateCache] = None
    ) -> None:
        """
            Construct a template renderer.
            
            :param engine: The template engine to use for rendering.
            :param context_processors: Optional list of context processor
                functions. Each processor is a callable that receives a
                context dictionary and returns a dictionary of additional
                variables to merge.
            :param loader: Optional TemplateLoader that locates and reads
                named templates. When None, template names are passed to
                the engine unchanged.
            :param cache: Optional TemplateCache that keeps templates the
                engine compiled from the loader's source. Requires a loader.
            
            :raises ValueError: If a cache is given without a loader.
        """
        if cache is not None and loader is None:
            errmsg_lines = [
                "A TemplateRenderer 'cache' requires a 'loader'.",
                "The cache holds templates the engine compiled from source the loader read, and it uses",
                "the loader's modification times to detect stale entries. Pass the TemplateLoader that",
                "locates the templates, or leave 'cache' as None.",
            ]
            errmsg = os.linesep.join(errmsg_lines)
            raise ValueError(errmsg)
        
        self._engine = engine
        self._context_processors: list = []
        self._loader = loader
        self._cache = cache
        
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
    def loader(self) -> Optional[TemplateLoader]:
        """
            Get the template loader that locates named templates.
            
            :returns: The TemplateLoader, or None when the engine locates
                templates by itself.
        """
        return self._loader
    
    @property
    def cache(self) -> Optional[TemplateCache]:
        """
            Get the cache holding compiled templates.
            
            :returns: The TemplateCache, or None when templates are not cached
                by the renderer.
        """
        return self._cache
    
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
    
    def _get_compiled_template(self, template_name: str) -> Any:
        """
            Get the compiled template for a name, using the loader and cache.
            
            The loader resolves the name (recognized extensions, directory
            priority). The cache is consulted with the template's current
            modification time, so an auto-reload cache drops a stale entry.
            On a miss the loader reads the source, the engine compiles it,
            and the result is stored in the cache.
            
            :param template_name: Name/path of the template.
            
            :returns: The compiled template, as returned by the engine's
                :meth:`TemplateEngine.compile_template`.
            
            :raises TemplateNotFoundError: If the loader finds no template.
            :raises TemplateError: If the template fails to compile.
        """
        loader = self._loader
        
        resolved_name = loader.resolve_name(template_name)
        if resolved_name is None:
            raise TemplateNotFoundError(
                template_name=template_name,
                searched_paths=loader.directories
            )
        
        template_mtime = loader.get_mtime(resolved_name)
        
        compiled_template = None
        if self._cache is not None:
            compiled_template = self._cache.get(resolved_name, mtime=template_mtime)
        
        if compiled_template is None:
            template_path = loader.get_path(resolved_name)
            template_source = loader.load(resolved_name)
            
            compiled_template = self._engine.compile_template(
                template_source,
                template_name=resolved_name,
                filename=template_path
            )
            
            if self._cache is not None:
                self._cache.set(resolved_name, compiled_template, mtime=template_mtime)
        
        return compiled_template
    
    def _render_stream_from_loader(
        self,
        template_name: str,
        merged_context: Dict[str, Any]
    ) -> Iterator[str]:
        """
            Stream a template located through the loader and cache.
            
            A generator, so the template is looked up when iteration starts,
            the same point at which an engine's own ``render_stream`` looks
            its template up.
            
            :param template_name: Name/path of the template.
            :param merged_context: The fully built rendering context.
            
            :yields: Chunks of rendered template output.
        """
        compiled_template = self._get_compiled_template(template_name)
        
        for chunk in self._engine.render_compiled_stream(compiled_template, merged_context):
            yield chunk
    
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
            rendering to the underlying template engine, through the loader
            and cache when the renderer has a loader.
            
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
        
        if self._loader is None:
            rendered = self._engine.render(template_name, merged_context)
        else:
            compiled_template = self._get_compiled_template(template_name)
            rendered = self._engine.render_compiled(compiled_template, merged_context)
        
        return rendered
    
    async def render_async(
        self,
        template_name: str,
        context: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> str:
        """
            Render a template asynchronously.
            
            Builds the final context and delegates to the engine's async
            rendering method, through the loader and cache when the renderer
            has a loader.
            
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
        
        if self._loader is None:
            rendered = await self._engine.render_async(template_name, merged_context)
        else:
            compiled_template = self._get_compiled_template(template_name)
            rendered = await self._engine.render_compiled_async(compiled_template, merged_context)
        
        return rendered
    
    def render_string(
        self,
        template_source: str,
        context: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> str:
        """
            Render a template string directly.
            
            Builds the final context and delegates to the engine's string
            rendering method. The loader and cache are not involved.
            
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
            rendering method, through the loader and cache when the renderer
            has a loader.
            
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
        
        if self._loader is None:
            chunks = self._engine.render_stream(template_name, merged_context)
        else:
            chunks = self._render_stream_from_loader(template_name, merged_context)
        
        return chunks
    
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
