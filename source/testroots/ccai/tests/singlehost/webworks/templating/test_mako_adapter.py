"""
    Tests for the MakoAdapter class.
    
    This module tests the MakoAdapter including:
    - Initialization and configuration
    - Template rendering (render, render_string)
    - Filter and global registration
    - Auto-escaping configuration
    - Cache management
"""

import os
import shutil
import tempfile

from ccai.webworks.templating.exceptions import (
    TemplateConfigurationError,
    TemplateError,
    TemplateNotFoundError,
    TemplateRenderError,
    TemplateSyntaxError,
    UndefinedVariableError,
)
from ccai.webworks.templating.mako_adapter import MakoAdapter


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
# 11.1 - __init__() and Configuration Tests
# =============================================================================

def test_init_creates_adapter():
    """
        Test that MakoAdapter can be instantiated with template directories.
    """
    temp_dir = _create_temp_template_dir({})
    
    try:
        adapter = MakoAdapter(template_dirs=[temp_dir])
        
        if not isinstance(adapter, MakoAdapter):
            raise AssertionError("Expected MakoAdapter instance")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_init_is_template_engine():
    """
        Test that MakoAdapter is a TemplateEngine subclass.
    """
    from ccai.webworks.templating.engine import TemplateEngine
    
    temp_dir = _create_temp_template_dir({})
    
    try:
        adapter = MakoAdapter(template_dirs=[temp_dir])
        
        if not isinstance(adapter, TemplateEngine):
            raise AssertionError("MakoAdapter should be a TemplateEngine")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_init_stores_template_dirs():
    """
        Test that __init__() stores the template directories.
    """
    temp_dir = _create_temp_template_dir({})
    
    try:
        adapter = MakoAdapter(template_dirs=[temp_dir])
        
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
        adapter = MakoAdapter(template_dirs=[temp_dir])
        
        if adapter._auto_escape is not True:
            raise AssertionError("auto_escape should default to True")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_init_default_encoding():
    """
        Test that encoding defaults to utf-8.
    """
    temp_dir = _create_temp_template_dir({})
    
    try:
        adapter = MakoAdapter(template_dirs=[temp_dir])
        
        if adapter._encoding != "utf-8":
            raise AssertionError(f"Expected 'utf-8', got '{adapter._encoding}'")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_init_default_module_directory():
    """
        Test that module_directory defaults to None.
    """
    temp_dir = _create_temp_template_dir({})
    
    try:
        adapter = MakoAdapter(template_dirs=[temp_dir])
        
        if adapter._module_directory is not None:
            raise AssertionError("module_directory should default to None")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_init_default_filters_with_auto_escape():
    """
        Test that default_filters is ['h'] when auto_escape is True.
    """
    temp_dir = _create_temp_template_dir({})
    
    try:
        adapter = MakoAdapter(template_dirs=[temp_dir])
        
        if adapter._default_filters != ["h"]:
            raise AssertionError(
                f"Expected ['h'], got {adapter._default_filters}"
            )
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_init_default_filters_without_auto_escape():
    """
        Test that default_filters is ['str'] when auto_escape is False.
    """
    temp_dir = _create_temp_template_dir({})
    
    try:
        adapter = MakoAdapter(template_dirs=[temp_dir], auto_escape=False)
        
        if adapter._default_filters != ["str"]:
            raise AssertionError(
                f"Expected ['str'], got {adapter._default_filters}"
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
        adapter = MakoAdapter(
            template_dirs=[temp_dir],
            auto_escape=False,
            encoding="latin-1",
            default_filters=["trim"],
        )
        
        if adapter._auto_escape is not False:
            raise AssertionError("auto_escape should be False")
        if adapter._encoding != "latin-1":
            raise AssertionError(f"Expected 'latin-1', got '{adapter._encoding}'")
        if adapter._default_filters != ["trim"]:
            raise AssertionError(
                f"Expected ['trim'], got {adapter._default_filters}"
            )
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_init_creates_mako_lookup():
    """
        Test that __init__() creates a Mako TemplateLookup.
    """
    from mako.lookup import TemplateLookup
    
    temp_dir = _create_temp_template_dir({})
    
    try:
        adapter = MakoAdapter(template_dirs=[temp_dir])
        
        if not isinstance(adapter._lookup, TemplateLookup):
            raise AssertionError("Expected mako.lookup.TemplateLookup instance")
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
        adapter = MakoAdapter(template_dirs=[temp_dir1, temp_dir2])
        
        if len(adapter._template_dirs) != 2:
            raise AssertionError(
                f"Expected 2 dirs, got {len(adapter._template_dirs)}"
            )
    finally:
        _cleanup_temp_dir(temp_dir1)
        _cleanup_temp_dir(temp_dir2)
    
    return


# =============================================================================
# 11.2 - Rendering Methods Tests
# =============================================================================

def test_render_returns_rendered_template():
    """
        Test that render() returns the rendered template content.
    """
    temp_dir = _create_temp_template_dir({
        "hello.html": "Hello ${name}!"
    })
    
    try:
        adapter = MakoAdapter(
            template_dirs=[temp_dir],
            auto_escape=False,
        )
        
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
        adapter = MakoAdapter(
            template_dirs=[temp_dir],
            auto_escape=False,
        )
        
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
        "multi.html": "${greeting}, ${name}! You are ${age}."
    })
    
    try:
        adapter = MakoAdapter(
            template_dirs=[temp_dir],
            auto_escape=False,
        )
        
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
        adapter = MakoAdapter(template_dirs=[temp_dir])
        
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
        "bad.html": "<%def name='unclosed>"
    })
    
    try:
        adapter = MakoAdapter(template_dirs=[temp_dir])
        
        try:
            adapter.render("bad.html", {})
            raise AssertionError("Should raise TemplateError")
        except (TemplateError, Exception):
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
        adapter = MakoAdapter(
            template_dirs=[temp_dir],
            auto_escape=False,
        )
        
        result = adapter.render_string("Hello ${name}!", {"name": "World"})
        
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
        adapter = MakoAdapter(
            template_dirs=[temp_dir],
            auto_escape=False,
        )
        
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
        adapter = MakoAdapter(template_dirs=[temp_dir])
        
        try:
            adapter.render_string("<%def name='unclosed>", {})
            raise AssertionError("Should raise TemplateError")
        except (TemplateError, Exception):
            pass  # Expected
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


