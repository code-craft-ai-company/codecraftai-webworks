"""
    ASGI Scope Parser module.
    
    This module provides the ScopeParser class that parses ASGI scope dictionaries
    into framework Request objects and manages framework-specific scope extensions.
"""

from typing import Any, Dict, List, Optional, Tuple

from automojo.webworks.routing.request import Request
from automojo.webworks.asgi.constants import (
    SCOPE_REQUEST,
    SCOPE_ROUTE,
    SCOPE_PATH_PARAMS,
)


# Framework namespace prefix for custom scope keys
FRAMEWORK_NAMESPACE: str = "webworks."

# Standard ASGI scope keys that should not be modified
STANDARD_ASGI_KEYS: Tuple[str, ...] = (
    "type",
    "asgi",
    "http_version",
    "method",
    "scheme",
    "path",
    "raw_path",
    "query_string",
    "root_path",
    "headers",
    "server",
    "client",
    "state",
    # WebSocket specific
    "subprotocols",
    # Extensions
    "extensions",
)


class ScopeParser:
    """
        Parses ASGI scope dictionaries into framework Request objects.
        
        This class provides methods to extract individual values from an ASGI
        scope dictionary and to create complete Request objects from HTTP scopes.
        It also manages framework-specific scope extensions.
    """
    
    def __init__(self):
        """
            Construct a ScopeParser instance.
        """
        return
    
    def get_method(self, scope: Dict[str, Any]) -> str:
        """
            Extract the HTTP method from the scope.
            
            :param scope: ASGI scope dictionary.
            
            :returns: HTTP method string (e.g., 'GET', 'POST').
        """
        rtnval = scope.get("method", "GET")
        return rtnval
    
    def get_path(self, scope: Dict[str, Any]) -> str:
        """
            Extract the request path from the scope.
            
            :param scope: ASGI scope dictionary.
            
            :returns: Request path string.
        """
        rtnval = scope.get("path", "/")
        return rtnval
    
    def get_query_string(self, scope: Dict[str, Any]) -> str:
        """
            Extract the query string from the scope.
            
            The query string is stored as bytes in the ASGI scope and is
            decoded to a UTF-8 string.
            
            :param scope: ASGI scope dictionary.
            
            :returns: Query string without leading '?'.
        """
        query_bytes = scope.get("query_string", b"")
        if isinstance(query_bytes, bytes):
            rtnval = query_bytes.decode("utf-8")
        else:
            rtnval = str(query_bytes)
        return rtnval
    
    def get_scheme(self, scope: Dict[str, Any]) -> str:
        """
            Extract the URL scheme from the scope.
            
            :param scope: ASGI scope dictionary.
            
            :returns: URL scheme string ('http' or 'https').
        """
        rtnval = scope.get("scheme", "http")
        return rtnval
    
    def get_server(self, scope: Dict[str, Any]) -> Tuple[str, int]:
        """
            Extract the server address from the scope.
            
            :param scope: ASGI scope dictionary.
            
            :returns: Tuple of (host, port).
        """
        server = scope.get("server")
        if server is not None:
            rtnval = (str(server[0]), int(server[1]))
        else:
            # Default based on scheme
            scheme = self.get_scheme(scope)
            if scheme == "https":
                rtnval = ("localhost", 443)
            else:
                rtnval = ("localhost", 80)
        return rtnval
    
    def get_client(self, scope: Dict[str, Any]) -> Optional[Tuple[str, int]]:
        """
            Extract the client address from the scope.
            
            :param scope: ASGI scope dictionary.
            
            :returns: Tuple of (host, port) or None if not available.
        """
        client = scope.get("client")
        if client is not None:
            rtnval = (str(client[0]), int(client[1]))
        else:
            rtnval = None
        return rtnval
    
    def get_http_version(self, scope: Dict[str, Any]) -> str:
        """
            Extract the HTTP version from the scope.
            
            :param scope: ASGI scope dictionary.
            
            :returns: HTTP version string (e.g., '1.1', '2').
        """
        rtnval = scope.get("http_version", "1.1")
        return rtnval
    
    def get_root_path(self, scope: Dict[str, Any]) -> str:
        """
            Extract the root path for mounted applications.
            
            :param scope: ASGI scope dictionary.
            
            :returns: Root path string.
        """
        rtnval = scope.get("root_path", "")
        return rtnval
    
    def get_headers(self, scope: Dict[str, Any]) -> Dict[str, str]:
        """
            Extract HTTP headers from the scope.
            
            ASGI stores headers as a list of (name, value) byte tuples.
            This method converts them to a dictionary with title-cased
            header names.
            
            :param scope: ASGI scope dictionary.
            
            :returns: Dictionary of header names to values.
        """
        headers: Dict[str, str] = {}
        raw_headers: List[Tuple[bytes, bytes]] = scope.get("headers", [])
        
        for name_bytes, value_bytes in raw_headers:
            # Decode header name and value
            if isinstance(name_bytes, bytes):
                name = name_bytes.decode("latin-1")
            else:
                name = str(name_bytes)
            
            if isinstance(value_bytes, bytes):
                value = value_bytes.decode("latin-1")
            else:
                value = str(value_bytes)
            
            # Normalize header name to title case
            normalized_name = name.title()
            headers[normalized_name] = value
        
        return headers
    
    def parse_http(self, scope: Dict[str, Any]) -> Request:
        """
            Parse an HTTP scope into a Request object.
            
            This method extracts all relevant data from the ASGI scope and
            creates a Request object. Note that the request body is not
            included as it must be read asynchronously via the receive callable.
            
            :param scope: ASGI HTTP scope dictionary.
            
            :returns: Parsed Request object (without body).
        """
        request = Request.from_asgi(scope, body=b"")
        return request
    
    def set_framework_scope(
        self,
        scope: Dict[str, Any],
        request: Request,
        route: Optional[Any] = None,
        path_params: Optional[Dict[str, str]] = None,
    ) -> None:
        """
            Set framework-specific scope keys.
            
            This method adds framework-specific data to the ASGI scope
            dictionary for use by middleware and handlers.
            
            :param scope: ASGI scope dictionary to modify.
            :param request: The Request object to store.
            :param route: Optional matched route object.
            :param path_params: Optional path parameters dictionary.
        """
        scope[SCOPE_REQUEST] = request
        
        if route is not None:
            scope[SCOPE_ROUTE] = route
        
        if path_params is not None:
            scope[SCOPE_PATH_PARAMS] = path_params
        
        return
    
    def set_custom_scope_key(
        self,
        scope: Dict[str, Any],
        key: str,
        value: Any,
    ) -> None:
        """
            Set a custom scope key with framework namespace prefix.
            
            This method allows middleware to add custom data to the scope
            while ensuring the framework namespace is used. If the key
            does not start with the framework namespace prefix, it will
            be added automatically.
            
            :param scope: ASGI scope dictionary to modify.
            :param key: The key name (with or without namespace prefix).
            :param value: The value to store.
        """
        if not key.startswith(FRAMEWORK_NAMESPACE):
            full_key = f"{FRAMEWORK_NAMESPACE}{key}"
        else:
            full_key = key
        
        scope[full_key] = value
        return
    
    def get_custom_scope_key(
        self,
        scope: Dict[str, Any],
        key: str,
        default: Any = None,
    ) -> Any:
        """
            Get a custom scope key value.
            
            This method retrieves a custom scope key value, automatically
            adding the framework namespace prefix if not present.
            
            :param scope: ASGI scope dictionary.
            :param key: The key name (with or without namespace prefix).
            :param default: Default value if key not found.
            
            :returns: The value or default.
        """
        if not key.startswith(FRAMEWORK_NAMESPACE):
            full_key = f"{FRAMEWORK_NAMESPACE}{key}"
        else:
            full_key = key
        
        rtnval = scope.get(full_key, default)
        return rtnval
    
    def get_framework_scope_keys(
        self,
        scope: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
            Get all framework namespace scope keys.
            
            This method returns all scope keys that are in the framework
            namespace (prefixed with 'webworks.').
            
            :param scope: ASGI scope dictionary.
            
            :returns: Dictionary of framework namespace keys and values.
        """
        rtnval: Dict[str, Any] = {}
        
        for key, value in scope.items():
            if key.startswith(FRAMEWORK_NAMESPACE):
                rtnval[key] = value
        
        return rtnval
    
    def is_standard_asgi_key(self, key: str) -> bool:
        """
            Check if a key is a standard ASGI scope key.
            
            :param key: The key to check.
            
            :returns: True if the key is a standard ASGI key.
        """
        rtnval = key in STANDARD_ASGI_KEYS
        return rtnval
    
    def preserve_standard_keys(
        self,
        scope: Dict[str, Any],
        updates: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
            Apply updates to scope while preserving standard ASGI keys.
            
            This method creates a new scope dictionary with updates applied,
            but ensures that standard ASGI keys are not modified by the
            updates. Framework namespace keys can be updated freely.
            
            :param scope: Original ASGI scope dictionary.
            :param updates: Dictionary of updates to apply.
            
            :returns: New scope dictionary with updates applied.
        """
        # Start with a copy of the original scope
        rtnval = scope.copy()
        
        # Apply updates, but skip standard ASGI keys
        for key, value in updates.items():
            if not self.is_standard_asgi_key(key):
                rtnval[key] = value
        
        return rtnval
    
    def get_state(self, scope: Dict[str, Any]) -> Dict[str, Any]:
        """
            Get the application state from scope.
            
            The state key is a standard ASGI scope key used to store
            application-level state that persists across requests.
            
            :param scope: ASGI scope dictionary.
            
            :returns: State dictionary (empty dict if not present).
        """
        rtnval = scope.get("state", {})
        return rtnval
    
    def ensure_state(self, scope: Dict[str, Any]) -> Dict[str, Any]:
        """
            Ensure the state key exists in scope and return it.
            
            If the state key does not exist, it will be created as an
            empty dictionary. This follows the ASGI spec which allows
            applications to use the state key for application-level state.
            
            :param scope: ASGI scope dictionary.
            
            :returns: State dictionary.
        """
        if "state" not in scope:
            scope["state"] = {}
        
        rtnval = scope["state"]
        return rtnval
