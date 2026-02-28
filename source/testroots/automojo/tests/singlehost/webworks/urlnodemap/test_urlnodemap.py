"""
    Tests for the URLNodeMap class.
    
    This module contains unit tests for the URLNodeMap class which represents
    the hierarchical tree structure for organizing URL paths and endpoint
    metadata. Tests cover node map creation, node addressing, and removal.
"""

from automojo.webworks.urlnodemap.urlnodemap import URLNodeMap
from automojo.webworks.urlnodemap.urlnode import URLNode
from automojo.webworks.urlnodemap.exceptions import (
    NodeNotFoundError,
    FrozenTreeError,
    NodeHasChildrenError,
)


# =============================================================================
# Unit Tests for URLNodeMap Initialization
# =============================================================================

def test_urlnodemap_init_creates_root():
    """
        Test that URLNodeMap initialization creates a root node.
        
        Validates: Requirements 1.2
    """
    node_map = URLNodeMap()
    
    if node_map.root is None:
        errmsg = "Expected root node to be created"
        raise AssertionError(errmsg)
    
    return


def test_urlnodemap_init_root_has_correct_path():
    """
        Test that the root node has path "/".
        
        Validates: Requirements 1.2
    """
    node_map = URLNodeMap()
    
    if node_map.root.path != "/":
        errmsg = f"Expected root path '/', got '{node_map.root.path}'"
        raise AssertionError(errmsg)
    
    return


def test_urlnodemap_init_root_has_empty_segment():
    """
        Test that the root node has empty segment.
    """
    node_map = URLNodeMap()
    
    if node_map.root.segment != "":
        errmsg = f"Expected root segment '', got '{node_map.root.segment}'"
        raise AssertionError(errmsg)
    
    return


def test_urlnodemap_init_root_has_no_parent():
    """
        Test that the root node has no parent.
    """
    node_map = URLNodeMap()
    
    if node_map.root.parent is not None:
        errmsg = "Expected root parent to be None"
        raise AssertionError(errmsg)
    
    return


def test_urlnodemap_init_not_frozen():
    """
        Test that URLNodeMap starts unfrozen.
    """
    node_map = URLNodeMap()
    
    if node_map.frozen is True:
        errmsg = "Expected node map to start unfrozen"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for get_node Method
# =============================================================================

def test_urlnodemap_get_node_returns_root_for_slash():
    """
        Test that get_node returns root for path "/".
        
        Validates: Requirements 2.1
    """
    node_map = URLNodeMap()
    
    result = node_map.get_node("/")
    
    if result is not node_map.root:
        errmsg = "Expected get_node('/') to return root"
        raise AssertionError(errmsg)
    
    return


def test_urlnodemap_get_node_returns_existing_node():
    """
        Test that get_node returns an existing node.
        
        Validates: Requirements 2.1
    """
    node_map = URLNodeMap()
    api_node = node_map.root.add_child("api")
    
    result = node_map.get_node("/api")
    
    if result is not api_node:
        errmsg = "Expected get_node to return the existing node"
        raise AssertionError(errmsg)
    
    return


def test_urlnodemap_get_node_returns_deep_node():
    """
        Test that get_node returns a deeply nested node.
        
        Validates: Requirements 2.1
    """
    node_map = URLNodeMap()
    api = node_map.root.add_child("api")
    v1 = api.add_child("v1")
    users = v1.add_child("users")
    
    result = node_map.get_node("/api/v1/users")
    
    if result is not users:
        errmsg = "Expected get_node to return the deep node"
        raise AssertionError(errmsg)
    
    return


def test_urlnodemap_get_node_raises_for_nonexistent():
    """
        Test that get_node raises NodeNotFoundError for nonexistent path.
        
        Validates: Requirements 2.5
    """
    node_map = URLNodeMap()
    
    try:
        node_map.get_node("/nonexistent")
        errmsg = "Expected NodeNotFoundError to be raised"
        raise AssertionError(errmsg)
    except NodeNotFoundError as exc:
        if exc.path != "/nonexistent":
            errmsg = f"Expected path '/nonexistent', got '{exc.path}'"
            raise AssertionError(errmsg)
    
    return


