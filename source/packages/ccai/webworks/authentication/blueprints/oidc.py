"""
.. module:: oidc
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: OpenID Connect blueprint providing OIDC provider endpoints.

.. moduleauthor:: Code Craft AI LLC

This module provides the :class:`OIDCBlueprint` class which extends
:class:`OAuth2Blueprint` to offer pre-built endpoints for OpenID Connect
authentication flows. The blueprint adds OIDC-specific endpoints for
discovery, UserInfo, and JWKS on top of the standard OAuth 2.0 endpoints.

Endpoints (in addition to OAuth2):
    - ``GET /.well-known/openid-configuration`` — OIDC discovery document.
    - ``GET <base_path>/userinfo`` — UserInfo endpoint for authenticated users.
    - ``GET /.well-known/jwks.json`` — JSON Web Key Set for token verification.
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


import time

from dataclasses import asdict
from typing import Any, Callable, Dict, List, Optional

from ccai.webworks.authentication.bearer import encode_jwt
from ccai.webworks.authentication.blueprints.oauth2 import OAuth2Blueprint
from ccai.webworks.authentication.blueprints.responses import (
    AuthError,
    AuthResponse
)
from ccai.webworks.authentication.blueprints.schemas import (
    OIDCDiscovery,
    UserInfo
)
from ccai.webworks.authentication.blueprints.security import (
    SecurityBlueprint
)
from ccai.webworks.endpoints.doc import Doc


class OIDCBlueprint(OAuth2Blueprint):
    """
        Blueprint for OpenID Connect provider endpoints.

        Extends :class:`OAuth2Blueprint` with OIDC-specific functionality
        including a discovery endpoint, UserInfo endpoint, and JWKS
        endpoint. Token responses include an ``id_token`` with standard
        OIDC claims (iss, sub, aud, exp, iat).

        Default Endpoints (in addition to OAuth2):
            - ``GET /.well-known/openid-configuration`` — Discovery document.
            - ``GET <base_path>/userinfo`` — UserInfo endpoint.
            - ``GET /.well-known/jwks.json`` — JSON Web Key Set.

        Class Attributes:
            base_path: Base URL path for all endpoints. Defaults to
                       ``"/oidc"``.
            tags: Documentation tags applied to all endpoints.
            issuer: The issuer identifier for the OIDC provider. When
                    None, the base URL from the request is used.
            jwks: Optional dictionary containing the JSON Web Key Set.
                  Defaults to None which returns an empty keys array.
            supported_scopes: List of supported OAuth 2.0 scopes.
                              Defaults to ``["openid", "profile", "email"]``.
            supported_claims: List of supported claims returned by the
                              UserInfo endpoint and included in ID tokens.
            id_token_lifetime: Lifetime of ID tokens in seconds. Defaults
                               to 3600 (1 hour).
            claim_mappings: Optional dictionary mapping standard claim
                            names to callables that extract claim values
                            from user data. Each callable receives the
                            user data dictionary and returns the claim value.
    """

    base_path: str = "/oidc"
    tags: List[str] = ["Authentication", "OIDC", "OAuth2"]

    # OIDC Configuration
    issuer: Optional[str] = None
    jwks: Optional[dict] = None
    supported_scopes: List[str] = ["openid", "profile", "email"]
    supported_claims: List[str] = [
        "sub", "name", "email", "email_verified"
    ]
    id_token_lifetime: int = 3600
    claim_mappings: Optional[Dict[str, Callable]] = None

    # --- Class constants ---
    # Override these on a subclass to rebrand wire-format strings without
    # rewriting handler bodies.

    # Default scheme / host fallbacks for base-URL resolution
    DEFAULT_HOST: str = "localhost"
    DEFAULT_SCHEME: str = "https"
    HOST_HEADER_NAME: str = "Host"

    # Well-known / endpoint paths
    DISCOVERY_PATH: str = "/.well-known/openid-configuration"
    JWKS_PATH: str = "/.well-known/jwks.json"
    AUTHORIZE_LEAF: str = "/authorize"
    TOKEN_LEAF: str = "/token"
    USERINFO_LEAF: str = "/userinfo"

    # Subject types reported in the discovery document
    SUBJECT_TYPES_SUPPORTED: List[str] = ["public"]

    # ID-token claim keys
    ID_TOKEN_CLAIM_SUB: str = "sub"
    ID_TOKEN_CLAIM_ISS: str = "iss"
    ID_TOKEN_CLAIM_AUD: str = "aud"
    ID_TOKEN_CLAIM_EXP: str = "exp"
    ID_TOKEN_CLAIM_IAT: str = "iat"

    # Default issuer fallback when neither cls.issuer nor request can
    # provide one (only reached in unit-test paths in practice).
    DEFAULT_ISSUER_FALLBACK: str = "https://localhost"

    # Token-response key used to attach the id_token onto the parent
    # token response body.
    ID_TOKEN_RESPONSE_KEY: str = "id_token"

    # Error codes
    ENDPOINT_DISABLED_ERROR_CODE: str = "endpoint_disabled"
    INVALID_TOKEN_ERROR_CODE: str = "invalid_token"

    # Empty JWKS sentinel returned when no keys are configured.
    EMPTY_JWKS_KEY: str = "keys"

    # In-memory user info store for testing
    _memory_user_store: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def _get_base_url(cls, request: Any) -> str:
        """
            Determine the base URL from the incoming request.

            Inspects the request object for common attributes that
            indicate the scheme and host. Falls back to
            ``"https://localhost"`` when the request does not provide
            sufficient information.

            :param request: The incoming HTTP request object.

            :returns: The base URL string without a trailing slash.
        """
        if hasattr(request, "base_url"):
            base_url = str(request.base_url).rstrip("/")
            return base_url

        scheme = cls.DEFAULT_SCHEME
        host = cls.DEFAULT_HOST

        if hasattr(request, "scheme"):
            scheme = request.scheme

        if hasattr(request, "host"):
            host = request.host
        elif hasattr(request, "headers"):
            headers = request.headers
            if isinstance(headers, dict):
                host = headers.get(cls.HOST_HEADER_NAME, headers.get(cls.HOST_HEADER_NAME.lower(), cls.DEFAULT_HOST))

        base_url = "{}://{}".format(scheme, host)
        return base_url

    @classmethod
    @SecurityBlueprint.read(
        path="/.well-known/openid-configuration",
        absolute=True,
        response_schema=OIDCDiscovery,
        doc=Doc(
            summary="OpenID Connect Discovery",
            description="Returns the OpenID Connect discovery document "
                        "containing provider metadata."
        )
    )
    def discovery(cls, request: Any) -> dict:
        """
            Return the OIDC discovery document.

            Builds and returns the OpenID Connect discovery document
            containing the issuer identifier, endpoint URLs, supported
            response types, signing algorithms, scopes, and claims.

            :param request: The incoming HTTP request object.

            :returns: A response dictionary with ``status``, ``body``,
                      and ``content_type`` keys.
        """
        if not cls.is_endpoint_enabled("discovery"):
            error = AuthError(
                error=cls.ENDPOINT_DISABLED_ERROR_CODE,
                error_description="Discovery endpoint is disabled"
            )
            response = cls.format_error(error, status_code=404)
            return response

        base_url = cls._get_base_url(request)

        discovery_doc = OIDCDiscovery(
            issuer=cls.issuer or base_url,
            authorization_endpoint="{}{}{}".format(
                base_url, cls.base_path, cls.AUTHORIZE_LEAF
            ),
            token_endpoint="{}{}{}".format(
                base_url, cls.base_path, cls.TOKEN_LEAF
            ),
            userinfo_endpoint="{}{}{}".format(
                base_url, cls.base_path, cls.USERINFO_LEAF
            ),
            jwks_uri="{}{}".format(base_url, cls.JWKS_PATH),
            response_types_supported=list(cls.supported_response_types),
            subject_types_supported=list(cls.SUBJECT_TYPES_SUPPORTED),
            id_token_signing_alg_values_supported=[cls.jwt_algorithm],
            scopes_supported=list(cls.supported_scopes),
            claims_supported=list(cls.supported_claims)
        )

        response = {
            "status": 200,
            "body": asdict(discovery_doc),
            "content_type": cls.JSON_CONTENT_TYPE
        }
        return response

    @classmethod
    @SecurityBlueprint.read(
        leaf="userinfo",
        response_schema=UserInfo,
        doc=Doc(
            summary="UserInfo endpoint",
            description="Returns claims about the authenticated user."
        )
    )
    def userinfo(cls, request: Any) -> dict:
        """
            Return user information for the authenticated user.

            Extracts the authenticated user's subject identifier from
            the request context and returns the corresponding claims.
            The claims returned are filtered to only include those
            listed in :attr:`supported_claims`.

            :param request: The incoming HTTP request object. Must
                            carry authentication context with a subject
                            identifier.

            :returns: A response dictionary with ``status``, ``body``,
                      and ``content_type`` keys.
        """
        if not cls.is_endpoint_enabled("userinfo"):
            error = AuthError(
                error=cls.ENDPOINT_DISABLED_ERROR_CODE,
                error_description="UserInfo endpoint is disabled"
            )
            response = cls.format_error(error, status_code=404)
            return response

        # Extract the authenticated user subject from the request
        subject = cls._get_authenticated_subject(request)

        if subject is None:
            error = AuthError(
                error=cls.INVALID_TOKEN_ERROR_CODE,
                error_description="Authentication required"
            )
            response = cls.format_error(error, status_code=401)
            return response

        # Look up user claims
        user_data = cls._get_user_claims(subject)

        if user_data is None:
            error = AuthError(
                error=cls.INVALID_TOKEN_ERROR_CODE,
                error_description="User not found"
            )
            response = cls.format_error(error, status_code=401)
            return response

        # Build UserInfo response with supported claims
        user_info_data = {cls.ID_TOKEN_CLAIM_SUB: subject}
        for claim in cls.supported_claims:
            if claim == cls.ID_TOKEN_CLAIM_SUB:
                continue
            if claim in user_data:
                user_info_data[claim] = user_data[claim]

        response = {
            "status": 200,
            "body": user_info_data,
            "content_type": cls.JSON_CONTENT_TYPE
        }
        return response

    @classmethod
    @SecurityBlueprint.read(
        path="/.well-known/jwks.json",
        absolute=True,
        doc=Doc(
            summary="JSON Web Key Set",
            description="Returns the public keys for verifying ID tokens."
        )
    )
    def jwks_endpoint(cls, request: Any) -> dict:
        """
            Return the JSON Web Key Set for token verification.

            Returns the configured JWKS or an empty keys array when
            no JWKS has been configured.

            :param request: The incoming HTTP request object.

            :returns: A response dictionary with ``status``, ``body``,
                      and ``content_type`` keys.
        """
        if not cls.is_endpoint_enabled("jwks"):
            error = AuthError(
                error=cls.ENDPOINT_DISABLED_ERROR_CODE,
                error_description="JWKS endpoint is disabled"
            )
            response = cls.format_error(error, status_code=404)
            return response

        jwks_data = cls.jwks or {cls.EMPTY_JWKS_KEY: []}

        response = {
            "status": 200,
            "body": jwks_data,
            "content_type": cls.JSON_CONTENT_TYPE
        }
        return response


    # =========================================================================
    # Token Issuance Override
    # =========================================================================

    @classmethod
    def _issue_tokens(
        cls,
        subject: str,
        scope: Optional[str] = None
    ) -> dict:
        """
            Issue tokens including an OIDC id_token.

            Overrides the parent :meth:`OAuth2Blueprint._issue_tokens`
            to include an ``id_token`` in the response body. The
            id_token contains the standard OIDC claims: ``iss``,
            ``sub``, ``aud``, ``exp``, and ``iat``.

            :param subject: The subject identifier for the token claims.
            :param scope: Optional scope string.

            :returns: A response dictionary.
        """
        # Call the parent to issue access and refresh tokens
        response = super()._issue_tokens(subject, scope)

        # If the parent returned an error, pass it through
        if response.get("status", 200) != 200:
            return response

        # Build and attach the id_token
        id_token = cls._build_id_token(subject, scope)
        if id_token is not None:
            response["body"][cls.ID_TOKEN_RESPONSE_KEY] = id_token

        return response

    @classmethod
    def _build_id_token(
        cls,
        subject: str,
        scope: Optional[str] = None
    ) -> Optional[str]:
        """
            Build a signed OIDC ID token JWT.

            The ID token contains the standard claims: ``iss`` (issuer),
            ``sub`` (subject), ``aud`` (audience, set to the subject),
            ``exp`` (expiration), and ``iat`` (issued at). Additional
            claims from the user data are included when claim mappings
            are configured.

            :param subject: The subject identifier.
            :param scope: Optional scope string.

            :returns: The encoded ID token JWT string, or None if the
                      JWT secret is not configured.
        """
        if cls.jwt_secret is None:
            return None

        now = time.time()

        id_token_payload = {
            cls.ID_TOKEN_CLAIM_ISS: cls.issuer or cls.DEFAULT_ISSUER_FALLBACK,
            cls.ID_TOKEN_CLAIM_SUB: subject,
            cls.ID_TOKEN_CLAIM_AUD: subject,
            cls.ID_TOKEN_CLAIM_EXP: int(now) + cls.id_token_lifetime,
            cls.ID_TOKEN_CLAIM_IAT: int(now),
        }

        # Add additional claims from user data if available
        user_data = cls._get_user_claims(subject)
        if user_data is not None:
            if cls.claim_mappings is not None:
                for claim_name, mapper in cls.claim_mappings.items():
                    claim_value = mapper(user_data)
                    if claim_value is not None:
                        id_token_payload[claim_name] = claim_value
            else:
                # Include supported claims from user data
                for claim in cls.supported_claims:
                    if claim == cls.ID_TOKEN_CLAIM_SUB:
                        continue
                    if claim in user_data:
                        id_token_payload[claim] = user_data[claim]

        id_token = encode_jwt(
            id_token_payload,
            cls.jwt_secret,
            algorithm=cls.jwt_algorithm
        )
        return id_token

    # =========================================================================
    # Private Helper Methods
    # =========================================================================

    @classmethod
    def _get_authenticated_subject(cls, request: Any) -> Optional[str]:
        """
            Extract the authenticated subject from the request.

            Inspects the request for authentication context attributes
            commonly set by authentication middleware. Checks for
            ``auth_context``, ``user``, and ``subject`` attributes.

            :param request: The incoming HTTP request object.

            :returns: The subject identifier string, or None if no
                      authenticated user is found.
        """
        # Check for auth attribute (Request.auth — the canonical
        # location for the AuthenticationContext on a webworks
        # Request); fall back to the historical ``auth_context``
        # attribute name for any consumer that pre-dates
        # Request.auth.
        for attr_name in ("auth", "auth_context"):
            if hasattr(request, attr_name):
                context = getattr(request, attr_name)
                if context is not None:
                    if hasattr(context, "principal"):
                        principal = context.principal
                        if hasattr(principal, "identifier"):
                            return principal.identifier
                    if hasattr(context, "subject"):
                        return context.subject
                    break

        # Check for user attribute
        if hasattr(request, "user"):
            user = request.user
            if isinstance(user, dict):
                return user.get("sub", user.get("id"))
            if hasattr(user, "sub"):
                return user.sub
            if hasattr(user, "identifier"):
                return user.identifier

        # Check for subject attribute
        if hasattr(request, "subject"):
            return request.subject

        return None

    @classmethod
    def _get_user_claims(cls, subject: str) -> Optional[Dict[str, Any]]:
        """
            Retrieve user claims for the given subject.

            Looks up user data in the in-memory user store. Subclasses
            may override this method to retrieve claims from an external
            identity provider or database.

            :param subject: The subject identifier.

            :returns: A dictionary of user claims, or None if the user
                      is not found.
        """
        user_data = cls._memory_user_store.get(subject)
        return user_data
