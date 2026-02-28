"""
    Tests for the Headers class.
    
    This module contains unit tests for case-insensitive header access.
"""

from automojo.webworks.routing.headers import Headers


# =============================================================================
# Unit Tests for Headers - Basic Access
# =============================================================================

def test_headers_getitem_returns_value():
    """
        Test that __getitem__ returns header value.
    """
    headers = Headers({"Content-Type": "application/json"})
    
    result = headers["Content-Type"]
    
    expected = "application/json"
    if result != expected:
        errmsg = f"Expected '{expected}', got '{result}'"
        raise AssertionError(errmsg)
    
    return


def test_headers_getitem_raises_keyerror_for_missing():
    """
        Test that __getitem__ raises KeyError for missing header.
    """
    headers = Headers({"Content-Type": "application/json"})
    
    try:
        _ = headers["Missing-Header"]
        errmsg = "Expected KeyError for missing header"
        raise AssertionError(errmsg)
    except KeyError:
        pass
    
    return


def test_headers_get_returns_value():
    """
        Test that get() returns header value.
    """
    headers = Headers({"Content-Type": "application/json"})
    
    result = headers.get("Content-Type")
    
    expected = "application/json"
    if result != expected:
        errmsg = f"Expected '{expected}', got '{result}'"
        raise AssertionError(errmsg)
    
    return


def test_headers_get_returns_default_for_missing():
    """
        Test that get() returns default for missing header.
    """
    headers = Headers({"Content-Type": "application/json"})
    
    result = headers.get("Missing-Header", "default")
    
    expected = "default"
    if result != expected:
        errmsg = f"Expected '{expected}', got '{result}'"
        raise AssertionError(errmsg)
    
    return


def test_headers_get_returns_none_when_no_default():
    """
        Test that get() returns None when no default provided.
    """
    headers = Headers({"Content-Type": "application/json"})
    
    result = headers.get("Missing-Header")
    
    if result is not None:
        errmsg = f"Expected None, got '{result}'"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for Headers - Case Insensitivity
# =============================================================================

def test_headers_getitem_is_case_insensitive():
    """
        Test that __getitem__ is case-insensitive.
    """
    headers = Headers({"Content-Type": "application/json"})
    
    # Test various case variations
    result_lower = headers["content-type"]
    result_upper = headers["CONTENT-TYPE"]
    result_mixed = headers["Content-type"]
    
    expected = "application/json"
    
    if result_lower != expected:
        errmsg = f"Expected '{expected}' for lowercase, got '{result_lower}'"
        raise AssertionError(errmsg)
    
    if result_upper != expected:
        errmsg = f"Expected '{expected}' for uppercase, got '{result_upper}'"
        raise AssertionError(errmsg)
    
    if result_mixed != expected:
        errmsg = f"Expected '{expected}' for mixed case, got '{result_mixed}'"
        raise AssertionError(errmsg)
    
    return


def test_headers_get_is_case_insensitive():
    """
        Test that get() is case-insensitive.
    """
    headers = Headers({"X-Custom-Header": "custom-value"})
    
    result_lower = headers.get("x-custom-header")
    result_upper = headers.get("X-CUSTOM-HEADER")
    result_mixed = headers.get("x-Custom-Header")
    
    expected = "custom-value"
    
    if result_lower != expected:
        errmsg = f"Expected '{expected}' for lowercase, got '{result_lower}'"
        raise AssertionError(errmsg)
    
    if result_upper != expected:
        errmsg = f"Expected '{expected}' for uppercase, got '{result_upper}'"
        raise AssertionError(errmsg)
    
    if result_mixed != expected:
        errmsg = f"Expected '{expected}' for mixed case, got '{result_mixed}'"
        raise AssertionError(errmsg)
    
    return


def test_headers_contains_is_case_insensitive():
    """
        Test that __contains__ is case-insensitive.
    """
    headers = Headers({"Content-Type": "application/json"})
    
    if "content-type" not in headers:
        errmsg = "Expected 'content-type' to be in headers"
        raise AssertionError(errmsg)
    
    if "CONTENT-TYPE" not in headers:
        errmsg = "Expected 'CONTENT-TYPE' to be in headers"
        raise AssertionError(errmsg)
    
    if "Content-Type" not in headers:
        errmsg = "Expected 'Content-Type' to be in headers"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for Headers - Modification
