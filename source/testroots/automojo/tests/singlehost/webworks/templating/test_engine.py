"""
    Tests for the TemplateEngine abstract base class.
    
    This module tests the TemplateEngine ABC including:
    - Abstract method definitions
    - Default implementations for render_async() and render_stream()
    - Proper inheritance behavior
"""

import asyncio
from abc import ABC
from typing import Any, Callable, Dict, Iterator

from automojo.webworks.templating.engine import TemplateEngine


# =============================================================================
# Concrete Implementation for Testing
# =============================================================================

class MockTemplateEngine(TemplateEngine):
    """
        Mock implementation of TemplateEngine for testing.
        
        Provides simple implementations of abstract methods to enable
        testing of the base class behavior.
    """
    
    def __init__(self):
        """
            Construct a MockTemplateEngine.
        """
        self._templates = {}
        self._filters = {}
        self._globals = {}
        self._cache_cleared = False
        return
    
    def add_template(self, name: str, content: str) -> None:
        """
            Add a template to the mock engine.
            
            :param name: Template name.
            :param content: Template content.
        """
        self._templates[name] = content
        return
    
    def render(
        self,
        template_name: str,
        context: Dict[str, Any]
    ) -> str:
        """
            Render a template with simple variable substitution.
            
            :param template_name: Name of the template.
            :param context: Context variables.
            
            :returns: Rendered template string.
        """
        if template_name not in self._templates:
            raise KeyError(f"Template '{template_name}' not found")
        
        content = self._templates[template_name]
        
        # Simple variable substitution for testing
        for key, value in context.items():
            content = content.replace("{{ " + key + " }}", str(value))
        
        return content
    
    def render_string(
        self,
        template_source: str,
        context: Dict[str, Any]
    ) -> str:
        """
            Render a template string with simple variable substitution.
            
            :param template_source: Template source code.
            :param context: Context variables.
            
            :returns: Rendered template string.
        """
        content = template_source
        
        # Simple variable substitution for testing
        for key, value in context.items():
            content = content.replace("{{ " + key + " }}", str(value))
        
        return content
    
    def add_filter(
        self,
        name: str,
        func: Callable[..., Any]
    ) -> None:
        """
            Register a filter function.
            
            :param name: Filter name.
            :param func: Filter function.
        """
        self._filters[name] = func
        return
    
    def add_global(
        self,
        name: str,
        value: Any
    ) -> None:
        """
            Register a global variable.
            
            :param name: Global name.
            :param value: Global value.
        """
        self._globals[name] = value
        return
    
    def clear_cache(self) -> None:
        """
            Clear the template cache.
        """
        self._cache_cleared = True
        return


# =============================================================================
# TemplateEngine ABC Tests
# =============================================================================

def test_templateengine_is_abstract():
    """
        Test that TemplateEngine is an abstract base class.
    """
    if not issubclass(TemplateEngine, ABC):
        raise AssertionError("TemplateEngine should be an ABC subclass")
    
    return


def test_templateengine_cannot_be_instantiated():
    """
        Test that TemplateEngine cannot be instantiated directly.
    """
    try:
        engine = TemplateEngine()
        raise AssertionError("TemplateEngine should not be instantiable")
    except TypeError as exc:
        # Expected - abstract class cannot be instantiated
        if "abstract" not in str(exc).lower():
            raise AssertionError(f"Expected abstract class error, got: {exc}")
    
    return


def test_templateengine_has_render_abstract_method():
    """
        Test that TemplateEngine defines render as abstract method.
    """
    if "render" not in TemplateEngine.__abstractmethods__:
        raise AssertionError("render should be an abstract method")
    
    return


def test_templateengine_has_render_string_abstract_method():
    """
        Test that TemplateEngine defines render_string as abstract method.
    """
    if "render_string" not in TemplateEngine.__abstractmethods__:
        raise AssertionError("render_string should be an abstract method")
    
    return


def test_templateengine_has_add_filter_abstract_method():
    """
        Test that TemplateEngine defines add_filter as abstract method.
    """
    if "add_filter" not in TemplateEngine.__abstractmethods__:
        raise AssertionError("add_filter should be an abstract method")
    
    return


def test_templateengine_has_add_global_abstract_method():
    """
        Test that TemplateEngine defines add_global as abstract method.
    """
    if "add_global" not in TemplateEngine.__abstractmethods__:
        raise AssertionError("add_global should be an abstract method")
    
    return


def test_templateengine_has_clear_cache_abstract_method():
    """
        Test that TemplateEngine defines clear_cache as abstract method.
    """
    if "clear_cache" not in TemplateEngine.__abstractmethods__:
        raise AssertionError("clear_cache should be an abstract method")
    
    return


def test_templateengine_render_async_not_abstract():
    """
        Test that render_async is not an abstract method.
    """
    if "render_async" in TemplateEngine.__abstractmethods__:
        raise AssertionError("render_async should not be an abstract method")
    
    return


