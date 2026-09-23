"""
    Tests for the session authentication module.
    
    This module contains unit tests and property-based tests for the session
    authentication implementation including SessionData, SessionStore,
    InMemorySessionStore, SessionAuthenticator, and CookieAttributes.
"""

import asyncio
import random
import string
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Set

from ccai.webworks.authentication import (
    AuthenticationStatus,
    Principal,
)
from ccai.webworks.authentication.session import (
    CookieAttributes,
    InMemorySessionStore,
    SameSitePolicy,
    SessionAuthenticator,
    SessionData,
    generate_secure_session_id
)


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
    return {generate_random_string(1, 20) for _ in range(num_roles)}


def generate_random_permissions() -> Set[str]:
    """
        Generate a random set of permission strings.
    """
    num_permissions = random.randint(0, 5)
    return {generate_random_string(1, 30) for _ in range(num_permissions)}


def generate_random_attributes() -> Dict[str, Any]:
    """
        Generate a random dictionary of attributes.
    """
    num_attrs = random.randint(0, 3)
    attrs = {}
    for _ in range(num_attrs):
        key = generate_random_string(1, 15)
        value_type = random.choice(['str', 'int', 'bool'])
        if value_type == 'str':
            attrs[key] = generate_random_string(0, 20)
        elif value_type == 'int':
            attrs[key] = random.randint(-100, 100)
        else:
            attrs[key] = random.choice([True, False])
    return attrs


def generate_random_principal() -> Principal:
    """
        Generate a random Principal instance with valid data.
    """
    identifier = generate_random_identifier()
    display_name = generate_random_string(0, 30) if random.choice([True, False]) else None
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


def generate_random_session_data() -> Dict[str, Any]:
    """
        Generate random session data dictionary.
    """
    num_items = random.randint(0, 5)
    data = {}
    for _ in range(num_items):
        key = generate_random_string(1, 15)
        data[key] = generate_random_string(1, 30)
    return data


def run_async(coro):
    """
        Helper to run async functions in tests.
    """
    return asyncio.run(coro)


# =============================================================================
# Unit Tests for SessionData
# =============================================================================

def test_session_data_creation():
    """
        Test that SessionData can be created with required fields.
    """
    principal = Principal(identifier="user123")
    session = SessionData(
        session_id="abc123",
        principal_id="user123",
        principal=principal
    )
    
    if session.session_id != "abc123":
        errmsg = f"Expected session_id 'abc123', got {session.session_id}"
        raise AssertionError(errmsg)
    
    if session.principal_id != "user123":
        errmsg = f"Expected principal_id 'user123', got {session.principal_id}"
        raise AssertionError(errmsg)
    
    return


def test_session_data_default_timestamps():
    """
        Test that SessionData has default timestamps.
    """
    principal = Principal(identifier="user123")
    before = datetime.now(timezone.utc)
    session = SessionData(
        session_id="abc123",
        principal_id="user123",
        principal=principal
    )
    after = datetime.now(timezone.utc)
    
    if session.created_at < before or session.created_at > after:
        errmsg = f"Expected created_at between {before} and {after}"
        raise AssertionError(errmsg)
    
    if session.last_accessed < before or session.last_accessed > after:
        errmsg = f"Expected last_accessed between {before} and {after}"
        raise AssertionError(errmsg)
    
    return


def test_session_data_is_expired_false_when_no_expiration():
    """
        Test that is_expired returns False when expires_at is None.
    """
    principal = Principal(identifier="user123")
    session = SessionData(
        session_id="abc123",
        principal_id="user123",
        principal=principal
    )
    
    if session.is_expired:
        errmsg = "Expected is_expired to be False when expires_at is None"
        raise AssertionError(errmsg)
    
    return


