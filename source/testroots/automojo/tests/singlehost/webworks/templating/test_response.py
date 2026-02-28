"""
    Tests for the template response integration module.
    
    This module tests the response integration including:
    - TemplateResponse class (body, status_code, content_type, headers)
    - StreamingTemplateResponse class (body_iterator, status_code, content_type, headers)
    - render_template() helper function
    - render_template_stream() helper function
    - Request context injection
    - Property test for response integration correctness
"""

import os
import random
import shutil
import string
import tempfile

from automojo.webworks.templating.jinja2_adapter import Jinja2Adapter
from automojo.webworks.templating.renderer import TemplateRenderer
from automojo.webworks.templating.response import (
    StreamingTemplateResponse,
    TemplateResponse,
    render_template,
    render_template_stream,
)


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


def _create_renderer_with_template(template_name: str, template_content: str):
    """
        Create a TemplateRenderer with a single template file.
        
        :param template_name: Name of the template file.
        :param template_content: Content of the template file.
        
        :returns: Tuple of (renderer, temp_dir) for cleanup.
    """
    temp_dir = _create_temp_template_dir({template_name: template_content})
    engine = Jinja2Adapter(template_dirs=[temp_dir])
    renderer = TemplateRenderer(engine)
    return renderer, temp_dir


# =============================================================================
# 17.1 - TemplateResponse Tests
# =============================================================================

def test_template_response_default_values():
    """
        Test that TemplateResponse has correct default values.
    """
    response = TemplateResponse(body="<h1>Hello</h1>")
    
    if response.body != "<h1>Hello</h1>":
        raise AssertionError(
            f"Expected body '<h1>Hello</h1>', got '{response.body}'"
        )
    
    if response.status_code != 200:
        raise AssertionError(
            f"Expected status_code 200, got {response.status_code}"
        )
    
    if response.content_type != "text/html; charset=utf-8":
        raise AssertionError(
            f"Expected content_type 'text/html; charset=utf-8', "
            f"got '{response.content_type}'"
        )
    
    if response.headers.get("Content-Type") != "text/html; charset=utf-8":
        raise AssertionError(
            f"Expected Content-Type header 'text/html; charset=utf-8', "
            f"got '{response.headers.get('Content-Type')}'"
        )
    
    return


def test_template_response_custom_status_code():
    """
        Test that TemplateResponse supports custom status codes.
    """
    response = TemplateResponse(body="Not Found", status_code=404)
    
    if response.status_code != 404:
        raise AssertionError(
            f"Expected status_code 404, got {response.status_code}"
        )
    
    return


def test_template_response_custom_content_type():
    """
        Test that TemplateResponse supports custom content types.
    """
    response = TemplateResponse(
        body='{"key": "value"}',
        content_type="application/json"
    )
    
    if response.content_type != "application/json":
        raise AssertionError(
            f"Expected content_type 'application/json', "
            f"got '{response.content_type}'"
        )
    
    if response.headers.get("Content-Type") != "application/json":
        raise AssertionError(
            f"Expected Content-Type header 'application/json', "
            f"got '{response.headers.get('Content-Type')}'"
        )
    
    return


def test_template_response_custom_headers():
    """
        Test that TemplateResponse supports custom headers.
    """
    custom_headers = {
        "X-Custom-Header": "custom-value",
        "Cache-Control": "no-cache",
    }
    
    response = TemplateResponse(
        body="<p>Test</p>",
        headers=custom_headers
    )
    
    headers = response.headers
    
    if headers.get("X-Custom-Header") != "custom-value":
        raise AssertionError(
            f"Expected X-Custom-Header 'custom-value', "
            f"got '{headers.get('X-Custom-Header')}'"
        )
    
    if headers.get("Cache-Control") != "no-cache":
        raise AssertionError(
            f"Expected Cache-Control 'no-cache', "
            f"got '{headers.get('Cache-Control')}'"
        )
    
    # Content-Type should still be present
    if "Content-Type" not in headers:
        raise AssertionError("Content-Type header should be present")
    
    return


