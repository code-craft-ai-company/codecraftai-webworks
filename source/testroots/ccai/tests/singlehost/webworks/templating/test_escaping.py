"""
    Tests for the auto-escaping utilities.
    
    This module tests the SafeString class and safe() function including:
    - SafeString creation and string subclass behavior
    - __html__() method for Jinja2 compatibility
    - safe() function for creating SafeString instances
    - String concatenation preserving SafeString type
    - Edge cases and boundary conditions
"""

from ccai.webworks.templating.escaping import SafeString, safe


# =============================================================================
# SafeString Class Tests
# =============================================================================

def test_safe_string_is_str_subclass():
    """
        Test that SafeString is a subclass of str.
    """
    safe_str = SafeString("test")
    
    if not isinstance(safe_str, str):
        raise AssertionError("SafeString should be a subclass of str")
    
    return


def test_safe_string_stores_value():
    """
        Test that SafeString stores the string value.
    """
    value = "Hello, World!"
    safe_str = SafeString(value)
    
    if str(safe_str) != value:
        raise AssertionError(f"Expected '{value}', got '{str(safe_str)}'")
    
    return


def test_safe_string_equality_with_str():
    """
        Test that SafeString equals equivalent str.
    """
    value = "test string"
    safe_str = SafeString(value)
    
    if safe_str != value:
        raise AssertionError(f"SafeString should equal equivalent str")
    
    return


def test_safe_string_with_empty_string():
    """
        Test that SafeString works with empty string.
    """
    safe_str = SafeString("")
    
    if safe_str != "":
        raise AssertionError("SafeString should handle empty string")
    
    if len(safe_str) != 0:
        raise AssertionError(f"Expected length 0, got {len(safe_str)}")
    
    return


def test_safe_string_with_html_content():
    """
        Test that SafeString preserves HTML content.
    """
    html = "<strong>Bold text</strong>"
    safe_str = SafeString(html)
    
    if safe_str != html:
        raise AssertionError(f"Expected '{html}', got '{safe_str}'")
    
    return


def test_safe_string_with_special_characters():
    """
        Test that SafeString preserves special characters.
    """
    special = "&amp; < > \" ' &lt;"
    safe_str = SafeString(special)
    
    if safe_str != special:
        raise AssertionError(f"Expected '{special}', got '{safe_str}'")
    
    return


def test_safe_string_with_unicode():
    """
        Test that SafeString handles unicode characters.
    """
    unicode_str = "Hello, 世界! 🌍"
    safe_str = SafeString(unicode_str)
    
    if safe_str != unicode_str:
        raise AssertionError(f"Expected '{unicode_str}', got '{safe_str}'")
    
    return


def test_safe_string_with_newlines():
    """
        Test that SafeString preserves newlines.
    """
    multiline = "Line 1\nLine 2\nLine 3"
    safe_str = SafeString(multiline)
    
    if safe_str != multiline:
        raise AssertionError(f"Expected '{multiline}', got '{safe_str}'")
    
    return


# =============================================================================
# __html__() Method Tests
# =============================================================================

def test_html_method_returns_self():
    """
        Test that __html__() returns self.
    """
    value = "<p>Test</p>"
    safe_str = SafeString(value)
    
    result = safe_str.__html__()
    
    if result is not safe_str:
        raise AssertionError("__html__() should return self (same object)")
    
    return


def test_html_method_returns_string_value():
    """
        Test that __html__() returns the string value.
    """
    value = "<div>Content</div>"
    safe_str = SafeString(value)
    
    result = safe_str.__html__()
    
    if result != value:
        raise AssertionError(f"Expected '{value}', got '{result}'")
    
    return


def test_html_method_with_empty_string():
    """
        Test that __html__() works with empty string.
    """
    safe_str = SafeString("")
    
    result = safe_str.__html__()
    
    if result != "":
        raise AssertionError(f"Expected empty string, got '{result}'")
    
    return


def test_html_method_callable():
    """
        Test that __html__ is callable (protocol requirement).
    """
    safe_str = SafeString("test")
    
    if not callable(getattr(safe_str, "__html__", None)):
        raise AssertionError("SafeString should have callable __html__ method")
    
    return


# =============================================================================
# __repr__() Method Tests
# =============================================================================

def test_repr_shows_safe_string():
    """
        Test that __repr__() shows SafeString wrapper.
    """
    safe_str = SafeString("test")
    
    result = repr(safe_str)
    
    if "SafeString" not in result:
        raise AssertionError(f"repr should contain 'SafeString', got '{result}'")
    
    return


def test_repr_shows_value():
    """
        Test that __repr__() shows the string value.
    """
    value = "test value"
    safe_str = SafeString(value)
    
    result = repr(safe_str)
    
    if value not in result:
        raise AssertionError(f"repr should contain value, got '{result}'")
    
    return


# =============================================================================
# String Concatenation Tests
# =============================================================================

def test_add_with_str_returns_safe_string():
    """
        Test that SafeString + str returns SafeString.
    """
    safe_str = SafeString("Hello, ")
    result = safe_str + "World!"
    
    if not isinstance(result, SafeString):
        raise AssertionError("SafeString + str should return SafeString")
    
    if result != "Hello, World!":
        raise AssertionError(f"Expected 'Hello, World!', got '{result}'")
    
    return


def test_add_with_safe_string_returns_safe_string():
    """
        Test that SafeString + SafeString returns SafeString.
    """
    safe1 = SafeString("Hello, ")
    safe2 = SafeString("World!")
    result = safe1 + safe2
    
    if not isinstance(result, SafeString):
        raise AssertionError("SafeString + SafeString should return SafeString")
    
    if result != "Hello, World!":
        raise AssertionError(f"Expected 'Hello, World!', got '{result}'")
    
    return


def test_radd_with_str_returns_safe_string():
    """
        Test that str + SafeString returns SafeString.
    """
    safe_str = SafeString("World!")
    result = "Hello, " + safe_str
    
    if not isinstance(result, SafeString):
        raise AssertionError("str + SafeString should return SafeString")
    
    if result != "Hello, World!":
        raise AssertionError(f"Expected 'Hello, World!', got '{result}'")
    
    return


def test_concatenation_chain():
    """
        Test that chained concatenation preserves SafeString.
    """
    safe_str = SafeString("A")
    result = safe_str + "B" + "C"
    
    if not isinstance(result, SafeString):
        raise AssertionError("Chained concatenation should return SafeString")
    
    if result != "ABC":
        raise AssertionError(f"Expected 'ABC', got '{result}'")
    
    return


def test_concatenation_with_empty_strings():
    """
        Test concatenation with empty strings.
    """
    safe_str = SafeString("test")
    
    result1 = safe_str + ""
    result2 = "" + safe_str
    
    if not isinstance(result1, SafeString):
        raise AssertionError("SafeString + '' should return SafeString")
    
    if not isinstance(result2, SafeString):
        raise AssertionError("'' + SafeString should return SafeString")
    
    if result1 != "test" or result2 != "test":
        raise AssertionError("Concatenation with empty string should preserve value")
    
    return


