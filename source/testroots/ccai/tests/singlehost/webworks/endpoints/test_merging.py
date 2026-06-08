"""
    Tests for the ConstraintMerger utility class.
    
    This module contains unit tests for the constraint merge utilities
    used in blueprint endpoint inheritance.
"""

from ccai.webworks.endpoints.accesspolicy import AccessPolicy
from ccai.webworks.endpoints.merging import ConstraintMerger
from ccai.webworks.endpoints.ratelimit import RateLimit


# =============================================================================
# Unit Tests for ConstraintMerger.merge_access_policies
# =============================================================================

def test_merge_access_policies_both_none():
    """
        Test that merge_access_policies returns None when both are None.
    """
    result = ConstraintMerger.merge_access_policies(None, None)
    
    if result is not None:
        errmsg = f"Expected None, got {result}"
        raise AssertionError(errmsg)
    
    return


def test_merge_access_policies_child_none_inherits_parent():
    """
        Test that child inherits parent when child is None.
    """
    parent = AccessPolicy(roles=["admin"], scopes=["read"])
    result = ConstraintMerger.merge_access_policies(parent, None)
    
    if result is not parent:
        errmsg = f"Expected parent policy, got {result}"
        raise AssertionError(errmsg)
    
    return


def test_merge_access_policies_parent_none_uses_child():
    """
        Test that child is used when parent is None.
    """
    child = AccessPolicy(roles=["user"], scopes=["write"])
    result = ConstraintMerger.merge_access_policies(None, child)
    
    if result is not child:
        errmsg = f"Expected child policy, got {result}"
        raise AssertionError(errmsg)
    
    return


def test_merge_access_policies_union_roles_by_default():
    """
        Test that roles are unioned by default.
    """
    parent = AccessPolicy(roles=["admin"], scopes=[])
    child = AccessPolicy(roles=["user"], scopes=[])
    
    result = ConstraintMerger.merge_access_policies(parent, child)
    
    if "admin" not in result.roles:
        errmsg = f"Expected 'admin' in roles, got {result.roles}"
        raise AssertionError(errmsg)
    
    if "user" not in result.roles:
        errmsg = f"Expected 'user' in roles, got {result.roles}"
        raise AssertionError(errmsg)
    
    return


def test_merge_access_policies_union_scopes_by_default():
    """
        Test that scopes are unioned by default.
    """
    parent = AccessPolicy(roles=[], scopes=["read"])
    child = AccessPolicy(roles=[], scopes=["write"])
    
    result = ConstraintMerger.merge_access_policies(parent, child)
    
    if "read" not in result.scopes:
        errmsg = f"Expected 'read' in scopes, got {result.scopes}"
        raise AssertionError(errmsg)
    
    if "write" not in result.scopes:
        errmsg = f"Expected 'write' in scopes, got {result.scopes}"
        raise AssertionError(errmsg)
    
    return


def test_merge_access_policies_replace_roles():
    """
        Test that replace_roles=True causes child roles to replace parent.
    """
    parent = AccessPolicy(roles=["admin"], scopes=[])
    child = AccessPolicy(roles=["user"], scopes=[])
    
    result = ConstraintMerger.merge_access_policies(
        parent, child, replace_roles=True
    )
    
    if "admin" in result.roles:
        errmsg = f"Expected 'admin' NOT in roles, got {result.roles}"
        raise AssertionError(errmsg)
    
    if "user" not in result.roles:
        errmsg = f"Expected 'user' in roles, got {result.roles}"
        raise AssertionError(errmsg)
    
    return


def test_merge_access_policies_replace_scopes():
    """
        Test that replace_scopes=True causes child scopes to replace parent.
    """
    parent = AccessPolicy(roles=[], scopes=["read"])
    child = AccessPolicy(roles=[], scopes=["write"])
    
    result = ConstraintMerger.merge_access_policies(
        parent, child, replace_scopes=True
    )
    
    if "read" in result.scopes:
        errmsg = f"Expected 'read' NOT in scopes, got {result.scopes}"
        raise AssertionError(errmsg)
    
    if "write" not in result.scopes:
        errmsg = f"Expected 'write' in scopes, got {result.scopes}"
        raise AssertionError(errmsg)
    
    return


def test_merge_access_policies_require_auth_logical_or():
    """
        Test that require_auth is True if either policy requires it.
    """
    parent = AccessPolicy(roles=[], scopes=[], require_auth=True)
    child = AccessPolicy(roles=[], scopes=[], require_auth=False)
    
    result = ConstraintMerger.merge_access_policies(parent, child)
    
    if not result.require_auth:
        errmsg = "Expected require_auth to be True (logical OR)"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for ConstraintMerger.merge_rate_limits
# =============================================================================

def test_merge_rate_limits_both_none():
    """
        Test that merge_rate_limits returns None when both are None.
    """
    result = ConstraintMerger.merge_rate_limits(None, None)
    
    if result is not None:
        errmsg = f"Expected None, got {result}"
        raise AssertionError(errmsg)
    
    return


def test_merge_rate_limits_child_none_inherits_parent():
    """
        Test that child inherits parent when child is None.
    """
    parent = RateLimit(requests=100, window=60)
    result = ConstraintMerger.merge_rate_limits(parent, None)
    
    if result is not parent:
        errmsg = f"Expected parent limit, got {result}"
        raise AssertionError(errmsg)
    
    return


def test_merge_rate_limits_parent_none_uses_child():
    """
        Test that child is used when parent is None.
    """
    child = RateLimit(requests=50, window=60)
    result = ConstraintMerger.merge_rate_limits(None, child)
    
    if result is not child:
        errmsg = f"Expected child limit, got {result}"
        raise AssertionError(errmsg)
    
    return


