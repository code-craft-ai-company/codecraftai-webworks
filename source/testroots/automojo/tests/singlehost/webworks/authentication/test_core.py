"""
    Tests for the authentication core module.
    
    This module contains unit tests and property-based tests for the core
    authentication data structures: AuthenticationStatus, AuthenticationResult,
    Principal, and AuthenticationContext.
"""

import random
import string
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Set

from automojo.webworks.authentication import (
    AuthenticationStatus,
    AuthenticationResult,
    Principal,
    AuthenticationContext
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
    num_roles = random.randint(0, 10)
    return {generate_random_string(1, 20) for _ in range(num_roles)}


def generate_random_permissions() -> Set[str]:
    """
        Generate a random set of permission strings.
    """
    num_permissions = random.randint(0, 10)
    return {generate_random_string(1, 30) for _ in range(num_permissions)}


def generate_random_attributes() -> Dict[str, Any]:
    """
        Generate a random dictionary of attributes.
    """
    num_attrs = random.randint(0, 5)
    attrs = {}
    for _ in range(num_attrs):
        key = generate_random_string(1, 20)
        # Generate various types of values
        value_type = random.choice(['str', 'int', 'bool', 'list'])
        if value_type == 'str':
            attrs[key] = generate_random_string(0, 30)
        elif value_type == 'int':
            attrs[key] = random.randint(-1000, 1000)
        elif value_type == 'bool':
            attrs[key] = random.choice([True, False])
        else:
            attrs[key] = [generate_random_string(1, 10) for _ in range(random.randint(0, 5))]
    return attrs


def generate_random_scheme() -> str:
    """
        Generate a random authentication scheme name.
    """
    schemes = ["Basic", "Bearer", "Digest", "APIKey", "OAuth2", "OIDC", "HMAC", "Session"]
    return random.choice(schemes)


def generate_random_principal() -> Principal:
    """
        Generate a random Principal instance with valid data.
    """
    identifier = generate_random_identifier()
    display_name = generate_random_string(0, 50) if random.choice([True, False]) else None
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
    authenticated_at = datetime.now(timezone.utc) - timedelta(seconds=random.randint(0, 3600))
    
    # Randomly decide if there's an expiration
    if random.choice([True, False]):
        # Expiration in the future
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=random.randint(60, 86400))
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
# Unit Tests for AuthenticationStatus
# =============================================================================

def test_authentication_status_has_success():
    """
        Test that AuthenticationStatus has SUCCESS value.
    """
    if AuthenticationStatus.SUCCESS.value != "success":
        errmsg = f"Expected SUCCESS value 'success', got {AuthenticationStatus.SUCCESS.value}"
        raise AssertionError(errmsg)
    
    return


def test_authentication_status_has_failure():
    """
        Test that AuthenticationStatus has FAILURE value.
    """
    if AuthenticationStatus.FAILURE.value != "failure":
        errmsg = f"Expected FAILURE value 'failure', got {AuthenticationStatus.FAILURE.value}"
        raise AssertionError(errmsg)
    
    return


def test_authentication_status_has_challenge():
    """
        Test that AuthenticationStatus has CHALLENGE value.
    """
    if AuthenticationStatus.CHALLENGE.value != "challenge":
        errmsg = f"Expected CHALLENGE value 'challenge', got {AuthenticationStatus.CHALLENGE.value}"
        raise AssertionError(errmsg)
    
    return


def test_authentication_status_has_skip():
    """
        Test that AuthenticationStatus has SKIP value.
    """
    if AuthenticationStatus.SKIP.value != "skip":
        errmsg = f"Expected SKIP value 'skip', got {AuthenticationStatus.SKIP.value}"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for Principal
# =============================================================================

def test_principal_creation_with_identifier():
    """
        Test that Principal can be created with just an identifier.
    """
    principal = Principal(identifier="user123")
    
    if principal.identifier != "user123":
        errmsg = f"Expected identifier 'user123', got {principal.identifier}"
        raise AssertionError(errmsg)
    
    return


def test_principal_default_values():
    """
        Test that Principal has correct default values.
    """
    principal = Principal(identifier="user123")
    
    if principal.display_name is not None:
        errmsg = f"Expected display_name None, got {principal.display_name}"
        raise AssertionError(errmsg)
    
    if principal.roles != set():
        errmsg = f"Expected empty roles set, got {principal.roles}"
        raise AssertionError(errmsg)
    
    if principal.permissions != set():
        errmsg = f"Expected empty permissions set, got {principal.permissions}"
        raise AssertionError(errmsg)
    
    if principal.attributes != {}:
        errmsg = f"Expected empty attributes dict, got {principal.attributes}"
        raise AssertionError(errmsg)
    
    return


def test_principal_has_role_returns_true():
    """
        Test that has_role returns True when principal has the role.
    """
    principal = Principal(identifier="user123", roles={"admin", "user"})
    
    if not principal.has_role("admin"):
        errmsg = "Expected has_role('admin') to return True"
        raise AssertionError(errmsg)
    
    return


def test_principal_has_role_returns_false():
    """
        Test that has_role returns False when principal lacks the role.
    """
    principal = Principal(identifier="user123", roles={"user"})
    
    if principal.has_role("admin"):
        errmsg = "Expected has_role('admin') to return False"
        raise AssertionError(errmsg)
    
    return


def test_principal_has_permission_returns_true():
    """
        Test that has_permission returns True when principal has the permission.
    """
    principal = Principal(identifier="user123", permissions={"read", "write"})
    
    if not principal.has_permission("read"):
        errmsg = "Expected has_permission('read') to return True"
        raise AssertionError(errmsg)
    
    return


def test_principal_has_permission_returns_false():
    """
        Test that has_permission returns False when principal lacks the permission.
    """
    principal = Principal(identifier="user123", permissions={"read"})
    
    if principal.has_permission("delete"):
        errmsg = "Expected has_permission('delete') to return False"
        raise AssertionError(errmsg)
    
    return


def test_principal_with_all_fields():
    """
        Test that Principal can be created with all fields.
    """
    principal = Principal(
        identifier="user123",
        display_name="John Doe",
        roles={"admin", "user"},
        permissions={"read", "write", "delete"},
        attributes={"email": "john@example.com", "department": "IT"}
    )
    
    if principal.identifier != "user123":
        errmsg = f"Expected identifier 'user123', got {principal.identifier}"
        raise AssertionError(errmsg)
    
    if principal.display_name != "John Doe":
        errmsg = f"Expected display_name 'John Doe', got {principal.display_name}"
        raise AssertionError(errmsg)
    
    if principal.roles != {"admin", "user"}:
        errmsg = f"Expected roles {{'admin', 'user'}}, got {principal.roles}"
        raise AssertionError(errmsg)
    
    if principal.permissions != {"read", "write", "delete"}:
        errmsg = f"Expected permissions {{'read', 'write', 'delete'}}, got {principal.permissions}"
        raise AssertionError(errmsg)
    
    if principal.attributes != {"email": "john@example.com", "department": "IT"}:
        errmsg = f"Expected attributes with email and department, got {principal.attributes}"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for AuthenticationContext
