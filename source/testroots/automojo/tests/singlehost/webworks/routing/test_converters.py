"""
    Tests for the path parameter converters.
    
    This module contains unit tests for the Converter protocol and
    built-in converters (StringConverter, IntConverter, FloatConverter,
    UUIDConverter, PathConverter) as well as the converter registry.
"""

import re
from uuid import UUID

from automojo.webworks.routing.converters import (
    StringConverter,
    IntConverter,
    FloatConverter,
    UUIDConverter,
    PathConverter,
    CONVERTERS,
    register_converter,
    get_converter,
)


# =============================================================================
# Unit Tests for StringConverter
# =============================================================================

def test_string_converter_regex_matches_non_empty_string():
    """
        Test that StringConverter regex matches non-empty strings.
    """
    converter = StringConverter()
    
    pattern = re.compile(f"^{converter.regex}$")
    
    if not pattern.match("hello"):
        errmsg = "Expected regex to match 'hello'"
        raise AssertionError(errmsg)
    
    if not pattern.match("user123"):
        errmsg = "Expected regex to match 'user123'"
        raise AssertionError(errmsg)
    
    if not pattern.match("a"):
        errmsg = "Expected regex to match single character 'a'"
        raise AssertionError(errmsg)
    
    return


def test_string_converter_regex_does_not_match_slash():
    """
        Test that StringConverter regex does not match strings with slashes.
    """
    converter = StringConverter()
    
    pattern = re.compile(f"^{converter.regex}$")
    
    if pattern.match("hello/world"):
        errmsg = "Expected regex to not match 'hello/world'"
        raise AssertionError(errmsg)
    
    if pattern.match("/"):
        errmsg = "Expected regex to not match '/'"
        raise AssertionError(errmsg)
    
    return


def test_string_converter_convert_returns_string():
    """
        Test that StringConverter.convert returns the input string.
    """
    converter = StringConverter()
    
    result = converter.convert("hello")
    
    if result != "hello":
        errmsg = f"Expected 'hello', got '{result}'"
        raise AssertionError(errmsg)
    
    if not isinstance(result, str):
        errmsg = f"Expected str type, got {type(result)}"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for IntConverter
# =============================================================================

def test_int_converter_regex_matches_positive_integers():
    """
        Test that IntConverter regex matches positive integers.
    """
    converter = IntConverter()
    
    pattern = re.compile(f"^{converter.regex}$")
    
    if not pattern.match("123"):
        errmsg = "Expected regex to match '123'"
        raise AssertionError(errmsg)
    
    if not pattern.match("0"):
        errmsg = "Expected regex to match '0'"
        raise AssertionError(errmsg)
    
    if not pattern.match("999999"):
        errmsg = "Expected regex to match '999999'"
        raise AssertionError(errmsg)
    
    return


def test_int_converter_regex_matches_negative_integers():
    """
        Test that IntConverter regex matches negative integers.
    """
    converter = IntConverter()
    
    pattern = re.compile(f"^{converter.regex}$")
    
    if not pattern.match("-123"):
        errmsg = "Expected regex to match '-123'"
        raise AssertionError(errmsg)
    
    if not pattern.match("-1"):
        errmsg = "Expected regex to match '-1'"
        raise AssertionError(errmsg)
    
    return


def test_int_converter_regex_does_not_match_floats():
    """
        Test that IntConverter regex does not match floats.
    """
    converter = IntConverter()
    
    pattern = re.compile(f"^{converter.regex}$")
    
    if pattern.match("12.34"):
        errmsg = "Expected regex to not match '12.34'"
        raise AssertionError(errmsg)
    
    return


def test_int_converter_regex_does_not_match_non_numeric():
    """
        Test that IntConverter regex does not match non-numeric strings.
    """
    converter = IntConverter()
    
    pattern = re.compile(f"^{converter.regex}$")
    
    if pattern.match("abc"):
        errmsg = "Expected regex to not match 'abc'"
        raise AssertionError(errmsg)
    
    if pattern.match("12abc"):
        errmsg = "Expected regex to not match '12abc'"
        raise AssertionError(errmsg)
    
    return


