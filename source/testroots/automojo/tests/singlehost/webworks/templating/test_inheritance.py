"""
    Tests for template inheritance and include support.
    
    This module tests the Jinja2Adapter's handling of template inheritance
    features including:
    - extends directive functionality
    - block override functionality
    - super() call functionality
    - include directive functionality
    - variable passing to includes
    - conditional includes
    - inheritance error handling (missing parents, circular inheritance)
    - property test for template inheritance chains
"""

import os
import random
import shutil
import string
import tempfile

from automojo.webworks.templating.exceptions import (
    TemplateError,
    TemplateInheritanceError,
    TemplateNotFoundError,
)
from automojo.webworks.templating.jinja2_adapter import Jinja2Adapter


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
# 14.1 - Verify Jinja2 Inheritance Support
# =============================================================================

def test_extends_directive_basic():
    """
        Test that a child template can extend a base template using
        the extends directive.
        
        Validates: Requirements 4.1
    """
    templates = {
        "base.html": (
            "<html>"
            "<head>{% block head %}{% endblock %}</head>"
            "<body>{% block content %}{% endblock %}</body>"
            "</html>"
        ),
        "child.html": (
            '{% extends "base.html" %}'
            "{% block content %}Hello World{% endblock %}"
        ),
    }
    
    temp_dir = _create_temp_template_dir(templates)
    
    try:
        adapter = Jinja2Adapter(
            template_dirs=[temp_dir],
            auto_escape=False
        )
        
        result = adapter.render("child.html", {})
        
        if "<html>" not in result:
            raise AssertionError(
                f"Expected '<html>' in result, got: {result}"
            )
        if "Hello World" not in result:
            raise AssertionError(
                f"Expected 'Hello World' in result, got: {result}"
            )
        if "<body>Hello World</body>" not in result:
            raise AssertionError(
                f"Expected '<body>Hello World</body>' in result, got: {result}"
            )
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_extends_directive_with_context():
    """
        Test that context variables are available in child templates
        that extend a base template.
        
        Validates: Requirements 4.1
    """
    templates = {
        "base.html": (
            "<html>"
            "<body>{% block content %}{% endblock %}</body>"
            "</html>"
        ),
        "child.html": (
            '{% extends "base.html" %}'
            "{% block content %}Hello {{ name }}{% endblock %}"
        ),
    }
    
    temp_dir = _create_temp_template_dir(templates)
    
    try:
        adapter = Jinja2Adapter(
            template_dirs=[temp_dir],
            auto_escape=False
        )
        
        result = adapter.render("child.html", {"name": "World"})
        
        if "Hello World" not in result:
            raise AssertionError(
                f"Expected 'Hello World' in result, got: {result}"
            )
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_block_override_replaces_parent_content():
    """
        Test that a child template block overrides the parent block content.
        
        Validates: Requirements 4.2
    """
    templates = {
        "base.html": (
            "<html>"
            "<head>{% block head %}Default Head{% endblock %}</head>"
            "<body>{% block content %}Default Content{% endblock %}</body>"
            "</html>"
        ),
        "child.html": (
            '{% extends "base.html" %}'
            "{% block head %}Custom Head{% endblock %}"
            "{% block content %}Custom Content{% endblock %}"
        ),
    }
    
    temp_dir = _create_temp_template_dir(templates)
    
    try:
        adapter = Jinja2Adapter(
            template_dirs=[temp_dir],
            auto_escape=False
        )
        
        result = adapter.render("child.html", {})
        
        if "Default Head" in result:
            raise AssertionError(
                f"Expected parent head to be overridden, got: {result}"
            )
        if "Default Content" in result:
            raise AssertionError(
                f"Expected parent content to be overridden, got: {result}"
            )
        if "Custom Head" not in result:
            raise AssertionError(
                f"Expected 'Custom Head' in result, got: {result}"
            )
        if "Custom Content" not in result:
            raise AssertionError(
                f"Expected 'Custom Content' in result, got: {result}"
            )
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_block_override_partial():
    """
        Test that only overridden blocks are replaced; non-overridden
        blocks retain parent content.
        
        Validates: Requirements 4.2
    """
    templates = {
        "base.html": (
            "{% block header %}Base Header{% endblock %}"
            "{% block body %}Base Body{% endblock %}"
            "{% block footer %}Base Footer{% endblock %}"
        ),
        "child.html": (
            '{% extends "base.html" %}'
            "{% block body %}Child Body{% endblock %}"
        ),
    }
    
    temp_dir = _create_temp_template_dir(templates)
    
    try:
        adapter = Jinja2Adapter(
            template_dirs=[temp_dir],
            auto_escape=False
        )
        
        result = adapter.render("child.html", {})
        
        if "Base Header" not in result:
            raise AssertionError(
                f"Expected 'Base Header' (not overridden), got: {result}"
            )
        if "Child Body" not in result:
            raise AssertionError(
                f"Expected 'Child Body' (overridden), got: {result}"
            )
        if "Base Footer" not in result:
            raise AssertionError(
                f"Expected 'Base Footer' (not overridden), got: {result}"
            )
        if "Base Body" in result:
            raise AssertionError(
                f"Expected 'Base Body' to be replaced, got: {result}"
            )
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_super_call_includes_parent_content():
    """
        Test that super() in a child block includes the parent block content.
        
        Validates: Requirements 4.3
    """
    templates = {
        "base.html": (
            "{% block content %}Parent Content{% endblock %}"
        ),
        "child.html": (
            '{% extends "base.html" %}'
            "{% block content %}Child Content {{ super() }}{% endblock %}"
        ),
    }
    
    temp_dir = _create_temp_template_dir(templates)
    
    try:
        adapter = Jinja2Adapter(
            template_dirs=[temp_dir],
            auto_escape=False
        )
        
        result = adapter.render("child.html", {})
        
        if "Child Content" not in result:
            raise AssertionError(
                f"Expected 'Child Content' in result, got: {result}"
            )
        if "Parent Content" not in result:
            raise AssertionError(
                f"Expected 'Parent Content' from super(), got: {result}"
            )
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_super_call_preserves_order():
    """
        Test that super() content appears at the correct position
        within the child block.
        
        Validates: Requirements 4.3
    """
    templates = {
        "base.html": (
            "{% block content %}PARENT{% endblock %}"
        ),
        "child.html": (
            '{% extends "base.html" %}'
            "{% block content %}BEFORE|{{ super() }}|AFTER{% endblock %}"
        ),
    }
    
    temp_dir = _create_temp_template_dir(templates)
    
    try:
        adapter = Jinja2Adapter(
            template_dirs=[temp_dir],
            auto_escape=False
        )
        
        result = adapter.render("child.html", {})
        
        if "BEFORE|PARENT|AFTER" not in result:
            raise AssertionError(
                f"Expected 'BEFORE|PARENT|AFTER' in result, got: {result}"
            )
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_multi_level_inheritance():
    """
        Test that template inheritance works across multiple levels
        (grandparent -> parent -> child).
        
        Validates: Requirements 4.1, 4.9
    """
    templates = {
        "grandparent.html": (
            "<html>"
            "{% block content %}Grandparent{% endblock %}"
            "</html>"
        ),
        "parent.html": (
            '{% extends "grandparent.html" %}'
            "{% block content %}Parent{% endblock %}"
        ),
        "child.html": (
            '{% extends "parent.html" %}'
            "{% block content %}Child{% endblock %}"
        ),
    }
    
    temp_dir = _create_temp_template_dir(templates)
    
    try:
        adapter = Jinja2Adapter(
            template_dirs=[temp_dir],
            auto_escape=False
        )
        
        result = adapter.render("child.html", {})
        
        if "<html>" not in result:
            raise AssertionError(
                f"Expected '<html>' from grandparent, got: {result}"
            )
        if "Child" not in result:
            raise AssertionError(
                f"Expected 'Child' in result, got: {result}"
            )
        if "Parent" in result:
            raise AssertionError(
                f"Expected 'Parent' to be overridden, got: {result}"
            )
        if "Grandparent" in result:
            raise AssertionError(
                f"Expected 'Grandparent' to be overridden, got: {result}"
            )
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return