def test_template_response_headers_returns_copy():
    """
        Test that headers property returns a copy, not the internal dict.
    """
    response = TemplateResponse(body="test")
    headers1 = response.headers
    headers2 = response.headers
    
    if headers1 is headers2:
        raise AssertionError("headers should return a new copy each time")
    
    return


# =============================================================================
# 17.2 - StreamingTemplateResponse Tests
# =============================================================================

def test_streaming_response_default_values():
    """
        Test that StreamingTemplateResponse has correct default values.
    """
    chunks = iter(["<h1>", "Hello", "</h1>"])
    response = StreamingTemplateResponse(body_iterator=chunks)
    
    if response.status_code != 200:
        raise AssertionError(
            f"Expected status_code 200, got {response.status_code}"
        )
    
    if response.content_type != "text/html; charset=utf-8":
        raise AssertionError(
            f"Expected content_type 'text/html; charset=utf-8', "
            f"got '{response.content_type}'"
        )
    
    return


def test_streaming_response_body_iterator():
    """
        Test that StreamingTemplateResponse provides the body iterator.
    """
    expected_chunks = ["<h1>", "Hello", "</h1>"]
    chunks = iter(expected_chunks)
    response = StreamingTemplateResponse(body_iterator=chunks)
    
    collected = list(response.body_iterator)
    
    if collected != expected_chunks:
        raise AssertionError(
            f"Expected chunks {expected_chunks}, got {collected}"
        )
    
    return


def test_streaming_response_custom_status_and_headers():
    """
        Test that StreamingTemplateResponse supports custom status and headers.
    """
    chunks = iter(["data"])
    custom_headers = {"X-Stream": "true"}
    
    response = StreamingTemplateResponse(
        body_iterator=chunks,
        status_code=206,
        content_type="text/plain",
        headers=custom_headers
    )
    
    if response.status_code != 206:
        raise AssertionError(
            f"Expected status_code 206, got {response.status_code}"
        )
    
    if response.content_type != "text/plain":
        raise AssertionError(
            f"Expected content_type 'text/plain', got '{response.content_type}'"
        )
    
    if response.headers.get("X-Stream") != "true":
        raise AssertionError(
            f"Expected X-Stream header 'true', "
            f"got '{response.headers.get('X-Stream')}'"
        )
    
    return


# =============================================================================
# 17.1 - render_template() Tests
# =============================================================================

