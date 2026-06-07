"""
    Tests for the AccessPolicy dataclass.
    
    This module contains unit tests for the access policy constraint dataclass.
"""

from typing import List

from ccai.webworks.endpoints.accesspolicy import AccessPolicy


# =============================================================================
# Helper Classes for Testing
# =============================================================================

class MockUser:
    """
        Mock user class for testing AccessPolicy.check().
    """
    
    def __init__(
        self,
        roles: List[str] = None,
        scopes: List[str] = None,
        is_authenticated: bool = True
    ):
        self._roles = roles or []
        self._scopes = scopes or []
        self._is_authenticated = is_authenticated
    
    @property
    def roles(self) -> List[str]:
        return self._roles
    
    @property
    def scopes(self) -> List[str]:
        return self._scopes
    
    @property
    def is_authenticated(self) -> bool:
        return self._is_authenticated


# =============================================================================
# Unit Tests for AccessPolicy - Basic Construction
# =============================================================================

def test_accesspolicy_default_values():
    """
        Test that AccessPolicy has correct default values.
    """
    policy = AccessPolicy()
    
    if policy.roles != ():
        errmsg = f"Expected empty roles list, got {policy.roles}"
        raise AssertionError(errmsg)
    
    if policy.scopes != ():
        errmsg = f"Expected empty scopes list, got {policy.scopes}"
        raise AssertionError(errmsg)
    
    if policy.require_auth is not True:
        errmsg = f"Expected require_auth to be True, got {policy.require_auth}"
        raise AssertionError(errmsg)
    
    return


def test_accesspolicy_with_roles():
    """
        Test that AccessPolicy can be created with roles.
    """
    policy = AccessPolicy(roles=["admin", "user"])
    
    if policy.roles != ("admin", "user"):
        errmsg = f"Expected roles ['admin', 'user'], got {policy.roles}"
        raise AssertionError(errmsg)
    
    return


def test_accesspolicy_with_scopes():
    """
        Test that AccessPolicy can be created with scopes.
    """
    policy = AccessPolicy(scopes=["read", "write"])
    
    if policy.scopes != ("read", "write"):
        errmsg = f"Expected scopes ['read', 'write'], got {policy.scopes}"
        raise AssertionError(errmsg)
    
    return


def test_accesspolicy_with_require_auth_false():
    """
        Test that AccessPolicy can be created with require_auth=False.
    """
    policy = AccessPolicy(require_auth=False)
    
    if policy.require_auth is not False:
        errmsg = f"Expected require_auth to be False, got {policy.require_auth}"
        raise AssertionError(errmsg)
    
    return


def test_accesspolicy_is_dataclass():
    """
        Test that AccessPolicy is a proper dataclass with equality.
    """
    policy1 = AccessPolicy(roles=["admin"], scopes=["read"])
    policy2 = AccessPolicy(roles=["admin"], scopes=["read"])
    
    if policy1 != policy2:
        errmsg = "Expected equal AccessPolicy instances to be equal"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for AccessPolicy - merge_with method
# =============================================================================

def test_merge_with_combines_roles():
    """
        Test that merge_with combines roles from both policies.
    """
    policy1 = AccessPolicy(roles=["admin"])
    policy2 = AccessPolicy(roles=["user"])
    
    result = policy1.merge_with(policy2)
    
    if "admin" not in result.roles:
        errmsg = "Expected 'admin' in merged roles"
        raise AssertionError(errmsg)
    
    if "user" not in result.roles:
        errmsg = "Expected 'user' in merged roles"
        raise AssertionError(errmsg)
    
    return


def test_merge_with_combines_scopes():
    """
        Test that merge_with combines scopes from both policies.
    """
    policy1 = AccessPolicy(scopes=["read"])
    policy2 = AccessPolicy(scopes=["write"])
    
    result = policy1.merge_with(policy2)
    
    if "read" not in result.scopes:
        errmsg = "Expected 'read' in merged scopes"
        raise AssertionError(errmsg)
    
    if "write" not in result.scopes:
        errmsg = "Expected 'write' in merged scopes"
        raise AssertionError(errmsg)
    
    return


