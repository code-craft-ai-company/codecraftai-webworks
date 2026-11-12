"""
    Tests for the Jinja2Adapter class.
    
    This module tests the Jinja2Adapter including:
    - Initialization and configuration
    - Template rendering (render, render_string, render_async, render_stream)
    - Filter and global registration
    - Auto-escaping configuration
    - Cache management and auto_reload
"""

import asyncio
import os
import shutil
import tempfile

from ccai.webworks.templating.exceptions import (
    TemplateConfigurationError,
    TemplateError,
    TemplateFilterNotFoundError,
    TemplateNotFoundError,
    TemplateRenderError,
    TemplateSyntaxError,
    UndefinedVariableError,
)
from ccai.webworks.templating.jinja2_adapter import Jinja2Adapter, Jinja2CompiledTemplate


# =============================================================================
# Test Fixtures / Setup
# =============================================================================

def _create_temp_template_dir(templates: dict) -> str:
    """
        Create a temporary directory with template files.
        
        :param templates: Dictionary mapping template names to content.
        
        :returns: Path to the temporary directory.
    """
    temp_dir = tempfile.mkdtemp()
    
    for name, content in templates.items():
        template_path = os.path.join(temp_dir, name)
        template_dir = os.path.dirname(template_path)
        
        if template_dir and not os.path.exists(template_dir):
            os.makedirs(template_dir)
        
        with open(template_path, "w", encoding="utf-8") as f:
            f.write(content)
    
    return temp_dir


def _cleanup_temp_dir(temp_dir: str) -> None:
    """
        Remove a temporary directory and its contents.
        
        :param temp_dir: Path to the temporary directory.
    """
    shutil.rmtree(temp_dir, ignore_errors=True)
    return


# =============================================================================
# 9.1 - __init__() and Configuration Tests
# =============================================================================

def test_init_creates_adapter():
    """
        Test that Jinja2Adapter can be instantiated with template directories.
    """
    temp_dir = _create_temp_template_dir({})
    
    try:
        adapter = Jinja2Adapter(template_dirs=[temp_dir])
        
        if not isinstance(adapter, Jinja2Adapter):
            raise AssertionError("Expected Jinja2Adapter instance")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_init_is_template_engine():
    """
        Test that Jinja2Adapter is a TemplateEngine subclass.
    """
    from ccai.webworks.templating.engine import TemplateEngine
    
    temp_dir = _create_temp_template_dir({})
    
    try:
        adapter = Jinja2Adapter(template_dirs=[temp_dir])
        
        if not isinstance(adapter, TemplateEngine):
            raise AssertionError("Jinja2Adapter should be a TemplateEngine")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_init_stores_template_dirs():
    """
        Test that __init__() stores the template directories.
    """
    temp_dir = _create_temp_template_dir({})
    
    try:
        adapter = Jinja2Adapter(template_dirs=[temp_dir])
        
        if adapter._template_dirs != [temp_dir]:
            raise AssertionError(
                f"Expected [{temp_dir}], got {adapter._template_dirs}"
            )
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_init_default_auto_escape():
    """
        Test that auto_escape defaults to True.
    """
    temp_dir = _create_temp_template_dir({})
    
    try:
        adapter = Jinja2Adapter(template_dirs=[temp_dir])
        
        if adapter._auto_escape is not True:
            raise AssertionError("auto_escape should default to True")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_init_default_cache_size():
    """
        Test that cache_size defaults to 400.
    """
    temp_dir = _create_temp_template_dir({})
    
    try:
        adapter = Jinja2Adapter(template_dirs=[temp_dir])
        
        if adapter._cache_size != 400:
            raise AssertionError(f"Expected cache_size 400, got {adapter._cache_size}")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_init_default_auto_reload():
    """
        Test that auto_reload defaults to False.
    """
    temp_dir = _create_temp_template_dir({})
    
    try:
        adapter = Jinja2Adapter(template_dirs=[temp_dir])
        
        if adapter._auto_reload is not False:
            raise AssertionError("auto_reload should default to False")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_init_default_encoding():
    """
        Test that encoding defaults to utf-8.
    """
    temp_dir = _create_temp_template_dir({})
    
    try:
        adapter = Jinja2Adapter(template_dirs=[temp_dir])
        
        if adapter._encoding != "utf-8":
            raise AssertionError(f"Expected 'utf-8', got '{adapter._encoding}'")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_init_default_undefined_behavior():
    """
        Test that undefined_behavior defaults to silent.
    """
    temp_dir = _create_temp_template_dir({})
    
    try:
        adapter = Jinja2Adapter(template_dirs=[temp_dir])
        
        if adapter._undefined_behavior != "silent":
            raise AssertionError(
                f"Expected 'silent', got '{adapter._undefined_behavior}'"
            )
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_init_custom_configuration():
    """
        Test that __init__() accepts custom configuration values.
    """
    temp_dir = _create_temp_template_dir({})
    
    try:
        adapter = Jinja2Adapter(
            template_dirs=[temp_dir],
            auto_escape=False,
            cache_size=200,
            auto_reload=True,
            encoding="latin-1",
            undefined_behavior="strict",
        )
        
        if adapter._auto_escape is not False:
            raise AssertionError("auto_escape should be False")
        if adapter._cache_size != 200:
            raise AssertionError(f"Expected cache_size 200, got {adapter._cache_size}")
        if adapter._auto_reload is not True:
            raise AssertionError("auto_reload should be True")
        if adapter._encoding != "latin-1":
            raise AssertionError(f"Expected 'latin-1', got '{adapter._encoding}'")
        if adapter._undefined_behavior != "strict":
            raise AssertionError(
                f"Expected 'strict', got '{adapter._undefined_behavior}'"
            )
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_init_creates_jinja2_environment():
    """
        Test that __init__() creates a Jinja2 Environment.
    """
    import jinja2
    
    temp_dir = _create_temp_template_dir({})
    
    try:
        adapter = Jinja2Adapter(template_dirs=[temp_dir])
        
        if not isinstance(adapter._environment, jinja2.Environment):
            raise AssertionError("Expected jinja2.Environment instance")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_init_with_multiple_template_dirs():
    """
        Test that __init__() accepts multiple template directories.
    """
    temp_dir1 = _create_temp_template_dir({})
    temp_dir2 = _create_temp_template_dir({})
    
    try:
        adapter = Jinja2Adapter(template_dirs=[temp_dir1, temp_dir2])
        
        if len(adapter._template_dirs) != 2:
            raise AssertionError(
                f"Expected 2 dirs, got {len(adapter._template_dirs)}"
            )
    finally:
        _cleanup_temp_dir(temp_dir1)
        _cleanup_temp_dir(temp_dir2)
    
    return


