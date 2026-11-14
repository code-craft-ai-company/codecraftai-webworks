"""
    Unit tests for SessionAuthBlueprint.

    This module verifies the SessionAuthBlueprint endpoints including
    session login, logout, and info retrieval. It validates secure
    cookie setting, session invalidation, configurable session duration,
    and session renewal on activity.

    **Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7**
"""

import asyncio

from datetime import datetime, timedelta, timezone

from ccai.webworks.authentication.blueprints.session import (
    SessionAuthBlueprint,
    SessionStore,
)
from ccai.webworks.authentication.blueprints.responses import AuthError
from ccai.webworks.authentication.core import AuthenticationStatus, Principal
from ccai.webworks.authentication.errors import (
    AccountLockoutPolicy,
    LockoutConfig,
    LoginThrottle,
)
from ccai.webworks.authentication.session import SessionAuthenticator


# =============================================================================
# Test Helpers
# =============================================================================


class MockJsonRequest:
    """
        A simple mock request that returns a JSON body dictionary
        and optionally carries cookie headers.
    """

    def __init__(self, data, cookies=None):
        self._data = data
        self.cookies = cookies

    def json(self):
        return self._data


class MockIdentityProvider:
    """
        A mock identity provider that knows about a single user.
    """

    def __init__(self, known_username, known_password, principal):
        self._known_username = known_username
        self._known_password = known_password
        self._principal = principal

    async def validate_credentials(self, username, password):
        if username == self._known_username and password == self._known_password:
            return self._principal
        return None


class RejectAllIdentityProvider:
    """
        A mock identity provider that rejects every credential pair.
    """

    async def validate_credentials(self, username, password):
        return None


class MockSessionStore(SessionStore):
    """
        A mock session store that stores sessions in memory.
    """

    def __init__(self):
        self._sessions = {}

    async def create_session(self, session_id, principal_id, created_at,
                             expires_at, last_accessed):
        self._sessions[session_id] = {
            "session_id": session_id,
            "principal_id": principal_id,
            "created_at": created_at,
            "expires_at": expires_at,
            "last_accessed": last_accessed,
        }

    async def get_session(self, session_id):
        return self._sessions.get(session_id)

    async def delete_session(self, session_id):
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False

    async def update_last_accessed(self, session_id, last_accessed):
        if session_id in self._sessions:
            self._sessions[session_id]["last_accessed"] = last_accessed
            return True
        return False


def _session_id_from_response(response, cookie_name="session_id"):
    """
        Read the session id from the Set-Cookie header of a response.

        The session id is deliberately absent from response bodies; the
        HttpOnly cookie is the only place it is sent.
    """
    cookie = response.get("headers", {}).get("Set-Cookie", "")
    first_part = cookie.split(";", 1)[0]
    name, _, value = first_part.partition("=")
    if name.strip() != cookie_name:
        errmsg = "Expected a {!r} cookie, got {!r}".format(cookie_name, cookie)
        raise AssertionError(errmsg)
    return value.strip()


def _session_exists(blueprint, session_id):
    """
        Check whether the blueprint's session store still holds a session.
    """
    session = asyncio.run(blueprint.get_session_store().get_session(session_id))
    return session is not None


TEST_PRINCIPAL = Principal(
    identifier="user-001",
    display_name="Test User",
)

KNOWN_USERNAME = "testuser"
KNOWN_PASSWORD = "testpass"


def _create_fresh_blueprint():
    """
        Create a fresh SessionAuthBlueprint subclass to avoid class-level
        state leakage between tests.
    """

    class FreshBlueprint(SessionAuthBlueprint):
        pass

    FreshBlueprint.identity_provider = MockIdentityProvider(
        KNOWN_USERNAME, KNOWN_PASSWORD, TEST_PRINCIPAL
    )
    FreshBlueprint.session_store = None
    FreshBlueprint.session_duration = 3600
    FreshBlueprint.remember_me_duration = 86400 * 30
    FreshBlueprint.cookie_name = "session_id"
    FreshBlueprint.cookie_secure = True
    FreshBlueprint.cookie_httponly = True
    FreshBlueprint.cookie_samesite = "Lax"
    FreshBlueprint.enabled_endpoints = None
    FreshBlueprint.auth_system = None
    FreshBlueprint.base_path = "/auth/session"
    FreshBlueprint._memory_store = {}

    return FreshBlueprint