def test_merge_rate_limits_most_restrictive_wins():
    """
        Test that the most restrictive rate limit is returned.
    """
    # 100 req/60s = 1.67 req/s
    parent = RateLimit(requests=100, window=60)
    # 50 req/60s = 0.83 req/s (more restrictive)
    child = RateLimit(requests=50, window=60)
    
    result = ConstraintMerger.merge_rate_limits(parent, child)
    
    if result is not child:
        errmsg = f"Expected child (more restrictive), got {result}"
        raise AssertionError(errmsg)
    
    return


def test_merge_rate_limits_parent_more_restrictive():
    """
        Test that parent is returned when it's more restrictive.
    """
    # 10 req/60s = 0.17 req/s (more restrictive)
    parent = RateLimit(requests=10, window=60)
    # 100 req/60s = 1.67 req/s
    child = RateLimit(requests=100, window=60)
    
    result = ConstraintMerger.merge_rate_limits(parent, child)
    
    if result is not parent:
        errmsg = f"Expected parent (more restrictive), got {result}"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for ConstraintMerger.merge_tags
# =============================================================================

def test_merge_tags_default_child_wins():
    """
        Test that child tags win by default when child has tags.
    """
    parent = ["api", "v1"]
    child = ["admin"]
    
    result = ConstraintMerger.merge_tags(parent, child)
    
    if result != ["admin"]:
        errmsg = f"Expected ['admin'], got {result}"
        raise AssertionError(errmsg)
    
    return


def test_merge_tags_default_inherits_parent_when_child_empty():
    """
        Test that parent tags are inherited when child is empty.
    """
    parent = ["api", "v1"]
    child = []
    
    result = ConstraintMerger.merge_tags(parent, child)
    
    if result != ["api", "v1"]:
        errmsg = f"Expected ['api', 'v1'], got {result}"
        raise AssertionError(errmsg)
    
    return


def test_merge_tags_merge_mode():
    """
        Test that merge=True appends parent tags to child tags.
    """
    parent = ["api", "v1"]
    child = ["admin"]
    
    result = ConstraintMerger.merge_tags(parent, child, merge=True)
    
    if "admin" not in result:
        errmsg = f"Expected 'admin' in result, got {result}"
        raise AssertionError(errmsg)
    
    if "api" not in result:
        errmsg = f"Expected 'api' in result, got {result}"
        raise AssertionError(errmsg)
    
    if "v1" not in result:
        errmsg = f"Expected 'v1' in result, got {result}"
        raise AssertionError(errmsg)
    
    return


def test_merge_tags_merge_mode_preserves_order():
    """
        Test that merge mode puts child tags first, then parent.
    """
    parent = ["api", "v1"]
    child = ["admin"]
    
    result = ConstraintMerger.merge_tags(parent, child, merge=True)
    
    # Child tags should come first
    if result[0] != "admin":
        errmsg = f"Expected 'admin' first, got {result}"
        raise AssertionError(errmsg)
    
    return


def test_merge_tags_merge_mode_no_duplicates():
    """
        Test that merge mode doesn't create duplicates.
    """
    parent = ["api", "v1"]
    child = ["api", "admin"]
    
    result = ConstraintMerger.merge_tags(parent, child, merge=True)
    
    api_count = result.count("api")
    if api_count != 1:
        errmsg = f"Expected 'api' once, got {api_count} times in {result}"
        raise AssertionError(errmsg)
    
    return


def test_merge_tags_replace_mode():
    """
        Test that replace=True causes child to fully replace parent.
    """
    parent = ["api", "v1"]
    child = ["admin"]
    
    result = ConstraintMerger.merge_tags(parent, child, replace=True)
    
    if result != ["admin"]:
        errmsg = f"Expected ['admin'], got {result}"
        raise AssertionError(errmsg)
    
    return


def test_merge_tags_replace_mode_empty_child():
    """
        Test that replace=True with empty child returns empty list.
    """
    parent = ["api", "v1"]
    child = []
    
    result = ConstraintMerger.merge_tags(parent, child, replace=True)
    
    if result != []:
        errmsg = f"Expected [], got {result}"
        raise AssertionError(errmsg)
    
    return


def test_merge_tags_returns_copy():
    """
        Test that merge_tags returns a copy, not the original list.
    """
    parent = ["api", "v1"]
    child = ["admin"]
    
    result = ConstraintMerger.merge_tags(parent, child)
    
    if result is child:
        errmsg = "Expected a copy, got the same list object"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Property 7: Security Policy Composition
# Feature: blueprint-endpoints, Property 7: Security Policy Composition
# Validates: Requirements 2.8
# =============================================================================

import random
import string


def _generate_random_string(min_len: int = 3, max_len: int = 10) -> str:
    """Generate a random alphanumeric string."""
    length = random.randint(min_len, max_len)
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))


def _generate_random_roles() -> list:
    """Generate a random list of roles."""
    num_roles = random.randint(1, 4)
    return [f"role_{_generate_random_string(3, 6)}" for _ in range(num_roles)]


def _generate_random_scopes() -> list:
    """Generate a random list of scopes."""
    num_scopes = random.randint(1, 4)
    return [f"scope_{_generate_random_string(3, 6)}" for _ in range(num_scopes)]


