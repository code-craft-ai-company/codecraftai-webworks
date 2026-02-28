"""
    Tests for the path utility functions.
    
    This module contains unit tests for the path utility functions
    (normalize_path, split_path, is_parameter_segment, extract_parameter_name)
    used throughout the URL Node Map implementation.
"""

from automojo.webworks.urlnodemap.pathutils import (
    normalize_path,
    split_path,
    is_parameter_segment,
    extract_parameter_name,
)


# =============================================================================
# Unit Tests for normalize_path
# =============================================================================

def test_normalize_path_returns_root_for_empty_string():
    """
        Test that normalize_path returns "/" for empty string.
    """
    result = normalize_path("")
    
    if result != "/":
        errmsg = f"Expected '/', got '{result}'"
        raise AssertionError(errmsg)
    
    return


def test_normalize_path_returns_root_unchanged():
    """
        Test that normalize_path returns "/" unchanged.
    """
    result = normalize_path("/")
    
    if result != "/":
        errmsg = f"Expected '/', got '{result}'"
        raise AssertionError(errmsg)
    
    return


def test_normalize_path_adds_leading_slash():
    """
        Test that normalize_path adds leading slash if missing.
    """
    result = normalize_path("api/v1/users")
    
    if result != "/api/v1/users":
        errmsg = f"Expected '/api/v1/users', got '{result}'"
        raise AssertionError(errmsg)
    
    return


def test_normalize_path_removes_trailing_slash():
    """
        Test that normalize_path removes trailing slash.
        
        Validates: Requirements 2.9, 2.10
    """
    result = normalize_path("/api/v1/users/")
    
    if result != "/api/v1/users":
        errmsg = f"Expected '/api/v1/users', got '{result}'"
        raise AssertionError(errmsg)
    
    return


def test_normalize_path_preserves_root_trailing_slash():
    """
        Test that normalize_path preserves root "/" even with trailing slash.
        
        Validates: Requirements 2.10
    """
    result = normalize_path("//")
    
    if result != "/":
        errmsg = f"Expected '/', got '{result}'"
        raise AssertionError(errmsg)
    
    return


def test_normalize_path_collapses_multiple_slashes():
    """
        Test that normalize_path collapses multiple consecutive slashes.
        
        Validates: Requirements 2.9
    """
    result = normalize_path("//api//v1//users//")
    
    if result != "/api/v1/users":
        errmsg = f"Expected '/api/v1/users', got '{result}'"
        raise AssertionError(errmsg)
    
    return


def test_normalize_path_handles_single_segment():
    """
        Test that normalize_path handles single segment paths.
    """
    result = normalize_path("/api")
    
    if result != "/api":
        errmsg = f"Expected '/api', got '{result}'"
        raise AssertionError(errmsg)
    
    return


def test_normalize_path_handles_single_segment_no_leading_slash():
    """
        Test that normalize_path handles single segment without leading slash.
    """
    result = normalize_path("api")
    
    if result != "/api":
        errmsg = f"Expected '/api', got '{result}'"
        raise AssertionError(errmsg)
    
    return


def test_normalize_path_handles_parameter_segments():
    """
        Test that normalize_path preserves parameter segments.
    """
    result = normalize_path("/api/v1/{user_id}")
    
    if result != "/api/v1/{user_id}":
        errmsg = f"Expected '/api/v1/{{user_id}}', got '{result}'"
        raise AssertionError(errmsg)
    
    return


def test_normalize_path_is_idempotent():
    """
        Test that normalizing an already normalized path returns the same result.
        
        Property 2: Path Normalization Idempotence
        Validates: Requirements 2.9, 2.10
    """
    original = "/api/v1/users"
    first_normalize = normalize_path(original)
    second_normalize = normalize_path(first_normalize)
    
    if first_normalize != second_normalize:
        errmsg = f"Expected idempotent result, got '{first_normalize}' then '{second_normalize}'"
        raise AssertionError(errmsg)
    
    return


