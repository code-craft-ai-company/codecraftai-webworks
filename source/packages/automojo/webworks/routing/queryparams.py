"""
    Query Parameters module.
    
    This module provides the QueryParams class for parsing and accessing
    query string parameters with support for multi-value keys.
"""

from typing import Dict, Iterable, List, Optional, Tuple
from urllib.parse import parse_qs


class QueryParams:
    """
        Dict-like object for query parameters supporting multi-value keys.
        
        This class parses a query string and provides a dict-like interface
        for accessing parameter values. It supports multi-value keys via
        the getlist() method.
    """
    
    def __init__(self, query_string: bytes):
        """
            Parse query string into parameters.
            
            :param query_string: Query string as bytes (without leading '?').
        """
        # Decode bytes to string if necessary
        if isinstance(query_string, bytes):
            decoded_string = query_string.decode("utf-8", errors="replace")
        else:
            decoded_string = str(query_string)
        
        # Parse the query string into a dict of lists
        self._params: Dict[str, List[str]] = parse_qs(
            decoded_string,
            keep_blank_values=True
        )
        return
    
    def __getitem__(self, key: str) -> str:
        """
            Get first value for key.
            
            :param key: Parameter name.
            
            :returns: First value for the key.
            
            :raises KeyError: If key not found.
        """
        values = self._params[key]
        rtnval = values[0]
        return rtnval
    
    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
            Get first value for key with default.
            
            :param key: Parameter name.
            :param default: Default value if key not found.
            
            :returns: First value for the key or default.
        """
        values = self._params.get(key)
        if values is not None and len(values) > 0:
            rtnval = values[0]
        else:
            rtnval = default
        return rtnval
    
    def getlist(self, key: str) -> List[str]:
        """
            Get all values for key.
            
            :param key: Parameter name.
            
            :returns: List of all values for the key (empty list if not found).
        """
        rtnval = self._params.get(key, [])
        return rtnval
    
    def keys(self) -> Iterable[str]:
        """
            Return all keys.
            
            :returns: Iterable of all parameter names.
        """
        rtnval = self._params.keys()
        return rtnval
    
    def items(self) -> Iterable[Tuple[str, str]]:
        """
            Return all key-value pairs (first value per key).
            
            :returns: Iterable of (key, first_value) tuples.
        """
        for key, values in self._params.items():
            if len(values) > 0:
                yield (key, values[0])
        return
    
    def __contains__(self, key: str) -> bool:
        """
            Check if key exists.
            
            :param key: Parameter name.
            
            :returns: True if key exists.
        """
        rtnval = key in self._params
        return rtnval
    
    def __len__(self) -> int:
        """
            Return number of unique keys.
            
            :returns: Number of unique parameter names.
        """
        rtnval = len(self._params)
        return rtnval
    
    def __repr__(self) -> str:
        """
            Get string representation.
            
            :returns: String representation.
        """
        rtnval = f"QueryParams({dict(self.items())})"
        return rtnval
