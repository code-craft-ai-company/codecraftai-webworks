"""
    Unit tests for :mod:`ccai.webworks.authentication.blueprints.oauthclient`.

    Covered:
        - **Kickoff** (``GET /login``): provider defaulting, success
          path attaches signed state cookie + redirects to provider,
          missing-secret → ``oauth_not_configured``, no providers
          configured → ``oauth_provider_unavailable``, unknown
          provider → ``unknown_provider``,
          ``provider_extras_resolver`` is honoured,
          authorization-URL build failure surfaces as
          ``oauth_provider_unavailable``.
        - **Register** (``POST /register``): missing captcha → 400
          ``missing_captcha``, captcha verifier rejects → 400
          ``captcha_failed``, success path returns JSON with
          ``redirect_url``.
        - **Callback** (``GET /callback``): provider error param,
          missing provider, missing / tampered state cookie,
          provider mismatch, state mismatch, missing code, unknown
          provider, exchange exception, parse_id_token exception,
          fetch_userinfo for non-OIDC providers,
          ``user_resolver`` error codes, short-circuit redirects,
          ``user_resolver`` returns wrong type, ``token_persister``
          invocation + non-fatal failure, missing
          ``session_blueprint`` → ``oauth_not_configured``,
          success path attaches session cookie + state-clear cookie.
        - **State cookie**: round-trip sign / unsign, tampered
          payload yields ``None``, expired payload yields ``None``,
          missing secret resolver yields ``None``.
        - **CSRF integration**:
          ``OAuthClientBlueprint.get_csrf_exempt_paths`` returns the
          register path resolved against the subclass base path.
        - **Disable**: each endpoint can be turned off via
          ``enabled_endpoints`` and returns 404.
"""

import json
import time

from typing import Any, Dict, List, Optional

from ccai.webworks.authentication.blueprints.oauthclient import (
    DEFAULT_STATE_COOKIE_NAME,
    ERROR_AUTHORIZATION_FAILED,
    ERROR_NOT_CONFIGURED,
    ERROR_NO_TOKEN,
    ERROR_PROVIDER_MISSING_ON_CALLBACK,
    ERROR_PROVIDER_UNAVAILABLE,
    ERROR_TOKEN_PARSE_FAILED,
    ERROR_UNKNOWN_PROVIDER,
    OAuthCallbackResult,
    OAuthClientBlueprint,
)
from ccai.webworks.authentication.blueprints.session import (
    SessionAuthBlueprint,
)
from ccai.webworks.authentication.core import Principal


# =============================================================================
# Test helpers
# =============================================================================


_TEST_SECRET = "test-secret-for-oauth-state-cookie-keying"


class MockRequest:
    """
        Minimal request stand-in.

        Surfaces ``query_params``, ``cookies``, ``scheme``, ``host``,
        and a ``json()`` / ``form()`` body — the four facets the
        blueprint reads.
    """

    def __init__(
        self,
        query_params: Optional[Dict[str, Any]] = None,
        cookies: Optional[Dict[str, str]] = None,
        json_body: Optional[Dict[str, Any]] = None,
        scheme: str = "https",
        host: str = "app.example.com",
    ):
        self.query_params = query_params or {}
        self.cookies = cookies or {}
        self._json_body = json_body
        self.scheme = scheme
        self.host = host

    def json(self):
        if self._json_body is None:
            errmsg = "no body"
            raise ValueError(errmsg)
        return self._json_body

    def form(self):
        return None


class StubOAuthClient:
    """
        Stand-in for :class:`OAuthClient` that records calls and
        returns canned values.
    """

    def __init__(
        self,
        provider_name: str = "google",
        authorization_url: str = "https://provider.example.com/o/authorize?ok=1",
        token_payload: Optional[Dict[str, Any]] = None,
        userinfo: Optional[Dict[str, Any]] = None,
        raise_on_build: Optional[Exception] = None,
        raise_on_exchange: Optional[Exception] = None,
        raise_on_parse_id_token: Optional[Exception] = None,
        raise_on_fetch_userinfo: Optional[Exception] = None,
    ):
        self.provider_name = provider_name
        self._authorization_url = authorization_url
        self._token_payload = token_payload or {
            "access_token": "atok",
            "id_token": "idtok",
        }
        self._userinfo = userinfo or {
            "sub": "subject-1",
            "email": "user@example.com",
        }
        self._raise_on_build = raise_on_build
        self._raise_on_exchange = raise_on_exchange
        self._raise_on_parse_id_token = raise_on_parse_id_token
        self._raise_on_fetch_userinfo = raise_on_fetch_userinfo

        self.calls: Dict[str, List[Dict[str, Any]]] = {
            "build": [],
            "exchange": [],
            "parse_id_token": [],
            "fetch_userinfo": [],
        }

    def build_authorization_url(self, **kwargs):
        self.calls["build"].append(kwargs)
        if self._raise_on_build is not None:
            raise self._raise_on_build
        return self._authorization_url

    def exchange_code_for_token(self, **kwargs):
        self.calls["exchange"].append(kwargs)
        if self._raise_on_exchange is not None:
            raise self._raise_on_exchange
        return dict(self._token_payload)

    def parse_id_token(self, token, *, nonce=None):
        self.calls["parse_id_token"].append(
            {"token": token, "nonce": nonce},
        )
        if self._raise_on_parse_id_token is not None:
            raise self._raise_on_parse_id_token
        return dict(self._userinfo)

    def fetch_userinfo(self, token):
        self.calls["fetch_userinfo"].append({"token": token})
        if self._raise_on_fetch_userinfo is not None:
            raise self._raise_on_fetch_userinfo
        return dict(self._userinfo)


