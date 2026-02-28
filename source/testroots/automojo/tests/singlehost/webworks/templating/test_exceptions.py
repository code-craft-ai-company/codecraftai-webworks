"""
    Tests for the template exception classes module.
    
    This module tests the template exception classes including:
    - TemplateSyntaxError with template name, line number, and source context
    - TemplateRenderError with template name, variable name, and line number
    - TemplateFilterNotFoundError with filter name and available filters
    - TemplateConfigurationError with field name
    - Existing exception classes (TemplateNotFoundError, TemplateEngineNotFoundError,
      UndefinedVariableError, TemplateInheritanceError)
    - Property test for error message completeness
"""

from automojo.webworks.templating.exceptions import (
    TemplateConfigurationError,
    TemplateEngineNotFoundError,
    TemplateError,
    TemplateFilterNotFoundError,
    TemplateInheritanceError,
    TemplateNotFoundError,
    TemplateRenderError,
    TemplateSyntaxError,
    UndefinedVariableError,
)


# =============================================================================
# TemplateSyntaxError Tests
# =============================================================================

def test_template_syntax_error_is_template_error():
    """
        Test that TemplateSyntaxError is a subclass of TemplateError.
    """
    exc = TemplateSyntaxError("page.html", 10, "unexpected tag")

    if not isinstance(exc, TemplateError):
        raise AssertionError(
            "TemplateSyntaxError should be a subclass of TemplateError"
        )

    return


def test_template_syntax_error_stores_template_name():
    """
        Test that TemplateSyntaxError stores the template name.
    """
    exc = TemplateSyntaxError("page.html", 10, "unexpected tag")

    if exc.template_name != "page.html":
        raise AssertionError(
            f"Expected template_name 'page.html', got '{exc.template_name}'"
        )

    return


def test_template_syntax_error_stores_line_number():
    """
        Test that TemplateSyntaxError stores the line number.
    """
    exc = TemplateSyntaxError("page.html", 42, "unexpected tag")

    if exc.line_number != 42:
        raise AssertionError(
            f"Expected line_number 42, got {exc.line_number}"
        )

    return


def test_template_syntax_error_message_includes_template_name():
    """
        Test that TemplateSyntaxError message includes the template name.
    """
    exc = TemplateSyntaxError("page.html", 10, "unexpected tag")
    message = str(exc)

    if "page.html" not in message:
        raise AssertionError(
            f"Expected 'page.html' in message, got: {message}"
        )

    return


def test_template_syntax_error_message_includes_line_number():
    """
        Test that TemplateSyntaxError message includes the line number.
    """
    exc = TemplateSyntaxError("page.html", 10, "unexpected tag")
    message = str(exc)

    if "10" not in message:
        raise AssertionError(
            f"Expected '10' in message, got: {message}"
        )

    return


def test_template_syntax_error_message_includes_description():
    """
        Test that TemplateSyntaxError message includes the error description.
    """
    exc = TemplateSyntaxError("page.html", 10, "unexpected tag")
    message = str(exc)

    if "unexpected tag" not in message:
        raise AssertionError(
            f"Expected 'unexpected tag' in message, got: {message}"
        )

    return


def test_template_syntax_error_with_source_context():
    """
        Test that TemplateSyntaxError includes source context when provided.
    """
    exc = TemplateSyntaxError(
        "page.html", 10, "unexpected tag",
        source_context="{% invalid %}"
    )

    if exc.source_context != "{% invalid %}":
        raise AssertionError(
            f"Expected source_context '{{%}} invalid {{%}}', got '{exc.source_context}'"
        )

    message = str(exc)
    if "{% invalid %}" not in message:
        raise AssertionError(
            f"Expected source context in message, got: {message}"
        )

    return


def test_template_syntax_error_without_source_context():
    """
        Test that TemplateSyntaxError works without source context.
    """
    exc = TemplateSyntaxError("page.html", 10, "unexpected tag")

    if exc.source_context is not None:
        raise AssertionError(
            f"Expected source_context None, got '{exc.source_context}'"
        )

    return


# =============================================================================
# TemplateRenderError Tests
# =============================================================================