def test_session_data_is_expired_false_when_future():
    """
        Test that is_expired returns False when expires_at is in the future.
    """
    principal = Principal(identifier="user123")
    future_time = datetime.now(timezone.utc) + timedelta(hours=1)
    session = SessionData(
        session_id="abc123",
        principal_id="user123",
        principal=principal,
        expires_at=future_time
    )
    
    if session.is_expired:
        errmsg = "Expected is_expired to be False when expires_at is in the future"
        raise AssertionError(errmsg)
    
    return


def test_session_data_is_expired_true_when_past():
    """
        Test that is_expired returns True when expires_at is in the past.
    """
    principal = Principal(identifier="user123")
    past_time = datetime.now(timezone.utc) - timedelta(hours=1)
    session = SessionData(
        session_id="abc123",
        principal_id="user123",
        principal=principal,
        expires_at=past_time
    )
    
    if not session.is_expired:
        errmsg = "Expected is_expired to be True when expires_at is in the past"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for CookieAttributes
# =============================================================================

def test_cookie_attributes_default_values():
    """
        Test that CookieAttributes has secure default values.
    """
    attrs = CookieAttributes()
    
    if not attrs.http_only:
        errmsg = "Expected http_only to be True by default"
        raise AssertionError(errmsg)
    
    if not attrs.secure:
        errmsg = "Expected secure to be True by default"
        raise AssertionError(errmsg)
    
    if attrs.same_site != SameSitePolicy.LAX:
        errmsg = f"Expected same_site to be LAX, got {attrs.same_site}"
        raise AssertionError(errmsg)
    
    if attrs.path != "/":
        errmsg = f"Expected path to be '/', got {attrs.path}"
        raise AssertionError(errmsg)
    
    return


def test_cookie_attributes_to_cookie_string():
    """
        Test that to_cookie_string generates correct cookie header.
    """
    attrs = CookieAttributes(
        http_only=True,
        secure=True,
        same_site=SameSitePolicy.STRICT,
        path="/app"
    )
    
    cookie_str = attrs.to_cookie_string("session_id", "abc123")
    
    if "session_id=abc123" not in cookie_str:
        errmsg = f"Expected 'session_id=abc123' in cookie string, got {cookie_str}"
        raise AssertionError(errmsg)
    
    if "HttpOnly" not in cookie_str:
        errmsg = f"Expected 'HttpOnly' in cookie string, got {cookie_str}"
        raise AssertionError(errmsg)
    
    if "Secure" not in cookie_str:
        errmsg = f"Expected 'Secure' in cookie string, got {cookie_str}"
        raise AssertionError(errmsg)
    
    if "SameSite=Strict" not in cookie_str:
        errmsg = f"Expected 'SameSite=Strict' in cookie string, got {cookie_str}"
        raise AssertionError(errmsg)
    
    if "Path=/app" not in cookie_str:
        errmsg = f"Expected 'Path=/app' in cookie string, got {cookie_str}"
        raise AssertionError(errmsg)
    
    return


def test_cookie_attributes_to_clear_cookie_string():
    """
        Test that to_clear_cookie_string generates correct clear cookie header.
    """
    attrs = CookieAttributes()
    
    clear_str = attrs.to_clear_cookie_string("session_id")
    
    if "session_id=" not in clear_str:
        errmsg = f"Expected 'session_id=' in clear string, got {clear_str}"
        raise AssertionError(errmsg)
    
    if "Max-Age=0" not in clear_str:
        errmsg = f"Expected 'Max-Age=0' in clear string, got {clear_str}"
        raise AssertionError(errmsg)
    
    if "Expires=" not in clear_str:
        errmsg = f"Expected 'Expires=' in clear string, got {clear_str}"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for InMemorySessionStore
# =============================================================================

def test_in_memory_session_store_create_session():
    """
        Test that InMemorySessionStore can create a session.
    """
    store = InMemorySessionStore()
    principal = Principal(identifier="user123", display_name="Test User")
    
    session = run_async(store.create_session(principal))
    
    if session.principal_id != "user123":
        errmsg = f"Expected principal_id 'user123', got {session.principal_id}"
        raise AssertionError(errmsg)
    
    if session.principal.identifier != "user123":
        errmsg = f"Expected principal identifier 'user123', got {session.principal.identifier}"
        raise AssertionError(errmsg)
    
    if len(session.session_id) == 0:
        errmsg = "Expected non-empty session_id"
        raise AssertionError(errmsg)
    
    return