def test_int_converter_convert_returns_int():
    """
        Test that IntConverter.convert returns an integer.
    """
    converter = IntConverter()
    
    result = converter.convert("123")
    
    if result != 123:
        errmsg = f"Expected 123, got {result}"
        raise AssertionError(errmsg)
    
    if not isinstance(result, int):
        errmsg = f"Expected int type, got {type(result)}"
        raise AssertionError(errmsg)
    
    return


def test_int_converter_convert_handles_negative():
    """
        Test that IntConverter.convert handles negative integers.
    """
    converter = IntConverter()
    
    result = converter.convert("-456")
    
    if result != -456:
        errmsg = f"Expected -456, got {result}"
        raise AssertionError(errmsg)
    
    return


def test_int_converter_convert_raises_on_invalid():
    """
        Test that IntConverter.convert raises ValueError on invalid input.
    """
    converter = IntConverter()
    
    try:
        converter.convert("not_a_number")
        errmsg = "Expected ValueError for invalid input"
        raise AssertionError(errmsg)
    except ValueError:
        pass
    
    return



# =============================================================================
# Unit Tests for FloatConverter
# =============================================================================

def test_float_converter_regex_matches_integers():
    """
        Test that FloatConverter regex matches integers.
    """
    converter = FloatConverter()
    
    pattern = re.compile(f"^{converter.regex}$")
    
    if not pattern.match("123"):
        errmsg = "Expected regex to match '123'"
        raise AssertionError(errmsg)
    
    if not pattern.match("0"):
        errmsg = "Expected regex to match '0'"
        raise AssertionError(errmsg)
    
    return


def test_float_converter_regex_matches_decimals():
    """
        Test that FloatConverter regex matches decimal numbers.
    """
    converter = FloatConverter()
    
    pattern = re.compile(f"^{converter.regex}$")
    
    if not pattern.match("12.34"):
        errmsg = "Expected regex to match '12.34'"
        raise AssertionError(errmsg)
    
    if not pattern.match("0.5"):
        errmsg = "Expected regex to match '0.5'"
        raise AssertionError(errmsg)
    
    if not pattern.match("100."):
        errmsg = "Expected regex to match '100.'"
        raise AssertionError(errmsg)
    
    return


def test_float_converter_regex_matches_negative():
    """
        Test that FloatConverter regex matches negative numbers.
    """
    converter = FloatConverter()
    
    pattern = re.compile(f"^{converter.regex}$")
    
    if not pattern.match("-12.34"):
        errmsg = "Expected regex to match '-12.34'"
        raise AssertionError(errmsg)
    
    if not pattern.match("-5"):
        errmsg = "Expected regex to match '-5'"
        raise AssertionError(errmsg)
    
    return


def test_float_converter_regex_does_not_match_non_numeric():
    """
        Test that FloatConverter regex does not match non-numeric strings.
    """
    converter = FloatConverter()
    
    pattern = re.compile(f"^{converter.regex}$")
    
    if pattern.match("abc"):
        errmsg = "Expected regex to not match 'abc'"
        raise AssertionError(errmsg)
    
    return


def test_float_converter_convert_returns_float():
    """
        Test that FloatConverter.convert returns a float.
    """
    converter = FloatConverter()
    
    result = converter.convert("12.34")
    
    if abs(result - 12.34) > 0.0001:
        errmsg = f"Expected 12.34, got {result}"
        raise AssertionError(errmsg)
    
    if not isinstance(result, float):
        errmsg = f"Expected float type, got {type(result)}"
        raise AssertionError(errmsg)
    
    return


def test_float_converter_convert_handles_integer_string():
    """
        Test that FloatConverter.convert handles integer strings.
    """
    converter = FloatConverter()
    
    result = converter.convert("123")
    
    if abs(result - 123.0) > 0.0001:
        errmsg = f"Expected 123.0, got {result}"
        raise AssertionError(errmsg)
    
    return


def test_float_converter_convert_handles_negative():
    """
        Test that FloatConverter.convert handles negative numbers.
    """
    converter = FloatConverter()
    
    result = converter.convert("-45.67")
    
    if abs(result - (-45.67)) > 0.0001:
        errmsg = f"Expected -45.67, got {result}"
        raise AssertionError(errmsg)
    
    return


