"""
    Tests for the TemplateRenderer class.
    
    This module tests the TemplateRenderer including:
    - Initialization with engine and context processors
    - Context building with _build_context()
    - Rendering methods (render, render_async, render_string, render_stream)
    - Context processor support (add_context_processor, processor application)
    - Property test for template rendering determinism
"""

import asyncio
import os
import random
import shutil
import string
import tempfile

from automojo.webworks.templating.engine import TemplateEngine
from automojo.webworks.templating.jinja2_adapter import Jinja2Adapter
from automojo.webworks.templating.renderer import TemplateRenderer


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
# 12.1 - __init__() and _build_context() Tests
# =============================================================================

def test_init_creates_renderer():
    """
        Test that TemplateRenderer can be instantiated with an engine.
    """
    temp_dir = _create_temp_template_dir({})
    
    try:
        engine = Jinja2Adapter(template_dirs=[temp_dir])
        renderer = TemplateRenderer(engine)
        
        if not isinstance(renderer, TemplateRenderer):
            raise AssertionError("Expected TemplateRenderer instance")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_init_stores_engine():
    """
        Test that __init__() stores the engine reference.
    """
    temp_dir = _create_temp_template_dir({})
    
    try:
        engine = Jinja2Adapter(template_dirs=[temp_dir])
        renderer = TemplateRenderer(engine)
        
        if renderer.engine is not engine:
            raise AssertionError("Renderer should store the engine reference")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_init_with_no_context_processors():
    """
        Test that __init__() defaults to empty context processors list.
    """
    temp_dir = _create_temp_template_dir({})
    
    try:
        engine = Jinja2Adapter(template_dirs=[temp_dir])
        renderer = TemplateRenderer(engine)
        
        if len(renderer.context_processors) != 0:
            raise AssertionError(
                f"Expected 0 context processors, got {len(renderer.context_processors)}"
            )
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_init_with_context_processors():
    """
        Test that __init__() accepts context processors.
    """
    temp_dir = _create_temp_template_dir({})
    
    try:
        engine = Jinja2Adapter(template_dirs=[temp_dir])
        processor = lambda ctx: {"year": 2024}
        renderer = TemplateRenderer(engine, context_processors=[processor])
        
        if len(renderer.context_processors) != 1:
            raise AssertionError(
                f"Expected 1 context processor, got {len(renderer.context_processors)}"
            )
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_build_context_empty():
    """
        Test that _build_context() returns empty dict with no inputs.
    """
    temp_dir = _create_temp_template_dir({})
    
    try:
        engine = Jinja2Adapter(template_dirs=[temp_dir])
        renderer = TemplateRenderer(engine)
        
        result = renderer._build_context(None, {})
        
        if result != {}:
            raise AssertionError(f"Expected empty dict, got {result}")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_build_context_with_context_only():
    """
        Test that _build_context() merges passed context.
    """
    temp_dir = _create_temp_template_dir({})
    
    try:
        engine = Jinja2Adapter(template_dirs=[temp_dir])
        renderer = TemplateRenderer(engine)
        
        result = renderer._build_context({"title": "Home"}, {})
        
        if result != {"title": "Home"}:
            raise AssertionError(f"Expected {{'title': 'Home'}}, got {result}")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_build_context_with_kwargs_only():
    """
        Test that _build_context() merges kwargs.
    """
    temp_dir = _create_temp_template_dir({})
    
    try:
        engine = Jinja2Adapter(template_dirs=[temp_dir])
        renderer = TemplateRenderer(engine)
        
        result = renderer._build_context(None, {"title": "Home"})
        
        if result != {"title": "Home"}:
            raise AssertionError(f"Expected {{'title': 'Home'}}, got {result}")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_build_context_kwargs_override_context():
    """
        Test that kwargs override context values in _build_context().
    """
    temp_dir = _create_temp_template_dir({})
    
    try:
        engine = Jinja2Adapter(template_dirs=[temp_dir])
        renderer = TemplateRenderer(engine)
        
        result = renderer._build_context(
            {"title": "Original"},
            {"title": "Override"}
        )
        
        if result["title"] != "Override":
            raise AssertionError(
                f"Expected 'Override', got '{result['title']}'"
            )
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_build_context_with_processor():
    """
        Test that _build_context() applies context processors.
    """
    temp_dir = _create_temp_template_dir({})
    
    try:
        engine = Jinja2Adapter(template_dirs=[temp_dir])
        processor = lambda ctx: {"year": 2024}
        renderer = TemplateRenderer(engine, context_processors=[processor])
        
        result = renderer._build_context(None, {})
        
        if result.get("year") != 2024:
            raise AssertionError(f"Expected year=2024, got {result}")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_build_context_context_overrides_processor():
    """
        Test that passed context overrides processor output.
    """
    temp_dir = _create_temp_template_dir({})
    
    try:
        engine = Jinja2Adapter(template_dirs=[temp_dir])
        processor = lambda ctx: {"year": 2024}
        renderer = TemplateRenderer(engine, context_processors=[processor])
        
        result = renderer._build_context({"year": 2025}, {})
        
        if result["year"] != 2025:
            raise AssertionError(
                f"Expected year=2025, got {result['year']}"
            )
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_build_context_kwargs_override_processor():
    """
        Test that kwargs override processor output.
    """
    temp_dir = _create_temp_template_dir({})
    
    try:
        engine = Jinja2Adapter(template_dirs=[temp_dir])
        processor = lambda ctx: {"year": 2024}
        renderer = TemplateRenderer(engine, context_processors=[processor])
        
        result = renderer._build_context(None, {"year": 2025})
        
        if result["year"] != 2025:
            raise AssertionError(
                f"Expected year=2025, got {result['year']}"
            )
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_build_context_multiple_processors():
    """
        Test that _build_context() applies multiple processors in order.
    """
    temp_dir = _create_temp_template_dir({})
    
    try:
        engine = Jinja2Adapter(template_dirs=[temp_dir])
        processor1 = lambda ctx: {"a": 1, "b": 10}
        processor2 = lambda ctx: {"b": 20, "c": 30}
        renderer = TemplateRenderer(
            engine,
            context_processors=[processor1, processor2]
        )
        
        result = renderer._build_context(None, {})
        
        if result.get("a") != 1:
            raise AssertionError(f"Expected a=1, got {result.get('a')}")
        if result.get("b") != 20:
            raise AssertionError(f"Expected b=20 (second processor wins), got {result.get('b')}")
        if result.get("c") != 30:
            raise AssertionError(f"Expected c=30, got {result.get('c')}")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_build_context_processor_returning_none():
    """
        Test that _build_context() handles processors returning None.
    """
    temp_dir = _create_temp_template_dir({})
    
    try:
        engine = Jinja2Adapter(template_dirs=[temp_dir])
        processor = lambda ctx: None
        renderer = TemplateRenderer(engine, context_processors=[processor])
        
        result = renderer._build_context({"title": "Home"}, {})
        
        if result != {"title": "Home"}:
            raise AssertionError(f"Expected {{'title': 'Home'}}, got {result}")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