def test_in_memory_session_store_get_session():
    """
        Test that InMemorySessionStore can retrieve a session.
    """
    store = InMemorySessionStore()
    principal = Principal(identifier="user123")
    
    created = run_async(store.create_session(principal))
    retrieved = run_async(store.get_session(created.session_id))
    
    if retrieved is None:
        errmsg = "Expected to retrieve session, got None"
        raise AssertionError(errmsg)
    
    if retrieved.session_id != created.session_id:
        errmsg = f"Expected session_id {created.session_id}, got {retrieved.session_id}"
        raise AssertionError(errmsg)
    
    return


def test_in_memory_session_store_get_nonexistent_session():
    """
        Test that InMemorySessionStore returns None for non-existent session.
    """
    store = InMemorySessionStore()
    
    session = run_async(store.get_session("nonexistent"))
    
    if session is not None:
        errmsg = f"Expected None for non-existent session, got {session}"
        raise AssertionError(errmsg)
    
    return


def test_in_memory_session_store_delete_session():
    """
        Test that InMemorySessionStore can delete a session.
    """
    store = InMemorySessionStore()
    principal = Principal(identifier="user123")
    
    session = run_async(store.create_session(principal))
    result = run_async(store.delete_session(session.session_id))
    
    if not result:
        errmsg = "Expected delete_session to return True"
        raise AssertionError(errmsg)
    
    retrieved = run_async(store.get_session(session.session_id))
    if retrieved is not None:
        errmsg = "Expected session to be deleted"
        raise AssertionError(errmsg)
    
    return


def test_in_memory_session_store_delete_sessions_for_principal():
    """
        Test that InMemorySessionStore can delete all sessions for a principal.
    """
    store = InMemorySessionStore()
    principal1 = Principal(identifier="user123")
    principal2 = Principal(identifier="user456")
    
    # Create multiple sessions for user123
    session1 = run_async(store.create_session(principal1))
    session2 = run_async(store.create_session(principal1))
    session3 = run_async(store.create_session(principal2))
    
    count = run_async(store.delete_sessions_for_principal("user123"))
    
    if count != 2:
        errmsg = f"Expected 2 sessions deleted, got {count}"
        raise AssertionError(errmsg)
    
    # Verify user123 sessions are gone
    if run_async(store.get_session(session1.session_id)) is not None:
        errmsg = "Expected session1 to be deleted"
        raise AssertionError(errmsg)
    
    if run_async(store.get_session(session2.session_id)) is not None:
        errmsg = "Expected session2 to be deleted"
        raise AssertionError(errmsg)
    
    # Verify user456 session still exists
    if run_async(store.get_session(session3.session_id)) is None:
        errmsg = "Expected session3 to still exist"
        raise AssertionError(errmsg)
    
    return


def test_in_memory_session_store_expired_session_cleanup():
    """
        Test that InMemorySessionStore cleans up expired sessions on get.
    """
    store = InMemorySessionStore(default_expiration=1)
    principal = Principal(identifier="user123")
    
    # Create session with very short expiration
    session = run_async(store.create_session(principal, expires_in=0))
    
    # Manually set expiration to past
    session.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    
    # Try to retrieve - should return None and clean up
    retrieved = run_async(store.get_session(session.session_id))
    
    if retrieved is not None:
        errmsg = "Expected None for expired session"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for SessionAuthenticator
# =============================================================================

def test_session_authenticator_scheme():
    """
        Test that SessionAuthenticator returns correct scheme.
    """
    store = InMemorySessionStore()
    auth = SessionAuthenticator(session_store=store)
    
    if auth.scheme != "Session":
        errmsg = f"Expected scheme 'Session', got {auth.scheme}"
        raise AssertionError(errmsg)
    
    return