def test_property_7_security_policy_composition():
    """
        Property 7: Security Policy Composition
        
        *For any* endpoint with multiple applicable policies (e.g., blueprint
        policy + handler policy), the combined policy SHALL enforce all
        constraints via logical AND, ensuring nested definitions do not
        inadvertently weaken security.
        
        This test generates random parent and child policies and verifies that:
        1. All parent roles are present in the merged policy (union)
        2. All child roles are present in the merged policy (union)
        3. All parent scopes are present in the merged policy (union)
        4. All child scopes are present in the merged policy (union)
        5. require_auth is True if either policy requires it (logical OR)
        
        The combined policy enforces ALL constraints - a user must satisfy
        both the parent AND child requirements.
        
        **Feature: blueprint-endpoints, Property 7: Security Policy Composition**
        **Validates: Requirements 2.8**
    """
    # Run 100 iterations with different random configurations
    for iteration in range(100):
        # Generate random parent policy
        parent_roles = _generate_random_roles()
        parent_scopes = _generate_random_scopes()
        parent_require_auth = random.choice([True, False])
        
        parent_policy = AccessPolicy(
            roles=parent_roles,
            scopes=parent_scopes,
            require_auth=parent_require_auth
        )
        
        # Generate random child policy (different from parent)
        child_roles = _generate_random_roles()
        child_scopes = _generate_random_scopes()
        child_require_auth = random.choice([True, False])
        
        child_policy = AccessPolicy(
            roles=child_roles,
            scopes=child_scopes,
            require_auth=child_require_auth
        )
        
        # Merge policies using ConstraintMerger
        merged_policy = ConstraintMerger.merge_access_policies(
            parent_policy,
            child_policy
        )
        
        # Property 7.1: All parent roles SHALL be in merged policy (union)
        for role in parent_roles:
            if role not in merged_policy.roles:
                errmsg = (
                    f"Iteration {iteration}: Parent role '{role}' should be in merged policy. "
                    f"parent_roles={parent_roles}, merged_roles={merged_policy.roles}. "
                    f"Combined policy must enforce ALL constraints (logical AND)."
                )
                raise AssertionError(errmsg)
        
        # Property 7.2: All child roles SHALL be in merged policy (union)
        for role in child_roles:
            if role not in merged_policy.roles:
                errmsg = (
                    f"Iteration {iteration}: Child role '{role}' should be in merged policy. "
                    f"child_roles={child_roles}, merged_roles={merged_policy.roles}. "
                    f"Combined policy must enforce ALL constraints (logical AND)."
                )
                raise AssertionError(errmsg)
        
        # Property 7.3: All parent scopes SHALL be in merged policy (union)
        for scope in parent_scopes:
            if scope not in merged_policy.scopes:
                errmsg = (
                    f"Iteration {iteration}: Parent scope '{scope}' should be in merged policy. "
                    f"parent_scopes={parent_scopes}, merged_scopes={merged_policy.scopes}. "
                    f"Combined policy must enforce ALL constraints (logical AND)."
                )
                raise AssertionError(errmsg)
        
        # Property 7.4: All child scopes SHALL be in merged policy (union)
        for scope in child_scopes:
            if scope not in merged_policy.scopes:
                errmsg = (
                    f"Iteration {iteration}: Child scope '{scope}' should be in merged policy. "
                    f"child_scopes={child_scopes}, merged_scopes={merged_policy.scopes}. "
                    f"Combined policy must enforce ALL constraints (logical AND)."
                )
                raise AssertionError(errmsg)
        
        # Property 7.5: require_auth SHALL be True if either policy requires it
        expected_require_auth = parent_require_auth or child_require_auth
        if merged_policy.require_auth != expected_require_auth:
            errmsg = (
                f"Iteration {iteration}: require_auth should be {expected_require_auth} "
                f"(parent={parent_require_auth}, child={child_require_auth}). "
                f"Got {merged_policy.require_auth}. "
                f"Combined policy must enforce ALL constraints (logical AND)."
            )
            raise AssertionError(errmsg)
    
    return


def test_property_7_security_policy_composition_no_weakening():
    """
        Property 7: Security Policy Composition (no weakening)
        
        *For any* parent policy with security constraints, adding a child
        policy SHALL NOT weaken the parent's security requirements.
        
        This test verifies that:
        1. If parent requires role "admin", merged policy still requires "admin"
        2. If parent requires scope "read", merged policy still requires "read"
        3. If parent requires auth, merged policy still requires auth
        
        **Feature: blueprint-endpoints, Property 7: Security Policy Composition**
        **Validates: Requirements 2.8**
    """
    # Run 100 iterations with different random configurations
    for iteration in range(100):
        # Generate parent policy with specific security requirements
        parent_roles = _generate_random_roles()
        parent_scopes = _generate_random_scopes()
        
        parent_policy = AccessPolicy(
            roles=parent_roles,
            scopes=parent_scopes,
            require_auth=True  # Parent always requires auth
        )
        
        # Generate child policy that might try to "weaken" security
        # (e.g., empty roles, empty scopes, require_auth=False)
        child_policy = AccessPolicy(
            roles=[],  # Child has no roles
            scopes=[],  # Child has no scopes
            require_auth=False  # Child doesn't require auth
        )
        
        # Merge policies
        merged_policy = ConstraintMerger.merge_access_policies(
            parent_policy,
            child_policy
        )
        
        # Verify parent roles are NOT removed (security not weakened)
        for role in parent_roles:
            if role not in merged_policy.roles:
                errmsg = (
                    f"Iteration {iteration}: Parent role '{role}' should NOT be removed. "
                    f"Child policy with empty roles should not weaken parent security. "
                    f"parent_roles={parent_roles}, merged_roles={merged_policy.roles}"
                )
                raise AssertionError(errmsg)
        
        # Verify parent scopes are NOT removed (security not weakened)
        for scope in parent_scopes:
            if scope not in merged_policy.scopes:
                errmsg = (
                    f"Iteration {iteration}: Parent scope '{scope}' should NOT be removed. "
                    f"Child policy with empty scopes should not weaken parent security. "
                    f"parent_scopes={parent_scopes}, merged_scopes={merged_policy.scopes}"
                )
                raise AssertionError(errmsg)
        
        # Verify require_auth is still True (parent requires it)
        if not merged_policy.require_auth:
            errmsg = (
                f"Iteration {iteration}: require_auth should still be True. "
                f"Child policy with require_auth=False should not weaken parent security."
            )
            raise AssertionError(errmsg)
    
    return


