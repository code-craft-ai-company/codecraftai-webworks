"""
    Tests for the AuthenticationMiddleware module.
    
    This module contains unit tests and property-based tests for the
    AuthenticationMiddleware class which integrates authentication
    into the ASGI request pipeline.
"""

import asyncio
import random
import string
import time
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Set

from ccai.webworks.authentication import (
    AuthenticationStatus,
    AuthenticationResult,
    Principal,
    AuthenticationContext
)
from ccai.webworks.authentication.basic import (
    BasicAuthenticator,
    create_basic_auth_header
)
from ccai.webworks.authentication.digest import DigestAuthenticator
from ccai.webworks.authentication.hmac_auth import (
    HMACAuthenticator,
    compute_hmac_signature,
    create_hmac_auth_header
)
from ccai.webworks.authentication.middleware import (
    AuthenticationMiddleware,
    create_authentication_middleware
)
from ccai.webworks.authentication.session import (
    InMemorySessionStore,
    SessionAuthenticator
)
from ccai.webworks.authentication.system import AuthenticationSystem
from ccai.webworks.endpoints.accesspolicy import AccessPolicy
from ccai.webworks.routing.request import Request


KNOWN_USERNAME = "alice"
KNOWN_PASSWORD = "correct horse"


class StaticIdentityProvider:
    """
        An identity provider that knows a single username and password.
    """
    
    async def validate_credentials(self, username: str, password: str) -> Optional[Principal]:
        if username == KNOWN_USERNAME and password == KNOWN_PASSWORD:
            return Principal(identifier=username)
        return None
    
    async def get_principal(self, identifier: str) -> Optional[Principal]:
        if identifier == KNOWN_USERNAME:
            return Principal(identifier=identifier)
        return None


class StaticDigestIdentityProvider:
    """
        A Digest identity provider that knows no users.
    """
    
    async def get_ha1(self, username: str, realm: str, algorithm: str = "MD5") -> Optional[str]:
        return None
    
    async def get_principal(self, username: str, realm: str) -> Optional[Principal]:
        return None


class StaticHMACKeyStore:
    """
        An HMAC key store backed by a dictionary of key id to secret.
    """
    
    def __init__(self, secrets_by_key_id: Dict[str, str]):
        self._secrets = secrets_by_key_id
    
    async def get_secret(self, key_id: str) -> Optional[str]:
        return self._secrets.get(key_id)
    
    async def get_principal(self, key_id: str) -> Optional[Principal]:
        return None


# =============================================================================
# Test Data Generators
# =============================================================================

def generate_random_string(min_length: int = 1, max_length: int = 50) -> str:
    """
        Generate a random string of alphanumeric characters.
    """
    length = random.randint(min_length, max_length)
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def generate_random_identifier() -> str:
    """
        Generate a random non-empty identifier string.
    """
    return generate_random_string(min_length=1, max_length=100)


def generate_random_roles() -> Set[str]:
    """
        Generate a random set of role strings.
    """
    num_roles = random.randint(0, 5)
    return {generate_random_string(1, 15) for _ in range(num_roles)}


def generate_random_permissions() -> Set[str]:
    """
        Generate a random set of permission strings.
    """
    num_permissions = random.randint(0, 5)
    return {generate_random_string(1, 20) for _ in range(num_permissions)}


def generate_random_attributes() -> Dict[str, Any]:
    """
        Generate a random dictionary of attributes.
    """
    num_attrs = random.randint(0, 3)
    attrs = {}
    for _ in range(num_attrs):
        key = generate_random_string(1, 15)
        attrs[key] = generate_random_string(1, 20)
    return attrs


def generate_random_scheme() -> str:
    """
        Generate a random authentication scheme name.
    """
    schemes = ["Basic", "Bearer", "Digest", "APIKey", "OAuth2", "OIDC", "HMAC", "Session"]
    return random.choice(schemes)


def generate_random_path() -> str:
    """
        Generate a random URL path.
    """
    num_segments = random.randint(1, 4)
    segments = [generate_random_string(1, 15) for _ in range(num_segments)]
    return "/" + "/".join(segments)


def generate_random_principal() -> Principal:
    """
        Generate a random Principal instance with valid data.
    """
    identifier = generate_random_identifier()
    display_name = generate_random_string(1, 30) if random.choice([True, False]) else None
    roles = generate_random_roles()
    permissions = generate_random_permissions()
    attributes = generate_random_attributes()
    
    return Principal(
        identifier=identifier,
        display_name=display_name,
        roles=roles,
        permissions=permissions,
        attributes=attributes
    )


def generate_random_authentication_context() -> AuthenticationContext:
    """
        Generate a random AuthenticationContext instance with valid data.
    """
    principal = generate_random_principal()
    scheme = generate_random_scheme()
    authenticated_at = datetime.utcnow() - timedelta(seconds=random.randint(0, 3600))
    
    # Expiration in the future
    if random.choice([True, False]):
        expires_at = datetime.utcnow() + timedelta(seconds=random.randint(60, 86400))
    else:
        expires_at = None
    
    attributes = generate_random_attributes()
    
    return AuthenticationContext(
        principal=principal,
        scheme=scheme,
        authenticated_at=authenticated_at,
        expires_at=expires_at,
        attributes=attributes
    )


# =============================================================================
# Mock Authenticator
# =============================================================================

class MockAuthenticator:
    """
        A mock authenticator for testing the middleware.
        
        This authenticator can be configured to return specific results
        for testing the AuthenticationMiddleware behavior.
    """
    
    def __init__(
        self,
        scheme_name: str,
        can_handle_result: bool = True,
        auth_result: Optional[AuthenticationResult] = None
    ):
        self._scheme_name = scheme_name
        self._can_handle_result = can_handle_result
        self._auth_result = auth_result or AuthenticationResult(
            status=AuthenticationStatus.SKIP
        )
        self._authenticate_called = False
        self._last_request = None
    
    @property
    def scheme(self) -> str:
        return self._scheme_name
    
    def can_handle(self, request: Any) -> bool:
        return self._can_handle_result
    
    async def authenticate(self, request: Any) -> AuthenticationResult:
        self._authenticate_called = True
        self._last_request = request
        return self._auth_result
    
    @property
    def was_authenticate_called(self) -> bool:
        return self._authenticate_called
    
    def reset(self):
        self._authenticate_called = False
        self._last_request = None
    
    def set_result(self, result: AuthenticationResult):
        self._auth_result = result


# =============================================================================
# Mock ASGI Application
# =============================================================================

class MockASGIApp:
    """
        A mock ASGI application for testing the middleware.
        
        Records whether it was called and captures the scope.
    """
    
    def __init__(self):
        self._called = False
        self._scope: Optional[Dict[str, Any]] = None
        self._receive = None
        self._send = None
    
    async def __call__(
        self,
        scope: Dict[str, Any],
        receive: Callable,
        send: Callable
    ) -> None:
        self._called = True
        self._scope = scope
        self._receive = receive
        self._send = send
        return
    
    @property
    def was_called(self) -> bool:
        return self._called
    
    @property
    def captured_scope(self) -> Optional[Dict[str, Any]]:
        return self._scope
    
    def reset(self):
        self._called = False
        self._scope = None
        self._receive = None
        self._send = None