def _make_session_blueprint() -> type:
    """
        Construct a fresh :class:`SessionAuthBlueprint` subclass
        with isolated class state so tests don't share session
        cookies / stores.
    """

    class FreshSession(SessionAuthBlueprint):
        pass

    FreshSession.identity_provider = None
    FreshSession.session_store = None
    FreshSession.session_duration = 3600
    FreshSession.remember_me_duration = 86400 * 30
    FreshSession.cookie_name = "site_session"
    FreshSession.cookie_secure = True
    FreshSession.cookie_httponly = True
    FreshSession.cookie_samesite = "Lax"
    FreshSession.enabled_endpoints = None
    FreshSession.auth_system = None
    FreshSession.base_path = "/auth/session"
    FreshSession._memory_store = {}

    rtnval = FreshSession
    return rtnval


def _make_oauth_blueprint(
    *,
    provider_resolver=None,
    provider_name_lister=None,
    user_resolver=None,
    token_persister=None,
    captcha_verifier=None,
    provider_extras_resolver=None,
    session_blueprint=None,
    secret_resolver=None,
) -> type:
    """
        Construct an isolated :class:`OAuthClientBlueprint` subclass
        with the supplied collaborators wired in.
    """

    class FreshOAuth(OAuthClientBlueprint):
        pass

    FreshOAuth.provider_resolver = (
        staticmethod(provider_resolver) if provider_resolver else None
    )
    FreshOAuth.provider_name_lister = (
        staticmethod(provider_name_lister) if provider_name_lister else None
    )
    FreshOAuth.user_resolver = (
        staticmethod(user_resolver) if user_resolver else None
    )
    FreshOAuth.token_persister = (
        staticmethod(token_persister) if token_persister else None
    )
    FreshOAuth.captcha_verifier = (
        staticmethod(captcha_verifier) if captcha_verifier else None
    )
    FreshOAuth.provider_extras_resolver = (
        staticmethod(provider_extras_resolver) if provider_extras_resolver else None
    )
    FreshOAuth.state_cookie_secret_resolver = (
        staticmethod(secret_resolver)
        if secret_resolver is not None
        else staticmethod(lambda: _TEST_SECRET)
    )
    FreshOAuth.session_blueprint = (
        session_blueprint
        if session_blueprint is not None
        else _make_session_blueprint()
    )
    FreshOAuth.enabled_endpoints = None
    FreshOAuth.auth_system = None
    FreshOAuth.base_path = "/auth/oauth"
    FreshOAuth.post_login_redirect_url = "/dashboard/"
    FreshOAuth.error_redirect_url = "/login"

    rtnval = FreshOAuth
    return rtnval


_DEFAULT_PROVIDER_CONFIG = {
    "google": {
        "client_id": "id-google",
        "client_secret": "secret-google",
        "authorize_url": "https://accounts.google.com/o/oauth2/v2/auth",
        "access_token_url": "https://oauth2.googleapis.com/token",
        "client_kwargs": {"scope": "openid email profile"},
    },
    "github": {
        "client_id": "id-github",
        "client_secret": "secret-github",
        "authorize_url": "https://github.com/login/oauth/authorize",
        "access_token_url": "https://github.com/login/oauth/access_token",
        "api_base_url": "https://api.github.com/",
        "client_kwargs": {"scope": "user:email"},
    },
}


def _provider_resolver(name: str):
    return _DEFAULT_PROVIDER_CONFIG.get(name)


def _provider_name_lister():
    return list(_DEFAULT_PROVIDER_CONFIG.keys())


def _set_cookie_headers(response) -> str:
    """
        Join every ``Set-Cookie`` header the response emits on the wire.

        The blueprint registers cookies through
        :meth:`Response.add_raw_set_cookie`, which emits one
        ``Set-Cookie`` header per cookie via :meth:`Response.to_wsgi`
        rather than a single entry in :attr:`Response.headers`, so
        the assertions read the wire headers.

        :param response: The :class:`Response` under test.

        :returns: The ``Set-Cookie`` header values joined by newlines,
                  or an empty string when the response sets no cookie.
    """
    _status, headers, _body = response.to_wsgi()

    values = [value for name, value in headers if name.lower() == "set-cookie"]

    rtnval = "\n".join(values)
    return rtnval


# =============================================================================
# State cookie round-trip
# =============================================================================


def test_state_cookie_round_trip():
    blueprint = _make_oauth_blueprint()

    payload = {
        "provider": "google",
        "state": "state-A",
        "nonce": "nonce-A",
        "register": True,
    }
    signed = blueprint._sign_state_payload(payload)

    if signed is None:
        errmsg = "Expected signed cookie value, got None"
        raise AssertionError(errmsg)

    unsigned = blueprint._unsign_state_payload(signed)

    if unsigned != payload:
        errmsg = "Round-trip mismatch: {!r} vs {!r}".format(payload, unsigned)
        raise AssertionError(errmsg)

    return