def test_property_7_security_policy_composition_additive():
    """
        Property 7: Security Policy Composition (additive)
        
        *For any* parent and child policies, the merged policy SHALL be
        additive - combining all constraints from both policies.
        
        This test verifies that the merged policy contains the union of
        all roles and scopes from both parent and child.
        
        **Feature: blueprint-endpoints, Property 7: Security Policy Composition**
        **Validates: Requirements 2.8**
    """
    # Run 100 iterations with different random configurations
    for iteration in range(100):
        # Generate distinct parent and child roles/scopes
        parent_roles = [f"parent_role_{i}_{_generate_random_string(3, 5)}" for i in range(random.randint(1, 3))]
        parent_scopes = [f"parent_scope_{i}_{_generate_random_string(3, 5)}" for i in range(random.randint(1, 3))]
        
        child_roles = [f"child_role_{i}_{_generate_random_string(3, 5)}" for i in range(random.randint(1, 3))]
        child_scopes = [f"child_scope_{i}_{_generate_random_string(3, 5)}" for i in range(random.randint(1, 3))]
        
        parent_policy = AccessPolicy(
            roles=parent_roles,
            scopes=parent_scopes,
            require_auth=True
        )
        
        child_policy = AccessPolicy(
            roles=child_roles,
            scopes=child_scopes,
            require_auth=True
        )
        
        # Merge policies
        merged_policy = ConstraintMerger.merge_access_policies(
            parent_policy,
            child_policy
        )
        
        # Verify merged roles is the union of parent and child roles
        expected_roles = set(parent_roles) | set(child_roles)
        actual_roles = set(merged_policy.roles)
        
        if expected_roles != actual_roles:
            errmsg = (
                f"Iteration {iteration}: Merged roles should be union of parent and child. "
                f"expected={expected_roles}, actual={actual_roles}"
            )
            raise AssertionError(errmsg)
        
        # Verify merged scopes is the union of parent and child scopes
        expected_scopes = set(parent_scopes) | set(child_scopes)
        actual_scopes = set(merged_policy.scopes)
        
        if expected_scopes != actual_scopes:
            errmsg = (
                f"Iteration {iteration}: Merged scopes should be union of parent and child. "
                f"expected={expected_scopes}, actual={actual_scopes}"
            )
            raise AssertionError(errmsg)
    
    return


def test_property_7_security_policy_composition_with_overlap():
    """
        Property 7: Security Policy Composition (with overlap)
        
        *For any* parent and child policies with overlapping roles/scopes,
        the merged policy SHALL contain each role/scope exactly once.
        
        This test verifies that duplicate roles/scopes are deduplicated
        in the merged policy.
        
        **Feature: blueprint-endpoints, Property 7: Security Policy Composition**
        **Validates: Requirements 2.8**
    """
    # Run 100 iterations with different random configurations
    for iteration in range(100):
        # Generate some shared roles/scopes
        shared_roles = [f"shared_role_{_generate_random_string(3, 5)}"]
        shared_scopes = [f"shared_scope_{_generate_random_string(3, 5)}"]
        
        # Generate unique roles/scopes for parent and child
        parent_unique_roles = [f"parent_role_{_generate_random_string(3, 5)}"]
        child_unique_roles = [f"child_role_{_generate_random_string(3, 5)}"]
        
        parent_unique_scopes = [f"parent_scope_{_generate_random_string(3, 5)}"]
        child_unique_scopes = [f"child_scope_{_generate_random_string(3, 5)}"]
        
        # Create policies with overlapping roles/scopes
        parent_policy = AccessPolicy(
            roles=shared_roles + parent_unique_roles,
            scopes=shared_scopes + parent_unique_scopes,
            require_auth=True
        )
        
        child_policy = AccessPolicy(
            roles=shared_roles + child_unique_roles,
            scopes=shared_scopes + child_unique_scopes,
            require_auth=True
        )
        
        # Merge policies
        merged_policy = ConstraintMerger.merge_access_policies(
            parent_policy,
            child_policy
        )
        
        # Verify shared roles appear exactly once
        for role in shared_roles:
            count = merged_policy.roles.count(role)
            if count != 1:
                errmsg = (
                    f"Iteration {iteration}: Shared role '{role}' should appear exactly once. "
                    f"Found {count} times in {merged_policy.roles}"
                )
                raise AssertionError(errmsg)
        
        # Verify shared scopes appear exactly once
        for scope in shared_scopes:
            count = merged_policy.scopes.count(scope)
            if count != 1:
                errmsg = (
                    f"Iteration {iteration}: Shared scope '{scope}' should appear exactly once. "
                    f"Found {count} times in {merged_policy.scopes}"
                )
                raise AssertionError(errmsg)
        
        # Verify all unique roles are present
        for role in parent_unique_roles + child_unique_roles:
            if role not in merged_policy.roles:
                errmsg = (
                    f"Iteration {iteration}: Unique role '{role}' should be in merged policy. "
                    f"merged_roles={merged_policy.roles}"
                )
                raise AssertionError(errmsg)
        
        # Verify all unique scopes are present
        for scope in parent_unique_scopes + child_unique_scopes:
            if scope not in merged_policy.scopes:
                errmsg = (
                    f"Iteration {iteration}: Unique scope '{scope}' should be in merged policy. "
                    f"merged_scopes={merged_policy.scopes}"
                )
                raise AssertionError(errmsg)
    
    return


# =============================================================================
# Property 8: Rate Limit Stacking
# Feature: blueprint-endpoints, Property 8: Rate Limit Stacking
# Validates: Requirements 2.9
# =============================================================================

def _generate_random_rate_limit() -> RateLimit:
    """Generate a random RateLimit with valid positive values."""
    requests = random.randint(1, 1000)
    window = random.randint(1, 3600)  # 1 second to 1 hour
    return RateLimit(requests=requests, window=window)