def test_normalize_path_idempotent_with_trailing_slash():
    """
        Test idempotence with trailing slash input.
        
        Property 2: Path Normalization Idempotence
        Validates: Requirements 2.9, 2.10
    """
    original = "/api/v1/users/"
    first_normalize = normalize_path(original)
    second_normalize = normalize_path(first_normalize)
    
    if first_normalize != second_normalize:
        errmsg = f"Expected idempotent result, got '{first_normalize}' then '{second_normalize}'"
        raise AssertionError(errmsg)
    
    return


def test_normalize_path_idempotent_with_multiple_slashes():
    """
        Test idempotence with multiple consecutive slashes.
        
        Property 2: Path Normalization Idempotence
        Validates: Requirements 2.9, 2.10
    """
    original = "//api//v1//users//"
    first_normalize = normalize_path(original)
    second_normalize = normalize_path(first_normalize)
    
    if first_normalize != second_normalize:
        errmsg = f"Expected idempotent result, got '{first_normalize}' then '{second_normalize}'"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for split_path
# =============================================================================

def test_split_path_returns_empty_list_for_root():
    """
        Test that split_path returns empty list for root path.
    """
    result = split_path("/")
    
    if result != []:
        errmsg = f"Expected [], got {result}"
        raise AssertionError(errmsg)
    
    return


def test_split_path_returns_segments_for_simple_path():
    """
        Test that split_path returns correct segments for simple path.
    """
    result = split_path("/api/v1/users")
    
    expected = ["api", "v1", "users"]
    if result != expected:
        errmsg = f"Expected {expected}, got {result}"
        raise AssertionError(errmsg)
    
    return


def test_split_path_handles_single_segment():
    """
        Test that split_path handles single segment paths.
    """
    result = split_path("/api")
    
    expected = ["api"]
    if result != expected:
        errmsg = f"Expected {expected}, got {result}"
        raise AssertionError(errmsg)
    
    return


def test_split_path_normalizes_before_splitting():
    """
        Test that split_path normalizes the path before splitting.
    """
    result = split_path("api/v1/users/")
    
    expected = ["api", "v1", "users"]
    if result != expected:
        errmsg = f"Expected {expected}, got {result}"
        raise AssertionError(errmsg)
    
    return


def test_split_path_handles_multiple_slashes():
    """
        Test that split_path handles multiple consecutive slashes.
    """
    result = split_path("//api//v1//users//")
    
    expected = ["api", "v1", "users"]
    if result != expected:
        errmsg = f"Expected {expected}, got {result}"
        raise AssertionError(errmsg)
    
    return


def test_split_path_preserves_parameter_segments():
    """
        Test that split_path preserves parameter segments.
    """
    result = split_path("/api/v1/{user_id}")
    
    expected = ["api", "v1", "{user_id}"]
    if result != expected:
        errmsg = f"Expected {expected}, got {result}"
        raise AssertionError(errmsg)
    
    return


def test_split_path_handles_empty_string():
    """
        Test that split_path handles empty string input.
    """
    result = split_path("")
    
    if result != []:
        errmsg = f"Expected [], got {result}"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for is_parameter_segment
# =============================================================================

def test_is_parameter_segment_returns_true_for_valid_parameter():
    """
        Test that is_parameter_segment returns True for valid parameter.
        
        Validates: Requirements 7.1, 7.2
    """
    result = is_parameter_segment("{user_id}")
    
    if result is not True:
        errmsg = f"Expected True, got {result}"
        raise AssertionError(errmsg)
    
    return


def test_is_parameter_segment_returns_true_for_simple_name():
    """
        Test that is_parameter_segment returns True for simple parameter name.
        
        Validates: Requirements 7.1, 7.2
    """
    result = is_parameter_segment("{id}")
    
    if result is not True:
        errmsg = f"Expected True, got {result}"
        raise AssertionError(errmsg)
    
    return