# =============================================================================
# 14.2 - Verify Template Include Support
# =============================================================================

def test_include_directive_basic():
    """
        Test that the include directive inserts another template's content.
        
        Validates: Requirements 4.4
    """
    templates = {
        "partial.html": "Partial Content",
        "main.html": 'Before|{% include "partial.html" %}|After',
    }
    
    temp_dir = _create_temp_template_dir(templates)
    
    try:
        adapter = Jinja2Adapter(
            template_dirs=[temp_dir],
            auto_escape=False
        )
        
        result = adapter.render("main.html", {})
        
        if "Before|Partial Content|After" not in result:
            raise AssertionError(
                f"Expected 'Before|Partial Content|After', got: {result}"
            )
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_include_with_variables():
    """
        Test that variables from the parent context are available
        in included templates.
        
        Validates: Requirements 4.5
    """
    templates = {
        "partial.html": "Hello {{ name }}",
        "main.html": '{% include "partial.html" %}',
    }
    
    temp_dir = _create_temp_template_dir(templates)
    
    try:
        adapter = Jinja2Adapter(
            template_dirs=[temp_dir],
            auto_escape=False
        )
        
        result = adapter.render("main.html", {"name": "World"})
        
        if "Hello World" not in result:
            raise AssertionError(
                f"Expected 'Hello World' in result, got: {result}"
            )
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_include_with_scoped_variables():
    """
        Test that variables can be passed to included templates using
        the with keyword and scoped context.
        
        Validates: Requirements 4.5
    """
    templates = {
        "partial.html": "Value: {{ item }}",
        "main.html": '{% include "partial.html" with context %}',
    }
    
    temp_dir = _create_temp_template_dir(templates)
    
    try:
        adapter = Jinja2Adapter(
            template_dirs=[temp_dir],
            auto_escape=False
        )
        
        result = adapter.render("main.html", {"item": "test_value"})
        
        if "Value: test_value" not in result:
            raise AssertionError(
                f"Expected 'Value: test_value' in result, got: {result}"
            )
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_include_with_set_variable():
    """
        Test that a variable set before include is available in the
        included template.
        
        Validates: Requirements 4.5
    """
    templates = {
        "partial.html": "Item: {{ item_name }}",
        "main.html": (
            '{% set item_name = "widget" %}'
            '{% include "partial.html" %}'
        ),
    }
    
    temp_dir = _create_temp_template_dir(templates)
    
    try:
        adapter = Jinja2Adapter(
            template_dirs=[temp_dir],
            auto_escape=False
        )
        
        result = adapter.render("main.html", {})
        
        if "Item: widget" not in result:
            raise AssertionError(
                f"Expected 'Item: widget' in result, got: {result}"
            )
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_conditional_include_true():
    """
        Test that a conditional include renders the included template
        when the condition is true.
        
        Validates: Requirements 4.6
    """
    templates = {
        "sidebar.html": "Sidebar Content",
        "main.html": (
            "Main|"
            '{% if show_sidebar %}{% include "sidebar.html" %}{% endif %}'
        ),
    }
    
    temp_dir = _create_temp_template_dir(templates)
    
    try:
        adapter = Jinja2Adapter(
            template_dirs=[temp_dir],
            auto_escape=False
        )
        
        result = adapter.render("main.html", {"show_sidebar": True})
        
        if "Main|Sidebar Content" not in result:
            raise AssertionError(
                f"Expected 'Main|Sidebar Content', got: {result}"
            )
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_conditional_include_false():
    """
        Test that a conditional include does not render the included
        template when the condition is false.
        
        Validates: Requirements 4.6
    """
    templates = {
        "sidebar.html": "Sidebar Content",
        "main.html": (
            "Main|"
            '{% if show_sidebar %}{% include "sidebar.html" %}{% endif %}'
        ),
    }
    
    temp_dir = _create_temp_template_dir(templates)
    
    try:
        adapter = Jinja2Adapter(
            template_dirs=[temp_dir],
            auto_escape=False
        )
        
        result = adapter.render("main.html", {"show_sidebar": False})
        
        if "Sidebar Content" in result:
            raise AssertionError(
                f"Expected no sidebar content when condition is false, got: {result}"
            )
        if "Main|" not in result:
            raise AssertionError(
                f"Expected 'Main|' in result, got: {result}"
            )
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_include_ignore_missing():
    """
        Test that include with ignore missing does not raise an error
        when the included template does not exist.
        
        Validates: Requirements 4.6
    """
    templates = {
        "main.html": (
            "Main|"
            '{% include "missing.html" ignore missing %}'
            "|End"
        ),
    }
    
    temp_dir = _create_temp_template_dir(templates)
    
    try:
        adapter = Jinja2Adapter(
            template_dirs=[temp_dir],
            auto_escape=False
        )
        
        result = adapter.render("main.html", {})
        
        if "Main||End" not in result:
            raise AssertionError(
                f"Expected 'Main||End' with missing template ignored, got: {result}"
            )
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_multiple_includes():
    """
        Test that multiple includes work correctly in the same template.
        
        Validates: Requirements 4.4
    """
    templates = {
        "header.html": "HEADER",
        "footer.html": "FOOTER",
        "main.html": (
            '{% include "header.html" %}'
            "|BODY|"
            '{% include "footer.html" %}'
        ),
    }
    
    temp_dir = _create_temp_template_dir(templates)
    
    try:
        adapter = Jinja2Adapter(
            template_dirs=[temp_dir],
            auto_escape=False
        )
        
        result = adapter.render("main.html", {})
        
        if "HEADER|BODY|FOOTER" not in result:
            raise AssertionError(
                f"Expected 'HEADER|BODY|FOOTER', got: {result}"
            )
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return



