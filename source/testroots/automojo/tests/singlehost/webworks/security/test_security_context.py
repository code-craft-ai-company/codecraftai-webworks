"""
    Tests for the Security_Context frozen dataclass.

    This module contains unit tests for the Security_Context class including
    field defaults, is_authenticated and is_expired properties, role and scope
    helper methods, the guest() classmethod, and immutability verification.
"""

from datetime import datetime, timedelta, timezone

from automojo.webworks.security.securitycontext import SecurityContext


# =============================================================================
# Unit Tests for Security_Context Fields and Defaults
# =============================================================================

def test_security_context_default_fields():
    """
        Test that a default Security_Context has expected default values.
    """
    ctx = SecurityContext()

    if ctx.user_id is not None:
        errmsg = f"Expected user_id to be None, got '{ctx.user_id}'"
        raise AssertionError(errmsg)

    if ctx.username is not None:
        errmsg = f"Expected username to be None, got '{ctx.username}'"
        raise AssertionError(errmsg)

    if ctx.email is not None:
        errmsg = f"Expected email to be None, got '{ctx.email}'"
        raise AssertionError(errmsg)

    if ctx.roles != ():
        errmsg = f"Expected roles to be empty tuple, got {ctx.roles}"
        raise AssertionError(errmsg)

    if ctx.scopes != ():
        errmsg = f"Expected scopes to be empty tuple, got {ctx.scopes}"
        raise AssertionError(errmsg)

    if ctx.provider is not None:
        errmsg = f"Expected provider to be None, got '{ctx.provider}'"
        raise AssertionError(errmsg)

    if ctx.authenticated_at is not None:
        errmsg = f"Expected authenticated_at to be None, got '{ctx.authenticated_at}'"
        raise AssertionError(errmsg)

    if ctx.expires_at is not None:
        errmsg = f"Expected expires_at to be None, got '{ctx.expires_at}'"
        raise AssertionError(errmsg)

    if ctx.extra != {}:
        errmsg = f"Expected extra to be empty dict, got {ctx.extra}"
        raise AssertionError(errmsg)

    return


def test_security_context_with_all_fields():
    """
        Test that Security_Context can be created with all fields populated.
    """
    now = datetime.now(timezone.utc)
    later = now + timedelta(hours=1)

    ctx = SecurityContext(
        user_id="user-123",
        username="testuser",
        email="test@example.com",
        roles=("admin", "editor"),
        scopes=("read", "write"),
        provider="jwt",
        authenticated_at=now,
        expires_at=later,
        extra={"tenant": "acme"}
    )

    if ctx.user_id != "user-123":
        errmsg = f"Expected user_id 'user-123', got '{ctx.user_id}'"
        raise AssertionError(errmsg)

    if ctx.username != "testuser":
        errmsg = f"Expected username 'testuser', got '{ctx.username}'"
        raise AssertionError(errmsg)

    if ctx.email != "test@example.com":
        errmsg = f"Expected email 'test@example.com', got '{ctx.email}'"
        raise AssertionError(errmsg)

    if ctx.roles != ("admin", "editor"):
        errmsg = f"Expected roles ('admin', 'editor'), got {ctx.roles}"
        raise AssertionError(errmsg)

    if ctx.scopes != ("read", "write"):
        errmsg = f"Expected scopes ('read', 'write'), got {ctx.scopes}"
        raise AssertionError(errmsg)

    if ctx.provider != "jwt":
        errmsg = f"Expected provider 'jwt', got '{ctx.provider}'"
        raise AssertionError(errmsg)

    if ctx.authenticated_at != now:
        errmsg = f"Expected authenticated_at '{now}', got '{ctx.authenticated_at}'"
        raise AssertionError(errmsg)

    if ctx.expires_at != later:
        errmsg = f"Expected expires_at '{later}', got '{ctx.expires_at}'"
        raise AssertionError(errmsg)

    if ctx.extra != {"tenant": "acme"}:
        errmsg = f"Expected extra {{'tenant': 'acme'}}, got {ctx.extra}"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for is_authenticated Property
# =============================================================================

def test_is_authenticated_true_when_user_id_present():
    """
        Test that is_authenticated returns True when user_id is set.
    """
    ctx = SecurityContext(user_id="user-456")

    result = ctx.is_authenticated

    if result is not True:
        errmsg = f"Expected is_authenticated to be True, got {result}"
        raise AssertionError(errmsg)

    return


def test_is_authenticated_false_when_user_id_none():
    """
        Test that is_authenticated returns False when user_id is None.
    """
    ctx = SecurityContext()

    result = ctx.is_authenticated

    if result is not False:
        errmsg = f"Expected is_authenticated to be False, got {result}"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for is_expired Property