# =============================================================================
# Mock Send Callable
# =============================================================================

class MockSend:
    """
        A mock send callable that captures sent messages.
    """
    
    def __init__(self):
        self._messages: List[Dict[str, Any]] = []
    
    async def __call__(self, message: Dict[str, Any]) -> None:
        self._messages.append(message)
    
    @property
    def messages(self) -> List[Dict[str, Any]]:
        return self._messages
    
    def reset(self):
        self._messages = []


# =============================================================================
# Mock Receive Callable
# =============================================================================

class MockReceive:
    """
        A mock receive callable.
    """
    
    async def __call__(self) -> Dict[str, Any]:
        return {"type": "http.request", "body": b""}


# =============================================================================
# Helper Functions
# =============================================================================

def run_async(coro):
    """
        Run an async coroutine synchronously for testing.
    """
    loop = asyncio.new_event_loop()
    try:
        return asyncio.run(coro)
    finally:
        loop.close()


def create_http_scope(
    path: str = "/",
    method: str = "GET",
    headers: Optional[List[tuple]] = None
) -> Dict[str, Any]:
    """
        Create a mock HTTP ASGI scope.
    """
    return {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": method,
        "scheme": "http",
        "path": path,
        "query_string": b"",
        "root_path": "",
        "headers": headers or [],
        "server": ("localhost", 8000),
    }


# =============================================================================
# Unit Tests for AuthenticationMiddleware
# =============================================================================

def test_middleware_creation():
    """
        Test that AuthenticationMiddleware can be created.
    """
    app = MockASGIApp()
    auth_system = AuthenticationSystem()
    
    middleware = AuthenticationMiddleware(app=app, auth_system=auth_system)
    
    if middleware.app is not app:
        errmsg = "Expected app to be the same instance"
        raise AssertionError(errmsg)
    
    if middleware.auth_system is not auth_system:
        errmsg = "Expected auth_system to be the same instance"
        raise AssertionError(errmsg)
    
    return


def test_middleware_default_exclude_paths():
    """
        Test that middleware has empty exclude_paths by default.
    """
    app = MockASGIApp()
    auth_system = AuthenticationSystem()
    
    middleware = AuthenticationMiddleware(app=app, auth_system=auth_system)
    
    if middleware.exclude_paths != set():
        errmsg = f"Expected empty exclude_paths, got {middleware.exclude_paths}"
        raise AssertionError(errmsg)
    
    return


def test_middleware_default_optional_paths():
    """
        Test that middleware has empty optional_paths by default.
    """
    app = MockASGIApp()
    auth_system = AuthenticationSystem()
    
    middleware = AuthenticationMiddleware(app=app, auth_system=auth_system)
    
    if middleware.optional_paths != set():
        errmsg = f"Expected empty optional_paths, got {middleware.optional_paths}"
        raise AssertionError(errmsg)
    
    return


def test_middleware_custom_exclude_paths():
    """
        Test that middleware accepts custom exclude_paths.
    """
    app = MockASGIApp()
    auth_system = AuthenticationSystem()
    exclude = {"/health", "/public"}
    
    middleware = AuthenticationMiddleware(
        app=app,
        auth_system=auth_system,
        exclude_paths=exclude
    )
    
    if middleware.exclude_paths != exclude:
        errmsg = f"Expected exclude_paths {exclude}, got {middleware.exclude_paths}"
        raise AssertionError(errmsg)
    
    return


def test_middleware_custom_optional_paths():
    """
        Test that middleware accepts custom optional_paths.
    """
    app = MockASGIApp()
    auth_system = AuthenticationSystem()
    optional = {"/api/optional", "/maybe-auth"}
    
    middleware = AuthenticationMiddleware(
        app=app,
        auth_system=auth_system,
        optional_paths=optional
    )
    
    if middleware.optional_paths != optional:
        errmsg = f"Expected optional_paths {optional}, got {middleware.optional_paths}"
        raise AssertionError(errmsg)
    
    return


def test_middleware_passes_lifespan_scope():
    """
        Test that middleware passes scopes that carry no request (lifespan)
        directly to the app without authenticating them.
    """
    app = MockASGIApp()
    auth_system = AuthenticationSystem()
    middleware = AuthenticationMiddleware(app=app, auth_system=auth_system)
    
    scope = {"type": "lifespan", "asgi": {"version": "3.0"}}
    receive = MockReceive()
    send = MockSend()
    
    run_async(middleware(scope, receive, send))
    
    if not app.was_called:
        errmsg = "Expected app to be called for lifespan scope"
        raise AssertionError(errmsg)
    
    if "auth" in scope:
        errmsg = "Expected no 'auth' key on a lifespan scope"
        raise AssertionError(errmsg)
    
    return


def create_websocket_scope(
    path: str = "/ws",
    headers: Optional[List[tuple]] = None
) -> Dict[str, Any]:
    """
        Create a mock WebSocket ASGI scope.
    """
    return {
        "type": "websocket",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "scheme": "ws",
        "path": path,
        "query_string": b"",
        "root_path": "",
        "headers": headers or [],
        "server": ("localhost", 8000),
        "subprotocols": [],
    }


def test_middleware_rejects_websocket_without_credentials():
    """
        Test that a WebSocket handshake to a protected path is closed before
        it is accepted when it carries no credentials.
    """
    app = MockASGIApp()
    auth_system = AuthenticationSystem()
    auth_system.register(BasicAuthenticator(StaticIdentityProvider()))
    middleware = AuthenticationMiddleware(app=app, auth_system=auth_system)
    
    scope = create_websocket_scope()
    send = MockSend()
    
    run_async(middleware(scope, MockReceive(), send))
    
    if app.was_called:
        errmsg = "Expected app NOT to be called for an unauthenticated WebSocket"
        raise AssertionError(errmsg)
    
    if len(send.messages) != 1:
        errmsg = f"Expected exactly one message, got {send.messages}"
        raise AssertionError(errmsg)
    
    message = send.messages[0]
    if message.get("type") != "websocket.close":
        errmsg = f"Expected websocket.close, got {message}"
        raise AssertionError(errmsg)
    
    if message.get("code") != 1008:
        errmsg = f"Expected close code 1008, got {message.get('code')}"
        raise AssertionError(errmsg)
    
    return