# =============================================================================
# String Method Inheritance Tests
# =============================================================================

def test_safe_string_len():
    """
        Test that len() works on SafeString.
    """
    safe_str = SafeString("Hello")
    
    if len(safe_str) != 5:
        raise AssertionError(f"Expected length 5, got {len(safe_str)}")
    
    return


def test_safe_string_indexing():
    """
        Test that indexing works on SafeString.
    """
    safe_str = SafeString("Hello")
    
    if safe_str[0] != "H":
        raise AssertionError(f"Expected 'H', got '{safe_str[0]}'")
    
    if safe_str[-1] != "o":
        raise AssertionError(f"Expected 'o', got '{safe_str[-1]}'")
    
    return


def test_safe_string_slicing():
    """
        Test that slicing works on SafeString.
    """
    safe_str = SafeString("Hello, World!")
    
    result = safe_str[0:5]
    
    if result != "Hello":
        raise AssertionError(f"Expected 'Hello', got '{result}'")
    
    return


def test_safe_string_upper():
    """
        Test that upper() works on SafeString.
    """
    safe_str = SafeString("hello")
    
    result = safe_str.upper()
    
    if result != "HELLO":
        raise AssertionError(f"Expected 'HELLO', got '{result}'")
    
    return


def test_safe_string_lower():
    """
        Test that lower() works on SafeString.
    """
    safe_str = SafeString("HELLO")
    
    result = safe_str.lower()
    
    if result != "hello":
        raise AssertionError(f"Expected 'hello', got '{result}'")
    
    return


def test_safe_string_strip():
    """
        Test that strip() works on SafeString.
    """
    safe_str = SafeString("  hello  ")
    
    result = safe_str.strip()
    
    if result != "hello":
        raise AssertionError(f"Expected 'hello', got '{result}'")
    
    return


def test_safe_string_split():
    """
        Test that split() works on SafeString.
    """
    safe_str = SafeString("a,b,c")
    
    result = safe_str.split(",")
    
    if result != ["a", "b", "c"]:
        raise AssertionError(f"Expected ['a', 'b', 'c'], got {result}")
    
    return


def test_safe_string_in_operator():
    """
        Test that 'in' operator works on SafeString.
    """
    safe_str = SafeString("Hello, World!")
    
    if "World" not in safe_str:
        raise AssertionError("'World' should be in SafeString")
    
    if "xyz" in safe_str:
        raise AssertionError("'xyz' should not be in SafeString")
    
    return


def test_safe_string_iteration():
    """
        Test that iteration works on SafeString.
    """
    safe_str = SafeString("abc")
    
    chars = list(safe_str)
    
    if chars != ["a", "b", "c"]:
        raise AssertionError(f"Expected ['a', 'b', 'c'], got {chars}")
    
    return


# =============================================================================
# safe() Function Tests
# =============================================================================

def test_safe_returns_safe_string():
    """
        Test that safe() returns a SafeString instance.
    """
    result = safe("test")
    
    if not isinstance(result, SafeString):
        raise AssertionError("safe() should return SafeString instance")
    
    return


def test_safe_preserves_value():
    """
        Test that safe() preserves the string value.
    """
    value = "Hello, World!"
    result = safe(value)
    
    if result != value:
        raise AssertionError(f"Expected '{value}', got '{result}'")
    
    return


def test_safe_with_empty_string():
    """
        Test that safe() works with empty string.
    """
    result = safe("")
    
    if not isinstance(result, SafeString):
        raise AssertionError("safe('') should return SafeString")
    
    if result != "":
        raise AssertionError(f"Expected empty string, got '{result}'")
    
    return


def test_safe_with_html_content():
    """
        Test that safe() preserves HTML content.
    """
    html = "<script>alert('xss')</script>"
    result = safe(html)
    
    if result != html:
        raise AssertionError(f"Expected '{html}', got '{result}'")
    
    return


def test_safe_with_special_characters():
    """
        Test that safe() preserves special characters.
    """
    special = "& < > \" '"
    result = safe(special)
    
    if result != special:
        raise AssertionError(f"Expected '{special}', got '{result}'")
    
    return


def test_safe_with_unicode():
    """
        Test that safe() handles unicode characters.
    """
    unicode_str = "日本語 🎉"
    result = safe(unicode_str)
    
    if result != unicode_str:
        raise AssertionError(f"Expected '{unicode_str}', got '{result}'")
    
    return


def test_safe_result_has_html_method():
    """
        Test that safe() result has __html__() method.
    """
    result = safe("test")
    
    if not hasattr(result, "__html__"):
        raise AssertionError("safe() result should have __html__ method")
    
    if not callable(result.__html__):
        raise AssertionError("__html__ should be callable")
    
    return


def test_safe_result_html_returns_value():
    """
        Test that safe() result's __html__() returns the value.
    """
    value = "<p>Test</p>"
    result = safe(value)
    
    html_result = result.__html__()
    
    if html_result != value:
        raise AssertionError(f"Expected '{value}', got '{html_result}'")
    
    return


# =============================================================================
# Edge Cases
# =============================================================================

def test_safe_string_with_null_bytes():
    """
        Test that SafeString handles null bytes.
    """
    value = "before\x00after"
    safe_str = SafeString(value)
    
    if safe_str != value:
        raise AssertionError(f"Expected '{value}', got '{safe_str}'")
    
    return


def test_safe_string_with_very_long_string():
    """
        Test that SafeString handles very long strings.
    """
    value = "x" * 100000
    safe_str = SafeString(value)
    
    if len(safe_str) != 100000:
        raise AssertionError(f"Expected length 100000, got {len(safe_str)}")
    
    if safe_str != value:
        raise AssertionError("SafeString should preserve very long strings")
    
    return


def test_safe_string_with_whitespace_only():
    """
        Test that SafeString handles whitespace-only strings.
    """
    value = "   \t\n\r   "
    safe_str = SafeString(value)
    
    if safe_str != value:
        raise AssertionError(f"Expected '{value!r}', got '{safe_str!r}'")
    
    return


def test_safe_string_hash():
    """
        Test that SafeString is hashable.
    """
    safe_str = SafeString("test")
    
    # Should not raise
    hash_value = hash(safe_str)
    
    # Hash should match equivalent str
    if hash_value != hash("test"):
        raise AssertionError("SafeString hash should match str hash")
    
    return


def test_safe_string_in_dict():
    """
        Test that SafeString can be used as dict key.
    """
    safe_str = SafeString("key")
    
    d = {safe_str: "value"}
    
    if d[safe_str] != "value":
        raise AssertionError("SafeString should work as dict key")
    
    # Should also work with equivalent str
    if d["key"] != "value":
        raise AssertionError("SafeString key should match str key")
    
    return


def test_safe_string_in_set():
    """
        Test that SafeString can be used in sets.
    """
    safe_str = SafeString("test")
    
    s = {safe_str}
    
    if safe_str not in s:
        raise AssertionError("SafeString should be in set")
    
    # Should also match equivalent str
    if "test" not in s:
        raise AssertionError("Equivalent str should be in set")
    
    return