def test_is_parameter_segment_returns_false_for_literal():
    """
        Test that is_parameter_segment returns False for literal segment.
        
        Validates: Requirements 7.1, 7.2
    """
    result = is_parameter_segment("users")
    
    if result is not False:
        errmsg = f"Expected False, got {result}"
        raise AssertionError(errmsg)
    
    return


def test_is_parameter_segment_returns_false_for_empty_braces():
    """
        Test that is_parameter_segment returns False for empty braces.
        
        Property 11: Parameter Segment Detection
        Validates: Requirements 7.1, 7.2
    """
    result = is_parameter_segment("{}")
    
    if result is not False:
        errmsg = f"Expected False for empty braces, got {result}"
        raise AssertionError(errmsg)
    
    return


def test_is_parameter_segment_returns_false_for_open_brace_only():
    """
        Test that is_parameter_segment returns False for open brace only.
    """
    result = is_parameter_segment("{")
    
    if result is not False:
        errmsg = f"Expected False, got {result}"
        raise AssertionError(errmsg)
    
    return


def test_is_parameter_segment_returns_false_for_close_brace_only():
    """
        Test that is_parameter_segment returns False for close brace only.
    """
    result = is_parameter_segment("}")
    
    if result is not False:
        errmsg = f"Expected False, got {result}"
        raise AssertionError(errmsg)
    
    return


def test_is_parameter_segment_returns_false_for_empty_string():
    """
        Test that is_parameter_segment returns False for empty string.
    """
    result = is_parameter_segment("")
    
    if result is not False:
        errmsg = f"Expected False, got {result}"
        raise AssertionError(errmsg)
    
    return


def test_is_parameter_segment_returns_false_for_partial_braces():
    """
        Test that is_parameter_segment returns False for partial braces.
    """
    result = is_parameter_segment("{user_id")
    
    if result is not False:
        errmsg = f"Expected False, got {result}"
        raise AssertionError(errmsg)
    
    result = is_parameter_segment("user_id}")
    
    if result is not False:
        errmsg = f"Expected False, got {result}"
        raise AssertionError(errmsg)
    
    return


def test_is_parameter_segment_returns_false_for_braces_in_middle():
    """
        Test that is_parameter_segment returns False for braces in middle.
    """
    result = is_parameter_segment("prefix{id}suffix")
    
    if result is not False:
        errmsg = f"Expected False, got {result}"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for extract_parameter_name
# =============================================================================

def test_extract_parameter_name_returns_name_for_valid_parameter():
    """
        Test that extract_parameter_name returns name for valid parameter.
        
        Validates: Requirements 7.1, 7.2
    """
    result = extract_parameter_name("{user_id}")
    
    if result != "user_id":
        errmsg = f"Expected 'user_id', got '{result}'"
        raise AssertionError(errmsg)
    
    return


def test_extract_parameter_name_returns_name_for_simple_parameter():
    """
        Test that extract_parameter_name returns name for simple parameter.
    """
    result = extract_parameter_name("{id}")
    
    if result != "id":
        errmsg = f"Expected 'id', got '{result}'"
        raise AssertionError(errmsg)
    
    return


def test_extract_parameter_name_returns_none_for_literal():
    """
        Test that extract_parameter_name returns None for literal segment.
    """
    result = extract_parameter_name("users")
    
    if result is not None:
        errmsg = f"Expected None, got '{result}'"
        raise AssertionError(errmsg)
    
    return


def test_extract_parameter_name_returns_none_for_empty_braces():
    """
        Test that extract_parameter_name returns None for empty braces.
    """
    result = extract_parameter_name("{}")
    
    if result is not None:
        errmsg = f"Expected None for empty braces, got '{result}'"
        raise AssertionError(errmsg)
    
    return


