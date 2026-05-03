"""
    Unit tests for :mod:`automojo.webworks.authentication.oauth`.

    Covered:
        - Constructor validation rejects empty provider name and
          missing ``client_id`` / ``client_secret``.
        - ``_resolve_authorize_url`` / ``_resolve_token_url`` /
          ``_resolve_userinfo_url`` walk the documented fallback
          chains and surface a descriptive ``ValueError`` when the
          chain bottoms out.
        - ``_resolve_scope`` honours an explicit override, falls
          back to ``client_kwargs["scope"]``, and returns ``""`` when
          neither source provides one.
        - ``build_authorization_url`` returns a URL whose query
          parameters carry the supplied state, nonce, and provider
          extras (``access_type=offline`` etc.).
        - ``parse_id_token`` rejects a payload with no ``id_token``
          and a payload whose discovery document is missing
          ``jwks_uri``.
        - ``fetch_userinfo`` rejects a payload with no
          ``access_token``.
        - ``generate_oauth_state`` / ``generate_oauth_nonce`` return
          URL-safe random tokens of the documented length.
"""

from typing import Any, Dict, Optional
from urllib.parse import parse_qs, urlparse

import pytest

from automojo.webworks.authentication.oauth import (
    OAuthClient,
    generate_oauth_nonce,
    generate_oauth_state,
)


# =============================================================================
# Helpers
# =============================================================================


def _make_client(
    provider_name: str = "google",
    config_overrides: Optional[Dict[str, Any]] = None,
) -> OAuthClient:
    """
        Construct a baseline :class:`OAuthClient` with the supplied
        provider name and config overrides merged onto the
        canonical Google-shaped config.
    """
    base_config: Dict[str, Any] = {
        "client_id": "id-12345",
        "client_secret": "secret-67890",
        "authorize_url": "https://provider.example.com/o/authorize",
        "access_token_url": "https://provider.example.com/o/token",
        "userinfo_endpoint": "https://provider.example.com/o/userinfo",
        "client_kwargs": {"scope": "openid email profile"},
    }

    if config_overrides is not None:
        base_config.update(config_overrides)

    rtnval = OAuthClient(
        provider_name=provider_name,
        provider_config=base_config,
    )
    return rtnval


# =============================================================================
# Constructor
# =============================================================================


def test_constructor_rejects_empty_provider_name():
    with pytest.raises(ValueError, match="provider name is required"):
        OAuthClient(
            provider_name="",
            provider_config={
                "client_id": "id",
                "client_secret": "secret",
            },
        )

    return


def test_constructor_rejects_whitespace_provider_name():
    with pytest.raises(ValueError, match="provider name is required"):
        OAuthClient(
            provider_name="   ",
            provider_config={
                "client_id": "id",
                "client_secret": "secret",
            },
        )

    return


def test_constructor_rejects_missing_client_id():
    with pytest.raises(ValueError, match="client_id"):
        OAuthClient(
            provider_name="google",
            provider_config={"client_secret": "secret"},
        )

    return


def test_constructor_rejects_empty_client_secret():
    with pytest.raises(ValueError, match="client_secret"):
        OAuthClient(
            provider_name="google",
            provider_config={
                "client_id": "id",
                "client_secret": "   ",
            },
        )

    return


def test_constructor_strips_provider_name():
    client = _make_client(provider_name="  github  ")

    if client.provider_name != "github":
        errmsg = "Expected provider_name 'github', got {!r}".format(
            client.provider_name,
        )
        raise AssertionError(errmsg)

    return


def test_client_id_property_exposes_constructor_value():
    client = _make_client()

    if client.client_id != "id-12345":
        errmsg = "Expected client_id 'id-12345', got {!r}".format(client.client_id)
        raise AssertionError(errmsg)

    return


# =============================================================================
# URL resolvers
# =============================================================================


def test_resolve_authorize_url_prefers_explicit_config():
    client = _make_client()

    url = client._resolve_authorize_url()

    if url != "https://provider.example.com/o/authorize":
        errmsg = "Expected explicit authorize_url, got {!r}".format(url)
        raise AssertionError(errmsg)

    return


