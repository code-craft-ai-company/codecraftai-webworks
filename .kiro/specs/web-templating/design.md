# Design Document: Web Templating

## Overview

This design document describes the architecture and implementation approach for the Web Templating feature. The feature provides a pluggable template engine interface with built-in support for Jinja2 and Mako, enabling dynamic HTML generation with template inheritance, context passing, and security features.

Key design principles:
- Pluggable Architecture: Support multiple template engines through a unified interface
- Security by Default: Auto-escaping enabled by default to prevent XSS attacks
- Performance: Template caching and compilation for production efficiency
- Developer Experience: Clear error messages with line numbers and template context
- Framework Integration: Seamless integration with request/response handling

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       Web Templating Architecture                            │
│                                                                              │
│  Request Handler                                                             │
│         │                                                                    │
│         ▼                                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    TemplateRenderer                                  │    │
│  │  render(template_name, context) -> str                              │    │
│  │  render_async(template_name, context) -> str                        │    │
│  │  render_stream(template_name, context) -> Iterator[str]             │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│         │                                                                    │
│         ├──────────────────────┬──────────────────────┐                     │
│         ▼                      ▼                      ▼                     │
│  ┌───────────────┐      ┌───────────────┐      ┌───────────────┐           │
│  │TemplateEngine │      │TemplateLoader │      │TemplateCache  │           │
│  │ (Abstract)    │      │ - load()      │      │ - get()       │           │
│  │ - render()    │      │ - exists()    │      │ - set()       │           │
│  └───────────────┘      └───────────────┘      └───────────────┘           │
│         │                                                                    │
│         ├──────────────────────┬──────────────────────┐                     │
│         ▼                      ▼                      ▼                     │
│  ┌───────────────┐      ┌───────────────┐      ┌───────────────┐           │
│  │Jinja2Adapter  │      │ MakoAdapter   │      │ CustomAdapter │           │
│  └───────────────┘      └───────────────┘      └───────────────┘           │
└─────────────────────────────────────────────────────────────────────────────┘
```


```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Template Rendering Flow                              │
│                                                                              │
│  1. Handler calls render_template(name, **context)                          │
│  2. TemplateRenderer receives request                                        │
│  3. TemplateLoader locates template file                                     │
│  4. TemplateCache checks for compiled template                              │
│  5. If not cached, TemplateEngine compiles template                         │
│  6. TemplateContext merges globals + request context + passed context       │
│  7. Template rendered with merged context                                    │
│  8. Auto-escaping applied to output                                         │
│  9. Rendered string returned (or streamed)                                  │
│                                                                              │
│  template_name ──▶ Loader ──▶ Cache ──▶ Engine ──▶ Context ──▶ Output      │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                         Template Inheritance                                 │
│                                                                              │
│  base.html                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  <!DOCTYPE html>                                                     │    │
│  │  <html>                                                              │    │
│  │    <head>{% block head %}{% endblock %}</head>                      │    │
│  │    <body>{% block content %}{% endblock %}</body>                   │    │
│  │  </html>                                                             │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│         ▲                                                                    │
│         │ extends                                                            │
│  page.html                                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  {% extends "base.html" %}                                          │    │
│  │  {% block content %}                                                │    │
│  │    <h1>{{ title }}</h1>                                             │    │
│  │    {{ super() }}                                                    │    │
│  │  {% endblock %}                                                     │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Components and Interfaces

### TemplateEngine Abstract Base Class

