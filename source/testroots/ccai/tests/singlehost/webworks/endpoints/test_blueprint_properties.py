"""
.. module:: test_blueprint_properties
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Property-based tests for Blueprint class.

.. moduleauthor:: Code Craft AI LLC

This module contains property-based tests for the Blueprint class,
validating correctness properties across many generated inputs.
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []

import random
import string
from typing import List, Optional

from ccai.webworks.endpoints import (
    AccessPolicy,
    Blueprint,
    Endpoint,
    EndpointRegistry,
    RateLimit,
)


# =============================================================================
# Helper Functions for Generating Random Test Data
# =============================================================================

def generate_random_string(min_len: int = 3, max_len: int = 15) -> str:
    """Generate a random alphanumeric string."""
    length = random.randint(min_len, max_len)
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))


def generate_random_path_segment() -> str:
    """Generate a random URL path segment (alphanumeric, no slashes)."""
    length = random.randint(2, 10)
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))


def generate_random_base_path() -> str:
    """Generate a random base path like /api/v1 or /users."""
    num_segments = random.randint(1, 3)
    segments = [generate_random_path_segment() for _ in range(num_segments)]
    return "/" + "/".join(segments)


def generate_random_leaf() -> str:
    """Generate a random leaf segment."""
    return generate_random_path_segment()


def generate_random_roles() -> List[str]:
    """Generate a random list of roles."""
    num_roles = random.randint(0, 3)
    return [generate_random_string(3, 8) for _ in range(num_roles)]


def generate_random_scopes() -> List[str]:
    """Generate a random list of scopes."""
    num_scopes = random.randint(0, 3)
    return [generate_random_string(3, 8) for _ in range(num_scopes)]


def generate_random_tags() -> List[str]:
    """Generate a random list of tags."""
    num_tags = random.randint(0, 4)
    return [generate_random_string(2, 6) for _ in range(num_tags)]


def generate_random_access_policy() -> Optional[AccessPolicy]:
    """Generate a random AccessPolicy or None."""
    if random.random() < 0.3:
        return None
    return AccessPolicy(
        roles=generate_random_roles(),
        scopes=generate_random_scopes(),
        require_auth=random.choice([True, False])
    )


def generate_random_rate_limit() -> Optional[RateLimit]:
    """Generate a random RateLimit or None."""
    if random.random() < 0.3:
        return None
    return RateLimit(
        requests=random.randint(10, 1000),
        window=random.randint(10, 3600)
    )


def _clear_registry():
    """Helper to clear the registry before tests."""
    registry = EndpointRegistry()
# =============================================================================
# Property 4: Path Composition
# Feature: blueprint-endpoints, Property 4: Path Composition
# Validates: Requirements 1.7, 4.3, 4.4
# =============================================================================

def test_property_path_composition():
    """
        Property 4: Path Composition
        
        *For any* Blueprint with `base_path` and any child endpoint with `leaf`:
        - The resulting path SHALL be the composition of base_path and leaf
        - If child provides absolute `path`, it SHALL override the composition
        
        This test generates random base_path and leaf combinations and verifies
        that the composed path follows the expected pattern.
        
        **Feature: blueprint-endpoints, Property 4: Path Composition**
        **Validates: Requirements 1.7, 4.3, 4.4**
    """
    registry = EndpointRegistry()
    
    # Run 100 iterations with different random configurations
    for iteration in range(100):
        registry = EndpointRegistry()
        
        # Generate random base_path
        base_path = generate_random_base_path()
        
        # Generate random leaf
        leaf = generate_random_leaf()
        
        # Create a Blueprint subclass with the random base_path
        class TestBlueprint(Blueprint):
            pass
        
        TestBlueprint.base_path = base_path
        
        # Test _compose_path with leaf
        composed = TestBlueprint._compose_path(leaf=leaf, path=None)
        
        # Verify the composed path is base_path + "/" + leaf
        expected = f"{base_path.rstrip('/')}/{leaf}"
        
        if composed != expected:
            errmsg = (
                f"Iteration {iteration}: Path composition failed. "
                f"base_path={base_path}, leaf={leaf}, "
                f"expected={expected}, got={composed}"
            )
            raise AssertionError(errmsg)
        
        # Verify the composed path starts with base_path
        if not composed.startswith(base_path.rstrip("/")):
            errmsg = (
                f"Iteration {iteration}: Composed path should start with base_path. "
                f"base_path={base_path}, composed={composed}"
            )
            raise AssertionError(errmsg)
        
        # Verify the composed path ends with leaf
        if not composed.endswith(leaf):
            errmsg = (
                f"Iteration {iteration}: Composed path should end with leaf. "
                f"leaf={leaf}, composed={composed}"
            )
            raise AssertionError(errmsg)
        
        # Verify no double slashes in composed path
        if "//" in composed:
            errmsg = (
                f"Iteration {iteration}: Composed path should not have double slashes. "
                f"composed={composed}"
            )
            raise AssertionError(errmsg)
    
    return


def test_property_path_composition_with_absolute_path():
    """
        Property 4: Path Composition (absolute path override)
        
        *For any* Blueprint with `base_path` and any child with absolute `path`:
        - The child's absolute path SHALL be appended to base_path
        
        **Feature: blueprint-endpoints, Property 4: Path Composition**
        **Validates: Requirements 1.7, 4.3, 4.4**
    """
    registry = EndpointRegistry()
    
    # Run 100 iterations with different random configurations
    for iteration in range(100):
        registry = EndpointRegistry()
        
        # Generate random base_path
        base_path = generate_random_base_path()
        
        # Generate random absolute path (starts with /)
        child_path = "/" + generate_random_path_segment()
        
        # Create a Blueprint subclass with the random base_path
        class TestBlueprint(Blueprint):
            pass
        
        TestBlueprint.base_path = base_path
        
        # Test _compose_path with absolute path
        composed = TestBlueprint._compose_path(leaf=None, path=child_path)
        
        # Verify the composed path is base_path + child_path
        expected = f"{base_path.rstrip('/')}{child_path}"
        
        if composed != expected:
            errmsg = (
                f"Iteration {iteration}: Absolute path composition failed. "
                f"base_path={base_path}, child_path={child_path}, "
                f"expected={expected}, got={composed}"
            )
            raise AssertionError(errmsg)
    
    return


def test_property_path_composition_with_base_leaf():
    """
        Property 4: Path Composition (base_leaf variant)
        
        *For any* Blueprint with `base_leaf` and any child with `leaf`:
        - The resulting path SHALL be /{base_leaf}/{child_leaf}
        
        **Feature: blueprint-endpoints, Property 4: Path Composition**
        **Validates: Requirements 1.7, 4.3, 4.4**
    """
    registry = EndpointRegistry()
    
    # Run 100 iterations with different random configurations
    for iteration in range(100):
        registry = EndpointRegistry()
        
        # Generate random base_leaf
        base_leaf = generate_random_leaf()
        
        # Generate random child leaf
        child_leaf = generate_random_leaf()
        
        # Create a Blueprint subclass with the random base_leaf
        class TestBlueprint(Blueprint):
            pass
        
        TestBlueprint.base_path = None
        TestBlueprint.base_leaf = base_leaf
        
        # Test _compose_path with leaf
        composed = TestBlueprint._compose_path(leaf=child_leaf, path=None)
        
        # Verify the composed path is /{base_leaf}/{child_leaf}
        expected = f"/{base_leaf}/{child_leaf}"
        
        if composed != expected:
            errmsg = (
                f"Iteration {iteration}: base_leaf composition failed. "
                f"base_leaf={base_leaf}, child_leaf={child_leaf}, "
                f"expected={expected}, got={composed}"
            )
            raise AssertionError(errmsg)
    
    return


def test_property_path_composition_no_base():
    """
        Property 4: Path Composition (no base path)
        
        *For any* Blueprint without base_path/base_leaf and any child with `leaf`:
        - The resulting path SHALL be /{leaf}
        
        **Feature: blueprint-endpoints, Property 4: Path Composition**
        **Validates: Requirements 1.7, 4.3, 4.4**
    """
    registry = EndpointRegistry()
    
    # Run 100 iterations with different random configurations
    for iteration in range(100):
        registry = EndpointRegistry()
        
        # Generate random leaf
        leaf = generate_random_leaf()
        
        # Create a Blueprint subclass with no base
        class TestBlueprint(Blueprint):
            pass
        
        TestBlueprint.base_path = None
        TestBlueprint.base_leaf = None
        
        # Test _compose_path with leaf
        composed = TestBlueprint._compose_path(leaf=leaf, path=None)
        
        # Verify the composed path is /{leaf}
        expected = f"/{leaf}"
        
        if composed != expected:
            errmsg = (
                f"Iteration {iteration}: No-base composition failed. "
                f"leaf={leaf}, expected={expected}, got={composed}"
            )
            raise AssertionError(errmsg)
    
    return



# =============================================================================
# Property 5: Security Constraint Inheritance
# Feature: blueprint-endpoints, Property 5: Security Constraint Inheritance
# Validates: Requirements 2.3, 2.4, 2.5, 6.5
# =============================================================================

def test_property_security_constraint_inheritance_child_inherits_parent():
    """
        Property 5: Security Constraint Inheritance
        
        *For any* parent-child endpoint relationship:
        - If the child does not set a security attribute, it SHALL inherit the parent's value
        
        This test generates random parent access policies and verifies that
        children without explicit policies inherit from the parent.
        
        **Feature: blueprint-endpoints, Property 5: Security Constraint Inheritance**
        **Validates: Requirements 2.3, 2.4, 2.5, 6.5**
    """
    registry = EndpointRegistry()
    
    # Run 100 iterations with different random configurations
    for iteration in range(100):
        registry = EndpointRegistry()
        
        # Generate random parent access policy
        parent_roles = generate_random_roles()
        parent_scopes = generate_random_scopes()
        parent_require_auth = random.choice([True, False])
        
        parent_policy = AccessPolicy(
            roles=parent_roles,
            scopes=parent_scopes,
            require_auth=parent_require_auth
        )
        
        # Generate random parent rate limit
        parent_rate_limit = generate_random_rate_limit()
        
        # Create a Blueprint subclass with the random constraints
        class TestBlueprint(Blueprint):
            pass
        
        TestBlueprint.base_path = generate_random_base_path()
        TestBlueprint.access_policy = parent_policy
        TestBlueprint.rate_limit = parent_rate_limit
        
        # Test _merge_constraints with no child constraints
        child_kwargs = {}
        merged = TestBlueprint._merge_constraints(child_kwargs)
        
        # Verify access_policy is inherited from parent
        if merged.get("access_policy") is None and parent_policy is not None:
            errmsg = (
                f"Iteration {iteration}: Child should inherit parent access_policy. "
                f"parent_policy={parent_policy}, merged={merged.get('access_policy')}"
            )
            raise AssertionError(errmsg)
        
        if merged.get("access_policy") is not None:
            # Verify roles are inherited
            for role in parent_roles:
                if role not in merged["access_policy"].roles:
                    errmsg = (
                        f"Iteration {iteration}: Child should inherit parent role '{role}'. "
                        f"parent_roles={parent_roles}, merged_roles={merged['access_policy'].roles}"
                    )
                    raise AssertionError(errmsg)
            
            # Verify scopes are inherited
            for scope in parent_scopes:
                if scope not in merged["access_policy"].scopes:
                    errmsg = (
                        f"Iteration {iteration}: Child should inherit parent scope '{scope}'. "
                        f"parent_scopes={parent_scopes}, merged_scopes={merged['access_policy'].scopes}"
                    )
                    raise AssertionError(errmsg)
        
        # Verify rate_limit is inherited from parent
        if parent_rate_limit is not None:
            if merged.get("rate_limit") is None:
                errmsg = (
                    f"Iteration {iteration}: Child should inherit parent rate_limit. "
                    f"parent_rate_limit={parent_rate_limit}, merged={merged.get('rate_limit')}"
                )
                raise AssertionError(errmsg)
    
    return


def test_property_security_constraint_inheritance_child_overrides_parent():
    """
        Property 5: Security Constraint Inheritance (child override)
        
        *For any* parent-child endpoint relationship:
        - If the child sets a security attribute, the child value SHALL override the parent
        
        This test generates random parent and child access policies and verifies
        that child policies properly override parent policies.
        
        **Feature: blueprint-endpoints, Property 5: Security Constraint Inheritance**
        **Validates: Requirements 2.3, 2.4, 2.5, 6.5**
    """
    registry = EndpointRegistry()
    
    # Run 100 iterations with different random configurations
    for iteration in range(100):
        registry = EndpointRegistry()
        
        # Generate random parent access policy
        parent_roles = generate_random_roles()
        parent_scopes = generate_random_scopes()
        
        parent_policy = AccessPolicy(
            roles=parent_roles,
            scopes=parent_scopes,
            require_auth=True
        )
        
        # Generate random child access policy
        child_roles = generate_random_roles()
        child_scopes = generate_random_scopes()
        
        child_policy = AccessPolicy(
            roles=child_roles,
            scopes=child_scopes,
            require_auth=False
        )
        
        # Create a Blueprint subclass with the random constraints
        class TestBlueprint(Blueprint):
            pass
        
        TestBlueprint.base_path = generate_random_base_path()
        TestBlueprint.access_policy = parent_policy
        
        # Test _merge_constraints with child access_policy
        child_kwargs = {"access_policy": child_policy}
        merged = TestBlueprint._merge_constraints(child_kwargs)
        
        # Verify merged policy contains child roles (merged with parent by default)
        merged_policy = merged.get("access_policy")
        if merged_policy is None:
            errmsg = (
                f"Iteration {iteration}: Merged policy should not be None. "
                f"parent_policy={parent_policy}, child_policy={child_policy}"
            )
            raise AssertionError(errmsg)
        
        # By default, roles are unioned (parent + child)
        for role in child_roles:
            if role not in merged_policy.roles:
                errmsg = (
                    f"Iteration {iteration}: Child role '{role}' should be in merged roles. "
                    f"child_roles={child_roles}, merged_roles={merged_policy.roles}"
                )
                raise AssertionError(errmsg)
        
        # By default, scopes are unioned (parent + child)
        for scope in child_scopes:
            if scope not in merged_policy.scopes:
                errmsg = (
                    f"Iteration {iteration}: Child scope '{scope}' should be in merged scopes. "
                    f"child_scopes={child_scopes}, merged_scopes={merged_policy.scopes}"
                )
                raise AssertionError(errmsg)
    
    return


def test_property_security_constraint_inheritance_replace_roles():
    """
        Property 5: Security Constraint Inheritance (replace_roles flag)
        
        *For any* Blueprint with replace_roles=True:
        - Child roles SHALL fully replace parent roles
        
        **Feature: blueprint-endpoints, Property 5: Security Constraint Inheritance**
        **Validates: Requirements 2.3, 2.4, 2.5, 6.5**
    """
    registry = EndpointRegistry()
    
    # Run 100 iterations with different random configurations
    for iteration in range(100):
        registry = EndpointRegistry()
        
        # Generate random parent roles (ensure non-empty for meaningful test)
        parent_roles = ["parent_role_" + generate_random_string(3, 5)]
        parent_policy = AccessPolicy(roles=parent_roles, scopes=[])
        
        # Generate random child roles (ensure non-empty and different)
        child_roles = ["child_role_" + generate_random_string(3, 5)]
        child_policy = AccessPolicy(roles=child_roles, scopes=[])
        
        # Create a Blueprint subclass with replace_roles=True
        class TestBlueprint(Blueprint):
            pass
        
        TestBlueprint.base_path = generate_random_base_path()
        TestBlueprint.access_policy = parent_policy
        TestBlueprint.replace_roles = True
        
        # Test _merge_constraints with child access_policy
        child_kwargs = {"access_policy": child_policy}
        merged = TestBlueprint._merge_constraints(child_kwargs)
        
        merged_policy = merged.get("access_policy")
        
        # Verify parent roles are NOT in merged (replaced by child)
        for role in parent_roles:
            if role in merged_policy.roles:
                errmsg = (
                    f"Iteration {iteration}: Parent role '{role}' should NOT be in merged roles "
                    f"when replace_roles=True. merged_roles={merged_policy.roles}"
                )
                raise AssertionError(errmsg)
        
        # Verify child roles ARE in merged
        for role in child_roles:
            if role not in merged_policy.roles:
                errmsg = (
                    f"Iteration {iteration}: Child role '{role}' should be in merged roles. "
                    f"merged_roles={merged_policy.roles}"
                )
                raise AssertionError(errmsg)
    
    return


def test_property_security_constraint_inheritance_replace_scopes():
    """
        Property 5: Security Constraint Inheritance (replace_scopes flag)
        
        *For any* Blueprint with replace_scopes=True:
        - Child scopes SHALL fully replace parent scopes
        
        **Feature: blueprint-endpoints, Property 5: Security Constraint Inheritance**
        **Validates: Requirements 2.3, 2.4, 2.5, 6.5**
    """
    registry = EndpointRegistry()
    
    # Run 100 iterations with different random configurations
    for iteration in range(100):
        registry = EndpointRegistry()
        
        # Generate random parent scopes (ensure non-empty for meaningful test)
        parent_scopes = ["parent_scope_" + generate_random_string(3, 5)]
        parent_policy = AccessPolicy(roles=[], scopes=parent_scopes)
        
        # Generate random child scopes (ensure non-empty and different)
        child_scopes = ["child_scope_" + generate_random_string(3, 5)]
        child_policy = AccessPolicy(roles=[], scopes=child_scopes)
        
        # Create a Blueprint subclass with replace_scopes=True
        class TestBlueprint(Blueprint):
            pass
        
        TestBlueprint.base_path = generate_random_base_path()
        TestBlueprint.access_policy = parent_policy
        TestBlueprint.replace_scopes = True
        
        # Test _merge_constraints with child access_policy
        child_kwargs = {"access_policy": child_policy}
        merged = TestBlueprint._merge_constraints(child_kwargs)
        
        merged_policy = merged.get("access_policy")
        
        # Verify parent scopes are NOT in merged (replaced by child)
        for scope in parent_scopes:
            if scope in merged_policy.scopes:
                errmsg = (
                    f"Iteration {iteration}: Parent scope '{scope}' should NOT be in merged scopes "
                    f"when replace_scopes=True. merged_scopes={merged_policy.scopes}"
                )
                raise AssertionError(errmsg)
        
        # Verify child scopes ARE in merged
        for scope in child_scopes:
            if scope not in merged_policy.scopes:
                errmsg = (
                    f"Iteration {iteration}: Child scope '{scope}' should be in merged scopes. "
                    f"merged_scopes={merged_policy.scopes}"
                )
                raise AssertionError(errmsg)
    
    return


def test_property_security_constraint_inheritance_rate_limit_most_restrictive():
    """
        Property 5: Security Constraint Inheritance (rate limit)
        
        *For any* parent-child endpoint relationship with rate limits:
        - The most restrictive rate limit SHALL apply
        
        **Feature: blueprint-endpoints, Property 5: Security Constraint Inheritance**
        **Validates: Requirements 2.3, 2.4, 2.5, 6.5**
    """
    registry = EndpointRegistry()
    
    # Run 100 iterations with different random configurations
    for iteration in range(100):
        registry = EndpointRegistry()
        
        # Generate random parent rate limit
        parent_requests = random.randint(50, 200)
        parent_window = 60
        parent_rate_limit = RateLimit(requests=parent_requests, window=parent_window)
        
        # Generate random child rate limit
        child_requests = random.randint(10, 100)
        child_window = 60
        child_rate_limit = RateLimit(requests=child_requests, window=child_window)
        
        # Create a Blueprint subclass
        class TestBlueprint(Blueprint):
            pass
        
        TestBlueprint.base_path = generate_random_base_path()
        TestBlueprint.rate_limit = parent_rate_limit
        
        # Test _merge_constraints with child rate_limit
        child_kwargs = {"rate_limit": child_rate_limit}
        merged = TestBlueprint._merge_constraints(child_kwargs)
        
        merged_rate_limit = merged.get("rate_limit")
        
        # Calculate requests per second for comparison
        parent_rps = parent_requests / parent_window
        child_rps = child_requests / child_window
        
        # The most restrictive (lower rps) should win
        expected_rps = min(parent_rps, child_rps)
        merged_rps = merged_rate_limit.requests / merged_rate_limit.window
        
        if merged_rps != expected_rps:
            errmsg = (
                f"Iteration {iteration}: Most restrictive rate limit should apply. "
                f"parent_rps={parent_rps}, child_rps={child_rps}, "
                f"expected_rps={expected_rps}, merged_rps={merged_rps}"
            )
            raise AssertionError(errmsg)
    
    return


# =============================================================================
# Property 1: Decorator Identity Preservation
# Feature: blueprint-endpoints, Property 1: Decorator Identity Preservation
# Validates: Requirements 3.1, 5.3
# =============================================================================

def test_property_decorator_identity_preservation():
    """
        Property 1: Decorator Identity Preservation
        
        *For any* handler function decorated with `attach_at`, the returned
        function SHALL be identical (same object identity) to the original
        function, ensuring decorator stacking works correctly.
        
        This test generates random handler functions and verifies that
        the decorator returns the exact same function object.
        
        **Feature: blueprint-endpoints, Property 1: Decorator Identity Preservation**
        **Validates: Requirements 3.1, 5.3**
    """
    registry = EndpointRegistry()
    
    # Run 100 iterations with different random configurations
    for iteration in range(100):
        registry = EndpointRegistry()
        
        # Generate random base_path and leaf
        base_path = generate_random_base_path()
        leaf = generate_random_leaf()
        
        # Create a Blueprint subclass
        class TestBlueprint(Blueprint):
            pass
        
        TestBlueprint.base_path = base_path
        
        # Create a unique handler function for this iteration
        handler_name = f"handler_{iteration}_{generate_random_string(5, 10)}"
        handler_doc = f"Docstring for {handler_name}"
        
        # Use exec to create a function with a unique name
        exec_globals = {}
        exec(f"""