# =============================================================================
# 14.3 - Inheritance Error Handling
# =============================================================================

def test_missing_parent_template_raises_error():
    """
        Test that extending a non-existent parent template raises
        TemplateNotFoundError or TemplateError.
        
        Validates: Requirements 4.7
    """
    templates = {
        "child.html": (
            '{% extends "nonexistent_base.html" %}'
            "{% block content %}Child{% endblock %}"
        ),
    }
    
    temp_dir = _create_temp_template_dir(templates)
    
    try:
        adapter = Jinja2Adapter(
            template_dirs=[temp_dir],
            auto_escape=False
        )
        
        caught_error = False
        
        try:
            adapter.render("child.html", {})
        except TemplateNotFoundError as exc:
            caught_error = True
            # The error may reference either the child or the parent
            # template name depending on how Jinja2 reports the error
            error_msg = str(exc)
            if not error_msg:
                raise AssertionError(
                    "Expected non-empty error message for missing parent"
                )
        except TemplateError as exc:
            caught_error = True
        
        if not caught_error:
            raise AssertionError(
                "Expected TemplateNotFoundError or TemplateError "
                "for missing parent template"
            )
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_missing_include_template_raises_error():
    """
        Test that including a non-existent template raises an error.
        
        Validates: Requirements 4.7
    """
    templates = {
        "main.html": '{% include "nonexistent.html" %}',
    }
    
    temp_dir = _create_temp_template_dir(templates)
    
    try:
        adapter = Jinja2Adapter(
            template_dirs=[temp_dir],
            auto_escape=False
        )
        
        caught_error = False
        
        try:
            adapter.render("main.html", {})
        except TemplateNotFoundError as exc:
            caught_error = True
            # The error may reference the main template or the included
            # template depending on how Jinja2 reports the error
            error_msg = str(exc)
            if not error_msg:
                raise AssertionError(
                    "Expected non-empty error message for missing include"
                )
        except TemplateError as exc:
            caught_error = True
        
        if not caught_error:
            raise AssertionError(
                "Expected TemplateNotFoundError or TemplateError "
                "for missing include template"
            )
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_circular_inheritance_raises_error():
    """
        Test that circular template inheritance is detected and raises
        a TemplateError.
        
        Jinja2 natively detects circular inheritance and raises a
        TemplateRuntimeError. Our adapter wraps this as a TemplateError.
        
        Validates: Requirements 4.8
    """
    templates = {
        "a.html": (
            '{% extends "b.html" %}'
            "{% block content %}A{% endblock %}"
        ),
        "b.html": (
            '{% extends "a.html" %}'
            "{% block content %}B{% endblock %}"
        ),
    }
    
    temp_dir = _create_temp_template_dir(templates)
    
    try:
        adapter = Jinja2Adapter(
            template_dirs=[temp_dir],
            auto_escape=False
        )
        
        caught_error = False
        
        try:
            adapter.render("a.html", {})
        except (TemplateError, TemplateInheritanceError) as exc:
            caught_error = True
        except RecursionError:
            # Jinja2 may raise RecursionError for circular inheritance
            caught_error = True
        
        if not caught_error:
            raise AssertionError(
                "Expected TemplateError, TemplateInheritanceError, or "
                "RecursionError for circular inheritance"
            )
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_self_referencing_extends_raises_error():
    """
        Test that a template extending itself raises an error.
        
        Validates: Requirements 4.8
    """
    templates = {
        "self_ref.html": (
            '{% extends "self_ref.html" %}'
            "{% block content %}Self{% endblock %}"
        ),
    }
    
    temp_dir = _create_temp_template_dir(templates)
    
    try:
        adapter = Jinja2Adapter(
            template_dirs=[temp_dir],
            auto_escape=False
        )
        
        caught_error = False
        
        try:
            adapter.render("self_ref.html", {})
        except (TemplateError, TemplateInheritanceError) as exc:
            caught_error = True
        except RecursionError:
            caught_error = True
        
        if not caught_error:
            raise AssertionError(
                "Expected error for self-referencing template inheritance"
            )
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_template_inheritance_error_class_exists():
    """
        Test that TemplateInheritanceError is properly defined and
        is a subclass of TemplateError.
        
        Validates: Requirements 4.8
    """
    if not issubclass(TemplateInheritanceError, TemplateError):
        raise AssertionError(
            "TemplateInheritanceError should be a subclass of TemplateError"
        )
    
    error = TemplateInheritanceError(
        "Circular inheritance detected",
        chain=["child.html", "parent.html", "child.html"]
    )
    
    if error.chain != ["child.html", "parent.html", "child.html"]:
        raise AssertionError(
            f"Expected chain attribute, got: {error.chain}"
        )
    
    error_msg = str(error)
    if "Circular inheritance detected" not in error_msg:
        raise AssertionError(
            f"Expected message in error string, got: {error_msg}"
        )
    if "child.html" not in error_msg:
        raise AssertionError(
            f"Expected chain info in error string, got: {error_msg}"
        )
    
    return