def _login_and_get_session_id(blueprint):
    """
        Perform a login and return the session_id from the response.
    """
    request = MockJsonRequest({
        "username": KNOWN_USERNAME,
        "password": KNOWN_PASSWORD,
    })
    response = blueprint.login(request)
    session_id = _session_id_from_response(response)
    return session_id, response


# =============================================================================
# Login Endpoint Tests (Requirement 5.1, 5.4)
# =============================================================================

def test_login_success():
    """
        Verify that the login endpoint creates a session and returns
        session info with a Set-Cookie header.

        **Validates: Requirements 5.1, 5.4**
    """
    blueprint = _create_fresh_blueprint()

    request = MockJsonRequest({
        "username": KNOWN_USERNAME,
        "password": KNOWN_PASSWORD,
    })

    response = blueprint.login(request)

    if response["status"] != 200:
        errmsg = "Expected status 200, got {}".format(response["status"])
        raise AssertionError(errmsg)

    body = response["body"]

    if "session_id" in body:
        errmsg = "Expected the session id to stay out of the response body"
        raise AssertionError(errmsg)

    if body.get("principal_id") != "user-001":
        errmsg = "Expected principal_id 'user-001', got {!r}".format(
            body.get("principal_id")
        )
        raise AssertionError(errmsg)

    if "created_at" not in body:
        errmsg = "Expected created_at in response body"
        raise AssertionError(errmsg)

    if "expires_at" not in body:
        errmsg = "Expected expires_at in response body"
        raise AssertionError(errmsg)

    # Verify Set-Cookie header is present
    headers = response.get("headers", {})
    cookie = headers.get("Set-Cookie", "")

    if not cookie:
        errmsg = "Expected Set-Cookie header in response"
        raise AssertionError(errmsg)

    if "session_id=" not in cookie:
        errmsg = "Expected session_id= in Set-Cookie header, got {!r}".format(cookie)
        raise AssertionError(errmsg)

    return


def test_login_sets_secure_cookie_attributes():
    """
        Verify that the login response cookie includes HttpOnly, Secure,
        and SameSite attributes.

        **Validates: Requirements 5.4**
    """
    blueprint = _create_fresh_blueprint()

    request = MockJsonRequest({
        "username": KNOWN_USERNAME,
        "password": KNOWN_PASSWORD,
    })

    response = blueprint.login(request)
    headers = response.get("headers", {})
    cookie = headers.get("Set-Cookie", "")

    if "HttpOnly" not in cookie:
        errmsg = "Expected HttpOnly in Set-Cookie header, got {!r}".format(cookie)
        raise AssertionError(errmsg)

    if "Secure" not in cookie:
        errmsg = "Expected Secure in Set-Cookie header, got {!r}".format(cookie)
        raise AssertionError(errmsg)

    if "SameSite=Lax" not in cookie:
        errmsg = "Expected SameSite=Lax in Set-Cookie header, got {!r}".format(cookie)
        raise AssertionError(errmsg)

    return


def test_login_invalid_credentials():
    """
        Verify that the login endpoint returns 401 for invalid credentials.

        **Validates: Requirements 5.1**
    """
    blueprint = _create_fresh_blueprint()

    request = MockJsonRequest({
        "username": "wronguser",
        "password": "wrongpass",
    })

    response = blueprint.login(request)

    if response["status"] != 401:
        errmsg = "Expected status 401, got {}".format(response["status"])
        raise AssertionError(errmsg)

    body = response["body"]

    if body.get("error") != "invalid_credentials":
        errmsg = "Expected error 'invalid_credentials', got {!r}".format(
            body.get("error")
        )
        raise AssertionError(errmsg)

    return


def test_login_missing_credentials():
    """
        Verify that the login endpoint returns 401 when credentials are missing.

        **Validates: Requirements 5.1**
    """
    blueprint = _create_fresh_blueprint()

    request = MockJsonRequest({})

    response = blueprint.login(request)

    if response["status"] != 401:
        errmsg = "Expected status 401, got {}".format(response["status"])
        raise AssertionError(errmsg)

    body = response["body"]

    if body.get("error") != "invalid_request":
        errmsg = "Expected error 'invalid_request', got {!r}".format(
            body.get("error")
        )
        raise AssertionError(errmsg)

    return