def test_session_authenticator_can_handle_with_cookie():
    """
        Test that can_handle returns True when session cookie is present.
    """
    store = InMemorySessionStore()
    auth = SessionAuthenticator(session_store=store, cookie_name="session_id")
    
    request = {"cookies": {"session_id": "abc123"}}
    
    if not auth.can_handle(request):
        errmsg = "Expected can_handle to return True when cookie is present"
        raise AssertionError(errmsg)
    
    return


def test_session_authenticator_can_handle_without_cookie():
    """
        Test that can_handle returns False when session cookie is absent.
    """
    store = InMemorySessionStore()
    auth = SessionAuthenticator(session_store=store, cookie_name="session_id")
    
    request = {"cookies": {}}
    
    if auth.can_handle(request):
        errmsg = "Expected can_handle to return False when cookie is absent"
        raise AssertionError(errmsg)
    
    return


def test_session_authenticator_authenticate_valid_session():
    """
        Test that authenticate returns SUCCESS for valid session.
    """
    store = InMemorySessionStore()
    auth = SessionAuthenticator(session_store=store, cookie_name="session_id")
    principal = Principal(identifier="user123", display_name="Test User")
    
    # Create a session
    session, _ = run_async(auth.create_session(principal))
    
    # Authenticate with the session
    request = {"cookies": {"session_id": session.session_id}}
    result = run_async(auth.authenticate(request))
    
    if result.status != AuthenticationStatus.SUCCESS:
        errmsg = f"Expected SUCCESS, got {result.status}"
        raise AssertionError(errmsg)
    
    if result.context.principal.identifier != "user123":
        errmsg = f"Expected principal identifier 'user123', got {result.context.principal.identifier}"
        raise AssertionError(errmsg)
    
    return


def test_session_authenticator_authenticate_invalid_session():
    """
        Test that authenticate returns FAILURE for invalid session.
    """
    store = InMemorySessionStore()
    auth = SessionAuthenticator(session_store=store, cookie_name="session_id")
    
    request = {"cookies": {"session_id": "invalid_session_id"}}
    result = run_async(auth.authenticate(request))
    
    if result.status != AuthenticationStatus.FAILURE:
        errmsg = f"Expected FAILURE, got {result.status}"
        raise AssertionError(errmsg)
    
    if result.error_code != "invalid_session":
        errmsg = f"Expected error_code 'invalid_session', got {result.error_code}"
        raise AssertionError(errmsg)
    
    return


def test_session_authenticator_authenticate_no_cookie():
    """
        Test that authenticate returns SKIP when no cookie is present.
    """
    store = InMemorySessionStore()
    auth = SessionAuthenticator(session_store=store, cookie_name="session_id")
    
    request = {"cookies": {}}
    result = run_async(auth.authenticate(request))
    
    if result.status != AuthenticationStatus.SKIP:
        errmsg = f"Expected SKIP, got {result.status}"
        raise AssertionError(errmsg)
    
    return


def test_session_authenticator_invalidate_session():
    """
        Test that invalidate_session removes the session.
    """
    store = InMemorySessionStore()
    auth = SessionAuthenticator(session_store=store, cookie_name="session_id")
    principal = Principal(identifier="user123")
    
    # Create a session
    session, _ = run_async(auth.create_session(principal))
    
    # Invalidate the session
    success, clear_cookie = run_async(auth.invalidate_session(session.session_id))
    
    if not success:
        errmsg = "Expected invalidate_session to return True"
        raise AssertionError(errmsg)
    
    # Verify session is gone
    request = {"cookies": {"session_id": session.session_id}}
    result = run_async(auth.authenticate(request))
    
    if result.status != AuthenticationStatus.FAILURE:
        errmsg = f"Expected FAILURE after invalidation, got {result.status}"
        raise AssertionError(errmsg)
    
    return


