"""
    .. module:: test_middlewareregistry_properties
        :platform: Darwin, Linux, Unix, Windows
        :synopsis: Property-based tests for MiddlewareRegistry scoped composition and querying.

    .. moduleauthor:: Code Craft AI LLC

    This module contains property-based tests for the MiddlewareRegistry,
    validating scoped pipeline composition order (Property 9), query by
    scope correctness (Property 10), registry grouped listing (Property 20),
    and effective pipeline export matching composition (Property 21).
"""

__author__ = "Code Craft AI LLC"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []

from typing import Callable, Dict

import ccai.testbase as testbase

from ccai.testbase.properties import given
from ccai.testbase.properties import strategies as st
from ccai.testbase.properties.strategies import composite

from ccai.webworks.routing.middlewareregistry import MiddlewareRegistry
from ccai.webworks.routing.request import Request


# =============================================================================
# Test Helpers
# =============================================================================

class MockResponse:
    """
        Minimal Response implementation for property tests.
    """

    def __init__(self, status_code: int = 200, body: bytes = b"", headers: Dict[str, str] = None):
        self._status_code = status_code
        self._body = body
        self._headers = headers or {}
        return

    @property
    def status_code(self) -> int:
        return self._status_code

    @property
    def body(self) -> bytes:
        return self._body

    @property
    def headers(self) -> Dict[str, str]:
        return self._headers


class ScopeTrackingMiddleware:
    """
        Middleware that records its name and scope into request.path_params["order"].
    """

    def __init__(self, mw_name: str):
        self.name = mw_name
        return

    def __call__(self, request: Request, call_next: Callable) -> MockResponse:
        if "order" not in request.path_params:
            request.path_params["order"] = []
        request.path_params["order"].append(self.name)
        return call_next(request)


# Strategy: unique middleware name strings (lowercase alpha, 3-8 chars)
name_strategy = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyz",
    min_size=3,
    max_size=8,
)


@composite
def unique_name_list(draw, min_size=1, max_size=4):
    """
        Generate a list of unique middleware name strings.
    """
    size = draw(st.integers(min_size, max_size))
    names = []
    for i in range(size):
        name = draw(name_strategy)
        # Ensure uniqueness by appending index
        names.append(f"{name}{i}")
    return names


@composite
def three_scope_name_lists(draw):
    """
        Generate three disjoint lists of unique names for global, blueprint,
        and route scopes.
    """
    global_count = draw(st.integers(1, 3))
    bp_count = draw(st.integers(1, 3))
    route_count = draw(st.integers(1, 3))

    # Use index-based naming to guarantee uniqueness and disjointness
    global_names = [f"g_mw{i}" for i in range(global_count)]
    bp_names = [f"b_mw{i}" for i in range(bp_count)]
    route_names = [f"r_mw{i}" for i in range(route_count)]

    return global_names, bp_names, route_names


# =============================================================================
# Property 9: Scoped pipeline composition order
# Feature: middleware-pipeline, Property 9
# Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.6, 4.7
# =============================================================================