# =============================================================================

def test_authentication_context_creation():
    """
        Test that AuthenticationContext can be created with required fields.
    """
    principal = Principal(identifier="user123")
    context = AuthenticationContext(principal=principal, scheme="Basic")
    
    if context.principal is not principal:
        errmsg = "Expected principal to be the same instance"
        raise AssertionError(errmsg)
    
    if context.scheme != "Basic":
        errmsg = f"Expected scheme 'Basic', got {context.scheme}"
        raise AssertionError(errmsg)
    
    return


def test_authentication_context_default_authenticated_at():
    """
        Test that AuthenticationContext has a default authenticated_at timestamp.
    """
    principal = Principal(identifier="user123")
    before = datetime.now(timezone.utc)
    context = AuthenticationContext(principal=principal, scheme="Basic")
    after = datetime.now(timezone.utc)
    
    if context.authenticated_at < before or context.authenticated_at > after:
        errmsg = f"Expected authenticated_at between {before} and {after}, got {context.authenticated_at}"
        raise AssertionError(errmsg)
    
    return


def test_authentication_context_default_expires_at():
    """
        Test that AuthenticationContext has None as default expires_at.
    """
    principal = Principal(identifier="user123")
    context = AuthenticationContext(principal=principal, scheme="Basic")
    
    if context.expires_at is not None:
        errmsg = f"Expected expires_at None, got {context.expires_at}"
        raise AssertionError(errmsg)
    
    return


def test_authentication_context_is_expired_false_when_no_expiration():
    """
        Test that is_expired returns False when expires_at is None.
    """
    principal = Principal(identifier="user123")
    context = AuthenticationContext(principal=principal, scheme="Basic")
    
    if context.is_expired:
        errmsg = "Expected is_expired to be False when expires_at is None"
        raise AssertionError(errmsg)
    
    return


def test_authentication_context_is_expired_false_when_future():
    """
        Test that is_expired returns False when expires_at is in the future.
    """
    principal = Principal(identifier="user123")
    future_time = datetime.now(timezone.utc) + timedelta(hours=1)
    context = AuthenticationContext(
        principal=principal,
        scheme="Basic",
        expires_at=future_time
    )
    
    if context.is_expired:
        errmsg = "Expected is_expired to be False when expires_at is in the future"
        raise AssertionError(errmsg)
    
    return


def test_authentication_context_is_expired_true_when_past():
    """
        Test that is_expired returns True when expires_at is in the past.
    """
    principal = Principal(identifier="user123")
    past_time = datetime.now(timezone.utc) - timedelta(hours=1)
    context = AuthenticationContext(
        principal=principal,
        scheme="Basic",
        expires_at=past_time
    )
    
    if not context.is_expired:
        errmsg = "Expected is_expired to be True when expires_at is in the past"
        raise AssertionError(errmsg)
    
    return


def test_authentication_context_with_attributes():
    """
        Test that AuthenticationContext can store attributes.
    """
    principal = Principal(identifier="user123")
    context = AuthenticationContext(
        principal=principal,
        scheme="Bearer",
        attributes={"token_type": "access", "scope": "read write"}
    )
    
    if context.attributes != {"token_type": "access", "scope": "read write"}:
        errmsg = f"Expected attributes with token_type and scope, got {context.attributes}"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for AuthenticationResult
# =============================================================================

def test_authentication_result_success():
    """
        Test that AuthenticationResult can represent success.
    """
    principal = Principal(identifier="user123")
    context = AuthenticationContext(principal=principal, scheme="Basic")
    result = AuthenticationResult(
        status=AuthenticationStatus.SUCCESS,
        context=context
    )
    
    if result.status != AuthenticationStatus.SUCCESS:
        errmsg = f"Expected status SUCCESS, got {result.status}"
        raise AssertionError(errmsg)
    
    if result.context is not context:
        errmsg = "Expected context to be the same instance"
        raise AssertionError(errmsg)
    
    return


def test_authentication_result_failure():
    """
        Test that AuthenticationResult can represent failure.
    """
    result = AuthenticationResult(
        status=AuthenticationStatus.FAILURE,
        error_code="invalid_credentials",
        error_description="Invalid username or password"
    )
    
    if result.status != AuthenticationStatus.FAILURE:
        errmsg = f"Expected status FAILURE, got {result.status}"
        raise AssertionError(errmsg)
    
    if result.error_code != "invalid_credentials":
        errmsg = f"Expected error_code 'invalid_credentials', got {result.error_code}"
        raise AssertionError(errmsg)
    
    if result.error_description != "Invalid username or password":
        errmsg = f"Expected error_description 'Invalid username or password', got {result.error_description}"
        raise AssertionError(errmsg)
    
    return


def test_authentication_result_challenge():
    """
        Test that AuthenticationResult can represent challenge.
    """
    result = AuthenticationResult(
        status=AuthenticationStatus.CHALLENGE,
        challenge='Basic realm="Restricted"'
    )
    
    if result.status != AuthenticationStatus.CHALLENGE:
        errmsg = f"Expected status CHALLENGE, got {result.status}"
        raise AssertionError(errmsg)
    
    if result.challenge != 'Basic realm="Restricted"':
        errmsg = f"Expected challenge 'Basic realm=\"Restricted\"', got {result.challenge}"
        raise AssertionError(errmsg)
    
    return


def test_authentication_result_skip():
    """
        Test that AuthenticationResult can represent skip.
    """
    result = AuthenticationResult(status=AuthenticationStatus.SKIP)
    
    if result.status != AuthenticationStatus.SKIP:
        errmsg = f"Expected status SKIP, got {result.status}"
        raise AssertionError(errmsg)
    
    return


def test_authentication_result_default_values():
    """
        Test that AuthenticationResult has correct default values.
    """
    result = AuthenticationResult(status=AuthenticationStatus.SUCCESS)
    
    if result.context is not None:
        errmsg = f"Expected context None, got {result.context}"
        raise AssertionError(errmsg)
    
    if result.challenge is not None:
        errmsg = f"Expected challenge None, got {result.challenge}"
        raise AssertionError(errmsg)
    
    if result.error_code is not None:
        errmsg = f"Expected error_code None, got {result.error_code}"
        raise AssertionError(errmsg)
    
    if result.error_description is not None:
        errmsg = f"Expected error_description None, got {result.error_description}"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Property-Based Tests
# =============================================================================

# Feature: authentication, Property 28: Authentication Context Structure Completeness
# *For any* successful authentication regardless of scheme, the Authentication_Context
# SHALL contain: a non-null Principal, the scheme identifier string, and an
# authenticated_at timestamp.
# **Validates: Requirements 11.1, 11.2, 11.3, 11.4**