```python
from abc import ABC, abstractmethod
from typing import Any, Dict, Iterator, Optional, Callable


class TemplateEngine(ABC):
    """
    Abstract base class for template engine adapters.
    
    Provides a unified interface for different template engines.
    """
    
    @abstractmethod
    def render(
        self,
        template_name: str,
        context: Dict[str, Any]
    ) -> str:
        """
        Render a template with the given context.
        
        Args:
            template_name: Name/path of the template file.
            context: Dictionary of variables to pass to the template.
        
        Returns:
            Rendered template as a string.
        
        Raises:
            TemplateNotFoundError: If template file does not exist.
            TemplateSyntaxError: If template contains syntax errors.
            TemplateRenderError: If rendering fails due to context errors.
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
        
        Args:
            template_source: Template source code as a string.
            context: Dictionary of variables to pass to the template.
        
        Returns:
            Rendered template as a string.
        """
        pass

    async def render_async(
        self,
        template_name: str,
        context: Dict[str, Any]
    ) -> str:
        """
        Render a template asynchronously.
        
        Args:
            template_name: Name/path of the template file.
            context: Dictionary of variables to pass to the template.
        
        Returns:
            Rendered template as a string.
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
        
        Args:
            template_name: Name/path of the template file.
            context: Dictionary of variables to pass to the template.
        
        Yields:
            Chunks of rendered template output.
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
        
        Args:
            name: Filter name to use in templates.
            func: Filter function.
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
        
        Args:
            name: Global name to use in templates.
            value: Global value (can be callable).
        """
        pass
    
    @abstractmethod
    def clear_cache(self) -> None:
        """Clear the template cache."""
        pass
```

### Jinja2Adapter Class

```python
class Jinja2Adapter(TemplateEngine):
    """
    Template engine adapter for Jinja2.
    """
    
    def __init__(
        self,
        template_dirs: list[str],
        auto_escape: bool = True,
        cache_size: int = 400,
        auto_reload: bool = False,
        encoding: str = "utf-8",
        undefined_behavior: str = "silent",
        extensions: Optional[list[str]] = None
    ):
        """
        Construct a Jinja2 adapter.
        
        Args:
            template_dirs: List of directories to search for templates.
            auto_escape: Enable auto-escaping (default True).
            cache_size: Maximum number of cached templates.
            auto_reload: Reload templates when modified (debug mode).
            encoding: Template file encoding.
            undefined_behavior: How to handle undefined variables.
            extensions: List of Jinja2 extensions to enable.
        """
        pass
    
    def render(
        self,
        template_name: str,
        context: Dict[str, Any]
    ) -> str:
        """Render a Jinja2 template."""
        pass
    
    def render_string(
        self,
        template_source: str,
        context: Dict[str, Any]
    ) -> str:
        """Render a Jinja2 template string."""
        pass

    async def render_async(
        self,
        template_name: str,
        context: Dict[str, Any]
    ) -> str:
        """Render a Jinja2 template asynchronously."""
        pass
    
    def render_stream(
        self,
        template_name: str,
        context: Dict[str, Any]
    ) -> Iterator[str]:
        """Render a Jinja2 template as a stream."""
        pass
    
    def add_filter(
        self,
        name: str,
        func: Callable[..., Any]
    ) -> None:
        """Register a Jinja2 filter."""
        pass
    
    def add_global(
        self,
        name: str,
        value: Any
    ) -> None:
        """Register a Jinja2 global."""
        pass
    
    def clear_cache(self) -> None:
        """Clear the Jinja2 template cache."""
        pass
    
    def _create_environment(self) -> "jinja2.Environment":
        """Create and configure the Jinja2 environment."""
        pass
    
    def _get_undefined_class(self, behavior: str) -> type:
        """Get the Jinja2 Undefined class for the specified behavior."""
        pass
```

### MakoAdapter Class

```python
class MakoAdapter(TemplateEngine):
    """
    Template engine adapter for Mako.
    """
    
    def __init__(
        self,
        template_dirs: list[str],
        auto_escape: bool = True,
        module_directory: Optional[str] = None,
        encoding: str = "utf-8",
        default_filters: Optional[list[str]] = None
    ):
        """
        Construct a Mako adapter.
        
        Args:
            template_dirs: List of directories to search for templates.
            auto_escape: Enable auto-escaping (default True).
            module_directory: Directory for compiled template modules.
            encoding: Template file encoding.
            default_filters: Default filters to apply to expressions.
        """
        pass
    
    def render(
        self,
        template_name: str,
        context: Dict[str, Any]
    ) -> str:
        """Render a Mako template."""
        pass
    
    def render_string(
        self,
        template_source: str,
        context: Dict[str, Any]
    ) -> str:
        """Render a Mako template string."""
        pass
    
    def add_filter(
        self,
        name: str,
        func: Callable[..., Any]
    ) -> None:
        """Register a Mako filter."""
        pass
    
    def add_global(
        self,
        name: str,
        value: Any
    ) -> None:
        """Register a Mako global."""
        pass
    
    def clear_cache(self) -> None:
        """Clear the Mako template cache."""
        pass
```