def test_login_no_identity_provider():
    """
        Verify that the login endpoint returns 500 when no identity
        provider is configured.

        **Validates: Requirements 5.1**
    """
    blueprint = _create_fresh_blueprint()
    blueprint.identity_provider = None

    request = MockJsonRequest({
        "username": KNOWN_USERNAME,
        "password": KNOWN_PASSWORD,
    })

    response = blueprint.login(request)

    if response["status"] != 500:
        errmsg = "Expected status 500, got {}".format(response["status"])
        raise AssertionError(errmsg)

    return


def test_login_with_session_store():
    """
        Verify that the login endpoint stores the session via the session store.

        **Validates: Requirements 5.1**
    """
    store = MockSessionStore()
    blueprint = _create_fresh_blueprint()
    blueprint.session_store = store

    request = MockJsonRequest({
        "username": KNOWN_USERNAME,
        "password": KNOWN_PASSWORD,
    })

    response = blueprint.login(request)

    if response["status"] != 200:
        errmsg = "Expected status 200, got {}".format(response["status"])
        raise AssertionError(errmsg)

    session_id = _session_id_from_response(response)

    if session_id not in store._sessions:
        errmsg = "Expected session to be stored in session store"
        raise AssertionError(errmsg)

    return


def test_login_remember_me():
    """
        Verify that the login endpoint uses remember_me_duration when
        remember_me is True.

        **Validates: Requirements 5.6**
    """
    blueprint = _create_fresh_blueprint()
    blueprint.session_duration = 3600
    blueprint.remember_me_duration = 86400 * 30

    request = MockJsonRequest({
        "username": KNOWN_USERNAME,
        "password": KNOWN_PASSWORD,
        "remember_me": True,
    })

    response = blueprint.login(request)

    if response["status"] != 200:
        errmsg = "Expected status 200, got {}".format(response["status"])
        raise AssertionError(errmsg)

    headers = response.get("headers", {})
    cookie = headers.get("Set-Cookie", "")

    # The Max-Age should reflect remember_me_duration (30 days = 2592000)
    expected_max_age = "Max-Age={}".format(86400 * 30)
    if expected_max_age not in cookie:
        errmsg = "Expected {} in cookie, got {!r}".format(expected_max_age, cookie)
        raise AssertionError(errmsg)

    return


# =============================================================================
# Logout Endpoint Tests (Requirement 5.2, 5.5)
# =============================================================================

def test_logout_clears_session():
    """
        Verify that the logout endpoint invalidates the session and
        clears the cookie.

        **Validates: Requirements 5.2, 5.5**
    """
    blueprint = _create_fresh_blueprint()

    # Login first
    session_id, _ = _login_and_get_session_id(blueprint)

    # Logout
    logout_request = MockJsonRequest(
        {},
        cookies={"session_id": session_id}
    )
    response = blueprint.logout(logout_request)

    if response["status"] != 200:
        errmsg = "Expected status 200, got {}".format(response["status"])
        raise AssertionError(errmsg)

    # Verify the clear-cookie header
    headers = response.get("headers", {})
    cookie = headers.get("Set-Cookie", "")

    if "Max-Age=0" not in cookie:
        errmsg = "Expected Max-Age=0 in clear cookie, got {!r}".format(cookie)
        raise AssertionError(errmsg)

    # Verify the session is removed from the store
    if _session_exists(blueprint, session_id):
        errmsg = "Expected session to be removed from memory store"
        raise AssertionError(errmsg)

    return


def test_logout_with_session_store():
    """
        Verify that the logout endpoint removes the session from the store.

        **Validates: Requirements 5.2, 5.5**
    """
    store = MockSessionStore()
    blueprint = _create_fresh_blueprint()
    blueprint.session_store = store

    # Login first
    login_request = MockJsonRequest({
        "username": KNOWN_USERNAME,
        "password": KNOWN_PASSWORD,
    })
    login_response = blueprint.login(login_request)
    session_id = _session_id_from_response(login_response)

    # Logout
    logout_request = MockJsonRequest(
        {},
        cookies={"session_id": session_id}
    )
    response = blueprint.logout(logout_request)

    if response["status"] != 200:
        errmsg = "Expected status 200, got {}".format(response["status"])
        raise AssertionError(errmsg)

    if session_id in store._sessions:
        errmsg = "Expected session to be removed from session store"
        raise AssertionError(errmsg)

    return


