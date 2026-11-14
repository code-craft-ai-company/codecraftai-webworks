"""
.. module:: authenticationprovider
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Authentication provider protocol and built-in provider implementations
        for JWT, session, and API key authentication.

.. moduleauthor:: Code Craft AI LLC

This module defines the Authentication_Provider protocol that all authentication
providers must implement, along with built-in providers for common authentication
mechanisms: JWT bearer tokens, session cookies, and API keys.

Each provider extracts credentials from the incoming request, validates them,
and returns a Security_Context on success or None on failure. Providers never
raise exceptions on authentication failure; they return None to allow the
authentication manager to try the next provider in the chain.
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []

import logging

from datetime import datetime, timezone
from typing import Any, Dict, Optional, Protocol, Tuple, Union, runtime_checkable

from ccai.webworks.security.jsonwebtoken import (
    HMAC_ALGORITHMS,
    ClaimsRegistry,
    JoseError,
    decode as decode_jwt,
)
from ccai.webworks.security.securitycontext import SecurityContext


#: Shortest shared secret a :class:`JWTAuthProvider` accepts, in bytes.
#: RFC 7518 section 3.2 requires an HMAC key at least as long as the hash
#: output; 32 bytes is that length for HS256. A shorter secret can be
#: found by brute force from a single captured token.
MIN_JWT_SECRET_BYTES: int = 32


# Module-level logger. The JWT verification helper deliberately
# returns ``None`` rather than raising so an authentication chain
# can fall through to the next provider, but the operator still
# wants the breadcrumb in the journal — a sudden surge of
# verification failures usually indicates a key rotation or a
# tampered-token attack.
logger = logging.getLogger(__name__)


def _coerce_string_collection(
        value: Any
    ) -> Optional[Tuple[str, ...]]:
    """
        Convert a JWT-claim or session-store value into a tuple
        of role / scope strings. Returns ``None`` when the value
        is malformed (not iterable, contains non-strings, is
        a bare string, etc.) so the caller can reject the auth
        attempt rather than silently producing a misleading
        SecurityContext.

        This guard exists because ``tuple(value)`` accepts:

        - Strings (yields a tuple of single characters — disastrous
          for ``role in ctx.roles`` permission checks).
        - Dicts (yields a tuple of dict keys, not values).
        - Generators (consumed once, then empty on retry).

        Bare-string roles like ``"admin,user"`` would silently
        decompose into single-character "roles" without this
        guard.

        :param value: Raw value pulled from a JWT claim or
                      session-store dict.

        :returns: Tuple of strings on success;
                  ``None`` when the value isn't a clean
                  list / tuple / set of strings.
                  An empty list / tuple / set returns
                  ``()`` (valid, just empty).
    """
    if value is None:
        return tuple()
    # Reject bare strings before any iteration logic — Python
    # iterates strings into characters, which would silently
    # turn "admin,user" into ("a", "d", "m", "i", "n", ",", ...).
    if isinstance(value, str):
        return None
    # Accept the canonical JSON-decoded shapes (list, tuple, set)
    # and reject anything else (dict, int, custom object).
    if not isinstance(value, (list, tuple, set, frozenset)):
        return None
    materialized = tuple(value)
    for element in materialized:
        if not isinstance(element, str):
            return None
    return materialized


@runtime_checkable
class AuthenticationProvider(Protocol):
    """
        Protocol for authentication providers that verify user identity.

        Implementations must expose a name and priority property, and provide
        both synchronous and asynchronous authenticate methods. Providers are
        tried in priority order (lower number = higher priority) by the
        Authentication_Manager.
    """

    @property
    def name(self) -> str:
        """
            Return the provider name for logging and identification.
        """

    @property
    def priority(self) -> int:
        """
            Return the priority for ordering. Lower values indicate higher priority.
        """

    def authenticate(self, request: Any) -> Optional[SecurityContext]:
        """
            Attempt to authenticate a request synchronously.

            :param request: The incoming request object. Expected to have a
                headers dict attribute, and optionally cookies and query_params
                dict attributes.

            :returns: A Security_Context if authentication succeeds, None otherwise.
        """

    async def authenticate_async(self, request: Any) -> Optional[SecurityContext]:
        """
            Attempt to authenticate a request asynchronously.

            :param request: The incoming request object.

            :returns: A Security_Context if authentication succeeds, None otherwise.
        """


def _verify_jwt(
    token: str,
    secret_key: Union[str, bytes],
    algorithm: str = "HS256",
    issuer: Optional[str] = None,
    audience: Optional[str] = None,
    leeway: int = 0
) -> Optional[Dict[str, Any]]:
    """
        Verify and decode a JWT token using HMAC signature verification.

        Supports HS256, HS384, and HS512 algorithms. The token is decoded
        and its signature verified by
        :func:`ccai.webworks.security.jsonwebtoken.decode`; its claims are
        then validated:

        - ``exp`` is required and must lie in the future, so a token can
          not be valid for ever;
        - ``nbf``, when present, must lie in the past;
        - ``iss`` must equal *issuer* when one is configured;
        - ``aud`` must equal, or contain, *audience* when one is configured.

        :param token: The JWT token string to verify.
        :param secret_key: The secret key used for signature verification.
        :param algorithm: The expected signing algorithm.
        :param issuer: The issuer the token must name, or None to accept any.
        :param audience: The audience the token must be issued for, or
            None to accept any.
        :param leeway: Clock skew tolerated in the time checks, in seconds.

        :returns: The decoded payload dictionary, or None if verification fails.
    """
    rtnval: Optional[Dict[str, Any]] = None

    if algorithm in HMAC_ALGORITHMS:
        claim_options: Dict[str, Dict[str, Any]] = {"exp": {"essential": True}}

        if issuer is not None:
            claim_options["iss"] = {"essential": True, "value": issuer}

        if audience is not None:
            claim_options["aud"] = {"essential": True, "value": audience}

        try:
            decoded = decode_jwt(token, secret_key, [algorithm])

            registry = ClaimsRegistry(claim_options, leeway=leeway)
            registry.validate(decoded.claims)

            rtnval = decoded.claims
        except JoseError as exc:
            logger.warning("JWT verify: token rejected: %s", exc)
        except (ValueError, TypeError, OverflowError) as exc:
            # Segments that are not base64url, claims of the wrong type
            logger.warning("JWT verify: malformed token: %s", exc)

    return rtnval


class JWTAuthProvider:
    """
        Authentication provider for JWT bearer tokens.

        Extracts a JWT from the Authorization header, verifies the signature
        using the configured secret key and algorithm, and returns a
        Security_Context populated from the token claims on success.

        A token is accepted only if it carries an ``exp`` claim in the
        future; ``nbf`` is honoured when present, and ``iss`` / ``aud``
        are checked when *issuer* / *audience* are configured. Configure
        them whenever the signing secret is shared with another service:
        without them a token minted for that service authenticates here.

        :param secret_key: The secret key used for HMAC signature
            verification. At least :data:`MIN_JWT_SECRET_BYTES` bytes.
        :param algorithm: The signing algorithm. Defaults to HS256.
        :param header_name: The request header containing the token. Defaults to Authorization.
        :param header_prefix: The prefix before the token value. Defaults to Bearer.
        :param priority: Provider priority for ordering. Lower is higher priority.
        :param issuer: The ``iss`` value a token must carry. None accepts
            any issuer.
        :param audience: The ``aud`` value a token must carry. None accepts
            any audience.
        :param leeway: Clock skew tolerated in the ``exp`` / ``nbf`` checks,
            in seconds.

        :raises ValueError: If the secret key is empty or shorter than
            :data:`MIN_JWT_SECRET_BYTES` bytes, or the algorithm is not one
            of HS256, HS384 and HS512.
    """

    def __init__(
        self,
        secret_key: Union[str, bytes],
        algorithm: str = "HS256",
        header_name: str = "Authorization",
        header_prefix: str = "Bearer",
        priority: int = 10,
        issuer: Optional[str] = None,
        audience: Optional[str] = None,
        leeway: int = 0
    ):
        if isinstance(secret_key, str):
            secret_length = len(secret_key.encode("utf-8"))
        elif isinstance(secret_key, (bytes, bytearray)):
            secret_length = len(secret_key)
        else:
            secret_length = 0

        if secret_length < MIN_JWT_SECRET_BYTES:
            errmsg = (
                "JWTAuthProvider: the secret key must be at least {} bytes long; "
                "tokens signed with a shorter or empty secret can be forged."
            ).format(MIN_JWT_SECRET_BYTES)
            raise ValueError(errmsg)

        if algorithm not in HMAC_ALGORITHMS:
            errmsg = (
                "JWTAuthProvider: unsupported algorithm {!r}; expected one of {}."
            ).format(algorithm, sorted(HMAC_ALGORITHMS.keys()))
            raise ValueError(errmsg)

        self._secret_key = secret_key
        self._algorithm = algorithm
        self._header_name = header_name
        self._header_prefix = header_prefix
        self._priority = priority
        self._issuer = issuer
        self._audience = audience
        self._leeway = leeway
        return

    @property
    def name(self) -> str:
        """
            Return the provider name for logging.
        """
        return "jwt"

    @property
    def priority(self) -> int:
        """
            Return the priority for ordering.
        """
        return self._priority

    def authenticate(self, request: Any) -> Optional[SecurityContext]:
        """
            Extract and validate a JWT from the Authorization header.

            The method looks for the configured header, strips the prefix,
            decodes and verifies the token, then builds a Security_Context
            from the token claims.

            :param request: The incoming request with a headers dict attribute.

            :returns: A Security_Context on success, None on failure.
        """
        headers = getattr(request, "headers", None)
        if headers is None:
            return None

        auth_value = headers.get(self._header_name)
        if auth_value is None:
            return None

        prefix = self._header_prefix + " "
        if auth_value.startswith(prefix) is not True:
            return None

        token = auth_value[len(prefix):]
        if len(token) == 0:
            return None

        payload = _verify_jwt(
            token,
            self._secret_key,
            self._algorithm,
            issuer=self._issuer,
            audience=self._audience,
            leeway=self._leeway
        )
        if payload is None:
            return None

        user_id = payload.get("sub")
        if user_id is None:
            return None

        username = payload.get("username")
        email = payload.get("email")

        roles = _coerce_string_collection(payload.get("roles"))
        if roles is None:
            # Malformed roles claim (string, dict, non-string
            # element, etc.) — reject the auth attempt rather
            # than silently producing a misleading SecurityContext
            # whose roles would mis-authorize the request.
            return None

        scopes = _coerce_string_collection(payload.get("scopes"))
        if scopes is None:
            return None

        try:
            iat_claim = payload.get("iat")
            authenticated_at = None
            if iat_claim is not None:
                authenticated_at = datetime.fromtimestamp(iat_claim, tz=timezone.utc)

            exp_claim = payload.get("exp")
            expires_at = None
            if exp_claim is not None:
                expires_at = datetime.fromtimestamp(exp_claim, tz=timezone.utc)
        except (TypeError, ValueError, OverflowError, OSError) as exc:
            # A timestamp claim that is not a usable number
            logger.warning("JWT verify: malformed timestamp claim: %s", exc)
            return None

        extra = {}
        reserved_claims = {"sub", "username", "email", "roles", "scopes", "iat", "exp", "alg", "typ"}
        for key, value in payload.items():
            if key not in reserved_claims:
                extra[key] = value

        rtnval = SecurityContext(
            user_id=str(user_id),
            username=username,
            email=email,
            roles=roles,
            scopes=scopes,
            provider=self.name,
            authenticated_at=authenticated_at,
            expires_at=expires_at,
            extra=extra
        )

        return rtnval

    async def authenticate_async(self, request: Any) -> Optional[SecurityContext]:
        """
            Async version of authenticate. Delegates to the synchronous method.

            :param request: The incoming request with a headers dict attribute.

            :returns: A Security_Context on success, None on failure.
        """
        rtnval = self.authenticate(request)
        return rtnval


class SessionAuthProvider:
    """
        Authentication provider for session cookies.

        Extracts a session identifier from a cookie, looks up the session
        data in the configured session store, and returns a Security_Context
        populated from the session data on success.

        The session_store must implement a get(key) method that returns
        session data as a dictionary or None if the session is not found
        or has expired.

        :param session_store: An object with a get(key) method for session lookup.
        :param cookie_name: The name of the cookie containing the session id.
        :param priority: Provider priority for ordering.
    """

    def __init__(
        self,
        session_store: Any,
        cookie_name: str = "session_id",
        priority: int = 20
    ):
        self._session_store = session_store
        self._cookie_name = cookie_name
        self._priority = priority
        return

    @property
    def name(self) -> str:
        """
            Return the provider name for logging.
        """
        return "session"

    @property
    def priority(self) -> int:
        """
            Return the priority for ordering.
        """
        return self._priority

    def authenticate(self, request: Any) -> Optional[SecurityContext]:
        """
            Extract and validate a session from a cookie.

            The method looks for the configured cookie name in the request
            cookies, retrieves the session data from the store, and builds
            a Security_Context from the session data.

            :param request: The incoming request with a cookies dict attribute.

            :returns: A Security_Context on success, None on failure.
        """
        cookies = getattr(request, "cookies", None)
        if cookies is None:
            return None

        session_id = cookies.get(self._cookie_name)
        if session_id is None:
            return None

        if len(str(session_id)) == 0:
            return None

        session_data = self._session_store.get(session_id)
        if session_data is None:
            return None

        user_id = session_data.get("user_id")
        if user_id is None:
            return None

        username = session_data.get("username")
        email = session_data.get("email")

        roles = _coerce_string_collection(session_data.get("roles"))
        if roles is None:
            # Malformed session — reject rather than mis-authorize.
            return None

        scopes = _coerce_string_collection(session_data.get("scopes"))
        if scopes is None:
            return None

        authenticated_at_value = session_data.get("authenticated_at")
        authenticated_at = None
        if authenticated_at_value is not None:
            if isinstance(authenticated_at_value, datetime):
                authenticated_at = authenticated_at_value

        expires_at_value = session_data.get("expires_at")
        expires_at = None
        if expires_at_value is not None:
            if isinstance(expires_at_value, datetime):
                expires_at = expires_at_value

        rtnval = SecurityContext(
            user_id=str(user_id),
            username=username,
            email=email,
            roles=roles,
            scopes=scopes,
            provider=self.name,
            authenticated_at=authenticated_at,
            expires_at=expires_at,
        )

        return rtnval

    async def authenticate_async(self, request: Any) -> Optional[SecurityContext]:
        """
            Async version of authenticate. Delegates to the synchronous method.

            :param request: The incoming request with a cookies dict attribute.

            :returns: A Security_Context on success, None on failure.
        """
        rtnval = self.authenticate(request)
        return rtnval


class APIKeyAuthProvider:
    """
        Authentication provider for API keys.

        Extracts an API key from a request header or query parameter, looks
        up the key data in the configured key store, and returns a
        Security_Context populated from the key data on success.

        The key_store must implement a get(key) method that returns key
        metadata as a dictionary or None if the key is not found or is
        invalid.

        :param key_store: An object with a get(key) method for key lookup.
        :param header_name: The request header containing the API key.
        :param query_param: The query parameter name for the API key, or None to disable.
        :param priority: Provider priority for ordering.
    """

    def __init__(
        self,
        key_store: Any,
        header_name: str = "X-API-Key",
        query_param: Optional[str] = "api_key",
        priority: int = 30
    ):
        self._key_store = key_store
        self._header_name = header_name
        self._query_param = query_param
        self._priority = priority
        return

    @property
    def name(self) -> str:
        """
            Return the provider name for logging.
        """
        return "api_key"

    @property
    def priority(self) -> int:
        """
            Return the priority for ordering.
        """
        return self._priority

    def authenticate(self, request: Any) -> Optional[SecurityContext]:
        """
            Extract and validate an API key from header or query parameter.

            The method first checks the configured header, then falls back
            to the query parameter if configured. The key is looked up in
            the key store and a Security_Context is built from the key data.

            :param request: The incoming request with headers and optionally
                query_params dict attributes.

            :returns: A Security_Context on success, None on failure.
        """
        api_key = None

        headers = getattr(request, "headers", None)
        if headers is not None:
            api_key = headers.get(self._header_name)

        if api_key is None:
            if self._query_param is not None:
                query_params = getattr(request, "query_params", None)
                if query_params is not None:
                    api_key = query_params.get(self._query_param)

        if api_key is None:
            return None

        if len(str(api_key)) == 0:
            return None

        key_data = self._key_store.get(api_key)
        if key_data is None:
            return None

        user_id = key_data.get("user_id")
        if user_id is None:
            return None

        username = key_data.get("username")
        email = key_data.get("email")

        roles_value = key_data.get("roles", ())
        roles = tuple(roles_value)

        scopes_value = key_data.get("scopes", ())
        scopes = tuple(scopes_value)

        rtnval = SecurityContext(
            user_id=str(user_id),
            username=username,
            email=email,
            roles=roles,
            scopes=scopes,
            provider=self.name,
        )

        return rtnval

    async def authenticate_async(self, request: Any) -> Optional[SecurityContext]:
        """
            Async version of authenticate. Delegates to the synchronous method.

            :param request: The incoming request with headers and optionally
                query_params dict attributes.

            :returns: A Security_Context on success, None on failure.
        """
        rtnval = self.authenticate(request)
        return rtnval