def test_merge_with_deduplicates_roles():
    """
        Test that merge_with deduplicates roles.
    """
    policy1 = AccessPolicy(roles=["admin", "user"])
    policy2 = AccessPolicy(roles=["user", "guest"])
    
    result = policy1.merge_with(policy2)
    
    # Count occurrences of 'user'
    user_count = result.roles.count("user")
    if user_count != 1:
        errmsg = f"Expected 'user' to appear once, got {user_count} times"
        raise AssertionError(errmsg)
    
    return


def test_merge_with_deduplicates_scopes():
    """
        Test that merge_with deduplicates scopes.
    """
    policy1 = AccessPolicy(scopes=["read", "write"])
    policy2 = AccessPolicy(scopes=["write", "delete"])
    
    result = policy1.merge_with(policy2)
    
    # Count occurrences of 'write'
    write_count = result.scopes.count("write")
    if write_count != 1:
        errmsg = f"Expected 'write' to appear once, got {write_count} times"
        raise AssertionError(errmsg)
    
    return


def test_merge_with_replace_roles():
    """
        Test that merge_with replaces roles when replace_roles=True.
    """
    policy1 = AccessPolicy(roles=["admin"])
    policy2 = AccessPolicy(roles=["user"])
    
    result = policy1.merge_with(policy2, replace_roles=True)
    
    if result.roles != ("user",):
        errmsg = f"Expected roles ['user'], got {result.roles}"
        raise AssertionError(errmsg)
    
    return


def test_merge_with_replace_scopes():
    """
        Test that merge_with replaces scopes when replace_scopes=True.
    """
    policy1 = AccessPolicy(scopes=["read"])
    policy2 = AccessPolicy(scopes=["write"])
    
    result = policy1.merge_with(policy2, replace_scopes=True)
    
    if result.scopes != ("write",):
        errmsg = f"Expected scopes ['write'], got {result.scopes}"
        raise AssertionError(errmsg)
    
    return


def test_merge_with_require_auth_or():
    """
        Test that merge_with uses OR for require_auth.
    """
    policy1 = AccessPolicy(require_auth=False)
    policy2 = AccessPolicy(require_auth=True)
    
    result = policy1.merge_with(policy2)
    
    if result.require_auth is not True:
        errmsg = f"Expected require_auth to be True, got {result.require_auth}"
        raise AssertionError(errmsg)
    
    return


def test_merge_with_both_require_auth_false():
    """
        Test that merge_with returns False when both have require_auth=False.
    """
    policy1 = AccessPolicy(require_auth=False)
    policy2 = AccessPolicy(require_auth=False)
    
    result = policy1.merge_with(policy2)
    
    if result.require_auth is not False:
        errmsg = f"Expected require_auth to be False, got {result.require_auth}"
        raise AssertionError(errmsg)
    
    return


def test_merge_with_preserves_order():
    """
        Test that merge_with preserves order (self first, then other).
    """
    policy1 = AccessPolicy(roles=["admin", "user"])
    policy2 = AccessPolicy(roles=["guest"])

    result = policy1.merge_with(policy2)

    expected = ("admin", "user", "guest")
    if result.roles != expected:
        errmsg = f"Expected roles {expected}, got {result.roles}"
        raise AssertionError(errmsg)
    
    return


def test_merge_with_returns_new_instance():
    """
        Test that merge_with returns a new AccessPolicy instance.
    """
    policy1 = AccessPolicy(roles=["admin"])
    policy2 = AccessPolicy(roles=["user"])
    
    result = policy1.merge_with(policy2)
    
    if result is policy1:
        errmsg = "Expected new instance, got same as policy1"
        raise AssertionError(errmsg)
    
    if result is policy2:
        errmsg = "Expected new instance, got same as policy2"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for AccessPolicy - check method
# =============================================================================

def test_check_unauthenticated_user_fails_when_auth_required():
    """
        Test that check returns False for unauthenticated user when auth required.
    """
    policy = AccessPolicy(require_auth=True)
    user = MockUser(is_authenticated=False)
    
    result = policy.check(user)
    
    if result is not False:
        errmsg = f"Expected False, got {result}"
        raise AssertionError(errmsg)
    
    return