def test_property_28_authentication_context_structure_completeness():
    """
        Property 28: Authentication Context Structure Completeness
        
        For any successful authentication regardless of scheme, the
        Authentication_Context SHALL contain: a non-null Principal,
        the scheme identifier string, and an authenticated_at timestamp.
        
        **Validates: Requirements 11.1, 11.2, 11.3, 11.4**
    """
    # Run 100 iterations with random data
    for iteration in range(100):
        # Generate a random authentication context
        context = generate_random_authentication_context()
        
        # Property: Principal must be non-null
        if context.principal is None:
            errmsg = f"Iteration {iteration}: Authentication_Context has null Principal"
            raise AssertionError(errmsg)
        
        # Property: Scheme must be a non-empty string
        if not isinstance(context.scheme, str):
            errmsg = f"Iteration {iteration}: scheme is not a string, got {type(context.scheme)}"
            raise AssertionError(errmsg)
        
        if len(context.scheme) == 0:
            errmsg = f"Iteration {iteration}: scheme is an empty string"
            raise AssertionError(errmsg)
        
        # Property: authenticated_at must be a datetime
        if not isinstance(context.authenticated_at, datetime):
            errmsg = f"Iteration {iteration}: authenticated_at is not a datetime, got {type(context.authenticated_at)}"
            raise AssertionError(errmsg)
        
        # Property: attributes must be a dict (possibly empty)
        if not isinstance(context.attributes, dict):
            errmsg = f"Iteration {iteration}: attributes is not a dict, got {type(context.attributes)}"
            raise AssertionError(errmsg)
    
    return


# Feature: authentication, Property 29: Principal Structure Completeness
# *For any* Principal in an Authentication_Context, the Principal SHALL have
# a non-empty identifier, and the roles and permissions collections SHALL be
# iterable (possibly empty).
# **Validates: Requirements 11.5, 11.6**

def test_property_29_principal_structure_completeness():
    """
        Property 29: Principal Structure Completeness
        
        For any Principal in an Authentication_Context, the Principal SHALL
        have a non-empty identifier, and the roles and permissions collections
        SHALL be iterable (possibly empty).
        
        **Validates: Requirements 11.5, 11.6**
    """
    # Run 100 iterations with random data
    for iteration in range(100):
        # Generate a random principal
        principal = generate_random_principal()
        
        # Property: identifier must be a non-empty string
        if not isinstance(principal.identifier, str):
            errmsg = f"Iteration {iteration}: identifier is not a string, got {type(principal.identifier)}"
            raise AssertionError(errmsg)
        
        if len(principal.identifier) == 0:
            errmsg = f"Iteration {iteration}: identifier is an empty string"
            raise AssertionError(errmsg)
        
        # Property: roles must be iterable
        try:
            roles_list = list(principal.roles)
        except TypeError:
            errmsg = f"Iteration {iteration}: roles is not iterable, got {type(principal.roles)}"
            raise AssertionError(errmsg)
        
        # Property: permissions must be iterable
        try:
            permissions_list = list(principal.permissions)
        except TypeError:
            errmsg = f"Iteration {iteration}: permissions is not iterable, got {type(principal.permissions)}"
            raise AssertionError(errmsg)
        
        # Property: has_role should work for any role in the set
        for role in principal.roles:
            if not principal.has_role(role):
                errmsg = f"Iteration {iteration}: has_role('{role}') returned False but role is in roles set"
                raise AssertionError(errmsg)
        
        # Property: has_permission should work for any permission in the set
        for permission in principal.permissions:
            if not principal.has_permission(permission):
                errmsg = f"Iteration {iteration}: has_permission('{permission}') returned False but permission is in permissions set"
                raise AssertionError(errmsg)
        
        # Property: has_role should return False for roles not in the set
        non_existent_role = "non_existent_role_" + generate_random_string(10, 20)
        if non_existent_role not in principal.roles and principal.has_role(non_existent_role):
            errmsg = f"Iteration {iteration}: has_role returned True for non-existent role"
            raise AssertionError(errmsg)
        
        # Property: has_permission should return False for permissions not in the set
        non_existent_perm = "non_existent_perm_" + generate_random_string(10, 20)
        if non_existent_perm not in principal.permissions and principal.has_permission(non_existent_perm):
            errmsg = f"Iteration {iteration}: has_permission returned True for non-existent permission"
            raise AssertionError(errmsg)
    
    return


# =============================================================================
# Imports for AuthenticationSystem tests
# =============================================================================

from automojo.webworks.authentication import (
    Authenticator,
    AuthenticationSystem
)


# =============================================================================
# Test Authenticator Implementations for Testing
# =============================================================================

class MockAuthenticator:
    """
        A mock authenticator for testing purposes.
        
        This authenticator can be configured to return specific results
        for testing the AuthenticationSystem behavior.
    """
    
    def __init__(
        self,
        scheme_name: str,
        can_handle_result: bool = True,
        auth_result: AuthenticationResult = None
    ):
        self._scheme_name = scheme_name
        self._can_handle_result = can_handle_result
        self._auth_result = auth_result or AuthenticationResult(
            status=AuthenticationStatus.SKIP
        )
        self._authenticate_called = False
    
    @property
    def scheme(self) -> str:
        return self._scheme_name
    
    def can_handle(self, request) -> bool:
        return self._can_handle_result
    
    async def authenticate(self, request) -> AuthenticationResult:
        self._authenticate_called = True
        return self._auth_result
    
    @property
    def was_authenticate_called(self) -> bool:
        return self._authenticate_called
    
    def reset(self):
        self._authenticate_called = False


def generate_random_mock_authenticator() -> MockAuthenticator:
    """
        Generate a random mock authenticator with a unique scheme name.
    """
    scheme_name = generate_random_string(3, 20)
    return MockAuthenticator(scheme_name=scheme_name)


# =============================================================================
# Unit Tests for AuthenticationSystem
# =============================================================================

def test_authentication_system_creation():
    """
        Test that AuthenticationSystem can be created.
    """
    system = AuthenticationSystem()
    
    if system.get_authenticator_count() != 0:
        errmsg = f"Expected 0 authenticators, got {system.get_authenticator_count()}"
        raise AssertionError(errmsg)
    
    return


def test_authentication_system_register_single():
    """
        Test that a single authenticator can be registered.
    """
    system = AuthenticationSystem()
    auth = MockAuthenticator(scheme_name="Basic")
    
    system.register(auth)
    
    if system.get_authenticator_count() != 1:
        errmsg = f"Expected 1 authenticator, got {system.get_authenticator_count()}"
        raise AssertionError(errmsg)
    
    if system.get_authenticator("Basic") is not auth:
        errmsg = "Expected to retrieve the same authenticator instance"
        raise AssertionError(errmsg)
    
    return


def test_authentication_system_register_multiple():
    """
        Test that multiple authenticators can be registered.
    """
    system = AuthenticationSystem()
    basic_auth = MockAuthenticator(scheme_name="Basic")
    bearer_auth = MockAuthenticator(scheme_name="Bearer")
    api_key_auth = MockAuthenticator(scheme_name="APIKey")
    
    system.register(basic_auth)
    system.register(bearer_auth)
    system.register(api_key_auth)
    
    if system.get_authenticator_count() != 3:
        errmsg = f"Expected 3 authenticators, got {system.get_authenticator_count()}"
        raise AssertionError(errmsg)
    
    return


