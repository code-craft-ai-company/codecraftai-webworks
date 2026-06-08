"""
    End-to-end dispatcher integration tests for the auth blueprints
    that mount endpoints (``MagicLinkBlueprint``,
    ``OAuthClientBlueprint``).

    Regression coverage for the bug discovered while preparing site
    OAuth migration: handlers that returned dict-shape responses
    survived ``cls.method(request)`` unit tests but blew up at
    request-dispatch time because :class:`Dispatcher` wraps any
    non-:class:`Response` return in ``JSONResponse(content=...)``.
    The fix forces these handlers to return :class:`Response`
    objects directly. A second part of the same fix routes through
    ``getattr(cls, attr_name)`` so that classmethod descriptors are
    bound (the dispatcher would otherwise call the underlying
    function with ``(request,)`` and fail because the implicit
    ``cls`` arg is missing).

    These tests run a real request through ``Dispatcher.dispatch``
    against a real ``Router`` populated by ``register()`` — the
    exact path that the production site goes through. They lock in
    the contract by asserting on the actual HTTP response shape
    (``status_code``, ``Location``, ``Set-Cookie``) rather than the
    handler's return value.
"""

import json

from typing import Any, Dict

from ccai.webworks.authentication.blueprints.magiclink import (
    MagicLinkBlueprint,
    MagicLinkConsumeResult,
)
from ccai.webworks.authentication.blueprints.oauthclient import (
    OAuthCallbackResult,
    OAuthClientBlueprint,
)
from ccai.webworks.authentication.blueprints.session import (
    SessionAuthBlueprint,
)
from ccai.webworks.authentication.core import Principal
from ccai.webworks.routing.dispatcher import Dispatcher
from ccai.webworks.routing.middleware import MiddlewarePipeline
from ccai.webworks.routing.response import Response
from ccai.webworks.routing.router import Router


# =============================================================================
# Helpers
# =============================================================================


def _make_session_blueprint() -> type:
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


class _MockRequest:
    """
        Minimal request stub with the four facets the auth blueprints
        consult (``method``, ``path``, ``headers``, ``query_params``,
        ``cookies``, ``scheme``, ``host``).
    """

    def __init__(
        self,
        *,
        method: str = "GET",
        path: str = "/",
        query_params: Dict[str, Any] = None,
        cookies: Dict[str, str] = None,
        json_body: Any = None,
    ):
        self.method = method
        self.path = path
        self.headers: Dict[str, str] = {}
        self.path_params: Dict[str, Any] = {}
        self.query_params = query_params or {}
        self.cookies = cookies or {}
        self.scheme = "https"
        self.host = "app.example.com"
        self._json_body = json_body

    def json(self):
        if self._json_body is None:
            errmsg = "no body"
            raise ValueError(errmsg)
        return self._json_body

    def form(self):
        return None


def _build_dispatcher_for_blueprint(blueprint_cls) -> Dispatcher:
    router = Router()
    for descriptor in blueprint_cls.register():
        router.add_endpoint(descriptor)
    rtnval = Dispatcher(router=router, pipeline=MiddlewarePipeline())
    return rtnval


# =============================================================================
# MagicLinkBlueprint
# =============================================================================


def test_magiclink_redeem_dispatch_returns_real_302_with_cookie():
    class FreshMagic(MagicLinkBlueprint):
        pass

    FreshMagic.token_consumer = staticmethod(
        lambda token: MagicLinkConsumeResult(
            principal=Principal(identifier="user-1"),
        )
    )
    FreshMagic.session_blueprint = _make_session_blueprint()
    FreshMagic.enabled_endpoints = None
    FreshMagic.auth_system = None
    FreshMagic.base_path = "/login/magic"

    dispatcher = _build_dispatcher_for_blueprint(FreshMagic)

    request = _MockRequest(
        method="GET",
        path="/login/magic/abcdefghijklmnop",
    )

    response = dispatcher.dispatch(request)

    if not isinstance(response, Response):
        errmsg = "Expected Response, got {!r}".format(type(response).__name__)
        raise AssertionError(errmsg)

    if response.status_code != 302:
        errmsg = (
            "Expected 302 redirect, got {} (dispatcher likely "
            "JSON-wrapped a dict-shape return)".format(
                response.status_code,
            )
        )
        raise AssertionError(errmsg)

    location = response.headers.get("Location")
    if location != "/set-password":
        errmsg = "Expected Location /set-password, got {!r}".format(location)
        raise AssertionError(errmsg)

    cookie = response.headers.get("Set-Cookie", "")
    if "site_session=" not in cookie:
        errmsg = "Expected session cookie on success redirect, got {!r}".format(cookie)
        raise AssertionError(errmsg)

    return