# =============================================================================
# 12.2 - Rendering Methods Tests
# =============================================================================

def test_render_returns_string():
    """
        Test that render() returns a rendered string.
    """
    temp_dir = _create_temp_template_dir({
        "hello.html": "Hello {{ name }}!"
    })
    
    try:
        engine = Jinja2Adapter(template_dirs=[temp_dir])
        renderer = TemplateRenderer(engine)
        
        result = renderer.render("hello.html", {"name": "World"})
        
        if result != "Hello World!":
            raise AssertionError(f"Expected 'Hello World!', got '{result}'")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_render_with_kwargs():
    """
        Test that render() accepts keyword arguments.
    """
    temp_dir = _create_temp_template_dir({
        "hello.html": "Hello {{ name }}!"
    })
    
    try:
        engine = Jinja2Adapter(template_dirs=[temp_dir])
        renderer = TemplateRenderer(engine)
        
        result = renderer.render("hello.html", name="World")
        
        if result != "Hello World!":
            raise AssertionError(f"Expected 'Hello World!', got '{result}'")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_render_with_context_and_kwargs():
    """
        Test that render() merges context and kwargs.
    """
    temp_dir = _create_temp_template_dir({
        "page.html": "{{ title }} by {{ author }}"
    })
    
    try:
        engine = Jinja2Adapter(template_dirs=[temp_dir])
        renderer = TemplateRenderer(engine)
        
        result = renderer.render(
            "page.html",
            {"title": "My Page"},
            author="Alice"
        )
        
        if result != "My Page by Alice":
            raise AssertionError(f"Expected 'My Page by Alice', got '{result}'")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_render_with_context_processor():
    """
        Test that render() applies context processors.
    """
    temp_dir = _create_temp_template_dir({
        "footer.html": "Copyright {{ year }}"
    })
    
    try:
        engine = Jinja2Adapter(template_dirs=[temp_dir])
        processor = lambda ctx: {"year": 2024}
        renderer = TemplateRenderer(engine, context_processors=[processor])
        
        result = renderer.render("footer.html")
        
        if result != "Copyright 2024":
            raise AssertionError(f"Expected 'Copyright 2024', got '{result}'")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_render_with_none_context():
    """
        Test that render() works with None context.
    """
    temp_dir = _create_temp_template_dir({
        "static.html": "Static content"
    })
    
    try:
        engine = Jinja2Adapter(template_dirs=[temp_dir])
        renderer = TemplateRenderer(engine)
        
        result = renderer.render("static.html")
        
        if result != "Static content":
            raise AssertionError(f"Expected 'Static content', got '{result}'")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_render_async_returns_string():
    """
        Test that render_async() returns a rendered string.
    """
    temp_dir = _create_temp_template_dir({
        "hello.html": "Hello {{ name }}!"
    })
    
    try:
        engine = Jinja2Adapter(template_dirs=[temp_dir])
        renderer = TemplateRenderer(engine)
        
        loop = asyncio.new_event_loop()
        try:
            result = loop.run_until_complete(
                renderer.render_async("hello.html", {"name": "Async"})
            )
        finally:
            loop.close()
        
        if result != "Hello Async!":
            raise AssertionError(f"Expected 'Hello Async!', got '{result}'")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_render_async_with_context_processor():
    """
        Test that render_async() applies context processors.
    """
    temp_dir = _create_temp_template_dir({
        "footer.html": "Copyright {{ year }}"
    })
    
    try:
        engine = Jinja2Adapter(template_dirs=[temp_dir])
        processor = lambda ctx: {"year": 2024}
        renderer = TemplateRenderer(engine, context_processors=[processor])
        
        loop = asyncio.new_event_loop()
        try:
            result = loop.run_until_complete(
                renderer.render_async("footer.html")
            )
        finally:
            loop.close()
        
        if result != "Copyright 2024":
            raise AssertionError(f"Expected 'Copyright 2024', got '{result}'")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_render_string_returns_string():
    """
        Test that render_string() renders a template string.
    """
    temp_dir = _create_temp_template_dir({})
    
    try:
        engine = Jinja2Adapter(template_dirs=[temp_dir])
        renderer = TemplateRenderer(engine)
        
        result = renderer.render_string(
            "Hello {{ name }}!",
            {"name": "World"}
        )
        
        if result != "Hello World!":
            raise AssertionError(f"Expected 'Hello World!', got '{result}'")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_render_string_with_kwargs():
    """
        Test that render_string() accepts keyword arguments.
    """
    temp_dir = _create_temp_template_dir({})
    
    try:
        engine = Jinja2Adapter(template_dirs=[temp_dir])
        renderer = TemplateRenderer(engine)
        
        result = renderer.render_string(
            "Hello {{ name }}!",
            name="World"
        )
        
        if result != "Hello World!":
            raise AssertionError(f"Expected 'Hello World!', got '{result}'")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_render_string_with_context_processor():
    """
        Test that render_string() applies context processors.
    """
    temp_dir = _create_temp_template_dir({})
    
    try:
        engine = Jinja2Adapter(template_dirs=[temp_dir])
        processor = lambda ctx: {"year": 2024}
        renderer = TemplateRenderer(engine, context_processors=[processor])
        
        result = renderer.render_string("Copyright {{ year }}")
        
        if result != "Copyright 2024":
            raise AssertionError(f"Expected 'Copyright 2024', got '{result}'")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_render_stream_returns_iterator():
    """
        Test that render_stream() returns an iterator.
    """
    temp_dir = _create_temp_template_dir({
        "hello.html": "Hello {{ name }}!"
    })
    
    try:
        engine = Jinja2Adapter(template_dirs=[temp_dir])
        renderer = TemplateRenderer(engine)
        
        result = renderer.render_stream("hello.html", {"name": "World"})
        
        # Collect all chunks
        chunks = list(result)
        output = "".join(chunks)
        
        if output != "Hello World!":
            raise AssertionError(f"Expected 'Hello World!', got '{output}'")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_render_stream_with_context_processor():
    """
        Test that render_stream() applies context processors.
    """
    temp_dir = _create_temp_template_dir({
        "footer.html": "Copyright {{ year }}"
    })
    
    try:
        engine = Jinja2Adapter(template_dirs=[temp_dir])
        processor = lambda ctx: {"year": 2024}
        renderer = TemplateRenderer(engine, context_processors=[processor])
        
        result = renderer.render_stream("footer.html")
        output = "".join(result)
        
        if output != "Copyright 2024":
            raise AssertionError(f"Expected 'Copyright 2024', got '{output}'")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