def test_float_converter_convert_raises_on_invalid():
    """
        Test that FloatConverter.convert raises ValueError on invalid input.
    """
    converter = FloatConverter()
    
    try:
        converter.convert("not_a_number")
        errmsg = "Expected ValueError for invalid input"
        raise AssertionError(errmsg)
    except ValueError:
        pass
    
    return


# =============================================================================
# Unit Tests for UUIDConverter
# =============================================================================

def test_uuid_converter_regex_matches_valid_uuid():
    """
        Test that UUIDConverter regex matches valid UUIDs.
    """
    converter = UUIDConverter()
    
    pattern = re.compile(f"^{converter.regex}$")
    
    valid_uuid = "550e8400-e29b-41d4-a716-446655440000"
    if not pattern.match(valid_uuid):
        errmsg = f"Expected regex to match '{valid_uuid}'"
        raise AssertionError(errmsg)
    
    return


def test_uuid_converter_regex_matches_uppercase_uuid():
    """
        Test that UUIDConverter regex matches uppercase UUIDs.
    """
    converter = UUIDConverter()
    
    pattern = re.compile(f"^{converter.regex}$")
    
    upper_uuid = "550E8400-E29B-41D4-A716-446655440000"
    if not pattern.match(upper_uuid):
        errmsg = f"Expected regex to match uppercase UUID '{upper_uuid}'"
        raise AssertionError(errmsg)
    
    return


def test_uuid_converter_regex_does_not_match_invalid_uuid():
    """
        Test that UUIDConverter regex does not match invalid UUIDs.
    """
    converter = UUIDConverter()
    
    pattern = re.compile(f"^{converter.regex}$")
    
    # Too short
    if pattern.match("550e8400-e29b-41d4-a716"):
        errmsg = "Expected regex to not match truncated UUID"
        raise AssertionError(errmsg)
    
    # No hyphens
    if pattern.match("550e8400e29b41d4a716446655440000"):
        errmsg = "Expected regex to not match UUID without hyphens"
        raise AssertionError(errmsg)
    
    # Invalid characters
    if pattern.match("550e8400-e29b-41d4-a716-44665544000g"):
        errmsg = "Expected regex to not match UUID with invalid character"
        raise AssertionError(errmsg)
    
    return


def test_uuid_converter_convert_returns_uuid():
    """
        Test that UUIDConverter.convert returns a UUID object.
    """
    converter = UUIDConverter()
    
    uuid_str = "550e8400-e29b-41d4-a716-446655440000"
    result = converter.convert(uuid_str)
    
    if not isinstance(result, UUID):
        errmsg = f"Expected UUID type, got {type(result)}"
        raise AssertionError(errmsg)
    
    if str(result) != uuid_str:
        errmsg = f"Expected '{uuid_str}', got '{result}'"
        raise AssertionError(errmsg)
    
    return


def test_uuid_converter_convert_raises_on_invalid():
    """
        Test that UUIDConverter.convert raises ValueError on invalid input.
    """
    converter = UUIDConverter()
    
    try:
        converter.convert("not-a-uuid")
        errmsg = "Expected ValueError for invalid UUID"
        raise AssertionError(errmsg)
    except ValueError:
        pass
    
    return


# =============================================================================
# Unit Tests for PathConverter
# =============================================================================

def test_path_converter_regex_matches_simple_path():
    """
        Test that PathConverter regex matches simple paths.
    """
    converter = PathConverter()
    
    pattern = re.compile(f"^{converter.regex}$")
    
    if not pattern.match("docs"):
        errmsg = "Expected regex to match 'docs'"
        raise AssertionError(errmsg)
    
    return


def test_path_converter_regex_matches_path_with_slashes():
    """
        Test that PathConverter regex matches paths with slashes.
    """
    converter = PathConverter()
    
    pattern = re.compile(f"^{converter.regex}$")
    
    if not pattern.match("docs/readme.txt"):
        errmsg = "Expected regex to match 'docs/readme.txt'"
        raise AssertionError(errmsg)
    
    if not pattern.match("a/b/c/d/e"):
        errmsg = "Expected regex to match 'a/b/c/d/e'"
        raise AssertionError(errmsg)
    
    return