def test_middleware_authenticates_websocket_scope():
    """
        Test that a WebSocket handshake with valid credentials reaches the
        app with the authentication context on the scope.
    """
    app = MockASGIApp()
    auth_system = AuthenticationSystem()
    auth_system.register(BasicAuthenticator(StaticIdentityProvider()))
    middleware = AuthenticationMiddleware(app=app, auth_system=auth_system)
    
    header_value = create_basic_auth_header(KNOWN_USERNAME, KNOWN_PASSWORD)
    scope = create_websocket_scope(
        headers=[(b"authorization", header_value.encode("latin-1"))]
    )
    
    run_async(middleware(scope, MockReceive(), MockSend()))
    
    if not app.was_called:
        errmsg = "Expected app to be called for an authenticated WebSocket"
        raise AssertionError(errmsg)
    
    context = app.captured_scope.get("auth")
    if context is None or context.principal.identifier != KNOWN_USERNAME:
        errmsg = f"Expected auth context for {KNOWN_USERNAME}, got {context}"
        raise AssertionError(errmsg)
    
    return


def test_middleware_closes_websocket_failing_access_policy():
    """
        Test that an authenticated WebSocket handshake that fails the path's
        access policy is closed before accept.
    """
    app = MockASGIApp()
    auth_system = AuthenticationSystem()
    auth_system.register(BasicAuthenticator(StaticIdentityProvider()))
    middleware = AuthenticationMiddleware(
        app=app,
        auth_system=auth_system,
        path_policies={"/ws": AccessPolicy(roles=["admin"])}
    )
    
    header_value = create_basic_auth_header(KNOWN_USERNAME, KNOWN_PASSWORD)
    scope = create_websocket_scope(
        headers=[(b"authorization", header_value.encode("latin-1"))]
    )
    send = MockSend()
    
    run_async(middleware(scope, MockReceive(), send))
    
    if app.was_called:
        errmsg = "Expected app NOT to be called when the policy denies access"
        raise AssertionError(errmsg)
    
    if send.messages[0].get("type") != "websocket.close":
        errmsg = f"Expected websocket.close, got {send.messages}"
        raise AssertionError(errmsg)
    
    return


def test_middleware_authenticates_basic_header_from_asgi_scope():
    """
        Test that a shipped authenticator works behind the middleware when
        the credentials arrive as real ASGI headers (a list of byte pairs).
    """
    app = MockASGIApp()
    auth_system = AuthenticationSystem()
    auth_system.register(BasicAuthenticator(StaticIdentityProvider()))
    middleware = AuthenticationMiddleware(app=app, auth_system=auth_system)
    
    header_value = create_basic_auth_header(KNOWN_USERNAME, KNOWN_PASSWORD)
    scope = create_http_scope(
        path="/protected",
        headers=[
            (b"host", b"localhost:8000"),
            (b"authorization", header_value.encode("latin-1")),
        ]
    )
    send = MockSend()
    
    run_async(middleware(scope, MockReceive(), send))
    
    if not app.was_called:
        errmsg = f"Expected app to be called, middleware sent {send.messages}"
        raise AssertionError(errmsg)
    
    context = app.captured_scope.get("auth")
    if context is None or context.principal.identifier != KNOWN_USERNAME:
        errmsg = f"Expected auth context for {KNOWN_USERNAME}, got {context}"
        raise AssertionError(errmsg)
    
    return


def test_middleware_authenticates_session_cookie_from_asgi_scope():
    """
        Test that the session authenticator finds its cookie when it arrives
        in the ASGI cookie header.
    """
    session_store = InMemorySessionStore()
    principal = Principal(identifier="cookie-user")
    session = run_async(session_store.create_session(principal))
    
    app = MockASGIApp()
    auth_system = AuthenticationSystem()
    auth_system.register(SessionAuthenticator(session_store, renew_on_access=False))
    middleware = AuthenticationMiddleware(app=app, auth_system=auth_system)
    
    cookie_header = f"theme=dark; session_id={session.session_id}"
    scope = create_http_scope(
        path="/protected",
        headers=[(b"cookie", cookie_header.encode("latin-1"))]
    )
    send = MockSend()
    
    run_async(middleware(scope, MockReceive(), send))
    
    if not app.was_called:
        errmsg = f"Expected app to be called, middleware sent {send.messages}"
        raise AssertionError(errmsg)
    
    context = app.captured_scope.get("auth")
    if context is None or context.principal.identifier != "cookie-user":
        errmsg = f"Expected auth context for cookie-user, got {context}"
        raise AssertionError(errmsg)
    
    return


def test_middleware_passes_request_object_to_authenticators():
    """
        Test that authenticators receive the framework Request, with the raw
        ASGI scope reachable through it.
    """
    app = MockASGIApp()
    auth_system = AuthenticationSystem()
    authenticator = MockAuthenticator("Mock")
    auth_system.register(authenticator)
    middleware = AuthenticationMiddleware(app=app, auth_system=auth_system)
    
    scope = create_http_scope(path="/protected", headers=[(b"x-test", b"1")])
    
    run_async(middleware(scope, MockReceive(), MockSend()))
    
    request = authenticator._last_request
    if not isinstance(request, Request):
        errmsg = f"Expected a Request, got {type(request).__name__}"
        raise AssertionError(errmsg)
    
    if request.headers.get("X-Test") != "1":
        errmsg = "Expected the ASGI header to be readable from the Request"
        raise AssertionError(errmsg)
    
    if request.scope is not scope:
        errmsg = "Expected request.scope to be the ASGI scope"
        raise AssertionError(errmsg)
    
    return


def get_response_header(messages: List[Dict[str, Any]], name: bytes) -> Optional[bytes]:
    """
        Find a header in the http.response.start message a middleware sent.
    """
    for message in messages:
        if message.get("type") == "http.response.start":
            for header_name, header_value in message.get("headers", []):
                if header_name == name:
                    return header_value
    return None


def test_middleware_sends_basic_challenge_without_credentials():
    """
        Test that a request without credentials gets a 401 that carries the
        Basic challenge, so a browser prompts for credentials.
    """
    app = MockASGIApp()
    auth_system = AuthenticationSystem()
    auth_system.register(BasicAuthenticator(StaticIdentityProvider(), realm="Site"))
    middleware = AuthenticationMiddleware(app=app, auth_system=auth_system)
    
    send = MockSend()
    run_async(middleware(create_http_scope(path="/protected"), MockReceive(), send))
    
    if send.messages[0].get("status") != 401:
        errmsg = f"Expected 401, got {send.messages[0]}"
        raise AssertionError(errmsg)
    
    challenge = get_response_header(send.messages, b"www-authenticate")
    if challenge != b'Basic realm="Site"':
        errmsg = f"Expected Basic challenge, got {challenge}"
        raise AssertionError(errmsg)
    
    return


def test_middleware_sends_digest_challenge_with_nonce_without_credentials():
    """
        Test that a request without credentials gets a Digest challenge with
        a nonce, which is how a Digest client starts the exchange.
    """
    app = MockASGIApp()
    auth_system = AuthenticationSystem()
    auth_system.register(DigestAuthenticator(StaticDigestIdentityProvider()))
    middleware = AuthenticationMiddleware(app=app, auth_system=auth_system)
    
    send = MockSend()
    run_async(middleware(create_http_scope(path="/protected"), MockReceive(), send))
    
    challenge = get_response_header(send.messages, b"www-authenticate")
    if challenge is None or not challenge.startswith(b"Digest ") or b"nonce=" not in challenge:
        errmsg = f"Expected a Digest challenge with a nonce, got {challenge}"
        raise AssertionError(errmsg)
    
    return