### TemplateRenderer Class

```python
class TemplateRenderer:
    """
    High-level template rendering interface.
    
    Coordinates template loading, caching, and rendering.
    """
    
    def __init__(
        self,
        engine: TemplateEngine,
        context_processors: Optional[list[Callable]] = None
    ):
        """
        Construct a template renderer.
        
        Args:
            engine: The template engine to use.
            context_processors: List of context processor functions.
        """
        pass
    
    def render(
        self,
        template_name: str,
        context: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> str:
        """
        Render a template with context.
        
        Args:
            template_name: Name/path of the template file.
            context: Dictionary of variables (optional).
            **kwargs: Additional variables merged into context.
        
        Returns:
            Rendered template as a string.
        """
        pass
    
    async def render_async(
        self,
        template_name: str,
        context: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> str:
        """
        Render a template asynchronously.
        
        Args:
            template_name: Name/path of the template file.
            context: Dictionary of variables (optional).
            **kwargs: Additional variables merged into context.
        
        Returns:
            Rendered template as a string.
        """
        pass
    
    def render_string(
        self,
        template_source: str,
        context: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> str:
        """
        Render a template string directly.
        
        Args:
            template_source: Template source code.
            context: Dictionary of variables (optional).
            **kwargs: Additional variables merged into context.
        
        Returns:
            Rendered template as a string.
        """
        pass
    
    def render_stream(
        self,
        template_name: str,
        context: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> Iterator[str]:
        """
        Render a template as a stream.
        
        Args:
            template_name: Name/path of the template file.
            context: Dictionary of variables (optional).
            **kwargs: Additional variables merged into context.
        
        Yields:
            Chunks of rendered template output.
        """
        pass
    
    def _build_context(
        self,
        context: Optional[Dict[str, Any]],
        kwargs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Build the final context by merging globals, processors, and passed context.
        """
        pass
    
    def add_context_processor(
        self,
        processor: Callable[[Dict[str, Any]], Dict[str, Any]]
    ) -> None:
        """
        Add a context processor function.
        
        Args:
            processor: Function that receives context and returns additional variables.
        """
        pass
```

### TemplateLoader Class

```python
class TemplateLoader:
    """
    Loads templates from configured directories.
    """
    
    def __init__(
        self,
        directories: list[str],
        extensions: Optional[list[str]] = None,
        encoding: str = "utf-8"
    ):
        """
        Construct a template loader.
        
        Args:
            directories: List of directories to search (in priority order).
            extensions: Recognized template file extensions.
            encoding: File encoding for reading templates.
        """
        pass
    
    def load(self, template_name: str) -> str:
        """
        Load a template's source code.
        
        Args:
            template_name: Name/path of the template.
        
        Returns:
            Template source code as a string.
        
        Raises:
            TemplateNotFoundError: If template does not exist.
        """
        pass
    
    def exists(self, template_name: str) -> bool:
        """
        Check if a template exists.
        
        Args:
            template_name: Name/path of the template.
        
        Returns:
            True if template exists, False otherwise.
        """
        pass
    
    def get_path(self, template_name: str) -> Optional[str]:
        """
        Get the full filesystem path to a template.
        
        Args:
            template_name: Name/path of the template.
        
        Returns:
            Full path if found, None otherwise.
        """
        pass
    
    def get_mtime(self, template_name: str) -> Optional[float]:
        """
        Get the modification time of a template file.
        
        Args:
            template_name: Name/path of the template.
        
        Returns:
            Modification timestamp if found, None otherwise.
        """
        pass
    
    def add_directory(self, directory: str, priority: int = 0) -> None:
        """
        Add a template directory.
        
        Args:
            directory: Directory path to add.
            priority: Priority (higher = searched first).
        """
        pass
```

