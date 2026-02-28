"""
    Tests for the EndpointConstraints dataclass.
    
    This module contains unit tests for the endpoint constraints dataclass.
"""

from automojo.webworks.endpoints.constraints import EndpointConstraints
from automojo.webworks.endpoints.accesspolicy import AccessPolicy
from automojo.webworks.endpoints.ratelimit import RateLimit


# =============================================================================
# Unit Tests for EndpointConstraints - Basic Construction
# =============================================================================

def test_endpoint_constraints_default_values():
    """
        Test that EndpointConstraints has correct default values.
    """
    constraints = EndpointConstraints()
    
    if constraints.access_policy is not None:
        errmsg = f"Expected access_policy to be None, got {constraints.access_policy}"
        raise AssertionError(errmsg)
    
    if constraints.rate_limit is not None:
        errmsg = f"Expected rate_limit to be None, got {constraints.rate_limit}"
        raise AssertionError(errmsg)
    
    if constraints.scopes != []:
        errmsg = f"Expected empty scopes list, got {constraints.scopes}"
        raise AssertionError(errmsg)
    
    if constraints.roles != []:
        errmsg = f"Expected empty roles list, got {constraints.roles}"
        raise AssertionError(errmsg)
    
    return


def test_endpoint_constraints_with_values():
    """
        Test that EndpointConstraints can be created with values.
    """
    policy = AccessPolicy(roles=["admin"], scopes=["read"])
    limit = RateLimit(requests=100, window=60)
    
    constraints = EndpointConstraints(
        access_policy=policy,
        rate_limit=limit,
        scopes=["api:read", "api:write"],
        roles=["user", "admin"]
    )
    
    if constraints.access_policy is not policy:
        errmsg = f"Expected access_policy to be {policy}, got {constraints.access_policy}"
        raise AssertionError(errmsg)
    
    if constraints.rate_limit is not limit:
        errmsg = f"Expected rate_limit to be {limit}, got {constraints.rate_limit}"
        raise AssertionError(errmsg)
    
    if constraints.scopes != ["api:read", "api:write"]:
        errmsg = f"Expected scopes ['api:read', 'api:write'], got {constraints.scopes}"
        raise AssertionError(errmsg)
    
    if constraints.roles != ["user", "admin"]:
        errmsg = f"Expected roles ['user', 'admin'], got {constraints.roles}"
        raise AssertionError(errmsg)
    
    return


def test_endpoint_constraints_is_dataclass():
    """
        Test that EndpointConstraints is a proper dataclass with equality.
    """
    policy = AccessPolicy(roles=["admin"])
    limit = RateLimit(requests=100, window=60)
    
    constraints1 = EndpointConstraints(
        access_policy=policy,
        rate_limit=limit,
        scopes=["read"],
        roles=["admin"]
    )
    constraints2 = EndpointConstraints(
        access_policy=policy,
        rate_limit=limit,
        scopes=["read"],
        roles=["admin"]
    )
    
    if constraints1 != constraints2:
        errmsg = "Expected equal EndpointConstraints instances to be equal"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for EndpointConstraints - merge method
# =============================================================================

def test_merge_with_empty_parent():
    """
        Test merging when parent has no constraints.
    """
    parent = EndpointConstraints()
    child = EndpointConstraints(
        access_policy=AccessPolicy(roles=["admin"]),
        rate_limit=RateLimit(requests=50, window=60),
        scopes=["read"],
        roles=["admin"]
    )
    
    merged = EndpointConstraints.merge(parent, child)
    
    if merged.access_policy.roles != ["admin"]:
        errmsg = f"Expected access_policy.roles ['admin'], got {merged.access_policy.roles}"
        raise AssertionError(errmsg)
    
    if merged.rate_limit.requests != 50:
        errmsg = f"Expected rate_limit.requests 50, got {merged.rate_limit.requests}"
        raise AssertionError(errmsg)
    
    if merged.scopes != ["read"]:
        errmsg = f"Expected scopes ['read'], got {merged.scopes}"
        raise AssertionError(errmsg)
    
    if merged.roles != ["admin"]:
        errmsg = f"Expected roles ['admin'], got {merged.roles}"
        raise AssertionError(errmsg)
    
    return


def test_merge_with_empty_child():
    """
        Test merging when child has no constraints (inherits from parent).
    """
    parent = EndpointConstraints(
        access_policy=AccessPolicy(roles=["user"]),
        rate_limit=RateLimit(requests=100, window=60),
        scopes=["api"],
        roles=["user"]
    )
    child = EndpointConstraints()
    
    merged = EndpointConstraints.merge(parent, child)
    
    if merged.access_policy.roles != ["user"]:
        errmsg = f"Expected access_policy.roles ['user'], got {merged.access_policy.roles}"
        raise AssertionError(errmsg)
    
    if merged.rate_limit.requests != 100:
        errmsg = f"Expected rate_limit.requests 100, got {merged.rate_limit.requests}"
        raise AssertionError(errmsg)
    
    if merged.scopes != ["api"]:
        errmsg = f"Expected scopes ['api'], got {merged.scopes}"
        raise AssertionError(errmsg)
    
    if merged.roles != ["user"]:
        errmsg = f"Expected roles ['user'], got {merged.roles}"
        raise AssertionError(errmsg)
    
    return