def test_middleware_sends_challenge_when_credentials_are_wrong():
    """
        Test that a 401 for rejected credentials also carries
        WWW-Authenticate.
    """
    app = MockASGIApp()
    auth_system = AuthenticationSystem()
    auth_system.register(BasicAuthenticator(StaticIdentityProvider()))
    middleware = AuthenticationMiddleware(app=app, auth_system=auth_system)
    
    header_value = create_basic_auth_header(KNOWN_USERNAME, "wrong")
    scope = create_http_scope(
        path="/protected",
        headers=[(b"authorization", header_value.encode("latin-1"))]
    )
    send = MockSend()
    run_async(middleware(scope, MockReceive(), send))
    
    if send.messages[0].get("status") != 401:
        errmsg = f"Expected 401, got {send.messages[0]}"
        raise AssertionError(errmsg)
    
    if get_response_header(send.messages, b"www-authenticate") is None:
        errmsg = "Expected WWW-Authenticate on the 401 for wrong credentials"
        raise AssertionError(errmsg)
    
    return


def test_middleware_401_names_registered_schemes_without_challenge_source():
    """
        Test that a 401 carries WWW-Authenticate even when no registered
        authenticator can produce a challenge.
    """
    app = MockASGIApp()
    auth_system = AuthenticationSystem()
    auth_system.register(MockAuthenticator("Custom", can_handle_result=False))
    middleware = AuthenticationMiddleware(app=app, auth_system=auth_system, realm="Site")
    
    send = MockSend()
    run_async(middleware(create_http_scope(path="/protected"), MockReceive(), send))
    
    challenge = get_response_header(send.messages, b"www-authenticate")
    if challenge != b'Custom realm="Site"':
        errmsg = f"Expected fallback challenge naming the scheme, got {challenge}"
        raise AssertionError(errmsg)
    
    return


def test_middleware_add_exclude_pattern_excludes_matching_paths():
    """
        Test that a glob registered with add_exclude_pattern excludes the
        paths it matches.
    """
    app = MockASGIApp()
    auth_system = AuthenticationSystem()
    auth_system.register(BasicAuthenticator(StaticIdentityProvider()))
    middleware = AuthenticationMiddleware(app=app, auth_system=auth_system)
    middleware.add_exclude_pattern("/auth/session/*")
    
    run_async(middleware(
        create_http_scope(path="/auth/session/login"), MockReceive(), MockSend()
    ))
    
    if not app.was_called:
        errmsg = "Expected the path matching the exclude pattern to reach the app"
        raise AssertionError(errmsg)
    
    return


def test_middleware_answers_429_when_authenticator_reports_throttling():
    """
        Test that a throttling failure from an authenticator becomes a 429
        with the Retry-After header the authenticator supplied.
    """
    app = MockASGIApp()
    auth_system = AuthenticationSystem()
    auth_system.register(MockAuthenticator(
        "Mock",
        auth_result=AuthenticationResult(
            status=AuthenticationStatus.FAILURE,
            error_code="rate_limit_exceeded",
            error_description="Too many authentication attempts",
            response_headers={"Retry-After": "30"}
        )
    ))
    middleware = AuthenticationMiddleware(app=app, auth_system=auth_system)
    
    send = MockSend()
    run_async(middleware(create_http_scope(path="/protected"), MockReceive(), send))
    
    if send.messages[0].get("status") != 429:
        errmsg = f"Expected 429, got {send.messages[0]}"
        raise AssertionError(errmsg)
    
    if get_response_header(send.messages, b"retry-after") != b"30":
        errmsg = "Expected Retry-After: 30 on the 429"
        raise AssertionError(errmsg)
    
    return


def test_middleware_adds_authenticator_response_headers_on_success():
    """
        Test that headers an authenticator asks for on success (a renewed
        session cookie) are added to the application's response.
    """
    context = generate_random_authentication_context()
    auth_system = AuthenticationSystem()
    auth_system.register(MockAuthenticator(
        "Mock",
        auth_result=AuthenticationResult(
            status=AuthenticationStatus.SUCCESS,
            context=context,
            response_headers={"Set-Cookie": "session_id=abc; Max-Age=60"}
        )
    ))
    
    async def responding_app(scope, receive, send):
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b"ok"})
    
    middleware = AuthenticationMiddleware(app=responding_app, auth_system=auth_system)
    
    send = MockSend()
    run_async(middleware(create_http_scope(path="/protected"), MockReceive(), send))
    
    cookie = get_response_header(send.messages, b"set-cookie")
    if cookie != b"session_id=abc; Max-Age=60":
        errmsg = f"Expected the renewed cookie on the response, got {cookie}"
        raise AssertionError(errmsg)
    
    return


class BodyReceive:
    """
        A receive callable that delivers a request body in two chunks.
    """
    
    def __init__(self, chunks: List[bytes]):
        self._chunks = list(chunks)
    
    async def __call__(self) -> Dict[str, Any]:
        chunk = self._chunks.pop(0)
        return {
            "type": "http.request",
            "body": chunk,
            "more_body": len(self._chunks) > 0
        }


def test_middleware_buffers_and_replays_body_for_signing_authenticator():
    """
        Test that the middleware hands the whole body to an HMAC
        authenticator and replays it to the application.
    """
    secret = "signing-secret"
    body = b'{"amount": 10}'
    timestamp = str(time.time())
    headers = {"host": "localhost:8000"}
    signature = compute_hmac_signature(
        secret=secret,
        method="POST",
        path="/payments",
        timestamp=timestamp,
        headers=headers,
        signed_headers=["host"],
        query_string="",
        body=body
    )
    auth_header = create_hmac_auth_header(
        "key-1", signature, timestamp, signed_headers=["host"]
    )
    
    received_bodies = []
    
    async def reading_app(scope, receive, send):
        message = await receive()
        received_bodies.append(message.get("body"))
    
    auth_system = AuthenticationSystem()
    auth_system.register(HMACAuthenticator(
        StaticHMACKeyStore({"key-1": secret}), signed_headers=["host"]
    ))
    middleware = AuthenticationMiddleware(app=reading_app, auth_system=auth_system)
    
    scope = create_http_scope(
        path="/payments",
        method="POST",
        headers=[
            (b"host", b"localhost:8000"),
            (b"authorization", auth_header.encode("latin-1")),
        ]
    )
    send = MockSend()
    
    run_async(middleware(scope, BodyReceive([body[:5], body[5:]]), send))
    
    if received_bodies != [body]:
        errmsg = (
            f"Expected the app to receive the replayed body, got "
            f"{received_bodies}; middleware sent {send.messages}"
        )
        raise AssertionError(errmsg)
    
    return


