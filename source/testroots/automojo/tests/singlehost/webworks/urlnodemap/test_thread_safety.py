"""
    Tests for thread safety and frozen immutability of the URL Node Map.
    
    This module contains unit tests for the freeze() method, frozen state
    checks on all modification operations, and RLock-based thread safety
    of the URLNodeMap and URLNode classes.
"""

from automojo.webworks.urlnodemap.urlnodemap import URLNodeMap
from automojo.webworks.urlnodemap.exceptions import FrozenTreeError


# =============================================================================
# Unit Tests for freeze() Method
# =============================================================================

def test_freeze_sets_frozen_state():
    """
        Test that freeze() sets the frozen property to True.
        
        Validates: Requirements 8.3
    """
    node_map = URLNodeMap()

    if node_map.frozen is True:
        errmsg = "Expected node map to start unfrozen"
        raise AssertionError(errmsg)

    node_map.freeze()

    if node_map.frozen is not True:
        errmsg = "Expected node map to be frozen after freeze()"
        raise AssertionError(errmsg)

    return


def test_freeze_is_idempotent():
    """
        Test that calling freeze() multiple times does not raise.
        
        Validates: Requirements 8.3
    """
    node_map = URLNodeMap()
    node_map.freeze()
    node_map.freeze()

    if node_map.frozen is not True:
        errmsg = "Expected node map to remain frozen"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for Frozen State Checks on URLNodeMap
# =============================================================================

def test_frozen_get_or_create_existing_node_succeeds():
    """
        Test that get_or_create_node returns an existing node on a frozen map.
        
        Validates: Requirements 8.5
    """
    node_map = URLNodeMap()
    node_map.get_or_create_node("/api/v1")
    node_map.freeze()

    # Retrieving an existing node should not raise
    result = node_map.get_or_create_node("/api/v1")

    if result.path != "/api/v1":
        errmsg = f"Expected path '/api/v1', got '{result.path}'"
        raise AssertionError(errmsg)

    return


def test_frozen_get_or_create_new_node_raises():
    """
        Test that get_or_create_node raises FrozenTreeError for new paths
        on a frozen map.
        
        Validates: Requirements 8.4
    """
    node_map = URLNodeMap()
    node_map.freeze()

    try:
        node_map.get_or_create_node("/api/v1")
        errmsg = "Expected FrozenTreeError to be raised"
        raise AssertionError(errmsg)
    except FrozenTreeError:
        pass

    return


def test_frozen_remove_node_raises():
    """
        Test that remove_node raises FrozenTreeError on a frozen map.
        
        Validates: Requirements 8.4
    """
    node_map = URLNodeMap()
    node_map.get_or_create_node("/api")
    node_map.freeze()

    try:
        node_map.remove_node("/api")
        errmsg = "Expected FrozenTreeError to be raised"
        raise AssertionError(errmsg)
    except FrozenTreeError:
        pass

    # Verify the node still exists
    if not node_map.has_node("/api"):
        errmsg = "Expected node to still exist after failed removal"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for Frozen State Checks on URLNode
# =============================================================================

def test_frozen_set_metadata_raises():
    """
        Test that set_metadata raises FrozenTreeError on a frozen map.
        
        Validates: Requirements 8.4
    """
    node_map = URLNodeMap()
    node = node_map.get_or_create_node("/api")
    node_map.freeze()

    try:
        node.set_metadata("tags", ["admin"])
        errmsg = "Expected FrozenTreeError to be raised"
        raise AssertionError(errmsg)
    except FrozenTreeError:
        pass

    # Verify metadata was not modified
    if node.get_metadata("tags") is not None:
        errmsg = "Expected metadata to remain unchanged after failed set"
        raise AssertionError(errmsg)

    return