def _calculate_requests_per_second(limit: RateLimit) -> float:
    """Calculate the requests per second ratio for a rate limit."""
    if limit.window == 0:
        return float('inf')
    return limit.requests / limit.window


def test_property_8_rate_limit_stacking_most_restrictive():
    """
        Property 8: Rate Limit Stacking
        
        *For any* endpoint with parent and child rate limits, the most
        restrictive rate limit SHALL apply.
        
        The most restrictive limit is determined by the lowest
        requests-per-second ratio.
        
        This test generates random parent and child rate limits and verifies
        that the merged result is always the most restrictive one.
        
        **Feature: blueprint-endpoints, Property 8: Rate Limit Stacking**
        **Validates: Requirements 2.9**
    """
    # Run 100 iterations with different random configurations
    for iteration in range(100):
        # Generate random parent and child rate limits
        parent_limit = _generate_random_rate_limit()
        child_limit = _generate_random_rate_limit()
        
        # Calculate requests per second for each
        parent_rps = _calculate_requests_per_second(parent_limit)
        child_rps = _calculate_requests_per_second(child_limit)
        
        # Merge rate limits
        merged_limit = ConstraintMerger.merge_rate_limits(parent_limit, child_limit)
        
        # Determine which should be the most restrictive (lower rps = more restrictive)
        if parent_rps <= child_rps:
            expected_limit = parent_limit
        else:
            expected_limit = child_limit
        
        # Verify the merged limit is the most restrictive
        if merged_limit is not expected_limit:
            errmsg = (
                f"Iteration {iteration}: Merged limit should be the most restrictive. "
                f"parent={parent_limit} ({parent_rps:.4f} req/s), "
                f"child={child_limit} ({child_rps:.4f} req/s), "
                f"expected={expected_limit}, got={merged_limit}"
            )
            raise AssertionError(errmsg)
    
    return


def test_property_8_rate_limit_stacking_child_none_inherits_parent():
    """
        Property 8: Rate Limit Stacking (child None inherits parent)
        
        *For any* parent rate limit, when child is None, the parent
        rate limit SHALL be inherited.
        
        This test generates random parent rate limits and verifies that
        when child is None, the parent limit is returned unchanged.
        
        **Feature: blueprint-endpoints, Property 8: Rate Limit Stacking**
        **Validates: Requirements 2.9**
    """
    # Run 100 iterations with different random configurations
    for iteration in range(100):
        # Generate random parent rate limit
        parent_limit = _generate_random_rate_limit()
        
        # Merge with None child
        merged_limit = ConstraintMerger.merge_rate_limits(parent_limit, None)
        
        # Verify parent is inherited
        if merged_limit is not parent_limit:
            errmsg = (
                f"Iteration {iteration}: When child is None, parent should be inherited. "
                f"parent={parent_limit}, got={merged_limit}"
            )
            raise AssertionError(errmsg)
    
    return


def test_property_8_rate_limit_stacking_parent_none_uses_child():
    """
        Property 8: Rate Limit Stacking (parent None uses child)
        
        *For any* child rate limit, when parent is None, the child
        rate limit SHALL be used.
        
        This test generates random child rate limits and verifies that
        when parent is None, the child limit is returned unchanged.
        
        **Feature: blueprint-endpoints, Property 8: Rate Limit Stacking**
        **Validates: Requirements 2.9**
    """
    # Run 100 iterations with different random configurations
    for iteration in range(100):
        # Generate random child rate limit
        child_limit = _generate_random_rate_limit()
        
        # Merge with None parent
        merged_limit = ConstraintMerger.merge_rate_limits(None, child_limit)
        
        # Verify child is used
        if merged_limit is not child_limit:
            errmsg = (
                f"Iteration {iteration}: When parent is None, child should be used. "
                f"child={child_limit}, got={merged_limit}"
            )
            raise AssertionError(errmsg)
    
    return


def test_property_8_rate_limit_stacking_both_none():
    """
        Property 8: Rate Limit Stacking (both None)
        
        *For any* merge operation where both parent and child are None,
        the result SHALL be None.
        
        **Feature: blueprint-endpoints, Property 8: Rate Limit Stacking**
        **Validates: Requirements 2.9**
    """
    # Run 100 iterations (though result is deterministic, for consistency)
    for iteration in range(100):
        # Merge None with None
        merged_limit = ConstraintMerger.merge_rate_limits(None, None)
        
        # Verify result is None
        if merged_limit is not None:
            errmsg = (
                f"Iteration {iteration}: When both are None, result should be None. "
                f"got={merged_limit}"
            )
            raise AssertionError(errmsg)
    
    return


def test_property_8_rate_limit_stacking_restrictiveness_ordering():
    """
        Property 8: Rate Limit Stacking (restrictiveness ordering)
        
        *For any* two rate limits A and B where A is more restrictive than B,
        merging A and B (in any order) SHALL always return A.
        
        This test verifies that the merge operation is commutative with
        respect to restrictiveness - the most restrictive limit always wins
        regardless of which is parent vs child.
        
        **Feature: blueprint-endpoints, Property 8: Rate Limit Stacking**
        **Validates: Requirements 2.9**
    """
    # Run 100 iterations with different random configurations
    for iteration in range(100):
        # Generate two rate limits with different restrictiveness
        limit_a = _generate_random_rate_limit()
        limit_b = _generate_random_rate_limit()
        
        rps_a = _calculate_requests_per_second(limit_a)
        rps_b = _calculate_requests_per_second(limit_b)
        
        # Determine which is more restrictive
        if rps_a <= rps_b:
            more_restrictive = limit_a
        else:
            more_restrictive = limit_b
        
        # Merge in both orders
        merged_ab = ConstraintMerger.merge_rate_limits(limit_a, limit_b)
        merged_ba = ConstraintMerger.merge_rate_limits(limit_b, limit_a)
        
        # Verify both merges return the more restrictive limit
        if merged_ab is not more_restrictive:
            errmsg = (
                f"Iteration {iteration}: merge(A, B) should return more restrictive. "
                f"A={limit_a} ({rps_a:.4f} req/s), B={limit_b} ({rps_b:.4f} req/s), "
                f"expected={more_restrictive}, got={merged_ab}"
            )
            raise AssertionError(errmsg)
        
        if merged_ba is not more_restrictive:
            errmsg = (
                f"Iteration {iteration}: merge(B, A) should return more restrictive. "
                f"A={limit_a} ({rps_a:.4f} req/s), B={limit_b} ({rps_b:.4f} req/s), "
                f"expected={more_restrictive}, got={merged_ba}"
            )
            raise AssertionError(errmsg)
    
    return