### TemplateCache Class

```python
class TemplateCache:
    """
    Caches compiled templates for performance.
    """
    
    def __init__(
        self,
        max_size: int = 400,
        auto_reload: bool = False
    ):
        """
        Construct a template cache.
        
        Args:
            max_size: Maximum number of cached templates.
            auto_reload: Check for template changes (debug mode).
        """
        pass
    
    def get(
        self,
        key: str,
        mtime: Optional[float] = None
    ) -> Optional[Any]:
        """
        Get a cached template.
        
        Args:
            key: Cache key (usually template name).
            mtime: Current modification time for staleness check.
        
        Returns:
            Cached template if found and fresh, None otherwise.
        """
        pass
    
    def set(
        self,
        key: str,
        template: Any,
        mtime: Optional[float] = None
    ) -> None:
        """
        Cache a compiled template.
        
        Args:
            key: Cache key (usually template name).
            template: Compiled template object.
            mtime: Modification time for staleness tracking.
        """
        pass
    
    def clear(self) -> None:
        """Clear all cached templates."""
        pass
    
    def remove(self, key: str) -> None:
        """
        Remove a specific template from cache.
        
        Args:
            key: Cache key to remove.
        """
        pass
    
    @property
    def size(self) -> int:
        """Return current cache size."""
        pass
```

### TemplateEngineRegistry Class

```python
class TemplateEngineRegistry:
    """
    Registry for template engine adapters.
    """
    
    _engines: Dict[str, type] = {}
    _default_engine: str = "jinja2"
    
    @classmethod
    def register(
        cls,
        name: str,
        engine_class: type
    ) -> None:
        """
        Register a template engine adapter.
        
        Args:
            name: Engine name (e.g., "jinja2", "mako").
            engine_class: Engine adapter class.
        """
        pass
    
    @classmethod
    def get(cls, name: str) -> type:
        """
        Get a registered engine class.
        
        Args:
            name: Engine name.
        
        Returns:
            Engine adapter class.
        
        Raises:
            TemplateEngineNotFoundError: If engine not registered.
        """
        pass
    
    @classmethod
    def create(
        cls,
        name: str,
        **kwargs: Any
    ) -> TemplateEngine:
        """
        Create an engine instance.
        
        Args:
            name: Engine name.
            **kwargs: Engine configuration options.
        
        Returns:
            Configured engine instance.
        """
        pass
    
    @classmethod
    def set_default(cls, name: str) -> None:
        """
        Set the default template engine.
        
        Args:
            name: Engine name to use as default.
        """
        pass
    
    @classmethod
    def list_engines(cls) -> list[str]:
        """Return list of registered engine names."""
        pass
```

### TemplateContext Class

```python
class TemplateContext:
    """
    Manages template context variables.
    """
    
    def __init__(
        self,
        initial: Optional[Dict[str, Any]] = None
    ):
        """
        Construct a template context.
        
        Args:
            initial: Initial context variables.
        """
        pass
    
    def __getitem__(self, key: str) -> Any:
        """Get a context variable."""
        pass
    
    def __setitem__(self, key: str, value: Any) -> None:
        """Set a context variable."""
        pass
    
    def __contains__(self, key: str) -> bool:
        """Check if a variable exists."""
        pass
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a context variable with default.
        
        Args:
            key: Variable name.
            default: Default value if not found.
        
        Returns:
            Variable value or default.
        """
        pass
    
    def update(self, data: Dict[str, Any]) -> None:
        """
        Update context with multiple variables.
        
        Args:
            data: Dictionary of variables to add.
        """
        pass
    
    def merge(self, other: "TemplateContext") -> "TemplateContext":
        """
        Merge with another context.
        
        Args:
            other: Context to merge.
        
        Returns:
            New merged context.
        """
        pass
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary."""
        pass
```