def test_frozen_attach_handler_raises():
    """
        Test that attach_handler raises FrozenTreeError on a frozen map.
        
        Validates: Requirements 8.4
    """
    node_map = URLNodeMap()
    node = node_map.get_or_create_node("/api")
    node_map.freeze()

    def dummy_handler():
        pass

    try:
        node.attach_handler("GET", dummy_handler)
        errmsg = "Expected FrozenTreeError to be raised"
        raise AssertionError(errmsg)
    except FrozenTreeError:
        pass

    # Verify handler was not attached
    if node.get_handler("GET") is not None:
        errmsg = "Expected handler to remain unset after failed attach"
        raise AssertionError(errmsg)

    return


def test_frozen_add_child_raises():
    """
        Test that add_child raises FrozenTreeError on a frozen map.
        
        Validates: Requirements 8.4
    """
    node_map = URLNodeMap()
    node = node_map.get_or_create_node("/api")
    node_map.freeze()

    try:
        node.add_child("v1")
        errmsg = "Expected FrozenTreeError to be raised"
        raise AssertionError(errmsg)
    except FrozenTreeError:
        pass

    # Verify child was not added
    if "v1" in node.children:
        errmsg = "Expected child to not be added after failed add_child"
        raise AssertionError(errmsg)

    return


def test_frozen_root_set_metadata_raises():
    """
        Test that set_metadata on the root node raises FrozenTreeError.
        
        Validates: Requirements 8.4
    """
    node_map = URLNodeMap()
    node_map.freeze()

    try:
        node_map.root.set_metadata("version", "1.0")
        errmsg = "Expected FrozenTreeError to be raised"
        raise AssertionError(errmsg)
    except FrozenTreeError:
        pass

    return


def test_frozen_root_add_child_raises():
    """
        Test that add_child on the root node raises FrozenTreeError.
        
        Validates: Requirements 8.4
    """
    node_map = URLNodeMap()
    node_map.freeze()

    try:
        node_map.root.add_child("api")
        errmsg = "Expected FrozenTreeError to be raised"
        raise AssertionError(errmsg)
    except FrozenTreeError:
        pass

    return


def test_frozen_deep_node_set_metadata_raises():
    """
        Test that set_metadata on a deeply nested node raises FrozenTreeError.
        
        Validates: Requirements 8.4
    """
    node_map = URLNodeMap()
    deep_node = node_map.get_or_create_node("/api/v1/users/profile")
    node_map.freeze()

    try:
        deep_node.set_metadata("rate_limit", 100)
        errmsg = "Expected FrozenTreeError to be raised"
        raise AssertionError(errmsg)
    except FrozenTreeError:
        pass

    return


def test_frozen_deep_node_attach_handler_raises():
    """
        Test that attach_handler on a deeply nested node raises FrozenTreeError.
        
        Validates: Requirements 8.4
    """
    node_map = URLNodeMap()
    deep_node = node_map.get_or_create_node("/api/v1/users")
    node_map.freeze()

    def handler():
        pass

    try:
        deep_node.attach_handler("POST", handler)
        errmsg = "Expected FrozenTreeError to be raised"
        raise AssertionError(errmsg)
    except FrozenTreeError:
        pass

    return


# =============================================================================
# Unit Tests for Read Operations on Frozen Map
# =============================================================================

def test_frozen_read_operations_succeed():
    """
        Test that read operations work on a frozen map.
        
        Validates: Requirements 8.1, 8.5
    """
    node_map = URLNodeMap()
    api = node_map.get_or_create_node("/api")
    api.set_metadata("tags", ["public"])

    def get_handler():
        pass

    api.attach_handler("GET", get_handler)
    node_map.freeze()

    # All read operations should succeed
    if not node_map.has_node("/api"):
        errmsg = "Expected has_node to work on frozen map"
        raise AssertionError(errmsg)

    node = node_map.get_node("/api")
    if node is not api:
        errmsg = "Expected get_node to work on frozen map"
        raise AssertionError(errmsg)

    if node.get_metadata("tags") != ["public"]:
        errmsg = "Expected get_metadata to work on frozen map"
        raise AssertionError(errmsg)

    if node.get_handler("GET") is not get_handler:
        errmsg = "Expected get_handler to work on frozen map"
        raise AssertionError(errmsg)

    if not node.is_leaf:
        errmsg = "Expected is_leaf to work on frozen map"
        raise AssertionError(errmsg)

    return