def test_property_8_rate_limit_stacking_same_window_lower_requests_wins():
    """
        Property 8: Rate Limit Stacking (same window, lower requests wins)
        
        *For any* two rate limits with the same window, the one with
        fewer requests SHALL be more restrictive and win.
        
        **Feature: blueprint-endpoints, Property 8: Rate Limit Stacking**
        **Validates: Requirements 2.9**
    """
    # Run 100 iterations with different random configurations
    for iteration in range(100):
        # Generate a common window
        window = random.randint(1, 3600)
        
        # Generate two different request counts
        requests_a = random.randint(1, 500)
        requests_b = random.randint(501, 1000)  # Ensure B > A
        
        limit_a = RateLimit(requests=requests_a, window=window)
        limit_b = RateLimit(requests=requests_b, window=window)
        
        # Merge rate limits
        merged_limit = ConstraintMerger.merge_rate_limits(limit_a, limit_b)
        
        # Verify the one with fewer requests wins
        if merged_limit is not limit_a:
            errmsg = (
                f"Iteration {iteration}: With same window, lower requests should win. "
                f"A={limit_a}, B={limit_b}, got={merged_limit}"
            )
            raise AssertionError(errmsg)
    
    return


def test_property_8_rate_limit_stacking_same_requests_longer_window_wins():
    """
        Property 8: Rate Limit Stacking (same requests, longer window wins)
        
        *For any* two rate limits with the same request count, the one with
        the longer window SHALL be more restrictive and win.
        
        **Feature: blueprint-endpoints, Property 8: Rate Limit Stacking**
        **Validates: Requirements 2.9**
    """
    # Run 100 iterations with different random configurations
    for iteration in range(100):
        # Generate a common request count
        requests = random.randint(1, 1000)
        
        # Generate two different windows
        window_a = random.randint(1801, 3600)  # Ensure A > B (longer = more restrictive)
        window_b = random.randint(1, 1800)
        
        limit_a = RateLimit(requests=requests, window=window_a)
        limit_b = RateLimit(requests=requests, window=window_b)
        
        # Merge rate limits
        merged_limit = ConstraintMerger.merge_rate_limits(limit_a, limit_b)
        
        # Verify the one with longer window wins (lower req/s)
        if merged_limit is not limit_a:
            errmsg = (
                f"Iteration {iteration}: With same requests, longer window should win. "
                f"A={limit_a} ({requests/window_a:.4f} req/s), "
                f"B={limit_b} ({requests/window_b:.4f} req/s), got={merged_limit}"
            )
            raise AssertionError(errmsg)
    
    return


# =============================================================================
# Property 6: List Field Merge Behavior
# =============================================================================


def _generate_random_tags() -> list:
    """Generate a random list of tags."""
    num_tags = random.randint(1, 5)
    return [f"tag_{_generate_random_string(3, 8)}" for _ in range(num_tags)]


def test_property_6_list_field_merge_tags_default_child_wins():
    """
        Property 6: List Field Merge Behavior (default - child wins)
        
        *For any* parent and child tag lists, when neither merge nor replace
        is set, the child tags SHALL win if the child list is non-empty,
        otherwise the parent tags SHALL be inherited.
        
        **Feature: blueprint-endpoints, Property 6: List Field Merge Behavior**
        **Validates: Requirements 2.1, 2.2**
    """
    for iteration in range(100):
        parent_tags = _generate_random_tags()
        child_tags = _generate_random_tags()

        merged = ConstraintMerger.merge_tags(parent_tags, child_tags)

        # Child tags should win when child is non-empty
        if merged != list(child_tags):
            errmsg = (
                f"Iteration {iteration}: Default merge should return child tags when child is non-empty. "
                f"parent={parent_tags}, child={child_tags}, merged={merged}"
            )
            raise AssertionError(errmsg)

    return


def test_property_6_list_field_merge_tags_default_inherits_parent():
    """
        Property 6: List Field Merge Behavior (default - inherit parent)
        
        *For any* parent tag list and an empty child tag list, when neither
        merge nor replace is set, the parent tags SHALL be inherited.
        
        **Feature: blueprint-endpoints, Property 6: List Field Merge Behavior**
        **Validates: Requirements 2.1, 2.2**
    """
    for iteration in range(100):
        parent_tags = _generate_random_tags()
        child_tags = []

        merged = ConstraintMerger.merge_tags(parent_tags, child_tags)

        if merged != list(parent_tags):
            errmsg = (
                f"Iteration {iteration}: Default merge should inherit parent when child is empty. "
                f"parent={parent_tags}, child={child_tags}, merged={merged}"
            )
            raise AssertionError(errmsg)

    return