def test_logout_without_cookie():
    """
        Verify that the logout endpoint succeeds even without a session cookie.

        **Validates: Requirements 5.2**
    """
    blueprint = _create_fresh_blueprint()

    request = MockJsonRequest({})
    response = blueprint.logout(request)

    if response["status"] != 200:
        errmsg = "Expected status 200, got {}".format(response["status"])
        raise AssertionError(errmsg)

    return


# =============================================================================
# Info Endpoint Tests (Requirement 5.3, 5.7)
# =============================================================================

def test_info_returns_session_details():
    """
        Verify that the info endpoint returns session details for a
        valid session.

        **Validates: Requirements 5.3**
    """
    blueprint = _create_fresh_blueprint()

    # Login first
    session_id, _ = _login_and_get_session_id(blueprint)

    # Get session info
    info_request = MockJsonRequest(
        {},
        cookies={"session_id": session_id}
    )
    response = blueprint.info(info_request)

    if response["status"] != 200:
        errmsg = "Expected status 200, got {}".format(response["status"])
        raise AssertionError(errmsg)

    body = response["body"]

    if "session_id" in body:
        errmsg = "Expected the session id to stay out of the info response body"
        raise AssertionError(errmsg)

    if body.get("principal_id") != "user-001":
        errmsg = "Expected principal_id 'user-001', got {!r}".format(
            body.get("principal_id")
        )
        raise AssertionError(errmsg)

    return


def test_info_no_cookie():
    """
        Verify that the info endpoint returns 401 when no session cookie
        is present.

        **Validates: Requirements 5.3**
    """
    blueprint = _create_fresh_blueprint()

    request = MockJsonRequest({})
    response = blueprint.info(request)

    if response["status"] != 401:
        errmsg = "Expected status 401, got {}".format(response["status"])
        raise AssertionError(errmsg)

    return


def test_info_invalid_session():
    """
        Verify that the info endpoint returns 401 for an invalid session ID.

        **Validates: Requirements 5.3**
    """
    blueprint = _create_fresh_blueprint()

    request = MockJsonRequest(
        {},
        cookies={"session_id": "nonexistent-session-id"}
    )
    response = blueprint.info(request)

    if response["status"] != 401:
        errmsg = "Expected status 401, got {}".format(response["status"])
        raise AssertionError(errmsg)

    return


def test_info_after_logout_returns_401():
    """
        Verify that the info endpoint returns 401 after the session
        has been invalidated via logout.

        **Validates: Requirements 5.5**
    """
    blueprint = _create_fresh_blueprint()

    # Login
    session_id, _ = _login_and_get_session_id(blueprint)

    # Logout
    logout_request = MockJsonRequest(
        {},
        cookies={"session_id": session_id}
    )
    blueprint.logout(logout_request)

    # Try to get info
    info_request = MockJsonRequest(
        {},
        cookies={"session_id": session_id}
    )
    response = blueprint.info(info_request)

    if response["status"] != 401:
        errmsg = "Expected status 401 after logout, got {}".format(
            response["status"]
        )
        raise AssertionError(errmsg)

    return


def test_info_updates_last_accessed():
    """
        Verify that the info endpoint updates the last_accessed timestamp
        to support session renewal on activity.

        **Validates: Requirements 5.7**
    """
    import time

    blueprint = _create_fresh_blueprint()

    # Login
    session_id, login_response = _login_and_get_session_id(blueprint)
    original_last_accessed = login_response["body"]["last_accessed"]

    # Small delay to ensure timestamp difference
    time.sleep(0.01)

    # Get session info
    info_request = MockJsonRequest(
        {},
        cookies={"session_id": session_id}
    )
    response = blueprint.info(info_request)

    if response["status"] != 200:
        errmsg = "Expected status 200, got {}".format(response["status"])
        raise AssertionError(errmsg)

    new_last_accessed = response["body"]["last_accessed"]

    if new_last_accessed == original_last_accessed:
        errmsg = (
            "Expected last_accessed to be updated on info request. "
            "original={!r}, new={!r}".format(
                original_last_accessed, new_last_accessed
            )
        )
        raise AssertionError(errmsg)

    return