def test_urlnodemap_get_node_raises_for_partial_path():
    """
        Test that get_node raises NodeNotFoundError when only part of path exists.
    """
    node_map = URLNodeMap()
    node_map.root.add_child("api")
    
    try:
        node_map.get_node("/api/v1/users")
        errmsg = "Expected NodeNotFoundError to be raised"
        raise AssertionError(errmsg)
    except NodeNotFoundError as exc:
        if exc.path != "/api/v1/users":
            errmsg = f"Expected path '/api/v1/users', got '{exc.path}'"
            raise AssertionError(errmsg)
    
    return


def test_urlnodemap_get_node_normalizes_path():
    """
        Test that get_node normalizes the path before lookup.
        
        Validates: Requirements 2.9, 2.10
    """
    node_map = URLNodeMap()
    api_node = node_map.root.add_child("api")
    
    # Test with trailing slash
    result = node_map.get_node("/api/")
    
    if result is not api_node:
        errmsg = "Expected get_node to normalize trailing slash"
        raise AssertionError(errmsg)
    
    return


def test_urlnodemap_get_node_normalizes_multiple_slashes():
    """
        Test that get_node normalizes multiple consecutive slashes.
        
        Validates: Requirements 2.9
    """
    node_map = URLNodeMap()
    api = node_map.root.add_child("api")
    v1 = api.add_child("v1")
    
    result = node_map.get_node("//api//v1//")
    
    if result is not v1:
        errmsg = "Expected get_node to normalize multiple slashes"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for get_or_create_node Method
# =============================================================================

def test_urlnodemap_get_or_create_node_returns_root():
    """
        Test that get_or_create_node returns root for path "/".
        
        Validates: Requirements 2.2
    """
    node_map = URLNodeMap()
    
    result = node_map.get_or_create_node("/")
    
    if result is not node_map.root:
        errmsg = "Expected get_or_create_node('/') to return root"
        raise AssertionError(errmsg)
    
    return


def test_urlnodemap_get_or_create_node_returns_existing():
    """
        Test that get_or_create_node returns existing node without creating.
        
        Validates: Requirements 2.2
    """
    node_map = URLNodeMap()
    api_node = node_map.root.add_child("api")
    
    result = node_map.get_or_create_node("/api")
    
    if result is not api_node:
        errmsg = "Expected get_or_create_node to return existing node"
        raise AssertionError(errmsg)
    
    return


def test_urlnodemap_get_or_create_node_creates_single_segment():
    """
        Test that get_or_create_node creates a single segment path.
        
        Validates: Requirements 2.2, 2.6
    """
    node_map = URLNodeMap()
    
    result = node_map.get_or_create_node("/api")
    
    if result is None:
        errmsg = "Expected get_or_create_node to return a node"
        raise AssertionError(errmsg)
    
    if result.path != "/api":
        errmsg = f"Expected path '/api', got '{result.path}'"
        raise AssertionError(errmsg)
    
    return


def test_urlnodemap_get_or_create_node_creates_intermediate_nodes():
    """
        Test that get_or_create_node creates all intermediate nodes.
        
        Validates: Requirements 1.3, 2.6
    """
    node_map = URLNodeMap()
    
    result = node_map.get_or_create_node("/api/v1/users")
    
    # Verify the target node
    if result.path != "/api/v1/users":
        errmsg = f"Expected path '/api/v1/users', got '{result.path}'"
        raise AssertionError(errmsg)
    
    # Verify intermediate nodes were created
    if not node_map.has_node("/api"):
        errmsg = "Expected intermediate node '/api' to exist"
        raise AssertionError(errmsg)
    
    if not node_map.has_node("/api/v1"):
        errmsg = "Expected intermediate node '/api/v1' to exist"
        raise AssertionError(errmsg)
    
    return


def test_urlnodemap_get_or_create_node_sets_parent_references():
    """
        Test that get_or_create_node sets correct parent references.
        
        Validates: Requirements 1.6
    """
    node_map = URLNodeMap()
    
    users = node_map.get_or_create_node("/api/v1/users")
    
    # Verify parent chain
    if users.parent is None:
        errmsg = "Expected users to have a parent"
        raise AssertionError(errmsg)
    
    v1 = users.parent
    if v1.path != "/api/v1":
        errmsg = f"Expected parent path '/api/v1', got '{v1.path}'"
        raise AssertionError(errmsg)
    
    api = v1.parent
    if api.path != "/api":
        errmsg = f"Expected grandparent path '/api', got '{api.path}'"
        raise AssertionError(errmsg)
    
    if api.parent is not node_map.root:
        errmsg = "Expected api.parent to be root"
        raise AssertionError(errmsg)
    
    return