def test_state_cookie_unsign_rejects_tampered_value():
    blueprint = _make_oauth_blueprint()

    signed = blueprint._sign_state_payload({"provider": "google", "state": "x"})
    tampered = signed[:-3] + "AAA" if signed is not None else ""

    result = blueprint._unsign_state_payload(tampered)

    if result is not None:
        errmsg = "Tampered cookie must yield None, got {!r}".format(result)
        raise AssertionError(errmsg)

    return


def test_state_cookie_unsign_rejects_empty():
    blueprint = _make_oauth_blueprint()

    result = blueprint._unsign_state_payload("")
    if result is not None:
        errmsg = "Empty cookie must yield None, got {!r}".format(result)
        raise AssertionError(errmsg)

    result = blueprint._unsign_state_payload(None)
    if result is not None:
        errmsg = "None cookie must yield None, got {!r}".format(result)
        raise AssertionError(errmsg)

    return


def test_state_cookie_no_secret_resolver_returns_none():
    blueprint = _make_oauth_blueprint()
    blueprint.state_cookie_secret_resolver = None

    signed = blueprint._sign_state_payload({"provider": "g", "state": "s"})

    if signed is not None:
        errmsg = "Expected None when no secret is wired, got {!r}".format(signed)
        raise AssertionError(errmsg)

    return


def test_state_cookie_unsign_rejects_expired_payload():
    blueprint = _make_oauth_blueprint()
    blueprint.state_cookie_max_age_seconds = 1

    signed = blueprint._sign_state_payload({"provider": "google", "state": "x"})

    # Wait past max_age. Sleep 2s — itsdangerous's TTL check is exclusive
    # and uses wall-clock, so a hard sleep is the simplest reliable test.
    time.sleep(2)

    result = blueprint._unsign_state_payload(signed)

    if result is not None:
        errmsg = "Expected None for expired cookie, got {!r}".format(result)
        raise AssertionError(errmsg)

    return


# =============================================================================
# Kickoff (GET /login)
# =============================================================================


def test_kickoff_success_redirects_with_signed_cookie():
    stub_client = StubOAuthClient()

    blueprint = _make_oauth_blueprint(
        provider_resolver=_provider_resolver,
        provider_name_lister=_provider_name_lister,
    )

    # Replace OAuthClient construction with the stub.
    blueprint._resolve_oauth_client = classmethod(lambda cls, provider: stub_client).__get__(None, blueprint)

    request = MockRequest(query_params={"provider": "google", "register": "1"})

    response = blueprint.kickoff(request)

    if response.status_code != 302:
        errmsg = "Expected 302, got {}".format(response.status_code)
        raise AssertionError(errmsg)

    location = response.headers["Location"]
    if location != "https://provider.example.com/o/authorize?ok=1":
        errmsg = "Expected provider authorization URL, got {!r}".format(location)
        raise AssertionError(errmsg)

    cookie = _set_cookie_headers(response)
    if DEFAULT_STATE_COOKIE_NAME not in cookie:
        errmsg = "Expected state cookie in Set-Cookie, got {!r}".format(cookie)
        raise AssertionError(errmsg)

    if "HttpOnly" not in cookie or "Secure" not in cookie or "SameSite=Lax" not in cookie:
        errmsg = "State cookie must carry HttpOnly + Secure + SameSite=Lax, got {!r}".format(
            cookie,
        )
        raise AssertionError(errmsg)

    if len(stub_client.calls["build"]) != 1:
        errmsg = "Expected exactly one build_authorization_url call"
        raise AssertionError(errmsg)

    build_call = stub_client.calls["build"][0]
    if build_call["state"] is None or len(build_call["state"]) < 16:
        errmsg = "Expected non-trivial state token, got {!r}".format(build_call["state"])
        raise AssertionError(errmsg)

    if build_call["nonce"] is None:
        errmsg = "Expected nonce to be generated for OIDC kickoff"
        raise AssertionError(errmsg)

    return


def test_kickoff_defaults_to_default_provider_when_query_omits_it():
    stub_client = StubOAuthClient()

    blueprint = _make_oauth_blueprint(
        provider_resolver=_provider_resolver,
        provider_name_lister=_provider_name_lister,
    )
    blueprint.default_provider_name = "google"

    blueprint._resolve_oauth_client = classmethod(lambda cls, provider: stub_client).__get__(None, blueprint)

    request = MockRequest(query_params={})

    response = blueprint.kickoff(request)

    if response.status_code != 302:
        errmsg = "Expected 302, got {}".format(response.status_code)
        raise AssertionError(errmsg)

    return


def test_kickoff_no_secret_resolver_redirects_with_not_configured():
    blueprint = _make_oauth_blueprint(
        provider_resolver=_provider_resolver,
        provider_name_lister=_provider_name_lister,
    )
    blueprint.state_cookie_secret_resolver = None

    request = MockRequest(query_params={"provider": "google"})

    response = blueprint.kickoff(request)

    location = response.headers["Location"]
    if "error={}".format(ERROR_NOT_CONFIGURED) not in location:
        errmsg = "Expected oauth_not_configured, got {!r}".format(location)
        raise AssertionError(errmsg)

    return


