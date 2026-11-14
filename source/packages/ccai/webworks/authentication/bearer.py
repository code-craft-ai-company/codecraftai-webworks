"""
.. module:: bearer
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Bearer Token Authentication implementation with JWT support.

.. moduleauthor:: Code Craft AI LLC

This module provides the BearerAuthenticator class which implements Bearer
Token Authentication as defined in RFC 6750. It supports JWT token validation
with configurable signing algorithms, as well as opaque token validation
via a TokenStore.
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


import base64
import hashlib
import hmac
import inspect
import json
import logging
import math
import secrets
import threading
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable

from ccai.webworks.authentication.core import (
    AuthenticationContext,
    AuthenticationResult,
    AuthenticationStatus,
    Principal
)


# Module-level logger for the JWT helpers / BearerAuthenticator. We
# log token validation failures at warning level so an operator can
# distinguish a misconfigured server (every token failing) from
# normal expired-token traffic without resorting to packet captures.
logger = logging.getLogger(__name__)


@runtime_checkable
class TokenStore(Protocol):
    """
        Protocol for token storage and validation.
        
        A TokenStore is responsible for storing and validating opaque tokens
        (non-JWT tokens) and returning their associated claims if valid.
    """
    
    async def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
            Validate a token and return its claims if valid.
            
            :param token: The token string to validate.
            
            :returns: A dictionary of claims if the token is valid, None otherwise.
        """
    
    async def store_token(
        self,
        token: str,
        claims: Dict[str, Any],
        expires_in: int
    ) -> None:
        """
            Store a token with its claims.
            
            :param token: The token string to store.
            :param claims: The claims associated with the token.
            :param expires_in: Time in seconds until the token expires.
        """
    
    async def revoke_token(self, token: str) -> bool:
        """
            Revoke a token.
            
            :param token: The token string to revoke.
            
            :returns: True if the token was revoked, False if not found.
        """


@runtime_checkable
class TokenRevocationList(Protocol):
    """
        Protocol for a list of revoked token identifiers.
        
        Signed JWTs stay valid until they expire, so revoking one means
        remembering its identifier until then. The token endpoints record
        revocations here and :class:`BearerAuthenticator`, the refresh
        grant and introspection consult it. Implementations may return
        awaitables from both methods (for a shared store such as Redis).
    """
    
    def revoke(self, token_id: str, expires_at: Optional[float] = None) -> None:
        """
            Record a token identifier as revoked.
            
            :param token_id: The identifier from :func:`get_token_revocation_id`.
            :param expires_at: Unix time at which the token expires and
                               the entry may be forgotten, or None.
        """
    
    def is_revoked(self, token_id: str) -> bool:
        """
            Check whether a token identifier has been revoked.
            
            :param token_id: The identifier from :func:`get_token_revocation_id`.
            
            :returns: True if the token has been revoked.
        """