# =============================================================================
# 9.2 - Rendering Methods Tests
# =============================================================================

def test_render_returns_rendered_template():
    """
        Test that render() returns the rendered template content.
    """
    temp_dir = _create_temp_template_dir({
        "hello.html": "Hello {{ name }}!"
    })
    
    try:
        adapter = Jinja2Adapter(template_dirs=[temp_dir])
        
        result = adapter.render("hello.html", {"name": "World"})
        
        if result != "Hello World!":
            raise AssertionError(f"Expected 'Hello World!', got '{result}'")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_render_with_empty_context():
    """
        Test that render() works with an empty context.
    """
    temp_dir = _create_temp_template_dir({
        "static.html": "No variables here."
    })
    
    try:
        adapter = Jinja2Adapter(template_dirs=[temp_dir])
        
        result = adapter.render("static.html", {})
        
        if result != "No variables here.":
            raise AssertionError(f"Expected 'No variables here.', got '{result}'")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_render_with_multiple_variables():
    """
        Test that render() handles multiple context variables.
    """
    temp_dir = _create_temp_template_dir({
        "multi.html": "{{ greeting }}, {{ name }}! You are {{ age }}."
    })
    
    try:
        adapter = Jinja2Adapter(template_dirs=[temp_dir])
        
        result = adapter.render("multi.html", {
            "greeting": "Hello",
            "name": "Alice",
            "age": 30,
        })
        
        if result != "Hello, Alice! You are 30.":
            raise AssertionError(f"Unexpected result: {result}")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_render_raises_template_not_found():
    """
        Test that render() raises TemplateNotFoundError for missing templates.
    """
    temp_dir = _create_temp_template_dir({})
    
    try:
        adapter = Jinja2Adapter(template_dirs=[temp_dir])
        
        try:
            adapter.render("missing.html", {})
            raise AssertionError("Should raise TemplateNotFoundError")
        except TemplateNotFoundError as exc:
            if exc.template_name != "missing.html":
                raise AssertionError(
                    f"Expected template_name 'missing.html', got '{exc.template_name}'"
                )
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_render_raises_error_for_syntax_error():
    """
        Test that render() raises TemplateError for syntax errors.
    """
    temp_dir = _create_temp_template_dir({
        "bad.html": "{% if unclosed %}"
    })
    
    try:
        adapter = Jinja2Adapter(template_dirs=[temp_dir])
        
        try:
            adapter.render("bad.html", {})
            raise AssertionError("Should raise TemplateError")
        except TemplateError:
            pass  # Expected
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_render_string_returns_rendered_content():
    """
        Test that render_string() renders a template string.
    """
    temp_dir = _create_temp_template_dir({})
    
    try:
        adapter = Jinja2Adapter(template_dirs=[temp_dir])
        
        result = adapter.render_string("Hello {{ name }}!", {"name": "World"})
        
        if result != "Hello World!":
            raise AssertionError(f"Expected 'Hello World!', got '{result}'")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_render_string_with_empty_context():
    """
        Test that render_string() works with empty context.
    """
    temp_dir = _create_temp_template_dir({})
    
    try:
        adapter = Jinja2Adapter(template_dirs=[temp_dir])
        
        result = adapter.render_string("Static content.", {})
        
        if result != "Static content.":
            raise AssertionError(f"Expected 'Static content.', got '{result}'")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_render_string_raises_error_for_syntax_error():
    """
        Test that render_string() raises TemplateError for syntax errors.
    """
    temp_dir = _create_temp_template_dir({})
    
    try:
        adapter = Jinja2Adapter(template_dirs=[temp_dir])
        
        try:
            adapter.render_string("{% if unclosed %}", {})
            raise AssertionError("Should raise TemplateError")
        except TemplateError:
            pass  # Expected
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_render_async_returns_rendered_content():
    """
        Test that render_async() returns rendered content.
    """
    temp_dir = _create_temp_template_dir({
        "async.html": "Async {{ name }}!"
    })
    
    try:
        adapter = Jinja2Adapter(template_dirs=[temp_dir])
        
        result = asyncio.run(
            adapter.render_async("async.html", {"name": "World"})
        )
        
        if result != "Async World!":
            raise AssertionError(f"Expected 'Async World!', got '{result}'")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_render_async_raises_template_not_found():
    """
        Test that render_async() raises TemplateNotFoundError.
    """
    temp_dir = _create_temp_template_dir({})
    
    try:
        adapter = Jinja2Adapter(template_dirs=[temp_dir])
        
        try:
            asyncio.run(adapter.render_async("missing.html", {}))
            raise AssertionError("Should raise TemplateNotFoundError")
        except TemplateNotFoundError:
            pass  # Expected
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_render_stream_yields_chunks():
    """
        Test that render_stream() yields rendered chunks.
    """
    temp_dir = _create_temp_template_dir({
        "stream.html": "Hello {{ name }}!"
    })
    
    try:
        adapter = Jinja2Adapter(template_dirs=[temp_dir])
        
        chunks = list(adapter.render_stream("stream.html", {"name": "World"}))
        
        result = "".join(chunks)
        
        if result != "Hello World!":
            raise AssertionError(f"Expected 'Hello World!', got '{result}'")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_render_stream_returns_iterator():
    """
        Test that render_stream() returns an iterator.
    """
    temp_dir = _create_temp_template_dir({
        "stream.html": "Content"
    })
    
    try:
        adapter = Jinja2Adapter(template_dirs=[temp_dir])
        
        stream = adapter.render_stream("stream.html", {})
        
        if not hasattr(stream, '__iter__'):
            raise AssertionError("render_stream should return an iterator")
        if not hasattr(stream, '__next__'):
            raise AssertionError("render_stream should return an iterator")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_render_stream_raises_template_not_found():
    """
        Test that render_stream() raises TemplateNotFoundError.
    """
    temp_dir = _create_temp_template_dir({})
    
    try:
        adapter = Jinja2Adapter(template_dirs=[temp_dir])
        
        try:
            list(adapter.render_stream("missing.html", {}))
            raise AssertionError("Should raise TemplateNotFoundError")
        except TemplateNotFoundError:
            pass  # Expected
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