def test_authentication_system_unregister():
    """
        Test that an authenticator can be unregistered.
    """
    system = AuthenticationSystem()
    auth = MockAuthenticator(scheme_name="Basic")
    
    system.register(auth)
    result = system.unregister("Basic")
    
    if not result:
        errmsg = "Expected unregister to return True"
        raise AssertionError(errmsg)
    
    if system.get_authenticator_count() != 0:
        errmsg = f"Expected 0 authenticators after unregister, got {system.get_authenticator_count()}"
        raise AssertionError(errmsg)
    
    return


def test_authentication_system_unregister_nonexistent():
    """
        Test that unregistering a non-existent scheme returns False.
    """
    system = AuthenticationSystem()
    
    result = system.unregister("NonExistent")
    
    if result:
        errmsg = "Expected unregister to return False for non-existent scheme"
        raise AssertionError(errmsg)
    
    return


def test_authentication_system_get_registered_schemes():
    """
        Test that get_registered_schemes returns all registered schemes.
    """
    system = AuthenticationSystem()
    basic_auth = MockAuthenticator(scheme_name="Basic")
    bearer_auth = MockAuthenticator(scheme_name="Bearer")
    
    system.register(basic_auth, priority=10)
    system.register(bearer_auth, priority=20)
    
    schemes = system.get_registered_schemes()
    
    if len(schemes) != 2:
        errmsg = f"Expected 2 schemes, got {len(schemes)}"
        raise AssertionError(errmsg)
    
    if "Basic" not in schemes:
        errmsg = "Expected 'Basic' in schemes"
        raise AssertionError(errmsg)
    
    if "Bearer" not in schemes:
        errmsg = "Expected 'Bearer' in schemes"
        raise AssertionError(errmsg)
    
    return


def test_authentication_system_priority_order():
    """
        Test that authenticators are ordered by priority (highest first).
    """
    system = AuthenticationSystem()
    low_auth = MockAuthenticator(scheme_name="Low")
    high_auth = MockAuthenticator(scheme_name="High")
    medium_auth = MockAuthenticator(scheme_name="Medium")
    
    system.register(low_auth, priority=10)
    system.register(high_auth, priority=30)
    system.register(medium_auth, priority=20)
    
    schemes = system.get_registered_schemes()
    
    if schemes[0] != "High":
        errmsg = f"Expected 'High' first, got {schemes[0]}"
        raise AssertionError(errmsg)
    
    if schemes[1] != "Medium":
        errmsg = f"Expected 'Medium' second, got {schemes[1]}"
        raise AssertionError(errmsg)
    
    if schemes[2] != "Low":
        errmsg = f"Expected 'Low' third, got {schemes[2]}"
        raise AssertionError(errmsg)
    
    return


def test_authentication_system_replace_authenticator():
    """
        Test that registering with same scheme replaces the authenticator.
    """
    system = AuthenticationSystem()
    auth1 = MockAuthenticator(scheme_name="Basic")
    auth2 = MockAuthenticator(scheme_name="Basic")
    
    system.register(auth1)
    system.register(auth2)
    
    if system.get_authenticator_count() != 1:
        errmsg = f"Expected 1 authenticator after replacement, got {system.get_authenticator_count()}"
        raise AssertionError(errmsg)
    
    if system.get_authenticator("Basic") is not auth2:
        errmsg = "Expected the second authenticator to replace the first"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Property-Based Tests for AuthenticationSystem Registry
# =============================================================================

# Feature: authentication, Property 1: Authenticator Registry Consistency
# *For any* set of Authenticators registered with the Authentication_System,
# the registry SHALL contain exactly those authenticators, each associated
# with its unique scheme identifier, and the count of registered authenticators
# SHALL equal the number of registrations.
# **Validates: Requirements 1.1, 1.2, 1.3**

def test_property_1_authenticator_registry_consistency():
    """
        Property 1: Authenticator Registry Consistency
        
        For any set of Authenticators registered with the Authentication_System,
        the registry SHALL contain exactly those authenticators, each associated
        with its unique scheme identifier, and the count of registered
        authenticators SHALL equal the number of registrations.
        
        **Validates: Requirements 1.1, 1.2, 1.3**
    """
    # Run 100 iterations with random data
    for iteration in range(100):
        system = AuthenticationSystem()
        
        # Generate a random number of authenticators (1-20)
        num_authenticators = random.randint(1, 20)
        
        # Generate unique scheme names
        scheme_names = set()
        while len(scheme_names) < num_authenticators:
            scheme_names.add(generate_random_string(3, 30))
        
        scheme_names = list(scheme_names)
        authenticators = {}
        
        # Register all authenticators
        for scheme_name in scheme_names:
            auth = MockAuthenticator(scheme_name=scheme_name)
            priority = random.randint(0, 100)
            system.register(auth, priority=priority)
            authenticators[scheme_name] = auth
        
        # Property: Count equals number of unique registrations
        if system.get_authenticator_count() != num_authenticators:
            errmsg = (
                f"Iteration {iteration}: Expected {num_authenticators} authenticators, "
                f"got {system.get_authenticator_count()}"
            )
            raise AssertionError(errmsg)
        
        # Property: Each authenticator is retrievable by its scheme
        for scheme_name, expected_auth in authenticators.items():
            retrieved_auth = system.get_authenticator(scheme_name)
            if retrieved_auth is not expected_auth:
                errmsg = (
                    f"Iteration {iteration}: Authenticator for scheme '{scheme_name}' "
                    f"does not match the registered instance"
                )
                raise AssertionError(errmsg)
        
        # Property: All registered schemes are in the scheme list
        registered_schemes = set(system.get_registered_schemes())
        expected_schemes = set(scheme_names)
        if registered_schemes != expected_schemes:
            errmsg = (
                f"Iteration {iteration}: Registered schemes {registered_schemes} "
                f"do not match expected {expected_schemes}"
            )
            raise AssertionError(errmsg)
        
        # Property: Unregistering reduces count
        scheme_to_remove = random.choice(scheme_names)
        result = system.unregister(scheme_to_remove)
        
        if not result:
            errmsg = f"Iteration {iteration}: Unregister returned False for existing scheme"
            raise AssertionError(errmsg)
        
        if system.get_authenticator_count() != num_authenticators - 1:
            errmsg = (
                f"Iteration {iteration}: Expected {num_authenticators - 1} authenticators "
                f"after unregister, got {system.get_authenticator_count()}"
            )
            raise AssertionError(errmsg)
        
        if system.get_authenticator(scheme_to_remove) is not None:
            errmsg = (
                f"Iteration {iteration}: Authenticator still retrievable after unregister"
            )
            raise AssertionError(errmsg)
    
    return



