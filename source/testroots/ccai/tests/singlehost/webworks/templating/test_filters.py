"""
    Tests for the built-in template filters.

    This module tests the filter functions including:
    - String manipulation filters: lower, upper, title, trim, format
    - Collection filters: length, join, first, last, sort, reverse
    - Utility filters: safe, escape, default, date, json
    - BUILTIN_FILTERS registry
    - apply_filters helper function
    - Property test for filter chaining correctness
"""

import random
from datetime import date, datetime

from ccai.webworks.templating.escaping import SafeString
from ccai.webworks.templating.filters import (
    BUILTIN_FILTERS,
    apply_filters,
    filter_date,
    filter_default,
    filter_escape,
    filter_first,
    filter_format,
    filter_join,
    filter_json,
    filter_last,
    filter_length,
    filter_lower,
    filter_reverse,
    filter_safe,
    filter_sort,
    filter_title,
    filter_trim,
    filter_upper,
)


# =============================================================================
# String Manipulation Filter Tests
# =============================================================================

def test_filter_lower_basic():
    """
        Test that filter_lower converts a string to lowercase.
    """
    result = filter_lower("HELLO")

    if result != "hello":
        raise AssertionError(f"Expected 'hello', got '{result}'")

    return


def test_filter_lower_mixed_case():
    """
        Test that filter_lower handles mixed case strings.
    """
    result = filter_lower("Hello World")

    if result != "hello world":
        raise AssertionError(f"Expected 'hello world', got '{result}'")

    return


def test_filter_lower_non_string():
    """
        Test that filter_lower converts non-string values to string first.
    """
    result = filter_lower(123)

    if result != "123":
        raise AssertionError(f"Expected '123', got '{result}'")

    return


def test_filter_upper_basic():
    """
        Test that filter_upper converts a string to uppercase.
    """
    result = filter_upper("hello")

    if result != "HELLO":
        raise AssertionError(f"Expected 'HELLO', got '{result}'")

    return


def test_filter_upper_mixed_case():
    """
        Test that filter_upper handles mixed case strings.
    """
    result = filter_upper("Hello World")

    if result != "HELLO WORLD":
        raise AssertionError(f"Expected 'HELLO WORLD', got '{result}'")

    return


def test_filter_title_basic():
    """
        Test that filter_title converts a string to title case.
    """
    result = filter_title("hello world")

    if result != "Hello World":
        raise AssertionError(f"Expected 'Hello World', got '{result}'")

    return


def test_filter_title_all_caps():
    """
        Test that filter_title handles all-caps input.
    """
    result = filter_title("HELLO WORLD")

    if result != "Hello World":
        raise AssertionError(f"Expected 'Hello World', got '{result}'")

    return


def test_filter_trim_basic():
    """
        Test that filter_trim strips whitespace.
    """
    result = filter_trim("  hello  ")

    if result != "hello":
        raise AssertionError(f"Expected 'hello', got '{result}'")

    return


def test_filter_trim_tabs_and_newlines():
    """
        Test that filter_trim strips tabs and newlines.
    """
    result = filter_trim("\t\nhello\n\t")

    if result != "hello":
        raise AssertionError(f"Expected 'hello', got '{result}'")

    return


def test_filter_trim_no_whitespace():
    """
        Test that filter_trim returns unchanged string with no whitespace.
    """
    result = filter_trim("hello")

    if result != "hello":
        raise AssertionError(f"Expected 'hello', got '{result}'")

    return


def test_filter_format_positional():
    """
        Test that filter_format handles positional arguments.
    """
    result = filter_format("Hello, {}!", "World")

    if result != "Hello, World!":
        raise AssertionError(f"Expected 'Hello, World!', got '{result}'")

    return


def test_filter_format_keyword():
    """
        Test that filter_format handles keyword arguments.
    """
    result = filter_format("{name} is {age}", name="Alice", age=30)

    if result != "Alice is 30":
        raise AssertionError(f"Expected 'Alice is 30', got '{result}'")

    return


def test_filter_format_mixed():
    """
        Test that filter_format handles mixed positional and keyword args.
    """
    result = filter_format("{} is {age}", "Alice", age=30)

    if result != "Alice is 30":
        raise AssertionError(f"Expected 'Alice is 30', got '{result}'")

    return