def test_render_template_basic():
    """
        Test that render_template() returns a TemplateResponse with rendered body.
    """
    renderer, temp_dir = _create_renderer_with_template(
        "hello.html", "<h1>Hello {{ name }}</h1>"
    )
    
    try:
        response = render_template(
            "hello.html",
            context={"name": "World"},
            renderer=renderer
        )
        
        if not isinstance(response, TemplateResponse):
            raise AssertionError("Expected TemplateResponse instance")
        
        if response.body != "<h1>Hello World</h1>":
            raise AssertionError(
                f"Expected body '<h1>Hello World</h1>', got '{response.body}'"
            )
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_render_template_default_content_type():
    """
        Test that render_template() sets Content-Type to text/html by default.
    """
    renderer, temp_dir = _create_renderer_with_template(
        "page.html", "<p>Test</p>"
    )
    
    try:
        response = render_template("page.html", renderer=renderer)
        
        if response.content_type != "text/html; charset=utf-8":
            raise AssertionError(
                f"Expected content_type 'text/html; charset=utf-8', "
                f"got '{response.content_type}'"
            )
        
        if response.headers.get("Content-Type") != "text/html; charset=utf-8":
            raise AssertionError(
                f"Expected Content-Type header 'text/html; charset=utf-8', "
                f"got '{response.headers.get('Content-Type')}'"
            )
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_render_template_custom_status_code():
    """
        Test that render_template() supports custom status codes.
    """
    renderer, temp_dir = _create_renderer_with_template(
        "error.html", "<h1>Not Found</h1>"
    )
    
    try:
        response = render_template(
            "error.html",
            status_code=404,
            renderer=renderer
        )
        
        if response.status_code != 404:
            raise AssertionError(
                f"Expected status_code 404, got {response.status_code}"
            )
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_render_template_custom_content_type():
    """
        Test that render_template() supports custom Content-Type.
    """
    renderer, temp_dir = _create_renderer_with_template(
        "data.xml", "<data>{{ value }}</data>"
    )
    
    try:
        response = render_template(
            "data.xml",
            context={"value": "test"},
            content_type="application/xml",
            renderer=renderer
        )
        
        if response.content_type != "application/xml":
            raise AssertionError(
                f"Expected content_type 'application/xml', "
                f"got '{response.content_type}'"
            )
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_render_template_custom_headers():
    """
        Test that render_template() supports custom headers.
    """
    renderer, temp_dir = _create_renderer_with_template(
        "page.html", "<p>Test</p>"
    )
    
    try:
        response = render_template(
            "page.html",
            headers={"X-Custom": "value"},
            renderer=renderer
        )
        
        if response.headers.get("X-Custom") != "value":
            raise AssertionError(
                f"Expected X-Custom header 'value', "
                f"got '{response.headers.get('X-Custom')}'"
            )
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_render_template_with_kwargs():
    """
        Test that render_template() passes kwargs to the template context.
    """
    renderer, temp_dir = _create_renderer_with_template(
        "greet.html", "Hello {{ name }}, age {{ age }}"
    )
    
    try:
        response = render_template(
            "greet.html",
            renderer=renderer,
            name="Alice",
            age=30
        )
        
        if response.body != "Hello Alice, age 30":
            raise AssertionError(
                f"Expected body 'Hello Alice, age 30', got '{response.body}'"
            )
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_render_template_raises_without_renderer():
    """
        Test that render_template() raises ValueError when renderer is None.
    """
    raised = False
    
    try:
        render_template("test.html")
    except ValueError:
        raised = True
    
    if not raised:
        raise AssertionError("Expected ValueError when renderer is None")
    
    return


# =============================================================================
# 17.2 - render_template_stream() Tests
# =============================================================================

def test_render_template_stream_basic():
    """
        Test that render_template_stream() returns a StreamingTemplateResponse.
    """
    renderer, temp_dir = _create_renderer_with_template(
        "stream.html", "<p>{{ message }}</p>"
    )
    
    try:
        response = render_template_stream(
            "stream.html",
            context={"message": "Streaming"},
            renderer=renderer
        )
        
        if not isinstance(response, StreamingTemplateResponse):
            raise AssertionError("Expected StreamingTemplateResponse instance")
        
        # Collect the streamed chunks
        body = "".join(response.body_iterator)
        
        if body != "<p>Streaming</p>":
            raise AssertionError(
                f"Expected body '<p>Streaming</p>', got '{body}'"
            )
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_render_template_stream_raises_without_renderer():
    """
        Test that render_template_stream() raises ValueError when renderer is None.
    """
    raised = False
    
    try:
        render_template_stream("test.html")
    except ValueError:
        raised = True
    
    if not raised:
        raise AssertionError("Expected ValueError when renderer is None")
    
    return


# =============================================================================
# 17.3 - Request Context Integration Tests
# =============================================================================

