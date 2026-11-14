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


import base64
import hashlib
import json
import logging
import threading
import time

from dataclasses import asdict
from typing import Any, Callable, Dict, List, Optional, Tuple

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

from ccai.webworks.authentication.blueprints.oauth2 import OAuth2Blueprint
from ccai.webworks.authentication.blueprints.responses import AuthError
from ccai.webworks.authentication.blueprints.schemas import (
    OIDCDiscovery,
    UserInfo
)
from ccai.webworks.authentication.blueprints.security import (
    SecurityBlueprint
)
from ccai.webworks.endpoints.doc import Doc


# Module-level logger for the OIDC blueprint handlers.
logger = logging.getLogger(__name__)

# Hash used by each supported RSASSA-PKCS1-v1_5 signing algorithm.
_RSA_SIGNING_HASHES = {
    "RS256": hashes.SHA256,
    "RS384": hashes.SHA384,
    "RS512": hashes.SHA512,
}

# Serialises the lazy creation of signing keys across handler threads.
_signing_key_lock = threading.Lock()


def _base64url(data: bytes) -> str:
    """
        Encode bytes as unpadded base64url, as JOSE requires.

        :param data: The bytes to encode.

        :returns: The base64url text without padding.
    """
    rtnval = base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")
    return rtnval


def _base64url_uint(value: int) -> str:
    """
        Encode a non-negative integer as a JWK ``Base64urlUInt``.

        :param value: The integer (an RSA modulus or exponent).

        :returns: The big-endian base64url encoding.
    """
    length = max(1, (value.bit_length() + 7) // 8)
    rtnval = _base64url(value.to_bytes(length, "big"))
    return rtnval


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
                    None, the public base URL of the request is used
                    (see :meth:`resolve_public_base_url`). The same
                    value is advertised by discovery and written into
                    the ``iss`` claim of every ID token.
            id_token_signing_key: The RSA private key ID tokens are
                                  signed with: a PEM string or bytes, or
                                  a ``cryptography`` RSA private key.
                                  Its public half is published at the
                                  JWKS endpoint. When None, a key is
                                  generated for the life of the process,
                                  which only suits a single worker.
            id_token_signing_alg: The signing algorithm: ``"RS256"``
                                  (default), ``"RS384"`` or ``"RS512"``.
            id_token_key_id: The ``kid`` of the signing key. Defaults to
                             a digest of the public key.
            jwks: Optional dictionary with additional JSON Web Keys to
                  publish next to the signing key (for key rotation).
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
    id_token_signing_key: Optional[Any] = None
    id_token_signing_alg: str = "RS256"
    id_token_key_id: Optional[str] = None
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
    ID_TOKEN_CLAIM_NONCE: str = "nonce"

    # Size of the signing key generated when none is configured
    GENERATED_SIGNING_KEY_BITS: int = 2048

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

    # In-memory user info store for testing. Like the client registry,
    # a subclass starts with a copy of its parent's entries.
    REGISTRY_MEMORY_STORES: Tuple[str, ...] = (
        "_memory_client_store",
        "_memory_user_store",
    )

    _memory_user_store: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def _get_base_url(cls, request: Any) -> str:
        """
            Determine the public base URL for the incoming request.

            A request object that offers ``base_url`` is taken at its
            word; otherwise the origin is resolved by
            :meth:`resolve_public_base_url` (configured public base URL,
            then the ``Host`` header including its port).

            :param request: The incoming HTTP request object.

            :returns: The base URL string without a trailing slash.
        """
        base_url = getattr(request, "base_url", None)
        if isinstance(base_url, str) and len(base_url) > 0:
            rtnval = base_url.rstrip("/")
            return rtnval

        rtnval = cls.resolve_public_base_url(request)
        return rtnval

    @classmethod
    def _get_issuer(cls, request: Any) -> str:
        """
            Determine the issuer identifier.

            Discovery and ID tokens both use this value, so a relying
            party that reads the discovery document accepts the ``iss``
            claim of the tokens.

            :param request: The incoming HTTP request object.

            :returns: The configured :attr:`issuer`, or the public base
                      URL of the request.
        """
        if cls.issuer:
            return cls.issuer

        rtnval = cls._get_base_url(request)
        return rtnval

    @classmethod
    def _get_signing_key(cls) -> Tuple[rsa.RSAPrivateKey, str]:
        """
            Get the RSA key ID tokens are signed with, and its key id.

            Loads :attr:`id_token_signing_key`. When none is configured
            a key is generated once per blueprint class and kept for the
            life of the process.

            :returns: A tuple of (private key, key id).

            :raises ValueError: If the configured key is not an RSA
                                private key.
        """
        source = cls.id_token_signing_key

        with _signing_key_lock:
            cached = cls.__dict__.get("_signing_key_state")
            if cached is not None and cached[0] is source:
                return (cached[1], cached[2])

            if source is None:
                logger.warning(
                    "%s: no id_token_signing_key is configured; generating "
                    "a signing key that lives only in this process. ID "
                    "tokens cannot be verified after a restart or by "
                    "another worker. Configure a persistent RSA key.",
                    cls.__name__,
                )
                private_key = rsa.generate_private_key(
                    public_exponent=65537,
                    key_size=cls.GENERATED_SIGNING_KEY_BITS
                )
            elif isinstance(source, (str, bytes)):
                pem = source.encode("utf-8") if isinstance(source, str) else source
                private_key = serialization.load_pem_private_key(pem, password=None)
            else:
                private_key = source

            if not isinstance(private_key, rsa.RSAPrivateKey):
                errmsg = "id_token_signing_key must be an RSA private key"
                raise ValueError(errmsg)

            key_id = cls.id_token_key_id
            if not key_id:
                public_der = private_key.public_key().public_bytes(
                    encoding=serialization.Encoding.DER,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo
                )
                key_id = _base64url(hashlib.sha256(public_der).digest())[:16]

            cls._signing_key_state = (source, private_key, key_id)

        return (private_key, key_id)

    @classmethod
    def _get_signing_jwk(cls) -> Dict[str, Any]:
        """
            Build the public JSON Web Key of the ID token signing key.

            :returns: The JWK dictionary published at the JWKS endpoint.
        """
        private_key, key_id = cls._get_signing_key()
        public_numbers = private_key.public_key().public_numbers()

        jwk = {
            "kty": "RSA",
            "use": "sig",
            "alg": cls.id_token_signing_alg,
            "kid": key_id,
            "n": _base64url_uint(public_numbers.n),
            "e": _base64url_uint(public_numbers.e),
        }
        return jwk

    @classmethod
    def _sign_id_token(cls, payload: Dict[str, Any]) -> str:
        """
            Sign an ID token payload as a compact JWS.

            :param payload: The ID token claims.

            :returns: The encoded ID token.

            :raises ValueError: If :attr:`id_token_signing_alg` is not a
                                supported RSA algorithm.
        """
        hash_class = _RSA_SIGNING_HASHES.get(cls.id_token_signing_alg)
        if hash_class is None:
            errmsg = "Unsupported id_token_signing_alg: {}".format(
                cls.id_token_signing_alg
            )
            raise ValueError(errmsg)

        private_key, key_id = cls._get_signing_key()

        header = {
            "alg": cls.id_token_signing_alg,
            "typ": "JWT",
            "kid": key_id,
        }

        header_segment = _base64url(json.dumps(header).encode("utf-8"))
        payload_segment = _base64url(json.dumps(payload).encode("utf-8"))
        signing_input = "{}.{}".format(header_segment, payload_segment)

        signature = private_key.sign(
            signing_input.encode("ascii"),
            padding.PKCS1v15(),
            hash_class()
        )

        id_token = "{}.{}".format(signing_input, _base64url(signature))
        return id_token

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
            issuer=cls._get_issuer(request),
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
            id_token_signing_alg_values_supported=[cls.id_token_signing_alg],
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

            Returns the public key of the ID token signing key,
            followed by any additional keys configured in :attr:`jwks`.

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

        keys = [cls._get_signing_jwk()]

        if isinstance(cls.jwks, dict):
            for extra_key in cls.jwks.get(cls.EMPTY_JWKS_KEY, []):
                if extra_key.get("kid") != keys[0]["kid"]:
                    keys.append(extra_key)

        jwks_data = {cls.EMPTY_JWKS_KEY: keys}

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
        scope: Optional[str] = None,
        client_id: Optional[str] = None,
        nonce: Optional[str] = None,
        request: Optional[Any] = None
    ) -> dict:
        """
            Issue tokens including an OIDC id_token.

            Overrides the parent :meth:`OAuth2Blueprint._issue_tokens`
            to include an ``id_token`` in the response body. The
            id_token identifies the authenticated user (``sub``) to the
            client (``aud``) and echoes the ``nonce`` of the
            authorization request.

            :param subject: The identifier of the authenticated user.
            :param scope: Optional scope string.
            :param client_id: The client the tokens are issued to.
            :param nonce: The nonce of the authorization request.
            :param request: The token request, used to derive the issuer.

            :returns: A response dictionary.
        """
        response = super()._issue_tokens(
            subject, scope, client_id=client_id, nonce=nonce, request=request
        )

        # Only add id_token on success
        if response.get("status", 200) != 200:
            return response

        id_token = cls._build_id_token(
            subject, scope, client_id=client_id, nonce=nonce, request=request
        )
        if id_token is not None:
            response["body"][cls.ID_TOKEN_RESPONSE_KEY] = id_token

        return response

    @classmethod
    def _build_id_token(
        cls,
        subject: str,
        scope: Optional[str] = None,
        client_id: Optional[str] = None,
        nonce: Optional[str] = None,
        request: Optional[Any] = None
    ) -> Optional[str]:
        """
            Build a signed OIDC ID token JWT.

            The ID token contains the standard claims: ``iss`` (the same
            issuer discovery advertises), ``sub`` (the authenticated
            user), ``aud`` (the client the token is for), ``exp``,
            ``iat`` and, when the authorization request carried one,
            ``nonce``. It is signed with the asymmetric key published at
            the JWKS endpoint, so any relying party can verify it.
            Additional claims from the user data are included when claim
            mappings are configured.

            :param subject: The identifier of the authenticated user.
            :param scope: Optional scope string.
            :param client_id: The client the token is issued to.
            :param nonce: The nonce of the authorization request.
            :param request: The token request, used to derive the issuer.

            :returns: The encoded ID token JWT string, or None when
                      there is no client to address the token to.
        """
        if not client_id:
            # An ID token without an audience is of no use to anyone
            return None

        now = time.time()

        id_token_payload = {
            cls.ID_TOKEN_CLAIM_ISS: cls._get_issuer(request),
            cls.ID_TOKEN_CLAIM_SUB: subject,
            cls.ID_TOKEN_CLAIM_AUD: client_id,
            cls.ID_TOKEN_CLAIM_EXP: int(now) + cls.id_token_lifetime,
            cls.ID_TOKEN_CLAIM_IAT: int(now),
        }

        if nonce:
            id_token_payload[cls.ID_TOKEN_CLAIM_NONCE] = nonce

        # Add user claims if available
        user_data = cls._get_user_claims(subject)
        if user_data is not None:
            if cls.claim_mappings is not None:
                for claim_name, mapper in cls.claim_mappings.items():
                    claim_value = mapper(user_data)
                    if claim_value is not None:
                        id_token_payload[claim_name] = claim_value
            else:
                for claim in cls.supported_claims:
                    if claim == cls.ID_TOKEN_CLAIM_SUB:
                        continue
                    if claim in user_data:
                        id_token_payload[claim] = user_data[claim]

        id_token = cls._sign_id_token(id_token_payload)
        return id_token

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
