"""
    Headers module.
    
    This module provides the Headers class for case-insensitive HTTP header
    access.
"""

from typing import Dict, Iterable, Optional, Tuple


class Headers:
    """
        Case-insensitive dict-like object for HTTP headers.
        
        This class stores headers with normalized (lowercase) keys internally
        while preserving the original header names for iteration. All lookups
        are case-insensitive.
    """
    
    def __init__(self, headers: Optional[Dict[str, str]] = None):
        """
            Initialize with optional headers dict.
            
            :param headers: Optional dictionary of header names to values.
        """
        # Store headers with lowercase keys for case-insensitive lookup
        self._headers: Dict[str, str] = {}
        # Store original names for iteration
        self._original_names: Dict[str, str] = {}
        
        if headers is not None:
            for name, value in headers.items():
                normalized_key = name.lower()
                self._headers[normalized_key] = value
                self._original_names[normalized_key] = name
        return
    
    def __getitem__(self, key: str) -> str:
        """
            Get header value (case-insensitive).
            
            :param key: Header name (any case).
            
            :returns: Header value.
            
            :raises KeyError: If header not found.
        """
        normalized_key = key.lower()
        rtnval = self._headers[normalized_key]
        return rtnval
    
    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
            Get header value with default (case-insensitive).
            
            :param key: Header name (any case).
            :param default: Default value if header not found.
            
            :returns: Header value or default.
        """
        normalized_key = key.lower()
        rtnval = self._headers.get(normalized_key, default)
        return rtnval
    
    def __contains__(self, key: str) -> bool:
        """
            Check if header exists (case-insensitive).
            
            :param key: Header name (any case).
            
            :returns: True if header exists.
        """
        normalized_key = key.lower()
        rtnval = normalized_key in self._headers
        return rtnval
    
    def __setitem__(self, key: str, value: str) -> None:
        """
            Set header value.
            
            :param key: Header name.
            :param value: Header value.
        """
        normalized_key = key.lower()
        self._headers[normalized_key] = value
        self._original_names[normalized_key] = key
        return
    
    def __delitem__(self, key: str) -> None:
        """
            Delete header.
            
            :param key: Header name (any case).
            
            :raises KeyError: If header not found.
        """
        normalized_key = key.lower()
        del self._headers[normalized_key]
        del self._original_names[normalized_key]
        return
    
    def keys(self) -> Iterable[str]:
        """
            Return all header names (original case).
            
            :returns: Iterable of header names.
        """
        rtnval = self._original_names.values()
        return rtnval
    
    def values(self) -> Iterable[str]:
        """
            Return all header values.
            
            :returns: Iterable of header values.
        """
        rtnval = self._headers.values()
        return rtnval
    
    def items(self) -> Iterable[Tuple[str, str]]:
        """
            Return all header name-value pairs (original case for names).
            
            :returns: Iterable of (name, value) tuples.
        """
        for normalized_key, value in self._headers.items():
            original_name = self._original_names[normalized_key]
            yield (original_name, value)
        return
    
    def __len__(self) -> int:
        """
            Return number of headers.
            
            :returns: Number of headers.
        """
        rtnval = len(self._headers)
        return rtnval
    
    def __repr__(self) -> str:
        """
            Get string representation.
            
            :returns: String representation.
        """
        rtnval = f"Headers({dict(self.items())})"
        return rtnval
    
    def copy(self) -> "Headers":
        """
            Create a copy of this Headers object.
            
            :returns: New Headers object with same headers.
        """
        rtnval = Headers()
        rtnval._headers = self._headers.copy()
        rtnval._original_names = self._original_names.copy()
        return rtnval