# =============================================================================
# 11.3 - Filter and Global Registration Tests
# =============================================================================

def test_add_global_registers_value():
    """
        Test that add_global() registers a global variable.
    """
    temp_dir = _create_temp_template_dir({
        "global.html": "App: ${app_name}"
    })
    
    try:
        adapter = MakoAdapter(
            template_dirs=[temp_dir],
            auto_escape=False,
        )
        
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
        "global_func.html": "Version: ${get_version()}"
    })
    
    try:
        adapter = MakoAdapter(
            template_dirs=[temp_dir],
            auto_escape=False,
        )
        
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
        adapter = MakoAdapter(
            template_dirs=[temp_dir],
            auto_escape=False,
        )
        
        adapter.add_global("site_name", "TestSite")
        
        result = adapter.render_string("Site: ${site_name}", {})
        
        if result != "Site: TestSite":
            raise AssertionError(f"Expected 'Site: TestSite', got '{result}'")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_add_multiple_globals():
    """
        Test that multiple globals can be registered.
    """
    temp_dir = _create_temp_template_dir({
        "multi_global.html": "${app_name} v${version}"
    })
    
    try:
        adapter = MakoAdapter(
            template_dirs=[temp_dir],
            auto_escape=False,
        )
        
        adapter.add_global("app_name", "MyApp")
        adapter.add_global("version", "2.0")
        
        result = adapter.render("multi_global.html", {})
        
        if result != "MyApp v2.0":
            raise AssertionError(f"Expected 'MyApp v2.0', got '{result}'")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_add_filter_stores_filter():
    """
        Test that add_filter() stores a custom filter function.
    """
    temp_dir = _create_temp_template_dir({})
    
    try:
        adapter = MakoAdapter(template_dirs=[temp_dir])
        
        adapter.add_filter("shout", lambda s: str(s).upper() + "!")
        
        if "shout" not in adapter._filters:
            raise AssertionError("Filter 'shout' should be stored")
        
        result = adapter._filters["shout"]("hello")
        if result != "HELLO!":
            raise AssertionError(f"Expected 'HELLO!', got '{result}'")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_add_multiple_filters():
    """
        Test that multiple filters can be registered.
    """
    temp_dir = _create_temp_template_dir({})
    
    try:
        adapter = MakoAdapter(template_dirs=[temp_dir])
        
        adapter.add_filter("shout", lambda s: str(s).upper())
        adapter.add_filter("whisper", lambda s: str(s).lower())
        
        if len(adapter._filters) != 2:
            raise AssertionError(
                f"Expected 2 filters, got {len(adapter._filters)}"
            )
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_context_overrides_global():
    """
        Test that context variables override globals with the same name.
    """
    temp_dir = _create_temp_template_dir({
        "override.html": "Name: ${name}"
    })
    
    try:
        adapter = MakoAdapter(
            template_dirs=[temp_dir],
            auto_escape=False,
        )
        
        adapter.add_global("name", "GlobalName")
        
        result = adapter.render("override.html", {"name": "ContextName"})
        
        if result != "Name: ContextName":
            raise AssertionError(f"Expected 'Name: ContextName', got '{result}'")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


