"""
    Unit tests for MagicLinkBlueprint.

    This module verifies the MagicLinkBlueprint redemption endpoint
    including defensive token-format validation, success and failure
    redirect paths, session cookie threading, error-code surfacing on
    the failure redirect, and graceful handling of malformed or
    misconfigured collaborators.
"""

import json

from typing import Any, Dict, List, Optional

from ccai.webworks.authentication.blueprints.magiclink import (
    DEFAULT_TOKEN_PATTERN,
    ERROR_CODE_CONSUMED,
    ERROR_CODE_EXPIRED,
    ERROR_CODE_INVALID,
    MagicLinkBlueprint,
    MagicLinkConsumeResult,
)
from ccai.webworks.authentication.blueprints.session import (
    SessionAuthBlueprint,
)
from ccai.webworks.authentication.core import Principal


# =============================================================================
# Test Helpers
# =============================================================================


class MockRequest:
    """
        Minimal request stand-in with a ``path_params`` attribute.

        The redemption handler only ever reads the ``token`` path
        parameter; the other request facets exposed by the real ASGI
        request adapter are not consulted.
    """

    def __init__(self, path_params: Optional[Dict[str, Any]] = None):
        if path_params is None:
            path_params = {}
        self.path_params = path_params


TEST_PRINCIPAL = Principal(
    identifier="user-001",
    display_name="Magic User",
    roles={"customeradmin"},
)


