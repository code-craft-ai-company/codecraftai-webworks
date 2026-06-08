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
import json
import logging
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
        ...
    
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
        ...
    
    async def revoke_token(self, token: str) -> bool:
        """
            Revoke a token.
            
            :param token: The token string to revoke.
            
            :returns: True if the token was revoked, False if not found.
        """
        ...


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
    verify_exp: bool = True
) -> Dict[str, Any]:
    """
        Decode and validate a JWT token.
        
        This function decodes a JWT token, verifies its signature using
        the provided secret and algorithms, and validates standard claims
        (exp, iss, aud) if configured.
        
        :param token: The JWT token string.
        :param secret: The secret key for signature verification.
        :param algorithms: List of allowed algorithms (e.g., ["HS256"]).
        :param issuer: Expected issuer claim value (optional).
        :param audience: Expected audience claim value (optional).
        :param verify_exp: Whether to verify the expiration claim.
        
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
    
    # Decode header
    try:
        header_bytes = _base64url_decode(header_b64)
        header = json.loads(header_bytes.decode('utf-8'))
    except json.JSONDecodeError as exc:
        raise JWTDecodeError(f"Invalid JWT header: {exc}")
    
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
    except json.JSONDecodeError as exc:
        raise JWTDecodeError(f"Invalid JWT payload: {exc}")
    
    # Verify expiration
    if verify_exp and 'exp' in payload:
        exp = payload['exp']
        if not isinstance(exp, (int, float)):
            raise JWTInvalidClaimsError("Invalid 'exp' claim: must be a number")
        if time.time() > exp:
            raise JWTExpiredError("Token has expired")
    
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
    """
    
    def __init__(
        self,
        token_store: Optional[TokenStore] = None,
        jwt_secret: Optional[str] = None,
        jwt_algorithms: Optional[List[str]] = None,
        jwt_issuer: Optional[str] = None,
        jwt_audience: Optional[str] = None
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
    
    @property
    def scheme(self) -> str:
        """
            Return the authentication scheme identifier.
            
            :returns: The string "Bearer".
        """
        return "Bearer"
    
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
                audience=self._jwt_audience
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