def test_kickoff_no_providers_configured_redirects_with_unavailable():
    blueprint = _make_oauth_blueprint(
        provider_resolver=lambda name: None,
        provider_name_lister=lambda: [],
    )

    request = MockRequest(query_params={"provider": "google"})

    response = blueprint.kickoff(request)

    location = response.headers["Location"]
    if "error={}".format(ERROR_PROVIDER_UNAVAILABLE) not in location:
        errmsg = "Expected oauth_provider_unavailable, got {!r}".format(location)
        raise AssertionError(errmsg)

    return


def test_kickoff_unknown_provider_redirects_with_unknown_provider():
    blueprint = _make_oauth_blueprint(
        provider_resolver=lambda name: None,  # nothing matches
        provider_name_lister=lambda: ["google"],  # but we have google
    )

    request = MockRequest(query_params={"provider": "facebook"})

    response = blueprint.kickoff(request)

    location = response.headers["Location"]
    if "error={}".format(ERROR_UNKNOWN_PROVIDER) not in location:
        errmsg = "Expected unknown_provider, got {!r}".format(location)
        raise AssertionError(errmsg)

    return


def test_kickoff_invokes_provider_extras_resolver():
    stub_client = StubOAuthClient()
    captured: Dict[str, Any] = {}

    def extras_resolver(provider, is_register):
        captured["provider"] = provider
        captured["register"] = is_register
        return {"access_type": "offline", "prompt": "consent"}

    blueprint = _make_oauth_blueprint(
        provider_resolver=_provider_resolver,
        provider_name_lister=_provider_name_lister,
        provider_extras_resolver=extras_resolver,
    )

    blueprint._resolve_oauth_client = classmethod(lambda cls, provider: stub_client).__get__(None, blueprint)

    request = MockRequest(query_params={"provider": "google", "register": "1"})

    blueprint.kickoff(request)

    if captured.get("provider") != "google":
        errmsg = "Expected resolver called with provider='google', got {!r}".format(captured)
        raise AssertionError(errmsg)

    if captured.get("register") is not True:
        errmsg = "Expected register=True, got {!r}".format(captured)
        raise AssertionError(errmsg)

    build_call = stub_client.calls["build"][0]
    extras = build_call.get("extra_params") or {}
    if extras.get("access_type") != "offline":
        errmsg = "Expected access_type=offline forwarded, got {!r}".format(extras)
        raise AssertionError(errmsg)

    return


def test_kickoff_authorization_url_build_failure_redirects_with_unavailable():
    stub_client = StubOAuthClient(raise_on_build=RuntimeError("network down"))

    blueprint = _make_oauth_blueprint(
        provider_resolver=_provider_resolver,
        provider_name_lister=_provider_name_lister,
    )

    blueprint._resolve_oauth_client = classmethod(lambda cls, provider: stub_client).__get__(None, blueprint)

    request = MockRequest(query_params={"provider": "google"})

    response = blueprint.kickoff(request)

    location = response.headers["Location"]
    if "error={}".format(ERROR_PROVIDER_UNAVAILABLE) not in location:
        errmsg = "Expected oauth_provider_unavailable, got {!r}".format(location)
        raise AssertionError(errmsg)

    return


# =============================================================================
# Register (POST /register)
# =============================================================================


def test_register_missing_captcha_returns_400():
    blueprint = _make_oauth_blueprint(
        provider_resolver=_provider_resolver,
        captcha_verifier=lambda token: True,
    )

    request = MockRequest(json_body={"provider": "google"})

    response = blueprint.register_intent(request)

    if response.status_code != 400:
        errmsg = "Expected 400, got {}".format(response.status_code)
        raise AssertionError(errmsg)

    if json.loads(response.body).get("error") != "missing_captcha":
        errmsg = "Expected missing_captcha, got {!r}".format(json.loads(response.body))
        raise AssertionError(errmsg)

    return


def test_register_failed_captcha_returns_400():
    blueprint = _make_oauth_blueprint(
        provider_resolver=_provider_resolver,
        captcha_verifier=lambda token: False,
    )

    request = MockRequest(
        json_body={"provider": "google", "captcha_response": "abc"},
    )

    response = blueprint.register_intent(request)

    if response.status_code != 400:
        errmsg = "Expected 400, got {}".format(response.status_code)
        raise AssertionError(errmsg)

    if json.loads(response.body).get("error") != "captcha_failed":
        errmsg = "Expected captcha_failed, got {!r}".format(json.loads(response.body))
        raise AssertionError(errmsg)

    return


