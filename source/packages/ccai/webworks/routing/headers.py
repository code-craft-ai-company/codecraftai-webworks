"""
    Headers module.
    
    This module provides the Headers class for case-insensitive HTTP header
    access.
"""

import re

from typing import Dict, Iterable, List, Optional, Tuple


# A backslash escape inside a quoted cookie value: three octal digits or
# any single character.
_COOKIE_ESCAPE_RE: re.Pattern = re.compile(r"\\(?:([0-3][0-7][0-7])|(.))")


def _unescape_cookie_value(match: "re.Match") -> str:
    """
        Replace one backslash escape of a quoted cookie value.

        :param match: A match of :data:`_COOKIE_ESCAPE_RE`.

        :returns: The character the escape stands for.
    """
    octal_digits = match.group(1)

    if octal_digits is not None:
        rtnval = chr(int(octal_digits, 8))
    else:
        rtnval = match.group(2)

    return rtnval


def parse_cookie_header(header_value: Optional[str]) -> List[Tuple[str, str]]:
    """
        Parse the value of a ``Cookie`` request header into its
        ``(name, value)`` pairs, in the order the client sent them.

        The header is split pair by pair, so one malformed cookie does not
        hide the others: ``prefs={"x":1}; session_id=abc`` yields both
        cookies. A value in double quotes is returned without the quotes
        and with its backslash escapes resolved.
        A pair without ``=`` or without a name is skipped.

        The same name can occur more than once -- a browser sends every
        cookie that matches the request, and cookies set for different
        paths or domains may share a name. All occurrences are returned so
        the caller decides which one counts, and can tell that there was
        more than one.

        :param header_value: The raw ``Cookie`` header value, or ``None``.

        :returns: List of ``(name, value)`` pairs; empty for an empty header.
    """
    rtnval: List[Tuple[str, str]] = []

    if header_value:
        for chunk in str(header_value).split(";"):
            name, separator, value = chunk.partition("=")
            name = name.strip()
            value = value.strip()

            if separator == "" or name == "":
                continue

            if len(value) >= 2 and value[0] == '"' and value[-1] == '"':
                value = value[1:-1]
                if "\\" in value:
                    value = _COOKIE_ESCAPE_RE.sub(_unescape_cookie_value, value)

            rtnval.append((name, value))

    return rtnval


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
    
    def __eq__(self, other: object) -> bool:
        """
            Compare against another Headers or any mapping, ignoring case.

            Header names are case-insensitive, so ``Content-Length`` and
            ``content-length`` are the same header and two collections
            differing only in the case of their names are equal. Without
            this, equality fell back to identity: a Headers object never
            compared equal to the dict it was built from, and even an empty
            one was unequal to ``{}``.

            :param other: A Headers, or a mapping of names to values.

            :returns: True when both hold the same headers.
        """
        if isinstance(other, Headers):
            return self._headers == other._headers

        if isinstance(other, dict):
            if len(other) != len(self._headers):
                return False
            for name, value in other.items():
                if not isinstance(name, str):
                    return False
                if self._headers.get(name.lower()) != value:
                    return False
            return True

        return NotImplemented

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