def test_safe_string_bool_true():
    """
        Test that non-empty SafeString is truthy.
    """
    safe_str = SafeString("test")
    
    if not safe_str:
        raise AssertionError("Non-empty SafeString should be truthy")
    
    return


def test_safe_string_bool_false():
    """
        Test that empty SafeString is falsy.
    """
    safe_str = SafeString("")
    
    if safe_str:
        raise AssertionError("Empty SafeString should be falsy")
    
    return


def test_multiple_safe_calls():
    """
        Test that calling safe() multiple times works.
    """
    value = "test"
    result1 = safe(value)
    result2 = safe(result1)
    
    if not isinstance(result2, SafeString):
        raise AssertionError("safe(safe(x)) should return SafeString")
    
    if result2 != value:
        raise AssertionError(f"Expected '{value}', got '{result2}'")
    
    return


def test_safe_string_format():
    """
        Test that format() works on SafeString.
    """
    safe_str = SafeString("Hello, {}!")
    
    result = safe_str.format("World")
    
    if result != "Hello, World!":
        raise AssertionError(f"Expected 'Hello, World!', got '{result}'")
    
    return


def test_safe_string_replace():
    """
        Test that replace() works on SafeString.
    """
    safe_str = SafeString("Hello, World!")
    
    result = safe_str.replace("World", "Python")
    
    if result != "Hello, Python!":
        raise AssertionError(f"Expected 'Hello, Python!', got '{result}'")
    
    return


def test_safe_string_join():
    """
        Test that join() works on SafeString.
    """
    safe_str = SafeString(", ")
    
    result = safe_str.join(["a", "b", "c"])
    
    if result != "a, b, c":
        raise AssertionError(f"Expected 'a, b, c', got '{result}'")
    
    return



# =============================================================================
# escape() Function Tests
# =============================================================================

from ccai.webworks.templating.escaping import escape, escape_json, escape_url


def test_escape_ampersand():
    """
        Test that escape() escapes ampersand.
    """
    result = escape("Tom & Jerry")
    
    if result != "Tom &amp; Jerry":
        raise AssertionError(f"Expected 'Tom &amp; Jerry', got '{result}'")
    
    return


def test_escape_less_than():
    """
        Test that escape() escapes less than.
    """
    result = escape("a < b")
    
    if result != "a &lt; b":
        raise AssertionError(f"Expected 'a &lt; b', got '{result}'")
    
    return


def test_escape_greater_than():
    """
        Test that escape() escapes greater than.
    """
    result = escape("a > b")
    
    if result != "a &gt; b":
        raise AssertionError(f"Expected 'a &gt; b', got '{result}'")
    
    return


def test_escape_double_quote():
    """
        Test that escape() escapes double quote.
    """
    result = escape('say "hello"')
    
    if result != "say &quot;hello&quot;":
        raise AssertionError(f"Expected 'say &quot;hello&quot;', got '{result}'")
    
    return


def test_escape_single_quote():
    """
        Test that escape() escapes single quote.
    """
    result = escape("it's")
    
    if result != "it&#39;s":
        raise AssertionError(f"Expected 'it&#39;s', got '{result}'")
    
    return


def test_escape_all_special_characters():
    """
        Test that escape() escapes all HTML special characters.
    """
    result = escape("<script>alert('xss' & \"test\")</script>")
    
    expected = "&lt;script&gt;alert(&#39;xss&#39; &amp; &quot;test&quot;)&lt;/script&gt;"
    if result != expected:
        raise AssertionError(f"Expected '{expected}', got '{result}'")
    
    return


def test_escape_empty_string():
    """
        Test that escape() handles empty string.
    """
    result = escape("")
    
    if result != "":
        raise AssertionError(f"Expected empty string, got '{result}'")
    
    return


def test_escape_no_special_characters():
    """
        Test that escape() returns unchanged string when no special characters.
    """
    value = "Hello World 123"
    result = escape(value)
    
    if result != value:
        raise AssertionError(f"Expected '{value}', got '{result}'")
    
    return


def test_escape_unicode():
    """
        Test that escape() preserves unicode characters.
    """
    result = escape("日本語 & 中文")
    
    if result != "日本語 &amp; 中文":
        raise AssertionError(f"Expected 'Japanese &amp; Chinese', got '{result}'")
    
    return


def test_escape_multiple_ampersands():
    """
        Test that escape() handles multiple ampersands.
    """
    result = escape("a & b & c")
    
    if result != "a &amp; b &amp; c":
        raise AssertionError(f"Expected 'a &amp; b &amp; c', got '{result}'")
    
    return


def test_escape_already_escaped():
    """
        Test that escape() escapes already-escaped content (double escaping).
    """
    # This is expected behavior - if content is already escaped,
    # it will be escaped again. Use SafeString to prevent this.
    result = escape("&amp;")
    
    if result != "&amp;amp;":
        raise AssertionError(f"Expected '&amp;amp;', got '{result}'")
    
    return


def test_escape_html_tag():
    """
        Test that escape() escapes HTML tags.
    """
    result = escape("<div class=\"test\">content</div>")
    
    expected = "&lt;div class=&quot;test&quot;&gt;content&lt;/div&gt;"
    if result != expected:
        raise AssertionError(f"Expected '{expected}', got '{result}'")
    
    return


def test_escape_script_tag():
    """
        Test that escape() escapes script tags (XSS prevention).
    """
    result = escape("<script>alert('xss')</script>")
    
    expected = "&lt;script&gt;alert(&#39;xss&#39;)&lt;/script&gt;"
    if result != expected:
        raise AssertionError(f"Expected '{expected}', got '{result}'")
    
    return


def test_escape_newlines_preserved():
    """
        Test that escape() preserves newlines.
    """
    result = escape("line1\nline2")
    
    if result != "line1\nline2":
        raise AssertionError(f"Expected 'line1\\nline2', got '{result}'")
    
    return


def test_escape_whitespace_preserved():
    """
        Test that escape() preserves whitespace.
    """
    result = escape("  spaces  \ttab")
    
    if result != "  spaces  \ttab":
        raise AssertionError(f"Expected '  spaces  \\ttab', got '{result}'")
    
    return


# =============================================================================
# escape_json() Function Tests
# =============================================================================

def test_escape_json_string():
    """
        Test that escape_json() escapes a string.
    """
    result = escape_json("hello")
    
    if result != '"hello"':
        raise AssertionError(f"Expected '\"hello\"', got '{result}'")
    
    return


def test_escape_json_number():
    """
        Test that escape_json() handles numbers.
    """
    result = escape_json(42)
    
    if result != "42":
        raise AssertionError(f"Expected '42', got '{result}'")
    
    return


def test_escape_json_float():
    """
        Test that escape_json() handles floats.
    """
    result = escape_json(3.14)
    
    if result != "3.14":
        raise AssertionError(f"Expected '3.14', got '{result}'")
    
    return


