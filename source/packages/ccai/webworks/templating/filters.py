"""
    Built-in template filters.

    This module provides a collection of built-in filter functions for
    template rendering. Filters transform template variable values during
    rendering and can be chained together in templates.

    The filters are organized into three categories:

    - String manipulation: lower, upper, title, trim, format
    - Collection operations: length, join, first, last, sort, reverse
    - Utility filters: safe, escape, default, date, json

    Each filter function follows a consistent pattern where the first
    argument is the value to transform, and additional arguments provide
    configuration options.

    Example usage in templates::

        {{ name | lower }}
        {{ items | join(", ") }}
        {{ value | default("N/A") }}
        {{ data | json }}
"""

import json
from datetime import date, datetime
from typing import Any, List

from ccai.webworks.templating.escaping import SafeString, escape


# =============================================================================
# String Manipulation Filters
# =============================================================================

def filter_lower(value: Any) -> str:
    """
        Convert a value to lowercase.

        The value is first converted to a string using str() before
        applying the lowercase transformation.

        :param value: The value to convert to lowercase.

        :returns: The lowercase string representation of the value.
    """
    return str(value).lower()


def filter_upper(value: Any) -> str:
    """
        Convert a value to uppercase.

        The value is first converted to a string using str() before
        applying the uppercase transformation.

        :param value: The value to convert to uppercase.

        :returns: The uppercase string representation of the value.
    """
    return str(value).upper()


def filter_title(value: Any) -> str:
    """
        Convert a value to title case.

        The value is first converted to a string using str() before
        applying the title case transformation. Title case capitalizes
        the first letter of each word.

        :param value: The value to convert to title case.

        :returns: The title case string representation of the value.
    """
    return str(value).title()


def filter_trim(value: Any) -> str:
    """
        Strip leading and trailing whitespace from a value.

        The value is first converted to a string using str() before
        stripping whitespace.

        :param value: The value to trim.

        :returns: The trimmed string representation of the value.
    """
    return str(value).strip()


def filter_format(value: str, *args: Any, **kwargs: Any) -> str:
    """
        Format a string using Python's str.format() method.

        The value is used as the format string, with positional and
        keyword arguments passed through to str.format().

        :param value: The format string.
        :param args: Positional arguments for formatting.
        :param kwargs: Keyword arguments for formatting.

        :returns: The formatted string.

        Example::

            filter_format("Hello, {}!", "World")
            # Returns: "Hello, World!"

            filter_format("{name} is {age}", name="Alice", age=30)
            # Returns: "Alice is 30"
    """
    return str(value).format(*args, **kwargs)


# =============================================================================
# Collection Filters
# =============================================================================

def filter_length(value: Any) -> int:
    """
        Return the length of a value.

        Works with any value that supports len(), including strings,
        lists, tuples, dictionaries, and sets.

        :param value: The value to measure.

        :returns: The length of the value.
    """
    return len(value)


def filter_join(value: List, separator: str = "") -> str:
    """
        Join list elements into a string.

        Each element is converted to a string using str() before
        joining with the specified separator.

        :param value: The list of values to join.
        :param separator: The separator string (default: empty string).

        :returns: The joined string.
    """
    return separator.join(str(v) for v in value)


def filter_first(value: List) -> Any:
    """
        Return the first element of a sequence.

        Returns None if the sequence is empty.

        :param value: The sequence to get the first element from.

        :returns: The first element, or None if empty.
    """
    return value[0] if value else None


def filter_last(value: List) -> Any:
    """
        Return the last element of a sequence.

        Returns None if the sequence is empty.

        :param value: The sequence to get the last element from.

        :returns: The last element, or None if empty.
    """
    return value[-1] if value else None


def filter_sort(value: List, reverse: bool = False) -> list:
    """
        Sort a list.

        Returns a new sorted list without modifying the original.

        :param value: The list to sort.
        :param reverse: If True, sort in descending order (default: False).

        :returns: A new sorted list.
    """
    return sorted(value, reverse=reverse)


def filter_reverse(value: List) -> list:
    """
        Reverse a list.

        Returns a new reversed list without modifying the original.

        :param value: The list to reverse.

        :returns: A new reversed list.
    """
    return list(reversed(value))


# =============================================================================
# Utility Filters
# =============================================================================

def filter_safe(value: Any) -> SafeString:
    """
        Mark a value as safe, bypassing auto-escaping.

        The value is converted to a string and wrapped in a SafeString
        instance. This indicates to the template engine that the content
        should not be auto-escaped during rendering.

        .. warning::

            Only use this filter with content that you trust completely.
            Marking untrusted user input as safe can lead to XSS
            vulnerabilities.

        :param value: The value to mark as safe.

        :returns: A SafeString instance.
    """
    return SafeString(str(value))


def filter_escape(value: Any) -> str:
    """
        Escape HTML special characters in a value.

        The value is converted to a string and HTML special characters
        are replaced with their entity equivalents to prevent XSS attacks.

        :param value: The value to escape.

        :returns: The escaped string.
    """
    return escape(str(value))


def filter_default(value: Any, default: Any = "") -> Any:
    """
        Return a default value if the input value is falsy.

        A value is considered falsy if it evaluates to False in a
        boolean context (None, empty string, 0, empty list, etc.).

        :param value: The value to check.
        :param default: The default value to return if value is falsy.

        :returns: The original value if truthy, otherwise the default.
    """
    return value if value else default


def filter_date(value: Any, format_str: str = "%Y-%m-%d") -> str:
    """
        Format a date or datetime value as a string.

        Supports datetime objects, date objects, and string values.
        String values are returned as-is since they are already
        string representations.

        :param value: The date or datetime value to format.
        :param format_str: The strftime format string (default: "%Y-%m-%d").

        :returns: The formatted date string.
    """
    if isinstance(value, (datetime, date)):
        return value.strftime(format_str)

    return str(value)


def filter_json(value: Any) -> str:
    """
        Convert a value to a JSON string.

        Serializes the value using Python's json module with
        ensure_ascii=False to preserve Unicode characters.

        :param value: The value to serialize to JSON.

        :returns: The JSON string representation.
    """
    return json.dumps(value, ensure_ascii=False)


# =============================================================================
# Built-in Filters Registry
# =============================================================================

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


def apply_filters(value: Any, filter_names: List[str]) -> Any:
    """
        Apply a sequence of filters to a value left-to-right.

        Each filter receives the output of the previous filter as its
        input. This function is used to implement filter chaining in
        templates.

        :param value: The initial value to transform.
        :param filter_names: List of filter names to apply in order.

        :returns: The value after all filters have been applied.

        :raises KeyError: If a filter name is not found in BUILTIN_FILTERS.
    """
    result = value
    for filter_name in filter_names:
        filter_func = BUILTIN_FILTERS[filter_name]
        result = filter_func(result)

    return result