def test_extract_parameter_name_returns_none_for_empty_string():
    """
        Test that extract_parameter_name returns None for empty string.
    """
    result = extract_parameter_name("")
    
    if result is not None:
        errmsg = f"Expected None, got '{result}'"
        raise AssertionError(errmsg)
    
    return


def test_extract_parameter_name_returns_none_for_partial_braces():
    """
        Test that extract_parameter_name returns None for partial braces.
    """
    result = extract_parameter_name("{user_id")
    
    if result is not None:
        errmsg = f"Expected None, got '{result}'"
        raise AssertionError(errmsg)
    
    result = extract_parameter_name("user_id}")
    
    if result is not None:
        errmsg = f"Expected None, got '{result}'"
        raise AssertionError(errmsg)
    
    return


def test_extract_parameter_name_handles_underscores():
    """
        Test that extract_parameter_name handles underscores in name.
    """
    result = extract_parameter_name("{user_profile_id}")
    
    if result != "user_profile_id":
        errmsg = f"Expected 'user_profile_id', got '{result}'"
        raise AssertionError(errmsg)
    
    return


def test_extract_parameter_name_handles_numbers():
    """
        Test that extract_parameter_name handles numbers in name.
    """
    result = extract_parameter_name("{item123}")
    
    if result != "item123":
        errmsg = f"Expected 'item123', got '{result}'"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Random Data Generators for Property Tests
# =============================================================================

import random
import string


def generate_random_segment(min_length: int = 1, max_length: int = 20) -> str:
    """
        Generate a random valid path segment.
        
        Valid segments contain alphanumeric characters, underscores, and hyphens.
        They do not start with a slash.
    """
    length = random.randint(min_length, max_length)
    # Valid segment characters: alphanumeric, underscore, hyphen
    chars = string.ascii_lowercase + string.digits + "_-"
    # First character should be alphanumeric
    first_char = random.choice(string.ascii_lowercase + string.digits)
    if length == 1:
        return first_char
    rest = ''.join(random.choices(chars, k=length - 1))
    return first_char + rest


def generate_random_parameter_segment() -> str:
    """
        Generate a random parameter segment in {name} format.
    """
    name_length = random.randint(1, 15)
    # Parameter names: alphanumeric and underscores
    chars = string.ascii_lowercase + string.digits + "_"
    first_char = random.choice(string.ascii_lowercase)
    if name_length == 1:
        name = first_char
    else:
        rest = ''.join(random.choices(chars, k=name_length - 1))
        name = first_char + rest
    return "{" + name + "}"


def generate_random_path(min_segments: int = 0, max_segments: int = 6) -> str:
    """
        Generate a random valid path string.
        
        The path may have:
        - Leading slash or not
        - Trailing slash or not
        - Multiple consecutive slashes
        - Mix of literal and parameter segments
    """
    num_segments = random.randint(min_segments, max_segments)
    
    if num_segments == 0:
        # Return root path with possible variations
        variations = ["/", "//", "///"]
        return random.choice(variations)
    
    segments = []
    for _ in range(num_segments):
        # 20% chance of parameter segment
        if random.random() < 0.2:
            segments.append(generate_random_parameter_segment())
        else:
            segments.append(generate_random_segment())
    
    # Build path with random variations
    path_parts = []
    
    # Random leading slashes (0-3)
    leading_slashes = random.randint(0, 3)
    path_parts.append("/" * leading_slashes)
    
    for i, segment in enumerate(segments):
        path_parts.append(segment)
        if i < len(segments) - 1:
            # Random number of slashes between segments (1-3)
            num_slashes = random.randint(1, 3)
            path_parts.append("/" * num_slashes)
    
    # Random trailing slashes (0-3)
    trailing_slashes = random.randint(0, 3)
    path_parts.append("/" * trailing_slashes)
    
    return "".join(path_parts)


# =============================================================================
# Property-Based Tests
# =============================================================================