# =============================================================================
# 9.3 - Filter and Global Registration Tests
# =============================================================================

def test_add_filter_registers_filter():
    """
        Test that add_filter() registers a custom filter.
    """
    temp_dir = _create_temp_template_dir({
        "filter.html": "{{ name|shout }}"
    })
    
    try:
        adapter = Jinja2Adapter(template_dirs=[temp_dir])
        
        adapter.add_filter("shout", lambda s: str(s).upper() + "!")
        
        result = adapter.render("filter.html", {"name": "hello"})
        
        if result != "HELLO!":
            raise AssertionError(f"Expected 'HELLO!', got '{result}'")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_add_filter_with_arguments():
    """
        Test that add_filter() supports filters with arguments.
    """
    temp_dir = _create_temp_template_dir({
        "filter_args.html": "{{ name|repeat(3) }}"
    })
    
    try:
        adapter = Jinja2Adapter(template_dirs=[temp_dir])
        
        adapter.add_filter("repeat", lambda s, n: str(s) * n)
        
        result = adapter.render("filter_args.html", {"name": "ha"})
        
        if result != "hahaha":
            raise AssertionError(f"Expected 'hahaha', got '{result}'")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_add_filter_available_in_render_string():
    """
        Test that filters registered via add_filter() work in render_string().
    """
    temp_dir = _create_temp_template_dir({})
    
    try:
        adapter = Jinja2Adapter(template_dirs=[temp_dir])
        
        adapter.add_filter("reverse_str", lambda s: str(s)[::-1])
        
        result = adapter.render_string("{{ word|reverse_str }}", {"word": "hello"})
        
        if result != "olleh":
            raise AssertionError(f"Expected 'olleh', got '{result}'")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_add_global_registers_value():
    """
        Test that add_global() registers a global variable.
    """
    temp_dir = _create_temp_template_dir({
        "global.html": "App: {{ app_name }}"
    })
    
    try:
        adapter = Jinja2Adapter(template_dirs=[temp_dir])
        
        adapter.add_global("app_name", "MyApp")
        
        result = adapter.render("global.html", {})
        
        if result != "App: MyApp":
            raise AssertionError(f"Expected 'App: MyApp', got '{result}'")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_add_global_registers_callable():
    """
        Test that add_global() registers a callable global.
    """
    temp_dir = _create_temp_template_dir({
        "global_func.html": "Version: {{ get_version() }}"
    })
    
    try:
        adapter = Jinja2Adapter(template_dirs=[temp_dir])
        
        adapter.add_global("get_version", lambda: "1.0.0")
        
        result = adapter.render("global_func.html", {})
        
        if result != "Version: 1.0.0":
            raise AssertionError(f"Expected 'Version: 1.0.0', got '{result}'")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_add_global_available_in_render_string():
    """
        Test that globals registered via add_global() work in render_string().
    """
    temp_dir = _create_temp_template_dir({})
    
    try:
        adapter = Jinja2Adapter(template_dirs=[temp_dir])
        
        adapter.add_global("site_name", "TestSite")
        
        result = adapter.render_string("Site: {{ site_name }}", {})
        
        if result != "Site: TestSite":
            raise AssertionError(f"Expected 'Site: TestSite', got '{result}'")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_add_multiple_filters():
    """
        Test that multiple filters can be registered.
    """
    temp_dir = _create_temp_template_dir({
        "multi_filter.html": "{{ name|shout|add_dots }}"
    })
    
    try:
        adapter = Jinja2Adapter(template_dirs=[temp_dir])
        
        adapter.add_filter("shout", lambda s: str(s).upper())
        adapter.add_filter("add_dots", lambda s: "..." + str(s) + "...")
        
        result = adapter.render("multi_filter.html", {"name": "hello"})
        
        if result != "...HELLO...":
            raise AssertionError(f"Expected '...HELLO...', got '{result}'")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_add_multiple_globals():
    """
        Test that multiple globals can be registered.
    """
    temp_dir = _create_temp_template_dir({
        "multi_global.html": "{{ app_name }} v{{ version }}"
    })
    
    try:
        adapter = Jinja2Adapter(template_dirs=[temp_dir])
        
        adapter.add_global("app_name", "MyApp")
        adapter.add_global("version", "2.0")
        
        result = adapter.render("multi_global.html", {})
        
        if result != "MyApp v2.0":
            raise AssertionError(f"Expected 'MyApp v2.0', got '{result}'")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