@given(
    scope_names=three_scope_name_lists(),
    constraints={"max_examples": 5},
)
def test_property_scoped_pipeline_composition_order(scope_names):
    """
        Property 9: Scoped pipeline composition order.

        For any set of middleware registered at global, blueprint, and route
        scopes, composing the effective pipeline should produce a chain where
        all global middleware appear first, then all blueprint middleware,
        then all route middleware, and the total count equals the sum of
        middleware at each applicable scope.

        **Feature: middleware-pipeline, Property 9: Scoped pipeline composition order**
        **Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.6, 4.7**
    """
    global_names, bp_names, route_names = scope_names

    registry = MiddlewareRegistry()

    # Register global middleware
    for name in global_names:
        mw = ScopeTrackingMiddleware(name)
        registry.register(mw, name=name, scope="global")

    # Register blueprint middleware
    bp_key = "test_blueprint"
    for name in bp_names:
        mw = ScopeTrackingMiddleware(name)
        registry.register(mw, name=name, scope="blueprint", scope_key=bp_key)

    # Register route middleware
    route_key = "/test/route"
    for name in route_names:
        mw = ScopeTrackingMiddleware(name)
        registry.register(mw, name=name, scope="route", scope_key=route_key)

    # Compose the effective pipeline
    pipeline = registry.compose_pipeline(
        blueprint_name=bp_key,
        route_path=route_key,
    )

    pipeline_names = pipeline.get_names()

    # Total count should equal sum of all scopes
    expected_total = len(global_names) + len(bp_names) + len(route_names)
    testbase.assert_equal(len(pipeline_names), expected_total,
        f"Pipeline should have {expected_total} middleware "
        f"({len(global_names)} global + {len(bp_names)} blueprint + "
        f"{len(route_names)} route), but had {len(pipeline_names)}. "
        f"Names: {pipeline_names}.")

    # Global middleware should appear first
    global_section = pipeline_names[:len(global_names)]
    testbase.assert_equal(set(global_section), set(global_names),
        f"First {len(global_names)} entries should be global middleware. "
        f"Expected {global_names}, got {global_section}.")

    # Blueprint middleware should appear second
    bp_start = len(global_names)
    bp_end = bp_start + len(bp_names)
    bp_section = pipeline_names[bp_start:bp_end]
    testbase.assert_equal(set(bp_section), set(bp_names),
        f"Blueprint middleware should follow global. "
        f"Expected {bp_names}, got {bp_section}.")

    # Route middleware should appear last
    route_section = pipeline_names[bp_end:]
    testbase.assert_equal(set(route_section), set(route_names),
        f"Route middleware should follow blueprint. "
        f"Expected {route_names}, got {route_section}.")


@given(
    scope_names=three_scope_name_lists(),
    constraints={"max_examples": 5},
)
def test_property_scoped_composition_global_only_when_no_blueprint_or_route(scope_names):
    """
        Property 9 (global-only): When no blueprint or route is specified,
        the composed pipeline should contain only global middleware.

        **Feature: middleware-pipeline, Property 9: Scoped pipeline composition order**
        **Validates: Requirements 4.1, 4.4**
    """
    global_names, bp_names, route_names = scope_names

    registry = MiddlewareRegistry()

    for name in global_names:
        mw = ScopeTrackingMiddleware(name)
        registry.register(mw, name=name, scope="global")

    bp_key = "test_blueprint"
    for name in bp_names:
        mw = ScopeTrackingMiddleware(name)
        registry.register(mw, name=name, scope="blueprint", scope_key=bp_key)

    route_key = "/test/route"
    for name in route_names:
        mw = ScopeTrackingMiddleware(name)
        registry.register(mw, name=name, scope="route", scope_key=route_key)

    # Compose with no blueprint or route
    pipeline = registry.compose_pipeline()
    pipeline_names = pipeline.get_names()

    testbase.assert_equal(len(pipeline_names), len(global_names),
        f"Pipeline with no blueprint/route should have only global middleware "
        f"({len(global_names)}), but had {len(pipeline_names)}. "
        f"Names: {pipeline_names}.")

    testbase.assert_equal(set(pipeline_names), set(global_names),
        f"Pipeline should contain only global middleware names. "
        f"Expected {global_names}, got {pipeline_names}.")


