"""
.. module:: bearer
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Bearer token authentication blueprint providing JWT token endpoints.

.. moduleauthor:: Automation Mojo LLC

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

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


import asyncio
import secrets
import time

from typing import Any, Dict, List, Optional

from automojo.webworks.authentication.bearer import (
    TokenStore,
    decode_jwt,
    encode_jwt,
    JWTError
)
from automojo.webworks.authentication.basic import IdentityProvider
from automojo.webworks.authentication.core import AuthenticationContext
from automojo.webworks.authentication.blueprints.responses import (
    AuthError,
    AuthResponse
)
from automojo.webworks.authentication.blueprints.schemas import (
    TokenRequest,
    TokenResponse
)
from automojo.webworks.authentication.blueprints.security import (
    SecurityBlueprint
)
from automojo.webworks.endpoints.doc import Doc


def _run_async(coro: Any) -> Any:
    """
        Run an asynchronous coroutine synchronously.

        This helper obtains the current event loop and uses
        ``run_until_complete`` to execute the coroutine. It is used
        internally by :class:`BearerAuthBlueprint` to call async
        :class:`TokenStore` and :class:`IdentityProvider` methods from
        synchronous endpoint handlers.

        :param coro: The coroutine to execute.

        :returns: The result of the coroutine.
    """
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(coro)
    return result


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
    """

    base_path: str = "/auth/token"
    tags: List[str] = ["Authentication", "Bearer", "JWT"]

    jwt_secret: Optional[str] = None
    jwt_algorithm: str = "HS256"
    access_token_expires: int = 3600
    refresh_token_expires: int = 86400 * 7
    token_store: Optional[TokenStore] = None
    identity_provider: Optional[IdentityProvider] = None

    # --- Class constants ---
    # Override these on a subclass to rebrand wire-format strings without
    # rewriting the handler bodies.

    # Error codes
    ENDPOINT_DISABLED_ERROR_CODE: str = "endpoint_disabled"
    INVALID_REQUEST_ERROR_CODE: str = "invalid_request"
    SERVER_ERROR_CODE: str = "server_error"
    INVALID_GRANT_ERROR_CODE: str = "invalid_grant"
    INVALID_CLIENT_ERROR_CODE: str = "invalid_client"
    UNSUPPORTED_GRANT_TYPE_ERROR_CODE: str = "unsupported_grant_type"

    # Authentication scheme label written into AuthenticationContext
    SCHEME_LABEL: str = "Bearer"

    # JWT claim keys
    JWT_CLAIM_SUB: str = "sub"
    JWT_CLAIM_IAT: str = "iat"
    JWT_CLAIM_EXP: str = "exp"
    JWT_CLAIM_TOKEN_TYPE: str = "token_type"
    JWT_CLAIM_SCOPE: str = "scope"

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

        body = request.json()
        grant_type = body.get("grant_type")

        if grant_type == cls.GRANT_TYPE_PASSWORD:
            response = cls._handle_password_grant(request, body)
            return response

        if grant_type == cls.GRANT_TYPE_REFRESH_TOKEN:
            response = cls._handle_refresh_grant(body)
            return response

        if grant_type == cls.GRANT_TYPE_CLIENT_CREDENTIALS:
            response = cls._handle_client_credentials_grant(body)
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

        body = request.json()
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

            Accepts a token in the request body and revokes it via the
            configured :attr:`token_store`. If no token store is
            configured, the endpoint acknowledges the request without
            performing any action.

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

        body = request.json()
        token_value = body.get("token")

        if not token_value:
            error = AuthError(
                error=cls.INVALID_REQUEST_ERROR_CODE,
                error_description="Token is required"
            )
            response = cls.format_error(error, status_code=400)
            return response

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
            and algorithm. If the token is valid, returns the decoded
            claims along with an ``active`` flag set to True. If the
            token is invalid or expired, returns ``active`` set to False.

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

        body = request.json()
        token_value = body.get("token")

        if not token_value:
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

        try:
            claims = decode_jwt(
                token_value,
                cls.jwt_secret,
                algorithms=[cls.jwt_algorithm]
            )
            response_body = {"active": True}
            response_body.update(claims)

            response = {
                "status": 200,
                "body": response_body,
                "content_type": cls.JSON_CONTENT_TYPE
            }
            return response

        except JWTError:
            response = {
                "status": 200,
                "body": {"active": False},
                "content_type": cls.JSON_CONTENT_TYPE
            }
            return response

    @classmethod
    def _handle_password_grant(cls, request: Any, body: Dict[str, Any]) -> dict:
        """
            Handle the password grant type.

            Validates the username and password from the request body
            against the configured :attr:`identity_provider`. On success,
            issues a JWT access token and an opaque refresh token.

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

        # Resolve the identity provider from the blueprint or auth_system
        provider = cls.identity_provider
        if provider is None and cls.auth_system is not None:
            basic_auth = cls.auth_system.get_authenticator("Basic")
            if basic_auth is not None and hasattr(basic_auth, "_identity_provider"):
                provider = basic_auth._identity_provider

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

        principal = _run_async(
            provider.validate_credentials(username, password)
        )

        if principal is None:
            error = AuthError(
                error=cls.INVALID_GRANT_ERROR_CODE,
                error_description="Invalid username or password"
            )
            response = cls.format_error(error)
            return response

        # Post-authentication hook
        context = AuthenticationContext(
            principal=principal,
            scheme=cls.SCHEME_LABEL
        )
        cls.post_authenticate(request, context)

        # Build JWT access token
        response = cls._issue_tokens(principal.identifier, body.get("scope"))
        return response

    @classmethod
    def _handle_refresh_grant(cls, body: Dict[str, Any]) -> dict:
        """
            Handle the refresh_token grant type.

            Validates the provided refresh token. If a :attr:`token_store`
            is configured, the token is validated through the store.
            Otherwise, the refresh token is decoded as a JWT. On success,
            issues a new JWT access token.

            :param body: The parsed request body dictionary.

            :returns: A response dictionary with ``status``, ``body``, and
                      ``content_type`` keys.
        """
        refresh_token = body.get("refresh_token")

        if not refresh_token:
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

        # Validate the refresh token via token_store if available
        if cls.token_store is not None:
            claims = _run_async(
                cls.token_store.validate_token(refresh_token)
            )
            if claims is None:
                error = AuthError(
                    error=cls.INVALID_GRANT_ERROR_CODE,
                    error_description="Invalid or expired refresh token"
                )
                response = cls.format_error(error)
                return response

            subject = claims.get(cls.JWT_CLAIM_SUB)
        else:
            # Decode the refresh token as a JWT
            try:
                claims = decode_jwt(
                    refresh_token,
                    cls.jwt_secret,
                    algorithms=[cls.jwt_algorithm]
                )
            except JWTError:
                error = AuthError(
                    error=cls.INVALID_GRANT_ERROR_CODE,
                    error_description="Invalid or expired refresh token"
                )
                response = cls.format_error(error)
                return response

            if claims.get(cls.JWT_CLAIM_TOKEN_TYPE) != cls.TOKEN_TYPE_REFRESH:
                error = AuthError(
                    error=cls.INVALID_GRANT_ERROR_CODE,
                    error_description="Token is not a refresh token"
                )
                response = cls.format_error(error)
                return response

            subject = claims.get(cls.JWT_CLAIM_SUB)

        if not subject:
            error = AuthError(
                error=cls.INVALID_GRANT_ERROR_CODE,
                error_description="Refresh token missing subject claim"
            )
            response = cls.format_error(error)
            return response

        # Issue a new access token
        now = time.time()
        access_payload = {
            cls.JWT_CLAIM_SUB: subject,
            cls.JWT_CLAIM_IAT: int(now),
            cls.JWT_CLAIM_EXP: int(now) + cls.access_token_expires,
            cls.JWT_CLAIM_TOKEN_TYPE: cls.TOKEN_TYPE_ACCESS
        }

        scope = body.get(cls.JWT_CLAIM_SCOPE)
        if scope:
            access_payload[cls.JWT_CLAIM_SCOPE] = scope

        access_token = encode_jwt(
            access_payload,
            cls.jwt_secret,
            algorithm=cls.jwt_algorithm
        )

        auth_response = AuthResponse(
            access_token=access_token,
            token_type=cls.TOKEN_TYPE_BEARER,
            expires_in=cls.access_token_expires,
            scope=scope
        )
        response = cls.format_success(auth_response)
        return response

    @classmethod
    def _handle_client_credentials_grant(cls, body: Dict[str, Any]) -> dict:
        """
            Handle the client_credentials grant type.

            Validates the ``client_id`` and ``client_secret`` from the
            request body. On success, issues a JWT access token. No
            refresh token is issued for client credentials grants.

            :param body: The parsed request body dictionary.

            :returns: A response dictionary with ``status``, ``body``, and
                      ``content_type`` keys.
        """
        client_id = body.get("client_id")
        client_secret = body.get("client_secret")

        if not client_id or not client_secret:
            error = AuthError(
                error=cls.INVALID_REQUEST_ERROR_CODE,
                error_description="Client ID and client secret are required"
            )
            response = cls.format_error(error, status_code=400)
            return response

        # Validate client credentials via identity_provider if available
        provider = cls.identity_provider
        if provider is None and cls.auth_system is not None:
            basic_auth = cls.auth_system.get_authenticator("Basic")
            if basic_auth is not None and hasattr(basic_auth, "_identity_provider"):
                provider = basic_auth._identity_provider

        if provider is not None:
            principal = _run_async(
                provider.validate_credentials(client_id, client_secret)
            )
            if principal is None:
                error = AuthError(
                    error=cls.INVALID_CLIENT_ERROR_CODE,
                    error_description="Invalid client credentials"
                )
                response = cls.format_error(error)
                return response

            subject = principal.identifier
        else:
            # Without a provider, accept the client_id as the subject
            subject = client_id

        if cls.jwt_secret is None:
            error = AuthError(
                error=cls.SERVER_ERROR_CODE,
                error_description="JWT secret is not configured"
            )
            response = cls.format_error(error, status_code=500)
            return response

        now = time.time()
        access_payload = {
            cls.JWT_CLAIM_SUB: subject,
            cls.JWT_CLAIM_IAT: int(now),
            cls.JWT_CLAIM_EXP: int(now) + cls.access_token_expires,
            cls.JWT_CLAIM_TOKEN_TYPE: cls.TOKEN_TYPE_ACCESS
        }

        scope = body.get(cls.JWT_CLAIM_SCOPE)
        if scope:
            access_payload[cls.JWT_CLAIM_SCOPE] = scope

        access_token = encode_jwt(
            access_payload,
            cls.jwt_secret,
            algorithm=cls.jwt_algorithm
        )

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
    def _issue_tokens(cls, subject: str, scope: Optional[str] = None) -> dict:
        """
            Issue an access token and refresh token for the given subject.

            Creates a JWT access token with ``sub``, ``iat``, ``exp``, and
            ``token_type`` claims. Also creates a JWT refresh token with a
            longer expiration. If a :attr:`token_store` is configured, the
            refresh token is stored for later validation.

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

        # Build access token payload
        access_payload = {
            cls.JWT_CLAIM_SUB: subject,
            cls.JWT_CLAIM_IAT: int(now),
            cls.JWT_CLAIM_EXP: int(now) + cls.access_token_expires,
            cls.JWT_CLAIM_TOKEN_TYPE: cls.TOKEN_TYPE_ACCESS
        }
        if scope:
            access_payload[cls.JWT_CLAIM_SCOPE] = scope

        access_token = encode_jwt(
            access_payload,
            cls.jwt_secret,
            algorithm=cls.jwt_algorithm
        )

        # Build refresh token payload
        refresh_payload = {
            cls.JWT_CLAIM_SUB: subject,
            cls.JWT_CLAIM_IAT: int(now),
            cls.JWT_CLAIM_EXP: int(now) + cls.refresh_token_expires,
            cls.JWT_CLAIM_TOKEN_TYPE: cls.TOKEN_TYPE_REFRESH
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