def _create_session_blueprint() -> type:
    """
        Create an isolated :class:`SessionAuthBlueprint` subclass that
        does not interact with any module-level identity provider or
        session store. The subclass is used purely as the target of
        ``establish_session`` calls from the magic-link redemption
        handler.

        :returns: A fresh subclass with default cookie attributes.
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


def _create_magic_blueprint(
    token_consumer=None,
    session_blueprint=None,
) -> type:
    """
        Create an isolated :class:`MagicLinkBlueprint` subclass with the
        given collaborators wired in. Each test gets its own subclass
        so class-level overrides don't leak across cases.

        :param token_consumer: Callable returning a
                               :class:`MagicLinkConsumeResult`.
        :param session_blueprint: Session blueprint to use for
                                  ``establish_session`` calls. When
                                  ``None``, a fresh blueprint is
                                  created.

        :returns: A fresh :class:`MagicLinkBlueprint` subclass.
    """

    if session_blueprint is None:
        session_blueprint = _create_session_blueprint()

    class FreshMagic(MagicLinkBlueprint):
        pass

    FreshMagic.token_consumer = staticmethod(token_consumer) if token_consumer else None
    FreshMagic.session_blueprint = session_blueprint
    FreshMagic.post_redemption_redirect_url = "/set-password"
    FreshMagic.error_redirect_url = "/login"
    FreshMagic.scheme_label = "MagicLink"
    FreshMagic.success_message = "Welcome — your link has been redeemed"
    FreshMagic.token_pattern = DEFAULT_TOKEN_PATTERN
    FreshMagic.enabled_endpoints = None
    FreshMagic.auth_system = None
    FreshMagic.base_path = "/auth/magic"

    rtnval = FreshMagic
    return rtnval


# =============================================================================
# Success Path
# =============================================================================


def test_redeem_success_returns_redirect_with_cookie():
    """
        A valid token consumed successfully must produce a 302 redirect
        to ``post_redemption_redirect_url`` with the session cookie
        attached.
    """

    def consumer(token: str) -> MagicLinkConsumeResult:
        return MagicLinkConsumeResult(
            principal=TEST_PRINCIPAL,
            token_id="tok-42",
        )

    blueprint = _create_magic_blueprint(token_consumer=consumer)

    request = MockRequest(path_params={"token": "abcdef0123456789"})

    response = blueprint.redeem(request)

    if response.status_code != 302:
        errmsg = "Expected status 302, got {}".format(response.status_code)
        raise AssertionError(errmsg)

    headers = response.headers

    location = headers.get("Location")
    if location != "/set-password":
        errmsg = "Expected Location /set-password, got {!r}".format(location)
        raise AssertionError(errmsg)

    cookie = headers.get("Set-Cookie")
    if cookie is None:
        errmsg = "Expected Set-Cookie header on success redirect"
        raise AssertionError(errmsg)

    if "site_session=" not in cookie:
        errmsg = "Expected session cookie marker in Set-Cookie header, got {!r}".format(
            cookie
        )
        raise AssertionError(errmsg)

    return


def test_redeem_success_records_token_id_attribute():
    """
        The blueprint must thread the consumer's ``token_id`` value
        into ``establish_session.extra_attributes`` as ``"token_id"``.
    """

    captured: List[Dict[str, Any]] = []

    session_blueprint = _create_session_blueprint()
    original_establish = session_blueprint.establish_session.__func__

    def capturing_establish(
        cls,
        principal,
        request=None,
        remember_me=False,
        scheme="Session",
        success_message="Session established",
        extra_attributes=None,
    ):
        captured.append({
            "principal": principal,
            "scheme": scheme,
            "extra_attributes": dict(extra_attributes or {}),
        })
        rtnval = original_establish(
            cls,
            principal,
            request=request,
            remember_me=remember_me,
            scheme=scheme,
            success_message=success_message,
            extra_attributes=extra_attributes,
        )
        return rtnval

    session_blueprint.establish_session = classmethod(capturing_establish)

    def consumer(token: str) -> MagicLinkConsumeResult:
        return MagicLinkConsumeResult(
            principal=TEST_PRINCIPAL,
            token_id="tok-77",
            extra_attributes={"channel": "welcome-email"},
        )

    blueprint = _create_magic_blueprint(
        token_consumer=consumer,
        session_blueprint=session_blueprint,
    )

    request = MockRequest(path_params={"token": "validtokenpayload"})

    response = blueprint.redeem(request)

    if response.status_code != 302:
        errmsg = "Expected status 302, got {}".format(response.status_code)
        raise AssertionError(errmsg)

    if len(captured) != 1:
        errmsg = "Expected exactly one establish_session call, got {}".format(
            len(captured)
        )
        raise AssertionError(errmsg)

    call = captured[0]

    if call["scheme"] != "MagicLink":
        errmsg = "Expected scheme 'MagicLink', got {!r}".format(call["scheme"])
        raise AssertionError(errmsg)

    extras = call["extra_attributes"]

    if extras.get("token_id") != "tok-77":
        errmsg = "Expected token_id 'tok-77' in extra_attributes, got {!r}".format(
            extras.get("token_id")
        )
        raise AssertionError(errmsg)

    if extras.get("channel") != "welcome-email":
        errmsg = "Expected channel 'welcome-email' in extra_attributes, got {!r}".format(
            extras.get("channel")
        )
        raise AssertionError(errmsg)

    return


# =============================================================================
# Failure Paths
# =============================================================================


def test_redeem_missing_token_redirects_with_invalid_error():
    """
        A request with no ``token`` path parameter must redirect to the
        error URL with ``?error=magic_link_invalid``.
    """

    def consumer(token: str) -> MagicLinkConsumeResult:
        errmsg = "Consumer must not be called when token is missing"
        raise AssertionError(errmsg)

    blueprint = _create_magic_blueprint(token_consumer=consumer)

    request = MockRequest(path_params={})

    response = blueprint.redeem(request)

    if response.status_code != 302:
        errmsg = "Expected status 302, got {}".format(response.status_code)
        raise AssertionError(errmsg)

    location = response.headers.get("Location", "")
    if "/login?error=magic_link_invalid" not in location:
        errmsg = "Expected error redirect, got Location {!r}".format(location)
        raise AssertionError(errmsg)

    return


def test_redeem_malformed_token_redirects_with_invalid_error():
    """
        A token that fails the format regex must short-circuit before
        the consumer is called.
    """

    def consumer(token: str) -> MagicLinkConsumeResult:
        errmsg = "Consumer must not be called for malformed tokens"
        raise AssertionError(errmsg)

    blueprint = _create_magic_blueprint(token_consumer=consumer)

    # Token contains characters outside [A-Za-z0-9_-].
    request = MockRequest(path_params={"token": "no spaces allowed!"})

    response = blueprint.redeem(request)

    if response.status_code != 302:
        errmsg = "Expected status 302, got {}".format(response.status_code)
        raise AssertionError(errmsg)

    location = response.headers.get("Location", "")
    if "error=magic_link_invalid" not in location:
        errmsg = "Expected magic_link_invalid in Location, got {!r}".format(location)
        raise AssertionError(errmsg)

    return


def test_redeem_consumer_returns_expired_error():
    """
        When the consumer returns ``error_code='magic_link_expired'``,
        the blueprint must redirect with that exact error code.
    """

    def consumer(token: str) -> MagicLinkConsumeResult:
        return MagicLinkConsumeResult(error_code=ERROR_CODE_EXPIRED)

    blueprint = _create_magic_blueprint(token_consumer=consumer)

    request = MockRequest(path_params={"token": "validlookingtoken123"})

    response = blueprint.redeem(request)

    if response.status_code != 302:
        errmsg = "Expected status 302, got {}".format(response.status_code)
        raise AssertionError(errmsg)

    location = response.headers.get("Location", "")
    if "error=magic_link_expired" not in location:
        errmsg = "Expected magic_link_expired in Location, got {!r}".format(location)
        raise AssertionError(errmsg)

    if "Set-Cookie" in response.headers:
        errmsg = "Failure redirect must not carry a Set-Cookie header"
        raise AssertionError(errmsg)

    return


def test_redeem_consumer_returns_consumed_error():
    """
        Single-use semantics — replays surface as ``magic_link_consumed``
        on the redirect.
    """

    def consumer(token: str) -> MagicLinkConsumeResult:
        return MagicLinkConsumeResult(error_code=ERROR_CODE_CONSUMED)

    blueprint = _create_magic_blueprint(token_consumer=consumer)

    request = MockRequest(path_params={"token": "alreadyusedtoken1234"})

    response = blueprint.redeem(request)

    location = response.headers.get("Location", "")
    if "error=magic_link_consumed" not in location:
        errmsg = "Expected magic_link_consumed in Location, got {!r}".format(location)
        raise AssertionError(errmsg)

    return


def test_redeem_consumer_raises_redirects_with_internal_error():
    """
        Unexpected exceptions in the consumer must not leak — the user
        lands on the generic ``magic_link_failed`` page.
    """

    def consumer(token: str) -> MagicLinkConsumeResult:
        raise RuntimeError("dbio blew up")

    blueprint = _create_magic_blueprint(token_consumer=consumer)

    request = MockRequest(path_params={"token": "validtokenpayload"})

    response = blueprint.redeem(request)

    location = response.headers.get("Location", "")
    if "error=magic_link_failed" not in location:
        errmsg = "Expected magic_link_failed in Location, got {!r}".format(location)
        raise AssertionError(errmsg)

    return


def test_redeem_consumer_returns_wrong_type_redirects_with_internal_error():
    """
        A consumer that returns something other than a
        :class:`MagicLinkConsumeResult` is treated as a programming bug
        — the blueprint redirects with ``magic_link_failed`` rather than
        crashing.
    """

    def consumer(token: str) -> Any:
        return {"principal": TEST_PRINCIPAL}

    blueprint = _create_magic_blueprint(token_consumer=consumer)

    request = MockRequest(path_params={"token": "validtokenpayload"})

    response = blueprint.redeem(request)

    location = response.headers.get("Location", "")
    if "error=magic_link_failed" not in location:
        errmsg = "Expected magic_link_failed in Location, got {!r}".format(location)
        raise AssertionError(errmsg)

    return


def test_redeem_consumer_returns_no_principal_and_no_error():
    """
        A consumer that returns an empty result (no principal, no
        error_code) is a programming bug; surface it as
        ``magic_link_failed`` so the user is not silently logged in.
    """

    def consumer(token: str) -> MagicLinkConsumeResult:
        return MagicLinkConsumeResult()

    blueprint = _create_magic_blueprint(token_consumer=consumer)

    request = MockRequest(path_params={"token": "validtokenpayload"})

    response = blueprint.redeem(request)

    location = response.headers.get("Location", "")
    if "error=magic_link_failed" not in location:
        errmsg = "Expected magic_link_failed in Location, got {!r}".format(location)
        raise AssertionError(errmsg)

    return


# =============================================================================
# Configuration Failure Paths
# =============================================================================


def test_redeem_without_token_consumer_redirects_with_internal_error():
    """
        A blueprint with no ``token_consumer`` configured must not
        process the request — it redirects with ``magic_link_failed``.
    """

    blueprint = _create_magic_blueprint(token_consumer=None)

    request = MockRequest(path_params={"token": "validtokenpayload"})

    response = blueprint.redeem(request)

    location = response.headers.get("Location", "")
    if "error=magic_link_failed" not in location:
        errmsg = "Expected magic_link_failed in Location, got {!r}".format(location)
        raise AssertionError(errmsg)

    return


def test_redeem_without_session_blueprint_redirects_with_internal_error():
    """
        A blueprint with no ``session_blueprint`` configured cannot
        issue a session — it redirects with ``magic_link_failed``.
    """

    def consumer(token: str) -> MagicLinkConsumeResult:
        return MagicLinkConsumeResult(principal=TEST_PRINCIPAL)

    blueprint = _create_magic_blueprint(token_consumer=consumer)
    blueprint.session_blueprint = None

    request = MockRequest(path_params={"token": "validtokenpayload"})

    response = blueprint.redeem(request)

    location = response.headers.get("Location", "")
    if "error=magic_link_failed" not in location:
        errmsg = "Expected magic_link_failed in Location, got {!r}".format(location)
        raise AssertionError(errmsg)

    return


def test_redeem_disabled_endpoint_returns_404():
    """
        When the ``redeem`` endpoint is disabled the blueprint must
        return a 404 rather than processing the token.
    """

    def consumer(token: str) -> MagicLinkConsumeResult:
        errmsg = "Consumer must not be called when endpoint is disabled"
        raise AssertionError(errmsg)

    blueprint = _create_magic_blueprint(token_consumer=consumer)
    blueprint.enabled_endpoints = set()

    request = MockRequest(path_params={"token": "validtokenpayload"})

    response = blueprint.redeem(request)

    if response.status_code != 404:
        errmsg = "Expected status 404, got {}".format(response.status_code)
        raise AssertionError(errmsg)

    return


# =============================================================================
# Pre-authenticate hook
# =============================================================================


def test_pre_authenticate_hook_can_short_circuit_redemption():
    """
        Subclasses that override ``pre_authenticate`` must be able to
        short-circuit the redemption flow with an :class:`AuthError`.
    """

    from ccai.webworks.authentication.blueprints.responses import AuthError

    def consumer(token: str) -> MagicLinkConsumeResult:
        errmsg = "Consumer must not be called when pre_authenticate aborts"
        raise AssertionError(errmsg)

    blueprint = _create_magic_blueprint(token_consumer=consumer)

    def aborting_pre_authenticate(cls, request):
        return AuthError(
            error="rate_limited",
            error_description="Too many redemption attempts"
        )

    blueprint.pre_authenticate = classmethod(aborting_pre_authenticate)

    request = MockRequest(path_params={"token": "validtokenpayload"})

    response = blueprint.redeem(request)

    if response.status_code != 401:
        errmsg = "Expected status 401, got {}".format(response.status_code)
        raise AssertionError(errmsg)

    body = json.loads(response.body)
    if body.get("error") != "rate_limited":
        errmsg = "Expected rate_limited error, got {!r}".format(body.get("error"))
        raise AssertionError(errmsg)

    return


# =============================================================================
# Path-param extraction
# =============================================================================


def test_redeem_handles_dict_style_request():
    """
        The handler must also accept request objects that surface
        ``path_params`` via mapping-style access (``request['path_params']``).
    """

    def consumer(token: str) -> MagicLinkConsumeResult:
        return MagicLinkConsumeResult(principal=TEST_PRINCIPAL)

    blueprint = _create_magic_blueprint(token_consumer=consumer)

    dict_request = {"path_params": {"token": "validtokenpayload"}}

    response = blueprint.redeem(dict_request)

    if response.status_code != 302:
        errmsg = "Expected status 302, got {}".format(response.status_code)
        raise AssertionError(errmsg)

    location = response.headers.get("Location")
    if location != "/set-password":
        errmsg = "Expected /set-password, got {!r}".format(location)
        raise AssertionError(errmsg)

    return


# =============================================================================
# Error redirect URL with existing query string
# =============================================================================


def test_error_redirect_appends_to_existing_query_string():
    """
        When ``error_redirect_url`` already carries a query string the
        ``error=`` parameter must be joined with ``&`` rather than
        ``?``.
    """

    def consumer(token: str) -> MagicLinkConsumeResult:
        return MagicLinkConsumeResult(error_code=ERROR_CODE_INVALID)

    blueprint = _create_magic_blueprint(token_consumer=consumer)
    blueprint.error_redirect_url = "/login?source=email"

    request = MockRequest(path_params={"token": "validtokenpayload"})

    response = blueprint.redeem(request)

    location = response.headers.get("Location", "")
    expected = "/login?source=email&error=magic_link_invalid"
    if location != expected:
        errmsg = "Expected Location {!r}, got {!r}".format(expected, location)
        raise AssertionError(errmsg)

    return


# =============================================================================
# Custom paths
# =============================================================================


# =============================================================================
# Issuance helpers
# =============================================================================


def test_issue_magic_link_invokes_issuer_and_returns_plaintext_plus_record():
    """
        Happy path: ``issue_magic_link`` generates a fresh plaintext,
        calls the site-supplied ``token_issuer`` with
        ``(plaintext, user_id, extra)``, and returns
        ``(plaintext, persisted_record)``.
    """
    captured: List[Dict[str, Any]] = []

    def issuer(plaintext, user_id, extra):
        captured.append({
            "plaintext": plaintext,
            "user_id": user_id,
            "extra": extra,
        })
        return {"id": "row-42", "user_id": user_id}

    blueprint = _create_magic_blueprint(token_consumer=lambda t: None)
    blueprint.token_issuer = staticmethod(issuer)

    plaintext, record = blueprint.issue_magic_link(
        user_id="user-100",
        extra={"channel": "welcome-email"},
    )

    if not isinstance(plaintext, str) or len(plaintext) < 32:
        errmsg = "Expected URL-safe-base64 plaintext, got {!r}".format(plaintext)
        raise AssertionError(errmsg)

    if record != {"id": "row-42", "user_id": "user-100"}:
        errmsg = "Expected persisted record to round-trip, got {!r}".format(record)
        raise AssertionError(errmsg)

    if len(captured) != 1:
        errmsg = "Expected token_issuer called exactly once, got {}".format(
            len(captured),
        )
        raise AssertionError(errmsg)

    call = captured[0]
    if call["plaintext"] != plaintext:
        errmsg = "Issuer received different plaintext than caller, got {!r}".format(
            call,
        )
        raise AssertionError(errmsg)

    if call["user_id"] != "user-100":
        errmsg = "Expected user_id 'user-100', got {!r}".format(call)
        raise AssertionError(errmsg)

    if call["extra"] != {"channel": "welcome-email"}:
        errmsg = "Expected extra forwarded, got {!r}".format(call)
        raise AssertionError(errmsg)

    return


def test_issue_magic_link_generates_token_matching_default_pattern():
    """
        The plaintext token issued by the helper must pass the
        defensive format check that ``redeem`` runs on inbound
        tokens; otherwise tokens issued via the helper would fail
        their own redemption.
    """
    blueprint = _create_magic_blueprint(token_consumer=lambda t: None)
    blueprint.token_issuer = staticmethod(lambda p, u, e: None)

    for _ in range(20):
        plaintext, _ = blueprint.issue_magic_link(user_id="u-1")
        if blueprint.token_pattern.match(plaintext) is None:
            errmsg = "Issued token {!r} fails format check".format(plaintext)
            raise AssertionError(errmsg)

    return


def test_issue_magic_link_generates_distinct_tokens_per_call():
    blueprint = _create_magic_blueprint(token_consumer=lambda t: None)
    blueprint.token_issuer = staticmethod(lambda p, u, e: None)

    samples = set()
    for _ in range(20):
        plaintext, _ = blueprint.issue_magic_link(user_id="u-1")
        samples.add(plaintext)

    if len(samples) != 20:
        errmsg = "Expected 20 distinct plaintexts, got {}".format(len(samples))
        raise AssertionError(errmsg)

    return


def test_issue_magic_link_raises_when_no_issuer_configured():
    blueprint = _create_magic_blueprint(token_consumer=lambda t: None)
    blueprint.token_issuer = None

    raised = False
    try:
        blueprint.issue_magic_link(user_id="u-1")
    except RuntimeError:
        raised = True

    if not raised:
        errmsg = "Expected RuntimeError when token_issuer is missing"
        raise AssertionError(errmsg)

    return


def test_issue_magic_link_coerces_user_id_to_string():
    captured: List[str] = []

    def issuer(plaintext, user_id, extra):
        captured.append(user_id)
        return None

    blueprint = _create_magic_blueprint(token_consumer=lambda t: None)
    blueprint.token_issuer = staticmethod(issuer)

    blueprint.issue_magic_link(user_id=12345)

    if captured != ["12345"]:
        errmsg = "Expected stringified user_id '12345', got {!r}".format(captured)
        raise AssertionError(errmsg)

    return


def test_issue_magic_link_extra_defaults_to_empty_dict():
    captured: List[Any] = []

    def issuer(plaintext, user_id, extra):
        captured.append(extra)
        return None

    blueprint = _create_magic_blueprint(token_consumer=lambda t: None)
    blueprint.token_issuer = staticmethod(issuer)

    blueprint.issue_magic_link(user_id="u-1")

    if captured != [{}]:
        errmsg = "Expected extra to default to {{}}, got {!r}".format(captured)
        raise AssertionError(errmsg)

    return


def test_build_magic_link_url_uses_subclass_base_path():
    blueprint = _create_magic_blueprint(token_consumer=lambda t: None)
    blueprint.base_path = "/login/magic"

    url = blueprint.build_magic_link_url(
        plaintext_token="abcdef0123456789",
        base_url="https://app.example.com",
    )

    expected = "https://app.example.com/login/magic/abcdef0123456789"
    if url != expected:
        errmsg = "Expected {!r}, got {!r}".format(expected, url)
        raise AssertionError(errmsg)

    return


def test_build_magic_link_url_tolerates_trailing_slash_on_base():
    blueprint = _create_magic_blueprint(token_consumer=lambda t: None)
    blueprint.base_path = "/auth/magic"

    url = blueprint.build_magic_link_url(
        plaintext_token="tok",
        base_url="https://app.example.com/",
    )

    if url != "https://app.example.com/auth/magic/tok":
        errmsg = "Trailing slash on base_url not stripped, got {!r}".format(url)
        raise AssertionError(errmsg)

    return


def test_issue_and_build_magic_link_round_trip_format_check():
    """
        End-to-end: issuance produces a token that passes the
        consume-side format check baked into ``redeem`` — meaning a
        token minted via ``issue_magic_link`` won't trip the
        defensive ``token_pattern`` regex when it comes back through
        the redemption endpoint.
    """
    blueprint = _create_magic_blueprint(token_consumer=lambda t: None)
    blueprint.token_issuer = staticmethod(lambda p, u, e: None)

    plaintext, _ = blueprint.issue_magic_link(user_id="u-1")
    url = blueprint.build_magic_link_url(
        plaintext_token=plaintext,
        base_url="https://app.example.com",
    )

    # Extract the token segment back out of the URL and confirm
    # the round-trip pattern still matches.
    suffix = url.rsplit("/", 1)[-1]
    if suffix != plaintext:
        errmsg = "URL suffix {!r} != plaintext {!r}".format(suffix, plaintext)
        raise AssertionError(errmsg)

    if blueprint.token_pattern.match(suffix) is None:
        errmsg = "Round-trip token failed format check: {!r}".format(suffix)
        raise AssertionError(errmsg)

    return


# =============================================================================
# Descriptor registration
# =============================================================================


def test_blueprint_register_resolves_token_path_against_base():
    """
        The redeem handler is registered at ``{base_path}/{token}``;
        the descriptor produced by ``register`` must reflect the
        subclass's overridden ``base_path``.
    """

    blueprint = _create_magic_blueprint(token_consumer=lambda t: MagicLinkConsumeResult(principal=TEST_PRINCIPAL))
    blueprint.base_path = "/login/magic"

    descriptors = blueprint.register()

    if len(descriptors) != 1:
        errmsg = "Expected exactly one descriptor, got {}".format(len(descriptors))
        raise AssertionError(errmsg)

    descriptor = descriptors[0]

    if descriptor.path != "/login/magic/{token}":
        errmsg = "Expected path /login/magic/{{token}}, got {!r}".format(descriptor.path)
        raise AssertionError(errmsg)

    if descriptor.methods != ["GET"]:
        errmsg = "Expected methods ['GET'], got {!r}".format(descriptor.methods)
        raise AssertionError(errmsg)

    return
