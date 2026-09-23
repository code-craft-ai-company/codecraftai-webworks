"""
    Tests for the URL pattern Matcher class.
    
    This module contains unit tests for the Matcher class which handles
    URL pattern matching with support for static segments, parameterized
    segments, and wildcard segments.
"""

from uuid import UUID

from ccai.webworks.routing.matcher import Matcher, SegmentType


# =============================================================================
# Unit Tests for Matcher Pattern Parsing
# =============================================================================

def test_matcher_parses_static_pattern():
    """
        Test that Matcher correctly parses a static URL pattern.
    """
    matcher = Matcher("/api/users")
    
    if len(matcher.segments) != 2:
        errmsg = f"Expected 2 segments, got {len(matcher.segments)}"
        raise AssertionError(errmsg)
    
    if matcher.segments[0].segment_type != SegmentType.STATIC:
        errmsg = f"Expected STATIC segment, got {matcher.segments[0].segment_type}"
        raise AssertionError(errmsg)
    
    if matcher.segments[0].value != "api":
        errmsg = f"Expected 'api', got '{matcher.segments[0].value}'"
        raise AssertionError(errmsg)
    
    if matcher.segments[1].value != "users":
        errmsg = f"Expected 'users', got '{matcher.segments[1].value}'"
        raise AssertionError(errmsg)
    
    return


def test_matcher_parses_parameterized_pattern():
    """
        Test that Matcher correctly parses a parameterized URL pattern.
    """
    matcher = Matcher("/users/{id}")
    
    if len(matcher.segments) != 2:
        errmsg = f"Expected 2 segments, got {len(matcher.segments)}"
        raise AssertionError(errmsg)
    
    if matcher.segments[0].segment_type != SegmentType.STATIC:
        errmsg = f"Expected STATIC segment, got {matcher.segments[0].segment_type}"
        raise AssertionError(errmsg)
    
    if matcher.segments[1].segment_type != SegmentType.PARAM:
        errmsg = f"Expected PARAM segment, got {matcher.segments[1].segment_type}"
        raise AssertionError(errmsg)
    
    if matcher.segments[1].value != "id":
        errmsg = f"Expected 'id', got '{matcher.segments[1].value}'"
        raise AssertionError(errmsg)
    
    return


def test_matcher_parses_typed_parameter():
    """
        Test that Matcher correctly parses typed parameters.
    """
    matcher = Matcher("/users/{id:int}")
    
    if matcher.segments[1].segment_type != SegmentType.PARAM:
        errmsg = f"Expected PARAM segment, got {matcher.segments[1].segment_type}"
        raise AssertionError(errmsg)
    
    if matcher.segments[1].value != "id":
        errmsg = f"Expected 'id', got '{matcher.segments[1].value}'"
        raise AssertionError(errmsg)
    
    if matcher.segments[1].converter is None:
        errmsg = "Expected converter to be set"
        raise AssertionError(errmsg)
    
    return


def test_matcher_parses_wildcard_pattern():
    """
        Test that Matcher correctly parses wildcard patterns.
    """
    matcher = Matcher("/files/{filepath:path}")
    
    if len(matcher.segments) != 2:
        errmsg = f"Expected 2 segments, got {len(matcher.segments)}"
        raise AssertionError(errmsg)
    
    if matcher.segments[1].segment_type != SegmentType.WILDCARD:
        errmsg = f"Expected WILDCARD segment, got {matcher.segments[1].segment_type}"
        raise AssertionError(errmsg)
    
    if matcher.segments[1].value != "filepath":
        errmsg = f"Expected 'filepath', got '{matcher.segments[1].value}'"
        raise AssertionError(errmsg)
    
    return


def test_matcher_parses_empty_pattern():
    """
        Test that Matcher correctly parses empty/root pattern.
    """
    matcher = Matcher("/")
    
    if len(matcher.segments) != 0:
        errmsg = f"Expected 0 segments for root pattern, got {len(matcher.segments)}"
        raise AssertionError(errmsg)
    
    return


def test_matcher_parses_complex_pattern():
    """
        Test that Matcher correctly parses complex patterns with multiple params.
    """
    matcher = Matcher("/users/{user_id:int}/posts/{slug}")
    
    if len(matcher.segments) != 4:
        errmsg = f"Expected 4 segments, got {len(matcher.segments)}"
        raise AssertionError(errmsg)
    
    # Check segment types
    expected_types = [SegmentType.STATIC, SegmentType.PARAM, SegmentType.STATIC, SegmentType.PARAM]
    actual_types = [s.segment_type for s in matcher.segments]
    
    if actual_types != expected_types:
        errmsg = f"Expected types {expected_types}, got {actual_types}"
        raise AssertionError(errmsg)
    
    return


