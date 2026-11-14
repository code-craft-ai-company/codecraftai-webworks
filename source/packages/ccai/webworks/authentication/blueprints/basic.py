"""
.. module:: basic
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Basic authentication blueprint providing login and logout endpoints.

.. moduleauthor:: Code Craft AI LLC

This module provides the :class:`BasicAuthBlueprint` class which extends
:class:`SecurityBlueprint` to offer pre-built login and logout endpoints
for username/password authentication. The blueprint delegates credential
validation to a configurable :class:`IdentityProvider` and produces
standardized authentication responses.

Endpoints:
    - ``POST <base_path>/login`` — Authenticate with username and password.
    - ``POST <base_path>/logout`` — End the current authentication session.
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


import logging
import time

from typing import Any, List, Optional

from ccai.webworks.authentication.basic import IdentityProvider
from ccai.webworks.authentication.bearer import (
    encode_jwt,
    extract_bearer_token,
    generate_token_id
)
from ccai.webworks.authentication.core import AuthenticationContext
from ccai.webworks.authentication.blueprints.responses import (
    AuthError,
    AuthResponse
)
from ccai.webworks.authentication.blueprints.schemas import (
    LoginRequest,
    LoginResponse
)
from ccai.webworks.authentication.blueprints.security import (
    SecurityBlueprint,
    run_async as _run_async
)
from ccai.webworks.endpoints.doc import Doc


# Module-level logger for the Basic blueprint handlers.
logger = logging.getLogger(__name__)


class BasicAuthBlueprint(SecurityBlueprint):
    """
        Blueprint for HTTP Basic Authentication endpoints.

        Provides login and logout endpoints for username/password
        authentication. Credential validation is delegated to a
        configurable :class:`IdentityProvider` instance set on the
        ``identity_provider`` class attribute.

        Default Endpoints:
            - ``POST /auth/basic/login`` — Authenticate with username and
              password credentials.
            - ``POST /auth/basic/logout`` — End the current authentication
              session.

        Class Attributes:
            base_path: Base URL path for all endpoints. Defaults to
                       ``"/auth/basic"``.
            tags: Documentation tags applied to all endpoints.
            identity_provider: The :class:`IdentityProvider` used for
                               credential validation. Must be set before
                               the login endpoint can process requests.
            issue_token: When True, a successful login returns a signed
                         JWT access token (``access_token``, ``token_type``
                         and ``expires_in`` in the response body) and
                         logout revokes the token presented with the
                         request. Requires :attr:`jwt_secret`. Defaults
                         to False.
            jwt_secret: The secret key used for signing the access token.
            jwt_algorithm: The signing algorithm. Defaults to ``"HS256"``.
            access_token_expires: Lifetime of the access token in
                                  seconds. Defaults to 3600 (1 hour).
    """

    base_path: str = "/auth/basic"
    tags: List[str] = ["Authentication", "Basic"]

    identity_provider: Optional[IdentityProvider] = None
    issue_token: bool = False
    jwt_secret: Optional[str] = None
    jwt_algorithm: str = "HS256"
    access_token_expires: int = 3600

    # --- Class constants ---
    # Override these on a subclass to rebrand wire-format strings without
    # rewriting the handler bodies.

    # Error codes
    ENDPOINT_DISABLED_ERROR_CODE: str = "endpoint_disabled"
    INVALID_REQUEST_ERROR_CODE: str = "invalid_request"
    SERVER_ERROR_CODE: str = "server_error"
    INVALID_CREDENTIALS_ERROR_CODE: str = "invalid_credentials"

    # Success / response messages
    LOGIN_SUCCESS_MESSAGE: str = "Login successful"
    LOGOUT_MESSAGE: str = "Logged out"

    # Authentication scheme label written into AuthenticationContext
    SCHEME_LABEL: str = "Basic"

    # Token literals used when ``issue_token`` is enabled
    TOKEN_TYPE_BEARER: str = "Bearer"
    TOKEN_TYPE_ACCESS: str = "access"

    @classmethod
    @SecurityBlueprint.create(
        leaf="login",
        request_schema=LoginRequest,
        response_schema=LoginResponse,
        doc=Doc(
            summary="Login with username and password",
            description="Authenticate using HTTP Basic credentials."
        )
    )
    def login(cls, request: Any) -> dict:
        """
            Handle a login request with username and password.

            Validates the provided credentials against the configured
            :attr:`identity_provider`. On success, creates an
            :class:`AuthenticationContext` and invokes the
            :meth:`post_authenticate` hook before returning a success
            response. On failure, returns a 401 error response.

            The endpoint can be disabled via the ``enabled_endpoints``
            configuration. When disabled, a 404 response is returned.

            :param request: The incoming HTTP request object. The request
                            body must contain ``username`` and ``password``
                            fields.

            :returns: A response dictionary with ``status``, ``body``, and
                      ``content_type`` keys.
        """
        if not cls.is_endpoint_enabled("login"):
            error = AuthError(
                error=cls.ENDPOINT_DISABLED_ERROR_CODE,
                error_description="Login endpoint is disabled"
            )
            response = cls.format_error(error, status_code=404)
            return response

        # Pre-authentication hook
        pre_error = cls.pre_authenticate(request)
        if pre_error is not None:
            response = cls.format_error(pre_error)
            return response

        # Extract credentials from request body
        body = cls.read_request_data(request)
        if body is None:
            response = cls.invalid_body_response()
            return response

        username = body.get("username")
        password = body.get("password")

        if not isinstance(username, str) or not isinstance(password, str):
            error = AuthError(
                error=cls.INVALID_REQUEST_ERROR_CODE,
                error_description="Username and password required"
            )
            response = cls.format_error(error)
            return response

        if len(username) == 0 or len(password) == 0:
            error = AuthError(
                error=cls.INVALID_REQUEST_ERROR_CODE,
                error_description="Username and password must not be empty"
            )
            response = cls.format_error(error)
            return response

        # Validate credentials via the identity provider
        if cls.identity_provider is None:
            error = AuthError(
                error=cls.SERVER_ERROR_CODE,
                error_description="No identity provider configured"
            )
            response = cls.format_error(error, status_code=500)
            return response

        if cls.issue_token and cls.jwt_secret is None:
            # A login that promises a token must not silently succeed
            # without one.
            logger.error(
                "%s: issue_token is enabled but jwt_secret is not configured",
                cls.__name__,
            )
            error = AuthError(
                error=cls.SERVER_ERROR_CODE,
                error_description="JWT secret is not configured"
            )
            response = cls.format_error(error, status_code=500)
            return response

        throttled_response = cls.check_login_throttle(request, username)
        if throttled_response is not None:
            return throttled_response

        principal = _run_async(
            cls.identity_provider.validate_credentials(username, password)
        )

        cls.record_login_attempt(request, username, principal is not None)

        if principal is None:
            error = AuthError(
                error=cls.INVALID_CREDENTIALS_ERROR_CODE,
                error_description="Invalid username or password"
            )
            response = cls.format_error(error)
            return response

        # Create authentication context
        context = AuthenticationContext(
            principal=principal,
            scheme=cls.SCHEME_LABEL
        )

        # Post-authentication hook
        cls.post_authenticate(request, context)

        # Build success response
        login_response = LoginResponse(
            authenticated=True,
            principal_id=principal.identifier,
            message=cls.LOGIN_SUCCESS_MESSAGE
        )

        auth_response = AuthResponse()
        if cls.issue_token:
            auth_response = AuthResponse(
                access_token=cls._encode_access_token(principal.identifier),
                token_type=cls.TOKEN_TYPE_BEARER,
                expires_in=cls.access_token_expires
            )

        response = cls.format_success(auth_response, status_code=200)

        # Merge login-specific fields into the response body
        response["body"]["authenticated"] = login_response.authenticated
        response["body"]["principal_id"] = login_response.principal_id
        response["body"]["message"] = login_response.message

        return response

    @classmethod
    @SecurityBlueprint.create(
        leaf="logout",
        doc=Doc(
            summary="Logout",
            description="End the current authentication session."
        )
    )
    def logout(cls, request: Any) -> dict:
        """
            Handle a logout request.

            Ends the current authentication session. When
            :attr:`issue_token` is enabled, the access token presented in
            the ``Authorization: Bearer`` header is put on the revocation
            list (see :meth:`get_revocation_list`), so it stops being
            accepted by a :class:`BearerAuthenticator` that was given the
            same list. Without ``issue_token`` there is no server-side
            state to end: Basic credentials are sent with every request.

            The endpoint can be disabled via the ``enabled_endpoints``
            configuration. When disabled, a 404 response is returned.

            :param request: The incoming HTTP request object.

            :returns: A response dictionary with ``status``, ``body``, and
                      ``content_type`` keys.
        """
        if not cls.is_endpoint_enabled("logout"):
            error = AuthError(
                error=cls.ENDPOINT_DISABLED_ERROR_CODE,
                error_description="Logout endpoint is disabled"
            )
            response = cls.format_error(error, status_code=404)
            return response

        if cls.issue_token:
            authorization = cls.get_request_header(request, "Authorization")
            token_value = extract_bearer_token(authorization or "")
            if token_value is not None:
                cls.revoke_signed_token(
                    token_value, cls.jwt_secret, cls.jwt_algorithm
                )

        response = {
            "status": 200,
            "body": {"message": cls.LOGOUT_MESSAGE},
            "content_type": cls.JSON_CONTENT_TYPE
        }
        return response

    @classmethod
    def _encode_access_token(cls, subject: str) -> str:
        """
            Build and sign the JWT access token returned by login.

            :param subject: The identifier of the authenticated principal.

            :returns: The encoded access token.
        """
        now = time.time()

        payload = {
            "sub": subject,
            "iat": int(now),
            "exp": int(now) + cls.access_token_expires,
            "token_type": cls.TOKEN_TYPE_ACCESS,
            "jti": generate_token_id()
        }

        access_token = encode_jwt(
            payload,
            cls.jwt_secret,
            algorithm=cls.jwt_algorithm
        )
        return access_token