def test_urlnodemap_get_or_create_node_normalizes_path():
    """
        Test that get_or_create_node normalizes the path.
        
        Validates: Requirements 2.9, 2.10
    """
    node_map = URLNodeMap()
    
    result = node_map.get_or_create_node("/api/v1/")
    
    if result.path != "/api/v1":
        errmsg = f"Expected normalized path '/api/v1', got '{result.path}'"
        raise AssertionError(errmsg)
    
    return


def test_urlnodemap_get_or_create_node_idempotent():
    """
        Test that calling get_or_create_node multiple times returns same node.
        
        Validates: Requirements 1.7
    """
    node_map = URLNodeMap()
    
    result1 = node_map.get_or_create_node("/api/v1/users")
    result2 = node_map.get_or_create_node("/api/v1/users")
    
    if result1 is not result2:
        errmsg = "Expected get_or_create_node to return same node on repeated calls"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for has_node Method
# =============================================================================

def test_urlnodemap_has_node_true_for_root():
    """
        Test that has_node returns True for root path.
        
        Validates: Requirements 2.3
    """
    node_map = URLNodeMap()
    
    result = node_map.has_node("/")
    
    if result is not True:
        errmsg = f"Expected has_node('/') to return True, got {result}"
        raise AssertionError(errmsg)
    
    return


def test_urlnodemap_has_node_true_for_existing():
    """
        Test that has_node returns True for existing path.
        
        Validates: Requirements 2.3
    """
    node_map = URLNodeMap()
    node_map.root.add_child("api")
    
    result = node_map.has_node("/api")
    
    if result is not True:
        errmsg = f"Expected has_node('/api') to return True, got {result}"
        raise AssertionError(errmsg)
    
    return


def test_urlnodemap_has_node_false_for_nonexistent():
    """
        Test that has_node returns False for nonexistent path.
        
        Validates: Requirements 2.3
    """
    node_map = URLNodeMap()
    
    result = node_map.has_node("/nonexistent")
    
    if result is not False:
        errmsg = f"Expected has_node('/nonexistent') to return False, got {result}"
        raise AssertionError(errmsg)
    
    return


def test_urlnodemap_has_node_false_for_partial_path():
    """
        Test that has_node returns False when only part of path exists.
    """
    node_map = URLNodeMap()
    node_map.root.add_child("api")
    
    result = node_map.has_node("/api/v1")
    
    if result is not False:
        errmsg = f"Expected has_node('/api/v1') to return False, got {result}"
        raise AssertionError(errmsg)
    
    return


def test_urlnodemap_has_node_normalizes_path():
    """
        Test that has_node normalizes the path before checking.
        
        Validates: Requirements 2.9, 2.10
    """
    node_map = URLNodeMap()
    node_map.root.add_child("api")
    
    # Test with trailing slash
    result = node_map.has_node("/api/")
    
    if result is not True:
        errmsg = "Expected has_node to normalize trailing slash"
        raise AssertionError(errmsg)
    
    return


def test_urlnodemap_has_node_deep_path():
    """
        Test has_node with a deep path.
    """
    node_map = URLNodeMap()
    api = node_map.root.add_child("api")
    v1 = api.add_child("v1")
    v1.add_child("users")
    
    if not node_map.has_node("/api/v1/users"):
        errmsg = "Expected has_node('/api/v1/users') to return True"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for remove_node Method
# =============================================================================

def test_urlnodemap_remove_node_removes_leaf():
    """
        Test that remove_node removes a leaf node.
        
        Validates: Requirements 2.4
    """
    node_map = URLNodeMap()
    node_map.root.add_child("api")
    
    node_map.remove_node("/api")
    
    if node_map.has_node("/api"):
        errmsg = "Expected node to be removed"
        raise AssertionError(errmsg)
    
    return


def test_urlnodemap_remove_node_raises_for_nonexistent():
    """
        Test that remove_node raises NodeNotFoundError for nonexistent path.
        
        Validates: Requirements 2.4
    """
    node_map = URLNodeMap()
    
    try:
        node_map.remove_node("/nonexistent")
        errmsg = "Expected NodeNotFoundError to be raised"
        raise AssertionError(errmsg)
    except NodeNotFoundError as exc:
        if exc.path != "/nonexistent":
            errmsg = f"Expected path '/nonexistent', got '{exc.path}'"
            raise AssertionError(errmsg)
    
    return