def test_register_success_returns_kickoff_url():
    blueprint = _make_oauth_blueprint(
        provider_resolver=_provider_resolver,
        captcha_verifier=lambda token: True,
    )

    request = MockRequest(
        json_body={"provider": "github", "captcha_response": "valid-token"},
    )

    response = blueprint.register_intent(request)

    if response.status_code != 200:
        errmsg = "Expected 200, got {}".format(response.status_code)
        raise AssertionError(errmsg)

    body = json.loads(response.body)
    if body.get("success") is not True:
        errmsg = "Expected success=True, got {!r}".format(body)
        raise AssertionError(errmsg)

    redirect_url = body.get("redirect_url", "")
    if "/auth/oauth/login" not in redirect_url:
        errmsg = "Expected /auth/oauth/login in redirect_url, got {!r}".format(redirect_url)
        raise AssertionError(errmsg)

    if "provider=github" not in redirect_url:
        errmsg = "Expected provider=github in redirect_url, got {!r}".format(redirect_url)
        raise AssertionError(errmsg)

    if "register=1" not in redirect_url:
        errmsg = "Expected register=1 in redirect_url, got {!r}".format(redirect_url)
        raise AssertionError(errmsg)

    return


def test_register_no_verifier_skips_captcha_check():
    blueprint = _make_oauth_blueprint(
        provider_resolver=_provider_resolver,
        captcha_verifier=None,  # dev mode
    )

    request = MockRequest(
        json_body={"provider": "google", "captcha_response": "anything"},
    )

    response = blueprint.register_intent(request)

    if response.status_code != 200:
        errmsg = "Expected 200, got {}".format(response.status_code)
        raise AssertionError(errmsg)

    return


# =============================================================================
# Callback (GET /callback) — error paths
# =============================================================================


def _build_callback_request(
    blueprint,
    *,
    provider="google",
    state="state-A",
    nonce="nonce-A",
    register=False,
    code="auth-code-1",
    cookie_state=None,
    cookie_provider=None,
    cookie_nonce=None,
    cookie_register=None,
    cookie_value_override=None,
    extra_query=None,
):
    """
        Build a MockRequest with a signed state cookie matching the
        supplied ``state`` / ``nonce`` / ``provider`` / ``register``
        unless overridden.
    """
    payload_state = cookie_state if cookie_state is not None else state
    payload_provider = cookie_provider if cookie_provider is not None else provider
    payload_nonce = cookie_nonce if cookie_nonce is not None else nonce
    payload_register = (
        cookie_register if cookie_register is not None else register
    )

    if cookie_value_override is not None:
        cookie_value = cookie_value_override
    else:
        cookie_value = blueprint._sign_state_payload({
            "provider": payload_provider,
            "state": payload_state,
            "nonce": payload_nonce,
            "register": payload_register,
        }) or ""

    query = {"provider": provider, "state": state, "code": code}
    if extra_query is not None:
        query.update(extra_query)

    cookies = {DEFAULT_STATE_COOKIE_NAME: cookie_value} if cookie_value else {}

    rtnval = MockRequest(query_params=query, cookies=cookies)
    return rtnval


def test_callback_provider_returned_error_redirects_with_authorization_failed():
    blueprint = _make_oauth_blueprint(
        provider_resolver=_provider_resolver,
        provider_name_lister=_provider_name_lister,
        user_resolver=lambda *args, **kwargs: OAuthCallbackResult(),
    )

    request = MockRequest(
        query_params={"provider": "google", "error": "access_denied"},
    )

    response = blueprint.callback(request)

    location = response.headers["Location"]
    if "error={}".format(ERROR_AUTHORIZATION_FAILED) not in location:
        errmsg = "Expected oauth_authorization_failed, got {!r}".format(location)
        raise AssertionError(errmsg)

    if "provider_error=access_denied" not in location:
        errmsg = "Expected provider_error=access_denied, got {!r}".format(location)
        raise AssertionError(errmsg)

    return


def test_callback_missing_provider_redirects_with_provider_missing():
    blueprint = _make_oauth_blueprint(
        provider_resolver=_provider_resolver,
        user_resolver=lambda *args, **kwargs: OAuthCallbackResult(),
    )

    request = MockRequest(query_params={"state": "x", "code": "y"})

    response = blueprint.callback(request)

    location = response.headers["Location"]
    if "error={}".format(ERROR_PROVIDER_MISSING_ON_CALLBACK) not in location:
        errmsg = "Expected provider_missing_callback, got {!r}".format(location)
        raise AssertionError(errmsg)

    return


def test_callback_missing_state_cookie_redirects_with_token_parse_failed():
    blueprint = _make_oauth_blueprint(
        provider_resolver=_provider_resolver,
        user_resolver=lambda *args, **kwargs: OAuthCallbackResult(),
    )

    request = MockRequest(
        query_params={"provider": "google", "state": "x", "code": "y"},
    )

    response = blueprint.callback(request)

    location = response.headers["Location"]
    if "error={}".format(ERROR_TOKEN_PARSE_FAILED) not in location:
        errmsg = "Expected token_parse_failed, got {!r}".format(location)
        raise AssertionError(errmsg)

    return


def test_callback_provider_mismatch_redirects_with_token_parse_failed():
    blueprint = _make_oauth_blueprint(
        provider_resolver=_provider_resolver,
        user_resolver=lambda *args, **kwargs: OAuthCallbackResult(),
    )

    request = _build_callback_request(
        blueprint,
        provider="google",  # query says google
        cookie_provider="github",  # cookie says github
    )

    response = blueprint.callback(request)

    location = response.headers["Location"]
    if "error={}".format(ERROR_TOKEN_PARSE_FAILED) not in location:
        errmsg = "Expected token_parse_failed for provider mismatch, got {!r}".format(
            location,
        )
        raise AssertionError(errmsg)

    return