### Response Integration Functions

```python
def render_template(
    template_name: str,
    context: Optional[Dict[str, Any]] = None,
    status_code: int = 200,
    content_type: str = "text/html; charset=utf-8",
    headers: Optional[Dict[str, str]] = None,
    **kwargs: Any
) -> "Response":
    """
    Render a template and return an HTTP Response.
    
    Args:
        template_name: Name/path of the template file.
        context: Dictionary of variables (optional).
        status_code: HTTP status code (default 200).
        content_type: Content-Type header value.
        headers: Additional response headers.
        **kwargs: Additional variables merged into context.
    
    Returns:
        HTTP Response with rendered template body.
    """
    pass


def render_template_stream(
    template_name: str,
    context: Optional[Dict[str, Any]] = None,
    status_code: int = 200,
    content_type: str = "text/html; charset=utf-8",
    headers: Optional[Dict[str, str]] = None,
    **kwargs: Any
) -> "StreamingResponse":
    """
    Render a template as a streaming HTTP Response.
    
    Args:
        template_name: Name/path of the template file.
        context: Dictionary of variables (optional).
        status_code: HTTP status code (default 200).
        content_type: Content-Type header value.
        headers: Additional response headers.
        **kwargs: Additional variables merged into context.
    
    Returns:
        Streaming HTTP Response with rendered template body.
    """
    pass
```

### Auto-Escaping Utilities

```python
class SafeString(str):
    """
    A string marked as safe that bypasses auto-escaping.
    """
    
    def __html__(self) -> str:
        """Return self for Jinja2 Markup compatibility."""
        return self


def safe(value: str) -> SafeString:
    """
    Mark a string as safe (bypasses auto-escaping).
    
    Args:
        value: String to mark as safe.
    
    Returns:
        SafeString instance.
    """
    return SafeString(value)


def escape(value: str) -> str:
    """
    Escape HTML special characters.
    
    Args:
        value: String to escape.
    
    Returns:
        Escaped string.
    """
    pass


def escape_json(value: Any) -> str:
    """
    Escape a value for safe embedding in JavaScript.
    
    Args:
        value: Value to escape.
    
    Returns:
        JSON-escaped string.
    """
    pass


def escape_url(value: str) -> str:
    """
    URL-encode a string.
    
    Args:
        value: String to encode.
    
    Returns:
        URL-encoded string.
    """
    pass
```

### Built-in Filters

```python
# Built-in filter implementations

def filter_safe(value: str) -> SafeString:
    """Mark value as safe."""
    return SafeString(value)


def filter_escape(value: str) -> str:
    """Escape HTML characters."""
    return escape(value)


def filter_lower(value: str) -> str:
    """Convert to lowercase."""
    return str(value).lower()


def filter_upper(value: str) -> str:
    """Convert to uppercase."""
    return str(value).upper()


def filter_title(value: str) -> str:
    """Convert to title case."""
    return str(value).title()


def filter_trim(value: str) -> str:
    """Strip whitespace."""
    return str(value).strip()


def filter_default(value: Any, default: Any = "") -> Any:
    """Return default if value is falsy."""
    return value if value else default


def filter_length(value: Any) -> int:
    """Return length of value."""
    return len(value)


def filter_join(value: list, separator: str = "") -> str:
    """Join list elements."""
    return separator.join(str(v) for v in value)


def filter_first(value: list) -> Any:
    """Return first element."""
    return value[0] if value else None


def filter_last(value: list) -> Any:
    """Return last element."""
    return value[-1] if value else None


def filter_sort(value: list, reverse: bool = False) -> list:
    """Sort list."""
    return sorted(value, reverse=reverse)


def filter_reverse(value: list) -> list:
    """Reverse list."""
    return list(reversed(value))


def filter_format(value: str, *args: Any, **kwargs: Any) -> str:
    """Format string."""
    return value.format(*args, **kwargs)


def filter_date(value: Any, format_str: str = "%Y-%m-%d") -> str:
    """Format date."""
    pass


def filter_json(value: Any) -> str:
    """Convert to JSON string."""
    pass


# Registry of built-in filters
BUILTIN_FILTERS = {
    "safe": filter_safe,
    "escape": filter_escape,
    "e": filter_escape,
    "lower": filter_lower,
    "upper": filter_upper,
    "title": filter_title,
    "trim": filter_trim,
    "default": filter_default,
    "d": filter_default,
    "length": filter_length,
    "join": filter_join,
    "first": filter_first,
    "last": filter_last,
    "sort": filter_sort,
    "reverse": filter_reverse,
    "format": filter_format,
    "date": filter_date,
    "json": filter_json,
}
```