def test_frozen_traversal_succeeds():
    """
        Test that tree traversal works on a frozen map.
        
        Validates: Requirements 8.1, 8.5
    """
    node_map = URLNodeMap()
    node_map.get_or_create_node("/api/v1")
    node_map.get_or_create_node("/docs")
    node_map.freeze()

    # iterate_nodes should work
    nodes = list(node_map.iterate_nodes())
    if len(nodes) != 4:
        errmsg = f"Expected 4 nodes, got {len(nodes)}"
        raise AssertionError(errmsg)

    return


def test_frozen_export_succeeds():
    """
        Test that export operations work on a frozen map.
        
        Validates: Requirements 8.1, 8.5
    """
    node_map = URLNodeMap()
    api = node_map.get_or_create_node("/api")

    def handler():
        pass

    api.attach_handler("GET", handler)
    node_map.freeze()

    # export_tree should work
    tree = node_map.export_tree()
    if tree is None:
        errmsg = "Expected export_tree to work on frozen map"
        raise AssertionError(errmsg)

    # export_routes should work
    routes = node_map.export_routes()
    if len(routes) != 1:
        errmsg = f"Expected 1 route, got {len(routes)}"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Unit Tests for Modifications Before Freeze
# =============================================================================

def test_modifications_before_freeze_succeed():
    """
        Test that all modification operations work before freezing.
        
        Validates: Requirements 8.2
    """
    node_map = URLNodeMap()

    # All modifications should succeed before freeze
    api = node_map.get_or_create_node("/api")
    api.set_metadata("version", "1.0")

    def handler():
        pass

    api.attach_handler("GET", handler)
    api.add_child("v1")

    # Verify modifications took effect
    if api.get_metadata("version") != "1.0":
        errmsg = "Expected metadata to be set"
        raise AssertionError(errmsg)

    if api.get_handler("GET") is not handler:
        errmsg = "Expected handler to be attached"
        raise AssertionError(errmsg)

    if "v1" not in api.children:
        errmsg = "Expected child to be added"
        raise AssertionError(errmsg)

    return


# =============================================================================
# Helper Functions for Property-Based Tests
# =============================================================================

import random
import string
import copy


def _generate_random_segment(min_length=1, max_length=12):
    """
        Generate a random valid literal path segment.

        :returns: A random literal segment string.
    """
    length = random.randint(min_length, max_length)
    chars = string.ascii_lowercase + string.digits + "_-"
    first_char = random.choice(string.ascii_lowercase)
    if length == 1:
        return first_char
    rest = "".join(random.choices(chars, k=length - 1))
    return first_char + rest


def _generate_random_path(min_segments=1, max_segments=5):
    """
        Generate a random valid normalized path string.

        :returns: A normalized path string (e.g., "/api/v1/users").
    """
    num_segments = random.randint(min_segments, max_segments)
    segments = [_generate_random_segment() for _ in range(num_segments)]
    return "/" + "/".join(segments)


def _generate_distinct_paths(count, min_segments=1, max_segments=5):
    """
        Generate a list of distinct random normalized paths.

        :returns: A list of distinct path strings.
    """
    paths = set()
    attempts = 0
    max_attempts = count * 10

    while len(paths) < count and attempts < max_attempts:
        path = _generate_random_path(min_segments, max_segments)
        paths.add(path)
        attempts += 1

    return list(paths)


def _snapshot_tree(node_map):
    """
        Capture a snapshot of the tree state for comparison.

        Returns a dictionary mapping each node path to a dict of its
        metadata copy, handler keys, and child segment names.

        :param node_map: The URLNodeMap to snapshot.
        :returns: A dict of path -> state info.
    """
    snapshot = {}
    for node in node_map.iterate_nodes():
        snapshot[node.path] = {
            "metadata": dict(node.metadata),
            "handler_methods": sorted(
                method for method in ["GET", "POST", "PUT", "DELETE", "PATCH"]
                if node.get_handler(method) is not None
            ),
            "children": sorted(node.children.keys()),
        }
    return snapshot