def test_property_6_list_field_merge_tags_merge_mode():
    """
        Property 6: List Field Merge Behavior (merge_tags=True)
        
        *For any* parent and child tag lists, when merge=True, the parent
        tags SHALL be appended to the child tags, and the result SHALL
        contain all tags from both lists without duplicates.
        
        **Feature: blueprint-endpoints, Property 6: List Field Merge Behavior**
        **Validates: Requirements 2.1, 2.2**
    """
    for iteration in range(100):
        parent_tags = _generate_random_tags()
        child_tags = _generate_random_tags()

        merged = ConstraintMerger.merge_tags(parent_tags, child_tags, merge=True)

        # All child tags must be present
        for tag in child_tags:
            if tag not in merged:
                errmsg = (
                    f"Iteration {iteration}: Child tag '{tag}' should be in merged result. "
                    f"parent={parent_tags}, child={child_tags}, merged={merged}"
                )
                raise AssertionError(errmsg)

        # All parent tags must be present
        for tag in parent_tags:
            if tag not in merged:
                errmsg = (
                    f"Iteration {iteration}: Parent tag '{tag}' should be in merged result. "
                    f"parent={parent_tags}, child={child_tags}, merged={merged}"
                )
                raise AssertionError(errmsg)

        # No duplicates in merged result
        if len(merged) != len(set(merged)):
            errmsg = (
                f"Iteration {iteration}: Merged tags should not contain duplicates. "
                f"merged={merged}"
            )
            raise AssertionError(errmsg)

    return


def test_property_6_list_field_merge_tags_merge_child_order_first():
    """
        Property 6: List Field Merge Behavior (merge preserves child-first order)
        
        *For any* parent and child tag lists, when merge=True, the child
        tags SHALL appear before parent tags in the merged result.
        
        **Feature: blueprint-endpoints, Property 6: List Field Merge Behavior**
        **Validates: Requirements 2.1, 2.2**
    """
    for iteration in range(100):
        # Use prefixed tags to guarantee uniqueness between parent and child
        parent_tags = [f"parent_{i}_{_generate_random_string(3, 5)}" for i in range(random.randint(1, 4))]
        child_tags = [f"child_{i}_{_generate_random_string(3, 5)}" for i in range(random.randint(1, 4))]

        merged = ConstraintMerger.merge_tags(parent_tags, child_tags, merge=True)

        # Child tags should appear first in the merged list
        for i, tag in enumerate(child_tags):
            if merged[i] != tag:
                errmsg = (
                    f"Iteration {iteration}: Child tags should appear first in merged result. "
                    f"Expected child tag '{tag}' at index {i}, got '{merged[i]}'. "
                    f"parent={parent_tags}, child={child_tags}, merged={merged}"
                )
                raise AssertionError(errmsg)

    return


def test_property_6_list_field_merge_tags_replace_mode():
    """
        Property 6: List Field Merge Behavior (replace=True)
        
        *For any* parent and child tag lists, when replace=True, the child
        tags SHALL fully replace the parent tags regardless of content.
        
        **Feature: blueprint-endpoints, Property 6: List Field Merge Behavior**
        **Validates: Requirements 2.1, 2.2**
    """
    for iteration in range(100):
        parent_tags = _generate_random_tags()
        child_tags = _generate_random_tags()

        merged = ConstraintMerger.merge_tags(parent_tags, child_tags, replace=True)

        if merged != list(child_tags):
            errmsg = (
                f"Iteration {iteration}: Replace mode should return child tags exactly. "
                f"parent={parent_tags}, child={child_tags}, merged={merged}"
            )
            raise AssertionError(errmsg)

    return


def test_property_6_list_field_merge_tags_replace_empty_child():
    """
        Property 6: List Field Merge Behavior (replace with empty child)
        
        *For any* parent tag list, when replace=True and child is empty,
        the result SHALL be an empty list (child fully replaces parent).
        
        **Feature: blueprint-endpoints, Property 6: List Field Merge Behavior**
        **Validates: Requirements 2.1, 2.2**
    """
    for iteration in range(100):
        parent_tags = _generate_random_tags()
        child_tags = []

        merged = ConstraintMerger.merge_tags(parent_tags, child_tags, replace=True)

        if merged != []:
            errmsg = (
                f"Iteration {iteration}: Replace mode with empty child should return empty list. "
                f"parent={parent_tags}, merged={merged}"
            )
            raise AssertionError(errmsg)

    return


def test_property_6_list_field_merge_roles_union_by_default():
    """
        Property 6: List Field Merge Behavior (roles union by default)
        
        *For any* parent and child access policies, the default behavior
        for roles SHALL be union (parent union child), meaning all roles
        from both policies appear in the merged result.
        
        **Feature: blueprint-endpoints, Property 6: List Field Merge Behavior**
        **Validates: Requirements 2.6, 2.7**
    """
    for iteration in range(100):
        parent_roles = _generate_random_roles()
        child_roles = _generate_random_roles()

        parent_policy = AccessPolicy(roles=parent_roles, scopes=[])
        child_policy = AccessPolicy(roles=child_roles, scopes=[])

        merged_policy = ConstraintMerger.merge_access_policies(parent_policy, child_policy)

        expected_roles = set(parent_roles) | set(child_roles)
        actual_roles = set(merged_policy.roles)

        if expected_roles != actual_roles:
            errmsg = (
                f"Iteration {iteration}: Default role merge should be union. "
                f"parent_roles={parent_roles}, child_roles={child_roles}, "
                f"expected={expected_roles}, actual={actual_roles}"
            )
            raise AssertionError(errmsg)

    return