def test_merge_scopes_union():
    """
        Test that scopes are merged as union by default.
    """
    parent = EndpointConstraints(scopes=["read", "write"])
    child = EndpointConstraints(scopes=["write", "delete"])
    
    merged = EndpointConstraints.merge(parent, child)
    
    # Union: read, write, delete (preserving order, no duplicates)
    expected = ["read", "write", "delete"]
    if merged.scopes != expected:
        errmsg = f"Expected scopes {expected}, got {merged.scopes}"
        raise AssertionError(errmsg)
    
    return


def test_merge_scopes_replace():
    """
        Test that scopes can be replaced when replace_scopes=True.
    """
    parent = EndpointConstraints(scopes=["read", "write"])
    child = EndpointConstraints(scopes=["admin"])
    
    merged = EndpointConstraints.merge(parent, child, replace_scopes=True)
    
    if merged.scopes != ["admin"]:
        errmsg = f"Expected scopes ['admin'], got {merged.scopes}"
        raise AssertionError(errmsg)
    
    return


def test_merge_roles_union():
    """
        Test that roles are merged as union by default.
    """
    parent = EndpointConstraints(roles=["user", "editor"])
    child = EndpointConstraints(roles=["editor", "admin"])
    
    merged = EndpointConstraints.merge(parent, child)
    
    # Union: user, editor, admin (preserving order, no duplicates)
    expected = ["user", "editor", "admin"]
    if merged.roles != expected:
        errmsg = f"Expected roles {expected}, got {merged.roles}"
        raise AssertionError(errmsg)
    
    return


def test_merge_roles_replace():
    """
        Test that roles can be replaced when replace_roles=True.
    """
    parent = EndpointConstraints(roles=["user", "editor"])
    child = EndpointConstraints(roles=["admin"])
    
    merged = EndpointConstraints.merge(parent, child, replace_roles=True)
    
    if merged.roles != ["admin"]:
        errmsg = f"Expected roles ['admin'], got {merged.roles}"
        raise AssertionError(errmsg)
    
    return


def test_merge_rate_limits_most_restrictive():
    """
        Test that the most restrictive rate limit is used.
    """
    parent = EndpointConstraints(rate_limit=RateLimit(requests=100, window=60))
    child = EndpointConstraints(rate_limit=RateLimit(requests=50, window=60))
    
    merged = EndpointConstraints.merge(parent, child)
    
    # Child is more restrictive (50/60 < 100/60)
    if merged.rate_limit.requests != 50:
        errmsg = f"Expected rate_limit.requests 50, got {merged.rate_limit.requests}"
        raise AssertionError(errmsg)
    
    if merged.rate_limit.window != 60:
        errmsg = f"Expected rate_limit.window 60, got {merged.rate_limit.window}"
        raise AssertionError(errmsg)
    
    return


def test_merge_rate_limits_parent_more_restrictive():
    """
        Test that parent rate limit is used when more restrictive.
    """
    parent = EndpointConstraints(rate_limit=RateLimit(requests=10, window=60))
    child = EndpointConstraints(rate_limit=RateLimit(requests=100, window=60))
    
    merged = EndpointConstraints.merge(parent, child)
    
    # Parent is more restrictive (10/60 < 100/60)
    if merged.rate_limit.requests != 10:
        errmsg = f"Expected rate_limit.requests 10, got {merged.rate_limit.requests}"
        raise AssertionError(errmsg)
    
    return


def test_merge_access_policies():
    """
        Test that access policies are merged correctly.
    """
    parent = EndpointConstraints(
        access_policy=AccessPolicy(roles=["user"], scopes=["read"])
    )
    child = EndpointConstraints(
        access_policy=AccessPolicy(roles=["admin"], scopes=["write"])
    )
    
    merged = EndpointConstraints.merge(parent, child)
    
    # Roles and scopes should be unioned
    if set(merged.access_policy.roles) != {"user", "admin"}:
        errmsg = f"Expected roles {{'user', 'admin'}}, got {set(merged.access_policy.roles)}"
        raise AssertionError(errmsg)
    
    if set(merged.access_policy.scopes) != {"read", "write"}:
        errmsg = f"Expected scopes {{'read', 'write'}}, got {set(merged.access_policy.scopes)}"
        raise AssertionError(errmsg)
    
    return


def test_merge_returns_new_instance():
    """
        Test that merge returns a new EndpointConstraints instance.
    """
    parent = EndpointConstraints(roles=["admin"])
    child = EndpointConstraints(roles=["user"])
    
    merged = EndpointConstraints.merge(parent, child)
    
    if merged is parent:
        errmsg = "Expected new instance, got same as parent"
        raise AssertionError(errmsg)
    
    if merged is child:
        errmsg = "Expected new instance, got same as child"
        raise AssertionError(errmsg)
    
    return


def test_merge_both_empty():
    """
        Test merging when both parent and child are empty.
    """
    parent = EndpointConstraints()
    child = EndpointConstraints()
    
    merged = EndpointConstraints.merge(parent, child)
    
    if merged.access_policy is not None:
        errmsg = f"Expected access_policy to be None, got {merged.access_policy}"
        raise AssertionError(errmsg)
    
    if merged.rate_limit is not None:
        errmsg = f"Expected rate_limit to be None, got {merged.rate_limit}"
        raise AssertionError(errmsg)
    
    if merged.scopes != []:
        errmsg = f"Expected empty scopes list, got {merged.scopes}"
        raise AssertionError(errmsg)
    
    if merged.roles != []:
        errmsg = f"Expected empty roles list, got {merged.roles}"
        raise AssertionError(errmsg)
    
    return