# =============================================================================
# Async Test Helpers
# =============================================================================

import asyncio


def run_async(coro):
    """
        Run an async coroutine synchronously.
    """
    return asyncio.get_event_loop().run_until_complete(coro)


# =============================================================================
# Unit Tests for AuthenticationSystem.authenticate()
# =============================================================================

def test_authentication_system_authenticate_success():
    """
        Test that authenticate returns SUCCESS when an authenticator succeeds.
    """
    system = AuthenticationSystem()
    
    principal = Principal(identifier="user123")
    context = AuthenticationContext(principal=principal, scheme="Basic")
    success_result = AuthenticationResult(
        status=AuthenticationStatus.SUCCESS,
        context=context
    )
    
    auth = MockAuthenticator(
        scheme_name="Basic",
        can_handle_result=True,
        auth_result=success_result
    )
    system.register(auth)
    
    result = run_async(system.authenticate({}))
    
    if result.status != AuthenticationStatus.SUCCESS:
        errmsg = f"Expected SUCCESS status, got {result.status}"
        raise AssertionError(errmsg)
    
    if result.context is not context:
        errmsg = "Expected the same context instance"
        raise AssertionError(errmsg)
    
    return


def test_authentication_system_authenticate_failure():
    """
        Test that authenticate returns FAILURE when authenticator fails.
    """
    system = AuthenticationSystem()
    
    failure_result = AuthenticationResult(
        status=AuthenticationStatus.FAILURE,
        error_code="invalid_credentials",
        error_description="Invalid username or password"
    )
    
    auth = MockAuthenticator(
        scheme_name="Basic",
        can_handle_result=True,
        auth_result=failure_result
    )
    system.register(auth)
    
    result = run_async(system.authenticate({}))
    
    if result.status != AuthenticationStatus.FAILURE:
        errmsg = f"Expected FAILURE status, got {result.status}"
        raise AssertionError(errmsg)
    
    if result.error_code != "invalid_credentials":
        errmsg = f"Expected error_code 'invalid_credentials', got {result.error_code}"
        raise AssertionError(errmsg)
    
    return


def test_authentication_system_authenticate_challenge():
    """
        Test that authenticate returns CHALLENGE when authenticator challenges.
    """
    system = AuthenticationSystem()
    
    challenge_result = AuthenticationResult(
        status=AuthenticationStatus.CHALLENGE,
        challenge='Basic realm="Restricted"'
    )
    
    auth = MockAuthenticator(
        scheme_name="Basic",
        can_handle_result=True,
        auth_result=challenge_result
    )
    system.register(auth)
    
    result = run_async(system.authenticate({}))
    
    if result.status != AuthenticationStatus.CHALLENGE:
        errmsg = f"Expected CHALLENGE status, got {result.status}"
        raise AssertionError(errmsg)
    
    if result.challenge != 'Basic realm="Restricted"':
        errmsg = f"Expected challenge 'Basic realm=\"Restricted\"', got {result.challenge}"
        raise AssertionError(errmsg)
    
    return


def test_authentication_system_authenticate_no_credentials():
    """
        Test that authenticate returns FAILURE with no_credentials when no authenticator handles.
    """
    system = AuthenticationSystem()
    
    auth = MockAuthenticator(
        scheme_name="Basic",
        can_handle_result=False  # Won't handle the request
    )
    system.register(auth)
    
    result = run_async(system.authenticate({}))
    
    if result.status != AuthenticationStatus.FAILURE:
        errmsg = f"Expected FAILURE status, got {result.status}"
        raise AssertionError(errmsg)
    
    if result.error_code != "no_credentials":
        errmsg = f"Expected error_code 'no_credentials', got {result.error_code}"
        raise AssertionError(errmsg)
    
    return


def test_authentication_system_authenticate_stops_on_success():
    """
        Test that authenticate stops iterating after first success.
    """
    system = AuthenticationSystem()
    
    principal = Principal(identifier="user123")
    context = AuthenticationContext(principal=principal, scheme="First")
    success_result = AuthenticationResult(
        status=AuthenticationStatus.SUCCESS,
        context=context
    )
    
    first_auth = MockAuthenticator(
        scheme_name="First",
        can_handle_result=True,
        auth_result=success_result
    )
    second_auth = MockAuthenticator(
        scheme_name="Second",
        can_handle_result=True,
        auth_result=AuthenticationResult(status=AuthenticationStatus.SUCCESS)
    )
    
    system.register(first_auth, priority=20)
    system.register(second_auth, priority=10)
    
    result = run_async(system.authenticate({}))
    
    if result.status != AuthenticationStatus.SUCCESS:
        errmsg = f"Expected SUCCESS status, got {result.status}"
        raise AssertionError(errmsg)
    
    if not first_auth.was_authenticate_called:
        errmsg = "Expected first authenticator to be called"
        raise AssertionError(errmsg)
    
    if second_auth.was_authenticate_called:
        errmsg = "Expected second authenticator NOT to be called after success"
        raise AssertionError(errmsg)
    
    return


def test_authentication_system_authenticate_stops_on_failure():
    """
        Test that authenticate stops iterating after definitive failure.
    """
    system = AuthenticationSystem()
    
    failure_result = AuthenticationResult(
        status=AuthenticationStatus.FAILURE,
        error_code="invalid_credentials"
    )
    
    first_auth = MockAuthenticator(
        scheme_name="First",
        can_handle_result=True,
        auth_result=failure_result
    )
    second_auth = MockAuthenticator(
        scheme_name="Second",
        can_handle_result=True,
        auth_result=AuthenticationResult(status=AuthenticationStatus.SUCCESS)
    )
    
    system.register(first_auth, priority=20)
    system.register(second_auth, priority=10)
    
    result = run_async(system.authenticate({}))
    
    if result.status != AuthenticationStatus.FAILURE:
        errmsg = f"Expected FAILURE status, got {result.status}"
        raise AssertionError(errmsg)
    
    if not first_auth.was_authenticate_called:
        errmsg = "Expected first authenticator to be called"
        raise AssertionError(errmsg)
    
    if second_auth.was_authenticate_called:
        errmsg = "Expected second authenticator NOT to be called after failure"
        raise AssertionError(errmsg)
    
    return


def test_authentication_system_authenticate_combines_challenges():
    """
        Test that authenticate combines challenges from multiple authenticators.
    """
    system = AuthenticationSystem()
    
    challenge1 = AuthenticationResult(
        status=AuthenticationStatus.CHALLENGE,
        challenge='Basic realm="Restricted"'
    )
    challenge2 = AuthenticationResult(
        status=AuthenticationStatus.CHALLENGE,
        challenge='Bearer realm="API"'
    )
    
    first_auth = MockAuthenticator(
        scheme_name="Basic",
        can_handle_result=True,
        auth_result=challenge1
    )
    second_auth = MockAuthenticator(
        scheme_name="Bearer",
        can_handle_result=True,
        auth_result=challenge2
    )
    
    system.register(first_auth, priority=20)
    system.register(second_auth, priority=10)
    
    result = run_async(system.authenticate({}))
    
    if result.status != AuthenticationStatus.CHALLENGE:
        errmsg = f"Expected CHALLENGE status, got {result.status}"
        raise AssertionError(errmsg)
    
    if 'Basic realm="Restricted"' not in result.challenge:
        errmsg = f"Expected Basic challenge in combined challenge, got {result.challenge}"
        raise AssertionError(errmsg)
    
    if 'Bearer realm="API"' not in result.challenge:
        errmsg = f"Expected Bearer challenge in combined challenge, got {result.challenge}"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Property-Based Tests for Authentication Iteration