def test_path_converter_regex_does_not_match_empty():
    """
        Test that PathConverter regex does not match empty string.
    """
    converter = PathConverter()
    
    pattern = re.compile(f"^{converter.regex}$")
    
    if pattern.match(""):
        errmsg = "Expected regex to not match empty string"
        raise AssertionError(errmsg)
    
    return


def test_path_converter_convert_returns_string():
    """
        Test that PathConverter.convert returns the input string.
    """
    converter = PathConverter()
    
    result = converter.convert("docs/readme.txt")
    
    if result != "docs/readme.txt":
        errmsg = f"Expected 'docs/readme.txt', got '{result}'"
        raise AssertionError(errmsg)
    
    if not isinstance(result, str):
        errmsg = f"Expected str type, got {type(result)}"
        raise AssertionError(errmsg)
    
    return



# =============================================================================
# Unit Tests for Converter Registry
# =============================================================================

def test_converters_dict_contains_builtin_converters():
    """
        Test that CONVERTERS dict contains all built-in converters.
    """
    expected_names = {"str", "int", "float", "uuid", "path"}
    
    actual_names = set(CONVERTERS.keys())
    
    if not expected_names.issubset(actual_names):
        missing = expected_names - actual_names
        errmsg = f"Missing built-in converters: {missing}"
        raise AssertionError(errmsg)
    
    return


def test_converters_dict_str_is_string_converter():
    """
        Test that CONVERTERS['str'] is a StringConverter.
    """
    converter = CONVERTERS["str"]
    
    if not isinstance(converter, StringConverter):
        errmsg = f"Expected StringConverter, got {type(converter)}"
        raise AssertionError(errmsg)
    
    return


def test_converters_dict_int_is_int_converter():
    """
        Test that CONVERTERS['int'] is an IntConverter.
    """
    converter = CONVERTERS["int"]
    
    if not isinstance(converter, IntConverter):
        errmsg = f"Expected IntConverter, got {type(converter)}"
        raise AssertionError(errmsg)
    
    return


def test_converters_dict_float_is_float_converter():
    """
        Test that CONVERTERS['float'] is a FloatConverter.
    """
    converter = CONVERTERS["float"]
    
    if not isinstance(converter, FloatConverter):
        errmsg = f"Expected FloatConverter, got {type(converter)}"
        raise AssertionError(errmsg)
    
    return


def test_converters_dict_uuid_is_uuid_converter():
    """
        Test that CONVERTERS['uuid'] is a UUIDConverter.
    """
    converter = CONVERTERS["uuid"]
    
    if not isinstance(converter, UUIDConverter):
        errmsg = f"Expected UUIDConverter, got {type(converter)}"
        raise AssertionError(errmsg)
    
    return


def test_converters_dict_path_is_path_converter():
    """
        Test that CONVERTERS['path'] is a PathConverter.
    """
    converter = CONVERTERS["path"]
    
    if not isinstance(converter, PathConverter):
        errmsg = f"Expected PathConverter, got {type(converter)}"
        raise AssertionError(errmsg)
    
    return


def test_register_converter_adds_custom_converter():
    """
        Test that register_converter adds a custom converter.
    """
    # Create a custom converter
    class SlugConverter:
        regex = r"[a-z0-9]+(?:-[a-z0-9]+)*"
        
        def convert(self, value: str) -> str:
            return value
    
    custom = SlugConverter()
    register_converter("slug", custom)
    
    if "slug" not in CONVERTERS:
        errmsg = "Expected 'slug' to be in CONVERTERS"
        raise AssertionError(errmsg)
    
    if CONVERTERS["slug"] is not custom:
        errmsg = "Expected registered converter to be the same instance"
        raise AssertionError(errmsg)
    
    # Clean up
    del CONVERTERS["slug"]
    
    return


def test_register_converter_overwrites_existing():
    """
        Test that register_converter can overwrite existing converters.
    """
    # Save original
    original = CONVERTERS["str"]
    
    # Create a replacement
    class CustomStringConverter:
        regex = r"[a-z]+"
        
        def convert(self, value: str) -> str:
            return value.lower()
    
    custom = CustomStringConverter()
    register_converter("str", custom)
    
    if CONVERTERS["str"] is not custom:
        errmsg = "Expected 'str' converter to be replaced"
        raise AssertionError(errmsg)
    
    # Restore original
    CONVERTERS["str"] = original
    
    return