# =============================================================================
# 9.4 - Auto-Escaping Configuration Tests
# =============================================================================

def test_auto_escape_enabled_by_default():
    """
        Test that auto-escaping is enabled by default for HTML templates.
    """
    temp_dir = _create_temp_template_dir({
        "escape.html": "{{ content }}"
    })
    
    try:
        adapter = Jinja2Adapter(template_dirs=[temp_dir])
        
        result = adapter.render("escape.html", {"content": "<script>alert('xss')</script>"})
        
        if "<script>" in result:
            raise AssertionError("Auto-escaping should escape HTML tags")
        
        if "&lt;script&gt;" not in result:
            raise AssertionError(f"Expected escaped HTML, got '{result}'")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_auto_escape_escapes_special_characters():
    """
        Test that auto-escaping escapes all HTML special characters.
    """
    temp_dir = _create_temp_template_dir({
        "special.html": "{{ content }}"
    })
    
    try:
        adapter = Jinja2Adapter(template_dirs=[temp_dir])
        
        result = adapter.render("special.html", {"content": '&<>"'})
        
        if "&amp;" not in result:
            raise AssertionError("Should escape &")
        if "&lt;" not in result:
            raise AssertionError("Should escape <")
        if "&gt;" not in result:
            raise AssertionError("Should escape >")
        if "&#34;" not in result and "&quot;" not in result:
            raise AssertionError("Should escape \"")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_auto_escape_disabled():
    """
        Test that auto-escaping can be disabled.
    """
    temp_dir = _create_temp_template_dir({
        "no_escape.html": "{{ content }}"
    })
    
    try:
        adapter = Jinja2Adapter(
            template_dirs=[temp_dir],
            auto_escape=False,
        )
        
        result = adapter.render("no_escape.html", {"content": "<b>bold</b>"})
        
        if result != "<b>bold</b>":
            raise AssertionError(f"Expected '<b>bold</b>', got '{result}'")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_auto_escape_for_html_extension():
    """
        Test that auto-escaping is applied for .html files.
    """
    temp_dir = _create_temp_template_dir({
        "page.html": "{{ content }}"
    })
    
    try:
        adapter = Jinja2Adapter(template_dirs=[temp_dir])
        
        result = adapter.render("page.html", {"content": "<em>test</em>"})
        
        if "<em>" in result:
            raise AssertionError("HTML files should be auto-escaped")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_auto_escape_for_xml_extension():
    """
        Test that auto-escaping is applied for .xml files.
    """
    temp_dir = _create_temp_template_dir({
        "data.xml": "<root>{{ content }}</root>"
    })
    
    try:
        adapter = Jinja2Adapter(template_dirs=[temp_dir])
        
        result = adapter.render("data.xml", {"content": "<tag>value</tag>"})
        
        if "<tag>" in result and "<root>" not in result:
            raise AssertionError("XML files should be auto-escaped")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_auto_escape_safe_markup_bypass():
    """
        Test that Jinja2 Markup (safe) strings bypass auto-escaping.
    """
    from markupsafe import Markup
    
    temp_dir = _create_temp_template_dir({
        "safe.html": "{{ content }}"
    })
    
    try:
        adapter = Jinja2Adapter(template_dirs=[temp_dir])
        
        safe_content = Markup("<b>bold</b>")
        result = adapter.render("safe.html", {"content": safe_content})
        
        if result != "<b>bold</b>":
            raise AssertionError(f"Expected '<b>bold</b>', got '{result}'")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_auto_escape_with_safe_filter():
    """
        Test that the |safe filter bypasses auto-escaping.
    """
    temp_dir = _create_temp_template_dir({
        "safe_filter.html": "{{ content|safe }}"
    })
    
    try:
        adapter = Jinja2Adapter(template_dirs=[temp_dir])
        
        result = adapter.render("safe_filter.html", {"content": "<b>bold</b>"})
        
        if result != "<b>bold</b>":
            raise AssertionError(f"Expected '<b>bold</b>', got '{result}'")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


# =============================================================================
# 9.5 - Cache Management Tests
# =============================================================================

def test_clear_cache_does_not_raise():
    """
        Test that clear_cache() can be called without error.
    """
    temp_dir = _create_temp_template_dir({
        "cached.html": "Hello {{ name }}!"
    })
    
    try:
        adapter = Jinja2Adapter(template_dirs=[temp_dir])
        
        # Render to populate cache
        adapter.render("cached.html", {"name": "World"})
        
        # Clear cache should not raise
        adapter.clear_cache()
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_clear_cache_can_be_called_multiple_times():
    """
        Test that clear_cache() can be called multiple times.
    """
    temp_dir = _create_temp_template_dir({})
    
    try:
        adapter = Jinja2Adapter(template_dirs=[temp_dir])
        
        adapter.clear_cache()
        adapter.clear_cache()
        adapter.clear_cache()
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_render_works_after_clear_cache():
    """
        Test that rendering works correctly after clearing cache.
    """
    temp_dir = _create_temp_template_dir({
        "cached.html": "Hello {{ name }}!"
    })
    
    try:
        adapter = Jinja2Adapter(template_dirs=[temp_dir])
        
        # Render, clear, render again
        result1 = adapter.render("cached.html", {"name": "World"})
        adapter.clear_cache()
        result2 = adapter.render("cached.html", {"name": "World"})
        
        if result1 != result2:
            raise AssertionError(
                f"Results should match: '{result1}' != '{result2}'"
            )
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_auto_reload_configuration():
    """
        Test that auto_reload is passed to the Jinja2 environment.
    """
    temp_dir = _create_temp_template_dir({})
    
    try:
        adapter = Jinja2Adapter(
            template_dirs=[temp_dir],
            auto_reload=True,
        )
        
        if adapter._environment.auto_reload is not True:
            raise AssertionError("Environment auto_reload should be True")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_auto_reload_disabled_by_default():
    """
        Test that auto_reload is disabled by default in the environment.
    """
    temp_dir = _create_temp_template_dir({})
    
    try:
        adapter = Jinja2Adapter(template_dirs=[temp_dir])
        
        if adapter._environment.auto_reload is not False:
            raise AssertionError("Environment auto_reload should be False by default")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