def test_magiclink_redeem_dispatch_invalid_token_returns_real_302_to_error():
    class FreshMagic(MagicLinkBlueprint):
        pass

    FreshMagic.token_consumer = staticmethod(
        lambda token: MagicLinkConsumeResult(error_code="magic_link_invalid")
    )
    FreshMagic.session_blueprint = _make_session_blueprint()
    FreshMagic.enabled_endpoints = None
    FreshMagic.auth_system = None
    FreshMagic.base_path = "/login/magic"

    dispatcher = _build_dispatcher_for_blueprint(FreshMagic)

    request = _MockRequest(
        method="GET",
        path="/login/magic/abcdefghijklmnop",
    )

    response = dispatcher.dispatch(request)

    if response.status_code != 302:
        errmsg = "Expected 302 redirect, got {}".format(response.status_code)
        raise AssertionError(errmsg)

    location = response.headers.get("Location", "")
    if "error=magic_link_invalid" not in location:
        errmsg = "Expected magic_link_invalid in Location, got {!r}".format(location)
        raise AssertionError(errmsg)

    return


def test_magiclink_redeem_dispatch_disabled_endpoint_returns_real_404():
    class FreshMagic(MagicLinkBlueprint):
        pass

    FreshMagic.token_consumer = staticmethod(
        lambda token: MagicLinkConsumeResult(
            principal=Principal(identifier="u-1"),
        )
    )
    FreshMagic.session_blueprint = _make_session_blueprint()
    FreshMagic.enabled_endpoints = set()  # nothing enabled
    FreshMagic.auth_system = None
    FreshMagic.base_path = "/login/magic"

    dispatcher = _build_dispatcher_for_blueprint(FreshMagic)

    request = _MockRequest(
        method="GET",
        path="/login/magic/abcdefghijklmnop",
    )

    response = dispatcher.dispatch(request)

    if response.status_code != 404:
        errmsg = "Expected 404 for disabled endpoint, got {}".format(
            response.status_code,
        )
        raise AssertionError(errmsg)

    body = json.loads(response.body)
    if body.get("error") != "endpoint_disabled":
        errmsg = "Expected endpoint_disabled error, got {!r}".format(body)
        raise AssertionError(errmsg)

    return


# =============================================================================
# OAuthClientBlueprint
# =============================================================================


def _make_oauth_blueprint(
    *,
    user_resolver=None,
    provider_resolver=None,
    provider_name_lister=None,
    captcha_verifier=None,
) -> type:
    class FreshOAuth(OAuthClientBlueprint):
        pass

    FreshOAuth.provider_resolver = (
        staticmethod(provider_resolver)
        if provider_resolver is not None
        else staticmethod(lambda name: None)
    )
    FreshOAuth.provider_name_lister = (
        staticmethod(provider_name_lister)
        if provider_name_lister is not None
        else staticmethod(lambda: [])
    )
    FreshOAuth.user_resolver = (
        staticmethod(user_resolver)
        if user_resolver is not None
        else staticmethod(lambda *a, **kw: OAuthCallbackResult())
    )
    FreshOAuth.captcha_verifier = (
        staticmethod(captcha_verifier) if captcha_verifier is not None else None
    )
    FreshOAuth.state_cookie_secret_resolver = staticmethod(
        lambda: "test-secret"
    )
    FreshOAuth.session_blueprint = _make_session_blueprint()
    FreshOAuth.enabled_endpoints = None
    FreshOAuth.auth_system = None
    FreshOAuth.base_path = "/auth/oauth"

    rtnval = FreshOAuth
    return rtnval