# =============================================================================

def test_headers_setitem_adds_header():
    """
        Test that __setitem__ adds a header.
    """
    headers = Headers()
    
    headers["Content-Type"] = "application/json"
    
    result = headers.get("Content-Type")
    expected = "application/json"
    if result != expected:
        errmsg = f"Expected '{expected}', got '{result}'"
        raise AssertionError(errmsg)
    
    return


def test_headers_setitem_overwrites_existing():
    """
        Test that __setitem__ overwrites existing header.
    """
    headers = Headers({"Content-Type": "text/plain"})
    
    headers["Content-Type"] = "application/json"
    
    result = headers.get("Content-Type")
    expected = "application/json"
    if result != expected:
        errmsg = f"Expected '{expected}', got '{result}'"
        raise AssertionError(errmsg)
    
    return


def test_headers_setitem_case_insensitive_overwrite():
    """
        Test that __setitem__ overwrites with different case.
    """
    headers = Headers({"Content-Type": "text/plain"})
    
    headers["content-type"] = "application/json"
    
    result = headers.get("Content-Type")
    expected = "application/json"
    if result != expected:
        errmsg = f"Expected '{expected}', got '{result}'"
        raise AssertionError(errmsg)
    
    return


def test_headers_delitem_removes_header():
    """
        Test that __delitem__ removes a header.
    """
    headers = Headers({"Content-Type": "application/json", "Accept": "*/*"})
    
    del headers["Content-Type"]
    
    if "Content-Type" in headers:
        errmsg = "Expected 'Content-Type' to be removed"
        raise AssertionError(errmsg)
    
    if "Accept" not in headers:
        errmsg = "Expected 'Accept' to still be present"
        raise AssertionError(errmsg)
    
    return


def test_headers_delitem_is_case_insensitive():
    """
        Test that __delitem__ is case-insensitive.
    """
    headers = Headers({"Content-Type": "application/json"})
    
    del headers["content-type"]
    
    if "Content-Type" in headers:
        errmsg = "Expected 'Content-Type' to be removed"
        raise AssertionError(errmsg)
    
    return


def test_headers_delitem_raises_keyerror_for_missing():
    """
        Test that __delitem__ raises KeyError for missing header.
    """
    headers = Headers({"Content-Type": "application/json"})
    
    try:
        del headers["Missing-Header"]
        errmsg = "Expected KeyError for missing header"
        raise AssertionError(errmsg)
    except KeyError:
        pass
    
    return


# =============================================================================
# Unit Tests for Headers - Iteration
# =============================================================================

def test_headers_keys_returns_original_names():
    """
        Test that keys() returns original header names.
    """
    headers = Headers({"Content-Type": "application/json", "X-Custom": "value"})
    
    result = list(headers.keys())
    
    expected_keys = {"Content-Type", "X-Custom"}
    if set(result) != expected_keys:
        errmsg = f"Expected keys {expected_keys}, got {set(result)}"
        raise AssertionError(errmsg)
    
    return


def test_headers_values_returns_all_values():
    """
        Test that values() returns all header values.
    """
    headers = Headers({"Content-Type": "application/json", "Accept": "*/*"})
    
    result = list(headers.values())
    
    expected_values = {"application/json", "*/*"}
    if set(result) != expected_values:
        errmsg = f"Expected values {expected_values}, got {set(result)}"
        raise AssertionError(errmsg)
    
    return


def test_headers_items_returns_name_value_pairs():
    """
        Test that items() returns name-value pairs.
    """
    headers = Headers({"Content-Type": "application/json", "Accept": "*/*"})
    
    result = dict(headers.items())
    
    expected = {"Content-Type": "application/json", "Accept": "*/*"}
    if result != expected:
        errmsg = f"Expected {expected}, got {result}"
        raise AssertionError(errmsg)
    
    return