# =============================================================================
# Undefined Behavior Tests
# =============================================================================

def test_silent_undefined_returns_empty_string():
    """
        Test that silent undefined behavior returns empty string.
    """
    temp_dir = _create_temp_template_dir({
        "undef.html": "Value: [{{ missing }}]"
    })
    
    try:
        adapter = Jinja2Adapter(
            template_dirs=[temp_dir],
            undefined_behavior="silent",
        )
        
        result = adapter.render("undef.html", {})
        
        if result != "Value: []":
            raise AssertionError(f"Expected 'Value: []', got '{result}'")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_strict_undefined_raises_error():
    """
        Test that strict undefined behavior raises an error.
    """
    temp_dir = _create_temp_template_dir({
        "strict.html": "{{ missing_var }}"
    })
    
    try:
        adapter = Jinja2Adapter(
            template_dirs=[temp_dir],
            undefined_behavior="strict",
        )
        
        try:
            adapter.render("strict.html", {})
            raise AssertionError("Should raise TemplateError for undefined variable")
        except TemplateError:
            pass  # Expected
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


# =============================================================================
# Environment Cache Size Tests
# =============================================================================

def test_cache_size_zero_disables_environment_cache():
    """
        Test that cache_size=0 reaches the Jinja2 Environment, which then keeps
        no compiled-template cache (what a disabled TemplateConfig cache asks for).
    """
    temp_dir = _create_temp_template_dir({})
    
    try:
        adapter = Jinja2Adapter(template_dirs=[temp_dir], cache_size=0)
        
        if adapter._environment.cache is not None:
            raise AssertionError(
                f"Expected no Jinja2 environment cache for cache_size=0, got {adapter._environment.cache!r}"
            )
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_cache_size_sets_environment_cache_capacity():
    """
        Test that a positive cache_size becomes the Jinja2 Environment's cache
        capacity.
    """
    temp_dir = _create_temp_template_dir({})
    
    try:
        adapter = Jinja2Adapter(template_dirs=[temp_dir], cache_size=7)
        
        capacity = adapter._environment.cache.capacity
        if capacity != 7:
            raise AssertionError(f"Expected environment cache capacity 7, got {capacity}")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_cache_size_zero_reloads_modified_template():
    """
        Test that with cache_size=0 a modified template is picked up on the
        next render.
    """
    temp_dir = _create_temp_template_dir({
        "page.html": "first"
    })
    
    try:
        adapter = Jinja2Adapter(template_dirs=[temp_dir], cache_size=0)
        
        first = adapter.render("page.html", {})
        
        with open(os.path.join(temp_dir, "page.html"), "w", encoding="utf-8") as f:
            f.write("second")
        
        second = adapter.render("page.html", {})
        
        if first != "first" or second != "second":
            raise AssertionError(f"Expected 'first' then 'second', got {first!r} then {second!r}")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


# =============================================================================
# compile_template() / render_compiled*() Tests
# =============================================================================