@given(
    scope_names=three_scope_name_lists(),
    constraints={"max_examples": 5},
)
def test_property_scoped_composition_route_middleware_additive(scope_names):
    """
        Property 9 (additive): Route-level middleware executes in addition
        to (not replacing) higher-scope middleware.

        **Feature: middleware-pipeline, Property 9: Scoped pipeline composition order**
        **Validates: Requirements 4.7**
    """
    global_names, bp_names, route_names = scope_names

    registry = MiddlewareRegistry()

    for name in global_names:
        mw = ScopeTrackingMiddleware(name)
        registry.register(mw, name=name, scope="global")

    bp_key = "test_blueprint"
    for name in bp_names:
        mw = ScopeTrackingMiddleware(name)
        registry.register(mw, name=name, scope="blueprint", scope_key=bp_key)

    route_key = "/test/route"
    for name in route_names:
        mw = ScopeTrackingMiddleware(name)
        registry.register(mw, name=name, scope="route", scope_key=route_key)

    pipeline = registry.compose_pipeline(
        blueprint_name=bp_key,
        route_path=route_key,
    )
    pipeline_names = pipeline.get_names()

    # All global names must be present
    for gname in global_names:
        testbase.assert_true(gname in pipeline_names,
            f"Global middleware '{gname}' should be present in composed pipeline. "
            f"Pipeline: {pipeline_names}.")

    # All blueprint names must be present
    for bname in bp_names:
        testbase.assert_true(bname in pipeline_names,
            f"Blueprint middleware '{bname}' should be present in composed pipeline. "
            f"Pipeline: {pipeline_names}.")

    # All route names must be present
    for rname in route_names:
        testbase.assert_true(rname in pipeline_names,
            f"Route middleware '{rname}' should be present in composed pipeline. "
            f"Pipeline: {pipeline_names}.")



# =============================================================================
# Property 10: Query by scope returns correct middleware
# Feature: middleware-pipeline, Property 10
# Validates: Requirements 4.5
# =============================================================================

@given(
    scope_names=three_scope_name_lists(),
    constraints={"max_examples": 5},
)
def test_property_query_by_scope_returns_correct_middleware(scope_names):
    """
        Property 10: Query by scope returns correct middleware.

        For any set of middleware registered at various scopes, querying
        the registry by a specific scope and scope key should return
        exactly the middleware registered at that scope and key, and no others.

        **Feature: middleware-pipeline, Property 10: Query by scope returns correct middleware**
        **Validates: Requirements 4.5**
    """
    global_names, bp_names, route_names = scope_names

    registry = MiddlewareRegistry()

    for name in global_names:
        mw = ScopeTrackingMiddleware(name)
        registry.register(mw, name=name, scope="global")

    bp_key = "api_v1"
    for name in bp_names:
        mw = ScopeTrackingMiddleware(name)
        registry.register(mw, name=name, scope="blueprint", scope_key=bp_key)

    route_key = "/api/users"
    for name in route_names:
        mw = ScopeTrackingMiddleware(name)
        registry.register(mw, name=name, scope="route", scope_key=route_key)

    # Query global scope
    global_entries = registry.get_middleware_by_scope("global")
    global_entry_names = [e.name for e in global_entries]
    testbase.assert_equal(set(global_entry_names), set(global_names),
        f"Global scope query should return exactly global middleware. "
        f"Expected {global_names}, got {global_entry_names}.")

    # Query blueprint scope
    bp_entries = registry.get_middleware_by_scope("blueprint", scope_key=bp_key)
    bp_entry_names = [e.name for e in bp_entries]
    testbase.assert_equal(set(bp_entry_names), set(bp_names),
        f"Blueprint scope query should return exactly blueprint middleware. "
        f"Expected {bp_names}, got {bp_entry_names}.")

    # Query route scope
    route_entries = registry.get_middleware_by_scope("route", scope_key=route_key)
    route_entry_names = [e.name for e in route_entries]
    testbase.assert_equal(set(route_entry_names), set(route_names),
        f"Route scope query should return exactly route middleware. "
        f"Expected {route_names}, got {route_entry_names}.")


@given(
    scope_names=three_scope_name_lists(),
    constraints={"max_examples": 5},
)
def test_property_query_by_scope_returns_empty_for_unknown_key(scope_names):
    """
        Property 10 (unknown key): Querying a scope with an unknown key
        should return an empty list.

        **Feature: middleware-pipeline, Property 10: Query by scope returns correct middleware**
        **Validates: Requirements 4.5**
    """
    global_names, bp_names, route_names = scope_names

    registry = MiddlewareRegistry()

    bp_key = "api_v1"
    for name in bp_names:
        mw = ScopeTrackingMiddleware(name)
        registry.register(mw, name=name, scope="blueprint", scope_key=bp_key)

    route_key = "/api/users"
    for name in route_names:
        mw = ScopeTrackingMiddleware(name)
        registry.register(mw, name=name, scope="route", scope_key=route_key)

    # Query with unknown blueprint key
    unknown_bp = registry.get_middleware_by_scope("blueprint", scope_key="nonexistent")
    testbase.assert_equal(len(unknown_bp), 0,
        f"Query for unknown blueprint key should return empty list, "
        f"got {len(unknown_bp)} entries.")

    # Query with unknown route key
    unknown_route = registry.get_middleware_by_scope("route", scope_key="/nonexistent")
    testbase.assert_equal(len(unknown_route), 0,
        f"Query for unknown route key should return empty list, "
        f"got {len(unknown_route)} entries.")


