"""
.. module:: bearer
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Bearer token authentication blueprint providing JWT token endpoints.

.. moduleauthor:: Code Craft AI LLC

This module provides the :class:`BearerAuthBlueprint` class which extends
:class:`SecurityBlueprint` to offer pre-built endpoints for JWT-based
authentication. The blueprint supports token issuance via multiple grant
types (password, refresh_token, client_credentials), token refresh,
revocation, and introspection.

Endpoints:
    - ``POST <base_path>`` — Issue an access token via a supported grant type.
    - ``POST <base_path>/refresh`` — Refresh an access token using a refresh token.
    - ``POST <base_path>/revoke`` — Revoke an access or refresh token.
    - ``POST <base_path>/introspect`` — Validate and inspect a token's claims.
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


import logging
import time

from typing import Any, Dict, List, Optional, Tuple

from ccai.webworks.authentication.bearer import (
    TokenStore,
    decode_jwt,
    encode_jwt,
    generate_token_id,
    JWTError
)
from ccai.webworks.authentication.basic import IdentityProvider
from ccai.webworks.authentication.core import AuthenticationContext, Principal
from ccai.webworks.authentication.blueprints.responses import (
    AuthError,
    AuthResponse
)
from ccai.webworks.authentication.blueprints.schemas import (
    TokenRequest,
    TokenResponse
)
from ccai.webworks.authentication.blueprints.security import (
    SecurityBlueprint,
    restrict_scope,
    run_async as _run_async,
    split_scope
)
from ccai.webworks.endpoints.doc import Doc


# Module-level logger used by the bearer-blueprint handlers when an
# error is converted into an HTTP error response. Keeping the
# operator visible into JWT decode failures and identity-provider
# misconfiguration is what lets us debug a 500 / 401 / 403 from
# the journal alone.
logger = logging.getLogger(__name__)


def _token_prefix(token_value: Optional[str]) -> str:
    """
        Truncate a token to a journal-safe prefix.

        Logs must not contain live access / refresh tokens. This
        helper returns the first 8 characters of the token followed
        by an ellipsis so the operator can correlate log lines with
        an issued token (or with a client's failing request) without
        exposing the secret.

        :param token_value: The token, or ``None``.

        :returns: A short prefix string suitable for logging.
    """
    if token_value is None:
        return "<none>"
    if len(token_value) == 0:
        return "<empty>"
    if len(token_value) <= 8:
        return "{}…".format(token_value[:4])
    rtnval = "{}…".format(token_value[:8])
    return rtnval


class BearerAuthBlueprint(SecurityBlueprint):
    """
        Blueprint for Bearer Token/JWT authentication endpoints.

        Provides endpoints for token issuance, refresh, revocation, and
        introspection. Token issuance supports multiple OAuth 2.0 grant
        types including ``password``, ``refresh_token``, and
        ``client_credentials``.

        JWT tokens are signed using the configured algorithm and secret.
        Access token and refresh token lifetimes are independently
        configurable.

        Default Endpoints:
            - ``POST /auth/token`` — Issue an access token via a supported
              grant type.
            - ``POST /auth/token/refresh`` — Refresh an access token using
              a refresh token.
            - ``POST /auth/token/revoke`` — Revoke an access or refresh
              token.
            - ``POST /auth/token/introspect`` — Validate and inspect a
              token's claims.

        Class Attributes:
            base_path: Base URL path for all endpoints. Defaults to
                       ``"/auth/token"``.
            tags: Documentation tags applied to all endpoints.
            jwt_secret: The secret key used for signing JWT tokens. Must
                        be set before token issuance can occur.
            jwt_algorithm: The signing algorithm for JWT tokens. Defaults
                           to ``"HS256"``.
            access_token_expires: Lifetime of access tokens in seconds.
                                  Defaults to 3600 (1 hour).
            refresh_token_expires: Lifetime of refresh tokens in seconds.
                                   Defaults to 604800 (7 days).
            token_store: Optional :class:`TokenStore` for persisting and
                         revoking tokens.
            identity_provider: Optional :class:`IdentityProvider` for
                               validating password grant credentials.
            client_store: Optional store of OAuth clients used by the
                          ``client_credentials`` grant. It must offer
                          ``async validate_client_secret(client_id,
                          client_secret) -> bool`` and may offer
                          ``async get_client(client_id) -> dict`` whose
                          ``scopes`` entry lists the scopes the client
                          may be granted. Without a client store the
                          grant validates against the identity provider;
                          with neither it is refused.
            revocation_list: Optional list of revoked token identifiers
                             (see :meth:`get_revocation_list`).

        Scopes:
            A requested ``scope`` is never copied into a token as is.
            The password grant grants only scopes in the principal's
            ``permissions`` (override :meth:`get_allowed_scopes` to
            change that), the client-credentials grant only scopes the
            client is registered for, and a refresh can only keep or
            narrow the scope of the refresh token.
    """

    base_path: str = "/auth/token"
    tags: List[str] = ["Authentication", "Bearer", "JWT"]

    jwt_secret: Optional[str] = None
    jwt_algorithm: str = "HS256"
    access_token_expires: int = 3600
    refresh_token_expires: int = 86400 * 7
    token_store: Optional[TokenStore] = None
    identity_provider: Optional[IdentityProvider] = None
    client_store: Optional[Any] = None

    # --- Class constants ---
    # Override these on a subclass to rebrand wire-format strings without
    # rewriting the handler bodies.

    # Error codes
    ENDPOINT_DISABLED_ERROR_CODE: str = "endpoint_disabled"
    INVALID_REQUEST_ERROR_CODE: str = "invalid_request"
    SERVER_ERROR_CODE: str = "server_error"
    INVALID_GRANT_ERROR_CODE: str = "invalid_grant"
    INVALID_CLIENT_ERROR_CODE: str = "invalid_client"
    INVALID_SCOPE_ERROR_CODE: str = "invalid_scope"
    UNAUTHORIZED_CLIENT_ERROR_CODE: str = "unauthorized_client"
    UNSUPPORTED_GRANT_TYPE_ERROR_CODE: str = "unsupported_grant_type"

    # Authentication scheme label written into AuthenticationContext
    SCHEME_LABEL: str = "Bearer"

    # JWT claim keys
    JWT_CLAIM_SUB: str = "sub"
    JWT_CLAIM_IAT: str = "iat"
    JWT_CLAIM_EXP: str = "exp"
    JWT_CLAIM_TOKEN_TYPE: str = "token_type"
    JWT_CLAIM_SCOPE: str = "scope"
    JWT_CLAIM_JTI: str = "jti"

    # Token type literals
    TOKEN_TYPE_ACCESS: str = "access"
    TOKEN_TYPE_REFRESH: str = "refresh"
    TOKEN_TYPE_BEARER: str = "Bearer"

    # Grant type literals
    GRANT_TYPE_PASSWORD: str = "password"
    GRANT_TYPE_REFRESH_TOKEN: str = "refresh_token"
    GRANT_TYPE_CLIENT_CREDENTIALS: str = "client_credentials"

    @classmethod
    @SecurityBlueprint.create(
        path="",
        request_schema=TokenRequest,
        response_schema=TokenResponse,
        doc=Doc(
            summary="Issue access token",
            description="Exchange credentials for an access token. Supports "
                        "password, refresh_token, and client_credentials "
                        "grant types."
        )
    )
    def token(cls, request: Any) -> dict:
        """
            Issue a new access token.

            Reads the ``grant_type`` field from the request body and
            dispatches to the appropriate grant handler. Supported grant
            types are ``password``, ``refresh_token``, and
            ``client_credentials``.

            The endpoint can be disabled via the ``enabled_endpoints``
            configuration. When disabled, a 404 response is returned.

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

        if grant_type == cls.GRANT_TYPE_PASSWORD:
            response = cls._handle_password_grant(request, body)
            return response

        if grant_type == cls.GRANT_TYPE_REFRESH_TOKEN:
            response = cls._handle_refresh_grant(body)
            return response

        if grant_type == cls.GRANT_TYPE_CLIENT_CREDENTIALS:
            response = cls._handle_client_credentials_grant(body, request)
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
    @SecurityBlueprint.create(
        leaf="refresh",
        doc=Doc(
            summary="Refresh access token",
            description="Exchange a refresh token for a new access token."
        )
    )
    def refresh(cls, request: Any) -> dict:
        """
            Refresh an access token using a refresh token.

            Validates the provided refresh token and issues a new access
            token with a fresh expiration. The refresh token itself is
            not rotated by this endpoint.

            The endpoint can be disabled via the ``enabled_endpoints``
            configuration. When disabled, a 404 response is returned.

            :param request: The incoming HTTP request object. The request
                            body must contain a ``refresh_token`` field.

            :returns: A response dictionary with ``status``, ``body``, and
                      ``content_type`` keys.
        """
        if not cls.is_endpoint_enabled("refresh"):
            error = AuthError(
                error=cls.ENDPOINT_DISABLED_ERROR_CODE,
                error_description="Refresh endpoint is disabled"
            )
            response = cls.format_error(error, status_code=404)
            return response

        body = cls.read_request_data(request)
        if body is None:
            response = cls.invalid_body_response()
            return response

        refresh_token = body.get("refresh_token")

        if not refresh_token:
            error = AuthError(
                error=cls.INVALID_REQUEST_ERROR_CODE,
                error_description="Refresh token is required"
            )
            response = cls.format_error(error, status_code=400)
            return response

        response = cls._handle_refresh_grant(body)
        return response

    @classmethod
    @SecurityBlueprint.create(
        leaf="revoke",
        doc=Doc(
            summary="Revoke token",
            description="Revoke an access or refresh token."
        )
    )
    def revoke(cls, request: Any) -> dict:
        """
            Revoke a token.

            Accepts a token in the request body. A JWT signed by this
            blueprint is put on the revocation list (see
            :meth:`get_revocation_list`), after which the refresh grant
            and introspection refuse it, and so does a
            :class:`BearerAuthenticator` that was given the same list.
            The token is also revoked in the configured
            :attr:`token_store`, when there is one.

            As RFC 7009 requires, the response is 200 whether or not the
            token was known.

            The endpoint can be disabled via the ``enabled_endpoints``
            configuration. When disabled, a 404 response is returned.

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

        response = {
            "status": 200,
            "body": {},
            "content_type": cls.JSON_CONTENT_TYPE
        }
        return response

    @classmethod
    @SecurityBlueprint.create(
        leaf="introspect",
        doc=Doc(
            summary="Introspect token",
            description="Validate and return information about a token."
        )
    )
    def introspect(cls, request: Any) -> dict:
        """
            Introspect a token to check validity and retrieve claims.

            Decodes the provided token using the configured JWT secret
            and algorithm. If the token is valid and has not been
            revoked, returns the decoded claims along with an ``active``
            flag set to True. Otherwise returns ``active`` set to False.

            The endpoint can be disabled via the ``enabled_endpoints``
            configuration. When disabled, a 404 response is returned.

            :param request: The incoming HTTP request object. The request
                            body must contain a ``token`` field.

            :returns: A response dictionary with ``status``, ``body``, and
                      ``content_type`` keys.
        """
        if not cls.is_endpoint_enabled("introspect"):
            error = AuthError(
                error=cls.ENDPOINT_DISABLED_ERROR_CODE,
                error_description="Introspect endpoint is disabled"
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

        if cls.jwt_secret is None:
            error = AuthError(
                error=cls.SERVER_ERROR_CODE,
                error_description="JWT secret is not configured"
            )
            response = cls.format_error(error, status_code=500)
            return response

        inactive_response = {
            "status": 200,
            "body": {"active": False},
            "content_type": cls.JSON_CONTENT_TYPE
        }

        try:
            claims = decode_jwt(
                token_value,
                cls.jwt_secret,
                algorithms=[cls.jwt_algorithm]
            )
        except JWTError as exc:
            # Introspection contract returns ``{"active": false}`` for
            # any decode failure (RFC 7662 §2.2). Operator still wants
            # the cause in the journal because a sudden surge of
            # JWTErrors usually means a misconfigured secret, a clock
            # skew problem, or a client sending the wrong token.
            logger.warning(
                "Token introspection: JWT decode failed for token=%s: %s",
                _token_prefix(token_value),
                exc,
            )
            return inactive_response

        if cls.is_token_revoked(token_value, claims):
            return inactive_response

        response_body = {"active": True}
        response_body.update(claims)

        response = {
            "status": 200,
            "body": response_body,
            "content_type": cls.JSON_CONTENT_TYPE
        }
        return response

    @classmethod
    def get_allowed_scopes(cls, principal: Principal) -> List[str]:
        """
            Get the scopes a principal may be granted.

            The default is the principal's ``permissions``, which is what
            :class:`AccessPolicy` scope requirements are checked against.
            Override this on a subclass to derive grantable scopes
            differently (for example from roles).

            :param principal: The authenticated principal.

            :returns: The scopes that may appear in the principal's tokens.
        """
        rtnval = sorted(str(permission) for permission in principal.permissions)
        return rtnval

    @classmethod
    def _resolve_scope(
        cls,
        requested_scope: Any,
        allowed_scopes: Any
    ) -> Tuple[Optional[str], Optional[dict]]:
        """
            Decide the scope a token is issued with.

            :param requested_scope: The ``scope`` value of the request.
            :param allowed_scopes: The scopes the principal, client or
                                   original grant permits.

            :returns: A tuple of (granted scope, error response). The
                      scope is None when no scope was requested; the
                      error response is set when a scope was requested
                      and none of it may be granted.
        """
        if len(split_scope(requested_scope)) == 0:
            return (None, None)

        granted_scope = restrict_scope(requested_scope, allowed_scopes)
        if granted_scope is None:
            error = AuthError(
                error=cls.INVALID_SCOPE_ERROR_CODE,
                error_description="The requested scope is not allowed"
            )
            response = cls.format_error(error, status_code=400)
            return (None, response)

        return (granted_scope, None)

    @classmethod
    def _handle_password_grant(cls, request: Any, body: Dict[str, Any]) -> dict:
        """
            Handle the password grant type.

            Validates the username and password from the request body
            against the configured :attr:`identity_provider`. On success,
            issues a JWT access token and a refresh token whose scope is
            limited to what the principal is allowed.

            :param request: The incoming HTTP request object.
            :param body: The parsed request body dictionary.

            :returns: A response dictionary with ``status``, ``body``, and
                      ``content_type`` keys.
        """
        username = body.get("username")
        password = body.get("password")

        if not username or not password:
            error = AuthError(
                error=cls.INVALID_REQUEST_ERROR_CODE,
                error_description="Username and password are required for password grant"
            )
            response = cls.format_error(error, status_code=400)
            return response

        provider = cls._resolve_identity_provider()

        if provider is None:
            error = AuthError(
                error=cls.SERVER_ERROR_CODE,
                error_description="No identity provider configured"
            )
            response = cls.format_error(error, status_code=500)
            return response

        # Pre-authentication hook
        pre_error = cls.pre_authenticate(request)
        if pre_error is not None:
            response = cls.format_error(pre_error)
            return response

        throttled_response = cls.check_login_throttle(request, str(username))
        if throttled_response is not None:
            return throttled_response

        principal = _run_async(
            provider.validate_credentials(username, password)
        )

        cls.record_login_attempt(request, str(username), principal is not None)

        if principal is None:
            error = AuthError(
                error=cls.INVALID_GRANT_ERROR_CODE,
                error_description="Invalid username or password"
            )
            response = cls.format_error(error)
            return response

        scope, scope_error = cls._resolve_scope(
            body.get(cls.JWT_CLAIM_SCOPE),
            cls.get_allowed_scopes(principal)
        )
        if scope_error is not None:
            return scope_error

        # Post-authentication hook
        context = AuthenticationContext(
            principal=principal,
            scheme=cls.SCHEME_LABEL
        )
        cls.post_authenticate(request, context)

        # Build JWT access token
        response = cls._issue_tokens(principal.identifier, scope)
        return response

    @classmethod
    def _resolve_identity_provider(cls) -> Optional[IdentityProvider]:
        """
            Find the identity provider that validates user credentials.

            Uses :attr:`identity_provider`, falling back to the provider
            of the Basic authenticator registered in :attr:`auth_system`.

            :returns: The identity provider, or None if there is none.
        """
        provider = cls.identity_provider
        if provider is None and cls.auth_system is not None:
            basic_auth = cls.auth_system.get_authenticator("Basic")
            if basic_auth is not None and hasattr(basic_auth, "_identity_provider"):
                provider = basic_auth._identity_provider

        return provider

    @classmethod
    def _handle_refresh_grant(cls, body: Dict[str, Any]) -> dict:
        """
            Handle the refresh_token grant type.

            Validates the provided refresh token. If a :attr:`token_store`
            is configured, the token is validated through the store.
            Otherwise, the refresh token is decoded as a JWT. A revoked
            refresh token is refused. On success, issues a new JWT access
            token whose scope is the refresh token's scope, or the part
            of it the request asks for.

            :param body: The parsed request body dictionary.

            :returns: A response dictionary with ``status``, ``body``, and
                      ``content_type`` keys.
        """
        refresh_token = body.get("refresh_token")

        if not refresh_token or not isinstance(refresh_token, str):
            error = AuthError(
                error=cls.INVALID_REQUEST_ERROR_CODE,
                error_description="Refresh token is required"
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

        # Validate the refresh token via token_store if available
        if cls.token_store is not None:
            claims = _run_async(
                cls.token_store.validate_token(refresh_token)
            )
            if not isinstance(claims, dict):
                response = cls.format_error(invalid_token_error)
                return response
        else:
            # Decode the refresh token as a JWT
            try:
                claims = decode_jwt(
                    refresh_token,
                    cls.jwt_secret,
                    algorithms=[cls.jwt_algorithm]
                )
            except JWTError as exc:
                # The wire response is the standard "invalid_grant" but
                # the operator wants to know whether this is a normal
                # expired-token case or a misconfigured server-side
                # secret. Log at warning so the cause is recoverable
                # from the journal without exposing the token.
                logger.warning(
                    "Refresh-grant: JWT decode failed for refresh_token=%s: %s",
                    _token_prefix(refresh_token),
                    exc,
                )
                response = cls.format_error(invalid_token_error)
                return response

            if claims.get(cls.JWT_CLAIM_TOKEN_TYPE) != cls.TOKEN_TYPE_REFRESH:
                error = AuthError(
                    error=cls.INVALID_GRANT_ERROR_CODE,
                    error_description="Token is not a refresh token"
                )
                response = cls.format_error(error)
                return response

        # A revoked refresh token must not mint new access tokens
        if cls.is_token_revoked(refresh_token, claims):
            response = cls.format_error(invalid_token_error)
            return response

        subject = claims.get(cls.JWT_CLAIM_SUB)

        if not subject:
            error = AuthError(
                error=cls.INVALID_GRANT_ERROR_CODE,
                error_description="Refresh token missing subject claim"
            )
            response = cls.format_error(error)
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

        access_token = cls._encode_access_token(subject, scope)

        auth_response = AuthResponse(
            access_token=access_token,
            token_type=cls.TOKEN_TYPE_BEARER,
            expires_in=cls.access_token_expires,
            scope=scope
        )
        response = cls.format_success(auth_response)
        return response

    @classmethod
    def _handle_client_credentials_grant(
        cls,
        body: Dict[str, Any],
        request: Optional[Any] = None
    ) -> dict:
        """
            Handle the client_credentials grant type.

            Validates the client identifier and secret, which may arrive
            in an HTTP Basic ``Authorization`` header or in the request
            body. They are checked against :attr:`client_store` when one
            is configured, otherwise against the identity provider. When
            neither is configured the grant is refused: a token is never
            issued for credentials nothing has verified.

            On success, issues a JWT access token whose scope is limited
            to what the client is allowed. No refresh token is issued for
            client credentials grants.

            :param body: The parsed request body dictionary.
            :param request: The incoming HTTP request object, when
                            available.

            :returns: A response dictionary with ``status``, ``body``, and
                      ``content_type`` keys.
        """
        client_id, client_secret = cls.extract_client_credentials(request, body)

        if not client_id or not client_secret:
            error = AuthError(
                error=cls.INVALID_REQUEST_ERROR_CODE,
                error_description="Client ID and client secret are required"
            )
            response = cls.format_error(error, status_code=400)
            return response

        client_id = str(client_id)
        client_secret = str(client_secret)

        client_store = cls.client_store
        provider = cls._resolve_identity_provider()

        if client_store is None and provider is None:
            # Fail closed: nothing can verify the client secret.
            logger.error(
                "%s: client_credentials grant refused because neither a "
                "client_store nor an identity_provider is configured",
                cls.__name__,
            )
            error = AuthError(
                error=cls.UNAUTHORIZED_CLIENT_ERROR_CODE,
                error_description="The client_credentials grant is not available"
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

        # Pre-authentication hook
        if request is not None:
            pre_error = cls.pre_authenticate(request)
            if pre_error is not None:
                response = cls.format_error(pre_error)
                return response

        throttled_response = cls.check_login_throttle(request, client_id)
        if throttled_response is not None:
            return throttled_response

        invalid_client_error = AuthError(
            error=cls.INVALID_CLIENT_ERROR_CODE,
            error_description="Invalid client credentials"
        )

        if client_store is not None:
            is_valid = _run_async(
                client_store.validate_client_secret(client_id, client_secret)
            )
            # Only an explicit True authenticates the client
            is_valid = is_valid is True

            cls.record_login_attempt(request, client_id, is_valid)

            if not is_valid:
                response = cls.format_error(invalid_client_error)
                return response

            subject = client_id
            allowed_scopes = cls._get_client_scopes(client_store, client_id)
        else:
            principal = _run_async(
                provider.validate_credentials(client_id, client_secret)
            )

            cls.record_login_attempt(request, client_id, principal is not None)

            if principal is None:
                response = cls.format_error(invalid_client_error)
                return response

            subject = principal.identifier
            allowed_scopes = cls.get_allowed_scopes(principal)

        scope, scope_error = cls._resolve_scope(
            body.get(cls.JWT_CLAIM_SCOPE),
            allowed_scopes
        )
        if scope_error is not None:
            return scope_error

        access_token = cls._encode_access_token(subject, scope)

        # Client credentials grant does not issue a refresh token
        auth_response = AuthResponse(
            access_token=access_token,
            token_type=cls.TOKEN_TYPE_BEARER,
            expires_in=cls.access_token_expires,
            scope=scope
        )
        response = cls.format_success(auth_response)
        return response

    @classmethod
    def _get_client_scopes(cls, client_store: Any, client_id: str) -> List[str]:
        """
            Read the scopes a client is registered for.

            :param client_store: The configured client store.
            :param client_id: The authenticated client identifier.

            :returns: The client's registered scopes; empty when the
                      store offers no ``get_client`` or the client record
                      lists none.
        """
        client_reader = getattr(client_store, "get_client", None)
        if not callable(client_reader):
            return []

        client = _run_async(client_reader(client_id))
        if not isinstance(client, dict):
            return []

        registered = client.get("scopes")
        if registered is None:
            registered = client.get("scope")

        rtnval = split_scope(registered)
        return rtnval

    @classmethod
    def _encode_access_token(cls, subject: str, scope: Optional[str]) -> str:
        """
            Build and sign a JWT access token.

            :param subject: The subject identifier for the token claims.
            :param scope: The granted scope, or None.

            :returns: The encoded access token.
        """
        now = time.time()

        access_payload = {
            cls.JWT_CLAIM_SUB: subject,
            cls.JWT_CLAIM_IAT: int(now),
            cls.JWT_CLAIM_EXP: int(now) + cls.access_token_expires,
            cls.JWT_CLAIM_TOKEN_TYPE: cls.TOKEN_TYPE_ACCESS,
            cls.JWT_CLAIM_JTI: generate_token_id()
        }
        if scope:
            access_payload[cls.JWT_CLAIM_SCOPE] = scope

        access_token = encode_jwt(
            access_payload,
            cls.jwt_secret,
            algorithm=cls.jwt_algorithm
        )
        return access_token

    @classmethod
    def _issue_tokens(cls, subject: str, scope: Optional[str] = None) -> dict:
        """
            Issue an access token and refresh token for the given subject.

            Creates a JWT access token with ``sub``, ``iat``, ``exp``,
            ``token_type`` and ``jti`` claims. Also creates a JWT refresh
            token with a longer expiration. If a :attr:`token_store` is
            configured, the refresh token is stored for later validation.

            The caller is responsible for the scope: it must already be
            limited to what the subject is allowed.

            :param subject: The subject identifier (principal ID) for the
                            token claims.
            :param scope: Optional scope string to include in the tokens.

            :returns: A response dictionary with ``status``, ``body``, and
                      ``content_type`` keys.
        """
        if cls.jwt_secret is None:
            error = AuthError(
                error=cls.SERVER_ERROR_CODE,
                error_description="JWT secret is not configured"
            )
            response = cls.format_error(error, status_code=500)
            return response

        now = time.time()

        access_token = cls._encode_access_token(subject, scope)

        # Build refresh token payload
        refresh_payload = {
            cls.JWT_CLAIM_SUB: subject,
            cls.JWT_CLAIM_IAT: int(now),
            cls.JWT_CLAIM_EXP: int(now) + cls.refresh_token_expires,
            cls.JWT_CLAIM_TOKEN_TYPE: cls.TOKEN_TYPE_REFRESH,
            cls.JWT_CLAIM_JTI: generate_token_id()
        }
        if scope:
            refresh_payload[cls.JWT_CLAIM_SCOPE] = scope

        refresh_token = encode_jwt(
            refresh_payload,
            cls.jwt_secret,
            algorithm=cls.jwt_algorithm
        )

        # Store the refresh token if a token store is configured
        if cls.token_store is not None:
            _run_async(
                cls.token_store.store_token(
                    refresh_token,
                    refresh_payload,
                    cls.refresh_token_expires
                )
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