def test_render_template_with_request_context():
    """
        Test that render_template() injects request context variables.
    """
    renderer, temp_dir = _create_renderer_with_template(
        "req.html", "User: {{ user }}, Path: {{ path }}"
    )
    
    try:
        response = render_template(
            "req.html",
            request_context={"user": "admin", "path": "/dashboard"},
            renderer=renderer
        )
        
        if response.body != "User: admin, Path: /dashboard":
            raise AssertionError(
                f"Expected body 'User: admin, Path: /dashboard', "
                f"got '{response.body}'"
            )
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_render_template_context_overrides_request_context():
    """
        Test that passed context overrides request context variables.
    """
    renderer, temp_dir = _create_renderer_with_template(
        "override.html", "Value: {{ key }}"
    )
    
    try:
        response = render_template(
            "override.html",
            context={"key": "from_context"},
            request_context={"key": "from_request"},
            renderer=renderer
        )
        
        if response.body != "Value: from_context":
            raise AssertionError(
                f"Expected body 'Value: from_context', got '{response.body}'"
            )
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_render_template_kwargs_override_all():
    """
        Test that kwargs override both request context and passed context.
    """
    renderer, temp_dir = _create_renderer_with_template(
        "priority.html", "Value: {{ key }}"
    )
    
    try:
        response = render_template(
            "priority.html",
            context={"key": "from_context"},
            request_context={"key": "from_request"},
            renderer=renderer,
            key="from_kwargs"
        )
        
        if response.body != "Value: from_kwargs":
            raise AssertionError(
                f"Expected body 'Value: from_kwargs', got '{response.body}'"
            )
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_render_template_stream_with_request_context():
    """
        Test that render_template_stream() injects request context variables.
    """
    renderer, temp_dir = _create_renderer_with_template(
        "stream_req.html", "User: {{ user }}"
    )
    
    try:
        response = render_template_stream(
            "stream_req.html",
            request_context={"user": "admin"},
            renderer=renderer
        )
        
        body = "".join(response.body_iterator)
        
        if body != "User: admin":
            raise AssertionError(
                f"Expected body 'User: admin', got '{body}'"
            )
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


def test_render_template_uses_configured_engine():
    """
        Test that render_template() uses the configured template engine
        from the renderer.
    """
    renderer, temp_dir = _create_renderer_with_template(
        "engine.html", "{% if show %}<p>Visible</p>{% endif %}"
    )
    
    try:
        response = render_template(
            "engine.html",
            context={"show": True},
            renderer=renderer
        )
        
        if response.body != "<p>Visible</p>":
            raise AssertionError(
                f"Expected body '<p>Visible</p>', got '{response.body}'"
            )
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return


# =============================================================================
# 17.4 - Property-Based Tests
# =============================================================================

def _generate_random_string(min_length: int = 1, max_length: int = 50) -> str:
    """
        Generate a random string for property testing.
        
        :param min_length: Minimum string length.
        :param max_length: Maximum string length.
        
        :returns: Random string of alphanumeric characters and spaces.
    """
    length = random.randint(min_length, max_length)
    chars = string.ascii_letters + string.digits + " _-."
    return "".join(random.choice(chars) for _ in range(length))


def _generate_random_identifier(min_length: int = 3, max_length: int = 15) -> str:
    """
        Generate a random valid Python/template identifier.
        
        :param min_length: Minimum identifier length.
        :param max_length: Maximum identifier length.
        
        :returns: Random valid identifier string.
    """
    length = random.randint(min_length, max_length)
    first_char = random.choice(string.ascii_lowercase)
    rest_chars = "".join(
        random.choice(string.ascii_lowercase + string.digits + "_")
        for _ in range(length - 1)
    )
    return first_char + rest_chars


def _generate_random_status_code() -> int:
    """
        Generate a random HTTP status code.
        
        :returns: Random HTTP status code from common values.
    """
    common_codes = [
        200, 201, 202, 204,
        301, 302, 304,
        400, 401, 403, 404, 405, 409, 422,
        500, 502, 503,
    ]
    return random.choice(common_codes)


def _generate_random_content_type() -> str:
    """
        Generate a random Content-Type value.
        
        :returns: Random Content-Type string.
    """
    content_types = [
        "text/html; charset=utf-8",
        "text/plain",
        "application/json",
        "application/xml",
        "text/css",
        "text/html",
    ]
    return random.choice(content_types)