def test_template_render_error_is_template_error():
    """
        Test that TemplateRenderError is a subclass of TemplateError.
    """
    exc = TemplateRenderError("page.html", "rendering failed")

    if not isinstance(exc, TemplateError):
        raise AssertionError(
            "TemplateRenderError should be a subclass of TemplateError"
        )

    return


def test_template_render_error_stores_template_name():
    """
        Test that TemplateRenderError stores the template name.
    """
    exc = TemplateRenderError("page.html", "rendering failed")

    if exc.template_name != "page.html":
        raise AssertionError(
            f"Expected template_name 'page.html', got '{exc.template_name}'"
        )

    return


def test_template_render_error_stores_variable_name():
    """
        Test that TemplateRenderError stores the variable name.
    """
    exc = TemplateRenderError(
        "page.html", "type error", variable_name="user.name"
    )

    if exc.variable_name != "user.name":
        raise AssertionError(
            f"Expected variable_name 'user.name', got '{exc.variable_name}'"
        )

    return


def test_template_render_error_message_includes_template_name():
    """
        Test that TemplateRenderError message includes the template name.
    """
    exc = TemplateRenderError("page.html", "rendering failed")
    message = str(exc)

    if "page.html" not in message:
        raise AssertionError(
            f"Expected 'page.html' in message, got: {message}"
        )

    return


def test_template_render_error_with_line_number():
    """
        Test that TemplateRenderError includes line number when provided.
    """
    exc = TemplateRenderError(
        "page.html", "type error", line_number=25
    )
    message = str(exc)

    if "25" not in message:
        raise AssertionError(
            f"Expected '25' in message, got: {message}"
        )

    return


def test_template_render_error_with_variable_name_in_message():
    """
        Test that TemplateRenderError includes variable name in message.
    """
    exc = TemplateRenderError(
        "page.html", "type error", variable_name="items"
    )
    message = str(exc)

    if "items" not in message:
        raise AssertionError(
            f"Expected 'items' in message, got: {message}"
        )

    return


def test_template_render_error_without_optional_fields():
    """
        Test that TemplateRenderError works without optional fields.
    """
    exc = TemplateRenderError("page.html", "rendering failed")

    if exc.variable_name is not None:
        raise AssertionError(
            f"Expected variable_name None, got '{exc.variable_name}'"
        )

    if exc.line_number is not None:
        raise AssertionError(
            f"Expected line_number None, got {exc.line_number}"
        )

    return


# =============================================================================
# TemplateFilterNotFoundError Tests
# =============================================================================

def test_template_filter_not_found_error_is_template_error():
    """
        Test that TemplateFilterNotFoundError is a subclass of TemplateError.
    """
    exc = TemplateFilterNotFoundError("custom_filter")

    if not isinstance(exc, TemplateError):
        raise AssertionError(
            "TemplateFilterNotFoundError should be a subclass of TemplateError"
        )

    return


def test_template_filter_not_found_error_stores_filter_name():
    """
        Test that TemplateFilterNotFoundError stores the filter name.
    """
    exc = TemplateFilterNotFoundError("custom_filter")

    if exc.filter_name != "custom_filter":
        raise AssertionError(
            f"Expected filter_name 'custom_filter', got '{exc.filter_name}'"
        )

    return


def test_template_filter_not_found_error_message_includes_filter_name():
    """
        Test that TemplateFilterNotFoundError message includes the filter name.
    """
    exc = TemplateFilterNotFoundError("custom_filter")
    message = str(exc)

    if "custom_filter" not in message:
        raise AssertionError(
            f"Expected 'custom_filter' in message, got: {message}"
        )

    return


def test_template_filter_not_found_error_with_available_filters():
    """
        Test that TemplateFilterNotFoundError includes available filters.
    """
    available = ["lower", "upper", "trim"]
    exc = TemplateFilterNotFoundError("custom_filter", available_filters=available)
    message = str(exc)

    if exc.available_filters != available:
        raise AssertionError(
            f"Expected available_filters {available}, got {exc.available_filters}"
        )

    for filter_name in available:
        if filter_name not in message:
            raise AssertionError(
                f"Expected '{filter_name}' in message, got: {message}"
            )

    return