# =============================================================================
# 12.3 - Context Processor Support Tests
# =============================================================================

def test_add_context_processor():
    """
        Test that add_context_processor() adds a processor.
    """
    temp_dir = _create_temp_template_dir({})
    
    try:
        engine = Jinja2Adapter(template_dirs=[temp_dir])
        renderer = TemplateRenderer(engine)
        
        processor = lambda ctx: {"year": 2024}
        renderer.add_context_processor(processor)
        
        if len(renderer.context_processors) != 1:
            raise AssertionError(
                f"Expected 1 processor, got {len(renderer.context_processors)}"
            )
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_add_multiple_context_processors():
    """
        Test that add_context_processor() can add multiple processors.
    """
    temp_dir = _create_temp_template_dir({})
    
    try:
        engine = Jinja2Adapter(template_dirs=[temp_dir])
        renderer = TemplateRenderer(engine)
        
        renderer.add_context_processor(lambda ctx: {"a": 1})
        renderer.add_context_processor(lambda ctx: {"b": 2})
        renderer.add_context_processor(lambda ctx: {"c": 3})
        
        if len(renderer.context_processors) != 3:
            raise AssertionError(
                f"Expected 3 processors, got {len(renderer.context_processors)}"
            )
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_context_processor_applied_during_render():
    """
        Test that context processors added via add_context_processor()
        are applied during rendering.
    """
    temp_dir = _create_temp_template_dir({
        "page.html": "{{ title }} - {{ year }}"
    })
    
    try:
        engine = Jinja2Adapter(template_dirs=[temp_dir])
        renderer = TemplateRenderer(engine)
        
        renderer.add_context_processor(lambda ctx: {"year": 2024})
        
        result = renderer.render("page.html", {"title": "Home"})
        
        if result != "Home - 2024":
            raise AssertionError(f"Expected 'Home - 2024', got '{result}'")
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_context_processor_order_matters():
    """
        Test that context processors are applied in registration order.
    """
    temp_dir = _create_temp_template_dir({
        "value.html": "{{ val }}"
    })
    
    try:
        engine = Jinja2Adapter(template_dirs=[temp_dir])
        renderer = TemplateRenderer(engine)
        
        renderer.add_context_processor(lambda ctx: {"val": "first"})
        renderer.add_context_processor(lambda ctx: {"val": "second"})
        
        result = renderer.render("value.html")
        
        if result != "second":
            raise AssertionError(
                f"Expected 'second' (last processor wins), got '{result}'"
            )
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