def test_matcher_raises_on_unknown_converter():
    """
        Test that Matcher raises ValueError for unknown converter.
    """
    try:
        Matcher("/users/{id:unknown}")
        errmsg = "Expected ValueError for unknown converter"
        raise AssertionError(errmsg)
    except ValueError as e:
        if "unknown" not in str(e).lower():
            errmsg = f"Expected error message to mention 'unknown', got: {e}"
            raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for Matcher.match() - Static Patterns
# =============================================================================

def test_matcher_match_static_pattern_success():
    """
        Test that Matcher.match() succeeds for matching static pattern.
    """
    matcher = Matcher("/api/users")
    
    result = matcher.match("/api/users")
    
    if result is None:
        errmsg = "Expected match to succeed"
        raise AssertionError(errmsg)
    
    if result != {}:
        errmsg = f"Expected empty dict for static match, got {result}"
        raise AssertionError(errmsg)
    
    return


def test_matcher_match_static_pattern_failure():
    """
        Test that Matcher.match() returns None for non-matching static pattern.
    """
    matcher = Matcher("/api/users")
    
    result = matcher.match("/api/posts")
    
    if result is not None:
        errmsg = f"Expected None for non-matching path, got {result}"
        raise AssertionError(errmsg)
    
    return


def test_matcher_match_root_pattern():
    """
        Test that Matcher.match() handles root pattern.
    """
    matcher = Matcher("/")
    
    result = matcher.match("/")
    
    if result is None:
        errmsg = "Expected match to succeed for root"
        raise AssertionError(errmsg)
    
    if result != {}:
        errmsg = f"Expected empty dict, got {result}"
        raise AssertionError(errmsg)
    
    return


def test_matcher_match_root_pattern_no_match():
    """
        Test that root pattern doesn't match non-root paths.
    """
    matcher = Matcher("/")
    
    result = matcher.match("/api")
    
    if result is not None:
        errmsg = f"Expected None for non-root path, got {result}"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for Matcher.match() - Parameterized Patterns
# =============================================================================

def test_matcher_match_param_extracts_value():
    """
        Test that Matcher.match() extracts parameter values.
    """
    matcher = Matcher("/users/{id}")
    
    result = matcher.match("/users/42")
    
    if result is None:
        errmsg = "Expected match to succeed"
        raise AssertionError(errmsg)
    
    if "id" not in result:
        errmsg = f"Expected 'id' in result, got {result}"
        raise AssertionError(errmsg)
    
    if result["id"] != "42":
        errmsg = f"Expected '42', got '{result['id']}'"
        raise AssertionError(errmsg)
    
    return


def test_matcher_match_typed_param_converts_int():
    """
        Test that Matcher.match() converts int parameters.
    """
    matcher = Matcher("/users/{id:int}")
    
    result = matcher.match("/users/42")
    
    if result is None:
        errmsg = "Expected match to succeed"
        raise AssertionError(errmsg)
    
    if result["id"] != 42:
        errmsg = f"Expected 42, got {result['id']}"
        raise AssertionError(errmsg)
    
    if not isinstance(result["id"], int):
        errmsg = f"Expected int type, got {type(result['id'])}"
        raise AssertionError(errmsg)
    
    return


def test_matcher_match_typed_param_converts_float():
    """
        Test that Matcher.match() converts float parameters.
    """
    matcher = Matcher("/prices/{amount:float}")
    
    result = matcher.match("/prices/19.99")
    
    if result is None:
        errmsg = "Expected match to succeed"
        raise AssertionError(errmsg)
    
    if abs(result["amount"] - 19.99) > 0.001:
        errmsg = f"Expected 19.99, got {result['amount']}"
        raise AssertionError(errmsg)
    
    if not isinstance(result["amount"], float):
        errmsg = f"Expected float type, got {type(result['amount'])}"
        raise AssertionError(errmsg)
    
    return