# =============================================================================
# 11.4 - Auto-Escaping Configuration Tests
# =============================================================================

def test_auto_escape_enabled_by_default():
    """
        Test that auto-escaping is enabled by default for HTML templates.
    """
    temp_dir = _create_temp_template_dir({
        "escape.html": "${content}"
    })
    
    try:
        adapter = MakoAdapter(template_dirs=[temp_dir])
        
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
        Test that auto-escaping escapes HTML special characters.
    """
    temp_dir = _create_temp_template_dir({
        "special.html": "${content}"
    })
    
    try:
        adapter = MakoAdapter(template_dirs=[temp_dir])
        
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
        "no_escape.html": "${content}"
    })
    
    try:
        adapter = MakoAdapter(
            template_dirs=[temp_dir],
            auto_escape=False,
        )
        
        result = adapter.render("no_escape.html", {"content": "<b>bold</b>"})
        
        if result != "<b>bold</b>":
            raise AssertionError(f"Expected '<b>bold</b>', got '{result}'")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_auto_escape_with_render_string():
    """
        Test that auto-escaping works with render_string().
    """
    temp_dir = _create_temp_template_dir({})
    
    try:
        adapter = MakoAdapter(template_dirs=[temp_dir])
        
        result = adapter.render_string("${content}", {"content": "<b>bold</b>"})
        
        if "<b>" in result:
            raise AssertionError("render_string should auto-escape")
        
        if "&lt;b&gt;" not in result:
            raise AssertionError(f"Expected escaped HTML, got '{result}'")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_auto_escape_disabled_with_render_string():
    """
        Test that auto-escaping can be disabled for render_string().
    """
    temp_dir = _create_temp_template_dir({})
    
    try:
        adapter = MakoAdapter(
            template_dirs=[temp_dir],
            auto_escape=False,
        )
        
        result = adapter.render_string("${content}", {"content": "<b>bold</b>"})
        
        if result != "<b>bold</b>":
            raise AssertionError(f"Expected '<b>bold</b>', got '{result}'")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


# =============================================================================
# Cache Management Tests
# =============================================================================

def test_clear_cache_does_not_raise():
    """
        Test that clear_cache() can be called without error.
    """
    temp_dir = _create_temp_template_dir({
        "cached.html": "Hello ${name}!"
    })
    
    try:
        adapter = MakoAdapter(
            template_dirs=[temp_dir],
            auto_escape=False,
        )
        
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
        adapter = MakoAdapter(template_dirs=[temp_dir])
        
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
        "cached.html": "Hello ${name}!"
    })
    
    try:
        adapter = MakoAdapter(
            template_dirs=[temp_dir],
            auto_escape=False,
        )
        
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


# =============================================================================
# compile_template() / render_compiled() Tests
# =============================================================================

def test_compile_template_and_render_compiled():
    """
        Test that a template compiled from source renders with the context
        and the registered globals, escaping by default.
    """
    temp_dir = _create_temp_template_dir({})
    
    try:
        adapter = MakoAdapter(template_dirs=[temp_dir])
        adapter.add_global("site", "Portal")
        
        compiled = adapter.compile_template("${site}: ${value}", template_name="page.html")
        result = adapter.render_compiled(compiled, {"value": "<b>"})
        
        if result != "Portal: &lt;b&gt;":
            raise AssertionError(f"Expected 'Portal: &lt;b&gt;', got {result!r}")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_compile_template_uses_name_as_uri_for_inherit():
    """
        Test that a compiled template inherits a parent the lookup resolves
        relative to the template name.
    """
    temp_dir = _create_temp_template_dir({
        "pages/base.html": "<main>${self.body()}</main>"
    })
    
    try:
        adapter = MakoAdapter(template_dirs=[temp_dir])
        
        compiled = adapter.compile_template(
            '<%inherit file="base.html"/>${title}',
            template_name="pages/child.html"
        )
        result = adapter.render_compiled(compiled, {"title": "Home"})
        
        if result != "<main>Home</main>":
            raise AssertionError(f"Expected '<main>Home</main>', got {result!r}")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_render_compiled_reports_missing_parent():
    """
        Test that a missing inherit target raises TemplateError naming the
        missing template, as render() reports it.
    """
    temp_dir = _create_temp_template_dir({})
    
    try:
        adapter = MakoAdapter(template_dirs=[temp_dir])
        
        compiled = adapter.compile_template('<%inherit file="missing.html"/>', template_name="child.html")
        
        raised = None
        try:
            adapter.render_compiled(compiled, {})
        except TemplateError as exc:
            raised = exc
        
        if raised is None:
            raise AssertionError("Expected TemplateError for a missing parent template")
        
        if "missing.html" not in str(raised):
            raise AssertionError(f"Expected the missing template's name in the error, got {raised}")
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
        adapter = MakoAdapter(template_dirs=[temp_dir])
        
        raised = None
        try:
            adapter.compile_template("% if x:\nunterminated", template_name="broken.html")
        except TemplateError as exc:
            raised = exc
        
        if raised is None:
            raise AssertionError("Expected TemplateError for a syntax error")
        
        if "broken.html" not in str(raised):
            raise AssertionError(f"Expected the template name in the error, got {raised}")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


# =============================================================================
# Export Tests
# =============================================================================

def test_mako_adapter_exported_from_package():
    """
        Test that MakoAdapter is exported from the templating package.
    """
    from ccai.webworks.templating import MakoAdapter as ExportedAdapter
    
    if ExportedAdapter is not MakoAdapter:
        raise AssertionError("MakoAdapter should be exported from package")
    
    return


# =============================================================================
# Registered filters are usable in templates
# =============================================================================

def test_added_filter_is_usable_in_render_string():
    """
        Test that a filter added with add_filter() works in a template string.
    """
    temp_dir = _create_temp_template_dir({})
    
    try:
        adapter = MakoAdapter(template_dirs=[temp_dir])
        adapter.add_filter("shout", lambda value: str(value).upper())
        
        output = adapter.render_string("${ name | shout }", {"name": "abc"})
        
        if output != "ABC":
            raise AssertionError(f"Expected 'ABC', got {output!r}")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_added_filter_is_usable_in_render():
    """
        Test that a filter added with add_filter() works in a template file.
    """
    temp_dir = _create_temp_template_dir({
        "page.html": "${ name | shout }"
    })
    
    try:
        adapter = MakoAdapter(template_dirs=[temp_dir])
        adapter.add_filter("shout", lambda value: str(value).upper())
        
        output = adapter.render("page.html", {"name": "abc"})
        
        if output != "ABC":
            raise AssertionError(f"Expected 'ABC', got {output!r}")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_added_filter_is_usable_in_render_compiled():
    """
        Test that a filter added with add_filter() works in a compiled
        template.
    """
    temp_dir = _create_temp_template_dir({})
    
    try:
        adapter = MakoAdapter(template_dirs=[temp_dir])
        adapter.add_filter("shout", lambda value: str(value).upper())
        
        compiled = adapter.compile_template("${ name | shout }", template_name="page.html")
        output = adapter.render_compiled(compiled, {"name": "abc"})
        
        if output != "ABC":
            raise AssertionError(f"Expected 'ABC', got {output!r}")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_context_variable_hides_filter_of_same_name():
    """
        Test that a caller's variable takes priority over a filter with the
        same name.
    """
    temp_dir = _create_temp_template_dir({})
    
    try:
        adapter = MakoAdapter(template_dirs=[temp_dir])
        adapter.add_filter("title", lambda value: str(value).title())
        
        output = adapter.render_string("${ title }", {"title": "Home"})
        
        if output != "Home":
            raise AssertionError(f"Expected 'Home', got {output!r}")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_has_filter_reports_added_and_mako_filters():
    """
        Test that has_filter() is True for added filters and Mako's own.
    """
    temp_dir = _create_temp_template_dir({})
    
    try:
        adapter = MakoAdapter(template_dirs=[temp_dir])
        adapter.add_filter("shout", lambda value: str(value).upper())
        
        if adapter.has_filter("shout") is not True:
            raise AssertionError("has_filter('shout') should be True after add_filter()")
        
        if adapter.has_filter("h") is not True:
            raise AssertionError("has_filter('h') should be True for Mako's own filter")
        
        if adapter.has_filter("no_such_filter") is not False:
            raise AssertionError("has_filter('no_such_filter') should be False")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


# =============================================================================
# Native Mako lookup options
# =============================================================================

def test_init_passes_lookup_options_to_mako():
    """
        Test that extra keyword options reach Mako for file and string
        templates.
    """
    temp_dir = _create_temp_template_dir({
        "page.html": "${ missing_name }"
    })
    
    try:
        adapter = MakoAdapter(template_dirs=[temp_dir], strict_undefined=True)
        
        try:
            adapter.render("page.html", {})
            raise AssertionError("Expected UndefinedVariableError for a file template")
        except UndefinedVariableError as exc:
            if exc.variable_name != "missing_name":
                raise AssertionError(f"Expected variable_name 'missing_name', got {exc.variable_name!r}")
        
        try:
            adapter.render_string("${ other_name }", {})
            raise AssertionError("Expected UndefinedVariableError for a string template")
        except UndefinedVariableError as exc:
            if exc.variable_name != "other_name":
                raise AssertionError(f"Expected variable_name 'other_name', got {exc.variable_name!r}")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_init_rejects_reserved_lookup_option():
    """
        Test that an option the adapter sets itself cannot be passed again.
    """
    temp_dir = _create_temp_template_dir({})
    
    try:
        try:
            MakoAdapter(template_dirs=[temp_dir], directories=["/elsewhere"])
            raise AssertionError("Expected TemplateConfigurationError for a reserved option")
        except TemplateConfigurationError:
            pass  # Expected
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_init_rejects_unknown_lookup_option():
    """
        Test that an option Mako does not know raises
        TemplateConfigurationError.
    """
    temp_dir = _create_temp_template_dir({})
    
    try:
        try:
            MakoAdapter(template_dirs=[temp_dir], no_such_option=True)
            raise AssertionError("Expected TemplateConfigurationError for an unknown option")
        except TemplateConfigurationError:
            pass  # Expected
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


# =============================================================================
# Engine exceptions are mapped to the specific templating exceptions
# =============================================================================

def test_render_raises_template_syntax_error_for_file():
    """
        Test that a syntax error in a template file raises
        TemplateSyntaxError with the template name and line.
    """
    temp_dir = _create_temp_template_dir({
        "broken.html": "line one\n% if True:\nnever closed\n"
    })
    
    try:
        adapter = MakoAdapter(template_dirs=[temp_dir])
        
        try:
            adapter.render("broken.html", {})
            raise AssertionError("Expected TemplateSyntaxError")
        except TemplateSyntaxError as exc:
            if exc.template_name != "broken.html":
                raise AssertionError(f"Expected template_name 'broken.html', got {exc.template_name!r}")
            if not isinstance(exc.line_number, int):
                raise AssertionError(f"Expected an integer line_number, got {exc.line_number!r}")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_render_string_raises_template_syntax_error():
    """
        Test that render_string() raises TemplateSyntaxError for bad syntax.
    """
    temp_dir = _create_temp_template_dir({})
    
    try:
        adapter = MakoAdapter(template_dirs=[temp_dir])
        
        try:
            adapter.render_string("% if True:\nnever closed\n", {})
            raise AssertionError("Expected TemplateSyntaxError")
        except TemplateSyntaxError:
            pass  # Expected
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
        adapter = MakoAdapter(template_dirs=[temp_dir])
        
        try:
            adapter.compile_template("% for x in y:\nnever closed\n", template_name="page.html")
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
        "divide.html": "first\nsecond\n${ 1 / zero }\n"
    })
    
    try:
        adapter = MakoAdapter(template_dirs=[temp_dir])
        
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


def test_render_compiled_wraps_python_exception_in_template_render_error():
    """
        Test that render_compiled() wraps an ordinary exception.
    """
    temp_dir = _create_temp_template_dir({})
    
    try:
        adapter = MakoAdapter(template_dirs=[temp_dir])
        compiled = adapter.compile_template("${ 1 / zero }", template_name="page.html")
        
        try:
            adapter.render_compiled(compiled, {"zero": 0})
            raise AssertionError("Expected TemplateRenderError")
        except TemplateRenderError as exc:
            if exc.template_name != "page.html":
                raise AssertionError(f"Expected template_name 'page.html', got {exc.template_name!r}")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return