def test_headers_len_returns_count():
    """
        Test that __len__ returns header count.
    """
    headers = Headers({"Content-Type": "application/json", "Accept": "*/*"})
    
    result = len(headers)
    
    expected = 2
    if result != expected:
        errmsg = f"Expected length {expected}, got {result}"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for Headers - Edge Cases
# =============================================================================

def test_headers_empty_initialization():
    """
        Test that Headers can be initialized empty.
    """
    headers = Headers()
    
    result = len(headers)
    
    expected = 0
    if result != expected:
        errmsg = f"Expected length {expected}, got {result}"
        raise AssertionError(errmsg)
    
    return


def test_headers_none_initialization():
    """
        Test that Headers can be initialized with None.
    """
    headers = Headers(None)
    
    result = len(headers)
    
    expected = 0
    if result != expected:
        errmsg = f"Expected length {expected}, got {result}"
        raise AssertionError(errmsg)
    
    return


def test_headers_copy_creates_independent_copy():
    """
        Test that copy() creates an independent copy.
    """
    original = Headers({"Content-Type": "application/json"})
    
    copied = original.copy()
    copied["Content-Type"] = "text/plain"
    
    original_value = original.get("Content-Type")
    copied_value = copied.get("Content-Type")
    
    if original_value != "application/json":
        errmsg = f"Expected original to be unchanged, got '{original_value}'"
        raise AssertionError(errmsg)
    
    if copied_value != "text/plain":
        errmsg = f"Expected copy to be modified, got '{copied_value}'"
        raise AssertionError(errmsg)
    
    return


def test_headers_repr_shows_dict():
    """
        Test that __repr__ shows dict representation.
    """
    headers = Headers({"Content-Type": "application/json"})
    
    result = repr(headers)
    
    if "Headers" not in result:
        errmsg = f"Expected 'Headers' in repr, got '{result}'"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Property 6: Request Header Case-Insensitivity
# **Validates: Requirements 3.4**
#
# *For any* header name in any case variation (e.g., "Content-Type",
# "content-type", "CONTENT-TYPE"), accessing request.headers[name] SHALL
# return the same value.
# =============================================================================

import random
import string


def _random_header_name() -> str:
    """
        Generate a random HTTP-style header name.

        Produces names like "X-Custom-Header" with 1-4 segments separated
        by hyphens, each segment being 2-8 alphabetic characters.
    """
    num_segments = random.randint(1, 4)
    segments = []
    for _ in range(num_segments):
        length = random.randint(2, 8)
        segment = ''.join(random.choices(string.ascii_lowercase, k=length))
        # Capitalize first letter to mimic typical header style
        segment = segment[0].upper() + segment[1:]
        segments.append(segment)
    return '-'.join(segments)


def _random_header_value() -> str:
    """
        Generate a random header value string.
    """
    chars = string.ascii_letters + string.digits + ' -_.;=,/'
    length = random.randint(1, 40)
    return ''.join(random.choices(chars, k=length))


def _random_case_variation(name: str) -> str:
    """
        Generate a random case variation of a header name by randomly
        toggling the case of each character.
    """
    result = []
    for ch in name:
        if ch.isalpha():
            if random.choice([True, False]):
                result.append(ch.upper())
            else:
                result.append(ch.lower())
        else:
            result.append(ch)
    return ''.join(result)