# =============================================================================
# Collection Filter Tests
# =============================================================================

def test_filter_length_list():
    """
        Test that filter_length returns the length of a list.
    """
    result = filter_length([1, 2, 3])

    if result != 3:
        raise AssertionError(f"Expected 3, got {result}")

    return


def test_filter_length_string():
    """
        Test that filter_length returns the length of a string.
    """
    result = filter_length("hello")

    if result != 5:
        raise AssertionError(f"Expected 5, got {result}")

    return


def test_filter_length_empty():
    """
        Test that filter_length returns 0 for empty collections.
    """
    result = filter_length([])

    if result != 0:
        raise AssertionError(f"Expected 0, got {result}")

    return


def test_filter_join_basic():
    """
        Test that filter_join joins list elements with separator.
    """
    result = filter_join(["a", "b", "c"], ", ")

    if result != "a, b, c":
        raise AssertionError(f"Expected 'a, b, c', got '{result}'")

    return


def test_filter_join_default_separator():
    """
        Test that filter_join uses empty string as default separator.
    """
    result = filter_join(["a", "b", "c"])

    if result != "abc":
        raise AssertionError(f"Expected 'abc', got '{result}'")

    return


def test_filter_join_non_string_elements():
    """
        Test that filter_join converts elements to strings.
    """
    result = filter_join([1, 2, 3], "-")

    if result != "1-2-3":
        raise AssertionError(f"Expected '1-2-3', got '{result}'")

    return


def test_filter_first_basic():
    """
        Test that filter_first returns the first element.
    """
    result = filter_first([10, 20, 30])

    if result != 10:
        raise AssertionError(f"Expected 10, got {result}")

    return


def test_filter_first_empty():
    """
        Test that filter_first returns None for empty list.
    """
    result = filter_first([])

    if result is not None:
        raise AssertionError(f"Expected None, got {result}")

    return


def test_filter_last_basic():
    """
        Test that filter_last returns the last element.
    """
    result = filter_last([10, 20, 30])

    if result != 30:
        raise AssertionError(f"Expected 30, got {result}")

    return


def test_filter_last_empty():
    """
        Test that filter_last returns None for empty list.
    """
    result = filter_last([])

    if result is not None:
        raise AssertionError(f"Expected None, got {result}")

    return


def test_filter_sort_basic():
    """
        Test that filter_sort sorts a list in ascending order.
    """
    result = filter_sort([3, 1, 2])

    if result != [1, 2, 3]:
        raise AssertionError(f"Expected [1, 2, 3], got {result}")

    return


def test_filter_sort_reverse():
    """
        Test that filter_sort sorts in descending order with reverse=True.
    """
    result = filter_sort([3, 1, 2], reverse=True)

    if result != [3, 2, 1]:
        raise AssertionError(f"Expected [3, 2, 1], got {result}")

    return


def test_filter_sort_does_not_modify_original():
    """
        Test that filter_sort returns a new list without modifying the original.
    """
    original = [3, 1, 2]
    result = filter_sort(original)

    if original != [3, 1, 2]:
        raise AssertionError(f"Original list was modified: {original}")

    if result != [1, 2, 3]:
        raise AssertionError(f"Expected [1, 2, 3], got {result}")

    return


def test_filter_reverse_basic():
    """
        Test that filter_reverse reverses a list.
    """
    result = filter_reverse([1, 2, 3])

    if result != [3, 2, 1]:
        raise AssertionError(f"Expected [3, 2, 1], got {result}")

    return


def test_filter_reverse_does_not_modify_original():
    """
        Test that filter_reverse returns a new list without modifying the original.
    """
    original = [1, 2, 3]
    result = filter_reverse(original)

    if original != [1, 2, 3]:
        raise AssertionError(f"Original list was modified: {original}")

    if result != [3, 2, 1]:
        raise AssertionError(f"Expected [3, 2, 1], got {result}")

    return


# =============================================================================
# Utility Filter Tests
# =============================================================================