def test_check_unauthenticated_user_passes_when_auth_not_required():
    """
        Test that check returns True for unauthenticated user when auth not required.
    """
    policy = AccessPolicy(require_auth=False)
    user = MockUser(is_authenticated=False)
    
    result = policy.check(user)
    
    if result is not True:
        errmsg = f"Expected True, got {result}"
        raise AssertionError(errmsg)
    
    return


def test_check_authenticated_user_passes_empty_policy():
    """
        Test that check returns True for authenticated user with empty policy.
    """
    policy = AccessPolicy()
    user = MockUser(is_authenticated=True)
    
    result = policy.check(user)
    
    if result is not True:
        errmsg = f"Expected True, got {result}"
        raise AssertionError(errmsg)
    
    return


def test_check_user_with_matching_role():
    """
        Test that check returns True when user has a matching role.
    """
    policy = AccessPolicy(roles=["admin", "user"])
    user = MockUser(roles=["user"], is_authenticated=True)
    
    result = policy.check(user)
    
    if result is not True:
        errmsg = f"Expected True, got {result}"
        raise AssertionError(errmsg)
    
    return


def test_check_user_without_matching_role():
    """
        Test that check returns False when user has no matching role.
    """
    policy = AccessPolicy(roles=["admin"])
    user = MockUser(roles=["user"], is_authenticated=True)
    
    result = policy.check(user)
    
    if result is not False:
        errmsg = f"Expected False, got {result}"
        raise AssertionError(errmsg)
    
    return


def test_check_user_with_all_required_scopes():
    """
        Test that check returns True when user has all required scopes.
    """
    policy = AccessPolicy(scopes=["read", "write"])
    user = MockUser(scopes=["read", "write", "delete"], is_authenticated=True)
    
    result = policy.check(user)
    
    if result is not True:
        errmsg = f"Expected True, got {result}"
        raise AssertionError(errmsg)
    
    return


def test_check_user_missing_required_scope():
    """
        Test that check returns False when user is missing a required scope.
    """
    policy = AccessPolicy(scopes=["read", "write"])
    user = MockUser(scopes=["read"], is_authenticated=True)
    
    result = policy.check(user)
    
    if result is not False:
        errmsg = f"Expected False, got {result}"
        raise AssertionError(errmsg)
    
    return


def test_check_user_with_role_and_scopes():
    """
        Test that check returns True when user has matching role and all scopes.
    """
    policy = AccessPolicy(roles=["admin"], scopes=["read", "write"])
    user = MockUser(roles=["admin"], scopes=["read", "write"], is_authenticated=True)
    
    result = policy.check(user)
    
    if result is not True:
        errmsg = f"Expected True, got {result}"
        raise AssertionError(errmsg)
    
    return


def test_check_user_with_role_but_missing_scope():
    """
        Test that check returns False when user has role but missing scope.
    """
    policy = AccessPolicy(roles=["admin"], scopes=["read", "write"])
    user = MockUser(roles=["admin"], scopes=["read"], is_authenticated=True)
    
    result = policy.check(user)
    
    if result is not False:
        errmsg = f"Expected False, got {result}"
        raise AssertionError(errmsg)
    
    return


def test_check_user_with_scope_but_missing_role():
    """
        Test that check returns False when user has scopes but missing role.
    """
    policy = AccessPolicy(roles=["admin"], scopes=["read"])
    user = MockUser(roles=["user"], scopes=["read"], is_authenticated=True)
    
    result = policy.check(user)
    
    if result is not False:
        errmsg = f"Expected False, got {result}"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for AccessPolicy - check_authentication_context method
# =============================================================================

from datetime import datetime, timedelta
from ccai.webworks.authentication.core import AuthenticationContext, Principal


def _create_test_context(
    identifier: str = "test-user",
    roles: set = None,
    permissions: set = None,
    expired: bool = False
) -> AuthenticationContext:
    """
        Helper to create an AuthenticationContext for testing.
    """
    principal = Principal(
        identifier=identifier,
        roles=roles or set(),
        permissions=permissions or set()
    )
    
    expires_at = None
    if expired:
        expires_at = datetime.utcnow() - timedelta(hours=1)
    
    return AuthenticationContext(
        principal=principal,
        scheme="Test"
    )