# Feature: url-node-map, Property 2: Path Normalization Idempotence
# *For any* valid path string, normalizing it multiple times SHALL produce
# the same result as normalizing it once.
# `normalize_path(normalize_path(path)) == normalize_path(path)`
# **Validates: Requirements 2.9, 2.10**

def test_property_2_path_normalization_idempotence():
    """
        Property 2: Path Normalization Idempotence
        
        For any valid path string, normalizing it multiple times SHALL produce
        the same result as normalizing it once.
        
        normalize_path(normalize_path(path)) == normalize_path(path)
        
        **Validates: Requirements 2.9, 2.10**
    """
    # Run 100 iterations with randomly generated paths
    for iteration in range(100):
        # Generate a random path
        original_path = generate_random_path()
        
        # Normalize once
        first_normalize = normalize_path(original_path)
        
        # Normalize twice
        second_normalize = normalize_path(first_normalize)
        
        # Property: normalizing twice should equal normalizing once
        if first_normalize != second_normalize:
            errmsg = (
                f"Iteration {iteration}: Path normalization is not idempotent.\n"
                f"  Original path: '{original_path}'\n"
                f"  First normalize: '{first_normalize}'\n"
                f"  Second normalize: '{second_normalize}'"
            )
            raise AssertionError(errmsg)
        
        # Additional check: normalize three times should still be the same
        third_normalize = normalize_path(second_normalize)
        if second_normalize != third_normalize:
            errmsg = (
                f"Iteration {iteration}: Path normalization is not idempotent after 3 applications.\n"
                f"  Original path: '{original_path}'\n"
                f"  Second normalize: '{second_normalize}'\n"
                f"  Third normalize: '{third_normalize}'"
            )
            raise AssertionError(errmsg)
    
    return


def test_property_2_path_normalization_idempotence_edge_cases():
    """
        Property 2: Path Normalization Idempotence (Edge Cases)
        
        Tests idempotence with specific edge case patterns that might
        cause normalization issues.
        
        **Validates: Requirements 2.9, 2.10**
    """
    # Edge case patterns to test
    edge_cases = [
        "",                          # Empty string
        "/",                         # Root only
        "//",                        # Multiple root slashes
        "///",                       # Triple root slashes
        "api",                       # No leading slash
        "/api",                      # Simple path
        "/api/",                     # Trailing slash
        "/api//",                    # Multiple trailing slashes
        "//api",                     # Multiple leading slashes
        "//api//",                   # Multiple leading and trailing
        "/api/v1/users",             # Multi-segment
        "/api//v1///users",          # Multiple internal slashes
        "api/v1/users/",             # No leading, with trailing
        "//api//v1//users//",        # All variations
        "/{id}",                     # Parameter segment
        "/api/{id}/details",         # Mixed segments
        "/api/v1/{user_id}/posts/{post_id}",  # Multiple parameters
    ]
    
    for iteration, original_path in enumerate(edge_cases):
        # Normalize once
        first_normalize = normalize_path(original_path)
        
        # Normalize twice
        second_normalize = normalize_path(first_normalize)
        
        # Property: normalizing twice should equal normalizing once
        if first_normalize != second_normalize:
            errmsg = (
                f"Edge case {iteration}: Path normalization is not idempotent.\n"
                f"  Original path: '{original_path}'\n"
                f"  First normalize: '{first_normalize}'\n"
                f"  Second normalize: '{second_normalize}'"
            )
            raise AssertionError(errmsg)
    
    return