def test_compile_template_returns_compiled_template():
    """
        Test that compile_template() returns a Jinja2CompiledTemplate that
        carries the name, filename and source.
    """
    temp_dir = _create_temp_template_dir({})
    
    try:
        adapter = Jinja2Adapter(template_dirs=[temp_dir])
        
        compiled = adapter.compile_template(
            "Hello {{ name }}!",
            template_name="hello.html",
            filename="/templates/hello.html"
        )
        
        if not isinstance(compiled, Jinja2CompiledTemplate):
            raise AssertionError(f"Expected Jinja2CompiledTemplate, got {type(compiled)}")
        
        if compiled.template_name != "hello.html":
            raise AssertionError(f"Expected template_name 'hello.html', got {compiled.template_name!r}")
        
        if compiled.filename != "/templates/hello.html":
            raise AssertionError(f"Expected the filename to be kept, got {compiled.filename!r}")
        
        if compiled.source != "Hello {{ name }}!":
            raise AssertionError(f"Expected the source to be kept, got {compiled.source!r}")
        
        if compiled.async_template is not None:
            raise AssertionError("The async variant should not be compiled until it is needed")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_render_compiled_renders_and_escapes():
    """
        Test that render_compiled() renders a compiled .html template with
        auto-escaping, like render() does for the same template.
    """
    temp_dir = _create_temp_template_dir({})
    
    try:
        adapter = Jinja2Adapter(template_dirs=[temp_dir])
        
        compiled = adapter.compile_template("<p>{{ value }}</p>", template_name="page.html")
        result = adapter.render_compiled(compiled, {"value": "<b>"})
        
        if result != "<p>&lt;b&gt;</p>":
            raise AssertionError(f"Expected '<p>&lt;b&gt;</p>', got {result!r}")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_render_compiled_resolves_extends_through_environment():
    """
        Test that a compiled template extends a parent the environment loads
        from the template directories.
    """
    temp_dir = _create_temp_template_dir({
        "base.html": "<main>{% block content %}{% endblock %}</main>"
    })
    
    try:
        adapter = Jinja2Adapter(template_dirs=[temp_dir])
        
        source = '{% extends "base.html" %}{% block content %}{{ title }}{% endblock %}'
        compiled = adapter.compile_template(source, template_name="child.html")
        result = adapter.render_compiled(compiled, {"title": "Home"})
        
        if result != "<main>Home</main>":
            raise AssertionError(f"Expected '<main>Home</main>', got {result!r}")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_render_compiled_raises_template_not_found_for_missing_parent():
    """
        Test that a missing extends target raises TemplateNotFoundError.
    """
    temp_dir = _create_temp_template_dir({})
    
    try:
        adapter = Jinja2Adapter(template_dirs=[temp_dir])
        
        compiled = adapter.compile_template('{% extends "missing.html" %}', template_name="child.html")
        
        raised = None
        try:
            adapter.render_compiled(compiled, {})
        except TemplateNotFoundError as exc:
            raised = exc
        
        if raised is None:
            raise AssertionError("Expected TemplateNotFoundError for a missing parent template")
        
        if raised.template_name != "missing.html":
            raise AssertionError(f"Expected the missing template's name, got {raised.template_name!r}")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_compile_template_syntax_error_names_template():
    """
        Test that a syntax error while compiling raises TemplateError naming
        the template.
    """
    temp_dir = _create_temp_template_dir({})
    
    try:
        adapter = Jinja2Adapter(template_dirs=[temp_dir])
        
        raised = None
        try:
            adapter.compile_template("{% if %}", template_name="broken.html")
        except TemplateError as exc:
            raised = exc
        
        if raised is None:
            raise AssertionError("Expected TemplateError for a syntax error")
        
        if "broken.html" not in str(raised):
            raise AssertionError(f"Expected the template name in the error, got {raised}")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_render_compiled_async_uses_async_environment():
    """
        Test that render_compiled_async() renders with the async environment
        (an async filter is awaited) and keeps the async variant for reuse.
    """
    temp_dir = _create_temp_template_dir({})
    
    try:
        adapter = Jinja2Adapter(template_dirs=[temp_dir])
        
        async def shout(value):
            return str(value).upper()
        
        adapter.add_filter("shout", shout)
        
        compiled = adapter.compile_template("{{ name|shout }}", template_name="async.html")
        
        first = asyncio.run(adapter.render_compiled_async(compiled, {"name": "one"}))
        async_template = compiled.async_template
        second = asyncio.run(adapter.render_compiled_async(compiled, {"name": "two"}))
        
        if first != "ONE" or second != "TWO":
            raise AssertionError(f"Expected 'ONE' and 'TWO', got {first!r} and {second!r}")
        
        if async_template is None or compiled.async_template is not async_template:
            raise AssertionError("The async variant should be compiled once and reused")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_render_compiled_stream_yields_chunks():
    """
        Test that render_compiled_stream() yields the rendered output.
    """
    temp_dir = _create_temp_template_dir({})
    
    try:
        adapter = Jinja2Adapter(template_dirs=[temp_dir])
        
        compiled = adapter.compile_template("{% for i in items %}{{ i }},{% endfor %}", template_name="list.html")
        chunks = list(adapter.render_compiled_stream(compiled, {"items": [1, 2, 3]}))
        result = "".join(chunks)
        
        if result != "1,2,3,":
            raise AssertionError(f"Expected '1,2,3,', got {result!r}")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


# =============================================================================
# Export Tests
# =============================================================================

def test_jinja2_adapter_exported_from_package():
    """
        Test that Jinja2Adapter is exported from the templating package.
    """
    from ccai.webworks.templating import Jinja2Adapter as ExportedAdapter
    
    if ExportedAdapter is not Jinja2Adapter:
        raise AssertionError("Jinja2Adapter should be exported from package")
    
    return


# =============================================================================
# clear_cache() empties Jinja2's own template cache
# =============================================================================

def test_clear_cache_empties_environment_cache():
    """
        Test that clear_cache() removes the templates Jinja2 cached by name.
    """
    temp_dir = _create_temp_template_dir({
        "page.html": "Page"
    })
    
    try:
        adapter = Jinja2Adapter(template_dirs=[temp_dir])
        adapter.render("page.html", {})
        
        if len(adapter._environment.cache) != 1:
            raise AssertionError("The rendered template should be in the Jinja2 cache")
        
        adapter.clear_cache()
        
        if len(adapter._environment.cache) != 0:
            raise AssertionError("clear_cache() should empty the Jinja2 cache")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_clear_cache_reloads_modified_parent_template():
    """
        Test that after clear_cache() a changed parent template is re-read
        even though auto_reload is off.
    """
    temp_dir = _create_temp_template_dir({
        "base.html": "old {% block body %}{% endblock %}",
        "child.html": "{% extends 'base.html' %}{% block body %}child{% endblock %}"
    })
    
    try:
        adapter = Jinja2Adapter(template_dirs=[temp_dir], auto_reload=False)
        
        first = adapter.render("child.html", {})
        
        with open(os.path.join(temp_dir, "base.html"), "w", encoding="utf-8") as f:
            f.write("new {% block body %}{% endblock %}")
        
        stale = adapter.render("child.html", {})
        adapter.clear_cache()
        fresh = adapter.render("child.html", {})
        
        if first != "old child" or stale != "old child":
            raise AssertionError(f"Expected the cached parent before clear_cache(), got {first!r} / {stale!r}")
        
        if fresh != "new child":
            raise AssertionError(f"Expected 'new child' after clear_cache(), got {fresh!r}")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_clear_cache_with_cache_disabled_does_not_raise():
    """
        Test that clear_cache() works when Jinja2 has no cache (size 0).
    """
    temp_dir = _create_temp_template_dir({})
    
    try:
        adapter = Jinja2Adapter(template_dirs=[temp_dir], cache_size=0)
        adapter.clear_cache()
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