def test_escape_json_boolean_true():
    """
        Test that escape_json() handles True.
    """
    result = escape_json(True)
    
    if result != "true":
        raise AssertionError(f"Expected 'true', got '{result}'")
    
    return


def test_escape_json_boolean_false():
    """
        Test that escape_json() handles False.
    """
    result = escape_json(False)
    
    if result != "false":
        raise AssertionError(f"Expected 'false', got '{result}'")
    
    return


def test_escape_json_null():
    """
        Test that escape_json() handles None.
    """
    result = escape_json(None)
    
    if result != "null":
        raise AssertionError(f"Expected 'null', got '{result}'")
    
    return


def test_escape_json_list():
    """
        Test that escape_json() handles lists.
    """
    result = escape_json([1, 2, 3])
    
    if result != "[1, 2, 3]":
        raise AssertionError(f"Expected '[1, 2, 3]', got '{result}'")
    
    return


def test_escape_json_dict():
    """
        Test that escape_json() handles dicts.
    """
    result = escape_json({"key": "value"})
    
    if result != '{"key": "value"}':
        raise AssertionError(f"Expected '{{\"key\": \"value\"}}', got '{result}'")
    
    return


def test_escape_json_less_than():
    """
        Test that escape_json() escapes less than for script safety.
    """
    result = escape_json("<script>")
    
    if "\\u003c" not in result:
        raise AssertionError(f"Expected '\\u003c' in result, got '{result}'")
    
    return


def test_escape_json_greater_than():
    """
        Test that escape_json() escapes greater than for script safety.
    """
    result = escape_json("</script>")
    
    if "\\u003e" not in result:
        raise AssertionError(f"Expected '\\u003e' in result, got '{result}'")
    
    return


def test_escape_json_ampersand():
    """
        Test that escape_json() escapes ampersand for HTML safety.
    """
    result = escape_json("a & b")
    
    if "\\u0026" not in result:
        raise AssertionError(f"Expected '\\u0026' in result, got '{result}'")
    
    return


def test_escape_json_script_injection():
    """
        Test that escape_json() prevents script injection.
    """
    result = escape_json("</script><script>alert('xss')</script>")
    
    # Should not contain literal </script>
    if "</script>" in result:
        raise AssertionError("Result should not contain literal '</script>'")
    
    return


def test_escape_json_nested_structure():
    """
        Test that escape_json() handles nested structures.
    """
    data = {
        "name": "<script>",
        "items": ["a & b", "c < d"],
        "nested": {"key": ">value"}
    }
    result = escape_json(data)
    
    # Should not contain literal < > &
    if "<" in result or ">" in result:
        raise AssertionError("Result should not contain literal < or >")
    
    return


def test_escape_json_unicode():
    """
        Test that escape_json() handles unicode.
    """
    result = escape_json("日本語")
    
    # Should be valid JSON
    if not result.startswith('"') or not result.endswith('"'):
        raise AssertionError(f"Expected quoted string, got '{result}'")
    
    return


def test_escape_json_empty_string():
    """
        Test that escape_json() handles empty string.
    """
    result = escape_json("")
    
    if result != '""':
        raise AssertionError(f"Expected '\"\"', got '{result}'")
    
    return


def test_escape_json_empty_list():
    """
        Test that escape_json() handles empty list.
    """
    result = escape_json([])
    
    if result != "[]":
        raise AssertionError(f"Expected '[]', got '{result}'")
    
    return


def test_escape_json_empty_dict():
    """
        Test that escape_json() handles empty dict.
    """
    result = escape_json({})
    
    if result != "{}":
        raise AssertionError(f"Expected '{{}}', got '{result}'")
    
    return


# =============================================================================
# escape_url() Function Tests
# =============================================================================

def test_escape_url_space():
    """
        Test that escape_url() encodes spaces.
    """
    result = escape_url("hello world")
    
    if result != "hello%20world":
        raise AssertionError(f"Expected 'hello%20world', got '{result}'")
    
    return


def test_escape_url_ampersand():
    """
        Test that escape_url() encodes ampersand.
    """
    result = escape_url("a&b")
    
    if result != "a%26b":
        raise AssertionError(f"Expected 'a%26b', got '{result}'")
    
    return


def test_escape_url_equals():
    """
        Test that escape_url() encodes equals sign.
    """
    result = escape_url("a=b")
    
    if result != "a%3Db":
        raise AssertionError(f"Expected 'a%3Db', got '{result}'")
    
    return


def test_escape_url_question_mark():
    """
        Test that escape_url() encodes question mark.
    """
    result = escape_url("a?b")
    
    if result != "a%3Fb":
        raise AssertionError(f"Expected 'a%3Fb', got '{result}'")
    
    return


def test_escape_url_hash():
    """
        Test that escape_url() encodes hash.
    """
    result = escape_url("a#b")
    
    if result != "a%23b":
        raise AssertionError(f"Expected 'a%23b', got '{result}'")
    
    return


def test_escape_url_slash():
    """
        Test that escape_url() encodes slash.
    """
    result = escape_url("a/b")
    
    if result != "a%2Fb":
        raise AssertionError(f"Expected 'a%2Fb', got '{result}'")
    
    return


def test_escape_url_unicode():
    """
        Test that escape_url() encodes unicode characters.
    """
    result = escape_url("日本語")
    
    # Japanese characters should be percent-encoded
    if result != "%E6%97%A5%E6%9C%AC%E8%AA%9E":
        raise AssertionError(f"Expected '%E6%97%A5%E6%9C%AC%E8%AA%9E', got '{result}'")
    
    return


def test_escape_url_empty_string():
    """
        Test that escape_url() handles empty string.
    """
    result = escape_url("")
    
    if result != "":
        raise AssertionError(f"Expected empty string, got '{result}'")
    
    return


def test_escape_url_alphanumeric():
    """
        Test that escape_url() preserves alphanumeric characters.
    """
    result = escape_url("abc123XYZ")
    
    if result != "abc123XYZ":
        raise AssertionError(f"Expected 'abc123XYZ', got '{result}'")
    
    return


def test_escape_url_hyphen():
    """
        Test that escape_url() preserves hyphen.
    """
    result = escape_url("a-b")
    
    if result != "a-b":
        raise AssertionError(f"Expected 'a-b', got '{result}'")
    
    return


def test_escape_url_underscore():
    """
        Test that escape_url() preserves underscore.
    """
    result = escape_url("a_b")
    
    if result != "a_b":
        raise AssertionError(f"Expected 'a_b', got '{result}'")
    
    return


def test_escape_url_period():
    """
        Test that escape_url() preserves period.
    """
    result = escape_url("a.b")
    
    if result != "a.b":
        raise AssertionError(f"Expected 'a.b', got '{result}'")
    
    return


def test_escape_url_tilde():
    """
        Test that escape_url() preserves tilde.
    """
    result = escape_url("a~b")
    
    if result != "a~b":
        raise AssertionError(f"Expected 'a~b', got '{result}'")
    
    return