def test_property_2_path_normalization_canonical_form():
    """
        Property 2: Path Normalization Idempotence (Canonical Form)
        
        Verifies that normalized paths have the expected canonical form:
        - Start with exactly one "/"
        - No trailing slash (except for root)
        - No consecutive slashes
        
        **Validates: Requirements 2.9, 2.10**
    """
    # Run 100 iterations with randomly generated paths
    for iteration in range(100):
        # Generate a random path
        original_path = generate_random_path()
        
        # Normalize the path
        normalized = normalize_path(original_path)
        
        # Property: normalized path must start with exactly one "/"
        if not normalized.startswith("/"):
            errmsg = (
                f"Iteration {iteration}: Normalized path does not start with '/'.\n"
                f"  Original path: '{original_path}'\n"
                f"  Normalized: '{normalized}'"
            )
            raise AssertionError(errmsg)
        
        # Property: normalized path must not have consecutive slashes
        if "//" in normalized:
            errmsg = (
                f"Iteration {iteration}: Normalized path contains consecutive slashes.\n"
                f"  Original path: '{original_path}'\n"
                f"  Normalized: '{normalized}'"
            )
            raise AssertionError(errmsg)
        
        # Property: normalized path must not have trailing slash (except root)
        if len(normalized) > 1 and normalized.endswith("/"):
            errmsg = (
                f"Iteration {iteration}: Normalized path has trailing slash.\n"
                f"  Original path: '{original_path}'\n"
                f"  Normalized: '{normalized}'"
            )
            raise AssertionError(errmsg)
        
        # Property: root path must be exactly "/"
        if normalized == "/" or (len(normalized) == 1 and normalized[0] == "/"):
            if normalized != "/":
                errmsg = (
                    f"Iteration {iteration}: Root path is not exactly '/'.\n"
                    f"  Original path: '{original_path}'\n"
                    f"  Normalized: '{normalized}'"
                )
                raise AssertionError(errmsg)
    
    return


# =============================================================================
# Property 11: Parameter Segment Detection
# =============================================================================

# Feature: url-node-map, Property 11: Parameter Segment Detection
# *For any* segment string, `is_parameter_segment(segment)` SHALL return True
# if and only if the segment matches the pattern `{name}` where name is non-empty.
# **Validates: Requirements 7.1, 7.2**


def generate_random_non_parameter_segment() -> str:
    """
        Generate a random segment that is NOT a valid parameter segment.
        
        This includes:
        - Regular literal segments (alphanumeric)
        - Empty string
        - Partial braces (missing open or close)
        - Empty braces {}
        - Braces with content before/after
        - Nested braces
        - Other special characters
    """
    strategies = [
        # Regular literal segment
        lambda: generate_random_segment(1, 15),
        # Empty string
        lambda: "",
        # Open brace only
        lambda: "{",
        # Close brace only
        lambda: "}",
        # Empty braces
        lambda: "{}",
        # Missing close brace
        lambda: "{" + generate_random_segment(1, 10),
        # Missing open brace
        lambda: generate_random_segment(1, 10) + "}",
        # Prefix before braces
        lambda: generate_random_segment(1, 5) + "{" + generate_random_segment(1, 5) + "}",
        # Suffix after braces
        lambda: "{" + generate_random_segment(1, 5) + "}" + generate_random_segment(1, 5),
        # Both prefix and suffix
        lambda: generate_random_segment(1, 3) + "{" + generate_random_segment(1, 5) + "}" + generate_random_segment(1, 3),
        # Nested braces
        lambda: "{{" + generate_random_segment(1, 5) + "}}",
        # Multiple brace pairs
        lambda: "{" + generate_random_segment(1, 3) + "}{" + generate_random_segment(1, 3) + "}",
        # Just whitespace in braces
        lambda: "{ }",
        # Numbers only (valid literal)
        lambda: str(random.randint(1, 99999)),
        # Special characters
        lambda: random.choice([".", "..", "...", "*", "**", "?", "#", "@", "!", "$"]),
    ]
    
    return random.choice(strategies)()


