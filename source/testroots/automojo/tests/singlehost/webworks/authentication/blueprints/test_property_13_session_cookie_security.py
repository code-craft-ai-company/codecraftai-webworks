"""
    Property test for session cookie security.

    Property 13: Session Cookie Security
        For any successful login via SessionAuthBlueprint, the response
        SHALL set a cookie with HttpOnly, Secure (when configured), and
        SameSite attributes.

    **Validates: Requirements 5.4**
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


SAMESITE_OPTIONS = ["Strict", "Lax", "None"]


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


def _random_cookie_name():
    """
        Generate a random cookie name.

        :returns: A random cookie name string using alphanumeric and
                  underscore characters.
    """
    length = random.randint(3, 20)
    chars = string.ascii_letters + string.digits + "_"
    name = "".join(random.choice(chars) for _ in range(length))
    return name


def _create_fresh_blueprint(
    cookie_secure,
    cookie_httponly,
    cookie_samesite,
    cookie_name,
    session_duration,
    remember_me,
    known_users
):
    """
        Create a fresh SessionAuthBlueprint subclass with the given
        configuration to avoid class-level state leakage.

        :param cookie_secure: Whether to set the Secure flag.
        :param cookie_httponly: Whether to set the HttpOnly flag.
        :param cookie_samesite: The SameSite attribute value.
        :param cookie_name: The cookie name.
        :param session_duration: Session lifetime in seconds.
        :param remember_me: Whether to use remember_me_duration.
        :param known_users: Dictionary mapping (username, password) to Principal.

        :returns: The fresh blueprint class.
    """

    class FreshBlueprint(SessionAuthBlueprint):
        pass

    FreshBlueprint.identity_provider = MockIdentityProvider(known_users)
    FreshBlueprint.session_store = None
    FreshBlueprint.session_duration = session_duration
    FreshBlueprint.remember_me_duration = session_duration * 10
    FreshBlueprint.cookie_name = cookie_name
    FreshBlueprint.cookie_secure = cookie_secure
    FreshBlueprint.cookie_httponly = cookie_httponly
    FreshBlueprint.cookie_samesite = cookie_samesite
    FreshBlueprint.enabled_endpoints = None
    FreshBlueprint.auth_system = None
    FreshBlueprint.base_path = "/auth/session"
    FreshBlueprint._memory_store = {}

    return FreshBlueprint


# =============================================================================
# Property Tests
# =============================================================================

def test_property_13_session_cookie_security():
    """
        Property 13: Session Cookie Security.

        For any successful login via SessionAuthBlueprint, the response
        SHALL set a cookie with HttpOnly, Secure (when configured), and
        SameSite attributes.

        For each iteration:
        1. Generate random cookie configuration (secure, httponly, samesite,
           cookie name, session duration).
        2. Generate random valid credentials.
        3. Perform a login request.
        4. Verify the Set-Cookie header is present.
        5. When cookie_httponly is True, verify HttpOnly is in the cookie.
        6. When cookie_secure is True, verify Secure is in the cookie.
        7. When cookie_samesite is set, verify SameSite=<value> is in the cookie.
        8. Verify the cookie name matches the configured name.

        **Validates: Requirements 5.4**
    """
    num_iterations = 100

    for iteration in range(num_iterations):
        # Generate random configuration
        cookie_secure = random.choice([True, False])
        cookie_httponly = random.choice([True, False])
        cookie_samesite = random.choice(SAMESITE_OPTIONS + [""])
        cookie_name = _random_cookie_name()
        session_duration = random.randint(60, 86400)
        remember_me = random.choice([True, False])

        # Generate random credentials
        username = _random_string(3, 20)
        password = _random_string(6, 30)
        principal_id = _random_string(5, 15)

        principal = Principal(
            identifier=principal_id,
            display_name="User {}".format(principal_id),
        )

        known_users = {(username, password): principal}

        blueprint = _create_fresh_blueprint(
            cookie_secure=cookie_secure,
            cookie_httponly=cookie_httponly,
            cookie_samesite=cookie_samesite,
            cookie_name=cookie_name,
            session_duration=session_duration,
            remember_me=remember_me,
            known_users=known_users,
        )

        # Perform login
        request_body = {
            "username": username,
            "password": password,
            "remember_me": remember_me,
        }
        request = MockJsonRequest(request_body)
        response = blueprint.login(request)

        # Verify login succeeded
        if response["status"] != 200:
            errmsg = (
                "Iteration {}: Expected status 200, got {}. "
                "username={!r}".format(
                    iteration, response["status"], username
                )
            )
            raise AssertionError(errmsg)

        # Verify Set-Cookie header is present
        headers = response.get("headers", {})
        cookie_header = headers.get("Set-Cookie", "")

        if not cookie_header:
            errmsg = (
                "Iteration {}: Expected Set-Cookie header in response".format(
                    iteration
                )
            )
            raise AssertionError(errmsg)

        # Verify cookie name
        expected_prefix = "{}=".format(cookie_name)
        if not cookie_header.startswith(expected_prefix):
            errmsg = (
                "Iteration {}: Expected cookie to start with {!r}, "
                "got {!r}".format(
                    iteration, expected_prefix, cookie_header
                )
            )
            raise AssertionError(errmsg)

        # Verify HttpOnly when configured
        if cookie_httponly:
            if "HttpOnly" not in cookie_header:
                errmsg = (
                    "Iteration {}: Expected HttpOnly in Set-Cookie when "
                    "cookie_httponly=True, got {!r}".format(
                        iteration, cookie_header
                    )
                )
                raise AssertionError(errmsg)
        else:
            if "HttpOnly" in cookie_header:
                errmsg = (
                    "Iteration {}: Expected no HttpOnly in Set-Cookie when "
                    "cookie_httponly=False, got {!r}".format(
                        iteration, cookie_header
                    )
                )
                raise AssertionError(errmsg)

        # Verify Secure when configured
        if cookie_secure:
            if "Secure" not in cookie_header:
                errmsg = (
                    "Iteration {}: Expected Secure in Set-Cookie when "
                    "cookie_secure=True, got {!r}".format(
                        iteration, cookie_header
                    )
                )
                raise AssertionError(errmsg)
        else:
            # Ensure "Secure" is not present as a standalone attribute
            # (it could appear as part of cookie_name, so check carefully)
            parts = [p.strip() for p in cookie_header.split(";")]
            has_secure = any(p == "Secure" for p in parts)
            if has_secure:
                errmsg = (
                    "Iteration {}: Expected no Secure in Set-Cookie when "
                    "cookie_secure=False, got {!r}".format(
                        iteration, cookie_header
                    )
                )
                raise AssertionError(errmsg)

        # Verify SameSite when configured
        if cookie_samesite:
            expected_samesite = "SameSite={}".format(cookie_samesite)
            if expected_samesite not in cookie_header:
                errmsg = (
                    "Iteration {}: Expected {!r} in Set-Cookie when "
                    "cookie_samesite={!r}, got {!r}".format(
                        iteration, expected_samesite,
                        cookie_samesite, cookie_header
                    )
                )
                raise AssertionError(errmsg)
        else:
            if "SameSite=" in cookie_header:
                errmsg = (
                    "Iteration {}: Expected no SameSite in Set-Cookie when "
                    "cookie_samesite is empty, got {!r}".format(
                        iteration, cookie_header
                    )
                )
                raise AssertionError(errmsg)

    return