def test_template_inheritance_error_exported():
    """
        Test that TemplateInheritanceError is exported from the
        templating package.
        
        Validates: Requirements 4.8
    """
    from automojo.webworks.templating import TemplateInheritanceError as ExportedError
    
    if ExportedError is not TemplateInheritanceError:
        raise AssertionError(
            "TemplateInheritanceError should be exported from "
            "automojo.webworks.templating"
        )
    
    return



# =============================================================================
# 14.4 - Property Test: Template Inheritance Chain
# =============================================================================
# Property 5: Template Inheritance Chain
#
# For any template inheritance chain (child extends parent extends grandparent),
# block content SHALL be resolved from the most specific (child) template,
# with super() calls correctly invoking parent block content.
#
# Validates: Requirements 4.1, 4.2, 4.3, 4.9

def _generate_random_identifier(rng: random.Random, min_len: int = 3, max_len: int = 10) -> str:
    """
        Generate a random identifier string suitable for use in
        template content markers.
        
        :param rng: Random number generator instance.
        :param min_len: Minimum identifier length.
        :param max_len: Maximum identifier length.
        
        :returns: Random alphabetic string.
    """
    length = rng.randint(min_len, max_len)
    return "".join(rng.choices(string.ascii_lowercase, k=length))


def _build_inheritance_chain(rng: random.Random, depth: int):
    """
        Build a template inheritance chain of the specified depth.
        
        Creates a chain of templates where each level extends the previous
        one. Each level has a unique content marker in the 'content' block.
        The deepest child template overrides the block with its own marker.
        
        :param rng: Random number generator instance.
        :param depth: Number of levels in the inheritance chain (1-5).
        
        :returns: Tuple of (templates_dict, level_markers_list) where
            templates_dict maps template names to content and
            level_markers_list contains the unique marker for each level.
    """
    templates = {}
    markers = []
    
    for level in range(depth):
        marker = f"LEVEL{level}_{_generate_random_identifier(rng)}"
        markers.append(marker)
        
        template_name = f"level_{level}.html"
        
        if level == 0:
            # Base template (root of the chain)
            templates[template_name] = (
                f"[START]"
                f"{{% block content %}}{marker}{{% endblock %}}"
                f"[END]"
            )
        else:
            # Child template extending the previous level
            parent_name = f"level_{level - 1}.html"
            templates[template_name] = (
                f'{{% extends "{parent_name}" %}}'
                f"{{% block content %}}{marker}{{% endblock %}}"
            )
    
    return templates, markers


