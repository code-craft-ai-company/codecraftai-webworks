"""
.. module:: oauth2
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: OAuth 2.0 authorization blueprint providing authorization and token endpoints.

.. moduleauthor:: Automation Mojo LLC

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

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


import asyncio
import hashlib
import secrets
import time

from base64 import urlsafe_b64encode
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode, urlparse

from automojo.webworks.authentication.bearer import (
    TokenStore,
    decode_jwt,
    encode_jwt,
    JWTError
)
from automojo.webworks.authentication.blueprints.responses import (
    AuthError,
    AuthResponse
)
from automojo.webworks.authentication.blueprints.schemas import (
    OAuth2AuthorizeRequest,
    OAuth2TokenRequest,
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
        internally by :class:`OAuth2Blueprint` to call async store
        methods from synchronous endpoint handlers.

        :param coro: The coroutine to execute.

        :returns: The result of the coroutine.
    """
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(coro)
    return result


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
                - ``client_secret``: The client secret for authentication.
                - ``redirect_uris``: A list of allowed redirect URIs.
                - ``grant_types``: A list of allowed grant types.

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
        code_challenge_method: Optional[str]
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
        """
        raise NotImplementedError("Subclasses must implement store_code")

    async def consume_code(self, code: str) -> Optional[Dict[str, Any]]:
        """
            Retrieve and consume an authorization code.

            The code is removed from the store after retrieval to prevent
            reuse. The returned dictionary should contain all fields
            stored by :meth:`store_code`.

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
        specified), the verifier is compared directly.

        :param code_verifier: The code verifier from the token request.
        :param code_challenge: The code challenge from the authorization request.
        :param code_challenge_method: The challenge method ("S256" or "plain").

        :returns: True if the verifier matches the challenge, False otherwise.
    """
    if code_challenge_method is None or code_challenge_method == "plain":
        is_valid = (code_verifier == code_challenge)
        return is_valid

    if code_challenge_method == "S256":
        digest = hashlib.sha256(code_verifier.encode("ascii")).digest()
        computed = urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
        is_valid = (computed == code_challenge)
        return is_valid

    # Unknown method — reject
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
        Validate a redirect URI against a list of allowed URIs.

        Performs exact string matching against the allowed URIs list.
        If the allowed list is empty, all URIs are accepted.

        :param redirect_uri: The redirect URI to validate.
        :param allowed_uris: List of allowed redirect URIs.

        :returns: True if the URI is allowed, False otherwise.
    """
    if not allowed_uris:
        return True

    is_valid = redirect_uri in allowed_uris
    return is_valid


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
                          grants. Defaults to False.
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

    # In-memory fallback stores
    _memory_code_store: Dict[str, Dict[str, Any]] = {}
    _memory_client_store: Dict[str, Dict[str, Any]] = {}
    _memory_token_store: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def _generate_authorization_code(cls) -> str:
        """
            Generate a cryptographically secure authorization code.

            :returns: A random URL-safe string of 32 bytes.
        """
        code = secrets.token_urlsafe(32)
        return code

    @classmethod
    def _get_query_param(cls, request: Any, name: str) -> Optional[str]:
        """
            Extract a query parameter from the request.

            Supports request objects with a ``query_params`` attribute
            (dict-like), a ``params`` attribute, or an ``args`` attribute.
            Falls back to parsing the ``query_string`` attribute if
            available.

            :param request: The incoming HTTP request object.
            :param name: The query parameter name.

            :returns: The parameter value, or None if not found.
        """
        if hasattr(request, "query_params"):
            params = request.query_params
            if isinstance(params, dict):
                return params.get(name)

        if hasattr(request, "params"):
            params = request.params
            if isinstance(params, dict):
                return params.get(name)

        if hasattr(request, "args"):
            args = request.args
            if isinstance(args, dict):
                return args.get(name)

        return None

    @classmethod
    @SecurityBlueprint.read(
        leaf="authorize",
        doc=Doc(
            summary="Authorization endpoint",
            description="OAuth 2.0 authorization endpoint for initiating "
                        "auth flows. Validates the client, redirect URI, "
                        "and response type, then generates an authorization "
                        "code and redirects to the redirect URI."
        ),
        on_conflict="replace"
    )
    def authorize(cls, request: Any) -> dict:
        """
            Handle an OAuth 2.0 authorization request.

            Validates the client identifier, redirect URI, and response
            type. If PKCE is required, validates the presence of a code
            challenge. On success, generates an authorization code and
            returns a redirect response to the redirect URI with the
            code and state parameters.

            :param request: The incoming HTTP request object. Query
                            parameters must include ``response_type``,
                            ``client_id``, and ``redirect_uri``. Optional
                            parameters include ``scope``, ``state``,
                            ``code_challenge``, and ``code_challenge_method``.

            :returns: A response dictionary with ``status``, ``headers``,
                      ``body``, and ``content_type`` keys.
        """
        if not cls.is_endpoint_enabled("authorize"):
            error = AuthError(
                error="endpoint_disabled",
                error_description="Authorization endpoint is disabled"
            )
            response = cls.format_error(error, status_code=404)
            return response

        # Extract query parameters
        response_type = cls._get_query_param(request, "response_type")
        client_id = cls._get_query_param(request, "client_id")
        redirect_uri = cls._get_query_param(request, "redirect_uri")
        scope = cls._get_query_param(request, "scope")
        state = cls._get_query_param(request, "state")
        code_challenge = cls._get_query_param(request, "code_challenge")
        code_challenge_method = cls._get_query_param(
            request, "code_challenge_method"
        )

        # Validate required parameters
        if not response_type:
            return cls._build_error_redirect(
                redirect_uri=redirect_uri,
                error_code="invalid_request",
                error_description="response_type is required",
                state=state
            )

        if not client_id:
            return cls._build_error_redirect(
                redirect_uri=redirect_uri,
                error_code="invalid_request",
                error_description="client_id is required",
                state=state
            )

        if not redirect_uri:
            error = AuthError(
                error="invalid_request",
                error_description="redirect_uri is required"
            )
            response = cls.format_error(error, status_code=400)
            return response

        # Validate response type
        if response_type not in cls.supported_response_types:
            return cls._build_error_redirect(
                redirect_uri=redirect_uri,
                error_code="unsupported_response_type",
                error_description="Response type '{}' is not supported".format(
                    response_type
                ),
                state=state
            )

        # Validate client
        client = cls._get_client(client_id)
        if client is None:
            return cls._build_error_redirect(
                redirect_uri=redirect_uri,
                error_code="invalid_client",
                error_description="Unknown client",
                state=state
            )

        # Validate redirect URI against client's allowed URIs
        allowed_uris = client.get("redirect_uris", [])
        if not _validate_redirect_uri(redirect_uri, allowed_uris):
            error = AuthError(
                error="invalid_request",
                error_description="Invalid redirect URI"
            )
            response = cls.format_error(error, status_code=400)
            return response

        # Validate PKCE if required
        if cls.require_pkce and not code_challenge:
            return cls._build_error_redirect(
                redirect_uri=redirect_uri,
                error_code="invalid_request",
                error_description="PKCE code_challenge is required",
                state=state
            )

        # Validate code_challenge_method if code_challenge is provided
        if code_challenge and code_challenge_method:
            if code_challenge_method not in ("S256", "plain"):
                return cls._build_error_redirect(
                    redirect_uri=redirect_uri,
                    error_code="invalid_request",
                    error_description="Unsupported code_challenge_method",
                    state=state
                )

        # Generate authorization code
        code = cls._generate_authorization_code()

        # Store the authorization code
        code_data = {
            "code": code,
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "scope": scope,
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": code_challenge_method,
            "created_at": time.time(),
        }

        if cls.authorization_code_store is not None:
            _run_async(
                cls.authorization_code_store.store_code(
                    code=code,
                    client_id=client_id,
                    redirect_uri=redirect_uri,
                    scope=scope,
                    state=state,
                    code_challenge=code_challenge,
                    code_challenge_method=code_challenge_method
                )
            )
        else:
            cls._memory_code_store[code] = code_data

        # Build redirect response with code and state
        redirect_params = {"code": code}
        if state is not None:
            redirect_params["state"] = state

        redirect_url = _build_redirect_url(redirect_uri, redirect_params)

        response = {
            "status": 302,
            "headers": {"Location": redirect_url},
            "body": {},
            "content_type": "application/json",
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

            :param request: The incoming HTTP request object. The request
                            body must contain a ``grant_type`` field and
                            any additional fields required by the grant type.

            :returns: A response dictionary with ``status``, ``body``, and
                      ``content_type`` keys.
        """
        if not cls.is_endpoint_enabled("token"):
            error = AuthError(
                error="endpoint_disabled",
                error_description="Token endpoint is disabled"
            )
            response = cls.format_error(error, status_code=404)
            return response

        body = request.json()
        grant_type = body.get("grant_type")

        if not grant_type:
            error = AuthError(
                error="invalid_request",
                error_description="grant_type is required"
            )
            response = cls.format_error(error, status_code=400)
            return response

        if grant_type not in cls.supported_grant_types:
            error = AuthError(
                error="unsupported_grant_type",
                error_description="Grant type '{}' is not supported".format(
                    grant_type
                )
            )
            response = cls.format_error(error, status_code=400)
            return response

        if grant_type == "authorization_code":
            response = cls._handle_authorization_code_grant(body)
            return response

        if grant_type == "client_credentials":
            response = cls._handle_client_credentials_grant(body)
            return response

        if grant_type == "refresh_token":
            response = cls._handle_refresh_token_grant(body)
            return response

        error = AuthError(
            error="unsupported_grant_type",
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
                error="endpoint_disabled",
                error_description="Callback endpoint is disabled"
            )
            response = cls.format_error(error, status_code=404)
            return response

        # Check for error response from provider
        error_code = cls._get_query_param(request, "error")
        if error_code is not None:
            error_description = cls._get_query_param(
                request, "error_description"
            )
            state = cls._get_query_param(request, "state")
            error = AuthError(
                error=error_code,
                error_description=error_description
            )
            response = cls.format_error(error, status_code=400)
            if state is not None:
                response["body"]["state"] = state
            return response

        # Extract code and state
        code = cls._get_query_param(request, "code")
        state = cls._get_query_param(request, "state")

        if not code:
            error = AuthError(
                error="invalid_request",
                error_description="Authorization code is required"
            )
            response = cls.format_error(error, status_code=400)
            return response

        # Look up the authorization code to validate state
        code_data = cls._consume_code(code)

        if code_data is None:
            error = AuthError(
                error="invalid_grant",
                error_description="Invalid or expired authorization code"
            )
            response = cls.format_error(error, status_code=400)
            return response

        # Validate state parameter
        stored_state = code_data.get("state")
        if stored_state is not None and stored_state != state:
            error = AuthError(
                error="invalid_request",
                error_description="State parameter mismatch"
            )
            response = cls.format_error(error, status_code=400)
            return response

        # Return success with the code data
        response_body = {
            "code": code,
            "client_id": code_data.get("client_id"),
            "scope": code_data.get("scope"),
        }
        if state is not None:
            response_body["state"] = state

        response = {
            "status": 200,
            "body": response_body,
            "content_type": "application/json",
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

            Accepts a token in the request body and revokes it via the
            configured :attr:`token_store`. If no token store is
            configured, the endpoint acknowledges the request without
            performing any action.

            :param request: The incoming HTTP request object. The request
                            body must contain a ``token`` field.

            :returns: A response dictionary with ``status``, ``body``, and
                      ``content_type`` keys.
        """
        if not cls.is_endpoint_enabled("revoke"):
            error = AuthError(
                error="endpoint_disabled",
                error_description="Revoke endpoint is disabled"
            )
            response = cls.format_error(error, status_code=404)
            return response

        body = request.json()
        token_value = body.get("token")

        if not token_value:
            error = AuthError(
                error="invalid_request",
                error_description="Token is required"
            )
            response = cls.format_error(error, status_code=400)
            return response

        if cls.token_store is not None:
            _run_async(cls.token_store.revoke_token(token_value))
        else:
            cls._memory_token_store.pop(token_value, None)

        response = {
            "status": 200,
            "body": {},
            "content_type": "application/json",
        }
        return response

    # =========================================================================
    # Private Helper Methods
    # =========================================================================

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
            return client

        client = cls._memory_client_store.get(client_id)
        return client

    @classmethod
    def _consume_code(cls, code: str) -> Optional[Dict[str, Any]]:
        """
            Retrieve and consume an authorization code.

            Uses the configured :attr:`authorization_code_store` if
            available, otherwise falls back to the in-memory code store.
            The code is removed from the store after retrieval.

            :param code: The authorization code to consume.

            :returns: A dictionary of code metadata, or None if not found.
        """
        if cls.authorization_code_store is not None:
            code_data = _run_async(
                cls.authorization_code_store.consume_code(code)
            )
            return code_data

        code_data = cls._memory_code_store.pop(code, None)
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

            If a redirect URI is available, returns a 302 redirect with
            error parameters in the query string. Otherwise, returns a
            JSON error response.

            :param redirect_uri: The redirect URI to redirect to.
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
            "error": error_code,
            "error_description": error_description,
        }
        if state is not None:
            params["state"] = state

        redirect_url = _build_redirect_url(redirect_uri, params)

        response = {
            "status": 302,
            "headers": {"Location": redirect_url},
            "body": {},
            "content_type": "application/json",
        }
        return response

    @classmethod
    def _handle_authorization_code_grant(
        cls,
        body: Dict[str, Any]
    ) -> dict:
        """
            Handle the authorization_code grant type.

            Validates the authorization code, client credentials,
            redirect URI, and PKCE code verifier. On success, issues
            a JWT access token and refresh token.

            :param body: The parsed request body dictionary.

            :returns: A response dictionary.
        """
        code = body.get("code")
        redirect_uri = body.get("redirect_uri")
        client_id = body.get("client_id")
        client_secret = body.get("client_secret")
        code_verifier = body.get("code_verifier")

        if not code:
            error = AuthError(
                error="invalid_request",
                error_description="Authorization code is required"
            )
            response = cls.format_error(error, status_code=400)
            return response

        # Consume the authorization code
        code_data = cls._consume_code(code)

        if code_data is None:
            error = AuthError(
                error="invalid_grant",
                error_description="Invalid or expired authorization code"
            )
            response = cls.format_error(error, status_code=400)
            return response

        # Validate client_id matches
        if client_id and code_data.get("client_id") != client_id:
            error = AuthError(
                error="invalid_grant",
                error_description="Client ID mismatch"
            )
            response = cls.format_error(error, status_code=400)
            return response

        # Validate redirect_uri matches
        if redirect_uri and code_data.get("redirect_uri") != redirect_uri:
            error = AuthError(
                error="invalid_grant",
                error_description="Redirect URI mismatch"
            )
            response = cls.format_error(error, status_code=400)
            return response

        # Validate PKCE code verifier if code_challenge was stored
        stored_challenge = code_data.get("code_challenge")
        if stored_challenge is not None:
            if not code_verifier:
                error = AuthError(
                    error="invalid_request",
                    error_description="code_verifier is required"
                )
                response = cls.format_error(error, status_code=400)
                return response

            stored_method = code_data.get("code_challenge_method")
            if not _verify_pkce(code_verifier, stored_challenge, stored_method):
                error = AuthError(
                    error="invalid_grant",
                    error_description="PKCE verification failed"
                )
                response = cls.format_error(error, status_code=400)
                return response
        elif cls.require_pkce:
            error = AuthError(
                error="invalid_request",
                error_description="PKCE is required but no code_challenge was provided"
            )
            response = cls.format_error(error, status_code=400)
            return response

        # Validate client secret if client_store is configured
        if client_secret and cls.client_store is not None:
            is_valid = _run_async(
                cls.client_store.validate_client_secret(
                    client_id or code_data.get("client_id"),
                    client_secret
                )
            )
            if not is_valid:
                error = AuthError(
                    error="invalid_client",
                    error_description="Invalid client credentials"
                )
                response = cls.format_error(error, status_code=401)
                return response

        # Issue tokens
        subject = client_id or code_data.get("client_id")
        scope = code_data.get("scope")
        response = cls._issue_tokens(subject, scope)
        return response

    @classmethod
    def _handle_client_credentials_grant(
        cls,
        body: Dict[str, Any]
    ) -> dict:
        """
            Handle the client_credentials grant type.

            Validates the client_id and client_secret. On success,
            issues a JWT access token. No refresh token is issued
            for client credentials grants.

            :param body: The parsed request body dictionary.

            :returns: A response dictionary.
        """
        client_id = body.get("client_id")
        client_secret = body.get("client_secret")

        if not client_id or not client_secret:
            error = AuthError(
                error="invalid_request",
                error_description="client_id and client_secret are required"
            )
            response = cls.format_error(error, status_code=400)
            return response

        # Validate client credentials
        client = cls._get_client(client_id)
        if client is None:
            error = AuthError(
                error="invalid_client",
                error_description="Unknown client"
            )
            response = cls.format_error(error, status_code=401)
            return response

        # Validate client secret
        if cls.client_store is not None:
            is_valid = _run_async(
                cls.client_store.validate_client_secret(
                    client_id, client_secret
                )
            )
        else:
            stored_secret = client.get("client_secret")
            is_valid = (stored_secret == client_secret)

        if not is_valid:
            error = AuthError(
                error="invalid_client",
                error_description="Invalid client credentials"
            )
            response = cls.format_error(error, status_code=401)
            return response

        # Check that client is allowed to use this grant type
        allowed_grants = client.get("grant_types", [])
        if allowed_grants and "client_credentials" not in allowed_grants:
            error = AuthError(
                error="unauthorized_client",
                error_description="Client not authorized for client_credentials grant"
            )
            response = cls.format_error(error, status_code=400)
            return response

        # Issue access token only (no refresh token for client credentials)
        scope = body.get("scope")
        response = cls._issue_access_token_only(client_id, scope)
        return response

    @classmethod
    def _handle_refresh_token_grant(
        cls,
        body: Dict[str, Any]
    ) -> dict:
        """
            Handle the refresh_token grant type.

            Validates the provided refresh token and issues a new
            access token.

            :param body: The parsed request body dictionary.

            :returns: A response dictionary.
        """
        refresh_token = body.get("refresh_token")

        if not refresh_token:
            error = AuthError(
                error="invalid_request",
                error_description="refresh_token is required"
            )
            response = cls.format_error(error, status_code=400)
            return response

        if cls.jwt_secret is None:
            error = AuthError(
                error="server_error",
                error_description="JWT secret is not configured"
            )
            response = cls.format_error(error, status_code=500)
            return response

        # Validate the refresh token
        if cls.token_store is not None:
            claims = _run_async(
                cls.token_store.validate_token(refresh_token)
            )
            if claims is None:
                error = AuthError(
                    error="invalid_grant",
                    error_description="Invalid or expired refresh token"
                )
                response = cls.format_error(error)
                return response
            subject = claims.get("sub")
        else:
            # Check in-memory store
            token_data = cls._memory_token_store.get(refresh_token)
            if token_data is None:
                error = AuthError(
                    error="invalid_grant",
                    error_description="Invalid or expired refresh token"
                )
                response = cls.format_error(error)
                return response

            # Check expiration
            if token_data.get("exp", 0) < time.time():
                cls._memory_token_store.pop(refresh_token, None)
                error = AuthError(
                    error="invalid_grant",
                    error_description="Refresh token has expired"
                )
                response = cls.format_error(error)
                return response

            subject = token_data.get("sub")

        if not subject:
            error = AuthError(
                error="invalid_grant",
                error_description="Refresh token missing subject"
            )
            response = cls.format_error(error)
            return response

        # Issue a new access token
        scope = body.get("scope")
        now = time.time()
        access_payload = {
            "sub": subject,
            "iat": int(now),
            "exp": int(now) + cls.access_token_expires,
            "token_type": "access",
        }
        if scope:
            access_payload["scope"] = scope

        access_token = encode_jwt(
            access_payload,
            cls.jwt_secret,
            algorithm=cls.jwt_algorithm
        )

        auth_response = AuthResponse(
            access_token=access_token,
            token_type="Bearer",
            expires_in=cls.access_token_expires,
            scope=scope
        )
        response = cls.format_success(auth_response)
        return response

    @classmethod
    def _issue_tokens(
        cls,
        subject: str,
        scope: Optional[str] = None
    ) -> dict:
        """
            Issue an access token and refresh token for the given subject.

            :param subject: The subject identifier for the token claims.
            :param scope: Optional scope string.

            :returns: A response dictionary.
        """
        if cls.jwt_secret is None:
            error = AuthError(
                error="server_error",
                error_description="JWT secret is not configured"
            )
            response = cls.format_error(error, status_code=500)
            return response

        now = time.time()

        # Build access token
        access_payload = {
            "sub": subject,
            "iat": int(now),
            "exp": int(now) + cls.access_token_expires,
            "token_type": "access",
        }
        if scope:
            access_payload["scope"] = scope

        access_token = encode_jwt(
            access_payload,
            cls.jwt_secret,
            algorithm=cls.jwt_algorithm
        )

        # Build refresh token
        refresh_payload = {
            "sub": subject,
            "iat": int(now),
            "exp": int(now) + cls.refresh_token_expires,
            "token_type": "refresh",
        }
        if scope:
            refresh_payload["scope"] = scope

        refresh_token = encode_jwt(
            refresh_payload,
            cls.jwt_secret,
            algorithm=cls.jwt_algorithm
        )

        # Store the refresh token
        if cls.token_store is not None:
            _run_async(
                cls.token_store.store_token(
                    refresh_token,
                    refresh_payload,
                    cls.refresh_token_expires
                )
            )
        else:
            cls._memory_token_store[refresh_token] = refresh_payload

        auth_response = AuthResponse(
            access_token=access_token,
            token_type="Bearer",
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
        scope: Optional[str] = None
    ) -> dict:
        """
            Issue an access token without a refresh token.

            Used for client credentials grants where refresh tokens
            are not appropriate.

            :param subject: The subject identifier for the token claims.
            :param scope: Optional scope string.

            :returns: A response dictionary.
        """
        if cls.jwt_secret is None:
            error = AuthError(
                error="server_error",
                error_description="JWT secret is not configured"
            )
            response = cls.format_error(error, status_code=500)
            return response

        now = time.time()

        access_payload = {
            "sub": subject,
            "iat": int(now),
            "exp": int(now) + cls.access_token_expires,
            "token_type": "access",
        }
        if scope:
            access_payload["scope"] = scope

        access_token = encode_jwt(
            access_payload,
            cls.jwt_secret,
            algorithm=cls.jwt_algorithm
        )

        auth_response = AuthResponse(
            access_token=access_token,
            token_type="Bearer",
            expires_in=cls.access_token_expires,
            scope=scope
        )
        response = cls.format_success(auth_response)
        return response