# =============================================================================
# Configurable Session Duration Tests (Requirement 5.6)
# =============================================================================

def test_configurable_session_duration():
    """
        Verify that the session duration is configurable.

        **Validates: Requirements 5.6**
    """
    blueprint = _create_fresh_blueprint()
    blueprint.session_duration = 7200  # 2 hours

    request = MockJsonRequest({
        "username": KNOWN_USERNAME,
        "password": KNOWN_PASSWORD,
    })

    response = blueprint.login(request)

    if response["status"] != 200:
        errmsg = "Expected status 200, got {}".format(response["status"])
        raise AssertionError(errmsg)

    headers = response.get("headers", {})
    cookie = headers.get("Set-Cookie", "")

    if "Max-Age=7200" not in cookie:
        errmsg = "Expected Max-Age=7200 in cookie, got {!r}".format(cookie)
        raise AssertionError(errmsg)

    return


# =============================================================================
# Endpoint Enable/Disable Tests
# =============================================================================

def test_disabled_login_endpoint():
    """
        Verify that the login endpoint returns 404 when disabled.
    """
    blueprint = _create_fresh_blueprint()
    blueprint.enabled_endpoints = {"logout", "info"}

    request = MockJsonRequest({
        "username": KNOWN_USERNAME,
        "password": KNOWN_PASSWORD,
    })

    response = blueprint.login(request)

    if response["status"] != 404:
        errmsg = "Expected status 404 for disabled endpoint, got {}".format(
            response["status"]
        )
        raise AssertionError(errmsg)

    return


def test_disabled_logout_endpoint():
    """
        Verify that the logout endpoint returns 404 when disabled.
    """
    blueprint = _create_fresh_blueprint()
    blueprint.enabled_endpoints = {"login", "info"}

    request = MockJsonRequest({})

    response = blueprint.logout(request)

    if response["status"] != 404:
        errmsg = "Expected status 404 for disabled endpoint, got {}".format(
            response["status"]
        )
        raise AssertionError(errmsg)

    return


def test_disabled_info_endpoint():
    """
        Verify that the info endpoint returns 404 when disabled.
    """
    blueprint = _create_fresh_blueprint()
    blueprint.enabled_endpoints = {"login", "logout"}

    request = MockJsonRequest(
        {},
        cookies={"session_id": "some-session"}
    )

    response = blueprint.info(request)

    if response["status"] != 404:
        errmsg = "Expected status 404 for disabled endpoint, got {}".format(
            response["status"]
        )
        raise AssertionError(errmsg)

    return


def test_pre_authenticate_hook_blocks_login():
    """
        Verify that the pre_authenticate hook can block login.
    """

    class HookBlueprint(SessionAuthBlueprint):
        pass

    HookBlueprint.identity_provider = MockIdentityProvider(
        KNOWN_USERNAME, KNOWN_PASSWORD, TEST_PRINCIPAL
    )
    HookBlueprint.session_store = None
    HookBlueprint.session_duration = 3600
    HookBlueprint.remember_me_duration = 86400 * 30
    HookBlueprint.cookie_name = "session_id"
    HookBlueprint.cookie_secure = True
    HookBlueprint.cookie_httponly = True
    HookBlueprint.cookie_samesite = "Lax"
    HookBlueprint.enabled_endpoints = None
    HookBlueprint.auth_system = None
    HookBlueprint.base_path = "/auth/session"
    HookBlueprint._memory_store = {}

    @classmethod
    def blocking_pre_auth(cls, request):
        return AuthError(
            error="rate_limited",
            error_description="Too many requests"
        )

    HookBlueprint.pre_authenticate = blocking_pre_auth

    request = MockJsonRequest({
        "username": KNOWN_USERNAME,
        "password": KNOWN_PASSWORD,
    })

    response = HookBlueprint.login(request)

    if response["status"] != 401:
        errmsg = "Expected status 401 from pre_authenticate hook, got {}".format(
            response["status"]
        )
        raise AssertionError(errmsg)

    body = response["body"]

    if body.get("error") != "rate_limited":
        errmsg = "Expected error 'rate_limited', got {!r}".format(
            body.get("error")
        )
        raise AssertionError(errmsg)

    return