def test_generate_secure_session_id():
    """
        Test that generate_secure_session_id produces unique IDs.
    """
    ids = set()
    for _ in range(100):
        session_id = generate_secure_session_id()
        if session_id in ids:
            errmsg = f"Generated duplicate session ID: {session_id}"
            raise AssertionError(errmsg)
        ids.add(session_id)
    
    return


def test_generate_secure_session_id_length():
    """
        Test that generate_secure_session_id produces correct length.
    """
    # Default length is 32 bytes = 64 hex characters
    session_id = generate_secure_session_id(32)
    
    if len(session_id) != 64:
        errmsg = f"Expected 64 character session ID, got {len(session_id)}"
        raise AssertionError(errmsg)
    
    # Custom length
    session_id = generate_secure_session_id(16)
    
    if len(session_id) != 32:
        errmsg = f"Expected 32 character session ID, got {len(session_id)}"
        raise AssertionError(errmsg)
    
    return



# =============================================================================
# Property-Based Tests
# =============================================================================

# Feature: authentication, Property 20: Session Round-Trip
# *For any* successful authentication that creates a session, the session ID
# stored in the cookie SHALL, when presented in a subsequent request, restore
# an equivalent Authentication_Context with the same Principal identifier.
# **Validates: Requirements 8.1, 8.2, 8.3**

def test_property_20_session_round_trip():
    """
        Property 20: Session Round-Trip
        
        For any successful authentication that creates a session, the session ID
        stored in the cookie SHALL, when presented in a subsequent request,
        restore an equivalent Authentication_Context with the same Principal
        identifier.
        
        **Validates: Requirements 8.1, 8.2, 8.3**
    """
    # Run 100 iterations with random data
    for iteration in range(100):
        # Create a fresh store and authenticator for each iteration
        store = InMemorySessionStore(default_expiration=3600)
        auth = SessionAuthenticator(session_store=store, cookie_name="session_id")
        
        # Generate a random principal
        principal = generate_random_principal()
        session_data = generate_random_session_data()
        
        # Create a session
        session, cookie_header = run_async(
            auth.create_session(principal, data=session_data)
        )
        
        # Property: Session ID should be non-empty
        if not session.session_id:
            errmsg = f"Iteration {iteration}: Session ID is empty"
            raise AssertionError(errmsg)
        
        # Property: Cookie header should contain the session ID
        if session.session_id not in cookie_header:
            errmsg = f"Iteration {iteration}: Cookie header does not contain session ID"
            raise AssertionError(errmsg)
        
        # Simulate a subsequent request with the session cookie
        request = {"cookies": {"session_id": session.session_id}}
        result = run_async(auth.authenticate(request))
        
        # Property: Authentication should succeed
        if result.status != AuthenticationStatus.SUCCESS:
            errmsg = f"Iteration {iteration}: Expected SUCCESS, got {result.status}"
            raise AssertionError(errmsg)
        
        # Property: Context should be present
        if result.context is None:
            errmsg = f"Iteration {iteration}: Authentication context is None"
            raise AssertionError(errmsg)
        
        # Property: Principal identifier should match
        if result.context.principal.identifier != principal.identifier:
            errmsg = (
                f"Iteration {iteration}: Principal identifier mismatch. "
                f"Expected {principal.identifier}, got {result.context.principal.identifier}"
            )
            raise AssertionError(errmsg)
        
        # Property: Scheme should be "Session"
        if result.context.scheme != "Session":
            errmsg = f"Iteration {iteration}: Expected scheme 'Session', got {result.context.scheme}"
            raise AssertionError(errmsg)
        
        # Property: Session ID should be in context attributes
        if result.context.attributes.get("session_id") != session.session_id:
            errmsg = f"Iteration {iteration}: Session ID not in context attributes"
            raise AssertionError(errmsg)
    
    return


# Feature: authentication, Property 21: Session Expiration Enforcement
# *For any* session with a configured expiration time, requests after that
# time SHALL fail authentication and clear the session cookie.
# **Validates: Requirements 8.4, 8.8**