def test_escape_url_query_string():
    """
        Test that escape_url() encodes a full query string.
    """
    result = escape_url("name=value&other=test")
    
    if result != "name%3Dvalue%26other%3Dtest":
        raise AssertionError(f"Expected 'name%3Dvalue%26other%3Dtest', got '{result}'")
    
    return


def test_escape_url_special_characters():
    """
        Test that escape_url() encodes various special characters.
    """
    result = escape_url("!@#$%^&*()")
    
    # All these should be encoded
    if "!" in result or "@" in result or "#" in result:
        raise AssertionError(f"Special characters should be encoded, got '{result}'")
    
    return


def test_escape_url_plus():
    """
        Test that escape_url() encodes plus sign.
    """
    result = escape_url("a+b")
    
    if result != "a%2Bb":
        raise AssertionError(f"Expected 'a%2Bb', got '{result}'")
    
    return


def test_escape_url_percent():
    """
        Test that escape_url() encodes percent sign.
    """
    result = escape_url("100%")
    
    if result != "100%25":
        raise AssertionError(f"Expected '100%25', got '{result}'")
    
    return


def test_escape_url_emoji():
    """
        Test that escape_url() encodes emoji.
    """
    result = escape_url("🎉")
    
    # Emoji should be percent-encoded
    if not result.startswith("%"):
        raise AssertionError(f"Emoji should be encoded, got '{result}'")
    
    return


# =============================================================================
# Property-Based Tests
# =============================================================================

import random
import string


# HTML special characters and their escaped equivalents
_HTML_SPECIAL_CHARS = {
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
}


def _generate_random_string(length: int = 20) -> str:
    """
        Generate a random string for property testing.

        :param length: Length of the random string.

        :returns: Random string containing various characters.
    """
    # Include alphanumeric, whitespace, and some safe special chars
    chars = string.ascii_letters + string.digits + " \t\n"
    return "".join(random.choice(chars) for _ in range(length))


def _generate_string_with_html_chars(min_special: int = 1, max_special: int = 10) -> str:
    """
        Generate a random string containing HTML special characters.

        :param min_special: Minimum number of special characters to include.
        :param max_special: Maximum number of special characters to include.

        :returns: Random string containing HTML special characters.
    """
    # Generate base random content
    base_length = random.randint(5, 50)
    base_chars = string.ascii_letters + string.digits + " \t"
    base = list("".join(random.choice(base_chars) for _ in range(base_length)))

    # Insert random HTML special characters at random positions
    special_chars = list(_HTML_SPECIAL_CHARS.keys())
    num_special = random.randint(min_special, max_special)

    for _ in range(num_special):
        char = random.choice(special_chars)
        pos = random.randint(0, len(base))
        base.insert(pos, char)

    return "".join(base)


def _generate_string_with_specific_char(char: str, count: int = None) -> str:
    """
        Generate a random string containing a specific HTML special character.

        :param char: The HTML special character to include.
        :param count: Number of times to include the character (random if None).

        :returns: Random string containing the specified character.
    """
    if count is None:
        count = random.randint(1, 5)

    # Generate base random content
    base_length = random.randint(5, 30)
    base_chars = string.ascii_letters + string.digits + " "
    base = list("".join(random.choice(base_chars) for _ in range(base_length)))

    # Insert the specific character at random positions
    for _ in range(count):
        pos = random.randint(0, len(base))
        base.insert(pos, char)

    return "".join(base)


def test_property_auto_escaping_correctness():
    """
        Property test for auto-escaping correctness.

        **Property 2: Auto-Escaping Correctness**

        *For any* string containing HTML special characters (&, <, >, ", '),
        when auto-escaping is enabled, the rendered output SHALL contain the
        escaped equivalents (&amp;, &lt;, &gt;, &quot;, &#39;) unless the
        string is marked as safe.

        **Validates: Requirements 5.1, 5.2, 5.6**

        This property test verifies that:
        1. For any string containing HTML special characters, escape() produces
           output with escaped equivalents
        2. Each HTML special character (&, <, >, ", ') is correctly escaped
        3. Non-special characters are preserved unchanged

        Test strategy:
        - Generate random strings containing HTML special characters
        - Apply escape() function
        - Verify all special characters are escaped to their equivalents
        - Verify non-special characters remain unchanged
    """
    iterations = 100

    for iteration in range(iterations):
        # Generate a random string with HTML special characters
        input_str = _generate_string_with_html_chars()

        # Apply escape function
        result = escape(input_str)

        # Verify all HTML special characters are escaped
        for char, escaped in _HTML_SPECIAL_CHARS.items():
            # Count occurrences in input
            input_count = input_str.count(char)

            if input_count > 0:
                # The escaped version should appear in the result
                result_count = result.count(escaped)

                # Account for ampersand being part of other escapes
                # When we escape &, it becomes &amp;
                # When we escape <, it becomes &lt; (contains &)
                # So we need to be careful about counting
                if char == "&":
                    # For ampersand, we need to count &amp; specifically
                    # and not count the & in &lt;, &gt;, &quot;, &#39;
                    # The result should have exactly input_count occurrences of &amp;
                    # plus any & that were part of the original escaped sequences
                    pass  # Complex case handled by direct verification below
                else:
                    if result_count < input_count:
                        raise AssertionError(
                            f"Iteration {iteration}: Expected at least {input_count} "
                            f"occurrences of '{escaped}' for '{char}', but found "
                            f"{result_count}. Input: {input_str!r}, Result: {result!r}"
                        )

        # Verify no unescaped special characters remain (except in escape sequences)
        # Check that literal special chars don't appear outside of escape sequences
        for char in _HTML_SPECIAL_CHARS.keys():
            if char == "&":
                # Ampersand is special - it appears in all escape sequences
                # We need to verify all & are part of valid escape sequences
                # Find all & positions and verify they're part of escapes
                pos = 0
                while pos < len(result):
                    amp_pos = result.find("&", pos)
                    if amp_pos == -1:
                        break

                    # Check if this & is part of a valid escape sequence
                    remaining = result[amp_pos:]
                    valid_escape = False
                    for escaped_seq in _HTML_SPECIAL_CHARS.values():
                        if remaining.startswith(escaped_seq):
                            valid_escape = True
                            break

                    if not valid_escape:
                        raise AssertionError(
                            f"Iteration {iteration}: Found unescaped '&' at position "
                            f"{amp_pos}. Input: {input_str!r}, Result: {result!r}"
                        )

                    pos = amp_pos + 1
            else:
                # For other special chars, they should not appear literally
                if char in result:
                    raise AssertionError(
                        f"Iteration {iteration}: Found unescaped '{char}' in result. "
                        f"Input: {input_str!r}, Result: {result!r}"
                    )

    return