def test_urlnodemap_remove_node_raises_for_root():
    """
        Test that remove_node raises ValueError for root path.
    """
    node_map = URLNodeMap()
    
    try:
        node_map.remove_node("/")
        errmsg = "Expected ValueError to be raised"
        raise AssertionError(errmsg)
    except ValueError as exc:
        if "root" not in str(exc).lower():
            errmsg = f"Expected error message to mention 'root', got '{exc}'"
            raise AssertionError(errmsg)
    
    return


def test_urlnodemap_remove_node_raises_for_node_with_children():
    """
        Test that remove_node raises NodeHasChildrenError when node has children.
        
        Validates: Requirements 2.4
    """
    node_map = URLNodeMap()
    api = node_map.root.add_child("api")
    api.add_child("v1")
    
    try:
        node_map.remove_node("/api")
        errmsg = "Expected NodeHasChildrenError to be raised"
        raise AssertionError(errmsg)
    except NodeHasChildrenError as exc:
        if exc.path != "/api":
            errmsg = f"Expected path '/api', got '{exc.path}'"
            raise AssertionError(errmsg)
        if exc.child_count != 1:
            errmsg = f"Expected child_count 1, got {exc.child_count}"
            raise AssertionError(errmsg)
    
    return


def test_urlnodemap_remove_node_recursive_removes_descendants():
    """
        Test that remove_node with recursive=True removes all descendants.
        
        Validates: Requirements 2.4
    """
    node_map = URLNodeMap()
    api = node_map.root.add_child("api")
    v1 = api.add_child("v1")
    v1.add_child("users")
    
    node_map.remove_node("/api", recursive=True)
    
    if node_map.has_node("/api"):
        errmsg = "Expected '/api' to be removed"
        raise AssertionError(errmsg)
    
    if node_map.has_node("/api/v1"):
        errmsg = "Expected '/api/v1' to be removed"
        raise AssertionError(errmsg)
    
    if node_map.has_node("/api/v1/users"):
        errmsg = "Expected '/api/v1/users' to be removed"
        raise AssertionError(errmsg)
    
    return


def test_urlnodemap_remove_node_recursive_leaf():
    """
        Test that remove_node with recursive=True works on leaf nodes.
    """
    node_map = URLNodeMap()
    node_map.root.add_child("api")
    
    node_map.remove_node("/api", recursive=True)
    
    if node_map.has_node("/api"):
        errmsg = "Expected node to be removed"
        raise AssertionError(errmsg)
    
    return


def test_urlnodemap_remove_node_preserves_siblings():
    """
        Test that remove_node preserves sibling nodes.
    """
    node_map = URLNodeMap()
    node_map.root.add_child("api")
    node_map.root.add_child("docs")
    
    node_map.remove_node("/api")
    
    if node_map.has_node("/api"):
        errmsg = "Expected '/api' to be removed"
        raise AssertionError(errmsg)
    
    if not node_map.has_node("/docs"):
        errmsg = "Expected '/docs' to be preserved"
        raise AssertionError(errmsg)
    
    return


def test_urlnodemap_remove_node_deep_path():
    """
        Test remove_node on a deeply nested node.
    """
    node_map = URLNodeMap()
    api = node_map.root.add_child("api")
    v1 = api.add_child("v1")
    v1.add_child("users")
    
    node_map.remove_node("/api/v1/users")
    
    if node_map.has_node("/api/v1/users"):
        errmsg = "Expected '/api/v1/users' to be removed"
        raise AssertionError(errmsg)
    
    # Parent should still exist
    if not node_map.has_node("/api/v1"):
        errmsg = "Expected '/api/v1' to still exist"
        raise AssertionError(errmsg)
    
    return


def test_urlnodemap_remove_node_normalizes_path():
    """
        Test that remove_node normalizes the path.
        
        Validates: Requirements 2.9, 2.10
    """
    node_map = URLNodeMap()
    node_map.root.add_child("api")
    
    node_map.remove_node("/api/")
    
    if node_map.has_node("/api"):
        errmsg = "Expected node to be removed with normalized path"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Unit Tests for Path Uniqueness
# =============================================================================