def test_middleware_refuses_body_over_limit_for_signing_authenticator():
    """
        Test that a body larger than max_body_bytes is refused with 413
        instead of being buffered.
    """
    app = MockASGIApp()
    auth_system = AuthenticationSystem()
    auth_system.register(HMACAuthenticator(StaticHMACKeyStore({})))
    middleware = AuthenticationMiddleware(
        app=app, auth_system=auth_system, max_body_bytes=4
    )
    
    send = MockSend()
    run_async(middleware(
        create_http_scope(path="/payments", method="POST"),
        BodyReceive([b"0123456789"]),
        send
    ))
    
    if app.was_called:
        errmsg = "Expected app NOT to be called for an oversized body"
        raise AssertionError(errmsg)
    
    if send.messages[0].get("status") != 413:
        errmsg = f"Expected 413, got {send.messages[0]}"
        raise AssertionError(errmsg)
    
    return


def test_middleware_excludes_path():
    """
        Test that middleware excludes configured paths from authentication.
    """
    app = MockASGIApp()
    auth_system = AuthenticationSystem()
    middleware = AuthenticationMiddleware(
        app=app,
        auth_system=auth_system,
        exclude_paths={"/health"}
    )
    
    scope = create_http_scope(path="/health")
    receive = MockReceive()
    send = MockSend()
    
    run_async(middleware(scope, receive, send))
    
    if not app.was_called:
        errmsg = "Expected app to be called for excluded path"
        raise AssertionError(errmsg)
    
    # Auth should be None for excluded paths
    if app.captured_scope.get("auth") is not None:
        errmsg = "Expected auth to be None for excluded path"
        raise AssertionError(errmsg)
    
    return


def test_middleware_attaches_context_on_success():
    """
        Test that middleware attaches AuthenticationContext on successful auth.
    """
    app = MockASGIApp()
    auth_system = AuthenticationSystem()
    
    # Create a successful authentication result
    principal = Principal(identifier="testuser", display_name="Test User")
    context = AuthenticationContext(principal=principal, scheme="Basic")
    success_result = AuthenticationResult(
        status=AuthenticationStatus.SUCCESS,
        context=context
    )
    
    # Register mock authenticator
    mock_auth = MockAuthenticator(
        scheme_name="Basic",
        can_handle_result=True,
        auth_result=success_result
    )
    auth_system.register(mock_auth)
    
    middleware = AuthenticationMiddleware(app=app, auth_system=auth_system)
    
    scope = create_http_scope(path="/protected")
    receive = MockReceive()
    send = MockSend()
    
    run_async(middleware(scope, receive, send))
    
    if not app.was_called:
        errmsg = "Expected app to be called on successful authentication"
        raise AssertionError(errmsg)
    
    # Verify context is attached
    attached_auth = app.captured_scope.get("auth")
    if attached_auth is None:
        errmsg = "Expected auth context to be attached to scope"
        raise AssertionError(errmsg)
    
    if attached_auth is not context:
        errmsg = "Expected attached auth to be the same context instance"
        raise AssertionError(errmsg)
    
    return


def test_middleware_sends_401_on_failure():
    """
        Test that middleware sends 401 response on authentication failure.
    """
    app = MockASGIApp()
    auth_system = AuthenticationSystem()
    
    # Create a failure result
    failure_result = AuthenticationResult(
        status=AuthenticationStatus.FAILURE,
        error_code="invalid_credentials",
        error_description="Invalid credentials"
    )
    
    mock_auth = MockAuthenticator(
        scheme_name="Basic",
        can_handle_result=True,
        auth_result=failure_result
    )
    auth_system.register(mock_auth)
    
    middleware = AuthenticationMiddleware(app=app, auth_system=auth_system)
    
    scope = create_http_scope(path="/protected")
    receive = MockReceive()
    send = MockSend()
    
    run_async(middleware(scope, receive, send))
    
    # App should NOT be called on failure
    if app.was_called:
        errmsg = "Expected app NOT to be called on authentication failure"
        raise AssertionError(errmsg)
    
    # Check response was sent
    if len(send.messages) < 2:
        errmsg = f"Expected at least 2 messages (start + body), got {len(send.messages)}"
        raise AssertionError(errmsg)
    
    # Check status code
    start_msg = send.messages[0]
    if start_msg.get("status") != 401:
        errmsg = f"Expected status 401, got {start_msg.get('status')}"
        raise AssertionError(errmsg)
    
    return


def test_middleware_sends_challenge_on_protected_path():
    """
        Test that middleware sends challenge response for protected paths.
    """
    app = MockASGIApp()
    auth_system = AuthenticationSystem()
    
    # Create a challenge result
    challenge_result = AuthenticationResult(
        status=AuthenticationStatus.CHALLENGE,
        challenge='Basic realm="Test"'
    )
    
    mock_auth = MockAuthenticator(
        scheme_name="Basic",
        can_handle_result=True,
        auth_result=challenge_result
    )
    auth_system.register(mock_auth)
    
    middleware = AuthenticationMiddleware(app=app, auth_system=auth_system)
    
    scope = create_http_scope(path="/protected")
    receive = MockReceive()
    send = MockSend()
    
    run_async(middleware(scope, receive, send))
    
    # App should NOT be called when challenge is required
    if app.was_called:
        errmsg = "Expected app NOT to be called when challenge is required"
        raise AssertionError(errmsg)
    
    # Check 401 response with WWW-Authenticate header
    start_msg = send.messages[0]
    if start_msg.get("status") != 401:
        errmsg = f"Expected status 401, got {start_msg.get('status')}"
        raise AssertionError(errmsg)
    
    # Check for WWW-Authenticate header
    headers = dict(start_msg.get("headers", []))
    if b"www-authenticate" not in headers:
        errmsg = "Expected WWW-Authenticate header in challenge response"
        raise AssertionError(errmsg)
    
    return


def test_middleware_allows_optional_path_without_auth():
    """
        Test that middleware allows access to optional paths without auth.
    """
    app = MockASGIApp()
    auth_system = AuthenticationSystem()
    
    # Create a challenge result (no credentials provided)
    challenge_result = AuthenticationResult(
        status=AuthenticationStatus.CHALLENGE,
        challenge='Basic realm="Test"'
    )
    
    mock_auth = MockAuthenticator(
        scheme_name="Basic",
        can_handle_result=True,
        auth_result=challenge_result
    )
    auth_system.register(mock_auth)
    
    middleware = AuthenticationMiddleware(
        app=app,
        auth_system=auth_system,
        optional_paths={"/optional"}
    )
    
    scope = create_http_scope(path="/optional")
    receive = MockReceive()
    send = MockSend()
    
    run_async(middleware(scope, receive, send))
    
    # App SHOULD be called for optional paths
    if not app.was_called:
        errmsg = "Expected app to be called for optional path"
        raise AssertionError(errmsg)
    
    # Auth should be None
    if app.captured_scope.get("auth") is not None:
        errmsg = "Expected auth to be None for optional path without credentials"
        raise AssertionError(errmsg)
    
    return