# =============================================================================
# establish_session() Tests
#
# These cover the public class method that sibling blueprints (magic-link,
# OAuth callback, SSO) use to materialize a session for an already-authenticated
# principal — i.e. the post-credential-validation half of login.
# =============================================================================


def test_establish_session_without_credentials_returns_session():
    """
        Verify that ``establish_session`` produces a fully formed session
        response when given a Principal directly, without going through the
        username/password ``login`` endpoint.
    """
    blueprint = _create_fresh_blueprint()

    response = blueprint.establish_session(principal=TEST_PRINCIPAL)

    if response["status"] != 200:
        errmsg = "Expected status 200, got {}".format(response["status"])
        raise AssertionError(errmsg)

    body = response["body"]

    if "session_id" in body:
        errmsg = "Expected the session id to stay out of the response body"
        raise AssertionError(errmsg)

    if body.get("principal_id") != "user-001":
        errmsg = "Expected principal_id 'user-001', got {!r}".format(
            body.get("principal_id")
        )
        raise AssertionError(errmsg)

    cookie = response.get("headers", {}).get("Set-Cookie", "")
    if "session_id=" not in cookie:
        errmsg = "Expected session_id= in Set-Cookie header, got {!r}".format(cookie)
        raise AssertionError(errmsg)

    if body.get("message") != "Session established":
        errmsg = "Expected default message 'Session established', got {!r}".format(
            body.get("message")
        )
        raise AssertionError(errmsg)

    return


def test_establish_session_persists_to_session_store():
    """
        Verify that ``establish_session`` writes the new session through a
        configured :class:`SessionStore`, not just the in-memory fallback.
    """
    blueprint = _create_fresh_blueprint()
    store = MockSessionStore()
    blueprint.session_store = store

    response = blueprint.establish_session(principal=TEST_PRINCIPAL)

    session_id = _session_id_from_response(response)
    persisted = store._sessions.get(session_id)

    if persisted is None:
        errmsg = "Expected session {!r} to be persisted in store".format(session_id)
        raise AssertionError(errmsg)

    if persisted.get("principal_id") != "user-001":
        errmsg = "Expected persisted principal_id 'user-001', got {!r}".format(
            persisted.get("principal_id")
        )
        raise AssertionError(errmsg)

    return


def test_establish_session_remember_me_uses_extended_duration():
    """
        Verify that ``remember_me=True`` causes the cookie Max-Age and the
        session expires_at to use :attr:`remember_me_duration` rather than
        :attr:`session_duration`.
    """
    blueprint = _create_fresh_blueprint()
    blueprint.session_duration = 60
    blueprint.remember_me_duration = 7 * 24 * 60 * 60

    response = blueprint.establish_session(
        principal=TEST_PRINCIPAL,
        remember_me=True
    )

    cookie = response.get("headers", {}).get("Set-Cookie", "")
    expected_max_age = "Max-Age={}".format(7 * 24 * 60 * 60)

    if expected_max_age not in cookie:
        errmsg = "Expected {!r} in Set-Cookie header, got {!r}".format(
            expected_max_age, cookie
        )
        raise AssertionError(errmsg)

    return


def test_establish_session_invokes_post_authenticate_with_scheme_and_attributes():
    """
        Verify that ``establish_session`` invokes the ``post_authenticate``
        hook with an :class:`AuthenticationContext` that carries the supplied
        ``scheme`` label and ``extra_attributes`` payload, so sibling
        blueprints can record channel-specific metadata.
    """
    blueprint = _create_fresh_blueprint()
    captured = {}

    @classmethod
    def capturing_post_auth(cls, request, context):
        captured["scheme"] = context.scheme
        captured["attributes"] = dict(context.attributes)
        captured["principal_id"] = context.principal.identifier
        return None

    blueprint.post_authenticate = capturing_post_auth

    blueprint.establish_session(
        principal=TEST_PRINCIPAL,
        scheme="MagicLink",
        extra_attributes={"token_id": "tok-42"},
    )

    if captured.get("scheme") != "MagicLink":
        errmsg = "Expected scheme 'MagicLink' on context, got {!r}".format(
            captured.get("scheme")
        )
        raise AssertionError(errmsg)

    if captured.get("attributes", {}).get("token_id") != "tok-42":
        errmsg = "Expected token_id 'tok-42' in context attributes, got {!r}".format(
            captured.get("attributes")
        )
        raise AssertionError(errmsg)

    if captured.get("principal_id") != "user-001":
        errmsg = "Expected principal_id 'user-001' on context, got {!r}".format(
            captured.get("principal_id")
        )
        raise AssertionError(errmsg)

    return