class InMemoryTokenRevocationList:
    """
        In-memory :class:`TokenRevocationList`.
        
        Entries are forgotten once the token they name has expired. The
        list is private to one process: a deployment with several workers
        needs a shared implementation, otherwise a token revoked in one
        worker is still accepted by the others.
        
        :param max_entries: Maximum number of revocations remembered.
    """
    
    DEFAULT_MAX_ENTRIES: int = 100000
    
    def __init__(self, max_entries: Optional[int] = None):
        """
            Initialize the revocation list.
            
            :param max_entries: Maximum number of revocations remembered.
                                Defaults to :attr:`DEFAULT_MAX_ENTRIES`.
        """
        if max_entries is None:
            max_entries = self.DEFAULT_MAX_ENTRIES
        
        self._max_entries = max_entries
        self._entries: Dict[str, Optional[float]] = {}
        self._lock = threading.Lock()
        return
    
    def revoke(self, token_id: str, expires_at: Optional[float] = None) -> None:
        """
            Record a token identifier as revoked.
            
            :param token_id: The identifier from :func:`get_token_revocation_id`.
            :param expires_at: Unix time at which the token expires and
                               the entry may be forgotten, or None to
                               remember it for the life of the process.
        """
        with self._lock:
            if len(self._entries) >= self._max_entries:
                self._sweep_expired()
            
            if len(self._entries) >= self._max_entries and token_id not in self._entries:
                # Still full of live entries. Make room by dropping the
                # entry closest to its natural expiry and say so: a
                # dropped revocation re-validates that token.
                victim = min(
                    self._entries,
                    key=lambda key: (
                        self._entries[key] is None,
                        self._entries[key] or 0.0
                    )
                )
                del self._entries[victim]
                logger.warning(
                    "Token revocation list is full (%d entries); the oldest "
                    "revocation was dropped. Configure a shared revocation "
                    "list sized for the deployment.",
                    self._max_entries,
                )
            
            self._entries[token_id] = expires_at
        return
    
    def is_revoked(self, token_id: str) -> bool:
        """
            Check whether a token identifier has been revoked.
            
            :param token_id: The identifier from :func:`get_token_revocation_id`.
            
            :returns: True if the token has been revoked.
        """
        with self._lock:
            rtnval = token_id in self._entries
        return rtnval
    
    def get_entry_count(self) -> int:
        """
            Get the number of revocations currently remembered.
            
            :returns: The number of entries.
        """
        with self._lock:
            rtnval = len(self._entries)
        return rtnval
    
    def _sweep_expired(self) -> None:
        """
            Forget revocations whose token has expired. The caller holds
            the lock.
        """
        now = time.time()
        expired = [
            token_id for token_id, expires_at in self._entries.items()
            if expires_at is not None and expires_at < now
        ]
        for token_id in expired:
            del self._entries[token_id]
        return


# Revocation list shared by BearerAuthenticator and the token endpoints
# when neither is given one. Revoking a token at a blueprint endpoint
# therefore makes the authenticator refuse it without further wiring.
_default_revocation_list = InMemoryTokenRevocationList()


def get_default_revocation_list() -> InMemoryTokenRevocationList:
    """
        Get the process-wide revocation list.
        
        :class:`BearerAuthenticator` and the authentication blueprints
        use it when they are not configured with a list of their own. It
        is private to one process; deployments with several workers
        configure a shared :class:`TokenRevocationList` on both sides.
        
        :returns: The process-wide :class:`InMemoryTokenRevocationList`.
    """
    return _default_revocation_list


def get_token_revocation_id(token: str, claims: Optional[Dict[str, Any]] = None) -> str:
    """
        Get the identifier under which a token is revoked.
        
        The ``jti`` claim is used when the token carries one. Tokens
        without it are identified by the SHA-256 digest of the token
        string, so any token can be revoked.
        
        :param token: The encoded token string.
        :param claims: The decoded claims, when available.
        
        :returns: The revocation identifier.
    """
    if claims is not None:
        token_id = claims.get("jti")
        if isinstance(token_id, str) and len(token_id) > 0:
            return token_id
    
    digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
    rtnval = "sha256:{}".format(digest)
    return rtnval


def generate_token_id() -> str:
    """
        Generate a unique ``jti`` claim value for an issued token.
        
        :returns: A random URL-safe identifier.
    """
    rtnval = secrets.token_urlsafe(16)
    return rtnval


class JWTError(Exception):
    """
        Base exception for JWT-related errors.
    """
    pass


class JWTExpiredError(JWTError):
    """
        Exception raised when a JWT token has expired.
    """
    pass


class JWTInvalidSignatureError(JWTError):
    """
        Exception raised when a JWT signature is invalid.
    """
    pass


class JWTInvalidClaimsError(JWTError):
    """
        Exception raised when JWT claims are invalid.
    """
    pass


class JWTDecodeError(JWTError):
    """
        Exception raised when JWT decoding fails.
    """
    pass


def _base64url_decode(data: str) -> bytes:
    """
        Decode a Base64URL-encoded string.
        
        JWT uses Base64URL encoding which differs from standard Base64
        by using '-' instead of '+' and '_' instead of '/'.
        
        :param data: The Base64URL-encoded string.
        
        :returns: The decoded bytes.
        
        :raises JWTDecodeError: If decoding fails.
    """
    # Add padding if necessary
    padding = 4 - len(data) % 4
    if padding != 4:
        data += '=' * padding
    
    # Replace URL-safe characters with standard Base64 characters
    data = data.replace('-', '+').replace('_', '/')
    
    try:
        return base64.b64decode(data)
    except Exception as exc:
        raise JWTDecodeError(f"Invalid Base64URL encoding: {exc}")


