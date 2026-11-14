"""
.. module:: security
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Base security blueprint class for authentication endpoints.

.. moduleauthor:: Code Craft AI LLC

This module provides the :class:`SecurityBlueprint` base class which extends
:class:`RestBlueprint` with authentication-specific functionality. All
authentication blueprints (Basic, Bearer, OAuth2, etc.) inherit from this
class to share common security patterns including error formatting,
pre/post authentication hooks, endpoint enable/disable control, and
integration with the :class:`AuthenticationSystem`.
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


import asyncio
import base64
import binascii
import contextvars
import functools
import logging
import re
import threading
import time
from collections.abc import MutableMapping
from typing import Any, Callable, Dict, Iterator, List, Optional, Set, Tuple, Type, TypeVar, TYPE_CHECKING

from ccai.webworks.endpoints.restblueprint import RestBlueprint
from ccai.webworks.endpoints.accesspolicy import AccessPolicy
from ccai.webworks.endpoints.constraints import EndpointConstraints
from ccai.webworks.endpoints.ratelimit import RateLimit
from ccai.webworks.endpoints.descriptor import EndpointDescriptor, record_rest_processing
from ccai.webworks.endpoints.doc import Doc
from ccai.webworks.endpoints.registry import EndpointRegistry
from ccai.webworks.authentication.system import AuthenticationSystem
from ccai.webworks.authentication.bearer import (
    JWTError,
    TokenRevocationList,
    decode_jwt,
    get_default_revocation_list,
    get_token_revocation_id
)
from ccai.webworks.authentication.core import AuthenticationContext, Principal
from ccai.webworks.authentication.errors import (
    LoginThrottle,
    get_client_key,
    sanitize_credentials,
    sanitize_dict
)

from ccai.webworks.authentication.blueprints.responses import (
    AuthResponse,
    AuthError
)


# Default set of keys whose values are considered sensitive and must be
# redacted from error response bodies.
_SENSITIVE_BODY_KEYS: Set[str] = {
    "password", "passwd", "pwd", "secret", "token", "access_token",
    "refresh_token", "id_token", "api_key", "apikey", "api-key",
    "client_secret", "credentials", "credential", "session_id",
    "sessionid", "nonce", "authorization", "auth",
}

if TYPE_CHECKING:
    from ccai.webworks.endpoints.router import Router as RouterProtocol
    from ccai.webworks.authentication.middleware import AuthenticationMiddleware


# Type variable for preserving function signatures in decorators
F = TypeVar("F", bound=Callable[..., Any])

# Attribute name used to store endpoint metadata on handler functions
_ENDPOINT_META_ATTR = "_security_endpoint_meta"

# Module-level logger shared by the blueprint base class helpers.
logger = logging.getLogger(__name__)

# A Host / X-Forwarded-Host value: a DNS name, an IPv4 address or a
# bracketed IPv6 address, optionally followed by a port.
_HOST_HEADER_PATTERN = re.compile(
    r"^(?:[A-Za-z0-9](?:[A-Za-z0-9.\-]*[A-Za-z0-9])?|\[[0-9A-Fa-f:.]+\])(?::\d{1,5})?$"
)

# A route parameter placeholder such as ``{key_id}`` or ``{name:path}``.
_ROUTE_PARAMETER_PATTERN = re.compile(r"\{[^{}]*\}")

# Event loop of the dispatcher that offloaded the current handler call
# to a worker thread (see ``SecurityBlueprint._wrap_handler``). When it
# is set, :func:`run_async` drives coroutines on that loop so stores
# bound to the application loop keep working.
_handler_thread_state = threading.local()


def _get_dispatcher_application_loop() -> Optional[asyncio.AbstractEventLoop]:
    """
        Get the event loop of the dispatcher that moved the current
        handler call to a worker thread, when it published one.
        
        :returns: The dispatcher's event loop, or None.
    """
    # Imported here because the routing package imports
    # authentication.core while it is being initialised.
    try:
        from ccai.webworks.routing.dispatcher import get_application_loop
    except ImportError:
        return None
    
    rtnval = get_application_loop()
    return rtnval


def run_async(coro: Any) -> Any:
    """
        Run a coroutine to completion from synchronous blueprint code.
        
        The blueprint handlers are synchronous while stores and identity
        providers are asynchronous. Three situations are handled:
        
        * The handler was offloaded to a worker thread, by the
          dispatcher or by the endpoint wrapper (the ASGI path): the
          coroutine is scheduled on the application's event loop, so a
          store bound to that loop (asyncpg, SQLAlchemy async) is driven
          by the loop that owns it.
        * No event loop is running on this thread (WSGI, tests): the
          coroutine runs on a fresh loop.
        * A loop is running on this very thread (a handler called inline
          from async code): the coroutine runs on a fresh loop in a
          helper thread, because a running loop cannot be re-entered.
        
        :param coro: The coroutine to execute.
        
        :returns: The result of the coroutine.
    """
    try:
        running_loop = asyncio.get_running_loop()
    except RuntimeError:
        running_loop = None
    
    if running_loop is None:
        application_loop = getattr(_handler_thread_state, "loop", None)
        if application_loop is None:
            application_loop = _get_dispatcher_application_loop()

        if application_loop is not None and application_loop.is_running():
            future = asyncio.run_coroutine_threadsafe(coro, application_loop)
            result = future.result()
            return result
        
        # No running loop on this thread — drive the coroutine here
        # with a fresh loop.
        result = asyncio.run(coro)
        return result
    
    # A running loop is present on this thread. Offload to a worker
    # thread that owns its own loop so we never recurse into the live
    # loop.
    import concurrent.futures
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(asyncio.run, coro)
        result = future.result()
    
    return result


def split_scope(scope: Any) -> List[str]:
    """
        Split a scope value into its individual scope tokens.
        
        :param scope: A space-separated scope string, or a list, tuple or
                      set of scope tokens. Anything else yields no tokens.
        
        :returns: The scope tokens in their original order, without
                  duplicates.
    """
    tokens: List[str] = []
    
    if isinstance(scope, str):
        candidates = scope.split()
    elif isinstance(scope, (list, tuple, set, frozenset)):
        candidates = [str(item) for item in scope]
    else:
        candidates = []
    
    for token in candidates:
        if token and token not in tokens:
            tokens.append(token)
    
    return tokens


def restrict_scope(requested: Any, allowed: Any) -> Optional[str]:
    """
        Reduce a requested scope to the part that may be granted.
        
        A caller never receives a scope merely because it asked for it:
        only the requested tokens that are also in *allowed* are granted.
        
        :param requested: The scope the caller asked for (string or
                          collection of tokens).
        :param allowed: The scope the principal, client or original
                        grant permits (string or collection of tokens).
        
        :returns: The granted scope as a space-separated string, or None
                  when no requested token may be granted.
    """
    allowed_tokens = set(split_scope(allowed))
    granted = [token for token in split_scope(requested) if token in allowed_tokens]
    
    rtnval = None
    if len(granted) > 0:
        rtnval = " ".join(granted)
    
    return rtnval


class ExpiringMemoryStore(MutableMapping):
    """
        Bounded, expiring in-memory mapping used as a fallback store.
        
        The authentication blueprints fall back to this store when no
        persistent store is configured. Entries are dropped once their
        time to live has passed and the number of entries is capped, so
        an unconfigured deployment cannot grow without bound. The store
        is private to one process: a deployment with several workers
        needs a shared store.
        
        :param max_entries: Maximum number of entries kept.
        :param ttl_seconds: Default time to live of an entry in seconds,
                            or None for entries that do not expire.
    """
    
    DEFAULT_MAX_ENTRIES: int = 10000
    
    def __init__(
        self,
        max_entries: Optional[int] = None,
        ttl_seconds: Optional[float] = None
    ):
        """
            Initialize the store.
            
            :param max_entries: Maximum number of entries kept. Defaults
                                to :attr:`DEFAULT_MAX_ENTRIES`.
            :param ttl_seconds: Default time to live of an entry in
                                seconds, or None for no expiry.
        """
        if max_entries is None:
            max_entries = self.DEFAULT_MAX_ENTRIES
        
        self._max_entries = max_entries
        self._ttl_seconds = ttl_seconds
        self._entries: Dict[Any, Tuple[Any, Optional[float]]] = {}
        self._lock = threading.RLock()
        return
    
    def set(self, key: Any, value: Any, ttl_seconds: Optional[float] = None) -> None:
        """
            Store an entry with its own time to live.
            
            :param key: The entry key.
            :param value: The entry value.
            :param ttl_seconds: Time to live in seconds. Defaults to the
                                store's ``ttl_seconds``.
        """
        if ttl_seconds is None:
            ttl_seconds = self._ttl_seconds
        
        expires_at = None
        if ttl_seconds is not None:
            expires_at = time.time() + ttl_seconds
        
        with self._lock:
            if key not in self._entries and len(self._entries) >= self._max_entries:
                self._sweep_expired()
            
            while key not in self._entries and len(self._entries) >= self._max_entries:
                # Still full of live entries: drop the oldest one.
                oldest_key = next(iter(self._entries))
                del self._entries[oldest_key]
            
            self._entries[key] = (value, expires_at)
        return
    
    def pop(self, key: Any, *default: Any) -> Any:
        """
            Remove an entry and return its value in one atomic step.
            
            :param key: The entry key.
            :param default: Optional value returned when the key is absent.
            
            :returns: The value, or the default.
            
            :raises KeyError: If the key is absent and no default is given.
        """
        with self._lock:
            entry = self._entries.pop(key, None)
        
        if entry is not None and not self._is_expired(entry):
            return entry[0]
        
        if len(default) > 0:
            return default[0]
        
        raise KeyError(key)
    
    def __getitem__(self, key: Any) -> Any:
        with self._lock:
            entry = self._entries[key]
            if self._is_expired(entry):
                del self._entries[key]
                raise KeyError(key)
            rtnval = entry[0]
        return rtnval
    
    def __setitem__(self, key: Any, value: Any) -> None:
        self.set(key, value)
        return
    
    def __delitem__(self, key: Any) -> None:
        with self._lock:
            del self._entries[key]
        return
    
    def __iter__(self) -> Iterator[Any]:
        with self._lock:
            keys = [
                key for key, entry in self._entries.items()
                if not self._is_expired(entry)
            ]
        return iter(keys)
    
    def __len__(self) -> int:
        with self._lock:
            self._sweep_expired()
            rtnval = len(self._entries)
        return rtnval
    
    def _is_expired(self, entry: Tuple[Any, Optional[float]]) -> bool:
        """
            Check whether a stored entry has outlived its time to live.
            
            :param entry: The (value, expires_at) tuple.
            
            :returns: True if the entry has expired.
        """
        expires_at = entry[1]
        if expires_at is None:
            return False
        rtnval = time.time() > expires_at
        return rtnval
    
    def _sweep_expired(self) -> None:
        """
            Remove every expired entry. The caller holds the lock.
        """
        expired = [
            key for key, entry in self._entries.items()
            if self._is_expired(entry)
        ]
        for key in expired:
            del self._entries[key]
        return


class SecurityBlueprint(RestBlueprint):
    """
        Base class for authentication blueprints.

        Provides common functionality for authentication endpoints including
        error handling, hooks, and integration with the authentication system.
        All authentication blueprint subclasses (BasicAuthBlueprint,
        BearerAuthBlueprint, etc.) extend this class to inherit shared
        security behavior.

        The :meth:`configure` class method associates the blueprint with an
        :class:`AuthenticationSystem` instance and optionally customizes the
        base path and set of enabled endpoints.

        Subclasses may override :meth:`pre_authenticate` and
        :meth:`post_authenticate` to inject custom logic before and after
        credential validation. The :meth:`format_error` and
        :meth:`format_success` methods produce standardized response
        dictionaries that follow RFC 6749 conventions.

        Endpoint decorators (:meth:`create`, :meth:`read`, etc.) store
        metadata on the handler function rather than registering with the
        global :class:`EndpointRegistry`. The :meth:`register` method
        builds :class:`EndpointDescriptor` instances at call time,
        resolving paths against the subclass ``base_path``.

        Class Attributes:
            auth_system: The AuthenticationSystem instance used for
                         credential validation. Set via :meth:`configure`.
            enabled_endpoints: Set of endpoint names that are active.
                               Defaults to ``{"all"}`` which enables every
                               endpoint. Provide a specific set to selectively
                               enable endpoints.
            error_format: Format for error responses. Currently supports
                          ``"json"`` (default).
            cors_origins: Optional list of allowed CORS origins for
                          cross-origin authentication requests. When set,
                          :meth:`get_cors_headers` returns appropriate
                          CORS headers for allowed origins.
            rest_processing: False. The handlers of an authentication
                             blueprint parse the request body and shape the
                             response themselves (:meth:`format_error`,
                             :meth:`format_success`), so the request and
                             response schemas they declare only document
                             them: they are not served through the REST
                             request/response processing. A handler that
                             returns plain data can opt in with
                             ``rest_processing=True`` on its decorator.
    """

    auth_system: Optional[AuthenticationSystem] = None
    enabled_endpoints: set = None
    error_format: str = "json"
    cors_origins: Optional[List[str]] = None

    # The schemas an authentication endpoint declares document it; the
    # handler parses the body and shapes the response itself, so it opts
    # out of the REST request/response processing (see the class docstring).
    rest_processing: bool = False

    # Optional rate limiting and account lockout applied to every
    # credential check the blueprint performs (logins, password and
    # client-credential grants). None leaves attempts unthrottled.
    login_throttle: Optional[LoginThrottle] = None

    # Public origin of the site (scheme, host and optional port, e.g.
    # ``"https://app.example.com"``). URLs handed to other parties
    # (OAuth redirect URIs, the OIDC issuer) are built from it. When it
    # is None the origin is derived from the request ``Host`` header.
    public_base_url: Optional[str] = None

    # Honour ``X-Forwarded-Proto`` / ``X-Forwarded-Host`` when deriving
    # the public origin. Enable only behind a proxy that sets them.
    trust_forwarded_headers: bool = False

    # Optional allow-list of ``host[:port]`` values accepted from the
    # ``Host`` / ``X-Forwarded-Host`` headers when deriving the origin.
    allowed_hosts: Optional[List[str]] = None

    # List of revoked token identifiers consulted and updated by the
    # token endpoints. None selects the process-wide in-memory default
    # (see :meth:`get_revocation_list`).
    revocation_list: Optional[TokenRevocationList] = None

    # Names of class attributes that hold an in-memory fallback store.
    # Every subclass receives its own instance of each, so blueprints do
    # not share sessions, codes or tokens through a common ancestor.
    # ``EXPIRING_MEMORY_STORES`` are replaced by a fresh empty
    # :class:`ExpiringMemoryStore`; ``REGISTRY_MEMORY_STORES`` (client and
    # user registrations) start as a copy of the parent's entries.
    EXPIRING_MEMORY_STORES: Tuple[str, ...] = ()
    REGISTRY_MEMORY_STORES: Tuple[str, ...] = ()
    MEMORY_STORE_MAX_ENTRIES: int = 10000

    # --- Class constants ---
    # Override these on a subclass to rebrand error codes / response shape
    # without rewriting the handler bodies. Every literal a handler used to
    # emit lives here as an UPPERCASE attribute referenced via ``cls.NAME``.

    # Response content types
    JSON_CONTENT_TYPE: str = "application/json"

    # Generic error codes / messages used by base-class handlers
    SERVER_ERROR_CODE: str = "server_error"
    SERVER_ERROR_MESSAGE: str = "An internal error occurred"

    # CORS literals
    CORS_DEFAULT_METHODS: str = "GET, POST, PUT, DELETE, OPTIONS"
    CORS_DEFAULT_HEADERS: str = "Authorization, Content-Type"
    CORS_ALLOW_CREDENTIALS: str = "true"
    CORS_ALLOW_ORIGIN_HEADER: str = "Access-Control-Allow-Origin"
    CORS_ALLOW_METHODS_HEADER: str = "Access-Control-Allow-Methods"
    CORS_ALLOW_HEADERS_HEADER: str = "Access-Control-Allow-Headers"
    CORS_ALLOW_CREDENTIALS_HEADER: str = "Access-Control-Allow-Credentials"
    CORS_WILDCARD_ORIGIN: str = "*"

    # Endpoint enablement / metadata
    ENABLE_ALL_TOKEN: str = "all"
    DEFAULT_ENDPOINT_TYPE: str = "auth"

    # Request parsing / throttling literals
    INVALID_BODY_ERROR_CODE: str = "invalid_request"
    INVALID_BODY_MESSAGE: str = "Request body must be a JSON object or form-encoded fields"
    AUTHENTICATION_REQUIRED_ERROR_CODE: str = "authentication_required"
    AUTHENTICATION_REQUIRED_MESSAGE: str = "Authentication is required"
    RETRY_AFTER_HEADER: str = "Retry-After"
    FORM_CONTENT_TYPES: Tuple[str, ...] = (
        "application/x-www-form-urlencoded",
        "multipart/form-data",
    )
    DEFAULT_PUBLIC_SCHEME: str = "https"
    DEFAULT_PUBLIC_HOST: str = "localhost"

    def __init_subclass__(cls, **kwargs: Any) -> None:
        """
            Give every subclass its own in-memory fallback stores.

            Without this, the stores declared on a base blueprint would be
            one dictionary shared by every subclass in the process.
        """
        super().__init_subclass__(**kwargs)

        for store_name in cls.EXPIRING_MEMORY_STORES:
            if store_name not in cls.__dict__:
                setattr(cls, store_name, cls.create_memory_store())

        for store_name in cls.REGISTRY_MEMORY_STORES:
            if store_name not in cls.__dict__:
                inherited = getattr(cls, store_name, None)
                setattr(cls, store_name, dict(inherited or {}))

        return

    @classmethod
    def create_memory_store(cls, ttl_seconds: Optional[float] = None) -> "ExpiringMemoryStore":
        """
            Create a bounded, expiring in-memory fallback store.

            :param ttl_seconds: Default time to live of an entry, or None.

            :returns: A new :class:`ExpiringMemoryStore`.
        """
        store = ExpiringMemoryStore(
            max_entries=cls.MEMORY_STORE_MAX_ENTRIES,
            ttl_seconds=ttl_seconds
        )
        return store

    @classmethod
    def put_in_memory_store(
        cls,
        store: Any,
        key: Any,
        value: Any,
        ttl_seconds: Optional[float]
    ) -> None:
        """
            Add an entry to an in-memory fallback store with a lifetime.

            :param store: The fallback store, an
                          :class:`ExpiringMemoryStore` or a plain dict
                          (which keeps the entry until it is removed).
            :param key: The entry key.
            :param value: The entry value.
            :param ttl_seconds: Time after which the entry is dropped.
        """
        if isinstance(store, ExpiringMemoryStore):
            store.set(key, value, ttl_seconds=ttl_seconds)
        else:
            store[key] = value
        return

    @classmethod
    def note_memory_fallback(cls, store_label: str) -> None:
        """
            Log, once per blueprint class and store, that the in-memory
            fallback is in use.

            The fallback is meant for development: it is private to one
            worker process and lost on restart, so a code or session
            created in one worker is unknown to the others.

            :param store_label: Human-readable name of the missing store.
        """
        warned = cls.__dict__.get("_memory_fallback_warned")
        if warned is None:
            warned = set()
            cls._memory_fallback_warned = warned

        if store_label in warned:
            return

        warned.add(store_label)
        logger.warning(
            "%s: no %s is configured; using the in-memory fallback, which "
            "is private to this process and lost on restart. Configure a "
            "shared store before running more than one worker.",
            cls.__name__,
            store_label,
        )
        return

    @classmethod
    def get_revocation_list(cls) -> TokenRevocationList:
        """
            Get the list the token endpoints record revocations in.

            Returns the configured :attr:`revocation_list`, or the
            process-wide default that :class:`BearerAuthenticator` also
            consults by default. A site that configures its own (shared)
            list passes the same object to the authenticator::

                BearerAuthenticator(
                    jwt_secret=secret,
                    revocation_list=BearerAuthBlueprint.get_revocation_list()
                )

            :returns: The :class:`TokenRevocationList` in use.
        """
        if cls.revocation_list is not None:
            return cls.revocation_list

        rtnval = get_default_revocation_list()
        return rtnval

    @classmethod
    def is_token_revoked(cls, token: str, claims: Optional[Dict[str, Any]]) -> bool:
        """
            Check whether a token has been revoked.

            :param token: The encoded token string.
            :param claims: The decoded token claims, when available.

            :returns: True if the token is on the revocation list.
        """
        token_id = get_token_revocation_id(token, claims)

        is_revoked = cls.get_revocation_list().is_revoked(token_id)
        if asyncio.iscoroutine(is_revoked):
            is_revoked = run_async(is_revoked)

        rtnval = bool(is_revoked)
        return rtnval

    @classmethod
    def revoke_signed_token(
        cls,
        token: str,
        secret: Optional[str],
        algorithm: str
    ) -> bool:
        """
            Put a JWT this server signed on the revocation list.

            The signature is verified first so that arbitrary strings
            cannot fill the list; expiry is not checked because revoking
            an expired token is harmless.

            :param token: The encoded token string.
            :param secret: The signing secret, or None if not configured.
            :param algorithm: The signing algorithm.

            :returns: True if the token was recorded as revoked, False
                      if it is not a token this server signed.
        """
        if secret is None:
            return False

        try:
            claims = decode_jwt(
                token,
                secret,
                algorithms=[algorithm],
                verify_exp=False
            )
        except JWTError as exc:
            logger.info(
                "%s: revoke ignored a token that does not verify: %s",
                cls.__name__,
                exc,
            )
            return False

        expires_at = claims.get("exp")
        if isinstance(expires_at, bool) or not isinstance(expires_at, (int, float)):
            expires_at = None

        token_id = get_token_revocation_id(token, claims)

        revoked = cls.get_revocation_list().revoke(token_id, expires_at)
        if asyncio.iscoroutine(revoked):
            run_async(revoked)

        return True

    @classmethod
    def get_request_header(cls, request: Any, name: str) -> Optional[str]:
        """
            Read a request header by name, ignoring case.

            Works with the framework Request (``Headers``), plain dict
            headers and dict-shaped test requests.

            :param request: The incoming HTTP request object.
            :param name: The header name.

            :returns: The header value, or None if it is not present.
        """
        headers = None
        if isinstance(request, dict):
            headers = request.get("headers")
        else:
            headers = getattr(request, "headers", None)

        if headers is None:
            return None

        if isinstance(headers, dict):
            for key, value in headers.items():
                if str(key).lower() == name.lower():
                    return value
            return None

        getter = getattr(headers, "get", None)
        if callable(getter):
            value = getter(name)
            if value is None:
                value = getter(name.lower())
            if isinstance(value, str):
                return value

        return None

    @classmethod
    def read_request_data(cls, request: Any) -> Optional[Dict[str, Any]]:
        """
            Parse the request body into a dictionary of fields.

            Accepts a JSON object and, as RFC 6749 clients send,
            ``application/x-www-form-urlencoded`` (or multipart) form
            fields. Anything else (invalid JSON, a JSON array or scalar,
            an undecodable body) yields None so the handler can answer
            400 ``invalid_request`` instead of failing.

            :param request: The incoming HTTP request object.

            :returns: The body fields, or None if the body cannot be
                      read as an object.
        """
        content_type = cls.get_request_header(request, "Content-Type") or ""
        media_type = content_type.split(";", 1)[0].strip().lower()

        if media_type in cls.FORM_CONTENT_TYPES:
            form_reader = getattr(request, "form", None)
            if not callable(form_reader):
                return None
            try:
                form_data = form_reader()
            except (ValueError, TypeError) as exc:
                logger.warning("%s: unreadable form body: %s", cls.__name__, exc)
                return None
            if not hasattr(form_data, "keys"):
                return None
            data = {key: form_data.get(key) for key in form_data.keys()}
            return data

        json_reader = getattr(request, "json", None)
        if not callable(json_reader):
            return None

        try:
            data = json_reader()
        except (ValueError, TypeError, AttributeError) as exc:
            # ValueError covers JSONDecodeError and UnicodeDecodeError
            logger.warning("%s: unreadable JSON body: %s", cls.__name__, exc)
            return None

        if not isinstance(data, dict):
            return None

        return data

    @classmethod
    def invalid_body_response(cls) -> dict:
        """
            Build the 400 response for a body that cannot be parsed.

            :returns: A response dictionary with an ``invalid_request``
                      error.
        """
        error = AuthError(
            error=cls.INVALID_BODY_ERROR_CODE,
            error_description=cls.INVALID_BODY_MESSAGE
        )
        response = cls.format_error(error, status_code=400)
        return response

    @classmethod
    def get_authenticated_principal(cls, request: Any) -> Optional[Principal]:
        """
            Get the principal the authentication middleware established
            for a request.

            Reads the :class:`AuthenticationContext` the middleware stores
            under ``scope["auth"]`` (exposed as ``request.auth``). An
            expired context does not count as authenticated.

            :param request: The incoming HTTP request object.

            :returns: The authenticated :class:`Principal`, or None.
        """
        context = getattr(request, "auth", None)

        if context is None:
            scope = None
            if isinstance(request, dict):
                scope = request
            else:
                scope = getattr(request, "scope", None)
            if isinstance(scope, dict):
                context = scope.get("auth")

        if not isinstance(context, AuthenticationContext):
            return None

        if context.is_expired:
            return None

        principal = context.principal
        if not isinstance(principal, Principal):
            return None

        return principal

    @classmethod
    def authentication_required_response(cls) -> dict:
        """
            Build the 401 response for an endpoint that needs a caller
            identity the request does not carry.

            :returns: A response dictionary with a 401 status.
        """
        error = AuthError(
            error=cls.AUTHENTICATION_REQUIRED_ERROR_CODE,
            error_description=cls.AUTHENTICATION_REQUIRED_MESSAGE
        )
        response = cls.format_error(error, status_code=401)
        return response

    @classmethod
    def check_login_throttle(
        cls,
        request: Any,
        account_id: Optional[str]
    ) -> Optional[dict]:
        """
            Check the configured :attr:`login_throttle` before a
            credential check.

            :param request: The incoming HTTP request object.
            :param account_id: The account the attempt names, or None.

            :returns: None when the attempt may proceed, otherwise a 429
                      response dictionary with a ``Retry-After`` header.
        """
        throttle = cls.login_throttle
        if throttle is None:
            return None

        client_key = get_client_key(request)
        throttle_error = throttle.check(client_key, account_id)
        if throttle_error is None:
            return None

        logger.warning(
            "%s: credential check refused: %s",
            cls.__name__,
            throttle_error.error_code,
        )

        error = AuthError(
            error=throttle_error.error_code,
            error_description=throttle_error.safe_message
        )
        response = cls.format_error(error, status_code=429)

        retry_after = throttle.get_retry_after(client_key, account_id)
        if retry_after is not None:
            response["headers"] = {cls.RETRY_AFTER_HEADER: str(retry_after)}

        return response

    @classmethod
    def record_login_attempt(
        cls,
        request: Any,
        account_id: Optional[str],
        success: bool
    ) -> None:
        """
            Record the outcome of a credential check with the configured
            :attr:`login_throttle`.

            :param request: The incoming HTTP request object.
            :param account_id: The account the attempt named, or None.
            :param success: Whether the credentials were valid.
        """
        throttle = cls.login_throttle
        if throttle is None:
            return

        client_key = get_client_key(request)
        throttle.record(client_key, account_id, success)
        return

    @classmethod
    def extract_client_credentials(
        cls,
        request: Any,
        body: Dict[str, Any]
    ) -> Tuple[Optional[str], Optional[str]]:
        """
            Read OAuth 2.0 client credentials from a token request.

            RFC 6749 section 2.3.1 lets a client authenticate with HTTP
            Basic (preferred) or with ``client_id`` / ``client_secret``
            body fields. The Basic header wins when both are present.

            :param request: The incoming HTTP request object, or None.
            :param body: The parsed request body fields.

            :returns: A tuple of (client_id, client_secret); either may
                      be None when it was not supplied.
        """
        client_id = body.get("client_id")
        client_secret = body.get("client_secret")

        authorization = None
        if request is not None:
            authorization = cls.get_request_header(request, "Authorization")

        if authorization is not None and authorization.lower().startswith("basic "):
            encoded = authorization[6:].strip()
            try:
                decoded = base64.b64decode(encoded, validate=True).decode("utf-8")
            except (binascii.Error, ValueError) as exc:
                logger.warning(
                    "%s: malformed Basic client credentials: %s", cls.__name__, exc
                )
                decoded = ""
            if ":" in decoded:
                client_id, client_secret = decoded.split(":", 1)

        return (client_id, client_secret)

    @classmethod
    def resolve_public_base_url(cls, request: Any) -> str:
        """
            Determine the public origin of the site for a request.

            Order of precedence:

            1. :attr:`public_base_url` when configured.
            2. ``X-Forwarded-Proto`` / ``X-Forwarded-Host`` when
               :attr:`trust_forwarded_headers` is enabled.
            3. The request scheme and the ``Host`` header, which carries
               the port the client used.
            4. The server address the request reports, with its port
               when that is not the default for the scheme.

            Header values that are not a well-formed ``host[:port]``, or
            that are missing from :attr:`allowed_hosts` when it is set,
            are ignored.

            :param request: The incoming HTTP request object.

            :returns: The origin without a trailing slash, e.g.
                      ``"https://app.example.com:8443"``.
        """
        if cls.public_base_url:
            rtnval = str(cls.public_base_url).rstrip("/")
            return rtnval

        scheme = str(getattr(request, "scheme", "") or cls.DEFAULT_PUBLIC_SCHEME)
        host = None

        if cls.trust_forwarded_headers:
            forwarded_proto = cls.get_request_header(request, "X-Forwarded-Proto")
            if forwarded_proto:
                candidate = forwarded_proto.split(",", 1)[0].strip().lower()
                if candidate in ("http", "https"):
                    scheme = candidate

            forwarded_host = cls.get_request_header(request, "X-Forwarded-Host")
            if forwarded_host:
                candidate = forwarded_host.split(",", 1)[0].strip()
                if cls._is_acceptable_host(candidate):
                    host = candidate

        if host is None:
            host_header = cls.get_request_header(request, "Host")
            if host_header and cls._is_acceptable_host(host_header.strip()):
                host = host_header.strip()

        if host is None:
            host = str(getattr(request, "host", "") or cls.DEFAULT_PUBLIC_HOST)
            port = getattr(request, "port", None)
            default_port = 443 if scheme == "https" else 80
            if isinstance(port, int) and port != default_port:
                host = "{}:{}".format(host, port)

        rtnval = "{}://{}".format(scheme, host)
        return rtnval

    @classmethod
    def _is_acceptable_host(cls, host: str) -> bool:
        """
            Check a ``Host`` / ``X-Forwarded-Host`` value before it is
            used to build a URL.

            :param host: The ``host[:port]`` value from the header.

            :returns: True if it is well formed and, when
                      :attr:`allowed_hosts` is set, listed there.
        """
        if _HOST_HEADER_PATTERN.match(host) is None:
            return False

        if cls.allowed_hosts is not None:
            allowed = [entry.lower() for entry in cls.allowed_hosts]
            if host.lower() not in allowed:
                return False

        return True

    @classmethod
    def configure(
        cls,
        auth_system: AuthenticationSystem,
        base_path: Optional[str] = None,
        enabled_endpoints: Optional[set] = None,
        access_policy: Optional[AccessPolicy] = None,
        rate_limit: Optional[RateLimit] = None,
        cors_origins: Optional[List[str]] = None
    ) -> None:
        """
            Configure the blueprint with an authentication system and options.

            Associates the given :class:`AuthenticationSystem` with this
            blueprint class so that endpoint handlers can delegate credential
            validation. Optionally overrides the base URL path, the set
            of enabled endpoints, and security constraints.

            :param auth_system: The authentication system instance to use
                                for credential validation.
            :param base_path: Optional base path override for all endpoints
                              registered by this blueprint.
            :param enabled_endpoints: Optional set of endpoint names to
                                      enable. When provided, only the named
                                      endpoints will respond to requests.
            :param access_policy: Optional :class:`AccessPolicy` to apply
                                  to all endpoints in this blueprint.
            :param rate_limit: Optional :class:`RateLimit` to apply to all
                               endpoints in this blueprint.
            :param cors_origins: Optional list of allowed CORS origins for
                                 cross-origin authentication requests.
        """
        cls.auth_system = auth_system

        if base_path is not None:
            cls.base_path = base_path

        if enabled_endpoints is not None:
            cls.enabled_endpoints = enabled_endpoints

        if access_policy is not None:
            cls.access_policy = access_policy

        if rate_limit is not None:
            cls.rate_limit = rate_limit

        if cors_origins is not None:
            cls.cors_origins = cors_origins

        return

    @classmethod
    def is_endpoint_enabled(cls, endpoint_name: str) -> bool:
        """
            Check whether a specific endpoint is enabled.

            An endpoint is considered enabled when the ``enabled_endpoints``
            set contains ``"all"`` or contains the given *endpoint_name*.

            :param endpoint_name: The name of the endpoint to check.

            :returns: True if the endpoint is enabled, False otherwise.
        """
        endpoints = cls.enabled_endpoints
        if endpoints is None:
            endpoints = {cls.ENABLE_ALL_TOKEN}

        is_enabled = cls.ENABLE_ALL_TOKEN in endpoints or endpoint_name in endpoints
        return is_enabled

    @classmethod
    def pre_authenticate(cls, request: Any) -> Optional[AuthError]:
        """
            Hook called before authentication processing.

            Override this method in a subclass to add custom
            pre-authentication logic such as rate limiting, request
            validation, or IP filtering. Return an :class:`AuthError`
            instance to abort the authentication flow and send an error
            response to the client.

            :param request: The incoming HTTP request object.

            :returns: None to continue authentication, or an AuthError
                      to abort with an error response.
        """
        return None

    @classmethod
    def post_authenticate(
        cls,
        request: Any,
        context: AuthenticationContext
    ) -> None:
        """
            Hook called after successful authentication.

            Override this method in a subclass to add custom
            post-authentication logic such as audit logging, session
            creation, or context enrichment.

            :param request: The incoming HTTP request object.
            :param context: The authentication context produced by
                            successful credential validation.
        """
        return

    @classmethod
    def format_error(cls, error: AuthError, status_code: int = 401) -> dict:
        """
            Format an authentication error into a response dictionary.

            Produces a standardized error response following RFC 6749
            conventions. The response dictionary contains the HTTP status
            code, a JSON-serializable body, and the content type.

            :param error: The authentication error to format.
            :param status_code: The HTTP status code for the response.
                                Defaults to 401.

            :returns: A dictionary with ``status``, ``body``, and
                      ``content_type`` keys suitable for returning from
                      an endpoint handler.
        """
        response = {
            "status": status_code,
            "body": error.to_dict(),
            "content_type": cls.JSON_CONTENT_TYPE
        }
        return response

    @classmethod
    def format_success(cls, response: AuthResponse, status_code: int = 200) -> dict:
        """
            Format a successful authentication result into a response dictionary.

            Produces a standardized success response. The response dictionary
            contains the HTTP status code, a JSON-serializable body, and the
            content type.

            :param response: The authentication response to format.
            :param status_code: The HTTP status code for the response.
                                Defaults to 200.

            :returns: A dictionary with ``status``, ``body``, and
                      ``content_type`` keys suitable for returning from
                      an endpoint handler.
        """
        result = {
            "status": status_code,
            "body": response.to_dict(),
            "content_type": cls.JSON_CONTENT_TYPE
        }
        return result

    @classmethod
    def sanitize_error_response(cls, response: dict) -> dict:
        """
            Sanitize an error response to remove sensitive data.

            Inspects the ``body`` of the response dictionary and redacts
            any values associated with sensitive keys (passwords, tokens,
            secrets, etc.). String values in the body are also scanned
            for embedded credential patterns and redacted accordingly.

            :param response: The response dictionary to sanitize. Expected
                             to contain a ``body`` key with a dict value.

            :returns: A new response dictionary with sensitive data removed
                      from the body.
        """
        sanitized = dict(response)
        body = sanitized.get("body")

        if isinstance(body, dict):
            sanitized["body"] = sanitize_dict(body, _SENSITIVE_BODY_KEYS)
        elif isinstance(body, str):
            sanitized["body"] = sanitize_credentials(body)

        return sanitized

    @classmethod
    def handle_internal_error(cls, error: Exception) -> dict:
        """
            Handle an internal error and return a safe response.

            Converts any exception into a generic ``server_error`` response
            that does not expose stack traces, exception class names, or
            other internal details to the client.

            :param error: The exception that occurred during request
                          processing.

            :returns: A response dictionary with a 500 status code and a
                      generic error body safe for client consumption.
        """
        safe_error = AuthError(
            error=cls.SERVER_ERROR_CODE,
            error_description=cls.SERVER_ERROR_MESSAGE
        )
        response = cls.format_error(safe_error, status_code=500)
        return response

    @classmethod
    def get_cors_headers(cls, origin: Optional[str] = None) -> Dict[str, str]:
        """
            Build CORS response headers for the given origin.

            When ``cors_origins`` is configured on the blueprint, this
            method checks whether the provided *origin* is in the allowed
            list and returns the appropriate CORS headers. A wildcard
            entry ``"*"`` in ``cors_origins`` allows any origin.

            :param origin: The ``Origin`` header value from the incoming
                           request. When None or not in the allowed list,
                           an empty dictionary is returned.

            :returns: A dictionary of CORS headers to include in the
                      response. Returns an empty dict when CORS is not
                      configured or the origin is not allowed.
        """
        cors_origins = cls.cors_origins
        if cors_origins is None:
            return {}

        if not origin:
            return {}

        # Check if the origin is allowed
        if cls.CORS_WILDCARD_ORIGIN in cors_origins:
            allowed_origin = cls.CORS_WILDCARD_ORIGIN
        elif origin in cors_origins:
            allowed_origin = origin
        else:
            return {}

        headers = {
            cls.CORS_ALLOW_ORIGIN_HEADER: allowed_origin,
            cls.CORS_ALLOW_METHODS_HEADER: cls.CORS_DEFAULT_METHODS,
            cls.CORS_ALLOW_HEADERS_HEADER: cls.CORS_DEFAULT_HEADERS,
            cls.CORS_ALLOW_CREDENTIALS_HEADER: cls.CORS_ALLOW_CREDENTIALS,
        }
        return headers

    @classmethod
    def set_access_policy(cls, policy: AccessPolicy) -> None:
        """
            Set the access policy for all endpoints in this blueprint.

            The access policy is applied as the class-level default and
            will be inherited by all endpoint descriptors registered via
            ``attach_at`` unless overridden at the endpoint level.

            :param policy: The :class:`AccessPolicy` to apply to all
                           endpoints in this blueprint.
        """
        cls.access_policy = policy
        return

    @classmethod
    def set_rate_limit(cls, rate_limit: RateLimit) -> None:
        """
            Set the rate limit for all endpoints in this blueprint.

            The rate limit is applied as the class-level default and
            will be inherited by all endpoint descriptors registered via
            ``attach_at`` unless overridden at the endpoint level.

            :param rate_limit: The :class:`RateLimit` to apply to all
                               endpoints in this blueprint.
        """
        cls.rate_limit = rate_limit
        return

    # -----------------------------------------------------------------
    # Decorator overrides
    # -----------------------------------------------------------------
    # The base RestEndpoint decorators (create, read, update, delete,
    # attach_at) register descriptors with the global EndpointRegistry
    # at class-definition time.  Because SecurityBlueprint subclasses
    # share leaf names (e.g. both BasicAuth and Session define "login"),
    # this causes EndpointConflictError.
    #
    # The overrides below store endpoint metadata on the handler
    # function itself.  The register() method later reads this metadata
    # and builds properly-pathed descriptors on demand.
    # -----------------------------------------------------------------

    @classmethod
    def attach_at(
        cls,
        leaf: Optional[str] = None,
        path: Optional[str] = None,
        methods: Optional[List[str]] = None,
        version: Optional[str] = None,
        tags: Optional[List[str]] = None,
        access_policy: Optional[AccessPolicy] = None,
        rate_limit: Optional[RateLimit] = None,
        request_schema: Optional[Type] = None,
        response_schema: Optional[Type] = None,
        error_map: Optional[Dict[int, Type]] = None,
        doc: Optional[Doc] = None,
        on_conflict: str = "error",
        absolute: bool = False,
        rest_processing: Optional[bool] = None,
        **extras
    ) -> Callable[[F], F]:
        """
            Decorator that stores endpoint metadata on the handler function.

            Unlike the parent :meth:`RestBlueprint.attach_at`, this method
            does **not** register with the global :class:`EndpointRegistry`.
            Instead it stores the metadata dictionary on the handler under
            the ``_security_endpoint_meta`` attribute.  The :meth:`register`
            method reads this metadata at call time and builds descriptors
            with paths resolved against the calling subclass's ``base_path``.

            :param leaf: URL leaf segment relative to blueprint base.
            :param path: URL path relative to blueprint base (or absolute
                         when *absolute* is True).
            :param methods: HTTP methods for this endpoint.
            :param version: API version string.
            :param tags: Documentation tags.
            :param access_policy: Endpoint-level access policy.
            :param rate_limit: Endpoint-level rate limit.
            :param request_schema: Request body schema.
            :param response_schema: Response body schema.
            :param error_map: Mapping of status codes to error schemas.
            :param doc: Documentation metadata.
            :param on_conflict: Conflict handling (unused, kept for API compat).
            :param absolute: If True, *path* is used as-is without prepending
                             the blueprint base.
            :param rest_processing: Whether a handler declaring a request or
                                    response schema is served through the
                                    REST request/response processing. None
                                    takes the class attribute
                                    :attr:`rest_processing` (False for an
                                    authentication blueprint), resolved
                                    against the subclass :meth:`register`
                                    is called on.
            :param extras: Additional metadata.

            :returns: Decorator that returns the original function unchanged.
        """
        def decorator(func: F) -> F:
            meta = {
                "leaf": leaf,
                "path": path,
                "methods": methods if methods is not None else list(cls.methods),
                "version": version if version is not None else cls.version,
                "tags": tags if tags is not None else list(cls.tags),
                "access_policy": access_policy,
                "rate_limit": rate_limit,
                "request_schema": request_schema,
                "response_schema": response_schema,
                "error_map": error_map,
                "doc": doc,
                "absolute": absolute,
                "rest_processing": rest_processing,
                "extras": extras,
            }
            setattr(func, _ENDPOINT_META_ATTR, meta)
            return func

        return decorator

    @classmethod
    def create(
        cls,
        leaf: Optional[str] = None,
        path: Optional[str] = None,
        version: Optional[str] = None,
        tags: Optional[List[str]] = None,
        access_policy: Optional[AccessPolicy] = None,
        rate_limit: Optional[RateLimit] = None,
        request_schema: Optional[Type] = None,
        response_schema: Optional[Type] = None,
        error_map: Optional[Dict[int, Type]] = None,
        doc: Optional[Doc] = None,
        on_conflict: str = "error",
        rest_processing: Optional[bool] = None,
        **extras
    ) -> Callable[[F], F]:
        """
            Convenience decorator for POST endpoints.

            Delegates to :meth:`attach_at` with ``methods=["POST"]``.
        """
        return cls.attach_at(
            leaf=leaf,
            path=path,
            methods=["POST"],
            version=version,
            tags=tags,
            access_policy=access_policy,
            rate_limit=rate_limit,
            request_schema=request_schema,
            response_schema=response_schema,
            error_map=error_map,
            doc=doc,
            on_conflict=on_conflict,
            rest_processing=rest_processing,
            **extras
        )

    @classmethod
    def read(
        cls,
        leaf: Optional[str] = None,
        path: Optional[str] = None,
        version: Optional[str] = None,
        tags: Optional[List[str]] = None,
        access_policy: Optional[AccessPolicy] = None,
        rate_limit: Optional[RateLimit] = None,
        response_schema: Optional[Type] = None,
        error_map: Optional[Dict[int, Type]] = None,
        doc: Optional[Doc] = None,
        on_conflict: str = "error",
        rest_processing: Optional[bool] = None,
        **extras
    ) -> Callable[[F], F]:
        """
            Convenience decorator for GET endpoints.

            Delegates to :meth:`attach_at` with ``methods=["GET"]``.
        """
        return cls.attach_at(
            leaf=leaf,
            path=path,
            methods=["GET"],
            version=version,
            tags=tags,
            access_policy=access_policy,
            rate_limit=rate_limit,
            request_schema=None,
            response_schema=response_schema,
            error_map=error_map,
            doc=doc,
            on_conflict=on_conflict,
            rest_processing=rest_processing,
            **extras
        )

    @classmethod
    def delete(
        cls,
        leaf: Optional[str] = None,
        path: Optional[str] = None,
        version: Optional[str] = None,
        tags: Optional[List[str]] = None,
        access_policy: Optional[AccessPolicy] = None,
        rate_limit: Optional[RateLimit] = None,
        error_map: Optional[Dict[int, Type]] = None,
        doc: Optional[Doc] = None,
        on_conflict: str = "error",
        rest_processing: Optional[bool] = None,
        **extras
    ) -> Callable[[F], F]:
        """
            Convenience decorator for DELETE endpoints.

            Delegates to :meth:`attach_at` with ``methods=["DELETE"]``.
        """
        return cls.attach_at(
            leaf=leaf,
            path=path,
            methods=["DELETE"],
            version=version,
            tags=tags,
            access_policy=access_policy,
            rate_limit=rate_limit,
            request_schema=None,
            response_schema=None,
            error_map=error_map,
            doc=doc,
            on_conflict=on_conflict,
            rest_processing=rest_processing,
            **extras
        )

    # -----------------------------------------------------------------
    # Registration
    # -----------------------------------------------------------------

    @classmethod
    def register(
        cls,
        router: Optional["RouterProtocol"] = None
    ) -> List[EndpointDescriptor]:
        """
            Register all child endpoints and return their descriptors.

            Scans the class hierarchy for methods decorated with
            :meth:`attach_at` (or its convenience wrappers ``create``,
            ``read``, ``delete``).  For each decorated method the stored
            metadata is combined with the calling subclass's ``base_path``
            to produce an :class:`EndpointDescriptor` with a fully
            resolved path.

            Blueprint-level ``access_policy`` and ``rate_limit`` are
            propagated to descriptors that do not carry their own.

            :param router: Optional router to add endpoints to.  If None,
                          descriptors are returned without router registration.

            :returns: List of EndpointDescriptor objects for all registered
                      endpoints.
        """
        base = cls._get_base_path()
        descriptors = []
        seen_names = set()

        # Walk the MRO to collect decorated methods (subclass first)
        for klass in cls.__mro__:
            if klass is SecurityBlueprint:
                break
            if klass is RestBlueprint:
                break

            for attr_name in list(vars(klass)):
                obj = vars(klass).get(attr_name)

                # The underlying function is where ``attach_at``
                # stashes its metadata marker; we read the metadata
                # from there. ``staticmethod`` / ``classmethod``
                # wrappers store the function on ``__func__``;
                # plain functions are themselves the underlying.
                if isinstance(obj, (classmethod, staticmethod)):
                    underlying = obj.__func__
                else:
                    underlying = obj

                if not callable(underlying):
                    continue

                meta = getattr(underlying, _ENDPOINT_META_ATTR, None)
                if meta is None:
                    continue

                # The MRO is walked most-derived first, so the first
                # definition seen under a name is the one Python will
                # call. A parent's definition of the same name has been
                # overridden and must not produce a second descriptor
                # (same path and method) for the route.
                if attr_name in seen_names:
                    continue
                seen_names.add(attr_name)

                # Resolve the bound form so the request dispatcher
                # can call ``descriptor.handler(request)`` directly:
                #
                # * ``classmethod`` ⇒ bound method that injects the
                #   *most-derived* subclass as the first argument
                #   (so site-supplied collaborators on the subclass
                #   are visible inside the handler — anchoring to the
                #   ``klass`` we found the method on would freeze
                #   ``cls`` at the ancestor that *defined* the
                #   method, hiding subclass overrides).
                # * ``staticmethod`` ⇒ unwrapped function (no
                #   implicit ``self`` / ``cls`` to thread).
                # * plain function ⇒ the function itself.
                #
                # Using ``getattr(cls, attr_name)`` triggers Python's
                # descriptor binding, which produces the right
                # shape for each case without us reproducing the
                # binding rules by hand.
                bound_handler = getattr(cls, attr_name)

                descriptor = cls._build_descriptor(
                    cls._wrap_handler(bound_handler),
                    meta,
                    base,
                )
                descriptors.append(descriptor)

        # Add to router if provided
        if router is not None:
            for descriptor in descriptors:
                router.add_endpoint(descriptor)

        return descriptors

    @classmethod
    def _wrap_handler(cls, handler: Callable) -> Callable:
        """
            Wrap an endpoint handler with the behaviour every
            authentication endpoint shares.

            The wrapper is what the router calls. It:

            * converts an unexpected exception into the generic 500 of
              :meth:`handle_internal_error` (HTTP exceptions pass through
              to the dispatcher);
            * redacts sensitive values from error response bodies with
              :meth:`sanitize_error_response`;
            * adds the CORS headers of :meth:`get_cors_headers` for an
              allowed ``Origin``;
            * keeps the event loop free: when it is called on a thread
              with a running event loop (the ASGI dispatcher) the
              synchronous handler runs on a worker thread and a
              coroutine is returned for the dispatcher to await.

            :param handler: The bound endpoint handler.

            :returns: The wrapped handler.
        """
        @functools.wraps(handler)
        def endpoint_handler(request: Any) -> Any:
            try:
                running_loop = asyncio.get_running_loop()
            except RuntimeError:
                running_loop = None

            if running_loop is None:
                result = cls._call_handler(handler, request)
                return result

            result = cls._call_handler_offloaded(running_loop, handler, request)
            return result

        return endpoint_handler

    @classmethod
    async def _call_handler_offloaded(
        cls,
        running_loop: asyncio.AbstractEventLoop,
        handler: Callable,
        request: Any
    ) -> Any:
        """
            Run a synchronous handler on a worker thread and await it.

            The worker thread remembers the calling event loop so that
            :func:`run_async` drives store coroutines on that loop.

            :param running_loop: The event loop of the dispatcher.
            :param handler: The bound endpoint handler.
            :param request: The incoming HTTP request object.

            :returns: The handler's response.
        """
        context = contextvars.copy_context()

        def call_on_worker_thread() -> Any:
            _handler_thread_state.loop = running_loop
            try:
                rtnval = context.run(cls._call_handler, handler, request)
            finally:
                _handler_thread_state.loop = None
            return rtnval

        result = await running_loop.run_in_executor(None, call_on_worker_thread)
        return result

    @classmethod
    def _call_handler(cls, handler: Callable, request: Any) -> Any:
        """
            Call an endpoint handler and post-process its response.

            :param handler: The bound endpoint handler.
            :param request: The incoming HTTP request object.

            :returns: The handler's response, or the generic 500 response
                      when the handler raised unexpectedly.
        """
        # Imported here because the routing package imports
        # authentication.core while it is being initialised.
        from ccai.webworks.routing.exceptions import HTTPException

        try:
            response = handler(request)
        except HTTPException:
            raise
        except Exception as exc:
            logger.exception(
                "%s: unhandled error in endpoint %s",
                cls.__name__,
                getattr(handler, "__name__", "handler"),
            )
            response = cls.handle_internal_error(exc)

        if isinstance(response, dict):
            status = response.get("status")
            if isinstance(status, int) and status >= 400:
                response = cls.sanitize_error_response(response)

        origin = cls.get_request_header(request, "Origin")
        cors_headers = cls.get_cors_headers(origin)
        if len(cors_headers) > 0:
            cls._add_response_headers(response, cors_headers)

        return response

    @classmethod
    def _add_response_headers(cls, response: Any, headers: Dict[str, str]) -> None:
        """
            Add headers to a handler response of either supported shape.

            :param response: A response dictionary or a Response object.
            :param headers: Header names and values to add.
        """
        if isinstance(response, dict):
            response_headers = response.get("headers")
            if not isinstance(response_headers, dict):
                response_headers = {}
                response["headers"] = response_headers
            response_headers.update(headers)
            return

        header_setter = getattr(response, "set_header", None)
        if callable(header_setter):
            for name, value in headers.items():
                header_setter(name, value)

        return

    @classmethod
    def _build_descriptor(
        cls,
        handler: Callable,
        meta: Dict[str, Any],
        base: Optional[str]
    ) -> EndpointDescriptor:
        """
            Build an :class:`EndpointDescriptor` from handler metadata.

            Resolves the endpoint path against the blueprint *base* path,
            merges tags, and propagates blueprint-level constraints when
            the endpoint does not define its own.

            :param handler: The endpoint handler callable.
            :param meta: The metadata dictionary stored by the decorator.
            :param base: The blueprint base path, or None.

            :returns: A fully resolved EndpointDescriptor.
        """
        leaf = meta.get("leaf")
        raw_path = meta.get("path")
        absolute = meta.get("absolute", False)

        # Resolve the full path
        full_path = cls._resolve_path(leaf, raw_path, base, absolute)

        # Build constraints
        ep_access = meta.get("access_policy")
        ep_rate = meta.get("rate_limit")

        if ep_access is None:
            ep_access = getattr(cls, "access_policy", None)
        if ep_rate is None:
            ep_rate = getattr(cls, "rate_limit", None)

        constraints = EndpointConstraints(
            access_policy=ep_access,
            rate_limit=ep_rate,
            scopes=ep_access.scopes if ep_access else [],
            roles=ep_access.roles if ep_access else []
        )

        # Merge tags
        ep_tags = meta.get("tags") or []
        merged_tags = cls._merge_blueprint_tags(ep_tags)

        # Mark every SecurityBlueprint descriptor as ``"auth"`` so
        # the OpenAPI generator's default filter (which only emits
        # endpoints with ``endpoint_type in {"rest", "auth"}``)
        # includes auth flows in the generated spec. Without this
        # mark the magic-link / OAuth / session endpoints would be
        # silently excluded from the API docs even though they
        # carry full :class:`Doc` metadata. Subclasses that already
        # set their own ``endpoint_type`` (e.g. via
        # ``@attach_at(..., endpoint_type="rest")``) win — their
        # value is preserved.
        descriptor_extras: Dict[str, Any] = dict(meta.get("extras", {}))
        descriptor_extras.setdefault("endpoint_type", cls.DEFAULT_ENDPOINT_TYPE)

        # Carry the request / response schemas where the OpenAPI
        # generator reads them (``extras["rest"]``), so the documented
        # body shapes of the auth endpoints are not dropped.
        request_schema = meta.get("request_schema")
        response_schema = meta.get("response_schema")
        if request_schema is not None or response_schema is not None:
            rest_extras: Dict[str, Any] = dict(descriptor_extras.get("rest", {}))
            if request_schema is not None:
                rest_extras.setdefault("request_schema", request_schema)
            if response_schema is not None:
                rest_extras.setdefault("response_schema", response_schema)

            # The handlers parse the body and shape the response themselves,
            # so by default the schemas only document the route and the
            # route is not served through the REST processing.
            rest_processing = meta.get("rest_processing")
            if rest_processing is None:
                rest_processing = cls.rest_processing
            record_rest_processing(rest_extras, rest_processing)

            descriptor_extras["rest"] = rest_extras

        descriptor = EndpointDescriptor(
            handler=handler,
            module=handler.__module__,
            leaf=None,
            path=full_path,
            methods=list(meta.get("methods", ["GET"])),
            version=meta.get("version"),
            tags=merged_tags if merged_tags else [],
            constraints=constraints,
            doc=meta.get("doc"),
            extras=descriptor_extras,
        )

        return descriptor

    @classmethod
    def _resolve_path(
        cls,
        leaf: Optional[str],
        path: Optional[str],
        base: Optional[str],
        absolute: bool
    ) -> str:
        """
            Compute the full endpoint path.

            When *absolute* is True the *path* is returned unchanged.
            Otherwise the path is constructed from *leaf* or *path* and
            prepended with *base*.

            :param leaf: Leaf segment (e.g. ``"login"``).
            :param path: Explicit path (e.g. ``""`` or ``"/.well-known/..."``).
            :param base: Blueprint base path.
            :param absolute: Whether the path is absolute.

            :returns: The resolved path string.
        """
        # Determine the raw relative path
        if absolute and path is not None:
            return path

        if path is not None:
            raw = path
        elif leaf is not None:
            raw = "/{}".format(leaf)
        else:
            raw = ""

        # Absolute well-known paths bypass the base prefix
        if raw.startswith("/.well-known"):
            return raw

        if base is None:
            return raw

        # Normalise: avoid double slashes
        if raw.startswith("/"):
            return "{}{}".format(base, raw)
        elif raw == "":
            return base
        else:
            return "{}/{}".format(base, raw)

    @classmethod
    def register_with_middleware(
        cls,
        middleware: "AuthenticationMiddleware",
        exclude: bool = False,
        optional: bool = False,
        policy: Optional[AccessPolicy] = None
    ) -> None:
        """
            Register this blueprint's paths with an AuthenticationMiddleware.

            This method configures the middleware to handle authentication
            for the blueprint's endpoint paths. Paths can be excluded from
            authentication, marked as optional, or associated with a
            specific access policy.

            :param middleware: The :class:`AuthenticationMiddleware` to
                               register with.
            :param exclude: If True, blueprint paths are excluded from
                            authentication.
            :param optional: If True, authentication is optional for
                             blueprint paths.
            :param policy: Optional :class:`AccessPolicy` to associate
                           with blueprint paths in the middleware.
        """
        # Register every resolved endpoint path. The middleware's exact
        # path sets are compared by equality, so a path with a route
        # parameter is registered as a compiled pattern instead.
        resolved_policy = policy
        if resolved_policy is None:
            resolved_policy = getattr(cls, "access_policy", None)

        for path in cls.get_endpoint_paths():
            has_parameters = _ROUTE_PARAMETER_PATTERN.search(path) is not None

            if has_parameters:
                pattern = cls._route_path_to_glob(path)
                if exclude:
                    middleware.add_exclude_pattern(pattern)
                elif optional:
                    middleware.add_optional_pattern(pattern)
                if resolved_policy is not None:
                    middleware.add_policy_pattern(pattern, resolved_policy)
                continue

            if exclude:
                middleware.exclude_paths.add(path)
            elif optional:
                middleware.optional_paths.add(path)
            if resolved_policy is not None:
                middleware.path_policies[path] = resolved_policy

        return

    @classmethod
    def _route_path_to_glob(cls, path: str) -> str:
        """
            Convert a route path with parameters to a middleware glob.

            ``{name}`` matches one path segment (``*``) and a path-style
            parameter such as ``{name:path}`` matches any number of
            segments (``**``).

            :param path: The route path, e.g. ``/auth/keys/{key_id}``.

            :returns: The glob pattern, e.g. ``/auth/keys/*``.
        """
        def replace_parameter(match: "re.Match") -> str:
            parameter = match.group(0)
            if parameter.endswith(":path}"):
                return "**"
            return "*"

        rtnval = _ROUTE_PARAMETER_PATTERN.sub(replace_parameter, path)
        return rtnval

    @classmethod
    def get_endpoint_paths(cls) -> List[str]:
        """
            Get all endpoint paths registered by this blueprint.

            Collects the paths from all endpoint descriptors that belong
            to this blueprint, resolved against the blueprint's base path.

            :returns: List of path strings for all registered endpoints.
        """
        descriptors = cls.register()

        paths = []
        for descriptor in descriptors:
            if descriptor.path is not None:
                paths.append(descriptor.path)
            elif descriptor.leaf is not None:
                paths.append("/{}".format(descriptor.leaf))

        return paths

    @classmethod
    def register_with_registry(
        cls,
        registry: Optional[EndpointRegistry] = None,
        on_conflict: str = "replace"
    ) -> List[EndpointDescriptor]:
        """
            Register all blueprint endpoints with an EndpointRegistry.

            Builds endpoint descriptors from decorated handler methods and
            registers each one with the given :class:`EndpointRegistry`.
            A registry is required -- there is no global one to fall back
            to, because a registry belongs to the application that built
            it.

            This method enables integration with the webworks endpoint
            infrastructure so that blueprint endpoints appear alongside
            other registered endpoints in security maps, documentation
            generation, and bulk router loading.

            :param registry: The :class:`EndpointRegistry` to register with.
                             Required; passing None raises ValueError.
            :param on_conflict: Conflict handling strategy passed to the
                                registry. Defaults to ``"replace"`` so that
                                re-registration overwrites previous entries.

            :returns: List of EndpointDescriptor objects that were registered.
        """
        if registry is None:
            errmsg = "register_with_registry requires a registry. Endpoints " \
                     "belong to the application that collected them; there " \
                     "is no process-wide registry to default to."
            raise ValueError(errmsg)

        descriptors = cls.register()

        for descriptor in descriptors:
            registry.register(descriptor, on_conflict=on_conflict)

        return descriptors

    @classmethod
    def integrate(
        cls,
        router: Optional["RouterProtocol"] = None,
        registry: Optional[EndpointRegistry] = None,
        middleware: Optional["AuthenticationMiddleware"] = None,
        access_policy: Optional[AccessPolicy] = None,
        rate_limit: Optional[RateLimit] = None,
        exclude_from_auth: bool = False,
        optional_auth: bool = False
    ) -> List[EndpointDescriptor]:
        """
            Perform full integration with webworks infrastructure.

            This convenience method registers the blueprint's endpoints
            with the :class:`EndpointRegistry`, :class:`Router`, and
            :class:`AuthenticationMiddleware` in a single call. It also
            applies access policy and rate limiting configuration before
            registration so that all descriptors carry the correct
            constraints.

            :param router: Optional :class:`Router` to register endpoints
                           with for request routing.
            :param registry: Optional :class:`EndpointRegistry` to register
                             endpoints with. Defaults to the global registry.
            :param middleware: Optional :class:`AuthenticationMiddleware` to
                              register paths with for authentication handling.
            :param access_policy: Optional :class:`AccessPolicy` to apply
                                  to all blueprint endpoints before
                                  registration.
            :param rate_limit: Optional :class:`RateLimit` to apply to all
                               blueprint endpoints before registration.
            :param exclude_from_auth: If True, blueprint paths are excluded
                                      from authentication in the middleware.
            :param optional_auth: If True, authentication is optional for
                                  blueprint paths in the middleware.

            :returns: List of EndpointDescriptor objects for all registered
                      endpoints.
        """
        # Apply access policy and rate limit before building descriptors
        if access_policy is not None:
            cls.set_access_policy(access_policy)

        if rate_limit is not None:
            cls.set_rate_limit(rate_limit)

        # Register with router (also builds descriptors)
        descriptors = cls.register(router=router)

        # Register with the endpoint registry, when one was supplied. There
        # is no global registry to fall back to.
        if registry is not None:
            for descriptor in descriptors:
                registry.register(descriptor, on_conflict="replace")

        # Register with middleware
        if middleware is not None:
            cls.register_with_middleware(
                middleware,
                exclude=exclude_from_auth,
                optional=optional_auth,
                policy=access_policy
            )

        return descriptors