def test_filter_safe_returns_safe_string():
    """
        Test that filter_safe returns a SafeString instance.
    """
    result = filter_safe("hello")

    if not isinstance(result, SafeString):
        raise AssertionError(f"Expected SafeString, got {type(result)}")

    return


def test_filter_safe_preserves_value():
    """
        Test that filter_safe preserves the string value.
    """
    result = filter_safe("<b>bold</b>")

    if str(result) != "<b>bold</b>":
        raise AssertionError(f"Expected '<b>bold</b>', got '{result}'")

    return


def test_filter_escape_basic():
    """
        Test that filter_escape escapes HTML special characters.
    """
    result = filter_escape("<script>alert('xss')</script>")

    expected = "&lt;script&gt;alert(&#39;xss&#39;)&lt;/script&gt;"
    if result != expected:
        raise AssertionError(f"Expected '{expected}', got '{result}'")

    return


def test_filter_escape_ampersand():
    """
        Test that filter_escape escapes ampersands.
    """
    result = filter_escape("Tom & Jerry")

    if result != "Tom &amp; Jerry":
        raise AssertionError(f"Expected 'Tom &amp; Jerry', got '{result}'")

    return


def test_filter_default_with_truthy_value():
    """
        Test that filter_default returns the value when truthy.
    """
    result = filter_default("hello", "default")

    if result != "hello":
        raise AssertionError(f"Expected 'hello', got '{result}'")

    return


def test_filter_default_with_falsy_value():
    """
        Test that filter_default returns the default when value is falsy.
    """
    result = filter_default("", "default")

    if result != "default":
        raise AssertionError(f"Expected 'default', got '{result}'")

    return


def test_filter_default_with_none():
    """
        Test that filter_default returns the default when value is None.
    """
    result = filter_default(None, "fallback")

    if result != "fallback":
        raise AssertionError(f"Expected 'fallback', got '{result}'")

    return


def test_filter_default_empty_default():
    """
        Test that filter_default uses empty string as default.
    """
    result = filter_default(None)

    if result != "":
        raise AssertionError(f"Expected '', got '{result}'")

    return


def test_filter_date_datetime():
    """
        Test that filter_date formats a datetime object.
    """
    dt = datetime(2024, 6, 15, 10, 30, 0)
    result = filter_date(dt)

    if result != "2024-06-15":
        raise AssertionError(f"Expected '2024-06-15', got '{result}'")

    return


def test_filter_date_custom_format():
    """
        Test that filter_date uses a custom format string.
    """
    dt = datetime(2024, 6, 15, 10, 30, 0)
    result = filter_date(dt, "%Y/%m/%d %H:%M")

    if result != "2024/06/15 10:30":
        raise AssertionError(f"Expected '2024/06/15 10:30', got '{result}'")

    return


def test_filter_date_date_object():
    """
        Test that filter_date formats a date object.
    """
    d = date(2024, 6, 15)
    result = filter_date(d)

    if result != "2024-06-15":
        raise AssertionError(f"Expected '2024-06-15', got '{result}'")

    return


def test_filter_date_string_passthrough():
    """
        Test that filter_date returns string values as-is.
    """
    result = filter_date("2024-06-15")

    if result != "2024-06-15":
        raise AssertionError(f"Expected '2024-06-15', got '{result}'")

    return


def test_filter_json_dict():
    """
        Test that filter_json serializes a dictionary.
    """
    result = filter_json({"name": "Alice", "age": 30})

    # Parse back to verify correctness
    import json
    parsed = json.loads(result)
    if parsed != {"name": "Alice", "age": 30}:
        raise AssertionError(f"Expected dict with name/age, got {parsed}")

    return


def test_filter_json_list():
    """
        Test that filter_json serializes a list.
    """
    result = filter_json([1, 2, 3])

    if result != "[1, 2, 3]":
        raise AssertionError(f"Expected '[1, 2, 3]', got '{result}'")

    return


def test_filter_json_string():
    """
        Test that filter_json serializes a string.
    """
    result = filter_json("hello")

    if result != '"hello"':
        raise AssertionError(f"Expected '\"hello\"', got '{result}'")

    return