def test_matcher_match_typed_param_converts_uuid():
    """
        Test that Matcher.match() converts UUID parameters.
    """
    matcher = Matcher("/items/{item_id:uuid}")
    
    uuid_str = "550e8400-e29b-41d4-a716-446655440000"
    result = matcher.match(f"/items/{uuid_str}")
    
    if result is None:
        errmsg = "Expected match to succeed"
        raise AssertionError(errmsg)
    
    if not isinstance(result["item_id"], UUID):
        errmsg = f"Expected UUID type, got {type(result['item_id'])}"
        raise AssertionError(errmsg)
    
    if str(result["item_id"]) != uuid_str:
        errmsg = f"Expected '{uuid_str}', got '{result['item_id']}'"
        raise AssertionError(errmsg)
    
    return


def test_matcher_match_typed_param_fails_on_invalid():
    """
        Test that Matcher.match() returns None when conversion fails.
    """
    matcher = Matcher("/users/{id:int}")
    
    result = matcher.match("/users/abc")
    
    if result is not None:
        errmsg = f"Expected None for invalid int, got {result}"
        raise AssertionError(errmsg)
    
    return


def test_matcher_match_multiple_params():
    """
        Test that Matcher.match() extracts multiple parameters.
    """
    matcher = Matcher("/users/{user_id:int}/posts/{slug}")
    
    result = matcher.match("/users/42/posts/hello-world")
    
    if result is None:
        errmsg = "Expected match to succeed"
        raise AssertionError(errmsg)
    
    if result["user_id"] != 42:
        errmsg = f"Expected user_id=42, got {result['user_id']}"
        raise AssertionError(errmsg)
    
    if result["slug"] != "hello-world":
        errmsg = f"Expected slug='hello-world', got '{result['slug']}'"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for Matcher.match() - Wildcard Patterns
# =============================================================================

def test_matcher_match_wildcard_captures_remaining():
    """
        Test that wildcard pattern captures remaining path.
    """
    matcher = Matcher("/files/{filepath:path}")
    
    result = matcher.match("/files/docs/readme.txt")
    
    if result is None:
        errmsg = "Expected match to succeed"
        raise AssertionError(errmsg)
    
    if result["filepath"] != "docs/readme.txt":
        errmsg = f"Expected 'docs/readme.txt', got '{result['filepath']}'"
        raise AssertionError(errmsg)
    
    return


def test_matcher_match_wildcard_with_prefix():
    """
        Test wildcard pattern with static prefix segments.
    """
    matcher = Matcher("/static/assets/{path:path}")
    
    result = matcher.match("/static/assets/css/style.css")
    
    if result is None:
        errmsg = "Expected match to succeed"
        raise AssertionError(errmsg)
    
    if result["path"] != "css/style.css":
        errmsg = f"Expected 'css/style.css', got '{result['path']}'"
        raise AssertionError(errmsg)
    
    return


def test_matcher_match_wildcard_single_segment():
    """
        Test wildcard pattern with single remaining segment.
    """
    matcher = Matcher("/files/{filepath:path}")
    
    result = matcher.match("/files/readme.txt")
    
    if result is None:
        errmsg = "Expected match to succeed"
        raise AssertionError(errmsg)
    
    if result["filepath"] != "readme.txt":
        errmsg = f"Expected 'readme.txt', got '{result['filepath']}'"
        raise AssertionError(errmsg)
    
    return


def test_matcher_match_wildcard_requires_content():
    """
        Test that wildcard pattern requires at least one segment.
    """
    matcher = Matcher("/files/{filepath:path}")
    
    result = matcher.match("/files")
    
    if result is not None:
        errmsg = f"Expected None when wildcard has no content, got {result}"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for Matcher.match() - Edge Cases
# =============================================================================

def test_matcher_match_handles_trailing_slash():
    """
        Test that Matcher.match() handles trailing slashes.
    """
    matcher = Matcher("/api/users")
    
    result = matcher.match("/api/users/")
    
    if result is None:
        errmsg = "Expected match to succeed with trailing slash"
        raise AssertionError(errmsg)
    
    return


def test_matcher_match_handles_leading_slash():
    """
        Test that Matcher.match() handles paths without leading slash.
    """
    matcher = Matcher("/api/users")
    
    result = matcher.match("api/users")
    
    if result is None:
        errmsg = "Expected match to succeed without leading slash"
        raise AssertionError(errmsg)
    
    return


