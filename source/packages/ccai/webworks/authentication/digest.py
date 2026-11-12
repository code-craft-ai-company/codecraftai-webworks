"""
.. module:: digest
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: HTTP Digest Authentication implementation.

.. moduleauthor:: Code Craft AI LLC

This module provides the DigestAuthenticator class which implements HTTP Digest
Authentication as defined in RFC 7616. It provides more secure password-based
authentication without transmitting passwords in cleartext by using a
challenge-response mechanism with cryptographic hashes.
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


import hashlib
import hmac
import logging
import re
import secrets
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional, Protocol, runtime_checkable
from urllib.parse import urlsplit

from ccai.webworks.authentication.core import (
    AuthenticationContext,
    AuthenticationResult,
    AuthenticationStatus,
    Principal
)
from ccai.webworks.authentication.errors import (
    AuthenticationError,
    LoginThrottle,
    get_client_key
)


# Module-level logger for the Digest authenticator. Malformed headers
# and replay-protection failures are logged at warning so the
# operator can spot abuse.
logger = logging.getLogger(__name__)

# A digest response is the hexadecimal form of an MD5 or SHA-256 hash.
_HEX_DIGEST_PATTERN = re.compile(r"^[0-9A-Fa-f]{32,128}$")


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
    
    def record_count(self, nonce: str, count: int) -> int:
        """
            Record the nonce count a client used, keeping the highest seen.
            
            :param nonce: The nonce the count belongs to.
            :param count: The nonce count the client sent.
            
            :returns: The highest count recorded for the nonce, or 0 if
                      the nonce is not known.
        """
        if nonce in self._nonces:
            if count > self._nonces[nonce].count:
                self._nonces[nonce].count = count
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
        qop: str = "auth",
        login_throttle: Optional[LoginThrottle] = None
    ):
        """
            Initialize the DigestAuthenticator.
            
            :param identity_provider: The provider for validating credentials.
            :param realm: The authentication realm. Defaults to "Restricted".
            :param algorithm: The hash algorithm. Defaults to MD5.
            :param nonce_max_age: Maximum nonce age in seconds. Defaults to 300.
            :param opaque: Optional opaque value for challenges.
            :param qop: Quality of protection. Defaults to "auth". The
                        client must use exactly this value; an empty
                        string selects the legacy mode without qop, in
                        which every nonce is accepted only once.
            :param login_throttle: Optional :class:`LoginThrottle` applied
                                   to every credential check.
        """
        self._identity_provider = identity_provider
        self._realm = realm
        self._algorithm = algorithm
        self._nonce_store = NonceStore(max_age_seconds=nonce_max_age)
        self._opaque = opaque or secrets.token_hex(16)
        self._qop = qop
        self._login_throttle = login_throttle
    
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
        
        # The algorithm and quality of protection are chosen by the
        # server. A header that names anything else is refused instead
        # of being verified with whatever the client picked.
        if credentials.algorithm.upper() != self._algorithm.value.upper():
            logger.warning(
                "Digest auth: algorithm %r does not match configured %r",
                credentials.algorithm,
                self._algorithm.value,
            )
            return self._invalid_credentials()
        
        expected_qop = self._qop or None
        if (credentials.qop or None) != expected_qop:
            logger.warning(
                "Digest auth: qop %r does not match configured %r",
                credentials.qop,
                self._qop,
            )
            return self._invalid_credentials()
        
        if expected_qop is not None:
            if not credentials.nc or not credentials.cnonce:
                return self._bad_request("Missing nonce count or client nonce")
        
        # The signed uri must be the target of this request, otherwise a
        # captured header could be replayed against another URL.
        request_target = self._get_request_target(request)
        if not self._uri_matches_target(credentials.uri, request_target):
            logger.warning(
                "Digest auth: uri %r does not match request target %r",
                credentials.uri,
                request_target,
            )
            return self._invalid_credentials()
        
        # The response is a hex digest; anything else can never match
        # (and non-ASCII text cannot be compared in constant time).
        if _HEX_DIGEST_PATTERN.match(credentials.response) is None:
            return self._invalid_credentials()
        
        # Refuse the attempt while the client or the account is throttled
        client_key = get_client_key(request)
        if self._login_throttle is not None:
            throttle_error = self._login_throttle.check(
                client_key, credentials.username
            )
            if throttle_error is not None:
                return self._throttled(
                    throttle_error, client_key, credentials.username
                )
        
        # Get HA1 from identity provider
        ha1 = await self._identity_provider.get_ha1(
            credentials.username,
            credentials.realm,
            self._algorithm.value
        )
        
        is_authentic = False
        if ha1 is not None:
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
                algorithm=self._algorithm.value
            )
            
            # Compare responses with a constant-time comparison so an
            # attacker can't infer the correct hash byte-by-byte from
            # response-time variations. RFC 7616 response values are
            # lowercase hex, but normalize defensively in case a
            # client capitalizes them.
            client_response = credentials.response.lower()
            server_response = expected_response.lower()
            is_authentic = hmac.compare_digest(client_response, server_response)
        
        if self._login_throttle is not None:
            self._login_throttle.record(
                client_key, credentials.username, success=is_authentic
            )
        
        if not is_authentic:
            # One message for an unknown user and a wrong password, so
            # the response does not reveal which usernames exist.
            return self._invalid_credentials()
        
        # Replay protection
        if expected_qop is not None:
            # The nonce count must be higher than every count already
            # seen for this nonce.
            try:
                client_nc = int(credentials.nc, 16)
            except ValueError as exc:
                logger.warning(
                    "Digest auth: invalid nonce-count %r: %s",
                    credentials.nc,
                    exc,
                )
                return self._bad_request("Invalid nonce count format")
            
            server_nc = self._nonce_store.get_count(credentials.nonce)
            if client_nc <= server_nc:
                # Replay attack detected
                return AuthenticationResult(
                    status=AuthenticationStatus.FAILURE,
                    error_code="replay_detected",
                    error_description="Nonce count too low"
                )
            
            # Remember the highest count the client has used
            self._nonce_store.record_count(credentials.nonce, client_nc)
        else:
            # Without qop there is no nonce count, so a nonce is good
            # for exactly one request.
            if self._nonce_store.get_count(credentials.nonce) > 0:
                return self._challenge_response(stale=True)
            self._nonce_store.record_count(credentials.nonce, 1)
        
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
                    "algorithm": self._algorithm.value,
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
    
    def _get_request_target(self, request: Any) -> Optional[str]:
        """
            Extract the request target (path plus query string).
            
            :param request: The HTTP request object.
            
            :returns: The request target, or None when the request does
                      not expose its path.
        """
        path = None
        query_string = None
        
        if isinstance(request, dict):
            path = request.get("path")
            query_string = request.get("query_string")
        else:
            path = getattr(request, "path", None)
            query_string = getattr(request, "query_string", None)
        
        if not isinstance(path, str) or len(path) == 0:
            return None
        
        if isinstance(query_string, bytes):
            query_string = query_string.decode("utf-8", errors="replace")
        
        rtnval = path
        if isinstance(query_string, str) and len(query_string) > 0:
            rtnval = "{}?{}".format(path, query_string)
        
        return rtnval
    
    def _uri_matches_target(self, uri: str, request_target: Optional[str]) -> bool:
        """
            Check that the ``uri`` a client signed is the request target.
            
            The client may send the target in origin form
            (``/path?query``) or as an absolute URI; both are compared
            by path and query string.
            
            :param uri: The ``uri`` parameter of the Authorization header.
            :param request_target: The target of the request being
                                   authenticated, or None if unknown.
            
            :returns: True if they name the same target. False when the
                      request target is unknown.
        """
        if request_target is None:
            return False
        
        signed_target = uri
        if "://" in uri:
            parts = urlsplit(uri)
            signed_target = parts.path or "/"
            if parts.query:
                signed_target = "{}?{}".format(signed_target, parts.query)
        
        rtnval = hmac.compare_digest(
            signed_target.encode("utf-8"), request_target.encode("utf-8")
        )
        return rtnval
    
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
    
    def get_challenge(self, stale: bool = False) -> str:
        """
            Issue a fresh nonce and return the challenge that carries it.
            
            The authentication system calls this for requests without
            credentials, which is how a Digest client obtains its first
            nonce.
            
            :param stale: If True, indicates the nonce is stale.
            
            :returns: The ``WWW-Authenticate`` header value.
        """
        result = self._challenge_response(stale=stale)
        return result.challenge
    
    def _invalid_credentials(self) -> AuthenticationResult:
        """
            Create the response for credentials that do not verify.
            
            :returns: An AuthenticationResult with FAILURE status and one
                      generic message for every cause.
        """
        return AuthenticationResult(
            status=AuthenticationStatus.FAILURE,
            error_code="invalid_credentials",
            error_description="Invalid credentials"
        )
    
    def _throttled(
        self,
        error: AuthenticationError,
        client_key: Optional[str],
        username: str
    ) -> AuthenticationResult:
        """
            Create the response for an attempt refused by the login throttle.
            
            :param error: The throttling error from :class:`LoginThrottle`.
            :param client_key: The client key used for rate limiting.
            :param username: The account named by the attempt.
            
            :returns: An AuthenticationResult with FAILURE status carrying
                      the throttling error code and a ``Retry-After`` header.
        """
        logger.warning("Digest auth: attempt refused: %s", error.error_code)
        
        response_headers = {}
        retry_after = self._login_throttle.get_retry_after(client_key, username)
        if retry_after is not None:
            response_headers["Retry-After"] = str(retry_after)
        
        return AuthenticationResult(
            status=AuthenticationStatus.FAILURE,
            error_code=error.error_code,
            error_description=error.safe_message,
            response_headers=response_headers
        )
    
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
            f'algorithm={self._algorithm.value}'
        ]
        if self._qop:
            parts.append(f'qop="{self._qop}"')
        parts.append(f'opaque="{self._opaque}"')
        
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
