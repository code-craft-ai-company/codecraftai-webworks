"""
    Tests for the AuthenticationMiddleware module.
    
    This module contains unit tests and property-based tests for the
    AuthenticationMiddleware class which integrates authentication
    into the ASGI request pipeline.
"""

import asyncio
import json
import random
import string
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Set

from automojo.webworks.authentication import (
    AuthenticationStatus,
    AuthenticationResult,
    Principal,
    AuthenticationContext
)
from automojo.webworks.authentication.middleware import (
    AuthenticationMiddleware,
    create_authentication_middleware
)
from automojo.webworks.authentication.system import AuthenticationSystem


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
        return loop.run_until_complete(coro)
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


def test_middleware_passes_non_http_requests():
    """
        Test that middleware passes non-HTTP requests directly to app.
    """
    app = MockASGIApp()
    auth_system = AuthenticationSystem()
    middleware = AuthenticationMiddleware(app=app, auth_system=auth_system)
    
    # WebSocket scope
    scope = {"type": "websocket", "path": "/ws"}
    receive = MockReceive()
    send = MockSend()
    
    run_async(middleware(scope, receive, send))
    
    if not app.was_called:
        errmsg = "Expected app to be called for non-HTTP request"
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

from automojo.webworks.endpoints.accesspolicy import AccessPolicy


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