def _base64url_encode(data: bytes) -> str:
    """
        Encode bytes as a Base64URL string.
        
        :param data: The bytes to encode.
        
        :returns: The Base64URL-encoded string without padding.
    """
    encoded = base64.b64encode(data).decode('utf-8')
    # Replace standard Base64 characters with URL-safe characters
    encoded = encoded.replace('+', '-').replace('/', '_')
    # Remove padding
    return encoded.rstrip('=')


def decode_jwt(
    token: str,
    secret: str,
    algorithms: List[str],
    issuer: Optional[str] = None,
    audience: Optional[str] = None,
    verify_exp: bool = True,
    leeway: float = 0.0
) -> Dict[str, Any]:
    """
        Decode and validate a JWT token.
        
        This function decodes a JWT token, verifies its signature using
        the provided secret and algorithms, and validates standard claims
        (exp, nbf, iss, aud) if configured.
        
        When *verify_exp* is True the ``exp`` claim is required: a token
        without an expiration would otherwise be valid forever. The
        ``nbf`` (not before) claim is honoured whenever it is present.
        
        :param token: The JWT token string.
        :param secret: The secret key for signature verification.
        :param algorithms: List of allowed algorithms (e.g., ["HS256"]).
        :param issuer: Expected issuer claim value (optional).
        :param audience: Expected audience claim value (optional).
        :param verify_exp: Whether to require and verify the expiration
                           claim and to verify the not-before claim.
        :param leeway: Clock skew in seconds tolerated when checking
                       ``exp`` and ``nbf``.
        
        :returns: The decoded payload claims.
        
        :raises JWTDecodeError: If the token format is invalid.
        :raises JWTInvalidSignatureError: If the signature is invalid.
        :raises JWTExpiredError: If the token has expired.
        :raises JWTInvalidClaimsError: If claims validation fails.
    """
    # Split token into parts
    parts = token.split('.')
    if len(parts) != 3:
        raise JWTDecodeError("Invalid JWT format: expected 3 parts")
    
    header_b64, payload_b64, signature_b64 = parts
    
    # Decode header. ValueError covers both invalid JSON and bytes
    # that are not UTF-8 (UnicodeDecodeError).
    try:
        header_bytes = _base64url_decode(header_b64)
        header = json.loads(header_bytes.decode('utf-8'))
    except ValueError as exc:
        raise JWTDecodeError(f"Invalid JWT header: {exc}")
    
    if not isinstance(header, dict):
        raise JWTDecodeError("Invalid JWT header: expected a JSON object")
    
    # Verify algorithm
    token_alg = header.get('alg')
    if token_alg not in algorithms:
        raise JWTInvalidSignatureError(
            f"Algorithm '{token_alg}' not in allowed algorithms: {algorithms}"
        )
    
    # Verify signature
    signing_input = f"{header_b64}.{payload_b64}"
    expected_signature = _compute_signature(signing_input, secret, token_alg)
    
    try:
        actual_signature = _base64url_decode(signature_b64)
    except JWTDecodeError:
        raise JWTInvalidSignatureError("Invalid signature encoding")
    
    if not hmac.compare_digest(expected_signature, actual_signature):
        raise JWTInvalidSignatureError("Signature verification failed")
    
    # Decode payload
    try:
        payload_bytes = _base64url_decode(payload_b64)
        payload = json.loads(payload_bytes.decode('utf-8'))
    except ValueError as exc:
        raise JWTDecodeError(f"Invalid JWT payload: {exc}")
    
    if not isinstance(payload, dict):
        raise JWTDecodeError("Invalid JWT payload: expected a JSON object")
    
    if verify_exp:
        now = time.time()
        
        # Verify expiration. The claim is required: a token without
        # one never expires.
        if 'exp' not in payload:
            raise JWTInvalidClaimsError("Missing 'exp' claim")
        exp = payload['exp']
        if not _is_finite_number(exp):
            raise JWTInvalidClaimsError("Invalid 'exp' claim: must be a number")
        if now > exp + leeway:
            raise JWTExpiredError("Token has expired")
        
        # Verify not-before
        if 'nbf' in payload:
            nbf = payload['nbf']
            if not _is_finite_number(nbf):
                raise JWTInvalidClaimsError("Invalid 'nbf' claim: must be a number")
            if now < nbf - leeway:
                raise JWTInvalidClaimsError("Token is not yet valid")
    
    # Verify issuer
    if issuer is not None:
        token_issuer = payload.get('iss')
        if token_issuer != issuer:
            raise JWTInvalidClaimsError(
                f"Invalid issuer: expected '{issuer}', got '{token_issuer}'"
            )
    
    # Verify audience
    if audience is not None:
        token_audience = payload.get('aud')
        # Audience can be a string or list of strings
        if isinstance(token_audience, list):
            if audience not in token_audience:
                raise JWTInvalidClaimsError(
                    f"Invalid audience: '{audience}' not in {token_audience}"
                )
        elif token_audience != audience:
            raise JWTInvalidClaimsError(
                f"Invalid audience: expected '{audience}', got '{token_audience}'"
            )
    
    return payload