def test_property_auto_escaping_each_special_char():
    """
        Property test for auto-escaping of each individual special character.

        **Property 2: Auto-Escaping Correctness** (individual characters)

        *For any* string containing a specific HTML special character,
        escape() SHALL correctly escape that character to its equivalent.

        **Validates: Requirements 5.1, 5.2, 5.6**

        This property test verifies that each HTML special character is
        correctly escaped when it appears in isolation or with other content.
    """
    iterations = 100

    for iteration in range(iterations):
        # Test each special character individually
        for char, escaped in _HTML_SPECIAL_CHARS.items():
            # Generate a string with this specific character
            input_str = _generate_string_with_specific_char(char)

            # Apply escape function
            result = escape(input_str)

            # Count occurrences
            input_count = input_str.count(char)

            # Verify the character is escaped
            if char == "&":
                # For ampersand, count &amp; occurrences
                result_count = result.count("&amp;")
                if result_count != input_count:
                    raise AssertionError(
                        f"Iteration {iteration}: Expected {input_count} '&amp;' "
                        f"for {input_count} '&', but found {result_count}. "
                        f"Input: {input_str!r}, Result: {result!r}"
                    )
            else:
                # For other chars, verify they don't appear literally
                if char in result:
                    raise AssertionError(
                        f"Iteration {iteration}: Found unescaped '{char}' in result. "
                        f"Input: {input_str!r}, Result: {result!r}"
                    )

                # Verify escaped version appears
                result_count = result.count(escaped)
                if result_count < input_count:
                    raise AssertionError(
                        f"Iteration {iteration}: Expected at least {input_count} "
                        f"'{escaped}' for '{char}', but found {result_count}. "
                        f"Input: {input_str!r}, Result: {result!r}"
                    )

    return


def test_property_auto_escaping_preserves_non_special_chars():
    """
        Property test verifying non-special characters are preserved.

        **Property 2: Auto-Escaping Correctness** (preservation)

        *For any* string, characters that are not HTML special characters
        SHALL be preserved unchanged in the escaped output.

        **Validates: Requirements 5.1, 5.2, 5.6**

        This property test verifies that escape() only modifies HTML special
        characters and leaves all other content unchanged.
    """
    iterations = 100

    for iteration in range(iterations):
        # Generate a string without any HTML special characters
        input_str = _generate_random_string()

        # Apply escape function
        result = escape(input_str)

        # Result should be identical to input (no special chars to escape)
        if result != input_str:
            raise AssertionError(
                f"Iteration {iteration}: String without special characters "
                f"should be unchanged. Input: {input_str!r}, Result: {result!r}"
            )

    return


def test_property_auto_escaping_with_mixed_content():
    """
        Property test for auto-escaping with mixed content.

        **Property 2: Auto-Escaping Correctness** (mixed content)

        *For any* string containing both HTML special characters and regular
        content, escape() SHALL escape only the special characters while
        preserving the regular content.

        **Validates: Requirements 5.1, 5.2, 5.6**

        This property test verifies that escape() correctly handles strings
        with a mix of special and non-special characters.
    """
    iterations = 100

    for iteration in range(iterations):
        # Generate a string with HTML special characters
        input_str = _generate_string_with_html_chars()

        # Apply escape function
        result = escape(input_str)

        # Manually compute expected result
        expected = input_str
        for char, escaped in _HTML_SPECIAL_CHARS.items():
            expected = expected.replace(char, escaped)

        if result != expected:
            raise AssertionError(
                f"Iteration {iteration}: Escape result doesn't match expected. "
                f"Input: {input_str!r}, Expected: {expected!r}, Got: {result!r}"
            )

    return


def test_property_auto_escaping_idempotent_safety():
    """
        Property test for escape function behavior with already-escaped content.

        **Property 2: Auto-Escaping Correctness** (double escaping)

        *For any* string that has already been escaped, applying escape()
        again SHALL escape the ampersands in the escape sequences, producing
        predictable double-escaped output.

        **Validates: Requirements 5.1, 5.2, 5.6**

        This property test verifies that escape() behaves predictably when
        applied to already-escaped content (double escaping).
    """
    iterations = 100

    for iteration in range(iterations):
        # Generate a string with HTML special characters
        input_str = _generate_string_with_html_chars()

        # Apply escape function twice
        first_escape = escape(input_str)
        second_escape = escape(first_escape)

        # The second escape should escape the & in the escape sequences
        # For example: &lt; becomes &amp;lt;
        expected = first_escape
        for char, escaped in _HTML_SPECIAL_CHARS.items():
            expected = expected.replace(char, escaped)

        if second_escape != expected:
            raise AssertionError(
                f"Iteration {iteration}: Double escape result doesn't match expected. "
                f"Input: {input_str!r}, First: {first_escape!r}, "
                f"Expected: {expected!r}, Got: {second_escape!r}"
            )

    return


def test_property_auto_escaping_all_chars_at_once():
    """
        Property test for auto-escaping when all special characters appear together.

        **Property 2: Auto-Escaping Correctness** (all characters)

        *For any* string containing all five HTML special characters,
        escape() SHALL correctly escape all of them simultaneously.

        **Validates: Requirements 5.1, 5.2, 5.6**

        This property test verifies that escape() handles strings containing
        all HTML special characters at once.
    """
    iterations = 100

    for iteration in range(iterations):
        # Generate base content
        base_chars = string.ascii_letters + string.digits + " "
        parts = ["".join(random.choice(base_chars) for _ in range(random.randint(1, 5)))
                 for _ in range(6)]

        # Insert all special characters
        special_chars = list(_HTML_SPECIAL_CHARS.keys())
        random.shuffle(special_chars)

        # Build string with all special chars interspersed
        input_str = ""
        for i, char in enumerate(special_chars):
            input_str += parts[i] + char
        input_str += parts[-1]

        # Apply escape function
        result = escape(input_str)

        # Verify all special characters are escaped
        for char in _HTML_SPECIAL_CHARS.keys():
            if char == "&":
                continue  # Ampersand appears in escape sequences
            if char in result:
                raise AssertionError(
                    f"Iteration {iteration}: Found unescaped '{char}' in result. "
                    f"Input: {input_str!r}, Result: {result!r}"
                )

        # Verify expected result
        expected = input_str
        for char, escaped in _HTML_SPECIAL_CHARS.items():
            expected = expected.replace(char, escaped)

        if result != expected:
            raise AssertionError(
                f"Iteration {iteration}: Result doesn't match expected. "
                f"Input: {input_str!r}, Expected: {expected!r}, Got: {result!r}"
            )

    return



# =============================================================================
# Property 3: Safe String Bypass Property Tests
# =============================================================================


def _generate_string_with_html_special_chars(min_length: int = 5, max_length: int = 50) -> str:
    """
        Generate a random string containing HTML special characters.

        This generator creates strings that would normally be escaped by
        auto-escaping, making them ideal for testing safe string bypass.

        :param min_length: Minimum length of the generated string.
        :param max_length: Maximum length of the generated string.

        :returns: Random string containing HTML special characters.
    """
    # Characters to include: alphanumeric, whitespace, and HTML special chars
    safe_chars = string.ascii_letters + string.digits + " \t\n"
    html_special = "&<>\"'"

    length = random.randint(min_length, max_length)
    result = []

    for _ in range(length):
        # 30% chance of HTML special character to ensure good coverage
        if random.random() < 0.3:
            result.append(random.choice(html_special))
        else:
            result.append(random.choice(safe_chars))

    return "".join(result)