## Data Models

### TemplateConfig Dataclass

```python
@dataclass
class TemplateConfig:
    """
    Configuration for template rendering.
    """
    
    engine: str = "jinja2"
    directories: list[str] = field(default_factory=list)
    extensions: list[str] = field(default_factory=lambda: [".html", ".htm", ".xml", ".txt"])
    auto_escape: bool = True
    cache_enabled: bool = True
    cache_size: int = 400
    auto_reload: bool = False
    encoding: str = "utf-8"
    undefined_behavior: str = "silent"  # "silent", "strict", "debug"
    engine_options: Dict[str, Any] = field(default_factory=dict)
    
    def validate(self) -> None:
        """
        Validate configuration.
        
        Raises:
            TemplateConfigurationError: If configuration is invalid.
        """
        pass
```

### TemplateInfo Dataclass

```python
@dataclass
class TemplateInfo:
    """
    Information about a loaded template.
    """
    
    name: str
    path: Optional[str]
    source: str
    mtime: Optional[float]
    engine: str
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Template Rendering Determinism

*For any* valid template and context, rendering the same template with the same context SHALL produce identical output on every invocation.

**Validates: Requirements 2.1, 2.6**

### Property 2: Auto-Escaping Correctness

*For any* string containing HTML special characters (&, <, >, ", '), when auto-escaping is enabled, the rendered output SHALL contain the escaped equivalents (&amp;, &lt;, &gt;, &quot;, &#39;) unless the string is marked as safe.

**Validates: Requirements 5.1, 5.2, 5.6**

### Property 3: Safe String Bypass

*For any* string marked as safe via the safe() function or SafeString class, the rendered output SHALL contain the original unescaped content regardless of auto-escaping settings.

**Validates: Requirements 5.3, 5.7**

### Property 4: Context Variable Access

*For any* context dictionary with nested structures, template expressions using dot notation SHALL correctly access nested values, and missing keys SHALL return empty string (in silent mode) or raise UndefinedVariableError (in strict mode).

**Validates: Requirements 3.2, 3.7, 3.8**

### Property 5: Template Inheritance Chain

*For any* template inheritance chain (child extends parent extends grandparent), block content SHALL be resolved from the most specific (child) template, with super() calls correctly invoking parent block content.

**Validates: Requirements 4.1, 4.2, 4.3, 4.9**

### Property 6: Filter Chaining Correctness

*For any* sequence of filters applied to a value, the filters SHALL be applied left-to-right, with each filter receiving the output of the previous filter.

**Validates: Requirements 7.4**

### Property 7: Cache Consistency

*For any* cached template, when auto_reload is enabled and the template file is modified, subsequent renders SHALL use the updated template content.

**Validates: Requirements 6.6, 6.8**

### Property 8: Engine Registration Idempotence

*For any* template engine registered multiple times with the same name, only the most recent registration SHALL be active, and creating an engine by name SHALL return an instance of the most recently registered class.

**Validates: Requirements 1.2**

### Property 9: Error Message Completeness

*For any* template error (syntax error, undefined variable, missing template), the error message SHALL include the template filename and line number where the error occurred.

**Validates: Requirements 9.1, 9.2**

### Property 10: Response Integration Correctness

*For any* call to render_template(), the returned Response SHALL have Content-Type set to the specified value (default text/html), status code set to the specified value (default 200), and body containing the rendered template output.

**Validates: Requirements 8.1, 8.2, 8.4**

## Error Handling

### Exception Hierarchy

```python
class TemplateError(Exception):
    """Base exception for template errors."""
    pass


