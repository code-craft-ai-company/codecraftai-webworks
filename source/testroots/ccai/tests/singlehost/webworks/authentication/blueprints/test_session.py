"""
    Unit tests for SessionAuthBlueprint.

    This module verifies the SessionAuthBlueprint endpoints including
    session login, logout, and info retrieval. It validates secure
    cookie setting, session invalidation, configurable session duration,
    and session renewal on activity.

    **Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7**
"""

from ccai.webworks.authentication.blueprints.session import (
    SessionAuthBlueprint,
    SessionStore,
)
from ccai.webworks.authentication.blueprints.responses import AuthError
from ccai.webworks.authentication.core import Principal


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
    session_id = response["body"]["session_id"]
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

    if "session_id" not in body:
        errmsg = "Expected session_id in response body"
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

    session_id = response["body"]["session_id"]

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
    if session_id in blueprint._memory_store:
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
    session_id = login_response["body"]["session_id"]

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

    if body.get("session_id") != session_id:
        errmsg = "Expected session_id {!r}, got {!r}".format(
            session_id, body.get("session_id")
        )
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

    if "session_id" not in body:
        errmsg = "Expected session_id in response body"
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

    session_id = response["body"]["session_id"]
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