def _generate_html_content() -> str:
    """
        Generate random HTML-like content for testing safe string bypass.

        This generator creates strings that look like HTML markup, which
        would be escaped by auto-escaping but should be preserved by SafeString.

        :returns: Random HTML-like content string.
    """
    tags = ["div", "span", "p", "strong", "em", "a", "script", "style"]
    attributes = ["class", "id", "href", "onclick", "style"]

    tag = random.choice(tags)
    attr = random.choice(attributes)
    attr_value = _generate_random_string(random.randint(3, 10))
    content = _generate_random_string(random.randint(5, 20))

    # Generate various HTML patterns
    patterns = [
        f"<{tag}>{content}</{tag}>",
        f"<{tag} {attr}=\"{attr_value}\">{content}</{tag}>",
        f"<{tag} {attr}='{attr_value}'>{content}</{tag}>",
        f"<{tag}></{tag}>",
        f"<{tag} />",
        f"<!-- {content} -->",
        f"&amp; &lt; &gt; &quot; &#39;",  # Pre-escaped content
        f"<script>alert('{content}')</script>",
        f"<a href=\"javascript:void(0)\">{content}</a>",
    ]

    return random.choice(patterns)


def test_property_safe_string_bypass_preserves_content():
    """
        Property test for safe string bypass content preservation.

        **Property 3: Safe String Bypass**

        *For any* string marked as safe via the safe() function or SafeString
        class, the rendered output SHALL contain the original unescaped content
        regardless of auto-escaping settings.

        **Validates: Requirements 5.3, 5.7**

        This property test verifies that:
        1. SafeString instances preserve their original content exactly
        2. HTML special characters are NOT escaped in SafeString
        3. The string value is identical to the original input

        Test strategy:
        - Generate random strings containing HTML special characters
        - Create SafeString instances
        - Verify the content is preserved exactly without modification
    """
    iterations = 100

    for iteration in range(iterations):
        # Generate a string with HTML special characters
        original = _generate_string_with_html_special_chars()

        # Create SafeString directly
        safe_str = SafeString(original)

        # Verify content is preserved exactly
        if str(safe_str) != original:
            raise AssertionError(
                f"Iteration {iteration}: SafeString content not preserved. "
                f"Original: {original!r}, SafeString: {str(safe_str)!r}"
            )

        # Verify equality with original
        if safe_str != original:
            raise AssertionError(
                f"Iteration {iteration}: SafeString should equal original. "
                f"Original: {original!r}, SafeString: {safe_str!r}"
            )

        # Verify length is preserved
        if len(safe_str) != len(original):
            raise AssertionError(
                f"Iteration {iteration}: SafeString length not preserved. "
                f"Original length: {len(original)}, SafeString length: {len(safe_str)}"
            )

    return


def test_property_safe_function_bypass_preserves_content():
    """
        Property test for safe() function content preservation.

        **Property 3: Safe String Bypass**

        *For any* string marked as safe via the safe() function, the result
        SHALL contain the original unescaped content.

        **Validates: Requirements 5.3, 5.7**

        This property test verifies that the safe() function creates SafeString
        instances that preserve the original content exactly.
    """
    iterations = 100

    for iteration in range(iterations):
        # Generate a string with HTML special characters
        original = _generate_string_with_html_special_chars()

        # Use safe() function
        safe_str = safe(original)

        # Verify it returns a SafeString
        if not isinstance(safe_str, SafeString):
            raise AssertionError(
                f"Iteration {iteration}: safe() should return SafeString. "
                f"Got: {type(safe_str).__name__}"
            )

        # Verify content is preserved exactly
        if str(safe_str) != original:
            raise AssertionError(
                f"Iteration {iteration}: safe() content not preserved. "
                f"Original: {original!r}, Result: {str(safe_str)!r}"
            )

        # Verify equality with original
        if safe_str != original:
            raise AssertionError(
                f"Iteration {iteration}: safe() result should equal original. "
                f"Original: {original!r}, Result: {safe_str!r}"
            )

    return


def test_property_safe_string_html_method_returns_original():
    """
        Property test for SafeString __html__() method.

        **Property 3: Safe String Bypass**

        *For any* SafeString instance, the __html__() method SHALL return
        the original unescaped content.

        **Validates: Requirements 5.3, 5.7**

        This property test verifies that the __html__() method (used by
        template engines for auto-escaping detection) returns the original
        content without any modification.
    """
    iterations = 100

    for iteration in range(iterations):
        # Generate a string with HTML special characters
        original = _generate_string_with_html_special_chars()

        # Create SafeString
        safe_str = SafeString(original)

        # Call __html__() method
        html_result = safe_str.__html__()

        # Verify __html__() returns the original content
        if html_result != original:
            raise AssertionError(
                f"Iteration {iteration}: __html__() should return original content. "
                f"Original: {original!r}, __html__(): {html_result!r}"
            )

        # Verify __html__() returns self (same object)
        if html_result is not safe_str:
            raise AssertionError(
                f"Iteration {iteration}: __html__() should return self. "
                f"SafeString id: {id(safe_str)}, __html__() id: {id(html_result)}"
            )

    return


def test_property_safe_string_bypass_with_html_content():
    """
        Property test for safe string bypass with HTML markup.

        **Property 3: Safe String Bypass**

        *For any* HTML markup string marked as safe, the content SHALL be
        preserved exactly without escaping HTML tags or attributes.

        **Validates: Requirements 5.3, 5.7**

        This property test verifies that SafeString correctly preserves
        HTML markup that would normally be escaped.
    """
    iterations = 100

    for iteration in range(iterations):
        # Generate HTML-like content
        html_content = _generate_html_content()

        # Create SafeString
        safe_str = SafeString(html_content)

        # Verify HTML content is preserved exactly
        if str(safe_str) != html_content:
            raise AssertionError(
                f"Iteration {iteration}: HTML content not preserved. "
                f"Original: {html_content!r}, SafeString: {str(safe_str)!r}"
            )

        # Verify __html__() returns the HTML content
        if safe_str.__html__() != html_content:
            raise AssertionError(
                f"Iteration {iteration}: __html__() should return HTML content. "
                f"Original: {html_content!r}, __html__(): {safe_str.__html__()!r}"
            )

        # Verify HTML special characters are NOT escaped
        # If original has <, the SafeString should still have <, not &lt;
        if "<" in html_content:
            if "&lt;" in str(safe_str) and "<" not in str(safe_str):
                raise AssertionError(
                    f"Iteration {iteration}: SafeString should not escape '<'. "
                    f"Original: {html_content!r}, SafeString: {str(safe_str)!r}"
                )

        if ">" in html_content:
            if "&gt;" in str(safe_str) and ">" not in str(safe_str):
                raise AssertionError(
                    f"Iteration {iteration}: SafeString should not escape '>'. "
                    f"Original: {html_content!r}, SafeString: {str(safe_str)!r}"
                )

    return