# =============================================================================
# 12.4 - Property-Based Tests
# =============================================================================

def _generate_random_string(min_length: int = 1, max_length: int = 50) -> str:
    """
        Generate a random string for property testing.
        
        :param min_length: Minimum string length.
        :param max_length: Maximum string length.
        
        :returns: Random string.
    """
    length = random.randint(min_length, max_length)
    chars = string.ascii_letters + string.digits + " _-."
    return "".join(random.choice(chars) for _ in range(length))


def _generate_random_context(max_depth: int = 2, max_keys: int = 5) -> dict:
    """
        Generate a random context dictionary for property testing.
        
        :param max_depth: Maximum nesting depth.
        :param max_keys: Maximum number of keys per level.
        
        :returns: Random context dictionary.
    """
    context = {}
    num_keys = random.randint(1, max_keys)
    
    for _ in range(num_keys):
        key = _generate_random_string(3, 15).replace(" ", "_").replace(".", "_").replace("-", "_")
        # Ensure key is a valid identifier
        key = "var_" + "".join(c for c in key if c.isalnum() or c == "_")
        
        value_type = random.choice(["string", "int", "float", "bool", "list"])
        
        if value_type == "string":
            context[key] = _generate_random_string()
        elif value_type == "int":
            context[key] = random.randint(-1000, 1000)
        elif value_type == "float":
            context[key] = round(random.uniform(-1000, 1000), 2)
        elif value_type == "bool":
            context[key] = random.choice([True, False])
        elif value_type == "list":
            context[key] = [random.randint(0, 100) for _ in range(random.randint(0, 5))]
    
    return context