# =============================================================================

# Feature: authentication, Property 2: Authentication Iteration Terminates on Success
# *For any* request and set of registered Authenticators where at least one can
# successfully authenticate, the Authentication_System SHALL return SUCCESS with
# a valid Authentication_Context, and no subsequent authenticators SHALL be
# invoked after the first success.
# **Validates: Requirements 1.4, 1.5**

def test_property_2_authentication_iteration_terminates_on_success():
    """
        Property 2: Authentication Iteration Terminates on Success
        
        For any request and set of registered Authenticators where at least
        one can successfully authenticate, the Authentication_System SHALL
        return SUCCESS with a valid Authentication_Context, and no subsequent
        authenticators SHALL be invoked after the first success.
        
        **Validates: Requirements 1.4, 1.5**
    """
    # Run 100 iterations with random data
    for iteration in range(100):
        system = AuthenticationSystem()
        
        # Generate a random number of authenticators (2-10)
        num_authenticators = random.randint(2, 10)
        
        # Randomly choose which authenticator will succeed (by index in priority order)
        success_index = random.randint(0, num_authenticators - 1)
        
        authenticators = []
        
        for i in range(num_authenticators):
            scheme_name = f"Scheme_{i}_{generate_random_string(3, 10)}"
            
            if i == success_index:
                # This authenticator will succeed
                principal = generate_random_principal()
                context = AuthenticationContext(principal=principal, scheme=scheme_name)
                auth_result = AuthenticationResult(
                    status=AuthenticationStatus.SUCCESS,
                    context=context
                )
            else:
                # Other authenticators will skip or challenge (not fail definitively)
                if random.choice([True, False]):
                    auth_result = AuthenticationResult(status=AuthenticationStatus.SKIP)
                else:
                    auth_result = AuthenticationResult(
                        status=AuthenticationStatus.CHALLENGE,
                        challenge=f'{scheme_name} realm="Test"'
                    )
            
            auth = MockAuthenticator(
                scheme_name=scheme_name,
                can_handle_result=True,
                auth_result=auth_result
            )
            
            # Higher index = lower priority (so we process in order 0, 1, 2, ...)
            priority = num_authenticators - i
            system.register(auth, priority=priority)
            authenticators.append(auth)
        
        # Run authentication
        result = run_async(system.authenticate({}))
        
        # Property: Result should be SUCCESS
        if result.status != AuthenticationStatus.SUCCESS:
            errmsg = (
                f"Iteration {iteration}: Expected SUCCESS status, got {result.status}"
            )
            raise AssertionError(errmsg)
        
        # Property: Context should be valid
        if result.context is None:
            errmsg = f"Iteration {iteration}: Expected non-null context on SUCCESS"
            raise AssertionError(errmsg)
        
        if result.context.principal is None:
            errmsg = f"Iteration {iteration}: Expected non-null principal in context"
            raise AssertionError(errmsg)
        
        # Property: No authenticators after the successful one should be called
        for i in range(success_index + 1, num_authenticators):
            if authenticators[i].was_authenticate_called:
                errmsg = (
                    f"Iteration {iteration}: Authenticator at index {i} was called "
                    f"after success at index {success_index}"
                )
                raise AssertionError(errmsg)
    
    return


# Feature: authentication, Property 3: Authentication Failure When All Fail
# *For any* request where no registered Authenticator succeeds, the
# Authentication_System SHALL return a FAILURE or CHALLENGE result with
# no Authentication_Context.
# **Validates: Requirements 1.6**

def test_property_3_authentication_failure_when_all_fail():
    """
        Property 3: Authentication Failure When All Fail
        
        For any request where no registered Authenticator succeeds, the
        Authentication_System SHALL return a FAILURE or CHALLENGE result
        with no Authentication_Context.
        
        **Validates: Requirements 1.6**
    """
    # Run 100 iterations with random data
    for iteration in range(100):
        system = AuthenticationSystem()
        
        # Generate a random number of authenticators (1-10)
        num_authenticators = random.randint(1, 10)
        
        # Track if any authenticator will issue a challenge
        has_challenge = False
        
        for i in range(num_authenticators):
            scheme_name = f"Scheme_{i}_{generate_random_string(3, 10)}"
            
            # Randomly choose between SKIP and CHALLENGE (never SUCCESS or FAILURE)
            # FAILURE would stop iteration, so we use SKIP or CHALLENGE
            if random.choice([True, False]):
                auth_result = AuthenticationResult(status=AuthenticationStatus.SKIP)
                can_handle = random.choice([True, False])
            else:
                auth_result = AuthenticationResult(
                    status=AuthenticationStatus.CHALLENGE,
                    challenge=f'{scheme_name} realm="Test"'
                )
                can_handle = True
                has_challenge = True
            
            auth = MockAuthenticator(
                scheme_name=scheme_name,
                can_handle_result=can_handle,
                auth_result=auth_result
            )
            
            priority = random.randint(0, 100)
            system.register(auth, priority=priority)
        
        # Run authentication
        result = run_async(system.authenticate({}))
        
        # Property: Result should be FAILURE or CHALLENGE (not SUCCESS)
        if result.status == AuthenticationStatus.SUCCESS:
            errmsg = (
                f"Iteration {iteration}: Expected FAILURE or CHALLENGE status, "
                f"got SUCCESS"
            )
            raise AssertionError(errmsg)
        
        # Property: Context should be None
        if result.context is not None:
            errmsg = (
                f"Iteration {iteration}: Expected null context when no authenticator "
                f"succeeds, got {result.context}"
            )
            raise AssertionError(errmsg)
        
        # Property: If any authenticator issued a challenge, result should be CHALLENGE
        if has_challenge:
            if result.status != AuthenticationStatus.CHALLENGE:
                errmsg = (
                    f"Iteration {iteration}: Expected CHALLENGE status when challenges "
                    f"were issued, got {result.status}"
                )
                raise AssertionError(errmsg)
            
            if not result.challenge:
                errmsg = (
                    f"Iteration {iteration}: Expected non-empty challenge string"
                )
                raise AssertionError(errmsg)
        else:
            # No challenges, should be FAILURE with no_credentials
            if result.status != AuthenticationStatus.FAILURE:
                errmsg = (
                    f"Iteration {iteration}: Expected FAILURE status when no challenges, "
                    f"got {result.status}"
                )
                raise AssertionError(errmsg)
            
            if result.error_code != "no_credentials":
                errmsg = (
                    f"Iteration {iteration}: Expected error_code 'no_credentials', "
                    f"got {result.error_code}"
                )
                raise AssertionError(errmsg)
    
    return



