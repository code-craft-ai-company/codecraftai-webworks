"""
    Auto-escaping utilities for web templating.
    
    This module provides utilities for marking strings as safe (bypassing
    auto-escaping) and for escaping HTML special characters. These utilities
    are essential for preventing XSS attacks while allowing trusted content
    to be rendered without escaping.
    
    The SafeString class is compatible with Jinja2's Markup interface,
    implementing the __html__() method for seamless integration.
"""

import json
from typing import Any, Union
from urllib.parse import quote as url_quote


# HTML special character escape mappings
# These characters have special meaning in HTML and must be escaped
# to prevent XSS attacks and ensure proper rendering.
_HTML_ESCAPE_MAP = {
    "&": "&amp;",   # Must be first to avoid double-escaping
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
}


class SafeString(str):
    """
        A string marked as safe that bypasses auto-escaping.
        
        SafeString is a subclass of str that indicates the content has been
        verified as safe and should not be escaped during template rendering.
        This is useful for pre-escaped HTML content or trusted markup.
        
        The class implements the __html__() method for compatibility with
        Jinja2's Markup interface and other template engines that use this
        protocol for auto-escaping detection.
        
        Example usage::
        
            # Create a safe string directly
            safe_html = SafeString("<strong>Bold text</strong>")
            
            # Or use the safe() function
            safe_html = safe("<strong>Bold text</strong>")
            
            # In templates, safe strings bypass auto-escaping
            # {{ safe_html }} renders as: <strong>Bold text</strong>
            # {{ unsafe_html }} renders as: &lt;strong&gt;Bold text&lt;/strong&gt;
    """
    
    def __html__(self) -> str:
        """
            Return self for Jinja2 Markup compatibility.
            
            This method is part of the __html__ protocol used by Jinja2 and
            other template engines to detect strings that should not be
            auto-escaped. When a template engine encounters an object with
            an __html__() method, it calls this method and uses the result
            without escaping.
            
            :returns: The string value (self).
        """
        return self
    
    def __repr__(self) -> str:
        """
            Return a representation of the SafeString.
            
            :returns: String representation showing this is a SafeString.
        """
        return f"SafeString({super().__repr__()})"
    
    def __add__(self, other: Union[str, "SafeString"]) -> "SafeString":
        """
            Concatenate with another string, escaping it unless it is safe.
            
            The result is a SafeString, so only content that is known to be
            safe may go into it unchanged. An operand that implements the
            ``__html__`` protocol (another SafeString, a Jinja2 Markup) is
            appended as it is; any other string is HTML-escaped first. This
            is what ``markupsafe.Markup`` does, and it is what keeps
            ``safe("<b>") + user_input + safe("</b>")`` from emitting the
            user input verbatim.
            
            :param other: String to append.
            
            :returns: New SafeString with the concatenated content, or
                NotImplemented when ``other`` is not a string.
        """
        result = NotImplemented
        
        if isinstance(other, str) or hasattr(other, "__html__"):
            other_markup = _to_safe_markup(other)
            result = SafeString(super().__add__(other_markup))
        
        return result
    
    def __radd__(self, other: Union[str, "SafeString"]) -> "SafeString":
        """
            Concatenate with another string (reversed), escaping it unless it is safe.
            
            The left operand is treated as :meth:`__add__` treats the right
            one: appended unchanged when it implements ``__html__`` and
            HTML-escaped otherwise.
            
            :param other: String to prepend.
            
            :returns: New SafeString with the concatenated content, or
                NotImplemented when ``other`` is not a string.
        """
        result = NotImplemented
        
        if isinstance(other, str) or hasattr(other, "__html__"):
            other_markup = _to_safe_markup(other)
            result = SafeString(other_markup + str(self))
        
        return result


def _to_safe_markup(value: Any) -> str:
    """
        Get the HTML-safe text for an operand joined to a SafeString.
        
        A value that implements the ``__html__`` protocol has declared its
        content safe, so that content is used unchanged. Every other value
        is HTML-escaped.
        
        :param value: The operand being concatenated with a SafeString.
        
        :returns: Plain ``str`` text that is safe to place in HTML.
    """
    if hasattr(value, "__html__"):
        markup = str(value.__html__())
    else:
        markup = escape(value)
    
    return markup


def safe(value: str) -> SafeString:
    """
        Mark a string as safe (bypasses auto-escaping).
        
        This function wraps a string in a SafeString instance, indicating
        that the content should not be auto-escaped during template rendering.
        Use this function when you have pre-escaped content or trusted HTML
        that should be rendered as-is.
        
        .. warning::
        
            Only use this function with content that you trust completely.
            Marking untrusted user input as safe can lead to XSS vulnerabilities.
        
        :param value: String to mark as safe.
        
        :returns: SafeString instance that bypasses auto-escaping.
        
        Example usage::
        
            # Mark trusted HTML as safe
            trusted_html = safe("<strong>Bold text</strong>")
            
            # In templates, this renders without escaping
            # {{ trusted_html }} -> <strong>Bold text</strong>
    """
    return SafeString(value)