def _generate_template_string(context: dict) -> str:
    """
        Generate a Jinja2 template string that uses the given context keys.
        
        :param context: Context dictionary whose keys will be referenced.
        
        :returns: A Jinja2 template string.
    """
    parts = []
    
    for key in context.keys():
        parts.append(f"{{{{ {key} }}}}")
    
    # Add some static text between variables
    template = " | ".join(parts)
    return "Output: " + template


def test_property_template_rendering_determinism():
    """
        Property test for template rendering determinism.
        
        **Property 1: Template Rendering Determinism**
        
        *For any* valid template and context, rendering the same template
        with the same context SHALL produce identical output on every
        invocation.
        
        **Validates: Requirements 2.1, 2.6**
        
        This property test verifies that:
        1. Rendering the same template with the same context produces
           identical output across multiple invocations
        2. This holds for randomly generated contexts with various
           value types (strings, ints, floats, bools, lists)
        3. This holds for both render() and render_string() methods
        
        Test strategy:
        - Generate random context dictionaries
        - Generate template strings that reference the context keys
        - Render the same template+context multiple times
        - Verify all outputs are identical
    """
    iterations = 100
    renders_per_iteration = 5
    
    temp_dir = _create_temp_template_dir({})
    
    try:
        engine = Jinja2Adapter(template_dirs=[temp_dir])
        renderer = TemplateRenderer(engine)
        
        for iteration in range(iterations):
            # Generate a random context
            context = _generate_random_context()
            
            if not context:
                continue
            
            # Generate a template string that uses the context keys
            template_source = _generate_template_string(context)
            
            # Render multiple times and collect results
            results = []
            for _ in range(renders_per_iteration):
                result = renderer.render_string(template_source, context)
                results.append(result)
            
            # Verify all results are identical
            first_result = results[0]
            for render_index, result in enumerate(results[1:], start=1):
                if result != first_result:
                    raise AssertionError(
                        f"Iteration {iteration}: Rendering is not deterministic. "
                        f"Render 0 produced '{first_result}', but render "
                        f"{render_index} produced '{result}'. "
                        f"Template: '{template_source}', "
                        f"Context keys: {list(context.keys())}"
                    )
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_property_template_rendering_determinism_with_processors():
    """
        Property test for rendering determinism with context processors.
        
        **Property 1: Template Rendering Determinism** (extended)
        
        Verifies that rendering determinism holds even when context
        processors are involved.
        
        **Validates: Requirements 2.1, 2.6**
        
        Test strategy:
        - Generate random context processors that return fixed values
        - Generate random contexts and templates
        - Render multiple times with processors active
        - Verify all outputs are identical
    """
    iterations = 100
    renders_per_iteration = 5
    
    temp_dir = _create_temp_template_dir({})
    
    try:
        for iteration in range(iterations):
            engine = Jinja2Adapter(template_dirs=[temp_dir])
            
            # Create a processor with a fixed value
            processor_value = _generate_random_string(5, 20)
            processor = lambda ctx, val=processor_value: {"proc_var": val}
            
            renderer = TemplateRenderer(engine, context_processors=[processor])
            
            # Generate a random context
            context = _generate_random_context()
            
            # Build a template that uses both context and processor vars
            parts = [f"{{{{ proc_var }}}}"]
            for key in context.keys():
                parts.append(f"{{{{ {key} }}}}")
            template_source = " | ".join(parts)
            
            # Render multiple times
            results = []
            for _ in range(renders_per_iteration):
                result = renderer.render_string(template_source, context)
                results.append(result)
            
            # Verify all results are identical
            first_result = results[0]
            for render_index, result in enumerate(results[1:], start=1):
                if result != first_result:
                    raise AssertionError(
                        f"Iteration {iteration}: Rendering with processors is "
                        f"not deterministic. Render 0 produced '{first_result}', "
                        f"but render {render_index} produced '{result}'. "
                        f"Template: '{template_source}'"
                    )
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return
