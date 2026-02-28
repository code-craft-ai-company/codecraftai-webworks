"""
.. module:: apikey
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: API Key Authentication implementation.

.. moduleauthor:: Automation Mojo LLC

This module provides the APIKeyAuthenticator class which implements API Key
Authentication. It supports extracting API keys from HTTP headers, query
parameters, or cookies, and validates them against a configurable key store.
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


from enum import Enum
from typing import Any, Dict, Optional, Protocol, Set, runtime_checkable

from automojo.webworks.authentication.core import (
    AuthenticationContext,
    AuthenticationResult,
    AuthenticationStatus,
    Principal
)


class APIKeyLocation(Enum):
    """
        Enumeration of locations where API keys can be extracted from.
        
        :cvar HEADER: Extract API key from an HTTP header.
        :cvar QUERY: Extract API key from a query parameter.
        :cvar COOKIE: Extract API key from a cookie.
    """
    
    HEADER = "header"
    QUERY = "query"
    COOKIE = "cookie"


@runtime_checkable
class APIKeyStore(Protocol):
    """
        Protocol for API key storage and validation.
        
        An APIKeyStore is responsible for validating API keys and returning
        associated metadata (client_id, roles, permissions, etc.) if valid.
    """
    
    async def validate_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """
            Validate an API key and return its associated metadata if valid.
            
            :param api_key: The API key string to validate.
            
            :returns: A dictionary of key metadata if valid, None otherwise.
                     The dictionary may contain:
                     - client_id: Unique identifier for the API key owner
                     - name: Display name for the key owner
                     - roles: List of roles associated with the key
                     - permissions: List of permissions granted to the key
                     - Additional custom attributes
        """
        ...


class APIKeyAuthenticator:
    """
        API Key Authentication implementation.
        
        This authenticator implements API Key Authentication by extracting
        keys from configurable locations (header, query parameter, or cookie)
        and validating them against a configured APIKeyStore.
        
        The authentication flow is:
        1. Extract API key from the configured location
        2. Validate the key against the APIKeyStore
        3. Return SUCCESS with context or FAILURE with error
        
        Example usage::
        
            key_store = MyAPIKeyStore()
            
            # Header-based API key (default)
            authenticator = APIKeyAuthenticator(key_store)
            
            # Query parameter-based API key
            authenticator = APIKeyAuthenticator(
                key_store,
                key_name="api_key",
                location=APIKeyLocation.QUERY
            )
            
            # Cookie-based API key
            authenticator = APIKeyAuthenticator(
                key_store,
                key_name="session_key",
                location=APIKeyLocation.COOKIE
            )
            
            result = await authenticator.authenticate(request)
            if result.status == AuthenticationStatus.SUCCESS:
                principal = result.context.principal
        
        :param key_store: The store for validating API keys.
        :param key_name: The name of the header/query param/cookie containing the key.
        :param location: Where to extract the API key from.
    """
    
    def __init__(
        self,
        key_store: APIKeyStore,
        key_name: str = "X-API-Key",
        location: APIKeyLocation = APIKeyLocation.HEADER
    ):
        """
            Initialize the APIKeyAuthenticator.
            
            :param key_store: The store for validating API keys.
            :param key_name: The name of the header/query param/cookie containing
                           the key. Defaults to "X-API-Key".
            :param location: Where to extract the API key from. Defaults to HEADER.
        """
        self._key_store = key_store
        self._key_name = key_name
        self._location = location
    
    @property
    def scheme(self) -> str:
        """
            Return the authentication scheme identifier.
            
            :returns: The string "APIKey".
        """
        return "APIKey"
    
    @property
    def key_name(self) -> str:
        """
            Return the configured key name.
            
            :returns: The key name string.
        """
        return self._key_name
    
    @property
    def location(self) -> APIKeyLocation:
        """
            Return the configured key location.
            
            :returns: The APIKeyLocation enum value.
        """
        return self._location
    
    def can_handle(self, request: Any) -> bool:
        """
            Check if this authenticator can handle the given request.
            
            This method checks if the request contains an API key at the
            configured location with the configured key name.
            
            :param request: The HTTP request object to examine.
            
            :returns: True if an API key is present at the configured location,
                     False otherwise.
        """
        return self._extract_key(request) is not None
    
    async def authenticate(self, request: Any) -> AuthenticationResult:
        """
            Attempt to authenticate the request using API key.
            
            This method:
            1. Extracts the API key from the configured location
            2. Validates the key against the APIKeyStore
            3. Returns the appropriate AuthenticationResult
            
            :param request: The HTTP request containing the API key.
            
            :returns: An AuthenticationResult with:
                     - SUCCESS and context if key is valid
                     - FAILURE with error if key is invalid or missing
        """
        api_key = self._extract_key(request)
        
        if api_key is None:
            return AuthenticationResult(
                status=AuthenticationStatus.FAILURE,
                error_code="missing_api_key",
                error_description="API key not provided"
            )
        
        # Validate the key against the store
        key_info = await self._key_store.validate_key(api_key)
        
        if key_info is None:
            return AuthenticationResult(
                status=AuthenticationStatus.FAILURE,
                error_code="invalid_api_key",
                error_description="Invalid API key"
            )
        
        # Create principal from key info
        principal = self._create_principal(api_key, key_info)
        
        return AuthenticationResult(
            status=AuthenticationStatus.SUCCESS,
            context=AuthenticationContext(
                principal=principal,
                scheme=self.scheme,
                attributes=key_info
            )
        )
    
    def _extract_key(self, request: Any) -> Optional[str]:
        """
            Extract the API key from the request at the configured location.
            
            :param request: The HTTP request object.
            
            :returns: The API key string or None if not present.
        """
        if self._location == APIKeyLocation.HEADER:
            return self._extract_from_header(request)
        elif self._location == APIKeyLocation.QUERY:
            return self._extract_from_query(request)
        elif self._location == APIKeyLocation.COOKIE:
            return self._extract_from_cookie(request)
        return None
    
    def _extract_from_header(self, request: Any) -> Optional[str]:
        """
            Extract the API key from an HTTP header.
            
            :param request: The HTTP request object.
            
            :returns: The API key string or None if not present.
        """
        # Handle dict-like request objects (e.g., test mocks)
        if isinstance(request, dict):
            headers = request.get("headers", {})
            if isinstance(headers, dict):
                # Try case-insensitive lookup
                for key, value in headers.items():
                    if key.lower() == self._key_name.lower():
                        return value if value else None
            return None
        
        # Handle request objects with headers attribute
        if hasattr(request, "headers"):
            headers = request.headers
            if isinstance(headers, dict):
                for key, value in headers.items():
                    if key.lower() == self._key_name.lower():
                        return value if value else None
            elif hasattr(headers, "get"):
                # Try exact match first, then case variations
                value = headers.get(self._key_name)
                if value is None:
                    value = headers.get(self._key_name.lower())
                return value if value else None
        
        return None
    
    def _extract_from_query(self, request: Any) -> Optional[str]:
        """
            Extract the API key from a query parameter.
            
            :param request: The HTTP request object.
            
            :returns: The API key string or None if not present.
        """
        # Handle dict-like request objects (e.g., test mocks)
        if isinstance(request, dict):
            query_params = request.get("query_params", {})
            if isinstance(query_params, dict):
                value = query_params.get(self._key_name)
                return value if value else None
            return None
        
        # Handle request objects with query_params attribute
        if hasattr(request, "query_params"):
            query_params = request.query_params
            if isinstance(query_params, dict):
                value = query_params.get(self._key_name)
                return value if value else None
            elif hasattr(query_params, "get"):
                value = query_params.get(self._key_name)
                return value if value else None
        
        return None
    
    def _extract_from_cookie(self, request: Any) -> Optional[str]:
        """
            Extract the API key from a cookie.
            
            :param request: The HTTP request object.
            
            :returns: The API key string or None if not present.
        """
        # Handle dict-like request objects (e.g., test mocks)
        if isinstance(request, dict):
            cookies = request.get("cookies", {})
            if isinstance(cookies, dict):
                value = cookies.get(self._key_name)
                return value if value else None
            return None
        
        # Handle request objects with cookies attribute
        if hasattr(request, "cookies"):
            cookies = request.cookies
            if isinstance(cookies, dict):
                value = cookies.get(self._key_name)
                return value if value else None
            elif hasattr(cookies, "get"):
                value = cookies.get(self._key_name)
                return value if value else None
        
        return None
    
    def _create_principal(
        self,
        api_key: str,
        key_info: Dict[str, Any]
    ) -> Principal:
        """
            Create a Principal from API key information.
            
            :param api_key: The API key string.
            :param key_info: The metadata associated with the key.
            
            :returns: A Principal representing the API key owner.
        """
        # Use client_id if available, otherwise use first 8 chars of key
        identifier = key_info.get("client_id", api_key[:8] if len(api_key) >= 8 else api_key)
        display_name = key_info.get("name")
        
        # Extract roles and permissions, ensuring they are sets
        roles_data = key_info.get("roles", [])
        permissions_data = key_info.get("permissions", [])
        
        roles: Set[str] = set(roles_data) if isinstance(roles_data, (list, set)) else set()
        permissions: Set[str] = set(permissions_data) if isinstance(permissions_data, (list, set)) else set()
        
        return Principal(
            identifier=identifier,
            display_name=display_name,
            roles=roles,
            permissions=permissions,
            attributes=key_info
        )


def extract_api_key(
    request: Any,
    key_name: str = "X-API-Key",
    location: APIKeyLocation = APIKeyLocation.HEADER
) -> Optional[str]:
    """
        Utility function to extract an API key from a request.
        
        This function provides a standalone way to extract API keys without
        creating an APIKeyAuthenticator instance.
        
        :param request: The HTTP request object.
        :param key_name: The name of the header/query param/cookie.
        :param location: Where to extract the API key from.
        
        :returns: The API key string or None if not present.
    """
    # Create a temporary authenticator just for extraction
    # We use a dummy store since we're only extracting, not validating
    class DummyStore:
        async def validate_key(self, api_key: str) -> Optional[Dict[str, Any]]:
            return None
    
    authenticator = APIKeyAuthenticator(
        key_store=DummyStore(),
        key_name=key_name,
        location=location
    )
    return authenticator._extract_key(request)