def test_filter_json_number():
    """
        Test that filter_json serializes a number.
    """
    result = filter_json(42)

    if result != "42":
        raise AssertionError(f"Expected '42', got '{result}'")

    return


def test_filter_json_none():
    """
        Test that filter_json serializes None to null.
    """
    result = filter_json(None)

    if result != "null":
        raise AssertionError(f"Expected 'null', got '{result}'")

    return


# =============================================================================
# BUILTIN_FILTERS Registry Tests
# =============================================================================

def test_builtin_filters_contains_all_filters():
    """
        Test that BUILTIN_FILTERS contains all expected filter names.
    """
    expected_names = [
        "safe", "escape", "e", "lower", "upper", "title", "trim",
        "default", "d", "length", "join", "first", "last", "sort",
        "reverse", "format", "date", "json",
    ]

    for name in expected_names:
        if name not in BUILTIN_FILTERS:
            raise AssertionError(f"Missing filter '{name}' in BUILTIN_FILTERS")

    return


def test_builtin_filters_escape_alias():
    """
        Test that 'e' is an alias for 'escape' in BUILTIN_FILTERS.
    """
    if BUILTIN_FILTERS["e"] is not BUILTIN_FILTERS["escape"]:
        raise AssertionError("'e' should be an alias for 'escape'")

    return


def test_builtin_filters_default_alias():
    """
        Test that 'd' is an alias for 'default' in BUILTIN_FILTERS.
    """
    if BUILTIN_FILTERS["d"] is not BUILTIN_FILTERS["default"]:
        raise AssertionError("'d' should be an alias for 'default'")

    return


# =============================================================================
# apply_filters Tests
# =============================================================================

def test_apply_filters_single_filter():
    """
        Test that apply_filters applies a single filter correctly.
    """
    result = apply_filters("HELLO", ["lower"])

    if result != "hello":
        raise AssertionError(f"Expected 'hello', got '{result}'")

    return


def test_apply_filters_chain():
    """
        Test that apply_filters applies filters left-to-right.
    """
    result = apply_filters("  HELLO  ", ["trim", "lower"])

    if result != "hello":
        raise AssertionError(f"Expected 'hello', got '{result}'")

    return


def test_apply_filters_empty_list():
    """
        Test that apply_filters returns the original value with no filters.
    """
    result = apply_filters("hello", [])

    if result != "hello":
        raise AssertionError(f"Expected 'hello', got '{result}'")

    return


def test_apply_filters_upper_then_lower():
    """
        Test that apply_filters chains upper then lower correctly.
    """
    result = apply_filters("Hello", ["upper", "lower"])

    if result != "hello":
        raise AssertionError(f"Expected 'hello', got '{result}'")

    return


# =============================================================================
# Property Tests
# =============================================================================

# Filters that accept a string and return a string (no extra args needed).
# These are safe to chain together in any order.
_CHAINABLE_STRING_FILTERS = ["lower", "upper", "title", "trim"]


def _generate_random_string(min_length: int = 1, max_length: int = 30) -> str:
    """
        Generate a random string with letters, digits, and whitespace.
    """
    chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 \t"
    length = random.randint(min_length, max_length)
    return "".join(random.choice(chars) for _ in range(length))


def _generate_random_filter_chain(min_length: int = 1, max_length: int = 5) -> list:
    """
        Generate a random chain of chainable string filters.
    """
    chain_length = random.randint(min_length, max_length)
    return [random.choice(_CHAINABLE_STRING_FILTERS) for _ in range(chain_length)]


