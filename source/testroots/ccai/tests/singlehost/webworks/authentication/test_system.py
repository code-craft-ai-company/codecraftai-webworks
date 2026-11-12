"""
    Tests for the AuthenticationSystem module.
    
    This module contains unit tests for the challenge handling of the
    AuthenticationSystem: what a request without credentials, or with
    rejected credentials, is told about how to authenticate.
"""

import asyncio
from typing import Any, Dict, Optional

from ccai.webworks.authentication import (
    AuthenticationResult,
    AuthenticationStatus,
    BasicAuthenticator,
    BearerAuthenticator,
    DigestAuthenticator,
    Principal,
)
from ccai.webworks.authentication.basic import create_basic_auth_header
from ccai.webworks.authentication.system import AuthenticationSystem


# =============================================================================
# Test Helpers
# =============================================================================

class StaticIdentityProvider:
    """
        An identity provider that knows a single username and password.
    """
    
    async def validate_credentials(self, username: str, password: str) -> Optional[Principal]:
        if username == "alice" and password == "secret":
            return Principal(identifier=username)
        return None
    
    async def get_principal(self, identifier: str) -> Optional[Principal]:
        return None


class EmptyDigestIdentityProvider:
    """
        A Digest identity provider that knows no users.
    """
    
    async def get_ha1(self, username: str, realm: str, algorithm: str = "MD5") -> Optional[str]:
        return None
    
    async def get_principal(self, username: str, realm: str) -> Optional[Principal]:
        return None


class BodySigningAuthenticator:
    """
        An authenticator that declares it needs the request body.
    """
    
    requires_body = True
    
    @property
    def scheme(self) -> str:
        return "Signed"
    
    def can_handle(self, request: Any) -> bool:
        return False
    
    async def authenticate(self, request: Any) -> AuthenticationResult:
        return AuthenticationResult(status=AuthenticationStatus.SKIP)


def run_async(coro):
    """
        Run an async coroutine synchronously for testing.
    """
    return asyncio.run(coro)


def create_request(headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """
        Create a dict-shaped request.
    """
    return {"headers": headers or {}, "method": "GET", "path": "/"}


# =============================================================================
# Challenge Tests
# =============================================================================

def test_request_without_credentials_gets_basic_challenge():
    """
        Test that a request without credentials is refused with the Basic
        challenge attached, although the Basic authenticator cannot handle
        a request that has no Authorization header.
    """
    system = AuthenticationSystem()
    system.register(BasicAuthenticator(StaticIdentityProvider(), realm="Site"))
    
    result = run_async(system.authenticate(create_request()))
    
    if result.status != AuthenticationStatus.FAILURE:
        errmsg = f"Expected FAILURE, got {result.status}"
        raise AssertionError(errmsg)
    
    if result.error_code != "no_credentials":
        errmsg = f"Expected no_credentials, got {result.error_code}"
        raise AssertionError(errmsg)
    
    if result.challenge != 'Basic realm="Site"':
        errmsg = f"Expected the Basic challenge, got {result.challenge!r}"
        raise AssertionError(errmsg)
    
    return


def test_request_without_credentials_gets_digest_nonce():
    """
        Test that a request without credentials receives a Digest challenge
        carrying a nonce, without which a Digest client cannot start.
    """
    system = AuthenticationSystem()
    system.register(DigestAuthenticator(EmptyDigestIdentityProvider()))
    
    result = run_async(system.authenticate(create_request()))
    
    if result.challenge is None or 'nonce="' not in result.challenge:
        errmsg = f"Expected a Digest challenge with a nonce, got {result.challenge!r}"
        raise AssertionError(errmsg)
    
    return


def test_challenges_of_all_capable_authenticators_are_combined():
    """
        Test that every challenge-capable authenticator contributes to the
        challenge, in priority order.
    """
    system = AuthenticationSystem()
    system.register(BasicAuthenticator(StaticIdentityProvider(), realm="Site"), priority=10)
    system.register(BearerAuthenticator(jwt_secret="secret", realm="API"), priority=20)
    
    result = run_async(system.authenticate(create_request()))
    
    expected = 'Bearer realm="API", Basic realm="Site"'
    if result.challenge != expected:
        errmsg = f"Expected {expected!r}, got {result.challenge!r}"
        raise AssertionError(errmsg)
    
    return


def test_rejected_credentials_carry_a_challenge():
    """
        Test that a definitive failure also carries the challenge, so a
        browser prompts again after a wrong password.
    """
    system = AuthenticationSystem()
    system.register(BasicAuthenticator(StaticIdentityProvider(), realm="Site"))
    
    request = create_request({"Authorization": create_basic_auth_header("alice", "wrong")})
    result = run_async(system.authenticate(request))
    
    if result.error_code != "invalid_credentials":
        errmsg = f"Expected invalid_credentials, got {result.error_code}"
        raise AssertionError(errmsg)
    
    if result.challenge != 'Basic realm="Site"':
        errmsg = f"Expected the Basic challenge, got {result.challenge!r}"
        raise AssertionError(errmsg)
    
    return


def test_get_challenge_is_none_without_challenge_capable_authenticator():
    """
        Test that a system whose authenticators cannot issue challenges
        reports none.
    """
    system = AuthenticationSystem()
    system.register(BodySigningAuthenticator())
    
    if system.get_challenge() is not None:
        errmsg = f"Expected None, got {system.get_challenge()!r}"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Body Requirement Tests
# =============================================================================

def test_requires_body_reflects_registered_authenticators():
    """
        Test that the system reports whether any authenticator needs the
        request body.
    """
    system = AuthenticationSystem()
    system.register(BasicAuthenticator(StaticIdentityProvider()))
    
    if system.requires_body is not False:
        errmsg = "Expected requires_body to be False without a signing authenticator"
        raise AssertionError(errmsg)
    
    system.register(BodySigningAuthenticator())
    
    if system.requires_body is not True:
        errmsg = "Expected requires_body to be True with a signing authenticator"
        raise AssertionError(errmsg)
    
    return


if __name__ == "__main__":
    from ccai.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