def _build_inheritance_chain_with_super(rng: random.Random, depth: int):
    """
        Build a template inheritance chain where each child calls super()
        to include parent block content.
        
        :param rng: Random number generator instance.
        :param depth: Number of levels in the inheritance chain (1-5).
        
        :returns: Tuple of (templates_dict, level_markers_list) where
            templates_dict maps template names to content and
            level_markers_list contains the unique marker for each level.
    """
    templates = {}
    markers = []
    
    for level in range(depth):
        marker = f"LEVEL{level}_{_generate_random_identifier(rng)}"
        markers.append(marker)
        
        template_name = f"super_level_{level}.html"
        
        if level == 0:
            # Base template (root of the chain)
            templates[template_name] = (
                f"{{% block content %}}{marker}{{% endblock %}}"
            )
        else:
            # Child template extending the previous level with super()
            parent_name = f"super_level_{level - 1}.html"
            templates[template_name] = (
                f'{{% extends "{parent_name}" %}}'
                f"{{% block content %}}{marker}|{{{{ super() }}}}{{% endblock %}}"
            )
    
    return templates, markers


def test_property_inheritance_chain():
    """
        Property 5: Template Inheritance Chain
        
        For any template inheritance chain of depth 1-5, the most specific
        (child) template's block content SHALL be used in the rendered output,
        overriding all ancestor block content.
        
        This test generates random inheritance chains and verifies that:
        1. The child template's content marker appears in the output
        2. Intermediate ancestor content markers do NOT appear (overridden)
        3. The base template's structural elements are preserved
        
        **Validates: Requirements 4.1, 4.2, 4.3, 4.9**
    """
    rng = random.Random(42)
    num_iterations = 100
    
    for iteration in range(num_iterations):
        depth = rng.randint(1, 5)
        templates, markers = _build_inheritance_chain(rng, depth)
        
        temp_dir = _create_temp_template_dir(templates)
        
        try:
            adapter = Jinja2Adapter(
                template_dirs=[temp_dir],
                auto_escape=False
            )
            
            # Render the deepest child template
            child_template = f"level_{depth - 1}.html"
            result = adapter.render(child_template, {})
            
            # The child's marker (last in the list) should be present
            child_marker = markers[-1]
            if child_marker not in result:
                raise AssertionError(
                    f"Iteration {iteration}: Expected child marker "
                    f"'{child_marker}' in result at depth {depth}, "
                    f"got: {result}"
                )
            
            # All ancestor markers should NOT be present (overridden)
            for level_idx in range(depth - 1):
                ancestor_marker = markers[level_idx]
                if ancestor_marker in result:
                    raise AssertionError(
                        f"Iteration {iteration}: Ancestor marker "
                        f"'{ancestor_marker}' at level {level_idx} should "
                        f"be overridden at depth {depth}, got: {result}"
                    )
            
            # Base template structural elements should be preserved
            if depth > 1:
                if "[START]" not in result:
                    raise AssertionError(
                        f"Iteration {iteration}: Expected '[START]' from "
                        f"base template at depth {depth}, got: {result}"
                    )
                if "[END]" not in result:
                    raise AssertionError(
                        f"Iteration {iteration}: Expected '[END]' from "
                        f"base template at depth {depth}, got: {result}"
                    )
        finally:
            _cleanup_temp_dir(temp_dir)
    
    return