def {handler_name}():
    '''{handler_doc}'''
    pass
""", exec_globals)
        
        original_handler = exec_globals[handler_name]
        
        # Store original identity
        original_id = id(original_handler)
        original_name = original_handler.__name__
        original_doc = original_handler.__doc__
        
        # Apply the decorator
        decorated = TestBlueprint.attach_at(leaf=leaf)(original_handler)
        
        # Verify identity is preserved
        if decorated is not original_handler:
            errmsg = (
                f"Iteration {iteration}: Decorated function should be the same object. "
                f"original_id={original_id}, decorated_id={id(decorated)}"
            )
            raise AssertionError(errmsg)
        
        if id(decorated) != original_id:
            errmsg = (
                f"Iteration {iteration}: Decorated function should have same id. "
                f"original_id={original_id}, decorated_id={id(decorated)}"
            )
            raise AssertionError(errmsg)
        
        if decorated.__name__ != original_name:
            errmsg = (
                f"Iteration {iteration}: Decorated function should have same __name__. "
                f"original_name={original_name}, decorated_name={decorated.__name__}"
            )
            raise AssertionError(errmsg)
        
        if decorated.__doc__ != original_doc:
            errmsg = (
                f"Iteration {iteration}: Decorated function should have same __doc__. "
                f"original_doc={original_doc}, decorated_doc={decorated.__doc__}"
            )
            raise AssertionError(errmsg)
    
    return


def test_property_decorator_identity_with_stacking():
    """
        Property 1: Decorator Identity Preservation (stacking)
        
        *For any* handler function decorated with multiple decorators including
        `attach_at`, the decorator stacking SHALL work correctly because
        `attach_at` returns the original function unchanged.
        
        **Feature: blueprint-endpoints, Property 1: Decorator Identity Preservation**
        **Validates: Requirements 3.1, 5.3**
    """
    registry = EndpointRegistry()
    
    # Run 100 iterations with different random configurations
    for iteration in range(100):
        registry = EndpointRegistry()
        
        # Generate random base_path and leaf
        base_path = generate_random_base_path()
        leaf = generate_random_leaf()
        
        # Create a Blueprint subclass
        class TestBlueprint(Blueprint):
            pass
        
        TestBlueprint.base_path = base_path
        
        # Create a simple decorator that adds an attribute
        def add_marker(func):
            func._marker = f"marked_{iteration}"
            return func
        
        # Create a handler function
        def original_handler():
            pass
        
        # Apply decorators in stack order (bottom to top)
        # First attach_at, then add_marker
        decorated = add_marker(TestBlueprint.attach_at(leaf=leaf)(original_handler))
        
        # Verify the marker was added (decorator stacking worked)
        if not hasattr(decorated, "_marker"):
            errmsg = (
                f"Iteration {iteration}: Decorator stacking failed - marker not found"
            )
            raise AssertionError(errmsg)
        
        if decorated._marker != f"marked_{iteration}":
            errmsg = (
                f"Iteration {iteration}: Decorator stacking failed - wrong marker value. "
                f"expected='marked_{iteration}', got='{decorated._marker}'"
            )
            raise AssertionError(errmsg)
        
        # Verify the function is still the original
        if decorated is not original_handler:
            errmsg = (
                f"Iteration {iteration}: Decorated function should be the same object"
            )
            raise AssertionError(errmsg)
    
    return


# =============================================================================
# Property 2: Class Default Inheritance and Override
# Feature: blueprint-endpoints, Property 2: Class Default Inheritance and Override
# Validates: Requirements 3.8, 3.9, 3.10
# =============================================================================

def test_property_class_default_inheritance():
    """
        Property 2: Class Default Inheritance and Override
        
        *For any* Endpoint subclass with class-level attributes and any
        `attach_at` call:
        - If a kwarg is not provided, the class attribute value SHALL be used
        
        This test generates random class attributes and verifies that
        they are inherited when not overridden.
        
        **Feature: blueprint-endpoints, Property 2: Class Default Inheritance and Override**
        **Validates: Requirements 3.8, 3.9, 3.10**
    """
    registry = EndpointRegistry()
    registry = EndpointRegistry()
    
    # Run 100 iterations with different random configurations
    for iteration in range(100):
        registry = EndpointRegistry()
        
        # Generate random class attributes
        class_methods = random.choice([["GET"], ["POST"], ["GET", "POST"], ["PUT", "DELETE"]])
        class_version = f"v{random.randint(1, 5)}"
        class_tags = generate_random_tags()
        class_access_policy = generate_random_access_policy()
        class_rate_limit = generate_random_rate_limit()
        
        # Create a Blueprint subclass with random attributes
        class TestBlueprint(Blueprint):
            pass
        
        TestBlueprint.base_path = generate_random_base_path()
        TestBlueprint.methods = class_methods
        TestBlueprint.version = class_version
        TestBlueprint.tags = class_tags
        TestBlueprint.access_policy = class_access_policy
        TestBlueprint.rate_limit = class_rate_limit
        
        # Generate random leaf
        leaf = generate_random_leaf()
        
        # Create and decorate a handler without providing kwargs
        def handler():
            pass
        
        TestBlueprint.attach_at(leaf=leaf)(handler)
        registry.collect_from(handler)
        
        # Get the registered descriptor
        descriptors = registry.collect()
        if len(descriptors) != 1:
            errmsg = f"Iteration {iteration}: Expected 1 descriptor, got {len(descriptors)}"
            raise AssertionError(errmsg)
        
        desc = descriptors[0]
        
        # Verify methods are inherited
        if desc.methods != class_methods:
            errmsg = (
                f"Iteration {iteration}: Methods should be inherited from class. "
                f"class_methods={class_methods}, desc_methods={desc.methods}"
            )
            raise AssertionError(errmsg)
        
        # Verify version is inherited
        if desc.version != class_version:
            errmsg = (
                f"Iteration {iteration}: Version should be inherited from class. "
                f"class_version={class_version}, desc_version={desc.version}"
            )
            raise AssertionError(errmsg)
        
        # Verify tags are inherited (may be empty list if class_tags was empty)
        if class_tags:
            for tag in class_tags:
                if tag not in desc.tags:
                    errmsg = (
                        f"Iteration {iteration}: Tag '{tag}' should be inherited from class. "
                        f"class_tags={class_tags}, desc_tags={desc.tags}"
                    )
                    raise AssertionError(errmsg)
    
    return


def test_property_class_default_override():
    """
        Property 2: Class Default Inheritance and Override
        
        *For any* Endpoint subclass with class-level attributes and any
        `attach_at` call:
        - If a kwarg is explicitly provided, it SHALL override the class attribute
        
        This test generates random class attributes and explicit kwargs,
        verifying that kwargs override class attributes.
        
        **Feature: blueprint-endpoints, Property 2: Class Default Inheritance and Override**
        **Validates: Requirements 3.8, 3.9, 3.10**
    """
    registry = EndpointRegistry()
    registry = EndpointRegistry()
    
    # Run 100 iterations with different random configurations
    for iteration in range(100):
        registry = EndpointRegistry()
        
        # Generate random class attributes
        class_methods = ["GET"]
        class_version = "v1"
        class_tags = ["class_tag"]
        
        # Generate different kwargs to override
        kwarg_methods = ["POST", "PUT"]
        kwarg_version = "v99"
        kwarg_tags = ["override_tag"]
        
        # Create a Blueprint subclass with class attributes
        class TestBlueprint(Blueprint):
            pass
        
        TestBlueprint.base_path = generate_random_base_path()
        TestBlueprint.methods = class_methods
        TestBlueprint.version = class_version
        TestBlueprint.tags = class_tags
        
        # Generate random leaf
        leaf = generate_random_leaf()
        
        # Create and decorate a handler WITH explicit kwargs
        def handler():
            pass
        
        TestBlueprint.attach_at(
            leaf=leaf,
            methods=kwarg_methods,
            version=kwarg_version,
            tags=kwarg_tags
        )(handler)
        registry.collect_from(handler)
        
        # Get the registered descriptor
        descriptors = registry.collect()
        desc = descriptors[0]
        
        # Verify methods are overridden
        if desc.methods != kwarg_methods:
            errmsg = (
                f"Iteration {iteration}: Methods should be overridden by kwargs. "
                f"kwarg_methods={kwarg_methods}, desc_methods={desc.methods}"
            )
            raise AssertionError(errmsg)
        
        # Verify version is overridden
        if desc.version != kwarg_version:
            errmsg = (
                f"Iteration {iteration}: Version should be overridden by kwargs. "
                f"kwarg_version={kwarg_version}, desc_version={desc.version}"
            )
            raise AssertionError(errmsg)
        
        # Verify tags are overridden (child wins when merge_tags=False)
        if desc.tags != kwarg_tags:
            errmsg = (
                f"Iteration {iteration}: Tags should be overridden by kwargs. "
                f"kwarg_tags={kwarg_tags}, desc_tags={desc.tags}"
            )
            raise AssertionError(errmsg)
    
    return


def test_property_class_attributes_unchanged():
    """
        Property 2: Class Default Inheritance and Override
        
        *For any* Endpoint subclass with class-level attributes and any
        `attach_at` call:
        - Class attributes SHALL remain unchanged after attachment
        
        This test verifies that decorating handlers does not modify
        the class attributes.
        
        **Feature: blueprint-endpoints, Property 2: Class Default Inheritance and Override**
        **Validates: Requirements 3.8, 3.9, 3.10**
    """
    registry = EndpointRegistry()
    
    # Run 100 iterations with different random configurations
    for iteration in range(100):
        registry = EndpointRegistry()
        
        # Generate random class attributes
        class_methods = random.choice([["GET"], ["POST"], ["GET", "POST"]])
        class_version = f"v{random.randint(1, 5)}"
        class_tags = generate_random_tags()
        
        # Create a Blueprint subclass with class attributes
        class TestBlueprint(Blueprint):
            pass
        
        TestBlueprint.base_path = generate_random_base_path()
        TestBlueprint.methods = list(class_methods)  # Copy to compare later
        TestBlueprint.version = class_version
        TestBlueprint.tags = list(class_tags)  # Copy to compare later
        
        # Store original values
        original_methods = list(class_methods)
        original_version = class_version
        original_tags = list(class_tags)
        
        # Generate random leaf
        leaf = generate_random_leaf()
        
        # Create and decorate a handler with different kwargs
        def handler():
            pass
        
        TestBlueprint.attach_at(
            leaf=leaf,
            methods=["DELETE"],
            version="v999",
            tags=["different_tag"]
        )(handler)
        registry.collect_from(handler)
        
        # Verify class attributes are unchanged
        if TestBlueprint.methods != original_methods:
            errmsg = (
                f"Iteration {iteration}: Class methods should be unchanged. "
                f"original={original_methods}, current={TestBlueprint.methods}"
            )
            raise AssertionError(errmsg)
        
        if TestBlueprint.version != original_version:
            errmsg = (
                f"Iteration {iteration}: Class version should be unchanged. "
                f"original={original_version}, current={TestBlueprint.version}"
            )
            raise AssertionError(errmsg)
        
        if TestBlueprint.tags != original_tags:
            errmsg = (
                f"Iteration {iteration}: Class tags should be unchanged. "
                f"original={original_tags}, current={TestBlueprint.tags}"
            )
            raise AssertionError(errmsg)
    
    return


# =============================================================================
# Property 3: Extra Kwargs Preservation
# Feature: blueprint-endpoints, Property 3: Extra Kwargs Preservation
# Validates: Requirements 3.7
# =============================================================================

def test_property_extra_kwargs_preservation():
    """
        Property 3: Extra Kwargs Preservation
        
        *For any* additional kwargs passed to `attach_at` beyond the standard
        parameters, those kwargs SHALL appear verbatim in the descriptor's
        `extras` field.
        
        This test generates random extra kwargs and verifies they are
        preserved in the descriptor.
        
        **Feature: blueprint-endpoints, Property 3: Extra Kwargs Preservation**
        **Validates: Requirements 3.7**
    """
    registry = EndpointRegistry()
    registry = EndpointRegistry()
    
    # Run 100 iterations with different random configurations
    for iteration in range(100):
        registry = EndpointRegistry()
        
        # Generate random extra kwargs
        num_extras = random.randint(1, 5)
        extra_kwargs = {}
        for _ in range(num_extras):
            key = f"custom_{generate_random_string(3, 8)}"
            # Generate random value types
            value_type = random.choice(["string", "int", "bool", "list", "dict"])
            if value_type == "string":
                value = generate_random_string(5, 15)
            elif value_type == "int":
                value = random.randint(1, 1000)
            elif value_type == "bool":
                value = random.choice([True, False])
            elif value_type == "list":
                value = [generate_random_string(3, 6) for _ in range(random.randint(1, 3))]
            else:  # dict
                value = {generate_random_string(3, 5): random.randint(1, 100)}
            extra_kwargs[key] = value
        
        # Create a Blueprint subclass
        class TestBlueprint(Blueprint):
            pass
        
        TestBlueprint.base_path = generate_random_base_path()
        
        # Generate random leaf
        leaf = generate_random_leaf()
        
        # Create and decorate a handler with extra kwargs
        def handler():
            pass
        
        TestBlueprint.attach_at(leaf=leaf, **extra_kwargs)(handler)
        registry.collect_from(handler)
        
        # Get the registered descriptor
        descriptors = registry.collect()
        desc = descriptors[0]
        
        # Verify all extra kwargs are preserved in extras
        for key, expected_value in extra_kwargs.items():
            if key not in desc.extras:
                errmsg = (
                    f"Iteration {iteration}: Extra kwarg '{key}' should be in extras. "
                    f"extras={desc.extras}"
                )
                raise AssertionError(errmsg)
            
            if desc.extras[key] != expected_value:
                errmsg = (
                    f"Iteration {iteration}: Extra kwarg '{key}' should have value {expected_value}. "
                    f"got={desc.extras[key]}"
                )
                raise AssertionError(errmsg)
    
    return


def test_property_extra_kwargs_verbatim():
    """
        Property 3: Extra Kwargs Preservation (verbatim)
        
        *For any* additional kwargs passed to `attach_at`, the values SHALL
        be stored verbatim without modification.
        
        This test verifies that complex nested structures are preserved
        exactly as provided.
        
        **Feature: blueprint-endpoints, Property 3: Extra Kwargs Preservation**
        **Validates: Requirements 3.7**
    """
    registry = EndpointRegistry()
    registry = EndpointRegistry()
    
    # Run 100 iterations with different random configurations
    for iteration in range(100):
        registry = EndpointRegistry()
        
        # Generate complex nested structure
        nested_value = {
            "level1": {
                "level2": {
                    "value": generate_random_string(5, 10),
                    "number": random.randint(1, 1000),
                    "list": [random.randint(1, 100) for _ in range(3)]
                }
            },
            "array": [
                {"item": generate_random_string(3, 6)}
                for _ in range(random.randint(1, 3))
            ]
        }
        
        # Create a Blueprint subclass
        class TestBlueprint(Blueprint):
            pass
        
        TestBlueprint.base_path = generate_random_base_path()
        
        # Generate random leaf
        leaf = generate_random_leaf()
        
        # Create and decorate a handler with nested extra kwargs
        def handler():
            pass
        
        TestBlueprint.attach_at(leaf=leaf, nested_config=nested_value)(handler)
        registry.collect_from(handler)
        
        # Get the registered descriptor
        descriptors = registry.collect()
        desc = descriptors[0]
        
        # Verify nested structure is preserved verbatim
        if "nested_config" not in desc.extras:
            errmsg = f"Iteration {iteration}: 'nested_config' should be in extras"
            raise AssertionError(errmsg)
        
        if desc.extras["nested_config"] != nested_value:
            errmsg = (
                f"Iteration {iteration}: Nested config should be preserved verbatim. "
                f"expected={nested_value}, got={desc.extras['nested_config']}"
            )
            raise AssertionError(errmsg)
    
    return


# =============================================================================
# Property 14: Child Attribute Preservation
# Feature: blueprint-endpoints, Property 14: Child Attribute Preservation
# Validates: Requirements 4.6, 6.6
# =============================================================================

def test_property_child_attribute_preservation():
    """
        Property 14: Child Attribute Preservation
        
        *For any* `attach_child` call without explicit overrides, the child
        endpoint's class attributes SHALL be preserved in the resulting
        descriptor.
        
        This test generates random child endpoint attributes and verifies
        they are preserved when attach_child is called without overrides.
        
        **Feature: blueprint-endpoints, Property 14: Child Attribute Preservation**
        **Validates: Requirements 4.6, 6.6**
    """
    registry = EndpointRegistry()
    
    # Run 100 iterations with different random configurations
    for iteration in range(100):
        registry = EndpointRegistry()
        
        # Generate random child attributes
        child_leaf = generate_random_leaf()
        child_methods = random.choice([["GET"], ["POST"], ["GET", "POST"], ["PUT", "DELETE"]])
        child_version = f"v{random.randint(1, 5)}"
        child_tags = generate_random_tags()
        
        # Create a parent Blueprint
        class ParentBlueprint(Blueprint):
            pass
        
        ParentBlueprint.base_path = generate_random_base_path()
        ParentBlueprint.methods = ["GET"]  # Different from child
        ParentBlueprint.version = "v0"  # Different from child
        ParentBlueprint.tags = ["parent_tag"]  # Different from child
        
        # Create a child Endpoint with random attributes
        class ChildEndpoint(Endpoint):
            pass
        
        ChildEndpoint.base_leaf = child_leaf
        ChildEndpoint.methods = child_methods
        ChildEndpoint.version = child_version
        ChildEndpoint.tags = child_tags
        
        # Call attach_child WITHOUT overrides
        descriptor = ParentBlueprint.attach_child(ChildEndpoint)
        
        # Verify child methods are preserved
        if descriptor.methods != child_methods:
            errmsg = (
                f"Iteration {iteration}: Child methods should be preserved. "
                f"child_methods={child_methods}, desc_methods={descriptor.methods}"
            )
            raise AssertionError(errmsg)
        
        # Verify child version is preserved
        if descriptor.version != child_version:
            errmsg = (
                f"Iteration {iteration}: Child version should be preserved. "
                f"child_version={child_version}, desc_version={descriptor.version}"
            )
            raise AssertionError(errmsg)
        
        # Verify child tags are preserved (child wins by default when merge_tags=False)
        if child_tags:
            for tag in child_tags:
                if tag not in descriptor.tags:
                    errmsg = (
                        f"Iteration {iteration}: Child tag '{tag}' should be preserved. "
                        f"child_tags={child_tags}, desc_tags={descriptor.tags}"
                    )
                    raise AssertionError(errmsg)
    
    return


def test_property_child_attribute_preservation_with_overrides():
    """
        Property 14: Child Attribute Preservation (with overrides)
        
        *For any* `attach_child` call with explicit overrides, the overrides
        SHALL apply only to the specified attributes, while other child
        attributes remain preserved.
        
        **Feature: blueprint-endpoints, Property 14: Child Attribute Preservation**
        **Validates: Requirements 4.6, 6.6**
    """
    registry = EndpointRegistry()
    
    # Run 100 iterations with different random configurations
    for iteration in range(100):
        registry = EndpointRegistry()
        
        # Generate random child attributes
        child_leaf = generate_random_leaf()
        child_methods = random.choice([["GET"], ["POST"], ["GET", "POST"]])
        child_version = f"v{random.randint(1, 5)}"
        child_tags = generate_random_tags()
        
        # Generate override values (different from child)
        override_methods = ["DELETE", "PATCH"]
        
        # Create a parent Blueprint
        class ParentBlueprint(Blueprint):
            pass
        
        ParentBlueprint.base_path = generate_random_base_path()
        
        # Create a child Endpoint with random attributes
        class ChildEndpoint(Endpoint):
            pass
        
        ChildEndpoint.base_leaf = child_leaf
        ChildEndpoint.methods = child_methods
        ChildEndpoint.version = child_version
        ChildEndpoint.tags = child_tags
        
        # Call attach_child WITH methods override only
        descriptor = ParentBlueprint.attach_child(ChildEndpoint, methods=override_methods)
        
        # Verify methods are overridden
        if descriptor.methods != override_methods:
            errmsg = (
                f"Iteration {iteration}: Methods should be overridden. "
                f"override_methods={override_methods}, desc_methods={descriptor.methods}"
            )
            raise AssertionError(errmsg)
        
        # Verify version is still preserved from child
        if descriptor.version != child_version:
            errmsg = (
                f"Iteration {iteration}: Version should be preserved from child. "
                f"child_version={child_version}, desc_version={descriptor.version}"
            )
            raise AssertionError(errmsg)
        
        # Verify tags are still preserved from child
        if child_tags:
            for tag in child_tags:
                if tag not in descriptor.tags:
                    errmsg = (
                        f"Iteration {iteration}: Child tag '{tag}' should be preserved. "
                        f"child_tags={child_tags}, desc_tags={descriptor.tags}"
                    )
                    raise AssertionError(errmsg)
    
    return


def test_property_child_attribute_preservation_access_policy():
    """
        Property 14: Child Attribute Preservation (access policy)
        
        *For any* `attach_child` call without access_policy override, the child
        endpoint's access_policy SHALL be preserved (merged with parent).
        
        **Feature: blueprint-endpoints, Property 14: Child Attribute Preservation**
        **Validates: Requirements 4.6, 6.6**
    """
    registry = EndpointRegistry()
    
    # Run 100 iterations with different random configurations
    for iteration in range(100):
        registry = EndpointRegistry()
        
        # Generate random child access policy
        child_roles = ["child_role_" + generate_random_string(3, 5)]
        child_scopes = ["child_scope_" + generate_random_string(3, 5)]
        child_policy = AccessPolicy(roles=child_roles, scopes=child_scopes)
        
        # Create a parent Blueprint with different policy
        class ParentBlueprint(Blueprint):
            pass
        
        ParentBlueprint.base_path = generate_random_base_path()
        ParentBlueprint.access_policy = AccessPolicy(
            roles=["parent_role"],
            scopes=["parent_scope"]
        )
        
        # Create a child Endpoint with access policy
        class ChildEndpoint(Endpoint):
            pass
        
        ChildEndpoint.base_leaf = generate_random_leaf()
        ChildEndpoint.access_policy = child_policy
        
        # Call attach_child WITHOUT access_policy override
        descriptor = ParentBlueprint.attach_child(ChildEndpoint)
        
        # Verify child roles are in merged policy (union by default)
        for role in child_roles:
            if role not in descriptor.constraints.access_policy.roles:
                errmsg = (
                    f"Iteration {iteration}: Child role '{role}' should be in merged policy. "
                    f"child_roles={child_roles}, merged_roles={descriptor.constraints.access_policy.roles}"
                )
                raise AssertionError(errmsg)
        
        # Verify child scopes are in merged policy (union by default)
        for scope in child_scopes:
            if scope not in descriptor.constraints.access_policy.scopes:
                errmsg = (
                    f"Iteration {iteration}: Child scope '{scope}' should be in merged policy. "
                    f"child_scopes={child_scopes}, merged_scopes={descriptor.constraints.access_policy.scopes}"
                )
                raise AssertionError(errmsg)
    
    return


def test_property_child_attribute_preservation_rate_limit():
    """
        Property 14: Child Attribute Preservation (rate limit)
        
        *For any* `attach_child` call without rate_limit override, the child
        endpoint's rate_limit SHALL be preserved (most restrictive wins).
        
        **Feature: blueprint-endpoints, Property 14: Child Attribute Preservation**
        **Validates: Requirements 4.6, 6.6**
    """
    registry = EndpointRegistry()
    
    # Run 100 iterations with different random configurations
    for iteration in range(100):
        registry = EndpointRegistry()
        
        # Generate random child rate limit (more restrictive than parent)
        child_requests = random.randint(10, 50)
        child_window = 60
        child_rate_limit = RateLimit(requests=child_requests, window=child_window)
        
        # Create a parent Blueprint with less restrictive rate limit
        class ParentBlueprint(Blueprint):
            pass
        
        ParentBlueprint.base_path = generate_random_base_path()
        ParentBlueprint.rate_limit = RateLimit(requests=100, window=60)
        
        # Create a child Endpoint with rate limit
        class ChildEndpoint(Endpoint):
            pass
        
        ChildEndpoint.base_leaf = generate_random_leaf()
        ChildEndpoint.rate_limit = child_rate_limit
        
        # Call attach_child WITHOUT rate_limit override
        descriptor = ParentBlueprint.attach_child(ChildEndpoint)
        
        # Verify most restrictive rate limit is used
        # Child has fewer requests, so it should be the most restrictive
        if descriptor.constraints.rate_limit.requests != child_requests:
            errmsg = (
                f"Iteration {iteration}: Most restrictive rate limit should be used. "
                f"child_requests={child_requests}, desc_requests={descriptor.constraints.rate_limit.requests}"
            )
            raise AssertionError(errmsg)
    
    return


def test_property_child_attribute_preservation_serializers():
    """
        Property 14: Child Attribute Preservation (serializers)
        
        *For any* `attach_child` call, the child endpoint's serializers
        SHALL be preserved in the descriptor's extras.
        
        **Feature: blueprint-endpoints, Property 14: Child Attribute Preservation**
        **Validates: Requirements 4.6, 6.6**
    """
    registry = EndpointRegistry()
    
    # Run 100 iterations with different random configurations
    for iteration in range(100):
        registry = EndpointRegistry()
        
        # Generate random serializers
        serializer_key = generate_random_string(3, 8)
        serializer_value = generate_random_string(5, 15)
        child_serializers = {serializer_key: serializer_value}
        
        # Create a parent Blueprint
        class ParentBlueprint(Blueprint):
            pass
        
        ParentBlueprint.base_path = generate_random_base_path()
        
        # Create a child Endpoint with serializers
        class ChildEndpoint(Endpoint):
            pass
        
        ChildEndpoint.base_leaf = generate_random_leaf()
        ChildEndpoint.serializers = child_serializers
        
        # Call attach_child
        descriptor = ParentBlueprint.attach_child(ChildEndpoint)
        
        # Verify serializers are preserved in extras
        if "serializers" not in descriptor.extras:
            errmsg = (
                f"Iteration {iteration}: Serializers should be in extras. "
                f"extras={descriptor.extras}"
            )
            raise AssertionError(errmsg)
        
        if descriptor.extras["serializers"] != child_serializers:
            errmsg = (
                f"Iteration {iteration}: Serializers should be preserved. "
                f"child_serializers={child_serializers}, desc_serializers={descriptor.extras['serializers']}"
            )
            raise AssertionError(errmsg)
    
    return


# =============================================================================
# Property 12: Blueprint Multi-Attachment
# Feature: blueprint-endpoints, Property 12: Blueprint Multi-Attachment
# Validates: Requirements 1.1, 1.3, 1.4
# =============================================================================

def test_property_blueprint_multi_attachment():
    """
        Property 12: Blueprint Multi-Attachment
        
        *For any* Blueprint with a `register()` method that calls `attach_at`
        multiple times, each call SHALL emit a separate EndpointDescriptor,
        and `register()` SHALL return all descriptors.
        
        This test generates random numbers of endpoints and verifies that
        register() returns all of them.
        
        **Feature: blueprint-endpoints, Property 12: Blueprint Multi-Attachment**
        **Validates: Requirements 1.1, 1.3, 1.4**
    """
    registry = EndpointRegistry()
    
    # Run 100 iterations with different random configurations
    for iteration in range(100):
        registry = EndpointRegistry()
        
        # Generate random number of endpoints (1-5)
        num_endpoints = random.randint(1, 5)
        
        # Generate random base_path
        base_path = generate_random_base_path()
        
        # Create a Blueprint subclass
        class TestBlueprint(Blueprint):
            pass
        
        TestBlueprint.base_path = base_path
        
        # Generate random leaves and attach handlers
        leaves = []
        for i in range(num_endpoints):
            leaf = f"{generate_random_leaf()}_{i}"
            leaves.append(leaf)
            
            # Create a unique handler for each endpoint
            def make_handler(idx):
                def handler():
                    pass
                handler.__name__ = f"handler_{idx}"
                return handler
            
            TestBlueprint.attach_at(leaf=leaf)(make_handler(i))
        
        # Call register() and verify all descriptors are returned
        result = TestBlueprint.register()
        
        # Verify correct number of descriptors
        if len(result) != num_endpoints:
            errmsg = (
                f"Iteration {iteration}: Expected {num_endpoints} descriptors, "
                f"got {len(result)}"
            )
            raise AssertionError(errmsg)
        
        # Verify each leaf is represented in the descriptors
        result_paths = [desc.path for desc in result]
        for leaf in leaves:
            expected_path = f"{base_path.rstrip('/')}/{leaf}"
            if expected_path not in result_paths:
                errmsg = (
                    f"Iteration {iteration}: Expected path '{expected_path}' not found. "
                    f"result_paths={result_paths}"
                )
                raise AssertionError(errmsg)
    
    return


def test_property_blueprint_multi_attachment_separate_descriptors():
    """
        Property 12: Blueprint Multi-Attachment (separate descriptors)
        
        *For any* Blueprint with multiple attach_at calls, each call SHALL
        emit a separate EndpointDescriptor with its own unique path.
        
        **Feature: blueprint-endpoints, Property 12: Blueprint Multi-Attachment**
        **Validates: Requirements 1.1, 1.3, 1.4**
    """
    registry = EndpointRegistry()
    
    # Run 100 iterations with different random configurations
    for iteration in range(100):
        registry = EndpointRegistry()
        
        # Generate random number of endpoints (2-4)
        num_endpoints = random.randint(2, 4)
        
        # Generate random base_path
        base_path = generate_random_base_path()
        
        # Create a Blueprint subclass
        class TestBlueprint(Blueprint):
            pass
        
        TestBlueprint.base_path = base_path
        
        # Generate unique leaves
        leaves = [f"endpoint_{i}_{generate_random_string(3, 6)}" for i in range(num_endpoints)]
        
        # Attach handlers
        for leaf in leaves:
            def handler():
                pass
            TestBlueprint.attach_at(leaf=leaf)(handler)
            registry.collect_from(handler)
        
        # Call register()
        result = TestBlueprint.register()
        
        # Verify all paths are unique
        paths = [desc.path for desc in result]
        unique_paths = set(paths)
        
        if len(unique_paths) != len(paths):
            errmsg = (
                f"Iteration {iteration}: All descriptor paths should be unique. "
                f"paths={paths}"
            )
            raise AssertionError(errmsg)
        
        # Verify each descriptor is a separate object
        descriptor_ids = [id(desc) for desc in result]
        unique_ids = set(descriptor_ids)
        
        if len(unique_ids) != len(descriptor_ids):
            errmsg = (
                f"Iteration {iteration}: Each descriptor should be a separate object"
            )
            raise AssertionError(errmsg)
    
    return


def test_property_blueprint_multi_attachment_all_inherit_constraints():
    """
        Property 12: Blueprint Multi-Attachment (constraint inheritance)
        
        *For any* Blueprint with multiple attach_at calls, all descriptors
        SHALL inherit the blueprint's constraints unless overridden.
        
        **Feature: blueprint-endpoints, Property 12: Blueprint Multi-Attachment**
        **Validates: Requirements 1.1, 1.3, 1.4**
    """
    registry = EndpointRegistry()
    
    # Run 100 iterations with different random configurations
    for iteration in range(100):
        registry = EndpointRegistry()
        
        # Generate random blueprint constraints
        blueprint_roles = ["role_" + generate_random_string(3, 5)]
        blueprint_policy = AccessPolicy(roles=blueprint_roles, scopes=[])
        blueprint_rate_limit = RateLimit(
            requests=random.randint(50, 200),
            window=60
        )
        
        # Create a Blueprint subclass with constraints
        class TestBlueprint(Blueprint):
            pass
        
        TestBlueprint.base_path = generate_random_base_path()
        TestBlueprint.access_policy = blueprint_policy
        TestBlueprint.rate_limit = blueprint_rate_limit
        
        # Generate random number of endpoints (2-4)
        num_endpoints = random.randint(2, 4)
        
        # Attach handlers without overriding constraints
        for i in range(num_endpoints):
            leaf = f"endpoint_{i}_{generate_random_string(3, 6)}"
            
            def handler():
                pass
            
            TestBlueprint.attach_at(leaf=leaf)(handler)
            registry.collect_from(handler)
        
        # Call register()
        result = TestBlueprint.register()
        
        # Verify all descriptors inherit blueprint constraints
        for desc in result:
            # Check access policy roles
            for role in blueprint_roles:
                if role not in desc.constraints.access_policy.roles:
                    errmsg = (
                        f"Iteration {iteration}: Descriptor should inherit blueprint role '{role}'. "
                        f"path={desc.path}, roles={desc.constraints.access_policy.roles}"
                    )
                    raise AssertionError(errmsg)
            
            # Check rate limit
            if desc.constraints.rate_limit.requests != blueprint_rate_limit.requests:
                errmsg = (
                    f"Iteration {iteration}: Descriptor should inherit blueprint rate limit. "
                    f"path={desc.path}, expected={blueprint_rate_limit.requests}, "
                    f"got={desc.constraints.rate_limit.requests}"
                )
                raise AssertionError(errmsg)
    
    return


# =============================================================================
# Property 13: Blueprint Router Integration
# Feature: blueprint-endpoints, Property 13: Blueprint Router Integration
# Validates: Requirements 1.5, 1.6
# =============================================================================

def test_property_blueprint_router_integration_with_router():
    """
        Property 13: Blueprint Router Integration
        
        *For any* Blueprint `register(router)` call:
        - If router is provided, `router.add_endpoint()` SHALL be called
          for each descriptor
        
        This test generates random blueprints and verifies that the router
        receives all descriptors.
        
        **Feature: blueprint-endpoints, Property 13: Blueprint Router Integration**
        **Validates: Requirements 1.5, 1.6**
    """
    registry = EndpointRegistry()
    
    # Run 100 iterations with different random configurations
    for iteration in range(100):
        registry = EndpointRegistry()
        
        # Generate random number of endpoints (1-5)
        num_endpoints = random.randint(1, 5)
        
        # Create a Blueprint subclass
        class TestBlueprint(Blueprint):
            pass
        
        TestBlueprint.base_path = generate_random_base_path()
        
        # Attach handlers
        for i in range(num_endpoints):
            leaf = f"endpoint_{i}_{generate_random_string(3, 6)}"
            
            def handler():
                pass
            
            TestBlueprint.attach_at(leaf=leaf)(handler)
            registry.collect_from(handler)
        
        # Create a mock router that tracks calls
        added_descriptors = []
        
        class MockRouter:
            def add_endpoint(self, descriptor):
                added_descriptors.append(descriptor)
        
        router = MockRouter()
        
        # Call register with router
        result = TestBlueprint.register(router=router)
        
        # Verify router.add_endpoint was called for each descriptor
        if len(added_descriptors) != num_endpoints:
            errmsg = (
                f"Iteration {iteration}: Expected {num_endpoints} add_endpoint calls, "
                f"got {len(added_descriptors)}"
            )
            raise AssertionError(errmsg)
        
        # Verify the same descriptors were returned
        if len(result) != num_endpoints:
            errmsg = (
                f"Iteration {iteration}: Expected {num_endpoints} descriptors returned, "
                f"got {len(result)}"
            )
            raise AssertionError(errmsg)
        
        # Verify the paths match
        result_paths = sorted([desc.path for desc in result])
        added_paths = sorted([desc.path for desc in added_descriptors])
        
        if result_paths != added_paths:
            errmsg = (
                f"Iteration {iteration}: Router should receive same descriptors as returned. "
                f"result_paths={result_paths}, added_paths={added_paths}"
            )
            raise AssertionError(errmsg)
    
    return


def test_property_blueprint_router_integration_without_router():
    """
        Property 13: Blueprint Router Integration
        
        *For any* Blueprint `register(router)` call:
        - If router is None, descriptors SHALL be returned without router
          interaction
        
        This test verifies that register() works correctly without a router.
        
        **Feature: blueprint-endpoints, Property 13: Blueprint Router Integration**
        **Validates: Requirements 1.5, 1.6**
    """
    registry = EndpointRegistry()
    
    # Run 100 iterations with different random configurations
    for iteration in range(100):
        registry = EndpointRegistry()
        
        # Generate random number of endpoints (1-5)
        num_endpoints = random.randint(1, 5)
        
        # Create a Blueprint subclass
        class TestBlueprint(Blueprint):
            pass
        
        TestBlueprint.base_path = generate_random_base_path()
        
        # Attach handlers
        leaves = []
        for i in range(num_endpoints):
            leaf = f"endpoint_{i}_{generate_random_string(3, 6)}"
            leaves.append(leaf)
            
            def handler():
                pass
            
            TestBlueprint.attach_at(leaf=leaf)(handler)
            registry.collect_from(handler)
        
        # Call register without router (router=None)
        result = TestBlueprint.register(router=None)
        
        # Verify descriptors are returned
        if len(result) != num_endpoints:
            errmsg = (
                f"Iteration {iteration}: Expected {num_endpoints} descriptors, "
                f"got {len(result)}"
            )
            raise AssertionError(errmsg)
        
        # Verify all leaves are represented
        result_paths = [desc.path for desc in result]
        base_path = TestBlueprint.base_path.rstrip("/")
        
        for leaf in leaves:
            expected_path = f"{base_path}/{leaf}"
            if expected_path not in result_paths:
                errmsg = (
                    f"Iteration {iteration}: Expected path '{expected_path}' not found. "
                    f"result_paths={result_paths}"
                )
                raise AssertionError(errmsg)
    
    return


def test_property_blueprint_router_integration_router_receives_complete_descriptors():
    """
        Property 13: Blueprint Router Integration (complete descriptors)
        
        *For any* Blueprint `register(router)` call, the router SHALL receive
        complete descriptors with all merged metadata.
        
        **Feature: blueprint-endpoints, Property 13: Blueprint Router Integration**
        **Validates: Requirements 1.5, 1.6**
    """
    registry = EndpointRegistry()
    
    # Run 100 iterations with different random configurations
    for iteration in range(100):
        registry = EndpointRegistry()
        
        # Generate random blueprint attributes
        blueprint_roles = ["role_" + generate_random_string(3, 5)]
        blueprint_policy = AccessPolicy(roles=blueprint_roles, scopes=[])
        blueprint_version = f"v{random.randint(1, 5)}"
        blueprint_tags = generate_random_tags()
        
        # Create a Blueprint subclass
        class TestBlueprint(Blueprint):
            pass
        
        TestBlueprint.base_path = generate_random_base_path()
        TestBlueprint.access_policy = blueprint_policy
        TestBlueprint.version = blueprint_version
        TestBlueprint.tags = blueprint_tags
        
        # Attach a handler
        leaf = generate_random_leaf()
        
        def handler():
            pass
        
        TestBlueprint.attach_at(leaf=leaf)(handler)
        registry.collect_from(handler)
        
        # Create a mock router
        received_descriptor = None
        
        class MockRouter:
            def add_endpoint(self, descriptor):
                nonlocal received_descriptor
                received_descriptor = descriptor
        
        router = MockRouter()
        
        # Call register with router
        TestBlueprint.register(router=router)
        
        # Verify router received complete descriptor
        if received_descriptor is None:
            errmsg = f"Iteration {iteration}: Router should receive a descriptor"
            raise AssertionError(errmsg)
        
        # Verify path is correct
        expected_path = f"{TestBlueprint.base_path.rstrip('/')}/{leaf}"
        if received_descriptor.path != expected_path:
            errmsg = (
                f"Iteration {iteration}: Descriptor path should be correct. "
                f"expected={expected_path}, got={received_descriptor.path}"
            )
            raise AssertionError(errmsg)
        
        # Verify version is inherited
        if received_descriptor.version != blueprint_version:
            errmsg = (
                f"Iteration {iteration}: Descriptor version should be inherited. "
                f"expected={blueprint_version}, got={received_descriptor.version}"
            )
            raise AssertionError(errmsg)
        
        # Verify access policy roles are inherited
        for role in blueprint_roles:
            if role not in received_descriptor.constraints.access_policy.roles:
                errmsg = (
                    f"Iteration {iteration}: Descriptor should inherit role '{role}'. "
                    f"roles={received_descriptor.constraints.access_policy.roles}"
                )
                raise AssertionError(errmsg)
    
    return


# =============================================================================
# Property 15: Blueprint Idempotency
# Feature: blueprint-endpoints, Property 15: Blueprint Idempotency
# Validates: Requirements 6.7
# =============================================================================

def test_property_blueprint_idempotency():
    """
        Property 15: Blueprint Idempotency
        
        *For any* Blueprint, calling `register()` multiple times SHALL return
        equivalent descriptor lists (same paths, methods, constraints).
        
        This test generates random blueprints and verifies that repeated
        register() calls return equivalent results.
        
        **Feature: blueprint-endpoints, Property 15: Blueprint Idempotency**
        **Validates: Requirements 6.7**
    """
    registry = EndpointRegistry()
    
    # Run 100 iterations with different random configurations
    for iteration in range(100):
        registry = EndpointRegistry()
        
        # Generate random number of endpoints (1-4)
        num_endpoints = random.randint(1, 4)
        
        # Create a Blueprint subclass
        class TestBlueprint(Blueprint):
            pass
        
        TestBlueprint.base_path = generate_random_base_path()
        TestBlueprint.access_policy = generate_random_access_policy()
        TestBlueprint.rate_limit = generate_random_rate_limit()
        
        # Attach handlers
        for i in range(num_endpoints):
            leaf = f"endpoint_{i}_{generate_random_string(3, 6)}"
            
            def handler():
                pass
            
            TestBlueprint.attach_at(leaf=leaf)(handler)
            registry.collect_from(handler)
        
        # Call register() multiple times
        result1 = TestBlueprint.register()
        result2 = TestBlueprint.register()
        result3 = TestBlueprint.register()
        
        # Verify same number of descriptors
        if len(result1) != len(result2) or len(result2) != len(result3):
            errmsg = (
                f"Iteration {iteration}: All register() calls should return same count. "
                f"counts: {len(result1)}, {len(result2)}, {len(result3)}"
            )
            raise AssertionError(errmsg)
        
        # Verify same paths
        paths1 = sorted([desc.path for desc in result1])
        paths2 = sorted([desc.path for desc in result2])
        paths3 = sorted([desc.path for desc in result3])
        
        if paths1 != paths2 or paths2 != paths3:
            errmsg = (
                f"Iteration {iteration}: All register() calls should return same paths. "
                f"paths1={paths1}, paths2={paths2}, paths3={paths3}"
            )
            raise AssertionError(errmsg)
    
    return


def test_property_blueprint_idempotency_same_methods():
    """
        Property 15: Blueprint Idempotency (methods)
        
        *For any* Blueprint, calling `register()` multiple times SHALL return
        descriptors with the same methods.
        
        **Feature: blueprint-endpoints, Property 15: Blueprint Idempotency**
        **Validates: Requirements 6.7**
    """
    registry = EndpointRegistry()
    
    # Run 100 iterations with different random configurations
    for iteration in range(100):
        registry = EndpointRegistry()
        
        # Generate random methods
        methods = random.choice([["GET"], ["POST"], ["GET", "POST"], ["PUT", "DELETE"]])
        
        # Create a Blueprint subclass
        class TestBlueprint(Blueprint):
            pass
        
        TestBlueprint.base_path = generate_random_base_path()
        TestBlueprint.methods = methods
        
        # Attach a handler
        leaf = generate_random_leaf()
        
        def handler():
            pass
        
        TestBlueprint.attach_at(leaf=leaf)(handler)
        registry.collect_from(handler)
        
        # Call register() multiple times
        result1 = TestBlueprint.register()
        result2 = TestBlueprint.register()
        
        # Verify same methods
        methods1 = result1[0].methods
        methods2 = result2[0].methods
        
        if methods1 != methods2:
            errmsg = (
                f"Iteration {iteration}: Methods should be same across calls. "
                f"methods1={methods1}, methods2={methods2}"
            )
            raise AssertionError(errmsg)
    
    return


def test_property_blueprint_idempotency_same_constraints():
    """
        Property 15: Blueprint Idempotency (constraints)
        
        *For any* Blueprint, calling `register()` multiple times SHALL return
        descriptors with the same constraints.
        
        **Feature: blueprint-endpoints, Property 15: Blueprint Idempotency**
        **Validates: Requirements 6.7**
    """
    registry = EndpointRegistry()
    
    # Run 100 iterations with different random configurations
    for iteration in range(100):
        registry = EndpointRegistry()
        
        # Generate random constraints
        roles = generate_random_roles()
        scopes = generate_random_scopes()
        access_policy = AccessPolicy(roles=roles, scopes=scopes)
        rate_limit = generate_random_rate_limit()
        
        # Create a Blueprint subclass
        class TestBlueprint(Blueprint):
            pass
        
        TestBlueprint.base_path = generate_random_base_path()
        TestBlueprint.access_policy = access_policy
        TestBlueprint.rate_limit = rate_limit
        
        # Attach a handler
        leaf = generate_random_leaf()
        
        def handler():
            pass
        
        TestBlueprint.attach_at(leaf=leaf)(handler)
        registry.collect_from(handler)
        
        # Call register() multiple times
        result1 = TestBlueprint.register()
        result2 = TestBlueprint.register()
        
        # Verify same access policy roles
        roles1 = sorted(result1[0].constraints.access_policy.roles) if result1[0].constraints.access_policy else []
        roles2 = sorted(result2[0].constraints.access_policy.roles) if result2[0].constraints.access_policy else []
        
        if roles1 != roles2:
            errmsg = (
                f"Iteration {iteration}: Roles should be same across calls. "
                f"roles1={roles1}, roles2={roles2}"
            )
            raise AssertionError(errmsg)
        
        # Verify same rate limit
        if result1[0].constraints.rate_limit is not None and result2[0].constraints.rate_limit is not None:
            if result1[0].constraints.rate_limit.requests != result2[0].constraints.rate_limit.requests:
                errmsg = (
                    f"Iteration {iteration}: Rate limit should be same across calls. "
                    f"requests1={result1[0].constraints.rate_limit.requests}, "
                    f"requests2={result2[0].constraints.rate_limit.requests}"
                )
                raise AssertionError(errmsg)
    
    return


def test_property_blueprint_idempotency_with_router():
    """
        Property 15: Blueprint Idempotency (with router)
        
        *For any* Blueprint, calling `register(router)` multiple times SHALL
        call router.add_endpoint() each time with equivalent descriptors.
        
        **Feature: blueprint-endpoints, Property 15: Blueprint Idempotency**
        **Validates: Requirements 6.7**
    """
    registry = EndpointRegistry()
    
    # Run 100 iterations with different random configurations
    for iteration in range(100):
        registry = EndpointRegistry()
        
        # Create a Blueprint subclass
        class TestBlueprint(Blueprint):
            pass
        
        TestBlueprint.base_path = generate_random_base_path()
        
        # Attach handlers
        num_endpoints = random.randint(1, 3)
        for i in range(num_endpoints):
            leaf = f"endpoint_{i}_{generate_random_string(3, 6)}"
            
            def handler():
                pass
            
            TestBlueprint.attach_at(leaf=leaf)(handler)
            registry.collect_from(handler)
        
        # Create mock routers for each call
        added1 = []
        added2 = []
        
        class MockRouter1:
            def add_endpoint(self, descriptor):
                added1.append(descriptor)
        
        class MockRouter2:
            def add_endpoint(self, descriptor):
                added2.append(descriptor)
        
        # Call register() with different routers
        TestBlueprint.register(router=MockRouter1())
        TestBlueprint.register(router=MockRouter2())
        
        # Verify same number of add_endpoint calls
        if len(added1) != len(added2):
            errmsg = (
                f"Iteration {iteration}: Same number of add_endpoint calls expected. "
                f"added1={len(added1)}, added2={len(added2)}"
            )
            raise AssertionError(errmsg)
        
        # Verify same paths
        paths1 = sorted([desc.path for desc in added1])
        paths2 = sorted([desc.path for desc in added2])
        
        if paths1 != paths2:
            errmsg = (
                f"Iteration {iteration}: Same paths should be added to both routers. "
                f"paths1={paths1}, paths2={paths2}"
            )
            raise AssertionError(errmsg)
    
    return


# =============================================================================
# Property 9: Descriptor Emission
# Feature: blueprint-endpoints, Property 9: Descriptor Emission
# Validates: Requirements 5.1, 5.6
# =============================================================================

def test_property_descriptor_emission():
    """
        Property 9: Descriptor Emission
        
        *For any* `attach_at` or `attach_child` call, an EndpointDescriptor
        SHALL be emitted to the EndpointRegistry containing the handler
        reference and merged metadata.
        
        This test generates random endpoints and verifies that descriptors
        are properly emitted to the registry with correct metadata.
        
        **Feature: blueprint-endpoints, Property 9: Descriptor Emission**
        **Validates: Requirements 5.1, 5.6**
    """
    registry = EndpointRegistry()
    registry = EndpointRegistry()
    
    # Run 100 iterations with different random configurations
    for iteration in range(100):
        registry = EndpointRegistry()
        
        # Generate random configuration
        base_path = generate_random_base_path()
        leaf = generate_random_leaf()
        methods = random.choice([["GET"], ["POST"], ["GET", "POST"], ["PUT", "DELETE"]])
        version = f"v{random.randint(1, 5)}"
        tags = generate_random_tags()
        access_policy = generate_random_access_policy()
        rate_limit = generate_random_rate_limit()
        
        # Create a Blueprint subclass
        class TestBlueprint(Blueprint):
            pass
        
        TestBlueprint.base_path = base_path
        TestBlueprint.access_policy = access_policy
        TestBlueprint.rate_limit = rate_limit
        
        # Create and decorate a handler
        def handler():
            pass
        
        handler.__name__ = f"handler_{iteration}"
        
        TestBlueprint.attach_at(
            leaf=leaf,
            methods=methods,
            version=version,
            tags=tags
        )(handler)
        registry.collect_from(handler)
        
        # Verify descriptor was emitted to registry
        descriptors = registry.collect()
        
        if len(descriptors) != 1:
            errmsg = (
                f"Iteration {iteration}: Expected 1 descriptor in registry, "
                f"got {len(descriptors)}"
            )
            raise AssertionError(errmsg)
        
        desc = descriptors[0]
        
        # Verify handler reference is preserved
        if desc.handler is not handler:
            errmsg = (
                f"Iteration {iteration}: Descriptor should contain handler reference. "
                f"expected handler={handler}, got={desc.handler}"
            )
            raise AssertionError(errmsg)
        
        # Verify path is correctly composed
        expected_path = f"{base_path.rstrip('/')}/{leaf}"
        if desc.path != expected_path:
            errmsg = (
                f"Iteration {iteration}: Descriptor path should be composed correctly. "
                f"expected={expected_path}, got={desc.path}"
            )
            raise AssertionError(errmsg)
        
        # Verify methods are preserved
        if desc.methods != methods:
            errmsg = (
                f"Iteration {iteration}: Descriptor methods should match. "
                f"expected={methods}, got={desc.methods}"
            )
            raise AssertionError(errmsg)
        
        # Verify version is preserved
        if desc.version != version:
            errmsg = (
                f"Iteration {iteration}: Descriptor version should match. "
                f"expected={version}, got={desc.version}"
            )
            raise AssertionError(errmsg)
        
        # Verify tags are preserved (child tags win when merge_tags=False)
        if tags:
            for tag in tags:
                if tag not in desc.tags:
                    errmsg = (
                        f"Iteration {iteration}: Descriptor should contain tag '{tag}'. "
                        f"expected_tags={tags}, got_tags={desc.tags}"
                    )
                    raise AssertionError(errmsg)
    
    return


def test_property_descriptor_emission_with_attach_child():
    """
        Property 9: Descriptor Emission (attach_child)
        
        *For any* `attach_child` call, an EndpointDescriptor SHALL be emitted
        to the EndpointRegistry containing the merged metadata.
        
        **Feature: blueprint-endpoints, Property 9: Descriptor Emission**
        **Validates: Requirements 5.1, 5.6**
    """
    registry = EndpointRegistry()
    registry = EndpointRegistry()
    
    # Run 100 iterations with different random configurations
    for iteration in range(100):
        registry = EndpointRegistry()
        
        # Generate random configuration
        parent_base_path = generate_random_base_path()
        child_leaf = generate_random_leaf()
        child_methods = random.choice([["GET"], ["POST"], ["GET", "POST"]])
        child_version = f"v{random.randint(1, 5)}"
        child_tags = generate_random_tags()
        
        # Create parent Blueprint
        class ParentBlueprint(Blueprint):
            pass
        
        ParentBlueprint.base_path = parent_base_path
        ParentBlueprint.access_policy = generate_random_access_policy()
        
        # Create child Endpoint
        class ChildEndpoint(Endpoint):
            pass
        
        ChildEndpoint.base_leaf = child_leaf
        ChildEndpoint.methods = child_methods
        ChildEndpoint.version = child_version
        ChildEndpoint.tags = child_tags
        
        # Attach child to parent
        descriptor = ParentBlueprint.attach_child(ChildEndpoint)
        registry.register(descriptor)

        # Verify descriptor was emitted to registry
        descriptors = registry.collect()
        
        if len(descriptors) != 1:
            errmsg = (
                f"Iteration {iteration}: Expected 1 descriptor in registry, "
                f"got {len(descriptors)}"
            )
            raise AssertionError(errmsg)
        
        reg_desc = descriptors[0]
        
        # Verify path is correctly composed
        expected_path = f"{parent_base_path.rstrip('/')}/{child_leaf}"
        if reg_desc.path != expected_path:
            errmsg = (
                f"Iteration {iteration}: Descriptor path should be composed correctly. "
                f"expected={expected_path}, got={reg_desc.path}"
            )
            raise AssertionError(errmsg)
        
        # Verify methods are preserved from child
        if reg_desc.methods != child_methods:
            errmsg = (
                f"Iteration {iteration}: Descriptor methods should match child. "
                f"expected={child_methods}, got={reg_desc.methods}"
            )
            raise AssertionError(errmsg)
    
    return


def test_property_descriptor_emission_merged_metadata():
    """
        Property 9: Descriptor Emission (merged metadata)
        
        *For any* `attach_at` call, the emitted descriptor SHALL contain
        merged metadata from both the blueprint class and the decorator kwargs.
        
        **Feature: blueprint-endpoints, Property 9: Descriptor Emission**
        **Validates: Requirements 5.1, 5.6**
    """
    registry = EndpointRegistry()
    registry = EndpointRegistry()
    
    # Run 100 iterations with different random configurations
    for iteration in range(100):
        registry = EndpointRegistry()
        
        # Generate random parent constraints
        parent_roles = [f"parent_role_{generate_random_string(3, 5)}"]
        parent_scopes = [f"parent_scope_{generate_random_string(3, 5)}"]
        parent_policy = AccessPolicy(
            roles=parent_roles,
            scopes=parent_scopes,
            require_auth=True
        )
        parent_rate_limit = RateLimit(
            requests=random.randint(50, 200),
            window=60
        )
        
        # Create a Blueprint subclass with constraints
        class TestBlueprint(Blueprint):
            pass
        
        TestBlueprint.base_path = generate_random_base_path()
        TestBlueprint.access_policy = parent_policy
        TestBlueprint.rate_limit = parent_rate_limit
        
        # Generate random leaf
        leaf = generate_random_leaf()
        
        # Create and decorate a handler (no explicit constraints)
        def handler():
            pass
        
        TestBlueprint.attach_at(leaf=leaf)(handler)
        registry.collect_from(handler)
        
        # Verify descriptor was emitted with merged metadata
        descriptors = registry.collect()
        desc = descriptors[0]
        
        # Verify access_policy is inherited from parent
        if desc.constraints.access_policy is None:
            errmsg = (
                f"Iteration {iteration}: Descriptor should have inherited access_policy"
            )
            raise AssertionError(errmsg)
        
        # Verify parent roles are in merged policy
        for role in parent_roles:
            if role not in desc.constraints.access_policy.roles:
                errmsg = (
                    f"Iteration {iteration}: Parent role '{role}' should be in merged policy. "
                    f"merged_roles={desc.constraints.access_policy.roles}"
                )
                raise AssertionError(errmsg)
        
        # Verify rate_limit is inherited from parent
        if desc.constraints.rate_limit is None:
            errmsg = (
                f"Iteration {iteration}: Descriptor should have inherited rate_limit"
            )
            raise AssertionError(errmsg)
    
    return


# =============================================================================
# Property 11: Conflict Detection and Replace
# Feature: blueprint-endpoints, Property 11: Conflict Detection and Replace
# Validates: Requirements 3.4, 3.5, 6.3, 6.4
# =============================================================================

def test_property_conflict_detection_missing_metadata():
    """
        Property 11: Conflict Detection and Replace (missing metadata)
        
        *For any* `attach_at` call:
        - If mandatory metadata (leaf or path) is missing, EndpointRegistrationError
          SHALL be raised
        
        **Feature: blueprint-endpoints, Property 11: Conflict Detection and Replace**
        **Validates: Requirements 3.4, 3.5, 6.3, 6.4**
    """
    from ccai.webworks.endpoints.exceptions import EndpointRegistrationError
    
    registry = EndpointRegistry()
    
    # Run 100 iterations with different random configurations
    for iteration in range(100):
        registry = EndpointRegistry()
        
        # Create a Blueprint subclass
        class TestBlueprint(Blueprint):
            pass
        
        TestBlueprint.base_path = generate_random_base_path()
        
        # Create a handler
        def handler():
            pass
        
        # Attempt to attach without leaf or path
        try:
            TestBlueprint.attach_at()(handler)
            registry.collect_from(handler)
            errmsg = (
                f"Iteration {iteration}: Expected EndpointRegistrationError "
                f"when leaf and path are both missing"
            )
            raise AssertionError(errmsg)
        except EndpointRegistrationError as e:
            # Verify error contains expected information
            if "leaf" not in str(e).lower() and "path" not in str(e).lower():
                errmsg = (
                    f"Iteration {iteration}: Error message should mention 'leaf' or 'path'. "
                    f"got: {str(e)}"
                )
                raise AssertionError(errmsg)
    
    return


def test_property_conflict_detection_duplicate_registration():
    """
        Property 11: Conflict Detection and Replace (duplicate registration)
        
        *For any* `attach_at` call:
        - If path+method conflicts with existing registration and on_conflict="error",
          EndpointConflictError SHALL be raised
        
        **Feature: blueprint-endpoints, Property 11: Conflict Detection and Replace**
        **Validates: Requirements 3.4, 3.5, 6.3, 6.4**
    """
    from ccai.webworks.endpoints.registry import EndpointConflictError
    
    registry = EndpointRegistry()
    
    # Run 100 iterations with different random configurations
    for iteration in range(100):
        registry = EndpointRegistry()
        
        # Generate random configuration
        base_path = generate_random_base_path()
        leaf = generate_random_leaf()
        methods = random.choice([["GET"], ["POST"], ["PUT"]])
        
        # Create a Blueprint subclass
        class TestBlueprint(Blueprint):
            pass
        
        TestBlueprint.base_path = base_path
        
        # Create first handler and attach
        def handler1():
            pass
        
        TestBlueprint.attach_at(leaf=leaf, methods=methods)(handler1)
        registry.collect_from(handler1)
        
        # Create second handler and attempt to attach at same path+method
        def handler2():
            pass
        
        try:
            TestBlueprint.attach_at(leaf=leaf, methods=methods)(handler2)
            registry.collect_from(handler2)
            errmsg = (
                f"Iteration {iteration}: Expected EndpointConflictError "
                f"when registering duplicate path+method"
            )
            raise AssertionError(errmsg)
        except EndpointConflictError as e:
            # Verify error contains expected information
            expected_path = f"{base_path.rstrip('/')}/{leaf}"
            if expected_path not in str(e):
                errmsg = (
                    f"Iteration {iteration}: Error message should contain path '{expected_path}'. "
                    f"got: {str(e)}"
                )
                raise AssertionError(errmsg)
            
            if methods[0] not in str(e):
                errmsg = (
                    f"Iteration {iteration}: Error message should contain method '{methods[0]}'. "
                    f"got: {str(e)}"
                )
                raise AssertionError(errmsg)
    
    return


def test_property_conflict_detection_replace_behavior():
    """
        Property 11: Conflict Detection and Replace (replace behavior)
        
        *For any* `attach_at` call:
        - If `on_conflict="replace"`, existing registration SHALL be replaced
          without error
        
        **Feature: blueprint-endpoints, Property 11: Conflict Detection and Replace**
        **Validates: Requirements 3.4, 3.5, 6.3, 6.4**
    """
    registry = EndpointRegistry()
    registry = EndpointRegistry()
    
    # Run 100 iterations with different random configurations
    for iteration in range(100):
        registry = EndpointRegistry()
        
        # Generate random configuration
        base_path = generate_random_base_path()
        leaf = generate_random_leaf()
        methods = random.choice([["GET"], ["POST"], ["PUT"]])
        
        # Create a Blueprint subclass
        class TestBlueprint(Blueprint):
            pass
        
        TestBlueprint.base_path = base_path
        
        # Create first handler and attach
        def handler1():
            pass
        
        handler1.__name__ = f"handler1_{iteration}"
        
        TestBlueprint.attach_at(leaf=leaf, methods=methods)(handler1)
        registry.collect_from(handler1)
        
        # Verify first handler is registered
        descriptors = registry.collect()
        if len(descriptors) != 1:
            errmsg = f"Iteration {iteration}: Expected 1 descriptor after first attach"
            raise AssertionError(errmsg)
        
        if descriptors[0].handler is not handler1:
            errmsg = f"Iteration {iteration}: First handler should be registered"
            raise AssertionError(errmsg)
        
        # Create second handler and attach with on_conflict="replace"
        def handler2():
            pass
        
        handler2.__name__ = f"handler2_{iteration}"
        
        # This should NOT raise an error
        TestBlueprint.attach_at(
            leaf=leaf,
            methods=methods,
            on_conflict="replace"
        )(handler2)
        registry.collect_from(handler2)
        
        # Verify second handler replaced first
        descriptors = registry.collect()
        
        if len(descriptors) != 1:
            errmsg = (
                f"Iteration {iteration}: Expected 1 descriptor after replace, "
                f"got {len(descriptors)}"
            )
            raise AssertionError(errmsg)
        
        if descriptors[0].handler is not handler2:
            errmsg = (
                f"Iteration {iteration}: Second handler should have replaced first. "
                f"expected handler2, got {descriptors[0].handler.__name__}"
            )
            raise AssertionError(errmsg)
    
    return


def test_property_conflict_detection_different_methods_allowed():
    """
        Property 11: Conflict Detection and Replace (different methods allowed)
        
        *For any* `attach_at` call:
        - Same path with different methods SHALL NOT conflict
        
        **Feature: blueprint-endpoints, Property 11: Conflict Detection and Replace**
        **Validates: Requirements 3.4, 3.5, 6.3, 6.4**
    """
    registry = EndpointRegistry()
    registry = EndpointRegistry()
    
    # Run 100 iterations with different random configurations
    for iteration in range(100):
        registry = EndpointRegistry()
        
        # Generate random configuration
        base_path = generate_random_base_path()
        leaf = generate_random_leaf()
        
        # Create a Blueprint subclass
        class TestBlueprint(Blueprint):
            pass
        
        TestBlueprint.base_path = base_path
        
        # Create handlers for different methods
        def get_handler():
            pass
        
        def post_handler():
            pass
        
        def put_handler():
            pass
        
        # Attach handlers with different methods at same path
        TestBlueprint.attach_at(leaf=leaf, methods=["GET"])(get_handler)
        registry.collect_from(get_handler)
        TestBlueprint.attach_at(leaf=leaf, methods=["POST"])(post_handler)
        registry.collect_from(post_handler)
        TestBlueprint.attach_at(leaf=leaf, methods=["PUT"])(put_handler)
        registry.collect_from(put_handler)
        
        # Verify all handlers are registered
        descriptors = registry.collect()
        
        if len(descriptors) != 3:
            errmsg = (
                f"Iteration {iteration}: Expected 3 descriptors for different methods, "
                f"got {len(descriptors)}"
            )
            raise AssertionError(errmsg)
        
        # Verify each method is registered
        registered_methods = set()
        for desc in descriptors:
            for method in desc.methods:
                registered_methods.add(method)
        
        expected_methods = {"GET", "POST", "PUT"}
        if registered_methods != expected_methods:
            errmsg = (
                f"Iteration {iteration}: Expected methods {expected_methods}, "
                f"got {registered_methods}"
            )
            raise AssertionError(errmsg)
    
    return


# =============================================================================
# Property 10: Handler Non-Execution During Registration
# Feature: blueprint-endpoints, Property 10: Handler Non-Execution During Registration
# Validates: Requirements 5.4, 5.7
# =============================================================================

def test_property_handler_non_execution_during_decoration():
    """
        Property 10: Handler Non-Execution During Registration
        
        *For any* handler decorated with `attach_at`, the handler SHALL NOT
        be executed during decoration or import; only descriptor generation
        SHALL occur.
        
        This test generates random handlers that track their execution and
        verifies that they are never called during the decoration process.
        
        **Feature: blueprint-endpoints, Property 10: Handler Non-Execution During Registration**
        **Validates: Requirements 5.4, 5.7**
    """
    registry = EndpointRegistry()
    registry = EndpointRegistry()
    
    # Run 100 iterations with different random configurations
    for iteration in range(100):
        registry = EndpointRegistry()
        
        # Generate random configuration
        base_path = generate_random_base_path()
        leaf = generate_random_leaf()
        
        # Create a Blueprint subclass
        class TestBlueprint(Blueprint):
            pass
        
        TestBlueprint.base_path = base_path
        
        # Track whether handler was called
        handler_called = [False]
        call_count = [0]
        
        # Create a handler that tracks its execution
        def tracking_handler():
            handler_called[0] = True
            call_count[0] += 1
            return f"handler_result_{iteration}"
        
        tracking_handler.__name__ = f"tracking_handler_{iteration}"
        
        # Apply the decorator - this should NOT call the handler
        decorated = TestBlueprint.attach_at(leaf=leaf)(tracking_handler)
        registry.collect_from(tracking_handler)
        
        # Verify handler was NOT called during decoration
        if handler_called[0]:
            errmsg = (
                f"Iteration {iteration}: Handler should NOT be called during decoration. "
                f"call_count={call_count[0]}"
            )
            raise AssertionError(errmsg)
        
        if call_count[0] != 0:
            errmsg = (
                f"Iteration {iteration}: Handler call_count should be 0, "
                f"got {call_count[0]}"
            )
            raise AssertionError(errmsg)
        
        # Verify the decorated function is the same as original
        if decorated is not tracking_handler:
            errmsg = (
                f"Iteration {iteration}: Decorated function should be same object"
            )
            raise AssertionError(errmsg)
        
        # Verify descriptor was created
        descriptors = registry.collect()
        if len(descriptors) != 1:
            errmsg = (
                f"Iteration {iteration}: Expected 1 descriptor, got {len(descriptors)}"
            )
            raise AssertionError(errmsg)
        
        # Verify handler reference is stored in descriptor (not called)
        if descriptors[0].handler is not tracking_handler:
            errmsg = (
                f"Iteration {iteration}: Descriptor should store handler reference"
            )
            raise AssertionError(errmsg)
        
        # Verify handler STILL was not called after collecting descriptors
        if handler_called[0]:
            errmsg = (
                f"Iteration {iteration}: Handler should NOT be called during descriptor collection"
            )
            raise AssertionError(errmsg)
    
    return


def test_property_handler_non_execution_with_constraints():
    """
        Property 10: Handler Non-Execution During Registration (with constraints)
        
        *For any* handler decorated with `attach_at` with various constraints,
        the handler SHALL NOT be executed during decoration; constraint
        processing SHALL NOT trigger handler execution.
        
        **Feature: blueprint-endpoints, Property 10: Handler Non-Execution During Registration**
        **Validates: Requirements 5.4, 5.7**
    """
    registry = EndpointRegistry()
    registry = EndpointRegistry()
    
    # Run 100 iterations with different random configurations
    for iteration in range(100):
        registry = EndpointRegistry()
        
        # Generate random configuration
        base_path = generate_random_base_path()
        leaf = generate_random_leaf()
        tags = generate_random_tags()
        access_policy = generate_random_access_policy()
        rate_limit = generate_random_rate_limit()
        
        # Create a Blueprint subclass with constraints
        class TestBlueprint(Blueprint):
            pass
        
        TestBlueprint.base_path = base_path
        TestBlueprint.tags = generate_random_tags()
        TestBlueprint.access_policy = generate_random_access_policy()
        TestBlueprint.rate_limit = generate_random_rate_limit()
        TestBlueprint.merge_tags = random.choice([True, False])
        TestBlueprint.replace_roles = random.choice([True, False])
        TestBlueprint.replace_scopes = random.choice([True, False])
        
        # Track whether handler was called
        handler_called = [False]
        
        # Create a handler that tracks its execution
        def tracking_handler():
            handler_called[0] = True
            return "result"
        
        # Apply the decorator with various constraints
        decorated = TestBlueprint.attach_at(
            leaf=leaf,
            tags=tags,
            access_policy=access_policy,
            rate_limit=rate_limit,
            methods=["GET", "POST"],
            version="v1"
        )(tracking_handler)
        registry.collect_from(tracking_handler)

        # Verify handler was NOT called during decoration
        if handler_called[0]:
            errmsg = (
                f"Iteration {iteration}: Handler should NOT be called during decoration "
                f"even with constraints. base_path={base_path}, leaf={leaf}"
            )
            raise AssertionError(errmsg)
        
        # Verify descriptor was created with merged constraints
        descriptors = registry.collect()
        if len(descriptors) != 1:
            errmsg = (
                f"Iteration {iteration}: Expected 1 descriptor, got {len(descriptors)}"
            )
            raise AssertionError(errmsg)
        
        # Verify handler STILL was not called
        if handler_called[0]:
            errmsg = (
                f"Iteration {iteration}: Handler should NOT be called after descriptor creation"
            )
            raise AssertionError(errmsg)
    
    return


def test_property_handler_non_execution_multiple_handlers():
    """
        Property 10: Handler Non-Execution During Registration (multiple handlers)
        
        *For any* Blueprint with multiple handlers decorated with `attach_at`,
        NONE of the handlers SHALL be executed during decoration.
        
        **Feature: blueprint-endpoints, Property 10: Handler Non-Execution During Registration**
        **Validates: Requirements 5.4, 5.7**
    """
    registry = EndpointRegistry()
    registry = EndpointRegistry()
    
    # Run 100 iterations with different random configurations
    for iteration in range(100):
        registry = EndpointRegistry()
        
        # Generate random configuration
        base_path = generate_random_base_path()
        num_handlers = random.randint(2, 5)
        
        # Create a Blueprint subclass
        class TestBlueprint(Blueprint):
            pass
        
        TestBlueprint.base_path = base_path
        
        # Track which handlers were called
        handlers_called = {i: False for i in range(num_handlers)}
        
        # Create and decorate multiple handlers
        for i in range(num_handlers):
            leaf = f"endpoint_{i}_{generate_random_string(3, 6)}"
            
            # Create a handler that tracks its execution
            def make_tracking_handler(idx):
                def tracking_handler():
                    handlers_called[idx] = True
                    return f"result_{idx}"
                tracking_handler.__name__ = f"handler_{idx}"
                return tracking_handler
            
            handler = make_tracking_handler(i)
            TestBlueprint.attach_at(leaf=leaf)(handler)
            registry.collect_from(handler)
        
        # Verify NO handlers were called during decoration
        for i, called in handlers_called.items():
            if called:
                errmsg = (
                    f"Iteration {iteration}: Handler {i} should NOT be called during decoration"
                )
                raise AssertionError(errmsg)
        
        # Verify all descriptors were created
        descriptors = registry.collect()
        if len(descriptors) != num_handlers:
            errmsg = (
                f"Iteration {iteration}: Expected {num_handlers} descriptors, "
                f"got {len(descriptors)}"
            )
            raise AssertionError(errmsg)
        
        # Verify handlers STILL were not called after collecting descriptors
        for i, called in handlers_called.items():
            if called:
                errmsg = (
                    f"Iteration {iteration}: Handler {i} should NOT be called "
                    f"after descriptor collection"
                )
                raise AssertionError(errmsg)
    
    return


def test_property_handler_non_execution_during_register():
    """
        Property 10: Handler Non-Execution During Registration (register method)
        
        *For any* Blueprint, calling register() SHALL NOT execute any handlers;
        it SHALL only collect and return descriptors.
        
        **Feature: blueprint-endpoints, Property 10: Handler Non-Execution During Registration**
        **Validates: Requirements 5.4, 5.7**
    """
    registry = EndpointRegistry()
    
    # Run 100 iterations with different random configurations
    for iteration in range(100):
        registry = EndpointRegistry()
        
        # Generate random configuration
        base_path = generate_random_base_path()
        num_handlers = random.randint(1, 4)
        
        # Create a Blueprint subclass
        class TestBlueprint(Blueprint):
            pass
        
        TestBlueprint.base_path = base_path
        
        # Track which handlers were called
        handlers_called = {i: False for i in range(num_handlers)}
        
        # Create and decorate multiple handlers
        for i in range(num_handlers):
            leaf = f"endpoint_{i}_{generate_random_string(3, 6)}"
            
            def make_tracking_handler(idx):
                def tracking_handler():
                    handlers_called[idx] = True
                    return f"result_{idx}"
                tracking_handler.__name__ = f"handler_{idx}"
                return tracking_handler
            
            handler = make_tracking_handler(i)
            TestBlueprint.attach_at(leaf=leaf)(handler)
            registry.collect_from(handler)
        
        # Call register() - this should NOT call any handlers
        result = TestBlueprint.register()
        
        # Verify NO handlers were called during register()
        for i, called in handlers_called.items():
            if called:
                errmsg = (
                    f"Iteration {iteration}: Handler {i} should NOT be called during register()"
                )
                raise AssertionError(errmsg)
        
        # Call register() again (idempotency) - still should not call handlers
        result2 = TestBlueprint.register()
        
        # Verify handlers STILL were not called
        for i, called in handlers_called.items():
            if called:
                errmsg = (
                    f"Iteration {iteration}: Handler {i} should NOT be called "
                    f"during repeated register() calls"
                )
                raise AssertionError(errmsg)
    
    return


def test_property_handler_non_execution_with_router():
    """
        Property 10: Handler Non-Execution During Registration (with router)
        
        *For any* Blueprint registered with a router, handlers SHALL NOT be
        executed during router registration; only descriptor references
        SHALL be passed to the router.
        
        **Feature: blueprint-endpoints, Property 10: Handler Non-Execution During Registration**
        **Validates: Requirements 5.4, 5.7**
    """
    registry = EndpointRegistry()
    
    # Run 100 iterations with different random configurations
    for iteration in range(100):
        registry = EndpointRegistry()
        
        # Generate random configuration
        base_path = generate_random_base_path()
        num_handlers = random.randint(1, 3)
        
        # Create a Blueprint subclass
        class TestBlueprint(Blueprint):
            pass
        
        TestBlueprint.base_path = base_path
        
        # Track which handlers were called
        handlers_called = {i: False for i in range(num_handlers)}
        
        # Create and decorate multiple handlers
        for i in range(num_handlers):
            leaf = f"endpoint_{i}_{generate_random_string(3, 6)}"
            
            def make_tracking_handler(idx):
                def tracking_handler():
                    handlers_called[idx] = True
                    return f"result_{idx}"
                tracking_handler.__name__ = f"handler_{idx}"
                return tracking_handler
            
            handler = make_tracking_handler(i)
            TestBlueprint.attach_at(leaf=leaf)(handler)
            registry.collect_from(handler)
        
        # Create a mock router
        added_descriptors = []
        
        class MockRouter:
            def add_endpoint(self, descriptor):
                added_descriptors.append(descriptor)
        
        router = MockRouter()
        
        # Call register() with router - this should NOT call any handlers
        result = TestBlueprint.register(router=router)
        
        # Verify NO handlers were called during register() with router
        for i, called in handlers_called.items():
            if called:
                errmsg = (
                    f"Iteration {iteration}: Handler {i} should NOT be called "
                    f"during register() with router"
                )
                raise AssertionError(errmsg)
        
        # Verify descriptors were added to router
        if len(added_descriptors) != len(result):
            errmsg = (
                f"Iteration {iteration}: Router should receive all descriptors. "
                f"expected={len(result)}, got={len(added_descriptors)}"
            )
            raise AssertionError(errmsg)
    
    return
