"""
.. module:: oauth
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Synchronous OAuth 2.0 client wrapper used by
        :class:`automojo.webworks.authentication.blueprints.oauthclient.OAuthClientBlueprint`
        and by application code that needs to perform out-of-band
        OAuth operations (token refresh, etc.).

.. moduleauthor:: Automation Mojo LLC

This module exposes a small, framework-independent
:class:`OAuthClient` that drives the three operations every OAuth
relying-party flow needs:

    1. Build an authorization URL (kickoff).
    2. Exchange an authorization code for a token (callback).
    3. Parse the OIDC ``id_token`` JWT, or fetch the userinfo
       endpoint, to recover the user's claims.

The wrapper deliberately avoids the framework adapters
(``flask_client``, ``starlette_client``) so it composes cleanly with
the webworks ASGI stack: provider config is supplied by the caller
as a plain dict, and the wrapper performs each network round trip
synchronously via ``authlib.integrations.requests_client``. The
synchronous shape matches the surrounding handler pattern; webworks
runs sync handlers on the default executor, so blocking on the
provider's authorization / token / JWKS / userinfo endpoints does
not stall the event loop.

The class carries no per-request state: handler code constructs a
fresh instance for the duration of one kickoff or callback request,
runs one of the flow methods, and discards it. Anything that has to
survive across requests (state value, nonce, register-flag, the
eventual user id, the issued token payload) is the caller's
responsibility — the blueprint stores those on a signed cookie and
the database.
"""

__author__ = "Automation Mojo LLC"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


import logging
import secrets

from typing import Any, Dict, Optional

import requests as http_requests


logger = logging.getLogger(__name__)


# Algorithms the OIDC id_token decoder will accept. Restricting the
# set up front (rather than letting the JWT library negotiate any
# algorithm the JWKS advertises) protects against algorithm-confusion
# attacks.
_ACCEPTED_ID_TOKEN_ALGORITHMS = ["RS256", "ES256", "ES384", "ES512"]


# Default network timeout (seconds) for the discovery / JWKS /
# userinfo HTTP calls. The wrapper is synchronous, so a hung request
# would tie up the calling worker; cap it tight enough that a stuck
# provider trips the surrounding error path quickly.
_HTTP_TIMEOUT_SECONDS = 10