def test_property_21_session_expiration_enforcement():
    """
        Property 21: Session Expiration Enforcement
        
        For any session with a configured expiration time, requests after that
        time SHALL fail authentication and clear the session cookie.
        
        **Validates: Requirements 8.4, 8.8**
    """
    # Run 100 iterations with random data
    for iteration in range(100):
        # Create a fresh store and authenticator for each iteration
        # Use a very short expiration for testing
        store = InMemorySessionStore(default_expiration=3600)
        auth = SessionAuthenticator(session_store=store, cookie_name="session_id")
        
        # Generate a random principal
        principal = generate_random_principal()
        
        # Create a session with explicit expiration
        session, _ = run_async(auth.create_session(principal, expires_in=3600))
        
        # Manually expire the session by setting expires_at to the past
        session.expires_at = datetime.now(timezone.utc) - timedelta(seconds=random.randint(1, 3600))
        
        # Simulate a request with the expired session
        request = {"cookies": {"session_id": session.session_id}}
        result = run_async(auth.authenticate(request))
        
        # Property: Authentication should fail for expired session
        if result.status != AuthenticationStatus.FAILURE:
            errmsg = f"Iteration {iteration}: Expected FAILURE for expired session, got {result.status}"
            raise AssertionError(errmsg)
        
        # Property: Error code should indicate session expiration or invalidity
        valid_error_codes = ["session_expired", "invalid_session"]
        if result.error_code not in valid_error_codes:
            errmsg = (
                f"Iteration {iteration}: Expected error_code in {valid_error_codes}, "
                f"got {result.error_code}"
            )
            raise AssertionError(errmsg)
        
        # Property: Context should be None for failed authentication
        if result.context is not None:
            errmsg = f"Iteration {iteration}: Expected context to be None for failed auth"
            raise AssertionError(errmsg)
    
    return


# Feature: authentication, Property 22: Session Cookie Security Attributes
# *For any* session cookie set by the Session_Authenticator, the cookie SHALL
# have HttpOnly, Secure (when configured), and SameSite attributes set.
# **Validates: Requirements 8.6**

def test_property_22_session_cookie_security_attributes():
    """
        Property 22: Session Cookie Security Attributes
        
        For any session cookie set by the Session_Authenticator, the cookie SHALL
        have HttpOnly, Secure (when configured), and SameSite attributes set.
        
        **Validates: Requirements 8.6**
    """
    # Run 100 iterations with random configurations
    for iteration in range(100):
        # Generate random cookie configuration
        http_only = random.choice([True, False])
        secure = random.choice([True, False])
        same_site = random.choice([SameSitePolicy.STRICT, SameSitePolicy.LAX, SameSitePolicy.NONE])
        path = "/" + generate_random_string(0, 10)
        
        cookie_attrs = CookieAttributes(
            http_only=http_only,
            secure=secure,
            same_site=same_site,
            path=path
        )
        
        store = InMemorySessionStore(default_expiration=3600)
        auth = SessionAuthenticator(
            session_store=store,
            cookie_name="session_id",
            cookie_attributes=cookie_attrs
        )
        
        # Generate a random principal
        principal = generate_random_principal()
        
        # Create a session
        session, cookie_header = run_async(auth.create_session(principal))
        
        # Property: Cookie header should contain the session ID
        if f"session_id={session.session_id}" not in cookie_header:
            errmsg = f"Iteration {iteration}: Cookie header missing session_id value"
            raise AssertionError(errmsg)
        
        # Property: HttpOnly should be present when configured
        if http_only and "HttpOnly" not in cookie_header:
            errmsg = f"Iteration {iteration}: HttpOnly attribute missing when configured"
            raise AssertionError(errmsg)
        
        if not http_only and "HttpOnly" in cookie_header:
            errmsg = f"Iteration {iteration}: HttpOnly attribute present when not configured"
            raise AssertionError(errmsg)
        
        # Property: Secure should be present when configured
        if secure and "Secure" not in cookie_header:
            errmsg = f"Iteration {iteration}: Secure attribute missing when configured"
            raise AssertionError(errmsg)
        
        if not secure and "Secure" in cookie_header:
            errmsg = f"Iteration {iteration}: Secure attribute present when not configured"
            raise AssertionError(errmsg)
        
        # Property: SameSite should be present with correct value
        expected_same_site = f"SameSite={same_site.value}"
        if expected_same_site not in cookie_header:
            errmsg = (
                f"Iteration {iteration}: Expected '{expected_same_site}' in cookie header, "
                f"got {cookie_header}"
            )
            raise AssertionError(errmsg)
        
        # Property: Path should be present
        expected_path = f"Path={path}"
        if expected_path not in cookie_header:
            errmsg = (
                f"Iteration {iteration}: Expected '{expected_path}' in cookie header, "
                f"got {cookie_header}"
            )
            raise AssertionError(errmsg)
    
    return


