"""
    Path parameter converters for URL routing.
    
    This module provides the Converter protocol and built-in converters for
    validating and transforming path segments in URL patterns.
    
    Converters are used to:
    - Define regex patterns for matching path segments
    - Convert matched string values to appropriate Python types
    
    Built-in converters:
    - StringConverter: matches any non-empty string segment
    - IntConverter: matches and converts integers
    - FloatConverter: matches and converts floats
    - UUIDConverter: matches and converts UUIDs
    - PathConverter: matches remaining path including slashes
"""

from typing import Any, Dict, Protocol
from uuid import UUID


class Converter(Protocol):
    """
    Protocol for path parameter converters that validate and
    transform path segments.
    
    Converters define a regex pattern for matching path segments
    and a convert method for transforming matched values to the
    target type.
    
    Attributes:
        regex: Regex pattern to match path segments.
    """
    
    regex: str
    
    def convert(self, value: str) -> Any:
        """
        Convert a matched string value to the target type.
        
        Args:
            value: String value from path segment.
        
        Returns:
            Converted value of the appropriate type.
        
        Raises:
            ValueError: If conversion fails.
        """


class StringConverter:
    """
    Converter that matches any non-empty string segment.
    
    This is the default converter used when no type is specified
    in a path parameter (e.g., {name} is equivalent to {name:str}).
    
    The regex matches any sequence of characters that does not
    include a forward slash.
    """
    
    regex: str = r"[^/]+"
    
    def convert(self, value: str) -> str:
        """
        Return the string value unchanged.
        
        Args:
            value: String value from path segment.
        
        Returns:
            The input string unchanged.
        """
        return value


class IntConverter:
    """
    Converter that matches integer values and converts to Python int.
    
    The regex matches one or more digits, optionally preceded by
    a minus sign for negative integers.
    """
    
    regex: str = r"-?\d+"
    
    def convert(self, value: str) -> int:
        """
        Convert string to integer.
        
        Args:
            value: String value from path segment.
        
        Returns:
            Integer value.
        
        Raises:
            ValueError: If the string cannot be converted to int.
        """
        return int(value)


class FloatConverter:
    """
    Converter that matches numeric values and converts to Python float.
    
    The regex matches integers and decimal numbers, optionally
    preceded by a minus sign.
    """
    
    regex: str = r"-?\d+\.?\d*"
    
    def convert(self, value: str) -> float:
        """
        Convert string to float.
        
        Args:
            value: String value from path segment.
        
        Returns:
            Float value.
        
        Raises:
            ValueError: If the string cannot be converted to float.
        """
        return float(value)


class UUIDConverter:
    """
    Converter that matches UUID strings and converts to Python UUID.
    
    The regex matches standard UUID format with hyphens:
    xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
    
    Both lowercase and uppercase hex digits are accepted.
    """
    
    regex: str = r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
    
    def convert(self, value: str) -> UUID:
        """
        Convert string to UUID.
        
        Args:
            value: String value from path segment.
        
        Returns:
            UUID object.
        
        Raises:
            ValueError: If the string is not a valid UUID.
        """
        return UUID(value)


class PathConverter:
    """
    Converter that matches any remaining path including slashes.
    
    This converter is used for catch-all routes that need to capture
    the entire remaining path, such as /files/{filepath:path} which
    would match /files/docs/readme.txt with filepath="docs/readme.txt".
    
    The regex matches one or more characters of any kind.
    """
    
    regex: str = r".+"
    
    def convert(self, value: str) -> str:
        """
        Return the path value unchanged.
        
        Args:
            value: String value from remaining path.
        
        Returns:
            The input string unchanged.
        """
        return value


# Global converter registry with built-in converters
CONVERTERS: Dict[str, Converter] = {
    "str": StringConverter(),
    "int": IntConverter(),
    "float": FloatConverter(),
    "uuid": UUIDConverter(),
    "path": PathConverter(),
}


def register_converter(name: str, converter: Converter) -> None:
    """
    Register a custom converter for use in URL patterns.
    
    Custom converters allow extending the routing system with
    application-specific parameter types. For example, a slug
    converter that only matches URL-safe strings.
    
    Args:
        name: Name to use in URL patterns (e.g., "slug" for {param:slug}).
        converter: Converter instance implementing the Converter protocol.
    
    Example:
        class SlugConverter:
            regex = r"[a-z0-9]+(?:-[a-z0-9]+)*"
            
            def convert(self, value: str) -> str:
                return value
        
        register_converter("slug", SlugConverter())
        # Now can use {title:slug} in URL patterns
    """
    CONVERTERS[name] = converter


def get_converter(name: str) -> Converter:
    """
    Get a converter by name from the registry.
    
    Args:
        name: Name of the converter to retrieve.
    
    Returns:
        The registered Converter instance.
    
    Raises:
        KeyError: If no converter is registered with the given name.
    """
    return CONVERTERS[name]