def test_get_converter_returns_registered_converter():
    """
        Test that get_converter returns the registered converter.
    """
    result = get_converter("int")
    
    if not isinstance(result, IntConverter):
        errmsg = f"Expected IntConverter, got {type(result)}"
        raise AssertionError(errmsg)
    
    return


def test_get_converter_raises_keyerror_for_unknown():
    """
        Test that get_converter raises KeyError for unknown converter.
    """
    try:
        get_converter("unknown_converter")
        errmsg = "Expected KeyError for unknown converter"
        raise AssertionError(errmsg)
    except KeyError:
        pass
    
    return

import random
import re
import string
from uuid import UUID as UUIDType

from automojo.webworks.routing.matcher import Matcher


# =============================================================================
# Property 13: Path Parameter Conversion
# **Validates: Requirements 10.2, 10.3, 10.4, 10.5, 10.6, 10.7**
#
# *For any* typed path parameter with converter C, if the path segment matches
# C's regex and C.convert() succeeds, the converted value SHALL be of the
# correct type. If the segment doesn't match or conversion fails, the route
# SHALL be treated as non-matching.
# =============================================================================


def _random_safe_string(min_len=1, max_len=20):
    """Generate a random URL-safe string without slashes."""
    length = random.randint(min_len, max_len)
    chars = string.ascii_letters + string.digits + "-_."
    return "".join(random.choice(chars) for _ in range(length))


def _random_uuid_string():
    """Generate a random valid UUID string."""
    hex_chars = "0123456789abcdef"
    parts = [
        "".join(random.choice(hex_chars) for _ in range(8)),
        "".join(random.choice(hex_chars) for _ in range(4)),
        "".join(random.choice(hex_chars) for _ in range(4)),
        "".join(random.choice(hex_chars) for _ in range(4)),
        "".join(random.choice(hex_chars) for _ in range(12)),
    ]
    return "-".join(parts)


def test_property_str_converter_type_and_identity():
    """
    Property 13: Path Parameter Conversion - str converter

    For any non-empty string segment without slashes, the str converter
    SHALL match and return a str equal to the original segment.

    **Feature: router-request-handling, Property 13: Path Parameter Conversion**
    **Validates: Requirements 10.2, 10.7**
    """
    converter = StringConverter()
    pattern = re.compile(f"^({converter.regex})$")

    for _ in range(100):
        value = _random_safe_string()

        # Property: regex matches non-empty strings without slashes
        match = pattern.match(value)
        if match is None:
            errmsg = f"StringConverter regex failed to match '{value}'"
            raise AssertionError(errmsg)

        # Property: convert returns str identical to input
        result = converter.convert(value)
        if not isinstance(result, str):
            errmsg = f"Expected str, got {type(result)} for '{value}'"
            raise AssertionError(errmsg)

        if result != value:
            errmsg = f"Expected '{value}', got '{result}'"
            raise AssertionError(errmsg)

    return


def test_property_int_converter_type_and_round_trip():
    """
    Property 13: Path Parameter Conversion - int converter

    For any integer value, converting its string representation SHALL
    produce a Python int equal to the original value.

    **Feature: router-request-handling, Property 13: Path Parameter Conversion**
    **Validates: Requirements 10.3, 10.7**
    """
    converter = IntConverter()
    pattern = re.compile(f"^({converter.regex})$")

    for _ in range(100):
        original_int = random.randint(-999999, 999999)
        value = str(original_int)

        # Property: regex matches integer strings
        match = pattern.match(value)
        if match is None:
            errmsg = f"IntConverter regex failed to match '{value}'"
            raise AssertionError(errmsg)

        # Property: convert returns int of correct value
        result = converter.convert(value)
        if not isinstance(result, int):
            errmsg = f"Expected int, got {type(result)} for '{value}'"
            raise AssertionError(errmsg)

        if result != original_int:
            errmsg = f"Expected {original_int}, got {result}"
            raise AssertionError(errmsg)

    return