def test_login_preserves_login_successful_message():
    """
        Regression: the credential ``login`` endpoint must continue to
        return ``message="Login successful"`` after the body was refactored
        to delegate to ``establish_session``. Existing API consumers depend
        on this string.
    """
    blueprint = _create_fresh_blueprint()

    request = MockJsonRequest({
        "username": KNOWN_USERNAME,
        "password": KNOWN_PASSWORD,
    })

    response = blueprint.login(request)

    if response["body"].get("message") != "Login successful":
        errmsg = "Expected message 'Login successful', got {!r}".format(
            response["body"].get("message")
        )
        raise AssertionError(errmsg)

    return


# =============================================================================
# Session Store Shared With SessionAuthenticator
# =============================================================================

def test_login_session_is_accepted_by_session_authenticator():
    """
        Verify that the cookie a login sets authenticates a later request
        through SessionAuthenticator when both use the blueprint's session
        store, and that the full principal comes back.
    """
    blueprint = _create_fresh_blueprint()
    blueprint.identity_provider = MockIdentityProvider(
        KNOWN_USERNAME,
        KNOWN_PASSWORD,
        Principal(identifier="user-001", roles={"editor"}, permissions={"read"})
    )

    session_id, _ = _login_and_get_session_id(blueprint)

    authenticator = SessionAuthenticator(
        session_store=blueprint.get_session_store(),
        cookie_name=blueprint.cookie_name
    )
    result = asyncio.run(
        authenticator.authenticate({"cookies": {"session_id": session_id}})
    )

    if result.status != AuthenticationStatus.SUCCESS:
        errmsg = "Expected SUCCESS for a blueprint session, got {} ({})".format(
            result.status, result.error_code
        )
        raise AssertionError(errmsg)

    principal = result.context.principal

    if principal.identifier != "user-001":
        errmsg = "Expected principal 'user-001', got {!r}".format(principal.identifier)
        raise AssertionError(errmsg)

    if principal.roles != {"editor"}:
        errmsg = "Expected the principal's roles to be kept, got {!r}".format(principal.roles)
        raise AssertionError(errmsg)

    return


def test_logged_out_session_is_refused_by_session_authenticator():
    """
        Verify that logout invalidates the session for SessionAuthenticator.
    """
    blueprint = _create_fresh_blueprint()
    session_id, _ = _login_and_get_session_id(blueprint)

    blueprint.logout(MockJsonRequest({}, cookies={"session_id": session_id}))

    authenticator = SessionAuthenticator(
        session_store=blueprint.get_session_store(),
        cookie_name=blueprint.cookie_name
    )
    result = asyncio.run(
        authenticator.authenticate({"cookies": {"session_id": session_id}})
    )

    if result.status != AuthenticationStatus.FAILURE:
        errmsg = "Expected FAILURE after logout, got {}".format(result.status)
        raise AssertionError(errmsg)

    return


def test_blueprint_subclasses_do_not_share_sessions():
    """
        Verify that each blueprint subclass has its own in-memory session
        store.
    """
    first = _create_fresh_blueprint()
    second = _create_fresh_blueprint()

    session_id, _ = _login_and_get_session_id(first)

    if first.get_session_store() is second.get_session_store():
        errmsg = "Expected each subclass to have its own session store"
        raise AssertionError(errmsg)

    if _session_exists(second, session_id):
        errmsg = "Expected a session of one subclass to be unknown to another"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Expiry Handling Fails Closed
# =============================================================================

def _blueprint_with_stored_expiry(expires_at):
    """
        Create a blueprint over a legacy store that holds one session with
        the given expires_at value.
    """
    store = MockSessionStore()
    store._sessions["stored-session"] = {
        "session_id": "stored-session",
        "principal_id": "user-001",
        "created_at": "2025-01-01T00:00:00+00:00",
        "expires_at": expires_at,
        "last_accessed": "2025-01-01T00:00:00+00:00",
    }

    blueprint = _create_fresh_blueprint()
    blueprint.session_store = store
    return blueprint, store