# =============================================================================

def test_is_expired_false_when_no_expiration():
    """
        Test that is_expired returns False when expires_at is None.
    """
    ctx = SecurityContext(user_id="user-789")

    result = ctx.is_expired

    if result is not False:
        errmsg = f"Expected is_expired to be False when expires_at is None, got {result}"
        raise AssertionError(errmsg)

    return


def test_is_expired_false_when_not_yet_expired():
    """
        Test that is_expired returns False when expires_at is in the future.
    """
    future = datetime.now(timezone.utc) + timedelta(hours=1)
    ctx = SecurityContext(user_id="user-789", expires_at=future)

    result = ctx.is_expired

    if result is not False:
        errmsg = f"Expected is_expired to be False for future expiration, got {result}"
        raise AssertionError(errmsg)

    return


def test_is_expired_true_when_past_expiration():
    """
        Test that is_expired returns True when expires_at is in the past.
    """
    past = datetime.now(timezone.utc) - timedelta(hours=1)
    ctx = SecurityContext(user_id="user-789", expires_at=past)

    result = ctx.is_expired

    if result is not True:
        errmsg = f"Expected is_expired to be True for past expiration, got {result}"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for has_role()
# =============================================================================

def test_has_role_returns_true_for_present_role():
    """
        Test that has_role returns True when the role is in the context.
    """
    ctx = SecurityContext(roles=("admin", "editor"))

    result = ctx.has_role("admin")

    if result is not True:
        errmsg = "Expected has_role('admin') to be True"
        raise AssertionError(errmsg)

    return


def test_has_role_returns_false_for_absent_role():
    """
        Test that has_role returns False when the role is not in the context.
    """
    ctx = SecurityContext(roles=("editor",))

    result = ctx.has_role("admin")

    if result is not False:
        errmsg = "Expected has_role('admin') to be False"
        raise AssertionError(errmsg)

    return


def test_has_role_returns_false_for_empty_roles():
    """
        Test that has_role returns False when the context has no roles.
    """
    ctx = SecurityContext()

    result = ctx.has_role("admin")

    if result is not False:
        errmsg = "Expected has_role('admin') to be False for empty roles"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for has_scope()
# =============================================================================

def test_has_scope_returns_true_for_present_scope():
    """
        Test that has_scope returns True when the scope is in the context.
    """
    ctx = SecurityContext(scopes=("read", "write"))

    result = ctx.has_scope("read")

    if result is not True:
        errmsg = "Expected has_scope('read') to be True"
        raise AssertionError(errmsg)

    return


def test_has_scope_returns_false_for_absent_scope():
    """
        Test that has_scope returns False when the scope is not in the context.
    """
    ctx = SecurityContext(scopes=("read",))

    result = ctx.has_scope("write")

    if result is not False:
        errmsg = "Expected has_scope('write') to be False"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for has_any_role()
# =============================================================================

def test_has_any_role_returns_true_when_one_matches():
    """
        Test that has_any_role returns True when at least one role matches.
    """
    ctx = SecurityContext(roles=("editor",))

    result = ctx.has_any_role("admin", "editor", "viewer")

    if result is not True:
        errmsg = "Expected has_any_role to be True when 'editor' is present"
        raise AssertionError(errmsg)

    return


def test_has_any_role_returns_false_when_none_match():
    """
        Test that has_any_role returns False when no roles match.
    """
    ctx = SecurityContext(roles=("viewer",))

    result = ctx.has_any_role("admin", "editor")

    if result is not False:
        errmsg = "Expected has_any_role to be False when no roles match"
        raise AssertionError(errmsg)

    return


def test_has_any_role_returns_false_for_empty_roles():
    """
        Test that has_any_role returns False when context has no roles.
    """
    ctx = SecurityContext()

    result = ctx.has_any_role("admin", "editor")

    if result is not False:
        errmsg = "Expected has_any_role to be False for empty roles"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for has_all_scopes()
# =============================================================================

def test_has_all_scopes_returns_true_when_all_present():
    """
        Test that has_all_scopes returns True when all scopes are present.
    """
    ctx = SecurityContext(scopes=("read", "write", "delete"))

    result = ctx.has_all_scopes("read", "write")

    if result is not True:
        errmsg = "Expected has_all_scopes to be True when all scopes present"
        raise AssertionError(errmsg)

    return


def test_has_all_scopes_returns_false_when_one_missing():
    """
        Test that has_all_scopes returns False when one scope is missing.
    """
    ctx = SecurityContext(scopes=("read",))

    result = ctx.has_all_scopes("read", "write")

    if result is not False:
        errmsg = "Expected has_all_scopes to be False when 'write' is missing"
        raise AssertionError(errmsg)

    return


