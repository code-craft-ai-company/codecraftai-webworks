"""
    Unit tests for BasicAuthBlueprint.

    This module verifies the login and logout endpoints of the
    BasicAuthBlueprint, in particular the ``issue_token`` option: a login
    that returns a signed access token and a logout that revokes it.
"""

import asyncio

from ccai.webworks.authentication.bearer import (
    BearerAuthenticator,
    InMemoryTokenRevocationList,
    decode_jwt,
)
from ccai.webworks.authentication.blueprints.basic import BasicAuthBlueprint
from ccai.webworks.authentication.core import AuthenticationStatus, Principal


# =============================================================================
# Test Helpers
# =============================================================================

JWT_SECRET = "test-secret-key-for-basic-tests"


class MockJsonRequest:
    """
        A simple mock request that returns a JSON body dictionary and
        carries headers.
    """

    def __init__(self, data, headers=None):
        self._data = data
        self.headers = headers or {}

    def json(self):
        return self._data


class SingleUserIdentityProvider:
    """
        A mock identity provider that knows about a single user.
    """

    async def validate_credentials(self, username, password):
        if username == "testuser" and password == "testpass":
            return Principal(identifier="user-123")
        return None

    async def get_principal(self, identifier):
        return None


def _create_fresh_blueprint(issue_token=False, jwt_secret=JWT_SECRET):
    """
        Create a fresh BasicAuthBlueprint subclass to avoid class-level
        state leakage between tests.
    """
    class FreshBlueprint(BasicAuthBlueprint):
        pass

    FreshBlueprint.identity_provider = SingleUserIdentityProvider()
    FreshBlueprint.issue_token = issue_token
    FreshBlueprint.jwt_secret = jwt_secret
    FreshBlueprint.enabled_endpoints = None
    FreshBlueprint.auth_system = None
    FreshBlueprint.base_path = "/auth/basic"
    FreshBlueprint.revocation_list = InMemoryTokenRevocationList()

    return FreshBlueprint


def _login(blueprint):
    """
        Log the known user in.
    """
    response = blueprint.login(
        MockJsonRequest({"username": "testuser", "password": "testpass"})
    )
    return response


# =============================================================================
# Login
# =============================================================================

def test_login_without_issue_token_returns_no_token():
    """
        Verify that the default login confirms the credentials without
        issuing a token.
    """
    blueprint = _create_fresh_blueprint(issue_token=False)

    response = _login(blueprint)

    if response["status"] != 200 or response["body"].get("authenticated") is not True:
        errmsg = "Expected a successful login, got {} {!r}".format(
            response["status"], response["body"]
        )
        raise AssertionError(errmsg)

    if "access_token" in response["body"]:
        errmsg = "Expected no access token when issue_token is off"
        raise AssertionError(errmsg)

    return


def test_login_with_issue_token_returns_signed_access_token():
    """
        Verify that issue_token makes a successful login return a JWT
        access token for the authenticated principal.
    """
    blueprint = _create_fresh_blueprint(issue_token=True)

    response = _login(blueprint)

    if response["status"] != 200:
        errmsg = "Expected status 200, got {}".format(response["status"])
        raise AssertionError(errmsg)

    body = response["body"]

    if body.get("token_type") != "Bearer" or not body.get("expires_in"):
        errmsg = "Expected token_type and expires_in in the body, got {!r}".format(body)
        raise AssertionError(errmsg)

    claims = decode_jwt(body["access_token"], JWT_SECRET, algorithms=["HS256"])

    if claims.get("sub") != "user-123":
        errmsg = "Expected sub 'user-123', got {!r}".format(claims.get("sub"))
        raise AssertionError(errmsg)

    if claims.get("token_type") != "access":
        errmsg = "Expected an access token, got token_type {!r}".format(claims.get("token_type"))
        raise AssertionError(errmsg)

    return


def test_login_with_issue_token_but_no_secret_fails_closed():
    """
        Verify that a login that should issue a token does not report
        success when no signing secret is configured.
    """
    blueprint = _create_fresh_blueprint(issue_token=True, jwt_secret=None)

    response = _login(blueprint)

    if response["status"] != 500:
        errmsg = "Expected status 500, got {}".format(response["status"])
        raise AssertionError(errmsg)

    return


def test_login_rejects_non_object_body():
    """
        Verify that a JSON body that is not an object is answered with 400.
    """
    blueprint = _create_fresh_blueprint()

    response = blueprint.login(MockJsonRequest("testuser:testpass"))

    if response["status"] != 400:
        errmsg = "Expected status 400, got {}".format(response["status"])
        raise AssertionError(errmsg)

    return


# =============================================================================
# Logout
# =============================================================================

def test_logout_revokes_the_presented_access_token():
    """
        Verify that logout puts the presented access token on the
        revocation list, so a BearerAuthenticator sharing the list
        refuses it afterwards.
    """
    blueprint = _create_fresh_blueprint(issue_token=True)

    access_token = _login(blueprint)["body"]["access_token"]

    authenticator = BearerAuthenticator(
        jwt_secret=JWT_SECRET,
        revocation_list=blueprint.get_revocation_list()
    )
    bearer_request = {"headers": {"Authorization": "Bearer {}".format(access_token)}}

    before = asyncio.run(authenticator.authenticate(bearer_request))
    if before.status != AuthenticationStatus.SUCCESS:
        errmsg = "Expected the token to authenticate before logout, got {}".format(before.status)
        raise AssertionError(errmsg)

    response = blueprint.logout(MockJsonRequest(
        {}, headers={"Authorization": "Bearer {}".format(access_token)}
    ))

    if response["status"] != 200:
        errmsg = "Expected status 200, got {}".format(response["status"])
        raise AssertionError(errmsg)

    after = asyncio.run(authenticator.authenticate(bearer_request))
    if after.status != AuthenticationStatus.FAILURE:
        errmsg = "Expected the token to be refused after logout, got {}".format(after.status)
        raise AssertionError(errmsg)

    return


if __name__ == "__main__":
    from ccai.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