def _is_finite_number(value: Any) -> bool:
    """
        Check that a claim value is a finite JSON number.
        
        Booleans are rejected although Python treats them as integers,
        and NaN / infinity are rejected because every comparison
        against them is false.
        
        :param value: The claim value to check.
        
        :returns: True if the value is a finite int or float.
    """
    if isinstance(value, bool):
        return False
    if not isinstance(value, (int, float)):
        return False
    rtnval = math.isfinite(value)
    return rtnval


def _compute_signature(signing_input: str, secret: str, algorithm: str) -> bytes:
    """
        Compute the signature for a JWT.
        
        :param signing_input: The header.payload string to sign.
        :param secret: The secret key.
        :param algorithm: The signing algorithm.
        
        :returns: The signature bytes.
        
        :raises JWTError: If the algorithm is not supported.
    """
    if algorithm == 'HS256':
        return hmac.HMAC(
            secret.encode('utf-8'),
            signing_input.encode('utf-8'),
            hashlib.sha256
        ).digest()
    elif algorithm == 'HS384':
        return hmac.HMAC(
            secret.encode('utf-8'),
            signing_input.encode('utf-8'),
            hashlib.sha384
        ).digest()
    elif algorithm == 'HS512':
        return hmac.HMAC(
            secret.encode('utf-8'),
            signing_input.encode('utf-8'),
            hashlib.sha512
        ).digest()
    else:
        raise JWTError(f"Unsupported algorithm: {algorithm}")


def encode_jwt(
    payload: Dict[str, Any],
    secret: str,
    algorithm: str = 'HS256'
) -> str:
    """
        Encode a payload as a JWT token.
        
        This utility function creates a JWT token from a payload dictionary
        using the specified secret and algorithm.
        
        :param payload: The claims to include in the token.
        :param secret: The secret key for signing.
        :param algorithm: The signing algorithm (default: HS256).
        
        :returns: The encoded JWT token string.
    """
    # Create header
    header = {'typ': 'JWT', 'alg': algorithm}
    header_b64 = _base64url_encode(json.dumps(header).encode('utf-8'))
    
    # Encode payload
    payload_b64 = _base64url_encode(json.dumps(payload).encode('utf-8'))
    
    # Create signature
    signing_input = f"{header_b64}.{payload_b64}"
    signature = _compute_signature(signing_input, secret, algorithm)
    signature_b64 = _base64url_encode(signature)
    
    return f"{header_b64}.{payload_b64}.{signature_b64}"


def extract_bearer_token(auth_header: str) -> Optional[str]:
    """
        Extract the token from a Bearer Authorization header.
        
        :param auth_header: The Authorization header value.
        
        :returns: The token string if valid Bearer format, None otherwise.
    """
    if not auth_header:
        return None
    
    parts = auth_header.split(' ', 1)
    if len(parts) != 2:
        return None
    
    scheme, token = parts
    if scheme.lower() != 'bearer':
        return None
    
    token = token.strip()
    if not token:
        return None
    
    return token