# =============================================================================
# Additional Unit Tests for Edge Cases
# =============================================================================

def test_session_authenticator_empty_session_id():
    """
        Test that authenticate returns FAILURE for empty session ID.
    """
    store = InMemorySessionStore()
    auth = SessionAuthenticator(session_store=store, cookie_name="session_id")
    
    request = {"cookies": {"session_id": ""}}
    result = run_async(auth.authenticate(request))
    
    if result.status != AuthenticationStatus.FAILURE:
        errmsg = f"Expected FAILURE for empty session ID, got {result.status}"
        raise AssertionError(errmsg)
    
    return


def test_session_authenticator_whitespace_session_id():
    """
        Test that authenticate returns FAILURE for whitespace session ID.
    """
    store = InMemorySessionStore()
    auth = SessionAuthenticator(session_store=store, cookie_name="session_id")
    
    request = {"cookies": {"session_id": "   "}}
    result = run_async(auth.authenticate(request))
    
    if result.status != AuthenticationStatus.FAILURE:
        errmsg = f"Expected FAILURE for whitespace session ID, got {result.status}"
        raise AssertionError(errmsg)
    
    return


def test_session_authenticator_renew_on_access():
    """
        Test that session expiration is renewed on access when configured.
    """
    store = InMemorySessionStore(default_expiration=3600)
    auth = SessionAuthenticator(
        session_store=store,
        cookie_name="session_id",
        renew_on_access=True
    )
    principal = Principal(identifier="user123")
    
    # Create a session
    session, _ = run_async(auth.create_session(principal, expires_in=3600))
    original_expires = session.expires_at
    
    # Wait a tiny bit and access the session
    import time
    time.sleep(0.01)
    
    request = {"cookies": {"session_id": session.session_id}}
    run_async(auth.authenticate(request))
    
    # Get the updated session
    updated_session = run_async(store.get_session(session.session_id))
    
    # The expiration should have been extended
    if updated_session.expires_at <= original_expires:
        errmsg = "Expected session expiration to be extended on access"
        raise AssertionError(errmsg)
    
    return


def test_session_authenticator_no_renew_on_access():
    """
        Test that session expiration is not renewed when renew_on_access is False.
    """
    store = InMemorySessionStore(default_expiration=3600)
    auth = SessionAuthenticator(
        session_store=store,
        cookie_name="session_id",
        renew_on_access=False
    )
    principal = Principal(identifier="user123")
    
    # Create a session
    session, _ = run_async(auth.create_session(principal, expires_in=3600))
    original_expires = session.expires_at
    
    # Access the session
    request = {"cookies": {"session_id": session.session_id}}
    run_async(auth.authenticate(request))
    
    # Get the session again
    updated_session = run_async(store.get_session(session.session_id))
    
    # The expiration should not have changed
    if updated_session.expires_at != original_expires:
        errmsg = "Expected session expiration to remain unchanged"
        raise AssertionError(errmsg)
    
    return


