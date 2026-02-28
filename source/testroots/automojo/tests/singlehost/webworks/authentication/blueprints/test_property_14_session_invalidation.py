"""
    Property test for session invalidation.

    Property 14: Session Invalidation
        For any logout request to SessionAuthBlueprint, the session SHALL
        be removed from the store and the cookie SHALL be cleared.

    **Validates: Requirements 5.5**
"""

import random
import string

from automojo.webworks.authentication.blueprints.session import (
    SessionAuthBlueprint,
    SessionStore,
)
from automojo.webworks.authentication.core import Principal


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
        A mock identity provider that accepts any credentials from a
        known set of users.
    """

    def __init__(self, known_users):
        self._known_users = known_users

    async def validate_credentials(self, username, password):
        key = (username, password)
        if key in self._known_users:
            return self._known_users[key]
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


def _random_string(min_len=1, max_len=30):
    """
        Generate a random alphanumeric string.

        :param min_len: Minimum string length.
        :param max_len: Maximum string length.

        :returns: A random string.
    """
    length = random.randint(min_len, max_len)
    chars = string.ascii_letters + string.digits
    result = "".join(random.choice(chars) for _ in range(length))
    return result


def _create_fresh_blueprint(use_store, known_users):
    """
        Create a fresh SessionAuthBlueprint subclass with the given
        configuration to avoid class-level state leakage.

        :param use_store: If True, attach a MockSessionStore.
        :param known_users: Dictionary mapping (username, password) to Principal.

        :returns: A tuple of (blueprint_class, store_or_None).
    """

    class FreshBlueprint(SessionAuthBlueprint):
        pass

    FreshBlueprint.identity_provider = MockIdentityProvider(known_users)
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

    store = None
    if use_store:
        store = MockSessionStore()
        FreshBlueprint.session_store = store

    return FreshBlueprint, store


# =============================================================================
# Property Tests
# =============================================================================

def test_property_14_session_invalidation():
    """
        Property 14: Session Invalidation.

        For any logout request to SessionAuthBlueprint, the session SHALL
        be removed from the store and the cookie SHALL be cleared.

        For each iteration:
        1. Generate random valid credentials.
        2. Randomly choose to use an in-memory store or a MockSessionStore.
        3. Login to create a session.
        4. Verify the session exists in the store.
        5. Logout with the session cookie.
        6. Verify the logout response contains a clear-cookie header
           (Max-Age=0).
        7. Verify the session is no longer in the store.
        8. Verify that a subsequent info request returns 401.

        **Validates: Requirements 5.5**
    """
    num_iterations = 100

    for iteration in range(num_iterations):
        # Generate random credentials
        username = _random_string(3, 20)
        password = _random_string(6, 30)
        principal_id = _random_string(5, 15)

        principal = Principal(
            identifier=principal_id,
            display_name="User {}".format(principal_id),
        )

        known_users = {(username, password): principal}
        use_store = random.choice([True, False])

        blueprint, store = _create_fresh_blueprint(
            use_store=use_store,
            known_users=known_users,
        )

        # Step 1: Login
        login_request = MockJsonRequest({
            "username": username,
            "password": password,
        })
        login_response = blueprint.login(login_request)

        if login_response["status"] != 200:
            errmsg = (
                "Iteration {}: Expected login status 200, got {}. "
                "username={!r}".format(
                    iteration, login_response["status"], username
                )
            )
            raise AssertionError(errmsg)

        session_id = login_response["body"]["session_id"]

        # Step 2: Verify session exists in the store
        if use_store:
            if session_id not in store._sessions:
                errmsg = (
                    "Iteration {}: Expected session to exist in store "
                    "after login. session_id={!r}".format(
                        iteration, session_id
                    )
                )
                raise AssertionError(errmsg)
        else:
            if session_id not in blueprint._memory_store:
                errmsg = (
                    "Iteration {}: Expected session to exist in memory "
                    "store after login. session_id={!r}".format(
                        iteration, session_id
                    )
                )
                raise AssertionError(errmsg)

        # Step 3: Logout
        logout_request = MockJsonRequest(
            {},
            cookies={"session_id": session_id}
        )
        logout_response = blueprint.logout(logout_request)

        if logout_response["status"] != 200:
            errmsg = (
                "Iteration {}: Expected logout status 200, got {}".format(
                    iteration, logout_response["status"]
                )
            )
            raise AssertionError(errmsg)

        # Step 4: Verify clear-cookie header
        headers = logout_response.get("headers", {})
        cookie_header = headers.get("Set-Cookie", "")

        if "Max-Age=0" not in cookie_header:
            errmsg = (
                "Iteration {}: Expected Max-Age=0 in logout Set-Cookie "
                "header, got {!r}".format(iteration, cookie_header)
            )
            raise AssertionError(errmsg)

        # Step 5: Verify session is removed from the store
        if use_store:
            if session_id in store._sessions:
                errmsg = (
                    "Iteration {}: Expected session to be removed from "
                    "store after logout. session_id={!r}".format(
                        iteration, session_id
                    )
                )
                raise AssertionError(errmsg)
        else:
            if session_id in blueprint._memory_store:
                errmsg = (
                    "Iteration {}: Expected session to be removed from "
                    "memory store after logout. session_id={!r}".format(
                        iteration, session_id
                    )
                )
                raise AssertionError(errmsg)

        # Step 6: Verify subsequent info request returns 401
        info_request = MockJsonRequest(
            {},
            cookies={"session_id": session_id}
        )
        info_response = blueprint.info(info_request)

        if info_response["status"] != 401:
            errmsg = (
                "Iteration {}: Expected info status 401 after logout, "
                "got {}. session_id={!r}".format(
                    iteration, info_response["status"], session_id
                )
            )
            raise AssertionError(errmsg)

    return