# =============================================================================
# has_filter()
# =============================================================================

def test_has_filter_reports_jinja2_builtin_filter():
    """
        Test that has_filter() is True for a filter Jinja2 ships.
    """
    temp_dir = _create_temp_template_dir({})
    
    try:
        adapter = Jinja2Adapter(template_dirs=[temp_dir])
        
        if adapter.has_filter("escape") is not True:
            raise AssertionError("has_filter('escape') should be True")
        
        if adapter.has_filter("no_such_filter") is not False:
            raise AssertionError("has_filter('no_such_filter') should be False")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_has_filter_reports_added_filter():
    """
        Test that has_filter() is True for a filter added with add_filter().
    """
    temp_dir = _create_temp_template_dir({})
    
    try:
        adapter = Jinja2Adapter(template_dirs=[temp_dir])
        adapter.add_filter("shout", lambda value: str(value).upper())
        
        if adapter.has_filter("shout") is not True:
            raise AssertionError("has_filter('shout') should be True after add_filter()")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


# =============================================================================
# Native Jinja2 environment options
# =============================================================================

def test_init_passes_environment_options_to_jinja2():
    """
        Test that extra keyword options are set on the Jinja2 environment.
    """
    temp_dir = _create_temp_template_dir({})
    
    try:
        adapter = Jinja2Adapter(template_dirs=[temp_dir], trim_blocks=True, lstrip_blocks=True)
        
        output = adapter.render_string("  {% if True %}\nyes\n  {% endif %}\n", {})
        
        if output != "yes\n":
            raise AssertionError(f"Expected 'yes\\n' with trim_blocks and lstrip_blocks, got {output!r}")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_init_environment_options_apply_to_async_environment():
    """
        Test that extra keyword options also reach the async environment.
    """
    temp_dir = _create_temp_template_dir({})
    
    try:
        adapter = Jinja2Adapter(template_dirs=[temp_dir], trim_blocks=True)
        
        if adapter._async_env.trim_blocks is not True:
            raise AssertionError("trim_blocks should be set on the async environment")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_init_rejects_reserved_environment_option():
    """
        Test that an option the adapter sets itself cannot be passed again.
    """
    temp_dir = _create_temp_template_dir({})
    
    try:
        try:
            Jinja2Adapter(template_dirs=[temp_dir], autoescape=False)
            raise AssertionError("Expected TemplateConfigurationError for a reserved option")
        except TemplateConfigurationError:
            pass  # Expected
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_init_rejects_unknown_environment_option():
    """
        Test that an option Jinja2 does not know raises
        TemplateConfigurationError.
    """
    temp_dir = _create_temp_template_dir({})
    
    try:
        try:
            Jinja2Adapter(template_dirs=[temp_dir], no_such_option=True)
            raise AssertionError("Expected TemplateConfigurationError for an unknown option")
        except TemplateConfigurationError:
            pass  # Expected
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


# =============================================================================
# Engine exceptions are mapped to the specific templating exceptions
# =============================================================================