class BearerAuthenticator:
    """
        Bearer Token Authentication with JWT support.
        
        This authenticator implements Bearer Token Authentication as defined
        in RFC 6750. It supports both JWT token validation with configurable
        signing algorithms and opaque token validation via a TokenStore.
        
        The authentication flow is:
        1. Check for Authorization header with "Bearer" scheme
        2. Extract the token from the header
        3. If JWT secret is configured, attempt JWT validation
        4. If JWT validation fails or is not configured, try TokenStore
        5. Return SUCCESS with context or FAILURE with error
        
        Example usage::
        
            # JWT-only authentication
            authenticator = BearerAuthenticator(
                jwt_secret="my-secret-key",
                jwt_algorithms=["HS256"],
                jwt_issuer="my-app"
            )
            
            # TokenStore-only authentication
            authenticator = BearerAuthenticator(token_store=my_token_store)
            
            # Both JWT and TokenStore (JWT tried first)
            authenticator = BearerAuthenticator(
                token_store=my_token_store,
                jwt_secret="my-secret-key"
            )
        
        :param token_store: Optional TokenStore for opaque token validation.
        :param jwt_secret: Optional secret key for JWT signature verification.
        :param jwt_algorithms: List of allowed JWT algorithms.
        :param jwt_issuer: Expected JWT issuer claim value.
        :param jwt_audience: Expected JWT audience claim value.
        :param revocation_list: Optional list of revoked token identifiers.
        :param required_token_type: Value the ``token_type`` claim must have
                                    when a JWT carries one.
        :param leeway: Clock skew in seconds tolerated for ``exp`` / ``nbf``.
        :param realm: Realm named in the ``WWW-Authenticate`` challenge.
    """
    
    # Claim that tells access tokens from refresh tokens, and the value
    # a token must carry to be accepted as an access token.
    TOKEN_TYPE_CLAIM: str = "token_type"
    ACCESS_TOKEN_TYPE: str = "access"
    
    def __init__(
        self,
        token_store: Optional[TokenStore] = None,
        jwt_secret: Optional[str] = None,
        jwt_algorithms: Optional[List[str]] = None,
        jwt_issuer: Optional[str] = None,
        jwt_audience: Optional[str] = None,
        revocation_list: Optional[TokenRevocationList] = None,
        required_token_type: Optional[str] = ACCESS_TOKEN_TYPE,
        leeway: float = 0.0,
        realm: str = "Restricted"
    ):
        """
            Initialize the BearerAuthenticator.

            At least one of ``token_store`` or ``jwt_secret`` MUST
            be supplied. An authenticator with neither has no way
            to validate any Bearer token and would silently reject
            every request — a footgun configuration that's almost
            always a deployment bug. Fail loudly at construction
            time instead.

            :param token_store: Optional TokenStore for opaque token validation.
            :param jwt_secret: Optional secret key for JWT signature verification.
            :param jwt_algorithms: List of allowed JWT algorithms. Defaults to ["HS256"].
            :param jwt_issuer: Expected JWT issuer claim value.
            :param jwt_audience: Expected JWT audience claim value.
            :param revocation_list: Optional :class:`TokenRevocationList`.
                                    A JWT whose identifier is on the list is
                                    rejected. Defaults to the process-wide
                                    list (:func:`get_default_revocation_list`)
                                    that the token endpoints also revoke
                                    into, so revoked tokens stop working
                                    without further wiring.
            :param required_token_type: Value the ``token_type`` claim must
                                        have when a JWT carries one. Defaults
                                        to ``"access"`` so a refresh token
                                        signed with the same secret is not
                                        accepted as an access token. None
                                        disables the check.
            :param leeway: Clock skew in seconds tolerated when checking the
                           ``exp`` and ``nbf`` claims.
            :param realm: Realm named in the ``WWW-Authenticate`` challenge.

            :raises ValueError: When neither ``token_store`` nor
                                ``jwt_secret`` is supplied.
        """
        if token_store is None and jwt_secret is None:
            raise ValueError(
                "BearerAuthenticator requires at least one of "
                "'token_store' or 'jwt_secret'. An authenticator "
                "with neither cannot validate any token and would "
                "silently reject every Bearer request."
            )
        self._token_store = token_store
        self._jwt_secret = jwt_secret
        self._jwt_algorithms = jwt_algorithms or ["HS256"]
        self._jwt_issuer = jwt_issuer
        self._jwt_audience = jwt_audience
        if revocation_list is None:
            revocation_list = get_default_revocation_list()
        self._revocation_list = revocation_list
        self._required_token_type = required_token_type
        self._leeway = leeway
        self._realm = realm
    
    @property
    def scheme(self) -> str:
        """
            Return the authentication scheme identifier.
            
            :returns: The string "Bearer".
        """
        return "Bearer"
    
    @property
    def revocation_list(self) -> TokenRevocationList:
        """
            Return the revocation list the authenticator consults.
            
            :returns: The :class:`TokenRevocationList`.
        """
        return self._revocation_list
    
    def get_challenge(self) -> str:
        """
            Return the challenge sent to clients that presented no
            usable credentials (RFC 6750 section 3).
            
            :returns: The ``WWW-Authenticate`` header value.
        """
        return f'Bearer realm="{self._realm}"'
    
    def can_handle(self, request: Any) -> bool:
        """
            Check if this authenticator can handle the given request.
            
            This method checks if the request contains an Authorization
            header that starts with "Bearer " (case-insensitive).
            
            :param request: The HTTP request object to examine.
            
            :returns: True if the request has a Bearer Authorization header,
                     False otherwise.
        """
        auth_header = self._get_authorization_header(request)
        if auth_header is None:
            return False
        return auth_header.lower().startswith("bearer ")
    
    async def authenticate(self, request: Any) -> AuthenticationResult:
        """
            Attempt to authenticate the request using Bearer token.
            
            This method:
            1. Extracts the Authorization header
            2. Extracts the token from the header
            3. Attempts JWT validation if configured
            4. Falls back to TokenStore validation if configured
            5. Returns the appropriate AuthenticationResult
            
            :param request: The HTTP request containing the token.
            
            :returns: An AuthenticationResult with:
                     - SUCCESS and context if token is valid
                     - FAILURE with error if token is invalid
                     - SKIP if no Bearer header present
        """
        auth_header = self._get_authorization_header(request)
        
        # No Authorization header - skip
        if auth_header is None:
            return AuthenticationResult(status=AuthenticationStatus.SKIP)
        
        # Extract token from header
        token = extract_bearer_token(auth_header)
        if token is None:
            return AuthenticationResult(status=AuthenticationStatus.SKIP)
        
        # Try JWT validation first if configured
        if self._jwt_secret is not None:
            result = self._validate_jwt(token)
            if result.status == AuthenticationStatus.SUCCESS:
                # A valid signature is not enough: the token may have
                # been revoked (logout) before it expired.
                is_revoked = await self._is_revoked(
                    token, result.context.attributes
                )
                if is_revoked:
                    return AuthenticationResult(
                        status=AuthenticationStatus.FAILURE,
                        error_code="invalid_token",
                        error_description="The access token has been revoked"
                    )
                return result
            if result.status != AuthenticationStatus.SKIP:
                return result
        
        # Fall back to token store if configured
        if self._token_store is not None:
            claims = await self._token_store.validate_token(token)
            if claims is not None:
                return self._create_success_result(claims)
        
        # No validation method succeeded
        return AuthenticationResult(
            status=AuthenticationStatus.FAILURE,
            error_code="invalid_token",
            error_description="The access token is invalid"
        )
    
    def _get_authorization_header(self, request: Any) -> Optional[str]:
        """
            Extract the Authorization header from the request.
            
            This method handles different request object types by checking
            for common header access patterns.
            
            :param request: The HTTP request object.
            
            :returns: The Authorization header value or None if not present.
        """
        # Handle dict-like request objects (e.g., test mocks)
        if isinstance(request, dict):
            headers = request.get("headers", {})
            if isinstance(headers, dict):
                # Try case-insensitive lookup
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
                # Try common header access methods
                return headers.get("Authorization") or headers.get("authorization")
        
        return None
    
    async def _is_revoked(self, token: str, claims: Dict[str, Any]) -> bool:
        """
            Check the revocation list for a token.
            
            :param token: The encoded token string.
            :param claims: The decoded token claims.
            
            :returns: True if a revocation list is configured and the
                      token is on it.
        """
        if self._revocation_list is None:
            return False
        
        token_id = get_token_revocation_id(token, claims)
        is_revoked = self._revocation_list.is_revoked(token_id)
        if inspect.isawaitable(is_revoked):
            is_revoked = await is_revoked
        
        rtnval = bool(is_revoked)
        return rtnval
    
    def _validate_jwt(self, token: str) -> AuthenticationResult:
        """
            Validate a JWT token.
            
            :param token: The JWT token string.
            
            :returns: An AuthenticationResult with the validation outcome.
        """
        try:
            claims = decode_jwt(
                token=token,
                secret=self._jwt_secret,
                algorithms=self._jwt_algorithms,
                issuer=self._jwt_issuer,
                audience=self._jwt_audience,
                leeway=self._leeway
            )
            
            # Only access tokens authenticate a request. Refresh tokens
            # are signed with the same secret and live much longer.
            if self._required_token_type is not None:
                token_type = claims.get(self.TOKEN_TYPE_CLAIM)
                if token_type is not None and token_type != self._required_token_type:
                    logger.warning(
                        "Bearer auth: rejected JWT with token_type %r", token_type
                    )
                    return AuthenticationResult(
                        status=AuthenticationStatus.FAILURE,
                        error_code="invalid_token",
                        error_description="The token is not an access token"
                    )
            
            return self._create_success_result(claims)
        
        except JWTExpiredError as exc:
            logger.warning("Bearer auth: JWT expired: %s", exc)
            return AuthenticationResult(
                status=AuthenticationStatus.FAILURE,
                error_code="invalid_token",
                error_description="The access token has expired"
            )

        except JWTInvalidSignatureError as exc:
            # An invalid signature is the canonical sign of either
            # client tampering or a misconfigured signing secret on
            # the server. Operator should always see this in the
            # journal so a sudden surge of signature failures is
            # actionable.
            logger.warning("Bearer auth: JWT invalid signature: %s", exc)
            return AuthenticationResult(
                status=AuthenticationStatus.FAILURE,
                error_code="invalid_token",
                error_description=str(exc)
            )

        except JWTInvalidClaimsError as exc:
            logger.warning("Bearer auth: JWT invalid claims: %s", exc)
            return AuthenticationResult(
                status=AuthenticationStatus.FAILURE,
                error_code="invalid_token",
                error_description=str(exc)
            )

        except JWTDecodeError as exc:
            # Token is not a valid JWT, skip to allow TokenStore fallback.
            # We still emit a debug-level breadcrumb so a fully-failed
            # decode chain can be reconstructed from the journal.
            logger.debug("Bearer auth: JWT decode failed (skipping to TokenStore): %s", exc)
            return AuthenticationResult(status=AuthenticationStatus.SKIP)
    
    def _create_success_result(self, claims: Dict[str, Any]) -> AuthenticationResult:
        """
            Create a successful authentication result from claims.
            
            :param claims: The token claims dictionary.
            
            :returns: An AuthenticationResult with SUCCESS status and context.
        """
        # Extract principal information from claims
        identifier = claims.get("sub", "unknown")
        display_name = claims.get("name")
        roles = set(claims.get("roles", []))
        permissions = set(claims.get("permissions", []))
        
        principal = Principal(
            identifier=identifier,
            display_name=display_name,
            roles=roles,
            permissions=permissions,
            attributes=claims
        )
        
        # Determine expiration from claims
        expires_at = None
        if "exp" in claims:
            try:
                expires_at = datetime.fromtimestamp(claims["exp"], tz=timezone.utc)
            except (TypeError, ValueError, OSError) as exc:
                # An ``exp`` claim that we cannot parse is suspicious —
                # log so the operator can investigate the issuer.
                logger.warning(
                    "Bearer auth: invalid 'exp' claim %r in token: %s",
                    claims.get("exp"),
                    exc,
                )
        
        return AuthenticationResult(
            status=AuthenticationStatus.SUCCESS,
            context=AuthenticationContext(
                principal=principal,
                scheme=self.scheme,
                expires_at=expires_at,
                attributes=claims
            )
        )