class OAuthClient:
    """
        Synchronous OAuth 2.0 client for a single configured provider.

        Construct one per request; do not cache instances across
        requests. Each method performs at most one network round
        trip and returns the parsed payload as a plain dict so
        handlers can branch on the result without learning the authlib
        type hierarchy.

        :param provider_name: Provider identifier (e.g. ``"google"``,
                              ``"github"``). Used only in error
                              messages and log lines.
        :param provider_config: Authlib-style kwargs dict — the same
                                shape that
                                ``OAuth.register(name, **config)``
                                consumes. Recognised keys:
                                ``client_id``, ``client_secret``,
                                ``server_metadata_url``,
                                ``authorize_url``,
                                ``access_token_url``,
                                ``api_base_url``,
                                ``userinfo_endpoint``,
                                ``client_kwargs``.

        :raises ValueError: When ``provider_name`` is empty or the
                            config is missing
                            ``client_id`` / ``client_secret``.
    """

    def __init__(
        self,
        provider_name: str,
        provider_config: Dict[str, Any],
    ) -> None:
        self._provider_name = str(provider_name or "").strip()

        if self._provider_name == "":
            raise ValueError("OAuth provider name is required.")

        self._provider_config = dict(provider_config or {})

        client_id_value = str(
            self._provider_config.get("client_id") or "",
        ).strip()
        client_secret_value = str(
            self._provider_config.get("client_secret") or "",
        ).strip()

        if client_id_value == "" or client_secret_value == "":
            errmsg = (
                "OAuth provider {!r} is missing client_id / "
                "client_secret.".format(self._provider_name)
            )
            raise ValueError(errmsg)

        self._client_id = client_id_value
        self._client_secret = client_secret_value
        self._client_kwargs = dict(
            self._provider_config.get("client_kwargs") or {},
        )
        self._server_metadata: Optional[Dict[str, Any]] = None

        return

    @property
    def provider_name(self) -> str:
        """
            :returns: The provider name supplied at construction.
        """
        return self._provider_name

    @property
    def client_id(self) -> str:
        """
            :returns: The OAuth ``client_id`` for this provider. Used
                      by the blueprint's id_token validator.
        """
        return self._client_id

    def _resolve_server_metadata(self) -> Dict[str, Any]:
        """
            Fetch and cache the provider's OIDC discovery document.

            Returns an empty dict for providers that don't advertise
            a discovery URL — the URL resolvers below fall back to
            explicit ``authorize_url`` / ``access_token_url`` /
            ``userinfo_endpoint`` config values.

            :returns: Parsed discovery document, or ``{}`` when the
                      provider has no ``server_metadata_url``.
        """
        if self._server_metadata is not None:
            return self._server_metadata

        metadata_url = str(
            self._provider_config.get("server_metadata_url") or "",
        ).strip()
        if metadata_url == "":
            self._server_metadata = {}
            return self._server_metadata

        response = http_requests.get(
            metadata_url,
            timeout=_HTTP_TIMEOUT_SECONDS,
        )
        response.raise_for_status()

        loaded = response.json()
        if not isinstance(loaded, dict):
            self._server_metadata = {}
            return self._server_metadata

        self._server_metadata = loaded
        return self._server_metadata

    def _resolve_authorize_url(self) -> str:
        """
            Resolve the provider's authorization endpoint URL.

            Falls back through:

              1. ``provider_config["authorize_url"]``.
              2. ``server_metadata["authorization_endpoint"]``.

            :returns: Absolute authorization URL.
            :raises ValueError: When neither source supplies a URL.
        """
        url = str(
            self._provider_config.get("authorize_url") or "",
        ).strip()
        if url != "":
            return url

        metadata = self._resolve_server_metadata()
        url = str(metadata.get("authorization_endpoint") or "").strip()
        if url != "":
            return url

        errmsg = (
            "OAuth provider {!r} does not advertise an authorization "
            "endpoint (no authorize_url and no "
            "server_metadata_url).".format(self._provider_name)
        )
        raise ValueError(errmsg)

    def _resolve_token_url(self) -> str:
        """
            Resolve the provider's token endpoint URL.

            Falls back through:

              1. ``provider_config["access_token_url"]``.
              2. ``server_metadata["token_endpoint"]``.

            :returns: Absolute token URL.
            :raises ValueError: When neither source supplies a URL.
        """
        url = str(
            self._provider_config.get("access_token_url") or "",
        ).strip()
        if url != "":
            return url

        metadata = self._resolve_server_metadata()
        url = str(metadata.get("token_endpoint") or "").strip()
        if url != "":
            return url

        errmsg = (
            "OAuth provider {!r} does not advertise a token endpoint "
            "(no access_token_url and no "
            "server_metadata_url).".format(self._provider_name)
        )
        raise ValueError(errmsg)

    def _resolve_userinfo_url(self) -> str:
        """
            Resolve the provider's userinfo endpoint URL.

            Falls back through:

              1. ``provider_config["userinfo_endpoint"]``.
              2. ``server_metadata["userinfo_endpoint"]``.
              3. ``provider_config["api_base_url"] + "user"`` (the
                 GitHub convention — its REST API doesn't ship a
                 dedicated ``/userinfo`` and the canonical profile
                 endpoint is ``GET /user``).

            :returns: Absolute userinfo URL.
            :raises ValueError: When no userinfo URL can be resolved.
        """
        url = str(
            self._provider_config.get("userinfo_endpoint") or "",
        ).strip()
        if url != "":
            return url

        metadata = self._resolve_server_metadata()
        url = str(metadata.get("userinfo_endpoint") or "").strip()
        if url != "":
            return url

        api_base = str(
            self._provider_config.get("api_base_url") or "",
        ).strip()
        if api_base != "":
            if not api_base.endswith("/"):
                api_base = api_base + "/"
            rtnval = api_base + "user"
            return rtnval

        errmsg = (
            "OAuth provider {!r} does not advertise a userinfo "
            "endpoint.".format(self._provider_name)
        )
        raise ValueError(errmsg)

    def _resolve_scope(self, override: Optional[str] = None) -> str:
        """
            Resolve the OAuth scope string for an authorization
            request.

            :param override: Explicit scope value. When non-empty,
                             takes precedence over the configured
                             scope.

            :returns: A space-delimited scope string. Empty only when
                      neither override nor config supplies one.
        """
        if override is not None:
            override_value = str(override).strip()
            if override_value != "":
                return override_value

        configured = str(self._client_kwargs.get("scope") or "").strip()
        if configured != "":
            return configured

        return ""

    def build_authorization_url(
        self,
        *,
        redirect_uri: str,
        state: str,
        nonce: Optional[str] = None,
        scope: Optional[str] = None,
        extra_params: Optional[Dict[str, str]] = None,
    ) -> str:
        """
            Build the URL the kickoff handler redirects the browser
            to.

            :param redirect_uri: Absolute callback URL the provider
                                 will redirect back to after the user
                                 approves.
            :param state: Opaque CSRF-protection token. The kickoff
                          handler generates this with
                          :func:`generate_oauth_state` and stores it
                          on the signed state cookie before
                          redirecting; the callback handler asserts
                          the value the provider returns matches.
            :param nonce: Optional OIDC nonce. Required for OIDC
                          providers (Google) so the id_token's nonce
                          claim can be validated. Stored on the
                          state cookie alongside ``state``.
            :param scope: Optional explicit scope override. Falls
                          back to ``client_kwargs["scope"]``.
            :param extra_params: Provider-specific extras (e.g.
                                 ``access_type=offline`` for Google,
                                 ``prompt=consent`` for forced
                                 re-consent on registration).

            :returns: The absolute URL to redirect the browser to.
        """
        # Lazy import keeps the module import-light when the OAuth
        # methods are not exercised — and lets consumers that don't
        # enable the ``oauth`` extra import this module without
        # crashing. Consumers that reach this code path without
        # ``authlib`` installed get a diagnostic message pointing
        # them at the right ``pip install`` invocation.
        try:
            from authlib.integrations.requests_client import OAuth2Session
        except ImportError as exc:
            errmsg = (
                "OAuth client functionality requires the 'oauth' "
                "extra. Install it with: "
                "pip install automojo-webworks[oauth]"
            )
            raise ImportError(errmsg) from exc

        scope_value = self._resolve_scope(override=scope)

        params: Dict[str, Any] = {}
        if extra_params is not None:
            params.update(extra_params)

        if nonce is not None:
            nonce_value = str(nonce).strip()
            if nonce_value != "":
                params["nonce"] = nonce_value

        scope_arg = scope_value if scope_value != "" else None

        session = OAuth2Session(
            client_id=self._client_id,
            client_secret=self._client_secret,
            scope=scope_arg,
            redirect_uri=redirect_uri,
            state=state,
        )

        authorize_url = self._resolve_authorize_url()

        url, _state = session.create_authorization_url(
            authorize_url,
            state=state,
            **params,
        )

        rtnval = url
        return rtnval

    def exchange_code_for_token(
        self,
        *,
        redirect_uri: str,
        code: str,
        state: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
            Exchange the authorization code returned to the callback
            for a token payload.

            :param redirect_uri: The same redirect URI passed to
                                 :meth:`build_authorization_url`.
            :param code: The authorization code returned by the
                         provider on the callback URL.
            :param state: Optional state value (some providers
                          include it in the form-encoded body when
                          the callback is a POST).

            :returns: The token dict from the provider, with at
                      minimum ``access_token`` and (for OIDC
                      providers) ``id_token``.
            :raises authlib.integrations.base_client.OAuthError:
                       When the provider rejects the token request.
        """
        try:
            from authlib.integrations.requests_client import OAuth2Session
        except ImportError as exc:
            errmsg = (
                "OAuth client functionality requires the 'oauth' "
                "extra. Install it with: "
                "pip install automojo-webworks[oauth]"
            )
            raise ImportError(errmsg) from exc

        session = OAuth2Session(
            client_id=self._client_id,
            client_secret=self._client_secret,
            redirect_uri=redirect_uri,
            state=state,
        )

        token_url = self._resolve_token_url()

        token = session.fetch_token(
            token_url,
            code=code,
            redirect_uri=redirect_uri,
            state=state,
        )

        rtnval = dict(token)
        return rtnval

    def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """
            Exchange a stored refresh token for a fresh access token.

            Used by application-level OAuth-token refresh cycles —
            e.g. a periodic background task that pre-warms tokens
            close to expiry, or a downstream API call that just
            received ``401``.

            The returned dict matches the shape that
            :meth:`exchange_code_for_token` returns: same keys
            (``access_token``, optional ``refresh_token``,
            ``token_type``, ``scope``, ``expires_at`` /
            ``expires_in``). Some providers issue a brand-new refresh
            token on each refresh; others (Google) keep the same one.
            Caller storage code is responsible for preserving the
            previous refresh token when the new payload omits it.

            :param refresh_token: The stored refresh token to
                                  exchange. Must not be empty.

            :returns: A dict of token attributes from the provider.
            :raises ValueError: When ``refresh_token`` is blank.
            :raises authlib.integrations.base_client.OAuthError:
                       When the provider rejects the refresh request
                       (e.g. ``invalid_grant`` after the user has
                       revoked consent).
        """
        try:
            from authlib.integrations.requests_client import OAuth2Session
        except ImportError as exc:
            errmsg = (
                "OAuth client functionality requires the 'oauth' "
                "extra. Install it with: "
                "pip install automojo-webworks[oauth]"
            )
            raise ImportError(errmsg) from exc

        refresh_value = str(refresh_token or "").strip()
        if refresh_value == "":
            errmsg = (
                "OAuth provider {!r} refresh requires a non-empty "
                "refresh token.".format(self._provider_name)
            )
            raise ValueError(errmsg)

        token_url = self._resolve_token_url()

        session = OAuth2Session(
            client_id=self._client_id,
            client_secret=self._client_secret,
        )

        new_token = session.refresh_token(
            token_url,
            refresh_token=refresh_value,
        )

        rtnval = dict(new_token)
        return rtnval

    def parse_id_token(
        self,
        token: Dict[str, Any],
        *,
        nonce: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
            Parse and validate the OIDC ``id_token`` JWT in a token
            payload.

            Validates the signature against the JWKS advertised by
            the provider's discovery document, the issuer claim, the
            audience claim, and (when supplied) the nonce claim.
            Algorithms are restricted to RS256 / ES256 / ES384 /
            ES512 to defend against algorithm-confusion attacks.

            :param token: Token payload returned by
                          :meth:`exchange_code_for_token`. Must
                          contain an ``id_token`` key.
            :param nonce: Optional nonce that the kickoff handler
                          stored on the state cookie. When supplied,
                          the parser asserts the JWT's ``nonce``
                          claim matches.

            :returns: The decoded JWT claim set as a dict (the OIDC
                      userinfo claims).
            :raises ValueError: When the token has no ``id_token`` or
                                the discovery document is missing
                                the ``jwks_uri`` / ``issuer`` fields
                                needed for validation.
        """
        try:
            from authlib.jose import JsonWebToken
        except ImportError as exc:
            errmsg = (
                "OIDC id_token validation requires the 'oauth' "
                "extra. Install it with: "
                "pip install automojo-webworks[oauth]"
            )
            raise ImportError(errmsg) from exc

        id_token_value = token.get("id_token")
        if id_token_value is None:
            raise ValueError("OAuth token payload has no id_token claim.")

        id_token_str = str(id_token_value).strip()
        if id_token_str == "":
            raise ValueError("OAuth token payload has no id_token claim.")

        metadata = self._resolve_server_metadata()
        jwks_uri = str(metadata.get("jwks_uri") or "").strip()
        if jwks_uri == "":
            errmsg = (
                "OAuth provider {!r} does not advertise a jwks_uri; "
                "cannot validate id_token.".format(self._provider_name)
            )
            raise ValueError(errmsg)

        jwks_response = http_requests.get(
            jwks_uri,
            timeout=_HTTP_TIMEOUT_SECONDS,
        )
        jwks_response.raise_for_status()
        jwks = jwks_response.json()

        claims_options: Dict[str, Any] = {
            "iss": {
                "essential": True,
                "value": metadata.get("issuer"),
            },
            "aud": {
                "essential": True,
                "value": self._client_id,
            },
        }

        if nonce is not None:
            nonce_value = str(nonce).strip()
            if nonce_value != "":
                claims_options["nonce"] = {
                    "essential": True,
                    "value": nonce_value,
                }

        jwt = JsonWebToken(_ACCEPTED_ID_TOKEN_ALGORITHMS)
        claims = jwt.decode(
            id_token_str,
            key=jwks,
            claims_options=claims_options,
        )
        claims.validate()

        rtnval = dict(claims)
        return rtnval

    def fetch_userinfo(self, token: Dict[str, Any]) -> Dict[str, Any]:
        """
            Fetch the provider's userinfo endpoint with the access
            token.

            Used for non-OIDC providers (GitHub) that don't return an
            ``id_token`` and require a follow-up API call to recover
            the profile claims. OIDC providers should generally use
            :meth:`parse_id_token` instead — it's one fewer round
            trip and includes the claims the provider actually
            signed.

            :param token: Token payload from
                          :meth:`exchange_code_for_token`.

            :returns: The userinfo dict.
            :raises ValueError: When the token has no
                                ``access_token`` or the userinfo
                                endpoint returns a non-dict body.
            :raises requests.HTTPError: When the userinfo endpoint
                                        returns a non-2xx response.
        """
        access_token = token.get("access_token")
        if access_token is None:
            errmsg = (
                "OAuth token payload from {!r} has no "
                "access_token.".format(self._provider_name)
            )
            raise ValueError(errmsg)

        access_token_str = str(access_token).strip()
        if access_token_str == "":
            errmsg = (
                "OAuth token payload from {!r} has no "
                "access_token.".format(self._provider_name)
            )
            raise ValueError(errmsg)

        userinfo_url = self._resolve_userinfo_url()

        response = http_requests.get(
            userinfo_url,
            headers={
                "Authorization": "Bearer {}".format(access_token_str),
            },
            timeout=_HTTP_TIMEOUT_SECONDS,
        )
        response.raise_for_status()

        loaded = response.json()
        if not isinstance(loaded, dict):
            errmsg = (
                "OAuth provider {!r} returned a non-dict userinfo "
                "payload.".format(self._provider_name)
            )
            raise ValueError(errmsg)

        rtnval = loaded
        return rtnval


def generate_oauth_state() -> str:
    """
        Generate a cryptographically random state value for the
        kickoff redirect.

        The kickoff handler stores this on the signed state cookie
        and includes it in the authorization URL; the callback
        handler asserts the provider returns the same value. The
        token is 32 random bytes encoded URL-safe-base64 (256 bits
        of entropy), which exceeds every provider's documented
        minimum.

        :returns: A 32-byte URL-safe random token.
    """
    rtnval = secrets.token_urlsafe(32)
    return rtnval


def generate_oauth_nonce() -> str:
    """
        Generate a cryptographically random nonce for OIDC
        authorization requests.

        Distinct from the state value: nonce ties the eventual
        ``id_token`` JWT back to the originating authorization
        request, where state ties the *callback URL* back to the
        originating browser.

        :returns: A 32-byte URL-safe random token.
    """
    rtnval = secrets.token_urlsafe(32)
    return rtnval


__all__ = [
    "OAuthClient",
    "generate_oauth_nonce",
    "generate_oauth_state",
]
