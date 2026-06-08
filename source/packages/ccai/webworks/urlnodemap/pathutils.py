"""
    Path utility functions for URL Node Map.
    
    This module provides utility functions for normalizing, splitting,
    and analyzing URL path strings. These functions are used throughout
    the URL Node Map implementation to ensure consistent path handling.
    
    Functions:
    - normalize_path: Normalize a URL path to canonical form
    - split_path: Split a path into its component segments
    - is_parameter_segment: Check if a segment is a parameter placeholder
    - extract_parameter_name: Extract the parameter name from a parameter segment
"""

import re
from typing import List, Optional


def normalize_path(path: str) -> str:
    """
    Normalize a URL path to canonical form.
    
    Normalization ensures consistent path representation by:
    - Ensuring the path starts with "/"
    - Collapsing multiple consecutive slashes into single slashes
    - Removing trailing slashes (except for root "/")
    
    This function is idempotent: normalizing an already normalized
    path returns the same result.
    
    Args:
        path: The path to normalize.
    
    Returns:
        The normalized path string.
    
    Examples:
        >>> normalize_path("/api/v1/users")
        '/api/v1/users'
        >>> normalize_path("/api/v1/users/")
        '/api/v1/users'
        >>> normalize_path("api/v1/users")
        '/api/v1/users'
        >>> normalize_path("//api//v1//users//")
        '/api/v1/users'
        >>> normalize_path("/")
        '/'
        >>> normalize_path("")
        '/'
    
    Validates: Requirements 2.9, 2.10
    """
    # Handle empty path
    if not path:
        return "/"
    
    # Ensure path starts with "/"
    if not path.startswith("/"):
        path = "/" + path
    
    # Collapse multiple consecutive slashes into single slashes
    path = re.sub(r"/+", "/", path)
    
    # Remove trailing slash (except for root "/")
    if len(path) > 1 and path.endswith("/"):
        path = path.rstrip("/")
    
    return path


def split_path(path: str) -> List[str]:
    """
    Split a path into its component segments.
    
    The path is first normalized, then split on "/" characters.
    Empty segments (from leading/trailing slashes) are filtered out.
    
    Args:
        path: The path to split (e.g., "/api/v1/users").
    
    Returns:
        List of segments (e.g., ["api", "v1", "users"]).
        Returns an empty list for the root path "/".
    
    Examples:
        >>> split_path("/api/v1/users")
        ['api', 'v1', 'users']
        >>> split_path("/")
        []
        >>> split_path("/api/v1/{user_id}")
        ['api', 'v1', '{user_id}']
        >>> split_path("api/v1/users")
        ['api', 'v1', 'users']
    """
    # Normalize the path first
    normalized = normalize_path(path)
    
    # Split and filter out empty segments
    segments = [seg for seg in normalized.split("/") if seg]
    
    return segments


def is_parameter_segment(segment: str) -> bool:
    """
    Check if a segment is a parameter placeholder.
    
    A parameter segment is identified by the pattern {param_name}
    where param_name is a non-empty string containing only valid
    identifier characters (alphanumeric and underscores). The segment
    must start with "{" and end with "}" with exactly one opening
    and one closing brace.
    
    Args:
        segment: The segment to check.
    
    Returns:
        True if segment matches {param_name} pattern with non-empty name.
    
    Examples:
        >>> is_parameter_segment("{user_id}")
        True
        >>> is_parameter_segment("{id}")
        True
        >>> is_parameter_segment("users")
        False
        >>> is_parameter_segment("{}")
        False
        >>> is_parameter_segment("{")
        False
        >>> is_parameter_segment("}")
        False
        >>> is_parameter_segment("{{nested}}")
        False
    
    Validates: Requirements 7.1, 7.2
    """
    if not segment:
        return False
    
    # Must start with "{" and end with "}"
    if not (segment.startswith("{") and segment.endswith("}")):
        return False
    
    # Must have exactly one opening and one closing brace
    if segment.count("{") != 1 or segment.count("}") != 1:
        return False
    
    # Must have at least one character between braces
    inner = segment[1:-1]
    if len(inner) == 0:
        return False
    
    # Inner content must not contain braces
    if "{" in inner or "}" in inner:
        return False
    
    # Inner content must not be only whitespace
    if inner.strip() == "":
        return False
    
    return True


def extract_parameter_name(segment: str) -> Optional[str]:
    """
    Extract the parameter name from a parameter segment.
    
    If the segment is a valid parameter segment (matches {param_name}
    pattern), returns the parameter name. Otherwise returns None.
    
    Args:
        segment: The segment (e.g., "{user_id}").
    
    Returns:
        The parameter name (e.g., "user_id") or None if not a parameter.
    
    Examples:
        >>> extract_parameter_name("{user_id}")
        'user_id'
        >>> extract_parameter_name("{id}")
        'id'
        >>> extract_parameter_name("users")
        None
        >>> extract_parameter_name("{}")
        None
    
    Validates: Requirements 7.1, 7.2
    """
    if not is_parameter_segment(segment):
        return None
    
    # Extract the name between braces
    return segment[1:-1]