@given(
    scope_names=three_scope_name_lists(),
    constraints={"max_examples": 5},
)
def test_property_query_by_scope_count_matches_registered(scope_names):
    """
        Property 10 (count): The number of entries returned by querying
        each scope should equal the number registered at that scope.

        **Feature: middleware-pipeline, Property 10: Query by scope returns correct middleware**
        **Validates: Requirements 4.5**
    """
    global_names, bp_names, route_names = scope_names

    registry = MiddlewareRegistry()

    for name in global_names:
        mw = ScopeTrackingMiddleware(name)
        registry.register(mw, name=name, scope="global")

    bp_key = "admin"
    for name in bp_names:
        mw = ScopeTrackingMiddleware(name)
        registry.register(mw, name=name, scope="blueprint", scope_key=bp_key)

    route_key = "/admin/dashboard"
    for name in route_names:
        mw = ScopeTrackingMiddleware(name)
        registry.register(mw, name=name, scope="route", scope_key=route_key)

    global_count = len(registry.get_middleware_by_scope("global"))
    testbase.assert_equal(global_count, len(global_names),
        f"Global scope should have {len(global_names)} entries, got {global_count}.")

    bp_count = len(registry.get_middleware_by_scope("blueprint", scope_key=bp_key))
    testbase.assert_equal(bp_count, len(bp_names),
        f"Blueprint scope should have {len(bp_names)} entries, got {bp_count}.")

    route_count = len(registry.get_middleware_by_scope("route", scope_key=route_key))
    testbase.assert_equal(route_count, len(route_names),
        f"Route scope should have {len(route_names)} entries, got {route_count}.")



# =============================================================================
# Property 20: Registry grouped listing partitions by scope
# Feature: middleware-pipeline, Property 20
# Validates: Requirements 12.4
# =============================================================================

@given(
    scope_names=three_scope_name_lists(),
    constraints={"max_examples": 5},
)
def test_property_registry_grouped_listing_partitions_by_scope(scope_names):
    """
        Property 20: Registry grouped listing partitions by scope.

        For any set of middleware registered at various scopes, the
        list_by_scope() method should return a dictionary where each scope
        key maps to exactly the middleware registered at that scope, and
        the union of all groups equals the full set of registered middleware.

        **Feature: middleware-pipeline, Property 20: Registry grouped listing partitions by scope**
        **Validates: Requirements 12.4**
    """
    global_names, bp_names, route_names = scope_names

    registry = MiddlewareRegistry()

    for name in global_names:
        mw = ScopeTrackingMiddleware(name)
        registry.register(mw, name=name, scope="global")

    bp_key = "api_v1"
    for name in bp_names:
        mw = ScopeTrackingMiddleware(name)
        registry.register(mw, name=name, scope="blueprint", scope_key=bp_key)

    route_key = "/api/users"
    for name in route_names:
        mw = ScopeTrackingMiddleware(name)
        registry.register(mw, name=name, scope="route", scope_key=route_key)

    grouped = registry.list_by_scope()

    # Global group should contain exactly global middleware
    global_group = grouped.get("global", [])
    global_group_names = [e.name for e in global_group]
    testbase.assert_equal(set(global_group_names), set(global_names),
        f"Global group should contain {global_names}, got {global_group_names}.")

    # Blueprint group should contain exactly blueprint middleware
    bp_group_key = f"blueprint:{bp_key}"
    bp_group = grouped.get(bp_group_key, [])
    bp_group_names = [e.name for e in bp_group]
    testbase.assert_equal(set(bp_group_names), set(bp_names),
        f"Blueprint group should contain {bp_names}, got {bp_group_names}.")

    # Route group should contain exactly route middleware
    route_group_key = f"route:{route_key}"
    route_group = grouped.get(route_group_key, [])
    route_group_names = [e.name for e in route_group]
    testbase.assert_equal(set(route_group_names), set(route_names),
        f"Route group should contain {route_names}, got {route_group_names}.")

    # Union of all groups should equal the full set
    all_names_from_groups = set()
    for entries in grouped.values():
        for entry in entries:
            all_names_from_groups.add(entry.name)

    all_registered = set(global_names) | set(bp_names) | set(route_names)
    testbase.assert_equal(all_names_from_groups, all_registered,
        f"Union of all groups should equal all registered middleware. "
        f"Groups: {all_names_from_groups}, registered: {all_registered}.")



