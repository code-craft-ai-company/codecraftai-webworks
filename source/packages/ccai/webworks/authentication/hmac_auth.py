"""
.. module:: hmac_auth
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: HMAC Request Signing Authentication implementation.

.. moduleauthor:: Code Craft AI LLC

This module provides the HMACAuthenticator class which implements HMAC-based
request signing authentication. It validates request signatures to verify
request integrity and authenticate API calls.
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


import hashlib
import hmac
import logging
import math
import re
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol, Union, runtime_checkable

from ccai.webworks.authentication.core import (
    AuthenticationContext,
    AuthenticationResult,
    AuthenticationStatus,
    Principal
)


# Module-level logger for the HMAC authenticator. Malformed signing
# headers and bad timestamps are logged at warning so a clock-skew
# wave from a misconfigured client doesn't go unnoticed.
logger = logging.getLogger(__name__)

# A signature is the hexadecimal form of an HMAC-SHA256 or HMAC-SHA512.
_HEX_SIGNATURE_PATTERN = re.compile(r"^[0-9A-Fa-f]{64,128}$")

# Hash constructions by the algorithm name carried in the header.
_HMAC_HASH_FUNCTIONS = {
    "HMAC-SHA256": hashlib.sha256,
    "HMAC-SHA512": hashlib.sha512,
}


class HMACAlgorithm(Enum):
    """
        Supported HMAC algorithms for request signing.
        
        :cvar HMAC_SHA256: HMAC with SHA-256 hash algorithm.
        :cvar HMAC_SHA512: HMAC with SHA-512 hash algorithm.
    """
    
    HMAC_SHA256 = "HMAC-SHA256"
    HMAC_SHA512 = "HMAC-SHA512"


@dataclass
class HMACCredentials:
    """
        Parsed HMAC authentication credentials from Authorization header.
        
        :param key_id: The identifier for the signing key.
        :param signature: The computed HMAC signature.
        :param timestamp: The request timestamp.
        :param algorithm: The HMAC algorithm used.
        :param signed_headers: List of headers included in the signature.
    """
    
    key_id: str
    signature: str
    timestamp: str
    algorithm: str = "HMAC-SHA256"
    signed_headers: List[str] = field(default_factory=list)


@runtime_checkable
class HMACKeyStore(Protocol):
    """
        Protocol for HMAC key storage and validation.
        
        Implementations must provide methods to retrieve the secret key
        for a given key ID and to get principal information.
    """
    
    async def get_secret(self, key_id: str) -> Optional[str]:
        """
            Get the secret key for a key ID.
            
            :param key_id: The identifier for the signing key.
            
            :returns: The secret key if found, None otherwise.
        """
    
    async def get_principal(self, key_id: str) -> Optional[Principal]:
        """
            Retrieve a principal by key ID.
            
            :param key_id: The identifier for the signing key.
            
            :returns: The Principal if found, None otherwise.
        """


class HMACAuthenticator:
    """
        HMAC Request Signing Authentication implementation.
        
        This authenticator validates request signatures in the Authorization
        header to verify request integrity and authenticate API calls.
        
        The authentication flow is:
        1. Client computes HMAC signature over canonical request string
        2. Client sends Authorization header with signature and metadata
        3. Server reconstructs canonical request and computes expected signature
        4. Server compares signatures and validates timestamp
        
        Example usage::
        
            key_store = MyHMACKeyStore()
            authenticator = HMACAuthenticator(
                key_store,
                timestamp_window=300,
                signed_headers=["host", "content-type"]
            )
            
            result = await authenticator.authenticate(request)
            if result.status == AuthenticationStatus.SUCCESS:
                principal = result.context.principal
        
        :param key_store: The store for retrieving signing keys.
        :param timestamp_window: Maximum age of requests in seconds.
        :param signed_headers: List of headers to include in signature.
        :param algorithm: The default HMAC algorithm to use.
    """
    
    def __init__(
        self,
        key_store: HMACKeyStore,
        timestamp_window: float = 300.0,
        signed_headers: Optional[List[str]] = None,
        algorithm: HMACAlgorithm = HMACAlgorithm.HMAC_SHA256
    ):
        """
            Initialize the HMACAuthenticator.
            
            :param key_store: The store for retrieving signing keys.
            :param timestamp_window: Maximum age of requests in seconds.
                                    Defaults to 300 (5 minutes).
            :param signed_headers: Headers every request must sign. A
                                  request whose ``SignedHeaders`` leaves
                                  one of them out is refused; the client
                                  may sign more. Defaults to
                                  ["host", "date"]. An empty list
                                  requires no header.
            :param algorithm: The default HMAC algorithm. Defaults to HMAC-SHA256.
        """
        self._key_store = key_store
        self._timestamp_window = timestamp_window
        if signed_headers is None:
            signed_headers = ["host", "date"]
        self._signed_headers = [
            header_name.lower() for header_name in signed_headers
        ]
        self._algorithm = algorithm
        
        # Signatures accepted inside the timestamp window, mapped to the
        # time after which they can no longer be replayed anyway.
        self._seen_signatures: Dict[str, float] = {}
        self._seen_signatures_lock = threading.Lock()
    
    @property
    def scheme(self) -> str:
        """
            Return the authentication scheme identifier.
            
            :returns: The string "HMAC".
        """
        return "HMAC"
    
    @property
    def requires_body(self) -> bool:
        """
            Whether this authenticator needs the request body.
            
            The signature covers a digest of the body, so the middleware
            buffers the body before authenticating.
            
            :returns: Always True.
        """
        return True
    
    @property
    def timestamp_window(self) -> float:
        """
            Return the timestamp validation window in seconds.
            
            :returns: The configured timestamp window.
        """
        return self._timestamp_window
    
    @property
    def signed_headers(self) -> List[str]:
        """
            Return the list of headers included in signature.
            
            :returns: The configured signed headers list.
        """
        return self._signed_headers.copy()
    
    @property
    def algorithm(self) -> HMACAlgorithm:
        """
            Return the default HMAC algorithm.
            
            :returns: The configured HMACAlgorithm.
        """
        return self._algorithm
    
    def can_handle(self, request: Any) -> bool:
        """
            Check if this authenticator can handle the given request.
            
            This method checks if the request contains an Authorization
            header that starts with "HMAC " (case-insensitive).
            
            :param request: The HTTP request object to examine.
            
            :returns: True if the request has an HMAC Authorization header,
                     False otherwise.
        """
        auth_header = self._get_authorization_header(request)
        if auth_header is None:
            return False
        return auth_header.upper().startswith("HMAC ")
    
    async def authenticate(self, request: Any) -> AuthenticationResult:
        """
            Attempt to authenticate the request using HMAC signature.
            
            This method:
            1. Extracts the Authorization header
            2. Parses the HMAC credentials
            3. Validates the timestamp
            4. Reconstructs the canonical request string
            5. Computes and compares the signature
            6. Returns the appropriate AuthenticationResult
            
            :param request: The HTTP request containing credentials.
            
            :returns: An AuthenticationResult with:
                     - SUCCESS and context if signature is valid
                     - FAILURE with error if signature is invalid
                     - SKIP if this authenticator doesn't apply
        """
        auth_header = self._get_authorization_header(request)
        
        # No Authorization header - skip
        if auth_header is None or auth_header.strip() == "":
            return AuthenticationResult(status=AuthenticationStatus.SKIP)
        
        # Check if this is an HMAC auth header
        if not auth_header.upper().startswith("HMAC "):
            return AuthenticationResult(status=AuthenticationStatus.SKIP)
        
        # Parse the HMAC credentials
        try:
            credentials = self._parse_hmac_header(auth_header)
        except ValueError as e:
            logger.warning("HMAC auth: malformed Authorization header: %s", e)
            return self._bad_request(str(e))
        
        # Validate timestamp
        timestamp_valid, timestamp_error = self._validate_timestamp(
            credentials.timestamp
        )
        if not timestamp_valid:
            return AuthenticationResult(
                status=AuthenticationStatus.FAILURE,
                error_code="invalid_timestamp",
                error_description=timestamp_error
            )
        
        # The signature is a hex digest; anything else can never match
        # (and non-ASCII text cannot be compared in constant time).
        if _HEX_SIGNATURE_PATTERN.match(credentials.signature) is None:
            return self._bad_request("Invalid signature format")
        
        if credentials.algorithm.upper() not in _HMAC_HASH_FUNCTIONS:
            return self._bad_request("Unsupported HMAC algorithm")
        
        # Every header this server is configured to protect must be in
        # the set the client signed.
        missing_headers = [
            header_name for header_name in self._signed_headers
            if header_name.lower() not in credentials.signed_headers
        ]
        if len(missing_headers) > 0:
            logger.warning(
                "HMAC auth: required headers not signed: %s", missing_headers
            )
            return AuthenticationResult(
                status=AuthenticationStatus.FAILURE,
                error_code="invalid_signature",
                error_description="Required headers are not signed"
            )
        
        # Get secret from key store
        secret = await self._key_store.get_secret(credentials.key_id)
        
        if secret is None:
            return AuthenticationResult(
                status=AuthenticationStatus.FAILURE,
                error_code="invalid_key",
                error_description="Unknown key ID"
            )
        
        # Reconstruct canonical request string
        canonical_string = self._build_canonical_string(
            request,
            credentials.timestamp,
            credentials.signed_headers
        )
        
        # Compute expected signature
        expected_signature = self._compute_signature(
            secret,
            canonical_string,
            credentials.algorithm
        )
        
        # Compare signatures (constant-time comparison)
        if not hmac.compare_digest(
            credentials.signature.lower(),
            expected_signature.lower()
        ):
            return AuthenticationResult(
                status=AuthenticationStatus.FAILURE,
                error_code="invalid_signature",
                error_description="Signature verification failed"
            )
        
        # A valid signature is accepted once: a second request carrying
        # it inside the timestamp window is a replay.
        if not self._remember_signature(credentials.signature.lower()):
            logger.warning(
                "HMAC auth: replayed signature for key %r", credentials.key_id
            )
            return AuthenticationResult(
                status=AuthenticationStatus.FAILURE,
                error_code="replay_detected",
                error_description="Request signature has already been used"
            )
        
        # Get principal from key store
        principal = await self._key_store.get_principal(credentials.key_id)
        
        if principal is None:
            # Create a basic principal if store doesn't return one
            principal = Principal(
                identifier=credentials.key_id,
                display_name=credentials.key_id
            )
        
        # Success - return context with principal
        return AuthenticationResult(
            status=AuthenticationStatus.SUCCESS,
            context=AuthenticationContext(
                principal=principal,
                scheme=self.scheme,
                attributes={
                    "key_id": credentials.key_id,
                    "algorithm": credentials.algorithm,
                    "signed_headers": credentials.signed_headers,
                    "timestamp": credentials.timestamp
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
    
    def _get_request_path(self, request: Any) -> str:
        """
            Extract the request path from the request.
            
            :param request: The HTTP request object.
            
            :returns: The request path string.
        """
        # Handle dict-like request objects
        if isinstance(request, dict):
            return request.get("path", "/")
        
        # Handle request objects with path attribute
        if hasattr(request, "path"):
            return request.path
        
        return "/"
    
    def _get_request_headers(self, request: Any) -> Dict[str, str]:
        """
            Extract headers from the request as a dictionary.
            
            Accepts a plain dict, any mapping-like object that offers
            ``items()`` (the framework ``Headers`` class) and the ASGI
            list of ``(name, value)`` byte pairs.
            
            :param request: The HTTP request object.
            
            :returns: A dictionary of lower-case header names to values.
        """
        headers = None
        if isinstance(request, dict):
            headers = request.get("headers", {})
        elif hasattr(request, "headers"):
            headers = request.headers
        
        if headers is None:
            return {}
        
        pairs = []
        if hasattr(headers, "items"):
            pairs = list(headers.items())
        elif isinstance(headers, (list, tuple)):
            pairs = [pair for pair in headers if len(pair) >= 2]
        
        rtnval: Dict[str, str] = {}
        for pair in pairs:
            name = pair[0]
            value = pair[1]
            if isinstance(name, bytes):
                name = name.decode("latin-1")
            if isinstance(value, bytes):
                value = value.decode("latin-1")
            rtnval[str(name).lower()] = value
        
        return rtnval
    
    def _get_request_query_string(self, request: Any) -> str:
        """
            Extract the raw query string from the request.
            
            :param request: The HTTP request object.
            
            :returns: The query string without the leading ``?``.
        """
        query_string = None
        if isinstance(request, dict):
            query_string = request.get("query_string")
        else:
            query_string = getattr(request, "query_string", None)
        
        if isinstance(query_string, bytes):
            query_string = query_string.decode("utf-8", errors="replace")
        
        if not isinstance(query_string, str):
            return ""
        
        return query_string
    
    def _get_request_body(self, request: Any) -> bytes:
        """
            Extract the raw body from the request.
            
            :param request: The HTTP request object.
            
            :returns: The request body bytes (empty when there is none).
        """
        body = None
        if isinstance(request, dict):
            body = request.get("body")
        else:
            body = getattr(request, "body", None)
        
        if isinstance(body, str):
            body = body.encode("utf-8")
        
        if not isinstance(body, (bytes, bytearray)):
            return b""
        
        return bytes(body)
    
    def _remember_signature(self, signature: str) -> bool:
        """
            Record an accepted signature for the timestamp window.
            
            :param signature: The verified signature (lower-case hex).
            
            :returns: True if the signature was not seen before, False if
                      it is a replay.
        """
        now = time.time()
        
        with self._seen_signatures_lock:
            # Forget signatures whose timestamp can no longer be valid
            expired = [
                seen for seen, forget_at in self._seen_signatures.items()
                if forget_at < now
            ]
            for seen in expired:
                del self._seen_signatures[seen]
            
            if signature in self._seen_signatures:
                return False
            
            # A timestamp is accepted from window seconds in the past to
            # window seconds in the future, so remember it for both.
            self._seen_signatures[signature] = now + (2 * self._timestamp_window)
        
        return True
    
    def _parse_hmac_header(self, auth_header: str) -> HMACCredentials:
        """
            Parse the HMAC Authorization header into credentials.
            
            Expected format:
            HMAC KeyId="key-id", Signature="signature", Timestamp="timestamp",
                 Algorithm="HMAC-SHA256", SignedHeaders="host;date"
            
            :param auth_header: The Authorization header value.
            
            :returns: An HMACCredentials object.
            
            :raises ValueError: If the header format is invalid.
        """
        # Remove "HMAC " prefix (case-insensitive)
        if not auth_header.upper().startswith("HMAC "):
            raise ValueError("Not an HMAC authorization header")
        
        params_str = auth_header[5:]  # Remove "HMAC " prefix
        
        # Parse key="value" pairs
        params = self._parse_hmac_params(params_str)
        
        # Validate required fields
        required_fields = ["keyid", "signature", "timestamp"]
        for field_name in required_fields:
            if field_name not in params:
                raise ValueError(f"Missing required field: {field_name}")
        
        # Parse signed headers (semicolon-separated)
        signed_headers_str = params.get("signedheaders", "")
        signed_headers = []
        if signed_headers_str:
            signed_headers = [h.strip().lower() for h in signed_headers_str.split(";") if h.strip()]
        
        return HMACCredentials(
            key_id=params["keyid"],
            signature=params["signature"],
            timestamp=params["timestamp"],
            algorithm=params.get("algorithm", "HMAC-SHA256"),
            signed_headers=signed_headers
        )
    
    def _parse_hmac_params(self, params_str: str) -> Dict[str, str]:
        """
            Parse HMAC authentication parameters.
            
            :param params_str: The parameters string from the header.
            
            :returns: A dictionary of parameter names to values.
        """
        params = {}
        
        # Pattern to match Key="value" or Key=value
        pattern = r'(\w+)=(?:"([^"]*)"|([^\s,]+))'
        
        for match in re.finditer(pattern, params_str):
            key = match.group(1).lower()
            # Value is either in group 2 (quoted) or group 3 (unquoted)
            value = match.group(2) if match.group(2) is not None else match.group(3)
            params[key] = value
        
        return params
    
    def _validate_timestamp(self, timestamp_str: str) -> tuple:
        """
            Validate the request timestamp.
            
            :param timestamp_str: The timestamp string (Unix timestamp).
            
            :returns: A tuple of (is_valid, error_message).
        """
        try:
            timestamp = float(timestamp_str)
        except ValueError as exc:
            logger.warning(
                "HMAC auth: invalid timestamp %r: %s", timestamp_str, exc
            )
            return (False, "Invalid timestamp format")
        
        # float() accepts "nan" and "inf"; every comparison against NaN
        # is false, which would skip the freshness check below.
        if not math.isfinite(timestamp):
            logger.warning("HMAC auth: non-finite timestamp %r", timestamp_str)
            return (False, "Invalid timestamp format")
        
        current_time = time.time()
        age = abs(current_time - timestamp)
        
        if age > self._timestamp_window:
            return (False, "Timestamp outside allowed window")
        
        return (True, None)
    
    def _build_canonical_string(
        self,
        request: Any,
        timestamp: str,
        signed_headers: List[str]
    ) -> str:
        """
            Build the canonical request string for signature computation.
            
            See :func:`build_hmac_canonical_string` for the format.
            
            :param request: The HTTP request object.
            :param timestamp: The request timestamp.
            :param signed_headers: List of headers to include.
            
            :returns: The canonical request string.
        """
        rtnval = build_hmac_canonical_string(
            method=self._get_request_method(request),
            path=self._get_request_path(request),
            timestamp=timestamp,
            headers=self._get_request_headers(request),
            signed_headers=signed_headers,
            query_string=self._get_request_query_string(request),
            body=self._get_request_body(request)
        )
        return rtnval
    
    def _compute_signature(
        self,
        secret: str,
        canonical_string: str,
        algorithm: str
    ) -> str:
        """
            Compute the HMAC signature.
            
            :param secret: The secret key.
            :param canonical_string: The canonical request string.
            :param algorithm: The HMAC algorithm.
            
            :returns: The computed signature as a hexadecimal string.
        """
        rtnval = _sign_canonical_string(secret, canonical_string, algorithm)
        return rtnval
    
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


def build_hmac_canonical_string(
    method: str,
    path: str,
    timestamp: str,
    headers: Dict[str, str],
    signed_headers: List[str],
    query_string: Union[str, bytes] = "",
    body: Union[str, bytes] = b""
) -> str:
    """
        Build the canonical request string that is signed.
        
        The canonical string format is::
        
            METHOD\n
            PATH\n
            QUERY-STRING\n
            TIMESTAMP\n
            SHA256-HEX-OF-BODY\n
            header1:value1\n
            header2:value2\n
            ...
        
        The query string is the raw query string of the request (empty
        when there is none) and the body digest is the SHA-256 of the
        raw body bytes, so neither can be changed without invalidating
        the signature.
        
        :param method: The HTTP method.
        :param path: The request path.
        :param timestamp: The request timestamp.
        :param headers: Dictionary of request headers.
        :param signed_headers: List of headers to include in signature.
        :param query_string: The raw query string without the leading ``?``.
        :param body: The raw request body.
        
        :returns: The canonical request string.
    """
    if isinstance(query_string, bytes):
        query_string = query_string.decode("utf-8", errors="replace")
    
    if isinstance(body, str):
        body = body.encode("utf-8")
    
    body_digest = hashlib.sha256(body).hexdigest()
    
    parts = [
        method.upper(),
        path,
        query_string,
        timestamp,
        body_digest
    ]
    
    # Add signed headers in order
    normalized_headers = {k.lower(): v for k, v in headers.items()}
    for header_name in sorted(signed_headers):
        header_value = normalized_headers.get(header_name.lower(), "")
        parts.append(f"{header_name.lower()}:{header_value}")
    
    return "\n".join(parts)


def _sign_canonical_string(secret: str, canonical_string: str, algorithm: str) -> str:
    """
        Compute the HMAC of a canonical request string.
        
        :param secret: The secret key.
        :param canonical_string: The canonical request string.
        :param algorithm: The HMAC algorithm name.
        
        :returns: The signature as a hexadecimal string.
        
        :raises ValueError: If the algorithm is not supported.
    """
    hash_func = _HMAC_HASH_FUNCTIONS.get(algorithm.upper())
    if hash_func is None:
        raise ValueError(f"Unsupported HMAC algorithm: {algorithm}")
    
    signature = hmac.HMAC(
        secret.encode("utf-8"),
        canonical_string.encode("utf-8"),
        hash_func
    )
    
    return signature.hexdigest()


def compute_hmac_signature(
    secret: str,
    method: str,
    path: str,
    timestamp: str,
    headers: Dict[str, str],
    signed_headers: List[str],
    algorithm: str = "HMAC-SHA256",
    query_string: Union[str, bytes] = "",
    body: Union[str, bytes] = b""
) -> str:
    """
        Compute the HMAC signature for a request.
        
        This utility function computes the signature that should be
        sent in the Authorization header.
        
        :param secret: The secret key.
        :param method: The HTTP method.
        :param path: The request path.
        :param timestamp: The request timestamp.
        :param headers: Dictionary of request headers.
        :param signed_headers: List of headers to include in signature.
        :param algorithm: The HMAC algorithm.
        :param query_string: The raw query string without the leading ``?``.
        :param body: The raw request body.
        
        :returns: The computed signature as a hexadecimal string.
    """
    canonical_string = build_hmac_canonical_string(
        method=method,
        path=path,
        timestamp=timestamp,
        headers=headers,
        signed_headers=signed_headers,
        query_string=query_string,
        body=body
    )
    
    rtnval = _sign_canonical_string(secret, canonical_string, algorithm)
    return rtnval


def create_hmac_auth_header(
    key_id: str,
    signature: str,
    timestamp: str,
    algorithm: str = "HMAC-SHA256",
    signed_headers: Optional[List[str]] = None
) -> str:
    """
        Create an HMAC Authorization header value.
        
        This utility function creates the full Authorization header
        value for HMAC authentication.
        
        :param key_id: The identifier for the signing key.
        :param signature: The computed HMAC signature.
        :param timestamp: The request timestamp.
        :param algorithm: The HMAC algorithm.
        :param signed_headers: List of headers included in signature.
        
        :returns: The complete Authorization header value.
    """
    parts = [
        f'KeyId="{key_id}"',
        f'Signature="{signature}"',
        f'Timestamp="{timestamp}"',
        f'Algorithm="{algorithm}"'
    ]
    
    if signed_headers:
        headers_str = ";".join(signed_headers)
        parts.append(f'SignedHeaders="{headers_str}"')
    
    return "HMAC " + ", ".join(parts)
