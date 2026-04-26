"""
.. module:: authenticationprovider
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Authentication provider protocol and built-in provider implementations
        for JWT, session, and API key authentication.

.. moduleauthor:: Automation Mojo LLC

This module defines the Authentication_Provider protocol that all authentication
providers must implement, along with built-in providers for common authentication
mechanisms: JWT bearer tokens, session cookies, and API keys.

Each provider extracts credentials from the incoming request, validates them,
and returns a Security_Context on success or None on failure. Providers never
raise exceptions on authentication failure; they return None to allow the
authentication manager to try the next provider in the chain.
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []

import base64
import hashlib
import hmac
import json
import time

from datetime import datetime, timezone
from typing import Any, Callable, Dict, Optional, Protocol, Tuple, runtime_checkable

from automojo.webworks.security.securitycontext import SecurityContext


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
        ...

    @property
    def priority(self) -> int:
        """
            Return the priority for ordering. Lower values indicate higher priority.
        """
        ...

    def authenticate(self, request: Any) -> Optional[SecurityContext]:
        """
            Attempt to authenticate a request synchronously.

            :param request: The incoming request object. Expected to have a
                headers dict attribute, and optionally cookies and query_params
                dict attributes.

            :returns: A Security_Context if authentication succeeds, None otherwise.
        """
        ...

    async def authenticate_async(self, request: Any) -> Optional[SecurityContext]:
        """
            Attempt to authenticate a request asynchronously.

            :param request: The incoming request object.

            :returns: A Security_Context if authentication succeeds, None otherwise.
        """
        ...


def _base64url_decode(data: str) -> bytes:
    """
        Decode a base64url-encoded string with padding correction.

        :param data: The base64url-encoded string to decode.

        :returns: The decoded bytes.
    """
    padding = 4 - len(data) % 4
    if padding != 4:
        data = data + "=" * padding

    rtnval = base64.urlsafe_b64decode(data)
    return rtnval


def _verify_jwt(token: str, secret_key: str, algorithm: str = "HS256") -> Optional[Dict[str, Any]]:
    """
        Verify and decode a JWT token using HMAC signature verification.

        Supports HS256, HS384, and HS512 algorithms. Checks the signature
        and expiration claim if present.

        :param token: The JWT token string to verify.
        :param secret_key: The secret key used for signature verification.
        :param algorithm: The expected signing algorithm.

        :returns: The decoded payload dictionary, or None if verification fails.
    """
    algorithm_map = {
        "HS256": hashlib.sha256,
        "HS384": hashlib.sha384,
        "HS512": hashlib.sha512,
    }

    hash_func = algorithm_map.get(algorithm)
    if hash_func is None:
        return None

    parts = token.split(".")
    if len(parts) != 3:
        return None

    header_segment = parts[0]
    payload_segment = parts[1]
    signature_segment = parts[2]

    try:
        header_bytes = _base64url_decode(header_segment)
        header = json.loads(header_bytes)
    except (ValueError, json.JSONDecodeError):
        return None

    header_alg = header.get("alg")
    if header_alg != algorithm:
        return None

    signing_input = f"{header_segment}.{payload_segment}"
    signing_input_bytes = signing_input.encode("utf-8")
    secret_bytes = secret_key.encode("utf-8")

    expected_signature = hmac.HMAC(secret_bytes, signing_input_bytes, hash_func).digest()

    try:
        actual_signature = _base64url_decode(signature_segment)
    except (ValueError,):
        return None

    if hmac.compare_digest(expected_signature, actual_signature) is not True:
        return None

    try:
        payload_bytes = _base64url_decode(payload_segment)
        payload = json.loads(payload_bytes)
    except (ValueError, json.JSONDecodeError):
        return None

    exp_claim = payload.get("exp")
    if exp_claim is not None:
        now = time.time()
        if now > exp_claim:
            return None

    rtnval = payload
    return rtnval


class JWTAuthProvider:
    """
        Authentication provider for JWT bearer tokens.

        Extracts a JWT from the Authorization header, verifies the signature
        using the configured secret key and algorithm, and returns a
        Security_Context populated from the token claims on success.

        :param secret_key: The secret key used for HMAC signature verification.
        :param algorithm: The signing algorithm. Defaults to HS256.
        :param header_name: The request header containing the token. Defaults to Authorization.
        :param header_prefix: The prefix before the token value. Defaults to Bearer.
        :param priority: Provider priority for ordering. Lower is higher priority.
    """

    def __init__(
        self,
        secret_key: str,
        algorithm: str = "HS256",
        header_name: str = "Authorization",
        header_prefix: str = "Bearer",
        priority: int = 10
    ):
        self._secret_key = secret_key
        self._algorithm = algorithm
        self._header_name = header_name
        self._header_prefix = header_prefix
        self._priority = priority
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

        payload = _verify_jwt(token, self._secret_key, self._algorithm)
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

        iat_claim = payload.get("iat")
        authenticated_at = None
        if iat_claim is not None:
            authenticated_at = datetime.fromtimestamp(iat_claim, tz=timezone.utc)

        exp_claim = payload.get("exp")
        expires_at = None
        if exp_claim is not None:
            expires_at = datetime.fromtimestamp(exp_claim, tz=timezone.utc)

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