def test_property_6_list_field_merge_roles_replace():
    """
        Property 6: List Field Merge Behavior (replace_roles=True)
        
        *For any* parent and child access policies, when replace_roles=True,
        the child roles SHALL fully replace the parent roles.
        
        **Feature: blueprint-endpoints, Property 6: List Field Merge Behavior**
        **Validates: Requirements 2.6, 2.7**
    """
    for iteration in range(100):
        parent_roles = _generate_random_roles()
        child_roles = _generate_random_roles()

        parent_policy = AccessPolicy(roles=parent_roles, scopes=[])
        child_policy = AccessPolicy(roles=child_roles, scopes=[])

        merged_policy = ConstraintMerger.merge_access_policies(
            parent_policy, child_policy, replace_roles=True
        )

        if set(merged_policy.roles) != set(child_roles):
            errmsg = (
                f"Iteration {iteration}: replace_roles=True should use child roles only. "
                f"parent_roles={parent_roles}, child_roles={child_roles}, "
                f"merged_roles={merged_policy.roles}"
            )
            raise AssertionError(errmsg)

        # Parent-only roles should NOT be present
        parent_only = set(parent_roles) - set(child_roles)
        for role in parent_only:
            if role in merged_policy.roles:
                errmsg = (
                    f"Iteration {iteration}: Parent-only role '{role}' should not be in merged "
                    f"when replace_roles=True. merged_roles={merged_policy.roles}"
                )
                raise AssertionError(errmsg)

    return


def test_property_6_list_field_merge_scopes_union_by_default():
    """
        Property 6: List Field Merge Behavior (scopes union by default)
        
        *For any* parent and child access policies, the default behavior
        for scopes SHALL be union (parent union child), meaning all scopes
        from both policies appear in the merged result.
        
        **Feature: blueprint-endpoints, Property 6: List Field Merge Behavior**
        **Validates: Requirements 2.6, 2.7**
    """
    for iteration in range(100):
        parent_scopes = _generate_random_scopes()
        child_scopes = _generate_random_scopes()

        parent_policy = AccessPolicy(roles=[], scopes=parent_scopes)
        child_policy = AccessPolicy(roles=[], scopes=child_scopes)

        merged_policy = ConstraintMerger.merge_access_policies(parent_policy, child_policy)

        expected_scopes = set(parent_scopes) | set(child_scopes)
        actual_scopes = set(merged_policy.scopes)

        if expected_scopes != actual_scopes:
            errmsg = (
                f"Iteration {iteration}: Default scope merge should be union. "
                f"parent_scopes={parent_scopes}, child_scopes={child_scopes}, "
                f"expected={expected_scopes}, actual={actual_scopes}"
            )
            raise AssertionError(errmsg)

    return


def test_property_6_list_field_merge_scopes_replace():
    """
        Property 6: List Field Merge Behavior (replace_scopes=True)
        
        *For any* parent and child access policies, when replace_scopes=True,
        the child scopes SHALL fully replace the parent scopes.
        
        **Feature: blueprint-endpoints, Property 6: List Field Merge Behavior**
        **Validates: Requirements 2.6, 2.7**
    """
    for iteration in range(100):
        parent_scopes = _generate_random_scopes()
        child_scopes = _generate_random_scopes()

        parent_policy = AccessPolicy(roles=[], scopes=parent_scopes)
        child_policy = AccessPolicy(roles=[], scopes=child_scopes)

        merged_policy = ConstraintMerger.merge_access_policies(
            parent_policy, child_policy, replace_scopes=True
        )

        if set(merged_policy.scopes) != set(child_scopes):
            errmsg = (
                f"Iteration {iteration}: replace_scopes=True should use child scopes only. "
                f"parent_scopes={parent_scopes}, child_scopes={child_scopes}, "
                f"merged_scopes={merged_policy.scopes}"
            )
            raise AssertionError(errmsg)

        # Parent-only scopes should NOT be present
        parent_only = set(parent_scopes) - set(child_scopes)
        for scope in parent_only:
            if scope in merged_policy.scopes:
                errmsg = (
                    f"Iteration {iteration}: Parent-only scope '{scope}' should not be in merged "
                    f"when replace_scopes=True. merged_scopes={merged_policy.scopes}"
                )
                raise AssertionError(errmsg)

    return


def test_property_6_list_field_merge_returns_copies():
    """
        Property 6: List Field Merge Behavior (returns copies)
        
        *For any* merge operation on list fields, the returned list SHALL
        be a new copy, not a reference to the original parent or child list.
        Mutating the result SHALL NOT affect the original lists.
        
        **Feature: blueprint-endpoints, Property 6: List Field Merge Behavior**
        **Validates: Requirements 2.1, 2.2, 2.6, 2.7**
    """
    for iteration in range(100):
        parent_tags = _generate_random_tags()
        child_tags = _generate_random_tags()

        parent_copy = list(parent_tags)
        child_copy = list(child_tags)

        # Test default mode
        merged_default = ConstraintMerger.merge_tags(parent_tags, child_tags)
        if merged_default is child_tags or merged_default is parent_tags:
            errmsg = (
                f"Iteration {iteration}: Default merge should return a new list, "
                f"not a reference to parent or child."
            )
            raise AssertionError(errmsg)

        # Test merge mode
        merged_merge = ConstraintMerger.merge_tags(parent_tags, child_tags, merge=True)
        if merged_merge is child_tags or merged_merge is parent_tags:
            errmsg = (
                f"Iteration {iteration}: Merge mode should return a new list, "
                f"not a reference to parent or child."
            )
            raise AssertionError(errmsg)

        # Test replace mode
        merged_replace = ConstraintMerger.merge_tags(parent_tags, child_tags, replace=True)
        if merged_replace is child_tags or merged_replace is parent_tags:
            errmsg = (
                f"Iteration {iteration}: Replace mode should return a new list, "
                f"not a reference to parent or child."
            )
            raise AssertionError(errmsg)

        # Verify originals are unchanged
        if parent_tags != parent_copy:
            errmsg = (
                f"Iteration {iteration}: Parent tags should not be mutated. "
                f"original={parent_copy}, current={parent_tags}"
            )
            raise AssertionError(errmsg)

        if child_tags != child_copy:
            errmsg = (
                f"Iteration {iteration}: Child tags should not be mutated. "
                f"original={child_copy}, current={child_tags}"
            )
            raise AssertionError(errmsg)

    return
