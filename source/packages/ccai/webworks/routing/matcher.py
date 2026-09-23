"""
    URL pattern matcher for routing.
    
    This module provides the Matcher class for matching URL paths against
    patterns with support for static segments, parameterized segments,
    and wildcard segments.
    
    Pattern syntax:
    - Static segments: /api/users (exact match)
    - Parameterized segments: /users/{id} (captures value)
    - Typed parameters: /users/{id:int} (captures and converts)
    - Wildcard segments: /files/{path:path} (captures remaining path)
    
    Examples:
        matcher = Matcher("/users/{id:int}")
        result = matcher.match("/users/42")
        # result = {"id": 42}
        
        matcher = Matcher("/files/{filepath:path}")
        result = matcher.match("/files/docs/readme.txt")
        # result = {"filepath": "docs/readme.txt"}
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

from ccai.webworks.routing.converters import CONVERTERS, Converter


class SegmentType(Enum):
    """
    Type of URL pattern segment.
    
    Used to classify segments during pattern parsing and to
    calculate route specificity for precedence ordering.
    """
    
    STATIC = "static"       # Exact match segment (e.g., "users")
    PARAM = "param"         # Parameterized segment (e.g., "{id}")
    WILDCARD = "wildcard"   # Wildcard segment (e.g., "{path:path}")


@dataclass
class Segment:
    """
    Represents a parsed segment of a URL pattern.
    
    Attributes:
        segment_type: Type of segment (static, param, or wildcard).
        value: For static segments, the literal value to match.
               For param/wildcard, the parameter name.
        converter: For param/wildcard segments, the converter to use.
        regex: Compiled regex pattern for matching this segment.
    """
    
    segment_type: SegmentType
    value: str
    converter: Optional[Converter] = None
    regex: Optional[re.Pattern] = None


class Matcher:
    """
    URL pattern matcher supporting static, parameterized, and
    wildcard path segments.
    
    The Matcher parses a URL pattern into segments and provides
    methods to match paths against the pattern and extract
    parameter values.
    
    Attributes:
        pattern: The original URL pattern string.
        segments: List of parsed Segment objects.
    
    Example:
        matcher = Matcher("/users/{id:int}/posts/{slug}")
        
        # Match a path
        result = matcher.match("/users/42/posts/hello-world")
        # result = {"id": 42, "slug": "hello-world"}
        
        # Non-matching path returns None
        result = matcher.match("/users/abc/posts/hello")
        # result = None (because "abc" doesn't match int converter)
    """
    
    # Regex to parse parameter segments: {name} or {name:converter}
    PARAM_PATTERN = re.compile(r"\{([a-zA-Z_][a-zA-Z0-9_]*)(?::([a-zA-Z_][a-zA-Z0-9_]*))?\}")
    
    def __init__(self, pattern: str, converters: Optional[Dict[str, Converter]] = None):
        """
        Construct a Matcher from a URL pattern.
        
        Args:
            pattern: URL pattern (e.g., "/users/{id:int}").
            converters: Optional custom converters to use. If not provided,
                       uses the global CONVERTERS registry.
        
        Raises:
            ValueError: If the pattern is invalid or references an
                       unknown converter.
        """
        self._pattern = pattern
        self._converters = converters if converters is not None else CONVERTERS
        self._segments: List[Segment] = []
        self._parse_pattern()
    
    @property
    def pattern(self) -> str:
        """Return the original URL pattern string."""
        return self._pattern
    
    @property
    def segments(self) -> List[Segment]:
        """Return the list of parsed segments."""
        return self._segments
    
    def _parse_pattern(self) -> None:
        """
        Parse the URL pattern into segments.
        
        Splits the pattern by '/' and classifies each segment as
        static, parameterized, or wildcard based on its syntax.
        
        Raises:
            ValueError: If the pattern contains invalid syntax or
                       references an unknown converter.
        """
        # Normalize pattern - remove leading/trailing slashes for parsing
        normalized = self._pattern.strip("/")
        
        if not normalized:
            # Empty pattern matches root path
            return
        
        parts = normalized.split("/")
        
        for part in parts:
            segment = self._parse_segment(part)
            self._segments.append(segment)
    
    def _parse_segment(self, part: str) -> Segment:
        """
        Parse a single segment of the URL pattern.
        
        Args:
            part: A single segment string (e.g., "users", "{id}", "{id:int}").
        
        Returns:
            A Segment object representing the parsed segment.
        
        Raises:
            ValueError: If the segment syntax is invalid or references
                       an unknown converter.
        """
        match = self.PARAM_PATTERN.fullmatch(part)
        
        if match:
            # This is a parameterized segment
            param_name = match.group(1)
            converter_name = match.group(2) or "str"  # Default to string converter
            
            try:
                converter = self._converters[converter_name]
            except KeyError:
                raise ValueError(
                    f"Unknown converter '{converter_name}' in pattern segment '{part}'. "
                    f"Available converters: {list(self._converters.keys())}"
                )
            
            # Determine if this is a wildcard (path converter)
            if converter_name == "path":
                segment_type = SegmentType.WILDCARD
            else:
                segment_type = SegmentType.PARAM
            
            # Compile regex for this segment
            regex = re.compile(f"^({converter.regex})$")
            
            return Segment(
                segment_type=segment_type,
                value=param_name,
                converter=converter,
                regex=regex,
            )
        else:
            # This is a static segment
            # Escape any regex special characters in the literal value
            escaped = re.escape(part)
            regex = re.compile(f"^{escaped}$")
            
            return Segment(
                segment_type=SegmentType.STATIC,
                value=part,
                converter=None,
                regex=regex,
            )

    
    def match(self, path: str) -> Optional[Dict[str, Any]]:
        """
        Match a path against this pattern.
        
        Attempts to match the given path against the URL pattern,
        extracting and converting any parameter values.
        
        Args:
            path: URL path to match (e.g., "/users/42").
        
        Returns:
            Dict of extracted parameters if the path matches, None otherwise.
            For static-only patterns, returns an empty dict on match.
        
        Example:
            matcher = Matcher("/users/{id:int}/posts/{slug}")
            
            result = matcher.match("/users/42/posts/hello-world")
            # result = {"id": 42, "slug": "hello-world"}
            
            result = matcher.match("/users/abc/posts/hello")
            # result = None (conversion failure)
            
            result = matcher.match("/other/path")
            # result = None (no match)
        """
        # Normalize path - remove leading/trailing slashes for matching
        normalized = path.strip("/")
        
        # Handle empty path (root)
        if not normalized and not self._segments:
            return {}
        
        if not normalized and self._segments:
            return None
        
        if normalized and not self._segments:
            return None
        
        parts = normalized.split("/")
        params: Dict[str, Any] = {}
        
        # Check for wildcard segment (path converter)
        has_wildcard = (
            self._segments and 
            self._segments[-1].segment_type == SegmentType.WILDCARD
        )
        
        if has_wildcard:
            # Wildcard must be the last segment and consumes remaining path
            non_wildcard_segments = self._segments[:-1]
            wildcard_segment = self._segments[-1]
            
            # Must have at least as many parts as non-wildcard segments
            if len(parts) < len(non_wildcard_segments):
                return None
            
            # Match non-wildcard segments
            for i, segment in enumerate(non_wildcard_segments):
                match_result = self._match_segment(segment, parts[i])
                if match_result is None:
                    return None
                params.update(match_result)
            
            # Remaining parts go to wildcard
            remaining_parts = parts[len(non_wildcard_segments):]
            if not remaining_parts:
                return None  # Wildcard must match at least something
            
            remaining_path = "/".join(remaining_parts)
            
            # Apply wildcard converter
            try:
                converted_value = wildcard_segment.converter.convert(remaining_path)
                params[wildcard_segment.value] = converted_value
            except (ValueError, TypeError):
                return None
        else:
            # No wildcard - must have exact segment count
            if len(parts) != len(self._segments):
                return None
            
            # Match each segment
            for segment, part in zip(self._segments, parts):
                match_result = self._match_segment(segment, part)
                if match_result is None:
                    return None
                params.update(match_result)
        
        return params
    
    def _match_segment(self, segment: Segment, part: str) -> Optional[Dict[str, Any]]:
        """
        Match a single segment against a path part.
        
        Args:
            segment: The Segment to match against.
            part: The path part to match.
        
        Returns:
            Dict with parameter name and converted value if match succeeds,
            empty dict for static segments, None if no match.
        """
        if segment.segment_type == SegmentType.STATIC:
            # Static segment - must match exactly
            if segment.regex.match(part):
                return {}
            return None
        
        elif segment.segment_type == SegmentType.PARAM:
            # Parameterized segment - must match regex and convert
            if not segment.regex.match(part):
                return None
            
            try:
                converted_value = segment.converter.convert(part)
                return {segment.value: converted_value}
            except (ValueError, TypeError):
                return None
        
        # Wildcard segments are handled separately in match()
        return None
    
    @property
    def specificity(self) -> int:
        """
        Return specificity score for route precedence.
        
        Higher scores indicate more specific routes. When multiple
        routes could match a path, the route with the highest
        specificity should be preferred.
        
        Scoring:
        - Static segments: 3 points each
        - Parameterized segments: 2 points each
        - Wildcard segments: 1 point each
        
        This ensures that:
        - /users/profile beats /users/{id}
        - /users/{id} beats /users/{path:path}
        - Longer specific routes beat shorter ones
        
        Returns:
            Integer specificity score.
        
        Example:
            Matcher("/users/profile").specificity  # 6 (3+3)
            Matcher("/users/{id}").specificity     # 5 (3+2)
            Matcher("/users/{path:path}").specificity  # 4 (3+1)
            Matcher("/{path:path}").specificity    # 1
        """
        score = 0
        
        for segment in self._segments:
            if segment.segment_type == SegmentType.STATIC:
                score += 3
            elif segment.segment_type == SegmentType.PARAM:
                score += 2
            elif segment.segment_type == SegmentType.WILDCARD:
                score += 1
        
        return score
    
    def __repr__(self) -> str:
        """Return string representation of the Matcher."""
        return f"Matcher({self._pattern!r})"
    
    def __eq__(self, other: object) -> bool:
        """Check equality based on pattern string."""
        if not isinstance(other, Matcher):
            return NotImplemented
        return self._pattern == other._pattern
    
    def __hash__(self) -> int:
        """Return hash based on pattern string."""
        return hash(self._pattern)