def test_middleware_attaches_context_on_optional_path_with_auth():
    """
        Test that middleware attaches context on optional path when auth succeeds.
    """
    app = MockASGIApp()
    auth_system = AuthenticationSystem()
    
    # Create a successful authentication result
    principal = Principal(identifier="testuser")
    context = AuthenticationContext(principal=principal, scheme="Bearer")
    success_result = AuthenticationResult(
        status=AuthenticationStatus.SUCCESS,
        context=context
    )
    
    mock_auth = MockAuthenticator(
        scheme_name="Bearer",
        can_handle_result=True,
        auth_result=success_result
    )
    auth_system.register(mock_auth)
    
    middleware = AuthenticationMiddleware(
        app=app,
        auth_system=auth_system,
        optional_paths={"/optional"}
    )
    
    scope = create_http_scope(path="/optional")
    receive = MockReceive()
    send = MockSend()
    
    run_async(middleware(scope, receive, send))
    
    if not app.was_called:
        errmsg = "Expected app to be called"
        raise AssertionError(errmsg)
    
    # Auth should be the context
    attached_auth = app.captured_scope.get("auth")
    if attached_auth is not context:
        errmsg = "Expected auth context to be attached for optional path with valid auth"
        raise AssertionError(errmsg)
    
    return


def test_create_authentication_middleware_factory():
    """
        Test the factory function creates middleware correctly.
    """
    app = MockASGIApp()
    auth_system = AuthenticationSystem()
    
    middleware = create_authentication_middleware(
        app=app,
        auth_system=auth_system,
        exclude_paths={"/health"},
        optional_paths={"/optional"},
        realm="TestRealm"
    )
    
    if not isinstance(middleware, AuthenticationMiddleware):
        errmsg = f"Expected AuthenticationMiddleware instance, got {type(middleware)}"
        raise AssertionError(errmsg)
    
    if middleware.exclude_paths != {"/health"}:
        errmsg = f"Expected exclude_paths {{'/health'}}, got {middleware.exclude_paths}"
        raise AssertionError(errmsg)
    
    if middleware.realm != "TestRealm":
        errmsg = f"Expected realm 'TestRealm', got {middleware.realm}"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Property-Based Tests
# =============================================================================

# Feature: authentication, Property 25: Middleware Context Attachment
# *For any* successfully authenticated request passing through
# Authentication_Middleware, the request scope SHALL contain an "auth" key
# with a valid Authentication_Context.
# **Validates: Requirements 10.1, 10.2**

def test_property_25_middleware_context_attachment():
    """
        Property 25: Middleware Context Attachment
        
        For any successfully authenticated request passing through
        Authentication_Middleware, the request scope SHALL contain an
        "auth" key with a valid Authentication_Context.
        
        **Validates: Requirements 10.1, 10.2**
    """
    # Run 100 iterations with random data
    for iteration in range(100):
        # Generate random authentication context
        context = generate_random_authentication_context()
        
        # Create success result with the context
        success_result = AuthenticationResult(
            status=AuthenticationStatus.SUCCESS,
            context=context
        )
        
        # Create mock authenticator
        scheme = context.scheme
        mock_auth = MockAuthenticator(
            scheme_name=scheme,
            can_handle_result=True,
            auth_result=success_result
        )
        
        # Create auth system and register authenticator
        auth_system = AuthenticationSystem()
        auth_system.register(mock_auth)
        
        # Create mock app
        app = MockASGIApp()
        
        # Create middleware
        middleware = AuthenticationMiddleware(app=app, auth_system=auth_system)
        
        # Generate random path
        path = generate_random_path()
        
        # Create scope
        scope = create_http_scope(path=path)
        receive = MockReceive()
        send = MockSend()
        
        # Execute middleware
        run_async(middleware(scope, receive, send))
        
        # Property: App must be called on successful authentication
        if not app.was_called:
            errmsg = f"Iteration {iteration}: App was not called on successful authentication"
            raise AssertionError(errmsg)
        
        # Property: Scope must contain "auth" key
        if "auth" not in app.captured_scope:
            errmsg = f"Iteration {iteration}: Scope does not contain 'auth' key"
            raise AssertionError(errmsg)
        
        attached_auth = app.captured_scope["auth"]
        
        # Property: "auth" must be the AuthenticationContext
        if attached_auth is not context:
            errmsg = f"Iteration {iteration}: Attached auth is not the expected context"
            raise AssertionError(errmsg)
        
        # Property: Context must have a non-null Principal
        if attached_auth.principal is None:
            errmsg = f"Iteration {iteration}: Attached context has null Principal"
            raise AssertionError(errmsg)
        
        # Property: Context must have a scheme string
        if not isinstance(attached_auth.scheme, str) or len(attached_auth.scheme) == 0:
            errmsg = f"Iteration {iteration}: Attached context has invalid scheme"
            raise AssertionError(errmsg)
        
        # Property: Context must have authenticated_at timestamp
        if not isinstance(attached_auth.authenticated_at, datetime):
            errmsg = f"Iteration {iteration}: Attached context has invalid authenticated_at"
            raise AssertionError(errmsg)
        
        # Property: Principal must have non-empty identifier
        if not isinstance(attached_auth.principal.identifier, str):
            errmsg = f"Iteration {iteration}: Principal identifier is not a string"
            raise AssertionError(errmsg)
        
        if len(attached_auth.principal.identifier) == 0:
            errmsg = f"Iteration {iteration}: Principal identifier is empty"
            raise AssertionError(errmsg)
        
        # Reset for next iteration
        app.reset()
        mock_auth.reset()
    
    return



# =============================================================================
# Unit Tests for Access Policy Integration
# =============================================================================



def test_middleware_with_path_policies():
    """
        Test that middleware accepts path_policies configuration.
    """
    app = MockASGIApp()
    auth_system = AuthenticationSystem()
    
    path_policies = {
        "/admin": AccessPolicy(roles=["admin"]),
        "/api/users": AccessPolicy(roles=["admin", "user"])
    }
    
    middleware = AuthenticationMiddleware(
        app=app,
        auth_system=auth_system,
        path_policies=path_policies
    )
    
    if middleware.path_policies != path_policies:
        errmsg = f"Expected path_policies to be set, got {middleware.path_policies}"
        raise AssertionError(errmsg)
    
    return


def test_middleware_with_default_policy():
    """
        Test that middleware accepts default_policy configuration.
    """
    app = MockASGIApp()
    auth_system = AuthenticationSystem()
    
    default_policy = AccessPolicy(require_auth=True)
    
    middleware = AuthenticationMiddleware(
        app=app,
        auth_system=auth_system,
        default_policy=default_policy
    )
    
    if middleware.default_policy is not default_policy:
        errmsg = "Expected default_policy to be set"
        raise AssertionError(errmsg)
    
    return