def _create_expired_context(
    identifier: str = "test-user",
    roles: set = None,
    permissions: set = None
) -> AuthenticationContext:
    """
        Helper to create an expired AuthenticationContext for testing.
    """
    principal = Principal(
        identifier=identifier,
        roles=roles or set(),
        permissions=permissions or set()
    )
    
    return AuthenticationContext(
        principal=principal,
        scheme="Test",
        expires_at=datetime.utcnow() - timedelta(hours=1)
    )


def test_check_authentication_context_none_fails_when_auth_required():
    """
        Test that check_authentication_context returns False for None context
        when auth is required.
    """
    policy = AccessPolicy(require_auth=True)
    
    result = policy.check_authentication_context(None)
    
    if result is not False:
        errmsg = f"Expected False, got {result}"
        raise AssertionError(errmsg)
    
    return


def test_check_authentication_context_none_passes_when_auth_not_required():
    """
        Test that check_authentication_context returns True for None context
        when auth is not required.
    """
    policy = AccessPolicy(require_auth=False)
    
    result = policy.check_authentication_context(None)
    
    if result is not True:
        errmsg = f"Expected True, got {result}"
        raise AssertionError(errmsg)
    
    return


def test_check_authentication_context_expired_fails_when_auth_required():
    """
        Test that check_authentication_context returns False for expired context
        when auth is required.
    """
    policy = AccessPolicy(require_auth=True)
    context = _create_expired_context()
    
    result = policy.check_authentication_context(context)
    
    if result is not False:
        errmsg = f"Expected False, got {result}"
        raise AssertionError(errmsg)
    
    return


def test_check_authentication_context_valid_passes_empty_policy():
    """
        Test that check_authentication_context returns True for valid context
        with empty policy.
    """
    policy = AccessPolicy()
    context = _create_test_context()
    
    result = policy.check_authentication_context(context)
    
    if result is not True:
        errmsg = f"Expected True, got {result}"
        raise AssertionError(errmsg)
    
    return


def test_check_authentication_context_with_matching_role():
    """
        Test that check_authentication_context returns True when principal
        has a matching role.
    """
    policy = AccessPolicy(roles=["admin", "user"])
    context = _create_test_context(roles={"user"})
    
    result = policy.check_authentication_context(context)
    
    if result is not True:
        errmsg = f"Expected True, got {result}"
        raise AssertionError(errmsg)
    
    return


def test_check_authentication_context_without_matching_role():
    """
        Test that check_authentication_context returns False when principal
        has no matching role.
    """
    policy = AccessPolicy(roles=["admin"])
    context = _create_test_context(roles={"user"})
    
    result = policy.check_authentication_context(context)
    
    if result is not False:
        errmsg = f"Expected False, got {result}"
        raise AssertionError(errmsg)
    
    return


def test_check_authentication_context_with_all_required_permissions():
    """
        Test that check_authentication_context returns True when principal
        has all required permissions (scopes).
    """
    policy = AccessPolicy(scopes=["read", "write"])
    context = _create_test_context(permissions={"read", "write", "delete"})
    
    result = policy.check_authentication_context(context)
    
    if result is not True:
        errmsg = f"Expected True, got {result}"
        raise AssertionError(errmsg)
    
    return


def test_check_authentication_context_missing_required_permission():
    """
        Test that check_authentication_context returns False when principal
        is missing a required permission.
    """
    policy = AccessPolicy(scopes=["read", "write"])
    context = _create_test_context(permissions={"read"})
    
    result = policy.check_authentication_context(context)
    
    if result is not False:
        errmsg = f"Expected False, got {result}"
        raise AssertionError(errmsg)
    
    return


def test_check_authentication_context_with_role_and_permissions():
    """
        Test that check_authentication_context returns True when principal
        has matching role and all permissions.
    """
    policy = AccessPolicy(roles=["admin"], scopes=["read", "write"])
    context = _create_test_context(roles={"admin"}, permissions={"read", "write"})
    
    result = policy.check_authentication_context(context)
    
    if result is not True:
        errmsg = f"Expected True, got {result}"
        raise AssertionError(errmsg)
    
    return