# =============================================================================
# Property-Based Tests
# =============================================================================

# Feature: url-node-map, Property 10: Frozen Immutability
# *For any* frozen URL Node Map, all modification operations (add_child,
# remove_node, set_metadata, attach_handler) SHALL raise FrozenTreeError
# without modifying the tree.
# **Validates: Requirements 8.3, 8.4**


def test_property_10_frozen_immutability_all_modifications_raise():
    """
        Property 10: Frozen Immutability

        For any frozen URL Node Map, all modification operations (add_child,
        remove_node, set_metadata, attach_handler) SHALL raise FrozenTreeError
        without modifying the tree. The tree state must remain unchanged after
        each failed modification attempt.

        **Validates: Requirements 8.3, 8.4**
    """
    http_methods = ["GET", "POST", "PUT", "DELETE", "PATCH"]

    for iteration in range(100):
        random.seed(iteration * 77777)

        # Build a random tree
        node_map = URLNodeMap()
        num_paths = random.randint(1, 10)
        paths = _generate_distinct_paths(num_paths, min_segments=1, max_segments=4)

        for path in paths:
            node_map.get_or_create_node(path)

        # Attach random handlers and metadata to some nodes
        all_nodes = list(node_map.iterate_nodes())
        for node in all_nodes:
            if random.random() < 0.4:
                method = random.choice(http_methods)
                if node.get_handler(method) is None:
                    node.attach_handler(method, lambda: None)
            if random.random() < 0.5:
                key = random.choice(["tags", "version", "rate_limit", "access_policy"])
                node.set_metadata(key, f"value_{iteration}")

        # Freeze the tree
        node_map.freeze()

        # Capture the tree state before modification attempts
        snapshot_before = _snapshot_tree(node_map)

        # Pick a random existing node to attempt modifications on
        target_node = random.choice(all_nodes)

        # 1. Test add_child raises FrozenTreeError
        new_segment = _generate_random_segment()
        try:
            target_node.add_child(new_segment)
            errmsg = (
                f"Iteration {iteration}: add_child('{new_segment}') on "
                f"node '{target_node.path}' did not raise FrozenTreeError"
            )
            raise AssertionError(errmsg)
        except FrozenTreeError:
            pass

        # Verify tree unchanged after add_child attempt
        snapshot_after = _snapshot_tree(node_map)
        if snapshot_after != snapshot_before:
            errmsg = (
                f"Iteration {iteration}: Tree state changed after failed "
                f"add_child on '{target_node.path}'"
            )
            raise AssertionError(errmsg)

        # 2. Test set_metadata raises FrozenTreeError
        meta_key = random.choice(["tags", "version", "rate_limit", "custom_key"])
        try:
            target_node.set_metadata(meta_key, "frozen_value")
            errmsg = (
                f"Iteration {iteration}: set_metadata('{meta_key}', ...) on "
                f"node '{target_node.path}' did not raise FrozenTreeError"
            )
            raise AssertionError(errmsg)
        except FrozenTreeError:
            pass

        # Verify tree unchanged after set_metadata attempt
        snapshot_after = _snapshot_tree(node_map)
        if snapshot_after != snapshot_before:
            errmsg = (
                f"Iteration {iteration}: Tree state changed after failed "
                f"set_metadata on '{target_node.path}'"
            )
            raise AssertionError(errmsg)

        # 3. Test attach_handler raises FrozenTreeError
        method = random.choice(http_methods)
        try:
            target_node.attach_handler(method, lambda: None)
            errmsg = (
                f"Iteration {iteration}: attach_handler('{method}', ...) on "
                f"node '{target_node.path}' did not raise FrozenTreeError"
            )
            raise AssertionError(errmsg)
        except FrozenTreeError:
            pass

        # Verify tree unchanged after attach_handler attempt
        snapshot_after = _snapshot_tree(node_map)
        if snapshot_after != snapshot_before:
            errmsg = (
                f"Iteration {iteration}: Tree state changed after failed "
                f"attach_handler on '{target_node.path}'"
            )
            raise AssertionError(errmsg)

    return