def test_matcher_match_wrong_segment_count():
    """
        Test that Matcher.match() returns None for wrong segment count.
    """
    matcher = Matcher("/api/users")
    
    # Too few segments
    result = matcher.match("/api")
    if result is not None:
        errmsg = f"Expected None for too few segments, got {result}"
        raise AssertionError(errmsg)
    
    # Too many segments
    result = matcher.match("/api/users/extra")
    if result is not None:
        errmsg = f"Expected None for too many segments, got {result}"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for Matcher.specificity
# =============================================================================

def test_matcher_specificity_static_only():
    """
        Test specificity calculation for static-only pattern.
    """
    matcher = Matcher("/api/users")
    
    # 2 static segments * 3 points each = 6
    if matcher.specificity != 6:
        errmsg = f"Expected specificity 6, got {matcher.specificity}"
        raise AssertionError(errmsg)
    
    return


def test_matcher_specificity_with_param():
    """
        Test specificity calculation for pattern with parameter.
    """
    matcher = Matcher("/users/{id}")
    
    # 1 static (3) + 1 param (2) = 5
    if matcher.specificity != 5:
        errmsg = f"Expected specificity 5, got {matcher.specificity}"
        raise AssertionError(errmsg)
    
    return


def test_matcher_specificity_with_wildcard():
    """
        Test specificity calculation for pattern with wildcard.
    """
    matcher = Matcher("/files/{path:path}")
    
    # 1 static (3) + 1 wildcard (1) = 4
    if matcher.specificity != 4:
        errmsg = f"Expected specificity 4, got {matcher.specificity}"
        raise AssertionError(errmsg)
    
    return


def test_matcher_specificity_ordering():
    """
        Test that specificity correctly orders routes.
    """
    static = Matcher("/users/profile")      # 6 (3+3)
    param = Matcher("/users/{id}")          # 5 (3+2)
    wildcard = Matcher("/users/{path:path}") # 4 (3+1)
    
    if not (static.specificity > param.specificity > wildcard.specificity):
        errmsg = (
            f"Expected static ({static.specificity}) > "
            f"param ({param.specificity}) > "
            f"wildcard ({wildcard.specificity})"
        )
        raise AssertionError(errmsg)
    
    return


def test_matcher_specificity_empty_pattern():
    """
        Test specificity for empty/root pattern.
    """
    matcher = Matcher("/")
    
    if matcher.specificity != 0:
        errmsg = f"Expected specificity 0 for root, got {matcher.specificity}"
        raise AssertionError(errmsg)
    
    return


def test_matcher_specificity_complex_pattern():
    """
        Test specificity for complex pattern.
    """
    matcher = Matcher("/api/v1/users/{id:int}/posts/{slug}")
    
    # 4 static (12) + 2 param (4) = 16
    if matcher.specificity != 16:
        errmsg = f"Expected specificity 16, got {matcher.specificity}"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for Matcher Special Methods
# =============================================================================

def test_matcher_repr():
    """
        Test Matcher.__repr__() returns expected string.
    """
    matcher = Matcher("/users/{id}")
    
    result = repr(matcher)
    
    if "Matcher" not in result:
        errmsg = f"Expected 'Matcher' in repr, got '{result}'"
        raise AssertionError(errmsg)
    
    if "/users/{id}" not in result:
        errmsg = f"Expected pattern in repr, got '{result}'"
        raise AssertionError(errmsg)
    
    return


def test_matcher_equality():
    """
        Test Matcher equality based on pattern.
    """
    matcher1 = Matcher("/users/{id}")
    matcher2 = Matcher("/users/{id}")
    matcher3 = Matcher("/users/{name}")
    
    if matcher1 != matcher2:
        errmsg = "Expected equal matchers to be equal"
        raise AssertionError(errmsg)
    
    if matcher1 == matcher3:
        errmsg = "Expected different patterns to be not equal"
        raise AssertionError(errmsg)
    
    return


def test_matcher_hash():
    """
        Test Matcher hash based on pattern.
    """
    matcher1 = Matcher("/users/{id}")
    matcher2 = Matcher("/users/{id}")
    
    if hash(matcher1) != hash(matcher2):
        errmsg = "Expected equal matchers to have equal hash"
        raise AssertionError(errmsg)
    
    # Can be used in sets/dicts
    matchers = {matcher1, matcher2}
    if len(matchers) != 1:
        errmsg = f"Expected 1 unique matcher in set, got {len(matchers)}"
        raise AssertionError(errmsg)
    
    return