def test_property_response_integration_correctness():
    """
        Property test for response integration correctness.
        
        **Property 10: Response Integration Correctness**
        
        *For any* call to render_template(), the returned Response SHALL
        have Content-Type set to the specified value (default text/html),
        status code set to the specified value (default 200), and body
        containing the rendered template output.
        
        **Validates: Requirements 8.1, 8.2, 8.4**
        
        This property test verifies that:
        1. The response status_code matches the requested status code
        2. The response content_type matches the requested content type
        3. The response body matches what the renderer produces directly
        4. The Content-Type header is always present in the headers dict
        5. Custom headers are included in the response
        
        Test strategy:
        - Generate random template content with random context variables
        - Generate random status codes and content types
        - Call render_template() and verify the response attributes match
        - Compare the response body against a direct renderer.render() call
    """
    iterations = 100
    
    temp_dir = _create_temp_template_dir({})
    
    try:
        engine = Jinja2Adapter(template_dirs=[temp_dir])
        renderer = TemplateRenderer(engine)
        
        for iteration in range(iterations):
            # Generate random context with 1-5 variables
            num_vars = random.randint(1, 5)
            context = {}
            template_parts = []
            
            for _ in range(num_vars):
                key = _generate_random_identifier()
                value = _generate_random_string(1, 30)
                context[key] = value
                template_parts.append(f"{{{{ {key} }}}}")
            
            # Build a template string with static text and variables
            static_prefix = _generate_random_string(1, 20)
            template_content = static_prefix + " " + " | ".join(template_parts)
            
            # Write the template to a file
            template_name = f"prop_test_{iteration}.html"
            template_path = os.path.join(temp_dir, template_name)
            
            with open(template_path, "w", encoding="utf-8") as f:
                f.write(template_content)
            
            # Generate random status code and content type
            status_code = _generate_random_status_code()
            content_type = _generate_random_content_type()
            
            # Generate random custom headers
            custom_header_key = "X-" + _generate_random_identifier(3, 10).title()
            custom_header_value = _generate_random_string(1, 20)
            custom_headers = {custom_header_key: custom_header_value}
            
            # Get the expected body by rendering directly
            expected_body = renderer.render(template_name, context)
            
            # Call render_template()
            response = render_template(
                template_name,
                context=context,
                status_code=status_code,
                content_type=content_type,
                headers=custom_headers,
                renderer=renderer
            )
            
            # Verify status_code
            if response.status_code != status_code:
                raise AssertionError(
                    f"Iteration {iteration}: Expected status_code "
                    f"{status_code}, got {response.status_code}. "
                    f"Template: '{template_name}'"
                )
            
            # Verify content_type
            if response.content_type != content_type:
                raise AssertionError(
                    f"Iteration {iteration}: Expected content_type "
                    f"'{content_type}', got '{response.content_type}'. "
                    f"Template: '{template_name}'"
                )
            
            # Verify body matches direct render
            if response.body != expected_body:
                raise AssertionError(
                    f"Iteration {iteration}: Response body does not match "
                    f"direct render. Expected '{expected_body}', "
                    f"got '{response.body}'. "
                    f"Template: '{template_name}'"
                )
            
            # Verify Content-Type header is present
            if response.headers.get("Content-Type") != content_type:
                raise AssertionError(
                    f"Iteration {iteration}: Content-Type header mismatch. "
                    f"Expected '{content_type}', "
                    f"got '{response.headers.get('Content-Type')}'. "
                    f"Template: '{template_name}'"
                )
            
            # Verify custom headers are present
            if response.headers.get(custom_header_key) != custom_header_value:
                raise AssertionError(
                    f"Iteration {iteration}: Custom header "
                    f"'{custom_header_key}' mismatch. "
                    f"Expected '{custom_header_value}', "
                    f"got '{response.headers.get(custom_header_key)}'. "
                    f"Template: '{template_name}'"
                )
            
            # Clean up the template file
            os.remove(template_path)
    finally:
        _cleanup_temp_dir(temp_dir)
    
    return