def test_callback_state_mismatch_redirects_with_token_parse_failed():
    blueprint = _make_oauth_blueprint(
        provider_resolver=_provider_resolver,
        user_resolver=lambda *args, **kwargs: OAuthCallbackResult(),
    )

    request = _build_callback_request(
        blueprint,
        state="state-from-provider",
        cookie_state="different-cookie-state",
    )

    response = blueprint.callback(request)

    location = response.headers["Location"]
    if "error={}".format(ERROR_TOKEN_PARSE_FAILED) not in location:
        errmsg = "Expected token_parse_failed for state mismatch, got {!r}".format(
            location,
        )
        raise AssertionError(errmsg)

    return


def test_callback_missing_code_redirects_with_no_token():
    blueprint = _make_oauth_blueprint(
        provider_resolver=_provider_resolver,
        user_resolver=lambda *args, **kwargs: OAuthCallbackResult(),
    )

    request = _build_callback_request(blueprint, code="")

    response = blueprint.callback(request)

    location = response.headers["Location"]
    if "error={}".format(ERROR_NO_TOKEN) not in location:
        errmsg = "Expected oauth_no_token, got {!r}".format(location)
        raise AssertionError(errmsg)

    return


def test_callback_unknown_provider_after_state_validation():
    blueprint = _make_oauth_blueprint(
        provider_resolver=lambda name: None,  # everything is unknown
        user_resolver=lambda *args, **kwargs: OAuthCallbackResult(),
    )

    request = _build_callback_request(blueprint)

    response = blueprint.callback(request)

    location = response.headers["Location"]
    if "error={}".format(ERROR_UNKNOWN_PROVIDER) not in location:
        errmsg = "Expected unknown_provider, got {!r}".format(location)
        raise AssertionError(errmsg)

    return


def test_callback_token_exchange_failure_redirects_with_authorization_failed():
    stub_client = StubOAuthClient(raise_on_exchange=RuntimeError("token refused"))

    blueprint = _make_oauth_blueprint(
        provider_resolver=_provider_resolver,
        user_resolver=lambda *args, **kwargs: OAuthCallbackResult(),
    )

    blueprint._resolve_oauth_client = classmethod(lambda cls, provider: stub_client).__get__(None, blueprint)

    request = _build_callback_request(blueprint)

    response = blueprint.callback(request)

    location = response.headers["Location"]
    if "error={}".format(ERROR_AUTHORIZATION_FAILED) not in location:
        errmsg = "Expected oauth_authorization_failed, got {!r}".format(location)
        raise AssertionError(errmsg)

    return


def test_callback_id_token_parse_failure_redirects_with_token_parse_failed():
    stub_client = StubOAuthClient(
        raise_on_parse_id_token=RuntimeError("invalid signature"),
    )

    blueprint = _make_oauth_blueprint(
        provider_resolver=_provider_resolver,
        user_resolver=lambda *args, **kwargs: OAuthCallbackResult(),
    )

    blueprint._resolve_oauth_client = classmethod(lambda cls, provider: stub_client).__get__(None, blueprint)

    request = _build_callback_request(blueprint)

    response = blueprint.callback(request)

    location = response.headers["Location"]
    if "error={}".format(ERROR_TOKEN_PARSE_FAILED) not in location:
        errmsg = "Expected token_parse_failed, got {!r}".format(location)
        raise AssertionError(errmsg)

    return


def test_callback_non_oidc_provider_uses_fetch_userinfo():
    # No id_token in token payload → blueprint must call fetch_userinfo.
    stub_client = StubOAuthClient(
        token_payload={"access_token": "atok"},
        userinfo={"id": "github-1", "login": "octocat"},
    )

    captured_principal: Dict[str, Any] = {}

    def user_resolver(provider, user_info, is_register, request):
        captured_principal["user_info"] = user_info
        principal = Principal(
            identifier="user-1",
            display_name="Octo Cat",
            roles=set(),
        )
        return OAuthCallbackResult(
            principal=principal,
            provider_ref_id=str(user_info.get("id")),
        )

    blueprint = _make_oauth_blueprint(
        provider_resolver=_provider_resolver,
        user_resolver=user_resolver,
    )

    blueprint._resolve_oauth_client = classmethod(lambda cls, provider: stub_client).__get__(None, blueprint)

    request = _build_callback_request(blueprint, provider="github")
    request.query_params["provider"] = "github"
    # rebuild the cookie so it matches the github provider
    cookie = blueprint._sign_state_payload({
        "provider": "github",
        "state": "state-A",
        "nonce": "nonce-A",
        "register": False,
    })
    request.cookies = {DEFAULT_STATE_COOKIE_NAME: cookie}

    response = blueprint.callback(request)

    if response.status_code != 302:
        errmsg = "Expected 302, got {}".format(response.status_code)
        raise AssertionError(errmsg)

    if len(stub_client.calls["fetch_userinfo"]) != 1:
        errmsg = "Expected fetch_userinfo to be called exactly once for non-OIDC, got {}".format(
            len(stub_client.calls["fetch_userinfo"]),
        )
        raise AssertionError(errmsg)

    if captured_principal.get("user_info", {}).get("id") != "github-1":
        errmsg = "Expected userinfo to reach user_resolver, got {!r}".format(
            captured_principal,
        )
        raise AssertionError(errmsg)

    return