def test_resolve_authorize_url_falls_back_to_metadata(monkeypatch):
    client = _make_client(
        config_overrides={
            "authorize_url": "",
            "server_metadata_url": "https://provider.example.com/.well-known",
        },
    )

    monkeypatch.setattr(
        client,
        "_resolve_server_metadata",
        lambda: {
            "authorization_endpoint": "https://provider.example.com/oidc/authorize",
        },
    )

    url = client._resolve_authorize_url()

    if url != "https://provider.example.com/oidc/authorize":
        errmsg = "Expected metadata fallback, got {!r}".format(url)
        raise AssertionError(errmsg)

    return


def test_resolve_authorize_url_raises_when_no_source(monkeypatch):
    client = _make_client(config_overrides={"authorize_url": ""})

    monkeypatch.setattr(client, "_resolve_server_metadata", lambda: {})

    with pytest.raises(ValueError, match="authorization endpoint"):
        client._resolve_authorize_url()

    return


def test_resolve_token_url_falls_back_to_metadata(monkeypatch):
    client = _make_client(
        config_overrides={
            "access_token_url": "",
        },
    )

    monkeypatch.setattr(
        client,
        "_resolve_server_metadata",
        lambda: {
            "token_endpoint": "https://provider.example.com/oidc/token",
        },
    )

    url = client._resolve_token_url()

    if url != "https://provider.example.com/oidc/token":
        errmsg = "Expected metadata fallback, got {!r}".format(url)
        raise AssertionError(errmsg)

    return


def test_resolve_userinfo_url_falls_back_to_api_base():
    client = _make_client(
        provider_name="github",
        config_overrides={
            "userinfo_endpoint": "",
            "api_base_url": "https://api.github.com/",
            "authorize_url": "https://github.com/login/oauth/authorize",
            "access_token_url": "https://github.com/login/oauth/access_token",
            "client_kwargs": {"scope": "user:email"},
        },
    )

    url = client._resolve_userinfo_url()

    if url != "https://api.github.com/user":
        errmsg = "Expected GitHub api_base fallback, got {!r}".format(url)
        raise AssertionError(errmsg)

    return


def test_resolve_userinfo_url_appends_slash_to_api_base(monkeypatch):
    client = _make_client(
        config_overrides={
            "userinfo_endpoint": "",
            "api_base_url": "https://api.example.com",  # no trailing slash
        },
    )

    monkeypatch.setattr(client, "_resolve_server_metadata", lambda: {})

    url = client._resolve_userinfo_url()

    if url != "https://api.example.com/user":
        errmsg = "Expected api_base with appended slash, got {!r}".format(url)
        raise AssertionError(errmsg)

    return


def test_resolve_userinfo_url_raises_when_no_source(monkeypatch):
    client = _make_client(config_overrides={"userinfo_endpoint": ""})

    monkeypatch.setattr(client, "_resolve_server_metadata", lambda: {})
    client._provider_config["api_base_url"] = ""

    with pytest.raises(ValueError, match="userinfo endpoint"):
        client._resolve_userinfo_url()

    return


# =============================================================================
# Scope resolution
# =============================================================================


def test_resolve_scope_uses_override():
    client = _make_client()

    scope = client._resolve_scope(override="email")

    if scope != "email":
        errmsg = "Expected override scope, got {!r}".format(scope)
        raise AssertionError(errmsg)

    return


def test_resolve_scope_falls_back_to_config():
    client = _make_client()

    scope = client._resolve_scope()

    if scope != "openid email profile":
        errmsg = "Expected configured scope, got {!r}".format(scope)
        raise AssertionError(errmsg)

    return


def test_resolve_scope_returns_empty_when_no_source():
    client = _make_client(config_overrides={"client_kwargs": {}})

    scope = client._resolve_scope()

    if scope != "":
        errmsg = "Expected empty scope, got {!r}".format(scope)
        raise AssertionError(errmsg)

    return


# =============================================================================
# build_authorization_url
# =============================================================================


def test_build_authorization_url_carries_state_and_nonce():
    client = _make_client()

    url = client.build_authorization_url(
        redirect_uri="https://app.example.com/auth/oauth/callback?provider=google",
        state="state-token-001",
        nonce="nonce-token-001",
    )

    parsed = urlparse(url)
    params = parse_qs(parsed.query)

    if params.get("state") != ["state-token-001"]:
        errmsg = "Expected state param, got {!r}".format(params.get("state"))
        raise AssertionError(errmsg)

    if params.get("nonce") != ["nonce-token-001"]:
        errmsg = "Expected nonce param, got {!r}".format(params.get("nonce"))
        raise AssertionError(errmsg)

    if params.get("client_id") != ["id-12345"]:
        errmsg = "Expected client_id, got {!r}".format(params.get("client_id"))
        raise AssertionError(errmsg)

    if "redirect_uri" not in params:
        errmsg = "Expected redirect_uri in authorization URL"
        raise AssertionError(errmsg)

    return