def test_property_safe_string_concatenation_preserves_safety():
    """
        Property test for SafeString concatenation preserving content.

        **Property 3: Safe String Bypass**

        *For any* SafeString concatenated with other strings, the resulting
        SafeString SHALL preserve all original content without escaping.

        **Validates: Requirements 5.3, 5.7**

        This property test verifies that concatenation operations on SafeString
        preserve the safe status and content.
    """
    iterations = 100

    for iteration in range(iterations):
        # Generate strings with HTML special characters
        str1 = _generate_string_with_html_special_chars(5, 20)
        str2 = _generate_string_with_html_special_chars(5, 20)

        # Create SafeString and concatenate
        safe_str = SafeString(str1)
        result = safe_str + str2

        # Verify result is SafeString
        if not isinstance(result, SafeString):
            raise AssertionError(
                f"Iteration {iteration}: Concatenation should return SafeString. "
                f"Got: {type(result).__name__}"
            )

        # Verify content is preserved
        expected = str1 + str2
        if str(result) != expected:
            raise AssertionError(
                f"Iteration {iteration}: Concatenation content not preserved. "
                f"Expected: {expected!r}, Got: {str(result)!r}"
            )

        # Test reverse concatenation (str + SafeString)
        result_reverse = str2 + safe_str

        if not isinstance(result_reverse, SafeString):
            raise AssertionError(
                f"Iteration {iteration}: Reverse concatenation should return SafeString. "
                f"Got: {type(result_reverse).__name__}"
            )

        expected_reverse = str2 + str1
        if str(result_reverse) != expected_reverse:
            raise AssertionError(
                f"Iteration {iteration}: Reverse concatenation content not preserved. "
                f"Expected: {expected_reverse!r}, Got: {str(result_reverse)!r}"
            )

    return


def test_property_safe_string_access_preserves_content():
    """
        Property test for SafeString content access preservation.

        **Property 3: Safe String Bypass**

        *For any* SafeString instance, accessing the content through various
        string operations SHALL preserve the original unescaped content.

        **Validates: Requirements 5.3, 5.7**

        This property test verifies that SafeString content is not modified
        when accessed through indexing, slicing, or iteration.
    """
    iterations = 100

    for iteration in range(iterations):
        # Generate a string with HTML special characters
        original = _generate_string_with_html_special_chars(10, 30)

        # Create SafeString
        safe_str = SafeString(original)

        # Test indexing preserves characters
        for i in range(len(original)):
            if safe_str[i] != original[i]:
                raise AssertionError(
                    f"Iteration {iteration}: Indexing should preserve character. "
                    f"Position {i}: Expected {original[i]!r}, Got {safe_str[i]!r}"
                )

        # Test slicing preserves content
        if len(original) >= 5:
            slice_result = safe_str[2:7]
            expected_slice = original[2:7]
            if slice_result != expected_slice:
                raise AssertionError(
                    f"Iteration {iteration}: Slicing should preserve content. "
                    f"Expected: {expected_slice!r}, Got: {slice_result!r}"
                )

        # Test iteration preserves characters
        iterated = "".join(safe_str)
        if iterated != original:
            raise AssertionError(
                f"Iteration {iteration}: Iteration should preserve content. "
                f"Original: {original!r}, Iterated: {iterated!r}"
            )

    return


def test_property_safe_string_multiple_safe_calls():
    """
        Property test for multiple safe() calls preserving content.

        **Property 3: Safe String Bypass**

        *For any* string, calling safe() multiple times SHALL preserve
        the original content without modification.

        **Validates: Requirements 5.3, 5.7**

        This property test verifies that safe() is idempotent with respect
        to content preservation.
    """
    iterations = 100

    for iteration in range(iterations):
        # Generate a string with HTML special characters
        original = _generate_string_with_html_special_chars()

        # Call safe() multiple times
        safe1 = safe(original)
        safe2 = safe(safe1)
        safe3 = safe(safe2)

        # All should be SafeString
        if not isinstance(safe1, SafeString):
            raise AssertionError(
                f"Iteration {iteration}: safe() should return SafeString"
            )
        if not isinstance(safe2, SafeString):
            raise AssertionError(
                f"Iteration {iteration}: safe(safe()) should return SafeString"
            )
        if not isinstance(safe3, SafeString):
            raise AssertionError(
                f"Iteration {iteration}: safe(safe(safe())) should return SafeString"
            )

        # All should preserve original content
        if str(safe1) != original:
            raise AssertionError(
                f"Iteration {iteration}: safe() should preserve content. "
                f"Original: {original!r}, safe(): {str(safe1)!r}"
            )
        if str(safe2) != original:
            raise AssertionError(
                f"Iteration {iteration}: safe(safe()) should preserve content. "
                f"Original: {original!r}, safe(safe()): {str(safe2)!r}"
            )
        if str(safe3) != original:
            raise AssertionError(
                f"Iteration {iteration}: safe(safe(safe())) should preserve content. "
                f"Original: {original!r}, safe(safe(safe())): {str(safe3)!r}"
            )

    return


def test_property_safe_string_bypass_all_html_special_chars():
    """
        Property test for safe string bypass with all HTML special characters.

        **Property 3: Safe String Bypass**

        *For any* string containing all five HTML special characters (&, <, >, ", '),
        marking it as safe SHALL preserve all characters without escaping.

        **Validates: Requirements 5.3, 5.7**

        This property test verifies that SafeString correctly preserves all
        HTML special characters that would normally be escaped.
    """
    iterations = 100

    for iteration in range(iterations):
        # Generate base content
        base_chars = string.ascii_letters + string.digits + " "
        parts = ["".join(random.choice(base_chars) for _ in range(random.randint(1, 5)))
                 for _ in range(6)]

        # Build string with all special chars
        special_chars = ["&", "<", ">", '"', "'"]
        random.shuffle(special_chars)

        original = ""
        for i, char in enumerate(special_chars):
            original += parts[i] + char
        original += parts[-1]

        # Create SafeString
        safe_str = SafeString(original)

        # Verify all special characters are preserved (not escaped)
        for char in special_chars:
            if char not in str(safe_str):
                raise AssertionError(
                    f"Iteration {iteration}: SafeString should preserve '{char}'. "
                    f"Original: {original!r}, SafeString: {str(safe_str)!r}"
                )

        # Verify no escape sequences were introduced
        escape_sequences = ["&amp;", "&lt;", "&gt;", "&quot;", "&#39;"]
        for seq in escape_sequences:
            # Only check if the sequence wasn't in the original
            if seq not in original and seq in str(safe_str):
                raise AssertionError(
                    f"Iteration {iteration}: SafeString should not introduce '{seq}'. "
                    f"Original: {original!r}, SafeString: {str(safe_str)!r}"
                )

        # Verify exact content preservation
        if str(safe_str) != original:
            raise AssertionError(
                f"Iteration {iteration}: SafeString content not preserved. "
                f"Original: {original!r}, SafeString: {str(safe_str)!r}"
            )

    return