def test_info_treats_naive_past_expiry_as_expired():
    """
        Verify that an expires_at without a timezone that lies in the past
        expires the session instead of being skipped.
    """
    naive_past = (datetime.now(timezone.utc) - timedelta(hours=1)).replace(tzinfo=None)
    blueprint, store = _blueprint_with_stored_expiry(naive_past.isoformat())

    response = blueprint.info(
        MockJsonRequest({}, cookies={"session_id": "stored-session"})
    )

    if response["status"] != 401:
        errmsg = "Expected status 401, got {}".format(response["status"])
        raise AssertionError(errmsg)

    if response["body"].get("error") != "session_expired":
        errmsg = "Expected error 'session_expired', got {!r}".format(
            response["body"].get("error")
        )
        raise AssertionError(errmsg)

    if "stored-session" in store._sessions:
        errmsg = "Expected the expired session to be removed from the store"
        raise AssertionError(errmsg)

    return


def test_info_accepts_naive_future_expiry():
    """
        Verify that an expires_at without a timezone that lies in the future
        is read as UTC and the session stays valid.
    """
    naive_future = (datetime.now(timezone.utc) + timedelta(hours=1)).replace(tzinfo=None)
    blueprint, _ = _blueprint_with_stored_expiry(naive_future.isoformat())

    response = blueprint.info(
        MockJsonRequest({}, cookies={"session_id": "stored-session"})
    )

    if response["status"] != 200:
        errmsg = "Expected status 200, got {}".format(response["status"])
        raise AssertionError(errmsg)

    return


def test_info_treats_unparseable_expiry_as_expired():
    """
        Verify that a session whose expires_at cannot be parsed is treated
        as expired rather than as valid forever.
    """
    blueprint, _ = _blueprint_with_stored_expiry("not-a-timestamp")

    response = blueprint.info(
        MockJsonRequest({}, cookies={"session_id": "stored-session"})
    )

    if response["status"] != 401:
        errmsg = "Expected status 401, got {}".format(response["status"])
        raise AssertionError(errmsg)

    return


def test_info_unknown_session_clears_cookie():
    """
        Verify that the info endpoint clears the cookie when it names a
        session that does not exist.
    """
    blueprint = _create_fresh_blueprint()

    response = blueprint.info(
        MockJsonRequest({}, cookies={"session_id": "no-such-session"})
    )

    cookie = response.get("headers", {}).get("Set-Cookie", "")
    if "Max-Age=0" not in cookie:
        errmsg = "Expected a clearing Set-Cookie header, got {!r}".format(cookie)
        raise AssertionError(errmsg)

    return


# =============================================================================
# Request Parsing and Throttling
# =============================================================================

def test_login_rejects_non_object_body():
    """
        Verify that a JSON body that is not an object is answered with 400.
    """
    blueprint = _create_fresh_blueprint()

    response = blueprint.login(MockJsonRequest(["testuser", "testpass"]))

    if response["status"] != 400:
        errmsg = "Expected status 400, got {}".format(response["status"])
        raise AssertionError(errmsg)

    return


def test_login_answers_429_once_account_is_locked():
    """
        Verify that a configured login throttle locks an account after
        repeated failures and the login endpoint then answers 429, even for
        the correct password.
    """
    blueprint = _create_fresh_blueprint()
    blueprint.login_throttle = LoginThrottle(
        lockout_policy=AccountLockoutPolicy(LockoutConfig(max_failures=2))
    )

    for _ in range(2):
        blueprint.login(MockJsonRequest({
            "username": KNOWN_USERNAME,
            "password": "wrong-password",
        }))

    response = blueprint.login(MockJsonRequest({
        "username": KNOWN_USERNAME,
        "password": KNOWN_PASSWORD,
    }))

    if response["status"] != 429:
        errmsg = "Expected status 429 for a locked account, got {}".format(response["status"])
        raise AssertionError(errmsg)

    if "Retry-After" not in response.get("headers", {}):
        errmsg = "Expected a Retry-After header on the 429"
        raise AssertionError(errmsg)

    return