def test_render_raises_template_syntax_error_with_name_and_line():
    """
        Test that a syntax error raises TemplateSyntaxError carrying the
        template name and line number.
    """
    temp_dir = _create_temp_template_dir({
        "broken.html": "line one\n{% if %}\n"
    })
    
    try:
        adapter = Jinja2Adapter(template_dirs=[temp_dir])
        
        try:
            adapter.render("broken.html", {})
            raise AssertionError("Expected TemplateSyntaxError")
        except TemplateSyntaxError as exc:
            if exc.template_name != "broken.html":
                raise AssertionError(f"Expected template_name 'broken.html', got {exc.template_name!r}")
            if exc.line_number != 2:
                raise AssertionError(f"Expected line_number 2, got {exc.line_number!r}")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_render_string_raises_template_syntax_error():
    """
        Test that render_string() raises TemplateSyntaxError for bad syntax.
    """
    temp_dir = _create_temp_template_dir({})
    
    try:
        adapter = Jinja2Adapter(template_dirs=[temp_dir])
        
        try:
            adapter.render_string("{% for %}", {})
            raise AssertionError("Expected TemplateSyntaxError")
        except TemplateSyntaxError as exc:
            if exc.line_number != 1:
                raise AssertionError(f"Expected line_number 1, got {exc.line_number!r}")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_compile_template_raises_template_syntax_error():
    """
        Test that compile_template() raises TemplateSyntaxError naming the
        template.
    """
    temp_dir = _create_temp_template_dir({})
    
    try:
        adapter = Jinja2Adapter(template_dirs=[temp_dir])
        
        try:
            adapter.compile_template("{% endif %}", template_name="page.html")
            raise AssertionError("Expected TemplateSyntaxError")
        except TemplateSyntaxError as exc:
            if exc.template_name != "page.html":
                raise AssertionError(f"Expected template_name 'page.html', got {exc.template_name!r}")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_render_wraps_python_exception_in_template_render_error():
    """
        Test that an ordinary exception raised by template code is wrapped
        in TemplateRenderError with the template name and line.
    """
    temp_dir = _create_temp_template_dir({
        "divide.html": "first\nsecond\n{{ 1 / zero }}\n"
    })
    
    try:
        adapter = Jinja2Adapter(template_dirs=[temp_dir])
        
        try:
            adapter.render("divide.html", {"zero": 0})
            raise AssertionError("Expected TemplateRenderError")
        except TemplateRenderError as exc:
            if exc.template_name != "divide.html":
                raise AssertionError(f"Expected template_name 'divide.html', got {exc.template_name!r}")
            if exc.line_number != 3:
                raise AssertionError(f"Expected line_number 3, got {exc.line_number!r}")
            if not isinstance(exc.__cause__, ZeroDivisionError):
                raise AssertionError(f"Expected the ZeroDivisionError as the cause, got {exc.__cause__!r}")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_render_string_wraps_python_exception_in_template_render_error():
    """
        Test that render_string() wraps an ordinary exception.
    """
    temp_dir = _create_temp_template_dir({})
    
    try:
        adapter = Jinja2Adapter(template_dirs=[temp_dir])
        
        try:
            adapter.render_string("{{ 1 / 0 }}", {})
            raise AssertionError("Expected TemplateRenderError")
        except TemplateRenderError as exc:
            if exc.line_number != 1:
                raise AssertionError(f"Expected line_number 1, got {exc.line_number!r}")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_render_compiled_wraps_python_exception_in_template_render_error():
    """
        Test that render_compiled() wraps an ordinary exception.
    """
    temp_dir = _create_temp_template_dir({})
    
    try:
        adapter = Jinja2Adapter(template_dirs=[temp_dir])
        compiled = adapter.compile_template("{{ 1 / 0 }}", template_name="page.html")
        
        try:
            adapter.render_compiled(compiled, {})
            raise AssertionError("Expected TemplateRenderError")
        except TemplateRenderError as exc:
            if exc.template_name != "page.html":
                raise AssertionError(f"Expected template_name 'page.html', got {exc.template_name!r}")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_render_stream_wraps_python_exception_in_template_render_error():
    """
        Test that render_stream() wraps an ordinary exception.
    """
    temp_dir = _create_temp_template_dir({
        "divide.html": "{{ 1 / 0 }}"
    })
    
    try:
        adapter = Jinja2Adapter(template_dirs=[temp_dir])
        
        try:
            list(adapter.render_stream("divide.html", {}))
            raise AssertionError("Expected TemplateRenderError")
        except TemplateRenderError:
            pass  # Expected
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_render_async_wraps_python_exception_in_template_render_error():
    """
        Test that render_async() wraps an ordinary exception.
    """
    temp_dir = _create_temp_template_dir({
        "divide.html": "{{ 1 / 0 }}"
    })
    
    try:
        adapter = Jinja2Adapter(template_dirs=[temp_dir])
        
        try:
            asyncio.run(adapter.render_async("divide.html", {}))
            raise AssertionError("Expected TemplateRenderError")
        except TemplateRenderError:
            pass  # Expected
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_strict_undefined_raises_undefined_variable_error():
    """
        Test that strict mode raises UndefinedVariableError naming the
        variable and the template.
    """
    temp_dir = _create_temp_template_dir({
        "strict.html": "ok\n{{ missing_var }}"
    })
    
    try:
        adapter = Jinja2Adapter(template_dirs=[temp_dir], undefined_behavior="strict")
        
        try:
            adapter.render("strict.html", {})
            raise AssertionError("Expected UndefinedVariableError")
        except UndefinedVariableError as exc:
            if exc.variable_name != "missing_var":
                raise AssertionError(f"Expected variable_name 'missing_var', got {exc.variable_name!r}")
            if exc.template_name != "strict.html":
                raise AssertionError(f"Expected template_name 'strict.html', got {exc.template_name!r}")
            if exc.line_number != 2:
                raise AssertionError(f"Expected line_number 2, got {exc.line_number!r}")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_silent_undefined_attribute_raises_template_render_error():
    """
        Test that, outside strict mode, using an attribute of an undefined
        variable raises TemplateRenderError naming the variable.
    """
    temp_dir = _create_temp_template_dir({})
    
    try:
        adapter = Jinja2Adapter(template_dirs=[temp_dir], undefined_behavior="silent")
        
        try:
            adapter.render_string("{{ user.name }}", {})
            raise AssertionError("Expected TemplateRenderError")
        except UndefinedVariableError:
            raise AssertionError("UndefinedVariableError is reserved for strict mode")
        except TemplateRenderError as exc:
            if exc.variable_name != "user":
                raise AssertionError(f"Expected variable_name 'user', got {exc.variable_name!r}")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_unknown_filter_raises_template_filter_not_found_error():
    """
        Test that a template using an unregistered filter raises
        TemplateFilterNotFoundError with the filter name.
    """
    temp_dir = _create_temp_template_dir({})
    
    try:
        adapter = Jinja2Adapter(template_dirs=[temp_dir])
        
        try:
            adapter.render_string("{{ value|no_such_filter }}", {"value": 1})
            raise AssertionError("Expected TemplateFilterNotFoundError")
        except TemplateFilterNotFoundError as exc:
            if exc.filter_name != "no_such_filter":
                raise AssertionError(f"Expected filter_name 'no_such_filter', got {exc.filter_name!r}")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_render_error_in_included_template_names_that_template():
    """
        Test that an error raised inside an included template is reported
        against the included template and its line.
    """
    temp_dir = _create_temp_template_dir({
        "outer.html": "outer\n{% include 'inner.html' %}",
        "inner.html": "inner\n\n{{ 1 / 0 }}"
    })
    
    try:
        adapter = Jinja2Adapter(template_dirs=[temp_dir])
        
        try:
            adapter.render("outer.html", {})
            raise AssertionError("Expected TemplateRenderError")
        except TemplateRenderError as exc:
            if exc.template_name != "inner.html":
                raise AssertionError(f"Expected template_name 'inner.html', got {exc.template_name!r}")
            if exc.line_number != 3:
                raise AssertionError(f"Expected line_number 3, got {exc.line_number!r}")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return