class TemplateNotFoundError(TemplateError):
    """Template file not found."""
    def __init__(self, template_name: str, searched_paths: list[str]):
        self.template_name = template_name
        self.searched_paths = searched_paths
        super().__init__(
            f"Template '{template_name}' not found. "
            f"Searched: {', '.join(searched_paths)}"
        )


class TemplateSyntaxError(TemplateError):
    """Template contains syntax errors."""
    def __init__(
        self,
        template_name: str,
        line_number: int,
        message: str,
        source_context: Optional[str] = None
    ):
        self.template_name = template_name
        self.line_number = line_number
        self.source_context = source_context
        super().__init__(
            f"Syntax error in '{template_name}' at line {line_number}: {message}"
        )


class TemplateRenderError(TemplateError):
    """Error during template rendering."""
    def __init__(
        self,
        template_name: str,
        line_number: Optional[int],
        variable_name: Optional[str],
        message: str
    ):
        self.template_name = template_name
        self.line_number = line_number
        self.variable_name = variable_name
        super().__init__(
            f"Render error in '{template_name}'"
            f"{f' at line {line_number}' if line_number else ''}: {message}"
        )


class UndefinedVariableError(TemplateRenderError):
    """Undefined variable accessed in strict mode."""
    def __init__(
        self,
        template_name: str,
        line_number: int,
        variable_name: str
    ):
        super().__init__(
            template_name,
            line_number,
            variable_name,
            f"Undefined variable '{variable_name}'"
        )


class TemplateInheritanceError(TemplateError):
    """Error in template inheritance chain."""
    def __init__(self, message: str, chain: list[str]):
        self.chain = chain
        super().__init__(f"{message}. Inheritance chain: {' -> '.join(chain)}")


class TemplateEngineNotFoundError(TemplateError):
    """Requested template engine not registered."""
    def __init__(self, engine_name: str, available: list[str]):
        self.engine_name = engine_name
        self.available = available
        super().__init__(
            f"Template engine '{engine_name}' not found. "
            f"Available: {', '.join(available)}"
        )


class TemplateFilterNotFoundError(TemplateError):
    """Requested filter not registered."""
    def __init__(self, filter_name: str):
        self.filter_name = filter_name
        super().__init__(f"Template filter '{filter_name}' not found")


class TemplateConfigurationError(TemplateError):
    """Invalid template configuration."""
    def __init__(self, message: str, config_key: Optional[str] = None):
        self.config_key = config_key
        super().__init__(
            f"Template configuration error"
            f"{f' ({config_key})' if config_key else ''}: {message}"
        )
```

## Testing Strategy

### Unit Tests

Unit tests should cover:
- TemplateLoader file discovery and loading
- TemplateCache get/set/clear operations
- TemplateContext variable access and merging
- Auto-escaping of HTML special characters
- SafeString bypass of auto-escaping
- Built-in filter implementations
- Error message formatting with line numbers

### Property-Based Tests

Property tests should verify:
- Template rendering determinism (same input = same output)
- Auto-escaping correctness for all HTML special characters
- Safe string bypass for marked content
- Context variable access with nested structures
- Template inheritance block resolution
- Filter chaining order
- Cache consistency with auto-reload
- Engine registration idempotence
- Error message completeness
- Response integration correctness

### Integration Tests

Integration tests should verify:
- Full template rendering with Jinja2 adapter
- Full template rendering with Mako adapter
- Template inheritance across multiple files
- Context processor integration
- Response helper integration
- Configuration loading and validation

### Test Configuration

- Use testbase framework per repository conventions
- Minimum 100 iterations for property-based tests
- Test files at `source/testroots/ccai/tests/singlehost/webworks/templating/`