def test_callback_user_resolver_error_code_propagates():
    stub_client = StubOAuthClient()

    blueprint = _make_oauth_blueprint(
        provider_resolver=_provider_resolver,
        user_resolver=lambda *args, **kwargs: OAuthCallbackResult(
            error_code="user-already-exists",
        ),
    )

    blueprint._resolve_oauth_client = classmethod(lambda cls, provider: stub_client).__get__(None, blueprint)

    request = _build_callback_request(blueprint)

    response = blueprint.callback(request)

    location = response.headers["Location"]
    if "error=user-already-exists" not in location:
        errmsg = "Expected user-already-exists, got {!r}".format(location)
        raise AssertionError(errmsg)

    # State-clear cookie should be attached on every callback exit path.
    cookie_header = _set_cookie_headers(response)
    if "Max-Age=0" not in cookie_header:
        errmsg = "Expected state-clear cookie on error redirect, got {!r}".format(cookie_header)
        raise AssertionError(errmsg)

    return


def test_callback_user_resolver_short_circuit_redirect():
    stub_client = StubOAuthClient()

    blueprint = _make_oauth_blueprint(
        provider_resolver=_provider_resolver,
        user_resolver=lambda *args, **kwargs: OAuthCallbackResult(
            short_circuit_redirect_url="/convert-user-to-oauth",
        ),
    )

    blueprint._resolve_oauth_client = classmethod(lambda cls, provider: stub_client).__get__(None, blueprint)

    request = _build_callback_request(blueprint)

    response = blueprint.callback(request)

    if response.status_code != 302:
        errmsg = "Expected 302, got {}".format(response.status_code)
        raise AssertionError(errmsg)

    if response.headers["Location"] != "/convert-user-to-oauth":
        errmsg = "Expected short-circuit URL, got {!r}".format(
            response.headers["Location"],
        )
        raise AssertionError(errmsg)

    return


def test_callback_user_resolver_returns_wrong_type_redirects_with_authorization_failed():
    stub_client = StubOAuthClient()

    blueprint = _make_oauth_blueprint(
        provider_resolver=_provider_resolver,
        user_resolver=lambda *args, **kwargs: {"principal": "wrong type"},
    )

    blueprint._resolve_oauth_client = classmethod(lambda cls, provider: stub_client).__get__(None, blueprint)

    request = _build_callback_request(blueprint)

    response = blueprint.callback(request)

    location = response.headers["Location"]
    if "error={}".format(ERROR_AUTHORIZATION_FAILED) not in location:
        errmsg = "Expected oauth_authorization_failed, got {!r}".format(location)
        raise AssertionError(errmsg)

    return


# =============================================================================
# Callback — success path with token persister
# =============================================================================


def test_callback_success_invokes_token_persister_and_establishes_session():
    stub_client = StubOAuthClient()
    persisted: List[Dict[str, Any]] = []

    def token_persister(user_id, provider_name, provider_ref_id, token_payload):
        persisted.append({
            "user_id": user_id,
            "provider_name": provider_name,
            "provider_ref_id": provider_ref_id,
            "token_payload": dict(token_payload),
        })

    def user_resolver(provider, user_info, is_register, request):
        principal = Principal(
            identifier="user-100",
            display_name="Test User",
            roles={"customeradmin"},
        )
        return OAuthCallbackResult(
            principal=principal,
            user_id="user-100",
            provider_ref_id=str(user_info.get("sub")),
        )

    blueprint = _make_oauth_blueprint(
        provider_resolver=_provider_resolver,
        user_resolver=user_resolver,
        token_persister=token_persister,
    )

    blueprint._resolve_oauth_client = classmethod(lambda cls, provider: stub_client).__get__(None, blueprint)

    request = _build_callback_request(blueprint)

    response = blueprint.callback(request)

    if response.status_code != 302:
        errmsg = "Expected 302, got {}".format(response.status_code)
        raise AssertionError(errmsg)

    if response.headers["Location"] != "/dashboard/":
        errmsg = "Expected /dashboard/, got {!r}".format(response.headers["Location"])
        raise AssertionError(errmsg)

    cookie_header = _set_cookie_headers(response)
    if "site_session=" not in cookie_header:
        errmsg = "Expected session cookie, got {!r}".format(cookie_header)
        raise AssertionError(errmsg)

    if "Max-Age=0" not in cookie_header:
        errmsg = "Expected state-clear cookie on success too, got {!r}".format(cookie_header)
        raise AssertionError(errmsg)

    if len(persisted) != 1:
        errmsg = "Expected token_persister called once, got {}".format(len(persisted))
        raise AssertionError(errmsg)

    if persisted[0]["user_id"] != "user-100":
        errmsg = "Expected user_id 'user-100', got {!r}".format(persisted[0])
        raise AssertionError(errmsg)

    if persisted[0]["provider_ref_id"] != "subject-1":
        errmsg = "Expected provider_ref_id from sub claim, got {!r}".format(
            persisted[0],
        )
        raise AssertionError(errmsg)

    return