def test_has_all_scopes_returns_true_for_empty_request():
    """
        Test that has_all_scopes returns True when no scopes are requested.
    """
    ctx = SecurityContext(scopes=("read",))

    result = ctx.has_all_scopes()

    if result is not True:
        errmsg = "Expected has_all_scopes() with no args to be True"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for guest() Classmethod
# =============================================================================

def test_guest_returns_unauthenticated_context():
    """
        Test that guest() returns a context with is_authenticated False.
    """
    ctx = SecurityContext.guest()

    if ctx.is_authenticated is not False:
        errmsg = "Expected guest context to have is_authenticated False"
        raise AssertionError(errmsg)

    if ctx.user_id is not None:
        errmsg = f"Expected guest user_id to be None, got '{ctx.user_id}'"
        raise AssertionError(errmsg)

    if ctx.roles != ():
        errmsg = f"Expected guest roles to be empty tuple, got {ctx.roles}"
        raise AssertionError(errmsg)

    if ctx.scopes != ():
        errmsg = f"Expected guest scopes to be empty tuple, got {ctx.scopes}"
        raise AssertionError(errmsg)

    return


def test_guest_returns_security_context_instance():
    """
        Regression test for BUG-5: guest() return type annotation used
        'Security_Context' instead of 'SecurityContext', causing
        get_type_hints() to fail with NameError.
    """
    import typing

    ctx = SecurityContext.guest()

    if not isinstance(ctx, SecurityContext):
        errmsg = f"Expected guest() to return SecurityContext instance, got {type(ctx).__name__}"
        raise AssertionError(errmsg)

    # Verify get_type_hints resolves cleanly (would raise NameError with wrong annotation)
    try:
        hints = typing.get_type_hints(SecurityContext.guest)
    except NameError as err:
        errmsg = f"get_type_hints(SecurityContext.guest) raised NameError: {err}"
        raise AssertionError(errmsg)

    return_type = hints.get("return")
    if return_type is not SecurityContext:
        errmsg = f"Expected return type hint to be SecurityContext, got {return_type}"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for Immutability (Frozen Dataclass)
# =============================================================================

def test_security_context_is_immutable():
    """
        Test that Security_Context fields cannot be modified after creation.
    """
    ctx = SecurityContext(user_id="user-123", roles=("admin",))

    try:
        ctx.user_id = "user-999"
        errmsg = "Expected FrozenInstanceError when setting user_id"
        raise AssertionError(errmsg)
    except AttributeError:
        pass

    try:
        ctx.roles = ("hacker",)
        errmsg = "Expected FrozenInstanceError when setting roles"
        raise AssertionError(errmsg)
    except AttributeError:
        pass

    return


# =============================================================================
# Property-Based Tests for Security Context Integrity
# **Validates: Requirements 8.6, 8.7**
# =============================================================================

import random
import string


def _random_string(min_length=1, max_length=20):
    """
        Generate a random alphanumeric string.
    """
    length = random.randint(min_length, max_length)
    rtnval = "".join(random.choices(string.ascii_lowercase + string.digits, k=length))
    return rtnval


def _random_string_tuple(min_count=0, max_count=8):
    """
        Generate a tuple of unique random strings.
    """
    count = random.randint(min_count, max_count)
    items = set()
    while len(items) < count:
        items.add(_random_string())
    rtnval = tuple(items)
    return rtnval


def _generate_random_security_context():
    """
        Generate a random Security_Context with random roles and scopes.
    """
    user_id = _random_string() if random.random() > 0.3 else None
    roles = _random_string_tuple(min_count=0, max_count=8)
    scopes = _random_string_tuple(min_count=0, max_count=8)

    ctx = SecurityContext(
        user_id=user_id,
        roles=roles,
        scopes=scopes
    )
    return ctx, roles, scopes


def test_property_security_context_immutability():
    """
        Property 6 (part 1): Security_Context SHALL be immutable after creation.

        For 100 random contexts, verify that attempting to set any attribute
        raises an AttributeError.

        **Validates: Requirements 8.6, 8.7**
    """
    num_iterations = 100
    attributes_to_test = ("user_id", "username", "email", "roles", "scopes", "provider")

    for iteration in range(num_iterations):
        ctx, _, _ = _generate_random_security_context()

        for attr_name in attributes_to_test:
            try:
                setattr(ctx, attr_name, "tampered")
                errmsg = (
                    f"Iteration {iteration}: Expected AttributeError when setting "
                    f"'{attr_name}' on frozen Security_Context"
                )
                raise AssertionError(errmsg)
            except AttributeError:
                pass

    return


