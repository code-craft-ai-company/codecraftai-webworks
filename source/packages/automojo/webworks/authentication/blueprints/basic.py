"""
.. module:: basic
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Basic authentication blueprint providing login and logout endpoints.

.. moduleauthor:: Automation Mojo LLC

This module provides the :class:`BasicAuthBlueprint` class which extends
:class:`SecurityBlueprint` to offer pre-built login and logout endpoints
for username/password authentication. The blueprint delegates credential
validation to a configurable :class:`IdentityProvider` and produces
standardized authentication responses.

Endpoints:
    - ``POST <base_path>/login`` — Authenticate with username and password.
    - ``POST <base_path>/logout`` — End the current authentication session.
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


import asyncio

from typing import Any, List, Optional

from automojo.webworks.authentication.basic import IdentityProvider
from automojo.webworks.authentication.core import AuthenticationContext
from automojo.webworks.authentication.blueprints.responses import (
    AuthError,
    AuthResponse
)
from automojo.webworks.authentication.blueprints.schemas import (
    LoginRequest,
    LoginResponse
)
from automojo.webworks.authentication.blueprints.security import (
    SecurityBlueprint
)
from automojo.webworks.endpoints.doc import Doc


def _run_async(coro: Any) -> Any:
    """
        Run an asynchronous coroutine synchronously, regardless of
        whether the calling thread already has a running event loop.

        Uvicorn / Hypercorn workers always have a running loop on the
        request-handling thread, so the naive pattern
        ``asyncio.get_event_loop().run_until_complete(coro)`` raises
        ``RuntimeError: This event loop is already running``. When a
        running loop is detected this helper offloads the coroutine
        to a fresh worker thread with its own loop and blocks on the
        thread's result; the sync caller observes a normal return
        value with no nested-loop interleaving.

        :param coro: The coroutine to execute.

        :returns: The result of the coroutine.
    """
    try:
        running_loop = asyncio.get_running_loop()
    except RuntimeError:
        running_loop = None

    if running_loop is None:
        # No running loop on this thread — drive the coroutine here
        # with a fresh loop.
        result = asyncio.run(coro)
        return result

    # A running loop is present (the typical ASGI case). Offload to
    # a worker thread that owns its own loop so we never recurse
    # into the live loop.
    import concurrent.futures

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(asyncio.run, coro)
        result = future.result()

    return result


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
            issue_token: When True, return a JWT token on successful login.
                         Defaults to False.
    """

    base_path: str = "/auth/basic"
    tags: List[str] = ["Authentication", "Basic"]

    identity_provider: Optional[IdentityProvider] = None
    issue_token: bool = False

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
        body = request.json()
        username = body.get("username")
        password = body.get("password")

        if username is None or password is None:
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

        principal = _run_async(
            cls.identity_provider.validate_credentials(username, password)
        )

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

            Ends the current authentication session. The endpoint can be
            disabled via the ``enabled_endpoints`` configuration. When
            disabled, a 404 response is returned.

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

        response = {
            "status": 200,
            "body": {"message": cls.LOGOUT_MESSAGE},
            "content_type": cls.JSON_CONTENT_TYPE
        }
        return response