def test_callback_token_persister_failure_is_non_fatal():
    stub_client = StubOAuthClient()

    def raising_persister(*args, **kwargs):
        raise RuntimeError("dbio glitch")

    def user_resolver(provider, user_info, is_register, request):
        return OAuthCallbackResult(
            principal=Principal(identifier="u-1"),
            provider_ref_id="ref-1",
        )

    blueprint = _make_oauth_blueprint(
        provider_resolver=_provider_resolver,
        user_resolver=user_resolver,
        token_persister=raising_persister,
    )

    blueprint._resolve_oauth_client = classmethod(lambda cls, provider: stub_client).__get__(None, blueprint)

    request = _build_callback_request(blueprint)

    response = blueprint.callback(request)

    if response.status_code != 302:
        errmsg = "Expected 302 success even when token_persister fails, got {}".format(
            response.status_code,
        )
        raise AssertionError(errmsg)

    if response.headers["Location"] != "/dashboard/":
        errmsg = "Expected /dashboard/, got {!r}".format(
            response.headers["Location"],
        )
        raise AssertionError(errmsg)

    return


def test_callback_no_user_resolver_redirects_with_not_configured():
    stub_client = StubOAuthClient()

    blueprint = _make_oauth_blueprint(
        provider_resolver=_provider_resolver,
        user_resolver=None,
    )

    blueprint._resolve_oauth_client = classmethod(lambda cls, provider: stub_client).__get__(None, blueprint)

    request = _build_callback_request(blueprint)

    response = blueprint.callback(request)

    location = response.headers["Location"]
    if "error={}".format(ERROR_NOT_CONFIGURED) not in location:
        errmsg = "Expected oauth_not_configured, got {!r}".format(location)
        raise AssertionError(errmsg)

    return


def test_callback_no_session_blueprint_redirects_with_not_configured():
    stub_client = StubOAuthClient()

    blueprint = _make_oauth_blueprint(
        provider_resolver=_provider_resolver,
        user_resolver=lambda *a, **kw: OAuthCallbackResult(
            principal=Principal(identifier="u"),
        ),
    )
    blueprint.session_blueprint = None

    blueprint._resolve_oauth_client = classmethod(lambda cls, provider: stub_client).__get__(None, blueprint)

    request = _build_callback_request(blueprint)

    response = blueprint.callback(request)

    location = response.headers["Location"]
    if "error={}".format(ERROR_NOT_CONFIGURED) not in location:
        errmsg = "Expected oauth_not_configured, got {!r}".format(location)
        raise AssertionError(errmsg)

    return


# =============================================================================
# Endpoint enable / disable
# =============================================================================


def test_kickoff_disabled_returns_404():
    blueprint = _make_oauth_blueprint(
        provider_resolver=_provider_resolver,
    )
    blueprint.enabled_endpoints = set()  # nothing enabled

    request = MockRequest(query_params={"provider": "google"})

    response = blueprint.kickoff(request)

    if response.status_code != 404:
        errmsg = "Expected 404, got {}".format(response.status_code)
        raise AssertionError(errmsg)

    return


def test_register_disabled_returns_404():
    blueprint = _make_oauth_blueprint(
        provider_resolver=_provider_resolver,
        captcha_verifier=lambda token: True,
    )
    blueprint.enabled_endpoints = {"kickoff", "callback"}  # register off

    request = MockRequest(json_body={"captcha_response": "x"})

    response = blueprint.register_intent(request)

    if response.status_code != 404:
        errmsg = "Expected 404, got {}".format(response.status_code)
        raise AssertionError(errmsg)

    return


def test_callback_disabled_returns_404():
    blueprint = _make_oauth_blueprint(
        provider_resolver=_provider_resolver,
    )
    blueprint.enabled_endpoints = {"kickoff", "register"}  # callback off

    request = MockRequest()

    response = blueprint.callback(request)

    if response.status_code != 404:
        errmsg = "Expected 404, got {}".format(response.status_code)
        raise AssertionError(errmsg)

    return


# =============================================================================
# CSRF integration
# =============================================================================


def test_get_csrf_exempt_paths_uses_subclass_base_path():
    blueprint = _make_oauth_blueprint(provider_resolver=_provider_resolver)
    blueprint.base_path = "/oauth"  # legacy URL space

    paths = blueprint.get_csrf_exempt_paths()

    if paths != ["/oauth/register"]:
        errmsg = "Expected ['/oauth/register'], got {!r}".format(paths)
        raise AssertionError(errmsg)

    return


# =============================================================================
# Descriptor registration
# =============================================================================


def test_blueprint_register_returns_three_descriptors():
    blueprint = _make_oauth_blueprint(provider_resolver=_provider_resolver)

    descriptors = blueprint.register()

    paths = sorted([d.path for d in descriptors])
    expected = sorted([
        "/auth/oauth/login",
        "/auth/oauth/register",
        "/auth/oauth/callback",
    ])

    if paths != expected:
        errmsg = "Expected paths {!r}, got {!r}".format(expected, paths)
        raise AssertionError(errmsg)

    return
