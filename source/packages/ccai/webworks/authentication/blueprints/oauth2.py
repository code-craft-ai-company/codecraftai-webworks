"""
.. module:: oauth2
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: OAuth 2.0 authorization blueprint providing authorization and token endpoints.

.. moduleauthor:: Code Craft AI LLC

This module provides the :class:`OAuth2Blueprint` class which extends
:class:`SecurityBlueprint` to offer pre-built endpoints for OAuth 2.0
authorization flows. The blueprint supports the Authorization Code flow
with state parameter validation, Client Credentials flow, PKCE
(code_challenge and code_verifier), and configurable redirect URI
validation.

Endpoints:
    - ``GET <base_path>/authorize`` — Authorization endpoint for initiating auth flows.
    - ``POST <base_path>/token`` — Token endpoint for exchanging codes/credentials.
    - ``GET <base_path>/callback`` — Callback handler for OAuth provider responses.
    - ``POST <base_path>/revoke`` — Token revocation endpoint.
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


import hashlib
import hmac
import inspect
import logging
import secrets
import time

from base64 import urlsafe_b64encode
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlencode

from ccai.webworks.authentication.bearer import (
    JWTError,
    TokenStore,
    decode_jwt,
    encode_jwt,
    generate_token_id,
)
from ccai.webworks.authentication.core import Principal
from ccai.webworks.authentication.blueprints.responses import (
    AuthError,
    AuthResponse
)
from ccai.webworks.authentication.blueprints.schemas import (
    OAuth2TokenRequest,
    TokenResponse,
)
from ccai.webworks.authentication.blueprints.security import (
    ExpiringMemoryStore,
    SecurityBlueprint,
    restrict_scope,
    run_async as _run_async,
    split_scope
)
from ccai.webworks.endpoints.doc import Doc


# Module-level logger for the OAuth 2.0 blueprint handlers.
logger = logging.getLogger(__name__)


class OAuth2ClientStore:
    """
        Abstract base class for OAuth 2.0 client persistence.

        Subclasses must implement all methods to provide client
        registration lookup and redirect URI validation.
    """

    async def get_client(self, client_id: str) -> Optional[Dict[str, Any]]:
        """
            Retrieve a client record by its identifier.

            The returned dictionary should contain at minimum:
                - ``client_id``: The client identifier string.
                - ``redirect_uris``: The registered redirect URIs. An
                  authorization request is refused unless its
                  ``redirect_uri`` is exactly one of them.
                - ``grant_types``: A list of allowed grant types.
                - ``scopes``: The scopes the client may be granted. A
                  requested scope outside this list is never granted.
                - ``client_type``: ``"confidential"`` or ``"public"``.
                  A confidential client must present its secret at the
                  token endpoint; a public client must use PKCE. When
                  the entry is absent, a client record from a client
                  store is treated as confidential.
                - ``client_secret``: The client secret (only needed for
                  the in-memory registry; a store validates secrets
                  through :meth:`validate_client_secret`).

            :param client_id: The client identifier to look up.

            :returns: A dictionary of client data, or None if not found.
        """
        raise NotImplementedError("Subclasses must implement get_client")

    async def validate_client_secret(
        self,
        client_id: str,
        client_secret: str
    ) -> bool:
        """
            Validate a client's secret.

            :param client_id: The client identifier.
            :param client_secret: The secret to validate.

            :returns: True if the secret is valid, False otherwise.
        """
        raise NotImplementedError(
            "Subclasses must implement validate_client_secret"
        )


class AuthorizationCodeStore:
    """
        Abstract base class for authorization code persistence.

        Subclasses must implement all methods to provide authorization
        code storage, retrieval, and consumption.
    """

    async def store_code(
        self,
        code: str,
        client_id: str,
        redirect_uri: str,
        scope: Optional[str],
        state: Optional[str],
        code_challenge: Optional[str],
        code_challenge_method: Optional[str],
        user_id: Optional[str] = None,
        nonce: Optional[str] = None,
        expires_at: Optional[float] = None
    ) -> None:
        """
            Store an authorization code with its associated metadata.

            :param code: The authorization code string.
            :param client_id: The client that requested the code.
            :param redirect_uri: The redirect URI from the authorization request.
            :param scope: The requested scope.
            :param state: The state parameter from the authorization request.
            :param code_challenge: The PKCE code challenge, if provided.
            :param code_challenge_method: The PKCE challenge method, if provided.
            :param user_id: Identifier of the resource owner that approved
                            the request. The tokens issued for the code
                            are issued for this user, so it must be
                            returned by :meth:`consume_code`.
            :param nonce: The OpenID Connect ``nonce`` of the request,
                          echoed into the ID token.
            :param expires_at: Unix time after which the code must no
                               longer be accepted.
        """
        raise NotImplementedError("Subclasses must implement store_code")

    async def consume_code(self, code: str) -> Optional[Dict[str, Any]]:
        """
            Retrieve and consume an authorization code.

            The code is removed from the store after retrieval to prevent
            reuse. The returned dictionary should contain all fields
            stored by :meth:`store_code`, including ``user_id``,
            ``nonce`` and ``expires_at``.

            :param code: The authorization code to consume.

            :returns: A dictionary of code metadata, or None if not found
                      or already consumed.
        """
        raise NotImplementedError("Subclasses must implement consume_code")


def _verify_pkce(code_verifier: str, code_challenge: str,
                 code_challenge_method: Optional[str]) -> bool:
    """
        Verify a PKCE code verifier against the stored code challenge.

        For the ``"S256"`` method, the code verifier is hashed with
        SHA-256 and base64url-encoded, then compared to the stored
        challenge. For the ``"plain"`` method (or when no method is
        specified), the verifier is compared directly. Comparisons run
        in constant time.

        :param code_verifier: The code verifier from the token request.
        :param code_challenge: The code challenge from the authorization request.
        :param code_challenge_method: The challenge method ("S256" or "plain").

        :returns: True if the verifier matches the challenge, False otherwise.
    """
    if not isinstance(code_verifier, str) or not isinstance(code_challenge, str):
        return False

    if code_challenge_method is None or code_challenge_method == "plain":
        is_valid = hmac.compare_digest(
            code_verifier.encode("utf-8"), code_challenge.encode("utf-8")
        )
        return is_valid

    if code_challenge_method == "S256":
        digest = hashlib.sha256(code_verifier.encode("utf-8")).digest()
        computed = urlsafe_b64encode(digest).rstrip(b"=")
        is_valid = hmac.compare_digest(computed, code_challenge.encode("utf-8"))
        return is_valid

    return False


def _build_redirect_url(base_url: str, params: Dict[str, str]) -> str:
    """
        Build a redirect URL by appending query parameters.

        :param base_url: The base redirect URI.
        :param params: Dictionary of query parameters to append.

        :returns: The complete redirect URL with query parameters.
    """
    query_string = urlencode(params)
    separator = "&" if "?" in base_url else "?"
    redirect_url = "{}{}{}".format(base_url, separator, query_string)
    return redirect_url


def _validate_redirect_uri(redirect_uri: str,
                           allowed_uris: List[str]) -> bool:
    """
        Validate a redirect URI against a client's registered URIs.

        Performs exact string matching. A client with no registered
        redirect URIs has no valid redirect URI at all: accepting any
        URI for it would turn the authorization endpoint into an open
        redirector.

        :param redirect_uri: The redirect URI to validate.
        :param allowed_uris: The client's registered redirect URIs.

        :returns: True if the URI is registered, False otherwise.
    """
    if not redirect_uri or not allowed_uris:
        return False

    if not isinstance(allowed_uris, (list, tuple, set, frozenset)):
        return False

    is_valid = redirect_uri in allowed_uris
    return is_valid


def _accepts_keywords(function: Any, names: Tuple[str, ...]) -> bool:
    """
        Check that a callable accepts every one of the given keywords.

        :param function: The callable to inspect.
        :param names: The keyword argument names it must accept.

        :returns: True if every name is a parameter or the callable
                  takes arbitrary keyword arguments.
    """
    try:
        parameters = inspect.signature(function).parameters
    except (TypeError, ValueError):
        return False

    for parameter in parameters.values():
        if parameter.kind == inspect.Parameter.VAR_KEYWORD:
            return True

    for name in names:
        if name not in parameters:
            return False

    return True


class OAuth2Blueprint(SecurityBlueprint):
    """
        Blueprint for OAuth 2.0 authorization server endpoints.

        Provides endpoints for OAuth 2.0 authorization flows including
        the Authorization Code flow with state parameter validation,
        Client Credentials flow, and PKCE support. The blueprint
        delegates client validation to a configurable
        :class:`OAuth2ClientStore` and manages authorization codes via
        an :class:`AuthorizationCodeStore`.

        Default Endpoints:
            - ``GET /oauth/authorize`` — Authorization endpoint for
              initiating auth flows.
            - ``POST /oauth/token`` — Token endpoint for exchanging
              codes or credentials for tokens.
            - ``GET /oauth/callback`` — Callback handler for OAuth
              provider responses.
            - ``POST /oauth/revoke`` — Token revocation endpoint.

        Class Attributes:
            base_path: Base URL path for all endpoints. Defaults to
                       ``"/oauth"``.
            tags: Documentation tags applied to all endpoints.
            client_store: Optional :class:`OAuth2ClientStore` for client
                          lookup and validation.
            authorization_code_store: Optional :class:`AuthorizationCodeStore`
                                      for authorization code persistence.
            token_store: Optional :class:`TokenStore` for token persistence
                         and revocation.
            jwt_secret: The secret key used for signing JWT tokens.
            jwt_algorithm: The signing algorithm for JWT tokens. Defaults
                           to ``"HS256"``.
            access_token_expires: Lifetime of access tokens in seconds.
                                  Defaults to 3600 (1 hour).
            refresh_token_expires: Lifetime of refresh tokens in seconds.
                                   Defaults to 604800 (7 days).
            supported_grant_types: List of supported grant types. Defaults
                                   to ``["authorization_code",
                                   "client_credentials", "refresh_token"]``.
            supported_response_types: List of supported response types.
                                      Defaults to ``["code"]``.
            require_pkce: Whether PKCE is required for authorization code
                          grants. Defaults to False. Public clients must
                          always use PKCE.
            authorization_code_lifetime: Lifetime of an authorization
                                         code in seconds. Defaults to 600.

        Authorization code flow:
            The authorization endpoint acts for a logged-in user: it
            reads the principal the authentication middleware stored on
            the request (``request.auth``) and answers 401
            ``login_required`` without one, so mount it behind the
            site's login. Override :meth:`approve_authorization` to ask
            the user for consent. The code is bound to that user, to the
            client and to the redirect URI, expires after
            :attr:`authorization_code_lifetime` and can be exchanged
            once. At the token endpoint a confidential client must
            authenticate with its secret (HTTP Basic or body fields) and
            a public client must present the PKCE verifier. The issued
            tokens name the user as ``sub`` and the client as
            ``client_id``.

        Redirects:
            The endpoint redirects to a ``redirect_uri`` only after the
            client is known and the URI is exactly one of the client's
            registered ``redirect_uris``. Until then every error is
            answered directly with 400.

        Scopes:
            A client is granted only scopes listed under ``scopes`` in
            its registration; a refresh can keep or narrow the scope of
            the refresh token, never widen it.

        In-memory fallbacks:
            Without stores the blueprint keeps codes, refresh tokens and
            client registrations in memory, per blueprint class. They
            are bounded, codes and tokens expire, and nothing is shared
            between worker processes: configure real stores for any
            deployment with more than one worker.
    """

    base_path: str = "/oauth"
    tags: List[str] = ["Authentication", "OAuth2"]

    # OAuth2 Configuration
    client_store: Optional[OAuth2ClientStore] = None
    authorization_code_store: Optional[AuthorizationCodeStore] = None
    token_store: Optional[TokenStore] = None
    jwt_secret: Optional[str] = None
    jwt_algorithm: str = "HS256"
    access_token_expires: int = 3600
    refresh_token_expires: int = 86400 * 7
    supported_grant_types: List[str] = [
        "authorization_code",
        "client_credentials",
        "refresh_token"
    ]
    supported_response_types: List[str] = ["code"]
    require_pkce: bool = False

    # Lifetime of an authorization code in seconds. RFC 6749 recommends
    # at most ten minutes.
    authorization_code_lifetime: int = 600

    # --- Class constants ---
    # Override these on a subclass to rebrand wire-format strings without
    # rewriting handler bodies.

    # Error codes
    ENDPOINT_DISABLED_ERROR_CODE: str = "endpoint_disabled"
    INVALID_REQUEST_ERROR_CODE: str = "invalid_request"
    INVALID_CLIENT_ERROR_CODE: str = "invalid_client"
    INVALID_GRANT_ERROR_CODE: str = "invalid_grant"
    INVALID_SCOPE_ERROR_CODE: str = "invalid_scope"
    ACCESS_DENIED_ERROR_CODE: str = "access_denied"
    LOGIN_REQUIRED_ERROR_CODE: str = "login_required"
    UNSUPPORTED_GRANT_TYPE_ERROR_CODE: str = "unsupported_grant_type"
    UNSUPPORTED_RESPONSE_TYPE_ERROR_CODE: str = "unsupported_response_type"
    UNAUTHORIZED_CLIENT_ERROR_CODE: str = "unauthorized_client"
    SERVER_ERROR_CODE: str = "server_error"

    # OAuth response & PKCE method literals
    RESPONSE_TYPE_CODE: str = "code"
    PKCE_METHOD_S256: str = "S256"
    PKCE_METHOD_PLAIN: str = "plain"

    # Grant type literals
    GRANT_TYPE_AUTHORIZATION_CODE: str = "authorization_code"
    GRANT_TYPE_CLIENT_CREDENTIALS: str = "client_credentials"
    GRANT_TYPE_REFRESH_TOKEN: str = "refresh_token"

    # Token type literal
    TOKEN_TYPE_BEARER: str = "Bearer"

    # JWT claim keys
    JWT_CLAIM_SUB: str = "sub"
    JWT_CLAIM_IAT: str = "iat"
    JWT_CLAIM_EXP: str = "exp"
    JWT_CLAIM_TOKEN_TYPE: str = "token_type"
    JWT_CLAIM_SCOPE: str = "scope"
    JWT_CLAIM_JTI: str = "jti"
    JWT_CLAIM_CLIENT_ID: str = "client_id"

    # Client registration keys / values
    CLIENT_TYPE_KEY: str = "client_type"
    CLIENT_TYPE_PUBLIC: str = "public"
    CLIENT_TYPE_CONFIDENTIAL: str = "confidential"
    CLIENT_SCOPES_KEY: str = "scopes"

    # Token-type values stored on JWT claims
    TOKEN_TYPE_ACCESS: str = "access"
    TOKEN_TYPE_REFRESH: str = "refresh"

    # OAuth wire parameter names
    OAUTH_PARAM_CODE: str = "code"
    OAUTH_PARAM_STATE: str = "state"
    OAUTH_PARAM_CLIENT_ID: str = "client_id"
    OAUTH_PARAM_REDIRECT_URI: str = "redirect_uri"
    OAUTH_PARAM_RESPONSE_TYPE: str = "response_type"
    OAUTH_PARAM_SCOPE: str = "scope"
    OAUTH_PARAM_CODE_CHALLENGE: str = "code_challenge"
    OAUTH_PARAM_CODE_CHALLENGE_METHOD: str = "code_challenge_method"
    OAUTH_PARAM_NONCE: str = "nonce"
    OAUTH_PARAM_ERROR: str = "error"
    OAUTH_PARAM_ERROR_DESCRIPTION: str = "error_description"

    # Header literals
    LOCATION_HEADER: str = "Location"

    # Random byte length used for authorization-code generation
    AUTHORIZATION_CODE_BYTE_LENGTH: int = 32

    # In-memory fallback stores. Every subclass gets its own (see
    # ``SecurityBlueprint.__init_subclass__``): codes and refresh tokens
    # in a fresh bounded store, client registrations as a copy of the
    # parent's.
    EXPIRING_MEMORY_STORES: Tuple[str, ...] = (
        "_memory_code_store",
        "_memory_token_store",
    )
    REGISTRY_MEMORY_STORES: Tuple[str, ...] = ("_memory_client_store",)

    _memory_code_store: Dict[str, Dict[str, Any]] = ExpiringMemoryStore()
    _memory_client_store: Dict[str, Dict[str, Any]] = {}
    _memory_token_store: Dict[str, Dict[str, Any]] = ExpiringMemoryStore()

    @classmethod
    def _generate_authorization_code(cls) -> str:
        """
            Generate a cryptographically secure authorization code.

            :returns: A random URL-safe string of 32 bytes.
        """
        code = secrets.token_urlsafe(cls.AUTHORIZATION_CODE_BYTE_LENGTH)
        return code

    @classmethod
    def _get_query_param(cls, request: Any, name: str) -> Optional[str]:
        """
            Extract a query parameter from the request.

            Supports request objects with a ``query_params`` attribute,
            a ``params`` attribute, or an ``args`` attribute. Each may
            be a plain dict or any mapping-like object that offers
            ``get`` (the framework ``QueryParams`` class is not a dict).

            :param request: The incoming HTTP request object.
            :param name: The query parameter name.

            :returns: The parameter value, or None if not found.
        """
        for attribute_name in ("query_params", "params", "args"):
            params = getattr(request, attribute_name, None)
            if params is None:
                continue

            getter = getattr(params, "get", None)
            if not callable(getter):
                continue

            value = getter(name)
            if isinstance(value, str):
                return value

        return None

    @classmethod
    def approve_authorization(
        cls,
        request: Any,
        principal: Principal,
        client: Dict[str, Any],
        scope: Optional[str]
    ) -> bool:
        """
            Decide whether the resource owner approves an authorization
            request.

            The default approves every request made by an authenticated
            user. Override this on a subclass to enforce consent, for
            example by consulting a record of the clients and scopes the
            user has approved.

            :param request: The incoming HTTP request object.
            :param principal: The authenticated resource owner.
            :param client: The registration of the requesting client.
            :param scope: The scope that would be granted.

            :returns: True to issue an authorization code, False to
                      answer ``access_denied``.
        """
        return True

    @classmethod
    def _is_public_client(cls, client: Dict[str, Any]) -> bool:
        """
            Decide whether a client is public (cannot keep a secret).

            ``client_type`` in the registration decides when present.
            Otherwise a client from a client store is confidential (its
            secret is checked by the store) and a client in the
            in-memory registry is public exactly when it has no
            ``client_secret``.

            :param client: The client registration.

            :returns: True for a public client.
        """
        client_type = client.get(cls.CLIENT_TYPE_KEY)
        if client_type == cls.CLIENT_TYPE_PUBLIC:
            return True
        if client_type == cls.CLIENT_TYPE_CONFIDENTIAL:
            return False

        if cls.client_store is not None:
            return False

        rtnval = not client.get("client_secret")
        return rtnval

    @classmethod
    def _authenticate_client(
        cls,
        client_id: str,
        client_secret: Optional[str],
        client: Dict[str, Any]
    ) -> bool:
        """
            Verify a client secret.

            :param client_id: The client identifier.
            :param client_secret: The secret the client presented.
            :param client: The client registration.

            :returns: True only if the secret is valid for the client.
        """
        if not client_secret or not isinstance(client_secret, str):
            return False

        if cls.client_store is not None:
            is_valid = _run_async(
                cls.client_store.validate_client_secret(client_id, client_secret)
            )
            rtnval = is_valid is True
            return rtnval

        stored_secret = client.get("client_secret")
        if not stored_secret or not isinstance(stored_secret, str):
            return False

        rtnval = hmac.compare_digest(
            stored_secret.encode("utf-8"), client_secret.encode("utf-8")
        )
        return rtnval

    @classmethod
    def _resolve_client_scope(
        cls,
        requested_scope: Any,
        client: Dict[str, Any]
    ) -> Tuple[Optional[str], bool]:
        """
            Limit a requested scope to what the client is registered for.

            :param requested_scope: The ``scope`` value of the request.
            :param client: The client registration.

            :returns: A tuple of (granted scope, is_allowed). The scope
                      is None when none was requested. is_allowed is
                      False when a scope was requested and none of it is
                      registered for the client.
        """
        if len(split_scope(requested_scope)) == 0:
            return (None, True)

        granted_scope = restrict_scope(
            requested_scope, client.get(cls.CLIENT_SCOPES_KEY)
        )
        if granted_scope is None:
            return (None, False)

        return (granted_scope, True)

    @classmethod
    @SecurityBlueprint.read(
        leaf="authorize",
        doc=Doc(
            summary="Authorization endpoint",
            description="OAuth 2.0 authorization endpoint for initiating "
                        "auth flows. Validates the client, redirect URI, "
                        "and response type, then generates an authorization "
                        "code for the logged-in user and redirects to the "
                        "redirect URI."
        ),
        on_conflict="replace"
    )
    def authorize(cls, request: Any) -> dict:
        """
            Handle an OAuth 2.0 authorization request.

            Validates the client identifier and the redirect URI first;
            until both are known to be registered, errors are answered
            directly and never by redirecting. The request must come
            from an authenticated user (``request.auth``), to whom the
            authorization code is bound. On success, generates an
            authorization code and returns a redirect response to the
            redirect URI with the code and state parameters.

            :param request: The incoming HTTP request object. Query
                            parameters must include ``response_type``,
                            ``client_id``, and ``redirect_uri``. Optional
                            parameters include ``scope``, ``state``,
                            ``nonce``, ``code_challenge``, and
                            ``code_challenge_method``.

            :returns: A response dictionary with ``status``, ``headers``,
                      ``body``, and ``content_type`` keys.
        """
        if not cls.is_endpoint_enabled("authorize"):
            error = AuthError(
                error=cls.ENDPOINT_DISABLED_ERROR_CODE,
                error_description="Authorization endpoint is disabled"
            )
            response = cls.format_error(error, status_code=404)
            return response

        response_type = cls._get_query_param(request, cls.OAUTH_PARAM_RESPONSE_TYPE)
        client_id = cls._get_query_param(request, cls.OAUTH_PARAM_CLIENT_ID)
        redirect_uri = cls._get_query_param(request, cls.OAUTH_PARAM_REDIRECT_URI)
        scope = cls._get_query_param(request, cls.OAUTH_PARAM_SCOPE)
        state = cls._get_query_param(request, cls.OAUTH_PARAM_STATE)
        nonce = cls._get_query_param(request, cls.OAUTH_PARAM_NONCE)
        code_challenge = cls._get_query_param(request, cls.OAUTH_PARAM_CODE_CHALLENGE)
        code_challenge_method = cls._get_query_param(
            request, cls.OAUTH_PARAM_CODE_CHALLENGE_METHOD
        )

        # --- Errors that must not redirect -------------------------------
        # Nothing is sent to the caller-supplied redirect_uri until the
        # client is known and the URI is one the client registered.
        if not client_id:
            error = AuthError(
                error=cls.INVALID_REQUEST_ERROR_CODE,
                error_description="client_id is required"
            )
            response = cls.format_error(error, status_code=400)
            return response

        if not redirect_uri:
            error = AuthError(
                error=cls.INVALID_REQUEST_ERROR_CODE,
                error_description="redirect_uri is required"
            )
            response = cls.format_error(error, status_code=400)
            return response

        client = cls._get_client(client_id)
        if client is None:
            error = AuthError(
                error=cls.INVALID_CLIENT_ERROR_CODE,
                error_description="Unknown client"
            )
            response = cls.format_error(error, status_code=400)
            return response

        allowed_uris = client.get("redirect_uris", [])
        if not _validate_redirect_uri(redirect_uri, allowed_uris):
            error = AuthError(
                error=cls.INVALID_REQUEST_ERROR_CODE,
                error_description="Invalid redirect URI"
            )
            response = cls.format_error(error, status_code=400)
            return response

        # --- Errors reported to the (now trusted) redirect URI ----------
        if not response_type:
            return cls._build_error_redirect(
                redirect_uri=redirect_uri,
                error_code=cls.INVALID_REQUEST_ERROR_CODE,
                error_description="response_type is required",
                state=state
            )

        if response_type not in cls.supported_response_types:
            return cls._build_error_redirect(
                redirect_uri=redirect_uri,
                error_code=cls.UNSUPPORTED_RESPONSE_TYPE_ERROR_CODE,
                error_description="Response type '{}' is not supported".format(
                    response_type
                ),
                state=state
            )

        # PKCE is mandatory for public clients: it is the only thing
        # that ties the code to the party that requested it.
        pkce_required = cls.require_pkce or cls._is_public_client(client)
        if pkce_required and not code_challenge:
            return cls._build_error_redirect(
                redirect_uri=redirect_uri,
                error_code=cls.INVALID_REQUEST_ERROR_CODE,
                error_description="PKCE code_challenge is required",
                state=state
            )

        if code_challenge and code_challenge_method:
            if code_challenge_method not in (cls.PKCE_METHOD_S256, cls.PKCE_METHOD_PLAIN):
                return cls._build_error_redirect(
                    redirect_uri=redirect_uri,
                    error_code=cls.INVALID_REQUEST_ERROR_CODE,
                    error_description="Unsupported code_challenge_method",
                    state=state
                )

        granted_scope, scope_allowed = cls._resolve_client_scope(scope, client)
        if not scope_allowed:
            return cls._build_error_redirect(
                redirect_uri=redirect_uri,
                error_code=cls.INVALID_SCOPE_ERROR_CODE,
                error_description="The requested scope is not allowed for this client",
                state=state
            )

        # --- Resource owner ------------------------------------------------
        # The code is issued on behalf of a logged-in user. Without one
        # there is nobody to authorize the client.
        principal = cls.get_authenticated_principal(request)
        if principal is None:
            error = AuthError(
                error=cls.LOGIN_REQUIRED_ERROR_CODE,
                error_description="The resource owner must be logged in"
            )
            response = cls.format_error(error, status_code=401)
            return response

        if not cls.approve_authorization(request, principal, client, granted_scope):
            return cls._build_error_redirect(
                redirect_uri=redirect_uri,
                error_code=cls.ACCESS_DENIED_ERROR_CODE,
                error_description="The resource owner denied the request",
                state=state
            )

        # Generate authorization code
        code = cls._generate_authorization_code()
        created_at = time.time()
        expires_at = created_at + cls.authorization_code_lifetime

        # Store the authorization code
        code_data = {
            "code": code,
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "scope": granted_scope,
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": code_challenge_method,
            "user_id": principal.identifier,
            "nonce": nonce,
            "created_at": created_at,
            "expires_at": expires_at,
        }

        if cls.authorization_code_store is not None:
            store_code = cls.authorization_code_store.store_code
            if not _accepts_keywords(store_code, ("user_id", "nonce", "expires_at")):
                # A store that cannot keep the resource owner would make
                # the code exchangeable for tokens that belong to nobody.
                logger.error(
                    "%s: authorization code store %s does not accept the "
                    "'user_id', 'nonce' and 'expires_at' arguments of "
                    "store_code; refusing to issue a code",
                    cls.__name__,
                    type(cls.authorization_code_store).__name__,
                )
                return cls._build_error_redirect(
                    redirect_uri=redirect_uri,
                    error_code=cls.SERVER_ERROR_CODE,
                    error_description="Authorization is not configured correctly",
                    state=state
                )

            _run_async(
                store_code(
                    code=code,
                    client_id=client_id,
                    redirect_uri=redirect_uri,
                    scope=granted_scope,
                    state=state,
                    code_challenge=code_challenge,
                    code_challenge_method=code_challenge_method,
                    user_id=principal.identifier,
                    nonce=nonce,
                    expires_at=expires_at
                )
            )
        else:
            cls.note_memory_fallback("authorization_code_store")
            cls.put_in_memory_store(
                cls._memory_code_store,
                code,
                code_data,
                cls.authorization_code_lifetime
            )

        # Build redirect response with code and state
        redirect_params = {cls.OAUTH_PARAM_CODE: code}
        if state is not None:
            redirect_params[cls.OAUTH_PARAM_STATE] = state

        redirect_url = _build_redirect_url(redirect_uri, redirect_params)

        response = {
            "status": 302,
            "headers": {cls.LOCATION_HEADER: redirect_url},
            "body": {},
            "content_type": cls.JSON_CONTENT_TYPE,
        }
        return response

    @classmethod
    @SecurityBlueprint.create(
        leaf="token",
        request_schema=OAuth2TokenRequest,
        response_schema=TokenResponse,
        doc=Doc(
            summary="Token endpoint",
            description="OAuth 2.0 token endpoint for exchanging "
                        "authorization codes or client credentials "
                        "for access tokens."
        ),
        on_conflict="replace"
    )
    def token(cls, request: Any) -> dict:
        """
            Handle an OAuth 2.0 token request.

            Reads the ``grant_type`` field from the request body and
            dispatches to the appropriate grant handler. Supported grant
            types are ``authorization_code``, ``client_credentials``,
            and ``refresh_token``.

            The body may be ``application/x-www-form-urlencoded`` (what
            RFC 6749 clients send) or a JSON object, and the client may
            authenticate with HTTP Basic or with ``client_id`` /
            ``client_secret`` body fields.

            :param request: The incoming HTTP request object. The request
                            body must contain a ``grant_type`` field and
                            any additional fields required by the grant type.

            :returns: A response dictionary with ``status``, ``body``, and
                      ``content_type`` keys.
        """
        if not cls.is_endpoint_enabled("token"):
            error = AuthError(
                error=cls.ENDPOINT_DISABLED_ERROR_CODE,
                error_description="Token endpoint is disabled"
            )
            response = cls.format_error(error, status_code=404)
            return response

        body = cls.read_request_data(request)
        if body is None:
            response = cls.invalid_body_response()
            return response

        grant_type = body.get("grant_type")

        if not grant_type:
            error = AuthError(
                error=cls.INVALID_REQUEST_ERROR_CODE,
                error_description="grant_type is required"
            )
            response = cls.format_error(error, status_code=400)
            return response

        if grant_type not in cls.supported_grant_types:
            error = AuthError(
                error=cls.UNSUPPORTED_GRANT_TYPE_ERROR_CODE,
                error_description="Grant type '{}' is not supported".format(
                    grant_type
                )
            )
            response = cls.format_error(error, status_code=400)
            return response

        if grant_type == cls.GRANT_TYPE_AUTHORIZATION_CODE:
            response = cls._handle_authorization_code_grant(body, request)
            return response

        if grant_type == cls.GRANT_TYPE_CLIENT_CREDENTIALS:
            response = cls._handle_client_credentials_grant(body, request)
            return response

        if grant_type == cls.GRANT_TYPE_REFRESH_TOKEN:
            response = cls._handle_refresh_token_grant(body, request)
            return response

        error = AuthError(
            error=cls.UNSUPPORTED_GRANT_TYPE_ERROR_CODE,
            error_description="Grant type '{}' is not supported".format(
                grant_type
            )
        )
        response = cls.format_error(error, status_code=400)
        return response

    @classmethod
    @SecurityBlueprint.read(
        leaf="callback",
        doc=Doc(
            summary="OAuth callback",
            description="Handle OAuth provider callback with authorization "
                        "code. Validates the state parameter against the "
                        "original request."
        ),
        on_conflict="replace"
    )
    def callback(cls, request: Any) -> dict:
        """
            Handle an OAuth 2.0 callback from a provider.

            Extracts the authorization code and state from the callback
            query parameters. Validates the state parameter against the
            stored authorization request. If an error parameter is
            present, returns an error response.

            :param request: The incoming HTTP request object. Query
                            parameters should include ``code`` and
                            ``state``, or ``error`` and optionally
                            ``error_description``.

            :returns: A response dictionary with ``status``, ``body``, and
                      ``content_type`` keys.
        """
        if not cls.is_endpoint_enabled("callback"):
            error = AuthError(
                error=cls.ENDPOINT_DISABLED_ERROR_CODE,
                error_description="Callback endpoint is disabled"
            )
            response = cls.format_error(error, status_code=404)
            return response

        # Check for error response from provider
        error_code = cls._get_query_param(request, cls.OAUTH_PARAM_ERROR)
        if error_code is not None:
            error_description = cls._get_query_param(
                request, cls.OAUTH_PARAM_ERROR_DESCRIPTION
            )
            state = cls._get_query_param(request, cls.OAUTH_PARAM_STATE)
            error = AuthError(
                error=error_code,
                error_description=error_description
            )
            response = cls.format_error(error, status_code=400)
            if state is not None:
                response["body"][cls.OAUTH_PARAM_STATE] = state
            return response

        code = cls._get_query_param(request, cls.OAUTH_PARAM_CODE)
        state = cls._get_query_param(request, cls.OAUTH_PARAM_STATE)

        if not code:
            error = AuthError(
                error=cls.INVALID_REQUEST_ERROR_CODE,
                error_description="Authorization code is required"
            )
            response = cls.format_error(error, status_code=400)
            return response

        # Look up the authorization code to validate state
        code_data = cls._consume_code(code)
        if code_data is None:
            error = AuthError(
                error=cls.INVALID_GRANT_ERROR_CODE,
                error_description="Invalid or expired authorization code"
            )
            response = cls.format_error(error, status_code=400)
            return response

        # Validate state parameter
        stored_state = code_data.get("state")
        if stored_state is not None and stored_state != state:
            error = AuthError(
                error=cls.INVALID_REQUEST_ERROR_CODE,
                error_description="State parameter mismatch"
            )
            response = cls.format_error(error, status_code=400)
            return response

        response_body = {
            "code": code,
            "client_id": code_data.get("client_id"),
            "scope": code_data.get("scope"),
        }
        if state is not None:
            response_body[cls.OAUTH_PARAM_STATE] = state

        response = {
            "status": 200,
            "body": response_body,
            "content_type": cls.JSON_CONTENT_TYPE,
        }
        return response

    @classmethod
    @SecurityBlueprint.create(
        leaf="revoke",
        doc=Doc(
            summary="Revoke token",
            description="OAuth 2.0 token revocation endpoint."
        ),
        on_conflict="replace"
    )
    def revoke(cls, request: Any) -> dict:
        """
            Revoke an OAuth 2.0 token.

            Accepts a token in the request body (form-encoded or JSON).
            A JWT signed by this blueprint is put on the revocation list
            (see :meth:`get_revocation_list`), after which the refresh
            grant refuses it and so does a :class:`BearerAuthenticator`
            that was given the same list. The token is also removed
            from the configured :attr:`token_store` or the in-memory
            refresh token store.

            As RFC 7009 requires, the response is 200 whether or not the
            token was known.

            :param request: The incoming HTTP request object. The request
                            body must contain a ``token`` field.

            :returns: A response dictionary with ``status``, ``body``, and
                      ``content_type`` keys.
        """
        if not cls.is_endpoint_enabled("revoke"):
            error = AuthError(
                error=cls.ENDPOINT_DISABLED_ERROR_CODE,
                error_description="Revoke endpoint is disabled"
            )
            response = cls.format_error(error, status_code=404)
            return response

        body = cls.read_request_data(request)
        if body is None:
            response = cls.invalid_body_response()
            return response

        token_value = body.get("token")

        if not token_value or not isinstance(token_value, str):
            error = AuthError(
                error=cls.INVALID_REQUEST_ERROR_CODE,
                error_description="Token is required"
            )
            response = cls.format_error(error, status_code=400)
            return response

        # Signed tokens stay valid until they expire unless their
        # identifier is remembered as revoked.
        cls.revoke_signed_token(token_value, cls.jwt_secret, cls.jwt_algorithm)

        if cls.token_store is not None:
            _run_async(cls.token_store.revoke_token(token_value))
        else:
            cls._memory_token_store.pop(token_value, None)

        response = {
            "status": 200,
            "body": {},
            "content_type": cls.JSON_CONTENT_TYPE,
        }
        return response

    @classmethod
    def _get_client(cls, client_id: str) -> Optional[Dict[str, Any]]:
        """
            Retrieve a client record by identifier.

            Uses the configured :attr:`client_store` if available,
            otherwise falls back to the in-memory client store.

            :param client_id: The client identifier to look up.

            :returns: A dictionary of client data, or None if not found.
        """
        if cls.client_store is not None:
            client = _run_async(cls.client_store.get_client(client_id))
        else:
            client = cls._memory_client_store.get(client_id)

        if not isinstance(client, dict):
            return None

        return client

    @classmethod
    def _consume_code(cls, code: str) -> Optional[Dict[str, Any]]:
        """
            Retrieve and consume an authorization code.

            Uses the configured :attr:`authorization_code_store` if
            available, otherwise falls back to the in-memory code store.
            The code is removed from the store after retrieval, and a
            code past its lifetime is refused.

            :param code: The authorization code to consume.

            :returns: A dictionary of code metadata, or None if the code
                      is unknown, already used or expired.
        """
        if cls.authorization_code_store is not None:
            code_data = _run_async(
                cls.authorization_code_store.consume_code(code)
            )
        else:
            code_data = cls._memory_code_store.pop(code, None)

        if not isinstance(code_data, dict):
            return None

        # Enforce the lifetime here as well, whatever the store does
        now = time.time()

        expires_at = code_data.get("expires_at")
        if isinstance(expires_at, (int, float)) and not isinstance(expires_at, bool):
            if now > expires_at:
                return None

        created_at = code_data.get("created_at")
        if isinstance(created_at, (int, float)) and not isinstance(created_at, bool):
            if now > created_at + cls.authorization_code_lifetime:
                return None

        return code_data

    @classmethod
    def _build_error_redirect(
        cls,
        redirect_uri: Optional[str],
        error_code: str,
        error_description: str,
        state: Optional[str]
    ) -> dict:
        """
            Build an error redirect response.

            Callers must only pass a redirect URI that has been validated
            against the client's registration. If no redirect URI is
            given, returns a JSON error response.

            :param redirect_uri: The validated redirect URI to redirect to.
            :param error_code: The OAuth 2.0 error code.
            :param error_description: Human-readable error description.
            :param state: The state parameter from the original request.

            :returns: A response dictionary.
        """
        if redirect_uri is None:
            error = AuthError(
                error=error_code,
                error_description=error_description
            )
            response = cls.format_error(error, status_code=400)
            return response

        params = {
            cls.OAUTH_PARAM_ERROR: error_code,
            cls.OAUTH_PARAM_ERROR_DESCRIPTION: error_description,
        }
        if state is not None:
            params[cls.OAUTH_PARAM_STATE] = state

        redirect_url = _build_redirect_url(redirect_uri, params)

        response = {
            "status": 302,
            "headers": {cls.LOCATION_HEADER: redirect_url},
            "body": {},
            "content_type": cls.JSON_CONTENT_TYPE,
        }
        return response

    @classmethod
    def _handle_authorization_code_grant(
        cls,
        body: Dict[str, Any],
        request: Optional[Any] = None
    ) -> dict:
        """
            Handle the authorization_code grant type.

            The code is exchanged only by the client it was issued to,
            for the redirect URI it was issued for, and only when the
            client proves itself: a confidential client with its secret
            (HTTP Basic or body fields), a public client with the PKCE
            code verifier. On success, issues a JWT access token and
            refresh token for the user who approved the request.

            :param body: The parsed request body dictionary.
            :param request: The incoming HTTP request object, when
                            available.

            :returns: A response dictionary.
        """
        code = body.get("code")
        redirect_uri = body.get("redirect_uri")
        code_verifier = body.get("code_verifier")
        client_id, client_secret = cls.extract_client_credentials(request, body)

        if not code or not isinstance(code, str):
            error = AuthError(
                error=cls.INVALID_REQUEST_ERROR_CODE,
                error_description="Authorization code is required"
            )
            response = cls.format_error(error, status_code=400)
            return response

        if not client_id:
            error = AuthError(
                error=cls.INVALID_REQUEST_ERROR_CODE,
                error_description="client_id is required"
            )
            response = cls.format_error(error, status_code=400)
            return response

        client_id = str(client_id)

        # Consume the authorization code (single use, even on failure)
        code_data = cls._consume_code(code)
        if code_data is None:
            error = AuthError(
                error=cls.INVALID_GRANT_ERROR_CODE,
                error_description="Invalid or expired authorization code"
            )
            response = cls.format_error(error, status_code=400)
            return response

        # The code belongs to one client
        if code_data.get("client_id") != client_id:
            error = AuthError(
                error=cls.INVALID_GRANT_ERROR_CODE,
                error_description="Client ID mismatch"
            )
            response = cls.format_error(error, status_code=400)
            return response

        # ... and to the redirect URI it was issued for
        if not redirect_uri or code_data.get("redirect_uri") != redirect_uri:
            error = AuthError(
                error=cls.INVALID_GRANT_ERROR_CODE,
                error_description="Redirect URI mismatch"
            )
            response = cls.format_error(error, status_code=400)
            return response

        client = cls._get_client(client_id)
        if client is None:
            error = AuthError(
                error=cls.INVALID_CLIENT_ERROR_CODE,
                error_description="Unknown client"
            )
            response = cls.format_error(error, status_code=401)
            return response

        allowed_grants = client.get("grant_types", [])
        if allowed_grants and cls.GRANT_TYPE_AUTHORIZATION_CODE not in allowed_grants:
            error = AuthError(
                error=cls.UNAUTHORIZED_CLIENT_ERROR_CODE,
                error_description="Client not authorized for authorization_code grant"
            )
            response = cls.format_error(error, status_code=400)
            return response

        # Client authentication: a confidential client proves itself
        # with its secret; a secret that is presented must be right.
        is_public = cls._is_public_client(client)
        if client_secret or not is_public:
            if not cls._authenticate_client(client_id, client_secret, client):
                error = AuthError(
                    error=cls.INVALID_CLIENT_ERROR_CODE,
                    error_description="Invalid client credentials"
                )
                response = cls.format_error(error, status_code=401)
                return response

        # Validate PKCE. A public client has no secret, so the verifier
        # is its only proof that it requested the code.
        stored_challenge = code_data.get("code_challenge")
        if stored_challenge:
            if not code_verifier:
                error = AuthError(
                    error=cls.INVALID_REQUEST_ERROR_CODE,
                    error_description="code_verifier is required"
                )
                response = cls.format_error(error, status_code=400)
                return response

            stored_method = code_data.get("code_challenge_method")
            if not _verify_pkce(code_verifier, stored_challenge, stored_method):
                error = AuthError(
                    error=cls.INVALID_GRANT_ERROR_CODE,
                    error_description="PKCE verification failed"
                )
                response = cls.format_error(error, status_code=400)
                return response
        elif cls.require_pkce or is_public:
            error = AuthError(
                error=cls.INVALID_REQUEST_ERROR_CODE,
                error_description="PKCE is required but no code_challenge was provided"
            )
            response = cls.format_error(error, status_code=400)
            return response

        # The tokens are issued for the user who approved the request
        subject = code_data.get("user_id")
        if not subject:
            logger.error(
                "%s: authorization code for client %r carries no user_id; "
                "refusing to issue tokens",
                cls.__name__,
                client_id,
            )
            error = AuthError(
                error=cls.INVALID_GRANT_ERROR_CODE,
                error_description="Authorization code is not bound to a user"
            )
            response = cls.format_error(error, status_code=400)
            return response

        scope = code_data.get("scope")

        response = cls._issue_tokens(
            str(subject),
            scope,
            client_id=client_id,
            nonce=code_data.get("nonce"),
            request=request
        )
        return response

    @classmethod
    def _handle_client_credentials_grant(
        cls,
        body: Dict[str, Any],
        request: Optional[Any] = None
    ) -> dict:
        """
            Handle the client_credentials grant type.

            Validates the client identifier and secret (HTTP Basic or
            body fields). On success, issues a JWT access token whose
            scope is limited to the client's registered scopes. No
            refresh token is issued for client credentials grants.

            :param body: The parsed request body dictionary.
            :param request: The incoming HTTP request object, when
                            available.

            :returns: A response dictionary.
        """
        client_id, client_secret = cls.extract_client_credentials(request, body)

        if not client_id or not client_secret:
            error = AuthError(
                error=cls.INVALID_REQUEST_ERROR_CODE,
                error_description="client_id and client_secret are required"
            )
            response = cls.format_error(error, status_code=400)
            return response

        client_id = str(client_id)

        throttled_response = cls.check_login_throttle(request, client_id)
        if throttled_response is not None:
            return throttled_response

        # Look up the client
        client = cls._get_client(client_id)
        if client is None:
            cls.record_login_attempt(request, client_id, False)
            error = AuthError(
                error=cls.INVALID_CLIENT_ERROR_CODE,
                error_description="Unknown client"
            )
            response = cls.format_error(error, status_code=401)
            return response

        # Validate client secret
        is_valid = cls._authenticate_client(client_id, client_secret, client)

        cls.record_login_attempt(request, client_id, is_valid)

        if not is_valid:
            error = AuthError(
                error=cls.INVALID_CLIENT_ERROR_CODE,
                error_description="Invalid client credentials"
            )
            response = cls.format_error(error, status_code=401)
            return response

        # Check grant type is allowed for client
        allowed_grants = client.get("grant_types", [])
        if allowed_grants and cls.GRANT_TYPE_CLIENT_CREDENTIALS not in allowed_grants:
            error = AuthError(
                error=cls.UNAUTHORIZED_CLIENT_ERROR_CODE,
                error_description="Client not authorized for client_credentials grant"
            )
            response = cls.format_error(error, status_code=400)
            return response

        scope, scope_allowed = cls._resolve_client_scope(body.get("scope"), client)
        if not scope_allowed:
            error = AuthError(
                error=cls.INVALID_SCOPE_ERROR_CODE,
                error_description="The requested scope is not allowed for this client"
            )
            response = cls.format_error(error, status_code=400)
            return response

        response = cls._issue_access_token_only(client_id, scope, client_id=client_id)
        return response

    @classmethod
    def _handle_refresh_token_grant(
        cls,
        body: Dict[str, Any],
        request: Optional[Any] = None
    ) -> dict:
        """
            Handle the refresh_token grant type.

            Validates the provided refresh token: it must be a refresh
            token signed by this blueprint, known to the token store,
            not revoked, and (when the request names a client) issued to
            that client. Issues a new access token whose scope is the
            refresh token's scope, or the part of it the request asks
            for.

            :param body: The parsed request body dictionary.
            :param request: The incoming HTTP request object, when
                            available.

            :returns: A response dictionary.
        """
        refresh_token = body.get("refresh_token")

        if not refresh_token or not isinstance(refresh_token, str):
            error = AuthError(
                error=cls.INVALID_REQUEST_ERROR_CODE,
                error_description="refresh_token is required"
            )
            response = cls.format_error(error, status_code=400)
            return response

        if cls.jwt_secret is None:
            error = AuthError(
                error=cls.SERVER_ERROR_CODE,
                error_description="JWT secret is not configured"
            )
            response = cls.format_error(error, status_code=500)
            return response

        invalid_token_error = AuthError(
            error=cls.INVALID_GRANT_ERROR_CODE,
            error_description="Invalid or expired refresh token"
        )

        # Validate refresh token
        if cls.token_store is not None:
            claims = _run_async(
                cls.token_store.validate_token(refresh_token)
            )
            if not isinstance(claims, dict):
                response = cls.format_error(invalid_token_error)
                return response
        else:
            # Check in-memory token store
            claims = cls._memory_token_store.get(refresh_token)
            if not isinstance(claims, dict):
                response = cls.format_error(invalid_token_error)
                return response

            # Check expiration
            if claims.get(cls.JWT_CLAIM_EXP, 0) < time.time():
                cls._memory_token_store.pop(refresh_token, None)
                error = AuthError(
                    error=cls.INVALID_GRANT_ERROR_CODE,
                    error_description="Refresh token has expired"
                )
                response = cls.format_error(error)
                return response

        # A token that looks like one of this blueprint's JWTs must
        # verify as a refresh token; an opaque token from a custom
        # token store is taken on the store's word.
        if refresh_token.count(".") == 2:
            try:
                signed_claims = decode_jwt(
                    refresh_token,
                    cls.jwt_secret,
                    algorithms=[cls.jwt_algorithm]
                )
            except JWTError as exc:
                logger.warning(
                    "%s: refresh token failed verification: %s", cls.__name__, exc
                )
                response = cls.format_error(invalid_token_error)
                return response

            if signed_claims.get(cls.JWT_CLAIM_TOKEN_TYPE) != cls.TOKEN_TYPE_REFRESH:
                response = cls.format_error(invalid_token_error)
                return response

            claims = signed_claims

        # A revoked refresh token must not mint new access tokens
        if cls.is_token_revoked(refresh_token, claims):
            response = cls.format_error(invalid_token_error)
            return response

        subject = claims.get(cls.JWT_CLAIM_SUB)

        if not subject:
            error = AuthError(
                error=cls.INVALID_GRANT_ERROR_CODE,
                error_description="Refresh token missing subject"
            )
            response = cls.format_error(error)
            return response

        # The refresh token belongs to the client it was issued to
        token_client_id = claims.get(cls.JWT_CLAIM_CLIENT_ID)
        client_id, client_secret = cls.extract_client_credentials(request, body)

        if client_id and token_client_id and str(client_id) != str(token_client_id):
            response = cls.format_error(invalid_token_error)
            return response

        if client_secret:
            presenting_client_id = str(client_id or token_client_id or "")
            client = cls._get_client(presenting_client_id)
            if client is None or not cls._authenticate_client(
                presenting_client_id, client_secret, client
            ):
                error = AuthError(
                    error=cls.INVALID_CLIENT_ERROR_CODE,
                    error_description="Invalid client credentials"
                )
                response = cls.format_error(error, status_code=401)
                return response

        # The new access token carries the scope of the refresh token.
        # A request may narrow it but never widen it.
        original_scope = claims.get(cls.JWT_CLAIM_SCOPE)
        requested_scope = body.get(cls.JWT_CLAIM_SCOPE)

        if len(split_scope(requested_scope)) == 0:
            scope = restrict_scope(original_scope, original_scope)
        else:
            requested_tokens = split_scope(requested_scope)
            original_tokens = split_scope(original_scope)
            exceeds_original = [
                token for token in requested_tokens
                if token not in original_tokens
            ]
            if len(exceeds_original) > 0:
                error = AuthError(
                    error=cls.INVALID_SCOPE_ERROR_CODE,
                    error_description="Requested scope exceeds the scope of the refresh token"
                )
                response = cls.format_error(error, status_code=400)
                return response
            scope = " ".join(requested_tokens)

        response = cls._issue_access_token_only(
            str(subject), scope, client_id=token_client_id
        )
        return response

    @classmethod
    def _encode_token(
        cls,
        subject: str,
        scope: Optional[str],
        token_type: str,
        lifetime: int,
        client_id: Optional[str] = None
    ) -> Tuple[str, Dict[str, Any]]:
        """
            Build and sign a JWT.

            :param subject: The subject identifier for the token claims.
            :param scope: The granted scope, or None.
            :param token_type: ``"access"`` or ``"refresh"``.
            :param lifetime: The token lifetime in seconds.
            :param client_id: The client the token is issued to, or None.

            :returns: A tuple of (encoded token, claims).
        """
        now = time.time()

        payload = {
            cls.JWT_CLAIM_SUB: subject,
            cls.JWT_CLAIM_IAT: int(now),
            cls.JWT_CLAIM_EXP: int(now) + lifetime,
            cls.JWT_CLAIM_TOKEN_TYPE: token_type,
            cls.JWT_CLAIM_JTI: generate_token_id(),
        }
        if scope:
            payload[cls.JWT_CLAIM_SCOPE] = scope
        if client_id:
            payload[cls.JWT_CLAIM_CLIENT_ID] = client_id

        token = encode_jwt(
            payload,
            cls.jwt_secret,
            algorithm=cls.jwt_algorithm
        )
        return (token, payload)

    @classmethod
    def _issue_tokens(
        cls,
        subject: str,
        scope: Optional[str] = None,
        client_id: Optional[str] = None,
        nonce: Optional[str] = None,
        request: Optional[Any] = None
    ) -> dict:
        """
            Issue an access token and refresh token for the given subject.

            The caller is responsible for the scope: it must already be
            limited to what the client is allowed.

            :param subject: The subject identifier for the token claims.
            :param scope: Optional scope string.
            :param client_id: The client the tokens are issued to.
            :param nonce: The OpenID Connect nonce of the authorization
                          request (used by :class:`OIDCBlueprint`).
            :param request: The token request (used by
                            :class:`OIDCBlueprint` to derive the issuer).

            :returns: A response dictionary.
        """
        if cls.jwt_secret is None:
            error = AuthError(
                error=cls.SERVER_ERROR_CODE,
                error_description="JWT secret is not configured"
            )
            response = cls.format_error(error, status_code=500)
            return response

        access_token, _ = cls._encode_token(
            subject, scope, cls.TOKEN_TYPE_ACCESS,
            cls.access_token_expires, client_id
        )

        refresh_token, refresh_payload = cls._encode_token(
            subject, scope, cls.TOKEN_TYPE_REFRESH,
            cls.refresh_token_expires, client_id
        )

        # Store refresh token
        if cls.token_store is not None:
            _run_async(
                cls.token_store.store_token(
                    refresh_token,
                    refresh_payload,
                    cls.refresh_token_expires
                )
            )
        else:
            cls.note_memory_fallback("token_store")
            cls.put_in_memory_store(
                cls._memory_token_store,
                refresh_token,
                refresh_payload,
                cls.refresh_token_expires
            )

        auth_response = AuthResponse(
            access_token=access_token,
            token_type=cls.TOKEN_TYPE_BEARER,
            expires_in=cls.access_token_expires,
            refresh_token=refresh_token,
            scope=scope
        )
        response = cls.format_success(auth_response)
        return response

    @classmethod
    def _issue_access_token_only(
        cls,
        subject: str,
        scope: Optional[str] = None,
        client_id: Optional[str] = None
    ) -> dict:
        """
            Issue an access token without a refresh token.

            Used for client credentials grants where refresh tokens
            are not appropriate, and for refreshes.

            :param subject: The subject identifier for the token claims.
            :param scope: Optional scope string.
            :param client_id: The client the token is issued to.

            :returns: A response dictionary.
        """
        if cls.jwt_secret is None:
            error = AuthError(
                error=cls.SERVER_ERROR_CODE,
                error_description="JWT secret is not configured"
            )
            response = cls.format_error(error, status_code=500)
            return response

        access_token, _ = cls._encode_token(
            subject, scope, cls.TOKEN_TYPE_ACCESS,
            cls.access_token_expires, client_id
        )

        auth_response = AuthResponse(
            access_token=access_token,
            token_type=cls.TOKEN_TYPE_BEARER,
            expires_in=cls.access_token_expires,
            scope=scope
        )
        response = cls.format_success(auth_response)
        return response