def test_cookie_attributes_with_domain():
    """
        Test that CookieAttributes includes domain when set.
    """
    attrs = CookieAttributes(domain="example.com")
    
    cookie_str = attrs.to_cookie_string("session_id", "abc123")
    
    if "Domain=example.com" not in cookie_str:
        errmsg = f"Expected 'Domain=example.com' in cookie string, got {cookie_str}"
        raise AssertionError(errmsg)
    
    return


def test_cookie_attributes_with_max_age():
    """
        Test that CookieAttributes includes max_age when set.
    """
    attrs = CookieAttributes(max_age=3600)
    
    cookie_str = attrs.to_cookie_string("session_id", "abc123")
    
    if "Max-Age=3600" not in cookie_str:
        errmsg = f"Expected 'Max-Age=3600' in cookie string, got {cookie_str}"
        raise AssertionError(errmsg)
    
    return


def test_in_memory_session_store_update_session():
    """
        Test that InMemorySessionStore can update session data.
    """
    store = InMemorySessionStore()
    principal = Principal(identifier="user123")
    
    # Create a session with initial data
    session = run_async(store.create_session(principal, data={"key1": "value1"}))
    
    # Update the session
    updated = run_async(store.update_session(
        session.session_id,
        data={"key2": "value2"}
    ))
    
    if updated is None:
        errmsg = "Expected updated session, got None"
        raise AssertionError(errmsg)
    
    if "key1" not in updated.data:
        errmsg = "Expected key1 to still be in session data"
        raise AssertionError(errmsg)
    
    if "key2" not in updated.data:
        errmsg = "Expected key2 to be added to session data"
        raise AssertionError(errmsg)
    
    return


def test_in_memory_session_store_session_count():
    """
        Test that InMemorySessionStore tracks session count correctly.
    """
    store = InMemorySessionStore()
    
    if store.get_session_count() != 0:
        errmsg = f"Expected 0 sessions, got {store.get_session_count()}"
        raise AssertionError(errmsg)
    
    principal = Principal(identifier="user123")
    run_async(store.create_session(principal))
    run_async(store.create_session(principal))
    
    if store.get_session_count() != 2:
        errmsg = f"Expected 2 sessions, got {store.get_session_count()}"
        raise AssertionError(errmsg)
    
    return


def test_in_memory_session_store_clear_all():
    """
        Test that InMemorySessionStore can clear all sessions.
    """
    store = InMemorySessionStore()
    principal = Principal(identifier="user123")
    
    run_async(store.create_session(principal))
    run_async(store.create_session(principal))
    run_async(store.create_session(principal))
    
    count = store.clear_all_sessions()
    
    if count != 3:
        errmsg = f"Expected 3 sessions cleared, got {count}"
        raise AssertionError(errmsg)
    
    if store.get_session_count() != 0:
        errmsg = f"Expected 0 sessions after clear, got {store.get_session_count()}"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Regression Tests for BUG-6
# =============================================================================

def test_session_data_default_timestamps_are_timezone_aware():
    """
        Regression test for BUG-6: SessionData default datetime fields must
        be timezone-aware to prevent TypeError when compared with other
        timezone-aware datetimes (e.g. AuthenticationContext.authenticated_at).
    """
    principal = Principal(identifier="user-tz-test")
    session = SessionData(
        session_id="tz-test",
        principal_id="user-tz-test",
        principal=principal
    )

    if session.created_at.tzinfo is None:
        errmsg = (
            "BUG-6 regression: SessionData.created_at must be timezone-aware, "
            f"got tzinfo=None for {session.created_at!r}"
        )
        raise AssertionError(errmsg)

    if session.last_accessed.tzinfo is None:
        errmsg = (
            "BUG-6 regression: SessionData.last_accessed must be timezone-aware, "
            f"got tzinfo=None for {session.last_accessed!r}"
        )
        raise AssertionError(errmsg)

    return