# =============================================================================
# Property 21: Effective pipeline export matches composition
# Feature: middleware-pipeline, Property 21
# Validates: Requirements 12.5
# =============================================================================

@given(
    scope_names=three_scope_name_lists(),
    constraints={"max_examples": 5},
)
def test_property_export_effective_pipeline_matches_composition(scope_names):
    """
        Property 21: Effective pipeline export matches composition.

        For any route path and optional blueprint name, the list of names
        returned by export_effective_pipeline() should equal the list of
        names from compose_pipeline().get_names().

        **Feature: middleware-pipeline, Property 21: Effective pipeline export matches composition**
        **Validates: Requirements 12.5**
    """
    global_names, bp_names, route_names = scope_names

    registry = MiddlewareRegistry()

    for name in global_names:
        mw = ScopeTrackingMiddleware(name)
        registry.register(mw, name=name, scope="global")

    bp_key = "api_v1"
    for name in bp_names:
        mw = ScopeTrackingMiddleware(name)
        registry.register(mw, name=name, scope="blueprint", scope_key=bp_key)

    route_key = "/api/users"
    for name in route_names:
        mw = ScopeTrackingMiddleware(name)
        registry.register(mw, name=name, scope="route", scope_key=route_key)

    # Get names via export_effective_pipeline
    exported_names = registry.export_effective_pipeline(
        route_path=route_key,
        blueprint_name=bp_key,
    )

    # Get names via compose_pipeline().get_names()
    composed_names = registry.compose_pipeline(
        blueprint_name=bp_key,
        route_path=route_key,
    ).get_names()

    testbase.assert_equal(exported_names, composed_names,
        f"export_effective_pipeline() should match compose_pipeline().get_names(). "
        f"Exported: {exported_names}, composed: {composed_names}.")


@given(
    scope_names=three_scope_name_lists(),
    constraints={"max_examples": 5},
)
def test_property_export_effective_pipeline_global_only(scope_names):
    """
        Property 21 (global-only): When exporting with no matching blueprint
        or route, the export should contain only global middleware names.

        **Feature: middleware-pipeline, Property 21: Effective pipeline export matches composition**
        **Validates: Requirements 12.5**
    """
    global_names, bp_names, route_names = scope_names

    registry = MiddlewareRegistry()

    for name in global_names:
        mw = ScopeTrackingMiddleware(name)
        registry.register(mw, name=name, scope="global")

    bp_key = "api_v1"
    for name in bp_names:
        mw = ScopeTrackingMiddleware(name)
        registry.register(mw, name=name, scope="blueprint", scope_key=bp_key)

    # Export with a route that has no registered middleware
    exported_names = registry.export_effective_pipeline(
        route_path="/nonexistent",
        blueprint_name=None,
    )

    testbase.assert_equal(len(exported_names), len(global_names),
        f"Export for unknown route should have only global middleware "
        f"({len(global_names)}), got {len(exported_names)}. "
        f"Names: {exported_names}.")


if __name__ == "__main__":
    from ccai.testbase.entrypoints import generic_test_entrypoint
    generic_test_entrypoint()