def test_template_filter_not_found_error_without_available_filters():
    """
        Test that TemplateFilterNotFoundError works without available filters.
    """
    exc = TemplateFilterNotFoundError("custom_filter")

    if exc.available_filters != []:
        raise AssertionError(
            f"Expected empty available_filters, got {exc.available_filters}"
        )

    return


# =============================================================================
# TemplateConfigurationError Tests
# =============================================================================

def test_template_configuration_error_is_template_error():
    """
        Test that TemplateConfigurationError is a subclass of TemplateError.
    """
    exc = TemplateConfigurationError("invalid engine")

    if not isinstance(exc, TemplateError):
        raise AssertionError(
            "TemplateConfigurationError should be a subclass of TemplateError"
        )

    return


def test_template_configuration_error_stores_field_name():
    """
        Test that TemplateConfigurationError stores the field name.
    """
    exc = TemplateConfigurationError("invalid value", field_name="engine")

    if exc.field_name != "engine":
        raise AssertionError(
            f"Expected field_name 'engine', got '{exc.field_name}'"
        )

    return


def test_template_configuration_error_message_with_field_name():
    """
        Test that TemplateConfigurationError message includes the field name.
    """
    exc = TemplateConfigurationError("invalid value", field_name="engine")
    message = str(exc)

    if "engine" not in message:
        raise AssertionError(
            f"Expected 'engine' in message, got: {message}"
        )

    if "invalid value" not in message:
        raise AssertionError(
            f"Expected 'invalid value' in message, got: {message}"
        )

    return


def test_template_configuration_error_message_without_field_name():
    """
        Test that TemplateConfigurationError works without field name.
    """
    exc = TemplateConfigurationError("general config error")
    message = str(exc)

    if exc.field_name is not None:
        raise AssertionError(
            f"Expected field_name None, got '{exc.field_name}'"
        )

    if "general config error" not in message:
        raise AssertionError(
            f"Expected 'general config error' in message, got: {message}"
        )

    return


# =============================================================================
# Existing Exception Classes - Verification Tests
# =============================================================================

def test_template_not_found_error_includes_template_name():
    """
        Test that TemplateNotFoundError message includes the template name.
    """
    exc = TemplateNotFoundError("missing.html", ["/templates", "/views"])
    message = str(exc)

    if "missing.html" not in message:
        raise AssertionError(
            f"Expected 'missing.html' in message, got: {message}"
        )

    return


def test_template_engine_not_found_error_includes_engine_name():
    """
        Test that TemplateEngineNotFoundError message includes the engine name.
    """
    exc = TemplateEngineNotFoundError("django", ["jinja2", "mako"])
    message = str(exc)

    if "django" not in message:
        raise AssertionError(
            f"Expected 'django' in message, got: {message}"
        )

    return


def test_undefined_variable_error_includes_variable_name():
    """
        Test that UndefinedVariableError message includes the variable name.
    """
    exc = UndefinedVariableError("missing_var")
    message = str(exc)

    if "missing_var" not in message:
        raise AssertionError(
            f"Expected 'missing_var' in message, got: {message}"
        )

    return


def test_template_inheritance_error_includes_chain():
    """
        Test that TemplateInheritanceError message includes the chain.
    """
    chain = ["child.html", "parent.html", "child.html"]
    exc = TemplateInheritanceError("Circular inheritance detected", chain=chain)
    message = str(exc)

    for template_name in chain:
        if template_name not in message:
            raise AssertionError(
                f"Expected '{template_name}' in message, got: {message}"
            )

    return


# =============================================================================
# Property-Based Tests
# =============================================================================

import random
import string


def _generate_random_template_name() -> str:
    """
        Generate a random template name for property testing.

        Generates names with random alphanumeric characters and a
        random file extension from common template extensions.

        :returns: Random template name string.
    """
    length = random.randint(3, 30)
    chars = string.ascii_lowercase + string.digits + "_-"
    name = "".join(random.choice(chars) for _ in range(length))
    extensions = [".html", ".htm", ".xml", ".txt", ".jinja2", ".mako"]
    ext = random.choice(extensions)
    return f"{name}{ext}"