def test_build_authorization_url_merges_extra_params():
    client = _make_client()

    url = client.build_authorization_url(
        redirect_uri="https://app.example.com/auth/oauth/callback?provider=google",
        state="state-token-002",
        extra_params={
            "access_type": "offline",
            "prompt": "consent",
        },
    )

    parsed = urlparse(url)
    params = parse_qs(parsed.query)

    if params.get("access_type") != ["offline"]:
        errmsg = "Expected access_type=offline, got {!r}".format(
            params.get("access_type"),
        )
        raise AssertionError(errmsg)

    if params.get("prompt") != ["consent"]:
        errmsg = "Expected prompt=consent, got {!r}".format(params.get("prompt"))
        raise AssertionError(errmsg)

    return


def test_build_authorization_url_uses_scope_override():
    client = _make_client()

    url = client.build_authorization_url(
        redirect_uri="https://app.example.com/auth/oauth/callback?provider=google",
        state="state-token-003",
        scope="user:email",
    )

    parsed = urlparse(url)
    params = parse_qs(parsed.query)

    if params.get("scope") != ["user:email"]:
        errmsg = "Expected scope override, got {!r}".format(params.get("scope"))
        raise AssertionError(errmsg)

    return


# =============================================================================
# parse_id_token
# =============================================================================


def test_parse_id_token_rejects_payload_without_id_token():
    client = _make_client()

    with pytest.raises(ValueError, match="no id_token"):
        client.parse_id_token({"access_token": "abc"})

    return


def test_parse_id_token_rejects_empty_id_token():
    client = _make_client()

    with pytest.raises(ValueError, match="no id_token"):
        client.parse_id_token({"id_token": "   "})

    return


def test_parse_id_token_round_trip_validates_signed_jwt(monkeypatch):
    """
        End-to-end: sign a JWT with a generated RSA key, construct
        the JWKS that publishes its public half, mock the JWKS HTTP
        fetch, and confirm :meth:`parse_id_token` decodes + validates
        the token cleanly under the joserfc-backed implementation.
    """
    import time

    from joserfc import jwt as joserfc_jwt
    from joserfc.jwk import RSAKey

    # Generate a fresh RSA key. Issue an id_token with the iss / aud /
    # nonce values the OAuthClient will assert against.
    signing_key = RSAKey.generate_key(
        2048,
        parameters={"kid": "round-trip-key"},
    )

    issuer = "https://provider.example.com"
    client_id = "id-12345"
    nonce_value = "round-trip-nonce"

    claims = {
        "iss": issuer,
        "aud": client_id,
        "nonce": nonce_value,
        "sub": "subject-1",
        "email": "user@example.com",
        "exp": int(time.time()) + 3600,
        "iat": int(time.time()),
    }
    id_token_str = joserfc_jwt.encode(
        {"alg": "RS256"},
        claims,
        signing_key,
    )

    # Public-half JWKS the provider would advertise.
    jwks = {"keys": [signing_key.as_dict(private=False)]}

    client = _make_client()

    # Stub server metadata + the JWKS HTTP fetch.
    monkeypatch.setattr(
        client,
        "_resolve_server_metadata",
        lambda: {
            "issuer": issuer,
            "jwks_uri": "https://provider.example.com/.well-known/jwks.json",
        },
    )

    class _StubResponse:
        def __init__(self, payload):
            self._payload = payload

        def raise_for_status(self):
            return None

        def json(self):
            return self._payload

    from automojo.webworks.authentication import oauth as oauth_module

    monkeypatch.setattr(
        oauth_module.http_requests,
        "get",
        lambda url, timeout=None: _StubResponse(jwks),
    )

    decoded = client.parse_id_token(
        {"id_token": id_token_str},
        nonce=nonce_value,
    )

    if decoded.get("sub") != "subject-1":
        errmsg = "Expected sub claim, got {!r}".format(decoded)
        raise AssertionError(errmsg)

    if decoded.get("email") != "user@example.com":
        errmsg = "Expected email claim, got {!r}".format(decoded)
        raise AssertionError(errmsg)

    return