def test_property_has_role_iff_in_roles():
    """
        Property 6 (part 2): has_role(r) SHALL return True iff r is in C.roles.

        For 100 random contexts, verify has_role returns True for every role
        in the context and False for roles not in the context.

        **Validates: Requirements 8.6, 8.7**
    """
    num_iterations = 100

    for iteration in range(num_iterations):
        ctx, roles, _ = _generate_random_security_context()

        # Verify has_role returns True for every role in the context
        for role in roles:
            result = ctx.has_role(role)
            if result is not True:
                errmsg = (
                    f"Iteration {iteration}: has_role('{role}') returned False "
                    f"but role is in roles={roles}"
                )
                raise AssertionError(errmsg)

        # Verify has_role returns False for roles not in the context
        for _ in range(5):
            absent_role = _random_string(min_length=21, max_length=30)
            result = ctx.has_role(absent_role)
            if result is not False:
                errmsg = (
                    f"Iteration {iteration}: has_role('{absent_role}') returned True "
                    f"but role is not in roles={roles}"
                )
                raise AssertionError(errmsg)

    return


def test_property_has_scope_iff_in_scopes():
    """
        Property 6 (part 3): has_scope(s) SHALL return True iff s is in C.scopes.

        For 100 random contexts, verify has_scope returns True for every scope
        in the context and False for scopes not in the context.

        **Validates: Requirements 8.6, 8.7**
    """
    num_iterations = 100

    for iteration in range(num_iterations):
        ctx, _, scopes = _generate_random_security_context()

        # Verify has_scope returns True for every scope in the context
        for scope in scopes:
            result = ctx.has_scope(scope)
            if result is not True:
                errmsg = (
                    f"Iteration {iteration}: has_scope('{scope}') returned False "
                    f"but scope is in scopes={scopes}"
                )
                raise AssertionError(errmsg)

        # Verify has_scope returns False for scopes not in the context
        for _ in range(5):
            absent_scope = _random_string(min_length=21, max_length=30)
            result = ctx.has_scope(absent_scope)
            if result is not False:
                errmsg = (
                    f"Iteration {iteration}: has_scope('{absent_scope}') returned True "
                    f"but scope is not in scopes={scopes}"
                )
                raise AssertionError(errmsg)

    return


def test_property_has_any_role_iff_any_in_roles():
    """
        Property 6 (part 4): has_any_role(*rs) SHALL return True iff any r in rs
        is in C.roles.

        For 100 random contexts, generate random query role sets and verify
        has_any_role matches the expected set intersection logic.

        **Validates: Requirements 8.6, 8.7**
    """
    num_iterations = 100

    for iteration in range(num_iterations):
        ctx, roles, _ = _generate_random_security_context()
        roles_set = set(roles)

        # Generate a random query set mixing present and absent roles
        query_roles = list(_random_string_tuple(min_count=1, max_count=6))

        # Optionally inject some roles that are actually in the context
        if roles and random.random() > 0.5:
            inject_count = random.randint(1, min(3, len(roles)))
            query_roles.extend(random.sample(list(roles), inject_count))

        expected = any(r in roles_set for r in query_roles)
        result = ctx.has_any_role(*query_roles)

        if result != expected:
            errmsg = (
                f"Iteration {iteration}: has_any_role({query_roles}) returned {result}, "
                f"expected {expected}. Context roles={roles}"
            )
            raise AssertionError(errmsg)

    return


def test_property_has_all_scopes_iff_all_in_scopes():
    """
        Property 6 (part 5): has_all_scopes(*ss) SHALL return True iff all s in ss
        are in C.scopes.

        For 100 random contexts, generate random query scope sets and verify
        has_all_scopes matches the expected subset logic.

        **Validates: Requirements 8.6, 8.7**
    """
    num_iterations = 100

    for iteration in range(num_iterations):
        ctx, _, scopes = _generate_random_security_context()
        scopes_set = set(scopes)

        # Generate a random query set mixing present and absent scopes
        query_scopes = list(_random_string_tuple(min_count=0, max_count=6))

        # Optionally inject some scopes that are actually in the context
        if scopes and random.random() > 0.5:
            inject_count = random.randint(1, min(3, len(scopes)))
            query_scopes.extend(random.sample(list(scopes), inject_count))

        expected = all(s in scopes_set for s in query_scopes)
        result = ctx.has_all_scopes(*query_scopes)

        if result != expected:
            errmsg = (
                f"Iteration {iteration}: has_all_scopes({query_scopes}) returned {result}, "
                f"expected {expected}. Context scopes={scopes}"
            )
            raise AssertionError(errmsg)

    return