def is_valid_parameter_pattern(segment: str) -> bool:
    """
        Reference implementation to check if a segment matches the parameter pattern.
        
        A valid parameter segment:
        - Starts with exactly one "{"
        - Ends with exactly one "}"
        - Has at least one character between the braces (non-empty name)
        - The entire string is just {name} with no prefix or suffix
    """
    if not segment:
        return False
    
    if len(segment) < 3:  # Minimum is "{x}" which is 3 characters
        return False
    
    if not segment.startswith("{"):
        return False
    
    if not segment.endswith("}"):
        return False
    
    # Extract what's between the braces
    inner = segment[1:-1]
    
    # Must have non-empty content
    if len(inner) == 0:
        return False
    
    # The inner content should not contain additional braces
    # (this ensures we have exactly one { at start and one } at end)
    if "{" in inner or "}" in inner:
        return False
    
    # Inner content must not be only whitespace
    if inner.strip() == "":
        return False
    
    return True


def test_property_11_parameter_segment_detection():
    """
        Property 11: Parameter Segment Detection
        
        For any segment string, `is_parameter_segment(segment)` SHALL return True
        if and only if the segment matches the pattern `{name}` where name is non-empty.
        
        **Validates: Requirements 7.1, 7.2**
    """
    # Run 100 iterations with randomly generated segments
    for iteration in range(100):
        # Generate a mix of valid parameter segments and non-parameter segments
        if random.random() < 0.5:
            # Generate a valid parameter segment
            segment = generate_random_parameter_segment()
            expected = True
        else:
            # Generate a non-parameter segment
            segment = generate_random_non_parameter_segment()
            expected = is_valid_parameter_pattern(segment)
        
        # Test the function
        result = is_parameter_segment(segment)
        
        # Verify the result matches expected
        if result != expected:
            errmsg = (
                f"Iteration {iteration}: Parameter segment detection failed.\n"
                f"  Segment: '{segment}'\n"
                f"  Expected: {expected}\n"
                f"  Got: {result}"
            )
            raise AssertionError(errmsg)
    
    return


def test_property_11_parameter_segment_true_condition():
    """
        Property 11: Parameter Segment Detection (True Condition)
        
        Verifies that is_parameter_segment returns True ONLY when the segment
        matches the exact pattern {name} with non-empty name.
        
        **Validates: Requirements 7.1, 7.2**
    """
    # Run 100 iterations with valid parameter segments
    for iteration in range(100):
        # Generate a valid parameter segment
        segment = generate_random_parameter_segment()
        
        # Test the function
        result = is_parameter_segment(segment)
        
        # Property: must return True for valid parameter segments
        if result is not True:
            errmsg = (
                f"Iteration {iteration}: Expected True for valid parameter segment.\n"
                f"  Segment: '{segment}'\n"
                f"  Got: {result}"
            )
            raise AssertionError(errmsg)
        
        # Verify the segment actually matches the pattern
        if not (segment.startswith("{") and segment.endswith("}")):
            errmsg = (
                f"Iteration {iteration}: Generated segment doesn't match pattern.\n"
                f"  Segment: '{segment}'"
            )
            raise AssertionError(errmsg)
        
        # Verify the name is non-empty
        inner = segment[1:-1]
        if len(inner) == 0:
            errmsg = (
                f"Iteration {iteration}: Generated segment has empty name.\n"
                f"  Segment: '{segment}'"
            )
            raise AssertionError(errmsg)
    
    return


def test_property_11_parameter_segment_false_condition():
    """
        Property 11: Parameter Segment Detection (False Condition)
        
        Verifies that is_parameter_segment returns False for segments that
        do NOT match the pattern {name} with non-empty name.
        
        **Validates: Requirements 7.1, 7.2**
    """
    # Run 100 iterations with non-parameter segments
    for iteration in range(100):
        # Generate a non-parameter segment
        segment = generate_random_non_parameter_segment()
        
        # Skip if we accidentally generated a valid parameter (unlikely but possible)
        if is_valid_parameter_pattern(segment):
            continue
        
        # Test the function
        result = is_parameter_segment(segment)
        
        # Property: must return False for non-parameter segments
        if result is not False:
            errmsg = (
                f"Iteration {iteration}: Expected False for non-parameter segment.\n"
                f"  Segment: '{segment}'\n"
                f"  Got: {result}"
            )
            raise AssertionError(errmsg)
    
    return