def test_middleware_get_policy_for_path_exact_match():
    """
        Test that get_policy_for_path returns exact match policy.
    """
    app = MockASGIApp()
    auth_system = AuthenticationSystem()
    
    admin_policy = AccessPolicy(roles=["admin"])
    path_policies = {"/admin": admin_policy}
    
    middleware = AuthenticationMiddleware(
        app=app,
        auth_system=auth_system,
        path_policies=path_policies
    )
    
    result = middleware.get_policy_for_path("/admin")
    
    if result is not admin_policy:
        errmsg = "Expected exact match policy to be returned"
        raise AssertionError(errmsg)
    
    return


def test_middleware_get_policy_for_path_default():
    """
        Test that get_policy_for_path returns default policy when no match.
    """
    app = MockASGIApp()
    auth_system = AuthenticationSystem()
    
    default_policy = AccessPolicy(require_auth=True)
    
    middleware = AuthenticationMiddleware(
        app=app,
        auth_system=auth_system,
        default_policy=default_policy
    )
    
    result = middleware.get_policy_for_path("/unknown")
    
    if result is not default_policy:
        errmsg = "Expected default policy to be returned"
        raise AssertionError(errmsg)
    
    return


def test_middleware_get_policy_for_path_none():
    """
        Test that get_policy_for_path returns None when no policy matches.
    """
    app = MockASGIApp()
    auth_system = AuthenticationSystem()
    
    middleware = AuthenticationMiddleware(
        app=app,
        auth_system=auth_system
    )
    
    result = middleware.get_policy_for_path("/unknown")
    
    if result is not None:
        errmsg = f"Expected None, got {result}"
        raise AssertionError(errmsg)
    
    return


def test_middleware_check_access_policy_no_policy():
    """
        Test that check_access_policy returns True when no policy defined.
    """
    app = MockASGIApp()
    auth_system = AuthenticationSystem()
    
    middleware = AuthenticationMiddleware(
        app=app,
        auth_system=auth_system
    )
    
    principal = Principal(identifier="testuser")
    context = AuthenticationContext(principal=principal, scheme="Basic")
    
    result = middleware.check_access_policy("/any-path", context)
    
    if result is not True:
        errmsg = f"Expected True when no policy defined, got {result}"
        raise AssertionError(errmsg)
    
    return


def test_middleware_check_access_policy_with_matching_role():
    """
        Test that check_access_policy returns True when role matches.
    """
    app = MockASGIApp()
    auth_system = AuthenticationSystem()
    
    admin_policy = AccessPolicy(roles=["admin"])
    path_policies = {"/admin": admin_policy}
    
    middleware = AuthenticationMiddleware(
        app=app,
        auth_system=auth_system,
        path_policies=path_policies
    )
    
    principal = Principal(identifier="testuser", roles={"admin"})
    context = AuthenticationContext(principal=principal, scheme="Basic")
    
    result = middleware.check_access_policy("/admin", context)
    
    if result is not True:
        errmsg = f"Expected True when role matches, got {result}"
        raise AssertionError(errmsg)
    
    return


def test_middleware_check_access_policy_without_matching_role():
    """
        Test that check_access_policy returns False when role doesn't match.
    """
    app = MockASGIApp()
    auth_system = AuthenticationSystem()
    
    admin_policy = AccessPolicy(roles=["admin"])
    path_policies = {"/admin": admin_policy}
    
    middleware = AuthenticationMiddleware(
        app=app,
        auth_system=auth_system,
        path_policies=path_policies
    )
    
    principal = Principal(identifier="testuser", roles={"user"})
    context = AuthenticationContext(principal=principal, scheme="Basic")
    
    result = middleware.check_access_policy("/admin", context)
    
    if result is not False:
        errmsg = f"Expected False when role doesn't match, got {result}"
        raise AssertionError(errmsg)
    
    return


def test_middleware_sends_403_on_policy_failure():
    """
        Test that middleware sends 403 Forbidden when policy check fails.
    """
    app = MockASGIApp()
    auth_system = AuthenticationSystem()
    
    # Create a successful authentication result with non-admin user
    principal = Principal(identifier="testuser", roles={"user"})
    context = AuthenticationContext(principal=principal, scheme="Basic")
    success_result = AuthenticationResult(
        status=AuthenticationStatus.SUCCESS,
        context=context
    )
    
    mock_auth = MockAuthenticator(
        scheme_name="Basic",
        can_handle_result=True,
        auth_result=success_result
    )
    auth_system.register(mock_auth)
    
    # Require admin role for /admin path
    admin_policy = AccessPolicy(roles=["admin"])
    path_policies = {"/admin": admin_policy}
    
    middleware = AuthenticationMiddleware(
        app=app,
        auth_system=auth_system,
        path_policies=path_policies
    )
    
    scope = create_http_scope(path="/admin")
    receive = MockReceive()
    send = MockSend()
    
    run_async(middleware(scope, receive, send))
    
    # App should NOT be called when policy fails
    if app.was_called:
        errmsg = "Expected app NOT to be called when policy check fails"
        raise AssertionError(errmsg)
    
    # Check 403 response
    if len(send.messages) < 2:
        errmsg = f"Expected at least 2 messages, got {len(send.messages)}"
        raise AssertionError(errmsg)
    
    start_msg = send.messages[0]
    if start_msg.get("status") != 403:
        errmsg = f"Expected status 403, got {start_msg.get('status')}"
        raise AssertionError(errmsg)
    
    return


def test_middleware_allows_access_when_policy_passes():
    """
        Test that middleware allows access when policy check passes.
    """
    app = MockASGIApp()
    auth_system = AuthenticationSystem()
    
    # Create a successful authentication result with admin user
    principal = Principal(identifier="admin-user", roles={"admin"})
    context = AuthenticationContext(principal=principal, scheme="Basic")
    success_result = AuthenticationResult(
        status=AuthenticationStatus.SUCCESS,
        context=context
    )
    
    mock_auth = MockAuthenticator(
        scheme_name="Basic",
        can_handle_result=True,
        auth_result=success_result
    )
    auth_system.register(mock_auth)
    
    # Require admin role for /admin path
    admin_policy = AccessPolicy(roles=["admin"])
    path_policies = {"/admin": admin_policy}
    
    middleware = AuthenticationMiddleware(
        app=app,
        auth_system=auth_system,
        path_policies=path_policies
    )
    
    scope = create_http_scope(path="/admin")
    receive = MockReceive()
    send = MockSend()
    
    run_async(middleware(scope, receive, send))
    
    # App SHOULD be called when policy passes
    if not app.was_called:
        errmsg = "Expected app to be called when policy check passes"
        raise AssertionError(errmsg)
    
    # Auth context should be attached
    if app.captured_scope.get("auth") is not context:
        errmsg = "Expected auth context to be attached"
        raise AssertionError(errmsg)
    
    return