def test_check_authentication_context_with_role_but_missing_permission():
    """
        Test that check_authentication_context returns False when principal
        has role but missing permission.
    """
    policy = AccessPolicy(roles=["admin"], scopes=["read", "write"])
    context = _create_test_context(roles={"admin"}, permissions={"read"})
    
    result = policy.check_authentication_context(context)
    
    if result is not False:
        errmsg = f"Expected False, got {result}"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for AccessPolicy - check_roles method
# =============================================================================

def test_check_roles_no_roles_required():
    """
        Test that check_roles returns True when no roles are required.
    """
    policy = AccessPolicy(roles=[])
    context = _create_test_context()
    
    result = policy.check_roles(context)
    
    if result is not True:
        errmsg = f"Expected True, got {result}"
        raise AssertionError(errmsg)
    
    return


def test_check_roles_none_context_fails():
    """
        Test that check_roles returns False for None context when roles required.
    """
    policy = AccessPolicy(roles=["admin"])
    
    result = policy.check_roles(None)
    
    if result is not False:
        errmsg = f"Expected False, got {result}"
        raise AssertionError(errmsg)
    
    return


def test_check_roles_expired_context_fails():
    """
        Test that check_roles returns False for expired context.
    """
    policy = AccessPolicy(roles=["admin"])
    context = _create_expired_context(roles={"admin"})
    
    result = policy.check_roles(context)
    
    if result is not False:
        errmsg = f"Expected False, got {result}"
        raise AssertionError(errmsg)
    
    return


def test_check_roles_matching_role():
    """
        Test that check_roles returns True when principal has matching role.
    """
    policy = AccessPolicy(roles=["admin", "user"])
    context = _create_test_context(roles={"user"})
    
    result = policy.check_roles(context)
    
    if result is not True:
        errmsg = f"Expected True, got {result}"
        raise AssertionError(errmsg)
    
    return


def test_check_roles_no_matching_role():
    """
        Test that check_roles returns False when principal has no matching role.
    """
    policy = AccessPolicy(roles=["admin"])
    context = _create_test_context(roles={"user"})
    
    result = policy.check_roles(context)
    
    if result is not False:
        errmsg = f"Expected False, got {result}"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for AccessPolicy - check_permissions method
# =============================================================================

def test_check_permissions_no_permissions_required():
    """
        Test that check_permissions returns True when no permissions required.
    """
    policy = AccessPolicy(scopes=[])
    context = _create_test_context()
    
    result = policy.check_permissions(context)
    
    if result is not True:
        errmsg = f"Expected True, got {result}"
        raise AssertionError(errmsg)
    
    return


def test_check_permissions_none_context_fails():
    """
        Test that check_permissions returns False for None context when
        permissions required.
    """
    policy = AccessPolicy(scopes=["read"])
    
    result = policy.check_permissions(None)
    
    if result is not False:
        errmsg = f"Expected False, got {result}"
        raise AssertionError(errmsg)
    
    return


def test_check_permissions_expired_context_fails():
    """
        Test that check_permissions returns False for expired context.
    """
    policy = AccessPolicy(scopes=["read"])
    context = _create_expired_context(permissions={"read"})
    
    result = policy.check_permissions(context)
    
    if result is not False:
        errmsg = f"Expected False, got {result}"
        raise AssertionError(errmsg)
    
    return


def test_check_permissions_all_permissions_present():
    """
        Test that check_permissions returns True when principal has all
        required permissions.
    """
    policy = AccessPolicy(scopes=["read", "write"])
    context = _create_test_context(permissions={"read", "write", "delete"})
    
    result = policy.check_permissions(context)
    
    if result is not True:
        errmsg = f"Expected True, got {result}"
        raise AssertionError(errmsg)
    
    return


def test_check_permissions_missing_permission():
    """
        Test that check_permissions returns False when principal is missing
        a required permission.
    """
    policy = AccessPolicy(scopes=["read", "write"])
    context = _create_test_context(permissions={"read"})
    
    result = policy.check_permissions(context)
    
    if result is not False:
        errmsg = f"Expected False, got {result}"
        raise AssertionError(errmsg)
    
    return