def escape(value: str) -> str:
    """
        Escape HTML special characters.
        
        This function escapes the five HTML special characters that can be
        used in XSS attacks or cause rendering issues:
        
        - & (ampersand) -> &amp;
        - < (less than) -> &lt;
        - > (greater than) -> &gt;
        - " (double quote) -> &quot;
        - ' (single quote) -> &#39;
        
        The ampersand is escaped first to prevent double-escaping of
        already-escaped sequences.
        
        :param value: String to escape.
        
        :returns: Escaped string with HTML special characters replaced.
        
        Example usage::
        
            escaped = escape("<script>alert('xss')</script>")
            # Result: "&lt;script&gt;alert(&#39;xss&#39;)&lt;/script&gt;"
            
            escaped = escape("Tom & Jerry")
            # Result: "Tom &amp; Jerry"
    """
    if not isinstance(value, str):
        value = str(value)
    
    result = value
    for char, replacement in _HTML_ESCAPE_MAP.items():
        result = result.replace(char, replacement)
    
    return result


def escape_json(value: Any) -> SafeString:
    """
        Escape a value for safe embedding in JavaScript.
        
        This function serializes a Python value to JSON and escapes
        characters that could cause issues when embedded in HTML script
        tags or JavaScript contexts. The following additional escapes
        are applied after JSON serialization:
        
        - < -> \\u003c (prevents </script> injection)
        - > -> \\u003e (prevents script tag issues)
        - & -> \\u0026 (prevents HTML entity issues)
        - ' -> \\u0027 (keeps the JSON inside a single-quoted HTML attribute)
        - U+2028 / U+2029 -> \\u2028 / \\u2029 (line terminators in JavaScript)
        
        The result contains none of the characters that end a script block
        or start an HTML entity, so it is returned as a :class:`SafeString`:
        an auto-escaping template engine emits it unchanged instead of
        turning its double quotes into entities, which would break the
        JavaScript. It is still JSON and parses to the same value.
        
        The double quote is not escaped, so in an HTML attribute the value
        must be placed inside single quotes.
        
        :param value: Value to escape. Can be any JSON-serializable type
            (str, int, float, bool, None, list, dict).
        
        :returns: JSON-escaped SafeString safe for embedding in JavaScript.
        
        Example usage::
        
            # In a template:
            # <script>var data = {{ escape_json(user_data) }};</script>
            
            escaped = escape_json({"name": "<script>", "count": 5})
            # Result: '{"name": "\\u003cscript\\u003e", "count": 5}'
            
            escaped = escape_json("Tom & Jerry")
            # Result: '"Tom \\u0026 Jerry"'
    """
    # Serialize to JSON
    json_str = json.dumps(value, ensure_ascii=False)
    
    # Escape characters that could cause issues in HTML/JavaScript contexts
    # These escapes prevent script injection when JSON is embedded in HTML
    json_str = json_str.replace("<", "\\u003c")
    json_str = json_str.replace(">", "\\u003e")
    json_str = json_str.replace("&", "\\u0026")
    json_str = json_str.replace("'", "\\u0027")
    json_str = json_str.replace("\u2028", "\\u2028")
    json_str = json_str.replace("\u2029", "\\u2029")
    
    return SafeString(json_str)


def escape_url(value: str) -> str:
    """
        URL-encode a string.
        
        This function encodes a string for safe use in URL components
        (query parameters, path segments, etc.). Characters that have
        special meaning in URLs or are not allowed are percent-encoded.
        
        The function uses UTF-8 encoding for non-ASCII characters and
        encodes all characters except:
        
        - Letters (A-Z, a-z)
        - Digits (0-9)
        - Unreserved characters: - _ . ~
        
        :param value: String to encode.
        
        :returns: URL-encoded string.
        
        Example usage::
        
            encoded = escape_url("hello world")
            # Result: "hello%20world"
            
            encoded = escape_url("name=value&other=test")
            # Result: "name%3Dvalue%26other%3Dtest"
            
            encoded = escape_url("日本語")
            # Result: "%E6%97%A5%E6%9C%AC%E8%AA%9E"
    """
    if not isinstance(value, str):
        value = str(value)
    
    # Use urllib.parse.quote with safe='' to encode all special characters
    # This ensures maximum safety for URL contexts
    return url_quote(value, safe='')