def test_property_filter_chaining_left_to_right():
    """
        Property test for filter chaining correctness.

        **Property 6: Filter Chaining Correctness**

        *For any* sequence of filters applied to a value, the filters
        SHALL be applied left-to-right, with each filter receiving the
        output of the previous filter.

        **Validates: Requirements 7.4**

        This property test verifies that:
        1. apply_filters produces the same result as manually applying
           each filter in sequence from left to right
        2. This holds for any random string input and any random
           sequence of chainable filters
        3. The order of filter application matters and is deterministic

        Test strategy:
        - Generate random string inputs
        - Generate random chains of string-to-string filters
        - Compare apply_filters result with manual sequential application
        - Run at least 100 iterations
    """
    iterations = 100

    for iteration in range(iterations):
        # Generate a random input string
        input_value = _generate_random_string()

        # Generate a random filter chain
        filter_chain = _generate_random_filter_chain()

        # Apply filters using the apply_filters helper
        result_via_helper = apply_filters(input_value, filter_chain)

        # Apply filters manually left-to-right
        manual_result = input_value
        for filter_name in filter_chain:
            filter_func = BUILTIN_FILTERS[filter_name]
            manual_result = filter_func(manual_result)

        # Results must be identical
        if result_via_helper != manual_result:
            raise AssertionError(
                f"Iteration {iteration}: Filter chaining mismatch.\n"
                f"Input: {repr(input_value)}\n"
                f"Filter chain: {filter_chain}\n"
                f"apply_filters result: {repr(result_via_helper)}\n"
                f"Manual result: {repr(manual_result)}"
            )

    return


def test_property_filter_chaining_order_matters():
    """
        Property test verifying that filter order affects the result.

        **Property 6: Filter Chaining Correctness**

        *For any* two different filter orderings applied to the same value,
        the results SHALL reflect the specific left-to-right application
        order of each chain.

        **Validates: Requirements 7.4**

        This property test verifies that:
        1. Reversing a filter chain can produce different results
        2. Each filter receives the output of the previous filter
        3. The chaining is not commutative in general

        Test strategy:
        - Generate random strings with mixed case and whitespace
        - Apply [lower, upper] and [upper, lower] chains
        - Verify the results differ as expected
    """
    iterations = 100

    for iteration in range(iterations):
        # Generate a string with mixed case to ensure filters have effect
        input_value = _generate_random_string(min_length=3, max_length=20)

        # Apply lower then upper
        chain_a = ["lower", "upper"]
        result_a = apply_filters(input_value, chain_a)

        # Apply upper then lower
        chain_b = ["upper", "lower"]
        result_b = apply_filters(input_value, chain_b)

        # Verify each result matches manual application
        expected_a = filter_upper(filter_lower(input_value))
        expected_b = filter_lower(filter_upper(input_value))

        if result_a != expected_a:
            raise AssertionError(
                f"Iteration {iteration}: Chain [lower, upper] mismatch.\n"
                f"Input: {repr(input_value)}\n"
                f"apply_filters result: {repr(result_a)}\n"
                f"Expected: {repr(expected_a)}"
            )

        if result_b != expected_b:
            raise AssertionError(
                f"Iteration {iteration}: Chain [upper, lower] mismatch.\n"
                f"Input: {repr(input_value)}\n"
                f"apply_filters result: {repr(result_b)}\n"
                f"Expected: {repr(expected_b)}"
            )

    return


def test_property_filter_chaining_with_escape():
    """
        Property test for filter chaining with escape filter.

        **Property 6: Filter Chaining Correctness**

        *For any* string containing HTML special characters, applying
        escape then lower SHALL produce the same result as escaping
        first and then lowering the escaped output.

        **Validates: Requirements 7.4**

        Test strategy:
        - Generate random strings with HTML special characters
        - Apply [escape, lower] chain via apply_filters
        - Compare with manual sequential application
    """
    html_chars = "<>&\"'"
    iterations = 100

    for iteration in range(iterations):
        # Generate a string that includes some HTML special characters
        base = _generate_random_string(min_length=2, max_length=15)
        num_special = random.randint(1, 3)
        chars_to_insert = [random.choice(html_chars) for _ in range(num_special)]

        # Insert special chars at random positions
        value_list = list(base)
        for ch in chars_to_insert:
            pos = random.randint(0, len(value_list))
            value_list.insert(pos, ch)
        input_value = "".join(value_list)

        # Apply via apply_filters
        result = apply_filters(input_value, ["escape", "lower"])

        # Apply manually
        expected = filter_lower(filter_escape(input_value))

        if result != expected:
            raise AssertionError(
                f"Iteration {iteration}: Escape+lower chain mismatch.\n"
                f"Input: {repr(input_value)}\n"
                f"apply_filters result: {repr(result)}\n"
                f"Expected: {repr(expected)}"
            )

    return