def test_property_10_frozen_immutability_remove_node_raises():
    """
        Property 10: Frozen Immutability - remove_node variant

        For any frozen URL Node Map, calling remove_node on any existing
        path SHALL raise FrozenTreeError without modifying the tree.

        **Validates: Requirements 8.3, 8.4**
    """
    for iteration in range(100):
        random.seed(iteration * 88888)

        # Build a random tree
        node_map = URLNodeMap()
        num_paths = random.randint(1, 10)
        paths = _generate_distinct_paths(num_paths, min_segments=1, max_segments=4)

        for path in paths:
            node_map.get_or_create_node(path)

        # Freeze the tree
        node_map.freeze()

        # Capture the tree state
        snapshot_before = _snapshot_tree(node_map)

        # Pick a random non-root path to attempt removal
        non_root_nodes = [n for n in node_map.iterate_nodes() if n.path != "/"]
        if len(non_root_nodes) == 0:
            continue

        target = random.choice(non_root_nodes)

        try:
            node_map.remove_node(target.path)
            errmsg = (
                f"Iteration {iteration}: remove_node('{target.path}') "
                f"did not raise FrozenTreeError"
            )
            raise AssertionError(errmsg)
        except FrozenTreeError:
            pass

        # Verify tree unchanged
        snapshot_after = _snapshot_tree(node_map)
        if snapshot_after != snapshot_before:
            errmsg = (
                f"Iteration {iteration}: Tree state changed after failed "
                f"remove_node on '{target.path}'"
            )
            raise AssertionError(errmsg)

        # Verify the node still exists
        if not node_map.has_node(target.path):
            errmsg = (
                f"Iteration {iteration}: Node '{target.path}' disappeared "
                f"after failed remove_node"
            )
            raise AssertionError(errmsg)

    return


def test_property_10_frozen_immutability_get_or_create_new_path_raises():
    """
        Property 10: Frozen Immutability - get_or_create_node for new paths

        For any frozen URL Node Map, calling get_or_create_node with a path
        that does not exist SHALL raise FrozenTreeError without modifying
        the tree.

        **Validates: Requirements 8.3, 8.4**
    """
    for iteration in range(100):
        random.seed(iteration * 99999)

        # Build a random tree
        node_map = URLNodeMap()
        num_paths = random.randint(0, 8)
        paths = _generate_distinct_paths(num_paths, min_segments=1, max_segments=3)

        for path in paths:
            node_map.get_or_create_node(path)

        # Freeze the tree
        node_map.freeze()

        # Capture the tree state
        snapshot_before = _snapshot_tree(node_map)

        # Generate a new path that does not exist in the tree
        new_path = None
        for _ in range(50):
            candidate = _generate_random_path(min_segments=1, max_segments=5)
            if not node_map.has_node(candidate):
                new_path = candidate
                break

        if new_path is None:
            continue

        try:
            node_map.get_or_create_node(new_path)
            errmsg = (
                f"Iteration {iteration}: get_or_create_node('{new_path}') "
                f"did not raise FrozenTreeError for a new path"
            )
            raise AssertionError(errmsg)
        except FrozenTreeError:
            pass

        # Verify tree unchanged
        snapshot_after = _snapshot_tree(node_map)
        if snapshot_after != snapshot_before:
            errmsg = (
                f"Iteration {iteration}: Tree state changed after failed "
                f"get_or_create_node for new path '{new_path}'"
            )
            raise AssertionError(errmsg)

        # Verify the new path was not created
        if node_map.has_node(new_path):
            errmsg = (
                f"Iteration {iteration}: New path '{new_path}' was created "
                f"despite FrozenTreeError"
            )
            raise AssertionError(errmsg)

    return