# =============================================================================
# Property-Based Tests for Cross-Scheme Context Consistency
# =============================================================================

# Feature: authentication, Property 30: Cross-Scheme Context Interface Consistency
# *For any* two Authentication_Contexts produced by different authentication schemes,
# both SHALL expose the same interface (principal, scheme, authenticated_at, attributes)
# with compatible types.
# **Validates: Requirements 11.7**

def test_property_30_cross_scheme_context_interface_consistency():
    """
        Property 30: Cross-Scheme Context Interface Consistency
        
        For any two Authentication_Contexts produced by different authentication
        schemes, both SHALL expose the same interface (principal, scheme,
        authenticated_at, attributes) with compatible types.
        
        **Validates: Requirements 11.7**
    """
    # Define all authentication schemes that produce AuthenticationContext
    all_schemes = ["Basic", "Bearer", "Digest", "APIKey", "OAuth2", "OIDC", "HMAC", "Session"]
    
    # Run 100 iterations with random data
    for iteration in range(100):
        # Generate two different random schemes
        scheme1 = random.choice(all_schemes)
        scheme2 = random.choice(all_schemes)
        while scheme2 == scheme1:
            scheme2 = random.choice(all_schemes)
        
        # Generate two AuthenticationContext instances with different schemes
        principal1 = generate_random_principal()
        principal2 = generate_random_principal()
        
        context1 = AuthenticationContext(
            principal=principal1,
            scheme=scheme1,
            authenticated_at=datetime.now(timezone.utc) - timedelta(seconds=random.randint(0, 3600)),
            expires_at=datetime.now(timezone.utc) + timedelta(seconds=random.randint(60, 86400)) if random.choice([True, False]) else None,
            attributes=generate_random_attributes()
        )
        
        context2 = AuthenticationContext(
            principal=principal2,
            scheme=scheme2,
            authenticated_at=datetime.now(timezone.utc) - timedelta(seconds=random.randint(0, 3600)),
            expires_at=datetime.now(timezone.utc) + timedelta(seconds=random.randint(60, 86400)) if random.choice([True, False]) else None,
            attributes=generate_random_attributes()
        )
        
        # Property: Both contexts have the same interface attributes
        required_attrs = ['principal', 'scheme', 'authenticated_at', 'expires_at', 'attributes']
        
        for attr in required_attrs:
            if not hasattr(context1, attr):
                errmsg = f"Iteration {iteration}: Context with scheme '{scheme1}' missing attribute '{attr}'"
                raise AssertionError(errmsg)
            
            if not hasattr(context2, attr):
                errmsg = f"Iteration {iteration}: Context with scheme '{scheme2}' missing attribute '{attr}'"
                raise AssertionError(errmsg)
        
        # Property: Both contexts have the is_expired property
        if not hasattr(context1, 'is_expired'):
            errmsg = f"Iteration {iteration}: Context with scheme '{scheme1}' missing 'is_expired' property"
            raise AssertionError(errmsg)
        
        if not hasattr(context2, 'is_expired'):
            errmsg = f"Iteration {iteration}: Context with scheme '{scheme2}' missing 'is_expired' property"
            raise AssertionError(errmsg)
        
        # Property: principal attribute has compatible type (Principal)
        if not isinstance(context1.principal, Principal):
            errmsg = f"Iteration {iteration}: Context with scheme '{scheme1}' has principal of type {type(context1.principal)}, expected Principal"
            raise AssertionError(errmsg)
        
        if not isinstance(context2.principal, Principal):
            errmsg = f"Iteration {iteration}: Context with scheme '{scheme2}' has principal of type {type(context2.principal)}, expected Principal"
            raise AssertionError(errmsg)
        
        # Property: scheme attribute has compatible type (str)
        if not isinstance(context1.scheme, str):
            errmsg = f"Iteration {iteration}: Context with scheme '{scheme1}' has scheme of type {type(context1.scheme)}, expected str"
            raise AssertionError(errmsg)
        
        if not isinstance(context2.scheme, str):
            errmsg = f"Iteration {iteration}: Context with scheme '{scheme2}' has scheme of type {type(context2.scheme)}, expected str"
            raise AssertionError(errmsg)
        
        # Property: authenticated_at attribute has compatible type (datetime)
        if not isinstance(context1.authenticated_at, datetime):
            errmsg = f"Iteration {iteration}: Context with scheme '{scheme1}' has authenticated_at of type {type(context1.authenticated_at)}, expected datetime"
            raise AssertionError(errmsg)
        
        if not isinstance(context2.authenticated_at, datetime):
            errmsg = f"Iteration {iteration}: Context with scheme '{scheme2}' has authenticated_at of type {type(context2.authenticated_at)}, expected datetime"
            raise AssertionError(errmsg)
        
        # Property: expires_at attribute has compatible type (datetime or None)
        if context1.expires_at is not None and not isinstance(context1.expires_at, datetime):
            errmsg = f"Iteration {iteration}: Context with scheme '{scheme1}' has expires_at of type {type(context1.expires_at)}, expected datetime or None"
            raise AssertionError(errmsg)
        
        if context2.expires_at is not None and not isinstance(context2.expires_at, datetime):
            errmsg = f"Iteration {iteration}: Context with scheme '{scheme2}' has expires_at of type {type(context2.expires_at)}, expected datetime or None"
            raise AssertionError(errmsg)
        
        # Property: attributes attribute has compatible type (dict)
        if not isinstance(context1.attributes, dict):
            errmsg = f"Iteration {iteration}: Context with scheme '{scheme1}' has attributes of type {type(context1.attributes)}, expected dict"
            raise AssertionError(errmsg)
        
        if not isinstance(context2.attributes, dict):
            errmsg = f"Iteration {iteration}: Context with scheme '{scheme2}' has attributes of type {type(context2.attributes)}, expected dict"
            raise AssertionError(errmsg)
        
        # Property: is_expired returns a boolean
        if not isinstance(context1.is_expired, bool):
            errmsg = f"Iteration {iteration}: Context with scheme '{scheme1}' has is_expired of type {type(context1.is_expired)}, expected bool"
            raise AssertionError(errmsg)
        
        if not isinstance(context2.is_expired, bool):
            errmsg = f"Iteration {iteration}: Context with scheme '{scheme2}' has is_expired of type {type(context2.is_expired)}, expected bool"
            raise AssertionError(errmsg)
        
        # Property: Principal interface is consistent across schemes
        # Both principals should have the same interface
        principal_attrs = ['identifier', 'display_name', 'roles', 'permissions', 'attributes']
        
        for attr in principal_attrs:
            if not hasattr(context1.principal, attr):
                errmsg = f"Iteration {iteration}: Principal from scheme '{scheme1}' missing attribute '{attr}'"
                raise AssertionError(errmsg)
            
            if not hasattr(context2.principal, attr):
                errmsg = f"Iteration {iteration}: Principal from scheme '{scheme2}' missing attribute '{attr}'"
                raise AssertionError(errmsg)
        
        # Property: Principal methods are consistent
        principal_methods = ['has_role', 'has_permission']
        
        for method in principal_methods:
            if not hasattr(context1.principal, method) or not callable(getattr(context1.principal, method)):
                errmsg = f"Iteration {iteration}: Principal from scheme '{scheme1}' missing method '{method}'"
                raise AssertionError(errmsg)
            
            if not hasattr(context2.principal, method) or not callable(getattr(context2.principal, method)):
                errmsg = f"Iteration {iteration}: Principal from scheme '{scheme2}' missing method '{method}'"
                raise AssertionError(errmsg)
        
        # Property: Principal identifier is a non-empty string for both
        if not isinstance(context1.principal.identifier, str) or len(context1.principal.identifier) == 0:
            errmsg = f"Iteration {iteration}: Principal from scheme '{scheme1}' has invalid identifier"
            raise AssertionError(errmsg)
        
        if not isinstance(context2.principal.identifier, str) or len(context2.principal.identifier) == 0:
            errmsg = f"Iteration {iteration}: Principal from scheme '{scheme2}' has invalid identifier"
            raise AssertionError(errmsg)
        
        # Property: Principal roles and permissions are iterable for both
        try:
            list(context1.principal.roles)
            list(context1.principal.permissions)
        except TypeError:
            errmsg = f"Iteration {iteration}: Principal from scheme '{scheme1}' has non-iterable roles or permissions"
            raise AssertionError(errmsg)
        
        try:
            list(context2.principal.roles)
            list(context2.principal.permissions)
        except TypeError:
            errmsg = f"Iteration {iteration}: Principal from scheme '{scheme2}' has non-iterable roles or permissions"
            raise AssertionError(errmsg)
    
    return