def test_property_header_case_insensitivity_getitem():
    """
        Property 6: Request Header Case-Insensitivity - __getitem__

        For any header name in any case variation, accessing headers[name]
        SHALL return the same value as accessing with the original name.

        **Feature: router-request-handling, Property 6: Request Header Case-Insensitivity**
        **Validates: Requirements 3.4**
    """
    for _ in range(100):
        # Generate 1-5 random headers
        num_headers = random.randint(1, 5)
        header_dict = {}
        header_names = []
        for _ in range(num_headers):
            name = _random_header_name()
            # Ensure unique normalized keys
            while name.lower() in [n.lower() for n in header_names]:
                name = _random_header_name()
            header_names.append(name)
            header_dict[name] = _random_header_value()

        headers = Headers(header_dict)

        # For each header, verify case-insensitive access via __getitem__
        for original_name, expected_value in header_dict.items():
            # Test several random case variations
            for _ in range(5):
                variant = _random_case_variation(original_name)
                result = headers[variant]
                if result != expected_value:
                    errmsg = (
                        f"Case-insensitive __getitem__ failed: "
                        f"original='{original_name}', variant='{variant}', "
                        f"expected='{expected_value}', got='{result}'"
                    )
                    raise AssertionError(errmsg)

            # Also test all-lowercase and all-uppercase explicitly
            lower_result = headers[original_name.lower()]
            if lower_result != expected_value:
                errmsg = (
                    f"Lowercase access failed for '{original_name}': "
                    f"expected='{expected_value}', got='{lower_result}'"
                )
                raise AssertionError(errmsg)

            upper_result = headers[original_name.upper()]
            if upper_result != expected_value:
                errmsg = (
                    f"Uppercase access failed for '{original_name}': "
                    f"expected='{expected_value}', got='{upper_result}'"
                )
                raise AssertionError(errmsg)

    return


def test_property_header_case_insensitivity_get():
    """
        Property 6: Request Header Case-Insensitivity - get()

        For any header name in any case variation, headers.get(name) SHALL
        return the same value as headers.get(original_name).

        **Feature: router-request-handling, Property 6: Request Header Case-Insensitivity**
        **Validates: Requirements 3.4**
    """
    for _ in range(100):
        num_headers = random.randint(1, 5)
        header_dict = {}
        header_names = []
        for _ in range(num_headers):
            name = _random_header_name()
            while name.lower() in [n.lower() for n in header_names]:
                name = _random_header_name()
            header_names.append(name)
            header_dict[name] = _random_header_value()

        headers = Headers(header_dict)

        for original_name, expected_value in header_dict.items():
            for _ in range(5):
                variant = _random_case_variation(original_name)
                result = headers.get(variant)
                if result != expected_value:
                    errmsg = (
                        f"Case-insensitive get() failed: "
                        f"original='{original_name}', variant='{variant}', "
                        f"expected='{expected_value}', got='{result}'"
                    )
                    raise AssertionError(errmsg)

        # Also verify that get() with a missing key returns the default
        missing_variant = _random_case_variation("X-Nonexistent-Header")
        default_val = "fallback"
        result = headers.get(missing_variant, default_val)
        if result != default_val:
            errmsg = (
                f"get() with missing key did not return default: "
                f"expected='{default_val}', got='{result}'"
            )
            raise AssertionError(errmsg)

    return


def test_property_header_case_insensitivity_contains():
    """
        Property 6: Request Header Case-Insensitivity - __contains__

        For any header name in any case variation, (name in headers) SHALL
        return True if the header was set with any case of that name.

        **Feature: router-request-handling, Property 6: Request Header Case-Insensitivity**
        **Validates: Requirements 3.4**
    """
    for _ in range(100):
        num_headers = random.randint(1, 5)
        header_dict = {}
        header_names = []
        for _ in range(num_headers):
            name = _random_header_name()
            while name.lower() in [n.lower() for n in header_names]:
                name = _random_header_name()
            header_names.append(name)
            header_dict[name] = _random_header_value()

        headers = Headers(header_dict)

        for original_name in header_dict:
            for _ in range(5):
                variant = _random_case_variation(original_name)
                if variant not in headers:
                    errmsg = (
                        f"Case-insensitive __contains__ failed: "
                        f"original='{original_name}', variant='{variant}' "
                        f"not found in headers"
                    )
                    raise AssertionError(errmsg)

            # Explicit lowercase and uppercase checks
            if original_name.lower() not in headers:
                errmsg = f"Lowercase '{original_name.lower()}' not found in headers"
                raise AssertionError(errmsg)

            if original_name.upper() not in headers:
                errmsg = f"Uppercase '{original_name.upper()}' not found in headers"
                raise AssertionError(errmsg)

    return