def test_urlnodemap_path_uniqueness():
    """
        Test that paths are unique in the tree.
        
        Validates: Requirements 1.7
    """
    node_map = URLNodeMap()
    
    node1 = node_map.get_or_create_node("/api/v1")
    node2 = node_map.get_or_create_node("/api/v1")
    
    if node1 is not node2:
        errmsg = "Expected same node for same path"
        raise AssertionError(errmsg)
    
    return


def test_urlnodemap_different_paths_different_nodes():
    """
        Test that different paths create different nodes.
    """
    node_map = URLNodeMap()
    
    node1 = node_map.get_or_create_node("/api/v1")
    node2 = node_map.get_or_create_node("/api/v2")
    
    if node1 is node2:
        errmsg = "Expected different nodes for different paths"
        raise AssertionError(errmsg)
    
    return


# =============================================================================
# Integration Tests
# =============================================================================

def test_urlnodemap_complex_tree_structure():
    """
        Test building a complex tree structure.
        
        Validates: Requirements 1.1, 1.3, 1.4
    """
    node_map = URLNodeMap()
    
    # Build a complex tree
    node_map.get_or_create_node("/api/v1/users")
    node_map.get_or_create_node("/api/v1/posts")
    node_map.get_or_create_node("/api/v2/users")
    node_map.get_or_create_node("/docs/api")
    node_map.get_or_create_node("/static/css")
    node_map.get_or_create_node("/static/js")
    
    # Verify all paths exist
    expected_paths = [
        "/",
        "/api",
        "/api/v1",
        "/api/v1/users",
        "/api/v1/posts",
        "/api/v2",
        "/api/v2/users",
        "/docs",
        "/docs/api",
        "/static",
        "/static/css",
        "/static/js",
    ]
    
    for path in expected_paths:
        if not node_map.has_node(path):
            errmsg = f"Expected path '{path}' to exist"
            raise AssertionError(errmsg)
    
    return


def test_urlnodemap_parameter_segments():
    """
        Test creating paths with parameter segments.
        
        Validates: Requirements 7.1, 7.2
    """
    node_map = URLNodeMap()
    
    user_node = node_map.get_or_create_node("/api/users/{user_id}")
    
    if not user_node.is_parameter:
        errmsg = "Expected user_id node to be a parameter"
        raise AssertionError(errmsg)
    
    if user_node.parameter_name != "user_id":
        errmsg = f"Expected parameter_name 'user_id', got '{user_node.parameter_name}'"
        raise AssertionError(errmsg)
    
    return



# =============================================================================
# Random Data Generators for Property Tests
# =============================================================================

import random
import string


def _generate_random_segment(min_length=1, max_length=15):
    """
        Generate a random valid literal path segment.
        
        Valid segments contain alphanumeric characters, underscores, and hyphens.
        The first character is always a letter.
        
        :returns: A random literal segment string.
    """
    length = random.randint(min_length, max_length)
    chars = string.ascii_lowercase + string.digits + "_-"
    first_char = random.choice(string.ascii_lowercase)
    if length == 1:
        return first_char
    rest = "".join(random.choices(chars, k=length - 1))
    return first_char + rest


def _generate_random_path(min_segments=1, max_segments=6):
    """
        Generate a random valid normalized path string using literal segments.
        
        The returned path starts with "/" and contains no trailing slash
        or consecutive slashes.
        
        :param min_segments: Minimum number of path segments.
        :param max_segments: Maximum number of path segments.
        
        :returns: A normalized path string (e.g., "/api/v1/users").
    """
    num_segments = random.randint(min_segments, max_segments)
    segments = [_generate_random_segment() for _ in range(num_segments)]
    return "/" + "/".join(segments)