def test_property_11_parameter_segment_biconditional():
    """
        Property 11: Parameter Segment Detection (Biconditional)
        
        Verifies the biconditional: is_parameter_segment(segment) == True
        if and only if segment matches {name} with non-empty name.
        
        This test generates completely random strings and verifies the
        function's output matches the expected pattern.
        
        **Validates: Requirements 7.1, 7.2**
    """
    # Generate a wide variety of random strings
    for iteration in range(100):
        # Generate random string with various characters
        length = random.randint(0, 25)
        if length == 0:
            segment = ""
        else:
            # Include braces, alphanumeric, and special chars
            chars = string.ascii_letters + string.digits + "_{}" + ".-*?#@!$%^&()[]<>:;'\""
            segment = ''.join(random.choices(chars, k=length))
        
        # Determine expected result using reference implementation
        expected = is_valid_parameter_pattern(segment)
        
        # Test the function
        result = is_parameter_segment(segment)
        
        # Property: result must match expected
        if result != expected:
            errmsg = (
                f"Iteration {iteration}: Biconditional property violated.\n"
                f"  Segment: '{segment}'\n"
                f"  Expected: {expected}\n"
                f"  Got: {result}"
            )
            raise AssertionError(errmsg)
    
    return


def test_property_11_parameter_segment_edge_cases():
    """
        Property 11: Parameter Segment Detection (Edge Cases)
        
        Tests specific edge cases that might cause issues with parameter
        segment detection.
        
        **Validates: Requirements 7.1, 7.2**
    """
    # Edge cases with expected results
    edge_cases = [
        # (segment, expected_result)
        ("", False),                          # Empty string
        ("{}", False),                        # Empty braces
        ("{a}", True),                        # Single character name
        ("{ab}", True),                       # Two character name
        ("{abc}", True),                      # Three character name
        ("{user_id}", True),                  # Underscore in name
        ("{userId}", True),                   # CamelCase name
        ("{user-id}", True),                  # Hyphen in name
        ("{123}", True),                      # Numeric name
        ("{a1b2c3}", True),                   # Alphanumeric name
        ("{", False),                         # Open brace only
        ("}", False),                         # Close brace only
        ("{{}", False),                       # Double open brace
        ("{}}", False),                       # Double close brace
        ("{{a}}", False),                     # Nested braces
        ("{a}{b}", False),                    # Multiple brace pairs
        ("a{b}", False),                      # Prefix before brace
        ("{a}b", False),                      # Suffix after brace
        ("a{b}c", False),                     # Both prefix and suffix
        ("{ }", False),                       # Space only in braces
        ("{ a}", True),                       # Space before name (still valid pattern)
        ("{a }", True),                       # Space after name (still valid pattern)
        ("{ a }", True),                      # Spaces around name (still valid pattern)
        ("{a{b}}", False),                    # Nested open brace
        ("{{a}b}", False),                    # Double open with content
        ("users", False),                     # Regular literal
        ("api", False),                       # Regular literal
        ("v1", False),                        # Version literal
        ("123", False),                       # Numeric literal
        ("_", False),                         # Underscore only
        ("-", False),                         # Hyphen only
        (".", False),                         # Dot only
        ("..", False),                        # Double dot
        ("*", False),                         # Wildcard
        ("**", False),                        # Double wildcard
    ]
    
    for segment, expected in edge_cases:
        result = is_parameter_segment(segment)
        
        if result != expected:
            errmsg = (
                f"Edge case failed.\n"
                f"  Segment: '{segment}'\n"
                f"  Expected: {expected}\n"
                f"  Got: {result}"
            )
            raise AssertionError(errmsg)
    
    return