def test_property_float_converter_type_and_round_trip():
    """
    Property 13: Path Parameter Conversion - float converter

    For any numeric value matching the float regex, converting SHALL
    produce a Python float of the correct value.

    **Feature: router-request-handling, Property 13: Path Parameter Conversion**
    **Validates: Requirements 10.4, 10.7**
    """
    converter = FloatConverter()
    pattern = re.compile(f"^({converter.regex})$")

    for _ in range(100):
        # Generate floats that match the converter regex pattern
        integer_part = random.randint(-9999, 9999)
        if random.random() < 0.5:
            # Integer-like float
            value = str(integer_part)
        else:
            # Decimal float
            decimal_digits = random.randint(1, 6)
            decimal_part = "".join(str(random.randint(0, 9)) for _ in range(decimal_digits))
            value = f"{integer_part}.{decimal_part}"

        match = pattern.match(value)
        if match is None:
            # Skip values that don't match the regex (e.g., negative decimals
            # depending on regex specifics)
            continue

        # Property: convert returns float
        result = converter.convert(value)
        if not isinstance(result, float):
            errmsg = f"Expected float, got {type(result)} for '{value}'"
            raise AssertionError(errmsg)

        # Property: converted value equals float(value)
        expected = float(value)
        if result != expected:
            errmsg = f"Expected {expected}, got {result} for '{value}'"
            raise AssertionError(errmsg)

    return


def test_property_uuid_converter_type_and_round_trip():
    """
    Property 13: Path Parameter Conversion - uuid converter

    For any valid UUID string, converting SHALL produce a Python UUID
    whose string representation matches the original (lowercased).

    **Feature: router-request-handling, Property 13: Path Parameter Conversion**
    **Validates: Requirements 10.5, 10.7**
    """
    converter = UUIDConverter()
    pattern = re.compile(f"^({converter.regex})$", re.IGNORECASE)

    for _ in range(100):
        uuid_str = _random_uuid_string()

        # Property: regex matches valid UUID strings
        match = pattern.match(uuid_str)
        if match is None:
            errmsg = f"UUIDConverter regex failed to match '{uuid_str}'"
            raise AssertionError(errmsg)

        # Property: convert returns UUID
        result = converter.convert(uuid_str)
        if not isinstance(result, UUIDType):
            errmsg = f"Expected UUID, got {type(result)} for '{uuid_str}'"
            raise AssertionError(errmsg)

        # Property: round-trip - str(UUID) matches original (lowercased)
        if str(result) != uuid_str.lower():
            errmsg = f"Expected '{uuid_str.lower()}', got '{str(result)}'"
            raise AssertionError(errmsg)

    return


def test_property_path_converter_preserves_slashes():
    """
    Property 13: Path Parameter Conversion - path converter

    For any non-empty path string (including slashes), the path converter
    SHALL match and return the string unchanged.

    **Feature: router-request-handling, Property 13: Path Parameter Conversion**
    **Validates: Requirements 10.6, 10.7**
    """
    converter = PathConverter()
    pattern = re.compile(f"^({converter.regex})$")

    for _ in range(100):
        # Generate paths with 1-5 segments
        num_segments = random.randint(1, 5)
        segments = [_random_safe_string() for _ in range(num_segments)]
        value = "/".join(segments)

        # Property: regex matches paths with slashes
        match = pattern.match(value)
        if match is None:
            errmsg = f"PathConverter regex failed to match '{value}'"
            raise AssertionError(errmsg)

        # Property: convert returns str identical to input
        result = converter.convert(value)
        if not isinstance(result, str):
            errmsg = f"Expected str, got {type(result)} for '{value}'"
            raise AssertionError(errmsg)

        if result != value:
            errmsg = f"Expected '{value}', got '{result}'"
            raise AssertionError(errmsg)

    return


