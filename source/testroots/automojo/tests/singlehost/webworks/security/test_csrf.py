"""
    Unit tests for the CSRF protection module.

    Covers:
        - CSRFTokenManager generation/validation invariants.
        - The cookie_session_id_resolver helper.
        - CSRFMiddleware enforcement on unsafe methods, with safe-method
          and exempt-path bypass paths.
        - The make_csrf_context_processor factory used for templating
          integration.
"""

import asyncio
import json

from typing import Any, Callable, Dict, List, Optional

from automojo.webworks.security.csrf import (
    CSRFError,
    CSRFMiddleware,
    CSRFTokenManager,
    cookie_session_id_resolver,
    make_csrf_context_processor,
)


# =============================================================================
# Test Helpers
# =============================================================================

SECRET_KEY = "unit-test-secret-key"
SESSION_ID = "session-abc-123"
OTHER_SESSION_ID = "session-xyz-789"


class MockASGIApp:
    """
        Captures whether it was invoked and what scope it received.
    """

    def __init__(self):
        self._called = False
        self._scope: Optional[Dict[str, Any]] = None

    async def __call__(
        self,
        scope: Dict[str, Any],
        receive: Callable,
        send: Callable
    ) -> None:
        self._called = True
        self._scope = scope
        return

    @property
    def was_called(self) -> bool:
        return self._called

    @property
    def captured_scope(self) -> Optional[Dict[str, Any]]:
        return self._scope


class MockSend:
    """
        Captures messages sent through the ASGI ``send`` callable.
    """

    def __init__(self):
        self._messages: List[Dict[str, Any]] = []

    async def __call__(self, message: Dict[str, Any]) -> None:
        self._messages.append(message)
        return

    @property
    def messages(self) -> List[Dict[str, Any]]:
        return self._messages


class MockReceive:
    """
        Returns an empty body. Sufficient for the header-based path.
    """

    async def __call__(self) -> Dict[str, Any]:
        return {"type": "http.request", "body": b"", "more_body": False}


def run_async(coro):
    """
        Drive a coroutine to completion on a fresh event loop.
    """
    loop = asyncio.new_event_loop()
    try:
        result = loop.run_until_complete(coro)
        return result
    finally:
        loop.close()


def create_http_scope(
    method: str = "POST",
    path: str = "/api/post",
    headers: Optional[List[tuple]] = None
) -> Dict[str, Any]:
    """
        Build a minimal ASGI HTTP scope for middleware tests.
    """
    if headers is None:
        headers = []

    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": method,
        "scheme": "http",
        "path": path,
        "query_string": b"",
        "root_path": "",
        "headers": headers,
        "server": ("localhost", 8000),
    }
    return scope