def test_matcher_pattern_property():
    """
        Test Matcher.pattern property returns original pattern.
    """
    pattern = "/users/{id:int}"
    matcher = Matcher(pattern)
    
    if matcher.pattern != pattern:
        errmsg = f"Expected '{pattern}', got '{matcher.pattern}'"
        raise AssertionError(errmsg)
    
    return

# =============================================================================
# Property-Based Tests
# =============================================================================

import random
import string


def _random_safe_segment(min_len=1, max_len=15):
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


def test_property_single_param_extraction():
    """
    Property 2: Path Parameter Extraction - Single parameter

    For any route with a single parameterized segment and any matching
    request path, the extracted path_params dict SHALL contain the
    parameter name as key with the corresponding path segment value.

    **Feature: router-request-handling, Property 2: Path Parameter Extraction**
    **Validates: Requirements 2.2, 2.3**
    """
    for _ in range(100):
        # Generate random static prefix and param name
        prefix = _random_safe_segment()
        param_name = random.choice(["id", "name", "slug", "key", "code"])
        param_value = _random_safe_segment()

        pattern = f"/{prefix}/{{{param_name}}}"
        matcher = Matcher(pattern)

        path = f"/{prefix}/{param_value}"
        result = matcher.match(path)

        if result is None:
            errmsg = f"Matcher({pattern!r}).match({path!r}) returned None, expected a match"
            raise AssertionError(errmsg)

        # Property: extracted dict contains the parameter name
        if param_name not in result:
            errmsg = f"Expected key '{param_name}' in result {result}"
            raise AssertionError(errmsg)

        # Property: extracted value equals the path segment (str converter)
        if result[param_name] != param_value:
            errmsg = f"Expected '{param_value}', got '{result[param_name]}'"
            raise AssertionError(errmsg)

        # Property: no extra keys beyond the declared parameter
        if len(result) != 1:
            errmsg = f"Expected 1 param, got {len(result)}: {result}"
            raise AssertionError(errmsg)

    return


def test_property_typed_param_extraction_int():
    """
    Property 2: Path Parameter Extraction - Typed int parameter

    For any route with an int-typed parameter and a matching integer
    path segment, the extracted value SHALL be a Python int equal to
    the original integer.

    **Feature: router-request-handling, Property 2: Path Parameter Extraction**
    **Validates: Requirements 2.3**
    """
    matcher = Matcher("/items/{id:int}")

    for _ in range(100):
        int_val = random.randint(0, 999999)
        path = f"/items/{int_val}"
        result = matcher.match(path)

        if result is None:
            errmsg = f"Matcher failed to match {path!r}"
            raise AssertionError(errmsg)

        if "id" not in result:
            errmsg = f"Expected key 'id' in result {result}"
            raise AssertionError(errmsg)

        if not isinstance(result["id"], int):
            errmsg = f"Expected int, got {type(result['id'])} for value {int_val}"
            raise AssertionError(errmsg)

        if result["id"] != int_val:
            errmsg = f"Expected {int_val}, got {result['id']}"
            raise AssertionError(errmsg)

    return


def test_property_typed_param_extraction_uuid():
    """
    Property 2: Path Parameter Extraction - Typed uuid parameter

    For any route with a uuid-typed parameter and a matching UUID
    path segment, the extracted value SHALL be a Python UUID whose
    string representation matches the original.

    **Feature: router-request-handling, Property 2: Path Parameter Extraction**
    **Validates: Requirements 2.3**
    """
    matcher = Matcher("/records/{uid:uuid}")

    for _ in range(100):
        uuid_str = _random_uuid_string()
        path = f"/records/{uuid_str}"
        result = matcher.match(path)

        if result is None:
            errmsg = f"Matcher failed to match {path!r}"
            raise AssertionError(errmsg)

        if "uid" not in result:
            errmsg = f"Expected key 'uid' in result {result}"
            raise AssertionError(errmsg)

        if not isinstance(result["uid"], UUID):
            errmsg = f"Expected UUID, got {type(result['uid'])}"
            raise AssertionError(errmsg)

        if str(result["uid"]) != uuid_str.lower():
            errmsg = f"Expected '{uuid_str.lower()}', got '{str(result['uid'])}'"
            raise AssertionError(errmsg)

    return