def test_templateengine_render_stream_not_abstract():
    """
        Test that render_stream is not an abstract method.
    """
    if "render_stream" in TemplateEngine.__abstractmethods__:
        raise AssertionError("render_stream should not be an abstract method")
    
    return


# =============================================================================
# MockTemplateEngine Subclass Tests
# =============================================================================

def test_mock_engine_is_templateengine():
    """
        Test that MockTemplateEngine is a TemplateEngine subclass.
    """
    engine = MockTemplateEngine()
    
    if not isinstance(engine, TemplateEngine):
        raise AssertionError("MockTemplateEngine should be a TemplateEngine subclass")
    
    return


def test_mock_engine_can_be_instantiated():
    """
        Test that a concrete subclass can be instantiated.
    """
    engine = MockTemplateEngine()
    
    if engine is None:
        raise AssertionError("MockTemplateEngine should be instantiable")
    
    return


# =============================================================================
# render() Method Tests
# =============================================================================

def test_render_returns_string():
    """
        Test that render() returns a string.
    """
    engine = MockTemplateEngine()
    engine.add_template("test.html", "Hello World")
    
    result = engine.render("test.html", {})
    
    if not isinstance(result, str):
        raise AssertionError(f"Expected str, got {type(result)}")
    
    return


def test_render_with_context():
    """
        Test that render() substitutes context variables.
    """
    engine = MockTemplateEngine()
    engine.add_template("test.html", "Hello {{ name }}!")
    
    result = engine.render("test.html", {"name": "World"})
    
    if result != "Hello World!":
        raise AssertionError(f"Expected 'Hello World!', got '{result}'")
    
    return


def test_render_with_multiple_variables():
    """
        Test that render() handles multiple context variables.
    """
    engine = MockTemplateEngine()
    engine.add_template("test.html", "{{ greeting }} {{ name }}!")
    
    result = engine.render("test.html", {"greeting": "Hello", "name": "World"})
    
    if result != "Hello World!":
        raise AssertionError(f"Expected 'Hello World!', got '{result}'")
    
    return


def test_render_with_empty_context():
    """
        Test that render() works with empty context.
    """
    engine = MockTemplateEngine()
    engine.add_template("test.html", "Static content")
    
    result = engine.render("test.html", {})
    
    if result != "Static content":
        raise AssertionError(f"Expected 'Static content', got '{result}'")
    
    return


# =============================================================================
# render_string() Method Tests
# =============================================================================

def test_render_string_returns_string():
    """
        Test that render_string() returns a string.
    """
    engine = MockTemplateEngine()
    
    result = engine.render_string("Hello World", {})
    
    if not isinstance(result, str):
        raise AssertionError(f"Expected str, got {type(result)}")
    
    return


def test_render_string_with_context():
    """
        Test that render_string() substitutes context variables.
    """
    engine = MockTemplateEngine()
    
    result = engine.render_string("Hello {{ name }}!", {"name": "World"})
    
    if result != "Hello World!":
        raise AssertionError(f"Expected 'Hello World!', got '{result}'")
    
    return


def test_render_string_with_empty_context():
    """
        Test that render_string() works with empty context.
    """
    engine = MockTemplateEngine()
    
    result = engine.render_string("Static content", {})
    
    if result != "Static content":
        raise AssertionError(f"Expected 'Static content', got '{result}'")
    
    return


# =============================================================================
# render_async() Default Implementation Tests
# =============================================================================

def test_render_async_returns_coroutine():
    """
        Test that render_async() returns a coroutine.
    """
    engine = MockTemplateEngine()
    engine.add_template("test.html", "Hello World")
    
    coro = engine.render_async("test.html", {})
    
    if not asyncio.iscoroutine(coro):
        raise AssertionError("render_async should return a coroutine")
    
    # Clean up the coroutine
    coro.close()
    
    return


def test_render_async_default_falls_back_to_sync():
    """
        Test that default render_async() falls back to sync render().
    """
    engine = MockTemplateEngine()
    engine.add_template("test.html", "Hello {{ name }}!")
    
    # Run the async method
    result = asyncio.get_event_loop().run_until_complete(
        engine.render_async("test.html", {"name": "World"})
    )
    
    if result != "Hello World!":
        raise AssertionError(f"Expected 'Hello World!', got '{result}'")
    
    return


def test_render_async_with_context():
    """
        Test that render_async() handles context variables.
    """
    engine = MockTemplateEngine()
    engine.add_template("test.html", "{{ greeting }} {{ name }}!")
    
    result = asyncio.get_event_loop().run_until_complete(
        engine.render_async("test.html", {"greeting": "Hello", "name": "World"})
    )
    
    if result != "Hello World!":
        raise AssertionError(f"Expected 'Hello World!', got '{result}'")
    
    return


# =============================================================================
# render_stream() Default Implementation Tests
# =============================================================================