def _decode_json_body(messages: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
        Reassemble the JSON body from captured ASGI response messages.
    """
    body_chunks = []
    for message in messages:
        if message.get("type") == "http.response.body":
            chunk = message.get("body", b"") or b""
            body_chunks.append(chunk)

    raw = b"".join(body_chunks)
    if len(raw) == 0:
        return {}

    decoded = json.loads(raw.decode("utf-8"))
    return decoded


# =============================================================================
# CSRFTokenManager
# =============================================================================

def test_token_manager_generates_deterministic_token_for_session():
    """
        Two generate() calls for the same session id yield the same token.
        This is the property the validator relies on for stateless
        verification.
    """
    manager = CSRFTokenManager(secret_key=SECRET_KEY)

    first = manager.generate(SESSION_ID)
    second = manager.generate(SESSION_ID)

    if first != second:
        errmsg = "Expected deterministic token, got {!r} != {!r}".format(first, second)
        raise AssertionError(errmsg)

    return


def test_token_manager_distinct_sessions_produce_distinct_tokens():
    """
        Different sessions must not collide on the same token.
    """
    manager = CSRFTokenManager(secret_key=SECRET_KEY)

    token_a = manager.generate(SESSION_ID)
    token_b = manager.generate(OTHER_SESSION_ID)

    if token_a == token_b:
        errmsg = "Expected distinct tokens for distinct sessions, got identical {!r}".format(token_a)
        raise AssertionError(errmsg)

    return


def test_token_manager_validates_matching_token():
    """
        A freshly generated token validates against its own session id.
    """
    manager = CSRFTokenManager(secret_key=SECRET_KEY)

    token = manager.generate(SESSION_ID)
    is_valid = manager.validate(SESSION_ID, token)

    if not is_valid:
        errmsg = "Expected freshly generated token to validate"
        raise AssertionError(errmsg)

    return


def test_token_manager_rejects_token_from_different_session():
    """
        A token signed for one session must not validate for another.
    """
    manager = CSRFTokenManager(secret_key=SECRET_KEY)

    token = manager.generate(SESSION_ID)
    is_valid = manager.validate(OTHER_SESSION_ID, token)

    if is_valid:
        errmsg = "Expected token to fail when validated against a different session"
        raise AssertionError(errmsg)

    return


def test_token_manager_rejects_empty_or_none_inputs():
    """
        validate() returns False for missing or empty arguments rather
        than raising; raising should be reserved for programmer errors.
    """
    manager = CSRFTokenManager(secret_key=SECRET_KEY)

    if manager.validate(None, "any") is not False:
        raise AssertionError("Expected False for None session_id")
    if manager.validate("", "any") is not False:
        raise AssertionError("Expected False for empty session_id")
    if manager.validate(SESSION_ID, None) is not False:
        raise AssertionError("Expected False for None token")
    if manager.validate(SESSION_ID, "") is not False:
        raise AssertionError("Expected False for empty token")

    return


def test_token_manager_requires_non_empty_secret_key():
    """
        Constructing a manager with an empty secret key is a programming
        error and should raise CSRFError.
    """
    try:
        CSRFTokenManager(secret_key="")
    except CSRFError:
        return

    errmsg = "Expected CSRFError for empty secret key"
    raise AssertionError(errmsg)


def test_token_manager_different_secret_keys_invalidate_tokens():
    """
        Tokens signed with one secret must not validate under another.
        Documents the operator-facing invariant for secret rotation.
    """
    manager_a = CSRFTokenManager(secret_key="secret-a")
    manager_b = CSRFTokenManager(secret_key="secret-b")

    token = manager_a.generate(SESSION_ID)
    is_valid = manager_b.validate(SESSION_ID, token)

    if is_valid:
        errmsg = "Expected token to fail when verified under a different secret"
        raise AssertionError(errmsg)

    return


# =============================================================================
# cookie_session_id_resolver
# =============================================================================

def test_cookie_resolver_extracts_named_cookie_value():
    """
        The resolver pulls the named cookie out of the Cookie header.
    """
    resolver = cookie_session_id_resolver(cookie_name="session_id")

    cookie_value = "other=foo; session_id=sess-42; theme=dark"
    scope = create_http_scope(
        headers=[(b"cookie", cookie_value.encode("ascii"))]
    )

    resolved = resolver(scope)

    if resolved != "sess-42":
        errmsg = "Expected resolved 'sess-42', got {!r}".format(resolved)
        raise AssertionError(errmsg)

    return


def test_cookie_resolver_returns_none_when_cookie_absent():
    """
        Missing cookie header / missing cookie name yields None.
    """
    resolver = cookie_session_id_resolver(cookie_name="session_id")
    scope = create_http_scope(headers=[])

    resolved = resolver(scope)

    if resolved is not None:
        errmsg = "Expected None when no Cookie header present, got {!r}".format(resolved)
        raise AssertionError(errmsg)

    return


# =============================================================================
# CSRFMiddleware
# =============================================================================

def _build_middleware(app, exempt_paths=None):
    manager = CSRFTokenManager(secret_key=SECRET_KEY)
    resolver = cookie_session_id_resolver(cookie_name="session_id")
    middleware = CSRFMiddleware(
        app=app,
        token_manager=manager,
        session_id_resolver=resolver,
        exempt_paths=exempt_paths,
    )
    return middleware, manager


def test_middleware_passes_safe_method_through():
    """
        GET/HEAD/OPTIONS bypass validation regardless of token presence.
    """
    app = MockASGIApp()
    middleware, _manager = _build_middleware(app)

    scope = create_http_scope(method="GET", path="/dashboard")
    send = MockSend()
    run_async(middleware(scope, MockReceive(), send))

    if not app.was_called:
        errmsg = "Expected wrapped app to be called for safe GET"
        raise AssertionError(errmsg)

    if len(send.messages) != 0:
        errmsg = "Expected no response messages from middleware on safe path"
        raise AssertionError(errmsg)

    return


def test_middleware_rejects_unsafe_method_when_no_session():
    """
        An unsafe request without a session cookie cannot be CSRF-validated
        and is rejected with 403 / csrf_missing_session.
    """
    app = MockASGIApp()
    middleware, _manager = _build_middleware(app)

    scope = create_http_scope(method="POST", path="/postback")
    send = MockSend()
    run_async(middleware(scope, MockReceive(), send))

    if app.was_called:
        errmsg = "Expected wrapped app NOT to be called when no session is present"
        raise AssertionError(errmsg)

    start_message = send.messages[0]
    if start_message.get("status") != 403:
        errmsg = "Expected 403 status, got {}".format(start_message.get("status"))
        raise AssertionError(errmsg)

    body = _decode_json_body(send.messages)
    if body.get("error") != "csrf_missing_session":
        errmsg = "Expected error 'csrf_missing_session', got {!r}".format(body.get("error"))
        raise AssertionError(errmsg)

    return


def test_middleware_rejects_unsafe_method_when_token_missing():
    """
        Session is present but no header / form token is supplied →
        403 / csrf_token_missing.
    """
    app = MockASGIApp()
    middleware, _manager = _build_middleware(app)

    scope = create_http_scope(
        method="POST",
        path="/postback",
        headers=[(b"cookie", b"session_id=" + SESSION_ID.encode("ascii"))],
    )
    send = MockSend()
    run_async(middleware(scope, MockReceive(), send))

    if app.was_called:
        errmsg = "Expected wrapped app NOT to be called when token missing"
        raise AssertionError(errmsg)

    body = _decode_json_body(send.messages)
    if body.get("error") != "csrf_token_missing":
        errmsg = "Expected error 'csrf_token_missing', got {!r}".format(body.get("error"))
        raise AssertionError(errmsg)

    return


def test_middleware_rejects_unsafe_method_when_token_invalid():
    """
        Session present, header supplied, but token does not match →
        403 / csrf_token_invalid.
    """
    app = MockASGIApp()
    middleware, _manager = _build_middleware(app)

    scope = create_http_scope(
        method="POST",
        path="/postback",
        headers=[
            (b"cookie", b"session_id=" + SESSION_ID.encode("ascii")),
            (b"x-csrf-token", b"this-is-not-a-valid-token"),
        ],
    )
    send = MockSend()
    run_async(middleware(scope, MockReceive(), send))

    if app.was_called:
        errmsg = "Expected wrapped app NOT to be called for invalid token"
        raise AssertionError(errmsg)

    body = _decode_json_body(send.messages)
    if body.get("error") != "csrf_token_invalid":
        errmsg = "Expected error 'csrf_token_invalid', got {!r}".format(body.get("error"))
        raise AssertionError(errmsg)

    return


def test_middleware_passes_unsafe_method_with_valid_token():
    """
        The happy path: session cookie + matching X-CSRF-Token header
        forwards through to the wrapped application untouched.
    """
    app = MockASGIApp()
    middleware, manager = _build_middleware(app)

    valid_token = manager.generate(SESSION_ID)
    scope = create_http_scope(
        method="POST",
        path="/postback",
        headers=[
            (b"cookie", b"session_id=" + SESSION_ID.encode("ascii")),
            (b"x-csrf-token", valid_token.encode("ascii")),
        ],
    )
    send = MockSend()
    run_async(middleware(scope, MockReceive(), send))

    if not app.was_called:
        errmsg = "Expected wrapped app to be called when CSRF token validates"
        raise AssertionError(errmsg)

    if len(send.messages) != 0:
        errmsg = "Expected no middleware-side response on success, got {}".format(send.messages)
        raise AssertionError(errmsg)

    return


def test_middleware_exempt_path_bypasses_validation():
    """
        Paths listed in exempt_paths skip CSRF entirely — useful for
        webhooks that authenticate via signature.
    """
    app = MockASGIApp()
    middleware, _manager = _build_middleware(app, exempt_paths={"/webhooks/stripe"})

    # No session, no token, but on the exempt path.
    scope = create_http_scope(method="POST", path="/webhooks/stripe")
    send = MockSend()
    run_async(middleware(scope, MockReceive(), send))

    if not app.was_called:
        errmsg = "Expected wrapped app to be called for exempt path"
        raise AssertionError(errmsg)

    return


def test_middleware_passes_non_http_scope_through():
    """
        Lifespan / websocket scopes are not HTTP and must not be
        intercepted by the CSRF middleware.
    """
    app = MockASGIApp()
    middleware, _manager = _build_middleware(app)

    scope = {"type": "lifespan"}
    send = MockSend()
    run_async(middleware(scope, MockReceive(), send))

    if not app.was_called:
        errmsg = "Expected wrapped app to be called for non-HTTP scope"
        raise AssertionError(errmsg)

    return


# =============================================================================
# make_csrf_context_processor
# =============================================================================

def test_context_processor_injects_token_when_session_id_present():
    """
        With a session_id in the rendering context, the processor
        emits the matching csrf_token under the configured key.
    """
    manager = CSRFTokenManager(secret_key=SECRET_KEY)
    processor = make_csrf_context_processor(token_manager=manager)

    output = processor({"session_id": SESSION_ID})

    if "csrf_token" not in output:
        errmsg = "Expected 'csrf_token' in processor output, got {!r}".format(output)
        raise AssertionError(errmsg)

    expected = manager.generate(SESSION_ID)
    if output["csrf_token"] != expected:
        errmsg = "Expected token {!r}, got {!r}".format(expected, output["csrf_token"])
        raise AssertionError(errmsg)

    return


def test_context_processor_returns_empty_when_session_id_missing():
    """
        Anonymous renders (no session) must succeed without injecting a
        token; the form-rendering caller is responsible for not exposing
        a CSRF-protected form to anonymous users.
    """
    manager = CSRFTokenManager(secret_key=SECRET_KEY)
    processor = make_csrf_context_processor(token_manager=manager)

    output = processor({})

    if output != {}:
        errmsg = "Expected empty dict for missing session_id, got {!r}".format(output)
        raise AssertionError(errmsg)

    return