# =============================================================================
# Unit Tests for Protocol Compliance Verification Functions
# =============================================================================

from automojo.webworks.authentication import (
    verify_authentication_context_compliance,
    verify_principal_compliance
)


def test_verify_principal_compliance_valid():
    """
        Test that verify_principal_compliance returns True for valid Principal.
    """
    principal = Principal(
        identifier="user123",
        display_name="John Doe",
        roles={"admin", "user"},
        permissions={"read", "write"},
        attributes={"email": "john@example.com"}
    )
    
    result = verify_principal_compliance(principal)
    
    if not result:
        errmsg = "Expected verify_principal_compliance to return True for valid Principal"
        raise AssertionError(errmsg)
    
    return


def test_verify_principal_compliance_minimal():
    """
        Test that verify_principal_compliance returns True for minimal Principal.
    """
    principal = Principal(identifier="user123")
    
    result = verify_principal_compliance(principal)
    
    if not result:
        errmsg = "Expected verify_principal_compliance to return True for minimal Principal"
        raise AssertionError(errmsg)
    
    return


def test_verify_principal_compliance_raises_for_non_principal():
    """
        Test that verify_principal_compliance raises TypeError for non-Principal.
    """
    try:
        verify_principal_compliance("not a principal")
        errmsg = "Expected TypeError for non-Principal input"
        raise AssertionError(errmsg)
    except TypeError:
        pass  # Expected
    
    return


def test_verify_authentication_context_compliance_valid():
    """
        Test that verify_authentication_context_compliance returns True for valid context.
    """
    principal = Principal(identifier="user123")
    context = AuthenticationContext(
        principal=principal,
        scheme="Basic",
        attributes={"realm": "test"}
    )
    
    result = verify_authentication_context_compliance(context)
    
    if not result:
        errmsg = "Expected verify_authentication_context_compliance to return True for valid context"
        raise AssertionError(errmsg)
    
    return


def test_verify_authentication_context_compliance_with_expiration():
    """
        Test that verify_authentication_context_compliance works with expiration.
    """
    principal = Principal(identifier="user123")
    context = AuthenticationContext(
        principal=principal,
        scheme="Bearer",
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
    )
    
    result = verify_authentication_context_compliance(context)
    
    if not result:
        errmsg = "Expected verify_authentication_context_compliance to return True for context with expiration"
        raise AssertionError(errmsg)
    
    return


def test_verify_authentication_context_compliance_raises_for_non_context():
    """
        Test that verify_authentication_context_compliance raises TypeError for non-context.
    """
    try:
        verify_authentication_context_compliance("not a context")
        errmsg = "Expected TypeError for non-AuthenticationContext input"
        raise AssertionError(errmsg)
    except TypeError:
        pass  # Expected
    
    return


def test_verify_authentication_context_compliance_all_schemes():
    """
        Test that verify_authentication_context_compliance works for all schemes.
    """
    schemes = ["Basic", "Bearer", "Digest", "APIKey", "OAuth2", "OIDC", "HMAC", "Session"]
    
    for scheme in schemes:
        principal = Principal(identifier=f"user-{scheme}")
        context = AuthenticationContext(principal=principal, scheme=scheme)
        
        result = verify_authentication_context_compliance(context)
        
        if not result:
            errmsg = f"Expected verify_authentication_context_compliance to return True for scheme '{scheme}'"
            raise AssertionError(errmsg)
    
    return


# =============================================================================
# BUG-2 Regression: timezone-aware datetime in AuthenticationContext
# =============================================================================

def test_authentication_context_timestamps_are_timezone_aware():
    """
        Test that AuthenticationContext.authenticated_at produces a
        timezone-aware datetime (not a naive datetime from the deprecated
        datetime.utcnow()).
    """
    principal = Principal(identifier="user-tz-test")
    context = AuthenticationContext(principal=principal, scheme="Bearer")
    
    # The default authenticated_at should be timezone-aware
    if context.authenticated_at.tzinfo is None:
        errmsg = (
            "Expected authenticated_at to be timezone-aware, "
            "but got a naive datetime (tzinfo is None)"
        )
        raise AssertionError(errmsg)
    
    return


def test_authentication_context_is_expired_with_timezone_aware_expiry():
    """
        Test that is_expired works correctly with timezone-aware expiry times.
    """
    principal = Principal(identifier="user-tz-expiry")
    
    # Future expiry — should not be expired
    future_ctx = AuthenticationContext(
        principal=principal,
        scheme="Bearer",
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
    )
    if future_ctx.is_expired:
        errmsg = "Expected is_expired=False for future tz-aware expiry"
        raise AssertionError(errmsg)
    
    # Past expiry — should be expired
    past_ctx = AuthenticationContext(
        principal=principal,
        scheme="Bearer",
        expires_at=datetime.now(timezone.utc) - timedelta(hours=1)
    )
    if not past_ctx.is_expired:
        errmsg = "Expected is_expired=True for past tz-aware expiry"
        raise AssertionError(errmsg)
    
    return