def test_property_multiple_params_extraction():
    """
    Property 2: Path Parameter Extraction - Multiple parameters

    For any route with multiple parameterized segments, the extracted
    path_params dict SHALL contain ALL parameter names as keys with
    their corresponding path segment values.

    **Feature: router-request-handling, Property 2: Path Parameter Extraction**
    **Validates: Requirements 2.2, 2.3**
    """
    for _ in range(100):
        # Generate random values for a multi-param pattern
        user_val = _random_safe_segment()
        post_id = random.randint(0, 99999)

        matcher = Matcher("/users/{username}/posts/{post_id:int}")
        path = f"/users/{user_val}/posts/{post_id}"
        result = matcher.match(path)

        if result is None:
            errmsg = f"Matcher failed to match {path!r}"
            raise AssertionError(errmsg)

        # Property: all parameter names present
        if "username" not in result:
            errmsg = f"Expected key 'username' in result {result}"
            raise AssertionError(errmsg)

        if "post_id" not in result:
            errmsg = f"Expected key 'post_id' in result {result}"
            raise AssertionError(errmsg)

        # Property: exactly 2 parameters extracted
        if len(result) != 2:
            errmsg = f"Expected 2 params, got {len(result)}: {result}"
            raise AssertionError(errmsg)

        # Property: values are correct and correctly typed
        if result["username"] != user_val:
            errmsg = f"Expected username '{user_val}', got '{result['username']}'"
            raise AssertionError(errmsg)

        if not isinstance(result["post_id"], int):
            errmsg = f"Expected int for post_id, got {type(result['post_id'])}"
            raise AssertionError(errmsg)

        if result["post_id"] != post_id:
            errmsg = f"Expected post_id {post_id}, got {result['post_id']}"
            raise AssertionError(errmsg)

    return


def test_property_wildcard_param_extraction():
    """
    Property 2: Path Parameter Extraction - Wildcard parameter

    For any route with a wildcard (path) parameter, the extracted value
    SHALL contain the full remaining path including slashes.

    **Feature: router-request-handling, Property 2: Path Parameter Extraction**
    **Validates: Requirements 2.4**
    """
    matcher = Matcher("/files/{filepath:path}")

    for _ in range(100):
        num_segments = random.randint(1, 5)
        segments = [_random_safe_segment() for _ in range(num_segments)]
        path_val = "/".join(segments)

        path = f"/files/{path_val}"
        result = matcher.match(path)

        if result is None:
            errmsg = f"Matcher failed to match {path!r}"
            raise AssertionError(errmsg)

        if "filepath" not in result:
            errmsg = f"Expected key 'filepath' in result {result}"
            raise AssertionError(errmsg)

        if result["filepath"] != path_val:
            errmsg = f"Expected '{path_val}', got '{result['filepath']}'"
            raise AssertionError(errmsg)

    return


def test_property_non_matching_path_returns_none():
    """
    Property 2: Path Parameter Extraction - Non-matching paths

    For any route with parameterized segments, when the path does not
    match (wrong prefix, wrong segment count, or failed conversion),
    the Matcher SHALL return None.

    **Feature: router-request-handling, Property 2: Path Parameter Extraction**
    **Validates: Requirements 2.2, 2.3**
    """
    matcher = Matcher("/users/{id:int}/posts")

    for _ in range(100):
        # Wrong prefix
        wrong_prefix = _random_safe_segment()
        while wrong_prefix == "users":
            wrong_prefix = _random_safe_segment()
        path = f"/{wrong_prefix}/42/posts"
        result = matcher.match(path)
        if result is not None:
            errmsg = f"Expected None for wrong prefix path {path!r}, got {result}"
            raise AssertionError(errmsg)

        # Non-integer value for int param
        non_int = _random_safe_segment()
        # Ensure it's not accidentally a valid integer
        if non_int.isdigit():
            non_int = non_int + "x"
        path = f"/users/{non_int}/posts"
        result = matcher.match(path)
        if result is not None:
            errmsg = f"Expected None for non-int param {path!r}, got {result}"
            raise AssertionError(errmsg)

        # Too few segments
        path = f"/users/{random.randint(0, 999)}"
        result = matcher.match(path)
        if result is not None:
            errmsg = f"Expected None for too-few-segments {path!r}, got {result}"
            raise AssertionError(errmsg)

        # Too many segments
        path = f"/users/{random.randint(0, 999)}/posts/extra"
        result = matcher.match(path)
        if result is not None:
            errmsg = f"Expected None for too-many-segments {path!r}, got {result}"
            raise AssertionError(errmsg)

    return