def test_render_stream_returns_iterator():
    """
        Test that render_stream() returns an iterator.
    """
    engine = MockTemplateEngine()
    engine.add_template("test.html", "Hello World")
    
    result = engine.render_stream("test.html", {})
    
    if not isinstance(result, Iterator):
        raise AssertionError(f"Expected Iterator, got {type(result)}")
    
    return


def test_render_stream_default_yields_single_chunk():
    """
        Test that default render_stream() yields entire output as single chunk.
    """
    engine = MockTemplateEngine()
    engine.add_template("test.html", "Hello World")
    
    chunks = list(engine.render_stream("test.html", {}))
    
    if len(chunks) != 1:
        raise AssertionError(f"Expected 1 chunk, got {len(chunks)}")
    
    if chunks[0] != "Hello World":
        raise AssertionError(f"Expected 'Hello World', got '{chunks[0]}'")
    
    return


def test_render_stream_with_context():
    """
        Test that render_stream() handles context variables.
    """
    engine = MockTemplateEngine()
    engine.add_template("test.html", "Hello {{ name }}!")
    
    chunks = list(engine.render_stream("test.html", {"name": "World"}))
    
    if len(chunks) != 1:
        raise AssertionError(f"Expected 1 chunk, got {len(chunks)}")
    
    if chunks[0] != "Hello World!":
        raise AssertionError(f"Expected 'Hello World!', got '{chunks[0]}'")
    
    return


def test_render_stream_can_be_iterated():
    """
        Test that render_stream() result can be iterated.
    """
    engine = MockTemplateEngine()
    engine.add_template("test.html", "Content")
    
    result = ""
    for chunk in engine.render_stream("test.html", {}):
        result += chunk
    
    if result != "Content":
        raise AssertionError(f"Expected 'Content', got '{result}'")
    
    return


# =============================================================================
# add_filter() Method Tests
# =============================================================================

def test_add_filter_registers_filter():
    """
        Test that add_filter() registers a filter function.
    """
    engine = MockTemplateEngine()
    
    def uppercase(value):
        return str(value).upper()
    
    engine.add_filter("uppercase", uppercase)
    
    if "uppercase" not in engine._filters:
        raise AssertionError("Filter should be registered")
    
    if engine._filters["uppercase"] is not uppercase:
        raise AssertionError("Filter function should be stored")
    
    return


def test_add_filter_accepts_callable():
    """
        Test that add_filter() accepts any callable.
    """
    engine = MockTemplateEngine()
    
    # Lambda function
    engine.add_filter("double", lambda x: x * 2)
    
    if "double" not in engine._filters:
        raise AssertionError("Lambda filter should be registered")
    
    return


def test_add_filter_multiple_filters():
    """
        Test that add_filter() can register multiple filters.
    """
    engine = MockTemplateEngine()
    
    engine.add_filter("upper", str.upper)
    engine.add_filter("lower", str.lower)
    engine.add_filter("strip", str.strip)
    
    if len(engine._filters) != 3:
        raise AssertionError(f"Expected 3 filters, got {len(engine._filters)}")
    
    return


# =============================================================================
# add_global() Method Tests
# =============================================================================

def test_add_global_registers_value():
    """
        Test that add_global() registers a global value.
    """
    engine = MockTemplateEngine()
    
    engine.add_global("app_name", "My Application")
    
    if "app_name" not in engine._globals:
        raise AssertionError("Global should be registered")
    
    if engine._globals["app_name"] != "My Application":
        raise AssertionError("Global value should be stored")
    
    return


def test_add_global_accepts_callable():
    """
        Test that add_global() accepts callable values.
    """
    engine = MockTemplateEngine()
    
    def get_version():
        return "1.0.0"
    
    engine.add_global("version", get_version)
    
    if "version" not in engine._globals:
        raise AssertionError("Callable global should be registered")
    
    if engine._globals["version"] is not get_version:
        raise AssertionError("Callable should be stored")
    
    return


def test_add_global_multiple_globals():
    """
        Test that add_global() can register multiple globals.
    """
    engine = MockTemplateEngine()
    
    engine.add_global("app_name", "My App")
    engine.add_global("version", "1.0.0")
    engine.add_global("debug", True)
    
    if len(engine._globals) != 3:
        raise AssertionError(f"Expected 3 globals, got {len(engine._globals)}")
    
    return


# =============================================================================
# clear_cache() Method Tests
# =============================================================================

def test_clear_cache_clears_cache():
    """
        Test that clear_cache() clears the template cache.
    """
    engine = MockTemplateEngine()
    
    engine.clear_cache()
    
    if not engine._cache_cleared:
        raise AssertionError("Cache should be cleared")
    
    return


def test_clear_cache_can_be_called_multiple_times():
    """
        Test that clear_cache() can be called multiple times.
    """
    engine = MockTemplateEngine()
    
    engine.clear_cache()
    engine.clear_cache()
    engine.clear_cache()
    
    if not engine._cache_cleared:
        raise AssertionError("Cache should be cleared")
    
    return