def _generate_random_line_number() -> int:
    """
        Generate a random line number for property testing.

        Generates line numbers in a realistic range for template files.

        :returns: Random positive line number.
    """
    return random.randint(1, 10000)


def _generate_random_message() -> str:
    """
        Generate a random error message for property testing.

        :returns: Random error message string.
    """
    length = random.randint(5, 100)
    chars = string.ascii_letters + string.digits + " _-.,;:!?"
    return "".join(random.choice(chars) for _ in range(length))


def test_property_error_message_completeness_syntax_error():
    """
        Property test for error message completeness on TemplateSyntaxError.

        **Property 9: Error Message Completeness**

        *For any* template error (syntax error), the error message SHALL
        include the template filename and line number where the error
        occurred.

        **Validates: Requirements 9.1, 9.2**

        This property test verifies that:
        1. For any randomly generated template name and line number,
           the TemplateSyntaxError message always contains both values
        2. This holds across 100 random iterations

        Test strategy:
        - Generate random template names and line numbers
        - Create TemplateSyntaxError instances
        - Verify the error message contains both the template name and line number
    """
    iterations = 100

    for iteration in range(iterations):
        template_name = _generate_random_template_name()
        line_number = _generate_random_line_number()
        description = _generate_random_message()

        exc = TemplateSyntaxError(template_name, line_number, description)
        message = str(exc)

        if template_name not in message:
            raise AssertionError(
                f"Iteration {iteration}: Expected template name "
                f"'{template_name}' in error message, got: {message}"
            )

        if str(line_number) not in message:
            raise AssertionError(
                f"Iteration {iteration}: Expected line number "
                f"'{line_number}' in error message, got: {message}"
            )

    return


def test_property_error_message_completeness_render_error():
    """
        Property test for error message completeness on TemplateRenderError.

        **Property 9: Error Message Completeness**

        *For any* template error (render error with line number), the error
        message SHALL include the template filename and line number where
        the error occurred.

        **Validates: Requirements 9.1, 9.2**

        This property test verifies that:
        1. For any randomly generated template name and line number,
           the TemplateRenderError message always contains both values
        2. This holds across 100 random iterations

        Test strategy:
        - Generate random template names and line numbers
        - Create TemplateRenderError instances with line numbers
        - Verify the error message contains both the template name and line number
    """
    iterations = 100

    for iteration in range(iterations):
        template_name = _generate_random_template_name()
        line_number = _generate_random_line_number()
        description = _generate_random_message()

        exc = TemplateRenderError(
            template_name, description, line_number=line_number
        )
        message = str(exc)

        if template_name not in message:
            raise AssertionError(
                f"Iteration {iteration}: Expected template name "
                f"'{template_name}' in error message, got: {message}"
            )

        if str(line_number) not in message:
            raise AssertionError(
                f"Iteration {iteration}: Expected line number "
                f"'{line_number}' in error message, got: {message}"
            )

    return


def test_property_error_message_completeness_not_found_error():
    """
        Property test for error message completeness on TemplateNotFoundError.

        **Property 9: Error Message Completeness**

        *For any* template error (missing template), the error message SHALL
        include the template filename.

        **Validates: Requirements 9.1, 9.2**

        This property test verifies that:
        1. For any randomly generated template name,
           the TemplateNotFoundError message always contains the template name
        2. This holds across 100 random iterations

        Test strategy:
        - Generate random template names and search paths
        - Create TemplateNotFoundError instances
        - Verify the error message contains the template name
    """
    iterations = 100

    for iteration in range(iterations):
        template_name = _generate_random_template_name()
        num_paths = random.randint(0, 5)
        searched_paths = [
            f"/templates/dir{i}" for i in range(num_paths)
        ]

        exc = TemplateNotFoundError(template_name, searched_paths)
        message = str(exc)

        if template_name not in message:
            raise AssertionError(
                f"Iteration {iteration}: Expected template name "
                f"'{template_name}' in error message, got: {message}"
            )

    return