def test_property_inheritance_chain_with_super():
    """
        Property 5: Template Inheritance Chain (super() variant)
        
        For any template inheritance chain of depth 1-5 where each child
        calls super(), the rendered output SHALL contain content markers
        from ALL levels in the chain, demonstrating that super() correctly
        invokes parent block content.
        
        **Validates: Requirements 4.1, 4.2, 4.3, 4.9**
    """
    rng = random.Random(99)
    num_iterations = 100
    
    for iteration in range(num_iterations):
        depth = rng.randint(1, 5)
        templates, markers = _build_inheritance_chain_with_super(rng, depth)
        
        temp_dir = _create_temp_template_dir(templates)
        
        try:
            adapter = Jinja2Adapter(
                template_dirs=[temp_dir],
                auto_escape=False
            )
            
            # Render the deepest child template
            child_template = f"super_level_{depth - 1}.html"
            result = adapter.render(child_template, {})
            
            # When using super(), ALL markers should be present
            for level_idx in range(depth):
                marker = markers[level_idx]
                if marker not in result:
                    raise AssertionError(
                        f"Iteration {iteration}: Expected marker "
                        f"'{marker}' at level {level_idx} in result "
                        f"(depth {depth} with super()), got: {result}"
                    )
            
            # Verify ordering: child marker should appear before parent
            # markers due to the template structure "CHILD|{{ super() }}"
            if depth > 1:
                child_pos = result.index(markers[-1])
                parent_pos = result.index(markers[-2])
                if child_pos > parent_pos:
                    raise AssertionError(
                        f"Iteration {iteration}: Child marker should "
                        f"appear before parent marker in super() chain. "
                        f"Child pos: {child_pos}, Parent pos: {parent_pos}, "
                        f"result: {result}"
                    )
        finally:
            _cleanup_temp_dir(temp_dir)
    
    return