def test_property_conversion_failure_means_no_match():
    """
    Property 13: Path Parameter Conversion - Conversion Failure

    For any typed path parameter, when the path segment does not match
    the converter's regex or conversion fails, the Matcher SHALL treat
    the route as non-matching (return None).

    **Feature: router-request-handling, Property 13: Path Parameter Conversion**
    **Validates: Requirements 10.7**
    """
    # int converter: non-numeric strings should not match
    int_matcher = Matcher("/items/{id:int}")
    non_int_values = [
        "abc", "hello", "12.5", "3.14", "twelve",
        "1a2b", "!@#", "true", "null", "",
    ]
    for value in non_int_values:
        path = f"/items/{value}"
        result = int_matcher.match(path)
        if result is not None:
            errmsg = f"Int matcher should not match '{path}', got {result}"
            raise AssertionError(errmsg)

    # float converter: non-numeric strings should not match
    float_matcher = Matcher("/price/{amount:float}")
    non_float_values = [
        "abc", "hello", "1.2.3", "!@#", "true", "",
    ]
    for value in non_float_values:
        path = f"/price/{value}"
        result = float_matcher.match(path)
        if result is not None:
            errmsg = f"Float matcher should not match '{path}', got {result}"
            raise AssertionError(errmsg)

    # uuid converter: non-UUID strings should not match
    uuid_matcher = Matcher("/users/{uid:uuid}")
    non_uuid_values = [
        "abc", "12345", "not-a-uuid", "123e4567-e89b-12d3",
        "123e4567-e89b-12d3-a456", "",
    ]
    for value in non_uuid_values:
        path = f"/users/{value}"
        result = uuid_matcher.match(path)
        if result is not None:
            errmsg = f"UUID matcher should not match '{path}', got {result}"
            raise AssertionError(errmsg)

    return


def test_property_matcher_integration_correct_types():
    """
    Property 13: Path Parameter Conversion - Matcher Integration

    For any path with typed parameters, the Matcher SHALL extract and
    convert parameters to the correct Python types.

    **Feature: router-request-handling, Property 13: Path Parameter Conversion**
    **Validates: Requirements 10.2, 10.3, 10.4, 10.5, 10.6, 10.7**
    """
    for _ in range(50):
        # Test int parameter extraction via Matcher
        int_val = random.randint(0, 99999)
        int_matcher = Matcher("/items/{id:int}")
        result = int_matcher.match(f"/items/{int_val}")
        if result is None:
            errmsg = f"Matcher failed to match /items/{int_val}"
            raise AssertionError(errmsg)
        if not isinstance(result["id"], int):
            errmsg = f"Expected int, got {type(result['id'])}"
            raise AssertionError(errmsg)
        if result["id"] != int_val:
            errmsg = f"Expected {int_val}, got {result['id']}"
            raise AssertionError(errmsg)

        # Test str parameter extraction via Matcher
        str_val = _random_safe_string()
        str_matcher = Matcher("/users/{name}")
        result = str_matcher.match(f"/users/{str_val}")
        if result is None:
            errmsg = f"Matcher failed to match /users/{str_val}"
            raise AssertionError(errmsg)
        if not isinstance(result["name"], str):
            errmsg = f"Expected str, got {type(result['name'])}"
            raise AssertionError(errmsg)
        if result["name"] != str_val:
            errmsg = f"Expected '{str_val}', got '{result['name']}'"
            raise AssertionError(errmsg)

        # Test uuid parameter extraction via Matcher
        uuid_str = _random_uuid_string()
        uuid_matcher = Matcher("/records/{uid:uuid}")
        result = uuid_matcher.match(f"/records/{uuid_str}")
        if result is None:
            errmsg = f"Matcher failed to match /records/{uuid_str}"
            raise AssertionError(errmsg)
        if not isinstance(result["uid"], UUIDType):
            errmsg = f"Expected UUID, got {type(result['uid'])}"
            raise AssertionError(errmsg)

    # Test path parameter extraction via Matcher
    for _ in range(50):
        num_segments = random.randint(1, 4)
        segments = [_random_safe_string() for _ in range(num_segments)]
        path_val = "/".join(segments)
        path_matcher = Matcher("/files/{filepath:path}")
        result = path_matcher.match(f"/files/{path_val}")
        if result is None:
            errmsg = f"Matcher failed to match /files/{path_val}"
            raise AssertionError(errmsg)
        if not isinstance(result["filepath"], str):
            errmsg = f"Expected str, got {type(result['filepath'])}"
            raise AssertionError(errmsg)
        if result["filepath"] != path_val:
            errmsg = f"Expected '{path_val}', got '{result['filepath']}'"
            raise AssertionError(errmsg)

    return