def test_oauth_kickoff_dispatch_unavailable_returns_real_302_to_error():
    blueprint = _make_oauth_blueprint()  # default provider_resolver returns None
    dispatcher = _build_dispatcher_for_blueprint(blueprint)

    request = _MockRequest(
        method="GET",
        path="/auth/oauth/login",
        query_params={"provider": "google"},
    )

    response = dispatcher.dispatch(request)

    if response.status_code != 302:
        errmsg = "Expected 302, got {}".format(response.status_code)
        raise AssertionError(errmsg)

    location = response.headers.get("Location", "")
    if "error=oauth_provider_unavailable" not in location:
        errmsg = (
            "Expected oauth_provider_unavailable in Location, got {!r}".format(
                location,
            )
        )
        raise AssertionError(errmsg)

    return


def test_oauth_register_intent_dispatch_returns_real_400_json_on_missing_captcha():
    blueprint = _make_oauth_blueprint(captcha_verifier=lambda token: True)
    dispatcher = _build_dispatcher_for_blueprint(blueprint)

    request = _MockRequest(
        method="POST",
        path="/auth/oauth/register",
        json_body={"provider": "google"},  # no captcha_response
    )

    response = dispatcher.dispatch(request)

    if response.status_code != 400:
        errmsg = "Expected 400, got {}".format(response.status_code)
        raise AssertionError(errmsg)

    content_type = response.headers.get("Content-Type", "")
    if "application/json" not in content_type:
        errmsg = "Expected JSON Content-Type, got {!r}".format(content_type)
        raise AssertionError(errmsg)

    body = json.loads(response.body)
    if body.get("error") != "missing_captcha":
        errmsg = "Expected missing_captcha, got {!r}".format(body)
        raise AssertionError(errmsg)

    return


def test_oauth_register_intent_dispatch_returns_real_200_on_success():
    blueprint = _make_oauth_blueprint(captcha_verifier=lambda token: True)
    dispatcher = _build_dispatcher_for_blueprint(blueprint)

    request = _MockRequest(
        method="POST",
        path="/auth/oauth/register",
        json_body={
            "provider": "google",
            "captcha_response": "verified-token",
        },
    )

    response = dispatcher.dispatch(request)

    if response.status_code != 200:
        errmsg = "Expected 200, got {}".format(response.status_code)
        raise AssertionError(errmsg)

    body = json.loads(response.body)
    if body.get("success") is not True:
        errmsg = "Expected success=true, got {!r}".format(body)
        raise AssertionError(errmsg)

    redirect_url = body.get("redirect_url", "")
    if "/auth/oauth/login" not in redirect_url:
        errmsg = "Expected /auth/oauth/login in redirect_url, got {!r}".format(
            redirect_url,
        )
        raise AssertionError(errmsg)

    return


def test_oauth_callback_dispatch_returns_real_302_to_error_on_missing_provider():
    blueprint = _make_oauth_blueprint()
    dispatcher = _build_dispatcher_for_blueprint(blueprint)

    request = _MockRequest(
        method="GET",
        path="/auth/oauth/callback",
        query_params={"state": "x", "code": "y"},  # no provider
    )

    response = dispatcher.dispatch(request)

    if response.status_code != 302:
        errmsg = "Expected 302, got {}".format(response.status_code)
        raise AssertionError(errmsg)

    location = response.headers.get("Location", "")
    if "error=provider_missing_callback" not in location:
        errmsg = (
            "Expected provider_missing_callback in Location, got {!r}".format(
                location,
            )
        )
        raise AssertionError(errmsg)

    # State-clear cookie should be attached on every callback exit
    # path, including this one.
    cookie = response.headers.get("Set-Cookie", "")
    if "Max-Age=0" not in cookie:
        errmsg = "Expected state-clear cookie on error redirect, got {!r}".format(
            cookie,
        )
        raise AssertionError(errmsg)

    return


def test_oauth_kickoff_dispatch_disabled_endpoint_returns_real_404():
    blueprint = _make_oauth_blueprint()
    blueprint.enabled_endpoints = set()  # disable kickoff
    dispatcher = _build_dispatcher_for_blueprint(blueprint)

    request = _MockRequest(
        method="GET",
        path="/auth/oauth/login",
        query_params={"provider": "google"},
    )

    response = dispatcher.dispatch(request)

    if response.status_code != 404:
        errmsg = "Expected 404 for disabled endpoint, got {}".format(
            response.status_code,
        )
        raise AssertionError(errmsg)

    body = json.loads(response.body)
    if body.get("error") != "endpoint_disabled":
        errmsg = "Expected endpoint_disabled, got {!r}".format(body)
        raise AssertionError(errmsg)

    return