def _generate_distinct_paths(count, min_segments=1, max_segments=5):
    """
        Generate a list of distinct random normalized paths.
        
        :param count: Number of distinct paths to generate.
        :param min_segments: Minimum number of segments per path.
        :param max_segments: Maximum number of segments per path.
        
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


# =============================================================================
# Property-Based Tests
# =============================================================================

# Feature: url-node-map, Property 1: Path Uniqueness
# *For any* URL Node Map, no two nodes SHALL have the same full path.
# Adding a node with a duplicate path SHALL raise NodeConflictError.
# **Validates: Requirements 1.7, 1.8**

from automojo.webworks.urlnodemap.exceptions import NodeConflictError


def test_property_1_path_uniqueness_no_duplicate_paths():
    """
        Property 1: Path Uniqueness
        
        For any URL Node Map populated with distinct paths, no two nodes
        SHALL have the same full path. Every node in the tree has a unique
        path value.
        
        **Validates: Requirements 1.7, 1.8**
    """
    for iteration in range(100):
        random.seed(iteration * 77777)

        node_map = URLNodeMap()

        # Generate a set of distinct paths
        num_paths = random.randint(2, 12)
        paths = _generate_distinct_paths(num_paths, min_segments=1, max_segments=4)

        # Insert all paths
        for path in paths:
            node_map.get_or_create_node(path)

        # Collect all node paths via depth-first traversal
        visited_paths = set()

        def collect_paths(node):
            if node.path in visited_paths:
                errmsg = (
                    f"Iteration {iteration}: Duplicate path found in tree.\n"
                    f"  Duplicate path: '{node.path}'\n"
                    f"  Inserted paths: {paths}"
                )
                raise AssertionError(errmsg)
            visited_paths.add(node.path)
            for child in node.children.values():
                collect_paths(child)

        collect_paths(node_map.root)

    return


def test_property_1_path_uniqueness_duplicate_add_child_raises():
    """
        Property 1: Path Uniqueness - Duplicate add_child raises NodeConflictError
        
        For any node, adding a child with a segment that already exists
        SHALL raise NodeConflictError.
        
        **Validates: Requirements 1.7, 1.8**
    """
    for iteration in range(100):
        random.seed(iteration * 88888)

        node_map = URLNodeMap()

        # Create a random path to get a parent node
        depth = random.randint(0, 4)
        current = node_map.root
        for _ in range(depth):
            segment = _generate_random_segment()
            if segment not in current._children:
                current = current.add_child(segment)
            else:
                current = current._children[segment]

        # Add a child with a random segment
        child_segment = _generate_random_segment()
        while child_segment in current._children:
            child_segment = _generate_random_segment()

        current.add_child(child_segment)

        # Attempt to add the same segment again - must raise NodeConflictError
        raised = False
        try:
            current.add_child(child_segment)
        except NodeConflictError as exc:
            raised = True
            # Verify the error references the correct path
            if child_segment not in exc.path:
                errmsg = (
                    f"Iteration {iteration}: NodeConflictError path does not contain "
                    f"the conflicting segment.\n"
                    f"  Segment: '{child_segment}'\n"
                    f"  Error path: '{exc.path}'"
                )
                raise AssertionError(errmsg)

        if not raised:
            errmsg = (
                f"Iteration {iteration}: Expected NodeConflictError when adding "
                f"duplicate segment '{child_segment}' to node at '{current.path}'"
            )
            raise AssertionError(errmsg)

    return


def test_property_1_path_uniqueness_get_or_create_returns_same_node():
    """
        Property 1: Path Uniqueness - get_or_create_node returns same node
        
        For any path, calling get_or_create_node multiple times SHALL return
        the exact same node object, confirming path uniqueness is maintained.
        
        **Validates: Requirements 1.7, 1.8**
    """
    for iteration in range(100):
        random.seed(iteration * 99999)

        node_map = URLNodeMap()

        # Generate a random path
        path = _generate_random_path(min_segments=1, max_segments=5)

        # Create the node
        node_first = node_map.get_or_create_node(path)

        # Call again - must return the same object
        node_second = node_map.get_or_create_node(path)

        if node_first is not node_second:
            errmsg = (
                f"Iteration {iteration}: get_or_create_node returned different "
                f"objects for the same path.\n"
                f"  Path: '{path}'\n"
                f"  First node id: {id(node_first)}\n"
                f"  Second node id: {id(node_second)}"
            )
            raise AssertionError(errmsg)

    return


# =============================================================================
# Property 3: Intermediate Node Creation
# =============================================================================

# Feature: url-node-map, Property 3: Intermediate Node Creation
# *For any* path with multiple segments, calling `get_or_create_node(path)`
# SHALL create all intermediate nodes such that traversing from root to the
# target node visits each segment in order.
# **Validates: Requirements 1.3, 2.6**

from automojo.webworks.urlnodemap.pathutils import split_path


def test_property_3_intermediate_node_creation_all_intermediates_exist():
    """
        Property 3: Intermediate Node Creation - All intermediate nodes exist
        
        For any path with multiple segments, calling get_or_create_node(path)
        SHALL create all intermediate nodes. Every prefix of the path SHALL
        correspond to an existing node in the tree.
        
        **Validates: Requirements 1.3, 2.6**
    """
    for iteration in range(100):
        random.seed(iteration * 33333)

        node_map = URLNodeMap()

        # Generate a path with at least 2 segments to ensure intermediates
        path = _generate_random_path(min_segments=2, max_segments=6)
        segments = split_path(path)

        # Create the target node
        target_node = node_map.get_or_create_node(path)

        # Verify every intermediate prefix path exists
        for i in range(1, len(segments) + 1):
            prefix_path = "/" + "/".join(segments[:i])
            if not node_map.has_node(prefix_path):
                errmsg = (
                    f"Iteration {iteration}: Intermediate node missing.\n"
                    f"  Full path: '{path}'\n"
                    f"  Missing prefix: '{prefix_path}'\n"
                    f"  Segments: {segments}"
                )
                raise AssertionError(errmsg)

    return


def test_property_3_intermediate_node_creation_traversal_visits_segments_in_order():
    """
        Property 3: Intermediate Node Creation - Traversal visits segments in order
        
        For any path with multiple segments, traversing from root to the target
        node SHALL visit each segment in the correct order. The parent chain
        from the target back to root must contain the segments in reverse order.
        
        **Validates: Requirements 1.3, 2.6**
    """
    for iteration in range(100):
        random.seed(iteration * 44444)

        node_map = URLNodeMap()

        # Generate a multi-segment path
        path = _generate_random_path(min_segments=2, max_segments=6)
        segments = split_path(path)

        # Create the target node
        target_node = node_map.get_or_create_node(path)

        # Walk from target back to root, collecting segments
        visited_segments = []
        current = target_node
        while current.parent is not None:
            visited_segments.append(current.segment)
            current = current.parent

        # Reverse to get root-to-target order
        visited_segments.reverse()

        # The visited segments must match the original path segments
        if visited_segments != segments:
            errmsg = (
                f"Iteration {iteration}: Traversal segments do not match path.\n"
                f"  Path: '{path}'\n"
                f"  Expected segments: {segments}\n"
                f"  Visited segments: {visited_segments}"
            )
            raise AssertionError(errmsg)

        # Verify we ended at the root
        if current is not node_map.root:
            errmsg = (
                f"Iteration {iteration}: Traversal did not end at root.\n"
                f"  Path: '{path}'\n"
                f"  Final node path: '{current.path}'"
            )
            raise AssertionError(errmsg)

    return


def test_property_3_intermediate_node_creation_parent_child_chain():
    """
        Property 3: Intermediate Node Creation - Parent-child chain integrity
        
        For any path with multiple segments, each intermediate node SHALL be
        a child of its predecessor and the parent of its successor. Walking
        from root to target via children must reach the target node.
        
        **Validates: Requirements 1.3, 2.6**
    """
    for iteration in range(100):
        random.seed(iteration * 55555)

        node_map = URLNodeMap()

        # Generate a multi-segment path
        path = _generate_random_path(min_segments=2, max_segments=6)
        segments = split_path(path)

        # Create the target node
        target_node = node_map.get_or_create_node(path)

        # Walk from root to target via children, segment by segment
        current = node_map.root
        for idx, segment in enumerate(segments):
            children = current.children
            if segment not in children:
                errmsg = (
                    f"Iteration {iteration}: Segment not found in children.\n"
                    f"  Path: '{path}'\n"
                    f"  Segment index: {idx}\n"
                    f"  Segment: '{segment}'\n"
                    f"  Current node path: '{current.path}'\n"
                    f"  Available children: {list(children.keys())}"
                )
                raise AssertionError(errmsg)
            child = children[segment]

            # Verify the child's parent is the current node
            if child.parent is not current:
                errmsg = (
                    f"Iteration {iteration}: Parent reference mismatch.\n"
                    f"  Path: '{path}'\n"
                    f"  Child path: '{child.path}'\n"
                    f"  Expected parent path: '{current.path}'\n"
                    f"  Actual parent path: '{child.parent.path}'"
                )
                raise AssertionError(errmsg)

            current = child

        # After walking all segments, we must be at the target node
        if current is not target_node:
            errmsg = (
                f"Iteration {iteration}: Walking children did not reach target.\n"
                f"  Path: '{path}'\n"
                f"  Target node path: '{target_node.path}'\n"
                f"  Reached node path: '{current.path}'"
            )
            raise AssertionError(errmsg)

    return