def test_middleware_policy_with_permissions():
    """
        Test that middleware enforces permission-based policies.
    """
    app = MockASGIApp()
    auth_system = AuthenticationSystem()
    
    # Create a successful authentication result with limited permissions
    principal = Principal(identifier="testuser", permissions={"read"})
    context = AuthenticationContext(principal=principal, scheme="Bearer")
    success_result = AuthenticationResult(
        status=AuthenticationStatus.SUCCESS,
        context=context
    )
    
    mock_auth = MockAuthenticator(
        scheme_name="Bearer",
        can_handle_result=True,
        auth_result=success_result
    )
    auth_system.register(mock_auth)
    
    # Require read and write permissions
    api_policy = AccessPolicy(scopes=["read", "write"])
    path_policies = {"/api/data": api_policy}
    
    middleware = AuthenticationMiddleware(
        app=app,
        auth_system=auth_system,
        path_policies=path_policies
    )
    
    scope = create_http_scope(path="/api/data")
    receive = MockReceive()
    send = MockSend()
    
    run_async(middleware(scope, receive, send))
    
    # App should NOT be called - missing write permission
    if app.was_called:
        errmsg = "Expected app NOT to be called when missing required permission"
        raise AssertionError(errmsg)
    
    # Check 403 response
    start_msg = send.messages[0]
    if start_msg.get("status") != 403:
        errmsg = f"Expected status 403, got {start_msg.get('status')}"
        raise AssertionError(errmsg)
    
    return


def test_middleware_policy_pattern_matching():
    """
        Test that middleware supports pattern-based policy matching.
    """
    app = MockASGIApp()
    auth_system = AuthenticationSystem()
    
    # Create a successful authentication result with admin role
    principal = Principal(identifier="admin-user", roles={"admin"})
    context = AuthenticationContext(principal=principal, scheme="Basic")
    success_result = AuthenticationResult(
        status=AuthenticationStatus.SUCCESS,
        context=context
    )
    
    mock_auth = MockAuthenticator(
        scheme_name="Basic",
        can_handle_result=True,
        auth_result=success_result
    )
    auth_system.register(mock_auth)
    
    # Pattern-based policy for /admin/*
    admin_policy = AccessPolicy(roles=["admin"])
    policy_patterns = [("/admin/*", admin_policy)]
    
    middleware = AuthenticationMiddleware(
        app=app,
        auth_system=auth_system,
        policy_patterns=policy_patterns
    )
    
    scope = create_http_scope(path="/admin/users")
    receive = MockReceive()
    send = MockSend()
    
    run_async(middleware(scope, receive, send))
    
    # App SHOULD be called - admin role matches
    if not app.was_called:
        errmsg = "Expected app to be called when pattern policy passes"
        raise AssertionError(errmsg)
    
    return


def test_create_authentication_middleware_with_policies():
    """
        Test the factory function with access policy parameters.
    """
    app = MockASGIApp()
    auth_system = AuthenticationSystem()
    
    path_policies = {"/admin": AccessPolicy(roles=["admin"])}
    default_policy = AccessPolicy(require_auth=True)
    
    middleware = create_authentication_middleware(
        app=app,
        auth_system=auth_system,
        path_policies=path_policies,
        default_policy=default_policy
    )
    
    if middleware.path_policies != path_policies:
        errmsg = "Expected path_policies to be set via factory"
        raise AssertionError(errmsg)
    
    if middleware.default_policy is not default_policy:
        errmsg = "Expected default_policy to be set via factory"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Path canonicalisation in the middleware itself
# =============================================================================

def _create_user_middleware(app, path_policies=None, exclude_paths=None):
    """
        Create an AuthenticationMiddleware whose authenticator signs in a
        user with the role 'user' on every request.
    """
    auth_system = AuthenticationSystem()
    principal = Principal(identifier="testuser", roles={"user"})
    context = AuthenticationContext(principal=principal, scheme="Basic")
    auth_system.register(MockAuthenticator(
        scheme_name="Basic",
        can_handle_result=True,
        auth_result=AuthenticationResult(status=AuthenticationStatus.SUCCESS, context=context)
    ))

    middleware = AuthenticationMiddleware(
        app=app,
        auth_system=auth_system,
        path_policies=path_policies,
        exclude_paths=exclude_paths
    )
    return middleware


def test_middleware_applies_path_policy_to_repeated_slash_spelling():
    """
        Test that a policy keyed on '/admin/users' also refuses
        '//admin//users', which the router serves from the same handler.
    """
    app = MockASGIApp()
    middleware = _create_user_middleware(app, path_policies={"/admin/users": AccessPolicy(roles=["admin"])})

    send = MockSend()
    run_async(middleware(create_http_scope(path="//admin//users"), MockReceive(), send))

    if app.was_called:
        raise AssertionError("Expected the policy to refuse the repeated-slash spelling")

    if send.messages[0].get("status") != 403:
        errmsg = f"Expected status 403, got {send.messages[0].get('status')}"
        raise AssertionError(errmsg)

    return


def test_middleware_hands_the_canonical_path_to_the_application():
    """
        Test that the application receives the canonical path the policy
        was decided on.
    """
    app = MockASGIApp()
    middleware = _create_user_middleware(app, exclude_paths={"/health"})

    run_async(middleware(create_http_scope(path="//health"), MockReceive(), MockSend()))

    if not app.was_called or app.captured_scope["path"] != "/health":
        errmsg = f"Expected the app to see '/health', got {app.captured_scope}"
        raise AssertionError(errmsg)

    if app.captured_scope.get("auth", "missing") is not None:
        raise AssertionError("Expected '//health' to be treated as the excluded '/health'")

    return


def test_middleware_redirects_paths_with_dot_segments():
    """
        Test that a path with '.' segments is answered with a 308 redirect
        to the path without them, keeping the query string.
    """
    app = MockASGIApp()
    middleware = _create_user_middleware(app, path_policies={"/admin/users": AccessPolicy(roles=["admin"])})

    scope = create_http_scope(path="/admin/./users")
    scope["query_string"] = b"page=2"
    send = MockSend()
    run_async(middleware(scope, MockReceive(), send))

    if app.was_called:
        raise AssertionError("Expected the dot-segment request not to reach the app")

    start = send.messages[0]
    location = dict(start.get("headers", [])).get(b"location")
    if start.get("status") != 308 or location != b"/admin/users?page=2":
        errmsg = f"Expected 308 to /admin/users?page=2, got {start.get('status')} {location!r}"
        raise AssertionError(errmsg)

    return


def test_middleware_closes_websocket_with_dot_segments():
    """
        Test that a WebSocket handshake on a path with '.' segments is
        closed instead of redirected.
    """
    app = MockASGIApp()
    middleware = _create_user_middleware(app)

    send = MockSend()
    run_async(middleware(create_websocket_scope(path="/ws/./chat"), MockReceive(), send))

    if app.was_called or send.messages[0].get("type") != "websocket.close":
        errmsg = f"Expected the handshake to be closed, got {send.messages}"
        raise AssertionError(errmsg)

    return
