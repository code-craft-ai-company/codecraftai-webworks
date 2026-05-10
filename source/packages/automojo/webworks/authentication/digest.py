"""
.. module:: digest
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: HTTP Digest Authentication implementation.

.. moduleauthor:: Automation Mojo LLC

This module provides the DigestAuthenticator class which implements HTTP Digest
Authentication as defined in RFC 7616. It provides more secure password-based
authentication without transmitting passwords in cleartext by using a
challenge-response mechanism with cryptographic hashes.
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


import hashlib
import hmac
import logging
import os
import re
import secrets
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional, Protocol, runtime_checkable

from automojo.webworks.authentication.core import (
    AuthenticationContext,
    AuthenticationResult,
    AuthenticationStatus,
    Principal
)


# Module-level logger for the Digest authenticator. Malformed headers
# and replay-protection failures are logged at warning so the
# operator can spot abuse.
logger = logging.getLogger(__name__)


class DigestAlgorithm(Enum):
    """
        Supported hash algorithms for Digest authentication.
        
        :cvar MD5: MD5 hash algorithm (legacy, less secure).
        :cvar SHA256: SHA-256 hash algorithm (recommended).
    """
    
    MD5 = "MD5"
    SHA256 = "SHA-256"


@dataclass
class NonceData:
    """
        Data associated with a nonce for validation.
        
        :param nonce: The nonce string.
        :param created_at: Unix timestamp when the nonce was created.
        :param count: Expected nonce count for replay protection.
    """
    
    nonce: str
    created_at: float
    count: int = 0


@dataclass
class DigestCredentials:
    """
        Parsed Digest authentication credentials from Authorization header.
        
        :param username: The username from the credentials.
        :param realm: The authentication realm.
        :param nonce: The server-provided nonce.
        :param uri: The request URI.
        :param response: The computed response hash.
        :param algorithm: The hash algorithm used.
        :param cnonce: Client-provided nonce (optional).
        :param nc: Nonce count (optional).
        :param qop: Quality of protection (optional).
        :param opaque: Opaque value from server (optional).
    """
    
    username: str
    realm: str
    nonce: str
    uri: str
    response: str
    algorithm: str = "MD5"
    cnonce: Optional[str] = None
    nc: Optional[str] = None
    qop: Optional[str] = None
    opaque: Optional[str] = None


@runtime_checkable
class DigestIdentityProvider(Protocol):
    """
        Protocol for identity validation backends for Digest authentication.
        
        Unlike Basic authentication which receives the password directly,
        Digest authentication requires access to the HA1 hash (hash of
        username:realm:password) to validate the response.
    """
    
    async def get_ha1(
        self,
        username: str,
        realm: str,
        algorithm: str
    ) -> Optional[str]:
        """
            Get the HA1 hash for a user.
            
            HA1 = H(username:realm:password) where H is the hash function.
            
            :param username: The username to look up.
            :param realm: The authentication realm.
            :param algorithm: The hash algorithm ("MD5" or "SHA-256").
            
            :returns: The HA1 hash if user exists, None otherwise.
        """
        ...
    
    async def get_principal(
        self,
        username: str,
        realm: str
    ) -> Optional[Principal]:
        """
            Retrieve a principal by username and realm.
            
            :param username: The username to look up.
            :param realm: The authentication realm.
            
            :returns: The Principal if found, None otherwise.
        """
        ...


class NonceStore:
    """
        In-memory store for nonce management.
        
        This store tracks issued nonces and their metadata for validation
        and replay attack prevention.
    """
    
    def __init__(self, max_age_seconds: float = 300.0):
        """
            Initialize the nonce store.
            
            :param max_age_seconds: Maximum age of a nonce in seconds.
                                   Defaults to 300 (5 minutes).
        """
        self._nonces: Dict[str, NonceData] = {}
        self._max_age_seconds = max_age_seconds
    
    def create_nonce(self) -> str:
        """
            Create a new nonce and store it.
            
            :returns: The generated nonce string.
        """
        # Generate a secure random nonce
        timestamp = time.time()
        random_bytes = secrets.token_hex(16)
        nonce = f"{timestamp}:{random_bytes}"
        
        # Store nonce data
        self._nonces[nonce] = NonceData(
            nonce=nonce,
            created_at=timestamp,
            count=0
        )
        
        # Clean up old nonces
        self._cleanup_expired()
        
        return nonce
    
    def validate_nonce(self, nonce: str) -> tuple:
        """
            Validate a nonce and check if it's stale.
            
            :param nonce: The nonce to validate.
            
            :returns: A tuple of (is_valid, is_stale).
                     is_valid: True if nonce exists and is not expired.
                     is_stale: True if nonce is expired but was valid.
        """
        if nonce not in self._nonces:
            return (False, False)
        
        nonce_data = self._nonces[nonce]
        age = time.time() - nonce_data.created_at
        
        if age > self._max_age_seconds:
            # Nonce is stale
            return (False, True)
        
        return (True, False)
    
    def increment_count(self, nonce: str) -> int:
        """
            Increment and return the nonce count.
            
            :param nonce: The nonce to increment.
            
            :returns: The new count value.
        """
        if nonce in self._nonces:
            self._nonces[nonce].count += 1
            return self._nonces[nonce].count
        return 0
    
    def get_count(self, nonce: str) -> int:
        """
            Get the current count for a nonce.
            
            :param nonce: The nonce to look up.
            
            :returns: The current count, or 0 if nonce not found.
        """
        if nonce in self._nonces:
            return self._nonces[nonce].count
        return 0
    
    def invalidate(self, nonce: str) -> bool:
        """
            Invalidate a nonce.
            
            :param nonce: The nonce to invalidate.
            
            :returns: True if nonce was found and removed, False otherwise.
        """
        if nonce in self._nonces:
            del self._nonces[nonce]
            return True
        return False
    
    def _cleanup_expired(self) -> None:
        """
            Remove expired nonces from the store.
        """
        current_time = time.time()
        expired = [
            nonce for nonce, data in self._nonces.items()
            if current_time - data.created_at > self._max_age_seconds * 2
        ]
        for nonce in expired:
            del self._nonces[nonce]
    
    @property
    def max_age_seconds(self) -> float:
        """
            Return the maximum nonce age in seconds.
            
            :returns: The max age configuration value.
        """
        return self._max_age_seconds


class DigestAuthenticator:
    """
        HTTP Digest Authentication implementation.
        
        This authenticator implements HTTP Digest Authentication as defined
        in RFC 7616. It uses a challenge-response mechanism where the server
        sends a nonce, and the client responds with a hash computed from
        the credentials and nonce.
        
        The authentication flow is:
        1. Client sends request without credentials
        2. Server responds with 401 and WWW-Authenticate header containing nonce
        3. Client computes response hash and sends Authorization header
        4. Server validates the response hash
        
        Example usage::
        
            identity_provider = MyDigestIdentityProvider()
            authenticator = DigestAuthenticator(identity_provider, realm="MyApp")
            
            result = await authenticator.authenticate(request)
            if result.status == AuthenticationStatus.SUCCESS:
                principal = result.context.principal
        
        :param identity_provider: The provider for validating credentials.
        :param realm: The authentication realm.
        :param algorithm: The hash algorithm to use (MD5 or SHA-256).
        :param nonce_max_age: Maximum age of nonces in seconds.
        :param opaque: Optional opaque value to include in challenges.
        :param qop: Quality of protection ("auth" or "auth-int").
    """
    
    def __init__(
        self,
        identity_provider: DigestIdentityProvider,
        realm: str = "Restricted",
        algorithm: DigestAlgorithm = DigestAlgorithm.MD5,
        nonce_max_age: float = 300.0,
        opaque: Optional[str] = None,
        qop: str = "auth"
    ):
        """
            Initialize the DigestAuthenticator.
            
            :param identity_provider: The provider for validating credentials.
            :param realm: The authentication realm. Defaults to "Restricted".
            :param algorithm: The hash algorithm. Defaults to MD5.
            :param nonce_max_age: Maximum nonce age in seconds. Defaults to 300.
            :param opaque: Optional opaque value for challenges.
            :param qop: Quality of protection. Defaults to "auth".
        """
        self._identity_provider = identity_provider
        self._realm = realm
        self._algorithm = algorithm
        self._nonce_store = NonceStore(max_age_seconds=nonce_max_age)
        self._opaque = opaque or secrets.token_hex(16)
        self._qop = qop
    
    @property
    def scheme(self) -> str:
        """
            Return the authentication scheme identifier.
            
            :returns: The string "Digest".
        """
        return "Digest"
    
    @property
    def realm(self) -> str:
        """
            Return the authentication realm.
            
            :returns: The configured realm string.
        """
        return self._realm
    
    @property
    def algorithm(self) -> DigestAlgorithm:
        """
            Return the hash algorithm.
            
            :returns: The configured DigestAlgorithm.
        """
        return self._algorithm
    
    @property
    def nonce_store(self) -> NonceStore:
        """
            Return the nonce store.
            
            :returns: The NonceStore instance.
        """
        return self._nonce_store
    
    def can_handle(self, request: Any) -> bool:
        """
            Check if this authenticator can handle the given request.
            
            This method checks if the request contains an Authorization
            header that starts with "Digest " (case-insensitive).
            
            :param request: The HTTP request object to examine.
            
            :returns: True if the request has a Digest Authorization header,
                     False otherwise.
        """
        auth_header = self._get_authorization_header(request)
        if auth_header is None:
            return False
        return auth_header.lower().startswith("digest ")
    
    async def authenticate(self, request: Any) -> AuthenticationResult:
        """
            Attempt to authenticate the request using Digest authentication.
            
            This method:
            1. Extracts the Authorization header
            2. Parses the Digest credentials
            3. Validates the nonce
            4. Computes and compares the response hash
            5. Returns the appropriate AuthenticationResult
            
            :param request: The HTTP request containing credentials.
            
            :returns: An AuthenticationResult with:
                     - SUCCESS and context if credentials are valid
                     - FAILURE with error if credentials are invalid
                     - CHALLENGE if no credentials or stale nonce
        """
        auth_header = self._get_authorization_header(request)
        
        # No Authorization header - issue challenge
        if auth_header is None or auth_header.strip() == "":
            return self._challenge_response()
        
        # Check if this is a Digest auth header
        if not auth_header.lower().startswith("digest "):
            return AuthenticationResult(status=AuthenticationStatus.SKIP)
        
        # Parse the Digest credentials
        try:
            credentials = self._parse_digest_header(auth_header)
        except ValueError as e:
            logger.warning("Digest auth: malformed Authorization header: %s", e)
            return self._bad_request(str(e))
        
        # Validate realm matches
        if credentials.realm != self._realm:
            return AuthenticationResult(
                status=AuthenticationStatus.FAILURE,
                error_code="invalid_realm",
                error_description="Realm mismatch"
            )
        
        # Validate nonce
        is_valid, is_stale = self._nonce_store.validate_nonce(credentials.nonce)
        
        if not is_valid:
            if is_stale:
                # Nonce is stale - issue new challenge with stale=true
                return self._challenge_response(stale=True)
            else:
                # Unknown nonce
                return self._challenge_response()
        
        # Get HA1 from identity provider
        ha1 = await self._identity_provider.get_ha1(
            credentials.username,
            credentials.realm,
            credentials.algorithm
        )
        
        if ha1 is None:
            return AuthenticationResult(
                status=AuthenticationStatus.FAILURE,
                error_code="invalid_credentials",
                error_description="Invalid username"
            )
        
        # Get request method and URI
        method = self._get_request_method(request)
        uri = credentials.uri
        
        # Compute expected response
        expected_response = self._compute_response(
            ha1=ha1,
            nonce=credentials.nonce,
            nc=credentials.nc,
            cnonce=credentials.cnonce,
            qop=credentials.qop,
            method=method,
            uri=uri,
            algorithm=credentials.algorithm
        )
        
        # Compare responses with a constant-time comparison so an
        # attacker can't infer the correct hash byte-by-byte from
        # response-time variations. RFC 7616 response values are
        # lowercase hex, but normalize defensively in case a
        # client capitalizes them.
        client_response = credentials.response.lower()
        server_response = expected_response.lower()
        if not hmac.compare_digest(client_response, server_response):
            return AuthenticationResult(
                status=AuthenticationStatus.FAILURE,
                error_code="invalid_credentials",
                error_description="Invalid response hash"
            )
        
        # Validate nonce count if qop is used
        if credentials.qop and credentials.nc:
            try:
                client_nc = int(credentials.nc, 16)
                server_nc = self._nonce_store.get_count(credentials.nonce)
                
                if client_nc <= server_nc:
                    # Replay attack detected
                    return AuthenticationResult(
                        status=AuthenticationStatus.FAILURE,
                        error_code="replay_detected",
                        error_description="Nonce count too low"
                    )
                
                # Update server count
                self._nonce_store.increment_count(credentials.nonce)
            except ValueError as exc:
                logger.warning(
                    "Digest auth: invalid nonce-count %r: %s",
                    credentials.nc,
                    exc,
                )
                return self._bad_request("Invalid nonce count format")
        
        # Get principal from identity provider
        principal = await self._identity_provider.get_principal(
            credentials.username,
            credentials.realm
        )
        
        if principal is None:
            # Create a basic principal if provider doesn't return one
            principal = Principal(
                identifier=credentials.username,
                display_name=credentials.username
            )
        
        # Success - return context with principal
        return AuthenticationResult(
            status=AuthenticationStatus.SUCCESS,
            context=AuthenticationContext(
                principal=principal,
                scheme=self.scheme,
                attributes={
                    "realm": credentials.realm,
                    "algorithm": credentials.algorithm,
                    "qop": credentials.qop
                }
            )
        )
    
    def _get_authorization_header(self, request: Any) -> Optional[str]:
        """
            Extract the Authorization header from the request.
            
            :param request: The HTTP request object.
            
            :returns: The Authorization header value or None if not present.
        """
        # Handle dict-like request objects
        if isinstance(request, dict):
            headers = request.get("headers", {})
            if isinstance(headers, dict):
                for key, value in headers.items():
                    if key.lower() == "authorization":
                        return value
            return None
        
        # Handle request objects with headers attribute
        if hasattr(request, "headers"):
            headers = request.headers
            if isinstance(headers, dict):
                for key, value in headers.items():
                    if key.lower() == "authorization":
                        return value
            elif hasattr(headers, "get"):
                return headers.get("Authorization") or headers.get("authorization")
        
        return None
    
    def _get_request_method(self, request: Any) -> str:
        """
            Extract the HTTP method from the request.
            
            :param request: The HTTP request object.
            
            :returns: The HTTP method string (e.g., "GET", "POST").
        """
        # Handle dict-like request objects
        if isinstance(request, dict):
            return request.get("method", "GET")
        
        # Handle request objects with method attribute
        if hasattr(request, "method"):
            return request.method
        
        return "GET"
    
    def _parse_digest_header(self, auth_header: str) -> DigestCredentials:
        """
            Parse the Digest Authorization header into credentials.
            
            :param auth_header: The Authorization header value.
            
            :returns: A DigestCredentials object.
            
            :raises ValueError: If the header format is invalid.
        """
        # Remove "Digest " prefix
        if not auth_header.lower().startswith("digest "):
            raise ValueError("Not a Digest authorization header")
        
        params_str = auth_header[7:]  # Remove "Digest " prefix
        
        # Parse key="value" pairs
        params = self._parse_digest_params(params_str)
        
        # Validate required fields. RFC 7616 requires each of
        # these to be a non-empty value; an empty quoted string
        # (e.g. ``username=""``) is treated as missing rather
        # than passed through to the hash-comparison step. Without
        # this guard a malformed header would advance through the
        # rest of the flow and fail later with a less specific
        # error, leaking timing information about which fields
        # were valid.
        required_fields = ["username", "realm", "nonce", "uri", "response"]
        for field in required_fields:
            if field not in params:
                raise ValueError(f"Missing required field: {field}")
            if len(params[field]) == 0:
                raise ValueError(f"Missing required field: {field}")

        return DigestCredentials(
            username=params["username"],
            realm=params["realm"],
            nonce=params["nonce"],
            uri=params["uri"],
            response=params["response"],
            algorithm=params.get("algorithm", "MD5"),
            cnonce=params.get("cnonce"),
            nc=params.get("nc"),
            qop=params.get("qop"),
            opaque=params.get("opaque")
        )
    
    def _parse_digest_params(self, params_str: str) -> Dict[str, str]:
        """
            Parse Digest authentication parameters.
            
            :param params_str: The parameters string from the header.
            
            :returns: A dictionary of parameter names to values.
        """
        params = {}
        
        # Pattern to match key="value" or key=value (value can contain hyphens)
        pattern = r'(\w+)=(?:"([^"]*)"|([^\s,]+))'
        
        for match in re.finditer(pattern, params_str):
            key = match.group(1)
            # Value is either in group 2 (quoted) or group 3 (unquoted)
            value = match.group(2) if match.group(2) is not None else match.group(3)
            params[key] = value
        
        return params
    
    def _compute_response(
        self,
        ha1: str,
        nonce: str,
        nc: Optional[str],
        cnonce: Optional[str],
        qop: Optional[str],
        method: str,
        uri: str,
        algorithm: str
    ) -> str:
        """
            Compute the expected Digest response hash.
            
            :param ha1: The HA1 hash (H(username:realm:password)).
            :param nonce: The server nonce.
            :param nc: The nonce count (if qop is used).
            :param cnonce: The client nonce (if qop is used).
            :param qop: Quality of protection.
            :param method: The HTTP method.
            :param uri: The request URI.
            :param algorithm: The hash algorithm.
            
            :returns: The computed response hash.
        """
        # Select hash function
        hash_func = self._get_hash_function(algorithm)
        
        # Compute HA2 = H(method:uri)
        ha2_input = f"{method}:{uri}"
        ha2 = hash_func(ha2_input.encode()).hexdigest()
        
        # Compute response
        if qop:
            # RFC 2617 with qop
            response_input = f"{ha1}:{nonce}:{nc}:{cnonce}:{qop}:{ha2}"
        else:
            # RFC 2069 (legacy)
            response_input = f"{ha1}:{nonce}:{ha2}"
        
        return hash_func(response_input.encode()).hexdigest()
    
    def _get_hash_function(self, algorithm: str):
        """
            Get the hash function for the specified algorithm.
            
            :param algorithm: The algorithm name ("MD5" or "SHA-256").
            
            :returns: The hash function.
        """
        if algorithm.upper() == "SHA-256":
            return hashlib.sha256
        else:
            return hashlib.md5
    
    def _challenge_response(self, stale: bool = False) -> AuthenticationResult:
        """
            Create a challenge response for unauthenticated requests.
            
            :param stale: If True, indicates the nonce is stale.
            
            :returns: An AuthenticationResult with CHALLENGE status.
        """
        nonce = self._nonce_store.create_nonce()
        
        # Build WWW-Authenticate header
        parts = [
            f'realm="{self._realm}"',
            f'nonce="{nonce}"',
            f'algorithm={self._algorithm.value}',
            f'qop="{self._qop}"',
            f'opaque="{self._opaque}"'
        ]
        
        if stale:
            parts.append("stale=true")
        
        challenge = "Digest " + ", ".join(parts)
        
        return AuthenticationResult(
            status=AuthenticationStatus.CHALLENGE,
            challenge=challenge
        )
    
    def _bad_request(self, message: str) -> AuthenticationResult:
        """
            Create a bad request response for malformed credentials.
            
            :param message: The error message describing the problem.
            
            :returns: An AuthenticationResult with FAILURE status.
        """
        return AuthenticationResult(
            status=AuthenticationStatus.FAILURE,
            error_code="bad_request",
            error_description=message
        )


def compute_ha1(
    username: str,
    realm: str,
    password: str,
    algorithm: str = "MD5"
) -> str:
    """
        Compute the HA1 hash for Digest authentication.
        
        HA1 = H(username:realm:password)
        
        This utility function is useful for identity providers that need
        to store the HA1 hash instead of the plaintext password.
        
        :param username: The username.
        :param realm: The authentication realm.
        :param password: The password.
        :param algorithm: The hash algorithm ("MD5" or "SHA-256").
        
        :returns: The HA1 hash as a hexadecimal string.
    """
    if algorithm.upper() == "SHA-256":
        hash_func = hashlib.sha256
    else:
        hash_func = hashlib.md5
    
    ha1_input = f"{username}:{realm}:{password}"
    return hash_func(ha1_input.encode()).hexdigest()


def create_digest_auth_header(
    username: str,
    realm: str,
    nonce: str,
    uri: str,
    response: str,
    algorithm: str = "MD5",
    cnonce: Optional[str] = None,
    nc: Optional[str] = None,
    qop: Optional[str] = None,
    opaque: Optional[str] = None
) -> str:
    """
        Create a Digest Authorization header value.
        
        This utility function creates the full Authorization header
        value for Digest authentication.
        
        :param username: The username.
        :param realm: The authentication realm.
        :param nonce: The server-provided nonce.
        :param uri: The request URI.
        :param response: The computed response hash.
        :param algorithm: The hash algorithm.
        :param cnonce: Client nonce (optional).
        :param nc: Nonce count (optional).
        :param qop: Quality of protection (optional).
        :param opaque: Opaque value (optional).
        
        :returns: The complete Authorization header value.
    """
    parts = [
        f'username="{username}"',
        f'realm="{realm}"',
        f'nonce="{nonce}"',
        f'uri="{uri}"',
        f'response="{response}"',
        f'algorithm={algorithm}'
    ]
    
    if qop:
        parts.append(f'qop={qop}')
    if cnonce:
        parts.append(f'cnonce="{cnonce}"')
    if nc:
        parts.append(f'nc={nc}')
    if opaque:
        parts.append(f'opaque="{opaque}"')
    
    return "Digest " + ", ".join(parts)


def compute_digest_response(
    username: str,
    realm: str,
    password: str,
    nonce: str,
    uri: str,
    method: str = "GET",
    algorithm: str = "MD5",
    cnonce: Optional[str] = None,
    nc: Optional[str] = None,
    qop: Optional[str] = None
) -> str:
    """
        Compute the Digest authentication response hash.
        
        This utility function computes the response hash that should be
        sent in the Authorization header.
        
        :param username: The username.
        :param realm: The authentication realm.
        :param password: The password.
        :param nonce: The server-provided nonce.
        :param uri: The request URI.
        :param method: The HTTP method.
        :param algorithm: The hash algorithm.
        :param cnonce: Client nonce (if qop is used).
        :param nc: Nonce count (if qop is used).
        :param qop: Quality of protection.
        
        :returns: The computed response hash.
    """
    # Select hash function
    if algorithm.upper() == "SHA-256":
        hash_func = hashlib.sha256
    else:
        hash_func = hashlib.md5
    
    # Compute HA1 = H(username:realm:password)
    ha1 = compute_ha1(username, realm, password, algorithm)
    
    # Compute HA2 = H(method:uri)
    ha2_input = f"{method}:{uri}"
    ha2 = hash_func(ha2_input.encode()).hexdigest()
    
    # Compute response
    if qop:
        response_input = f"{ha1}:{nonce}:{nc}:{cnonce}:{qop}:{ha2}"
    else:
        response_input = f"{ha1}:{nonce}:{ha2}"
    
    return hash_func(response_input.encode()).hexdigest()