def test_parse_id_token_rejects_wrong_nonce(monkeypatch):
    """
        joserfc must reject a JWT whose ``nonce`` claim doesn't match
        the value the kickoff handler stored on the state cookie.
    """
    import time

    from joserfc import jwt as joserfc_jwt
    from joserfc.jwk import RSAKey

    signing_key = RSAKey.generate_key(
        2048,
        parameters={"kid": "wrong-nonce-key"},
    )

    issuer = "https://provider.example.com"
    client_id = "id-12345"

    claims = {
        "iss": issuer,
        "aud": client_id,
        "nonce": "actual-nonce",
        "sub": "subject-1",
        "exp": int(time.time()) + 3600,
        "iat": int(time.time()),
    }
    id_token_str = joserfc_jwt.encode(
        {"alg": "RS256"},
        claims,
        signing_key,
    )

    jwks = {"keys": [signing_key.as_dict(private=False)]}

    client = _make_client()

    monkeypatch.setattr(
        client,
        "_resolve_server_metadata",
        lambda: {
            "issuer": issuer,
            "jwks_uri": "https://provider.example.com/.well-known/jwks.json",
        },
    )

    class _StubResponse:
        def __init__(self, payload):
            self._payload = payload

        def raise_for_status(self):
            return None

        def json(self):
            return self._payload

    from automojo.webworks.authentication import oauth as oauth_module

    monkeypatch.setattr(
        oauth_module.http_requests,
        "get",
        lambda url, timeout=None: _StubResponse(jwks),
    )

    raised = False
    try:
        client.parse_id_token(
            {"id_token": id_token_str},
            nonce="expected-different-nonce",
        )
    except Exception:
        raised = True

    if not raised:
        errmsg = "Expected parse_id_token to reject nonce mismatch"
        raise AssertionError(errmsg)

    return


def test_parse_id_token_rejects_when_metadata_lacks_jwks_uri(monkeypatch):
    client = _make_client(
        config_overrides={
            "server_metadata_url": "https://provider.example.com/.well-known",
        },
    )

    monkeypatch.setattr(
        client,
        "_resolve_server_metadata",
        lambda: {"issuer": "https://provider.example.com"},
    )

    with pytest.raises(ValueError, match="jwks_uri"):
        client.parse_id_token({"id_token": "header.payload.signature"})

    return


# =============================================================================
# fetch_userinfo
# =============================================================================


def test_fetch_userinfo_rejects_payload_without_access_token():
    client = _make_client()

    with pytest.raises(ValueError, match="no access_token"):
        client.fetch_userinfo({"id_token": "abc"})

    return


def test_fetch_userinfo_rejects_empty_access_token():
    client = _make_client()

    with pytest.raises(ValueError, match="no access_token"):
        client.fetch_userinfo({"access_token": "   "})

    return


# =============================================================================
# refresh_token
# =============================================================================


def test_refresh_token_rejects_empty_input():
    client = _make_client()

    with pytest.raises(ValueError, match="non-empty refresh token"):
        client.refresh_token("   ")

    return


# =============================================================================
# State / nonce generators
# =============================================================================


def test_generate_oauth_state_returns_url_safe_token():
    state = generate_oauth_state()

    if not isinstance(state, str):
        errmsg = "Expected str, got {!r}".format(type(state).__name__)
        raise AssertionError(errmsg)

    if len(state) < 32:
        errmsg = "Expected token of length >= 32, got len={}".format(len(state))
        raise AssertionError(errmsg)

    # URL-safe base64 = [A-Za-z0-9_-]
    allowed = set(
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        "abcdefghijklmnopqrstuvwxyz"
        "0123456789-_"
    )
    if not all(ch in allowed for ch in state):
        errmsg = "State contains non-URL-safe chars: {!r}".format(state)
        raise AssertionError(errmsg)

    return


def test_generate_oauth_state_emits_distinct_values():
    samples = {generate_oauth_state() for _ in range(50)}

    if len(samples) != 50:
        errmsg = "Expected 50 distinct values, got {}".format(len(samples))
        raise AssertionError(errmsg)

    return


def test_generate_oauth_nonce_emits_distinct_values():
    samples = {generate_oauth_nonce() for _ in range(50)}

    if len(samples) != 50:
        errmsg = "Expected 50 distinct values, got {}".format(len(samples))
        raise AssertionError(errmsg)

    return
